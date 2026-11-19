# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Print the empty one-page plan skeleton for 「같이 기획」 (see references/co-plan.md). The model fills it in.

Usage: python3 coplan.py [--title "유튜브 채널 기획"] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SECTIONS = [("goal", "목표", "<한 줄>"), ("audience", "대상", "<누구를 위한 것>"),
            ("options", "방향 3가지", "A <한 줄·장단점> / B <...> (추천) / C <...>"), ("why", "추천 이유", "<한 줄>"),
            ("steps", "할 일 (순서대로)", "1) <누가·언제> 2) 3)"), ("risks", "위험·주의", "<개인정보·저작권·시간 등 1~3개>"),
            ("sources", "출처", "<제목, 링크, 확인한 날짜> (없으면 「출처 없음, 확인 필요」)")]


def skeleton(title: str = "") -> str:
    lines = ["# " + (title or "<제목>")]
    lines += ["%s: %s" % (label, hint) for _k, label, hint in SECTIONS]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--title", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    print(json.dumps({"title": a.title, "sections": [{"key": k, "label": l, "hint": h} for k, l, h in SECTIONS]}, ensure_ascii=False, indent=1) if a.json else skeleton(a.title))
    return 0


if __name__ == "__main__":
    sys.exit(main())
