#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Aggregates -> .xlsx (with live formulas + a chart per sheet) and a flat .csv. Raw rows are never written; only aggregates."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tdata  # noqa: E402


def write_csv(agg: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["분석", "항목", "계열", "값", "단위"])
        for r in agg["results"]:
            for s in r["series"]:
                for lab, v in zip(r["labels"], s["values"]):
                    w.writerow([r["title"], lab, s["name"], "" if v is None else v, r.get("unit", "")])


def _col(n: int) -> str:
    s = ""
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def write_xlsx(agg: dict, path: str, headline: str, summary: list[str], consent: bool = False) -> None:
    try:
        import openpyxl
    except ImportError:
        import ensure
        res = ensure.ensure("openpyxl", consent=consent)
        if not res["ok"]:
            raise tdata.NeedInstall(res["prompt"], "openpyxl")
        import openpyxl
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws0 = wb.active
    ws0.title = "요약"
    bold = Font(bold=True)
    ws0["A1"], ws0["A1"].font = agg["title"], Font(bold=True, size=16)
    ws0["A3"], ws0["A3"].font = "한 줄 결론", bold
    ws0["A4"] = headline
    ws0["A6"], ws0["A6"].font = "세 줄 요약", bold
    for i, s in enumerate(summary):
        ws0.cell(row=7 + i, column=1, value=f"{i + 1}. {s}")
    ws0["A11"] = "표의 파란 글씨 칸은 계산식이에요. 숫자를 바꾸면 결과도 같이 바뀌어요. 원본 줄(학생 이름 등)은 이 파일에 없어요."
    ws0.column_dimensions["A"].width = 100
    head_fill = PatternFill("solid", fgColor="DDE7F5")
    blue = Font(color="1F4FBF")
    for k, r in enumerate(agg["results"], 1):
        ws = wb.create_sheet(f"분석{k}")
        cols, rows = list(r["table"]["columns"]), [list(x) for x in r["table"]["rows"]]
        ws["A1"], ws["A1"].font = r["title"], Font(bold=True, size=13)
        hr = 3
        extra: list[str] = []
        t, f = r["type"], r["facts"]
        n = len(rows)
        first, last = hr + 1, hr + n
        if t == "groupby" or t == "distribution":
            if t == "distribution" or f.get("agg") in ("sum", "count"):
                cols.append("차지하는 비율(%)")
        if t == "trend":
            cols.append("앞 기간보다 늘어난 양")
        for j, c in enumerate(cols, 1):
            cell = ws.cell(row=hr, column=j, value=c)
            cell.font, cell.fill = bold, head_fill
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        for i, row in enumerate(rows):
            rr = hr + 1 + i
            for j, v in enumerate(row, 1):
                ws.cell(row=rr, column=j, value=v)
            if t == "change":
                ws.cell(row=rr, column=4, value=f"=C{rr}-B{rr}").font = blue
            if t == "groupby" and f.get("agg") in ("sum", "count") or t == "distribution":
                ws.cell(row=rr, column=len(cols), value=f"=B{rr}/SUM(B${first}:B${last})*100").font = blue
            if t == "trend" and i > 0:
                ws.cell(row=rr, column=len(cols), value=f"=B{rr}-B{rr - 1}").font = blue
        sr = last + 2
        if t == "groupby" and f.get("agg") == "mean":
            ws.cell(row=sr, column=1, value="전체 평균(사람 수로 가중)").font = bold
            ws.cell(row=sr, column=2, value=f"=SUMPRODUCT(B{first}:B{last},C{first}:C{last})/SUM(C{first}:C{last})").font = blue
            ws.cell(row=sr + 1, column=1, value="가장 높은 곳 − 가장 낮은 곳").font = bold
            ws.cell(row=sr + 1, column=2, value=f"=MAX(B{first}:B{last})-MIN(B{first}:B{last})").font = blue
        elif t == "groupby" or t == "distribution":
            ws.cell(row=sr, column=1, value="합계").font = bold
            ws.cell(row=sr, column=2, value=f"=SUM(B{first}:B{last})").font = blue
        elif t == "trend":
            ws.cell(row=sr, column=1, value="합계" if f.get("agg") in ("sum", "count") else "평균").font = bold
            fn = "SUM" if f.get("agg") in ("sum", "count") else "AVERAGE"
            ws.cell(row=sr, column=2, value=f"={fn}(B{first}:B{last})").font = blue
        elif t == "likert":
            ws.cell(row=sr, column=1, value="전체 평균").font = bold
            ws.cell(row=sr, column=2, value=f"=AVERAGE(B{first}:B{last})").font = blue
        elif t == "change":
            ws.cell(row=sr, column=1, value="가장 많이 오른 곳").font = bold
            ws.cell(row=sr, column=2, value=f"=INDEX(A{first}:A{last},MATCH(MAX(D{first}:D{last}),D{first}:D{last},0))").font = blue
        for j in range(1, len(cols) + 1):
            ws.column_dimensions[_col(j)].width = 22 if j > 1 else 26
        for nt in r.get("notes", []):
            sr += 1 if nt is r["notes"][0] else 1
        if t in ("groupby", "distribution", "likert", "change", "trend", "correlation") and n >= 2:
            ch = LineChart() if r.get("chart") == "line" else BarChart()
            ch.title, ch.height, ch.width = r["title"], 8, 16
            ns = len(r["series"])
            ch.add_data(Reference(ws, min_col=2, max_col=1 + ns, min_row=hr, max_row=last), titles_from_data=True)
            ch.set_categories(Reference(ws, min_col=1, min_row=first, max_row=last))
            ws.add_chart(ch, f"{_col(len(cols) + 2)}3")
    wb.calculation.fullCalcOnLoad = True
    wb.save(path)


def write(agg: dict, xlsx: str | None, csv_path: str | None, headline: str, summary: list[str], consent: bool = False) -> None:
    if csv_path:
        write_csv(agg, csv_path)
    if xlsx:
        write_xlsx(agg, xlsx, headline, summary, consent)
