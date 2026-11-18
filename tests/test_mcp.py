"""Tests du serveur MCP : outils heat/pepites/report, clé absente, bornes de days.

Fixtures synthétiques, HTTP mocké au niveau transport — mêmes conventions que
les autres tests CLI. Le SDK ``mcp`` n'est pas requis pour ces tests.
"""

import httpx
import pytest

from rifterm import client, mcp_server
from rifterm.config import save_api_key

HEAT = {"success": True, "count": 1, "data": [{"ticker": "ACME", "heat_index": 72.5}]}
PEPITES = {"success": True, "count": 1, "data": [{"ticker": "ZORG", "score": 88.0}]}


def mock_transport(monkeypatch, tmp_path, handler, *, avec_cle=True):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    if avec_cle:
        save_api_key("rif_cle_synthe_tique")

    def fake_get(path, *, api_key=None, params=None, transport=None):
        return client.get(
            path, api_key=api_key, params=params, transport=httpx.MockTransport(handler)
        )

    monkeypatch.setattr("rifterm.cache.get", fake_get)


def handler_par_endpoint(request):
    if request.url.path.endswith("/cli/heat"):
        return httpx.Response(200, json=HEAT)
    return httpx.Response(200, json=PEPITES)


def test_heat_renvoie_le_payload(tmp_path, monkeypatch):
    mock_transport(monkeypatch, tmp_path, handler_par_endpoint)
    assert mcp_server.heat() == HEAT


def test_pepites_renvoie_le_payload(tmp_path, monkeypatch):
    mock_transport(monkeypatch, tmp_path, handler_par_endpoint)
    assert mcp_server.pepites(days=3) == PEPITES


def test_report_agrege_heat_et_pepites(tmp_path, monkeypatch):
    mock_transport(monkeypatch, tmp_path, handler_par_endpoint)
    payload = mcp_server.report(days=2)
    assert payload == {"report_version": 1, "days": 2, "heat": HEAT, "pepites": PEPITES}


def test_sans_cle_leve_une_erreur_lisible(tmp_path, monkeypatch):
    mock_transport(monkeypatch, tmp_path, handler_par_endpoint, avec_cle=False)
    with pytest.raises(ValueError, match="rifterm login"):
        mcp_server.heat()


@pytest.mark.parametrize("days", [0, 31])
def test_days_hors_bornes_est_refuse(tmp_path, monkeypatch, days):
    mock_transport(monkeypatch, tmp_path, handler_par_endpoint)
    with pytest.raises(ValueError, match="entre 1 et 30"):
        mcp_server.heat(days=days)


def test_erreur_api_remontee_en_valueerror(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(403)

    mock_transport(monkeypatch, tmp_path, handler)
    with pytest.raises(ValueError, match="abonnement"):
        mcp_server.heat()
