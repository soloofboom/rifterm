"""Tests du client HTTP : header X-API-Key, erreurs FR, réponse brute."""

import httpx
import pytest

from rifterm.client import RifApiError, get


def test_get_sends_api_key_and_ua(monkeypatch):
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-API-Key"] == "rif_abc123"
        assert request.headers["User-Agent"].startswith("rifterm/")
        return httpx.Response(200, json={"success": True})

    resp = get("/health", api_key="rif_abc123", transport=httpx.MockTransport(handler))
    assert resp.status_code == 200


def test_get_without_key_sends_no_header(monkeypatch):
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request: httpx.Request) -> httpx.Response:
        assert "X-API-Key" not in request.headers
        return httpx.Response(200, json={"success": True})

    resp = get("/health", transport=httpx.MockTransport(handler))
    assert resp.status_code == 200


def test_401_raises_invalide(monkeypatch):
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"success": False})

    with pytest.raises(RifApiError, match="invalide"):
        get("/health", api_key="rif_mauvaise", transport=httpx.MockTransport(handler))


def test_403_raises_pro_plus(monkeypatch):
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"success": False})

    with pytest.raises(RifApiError, match="PRO\\+"):
        get("/health", api_key="rif_gratuite", transport=httpx.MockTransport(handler))


def test_429_raises_quota(monkeypatch):
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"success": False})

    with pytest.raises(RifApiError, match="[Qq]uota"):
        get("/health", api_key="rif_ok", transport=httpx.MockTransport(handler))


def test_500_raises_souci(monkeypatch):
    monkeypatch.setenv("RIFTERM_API_URL", "https://test.local")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={})

    with pytest.raises(RifApiError, match="souci"):
        get("/health", transport=httpx.MockTransport(handler))
