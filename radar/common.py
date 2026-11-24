import json, os, re, unicodedata, datetime as dt
from zoneinfo import ZoneInfo

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(RACINE, "config", "radar.json"), encoding="utf-8"))
GROUPES = json.load(open(os.path.join(RACINE, "config", "groupes.json"), encoding="utf-8"))
TZ = ZoneInfo(CFG["fuseau"])
DATA = os.path.join(RACINE, "data")
DOCS = os.path.join(RACINE, "docs")
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
NB = " "


def maintenant():
    return dt.datetime.now(TZ)


def date_fr(d):
    if isinstance(d, str):
        d = dt.date.fromisoformat(d)
    j = "1er" if d.day == 1 else str(d.day)
    return f"{j}{NB}{MOIS[d.month - 1]}{NB}{d.year}"


def heure_fr(h):
    return f"{h.hour}{NB}h{NB}{h.minute:02d}"


def moteurs_du_jour(d):
    """Moteurs relevés à la date d, selon leur cadence."""
    out = []
    for m in CFG["moteurs"]:
        c = m["cadence"]
        if c == "quotidien":
            out.append(m)
        elif c == "hebdomadaire" and JOURS[d.weekday()] == m["jour"]:
            out.append(m)
        elif c == "bimensuel" and JOURS[d.weekday()] == m["jour"]:
            pair = d.isocalendar()[1] % 2 == 0
            if (m["semaines"] == "paires") == pair:
                out.append(m)
    return out


def prochain_releve(m, d):
    for i in range(0, 21):
        x = d + dt.timedelta(days=i)
        if m in moteurs_du_jour(x):
            return x
    return None


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t)


def hote(url):
    m = re.match(r"^[a-z]+://([^/:?#]+)", (url or "").lower())
    h = m.group(1) if m else ""
    return h[4:] if h.startswith("www.") else h


def cite_groupe(rec, g):
    """Renvoie la liste des preuves de citation du groupe g dans la réponse rec."""
    preuves = []
    dom = g["domaine"].lower()
    for s in rec.get("sources", []):
        if not s.get("citee"):
            continue
        h = hote(s.get("url", ""))
        d2 = (s.get("domaine") or s.get("titre") or "").lower().strip()
        if h == dom or h.endswith("." + dom) or d2 == dom or d2 == "www." + dom:
            preuves.append({"type": "lien", "valeur": s.get("url") or dom})
    txt = norm(rec.get("texte", ""))
    if dom in txt:
        preuves.append({"type": "domaine", "valeur": dom})
    for n in g.get("noms", []):
        if n and norm(n) in txt:
            preuves.append({"type": "nom", "valeur": n})
    return preuves


def charger(p, defaut):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return defaut


def sauver(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
