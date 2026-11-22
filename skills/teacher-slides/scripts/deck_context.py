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
        "palette": "bright: the topic's colour when it has one, else the style's palette; one main colour + up to two marker colours; answers blue/orange (colour-blind safe)",
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
CONTENT_TYPES = ("bullets", "compare", "steps", "bignumbers", "bignumber", "timeline", "chart", "table", "summary", "illustration", "image", "quiz", "math", "diagram", "panel")
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
    import deck_shape
    slides = deck_shape.resolve([dict(x) for x in (s.get("slides") or s.get("items") or [])])  # {"type": "auto"} -> the type the content's shape asks for
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


# ---- dates: the weekday is computed, never recalled ----------------------------------------------------------------------
_DATE_WD = re.compile(r"(?:(20\d{2})\s*[.년/-]\s*)?(\d{1,2})\s*[.월/]\s*(\d{1,2})\s*[.일]?\s*\(\s*([월화수목금토일])(?:요일)?\s*\)")
_YEAR = re.compile(r"(20\d{2})\s*(?:[.년]|학년도)")


def _strings(o, skip=("note", "file", "url", "tex", "fillins")):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in skip and not str(k).startswith("_"):
                yield from _strings(v, skip)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v, skip)


def weekday_errors(spec: dict) -> list[str]:
    """Dates written with a weekday - 2026. 12. 5.(금), 12월 5일(토) - whose weekday is wrong. A date without a year takes the deck's year
    (the one year written in the deck; with none or several, such dates are left alone)."""
    import datetime
    texts = list(_strings({k: v for k, v in spec.items() if k in ("slides", "title", "date", "summary", "objectives", "recap")}))
    years = {int(y) for t in texts for y in _YEAR.findall(t)}
    year0 = next(iter(years)) if len(years) == 1 else None
    out = []
    for t in texts:
        for y, m, d, wd in _DATE_WD.findall(t):
            yy = int(y) if y else year0
            if not yy:
                continue
            try:
                real = "월화수목금토일"[datetime.date(yy, int(m), int(d)).weekday()]
            except ValueError:
                out.append(f"없는 날짜예요: {yy}. {m}. {d}. -> 날짜를 다시 확인하세요")
                continue
            if real != wd:
                msg = f"요일이 달라요: {yy}. {int(m)}. {int(d)}.은 ({wd})이 아니라 ({real})요일 -> 요일을 고치거나 날짜를 다시 정하세요 (요일은 계산해서 적기)"
                if msg not in out:
                    out.append(msg)
    return out


# ---- what a report must not leave out ------------------------------------------------------------------------------------------
# A part of a report and the words a slide uses when it covers that part. The names are what the WARN line shows the author.
PARTS = {
    "실적": ("실적", "현황", "참여", "운영 결과", "추진 결과", "개설", "이용", "수강", "건수", "횟수"),
    "예산": ("예산", "집행", "결산", "재원", "지출", "편성", "사업비", "비용", "지원금", "교부"),
    "성과": ("성과", "만족도", "효과", "달성", "향상", "설문", "우수 사례", "변화"),
    "계획": ("계획", "일정", "향후", "내년", "차기", "개선", "과제", "추진 방향", "로드맵"),
    "문제점": ("문제점", "한계", "미흡", "어려움", "애로", "보완", "개선"),
    "건의": ("건의", "요청", "지원 요청", "협조", "제안"),
    "추진 체계": ("추진 체계", "조직", "담당", "역할", "협력", "운영 체계"),
    "안전": ("안전", "사고", "예방", "점검"),
    "홍보": ("홍보", "안내", "가정통신문", "누리집"),
}
_PART_ASK = {"실적": ("실적", "현황"), "예산": ("예산", "집행", "결산", "사업비"), "성과": ("성과", "만족도", "효과"), "계획": ("계획", "일정", "향후", "내년", "로드맵"),
             "문제점": ("문제점", "한계", "애로"), "건의": ("건의",), "추진 체계": ("추진 체계", "조직"), "안전": ("안전",), "홍보": ("홍보",)}
_RESULT = re.compile(r"(?:운영|추진|사업|교육|활동|집행)?\s*(?:결과|성과|실적)(?:\s*(?:보고|발표|공유|및|와|과|,))?|결산|평가\s*보고|성과\s*보고")
_PART_HINT = {"실적": "무엇을 얼마나 했는지 수치 표·그래프", "예산": "편성액·집행액·집행률 표 (모르면 예시 수치로 쓰고 표시)", "성과": "만족도·달성률 같은 결과 수치",
              "계획": "다음 일정·개선 계획 (timeline)", "문제점": "잘 안 된 점과 까닭", "건의": "받는 기관에 바라는 점"}


def _slide_text(it: dict) -> str:
    """Every word a slide shows (titles, lists, tables, panel blocks), for asking whether a part is covered."""
    out = []

    def walk(v, key=""):
        if key in ("note", "source", "footnote", "file", "layout", "type", "kind"):
            return
        if isinstance(v, dict):
            for k_, x in v.items():
                walk(x, k_)
        elif isinstance(v, list):
            for x in v:
                walk(x, key)
        elif isinstance(v, str):
            out.append(v)
    walk(it)
    return " ".join(out)


def required_parts(spec: dict) -> list:
    """The parts this deck has to carry: what the author listed (`must`), what the request / title names, and - for a results report -
    the four things any reader of one looks for (실적, 예산, 성과, 계획). `omit` takes a part off the list when it truly does not apply."""
    asked = " ".join(str(spec.get(k) or "") for k in ("request", "title", "subtitle"))
    need = []
    for m in spec.get("must") or spec.get("required") or []:
        if str(m).strip() and str(m).strip() not in need:
            need.append(str(m).strip())
    for part, words in _PART_ASK.items():
        if any(w in asked for w in words) and part not in need and not any(part in n_ or n_ in part for n_ in need):
            need.append(part)
    if context_of(spec) == "public" and _RESULT.search(asked):
        for part in ("실적", "예산", "성과", "계획"):
            if part not in need:
                need.append(part)
    omit = [str(x) for x in spec.get("omit") or []]
    return [n_ for n_ in need if not any(o and (o in n_ or n_ in o) for o in omit)]


def missing_parts(spec: dict) -> list:
    """Required parts no body slide covers. A part named only on the cover / 목차 / 요약 line does not count: it needs its own content."""
    slides = [it for it in spec.get("slides") or [] if isinstance(it, dict)]
    body = [it for it in slides if it.get("type") not in ("title", "hero", "toc", "closing", "section")]
    texts = [_slide_text(it) for it in body if it.get("type") != "summary"]
    heads = [str(it.get("title") or "") + " " + str(it.get("_section") or "") + " " + str(it.get("kicker") or "") for it in body if it.get("type") != "summary"]
    out = []
    for part in required_parts(spec):
        words = PARTS.get(part) or (part,)
        if part == "예산":  # a budget is covered by figures, not by the word in passing
            ok = any(any(w in h for w in words) for h in heads) or any(sum(t.count(w) for w in words) >= 2 and re.search(r"\d", t) for t in texts)
        else:
            ok = any(any(w in h for w in words) for h in heads) or sum(1 for t in texts if any(w in t for w in words)) >= 1
        if not ok:
            out.append(part)
    return out


# ---- lints -------------------------------------------------------------------------------------------------------------
_POLITE = re.compile(r"(?:습니다|니다|어요|아요|해요|예요|이에요|세요|죠)[.!?]?\s*$")


_EX_SRC = re.compile(r"가상|예시|임의|샘플|허구|지어낸")  # an example marker inside a source / footnote line


def dspec_quiz_set(it: dict) -> list:
    import deck_spec
    return deck_spec.quiz_set(it)


_FRAME_ROLES = ("objectives", "recap")


def frame_notes(spec: dict, slides: list) -> list[str]:
    """A lesson deck spends its pages on ideas first: cover, goals, check questions, answers, recap and closing (the frame) must not
    outnumber the slides that teach in a deck of ten or fewer pages. There the frame folds into neighbours instead of pushing a sub-topic out."""
    types = [x.get("type") for x in slides]
    total = len(slides) + (1 if "quiz" in types else 0)  # + the 「확인 문제 정답」 page the .pptx adds
    try:
        total = max(total, int(spec.get("target_slides") or 0))
    except (TypeError, ValueError):
        pass
    content = sum(1 for x in slides if x.get("type") not in ("title", "closing", "section", "quiz", "toc") and x.get("_role") not in _FRAME_ROLES)
    if 0 < total <= 10 and content * 2 < total:  # a longer deck has room for its frame; a short one loses a sub-topic to it
        return [f"수업용: 내용 장이 {content}장뿐이에요 ({total}장 중, 정답 장 포함) -> 가르치는 장이 절반은 넘게: 학습 목표는 표지 \"subtitle\" 한 줄로, "
                "정리는 마무리 \"sub\"로, 확인 문제 2~3개는 한 장에 (\"questions\": [...]) 모으고, 비운 자리에 단원의 빠진 내용을 넣기"]
    return []


def _words(t) -> list:
    return [w for w in re.findall(r"[가-힣A-Za-z0-9]+", str(t or "").replace("**", "")) if len(w) >= 2]


def drawing_notes(i: int, shapes: list, siblings: list | None = None) -> list[str]:
    """Two soft checks on a drawing (a `diagram` slide or a panel's diagram block):
    bare shapes - three or more separate filled outlines with nothing inside them and no lines between them (a row of plain
    triangles / circles / squares standing for real things: signs, signals, tools), so the drawing shows a shape, not the thing;
    repeated words - the cards beside the drawing say again what its labels already say (the same words twice, nothing added)."""
    out = []
    sh = [x for x in shapes or [] if isinstance(x, dict)]
    import deck_diagram as dg
    kinds = [dg.kind_of(x) for x in sh]
    if not any(k in ("line", "dash", "arrow", "dasharrow") for k in kinds) and "icon" not in kinds:
        def box(x):
            k = dg.kind_of(x)
            f = dg._f
            if k == "rect":
                return f(x.get("x")), f(x.get("y")), f(x.get("x")) + f(x.get("w")), f(x.get("y")) + f(x.get("h"))
            if k == "circle":
                rx, ry = dg.radii(x)
                return f(x.get("cx")) - rx, f(x.get("cy")) - ry, f(x.get("cx")) + rx, f(x.get("cy")) + ry
            if k == "poly" and isinstance(x.get("points"), list) and x["points"]:
                xs = [f(p[0]) for p in x["points"] if isinstance(p, (list, tuple)) and len(p) == 2]
                ys = [f(p[1]) for p in x["points"] if isinstance(p, (list, tuple)) and len(p) == 2]
                return (min(xs), min(ys), max(xs), max(ys)) if xs and ys else None
            return None
        figs = [(j, box(x)) for j, x in enumerate(sh) if kinds[j] in ("rect", "circle", "poly") and x.get("fill") != "none" and box(x)]

        def inside(b, c):
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            return c[0] <= cx <= c[2] and c[1] <= cy <= c[3]
        top = [(j, b) for j, b in figs if not any(j2 != j and inside(b, b2) and (b2[2] - b2[0]) * (b2[3] - b2[1]) > (b[2] - b[0]) * (b[3] - b[1]) for j2, b2 in figs)]
        bare = [j for j, b in top if not any(j2 != j and inside(b2, b) for j2, b2 in figs)]
        if len(bare) >= 3:
            out.append(f"slide {i}: 그림 {len(bare)}개가 속이 빈 맨 도형이에요 -> 실제 물건(표지·기구·동식물·기호)을 나타낸다면 알아보게 그리기: "
                       "실제 모양과 테두리·색, 안의 그림(kind \"icon\": person-standing, bike, baby, car ...). 다 그리기 어려우면 개수를 줄이고 제대로")
    if siblings:
        labels = [x.get("text") for x in sh if x.get("text")]
        texts = [" ".join([str(c.get("title") or "")] + [str(m) for m in (c.get("items") or [])] + [str(c.get("text") or "")]) if isinstance(c, dict) else str(c)
                 for c in siblings]
        dup = [l_ for l_ in labels if _words(l_) and any(all(w in t for w in _words(l_)) for t in texts)]
        if len(dup) >= 2:
            out.append(f"slide {i}: 그림의 이름표({', '.join(str(d) for d in dup[:3])})를 옆 칸이 다시 말해요 -> 같은 말은 한 번만: "
                       "옆 칸에는 그림이 보여 주지 못하는 것(까닭, 예외, 예, 헷갈리는 것)을")
    return out


def lint(spec: dict) -> tuple[list[str], list[str]]:
    """(errors, warnings) for the context's conventions. Errors stop the build like other spec errors (fix list)."""
    ctx = context_of(spec)
    errs: list[str] = []
    warns: list[str] = []
    import deck_shape
    warns += deck_shape.notes(spec.get("slides") or [])  # every deck, with or without a context: the slide type follows the content's shape
    errs += weekday_errors(spec)  # a wrong weekday on a notice sends people on the wrong day: the build stops
    if not ctx:
        return errs, warns
    slides = spec.get("slides") or []
    for part in missing_parts(spec):  # every context: what the request names (and, for a results report, what its reader looks for) must not vanish
        warns.append(f"꼭 담을 내용이 빠졌어요: 「{part}」 -> {_PART_HINT.get(part, '이 내용을 다루는 장')}을(를) 한 장 넣기. "
                     f"정말 해당 없으면 spec \"omit\": [\"{part}\"] 로 알리고 마지막 답에 한 줄로 말하기")
    types = [x.get("type") for x in slides]
    pk = {b.get("kind") for x in slides if x.get("type") == "panel" for b in x.get("blocks") or [] if isinstance(b, dict)}  # block kinds inside panels
    # the user named a length (「10장」「10장 정도」): the deck lands on it. One page over is allowed only for the answers slide; any other
    # miss is a WARN the author fixes, and a deck far over (more than about a seventh) stops the build.
    L = deck_shape.length(spec, ctx == "public")
    if L["hard"]:
        errs.append(f"{L['got']}장이에요 (요청 {L['want']}장, 「확인 문제 정답」 장 포함) -> {L['want']}장으로: 비슷한 개념 장을 합치고, 정리는 마무리 장과 합치기 (내용을 버리지 말고 한 장에 두 가지를 담기)")
    else:
        warns += ["장수: " + n for n in deck_shape.length_notes(spec, ctx == "public")]
    # the unknowns rule: ONE example note per file. A source or footnote line that says 「가상」「예시」 on slide after slide is that note
    # repeated; the source line names the record, the note is written once (first slide's speaker notes, added by the build from "fillins").
    ex_src = [i for i, it in enumerate(slides, 1) if isinstance(it, dict) and _EX_SRC.search(" ".join(str(it.get(k) or "") for k in ("source", "footnote", "caption")))]
    if len(ex_src) >= 2:
        errs.append(f"slide {', '.join(map(str, ex_src[:8]))}: 출처·주석 줄 {len(ex_src)}곳에 「가상」「예시」를 되풀이했어요 -> 예시 안내는 파일 전체에서 한 번만. "
                    "출처 줄에는 자료 이름만 쓰고(예: \"source\": \"우리 학교 급식 운영 기록(2026)\"), 예시로 채운 값은 spec \"fillins\"에 적으세요 "
                    "(첫 장 발표자 메모에 안내 한 줄이 자동으로 들어가요)")
    if ctx == "public":
        for i, it in enumerate(slides, 1):
            t = it.get("type")
            if t in DATA_TYPES or (t == "compare" and it.get("rows")) or (t == "panel" and any(isinstance(b, dict) and b.get("kind") in ("chart", "table", "kpis") for b in it.get("blocks") or [])):
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
            if t == "panel":
                import deck_panel
                texts += deck_panel.texts(it)
            polite = [x for x in texts if _POLITE.search(x.replace("**", ""))]
            if polite:
                warns.append(f"slide {i}: 개조식이 아니에요 ('{polite[0][:16]}...') -> 명사형으로 끝내기 (~함, ~임, ~추진, ~예정)")
        if "summary" not in types:
            warns.append("공공 보고: 요약(핵심) 장이 없어요 -> \"summary\": [\"핵심 1\", ...] 또는 {\"type\":\"summary\"} 추가")
        if not (spec.get("org") or spec.get("agency")):
            warns.append("공공 보고: 표지에 기관명이 없어요 -> spec \"org\": 실제 기관명, 모르면 \"우리 학교\" (빈칸·○○ 금지)")
        if not ({"table", "chart"} & (set(types) | pk)):
            warns.append("공공 보고: 표나 그래프가 없어요 -> 실적은 {\"type\":\"table\"} / {\"type\":\"chart\"} + \"source\" (서로 맞는 숫자로)")
        n_data = sum(1 for x in slides if x.get("type") in ("table", "chart", "bignumbers", "bignumber") or (x.get("type") == "compare" and x.get("rows"))
                     or (x.get("type") == "panel" and any(isinstance(b, dict) and b.get("kind") in ("chart", "table", "kpis") for b in x.get("blocks") or [])))
        n_body = sum(1 for x in slides if x.get("type") not in ("title", "toc", "section", "closing", "summary"))
        if n_body >= 6 and n_data < max(3, round(n_body * 0.4)):
            warns.append(f"공공 보고: 수치가 든 장이 {n_data}장뿐이에요 (본문 {n_body}장) -> 실적·예산·성과마다 표나 그래프 하나씩, 본문의 절반쯤은 숫자로 말하기")
        if len(slides) >= 8 and not ({"timeline", "steps", "flow"} & (set(types) | pk)):
            warns.append("공공 보고: 일정 장이 없어요 -> 향후 계획은 {\"type\":\"timeline\"} (분기·월별)")
        d = str(spec.get("date") or "")
        if not d:
            warns.append("공공 보고: 표지 날짜가 없어요 -> spec \"date\": \"2026. 11. 19.\"")
        elif not GOV_DATE_OK.match(d.strip()):
            warns.append(f"공공 보고: 날짜 형식 '{d}' -> 2026. 11. 19. (연·월·일 대신 온점)")
    elif ctx == "class":
        import deck_style
        if deck_style.audience_band(spec) in ("young", "kid"):  # a young room: the screen is read aloud, a line at a time
            long_ = [i for i, it in enumerate(slides, 1) if it.get("type") == "bullets" and (len(it.get("items") or []) > 4 or any(len(str(x)) > 34 for x in it.get("items") or []))]
            if long_:
                warns.append(f"slide {', '.join(map(str, long_[:4]))}: 어린 학년에게는 글이 많아요 -> 한 장에 3~4줄, 한 줄 30자 안쪽, 아이 말투(~해요)로")
            if deck_style.audience_band(spec) == "young":
                def pictured(x):
                    return bool(x.get("pics") or x.get("pic") or x.get("shapes") or x.get("type") in ("diagram", "image", "illustration")
                                or any(isinstance(x.get(k), dict) and x[k].get("pics") for k in ("a", "b"))
                                or any(isinstance(m, dict) and m.get("pic") for m in x.get("steps") or [])
                                or any(isinstance(b, dict) and (b.get("kind") == "diagram" or any(isinstance(m, dict) and m.get("pic") for m in b.get("items") or [])) for b in x.get("blocks") or []))
                idea = [x for x in slides if x.get("type") in ("bullets", "compare", "steps", "quiz", "panel", "table") and x.get("_role") not in ("objectives",)]
                n_pic = sum(1 for x in idea if pictured(x))
                if idea and n_pic * 2 < len(idea):
                    warns.append(f"저학년 수업: 낱말에 그림이 붙은 장이 {n_pic}장뿐이에요 (내용 {len(idea)}장) -> 낱말·예시·보기마다 앞에 이모지 하나 "
                                 "(\"🐶 멍멍: 강아지가 짖어요\", 보기 \"⭐ 반짝반짝\", 단계 제목 \"✂️ 오리기\"): 빌드가 글에서 떼어 낱말 옆에 크게 그려요. 제목에는 쓰지 않기")
                if not any(x.get("type") == "title" and (x.get("pic") or x.get("shapes")) for x in slides):
                    warns.append("저학년 수업: 표지에 그림이 없어요 -> 표지에 \"pic\": \"🌧️\" (주제를 보여 주는 이모지 하나) 또는 \"shapes\"로 직접 그리기")
        warns += frame_notes(spec, slides)
        for i, it in enumerate(slides, 1):
            if it.get("type") == "diagram":
                warns += drawing_notes(i, it.get("shapes") or [])
            elif it.get("type") == "panel":
                bl = [b for b in it.get("blocks") or [] if isinstance(b, dict)]
                sib = [m for b in bl if b.get("kind") in ("cards", "list") for m in (b.get("items") or [])]
                for b in bl:
                    if b.get("kind") == "diagram":
                        warns += drawing_notes(i, b.get("shapes") or [], sib)
        try:
            want_ = int(spec.get("target_slides") or 0)
        except (TypeError, ValueError):
            want_ = 0
        short = 0 < (want_ or len(slides) + (1 if "quiz" in types else 0)) <= 8  # a short lesson deck: the frame folds into the content slides
        cover_goal = any(x.get("type") == "title" and (x.get("subtitle") or x.get("objectives")) for x in slides)
        if not any(x.get("_role") == "objectives" for x in slides) and not spec.get("objectives") and not (short and cover_goal):
            warns.append("수업용: 학습 목표 장이 없어요 -> spec \"objectives\": [...] (표지 다음에 자동으로 들어가요; 8장 이하면 표지 \"subtitle\"에 목표 한 줄로도 돼요)")
        if not ({"quiz", "timer"} & set(types)) and not any(x.get("_role") == "activity" for x in slides):
            warns.append("수업용: 퀴즈나 활동 장이 없어요 -> {\"type\":\"quiz\"} 또는 {\"type\":\"activity\"} 한 장")
        closing_recap = any(x.get("type") == "closing" and (x.get("sub") or x.get("next")) for x in slides)
        if not any(x.get("_role") == "recap" for x in slides) and not spec.get("recap") and not (short and closing_recap):
            warns.append("수업용: 정리 장이 없어요 -> spec \"recap\": [...] (마무리 앞에 자동으로 들어가요)")
        for i, it in enumerate(slides, 1):
            if it.get("type") == "bullets" and len(it.get("items") or []) > 4:
                warns.append(f"slide {i}: 수업용은 한 장에 4개까지가 잘 읽혀요 ({len(it['items'])}개) -> 두 장으로 나누기")
            if it.get("type") == "quiz" and not str(it.get("explain") or "").strip():
                warns.append(f"slide {i}: 확인 문제에 풀이가 없어요 -> \"explain\": \"한 줄 풀이\" (PPT의 정답 장에 함께 나와요)")
        if len(slides) >= 8:
            n_quiz = sum(len(dspec_quiz_set(x)) for x in slides if x.get("type") == "quiz")
            n_act = sum(1 for x in slides if x.get("_role") == "activity") + types.count("timer")
            if n_quiz < 2:
                warns.append(f"수업용: 확인 문제가 {n_quiz}개예요 -> 개념 묶음마다 하나씩, 2개 이상 ({{\"type\":\"quiz\",\"answer\":0,\"explain\":\"...\"}})")
            if not n_act and not short:
                warns.append("수업용: 활동 장이 없어요 -> {\"type\":\"activity\",\"minutes\":5,\"steps\":[...]} 한 장 (준비물은 note에)")
            if not ({"diagram", "image", "compare", "table", "chart", "steps", "timeline", "illustration", "panel"} & set(types)):
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
