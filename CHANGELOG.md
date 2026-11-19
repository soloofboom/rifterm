# Changelog

Tous les changements notables de rifterm sont documentés ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) — versions
[SemVer](https://semver.org/lang/fr/).

## Non publié

### Sécurité

- La clé API est créée directement en `0600` : plus de fenêtre lisible entre
  l'écriture du fichier et le `chmod`.
- `rifterm login --stdin` lit la clé sur l'entrée standard, sans la laisser dans
  l'historique shell ni dans `ps`.
- `RIFTERM_API_URL` refuse `http://` hors localhost — la clé ne peut plus partir
  en clair vers un hôte détourné.
- Le charset de la clé est validé avant écriture (une clé contenant un guillemet
  ne peut plus casser le TOML).
- CI : permissions du workflow limitées à `contents: read`.

## [0.3.0] — 2026-11-18

### Ajouté

- `rifterm mcp` — serveur MCP (stdio) exposant `heat`, `pepites` et `report`
  aux agents IA compatibles (Claude, Codex, Cursor). Extra optionnel :
  `pip install 'rifterm[mcp]'`.

## [0.2.0] — 2026-11-17

### Ajouté

- `rifterm report` — agrégat côté CLI de `heat` et `pepites`, avec lecture
  normale, `--json` et export `--out report.md` / `--out report.json`.

### Note

- L'endpoint serveur `/cli/report` n'est pas encore branché; la commande
  appelle pour l'instant `/cli/heat` + `/cli/pepites`.

## [0.1.0] — 2026-09-14

Première version fonctionnelle du CLI — données Heat Index et pépites
depuis l'API RIF.

### Ajouté

- `rifterm login <clé>` — sauvegarde de la clé API RIF (config locale,
  permissions 600).
- `rifterm heat` — Heat Index quotidien : score global + tickers les plus
  chauds, rendu riche en terminal.
- `rifterm pepites` — pépites récentes : ticker, score, heat, signaux.
- `rifterm status` — validité de la clé + quota quotidien restant.
- `--json` (global ou par commande) — sortie JSON brute pour scripts et
  pipes, `--days N` (1–30), `--no-cache`.
- Cache local TTL 5 min par endpoint — économise le quota de 1000 appels/jour.

[0.3.0]: https://github.com/soloofboom/rifterm/releases/tag/v0.3.0
[0.2.0]: https://github.com/soloofboom/rifterm/releases/tag/v0.2.0
[0.1.0]: https://github.com/soloofboom/rifterm/releases/tag/v0.1.0
