from __future__ import annotations

from rich.console import Console

from shellsense.cli.commands.shared import get_automation_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def template_list_callback(category: str | None = None) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    templates = engine.list_templates(category)
    if not templates:
        formatter.print_info("No templates found")
        return

    formatter.print_info(f"Found {len(templates)} templates")
    for t in templates:
        formatter.print_info(f"  [bold]{t['name']}[/bold] ({t['category']})")
        formatter.print_info(f"    {t['description']}")
        if t.get("tags"):
            formatter.print_info(f"    Tags: {', '.join(t['tags'])}")


def template_show_callback(name: str) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    tpl = engine.get_template(name)
    if tpl is None:
        formatter.print_error(f"Template not found: {name}")
        return

    formatter.print_panel(
        tpl["name"], f"Category: {tpl['category']}\n{tpl['description']}"
    )
    if tpl.get("tags"):
        formatter.print_info(f"Tags: {', '.join(tpl['tags'])}")
    formatter.print_info(f"Extension: {tpl.get('output_extension', '')}")
    formatter.print_info(f"Version: {tpl.get('version', '1.0.0')}")
    formatter.print_code_block(tpl.get("content", ""), tpl["category"])


def template_categories_callback() -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    categories = engine.templates.list_categories()
    rows = [[c, str(len(engine.templates.list(c)))] for c in categories]
    formatter.print_table("Template Categories", ["Category", "Count"], rows)
