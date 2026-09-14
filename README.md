# rifterm

> Le marché, dans votre terminal.

CLI open source (MIT) de [rif](https://lerif.ca) — Heat Index, pépites et
données de marché en ligne de commande. Le CLI est gratuit, les données sont
payantes.

**Statut : v0.1.** Publication PyPI prévue au lancement — en attendant :
`pip install -e .` depuis le dépôt.

## Utilisation

```bash
pipx install rifterm      # (à venir — publication PyPI prévue)
```

```text
rifterm login <clé>    Sauvegarde ta clé API RIF (format rif_…)
rifterm heat           Heat Index quotidien — score global + tickers
rifterm pepites        Pépites récentes — ticker, score, heat, signaux
rifterm status         État de ta clé + quota quotidien
```

Options utiles (sur `heat` et `pepites`) :

- `--days N` — fenêtre en jours (1–30, défaut 1)
- `--no-cache` — force l'appel API en ignorant le cache local (TTL 5 min)
- `--json` — sortie JSON brute, sans styles ni emoji (global ou par commande)

Exemples :

```bash
rifterm heat                 # tableau riche dans le terminal
rifterm heat --json | jq '.data[0]'
rifterm pepites --days 3 --json
```

Les données nécessitent une clé API (abonnement PRO+ sur
[lerif.ca/rifterm](https://lerif.ca/rifterm)). Le CLI lui-même est gratuit et
open source.

Le cache local (5 min, par endpoint + paramètres, dans le dossier de config)
économise ton quota quotidien de 1000 appels ; `--no-cache` pour forcer.

## Développement

```bash
git clone https://github.com/soloofboom/rifterm
cd rifterm
pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

Architecture :

- `src/rifterm/cli.py` — commandes Typer
- `src/rifterm/client.py` — client HTTP (`X-API-Key`, erreurs FR, quotas)
- `src/rifterm/cache.py` — cache TTL local (5 min, quota 1000/jour)
- `src/rifterm/render.py` — rendu rich vs JSON
- `src/rifterm/config.py` — clé API locale (`~/.config/rifterm/config.toml`, 0600)

Variables d'environnement :

- `RIFTERM_API_URL` — URL de base de l'API (défaut : `https://lerif.ca`)
- `RIFTERM_CONFIG` — chemin de la config (défaut : `~/.config/rifterm/config.toml`)

## Feuille de route

`rifterm report` (agrégat quotidien + export Markdown/JSON) arrive en v0.2 —
suivi dans l'issue [#3](https://github.com/soloofboom/rifterm/issues/3).

## Licence

[MIT](LICENSE) — forkez, auditez, contribuez.