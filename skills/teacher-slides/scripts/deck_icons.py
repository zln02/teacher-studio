# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Icons picked by meaning, for the web deck and the .pptx alike (Lucide, ISC / MIT: shared/vendor/lucide/LICENSE).

    pick("카카오톡으로 사진 보내기")  -> "message-circle"     (None when no word on the line has a clear picture)
    name("전화")                     -> "phone"              (a Korean word or a Lucide name -> a Lucide name that exists, else None)
    outline("phone")                 -> [(filled, [("M", x, y), ("L", x, y), ("C", x1, y1, x2, y2, x, y), ("Z",)]), ...] on the 24 x 24 grid

The web deck shows an icon as `<svg><use href="#lucide-NAME"/></svg>` (shared/vendor/inline.py adds the symbols used); the .pptx
draws the same outline as one editable freeform (deck_pptx.py), so nothing is a picture and the colour follows the deck.
An icon is drawn only where the words name something: a line with no match keeps its number or dot. Never decoration for its own sake.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
_V = SKILL / "shared" / "vendor" / "lucide"
if not _V.exists():
    _V = SKILL.parent.parent / "shared" / "vendor" / "lucide"

# Meaning -> Lucide name. Longer, more specific words first within a line: the first match in the TEXT (leftmost) wins, ties go to the longer word.
WORDS = {
    # 통신·기기
    "카카오톡": "message-circle", "카톡": "message-circle", "메신저": "message-circle", "대화": "messages-square", "토론": "messages-square", "토의": "messages-square",
    "문자": "message-square-text", "댓글": "message-square-text", "영상통화": "video", "화상": "video", "전화": "phone", "통화": "phone", "연락": "phone",
    "스마트폰": "smartphone", "휴대폰": "smartphone", "핸드폰": "smartphone", "앱": "layout-grid", "키오스크": "monitor-smartphone", "태블릿": "tablet",
    "컴퓨터": "monitor", "노트북": "laptop", "인터넷": "globe", "검색": "search", "와이파이": "wifi", "이메일": "mail", "메일": "mail", "편지": "mail",
    "사진": "camera", "카메라": "camera", "촬영": "camera", "영상": "clapperboard", "동영상": "clapperboard", "유튜브": "play", "방송": "tv", "뉴스": "newspaper",
    "신문": "newspaper", "광고": "megaphone", "홍보": "megaphone", "알림": "bell", "공지": "megaphone", "안내": "info", "인공지능": "bot", "로봇": "bot",
    "코딩": "code", "프로그램": "app-window", "데이터": "database", "비밀번호": "key-round", "보안": "shield-check", "개인정보": "lock",
    # 돈·경제
    "결제": "credit-card", "카드": "credit-card", "은행": "landmark", "저축": "piggy-bank", "용돈": "piggy-bank", "예산": "wallet", "지갑": "wallet",
    "가격": "tag", "할인": "badge-percent", "수강료": "banknote", "무료": "gift", "비용": "banknote", "매출": "trending-up", "수익": "trending-up",
    "이익": "trending-up", "돈": "banknote", "소비": "shopping-cart", "쇼핑": "shopping-cart", "구매": "shopping-bag", "시장": "store", "가게": "store",
    "매장": "store", "기업": "building-2", "회사": "building-2", "생산": "factory", "공장": "factory", "무역": "ship", "수요": "trending-down",
    "공급": "trending-up", "선택": "git-fork", "기회비용": "scale", "비교": "scale", "균형": "scale", "세금": "receipt", "계약": "file-signature",
    # 사람·관계
    "어르신": "heart-handshake", "가족": "users", "손주": "baby", "아기": "baby", "친구": "users", "모둠": "users", "팀": "users", "함께": "users",
    "학부모": "heart-handshake", "선생님": "graduation-cap", "교사": "graduation-cap", "강사": "presentation", "학생": "backpack", "주민": "users",
    "단원": "users", "회원": "users", "신입": "user-plus", "모집": "user-plus", "신청": "clipboard-pen", "접수": "clipboard-pen", "등록": "clipboard-pen",
    "협력": "handshake", "도움": "hand-helping", "도와": "hand-helping", "봉사": "hand-heart", "나눔": "hand-heart", "배려": "hand-heart", "존중": "hand-heart",
    "사랑": "heart", "마음": "heart", "감사": "heart", "칭찬": "thumbs-up", "응원": "thumbs-up", "약속": "handshake", "규칙": "list-checks",
    "상담": "messages-square", "면담": "messages-square", "인사": "hand", "자기소개": "id-card", "이름": "id-card",
    # 학교·공부
    "학습 목표": "target", "목표": "target", "수업": "presentation", "교실": "school", "학교": "school", "교과서": "book-open", "책": "book-open",
    "독서": "book-open", "읽기": "book-open", "쓰기": "pencil", "글쓰기": "pencil", "받아쓰기": "pencil", "일기": "notebook-pen", "공책": "notebook-pen",
    "필기": "notebook-pen", "숙제": "clipboard-list", "과제": "clipboard-list", "준비물": "backpack", "시험": "file-check", "평가": "clipboard-check",
    "퀴즈": "circle-help", "문제": "circle-help", "질문": "circle-help", "궁금": "circle-help", "정답": "circle-check", "확인": "circle-check",
    "정리": "list-checks", "복습": "repeat", "반복": "repeat", "연습": "repeat", "발표": "mic", "말하기": "mic", "듣기": "ear", "생각": "lightbulb",
    "아이디어": "lightbulb", "까닭": "lightbulb", "이유": "lightbulb", "핵심": "key-round", "중요": "star", "주의": "triangle-alert", "조심": "triangle-alert",
    "위험": "triangle-alert", "금지": "ban", "수료": "award", "상장": "award", "우승": "trophy", "대회": "trophy", "성과": "trophy", "성장": "sprout",
    "활동": "puzzle", "놀이": "puzzle", "게임": "gamepad-2", "만들기": "scissors", "그리기": "palette", "색칠": "palette", "미술": "palette",
    "노래": "music", "음악": "music", "합창": "music", "악보": "music", "악기": "piano", "연주": "piano", "공연": "ticket", "무대": "theater",
    "체육": "volleyball", "운동": "dumbbell", "달리기": "footprints", "걷기": "footprints", "산책": "footprints", "줄넘기": "activity", "수영": "waves",
    "축구": "volleyball", "춤": "music-2", "영어": "languages", "외국어": "languages", "한글": "type", "낱말": "whole-word", "문장": "text", "설득": "megaphone",
    "수학": "calculator", "계산": "calculator", "덧셈": "plus", "뺄셈": "minus", "곱셈": "x", "나눗셈": "divide", "분수": "pie-chart", "도형": "shapes",
    "세모": "triangle", "네모": "square", "동그라미": "circle", "길이": "ruler", "무게": "weight", "시계": "clock", "시각": "clock", "그래프": "bar-chart-3",
    "통계": "bar-chart-3", "표": "table", "설문": "clipboard-list", "만족도": "smile", "조사": "search", "관찰": "eye", "탐구": "microscope",
    "실험": "flask-conical", "과학": "flask-conical", "현미경": "microscope", "돋보기": "search", "자석": "magnet", "전기": "zap", "전구": "lightbulb",
    "에너지": "zap", "빛": "sun", "그림자": "sun-dim", "소리": "volume-2", "온도": "thermometer", "열": "flame", "불": "flame", "화재": "flame",
    # 자연·지구
    "화산": "mountain", "용암": "flame", "마그마": "flame", "지진": "activity", "지층": "layers", "암석": "gem", "돌": "gem", "흙": "shovel", "산": "mountain",
    "등산": "mountain", "산행": "mountain", "바다": "waves", "강": "waves", "물": "droplet", "비": "cloud-rain", "구름": "cloud", "눈": "snowflake",
    "날씨": "cloud-sun", "바람": "wind", "태양": "sun", "해": "sun", "달": "moon", "별": "star", "우주": "rocket", "지구": "earth", "행성": "orbit",
    "계절": "calendar-days", "봄": "flower-2", "여름": "sun", "가을": "leaf", "겨울": "snowflake", "식물": "sprout", "씨앗": "sprout", "새싹": "sprout",
    "꽃": "flower-2", "나무": "tree-deciduous", "숲": "trees", "잎": "leaf", "열매": "apple", "과일": "apple", "채소": "carrot", "동물": "paw-print",
    "강아지": "dog", "고양이": "cat", "새": "bird", "물고기": "fish", "곤충": "bug", "나비": "bug", "환경": "recycle", "재활용": "recycle",
    "분리배출": "recycle", "쓰레기": "trash-2", "기후": "thermometer-sun", "탄소": "cloud", "자연": "trees",
    # 생활·안전·건강
    "안전": "shield-check", "예방": "shield-check", "보호": "shield", "대피": "door-open", "출구": "door-open", "계단": "footprints", "엘리베이터": "arrow-up-down",
    "소화기": "fire-extinguisher", "신고": "siren", "응급": "siren", "병원": "hospital", "약": "pill", "건강": "heart-pulse", "손 씻기": "hand",
    "양치": "smile", "급식": "utensils", "식사": "utensils", "간식": "cookie", "음식": "utensils", "요리": "chef-hat", "빵": "croissant", "커피": "coffee",
    "잠": "bed", "휴식": "armchair", "집": "house", "가정": "house", "마을": "map", "동네": "map", "지도": "map", "길 찾기": "map-pin", "장소": "map-pin",
    "위치": "map-pin", "오시는 길": "map-pin", "버스": "bus", "지하철": "train-front", "기차": "train-front", "자동차": "car", "자전거": "bike",
    "비행기": "plane", "여행": "plane", "교통": "traffic-cone", "횡단보도": "traffic-cone", "신호등": "traffic-cone",
    # 일정·행사·행정
    "일정": "calendar-days", "날짜": "calendar-days", "기간": "calendar-range", "요일": "calendar-days", "시간": "clock", "마감": "alarm-clock",
    "선착순": "alarm-clock", "대상": "users", "인원": "users", "정원": "users", "축제": "party-popper", "행사": "party-popper", "축하": "party-popper",
    "잔치": "party-popper", "생일": "cake", "선물": "gift", "송년": "party-popper", "모임": "users", "회의": "presentation", "보고": "file-text",
    "문서": "file-text", "서류": "file-text", "민원": "file-text", "계획": "list-todo", "추진": "rocket", "운영": "settings", "개선": "wrench",
    "과제 해결": "wrench", "결과": "flag", "실적": "bar-chart-3", "현황": "bar-chart-3", "증가": "trending-up", "감소": "trending-down", "참여": "hand",
    "투표": "vote", "선거": "vote", "법": "scale", "권리": "scale", "역사": "landmark", "문화유산": "landmark", "박물관": "landmark", "전통": "landmark",
    "세계": "globe", "나라": "flag", "태극기": "flag", "진로": "compass", "직업": "briefcase", "꿈": "sparkles", "체험": "tent", "캠프": "tent",
    "도서관": "library", "주민센터": "building", "기관": "building", "구청": "building", "시청": "building",
}
# picture words that are often part of another word: only as a whole word (산 in 생산, 비 in 준비, 눈 in 눈높이, 해 in 이해 ...)
_WHOLE = {"산", "강", "물", "비", "눈", "해", "달", "별", "불", "열", "돌", "흙", "봄", "잎", "꽃", "새", "약", "잠", "집", "빛", "춤", "책", "표", "법", "꿈", "팀", "앱", "돈", "빵"}
_JOSA = "은는이가을를과와의에도로만"

_sprite: dict | None = None
_cache: dict = {}


def _load() -> dict:
    """name -> inner markup of its <symbol> (parsed once)."""
    global _sprite
    if _sprite is None:
        _sprite = {}
        f = next(iter(sorted(_V.glob("lucide-*-sprite.svg"))), None) if _V.exists() else None
        if f:
            for m in re.finditer(r'<symbol id="([a-z0-9-]+)"[^>]*>(.*?)</symbol>', f.read_text(encoding="utf-8"), re.S):
                _sprite[m.group(1)] = m.group(2)
    return _sprite


def exists(n: str) -> bool:
    return bool(n) and n in _load()


def name(word) -> str | None:
    """A Korean word or a Lucide name -> a Lucide name in the vendored set, or None."""
    w = str(word or "").strip()
    if not w:
        return None
    lw = w.lower()
    if re.fullmatch(r"[a-z0-9-]+", lw):
        return lw if exists(lw) else None
    return pick(w)


def pick(text, default: str | None = None) -> str | None:
    """The icon for the thing a line names: the leftmost picture word wins (a longer word beats a shorter one at the same place)."""
    t = re.sub(r"\*\*", "", str(text or ""))
    best = None
    for k, v in WORDS.items():
        i = t.find(k)
        while i >= 0 and k in _WHOLE:  # a one-syllable word must stand alone (a particle may follow)
            before = t[i - 1] if i > 0 else " "
            after = t[i + len(k)] if i + len(k) < len(t) else " "
            if not ("가" <= before <= "힣") and (not ("가" <= after <= "힣") or after in _JOSA):
                break
            i = t.find(k, i + 1)
        if i < 0:
            continue
        cand = (i, -len(k), v)
        if best is None or cand < best:
            best = cand
    if best and exists(best[2]):
        return best[2]
    return default if (default and exists(default)) else None


def pick_all(texts, explicit=None) -> list:
    """One icon per line, or [] when the lines do not all have their own picture (a half-illustrated list looks unfinished).
    explicit: names / words the author gave (same length); they win line by line."""
    explicit = list(explicit or [])
    out = []
    for i, t in enumerate(texts):
        n = name(explicit[i]) if i < len(explicit) and explicit[i] else None
        out.append(n or pick(t))
    if any(x is None for x in out) or len(set(out)) < len(out):  # the same picture twice says nothing: numbers are clearer
        return []
    return out


# ---- outlines --------------------------------------------------------------------------------------------------------
_NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def _arc(x0, y0, rx, ry, phi, large, sweep, x, y):
    """SVG elliptical arc -> cubic Bezier segments [(x1, y1, x2, y2, x, y)]."""
    if rx == 0 or ry == 0 or (x0 == x and y0 == y):
        return [(x0, y0, x, y, x, y)]
    rx, ry = abs(rx), abs(ry)
    ph = math.radians(phi)
    cp, sp = math.cos(ph), math.sin(ph)
    dx, dy = (x0 - x) / 2, (y0 - y) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx, cy = cp * cxp - sp * cyp + (x0 + x) / 2, sp * cxp + cp * cyp + (y0 + y) / 2

    def ang(ux, uy, vx, vy):
        d = math.hypot(ux, uy) * math.hypot(vx, vy)
        a = math.acos(max(-1.0, min(1.0, (ux * vx + uy * vy) / d))) if d else 0.0
        return -a if ux * vy - uy * vx < 0 else a
    th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi
    n = max(1, int(math.ceil(abs(dth) / (math.pi / 2) - 1e-9)))
    seg = dth / n
    k = 4 / 3 * math.tan(seg / 4)
    out = []
    for i in range(n):
        a0, a1 = th1 + i * seg, th1 + (i + 1) * seg
        c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
        p1 = (c0 - k * s0, s0 + k * c0)
        p2 = (c1 + k * s1, s1 - k * c1)

        def tr(px, py):
            return (cp * rx * px - sp * ry * py + cx, sp * rx * px + cp * ry * py + cy)
        out.append((*tr(*p1), *tr(*p2), *tr(c1, s1)))
    return out


def _path(d: str) -> list:
    """SVG path data -> absolute M / L / C / Z commands."""
    out = []
    i, cmd, n_d = 0, "", len(d)
    x = y = sx = sy = 0.0
    px = py = None  # last control point (for S / T)
    prev = ""
    # scanned in place: arc flags may be written without a separator ("a2 2 0 012 2")

    def skip():
        nonlocal i
        while i < n_d and (d[i].isspace() or d[i] == ","):
            i += 1

    def num():
        nonlocal i
        skip()
        m = _NUM.match(d, i)
        if not m:
            raise ValueError("number expected")
        i = m.end()
        return float(m.group())

    def flag():
        nonlocal i
        skip()
        v = d[i]
        i += 1
        return float(v)

    def nums(n):
        if n == 7:
            return [num(), num(), num(), flag(), flag(), num(), num()]
        return [num() for _ in range(n)]
    while True:
        skip()
        if i >= n_d:
            break
        if d[i].isalpha():
            cmd = d[i]
            i += 1
            if cmd in "Zz":
                out.append(("Z",))
                x, y = sx, sy
                prev = "Z"
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            a, b = nums(2)
            x, y = (x + a, y + b) if rel else (a, b)
            sx, sy = x, y
            out.append(("M", x, y))
            cmd = "l" if rel else "L"  # further pairs are line-tos
        elif c == "L":
            a, b = nums(2)
            x, y = (x + a, y + b) if rel else (a, b)
            out.append(("L", x, y))
        elif c == "H":
            a, = nums(1)
            x = x + a if rel else a
            out.append(("L", x, y))
        elif c == "V":
            a, = nums(1)
            y = y + a if rel else a
            out.append(("L", x, y))
        elif c in "CS":
            if c == "C":
                x1, y1, x2, y2, a, b = nums(6)
                if rel:
                    x1, y1, x2, y2, a, b = x + x1, y + y1, x + x2, y + y2, x + a, y + b
            else:
                x2, y2, a, b = nums(4)
                if rel:
                    x2, y2, a, b = x + x2, y + y2, x + a, y + b
                x1, y1 = (2 * x - px, 2 * y - py) if prev in "CS" and px is not None else (x, y)
            out.append(("C", x1, y1, x2, y2, a, b))
            px, py, x, y = x2, y2, a, b
        elif c in "QT":
            if c == "Q":
                qx, qy, a, b = nums(4)
                if rel:
                    qx, qy, a, b = x + qx, y + qy, x + a, y + b
            else:
                a, b = nums(2)
                if rel:
                    a, b = x + a, y + b
                qx, qy = (2 * x - px, 2 * y - py) if prev in "QT" and px is not None else (x, y)
            out.append(("C", x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y), a + 2 / 3 * (qx - a), b + 2 / 3 * (qy - b), a, b))
            px, py, x, y = qx, qy, a, b
        elif c == "A":
            rx, ry, phi, large, sweep, a, b = nums(7)
            if rel:
                a, b = x + a, y + b
            for sg in _arc(x, y, rx, ry, phi, bool(large), bool(sweep), a, b):
                out.append(("C", *sg))
            x, y = a, b
        else:  # unknown: stop rather than draw rubbish
            break
        prev = c
    return out


def _ellipse(cx, cy, rx, ry) -> list:
    k = 0.5522847498
    return [("M", cx + rx, cy), ("C", cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry), ("C", cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy),
            ("C", cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry), ("C", cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy), ("Z",)]


def outline(n: str) -> list:
    """[(filled, commands)] for a Lucide icon on its 24 x 24 grid; [] when the name is not in the set."""
    if n in _cache:
        return _cache[n]
    src = _load().get(n)
    for _ in range(3):  # an alias symbol points at the real one: <use href="#other"/>
        m_ = re.search(r'<use href="#([a-z0-9-]+)"', src or "")
        if not m_:
            break
        src = _load().get(m_.group(1))
    out = []
    if src:
        for m in re.finditer(r"<(path|circle|ellipse|rect|line|polyline|polygon)\b([^>]*?)/?>", src):
            tag = m.group(1)
            a = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(2)))
            f = lambda k, d=0.0: float(a.get(k, d))  # noqa: E731
            filled = a.get("fill") == "currentColor"
            if tag == "path":
                cm = _path(a.get("d", ""))
            elif tag == "circle":
                cm = _ellipse(f("cx"), f("cy"), f("r"), f("r"))
            elif tag == "ellipse":
                cm = _ellipse(f("cx"), f("cy"), f("rx"), f("ry"))
            elif tag == "line":
                cm = [("M", f("x1"), f("y1")), ("L", f("x2"), f("y2"))]
            elif tag in ("polyline", "polygon"):
                v = [float(t) for t in _NUM.findall(a.get("points", ""))]
                pts = list(zip(v[0::2], v[1::2]))
                cm = [("M", *pts[0])] + [("L", *p) for p in pts[1:]] + ([("Z",)] if tag == "polygon" else []) if pts else []
            else:  # rect, with rounded corners
                x0, y0, w, h = f("x"), f("y"), f("width"), f("height")
                rx = min(f("rx", a.get("ry", 0)), w / 2)
                ry = min(f("ry", a.get("rx", 0)), h / 2)
                if rx <= 0 or ry <= 0:
                    cm = [("M", x0, y0), ("L", x0 + w, y0), ("L", x0 + w, y0 + h), ("L", x0, y0 + h), ("Z",)]
                else:
                    cm = _path(f"M{x0 + rx} {y0}h{w - 2 * rx}a{rx} {ry} 0 0 1 {rx} {ry}v{h - 2 * ry}a{rx} {ry} 0 0 1 {-rx} {ry}h{-(w - 2 * rx)}"
                               f"a{rx} {ry} 0 0 1 {-rx} {-ry}v{-(h - 2 * ry)}a{rx} {ry} 0 0 1 {rx} {-ry}z")
            if cm:
                out.append((filled, cm))
    _cache[n] = out
    return out


def svg_path(n: str) -> str:
    """The outline as one SVG path string (tests and previews)."""
    d = []
    for _, cm in outline(n):
        for c in cm:
            d.append(c[0] + " ".join(f"{v:.2f}" for v in c[1:]))
    return "".join(d)


if __name__ == "__main__":
    import sys
    bad = sorted({v for v in WORDS.values() if not exists(v)})
    print("icons in the set:", len(_load()), "| words:", len(WORDS), "| names not in the set:", bad)
    for w in sys.argv[1:]:
        print(w, "->", pick(w))
