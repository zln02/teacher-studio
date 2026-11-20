# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Example-likeness: did an output follow a shipped example too closely?

The files in a skill's examples folder are FIXTURES (they prove the builder accepts a shape). They are not patterns. A result whose
words or skeleton come from one of them gets a WARN: 「예시를 그대로 따라간 것 같아요」.

Two ways to ask:
  check_spec(spec, folders)   the builder has the spec: copied sentences, or the same part sequence with the same headings
  check_text(text, folders)   a checker only has the finished file (HTML / extracted text): the example's sentences found in it

Rules (WARN, never FAIL: the user may really want the example):
  - text    >= 60 % of the example's content sentences appear in the output, word for word
  - skeleton the part sequence (slide types, sections ...) is the same AND > 60 % of the headings are the example's headings
  - shape   a long, varied part sequence (>= 6 parts, >= 3 kinds) repeats an example part for part, down to how much each part holds
An unchanged fixture built as itself (it carries "_fixture") is reported as PASS, so the fixtures can still be test-built.

Usage: python3 example_likeness.py spec.json examples_dir [more_dirs]
"""
from __future__ import annotations

import difflib
import html as _html
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

MSG = "예시를 그대로 따라간 것 같아요"
FIX = "예시는 도구가 받는 모양을 보여 주는 시험용 파일이에요. 이 내용에서 차례와 문장을 새로 정해 주세요"
TEXT_SHARE = 0.6      # share of an example's sentences found in the output
HEAD_SHARE = 0.6      # share of headings that are the example's headings (with the same part sequence)
SHAPE_RATIO = 0.9     # part-for-part likeness of a long, varied sequence
MIN_STRINGS = 4       # examples with fewer content sentences cannot be judged by text
# keys whose values are settings, code or file names, not content
CONFIG_KEYS = {"type", "kind", "layout", "mechanic", "context", "style", "mood", "device", "use", "purpose", "theme", "font", "id", "icon", "art",
               "motif", "file", "url", "css", "js", "code", "palette", "palette_from", "design", "words", "seed", "format", "paper",
               "color", "fill", "tex", "keys", "variant", "transition", "align", "unit", "when", "date", "labels", "columns", "_fixture"}
HEAD_KEYS = {"title", "subtitle", "q", "question", "heading", "label", "name", "kicker", "sub", "caption"}
LIST_KEYS = ("slides", "items", "sections", "parts", "blocks", "frames", "body", "pages", "rows", "analyses")
_KEEP = re.compile(r"[^0-9A-Za-z가-힣]+")


def norm(s: str) -> str:
    """Letters and digits only: survives HTML escaping, **stars**, line breaks and punctuation changes."""
    return _KEEP.sub("", str(s))


def strings(node, heads: bool = False, _key: str = "") -> list[str]:
    """Content sentences of a spec (normalised, >= 5 letters: Korean is dense), settings and code left out. heads=True: heading-like keys only."""
    out: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in CONFIG_KEYS or str(k).startswith("_"):
                continue
            out += strings(v, heads, str(k))
    elif isinstance(node, list):
        for v in node:
            out += strings(v, heads, _key)
    elif isinstance(node, str) and _key == "html":  # a web app part's own markup: the words between the tags are content
        if not heads:
            out += [n for n in (norm(t) for t in re.split(r"<[^>]*>", node)) if len(n) >= 4]
    elif isinstance(node, str):
        n = norm(node)
        if len(n) >= 5 and (not heads or _key in HEAD_KEYS):
            out.append(n)
    return out


def main_list(spec: dict) -> list:
    """The list that carries the parts (slides, items, sections ...): the longest list of objects under a known key."""
    best: list = []
    for k in LIST_KEYS:
        v = spec.get(k) if isinstance(spec, dict) else None
        if isinstance(v, list) and len([x for x in v if isinstance(x, dict)]) > len(best):
            best = [x for x in v if isinstance(x, dict)]
    return best


def sequence(spec: dict) -> list[str]:
    return [str(p.get("type") or p.get("kind") or p.get("layout") or "-") for p in main_list(spec)]


def shape(spec: dict) -> list[str]:
    """Per part: kind + how many children (points, steps, rows). Two decks with the same shape have the same skeleton."""
    out = []
    for p in main_list(spec):
        kids = max([len(v) for v in p.values() if isinstance(v, list)] or [0])
        out.append(f"{p.get('type') or p.get('kind') or '-'}:{kids}")
    return out


def compare(spec: dict, example: dict) -> dict:
    mine, theirs = strings(spec), set(strings(example))
    ex_list = strings(example)
    got = set(mine)
    text = sum(1 for s in ex_list if s in got) / len(ex_list) if len(ex_list) >= MIN_STRINGS else 0.0
    h_mine, h_theirs = strings(spec, True), set(strings(example, True))
    heads = sum(1 for s in h_mine if s in h_theirs) / len(h_mine) if len(h_mine) >= 3 else 0.0
    sa, sb = sequence(spec), sequence(example)
    pa, pb = shape(spec), shape(example)
    shp = difflib.SequenceMatcher(None, pa, pb).ratio() if len(pa) >= 6 and len(set(sa)) >= 3 and abs(len(pa) - len(pb)) <= 1 else 0.0
    return {"text": round(text, 3), "heads": round(heads, 3), "same_sequence": bool(sa) and sa == sb, "shape": round(shp, 3),
            "identical": bool(mine) and sorted(mine) == sorted(ex_list), "copied": sum(1 for s in mine if s in theirs)}


def load_examples(folders) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for folder in folders:
        folder = Path(folder)
        if not folder.is_dir():
            continue
        for f in sorted(folder.rglob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(data, dict):
                out[f.name] = data
    return out


def judge(c: dict) -> str:
    """Why this pair is too alike ('' = it is not)."""
    if c["text"] >= TEXT_SHARE:
        return f"예시 문장의 {round(c['text'] * 100)}%가 그대로 들어 있어요"
    if c["same_sequence"] and c["heads"] > HEAD_SHARE:
        return f"차례가 예시와 같고 제목의 {round(c['heads'] * 100)}%가 예시 제목이에요"
    if c["shape"] >= SHAPE_RATIO:
        return "장마다 종류와 분량이 예시와 똑같은 뼈대예요"
    return ""


def check_spec(spec: dict, folders, skeleton_only: bool = False) -> list[tuple[str, str]]:
    """[("WARN", ...)] when the spec follows a shipped example, [("PASS", ...)] otherwise (or [] when there is nothing to compare)."""
    examples = load_examples(folders)
    if not examples or not isinstance(spec, dict):
        return []
    worst = None
    for name, ex in examples.items():
        c = compare(spec, ex)
        if c["identical"] and spec.get("_fixture"):
            return [("PASS", f"example-likeness: this is the shipped fixture {name} itself (test build)")]
        why = judge(c)
        if skeleton_only and c["text"] >= TEXT_SHARE:  # the caller's page checker reports copied sentences itself
            why = ""
        if why and (worst is None or c["text"] + c["heads"] > worst[2]["text"] + worst[2]["heads"]):
            worst = (name, why, c)
    if worst:
        left = " 예시 표시(_fixture)도 남아 있어요." if spec.get("_fixture") else ""
        return [("WARN", f"{MSG}: {worst[0]} ({worst[1]}).{left} {FIX}")]
    return [("PASS", f"example-likeness: not a copy of a shipped example ({len(examples)} compared)")]


_DATA_URI = re.compile(r"data:[a-z0-9/+.-]+;base64,[A-Za-z0-9+/=]+")
_UESC = re.compile(r"\\u([0-9a-fA-F]{4})")


def text_of(page: str) -> str:
    """Normalised haystack of a built file: embedded fonts and pictures dropped, tags, entities and \\uXXXX escapes resolved."""
    s = _DATA_URI.sub("", page)
    s = _UESC.sub(lambda m: chr(int(m.group(1), 16)), s)
    s = re.sub(r"<[^>]{0,400}>", " ", s)
    return norm(_html.unescape(s))


def check_text(page: str, folders, fixture_ok: bool = True) -> list[tuple[str, str]]:
    """Same question for a finished file. An unchanged fixture (every sentence present and the page says it is one) passes."""
    examples = load_examples(folders)
    if not examples:
        return []
    hay = text_of(page)
    marked = "_fixture" in page or 'name="ts-fixture"' in page
    worst = None
    for name, ex in examples.items():
        ss = strings(ex)
        if len(ss) < MIN_STRINGS:
            continue
        share = sum(1 for s in ss if s in hay) / len(ss)
        if share >= TEXT_SHARE and (worst is None or share > worst[1]):
            worst = (name, share)
    if worst and worst[1] >= 0.999 and marked and fixture_ok:
        return [("PASS", f"example-likeness: this is the shipped fixture {worst[0]} itself (test build)")]
    if worst:
        left = " 예시 표시(_fixture)도 남아 있어요." if marked else ""
        return [("WARN", f"{MSG}: {worst[0]} (예시 문장의 {round(worst[1] * 100)}%가 그대로 들어 있어요).{left} {FIX}")]
    return [("PASS", f"example-likeness: not a copy of a shipped example ({len(examples)} compared)")]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    target = Path(sys.argv[1])
    raw = target.read_text(encoding="utf-8")
    res = check_spec(json.loads(raw), sys.argv[2:]) if target.suffix == ".json" else check_text(raw, sys.argv[2:])
    for lvl, msg in res:
        print(lvl, msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
