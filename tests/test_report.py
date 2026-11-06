"""Tests report : agrégat CLI, JSON, export Markdown/JSON — fixtures synthétiques."""

import json

import httpx
from typer.testing import CliRunner

from rifterm import client
from rifterm.cli import app

runner = CliRunner()

HEAT_FIXTURE = {
    "success": True,
    "count": 1,
    "data": [
        {
            "ticker": "ACME",
            "heat_index": 72.5,
            "heat_level": "HOT",
            "market_type": "tradfi",
            "date": "2026-01-15",
            "conviction_score": 61.0,
            "signal_count": 2,
            "signals": ["bullish_news", "social_buzz"],
        }
    ],
}

PEPITES_FIXTURE = {
    "success": True,
    "count": 1,
    "data": [
        {
            "ticker": "ACME",
            "pepite_score": 78.4,
            "heat_index": 42.1,
            "signal_count": 1,
            "signals": ["yahoo_trending"],
            "date": "2026-01-15",
        }
    ],
}


def mock_transport(monkeypatch, tmp_path, handler):
    """Config temporaire, clé synthétique, HTTP mocké (même pattern que heat/pépites)."""
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))

    def fake_get(path, *, api_key=None, params=None, transport=None):
        return client.get(
            path,
            api_key=api_key,
            params=params,
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr("rifterm.cache.get", fake_get)
    runner.invoke(app, ["login", "rif_cle_synthe_tique"])


def report_payload():
    return {
        "report_version": 1,
        "days": 2,
        "heat": HEAT_FIXTURE,
        "pepites": PEPITES_FIXTURE,
    }


def fixture_for(request):
    endpoint = request.url.path.rsplit("/", 1)[-1]
    return HEAT_FIXTURE if endpoint == "heat" else PEPITES_FIXTURE


def test_report_agrege_heat_et_pepites_par_endpoint(tmp_path, monkeypatch):
    appels = []

    def handler(request):
        appels.append((request.url.path, request.url.params.get("days")))
        return httpx.Response(200, json=fixture_for(request))

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["report", "--days", "2"])
    assert result.exit_code == 0
    assert appels == [
        ("/api/v1/cli/heat", "2"),
        ("/api/v1/cli/pepites", "2"),
    ]
    assert "Rapport rifterm" in result.output
    assert "ACME" in result.output
    assert "Endpoint serveur /cli/report non branché" in result.output
    assert "\x1b[" not in result.output


def test_report_json_renvoie_l_agregat(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=fixture_for(request))

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["report", "--days", "2", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == report_payload()
    assert "\x1b[" not in result.output


def test_report_export_markdown(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=fixture_for(request))

    mock_transport(monkeypatch, tmp_path, handler)
    out = tmp_path / "report.md"
    result = runner.invoke(app, ["report", "--days", "2", "--out", str(out)])
    assert result.exit_code == 0
    content = out.read_text()
    assert "# Rapport rifterm" in content
    assert "Période : 2 jour(s)" in content
    assert "ACME" in content
    assert "\x1b[" not in content


def test_report_export_json(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=fixture_for(request))

    mock_transport(monkeypatch, tmp_path, handler)
    out = tmp_path / "report.json"
    result = runner.invoke(app, ["report", "--days", "2", "--out", str(out)])
    assert result.exit_code == 0
    assert json.loads(out.read_text()) == report_payload()


def test_report_export_refuse_un_autre_format(tmp_path, monkeypatch):
    out = tmp_path / "report.txt"
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    result = runner.invoke(app, ["report", "--out", str(out)])
    assert result.exit_code == 1
    assert "--out attend" in result.output
    assert ".md ou .json" in result.output
    assert out.exists() is False
