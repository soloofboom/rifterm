"""Tests de la config locale (clé API : roundtrip, permissions, corruption)."""

from rifterm.config import config_path, load_api_key, save_api_key


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    path = save_api_key("rif_abc123")
    assert path == config_path()
    assert load_api_key() == "rif_abc123"


def test_permissions_are_0600(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    path = save_api_key("rif_abc123")
    assert path.stat().st_mode & 0o777 == 0o600


def test_load_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "absent.toml"))
    assert load_api_key() is None


def test_load_corrupt_returns_none(tmp_path, monkeypatch):
    p = tmp_path / "config.toml"
    p.write_text("{{{ not toml")
    monkeypatch.setenv("RIFTERM_CONFIG", str(p))
    assert load_api_key() is None
