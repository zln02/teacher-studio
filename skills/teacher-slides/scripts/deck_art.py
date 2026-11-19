# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Procedural, image-free art for slides: restrained backgrounds (one quiet motif per style) and purposeful hero shapes.

Principle (owner's bar): restraint over decoration. Backgrounds carry ONE low-opacity motif at an edge; hero shapes are
geometric (rings / blocks / arcs) in the deck's accent + one Lucide icon. No scattered icon stickers, no clip-art.
Everything is a pure function of (design tokens, seed, slide index): same input -> same SVG.
"""
from __future__ import annotations

import math
import random

ICON_ALIAS = {
    "식물": "sprout", "광합성": "sun", "잎": "leaf", "나무": "tree-pine", "꽃": "flower-2", "햇빛": "sun", "태양": "sun", "물": "droplet", "비": "cloud-rain",
    "과학": "flask-conical", "실험": "flask-conical", "화학": "flask-conical", "원자": "atom", "세포": "microscope", "생물": "dna", "현미경": "microscope",
    "수학": "calculator", "계산": "calculator", "도형": "ruler", "책": "book-open", "독서": "book-open", "국어": "book-open", "영어": "message-circle", "대화": "message-circle",
    "지구": "globe", "세계": "globe", "사회": "globe", "역사": "landmark", "지도": "map-pin", "음악": "music", "노래": "music-2", "미술": "palette", "그림": "palette",
    "체육": "trophy", "운동": "bike", "게임": "gamepad-2", "컴퓨터": "bot", "ai": "bot", "AI": "bot", "코딩": "bot", "로봇": "bot", "학교": "school", "교실": "school",
    "학부모": "heart-handshake", "가정": "house", "집": "house", "사람": "users", "모둠": "users", "협력": "handshake", "응원": "heart", "사랑": "heart", "마음": "heart",
    "아이디어": "lightbulb", "생각": "lightbulb", "목표": "target", "별": "star", "축하": "party-popper", "시간": "clock", "타이머": "timer", "달력": "calendar", "일정": "calendar",
    "안전": "shield", "경고": "triangle-alert", "질문": "search", "퀴즈": "puzzle", "수업": "graduation-cap", "연수": "graduation-cap", "발표": "megaphone", "홍보": "megaphone",
    "동아리": "sparkles", "영상": "clapperboard", "사진": "camera", "편지": "mail", "전화": "phone", "건강": "heart", "급식": "apple", "환경": "recycle", "우주": "rocket",
    "chart": "chart-bar", "그래프": "chart-bar", "통계": "chart-bar", "데이터": "chart-bar",
}


def icon_name(word: str, default: str = "sparkles") -> str:
    """Keyword (Korean or Lucide name) -> a Lucide icon name."""
    w = (word or "").strip()
    if not w:
        return default
    if w in ICON_ALIAS:
        return ICON_ALIAS[w]
    for k, v in ICON_ALIAS.items():
        if k in w:
            return v
    return w.lower() if all(ch.isalnum() or ch == "-" for ch in w.lower()) and w.isascii() else default


def icon(name: str, cls: str = "i") -> str:
    """Inline Lucide icon (symbols are added to the page by shared/vendor/inline.py)."""
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true"><use href="#lucide-{name}"/></svg>'


def _op(v: float) -> str:
    return f"{max(0.0, min(1.0, v)):.3f}".rstrip("0").rstrip(".")


def blob(r: random.Random, cx: float, cy: float, rad: float, n: int = 7, jitter: float = 0.18) -> str:
    """Smooth closed organic path."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = rad * (1 + r.uniform(-jitter, jitter))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = []
    for k in range(n):
        p0, p1, p2, p3 = pts[(k - 1) % n], pts[k], pts[(k + 1) % n], pts[(k + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        if k == 0:
            d.append(f"M{p1[0]:.1f} {p1[1]:.1f}")
        d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return "".join(d) + "z"


CORNERS = [(1920, 0), (0, 1080), (1920, 1080), (0, 0)]


def background(dz: dict, idx: int, role: str) -> str:
    """Slide background SVG: soft gradient + ONE quiet motif. role: cover | section | content."""
    c, gen, seed = dz["colors"], dz["lang"]["bg"], dz["seed"]
    r = random.Random(seed * 7919 + idx * 31)
    s = {"cover": 1.0, "section": 0.9, "content": 0.5}.get(role, 0.5)
    cx, cy = CORNERS[(idx + seed) % 4]
    if gen in ("bokeh", "neongrid", "glassblobs", "stage"):
        cx, cy = 1920, (0 if idx % 2 == 0 else 1080)  # glows sit on the right edge, away from left-aligned text
    ang = (idx * 37 + seed * 13) % 360
    uid = f"g{idx}"
    defs = (f'<linearGradient id="{uid}" gradientTransform="rotate({ang} .5 .5)"><stop offset="0" stop-color="{c["bg1"]}"/><stop offset="1" stop-color="{c["bg2"]}"/></linearGradient>'
            f'<radialGradient id="{uid}r"><stop offset="0" stop-color="{c["pr"]}" stop-opacity=".34"/><stop offset="1" stop-color="{c["pr"]}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="{uid}w"><stop offset="0" stop-color="{c["tx"]}" stop-opacity=".14"/><stop offset="1" stop-color="{c["tx"]}" stop-opacity="0"/></radialGradient>')
    body = [f'<rect width="1920" height="1080" fill="url(#{uid})"/>']
    pr, ac, tx = c["pr"], c["ac"], c["tx"]
    if gen == "neongrid":
        horizon = 700 if role != "content" else 840
        lines = []
        for k in range(1, 9):
            y = horizon + (1080 - horizon) * (k / 8) ** 1.7
            lines.append(f'<line x1="0" x2="1920" y1="{y:.0f}" y2="{y:.0f}"/>')
        for k in range(-12, 13):
            lines.append(f'<line x1="960" y1="{horizon}" x2="{960 + k * 190}" y2="1080"/>')
        body.append(f'<g stroke="{pr}" stroke-opacity="{_op(.22 * s)}" stroke-width="2">{"".join(lines)}</g>')
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{520 * (0.6 + s * .4):.0f}" fill="url(#{uid}r)" opacity="{_op(.45 * s + .1)}"/>')
    elif gen == "bokeh":
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{620 * (0.7 + s * .3):.0f}" fill="url(#{uid}r)" opacity="{_op(.2 * s + .03)}"/>')
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{360}" fill="none" stroke="{pr}" stroke-opacity="{_op(.25 * s)}" stroke-width="2"/>')
    elif gen == "memphis":
        rad = 420 if role != "content" else 230
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="{pr}" fill-opacity="{_op(.95 if role == "cover" else .85 if role == "section" else .18)}"/>')
        body.append(f'<circle cx="{cx}" cy="{cy}" r="{rad + 70}" fill="none" stroke="{ac}" stroke-opacity="{_op(.8 if role != "content" else .3)}" stroke-width="6"/>')
    elif gen == "bunting":
        n, y0 = 9, 0
        fl = []
        for k in range(n):
            x = 60 + k * (1800 / (n - 1))
            sag = 38 * math.sin(math.pi * k / (n - 1))
            col = pr if k % 2 == 0 else ac
            fl.append(f'<path d="M{x - 34:.0f} {y0 + sag:.0f}h68l-34 {44 if role != "content" else 30}z" fill="{col}" fill-opacity="{_op(.8 if role != "content" else .35)}"/>')
        body.append("".join(fl))
    elif gen == "stage":
        x0 = 480 + (idx % 3) * 480
        body.append(f'<path d="M{x0 - 40} 0L{x0 + 40} 0L{x0 + 420} 1080L{x0 - 420} 1080z" fill="url(#{uid}w)" opacity="{_op(.5 * s + .15)}"/>')
        body.append(f'<ellipse cx="{x0}" cy="1040" rx="520" ry="70" fill="{pr}" fill-opacity="{_op(.18 * s)}"/>')
    elif gen == "glassblobs":
        body.append(f'<filter id="{uid}f" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="90"/></filter>')
        ox, oy = 1920 - cx, 1080 - cy
        body.append(f'<g filter="url(#{uid}f)"><circle cx="{cx}" cy="{cy}" r="{420 * (0.7 + s * .3):.0f}" fill="{pr}" fill-opacity="{_op(.26 * s + .04)}"/>'
                    f'<circle cx="{ox}" cy="{oy}" r="{300 * (0.7 + s * .3):.0f}" fill="{pr}" fill-opacity="{_op(.16 * s + .03)}"/></g>')
    elif gen == "speed":
        fx, fy = (cx, cy)
        ls = []
        for k in range(36):
            a = 2 * math.pi * k / 36 + r.uniform(-.03, .03)
            ls.append(f'<line x1="{fx + 520 * math.cos(a):.0f}" y1="{fy + 520 * math.sin(a):.0f}" x2="{fx + 2600 * math.cos(a):.0f}" y2="{fy + 2600 * math.sin(a):.0f}"/>')
        body.append(f'<g stroke="{tx}" stroke-opacity="{_op(.10 * s + .03)}" stroke-width="{4 if role != "content" else 2}">{"".join(ls)}</g>')
    elif gen == "hills":
        h = 230 if role != "content" else 120
        p1 = f"M0 {1080 - h}C400 {1080 - h - 90} 800 {1080 - h + 40} 1200 {1080 - h - 30}S1700 {1080 - h - 80} 1920 {1080 - h - 20}V1080H0z"
        p2 = f"M0 {1080 - h * .55:.0f}C500 {1080 - h * .9:.0f} 900 {1080 - h * .3:.0f} 1400 {1080 - h * .7:.0f}S1800 {1080 - h * .5:.0f} 1920 {1080 - h * .6:.0f}V1080H0z"
        body.append(f'<path d="{p1}" fill="{pr}" fill-opacity="{_op(.14 + .05 * s)}"/><path d="{p2}" fill="{ac}" fill-opacity="{_op(.16 + .05 * s)}"/>')
    elif gen == "pixel":
        u = 48 if role != "content" else 32
        sq = []
        for k in range(7 if role != "content" else 4):
            for j in range(k + 1):
                x = (1920 - (k + 1) * u) if cx else k * u
                y = 1080 - (j + 1) * u
                sq.append(f'<rect x="{x}" y="{y}" width="{u}" height="{u}"/>')
        body.append(f'<g fill="{pr}" fill-opacity="{_op(.22 * s + .06)}">{"".join(sq)}</g>')
    elif gen == "minimal":
        body.append(f'<rect x="56" y="56" width="1808" height="968" fill="none" stroke="{tx}" stroke-opacity=".14" stroke-width="2"/>')
        if role != "content":
            body.append(f'<circle cx="{cx}" cy="{cy}" r="440" fill="none" stroke="{pr}" stroke-opacity=".22" stroke-width="2"/>')
    elif gen == "chalk":
        body.append(f'<rect x="48" y="48" width="1824" height="984" rx="18" fill="none" stroke="{tx}" stroke-opacity=".4" stroke-width="3" stroke-dasharray="26 14"/>')
        dots = "".join(f'<circle cx="{r.randint(60, 1860)}" cy="{r.randint(60, 1020)}" r="{r.choice((1.5, 2, 3))}"/>' for _ in range(46))
        body.append(f'<g fill="{tx}" fill-opacity=".13">{dots}</g>')
    elif gen == "leaves":
        lv = []
        for k in range(3 if role != "content" else 2):
            a = (k - 1) * 32 + (20 if cx else 160)
            L = (520 - 90 * k) * (0.6 + s * .4)
            col = pr if k % 2 == 0 else ac
            lv.append(f'<g transform="translate({cx} {cy}) rotate({a + (180 if cy else 0)})"><path d="M0 0C{L * .25:.0f} {-L * .32:.0f} {L * .75:.0f} {-L * .22:.0f} {L:.0f} 0C{L * .75:.0f} {L * .22:.0f} {L * .25:.0f} {L * .32:.0f} 0 0z" fill="{col}" fill-opacity="{_op(.14 + .06 * s)}"/></g>')
        body.append("".join(lv))
    return f'<svg class="bgart" viewBox="0 0 1920 1080" preserveAspectRatio="none" aria-hidden="true"><defs>{defs}</defs>{"".join(body)}</svg>'


def hero(dz: dict, kind: str, names: list[str], w: int, h: int, idx: int = 0) -> str:
    """Purposeful hero art: geometric composition in the accent + ONE Lucide icon. kind: rings | blocks | arc."""
    c = dz["colors"]
    r = random.Random(dz["seed"] * 101 + idx)
    pr, ac, bg, tx = c["pr"], c["ac"], c["bg1"], c["tx"]
    ink = c["bt"]
    ic = names[0] if names else "sparkles"
    parts = []
    cx, cy = w / 2, h / 2
    m = min(w, h)
    if kind == "rings":
        for k, f in enumerate((0.48, 0.36, 0.25)):
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{m * f:.0f}" fill="{pr if k == 2 else "none"}" fill-opacity="1" stroke="{pr}" stroke-opacity="{_op(.55 - k * .12)}" stroke-width="{3 if k < 2 else 0}"/>')
        parts.append(f'<circle cx="{cx + m * .34 * math.cos(.9):.0f}" cy="{cy - m * .34 * math.sin(.9):.0f}" r="{m * .05:.0f}" fill="{pr}" fill-opacity=".6"/>')
        s = m * 0.24
        parts.append(f'<svg x="{cx - s / 2:.0f}" y="{cy - s / 2:.0f}" width="{s:.0f}" height="{s:.0f}" viewBox="0 0 24 24" style="color:{ink}" stroke-width="1.4"><use href="#lucide-{ic}"/></svg>')
    elif kind == "blocks":
        n = 5
        bw = w / (n * 1.4)
        for k in range(n):
            bh = h * (0.28 + 0.14 * k) * (0.9 + r.random() * .1)
            x = w * 0.08 + k * bw * 1.4
            col = pr if k == n - 1 else c["card"]
            parts.append(f'<rect x="{x:.0f}" y="{h - bh:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="{bw * .22:.0f}" fill="{col}" fill-opacity="{1 if k == n - 1 else _op(.55 + k * .08)}"/>')
        s = bw * 0.62
        x = w * 0.08 + (n - 1) * bw * 1.4 + (bw - s) / 2
        parts.append(f'<svg x="{x:.0f}" y="{h - h * (0.28 + 0.14 * (n - 1)) + 36:.0f}" width="{s:.0f}" height="{s:.0f}" viewBox="0 0 24 24" style="color:{ink}" stroke-width="1.6"><use href="#lucide-{ic}"/></svg>')
    else:  # arc
        parts.append(f'<circle cx="{cx}" cy="{h * .56:.0f}" r="{m * .36:.0f}" fill="{pr}"/><circle cx="{cx}" cy="{h * .56:.0f}" r="{m * .46:.0f}" fill="none" stroke="{pr}" stroke-opacity=".35" stroke-width="3"/>')
        parts.append(f'<path d="M{w * .06:.0f} {h * .94:.0f}H{w * .94:.0f}" stroke="{tx}" stroke-opacity=".25" stroke-width="3"/>')
        s = m * 0.3
        parts.append(f'<svg x="{cx - s / 2:.0f}" y="{h * .56 - s / 2:.0f}" width="{s:.0f}" height="{s:.0f}" viewBox="0 0 24 24" style="color:{ink}" stroke-width="1.4"><use href="#lucide-{ic}"/></svg>')
    return f'<svg class="hero" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">{"".join(parts)}</svg>'


def abstract(dz: dict, w: int, h: int, idx: int = 0) -> str:
    """Icon-free abstract panel art (used on covers): two overlapping discs + one arc line in the accent."""
    c = dz["colors"]
    r = random.Random(dz["seed"] * 53 + idx)
    m = min(w, h)
    a, b = r.uniform(.3, .7), r.uniform(.3, .7)
    parts = [f'<circle cx="{w * a:.0f}" cy="{h * .4:.0f}" r="{m * .36:.0f}" fill="{c["bt"]}" fill-opacity=".16"/>',
             f'<circle cx="{w * b:.0f}" cy="{h * .66:.0f}" r="{m * .22:.0f}" fill="{c["bt"]}" fill-opacity=".22"/>',
             f'<path d="M0 {h * .86:.0f}Q{w / 2:.0f} {h * .5:.0f} {w} {h * .9:.0f}" stroke="{c["bt"]}" stroke-opacity=".5" stroke-width="3" fill="none"/>']
    return f'<svg class="hero" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true">{"".join(parts)}</svg>'
