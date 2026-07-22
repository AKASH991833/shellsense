from rich.console import Console

from shellsense import __title__, __version__

console = Console()


def version_callback() -> None:
    console.print(f"[bold cyan]{__title__}[/] [green]v{__version__}[/]")
