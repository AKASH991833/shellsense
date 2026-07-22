from __future__ import annotations

from shellsense.ai.prompts import PromptEngine
from shellsense.intelligence.context_collectors import TerminalContext
from shellsense.intelligence.privacy import PrivacyEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

CONTEXT_SYSTEM_PROMPT = """You are ShellSense AI, an intelligent terminal assistant integrated into the user's shell environment.

You have access to the user's terminal context to provide accurate, context-aware assistance.

RULES:
- Provide concise, accurate answers. Use code blocks for commands.
- Never execute commands. Only suggest them.
- Warn about destructive operations clearly.
- Reference local knowledge before suggesting AI-generated solutions.
- Mark AI-generated content clearly."""

ERROR_ANALYSIS_SYSTEM_PROMPT = """You are ShellSense AI's error analysis system.

Analyze the following command error and provide:
1. Root cause analysis
2. Recommended fix steps
3. Alternative commands if applicable
4. Documentation references
5. Safety warnings

Be concise and practical. Prefer safe, well-known solutions."""

SCRIPT_ANALYSIS_SYSTEM_PROMPT = """You are ShellSense AI's script analysis engine.

Analyze the provided shell script and provide:
1. Purpose and overview
2. Complexity assessment
3. Potential bugs and issues
4. Security concerns
5. Performance improvements
6. Best practice recommendations

Be thorough but practical. Focus on actionable insights."""

LOG_ANALYSIS_SYSTEM_PROMPT = """You are ShellSense AI's log analysis engine.

Analyze the provided log content and provide:
1. Summary of findings
2. Anomalies or suspicious entries
3. Known error patterns detected
4. Recommended actions

Focus on actionable insights. Flag critical issues prominently."""


class PromptBuilder:
    def __init__(self, prompt_engine: PromptEngine | None = None) -> None:
        self._prompt_engine = prompt_engine or PromptEngine()
        self._templates: dict[str, str] = {}

    def register_template(self, name: str, template: str) -> None:
        self._templates[name] = template

    def build_system_prompt(self, style: str = "context") -> str:
        prompts = {
            "context": CONTEXT_SYSTEM_PROMPT,
            "error": ERROR_ANALYSIS_SYSTEM_PROMPT,
            "script": SCRIPT_ANALYSIS_SYSTEM_PROMPT,
            "log": LOG_ANALYSIS_SYSTEM_PROMPT,
        }
        return prompts.get(style, CONTEXT_SYSTEM_PROMPT)

    def build_context_block(
        self, context: TerminalContext, privacy: PrivacyEngine | None = None
    ) -> str:
        context_dict = context.to_dict()
        if privacy is not None:
            context_dict = privacy.filter_context(context_dict)

        parts: list[str] = ["<terminal_context>"]
        mapped = {
            "current_command": ("Current Command", True),
            "command_args": ("Arguments", True),
            "working_directory": ("Working Directory", True),
            "shell": ("Shell", True),
            "operating_system": ("Operating System", True),
            "distribution": ("Distribution", True),
            "kernel_version": ("Kernel", True),
            "user": ("User", False),
            "hostname": ("Hostname", False),
            "system_time": ("System Time", False),
            "python_virtual_env": ("Python Virtual Env", True),
            "is_container": ("Container", True),
            "git_repo": ("Git Repository", True),
            "git_branch": ("Git Branch", True),
            "git_status": ("Git Status", True),
            "package_managers": ("Package Managers", True),
            "recent_history": ("Recent History", True),
            "env_vars": ("Environment Variables", True),
        }

        for key, (label, _) in mapped.items():
            val = context_dict.get(key)
            if val is None or val == "" or val == [] or val == {}:
                continue
            if key == "recent_history" and isinstance(val, list):
                parts.append(f"  {label}:")
                for line in val[-5:]:
                    parts.append(f"    - {line}")
            elif key == "env_vars" and isinstance(val, dict):
                if val:
                    parts.append(f"  {label}:")
                    for k, v in val.items():
                        parts.append(f"    {k}={v}")
            elif key == "package_managers" and isinstance(val, list):
                parts.append(f"  {label}: {', '.join(val)}")
            else:
                parts.append(f"  {label}: {val}")

        parts.append("</terminal_context>")
        return "\n".join(parts)

    def build_question_prompt(
        self,
        question: str,
        context: TerminalContext | None = None,
        privacy: PrivacyEngine | None = None,
    ) -> str:
        parts: list[str] = []
        if context is not None:
            parts.append(self.build_context_block(context, privacy))
            parts.append("")
        parts.append("<user_question>")
        parts.append(question)
        parts.append("</user_question>")
        return "\n".join(parts)

    def build_error_analysis_prompt(
        self,
        command: str,
        error_message: str,
        exit_code: int | None = None,
        context: TerminalContext | None = None,
        privacy: PrivacyEngine | None = None,
    ) -> str:
        parts: list[str] = []
        parts.append("<error_analysis>")
        parts.append(f"  Command: {command}")
        if exit_code is not None:
            parts.append(f"  Exit Code: {exit_code}")
        parts.append("  Error Output:")
        for line in error_message.strip().split("\n"):
            parts.append(f"    {line}")
        parts.append("</error_analysis>")
        if context is not None:
            parts.append("")
            parts.append(self.build_context_block(context, privacy))
        return "\n".join(parts)

    def build_script_analysis_prompt(
        self,
        script_path: str,
        script_content: str,
        mode: str = "analyze",
    ) -> str:
        parts: list[str] = []
        mode_descriptions = {
            "analyze": "Analyze this shell script for bugs, security issues, and improvements.",
            "optimize": "Optimize this shell script for performance and readability.",
            "explain": "Explain what this shell script does in detail.",
        }
        description = mode_descriptions.get(mode, mode_descriptions["analyze"])
        parts.append(f'<script_analysis mode="{mode}">')
        parts.append(f"  {description}")
        parts.append("")
        parts.append(f"  File: {script_path}")
        parts.append("")
        parts.append("  ```bash")
        for line in script_content.split("\n"):
            parts.append(f"  {line}")
        parts.append("  ```")
        parts.append("</script_analysis>")
        return "\n".join(parts)

    def build_log_analysis_prompt(
        self,
        log_source: str,
        log_content: str,
        context: TerminalContext | None = None,
    ) -> str:
        parts: list[str] = []
        parts.append("<log_analysis>")
        parts.append(f"  Source: {log_source}")
        parts.append("")
        for line in log_content.strip().split("\n"):
            parts.append(f"  {line}")
        parts.append("</log_analysis>")
        if context is not None:
            parts.append("")
            parts.append(self.build_context_block(context, None))
        return "\n".join(parts)

    def build_git_prompt(
        self,
        question: str,
        git_info: dict[str, str],
        mode: str = "explain",
    ) -> str:
        parts: list[str] = []
        parts.append("<git_context>")
        for key, val in git_info.items():
            if val:
                parts.append(f"  {key}: {val}")
        parts.append("</git_context>")
        parts.append("")
        parts.append(f'<question mode="{mode}">')
        parts.append(question)
        parts.append("</question>")
        return "\n".join(parts)

    def build_service_prompt(
        self,
        service_name: str,
        service_status: str,
        mode: str = "explain",
    ) -> str:
        parts: list[str] = []
        parts.append(f'<service name="{service_name}">')
        parts.append(f"  status: {service_status}")
        parts.append(f"  mode: {mode}")
        parts.append("</service>")
        return "\n".join(parts)
