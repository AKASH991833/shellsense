import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shellsense.utils.config import ConfigManager
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def config_show_callback() -> None:
    config = ConfigManager()
    all_config = config.all()

    table = Table(title="Configuration", highlight=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    def flatten(d: dict[str, object], prefix: str = "") -> None:
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flatten(value, full_key)
            else:
                table.add_row(full_key, str(value))

    flatten(all_config)
    console.print(Panel(table, title="[bold cyan]ShellSense Configuration[/]"))


def config_get_callback(key: str) -> None:
    config = ConfigManager()
    value = config.get(key)
    if value is None:
        console.print(f"[yellow]Key '{key}' not found in configuration[/]")
        raise typer.Exit(code=1)
    console.print(f"[cyan]{key}[/] = [green]{value}[/]")


def config_set_callback(key: str, value: str) -> None:
    config = ConfigManager()
    typed_value: str | int | float | bool = value
    if value.lower() in ("true", "false"):
        typed_value = value.lower() == "true"
    else:
        try:
            if "." in value:
                typed_value = float(value)
            else:
                typed_value = int(value)
        except ValueError:
            pass
    config.set(key, typed_value)
    console.print(f"[green]Set[/] [cyan]{key}[/] = [green]{typed_value}[/]")


def config_reset_callback() -> None:
    config = ConfigManager()
    config.reset()
    console.print("[green]Configuration reset to defaults[/]")


def config_path_callback() -> None:
    config = ConfigManager()
    console.print(f"[cyan]Config file:[/] [green]{config.path}[/]")
