"""Serveur MCP (stdio) — expose heat, pepites et report aux harness IA.

Le serveur tourne sur la machine du client, lit la clé depuis le même
``config.toml`` que le CLI et réutilise le cache TTL 5 min. Aucune clé tierce,
aucun LLM embarqué : l'agent appelle les outils, le modèle reste le sien.
"""

from __future__ import annotations

from typing import Any

from rifterm.cache import fetch
from rifterm.client import RifApiError
from rifterm.config import load_api_key


def _fetch(path: str, days: int) -> dict[str, Any]:
    if not 1 <= days <= 30:
        raise ValueError("days doit être entre 1 et 30.")
    api_key = load_api_key()
    if not api_key:
        raise ValueError("Pas de clé API RIF — lance `rifterm login <clé>` d'abord.")
    try:
        payload, _ = fetch(path, api_key=api_key, params={"days": days})
    except RifApiError as exc:
        raise ValueError(str(exc)) from exc
    return payload


def heat(days: int = 1) -> dict[str, Any]:
    """Heat Index quotidien : score global et tickers les plus chauds.

    Args:
        days: fenêtre en jours, 1 à 30 (défaut 1).
    """
    return _fetch("/cli/heat", days)


def pepites(days: int = 1) -> dict[str, Any]:
    """Pépites récentes : ticker, score, heat et signaux.

    Args:
        days: fenêtre en jours, 1 à 30 (défaut 1).
    """
    return _fetch("/cli/pepites", days)


def report(days: int = 1) -> dict[str, Any]:
    """Rapport agrégé : heat + pépites de la même fenêtre, en un seul objet JSON.

    Args:
        days: fenêtre en jours, 1 à 30 (défaut 1).
    """
    return {
        "report_version": 1,
        "days": days,
        "heat": _fetch("/cli/heat", days),
        "pepites": _fetch("/cli/pepites", days),
    }


def main() -> None:
    """Démarre le serveur MCP sur stdio."""
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError:
        raise SystemExit("Le SDK MCP n'est pas installé — pip install 'rifterm[mcp]'.") from None

    server = MCPServer("rifterm")
    for tool in (heat, pepites, report):
        server.tool()(tool)
    server.run()
