"""Configuration locale de rifterm — stockage de la clé API.

La clé est écrite dans un TOML minimal sous ``~/.config/rifterm/config.toml``
(ou ``$RIFTERM_CONFIG``), avec permissions 0600 : une clé API est un secret.
"""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "rifterm"

# Charset volontairement strict : la clé est interpolée dans du TOML, donc un
# guillemet ou un retour à la ligne casserait le fichier de config.
API_KEY_RE = re.compile(r"rif_[A-Za-z0-9_-]+")


def config_path() -> Path:
    """Chemin du fichier de config (override via ``RIFTERM_CONFIG``)."""
    env = os.environ.get("RIFTERM_CONFIG")
    return Path(env) if env else DEFAULT_CONFIG_DIR / "config.toml"


def save_api_key(raw_key: str) -> Path:
    """Écrit la clé dans la config avec permissions 0600 dès la création."""
    if not API_KEY_RE.fullmatch(raw_key):
        raise ValueError(
            "Clé invalide — format attendu : rif_… (lettres, chiffres, - et _ uniquement)."
        )
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_CREAT + mode 0600 : le fichier n'existe jamais lisible par les autres,
    # même brièvement (write_text + chmod laissait une fenêtre en 0644).
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f'api_key = "{raw_key}"\n')
    path.chmod(0o600)  # un fichier préexistant garde sinon ses anciens droits
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
