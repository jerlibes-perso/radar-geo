"""Construit le site du Radar dans docs/ : classement, fiches des groupes, journées, règles,
et les captures de preuve de chaque citation (PNG)."""
import os, re, json, html, shutil, datetime as dt
from .common import CFG, GROUPES, NSITES, NQUESTIONS, DATA, DOCS, RACINE, NB, date_fr, heure_fr, maintenant, moteurs_du_jour, prochain_releve, hote, charger
from .score import calculer
from .vitrine import vitrine, CSS_JEU, JS, niveau, jauge

MNOM = {m["id"]: m["nom"] for m in CFG["moteurs"]}
MORDRE = [m["id"] for m in CFG["moteurs"]]
GIDX = {g["u"]: g for g in GROUPES}
FONTS = "https://www.influa.com/k-custom/assets/fonts/"


def fr(s):
    s = re.sub(r" ([:;?!])", NB + r"\1", str(s))
    s = re.sub(r"(\d) (h|points|point|questions|moteurs|jours|%)\b", lambda m: m.group(1) + NB + m.group(2), s)
    return html.escape(s, quote=False)


def logo(couleur="#0E0E10"):
    s = open(os.path.join(RACINE, "assets", "logo_influa_positif.svg"), encoding="utf-8").read()
    s = re.sub(r'fill="#[0-9A-Fa-f]{6}"', f'fill="{couleur}"', s)
    return s.replace("<svg ", '<svg role="img" aria-label="Influa" ')


def police(base_fonts, n):
    if base_fonts.startswith("file://"):
        import base64
        f = os.path.join(base_fonts[7:], f"Hellix-{n}.woff2")
        if os.path.exists(f):
            return "data:font/woff2;base64," + base64.b64encode(open(f, "rb").read()).decode()
    return f"{base_fonts}Hellix-{n}.woff2"


def css(base_fonts=None):
    return open(os.path.join(RACINE, "kit", "theme.css"), encoding="utf-8").read() + """
:root{--choc:Impact,Anton,"HelveticaNeue-CondensedBlack","Arial Narrow Bold","Arial Black",sans-serif;color-scheme:dark}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--nuit);color:var(--blanc)}
body{font-family:var(--texte);font-size:16px;line-height:1.5}
a{color:inherit}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
header.band{background:var(--couchant);overflow:hidden;position:relative}
header.band .wrap{padding-top:24px;padding-bottom:0;position:relative;z-index:2}
header.band .ville{display:block;width:100%;height:120px;margin-top:-40px;position:relative;z-index:1}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.top svg{height:30px;width:auto}
.top nav a{font-family:var(--choc);font-weight:900;letter-spacing:2px;text-transform:uppercase;text-decoration:none;margin-left:20px;color:var(--cyan)}
.top nav a:hover{color:var(--jaune)}
.kicker{font-family:var(--choc);font-weight:900;font-size:14px;letter-spacing:4px;text-transform:uppercase;color:var(--cyan);margin-top:30px}
h1{font-family:var(--choc);font-weight:900;text-transform:uppercase;font-size:clamp(40px,6vw,72px);line-height:.98;margin-top:10px;text-shadow:4px 4px 0 var(--magenta)}
.sub{font-size:20px;font-weight:700;margin-top:12px}
.stamp{margin-top:8px;font-size:14px;color:var(--brume)}
main{background:var(--nuit)}
main .wrap{padding-top:34px;padding-bottom:60px}
h2{font-family:var(--choc);font-weight:900;text-transform:uppercase;font-size:clamp(26px,3.4vw,36px);line-height:1.05;margin:46px 0 16px;letter-spacing:.5px}
h3{font-family:var(--choc);font-weight:900;text-transform:uppercase;font-size:20px;margin:22px 0 8px}
p{margin-bottom:10px}
.muted{color:var(--brume);font-size:14px}
table{width:100%;border-collapse:collapse;font-size:15px;background:var(--panneau)}
th{text-align:left;font-family:var(--choc);font-weight:900;letter-spacing:1px;text-transform:uppercase;color:var(--cyan);padding:12px 10px;border-bottom:3px solid var(--cyan);vertical-align:bottom;white-space:nowrap}
td{padding:11px 10px;border-bottom:1px solid var(--ombre);vertical-align:top}
td.n,th.n{text-align:right}
tr.hl td{background:var(--panneau2)}
td.rank{font-family:var(--choc);font-weight:900;font-size:26px;width:52px;color:var(--jaune)}
.up{font-weight:700;color:var(--cyan)}
.down{color:var(--magenta);font-weight:700}
.scroll{overflow-x:auto}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.card{display:block;text-decoration:none;background:var(--panneau2)}
.card img{width:100%;display:block}
.card .t{padding:12px 14px;font-size:14px}
.card .t b{font-weight:700;color:var(--jaune)}
.card .go{display:block;margin-top:6px;font-weight:700;color:var(--cyan);text-decoration:underline}
.cell-ok{background:var(--jaune);color:var(--nuit);font-weight:700}
.cell-no{color:var(--brume)}
.cell-wait{color:var(--ombre)}
.flag{display:inline-block;background:var(--magenta);color:var(--blanc);font-weight:700;font-size:12px;padding:2px 8px}
svg.chart text{font-family:var(--texte);font-size:12px;fill:var(--brume)}
.rules{background:var(--panneau);padding:22px 26px}
.rules ol,ol.todo{padding-left:22px}ol.todo li{margin-bottom:6px}
.rules li{margin-bottom:8px}
footer{background:#06030D;color:var(--brume)}
footer .wrap{padding-top:28px;padding-bottom:28px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:14px}
footer svg{height:24px;width:auto}
""" + CSS_JEU + """
@media (max-width:760px){
 .sub{font-size:17px}
 .grid2{grid-template-columns:1fr}
 .wrap{padding:0 16px}
 .top nav a{margin:0 14px 0 0}
 th,td{font-size:14px}
 header.band .ville{height:70px;margin-top:-20px}
}
"""


def page(titre, corps, chemin_racine="", desc="", js=False, url=""):
    desc = desc or "Classement quotidien du Challenge GEO Inseec MSC M1 Marketing Digital et Big Data : " + str(NSITES) + " sites cités ou non par ChatGPT, Claude, Gemini et Perplexity."
    canon = "https://radar.influa.com/" + url
    desc = re.sub(r" ([:;?!])", NB + r"\1", desc)
    nav = f'<nav><a href="{chemin_racine}index.html">Classement</a><a href="{chemin_racine}jours.html">Journées</a><a href="{chemin_racine}regles.html">Règles</a></nav>'
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex, nofollow, noarchive, noimageindex">
<title>{fr(titre)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Radar GEO Influa"><meta property="og:locale" content="fr_FR"><meta property="og:url" content="{canon}">
<meta property="og:title" content="{html.escape(titre)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:image" content="https://radar.influa.com/kit/hero.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Écran de chargement du classement, coucher de soleil sur Bordeaux Lac">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(titre)}"><meta name="twitter:description" content="{html.escape(desc)}"><meta name="twitter:image" content="https://radar.influa.com/kit/hero.png">
<meta name="theme-color" content="#0B0618">
<link rel="icon" href="{chemin_racine}kit/favicon.svg" type="image/svg+xml"><link rel="icon" href="{chemin_racine}kit/favicon.ico" sizes="48x48"><link rel="apple-touch-icon" href="{chemin_racine}kit/favicon-180.png"><link rel="manifest" href="{chemin_racine}kit/site.webmanifest">
<style>{css(FONTS)}</style></head><body>
{corps.replace('%%NAV%%', nav)}
<footer><div class="wrap"><div>{logo('#FFFFFF')}</div><div>{fr("Radar GEO du Challenge GEO Inseec MSC M1 Marketing Digital et Big Data, 2026-2027. Influa, marque du groupe IA GROUP.")}</div></div></footer>
{('<script>' + JS + '</script>') if js else ''}</body></html>"""


def entete(kicker, titre, sous, stamp, lead=""):
    return f"""<header class="band"><div class="wrap"><div class="top">{logo("#FFFFFF")}%%NAV%%</div>
<p class="kicker">{fr(kicker)}</p><h1>{fr(titre)}</h1><p class="sub">{fr(sous)}</p><p class="stamp">{fr(stamp)}</p>{lead}</div><svg class="ville" viewBox="0 0 1075 260" preserveAspectRatio="none" aria-hidden="true"><path fill="#0B0618" d="M0 260V170h40v-30h30v50h40V90h20V60h30v130h40v-60h50v40h30V40h15V20h15v20h15v150h40v-70h60v80h30V100h50v90h40v-50h30v-40h20v90h40V70h25V50h20v20h25v120h40v-60h50v70h30V110h40v80h40v-40h60v40h40V80h30v110h40v70z"/></svg></header>"""


def evo(v):
    if v > 0:
        return f'<span class="up">+{v}</span>'
    if v < 0:
        return f'<span class="down">{v}</span>'
    return "="


def chart(hist, us):
    if len(hist) < 2 or not any(h["cumul"][u] for h in hist for u in us):
        return '<p class="muted">La courbe démarre avec la première citation.</p>'
    W, H, L, R, T, B = 1100, 340, 40, 170, 10, 30
    mx = max(1, max(h["cumul"][u] for h in hist for u in us))
    n = len(hist) - 1
    X = lambda i: L + (W - L - R) * i / n
    Y = lambda v: T + (H - T - B) * (1 - v / mx)
    tete = sorted(us, key=lambda u: -hist[-1]["cumul"][u])[0]
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Cumul des points par site">']
    for k in range(5):
        v = mx * k / 4
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#3A2A5E"/><text x="{L-6}" y="{Y(v)+4:.1f}" text-anchor="end">{int(v)}</text>')
    out.append(f'<text x="{L}" y="{H-8}">{fr(date_fr(hist[0]["date"]))}</text><text x="{W-R}" y="{H-8}" text-anchor="end">{fr(date_fr(hist[-1]["date"]))}</text>')
    ys = []
    for u in sorted(us, key=lambda u: u == tete):
        pts = " ".join(f"{X(i):.1f},{Y(h['cumul'][u]):.1f}" for i, h in enumerate(hist))
        col, w = ("#FFD23F", 3.5) if u == tete else ("#B9AED6", 1.4)
        out.append(f'<polyline fill="none" stroke="{col}" stroke-width="{w}" points="{pts}"/>')
        ys.append((Y(hist[-1]["cumul"][u]), u))
    ys.sort()
    last = -99
    for y, u in ys:
        y = max(y, last + 14)
        last = y
        out.append(f'<text x="{W-R+8}" y="{y+4:.1f}" style="font-weight:{600 if u == tete else 400}">{html.escape(GIDX[u]["domaine"])}</text>')
    out.append("</svg>")
    return "".join(out)


def carte(c, racine=""):
    g = GIDX[c["groupe"]]
    return f"""<a class="card" href="{racine}{c['image']}"><img loading="lazy" decoding="async" src="{racine}{c['image']}" alt="{html.escape('Capture de la réponse de ' + MNOM[c['moteur']] + ' citant ' + g['domaine'])}">
<div class="t"><b>{fr(g['domaine'])}</b>, {fr(MNOM[c['moteur']])}, +{c['points']}{NB}point{'s' if c['points'] > 1 else ''}<br>{fr(c['question'])}<span class="go">{fr("Voir la capture")}</span></div></a>"""


# ---------------------------------------------------------------- captures de preuve
def preuves(s, base_fonts):
    a_faire = [c for c in s["citations"] if not os.path.exists(os.path.join(DOCS, c["image"]))]
    if not a_faire:
        return 0
    from playwright.sync_api import sync_playwright
    index = {}
    for c in a_faire:
        f = os.path.join(DATA, "reponses", c["date"], f"{c['moteur']}.json")
        if f not in index:
            index[f] = {r["qid"]: r for r in json.load(open(f, encoding="utf-8"))}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 100}, device_scale_factor=1)
        for c in a_faire:
            r = index[os.path.join(DATA, "reponses", c["date"], f"{c['moteur']}.json")][c["qid"]]
            g = GIDX[c["groupe"]]
            dom = g["domaine"]
            txt = html.escape(r.get("texte", "")[:2200] + ("…" if len(r.get("texte", "")) > 2200 else "")).replace("…", "[suite]")
            for v in {pr["valeur"] for pr in c["preuves"] if pr["type"] in ("domaine", "nom")} | {dom}:
                txt = re.sub(re.escape(html.escape(v)), lambda m: f'<mark>{m.group(0)}</mark>', txt, flags=re.I)
            txt = txt.replace("\n", "<br>")
            srcs = ""
            for so in [x for x in r.get("sources", []) if x.get("citee")][:12]:
                h = hote(so.get("url", "")) or (so.get("domaine") or so.get("titre") or "")
                ok = h == dom or h.endswith("." + dom) or (so.get("titre") or "").lower() == dom
                srcs += f'<li class="{"m" if ok else ""}">{html.escape(h)}<span>{html.escape((so.get("titre") or "")[:90])}</span></li>'
            heure = dt.datetime.fromisoformat(r["heure"])
            doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{css(base_fonts)}
body{{width:1200px}}.h{{background:var(--neon);padding:26px 40px;display:flex;justify-content:space-between;align-items:center}}.h svg{{height:30px}}
.h .p{{font-family:var(--choc);font-weight:900;font-size:48px;line-height:1;color:var(--jaune);text-shadow:3px 3px 0 var(--nuit)}}.b{{padding:28px 40px 34px}}.q{{font-family:var(--choc);font-weight:900;text-transform:uppercase;font-size:32px;line-height:1.1}}
.meta{{margin-top:10px;font-size:16px}}.meta{{color:var(--brume)}}.meta b{{font-weight:700;color:var(--cyan)}}.ans{{margin-top:20px;font-size:16px;line-height:1.55;color:#fff;border-top:3px solid var(--cyan);padding-top:16px}}
mark{{background:var(--jaune);color:var(--nuit);font-weight:600;padding:0 3px}}ul{{list-style:none;margin-top:18px;border-top:1px solid var(--ombre)}}
li{{padding:6px 0;border-bottom:1px solid var(--ombre);font-weight:700;font-size:15px}}li span{{font-weight:400;color:var(--brume);margin-left:12px}}li.m{{background:var(--jaune);color:var(--nuit)}}li.m span{{color:var(--nuit)}}
.b{{background:var(--panneau)}}.ft{{padding:14px 40px;background:#06030D;color:var(--brume);font-size:14px}}</style></head><body>
<div class="h">{logo("#FFFFFF")}<div class="p">+{c['points']}{NB}point{'s' if c['points'] > 1 else ''}</div></div>
<div class="b"><div class="q">{fr(r['question'])}</div>
<div class="meta"><b>{fr(MNOM[c['moteur']])}</b> ({html.escape(r.get('modele', ''))}, recherche web), {fr(date_fr(c['date']))} à {fr(heure_fr(heure))}. Question de {html.escape(dom)}. Preuve : {fr(', '.join(sorted({pr['type'] for pr in c['preuves']})))}.</div>
<div class="ans">{txt}</div><ul>{srcs}</ul></div>
<div class="ft">{fr("Radar GEO Influa. Capture générée à partir de la réponse archivée du moteur, identifiant " + c['qid'] + ".")}</div></body></html>"""
            pg.set_content(doc, wait_until="load")
            pg.evaluate("document.fonts.ready")
            out = os.path.join(DOCS, c["image"])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            pg.screenshot(path=out, full_page=True)
        b.close()
    return len(a_faire)


# ---------------------------------------------------------------- pages
def construire(base_fonts_preuves=FONTS):
    s = calculer()
    os.makedirs(DOCS, exist_ok=True)
    shutil.copytree(os.path.join(RACINE, "assets"), os.path.join(DOCS, "assets"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(RACINE, "kit"), os.path.join(DOCS, "kit"), dirs_exist_ok=True)
    n = preuves(s, base_fonts_preuves)
    hist = s["historique"]
    us = [g["u"] for g in GROUPES]
    now = maintenant()
    jour = dt.date.fromisoformat(hist[-1]["date"]) if hist else now.date()
    h = hist[-1]
    ordre = sorted(us, key=lambda u: (h["rang"][u], -len(s["questions"][u]), u))
    corps = vitrine(s, hist, us, ordre, jour, now)
    open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(page("Radar GEO Influa, classement du Challenge GEO Inseec", corps, "", "Classement quotidien du challenge GEO Inseec 2026-2027 : " + str(NSITES) + " sites face à ChatGPT, Claude, Gemini et Perplexity.", js=True))

    # fiches groupe
    os.makedirs(os.path.join(DOCS, "groupe"), exist_ok=True)
    for g in GROUPES:
        u = g["u"]
        lignes = ""
        for q in g["questions"]:
            cells = ""
            for m in MORDRE:
                c = s["grille"][u].get(q["id"], {}).get(m)
                if not c:
                    cells += f'<td class="cell-wait">{fr("À venir")}</td>'
                elif c["cite"]:
                    cells += f'<td class="cell-ok">{fr("Cité")}<br><span class="muted">{fr(date_fr(c["date"]))}</span></td>'
                else:
                    cells += f'<td class="cell-no">{fr("Non cité")}<br><span class="muted">{fr(date_fr(c["date"]))}</span></td>'
            lignes += f"<tr><td>{fr(q['texte'])}<br><span class='muted'>{fr('Question ' + q['type'])}</span></td>{cells}</tr>"
        cit = sorted([c for c in s["citations"] if c["groupe"] == u], key=lambda c: c["date"], reverse=True)
        st = f"Rang {h['rang'][u]} sur {NSITES}, {h['cumul'][u]} points, {len(s['questions'][u])} questions citées sur 20."
        i = ordre.index(u)
        if i and h["cumul"][ordre[i - 1]] > h["cumul"][u]:
            obj = f"Encore {h['cumul'][ordre[i - 1]] - h['cumul'][u] + 1} points pour passer devant {GIDX[ordre[i - 1]]['domaine']}."
        elif i == 0 and h["cumul"][u] > 0:
            obj = f"En tête du challenge, {h['cumul'][u] - h['cumul'][ordre[1]]} points d'avance sur {GIDX[ordre[1]]['domaine']}."
        else:
            obj = "Une seule citation suffit pour prendre la tête du classement."
        libres = [q for q in g["questions"] if q["id"] not in s["questions"][u]]
        lead_g = f'<div class="score"><div class="giant">{h["rang"][u]}<small>{"er" if h["rang"][u] == 1 else "e"} sur {NSITES}</small></div><div class="facts"><div class="fact"><div class="v"><span data-n="{h["cumul"][u]}">{h["cumul"][u]}</span></div><div class="l">points</div></div><div class="fact mag"><div class="v">+<span data-n="{h["points"][u]}">{h["points"][u]}</span></div><div class="l">{fr("points ce matin")}</div></div><div class="fact"><div class="v">{len(s["questions"][u])}/20</div><div class="l">{fr("questions citées")}</div></div><div class="fact"><div class="v">{len(libres)}</div><div class="l">{fr("questions encore à prendre")}</div></div><div class="fact ja" style="grid-column:1/-1;display:flex;align-items:center;gap:14px"><img loading="lazy" decoding="async" src="../kit/rang-{niveau(h["cumul"][u])[0]}.png" alt="" width="64" height="64"><div><div class="v">{fr("Niveau " + str(niveau(h["cumul"][u])[0]) + " " + niveau(h["cumul"][u])[1])}</div>{jauge(niveau(h["cumul"][u])[0])}</div></div></div></div>'
        b = entete(g["theme"], g["domaine"], st, obj, lead_g)
        b += f"""<main><div class="wrap"><h2>{fr("Les questions encore à prendre")}</h2>
<p>{fr("Une page par question, la réponse en 40 à 50 mots en tête, une source officielle : ce sont les pages que les moteurs citent.")}</p>
<ol class="todo">{"".join(f"<li>{fr(q['texte'])} <span class='muted'>{fr('(question ' + q['type'] + ')')}</span></li>" for q in libres) or f"<li>{fr('Toutes vos questions ont déjà été citées au moins une fois.')}</li>"}</ol>
<h2>{fr("Où en sont vos 20 questions ?")}</h2>
<p class="muted">{fr("Dernier relevé de chaque moteur sur chaque question. Cité : le moteur a donné un lien vers votre site ou l'a nommé dans sa réponse.")}</p>
<div class="scroll"><table><thead><tr><th>Question</th>{''.join(f'<th>{fr(MNOM[m])}</th>' for m in MORDRE)}</tr></thead><tbody>{lignes}</tbody></table></div>
<h2>{fr("Distinctions")}</h2><p>{fr(', '.join(d['nom'] + ' (' + date_fr(d['date']) + ')' for d in s['distinctions'][u]) or "Aucune pour l'instant.")}</p>
<h2>{fr("Les captures de vos citations")}</h2>""" + (('<div class="cards">' + "".join(carte(c, "../") for c in cit) + "</div>") if cit else f"<p>{fr('Aucune citation relevée pour le moment.')}</p>") + "</div></main>"
        open(os.path.join(DOCS, "groupe", f"{u}.html"), "w", encoding="utf-8").write(page(f"{g['domaine']}, Radar GEO Influa", b.replace('href="groupe/', 'href="'), "../", f"Fiche de {g['domaine']} au Radar GEO : rang, points, niveau et état de ses 20 questions face à ChatGPT, Claude, Gemini et Perplexity.", js=True, url=f"groupe/{u}.html"))

    # journées
    os.makedirs(os.path.join(DOCS, "jour"), exist_ok=True)
    lj = ""
    for hh in reversed(hist):
        d = hh["date"]
        cj = [c for c in s["citations"] if c["date"] == d]
        tot = sum(hh["points"].values())
        rows = "".join(f"<tr><td><a href='../groupe/{u}.html'>{fr(GIDX[u]['domaine'])}</a></td><td class='n'>+{hh['points'][u]}</td><td class='n'>{hh['cumul'][u]}</td><td class='n'>{hh['rang'][u]}</td></tr>" for u in sorted(us, key=lambda u: hh["rang"][u]))
        et = s["etats"].get(d, {})
        mo = ", ".join(f"{MNOM.get(k, k)} ({v})" for k, v in et.items() if k in MNOM) or "Aucun relevé"
        b = entete("Journée du Radar", date_fr(d), f"{len(cj)} citations, {tot} points distribués", f"Moteurs relevés : {mo}.")
        b += f"""<main><div class="wrap"><h2>{fr("Points de la journée")}</h2><table><thead><tr><th>Site</th><th class="n">{fr("Points du jour")}</th><th class="n">Cumul</th><th class="n">Rang</th></tr></thead><tbody>{rows}</tbody></table>
<h2>{fr("Captures de la journée")}</h2>""" + (('<div class="cards">' + "".join(carte(c, "../") for c in cj) + "</div>") if cj else f"<p>{fr('Aucune citation ce jour-là.')}</p>") + "</div></main>"
        open(os.path.join(DOCS, "jour", f"{d}.html"), "w", encoding="utf-8").write(page(f"Journée du {date_fr(d)}, Radar GEO Influa", b, "../", f"Citations, points et relevés du {date_fr(d)} au Radar GEO du Challenge GEO Inseec.", url=f"jour/{d}.html"))
        lj += f"<tr><td><a href='jour/{d}.html'><b>{fr(date_fr(d))}</b></a></td><td class='n'>{len(cj)}</td><td class='n'>{tot}</td><td>{fr(mo)}</td></tr>"
    b = entete("Radar GEO Influa", "Les journées du challenge", "Chaque journée garde ses points et ses captures", f"Depuis le {date_fr(CFG['debut'])}.")
    b += f"<main><div class='wrap'><h2>{fr("Que s'est-il passé chaque jour ?")}</h2><div class='scroll'><table><thead><tr><th>Journée</th><th class='n'>Citations</th><th class='n'>Points</th><th>{fr('Moteurs relevés')}</th></tr></thead><tbody>{lj}</tbody></table></div></div></main>"
    open(os.path.join(DOCS, "jours.html"), "w", encoding="utf-8").write(page("Les journées, Radar GEO Influa", b, "", "Toutes les journées du Radar GEO : relevés des moteurs, citations et captures de preuve, jour par jour.", url="jours.html"))

    # règles
    b = entete("Radar GEO Influa", "Les règles du Radar", "Points, cadences des moteurs et distinctions", "Le groupe qui totalise le plus de points le 1er juin 2027 à 23 h 59 gagne le challenge.")
    b += f"""<main><div class="wrap rules">
<h2>{fr("Comment le Radar compte-t-il les points ?")}</h2><ol>
<li>{fr("Le Radar pose les 20 questions du panel de chaque site à 4 moteurs, ChatGPT, Claude, Gemini et Perplexity, par leurs interfaces de programmation officielles, recherche web activée, avec une localisation à Bordeaux.")}</li>
<li>{fr("Une citation rapporte des points quand le moteur donne un lien vers votre site dans sa réponse, écrit votre domaine, ou nomme votre site par le nom déclaré par le groupe.")}</li>
<li>{fr("Gemini est relevé chaque jour : 1 point par citation. Perplexity est relevé chaque lundi : 7 points par citation. ChatGPT et Claude sont relevés un lundi sur deux : 14 points par citation. Chaque moteur pèse ainsi autant chaque jour, soit 80 points par jour au maximum.")}</li>
<li>{fr("Seules les citations sur les questions de votre propre panel comptent.")}</li>
<li>{fr("Le site du magasin, essaie-moi.fr, figure hors concours sur toutes les questions : il sert de niveau à battre et ne prend aucune place au classement.")}</li>
<li>{fr("Égalité : le site cité sur le plus grand nombre de questions différentes passe devant.")}</li>
<li>{fr("Collecte vers 5 h, classement publié à 8 h, heure de Paris. Chaque réponse est archivée en texte intégral ; chaque citation donne lieu à une capture.")}</li></ol>
<h2>{fr("Les distinctions")}</h2><ol>
<li>{fr("Première citation : le premier jour où un moteur cite votre site.")}</li>
<li>{fr("Cité par les 4 moteurs : chacun des 4 moteurs a cité votre site au moins une fois.")}</li>
<li>{fr("10 questions citées : votre site est cité sur au moins 10 questions différentes de votre panel.")}</li>
<li>{fr("7 jours de suite : votre site marque des points 7 jours consécutifs.")}</li></ol>
<h2>{fr("Pourquoi les réponses peuvent-elles différer de l'application ?")}</h2>
<p>{fr("Le Radar interroge les moteurs sans compte personnel ni historique, comme un nouvel internaute. Vos tests dans l'application, avec votre compte, peuvent donner d'autres sources. Seul le Radar fait foi pour le classement.")}</p>
</div></main>"""
    open(os.path.join(DOCS, "regles.html"), "w", encoding="utf-8").write(page("Les règles, Radar GEO Influa", b, "", "Règles du Radar GEO : moteurs, cadences, barème de 1, 7 ou 14 points par citation, niveaux, distinctions et départage.", url="regles.html"))
    cn = os.path.join(DOCS, "CNAME")
    if CFG.get("domaine_perso"):
        open(cn, "w").write(CFG["domaine_perso"] + "\n")
    elif os.path.exists(cn):
        os.remove(cn)
    open(os.path.join(DOCS, ".nojekyll"), "w").write("")
    open(os.path.join(DOCS, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
    print(f"Site construit, {n} captures nouvelles, {len(s['citations'])} citations au total")
    return s


if __name__ == "__main__":
    import sys
    construire(sys.argv[1] if len(sys.argv) > 1 else FONTS)
