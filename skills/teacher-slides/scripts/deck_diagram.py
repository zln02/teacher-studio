# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""`diagram` slide: a simple drawn figure (ray diagram, flow, labelled picture) from a list of shapes - image-free, editable in PPT.

    {"type":"diagram","title":"빛의 반사 법칙","points":["입사각 = 반사각", ...],          # points: 0-4 short notes beside the figure
     "shapes":[{"kind":"line","x1":10,"y1":50,"x2":90,"y2":50,"color":"mu","w":3},          # canvas = 100 wide x 60 high, (0,0) top-left
               {"kind":"dash","x1":50,"y1":8,"x2":50,"y2":50},
               {"kind":"arrow","x1":20,"y1":12,"x2":50,"y2":50,"color":"ac"},
               {"kind":"arc","cx":50,"cy":50,"r":10,"from":90,"to":128},                    # degrees: 0 = right, 90 = up
               {"kind":"rect","x":0,"y":50,"w":100,"h":10,"fill":"water","text":"물"},
               {"kind":"circle","cx":20,"cy":20,"r":6,"fill":"ac","text":"광원"},
               {"kind":"label","x":22,"y":20,"text":"입사 광선","color":"ac","size":"m","align":"l"}]}
               {"kind":"poly","points":[[30,50],[50,15],[70,50]],"fill":"ac"}                # any closed outline (3-12 corners)
kinds: line, dash, arrow, dasharrow, rect, circle (rx, ry instead of r = an oval), poly, arc, label.  colours: pr ac tx mu good bad line water sky sun (or #rrggbb).
The same list draws the web slide (inline SVG) and the .pptx (real lines, arrows, shapes and text boxes).
"""
from __future__ import annotations

import math
import re

from deck_kit import esc, plain

KINDS = ("line", "dash", "arrow", "dasharrow", "rect", "circle", "arc", "label", "poly")
ALIAS = {"text": "label", "box": "rect", "oval": "circle", "ellipse": "circle", "polygon": "poly", "triangle": "poly", "shape": "poly", "dashed": "dash", "ray": "arrow", "dashedarrow": "dasharrow", "dash-arrow": "dasharrow"}
FIXED = {"water": "#bfe3f2", "sky": "#eaf4fb", "sun": "#f5b301", "white": "#ffffff", "black": "#111111", "glass": "#d7ecf5"}
SIZES = {"s": 0.8, "m": 1.0, "l": 1.35}
CW_, CH_ = 100.0, 60.0


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def kind_of(sh: dict) -> str:
    k = str(sh.get("kind") or sh.get("type") or "").lower()
    return ALIAS.get(k, k)


def check(i: int, it: dict) -> list[str]:
    e: list[str] = []
    shapes = it.get("shapes") or []
    if not isinstance(shapes, list) or not 2 <= len(shapes) <= 40:
        return [f"slide {i} diagram.shapes: {len(shapes) if isinstance(shapes, list) else 0} shapes -> use 2-40 (canvas 100 x 60, kinds: {', '.join(KINDS)})"]
    for j, sh in enumerate(shapes):
        k = kind_of(sh) if isinstance(sh, dict) else ""
        if k not in KINDS:
            e.append(f"slide {i} diagram.shapes[{j}]: kind '{sh.get('kind') if isinstance(sh, dict) else sh}' -> one of {', '.join(KINDS)}")
            continue
        need = {"line": ("x1", "y1", "x2", "y2"), "dash": ("x1", "y1", "x2", "y2"), "arrow": ("x1", "y1", "x2", "y2"), "dasharrow": ("x1", "y1", "x2", "y2"),
                "rect": ("x", "y", "w", "h"), "circle": ("cx", "cy", "r"), "arc": ("cx", "cy", "r", "from", "to"), "label": ("x", "y", "text"), "poly": ("points",)}[k]
        if k == "circle" and sh.get("r") is None and sh.get("rx") is not None and sh.get("ry") is not None:
            need = ("cx", "cy")
        if k == "poly":
            pts_ = sh.get("points")
            if not isinstance(pts_, list) or not 3 <= len(pts_) <= 12 or any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in pts_):
                e.append(f"slide {i} diagram.shapes[{j}] poly: points = 3-12 corners [[x, y], ...]")
                continue
            if any(not -2 <= _f(p[0]) <= 102 or not -2 <= _f(p[1]) <= 62 for p in pts_):
                e.append(f"slide {i} diagram.shapes[{j}] poly: outside the canvas (x 0-100, y 0-60)")
            continue
        miss = [n for n in need if sh.get(n) is None]
        if miss:
            e.append(f"slide {i} diagram.shapes[{j}] {k}: missing {', '.join(miss)}")
            continue
        xs = [_f(sh.get(n)) for n in ("x", "x1", "x2", "cx") if sh.get(n) is not None]
        ys = [_f(sh.get(n)) for n in ("y", "y1", "y2", "cy") if sh.get(n) is not None]
        if any(not -2 <= v <= 102 for v in xs) or any(not -2 <= v <= 62 for v in ys):
            e.append(f"slide {i} diagram.shapes[{j}] {k}: outside the canvas (x 0-100, y 0-60)")
        if len(plain(str(sh.get("text", "")))) > 24:
            e.append(f"slide {i} diagram.shapes[{j}]: text > 24 chars -> a short label (put the sentence in points)")
    pts = it.get("points") or []
    if len(pts) > 4 or any(len(plain(str(p))) > 44 for p in pts):
        e.append(f"slide {i} diagram.points: at most 4 notes of <= 44 chars")
    if not any(kind_of(sh) == "label" or sh.get("text") for sh in shapes if isinstance(sh, dict)):
        e.append(f"slide {i} diagram: add labels (kind 'label') so the figure explains itself")
    if not e:
        e += [f"slide {i} diagram: {m}" for m in overlaps(it)[:4]]
    return e


def color(name, colors: dict, default: str) -> str:
    """Role name / fixed name / hex -> hex."""
    n = str(name or "").strip()
    if not n:
        n = default
    if re.match(r"^#[0-9a-fA-F]{6}$", n):
        return n
    if n in FIXED:
        return FIXED[n]
    return colors.get({"primary": "pr", "accent": "ac", "text": "tx", "muted": "mu"}.get(n, n)) or colors.get(default) or "#444444"


def _lum(h: str) -> float:
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ink_on(fill: str) -> str:
    return "#111111" if _lum(fill) > 0.55 else "#ffffff"


def arc_points(sh) -> tuple[float, float, float, float, float]:
    """(cx, cy, r, screen start deg, screen end deg) with the sweep going clockwise on screen."""
    a, b = _f(sh.get("from")), _f(sh.get("to"))
    lo, hi = min(a, b), max(a, b)
    return _f(sh.get("cx")), _f(sh.get("cy")), _f(sh.get("r")), (-hi) % 360, (-lo) % 360


def svg(it: dict, colors: dict, w: int, h: int, floor: int = 28, uid: str = "d") -> str:
    """Inline SVG in stage pixels (text sizes are real px so the 28px review floor holds)."""
    k = w / CW_
    base = max(floor, 30)
    canvas = colors.get("card") or "#ffffff"
    onc = colors.get("ct") or ink_on(canvas)
    labels = []  # texts are real HTML boxes over the drawing (keep-all, contrast and size checks see them like any slide text)

    def lab(x, y, text, size, col, anchor="middle"):
        tr = {"start": "translate(0,-50%)", "end": "translate(-100%,-50%)"}.get(anchor, "translate(-50%,-50%)")
        labels.append(f'<div class="dl" style="position:absolute;left:{x:.0f}px;top:{y:.0f}px;transform:{tr};font-size:{size}px;line-height:1.15;'
                      f'font-weight:700;color:{col};white-space:nowrap;word-break:keep-all">{esc(plain(text))}</div>')
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true">'
           f'<defs></defs><rect x="0" y="0" width="{w}" height="{h}" rx="18" fill="{canvas}"/>']
    defs = []
    shapes_ = it.get("shapes") or []
    for n, sh in enumerate(shapes_):
        kd = kind_of(sh)
        col = color(sh.get("color"), colors, "ct" if kd in ("label", "line", "dash") else "pr")
        col = legible(col, shapes_, n, colors)
        lw = max(3.0, _f(sh.get("w"), 4.0) * 1.4)
        if kd in ("line", "dash", "arrow", "dasharrow"):
            x1, y1, x2, y2 = (_f(sh.get(a)) * k for a in ("x1", "y1", "x2", "y2"))
            mk = ""
            if "arrow" in kd:
                mid = f"{uid}a{n}"
                defs.append(f'<marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="{col}"/></marker>')
                mk = f' marker-end="url(#{mid})"'
            da = f' stroke-dasharray="{lw * 3:.0f} {lw * 2.4:.0f}"' if "dash" in kd else ""
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{lw:.1f}" stroke-linecap="round"{da}{mk}/>')
        elif kd in ("rect", "circle"):
            fill = color(sh.get("fill"), colors, "bg2") if sh.get("fill") != "none" else "none"
            st = f' stroke="{color(sh.get("color"), colors, "line")}" stroke-width="3"' if sh.get("color") or fill == "none" else ""
            if kd == "rect":
                x, y, ww, hh = (_f(sh.get(a)) * k for a in ("x", "y", "w", "h"))
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{ww:.1f}" height="{hh:.1f}" rx="{_f(sh.get("round"), 0) * k:.1f}" fill="{fill}"{st}/>')
                tx, ty = x + ww / 2, y + hh / 2
            else:
                cx, cy = (_f(sh.get(a)) * k for a in ("cx", "cy"))
                rx, ry = radii(sh)
                out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx * k:.1f}" ry="{ry * k:.1f}" fill="{fill}"{st}/>')
                tx, ty = cx, cy
            if sh.get("text"):
                tc = ink_on(fill) if fill != "none" else onc
                lab(tx, ty, sh["text"], base, tc)
        elif kd == "poly":
            fill = color(sh.get("fill"), colors, "bg2") if sh.get("fill") != "none" else "none"
            st = f' stroke="{color(sh.get("color"), colors, "line")}" stroke-width="3" stroke-linejoin="round"' if sh.get("color") or fill == "none" else ""
            out.append('<polygon points="' + " ".join(f"{_f(p[0]) * k:.1f},{_f(p[1]) * k:.1f}" for p in sh["points"]) + f'" fill="{fill}"{st}/>')
            if sh.get("text"):
                lab(sum(_f(p[0]) for p in sh["points"]) / len(sh["points"]) * k, sum(_f(p[1]) for p in sh["points"]) / len(sh["points"]) * k, sh["text"], base,
                    ink_on(fill) if fill != "none" else onc)
        elif kd == "arc":
            cx, cy, r, s, e_ = arc_points(sh)
            p0 = (cx * k + r * k * math.cos(math.radians(s)), cy * k + r * k * math.sin(math.radians(s)))
            p1 = (cx * k + r * k * math.cos(math.radians(e_)), cy * k + r * k * math.sin(math.radians(e_)))
            big = 1 if (e_ - s) % 360 > 180 else 0
            out.append(f'<path d="M{p0[0]:.1f} {p0[1]:.1f} A{r * k:.1f} {r * k:.1f} 0 {big} 1 {p1[0]:.1f} {p1[1]:.1f}" fill="none" stroke="{col}" stroke-width="{lw:.1f}"/>')
        elif kd == "label":
            size = int(base * SIZES.get(str(sh.get("size", "m")), 1.0))
            size = max(size, floor)
            anc = {"l": "start", "c": "middle", "r": "end"}.get(str(sh.get("align", "c"))[:1], "middle")
            lab(_f(sh.get("x")) * k, _f(sh.get("y")) * k, sh["text"], size, col, anc)
    return "".join(out).replace("<defs></defs>", "<defs>" + "".join(defs) + "</defs>") + "</svg>" + "".join(labels)


def radii(sh: dict) -> tuple[float, float]:
    """(rx, ry) of a circle shape; rx / ry make it an oval."""
    r = _f(sh.get("r"))
    return _f(sh.get("rx"), r) or r, _f(sh.get("ry"), r) or r


def _in_poly(x: float, y: float, pts: list) -> bool:
    inside = False
    n = len(pts)
    for a in range(n):
        x1, y1 = _f(pts[a][0]), _f(pts[a][1])
        x2, y2 = _f(pts[(a + 1) % n][0]), _f(pts[(a + 1) % n][1])
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1:
            inside = not inside
    return inside


def _contrast(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def backdrop(shapes: list, upto: int, x: float, y: float, colors: dict) -> str:
    """Fill colour under canvas point (x, y): the last filled rect / circle drawn before shape `upto` that contains it, else the card."""
    bg = colors.get("card") or "#ffffff"
    for sh in shapes[:upto]:
        if not isinstance(sh, dict) or sh.get("fill") == "none":
            continue
        kd = kind_of(sh)
        if kd == "rect" and _f(sh.get("x")) <= x <= _f(sh.get("x")) + _f(sh.get("w")) and _f(sh.get("y")) <= y <= _f(sh.get("y")) + _f(sh.get("h")):
            bg = color(sh.get("fill"), colors, "bg2")
        elif kd == "circle" and ((x - _f(sh.get("cx"))) / (radii(sh)[0] or 1)) ** 2 + ((y - _f(sh.get("cy"))) / (radii(sh)[1] or 1)) ** 2 <= 1:
            bg = color(sh.get("fill"), colors, "bg2")
        elif kd == "poly" and isinstance(sh.get("points"), list) and _in_poly(x, y, sh["points"]):
            bg = color(sh.get("fill"), colors, "bg2")
    return bg


def legible(col: str, shapes: list, idx: int, colors: dict) -> str:
    """The shape's colour, or black/white when it would vanish on what lies under it (yellow ray on light water ...)."""
    sh = shapes[idx]
    kd = kind_of(sh)
    if kd == "label":
        pts = [(_f(sh.get("x")), _f(sh.get("y")))]
    elif kd == "arc":
        cx, cy, r, s, e_ = arc_points(sh)
        m = math.radians(s + ((e_ - s) % 360) / 2)
        pts = [(cx + r * math.cos(m), cy + r * math.sin(m))]
    elif kd in ("line", "dash", "arrow", "dasharrow"):
        x1, y1, x2, y2 = (_f(sh.get(a)) for a in ("x1", "y1", "x2", "y2"))
        pts = [(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t) for t in (0.25, 0.5, 0.75)]
    else:
        return col
    worst = min(pts, key=lambda p: _contrast(col, backdrop(shapes, idx, p[0], p[1], colors)))
    bg = backdrop(shapes, idx, worst[0], worst[1], colors)
    need = 3.0 if kd != "label" else 4.5
    if _contrast(col, bg) >= need:
        return col
    for alt in ("pr", "ac", "ct", "tx"):
        c = colors.get(alt)
        if c and _contrast(c, bg) >= need and kd != "label":
            return c
    return ink_on(bg)


_LABEL_H = {"s": 2.6, "m": 3.3, "l": 4.4}  # label height in canvas units (matches the .pptx sizes 14 / 18 / 24 pt)


def _label_box(sh: dict) -> tuple[float, float, float, float]:
    import pptx_fit
    h = _LABEL_H.get(str(sh.get("size", "m")), 3.3)
    w = pptx_fit.width_em(plain(str(sh.get("text", "")))) * h * 0.92
    x, y = _f(sh.get("x")), _f(sh.get("y"))
    al = str(sh.get("align", "c"))[:1]
    x0 = x if al == "l" else (x - w if al == "r" else x - w / 2)
    return x0 + w * 0.06, y - h * 0.36, x0 + w * 0.94, y + h * 0.36  # a little smaller than the glyph box: touching is fine


def _seg_hits(x1, y1, x2, y2, box) -> bool:
    """Liang-Barsky: does the segment pass through the box?"""
    bx0, by0, bx1, by1 = box
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
        if abs(p) < 1e-9:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return False
    return True


def overlaps(it: dict) -> list[str]:
    """Labels that sit on top of a line / arrow, or on another label (hard to read on a projector): plain fix hints."""
    shapes = [s for s in (it.get("shapes") or []) if isinstance(s, dict)]
    labels = [(j, s, _label_box(s)) for j, s in enumerate(shapes) if kind_of(s) == "label" and s.get("text")]
    out = []
    for j, s, box in labels:
        for ln in shapes:
            if kind_of(ln) in ("line", "dash", "arrow", "dasharrow") and all(ln.get(a) is not None for a in ("x1", "y1", "x2", "y2")):
                if _seg_hits(_f(ln["x1"]), _f(ln["y1"]), _f(ln["x2"]), _f(ln["y2"]), box):
                    out.append(f"label '{plain(str(s['text']))}' (shapes[{j}]) sits on a line -> move it about 4 units to the side (its box is x {box[0]:.0f}-{box[2]:.0f}, y {box[1]:.0f}-{box[3]:.0f})")
                    break
        else:
            for j2, s2, b2 in labels:
                if j2 > j and box[0] < b2[2] and b2[0] < box[2] and box[1] < b2[3] and b2[1] < box[3]:
                    out.append(f"labels '{plain(str(s['text']))}' and '{plain(str(s2['text']))}' overlap -> move one of them")
                    break
    return out
