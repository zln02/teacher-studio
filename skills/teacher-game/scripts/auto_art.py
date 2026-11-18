# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""First-party art for the auto theme: coloured sea props, animal hosts (4 moods), sticker badges, card patterns, prop tags.

Everything here is original vector art written for this project (no third-party files). Tabler icons (MIT, shared/assets)
are wrapped into coloured "sticker" badges so props are never thin grey line icons.
"""
from __future__ import annotations

import math
import re
import urllib.parse

INK = "#1a1030"

# ---- tags: a prop is relevant to a world when their tags intersect (design_review checks this) ----
PROP_TAGS: dict[str, set] = {
    # sea (own coloured art)
    "fish": {"sea", "animal"}, "shell": {"sea"}, "starfish": {"sea"}, "whale": {"sea", "animal"}, "anchor": {"sea"}, "seaweed": {"sea", "nature"}, "bubble": {"sea"}, "crab": {"sea", "animal"},
    # tabler stickers
    "planet": {"space"}, "rocket": {"space", "science"}, "satellite": {"space"}, "ufo": {"space"}, "stars": {"space", "fairy", "luxe"}, "alien": {"space"}, "telescope": {"space", "science"}, "moon": {"space", "tense"},
    "crown": {"fairy", "luxe"}, "building-castle": {"fairy", "history"}, "butterfly": {"fairy", "nature"}, "flower": {"fairy", "nature", "warm"}, "rainbow": {"fairy"}, "sparkles": {"fairy", "luxe"}, "feather": {"fairy", "history"},
    "key": {"tense"}, "lock": {"tense"}, "clock": {"tense"}, "hourglass": {"tense", "history"}, "ghost": {"tense"}, "alarm": {"tense"}, "eye": {"tense"}, "shield": {"tense", "history"},
    "trophy": {"luxe", "sports"}, "gift": {"luxe", "warm"}, "cake": {"luxe", "warm"}, "balloon": {"luxe", "warm"}, "medal": {"luxe", "sports"}, "confetti": {"luxe", "sports"},
    "heart": {"warm"}, "sun": {"warm", "nature"}, "home": {"warm"}, "coffee": {"warm"},
    "leaf": {"nature"}, "tree": {"nature"}, "trees": {"nature"}, "bug": {"nature"}, "paw": {"nature", "animal"},
    "flag": {"history", "sports"}, "sword": {"history"}, "map": {"history"}, "book": {"history", "science"}, "compass": {"history"}, "mountain": {"history", "nature"}, "brush": {"history"}, "writing": {"history"},
    "target": {"sports"}, "bike": {"sports"}, "stopwatch": {"sports"}, "award": {"sports", "luxe"}, "bolt": {"sports", "science"},
    "atom": {"science"}, "flask": {"science"}, "microscope": {"science"}, "bulb": {"science", "generic"}, "calculator": {"science"}, "dna": {"science"}, "magnet": {"science"}, "robot": {"science"},
    "star": {"generic"}, "puzzle": {"generic"}, "heart-generic": {"generic"},
}
WORLD_TAGS = {"space": {"space"}, "sea": {"sea"}, "fairy": {"fairy"}, "tense": {"tense"}, "luxe": {"luxe"}, "warm": {"warm"}, "forest": {"nature"}, "hanok": {"history"},
              "sports": {"sports"}, "science": {"science"}, "generic": {"generic", "science"}}


def _mix(a: str, b: str, t: float) -> str:
    x = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    y = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x[i] + (y[i] - x[i]) * t) for i in range(3))


# ---- coloured sea props (viewBox 0 0 100 100) ----
SEA_PROPS = {
    "fish": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M78 50 L98 30 L96 70Z" fill="#ff9a3c" stroke="#1a1030" stroke-width="4" stroke-linejoin="round"/><ellipse cx="46" cy="50" rx="38" ry="26" fill="#ffb84d" stroke="#1a1030" stroke-width="4"/><path d="M40 26 Q52 14 62 28" fill="#ff9a3c" stroke="#1a1030" stroke-width="4" stroke-linejoin="round"/><path d="M52 28 Q60 50 52 72" fill="none" stroke="#fff3d6" stroke-width="5" stroke-linecap="round"/><circle cx="28" cy="44" r="6" fill="#fff" stroke="#1a1030" stroke-width="3"/><circle cx="27" cy="44" r="2.6" fill="#1a1030"/><path d="M18 58 Q24 62 30 58" fill="none" stroke="#1a1030" stroke-width="3" stroke-linecap="round"/></svg>',
    "shell": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M10 62 Q8 22 50 14 Q92 22 90 62 Q86 82 50 86 Q14 82 10 62Z" fill="#ffb3c7" stroke="#1a1030" stroke-width="4" stroke-linejoin="round"/><path d="M50 86 L30 24 M50 86 L50 16 M50 86 L70 24 M50 86 L16 40 M50 86 L84 40" stroke="#e0709a" stroke-width="4" stroke-linecap="round" fill="none"/><rect x="38" y="84" width="24" height="10" rx="4" fill="#ff8fb0" stroke="#1a1030" stroke-width="4"/></svg>',
    "starfish": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M50 8 L61 36 L92 38 L68 58 L77 90 L50 72 L23 90 L32 58 L8 38 L39 36Z" fill="#ff8a5c" stroke="#1a1030" stroke-width="4" stroke-linejoin="round"/><circle cx="50" cy="42" r="4" fill="#ffd0a8"/><circle cx="50" cy="26" r="3" fill="#ffd0a8"/><circle cx="36" cy="56" r="3" fill="#ffd0a8"/><circle cx="64" cy="56" r="3" fill="#ffd0a8"/><circle cx="44" cy="52" r="2.6" fill="#1a1030"/><circle cx="56" cy="52" r="2.6" fill="#1a1030"/></svg>',
    "whale": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M60 22 Q64 8 56 4 M60 22 Q70 10 78 14" fill="none" stroke="#8fd8ff" stroke-width="5" stroke-linecap="round"/><path d="M8 58 Q8 26 46 26 Q82 26 86 54 Q96 46 96 32 Q96 62 82 72 Q70 84 40 84 Q8 84 8 58Z" fill="#4aa3df" stroke="#1a1030" stroke-width="4" stroke-linejoin="round"/><path d="M14 66 Q40 80 76 70 Q60 84 36 82 Q16 80 14 66Z" fill="#cfeeff"/><circle cx="28" cy="52" r="5" fill="#fff" stroke="#1a1030" stroke-width="3"/><circle cx="28" cy="52" r="2.4" fill="#1a1030"/><path d="M22 66 Q30 72 38 66" fill="none" stroke="#1a1030" stroke-width="3.5" stroke-linecap="round"/></svg>',
    "anchor": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g fill="none" stroke="#1a1030" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"><circle cx="50" cy="20" r="8"/><path d="M50 28 V84 M30 46 H70 M14 62 Q18 86 50 88 Q82 86 86 62"/></g><g fill="none" stroke="#3b82c4" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"><circle cx="50" cy="20" r="8"/><path d="M50 28 V84 M30 46 H70 M14 62 Q18 86 50 88 Q82 86 86 62"/></g></svg>',
    "seaweed": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g fill="none" stroke-linecap="round"><path d="M30 96 Q10 70 30 50 Q50 30 30 6" stroke="#1a1030" stroke-width="16"/><path d="M62 96 Q46 76 62 58 Q78 40 62 22" stroke="#1a1030" stroke-width="16"/><path d="M30 96 Q10 70 30 50 Q50 30 30 6" stroke="#3ccf7e" stroke-width="9"/><path d="M62 96 Q46 76 62 58 Q78 40 62 22" stroke="#26a862" stroke-width="9"/></g></svg>',
    "bubble": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g stroke="#1a1030" stroke-width="4"><circle cx="38" cy="62" r="26" fill="#bfeaff"/><circle cx="72" cy="30" r="15" fill="#d9f3ff"/><circle cx="76" cy="74" r="9" fill="#d9f3ff"/></g><path d="M26 56 Q28 46 38 42" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/></svg>',
    "crab": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g stroke="#1a1030" stroke-width="4" stroke-linejoin="round"><path d="M16 50 Q2 40 8 24 Q22 26 26 42Z" fill="#ff6b5c"/><path d="M84 50 Q98 40 92 24 Q78 26 74 42Z" fill="#ff6b5c"/><ellipse cx="50" cy="60" rx="32" ry="22" fill="#ff6b5c"/></g><path d="M22 74 L12 86 M36 80 L32 92 M64 80 L68 92 M78 74 L88 86" stroke="#1a1030" stroke-width="5" stroke-linecap="round"/><circle cx="40" cy="48" r="7" fill="#fff" stroke="#1a1030" stroke-width="3"/><circle cx="60" cy="48" r="7" fill="#fff" stroke="#1a1030" stroke-width="3"/><circle cx="40" cy="49" r="3" fill="#1a1030"/><circle cx="60" cy="49" r="3" fill="#1a1030"/><path d="M42 64 Q50 70 58 64" fill="none" stroke="#1a1030" stroke-width="3.5" stroke-linecap="round"/></svg>',
}


def sticker(tabler_svg: str, color: str) -> str:
    """Wrap a Tabler outline icon into a coloured round sticker (white icon on a colour disc with an ink outline)."""
    s = re.sub(r"<!--.*?-->", "", tabler_svg, flags=re.S)
    inner = re.search(r"<svg[^>]*>(.*)</svg>", s, re.S).group(1)
    inner = re.sub(r'<path stroke="none"[^>]*/>', "", inner)
    inner = re.sub(r"\s+", " ", inner).strip()
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%s" stroke="%s" stroke-width="1.2"/>'
            '<circle cx="12" cy="12" r="9" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width=".6"/>'
            '<g transform="translate(4.8 4.8) scale(.6)" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">%s</g></svg>') % (color, INK, inner)


# ---- card patterns (tile SVG as CSS data URI) ----
def _pat_body(kind: str, c: str, a: float) -> str:
    o = f'fill="{c}" fill-opacity="{a}"'
    if kind == "waves":
        return f'<path d="M0 14 Q10 6 20 14 T40 14" fill="none" stroke="{c}" stroke-opacity="{a}" stroke-width="3"/><path d="M0 34 Q10 26 20 34 T40 34" fill="none" stroke="{c}" stroke-opacity="{a}" stroke-width="3"/>'
    if kind in ("stars", "sparkle"):
        return f'<path d="M20 8 L23 17 L32 20 L23 23 L20 32 L17 23 L8 20 L17 17Z" {o}/>'
    if kind == "diamond":
        return f'<path d="M20 6 L34 20 L20 34 L6 20Z" fill="none" stroke="{c}" stroke-opacity="{a}" stroke-width="2.5"/>'
    if kind == "grid":
        return f'<path d="M0 0 H40 M0 0 V40" stroke="{c}" stroke-opacity="{a}" stroke-width="2" fill="none"/>'
    if kind == "leaves":
        return f'<ellipse cx="20" cy="20" rx="12" ry="5" transform="rotate(-35 20 20)" {o}/>'
    if kind == "stripes":
        return f'<path d="M-4 44 L44 -4 M16 44 L44 16 M-4 24 L24 -4" stroke="{c}" stroke-opacity="{a}" stroke-width="5" fill="none"/>'
    return f'<circle cx="10" cy="10" r="4" {o}/><circle cx="30" cy="30" r="4" {o}/>'


def pattern_uri(kind: str, color: str, alpha: float) -> str:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 40 40">{_pat_body(kind, color, alpha)}</svg>'
    return 'url("data:image/svg+xml,' + urllib.parse.quote(svg, safe="/:=\"' ()") .replace('"', "%22") + '")'


# ---- animal hosts: 300x440, groups f-idle/f-happy/f-sad/f-wow ----
def _face(cx: int, cy: int, gap: int = 44) -> str:
    l, r = cx - gap, cx + gap

    def eye(x, rr, dy=0):
        return (f'<circle cx="{x}" cy="{cy + dy}" r="{rr}" fill="#fff" stroke="{INK}" stroke-width="4"/><circle cx="{x + 2}" cy="{cy + dy + 2}" r="{rr * .55:.1f}" fill="{INK}"/>'
                f'<circle cx="{x + 5}" cy="{cy + dy - 3}" r="3" fill="#fff"/>')
    cheeks = f'<ellipse cx="{l - 14}" cy="{cy + 30}" rx="14" ry="8" fill="#ff8fa3" opacity=".6"/><ellipse cx="{r + 14}" cy="{cy + 30}" rx="14" ry="8" fill="#ff8fa3" opacity=".6"/>'
    idle = eye(l, 15) + eye(r, 15) + f'<path d="M{cx - 18} {cy + 32} Q{cx} {cy + 48} {cx + 18} {cy + 32}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    happy = (f'<path d="M{l - 16} {cy + 4} Q{l} {cy - 18} {l + 16} {cy + 4} M{r - 16} {cy + 4} Q{r} {cy - 18} {r + 16} {cy + 4}" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
             f'<path d="M{cx - 24} {cy + 26} Q{cx} {cy + 64} {cx + 24} {cy + 26}Z" fill="#8a1f33" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    sad = (eye(l, 14, 4) + eye(r, 14, 4) + f'<path d="M{l - 18} {cy - 16} L{l + 14} {cy - 8} M{r + 18} {cy - 16} L{r - 14} {cy - 8}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
           f'<path d="M{cx - 16} {cy + 46} Q{cx} {cy + 32} {cx + 16} {cy + 46}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
           f'<path d="M{l - 6} {cy + 26} q-9 16 0 24 q9 -8 0 -24z" fill="#7cc8ff" stroke="{INK}" stroke-width="3"/>')
    wow = eye(l, 19, -2) + eye(r, 19, -2) + f'<ellipse cx="{cx}" cy="{cy + 42}" rx="12" ry="16" fill="#8a1f33" stroke="{INK}" stroke-width="5"/>'
    return (f'<g class="f f-idle">{cheeks}{idle}</g><g class="f f-happy">{cheeks}{happy}</g><g class="f f-sad">{sad}</g><g class="f f-wow">{cheeks}{wow}</g>')


def animal_host(species: str) -> str:
    shadow = '<ellipse cx="150" cy="430" rx="100" ry="11" fill="rgba(0,0,0,.3)"/>'
    if species == "whale":
        body = (f'<path d="M262 330 Q300 290 280 250 Q270 300 232 316Z" fill="#3b8fd0" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
                f'<path d="M140 80 Q130 40 100 30 M160 80 Q170 40 196 34 M150 78 V28" fill="none" stroke="#8fd8ff" stroke-width="9" stroke-linecap="round"/>'
                f'<ellipse cx="150" cy="260" rx="128" ry="150" fill="#4aa3df" stroke="{INK}" stroke-width="8"/>'
                f'<path d="M60 300 Q150 400 240 300 Q220 410 150 414 Q80 410 60 300Z" fill="#cfeeff"/>'
                f'<ellipse cx="36" cy="300" rx="24" ry="40" transform="rotate(20 36 300)" fill="#3b8fd0" stroke="{INK}" stroke-width="7"/>'
                f'<ellipse cx="264" cy="300" rx="24" ry="40" transform="rotate(-20 264 300)" fill="#3b8fd0" stroke="{INK}" stroke-width="7"/>')
        return f'<svg viewBox="0 0 300 440" width="300" height="440" xmlns="http://www.w3.org/2000/svg">{shadow}{body}{_face(150, 210)}</svg>'
    if species == "octopus":
        tent = "".join(f'<path d="M{x} 300 Q{x - 24} 360 {x + 8} 392 Q{x + 30} 410 {x + 10} 424" fill="none" stroke="{INK}" stroke-width="30" stroke-linecap="round"/>'
                       f'<path d="M{x} 300 Q{x - 24} 360 {x + 8} 392 Q{x + 30} 410 {x + 10} 424" fill="none" stroke="#9b6bdb" stroke-width="20" stroke-linecap="round"/>' for x in (66, 108, 150, 192, 234))
        body = tent + (f'<ellipse cx="150" cy="190" rx="116" ry="138" fill="#9b6bdb" stroke="{INK}" stroke-width="8"/>'
                       f'<circle cx="104" cy="96" r="12" fill="#c6a6f2"/><circle cx="196" cy="110" r="8" fill="#c6a6f2"/><circle cx="150" cy="70" r="7" fill="#c6a6f2"/>')
        return f'<svg viewBox="0 0 300 440" width="300" height="440" xmlns="http://www.w3.org/2000/svg">{shadow}{body}{_face(150, 200)}</svg>'
    # puffer fish
    spikes = "".join(f'<path d="M{150 + 112 * math.cos(a):.0f} {240 + 112 * math.sin(a):.0f} l{22 * math.cos(a):.0f} {22 * math.sin(a):.0f}" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
                     for a in [i * 0.52 + 0.1 for i in range(12)])
    body = (spikes + f'<ellipse cx="150" cy="250" rx="122" ry="126" fill="#ffc94a" stroke="{INK}" stroke-width="8"/>'
            f'<path d="M50 300 Q150 410 250 300 Q230 400 150 404 Q70 400 50 300Z" fill="#fff0b8"/>'
            f'<path d="M24 240 Q-4 214 6 190 Q34 204 40 236Z" fill="#ff9a3c" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M276 240 Q304 214 294 190 Q266 204 260 236Z" fill="#ff9a3c" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M90 140 Q150 100 210 140" fill="none" stroke="#ff9a3c" stroke-width="12" stroke-linecap="round"/>')
    return f'<svg viewBox="0 0 300 440" width="300" height="440" xmlns="http://www.w3.org/2000/svg">{shadow}{body}{_face(150, 235)}</svg>'
