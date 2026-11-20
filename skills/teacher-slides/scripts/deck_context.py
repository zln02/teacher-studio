# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Context recipes: one spec key (`"context": "class|promo|public|personal"`) switches a deck to expert conventions for that use.

    수업용  class     big readable type, one idea per slide, objectives -> activity/quiz -> recap
    홍보용  promo     bold visual, hero image area, short punchy copy, CTA + QR
    공공기관 보고용 public  formal cover (기관·날짜), 목차, 요약/핵심 box, Ⅰ./1./가. headings, tables, 자료/주 line on data slides,
                     restrained navy palette, 개조식 tone   (sources: ../references/context-recipes.md)
    개인용  personal  warm, photo-centric storytelling (가족 행사, 자기소개, 동호회)

Each recipe = layout set (allowed variants + family weights), type scale (px floor + multipliers), palette strategy, slide-type
defaults, text caps and lints. Same recipe drives the HTML deck (deck.py) and the .pptx (deck_pptx.py). Template-first still wins:
`--template mine.pptx` keeps the user's masters, `design.palette_from` keeps the user's colours; the recipe then adds only structure.
Pure data + spec transforms (no layout imports) so deck_style / deck_spec can import it without cycles.
"""
from __future__ import annotations

import re

ALIASES = {
    "class": "class", "lesson": "class", "수업": "class", "수업용": "class", "학습": "class",
    "promo": "promo", "promotion": "promo", "홍보": "promo", "홍보용": "promo", "모집": "promo", "광고": "promo",
    "public": "public", "official": "public", "report": "public", "gov": "public", "공공": "public", "공공기관": "public", "기관 보고": "public",
    "보고": "public", "보고용": "public", "공공기관 보고용": "public", "행정": "public",
    "personal": "personal", "개인": "personal", "개인용": "personal", "가족": "personal", "자기소개": "personal", "동호회": "personal",
}
LABEL = {"class": "수업용", "promo": "홍보용", "public": "공공기관 보고용", "personal": "개인용"}

# Navy / slate / teal: restrained public-sector palettes (white page, one dark accent, a quiet second tone). Contrast-checked by deck_style.
PUBLIC_PALETTES = {
    "gov-navy": {"bg1": "#ffffff", "bg2": "#f2f4f7", "text": "#1b1f24", "card": "#f5f7fa", "cardText": "#1b1f24", "cardBorder": "#c9d1dc",
                 "primary": "#1f3a68", "btnText": "#ffffff", "accent": "#3f6e9a", "good": "#1d4ed8", "bad": "#b42318"},
    "gov-slate": {"bg1": "#ffffff", "bg2": "#f3f4f6", "text": "#1f2328", "card": "#f6f7f9", "cardText": "#1f2328", "cardBorder": "#cfd4da",
                  "primary": "#2d3a4a", "btnText": "#ffffff", "accent": "#5b6b7f", "good": "#1d4ed8", "bad": "#b42318"},
    "gov-teal": {"bg1": "#ffffff", "bg2": "#f1f5f5", "text": "#1a2224", "card": "#f4f8f8", "cardText": "#1a2224", "cardBorder": "#c6d6d6",
                 "primary": "#0f5560", "btnText": "#ffffff", "accent": "#3d7f86", "good": "#1d4ed8", "bad": "#b42318"},
}

RECIPES: dict[str, dict] = {
    "class": {
        "styles": {"chalk-paper": 3, "nature-calm": 3, "pop-colorful": 3, "pastel-cute": 2, "glass-3d": 2, "anime-cartoon": 1},
        "mood": "밝게", "floor": 32, "tscale": {"h": 1.0, "p": 1.12},
        "type_px": {"cover": 120, "heading": 72, "body": 44, "caption": 32},
        "family": {"stack": 1.5, "bento": 1.5, "split": 1.2, "center": 1.1, "editorial": 0.8, "poster": 0.8},
        "allowed": {"bullets": ["cards", "stack", "rows"]},
        "caps": {"bullet_items": (2, 6), "bullet_chars": 60, "total": 330},
        "palette": "bright: the style's own high-contrast palette, ONE accent; answers blue/orange (colour-blind safe)",
        "slide_defaults": "title -> objectives -> (concept / steps / quiz / activity + timer) x n -> recap -> closing",
    },
    "promo": {
        "styles": {"pop-colorful": 4, "neon-cyber": 3, "festival-party": 3, "glass-3d": 3, "gold-luxury": 2, "tv-gameshow": 1},
        "mood": "신나게", "floor": 28, "tscale": {"h": 1.18, "p": 0.95},
        "type_px": {"cover": 160, "heading": 88, "body": 40, "caption": 28},
        "family": {"poster": 2.0, "bigtype": 2.0, "split": 1.3, "center": 1.1, "bento": 1.0, "editorial": 0.6, "stack": 0.6},
        "allowed": {"title": ["poster", "bottom", "left"], "bullets": ["cards", "stack"]},
        "caps": {"bullet_items": (2, 6), "bullet_chars": 60, "total": 330},
        "palette": "bold: saturated primary or a dark hero background; one loud accent for the CTA",
        "slide_defaults": "hero (image + headline + CTA) -> 3 reasons (bignumbers / cards) -> proof (quote / photo) -> CTA closing with QR",
    },
    "public": {
        "style": "minimal-premium", "palettes": list(PUBLIC_PALETTES), "mood": "단정하게", "floor": 24, "tscale": {"h": 0.72, "p": 0.8},
        "type_px": {"cover": 80, "heading": 52, "body": 32, "caption": 24},
        "family": {"editorial": 2.0, "stack": 1.3, "split": 1.0, "center": 0.8, "bento": 0.6, "bigtype": 0.4, "poster": 0.3},
        "allowed": {"title": ["gov"], "bullets": ["gov", "govsplit"], "compare": ["table"], "section": ["num"], "statement": ["center", "big"],
                    "bignumbers": ["cols", "duo"], "steps": ["list", "row"]},
        "caps": {"bullet_items": (2, 7), "bullet_chars": 70, "total": 440},
        "builds": False, "numbering": True, "header": True,
        "palette": "restrained: white page, navy/slate/teal accent, grey second tone; no gradients, no decoration",
        "slide_defaults": "표지(기관·날짜·부서) -> 목차 -> 요약(핵심 box) -> Ⅰ. 추진 배경 -> Ⅱ. 현황(표·그래프 + 자료:) -> Ⅲ. 추진 계획 -> Ⅳ. 향후 일정",
    },
    "personal": {
        "styles": {"pastel-cute": 4, "nature-calm": 3, "gold-luxury": 2, "festival-party": 2, "chalk-paper": 1},
        "mood": "따뜻하게", "floor": 28, "tscale": {"h": 1.0, "p": 1.0},
        "type_px": {"cover": 112, "heading": 64, "body": 38, "caption": 28},
        "family": {"poster": 1.6, "split": 1.4, "center": 1.3, "bigtype": 1.1, "bento": 0.8, "editorial": 0.9},
        "allowed": {},
        "caps": {"bullet_items": (2, 6), "bullet_chars": 60, "total": 330},
        "palette": "warm: cream / soft paper backgrounds, one warm accent; photos carry the colour",
        "slide_defaults": "photo cover (hero) -> story beats (image + caption, timeline) -> quote / thanks",
    },
}

DATA_TYPES = ("chart", "table", "bignumber", "bignumbers")
CONTENT_TYPES = ("bullets", "compare", "steps", "bignumbers", "bignumber", "timeline", "chart", "table", "summary", "illustration", "image", "quiz", "math", "diagram")
ROMAN = "Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ".split()
GANA = "가나다라마바사아자차카타파하"
_NUMBERED = re.compile(r"^\s*(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|\d+\.|[가-하]\.|\d+\)|[가-하]\))\s")


def context_of(spec: dict) -> str:
    """'' when the spec has no context (old decks look exactly as before)."""
    v = str((spec or {}).get("context") or "").strip().lower()
    if not v:
        return ""
    if v in RECIPES:
        return v
    for k, c in ALIASES.items():
        if k in v:
            return c
    return ""


def recipe(ctx: str) -> dict:
    return RECIPES.get(ctx, {})


def gov_date(s: str) -> str:
    """'2026-11-19' / '2026.11.19' / '2026년 11월 19일' -> '2026. 11. 19.' (공문서 날짜: 연·월·일 글자 대신 온점, 앞 0 없음)."""
    m = re.search(r"(\d{4})\s*[-./년]\s*(\d{1,2})\s*[-./월]\s*(\d{1,2})", str(s or ""))
    if not m:
        return str(s or "")
    y, mo, d = m.groups()
    return f"{y}. {int(mo)}. {int(d)}."


GOV_DATE_OK = re.compile(r"^\d{4}\. (?:[1-9]|1[0-2])\. (?:[1-9]|[12]\d|3[01])\.(?:\s*\([월화수목금토일]\))?$")


def roman(n: int) -> str:
    return ROMAN[n - 1] if 1 <= n <= len(ROMAN) else str(n)


def item_level(s: str) -> tuple[int, str]:
    """Bullet item -> (level 1..3, text). '- x' = level 2, '-- x' = level 3 (공공 보고: □ / ○ / -)."""
    t = str(s)
    m = re.match(r"^\s*(-{1,2})\s+", t)
    if not m:
        return 1, t.strip()
    return 1 + len(m.group(1)), t[m.end():].strip()


MARKS = {"box": ("□", "○", "-"), "num": None}


def marker(level: int, idx: int, style: str = "box") -> str:
    """□ ○ - (default, 개조식 관행) or 가./1)/가) when style == 'num'."""
    if style == "num":
        return (f"{GANA[idx % len(GANA)]}.", f"{idx + 1})", f"{GANA[idx % len(GANA)]})")[level - 1]
    return MARKS["box"][level - 1]


# ---- spec transforms ---------------------------------------------------------------------------------------------------
def _ins_after_cover(slides: list, new: list) -> list:
    i = 1 if slides and slides[0].get("type") in ("title", "cover", "hero", "intro") else 0
    return slides[:i] + new + slides[i:]


def pre(spec: dict) -> dict:
    """Before normalising: context slide types (objectives / recap / activity / toc aliases) and auto slides from top-level lists."""
    ctx = context_of(spec)
    s = dict(spec)
    slides = [dict(x) for x in (s.get("slides") or s.get("items") or [])]
    out = []
    for it in slides:
        t = str(it.get("type", ""))
        if t in ("objectives", "목표", "학습목표"):
            it = {**it, "type": "bullets", "title": it.get("title") or "오늘의 학습 목표", "kicker": it.get("kicker") or "학습 목표", "_role": "objectives"}
        elif t in ("recap", "정리", "summary-recap"):
            it = {**it, "type": "bullets", "title": it.get("title") or "오늘 배운 것", "kicker": it.get("kicker") or "정리", "_role": "recap"}
        elif t in ("activity", "활동"):
            base = {**it, "kicker": it.get("kicker") or "활동", "title": it.get("title") or "함께 해 봐요", "_role": "activity"}
            if it.get("minutes"):
                base["note"] = (str(it.get("note", "")) + f" (활동 {int(it['minutes'])}분)").strip()
            it = {**base, "type": "steps"} if it.get("steps") else {**base, "type": "bullets"}
        elif t in ("agenda-toc", "목차", "contents"):
            it = {**it, "type": "toc"}
        elif t in ("요약", "핵심", "key"):
            it = {**it, "type": "summary"}
        out.append(it)
    if ctx and s.get("objectives") and not any(x.get("_role") == "objectives" for x in out):
        out = _ins_after_cover(out, [{"type": "bullets", "title": "오늘의 학습 목표", "kicker": "학습 목표", "items": list(s["objectives"]), "_role": "objectives"}])
    if ctx and s.get("recap") and not any(x.get("_role") == "recap" for x in out):
        rc = {"type": "bullets", "title": "오늘 배운 것", "kicker": "정리", "items": list(s["recap"]), "_role": "recap"}
        j = next((k for k in range(len(out) - 1, -1, -1) if out[k].get("type") in ("closing", "end", "thanks", "outro")), len(out))
        out = out[:j] + [rc] + out[j:]
    if ctx == "public":
        if s.get("summary") and not any(x.get("type") == "summary" for x in out):
            out = _ins_after_cover(out, [{"type": "summary", "title": "요약", "points": list(s["summary"])}])
        secs = [x for x in out if x.get("type") == "section"]
        if len(secs) >= 2 and not any(x.get("type") == "toc" for x in out) and s.get("toc", True) is not False:
            out = _ins_after_cover(out, [{"type": "toc", "title": "목차", "_auto": True}])
        if s.get("date"):
            s["date"] = gov_date(s["date"])
        d = s.setdefault("design", {}) if isinstance(s.get("design"), dict) or not s.get("design") else s["design"]
        if isinstance(d, dict):
            d.setdefault("builds", False)
            s["design"] = d
    s["slides"] = out
    s.pop("items", None)
    return s


def post(spec: dict) -> dict:
    """After normalising: public numbering (Ⅰ. section / 1. slide title within the section), toc items, cover fields."""
    ctx = context_of(spec)
    if not ctx:
        return spec
    slides = spec["slides"]
    for it in slides:
        it["_ctx"] = ctx
    if ctx != "public":
        return spec
    sec_titles = [str(x.get("title", "")) for x in slides if x["type"] == "section"]
    sec, n, cur = 0, 0, ""
    for it in slides:
        t = it["type"]
        if t == "section":
            sec += 1
            n = 0
            raw = re.sub(_NUMBERED, "", str(it["title"]))
            cur = f"{roman(sec)}. {raw}"
            it["title"] = raw  # the big section number is the Roman numeral itself (no 01 + Ⅰ. twice)
            it["num"] = roman(sec)
            it["_secno"] = sec
        elif t in CONTENT_TYPES and t != "summary" and it.get("title") and spec.get("numbering", True) is not False:
            if not _NUMBERED.match(str(it["title"])):
                n += 1
                it["title"] = f"{n}. {it['title']}"
        it["_section"] = cur
        if t == "toc" and not it.get("items"):
            it["items"] = [re.sub(_NUMBERED, "", x) for x in sec_titles] or ["요약"]
        if t == "title":
            it["_org"] = str(spec.get("org") or spec.get("agency") or it.get("kicker") or "")
            it["_date"] = gov_date(spec.get("date") or it.get("date") or "")
            it["_dept"] = str(spec.get("dept") or it.get("meta") or "")
    return spec


# ---- lints -------------------------------------------------------------------------------------------------------------
_POLITE = re.compile(r"(?:습니다|니다|어요|아요|해요|예요|이에요|세요|죠)[.!?]?\s*$")


def lint(spec: dict) -> tuple[list[str], list[str]]:
    """(errors, warnings) for the context's conventions. Errors stop the build like other spec errors (fix list)."""
    ctx = context_of(spec)
    errs: list[str] = []
    warns: list[str] = []
    if not ctx:
        return errs, warns
    slides = spec.get("slides") or []
    types = [x.get("type") for x in slides]
    if ctx == "public":
        for i, it in enumerate(slides, 1):
            t = it.get("type")
            if t in DATA_TYPES or (t == "compare" and it.get("rows")):
                if not str(it.get("source") or "").strip():
                    errs.append(f"slide {i} {t}: 공공 보고 자료 장에는 출처가 필요해요 -> \"source\": \"기관명, 자료명(연도)\" (주석은 \"footnote\")")
            texts = []
            if t in ("closing", "quote"):  # 「감사합니다」 and quotations are not 개조식 body text
                continue
            for k in ("title", "text", "sub", "caption", "takeaway"):
                if isinstance(it.get(k), str):
                    texts.append(it[k])
            for k in ("items", "points"):
                texts += [str(x) for x in it.get(k) or []]
            polite = [x for x in texts if _POLITE.search(x.replace("**", ""))]
            if polite:
                warns.append(f"slide {i}: 개조식이 아니에요 ('{polite[0][:16]}...') -> 명사형으로 끝내기 (~함, ~임, ~추진, ~예정)")
        if "summary" not in types:
            warns.append("공공 보고: 요약(핵심) 장이 없어요 -> \"summary\": [\"핵심 1\", ...] 또는 {\"type\":\"summary\"} 추가")
        if not (spec.get("org") or spec.get("agency")):
            warns.append("공공 보고: 표지에 기관명이 없어요 -> spec \"org\": 실제 기관명, 모르면 \"우리 학교\" (빈칸·○○ 금지)")
        if not ({"table", "chart"} & set(types)):
            warns.append("공공 보고: 표나 그래프가 없어요 -> 실적은 {\"type\":\"table\"} / {\"type\":\"chart\"} + \"source\" (서로 맞는 숫자로)")
        if len(slides) >= 8 and not ({"timeline", "steps"} & set(types)):
            warns.append("공공 보고: 일정 장이 없어요 -> 향후 계획은 {\"type\":\"timeline\"} (분기·월별)")
        d = str(spec.get("date") or "")
        if not d:
            warns.append("공공 보고: 표지 날짜가 없어요 -> spec \"date\": \"2026. 11. 19.\"")
        elif not GOV_DATE_OK.match(d.strip()):
            warns.append(f"공공 보고: 날짜 형식 '{d}' -> 2026. 11. 19. (연·월·일 대신 온점)")
    elif ctx == "class":
        if not any(x.get("_role") == "objectives" for x in slides) and not spec.get("objectives"):
            warns.append("수업용: 학습 목표 장이 없어요 -> spec \"objectives\": [...] (표지 다음에 자동으로 들어가요)")
        if not ({"quiz", "timer"} & set(types)) and not any(x.get("_role") == "activity" for x in slides):
            warns.append("수업용: 퀴즈나 활동 장이 없어요 -> {\"type\":\"quiz\"} 또는 {\"type\":\"activity\"} 한 장")
        if not any(x.get("_role") == "recap" for x in slides) and not spec.get("recap"):
            warns.append("수업용: 정리 장이 없어요 -> spec \"recap\": [...] (마무리 앞에 자동으로 들어가요)")
        for i, it in enumerate(slides, 1):
            if it.get("type") == "bullets" and len(it.get("items") or []) > 4:
                warns.append(f"slide {i}: 수업용은 한 장에 4개까지가 잘 읽혀요 ({len(it['items'])}개) -> 두 장으로 나누기")
            if it.get("type") == "quiz" and not str(it.get("explain") or "").strip():
                warns.append(f"slide {i}: 확인 문제에 풀이가 없어요 -> \"explain\": \"한 줄 풀이\" (PPT의 정답 장에 함께 나와요)")
        if len(slides) >= 8:
            n_quiz = types.count("quiz")
            n_act = sum(1 for x in slides if x.get("_role") == "activity") + types.count("timer")
            if n_quiz < 2:
                warns.append(f"수업용: 확인 문제가 {n_quiz}개예요 -> 개념 묶음마다 하나씩, 2개 이상 ({{\"type\":\"quiz\",\"answer\":0,\"explain\":\"...\"}})")
            if not n_act:
                warns.append("수업용: 활동 장이 없어요 -> {\"type\":\"activity\",\"minutes\":5,\"steps\":[...]} 한 장 (준비물은 note에)")
            if not ({"diagram", "image", "compare", "table", "chart", "steps", "timeline", "illustration"} & set(types)):
                warns.append("수업용: 그림·표가 하나도 없어요 -> 교과서에 그림이 있는 개념은 {\"type\":\"diagram\"}으로 그리기 (광선, 순환, 구조)")
    elif ctx == "promo":
        if not any((x.get("type") in ("hero", "closing", "qr")) and (x.get("url") or x.get("cta")) for x in slides):
            warns.append("홍보용: 행동 유도(CTA)가 없어요 -> hero의 \"cta\" 또는 closing의 \"url\"(QR)")
        for i, it in enumerate(slides, 1):
            h = str(it.get("headline") or it.get("title") or "")
            if it.get("type") in ("hero", "title", "statement") and len(h.replace("**", "")) > 24:
                warns.append(f"slide {i}: 홍보 문구는 짧을수록 세요 ({len(h)}자) -> 24자 이내")
            if it.get("type") == "bullets" and len(it.get("items") or []) > 3:
                warns.append(f"slide {i}: 홍보용은 3개까지 -> 핵심만 남기기")
    elif ctx == "personal":
        if not ({"image", "hero"} & set(types)):
            warns.append("개인용: 사진 장이 있으면 훨씬 따뜻해져요 -> {\"type\":\"image\",\"file\":\"...\"} 또는 hero에 file")
    return errs, warns
