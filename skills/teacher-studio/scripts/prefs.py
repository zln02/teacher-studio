# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""First-run teacher preferences: school level, main subject, device. Stored locally, no student data, no network.

Usage:
    python3 prefs.py show [--json]             # print saved prefs (exit 0; prints 'unset' if none)
    python3 prefs.py set --level 중학교 --subject 과학 --device board
    python3 prefs.py defaults                  # save the recommended defaults (중학교 / 전과목 / board)
    python3 prefs.py reset                     # forget (for 「설정 바꿔 줘」, then ask again); taste is kept
    python3 prefs.py taste-add "덜 화려하게" "글씨 크게" | taste-show | taste-reset   # 「취향 초기화」

File: ~/.teacher-studio/prefs.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(errors="replace")

PATH = Path.home() / ".teacher-studio" / "prefs.json"
LEVELS = ["초등학교", "중학교", "고등학교", "특수·기타"]
DEVICES = {"board": "칠판 TV", "tablet": "태블릿", "pc": "개인 PC"}
DEFAULTS = {"level": "중학교", "subject": "전과목", "device": "board"}
ALLOWED = set(DEFAULTS)  # only these keys are ever stored


OPPOSITES = [("덜 화려하게", "더 화려하게"), ("단순하게", "풍부하게"), ("글씨 크게", "글씨 작게"),
             ("따뜻한 색", "시원한 색"), ("귀엽게", "고급스럽게"), ("밝게", "어둡게")]
TASTE_MAX = 12


def _raw() -> dict:
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load_taste() -> list:
    """Short style preferences (no personal data), newest last."""
    t = _raw().get("taste")
    return [x for x in t if isinstance(x, str)][:TASTE_MAX] if isinstance(t, list) else []


def add_taste(items) -> list:
    """Append phrases; an opposite phrase replaces its pair. Rejects digits/links/@ (no personal data)."""
    taste = load_taste()
    for it in items:
        it = (it or "").strip()[:20]
        if not it or re.search(r"[0-9@:/]", it):
            continue
        for a, b in OPPOSITES:
            if it in (a, b):
                taste = [x for x in taste if x != (b if it == a else a)]
        if it in taste:
            taste.remove(it)
        taste.append(it)
    taste = taste[-TASTE_MAX:]
    p = load()
    PATH.parent.mkdir(parents=True, exist_ok=True)
    out = {k: v for k, v in p.items() if k in ALLOWED}
    if taste:
        out["taste"] = taste
    PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return taste


def load() -> dict:
    """Return saved prefs (level/subject/device only), or {} when none/unreadable."""
    data = _raw()
    return {k: v for k, v in data.items() if k in ALLOWED and isinstance(v, str)}


def save(prefs: dict) -> None:
    """Write prefs (allowed keys only); the taste list is kept."""
    out = {k: v for k, v in prefs.items() if k in ALLOWED}
    taste = load_taste()
    if taste:
        out["taste"] = taste
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def summary(prefs: dict | None = None) -> str:
    """One Korean line for doctor / cards; empty-state text when unset."""
    p = load() if prefs is None else prefs
    if not p:
        return "아직 없음 (처음 만들 때 한 번만 물어볼게요)"
    return f"{p.get('level', '?')} · {p.get('subject', '?')} · {DEVICES.get(p.get('device', ''), p.get('device', '?'))}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["show", "set", "defaults", "reset", "taste-add", "taste-show", "taste-reset"])
    ap.add_argument("items", nargs="*", help="taste phrases for taste-add")
    ap.add_argument("--level")
    ap.add_argument("--subject")
    ap.add_argument("--device", choices=sorted(DEVICES))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "reset":
        taste = load_taste()
        try:
            PATH.unlink()
        except OSError:
            pass
        if taste:
            add_taste(taste)
        print("설정을 지웠어요.")
    elif a.cmd == "taste-add":
        print("취향 기억:", " · ".join(add_taste(a.items)) or "없음")
    elif a.cmd == "taste-show":
        print(json.dumps(load_taste(), ensure_ascii=False))
    elif a.cmd == "taste-reset":
        p = load()
        try:
            PATH.unlink()
        except OSError:
            pass
        if p:
            save(p)
        print("취향을 초기화했어요.")
    elif a.cmd == "defaults":
        save(DEFAULTS)
        print("추천 설정으로 저장했어요:", summary())
    elif a.cmd == "set":
        p = load()
        for k in ALLOWED:
            v = getattr(a, k)
            if v:
                p[k] = v.strip()[:40]
        save(p)
        print("저장했어요:", summary(p))
    else:
        p = load()
        print(json.dumps(p, ensure_ascii=False) if a.json else summary(p))


if __name__ == "__main__":
    main()
