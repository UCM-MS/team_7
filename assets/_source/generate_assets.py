#!/usr/bin/env python3
"""Generátor grafických assetov – Robotická číselná misia (Tím č. 7).

Skript vytvorí SVG zdroje do assets/_source/svg/ a vyrenderuje ich do PNG
do priečinkov assets/<kategória>/ pomocou Inkscape (CLI).

Spustenie (z koreňa projektu):
    python3 assets/_source/generate_assets.py
Voliteľne cesta k Inkscape:
    INKSCAPE=/cesta/k/inkscape python3 assets/_source/generate_assets.py

Všetka grafika je pôvodná (vektorová, kreslená kódom), nevyžaduje externé
balíky a dá sa voľne upravovať. Farby sú v slovníku PAL (zhodné s ADD).
"""
import math
import os
import random
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # assets/
SRC = os.path.join(ROOT, "_source", "svg")
INKSCAPE = os.environ.get("INKSCAPE") or shutil.which("inkscape") or "/Applications/Inkscape.app/Contents/MacOS/inkscape"

# ---------------------------------------------------------------- paleta (ADD 2.2)
PAL = {
    "bg": "#101B2D",        # tmavomodrá – pozadie
    "bg_deep": "#070F1E",
    "panel": "#245B8F",     # modrá – panely
    "panel_dark": "#14304F",
    "cyan": "#35D6D0",      # tyrkysová – aktívne prvky
    "cyan_hi": "#9FF5F0",
    "green": "#54D68A",     # správna odpoveď
    "red": "#F05B67",       # nesprávna odpoveď
    "white": "#FFFFFF",
    "orange": "#FFB547",    # upozornenia
    "yellow": "#FFD64A",    # hviezdy, navigačné značky
    "purple": "#9B6BFF",    # bonus / portál
    "outline": "#0B1A33",   # obrys postáv a objektov
    "metal": "#E8F2FF",
    "metal_dark": "#9DB4CF",
}

JOBS = []  # (svg_path, png_path, width, height)


def shade(hex_color, f):
    """f>0 zosvetlí, f<0 stmaví (−1..1)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if f >= 0:
        r, g, b = [int(c + (255 - c) * f) for c in (r, g, b)]
    else:
        r, g, b = [int(c * (1 + f)) for c in (r, g, b)]
    return "#%02X%02X%02X" % (r, g, b)


def svg_doc(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>')


def emit(rel_png, w, h, body, defs=""):
    """Zapíše SVG zdroj a zaradí PNG do renderovania."""
    name = rel_png.replace("/", "__").replace(".png", ".svg")
    svg_path = os.path.join(SRC, name)
    png_path = os.path.join(ROOT, rel_png)
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(svg_doc(w, h, body, defs))
    JOBS.append((svg_path, png_path, w, h))


def lin(id_, stops, x1=0, y1=0, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def rad(id_, stops, cx=0.5, cy=0.5, r=0.5, fx=None, fy=None):
    fx = cx if fx is None else fx
    fy = cy if fy is None else fy
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}" fx="{fx}" fy="{fy}">{s}</radialGradient>'


def blur(id_, sd):
    return (f'<filter id="{id_}" x="-60%" y="-60%" width="220%" height="220%">'
            f'<feGaussianBlur stdDeviation="{sd}"/></filter>')


def glow(id_, sd, color=None):
    """Žiara okolo objektu (kópia rozmazaná pod originálom)."""
    flood = f'<feFlood flood-color="{color}"/><feComposite in2="b" operator="in"/>' if color else ""
    return (f'<filter id="{id_}" x="-60%" y="-60%" width="220%" height="220%">'
            f'<feGaussianBlur in="SourceGraphic" stdDeviation="{sd}" result="b"/>{flood}'
            f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


# ====================================================================== ROBOT RX-7
ROBOT_DEFS = (
    lin("rbMetal", [(0, "#FFFFFF", 1), (0.55, "#E6F0FB", 1), (1, "#AFC3DB", 1)])
    + lin("rbVisor", [(0, "#16305A", 1), (1, "#050C1C", 1)])
    + lin("rbBlue", [(0, "#5FB8FF", 1), (1, "#1D5FD0", 1)])
    + rad("rbChest", [(0, "#E9FFFE", 1), (0.45, PAL["cyan"], 1), (1, "#0E7C9A", 1)])
    + glow("rbGlow", 2.2)
)
OUT = PAL["outline"]


def robot(dy=0, arm_l=8, arm_r=8, leg_l=0, leg_r=0, lift_l=0, lift_r=0, eyes="open", tilt=0,
          sx=1.0, sy=1.0, look=0, head_dy=0, tint=None):
    """Vráti SVG skupinu robota v rámčeku 128×128 (chodidlá na y≈121).
    arm_* = uhol od tela (0 = dole, 90 = vodorovne, 170 = hore), leg_* = výkyv nohy,
    lift_* = zdvih chodidla, eyes = open/blink/happy/sad/x/closed, look = posun očí."""
    sw = 2.6
    parts = []

    def leg(x, ang, lift):
        return (f'<g transform="translate({x},{98 - lift}) rotate({ang})">'
                f'<rect x="-5" y="0" width="10" height="17" rx="5" fill="url(#rbMetal)" stroke="{OUT}" stroke-width="{sw}"/>'
                f'<ellipse cx="0" cy="18" rx="9" ry="5.2" fill="url(#rbBlue)" stroke="{OUT}" stroke-width="{sw}"/></g>')

    def arm(x, ang):
        return (f'<g transform="translate({x},80) rotate({ang})">'
                f'<rect x="-4.6" y="-2" width="9.2" height="22" rx="4.6" fill="url(#rbMetal)" stroke="{OUT}" stroke-width="{sw}"/>'
                f'<circle cx="0" cy="22" r="6" fill="url(#rbBlue)" stroke="{OUT}" stroke-width="{sw}"/></g>')

    parts.append(leg(56, leg_l, lift_l))
    parts.append(leg(72, leg_r, lift_r))
    parts.append(arm(44, arm_l))           # ľavá ruka (z pohľadu diváka)
    parts.append(arm(84, -arm_r))          # pravá ruka
    # telo
    parts.append(f'<rect x="43" y="70" width="42" height="33" rx="15" fill="url(#rbMetal)" stroke="{OUT}" stroke-width="{sw}"/>')
    parts.append(f'<path d="M50 96 Q64 101 78 96" fill="none" stroke="#9DB4CF" stroke-width="2" stroke-linecap="round"/>')
    parts.append(f'<circle cx="64" cy="86" r="6.5" fill="url(#rbChest)" stroke="{OUT}" stroke-width="2" filter="url(#rbGlow)"/>')
    # hlava
    h = [f'<g transform="translate(0,{head_dy})">']
    for ax, tipx in ((50, 43), (78, 85)):
        h.append(f'<path d="M{ax} 24 L{tipx} 9" stroke="{OUT}" stroke-width="5" stroke-linecap="round"/>'
                 f'<path d="M{ax} 24 L{tipx} 9" stroke="#C7D7EA" stroke-width="2.4" stroke-linecap="round"/>'
                 f'<circle cx="{tipx}" cy="8" r="4.8" fill="{PAL["cyan"]}" stroke="{OUT}" stroke-width="2.2" filter="url(#rbGlow)"/>')
    for ex in (30, 98):
        h.append(f'<circle cx="{ex}" cy="47" r="9" fill="url(#rbBlue)" stroke="{OUT}" stroke-width="{sw}"/>'
                 f'<circle cx="{ex}" cy="47" r="3.6" fill="{PAL["cyan_hi"]}"/>')
    h.append(f'<rect x="31" y="20" width="66" height="53" rx="25" fill="url(#rbMetal)" stroke="{OUT}" stroke-width="{sw}"/>')
    h.append('<path d="M40 31 Q50 23 66 23" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" opacity="0.9"/>')
    vx = 39 + look
    h.append(f'<rect x="{vx}" y="30" width="50" height="34" rx="15" fill="url(#rbVisor)" stroke="{OUT}" stroke-width="2"/>')
    h.append(f'<path d="M{vx + 6} 37 Q{vx + 14} 32 {vx + 26} 32" fill="none" stroke="#6E8FC4" stroke-width="2.2" stroke-linecap="round" opacity="0.7"/>')
    c = PAL["cyan"] if tint is None else tint
    lx, rx_, ey = 54 + look, 74 + look, 47
    if eyes == "open":
        for x in (lx, rx_):
            h.append(f'<ellipse cx="{x}" cy="{ey}" rx="6.5" ry="7.5" fill="{c}" filter="url(#rbGlow)"/>'
                     f'<circle cx="{x + 2}" cy="{ey - 3}" r="2" fill="#FFFFFF"/>')
    elif eyes == "blink":
        for x in (lx, rx_):
            h.append(f'<rect x="{x - 6.5}" y="{ey - 1.4}" width="13" height="2.8" rx="1.4" fill="{c}" filter="url(#rbGlow)"/>')
    elif eyes == "happy":
        for x in (lx, rx_):
            h.append(f'<path d="M{x - 6} {ey + 3} Q{x} {ey - 7} {x + 6} {ey + 3}" fill="none" stroke="{c}" stroke-width="4" stroke-linecap="round" filter="url(#rbGlow)"/>')
        h.append(f'<path d="M{58 + look} 56 Q{64 + look} 60 {70 + look} 56" fill="none" stroke="{c}" stroke-width="2.6" stroke-linecap="round"/>')
    elif eyes == "sad":
        for x in (lx, rx_):
            h.append(f'<path d="M{x - 6} {ey - 2} Q{x} {ey + 5} {x + 6} {ey - 2}" fill="none" stroke="{c}" stroke-width="4" stroke-linecap="round" filter="url(#rbGlow)"/>')
    elif eyes == "x":
        for x in (lx, rx_):
            h.append(f'<path d="M{x - 5} {ey - 5} L{x + 5} {ey + 5} M{x + 5} {ey - 5} L{x - 5} {ey + 5}" stroke="{c}" stroke-width="3.6" stroke-linecap="round" filter="url(#rbGlow)"/>')
    h.append("</g>")
    parts.append("".join(h))
    body = "".join(parts)
    k = 0.88  # rezerva nad hlavou pre skok/zdvihnuté ruky
    tr = f'translate(0,{dy}) rotate({tilt} 64 121) translate(64 121) scale({sx * k} {sy * k}) translate(-64 -121)'
    return f'<g transform="{tr}">{body}</g>'


def shadow(cx=64, cy=122, rx=24, op=0.35):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="4.5" fill="#000814" opacity="{op}"/>'


ROBOT_ANIMS = {
    # názov: zoznam (parametre, šírka tieňa)
    "idle": [
        (dict(dy=0, arm_l=8, arm_r=8), 24),
        (dict(dy=-1, arm_l=10, arm_r=10, head_dy=-0.5), 23),
        (dict(dy=-2, arm_l=12, arm_r=12, head_dy=-1, eyes="blink"), 22),
        (dict(dy=-1, arm_l=10, arm_r=10, head_dy=-0.5), 23),
    ],
    "walk": [
        (dict(dy=0, look=5, tilt=4, arm_l=28, arm_r=-6, lift_l=0, lift_r=5, leg_r=-8), 24),
        (dict(dy=-2, look=5, tilt=4, arm_l=16, arm_r=4, lift_l=0, lift_r=2, head_dy=1), 22),
        (dict(dy=-1, look=5, tilt=4, arm_l=4, arm_r=16, lift_l=2, lift_r=0, head_dy=0.5), 23),
        (dict(dy=0, look=5, tilt=4, arm_l=-6, arm_r=28, lift_l=5, lift_r=0, leg_l=8), 24),
        (dict(dy=-2, look=5, tilt=4, arm_l=4, arm_r=16, lift_l=2, lift_r=0, head_dy=1), 22),
        (dict(dy=-1, look=5, tilt=4, arm_l=16, arm_r=4, lift_l=0, lift_r=2, head_dy=0.5), 23),
    ],
    "jump": [
        (dict(dy=4, sy=0.9, sx=1.06, arm_l=35, arm_r=35, eyes="blink"), 26),
        (dict(dy=-9, sy=1.06, sx=0.96, arm_l=150, arm_r=150, lift_l=3, lift_r=3), 16),
        (dict(dy=-14, arm_l=95, arm_r=95, lift_l=6, lift_r=6, leg_l=12, leg_r=-12, eyes="happy"), 12),
        (dict(dy=3, sy=0.92, sx=1.05, arm_l=45, arm_r=45), 26),
    ],
    "success": [
        (dict(dy=0, arm_l=10, arm_r=150, eyes="happy"), 24),
        (dict(dy=-6, arm_l=25, arm_r=170, eyes="happy", head_dy=-1), 20),
        (dict(dy=-8, arm_l=40, arm_r=140, eyes="happy", head_dy=-1, lift_l=2, lift_r=2), 18),
        (dict(dy=-4, arm_l=20, arm_r=165, eyes="happy"), 21),
    ],
    "hurt": [
        (dict(dy=0, tilt=-7, arm_l=40, arm_r=40, eyes="x", tint=PAL["red"], lift_r=3), 24),
        (dict(dy=1, tilt=5, arm_l=20, arm_r=55, eyes="sad", tint=PAL["orange"]), 24),
        (dict(dy=0, tilt=-2, arm_l=12, arm_r=12, eyes="sad"), 24),
    ],
}


def gen_robot():
    total_frames = 0
    for name, frames in ROBOT_ANIMS.items():
        n = len(frames)
        body = ""
        for i, (p, shw) in enumerate(frames):
            body += f'<g transform="translate({i * 128},0)">{shadow(rx=shw)}{robot(**p)}</g>'
            emit(f"sprites/robot/frames/robot_{name}_{i + 1:02d}.png", 128, 128,
                 shadow(rx=shw) + robot(**p), ROBOT_DEFS)
        emit(f"sprites/robot/robot_{name}_sheet.png", 128 * n, 128, body, ROBOT_DEFS)
        total_frames += n
    # Portrét do menu (ukazuje prstom hore ako na referencii) – 512 px
    portrait = shadow(rx=26, op=0.3) + robot(arm_l=12, arm_r=150, eyes="happy")
    emit("sprites/robot/robot_portrait.png", 512, 512,
         f'<g transform="scale(4)">{portrait}</g>', ROBOT_DEFS)
    emit("sprites/robot/robot_idle_large.png", 512, 512,
         f'<g transform="scale(4)">{shadow(rx=24)}{robot()}</g>', ROBOT_DEFS)
    # Ikona aplikácie
    head = f'<g transform="translate(-8,6) scale(1.14)">{robot()}</g>'
    icon = (f'<rect x="4" y="4" width="120" height="120" rx="28" fill="url(#icBg)" stroke="{PAL["cyan"]}" stroke-width="4"/>'
            f'<g clip-path="url(#icClip)">{head}</g>')
    defs = ROBOT_DEFS + lin("icBg", [(0, "#1B3B6B", 1), (1, PAL["bg_deep"], 1)]) + \
        '<clipPath id="icClip"><rect x="6" y="6" width="116" height="116" rx="26"/></clipPath>'
    emit("ui/app_icon.png", 256, 256, f'<g transform="scale(2)">{icon}</g>', defs)
    return total_frames


# ====================================================================== PREKÁŽKY
def block_defs(id_, color):
    return (lin(id_, [(0, shade(color, 0.35), 1), (0.5, color, 1), (1, shade(color, -0.35), 1)])
            + glow(id_ + "G", 3))


def glossy_shape(d, id_, color, extra=""):
    return (f'<path d="{d}" fill="#000814" opacity="0.35" transform="translate(3,5)"/>'
            f'<path d="{d}" fill="url(#{id_})" stroke="{shade(color, -0.55)}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{shade(color, 0.6)}" stroke-width="2" stroke-linejoin="round" opacity="0.7" transform="translate(0,1.5) scale(0.985)"/>{extra}')


def poly_from_cells(cells, u, ox, oy):
    """Obrys tetromina z mriežkových buniek (pre L tvar)."""
    edges = {}
    for (cx, cy) in cells:
        pts = [(cx, cy), (cx + 1, cy), (cx + 1, cy + 1), (cx, cy + 1)]
        for k in range(4):
            a, b = pts[k], pts[(k + 1) % 4]
            if (b, a) in edges:
                del edges[(b, a)]
            else:
                edges[(a, b)] = True
    nxt = {a: b for (a, b) in edges}
    start = min(nxt)
    path, cur = [start], nxt[start]
    while cur != start:
        path.append(cur)
        cur = nxt[cur]
    return "M" + " L".join(f"{ox + x * u} {oy + y * u}" for x, y in path) + " Z"


def gen_obstacles():
    s = 128
    # Plus
    d = "M48 14 H80 V48 H114 V80 H80 V114 H48 V80 H14 V48 H48 Z"
    emit("sprites/obstacles/obstacle_plus.png", s, s, glossy_shape(d, "obP", PAL["red"]) +
         '<path d="M54 22 H74" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" opacity="0.6"/>',
         block_defs("obP", PAL["red"]))
    # Mínus
    d = "M14 46 H114 V82 H14 Z"
    emit("sprites/obstacles/obstacle_minus.png", s, s,
         glossy_shape("M20 46 H108 Q114 46 114 52 V76 Q114 82 108 82 H20 Q14 82 14 76 V52 Q14 46 20 46 Z", "obM", "#2E8BFF") +
         '<path d="M26 54 H96" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" opacity="0.55"/>',
         block_defs("obM", "#2E8BFF"))
    # L tvar – 4 rotácie
    base = [(0, 0), (0, 1), (0, 2), (1, 2)]
    for rot in (0, 90, 180, 270):
        cells = base
        for _ in range(rot // 90):
            cells = [(2 - y, x) for (x, y) in cells]  # rotácia v mriežke 3×3
        minx = min(c[0] for c in cells); miny = min(c[1] for c in cells)
        cells = [(x - minx, y - miny) for x, y in cells]
        w = max(c[0] for c in cells) + 1; h = max(c[1] for c in cells) + 1
        u = 34
        ox, oy = (s - w * u) / 2, (s - h * u) / 2
        d = poly_from_cells(cells, u, ox, oy)
        emit(f"sprites/obstacles/obstacle_L_{rot:03d}.png", s, s, glossy_shape(d, "obL", PAL["orange"]),
             block_defs("obL", PAL["orange"]))
    # Energetická bariéra (červený blok z ukážky hry)
    emit("sprites/obstacles/obstacle_barrier.png", s, 64,
         '<rect x="10" y="12" width="108" height="40" rx="10" fill="#000814" opacity="0.35" transform="translate(2,4)"/>'
         f'<rect x="10" y="12" width="108" height="40" rx="10" fill="url(#obB)" stroke="{shade(PAL["red"], -0.55)}" stroke-width="4"/>'
         '<path d="M24 22 H104" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" opacity="0.5"/>'
         + "".join(f'<path d="M{30 + i * 18} 46 l10 -16" stroke="{shade(PAL["red"], -0.4)}" stroke-width="5" stroke-linecap="round"/>' for i in range(4)),
         block_defs("obB", PAL["red"]))
    # Meteorit (Planéta PREKÁŽKY)
    rnd = random.Random(7)
    pts = []
    for i in range(14):
        a = i / 14 * math.tau
        r = 44 + rnd.uniform(-6, 5)
        pts.append(f"{64 + r * math.cos(a):.1f} {66 + r * math.sin(a):.1f}")
    d = "M" + " L".join(pts) + " Z"
    craters = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#4A3426" stroke="#2A1C14" stroke-width="2"/>'
        f'<path d="M{x - r * 0.7} {y - r * 0.2} A{r} {r} 0 0 1 {x + r * 0.6} {y - r * 0.5}" stroke="#8A6A52" stroke-width="2" fill="none"/>'
        for x, y, r in ((50, 56, 10), (80, 78, 8), (78, 46, 6), (52, 88, 5)))
    emit("sprites/obstacles/obstacle_meteor.png", s, s,
         f'<path d="{d}" fill="#000814" opacity="0.35" transform="translate(3,5)"/>'
         f'<path d="{d}" fill="url(#meR)" stroke="#2A1C14" stroke-width="4" stroke-linejoin="round"/>{craters}',
         rad("meR", [(0, "#B48A68", 1), (0.6, "#7A5640", 1), (1, "#3E2A1E", 1)], cx=0.38, cy=0.35, r=0.7))


# ====================================================================== KRYŠTÁLY A BONUSY
def gem(color, id_):
    c1, c2, c3 = shade(color, 0.55), color, shade(color, -0.45)
    defs = lin(id_, [(0, c1, 1), (0.5, c2, 1), (1, c3, 1)], 0, 0, 1, 1) + glow(id_ + "G", 4)
    body = (f'<g filter="url(#{id_}G)">'
            f'<path d="M64 8 L100 48 L64 120 L28 48 Z" fill="url(#{id_})" stroke="{shade(color, -0.6)}" stroke-width="4" stroke-linejoin="round"/></g>'
            f'<path d="M28 48 L100 48 M64 8 L52 48 L64 120 M64 8 L76 48 L64 120" fill="none" stroke="{c1}" stroke-width="2" opacity="0.8"/>'
            f'<path d="M64 8 L52 48 L28 48 Z" fill="#FFFFFF" opacity="0.35"/>')
    return body, defs


def star_path(cx, cy, r1, r2, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(rot + i * 180 / n)
        pts.append(f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


HEART = "M64 112 C30 88 10 66 10 42 C10 22 26 10 42 10 C52 10 60 16 64 24 C68 16 76 10 86 10 C102 10 118 22 118 42 C118 66 98 88 64 112 Z"


def gen_items():
    s = 128
    b, d = gem(PAL["green"], "gmG")
    emit("sprites/items/item_crystal_energy.png", s, s, b, d)
    # Bonus – fialový osemhranný drahokam
    defs = lin("gmP", [(0, "#E4D4FF", 1), (0.5, PAL["purple"], 1), (1, "#4B2A9E", 1)], 0, 0, 1, 1) + glow("gmPG", 5)
    body = ('<g filter="url(#gmPG)"><path d="M64 6 L104 34 L104 94 L64 122 L24 94 L24 34 Z" fill="url(#gmP)" stroke="#2E1766" stroke-width="4" stroke-linejoin="round"/></g>'
            '<path d="M64 6 L64 122 M24 34 L104 94 M104 34 L24 94" stroke="#E4D4FF" stroke-width="2" opacity="0.55"/>'
            '<path d="M64 6 L104 34 L64 50 L24 34 Z" fill="#FFFFFF" opacity="0.3"/>')
    emit("sprites/items/item_bonus_gem.png", s, s, body, defs)
    # Hviezda
    defs = rad("stY", [(0, "#FFF6C2", 1), (0.6, PAL["yellow"], 1), (1, "#E09A12", 1)], cx=0.4, cy=0.35, r=0.7) + glow("stG", 3)
    body = (f'<path d="{star_path(64, 68, 56, 24)}" fill="#000814" opacity="0.3" transform="translate(2,4)"/>'
            f'<path d="{star_path(64, 66, 56, 24)}" fill="url(#stY)" stroke="#8A5A00" stroke-width="4" stroke-linejoin="round" filter="url(#stG)"/>'
            f'<path d="{star_path(64, 66, 34, 14)}" fill="#FFFFFF" opacity="0.25"/>')
    emit("sprites/items/item_star.png", s, s, body, defs)
    # Batéria
    defs = lin("btB", [(0, "#8FD0FF", 1), (0.5, "#2E8BFF", 1), (1, "#164C9E", 1)], 0, 0, 1, 0)
    body = ('<rect x="38" y="18" width="52" height="98" rx="12" fill="#000814" opacity="0.3" transform="translate(3,4)"/>'
            '<rect x="52" y="8" width="24" height="14" rx="4" fill="#BFD4EA" stroke="#0B2A55" stroke-width="4"/>'
            '<rect x="38" y="18" width="52" height="98" rx="12" fill="url(#btB)" stroke="#0B2A55" stroke-width="4"/>'
            '<rect x="46" y="62" width="36" height="46" rx="6" fill="#9FF5F0" opacity="0.85"/>'
            '<path d="M68 30 L54 56 H66 L60 78 L76 50 H64 Z" fill="#FFFFFF" stroke="#0B2A55" stroke-width="2.5" stroke-linejoin="round"/>'
            '<path d="M46 26 V100" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" opacity="0.45"/>')
    emit("sprites/items/item_battery.png", s, s, body, defs)
    # Srdce (život)
    defs = rad("hrR", [(0, "#FFB3BA", 1), (0.55, PAL["red"], 1), (1, "#A3202E", 1)], cx=0.35, cy=0.3, r=0.75)
    body = (f'<path d="{HEART}" fill="#000814" opacity="0.3" transform="translate(2,4)"/>'
            f'<path d="{HEART}" fill="url(#hrR)" stroke="#5E0D17" stroke-width="4"/>'
            '<path d="M30 34 Q34 22 46 22" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" fill="none" opacity="0.7"/>')
    emit("sprites/items/item_heart.png", s, s, body, defs)


# ====================================================================== UI
def button(w, h, color, state):
    top, mid, bot = shade(color, 0.35), color, shade(color, -0.3)
    if state == "hover":
        top, mid, bot = shade(color, 0.5), shade(color, 0.15), shade(color, -0.15)
    if state == "pressed":
        top, mid, bot = shade(color, -0.1), shade(color, -0.2), shade(color, -0.35)
    if state == "disabled":
        top, mid, bot = "#5F6F82", "#4A586A", "#3A4554"
    stroke = shade(color, -0.6) if state != "disabled" else "#252E3A"
    off = 4 if state == "pressed" else 0
    r = min(16, h / 3)
    defs = lin("bt", [(0, top, 1), (0.5, mid, 1), (1, bot, 1)])
    body = ""
    if state != "pressed":
        body += f'<rect x="3" y="7" width="{w - 6}" height="{h - 10}" rx="{r}" fill="{shade(color, -0.65) if state != "disabled" else "#1C232C"}"/>'
    body += (f'<rect x="3" y="{3 + off}" width="{w - 6}" height="{h - 10}" rx="{r}" fill="url(#bt)" stroke="{stroke}" stroke-width="3"/>'
             f'<rect x="{r}" y="{8 + off}" width="{w - 2 * r}" height="{(h - 10) * 0.22:.1f}" rx="{(h - 10) * 0.11:.1f}" fill="#FFFFFF" opacity="{0.35 if state != "disabled" else 0.12}"/>')
    return body, defs


def gen_ui():
    colors = {"green": PAL["green"], "blue": "#2E8BFF", "red": PAL["red"], "cyan": PAL["cyan"],
              "orange": PAL["orange"], "dark": PAL["panel_dark"]}
    for name, col in colors.items():
        for st in ("normal", "hover", "pressed", "disabled"):
            if name not in ("green", "blue", "red") and st == "disabled":
                continue
            b, d = button(192, 64, col, st)
            emit(f"ui/buttons/button_{name}_{st}.png", 192, 64, b, d)
    # Štvorcové tlačidlo odpovede (číslo) a ikonové tlačidlo
    for name, col in (("blue", "#2E8BFF"), ("green", PAL["green"]), ("red", PAL["red"])):
        for st in ("normal", "hover", "pressed"):
            b, d = button(96, 96, col, st)
            emit(f"ui/buttons/button_square_{name}_{st}.png", 96, 96, b, d)
    # Panel (9-slice: okraj 24 px)
    defs = lin("pn", [(0, "#173A63", 0.96), (1, "#0D2240", 0.96)])
    emit("ui/panels/panel.png", 128, 128,
         f'<rect x="3" y="3" width="122" height="122" rx="18" fill="url(#pn)" stroke="{PAL["cyan"]}" stroke-width="3" stroke-opacity="0.75"/>'
         '<rect x="9" y="9" width="110" height="110" rx="13" fill="none" stroke="#FFFFFF" stroke-width="1" stroke-opacity="0.12"/>', defs)
    emit("ui/panels/panel_header.png", 256, 128,
         f'<rect x="3" y="3" width="250" height="122" rx="18" fill="url(#pn)" stroke="{PAL["cyan"]}" stroke-width="3" stroke-opacity="0.75"/>'
         f'<path d="M3 40 V21 Q3 3 21 3 H235 Q253 3 253 21 V40 Z" fill="{PAL["panel"]}" opacity="0.9"/>'
         f'<path d="M3 40 H253" stroke="{PAL["cyan"]}" stroke-width="2" stroke-opacity="0.6"/>', defs)
    emit("ui/panels/panel_dark.png", 128, 128,
         f'<rect x="3" y="3" width="122" height="122" rx="18" fill="{PAL["bg_deep"]}" fill-opacity="0.88" stroke="#3B5A80" stroke-width="3"/>')
    emit("ui/panels/panel_highlight.png", 128, 128,
         f'<rect x="4" y="4" width="120" height="120" rx="18" fill="{PAL["cyan"]}" fill-opacity="0.12" stroke="{PAL["cyan"]}" stroke-width="4"/>', "")
    # Bublina reči
    emit("ui/panels/speech_bubble.png", 256, 160,
         '<path d="M24 8 H232 Q248 8 248 24 V104 Q248 120 232 120 H90 L56 150 L62 120 H24 Q8 120 8 104 V24 Q8 8 24 8 Z" fill="#000814" opacity="0.3" transform="translate(2,4)"/>'
         '<path d="M24 8 H232 Q248 8 248 24 V104 Q248 120 232 120 H90 L56 150 L62 120 H24 Q8 120 8 104 V24 Q8 8 24 8 Z" fill="#FFFFFF" stroke="#2E8BFF" stroke-width="4" stroke-linejoin="round"/>')
    # Karta planéty pre výber úrovne
    emit("ui/panels/level_card.png", 256, 96,
         f'<rect x="3" y="3" width="250" height="90" rx="14" fill="url(#pn)" stroke="{PAL["cyan"]}" stroke-width="3" stroke-opacity="0.7"/>', defs)
    emit("ui/panels/level_card_locked.png", 256, 96,
         '<rect x="3" y="3" width="250" height="90" rx="14" fill="#172638" stroke="#526477" stroke-width="3"/>')
    # HUD – energia
    emit("ui/hud/bar_frame.png", 256, 32,
         '<rect x="2" y="2" width="252" height="28" rx="14" fill="#0A1628" stroke="#3B5A80" stroke-width="3"/>')
    for name, col in (("green", PAL["green"]), ("cyan", PAL["cyan"]), ("orange", PAL["orange"]), ("red", PAL["red"])):
        emit(f"ui/hud/bar_fill_{name}.png", 64, 24,
             f'<rect x="0" y="0" width="64" height="24" rx="12" fill="url(#bf)"/>'
             '<rect x="8" y="4" width="48" height="5" rx="2.5" fill="#FFFFFF" opacity="0.45"/>',
             lin("bf", [(0, shade(col, 0.35), 1), (1, shade(col, -0.25), 1)]))
    # Prázdne srdce / prázdna hviezda (HUD)
    emit("ui/hud/heart_empty.png", 128, 128,
         f'<path d="{HEART}" fill="#1A2638" stroke="#4E6380" stroke-width="5" stroke-dasharray="0"/>')
    emit("ui/hud/star_empty.png", 128, 128,
         f'<path d="{star_path(64, 66, 56, 24)}" fill="#1A2638" stroke="#4E6380" stroke-width="5" stroke-linejoin="round"/>')


# ====================================================================== IKONY
def gear(cx, cy, r_out, r_in, teeth=8):
    pts = []
    for i in range(teeth * 4):
        a = i / (teeth * 4) * math.tau
        r = r_out if (i % 4) in (1, 2) else r_in
        pts.append(f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


ICONS = {
    "home": '<path d="M14 58 L64 16 L114 58" fill="none" stroke="W" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="M28 56 V110 H54 V80 H74 V110 H100 V56" fill="none" stroke="W" stroke-width="12" stroke-linejoin="round"/>',
    "settings": f'<path d="{gear(64, 64, 52, 40)}" fill="W" stroke="W" stroke-width="4" stroke-linejoin="round"/><circle cx="64" cy="64" r="17" fill="BG"/>',
    "trophy": '<path d="M34 14 H94 V44 Q94 78 64 82 Q34 78 34 44 Z" fill="W"/>'
              '<path d="M34 26 H16 Q14 56 40 60 M94 26 H112 Q114 56 88 60" fill="none" stroke="W" stroke-width="9" stroke-linecap="round"/>'
              '<rect x="56" y="80" width="16" height="18" fill="W"/><rect x="34" y="98" width="60" height="16" rx="5" fill="W"/>',
    "book": '<path d="M64 30 Q42 16 12 20 V104 Q42 100 64 114 Q86 100 116 104 V20 Q86 16 64 30 Z" fill="W"/>'
            '<path d="M64 32 V110" stroke="BG" stroke-width="6"/>'
            '<path d="M24 40 Q40 38 52 44 M24 58 Q40 56 52 62 M76 44 Q88 38 104 40 M76 62 Q88 56 104 58" stroke="BG" stroke-width="5" stroke-linecap="round" fill="none"/>',
    "music": '<path d="M48 92 V26 L108 14 V80" fill="none" stroke="W" stroke-width="10" stroke-linejoin="round"/>'
             '<ellipse cx="34" cy="94" rx="18" ry="14" fill="W"/><ellipse cx="94" cy="82" rx="18" ry="14" fill="W"/>',
    "sound_on": '<path d="M14 48 H38 L66 22 V106 L38 80 H14 Z" fill="W" stroke="W" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M82 44 Q94 64 82 84 M96 30 Q118 64 96 98" fill="none" stroke="W" stroke-width="9" stroke-linecap="round"/>',
    "sound_off": '<path d="M14 48 H38 L66 22 V106 L38 80 H14 Z" fill="W" stroke="W" stroke-width="6" stroke-linejoin="round"/>'
                 '<path d="M84 46 L114 82 M114 46 L84 82" stroke="R" stroke-width="10" stroke-linecap="round"/>',
    "pause": '<rect x="30" y="20" width="24" height="88" rx="8" fill="W"/><rect x="74" y="20" width="24" height="88" rx="8" fill="W"/>',
    "play": '<path d="M36 18 L108 64 L36 110 Z" fill="W" stroke="W" stroke-width="8" stroke-linejoin="round"/>',
    "lock": '<path d="M38 58 V42 Q38 16 64 16 Q90 16 90 42 V58" fill="none" stroke="W" stroke-width="11"/>'
            '<rect x="24" y="56" width="80" height="58" rx="12" fill="W"/><circle cx="64" cy="80" r="8" fill="BG"/><rect x="60" y="82" width="8" height="18" rx="3" fill="BG"/>',
    "back": '<path d="M58 22 L16 64 L58 106 M18 64 H112" fill="none" stroke="W" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>',
    "retry": '<path d="M98 40 A40 40 0 1 0 104 76" fill="none" stroke="W" stroke-width="12" stroke-linecap="round"/>'
             '<path d="M106 12 V46 H72" fill="none" stroke="W" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>',
    "hint": '<path d="M64 10 Q100 10 100 46 Q100 64 84 78 V90 H44 V78 Q28 64 28 46 Q28 10 64 10 Z" fill="W"/>'
            '<rect x="44" y="96" width="40" height="10" rx="5" fill="W"/><rect x="50" y="110" width="28" height="9" rx="4.5" fill="W"/>'
            '<path d="M52 44 Q64 30 76 44" stroke="BG" stroke-width="5" fill="none" stroke-linecap="round"/>',
    "check": '<path d="M18 66 L50 98 L112 30" fill="none" stroke="G" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>',
    "close": '<path d="M26 26 L102 102 M102 26 L26 102" stroke="R" stroke-width="16" stroke-linecap="round"/>',
    "help": '<circle cx="64" cy="64" r="52" fill="none" stroke="W" stroke-width="10"/>'
            '<path d="M44 50 Q44 30 64 30 Q84 30 84 48 Q84 60 70 66 Q64 70 64 80" fill="none" stroke="W" stroke-width="11" stroke-linecap="round"/>'
            '<circle cx="64" cy="98" r="7" fill="W"/>',
    "star": f'<path d="{star_path(64, 66, 54, 23)}" fill="Y" stroke="Y" stroke-width="4" stroke-linejoin="round"/>',
    "map": '<path d="M12 28 L46 16 L82 30 L116 18 V100 L82 112 L46 98 L12 110 Z" fill="W"/>'
           '<path d="M46 16 V98 M82 30 V112" stroke="BG" stroke-width="5"/>',
    "exit": '<path d="M70 18 H30 Q22 18 22 26 V102 Q22 110 30 110 H70" fill="none" stroke="W" stroke-width="11" stroke-linecap="round"/>'
            '<path d="M56 64 H112 M92 42 L114 64 L92 86" fill="none" stroke="W" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>',
}


def gen_icons():
    for name, tpl in ICONS.items():
        for variant, wcol in (("", "#FFFFFF"), ("_cyan", PAL["cyan"])):
            g = (tpl.replace('"W"', f'"{wcol}"').replace('"BG"', f'"{PAL["panel_dark"]}"')
                 .replace('"R"', f'"{PAL["red"]}"').replace('"G"', f'"{PAL["green"]}"').replace('"Y"', f'"{PAL["yellow"]}"'))
            shadow_g = (tpl.replace('"W"', '"#000814"').replace('"BG"', '"#000814"').replace('"R"', '"#000814"')
                        .replace('"G"', '"#000814"').replace('"Y"', '"#000814"'))
            body = f'<g opacity="0.35" transform="translate(2,4)">{shadow_g}</g>{g}'
            emit(f"ui/icons/icon_{name}{variant}.png", 128, 128, body)


# ====================================================================== ČÍSELNÁ OS
def gen_numberline():
    emit("ui/numberline/axis_tile.png", 64, 16,
         '<rect x="0" y="4" width="64" height="8" fill="#FFFFFF"/><rect x="0" y="4" width="64" height="2.5" fill="#BFE9FF"/><rect x="0" y="10" width="64" height="2" fill="#6C8DB5"/>')
    emit("ui/numberline/tick_major.png", 8, 40, '<rect x="1" y="0" width="6" height="40" rx="3" fill="#FFFFFF"/>')
    emit("ui/numberline/tick_minor.png", 6, 24, '<rect x="1" y="0" width="4" height="24" rx="2" fill="#C9DAEE"/>')
    emit("ui/numberline/tick_zero.png", 12, 52,
         f'<rect x="2" y="0" width="8" height="52" rx="4" fill="{PAL["yellow"]}" stroke="{OUT}" stroke-width="1.5"/>')
    emit("ui/numberline/arrow_end.png", 40, 40, '<path d="M4 6 L36 20 L4 34 L12 20 Z" fill="#FFFFFF"/>')
    for name, col in (("start", "#2E8BFF"), ("goal", PAL["green"]), ("wrong", PAL["red"]), ("current", PAL["cyan"])):
        emit(f"ui/numberline/marker_{name}.png", 64, 64,
             f'<circle cx="32" cy="32" r="28" fill="{col}" opacity="0.25" filter="url(#mg)"/>'
             f'<circle cx="32" cy="32" r="18" fill="url(#mk)" stroke="{OUT}" stroke-width="3"/>'
             '<circle cx="27" cy="26" r="5" fill="#FFFFFF" opacity="0.6"/>',
             rad("mk", [(0, shade(col, 0.5), 1), (1, shade(col, -0.3), 1)], cx=0.4, cy=0.35) + blur("mg", 3))
    emit("ui/numberline/pointer_pin.png", 64, 80,
         f'<path d="M32 76 Q8 46 8 30 A24 24 0 0 1 56 30 Q56 46 32 76 Z" fill="url(#pp)" stroke="{OUT}" stroke-width="3"/>'
         '<circle cx="32" cy="30" r="10" fill="#FFFFFF"/><circle cx="32" cy="30" r="5" fill="#2E8BFF"/>',
         lin("pp", [(0, PAL["cyan_hi"], 1), (1, "#1B8FB8", 1)]))
    emit("ui/numberline/goal_flag.png", 64, 96,
         f'<rect x="12" y="8" width="6" height="84" rx="3" fill="#D7E4F3" stroke="{OUT}" stroke-width="2"/>'
         f'<path d="M18 10 H56 L46 26 L56 42 H18 Z" fill="{PAL["yellow"]}" stroke="{OUT}" stroke-width="3" stroke-linejoin="round"/>'
         '<ellipse cx="15" cy="92" rx="12" ry="4" fill="#000814" opacity="0.35"/>')
    emit("ui/numberline/target_cell.png", 64, 64,
         '<rect x="4" y="4" width="56" height="56" rx="8" fill="#1A4F8F" stroke="#5FB8FF" stroke-width="4"/>'
         '<circle cx="32" cy="32" r="14" fill="none" stroke="#FFFFFF" stroke-width="3"/>'
         '<path d="M32 10 V24 M32 40 V54 M10 32 H24 M40 32 H54" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>')
    emit("ui/numberline/move_arrow.png", 128, 32,
         f'<path d="M4 12 H96 V4 L124 16 L96 28 V20 H4 Z" fill="{PAL["yellow"]}" stroke="{OUT}" stroke-width="2.5" stroke-linejoin="round"/>')
    emit("ui/numberline/jump_arc.png", 256, 96,
         f'<path d="M12 84 Q128 -20 244 84" fill="none" stroke="{PAL["yellow"]}" stroke-width="5" stroke-dasharray="12 9" stroke-linecap="round"/>'
         f'<path d="M232 66 L246 88 L222 84" fill="none" stroke="{PAL["yellow"]}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')


# ====================================================================== EFEKTY (sprite sheety 6 snímok)
def gen_effects():
    n, s = 6, 128
    for name, col in (("success", PAL["green"]), ("error", PAL["red"]), ("crystal", PAL["cyan"])):
        defs = glow("fxG", 3) + rad("fxR", [(0, "#FFFFFF", 1), (0.35, col, 0.9), (1, col, 0)])
        body = ""
        for i in range(n):
            t = (i + 1) / n
            alpha = 1.0 if t < 0.6 else max(0.0, 1 - (t - 0.6) / 0.4)
            g = f'<g transform="translate({i * s},0)" opacity="{alpha:.2f}">'
            g += f'<circle cx="64" cy="64" r="{14 + 40 * t:.1f}" fill="url(#fxR)" opacity="{0.9 - 0.5 * t:.2f}"/>'
            g += f'<circle cx="64" cy="64" r="{12 + 46 * t:.1f}" fill="none" stroke="{col}" stroke-width="{6 * (1 - t) + 1:.1f}" filter="url(#fxG)"/>'
            rays = 8
            for k in range(rays):
                a = k / rays * math.tau + (0.39 if name == "crystal" else 0)
                r1, r2 = 10 + 30 * t, 22 + 38 * t
                g += (f'<path d="M{64 + r1 * math.cos(a):.1f} {64 + r1 * math.sin(a):.1f} L{64 + r2 * math.cos(a):.1f} {64 + r2 * math.sin(a):.1f}" '
                      f'stroke="{shade(col, 0.4)}" stroke-width="{5 * (1 - t) + 1.5:.1f}" stroke-linecap="round"/>')
            if name == "crystal":
                g += f'<path d="{star_path(64, 64, 26 * (1 - t * 0.6), 6, 4, -90)}" fill="#FFFFFF" filter="url(#fxG)"/>'
            elif name == "error":
                k = 18 * (1 - t * 0.5)
                g += f'<path d="M{64 - k} {64 - k} L{64 + k} {64 + k} M{64 + k} {64 - k} L{64 - k} {64 + k}" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round"/>'
            else:
                g += f'<path d="{star_path(64, 64, 22 * (1 - t * 0.5), 9)}" fill="#FFFFFF" filter="url(#fxG)"/>'
            body += g + "</g>"
        emit(f"effects/fx_{name}_sheet.png", s * n, s, body, defs)
    # Portál – rotujúci vír
    defs = rad("ptR", [(0, "#FFFFFF", 1), (0.25, "#D8C4FF", 1), (0.6, PAL["purple"], 0.9), (1, "#2E1766", 0)]) + glow("ptG", 3)
    body = ""
    for i in range(n):
        g = f'<g transform="translate({i * s},0)"><circle cx="64" cy="64" r="54" fill="url(#ptR)"/>'
        for k in range(3):
            rot = i * 20 + k * 120
            g += (f'<path d="M64 64 m0 -46 a46 46 0 0 1 40 24" fill="none" stroke="#E4D4FF" stroke-width="5" stroke-linecap="round" '
                  f'transform="rotate({rot} 64 64)" filter="url(#ptG)" opacity="0.85"/>')
            g += (f'<path d="M64 64 m0 -28 a28 28 0 0 1 24 14" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" '
                  f'transform="rotate({-rot * 1.4 + 60} 64 64)" opacity="0.8"/>')
        body += g + "</g>"
    emit("effects/fx_portal_sheet.png", s * n, s, body, defs)
    # Hviezdičky (oslava)
    rnd = random.Random(3)
    sparks = [(rnd.uniform(0, math.tau), rnd.uniform(0.5, 1.0), rnd.choice([PAL["yellow"], "#FFFFFF", PAL["orange"]])) for _ in range(9)]
    body = ""
    for i in range(n):
        t = (i + 1) / n
        g = f'<g transform="translate({i * s},0)" opacity="{1 if t < 0.7 else (1 - t) / 0.3:.2f}">'
        for a, sp, col in sparks:
            r = 52 * t * sp
            x, y = 64 + r * math.cos(a), 64 + r * math.sin(a) + 10 * t * t
            g += f'<path d="{star_path(x, y, 11 * (1 - 0.4 * t), 4.5)}" fill="{col}" stroke="#8A5A00" stroke-width="1.2"/>'
        body += g + "</g>"
    emit("effects/fx_stars_sheet.png", s * n, s, body)
    # Statické verzie (1 snímka) – pre jednoduché použitie ako Sprite2D
    for name, col in (("success", PAL["green"]), ("error", PAL["red"]), ("crystal", PAL["cyan"]), ("portal", PAL["purple"])):
        emit(f"effects/fx_{name}.png", s, s,
             f'<circle cx="64" cy="64" r="50" fill="url(#st)"/>'
             f'<path d="{star_path(64, 64, 46, 8, 4)}" fill="{shade(col, 0.3)}" opacity="0.9" filter="url(#sg)"/>'
             f'<path d="{star_path(64, 64, 30, 6, 4, -45)}" fill="#FFFFFF" opacity="0.9" filter="url(#sg)"/>'
             '<circle cx="64" cy="64" r="9" fill="#FFFFFF"/>',
             rad("st", [(0, "#FFFFFF", 0.95), (0.3, col, 0.8), (1, col, 0)]) + glow("sg", 3))


# ====================================================================== PLANÉTY (mapa úrovní)
PLANETS = [
    # (súbor, hlavná farba, tmavá, symbol, typ povrchu)
    ("01_plus", "#3FBF5A", "#1E5E3A", "plus", "continents"),
    ("02_minus", "#5AB4F0", "#1B4C8A", "minus", "ice"),
    ("03_nula", "#9A6BE8", "#3E2478", "zero", "craters"),
    ("04_zrkadlo", "#F2B233", "#9A5A10", "abs", "bands"),
    ("05_rovnice", "#E5484D", "#7A1A24", "equals", "lava"),
    ("06_porovnanie", "#2FC7B6", "#126B66", "compare", "bands"),
    ("07_desatinna", "#FF8C42", "#8F3A12", "half", "craters"),
    ("08_dvojkrok", "#E063C8", "#6B1E66", "twostep", "bands"),
    ("09_prekazky", "#A57C5A", "#4A3222", "meteor", "craters"),
    ("10_boss", "#B0263A", "#3A0A14", "boss", "lava"),
]


def planet_symbol(kind):
    W = "#FFFFFF"
    st = f'stroke="{OUT}" stroke-width="6" stroke-linejoin="round" paint-order="stroke"'
    if kind == "plus":
        return f'<path d="M110 70 H146 V110 H186 V146 H146 V186 H110 V146 H70 V110 H110 Z" fill="#E9FFE9" {st}/>'
    if kind == "minus":
        return f'<rect x="64" y="108" width="128" height="40" rx="12" fill="#BFE9FF" {st}/>'
    if kind == "zero":
        return f'<ellipse cx="128" cy="128" rx="40" ry="54" fill="none" stroke="{OUT}" stroke-width="30"/><ellipse cx="128" cy="128" rx="40" ry="54" fill="none" stroke="{W}" stroke-width="18"/>'
    if kind == "abs":
        return f'<rect x="88" y="66" width="26" height="124" rx="8" fill="{W}" {st}/><rect x="142" y="66" width="26" height="124" rx="8" fill="{W}" {st}/>'
    if kind == "equals":
        return f'<rect x="70" y="92" width="116" height="30" rx="10" fill="{W}" {st}/><rect x="70" y="136" width="116" height="30" rx="10" fill="{W}" {st}/>'
    if kind == "compare":
        return (f'<path d="M110 86 L70 128 L110 170" fill="none" stroke="{OUT}" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M110 86 L70 128 L110 170" fill="none" stroke="{W}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M146 86 L186 128 L146 170" fill="none" stroke="{OUT}" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M146 86 L186 128 L146 170" fill="none" stroke="{W}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "half":
        return (f'<text x="128" y="160" text-anchor="middle" font-family="Avenir Next" font-weight="800" font-size="96" fill="{W}" '
                f'stroke="{OUT}" stroke-width="8" paint-order="stroke">0,5</text>')
    if kind == "twostep":
        return (f'<path d="M78 90 L114 128 L78 166 M128 90 L164 128 L128 166" fill="none" stroke="{OUT}" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M78 90 L114 128 L78 166 M128 90 L164 128 L128 166" fill="none" stroke="{PAL["yellow"]}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "meteor":
        return (f'<path d="M60 70 L120 118" stroke="{PAL["orange"]}" stroke-width="18" stroke-linecap="round" opacity="0.8"/>'
                f'<circle cx="138" cy="134" r="34" fill="#6B4A34" {st}/><circle cx="128" cy="124" r="8" fill="#3E2A1E"/><circle cx="150" cy="146" r="6" fill="#3E2A1E"/>')
    if kind == "boss":
        return (f'<path d="M78 186 V110 L92 96 V78 H104 V96 H120 V70 H136 V96 H152 V78 H164 V96 L178 110 V186 Z" fill="#1A0A12" stroke="{OUT}" stroke-width="4"/>'
                f'<path d="M104 128 L116 136 M152 128 L140 136" stroke="#FF3B3B" stroke-width="7" stroke-linecap="round" filter="url(#plG)"/>'
                f'<path d="M116 186 V160 Q128 148 140 160 V186 Z" fill="#FF3B3B" opacity="0.85" filter="url(#plG)"/>')
    return ""


def planet_surface(kind, main, dark, rnd):
    s = ""
    if kind == "continents":
        for _ in range(6):
            x, y, r = rnd.uniform(60, 200), rnd.uniform(60, 200), rnd.uniform(18, 34)
            s += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.0f}" ry="{r * 0.7:.0f}" fill="{shade(main, -0.35)}" opacity="0.8" transform="rotate({rnd.uniform(0, 180):.0f} {x:.0f} {y:.0f})"/>'
    elif kind == "ice":
        for _ in range(9):
            x, y = rnd.uniform(40, 210), rnd.uniform(40, 210)
            s += f'<path d="M{x:.0f} {y:.0f} l{rnd.uniform(-30, 30):.0f} {rnd.uniform(-20, 20):.0f}" stroke="#E8F7FF" stroke-width="3" opacity="0.6"/>'
    elif kind == "craters":
        for _ in range(8):
            x, y, r = rnd.uniform(50, 205), rnd.uniform(50, 205), rnd.uniform(6, 18)
            s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{shade(main, -0.3)}" stroke="{shade(main, 0.25)}" stroke-width="2" opacity="0.85"/>'
    elif kind == "bands":
        for k in range(5):
            y = 50 + k * 38 + rnd.uniform(-6, 6)
            s += f'<path d="M20 {y:.0f} Q128 {y + rnd.uniform(-18, 18):.0f} 236 {y:.0f}" stroke="{shade(main, -0.3 if k % 2 else 0.25)}" stroke-width="{rnd.uniform(10, 20):.0f}" fill="none" opacity="0.6"/>'
    elif kind == "lava":
        for _ in range(7):
            x, y = rnd.uniform(40, 210), rnd.uniform(40, 210)
            s += f'<path d="M{x:.0f} {y:.0f} q{rnd.uniform(-30, 30):.0f} {rnd.uniform(-30, 30):.0f} {rnd.uniform(-40, 40):.0f} {rnd.uniform(-10, 30):.0f}" stroke="#FFB547" stroke-width="5" fill="none" opacity="0.8" stroke-linecap="round"/>'
    return s


def gen_planets():
    for i, (fname, main, dark, sym, surf) in enumerate(PLANETS):
        rnd = random.Random(100 + i)
        defs = (rad("plB", [(0, shade(main, 0.45), 1), (0.55, main, 1), (1, dark, 1)], cx=0.38, cy=0.34, r=0.72)
                + rad("plA", [(0.8, main, 0), (0.9, shade(main, 0.3), 0.55), (1, main, 0)])
                + rad("plS", [(0.5, "#000000", 0), (1, "#000000", 0.55)], cx=0.35, cy=0.3, r=0.8)
                + '<clipPath id="plC"><circle cx="128" cy="128" r="98"/></clipPath>' + glow("plG", 4))
        body = (f'<circle cx="128" cy="128" r="124" fill="url(#plA)"/>'
                f'<circle cx="128" cy="128" r="98" fill="url(#plB)"/>'
                f'<g clip-path="url(#plC)">{planet_surface(surf, main, dark, rnd)}<circle cx="128" cy="128" r="98" fill="url(#plS)"/></g>'
                f'<circle cx="128" cy="128" r="98" fill="none" stroke="{OUT}" stroke-width="4"/>'
                f'<path d="M64 84 Q80 50 118 40" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round" fill="none" opacity="0.45"/>'
                + planet_symbol(sym))
        if fname == "06_porovnanie" or fname == "08_dvojkrok":
            body = (f'<ellipse cx="128" cy="132" rx="124" ry="30" fill="none" stroke="{shade(main, 0.4)}" stroke-width="8" opacity="0.7" transform="rotate(-14 128 128)"/>' + body)
        emit(f"sprites/planets/planet_{fname}.png", 256, 256, body, defs)
    emit("sprites/planets/planet_locked.png", 256, 256,
         '<circle cx="128" cy="128" r="98" fill="url(#lk)" stroke="#0B1A33" stroke-width="4"/>'
         f'<g transform="translate(78,70) scale(0.78)">{ICONS["lock"].replace(chr(34) + "W" + chr(34), chr(34) + "#C9D6E6" + chr(34)).replace(chr(34) + "BG" + chr(34), chr(34) + "#3A4A5E" + chr(34))}</g>',
         rad("lk", [(0, "#6E7F94", 1), (1, "#2A3646", 1)], cx=0.38, cy=0.34, r=0.72))
    emit("sprites/planets/planet_path_dot.png", 16, 16, '<circle cx="8" cy="8" r="5" fill="#BFE9FF" opacity="0.85"/>')


# ====================================================================== POZADIA 1280×720
W_, H_ = 1280, 720


def starfield(rnd, n=170, w=W_, h=H_):
    s = ""
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * 0.85)
        r = rnd.choice([0.7, 0.9, 1.1, 1.4, 1.8])
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#FFFFFF" opacity="{rnd.uniform(0.35, 0.95):.2f}"/>'
    for _ in range(7):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * 0.6)
        s += f'<path d="{star_path(x, y, 7, 1.4, 4)}" fill="#FFFFFF" opacity="0.9"/>'
    return s


def nebula(rnd, colors, n=5):
    s = ""
    for k in range(n):
        x, y = rnd.uniform(0, W_), rnd.uniform(40, 420)
        rx, ry = rnd.uniform(220, 420), rnd.uniform(120, 220)
        s += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="{colors[k % len(colors)]}" opacity="{rnd.uniform(0.18, 0.35):.2f}" filter="url(#nb)"/>'
    return s


def hills(rnd, base_y, amp, color, seg=10, stroke=None):
    pts = [(0, base_y)]
    for i in range(1, seg + 1):
        pts.append((i * W_ / seg, base_y + rnd.uniform(-amp, amp)))
    d = f"M0 {H_} L0 {pts[0][1]:.0f}"
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        d += f" Q{(x0 + x1) / 2:.0f} {min(y0, y1) - amp * 0.6:.0f} {x1:.0f} {y1:.0f}"
    d += f" L{W_} {H_} Z"
    st = f' stroke="{stroke}" stroke-width="3"' if stroke else ""
    return f'<path d="{d}" fill="{color}"{st}/>'


def bg_planet(x, y, r, col, ring=False):
    s = f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#bp)"/>'
    s = s.replace("url(#bp)", f"url(#bp{col[1:]})")
    if ring:
        s = (f'<ellipse cx="{x}" cy="{y}" rx="{r * 1.8}" ry="{r * 0.4}" fill="none" stroke="{shade(col, 0.4)}" stroke-width="{r * 0.12:.0f}" opacity="0.6" transform="rotate(-12 {x} {y})"/>' + s)
    return s


def bg_planet_def(col):
    return rad(f"bp{col[1:]}", [(0, shade(col, 0.4), 1), (0.6, col, 1), (1, shade(col, -0.6), 1)], cx=0.35, cy=0.3, r=0.75)


def prop(kind, x, y, sc, rnd, lit=True):
    """Tematické objekty na zemi."""
    g = f'<g transform="translate({x},{y}) scale({sc})">'
    if kind == "solar":
        g += (f'<rect x="-4" y="-60" width="8" height="60" fill="#5C6E86"/>'
              f'<g transform="rotate(-18 0 -62)"><rect x="-60" y="-92" width="120" height="58" rx="4" fill="#163A73" stroke="#9DB4CF" stroke-width="4"/>'
              + "".join(f'<path d="M{-60 + k * 30} -92 V-34" stroke="#5FB8FF" stroke-width="2"/>' for k in range(1, 4))
              + '<path d="M-60 -63 H60" stroke="#5FB8FF" stroke-width="2"/>'
              + (f'<rect x="-60" y="-92" width="120" height="58" rx="4" fill="{PAL["cyan"]}" opacity="0.25"/>' if lit else "") + "</g>")
    elif kind == "ice":
        for k in range(3):
            h = rnd.uniform(60, 120); dx = (k - 1) * 30
            g += f'<path d="M{dx - 18} 0 L{dx} {-h:.0f} L{dx + 18} 0 Z" fill="#BFE9FF" stroke="#5AA8E0" stroke-width="3" opacity="0.92"/><path d="M{dx} {-h:.0f} L{dx + 6} 0" stroke="#FFFFFF" stroke-width="3" opacity="0.7"/>'
    elif kind == "crystal":
        for k, (dx, h, col) in enumerate(((-26, 70, "#B58CFF"), (0, 110, "#D8C4FF"), (24, 80, "#9B6BFF"))):
            g += f'<path d="M{dx - 14} 0 L{dx - 10} {-h * 0.8:.0f} L{dx} {-h} L{dx + 10} {-h * 0.8:.0f} L{dx + 14} 0 Z" fill="{col}" stroke="#4B2A9E" stroke-width="3" filter="url(#gl)"/>'
    elif kind == "tower":
        win = PAL["cyan"] if lit else "#2A3A50"
        g += (f'<path d="M-30 0 L-22 -200 L22 -200 L30 0 Z" fill="#1C2F4D" stroke="#36527A" stroke-width="3"/>'
              f'<ellipse cx="0" cy="-204" rx="46" ry="16" fill="#2B4A75" stroke="#5FB8FF" stroke-width="3"/>'
              f'<path d="M0 -220 V-260" stroke="#9DB4CF" stroke-width="4"/><circle cx="0" cy="-262" r="6" fill="{PAL["red"] if not lit else PAL["yellow"]}" filter="url(#gl)"/>'
              + "".join(f'<rect x="-10" y="{-180 + k * 34}" width="20" height="14" rx="3" fill="{win}" opacity="{0.9 if lit else 0.6}"/>' for k in range(5)))
    elif kind == "dome":
        g += (f'<path d="M-90 0 A90 80 0 0 1 90 0 Z" fill="url(#dm)" stroke="#5FB8FF" stroke-width="3"/>'
              f'<path d="M-60 -40 Q0 -90 60 -40" stroke="#FFFFFF" stroke-width="4" fill="none" opacity="0.35"/>'
              f'<rect x="-100" y="-6" width="200" height="12" rx="6" fill="#2B4A75"/>'
              + "".join(f'<circle cx="{-70 + k * 35}" cy="0" r="4" fill="{PAL["cyan"] if lit else "#304560"}"/>' for k in range(5)))
    elif kind == "pylon":
        col = PAL["green"] if lit else "#2A3A50"
        g += (f'<rect x="-16" y="-120" width="32" height="120" rx="6" fill="#1C2F4D" stroke="#36527A" stroke-width="3"/>'
              + "".join(f'<rect x="-10" y="{-110 + k * 22}" width="20" height="14" rx="3" fill="{col}" opacity="0.9"/>' for k in range(5))
              + f'<circle cx="0" cy="-130" r="10" fill="{col}" filter="url(#gl)"/>')
    elif kind == "radar":
        g += (f'<rect x="-6" y="-80" width="12" height="80" fill="#5C6E86"/>'
              f'<path d="M-50 -100 Q0 -60 50 -100 Q0 -120 -50 -100 Z" fill="#9DB4CF" stroke="#36527A" stroke-width="3" transform="rotate(-20 0 -90)"/>'
              f'<circle cx="0" cy="-96" r="5" fill="{PAL["cyan"]}" filter="url(#gl)"/>')
    elif kind == "gate":
        g += (f'<path d="M-60 0 V-140 Q0 -200 60 -140 V0 H40 V-130 Q0 -170 -40 -130 V0 Z" fill="#2B2147" stroke="#B58CFF" stroke-width="4"/>'
              f'<path d="M-40 0 V-130 Q0 -170 40 -130 V0 Z" fill="{PAL["purple"]}" opacity="0.35" filter="url(#gl)"/>')
    elif kind == "gauge":
        g += (f'<rect x="-40" y="-90" width="80" height="90" rx="10" fill="#1C2F4D" stroke="#36527A" stroke-width="3"/>'
              f'<path d="M-28 -40 A28 28 0 0 1 28 -40" fill="none" stroke="{PAL["orange"]}" stroke-width="6"/>'
              f'<path d="M0 -40 L16 -60" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>'
              f'<rect x="-28" y="-26" width="56" height="16" rx="4" fill="{PAL["cyan"]}" opacity="0.7"/>')
    elif kind == "rock":
        g += f'<path d="M-50 0 L-40 -36 L-10 -54 L26 -46 L48 -18 L54 0 Z" fill="#3E2A1E" stroke="#6B4A34" stroke-width="3"/>'
    elif kind == "fortress":
        g += (f'<path d="M-170 0 V-180 L-150 -200 V-240 H-130 V-200 H-90 V-300 L-60 -340 L-30 -300 V-380 L0 -430 L30 -380 V-300 L60 -340 L90 -300 V-200 H130 V-240 H150 V-200 L170 -180 V0 Z" fill="#14070D" stroke="#3A0A14" stroke-width="4"/>'
              + "".join(f'<rect x="{x0}" y="{y0}" width="10" height="18" fill="#FF3B3B" filter="url(#gl)"/>' for x0, y0 in ((-120, -150), (-60, -230), (50, -230), (110, -150), (-5, -330)))
              + '<path d="M-30 0 V-70 Q0 -100 30 -70 V0 Z" fill="#FF3B3B" opacity="0.85" filter="url(#gl)"/>'
              + '<path d="M-40 -260 L-14 -244 M40 -260 L14 -244" stroke="#FF3B3B" stroke-width="8" stroke-linecap="round" filter="url(#gl)"/>')
    g += "</g>"
    return g


BG_THEMES = {
    # názov: sky_top, sky_bottom, nebuly, planéta v diaľke, zem (zadná, predná), rekvizity
    "01_plus": ("#0B1E3A", "#1C5B5A", ["#3FBF5A", "#2E8BFF", "#35D6D0"], ("#3FBF5A", 1080, 140, 70, False), ("#1E4A3A", "#163829"), ["solar", "solar", "pylon", "solar"]),
    "02_minus": ("#08142E", "#2A5C8F", ["#5AB4F0", "#9FD8FF", "#2E8BFF"], ("#9FD8FF", 200, 150, 60, True), ("#3D6E9C", "#2A527A"), ["ice", "ice", "radar", "ice"]),
    "03_nula": ("#120A2A", "#3A2466", ["#9A6BE8", "#E063C8", "#2E8BFF"], ("#9A6BE8", 1060, 120, 80, False), ("#2E2050", "#21163C"), ["crystal", "rock", "crystal", "rock"]),
    "04_zrkadlo": ("#1A1030", "#7A4A1A", ["#F2B233", "#FF8C42", "#9B6BFF"], ("#F2B233", 640, 110, 70, True), ("#5A3A1A", "#3E2812"), ["crystal", "gauge", "crystal", "tower"]),
    "05_rovnice": ("#1A0A1E", "#6A1E2A", ["#E5484D", "#FF8C42", "#9B6BFF"], ("#E5484D", 180, 130, 65, False), ("#4A1A22", "#341218"), ["pylon", "pylon", "tower", "pylon"]),
    "06_porovnanie": ("#06182A", "#145A5A", ["#2FC7B6", "#35D6D0", "#2E8BFF"], ("#2FC7B6", 1100, 150, 75, True), ("#16454A", "#0F3236"), ["radar", "tower", "radar", "dome"]),
    "07_desatinna": ("#1A0E1E", "#7A3A1A", ["#FF8C42", "#FFB547", "#E5484D"], ("#FF8C42", 260, 120, 60, False), ("#55301A", "#3C2010"), ["gauge", "radar", "gauge", "pylon"]),
    "08_dvojkrok": ("#160A2A", "#5A1E5A", ["#E063C8", "#9B6BFF", "#2E8BFF"], ("#E063C8", 1040, 130, 70, True), ("#3E1A44", "#2C1232"), ["gate", "crystal", "gate", "crystal"]),
    "09_prekazky": ("#0E0A14", "#4A3020", ["#A57C5A", "#FF8C42", "#5A4A8A"], ("#A57C5A", 640, 130, 55, False), ("#3A281C", "#291C13"), ["rock", "rock", "radar", "rock"]),
    "10_boss": ("#0A0408", "#5A0A14", ["#B0263A", "#FF3B3B", "#5A0A14"], ("#5A0A14", 1120, 120, 70, False), ("#24080E", "#16050A"), ["fortress"]),
}


def gen_backgrounds():
    for name, (top, bottom, neb, pl, ground, props) in BG_THEMES.items():
        rnd = random.Random(sum(map(ord, name)))
        defs = (lin("sky", [(0, top, 1), (0.7, shade(bottom, -0.25), 1), (1, bottom, 1)]) + blur("nb", 60) + glow("gl", 6)
                + bg_planet_def(pl[0]) + lin("dm", [(0, "#5FB8FF", 0.5), (1, "#1C2F4D", 0.9)])
                + lin("trail", [(0, "#FFB547", 0), (1, "#FFD64A", 0.9)], 0, 0, 1, 1)
                + rad("hz", [(0, shade(bottom, 0.35), 0.6), (1, bottom, 0)])
                + lin("vig", [(0, "#000000", 0.25), (0.25, "#000000", 0), (0.75, "#000000", 0), (1, "#000000", 0.35)]))
        body = f'<rect width="{W_}" height="{H_}" fill="url(#sky)"/>' + nebula(rnd, neb) + starfield(rnd)
        body += bg_planet(pl[1], pl[2], pl[3], pl[0], pl[4])
        if name == "09_prekazky":  # padajúce meteority
            for _ in range(7):
                x, y, r = rnd.uniform(80, 1200), rnd.uniform(60, 380), rnd.uniform(8, 22)
                body += (f'<path d="M{x - r * 0.9:.0f} {y - r * 0.5:.0f} L{x - r * 7:.0f} {y - r * 4.5:.0f} L{x - r * 0.2:.0f} {y + r * 0.9:.0f} Z" fill="url(#trail)" opacity="0.85"/>'
                         f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="#6B4A34" stroke="#3E2A1E" stroke-width="3"/>')
        if name == "10_boss":
            body += f'<ellipse cx="640" cy="600" rx="700" ry="180" fill="#FF3B3B" opacity="0.25" filter="url(#nb)"/>'
        body += f'<ellipse cx="640" cy="580" rx="820" ry="170" fill="url(#hz)"/>'
        body += hills(rnd, 560, 30, ground[0])
        # rekvizity na zadnom kopci
        if props == ["fortress"]:
            body += prop("fortress", 640, 600, 1.0, rnd)
        else:
            xs = [110, 300, 980, 1170]
            for k, kind in enumerate(props):
                body += prop(kind, xs[k], 600 + rnd.uniform(-8, 8), 0.8 + rnd.uniform(0, 0.25), rnd)
        body += hills(rnd, 640, 18, ground[1], seg=8, stroke=shade(ground[1], 0.25))
        body += f'<rect width="{W_}" height="{H_}" fill="url(#vig)"/>'
        emit(f"backgrounds/bg_level_{name}.png", W_, H_, body, defs)

    # Hlavná základňa (menu) – stav poškodená / opravená (ADD 2.3)
    for state in ("damaged", "repaired"):
        lit = state == "repaired"
        rnd = random.Random(42)
        defs = (lin("sky", [(0, "#081430", 1), (0.65, "#132E5C", 1), (1, "#1D3F73", 1)]) + blur("nb", 60) + glow("gl", 6)
                + bg_planet_def("#E07A3A") + bg_planet_def("#6E5AD8") + lin("dm", [(0, "#5FB8FF", 0.55), (1, "#1C2F4D", 0.95)])
                + lin("plat", [(0, "#3A5A85", 1), (1, "#1A2C48", 1)])
                + lin("vig", [(0, "#000000", 0.3), (0.3, "#000000", 0), (0.7, "#000000", 0), (1, "#000000", 0.4)]))
        body = f'<rect width="{W_}" height="{H_}" fill="url(#sky)"/>' + nebula(rnd, ["#2E8BFF", "#9B6BFF", "#35D6D0"]) + starfield(rnd)
        body += bg_planet(130, 150, 46, "#E07A3A") + bg_planet(1150, 110, 70, "#6E5AD8", True)
        # mesto v diaľke
        for k in range(26):
            x = k * 52 + rnd.uniform(-10, 10)
            h = rnd.uniform(60, 180)
            body += f'<rect x="{x:.0f}" y="{520 - h:.0f}" width="{rnd.uniform(28, 46):.0f}" height="{h + 40:.0f}" rx="4" fill="#132A4A" opacity="0.85"/>'
            for j in range(int(h // 30)):
                on = rnd.random() < (0.7 if lit else 0.18)
                body += f'<rect x="{x + 8:.0f}" y="{520 - h + 12 + j * 28:.0f}" width="10" height="8" fill="{PAL["cyan"] if on else "#1F3556"}" opacity="0.9"/>'
        body += hills(rnd, 540, 14, "#1A3358")
        body += prop("tower", 210, 560, 1.0, rnd, lit) + prop("tower", 1080, 560, 1.25, rnd, lit)
        body += prop("dome", 420, 556, 0.9, rnd, lit) + prop("dome", 880, 556, 1.1, rnd, lit)
        body += prop("pylon", 1210, 570, 0.8, rnd, lit) + prop("radar", 60, 570, 0.9, rnd)
        # platforma s cestičkou
        body += f'<path d="M0 600 Q640 560 1280 600 V720 H0 Z" fill="url(#plat)" stroke="#5FB8FF" stroke-width="3" stroke-opacity="0.6"/>'
        for k in range(9):
            x = 160 + k * 120
            col = PAL["yellow"] if (lit or k % 3 == 0) else "#3A4A5E"
            body += f'<rect x="{x}" y="{640 + abs(k - 4) * 4}" width="70" height="16" rx="6" fill="{col}" opacity="{0.9 if lit else 0.6}"' + (' filter="url(#gl)"' if lit else "") + "/>"
        # podstavec s kryštálom
        body += (f'<ellipse cx="640" cy="626" rx="70" ry="16" fill="#2B4A75" stroke="#5FB8FF" stroke-width="3"/>'
                 f'<path d="M640 540 L664 580 L640 620 L616 580 Z" fill="{PAL["cyan"] if lit else "#3B5A80"}" stroke="#0B2A55" stroke-width="3"'
                 + (' filter="url(#gl)"' if lit else "") + "/>")
        if not lit:  # poškodenie – iskry a výstražné svetlá
            for x, y in ((200, 380), (1090, 330), (440, 520), (900, 500)):
                body += f'<path d="{star_path(x, y, 14, 3, 4)}" fill="{PAL["orange"]}" filter="url(#gl)"/>'
            body += f'<rect width="{W_}" height="{H_}" fill="#000814" opacity="0.25"/>'
        body += f'<rect width="{W_}" height="{H_}" fill="url(#vig)"/>'
        emit(f"backgrounds/bg_base_{state}.png", W_, H_, body, defs)

    # Samostatná parallax vrstva hviezd (priehľadná) – pre jemný pohyb pozadia
    rnd = random.Random(9)
    emit("backgrounds/layer_stars_parallax.png", W_, H_, starfield(rnd, 120))


# ====================================================================== LOGO
def gen_logo():
    defs = (lin("lg", [(0, "#BFFBFF", 1), (0.5, PAL["cyan"], 1), (1, "#1E7FD6", 1)]) + glow("lgG", 8, "#2E8BFF") + ROBOT_DEFS)
    ff = 'font-family="Avenir Next" font-weight="800"'
    t1 = (f'<text x="600" y="150" text-anchor="middle" {ff} font-size="128" letter-spacing="2" fill="url(#lg)" '
          f'stroke="#0B1A33" stroke-width="16" stroke-linejoin="round" paint-order="stroke" filter="url(#lgG)">ROBOTICKÁ</text>')
    t2 = t1.replace('y="150"', 'y="282"').replace(">ROBOTICKÁ<", ">ČÍSELNÁ MISIA<").replace('font-size="128"', 'font-size="118"')
    sub = (f'<rect x="250" y="318" width="700" height="52" rx="26" fill="{PAL["panel_dark"]}" stroke="{PAL["cyan"]}" stroke-width="3"/>'
           f'<text x="600" y="354" text-anchor="middle" {ff} font-size="28" letter-spacing="3" fill="#FFFFFF">MATEMATICKÁ VÝPRAVA PO ČÍSELNEJ OSI</text>')
    badges = ""
    for cx, cy, sym, col in ((90, 120, "+", PAL["green"]), (1110, 250, "−", PAL["orange"])):
        badges += (f'<circle cx="{cx}" cy="{cy}" r="48" fill="{col}" stroke="#0B1A33" stroke-width="6"/>'
                   f'<text x="{cx}" y="{cy + 32}" text-anchor="middle" {ff} font-size="96" fill="#FFFFFF">{sym}</text>')
    emit("ui/logo/logo_full.png", 1200, 400, badges + t1 + t2 + sub, defs)
    emit("ui/logo/logo_title_only.png", 1200, 300, t1 + t2, defs)


# ====================================================================== MOCKUPY (kompozícia)
def img(path, x, y, w, h, extra=""):
    href = os.path.relpath(os.path.join(ROOT, path), SRC)
    return f'<image xlink:href="{href}" href="{href}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" {extra}/>'


def txt(x, y, s, size=20, col="#FFFFFF", anchor="start", weight=700):
    return (f'<text x="{x}" y="{y}" font-family="Avenir Next" font-weight="{weight}" font-size="{size}" fill="{col}" '
            f'text-anchor="{anchor}">{s}</text>')


def nine(path, x, y, w, h, m, tw, th):
    """9-slice kompozícia (pre mockup) – sprite tw×th s okrajom m."""
    href = os.path.relpath(os.path.join(ROOT, path), SRC)
    out = ""
    xs = [(0, m, x, m), (m, tw - 2 * m, x + m, w - 2 * m), (tw - m, m, x + w - m, m)]
    ys = [(0, m, y, m), (m, th - 2 * m, y + m, h - 2 * m), (th - m, m, y + h - m, m)]
    for sx, sw, dx, dw in xs:
        for sy, sh, dy, dh in ys:
            NINE_ID[0] += 1
            cid = f"ns{NINE_ID[0]}"
            kx, ky = dw / sw, dh / sh
            out += (f'<clipPath id="{cid}"><rect x="{dx}" y="{dy}" width="{dw}" height="{dh}"/></clipPath>'
                    f'<g clip-path="url(#{cid})"><image href="{href}" xlink:href="{href}" width="{tw}" height="{th}" '
                    f'preserveAspectRatio="none" transform="translate({dx - sx * kx:.3f},{dy - sy * ky:.3f}) scale({kx:.5f},{ky:.5f})"/></g>')
    return out


NINE_ID = [0]


def gen_mockups():
    # Herná obrazovka
    b = img("backgrounds/bg_level_01_plus.png", 0, 0, 1280, 720)
    b += nine("ui/panels/panel.png", 24, 16, 1232, 72, 24, 128, 128)
    for i in range(3):
        b += img("sprites/items/item_heart.png", 44 + i * 44, 30, 40, 40)
    b += img("sprites/items/item_star.png", 190, 28, 44, 44) + txt(240, 62, "320", 28, PAL["yellow"])
    b += txt(640, 50, "PLANÉTA PLUS • KLADNÉ ČÍSLA", 22, "#FFFFFF", "middle") + txt(640, 76, "ÚLOHA 3 / 5", 16, PAL["cyan"], "middle")
    b += nine("ui/hud/bar_frame.png", 900, 38, 220, 24, 12, 256, 32) + nine("ui/hud/bar_fill_green.png", 904, 41, 130, 18, 10, 64, 24)
    b += img("ui/buttons/button_dark_normal.png", 1140, 26, 100, 52) + img("ui/icons/icon_pause.png", 1172, 34, 34, 34)
    b += nine("ui/panels/panel_header.png", 440, 110, 400, 110, 40, 256, 128)
    b += txt(640, 140, "VYRIEŠ PRÍKLAD", 16, PAL["cyan"], "middle") + txt(640, 200, "2 + 4 = ?", 46, "#FFFFFF", "middle")
    b += img("sprites/obstacles/obstacle_barrier.png", 300, 330, 100, 50) + img("sprites/obstacles/obstacle_L_000.png", 960, 260, 110, 110)
    b += img("sprites/items/item_crystal_energy.png", 150, 300, 60, 60) + img("sprites/items/item_bonus_gem.png", 1100, 380, 54, 54)
    ax0, ax1, ay = 110, 1170, 520
    for k in range(ax0, ax1, 64):
        b += img("ui/numberline/axis_tile.png", k, ay - 8, 64, 16)
    b += img("ui/numberline/arrow_end.png", ax1 - 6, ay - 20, 40, 40)
    for n in range(-10, 11):
        x = ax0 + (n + 10) / 20 * (ax1 - ax0 - 40) + 20
        if n == 0:
            b += img("ui/numberline/tick_zero.png", x - 6, ay - 26, 12, 52)
        else:
            b += img("ui/numberline/tick_major.png" if n % 2 == 0 else "ui/numberline/tick_minor.png", x - 4, ay - (20 if n % 2 == 0 else 12), 8 if n % 2 == 0 else 6, 40 if n % 2 == 0 else 24)
        if n % 2 == 0:
            b += txt(x, ay + 50, str(n).replace("-", "−"), 22, "#FFFFFF", "middle")
    def nx(v):
        return ax0 + (v + 10) / 20 * (ax1 - ax0 - 40) + 20
    b += img("ui/numberline/jump_arc.png", nx(2), ay - 100, nx(6) - nx(2), 80)
    b += img("ui/numberline/marker_start.png", nx(2) - 22, ay - 22, 44, 44) + img("ui/numberline/goal_flag.png", nx(6) - 10, ay - 90, 48, 72)
    b += img("sprites/robot/frames/robot_walk_02.png", nx(3.2) - 64, ay - 128, 128, 128)
    for i, v in enumerate(("5", "6", "7", "8")):
        st = "green" if v == "6" else "blue"
        b += img(f"ui/buttons/button_square_{st}_normal.png", 448 + i * 100, 590, 88, 88) + txt(492 + i * 100, 642, v, 36, "#FFFFFF", "middle")
    b += img("ui/buttons/button_orange_normal.png", 60, 610, 170, 58) + img("ui/icons/icon_hint.png", 76, 620, 32, 32) + txt(156, 645, "NÁPOVEDA", 18, "#FFFFFF", "middle")
    b += img("ui/buttons/button_green_normal.png", 1050, 610, 170, 58) + img("ui/icons/icon_check.png", 1064, 620, 32, 32) + txt(1146, 645, "POTVRDIŤ", 18, "#FFFFFF", "middle")
    b += img("effects/fx_crystal.png", 150, 290, 80, 80, 'opacity="0.8"')
    emit("reference/mockup_game.png", 1280, 720, b)

    # Hlavné menu
    b = img("backgrounds/bg_base_repaired.png", 0, 0, 1280, 720)
    b += img("ui/logo/logo_full.png", 40, 20, 660, 220)
    b += img("sprites/robot/robot_portrait.png", 760, 150, 460, 460)
    b += img("ui/panels/speech_bubble.png", 1010, 70, 230, 144) + txt(1124, 122, "Poďme opraviť", 20, PAL["bg"], "middle") + txt(1124, 150, "základňu!", 20, PAL["bg"], "middle")
    labels = (("green", "ZAČAŤ MISIU", "play"), ("blue", "VÝBER ÚROVNE", "map"), ("dark", "NASTAVENIA", "settings"),
              ("dark", "AKO HRAŤ", "help"), ("red", "KONIEC", "exit"))
    for i, (col, lab, ic) in enumerate(labels):
        y = 270 + i * 78
        b += img(f"ui/buttons/button_{col}_normal.png", 140, y, 380, 68) + img(f"ui/icons/icon_{ic}.png", 166, y + 12, 38, 38) + txt(345, y + 41, lab, 24, "#FFFFFF", "middle")
    emit("reference/mockup_menu.png", 1280, 720, b)

    # Mapa úrovní
    b = img("backgrounds/bg_level_03_nula.png", 0, 0, 1280, 720)
    b += txt(640, 70, "MAPA ÚROVNÍ", 40, "#FFFFFF", "middle")
    pos = [(110, 220), (330, 170), (550, 230), (770, 170), (990, 230), (1170, 300), (990, 460), (770, 520), (550, 460), (300, 500)]
    for i in range(len(pos) - 1):
        (x0, y0), (x1, y1) = pos[i], pos[i + 1]
        for k in range(1, 8):
            t = k / 8
            b += img("sprites/planets/planet_path_dot.png", x0 + (x1 - x0) * t - 6, y0 + (y1 - y0) * t - 6, 12, 12)
    for i, (x, y) in enumerate(pos):
        f = PLANETS[i][0] if i < 4 else None
        src = f"sprites/planets/planet_{f}.png" if f else "sprites/planets/planet_locked.png"
        if i == 9:
            src = "sprites/planets/planet_10_boss.png" if False else "sprites/planets/planet_locked.png"
        b += img(src, x - 70, y - 70, 140, 140)
        b += txt(x, y + 92, f"{i + 1}. " + ["PLUS", "MÍNUS", "NULA", "ZRKADLO", "ROVNICE", "POROVNANIE", "DESATINNÁ", "DVOJKROK", "PREKÁŽKY", "BOSS"][i], 18, "#FFFFFF" if i < 4 else "#8FA3BC", "middle")
        if i < 3:
            for s in range(3):
                b += img("sprites/items/item_star.png", x - 42 + s * 28, y - 100, 26, 26)
    b += img("sprites/robot/frames/robot_idle_01.png", 690, 60, 100, 100)
    b += img("ui/buttons/button_dark_normal.png", 40, 630, 200, 60) + img("ui/icons/icon_back.png", 58, 644, 32, 32) + txt(156, 668, "SPÄŤ", 20, "#FFFFFF", "middle")
    emit("reference/mockup_levels.png", 1280, 720, b)


# ====================================================================== RENDER
def render(jobs):
    if not os.path.exists(INKSCAPE):
        sys.exit("Inkscape sa nenašiel – nastav premennú INKSCAPE.")
    # Inkscape shell mód – jeden proces pre všetky súbory
    cmds = "".join(f"file-open:{s}; export-filename:{p}; export-width:{w}; export-height:{h}; export-background-opacity:0; export-do; file-close\n"
                   for s, p, w, h in jobs)
    proc = subprocess.run([INKSCAPE, "--shell"], input=cmds + "quit\n", text=True, capture_output=True)
    missing = [p for _, p, _, _ in jobs if not os.path.exists(p)]
    if missing:
        print(proc.stderr[-2000:])
        sys.exit(f"Nevyrenderované: {len(missing)} súborov, napr. {missing[:3]}")


def main():
    os.makedirs(SRC, exist_ok=True)
    # .gdignore – Godot nebude importovať SVG zdroje ani skript
    open(os.path.join(ROOT, "_source", ".gdignore"), "w").close()
    gen_robot(); gen_obstacles(); gen_items(); gen_ui(); gen_icons(); gen_numberline()
    gen_effects(); gen_planets(); gen_backgrounds(); gen_logo()
    base_jobs = list(JOBS)
    render(base_jobs)
    JOBS.clear()
    gen_mockups()           # mockupy skladajú už vyrenderované PNG
    render(JOBS)
    print(f"Hotovo: {len(base_jobs)} assetov + {len(JOBS)} mockupy.")


if __name__ == "__main__":
    main()
