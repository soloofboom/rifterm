# rifterm

> Le marché, dans votre terminal.

CLI open source (MIT) de [rif](https://lerif.ca) — Heat Index, pépites et
rapports quotidiens en ligne de commande.

**Statut : en construction.** La version initiale arrive bientôt — rejoignez
la liste d'attente sur [lerif.ca/rifterm](https://lerif.ca/rifterm).

## Installation (à venir)

```bash
pipx install rifterm
```

Publication sur PyPI prévue au lancement — le paquet n'est pas encore publié.

## Utilisation prévue

```text
rifterm login <clé>    Sauvegarde ta clé API RIF (format rif_…)
rifterm heat           Heat Index 0–100 + détail des sources
rifterm pepites        Pépites détectées (24h)
rifterm report         Rapport quotidien (JSON / Markdown)
rifterm status         État de ta clé + quota quotidien
rifterm --json         Sortie JSON pour scripts / pipe
```

Les données RIF nécessitent une clé API (abonnement PRO+ sur
[lerif.ca/pricing](https://lerif.ca/pricing)). Le CLI lui-même est gratuit
et open source.

## Développement

```bash
git clone https://github.com/soloofboom/rifterm
cd rifterm
pip install -e ".[dev]"
pytest
ruff check .
```

Architecture :

- `src/rifterm/cli.py` — commandes Typer
- `src/rifterm/client.py` — client HTTP (`X-API-Key`, erreurs FR, quotas)
- `src/rifterm/config.py` — clé API locale (`~/.config/rifterm/config.toml`, 0600)

Variables d'environnement :

- `RIFTERM_API_URL` — URL de base de l'API (défaut : `https://lerif.ca`)
- `RIFTERM_CONFIG` — chemin de la config (défaut : `~/.config/rifterm/config.toml`)

## Licence

[MIT](LICENSE) — forkez, auditez, contribuez.