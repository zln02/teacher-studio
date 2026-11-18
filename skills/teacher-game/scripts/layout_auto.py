#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Layout generator: picks a composition + component styles for a spec, so two builds do not look alike.

Principle: tools guarantee the quality floor (every layout declares its zones in assets/layouts/layouts.css, text never overlaps),
the AI adds request-specific creativity on top (design.words, custom_css, custom_svg, design.layout ...).

Choices (all deterministic from the spec + design.seed; build.py draws a fresh seed when the spec has none and prints/stores it):
  layout   quiz/escape/board question screens: stack | split | bento | news | poster
  mech     per mechanic: match grid|scatter|shelf|brick - bingo grid|tilt|shelf - sort bins|shelves|conveyor - board snake|wave|stair
           survival row|bridge|stagger|arena - escape lockpos top|side
  choice   answer buttons: default | pill | tile | stamp | neon | note
  card     cards: default | round | ticket | polaroid | hex
  score    scoreboard: default | led | chalk | sticker | banner
  title    title treatment: default | outline | stack3d | stamp | underline (+ scale sm|md|lg, position center|left|top)
  transition  iris | wipe | fade
Mood steers the weights (긴장감 -> dark split/news + neon; 귀엽게/따뜻하게 -> rounded bento; 고급스럽게 -> poster/news + ticket ...).
Spec overrides: design.layout, design.choice, design.card, design.score, design.title.
Usage: python3 layout_auto.py --mechanic quiz --mood 긴장감 --seed 3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import style_auto  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

LAYOUTS = ["stack", "split", "bento", "news", "poster"]
MECH_VARIANTS = {"match": ["grid", "scatter", "shelf", "brick"], "bingo": ["grid", "tilt", "shelf"], "sort": ["bins", "shelves", "conveyor"],
                 "board": ["snake", "wave", "stair"], "survival": ["row", "bridge", "stagger", "arena"], "escape": ["top", "side"], "quiz": [""]}
CHOICES = ["default", "pill", "tile", "stamp", "neon", "note"]
CARDS = ["default", "round", "ticket", "polaroid", "hex"]
SCORES = ["default", "led", "chalk", "sticker", "banner"]
TITLES = ["default", "outline", "stack3d", "stamp", "underline"]
TRANSITIONS = ["iris", "wipe", "fade"]

# style families by mood word (substring match on design.mood + design.words + recipe); weights per option
FAMILY = {
    "tense": {"keys": ["긴장", "방탈출", "미스터리", "탐정", "추리", "tense"], "dark": True,
              "layout": {"split": 4, "news": 4, "poster": 1, "stack": 1, "bento": 1}, "choice": {"neon": 4, "tile": 2, "stamp": 2, "pill": 1},
              "card": {"ticket": 3, "default": 2, "hex": 2}, "score": {"led": 4, "banner": 2, "chalk": 1}, "title": {"stack3d": 3, "outline": 3, "stamp": 2}, "transition": {"wipe": 3, "fade": 1}},
    "cute": {"keys": ["귀여", "동화", "따뜻", "바다", "숲", "가족", "밝", "자연", "fairy", "warm", "sea", "forest"], "dark": False,
             "layout": {"bento": 4, "stack": 2, "poster": 2, "split": 1, "news": 1}, "choice": {"pill": 4, "note": 3, "tile": 1, "stamp": 1},
             "card": {"round": 4, "polaroid": 3, "default": 1}, "score": {"sticker": 4, "chalk": 2, "banner": 1}, "title": {"underline": 3, "stack3d": 2, "stamp": 2}, "transition": {"iris": 3, "fade": 2}},
    "luxe": {"keys": ["고급", "송년", "연말", "품격", "우아", "luxe"], "dark": True,
             "layout": {"poster": 4, "news": 3, "split": 2, "stack": 1, "bento": 1}, "choice": {"tile": 3, "pill": 2, "neon": 2},
             "card": {"ticket": 4, "default": 2, "polaroid": 1}, "score": {"banner": 4, "led": 2}, "title": {"underline": 4, "outline": 2, "stack3d": 1}, "transition": {"fade": 3, "wipe": 2}},
    "fun": {"keys": ["신남", "우주", "스포츠", "운동", "축제", "파티", "과학", "space", "sports"], "dark": False,
            "layout": {"split": 3, "bento": 3, "news": 2, "stack": 1, "poster": 2}, "choice": {"pill": 2, "neon": 2, "stamp": 2, "tile": 2, "note": 1},
            "card": {"hex": 3, "round": 2, "ticket": 2, "default": 1}, "score": {"led": 3, "sticker": 3, "banner": 2}, "title": {"stack3d": 3, "stamp": 3, "outline": 2}, "transition": {"iris": 2, "wipe": 2, "fade": 1}},
    "classic": {"keys": ["역사", "조선", "전통", "차분", "hanok"], "dark": False,
                "layout": {"poster": 3, "stack": 3, "split": 2, "news": 1, "bento": 1}, "choice": {"note": 3, "tile": 3, "stamp": 2, "pill": 1},
                "card": {"polaroid": 3, "ticket": 2, "default": 2}, "score": {"chalk": 3, "banner": 3, "sticker": 1}, "title": {"underline": 3, "stamp": 3, "outline": 1}, "transition": {"fade": 3, "wipe": 2}},
}
DEFAULT_FAMILY = {"dark": False, "layout": {k: 2 for k in LAYOUTS}, "choice": {k: 1 for k in CHOICES}, "card": {k: 1 for k in CARDS},
                  "score": {k: 1 for k in SCORES}, "title": {k: 1 for k in TITLES}, "transition": {k: 1 for k in TRANSITIONS}}


def _h(key: str) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:10], 16)


def _pick(opts: dict, key: str) -> str:
    """Weighted deterministic pick."""
    total = sum(opts.values())
    r = _h(key) % total
    for k, w in sorted(opts.items()):
        if r < w:
            return k
        r -= w
    return next(iter(opts))


def family_for(text: str) -> tuple[str, dict]:
    for name, fam in FAMILY.items():
        if any(k in text for k in fam["keys"]):
            return name, fam
    return "", DEFAULT_FAMILY


def compose(spec: dict, tokens: dict | None = None, recipe: str = "", style: str = "") -> dict:
    """The layout config stored in the page (SPEC.layoutCfg). Deterministic for (spec words, design.seed)."""
    d = spec.get("design") or {}
    mech = spec.get("mechanic", "quiz")
    words = " ".join(map(str, d.get("words") or [])) if isinstance(d.get("words"), list) else str(d.get("words") or "")
    text = " ".join([words, str(d.get("mood", "")), str(spec.get("title", "")), recipe])
    fname, fam = family_for(text)
    if style in style_auto.STYLES:  # the general style taxonomy decides (each style = its own composition language)
        fname, fam = style, style_auto.STYLES[style]
    seed = int(d.get("seed", 0))
    key = f"{mech}|{fname}|{seed}"
    colors = (tokens or {}).get("colors") or {}
    dark = sum(int(colors.get("bg1", "#ffffff")[i:i + 2], 16) for i in (1, 3, 5)) < 330
    layout = d.get("layout") if d.get("layout") in LAYOUTS else _pick(fam["layout"], key + "L")
    choice_opts = dict(fam["choice"])
    if not dark:
        choice_opts.pop("neon", None)  # neon glow needs a dark scene
        choice_opts.setdefault("tile", 1)
    cfg = {
        "family": fname or "generic", "style": style if style in style_auto.STYLES else "", "css": (style_auto.STYLES[style].get("css", "") if style in style_auto.STYLES else ""), "seed": seed, "mechanic": mech, "layout": layout,
        "mech": _pick({v: 1 for v in MECH_VARIANTS.get(mech, [""])}, key + "M") if MECH_VARIANTS.get(mech) else "",
        "choice": d.get("choice") if d.get("choice") in CHOICES else _pick(choice_opts, key + "C"),
        "card": d.get("card") if d.get("card") in CARDS else _pick(fam["card"], key + "K"),
        "score": d.get("score") if d.get("score") in SCORES else _pick(fam["score"], key + "S"),
        "title": d.get("title_style") if d.get("title_style") in TITLES else _pick(fam["title"], key + "T"),
        "titleScale": ["sm", "md", "lg"][_h(key + "Z") % 3], "tpos": ["center", "left", "top", "center"][_h(key + "P") % 4],
        "transition": _pick(fam["transition"], key + "X"),
    }
    if mech == "escape" and cfg["mech"] == "side":
        cfg["mech"] = "side"
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mechanic", default="quiz")
    ap.add_argument("--mood", default="")
    ap.add_argument("--words", default="")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    print(json.dumps(compose({"mechanic": a.mechanic, "design": {"mood": a.mood, "words": a.words.split(), "seed": a.seed}}), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
