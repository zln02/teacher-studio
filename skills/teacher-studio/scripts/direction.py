# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Direction step helper: structure + previews so every model asks the same way. No network, no student data.

Usage:
    python3 direction.py "느낌 있게 발표자료"                  # JSON: inferred facts, open decisions, 3 pitch slots, 3 cards
    python3 direction.py "..." --html out.html [--open]        # also write ONE offline file with 3 mood preview cards
    python3 direction.py "..." --text                          # plain Korean fallback (one line per card)
    python3 direction.py "..." --prefs '{"level":"중학교","subject":"과학","device":"board"}'   # default: ~/.teacher-studio/prefs.json

The script gives structure (what is known / open / which 3 looks). The MODEL writes the three one-line pitches
(idea / mood / structure) and the questions' wording; see references/direction-step.md.
Styles come from shared/design/styles.py (found in this skill, a sibling skill or the repo); oklch.py (if present) makes the three
looks visibly distinct. Without them a built-in set of three looks is used.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import webbrowser
from pathlib import Path


def _load_workdir():
    """shared/tools/workdir.py: work folders that never need %TEMP% (an agent's security box cannot use tempfile's private folders) + the no-browser probe."""
    here = Path(__file__).resolve().parent
    for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
        if (d / "workdir.py").is_file():
            if str(d) not in sys.path:
                sys.path.append(str(d))
            import workdir as _w
            return _w
    raise ImportError("shared/tools/workdir.py not found (run tools/sync_shared.py)")


workdir = _load_workdir()

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
QUICK = ["알아서", "바로", "그냥 해", "빨리 만들", "대충"]
KINDS = {  # kind -> (words, skill/route)
    "game": (["게임", "퀴즈", "방탈출", "빙고", "보드게임", "미션", "ox", "OX", "골든벨", "짝 맞추기", "끌어서"], "teacher-game"),
    "slides": (["슬라이드", "ppt", "PPT", "피피티", "발표자료", "발표 자료", "발표", "연수 자료", "강의안", "학부모 총회", "학부모 안내"], "teacher-slides"),
    "motion": (["영상", "오프닝", "카운트다운", "시작 화면", "애니메이션", "홍보 영상", "소개 영상"], "teacher-motion"),
    "tools": (["타이머", "뽑기", "모둠 나누기", "모둠 만들", "대진표", "점수판", "자리 바꾸기"], "teacher-class-tools"),
    "data": (["엑셀", "csv", "CSV", "xlsx", "설문", "그래프", "성적 분석", "가계부", "매출"], "teacher-data"),
    "plan": (["기획", "계획", "아이디어", "운영안", "커리큘럼", "채널", "행사 준비", "조사", "리서치", "분석해", "정리해"], "co-plan"),
}
FILLER = ["느낌 있게", "느낌있게", "뭔가", "좀", "멋지게", "예쁘게", "재밌는", "재미있는", "알아서", "바로", "만들어 줘", "만들어줘",
          "해 줘", "해줘", "같이", "자료", "뭐", "거", "것", "하나", "주세요", "부탁", "우리", "내", "나", "용", "으로", "에서", "을", "를"]
VAGUE_MOOD = ["느낌", "분위기", "멋지", "예쁘", "세련", "좋게", "재밌", "재미있"]
MOODS = ["귀엽", "귀여", "차분", "신나", "신남", "발랄", "고급", "미니멀", "깔끔", "심플", "따뜻", "긴장", "네온", "레트로", "파스텔", "칠판", "자연", "화려"]
PURPOSE = ["복습", "도입", "수업 시작", "시험", "정리", "연수", "행사", "홍보", "상담", "첫 시간", "총회", "발표", "소개", "오리엔테이션", "대회", "송년", "졸업", "축하"]
AUDIENCE = ["학부모", "학생", "친구", "동료", "선생님", "가족", "아이들", "어르신", "신입", "고객", "회원"]
DEVICE_WORDS = {"board": ["칠판", "TV", "tv", "전자칠판", "빔"], "phone": ["폰", "핸드폰", "휴대폰", "스마트폰", "휴대전화", "모바일", "스마트 기기"],
                "tablet": ["태블릿", "패드", "아이패드", "갤럭시탭"], "pc": ["개인 PC", "노트북"]}
PHONE_NOT = re.compile(r"(헤드|이어|마이크|스피커|블루투스|전화기|공중전화)\s*폰|폰트|폰티")  # headphone, earphone, microphone, font (폰트) ... are not a phone
SUBJECTS = ["국어", "영어", "수학", "과학", "사회", "역사", "도덕", "음악", "미술", "체육", "기술", "정보", "한문", "실과", "통합", "전과목"]
MATERIAL = ["첨부", "학습지", "이 파일", "이 자료", "사진", "교과서", "내 양식", "양식", "로고", "pdf", "PDF", "엑셀 파일"]
LENGTH = ["분", "장", "문제", "개", "쪽", "초", "시간"]

# ko name, one-line feel for each style id (fallback copy when styles.py gives only ids)
FEEL = {
    "neon-cyber": ("먹빛 테크", "먹빛 바탕에 상아색 글씨, 하늘빛 한 줄. 차분한 긴장감"), "gold-luxury": ("먹과 놋쇠", "먹빛과 놋쇠색, 명조 제목. 품격 있는 시상식 느낌"),
    "pop-colorful": ("팝 블록", "흰 바탕에 큰 색 덩어리 둘, 굵은 글씨. 신나는 분위기"), "festival-party": ("축제 포스터", "오려 붙인 색종이 모양이 줄지어 선 포스터 느낌"),
    "tv-gameshow": ("스튜디오 쇼", "짙은 청록 무대에 호박색 한 줄, 점수판"), "glass-3d": ("소프트 뎁스", "짙은 남회색 판이 겹겹이, 차분하고 세련된 느낌"),
    "anime-cartoon": ("만화 컷", "굵은 먹선 칸과 망점, 빨강 하나"), "pastel-cute": ("파스텔", "연한 분홍과 둥근 모양, 포근함"),
    "retro-pixel": ("픽셀", "네모난 도트 화면, 오락실 느낌"), "minimal-premium": ("에디토리얼", "여백 많고 깔끔, 가는 선과 딱 한 가지 강조색"),
    "chalk-paper": ("칠판", "초록 칠판에 분필 글씨, 교실 느낌"), "nature-calm": ("자연", "연한 풀빛 종이에 짙은 초록, 마음이 편한 느낌"),
}
BUILTIN = {  # used only when styles.py cannot be found (same three looks as shared/design/styles.py)
    "minimal-premium": {"dark": False, "font": "TS Sans", "pal": {"bg1": "#f4f6f8", "text": "#161b20", "primary": "#1a2026", "accent": "#a38043", "card": "#fcfdff"}, "layout": {"poster": 4}, "keys": ["미니멀", "깔끔"]},
    "pastel-cute": {"dark": False, "font": "TS Sans", "pal": {"bg1": "#fdedf4", "text": "#1f181b", "primary": "#954074", "accent": "#65af9c", "card": "#fff6fa"}, "layout": {"bento": 4}, "keys": ["귀여", "파스텔"]},
    "neon-cyber": {"dark": True, "font": "TS Sans", "pal": {"bg1": "#11100f", "text": "#f4f0e7", "primary": "#8ac6d5", "accent": "#d7ac68", "card": "#1e1d1b"}, "layout": {"split": 4}, "keys": ["네온", "긴장"]},
}
AVOID = {"slides": {"tv-gameshow", "retro-pixel", "festival-party", "anime-cartoon"}, "data": {"tv-gameshow", "retro-pixel", "festival-party", "anime-cartoon", "neon-cyber"},
         "tools": {"gold-luxury", "glass-3d"}}  # looks that rarely suit that kind of output
SERIF = {"Noto Serif KR", "Gowun Batang", "Nanum Myeongjo"}


def _load_module(name: str):
    """Import styles.py / oklch.py from this skill, a sibling skill, or the repo (read-only). None if absent."""
    cands = [SKILL / "shared" / "design", *sorted(SKILL.parent.glob("*/shared/design")), SKILL.parent.parent / "shared" / "design"]
    for d in cands:
        f = d / f"{name}.py"
        if f.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"_ts_{name}", f)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return mod
            except Exception:
                continue
    return None


def _has(text: str, words) -> list:
    low = text.lower()
    return [w for w in words if w.lower() in low]


def infer(request: str, prefs: dict | None = None) -> dict:
    """Facts that can be read from the request + prefs. Never ask about these."""
    prefs = prefs or {}
    req = request or ""
    kinds = {k: _has(req, v[0]) for k, v in KINDS.items()}
    kinds = {k: v for k, v in kinds.items() if v}
    kind = None
    if kinds:  # the longest matched word wins; plan words lose to a concrete making word
        order = sorted(kinds, key=lambda k: (k == "plan", -max(len(w) for w in kinds[k])))
        kind = order[0]
    grade = re.search(r"(초|중|고)\s*([1-6])|([1-6])\s*학년", req)
    level = {"초": "초등학교", "중": "중학교", "고": "고등학교"}.get(grade.group(1)) if grade and grade.group(1) else None
    req_dev = PHONE_NOT.sub("", req)  # 「폰으로」 = phone (it used to be read as tablet)
    device = next((d for d, ws in DEVICE_WORDS.items() if _has(req_dev, ws)), None)
    subject = next((s for s in SUBJECTS if s in req), None)
    return {
        "kind": kind, "skill": KINDS[kind][1] if kind else None,
        "grade": grade.group(0).replace(" ", "") if grade else None,
        "level": level or prefs.get("level"), "subject": subject or prefs.get("subject"),
        "device": device or prefs.get("device"),
        "from_prefs": [k for k in ("level", "subject", "device") if prefs.get(k) and not (
            (k == "level" and level) or (k == "subject" and subject) or (k == "device" and device))],
        "quick": bool(_has(req, QUICK)),
    }


def topic_left(req: str) -> str:
    t = req
    for ws in [w for v in KINDS.values() for w in v[0]] + FILLER + SUBJECTS + [w for v in DEVICE_WORDS.values() for w in v]:
        t = re.sub(re.escape(ws), " ", t, flags=re.I)
    t = re.sub(r"(초|중|고)\s*[1-6]|[1-6]\s*학년|[^\w가-힣]+", " ", t)
    return t.strip()


def coverage(request: str, facts: dict) -> list[dict]:
    """The five decisions every direction needs. status known|open; recommended answers are defaults the model may offer."""
    req = request or ""
    purpose = _has(req, PURPOSE)
    topic = topic_left(req)
    aud = _has(req, AUDIENCE)
    mood = _has(req, MOODS)
    mat = _has(req, MATERIAL)
    length = re.search(r"\d+\s*(분|장|문제|개|쪽|초)", req)
    rows = [
        ("purpose", "무엇을 위한 것", bool(purpose or (facts["kind"] and len(topic) >= 2)), (purpose or [topic])[0] if (purpose or topic) else "",
         "어떤 때 쓰실 건가요?", ["수업 도입", "복습·정리", "행사·발표"], "수업 도입"),
        ("audience", "보는 사람", bool(aud or facts["grade"] or facts["level"] and "level" not in facts["from_prefs"]), (aud or [facts["grade"] or facts["level"] or ""])[0],
         "누가 보나요?", ["우리 반 학생", "학부모", "동료·모임"], "우리 반 학생"),
        ("mood", "분위기", bool(mood), mood[0] if mood else "", "어떤 느낌이 좋으세요?", ["차분하고 깔끔", "신나고 밝게", "고급스럽게"], "차분하고 깔끔"),
        ("material", "자료", bool(mat), mat[0] if mat else "", "참고할 파일·사진이 있나요?", ["없어요, 알아서", "있어요(올릴게요)"], "없어요, 알아서"),
        ("length", "길이·양", bool(length), length.group(0) if length else "", "분량은요?", ["짧게(5분·6장)", "보통(10분·10장)", "길게"], "짧게(5분·6장)"),
    ]
    return [{"key": k, "label": lab, "status": "known" if kn else "open", "value": val if kn else "", "question": q,
             "options": opts, "recommended": rec} for k, lab, kn, val, q, opts, rec in rows]


def is_vague(request: str, facts: dict, cov: list[dict]) -> bool:
    if facts["quick"]:
        return False
    known = {c["key"] for c in cov if c["status"] == "known"}
    if not facts["kind"]:
        return True
    if facts["kind"] == "plan":
        return len(topic_left(request)) < 4
    if "purpose" not in known:
        return True
    return len(known) < 2


def pick_styles(request: str, kind: str | None, seed: int = 0) -> list[dict]:
    """Three visibly different looks. A style named in the words comes first; the rest maximise OKLab distance, fonts and light/dark spread."""
    st = _load_module("styles")
    ok = _load_module("oklch")
    styles = dict(st.STYLES) if st and hasattr(st, "STYLES") else dict(BUILTIN)
    avoid = AVOID.get(kind or "", set())
    al = _load_module("ai_look")
    if al:  # never offer an AI-company house look (cream + clay + serif) as one of our own three looks
        avoid = avoid | {i for i, v in styles.items() if al.is_house(v["pal"].get("bg1", ""), [v["pal"].get("primary", ""), v["pal"].get("accent", "")], v.get("font", ""))}
    ids = [i for i in sorted(styles) if i not in avoid] or sorted(styles)
    h = int(hashlib.sha256((request + str(seed)).encode("utf-8")).hexdigest()[:8], 16)

    def col(sid: str):
        p = styles[sid]["pal"]
        return p.get("bg1", "#ffffff"), p.get("primary", "#000000")

    def dist(a: str, b: str) -> float:
        if ok:
            try:
                (a1, a2), (b1, b2) = col(a), col(b)
                return ok.delta_e(a1, b1) + 0.5 * ok.delta_e(a2, b2)
            except Exception:
                pass
        return 0.0 if a == b else 1.0

    named = [sid for sid in ids if any(k in request for k in styles[sid].get("keys", []))]
    chosen = [named[0]] if named else [ids[h % len(ids)]]
    while len(chosen) < 3:
        def score(s: str) -> float:
            m = min(dist(s, c) for c in chosen)
            font_bonus = 0.15 if all(styles[s].get("font") != styles[c].get("font") for c in chosen) else 0.0
            dark_bonus = 0.15 if any(styles[s].get("dark") != styles[c].get("dark") for c in chosen) else 0.0
            return m + font_bonus + dark_bonus + ((h >> (len(chosen) * 3)) % 7) * 1e-4
        chosen.append(max((s for s in ids if s not in chosen), key=score))
    return [{"id": sid, **styles[sid]} for sid in chosen]


GENERIC_KIND_WORDS = {"발표자료", "발표 자료", "발표", "슬라이드", "ppt", "PPT", "피피티", "게임", "퀴즈", "영상", "애니메이션", "그래프", "엑셀", "csv", "CSV", "xlsx"}


def sample_title(request: str, facts: dict) -> str:
    """A short title for the preview screens: the request minus filler, generic kind words (게임, 발표자료), subject, grade, device and length.
    「반 성적 분석 보고서」 stays whole, 「학부모 총회 발표자료 8장」 -> 「학부모 총회」, 「중2 과학 빛 복습 게임」 -> 「빛 복습」."""
    t = request or ""
    for ws in sorted(GENERIC_KIND_WORDS | set(FILLER) | set(SUBJECTS) | {w for v in DEVICE_WORDS.values() for w in v}, key=len, reverse=True):
        t = re.sub(r"(?<![가-힣])" + re.escape(ws) + r"(?![가-힣])" if len(ws) == 1 else re.escape(ws), " ", t, flags=re.I)
    t = re.sub(r"(초|중|고)\s*[1-6]|[1-6]\s*학년|\d+\s*(분|장|문제|개|쪽|초|시간)|[^\w가-힣]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t.replace(" ", "")) >= 2:
        return t[:14]
    return (facts.get("subject") or "오늘의 주제")[:14]


def cards(request: str, facts: dict, seed: int = 0, palette: dict | None = None) -> list[dict]:
    title = sample_title(request, facts)
    out = []
    styles3 = pick_styles(request, facts["kind"], seed)
    if palette:  # the user's own colours come first; the two other cards are looks of ours
        styles3 = styles3[:2]
    for letter, s in zip("BC" if palette else "ABC", styles3):
        pal = s["pal"]
        lay = max(s.get("layout", {"stack": 1}).items(), key=lambda kv: kv[1])[0]
        name, feel = FEEL.get(s["id"], (s["id"], ""))
        out.append({"id": letter, "style": s["id"], "name": name, "feel": feel, "dark": bool(s.get("dark")), "font": s.get("font", ""),
                    "serif": s.get("font", "") in SERIF, "layout": lay, "sample_title": title,
                    "colors": {k: pal.get(k, "") for k in ("bg1", "text", "primary", "accent", "card")}})
    return ([user_card(palette, title)] + out) if palette else out


def user_palette(arg, prefs_mod=None) -> dict:
    """The user's OWN colours: 'saved' (prefs.json) or a JSON file from color_from.py / design tokens. {} if none. Colours only."""
    cols = {}
    try:
        if arg == "saved" and prefs_mod is not None:
            cols = (prefs_mod.load_palette() or {}).get("colors", {})
        elif arg and arg != "saved":
            d = json.loads(Path(arg).read_text(encoding="utf-8"))
            cols = d.get("colors", d) if isinstance(d, dict) else {}
    except Exception:
        return {}
    return {k: v for k, v in cols.items() if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}


def user_card(cols: dict, title: str) -> dict:
    """A preview card in the user's own colours; text is re-fitted for contrast (oklch.py) when available."""
    bg = cols.get("bg1") or cols.get("bg") or "#ffffff"
    tx = cols.get("text") or cols.get("tx") or "#1a1a1a"
    ok = _load_module("oklch")
    if ok:
        try:
            if ok.contrast(tx, bg) < 4.5:
                tx = ok.fit_contrast(tx, bg, 4.5)
        except Exception:
            pass
    pr = cols.get("primary") or cols.get("pr") or tx
    return {"id": "A", "style": "own-palette", "name": "내 색", "feel": "가지고 계신 로고·양식의 색 그대로", "dark": False, "font": "TS Sans", "serif": False,
            "layout": "poster", "sample_title": title,
            "colors": {"bg1": bg, "text": tx, "primary": pr, "accent": cols.get("accent") or cols.get("ac") or pr, "card": cols.get("card") or bg}}


def pitch_slots() -> list[dict]:
    """The model fills `pitch` (one Korean line each) and marks one 추천. Three different angles, never three versions of one idea."""
    return [{"id": "A", "angle": "idea", "angle_ko": "아이디어", "pitch": "", "hint": "무엇을 만들지: 가장 쓸모 있는 한 가지"},
            {"id": "B", "angle": "mood", "angle_ko": "분위기", "pitch": "", "hint": "같은 내용을 다른 느낌으로"},
            {"id": "C", "angle": "structure", "angle_ko": "구성", "pitch": "", "hint": "다른 짜임(예: 게임 대신 짧은 영상, 장수 줄이기)"},
            ]


def text_fallback(cs: list[dict]) -> str:
    return "\n".join("%s. %s: %s (글꼴 %s, 배경 %s, 강조 %s)" % (c["id"], c["name"], c["feel"], c["font"], c["colors"]["bg1"], c["colors"]["primary"]) for c in cs)


KIND_DEVICE = {"game": "board", "slides": "tv", "data": "laptop", "tools": "board", "motion": "tv", "plan": "laptop"}
KIND_SAMPLE = {"game": "게임 시작 화면", "slides": "표지 슬라이드", "data": "보고서 첫 화면", "tools": "교실 도구 화면", "motion": "영상 첫 장면", "plan": "기획 한 장"}


def _first_frame(c: dict, kind: str | None, request: str = "", n: int = 1) -> dict:
    """What the result's first screen would show, as a storyboard frame (drawn by storyboard.mock)."""
    title = c["sample_title"]
    aud = _has(request, AUDIENCE)
    who = {"학부모": "학부모님께", "학생": "우리 반 친구들", "동료": "선생님들께", "선생님": "선생님들께", "가족": "우리 가족", "친구": "친구들과"}.get(aud[0] if aud else "", "")
    base = {"title": title, "note": "", "items": [], "value": "", "kicker": "", "tag": "", "secs": None, "char": "abcd"[n % 4]}
    if kind == "data":
        return {**base, "layout": "report", "items": ["78|평균", "96|최고", "+6|지난번보다"], "kicker": "한눈에 보기"}
    if kind == "tools":
        return {**base, "layout": "timer", "value": "05:00", "kicker": "모둠 활동"}
    if kind == "game":
        return {**base, "layout": "title", "kicker": who or "준비되면 시작!", "tag": "시작"}
    if kind == "motion":
        return {**base, "layout": "title", "kicker": "COMING UP", "note": who}
    return {**base, "layout": "title", "kicker": who or "오늘의 주제", "note": "%d학년도" % __import__("datetime").date.today().year}


def _shell_tokens(sh, c: dict):
    if c.get("style") == "own-palette":
        return sh.tokens(None, user=c["colors"], name=c.get("name", ""))
    st = _load_module("styles")
    if st and c.get("style") in getattr(st, "STYLES", {}):
        return sh.tokens(c["style"], name=c.get("name", ""))
    return sh.tokens({"id": c.get("style"), "pal": c["colors"], "font": c.get("font", ""), "dark": c.get("dark")}, name=c.get("name", ""))


def render_html(cs: list[dict], request: str, plan_line: str = "", pitches: dict | None = None, kind: str | None = None, device: str | None = None,
                embed: bool = False) -> str:
    """Three cards, each a mini first screen of the result in that look (device frame + pattern + real font + icon), the pitch line under it."""
    e = html.escape
    try:
        if str(HERE) not in sys.path:
            sys.path.insert(0, str(HERE))
        import storyboard as sb
        sh = sb._load("shell", "shell")
    except Exception:
        sb, sh = None, None
    if sh is None:
        return _render_swatches(cs, request, plan_line)
    pitches = pitches or {}
    dev = device if device in ("phone", "tablet", "tv", "board", "laptop", "a4") else KIND_DEVICE.get(kind or "", "tv")
    parts = []
    for c in cs:
        t = _shell_tokens(sh, c)
        k = c["colors"]
        screen = sh.frame(dev, sb.mock(_first_frame(c, kind, request, len(parts)), t, sh, kind or "slides", 1, 8), t)
        pitch = str(pitches.get(c["id"]) or c.get("pitch") or c["feel"])
        sw = "".join('<i style="background:%s"></i>' % e(v) for v in (k["bg1"], k["primary"], k["accent"], k["card"]))
        parts.append(
            '<section class="card" style="--c-bg:%s;--c-pr:%s;--c-ink:%s"><header><b class="id">%s</b><div><h2>%s</h2><span class="meta">%s · %s · %s</span></div></header>'
            '<div class="stage">%s</div><p class="pitch">%s</p><div class="sw">%s</div></section>' % (
                e(t["bg"]), e(t["primary"]), e(t["ink"]), e(c["id"]), e(c["name"]), e(("명조" if t["serif"] else "고딕") + " 제목"), e("어둡게" if t["dark"] else "밝게"),
                e(KIND_SAMPLE.get(kind or "", "첫 화면")), screen, e(pitch), sw))
    css = ("*{box-sizing:border-box}body{margin:0;padding:32px 24px 40px;background:#f2f4f7;color:#161b22;font-synthesis:none;word-break:keep-all;"
           "font:16px/1.5 'TS Sans','Pretendard','TS Sans','Pretendard','Noto Sans KR','Malgun Gothic',sans-serif}h1{font-size:28px;margin:0 0 4px;font-weight:760;letter-spacing:-.035em;line-height:1.2}.sub{margin:0 0 24px;color:#4a5365}"
           ".row{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}"
           ".card{background:#fff;border-radius:12px;padding:16px;border:1px solid #e1e5ea}"
           ".card header{display:flex;gap:12px;align-items:center;margin-bottom:16px}.id{flex:none;width:40px;height:40px;border-radius:8px;display:grid;place-items:center;font-size:20px;font-weight:700;"
           "background:var(--c-bg);color:var(--c-ink);box-shadow:inset 0 0 0 1.5px var(--c-pr)}h2{font-size:19px;margin:0;line-height:1.25;font-weight:700;letter-spacing:-.022em}.meta{font-size:13px;color:#566079}"
           ".stage{padding:16px 8px 8px;border-radius:8px;background:#f2f4f7}.pitch{margin:16px 0 12px;font-size:16px;font-weight:600;line-height:1.5;letter-spacing:-.012em;text-wrap:pretty}"
           ".sw{display:flex;gap:0}.sw i{width:32px;height:12px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}")
    body = ('<h1>어떤 느낌이 마음에 드세요?</h1><p class="sub">%s완성되면 첫 화면이 이렇게 보여요. 번호(A/B/C)만 말씀해 주세요. 섞어도 돼요.</p><div class="row">%s</div>'
            % (e(plan_line + " ") if plan_line else "", "".join(parts)))
    return sh.page("분위기 미리보기", body, css.replace("%%", "%") + sb.MOCK_CSS, embed=embed)


SKETCH = {  # layout -> list of (x, y, w, h) boxes on a 120x68 canvas (fallback without the shell kit)
    "split": [(6, 6, 52, 56), (64, 6, 50, 26), (64, 36, 50, 26)], "news": [(6, 6, 108, 40), (6, 50, 52, 12), (62, 50, 52, 12)],
    "poster": [(30, 8, 60, 30), (40, 44, 40, 8), (48, 56, 24, 6)], "bento": [(6, 6, 52, 30), (62, 6, 52, 14), (62, 24, 52, 12), (6, 40, 108, 22)],
    "stack": [(20, 6, 80, 16), (20, 26, 80, 16), (20, 46, 80, 16)],
}


def _render_swatches(cs: list[dict], request: str, plan_line: str = "") -> str:
    e = html.escape
    parts = []
    for c in cs:
        k = c["colors"]
        ff = ("'Noto Serif KR','Batang',serif" if c["serif"] else "'TS Sans','Pretendard','Noto Sans KR','Malgun Gothic',sans-serif")
        boxes = "".join('<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="%s" opacity="%s"/>' % (x, y, w, h, e(k["primary"] if i == 0 else k["card"]), "0.9" if i == 0 else "0.75")
                        for i, (x, y, w, h) in enumerate(SKETCH.get(c["layout"], SKETCH["stack"])))
        parts.append(
            '<section class="card" style="background:%s;color:%s"><b class="id">%s</b>'
            '<h2 style="font-family:%s;color:%s">%s</h2><p class="feel">%s</p>'
            '<svg viewBox="0 0 120 68" role="img" aria-label="%s 배치 스케치"><rect width="120" height="68" rx="6" fill="%s" stroke="%s" stroke-opacity=".3"/>%s</svg>'
            '<div class="sw">%s</div><p class="meta">%s · %s</p></section>' % (
                e(k["bg1"]), e(k["text"]), e(c["id"]), ff, e(k["text"]), e(c["sample_title"]), e(c["name"] + " · " + c["feel"]), e(c["name"]), e(k["bg1"]), e(k["text"]), boxes,
                "".join('<i style="background:%s"></i>' % e(v) for v in (k["bg1"], k["primary"], k["accent"], k["card"])), e(c["font"]), e("어둡게" if c["dark"] else "밝게")))
    return ("<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>분위기 미리보기</title><style>body{margin:0;padding:24px;background:#f4f4f4;color:#111;font:16px 'TS Sans','Pretendard','Noto Sans KR','Malgun Gothic',sans-serif}"
            "h1{font-size:20px;margin:0 0 4px}.sub{margin:0 0 16px;color:#444}.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}"
            ".card{border-radius:14px;padding:16px;position:relative;box-shadow:0 2px 8px #0003}.id{position:absolute;top:12px;right:16px;font-size:28px;opacity:.7}"
            "h2{font-size:26px;margin:8px 0 4px;line-height:1.25}.feel{margin:0 0 8px;font-size:15px;opacity:.9}svg{width:100%%;height:auto;display:block}"
            ".sw{display:flex;gap:8px;margin-top:8px}.sw i{width:26px;height:26px;border-radius:50%%;border:1px solid #8886}.meta{font-size:13px;opacity:.8;margin:8px 0 0}"
            "</style><h1>어떤 느낌이 마음에 드세요?</h1><p class=\"sub\">%s번호(A/B/C)만 말씀해 주세요. 섞어도 돼요.</p><div class=\"row\">%s</div></html>" % (
                e(plan_line + " ") if plan_line else "", "".join(parts)))


def build(request: str, prefs: dict | None = None, seed: int = 0, palette: dict | None = None) -> dict:
    facts = infer(request, prefs)
    cov = coverage(request, facts)
    vague = is_vague(request, facts, cov)
    cs = cards(request, facts, seed, palette)
    route = "co-plan" if facts["kind"] == "plan" else ("make" if facts["kind"] else "unknown")
    return {
        "request": request, "inferred": facts, "route_hint": route, "vague": vague, "quick": facts["quick"],
        "mode": "build_now" if (facts["quick"] or not vague) else "direction",
        "coverage": cov, "open": [c["key"] for c in cov if c["status"] == "open"],
        "question_budget": 0 if (facts["quick"] or not vague) else 5,
        "ask_prefs_in_same_round": not prefs,
        "own_palette": bool(palette), "pitch_slots": pitch_slots(), "cards": cs, "text_fallback": text_fallback(cs),
        "assumptions": ["%s: %s" % (c["label"], c["recommended"]) for c in cov if c["status"] == "open"],
    }


def _prefs_module():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_ts_prefs", HERE / "prefs.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def _prefs_arg(s: str | None) -> dict:
    if s:
        try:
            d = json.loads(s)
            return d if isinstance(d, dict) else {}
        except ValueError:
            return {}
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_ts_prefs", HERE / "prefs.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.load() or {}
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("request")
    ap.add_argument("--prefs", help="JSON; default ~/.teacher-studio/prefs.json")
    ap.add_argument("--html", help="write the 3 mood preview cards to this file")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--text", action="store_true", help="print only the plain-Korean card lines")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pitches", help='JSON {"A": "one line", "B": ..., "C": ...}: the pitch shown under each preview')
    ap.add_argument("--palette-from", help="'saved' (prefs.json) or a colours JSON; default: the saved palette if any. One card then shows the user's own colours")
    a = ap.parse_args()
    pal = user_palette(a.palette_from or "saved", _prefs_module())
    d = build(a.request, _prefs_arg(a.prefs), a.seed, pal)
    if a.html or a.open:
        path = Path(a.html) if a.html else workdir.named("teacher-studio-moods.html")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            pitches = json.loads(a.pitches) if a.pitches else {}
        except ValueError:
            pitches = {}
        path.write_text(render_html(d["cards"], a.request, pitches=pitches if isinstance(pitches, dict) else {}, kind=d["inferred"]["kind"],
                                    device=d["inferred"]["device"], embed=True), encoding="utf-8")
        d["preview_html"] = str(path)
        if a.open:
            webbrowser.open(path.as_uri())
    print(d["text_fallback"] if a.text else json.dumps(d, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
