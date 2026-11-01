# Sécurité

## Signaler une vulnérabilité

**Ne pas ouvrir d'issue publique pour une faille de sécurité.** Utilise le
signalement privé : onglet *Security* → *Report a vulnerability* du repo
GitHub, ou contacte le mainteneur via la page du profil soloofboom.

Une réponse sous 7 jours, une correction prioritaire pour tout ce qui touche
les clés API des utilisateurs.

## Périmètre

- **Dans le périmètre** : le code de ce repo (`src/rifterm/`), le workflow
  de publication, la gestion locale de la clé API (`~/.config/rifterm/`).
- **Hors périmètre** : l'API RIF elle-même (lerif.ca) et ses endpoints —
  les failles côté serveur se rapportent séparément au mainteneur, pas via
  les issues publiques de ce repo.

## Bonnes pratiques en vigueur

- Publication PyPI par [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
  (OIDC) — aucun token PyPI stocké dans le repo, aucun secret dans le
  workflow. La publication ne se déclenche que sur push de tag.
- La clé API RIF est stockée localement avec permissions 600 et envoyée
  uniquement à `https://lerif.ca` (HTTPS, header `X-API-Key`). Elle n'est
  jamais journalisée ni transmise ailleurs.
- `RIFTERM_API_URL` permet de pointer ailleurs pour le développement —
  un utilisateur qui le fait sait ce qu'il fait.