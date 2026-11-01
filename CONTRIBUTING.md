# Contribuer à rifterm

Merci de vouloir contribuer ! Le projet est petit — le processus l'est aussi.

## Setup

```bash
git clone https://github.com/soloofboom/rifterm
cd rifterm
pip install -e ".[dev]"
```

## Avant de proposer un changement

```bash
pytest
ruff check .
ruff format --check .
```

Tout doit être vert. La CI rejoue exactement ces trois commandes.

## Flow

1. Branche nommée `feature/<slug>` ou `fix/<slug>` depuis `main`.
2. Une PR par sujet, petite et focalisée. Les tests nouveaux accompagnent
   chaque comportement nouveau.
3. Le français est bienvenu (messages d'erreur, docs) — le code et les
   identifiants restent en anglais.

## Conventions du code

- Stack : Typer (CLI), httpx (HTTP), rich (rendu terminal).
- Aucune dépendance nouvelle sans discussion préalable dans une issue.
- Le CLI consomme uniquement les endpoints `/api/v1/cli/*` (clé API PRO+) —
  jamais de scraping direct du site.
- Aucun secret dans le code ou l'historique : la clé API vit chez
  l'utilisateur final (`~/.config/rifterm/`), jamais dans ce repo.

## Signaler un bug ou proposer une idée

Ouvre une [issue](https://github.com/soloofboom/rifterm/issues) avec :
la commande exacte lancée, la sortie, et la version (`rifterm --version`).