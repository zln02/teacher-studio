#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""껍데기 키트 (shell kit): device frames, background patterns, icons, spot illustrations, badges and ornaments for previews and
mock screens, all driven by design tokens so they always match the chosen style. Stdlib only, offline, no <script>, no outside address.

    import shell
    t = shell.tokens("neon-cyber")                      # a style id from shared/design/styles.py, design tokens, or a flat palette
    t = shell.tokens("pastel-cute", user={"bg1": "#102a43", "primary": "#f0b429"})   # the user's own colours win
    shell.frame("tv", inner_html, t)                     # phone | tablet | tv | board | laptop | a4
    shell.pattern(t)                                     # CSS background for the style (dotgrid, frame, blocks, panels, planes, bands ...)
    shell.icon("bulb", 24)                               # inline SVG (Tabler, MIT); unknown names -> "sparkles"
    shell.icon_for("빛의 반사")                           # icon name chosen from the words
    shell.spot("bulb", t)                                # a small spot illustration (icon on one matte tonal tile)
    shell.character("a")                                 # DiceBear thumbs face (CC0)
    shell.badge("3분", t) / shell.ornament("tape")
    shell.css()                                          # the stylesheet every helper relies on (put once in <style>)
    shell.page(title, body_html, embed=True)             # a full offline page; TS Sans (+ Noto Serif KR) subset embedded when fonttools exists

All text goes through html.escape; colours are accepted only as #rrggbb; fonts come from a fixed list.
Assets: icons.json (Tabler Icons, MIT, LICENSE-tabler.txt), characters/ (DiceBear thumbs, CC0 1.0). Built by tools/build_shell_kit.py.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_DESIGN = next((d for d in (HERE.parent / "design", HERE.parent.parent / "shared" / "design") if (d / "styles.py").exists()), HERE.parent / "design")
_FONTS = next((d for d in (HERE.parent / "fonts", HERE.parent.parent / "shared" / "fonts") if (d / "embed.py").exists()), None)
if str(_DESIGN) not in sys.path:
    sys.path.insert(0, str(_DESIGN))

try:
    import styles as _styles  # noqa: E402
except Exception:  # pragma: no cover - the kit still works with flat palettes
    _styles = None
try:
    import oklch as _ok  # noqa: E402
except Exception:  # pragma: no cover
    _ok = None
try:
    import system as _ds  # noqa: E402  (type scale, tracking, motion, polish layer)
except Exception:  # pragma: no cover
    _ds = None

_HEX = re.compile(r"#[0-9a-fA-F]{6}")
_ICONS: dict | None = None
KINDS = ("phone", "tablet", "tv", "board", "laptop", "a4")
PATTERNS = ("none", "dots", "grid", "paper", "dotgrid", "frame", "blocks", "papercut", "panels", "planes", "halftone", "pixel", "chalk", "bands", "hills")
# retired (2026-11, 「밤티」 pass): neongrid, mesh blobs, confetti spots, light rays, sparkle, leaves. Old names map to their replacement.
_PATTERN_ALIAS = {"neongrid": "dotgrid", "mesh": "planes", "confetti": "papercut", "rays": "panels", "sparkle": "hills", "leaves": "bands", "diamond": "frame"}

# how each style is "dressed". The numbers come from shared/design/styles.py (grid, type, radius, ornaments); only the mock-screen pieces live here:
# pat = backdrop pattern, fx = title treatment (plain | rule | serif | block | under | chalk | pixel), btn = button shape. No glow anywhere.
DRESS = {
    "neon-cyber": dict(r=6, pat="dotgrid", fx="rule", btn="line", serif=False, w=700, tr=-0.04),
    "gold-luxury": dict(r=2, pat="frame", fx="serif", btn="line", serif=True, w=600, tr=-0.02),
    "pop-colorful": dict(r=14, pat="blocks", fx="block", btn="stamp", serif=False, w=800, tr=-0.045),
    "festival-party": dict(r=20, pat="papercut", fx="under", btn="pill", serif=False, w=800, tr=-0.04),
    "tv-gameshow": dict(r=8, pat="panels", fx="rule", btn="tile", serif=False, w=800, tr=-0.035),
    "glass-3d": dict(r=20, pat="planes", fx="plain", btn="soft", serif=False, w=700, tr=-0.035),
    "anime-cartoon": dict(r=10, pat="halftone", fx="block", btn="stamp", serif=False, w=800, tr=-0.045),
    "pastel-cute": dict(r=24, pat="hills", fx="under", btn="pill", serif=False, w=760, tr=-0.035),
    "retro-pixel": dict(r=0, pat="pixel", fx="pixel", btn="tile", serif=False, w=800, tr=0.02),
    "minimal-premium": dict(r=2, pat="none", fx="rule", btn="line", serif=False, w=700, tr=-0.04),
    "chalk-paper": dict(r=10, pat="chalk", fx="chalk", btn="note", serif=False, w=700, tr=-0.02),
    "nature-calm": dict(r=16, pat="bands", fx="under", btn="pill", serif=False, w=700, tr=-0.035),
    "own-palette": dict(r=12, pat="none", fx="plain", btn="pill", serif=False, w=760, tr=-0.035),
    "studio-clean": dict(r=12, pat="none", fx="plain", btn="pill", serif=False, w=760, tr=-0.035),
}
# the harness default when nothing is chosen: cool paper, ink-blue, one warm accent, sans. Deliberately NOT cream + clay + serif.
DEFAULT_PAL = {"bg1": "#f5f7fa", "bg2": "#e9edf2", "text": "#161b22", "card": "#ffffff", "primary": "#2a4fb8", "btnText": "#ffffff", "accent": "#b9853a",
               "good": "#005c75", "bad": "#cb4a2a"}
SERIF_FONTS = {"Noto Serif KR", "Gowun Batang", "Nanum Myeongjo", "Song Myung"}

# words -> icon (first hit wins; Korean classroom vocabulary). Unknown -> a stable pick from GENERIC.
WORDS = [
    (("빛", "반사", "굴절", "렌즈", "전구", "아이디어", "생각"), "bulb"), (("파동", "소리", "음", "진동"), "volume"), (("우주", "행성", "태양계"), "planet"),
    (("별", "별자리"), "stars"), (("로켓", "발사"), "rocket"), (("달", "밤"), "moon"), (("해", "태양", "여름"), "sun"), (("날씨", "비", "기후"), "cloud-rain"),
    (("원자", "분자", "화학", "물질"), "atom"), (("실험", "과학"), "flask"), (("세포", "유전", "DNA", "생명"), "dna"), (("현미경", "관찰"), "microscope"),
    (("식물", "나무", "숲", "자연", "생태"), "trees"), (("잎", "환경"), "leaf"), (("재활용", "분리", "쓰레기"), "recycle"), (("바다", "물고기", "해양"), "fish"),
    (("동물", "강아지", "개"), "dog"), (("고양이",), "cat"), (("꽃", "봄"), "flower"), (("눈", "겨울"), "snowflake"),
    (("수학", "계산", "곱셈", "나눗셈", "덧셈"), "calculator"), (("함수", "방정식", "그래프 함수"), "math-function"), (("도형", "삼각형"), "triangle"), (("측정", "길이", "자"), "ruler"),
    (("역사", "조선", "고려", "왕", "독립", "삼국"), "building-castle"), (("지도", "지리", "독도", "나라", "세계"), "map-2"), (("지구", "국제"), "world"),
    (("영어", "단어", "알파벳", "받아쓰기", "말하기"), "abc"), (("국어", "글쓰기", "작문", "시", "소설", "독서"), "writing"), (("책", "도서", "읽기"), "books"),
    (("음악", "노래", "합창"), "music"), (("미술", "그림", "색"), "palette"), (("체육", "운동", "축구", "경기"), "bike"), (("코딩", "정보", "로봇", "AI", "인공지능"), "robot"),
    (("학부모", "가족", "부모"), "users"), (("학생", "친구", "모둠", "팀"), "users"), (("학교", "교실", "수업", "총회", "설명회"), "school"), (("선생님", "교사"), "user-circle"),
    (("성적", "분석", "점수", "통계", "결과", "보고서", "데이터"), "target"), (("설문",), "writing"), (("일정", "시간", "계획", "시간표"), "clock"), (("타이머", "카운트다운"), "stopwatch"),
    (("안내", "공지", "알림"), "speakerphone"), (("규칙", "약속"), "shield"), (("질문", "퀴즈", "문제", "OX", "ox"), "question-mark"), (("정답", "맞"), "circle-check"),
    (("오답", "틀"), "circle-x"), (("우승", "승리", "1등", "시상", "이기"), "trophy"), (("보상", "메달"), "medal"), (("자물쇠", "방탈출", "탈출", "비밀"), "lock"),
    (("열쇠", "단서"), "key"), (("빙고", "카드", "짝"), "cards"), (("주사위", "보드"), "dice-5"), (("축하", "파티", "생일", "축제"), "confetti"), (("선물",), "gift"),
    (("감사", "마무리", "끝"), "heart"), (("시작", "출발"), "player-play"), (("영상", "비디오", "컷"), "camera"), (("사진", "이미지"), "photo"), (("목표", "핵심"), "target"),
    (("상담", "대화", "소통"), "microphone"), (("돈", "예산", "가계부", "매출"), "calculator"), (("건강", "급식", "음식"), "apple"), (("안전",), "shield"),
]
GENERIC = ("sparkles", "star", "bulb", "rocket", "compass", "flag", "puzzle", "target", "books", "palette")


# ---------------------------------------------------------------- colours ---------------------------------------------------------------
def _hex(c, fallback: str) -> str:
    return c.lower() if isinstance(c, str) and _HEX.fullmatch(c.strip()) else fallback


def _rgb(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def rgba(c: str, a: float) -> str:
    r, g, b = _rgb(_hex(c, "#000000"))
    return "rgba(%d,%d,%d,%.3g)" % (r, g, b, max(0.0, min(1.0, a)))


def mix(a: str, b: str, t: float) -> str:
    """t=0 -> a, t=1 -> b (sRGB)."""
    ra, rb = _rgb(_hex(a, "#000000")), _rgb(_hex(b, "#ffffff"))
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ra, rb))


def _lum(c: str) -> float:
    ch = []
    for v in _rgb(c):
        v /= 255
        ch.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _legible(fg: str, bg: str, need: float) -> str:
    if contrast(fg, bg) >= need:
        return fg
    if _ok:
        try:
            return _ok.fit_contrast(fg, bg, need)
        except Exception:
            pass
    return "#ffffff" if _lum(bg) < 0.4 else "#111111"


# ---------------------------------------------------------------- tokens ----------------------------------------------------------------
def tokens(src=None, user: dict | None = None, name: str = "") -> dict:
    """Normalised shell tokens from a style id / style dict / design tokens / flat palette (None = studio default). `user` colours win."""
    sid, pal, font, dark = "studio-clean", dict(DEFAULT_PAL), "TS Sans", False
    if isinstance(src, str) and _styles and src in _styles.STYLES:
        s = _styles.STYLES[src]
        sid, pal, font, dark = src, dict(s["pal"]), s.get("font", font), bool(s.get("dark"))
    elif isinstance(src, dict) and isinstance(src.get("pal"), dict):
        sid = src.get("id", sid) if src.get("id") in DRESS else ("own-palette" if src.get("id") == "own-palette" else sid)
        pal, font, dark = dict(src["pal"]), src.get("font", font), bool(src.get("dark"))
    elif isinstance(src, dict) and isinstance(src.get("colors"), dict):
        pal = {**DEFAULT_PAL, **src["colors"]}
        f = src.get("fonts") or {}
        font = f.get("display", font) if isinstance(f, dict) else font
        sid = "own-palette" if src.get("userPalette") else (src.get("style") if src.get("style") in DRESS else sid)
    elif isinstance(src, dict):
        pal = {**DEFAULT_PAL, **src}
        sid = src.get("style") if src.get("style") in DRESS else "own-palette"
    own = bool(user)
    if user:
        pal = {**pal, **{k: v for k, v in user.items() if isinstance(v, str) and _HEX.fullmatch(v)}}
        sid = sid if sid in DRESS else "own-palette"
    d = dict(DRESS.get(sid, DRESS["studio-clean"]))
    bg = _hex(pal.get("bg1") or pal.get("bg"), DEFAULT_PAL["bg1"])
    dark = _lum(bg) < 0.18 if (own or sid in ("own-palette", "studio-clean")) else dark
    bg2 = _hex(pal.get("bg2"), mix(bg, "#000000" if not dark else "#ffffff", 0.06))
    ink = _legible(_hex(pal.get("text") or pal.get("tx"), "#f5f5f5" if dark else "#141414"), bg, 4.5)
    surface = _hex(pal.get("card"), mix(bg, "#ffffff", 0.7) if not dark else mix(bg, "#ffffff", 0.08))
    if contrast(ink, surface) < 4.5:
        surface = mix(bg, "#ffffff", 0.75) if not dark else mix(bg, "#ffffff", 0.1)
    card_ink = _legible(_hex(pal.get("cardText"), ink), surface, 4.5)
    primary = _hex(pal.get("primary") or pal.get("pr"), ink)
    on_primary = _hex(pal.get("btnText"), "#ffffff")
    if contrast(on_primary, primary) < 4.5:
        on_primary = "#ffffff" if contrast("#ffffff", primary) >= contrast("#111111", primary) else "#111111"
    accent = _hex(pal.get("accent") or pal.get("ac"), primary)
    serif = d["serif"] or (font in SERIF_FONTS)
    if own:
        serif = False  # the user's colours never inherit our serif headline
    t = {
        "style": sid, "name": name or sid, "dark": dark, "own": own, "font": font, "serif": serif,
        "bg": bg, "bg2": bg2, "surface": surface, "ink": ink, "card_ink": card_ink, "muted": _legible(mix(ink, bg, 0.32), bg, 4.5),
        "primary": primary, "on_primary": on_primary, "accent": accent, "line": mix(ink, bg, 0.82),
        "good": _hex(pal.get("good"), "#005c75"), "bad": _hex(pal.get("bad"), "#cb4a2a"),
        "r": d["r"], "pattern": d["pat"], "fx": d["fx"], "btn": d["btn"], "w": d["w"], "tr": d["tr"],
    }
    t["pr_text"] = _legible(primary, bg, 3.0)
    return t


def font_stack(t: dict, display: bool = True) -> str:
    if display and t.get("serif"):
        return "'Noto Serif KR','Batang',serif"
    return "'TS Sans','Pretendard','Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo',sans-serif"


def vars_style(t: dict) -> str:
    """Inline CSS custom properties for one scope (a mock screen, a card)."""
    keys = {"bg": "bg", "bg2": "bg2", "sf": "surface", "ink": "ink", "ci": "card_ink", "mu": "muted", "pr": "primary", "op": "on_primary", "ac": "accent",
            "ln": "line", "gd": "good", "bd": "bad", "pt": "pr_text"}
    parts = ["--sk-%s:%s" % (k, _hex(t.get(v), "#888888")) for k, v in keys.items()]
    parts += ["--sk-fd:%s" % font_stack(t, True), "--sk-fb:%s" % font_stack(t, False), "--sk-dw:%d" % int(t.get("w", 800)),
              "--sk-tr:%.3fem" % float(t.get("tr", 0)), "--sk-r:%dpx" % int(t.get("r", 12))]
    return ";".join(parts)


# ---------------------------------------------------------------- patterns --------------------------------------------------------------
def pattern(t: dict, kind: str | None = None) -> str:
    """A CSS `background` value (gradients only, no images) for the style's backdrop over its background colour.

    Every backdrop is flat and matte: tonal planes, hairlines and fine grain built from the palette's own neutrals, with at most ONE accent shape.
    No glow, no multi-colour gradient, no scattered confetti. (Rules: shared/design/DESIGN-RULES.md, ornaments.)"""
    k = kind or t.get("pattern", "none")
    k = _PATTERN_ALIAS.get(k, k)
    bg, bg2, pr, ac, ink = t["bg"], t["bg2"], t["primary"], t["accent"], t["ink"]
    dk = t.get("dark")
    if k == "dots":
        return "radial-gradient(%s 1px,transparent 1.5px) 0 0/16px 16px,%s" % (rgba(ink, 0.10), bg)
    if k == "grid":
        return ("linear-gradient(%s 1px,transparent 1px) 0 0/16px 16px,linear-gradient(90deg,%s 1px,transparent 1px) 0 0/16px 16px,%s"
                % (rgba(ink, 0.06), rgba(ink, 0.06), bg))
    if k == "dotgrid":   # fine dot grain + one hairline rule near the top (ledger look)
        return ("linear-gradient(%s,%s) 0 13%%/100%% 1px no-repeat,radial-gradient(%s 1px,transparent 1.5px) 0 0/16px 16px,linear-gradient(180deg,%s,%s)"
                % (rgba(ink, 0.14), rgba(ink, 0.14), rgba(ink, 0.07), bg, bg2))
    if k == "frame":     # one inset double hairline frame
        return ("linear-gradient(%s,%s) 50%% 50%%/calc(100%% - 16px) calc(100%% - 16px) no-repeat,linear-gradient(%s,%s) 50%% 50%%/calc(100%% - 14px) calc(100%% - 14px) no-repeat,"
                "linear-gradient(%s,%s) 50%% 50%%/calc(100%% - 8px) calc(100%% - 8px) no-repeat,linear-gradient(%s,%s) 50%% 50%%/calc(100%% - 6px) calc(100%% - 6px) no-repeat,%s"
                % (bg, bg, rgba(pr, 0.55), rgba(pr, 0.55), bg, bg, rgba(pr, 0.3), rgba(pr, 0.3), bg))
    if k == "paper":
        return ("repeating-linear-gradient(180deg,transparent 0 23px,%s 23px 24px),linear-gradient(90deg,transparent 31px,%s 31px 32px,transparent 32px),%s"
                % (rgba(ink, 0.08), rgba(ac, 0.3), bg))
    if k == "blocks":    # two flat colour blocks bleeding off opposite corners
        return ("radial-gradient(circle at 100%% 0%%,%s 0 22%%,transparent 22.3%%),linear-gradient(%s,%s) 0 100%%/26%% 18%% no-repeat,%s"
                % (rgba(ac, 0.9), pr, pr, bg))
    if k == "papercut":  # a row of paper-cut shapes on the top edge, on a grid
        return ("radial-gradient(circle at 12%% 0,%s 0 9%%,transparent 9.3%%),radial-gradient(circle at 36%% 0,%s 0 6%%,transparent 6.3%%),"
                "radial-gradient(circle at 64%% 0,%s 0 6%%,transparent 6.3%%),radial-gradient(circle at 88%% 0,%s 0 9%%,transparent 9.3%%),"
                "linear-gradient(%s,%s) 0 100%%/100%% 5%% no-repeat,%s" % (pr, ac, pr, ac, bg2, bg2, bg))
    if k == "panels":    # vertical tonal panels of a studio set + one marquee line
        return ("linear-gradient(%s,%s) 0 82%%/100%% 2px no-repeat,repeating-linear-gradient(90deg,%s 0 12.5%%,%s 12.5%% 25%%)" % (pr, pr, bg, bg2))
    if k == "planes":    # two matte planes at different depths
        return ("linear-gradient(155deg,transparent 0 58%%,%s 58%% 100%%),linear-gradient(155deg,transparent 0 76%%,%s 76%% 100%%),%s"
                % (bg2, mix(bg2, "#ffffff" if dk else "#000000", 0.05), bg))
    if k == "halftone":  # halftone corner + a flat ink band
        return "radial-gradient(circle at 100%% 0,transparent 0 34%%,%s 34.3%%),radial-gradient(%s 1.6px,transparent 2.2px) 0 0/10px 10px,%s" % (bg, rgba(ink, 0.22), bg)
    if k == "pixel":
        return ("conic-gradient(%s 25%%,transparent 0 50%%,%s 0 75%%,transparent 0) 0 0/16px 16px,linear-gradient(180deg,%s,%s)"
                % (rgba(pr, 0.06), rgba(pr, 0.06), bg, bg2))
    if k == "chalk":
        return ("repeating-linear-gradient(12deg,%s 0 1px,transparent 1px 8px),linear-gradient(180deg,%s,%s)" % (rgba("#ffffff", 0.025), bg, bg2))
    if k == "bands":     # three flat tonal bands along the bottom
        m1, m2, m3 = mix(bg, pr, 0.10), mix(bg, pr, 0.20), mix(bg, pr, 0.32)
        return "linear-gradient(180deg,%s 0 70%%,%s 70%% 80%%,%s 80%% 90%%,%s 90%% 100%%)" % (bg, m1, m2, m3)
    if k == "hills":     # two soft flat hills + a sun disc
        return ("radial-gradient(circle at 84%% 22%%,%s 0 7%%,transparent 7.3%%),radial-gradient(70%% 34%% at 22%% 108%%,%s 0 99%%,transparent 100%%),"
                "radial-gradient(80%% 30%% at 82%% 112%%,%s 0 99%%,transparent 100%%),linear-gradient(180deg,%s,%s)"
                % (rgba("#ffffff", 0.75), mix(bg2, ac, 0.35), mix(bg2, pr, 0.22), bg, bg2))
    return "linear-gradient(180deg,%s,%s)" % (bg, bg2)


# ---------------------------------------------------------------- icons -----------------------------------------------------------------
def _icons() -> dict:
    global _ICONS
    if _ICONS is None:
        try:
            _ICONS = json.loads((HERE / "icons.json").read_text(encoding="utf-8"))["icons"]
        except (OSError, ValueError, KeyError):
            _ICONS = {}
    return _ICONS


def icon_names() -> list[str]:
    return sorted(_icons())


def _color(c: str) -> str:
    if isinstance(c, str) and (c == "currentColor" or _HEX.fullmatch(c) or re.fullmatch(r"var\(--sk-[a-z0-9]+\)", c)):
        return c
    return "currentColor"


def icon(name: str, size: int = 24, color: str = "currentColor", stroke: float = 2.0, cls: str = "sk-i") -> str:
    """Inline SVG icon (no xmlns: HTML5 inline). Unknown names fall back to "sparkles"."""
    lib = _icons()
    body = lib.get(str(name)) or lib.get("sparkles", "")
    cls = re.sub(r"[^a-z0-9 _-]", "", str(cls).lower())
    return ('<svg class="%s" viewBox="0 0 24 24" width="%d" height="%d" fill="none" stroke="%s" stroke-width="%.3g" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">%s</svg>' % (cls, int(size), int(size), _color(color), float(stroke), body))


def icon_for(text: str, salt: str = "") -> str:
    s = str(text or "")
    for words, name in WORDS:
        if any(w in s for w in words) and name in _icons():
            return name
    h = int(hashlib.sha256((s + salt).encode("utf-8")).hexdigest()[:6], 16)
    return GENERIC[h % len(GENERIC)]


def spot(name: str, t: dict, size: int = 96, seed: str = "") -> str:
    """A spot illustration: the icon on one matte tonal tile (rounded square or circle, by style radius) with a hairline. Pure SVG, coloured by the tokens.
    (The old blob + ring + sparkles version was retired: generic decoration.)"""
    h = int(hashlib.sha256((str(name) + seed).encode("utf-8")).hexdigest()[:6], 16)
    pr, ink = t["primary"], t["ink"]
    dk = t.get("dark")
    body = _icons().get(str(name)) or _icons().get("sparkles", "")
    stroke_c = pr if not dk else mix(pr, "#ffffff", 0.15)
    if contrast(stroke_c, t["bg"]) < 3:
        stroke_c = ink
    rx = 60 if int(t.get("r", 12)) >= 20 else max(0, min(28, int(t.get("r", 12)) * 2))
    return ('<svg class="sk-spot" viewBox="0 0 120 120" width="%d" height="%d" aria-hidden="true">'
            '<rect x="6" y="6" width="108" height="108" rx="%d" fill="%s" stroke="%s" stroke-width="1.5"/>'
            '<g transform="translate(%d 30) scale(2.5)" fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">%s</g></svg>'
            % (int(size), int(size), rx, rgba(pr, 0.12 if dk else 0.08), rgba(pr, 0.30), 30, stroke_c, body))


def character(seed: str = "a", size: int = 72) -> str:
    """DiceBear thumbs face (CC0 1.0), inlined without its metadata/xmlns so the page stays address-free."""
    seed = seed if seed in ("a", "b", "c", "d") else "a"
    try:
        svg = (HERE / "characters" / ("thumbs-%s.svg" % seed)).read_text(encoding="utf-8")
    except OSError:
        return icon("mood-smile", size)
    svg = re.sub(r"<metadata\b.*?</metadata>", "", svg, flags=re.S)
    svg = re.sub(r'\s+xmlns(:\w+)?="[^"]*"', "", svg)
    return svg.replace("<svg", '<svg class="sk-char" width="%d" height="%d" aria-hidden="true"' % (int(size), int(size)), 1)


# ---------------------------------------------------------------- pieces ----------------------------------------------------------------
def badge(text: str, t: dict | None = None, kind: str = "soft") -> str:
    kind = kind if kind in ("soft", "solid", "outline") else "soft"
    return '<span class="sk-badge sk-badge-%s">%s</span>' % (kind, html.escape(str(text)))


def ornament(kind: str = "tape") -> str:
    """Card ornaments: rule (hairline), kicker (short accent rule), edge (accent bar), corner (tonal corner). Old names tape / pin / stars still work."""
    kind = kind if kind in ("rule", "kicker", "edge", "corner", "tape", "pin", "stars") else "rule"
    return '<span class="sk-orn sk-orn-%s" aria-hidden="true"></span>' % kind


def button(text: str, t: dict, primary: bool = True) -> str:
    return '<span class="sk-btn sk-btn-%s%s">%s</span>' % (t.get("btn", "pill"), "" if primary else " sk-btn-ghost", html.escape(str(text)))


def title(text: str, t: dict, cls: str = "") -> str:
    cls = re.sub(r"[^a-z0-9 _-]", "", cls)
    return '<div class="sk-h sk-fx-%s %s">%s</div>' % (t.get("fx", "plain"), cls, html.escape(str(text)))


def frame(kind: str, inner_html: str, t: dict | None = None, label: str = "", bg: str | None = None) -> str:
    """A device around a screen. inner_html is trusted markup built by the caller (escape text before passing it in)."""
    kind = kind if kind in KINDS else "tv"
    t = t or tokens()
    scr = 'class="sk-scr" style="%s;background:%s"' % (vars_style(t), bg or pattern(t))
    lab = '<figcaption class="sk-lab">%s</figcaption>' % html.escape(label) if label else ""
    extra = {"tv": '<i class="sk-stand"></i>', "board": '<i class="sk-tray"></i>', "laptop": '<i class="sk-base"></i>', "phone": "", "tablet": "", "a4": '<i class="sk-fold"></i>'}[kind]
    return '<figure class="sk-dev sk-%s"><div class="sk-body"><div %s>%s</div></div>%s%s</figure>' % (kind, scr, inner_html, extra, lab)


def css() -> str:
    """Stylesheet for frames, screens and pieces. Sizes inside a screen use cqw so a mock scales with its frame."""
    return (
        ".sk-dev{margin:0;position:relative;width:100%}.sk-body{position:relative}"
        ".sk-scr{position:relative;overflow:hidden;container-type:inline-size;color:var(--sk-ink);font-family:var(--sk-fb);line-height:1.3;word-break:keep-all}"
        ".sk-tv .sk-body,.sk-board .sk-body{background:#1a1c20;border-radius:10px;padding:2.2%;box-shadow:0 16px 28px -18px rgba(10,14,24,.55)}"
        ".sk-tv .sk-scr,.sk-board .sk-scr,.sk-laptop .sk-scr{aspect-ratio:16/9;border-radius:4px}"
        ".sk-stand{display:block;margin:0 auto;width:22%;height:10px;background:#1a1c20;clip-path:polygon(18% 0,82% 0,100% 100%,0 100%);border-radius:0 0 4px 4px}"
        ".sk-board .sk-body{padding:2.2% 2.2% 3.2%;background:#22252a}"
        ".sk-tray{display:block;margin:-2px 3% 0;height:9px;border-radius:0 0 6px 6px;background:#c3c8cf}"
        ""
        ".sk-laptop .sk-body{background:#1b1d22;border-radius:12px 12px 0 0;padding:2.4% 2.4% 3%;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}"
        ".sk-base{display:block;height:11px;margin:0 -6%;border-radius:0 0 12px 12px;background:#c3c8cf}"
        ".sk-base::before{content:'';display:block;width:16%;height:4px;margin:0 auto;border-radius:0 0 6px 6px;background:#8d949e}"
        ".sk-phone{width:46%;margin:0 auto}.sk-phone .sk-body{background:#16181d;border-radius:26px;padding:6px;box-shadow:0 14px 26px -10px rgba(10,14,24,.5),inset 0 0 0 2px #2c2f36}"
        ".sk-phone .sk-scr{aspect-ratio:9/19;border-radius:20px}.sk-phone .sk-scr::before{content:'';position:absolute;z-index:5;top:2.2%;left:50%;width:30%;height:2.4%;transform:translateX(-50%);border-radius:99px;background:#0c0d10}"
        ".sk-tablet{width:78%;margin:0 auto}.sk-tablet .sk-body{background:#1a1c21;border-radius:20px;padding:3.2%;box-shadow:0 14px 26px -10px rgba(10,14,24,.45),inset 0 0 0 2px #2c2f36}"
        ".sk-tablet .sk-scr{aspect-ratio:4/3;border-radius:8px}"
        ".sk-a4{width:62%;margin:0 auto}.sk-a4 .sk-scr{aspect-ratio:1/1.414;border-radius:2px;box-shadow:0 1px 0 rgba(0,0,0,.05),0 12px 24px -10px rgba(10,14,24,.35),0 0 0 1px rgba(0,0,0,.06)}"
        ".sk-fold{position:absolute;right:0;top:0;width:14%;aspect-ratio:1;background:linear-gradient(225deg,transparent 50%,rgba(0,0,0,.12) 50%,#fff 56%);}"
        ".sk-lab{margin-top:8px;text-align:center;font-size:13px;letter-spacing:.01em;opacity:.7}"
        ".sk-h{font-family:var(--sk-fd);font-weight:var(--sk-dw);letter-spacing:var(--sk-tr);line-height:1.14;color:var(--sk-ink);text-wrap:balance}"
        ".sk-fx-rule::before{content:'';display:block;width:1.6em;height:.09em;min-height:2px;margin-bottom:.4em;background:var(--sk-pt)}"
        ".sk-fx-serif::after{content:'';display:block;width:2em;height:1px;margin-top:.34em;background:var(--sk-pt)}"
        ".sk-fx-block{display:inline;background:var(--sk-pr);color:var(--sk-op);padding:.04em .22em;box-decoration-break:clone;-webkit-box-decoration-break:clone}"
        ".sk-fx-under{background:linear-gradient(transparent 68%,color-mix(in srgb,var(--sk-ac) 38%,transparent) 68%);display:inline;box-decoration-break:clone;-webkit-box-decoration-break:clone}"
        ".sk-fx-pixel{text-shadow:.07em .07em 0 color-mix(in srgb,var(--sk-ink) 28%,transparent)}"
        ".sk-fx-chalk{color:var(--sk-ink);opacity:.96}"
        # legacy names keep working, drawn the new way
        ".sk-fx-glow::before,.sk-fx-stack::before{content:'';display:block;width:1.6em;height:.09em;min-height:2px;margin-bottom:.4em;background:var(--sk-pt)}"
        ".sk-fx-stamp{display:inline;background:var(--sk-pr);color:var(--sk-op);padding:.04em .22em;box-decoration-break:clone;-webkit-box-decoration-break:clone}"
        ".sk-btn{display:inline-flex;align-items:center;justify-content:center;gap:.4em;font-weight:700;letter-spacing:-.012em;font-family:var(--sk-fb);background:var(--sk-pr);color:var(--sk-op);padding:.5em 1.2em;border-radius:999px;white-space:nowrap}"
        ".sk-btn-tile{border-radius:var(--sk-r)}.sk-btn-line,.sk-btn-neon{background:transparent;color:var(--sk-pt);border:1.5px solid currentColor;border-radius:var(--sk-r)}"
        ".sk-btn-stamp{border-radius:var(--sk-r);border:2px solid var(--sk-ink);box-shadow:.16em .16em 0 var(--sk-ink)}"
        ".sk-btn-soft,.sk-btn-glass{border-radius:var(--sk-r);box-shadow:0 .5em 1em -.6em rgba(0,0,0,.6)}"
        ".sk-btn-note{border-radius:3px;transform:rotate(-1.2deg)}"
        ".sk-btn-ghost{background:transparent;color:var(--sk-ink);box-shadow:none;border:1.5px solid color-mix(in srgb,var(--sk-ink) 30%,transparent)}"
        ".sk-badge{display:inline-flex;align-items:center;gap:.3em;font-size:12px;font-weight:600;letter-spacing:.01em;padding:.15em .65em;border-radius:999px;background:color-mix(in srgb,var(--sk-pr) 12%,transparent);color:var(--sk-ink);font-variant-numeric:tabular-nums}"
        ".sk-badge-solid{background:var(--sk-pr);color:var(--sk-op)}.sk-badge-outline{background:transparent;border:1px solid color-mix(in srgb,currentColor 45%,transparent)}"
        ".sk-orn{position:absolute;pointer-events:none;z-index:3}"
        # ornaments (shared/design/system.py ORNAMENTS): rule, kicker, edge, corner. tape / pin / stars are kept as names and drawn as these.
        ".sk-orn-rule,.sk-orn-tape{top:0;left:0;right:0;height:1px;background:color-mix(in srgb,var(--sk-ink) 14%,transparent)}"
        ".sk-orn-kicker,.sk-orn-pin{top:10px;left:12px;width:28px;height:2px;background:var(--sk-pt)}"
        ".sk-orn-edge{top:0;bottom:0;left:0;width:3px;background:var(--sk-pt)}"
        ".sk-orn-corner,.sk-orn-stars{right:0;top:0;width:20px;height:20px;background:linear-gradient(225deg,color-mix(in srgb,var(--sk-pr) 22%,transparent) 50%,transparent 50%)}"
        ".sk-i{display:inline-block;vertical-align:middle;flex:none}.sk-spot,.sk-char{display:block;flex:none}"
        + (_ds.polish_css("shell") if _ds else "")
    )


def embed_fonts(page_html: str) -> str:
    """Embed the Noto Sans/Serif KR subset the page uses (shared/fonts/embed.py). Untouched when fonttools is missing."""
    if not _FONTS:
        return page_html
    try:
        if str(_FONTS) not in sys.path:
            sys.path.insert(0, str(_FONTS))
        import embed as _embed
        fams = ["TS Sans" if "TS Sans" in page_html else "Noto Sans KR"] + (["Noto Serif KR"] if "--sk-fd:'Noto Serif KR'" in page_html or "font-family:'Noto Serif KR'" in page_html else [])
        out, _rep = _embed.embed(page_html, fams)  # the serif subset only when a serif headline is really used (it is the slow, big one)
        return out
    except Exception:
        return page_html


def page(title_text: str, body: str, extra_css: str = "", embed: bool = True, lang: str = "ko") -> str:
    doc = ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           "<title>%s</title><style>%s%s</style></head><body>%s</body></html>" % (html.escape(lang), html.escape(title_text), css(), extra_css, body))
    return embed_fonts(doc) if embed else doc


if __name__ == "__main__":  # quick look: python3 shell.py > kit.html
    rows = []
    for sid in (list(_styles.STYLES) if _styles else []) + ["studio-clean"]:
        t = tokens(sid if sid != "studio-clean" else None)
        inner = ('<div style="position:absolute;inset:0;display:flex;align-items:center;gap:6cqw;padding:6cqw">%s<div>%s<div style="margin-top:4cqw">%s</div></div></div>'
                 % (spot(icon_for(sid), t, 120), title(sid, t, "x").replace('class="sk-h', 'style="font-size:7cqw" class="sk-h'), button("시작", t)))
        rows.append('<div style="width:300px">%s</div>' % frame("tv", inner, t, sid))
    sys.stdout.write(page("shell kit", '<div style="display:flex;flex-wrap:wrap;gap:24px;padding:24px;background:#eef1f6">%s</div>' % "".join(rows), embed=False))
