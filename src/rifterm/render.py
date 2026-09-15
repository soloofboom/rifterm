"""Rendu des données RIF — tableau rich en terminal, JSON brut en pipe.

Deux sorties par commande :
- ``--json`` : le payload de l'API, tel quel, sans ANSI ni emoji ;
- sinon : rendu rich — les styles sont désactivés automatiquement quand
  stdout n'est pas un TTY (rich détecte), les tableaux restent lisibles.
"""

from __future__ import annotations

import json
from statistics import fmean
from typing import Any

from rich.console import Console
from rich.table import Table

# Valeurs de heat_level observées côté API (normalisées en minuscules).
_LEVEL_STYLES = {"tres hot": "bold red", "hot": "red", "warm": "yellow"}


def _dump_json(payload: dict[str, Any]) -> None:
    """JSON compact sur stdout brut — jq/pipes, aucun style."""
    print(json.dumps(payload, ensure_ascii=False))


def _rows(payload: dict[str, Any], score_key: str) -> list[dict[str, Any]]:
    """Lignes ``data`` triées par score décroissant (sans compter sur le tri serveur)."""
    rows = [row for row in payload.get("data", []) if isinstance(row, dict)]
    return sorted(rows, key=lambda row: float(row.get(score_key) or 0), reverse=True)


def _signals(row: dict[str, Any]) -> str:
    """Signaux lisibles : jusqu'à 3, suffixe ``(+N)`` au-delà."""
    signaux = [str(signal) for signal in (row.get("signals") or [])]
    if not signaux:
        count = row.get("signal_count")
        return f"{count} signal" if isinstance(count, int) and count else "-"
    affiches = ", ".join(signaux[:3])
    if len(signaux) > 3:
        affiches += f" (+{len(signaux) - 3})"
    return affiches


def global_heat(payload: dict[str, Any]) -> float | None:
    """Score global : moyenne du ``heat_index`` du dernier jour (calculée côté client)."""
    rows = _rows(payload, "heat_index")
    if not rows:
        return None
    dernier_jour = max(str(row.get("date", "")) for row in rows)
    lignes_du_jour = [row for row in rows if str(row.get("date")) == dernier_jour]
    return round(fmean(float(row.get("heat_index") or 0) for row in lignes_du_jour), 1)


def render_heat(console: Console, payload: dict[str, Any], *, json_mode: bool) -> None:
    """Heat Index : score global + tableau des tickers, ou payload JSON."""
    if json_mode:
        _dump_json(payload)
        return
    rows = _rows(payload, "heat_index")
    if not rows:
        console.print("Aucune donnée heat disponible pour cette période.")
        return
    dernier_jour = max(str(row.get("date", "")) for row in rows)
    score = global_heat(payload)
    count = payload.get("count", len(rows))
    console.print(
        f"[bold]Heat Index[/bold] — {dernier_jour} · "
        f"score global [bold]{score}[/bold] · {count} lignes"
    )
    console.print("[dim]Score global = moyenne du heat_index du dernier jour.[/dim]")
    table = Table()
    table.add_column("Ticker", style="bold")
    table.add_column("Date")
    table.add_column("Heat", justify="right")
    table.add_column("Niveau")
    table.add_column("Type")
    table.add_column("Conviction", justify="right")
    table.add_column("Signaux")
    for row in rows:
        heat = row.get("heat_index")
        conviction = row.get("conviction_score")
        niveau = str(row.get("heat_level") or "-")
        table.add_row(
            str(row.get("ticker") or "?"),
            str(row.get("date") or "-"),
            f"{float(heat):.1f}" if heat is not None else "-",
            niveau,
            str(row.get("market_type") or "-"),
            f"{float(conviction):.1f}" if conviction is not None else "-",
            _signals(row),
            style=_LEVEL_STYLES.get(niveau.lower(), ""),
        )
    console.print(table)


def render_pepites(console: Console, payload: dict[str, Any], *, json_mode: bool) -> None:
    """Pépites : ticker / score / heat / signaux, ou payload JSON."""
    if json_mode:
        _dump_json(payload)
        return
    rows = _rows(payload, "pepite_score")
    if not rows:
        console.print("Aucune pépite détectée sur la période.")
        return
    count = payload.get("count", len(rows))
    console.print(f"[bold]Pépites[/bold] — {count} lignes sur la période")
    table = Table()
    table.add_column("Ticker", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Heat", justify="right")
    table.add_column("Signaux")
    table.add_column("Date")
    for row in rows:
        score = row.get("pepite_score")
        heat = row.get("heat_index")
        table.add_row(
            str(row.get("ticker") or "?"),
            f"{float(score):.1f}" if score is not None else "-",
            f"{float(heat):.1f}" if heat is not None else "-",
            _signals(row),
            str(row.get("date") or "-"),
        )
    console.print(table)
