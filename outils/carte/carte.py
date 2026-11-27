"""Carte de la Gironde, focus Bordeaux Lac. Sources : IGN BD CARTO V5 et BD TOPO V3 (Géoplateforme, WFS)."""
import json, math
from shapely.geometry import shape, box, Point, mapping
from shapely.ops import unary_union
from shapely import affinity

W = H = 1200
NUIT, P1, P2, OMBRE = "#0B0618", "#160C2E", "#21123F", "#3A2A5E"
MAG, ORA, JAU, CYA, BRU = "#FF2E88", "#FF7A00", "#FFD23F", "#17E3FF", "#B9AED6"
LAC = (-0.5778, 44.8868)  # centroïde du lac de Bordeaux, BD TOPO

def load(f):
    return json.load(open(f))["features"]

deps = {f["properties"]["code_insee"]: shape(f["geometry"]) for f in load("c_dep.json")}
gir = deps["33"]
# cadrage : Gironde + marge
x0, y0, x1, y1 = gir.bounds
k = math.cos(math.radians(44.9))
X0, X1 = -2.02, 0.36
Y0 = 44.04
Y1 = Y0 + (X1 - X0) * k
vue = box(X0, Y0, X1, Y1)
S = min(W / ((X1 - X0) * k), H / (Y1 - Y0))
OX = (W - (X1 - X0) * k * S) / 2
OY = (H - (Y1 - Y0) * S) / 2

def P(x, y):
    return OX + (x - X0) * k * S, OY + (Y1 - y) * S

def d(g, tol=0.0):
    if tol:
        g = g.simplify(tol, preserve_topology=True)
    out = []
    for gg in getattr(g, "geoms", [g]):
        t = gg.geom_type
        if t == "Polygon":
            for r in [gg.exterior] + list(gg.interiors):
                out.append("M" + "L".join("%.1f %.1f" % P(*c[:2]) for c in r.coords) + "Z")
        elif t == "LineString":
            out.append("M" + "L".join("%.1f %.1f" % P(*c[:2]) for c in gg.coords))
        elif hasattr(gg, "geoms"):
            out.append(d(gg))
    return "".join(out)

terre = unary_union(list(deps.values())).buffer(0)
voisins = unary_union([g for c, g in deps.items() if c != "33"]).intersection(vue)
# mer : partie de la vue hors départements, à l'ouest (le reste est hors données)
hors = vue.difference(terre)
mer = unary_union([g for g in getattr(hors, "geoms", [hors]) if g.bounds[0] < -1.0])

surf = load("c_surf.json")
eaux = []
for f in surf:
    g = shape(f["geometry"])
    if not g.is_valid:
        g = g.buffer(0)
    n = f["properties"]["nature"]
    if n in ("Estuaire", "Ecoulement naturel", "Lac") or g.area > 0.0004:
        eaux.append(g)
eaux = unary_union(eaux).intersection(vue)

NOMS = {"la Garonne": 3.2, "Fleuve la Garonne": 3.2, "la Dordogne": 3.0, "l'Isle": 2.0, "la Dronne": 1.6,
        "la Leyre": 2.0, "la Grande Leyre": 1.6, "le Ciron": 1.4, "le Dropt": 1.4}
cours = []
for f in load("c_cours.json"):
    n = f["properties"].get("toponyme")
    if n in NOMS:
        cours.append((NOMS[n], shape(f["geometry"]).intersection(gir)))

# loupe Bordeaux Lac (BD TOPO)
RL = 0.034  # rayon en degrés de latitude, environ 4,4 km
cx, cy = P(*LAC)
LX, LY, LR = 245, 430, 200  # centre et rayon de la loupe en pixels
s2 = LR / (RL * S)  # grossissement

def PL(x, y):
    px, py = P(x, y)
    return LX + (px - cx) * s2, LY + (py - cy) * s2

def dl(g):
    out = []
    for gg in getattr(g, "geoms", [g]):
        t = gg.geom_type
        if t == "Polygon":
            for r in [gg.exterior] + list(gg.interiors):
                out.append("M" + "L".join("%.1f %.1f" % PL(*c[:2]) for c in r.coords) + "Z")
        elif t == "LineString":
            out.append("M" + "L".join("%.1f %.1f" % PL(*c[:2]) for c in gg.coords))
        elif hasattr(gg, "geoms"):
            out.append(dl(gg))
    return "".join(out)

zone = Point(LAC).buffer(RL * 1.6)
zone = affinity.scale(zone, 1 / k, 1)  # cercle vrai à l'écran
t_eau = []
for f in load("t_surf.json") + load("t_plan.json"):
    g = shape(f["geometry"])
    if not g.is_valid:
        g = g.buffer(0)
    if g.area > 2e-6 or f["properties"].get("nature") == "Ecoulement naturel":
        t_eau.append(g)
t_eau = unary_union(t_eau).intersection(zone).simplify(0.00004)
lac = [shape(f["geometry"]) for f in load("t_plan.json") if f["properties"].get("toponyme") == "le Lac"][0]
routes = {"aut": [], "r2": [], "r1": []}
for f in load("t_route.json"):
    p = f["properties"]
    n = p["nature"]
    if n in ("Type autoroutier", "Bretelle"):
        routes["aut"].append(shape(f["geometry"]))
    elif n == "Route à 2 chaussées" or p.get("importance") in ("1", "2"):
        routes["r2"].append(shape(f["geometry"]))
    elif p.get("importance") == "3":
        routes["r1"].append(shape(f["geometry"]))
for kk in routes:
    routes[kk] = unary_union(routes[kk]).intersection(zone).simplify(0.00003)

# communes pour les étiquettes
com = {f["properties"]["nom"]: shape(f["geometry"]) for f in json.load(open("com.json"))["features"]}
bx_commune = com["Bordeaux"]

def lab(x, y, t, size, fill, anchor="middle", ls=3, op=1):
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-family="Impact,Anton,\'Arial Black\',sans-serif" '
            f'font-size="{size}" letter-spacing="{ls}" fill="{fill}" opacity="{op}">{t}</text>')

def labi(x, y, t, size, fill, anchor="middle"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-family="Helvetica,Arial,sans-serif" font-style="italic" '
            f'font-size="{size}" fill="{fill}">{t}</text>')

o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     "<defs>",
     f'<pattern id="gr" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{CYA}" stroke-opacity=".07" stroke-width="1.5"/></pattern>',
     f'<radialGradient id="bal" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate({cx:.1f} {cy:.1f}) scale(300)">'
     f'<stop offset="0" stop-color="{CYA}" stop-opacity=".30"/><stop offset="1" stop-color="{CYA}" stop-opacity="0"/></radialGradient>',
     f'<clipPath id="lp"><circle cx="{LX}" cy="{LY}" r="{LR}"/></clipPath>',
     f'<clipPath id="gc"><path d="{d(gir, 0.0006)}"/></clipPath>',
     "</defs>",
     f'<rect width="{W}" height="{H}" fill="{NUIT}"/>',
     f'<path d="{d(mer, 0.0008)}" fill="url(#gr)"/>',
     f'<path d="{d(voisins, 0.0008)}" fill="{P1}" stroke="{OMBRE}" stroke-width="2"/>',
     f'<path d="{d(gir, 0.0005)}" fill="{P2}"/>',
     f'<path d="{d(bx_commune, 0.0003)}" fill="{OMBRE}" stroke="{MAG}" stroke-width="2" stroke-opacity=".9"/>',
     ]
for w, g in cours:
    o.append(f'<path d="{d(g, 0.0005)}" fill="none" stroke="{CYA}" stroke-opacity=".75" stroke-width="{w:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
o.append(f'<path d="{d(eaux, 0.0004)}" fill="{CYA}" fill-opacity=".55" stroke="{CYA}" stroke-width="1"/>')
o.append(f'<path d="{d(gir, 0.0005)}" fill="none" stroke="#FFFFFF" stroke-opacity=".9" stroke-width="3.5" stroke-linejoin="round"/>')
# radar centré sur Bordeaux Lac
o.append(f'<g clip-path="url(#gc)"><path d="M{cx:.1f} {cy:.1f}L{cx:.1f} {cy-300:.1f}A300 300 0 0 1 {cx+259.8:.1f} {cy-150:.1f}Z" fill="url(#bal)"/></g>')
for r in (70, 140, 210, 280):
    o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{JAU}" stroke-opacity="{.55 - r/700:.2f}" stroke-width="2" stroke-dasharray="{"6 8" if r > 70 else "none"}"/>')
# ligne de rappel vers la loupe
ang = math.atan2(LY - cy, LX - cx)
o.append(f'<line x1="{cx + 18*math.cos(ang):.1f}" y1="{cy + 18*math.sin(ang):.1f}" x2="{LX - LR*math.cos(ang):.1f}" y2="{LY - LR*math.sin(ang):.1f}" stroke="{JAU}" stroke-width="3"/>')
o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="16" fill="none" stroke="{JAU}" stroke-width="4"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{JAU}"/>')

# loupe
o.append(f'<circle cx="{LX}" cy="{LY}" r="{LR+10}" fill="{NUIT}"/>')
o.append(f'<g clip-path="url(#lp)"><rect x="{LX-LR}" y="{LY-LR}" width="{2*LR}" height="{2*LR}" fill="{P2}"/>')
o.append(f'<path d="{dl(routes["r1"])}" fill="none" stroke="{OMBRE}" stroke-width="2"/>')
o.append(f'<path d="{dl(routes["r2"])}" fill="none" stroke="#5B4690" stroke-width="3.5"/>')
o.append(f'<path d="{dl(routes["aut"])}" fill="none" stroke="{MAG}" stroke-width="5" stroke-linejoin="round"/>')
o.append(f'<path d="{dl(t_eau)}" fill="{CYA}" fill-opacity=".55" stroke="{CYA}" stroke-width="1.2"/>')
o.append(f'<path d="{dl(lac)}" fill="{CYA}" stroke="#FFFFFF" stroke-width="2.5"/>')
lx, ly = PL(*LAC)
for r in (60, 120, 180):
    o.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="{r}" fill="none" stroke="{JAU}" stroke-opacity=".45" stroke-width="2" stroke-dasharray="6 8"/>')
o.append("</g>")
o.append(f'<circle cx="{LX}" cy="{LY}" r="{LR}" fill="none" stroke="{JAU}" stroke-width="6"/>')
# étiquettes loupe
o.append(f'<rect x="{LX-165}" y="{LY+LR-26}" width="330" height="58" fill="{JAU}"/>')
o.append(lab(LX, LY + LR + 18, "BORDEAUX LAC", 44, NUIT, ls=4))
o.append(labi(lx, ly - 70, "Lac de Bordeaux", 26, "#FFFFFF"))
o.append(f'<g transform="translate({LX+118} {LY+92}) rotate(-66)">' + labi(0, 0, "Garonne", 22, "#FFFFFF", "middle") + "</g>")
rx, ry = PL(-0.606, 44.876); o.append(labi(rx, ry, "Rocade", 24, MAG, "middle"))

# étiquettes carte
def at(lon, lat):
    return P(lon, lat)
o.append(lab(245, 120, "OCÉAN ATLANTIQUE", 30, BRU, "middle", 6, .75))
x, y = at(-0.98, 45.60); o.append(labi(x, y, "Estuaire de la Gironde", 24, CYA, "start"))

x, y = at(-0.27, 44.665); o.append(labi(x, y, "Garonne", 24, CYA, "start"))
x, y = at(-0.16, 44.79); o.append(labi(x, y, "Dordogne", 24, CYA, "start"))
bxc = bx_commune.centroid; x, y = P(bxc.x, bxc.y); o.append(lab(x - 26, y + 42, "BORDEAUX", 36, "#FFFFFF", "end", 3))
lib = com["Libourne"].centroid; x, y = P(lib.x, lib.y); o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="#FFFFFF"/>'); o.append(lab(x + 12, y - 12, "LIBOURNE", 26, BRU, "start", 2))
arc = com["Arcachon"].centroid; x, y = P(arc.x, arc.y); o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="#FFFFFF"/>'); o.append(lab(x - 16, y + 36, "ARCACHON", 26, BRU, "end", 2)); o.append(labi(x - 46, y - 46, "Bassin d'Arcachon", 24, CYA, "end"))
lsp = com["Lesparre-Médoc"].centroid; x, y = P(lsp.x, lsp.y); o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="#FFFFFF"/>'); o.append(lab(x + 12, y + 8, "LESPARRE", 26, BRU, "start", 2))
lng = com["Langon"].centroid; x, y = P(lng.x, lng.y); o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="#FFFFFF"/>'); o.append(lab(x + 12, y + 30, "LANGON", 26, BRU, "start", 2))
# titre
o.append(lab(40, 1120, "GIRONDE", 88, JAU, "start", 10))
o.append(lab(44, 1166, "TERRAIN DU CHALLENGE", 28, CYA, "start", 6))
o.append(f'<text x="{W-24}" y="24" text-anchor="end" font-family="Helvetica,Arial,sans-serif" font-size="15" fill="{BRU}" opacity=".7">Sources : IGN BD CARTO et BD TOPO</text>')
o.append("</svg>")
open("carte.svg", "w", encoding="utf-8").write("".join(o))
print("ok", len("".join(o)) // 1024, "Ko", "lac px", round(cx), round(cy))
