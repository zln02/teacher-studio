#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Slide type from the SHAPE of the content (counts, hierarchy, media), not from a fixed order per context.

A slide written as {"type": "auto", ...} (or with no type) gets its type here; a `bullets` slide whose items are really a sequence,
a set of figures or a two-sided comparison gets a NOTE naming the type that fits. The outline itself (which slides, in which order)
is still the author's decision and comes from the content: nothing here inserts or reorders slides.

    what the content is                          -> type
    a question with choices                      -> quiz
    series / labels + data                       -> chart          columns + rows            -> table
    shapes                                       -> diagram        tex                       -> math
    dated or timed events                        -> timeline       ordered steps             -> steps
    two sides (a / b, or rows with k, a, b)      -> compare        one figure (value)        -> bignumber
    2-3 figures                                  -> bignumbers     a picture or a video file -> image / video
    a headline with a call to action             -> hero           an address only           -> qr
    one sentence                                 -> statement      a sentence with a source  -> quote
    a title only                                 -> section        a list of points          -> bullets

Usage: python3 deck_shape.py deck.json      # prints the type each "auto" slide would get and the NOTEs
"""
from __future__ import annotations

import json
import re
import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

VIDEO_EXT = (".mp4", ".webm", ".mov", ".m4v")
_ORDER = re.compile(r"^\s*(?:[①-⑳]|\d{1,2}\s*[.)]|\d{1,2}\s*단계|첫째|둘째|셋째|넷째|먼저|다음(?:으로)?|그다음|마지막(?:으로)?|끝으로)[\s,:]")
_FIGURE = re.compile(r"^\s*(?:약\s*)?([0-9][0-9.,]*)\s*(%|％|명|개|건|원|만 원|시간|분|배|회|점|곳|학급|교|권|km|kg|m|℃)?\s*[:·\-–—]\s*(.{2,})$")
_WHEN = re.compile(r"^\s*(\d{4}\s*년(?:\s*\d{1,2}\s*월)?(?:\s*\d{1,2}\s*일)?|\d{1,2}\s*월(?:\s*\d{1,2}\s*일)?|\d{1,2}\s*:\s*\d{2}|\d{1,2}\s*시(?:\s*\d{1,2}\s*분)?|\d{1,2}\s*교시|\d{1,2}\s*주차?)\s*[:·\-–—]\s*(.{2,})$")
_PAIR = re.compile(r"^(.{1,14}?)\s*[:：]\s*(.{2,})$")


def _texts(items) -> list[str]:
    return [x for x in (items or []) if isinstance(x, str)]


def list_shape(items) -> str:
    """What a plain list of strings really is: 'steps' | 'bignumbers' | 'timeline' | 'pairs' | ''."""
    ss = _texts(items)
    if len(ss) < 2 or len(ss) != len(items):
        return ""
    if 2 <= len(ss) <= 3 and all(_FIGURE.match(s) for s in ss):
        return "bignumbers"
    if len(ss) >= 3 and all(_WHEN.match(s) for s in ss):
        return "timeline"
    if len(ss) >= 3 and sum(1 for s in ss if _ORDER.match(s)) >= len(ss) - 1:
        return "steps"
    if len(ss) >= 3 and all(_PAIR.match(s) for s in ss):
        return "pairs"
    return ""


def infer(it: dict) -> dict:
    """Return the slide with a concrete type chosen from its content. Keys the author wrote are kept; lists are re-keyed when the type needs it."""
    d = {k: v for k, v in it.items() if k != "type"}
    items = d.get("items")
    f = str(d.get("file") or "").lower()

    def as_(t: str, **extra) -> dict:
        return {**d, **extra, "type": t}

    if d.get("q") and d.get("choices"):
        return as_("quiz")
    if d.get("series") or (d.get("labels") and d.get("data")):
        return as_("chart")
    if d.get("columns") and d.get("rows"):
        return as_("table")
    if d.get("shapes"):
        return as_("diagram")
    if d.get("tex"):
        return as_("math")
    if d.get("events"):
        return as_("timeline")
    if d.get("steps"):
        return as_("steps")
    if (d.get("a") and d.get("b")) or (isinstance(d.get("rows"), list) and d["rows"] and all(isinstance(r, dict) for r in d["rows"])):
        return as_("compare")
    if d.get("value") is not None:
        return as_("bignumber")
    if d.get("headline"):
        return as_("hero")
    if f:
        return as_("video" if f.endswith(VIDEO_EXT) else "image")
    if isinstance(items, list) and items:
        if all(isinstance(x, dict) for x in items):
            if all("value" in x for x in items) and 2 <= len(items) <= 3:
                return as_("bignumbers")
            if all("value" in x for x in items):
                rows = [[str(x.get("caption", "")), "%s%s" % (x.get("value", ""), x.get("unit", ""))] for x in items][:8]
                return as_("table", columns=["항목", "값"], rows=rows, items=None)
            if all("when" in x for x in items):
                return as_("timeline", events=items, items=None)
            if all("title" in x for x in items):
                return as_("steps", steps=items, items=None)
        kind = list_shape(items)
        if kind == "bignumbers":
            ms = [_FIGURE.match(s) for s in items]
            return as_("bignumbers", items=[{"value": m.group(1), "unit": m.group(2) or "", "caption": m.group(3).strip()} for m in ms])
        if kind == "timeline" and 3 <= len(items) <= 6:
            ms = [_WHEN.match(s) for s in items]
            return as_("timeline", events=[{"when": m.group(1).strip(), "title": m.group(2).strip()} for m in ms], items=None)
        if kind == "pairs" and len(items) <= 8:
            ms = [_PAIR.match(s) for s in items]
            return as_("table", columns=d.get("columns") or ["항목", "내용"], rows=[[m.group(1).strip(), m.group(2).strip()] for m in ms], items=None)
        return as_("bullets")
    if d.get("points"):
        return as_("summary")
    if d.get("url") and not d.get("text"):
        return as_("qr")
    if d.get("minutes") and not d.get("text"):
        return as_("timer")
    if d.get("text") and d.get("source"):
        return as_("quote")
    if d.get("text") and not d.get("title"):
        return as_("statement")
    if d.get("text"):
        return as_("illustration")
    return as_("section")


def resolve(slides: list) -> list:
    """Give every {"type": "auto"} / untyped slide its type. An untyped title-only first slide is the cover, a last one the closing."""
    out = []
    n = len(slides)
    for i, it in enumerate(slides):
        if not isinstance(it, dict) or (it.get("type") not in (None, "", "auto")) or it.get("layout"):
            out.append(it)
            continue
        got = infer(it)
        if got["type"] == "section" and i == 0:
            got["type"] = "title"
        elif got["type"] in ("section", "statement") and i == n - 1 and n > 2:
            got = {**got, "type": "closing", "title": got.get("title") or got.get("text", "")}
        out.append({k: v for k, v in got.items() if v is not None})
    return out


NOTE_TEXT = {"steps": "순서가 있는 내용이에요 → steps", "bignumbers": "숫자가 주인공이에요 → bignumbers", "timeline": "날짜·시간 순서예요 → timeline",
             "pairs": "「이름: 설명」 짝이에요 → table 또는 compare"}


def notes(slides: list) -> list[str]:
    """NOTE lines: a bullets slide whose list has another shape (the fit is the author's call; the build never changes a typed slide)."""
    out = []
    for i, it in enumerate(slides, 1):
        if isinstance(it, dict) and it.get("type") in ("bullets", "list", "cards") and not it.get("_role") and not it.get("pics"):  # a picture list is drawn as picture tiles
            k = list_shape(it.get("items"))
            if k:
                out.append(f"slide {i} bullets: {NOTE_TEXT[k]} (내용 모양에 맞는 장으로 바꾸면 한눈에 읽혀요)")
    typed = [it.get("type") for it in slides if isinstance(it, dict)]
    body = [t for t in typed if t not in ("title", "cover", "hero", "section", "closing", "toc", "end")]
    out += variety(slides)
    return out


LISTS = ("bullets", "list", "cards")


def variety(slides: list) -> list[str]:
    """NOTE lines about the deck as a whole: it must not look the same on every slide, and evidence belongs next to its claim."""
    out = []
    its = [it for it in slides if isinstance(it, dict)]
    body = [it for it in its if it.get("type") not in ("title", "cover", "hero", "section", "closing", "toc", "end") and not it.get("_role")]
    types = [it.get("type") for it in body]
    n = len(types)
    if n >= 6:
        nl = sum(1 for it in body if it.get("type") in LISTS and not it.get("pics"))
        if nl / n > 1 / 3:
            out.append(f"본문 {n}장 가운데 {nl}장이 글머리표예요 → 순서는 steps, 비교는 compare/table, 수치는 bignumbers/chart, 구조는 diagram, 근거가 둘이면 panel로 내용 모양을 따라가세요")
        top = max(set(types), key=types.count)
        if top not in LISTS and types.count(top) / n > 0.5:
            out.append(f"본문의 절반 넘게가 같은 종류({top})예요 → 장마다 내용 모양에 맞는 종류로 (모든 장이 같은 모양이면 단조로워요)")
    seq = [it.get("type") for it in its]
    for i in range(len(seq) - 2):
        if all(t in LISTS for t in seq[i:i + 3]) and not any(its[j].get("_role") or its[j].get("pics") for j in range(i, i + 3)):
            out.append(f"slide {i + 1}-{i + 3}: 글머리표 장이 세 장 이어져요 → 가운데 장을 표·그림·비교·panel로")
            break
    for i in range(len(its) - 1):
        a, b = its[i].get("type"), its[i + 1].get("type")
        if {a, b} & {"bignumber", "bignumbers"} and {a, b} & {"chart", "table"}:
            out.append(f"slide {i + 1}-{i + 2}: 숫자 장과 그 근거(표·그래프) 장이 따로 있어요 → 한 장으로: {{\"type\":\"panel\",\"blocks\":[{{\"kind\":\"kpis\"}},{{\"kind\":\"chart\"}}]}}")
            break
    data = [it for it in body if it.get("type") in ("chart", "table") or (it.get("type") == "panel" and any(isinstance(b, dict) and b.get("kind") in ("chart", "table") for b in it.get("blocks") or []))]
    if len(data) >= 2 and not any(it.get("takeaway") for it in data):
        out.append("표·그래프 장에 결론 한 줄이 없어요 → 그 자료가 무엇을 뜻하는지 \"takeaway\"로 (제목을 되풀이하지 말고 의미를)")
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    spec = json.loads(open(sys.argv[1], encoding="utf-8").read())
    slides = spec.get("slides") or spec.get("items") or []
    done = resolve(slides)
    for i, (a, b) in enumerate(zip(slides, done), 1):
        if a.get("type") in (None, "", "auto"):
            print(f"slide {i}: auto -> {b['type']}")
    for n in notes(done):
        print("NOTE", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
