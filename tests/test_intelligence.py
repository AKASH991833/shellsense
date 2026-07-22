from __future__ import annotations

import os
import tempfile

from shellsense.intelligence.context_collectors import ContextCollector, TerminalContext
from shellsense.intelligence.engine import IntelligenceEngine
from shellsense.intelligence.error_analysis import (
    ERROR_PATTERNS,
    ErrorAnalysisResult,
    ErrorAnalyzer,
    get_exit_code,
    get_last_command,
)
from shellsense.intelligence.formatter import ResponseFormatter
from shellsense.intelligence.git_intelligence import GitIntelligence
from shellsense.intelligence.log_analysis import LOG_PATTERNS, LogAnalyzer
from shellsense.intelligence.privacy import (
    PRIVACY_DEFAULT_SETTINGS,
    PrivacyEngine,
    PrivacySettings,
)
from shellsense.intelligence.prompt_builder import (
    PromptBuilder,
)
from shellsense.intelligence.script_analysis import SECURITY_PATTERNS, ScriptAnalyzer
from shellsense.intelligence.service_intelligence import ServiceIntelligence


class TestTerminalContext:
    def test_context_has_default_values(self) -> None:
        ctx = TerminalContext()
        assert ctx.current_command == ""
        assert ctx.working_directory == ""
        assert ctx.shell == ""

    def test_context_to_dict(self) -> None:
        ctx = TerminalContext(
            current_command="ls",
            working_directory="/home",
            shell="/bin/bash",
            operating_system="linux",
        )
        d = ctx.to_dict()
        assert d["current_command"] == "ls"
        assert d["working_directory"] == "/home"
        assert d["operating_system"] == "linux"

    def test_context_summary(self) -> None:
        ctx = TerminalContext(
            operating_system="linux",
            distribution="Ubuntu",
            shell="/bin/zsh",
            working_directory="/tmp",
            git_branch="main",
        )
        summary = ctx.summary()
        assert "Ubuntu" in summary
        assert "main" in summary

    def test_collector_collect_shell(self) -> None:
        collector = ContextCollector()
        shell = collector.collect_shell()
        assert isinstance(shell, str)

    def test_collector_working_directory(self) -> None:
        collector = ContextCollector()
        cwd = collector.collect_working_directory()
        assert cwd == os.getcwd()

    def test_collector_operating_system(self) -> None:
        collector = ContextCollector()
        os_name = collector.collect_operating_system()
        assert os_name in ("linux", "darwin", "windows")

    def test_collector_kernel(self) -> None:
        collector = ContextCollector()
        kernel = collector.collect_kernel_version()
        assert isinstance(kernel, str)
        assert len(kernel) > 0

    def test_collector_user(self) -> None:
        collector = ContextCollector()
        user = collector.collect_user()
        assert isinstance(user, str)

    def test_collector_hostname(self) -> None:
        collector = ContextCollector()
        hostname = collector.collect_hostname()
        assert isinstance(hostname, str)

    def test_collector_virtual_env(self) -> None:
        collector = ContextCollector()
        venv = collector.collect_virtual_env()
        assert isinstance(venv, str)

    def test_collector_container(self) -> None:
        collector = ContextCollector()
        is_container = collector.collect_container()
        assert isinstance(is_container, bool)

    def test_collector_collect_all(self) -> None:
        collector = ContextCollector()
        ctx = collector.collect_all()
        assert isinstance(ctx, TerminalContext)
        assert ctx.operating_system in ("linux", "darwin", "windows")

    def test_collector_env_vars(self) -> None:
        collector = ContextCollector()
        env = collector.collect_env_vars()
        assert isinstance(env, dict)

    def test_collector_clear_cache(self) -> None:
        collector = ContextCollector()
        collector._history_cache = ["a", "b"]
        collector.clear_cache()
        assert collector._history_cache == []

    def test_collector_set_env_allowlist(self) -> None:
        collector = ContextCollector()
        collector.set_env_allowlist(["PATH", "HOME"])
        env = collector.collect_env_vars()
        assert "PATH" in env or "HOME" in env


class TestPrivacyEngine:
    def test_privacy_settings_defaults(self) -> None:
        settings = PrivacySettings()
        assert settings.is_allowed("share_current_directory") is True
        assert settings.is_allowed("share_user") is False

    def test_privacy_settings_allow(self) -> None:
        settings = PrivacySettings()
        settings.allow("share_user")
        assert settings.is_allowed("share_user") is True

    def test_privacy_settings_deny(self) -> None:
        settings = PrivacySettings()
        settings.deny("share_current_directory")
        assert settings.is_allowed("share_current_directory") is False

    def test_privacy_settings_toggle(self) -> None:
        settings = PrivacySettings()
        initial = settings.is_allowed("share_user")
        toggled = settings.toggle("share_user")
        assert toggled == (not initial)

    def test_privacy_settings_from_dict(self) -> None:
        settings = PrivacySettings.from_dict({"share_user": True})
        assert settings.is_allowed("share_user") is True
        assert settings.is_allowed("share_current_directory") is True

    def test_privacy_settings_get_allowed_keys(self) -> None:
        settings = PrivacySettings()
        allowed = settings.get_allowed_keys()
        assert "share_current_directory" in allowed
        assert "share_user" not in allowed

    def test_privacy_settings_get_denied_keys(self) -> None:
        settings = PrivacySettings()
        denied = settings.get_denied_keys()
        assert "share_user" in denied
        assert "share_current_directory" not in denied

    def test_privacy_engine_load_defaults(self) -> None:
        engine = PrivacyEngine()
        assert engine.is_allowed("current_directory") is True
        assert engine.is_allowed("user") is False

    def test_privacy_engine_allow_deny(self) -> None:
        engine = PrivacyEngine()
        engine.allow("user")
        assert engine.is_allowed("user") is True
        engine.deny("user")
        assert engine.is_allowed("user") is False

    def test_privacy_engine_toggle(self) -> None:
        engine = PrivacyEngine()
        start = engine.is_allowed("history")
        result = engine.toggle("history")
        assert result == (not start)

    def test_privacy_engine_filter_context(self) -> None:
        engine = PrivacyEngine()
        context = {
            "current_command": "ls",
            "user": "testuser",
            "working_directory": "/tmp",
            "recent_history": ["cmd1", "cmd2"],
            "env_vars": {"PATH": "/usr/bin"},
        }
        filtered = engine.filter_context(context)
        assert "current_command" in filtered
        assert "user" not in filtered

    def test_privacy_engine_reset(self) -> None:
        engine = PrivacyEngine()
        engine.allow("user")
        engine.reset_to_defaults()
        assert engine.is_allowed("user") is False

    def test_privacy_engine_get_summary(self) -> None:
        engine = PrivacyEngine()
        summary = engine.get_summary()
        assert isinstance(summary, dict)
        assert "share_current_directory" in summary

    def test_privacy_default_settings_structure(self) -> None:
        assert "share_current_directory" in PRIVACY_DEFAULT_SETTINGS
        assert "share_user" in PRIVACY_DEFAULT_SETTINGS
        assert "share_history" in PRIVACY_DEFAULT_SETTINGS


class TestPromptBuilder:
    def test_build_system_prompt_context(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("context")
        assert "ShellSense AI" in prompt

    def test_build_system_prompt_error(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("error")
        assert "error analysis" in prompt.lower()

    def test_build_system_prompt_script(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("script")
        assert "script" in prompt.lower()

    def test_build_system_prompt_log(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("log")
        assert "log" in prompt.lower()

    def test_build_system_prompt_default(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("unknown")
        assert "ShellSense AI" in prompt

    def test_build_context_block(self) -> None:
        builder = PromptBuilder()
        ctx = TerminalContext(
            operating_system="linux",
            shell="/bin/bash",
            working_directory="/home",
        )
        block = builder.build_context_block(ctx)
        assert "linux" in block
        assert "/bin/bash" in block

    def test_build_context_block_with_history(self) -> None:
        builder = PromptBuilder()
        ctx = TerminalContext(
            operating_system="linux",
            recent_history=["ls", "cd /tmp", "git status"],
        )
        block = builder.build_context_block(ctx)
        assert "ls" in block
        assert "git status" in block

    def test_build_question_prompt(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_question_prompt("How do I use grep?")
        assert "How do I use grep?" in prompt
        assert "<user_question>" in prompt

    def test_build_question_prompt_with_context(self) -> None:
        builder = PromptBuilder()
        ctx = TerminalContext(operating_system="linux")
        prompt = builder.build_question_prompt("List files", ctx)
        assert "linux" in prompt
        assert "List files" in prompt

    def test_build_error_analysis_prompt(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_error_analysis_prompt(
            "ls /root", "permission denied", exit_code=1
        )
        assert "ls /root" in prompt
        assert "permission denied" in prompt
        assert "Exit Code: 1" in prompt

    def test_build_script_analysis_prompt(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_script_analysis_prompt(
            "/tmp/test.sh", "#!/bin/bash\necho hello", mode="analyze"
        )
        assert "/tmp/test.sh" in prompt
        assert "echo hello" in prompt

    def test_build_log_analysis_prompt(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_log_analysis_prompt(
            "journald", "error: connection refused"
        )
        assert "connection refused" in prompt
        assert "journald" in prompt

    def test_build_git_prompt(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_git_prompt(
            "How to rebase?", {"branch": "main", "repo": "/repo"}
        )
        assert "rebase" in prompt
        assert "main" in prompt

    def test_build_service_prompt(self) -> None:
        builder = PromptBuilder()
        prompt = builder.build_service_prompt("nginx", "active", mode="explain")
        assert "nginx" in prompt
        assert "active" in prompt
        assert "explain" in prompt


class TestResponseFormatter:
    def test_format_markdown(self) -> None:
        formatter = ResponseFormatter()
        md = formatter.format_markdown("# Hello")
        assert md is not None

    def test_print_code_block(self) -> None:
        formatter = ResponseFormatter()
        formatter.print_code_block("ls -la", "bash")

    def test_print_warning(self) -> None:
        formatter = ResponseFormatter()
        formatter.print_warning("This is a warning")

    def test_print_error(self) -> None:
        formatter = ResponseFormatter()
        formatter.print_error("This is an error")

    def test_print_success(self) -> None:
        formatter = ResponseFormatter()
        formatter.print_success("Success!")

    def test_print_info(self) -> None:
        formatter = ResponseFormatter()
        formatter.print_info("Info message")

    def test_print_panel(self) -> None:
        formatter = ResponseFormatter()
        formatter.print_panel("Title", "Content")

    def test_print_table(self) -> None:
        formatter = ResponseFormatter()
        formatter.print_table("Test", ["A", "B"], [["1", "2"]])


class TestErrorAnalysis:
    def test_error_patterns_structure(self) -> None:
        assert "permission_denied" in ERROR_PATTERNS
        assert "command_not_found" in ERROR_PATTERNS
        assert "disk_full" in ERROR_PATTERNS

    def test_analyzer_match_known(self) -> None:
        analyzer = ErrorAnalyzer()
        result = analyzer._match_known_pattern("permission denied")
        assert result is not None
        assert result["category"] == "permission"

    def test_analyzer_match_unknown(self) -> None:
        analyzer = ErrorAnalyzer()
        result = analyzer._match_known_pattern("some random error text")
        assert result is None

    def test_analyze_permission_denied(self) -> None:
        analyzer = ErrorAnalyzer()
        result = analyzer.analyze("ls /root", "permission denied", exit_code=1)
        assert result.category == "permission"
        assert (
            "sudo" in result.suggested_fix.lower()
            or "permission" in result.suggested_fix.lower()
        )

    def test_analyze_command_not_found(self) -> None:
        analyzer = ErrorAnalyzer()
        result = analyzer.analyze("foo", "command not found: foo", exit_code=127)
        assert result.category == "missing_command"

    def test_analyze_network_unreachable(self) -> None:
        analyzer = ErrorAnalyzer()
        result = analyzer.analyze(
            "curl http://example.com", "network is unreachable", exit_code=7
        )
        assert result.category == "network"

    def test_analyze_disk_full(self) -> None:
        analyzer = ErrorAnalyzer()
        result = analyzer.analyze(
            "dd if=/dev/zero of=/tmp/test", "no space left on device", exit_code=1
        )
        assert result.category == "system"

    def test_analyze_port_in_use(self) -> None:
        analyzer = ErrorAnalyzer()
        result = analyzer.analyze(
            "python -m http.server 80", "address already in use", exit_code=98
        )
        assert result.category == "network"

    def test_error_analysis_result_to_dict(self) -> None:
        result = ErrorAnalysisResult(
            command="test",
            error_message="something broke",
            exit_code=1,
            category="unknown",
            severity="high",
            root_cause="test failed",
            suggested_fix="try again",
            alternative_commands=["cmd2"],
        )
        d = result.to_dict()
        assert d["command"] == "test"
        assert d["severity"] == "high"
        assert "cmd2" in d["alternative_commands"]

    def test_get_last_command(self) -> None:
        result = get_last_command()
        assert isinstance(result, str)

    def test_get_exit_code(self) -> None:
        code = get_exit_code()
        assert isinstance(code, int)


class TestScriptAnalysis:
    def test_analyze_simple_script(self) -> None:
        analyzer = ScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\necho hello\n")
            path = f.name
        try:
            result = analyzer.analyze(path)
            assert result.line_count == 3
            assert result.shebang == "#!/bin/bash"
        finally:
            os.unlink(path)

    def test_analyze_complex_script(self) -> None:
        analyzer = ScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\n")
            for i in range(60):
                f.write(f"echo line {i}\n")
            path = f.name
        try:
            result = analyzer.analyze(path)
            assert result.line_count == 62
        finally:
            os.unlink(path)

    def test_analyze_security_rm_rf(self) -> None:
        analyzer = ScriptAnalyzer()
        result = analyzer._find_security_issues("rm -rf /")
        assert len(result) > 0
        assert result[0]["severity"] == "critical"

    def test_analyze_security_fork_bomb(self) -> None:
        analyzer = ScriptAnalyzer()
        result = analyzer._find_security_issues(":(){ :|:& };:")
        assert len(result) > 0
        assert result[0]["severity"] == "critical"

    def test_analyze_security_curl_bash(self) -> None:
        analyzer = ScriptAnalyzer()
        result = analyzer._find_security_issues(
            "curl http://example.com/script.sh | bash"
        )
        assert len(result) > 0
        assert "piped curl" in result[0]["message"].lower()

    def test_analyze_bugs(self) -> None:
        analyzer = ScriptAnalyzer()
        bugs = analyzer._find_bugs(
            ["#!/bin/bash", "x=`echo hello`", "if [[ $x && $y ]]"]
        )
        assert len(bugs) >= 1

    def test_analyze_complexity_simple(self) -> None:
        analyzer = ScriptAnalyzer()
        assert analyzer._assess_complexity(["#!/bin/bash", "echo hi"]) == "simple"

    def test_analyze_complexity_moderate(self) -> None:
        analyzer = ScriptAnalyzer()
        lines = ["#!/bin/bash"] + [f"echo {i}" for i in range(60)]
        assert analyzer._assess_complexity(lines) == "moderate"

    def test_analyze_complexity_complex(self) -> None:
        analyzer = ScriptAnalyzer()
        lines = ["#!/bin/bash"] + [f"echo {i}" for i in range(250)]
        assert analyzer._assess_complexity(lines) == "complex"

    def test_analyze_performance_cat_grep(self) -> None:
        analyzer = ScriptAnalyzer()
        improvements = analyzer._find_performance_improvements(
            ["cat file | grep pattern"]
        )
        assert len(improvements) > 0

    def test_analyze_best_practices(self) -> None:
        analyzer = ScriptAnalyzer()
        practices = analyzer._find_best_practices(["echo hello"])
        assert len(practices) >= 1

    def test_security_patterns_defined(self) -> None:
        assert len(SECURITY_PATTERNS) > 0

    def test_script_to_dict(self) -> None:
        analyzer = ScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\necho hello\n")
            path = f.name
        try:
            result = analyzer.analyze(path)
            d = result.to_dict()
            assert d["shebang"] == "#!/bin/bash"
            assert d["line_count"] == 3
        finally:
            os.unlink(path)


class TestLogAnalysis:
    def test_log_patterns_structure(self) -> None:
        assert "systemd" in LOG_PATTERNS
        assert "nginx" in LOG_PATTERNS
        assert "ssh" in LOG_PATTERNS

    def test_analyze_empty_log(self) -> None:
        analyzer = LogAnalyzer()
        result = analyzer.analyze_log_file("/nonexistent/log.log")
        assert "not found" in result.summary.lower()

    def test_analyze_with_errors(self) -> None:
        analyzer = LogAnalyzer()
        from shellsense.intelligence.log_analysis import LogAnalysisResult

        result = LogAnalysisResult(
            source="test",
            content_lines=["line1", "error: out of memory", "line3"],
            suspicious_entries=[],
            severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 0},
            summary="",
            recommendations=[],
        )
        analyzer._analyze_content(result, "systemd")
        assert len(result.suspicious_entries) > 0

    def test_log_result_to_dict(self) -> None:
        from shellsense.intelligence.log_analysis import LogAnalysisResult

        result = LogAnalysisResult(
            source="test",
            content_lines=["line1", "line2"],
            suspicious_entries=[
                {"line": 1, "content": "error", "severity": "high", "label": "test"}
            ],
        )
        d = result.to_dict()
        assert d["source"] == "test"
        assert d["suspicious_count"] == 1


class TestGitIntelligence:
    def test_git_not_a_repo(self) -> None:
        git = GitIntelligence()
        result = git.get_status()
        assert isinstance(result.repo_root, str)

    def test_explain_command_not_found(self) -> None:
        git = GitIntelligence()
        result = git.explain_command("nonexistent-git-command-xyz")
        assert isinstance(result, str)


class TestServiceIntelligence:
    def test_service_status_nonexistent(self) -> None:
        svc = ServiceIntelligence()
        result = svc.get_status("nonexistent-service-xyz-12345")
        assert result.name == "nonexistent-service-xyz-12345"
        assert isinstance(result.active, bool)

    def test_service_result_to_dict(self) -> None:
        from shellsense.intelligence.service_intelligence import ServiceResult

        result = ServiceResult(
            name="nginx",
            status="active",
            active=True,
            enabled=True,
            pid=1234,
        )
        d = result.to_dict()
        assert d["name"] == "nginx"
        assert d["active"] is True


class TestIntelligenceEngine:
    def test_engine_creation(self) -> None:
        engine = IntelligenceEngine()
        assert engine.collector is not None
        assert engine.privacy is not None
        assert engine.prompts is not None
        assert engine.formatter is not None
        assert engine.ai_ready is False

    def test_engine_collect_context(self) -> None:
        engine = IntelligenceEngine()
        ctx = engine.collect_terminal_context()
        assert isinstance(ctx, TerminalContext)
        assert ctx.operating_system in ("linux", "darwin", "windows")

    def test_engine_build_context_block(self) -> None:
        engine = IntelligenceEngine()
        block = engine.build_context_block()
        assert isinstance(block, str)
        assert "<terminal_context>" in block

    def test_engine_build_question_prompt(self) -> None:
        engine = IntelligenceEngine()
        prompt = engine.build_question_prompt("How do I use ls?")
        assert "How do I use ls?" in prompt

    def test_engine_ask_ai_fallback(self) -> None:
        engine = IntelligenceEngine()
        result = engine.ask_ai("How do I use ls?")
        assert isinstance(result, str)

    def test_engine_analyze_error(self) -> None:
        engine = IntelligenceEngine()
        result = engine.analyze_error("ls /root", "permission denied")
        assert isinstance(result, ErrorAnalysisResult)

    def test_engine_analyze_error_unknown(self) -> None:
        engine = IntelligenceEngine()
        result = engine.analyze_error("foo", "unknown error")
        assert isinstance(result, ErrorAnalysisResult)

    def test_engine_analyze_script_not_found(self) -> None:
        engine = IntelligenceEngine()
        result = engine.analyze_script("/nonexistent/script.sh")
        assert isinstance(result, str) or result.potential_bugs

    def test_engine_get_git_status(self) -> None:
        engine = IntelligenceEngine()
        result = engine.get_git_status()
        assert isinstance(result.repo_root, str)

    def test_engine_get_service_status(self) -> None:
        engine = IntelligenceEngine()
        result = engine.get_service_status("nonexistent-service-xyz")
        assert isinstance(result.active, bool)

    def test_engine_explain_current_command(self) -> None:
        engine = IntelligenceEngine()
        result = engine.explain_current_command()
        assert result is None or isinstance(result, str)
