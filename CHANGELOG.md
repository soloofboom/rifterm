# Changelog

Tous les changements notables de rifterm sont documentés ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) — versions
[SemVer](https://semver.org/lang/fr/).

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

[0.1.0]: https://github.com/soloofboom/rifterm/releases/tag/v0.1.0