"""Page d'accueil du Radar : tableau de score, podium, course des 9 sites, fil des citations,
défis et records, compte à rebours. Charte Influa Signal, animations à chaque visite."""
import html, datetime as dt
from .common import CFG, GROUPES, NB, date_fr, moteurs_du_jour

GIDX = {g["u"]: g for g in GROUPES}
MNOM = {m["id"]: m["nom"] for m in CFG["moteurs"]}
JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

CSS_JEU = """
.score{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:28px;align-items:end;margin-top:26px}
.score .giant{font-weight:600;font-size:clamp(150px,22vw,300px);line-height:.74;letter-spacing:-.05em;margin-bottom:-64px;white-space:nowrap}
.score .giant small{font-size:.16em;letter-spacing:0;font-weight:600;margin-left:10px;vertical-align:top;display:inline-block;margin-top:.5em}
.facts{display:grid;grid-template-columns:1fr 1fr;border-top:3px solid var(--anthracite)}
.fact{padding:14px 14px 14px 0;border-bottom:1px solid rgba(14,14,16,.35)}
.fact .v{font-weight:600;font-size:34px;line-height:1.05}
.fact .l{font-size:14px;margin-top:2px}
.fact.mag .v{color:var(--magenta)}
.ticker{background:var(--anthracite);color:var(--blanc);overflow:hidden;white-space:nowrap;position:relative}
.ticker .lab{position:absolute;left:0;top:0;bottom:0;display:flex;align-items:center;padding:0 18px;background:var(--magenta);font-weight:600;font-size:14px;text-transform:uppercase;letter-spacing:.1em;z-index:2}
.ticker .rail{display:inline-flex;gap:46px;padding:16px 0 16px 230px;animation:defile var(--duree,40s) linear infinite}
.ticker:hover .rail{animation-play-state:paused}
.ticker .it{font-size:16px}.ticker .it b{font-weight:600;color:var(--lime)}.ticker .it .p{color:var(--blanc);font-weight:600;margin-left:6px}
@keyframes defile{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.podium{display:grid;grid-template-columns:1fr 1.15fr 1fr;gap:14px;align-items:end;margin-top:10px}
.step{display:flex;flex-direction:column;justify-content:flex-end;text-decoration:none;overflow:hidden;position:relative;padding:18px 18px 16px}
.step .r{font-weight:600;line-height:.8;letter-spacing:-.05em;position:absolute;right:-6px;bottom:-14px;opacity:1}
.step .d{font-weight:600;font-size:20px;line-height:1.15;position:relative}
.step .t{font-size:14px;position:relative}
.step .pts{font-weight:600;font-size:44px;line-height:1;margin-top:10px;position:relative}
.step .ev{font-size:14px;font-weight:600;margin-top:4px;position:relative}
.step.s1{background:var(--lime);height:330px}.step.s1 .r{font-size:300px;color:rgba(14,14,16,.12)}
.step.s2{background:var(--anthracite);color:var(--blanc);height:270px}.step.s2 .r{font-size:240px;color:rgba(255,255,255,.1)}
.step.s3{background:var(--ink100);height:225px}.step.s3 .r{font-size:200px;color:rgba(14,14,16,.08)}
.step.vide .d{color:inherit;opacity:.7}
.step .go{position:relative;font-size:14px;font-weight:600;text-decoration:underline;margin-top:8px}
.race{margin-top:6px;border-top:3px solid var(--anthracite)}
.lane{display:grid;grid-template-columns:64px minmax(0,1.6fr) minmax(0,2.4fr) 130px 120px;gap:18px;align-items:center;padding:14px 0;border-bottom:1px solid var(--ink300);text-decoration:none;position:relative;background:var(--blanc)}
.lane:hover{background:var(--ink100)}
.lane .rk{font-weight:600;font-size:40px;line-height:1;letter-spacing:-.03em}
.lane .nm b{font-weight:600;font-size:18px;display:block}.lane .nm span{font-size:14px;color:var(--ink600)}
.br{display:block}.bar{display:block;height:14px;background:var(--ink100);position:relative}
.bar i{position:absolute;left:0;top:0;bottom:0;background:var(--anthracite);width:0;transition:width 1.4s cubic-bezier(.2,.8,.2,1)}
.lane.first .bar i{background:var(--lime)}
.gap{font-size:13px;color:var(--ink600);margin-top:6px}
.lane .pt{text-align:right}.lane .pt b{font-weight:600;font-size:30px;line-height:1;display:block}
.lane .pt .td{color:var(--magenta);font-weight:600;font-size:14px}
.lane .sp svg{width:120px;height:36px;display:block}
.lane .mv{font-size:13px;font-weight:600}
.lane .mv.up{color:var(--anthracite)}.lane .mv.down{color:var(--magenta)}
.lane .lk{font-size:13px;font-weight:600;text-decoration:underline;display:block;margin-top:4px}
.defis{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-top:3px solid var(--anthracite)}
.defi{padding:16px 16px 18px 0;border-bottom:1px solid var(--ink300)}
.defi .k{font-size:13px;text-transform:uppercase;letter-spacing:.1em;font-weight:600;color:var(--ink600)}
.defi .v{font-weight:600;font-size:22px;line-height:1.2;margin-top:6px}
.defi .v.libre{color:var(--magenta)}
.defi .x{font-size:14px;margin-top:4px}
.engines{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.eng{border:1px solid var(--ink300);padding:16px}
.eng .n{font-weight:600;font-size:20px}.eng .w{font-weight:600;font-size:56px;line-height:1;letter-spacing:-.03em;margin-top:8px}
.eng .w small{display:block;font-size:15px;letter-spacing:0;margin-top:6px}
.eng .c{font-size:14px;margin-top:6px}.eng .s{font-size:14px;margin-top:8px;font-weight:600}
.eng.today{background:var(--lime);border-color:var(--lime)}
.fact .v.cd{font-variant-numeric:tabular-nums;font-size:28px}
.chart polyline{stroke-dasharray:var(--len,3000);stroke-dashoffset:var(--len,3000);animation:trace 1.8s ease-out forwards}
@keyframes trace{to{stroke-dashoffset:0}}
.reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.reveal.on{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.ticker .rail{animation:none}.chart polyline{animation:none;stroke-dashoffset:0}.reveal{opacity:1;transform:none;transition:none}.bar i{transition:none}}
@media (max-width:900px){
 .score{grid-template-columns:1fr}.score .giant{margin-bottom:-38px}
 .podium{grid-template-columns:1fr;gap:10px}.step.s1,.step.s2,.step.s3{height:auto;min-height:150px}
 .step.s1 .r,.step.s2 .r,.step.s3 .r{font-size:170px}
 .podium .step.s1{order:1}.podium .step.s2{order:2}.podium .step.s3{order:3}
 .lane{grid-template-columns:48px minmax(0,1fr) auto;grid-template-areas:"rk nm pt" "rk br br" "rk sp mv";gap:8px 12px}
 .lane .rk{grid-area:rk;font-size:30px}.lane .nm{grid-area:nm}.lane .pt{grid-area:pt}.lane .br{grid-area:br}.lane .sp{grid-area:sp}.lane .mvw{grid-area:mv;text-align:right}
 .defis,.engines{grid-template-columns:1fr 1fr}
 .ticker .rail{padding-left:180px}
}
"""

# Script ASCII : les textes viennent du HTML.
JS = r"""
(function(){
var calme=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function fmt(n){return String(n).replace(/\B(?=(\d{3})+(?!\d))/g,'\u00a0');}
function compte(el){var fin=parseInt(el.getAttribute('data-n'),10)||0;if(calme||fin===0){el.textContent=fmt(fin);return;}
 var t0=null,d=1300;function pas(t){if(!t0)t0=t;var k=Math.min(1,(t-t0)/d);var v=Math.round(fin*(1-Math.pow(1-k,3)));el.textContent=fmt(v);if(k<1)requestAnimationFrame(pas);}
 el.textContent='0';requestAnimationFrame(pas);}
document.querySelectorAll('[data-n]').forEach(compte);
setTimeout(function(){document.querySelectorAll('.bar i[data-w]').forEach(function(b){b.style.width=b.getAttribute('data-w')+'%';});},calme?0:250);
var lanes=[].slice.call(document.querySelectorAll('.lane[data-prev]'));
if(!calme&&lanes.length){var h=lanes[0].offsetHeight;lanes.forEach(function(l){var dlt=(parseInt(l.getAttribute('data-prev'),10)-parseInt(l.getAttribute('data-now'),10))*h;
 if(dlt){l.style.transform='translateY('+dlt+'px)';l.style.zIndex=5;}});
 requestAnimationFrame(function(){requestAnimationFrame(function(){lanes.forEach(function(l){l.style.transition='transform 1.1s cubic-bezier(.2,.8,.2,1) .5s';l.style.transform='none';});});});}
document.querySelectorAll('.chart polyline').forEach(function(p){try{p.style.setProperty('--len',Math.ceil(p.getTotalLength()));}catch(e){}});
var io='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('on');io.unobserve(e.target);}});},{threshold:.12}):null;
document.querySelectorAll('.reveal').forEach(function(r){if(io&&!calme)io.observe(r);else r.classList.add('on');});
var rail=document.querySelector('.ticker .rail');if(rail){rail.innerHTML+=rail.innerHTML;rail.style.setProperty('--duree',Math.max(25,rail.children.length*4)+'s');}
function cd(){document.querySelectorAll('[data-cible]').forEach(function(el){var ms=new Date(el.getAttribute('data-cible'))-new Date();
 if(ms<=0){el.textContent=el.getAttribute('data-fin');return;}var s=Math.floor(ms/1000),hh=Math.floor(s/3600),mm=Math.floor(s%3600/60),ss=s%60;
 var j=Math.floor(hh/24);el.textContent=(j>0?j+'\u00a0j ':'')+(hh%24)+'\u00a0h '+(mm<10?'0':'')+mm+'\u00a0min '+(ss<10?'0':'')+ss+'\u00a0s';});}
cd();setInterval(cd,1000);
})();
"""


def e(s):
    from .build_site import fr
    return fr(s)


def pl(n, mot):
    return f"{n}{NB}{mot}{'s' if abs(n) > 1 else ''}"


def sparkline(vals, accent):
    if len(vals) < 2 or max(vals) == 0:
        return '<svg viewBox="0 0 120 36" aria-hidden="true"><line x1="0" y1="34" x2="120" y2="34" stroke="#C8C8CC" stroke-width="2"/></svg>'
    mx = max(vals)
    n = len(vals) - 1
    pts = " ".join(f"{120 * i / n:.1f},{34 - 30 * v / mx:.1f}" for i, v in enumerate(vals))
    return f'<svg viewBox="0 0 120 36" aria-hidden="true"><polyline fill="none" stroke="{accent}" stroke-width="2.5" points="{pts}"/></svg>'


def mouvement(v):
    if v > 0:
        return f'<span class="mv up">+{pl(v, "place")}</span>'
    if v < 0:
        return f'<span class="mv down">{v}{NB}place{"s" if v < -1 else ""}</span>'
    return '<span class="mv">Rang stable</span>'


def serie_max(hist, u):
    best = cur = 0
    who = 0
    for h in hist:
        cur = cur + 1 if h["points"][u] > 0 else 0
        best = max(best, cur)
    return best


def prochain_gros(jour):
    for i in range(0, 21):
        d = jour + dt.timedelta(days=i)
        ms = [m for m in moteurs_du_jour(d) if m["poids"] > 1]
        if ms:
            return d, ms
    return None, []


def vitrine(s, hist, us, ordre, jour, now):
    from .build_site import entete, chart, carte, logo
    h = hist[-1]
    tete = ordre[0]
    pts_t = h["cumul"][tete]
    second = ordre[1] if len(ordre) > 1 else tete
    ecart = pts_t - h["cumul"][second]
    du_jour = sum(h["points"].values())
    cj = [c for c in s["citations"] if c["date"] == h["date"]]
    tz = now.tzinfo
    pub = dt.datetime.combine(now.date(), dt.time(CFG["heure_publication"]), tz)
    if now >= pub:
        pub += dt.timedelta(days=1)
    dg, mg = prochain_gros(now.date() if now.hour < CFG["heure_collecte"] else now.date() + dt.timedelta(days=1))

    # bandeau tableau de score
    if pts_t > 0:
        titre = f"{GIDX[tete]['domaine']} mène avec {pl(pts_t, 'point')}"
        giant = f'<div class="giant"><span data-n="{pts_t}">{pts_t}</span><small>{"points" if pts_t > 1 else "point"}</small></div>'
    else:
        titre = "Qui sera cité le premier ?"
        giant = '<div class="giant">0<small>point</small></div>'
    gros = ""
    if dg:
        gros = f"{JOURS_FR[dg.weekday()].capitalize()} {date_fr(dg)} : " + " et ".join(f"{m['nom']} ({m['poids']} points par citation)" for m in mg)
    facts = f"""<div class="facts">
<div class="fact"><div class="v">{('<span data-n="' + str(ecart) + '">' + str(ecart) + '</span>') if pts_t else '0'}</div><div class="l">{e("points d'avance sur le deuxième" if pts_t else "point d'écart entre les 9 sites")}</div></div>
<div class="fact mag"><div class="v">+<span data-n="{du_jour}">{du_jour}</span></div><div class="l">{e("points distribués ce matin")}</div></div>
<div class="fact"><div class="v cd" data-cible="{pub.isoformat()}" data-fin="{e('Publication en cours')}">{e('...')}</div><div class="l">{e("avant le prochain classement, à " + str(CFG['heure_publication']) + " h")}</div></div>
<div class="fact"><div class="v"><span data-n="{len(s['citations'])}">{len(s['citations'])}</span></div><div class="l">{e("citations depuis le " + date_fr(CFG['debut']))}</div></div>
</div>"""
    corps = entete("Radar GEO Influa, challenge GEO Inseec 2026-2027", titre, "9 sites face à 4 IA. Classement chaque matin à 8 h.",
                   f"Classement arrêté au {date_fr(jour)} à {CFG['heure_publication']} h. Fin du challenge le {date_fr(CFG['fin'])} à 23 h 59.",
                   f'<div class="score">{giant}{facts}</div>')

    # fil des citations
    fil = sorted(s["citations"], key=lambda c: (c["date"], c.get("heure") or ""), reverse=True)[:16]
    if fil:
        items = "".join(f'<span class="it"><b>{e(GIDX[c["groupe"]]["domaine"])}</b> cité par {e(MNOM[c["moteur"]])} sur "{e(c["question"])}"<span class="p">+{c["points"]}</span></span>' for c in fil)
        lab = "Citations"
    else:
        items = "".join(f'<span class="it">{e(t)}</span>' for t in [
            "Première citation : à prendre", "Le premier site cité gagne la distinction Première citation",
            "Gemini relève les 9 sites chaque matin", f"{gros}" if gros else "Perplexity, ChatGPT et Claude passent le lundi",
            "Une citation de ChatGPT ou de Claude vaut 14 points"])
        lab = "En jeu"
    corps += f'<div class="ticker" aria-label="{e("Fil des citations")}"><span class="lab">{e(lab)}</span><div class="rail">{items}</div></div>'

    corps += '<main><div class="wrap">'
    # podium
    corps += f'<h2 class="reveal">{e("Le podium du jour")}</h2><div class="podium reveal">'
    for pos, cls in [(1, "s2"), (0, "s1"), (2, "s3")]:
        u = ordre[pos]
        g = GIDX[u]
        if h["cumul"][u] > 0:
            corps += f"""<a class="step {cls}" href="groupe/{u}.html"><span class="r" aria-hidden="true">{h['rang'][u]}</span>
<span class="d">{e(g['domaine'])}</span><span class="t">{e(g['theme'])}</span><span class="pts"><span data-n="{h['cumul'][u]}">{h['cumul'][u]}</span>{NB}<small style="font-size:18px">pts</small></span>
<span class="ev">{mouvement(h['evolution'][u])}</span><span class="go">{e("Voir la fiche")}</span></a>"""
        else:
            corps += f"""<div class="step {cls} vide"><span class="r" aria-hidden="true">{pos + 1}</span><span class="d">{e(str(pos + 1) + ('re' if pos == 0 else 'e') + ' place : à prendre')}</span>
<span class="t">{e("Le premier site cité monte ici")}</span></div>"""
    corps += "</div>"

    # course
    corps += f'<h2 class="reveal">{e("La course des 9 sites")}</h2><div class="race">'
    for i, u in enumerate(ordre):
        g = GIDX[u]
        w = round(100 * h["cumul"][u] / pts_t) if pts_t else 0
        devant = ordre[i - 1] if i else None
        if devant and h["cumul"][devant] > h["cumul"][u]:
            gp = f"À {pl(h['cumul'][devant] - h['cumul'][u], 'point')} de {GIDX[devant]['domaine']}"
        elif i == 0 and pts_t:
            gp = f"En tête, {pl(ecart, 'point')} d'avance"
        else:
            gp = "Une citation suffit pour prendre la tête" if not pts_t else "À égalité avec le site devant"
        prev = h["rang"][u] + h["evolution"][u]
        vals = [x["points"][u] for x in hist[-14:]]
        corps += f"""<a class="lane{' first' if i == 0 and pts_t else ''}" href="groupe/{u}.html" data-prev="{min(max(prev, 1), 9)}" data-now="{i + 1}">
<span class="rk">{h['rang'][u]}</span>
<span class="nm"><b>{e(g['domaine'])}</b><span>{e(g['theme'])}</span></span>
<span class="br"><span class="bar"><i data-w="{w}"></i></span><span class="gap">{e(gp)}</span></span>
<span class="pt"><b data-n="{h['cumul'][u]}">{h['cumul'][u]}</b><span class="td"{' style="color:#76767E"' if not h['points'][u] else ''}>+{h['points'][u]} {e("ce matin")}</span></span>
<span class="mvw"><span class="sp">{sparkline(vals, '#0E0E10' if i else '#C1C600')}</span>{mouvement(h['evolution'][u])}<span class="lk">{e("Voir la fiche")}</span></span></a>"""
    corps += f'</div><p class="muted" style="margin-top:10px">{e("Égalité de points : le site cité sur le plus de questions différentes passe devant. La courbe montre les points gagnés chaque jour sur les 14 derniers jours.")}</p>'

    # défis et records
    def premier(nom):
        for u in us:
            for d in s["distinctions"][u]:
                if d["nom"] == nom:
                    yield u, d["date"]
    pc = sorted(premier("Première citation"), key=lambda x: x[1])
    q4 = sorted(premier("Cité par les 4 moteurs"), key=lambda x: x[1])
    rec = max(((x["points"][u], u, x["date"]) for x in hist for u in us), default=(0, None, None))
    sm = max(((serie_max(hist, u), u) for u in us), default=(0, None))
    def defi(k, v, x, libre):
        return f'<div class="defi"><div class="k">{e(k)}</div><div class="v{" libre" if libre else ""}">{e(v)}</div><div class="x">{e(x)}</div></div>'
    corps += f'<h2 class="reveal">{e("Défis et records")}</h2><div class="defis reveal">'
    corps += defi("Première citation", GIDX[pc[0][0]]["domaine"] if pc else "À prendre", f"le {date_fr(pc[0][1])}" if pc else "Le premier site cité la remporte", not pc)
    corps += defi("Cité par les 4 moteurs", GIDX[q4[0][0]]["domaine"] if q4 else "À prendre", f"le {date_fr(q4[0][1])}" if q4 else "Gemini, Perplexity, ChatGPT et Claude", not q4)
    corps += defi("Record d'un matin", f"+{pl(rec[0], 'point')}" if rec[0] else "À établir", f"{GIDX[rec[1]]['domaine']}, le {date_fr(rec[2])}" if rec[0] else "Un lundi peut rapporter jusqu'à 700 points", not rec[0])
    corps += defi("Plus longue série", pl(sm[0], "jour") if sm[0] else "À lancer", f"{GIDX[sm[1]]['domaine']}, jours consécutifs avec des points" if sm[0] else "7 jours de suite donnent une distinction", not sm[0])
    corps += "</div>"

    # courbe
    corps += f'<h2 class="reveal">{e("Comment les points avancent-ils ?")}</h2>' + chart(hist, us)

    # moteurs
    corps += f'<h2 class="reveal">{e("Les 4 moteurs et leur prochain passage")}</h2><div class="engines reveal">'
    from .common import prochain_releve
    et = s["etats"].get(jour.isoformat(), {})
    for m in CFG["moteurs"]:
        cad = {"quotidien": "Chaque jour", "hebdomadaire": f"Chaque {m.get('jour')}", "bimensuel": f"Un {m.get('jour')} sur deux"}[m["cadence"]]
        auj = m in moteurs_du_jour(jour)
        st = et.get(m["id"])
        if st == "absent":
            etat = "Clé d'accès en cours d'installation"
        elif st == "plafond":
            etat = "Plafond du mois atteint"
        elif st:
            etat = f"Relevé ce matin : {st} réponses"
        else:
            pro = prochain_releve(m, jour + dt.timedelta(days=1))
            etat = f"Prochain passage : {JOURS_FR[pro.weekday()]} {date_fr(pro)}" if pro else ""
        corps += f'<div class="eng{" today" if auj else ""}"><div class="n">{e(m["nom"])}</div><div class="w">{m["poids"]}<small>{"points" if m["poids"] > 1 else "point"} par citation</small></div><div class="c">{e(cad)}</div><div class="s">{e(etat)}</div></div>'
    corps += f'</div><p class="muted" style="margin-top:10px">{e("Chaque moteur pèse autant : une citation de Perplexity vaut les 7 jours de son relevé, une citation de ChatGPT ou de Claude les 14 jours du sien.")}</p>'

    # mur des preuves
    dern = sorted(s["citations"], key=lambda c: (c["date"], c.get("heure") or ""), reverse=True)[:12]
    corps += f'<h2 class="reveal">{e("Le mur des preuves")}</h2>'
    corps += ('<div class="cards reveal">' + "".join(carte(c) for c in dern) + "</div>") if dern else f'<p>{e("Chaque citation affichera ici la capture de la réponse du moteur. Les premières arrivent après l’indexation des sites par Google et Bing.".replace("’", "'"))}</p>'
    corps += f'<p style="margin-top:14px"><a href="jours.html"><b>{e("Toutes les journées et leurs captures")}</b></a></p></div></main>'
    return corps
