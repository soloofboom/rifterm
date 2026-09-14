"""Client HTTP vers l'API RIF — header ``X-API-Key`` et erreurs lisibles."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import httpx

from rifterm import __version__

DEFAULT_BASE_URL = "https://lerif.ca"
API_PREFIX = "/api/v1"


class RifApiError(Exception):
    """Erreur d'appel API, avec un message prêt à afficher en français."""


def base_url() -> str:
    """URL de base de l'API (override via ``RIFTERM_API_URL``, utile en dev)."""
    return os.environ.get("RIFTERM_API_URL", DEFAULT_BASE_URL).rstrip("/")


def rate_reset_local(headers: httpx.Headers) -> str | None:
    """Heure locale (``HH:MM``) de réinitialisation du quota.

    Calculée depuis ``X-RateLimit-Reset`` — l'epoch de minuit UTC côté
    serveur. ``None`` si l'en-tête est absent ou illisible.
    """
    raw = headers.get("X-RateLimit-Reset")
    if not raw:
        return None
    try:
        epoch = int(raw)
    except (TypeError, ValueError):
        return None
    reset = datetime.fromtimestamp(epoch, tz=UTC).astimezone()
    return reset.strftime("%H:%M")


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
        raise RifApiError(
            "L'accès API nécessite un abonnement PRO+ — abonne-toi sur lerif.ca/rifterm."
        )
    if resp.status_code == 429:
        reset = rate_reset_local(resp.headers)
        if reset:
            raise RifApiError(
                "Quota quotidien atteint (1000 appels/jour) — "
                f"réinitialisation à {reset} heure locale (minuit UTC)."
            )
        raise RifApiError(
            "Quota quotidien atteint (1000 appels/jour) — réinitialisation à minuit UTC."
        )
    if resp.status_code >= 500:
        raise RifApiError(f"L'API RIF a un souci (HTTP {resp.status_code}) — réessaie plus tard.")
    if resp.status_code != 200:
        raise RifApiError(f"Appel API échoué (HTTP {resp.status_code}).")
    return resp
