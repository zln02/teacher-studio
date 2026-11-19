#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Shared style taxonomy (games AND slides): 12 styles, each with its own composition language. Lives in shared/design; scripts/style_auto.py (game) re-exports it.

A WORLD (theme_auto.py: space, sea, fairy ... = props, character, signature drawing) is orthogonal to a STYLE (this file = how it is staged:
palette, background generator, layout, button/card/scoreboard/title treatments, transitions). Same world x different style = different look.

  neon-cyber        네온/사이버      dark, perspective neon grid, glowing outlines, LED scoreboard
  gold-luxury       골드 럭셔리      black + gold, bokeh, ticket cards, serif titles
  pop-colorful      팝 컬러풀        flat bright shapes, thick outlines, hard shadows, stickers
  festival-party    축제/파티        bunting, confetti, balloons, polaroid cards
  tv-gameshow       TV 게임쇼        stage lights + LED panel wall (generic, no legacy mascot or signs)
  glass-3d          글래스/3D        frosted translucent panels over blurred colour orbs
  anime-cartoon     애니/카툰        speed lines + halftone, heavy ink outlines
  pastel-cute       파스텔 귀여움    soft clouds and hills, rounded pills, sticker scores
  retro-pixel       레트로/픽셀      blocky pixel backdrop, square hard-edged UI
  minimal-premium   미니멀 프리미엄  off-white paper, hairlines, lots of whitespace, one accent, no props
  chalk-paper       칠판/종이        chalkboard with dust and dashed chalk frames
  nature-calm       자연/차분        hills and leaves, calm motion, soft rounded UI
Usage: python3 styles.py --words "우주 미니멀" --seed 3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

STYLES: dict[str, dict] = {
    "neon-cyber": {"keys": ["네온", "사이버", "미래", "게임", "해킹", "ai", "AI", "코딩"], "dark": True, "bg": "neongrid", "pattern": "grid", "font": "Black Han Sans", "music": "tension", "motion": "high",
        "pal": {"bg1": "#05070f", "bg2": "#1a0b3d", "text": "#ffffff", "card": "#0d1230", "cardText": "#eaf2ff", "cardBorder": "#00e5ff", "primary": "#00e5ff", "btnText": "#02111a", "accent": "#ff2bd6", "good": "#39ff9c", "bad": "#ff5c7a"},
        "layout": {"split": 4, "news": 3, "poster": 2, "bento": 1}, "choice": {"neon": 6, "tile": 1}, "card": {"hex": 3, "ticket": 3, "default": 1}, "score": {"led": 5, "banner": 1}, "title": {"outline": 4, "stack3d": 3},
        "transition": {"wipe": 3, "fade": 1}, "props": True, "css": "neon"},
    "gold-luxury": {"keys": ["골드", "럭셔리", "고급", "송년", "연말", "시상", "품격", "우아", "프리미엄 파티"], "dark": True, "bg": "bokeh", "pattern": "diamond", "font": "Noto Serif KR", "music": "upbeat", "motion": "normal",
        "pal": {"bg1": "#14110f", "bg2": "#2b2118", "text": "#fff4d6", "card": "#1f1a14", "cardText": "#fff4d6", "cardBorder": "#e0b44c", "primary": "#e0b44c", "btnText": "#1a1206", "accent": "#f4e3b2", "good": "#5be0a0", "bad": "#ff8a8a"},
        "layout": {"poster": 4, "news": 3, "split": 2, "stack": 1}, "choice": {"tile": 3, "pill": 3}, "card": {"ticket": 5, "default": 2}, "score": {"banner": 5, "led": 1}, "title": {"underline": 5, "outline": 1},
        "transition": {"fade": 4, "wipe": 1}, "props": True, "css": "gold"},
    "pop-colorful": {"keys": ["팝", "컬러풀", "발랄", "신나", "신남", "알록달록"], "dark": False, "bg": "memphis", "pattern": "dots", "font": "Jua", "music": "upbeat", "motion": "high",
        "pal": {"bg1": "#fff1a8", "bg2": "#ffd0e8", "text": "#1b1230", "card": "#ffffff", "cardText": "#1b1230", "cardBorder": "#1b1230", "primary": "#d6214a", "btnText": "#ffffff", "accent": "#2b6cff", "good": "#0f8a4a", "bad": "#c4163a"},
        "layout": {"bento": 4, "stack": 2, "poster": 2, "split": 2}, "choice": {"stamp": 3, "tile": 4, "pill": 1}, "card": {"round": 2, "ticket": 3, "default": 1}, "score": {"sticker": 6}, "title": {"stamp": 4, "stack3d": 3},
        "transition": {"iris": 3, "wipe": 2}, "props": True, "css": "pop"},
    "festival-party": {"keys": ["축제", "파티", "생일", "운동회", "잔치", "페스티벌", "기념일"], "dark": True, "bg": "bunting", "pattern": "dots", "font": "Jua", "music": "upbeat", "motion": "high",
        "pal": {"bg1": "#3b0a45", "bg2": "#7a1e5a", "text": "#ffffff", "card": "#fff3fb", "cardText": "#3b0a45", "cardBorder": "#ffd23f", "primary": "#ffd23f", "btnText": "#3b0a45", "accent": "#ff5ca8", "good": "#0f8a4a", "bad": "#c4163a"},
        "layout": {"bento": 3, "stack": 3, "split": 2, "poster": 1}, "choice": {"pill": 4, "note": 2, "stamp": 1}, "card": {"polaroid": 4, "round": 2}, "score": {"sticker": 4, "banner": 2}, "title": {"stamp": 4, "stack3d": 2},
        "transition": {"iris": 3, "fade": 1}, "props": True, "css": "party"},
    "tv-gameshow": {"keys": ["게임쇼", "방송", "퀴즈쇼", "대결", "최종 결전", "도전"], "dark": True, "bg": "stage", "pattern": "dots", "font": "Black Han Sans", "music": "upbeat", "motion": "high",
        "pal": {"bg1": "#08202a", "bg2": "#0f4a5a", "text": "#ffffff", "card": "#0c2f3b", "cardText": "#ffffff", "cardBorder": "#ff9f1c", "primary": "#ff9f1c", "btnText": "#1a1004", "accent": "#2ec4b6", "good": "#5df2a3", "bad": "#ff7a7a"},
        "layout": {"news": 4, "split": 3, "bento": 1, "stack": 1}, "choice": {"pill": 3, "tile": 3, "neon": 1}, "card": {"ticket": 3, "round": 2}, "score": {"led": 3, "banner": 4}, "title": {"stack3d": 4, "stamp": 2},
        "transition": {"wipe": 3, "iris": 2}, "props": True, "css": "show"},
    "glass-3d": {"keys": ["글래스", "3D", "3d", "유리", "입체", "모던", "세련"], "dark": True, "bg": "glassblobs", "pattern": "dots", "font": "Noto Sans KR", "music": "mystery", "motion": "normal",
        "pal": {"bg1": "#0f1b4d", "bg2": "#5b2a86", "text": "#ffffff", "card": "#1c2a6e", "cardText": "#ffffff", "cardBorder": "#9fb7ff", "primary": "#7cf2e6", "btnText": "#04201d", "accent": "#ff8bd1", "good": "#6bffb0", "bad": "#ff8a9a"},
        "layout": {"bento": 4, "split": 3, "poster": 2, "stack": 1}, "choice": {"pill": 4, "tile": 2}, "card": {"round": 5, "default": 1}, "score": {"banner": 3, "chalk": 2, "sticker": 1}, "title": {"underline": 3, "outline": 2, "default": 2},
        "transition": {"fade": 4, "iris": 2}, "props": False, "css": "glass"},
    "anime-cartoon": {"keys": ["애니", "카툰", "만화", "웹툰", "히어로"], "dark": False, "bg": "speed", "pattern": "dots", "font": "Black Han Sans", "music": "sports", "motion": "high",
        "pal": {"bg1": "#8fd3ff", "bg2": "#fff3b0", "text": "#0b1b3a", "card": "#ffffff", "cardText": "#0b1b3a", "cardBorder": "#0b1b3a", "primary": "#d7263d", "btnText": "#ffffff", "accent": "#1d4ed8", "good": "#0f8a4a", "bad": "#c4163a"},
        "layout": {"split": 3, "bento": 3, "news": 2, "poster": 2}, "choice": {"stamp": 3, "tile": 4, "note": 1}, "card": {"ticket": 3, "default": 3, "round": 1}, "score": {"sticker": 5, "banner": 1}, "title": {"stamp": 3, "stack3d": 4},
        "transition": {"wipe": 4, "iris": 2}, "props": True, "css": "anime"},
    "pastel-cute": {"keys": ["파스텔", "귀엽", "귀여", "동화", "유아", "저학년", "몽글"], "dark": False, "bg": "hills", "pattern": "sparkle", "font": "Jua", "music": "cute", "motion": "normal",
        "pal": {"bg1": "#ffe8f1", "bg2": "#e0f3ff", "text": "#4a2f5e", "card": "#ffffff", "cardText": "#4a2f5e", "cardBorder": "#ffb3d1", "primary": "#a63d8f", "btnText": "#ffffff", "accent": "#5fbfa8", "good": "#1b7a55", "bad": "#c43d5a"},
        "layout": {"bento": 4, "stack": 3, "poster": 1, "split": 1}, "choice": {"pill": 5, "note": 2}, "card": {"round": 5, "polaroid": 2}, "score": {"sticker": 4, "chalk": 1, "banner": 1}, "title": {"underline": 3, "stack3d": 3, "stamp": 1},
        "transition": {"iris": 4, "fade": 2}, "props": True, "css": "pastel"},
    "retro-pixel": {"keys": ["레트로", "픽셀", "8비트", "오락실", "아케이드", "도트"], "dark": True, "bg": "pixel", "pattern": "grid", "font": "Do Hyeon", "music": "upbeat", "motion": "high",
        "pal": {"bg1": "#1a0f2e", "bg2": "#2b1850", "text": "#f4ecff", "card": "#2b1850", "cardText": "#fff7d6", "cardBorder": "#5cff8a", "primary": "#5cff8a", "btnText": "#07210f", "accent": "#ff5c5c", "good": "#5cff8a", "bad": "#ff7a7a"},
        "layout": {"split": 3, "news": 3, "bento": 2, "stack": 2}, "choice": {"tile": 5, "stamp": 2}, "card": {"default": 4, "hex": 1}, "score": {"led": 5, "banner": 1}, "title": {"outline": 3, "stack3d": 3},
        "transition": {"wipe": 5}, "props": True, "css": "pixel"},
    "minimal-premium": {"keys": ["미니멀", "심플", "프리미엄", "깔끔", "모노", "화이트"], "dark": False, "bg": "minimal", "pattern": "none", "font": "Noto Serif KR", "music": "mystery", "motion": "calm",
        "pal": {"bg1": "#f6f4ef", "bg2": "#ebe7de", "text": "#1a1a1a", "card": "#ffffff", "cardText": "#1a1a1a", "cardBorder": "#1a1a1a", "primary": "#1a1a1a", "btnText": "#f6f4ef", "accent": "#b08d3c", "good": "#1d6f45", "bad": "#b3261e"},
        "layout": {"poster": 4, "split": 4, "news": 1, "stack": 1}, "choice": {"tile": 4, "pill": 2}, "card": {"default": 4, "round": 1}, "score": {"banner": 3, "chalk": 3}, "title": {"underline": 4, "default": 3},
        "transition": {"fade": 6}, "props": False, "css": "minimal"},
    "chalk-paper": {"keys": ["칠판", "종이", "분필", "노트", "교실", "수업"], "dark": True, "bg": "chalk", "pattern": "none", "font": "Gowun Dodum", "music": "cute", "motion": "calm",
        "pal": {"bg1": "#1f3d33", "bg2": "#16302a", "text": "#f5f5ef", "card": "#2a4d41", "cardText": "#f5f5ef", "cardBorder": "#f5f5ef", "primary": "#ffe066", "btnText": "#2a2200", "accent": "#ff9e9e", "good": "#8dffb8", "bad": "#ff9e9e"},
        "layout": {"stack": 3, "split": 3, "poster": 2, "bento": 1}, "choice": {"stamp": 4, "note": 3}, "card": {"polaroid": 2, "default": 3, "ticket": 1}, "score": {"chalk": 6}, "title": {"underline": 4, "stamp": 2},
        "transition": {"fade": 3, "wipe": 2}, "props": True, "css": "chalk"},
    "nature-calm": {"keys": ["자연", "차분", "숲", "힐링", "식물", "정원", "생태"], "dark": False, "bg": "hills", "pattern": "leaves", "font": "Jua", "music": "nature", "motion": "calm",
        "pal": {"bg1": "#dff5e1", "bg2": "#b6e3c0", "text": "#1d3a26", "card": "#ffffff", "cardText": "#1d3a26", "cardBorder": "#4caf6a", "primary": "#237a43", "btnText": "#ffffff", "accent": "#f2b134", "good": "#1a7a43", "bad": "#b8322d"},
        "layout": {"stack": 3, "bento": 3, "poster": 2, "split": 1}, "choice": {"pill": 4, "note": 2, "tile": 1}, "card": {"round": 4, "polaroid": 2}, "score": {"sticker": 3, "banner": 2, "chalk": 1}, "title": {"underline": 4, "stack3d": 1},
        "transition": {"fade": 4, "iris": 2}, "props": True, "css": "nature"},
}
# which styles suit which world when the words do not name a style (weights; 1 = possible, 4 = natural fit)
WORLD_STYLE = {
    "space": {"neon-cyber": 4, "glass-3d": 4, "retro-pixel": 3, "minimal-premium": 3, "pop-colorful": 2, "anime-cartoon": 2, "tv-gameshow": 1},
    "sea": {"pastel-cute": 4, "anime-cartoon": 3, "glass-3d": 3, "nature-calm": 3, "pop-colorful": 3, "minimal-premium": 1},
    "fairy": {"pastel-cute": 5, "pop-colorful": 2, "anime-cartoon": 2, "festival-party": 2, "glass-3d": 1},
    "tense": {"neon-cyber": 4, "retro-pixel": 3, "chalk-paper": 2, "glass-3d": 2, "minimal-premium": 2, "gold-luxury": 1},
    "luxe": {"gold-luxury": 5, "minimal-premium": 3, "festival-party": 2, "tv-gameshow": 2, "glass-3d": 1},
    "warm": {"pastel-cute": 3, "nature-calm": 3, "festival-party": 3, "chalk-paper": 2, "pop-colorful": 2, "minimal-premium": 1},
    "forest": {"nature-calm": 5, "pastel-cute": 2, "chalk-paper": 2, "minimal-premium": 1, "anime-cartoon": 1},
    "hanok": {"minimal-premium": 3, "chalk-paper": 3, "gold-luxury": 2, "nature-calm": 2, "retro-pixel": 1},
    "sports": {"pop-colorful": 4, "tv-gameshow": 4, "anime-cartoon": 4, "festival-party": 2, "retro-pixel": 2},
    "science": {"glass-3d": 3, "neon-cyber": 3, "minimal-premium": 3, "chalk-paper": 3, "retro-pixel": 2, "pop-colorful": 2},
    "generic": {k: 1 for k in STYLES},
}


def _h(key: str) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:10], 16)


def pick_style(text: str, world: str, seed: int, forced: str = "") -> tuple[str, str]:
    """(style id, why). A style named in the words or design.style wins; otherwise a seeded weighted pick that suits the world."""
    if forced in STYLES:
        return forced, "design.style"
    hits = [(sum(text.count(k) for k in v["keys"]), i, sid) for i, (sid, v) in enumerate(STYLES.items())]
    hits = [h for h in hits if h[0] > 0]
    if hits:
        hits.sort(key=lambda x: (-x[0], x[1]))
        return hits[0][2], "words"
    opts = WORLD_STYLE.get(world or "generic", WORLD_STYLE["generic"])
    total = sum(opts.values())
    r = _h(f"{world}|{seed}|style") % total
    for sid, w in sorted(opts.items()):
        if r < w:
            return sid, "seed"
        r -= w
    return next(iter(opts)), "seed"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--words", default="")
    ap.add_argument("--world", default="")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    print(json.dumps(dict(zip(("style", "why"), pick_style(a.words, a.world, a.seed))), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
