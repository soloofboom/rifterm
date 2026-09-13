"""CLI rifterm — le marché, dans votre terminal."""

from __future__ import annotations

import typer
from rich.console import Console

from rifterm import __version__
from rifterm.client import RifApiError, get
from rifterm.config import config_path, load_api_key, save_api_key

app = typer.Typer(help="rifterm — le marché, dans votre terminal.", no_args_is_help=True)
console = Console()
err_console = Console(stderr=True)


def _print_version(value: bool) -> None:
    if value:
        console.print(f"rifterm {__version__} (open source · MIT)")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_print_version,
        is_eager=True,
        help="Affiche la version et quitte.",
    ),
) -> None:
    """rifterm — CLI open source de rif. Données RIF sur lerif.ca (clé PRO+)."""


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


if __name__ == "__main__":
    app()
