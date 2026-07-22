from __future__ import annotations

from shellsense.ai.core import AIEngine
from shellsense.database.manager import DatabaseManager
from shellsense.intelligence.context_collectors import ContextCollector, TerminalContext
from shellsense.intelligence.error_analysis import ErrorAnalysisResult, ErrorAnalyzer
from shellsense.intelligence.formatter import ResponseFormatter
from shellsense.intelligence.git_intelligence import (
    GitIntelligence,
    GitIntelligenceResult,
)
from shellsense.intelligence.log_analysis import LogAnalysisResult, LogAnalyzer
from shellsense.intelligence.privacy import PrivacyEngine
from shellsense.intelligence.prompt_builder import PromptBuilder
from shellsense.intelligence.script_analysis import ScriptAnalysisResult, ScriptAnalyzer
from shellsense.intelligence.service_intelligence import (
    ServiceIntelligence,
    ServiceResult,
)
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class IntelligenceEngine:
    def __init__(
        self,
        db: DatabaseManager | None = None,
        ai: AIEngine | None = None,
    ) -> None:
        self._db = db
        self._ai = ai
        self._knowledge = KnowledgeEngine(db) if db is not None else None

        self.collector = ContextCollector()
        self.privacy = PrivacyEngine()
        self.prompts = PromptBuilder()
        self.formatter = ResponseFormatter()
        self.error_analyzer = ErrorAnalyzer(db)
        self.script_analyzer = ScriptAnalyzer()
        self.log_analyzer = LogAnalyzer()
        self.git_intelligence = GitIntelligence()
        self.service_intel = ServiceIntelligence(self._knowledge)

    @property
    def ai_ready(self) -> bool:
        return self._ai is not None and self._ai.is_ready

    def collect_terminal_context(self) -> TerminalContext:
        return self.collector.collect_all()

    def build_context_block(self, context: TerminalContext | None = None) -> str:
        if context is None:
            context = self.collect_terminal_context()
        return self.prompts.build_context_block(context, self.privacy)

    def build_question_prompt(
        self,
        question: str,
        context: TerminalContext | None = None,
    ) -> str:
        if context is None:
            context = self.collect_terminal_context()
        return self.prompts.build_question_prompt(question, context, self.privacy)

    def ask_ai(
        self,
        question: str,
        system_style: str = "context",
        provider: str | None = None,
    ) -> str:
        if self._ai is None or not self._ai.is_ready:
            return self._fallback_ask(question)

        context = self.collect_terminal_context()
        system_prompt = self.prompts.build_system_prompt(system_style)
        user_prompt = self.build_question_prompt(question, context)

        try:
            response = self._ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                provider=provider,
            )
            return response.content
        except Exception as e:
            logger.error("AI request failed: %s", e)
            return self._fallback_ask(question)

    def _fallback_ask(self, question: str) -> str:
        if self._knowledge is None:
            return "AI is not configured. Use `ss ai login` to set up an AI provider."
        cmd = question.strip().split()[0] if question.strip() else ""
        info = self._knowledge.explain(cmd) if cmd else None
        if info:
            desc = info.get("long_description") or info.get("short_description", "")
            return (
                f"**{cmd}**\n\n{desc}\n\n*AI not available - showing offline knowledge*"
            )
        return "AI is not configured. Use `ss ai config` to enable AI, or `ss search` for local knowledge."

    def analyze_error(
        self,
        command: str,
        error_message: str,
        exit_code: int = -1,
        use_ai: bool = False,
        provider: str | None = None,
    ) -> ErrorAnalysisResult | str:
        local_result = self.error_analyzer.analyze(command, error_message, exit_code)

        if use_ai and self._ai is not None and self._ai.is_ready:
            context = self.collect_terminal_context()
            system_prompt = self.prompts.build_system_prompt("error")
            user_prompt = self.prompts.build_error_analysis_prompt(
                command,
                error_message,
                exit_code,
                context,
                self.privacy,
            )
            try:
                response = self._ai.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    provider=provider,
                )
                if response.content:
                    return response.content
            except Exception as e:
                logger.error("AI error analysis failed: %s", e)

        return local_result

    def analyze_script(
        self, path: str, use_ai: bool = False, provider: str | None = None
    ) -> ScriptAnalysisResult | str:
        local_result = self.script_analyzer.analyze(path)

        if (
            use_ai
            and self._ai is not None
            and self._ai.is_ready
            and local_result.content
        ):
            system_prompt = self.prompts.build_system_prompt("script")
            user_prompt = self.prompts.build_script_analysis_prompt(
                path,
                local_result.content,
                "analyze",
            )
            try:
                response = self._ai.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    provider=provider,
                )
                if response.content:
                    return response.content
            except Exception as e:
                logger.error("AI script analysis failed: %s", e)

        return local_result

    def optimize_script(
        self, path: str, use_ai: bool = False, provider: str | None = None
    ) -> ScriptAnalysisResult | str:
        if use_ai and self._ai is not None and self._ai.is_ready:
            try:
                with open(path) as f:
                    content = f.read()
                system_prompt = self.prompts.build_system_prompt("script")
                user_prompt = self.prompts.build_script_analysis_prompt(
                    path, content, "optimize"
                )
                response = self._ai.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    provider=provider,
                )
                if response.content:
                    return response.content
            except Exception as e:
                logger.error("AI script optimization failed: %s", e)

        return self.script_analyzer.analyze(path)

    def explain_script(
        self, path: str, use_ai: bool = False, provider: str | None = None
    ) -> str:
        if use_ai and self._ai is not None and self._ai.is_ready:
            try:
                with open(path) as f:
                    content = f.read()
                system_prompt = self.prompts.build_system_prompt("script")
                user_prompt = self.prompts.build_script_analysis_prompt(
                    path, content, "explain"
                )
                response = self._ai.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    provider=provider,
                )
                if response.content:
                    return response.content
            except Exception as e:
                logger.error("AI script explanation failed: %s", e)

        if self._knowledge is None:
            return "No AI configured. Use `ss ai config` to enable AI explanations."
        return "AI is not configured. Use `ss ai config` to enable script explanations."

    def analyze_logs(
        self,
        source: str = "journald",
        units: list[str] | None = None,
        lines: int = 100,
    ) -> LogAnalysisResult:
        if source == "journald":
            return self.log_analyzer.analyze_systemd_journal(units, lines)
        return self.log_analyzer.analyze_log_file(source)

    def get_git_status(self) -> GitIntelligenceResult:
        return self.git_intelligence.get_status()

    def get_git_log(self, count: int = 10) -> str:
        return self.git_intelligence.get_short_log(count)

    def explain_git_command(self, git_command: str) -> str:
        return self.git_intelligence.explain_command(git_command)

    def get_service_status(self, service_name: str) -> ServiceResult:
        return self.service_intel.get_status(service_name)

    def diagnose_service(self, service_name: str) -> str:
        return self.service_intel.diagnose(service_name)

    def explain_current_command(self) -> str | None:
        cmd = self.collector.collect_current_command()
        if not cmd:
            return None
        cmd_name = cmd.split()[0]
        if self._knowledge:
            info: dict[str, object] | None = self._knowledge.explain(cmd_name)
            if info:
                lines: list[str] = []
                lines.append(f"# {cmd_name}")

                short_desc = info.get("short_description")
                if short_desc:
                    lines.append(f"\n**Purpose:** {short_desc}")

                syntax = info.get("syntax")
                if syntax:
                    lines.append(f"\n**Syntax:** `{syntax}`")

                options_val = info.get("options")
                if options_val and isinstance(options_val, list):
                    lines.append("\n**Common Options:**")
                    for opt in options_val[:10]:
                        if isinstance(opt, dict):
                            flag = opt.get("flag", "")
                            desc = opt.get("description", "")
                            lines.append(f"  - `{flag}`: {desc}")

                examples_val = info.get("examples")
                if examples_val and isinstance(examples_val, list):
                    lines.append("\n**Examples:**")
                    for ex in examples_val[:5]:
                        if isinstance(ex, dict):
                            ex_cmd = ex.get("command", "")
                            ex_desc = ex.get("description", "")
                            lines.append(f"  ```bash\n  $ {ex_cmd}\n  ```")
                            if ex_desc:
                                lines.append(f"  {ex_desc}")

                risk = info.get("risk_level")
                if risk:
                    lines.append(f"\n**Risk Level:** {risk}")

                warnings_val = info.get("warnings")
                if warnings_val and isinstance(warnings_val, list):
                    for w in warnings_val:
                        lines.append(f"\n⚠ **Warning:** {w}")
                return "\n".join(lines)
        return None

    def get_recent_error(self) -> str | None:
        return self.error_analyzer.get_recent_error()
