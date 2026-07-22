from __future__ import annotations

from typing import Any, cast

from shellsense.automation.templates import TemplateInfo, TemplateLibrary
from shellsense.utils.logging import get_logger


class KnowledgeAPI:
    def __init__(self, knowledge_engine: Any) -> None:
        self._engine = knowledge_engine

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return cast("list[dict[str, Any]]", self._engine.search(query, limit=limit))

    def get_command(self, name: str) -> dict[str, Any] | None:
        return cast("dict[str, Any] | None", self._engine.get_command(name))

    def get_categories(self) -> list[str]:
        return cast("list[str]", self._engine.get_categories())


class SuggestionAPI:
    def __init__(self, suggest_func: Any) -> None:
        self._suggest = suggest_func

    def suggest(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return cast("list[dict[str, Any]]", self._suggest(query, limit=limit))


class AIAPI:
    def __init__(self, ai_engine: Any) -> None:
        self._ai = ai_engine

    def ask(self, question: str, style: str = "context") -> str:
        if hasattr(self._ai, "ask"):
            return cast(str, self._ai.ask(question, style))
        raise RuntimeError("AI engine not available")

    def get_providers(self) -> list[str]:
        if hasattr(self._ai, "get_providers"):
            return cast("list[str]", self._ai.get_providers())
        return []

    def is_enabled(self) -> bool:
        if hasattr(self._ai, "is_enabled"):
            return cast(bool, self._ai.is_enabled())
        return False


class ContextAPI:
    def __init__(self, context_collector: Any) -> None:
        self._collector = context_collector

    def get_current(self) -> dict[str, Any]:
        if hasattr(self._collector, "collect"):
            return cast("dict[str, Any]", self._collector.collect())
        return {}

    def get(self, key: str) -> Any:
        ctx = self.get_current()
        return ctx.get(key)


class AutomationAPI:
    def __init__(self, automation_engine: Any) -> None:
        self._engine = automation_engine

    def generate(self, template_type: str, **kwargs: Any) -> Any:
        return self._engine.generate(template_type, **kwargs)

    def list_templates(self, category: str | None = None) -> list[dict[str, Any]]:
        return cast("list[dict[str, Any]]", self._engine.list_templates(category))

    def validate(self, content: str, file_type: str) -> Any:
        return self._engine.validate(content, file_type)


class TemplateAPI:
    def __init__(self, template_library: TemplateLibrary) -> None:
        self._lib = template_library

    def list_templates(self, category: str | None = None) -> list[TemplateInfo]:
        return self._lib.list(category)

    def get(self, name: str) -> TemplateInfo | None:
        return self._lib.get(name)

    def search(self, query: str) -> list[TemplateInfo]:
        return cast("list[TemplateInfo]", self._lib.search(query))


class ConfigAPI:
    def __init__(self, config_manager: Any, plugin_id: str) -> None:
        self._config = config_manager
        self._plugin_id = plugin_id

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(f"plugins.{self._plugin_id}.{key}", default)

    def set(self, key: str, value: Any) -> None:
        self._config.set(f"plugins.{self._plugin_id}.{key}", value)

    def get_global(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)


class LoggerAPI:
    def __init__(self, plugin_id: str) -> None:
        self._logger = get_logger(f"plugin.{plugin_id}")

    def info(self, msg: str, *args: Any) -> None:
        self._logger.info(msg, *args)

    def warn(self, msg: str, *args: Any) -> None:
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        self._logger.error(msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        self._logger.debug(msg, *args)


class ShellAPI:
    def __init__(self, shell_integration: Any) -> None:
        self._shell = shell_integration

    def get_current_command(self) -> str:
        if hasattr(self._shell, "get_current_command"):
            return cast(str, self._shell.get_current_command())
        return ""

    def get_shell_type(self) -> str:
        if hasattr(self._shell, "get_shell_type"):
            return cast(str, self._shell.get_shell_type())
        return ""


class FormatterAPI:
    def __init__(self, formatter: Any) -> None:
        self._formatter = formatter

    def markdown(self, text: str) -> str:
        if hasattr(self._formatter, "render_markdown"):
            return cast(str, self._formatter.render_markdown(text))
        return text

    def table(self, headers: list[str], rows: list[list[str]]) -> str:
        if hasattr(self._formatter, "render_table"):
            return cast(str, self._formatter.render_table(headers, rows))
        return "\n".join([",".join(headers)] + [",".join(r) for r in rows])

    def code_block(self, code: str, language: str = "") -> str:
        if hasattr(self._formatter, "render_code_block"):
            return cast(str, self._formatter.render_code_block(code, language))
        return f"```{language}\n{code}\n```"


class PluginAPI:
    def __init__(
        self,
        plugin_id: str,
        knowledge_engine: Any = None,
        suggest_func: Any = None,
        ai_engine: Any = None,
        context_collector: Any = None,
        automation_engine: Any = None,
        template_library: TemplateLibrary | None = None,
        config_manager: Any = None,
        shell_integration: Any = None,
        formatter: Any = None,
    ) -> None:
        self.knowledge = KnowledgeAPI(knowledge_engine) if knowledge_engine else None
        self.suggestions = SuggestionAPI(suggest_func) if suggest_func else None
        self.ai = AIAPI(ai_engine) if ai_engine else None
        self.context = ContextAPI(context_collector) if context_collector else None
        self.automation = (
            AutomationAPI(automation_engine) if automation_engine else None
        )
        self.templates = TemplateAPI(template_library) if template_library else None
        self.config = ConfigAPI(config_manager, plugin_id) if config_manager else None
        self.log = LoggerAPI(plugin_id)
        self.shell = ShellAPI(shell_integration) if shell_integration else None
        self.formatter = FormatterAPI(formatter) if formatter else None
