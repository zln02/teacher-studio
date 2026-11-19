#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Make SYNTHETIC practice files (no real people): class unit-test scores (long and wide form), parent survey, 3-month household ledger.

    python3 make_samples.py [out_dir]     # default: ../assets/sample-data

Names, e-mails and phone numbers are randomly assembled; any match with a real person is a coincidence.
"""
from __future__ import annotations

import csv
import datetime as dt
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SURN = "김이박최정강조윤장임한오서신권황안송류홍"
GIVEN = ["하준", "서윤", "도윤", "지안", "시우", "아린", "예준", "수아", "주원", "하린", "유준", "채원", "건우", "다은", "지호", "소율",
         "은우", "나윤", "태오", "이솔", "민재", "보람", "현우", "가온", "라온", "해든", "세아", "우진", "윤슬", "단아"]


def names(rng: random.Random, n: int) -> list[str]:
    seen: set[str] = set()
    while len(seen) < n:
        seen.add(rng.choice(SURN) + rng.choice(GIVEN))
    return sorted(seen)


def scores(out: Path) -> None:
    rng = random.Random(11)
    base = {"1반": (72, 1.5), "2반": (75, 0.5), "3반": (70, 5.2)}
    people = names(rng, 75)
    rows = []
    for ci, (cls, (m, up)) in enumerate(base.items()):
        for nm in people[ci * 25:(ci + 1) * 25]:
            ability = rng.gauss(0, 7)
            sex = rng.choice(["남", "여"])
            for day, bonus in ((dt.date(2026, 10, 21), 0.0), (dt.date(2026, 11, 18), up)):
                sc = max(35, min(100, round(m + ability + bonus + rng.gauss(0, 5))))
                rows.append([nm, cls, sex, day.isoformat(), sc])
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["이름", "반", "성별", "시험일", "점수"])
        w.writerows(rows)


def scores_wide(out: Path) -> None:
    """One row per student, one column per subject (the shape most teachers have): 25 students x 국어·수학·과학·영어."""
    rng = random.Random(31)
    people = names(rng, 25)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["이름", "국어", "수학", "과학", "영어"])
        for nm in people:
            ab = rng.gauss(0, 9)
            w.writerow([nm] + [max(30, min(100, round(m + k * ab + rng.gauss(0, 7)))) for m, k in ((74, 0.7), (70, 1.0), (72, 0.9), (77, 0.5))])


def survey(out: Path) -> None:
    rng = random.Random(23)
    groups = ["저학년", "중학년", "고학년"]
    bias = {"저학년": 0.35, "중학년": 0.1, "고학년": -0.15}
    qs = {"수업": 4.2, "소통": 3.8, "급식": 3.5, "안전": 4.4, "숙제양": 3.2}
    ops = ["선생님이 친절해요", "숙제가 조금 많아요", "급식 메뉴가 다양했으면 해요", "알림장 소통이 좋아요", "", "", "방과후 수업이 늘면 좋겠어요", "운동장이 안전해서 좋아요"]
    rows = []
    start = dt.date(2026, 11, 2)
    for i in range(84):
        g = rng.choices(groups, [30, 28, 26])[0]
        ans = []
        for q, mu in qs.items():
            v = round(rng.gauss(mu + bias[g], 0.85))
            ans.append(max(1, min(5, v)))
        email = f"parent{rng.randint(100, 999)}@example.com" if rng.random() < 0.3 else ""
        rows.append([(start + dt.timedelta(days=rng.randint(0, 9))).isoformat(), g] + ans + [rng.choice(ops), email])
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["응답일", "학년군"] + list(qs) + ["의견", "이메일"])
        w.writerows(rows)


def budget(out: Path) -> None:
    import openpyxl
    rng = random.Random(37)
    cats = {"식비": (9000, 30000, 38), "교통": (1500, 9000, 24), "생활용품": (5000, 40000, 8), "교육": (20000, 120000, 3),
            "문화·여가": (8000, 50000, 8), "의료": (3000, 45000, 4), "통신": (55000, 55000, 1), "기타": (2000, 30000, 6)}
    rows = []
    for mo, extra in ((8, 0), (9, 0), (10, 70000)):
        rows.append([dt.date(2026, mo, 25), "수입", "월급", "월급", 2_600_000])
        if mo == 9:
            rows.append([dt.date(2026, mo, 12), "수입", "부수입", "중고 판매", 85000])
        for cat, (lo, hi, k) in cats.items():
            for _ in range(k if cat != "통신" else 1):
                d = dt.date(2026, mo, rng.randint(1, 28))
                amt = round(rng.randint(lo, hi) / 100) * 100
                if cat == "문화·여가" and mo == 10:
                    amt += extra // 8
                rows.append([d, "지출", cat, f"{cat} 지출", amt])
    rows.sort(key=lambda r: r[0])
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "가계부"
    ws.append(["날짜", "구분", "분류", "내용", "금액"])
    for r in rows:
        ws.append(r)
    wb.save(out)


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "assets" / "sample-data"
    out.mkdir(parents=True, exist_ok=True)
    scores(out / "scores-synthetic.csv")
    scores_wide(out / "scores-wide-synthetic.csv")
    survey(out / "survey-synthetic.csv")
    budget(out / "budget-synthetic.xlsx")
    print("OK", *sorted(p.name for p in out.iterdir()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
