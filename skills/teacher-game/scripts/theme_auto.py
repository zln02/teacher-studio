#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Auto theme: turn mood words ("우주", "동화", "바다", "긴장감", "따뜻하게", "고급스럽게" ...) into a designed look.

Deterministic (same words + seed -> same result, no AI). It composes, from the shared asset arsenal (shared/assets):
  background generator (aurora / waves / hills / city / bokeh / blobs / mesh / sunburst / pitch / geometric) + pattern overlay,
  a host character (DiceBear CC0 style, wrapped as a 300x440 host with 4 moods), floating props (Tabler icons, MIT),
  a title font, a palette (contrast-checked by build.py), a celebration effect and the music mood.
The runtime that draws it is assets/themes/auto.js (reads SPEC.autoTheme).

Usage:  python3 theme_auto.py --words "우주 동화" --title "..." [--subject 과학] [--seed 1]   -> prints the composed JSON
In a spec: "design": {"theme": "auto", "mood": "긴장감", "words": ["우주"], "seed": 2}   (build.py calls compose()).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "shared" / "assets"
if not ASSETS.exists():  # running from the repo root copy
    ASSETS = HERE.parent.parent.parent / "shared" / "assets"

# recipe id -> look. kw = words that pick it; bg/pattern = background generators (auto.js); props = Tabler icon names
RECIPES: dict[str, dict] = {
    "space": {"kw": ["우주", "별", "행성", "로켓", "은하", "천문", "태양계", "지구", "달", "외계", "과학 탐험"], "bg": "aurora", "pattern": "stars",
              "props": ["planet", "rocket", "satellite", "ufo", "stars", "alien", "telescope", "moon"], "chars": ["thumbs", "shapes", "pixel-art"],
              "cel": "stars", "font": "Black Han Sans", "music": "space", "motion": "high", "base": "space",
              "pal": {"bg1": "#070b24", "bg2": "#1d1655", "text": "#ffffff", "card": "#17204f", "cardText": "#ffffff", "cardBorder": "#8fa8ff",
                      "primary": "#ffd23f", "btnText": "#1a1a1a", "accent": "#5ce1ff", "good": "#43e8a0", "bad": "#ff6b7a"},
              "lines": {"title": ["우주 탐험 출발!"], "start": ["발사 준비 완료!"], "correct": ["별처럼 반짝!", "굿 샷!"], "wrong": ["궤도 수정!", "다시 도전!"], "win": ["임무 성공!"], "lose": ["다음엔 꼭!"]}},
    "sea": {"kw": ["바다", "물고기", "해양", "파도", "섬", "배", "항해", "수족관", "해변", "동물"], "bg": "waves", "pattern": "dots",
            "props": ["fish", "ship", "sun", "cloud", "butterfly", "umbrella", "flag-3", "stars"], "chars": ["thumbs", "lorelei", "shapes"],
            "cel": "bubbles", "font": "Jua", "music": "nature", "motion": "normal", "base": "ocean",
            "pal": {"bg1": "#0b5a96", "bg2": "#0a3d73", "text": "#ffffff", "card": "#ffffff", "cardText": "#0b2a4a", "cardBorder": "#5cc8ff",
                    "primary": "#ffd23f", "btnText": "#1a1a1a", "accent": "#5cf0e0", "good": "#0f7d45", "bad": "#c62828"},
            "lines": {"title": ["바다로 출발!"], "start": ["물결 따라 가요!"], "correct": ["첨벙! 정답!", "바다 최고!"], "wrong": ["파도에 휩쓸렸어요", "다시 헤엄쳐요"], "win": ["보물섬 도착!"], "lose": ["다음엔 꼭!"]}},
    "fairy": {"kw": ["동화", "공주", "마법", "요정", "왕자", "성", "상상", "그림책", "판타지", "귀여", "유치원"], "bg": "hills", "pattern": "sparkle",
              "props": ["crown", "building-castle", "stars", "feather", "butterfly", "flower", "rainbow", "sparkles"], "chars": ["lorelei", "thumbs"],
              "cel": "petals", "font": "Jua", "music": "cute", "motion": "normal", "base": "fairytale",
              "pal": {"bg1": "#ffe3f1", "bg2": "#cfe9ff", "text": "#3a1f4a", "card": "#ffffff", "cardText": "#3a1f4a", "cardBorder": "#ff8fc7",
                      "primary": "#c2307f", "btnText": "#ffffff", "accent": "#8a6bff", "good": "#1a7f56", "bad": "#c4254f"},
              "lines": {"title": ["옛날 옛적에..."], "start": ["이야기 시작!"], "correct": ["반짝! 마법 성공!", "멋져요!"], "wrong": ["앗, 마법이 틀렸어요", "다시 해 봐요"], "win": ["행복한 결말!"], "lose": ["다시 읽어 볼까요?"]}},
    "tense": {"kw": ["긴장", "방탈출", "미스터리", "탐정", "추리", "스릴", "탈출", "비밀", "사건", "어둠", "밤"], "bg": "city", "pattern": "grid",
              "props": ["key", "lock", "clock", "hourglass", "ghost", "alarm", "eye", "shield"], "chars": ["pixel-art", "shapes", "thumbs"],
              "cel": "sparks", "font": "Black Han Sans", "music": "tension", "motion": "high", "base": "arcade",
              "pal": {"bg1": "#0b0f14", "bg2": "#1a2330", "text": "#f2f5f8", "card": "#141c26", "cardText": "#f2f5f8", "cardBorder": "#ff5a66",
                      "primary": "#ff5a66", "btnText": "#14080a", "accent": "#ffb020", "good": "#3ee6a0", "bad": "#ff7a7a"},
              "lines": {"title": ["시간이 없어요..."], "start": ["지금부터 시작!"], "correct": ["단서 발견!", "한 걸음 더!"], "wrong": ["경보가 울려요!", "침착하게!"], "win": ["탈출 성공!"], "lose": ["시간 초과..."]}},
    "luxe": {"kw": ["고급", "송년", "연말", "파티", "시상", "품격", "럭셔리", "회식", "워크숍", "행사", "축하", "우아"], "bg": "bokeh", "pattern": "diamond",
             "props": ["trophy", "crown", "gift", "cake", "balloon", "sparkles", "medal", "confetti"], "chars": ["lorelei", "thumbs"],
             "cel": "gold", "font": "Noto Serif KR", "music": "upbeat", "motion": "normal", "base": "gameshow",
             "pal": {"bg1": "#14110f", "bg2": "#2b2118", "text": "#fff4d6", "card": "#1f1a14", "cardText": "#fff4d6", "cardBorder": "#e0b44c",
                     "primary": "#e0b44c", "btnText": "#1a1206", "accent": "#f4e3b2", "good": "#5be0a0", "bad": "#ff8a8a"},
             "lines": {"title": ["오늘 밤의 주인공은?"], "start": ["건배하듯 시작!"], "correct": ["훌륭해요!", "브라보!"], "wrong": ["아쉬워요", "다음 문제에서!"], "win": ["우승을 축하해요!"], "lose": ["멋진 도전이었어요"]}},
    "warm": {"kw": ["따뜻", "가족", "포근", "다정", "엄마", "아빠", "할머니", "할아버지", "집", "명절", "감사", "사랑"], "bg": "sunburst", "pattern": "dots",
             "props": ["heart", "sun", "home", "cake", "coffee", "gift", "flower", "stars"], "chars": ["lorelei", "thumbs"],
             "cel": "hearts", "font": "Jua", "music": "cute", "motion": "calm", "base": "fairytale",
             "pal": {"bg1": "#fff1dc", "bg2": "#ffd9b0", "text": "#4a2a14", "card": "#fffaf2", "cardText": "#4a2a14", "cardBorder": "#e8a24a",
                     "primary": "#b85d1c", "btnText": "#ffffff", "accent": "#b4553a", "good": "#1f7a4d", "bad": "#b3261e"},
             "lines": {"title": ["같이 즐겨요!"], "start": ["시작해 볼까요?"], "correct": ["우와, 맞았어요!", "최고예요!"], "wrong": ["괜찮아요~", "한 번 더!"], "win": ["모두 수고했어요!"], "lose": ["다음에 또 해요"]}},
    "forest": {"kw": ["숲", "자연", "식물", "나무", "생태", "환경", "곤충", "꽃", "계절", "봄", "가을", "정원"], "bg": "hills", "pattern": "leaves",
               "props": ["leaf", "tree", "trees", "flower", "butterfly", "bug", "sun", "paw"], "chars": ["thumbs", "lorelei"],
               "cel": "petals", "font": "Jua", "music": "nature", "motion": "calm", "base": "forest",
               "pal": {"bg1": "#dff5e1", "bg2": "#b6e3c0", "text": "#1d3a26", "card": "#ffffff", "cardText": "#1d3a26", "cardBorder": "#4caf6a",
                       "primary": "#237a43", "btnText": "#ffffff", "accent": "#f2b134", "good": "#1a7a43", "bad": "#b8322d"},
               "lines": {"title": ["숲으로 떠나요!"], "start": ["살금살금 시작!"], "correct": ["싱그러워요!", "쑥쑥 자라요!"], "wrong": ["다시 살펴봐요", "천천히!"], "win": ["숲이 활짝 폈어요!"], "lose": ["다음엔 꼭!"]}},
    "hanok": {"kw": ["역사", "조선", "전통", "한옥", "고려", "삼국", "한복", "궁", "왕", "옛날", "국악", "한글"], "bg": "ink", "pattern": "waves",
              "props": ["flag", "sword", "map", "book", "compass", "pennant", "building-castle", "mountain"], "chars": ["shapes", "thumbs"],
              "cel": "petals", "font": "Song Myung", "music": "korean", "motion": "normal", "base": "hanok",
              "pal": {"bg1": "#f4ead5", "bg2": "#e0cfaa", "text": "#2b1d12", "card": "#fffaf0", "cardText": "#2b1d12", "cardBorder": "#8b5a2b",
                      "primary": "#a83232", "btnText": "#ffffff", "accent": "#2f5d8a", "good": "#1f7a43", "bad": "#b3261e"},
              "lines": {"title": ["옛이야기 속으로!"], "start": ["북을 울려라!"], "correct": ["훌륭하오!", "맞았소!"], "wrong": ["아쉽소!", "다시 생각해 보오"], "win": ["대승이오!"], "lose": ["후일을 기약하오"]}},
    "sports": {"kw": ["스포츠", "운동", "체육", "축구", "달리기", "올림픽", "대결", "시합", "운동회", "응원"], "bg": "pitch", "pattern": "stripes",
               "props": ["trophy", "medal", "flag", "target", "bike", "stopwatch", "award", "bolt"], "chars": ["thumbs", "shapes"],
               "cel": "confetti", "font": "Black Han Sans", "music": "sports", "motion": "high", "base": "sports",
               "pal": {"bg1": "#0f5132", "bg2": "#1b7a4a", "text": "#ffffff", "card": "#ffffff", "cardText": "#11331f", "cardBorder": "#ffd23f",
                       "primary": "#ffd23f", "btnText": "#1a1a1a", "accent": "#ff6b35", "good": "#0e7a3c", "bad": "#c62828"},
               "lines": {"title": ["경기 시작!"], "start": ["준비, 땅!"], "correct": ["굿 플레이!", "골인!"], "wrong": ["아깝다!", "다시 한 번!"], "win": ["우승!"], "lose": ["다음 경기엔!"]}},
    "science": {"kw": ["과학", "실험", "화학", "물리", "수학", "탐구", "연구", "기술", "코딩", "로봇", "AI"], "bg": "geometric", "pattern": "grid",
                "props": ["atom", "flask", "microscope", "bulb", "calculator", "dna", "magnet", "robot"], "chars": ["shapes", "pixel-art", "thumbs"],
                "cel": "sparks", "font": "Do Hyeon", "music": "mystery", "motion": "normal", "base": "space",
                "pal": {"bg1": "#06202b", "bg2": "#0d3b4f", "text": "#ffffff", "card": "#0f2f3f", "cardText": "#ffffff", "cardBorder": "#4ee3d1",
                        "primary": "#4ee3d1", "btnText": "#031a1a", "accent": "#ffcf4a", "good": "#4cf0a0", "bad": "#ff7a7a"},
                "lines": {"title": ["실험 시작!"], "start": ["가설을 세워요!"], "correct": ["가설 증명!", "대단해요!"], "wrong": ["다시 관찰해요", "오차 발생!"], "win": ["실험 성공!"], "lose": ["다시 실험해요"]}},
}
DEFAULT = {"bg": "mesh", "pattern": "dots", "props": ["star", "bulb", "puzzle", "rocket", "trophy", "sparkles", "flag", "heart"], "chars": ["thumbs", "shapes"],
           "cel": "confetti", "font": None, "music": None, "motion": None, "base": None, "pal": None,
           "lines": {"title": ["준비됐나요?"], "start": ["시작해요!"], "correct": ["정답!", "잘했어요!"], "wrong": ["아쉬워요", "다시 한 번!"], "win": ["모두 수고했어요!"], "lose": ["다음엔 꼭!"]}}
# subject -> recipe when no mood word hits
SUBJECT_HINT = {"과학": "science", "수학": "science", "사회": "forest", "역사": "hanok", "영어": "fairy", "국어": "warm", "도덕": "warm", "체육": "sports", "미술": "fairy", "음악": "luxe", "가족": "warm"}
MOOD_HINT = {"긴장감": "tense", "신남": "sports", "따뜻함": "warm", "차분": "forest", "고급스러움": "luxe", "밝음": "fairy"}


# --- parts library: every ported theme (assets/themes/<id>.js) is also a source of reusable parts -------------------------------
# host characters (each ported theme brings one), staging (deco + reactions + sfx), scene backgrounds. The auto theme mixes
# these with generated backgrounds, DiceBear characters, Tabler props and celebration effects for any mood.
HOST_PARTS = {"tv-studio": "미스터 Q (정장 진행자)", "auditorium-bell": "강당 선생님 진행자", "space-station": "로봇 코비", "joseon-war-room": "조선 수군 장교",
              "antidote-lab": "연구원", "sun-temple": "탐험가", "recycle-robot": "재활용 로봇", "post-office-night": "고양이 집배원", "cell-feeding": "세포 몽글이"}
STAGE_PARTS = {"tv-studio": "ON AIR · APPLAUSE 간판 + 박수 소리"}
RECIPE_HOSTS = {"space": ["space-station", "dice", "tv-studio"], "sea": ["dice", "post-office-night", "cell-feeding"], "fairy": ["dice", "post-office-night", "cell-feeding"],
                "tense": ["antidote-lab", "sun-temple", "dice"], "luxe": ["tv-studio", "auditorium-bell", "dice"], "warm": ["auditorium-bell", "post-office-night", "dice"],
                "forest": ["recycle-robot", "sun-temple", "dice"], "hanok": ["joseon-war-room", "auditorium-bell", "dice"], "sports": ["tv-studio", "dice", "recycle-robot"],
                "science": ["antidote-lab", "recycle-robot", "space-station"]}
RECIPE_STAGE = {"luxe": "tv-studio", "sports": "tv-studio"}
# a request that clearly names one ported world uses that whole theme as is (word -> theme id)
NAMED = {"tv-studio": ["방송국", "생방송", "퀴즈쇼", "스튜디오"], "auditorium-bell": ["강당", "종 울리", "종을 울"], "space-station": ["우주 정거장", "우주선", "우주 기지"],
         "joseon-war-room": ["거북선", "임진왜란", "이순신", "수군"], "antidote-lab": ["해독제", "연구소", "바이러스"], "sun-temple": ["사원", "유적", "이집트", "잉카", "마야"],
         "post-office-night": ["우체국", "편지 배달", "우편"], "cell-feeding": ["세포"], "recycle-robot": ["분리배출", "재활용", "분리수거"]}
HOST_BY_WORD = {"역사": "joseon-war-room", "조선": "joseon-war-room", "실험": "antidote-lab", "우주": "space-station", "재활용": "recycle-robot", "세포": "cell-feeding",
                "편지": "post-office-night", "방송": "tv-studio", "고대": "sun-temple", "송년": "tv-studio", "시상": "tv-studio"}


def named_theme(text: str) -> str:
    for tid, words in NAMED.items():
        if any(w in text for w in words):
            return tid
    return ""


def _h(key: str) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)


def pick_recipe(text: str, subject: str, mood: str) -> tuple[str, list[str]]:
    """Score recipes by keyword hits in the request words; fall back to mood, then subject, then the generic look."""
    scores = []
    for rid, r in RECIPES.items():
        hits = [k for k in r["kw"] if k in text]
        if hits:
            scores.append((-len(hits), list(RECIPES).index(rid), rid, hits))
    if scores:
        scores.sort()
        return scores[0][2], scores[0][3]
    for k, rid in MOOD_HINT.items():
        if k[:2] in mood:
            return rid, [k]
    if subject in SUBJECT_HINT:
        return SUBJECT_HINT[subject], [subject]
    return "", []


def _svg_inner(svg: str) -> tuple[str, str]:
    """(viewBox, inner markup) of a DiceBear SVG without its metadata block."""
    svg = re.sub(r"<metadata.*?</metadata>", "", svg, flags=re.S)
    m = re.match(r"\s*<svg[^>]*viewBox=\"([^\"]+)\"[^>]*>(.*)</svg>\s*$", svg, re.S)
    if not m:
        raise ValueError("unexpected avatar svg")
    return m.group(1), m.group(2)


def _avatar_def(sid: str, svg: str) -> tuple[str, str]:
    vb, inner = _svg_inner(svg)
    # ids inside the avatar must stay unique per avatar
    inner = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{sid}-{m.group(1)}"', inner)
    inner = re.sub(r'url\(#([^)]+)\)', lambda m: f"url(#{sid}-{m.group(1)})", inner)
    inner = re.sub(r'(xlink:)?href="#([^"]+)"', lambda m: f'href="#{sid}-{m.group(2)}"', inner)
    return vb, inner


def host_svg(style: str, letter: str, accent: str, ink: str) -> str:
    """A 300x440 host (4 moods) around a DiceBear avatar: torso in the accent colour, shadow, mood decorations."""
    base = ASSETS / "characters" / "dicebear"
    idle = (base / style / f"{letter}.svg").read_text(encoding="utf-8")
    defs, uses = "", {}
    variants = {"idle": idle, "happy": idle, "sad": idle}
    if style == "lorelei" and letter in "abcdef":
        variants["happy"] = (base / "lorelei-mood" / f"happy-{letter}.svg").read_text(encoding="utf-8")
        variants["sad"] = (base / "lorelei-mood" / f"sad-{letter}.svg").read_text(encoding="utf-8")
    seen: dict[str, str] = {}
    for k, svg in variants.items():
        if svg in seen:
            uses[k] = seen[svg]
            continue
        sid = f"av{k}"
        vb, inner = _avatar_def(sid, svg)
        defs += f'<symbol id="{sid}" viewBox="{vb}">{inner}</symbol>'
        seen[svg] = sid
        uses[k] = sid
    body = (f'<ellipse cx="150" cy="430" rx="96" ry="11" fill="rgba(0,0,0,.3)"/>'
            f'<path d="M62 436 Q62 300 150 292 Q238 300 238 436 Z" fill="{accent}" stroke="{ink}" stroke-width="7" stroke-linejoin="round"/>'
            f'<path d="M122 296 L150 340 L178 296" fill="#fff" stroke="{ink}" stroke-width="5" stroke-linejoin="round"/>')

    def face(k: str, extra: str = "", tf: str = "") -> str:
        return f'<g transform="{tf}"><use href="#{uses[k]}" x="30" y="40" width="240" height="260"/></g>{extra}'
    happy_x = ('<path d="M246 74 l8 -18 l8 18 l18 8 l-18 8 l-8 18 l-8 -18 l-18 -8z" fill="#ffd23f" stroke="' + ink + '" stroke-width="3"/>'
               '<path d="M40 96 l5 -12 l5 12 l12 5 l-12 5 l-5 12 l-5 -12 l-12 -5z" fill="#fff6b0" stroke="' + ink + '" stroke-width="3"/>')
    sad_x = '<path d="M96 196 q-9 18 0 26 q9 -8 0 -26z" fill="#7cc8ff" stroke="' + ink + '" stroke-width="3"/>'
    wow_x = ('<circle cx="262" cy="70" r="26" fill="#fff" stroke="' + ink + '" stroke-width="5"/>'
             '<path d="M262 54 v18 M262 80 v3" stroke="' + ink + '" stroke-width="8" stroke-linecap="round"/>')
    return ('<svg viewBox="0 0 300 440" width="300" height="440" xmlns="http://www.w3.org/2000/svg"><defs>' + defs + '</defs>' + body +
            '<g class="f f-idle">' + face("idle") + '</g>'
            '<g class="f f-happy">' + face("happy", happy_x, "translate(0,-6)") + '</g>'
            '<g class="f f-sad">' + face("sad", sad_x, "rotate(-4 150 180) translate(0,6)") + '</g>'
            '<g class="f f-wow">' + face("idle", wow_x, "translate(150 170) scale(1.06) translate(-150 -170)") + '</g></svg>')


def icon_svg(name: str) -> str:
    f = ASSETS / "icons" / "tabler" / f"{name}.svg"
    s = f.read_text(encoding="utf-8")
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    return re.sub(r"\s+", " ", s).strip()


def compose(spec: dict, tokens: dict | None = None) -> dict:
    """Return {config, palette, fonts, motion, music, baseTheme, recipe, matched}. Pure function of the spec words + seed."""
    d = spec.get("design") or {}
    words = " ".join(map(str, d.get("words") or [])) if isinstance(d.get("words"), list) else str(d.get("words") or "")
    text = " ".join([words, str(d.get("mood", "")), str(spec.get("title", "")), str(spec.get("subtitle", "")), str(d.get("subject", ""))])
    rid, matched = pick_recipe(text, str(d.get("subject", "")), str(d.get("mood", "")))
    r = RECIPES.get(rid, DEFAULT)
    seed = int(d.get("seed", 0))
    key = f"{rid}|{text}|{seed}"
    style = r["chars"][_h(key + "c") % len(r["chars"])]
    letter = "abcdefghijkl"[_h(key + "l") % 12]
    if style == "lorelei":
        letter = "abcdef"[_h(key + "l") % 6]
    named = named_theme(text)
    host_id = next((v for k, v in HOST_BY_WORD.items() if k in text), "")
    if not host_id:
        cands = RECIPE_HOSTS.get(rid, ["dice"])
        host_id = cands[_h(key + "h") % len(cands)]
    stage = RECIPE_STAGE.get(rid, "") if (rid in RECIPE_STAGE and _h(key + "s") % 3) else ""
    pal = r["pal"] or dict((tokens or {}).get("colors") or {})
    accent = pal.get("accent", "#ffd23f")
    props = list(r["props"])
    order = sorted(range(len(props)), key=lambda i: _h(f"{key}p{i}"))
    chosen = [props[i] for i in order][:7]
    icons = {n: icon_svg(n) for n in chosen}
    cfg = {
        "recipe": rid or "generic", "bg": r["bg"], "pattern": r["pattern"], "cel": r["cel"], "seed": _h(key) % 10000,
        "icons": icons, "props": chosen,
        "host": {"svg": host_svg(style, letter, accent, "#1a1020") if host_id == "dice" else "", "theme": "" if host_id == "dice" else host_id,
                 "name": "도우미", "style": f"dicebear-{style}" if host_id == "dice" else host_id, "lines": r["lines"]},
        "stage": stage, "partThemes": sorted({x for x in (stage, "" if host_id == "dice" else host_id) if x}),
        "palette": [pal.get(k) for k in ("primary", "accent", "bg1", "bg2", "card")],
    }
    out = {"named": named, "parts": {"background": r["bg"] + "+" + r["pattern"], "host": host_id if host_id != "dice" else f"dicebear-{style}/{letter}", "stage": stage or "-",
                                    "props": chosen, "celebration": r["cel"], "font": r["font"] or "(palette font)", "music": r["music"]},
           "config": cfg, "recipe": rid or "generic", "matched": matched, "character": f"dicebear-{style}/{letter}", "props": chosen}
    if r["pal"]:
        out["palette"] = r["pal"]
    if r["font"]:
        out["fonts"] = {"display": r["font"], "body": "Noto Serif KR" if r["font"] in ("Song Myung", "Noto Serif KR") else "Noto Sans KR"}
    for k in ("motion", "music"):
        if r[k]:
            out[k] = r[k]
    if r["base"]:
        out["baseTheme"] = r["base"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--words", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--subject", default="")
    ap.add_argument("--mood", default="")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = compose({"title": a.title, "design": {"words": a.words.split(), "subject": a.subject, "mood": a.mood, "seed": a.seed}})
    brief = {k: v for k, v in out.items() if k != "config"}
    brief["config_bytes"] = len(json.dumps(out["config"], ensure_ascii=False))
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
