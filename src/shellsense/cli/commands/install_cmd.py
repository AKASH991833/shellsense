from __future__ import annotations

from rich.console import Console

from shellsense.shell.integration import ShellIntegrationManager
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def install_callback(shell: str | None = None) -> None:
    manager = ShellIntegrationManager()
    try:
        result = manager.install(shell)
        if result:
            console.print("[green]Shell integration installed successfully![/]")
            console.print()
            console.print("Please restart your shell or run:")
            console.print("  [bold]source ~/.bashrc[/]  (for Bash)")
            console.print("  [bold]source ~/.zshrc[/]   (for Zsh)")
            console.print("  [bold]exec fish[/]         (for Fish)")
        else:
            console.print("[yellow]Shell integration installation incomplete[/]")
    except Exception as e:
        logger.error("Installation failed: %s", e)
        console.print(f"[red]Installation failed: {e}[/]")


def uninstall_callback(shell: str | None = None) -> None:
    manager = ShellIntegrationManager()
    try:
        result = manager.uninstall(shell)
        if result:
            console.print("[green]Shell integration uninstalled successfully![/]")
            console.print()
            console.print("Please restart your shell to apply changes.")
        else:
            console.print("[yellow]Shell integration was not found[/]")
    except Exception as e:
        logger.error("Uninstallation failed: %s", e)
        console.print(f"[red]Uninstallation failed: {e}[/]")


def doctor_callback() -> None:
    manager = ShellIntegrationManager()
    checks = manager.diagnose()

    console.print("[bold]ShellSense AI Diagnostics[/]")
    console.print("=" * 40)
    console.print()

    all_passed = True
    for check in checks:
        status = check.get("status", "unknown")
        name = check.get("name", "Unknown")
        detail = check.get("detail", "")

        if status == "passed":
            console.print(f"  [green]PASS[/] {name}")
        elif status == "warning":
            console.print(f"  [yellow]WARN[/] {name}")
            all_passed = False
        else:
            console.print(f"  [red]FAIL[/] {name}")
            all_passed = False

        if detail:
            console.print(f"       {detail}")

        fix = check.get("fix")
        if fix and status != "passed":
            console.print(f"       [dim]Fix: {fix}[/]")
        console.print()

    if all_passed:
        console.print("[bold green]All checks passed![/]")
    else:
        console.print(
            "[yellow]Some checks require attention. Run [bold]ss repair[/] to attempt fixes.[/]"
        )


def repair_callback() -> None:
    manager = ShellIntegrationManager()
    results = manager.repair()

    if not results:
        console.print("[green]No repairs needed. Everything looks good![/]")
        return

    console.print("[bold]ShellSense AI Repair Results[/]")
    console.print("=" * 40)
    console.print()

    fixed = 0
    failed = 0
    for result in results:
        name = result.get("name", "Unknown")
        if result.get("fixed"):
            console.print(f"  [green]FIXED[/] {name}")
            fixed += 1
        else:
            console.print(f"  [red]FAILED[/] {name}")
            failed += 1
            error = result.get("fix_error", "")
            if error:
                console.print(f"         Error: {error}")
        console.print()

    console.print(f"[bold]{fixed} fixed, {failed} failed[/]")
