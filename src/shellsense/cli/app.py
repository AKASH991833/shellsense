import typer
from rich.console import Console

from shellsense import __title__
from shellsense.cli.commands.ai_cmd import (
    ai_cache_callback,
    ai_chat_callback,
    ai_clear_callback,
    ai_config_callback,
    ai_doctor_callback,
    ai_history_callback,
    ai_login_callback,
    ai_logout_callback,
    ai_models_callback,
    ai_providers_callback,
    ai_status_callback,
    ai_test_callback,
    ai_usage_callback,
)
from shellsense.cli.commands.analyze_cmd import (
    analyze_callback,
    explain_script_callback,
    optimize_callback,
)
from shellsense.cli.commands.ask_cmd import ask_callback
from shellsense.cli.commands.autocomplete_cmd import autocomplete_callback
from shellsense.cli.commands.backup_cmd import (
    create_backup_callback,
    list_backups_callback,
    restore_backup_callback,
)
from shellsense.cli.commands.daemon_cmd import (
    daemon_start_callback,
    daemon_status_callback,
    daemon_stop_callback,
    daemon_restart_callback,
    daemon_suggest_callback,
)
from shellsense.cli.commands.discover_cmd import discover_callback
from shellsense.cli.commands.category_cmd import (
    category_list_callback,
    category_show_callback,
)
from shellsense.cli.commands.check_cmd import check_command_callback
from shellsense.cli.commands.config import (
    config_get_callback,
    config_path_callback,
    config_reset_callback,
    config_set_callback,
    config_show_callback,
)
from shellsense.cli.commands.context_cmd import context_callback
from shellsense.cli.commands.examples_cmd import examples_callback
from shellsense.cli.commands.explain_cmd import explain_callback
from shellsense.cli.commands.explain_current_cmd import explain_current_callback
from shellsense.cli.commands.fix_cmd import fix_callback
from shellsense.cli.commands.generate_cmd import (
    compare_callback,
    document_callback,
    export_callback,
    generate_callback,
    generate_interactive_callback,
    list_templates_callback,
    preview_callback,
    search_templates_callback,
    validate_callback,
)
from shellsense.cli.commands.git_cmd import git_explain_callback, git_help_callback
from shellsense.cli.commands.history_cmd import (
    clear_history_callback,
    history_callback,
)
from shellsense.cli.commands.info import info_callback
from shellsense.cli.commands.install_cmd import (
    doctor_callback,
    install_callback,
    repair_callback,
    uninstall_callback,
)
from shellsense.cli.commands.logs_cmd import logs_analyze_callback
from shellsense.cli.commands.marketplace_cmd import (
    marketplace_doctor_callback,
    marketplace_export_callback,
    marketplace_import_callback,
    marketplace_info_callback,
    marketplace_install_callback,
    marketplace_list_callback,
    marketplace_remove_callback,
    marketplace_repo_callback,
    marketplace_search_callback,
    marketplace_sync_callback,
    marketplace_update_callback,
    marketplace_verify_callback,
)
from shellsense.cli.commands.plugin_cmd import (
    plugin_create_callback,
    plugin_disable_callback,
    plugin_doctor_callback,
    plugin_enable_callback,
    plugin_info_callback,
    plugin_install_callback,
    plugin_list_callback,
    plugin_permissions_callback,
    plugin_reload_callback,
    plugin_remove_callback,
    plugin_scaffold_callback,
    plugin_validate_callback,
)
from shellsense.cli.commands.privacy_cmd import (
    privacy_allow_callback,
    privacy_deny_callback,
    privacy_reset_callback,
    privacy_show_callback,
    privacy_toggle_callback,
)
from shellsense.cli.commands.recommend_cmd import (
    recommend_callback,
    similar_callback,
)
from shellsense.cli.commands.related_cmd import related_callback
from shellsense.cli.commands.search_cmd import search_callback
from shellsense.cli.commands.service_cmd import (
    service_diagnose_callback,
    service_explain_callback,
)
from shellsense.cli.commands.suggest_cmd import suggest_callback
from shellsense.cli.commands.template_cmd import (
    template_categories_callback,
    template_list_callback,
    template_show_callback,
)
from shellsense.cli.commands.version import version_callback
from shellsense.startup import initialize
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(
    name=__title__,
    help="Think Less. Command More. — Intelligent Linux Terminal Assistant",
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
)

config_app = typer.Typer(
    name="config",
    help="Manage ShellSense AI configuration",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


def _version_callback(value: bool) -> None:
    if value:
        version_callback()
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["INITIALIZED"] = False
    try:
        initialize(verbose=verbose)
        ctx.obj["INITIALIZED"] = True
    except Exception as e:
        logger.error("Initialization failed: %s", e)
        console.print(f"[red]Initialization failed: {e}[/]")
        raise typer.Exit(code=1)


@app.command(name="version")
def version() -> None:
    """Show ShellSense AI version."""
    version_callback()


@app.command(name="info")
def info(
    command: str = typer.Argument(
        None, help="Command name to get info about (optional)"
    ),
) -> None:
    """Show system information or command details."""
    info_callback(command)


@app.command(name="doctor")
def doctor() -> None:
    """Run system diagnostics."""
    doctor_callback()


backup_app = typer.Typer(
    name="backup",
    help="Backup and restore ShellSense AI data",
)
app.add_typer(backup_app, name="backup")

discover_app = typer.Typer(
    name="discover",
    help="Discover Linux commands from your system",
)
app.add_typer(discover_app, name="discover")


@backup_app.command(name="create")
def backup_create(
    name: str | None = typer.Option(None, "--name", "-n", help="Backup name"),
    item: list[str] | None = typer.Option(
        None, "--item", "-i", help="Items to backup (config, database, plugins, logs)"
    ),
) -> None:
    """Create a backup of ShellSense AI data."""
    create_backup_callback(name=name, items=item)


@backup_app.command(name="restore")
def backup_restore(
    name: str = typer.Argument(..., help="Backup name to restore from"),
    item: list[str] | None = typer.Option(
        None, "--item", "-i", help="Items to restore (config, database, plugins, logs)"
    ),
) -> None:
    """Restore ShellSense AI data from a backup."""
    restore_backup_callback(name, items=item)


@backup_app.command(name="list")
def backup_list() -> None:
    """List available backups."""
    list_backups_callback()


@discover_app.command(name="scan")
def discover_scan(
    max_commands: int = typer.Option(
        500, "--max", "-m", help="Maximum commands to discover"
    ),
    refresh: bool = typer.Option(
        False, "--refresh", "-r", help="Refresh existing discovered commands"
    ),
    stats: bool = typer.Option(
        False, "--stats", "-s", help="Show discovery stats only"
    ),
) -> None:
    """Scan system and discover Linux commands with descriptions."""
    discover_callback(max_commands=max_commands, refresh=refresh, stats=stats)


daemon_app = typer.Typer(
    name="daemon",
    help="Background daemon for auto-suggestions",
)
app.add_typer(daemon_app, name="daemon")


@daemon_app.command(name="start")
def daemon_start(
    foreground: bool = typer.Option(False, "--foreground", "-f"),
) -> None:
    """Start the ShellSense daemon."""
    daemon_start_callback(foreground=foreground)


@daemon_app.command(name="stop")
def daemon_stop() -> None:
    """Stop the ShellSense daemon."""
    daemon_stop_callback()


@daemon_app.command(name="status")
def daemon_status() -> None:
    """Show daemon status."""
    daemon_status_callback()


@daemon_app.command(name="restart")
def daemon_restart() -> None:
    """Restart the ShellSense daemon."""
    daemon_restart_callback()


@daemon_app.command(name="suggest")
def daemon_suggest(
    partial: str = typer.Argument(..., help="Partial command"),
) -> None:
    """Get auto-suggestion from daemon."""
    daemon_suggest_callback(partial=partial)


@app.command(name="search")
def search(
    query: str = typer.Argument(..., help="Search query for commands"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
) -> None:
    """Search for commands in the knowledge base."""
    search_callback(query, limit=limit)


@app.command(name="explain")
def explain(
    command: str = typer.Argument(..., help="Command name to explain"),
) -> None:
    """Get a detailed explanation of a command."""
    explain_callback(command)


@app.command(name="examples")
def examples(
    command: str = typer.Argument(..., help="Command name to show examples for"),
) -> None:
    """Show usage examples for a command."""
    examples_callback(command)


@app.command(name="category")
def category(
    category_name: str = typer.Argument(
        None, help="Category name (omit to list all categories)"
    ),
) -> None:
    """List command categories or commands in a category."""
    if category_name:
        category_show_callback(category_name)
    else:
        category_list_callback()


@app.command(name="related")
def related(
    command: str = typer.Argument(..., help="Command name to find related commands for")
) -> None:
    """Show related commands for a given command."""
    related_callback(command)


@app.command(name="suggest")
def suggest(
    query: str = typer.Argument(..., help="Partial text to get suggestions for"),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of suggestions"
    ),
) -> None:
    """Get intelligent command suggestions."""
    suggest_callback(query, limit=limit)


@app.command(name="recommend")
def recommend(
    command: str = typer.Argument(..., help="Command name to get recommendations for"),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of recommendations"
    ),
) -> None:
    """Get recommended commands related to a given command."""
    recommend_callback(command, limit=limit)


@app.command(name="similar")
def similar(
    command: str = typer.Argument(
        ..., help="Command name to find similar commands for"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of similar commands"
    ),
) -> None:
    """Find commands similar to a given command."""
    similar_callback(command, limit=limit)


@app.command(name="history")
def history(
    limit: int = typer.Option(
        20, "--limit", "-l", help="Maximum number of history entries"
    ),
) -> None:
    """Show search and suggestion history."""
    history_callback(limit=limit)


@app.command(name="clear-history")
def clear_history() -> None:
    """Clear all search and suggestion history."""
    clear_history_callback()


@app.command(name="install")
def install(
    shell: str = typer.Argument(
        None, help="Shell to install integration for (bash, zsh, fish)"
    ),
) -> None:
    """Install ShellSense shell integration."""
    install_callback(shell)


@app.command(name="uninstall")
def uninstall(
    shell: str = typer.Argument(None, help="Shell to uninstall integration from"),
) -> None:
    """Uninstall ShellSense shell integration."""
    uninstall_callback(shell)


@app.command(name="repair")
def repair() -> None:
    """Attempt to repair ShellSense installation."""
    repair_callback()


@app.command(name="autocomplete")
def autocomplete(
    partial: str = typer.Argument(
        ..., help="Partial text to get autocomplete suggestions for"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of suggestions"
    ),
) -> None:
    """Get autocomplete suggestions (used by shell integration)."""
    autocomplete_callback(partial, limit=limit)


@app.command(name="check-command", hidden=True)
def check_command(
    command: str = typer.Argument(..., help="Command to check for safety"),
) -> None:
    """Check a command for safety warnings."""
    check_command_callback(command)


@app.command(name="ask")
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    system_style: str = typer.Option(
        "context", "--style", "-s", help="System prompt style"
    ),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
    show_context: bool = typer.Option(
        False, "--context", "-c", help="Show collected context"
    ),
) -> None:
    """Ask a question with terminal context."""
    ask_callback(question, system_style, provider, show_context)


@app.command(name="explain-current")
def explain_current(
    use_ai: bool = typer.Option(
        False, "--ai", help="Use AI for explanation if not in knowledge base"
    ),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Explain the current or last command."""
    explain_current_callback(use_ai=use_ai, provider=provider)


@app.command(name="fix")
def fix(
    command: str = typer.Argument(
        None, help="Failed command (auto-detected if omitted)"
    ),
    error_message: str = typer.Option(None, "--error", "-e", help="Error message text"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for error analysis"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Analyze and fix a failed command."""
    fix_callback(command, error_message, use_ai=use_ai, provider=provider)


analyze_app = typer.Typer(
    name="analyze", help="Analyze scripts and files", no_args_is_help=True
)
app.add_typer(analyze_app, name="analyze")


@analyze_app.command(name="script")
def analyze_script(
    path: str = typer.Argument(..., help="Path to shell script"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for analysis"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Analyze a shell script for bugs and security issues."""
    analyze_callback(path, use_ai=use_ai, provider=provider)


@analyze_app.command(name="optimize")
def analyze_optimize(
    path: str = typer.Argument(..., help="Path to shell script"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for optimization"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Suggest performance improvements for a shell script."""
    optimize_callback(path, use_ai=use_ai, provider=provider)


@analyze_app.command(name="explain")
def analyze_explain(
    path: str = typer.Argument(..., help="Path to shell script"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for explanation"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Explain what a shell script does."""
    explain_script_callback(path, use_ai=use_ai, provider=provider)


logs_app = typer.Typer(name="logs", help="Log analysis commands", no_args_is_help=True)
app.add_typer(logs_app, name="logs")


@logs_app.command(name="analyze")
def logs_analyze(
    source: str = typer.Argument("journald", help="Log source (journald or file path)"),
    units: str = typer.Option(
        None, "--unit", "-u", help="Systemd unit filter (comma-separated)"
    ),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines"),
) -> None:
    """Analyze system logs for issues."""
    unit_list = units.split(",") if units else None
    logs_analyze_callback(source=source, units=unit_list, lines=lines)


git_app = typer.Typer(
    name="git", help="Git intelligence commands", no_args_is_help=True
)
app.add_typer(git_app, name="git")


@git_app.command(name="explain")
def git_explain(
    git_command: str = typer.Argument(
        "", help="Git command to explain (omit for repo status)"
    ),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for explanation"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Explain a git command or show repository status."""
    git_explain_callback(git_command, use_ai=use_ai, provider=provider)


@git_app.command(name="help")
def git_help(
    git_command: str = typer.Argument("", help="Git command to get help for"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for help"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Get help for a git command."""
    git_help_callback(git_command, use_ai=use_ai, provider=provider)


service_app = typer.Typer(
    name="service", help="Service intelligence commands", no_args_is_help=True
)
app.add_typer(service_app, name="service")


@service_app.command(name="explain")
def service_explain(
    service_name: str = typer.Argument(..., help="Service name"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for explanation"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Show service status and information."""
    service_explain_callback(service_name, use_ai=use_ai, provider=provider)


@service_app.command(name="diagnose")
def service_diagnose(
    service_name: str = typer.Argument(..., help="Service name"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for diagnosis"),
    provider: str = typer.Option(None, "--provider", "-p", help="AI provider"),
) -> None:
    """Diagnose issues with a service."""
    service_diagnose_callback(service_name, use_ai=use_ai, provider=provider)


plugin_app = typer.Typer(name="plugin", help="Manage plugins", no_args_is_help=True)
app.add_typer(plugin_app, name="plugin")


@plugin_app.command(name="list")
def plugin_list() -> None:
    """List installed plugins."""
    plugin_list_callback()


@plugin_app.command(name="info")
def plugin_info(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Show plugin information."""
    plugin_info_callback(plugin_id)


@plugin_app.command(name="enable")
def plugin_enable(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Enable a plugin."""
    plugin_enable_callback(plugin_id)


@plugin_app.command(name="disable")
def plugin_disable(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Disable a plugin."""
    plugin_disable_callback(plugin_id)


@plugin_app.command(name="reload")
def plugin_reload(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Reload a plugin."""
    plugin_reload_callback(plugin_id)


@plugin_app.command(name="install")
def plugin_install(
    path: str = typer.Argument(..., help="Plugin directory path or name"),
) -> None:
    """Install a plugin from a directory."""
    plugin_install_callback(path)


@plugin_app.command(name="remove")
def plugin_remove(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Remove a plugin."""
    plugin_remove_callback(plugin_id)


@plugin_app.command(name="validate")
def plugin_validate(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Validate a plugin."""
    plugin_validate_callback(plugin_id)


@plugin_app.command(name="doctor")
def plugin_doctor() -> None:
    """Run plugin diagnostics."""
    plugin_doctor_callback()


@plugin_app.command(name="create")
def plugin_create(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
    name: str = typer.Option("", "--name", "-n", help="Plugin display name"),
    description: str = typer.Option(
        "", "--description", "-d", help="Plugin description"
    ),
    author: str = typer.Option("", "--author", "-a", help="Plugin author"),
    version: str = typer.Option("0.1.0", "--version", "-v", help="Plugin version"),
) -> None:
    """Create a new plugin project."""
    plugin_create_callback(
        plugin_id,
        output_dir,
        name=name,
        description=description,
        author=author,
        version=version,
    )


@plugin_app.command(name="scaffold")
def plugin_scaffold(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
) -> None:
    """Scaffold a basic plugin structure."""
    plugin_scaffold_callback(plugin_id, output_dir)


@plugin_app.command(name="permissions")
def plugin_permissions(
    plugin_id: str = typer.Argument(None, help="Plugin ID (omit to list all)"),
) -> None:
    """Show plugin permissions."""
    plugin_permissions_callback(plugin_id)


marketplace_app = typer.Typer(
    name="marketplace",
    help="Plugin marketplace and repository management",
    no_args_is_help=True,
)
app.add_typer(marketplace_app, name="marketplace")


@marketplace_app.command(name="search")
def marketplace_search(
    query: str = typer.Argument(..., help="Search query"),
    category: str = typer.Option("", "--category", "-c", help="Filter by category"),
    sort_by: str = typer.Option(
        "name", "--sort", "-s", help="Sort by: name, downloads, rating, newest"
    ),
) -> None:
    """Search for plugins in the marketplace."""
    marketplace_search_callback(query, category=category, sort_by=sort_by)


@marketplace_app.command(name="info")
def marketplace_info(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Show plugin information."""
    marketplace_info_callback(plugin_id)


@marketplace_app.command(name="install")
def marketplace_install(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
    version: str = typer.Option("", "--version", "-v", help="Specific version"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without installing"),
) -> None:
    """Install a plugin from the marketplace."""
    marketplace_install_callback(plugin_id, version=version, dry_run=dry_run)


@marketplace_app.command(name="remove")
def marketplace_remove(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Remove an installed marketplace plugin."""
    marketplace_remove_callback(plugin_id)


@marketplace_app.command(name="update")
def marketplace_update(
    plugin_id: str = typer.Argument(None, help="Plugin ID (omit for all)"),
    all_plugins: bool = typer.Option(False, "--all", "-a", help="Check all plugins"),
) -> None:
    """Check and apply plugin updates."""
    marketplace_update_callback(plugin_id, all_plugins=all_plugins)


@marketplace_app.command(name="sync")
def marketplace_sync(
    repo_name: str = typer.Argument(None, help="Repository name (omit for all)"),
) -> None:
    """Synchronize marketplace repository cache."""
    marketplace_sync_callback(repo_name)


@marketplace_app.command(name="repo")
def marketplace_repo(
    action: str = typer.Argument(
        "list", help="Action: list, add, remove, enable, disable"
    ),
    name: str = typer.Option("", "--name", "-n", help="Repository name"),
    url: str = typer.Option("", "--url", "-u", help="Repository URL"),
    priority: int = typer.Option(50, "--priority", "-p", help="Repository priority"),
    repo_type: str = typer.Option("community", "--type", "-t", help="Repository type"),
) -> None:
    """Manage plugin repositories."""
    marketplace_repo_callback(
        action, name=name, url=url, priority=priority, repo_type=repo_type
    )


@marketplace_app.command(name="verify")
def marketplace_verify(
    plugin_id: str = typer.Argument(..., help="Plugin ID"),
) -> None:
    """Verify plugin integrity and signature."""
    marketplace_verify_callback(plugin_id)


@marketplace_app.command(name="list")
def marketplace_list(
    category: str = typer.Option("", "--category", "-c", help="Filter by category"),
) -> None:
    """List installed marketplace plugins."""
    marketplace_list_callback(category=category)


@marketplace_app.command(name="doctor")
def marketplace_doctor() -> None:
    """Run marketplace diagnostics."""
    marketplace_doctor_callback()


@marketplace_app.command(name="export")
def marketplace_export(
    output_path: str = typer.Argument(..., help="Output file path"),
) -> None:
    """Export installed plugin collection."""
    marketplace_export_callback(output_path)


@marketplace_app.command(name="import")
def marketplace_import(
    input_path: str = typer.Argument(..., help="Input collection file"),
) -> None:
    """Import a plugin collection."""
    marketplace_import_callback(input_path)


@app.command(name="context")
def context() -> None:
    """Show current terminal context."""
    context_callback()


privacy_app = typer.Typer(name="privacy", help="Privacy settings", no_args_is_help=True)
app.add_typer(privacy_app, name="privacy")


@privacy_app.command(name="show")
def privacy_show() -> None:
    """Show current privacy settings."""
    privacy_show_callback()


@privacy_app.command(name="allow")
def privacy_allow(
    key: str = typer.Argument(..., help="Context key to allow"),
) -> None:
    """Allow sharing a context field."""
    privacy_allow_callback(key)


@privacy_app.command(name="deny")
def privacy_deny(
    key: str = typer.Argument(..., help="Context key to deny"),
) -> None:
    """Deny sharing a context field."""
    privacy_deny_callback(key)


@privacy_app.command(name="toggle")
def privacy_toggle(
    key: str = typer.Argument(..., help="Context key to toggle"),
) -> None:
    """Toggle sharing for a context field."""
    privacy_toggle_callback(key)


@privacy_app.command(name="reset")
def privacy_reset() -> None:
    """Reset privacy settings to defaults."""
    privacy_reset_callback()


generate_app = typer.Typer(
    name="generate",
    help="Generate automation and infrastructure files",
    no_args_is_help=True,
)
app.add_typer(generate_app, name="generate")


@generate_app.command(name="interactive")
def generate_interactive(
    template_type: str = typer.Argument(
        ..., help="Template type (e.g. backup, systemd-service, dockerfile)"
    ),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
) -> None:
    """Interactive guided generation."""
    generate_interactive_callback(template_type, output_dir)


@generate_app.command(name="list")
def generate_list(
    category: str = typer.Argument(None, help="Filter by category"),
) -> None:
    """List available generation templates."""
    list_templates_callback(category)


@generate_app.command(name="search")
def generate_search(
    query: str = typer.Argument(..., help="Search query"),
) -> None:
    """Search generation templates."""
    search_templates_callback(query)


@generate_app.command(name="preview")
def generate_preview(
    template_type: str = typer.Argument(..., help="Template type"),
    kwargs: list[str] = typer.Argument(None, help="Key=value parameters"),
) -> None:
    """Preview generated output without saving."""
    params = _parse_kwargs(kwargs)
    preview_callback(template_type, **params)


@generate_app.command(name="validate")
def generate_validate(
    file_path: str = typer.Argument(None, help="File to validate"),
    content: str = typer.Option(None, "--content", "-c", help="Content string"),
    file_type: str = typer.Option("", "--type", "-t", help="File type"),
) -> None:
    """Validate generated output syntax."""
    validate_callback(content=content, file_path=file_path, file_type=file_type)


@generate_app.command(name="export")
def generate_export(
    template_type: str = typer.Argument(..., help="Template type"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
    kwargs: list[str] = typer.Argument(None, help="Key=value parameters"),
) -> None:
    """Generate and export to file."""
    params = _parse_kwargs(kwargs)
    export_callback(template_type, output_dir, **params)


@app.command(name="generate")
def generate(
    template_type: str = typer.Argument(..., help="Template type"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI for generation"),
    requirement: str = typer.Option(
        "", "--requirement", "-r", help="AI requirement description"
    ),
    kwargs: list[str] = typer.Argument(None, help="Key=value parameters"),
) -> None:
    """Generate automation and infrastructure files."""
    params = _parse_kwargs(kwargs)
    generate_callback(
        template_type, output_dir, use_ai=use_ai, requirement=requirement, **params
    )


template_app = typer.Typer(
    name="template",
    help="Manage generation templates",
    no_args_is_help=True,
)
app.add_typer(template_app, name="template")


@template_app.command(name="list")
def template_list(
    category: str = typer.Argument(None, help="Filter by category"),
) -> None:
    """List available templates."""
    template_list_callback(category)


@template_app.command(name="show")
def template_show(
    name: str = typer.Argument(..., help="Template name"),
) -> None:
    """Show template details."""
    template_show_callback(name)


@template_app.command(name="categories")
def template_categories() -> None:
    """List template categories."""
    template_categories_callback()


@app.command(name="validate")
def validate(
    file_path: str = typer.Argument(None, help="File to validate"),
    content: str = typer.Option(None, "--content", "-c", help="Content string"),
    file_type: str = typer.Option("", "--type", "-t", help="File type"),
) -> None:
    """Validate a file or content."""
    validate_callback(content=content, file_path=file_path, file_type=file_type)


@app.command(name="document")
def document(
    file_path: str = typer.Argument(..., help="File to document"),
) -> None:
    """Generate documentation for a file."""
    document_callback(file_path)


@app.command(name="compare")
def compare(
    file_a: str = typer.Argument(..., help="First file"),
    file_b: str = typer.Argument(..., help="Second file"),
) -> None:
    """Compare two files."""
    compare_callback(file_a, file_b)


@app.command(name="export")
def export(
    template_type: str = typer.Argument(..., help="Template type"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
    kwargs: list[str] = typer.Argument(None, help="Key=value parameters"),
) -> None:
    """Generate and export to file."""
    params = _parse_kwargs(kwargs)
    export_callback(template_type, output_dir, **params)


@app.command(name="preview")
def preview(
    template_type: str = typer.Argument(..., help="Template type"),
    kwargs: list[str] = typer.Argument(None, help="Key=value parameters"),
) -> None:
    """Preview generated output."""
    params = _parse_kwargs(kwargs)
    preview_callback(template_type, **params)


def _parse_kwargs(kwargs: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    if kwargs:
        for item in kwargs:
            if "=" in item:
                key, val = item.split("=", 1)
                result[key.strip()] = val.strip()
    return result


ai_app = typer.Typer(name="ai", help="AI subsystem commands", no_args_is_help=True)
app.add_typer(ai_app, name="ai")


@ai_app.command(name="status")
def ai_status() -> None:
    """Show AI engine status."""
    ai_status_callback()


@ai_app.command(name="providers")
def ai_providers() -> None:
    """List available AI providers."""
    ai_providers_callback()


@ai_app.command(name="models")
def ai_models(
    provider: str = typer.Argument(None, help="Provider name (optional)"),
) -> None:
    """List available models for a provider."""
    ai_models_callback(provider)


@ai_app.command(name="login")
def ai_login(
    provider: str = typer.Argument(..., help="Provider name"),
    api_key: str = typer.Argument(..., help="API key"),
) -> None:
    """Configure an API key for a provider."""
    ai_login_callback(provider, api_key)


@ai_app.command(name="logout")
def ai_logout(
    provider: str = typer.Argument(..., help="Provider name"),
) -> None:
    """Remove an API key for a provider."""
    ai_logout_callback(provider)


@ai_app.command(name="config")
def ai_config(
    key: str = typer.Argument(None, help="Configuration key"),
    value: str = typer.Argument(None, help="Configuration value"),
) -> None:
    """View or set AI configuration."""
    ai_config_callback(key, value)


@ai_app.command(name="test")
def ai_test(
    provider: str = typer.Argument(None, help="Provider name (optional)"),
) -> None:
    """Test connection to an AI provider."""
    ai_test_callback(provider)


@ai_app.command(name="chat")
def ai_chat(
    message: str = typer.Argument(..., help="Message to send"),
    session_id: str = typer.Option(None, "--session", "-s", help="Session ID"),
    provider: str = typer.Option(None, "--provider", "-p", help="Provider"),
    stream: bool = typer.Option(False, "--stream", help="Enable streaming"),
) -> None:
    """Chat with an AI provider."""
    ai_chat_callback(message, session_id, provider, stream)


@ai_app.command(name="clear")
def ai_clear(
    session_id: str = typer.Argument(None, help="Session ID (omit to clear all)"),
) -> None:
    """Clear AI session or all memory."""
    ai_clear_callback(session_id)


@ai_app.command(name="history")
def ai_history(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum entries"),
) -> None:
    """Show AI conversation history."""
    ai_history_callback(limit)


@ai_app.command(name="usage")
def ai_usage() -> None:
    """Show AI usage statistics."""
    ai_usage_callback()


@ai_app.command(name="cache")
def ai_cache(
    action: str = typer.Argument("status", help="Action: status or clear"),
) -> None:
    """View or clear AI cache."""
    ai_cache_callback(action)


@ai_app.command(name="doctor")
def ai_doctor() -> None:
    """Run AI subsystem diagnostics."""
    ai_doctor_callback()


@config_app.command(name="show")
def config_show() -> None:
    """Show all configuration values."""
    config_show_callback()


@config_app.command(name="get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key (e.g. general.theme)")
) -> None:
    """Get a configuration value."""
    config_get_callback(key)


@config_app.command(name="set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """Set a configuration value."""
    config_set_callback(key, value)


@config_app.command(name="reset")
def config_reset() -> None:
    """Reset configuration to defaults."""
    config_reset_callback()


@config_app.command(name="path")
def config_path() -> None:
    """Show configuration file path."""
    config_path_callback()
