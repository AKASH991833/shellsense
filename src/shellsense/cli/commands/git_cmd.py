from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def git_explain_callback(
    git_command: str = "",
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    git_info = engine.get_git_status()

    if git_command:
        help_text = engine.explain_git_command(git_command)
        if help_text:
            formatter.print_panel(f"Git {git_command}", help_text[:2000])
        elif use_ai and engine.ai_ready and engine._ai is not None:
            context = engine.collect_terminal_context()
            system_prompt = engine.prompts.build_system_prompt("context")
            user_prompt = engine.prompts.build_git_prompt(
                f"Explain the git command: {git_command}\n\nProvide purpose, options, and examples.",
                {"branch": git_info.branch, "repo": git_info.repo_root},
                "explain",
            )
            try:
                response = engine._ai.generate(
                    prompt=user_prompt, system_prompt=system_prompt, provider=provider
                )
                console.print(Markdown(response.content))
            except Exception as e:
                formatter.print_error(f"AI explanation failed: {e}")
        else:
            formatter.print_warning(f"No documentation found for `git {git_command}`")
    else:
        formatter.print_service_status(git_info.to_dict())
        if git_info.status_lines:
            formatter.print_code_block("\n".join(git_info.status_lines[:20]), "diff")


def git_help_callback(
    git_command: str = "",
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    if git_command:
        help_text = engine.explain_git_command(git_command)
        if help_text:
            formatter.print_code_block(help_text[:3000], "text")
        elif use_ai and engine.ai_ready and engine._ai is not None:
            context = engine.collect_terminal_context()
            system_prompt = engine.prompts.build_system_prompt("context")
            user_prompt = engine.prompts.build_git_prompt(
                f"Provide help for: git {git_command}\n\nExplain common usage, options, and examples.",
                {},
                "help",
            )
            try:
                response = engine._ai.generate(
                    prompt=user_prompt, system_prompt=system_prompt, provider=provider
                )
                console.print(Markdown(response.content))
            except Exception as e:
                formatter.print_error(f"AI help failed: {e}")
        else:
            formatter.print_warning(f"No help available for `git {git_command}`")
    else:
        log = engine.get_git_log(10)
        if log:
            formatter.print_panel("Recent Git Log", log)
        else:
            formatter.print_warning("No git repository detected or no commits found.")
