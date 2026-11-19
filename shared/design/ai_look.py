#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Anti "AI-default look" check (stdlib only): does a page look like a well-known AI company's house style instead of a design of its own?

Rule: never default to an AI-company house look. The user's own palette / template always wins (then this check stays quiet).

Measured, not guessed. Colours are read in OKLCH (oklch.py): L = lightness 0..1, C = chroma (colourfulness), h = hue in degrees.

1. "AI house" combo (cream paper + serif headline, with any accent; terracotta/clay is the classic one). WARN when the first and third hold (the accent is reported but not required):
   - CREAM background : L >= 0.88, 0.004 <= C <= 0.07, 55 <= h <= 110       (warm off-white / beige / linen; pure white and grey have C < 0.004)
   - CLAY accent      : 0.42 <= L <= 0.78, 0.07 <= C <= 0.19, 32 <= h <= 62  (terracotta, clay, burnt orange; e.g. #d97757 = L .67 C .13 h 39)
                        h < 32 is red / dancheong vermilion (#a82920 = h 29) and h > 62 is ochre / gold (#b08d3c = h 86): both are not this look.
   - SERIF headline   : the heading font family is a serif (Noto Serif KR, Gowun Batang, Nanum Myeongjo, Song Myung, Georgia, Times, Playfair, Lora,
                        Tiempos, Copernicus, Source Serif ... or a bare `serif` generic).
2. Generic AI tell: a blue -> purple gradient (two or more gradient colours with C >= 0.10 and 250 <= h <= 315, at least 25 degrees apart) on a white or
   near-white page (L >= 0.93, C <= 0.03) TOGETHER WITH an emoji-heavy hero (>= 3 emoji in the headings or the first 600 characters of text).

Either is a WARN (never FAIL): taste is the teacher's call, but the default must not drift there.

    from ai_look import is_house, check_tokens, check_html, html_results
    is_house("#faf9f5", ["#d97757"], "Noto Serif KR")    # -> True
    html_results(page_html)                                # -> [("WARN", "...")] / [("PASS", "...")] / [] (nothing measurable)

CLI:  python3 ai_look.py --html page.html | --colors BG ACCENT [ACCENT...] --font "Noto Serif KR"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oklch  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

CREAM = {"L_min": 0.88, "C_min": 0.004, "C_max": 0.07, "h_min": 55.0, "h_max": 110.0}
CLAY = {"L_min": 0.42, "L_max": 0.78, "C_min": 0.07, "C_max": 0.19, "h_min": 32.0, "h_max": 62.0}
WHITE = {"L_min": 0.93, "C_max": 0.03}
BLUE_PURPLE = {"C_min": 0.10, "h_min": 250.0, "h_max": 315.0, "spread": 25.0}
EMOJI_MIN = 3
SERIF_WORDS = ("serif kr", "noto serif", "batang", "바탕", "myeongjo", "명조", "song myung", "georgia", "times", "playfair", "lora", "tiempos",
               "copernicus", "source serif", "merriweather", "garamond", "libre baskerville", "crimson", "fraunces", "dm serif", "nanum myeongjo")
USER_MARKERS = re.compile(r'"userPalette"\s*:\s*true|"palette"\s*:\s*"user"|data-user-design|data-own-palette|"palette_from"\s*:', re.I)
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
_EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")


def _ok_hex(c) -> bool:
    return isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", c.strip()) is not None


def is_cream(bg: str) -> bool:
    if not _ok_hex(bg):
        return False
    L, C, h = oklch.hex_to_oklch(bg)
    return L >= CREAM["L_min"] and CREAM["C_min"] <= C <= CREAM["C_max"] and CREAM["h_min"] <= h <= CREAM["h_max"]


def is_clay(c: str) -> bool:
    if not _ok_hex(c):
        return False
    L, C, h = oklch.hex_to_oklch(c)
    return CLAY["L_min"] <= L <= CLAY["L_max"] and CLAY["C_min"] <= C <= CLAY["C_max"] and CLAY["h_min"] <= h <= CLAY["h_max"]


def is_serif(family: str) -> bool:
    f = (family or "").lower()
    if any(w in f for w in SERIF_WORDS):
        return True
    first = f.split(",")[0].strip().strip("'\"")
    return first == "serif"


def is_house(bg: str, accents, heading_font: str) -> bool:
    """Cream paper + serif headline (the accent hue no longer matters: terracotta, gold ... all read as the same house look)."""
    accents = [accents] if isinstance(accents, str) else list(accents or [])
    return is_cream(bg) and is_serif(heading_font)  # cream paper + serif headline reads as the house look whatever the accent hue (clay, gold, ...)


def measure(bg: str, accents, heading_font: str) -> dict:
    accents = [accents] if isinstance(accents, str) else list(accents or [])
    return {"bg": bg, "bg_oklch": [round(x, 3) for x in oklch.hex_to_oklch(bg)] if _ok_hex(bg) else None,
            "cream_bg": is_cream(bg), "clay_accent": [a for a in accents if is_clay(a)], "serif_heading": is_serif(heading_font),
            "heading_font": heading_font, "house": is_house(bg, accents, heading_font)}


def check_tokens(tokens: dict) -> list[str]:
    """Problems in design tokens (design.py / deck_style / shell tokens). [] when fine or when the colours are the user's own."""
    if tokens.get("userPalette") or tokens.get("palette") == "user" or tokens.get("user"):
        return []
    c = tokens.get("colors", tokens)
    bg = c.get("bg1") or c.get("bg")
    acc = [c.get(k) for k in ("primary", "accent", "pr", "ac", "brand") if c.get(k)]
    f = tokens.get("fonts", {})
    font = (f.get("display") if isinstance(f, dict) else "") or tokens.get("font_display") or tokens.get("font") or ""
    return [house_line()] if is_house(bg, acc, font) else []


def house_line() -> str:
    return ("AI 회사 기본 느낌: 크림색 배경 + 명조(세리프) 제목 조합이에요(강조색이 뭐든). 흔한 'AI가 만든 티'가 나요. "
            "배경을 흰색·다른 색으로, 강조색을 다른 색으로, 또는 제목을 고딕으로 바꿔 주세요 (선생님 로고·양식 색이면 그대로 두셔도 돼요).")


def gradient_line() -> str:
    return "AI 기본 느낌: 흰 바탕에 파랑-보라 그라데이션 + 이모지가 많은 첫 화면이에요. 그라데이션이나 이모지를 줄이고 주제에 맞는 색 하나를 골라 주세요."


# ---------- reading a built page ----------
_VAR_BG = ("bg1", "bg", "background", "paper", "page", "surface-bg", "sk-bg")
_VAR_AC = ("primary", "pr", "accent", "ac", "brand", "clay", "sk-pr", "sk-ac")
_VAR_FONT = ("font-display", "fd", "display", "font-head", "heading-font", "ff-display", "sk-fd")


def _css_vars(html: str) -> dict:
    out: dict = {}
    for k, v in re.findall(r"--([\w-]+)\s*:\s*([^;}\n]+)", html):
        out.setdefault(k.lower(), v.strip())
    return out


def _rule(html: str, selector_pat: str, prop: str) -> str:
    for m in re.finditer(r"(?:^|[}\s,>;])(?:%s)\s*(?:,[^{]*)?\{([^}]*)\}" % selector_pat, html):
        pm = re.search(r"(?:^|;)\s*%s\s*:\s*([^;]+)" % prop, m.group(1))
        if pm:
            return pm.group(1).strip()
    return ""


def _resolve(val: str, vars_: dict, depth: int = 0) -> str:
    m = re.search(r"var\(\s*--([\w-]+)", val or "")
    if m and depth < 4:
        return _resolve(vars_.get(m.group(1).lower(), ""), vars_, depth + 1)
    return val or ""


def page_tokens(html: str) -> dict:
    """bg, accents and heading font as a page declares them (CSS variables first, then body/h1 rules)."""
    v = _css_vars(html)
    bg = next((_resolve(v[k], v) for k in _VAR_BG if k in v and HEX.search(_resolve(v[k], v))), "")
    if not bg:
        bg = _resolve(_rule(html, r"body", r"background(?:-color)?"), v)
    bgm = HEX.search(bg or "")
    acc = []
    for k in _VAR_AC:
        if k in v:
            m = HEX.search(_resolve(v[k], v))
            if m:
                acc.append(m.group(0).lower())
    font = next((_resolve(v[k], v) for k in _VAR_FONT if k in v), "")
    if not font:
        font = _resolve(_rule(html, r"h1|\.title|\.hero h1|h1\.title", "font-family"), v)
    if not font:
        font = _resolve(_rule(html, r"body", "font-family"), v)
    return {"bg": bgm.group(0).lower() if bgm else "", "accents": acc, "font": font.strip()}


def _gradient_tell(html: str, bg: str) -> bool:
    if not bg or not _ok_hex(bg):
        return False
    L, C, _h = oklch.hex_to_oklch(bg)
    if L < WHITE["L_min"] or C > WHITE["C_max"]:
        return False
    for g in re.findall(r"(?:linear|radial|conic)-gradient\(([^;]*?)\)\s*[;}]", html):
        hues = []
        for c in HEX.findall(g):
            Lc, Cc, hc = oklch.hex_to_oklch(c)
            if Cc >= BLUE_PURPLE["C_min"] and BLUE_PURPLE["h_min"] <= hc <= BLUE_PURPLE["h_max"]:
                hues.append(hc)
        if len(hues) >= 2 and max(hues) - min(hues) >= BLUE_PURPLE["spread"]:
            return True
    return False


def _emoji_heavy(html: str) -> bool:
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    heads = " ".join(re.findall(r"<h[12][^>]*>(.*?)</h[12]>", body, flags=re.S | re.I))
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text).strip()[:600]
    return len(_EMOJI.findall(heads)) >= EMOJI_MIN or len(_EMOJI.findall(text)) >= EMOJI_MIN


def check_html(html: str) -> list[str]:
    """Plain-Korean WARN lines for a built page ([] = fine / nothing measurable / the user's own design)."""
    if USER_MARKERS.search(html or ""):
        return []
    t = page_tokens(html or "")
    out = []
    if t["bg"] and is_house(t["bg"], t["accents"], t["font"]):
        out.append(house_line())
    if _gradient_tell(html, t["bg"]) and _emoji_heavy(html):
        out.append(gradient_line())
    return out


def html_results(html: str) -> list[tuple[str, str]]:
    """For the checkers: WARN lines, one PASS line when a background could be measured, [] otherwise."""
    try:
        if USER_MARKERS.search(html or ""):
            return [("PASS", "not an AI-company house look (user's own design wins)")]
        warns = check_html(html)
        if warns:
            return [("WARN", w) for w in warns]
        return [("PASS", "not an AI-company house look (cream+clay+serif / blue-purple+emoji)")] if page_tokens(html)["bg"] else []
    except Exception:  # a taste hint must never break a check
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html")
    ap.add_argument("--colors", nargs="*", help="BG then accent colours")
    ap.add_argument("--font", default="")
    a = ap.parse_args()
    if a.html:
        h = Path(a.html).read_text(encoding="utf-8", errors="replace")
        print(json.dumps({"tokens": page_tokens(h), "warn": check_html(h)}, ensure_ascii=False, indent=1))
    elif a.colors:
        print(json.dumps(measure(a.colors[0], a.colors[1:], a.font), ensure_ascii=False, indent=1))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
