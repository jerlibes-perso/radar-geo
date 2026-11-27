"""Page d'accueil du Radar : tableau de score, podium, course des 9 sites, fil des citations,
défis et records, compte à rebours. Charte Influa Signal, animations à chaque visite."""
import html, datetime as dt
from .common import CFG, GROUPES, NB, date_fr, moteurs_du_jour

GIDX = {g["u"]: g for g in GROUPES}
MNOM = {m["id"]: m["nom"] for m in CFG["moteurs"]}
JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

CSS_JEU = """
.score{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:28px;align-items:end;margin-top:22px}
.score .cl{font-family:var(--choc);font-weight:900;letter-spacing:4px;text-transform:uppercase;color:var(--cyan);font-size:16px}
.score .compte{font-family:var(--choc);font-weight:900;color:var(--jaune);font-size:clamp(76px,13vw,168px);line-height:.92;text-shadow:5px 5px 0 var(--magenta);font-variant-numeric:tabular-nums;white-space:nowrap}
.score .giant{font-family:var(--choc);font-weight:900;color:var(--jaune);font-size:clamp(130px,20vw,240px);line-height:.85;text-shadow:6px 6px 0 var(--magenta);white-space:nowrap}
.score .giant small{font-size:.2em;margin-left:10px;color:#fff;text-shadow:none;vertical-align:top;display:inline-block;margin-top:.6em}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.fact{background:rgba(11,6,24,.72);padding:12px 14px}
.fact .v{font-family:var(--choc);font-weight:900;font-size:36px;line-height:1.05;color:#fff}
.fact .l{font-size:13px;color:var(--brume);margin-top:2px}
.fact.mag .v{color:var(--magenta)}.fact.cy .v{color:var(--cyan)}.fact.ja .v{color:var(--jaune)}
.ticker{background:var(--neon);color:#fff;overflow:hidden;white-space:nowrap;position:relative}
.ticker .lab{position:absolute;left:0;top:0;bottom:0;display:flex;align-items:center;padding:0 18px;background:var(--nuit);color:var(--jaune);font-family:var(--choc);font-weight:900;font-size:16px;text-transform:uppercase;letter-spacing:3px;z-index:2}
.ticker .rail{display:inline-flex;gap:46px;padding:14px 0 14px 200px;animation:defile var(--duree,40s) linear infinite}
.ticker:hover .rail{animation-play-state:paused}
.ticker .it{font-family:var(--choc);font-weight:900;font-size:17px;letter-spacing:2px;text-transform:uppercase}.ticker .it b{color:var(--jaune)}.ticker .it .p{color:var(--nuit);margin-left:6px}
@keyframes defile{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.podium{display:grid;grid-template-columns:1fr 1.15fr 1fr;gap:10px;align-items:end;margin-top:10px}
.step{display:flex;flex-direction:column;justify-content:flex-end;text-decoration:none;overflow:hidden;position:relative;padding:18px 18px 16px;background:var(--panneau2)}
.step .r{font-family:var(--choc);font-weight:900;line-height:.8;position:absolute;right:8px;bottom:-4px;text-shadow:5px 5px 0 var(--nuit)}
.step .d{font-family:var(--choc);font-weight:900;text-transform:uppercase;font-size:22px;line-height:1.1;position:relative}
.step .t{font-size:14px;position:relative;color:var(--brume)}
.step .pts{font-family:var(--choc);font-weight:900;font-size:50px;line-height:1;margin-top:10px;position:relative}
.step .ev{font-size:14px;font-weight:700;margin-top:4px;position:relative}
.step.s1{height:330px;border-top:6px solid var(--jaune)}.step.s1 .r{font-size:280px;color:var(--jaune)}
.step.s2{height:270px;border-top:6px solid var(--cyan)}.step.s2 .r{font-size:220px;color:var(--cyan)}
.step.s3{height:225px;border-top:6px solid var(--magenta)}.step.s3 .r{font-size:190px;color:var(--magenta)}
.step .go{position:relative;font-size:14px;font-weight:700;color:var(--cyan);text-decoration:underline;margin-top:8px}
.jeu{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:18px;align-items:start}
.jeu aside img{width:100%;height:auto;display:block}
.jeu aside p{font-size:13px;color:var(--brume);margin-top:8px}
.lane{display:grid;grid-template-columns:56px minmax(0,1.4fr) minmax(0,1.6fr) 100px 110px;gap:14px;align-items:center;padding:12px 14px;margin-bottom:6px;text-decoration:none;position:relative;background:var(--panneau2)}
.lane:hover{background:var(--ombre)}
.lane .rk{font-family:var(--choc);font-weight:900;font-size:42px;line-height:1;color:#fff}
.lane:nth-child(1) .rk{color:var(--jaune)}.lane:nth-child(2) .rk{color:var(--cyan)}.lane:nth-child(3) .rk{color:var(--magenta)}
.lane .nm b{font-weight:700;font-size:17px;display:block}.lane .nm span{font-size:13px;color:var(--brume)}
.niv{display:flex;align-items:center;gap:10px}
.niv img{width:40px;height:40px;display:block}
.niv .nn{font-family:var(--choc);font-weight:900;font-size:14px;letter-spacing:2px;text-transform:uppercase}
.niv .jauge{margin-top:5px}
.gap{display:block;font-size:12px;color:var(--brume);margin-top:4px}
.lane .pt{text-align:right}.lane .pt b{font-family:var(--choc);font-weight:900;font-size:38px;line-height:1;display:block}
.lane .pt .td{color:var(--magenta);font-weight:700;font-size:13px}
.lane .sp svg{width:110px;height:32px;display:block}
.lane .mv{font-size:12px;font-weight:700;color:var(--brume)}
.lane .mv.up{color:var(--cyan)}.lane .mv.down{color:var(--magenta)}
.lane .lk{font-size:12px;font-weight:700;color:var(--cyan);text-decoration:underline;display:block;margin-top:3px}
.niveaux{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
.niveaux div{background:var(--panneau);text-align:center;padding:12px 8px}
.niveaux img{width:110px;height:110px;display:block;margin:0 auto}
.niveaux b{display:block;font-family:var(--choc);font-weight:900;color:var(--jaune);font-size:18px;letter-spacing:1px;text-transform:uppercase;margin-top:4px}
.niveaux span{font-size:13px;color:var(--brume)}
.missions{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.mi{background:var(--panneau);padding:16px;display:flex;flex-direction:column;gap:8px}
.mi h3{margin:0;font-size:22px;line-height:1.05}
.mi .mission{padding:10px 12px}
.mi .mission p{margin:2px 0 0;font-size:14px}
.mi .st{font-family:var(--choc);font-weight:900;letter-spacing:2px;text-transform:uppercase;font-size:15px;color:var(--jaune);margin-top:auto}
.mi .st.ouv{color:var(--cyan)}
.engines{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.eng{background:var(--panneau);padding:16px;border-top:4px solid var(--ombre)}
.eng .n{font-family:var(--choc);font-weight:900;text-transform:uppercase;letter-spacing:1px;font-size:22px}
.eng .w{font-family:var(--choc);font-weight:900;font-size:64px;line-height:1;color:var(--jaune);margin-top:6px}
.eng .w small{display:block;font-family:var(--texte);font-weight:700;font-size:14px;color:#fff;margin-top:6px}
.eng .c{font-size:14px;margin-top:6px;color:var(--brume)}.eng .s{font-size:14px;margin-top:8px;font-weight:700;color:var(--cyan)}
.eng.today{border-top-color:var(--jaune);background:var(--panneau2)}
.cta{margin:22px 0 4px}
svg.chart{background:var(--panneau);padding:10px}
.chart polyline{stroke-dasharray:var(--len,3000);stroke-dashoffset:var(--len,3000);animation:trace 1.8s ease-out forwards}
@keyframes trace{to{stroke-dashoffset:0}}
.reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.reveal.on{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.ticker .rail{animation:none}.chart polyline{animation:none;stroke-dashoffset:0}.reveal{opacity:1;transform:none;transition:none}}
@media (max-width:980px){.jeu{grid-template-columns:1fr}.jeu aside{max-width:360px}.missions{grid-template-columns:1fr 1fr}}
@media (max-width:900px){
 .score{grid-template-columns:1fr}
 .podium{grid-template-columns:1fr;gap:8px}.step.s1,.step.s2,.step.s3{height:auto;min-height:150px}
 .step.s1 .r,.step.s2 .r,.step.s3 .r{font-size:150px}
 .lane{grid-template-columns:44px minmax(0,1fr) auto;grid-template-areas:"rk nm pt" "rk nv nv" "rk sp mv";gap:8px 12px}
 .lane .rk{grid-area:rk;font-size:32px}.lane .nm{grid-area:nm}.lane .pt{grid-area:pt}.lane .nvw{grid-area:nv}.lane .sp{grid-area:sp}.lane .mvw{grid-area:mv;text-align:right}
 .engines{grid-template-columns:1fr 1fr}.niveaux{grid-template-columns:repeat(3,1fr)}.niveaux img{width:80px;height:80px}
 .ticker .rail{padding-left:150px}
 .lane .sp{display:none}.lane{grid-template-areas:"rk nm pt" "rk nv nv" "rk mv mv"}
}
@media (max-width:560px){.missions{grid-template-columns:1fr}}
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
function d2(x){return (x<10?'0':'')+x;}
function cd(){document.querySelectorAll('[data-cible]').forEach(function(el){var ms=new Date(el.getAttribute('data-cible'))-new Date();
 if(ms<=0){el.textContent=el.getAttribute('data-fin');return;}var s=Math.floor(ms/1000),hh=Math.floor(s/3600),mm=Math.floor(s%3600/60),ss=s%60;
 el.textContent=el.classList.contains('compte')?(d2(hh)+':'+d2(mm)+':'+d2(ss)):(hh+'\u00a0h '+d2(mm)+'\u00a0min');});}
cd();setInterval(cd,1000);
})();
"""


def e(s):
    from .build_site import fr
    return fr(s)


def pl(n, mot):
    return f"{n}{NB}{mot}{'s' if abs(n) > 1 else ''}"


NIVEAUX = [(75, 5, "Autorité"), (30, 4, "Référence"), (10, 3, "Cité"), (1, 2, "Repéré"), (0, 1, "Éclaireur")]


def niveau(pts):
    for seuil, n, nom in NIVEAUX:
        if pts >= seuil:
            return n, nom


def jauge(n):
    return '<span class="jauge" aria-hidden="true">' + "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(5)) + "</span>"


def sparkline(vals, accent):
    if len(vals) < 2 or max(vals) == 0:
        return '<svg viewBox="0 0 120 36" aria-hidden="true"><line x1="0" y1="34" x2="120" y2="34" stroke="#3A2A5E" stroke-width="2"/></svg>'
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

    # écran d'ouverture
    egaux = [u for u in us if h["cumul"][u] == pts_t]
    if len(egaux) > 1:
        titre = f"{len(egaux)} sites à égalité, {pl(pts_t, 'point')}"
    else:
        titre = f"{GIDX[tete]['domaine']} en tête avec {pl(pts_t, 'point')}"
    gros = ""
    if dg:
        gros = f"{JOURS_FR[dg.weekday()].capitalize()} {date_fr(dg)} : " + " et ".join(f"{m['nom']} ({m['poids']} points par citation)" for m in mg)
    compte = f'<div><div class="cl">{e("Prochain classement dans")}</div><div class="compte" data-cible="{pub.isoformat()}" data-fin="{e("En cours")}">00:00:00</div></div>'
    facts = f"""<div class="facts">
<div class="fact ja"><div class="v"><span data-n="{pts_t}">{pts_t}</span></div><div class="l">{e("points pour le premier")}</div></div>
<div class="fact cy"><div class="v"><span data-n="{ecart}">{ecart}</span></div><div class="l">{e("points d'écart avec le deuxième")}</div></div>
<div class="fact mag"><div class="v">+<span data-n="{du_jour}">{du_jour}</span></div><div class="l">{e("points distribués ce matin")}</div></div>
<div class="fact"><div class="v"><span data-n="{len(s['citations'])}">{len(s['citations'])}</span></div><div class="l">{e("citations depuis le " + date_fr(CFG['debut']))}</div></div>
</div>"""
    corps = entete("Challenge GEO Inseec MSC M1 Marketing Digital et Big Data", titre, "9 sites face à 4 IA. Nouveau classement chaque matin à 8 h.",
                   f"Classement arrêté au {date_fr(jour)} à {CFG['heure_publication']} h. Fin du challenge le {date_fr(CFG['fin'])} à 23 h 59.",
                   f'<div class="score">{compte}{facts}</div>')

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

    # course et carte
    corps += f'<h2 class="reveal">{e("La course des 9 sites")}</h2><div class="jeu"><div class="race">'
    for i, u in enumerate(ordre):
        g = GIDX[u]
        devant = ordre[i - 1] if i else None
        if devant and h["cumul"][devant] > h["cumul"][u]:
            gp = f"À {pl(h['cumul'][devant] - h['cumul'][u], 'point')} de {GIDX[devant]['domaine']}"
        elif i == 0 and pts_t and len(egaux) == 1:
            gp = f"En tête, {pl(ecart, 'point')} d'avance"
        else:
            gp = "Une citation suffit pour prendre la tête" if not pts_t else "À égalité avec le site devant"
        prev = h["rang"][u] + h["evolution"][u]
        vals = [x["points"][u] for x in hist[-14:]]
        n, nom = niveau(h["cumul"][u])
        corps += f"""<a class="lane" href="groupe/{u}.html" data-prev="{min(max(prev, 1), 9)}" data-now="{i + 1}">
<span class="rk">{h['rang'][u]}</span>
<span class="nm"><b>{e(g['domaine'])}</b><span>{e(g['theme'])}</span></span>
<span class="nvw"><span class="niv"><img src="kit/rang-{n}.png" alt="{e('Niveau ' + str(n) + ', ' + nom)}" width="40" height="40"><span><span class="nn">{e('Niveau ' + str(n) + ' ' + nom)}</span><br>{jauge(n)}</span></span><span class="gap">{e(gp)}</span></span>
<span class="pt"><b data-n="{h['cumul'][u]}">{h['cumul'][u]}</b><span class="td"{' style="color:#B9AED6"' if not h['points'][u] else ''}>+{h['points'][u]} {e("ce matin")}</span></span>
<span class="mvw"><span class="sp">{sparkline(vals, '#FFD23F' if i == 0 else '#17E3FF')}</span>{mouvement(h['evolution'][u])}<span class="lk">{e("Voir la fiche")}</span></span></a>"""
    corps += f"""</div><aside><img src="kit/carte.png" alt="{e('Carte radar de Bordeaux Lac, un point par site du challenge')}" width="600" height="600"><p>{e("Bordeaux Lac, terrain de jeu des 9 sites : chaque point est un site en course.")}</p></aside></div>"""
    corps += f'<p class="muted" style="margin-top:10px">{e("Égalité de points : le site cité sur le plus de questions différentes passe devant. La courbe de chaque ligne montre les points gagnés sur les 14 derniers jours.")}</p>'
    corps += f'<p class="cta"><a class="bouton" href="regles.html">{e("Voir les règles du jeu")}</a></p>'

    # niveaux
    corps += f'<h2 class="reveal">{e("Les 5 niveaux")}</h2><div class="niveaux reveal">'
    for seuil, n, nom in sorted(NIVEAUX, key=lambda x: x[1]):
        corps += f'<div><img src="kit/rang-{n}.png" alt="" width="240" height="240"><b>{e(nom)}</b><span>{e("Dès " + pl(seuil, "point") if seuil else "Au départ")}</span></div>'
    corps += "</div>"

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
    def mission(titre, objectif, cible, recompense, statut, ouverte):
        return f"""<div class="mi"><h3>{e(titre)}</h3>
<div class="mission"><div class="etiquette">Objectif</div><p>{e(objectif)}</p></div>
<div class="mission"><div class="etiquette">Cible</div><p>{e(cible)}</p></div>
<div class="mission"><div class="etiquette">{e("Récompense")}</div><p>{e(recompense)}</p></div>
<div class="st{' ouv' if ouverte else ''}">{e(statut)}</div></div>"""
    corps += f'<h2 class="reveal">{e("Missions en cours")}</h2><div class="missions reveal">'
    corps += mission("Première citation", "Être cité une première fois par un des 4 moteurs.", "Une des 20 questions de votre panel.", "La distinction Première citation et le niveau 2 Repéré.",
                     f"Remportée par {GIDX[pc[0][0]]['domaine']} le {date_fr(pc[0][1])}" if pc else "Mission ouverte", not pc)
    corps += mission("Les 4 moteurs", "Être cité par Gemini, Perplexity, ChatGPT et Claude.", "Vos questions locales sur Bordeaux.", "La distinction Cité par les 4 moteurs.",
                     f"Remportée par {GIDX[q4[0][0]]['domaine']} le {date_fr(q4[0][1])}" if q4 else "Mission ouverte", not q4)
    corps += mission("Lundi décisif", "Être cité par Perplexity, ChatGPT ou Claude un lundi.", gros or "Le prochain lundi de relevé.", "7 points par citation de Perplexity, 14 pour ChatGPT ou Claude.",
                     f"Record : +{pl(rec[0], 'point')}, {GIDX[rec[1]]['domaine']}" if rec[0] else "Mission ouverte", not rec[0])
    corps += mission("7 jours de suite", "Marquer des points 7 matins consécutifs.", "Gemini, relevé chaque jour.", "La distinction 7 jours de suite.",
                     f"Meilleure série : {pl(sm[0], 'jour')}, {GIDX[sm[1]]['domaine']}" if sm[0] else "Mission ouverte", not sm[0])
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
    corps += f'<p class="cta"><a class="bouton" href="jours.html">{e("Toutes les journées et leurs captures")}</a></p></div></main>'
    return corps
