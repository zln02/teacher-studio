#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Design preset E (「잉크 포스터」): the look of the 2026-11-23 training deck, as reusable tokens (stdlib only).

Style id in styles.py: "ink-poster". One source for the palette (dark ink + light paper, every text pair contrast-checked),
the 12-column stage grid, the type scale, the six card components and the motion tokens that shared/design/motion_e.js reads.

    import preset_e as E
    E.PALETTE["dark"]["acc"]        # "#E4502F" vermilion: the ONE accent
    E.text_issues()                 # [] when every text pair passes (4.5:1 body, 3:1 large-only roles)
    E.css(mode="dark")              # :root tokens + .e-* components (cards, pills, pen, hud, cursor) for a page
    E.motion_js()                   # the motion vocabulary (ES2017, no libraries) with these tokens baked in

Rules that come with the preset (DESIGN-RULES.md, 「Preset E」):
- one accent (vermilion) for emphasis; cobalt only for the "with the tool" side / pen notes; lime only for a correct mark.
- vermilion text on paper is large-only (3.3:1): body text on paper is ink or grey, never vermilion.
- cards are flat: 1.5px hairline, radius 12, no shadow, no gradient.
- motion: fast in (120-260 ms), blur only while moving, then hold still; reduced motion = the final state at once.
- every new class starts with `e-` (old page CSS such as .hl .chip .pn must not leak in).
CLI: python3 preset_e.py --show | --css [--mode light] | --check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design as design_core  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

STYLE_ID = "ink-poster"
NAME = "잉크 포스터"

# ---- palette (taken from the reference video colours; dark is the default, light is the paper variant) ----------------------------------
PALETTE = {
    "dark": {"bg": "#121214", "bg2": "#161618", "surf": "#1a1a1d", "surf2": "#212125", "line": "#2b2b30", "line2": "#3d3d43",
             "ink": "#F0EDE6", "sub": "#bdbab4", "mute": "#8E8E92", "acc": "#E4502F", "cool": "#6F74FF", "good": "#D8E46C",
             "on_acc": "#121214", "scrim": "rgba(18,18,20,.62)", "dot": "rgba(240,237,230,.045)", "glow": "rgba(228,80,47,.07)", "tick": "rgba(240,237,230,.16)"},
    "light": {"bg": "#F0EDE6", "bg2": "#e9e5dc", "surf": "#f7f5f0", "surf2": "#ebe7df", "line": "#d6d1c6", "line2": "#bdb7ab",
              "ink": "#121214", "sub": "#3d3d42", "mute": "#5c5c61", "acc": "#E4502F", "cool": "#3338F0", "good": "#56620e",
              "on_acc": "#121214", "scrim": "rgba(240,237,230,.7)", "dot": "rgba(18,18,20,.06)", "glow": "rgba(228,80,47,.06)", "tick": "rgba(18,18,20,.18)"},
}
# (fg, bg, need, why). need 3.0 = large text only (>= 46px bold on the stage).
TEXT_PAIRS = {
    "dark": [("ink", "bg", 4.5, "body"), ("ink", "surf", 4.5, "card body"), ("sub", "surf", 4.5, "card detail"), ("mute", "bg", 4.5, "kicker / caption"),
             ("acc", "bg", 4.5, "accent words"), ("cool", "bg", 4.5, "tool side / pen"), ("good", "bg", 4.5, "correct mark"), ("on_acc", "acc", 4.5, "text on an accent chip")],
    "light": [("ink", "bg", 4.5, "body"), ("ink", "surf", 4.5, "card body"), ("sub", "surf", 4.5, "card detail"), ("mute", "bg", 4.5, "kicker / caption"),
              ("cool", "bg", 4.5, "tool side / pen"), ("good", "bg", 4.5, "correct mark"), ("acc", "bg", 3.0, "accent: large text only"), ("on_acc", "acc", 4.5, "text on an accent chip")],
}
LARGE_ONLY = {"light": ["acc"]}   # roles that may colour large text only (>= 46px)

# ---- grid + type (1920 x 1080 stage px). Nothing on a slide is under 28px (the slides gate floor). ----------------------------------------
GRID = {"cols": 12, "margin": 128, "gutter": 32, "top": 96, "bottom": 96, "stage": [1920, 1080], "rhythm": 8,
        "zones": {"text": (1, 6), "picture": (7, 6), "full": (1, 12), "narrow": (2, 8)}}
TYPE = {"big": 176, "reveal": 300, "h1": 84, "h2": 62, "card": 46, "body": 34, "detail": 30, "kicker": 28, "label": 28,
        "weight": {"big": 800, "h": 800, "card": 700, "body": 400}, "tracking": {"big": -0.055, "h": -0.045, "card": -0.03, "body": -0.01, "kicker": 0.04},
        "leading": {"big": 1.04, "h": 1.1, "body": 1.45}, "mono_for": ["kicker", "step numbers", "pill labels", "evidence lines"]}

# ---- motion tokens (ms). Read by motion_e.js. -----------------------------------------------------------------------------------------
MOTION = {"xs": 120, "s": 200, "m": 260, "l": 420, "gap": 60, "stagger": 45, "in": 200, "out": 150, "blur": 8, "word": 70, "pen": 520, "cursor": 620,
          "ease_in": "cubic-bezier(.16,1,.3,1)", "ease_out": "cubic-bezier(.4,0,1,1)",
          "rules": ["fast in (120-260 ms), blur only while moving, hold still", "one accent moves per beat", "presenter click drives every beat",
                    "back / reduced motion / print = the final state at once", "cursor scenes end on the real result and make no speed claim"]}

# ---- the six card components ----------------------------------------------------------------------------------------------------------
CARDS = {
    "note": "flat surface card: 1.5px hairline, radius 12, no shadow (the default box)",
    "step": "numbered step: the number in mono, accent colour; title + one line",
    "ask": "a request / prompt card with one accent caret at the end (what someone typed)",
    "pair": "a comparison pair with a hairline down the middle; the 'with the tool' side in cobalt",
    "node": "a hub node: outline icon + short label on the background colour (diagrams)",
    "window": "an app-screen frame: title bar + body (show the REAL thing before an analogy)",
}


def contrast(a: str, b: str) -> float:
    return design_core.contrast(a, b)


def text_issues() -> list[str]:
    """Every text pair of both modes; [] when all pass."""
    out = []
    for mode, pairs in TEXT_PAIRS.items():
        p = PALETTE[mode]
        for fg, bg, need, why in pairs:
            r = contrast(p[fg], p[bg])
            if r < need:
                out.append(f"{mode}: {fg} on {bg} = {r:.2f} < {need} ({why})")
    return out


def style_palette() -> dict:
    """The 11-key palette styles.py expects (dark mode)."""
    d = PALETTE["dark"]
    return {"bg1": d["bg"], "bg2": d["bg2"], "text": d["ink"], "card": d["surf"], "cardText": d["ink"], "cardBorder": d["line"],
            "primary": d["acc"], "btnText": d["on_acc"], "accent": d["cool"], "good": d["good"], "bad": d["acc"]}


def css_vars(mode: str = "dark", sel: str = ":root") -> str:
    p = PALETTE[mode]
    v = ";".join(f"--e-{k.replace('_', '-')}:{c}" for k, c in p.items())
    m = ";".join(f"--e-t-{k}:{MOTION[k]}ms" for k in ("xs", "s", "m", "l", "gap", "stagger", "in", "out"))
    t = ";".join(f"--e-fs-{k}:{TYPE[k]}px" for k in ("big", "reveal", "h1", "h2", "card", "body", "detail", "kicker", "label"))
    return f"{sel}{{{v};{m};{t};--e-ease:{MOTION['ease_in']};--e-r:12px;--e-hair:1.5px;--e-margin:{GRID['margin']}px;--e-gutter:{GRID['gutter']}px}}"


COMPONENTS = """
.e-mono{font-family:"D2Coding","Consolas","SFMono-Regular","Menlo","TS Sans","Noto Sans KR",monospace}
.e-kicker{font-size:var(--e-fs-kicker);letter-spacing:.04em;color:var(--e-mute)}
.e-big{font-size:var(--e-fs-big);font-weight:800;letter-spacing:-.055em;line-height:1.04;color:var(--e-ink);margin:0}
.e-big em,.e-h em{font-style:normal;color:var(--e-acc)}
.e-card{background:var(--e-surf);border:var(--e-hair) solid var(--e-line);border-radius:var(--e-r);box-shadow:none;padding:36px 40px;color:var(--e-ink)}
.e-card b{display:block;font-size:var(--e-fs-card);font-weight:700;letter-spacing:-.03em;line-height:1.15}
.e-card p{margin:10px 0 0;font-size:var(--e-fs-detail);color:var(--e-sub);line-height:1.4}
.e-step .e-n{font-family:"D2Coding","Consolas","TS Sans",monospace;font-size:40px;color:var(--e-acc)}
.e-ask{background:var(--e-surf);border:var(--e-hair) solid var(--e-line2);border-radius:var(--e-r);padding:24px 30px;font-size:var(--e-fs-body);color:var(--e-ink)}
.e-ask:after{content:"";display:inline-block;width:3px;height:1em;margin-left:8px;vertical-align:-.12em;background:var(--e-acc)}
.e-pair{position:relative;display:grid;grid-template-columns:1fr 1fr;gap:64px}
.e-pair:before{content:"";position:absolute;left:50%;top:0;bottom:0;border-left:var(--e-hair) solid var(--e-line)}
.e-pair .e-tool{border-color:var(--e-cool)}
.e-pair .e-tool b{color:var(--e-cool)}
.e-node{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;min-width:180px;min-height:128px;border:2px solid var(--e-line2);border-radius:var(--e-r);background:var(--e-bg);color:var(--e-cool)}
.e-node b{font-size:var(--e-fs-label);font-weight:700;color:var(--e-ink);white-space:nowrap}
.e-node.e-core{border-color:var(--e-acc);color:var(--e-acc)}
.e-window{background:var(--e-surf);border:var(--e-hair) solid var(--e-line2);border-radius:14px;overflow:hidden}
.e-window>.e-bar{height:58px;display:flex;align-items:center;gap:10px;padding:0 20px;border-bottom:var(--e-hair) solid var(--e-line);background:var(--e-surf2);font-size:var(--e-fs-label);color:var(--e-sub)}
.e-window>.e-bar>i{width:14px;height:14px;border-radius:50%;background:var(--e-line2)}
.e-window>.e-body{padding:26px 28px}
.e-pills{display:flex;gap:14px}
.e-pills>span{position:relative;flex:1;display:flex;flex-direction:column;gap:8px;font-size:var(--e-fs-label);color:var(--e-mute);white-space:nowrap;word-break:keep-all}
.e-pills>span:before{content:"";display:block;height:5px;border-radius:3px;background:var(--e-line2)}
.e-pills>span>i{position:absolute;left:0;top:0;width:100%;height:5px;border-radius:3px;background:var(--e-sub);transform-origin:0 50%;transform:scaleX(0)}
.e-pills>span.e-cur{color:var(--e-ink)}
.e-pills>span.e-cur>i{background:var(--e-acc)}
.e-hl .e-w{opacity:.28}
.e-hl .e-w.e-lit{opacity:1;color:var(--e-ink)}
.e-hl .e-w.e-num.e-lit{color:var(--e-acc)}
.e-pen{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;overflow:visible}
.e-pen path{fill:none;stroke:var(--e-cool);stroke-width:4.5;stroke-linecap:round;stroke-linejoin:round}
.e-pen path.e-acc{stroke:var(--e-acc)}
.e-note{position:absolute;font-size:36px;font-weight:700;letter-spacing:-.02em;white-space:nowrap;transform:rotate(-3deg);color:var(--e-cool)}
.e-dot{position:absolute;left:0;top:0;width:26px;height:26px;border-radius:50%;background:var(--e-acc);pointer-events:none}
.e-hud{position:absolute;inset:0;pointer-events:none;z-index:6}
.e-hud>i{position:absolute;width:30px;height:30px;border:0 solid var(--e-line2)}
.e-hud>i:nth-child(1){left:26px;top:26px;border-left-width:2px;border-top-width:2px}
.e-hud>i:nth-child(2){right:26px;top:26px;border-right-width:2px;border-top-width:2px}
.e-hud>i:nth-child(3){left:26px;bottom:26px;border-left-width:2px;border-bottom-width:2px}
.e-hud>i:nth-child(4){right:26px;bottom:26px;border-right-width:2px;border-bottom-width:2px}
.e-hud>u{position:absolute;left:96px;right:96px;bottom:14px;height:9px;background:linear-gradient(90deg,var(--e-tick) 1px,transparent 1px) 0 100%/24px 5px repeat-x}
.e-hud>u:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,var(--e-tick) 1px,transparent 1px) 0 100%/192px 9px repeat-x}
.e-hud>u>b{position:absolute;bottom:0;width:3px;height:16px;margin-left:-1px;border-radius:2px;background:var(--e-acc)}
.e-board{position:relative}
.e-board .e-sel{position:absolute;border:2px solid var(--e-cool);border-radius:2px;pointer-events:none}
.e-board .e-guide{position:absolute;background:var(--e-acc);pointer-events:none}
.e-cur{position:absolute;left:0;top:0;z-index:8;pointer-events:none;white-space:nowrap}
.e-cur svg{position:absolute;left:-4px;top:-3px;width:36px;height:36px;fill:var(--e-cc,var(--e-acc));stroke:#fff;stroke-width:1.4;stroke-linejoin:round}
.e-cur b{position:absolute;left:26px;top:28px;font-size:24px;font-weight:700;padding:3px 12px;border-radius:999px;background:var(--e-cc,var(--e-acc));color:#fff}
.e-cur.e-grab svg{transform:scale(.86)}
.e-ring{position:absolute;left:-14px;top:-14px;width:28px;height:28px;border-radius:50%;border:2px solid var(--e-cc,var(--e-acc));opacity:0}
.e-ok{position:absolute;right:-22px;top:-22px;width:48px;height:48px;border-radius:50%;display:grid;place-items:center;font-size:30px;font-weight:800;background:var(--e-good);color:#121214}
.e-scene{position:absolute;inset:0;z-index:0;background-size:cover;background-position:center;pointer-events:none}
.e-scene:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,var(--e-bg) 0%,var(--e-scrim) 46%,transparent 100%)}
.e-scene:before{content:"";position:absolute;left:0;right:0;bottom:0;height:30%;z-index:1;background:linear-gradient(0deg,var(--e-bg),transparent)}
.e-note{word-break:keep-all}
@media (prefers-reduced-motion: reduce){.e-hl .e-w,.e-pills>span>i{transition:none}}
"""


def css(mode: str = "dark", scope: str = ":root") -> str:
    """Tokens + components for one page (dark ink by default, `light` = paper)."""
    return css_vars(mode, scope) + COMPONENTS


def motion_js() -> str:
    """motion_e.js with this preset's motion tokens baked in."""
    src = (HERE / "motion_e.js").read_text(encoding="utf-8")
    tok = json.dumps({k: MOTION[k] for k in ("xs", "s", "m", "l", "gap", "stagger", "in", "out", "blur", "word", "pen", "cursor")})
    return src.replace("/*E_TOKENS*/null", tok, 1)


def tokens() -> dict:
    return {"id": STYLE_ID, "name": NAME, "palette": PALETTE, "grid": GRID, "type": TYPE, "motion": MOTION, "cards": CARDS}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--css", action="store_true")
    ap.add_argument("--mode", default="dark", choices=sorted(PALETTE))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.css:
        print(css(a.mode))
        return 0
    if a.check:
        bad = text_issues()
        print("\n".join(bad) if bad else "PASS preset E: every text pair passes in dark and light")
        return 1 if bad else 0
    print(json.dumps(tokens(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
