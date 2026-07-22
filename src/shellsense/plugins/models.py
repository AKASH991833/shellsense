from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class PluginState(enum.Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginLifecycleEvent(enum.Enum):
    INSTALL = "install"
    ENABLE = "enable"
    DISABLE = "disable"
    RELOAD = "reload"
    UPDATE = "update"
    UNINSTALL = "uninstall"
    SHUTDOWN = "shutdown"
    STARTUP = "startup"
    ERROR_RECOVERY = "error_recovery"


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    min_shellsense_version: str = "0.1.0"
    max_shellsense_version: str = ""
    dependencies: dict[str, str] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    platforms: list[str] = field(default_factory=lambda: ["linux"])
    shells: list[str] = field(default_factory=list)
    license: str = "MIT"
    homepage: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginManifest:
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            version=data.get("version", "0.1.0"),
            author=data.get("author", "Unknown"),
            description=data.get("description", ""),
            entry_point=data.get("entry_point", "plugin"),
            min_shellsense_version=data.get("min_shellsense_version", "0.1.0"),
            max_shellsense_version=data.get("max_shellsense_version", ""),
            dependencies=data.get("dependencies", {}),
            permissions=data.get("permissions", []),
            hooks=data.get("hooks", []),
            commands=data.get("commands", []),
            config_schema=data.get("config_schema", {}),
            platforms=data.get("platforms", ["linux"]),
            shells=data.get("shells", []),
            license=data.get("license", "MIT"),
            homepage=data.get("homepage", ""),
            tags=data.get("tags", []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "entry_point": self.entry_point,
            "min_shellsense_version": self.min_shellsense_version,
            "max_shellsense_version": self.max_shellsense_version,
            "dependencies": self.dependencies,
            "permissions": self.permissions,
            "hooks": self.hooks,
            "commands": self.commands,
            "config_schema": self.config_schema,
            "platforms": self.platforms,
            "shells": self.shells,
            "license": self.license,
            "homepage": self.homepage,
            "tags": self.tags,
        }


@dataclass
class PluginInfo:
    manifest: PluginManifest
    state: PluginState = PluginState.DISCOVERED
    path: str = ""
    enabled: bool = False
    error: str = ""
    load_count: int = 0
    last_loaded: float = 0.0
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def version(self) -> str:
        return self.manifest.version


class PluginBase:
    manifest: PluginManifest
    config: dict[str, Any] = {}
    _api: Any = None
    _logger: Any = None

    def __init__(self) -> None:
        pass

    def on_install(self) -> None:
        pass

    def on_uninstall(self) -> None:
        pass

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass

    def on_enable(self) -> None:
        pass

    def on_disable(self) -> None:
        pass

    def on_startup(self) -> None:
        pass

    def on_shutdown(self) -> None:
        pass

    def on_error_recovery(self, error: Exception) -> None:
        pass
