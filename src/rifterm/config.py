"""Configuration locale de rifterm — stockage de la clé API.

La clé est écrite dans un TOML minimal sous ``~/.config/rifterm/config.toml``
(ou ``$RIFTERM_CONFIG``), avec permissions 0600 : une clé API est un secret.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "rifterm"


def config_path() -> Path:
    """Chemin du fichier de config (override via ``RIFTERM_CONFIG``)."""
    env = os.environ.get("RIFTERM_CONFIG")
    return Path(env) if env else DEFAULT_CONFIG_DIR / "config.toml"


def save_api_key(raw_key: str) -> Path:
    """Écrit la clé dans la config avec permissions 0600. Retourne le chemin."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'api_key = "{raw_key}"\n', encoding="utf-8")
    path.chmod(0o600)
    return path


def load_api_key() -> str | None:
    """Lit la clé sauvegardée, ou ``None`` si absente/illisible."""
    path = config_path()
    if not path.is_file():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return None
    key = data.get("api_key")
    return key if isinstance(key, str) and key else None
