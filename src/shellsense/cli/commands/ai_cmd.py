from __future__ import annotations

from rich.console import Console
from rich.table import Table

from shellsense.ai.config import get_available_providers, set_default_provider
from shellsense.ai.core import AIEngine
from shellsense.ai.security import has_api_key, set_api_key
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()
_engine: AIEngine | None = None


def _get_engine() -> AIEngine:
    global _engine
    if _engine is None:
        _engine = AIEngine()
    return _engine


def ai_status_callback() -> None:
    engine = _get_engine()
    info = engine.get_provider_info()
    console.print("[bold]AI Engine Status[/]")
    console.print(f"  Provider:    {engine.provider_name}")
    console.print(f"  Available:   {'yes' if info.available else 'no'}")
    console.print(f"  Offline:     {'yes' if info.offline else 'no'}")
    console.print(
        f"  API Key:     {'configured' if has_api_key(engine.provider_name) else 'not set'}"
    )
    console.print(f"  Sessions:    {len(engine.sessions.list_sessions())}")
    usage = engine.tokens.get_daily_usage()
    console.print(
        f"  Today:       {usage.get('total_tokens', 0)} tokens (${usage.get('cost', 0):.6f})"
    )


def ai_providers_callback() -> None:
    engine = _get_engine()
    providers = engine.list_providers()

    table = Table(title="AI Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Available", style="green")
    table.add_column("Offline", style="blue")
    table.add_column("Requires Key", style="yellow")
    table.add_column("Has Key", style="magenta")
    table.add_column("Model")

    for p in providers:
        table.add_row(
            p.get("display_name", p.get("name", "")),
            "[green]yes[/]" if p.get("available") else "[red]no[/]",
            "[cyan]yes[/]" if p.get("offline") else "no",
            "[yellow]yes[/]" if p.get("requires_api_key") else "no",
            "[green]yes[/]" if p.get("has_api_key") else "[red]no[/]",
            "",
        )

    console.print(table)
    console.print(f"\nDefault provider: [bold]{engine.provider_name}[/]")
    console.print("Switch with: [dim]ss ai config default_provider <name>[/]")


def ai_models_callback(provider: str | None = None) -> None:
    engine = _get_engine()
    try:
        models = engine.get_models(provider)
        table = Table(title=f"Models ({provider or engine.provider_name})")
        table.add_column("Model ID", style="cyan")
        table.add_column("Provider", style="blue")
        for m in models:
            table.add_row(m.id, m.provider)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Failed to fetch models: {e}[/]")


def ai_login_callback(provider: str, api_key: str) -> None:
    set_api_key(provider, api_key)
    console.print(f"[green]API key configured for {provider}[/]")


def ai_logout_callback(provider: str) -> None:
    set_api_key(provider, "")
    console.print(f"[green]API key removed for {provider}[/]")


def ai_config_callback(key: str | None = None, value: str | None = None) -> None:
    if key and value:
        if key == "default_provider":
            if value not in get_available_providers():
                console.print(
                    f"[red]Unknown provider: {value}. Choose from: {', '.join(get_available_providers())}[/]"
                )
                return
            set_default_provider(value)
            engine = _get_engine()
            engine.set_provider(value)
            console.print(f"[green]Default provider set to: {value}[/]")
        else:
            console.print(f"[yellow]Unknown config key: {key}[/]")
    else:
        engine = _get_engine()
        console.print("[bold]Current AI Configuration[/]")
        console.print(f"  Default provider: {engine.provider_name}")
        console.print(f"  Providers: {', '.join(get_available_providers())}")


def ai_test_callback(provider: str | None = None) -> None:
    engine = _get_engine()
    name = provider or engine.provider_name
    console.print(f"Testing connection to [bold]{name}[/]...")

    try:
        ok = engine.test_connection(provider)
        if ok:
            console.print("[green]Connection successful![/]")
        else:
            console.print("[red]Connection failed[/]")
            if has_api_key(name):
                console.print("  API key is configured but connection failed.")
                console.print("  Check your network and API key validity.")
            else:
                console.print("  No API key configured.")
                console.print(f"  Use: [bold]ss ai login {name} <api_key>[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")


def ai_chat_callback(
    message: str,
    session_id: str | None = None,
    provider: str | None = None,
    stream: bool = False,
) -> None:
    engine = _get_engine()
    try:
        if stream:
            console.print("[dim]Streaming not yet fully implemented, using sync...[/]")
        response = engine.chat(message, session_id=session_id, provider=provider)

        if response.content:
            console.print(response.content)
        else:
            console.print("[yellow]No response generated[/]")

        console.print()
        console.print(
            f"[dim]Tokens: {response.usage.total_tokens} | "
            f"Latency: {response.usage.latency_ms:.0f}ms | "
            f"Model: {response.model}[/]"
        )
    except Exception as e:
        console.print(f"[red]Chat failed: {e}[/]")


def ai_clear_callback(session_id: str | None = None) -> None:
    engine = _get_engine()
    if session_id:
        engine.sessions.delete_session(session_id)
        console.print(f"[green]Session {session_id} cleared[/]")
    else:
        engine.memory.clear()
        engine.sessions.clear_all_sessions()
        console.print("[green]All AI memory and sessions cleared[/]")


def ai_history_callback(limit: int = 20) -> None:
    engine = _get_engine()
    sessions = engine.sessions.list_sessions()

    if not sessions:
        console.print("[yellow]No conversation history[/]")
        return

    table = Table(title=f"Conversation History (last {min(len(sessions), limit)})")
    table.add_column("Session ID", style="cyan")
    table.add_column("Provider", style="blue")
    table.add_column("Messages", style="magenta")
    table.add_column("Created", style="dim")
    table.add_column("Updated", style="dim")

    for s in sessions[:limit]:
        table.add_row(
            s.get("session_id", "")[:8] + "...",
            s.get("provider", ""),
            str(s.get("message_count", 0)),
            s.get("created_at", ""),
            s.get("updated_at", ""),
        )

    console.print(table)


def ai_usage_callback() -> None:
    engine = _get_engine()
    daily = engine.tokens.get_daily_usage()
    monthly = engine.tokens.get_monthly_usage()
    providers = engine.tokens.get_provider_usage()

    console.print("[bold]AI Usage Statistics[/]")
    console.print()
    console.print(
        f"Today:     {daily.get('total_tokens', 0)} tokens (${daily.get('cost', 0):.6f})"
    )
    console.print(
        f"Month:     {monthly.get('total_tokens', 0)} tokens (${monthly.get('cost', 0):.6f})"
    )
    console.print()

    if providers:
        table = Table(title="Per-Provider Usage")
        table.add_column("Provider", style="cyan")
        table.add_column("Requests", style="blue")
        table.add_column("Input Tokens", style="magenta")
        table.add_column("Output Tokens", style="yellow")
        table.add_column("Total Tokens", style="green")
        table.add_column("Cost", style="red")

        for pname, stats in providers.items():
            table.add_row(
                pname,
                str(stats.get("requests", 0)),
                str(stats.get("input_tokens", 0)),
                str(stats.get("output_tokens", 0)),
                str(stats.get("total_tokens", 0)),
                f"${stats.get('cost', 0):.4f}",
            )

        console.print(table)


def ai_cache_callback(action: str = "status") -> None:
    engine = _get_engine()
    if action == "clear":
        engine.cache.clear()
        console.print("[green]AI cache cleared[/]")
    else:
        console.print("[bold]AI Cache[/]")
        console.print("  Status: enabled")
        console.print("  Type: memory + disk")
        console.print("  TTL: 600s")
        console.print("  Use: [dim]ss ai cache clear[/] to clear")


def ai_doctor_callback() -> None:
    engine = _get_engine()
    console.print("[bold]AI Subsystem Diagnostics[/]")
    console.print("=" * 40)
    console.print()

    checks: list[tuple[str, bool, str]] = [
        ("Engine initialized", True, ""),
        ("Provider configured", bool(engine.provider_name), "No provider set"),
    ]

    for name, provider_n in [
        ("openai", "OpenAI"),
        ("gemini", "Gemini"),
        ("ollama", "Ollama"),
    ]:
        try:
            ok = engine.health_check(name)
            key = has_api_key(name)
            checks.append(
                (f"{provider_n} available", ok, "Connection failed" if not ok else "")
            )
            checks.append(
                (f"{provider_n} has API key", key, "Configure with: ss ai login")
            )
        except Exception:
            checks.append((f"{provider_n} check", False, "Error during check"))

    for name, passed, msg in checks:
        status = "[green]PASS[/]" if passed else "[red]FAIL[/]"
        console.print(f"  {status} {name}")
        if not passed and msg:
            console.print(f"         {msg}")
        console.print()
