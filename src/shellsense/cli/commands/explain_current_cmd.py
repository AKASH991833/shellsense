from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def explain_current_callback(use_ai: bool = False, provider: str | None = None) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    result = engine.explain_current_command()

    if result:
        console.print(Markdown(result))
        return

    if use_ai and engine.ai_ready and engine._ai is not None:
        cmd = engine.collector.collect_current_command()
        if not cmd:
            formatter.print_warning("Could not detect current command.")
            return
        context = engine.collect_terminal_context()
        system_prompt = engine.prompts.build_system_prompt("context")
        user_prompt = (
            f"{engine.build_context_block(context)}\n\n"
            f"Explain the command `{cmd}` in detail. Include: purpose, arguments, "
            f"flags, risks, examples, related commands, and safer alternatives."
        )
        try:
            response = engine._ai.generate(
                prompt=user_prompt, system_prompt=system_prompt, provider=provider
            )
            console.print(Markdown(response.content))
        except Exception as e:
            formatter.print_error(f"AI explanation failed: {e}")
    else:
        formatter.print_warning(
            "Could not find command in knowledge base. Use `ss ai config` to enable AI."
        )
