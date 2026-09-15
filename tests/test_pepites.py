"""Tests pepites : rendu rich, --json, cache, erreurs — fixtures 100 % synthétiques."""

import json

import httpx
from typer.testing import CliRunner

from rifterm import client
from rifterm.cli import app

runner = CliRunner()

# Valeurs inventées (tickers, scores, dates, signaux) — clés du schéma réelles uniquement.
PEPITES_FIXTURE = {
    "success": True,
    "count": 2,
    "data": [
        {
            "ticker": "ACME",
            "pepite_score": 78.4,
            "heat_index": 42.1,
            "finviz_screeners_hit": 1,
            "reddit_mentions": 0,
            "signal_count": 2,
            "signals": ["bullish_news", "yahoo_trending"],
            "snapshot_source": "pepites_detected",
            "date": "2026-01-15",
        },
        {
            "ticker": "ZORG",
            "pepite_score": 65.0,
            "heat_index": 31.7,
            "finviz_screeners_hit": 0,
            "reddit_mentions": 2,
            "signal_count": 1,
            "signals": ["social_buzz"],
            "snapshot_source": "pepites_detected",
            "date": "2026-01-14",
        },
    ],
}


def mock_transport(monkeypatch, tmp_path, handler):
    """Config temporaire, clé synthétique, transport HTTP mocké.

    Le wrapper ignore tout ``transport`` reçu du code testé et force
    MockTransport — le HTTP ne quitte jamais la machine.
    """
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))

    def fake_get(path, *, api_key=None, params=None, transport=None):
        return client.get(
            path, api_key=api_key, params=params, transport=httpx.MockTransport(handler)
        )

    monkeypatch.setattr("rifterm.cache.get", fake_get)
    runner.invoke(app, ["login", "rif_cle_synthe_tique"])


def test_pepites_rich_affiche_tickers_scores_et_signaux(tmp_path, monkeypatch):
    vus = {}

    def handler(request):
        vus["path"] = request.url.path
        vus["days"] = request.url.params.get("days")
        return httpx.Response(200, json=PEPITES_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["pepites"])
    assert result.exit_code == 0
    assert "ACME" in result.output
    assert "78.4" in result.output
    assert "bullish_news" in result.output
    # stdout non-TTY : aucun style ANSI, même sans --json.
    assert "\x1b[" not in result.output
    assert vus["path"].endswith("/api/v1/cli/pepites")
    assert vus["days"] == "1"


def test_pepites_json_renvoie_le_payload(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=PEPITES_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["--json", "pepites"])
    assert result.exit_code == 0
    assert json.loads(result.output) == PEPITES_FIXTURE
    assert "\x1b[" not in result.output


def test_pepites_transmet_le_parametre_days(tmp_path, monkeypatch):
    vus = {}

    def handler(request):
        vus["days"] = request.url.params.get("days")
        return httpx.Response(200, json=PEPITES_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    assert runner.invoke(app, ["pepites", "--days", "5", "--json"]).exit_code == 0
    assert vus["days"] == "5"


def test_pepites_rejoue_depuis_le_cache_sans_appel_reseau(tmp_path, monkeypatch):
    appels = []

    def handler(request):
        appels.append(request)
        return httpx.Response(200, json=PEPITES_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    assert runner.invoke(app, ["pepites"]).exit_code == 0
    assert runner.invoke(app, ["pepites"]).exit_code == 0
    assert len(appels) == 1


def test_pepites_401_message_guide_login(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(401, json={"success": False})

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["pepites"])
    assert result.exit_code == 1
    assert "login" in result.output


def test_pepites_403_pointe_vers_abonnement_pro_plus(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(403, json={"success": False})

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["pepites"])
    assert result.exit_code == 1
    assert "PRO+" in result.output
    assert "lerif.ca/rifterm" in result.output


def test_pepites_payload_vide_message_clair(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"success": True, "count": 0, "data": []})

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["pepites"])
    assert result.exit_code == 0
    assert "Aucune pépite" in result.output
