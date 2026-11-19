#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""껍데기 키트 (shell kit): device frames, background patterns, icons, spot illustrations, badges and ornaments for previews and
mock screens, all driven by design tokens so they always match the chosen style. Stdlib only, offline, no <script>, no outside address.

    import shell
    t = shell.tokens("neon-cyber")                      # a style id from shared/design/styles.py, design tokens, or a flat palette
    t = shell.tokens("pastel-cute", user={"bg1": "#102a43", "primary": "#f0b429"})   # the user's own colours win
    shell.frame("tv", inner_html, t)                     # phone | tablet | tv | board | laptop | a4
    shell.pattern(t)                                     # CSS background for the style (dots, grid, paper, mesh, rays ...)
    shell.icon("bulb", 24)                               # inline SVG (Tabler, MIT); unknown names -> "sparkles"
    shell.icon_for("빛의 반사")                           # icon name chosen from the words
    shell.spot("bulb", t)                                # a small spot illustration (blob + ring + icon + sparkles)
    shell.character("a")                                 # DiceBear thumbs face (CC0)
    shell.badge("3분", t) / shell.ornament("tape")
    shell.css()                                          # the stylesheet every helper relies on (put once in <style>)
    shell.page(title, body_html, embed=True)             # a full offline page; Noto Sans/Serif KR subset embedded when fonttools exists

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

_HEX = re.compile(r"#[0-9a-fA-F]{6}")
_ICONS: dict | None = None
KINDS = ("phone", "tablet", "tv", "board", "laptop", "a4")
PATTERNS = ("none", "dots", "grid", "paper", "mesh", "diamond", "confetti", "rays", "halftone", "pixel", "chalk", "leaves", "sparkle", "neongrid")

# how each style is "dressed": radius, background pattern, title effect, button shape, serif headline, weight, letter-spacing
DRESS = {
    "neon-cyber": dict(r=12, pat="neongrid", fx="glow", btn="neon", serif=False, w=900, tr=-0.02),
    "gold-luxury": dict(r=4, pat="diamond", fx="serif", btn="line", serif=True, w=700, tr=0.0),
    "pop-colorful": dict(r=16, pat="dots", fx="stamp", btn="stamp", serif=False, w=900, tr=-0.03),
    "festival-party": dict(r=22, pat="confetti", fx="stamp", btn="pill", serif=False, w=900, tr=-0.02),
    "tv-gameshow": dict(r=10, pat="rays", fx="stack", btn="tile", serif=False, w=900, tr=-0.02),
    "glass-3d": dict(r=20, pat="mesh", fx="plain", btn="glass", serif=False, w=800, tr=-0.02),
    "anime-cartoon": dict(r=12, pat="halftone", fx="stamp", btn="stamp", serif=False, w=900, tr=-0.03),
    "pastel-cute": dict(r=24, pat="sparkle", fx="under", btn="pill", serif=False, w=800, tr=-0.02),
    "retro-pixel": dict(r=0, pat="pixel", fx="pixel", btn="tile", serif=False, w=900, tr=0.02),
    "minimal-premium": dict(r=3, pat="none", fx="serif", btn="line", serif=True, w=700, tr=-0.015),
    "chalk-paper": dict(r=10, pat="chalk", fx="chalk", btn="note", serif=False, w=700, tr=0.0),
    "nature-calm": dict(r=22, pat="leaves", fx="under", btn="pill", serif=False, w=800, tr=-0.02),
    "own-palette": dict(r=14, pat="dots", fx="plain", btn="pill", serif=False, w=800, tr=-0.02),
    "studio-clean": dict(r=14, pat="dots", fx="plain", btn="pill", serif=False, w=800, tr=-0.02),
}
# the harness default when nothing is chosen: cool paper, ink-blue, one warm accent, sans. Deliberately NOT cream + clay + serif.
DEFAULT_PAL = {"bg1": "#f3f6fb", "bg2": "#e4ebf7", "text": "#172033", "card": "#ffffff", "primary": "#2f5bea", "btnText": "#ffffff", "accent": "#ff8a3d",
               "good": "#1d7a4c", "bad": "#c4302b"}
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
    sid, pal, font, dark = "studio-clean", dict(DEFAULT_PAL), "Noto Sans KR", False
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
        "good": _hex(pal.get("good"), "#1d7a4c"), "bad": _hex(pal.get("bad"), "#c4302b"),
        "r": d["r"], "pattern": d["pat"], "fx": d["fx"], "btn": d["btn"], "w": d["w"], "tr": d["tr"],
    }
    t["pr_text"] = _legible(primary, bg, 3.0)
    return t


def font_stack(t: dict, display: bool = True) -> str:
    if display and t.get("serif"):
        return "'Noto Serif KR','Batang',serif"
    return "'Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo',sans-serif"


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
    """A CSS `background` value (gradients only, no images) for the style's pattern over its background colour."""
    k = kind or t.get("pattern", "dots")
    bg, bg2, pr, ac, ink = t["bg"], t["bg2"], t["primary"], t["accent"], t["ink"]
    dk = t.get("dark")
    soft = 0.10 if not dk else 0.16
    if k == "dots":
        return "radial-gradient(%s 1.2px,transparent 1.7px) 0 0/14px 14px,linear-gradient(160deg,%s,%s)" % (rgba(ink, 0.13), bg, bg2)
    if k == "grid":
        return ("linear-gradient(%s 1px,transparent 1px) 0 0/18px 18px,linear-gradient(90deg,%s 1px,transparent 1px) 0 0/18px 18px,%s"
                % (rgba(ink, 0.07), rgba(ink, 0.07), bg))
    if k == "neongrid":
        return ("linear-gradient(%s 1px,transparent 1px) 0 0/22px 22px,linear-gradient(90deg,%s 1px,transparent 1px) 0 0/22px 22px,"
                "radial-gradient(120%% 80%% at 50%% 110%%,%s,transparent 60%%),linear-gradient(180deg,%s,%s)"
                % (rgba(pr, 0.16), rgba(pr, 0.16), rgba(ac, 0.45), bg, bg2))
    if k == "paper":
        return ("repeating-linear-gradient(180deg,transparent 0 19px,%s 19px 20px),linear-gradient(90deg,transparent 30px,%s 30px 31px,transparent 31px),%s"
                % (rgba(pr, 0.14), rgba(ac, 0.35), bg))
    if k == "mesh":
        return ("radial-gradient(60%% 70%% at 12%% 18%%,%s,transparent 70%%),radial-gradient(55%% 60%% at 88%% 22%%,%s,transparent 70%%),"
                "radial-gradient(70%% 60%% at 60%% 100%%,%s,transparent 70%%),%s" % (rgba(pr, 0.55 if dk else 0.30), rgba(ac, 0.5 if dk else 0.28), rgba(bg2, 0.9), bg))
    if k == "diamond":
        return ("repeating-linear-gradient(45deg,%s 0 1px,transparent 1px 16px),repeating-linear-gradient(-45deg,%s 0 1px,transparent 1px 16px),"
                "radial-gradient(80%% 60%% at 50%% 0%%,%s,transparent 70%%),%s" % (rgba(pr, 0.16), rgba(pr, 0.16), rgba(pr, 0.22), bg))
    if k == "confetti":
        spots = [(12, 20, pr), (78, 14, ac), (30, 82, ac), (88, 70, pr), (55, 30, "#ffffff"), (8, 60, ac), (66, 88, pr)]
        lay = ",".join("radial-gradient(circle at %d%% %d%%,%s 0 3px,transparent 3.5px)" % (x, y, rgba(c, 0.8)) for x, y, c in spots)
        return lay + ",linear-gradient(160deg,%s,%s)" % (bg, bg2)
    if k == "rays":
        return ("repeating-conic-gradient(from 0deg at 50%% 110%%,%s 0 6deg,transparent 6deg 14deg),radial-gradient(90%% 70%% at 50%% 100%%,%s,transparent 70%%),"
                "linear-gradient(180deg,%s,%s)" % (rgba(pr, 0.10), rgba(pr, 0.35), bg, bg2))
    if k == "halftone":
        return ("radial-gradient(%s 2px,transparent 2.6px) 0 0/10px 10px,repeating-conic-gradient(from 0deg at 85%% 15%%,%s 0 4deg,transparent 4deg 12deg),"
                "linear-gradient(160deg,%s,%s)" % (rgba(ink, 0.10), rgba("#ffffff", 0.35), bg, bg2))
    if k == "pixel":
        return ("conic-gradient(%s 25%%,transparent 0 50%%,%s 0 75%%,transparent 0) 0 0/16px 16px,linear-gradient(180deg,%s,%s)"
                % (rgba(pr, 0.07), rgba(pr, 0.07), bg, bg2))
    if k == "chalk":
        return ("radial-gradient(40%% 30%% at 20%% 30%%,%s,transparent 70%%),radial-gradient(35%% 25%% at 75%% 70%%,%s,transparent 70%%),"
                "repeating-linear-gradient(12deg,%s 0 1px,transparent 1px 7px),%s" % (rgba("#ffffff", 0.07), rgba("#ffffff", 0.06), rgba("#ffffff", 0.02), bg))
    if k == "leaves":
        return ("radial-gradient(70%% 50%% at 0%% 100%%,%s,transparent 70%%),radial-gradient(50%% 40%% at 100%% 0%%,%s,transparent 70%%),"
                "radial-gradient(%s 1.2px,transparent 1.7px) 0 0/16px 16px,%s" % (rgba(pr, 0.28), rgba(ac, 0.30), rgba(pr, 0.18), bg))
    if k == "sparkle":
        return ("radial-gradient(circle at 15%% 20%%,%s 0 2px,transparent 2.5px),radial-gradient(circle at 80%% 30%%,%s 0 2.5px,transparent 3px),"
                "radial-gradient(circle at 70%% 80%%,%s 0 2px,transparent 2.5px),radial-gradient(60%% 50%% at 90%% 100%%,%s,transparent 70%%),linear-gradient(170deg,%s,%s)"
                % (rgba(pr, 0.45), rgba(ac, 0.55), rgba(pr, 0.4), rgba(ac, 0.25), bg, bg2))
    return "radial-gradient(120%% 90%% at 50%% 0%%,%s,transparent 70%%),%s" % (rgba("#ffffff" if not dk else pr, soft), bg)


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
    """A spot illustration: soft blob + accent ring + sparkles + the icon. Pure SVG, coloured by the tokens."""
    h = int(hashlib.sha256((str(name) + seed).encode("utf-8")).hexdigest()[:6], 16)
    blobs = ["M60 8c22 0 46 14 50 38s-6 52-30 60-56 2-68-20S30 8 60 8z", "M58 10c26-4 50 18 50 44s-18 52-48 54S10 92 10 62 32 14 58 10z",
             "M64 9c24 4 44 26 42 50s-26 48-52 47S12 84 12 58 40 5 64 9z"]
    pr, ac, ink = t["primary"], t["accent"], t["ink"]
    dk = t.get("dark")
    fill = rgba(pr, 0.22 if dk else 0.16)
    ring = rgba(ac, 0.9)
    sw = 1.7
    body = _icons().get(str(name)) or _icons().get("sparkles", "")
    stroke_c = pr if not dk else mix(pr, "#ffffff", 0.15)
    if contrast(stroke_c, t["bg"]) < 3:
        stroke_c = ink
    return ('<svg class="sk-spot" viewBox="0 0 120 120" width="%d" height="%d" aria-hidden="true">'
            '<path d="%s" fill="%s"/>'
            '<circle cx="%d" cy="%d" r="9" fill="none" stroke="%s" stroke-width="3"/>'
            '<path d="M%d %dl2.2 5.8 5.8 2.2-5.8 2.2-2.2 5.8-2.2-5.8-5.8-2.2 5.8-2.2z" fill="%s"/>'
            '<circle cx="%d" cy="%d" r="3.4" fill="%s"/>'
            '<g transform="translate(30 30) scale(2.5)" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" stroke-linejoin="round">%s</g></svg>'
            % (int(size), int(size), blobs[h % 3], fill, 96 - h % 9, 22 + h % 7, ring, 14 + h % 6, 84 - h % 8, ac, 22 + h % 11, 24 + h % 5, rgba(pr, 0.7),
               stroke_c, sw, body))


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
    """Card ornaments: tape (washi strip), pin, corner (folded), stars."""
    kind = kind if kind in ("tape", "pin", "corner", "stars") else "tape"
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
        ".sk-tv .sk-body,.sk-board .sk-body{background:linear-gradient(180deg,#23262d,#14161a);border-radius:12px;padding:2.4%;box-shadow:0 14px 28px -10px rgba(10,14,24,.45),inset 0 0 0 1px rgba(255,255,255,.07)}"
        ".sk-tv .sk-scr,.sk-board .sk-scr,.sk-laptop .sk-scr{aspect-ratio:16/9;border-radius:4px}"
        ".sk-stand{display:block;margin:0 auto;width:22%;height:10px;background:linear-gradient(180deg,#2a2d34,#14161a);clip-path:polygon(18% 0,82% 0,100% 100%,0 100%);border-radius:0 0 4px 4px}"
        ".sk-board .sk-body{padding:2.2% 2.2% 3.2%;background:linear-gradient(180deg,#2c3038,#1a1d22)}"
        ".sk-tray{display:block;margin:-2px 3% 0;height:9px;border-radius:0 0 6px 6px;background:linear-gradient(180deg,#d9dde3,#9aa2ad);box-shadow:0 6px 12px -6px rgba(0,0,0,.4)}"
        ".sk-tray::after{content:'';display:block;width:14%;height:4px;margin:2px 0 0 70%;border-radius:3px;background:#e2483d}"
        ".sk-laptop .sk-body{background:#1b1d22;border-radius:12px 12px 0 0;padding:2.4% 2.4% 3%;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}"
        ".sk-base{display:block;height:11px;margin:0 -6%;border-radius:0 0 12px 12px;background:linear-gradient(180deg,#d7dbe1,#a3aab4);box-shadow:0 10px 16px -8px rgba(0,0,0,.35)}"
        ".sk-base::before{content:'';display:block;width:16%;height:4px;margin:0 auto;border-radius:0 0 6px 6px;background:#8d949e}"
        ".sk-phone{width:46%;margin:0 auto}.sk-phone .sk-body{background:#16181d;border-radius:26px;padding:6px;box-shadow:0 14px 26px -10px rgba(10,14,24,.5),inset 0 0 0 2px #2c2f36}"
        ".sk-phone .sk-scr{aspect-ratio:9/19;border-radius:20px}.sk-phone .sk-scr::before{content:'';position:absolute;z-index:5;top:2.2%;left:50%;width:30%;height:2.4%;transform:translateX(-50%);border-radius:99px;background:#0c0d10}"
        ".sk-tablet{width:78%;margin:0 auto}.sk-tablet .sk-body{background:#1a1c21;border-radius:20px;padding:3.2%;box-shadow:0 14px 26px -10px rgba(10,14,24,.45),inset 0 0 0 2px #2c2f36}"
        ".sk-tablet .sk-scr{aspect-ratio:4/3;border-radius:8px}"
        ".sk-a4{width:62%;margin:0 auto}.sk-a4 .sk-scr{aspect-ratio:1/1.414;border-radius:2px;box-shadow:0 1px 0 rgba(0,0,0,.05),0 12px 24px -10px rgba(10,14,24,.35),0 0 0 1px rgba(0,0,0,.06)}"
        ".sk-fold{position:absolute;right:0;top:0;width:14%;aspect-ratio:1;background:linear-gradient(225deg,transparent 50%,rgba(0,0,0,.12) 50%,#fff 56%);}"
        ".sk-lab{margin-top:8px;text-align:center;font-size:13px;opacity:.75}"
        ".sk-h{font-family:var(--sk-fd);font-weight:var(--sk-dw);letter-spacing:var(--sk-tr);line-height:1.12;color:var(--sk-ink)}"
        ".sk-fx-glow{color:#fff;text-shadow:0 0 .35em var(--sk-pr),0 0 .9em var(--sk-pr)}"
        ".sk-fx-stamp{color:var(--sk-ink);text-shadow:.06em .06em 0 var(--sk-ac)}"
        ".sk-fx-stack{color:#fff;text-shadow:0 .05em 0 var(--sk-pr),0 .1em 0 rgba(0,0,0,.35)}"
        ".sk-fx-serif{font-weight:700}.sk-fx-serif::after{content:'';display:block;width:2.2em;height:2px;margin-top:.28em;background:var(--sk-ac)}"
        ".sk-fx-under{background:linear-gradient(transparent 62%,color-mix(in srgb,var(--sk-ac) 45%,transparent) 62%);display:inline;box-decoration-break:clone;-webkit-box-decoration-break:clone}"
        ".sk-fx-pixel{text-shadow:.06em 0 0 var(--sk-ac),-.06em 0 0 var(--sk-pr)}"
        ".sk-fx-chalk{color:var(--sk-ink);text-shadow:0 0 1px rgba(255,255,255,.6);opacity:.95}"
        ".sk-btn{display:inline-flex;align-items:center;justify-content:center;gap:.4em;font-weight:800;font-family:var(--sk-fb);background:var(--sk-pr);color:var(--sk-op);padding:.5em 1.2em;border-radius:999px;white-space:nowrap;box-shadow:0 .25em .6em -.2em color-mix(in srgb,var(--sk-pr) 60%,transparent)}"
        ".sk-btn-tile{border-radius:var(--sk-r)}.sk-btn-line{background:transparent;color:var(--sk-pt);border:1.5px solid currentColor;border-radius:var(--sk-r);box-shadow:none}"
        ".sk-btn-neon{background:transparent;color:var(--sk-pr);border:2px solid var(--sk-pr);border-radius:var(--sk-r);box-shadow:0 0 .6em var(--sk-pr),inset 0 0 .5em color-mix(in srgb,var(--sk-pr) 40%,transparent);text-shadow:0 0 .4em var(--sk-pr)}"
        ".sk-btn-stamp{border-radius:var(--sk-r);border:2px solid var(--sk-ink);box-shadow:.18em .18em 0 var(--sk-ink)}"
        ".sk-btn-glass{background:color-mix(in srgb,#fff 18%,transparent);color:var(--sk-ink);border:1px solid color-mix(in srgb,#fff 40%,transparent);backdrop-filter:blur(6px)}"
        ".sk-btn-note{border-radius:3px;transform:rotate(-1.5deg);box-shadow:.12em .2em 0 rgba(0,0,0,.25)}"
        ".sk-btn-ghost{background:transparent;color:var(--sk-ink);box-shadow:none;border:1.5px solid color-mix(in srgb,var(--sk-ink) 35%,transparent)}"
        ".sk-badge{display:inline-flex;align-items:center;gap:.3em;font-size:12px;font-weight:700;padding:.15em .65em;border-radius:999px;background:color-mix(in srgb,var(--sk-pr) 14%,transparent);color:var(--sk-ink)}"
        ".sk-badge-solid{background:var(--sk-pr);color:var(--sk-op)}.sk-badge-outline{background:transparent;border:1px solid currentColor}"
        ".sk-orn{position:absolute;pointer-events:none;z-index:3}"
        ".sk-orn-tape{top:-9px;left:50%;width:64px;height:18px;transform:translateX(-50%) rotate(-3deg);background:repeating-linear-gradient(45deg,rgba(255,255,255,.55) 0 6px,rgba(255,255,255,.25) 6px 12px),var(--sk-ac,#ffd166);opacity:.85;border-radius:2px;box-shadow:0 2px 4px rgba(0,0,0,.12)}"
        ".sk-orn-pin{top:-7px;left:50%;width:14px;height:14px;margin-left:-7px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#fff8,transparent 40%),var(--sk-ac,#e2483d);box-shadow:0 3px 5px rgba(0,0,0,.3)}"
        ".sk-orn-corner{right:0;top:0;width:22px;height:22px;background:linear-gradient(225deg,transparent 50%,rgba(0,0,0,.14) 50%)}"
        ".sk-orn-stars{right:10px;top:8px;width:30px;height:20px;background:radial-gradient(circle at 20% 60%,var(--sk-ac,#ffd166) 0 2.5px,transparent 3px),radial-gradient(circle at 70% 30%,var(--sk-ac,#ffd166) 0 3.5px,transparent 4px),radial-gradient(circle at 90% 85%,var(--sk-ac,#ffd166) 0 2px,transparent 2.5px)}"
        ".sk-i{display:inline-block;vertical-align:middle;flex:none}.sk-spot,.sk-char{display:block;flex:none}"
    )


def embed_fonts(page_html: str) -> str:
    """Embed the Noto Sans/Serif KR subset the page uses (shared/fonts/embed.py). Untouched when fonttools is missing."""
    if not _FONTS:
        return page_html
    try:
        if str(_FONTS) not in sys.path:
            sys.path.insert(0, str(_FONTS))
        import embed as _embed
        fams = ["Noto Sans KR"] + (["Noto Serif KR"] if "--sk-fd:'Noto Serif KR'" in page_html or "font-family:'Noto Serif KR'" in page_html else [])
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
