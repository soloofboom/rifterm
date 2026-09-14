"""Cache local TTL — économise le quota quotidien (1000 appels par clé).

Les réponses sont stockées en JSON dans ``<dossier de config>/cache/`` : une
entrée par (endpoint + paramètres), TTL court (5 min par défaut). Un échec
d'écriture ou de lecture est silencieux — le cache est un plus, jamais un
blocage.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx

from rifterm.client import RifApiError, get
from rifterm.config import config_path

CACHE_TTL_SECONDS = 300


def cache_dir() -> Path:
    """Dossier du cache : à côté du fichier de config (``RIFTERM_CONFIG`` respecté)."""
    return config_path().parent / "cache"


def cache_key(path: str, params: dict[str, object] | None) -> str:
    """Clé stable pour un (endpoint + paramètres), indépendante de l'ordre."""
    normalise = json.dumps(params or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{path}?{normalise}".encode()).hexdigest()


def cache_get(path: str, params: dict[str, object] | None) -> dict[str, Any] | None:
    """Payload en cache si le TTL est valide, sinon ``None`` (entrée expirée supprimée)."""
    fichier = cache_dir() / f"{cache_key(path, params)}.json"
    try:
        entree = json.loads(fichier.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(entree, dict) or time.time() >= float(entree.get("expires", 0)):
        try:
            fichier.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    payload = entree.get("payload")
    return payload if isinstance(payload, dict) else None


def cache_put(path: str, params: dict[str, object] | None, payload: dict[str, Any]) -> None:
    """Écrit le payload dans le cache avec un TTL ; échec silencieux."""
    dossier = cache_dir()
    fichier = dossier / f"{cache_key(path, params)}.json"
    entree = {"expires": time.time() + CACHE_TTL_SECONDS, "payload": payload}
    try:
        dossier.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps(entree, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def fetch(
    path: str,
    *,
    api_key: str | None = None,
    params: dict[str, object] | None = None,
    use_cache: bool = True,
    transport: httpx.BaseTransport | None = None,
) -> tuple[dict[str, Any], httpx.Response | None]:
    """``GET`` avec cache TTL : ``(payload, réponse)`` — ``réponse`` est ``None`` en cache hit.

    Lève :py:class:`RifApiError` sur erreur API (401/403/429/5xx, réseau)
    ou corps JSON illisible.
    """
    if use_cache:
        cached = cache_get(path, params)
        if cached is not None:
            return cached, None
    resp = get(path, api_key=api_key, params=params, transport=transport)
    try:
        payload = resp.json()
    except ValueError as exc:
        raise RifApiError("Réponse inattendue de l'API RIF (JSON invalide).") from exc
    if not isinstance(payload, dict):
        raise RifApiError("Réponse inattendue de l'API RIF (payload inattendu).")
    cache_put(path, params, payload)
    return payload, resp
