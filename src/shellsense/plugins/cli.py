from __future__ import annotations

import os

from rich.console import Console
from rich.table import Table

from shellsense.plugins.exceptions import PluginError
from shellsense.plugins.manager import PluginManager
from shellsense.plugins.permissions import PERMISSION_GROUPS
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def get_plugin_manager() -> PluginManager:
    from shellsense.cli.commands.shared import get_plugin_manager as _get_pm

    return _get_pm()


def plugin_list_callback() -> None:
    pm = get_plugin_manager()
    pm.discover()
    plugins = pm.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins found.[/]")
        console.print(f"  Plugin directory: {pm.plugins_dir}")
        return

    table = Table(title="ShellSense Plugins")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version", style="blue")
    table.add_column("State", style="yellow")
    table.add_column("Author")

    for p in plugins:
        state = "[green]enabled[/]" if p.enabled else "[dim]disabled[/]"
        table.add_row(p.id, p.name, p.version, state, p.manifest.author)
    console.print(table)


def plugin_info_callback(plugin_id: str) -> None:
    pm = get_plugin_manager()
    try:
        info = pm.get_plugin(plugin_id)
    except PluginError as e:
        console.print(f"[red]{e}[/]")
        return

    m = info.manifest
    console.print(f"[bold]Plugin:[/] {m.name} ({m.id})")
    console.print(f"[bold]Version:[/] {m.version}")
    console.print(f"[bold]Author:[/] {m.author}")
    console.print(f"[bold]Description:[/] {m.description}")
    console.print(
        f"[bold]State:[/] {'[green]enabled[/]' if info.enabled else '[dim]disabled[/]'}"
    )
    console.print(f"[bold]Path:[/] {info.path}")
    console.print(f"[bold]Entry Point:[/] {m.entry_point}")
    console.print(f"[bold]Min ShellSense:[/] {m.min_shellsense_version}")
    console.print(f"[bold]License:[/] {m.license}")

    if m.dependencies:
        console.print("[bold]Dependencies:[/]")
        for dep_id, dep_ver in m.dependencies.items():
            console.print(f"  - {dep_id} ({dep_ver})")

    if m.permissions:
        console.print("[bold]Permissions:[/]")
        for perm in m.permissions:
            granted = pm.get_plugin_permissions(plugin_id)
            status = "[green]granted[/]" if perm in granted else "[red]not granted[/]"
            desc = PERMISSION_GROUPS.get(perm, perm)
            console.print(f"  - {desc} ({status})")

    if m.hooks:
        console.print(f"[bold]Hooks:[/] {', '.join(m.hooks)}")

    health = pm.get_health(plugin_id)
    if health:
        console.print(f"[bold]Health:[/] {health.status}")
        if health.last_error:
            console.print(f"[bold]Last Error:[/] [red]{health.last_error}[/]")
        if health.error_count:
            console.print(f"[bold]Error Count:[/] {health.error_count}")


def plugin_enable_callback(plugin_id: str) -> None:
    pm = get_plugin_manager()
    try:
        pm.enable(plugin_id)
        console.print(f"[green]Enabled plugin: {plugin_id}[/]")
    except PluginError as e:
        console.print(f"[red]{e}[/]")


def plugin_disable_callback(plugin_id: str) -> None:
    pm = get_plugin_manager()
    try:
        pm.disable(plugin_id)
        console.print(f"[green]Disabled plugin: {plugin_id}[/]")
    except PluginError as e:
        console.print(f"[red]{e}[/]")


def plugin_reload_callback(plugin_id: str) -> None:
    pm = get_plugin_manager()
    try:
        pm.reload(plugin_id)
        console.print(f"[green]Reloaded plugin: {plugin_id}[/]")
    except PluginError as e:
        console.print(f"[red]{e}[/]")


def plugin_install_callback(path: str) -> None:
    pm = get_plugin_manager()
    try:
        if not os.path.isdir(path):
            # Try as a plugin ID from examples

            examples_dir = os.path.join(
                os.path.dirname(__file__), "..", "plugins", "examples"
            )
            candidate = os.path.join(examples_dir, path)
            if os.path.isdir(candidate):
                path = candidate
            else:
                console.print(f"[red]Plugin path not found: {path}[/]")
                return

        info = pm.install(path)
        console.print(f"[green]Installed plugin: {info.name} v{info.version}[/]")
        console.print(f"  ID: {info.id}")
        console.print(f"  Path: {info.path}")

        if info.manifest.permissions:
            console.print("\n[yellow]Required permissions:[/]")
            for perm in info.manifest.permissions:
                desc = PERMISSION_GROUPS.get(perm, perm)
                console.print(f"  - {desc}")

            from rich.prompt import Confirm

            grant_all = Confirm.ask(
                "Grant all required permissions?",
                default=True,
            )
            if grant_all:
                for perm in info.manifest.permissions:
                    pm.grant_permission(info.id, perm)
                console.print("[green]Permissions granted.[/]")
            else:
                console.print(
                    "[yellow]Permissions not granted. Use 'shellsense plugin permissions' to manage.[/]"
                )
    except (PluginError, FileExistsError) as e:
        console.print(f"[red]{e}[/]")


def plugin_remove_callback(plugin_id: str) -> None:
    pm = get_plugin_manager()
    try:
        pm.remove(plugin_id)
        console.print(f"[green]Removed plugin: {plugin_id}[/]")
    except PluginError as e:
        console.print(f"[red]{e}[/]")


def plugin_validate_callback(plugin_id: str) -> None:
    pm = get_plugin_manager()
    pm.discover()
    issues = pm.validate_plugin(plugin_id)
    if not issues:
        console.print(f"[green]Plugin '{plugin_id}' is valid.[/]")
    else:
        console.print(f"[red]Plugin '{plugin_id}' has {len(issues)} issue(s):[/]")
        for issue in issues:
            console.print(f"  - {issue}")


def plugin_doctor_callback() -> None:
    pm = get_plugin_manager()
    pm.discover()
    plugins = pm.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins installed.[/]")
        console.print(f"  Plugin directory: {pm.plugins_dir}")
        return

    console.print("[bold]Plugin Doctor Report[/]\n")
    all_ok = True
    for p in plugins:
        issues = pm.validate_plugin(p.id)
        if issues:
            all_ok = False
            console.print(f"[red]✗ {p.name} ({p.id})[/]")
            for issue in issues:
                console.print(f"    - {issue}")
        else:
            console.print(f"[green]✓ {p.name} ({p.id}) v{p.version}[/]")

    summary = pm.get_health_summary()
    if summary:
        console.print("\n[bold]Health Summary:[/]")
        for s in summary:
            status_color = "green" if s["status"] in ("loaded", "enabled") else "red"
            console.print(
                f"  {s['plugin_id']}: [{status_color}]{s['status']}[/]"
                f" (errors: {s['error_count']})"
            )

    if all_ok:
        console.print(f"\n[green]All {len(plugins)} plugins healthy.[/]")
    else:
        console.print("\n[yellow]Some plugins have issues (see above).[/]")


def plugin_create_callback(
    plugin_id: str,
    output_dir: str,
    name: str = "",
    description: str = "",
    author: str = "",
    version: str = "0.1.0",
    permissions: list[str] | None = None,
) -> None:
    from shellsense.plugins.scaffold import scaffold_plugin

    try:
        path = scaffold_plugin(
            plugin_id=plugin_id,
            output_dir=output_dir,
            name=name,
            description=description,
            author=author or os.environ.get("USER", "Anonymous"),
            version=version,
            permissions=permissions or [],
        )
        console.print(f"[green]Created plugin project at: {path}[/]")
        console.print("\nNext steps:")
        console.print(f"  1. cd {path}")
        console.print("  2. Edit plugin.py to add functionality")
        console.print("  3. Edit manifest.json to configure metadata")
        console.print(f"  4. ss plugin install {path}")
    except Exception as e:
        console.print(f"[red]Failed to create plugin: {e}[/]")


def plugin_scaffold_callback(
    plugin_id: str,
    output_dir: str = ".",
    template: str = "basic",
) -> None:
    from shellsense.plugins.scaffold import scaffold_plugin

    try:
        path = scaffold_plugin(
            plugin_id=plugin_id,
            output_dir=output_dir,
            name=plugin_id,
            description=f"{plugin_id} plugin for ShellSense AI",
            author=os.environ.get("USER", "Anonymous"),
        )
        console.print(f"[green]Scaffolded plugin at: {path}[/]")
    except Exception as e:
        console.print(f"[red]{e}[/]")


def plugin_permissions_callback(plugin_id: str | None = None) -> None:
    pm = get_plugin_manager()

    if plugin_id:
        try:
            info = pm.get_plugin(plugin_id)
        except PluginError as e:
            console.print(f"[red]{e}[/]")
            return

        required = info.manifest.permissions
        granted = pm.get_plugin_permissions(plugin_id)

        console.print(f"[bold]Permissions for {info.name}:[/]\n")
        for perm in PERMISSION_GROUPS:
            is_required = perm in required
            is_granted = perm in granted
            status = "[green]granted[/]" if is_granted else "[red]not granted[/]"
            req = "[bold](required)[/]" if is_required else ""
            console.print(f"  {PERMISSION_GROUPS[perm]}: {status} {req}")
    else:
        console.print("[bold]Available Permissions:[/]\n")
        for perm, desc in PERMISSION_GROUPS.items():
            console.print(f"  {perm}: {desc}")
