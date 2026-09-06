"""Client HTTP vers l'API RIF — header ``X-API-Key`` et erreurs lisibles."""

from __future__ import annotations

import os

import httpx

from rifterm import __version__

DEFAULT_BASE_URL = "https://lerif.ca"
API_PREFIX = "/api/v1"


class RifApiError(Exception):
    """Erreur d'appel API, avec un message prêt à afficher en français."""


def base_url() -> str:
    """URL de base de l'API (override via ``RIFTERM_API_URL``, utile en dev)."""
    return os.environ.get("RIFTERM_API_URL", DEFAULT_BASE_URL).rstrip("/")


def get(
    path: str,
    *,
    api_key: str | None = None,
    params: dict[str, object] | None = None,
    transport: httpx.BaseTransport | None = None,
) -> httpx.Response:
    """``GET {base}/api/v1{path}`` avec ``X-API-Key`` si fournie.

    Lève :py:class:`RifApiError` (message en français) sur 401/403/429/5xx
    ou erreur réseau. Retourne la réponse brute — le quota restant est dans
    les en-têtes ``X-RateLimit-*``.
    """
    headers = {"User-Agent": f"rifterm/{__version__}"}
    if api_key:
        headers["X-API-Key"] = api_key
    url = f"{base_url()}{API_PREFIX}{path}"
    try:
        with httpx.Client(timeout=15, transport=transport, headers=headers) as client:
            resp = client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise RifApiError(f"Impossible de joindre l'API RIF ({exc}).") from exc

    if resp.status_code == 401:
        raise RifApiError(
            "Clé API invalide ou révoquée — rifterm login <clé> pour enregistrer une nouvelle clé."
        )
    if resp.status_code == 403:
        raise RifApiError("L'accès API nécessite un abonnement PRO+ — lerif.ca/pricing.")
    if resp.status_code == 429:
        raise RifApiError("Quota quotidien atteint (1000 appels/jour) — reviens demain.")
    if resp.status_code >= 500:
        raise RifApiError(f"L'API RIF a un souci (HTTP {resp.status_code}) — réessaie plus tard.")
    if resp.status_code != 200:
        raise RifApiError(f"Appel API échoué (HTTP {resp.status_code}).")
    return resp
