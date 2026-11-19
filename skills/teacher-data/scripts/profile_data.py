#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Profile a CSV/XLSX WITHOUT showing raw rows: columns, types, missing values, units, personal-data warning, 3 masked sample rows.

    python3 profile_data.py data.csv [--sheet 시트] [--yes] [--json]

The AI reads only this output (aggregates + schema), never the file itself. Personal columns (name, phone, e-mail,
student id, address, birth/ID number) are found and pseudonymized in memory before anything is printed.
The original file is never modified. Nothing is sent anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tdata  # noqa: E402


def profile(path: str, sheet: str | None = None, consent: bool = False) -> dict:
    raw = tdata.load(path, sheet, consent)
    if not raw.cols:
        raise ValueError("표가 비어 있어요. 첫 줄에 칸 이름이 있는지 확인해 주세요.")
    safe, rep = tdata.prepare(raw)
    pii = {p["column"]: p["kind"] for p in rep["pii_columns"]}
    cols = []
    for c in safe.cols:
        info = tdata.column_info(c, safe.data[c])
        if c in pii:
            info.update(kind="personal", pii=pii[c])
            info.pop("unique", None)
        elif info["kind"] == "category" and info["unique"] <= 12:
            info["top_values"] = [[k, v] for k, v in Counter(str(x) for x in safe.data[c] if not tdata.is_missing(x)).most_common(8)]
        cols.append(info)
    dup = safe.n - len({tuple(str(safe.data[c][i]) for c in safe.cols) for i in range(safe.n)})
    sample = [{c: (tdata.scrub_text(safe.data[c][i]) if isinstance(safe.data[c][i], str) else str(safe.data[c][i])) for c in safe.cols}
              for i in range(min(3, safe.n))]
    nums = [c["name"] for c in cols if c["kind"] == "number"]
    cats = [c["name"] for c in cols if c["kind"] == "category"]
    dates = [c["name"] for c in cols if c["kind"] == "date"]
    hints = []
    if len(nums) >= 2 and not dates:
        hints.append(f"숫자 칸 {len(nums)}개({', '.join(nums[:5])}) 한꺼번에 살펴보기: 평균·점수대·높은/낮은 쪽·함께 움직임·다음에 할 일 (overview, 첫째로 추천)")
    if cats and nums:
        hints.append(f"{cats[0]}별 {nums[0]} 비교 (groupby)")
    if dates and nums:
        hints.append(f"{dates[0]}에 따른 {nums[0]} 변화 (trend/change)")
    likert = [c["name"] for c in cols if c["kind"] == "number" and c.get("integer_scale") and c.get("max", 0) <= 10]
    if len(likert) >= 2:
        hints.append(f"점수 척도 칸 {len(likert)}개 평균 (likert)")
    if cats:
        hints.append(f"{cats[0]} 분포 (distribution)")
    notes = []
    if dup:
        notes.append(f"똑같은 줄이 {dup}개 있어요")
    worst = [c["name"] for c in cols if c["missing_pct"] >= 20]
    if worst:
        notes.append("빈칸이 많은 칸(20% 이상): " + ", ".join(worst))
    return {"rows": safe.n, "columns": cols, "pii": rep["pii_columns"], "pseudonymized": rep["pseudonymized"], "warning": rep["warning"],
            "duplicate_rows": dup, "sample_rows_masked": sample, "suggested": hints, "notes": notes,
            "privacy": "원본 파일은 바꾸지 않았고, 아무 데로도 보내지 않았어요."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("--sheet")
    ap.add_argument("--yes", action="store_true", help="install openpyxl for .xlsx if missing")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        p = profile(a.data, a.sheet, a.yes)
    except tdata.NeedInstall as e:
        print(json.dumps({"need_install": e.name, "prompt": e.prompt}, ensure_ascii=False))
        return 2
    except (FileNotFoundError, ValueError) as e:
        print(f"FAIL {e}")
        return 1
    if p["warning"]:
        print("WARN " + p["warning"], file=sys.stderr)
    print(json.dumps(p, ensure_ascii=False, indent=None if a.json else 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
