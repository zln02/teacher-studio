# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""teacher-data 'overview': a wide score table (one column per subject) -> every numeric column in the headline, stats, bands, top/bottom (pseudonyms),
correlation pairs, next steps; check_report static checks PASS for all four audiences; xlsx has native charts.   Run: py tools/test_data_overview.py"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "skills" / "teacher-data"
sys.path[:0] = [str(DATA / "scripts"), str(ROOT / "shared" / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")
import analyze  # noqa: E402
import report  # noqa: E402
import tdata  # noqa: E402

CSV = DATA / "assets" / "sample-data" / "scores-wide-synthetic.csv"
PLAN = json.loads((DATA / "assets" / "spec-examples" / "scores-wide-plan.json").read_text(encoding="utf-8"))
SUBJECTS = ["국어", "수학", "과학", "영어"]


class Overview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agg = analyze.run(tdata.load(CSV), PLAN)
        cls.tmp = Path(tempfile.mkdtemp())
        (cls.tmp / "agg.json").write_text(json.dumps(cls.agg, ensure_ascii=False), encoding="utf-8")

    def test_results(self):
        self.assertEqual([r["type"] for r in self.agg["results"]], ["profile", "bands", "rank", "matrix"])
        prof = self.agg["results"][0]
        self.assertEqual(prof["labels"], SUBJECTS)  # every numeric column, not just the first
        self.assertEqual(len(self.agg["results"][3]["labels"]), 6)  # 4 subjects -> 6 pairs
        self.assertTrue(self.agg["next_steps"])

    def test_headline_covers_all_subjects(self):
        for aud in ("초등", "학부모", "선생님", "전문가"):
            st = report.build_story(self.agg, aud)
            self.assertIn(f"{len(SUBJECTS)}개 과목", st["headline"])
            self.assertTrue(all(c in " ".join(st["summary"]) for c in SUBJECTS[:2]))
            self.assertTrue(all(c in report.texts(self.agg["results"][0], aud)["bullets"][0] for c in SUBJECTS), aud)

    def test_names_hidden(self):
        blob = json.dumps(self.agg, ensure_ascii=False)
        for nm in {str(v) for v in tdata.load(CSV).data["이름"]}:
            self.assertNotIn(nm, blob)
        self.assertIn("상위", self.agg["results"][2]["labels"][0])  # anonymous ranks by default

    def test_check_report_static_all_audiences(self):
        for aud in ("초등", "학부모", "선생님", "전문가"):
            page, _ = report.build(self.agg, aud, embed_fonts=False)
            out = self.tmp / f"{aud}.html"
            out.write_text(page, encoding="utf-8")
            r = subprocess.run([sys.executable, str(DATA / "scripts" / "check_report.py"), str(out), "--agg", str(self.tmp / "agg.json"), "--source", str(CSV), "--no-play"],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, aud + "\n" + "\n".join(l for l in r.stdout.splitlines() if l.startswith("FAIL")))

    def test_xlsx_native_charts(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl missing")
        import export
        x = self.tmp / "r.xlsx"
        export.write(self.agg, str(x), None, "h", ["a", "b", "c"], False)
        wb = openpyxl.load_workbook(x)
        self.assertGreaterEqual(len(wb.sheetnames), 6)
        self.assertEqual(sum(len(ws._charts) for ws in wb), 4)
        self.assertIn("다음에 할 일", wb.sheetnames)


if __name__ == "__main__":
    unittest.main(verbosity=1)
