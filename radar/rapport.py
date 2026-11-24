"""Message du jour pour Jérôme : podium, mouvements, citations, relevés, dépenses."""
import os
from .common import CFG, GROUPES, DATA, date_fr, charger

MNOM = {m["id"]: m["nom"] for m in CFG["moteurs"]}
GIDX = {g["u"]: g for g in GROUPES}


def main():
    s = charger(os.path.join(DATA, "scores.json"), None)
    if not s or not s["historique"]:
        print("Aucun classement calculé.")
        return
    h = s["historique"][-1]
    d = h["date"]
    us = sorted(h["rang"], key=lambda u: (h["rang"][u], u))
    out = [f"## Classement du {date_fr(d)}", "", "| Rang | Site | Points | Aujourd'hui | Évolution |", "|---:|---|---:|---:|---:|"]
    for u in us:
        e = h["evolution"][u]
        out.append(f"| {h['rang'][u]} | {GIDX[u]['domaine']} | {h['cumul'][u]} | +{h['points'][u]} | {('+' if e > 0 else '') + str(e) if e else '='} |")
    cj = [c for c in s["citations"] if c["date"] == d]
    out += ["", f"**Citations du jour : {len(cj)}**"]
    for c in cj[:15]:
        out.append(f"- {GIDX[c['groupe']]['domaine']}, {MNOM[c['moteur']]}, +{c['points']} : {c['question']}")
    et = s["etats"].get(d, {})
    out += ["", "**Relevés du jour** : " + (", ".join(f"{MNOM[k]} {v}" for k, v in et.items()) or "aucun")]
    dep = charger(os.path.join(DATA, "depenses.json"), {}).get(d[:7], {})
    tot = sum(dep.values())
    out += [f"**Dépense estimée du mois** : {tot:.2f} €".replace(".", ","), "", "https://radar.influa.com/"]
    print("\n".join(out))


if __name__ == "__main__":
    main()
