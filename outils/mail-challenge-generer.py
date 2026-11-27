# -*- coding: utf-8 -*-
"""Mail gamifie du Challenge GEO Inseec MSC M1 Marketing Digital & Data.
Usage : python3 -I generer.py <dossier_donnees> <dossier_sortie> [AAAA-MM-JJ]
Le dossier de donnees contient scores.json et groupes.json du depot radar-geo.
Le script controle aussi l'etat reel de chaque site (indexation, pages publiees,
Search Console, Bing, page magasin, FAQ) pour choisir la mission de chaque groupe.
Sortie : mail.html, corps.html (contenu a coller dans Gmail), objet.txt, texte.txt,
destinataires.json, diagnostic.json.
Design : jeu d'action urbain 2026 (nuit, neons, coucher de soleil, typo condensee).
Liens : uniquement des liens directs ; le script s'arrete si un lien de redirection apparait.
"""
import json, sys, os, datetime, html, re, urllib.request, ssl

SRC, OUT = sys.argv[1], sys.argv[2]
TODAY = datetime.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else datetime.date.today()
FIN = datetime.date(2027, 6, 1)
SEANCE2 = datetime.date(2026, 12, 15)
RADAR = "https://radar.influa.com/"
NOM = "Challenge GEO Inseec MSC M1 Marketing Digital & Data"
# Visuels originaux du kit, servis par radar.influa.com une fois publies dans le depot radar-geo (dossier kit/).
# https://radar.influa.com/kit/hero.png repond en 200 depuis le 27 novembre 2026.
KIT = "https://radar.influa.com/kit/"

# palette nuit et neons
NUIT, PANNEAU, PANNEAU2 = "#0B0618", "#160C2E", "#21123F"
MAGENTA, ORANGE, JAUNE, CYAN = "#FF2E88", "#FF7A00", "#FFD23F", "#17E3FF"
BLANC, BRUME, OMBRE = "#FFFFFF", "#B9AED6", "#3A2A5E"
FONT = "Helvetica,Arial,sans-serif"
CHOC = "Impact,'HelveticaNeue-CondensedBlack','Helvetica Neue Condensed Black','Arial Narrow Bold','Arial Black',sans-serif"

NBSP = " "

def fr(s):
    for p in (":", ";", "?", "!"):
        s = s.replace(" " + p, NBSP + p)
    return s.replace("’", "'")

def e(s):
    return html.escape(fr(str(s)), quote=True)

def lien(d, color=BLANC):
    return f'<a href="https://{d}/" style="color:{color};text-decoration:none;">{e(d)}</a>'

def fond(color, grad=None):
    """Couleur unie en attribut et en style, degrade en plus quand le client le lit."""
    g = f"background-image:linear-gradient({grad});" if grad else ""
    return f'bgcolor="{color}" style="background-color:{color};{g}'

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

def date_fr(d, jour=True):
    j = "1er" if d.day == 1 else str(d.day)
    t = f"{j} {MOIS[d.month - 1]} {d.year}"
    return f"{JOURS[d.weekday()]} {t}" if jour else t

def pl(n, mot):
    return f"{n} {mot}{'s' if n > 1 else ''}"

# ---------------------------------------------------------------- equipes
EQUIPES = {
    "sport": ["Léonore Bingol", "Valentin Gauche", "Talia Ghazal", "Emma Grasset"],
    "enfants": ["Iban Bagalciague", "Kenzo Menu"],
    "style": ["Camilo Franco Barreto", "Célia Iturria", "Joshua Siau"],
    "soins": ["Yasmine Antar", "Chaïma Abbad", "Ava Bordin", "Rémy Hervois"],
    "lentilles": ["Nolann Boucaud", "Guilhem Confais-Pollet", "Zélia Trad"],
    "soleil": ["Fatima Ezzahraa Khallouk", "Kimou Don", "Pétula Kouakou"],
}
SANS_GROUPE = ["Yacine Koyate"]

ETUDIANTS = [
    "yasmine.antar", "camilo.francobarreto", "celia.iturria", "fatimaezzahraa.khallouk",
    "joshua.siau", "chaima.abbad", "iban.bagalciague", "leonore.bingol", "ava.bordin",
    "nolann.boucaud", "guilhem.confaispollet", "kimou.don", "valentin.gauche",
    "talia.ghazal", "emma.grasset", "remy.hervois", "petula.kouakou", "yacine.koyate",
    "kenzo.menu", "zelia.trad"]
DEST = {"to": ["j.libes@influa.com", "atol.bordeauxlac@gmail.com"],
        "cc": ["mdouens@inseec.com", "adeline@influa.com"],
        "bcc": [x + "@inseec-france.com" for x in ETUDIANTS]}

CONSEILS_THEME = {
    "sport": ["Comparez lunettes, lentilles et masques dans un tableau à 3 colonnes par sport.",
              "Expliquez les catégories de filtres de 0 à 4 pour le ski, avec la source."],
    "enfants": ["Donnez le calendrier des examens de vue par âge, avec le lien ameli.fr.",
                "Publiez la liste des signes qu'un enfant voit mal, en liste numérotée."],
    "style": ["Publiez un tableau forme du visage, forme de monture, à 3 colonnes.",
              "Faites une page par matière : acétate, titane, métal."],
    "soins": ["Appuyez chaque page santé sur une source HAS, Inserm ou ameli.fr.",
              "Ajoutez sur chaque page un encadré sur les signes d'alerte qui imposent de consulter."],
    "lentilles": ["Comparez journalières, mensuelles et rigides dans un tableau : durée, entretien, coût.",
                  "Publiez les erreurs d'entretien des lentilles en liste numérotée."],
    "soleil": ["Présentez les catégories de filtres de 0 à 4 dans un tableau, avec l'usage de chacune.",
               "Expliquez le marquage CE et la mention UV400, avec la source officielle."],
}

NIVEAUX = [(0, 1, "Éclaireur"), (1, 2, "Repéré"), (10, 3, "Cité"), (30, 4, "Référence"), (75, 5, "Autorité")]

def niveau(p):
    n = NIVEAUX[0]
    for x in NIVEAUX:
        if p >= x[0]:
            n = x
    return n

# ---------------------------------------------------------------- diagnostic des sites
CTX = ssl.create_default_context()

def get(url, limit=400000):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ChallengeGEOInseec/1.0"})
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            return r.status, r.read(limit).decode("utf-8", "replace")
    except Exception:
        return None, ""

def diagnostic(dom):
    d = {"joignable": False}
    st, home = get(f"https://{dom}/")
    if st != 200:
        return d
    d["joignable"] = True
    d["noindex"] = bool(re.search(r'<meta[^>]+name=.robots.[^>]+noindex', home, re.I))
    d["gsc"] = "google-site-verification" in home
    d["bing"] = "msvalidate.01" in home
    st, sm = get(f"https://{dom}/sitemap_index.xml", 20000)
    d["sitemap"] = st == 200 and "<sitemap" in sm
    allp = []
    for typ in ("pages", "posts"):
        st, js = get(f"https://{dom}/wp-json/wp/v2/{typ}?per_page=100&_fields=slug,content")
        try:
            allp += [x for x in json.loads(js) if isinstance(x, dict)] if st == 200 else []
        except Exception:
            pass
    d["nb"] = len(allp)
    d["magasin"] = any("bordeaux-lac" in x.get("slug", "") or "magasin" in x.get("slug", "") for x in allp)
    d["faq"] = "FAQPage" in home or any("rank-math-faq" in (x.get("content") or {}).get("rendered", "") for x in allp)
    return d

def mission(u, d, k):
    """Premiere etape non faite, dans l'ordre du guide technique."""
    if not d.get("joignable"):
        return ("Remettez le site en ligne", "Vérifiez que le site s'affiche, puis prévenez Jérôme Libes s'il reste hors ligne.")
    if d["noindex"]:
        return ("Ouvrez l'indexation",
                "Réglages, Lecture : décochez Demander aux moteurs de recherche de ne pas indexer ce site. Tant que la case reste cochée, aucun point n'est possible.")
    if d["nb"] == 0:
        return ("Publiez votre première page réponse",
                "Recopiez une question du panel en H1, puis un chapô de 40 à 50 mots qui répond seul, avec un chiffre et sa source.")
    if not d["gsc"]:
        return ("Reliez la Search Console",
                "Collez la balise HTML de Google dans Rank Math, puis soumettez sitemap_index.xml.")
    if not d["bing"]:
        return ("Inscrivez le site sur Bing Webmaster Tools",
                "Bing est lu par ChatGPT et Copilot. Soumettez-y aussi sitemap_index.xml.")
    if not d["magasin"]:
        return ("Créez la page Le magasin à Bordeaux Lac",
                "Adresse, téléphone et horaires d'Atol Mon Opticien Bordeaux Lac repris de sa fiche Google, avec le schéma Optician.")
    if not d["faq"]:
        return ("Ajoutez une FAQ balisée",
                "Un bloc FAQ by Rank Math de 3 à 6 questions sur vos pages clés, testé sur validator.schema.org.")
    if d["nb"] < 10:
        return (f"Passez à 10 pages publiées ({d['nb']} aujourd'hui)", CONSEILS_THEME[u][k % 2])
    return (f"Cap sur 50 pages ({d['nb']} aujourd'hui)", CONSEILS_THEME[u][k % 2])

# ---------------------------------------------------------------- donnees du classement
S = json.load(open(os.path.join(SRC, "scores.json"), encoding="utf-8"))
G = json.load(open(os.path.join(SRC, "groupes.json"), encoding="utf-8"))
GRP = {g["u"]: g for g in G if g["u"] in EQUIPES}
QTYPE = {q["id"]: q["type"] for g in G for q in g["questions"]}
H = sorted([h for h in S["historique"] if h["date"] <= TODAY.isoformat()], key=lambda h: h["date"])
CIT = [c for c in S.get("citations", []) if c["date"] <= TODAY.isoformat() and c["groupe"] in EQUIPES]
NOMS_MOT = {"gemini": "Gemini", "perplexity": "Perplexity", "openai": "ChatGPT", "anthropic": "Claude"}

last = H[-1] if H else {"cumul": {}}
cumul = {u: last["cumul"].get(u, 0) for u in EQUIPES}
recul_j = 4 if TODAY.weekday() == 0 else 3
debut_d = TODAY - datetime.timedelta(days=recul_j)
debut = debut_d.isoformat()
ref = None
for h in H:
    if h["date"] <= debut:
        ref = h
ref_cumul = {u: (ref["cumul"].get(u, 0) if ref else 0) for u in EQUIPES}
gain = {u: cumul[u] - ref_cumul[u] for u in EQUIPES}
cit_periode = [c for c in CIT if c["date"] > debut]

def nbq(u):
    return len({c["qid"] for c in CIT if c["groupe"] == u})

ordre = sorted(EQUIPES, key=lambda u: (-cumul[u], -nbq(u), GRP[u]["domaine"]))
rang, prev = {}, None
for i, u in enumerate(ordre):
    k = (cumul[u], nbq(u))
    rang[u] = rang[ordre[i - 1]] if prev == k else i + 1
    prev = k

def rang_ref(u):
    return 1 + sum(1 for x in EQUIPES if ref_cumul[x] > ref_cumul[u])

mouv = {u: (rang_ref(u) - rang[u]) if ref else 0 for u in EQUIPES}

def badges(u):
    cs = [c for c in CIT if c["groupe"] == u]
    mot = {c["moteur"] for c in cs}
    dates = sorted({c["date"] for c in cs})
    serie = best = 0
    for i, dd in enumerate(dates):
        serie = serie + 1 if i and (datetime.date.fromisoformat(dd) - datetime.date.fromisoformat(dates[i - 1])).days == 1 else 1
        best = max(best, serie)
    return sum([len(cs) > 0, any(QTYPE.get(c["qid"]) == "locale" for c in cs), len(mot) >= 2, best >= 3, len(mot) >= 4])

ed, dd = 0, datetime.date(2026, 11, 30)
while dd <= TODAY:
    ed += dd.weekday() in (0, 3)
    dd += datetime.timedelta(days=1)
edition = f"Édition {ed}" if ed else "Édition de lancement"
semaine = TODAY.isocalendar()[1]
jours_fin = (FIN - TODAY).days
jours_s2 = (SEANCE2 - TODAY).days
prochaine = TODAY + datetime.timedelta(days=1)
while prochaine.weekday() not in (0, 3):
    prochaine += datetime.timedelta(days=1)
total_cit = len(CIT)
top = [u for u in ordre if rang[u] == 1]
n_sites = len(EQUIPES)

DIAG = {u: diagnostic(GRP[u]["domaine"]) for u in EQUIPES}
nb_fermes = sum(1 for u in EQUIPES if DIAG[u].get("noindex"))

# ---------------------------------------------------------------- defi et objet
if total_cit == 0:
    objet = "Défi de la semaine : décrocher la première citation du challenge"
    defi_titre = "Décrochez la première citation du challenge"
    defi_txt = "Objectif : être le premier site cité par un moteur. Récompense : la tête du classement, seul."
elif len(top) == 1:
    u = top[0]
    ecart = cumul[u] - max(cumul[x] for x in EQUIPES if x != u)
    objet = f"Défi de la semaine : détrôner {GRP[u]['domaine']}, en tête avec {cumul[u]} points"
    defi_titre = f"Détrônez {GRP[u]['domaine']}"
    defi_txt = f"Cible : {GRP[u]['domaine']}, {pl(ecart, 'point')} d'avance. Objectif : une citation ChatGPT ou Claude. Récompense : 14 points, de quoi renverser le classement en un lundi."
else:
    objet = "Défi de la semaine : sortir de l'égalité en tête du classement"
    defi_titre = "Sortez de l'égalité en tête"
    defi_txt = f"{len(top)} sites partagent la première place avec {pl(cumul[top[0]], 'point')}. Objectif : être cité sur une question de plus que les autres. Récompense : la première place, seul."
if nb_fermes:
    qui = "tous les sites restent fermés" if nb_fermes == n_sites else (f"{nb_fermes} sites restent fermés" if nb_fermes > 1 else "1 site reste fermé")
    defi_txt += f" Renseignement du matin : {qui} aux moteurs. Première étape : ouvrir l'indexation."

# titres-message des sections
if cumul[ordre[0]] == 0:
    t_class = f"{n_sites} sites à égalité, 0 point"
elif len(top) == 1:
    t_class = f"{GRP[top[0]]['domaine']} en tête avec {pl(cumul[top[0]], 'point')}"
else:
    t_class = f"{len(top)} sites en tête avec {pl(cumul[top[0]], 'point')}"
prog = sorted([u for u in EQUIPES if gain[u] > 0], key=lambda u: -gain[u])[:3]
depuis = "le lancement" if ed == 0 else JOURS[debut_d.weekday()]
if prog:
    t_prog = f"{GRP[prog[0]]['domaine']} gagne {pl(gain[prog[0]], 'point')} depuis {depuis}"
else:
    t_prog = f"Aucun point marqué depuis {depuis}"

# ---------------------------------------------------------------- briques html
def sp(h=14, bg=NUIT):
    return f'<tr><td {fond(bg)}height:{h}px;line-height:{h}px;font-size:0;">&nbsp;</td></tr>'

def hud(t, color=CYAN):
    return (f'<div style="font-family:{CHOC};font-weight:900;font-size:13px;letter-spacing:4px;text-transform:uppercase;'
            f'color:{color};margin:0 0 6px;">{e(t)}</div>')

def titre(t, color=BLANC, size=34):
    return (f'<div style="font-family:{CHOC};font-weight:900;font-size:{size}px;line-height:1.02;color:{color};'
            f'text-transform:uppercase;letter-spacing:0.5px;margin:0 0 14px;">{e(t)}</div>')

def p(t, color=BRUME, size=15, m="0 0 10px"):
    return f'<div style="font-family:{FONT};font-size:{size}px;line-height:1.5;color:{color};margin:{m};">{e(t)}</div>'

def jauge(nv, on=JAUNE, off=OMBRE, w=16, h=10):
    c = "".join(f'<td width="{w}" {fond(on if i < nv else off)}height:{h}px;line-height:{h}px;font-size:0;">&nbsp;</td>'
                f'<td width="4" style="font-size:0;">&nbsp;</td>' for i in range(5))
    return f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>{c}</tr></table>'

def bandeau(txt, bg, fg=NUIT, grad=None):
    return (f'<tr><td {fond(bg, grad)}padding:12px 28px;font-family:{CHOC};font-weight:900;font-size:18px;letter-spacing:3px;'
            f'text-transform:uppercase;color:{fg};">{e(txt)}</td></tr>')

def bloc(inner, bg=PANNEAU, pad="26px 28px"):
    return f'<tr><td {fond(bg)}padding:{pad};">{inner}</td></tr>'

# silhouette de ville en blocs
SKY = [38, 22, 54, 70, 44, 26, 82, 48, 34, 66, 92, 40, 24, 58, 74, 46, 30, 62, 20, 56]
def skyline():
    cells = "".join(f'<td valign="bottom" style="font-size:0;line-height:0;">'
                    f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                    f'<td height="{h}" {fond(NUIT)}height:{h}px;font-size:0;line-height:0;">&nbsp;</td></tr></table></td>' for h in SKY)
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="table-layout:fixed;"><tr>{cells}</tr></table>'

def soleil():
    rows = ""
    for w, h, g in ((46, 10, 8), (52, 8, 6), (56, 6, 5), (58, 4, 4)):
        rows += (f'<tr><td align="center" style="font-size:0;line-height:0;padding-bottom:{g}px;">'
                 f'<table role="presentation" width="{w}%" cellpadding="0" cellspacing="0" border="0"><tr>'
                 f'<td height="{h}" {fond(JAUNE, "90deg," + ORANGE + "," + JAUNE + "," + ORANGE)}height:{h}px;font-size:0;line-height:0;">&nbsp;</td>'
                 f'</tr></table></td></tr>')
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>'

parts = []

# ecran d'ouverture : coucher de soleil, compte a rebours geant
if KIT:
    parts.append(f'<tr><td {fond(NUIT)}padding:0;font-size:0;line-height:0;"><a href="{RADAR}"><img src="{KIT}hero.png" width="600" alt="{e(NOM)}" style="display:block;width:100%;max-width:600px;height:auto;border:0;"></a></td></tr>')
parts.append(
    f'<tr><td {fond("#3A0F5C", "180deg,#140726 0%,#3A0F5C 38%,#B0197A 72%,#FF5A3C 100%")}padding:28px 26px 0;">'
    f'<div style="font-family:{CHOC};font-weight:900;font-size:14px;letter-spacing:3px;line-height:1.35;text-transform:uppercase;color:{CYAN};">{e(NOM)}</div>'
    f'<div style="font-family:{FONT};font-size:11px;letter-spacing:3px;text-transform:uppercase;color:{BLANC};font-weight:bold;margin:8px 0 10px;">{e(edition)}<span style="display:inline-block;width:14px;"></span>{e(date_fr(TODAY))}</div>'
    f'<div class="jbig" style="font-family:{CHOC};font-weight:900;font-size:150px;line-height:140px;color:{JAUNE};letter-spacing:2px;white-space:nowrap;text-shadow:5px 5px 0 {MAGENTA};">J-{jours_fin}</div>'
    f'<div style="font-family:{CHOC};font-weight:900;font-size:20px;line-height:1.15;color:{BLANC};letter-spacing:1px;margin:10px 0 20px;">{e("avant le classement final, le 1er juin 2027 à 23 h 59")}</div>'
    f'{soleil()}{skyline()}</td></tr>')

# defi de la semaine
parts.append(bandeau("Défi de la semaine", MAGENTA, BLANC, f"90deg,{MAGENTA},{ORANGE}"))
parts.append(bloc(f'{titre(defi_titre, JAUNE, 38)}{p(defi_txt, BLANC, 16, "0")}', NUIT, "22px 28px 26px"))
if jours_s2 >= 0:
    parts.append(
        f'<tr><td {fond(PANNEAU2)}padding:16px 28px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td width="92" valign="middle" style="font-family:{CHOC};font-weight:900;font-size:40px;line-height:40px;color:{CYAN};">J-{jours_s2}</td>'
        f'<td valign="middle" style="font-family:{FONT};font-size:13px;line-height:1.45;color:{BLANC};">'
        f'{e("Séance 2, mardi 15 décembre à 14 h : chaque groupe présente sa stratégie GEO devant Atol Bordeaux Lac, site en ligne et indexé.")}</td>'
        f'</tr></table></td></tr>')
parts.append(sp())

# etape 1 : classement
maxp = max([cumul[u] for u in EQUIPES] + [1])
couleurs = {1: JAUNE, 2: CYAN, 3: MAGENTA}
podium = ""
if cumul[ordre[0]] > 0:
    cols = ""
    for pos in (1, 0, 2):
        u = ordre[pos]
        hgt, c = [120, 86, 62][pos], [JAUNE, CYAN, MAGENTA][pos]
        cols += (f'<td width="33%" valign="bottom" align="center" style="font-family:{FONT};padding:0 3px;">'
                 f'<div class="pod" style="font-size:12px;font-weight:bold;color:{BLANC};margin-bottom:2px;word-break:break-all;">{e(GRP[u]["domaine"])}</div>'
                 f'<div style="font-size:12px;color:{BRUME};margin-bottom:6px;">{pl(cumul[u], "pt")}</div>'
                 f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td align="center" height="{hgt}" {fond(c)}height:{hgt}px;font-family:{CHOC};font-weight:900;font-size:48px;color:{NUIT};">{rang[u]}</td></tr></table></td>')
    podium = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:4px 0 18px;"><tr>{cols}</tr></table>'
rows = ""
for u in ordre:
    r, c = rang[u], couleurs.get(rang[u], BRUME)
    w = max(3, int(100 * cumul[u] / maxp)) if cumul[u] else 3
    mv = mouv[u]
    mvt = (f'<span style="color:{CYAN};font-weight:bold;">+{mv}</span>' if mv > 0 else
           f'<span style="color:{MAGENTA};font-weight:bold;">{mv}</span>' if mv < 0 else
           f'<span style="color:{BRUME};">=</span>')
    nv = niveau(cumul[u])
    rows += (
        f'<tr><td {fond(PANNEAU2)}padding:12px 14px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td width="46" style="font-family:{CHOC};font-weight:900;font-size:40px;line-height:40px;color:{c};vertical-align:top;">{r}</td>'
        f'<td style="font-family:{FONT};vertical-align:top;">'
        f'<div style="font-size:16px;font-weight:bold;color:{BLANC};">{lien(GRP[u]["domaine"])}</div>'
        f'<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{BRUME};margin:3px 0 7px;">{e("Niveau " + str(nv[1]) + ", " + nv[2])}</div>'
        f'{jauge(nv[1])}'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;"><tr>'
        f'<td width="{w}%" {fond(c, "90deg," + MAGENTA + "," + c)}height:6px;line-height:6px;font-size:0;">&nbsp;</td>'
        f'<td {fond(OMBRE)}height:6px;line-height:6px;font-size:0;">&nbsp;</td></tr></table></td>'
        f'<td width="70" align="right" style="font-family:{FONT};vertical-align:top;">'
        f'<div style="font-family:{CHOC};font-weight:900;font-size:34px;line-height:36px;color:{BLANC};">{cumul[u]}</div>'
        f'<div style="font-size:12px;">{mvt}</div></td>'
        f'</tr></table></td></tr><tr><td style="height:6px;line-height:6px;font-size:0;">&nbsp;</td></tr>')
regle = "Gemini : 1 point par citation, chaque jour. Perplexity : 7 points, le lundi. ChatGPT et Claude : 14 points, un lundi sur deux."
parts.append(bloc(f'{hud("Étape 1, classement")}{titre(t_class)}{podium}'
                  f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>'
                  f'{p(regle, BRUME, 12, "12px 0 0")}'))
parts.append(sp())

# etape 2 : progressions
recul = [u for u in EQUIPES if mouv[u] < 0]
inner = hud("Étape 2, missions accomplies", JAUNE) + titre(t_prog)
if prog:
    for i, u in enumerate(prog):
        c = [JAUNE, CYAN, MAGENTA][i]
        inner += (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:8px;"><tr>'
                  f'<td {fond(NUIT)}padding:14px 16px;font-family:{FONT};">'
                  f'<div style="font-family:{CHOC};font-weight:900;font-size:14px;letter-spacing:3px;color:{c};text-transform:uppercase;">{e("Mission accomplie")}</div>'
                  f'<div style="font-size:16px;font-weight:bold;color:{BLANC};margin-top:4px;">{e(GRP[u]["domaine"])}</div>'
                  f'<div style="font-size:12px;color:{BRUME};">{e(", ".join(EQUIPES[u]))}</div></td>'
                  f'<td width="96" align="right" {fond(NUIT)}padding:14px 16px;font-family:{CHOC};font-weight:900;font-size:44px;color:{c};">+{gain[u]}</td>'
                  f'</tr></table>')
    for c in sorted(cit_periode, key=lambda c: -c["points"])[:3]:
        inner += p(f"{GRP[c['groupe']]['domaine']}, cité par {NOMS_MOT.get(c['moteur'], c['moteur'])} (+{c['points']}) : {c['question']}", BLANC, 13, "6px 0 0")
else:
    inner += p("Le premier point marqué inscrit son groupe ici, en tête du tableau des missions.", m="0")
if recul:
    inner += p("En recul : " + ", ".join(GRP[u]["domaine"] for u in recul) + ". Une mission bouclée cette semaine suffit à revenir.", MAGENTA, 14, "12px 0 0")
parts.append(bloc(inner))
parts.append(sp())

# etape 3 : une mission par site
MIS = {u: mission(u, DIAG[u], ed + i) for i, u in enumerate(ordre)}
compte = {}
for u in ordre:
    compte[MIS[u]] = compte.get(MIS[u], 0) + 1
commune = max(compte, key=compte.get) if compte and max(compte.values()) >= 2 else None
if commune:
    t_mis = commune[0] + (" pour marquer le premier point" if total_cit == 0 else "")
else:
    t_mis = f"{pl(len(ordre), 'mission')}, une par site"
bloc_commun = ""
if commune:
    n = compte[commune]
    bloc_commun = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:10px;"><tr>'
                   f'<td {fond(JAUNE, "135deg," + JAUNE + "," + ORANGE)}padding:18px 18px;font-family:{FONT};">'
                   f'<div style="font-family:{CHOC};font-weight:900;font-size:14px;letter-spacing:3px;color:{NUIT};text-transform:uppercase;">{e("Objectif commun à " + ("tous les sites" if n == n_sites else pl(n, "site")))}</div>'
                   f'<div style="font-size:14px;line-height:1.45;color:{NUIT};margin-top:6px;">{e(commune[1])}</div></td></tr></table>')
cards = ""
for i, u in enumerate(ordre):
    g, dg = GRP[u], DIAG[u]
    cites = {c["qid"] for c in CIT if c["groupe"] == u}
    libres = [x for x in g["questions"] if x["id"] not in cites and x["type"] == "locale"] or \
             [x for x in g["questions"] if x["id"] not in cites] or g["questions"]
    q = libres[(semaine * 2 + (TODAY.weekday() != 0) + i) % len(libres)]
    nv = niveau(cumul[u])
    pages = dg.get("nb", 0)
    wp = max(2, min(100, 2 * pages))
    propre = "" if MIS[u] == commune else (
        f'<div style="font-family:{CHOC};font-weight:900;font-size:13px;letter-spacing:3px;color:{JAUNE};text-transform:uppercase;margin:12px 0 3px;">{e("Objectif")}</div>'
        f'<div style="font-family:{FONT};font-size:14px;font-weight:bold;color:{BLANC};">{e(MIS[u][0])}</div>'
        f'<div style="font-family:{FONT};font-size:13px;line-height:1.45;color:{BRUME};margin-top:2px;">{e(MIS[u][1])}</div>')
    cards += (
        f'<tr><td {fond(NUIT)}padding:16px 16px 14px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td style="font-family:{FONT};"><div class="dom" style="font-family:{CHOC};font-weight:900;font-size:22px;line-height:1.1;color:{BLANC};letter-spacing:0.5px;word-break:break-all;">{lien(g["domaine"])}</div>'
        f'<div style="font-size:11px;color:{BRUME};margin-top:3px;">{e(", ".join(EQUIPES[u]))}</div></td>'
        f'<td align="right" valign="top" style="font-family:{CHOC};font-weight:900;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:{CYAN};white-space:nowrap;">{e(nv[2])}<div style="margin-top:5px;">{jauge(nv[1], CYAN, OMBRE, 10, 8)}</div></td>'
        f'</tr></table>{propre}'
        f'<div style="font-family:{CHOC};font-weight:900;font-size:13px;letter-spacing:3px;color:{MAGENTA};text-transform:uppercase;margin:12px 0 3px;">{e("Cible")}</div>'
        f'<div style="font-family:{FONT};font-size:15px;line-height:1.4;color:{BLANC};">{e(q["texte"])}</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:12px;"><tr>'
        f'<td width="{wp}%" {fond(CYAN, "90deg," + CYAN + "," + MAGENTA)}height:5px;line-height:5px;font-size:0;">&nbsp;</td>'
        f'<td {fond(OMBRE)}height:5px;line-height:5px;font-size:0;">&nbsp;</td></tr></table>'
        f'<div style="font-family:{FONT};font-size:11px;color:{BRUME};margin-top:5px;">{e(f"{pages} pages publiées sur 50, {badges(u)} badges sur 5")}</div>'
        f'</td></tr><tr><td style="height:8px;line-height:8px;font-size:0;">&nbsp;</td></tr>')
chapo_mis = p("Briefing établi sur l'état réel de chaque site, contrôlé ce matin. Récompense : 1 point par citation Gemini, chaque jour, 7 points Perplexity le lundi, 14 points ChatGPT ou Claude.", m="0 0 14px")
parts.append(bloc(f'{hud("Étape 3, vos missions", MAGENTA)}{titre(t_mis)}'
                  f'{chapo_mis}{bloc_commun}'
                  f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{cards}</table>'))
parts.append(sp())

# recrue
if SANS_GROUPE:
    petits = sorted(EQUIPES, key=lambda u: len(EQUIPES[u]))
    cible = [u for u in petits if len(EQUIPES[u]) == len(EQUIPES[petits[0]])]
    lst = [n for u in cible for n in EQUIPES[u]]
    membres = ", ".join(lst[:-1]) + " et " + lst[-1] if len(lst) > 1 else lst[0]
    de = "d'" if membres[0].lower() in "aeiouyéèh" else "de "
    t_rec = f"{', '.join(SANS_GROUPE)}, rejoignez {' ou '.join(GRP[u]['domaine'] for u in cible)}"
    txt = (f"L'équipe {de}{membres} est le seul groupe de deux. "
           "Votre arrivée lui donne un troisième rédacteur et vous ouvre le classement dès cette semaine.")
    parts.append(bandeau("Recrue attendue", CYAN, NUIT, f"90deg,{CYAN},#7B5CFF"))
    parts.append(bloc(f'{titre(t_rec, BLANC, 24).replace('margin:0 0 14px;', 'margin:0 0 14px;word-break:break-word;').replace('<div style', '<div class="rec" style', 1)}{p(txt, BRUME, 15, "0")}', PANNEAU, "20px 28px 24px"))
    parts.append(sp())

# appel a l'action
parts.append(
    f'<tr><td align="center" {fond(NUIT)}padding:12px 0 16px;">'
    f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td {fond(JAUNE, "90deg," + JAUNE + "," + ORANGE)}padding:18px 22px;">'
    f'<a class="cta" href="{RADAR}" style="color:{NUIT};font-family:{CHOC};font-weight:900;font-size:20px;letter-spacing:1px;text-transform:uppercase;text-decoration:none;">{e("Voir le classement complet")}</a>'
    f'</td></tr></table></td></tr>'
    f'<tr><td align="center" {fond(NUIT)}font-family:{FONT};font-size:12px;color:{BRUME};padding:0 20px 30px;line-height:1.6;">'
    f'{e("Badges, citations et questions de chaque site sur")} <a href="{RADAR}" style="color:{CYAN};text-decoration:none;">radar.influa.com</a><br>'
    f'{e("Prochaine édition : " + date_fr(prochaine))}</td></tr>')

pre = f"{defi_titre}. J-{jours_fin} avant le classement final."
corps = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td align="center" {fond(NUIT)}padding:0;">'
         '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">'
         + "".join(parts) + '</table></td></tr></table>')
doc = (
    '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1"><title>' + e(objet) + '</title>'
    '<style>@media only screen and (max-width:480px){.jbig{font-size:104px !important;line-height:100px !important;}.pod{font-size:11px !important;}.cta{font-size:16px !important;}.dom{font-size:17px !important;}.rec{font-size:19px !important;}}</style></head>'
    f'<body style="margin:0;padding:0;background:{NUIT};">'
    f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{e(pre)}</div>'
    + corps + '</body></html>')

tx = [f"{NOM}, {edition.lower()}, {date_fr(TODAY)}",
      f"J-{jours_fin} avant le classement final. J-{jours_s2} avant la séance 2 du 15 décembre.", "",
      "Défi de la semaine : " + defi_titre, defi_txt, "", t_class + " :"]
tx += [f"{rang[u]}. {GRP[u]['domaine']} : {pl(cumul[u], 'point')}" for u in ordre]
tx += ["", t_mis + " :"] + [f"{GRP[u]['domaine']} : {MIS[u][0]}" for u in ordre]
tx += ["", "Classement complet : " + RADAR]

# garde-fou : liens directs uniquement
for blob in (doc, "\n".join(tx)):
    hrefs = re.findall(r'href="([^"]+)"', blob)
    assert all((h.startswith("https://")) and "google.com/url" not in h and "safelinks" not in h for h in hrefs), hrefs
    assert "google.com/url" not in blob

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "mail.html"), "w", encoding="utf-8").write(doc)
open(os.path.join(OUT, "corps.html"), "w", encoding="utf-8").write(corps)
open(os.path.join(OUT, "objet.txt"), "w", encoding="utf-8").write(fr(objet))
open(os.path.join(OUT, "texte.txt"), "w", encoding="utf-8").write(fr("\n".join(tx)))
json.dump(DEST, open(os.path.join(OUT, "destinataires.json"), "w"))
json.dump(DIAG, open(os.path.join(OUT, "diagnostic.json"), "w"), ensure_ascii=False)
print("OK", objet, len(doc))
