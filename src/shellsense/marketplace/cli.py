from __future__ import annotations

import os

from rich.console import Console
from rich.table import Table

from shellsense.marketplace.exceptions import MarketplaceError
from shellsense.marketplace.marketplace import MarketplaceManager
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def get_marketplace_manager() -> MarketplaceManager:
    from shellsense.cli.commands.shared import get_marketplace_manager as _get_mm

    return _get_mm()


def marketplace_search_callback(
    query: str, category: str = "", sort_by: str = "name"
) -> None:
    mm = get_marketplace_manager()
    result = mm.search(query, category=category, sort_by=sort_by)

    if not result.results:
        console.print("[yellow]No plugins found matching your query.[/]")
        return

    table = Table(title=f"Marketplace Search: '{query}' ({result.total} results)")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version", style="blue")
    table.add_column("Author")
    table.add_column("Downloads")
    table.add_column("Rating")

    for p in result.results:
        rating_str = f"{p.rating:.1f}" if p.rating else "-"
        table.add_row(p.id, p.name, p.version, p.author, str(p.downloads), rating_str)
    console.print(table)

    if result.facets["categories"]:
        console.print(
            f"\n[bold]Categories:[/] {', '.join(result.facets['categories'])}"
        )


def marketplace_info_callback(plugin_id: str) -> None:
    mm = get_marketplace_manager()
    plugin = mm.info(plugin_id)

    if plugin is None:
        console.print(f"[red]Plugin '{plugin_id}' not found in marketplace.[/]")
        return

    console.print(f"[bold]Plugin:[/] {plugin.name} ({plugin.id})")
    console.print(f"[bold]Version:[/] {plugin.version}")
    console.print(f"[bold]Author:[/] {plugin.author}")
    console.print(f"[bold]Description:[/] {plugin.description}")
    console.print(f"[bold]License:[/] {plugin.license}")
    console.print(f"[bold]Publisher:[/] {plugin.publisher or 'Unknown'}")
    console.print(f"[bold]Downloads:[/] {plugin.downloads}")
    console.print(
        f"[bold]Rating:[/] {plugin.rating:.1f}"
        if plugin.rating
        else "[bold]Rating:[/] N/A"
    )

    if plugin.categories:
        console.print(f"[bold]Categories:[/] {', '.join(plugin.categories)}")
    if plugin.tags:
        console.print(f"[bold]Tags:[/] {', '.join(plugin.tags)}")
    if plugin.dependencies:
        console.print("[bold]Dependencies:[/]")
        for dep_id, dep_ver in plugin.dependencies.items():
            console.print(f"  - {dep_id} ({dep_ver})")
    if plugin.permissions:
        console.print("[bold]Permissions:[/]")
        from shellsense.plugins.permissions import PERMISSION_GROUPS

        for perm in plugin.permissions:
            desc = PERMISSION_GROUPS.get(perm, perm)
            console.print(f"  - {desc}")
    if plugin.homepage:
        console.print(f"[bold]Homepage:[/] {plugin.homepage}")
    if plugin.source_url:
        console.print(f"[bold]Source:[/] {plugin.source_url}")
    if plugin.documentation_url:
        console.print(f"[bold]Documentation:[/] {plugin.documentation_url}")


def marketplace_install_callback(
    plugin_id: str, version: str = "", dry_run: bool = False
) -> None:
    mm = get_marketplace_manager()

    if dry_run:
        console.print(f"[yellow]Dry run: would install '{plugin_id}'[/]")
        result = mm.install(plugin_id, version=version, dry_run=True)
        if result.dependencies:
            console.print(f"  Dependencies: {', '.join(result.dependencies)}")
        if result.warnings:
            for w in result.warnings:
                console.print(f"  [yellow]Warning: {w}[/]")
        if result.errors:
            for e in result.errors:
                console.print(f"  [red]Error: {e}[/]")
        else:
            console.print("[green]Dry run completed successfully.[/]")
        return

    console.print(f"Installing '{plugin_id}'...")
    result = mm.install(plugin_id, version=version)

    if result.success:
        console.print(f"[green]Installed '{plugin_id}' v{result.version}[/]")
        if result.dependencies:
            console.print(f"  Dependencies: {', '.join(result.dependencies)}")
        if result.path:
            console.print(f"  Path: {result.path}")
    else:
        for e in result.errors:
            console.print(f"[red]{e}[/]")

    if result.warnings:
        for w in result.warnings:
            console.print(f"[yellow]Warning: {w}[/]")


def marketplace_remove_callback(plugin_id: str) -> None:
    mm = get_marketplace_manager()
    result = mm.remove(plugin_id)

    if result.success:
        console.print(f"[green]Removed plugin '{plugin_id}'[/]")
    else:
        for e in result.errors:
            console.print(f"[red]{e}[/]")


def marketplace_update_callback(
    plugin_id: str | None = None, all_plugins: bool = False
) -> None:
    mm = get_marketplace_manager()

    if plugin_id:
        console.print(f"Checking updates for '{plugin_id}'...")
        result = mm.update(plugin_id)
        if result.success:
            if result.old_version == result.new_version:
                console.print(
                    f"[green]'{plugin_id}' is up to date ({result.old_version})[/]"
                )
            else:
                console.print(
                    f"[green]Updated '{plugin_id}': {result.old_version} -> {result.new_version}[/]"
                )
        else:
            for e in result.errors:
                console.print(f"[red]{e}[/]")
    elif all_plugins:
        console.print("Checking for updates...")
        updates = mm.check_updates()
        if not updates:
            console.print("[green]All plugins are up to date.[/]")
        else:
            table = Table(title="Available Updates")
            table.add_column("Plugin", style="cyan")
            table.add_column("Current", style="yellow")
            table.add_column("Available", style="green")
            for u in updates:
                table.add_row(u.plugin_id, u.old_version, u.new_version)
            console.print(table)
    else:
        installed = mm.list_installed()
        if not installed:
            console.print("[yellow]No plugins installed through marketplace.[/]")
        else:
            console.print("[bold]Installed Marketplace Plugins:[/]")
            for p in installed:
                console.print(f"  {p['id']}: v{p['version']}")
            console.print("\nUse 'ss marketplace update --all' to check for updates.")


def marketplace_sync_callback(repo_name: str | None = None) -> None:
    mm = get_marketplace_manager()

    if repo_name:
        console.print(f"Syncing repository '{repo_name}'...")
        result = mm.repos.sync(repo_name)
    else:
        console.print("Syncing all repositories...")
        results = mm.sync_all()
        for result in results:
            if result.success:
                console.print(
                    f"[green]  {result.repository}: {result.plugins_found} plugins found[/]"
                )
            else:
                console.print(f"[red]  {result.repository}: sync failed[/]")
                for e in result.errors:
                    console.print(f"    [red]{e}[/]")
        return

    if result.success:
        console.print(
            f"[green]Synced '{result.repository}': {result.plugins_found} plugins[/]"
        )
    else:
        console.print(f"[red]Sync failed for '{result.repository}'[/]")
        for e in result.errors:
            console.print(f"  {e}")


def marketplace_repo_callback(
    action: str,
    name: str = "",
    url: str = "",
    priority: int = 50,
    repo_type: str = "community",
) -> None:
    mm = get_marketplace_manager()

    if action == "list":
        repos = mm.repos.list_all()
        if not repos:
            console.print("[yellow]No repositories configured.[/]")
            return
        table = Table(title="Plugin Repositories")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="blue")
        table.add_column("Type")
        table.add_column("Priority")
        table.add_column("Status")
        for r in repos:
            status = "[green]enabled[/]" if r.enabled else "[dim]disabled[/]"
            table.add_row(r.name, r.url, r.type, str(r.priority), status)
        console.print(table)

    elif action == "add":
        if not name or not url:
            console.print(
                "[red]Both --name and --url are required to add a repository[/]"
            )
            return
        try:
            repo = mm.repos.add(name, url, repo_type=repo_type, priority=priority)
            console.print(f"[green]Added repository '{repo.name}' -> {repo.url}[/]")
        except MarketplaceError as e:
            console.print(f"[red]{e}[/]")

    elif action == "remove":
        if not name:
            console.print("[red]--name is required to remove a repository[/]")
            return
        try:
            mm.repos.remove(name)
            console.print(f"[green]Removed repository '{name}'[/]")
        except MarketplaceError as e:
            console.print(f"[red]{e}[/]")

    elif action == "enable":
        try:
            mm.repos.enable(name)
            console.print(f"[green]Enabled repository '{name}'[/]")
        except MarketplaceError as e:
            console.print(f"[red]{e}[/]")

    elif action == "disable":
        try:
            mm.repos.disable(name)
            console.print(f"[green]Disabled repository '{name}'[/]")
        except MarketplaceError as e:
            console.print(f"[red]{e}[/]")

    else:
        console.print(
            f"[red]Unknown action: {action}. Use: list, add, remove, enable, disable[/]"
        )


def marketplace_verify_callback(plugin_id: str) -> None:
    mm = get_marketplace_manager()
    warnings = mm.verify(plugin_id)

    if not warnings:
        console.print(f"[green]Plugin '{plugin_id}' verified successfully.[/]")
    else:
        console.print(f"[yellow]Verification warnings for '{plugin_id}':[/]")
        for w in warnings:
            console.print(f"  - {w}")


def marketplace_list_callback(category: str = "") -> None:
    mm = get_marketplace_manager()
    installed = mm.list_installed()

    if not installed:
        console.print("[yellow]No plugins installed through marketplace.[/]")
        return

    table = Table(title="Installed Marketplace Plugins")
    table.add_column("Plugin ID", style="cyan")
    table.add_column("Version", style="blue")
    table.add_column("Installed At", style="dim")
    repository = mm.repos

    for p in installed:
        repo_name = p.get("repository", "")
        installed_at = p.get("installed_at", "")[:10] if p.get("installed_at") else ""
        table.add_row(p["id"], p.get("version", ""), installed_at)
    console.print(table)

    console.print(f"\nTotal: {len(installed)} plugin(s) installed")
    console.print("Use 'ss marketplace update --all' to check for updates")


def marketplace_doctor_callback() -> None:
    mm = get_marketplace_manager()

    console.print("[bold]Marketplace Doctor Report[/]\n")

    repos = mm.repos.list_all()
    console.print(f"[bold]Repositories:[/] {len(repos)} configured")
    for r in repos:
        status = "[green]enabled[/]" if r.enabled else "[red]disabled[/]"
        cache = "cached" if mm.repos.get_cache(r.name) else "[yellow]not cached[/]"
        console.print(
            f"  {r.name}: {status} ({r.type}, priority {r.priority}) - {cache}"
        )

    installed = mm.list_installed()
    console.print(f"\n[bold]Installed Plugins:[/] {len(installed)}")

    if installed:
        updates = mm.check_updates()
        if updates:
            console.print(f"[yellow]  {len(updates)} update(s) available[/]")
        else:
            console.print("[green]  All up to date[/]")

    from shellsense.marketplace.signatures import SignatureManager

    sig = SignatureManager()
    trusted = sig.get_trusted_publishers()
    console.print(f"\n[bold]Trusted Publishers:[/] {len(trusted)}")

    from pathlib import Path

    cache_size = (
        sum(
            f.stat().st_size
            for f in Path(mm.repos._local_cache_dir).rglob("*")
            if f.is_file()
        )
        if os.path.isdir(mm.repos._local_cache_dir)
        else 0
    )
    console.print(f"\n[bold]Cache Size:[/] {cache_size / 1024:.1f} KB")

    console.print("\n[green]Marketplace status: OK[/]")


def marketplace_export_callback(output_path: str) -> None:
    mm = get_marketplace_manager()
    try:
        mm.export_collection(output_path)
        console.print(f"[green]Exported plugin collection to {output_path}[/]")
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/]")


def marketplace_import_callback(input_path: str) -> None:
    mm = get_marketplace_manager()
    try:
        count = mm.import_collection(input_path)
        console.print(f"[green]Imported {count} plugin(s) from {input_path}[/]")
    except Exception as e:
        console.print(f"[red]Import failed: {e}[/]")
