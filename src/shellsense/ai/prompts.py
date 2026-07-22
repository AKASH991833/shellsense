from __future__ import annotations

from typing import Any

SYSTEM_PROMPTS: dict[str, str] = {
    "default": (
        "You are ShellSense AI, a helpful Linux terminal assistant. "
        "Provide concise, accurate answers about Linux commands, shell usage, "
        "and system administration. Keep responses brief and actionable."
    ),
    "expert": (
        "You are an expert Linux system administrator assistant. "
        "Provide detailed, technically precise answers with command examples. "
        "Include relevant flags, options, and edge cases."
    ),
    "beginner": (
        "You are a friendly Linux tutor for beginners. "
        "Explain concepts simply, avoid jargon when possible, "
        "and provide step-by-step instructions."
    ),
}


class PromptEngine:
    def __init__(self) -> None:
        self._templates: dict[str, str] = {}
        self._variables: dict[str, str] = {}

    def register_template(self, name: str, template: str) -> None:
        self._templates[name] = template

    def get_template(self, name: str) -> str:
        return self._templates.get(name, "")

    def render(self, name: str, variables: dict[str, Any] | None = None) -> str:
        template = self._templates.get(name, "")
        if not template:
            return ""
        merged = dict(self._variables)
        if variables:
            merged.update(variables)
        result = template
        for key, value in merged.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def set_variable(self, key: str, value: str) -> None:
        self._variables[key] = value

    def get_system_prompt(self, style: str = "default") -> str:
        return SYSTEM_PROMPTS.get(style, SYSTEM_PROMPTS["default"])

    def create_command_explain_prompt(self, command: str) -> str:
        return f"Explain the Linux command '{command}' in detail. Include syntax, common options, and examples."

    def create_command_suggest_prompt(self, partial: str) -> str:
        return f"Suggest Linux commands matching '{partial}'. List the most likely commands."

    def create_error_help_prompt(self, command: str, error: str) -> str:
        return (
            f"I ran '{command}' and got this error: '{error}'. "
            f"What does this error mean and how can I fix it?"
        )
