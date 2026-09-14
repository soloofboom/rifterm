"""Tests heat : rendu rich, --json (avant/après la commande), cache, erreurs.

Fixtures 100 % synthétiques — valeurs inventées, seules les clés du schéma
sont réelles. Le HTTP est mocké au niveau transport (httpx.MockTransport),
le vrai client + le vrai cache TTL sont exercés.
"""

import json
from datetime import UTC, datetime, timedelta

import httpx
from typer.testing import CliRunner

from rifterm import client
from rifterm.cli import app

runner = CliRunner()

# Valeurs inventées (tickers, scores, dates) — clés du schéma réelles uniquement.
HEAT_FIXTURE = {
    "success": True,
    "count": 2,
    "data": [
        {
            "ticker": "ACME",
            "heat_index": 72.5,
            "heat_level": "HOT",
            "market_type": "tradfi",
            "date": "2026-01-15",
            "conviction_score": 61.0,
            "finviz_score": None,
            "finviz_screeners_hit": None,
            "reddit_mentions": None,
            "reddit_score": 55.0,
            "signal_count": 2,
            "signals": ["bullish_news", "social_buzz"],
            "snapshot_source": "heat_daily",
        },
        {
            "ticker": "ZORG",
            "heat_index": 48.2,
            "heat_level": "WARM",
            "market_type": "crypto",
            "date": "2026-01-15",
            "conviction_score": None,
            "finviz_score": None,
            "finviz_screeners_hit": None,
            "reddit_mentions": None,
            "reddit_score": None,
            "signal_count": 0,
            "signals": [],
            "snapshot_source": "heat_daily",
        },
    ],
}

HEAT_VIDE = {"success": True, "count": 0, "data": []}


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


def test_heat_rich_affiche_score_global_et_tickers(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=HEAT_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat"])
    assert result.exit_code == 0
    assert "Heat Index" in result.output
    assert "ACME" in result.output
    assert "ZORG" in result.output
    assert "72.5" in result.output
    # stdout non-TTY : aucun style ANSI, même sans --json.
    assert "\x1b[" not in result.output


def test_heat_json_avant_la_commande_renvoie_le_payload(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=HEAT_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["--json", "heat"])
    assert result.exit_code == 0
    assert json.loads(result.output) == HEAT_FIXTURE


def test_heat_json_apres_la_commande_renvoie_le_payload(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=HEAT_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == HEAT_FIXTURE
    assert "\x1b[" not in result.output


def test_heat_transmet_le_parametre_days(tmp_path, monkeypatch):
    vus = {}

    def handler(request):
        vus["days"] = request.url.params.get("days")
        vus["path"] = request.url.path
        return httpx.Response(200, json=HEAT_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat", "--days", "3"])
    assert result.exit_code == 0
    assert vus["days"] == "3"
    assert vus["path"].endswith("/api/v1/cli/heat")


def test_heat_refuse_days_hors_bornes(tmp_path, monkeypatch):
    mock_transport(monkeypatch, tmp_path, lambda request: httpx.Response(200, json=HEAT_FIXTURE))
    result = runner.invoke(app, ["heat", "--days", "45"])
    assert result.exit_code != 0


def test_heat_sans_cle_ne_consomme_pas_le_quota(tmp_path, monkeypatch):
    appele = []

    def handler(request):
        appele.append(request)
        return httpx.Response(200, json=HEAT_FIXTURE)

    monkeypatch.setenv("RIFTERM_CONFIG", str(tmp_path / "config.toml"))
    monkeypatch.setattr(
        "rifterm.cache.get",
        lambda path, **kwargs: client.get(
            path,
            **{**kwargs, "transport": httpx.MockTransport(handler)},
        ),
    )
    result = runner.invoke(app, ["heat"])
    assert result.exit_code == 1
    assert "login" in result.output
    assert appele == []


def test_heat_rejoue_depuis_le_cache_sans_appel_reseau(tmp_path, monkeypatch):
    appels = []

    def handler(request):
        appels.append(request)
        return httpx.Response(200, json=HEAT_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    assert runner.invoke(app, ["heat"]).exit_code == 0
    assert runner.invoke(app, ["heat"]).exit_code == 0
    assert len(appels) == 1


def test_heat_no_cache_force_un_deuxieme_appel(tmp_path, monkeypatch):
    appels = []

    def handler(request):
        appels.append(request)
        return httpx.Response(200, json=HEAT_FIXTURE)

    mock_transport(monkeypatch, tmp_path, handler)
    assert runner.invoke(app, ["heat"]).exit_code == 0
    assert runner.invoke(app, ["heat", "--no-cache"]).exit_code == 0
    assert len(appels) == 2


def test_heat_401_message_guide_login(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(401, json={"success": False})

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat"])
    assert result.exit_code == 1
    assert "login" in result.output


def test_heat_403_pointe_vers_abonnement_pro_plus(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(403, json={"success": False})

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat"])
    assert result.exit_code == 1
    assert "PRO+" in result.output
    assert "lerif.ca/rifterm" in result.output


def test_heat_429_affiche_le_reset_en_heure_locale(tmp_path, monkeypatch):
    epoch_reset = int(
        (
            datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        ).timestamp()
    )
    attendu = datetime.fromtimestamp(epoch_reset, tz=UTC).astimezone().strftime("%H:%M")

    def handler(request):
        return httpx.Response(
            429,
            json={"success": False},
            headers={"X-RateLimit-Reset": str(epoch_reset)},
        )

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat"])
    assert result.exit_code == 1
    # rich peut replier la ligne à 80 colonnes : on compare sans les retours à la ligne.
    message = " ".join(result.output.split())
    assert "Quota" in message
    assert f"réinitialisation à {attendu} heure locale" in message
    assert "minuit UTC" in message


def test_heat_5xx_invite_a_reessayer(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(503, json={})

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat"])
    assert result.exit_code == 1
    assert "réessaie plus tard" in result.output


def test_heat_payload_vide_message_clair(tmp_path, monkeypatch):
    def handler(request):
        return httpx.Response(200, json=HEAT_VIDE)

    mock_transport(monkeypatch, tmp_path, handler)
    result = runner.invoke(app, ["heat"])
    assert result.exit_code == 0
    assert "Aucune donnée" in result.output
