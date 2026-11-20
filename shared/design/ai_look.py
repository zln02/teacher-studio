#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Anti "AI-default look" check + 「밤티 검사」 (stdlib only): does a page look like a well-known AI company's house style instead of a design of its own?

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

3. 「밤티 검사」 (bamti / pro_gate): the generated-not-designed tells, measured on the page's CSS text.
   glow     coloured blur without offset (box/text-shadow `0 0 Npx colour`, drop-shadow(0 0 ..)) more than 2 times
   hollow   outlined unfilled type (-webkit-text-stroke > 0)             gradient  2+ gradients through clearly different hues
   accents  more than 3 accent hues among the theme colours               neon      a fluorescent theme colour (system.is_neon)
   emoji    more than 3 emoji in the headings                             weight    font-weight 900 more than twice
   grid     > 40% of the spacing values off the 4px step                  density   one element with more than 5 stacked decoration layers
   fonts    more than 3 named font families                               italic    slanted Korean text       leading  body line-height < 1.3
   pro_gate() groups them into the five criteria of 「전문 디자이너가 그대로 쓸 수준인가?」: type / colour / surface / rhythm / restraint.

All are WARN (never FAIL): taste is the teacher's call, but the default must not drift there. All are silent for the user's own design.

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
            return [("WARN", w) for w in warns] + bamti_results(html)
        return ([("PASS", "not an AI-company house look (cream+clay+serif / blue-purple+emoji)")] if page_tokens(html)["bg"] else []) + bamti_results(html)
    except Exception:  # a taste hint must never break a check
        return []


# =====================================================================================================================
# 「밤티 검사」 (2026-11): does the page look generated instead of designed?  WARN only, quiet for the user's own design.
# Rules in words: DESIGN-RULES.md. Everything is measured on the page's CSS text (static, no browser), after the shared
# polish layer when the page carries one (rules before the "ds:polish" marker are overridden by it and are not counted).
# =====================================================================================================================
POLISH_MARK = "design system polish"
BAMTI = {"glow_max": 2, "hollow_max": 0, "soup_max": 1, "accent_hues_max": 3, "emoji_hero_max": 3, "w900_max": 2, "offgrid_share": 0.4, "offgrid_min_n": 14,
         "layers_max": 5, "families_max": 3, "body_leading_min": 1.3}
_DATA = re.compile(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]+")
_STATE_NAMES = ("good", "bad", "ok", "err", "warn", "danger", "success", "team", "tc", "series", "chart", "gd", "bd", "on-")
_SHADOW = re.compile(r"(?:box-shadow|text-shadow)\s*:\s*([^;}]+)", re.I)
_GLOW_LAYER = re.compile(r"^(?:inset\s+)?0(?:px)?\s+0(?:px)?\s+(\d*\.?\d+)(?:px|em|rem|cqw)(?:\s+0(?:px)?)?\s+(.+)$", re.I)
_GENERIC = {"serif", "sans-serif", "monospace", "system-ui", "ui-sans-serif", "ui-monospace", "cursive", "fantasy", "inherit", "-apple-system", "blinkmacsystemfont"}
_FALLBACKS = ("malgun", "맑은", "apple sd", "segoe", "arial", "helvetica", "noto sans cjk", "batang", "함초롬", "gulim", "dotum", "consolas", "courier", "menlo", "d2coding",
              "sfmono", "georgia", "times", "pretendard", "nanum")


def _styles_of(html: str) -> str:
    """The page's CSS text: <style> blocks (font data removed) + inline style attributes. With the polish layer present, only what comes after it."""
    h = _DATA.sub("", html or "")
    css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", h, flags=re.S | re.I))
    if POLISH_MARK in css:
        css = css[css.index(POLISH_MARK):]
    inline = " ".join("x{%s}" % m for m in re.findall(r'\sstyle="([^"]*)"', re.sub(r"<(script|style)\b.*?</\1>", " ", h, flags=re.S | re.I)))
    return css + "\n" + inline


def _chromatic(val: str, vars_: dict) -> bool:
    """True when a shadow colour is a real colour (not black / white / grey): a glow, not a shade."""
    v = _resolve(val, vars_) if "var(" in val else val
    m = HEX.search(v)
    if m:
        return oklch.hex_to_oklch(m.group(0))[1] >= 0.06
    m = re.search(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)", v)
    if m:
        r, g, b = (int(x) for x in m.groups())
        return oklch.hex_to_oklch("#%02x%02x%02x" % (min(r, 255), min(g, 255), min(b, 255)))[1] >= 0.06
    if "var(" in val:   # an unresolved theme colour (--primary, --accent ...) used as a blur = a glow
        return not re.search(r"var\(\s*--(?:shadow|ds-shadow|ds-press|line|ln|ink|bg)", val)
    return "currentcolor" in v.lower()


def _split_layers(v: str) -> list[str]:
    return [x.strip() for x in re.split(r",(?![^(]*\))", v) if x.strip()]


def count_glow(css: str, vars_: dict | None = None) -> int:
    """Coloured blur with no offset (the neon-sign effect): box-shadow / text-shadow `0 0 Npx <colour>`, drop-shadow(0 0 ...)."""
    vars_ = vars_ if vars_ is not None else {}
    n = 0
    for m in _SHADOW.finditer(css):
        for layer in _split_layers(m.group(1)):
            g = _GLOW_LAYER.match(layer)
            if g and float(g.group(1)) >= 6 and _chromatic(g.group(2), vars_):
                n += 1
    n += len(re.findall(r"drop-shadow\(\s*0(?:px)?\s+0(?:px)?\s+[1-9]", css))
    return n


def count_hollow(css: str) -> int:
    """Outlined, unfilled display type."""
    return len(re.findall(r"-webkit-text-stroke(?:-width)?\s*:\s*(?!0(?:px)?\b)[\d.]+", css))


def count_gradient_soup(css: str) -> int:
    """Gradients that run through two or more clearly different colours (hues >= 40 degrees apart, both colourful)."""
    n = 0
    for g in re.findall(r"(?:linear|radial|conic)-gradient\(((?:[^()]|\([^()]*\))*)\)", css):
        hues = [oklch.hex_to_oklch(c)[2] for c in HEX.findall(g) if oklch.hex_to_oklch(c)[1] >= 0.09]
        if len(hues) >= 2 and max(oklch.hue_distance(a, b) for a in hues for b in hues) >= 40:
            n += 1
    return n


def accent_hues(html: str) -> list[float]:
    """Distinct accent hues among the page's theme colours (CSS custom properties; state / team / chart colours do not count)."""
    hues: list[float] = []
    for k, v in _css_vars(_DATA.sub("", html or "")).items():
        if any(s in k for s in _STATE_NAMES):
            continue
        m = HEX.fullmatch(v.strip())
        if not m:
            continue
        L, C, h = oklch.hex_to_oklch(m.group(0))
        if C < 0.09 or L < 0.25:
            continue
        if all(oklch.hue_distance(h, x) > 35 for x in hues):
            hues.append(h)
    return hues


def neon_colours(html: str) -> list[str]:
    """Fluorescent theme colours (shared/design/system.py is_neon): high chroma AND light."""
    try:
        import system as _ds
    except Exception:
        return []
    out = []
    for k, v in _css_vars(_DATA.sub("", html or "")).items():
        if any(s in k for s in _STATE_NAMES):
            continue
        m = HEX.fullmatch(v.strip())
        if m and _ds.is_neon(m.group(0)) and m.group(0).lower() not in out:
            out.append(m.group(0).lower())
    return out


def emoji_in_hero(html: str) -> int:
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", html or "", flags=re.S | re.I)
    heads = " ".join(re.findall(r"<h[12][^>]*>(.*?)</h[12]>", body, flags=re.S | re.I))
    return len(_EMOJI.findall(re.sub(r"<[^>]+>", " ", heads)))


def offgrid_share(css: str) -> tuple[float, int]:
    """Share of spacing values (padding / margin / gap, px, >= 4) that are not on the 4px half-step of the 8pt rhythm."""
    vals = []
    for m in re.finditer(r"(?:padding|margin|gap)(?:-[a-z]+)?\s*:\s*([^;}]+)", css):
        vals += [float(x) for x in re.findall(r"(?<![\w.#-])(\d+(?:\.\d+)?)px", m.group(1))]
    vals = [v for v in vals if v >= 4]
    if not vals:
        return 0.0, 0
    return sum(1 for v in vals if v % 4) / len(vals), len(vals)


def max_layers(css: str) -> int:
    """The busiest single declaration: stacked background gradients or shadow layers."""
    worst = 0
    for m in re.finditer(r"(?:background(?:-image)?|box-shadow)\s*:\s*([^;}]+)", css):
        worst = max(worst, len(_split_layers(m.group(1))) if ("gradient(" in m.group(1) or "shadow" in m.group(0)) else 0)
    return worst


def font_families(css: str) -> list[str]:
    """Named (non-fallback) font families the page asks for."""
    out: list[str] = []
    for m in re.finditer(r"font(?:-family)?\s*:\s*([^;}]+)", css):
        for f in re.findall(r"""["']([^"']+)["']""", m.group(1)):
            fl = f.strip().lower()
            if fl and fl not in _GENERIC and not any(x in fl for x in _FALLBACKS) and fl not in out and not fl.startswith("var("):
                out.append(fl)
    return out


def bamti(html: str) -> list[tuple[str, str]]:
    """[(code, plain-Korean WARN line)] for a built page. [] = clean, nothing measurable, or the user's own design."""
    if not html or USER_MARKERS.search(html):
        return []
    css = _styles_of(html)
    if len(css.strip()) < 40:
        return []
    v = _css_vars(_DATA.sub("", html))
    out: list[tuple[str, str]] = []
    g = count_glow(css, v)
    if g > BAMTI["glow_max"]:
        out.append(("glow", f"빛 번짐(네온) 효과가 {g}군데 있어요. 색이 번지는 그림자(0 0 Npx 색)는 빼고, 아래로 떨어지는 어두운 그림자 하나만 써 주세요."))
    hw = count_hollow(css)
    if hw > BAMTI["hollow_max"]:
        out.append(("hollow", f"속이 빈 테두리 글자가 {hw}군데 있어요. 글자는 속을 채우고, 강조는 색이나 굵기로 해 주세요."))
    gs = count_gradient_soup(css)
    if gs > BAMTI["soup_max"]:
        out.append(("gradient", f"여러 색이 섞인 그라데이션이 {gs}개예요. 바탕은 한 가지 색(또는 같은 색의 밝기 차이)으로 두고 강조색은 한 곳에만 써 주세요."))
    ah = accent_hues(html)
    if len(ah) > BAMTI["accent_hues_max"]:
        out.append(("accents", f"강조색이 {len(ah)}가지예요. 주 색 하나 + 보조 색 하나 + 회색 계열로 줄여 주세요 (정답·오답 색은 따로 세지 않아요)."))
    nc = neon_colours(html)
    if nc:
        out.append(("neon", f"형광색이 있어요({', '.join(nc[:3])}). 채도를 낮춘 색으로 바꿔 주세요 (design.py 팔레트는 모두 형광이 아니에요)."))
    em = emoji_in_hero(html)
    if em > BAMTI["emoji_hero_max"]:
        out.append(("emoji", f"제목에 이모지가 {em}개예요. 제목은 글자로만 두고, 그림은 아이콘 하나로 충분해요."))
    w9 = len(re.findall(r"font-weight\s*:\s*900", css))
    if w9 > BAMTI["w900_max"]:
        out.append(("weight", f"가장 굵은 글씨(900)를 {w9}군데 썼어요. 굵기는 800까지만, 큰 글자일수록 한 단계 가늘게 해 주세요."))
    share, n = offgrid_share(css)
    if n >= BAMTI["offgrid_min_n"] and share > BAMTI["offgrid_share"]:
        out.append(("grid", f"여백 값의 {int(share * 100)}%가 4의 배수가 아니에요({n}개 중). 여백은 4·8·12·16·24·32·48·64 가운데에서 골라 주세요."))
    ml = max_layers(css)
    if ml > BAMTI["layers_max"]:
        out.append(("density", f"한 요소에 장식이 {ml}겹 쌓여 있어요. 무늬·그림자는 한 화면에 한두 가지면 충분해요."))
    fam = font_families(css)
    if len(fam) > BAMTI["families_max"]:
        out.append(("fonts", f"글꼴이 {len(fam)}가지예요({', '.join(fam[:4])}). 한 가지(제목용 명조를 더하면 두 가지)로 맞춰 주세요."))
    if re.search(r"font-style\s*:\s*(?:italic|oblique)", css) and re.search(r"[가-힣]", html):
        out.append(("italic", "기울인 글씨(이탤릭)가 있어요. 한글은 기울이지 않고 굵기나 색으로 강조해 주세요."))
    lm = re.search(r"(?:^|[}\s])body\s*\{[^}]*?line-height\s*:\s*([\d.]+)\s*[;}]", css)
    if lm and float(lm.group(1)) < BAMTI["body_leading_min"] and "/* stage */" not in css and not re.search(r"1920|data-stage|#stage", css[:6000]):
        out.append(("leading", f"본문 줄 간격이 {lm.group(1)}로 빽빽해요. 본문은 1.5 안팎으로 해 주세요."))
    return out


PRO_CRITERIA = (
    ("type", "글꼴은 한두 가지, 굵기 800 이하, 기울임 없음", ("fonts", "weight", "italic")),
    ("colour", "강조색은 주 색 + 보조 색, 형광 없음", ("accents", "neon")),
    ("surface", "빛 번짐·속 빈 글자·여러 색 그라데이션 없음", ("glow", "hollow", "gradient")),
    ("rhythm", "여백이 4·8 단위, 본문 줄 간격 넉넉", ("grid", "leading")),
    ("restraint", "장식은 한두 가지, 제목에 이모지 없음", ("density", "emoji")),
)


def pro_gate(html: str) -> dict:
    """The self-review gate 「전문 디자이너가 그대로 쓸 수준인가?」 as five checkable criteria. {"pass": n, "of": 5, "failed": [(id, label)], "warn": [...]}."""
    warns = bamti(html)
    codes = {c for c, _ in warns}
    failed = [(cid, label) for cid, label, cs in PRO_CRITERIA if codes & set(cs)]
    return {"pass": len(PRO_CRITERIA) - len(failed), "of": len(PRO_CRITERIA), "failed": failed, "warn": warns}


def bamti_results(html: str) -> list[tuple[str, str]]:
    """For the checkers: WARN lines, or one PASS line. Never raises."""
    try:
        if USER_MARKERS.search(html or ""):
            return []
        g = pro_gate(html)
        if not g["warn"]:
            return [("PASS", "밤티 검사 통과: 전문 디자이너 기준 5/5 (글꼴·색·표면·여백·절제)")] if len(_styles_of(html).strip()) >= 40 else []
        return [("WARN", "밤티 검사: " + msg) for _c, msg in g["warn"]] + [("WARN", "전문 디자이너 기준 %d/%d: %s" % (g["pass"], g["of"], " / ".join(l for _i, l in g["failed"])))]
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
        g = pro_gate(h)
        print(json.dumps({"tokens": page_tokens(h), "warn": check_html(h), "bamti": [m for _c, m in g["warn"]], "pro_gate": "%d/%d" % (g["pass"], g["of"]),
                          "failed": [l for _i, l in g["failed"]]}, ensure_ascii=False, indent=1))
    elif a.colors:
        print(json.dumps(measure(a.colors[0], a.colors[1:], a.font), ensure_ascii=False, indent=1))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
