#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""The studio design system: ONE source for type, spacing, grids, colour ramps, ornaments and motion (stdlib only).

Every weapon (game, slides, shell kit / 콘티 / direction cards, web app, class tools, data report, documents) reads these
numbers instead of inventing its own. Rules in words: DESIGN-RULES.md (same folder). The user's own template / palette /
font always wins: nothing here is applied over a user design.

    import system as ds
    ds.STACK_SANS                      # font-family value: "TS Sans" (Pretendard subset, OFL) -> Noto Sans KR -> system
    ds.size("stage", "h1")             # 96   (px on the 1920x1080 stage)   roles: display h1 h2 h3 lead body label caption
    ds.tracking(96) / ds.leading(96) / ds.weight(96)      # optical compensation by size: -0.045em / 1.1 / 700
    ds.SPACE                           # 8pt rhythm: 4 8 12 16 24 32 48 64 96 128
    ds.GRIDS["ledger"]                 # named layout grids (columns, margins, gutter, zones)
    ds.MOTION                          # durations (ms) and easing curves
    ds.ramp("#2f5bea")                 # 11-step tonal ramp (50..950) in OKLCH, hue kept, chroma tapered at the ends
    ds.neutral_ramp(hue=250)           # the grey ramp, slightly tinted toward the brand hue
    ds.palette("dark", 250, (0.80, 0.07, 215), (0.77, 0.10, 75))    # a balanced 11-key palette (contrast fitted)
    ds.css_vars("stage")               # ":root{--ds-...}" custom properties
    ds.type_css()                      # typographic detailing every page gets (tabular figures, Korean line breaking ...)
    ds.polish_css("game")              # the anti-「밤티」 layer for one weapon: game | deck | shell | web | print

CLI:  python3 system.py --show            # print the scale, spacing, grids, motion
      python3 system.py --ramp "#2f5bea"  # print a ramp
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oklch  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

# ------------------------------------------------------------------ type ------------------------------------------------------------------
FONT_SANS = "TS Sans"            # Pretendard 1.3.9 subset, renamed (Reserved Font Name), SIL OFL 1.1: shared/fonts
FONT_SERIF = "Noto Serif KR"     # only for styles that are editorial by design (never on cream paper: ai_look.py)
STACK_SANS = '"TS Sans","Pretendard Variable","Pretendard","Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif'
STACK_SERIF = '"Noto Serif KR","Nanum Myeongjo","Batang",serif'
STACK_MONO = '"D2Coding","Consolas","SFMono-Regular","Menlo",monospace'
SERIFS = {"Noto Serif KR", "Gowun Batang", "Nanum Myeongjo", "Song Myung"}

# One modular scale per canvas. stage = 1920x1080 (ratio ~1.3, the owner-approved deck steps), web = rem (1.25), print = pt (1.2).
SCALE = {
    "stage": {"caption": 24, "label": 28, "body": 36, "lead": 44, "h3": 56, "h2": 72, "h1": 96, "display": 132},
    "web": {"caption": 0.8, "label": 0.9, "body": 1.0, "lead": 1.25, "h3": 1.25, "h2": 1.56, "h1": 1.95, "display": 2.44},
    "print": {"caption": 9, "label": 10, "body": 11, "lead": 13, "h3": 13, "h2": 16, "h1": 19, "display": 23},
}
UNIT = {"stage": "px", "web": "rem", "print": "pt"}
FLOOR = {"stage": 22, "web": 0.75, "print": 9}   # nothing smaller is ever set
MAX_WEIGHT = 800                                  # 900 looks like a default "impact" face; big type gets lighter, not heavier


def size(canvas: str, role: str):
    return SCALE[canvas][role]


def tracking(px: float) -> float:
    """Letter-spacing (em) by size: big type is tightened, small labels are opened (optical compensation; the face has no opsz axis)."""
    if px >= 96:
        return -0.045
    if px >= 60:
        return -0.035
    if px >= 36:
        return -0.022
    if px >= 24:
        return -0.012
    return 0.0


def leading(px: float) -> float:
    """Line-height by size (Korean needs a little more than Latin at text sizes)."""
    if px >= 96:
        return 1.1
    if px >= 56:
        return 1.18
    if px >= 40:
        return 1.28
    return 1.5


def weight(px: float, strong: bool = True) -> int:
    """Weight by size: the bigger the type, the lighter it can be (never above MAX_WEIGHT)."""
    if not strong:
        return 500 if px < 40 else 600
    return 700 if px >= 96 else (760 if px >= 56 else MAX_WEIGHT)


LABEL_TRACKING = 0.06   # small caps-like labels / kickers (em)

# ------------------------------------------------------------------ space + grids ----------------------------------------------------------
SPACE = (4, 8, 12, 16, 24, 32, 48, 64, 96, 128)   # 8pt rhythm (4 = the half step for icon gaps only)
RADII = {"none": 0, "hair": 2, "soft": 8, "card": 16, "round": 28, "pill": 999}
# Named grids on the 1920x1080 stage (12 columns, 96px margins, 32px gutter): each zone is (first column, span). A layout names a grid.
GRIDS = {
    "poster":    {"cols": 12, "margin": 96, "gutter": 32, "zones": {"main": (3, 8)}, "align": "center", "note": "one centred column, big type, wide margins"},
    "editorial": {"cols": 12, "margin": 96, "gutter": 32, "zones": {"main": (1, 7), "side": (9, 4)}, "align": "left", "note": "asymmetric 7/4 with a hairline between"},
    "ledger":    {"cols": 12, "margin": 96, "gutter": 32, "zones": {"label": (1, 3), "main": (4, 9)}, "align": "left", "note": "narrow label column + content (reports, public)"},
    "split":     {"cols": 12, "margin": 96, "gutter": 32, "zones": {"left": (1, 6), "right": (7, 6)}, "align": "left", "note": "two equal halves"},
    "bento":     {"cols": 12, "margin": 96, "gutter": 24, "zones": {"a": (1, 5), "b": (6, 4), "c": (10, 3)}, "align": "left", "note": "unequal tiles, one hero tile"},
    "stack":     {"cols": 12, "margin": 96, "gutter": 32, "zones": {"main": (2, 10)}, "align": "left", "note": "rows under one headline"},
    "swiss":     {"cols": 12, "margin": 128, "gutter": 32, "zones": {"text": (1, 6), "picture": (7, 6)}, "align": "left", "note": "preset E: 12 columns, 128 margins, text left 6 / picture right 6, big type spans"},
    "web":       {"cols": 12, "margin": 24, "gutter": 24, "max": 1200, "zones": {"main": (1, 8), "side": (9, 4)}, "align": "left", "note": "responsive page"},
    "print-a4":  {"cols": 6, "margin": "20mm", "gutter": "5mm", "zones": {"main": (1, 6)}, "align": "left", "note": "A4 portrait, 6 columns"},
}
SAFE = 70   # px on the stage: nothing essential closer to the edge

# ------------------------------------------------------------------ motion ----------------------------------------------------------------
MOTION = {
    "dur": {"instant": 90, "fast": 160, "base": 240, "slow": 420, "scene": 700},
    "ease": {"standard": "cubic-bezier(.2,0,0,1)", "enter": "cubic-bezier(.16,1,.3,1)", "exit": "cubic-bezier(.4,0,1,1)", "emphasis": "cubic-bezier(.34,1.3,.64,1)"},
    "stagger": 60,
    "rules": ["one thing moves per beat", "enter = fade + 12-24px travel, never a spin", "exit is faster than enter", "prefers-reduced-motion: no travel"],
}

# ------------------------------------------------------------------ colour ----------------------------------------------------------------
RAMP_STEPS = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950)
_RAMP_L = (0.975, 0.945, 0.89, 0.82, 0.73, 0.64, 0.55, 0.46, 0.37, 0.28, 0.20)
MAX_ACCENT_CHROMA = 0.17     # above this a colour reads as "neon" on screen (OKLCH C); state colours (good/bad) are exempt
MAX_ACCENT_AREA = 0.05       # share of the screen an accent may cover


def ramp(seed: str) -> dict:
    """{50: hex ... 950: hex}: a tonal ramp on the seed's hue. Lightness is a fixed ladder; chroma peaks mid-ramp and tapers at both ends."""
    _L, C, h = oklch.hex_to_oklch(seed)
    out = {}
    for step, L in zip(RAMP_STEPS, _RAMP_L):
        taper = 1 - abs(L - 0.6) / 0.6      # 1 at mid lightness, ~0.4 at the ends
        out[step] = oklch.oklch_to_hex(L, C * max(0.25, min(1.0, 0.35 + taper)), h)
    return out


def neutral_ramp(hue: float = 250.0, chroma: float = 0.008) -> dict:
    """The grey ramp, tinted a little toward the brand hue so greys and colours belong together (never pure #808080)."""
    return {step: oklch.oklch_to_hex(L, chroma, hue) for step, L in zip(RAMP_STEPS, _RAMP_L)}


def palette(mode: str, neutral_hue: float, primary: tuple, support: tuple, bg_l: float | None = None, bg_c: float = 0.008) -> dict:
    """A balanced 11-key palette: a tinted neutral ramp for surfaces and text, ONE primary, ONE support. All text pairs are contrast-fitted.

    mode: "dark" | "light".  primary / support: (L, C, h) in OKLCH.  The state colours (good = blue-green, bad = warm red) keep apart for colour-blind eyes."""
    dark = mode == "dark"
    L0 = bg_l if bg_l is not None else (0.175 if dark else 0.972)
    bg1 = oklch.oklch_to_hex(L0, bg_c, neutral_hue)
    bg2 = oklch.oklch_to_hex(L0 + (0.035 if dark else -0.035), bg_c * 1.2, neutral_hue)
    card = oklch.oklch_to_hex(L0 + (0.055 if dark else 0.022), bg_c, neutral_hue) if dark or L0 < 0.975 else "#ffffff"
    text = oklch.oklch_to_hex(0.955 if dark else 0.22, 0.012, neutral_hue)
    pr = oklch.oklch_to_hex(*primary)
    ac = oklch.oklch_to_hex(*support)
    pr = oklch.fit_contrast(pr, [bg1, bg2], 3.0)
    btn = oklch.fit_contrast(oklch.oklch_to_hex(0.18 if oklch.hex_to_oklch(pr)[0] > 0.62 else 0.985, 0.02, primary[2]), pr, 4.5)
    border = oklch.oklch_to_hex(L0 + (0.16 if dark else -0.16), bg_c * 1.5, neutral_hue)
    # good = light teal-blue, bad = deeper orange-red: apart in hue AND lightness, so they survive protan / deutan / tritan simulation
    good = oklch.fit_contrast(oklch.oklch_to_hex(0.86 if dark else 0.44, 0.10 if dark else 0.09, 200 if dark else 225), card, 3.0)
    bad = oklch.fit_contrast(oklch.oklch_to_hex(0.66 if dark else 0.58, 0.17, 35), card, 3.0)
    return {"bg1": bg1, "bg2": bg2, "text": oklch.fit_contrast(text, [bg1, bg2], 7.0), "card": card, "cardText": oklch.fit_contrast(text, card, 7.0),
            "cardBorder": border, "primary": pr, "btnText": btn, "accent": ac, "good": good, "bad": bad}


def is_neon(hexc: str) -> bool:
    """True for a fluorescent screen colour (light AND as colourful as it gets): the kind that reads as a neon sign."""
    try:
        L, C, _h = oklch.hex_to_oklch(hexc)
    except Exception:
        return False
    if (C > 0.165 and L > 0.7) or (C > 0.215 and L > 0.6):
        return True
    # hues with a small gamut (cyan, lime) never reach C 0.165: for them "as colourful as the screen can show" is the neon tell
    cmax = oklch.clamp_chroma(L, 0.4, _h)[1]
    return L > 0.7 and C >= 0.11 and cmax > 0 and C / cmax >= 0.9


# ------------------------------------------------------------------ ornaments -------------------------------------------------------------
# The whole ornament vocabulary. A style may use at most TWO of these, and never more than three ornament elements on one screen.
ORNAMENTS = {
    "rule":    "a hairline (1-2px, text colour at 14%) across a column",
    "kicker":  "a 36x2px accent rule before a grey label (the label itself is never accent-coloured)",
    "frame":   "one inset hairline frame around the stage (double for formal styles)",
    "edge":    "a 3-4px accent bar on the left edge of ONE card",
    "corner":  "a quarter-circle or square block bleeding off one corner (flat, one tone)",
    "numeral": "an oversized filled numeral at 8-10% of the text colour (never an outline)",
    "grain":   "a dot grid or paper grain at <= 8% (texture only, never a picture)",
    "hud":     "four 30px corner brackets + a tick ruler along the bottom with the slide's place on it (hairline, <= 16% text colour; preset E)",
}

# ------------------------------------------------------------------ CSS -------------------------------------------------------------------
def css_vars(canvas: str = "stage", prefix: str = "ds") -> str:
    """:root custom properties: scale, spacing, motion, font stacks."""
    u = UNIT[canvas]
    parts = ["--%s-%s:%s%s" % (prefix, k, ("%g" % v), u) for k, v in SCALE[canvas].items()]
    parts += ["--%s-s%d:%dpx" % (prefix, i + 1, v) for i, v in enumerate(SPACE)]
    parts += ["--%s-t-%s:%dms" % (prefix, k, v) for k, v in MOTION["dur"].items()]
    parts += ["--%s-e-%s:%s" % (prefix, k, v) for k, v in MOTION["ease"].items()]
    parts += ["--%s-sans:%s" % (prefix, STACK_SANS), "--%s-serif:%s" % (prefix, STACK_SERIF), "--%s-mono:%s" % (prefix, STACK_MONO)]
    return ":root{" + ";".join(parts) + "}"


def type_css(scope: str = "") -> str:
    """Typographic detailing every page gets. Safe everywhere: unknown properties are ignored by old browsers."""
    s = scope + " " if scope else ""
    root = scope or "html"
    return (
        # no faux bold / italic; kerning on; Korean never breaks inside a word; CJK brackets 「」 and middle dots lose their dead half-width space
        "%s{font-synthesis:none;font-kerning:normal;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;"
        "word-break:keep-all;overflow-wrap:break-word;line-break:strict;text-spacing-trim:space-first;font-feature-settings:'kern','case'}\n"
        "%sh1,%sh2,%sh3,%s.ds-h{text-wrap:balance}\n%sp,%sli,%s.ds-b{text-wrap:pretty}\n"
        # figures line up in scores, timers, tables, page numbers
        "%s.ds-num,%stime,%std,%sth,%soutput{font-variant-numeric:tabular-nums;font-feature-settings:'tnum','kern'}\n"
        "%sem,%si,%scite,%sdfn,%saddress{font-style:normal}\n"       # Korean has no italic: emphasis is weight or colour, never a slanted fake
        % (root, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s, s))


def _deck() -> str:
    return (
        "/* design system polish (deck) */\n"
        ".h,.big,.q,.lead{text-wrap:balance}.sl p,.sl li,.b{text-wrap:pretty}\n"
        ".h{text-shadow:none!important}\n"                                        # no glow / 3D title: the title is type, not an effect
        ".gnum,.bignum,.big,.tdisp,.chip{font-weight:%d!important}\n" % MAX_WEIGHT
        + ".gnum{opacity:.1;-webkit-text-stroke:0}\n"                               # oversized numeral: filled, 10% (ornament 'numeral')
        ".pg,.tdisp,.bignum,.gnum,.chip{font-variant-numeric:tabular-nums;font-feature-settings:'tnum','kern'}\n")


def _game() -> str:
    w = MAX_WEIGHT
    r = ":root body "    # beats the engine's [data-skin=x] .card rules (0,2,0); the style packs in layouts.css come later and win ties
    return (
        "/* design system polish (shared/design/system.py): matte surfaces, one falling shadow, no coloured glow, no hollow type */\n"
        ":root{--glow:none!important;--ds-shadow:0 18px 40px -22px rgba(0,0,0,.55);--ds-press:0 6px 0 rgba(0,0,0,.22)}\n"
        "body{font-weight:500;font-synthesis:none;font-kerning:normal;line-break:strict;text-spacing-trim:space-first}\n"
        + r + ".title{font-weight:760;letter-spacing:-.04em;line-height:1.1;-webkit-text-stroke:0;text-shadow:none;text-wrap:balance}\n"
        + r + ".h1," + r + ".h2{font-weight:%d;letter-spacing:-.035em;text-wrap:balance;text-shadow:none}\n" % w
        + r + ".btn," + r + ".choice," + r + ".badge," + r + ".float," + r + ".mark," + r + ".tname{font-weight:%d;letter-spacing:-.022em}\n" % w
        + r + ".choice{text-wrap:balance}\n"
        + r + ".review li{font-size:var(--t-s,34px);line-height:1.35}\n"   # the wrong-answer list was 30px: below the stage floor
        + r + ".tscore," + r + ".timer," + r + "#timer," + r + ".ts-count," + r + ".score{font-weight:%d;font-variant-numeric:tabular-nums;font-feature-settings:'tnum','kern';text-shadow:none}\n" % w
        + r + ".card," + r + ".choice," + r + ".ts-q," + r + ".ts-tile," + r + ".ts-bin," + r + ".ts-explcard{box-shadow:var(--ds-shadow)}\n"
        + r + ".btn{box-shadow:var(--ds-press)}" + r + ".btn:active," + r + ".btn.pressed{box-shadow:0 2px 0 rgba(0,0,0,.22)}\n"
        + r + ".btn.secondary{box-shadow:inset 0 0 0 3px var(--cardBorder)}\n"
        # state = solid colour + a ring (never a glow), so it also reads on a washed-out projector
        + r + ".choice.correct{box-shadow:0 0 0 6px var(--good),var(--ds-shadow)!important}" + r + ".choice.wrong{box-shadow:0 0 0 6px var(--bad),var(--ds-shadow)!important}\n"
        + r + ".badge.good," + r + ".badge.bad," + r + ".badge.info{box-shadow:var(--ds-shadow)}\n"
        + r + ".team.turn{box-shadow:0 0 0 4px var(--primary);transform:scale(1.04)}\n"
        + r + ".ts-pod.on{box-shadow:0 0 0 4px var(--tc)}" + r + ".ts-lamps i.lit{box-shadow:none}\n")


def _shell() -> str:
    return ("/* design system polish (shell) */.sk-scr{font-synthesis:none;font-kerning:normal;line-break:strict;text-spacing-trim:space-first}"
            ".sk-h{text-wrap:balance}.sk-scr b,.sk-scr strong{font-weight:700}"
            ".sk-num{font-variant-numeric:tabular-nums;font-feature-settings:'tnum','kern'}")


def _web() -> str:
    return ("/* design system polish (web) */\n" + type_css() +
            "h1,h2,h3{letter-spacing:-.022em;line-height:1.2}\n"
            "input,textarea,select,button{letter-spacing:inherit}\n"
            "input[type=number],.num,output,b.num{font-variant-numeric:tabular-nums;font-feature-settings:'tnum','kern'}\n")


def _print() -> str:
    return ("/* design system polish (print) */\n" + type_css() +
            "h1,h2,h3{letter-spacing:-.015em;break-after:avoid}\n"
            "table{font-variant-numeric:tabular-nums}\np,li{orphans:2;widows:2}\n")


def polish_css(target: str) -> str:
    """The shared finishing layer for one weapon. Appended AFTER the weapon's own CSS and BEFORE a user's custom CSS (the user wins)."""
    return {"game": _game, "deck": _deck, "shell": _shell, "web": _web, "print": _print}[target]()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--ramp")
    a = ap.parse_args()
    if a.ramp:
        print(json.dumps(ramp(a.ramp), indent=1))
        return 0
    print(json.dumps({"scale": SCALE, "floor": FLOOR, "space": SPACE, "radii": RADII, "grids": GRIDS, "motion": MOTION, "ornaments": ORNAMENTS,
                      "tracking": {str(s): tracking(s) for s in (132, 96, 72, 56, 44, 36, 28, 24)},
                      "leading": {str(s): leading(s) for s in (132, 96, 72, 56, 44, 36, 28, 24)}}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
