"""Teste chaque moteur sur une question du panel, sans rien enregistrer. N'affiche jamais les clés."""
import os
from .common import CFG, GROUPES
from .engines import MOTEURS, CLES

q = GROUPES[0]["questions"][10]["texte"]
for m in CFG["moteurs"]:
    if not os.environ.get(CLES[m["id"]]):
        print(f"{m['nom']} : clé absente")
        continue
    try:
        r = MOTEURS[m["id"]](q, m, CFG["localisation"])
        print(f"{m['nom']} : OK, {len(r['texte'])} caractères, {len(r['sources'])} sources, modèle {r['modele']}")
    except Exception as e:
        print(f"{m['nom']} : ERREUR {str(e)[:300]}")
