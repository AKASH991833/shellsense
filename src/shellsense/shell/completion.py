from __future__ import annotations

from pathlib import Path

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

COMPLETION_SCRIPTS: dict[str, str] = {}


def _get_bash_completion() -> str:
    return """# ShellSense AI - Bash Completion
_shellsense_completion() {
    local cur prev words cword
    _init_completion || return

    if [[ $cword -eq 1 ]]; then
        local suggestions
        suggestions=$(shellsense suggest --limit 20 "$cur" 2>/dev/null | grep -oP '(?<=\\\\| )[^|]+(?= \\\\|)' | tr '\\n' ' ')
        COMPREPLY=($(compgen -W "$suggestions" -- "$cur"))
        return 0
    fi

    local cmd="${words[0]}"
    if [[ $cword -eq 2 ]]; then
        local suggestions
        suggestions=$(shellsense suggest --limit 20 "$cmd $cur" 2>/dev/null | grep -oP '(?<=\\\\| )[^|]+(?= \\\\|)' | tr '\\n' ' ')
        COMPREPLY=($(compgen -W "$suggestions" -- "$cur"))
        return 0
    fi

    COMPREPLY=($(compgen -f -- "$cur"))
}

complete -F _shellsense_completion shellsense
"""


def _get_zsh_completion() -> str:
    return """# ShellSense AI - Zsh Completion
_shellsense_completion() {
    local -a suggestions
    local cur="${words[-1]}"
    local cmd="${words[1]}"

    if [[ $CURRENT -eq 2 ]]; then
        suggestions=(${(f)"$(shellsense suggest --limit 20 "$cur" 2>/dev/null | grep -oP '(?<=\\\\| )[^|]+(?= \\\\|)')"})
        _describe 'command' suggestions
    elif [[ $CURRENT -eq 3 ]]; then
        suggestions=(${(f)"$(shellsense suggest --limit 20 "$cmd $cur" 2>/dev/null | grep -oP '(?<=\\\\| )[^|]+(?= \\\\|)')"})
        _describe 'subcommand' suggestions
    fi
}

compdef _shellsense_completion shellsense
"""


def _get_fish_completion() -> str:
    return """# ShellSense AI - Fish Completion
function __shellsense_complete
    set -l cmd (commandline -op)
    set -l cur (commandline -t)

    if test (count $cmd) -eq 1
        shellsense suggest --limit 20 $cur 2>/dev/null | string match -r '(?<=\\\\| )[^|]+(?= \\\\|)' | string trim
    else
        set -l full_cmd (string join " " $cmd)
        shellsense suggest --limit 20 "$full_cmd $cur" 2>/dev/null | string match -r '(?<=\\\\| )[^|]+(?= \\\\|)' | string trim
    end
end

complete -c shellsense -f -a "(__shellsense_complete)"
"""


def get_completion_script(shell: str) -> str:
    scripts = {
        "bash": _get_bash_completion,
        "zsh": _get_zsh_completion,
        "fish": _get_fish_completion,
    }
    generator = scripts.get(shell)
    if generator:
        return generator()
    return ""


def install_completion(shell: str, target_dir: Path | None = None) -> Path:
    content = get_completion_script(shell)
    if not content:
        raise ValueError(f"No completion script for shell: {shell}")

    if target_dir is None:
        base = Path.home() / ".shellsense"
        base.mkdir(parents=True, exist_ok=True)
        target_dir = base

    ext = {
        "bash": ".bash",
        "zsh": ".zsh",
        "fish": ".fish",
    }
    filename = f"shellsense-completion{ext.get(shell, '.sh')}"
    filepath = target_dir / filename
    filepath.write_text(content)
    logger.info("Completion script written to %s", filepath)
    return filepath


def remove_completion(filepath: Path) -> bool:
    if filepath.exists():
        filepath.unlink()
        logger.info("Removed completion script: %s", filepath)
        return True
    return False
