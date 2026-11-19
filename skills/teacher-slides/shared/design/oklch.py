#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""OKLab / OKLCH utilities (stdlib only): conversion, gamut clamp, contrast fitting, harmonies, equal-perceived-step ramps.

OKLab (Bjorn Ottosson, 2020, public domain matrices) is a colour space where equal numeric steps look about equally different, so
"same hue, lighter" and "10 evenly spaced shades" behave. Colours here are "#rrggbb" strings; L is 0..1, C ~0..0.37, h in degrees.

    from oklch import hex_to_oklch, oklch_to_hex, harmony, ramp, fit_contrast, delta_e
    hex_to_oklch("#ff0000")         # (0.6280, 0.2577, 29.23)
    harmony("#2b6cff", "triad")     # three hexes, hue +0/+120/+240
    ramp("#2b6cff", 5)              # tints/shades at equal OKLab lightness steps (hue and chroma kept, chroma clamped into sRGB)
    fit_contrast("#ff9900", "#ffffff", 4.5)   # darken (lightness only, hue kept) until text passes

CLI:  python3 oklch.py "#ff0000" [--harmony analogous|complementary|triad|split|tetrad] [--ramp 7]
"""
from __future__ import annotations

import argparse
import json
import math
import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HARMONIES = {"analogous": (-30, 0, 30), "complementary": (0, 180), "triad": (0, 120, 240), "split": (0, 150, 210), "tetrad": (0, 90, 180, 270)}


# ---------- sRGB <-> linear ----------
def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """'#rgb' or '#rrggbb' -> (r, g, b) 0..255."""
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: float, g: float, b: float) -> str:
    """0..255 floats (clamped, rounded) -> '#rrggbb'."""
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))


def to_linear(v: float) -> float:
    """sRGB channel 0..1 -> linear light."""
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def to_srgb(v: float) -> float:
    """Linear light -> sRGB channel 0..1."""
    return 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


def hex_to_linear(h: str) -> tuple[float, float, float]:
    r, g, b = hex_to_rgb(h)
    return to_linear(r / 255), to_linear(g / 255), to_linear(b / 255)


def linear_to_hex(r: float, g: float, b: float) -> str:
    return rgb_to_hex(*(to_srgb(max(0.0, min(1.0, v))) * 255 for v in (r, g, b)))


# ---------- linear sRGB <-> OKLab ----------
def linear_to_oklab(r: float, g: float, b: float) -> tuple[float, float, float]:
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def oklab_to_linear(L: float, a: float, b: float) -> tuple[float, float, float]:
    """OKLab -> linear sRGB (NOT clamped: values outside 0..1 mean out of gamut)."""
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def hex_to_oklab(h: str) -> tuple[float, float, float]:
    return linear_to_oklab(*hex_to_linear(h))


def oklab_to_hex(L: float, a: float, b: float) -> str:
    return linear_to_hex(*oklab_to_linear(L, a, b))


# ---------- OKLab <-> OKLCH ----------
def oklab_to_oklch(L: float, a: float, b: float) -> tuple[float, float, float]:
    C = math.hypot(a, b)
    h = math.degrees(math.atan2(b, a)) % 360 if C > 1e-6 else 0.0
    return L, C, h


def oklch_to_oklab(L: float, C: float, h: float) -> tuple[float, float, float]:
    hr = math.radians(h)
    return L, C * math.cos(hr), C * math.sin(hr)


def hex_to_oklch(h: str) -> tuple[float, float, float]:
    """'#rrggbb' -> (L, C, h)."""
    return oklab_to_oklch(*hex_to_oklab(h))


def in_gamut(L: float, C: float, h: float, eps: float = 1e-4) -> bool:
    """True when the OKLCH colour fits inside sRGB."""
    return all(-eps <= v <= 1 + eps for v in oklab_to_linear(*oklch_to_oklab(L, C, h)))


def clamp_chroma(L: float, C: float, h: float) -> tuple[float, float, float]:
    """Gamut clamp: keep lightness and hue, lower chroma (bisection) until the colour fits sRGB."""
    L = max(0.0, min(1.0, L))
    if in_gamut(L, C, h):
        return L, C, h
    lo, hi = 0.0, C
    for _ in range(24):
        mid = (lo + hi) / 2
        if in_gamut(L, mid, h):
            lo = mid
        else:
            hi = mid
    return L, lo, h


def oklch_to_hex(L: float, C: float, h: float, clamp: bool = True) -> str:
    """OKLCH -> '#rrggbb'. With clamp (default) out-of-gamut chroma is reduced first so hue and lightness stay put."""
    if clamp:
        L, C, h = clamp_chroma(L, C, h)
    return oklab_to_hex(*oklch_to_oklab(L, C, h))


def delta_e(a: str, b: str) -> float:
    """Euclidean distance in OKLab (ΔE_OK) between two hex colours. ~0.02 is barely visible, 0.1 is clearly different."""
    la, lb = hex_to_oklab(a), hex_to_oklab(b)
    return math.dist(la, lb)


# ---------- contrast ----------
def luminance(h: str) -> float:
    """WCAG relative luminance."""
    r, g, b = hex_to_linear(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio of two hex colours (same value as design.contrast)."""
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def fit_contrast(fg: str, bg, ratio: float = 4.5) -> str:
    """Move fg's OKLCH lightness only (hue kept, chroma clamped into gamut) until it reaches `ratio` against bg (one hex or a list: all must pass).

    Goes away from the background(s); if that cannot reach the ratio it tries the other direction; returns the closest try otherwise."""
    bgs = [bg] if isinstance(bg, str) else list(bg)
    ok = lambda c: min(contrast(c, x) for x in bgs) >= ratio  # noqa: E731
    if ok(fg):
        return fg
    L, C, h = hex_to_oklch(fg)
    mean_bg = sum(hex_to_oklab(x)[0] for x in bgs) / len(bgs)
    first = -1 if L <= mean_bg else 1
    best, best_r = fg, min(contrast(fg, x) for x in bgs)
    for d in (first, -first):
        for i in range(1, 201):
            l2 = L + d * i * 0.005
            if not 0 <= l2 <= 1:
                break
            c = oklch_to_hex(l2, C, h)
            r = min(contrast(c, x) for x in bgs)
            if r >= ratio:
                return c
            if r > best_r:
                best, best_r = c, r
    return best


# ---------- harmonies and ramps ----------
def harmony(seed: str, kind: str = "analogous") -> list[str]:
    """Colours that share the seed's lightness and chroma and rotate hue: analogous(-30,0,+30), complementary(0,180), triad, split(0,150,210), tetrad.

    The seed itself is returned unchanged where the offset is 0 (so the list always contains the user's own colour)."""
    if kind not in HARMONIES:
        raise ValueError(f"harmony must be one of {', '.join(HARMONIES)}")
    L, C, h = hex_to_oklch(seed)
    return [seed.lower() if off == 0 else oklch_to_hex(L, C, (h + off) % 360) for off in HARMONIES[kind]]


def ramp(seed: str, n: int = 5, l_min: float = 0.25, l_max: float = 0.95) -> list[str]:
    """n colours from dark to light at equal OKLab lightness steps, same hue and chroma as the seed (chroma clamped, so very light/dark ends are less saturated)."""
    if n < 2:
        return [seed.lower()]
    _, C, h = hex_to_oklch(seed)
    return [oklch_to_hex(l_min + (l_max - l_min) * i / (n - 1), C, h) for i in range(n)]


def tints_shades(seed: str, steps: int = 2, step: float = 0.08) -> dict:
    """{'tints': [lighter...], 'shades': [darker...]}, each `step` of OKLab lightness apart (equal perceived steps), hue kept."""
    L, C, h = hex_to_oklch(seed)
    return {"tints": [oklch_to_hex(min(0.99, L + step * i), C, h) for i in range(1, steps + 1)],
            "shades": [oklch_to_hex(max(0.05, L - step * i), C, h) for i in range(1, steps + 1)]}


def hue_distance(a: float, b: float) -> float:
    """Shortest angle between two hues, 0..180."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("color")
    ap.add_argument("--harmony", choices=list(HARMONIES))
    ap.add_argument("--ramp", type=int)
    a = ap.parse_args()
    L, C, h = hex_to_oklch(a.color)
    out = {"hex": a.color.lower(), "oklch": [round(L, 4), round(C, 4), round(h, 1)]}
    if a.harmony:
        out["harmony"] = harmony(a.color, a.harmony)
    if a.ramp:
        out["ramp"] = ramp(a.color, a.ramp)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
