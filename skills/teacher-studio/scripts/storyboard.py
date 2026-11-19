# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Storyboard (콘티) sheet: numbered frames as boxes from a spec/plan JSON. One offline HTML + a plain-text fallback. No network, no student data.

Usage:
    python3 storyboard.py spec.json [--html sheet.html [--open]] [--text] [--palette-from saved|FILE] [--title T]

Reads, WITHOUT changing them: a teacher-slides deck spec ({"slides":[...]}), a teacher-game spec ({"mechanic","items"}),
a shot list ({"shots":[{"title","seconds","narration"}]}), and the generic {"frames":[{"title","note","layout"}]}.
Anything else with a top-level list of dicts falls back to a generic frame list. Colours: the saved/own palette if any, else calm defaults.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
import webbrowser
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# layout -> rectangles (x, y, w, h in %, kind). kind: h heading, t text, b block, a accent
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
ALIAS = {"intro": "title", "cover": "title", "outro": "closing", "end": "closing", "result": "bignumber", "play": "quiz", "rules": "bullets",
         "flow": "steps", "screen": "list", "wireframe": "list", "full": "image", "shots": "shot", "scene": "shot"}
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
DEFAULT = {"bg": "#f6f4ef", "ink": "#1d2433", "frame": "#ffffff", "line": "#c9c4b8", "accent": "#2563eb", "soft": "#e8eefc", "muted": "#5b6474"}


def _s(v, n=120) -> str:
    return re.sub(r"\s+", " ", str(v if v is not None else "")).replace("**", "").strip()[:n]


def _layout(name: str) -> str:
    name = _s(name, 40).split(".")[0].lower()
    name = ALIAS.get(name, name)
    return name if name in SKETCH else "list"


def _frame(title, layout, note="", secs=None, tag="") -> dict:
    return {"title": _s(title, 60), "layout": _layout(layout), "note": _s(note, 160), "secs": secs, "tag": _s(tag, 20)}


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


def frames_from_slides(d: dict) -> list:
    out = []
    for sl in d.get("slides", []):
        if not isinstance(sl, dict):
            continue
        t = sl.get("type", "bullets")
        title = sl.get("title") or sl.get("text") or sl.get("q") or sl.get("tex") or (str(sl.get("value", "")) + str(sl.get("unit", "")))
        out.append(_frame(title, sl.get("layout") or t, slide_note(sl), tag=t))
    return out


def frames_from_game(d: dict) -> list:
    mech = d.get("mechanic", "quiz")
    items = d.get("items") if isinstance(d.get("items"), list) else []
    title = d.get("title") or "게임"
    qs = []
    for it in items[:3]:
        if isinstance(it, dict):
            qs.append(_s(it.get("q") or it.get("word") or it.get("a"), 30))
    teams = d.get("teams") or 0
    secs = d.get("seconds")
    has_exp = any(isinstance(i, dict) and i.get("exp") for i in items)
    frames = [
        _frame(title, "title", _s(d.get("subtitle")) or "제목 화면: 시작 버튼 하나", tag="시작"),
        _frame("규칙 한 장", "bullets", "방식: %s · %s%s" % (mech, ("%d팀 · " % teams) if teams else "", ("제한 %s초" % secs) if secs else "문제 %d개" % len(items)), tag="규칙"),
        _frame("진행 화면", GAME_PLAY.get(mech, "quiz"), GAME_PLAY_KO.get(mech, "문제를 풀며 진행한다") + ((" · 예: " + " / ".join(qs)) if qs else ""), tag="진행"),
        _frame("정답 공개", "bignumber", "정답과 한 줄 설명 (" + ("설명 있음" if has_exp else "설명 없음") + ") · 손맛: " + GAME_JUICE.get(mech, "정답 순간 작은 연출"), tag="공개"),
        _frame("이기면", "closing", "순위·점수, 박수와 꽃가루", tag="승리"),
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
                              secs=sec if isinstance(sec, (int, float)) else None))
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


def palette(arg=None) -> dict:
    """Own palette if saved/given, else calm defaults. Text is re-fitted for contrast when oklch is available."""
    tok = dict(DEFAULT)
    try:
        import direction
        cols = direction.user_palette(arg or "saved", direction._prefs_module())
        if cols:
            tok["bg"] = cols.get("bg1") or cols.get("bg") or tok["bg"]
            tok["ink"] = cols.get("text") or tok["ink"]
            tok["accent"] = cols.get("primary") or cols.get("accent") or tok["accent"]
            tok["frame"] = cols.get("card") or tok["frame"]
            ok = direction._load_module("oklch")
            if ok and ok.contrast(tok["ink"], tok["bg"]) < 4.5:
                tok["ink"] = ok.fit_contrast(tok["ink"], tok["bg"], 4.5)
            if re.fullmatch(r"#[0-9a-fA-F]{6}", tok["accent"]):
                tok["soft"] = tok["accent"] + "33"
    except Exception:
        pass
    return tok


def _sketch_html(layout: str) -> str:
    out = []
    for x, y, w, h, k in SKETCH.get(layout, SKETCH["list"]):
        out.append('<i class="%s" style="left:%d%%;top:%d%%;width:%d%%;height:%d%%"></i>' % (k, x, y, w, h))
    return "".join(out)


def render_html(frames: list, title: str, tok: dict | None = None) -> str:
    tok = tok or DEFAULT
    cards = []
    for i, f in enumerate(frames, 1):
        sec = '<span class="sec">%g초</span>' % f["secs"] if f.get("secs") else ""
        tag = '<span class="tag">%s</span>' % html.escape(f["tag"]) if f.get("tag") else ""
        cards.append('<li class="card"><div class="no">%d</div><div class="fr">%s</div><div class="meta"><b>%s</b>%s%s<p>%s</p></div></li>' % (
            i, _sketch_html(f["layout"]), html.escape(f["title"]), tag, sec, html.escape(f["note"])))
    t = total_secs(frames)
    foot = "합계 %g초 · %d컷" % (t, len(frames)) if t else "%d장면" % len(frames)
    css = (":root{--bg:%(bg)s;--ink:%(ink)s;--frame:%(frame)s;--line:%(line)s;--ac:%(accent)s;--soft:%(soft)s}"
           "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.5 'Noto Sans KR','Malgun Gothic',system-ui,sans-serif;padding:28px 16px}"
           "h1{font-size:30px;margin:0 0 4px}.sub{opacity:.7;margin:0 0 22px}"
           "ol{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}"
           ".card{position:relative;background:var(--frame);border:2px solid var(--line);border-radius:14px;padding:12px}"
           ".no{position:absolute;left:-8px;top:-10px;background:var(--ac);color:#fff;border-radius:999px;min-width:34px;height:34px;display:grid;place-items:center;font-weight:700;padding:0 8px}"
           ".fr{position:relative;aspect-ratio:16/9;background:var(--bg);border:1px solid var(--line);border-radius:8px;overflow:hidden}"
           ".fr i{position:absolute;display:block;border-radius:4px;background:var(--line)}.fr i.h{background:var(--ink);opacity:.8}.fr i.a{background:var(--ac);opacity:.75}.fr i.b{background:var(--soft);border:2px solid var(--ac)}"
           ".meta{padding-top:10px}.meta b{font-size:20px}.meta p{margin:4px 0 0;font-size:16px;opacity:.85}"
           ".tag,.sec{display:inline-block;margin-left:8px;padding:0 8px;border-radius:999px;font-size:14px;background:var(--soft);border:1px solid var(--ac)}"
           ".foot{margin-top:22px;opacity:.7}@media print{body{padding:8px}.card{break-inside:avoid}}") % tok
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>%s - 콘티</title><style>%s</style></head><body><h1>%s</h1><p class=\"sub\">콘티 (장면 순서와 그림 위치). 바꾸고 싶은 번호를 말씀해 주세요.</p><ol>%s</ol><p class=\"foot\">%s</p></body></html>" % (
                html.escape(title), css, html.escape(title), "".join(cards), html.escape(foot)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--html")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--title")
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
        path = Path(a.html) if a.html else Path(tempfile.gettempdir()) / "storyboard.html"
        path.write_text(render_html(fr, title, palette(a.palette_from)), encoding="utf-8")
        print("READY " + str(path))
        if a.open:
            webbrowser.open(path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
