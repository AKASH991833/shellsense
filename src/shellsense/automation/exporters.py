from __future__ import annotations

from pathlib import Path

from shellsense.automation.generators.bash import GeneratedOutput
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

OUTPUT_EXTENSIONS: dict[str, str] = {
    "sh": ".sh",
    "py": ".py",
    "service": ".service",
    "timer": ".timer",
    "socket": ".socket",
    "target": ".target",
    "Dockerfile": "Dockerfile",
    "compose.yaml": "compose.yaml",
    "yaml": ".yaml",
    "yml": ".yml",
    "conf": ".conf",
    "json": ".json",
    "md": ".md",
    "txt": ".txt",
    "toml": ".toml",
    "ini": ".ini",
    "cfg": ".cfg",
}


class AutomationExporter:
    def export(self, output: GeneratedOutput, directory: str = ".") -> str:
        target_dir = Path(directory).expanduser().resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = output.filename
        if not filename.endswith(output.extension) and output.extension:
            filename = f"{filename}{output.extension}"
        target_path = target_dir / filename
        target_path.write_text(output.content)
        logger.info("Exported to %s", target_path)
        return str(target_path)

    def export_with_warnings(
        self, output: GeneratedOutput, directory: str = "."
    ) -> tuple[str, list[str]]:
        path = self.export(output, directory)
        return path, output.warnings

    def to_markdown(self, output: GeneratedOutput) -> str:
        lines = [
            f"# {output.description}",
            "",
            f"**File:** `{output.filename}{output.extension}`",
            "",
            "```" + output.extension.lstrip(".") if output.extension else "",
            output.content,
            "```",
            "",
        ]
        if output.warnings:
            lines.append("## Warnings")
            for w in output.warnings:
                lines.append(f"- ⚠ {w}")
        return "\n".join(lines)

    def preview(self, output: GeneratedOutput, max_lines: int = 30) -> str:
        lines = output.content.split("\n")
        total = len(lines)
        show_lines = min(max_lines, total)
        preview_text = "\n".join(lines[:show_lines])
        if total > show_lines:
            preview_text += f"\n... ({total - show_lines} more lines)"
        return (
            f"# Preview: {output.filename}{output.extension}\n"
            f"# Description: {output.description}\n"
            f"# Total lines: {total}\n"
            f"# Warnings: {len(output.warnings)}\n"
            f"\n{preview_text}"
        )

    def supported_formats(self) -> list[str]:
        return sorted(OUTPUT_EXTENSIONS.keys())

    def get_extension_for(self, file_type: str) -> str:
        return OUTPUT_EXTENSIONS.get(file_type, ".txt")
