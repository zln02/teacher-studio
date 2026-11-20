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
    try:  # the shared picker knows more words (and checks that the icon exists); the short table below stays as the fallback
        import deck_icons
        n = deck_icons.name(w)
        if n and deck_icons.exists(n):
            return n
    except Exception:
        pass
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
    """Slide background SVG: a flat tonal field + ONE quiet structural motif. role: cover | section | content.

    Matte by rule (shared/design/DESIGN-RULES.md): tonal planes, hairlines, fine grain, at most one accent shape. No radial glow, no blur filter,
    no light beams, no scattered confetti. The motif moves with the seed and the slide index, so decks do not share a skeleton.
    Motifs: dotgrid frame blocks papercut panels planes halftone bands hills pixel minimal chalk."""
    c, gen, seed = dz["colors"], dz["lang"]["bg"], dz["seed"]
    gen = {"neongrid": "dotgrid", "bokeh": "frame", "memphis": "blocks", "bunting": "papercut", "stage": "panels", "glassblobs": "planes", "speed": "halftone",
           "leaves": "bands"}.get(gen, gen)
    r = random.Random(seed * 7919 + idx * 31)
    s = {"cover": 1.0, "section": 0.9, "content": 0.5}.get(role, 0.5)
    cx, cy = CORNERS[(idx + seed) % 4]
    right, top = cx > 0, cy == 0
    uid = f"g{idx}"
    defs = (f'<linearGradient id="{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["bg1"]}"/><stop offset="1" stop-color="{c["bg2"]}"/></linearGradient>')
    body = [f'<rect width="1920" height="1080" fill="url(#{uid})"/>']
    pr, ac, tx, line = c["pr"], c["ac"], c["tx"], c["line"]
    big = role != "content"
    if gen == "dotgrid":
        dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.6"/>' for y in range(36, 1080, 72) for x in range(36, 1920, 72))
        body.append(f'<g fill="{tx}" fill-opacity="{_op(.10 if big else .06)}">{dots}</g>')
        y = 150 if top else 930
        body.append(f'<rect x="96" y="{y}" width="1728" height="2" fill="{tx}" fill-opacity=".14"/><rect x="{96 if not right else 1704}" y="{y - 6}" width="120" height="8" fill="{pr}"/>')
    elif gen == "frame":
        m = 44 if big else 36
        body.append(f'<rect x="{m}" y="{m}" width="{1920 - 2 * m}" height="{1080 - 2 * m}" fill="none" stroke="{pr}" stroke-opacity="{_op(.6 if big else .3)}" stroke-width="2"/>')
        if big:
            body.append(f'<rect x="{m + 12}" y="{m + 12}" width="{1920 - 2 * m - 24}" height="{1080 - 2 * m - 24}" fill="none" stroke="{pr}" stroke-opacity=".28" stroke-width="1"/>')
    elif gen == "blocks":
        # the corner block always sits on the RIGHT edge (text starts on the left), top or bottom by seed: it never runs under a title or kicker
        rad = 300 if big else 190
        body.append(f'<circle cx="1920" cy="{cy}" r="{rad}" fill="{pr}" fill-opacity="{_op(1 if big else .14)}"/>')
        if big:
            by = 1080 - 96 if top else 0
            body.append(f'<rect x="1344" y="{by}" width="384" height="96" fill="{ac}"/><rect x="1248" y="{by}" width="96" height="96" fill="{tx}"/>')
    elif gen == "papercut":
        n, hgt = 10, (88 if big else 46)
        sh = []
        for k in range(n):
            x = 96 + k * 192
            col = (pr, ac)[(k + seed) % 2]
            op = _op(1 if big else .35)
            kind = (k + seed + idx) % 3
            if kind == 0:
                sh.append(f'<path d="M{x - hgt} 0a{hgt} {hgt} 0 0 0 {2 * hgt} 0z" fill="{col}" fill-opacity="{op}"/>')
            elif kind == 1:
                sh.append(f'<path d="M{x - hgt} 0h{2 * hgt}l{-hgt} {hgt * 1.1:.0f}z" fill="{col}" fill-opacity="{op}"/>')
            else:
                sh.append(f'<rect x="{x - hgt * .7:.0f}" y="0" width="{hgt * 1.4:.0f}" height="{hgt * .8:.0f}" fill="{col}" fill-opacity="{op}"/>')
        body.append("".join(sh))
    elif gen == "panels":
        n = (6, 8, 10)[(seed + idx) % 3]
        w = 1920 / n
        body.append("".join(f'<rect x="{k * w:.0f}" y="0" width="{w + 1:.0f}" height="1080" fill="{tx}" fill-opacity="{_op(.035 if big else .02)}"/>' for k in range(0, n, 2)))
        body.append(f'<rect x="0" y="{918 if big else 1000}" width="1920" height="{6 if big else 3}" fill="{pr}" fill-opacity="{_op(1 if big else .5)}"/>')
    elif gen == "planes":
        x0 = (1040, 1200, 880, 1320)[(seed + idx) % 4] if right else (880, 720, 1040, 600)[(seed + idx) % 4]
        if right:
            body.append(f'<path d="M{x0} 0H1920V1080H{x0 - 480}z" fill="{tx}" fill-opacity="{_op(.045 * s + .01)}"/><path d="M{x0 + 420} 0H1920V1080H{x0 - 60}z" fill="{tx}" fill-opacity="{_op(.045 * s + .01)}"/>')
        else:
            body.append(f'<path d="M0 0H{x0}L{x0 - 480} 1080H0z" fill="{tx}" fill-opacity="{_op(.045 * s + .01)}"/><path d="M0 0H{x0 - 420}L{x0 - 900} 1080H0z" fill="{tx}" fill-opacity="{_op(.045 * s + .01)}"/>')
    elif gen == "halftone":
        dots = []
        for j in range(22):
            for k in range(30):
                rr = 8 - (k * k + j * j) ** 0.5 * 0.3
                if rr > 0.7:
                    dots.append(f'<circle cx="{(1896 - k * 26) if right else (24 + k * 26)}" cy="{(24 + j * 26) if top else (1056 - j * 26)}" r="{rr:.1f}"/>')
        body.append(f'<g fill="{tx}" fill-opacity="{_op(.2 if big else .1)}">{"".join(dots)}</g>')
        if big:
            body.append(f'<rect x="0" y="1056" width="1920" height="24" fill="{tx}"/>')
    elif gen == "bands":
        n = 3 if big else 2
        hgt = 62 if big else 34
        for k in range(n):
            y = 1080 - (n - k) * hgt
            amp = 14 + 4 * k
            ph = (seed + idx + k * 2) % 5 * 120
            d = f"M0 {y}C{480 + ph % 200} {y - amp} {900 + ph % 300} {y + amp} 1320 {y - amp / 2:.0f}S1800 {y + amp} 1920 {y}V1080H0z"
            body.append(f'<path d="{d}" fill="{pr}" fill-opacity="{_op(.10 + .09 * k)}"/>')
    elif gen == "hills":
        h = 230 if big else 120
        p1 = f"M0 {1080 - h}C400 {1080 - h - 90} 800 {1080 - h + 40} 1200 {1080 - h - 30}S1700 {1080 - h - 80} 1920 {1080 - h - 20}V1080H0z"
        p2 = f"M0 {1080 - h * .55:.0f}C500 {1080 - h * .9:.0f} 900 {1080 - h * .3:.0f} 1400 {1080 - h * .7:.0f}S1800 {1080 - h * .5:.0f} 1920 {1080 - h * .6:.0f}V1080H0z"
        body.append(f'<path d="{p1}" fill="{pr}" fill-opacity="{_op(.12 + .05 * s)}"/><path d="{p2}" fill="{ac}" fill-opacity="{_op(.18 + .05 * s)}"/>')
    elif gen == "pixel":
        u = 48 if big else 32
        sq = []
        for k in range(7 if big else 4):
            for j in range(k + 1):
                x = (1920 - (k + 1) * u) if cx else k * u
                y = 1080 - (j + 1) * u
                sq.append(f'<rect x="{x}" y="{y}" width="{u}" height="{u}"/>')
        body.append(f'<g fill="{pr}" fill-opacity="{_op(.22 * s + .06)}">{"".join(sq)}</g>')
    elif gen == "minimal":
        body.append(f'<rect x="96" y="{96 if top else 982}" width="1728" height="2" fill="{tx}" fill-opacity=".14"/>')
        if big:
            body.append(f'<rect x="{96 if not right else 1704}" y="{90 if top else 976}" width="120" height="8" fill="{pr}"/>')
    elif gen == "chalk":
        body.append(f'<rect x="48" y="48" width="1824" height="984" rx="14" fill="none" stroke="{tx}" stroke-opacity=".4" stroke-width="3" stroke-dasharray="26 14"/>')
        dots = "".join(f'<circle cx="{r.randint(60, 1860)}" cy="{r.randint(60, 1020)}" r="{r.choice((1.5, 2, 3))}"/>' for _ in range(40))
        body.append(f'<g fill="{tx}" fill-opacity=".10">{dots}</g>')
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
