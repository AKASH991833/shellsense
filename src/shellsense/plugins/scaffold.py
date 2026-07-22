from __future__ import annotations

import os
from typing import Any

from shellsense.plugins.manifest import VALID_PERMISSIONS
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

MANIFEST_TEMPLATE = """\
{{
    "id": "{plugin_id}",
    "name": "{name}",
    "version": "{version}",
    "author": "{author}",
    "description": "{description}",
    "entry_point": "plugin",
    "min_shellsense_version": "{min_version}",
    "max_shellsense_version": "",
    "dependencies": {dependencies},
    "permissions": {permissions},
    "hooks": {hooks},
    "commands": {commands},
    "config_schema": {config_schema},
    "platforms": ["linux"],
    "shells": [],
    "license": "{license}",
    "homepage": "",
    "tags": {tags}
}}
"""

PLUGIN_INIT_TEMPLATE = '''\
from shellsense.plugins import PluginBase, PluginAPI
from shellsense.plugins.hooks import HookEvent


class {class_name}(PluginBase):
    """{description}"""

    def on_load(self) -> None:
        self._api.log.info("Plugin loaded: {name}")

    def on_enable(self) -> None:
        self._api.log.info("Plugin enabled: {name}")

    def on_disable(self) -> None:
        self._api.log.info("Plugin disabled: {name}")

    def on_unload(self) -> None:
        self._api.log.info("Plugin unloaded: {name}")

    def on_startup(self) -> None:
        self._api.log.info("Plugin startup: {name}")


def register_hooks(api: PluginAPI) -> None:
    pass


def register_commands(api: PluginAPI) -> None:
    pass
'''

PLUGIN_CONFIG_TEMPLATE = """\
{{
    "enabled": true,
    "setting": "value"
}}
"""

README_TEMPLATE = """\
# {name}

{description}

## Version

{version}

## Author

{author}

## Requirements

- ShellSense >= {min_version}

## Installation

```bash
ss plugin install /path/to/{plugin_id}
```

## Permissions

{permissions_text}

## Commands

{commands_text}
"""

TEST_TEMPLATE = """\
from {plugin_id} import plugin


def test_plugin_load() -> None:
    assert plugin is not None
"""


def scaffold_plugin(
    plugin_id: str,
    output_dir: str,
    name: str = "",
    description: str = "",
    author: str = "Anonymous",
    version: str = "0.1.0",
    min_version: str = "0.1.0",
    license: str = "MIT",
    permissions: list[str] | None = None,
    hooks: list[str] | None = None,
    tags: list[str] | None = None,
) -> str:
    name = name or plugin_id
    description = description or f"{name} plugin for ShellSense AI"
    permissions = permissions or []
    hooks_list = hooks or []
    tags = tags or []

    permissions = [p for p in permissions if p in VALID_PERMISSIONS]

    plugin_dir = os.path.join(output_dir, plugin_id)
    commands_dir = os.path.join(plugin_dir, "commands")
    hooks_dir = os.path.join(plugin_dir, "hooks")
    tests_dir = os.path.join(plugin_dir, "tests")
    docs_dir = os.path.join(plugin_dir, "docs")

    os.makedirs(commands_dir, exist_ok=True)
    os.makedirs(hooks_dir, exist_ok=True)
    os.makedirs(tests_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    class_name = "".join(
        part.capitalize() for part in plugin_id.replace("-", "_").split("_")
    )

    manifest_content = MANIFEST_TEMPLATE.format(
        plugin_id=plugin_id,
        name=name,
        version=version,
        author=author,
        description=description,
        min_version=min_version,
        dependencies="{}",
        permissions=json_dumps(permissions),
        hooks=json_dumps(hooks_list),
        commands="[]",
        config_schema="{}",
        license=license,
        tags=json_dumps(tags),
    )
    _write(os.path.join(plugin_dir, "manifest.json"), manifest_content)

    plugin_content = PLUGIN_INIT_TEMPLATE.format(
        class_name=class_name,
        description=description,
        name=name,
    )
    _write(os.path.join(plugin_dir, "plugin.py"), plugin_content)

    _write(os.path.join(plugin_dir, "config.json"), PLUGIN_CONFIG_TEMPLATE)

    permissions_text = (
        "\n".join(f"- {p}" for p in permissions) if permissions else "- None required"
    )
    commands_text = "This plugin does not define any CLI commands."

    readme_content = README_TEMPLATE.format(
        name=name,
        description=description,
        version=version,
        author=author,
        min_version=min_version,
        plugin_id=plugin_id,
        permissions_text=permissions_text,
        commands_text=commands_text,
    )
    _write(os.path.join(plugin_dir, "README.md"), readme_content)

    test_content = TEST_TEMPLATE.format(plugin_id=plugin_id)
    _write(os.path.join(tests_dir, "test_plugin.py"), test_content)

    _write(
        os.path.join(commands_dir, "__init__.py"), "# CLI commands for this plugin\n"
    )
    _write(os.path.join(hooks_dir, "__init__.py"), "# Hook handlers for this plugin\n")
    _write(
        os.path.join(docs_dir, "index.md"), f"# {name} Documentation\n\n{description}\n"
    )

    _write(
        os.path.join(plugin_dir, "__init__.py"),
        f"from {plugin_id}.plugin import {class_name}\n\n__all__ = ['{class_name}']\n",
    )

    logger.info("Scaffolded plugin '%s' at %s", plugin_id, plugin_dir)
    return plugin_dir


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content.lstrip("\n"))


def json_dumps(obj: Any) -> str:
    import json

    return json.dumps(obj)
