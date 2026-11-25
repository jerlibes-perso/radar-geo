"""Collecte du jour : interroge les moteurs prévus aujourd'hui sur les 180 questions.
Usage : python -m radar.collect [--date AAAA-MM-JJ] [--moteurs gemini,mistral] [--force]"""
import os, sys, json, time, argparse, threading, datetime as dt, concurrent.futures as cf
from .common import CFG, GROUPES, DATA, maintenant, moteurs_du_jour, charger, sauver
from .engines import MOTEURS, CLES


def depense_du_mois(mois):
    u = charger(os.path.join(DATA, "depenses.json"), {})
    return u.get(mois, {})


VERROU = threading.Lock()


def noter_depense(mois, mid, eur):
  with VERROU:
    p = os.path.join(DATA, "depenses.json")
    u = charger(p, {})
    u.setdefault(mois, {}).setdefault(mid, 0.0)
    u[mois][mid] = round(u[mois][mid] + eur, 4)
    sauver(p, u)


def relever(m, jour, force=False):
    mid = m["id"]
    sortie = os.path.join(DATA, "reponses", jour.isoformat(), f"{mid}.json")
    if os.path.exists(sortie) and not force:
        print(f"{mid} : déjà relevé le {jour}")
        return
    if not (os.environ.get(CLES[mid]) or (mid == "mistral" and os.environ.get("MISTRAL_KEY"))):
        print(f"{mid} : clé {CLES[mid]} absente, moteur ignoré")
        sauver(sortie.replace(".json", ".absent.json"), {"raison": "clé absente"})
        return
    mois = jour.strftime("%Y-%m")
    unit = CFG["cout_estime_eur_par_reponse"].get(mid, 0.0)
    plafond = m.get("plafond_mensuel_eur", 0)
    deja = depense_du_mois(mois).get(mid, 0.0)
    if unit and deja + unit * 180 > plafond:
        print(f"{mid} : plafond mensuel atteint ({deja:.2f} EUR sur {plafond})")
        sauver(sortie.replace(".json", ".plafond.json"), {"raison": "plafond mensuel", "depense": deja, "plafond": plafond})
        return
    f = MOTEURS[mid]
    loc = CFG["localisation"]
    recs = []
    for g in GROUPES:
        for q in g["questions"]:
            r = {"qid": q["id"], "groupe": g["u"], "question": q["texte"], "type": q["type"], "moteur": mid}
            t0 = maintenant()
            try:
                r.update(f(q["texte"], m, loc))
            except Exception as e:
                r.update({"texte": "", "sources": [], "erreur": str(e)[:400]})
            r["heure"] = t0.isoformat(timespec="seconds")
            recs.append(r)
            time.sleep(1.2 if mid == "mistral" else 0.3)
    sauver(sortie, recs)
    ok = sum(1 for r in recs if not r.get("erreur"))
    noter_depense(mois, mid, unit * ok)
    print(f"{mid} : {ok} réponses sur {len(recs)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--moteurs")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--apres", type=int, help="ne collecte qu'à partir de cette heure locale")
    a = ap.parse_args()
    now = maintenant()
    if a.apres is not None and now.hour < a.apres:
        print(f"Heure locale {now.hour} h : collecte à partir de {a.apres} h, rien à faire")
        return
    jour = dt.date.fromisoformat(a.date) if a.date else now.date()
    fin = dt.date.fromisoformat(CFG["fin"])
    if jour > fin:
        print("Challenge terminé")
        return
    ms = moteurs_du_jour(jour)
    if a.moteurs:
        ids = a.moteurs.split(",")
        ms = [m for m in CFG["moteurs"] if m["id"] in ids]
    print("Moteurs du jour :", ", ".join(m["nom"] for m in ms))
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(lambda m: relever(m, jour, a.force), ms))


if __name__ == "__main__":
    main()
