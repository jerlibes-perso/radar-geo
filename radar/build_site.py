"""Construit le site du Radar dans docs/ : classement, fiches des groupes, journées, règles,
et les captures de preuve de chaque citation (PNG)."""
import os, re, json, html, shutil, datetime as dt
from .common import CFG, GROUPES, DATA, DOCS, RACINE, NB, date_fr, heure_fr, maintenant, moteurs_du_jour, prochain_releve, hote, charger
from .score import calculer

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


def css(base_fonts):
    f = "".join(f"@font-face{{font-family:Hellix;font-weight:{w};font-display:swap;src:url({police(base_fonts, n)}) format('woff2')}}"
                for w, n in [(300, "Light"), (400, "Regular"), (500, "Medium"), (600, "SemiBold")])
    return f + """
:root{--anthracite:#0E0E10;--blanc:#FFFFFF;--lime:#C1C600;--magenta:#DE007E;--ink900:#1C1C1F;--ink700:#34343A;--ink600:#5E5E66;--ink500:#76767E;--ink300:#C8C8CC;--ink100:#EFEFF1;color-scheme:light}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--blanc);color:var(--anthracite)}
body{font-family:Hellix,Arial,sans-serif;font-size:16px;line-height:1.5}
a{color:inherit}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
header.band{background:var(--lime);overflow:hidden}
header.band .wrap{padding-top:28px;padding-bottom:36px;position:relative}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.top svg{height:34px;width:auto}
.top nav a{font-weight:600;text-decoration:none;margin-left:20px;border-bottom:2px solid var(--anthracite)}
.kicker{font-weight:600;text-transform:uppercase;letter-spacing:.14em;font-size:12px;margin-top:34px}
h1{font-weight:600;font-size:64px;line-height:1;margin-top:10px;letter-spacing:-.01em}
.sub{font-size:22px;font-weight:500;margin-top:14px}
.stamp{margin-top:10px;font-size:14px}
.lead{display:grid;grid-template-columns:1fr auto;align-items:end;gap:24px;margin-top:30px}
.lead .big{font-weight:600;font-size:200px;line-height:.78;letter-spacing:-.04em;margin-bottom:-58px}
.lead .who{font-size:18px}
.lead .who b{display:block;font-size:30px;font-weight:600}
main .wrap{padding-top:40px;padding-bottom:60px}
h2{font-weight:600;font-size:28px;line-height:1.15;margin:44px 0 14px}
h3{font-weight:600;font-size:18px;margin:22px 0 8px}
p{margin-bottom:10px}
.muted{color:var(--ink600);font-size:14px}
table{width:100%;border-collapse:collapse;font-size:15px}
th{text-align:left;font-weight:600;padding:10px 10px 10px 0;border-bottom:3px solid var(--anthracite);vertical-align:bottom;white-space:nowrap}
td{padding:11px 10px 11px 0;border-bottom:1px solid var(--ink300);vertical-align:top}
td.n,th.n{text-align:right}
tr.hl td{background:var(--lime)}
td.rank{font-weight:600;font-size:22px;width:52px}
.up{font-weight:600}
.down{color:var(--magenta);font-weight:600}
.scroll{overflow-x:auto}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px}
.card{display:block;text-decoration:none;border:1px solid var(--ink300)}
.card img{width:100%;display:block;border-bottom:1px solid var(--ink300)}
.card .t{padding:10px 12px;font-size:14px}
.card .t b{font-weight:600}
.card .go{display:block;margin-top:6px;font-weight:600;text-decoration:underline}
.cell-ok{background:var(--lime);font-weight:600}
.cell-no{color:var(--ink600)}
.cell-wait{color:var(--ink500)}
.flag{display:inline-block;background:var(--magenta);color:var(--blanc);font-weight:600;font-size:12px;padding:2px 8px}
svg.chart text{font-family:Hellix,Arial,sans-serif;font-size:12px;fill:var(--ink700)}
.rules ol{padding-left:22px}
.rules li{margin-bottom:8px}
footer{background:var(--anthracite);color:var(--blanc)}
footer .wrap{padding-top:28px;padding-bottom:28px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:14px}
footer svg{height:26px;width:auto}
@media (max-width:760px){
 h1{font-size:44px}.sub{font-size:18px}
 .lead{grid-template-columns:1fr}.lead .big{font-size:120px;margin-bottom:-34px}
 .grid2{grid-template-columns:1fr}
 .wrap{padding:0 16px}
 .top nav a{margin:0 14px 0 0}
 th,td{font-size:14px}
}
"""


def page(titre, corps, chemin_racine="", desc=""):
    nav = f'<nav><a href="{chemin_racine}index.html">Classement</a><a href="{chemin_racine}jours.html">Journées</a><a href="{chemin_racine}regles.html">Règles</a></nav>'
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex, nofollow, noarchive, noimageindex">
<title>{fr(titre)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="{chemin_racine}assets/favicon.ico"><link rel="apple-touch-icon" href="{chemin_racine}assets/favicon-180.png">
<style>{css(FONTS)}</style></head><body>
{corps.replace('%%NAV%%', nav)}
<footer><div class="wrap"><div>{logo('#FFFFFF')}</div><div>{fr("Radar GEO Influa pour le challenge GEO Inseec 2026-2027. INFLUA, marque d'IA GROUP. Web company.")}</div></div></footer>
</body></html>"""


def entete(kicker, titre, sous, stamp, lead=""):
    return f"""<header class="band"><div class="wrap"><div class="top">{logo()}%%NAV%%</div>
<p class="kicker">{fr(kicker)}</p><h1>{fr(titre)}</h1><p class="sub">{fr(sous)}</p><p class="stamp">{fr(stamp)}</p>{lead}</div></header>"""


def evo(v):
    if v > 0:
        return f'<span class="up">+{v}</span>'
    if v < 0:
        return f'<span class="down">{v}</span>'
    return "="


def chart(hist, us):
    if len(hist) < 2:
        return '<p class="muted">La courbe apparaît après deux journées de relevé.</p>'
    W, H, L, R, T, B = 1100, 340, 40, 170, 10, 30
    mx = max(1, max(h["cumul"][u] for h in hist for u in us))
    n = len(hist) - 1
    X = lambda i: L + (W - L - R) * i / n
    Y = lambda v: T + (H - T - B) * (1 - v / mx)
    tete = sorted(us, key=lambda u: -hist[-1]["cumul"][u])[0]
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Cumul des points par site">']
    for k in range(5):
        v = mx * k / 4
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#EFEFF1"/><text x="{L-6}" y="{Y(v)+4:.1f}" text-anchor="end">{int(v)}</text>')
    out.append(f'<text x="{L}" y="{H-8}">{fr(date_fr(hist[0]["date"]))}</text><text x="{W-R}" y="{H-8}" text-anchor="end">{fr(date_fr(hist[-1]["date"]))}</text>')
    ys = []
    for u in sorted(us, key=lambda u: u == tete):
        pts = " ".join(f"{X(i):.1f},{Y(h['cumul'][u]):.1f}" for i, h in enumerate(hist))
        col, w = ("#0E0E10", 3.5) if u == tete else ("#76767E", 1.6)
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
    return f"""<a class="card" href="{racine}{c['image']}"><img loading="lazy" src="{racine}{c['image']}" alt="{html.escape('Capture de la réponse de ' + MNOM[c['moteur']] + ' citant ' + g['domaine'])}">
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
body{{width:1200px}}.h{{background:var(--lime);padding:26px 40px;display:flex;justify-content:space-between;align-items:center}}.h svg{{height:30px}}
.h .p{{font-weight:600;font-size:44px;line-height:1}}.b{{padding:28px 40px 34px}}.q{{font-size:30px;font-weight:600;line-height:1.2}}
.meta{{margin-top:10px;font-size:16px}}.meta b{{font-weight:600}}.ans{{margin-top:20px;font-size:16px;line-height:1.55;color:#1C1C1F;border-top:3px solid #0E0E10;padding-top:16px}}
mark{{background:var(--lime);color:#0E0E10;font-weight:600;padding:0 3px}}ul{{list-style:none;margin-top:18px;border-top:1px solid #C8C8CC}}
li{{padding:6px 0;border-bottom:1px solid #EFEFF1;font-weight:600;font-size:15px}}li span{{font-weight:400;color:#5E5E66;margin-left:12px}}li.m{{background:var(--lime)}}
.ft{{padding:14px 40px;background:#0E0E10;color:#fff;font-size:14px}}</style></head><body>
<div class="h">{logo()}<div class="p">+{c['points']}{NB}point{'s' if c['points'] > 1 else ''}</div></div>
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
    n = preuves(s, base_fonts_preuves)
    hist = s["historique"]
    us = [g["u"] for g in GROUPES]
    now = maintenant()
    jour = dt.date.fromisoformat(hist[-1]["date"]) if hist else now.date()
    h = hist[-1]
    ordre = sorted(us, key=lambda u: (h["rang"][u], u))
    tete = ordre[0]
    lead = f'<div class="lead"><div class="who">{fr("En tête")}<b>{fr(GIDX[tete]["domaine"])}</b>{fr(GIDX[tete]["theme"])}</div><div class="big">{h["cumul"][tete]}</div></div>' if h["cumul"][tete] > 0 else ""
    stamp = f"Classement arrêté au {date_fr(jour)} à {CFG['heure_publication']} h. Mesure officielle jusqu'au {date_fr(CFG['fin'])} à 23 h 59."
    corps = entete("Challenge GEO Inseec 2026-2027", "Radar GEO Influa", f"Classement du jour : 9 sites face à 4 IA", stamp, lead)
    rows = ""
    for u in ordre:
        g = GIDX[u]
        dist = ", ".join(d["nom"] for d in s["distinctions"][u]) or "Aucune pour l'instant"
        rows += f"""<tr class="{'hl' if u == tete and h['cumul'][u] > 0 else ''}"><td class="rank">{h['rang'][u]}</td><td>{evo(h['evolution'][u])}</td>
<td><a href="groupe/{u}.html"><b>{fr(g['domaine'])}</b></a><br><span class="muted">{fr(g['theme'])}</span></td>
<td class="n"><b>{h['cumul'][u]}</b></td><td class="n">+{h['points'][u]}</td><td class="n">{len(s['questions'][u])}/20</td>
<td>{fr(', '.join(MNOM[m] for m in MORDRE if m in s['moteurs'][u]) or 'Aucun')}</td><td>{fr(dist)}</td></tr>"""
    corps += f"""<main><div class="wrap">
<h2>{fr("Qui mène le challenge ?")}</h2>
<div class="scroll"><table><thead><tr><th>Rang</th><th>{fr("Évolution")}</th><th>Site</th><th class="n">Points</th><th class="n">{fr("Aujourd'hui")}</th><th class="n">{fr("Questions citées")}</th><th>Moteurs qui citent</th><th>Distinctions</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="muted">{fr("Évolution : places gagnées ou perdues depuis la veille. Égalité de points : le site cité sur le plus de questions différentes passe devant. Cliquez un site pour voir ses 20 questions et ses captures.")}</p>
<h2>{fr("Comment les points avancent-ils ?")}</h2>{chart(hist, us)}
"""
    # relevés du jour
    et = s["etats"].get(jour.isoformat(), {})
    rr = ""
    for m in CFG["moteurs"]:
        prevu = m in moteurs_du_jour(jour)
        st = et.get(m["id"])
        if st == "absent":
            etat = "Clé d'accès à configurer"
        elif st == "plafond":
            etat = "Plafond de dépense du mois atteint"
        elif st:
            etat = f"Relevé : {st} réponses"
        else:
            etat = "Prévu aujourd'hui" if prevu else "Pas de relevé aujourd'hui"
        pro = prochain_releve(m, jour + dt.timedelta(days=1))
        cad = {"quotidien": "chaque jour", "hebdomadaire": f"chaque {m.get('jour')}", "bimensuel": f"un {m.get('jour')} sur deux"}[m["cadence"]]
        rr += f"<tr><td><b>{fr(m['nom'])}</b></td><td>{fr(cad)}</td><td class='n'>{m['poids']}</td><td>{fr(etat)}</td><td>{fr(date_fr(pro)) if pro else ''}</td></tr>"
    corps += f"""<h2>{fr("Quels moteurs ont été interrogés aujourd'hui ?")}</h2>
<div class="scroll"><table><thead><tr><th>Moteur</th><th>Relevé</th><th class="n">{fr("Points par citation")}</th><th>{fr("État du jour")}</th><th>{fr("Prochain relevé")}</th></tr></thead><tbody>{rr}</tbody></table></div>
<p class="muted">{fr("Chaque moteur pèse autant chaque jour. Un moteur relevé une fois par semaine compte 7 points par citation, ceux de ses 7 jours. Un moteur relevé tous les 15 jours compte 14 points.")}</p>
"""
    dern = sorted(s["citations"], key=lambda c: (c["date"], c.get("heure") or ""), reverse=True)[:12]
    corps += f"<h2>{fr('Quelles réponses citent vos sites ?')}</h2>"
    corps += ('<div class="cards">' + "".join(carte(c) for c in dern) + "</div>") if dern else f'<p>{fr("Aucune citation relevée pour le moment. Les premières arrivent après l'indexation des sites par Google et Bing.")}</p>'
    corps += f'<p style="margin-top:14px"><a href="jours.html"><b>{fr("Toutes les journées et leurs captures")}</b></a></p></div></main>'
    open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(page("Radar GEO Influa", corps, "", "Classement quotidien du challenge GEO Inseec 2026-2027 : 9 sites face à ChatGPT, Claude, Gemini et Perplexity."))

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
        st = f"Rang {h['rang'][u]}, {h['cumul'][u]} points, {len(s['questions'][u])} questions citées sur 20."
        b = entete(g["theme"], g["domaine"], st, f"Arrêté au {date_fr(jour)} à {CFG['heure_publication']} h.")
        b += f"""<main><div class="wrap"><h2>{fr("Où en sont vos 20 questions ?")}</h2>
<p class="muted">{fr("Dernier relevé de chaque moteur sur chaque question. Cité : le moteur a donné un lien vers votre site ou l'a nommé dans sa réponse.")}</p>
<div class="scroll"><table><thead><tr><th>Question</th>{''.join(f'<th>{fr(MNOM[m])}</th>' for m in MORDRE)}</tr></thead><tbody>{lignes}</tbody></table></div>
<h2>{fr("Distinctions")}</h2><p>{fr(', '.join(d['nom'] + ' (' + date_fr(d['date']) + ')' for d in s['distinctions'][u]) or "Aucune pour l'instant.")}</p>
<h2>{fr("Les captures de vos citations")}</h2>""" + (('<div class="cards">' + "".join(carte(c, "../") for c in cit) + "</div>") if cit else f"<p>{fr('Aucune citation relevée pour le moment.')}</p>") + "</div></main>"
        open(os.path.join(DOCS, "groupe", f"{u}.html"), "w", encoding="utf-8").write(page(f"{g['domaine']}, Radar GEO Influa", b.replace('href="groupe/', 'href="'), "../"))

    # journées
    os.makedirs(os.path.join(DOCS, "jour"), exist_ok=True)
    lj = ""
    for hh in reversed(hist):
        d = hh["date"]
        cj = [c for c in s["citations"] if c["date"] == d]
        tot = sum(hh["points"].values())
        rows = "".join(f"<tr><td><a href='../groupe/{u}.html'>{fr(GIDX[u]['domaine'])}</a></td><td class='n'>+{hh['points'][u]}</td><td class='n'>{hh['cumul'][u]}</td><td class='n'>{hh['rang'][u]}</td></tr>" for u in sorted(us, key=lambda u: hh["rang"][u]))
        et = s["etats"].get(d, {})
        mo = ", ".join(f"{MNOM[k]} ({v})" for k, v in et.items()) or "Aucun relevé"
        b = entete("Journée du Radar", date_fr(d), f"{len(cj)} citations, {tot} points distribués", f"Moteurs relevés : {mo}.")
        b += f"""<main><div class="wrap"><h2>{fr("Points de la journée")}</h2><table><thead><tr><th>Site</th><th class="n">{fr("Points du jour")}</th><th class="n">Cumul</th><th class="n">Rang</th></tr></thead><tbody>{rows}</tbody></table>
<h2>{fr("Captures de la journée")}</h2>""" + (('<div class="cards">' + "".join(carte(c, "../") for c in cj) + "</div>") if cj else f"<p>{fr('Aucune citation ce jour-là.')}</p>") + "</div></main>"
        open(os.path.join(DOCS, "jour", f"{d}.html"), "w", encoding="utf-8").write(page(f"Journée du {date_fr(d)}, Radar GEO Influa", b, "../"))
        lj += f"<tr><td><a href='jour/{d}.html'><b>{fr(date_fr(d))}</b></a></td><td class='n'>{len(cj)}</td><td class='n'>{tot}</td><td>{fr(mo)}</td></tr>"
    b = entete("Radar GEO Influa", "Les journées du challenge", "Chaque journée garde ses points et ses captures", f"Depuis le {date_fr(CFG['debut'])}.")
    b += f"<main><div class='wrap'><h2>{fr("Que s'est-il passé chaque jour ?")}</h2><div class='scroll'><table><thead><tr><th>Journée</th><th class='n'>Citations</th><th class='n'>Points</th><th>{fr('Moteurs relevés')}</th></tr></thead><tbody>{lj}</tbody></table></div></div></main>"
    open(os.path.join(DOCS, "jours.html"), "w", encoding="utf-8").write(page("Les journées, Radar GEO Influa", b))

    # règles
    b = entete("Radar GEO Influa", "Les règles du Radar", "Points, cadences des moteurs et distinctions", "Le groupe qui totalise le plus de points le 1er juin 2027 à 23 h 59 gagne le challenge.")
    b += f"""<main><div class="wrap rules">
<h2>{fr("Comment le Radar compte-t-il les points ?")}</h2><ol>
<li>{fr("Le Radar pose les 20 questions du panel de chaque site à 4 moteurs, ChatGPT, Claude, Gemini et Perplexity, par leurs interfaces de programmation officielles, recherche web activée, avec une localisation à Bordeaux.")}</li>
<li>{fr("Une citation rapporte des points quand le moteur donne un lien vers votre site dans sa réponse, écrit votre domaine, ou nomme votre site par le nom déclaré par le groupe.")}</li>
<li>{fr("Gemini est relevé chaque jour : 1 point par citation. Perplexity est relevé chaque lundi : 7 points par citation. ChatGPT et Claude sont relevés un lundi sur deux : 14 points par citation. Chaque moteur pèse ainsi autant chaque jour, soit 80 points par jour au maximum.")}</li>
<li>{fr("Seules les citations sur les questions de votre propre panel comptent.")}</li>
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
    open(os.path.join(DOCS, "regles.html"), "w", encoding="utf-8").write(page("Les règles, Radar GEO Influa", b))
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
