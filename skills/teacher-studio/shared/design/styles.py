#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Shared style taxonomy (games AND slides): 12 styles, each with its own composition language (grid, type, ornament, backdrop: not a palette swap). Lives in shared/design; scripts/style_auto.py (game) re-exports it.

A WORLD (theme_auto.py: space, sea, fairy ... = props, character, signature drawing) is orthogonal to a STYLE (this file = how it is staged:
palette, background generator, layout, button/card/scoreboard/title treatments, transitions). Same world x different style = different look.

  neon-cyber        먹빛 테크        matte ink, ivory type, mist-blue signal + brass; ledger grid, hairline cards (the old neon grid is retired)
  gold-luxury       먹과 놋쇠        warm ink + brass, serif headline, one inset frame, poster grid
  pop-colorful      팝 블록          cool white, two flat colour blocks, heavy tight type, sticker cards
  festival-party    축제 포스터      riso poster: coral + teal paper-cut edge shapes, centred stack
  tv-gameshow       스튜디오 쇼      petrol set, amber marquee line, tonal panels, scoreboard banner (no light beams)
  glass-3d          소프트 뎁스      slate planes at three depths, matte cards, one falling shadow (no blur blobs)
  anime-cartoon     만화 컷          comic panels with an ink line, halftone corner, red + ink blue
  pastel-cute       파스텔           blush + plum + mint, soft hills, fully rounded
  retro-pixel       픽셀             square UI on an 8px grid, phosphor green + amber
  minimal-premium   에디토리얼       cool off-white (not cream), ink, one ochre accent, hairlines, asymmetric grid, no props
  chalk-paper       칠판             board green, chalk yellow, dashed chalk frames
  nature-calm       자연             sage paper, forest + wheat, flat tonal bands, editorial stack
Each style also names its grid, type treatment, radius and its two allowed ornaments (shared/design/system.py, DESIGN-RULES.md).
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

# Each style is a COMPOSITION LANGUAGE, not a recolour: its own grid (system.GRIDS), type treatment, ornament pair (system.ORNAMENTS, max two),
# corner radius and backdrop. Palettes are built in OKLCH by system.palette(): a tinted neutral ramp + ONE primary + ONE support colour,
# every text pair contrast-fitted, good/bad apart for colour-blind eyes, no fluorescent colour (system.is_neon), no cream paper.
#   name = what the teacher sees   grid = named layout grid   type = display treatment (weight, tracking em, label case)
#   orn  = the only two ornaments this style may use           rad  = corner radius px on the 1920 stage
STYLES: dict[str, dict] = {
    # 먹빛 테크 (was: neon grid). Matte ink, ivory type, one mist-blue signal + brass. Ledger grid, hairline cards, small tracked labels. No glow.
    "neon-cyber": {"name": "먹빛 테크", "keys": ["네온", "사이버", "미래", "게임", "해킹", "코딩", "테크"], "dark": True, "bg": "dotgrid", "pattern": "none", "font": "TS Sans", "music": "tension", "motion": "normal",
        "grid": "ledger", "type": {"w": 700, "tr": -0.04, "label": "tracked"}, "orn": ["kicker", "grain"], "rad": 6,
        "pal": {"bg1": "#11100f", "bg2": "#191816", "text": "#f4f0e7", "card": "#1e1d1b", "cardText": "#f4f0e7", "cardBorder": "#383633", "primary": "#8ac6d5", "btnText": "#071417", "accent": "#d7ac68", "good": "#79e5eb", "bad": "#e76444"},
        "layout": {"split": 4, "news": 4, "poster": 1, "stack": 1}, "choice": {"tile": 5, "neon": 2}, "card": {"default": 4, "ticket": 2}, "score": {"led": 4, "banner": 2}, "title": {"underline": 4, "default": 3},
        "transition": {"wipe": 2, "fade": 3}, "props": False, "css": "neon"},
    # 먹과 놋쇠 (was: black + gold bokeh). Warm ink, brass, a serif headline, one inset frame. Poster grid, generous margins.
    "gold-luxury": {"name": "먹과 놋쇠", "keys": ["골드", "럭셔리", "고급", "송년", "연말", "시상", "품격", "우아", "프리미엄 파티"], "dark": True, "bg": "frame", "pattern": "none", "font": "Noto Serif KR", "music": "upbeat", "motion": "calm",
        "grid": "poster", "type": {"w": 600, "tr": -0.02, "label": "tracked"}, "orn": ["frame", "rule"], "rad": 2,
        "pal": {"bg1": "#110e0b", "bg2": "#191511", "text": "#f6efe8", "card": "#1d1a17", "cardText": "#f6efe8", "cardBorder": "#38332e", "primary": "#d7ac68", "btnText": "#161107", "accent": "#dcd0b8", "good": "#79e5eb", "bad": "#e76444"},
        "layout": {"poster": 5, "news": 2, "split": 2, "stack": 1}, "choice": {"tile": 4, "pill": 1}, "card": {"ticket": 3, "default": 3}, "score": {"banner": 5}, "title": {"underline": 5, "default": 1},
        "transition": {"fade": 5}, "props": False, "css": "gold"},
    # 팝 블록. Cool white paper, two flat colour blocks bleeding off the corners, heavy tight type, sticker cards with ONE ink offset shadow.
    "pop-colorful": {"name": "팝 블록", "keys": ["팝", "컬러풀", "발랄", "신나", "신남", "알록달록"], "dark": False, "bg": "blocks", "pattern": "none", "font": "TS Sans", "music": "upbeat", "motion": "high",
        "grid": "bento", "type": {"w": 800, "tr": -0.045, "label": "plain"}, "orn": ["corner", "numeral"], "rad": 20,
        "pal": {"bg1": "#f6f8fa", "bg2": "#eaecef", "text": "#171b20", "card": "#ffffff", "cardText": "#171b20", "cardBorder": "#c1c4c7", "primary": "#cc342d", "btnText": "#fff8f7", "accent": "#305eb7", "good": "#005c75", "bad": "#cb4a2a"},
        "layout": {"bento": 5, "poster": 2, "split": 2, "stack": 1}, "choice": {"stamp": 4, "tile": 3}, "card": {"round": 2, "default": 3}, "score": {"sticker": 5, "banner": 1}, "title": {"stamp": 4, "default": 2},
        "transition": {"iris": 2, "wipe": 3}, "props": True, "css": "pop"},
    # 축제 포스터. Riso-print poster: warm white, coral + teal paper-cut shapes lined up on the edges, a centred stack.
    "festival-party": {"name": "축제 포스터", "keys": ["축제", "파티", "생일", "운동회", "잔치", "페스티벌", "기념일"], "dark": False, "bg": "papercut", "pattern": "none", "font": "TS Sans", "music": "upbeat", "motion": "high",
        "grid": "stack", "type": {"w": 800, "tr": -0.04, "label": "plain"}, "orn": ["corner", "rule"], "rad": 28,
        "pal": {"bg1": "#fef3f2", "bg2": "#f4e7e5", "text": "#201918", "card": "#fffcfc", "cardText": "#201918", "cardBorder": "#cdbdbc", "primary": "#ca435f", "btnText": "#fffafb", "accent": "#209993", "good": "#005c75", "bad": "#cb4a2a"},
        "layout": {"stack": 4, "bento": 3, "poster": 2, "split": 1}, "choice": {"pill": 5, "note": 1}, "card": {"round": 4, "polaroid": 1}, "score": {"sticker": 3, "banner": 3}, "title": {"stamp": 3, "underline": 2},
        "transition": {"iris": 3, "fade": 2}, "props": True, "css": "party"},
    # 스튜디오 쇼 (was: stage lights + LED wall). Deep petrol set, amber marquee line, vertical tonal panels, split grid, a scoreboard banner.
    "tv-gameshow": {"name": "스튜디오 쇼", "keys": ["게임쇼", "방송", "퀴즈쇼", "대결", "최종 결전", "도전"], "dark": True, "bg": "panels", "pattern": "none", "font": "TS Sans", "music": "upbeat", "motion": "high",
        "grid": "split", "type": {"w": 800, "tr": -0.035, "label": "tracked"}, "orn": ["edge", "rule"], "rad": 10,
        "pal": {"bg1": "#071c27", "bg2": "#0a2533", "text": "#e9f2f7", "card": "#142935", "cardText": "#e9f2f7", "cardBorder": "#234559", "primary": "#eeb154", "btnText": "#171008", "accent": "#69bbba", "good": "#79e5eb", "bad": "#e76444"},
        "layout": {"news": 4, "split": 4, "bento": 1}, "choice": {"tile": 4, "pill": 2}, "card": {"ticket": 4, "default": 2}, "score": {"banner": 5, "led": 1}, "title": {"underline": 3, "stamp": 2},
        "transition": {"wipe": 4, "fade": 1}, "props": False, "css": "show"},
    # 소프트 뎁스 (was: glass over colour blobs). Slate planes at three depths, matte cards with one soft falling shadow, bento tiles.
    "glass-3d": {"name": "소프트 뎁스", "keys": ["글래스", "3D", "3d", "유리", "입체", "모던", "세련"], "dark": True, "bg": "planes", "pattern": "none", "font": "TS Sans", "music": "mystery", "motion": "normal",
        "grid": "bento", "type": {"w": 700, "tr": -0.035, "label": "plain"}, "orn": ["edge", "grain"], "rad": 28,
        "pal": {"bg1": "#111724", "bg2": "#171f2f", "text": "#ecf0f9", "card": "#1d2432", "cardText": "#ecf0f9", "cardBorder": "#343e55", "primary": "#7dcece", "btnText": "#061414", "accent": "#d9a3d3", "good": "#79e5eb", "bad": "#e76444"},
        "layout": {"bento": 5, "split": 3, "poster": 1}, "choice": {"pill": 3, "tile": 3}, "card": {"round": 5, "default": 1}, "score": {"banner": 3, "sticker": 2}, "title": {"default": 4, "underline": 2},
        "transition": {"fade": 4, "iris": 1}, "props": False, "css": "glass"},
    # 만화 컷. Cool paper, comic panels with a 4px ink line, a halftone corner, red + ink blue, heavy type with a flat offset.
    "anime-cartoon": {"name": "만화 컷", "keys": ["애니", "카툰", "만화", "웹툰", "히어로"], "dark": False, "bg": "halftone", "pattern": "none", "font": "TS Sans", "music": "sports", "motion": "high",
        "grid": "split", "type": {"w": 800, "tr": -0.045, "label": "plain"}, "orn": ["corner", "grain"], "rad": 12,
        "pal": {"bg1": "#f4f8fb", "bg2": "#e8edf1", "text": "#161b20", "card": "#ffffff", "cardText": "#161b20", "cardBorder": "#bec4c9", "primary": "#cc272e", "btnText": "#fff8f8", "accent": "#234993", "good": "#005c75", "bad": "#cb4a2a"},
        "layout": {"split": 4, "bento": 3, "news": 2}, "choice": {"stamp": 4, "tile": 3}, "card": {"default": 4, "ticket": 2}, "score": {"sticker": 4, "banner": 2}, "title": {"stamp": 5, "default": 1},
        "transition": {"wipe": 4, "iris": 1}, "props": True, "css": "anime"},
    # 파스텔. Blush paper, plum type, mint support, soft hills, fully rounded cards.
    "pastel-cute": {"name": "파스텔", "keys": ["파스텔", "귀엽", "귀여", "동화", "유아", "저학년", "몽글"], "dark": False, "bg": "hills", "pattern": "none", "font": "TS Sans", "music": "cute", "motion": "normal",
        "grid": "bento", "type": {"w": 760, "tr": -0.035, "label": "plain"}, "orn": ["corner", "kicker"], "rad": 40,
        "pal": {"bg1": "#fdedf4", "bg2": "#f4e0e8", "text": "#1f181b", "card": "#fff6fa", "cardText": "#1f181b", "cardBorder": "#ceb6c0", "primary": "#954074", "btnText": "#fff8fb", "accent": "#65af9c", "good": "#005c75", "bad": "#cb4a2a"},
        "layout": {"bento": 4, "stack": 3, "poster": 1}, "choice": {"pill": 5, "note": 1}, "card": {"round": 5, "polaroid": 1}, "score": {"sticker": 4, "banner": 1}, "title": {"underline": 4, "default": 2},
        "transition": {"iris": 3, "fade": 3}, "props": True, "css": "pastel"},
    # 픽셀. A deliberate genre look: square UI, 8px grid, phosphor green + amber on CRT ink, hard 1-step shadows. No scanline glow.
    "retro-pixel": {"name": "픽셀", "keys": ["레트로", "픽셀", "8비트", "오락실", "아케이드", "도트"], "dark": True, "bg": "pixel", "pattern": "none", "font": "TS Sans", "music": "upbeat", "motion": "high",
        "grid": "split", "type": {"w": 800, "tr": 0.02, "label": "tracked"}, "orn": ["grain", "edge"], "rad": 0,
        "pal": {"bg1": "#141327", "bg2": "#1c1a34", "text": "#efeff8", "card": "#212035", "cardText": "#efeff8", "cardBorder": "#3a385b", "primary": "#7cdd93", "btnText": "#0b140d", "accent": "#e8a95c", "good": "#79e5eb", "bad": "#e76444"},
        "layout": {"split": 4, "news": 3, "stack": 2}, "choice": {"tile": 6}, "card": {"default": 5}, "score": {"led": 5, "banner": 1}, "title": {"default": 3, "stamp": 3},
        "transition": {"wipe": 5}, "props": True, "css": "pixel"},
    # 에디토리얼. Cool off-white (not cream), ink, one ochre accent. Asymmetric editorial grid, hairlines, lots of white, no props.
    "minimal-premium": {"name": "에디토리얼", "keys": ["미니멀", "심플", "프리미엄", "깔끔", "모노", "화이트", "에디토리얼"], "dark": False, "bg": "minimal", "pattern": "none", "font": "TS Sans", "music": "mystery", "motion": "calm",
        "grid": "editorial", "type": {"w": 700, "tr": -0.04, "label": "tracked"}, "orn": ["rule", "kicker"], "rad": 2,
        "pal": {"bg1": "#f4f6f8", "bg2": "#e8eaed", "text": "#161b20", "card": "#fcfdff", "cardText": "#161b20", "cardBorder": "#bfc2c5", "primary": "#1a2026", "btnText": "#f6fbff", "accent": "#a38043", "good": "#005c75", "bad": "#cb4a2a"},
        "layout": {"poster": 4, "split": 4, "news": 1, "stack": 1}, "choice": {"tile": 5, "pill": 1}, "card": {"default": 5}, "score": {"banner": 3, "chalk": 2}, "title": {"underline": 4, "default": 3},
        "transition": {"fade": 6}, "props": False, "css": "minimal"},
    # 칠판. Board green, chalk yellow, dashed chalk frames, a stack of rows like board writing.
    "chalk-paper": {"name": "칠판", "keys": ["칠판", "종이", "분필", "노트", "교실", "수업"], "dark": True, "bg": "chalk", "pattern": "none", "font": "TS Sans", "music": "cute", "motion": "calm",
        "grid": "stack", "type": {"w": 700, "tr": -0.02, "label": "plain"}, "orn": ["frame", "rule"], "rad": 14,
        "pal": {"bg1": "#253d32", "bg2": "#29473a", "text": "#e9f3ee", "card": "#334b40", "cardText": "#e9f3ee", "cardBorder": "#446c5a", "primary": "#eed780", "btnText": "#141207", "accent": "#eda9a8", "good": "#79e5eb", "bad": "#ec6949"},
        "layout": {"stack": 4, "split": 3, "poster": 1}, "choice": {"stamp": 3, "note": 3}, "card": {"default": 4, "polaroid": 1}, "score": {"chalk": 6}, "title": {"underline": 4, "default": 2},
        "transition": {"fade": 4, "wipe": 1}, "props": True, "css": "chalk"},
    # 자연. Sage paper, forest green, wheat. Flat tonal bands along the bottom (not the pastel hills), editorial stack, soft radius.
    "nature-calm": {"name": "자연", "keys": ["자연", "차분", "숲", "힐링", "식물", "정원", "생태"], "dark": False, "bg": "bands", "pattern": "none", "font": "TS Sans", "music": "nature", "motion": "calm",
        "grid": "editorial", "type": {"w": 700, "tr": -0.035, "label": "plain"}, "orn": ["rule", "corner"], "rad": 20,
        "pal": {"bg1": "#ecf6ea", "bg2": "#e0ebdd", "text": "#181c17", "card": "#f4fdf2", "cardText": "#181c17", "cardBorder": "#b6c3b3", "primary": "#296a3b", "btnText": "#f1fef3", "accent": "#c69449", "good": "#005c75", "bad": "#cb4a2a"},
        "layout": {"stack": 4, "split": 3, "poster": 2}, "choice": {"pill": 3, "tile": 3}, "card": {"round": 3, "default": 3}, "score": {"banner": 3, "sticker": 2}, "title": {"underline": 4, "default": 2},
        "transition": {"fade": 5, "iris": 1}, "props": True, "css": "nature"},
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


def _hits(text: str) -> list[tuple[int, int, str]]:
    hits = [(sum(text.count(k) for k in v["keys"]), i, sid) for i, (sid, v) in enumerate(STYLES.items())]
    hits = [h for h in hits if h[0] > 0]
    hits.sort(key=lambda x: (-x[0], x[1]))
    return hits


def pick_style(text: str, world: str, seed: int, forced: str = "", priority: str = "") -> tuple[str, str]:
    """(style id, why). Order of authority: design.style > style words in `priority` (design.words + design.mood) > style words in the rest of
    `text` (title, subtitle, subject) > a seeded weighted pick that suits the world. So a title such as "AI 연수" can never beat an explicit "미니멀"."""
    if forced in STYLES:
        return forced, "design.style"
    hits = _hits(priority) if priority else []
    if hits:
        return hits[0][2], "words"
    hits = _hits(text)
    if hits:
        return hits[0][2], "title"
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
