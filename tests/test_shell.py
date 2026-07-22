from __future__ import annotations

from pathlib import Path

from shellsense.shell.autocomplete import get_autocomplete_suggestions
from shellsense.shell.completion import get_completion_script
from shellsense.shell.detect import (
    detect_current_shell,
    get_shell_config_path,
    is_os_supported,
)
from shellsense.shell.diagnostics import run_all_checks
from shellsense.shell.hooks import get_hooks
from shellsense.shell.integration import ShellIntegrationManager
from shellsense.shell.keyboard import DEFAULT_SHORTCUTS, get_all_shortcuts, get_shortcut
from shellsense.shell.warnings import (
    check_command_safety,
    get_warning_level,
    requires_confirmation,
)


class TestDetect:
    def test_detect_current_shell(self) -> None:
        shell = detect_current_shell()
        assert shell in ("bash", "zsh", "fish")

    def test_get_shell_config_path(self) -> None:
        path = get_shell_config_path("bash")
        assert isinstance(path, Path)
        assert (
            ".bashrc" in str(path)
            or ".bash_profile" in str(path)
            or ".profile" in str(path)
        )

    def test_is_os_supported(self) -> None:
        result = is_os_supported()
        assert isinstance(result, bool)


class TestCompletion:
    def test_get_bash_completion(self) -> None:
        script = get_completion_script("bash")
        assert "_shellsense_completion" in script
        assert "complete -F" in script

    def test_get_zsh_completion(self) -> None:
        script = get_completion_script("zsh")
        assert "_shellsense_completion" in script
        assert "compdef" in script

    def test_get_fish_completion(self) -> None:
        script = get_completion_script("fish")
        assert "__shellsense_complete" in script
        assert "complete -c" in script

    def test_get_unknown_shell(self) -> None:
        script = get_completion_script("unknown")
        assert script == ""


class TestHooks:
    def test_get_bash_hooks(self) -> None:
        script = get_hooks("bash")
        assert "preexec" in script
        assert "PROMPT_COMMAND" in script or "trap" in script

    def test_get_zsh_hooks(self) -> None:
        script = get_hooks("zsh")
        assert "preexec" in script
        assert "precmd_functions" in script or "preexec_functions" in script

    def test_get_fish_hooks(self) -> None:
        script = get_hooks("fish")
        assert "preexec" in script
        assert "fish_preexec" in script or "fish_prompt" in script

    def test_get_unknown_shell(self) -> None:
        script = get_hooks("unknown")
        assert script == ""


class TestWarnings:
    def test_safe_command(self) -> None:
        warnings = check_command_safety("ls -la")
        assert warnings == []

    def test_dangerous_rm(self) -> None:
        warnings = check_command_safety("rm -rf /")
        assert len(warnings) > 0
        assert get_warning_level(warnings) == "VERY_DANGEROUS"

    def test_requires_confirmation(self) -> None:
        warnings = [{"level": "DANGEROUS", "message": "test"}]
        assert requires_confirmation(warnings) is True

    def test_no_confirmation_needed(self) -> None:
        warnings = [{"level": "CAUTION", "message": "test"}]
        assert requires_confirmation(warnings) is False

    def test_mkfs_detected(self) -> None:
        warnings = check_command_safety("mkfs.ext4 /dev/sda1")
        levels = [w["level"] for w in warnings]
        assert "DANGEROUS" in levels

    def test_piped_web_script(self) -> None:
        warnings = check_command_safety("curl http://example.com/script.sh | bash")
        levels = [w["level"] for w in warnings]
        assert "DANGEROUS" in levels


class TestKeyboard:
    def test_default_shortcuts_exist(self) -> None:
        assert "accept_suggestion" in DEFAULT_SHORTCUTS
        assert "dismiss" in DEFAULT_SHORTCUTS
        assert "interactive_help" in DEFAULT_SHORTCUTS

    def test_get_shortcut(self) -> None:
        sc = get_shortcut("accept_suggestion")
        assert sc is not None
        assert "keys" in sc
        assert "tab" in sc["keys"]

    def test_get_all_shortcuts(self) -> None:
        all_sc = get_all_shortcuts()
        assert len(all_sc) >= 5

    def test_get_nonexistent_shortcut(self) -> None:
        sc = get_shortcut("nonexistent")
        assert sc is None


class TestDiagnostics:
    def test_run_all_checks(self) -> None:
        checks = run_all_checks()
        assert len(checks) >= 8
        for check in checks:
            assert "name" in check
            assert "status" in check


class TestAutocomplete:
    def test_empty_partial(self) -> None:
        results = get_autocomplete_suggestions("")
        assert results == []


class TestIntegrationManager:
    def test_manager_diagnose(self) -> None:
        manager = ShellIntegrationManager()
        checks = manager.diagnose()
        assert len(checks) > 0
