"""CLI rifterm — le marché, dans votre terminal."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from rifterm import __version__
from rifterm.cache import fetch
from rifterm.client import RifApiError, get
from rifterm.config import config_path, load_api_key, save_api_key
from rifterm.render import render_heat, render_pepites, report_markdown

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


def write_text_or_exit(path: str, content: str) -> None:
    """Export fichier avec une erreur lisible si le chemin est indisponible."""
    try:
        Path(path).write_text(content, encoding="utf-8", newline="\n")
    except OSError as exc:
        err_console.print(f"[red]Écriture impossible dans {path} — {exc}[/red]")
        raise typer.Exit(code=1) from exc


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


@app.command()
def report(
    ctx: typer.Context,
    days: int = typer.Option(
        1, "--days", min=1, max=30, help="Fenêtre en jours (défaut 1, max 30)."
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Force l'appel API (ignore le cache local de 5 min)."
    ),
    out: str | None = typer.Option(
        None, "--out", help="Fichier d'export (.md ou .json) au lieu de la sortie terminal."
    ),
    json_local: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Agrégat heat + pépites, export Markdown/JSON.

    Côté CLI seulement : l'endpoint serveur ``/cli/report`` n'est pas encore
    branché, donc les données viennent des endpoints ``heat`` et ``pepites``.
    """
    suffix = ""
    if out is not None:
        suffix = out.rsplit(".", 1)[-1].lower() if "." in out else ""
        if suffix not in {"json", "md"} or not Path(out).parent.is_dir():
            err_console.print(
                "[red]--out attend un dossier existant et le format .md ou .json.[/red]"
            )
            raise typer.Exit(code=1)

    api_key = _load_key_or_exit()
    heat_payload = _fetch_or_exit(
        "/cli/heat",
        api_key,
        params={"days": days},
        use_cache=not no_cache,
    )
    pepites_payload = _fetch_or_exit(
        "/cli/pepites",
        api_key,
        params={"days": days},
        use_cache=not no_cache,
    )
    payload = {
        "report_version": 1,
        "days": days,
        "heat": heat_payload,
        "pepites": pepites_payload,
    }

    if out is None:
        if _json_mode(ctx, json_local):
            print(json.dumps(payload, ensure_ascii=False))
        else:
            console.rule("Rapport rifterm")
            console.print("[dim]Endpoint serveur /cli/report non branché — agrégat local.[/dim]")
            render_heat(console, heat_payload, json_mode=False)
            console.print()
            render_pepites(console, pepites_payload, json_mode=False)
        return

    content = (
        json.dumps(payload, ensure_ascii=False) + "\n"
        if suffix == "json"
        else report_markdown(payload)
    )
    write_text_or_exit(out, content)
    console.print(f"[green]✓[/green] Rapport écrit dans [bold]{out}[/bold].")


if __name__ == "__main__":
    app()
