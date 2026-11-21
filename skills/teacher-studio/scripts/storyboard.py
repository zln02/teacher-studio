# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Storyboard (콘티) sheet: every frame drawn as a small mock screen in the chosen style (real colours, real font, icons, buttons,
charts, a device frame and the style's background pattern), so the teacher sees 「완성되면 이렇게 보이겠구나」. One offline HTML + a
plain-text fallback. No network, no student data, no <script>.

Usage:
    python3 storyboard.py spec.json [--html sheet.html [--open]] [--text] [--palette-from saved|FILE] [--title T]
                                    [--style STYLE_ID] [--device tv|board|laptop|tablet|phone|a4]

Reads, WITHOUT changing them: a teacher-slides deck spec ({"slides":[...]}), a teacher-game spec ({"mechanic","items"}),
a shot list ({"shots":[{"title","seconds","narration"}]}), and the generic {"frames":[{"title","note","layout","items"}]}.
Anything else with a top-level list of dicts falls back to a generic frame list.
Look: the user's own palette (saved / --palette-from / spec design.palette_from) first; else spec design.style / --style; else a style picked from
the spec's words (shared/design/styles.py), never the AI-company house look (shared/design/ai_look.py). Pieces come from shared/shell (shell kit).
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
sys.path.insert(0, str(HERE))

# known layouts (rectangles kept for the no-shell fallback). kind: h heading, t text, b block, a accent
SKETCH = {
    "title": [(10, 34, 80, 14, "h"), (10, 54, 50, 6, "t")],
    "section": [(10, 40, 60, 14, "h")],
    "statement": [(10, 30, 80, 10, "h"), (10, 46, 70, 10, "h"), (10, 66, 40, 6, "t")],
    "bullets": [(8, 10, 50, 10, "h"), (8, 34, 70, 6, "t"), (8, 48, 60, 6, "t"), (8, 62, 66, 6, "t")],
    "compare": [(8, 10, 50, 10, "h"), (8, 30, 40, 52, "b"), (52, 30, 40, 52, "b")],
    "steps": [(8, 10, 50, 10, "h"), (8, 40, 20, 36, "b"), (32, 40, 20, 36, "b"), (56, 40, 20, 36, "b"), (80, 40, 14, 36, "b")],
    "bignumber": [(20, 24, 60, 34, "a"), (30, 68, 40, 6, "t")],
    "quote": [(12, 28, 76, 10, "h"), (12, 44, 60, 10, "h"), (12, 66, 30, 6, "t")],
    "illustration": [(8, 10, 40, 10, "h"), (8, 34, 40, 6, "t"), (56, 16, 36, 62, "a")],
    "quiz": [(8, 8, 84, 16, "h"), (8, 34, 40, 18, "b"), (52, 34, 40, 18, "b"), (8, 58, 40, 18, "b"), (52, 58, 40, 18, "b")],
    "timeline": [(8, 10, 50, 10, "h"), (8, 52, 84, 3, "a"), (14, 44, 8, 18, "b"), (44, 44, 8, 18, "b"), (74, 44, 8, 18, "b")],
    "chart": [(8, 10, 50, 10, "h"), (12, 54, 10, 28, "b"), (28, 40, 10, 42, "a"), (44, 48, 10, 34, "b"), (60, 28, 10, 54, "b")],
    "math": [(8, 10, 50, 10, "h"), (20, 40, 60, 16, "a")],
    "timer": [(30, 24, 40, 30, "a"), (35, 64, 30, 8, "b")],
    "qr": [(8, 12, 50, 10, "h"), (56, 20, 30, 56, "a")],
    "image": [(8, 8, 84, 70, "a"), (8, 84, 50, 6, "t")],
    "video": [(8, 8, 84, 70, "a"), (8, 84, 50, 6, "t")],
    "closing": [(14, 36, 72, 14, "h"), (14, 58, 40, 6, "t")],
    "grid": [(8 + 21 * c, 14 + 26 * r, 18, 22, "b") for r in range(3) for c in range(4)],
    "bins": [(8, 12, 84, 12, "h"), (8, 44, 24, 38, "b"), (38, 44, 24, 38, "b"), (68, 44, 24, 38, "b")],
    "locks": [(8, 10, 60, 10, "h"), (8, 40, 14, 26, "a"), (26, 40, 14, 26, "a"), (44, 40, 14, 26, "b"), (62, 40, 14, 26, "b")],
    "shot": [(6, 8, 88, 62, "a"), (6, 78, 70, 8, "t")],
    "list": [(8, 12, 50, 10, "h"), (8, 34, 70, 6, "t"), (8, 48, 60, 6, "t"), (8, 62, 66, 6, "t")],
}
ALIAS = {"intro": "title", "cover": "title", "outro": "closing", "end": "closing", "result": "bignumber", "bignumbers": "bignumber", "kpi": "chart",
         "report": "chart", "play": "quiz", "rules": "bullets", "flow": "steps", "screen": "list", "wireframe": "list", "full": "image", "shots": "shot",
         "scene": "shot", "table": "list"}
GAME_PLAY = {"quiz": "quiz", "survival": "quiz", "escape": "locks", "match": "grid", "bingo": "grid", "board": "steps", "sort": "bins"}
GAME_PLAY_KO = {"quiz": "문제가 크게 나오고 보기를 고른다", "survival": "OX 문제, 틀린 팀은 목숨이 줄어든다", "escape": "문제를 풀면 자물쇠가 하나씩 열린다",
                "match": "카드를 뒤집어 짝을 맞춘다", "bingo": "낱말 칸을 채워 줄을 만든다", "board": "주사위로 말을 움직이고 칸의 문제를 푼다", "sort": "항목을 알맞은 통에 끌어 넣는다"}
GAME_JUICE = {"quiz": "정답 순간 꽃가루, 오답은 짧은 흔들림, 마지막 문제 긴장 음",
              "survival": "탈락할 때 화면 흔들림, 마지막 생존 팀 꽃가루",
              "escape": "자물쇠가 열리는 소리와 빛, 남은 시간 10초 경고",
              "match": "짝이 맞으면 반짝, 마지막 짝에서 꽃가루",
              "bingo": "줄이 완성될 때 BINGO 글자 튀어나오기",
              "board": "말이 칸을 지날 때 통통, 도착 칸 꽃가루",
              "sort": "맞으면 쏙 들어가는 소리, 틀리면 튕겨 나오기"}
# fallback colours when nothing else is known: cool paper + ink blue (not cream + clay: see shared/design/ai_look.py)
DEFAULT = {"bg": "#f3f6fb", "ink": "#172033", "frame": "#ffffff", "line": "#c5cedc", "accent": "#2f5bea", "soft": "#e3eafc", "muted": "#5b6474"}
KIND_STYLES = {"slides": {"nature-calm": 3, "pastel-cute": 2, "glass-3d": 2, "minimal-premium": 2, "chalk-paper": 2, "pop-colorful": 1, "studio-clean": 2},
               "data": {"studio-clean": 4, "glass-3d": 2, "nature-calm": 2, "minimal-premium": 1}}
AVOID = {"slides": {"tv-gameshow", "retro-pixel", "festival-party", "anime-cartoon"},
         "data": {"tv-gameshow", "retro-pixel", "festival-party", "anime-cartoon", "neon-cyber", "pop-colorful"}}


def _s(v, n=120) -> str:
    return re.sub(r"\s+", " ", str(v if v is not None else "")).replace("**", "").strip()[:n]


def _layout(name: str) -> str:
    name = _s(name, 40).split(".")[0].lower()
    name = ALIAS.get(name, name)
    return name if name in SKETCH else "list"


def _frame(title, layout, note="", secs=None, tag="", items=None, value="", kicker="") -> dict:
    its = [_s(x, 40) for x in (items or []) if _s(x, 40)][:6]
    return {"title": _s(title, 60), "layout": _layout(layout), "note": _s(note, 160), "secs": secs, "tag": _s(tag, 20),
            "items": its, "value": _s(value, 12), "kicker": _s(kicker, 30)}


def _label(x) -> str:
    if isinstance(x, dict):
        return _s(x.get("title") or x.get("text") or x.get("label") or x.get("caption") or x.get("word") or x.get("q") or "", 40)
    return _s(x, 40)


def slide_note(sl: dict) -> str:
    keys = ("sub", "subtitle", "text", "caption", "takeaway", "meta")
    parts = [_s(sl.get(k), 70) for k in keys if sl.get(k)]
    for k in ("items", "steps", "events", "choices"):
        v = sl.get(k)
        if isinstance(v, list) and v:
            first = v[0]
            first = (first.get("title") or first.get("text") or first.get("label")) if isinstance(first, dict) else first
            parts.append("%d개: %s…" % (len(v), _s(first, 24)))
    if sl.get("value"):
        parts.append("%s%s" % (sl.get("value"), sl.get("unit", "")))
    if sl.get("note"):
        parts.append("발표 메모 있음")
    return " · ".join(p for p in parts if p)[:160]


def _slide_items(sl: dict) -> list:
    for k in ("items", "steps", "events", "choices", "next", "labels"):
        v = sl.get(k)
        if isinstance(v, list) and v:
            if k == "items" and isinstance(v[0], dict) and "value" in v[0]:
                return ["%s%s|%s" % (_s(x.get("value"), 8), _s(x.get("unit"), 4), _s(x.get("caption"), 24)) for x in v if isinstance(x, dict)]
            return [_label(x) for x in v]
    if isinstance(sl.get("a"), dict) and isinstance(sl.get("b"), dict):
        return [_label(sl["a"]), _label(sl["b"])]
    if isinstance(sl.get("series"), list) and sl["series"] and isinstance(sl["series"][0], dict):
        return [str(x) for x in (sl["series"][0].get("data") or [])][:6]
    return []


def frames_from_slides(d: dict) -> list:
    out = []
    for sl in d.get("slides", []):
        if not isinstance(sl, dict):
            continue
        t = sl.get("type", "bullets")
        title = sl.get("title") or sl.get("text") or sl.get("q") or sl.get("tex") or (str(sl.get("value", "")) + str(sl.get("unit", "")))
        val = (str(sl.get("value", "")) + str(sl.get("unit", ""))) if sl.get("value") not in (None, "") else ("%s분" % sl["minutes"] if sl.get("minutes") else "")
        out.append(_frame(title, sl.get("layout") or t, slide_note(sl), tag=t, items=_slide_items(sl), value=val, kicker=sl.get("kicker") or sl.get("subtitle") or ""))
    return out


def frames_from_game(d: dict) -> list:
    mech = d.get("mechanic", "quiz")
    items = d.get("items") if isinstance(d.get("items"), list) else []
    title = d.get("title") or "게임"
    qs = []
    for it in items[:3]:
        if isinstance(it, dict):
            qs.append(_s(it.get("q") or it.get("word") or it.get("a"), 30))
    first = next((it for it in items if isinstance(it, dict)), {})
    choices = [_label(c) for c in (first.get("choices") or [])] if isinstance(first.get("choices"), list) else []
    if not choices:
        choices = [_label(it.get("word") or it.get("a") or it.get("q")) for it in items[:8] if isinstance(it, dict)]
    ans = ""
    if isinstance(first.get("answer"), int) and isinstance(first.get("choices"), list) and 0 <= first["answer"] < len(first["choices"]):
        ans = _label(first["choices"][first["answer"]])
    teams = d.get("teams") or 0
    secs = d.get("seconds")
    has_exp = any(isinstance(i, dict) and i.get("exp") for i in items)
    rules = ["방식: " + GAME_PLAY_KO.get(mech, "문제를 풀며 진행"), ("%d팀 대결" % teams) if teams else "모두 함께", ("제한 %s초" % secs) if secs else "문제 %d개" % len(items)]
    frames = [
        _frame(title, "title", _s(d.get("subtitle")) or "제목 화면: 시작 버튼 하나", tag="시작", kicker=_s(d.get("subtitle"), 30)),
        _frame("규칙 한 장", "bullets", "방식: %s · %s%s" % (mech, ("%d팀 · " % teams) if teams else "", ("제한 %s초" % secs) if secs else "문제 %d개" % len(items)), tag="규칙", items=rules),
        _frame("진행 화면", GAME_PLAY.get(mech, "quiz"), GAME_PLAY_KO.get(mech, "문제를 풀며 진행한다") + ((" · 예: " + " / ".join(qs)) if qs else ""), tag="진행",
               items=choices, kicker=_s(first.get("q") or first.get("word") or "", 60)),
        _frame("정답 공개", "bignumber", "정답과 한 줄 설명 (" + ("설명 있음" if has_exp else "설명 없음") + ") · 손맛: " + GAME_JUICE.get(mech, "정답 순간 작은 연출"), tag="공개",
               value=ans or "정답", kicker=_s(first.get("exp"), 50)),
        _frame("이기면", "closing", "순위·점수, 박수와 꽃가루", tag="승리", items=["1등 모둠", "2등 모둠", "3등 모둠"]),
        _frame("지면 / 시간 끝", "closing", "아깝다 화면 + 틀린 문제만 다시 풀기", tag="패배"),
    ]
    return frames


def frames_from_shots(d: dict) -> list:
    shots = d.get("shots") or d.get("scenes") or []
    out = []
    for i, s in enumerate(shots, 1):
        if not isinstance(s, dict):
            continue
        sec = s.get("seconds") or s.get("sec") or s.get("duration")
        try:
            sec = float(sec)
        except (TypeError, ValueError):
            sec = None
        note = " · ".join(x for x in (_s(s.get("narration") or s.get("caption"), 80), ("움직임: " + _s(s.get("motion"), 30)) if s.get("motion") else "") if x)
        out.append(_frame(s.get("title") or "컷 %d" % i, s.get("layout") or "shot", note, secs=sec, tag="컷"))
    return out


def frames_generic(d: dict) -> list:
    fr = d.get("frames")
    if not isinstance(fr, list):
        fr = None
        for v in d.values():  # first top-level list of dicts
            if isinstance(v, list) and v and isinstance(v[0], dict):
                fr = v
                break
    out = []
    for i, f in enumerate(fr or [], 1):
        if isinstance(f, dict):
            sec = f.get("seconds")
            out.append(_frame(f.get("title") or f.get("name") or "장면 %d" % i, f.get("layout") or "list", f.get("note") or f.get("text") or "",
                              secs=sec if isinstance(sec, (int, float)) else None, items=f.get("items") if isinstance(f.get("items"), list) else None,
                              value=f.get("value") or "", kicker=f.get("kicker") or "", tag=f.get("tag") or ""))
        else:
            out.append(_frame(f, "list"))
    return out


def frames_from_spec(d) -> list:
    if not isinstance(d, dict):
        return []
    if isinstance(d.get("frames"), list):
        return frames_generic(d)
    if isinstance(d.get("slides"), list):
        return frames_from_slides(d)
    if "mechanic" in d:
        return frames_from_game(d)
    if isinstance(d.get("shots"), list) or isinstance(d.get("scenes"), list):
        return frames_from_shots(d)
    return frames_generic(d)


def sheet_title(d, override=None) -> str:
    return _s(override or (d.get("title") if isinstance(d, dict) else "") or "콘티", 60)


def total_secs(frames: list):
    v = [f["secs"] for f in frames if isinstance(f.get("secs"), (int, float))]
    return sum(v) if v else None


def render_text(frames: list, title: str) -> str:
    lines = ["콘티: " + title]
    for i, f in enumerate(frames, 1):
        sec = (" (%g초)" % f["secs"]) if f.get("secs") else ""
        lines.append("%d. [%s] %s%s" % (i, f["layout"], f["title"], sec) + ((" - " + f["note"]) if f["note"] else ""))
    t = total_secs(frames)
    if t:
        lines.append("합계 %g초" % t)
    return "\n".join(lines)


# ------------------------------------------------------------------ look ----------------------------------------------------------------
def _load(name: str, sub: str = "design"):
    """Import a shared module (design/styles.py, shell/shell.py ...) from this skill, a sibling skill or the repo. None if absent."""
    cands = [SKILL / "shared" / sub, *sorted(SKILL.parent.glob("*/shared/" + sub)), SKILL.parent.parent / "shared" / sub]
    for d in cands:
        f = d / f"{name}.py"
        if f.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"_sb_{sub}_{name}", f)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return mod
            except Exception:
                continue
    return None


def palette(arg=None) -> dict:
    """Own palette if saved/given, else calm defaults. Text is re-fitted for contrast when oklch is available. `_own` marks the user's colours."""
    tok = dict(DEFAULT)
    try:
        import direction
        cols = direction.user_palette(arg or "saved", direction._prefs_module())
        if cols:
            tok["bg"] = cols.get("bg1") or cols.get("bg") or tok["bg"]
            tok["ink"] = cols.get("text") or tok["ink"]
            tok["accent"] = cols.get("primary") or cols.get("accent") or tok["accent"]
            tok["frame"] = cols.get("card") or tok["frame"]
            if cols.get("accent"):
                tok["accent2"] = cols["accent"]
            ok = direction._load_module("oklch")
            if ok and ok.contrast(tok["ink"], tok["bg"]) < 4.5:
                tok["ink"] = ok.fit_contrast(tok["ink"], tok["bg"], 4.5)
            if re.fullmatch(r"#[0-9a-fA-F]{6}", tok["accent"]):
                tok["soft"] = tok["accent"] + "33"
            tok["_own"] = True
    except Exception:
        pass
    return tok


def kind_of(d) -> str:
    if not isinstance(d, dict):
        return "generic"
    if "mechanic" in d:
        return "game"
    if isinstance(d.get("slides"), list):
        return "slides"
    if isinstance(d.get("shots"), list) or isinstance(d.get("scenes"), list):
        return "motion"
    k = str(d.get("kind") or d.get("type") or "")
    return k if k in ("data", "slides", "game", "motion", "tools") else "generic"


def choose_style(d, forced: str = "", kind: str = "") -> str:
    """design.style / --style first; else style words in the spec; else a seeded pick that suits the kind. Never the AI house look."""
    st = _load("styles")
    if not st:
        return ""
    des = d.get("design") if isinstance(d, dict) and isinstance(d.get("design"), dict) else {}
    forced = forced or str(des.get("style") or (d.get("style") if isinstance(d, dict) else "") or "")
    if forced in st.STYLES:
        return forced
    words = des.get("words") if isinstance(des.get("words"), list) else [str(des.get("words") or "")]
    mood = d.get("mood") if isinstance(d, dict) else ""
    mood = " ".join(mood) if isinstance(mood, list) else str(mood or des.get("mood") or "")
    priority = " ".join([*map(str, words), mood])
    text = " ".join(str(d.get(k, "")) for k in ("title", "subtitle", "subject", "purpose", "audience")) if isinstance(d, dict) else ""
    seed = int(des.get("seed") or 0) if str(des.get("seed") or "0").isdigit() else 0
    avoid = AVOID.get(kind, set())
    al = _load("ai_look")
    hits = st._hits(priority) or st._hits(text)
    if not hits and kind in KIND_STYLES:  # no style words: a seeded pick among looks that suit this kind of output
        opts = sorted(KIND_STYLES[kind].items())
        r = int(hashlib.sha256(("%s|%s|%d" % (kind, text, seed)).encode("utf-8")).hexdigest()[:8], 16) % sum(w for _, w in opts)
        for sid, w in opts:
            if r < w:
                return "" if sid == "studio-clean" else sid
            r -= w
    for s in range(seed, seed + 24):
        sid, why = st.pick_style(text, "generic", s, "", priority=priority)
        if why in ("words", "title") and sid not in avoid:
            break
        if sid in avoid:
            continue
        p = st.STYLES[sid]["pal"]
        if al and al.is_house(p.get("bg1", ""), [p.get("primary", ""), p.get("accent", "")], st.STYLES[sid].get("font", "")):
            continue
        break
    return sid


def device_for(d, kind: str, forced: str = "") -> str:
    if forced in ("phone", "tablet", "tv", "board", "laptop", "a4"):
        return forced
    dev = str(d.get("device", "")) if isinstance(d, dict) else ""
    if dev in ("phone", "tablet"):
        return dev
    if kind == "game" or dev == "board":
        return "board"
    if kind == "data":
        return "laptop"
    return "tv"


# --------------------------------------------------------------- mock screens -----------------------------------------------------------
E = html.escape


def _clip(s: str, n: int) -> str:
    s = _s(s, 200)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _bar_values(f: dict) -> list[float]:
    vals = []
    for x in f.get("items") or []:
        m = re.match(r"\s*(-?\d+(?:\.\d+)?)", str(x))
        if m:
            vals.append(float(m.group(1)))
    return vals if len(vals) >= 2 else [42, 68, 55, 86, 74]


def mock(f: dict, t: dict, sh, kind: str, n: int, total: int) -> str:
    """Inner HTML of one mock screen. Every text goes through E()."""
    lay, ttl, note, items = f["layout"], f["title"], f["note"], f.get("items") or []
    ic = sh.icon_for(ttl + " " + note + " " + " ".join(items), salt=str(n))
    kick = f.get("kicker") or ""
    pg = '<span class="m-pg">%d / %d</span>' % (n, total) if kind == "slides" else ""
    chip = '<span class="sk-badge">%s</span>' % E(_clip(kick, 22)) if kick else ""
    h = lambda txt, cls="m-t2": sh.title(_clip(txt, 34), t, cls)  # noqa: E731
    if lay == "title":
        cta = sh.button("게임 시작", t) if kind == "game" else (sh.button("시작", t) if kind in ("motion", "tools") else "")
        art = sh.character(f.get("char") or "abcd"[n % 4], 90) if kind == "game" else sh.spot(ic, t, 120)
        sub = '<p class="m-sub">%s</p>' % E(_clip(note, 44)) if note and (not kick or kind != "game") else ""
        hud = ('<div class="m-hud m-top"><span class="sk-badge">%s 모둠 대결</span><span class="sk-badge sk-badge-solid">%s 0</span></div>'
               % (sh.icon("users", 12), sh.icon("star", 12))) if kind == "game" else ""
        rule = '<i class="m-rule"></i>' if kind == "slides" and t.get("fx") != "serif" else ""
        return ('<div class="m m-cover">%s<div class="m-art">%s</div><div class="m-col">%s%s%s%s<div class="m-cta">%s</div></div>%s'
                '<i class="m-deco m-deco1"></i><i class="m-deco m-deco2"></i></div>' % (hud, art, chip, h(ttl, "m-t1"), rule, sub, cta, pg))
    if lay == "report":
        nums = [x.split("|", 1) for x in items if "|" in x][:3]
        tiles = "".join('<div class="m-kpi sm"><b>%s</b><span>%s</span></div>' % (E(_clip(v, 6)), E(_clip(c, 10))) for v, c in nums)
        bars = "".join('<i style="height:%d%%"%s></i>' % (v, ' class="hi"' if v == 88 else "") for v in (46, 62, 54, 88, 70, 58))
        return ('<div class="m m-report"><div class="m-hud">%s<span class="sk-badge">%s 이름 없음</span></div>%s<div class="m-chartrow"><div class="m-kcol">%s</div>'
                '<div class="m-bars">%s</div></div></div>' % (chip, sh.icon("shield", 12), h(ttl), tiles, bars))
    if lay == "section":
        return '<div class="m m-sec"><span class="m-big">%02d</span><div class="m-col">%s%s</div>%s</div>' % (n, chip, h(ttl, "m-t1"), pg)
    if lay in ("statement", "quote"):
        q = '<span class="m-q">&ldquo;</span>' if lay == "quote" else sh.spot(ic, t, 70)
        return '<div class="m m-stmt">%s%s%s<p class="m-sub">%s</p>%s</div>' % (q, chip, h(ttl, "m-t1"), E(_clip(note, 50)), pg)
    if lay in ("bullets", "list"):
        lis = items or [x for x in re.split(r"\s*·\s*", note) if x][:3] or ["첫째", "둘째", "셋째"]
        rows = "".join('<li>%s<span>%s</span></li>' % (sh.icon("check", 14, "var(--sk-op)", 3, "m-tick"), E(_clip(x, 26))) for x in lis[:4])
        return '<div class="m m-list"><div class="m-col">%s%s<ul>%s</ul></div><div class="m-side">%s</div>%s</div>' % (chip, h(ttl), rows, sh.spot(ic, t, 110), pg)
    if lay == "compare":
        a, b = (items + ["A", "B"])[:2]
        card = lambda lab, icn, k: '<div class="m-card m-cmp-%s">%s<b>%s</b><i class="m-line"></i><i class="m-line s"></i></div>' % (k, sh.icon(icn, 22, "var(--sk-pr)" if k == "a" else "var(--sk-ac)", 2), E(_clip(lab, 14)))  # noqa: E731
        return '<div class="m m-cmp">%s%s<div class="m-two">%s<span class="m-vs">VS</span>%s</div>%s</div>' % (chip, h(ttl), card(a, sh.icon_for(a, "a"), "a"), card(b, sh.icon_for(b, "b"), "b"), pg)
    if lay in ("steps", "timeline"):
        lis = (items or ["시작", "탐구", "정리", "발표"])[:4]
        dots = "".join('<li><span class="m-dot">%d</span><b>%s</b></li>' % (i + 1, E(_clip(x, 9))) for i, x in enumerate(lis))
        return '<div class="m m-steps">%s%s<ol class="m-track">%s</ol>%s</div>' % (chip, h(ttl), dots, pg)
    if lay == "bignumber":
        if kind == "game":
            return ('<div class="m m-reveal"><div class="m-ok">%s</div><div class="m-col"><span class="sk-badge sk-badge-solid">정답</span>%s<p class="m-sub">%s</p></div>'
                    '<i class="m-burst"></i></div>' % (sh.icon("circle-check", 64, "var(--sk-gd)", 2.2), h(f.get("value") or ttl, "m-t1"), E(_clip(kick or note, 40))))
        nums = [x.split("|", 1) for x in items if "|" in x][:3]
        if nums:
            tiles = "".join('<div class="m-kpi"><b>%s</b><span>%s</span></div>' % (E(_clip(v, 7)), E(_clip(c, 14))) for v, c in nums)
            return '<div class="m m-kpis">%s%s<div class="m-row3">%s</div>%s</div>' % (chip, h(ttl), tiles, pg)
        return '<div class="m m-bign"><b class="m-num">%s</b><p class="m-sub">%s</p>%s</div>' % (E(_clip(f.get("value") or ttl, 8)), E(_clip(note, 40)), pg)
    if lay == "quiz":
        q = kick or ttl
        ch = (items or ["보기 1", "보기 2", "보기 3", "보기 4"])[:4]
        btns = "".join('<span class="m-ans"><i>%s</i>%s</span>' % ("ABCD"[i], E(_clip(x, 12))) for i, x in enumerate(ch))
        hud = ('<div class="m-hud"><span class="sk-badge">%s 문제 1</span><span class="sk-badge">%s 0:20</span><span class="sk-badge sk-badge-solid">%s 120</span></div>'
               % (sh.icon("question-mark", 12), sh.icon("stopwatch", 12), sh.icon("star", 12)))
        return '<div class="m m-quiz">%s<div class="m-qcard">%s</div><div class="m-grid2">%s</div></div>' % (hud, E(_clip(q, 44)), btns)
    if lay == "chart":
        vals = _bar_values(f)
        mx = max(vals) or 1
        bars = "".join('<i style="height:%d%%"%s></i>' % (max(8, round(v / mx * 100)), ' class="hi"' if v == mx else "") for v in vals[:6])
        kp = '<div class="m-kpi sm"><b>%s</b><span>최고</span></div><div class="m-kpi sm"><b>%s</b><span>평균</span></div>' % (E("%g" % mx), E("%.0f" % (sum(vals) / len(vals))))
        return '<div class="m m-chart">%s%s<div class="m-chartrow"><div class="m-bars">%s</div><div class="m-kcol">%s</div></div>%s</div>' % (chip, h(ttl), bars, kp, pg)
    if lay == "math":
        return '<div class="m m-math">%s%s<div class="m-formula">%s</div>%s</div>' % (chip, h(ttl), E(_clip(note or "a² + b² = c²", 30)), pg)
    if lay == "timer":
        return ('<div class="m m-timer"><div class="m-ring"><b>%s</b></div><div class="m-col">%s%s<div class="m-cta">%s %s</div></div></div>'
                % (E(_clip(f.get("value") or "05:00", 6)), chip, h(ttl), sh.button("시작", t), sh.button("멈춤", t, False)))
    if lay == "qr":
        return '<div class="m m-qr"><div class="m-col">%s%s<p class="m-sub">%s</p></div><div class="m-code"></div>%s</div>' % (chip, h(ttl), E(_clip(note, 30)), pg)
    if lay in ("image", "video", "shot", "illustration"):
        mic = "player-play" if lay in ("video", "shot") else "photo"
        return ('<div class="m m-media"><div class="m-ph">%s<span class="m-play">%s</span></div><div class="m-cap">%s<b>%s</b></div></div>'
                % (sh.spot(ic, t, 110), sh.icon(mic, 18, "var(--sk-op)", 2.2), chip, E(_clip(ttl, 26))))
    if lay == "grid":
        tiles = []
        for i in range(12):
            if i in (1, 6, 9) and items:
                tiles.append('<span class="m-tile up">%s</span>' % E(_clip(items[i % len(items)], 6)))
            elif i in (3, 10):
                tiles.append('<span class="m-tile up ic">%s</span>' % sh.icon(sh.icon_for(ttl, str(i)), 18, "var(--sk-pr)"))
            else:
                tiles.append('<span class="m-tile">?</span>')
        return '<div class="m m-gridw"><div class="m-hud"><span class="sk-badge">짝 2 / 6</span><span class="sk-badge sk-badge-solid">0:45</span></div><div class="m-tiles">%s</div></div>' % "".join(tiles)
    if lay == "bins":
        lab = (items or ["종이", "플라스틱", "캔"])[:3]
        bins = "".join('<div class="m-bin">%s<b>%s</b></div>' % (sh.icon(sh.icon_for(x, str(i)), 20, "var(--sk-pr)"), E(_clip(x, 6))) for i, x in enumerate(lab))
        return '<div class="m m-bins">%s<div class="m-chips"><span class="m-chipx">%s</span></div><div class="m-row3">%s</div></div>' % (h(ttl), E(_clip(ttl, 10)), bins)
    if lay == "locks":
        locks = "".join('<span class="m-lock%s">%s</span>' % (" open" if i < 2 else "", sh.icon("lock-open" if i < 2 else "lock", 20, "var(--sk-gd)" if i < 2 else "var(--sk-ink)", 2.2)) for i in range(5))
        q = kick or ttl
        return ('<div class="m m-locks"><div class="m-hud"><span class="sk-badge">%s 6:40</span><span class="sk-badge sk-badge-solid">단서 2 / 5</span></div><div class="m-lockrow">%s</div>'
                '<div class="m-qcard">%s</div><div class="m-input"><span>정답 입력</span>%s</div></div>' % (sh.icon("hourglass", 12), locks, E(_clip(q, 40)), sh.button("열기", t)))
    if lay == "closing":
        win = f.get("tag") != "패배"
        if kind == "game":
            podium = "".join('<div class="m-pod p%d"><b>%d</b></div>' % (i, i) for i in (2, 1, 3)) if win else ""
            art = sh.spot("trophy" if win else "refresh", t, 84)
            cta = sh.button("다시 하기" if win else "틀린 문제 다시", t)
            return ('<div class="m m-end%s"><div class="m-art">%s</div><div class="m-col">%s<p class="m-sub">%s</p><div class="m-cta">%s</div></div>%s<i class="m-burst"></i></div>'
                    % ("" if win else " lose", art, h(ttl, "m-t1"), E(_clip(note, 30)), cta, ('<div class="m-podium">%s</div>' % podium) if podium else ""))
        nx = "".join("<li>%s</li>" % E(_clip(x, 22)) for x in items[:3])
        return '<div class="m m-close">%s%s%s<ul class="m-next">%s</ul>%s<i class="m-deco m-deco1"></i></div>' % (sh.spot("heart", t, 64), chip, h(ttl, "m-t1"), nx, pg)
    return '<div class="m m-list"><div class="m-col">%s%s<p class="m-sub">%s</p></div><div class="m-side">%s</div></div>' % (chip, h(ttl), E(_clip(note, 50)), sh.spot(ic, t, 100))


MOCK_CSS = (
    ".m{position:absolute;inset:0;padding:6.5cqw 7cqw;display:flex;flex-direction:column;gap:2.6cqw;font-size:3.6cqw}"
    ".m .sk-badge{font-size:2.9cqw;align-self:flex-start}.m .sk-btn{font-size:3.4cqw}.m-col{display:flex;flex-direction:column;gap:2cqw;min-width:0}"
    ".m-t1{font-size:7.4cqw}.m-t2{font-size:5.6cqw}.m-sub{margin:0;color:var(--sk-mu);font-size:3.5cqw}.m-cta{display:flex;gap:2cqw;margin-top:1.5cqw}"
    ".m-pg{position:absolute;right:4cqw;bottom:3cqw;font-size:2.6cqw;color:var(--sk-mu);font-weight:700;letter-spacing:.06em}"
    ".m-cover{flex-direction:row;align-items:center;gap:5cqw}.m-art{flex:none;width:30cqw;display:grid;place-items:center}.m-art svg{width:100%;height:auto}.m-art .sk-char{border-radius:50%;background:var(--sk-sf);padding:2cqw;box-shadow:0 0 0 .5cqw color-mix(in srgb,var(--sk-pr) 30%,transparent);overflow:hidden}"
    ".m-deco{position:absolute;border-radius:50%;pointer-events:none}.m-deco1{width:22cqw;height:22cqw;right:-11cqw;top:-11cqw;background:color-mix(in srgb,var(--sk-pr) 14%,transparent)}"
    ".m-deco2{display:none}"
    ".m-top{position:absolute;left:5cqw;right:5cqw;top:4cqw}.m-rule{display:block;width:9cqw;height:.6cqw;background:var(--sk-pt)}"
    ".m-report .m-kcol{width:30cqw}.m-report .m-kpi.sm{flex-direction:row;align-items:baseline;justify-content:space-between;padding:1.4cqw 2.4cqw}.m-report .m-kpi.sm b{font-size:5.4cqw}"
    ".m-sec{flex-direction:row;align-items:center;gap:5cqw}.m-big{font-family:var(--sk-fd);font-weight:800;font-size:24cqw;line-height:1;color:var(--sk-pt);opacity:.9}"
    ".m-stmt{justify-content:center}.m-stmt .sk-spot{width:13cqw;height:13cqw}.m-q{font-family:var(--sk-fd);font-size:16cqw;line-height:.6;color:var(--sk-ac);height:7cqw}"
    ".m-list{flex-direction:row;align-items:center;gap:4cqw}.m-list .m-col{flex:1}.m-side{flex:none;width:28cqw}.m-side svg{width:100%;height:auto}"
    ".m ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1.8cqw}.m-list ul{gap:1.3cqw}.m-list li{display:flex;align-items:center;gap:2cqw;background:var(--sk-sf);color:var(--sk-ci);border-radius:calc(var(--sk-r)*.6);padding:1cqw 2.4cqw;font-size:3.3cqw;box-shadow:0 .4cqw 1.2cqw -.6cqw rgba(0,0,0,.25)}"
    ".m-tick{width:3.6cqw;height:3.6cqw;padding:.6cqw;border-radius:50%;background:var(--sk-pr);box-sizing:content-box}"
    ".m-two{flex:1;display:flex;gap:3cqw;align-items:stretch;position:relative}.m-card{flex:1;background:var(--sk-sf);color:var(--sk-ci);border-radius:var(--sk-r);padding:3cqw;display:flex;flex-direction:column;gap:1.6cqw;box-shadow:0 .6cqw 1.8cqw -.8cqw rgba(0,0,0,.3)}"
    ".m-card svg{width:7cqw;height:7cqw}.m-card b{font-size:4.2cqw}.m-cmp-a{border-top:1.2cqw solid var(--sk-pr)}.m-cmp-b{border-top:1.2cqw solid var(--sk-ac)}"
    ".m-line{display:block;height:1.6cqw;border-radius:2cqw;background:color-mix(in srgb,var(--sk-ci) 16%,transparent);width:90%}.m-line.s{width:62%}"
    ".m-vs{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:var(--sk-ink);color:var(--sk-bg);font-weight:800;font-size:3cqw;border-radius:50%;width:8cqw;height:8cqw;display:grid;place-items:center}"
    ".m-track{list-style:none;margin:auto 0;padding:0;display:flex;justify-content:space-between;position:relative}.m-track::before{content:'';position:absolute;left:6%;right:6%;top:4.5cqw;height:.8cqw;background:color-mix(in srgb,var(--sk-pr) 35%,transparent);border-radius:1cqw}"
    ".m-track li{position:relative;display:flex;flex-direction:column;align-items:center;gap:1.6cqw;width:22%;text-align:center}.m-dot{width:9cqw;height:9cqw;border-radius:50%;display:grid;place-items:center;background:var(--sk-pr);color:var(--sk-op);font-weight:800;font-size:4cqw;box-shadow:0 0 0 1.2cqw var(--sk-bg)}"
    ".m-track b{font-size:3.2cqw}"
    ".m-reveal{flex-direction:row;align-items:center;gap:5cqw}.m-ok svg{width:24cqw;height:24cqw}"
    ".m-burst{display:none}"
    ".m-row3{display:flex;gap:3cqw;flex:1;align-items:stretch}.m-kpi{flex:1;background:var(--sk-sf);color:var(--sk-ci);border-radius:var(--sk-r);padding:3cqw;display:flex;flex-direction:column;justify-content:center;gap:1cqw;box-shadow:0 .6cqw 1.8cqw -.8cqw rgba(0,0,0,.3)}"
    ".m-kpi b{font-family:var(--sk-fd);font-size:9cqw;line-height:1;color:var(--sk-pt)}.m-kpi span{font-size:3cqw;color:var(--sk-ci);opacity:.8}.m-kpi.sm{padding:2cqw}.m-kpi.sm b{font-size:6cqw}"
    ".m-bign{justify-content:center;align-items:center;text-align:center}.m-num{font-family:var(--sk-fd);font-size:22cqw;line-height:1;color:var(--sk-pt)}"
    ".m-quiz{gap:3cqw}.m-hud{display:flex;gap:2cqw;align-items:center}.m-hud .sk-badge:last-child{margin-left:auto}"
    ".m-qcard{background:var(--sk-sf);color:var(--sk-ci);border-radius:var(--sk-r);padding:3.4cqw 4cqw;font-weight:800;font-size:4.6cqw;line-height:1.3;box-shadow:0 .8cqw 2cqw -1cqw rgba(0,0,0,.35)}"
    ".m-grid2{display:grid;grid-template-columns:1fr 1fr;gap:2.4cqw;flex:1}.m-ans{display:flex;align-items:center;gap:2cqw;background:var(--sk-pr);color:var(--sk-op);border-radius:var(--sk-r);padding:0 3cqw;font-weight:800;font-size:3.8cqw}"
    ".m-ans i{font-style:normal;width:6cqw;height:6cqw;border-radius:50%;display:grid;place-items:center;background:color-mix(in srgb,var(--sk-op) 22%,transparent);font-size:3cqw}"
    ".m-ans:nth-child(2){background:var(--sk-ac);color:var(--sk-bg)}.m-ans:nth-child(3){background:color-mix(in srgb,var(--sk-pr) 70%,var(--sk-ink))}.m-ans:nth-child(4){background:color-mix(in srgb,var(--sk-ac) 70%,var(--sk-ink));color:var(--sk-bg)}"
    ".m-chartrow{flex:1;display:flex;gap:4cqw;min-height:0}.m-bars{flex:1;display:flex;align-items:flex-end;gap:2.4cqw;border-bottom:.5cqw solid color-mix(in srgb,var(--sk-ink) 40%,transparent);padding:0 1cqw}"
    ".m-bars i{flex:1;border-radius:1.2cqw 1.2cqw 0 0;background:color-mix(in srgb,var(--sk-ink) 28%,transparent)}.m-bars i.hi{background:var(--sk-pr)}.m-kcol{display:flex;flex-direction:column;gap:2cqw;width:24cqw}"
    ".m-formula{margin:auto;font-family:var(--sk-fd);font-size:7cqw;background:var(--sk-sf);color:var(--sk-ci);padding:3cqw 6cqw;border-radius:var(--sk-r)}"
    ".m-timer{flex-direction:row;align-items:center;gap:6cqw}.m-ring{width:34cqw;height:34cqw;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--sk-pr) 0 72%,color-mix(in srgb,var(--sk-ink) 14%,transparent) 0);flex:none}"
    ".m-ring b{width:27cqw;height:27cqw;border-radius:50%;display:grid;place-items:center;background:var(--sk-bg);font-family:var(--sk-fd);font-size:8cqw}"
    ".m-qr{flex-direction:row;align-items:center;gap:5cqw}.m-qr .m-col{flex:1}.m-code{width:30cqw;height:30cqw;flex:none;border-radius:2cqw;background:conic-gradient(var(--sk-ink) 25%,transparent 0 50%,var(--sk-ink) 0 75%,transparent 0) 0 0/5cqw 5cqw,var(--sk-sf);"
    "box-shadow:inset 0 0 0 2.4cqw var(--sk-sf),0 0 0 .6cqw var(--sk-ink)}"
    ".m-media{padding:4cqw;gap:2cqw}.m-ph{flex:1;border-radius:var(--sk-r);position:relative;display:grid;place-items:center;background:color-mix(in srgb,var(--sk-pr) 14%,var(--sk-bg));border:1px solid color-mix(in srgb,var(--sk-ink) 14%,transparent)}"
    ".m-ph svg.sk-spot{width:24cqw;height:24cqw}.m-play{position:absolute;right:3cqw;bottom:3cqw;width:9cqw;height:9cqw;border-radius:50%;display:grid;place-items:center;background:var(--sk-pr)}.m-play svg{width:4.5cqw;height:4.5cqw}"
    ".m-cap{display:flex;align-items:center;gap:2cqw;font-size:3.8cqw}"
    ".m-tiles{flex:1;display:grid;grid-template-columns:repeat(4,1fr);gap:1.8cqw}.m-tile{display:grid;place-items:center;border-radius:calc(var(--sk-r)*.6);font-weight:800;font-size:4.6cqw;color:var(--sk-op);"
    "background:repeating-linear-gradient(45deg,color-mix(in srgb,var(--sk-op) 12%,transparent) 0 1cqw,transparent 1cqw 2.4cqw),var(--sk-pr)}.m-tile.up{background:var(--sk-sf);color:var(--sk-ci);font-size:3.4cqw;box-shadow:inset 0 0 0 .6cqw var(--sk-ac)}.m-tile svg{width:6cqw;height:6cqw}"
    ".m-bins .m-row3{align-items:flex-end}.m-bin{flex:1;height:26cqw;border-radius:1.4cqw 1.4cqw var(--sk-r) var(--sk-r);background:var(--sk-sf);color:var(--sk-ci);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.4cqw;border-top:1.8cqw solid var(--sk-pr)}"
    ".m-bin svg{width:7cqw;height:7cqw}.m-chips{display:flex;justify-content:center}.m-chipx{background:var(--sk-ac);color:var(--sk-bg);font-weight:800;padding:1.4cqw 3.4cqw;border-radius:99px}"
    ".m-lockrow{display:flex;gap:2.4cqw;justify-content:center}.m-lock{width:10cqw;height:10cqw;border-radius:var(--sk-r);display:grid;place-items:center;background:var(--sk-sf);box-shadow:inset 0 0 0 .5cqw color-mix(in srgb,var(--sk-ink) 20%,transparent)}"
    ".m-lock.open{box-shadow:inset 0 0 0 .8cqw var(--sk-gd)}.m-lock svg{width:5.4cqw;height:5.4cqw}"
    ".m-input{display:flex;gap:2cqw;align-items:center}.m-input span{flex:1;border:.5cqw dashed color-mix(in srgb,var(--sk-ink) 40%,transparent);border-radius:var(--sk-r);padding:1.6cqw 3cqw;color:var(--sk-mu);font-size:3.2cqw}"
    ".m-end{flex-direction:row;align-items:center;gap:4cqw}.m-end .m-art{width:24cqw}.m-end.lose{filter:saturate(.75)}"
    ".m-podium{position:absolute;right:6cqw;bottom:0;display:flex;align-items:flex-end;gap:1cqw}.m-pod{width:7cqw;background:var(--sk-pr);color:var(--sk-op);border-radius:1cqw 1cqw 0 0;display:flex;justify-content:center;padding-top:1cqw;font-size:3cqw}"
    ".m-pod.p1{height:16cqw;background:var(--sk-ac);color:var(--sk-bg)}.m-pod.p2{height:11cqw}.m-pod.p3{height:8cqw;opacity:.8}"
    ".m-close{justify-content:center;align-items:flex-start}.m-close .sk-spot{width:12cqw;height:12cqw}.m-next li{font-size:3.2cqw;color:var(--sk-mu)}.m-next li::before{content:'→ ';color:var(--sk-pt);font-weight:800}"
    ".sk-phone .m,.sk-a4 .m{padding:9cqw 7cqw}.sk-phone .m-cover,.sk-phone .m-list,.sk-phone .m-timer,.sk-phone .m-qr,.sk-phone .m-reveal,.sk-phone .m-end,.sk-a4 .m-cover,.sk-a4 .m-list{flex-direction:column;align-items:flex-start}"
    ".sk-phone .m-t1{font-size:10cqw}.sk-phone .m-t2{font-size:8cqw}.sk-phone .m{font-size:5cqw}.sk-phone .m-grid2{grid-template-columns:1fr}"
)

SHEET_CSS = (
    "*{box-sizing:border-box}body{margin:0;background:#f2f4f7;color:#161b22;font-synthesis:none;"
    "font:16px/1.5 'TS Sans','Pretendard','Noto Sans KR','Malgun Gothic',system-ui,sans-serif;padding:0 0 40px;word-break:keep-all}"
    ".top{padding:32px 28px 24px;background:var(--hd-bg);color:var(--hd-ink);position:relative;overflow:hidden}"
    ".top::after{content:'';position:absolute;left:28px;bottom:0;width:48px;height:3px;background:var(--hd-ac)}"
    ".top h1{font-size:32px;margin:8px 0 4px;font-weight:760;letter-spacing:-.035em;line-height:1.2;text-wrap:balance;position:relative;z-index:1}.top p{margin:0;opacity:.85;position:relative;z-index:1}"
    ".kick{display:flex;gap:8px;flex-wrap:wrap;position:relative;z-index:1}.kick span{font-size:13px;font-weight:600;letter-spacing:.02em;padding:3px 8px;border-radius:99px;border:1px solid color-mix(in srgb,currentColor 30%,transparent)}"
    ".sw{display:inline-flex;gap:4px;vertical-align:middle}.sw i{width:14px;height:14px;border-radius:50%;border:1.5px solid rgba(255,255,255,.7)}"
    "ol.sheet{list-style:none;margin:0;padding:24px 24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:32px 24px}"
    ".card{position:relative;background:#fff;border-radius:12px;padding:16px;border:1px solid #e1e5ea}"
    ".no{position:absolute;left:-10px;top:-12px;z-index:4;background:#151b28;color:#fff;border-radius:8px;min-width:32px;height:32px;display:grid;place-items:center;font-weight:700;font-variant-numeric:tabular-nums;padding:0 8px;box-shadow:0 0 0 3px #f2f4f7}"
    ".meta{padding-top:12px}.meta b{font-size:18px;font-weight:700;letter-spacing:-.02em}.meta p{margin:4px 0 0;font-size:14.5px;color:#4a5365}"
    ".tag,.sec{display:inline-block;margin-left:8px;padding:0 8px;border-radius:999px;font-size:12.5px;font-weight:700;background:#eef1f6;color:#30394b;vertical-align:2px}"
    ".foot{padding:0 28px;color:#566079}@media print{body{background:#fff}.card{break-inside:avoid;box-shadow:none;border:1px solid #ccd}}"
)


def render_html(frames: list, title: str, tok: dict | None = None, style: str = "", device: str = "tv", kind: str = "generic", embed: bool = False) -> str:
    """The 콘티 sheet. tok = palette() result (the user's own colours win when tok['_own']); style = a styles.py id; device = frame kind."""
    sh = _load("shell", "shell")
    if sh is None:
        return _render_wire(frames, title, tok)
    user = None
    if tok and tok.get("_own"):
        user = {"bg1": tok["bg"], "text": tok["ink"], "primary": tok["accent"], "card": tok.get("frame", "#ffffff")}
        if tok.get("accent2"):
            user["accent"] = tok["accent2"]
    t = sh.tokens(style or None, user=user)
    total = len(frames)
    cards = []
    for i, f in enumerate(frames, 1):
        sec = '<span class="sec">%g초</span>' % f["secs"] if f.get("secs") else ""
        tag = '<span class="tag">%s</span>' % E(f["tag"]) if f.get("tag") else ""
        screen = sh.frame(device, mock(f, t, sh, kind, i, total), t)
        cards.append('<li class="card"><div class="no">%d</div>%s<div class="meta"><b>%s</b>%s%s<p>%s</p></div></li>' % (i, screen, E(f["title"]), tag, sec, E(f["note"])))
    tt = total_secs(frames)
    foot = "합계 %g초 · %d컷" % (tt, len(frames)) if tt else "%d장면" % len(frames)
    look = "내 색" if t["own"] else _style_ko(t["style"])
    hd_bg = t["primary"] if not t["dark"] else t["bg"]
    hd_ink = t["on_primary"] if not t["dark"] else t["ink"]
    head_vars = "--hd-bg:%s;--hd-ink:%s;--hd-ac:%s" % (hd_bg, hd_ink, t["accent"])
    sw = "".join('<i style="background:%s"></i>' % c for c in (t["bg"], t["primary"], t["accent"], t["surface"]))
    body = ('<header class="top" style="%s"><div class="kick"><span>콘티</span><span>%s <span class="sw">%s</span></span><span>%s</span></div><h1>%s</h1>'
            '<p>완성되면 이런 화면이 이 순서로 나와요. 바꾸고 싶은 번호를 말씀해 주세요.</p></header><ol class="sheet">%s</ol><p class="foot">%s</p>'
            % (head_vars, E(look), sw, E(DEVICE_KO.get(device, device)), E(title), "".join(cards), E(foot)))
    return sh.page(title + " - 콘티", body, SHEET_CSS + MOCK_CSS, embed=embed)


DEVICE_KO = {"tv": "TV·빔 화면", "board": "전자칠판", "laptop": "노트북", "tablet": "태블릿", "phone": "휴대폰", "a4": "A4 인쇄"}


def _style_ko(sid: str) -> str:
    try:
        import direction
        return direction.FEEL.get(sid, (sid, ""))[0]
    except Exception:
        return sid


def _render_wire(frames: list, title: str, tok: dict | None = None) -> str:
    """Fallback when shared/shell is missing: the old box sketch."""
    tok = tok or DEFAULT
    cards = []
    for i, f in enumerate(frames, 1):
        boxes = "".join('<i class="%s" style="left:%d%%;top:%d%%;width:%d%%;height:%d%%"></i>' % (k, x, y, w, h) for x, y, w, h, k in SKETCH.get(f["layout"], SKETCH["list"]))
        cards.append('<li class="card"><div class="no">%d</div><div class="fr">%s</div><div class="meta"><b>%s</b><p>%s</p></div></li>' % (i, boxes, E(f["title"]), E(f["note"])))
    css = (":root{--bg:%(bg)s;--ink:%(ink)s;--frame:%(frame)s;--line:%(line)s;--ac:%(accent)s;--soft:%(soft)s}"
           "body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.5 'TS Sans','Pretendard','Noto Sans KR','Malgun Gothic',sans-serif;padding:28px 16px}ol{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}"
           ".card{position:relative;background:var(--frame);border:2px solid var(--line);border-radius:14px;padding:12px}.fr{position:relative;aspect-ratio:16/9;background:var(--bg);overflow:hidden}"
           ".fr i{position:absolute;background:var(--line)}.fr i.h{background:var(--ink)}.fr i.a{background:var(--ac)}") % {k: tok.get(k, DEFAULT[k]) for k in DEFAULT}
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>%s - 콘티</title><style>%s</style></head><body><h1>%s</h1><ol>%s</ol></body></html>'
            % (E(title), css, E(title), "".join(cards)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--html")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--title")
    ap.add_argument("--style", default="", help="a style id (shared/design/styles.py); default: from the spec")
    ap.add_argument("--device", default="", help="tv | board | laptop | tablet | phone | a4 (default: from the spec)")
    ap.add_argument("--palette-from", help="'saved' (default) or a colours JSON")
    a = ap.parse_args()
    try:
        d = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("읽을 수 없는 파일이에요: %s" % e)
        return 1
    fr = frames_from_spec(d)
    if not fr:
        print('콘티로 바꿀 장면이 없어요. slides·game·shots 형식이거나 {"frames":[{"title","note","layout"}]} 로 써 주세요.')
        return 1
    title = sheet_title(d, a.title)
    print(render_text(fr, title))
    if a.html or a.open:
        kind = kind_of(d)
        des = d.get("design") if isinstance(d.get("design"), dict) else {}
        pal_arg = a.palette_from or (des.get("palette_from") if isinstance(des.get("palette_from"), str) else None)
        path = Path(a.html) if a.html else workdir.named("storyboard.html")
        style = choose_style(d, a.style, kind)
        path.write_text(render_html(fr, title, palette(pal_arg), style, device_for(d, kind, a.device), kind, embed=True), encoding="utf-8")
        print("READY " + str(path))
        if a.open:
            webbrowser.open(path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
