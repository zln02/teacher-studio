# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Slide style language: spec words -> one of the 13 shared styles + palette + composition rules (deterministic per seed).

The 13 styles come from shared/design/styles.py (same taxonomy as games). Here each style also gets a SLIDE composition language:
title treatment, card style, emphasis style, background generator, transition and which layout families it prefers.
Palettes: the style's own palette, or (seeded) a validated shared/design palette with the same light/dark tone.
Everything derived from colours is contrast-guarded here (muted text, emphasis colour, marker tints) so the page checker never has to.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
_SHARED = SKILL / "shared" if (SKILL / "shared" / "design").exists() else SKILL.parent.parent / "shared"
sys.path.insert(0, str(_SHARED / "design"))
import design as design_core  # noqa: E402
import styles as style_core  # noqa: E402

sys.path.insert(0, str(HERE))
import deck_context as dctx  # noqa: E402

STYLES = style_core.STYLES

# ---- composition language per style --------------------------------------------------------------------------------
# font: sans | serif   tw: title weight   ls: title letter-spacing(em)   title: treatment   card: card style   em: emphasis style
# bg: background generator   trans: slide entrance   prefer: layout family weights   rad: radius px
# The slide language follows the shared style table (shared/design/styles.py: grid, type weight/tracking, radius, ornaments). No glow, no 3D title,
# no weight above 800 (system.MAX_WEIGHT); the backdrop names are the matte set drawn by deck_art.background.
LANG: dict[str, dict] = {
    "neon-cyber": dict(font="sans", tw=700, ls=-0.04, title="rule", card="hair", em="color", bg="dotgrid", trans="fade", rad=6,
                       prefer={"editorial": 4, "split": 3, "stack": 3, "bigtype": 2, "bento": 1, "poster": 1}),
    "gold-luxury": dict(font="serif", tw=600, ls=-0.02, title="serif", card="hair", em="color", bg="frame", trans="fade", rad=2,
                        prefer={"poster": 4, "editorial": 4, "split": 2, "bigtype": 1, "bento": 1, "stack": 1}),
    "pop-colorful": dict(font="sans", tw=800, ls=-0.045, title="plain", card="sticker", em="marker", bg="blocks", trans="iris", rad=20,
                         prefer={"bento": 4, "bigtype": 4, "poster": 2, "split": 2, "stack": 1, "editorial": 1}),
    "festival-party": dict(font="sans", tw=800, ls=-0.04, title="plain", card="round", em="marker", bg="papercut", trans="iris", rad=28,
                           prefer={"stack": 4, "poster": 3, "bento": 2, "bigtype": 2, "split": 1, "editorial": 1}),
    "tv-gameshow": dict(font="sans", tw=800, ls=-0.035, title="rule", card="ticket", em="color", bg="panels", trans="wipe", rad=10,
                        prefer={"split": 5, "bigtype": 3, "bento": 1, "poster": 1, "stack": 1, "editorial": 1}),
    "glass-3d": dict(font="sans", tw=700, ls=-0.035, title="plain", card="soft", em="color", bg="planes", trans="fade", rad=28,
                     prefer={"bento": 5, "split": 3, "poster": 1, "editorial": 1, "stack": 1, "bigtype": 2}),
    "anime-cartoon": dict(font="sans", tw=800, ls=-0.045, title="plain", card="sticker", em="marker", bg="halftone", trans="wipe", rad=12,
                          prefer={"split": 4, "bigtype": 4, "bento": 2, "poster": 1, "stack": 1, "editorial": 1}),
    "pastel-cute": dict(font="sans", tw=760, ls=-0.035, title="underline", card="round", em="marker", bg="hills", trans="iris", rad=40,
                        prefer={"bento": 4, "stack": 3, "center": 2, "split": 2, "poster": 1, "editorial": 1, "bigtype": 1}),
    "retro-pixel": dict(font="sans", tw=800, ls=0.02, title="pixel", card="pixel", em="color", bg="pixel", trans="wipe", rad=0,
                        prefer={"split": 3, "bento": 3, "bigtype": 2, "stack": 2, "poster": 1, "editorial": 1}),
    "minimal-premium": dict(font="sans", tw=700, ls=-0.04, title="plain", card="hair", em="underline", bg="minimal", trans="fade", rad=2,
                            prefer={"editorial": 5, "poster": 3, "split": 2, "bigtype": 2, "stack": 1, "bento": 1}),
    "chalk-paper": dict(font="sans", tw=700, ls=-0.02, title="chalk", card="chalk", em="underline", bg="chalk", trans="fade", rad=14,
                        prefer={"stack": 4, "split": 3, "editorial": 2, "bento": 1, "poster": 1, "bigtype": 1}),
    "nature-calm": dict(font="sans", tw=700, ls=-0.035, title="underline", card="flat", em="color", bg="bands", trans="fade", rad=20,
                        prefer={"editorial": 3, "stack": 3, "split": 2, "poster": 2, "bento": 1, "bigtype": 1}),
    # preset E (shared/design/preset_e.py): HUD backdrop, flat hairline cards, big tight type, fast blur-in builds (motion_e.js)
    "ink-poster": dict(font="sans", tw=800, ls=-0.055, title="plain", card="e", em="color", bg="hud", trans="fade", rad=12,
                       prefer={"bigtype": 4, "split": 4, "editorial": 3, "poster": 2, "stack": 1, "bento": 1}),
}

# slides use the style's own (already restrained) palette: the calmer slide-only copies were retired with the neon looks
SLIDE_PAL: dict[str, dict] = {}

# what each purpose naturally looks like (weights; a mood word or an explicit style beats these)
PURPOSE_STYLE = {
    "수업": {"chalk-paper": 3, "nature-calm": 3, "pop-colorful": 3, "pastel-cute": 2, "glass-3d": 3, "anime-cartoon": 2, "minimal-premium": 1, "tv-gameshow": 2, "neon-cyber": 1, "retro-pixel": 1},
    "연수": {"ink-poster": 3, "minimal-premium": 4, "glass-3d": 4, "gold-luxury": 2, "nature-calm": 2, "neon-cyber": 2, "tv-gameshow": 1, "pastel-cute": 1, "chalk-paper": 1},
    "학부모 설명회": {"pastel-cute": 4, "nature-calm": 4, "minimal-premium": 2, "festival-party": 1, "gold-luxury": 1, "glass-3d": 1, "chalk-paper": 1},
    "발표": {"ink-poster": 3, "minimal-premium": 4, "gold-luxury": 3, "glass-3d": 3, "neon-cyber": 2, "nature-calm": 1, "tv-gameshow": 1},
    "동아리": {"pop-colorful": 4, "neon-cyber": 3, "anime-cartoon": 3, "retro-pixel": 3, "festival-party": 3, "tv-gameshow": 2, "glass-3d": 2},
    "개인": {k: 1 for k in style_core.SEEDED},
}
# everyday mood words -> style weights (added on top of the purpose weights, x3)
MOOD_STYLE = {
    "따뜻": {"pastel-cute": 3, "nature-calm": 3, "chalk-paper": 1},
    "포근": {"pastel-cute": 3, "nature-calm": 3},
    "부드": {"pastel-cute": 3, "nature-calm": 2, "glass-3d": 1},
    "귀엽": {"pastel-cute": 4, "pop-colorful": 1},
    "깔끔": {"minimal-premium": 4, "glass-3d": 2, "nature-calm": 1},
    "단정": {"minimal-premium": 4, "gold-luxury": 1},
    "세련": {"minimal-premium": 3, "glass-3d": 3, "gold-luxury": 2},
    "고급": {"gold-luxury": 4, "minimal-premium": 2},
    "우아": {"gold-luxury": 3, "minimal-premium": 2, "pastel-cute": 1},
    "신나": {"pop-colorful": 3, "festival-party": 3, "anime-cartoon": 3, "tv-gameshow": 2},
    "신남": {"pop-colorful": 3, "festival-party": 3, "anime-cartoon": 3, "tv-gameshow": 2},
    "발랄": {"pop-colorful": 3, "pastel-cute": 2, "festival-party": 2},
    "힙": {"neon-cyber": 4, "retro-pixel": 3, "anime-cartoon": 2, "pop-colorful": 2, "glass-3d": 2},
    "트렌디": {"neon-cyber": 3, "glass-3d": 3, "pop-colorful": 2},
    "미래": {"neon-cyber": 4, "glass-3d": 3},
    "차분": {"nature-calm": 3, "minimal-premium": 3, "chalk-paper": 2},
    "자연": {"nature-calm": 5},
    "진지": {"minimal-premium": 2, "gold-luxury": 2, "chalk-paper": 2},
    "재미": {"pop-colorful": 2, "anime-cartoon": 2, "tv-gameshow": 2, "festival-party": 2},
    "레트로": {"retro-pixel": 5},
    "칠판": {"chalk-paper": 5},
    "강렬": {"ink-poster": 4, "pop-colorful": 1},
    "임팩트": {"ink-poster": 4},
    "또렷": {"ink-poster": 3, "minimal-premium": 2},
}
SUBJECT_STYLE = {
    "과학": {"glass-3d": 2, "nature-calm": 2, "neon-cyber": 1, "chalk-paper": 2},
    "수학": {"chalk-paper": 2, "minimal-premium": 2, "glass-3d": 1},
    "역사": {"gold-luxury": 2, "minimal-premium": 2, "chalk-paper": 1},
    "영어": {"pop-colorful": 2, "pastel-cute": 1},
    "미술": {"pop-colorful": 2, "pastel-cute": 2},
    "음악": {"neon-cyber": 1, "pop-colorful": 1, "festival-party": 1},
    "체육": {"anime-cartoon": 2, "tv-gameshow": 2, "pop-colorful": 2},
}
PURPOSES = ("수업", "연수", "학부모 설명회", "발표", "동아리", "개인")
PURPOSE_ALIAS = {"수업": "수업", "학급": "수업", "교실": "수업", "연수": "연수", "교원": "연수", "학부모": "학부모 설명회", "설명회": "학부모 설명회",
                  "발표": "발표", "강연": "발표", "동아리": "동아리", "홍보": "동아리", "모집": "동아리", "개인": "개인", "lesson": "수업", "training": "연수",
                  "parents": "학부모 설명회", "talk": "발표", "club": "동아리", "personal": "개인"}


def purpose_of(text: str) -> str:
    """Normalise a purpose word ('학부모 설명회', 'training' ...) to one of PURPOSES."""
    t = (text or "").lower()
    for k, v in PURPOSE_ALIAS.items():
        if k in t:
            return v
    return "개인" if not t else "발표"


# ---- colour helpers --------------------------------------------------------------------------------------------------
def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(c) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in c)


def mix(a: str, b: str, t: float) -> str:
    """Blend colour a toward b by t (0..1)."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def is_dark(h: str) -> bool:
    return design_core._lum(h) < 0.25


def legible(fg: str, bg: str, need: float = 4.5) -> str:
    """Move fg toward white/black (whichever the bg needs) until it reaches the contrast; returns a hex."""
    if design_core.contrast(fg, bg) >= need:
        return fg
    target = "#ffffff" if design_core._lum(bg) < 0.4 else "#000000"
    for i in range(1, 21):
        c = mix(fg, target, i / 20)
        if design_core.contrast(c, bg) >= need:
            return c
    return target


def worst_bg(colors: list[str]) -> list[str]:
    return colors


def _h(key: str) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:10], 16)


def weighted(opts: dict, key: str) -> str:
    """Seeded weighted pick (deterministic)."""
    items = sorted((k, w) for k, w in opts.items() if w > 0)
    total = sum(w for _, w in items)
    r = _h(key) % total
    for k, w in items:
        if r < w:
            return k
        r -= w
    return items[0][0]


def pick_style(purpose: str, mood: str, subject: str, seed: int, forced: str = "", avoid: list | None = None, context: str = "") -> tuple[str, str]:
    """(style id, why): an explicit design.style wins; else mood words + purpose (or the context recipe) + subject weights with a seeded pick."""
    if forced in STYLES:
        return forced, "style"
    rc = dctx.recipe(context)
    if rc.get("style"):
        return rc["style"], "context"
    w = {k: float(v) for k, v in (rc.get("styles") or PURPOSE_STYLE.get(purpose, PURPOSE_STYLE["발표"])).items()}
    why = "context" if rc else "purpose"
    words = f"{mood} {subject}"
    for key, add in MOOD_STYLE.items():
        if key in words:
            for s, v in add.items():
                w[s] = w.get(s, 0) + v * 3
            why = "mood"
    for key, add in SUBJECT_STYLE.items():
        if key in words or key in subject:
            for s, v in add.items():
                w[s] = w.get(s, 0) + v
    for sid, v in STYLES.items():  # a style's own keywords in the words ("미니멀", "네온") count strongly
        if any(k in words for k in v["keys"]):
            w[sid] = w.get(sid, 0) + 8
            why = "words"
    if rc:  # a context keeps to its own style family: mood/subject words only re-weight inside it
        w = {k: v for k, v in w.items() if k in rc["styles"]}
    for a in (avoid or []):  # styles used in the last builds are much less likely (same request -> visibly different looks)
        if a in w:
            w[a] *= 0.02
    return weighted({k: max(1, int(v * 10)) for k, v in w.items()}, f"style|{seed}|{purpose}"), why


def palette_for(style: str, mood: str, seed: int) -> tuple[dict, str]:
    """The style's own palette, or a validated shared palette of the same tone that matches the mood (seeded)."""
    own = dict(STYLES[style]["pal"])
    if style in SLIDE_PAL:  # slides want a calmer base than the game version of this style
        return dict(SLIDE_PAL[style]), style
    if style in ("minimal-premium", "chalk-paper", "retro-pixel", "tv-gameshow", "anime-cartoon", "neon-cyber", "ink-poster"):
        return own, style  # these need their signature colours
    data = design_core.load()
    mood_n = design_core.normalize_mood(mood or "", data)
    dark = bool(STYLES[style]["dark"])
    cands = []
    for name, p in data["palettes"].items():
        if "present" not in p.get("uses", []) or bool(p["dark"]) != dark or design_core.palette_issues(name, p):
            continue
        score = 3 if mood_n and mood_n in p["mood"] else 0
        cands.append((score, name, p))
    opts = {"@own": 3}
    for score, name, p in cands:
        opts[name] = 2 + score
    pick = weighted({k: v for k, v in opts.items()}, f"pal|{style}|{seed}")
    if pick == "@own":
        return own, style
    p = data["palettes"][pick]
    keys = ("bg1", "bg2", "text", "card", "cardText", "cardBorder", "primary", "btnText", "accent", "good", "bad")
    return {k: p[k] for k in keys}, pick


# ---- who is in the room, and what colour the topic has ----------------------------------------------------------------------
_OLDER = ("중학", "고등", "중1", "중2", "중3", "고1", "고2", "고3", "대학", "교사", "교원", "학부모", "직원", "성인")
_SENIOR = ("어르신", "노인", "시니어", "경로", "실버", "할머니", "할아버지", "60세", "65세", "70세", "60대", "70대", "80대")
ZOOM = {"young": 1.3, "kid": 1.2, "senior": 1.3, "": 1.0}
AUD_STYLES = {  # light, friendly structures for small children and for older eyes (a dark board or a tech look is not for them)
    "young": {"pop-colorful": 4, "festival-party": 3, "pastel-cute": 3, "nature-calm": 1},
    "kid": {"pop-colorful": 4, "pastel-cute": 2, "nature-calm": 3, "festival-party": 2, "anime-cartoon": 1},
    "senior": {"nature-calm": 4, "pop-colorful": 2, "minimal-premium": 2, "pastel-cute": 1},
}


def audience_band(spec: dict) -> str:
    """'young' (유치원 ~ 초3) | 'kid' (초4 ~ 6) | 'senior' (어르신) | '' : read from the audience / grade / title words of the spec.
    It sets how big the type starts, how round the shapes are and which looks are allowed; the content stays the author's."""
    import re
    aud = " ".join(str(spec.get(k) or "") for k in ("audience", "grade"))
    ttl = " ".join(str(spec.get(k) or "") for k in ("title", "subject"))
    lesson = dctx.context_of(spec) in ("class", "") or "수업" in str(spec.get("purpose", ""))
    for words in (aud, aud + " " + ttl):
        w = words.replace(" ", "")
        if not w:
            continue
        if any(k in w for k in _SENIOR):
            return "senior"
        if not lesson:
            continue
        if any(k in w for k in ("유치원", "어린이집", "유아", "저학년")):
            return "young"
        if any(k in w for k in _OLDER) and "초등" not in w:
            return ""
        if "초" in w or "어린이" in w:
            m = re.search(r"초(?:등학교|등)?([1-6])(?:[~\-,·]([1-6]))?(?:학년)?", w) or re.search(r"([1-6])(?:[~\-,·]([1-6]))?학년", w)
            if m:
                return "young" if int(m.group(2) or m.group(1)) <= 3 else "kid"
            return "kid"
    return ""


# topic words -> (primary hue, support hue, third hue) in OKLCH degrees: the colour people already give the thing (lava is not blue)
TOPIC_HUES = (
    (("화산", "용암", "마그마", "불", "화재", "소방", "연소"), (38, 78, 255)),
    (("지진", "지층", "암석", "화석", "흙", "사막", "공룡"), (58, 30, 200)),
    (("바다", "해양", "강", "물", "수영", "비", "날씨", "구름", "하늘", "얼음", "겨울", "눈"), (245, 195, 70)),
    (("식물", "숲", "나무", "잎", "광합성", "자연", "환경", "생태", "텃밭", "봄", "새싹", "기후", "재활용"), (150, 100, 40)),
    (("우주", "태양계", "행성", "별", "달", "밤", "천문"), (275, 85, 200)),
    (("빛", "전기", "에너지", "여름", "태양"), (255, 80, 30)),
    (("경제", "시장", "금융", "소비", "무역", "용돈", "저축", "창업", "매출", "돈"), (200, 65, 25)),
    (("음악", "합창", "노래", "악기", "공연", "연극", "축제", "예술", "미술"), (320, 75, 200)),
    (("마음", "감정", "사랑", "가족", "친구", "우정", "인권", "배려", "복지", "건강", "보건"), (20, 195, 90)),
    (("스마트폰", "디지털", "인공지능", "코딩", "컴퓨터", "정보", "데이터", "미디어", "인터넷", "로봇"), (255, 190, 55)),
    (("안전", "교통", "재난", "예방"), (65, 250, 25)),
    (("역사", "전통", "문화유산", "한옥", "조선", "고려", "삼국", "독립"), (30, 230, 90)),
    (("빵", "음식", "요리", "급식", "카페", "가을", "수확"), (55, 150, 20)),
    (("동물", "곤충", "새", "반려"), (75, 150, 250)),
    (("등산", "산행", "산", "캠핑", "여행", "체험", "진로"), (160, 60, 240)),
    (("수학", "도형", "분수", "덧셈", "뺄셈", "곱셈", "나눗셈", "계산"), (265, 55, 165)),
    (("국어", "독서", "책", "글쓰기", "한글", "받아쓰기", "문학", "광고", "설득"), (25, 215, 95)),
    (("영어", "외국어", "세계", "지구", "나라", "지리"), (225, 150, 50)),
    (("체육", "운동", "스포츠", "달리기", "축구"), (30, 250, 145)),
)
_ONE = {"불", "강", "물", "비", "눈", "숲", "잎", "봄", "별", "달", "밤", "빛", "돈", "빵", "새", "산", "책"}


def topic_hues(spec: dict):
    """(primary, support, third) hues for the deck's topic, or None when the title names nothing with a colour of its own."""
    import re
    t = " ".join(str(spec.get(k) or "") for k in ("title", "subject"))
    best = None
    for words, hues in TOPIC_HUES:
        for w in words:
            i = t.find(w)
            if w in _ONE:  # one-syllable words must stand alone (산 in 생산, 비 in 준비)
                m = re.search(r"(?<![가-힣])" + re.escape(w) + r"(?![가-힣])|(?<![가-힣])" + re.escape(w) + r"(?=[은는이가을를과와의에도])", t)
                i = m.start() if m else -1
            if i >= 0 and (best is None or (i, -len(w)) < best[:2]):
                best = (i, -len(w), hues)
    return best[2] if best else None


def topic_palette(hues, dark: bool, seed: int, aud: str = "") -> dict:
    """A design-system palette (shared/design/system.py: tinted neutral ramp + one primary + one support) in the topic's hues."""
    import system as system_core
    hp, hs, _ = hues
    v = _h(f"tp|{seed}") % 3  # paper: near white / lightly tinted / a shade deeper (same hue family, never a second hue)
    if dark:
        return system_core.palette("dark", hp, (0.80, 0.11, hp), (0.80, 0.10, hs), bg_l=(0.19, 0.21, 0.23)[v], bg_c=0.022)
    soft = aud in ("young", "kid")
    return system_core.palette("light", hp, (0.56 if soft else 0.50, 0.15, hp), (0.66 if soft else 0.62, 0.14, hs),
                               bg_l=(0.985, 0.972, 0.962)[v], bg_c=(0.006, 0.014, 0.02)[v] * (1.4 if soft else 1.0))


# A young room (유치원 ~ 초3) reads colour before words: crayon-box primaries, each clearly its own hue, on warm white paper.
# Bright and saturated but never fluorescent (system.is_neon stays False: L <= 0.70 with C < 0.165, or L <= 0.60 with C < 0.215).
YOUNG_HUES = (28, 150, 245, 300, 5, 75, 200)   # tomato, leaf, sky, grape, strawberry, sunflower, sea: where a deck without a topic colour starts


def _crayon(h: float) -> tuple:
    """(L, C, h) of a crayon-bright colour in this hue. Yellows carry their colour only when light, blues only when deeper."""
    h %= 360
    if 55 <= h <= 115:
        return (0.70, 0.150, h)
    if 115 < h <= 200:
        return (0.62, 0.160, h)
    if 200 < h <= 290:
        return (0.58, 0.180, h)
    return (0.60, 0.200, h)


def young_palette(hues, seed: int) -> tuple[dict, tuple]:
    """Palette for small children: the topic's hue when it has one (else a seeded crayon), two more crayons a third of the wheel away.
    Returns (palette, (primary, support, third) hues). Every colour passes system.is_neon; the text pairs are contrast-fitted by system.palette."""
    import oklch
    import system as system_core
    if hues:
        hp = hues[0]
    else:
        hp = YOUNG_HUES[_h(f"yh|{seed}") % len(YOUNG_HUES)]
    if 50 <= hp % 360 <= 115:
        hp = 40  # a yellow that carries white words is mustard: the main colour becomes tangerine, yellow stays a marker
    turn = (120, -120)[_h(f"yt|{seed}") % 2]
    hs, h3 = (hp + turn) % 360, (hp - turn) % 360
    v = _h(f"tp|{seed}") % 3
    prim = oklch.hex_to_oklch(oklch.fit_contrast(oklch.oklch_to_hex(*_crayon(hp)), "#ffffff", 4.6))  # white words on the main colour, as on a crayon label
    pal = system_core.palette("light", 80, prim, _crayon(hs), bg_l=(0.99, 0.982, 0.975)[v], bg_c=(0.008, 0.014, 0.02)[v])
    for k in ("primary", "accent"):  # belt and braces: a colour the fitter pushed into the fluorescent corner comes back down
        L, C, h = oklch.hex_to_oklch(pal[k])
        while system_core.is_neon(pal[k]) and C > 0.08:
            C -= 0.01
            pal[k] = oklch.oklch_to_hex(L, C, h)
    return pal, (hp, hs, h3)


def third_tone(pr: str, ac: str, bg1: str, dark: bool, hue=None, calm: bool = False, vivid: bool = False) -> str:
    """A third marker colour, far in hue from both the primary and the support (rule 13: at most three accent hues on a screen)."""
    import oklch
    hp, ha = oklch.hex_to_oklch(pr)[2], oklch.hex_to_oklch(ac)[2]
    if hue is None:
        cands = [(hp + 180) % 360, (ha + 180) % 360, (hp + 100) % 360, (hp - 100) % 360, ((hp + ha) / 2 + 180) % 360]
        hue = max(cands, key=lambda h: min(oklch.hue_distance(h, hp), oklch.hue_distance(h, ha)))
    if vivid:  # a young room's third crayon
        import system as system_core
        L, C, h = _crayon(hue)
        c = oklch.fit_contrast(oklch.oklch_to_hex(L, C, h), bg1, 2.2)
        while system_core.is_neon(c) and C > 0.08:
            C -= 0.01
            c = oklch.fit_contrast(oklch.oklch_to_hex(L, C, h), bg1, 2.2)
        return c
    c = oklch.oklch_to_hex(0.80 if dark else 0.55, 0.095 if calm else (0.10 if dark else 0.12), hue % 360)
    return oklch.fit_contrast(c, bg1, 3.0)


def tones_of(pr: str, ac: str, t3: str, bg1: str, card: str) -> list:
    """The colours a slide may fill a badge, a card head or a band with, the primary first. A support colour too close to the page
    or to the primary (a navy and its own lighter step) is left out: two near-equal blues are one colour to the eye."""
    import oklch
    out = [pr]
    for c in (ac, t3):
        if min(design_core.contrast(c, bg1), design_core.contrast(c, card)) < 1.9:
            c = oklch.fit_contrast(c, [bg1, card], 2.4)
        if all(oklch.delta_e(c, o) >= 0.11 for o in out):
            out.append(c)
    return out


def resolve(spec: dict, seed: int, avoid: list | None = None) -> dict:
    """Design object used by every layout: style, language, colours (+ guarded derived colours), floors, fonts."""
    d = spec.get("design") or {}
    purpose = purpose_of(spec.get("purpose", ""))
    context = dctx.context_of(spec)
    rc = dctx.recipe(context)
    mood = " ".join(spec.get("mood") if isinstance(spec.get("mood"), list) else [str(spec.get("mood", ""))])
    if rc and not mood.strip():
        mood = rc["mood"]
    words = " ".join([mood, str(spec.get("title", ""))])
    aud = audience_band(spec)
    if aud and context != "public" and str(d.get("style", "")) not in STYLES:
        opts = {k: v * 10 for k, v in AUD_STYLES[aud].items() if k not in (avoid or [])} or {k: v * 10 for k, v in AUD_STYLES[aud].items()}
        style, why = weighted(opts, f"aud|{seed}|{aud}"), "audience"
    else:
        style, why = pick_style(purpose, words, str(spec.get("subject", "")), seed, str(d.get("style", "")), avoid, context)
    lang = dict(LANG[style])
    pal, pal_name = palette_for(style, mood, seed)
    hues = topic_hues(spec) if context != "public" and not d.get("style") and style != "ink-poster" else None  # preset E keeps its one vermilion
    if hues:  # the topic has a colour of its own: the deck takes it (the structure still comes from the style)
        pal, pal_name = topic_palette(hues, bool(STYLES[style]["dark"]), seed, aud), "topic"
    yh = None
    if aud == "young" and context != "public" and not d.get("style") and not STYLES[style]["dark"]:
        # 유치원 ~ 초3: crayon-box colours whatever the style's own palette is (the structure still comes from the style, the hue from the topic or the seed)
        pal, yh = young_palette(hues, seed)
        pal_name = "young-topic" if hues else "young"
    if aud in ("young", "kid"):
        lang["rad"] = max(lang["rad"], 28)
    if rc.get("palettes") and not d.get("style"):  # public: restrained navy/slate/teal, seeded
        pal_name = weighted({k: 1 for k in rc["palettes"]}, f"gov|{seed}")
        pal = dict(dctx.PUBLIC_PALETTES[pal_name])
        lang.update(em="color", card="hair", rad=4, bg="minimal", trans="fade", tw=800)
    if rc:
        fam = rc.get("family") or {}
        lang["prefer"] = {k: max(1, round(v * fam.get(k, 1.0))) for k, v in lang["prefer"].items()}
    if d.get("palette_from"):  # the user's own colours (logo / template): they replace the style's palette; the style's composition stays
        pal, pal_name = design_core.load_user_palette(d["palette_from"]), "user"
    bg1, bg2, tx = pal["bg1"], pal["bg2"], pal["text"]
    dark = is_dark(bg1)
    # restraint: bg + text + muted + ONE accent. The card is a quiet tint of the background (never a second colour), text on it is the normal text colour.
    card = mix(bg1, "#ffffff", 0.08) if dark else mix(bg1, "#ffffff", 0.7)
    ct = tx
    pr = legible(pal["primary"], bg1, 3.0) if design_core.contrast(pal["primary"], bg1) < 3 else pal["primary"]
    ac = pal["accent"]
    # text colours that must pass 4.5:1 on BOTH the slide background and the card
    emc = legible(pr, bg1, 5.6)
    emc = emc if design_core.contrast(emc, bg2) >= 5.6 else legible(emc, bg2, 5.6)
    emcc = legible(pr, card, 4.5)
    emc2 = emcc
    mu = mix(tx, bg1, 0.14)
    mu = mu if min(design_core.contrast(mu, bg1), design_core.contrast(mu, bg2)) >= 4.5 else legible(mu, bg2, 4.5)
    cmu = mix(ct, card, 0.25)
    cmu = cmu if design_core.contrast(cmu, card) >= 4.5 else legible(cmu, card, 4.5)
    hl = mix(bg1, pr, 0.30)  # marker tint: tx must stay >= 4.5 on it, else lighten
    if design_core.contrast(tx, hl) < 4.5:
        hl = mix(bg1, pr, 0.16)
    hl_card = mix(card, pr, 0.28)
    if design_core.contrast(ct, hl_card) < 4.5:
        hl_card = mix(card, pr, 0.14)
    # meaning colours: blue vs orange keep apart for colour-blind eyes (checked with shared/design/color_check.py); the layouts also say it in words (정답/오답)
    purpose_floor = 24 if purpose == "개인" else 28
    if rc:
        purpose_floor = rc["floor"]
    user_pal = bool(d.get("palette_from"))
    if user_pal:
        yh = None
    t3 = third_tone(pr, ac, bg1, dark, yh[2] if yh else (hues[2] if hues else None), calm=context == "public", vivid=bool(yh))
    tones = tones_of(pr, ac, t3, bg1, card)
    if context == "public" and len(tones) == 3:  # a report keeps one navy and marks with one other hue; the navy's own lighter step comes last
        tones = [tones[0], tones[2], tones[1]]
    if user_pal:  # the user's colours are used as given: nothing we derived is added to them
        tones = [c for c in tones if c != t3] or [pr]
    return {
        "style": style, "why": why, "purpose": purpose, "palette": pal_name, "seed": seed, "lang": lang, "dark": dark,
        "colors": {"t3": t3, "bg1": bg1, "bg2": bg2, "tx": tx, "mu": mu, "card": card, "ct": ct, "cmu": cmu, "cb": mix(tx, bg1, 0.82), "line": mix(tx, bg1, 0.84), "pr": pr, "bt": pal["btnText"],
                   "ac": ac, "good": "#6ea8ff" if dark else "#1d4ed8", "bad": "#ffb454" if dark else "#c2410c", "emc": emc, "emcc": emcc, "emc2": emc2, "hl": hl, "hlc": hl_card,
                   "ink": "#1a1a1a" if not dark else "#f5f5f5"},
        "fonts": {"display": "Noto Serif KR" if lang["font"] == "serif" else "TS Sans", "body": "TS Sans"},
        "floor": purpose_floor, "motion": STYLES[style]["motion"],
        "context": context, "tscale": dict(rc.get("tscale") or {}), "allowed": dict(rc.get("allowed") or {}),
        "audience": aud, "zoom": ZOOM[aud], "tones": tones, "topic": bool(hues), "crayon": bool(yh),
    }


def contrast_report(dz: dict) -> list[str]:
    """Contrast problems of the resolved design (empty = fine); used by the build and by tests."""
    c, out = dz["colors"], []
    for fg, bg, need in (("tx", "bg1", 4.5), ("tx", "bg2", 4.5), ("mu", "bg1", 4.5), ("mu", "bg2", 4.5), ("ct", "card", 4.5), ("cmu", "card", 4.5),
                         ("emc", "bg1", 4.5), ("emcc", "card", 4.5), ("tx", "hl", 4.5), ("ct", "hlc", 4.5), ("bt", "pr", 4.5)):
        r = design_core.contrast(c[fg], c[bg])
        if r < need:
            out.append(f"{fg} on {bg} = {r:.2f} (< {need})")
    return out


if __name__ == "__main__":
    import json
    for purpose, mood in (("학부모 설명회", "따뜻하게"), ("연수", "깔끔하게"), ("수업", "신나게"), ("동아리", "힙하게")):
        for sd in range(4):
            dz = resolve({"purpose": purpose, "mood": mood}, sd)
            print(purpose, mood, sd, dz["style"], dz["palette"], contrast_report(dz))
    bad = []
    for s in STYLES:
        for sd in range(12):
            dz = resolve({"purpose": "개인", "mood": "", "design": {"style": s}}, sd)
            bad += [f"{s}/{sd}/{dz['palette']}: {x}" for x in contrast_report(dz)]
    print(json.dumps(bad[:20], ensure_ascii=False, indent=0))
