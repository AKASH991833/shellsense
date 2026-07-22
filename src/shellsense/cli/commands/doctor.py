import os
import shutil
import sys
import time
from importlib.metadata import distributions

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import (
    get_cache_dir,
    get_config_path,
    get_db_path,
    get_log_path,
    get_plugins_dir,
    get_shellsense_dir,
)
from shellsense.utils.platform import get_system_info, is_linux, is_supported_distro

logger = get_logger(__name__)
console = Console()

REQUIRED_PACKAGES = [
    "typer",
    "rich",
]

RECOMMENDED_PACKAGES: list[str] = []

CHECK_SYMBOLS = {
    "pass": "[bold green]\u2713[/]",
    "fail": "[bold red]\u2717[/]",
    "warn": "[bold yellow]\u26a0[/]",
}


def doctor_callback() -> None:
    console.print(Panel("[bold cyan]ShellSense AI - System Diagnostics[/]"))
    checks: list[tuple[str, bool | str, str]] = []

    _check_platform(checks)
    _check_installation(checks)
    _check_config(checks)
    _check_database(checks)
    _check_daemon(checks)
    _check_plugins(checks)
    _check_marketplace(checks)
    _check_ai_providers(checks)
    _check_permissions(checks)
    _check_performance(checks)
    _check_packages(checks)

    table = Table(highlight=True)
    table.add_column("Status", width=4)
    table.add_column("Check", style="cyan")
    table.add_column("Details", style="yellow")

    all_passed = True
    for name, status, msg in checks:
        if status is True:
            symbol = CHECK_SYMBOLS["pass"]
        elif status is False:
            symbol = CHECK_SYMBOLS["fail"]
            all_passed = False
        else:
            symbol = CHECK_SYMBOLS["warn"]
        table.add_row(symbol, name, str(msg) if status is not True else "")

    console.print(Panel(table, title="[bold cyan]Diagnostic Results[/]"))

    if all_passed:
        console.print("\n[bold green]All checks passed. ShellSense AI is ready![/]")
    else:
        msg = (
            "\n[yellow]Some checks failed or need attention."
            " Review the issues above.[/]"
        )
        console.print(msg)
        raise typer.Exit(code=1)


def _check_platform(checks: list[tuple[str, bool | str, str]]) -> None:
    checks.append(("Platform: Linux", is_linux(), "Only Linux is supported"))

    distro_supported = is_supported_distro()
    info = get_system_info()
    distro_detail = info.distro or "unknown"
    checks.append(
        ("Supported Distribution", distro_supported, f"Distro: {distro_detail}")
    )
    checks.append(
        (
            "Python >= 3.12",
            sys.version_info >= (3, 12),
            f"Python {sys.version_info.major}.{sys.version_info.minor}"
            f".{sys.version_info.micro}",
        )
    )
    checks.append(
        ("Shell detected", info.shell is not None, f"Shell: {info.shell or 'none'}")
    )
    checks.append(
        (
            "Terminal detected",
            info.terminal is not None,
            f"Terminal: {info.terminal or 'none'}",
        )
    )


def _check_installation(checks: list[tuple[str, bool | str, str]]) -> None:
    shellsense_dir = get_shellsense_dir()
    config_path = get_config_path()
    db_path = get_db_path()
    log_path = get_log_path()

    checks.append(("Config directory", shellsense_dir.exists(), str(shellsense_dir)))
    checks.append(("Config file", config_path.exists(), str(config_path)))
    checks.append(("Database file", db_path.exists(), str(db_path)))
    checks.append(("Log file", log_path.exists(), str(log_path)))

    cli_available = shutil.which("ss") is not None or _is_package_installed(
        "shellsense"
    )
    checks.append(
        (
            "CLI entry point",
            cli_available,
            "Available" if cli_available else "Run 'pip install -e .'",
        )
    )


def _check_config(checks: list[tuple[str, bool | str, str]]) -> None:
    config_path = get_config_path()
    if config_path.exists():
        size = config_path.stat().st_size
        checks.append(("Config file size", True, f"{size / 1024:.1f} KB"))
        try:
            import json

            data = json.loads(config_path.read_text())
            has_api_keys = any(
                "api_key" in str(v) or "key" in str(k).lower()
                for k, v in data.get("ai", {}).items()
                if isinstance(v, str) and v
            )
            if has_api_keys:
                checks.append(
                    (
                        "API keys in config",
                        False,
                        "Warning: API keys stored in plaintext",
                    )
                )
            else:
                checks.append(("API key storage", True, "No plaintext keys found"))
        except Exception as e:
            checks.append(("Config file readable", False, str(e)))
    else:
        checks.append(("Config check", "skipped", "No config file to check"))


def _check_database(checks: list[tuple[str, bool | str, str]]) -> None:
    db_path = get_db_path()
    if db_path.exists():
        size = db_path.stat().st_size
        checks.append(("Database size", True, f"{size / (1024 * 1024):.1f} MB"))
        try:
            from shellsense.database.manager import DatabaseManager

            db = DatabaseManager(db_path)
            db.initialize()
            seeded = db.is_seeded()
            db.close()
            checks.append(
                (
                    "Database seeded",
                    seeded,
                    "yes" if seeded else "Run 'ss search' to seed",
                )
            )
        except Exception as e:
            checks.append(("Database connection", False, str(e)))
    else:
        checks.append(("Database", "skipped", "Not initialized yet"))


def _check_plugins(checks: list[tuple[str, bool | str, str]]) -> None:
    plugins_dir = get_plugins_dir()
    if plugins_dir.exists():
        plugin_count = len([p for p in plugins_dir.iterdir() if p.is_dir()])
        checks.append(("Plugins installed", True, f"{plugin_count} plugin(s)"))
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest = plugin_dir / "manifest.json"
                if not manifest.exists():
                    checks.append(
                        (
                            f"Plugin '{plugin_dir.name}'",
                            "warning",
                            "Missing manifest.json",
                        )
                    )
    else:
        checks.append(("Plugin system", True, "No plugins installed"))


def _check_marketplace(checks: list[tuple[str, bool | str, str]]) -> None:
    cache_dir = get_cache_dir() / "marketplace"
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))
        checks.append(("Marketplace cache", True, f"{len(cache_files)} cached file(s)"))
    else:
        checks.append(("Marketplace", True, "Not initialized"))


def _check_ai_providers(checks: list[tuple[str, bool | str, str]]) -> None:
    config_path = get_config_path()
    providers_found: list[str] = []
    if config_path.exists():
        try:
            import json

            data = json.loads(config_path.read_text())
            ai_config = data.get("ai", {})
            for provider_key in [
                "openai",
                "anthropic",
                "gemini",
                "ollama",
                "openrouter",
            ]:
                provider_config = ai_config.get(provider_key, {})
                if provider_config.get("api_key") or provider_config.get(
                    "enabled", False
                ):
                    providers_found.append(provider_key)
        except Exception:
            pass

    env_providers = []
    if os.environ.get("OPENAI_API_KEY"):
        env_providers.append("openai")
    if os.environ.get("ANTHROPIC_API_KEY"):
        env_providers.append("anthropic")
    if os.environ.get("GOOGLE_API_KEY"):
        env_providers.append("gemini")

    all_providers = set(providers_found + env_providers)
    if all_providers:
        checks.append(("AI Providers", True, ", ".join(sorted(all_providers))))
    else:
        checks.append(("AI Providers", True, "None configured (optional)"))


def _check_permissions(checks: list[tuple[str, bool | str, str]]) -> None:
    shellsense_dir = get_shellsense_dir()
    if shellsense_dir.exists():
        mode = oct(shellsense_dir.stat().st_mode)[-3:]
        readable = os.access(shellsense_dir, os.R_OK)
        writable = os.access(shellsense_dir, os.W_OK)
        checks.append(
            ("Config directory permissions", readable and writable, f"Mode: {mode}")
        )

    config_path = get_config_path()
    if config_path.exists():
        mode = oct(config_path.stat().st_mode)[-3:]
        checks.append(
            (
                "Config file permissions",
                mode in ("600", "700"),
                f"Mode: {mode} (recommended: 600)",
            )
        )


def _check_performance(checks: list[tuple[str, bool | str, str]]) -> None:
    db_path = get_db_path()
    if db_path.exists():
        start = time.time()
        try:
            from shellsense.database.manager import DatabaseManager

            db = DatabaseManager(db_path)
            db.initialize()
            row = db.execute("SELECT COUNT(*) FROM commands").fetchone()
            count = row[0] if row else 0
            db.close()
            elapsed = (time.time() - start) * 1000
            checks.append(
                (
                    "Database query time",
                    elapsed < 500,
                    f"{elapsed:.0f}ms ({count} commands)",
                )
            )
        except Exception:
            pass

    cache_dir = get_cache_dir()
    if cache_dir.exists():
        cache_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
        checks.append(("Cache size", True, f"{cache_size / 1024:.1f} KB"))


def _check_packages(
    checks: list[tuple[str, bool | str, str]],
) -> None:
    installed = {dist.metadata["Name"].lower() for dist in distributions()}
    for pkg in REQUIRED_PACKAGES:
        found = pkg.lower() in installed
        checks.append(
            (
                f"Package: {pkg}",
                found,
                f"Install with: pip install {pkg}" if not found else "installed",
            )
        )
    for pkg in RECOMMENDED_PACKAGES:
        found = pkg.lower() in installed
        if not found:
            checks.append(
                (
                    f"Package: {pkg} (recommended)",
                    False,
                    f"Install with: pip install {pkg}",
                )
            )


def _check_daemon(checks: list[tuple[str, bool | str, str]]) -> None:
    from shellsense.daemon.server import is_running

    running = is_running()
    if running:
        from shellsense.daemon.client import DaemonClient

        client = DaemonClient()
        stats = client.stats()
        if stats.get("status") == "ok":
            counts = stats.get("counts", {})
            total = counts.get("total", 0)
            uptime = stats.get("uptime", 0)
            checks.append(
                (
                    "Daemon",
                    True,
                    f"Running (uptime: {uptime}s, commands: {total})",
                )
            )
        else:
            checks.append(("Daemon", True, "Running"))
    else:
        checks.append(
            (
                "Daemon",
                "STOPPED",
                "Not running. Start with: ss daemon start",
            )
        )


def _is_package_installed(name: str) -> bool:
    try:
        from importlib.metadata import distribution

        distribution(name)
        return True
    except Exception:
        return False
