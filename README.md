# Radar GEO Influa

Classement quotidien du challenge GEO Inseec 2026-2027 : 9 sites face à 5 moteurs conversationnels (ChatGPT, Claude, Gemini, Perplexity, Le Chat).

- Collecte vers 5 h (heure de Paris) : `.github/workflows/collecte.yml`, script `radar/collect.py`.
- Publication à 8 h : `.github/workflows/publication.yml`, scripts `radar/score.py`, `radar/build_site.py`, `radar/rapport.py`.
- Questions des groupes et noms déclarés : `config/groupes.json`. Moteurs, cadences, poids et plafonds : `config/radar.json`.
- Archives : `data/reponses/AAAA-MM-JJ/<moteur>.json`. Site publié : `docs/` (GitHub Pages, radar.influa.com).

Clés d'accès en secrets du dépôt : OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, PERPLEXITY_API_KEY, MISTRAL_API_KEY. Un moteur sans clé est signalé sur la page et ignoré.

Relance manuelle : onglet Actions, workflow "Collecte quotidienne" puis "Publication du classement", bouton "Run workflow".
