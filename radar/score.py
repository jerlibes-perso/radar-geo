"""Calcule les points, le classement jour par jour, la grille et les distinctions.
Écrit data/scores.json."""
import os, glob, json, datetime as dt
from .common import CFG, GROUPES, DATA, cite_groupe, charger, sauver, maintenant

POIDS = {m["id"]: m["poids"] for m in CFG["moteurs"]}
GIDX = {g["u"]: g for g in GROUPES}


def classer(cumul, questions):
    us = sorted(cumul, key=lambda u: (-cumul[u], -len(questions[u]), u))
    rang, prec = {}, None
    for i, u in enumerate(us):
        cle = (cumul[u], len(questions[u]))
        rang[u] = rang[us[i - 1]] if prec == cle else i + 1
        prec = cle
    return us, rang


def calculer(jusqu_au=None):
    debut = dt.date.fromisoformat(CFG["debut"])
    fin = min(dt.date.fromisoformat(CFG["fin"]), jusqu_au or maintenant().date())
    dossiers = sorted(glob.glob(os.path.join(DATA, "reponses", "*")))
    recs_par_jour = {}
    etats = {}
    for d in dossiers:
        jour = os.path.basename(d)
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            nom = os.path.basename(f)
            if nom.endswith(".absent.json") or nom.endswith(".plafond.json"):
                etats.setdefault(jour, {})[nom.split(".")[0]] = "plafond" if "plafond" in nom else "absent"
                continue
            mid = nom[:-5]
            recs = json.load(open(f, encoding="utf-8"))
            ok = sum(1 for r in recs if not r.get("erreur"))
            etats.setdefault(jour, {})[mid] = f"{ok}/{len(recs)}"
            recs_par_jour.setdefault(jour, []).extend(recs)

    us = [g["u"] for g in GROUPES]
    cumul = {u: 0 for u in us}
    questions = {u: set() for u in us}
    moteurs = {u: set() for u in us}
    jours_cites = {u: [] for u in us}
    grille = {u: {} for u in us}
    citations, historique = [], []
    distinctions = {u: [] for u in us}
    rang_prec = None
    j = debut
    while j <= fin:
        js = j.isoformat()
        pts = {u: 0 for u in us}
        for r in recs_par_jour.get(js, []):
            g = GIDX.get(r["groupe"])
            if not g or r.get("erreur"):
                continue
            pr = cite_groupe(r, g)
            cell = {"date": js, "cite": bool(pr)}
            grille[g["u"]].setdefault(r["qid"], {})[r["moteur"]] = cell
            if pr:
                p = POIDS[r["moteur"]]
                pts[g["u"]] += p
                questions[g["u"]].add(r["qid"])
                moteurs[g["u"]].add(r["moteur"])
                citations.append({"date": js, "heure": r.get("heure"), "groupe": g["u"], "qid": r["qid"], "question": r["question"],
                                  "moteur": r["moteur"], "points": p, "preuves": pr,
                                  "image": f"preuves/{js}/{r['qid']}-{r['moteur']}.png"})
        for u in us:
            cumul[u] += pts[u]
            if pts[u]:
                jours_cites[u].append(j)
        ordre, rang = classer(cumul, questions)
        for u in us:
            d = distinctions[u]
            noms = {x["nom"] for x in d}
            if cumul[u] > 0 and "Première citation" not in noms:
                d.append({"nom": "Première citation", "date": js})
            if len(moteurs[u]) >= 5 and "Cité par les 5 moteurs" not in noms:
                d.append({"nom": "Cité par les 5 moteurs", "date": js})
            if len(questions[u]) >= 10 and "10 questions citées" not in noms:
                d.append({"nom": "10 questions citées", "date": js})
            jc = jours_cites[u]
            if len(jc) >= 7 and all((jc[-1] - jc[-1 - k]).days == k for k in range(7)) and "7 jours de suite" not in noms:
                d.append({"nom": "7 jours de suite", "date": js})
        historique.append({"date": js, "points": pts, "cumul": dict(cumul), "rang": rang,
                           "evolution": {u: (rang_prec[u] - rang[u]) if rang_prec else 0 for u in us}})
        rang_prec = rang
        j += dt.timedelta(days=1)

    out = {"calcule_le": maintenant().isoformat(timespec="minutes"), "debut": CFG["debut"], "fin": CFG["fin"],
           "historique": historique, "citations": citations, "etats": etats,
           "questions": {u: sorted(questions[u]) for u in us}, "moteurs": {u: sorted(moteurs[u]) for u in us},
           "distinctions": distinctions, "grille": grille}
    sauver(os.path.join(DATA, "scores.json"), out)
    return out


if __name__ == "__main__":
    s = calculer()
    h = s["historique"][-1]
    print(h["date"], h["cumul"])
