from __future__ import annotations

import os

from rich.console import Console
from rich.markdown import Markdown

from shellsense.cli.commands.shared import get_automation_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def generate_callback(
    template_type: str,
    output_dir: str = ".",
    use_ai: bool = False,
    requirement: str = "",
    **kwargs: str,
) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    if use_ai and requirement:
        formatter.print_info(f"Generating {template_type} with AI...")
        result = engine.generate_with_ai(template_type, requirement)
    else:
        formatter.print_info(f"Generating {template_type}...")
        result = engine.generate(template_type, **kwargs)

    if result.warnings:
        for w in result.warnings:
            formatter.print_warning(w)

    path = engine.export(result, output_dir)
    formatter.print_success(f"Generated: {path}")
    console.print(Markdown(f"```{result.extension.lstrip('.')}\n{result.content}\n```"))


def generate_interactive_callback(template_type: str, output_dir: str = ".") -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    questions = engine.interactive.get_questions_for(template_type)
    if not questions:
        formatter.print_error(f"No interactive questions defined for '{template_type}'")
        formatter.print_info(f"Try: ss generate {template_type} --help")
        return

    answers: dict[str, str] = {}
    from rich.prompt import Prompt

    for q in questions:
        default = q.get("default", "")
        prompt_text = f"{q['question']}"
        if default:
            prompt_text += f" [{default}]"
        answer = Prompt.ask(prompt_text, default=default)
        answers[q["key"]] = answer

    result = engine.generate(template_type, **answers)
    if result.warnings:
        for w in result.warnings:
            formatter.print_warning(w)

    path = engine.export(result, output_dir)
    formatter.print_success(f"Generated: {path}")
    formatter.print_code_block(result.content, result.extension.lstrip("."))


def list_templates_callback(category: str | None = None) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    if category:
        templates = engine.list_templates(category)
        title = f"Templates in '{category}'"
    else:
        templates = engine.list_templates()
        title = "All Templates"

    rows = [
        [t["name"], t["category"], t["description"][:60], ", ".join(t["tags"][:3])]
        for t in templates
    ]
    formatter.print_table(title, ["Name", "Category", "Description", "Tags"], rows)


def validate_callback(
    content: str | None = None, file_path: str | None = None, file_type: str = ""
) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    if file_path:
        if not os.path.isfile(file_path):
            formatter.print_error(f"File not found: {file_path}")
            return
        with open(file_path) as f:
            content = f.read()
        if not file_type:
            ext = os.path.splitext(file_path)[1].lstrip(".")
            file_type = ext

    if not content:
        formatter.print_error("No content to validate")
        return

    result = engine.validate(content, file_type)
    formatter.print_panel(
        "Validation Result", f"{'PASSED' if result.valid else 'FAILED'}"
    )
    if result.errors:
        for e in result.errors:
            formatter.print_error(e)
    if result.warnings:
        for w in result.warnings:
            formatter.print_warning(w)
    if result.suggestions:
        formatter.print_info("Suggestions:")
        for s in result.suggestions:
            formatter.print_info(f"  - {s}")


def optimize_callback(file_path: str) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    if not os.path.isfile(file_path):
        formatter.print_error(f"File not found: {file_path}")
        return

    with open(file_path) as f:
        content = f.read()
    ext = os.path.splitext(file_path)[1].lstrip(".")
    file_type = ext

    result = engine.optimize(content, file_type)
    formatter.print_info("Optimization complete")
    formatter.print_code_block(result.content, file_type)
    if result.warnings:
        for w in result.warnings:
            formatter.print_warning(w)


def document_callback(file_path: str) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    if not os.path.isfile(file_path):
        formatter.print_error(f"File not found: {file_path}")
        return

    with open(file_path) as f:
        content = f.read()
    ext = os.path.splitext(file_path)[1].lstrip(".")

    doc = engine.generate_documentation(content, ext)
    console.print(Markdown(doc))


def compare_callback(file_a: str, file_b: str) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    for fpath, label in [(file_a, "A"), (file_b, "B")]:
        if not os.path.isfile(fpath):
            formatter.print_error(f"File {label} not found: {fpath}")
            return

    with open(file_a) as f:
        content_a = f.read()
    with open(file_b) as f:
        content_b = f.read()

    ext = os.path.splitext(file_a)[1].lstrip(".")
    from shellsense.automation.generators.bash import GeneratedOutput

    output_a = GeneratedOutput(
        content=content_a, filename=os.path.basename(file_a), extension=f".{ext}"
    )
    output_b = GeneratedOutput(
        content=content_b, filename=os.path.basename(file_b), extension=f".{ext}"
    )

    comparison = engine.compare(output_a, output_b)
    console.print(Markdown(comparison))


def preview_callback(template_type: str, **kwargs: str) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    result = engine.generate(template_type, **kwargs)
    preview = engine.preview(result, max_lines=40)
    formatter.print_code_block(preview, "text")
    if result.warnings:
        for w in result.warnings:
            formatter.print_warning(w)


def export_callback(template_type: str, output_dir: str = ".", **kwargs: str) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    result = engine.generate(template_type, **kwargs)
    path = engine.export(result, output_dir)
    formatter.print_success(f"Exported to: {path}")


def search_templates_callback(query: str) -> None:
    engine = get_automation_engine()
    formatter = ResponseFormatter()

    results = engine.search_templates(query)
    if not results:
        formatter.print_info(f"No templates found matching '{query}'")
        return

    rows = [[r["name"], r["category"], r["description"][:60]] for r in results]
    formatter.print_table(
        f"Templates matching '{query}'", ["Name", "Category", "Description"], rows
    )
