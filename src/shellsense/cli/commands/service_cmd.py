from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def service_explain_callback(
    service_name: str,
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    status = engine.get_service_status(service_name)
    formatter.print_service_status(status.to_dict())

    if status.knowledge_description:
        formatter.print_panel("About", status.knowledge_description)
    if status.knowledge_warnings:
        for w in status.knowledge_warnings:
            formatter.print_warning(w)
    if status.related_commands:
        formatter.print_info(f"\nRelated: {', '.join(status.related_commands)}")

    if use_ai and engine.ai_ready and engine._ai is not None:
        system_prompt = engine.prompts.build_system_prompt("context")
        user_prompt = engine.prompts.build_service_prompt(
            service_name, status.status, "explain"
        )
        try:
            response = engine._ai.generate(
                prompt=user_prompt, system_prompt=system_prompt, provider=provider
            )
            console.print(Markdown(response.content))
        except Exception as e:
            formatter.print_error(f"AI explanation failed: {e}")


def service_diagnose_callback(
    service_name: str,
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    status = engine.get_service_status(service_name)
    formatter.print_service_status(status.to_dict())

    formatter.print_info(f"\nRecent journal entries for {service_name}:")
    journal = engine.diagnose_service(service_name)
    if journal:
        formatter.print_code_block(journal[:3000], "text")
    else:
        formatter.print_info("No journal entries found.")

    if use_ai and engine.ai_ready and engine._ai is not None:
        system_prompt = engine.prompts.build_system_prompt("error")
        user_prompt = (
            f"Service: {service_name}\nStatus: {status.status}\n"
            f"Journal:\n{journal[:2000]}\n\n"
            f"Diagnose any issues with this service."
        )
        try:
            response = engine._ai.generate(
                prompt=user_prompt, system_prompt=system_prompt, provider=provider
            )
            console.print(Markdown(response.content))
        except Exception as e:
            formatter.print_error(f"AI diagnosis failed: {e}")
