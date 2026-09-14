"""Tests du cache TTL : clés, TTL, corruption, fetch (cache hit/miss/force)."""

import json
import time

import httpx
import pytest

from rifterm.cache import cache_dir, cache_get, cache_key, cache_put, fetch
from rifterm.client import RifApiError

PAYLOAD = {"success": True, "count": 1, "data": [{"ticker": "ACME", "heat_index": 51.0}]}


def path_de(monkeypatch, tmp_path, path, params):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    return cache_dir() / f"{cache_key(path, params)}.json"


def test_cache_key_ignore_l_ordre_des_params():
    assert cache_key("/cli/heat", {"days": 3, "limit": 10}) == cache_key(
        "/cli/heat", {"limit": 10, "days": 3}
    )


def test_cache_key_separe_endpoints_et_params():
    assert cache_key("/cli/heat", {"days": 1}) != cache_key("/cli/pepites", {"days": 1})
    assert cache_key("/cli/heat", {"days": 1}) != cache_key("/cli/heat", {"days": 2})


def test_cache_put_get_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    cache_put("/cli/heat", {"days": 1}, PAYLOAD)
    assert cache_get("/cli/heat", {"days": 1}) == PAYLOAD


def test_cache_expiration_rejette_et_supprime(tmp_path, monkeypatch):
    path = path_de(monkeypatch, tmp_path, "/cli/heat", {"days": 1})
    cache_put("/cli/heat", {"days": 1}, PAYLOAD)
    entree = json.loads(path.read_text(encoding="utf-8"))
    entree["expires"] = time.time() - 1
    path.write_text(json.dumps(entree), encoding="utf-8")
    assert cache_get("/cli/heat", {"days": 1}) is None
    assert not path.exists()


def test_cache_corrupt_renvoie_none(tmp_path, monkeypatch):
    path = path_de(monkeypatch, tmp_path, "/cli/heat", {"days": 1})
    cache_dir().mkdir(parents=True, exist_ok=True)
    path.write_text("{{{ pas du json", encoding="utf-8")
    assert cache_get("/cli/heat", {"days": 1}) is None


def test_cache_put_silencieux_si_dossier_bloque(tmp_path, monkeypatch):
    bloque = tmp_path / "bloque"
    bloque.write_text("fichier, pas un dossier", encoding="utf-8")
    # config sous un parent-fichier : cache_dir().mkdir échoue -> OSError -> silencieux
    monkeypatch.setenv("RIFTERM_CONFIG", str(bloque / "config.toml"))
    cache_put("/cli/heat", {"days": 1}, PAYLOAD)  # ne doit pas lever


def test_fetch_cache_hit_sans_transport(tmp_path, monkeypatch):
    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")
    cache_put("/cli/heat", {"days": 1}, PAYLOAD)

    payload, resp = fetch("/cli/heat", api_key="rif_cle", params={"days": 1}, transport=None)
    assert payload == PAYLOAD
    assert resp is None


def test_fetch_miss_puis_cache_hit(tmp_path, monkeypatch):
    path_de(monkeypatch, tmp_path, "/cli/heat", {"days": 1})
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")
    appels = []

    def handler(request):
        appels.append(request)
        return httpx.Response(200, json=PAYLOAD)

    transport = httpx.MockTransport(handler)
    payload, resp = fetch("/cli/heat", api_key="rif_cle", params={"days": 1}, transport=transport)
    assert payload == PAYLOAD
    assert resp is not None
    payload2, resp2 = fetch("/cli/heat", api_key="rif_cle", params={"days": 1}, transport=transport)
    assert payload2 == PAYLOAD
    assert resp2 is None
    assert len(appels) == 1


def test_fetch_use_cache_false_force_le_reseau(tmp_path, monkeypatch):
    path_de(monkeypatch, tmp_path, "/cli/heat", {"days": 1})
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")
    appels = []

    def handler(request):
        appels.append(request)
        return httpx.Response(200, json=PAYLOAD)

    transport = httpx.MockTransport(handler)
    fetch("/cli/heat", api_key="rif_cle", params={"days": 1}, transport=transport)
    payload, resp = fetch(
        "/cli/heat",
        api_key="rif_cle",
        params={"days": 1},
        use_cache=False,
        transport=transport,
    )
    assert payload == PAYLOAD
    assert resp is not None
    assert len(appels) == 2


def test_fetch_json_invalide_leve_rifapierror(tmp_path, monkeypatch):
    path_de(monkeypatch, tmp_path, "/cli/heat", {"days": 1})
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request):
        return httpx.Response(200, text="pas du json")

    with pytest.raises(RifApiError, match="inattendue"):
        fetch(
            "/cli/heat",
            api_key="rif_cle",
            params={"days": 1},
            transport=httpx.MockTransport(handler),
        )


def test_fetch_payload_non_dict_leve(tmp_path, monkeypatch):
    path_de(monkeypatch, tmp_path, "/cli/heat", {"days": 1})
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request):
        return httpx.Response(200, json=[1, 2, 3])

    with pytest.raises(RifApiError, match="payload inattendu"):
        fetch(
            "/cli/heat",
            api_key="rif_cle",
            params={"days": 1},
            transport=httpx.MockTransport(handler),
        )
