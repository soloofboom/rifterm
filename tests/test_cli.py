"""Tests CLI : --version, login (validation + persistance), status (quota/erreurs)."""

import httpx
from typer.testing import CliRunner

from rifterm.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_login_saves_key(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    result = runner.invoke(app, ["login", "rif_abc123"])
    assert result.exit_code == 0
    assert "rif_abc123" in (tmp_path / "config.toml").read_text()


def test_login_rejects_bad_prefix(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    result = runner.invoke(app, ["login", "not-a-rif-key"])
    assert result.exit_code == 1
    assert not (tmp_path / "config.toml").exists()


def test_status_without_key(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "login" in result.output


def test_status_with_valid_key_shows_quota(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    runner.invoke(app, ["login", "rif_abc123"])

    def fake_get(path, *, api_key=None, params=None, transport=None):
        assert api_key == "rif_abc123"
        assert path == "/heat-index/daily"
        return httpx.Response(200, json={"success": True}, headers={"X-RateLimit-Remaining": "998"})

    monkeypatch.setattr("rifterm.cli.get", fake_get)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "998" in result.output


def test_status_with_invalid_key_exits_1(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    runner.invoke(app, ["login", "rif_abc123"])

    def fake_get(path, *, api_key=None, params=None, transport=None):
        from rifterm.client import RifApiError

        raise RifApiError(
            "Clé API invalide ou révoquée — rifterm login <clé> pour enregistrer une nouvelle clé."
        )

    monkeypatch.setattr("rifterm.cli.get", fake_get)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "invalide" in result.output
