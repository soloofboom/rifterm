"""CLI rifterm — le marché, dans votre terminal."""

from __future__ import annotations

import typer
from rich.console import Console

from rifterm import __version__
from rifterm.cache import fetch
from rifterm.client import RifApiError, get
from rifterm.config import config_path, load_api_key, save_api_key
from rifterm.render import render_heat, render_pepites

app = typer.Typer(help="rifterm — le marché, dans votre terminal.", no_args_is_help=True)
console = Console()
err_console = Console(stderr=True)

_JSON_HELP = "Sortie JSON brute (sans styles ni emoji) — pour scripts et pipes."


def _print_version(value: bool) -> None:
    if value:
        console.print(f"rifterm {__version__} (open source · MIT)")
        raise typer.Exit()


def _json_mode(ctx: typer.Context, local: bool) -> bool:
    """Mode JSON : ``--json`` avant (global) ou après la commande."""
    return local or bool((ctx.obj or {}).get("json"))


def _load_key_or_exit() -> str:
    """Clé API locale, ou message guidé ``rifterm login`` (sans consommer le quota)."""
    api_key = load_api_key()
    if not api_key:
        err_console.print("[red]Pas de clé sauvegardée — [bold]rifterm login <clé>[/bold][/red]")
        raise typer.Exit(code=1)
    return api_key


def _fetch_or_exit(path: str, api_key: str, params: dict[str, object], use_cache: bool) -> dict:
    """Appel API via le cache TTL ; lève une sortie 1 avec le message d'erreur FR."""
    try:
        payload, _resp = fetch(path, api_key=api_key, params=params, use_cache=use_cache)
    except RifApiError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    return payload


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        callback=_print_version,
        is_eager=True,
        help="Affiche la version et quitte.",
    ),
    json_output: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """rifterm — CLI open source de rif. Données RIF sur lerif.ca (clé PRO+)."""
    ctx.obj = {"json": json_output}


@app.command()
def login(
    api_key: str = typer.Argument(..., help="Ta clé API RIF (format rif_…)."),
) -> None:
    """Sauvegarde ta clé API RIF localement (permissions 600)."""
    if not api_key.startswith("rif_"):
        err_console.print("[red]Clé invalide — format attendu : rif_…[/red]")
        raise typer.Exit(code=1)
    path = save_api_key(api_key)
    console.print(f"[green]✓[/green] Clé sauvegardée dans {path} (permissions 600).")
    console.print(f"Teste-la avec [bold]rifterm status[/bold] — config : {config_path()}")


@app.command()
def status() -> None:
    """Vérifie ta clé contre l'API et affiche ton quota quotidien."""
    api_key = load_api_key()
    if not api_key:
        err_console.print("[red]Pas de clé sauvegardée — [bold]rifterm login <clé>[/bold][/red]")
        raise typer.Exit(code=1)
    try:
        resp = get("/cli/heat", api_key=api_key, params={"days": 1, "limit": 1})
    except RifApiError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    remaining = resp.headers.get("X-RateLimit-Remaining", "?")
    console.print("[green]✓[/green] Clé valide — API RIF joignable.")
    console.print(f"  Quota : [bold]{remaining}[/bold] appels restants aujourd'hui.")


@app.command()
def heat(
    ctx: typer.Context,
    days: int = typer.Option(
        1, "--days", min=1, max=30, help="Fenêtre en jours (défaut 1, max 30)."
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Force l'appel API (ignore le cache local de 5 min)."
    ),
    json_local: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Heat Index quotidien — score global + tickers les plus chauds."""
    api_key = _load_key_or_exit()
    payload = _fetch_or_exit("/cli/heat", api_key, params={"days": days}, use_cache=not no_cache)
    render_heat(console, payload, json_mode=_json_mode(ctx, json_local))


@app.command()
def pepites(
    ctx: typer.Context,
    days: int = typer.Option(
        1, "--days", min=1, max=30, help="Fenêtre en jours (défaut 1, max 30)."
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Force l'appel API (ignore le cache local de 5 min)."
    ),
    json_local: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Pépites récentes — ticker, score, heat et signaux."""
    api_key = _load_key_or_exit()
    payload = _fetch_or_exit("/cli/pepites", api_key, params={"days": days}, use_cache=not no_cache)
    render_pepites(console, payload, json_mode=_json_mode(ctx, json_local))


if __name__ == "__main__":
    app()
