# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""'User wins' switches: safe defaults, and the user can turn them off (each prints a caution).
teacher-data show_ids / show_labels, slides template_blanks, game waive.   Run: py tools/test_user_wins.py"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
for p in (SK / "teacher-data" / "scripts", SK / "teacher-slides" / "scripts", SK / "teacher-game" / "scripts", ROOT / "shared" / "design", ROOT / "shared" / "tools"):
    sys.path.insert(0, str(p))
os.environ.setdefault("PYTHONUTF8", "1")
import analyze  # noqa: E402
import check_game  # noqa: E402
import placeholders  # noqa: E402
import specs  # noqa: E402
import tdata  # noqa: E402

ROWS = [(20230 + i, 50 + i * 4, 90 - i * 3, 60 + (i * 7) % 30) for i in range(1, 11)]


def make_csv() -> Path:
    d = Path(tempfile.mkdtemp())
    f = d / "s.csv"
    f.write_text("학번,국어,수학,과학\n" + "\n".join(",".join(map(str, r)) for r in ROWS) + "\n", encoding="utf-8")
    return f


def rank_result(plan_extra: dict):
    plan = {"analyses": [{"type": "overview", "columns": ["국어", "수학", "과학"], **plan_extra}]}
    agg = analyze.run(tdata.load(make_csv()), plan)
    return agg, next(r for r in agg["results"] if r["type"] == "rank")


class DataIds(unittest.TestCase):
    def test_default_hides_ids(self):
        agg, r = rank_result({})
        blob = json.dumps(agg, ensure_ascii=False)
        self.assertNotIn("2023", blob)
        self.assertIn("상위", r["labels"][0])
        self.assertFalse(agg["meta"].get("shows_ids"))

    def test_show_ids_when_asked(self):
        agg, r = rank_result({"show_ids": True})
        self.assertTrue(any("학번 2023" in x for x in r["labels"]))
        self.assertTrue(agg["meta"]["shows_ids"])
        self.assertIn("밖으로 보내지 마세요", agg["meta"]["caution"])
        self.assertTrue(any("밖으로 보내지" in n for n in r["notes"]))
        self.assertNotIn("records", agg)

    def test_plan_level_show_ids(self):
        plan = {"show_ids": True, "analyses": [{"type": "overview", "columns": ["국어", "수학"]}]}
        agg = analyze.run(tdata.load(make_csv()), plan)
        self.assertTrue(agg["meta"]["shows_ids"])
        analyze._RAW_IDS.clear()


class SlidesBlanks(unittest.TestCase):
    def test_blank_fails_by_default_and_passes_for_template(self):
        self.assertTrue(placeholders.leftovers("[학교명] 20XX학년도"))
        fills = placeholders.with_blanks([], True)
        self.assertEqual(placeholders.leftovers("[학교명] 20XX학년도", fills), [])
        self.assertIn("[학교명]", placeholders.fillin_list(["[학교명] 20XX학년도"], fills))
        self.assertEqual(placeholders.with_blanks(["a"], False), ["a"])

    def test_deck_gate(self):
        import deck
        spec = {"title": "가정통신문", "slides": [{"type": "title", "title": "[학교명] 안내"}]}
        left, _ = deck.placeholder_gate(spec)
        self.assertTrue(left)
        left, listed = deck.placeholder_gate({**spec, "template_blanks": True})
        self.assertEqual(left, [])
        self.assertTrue(listed)


class GameWaive(unittest.TestCase):
    def test_waive_downgrades_only_listed(self):
        res = [("FAIL", "no text overflow / clipped answers: x"), ("FAIL", "top bar parts (timer) never cover"), ("FAIL", "phone 390x844: JavaScript errors: x"),
               ("FAIL", "phone 390x844: every button/answer >= 44px: y"), ("PASS", "ok")]
        out = check_game.apply_waive(res, ["overflow", "phone"])
        self.assertEqual(out[0][0], "WARN")
        self.assertEqual(out[1][0], "FAIL")  # hud not waived
        self.assertEqual(out[2][0], "FAIL")  # JS errors never waived
        self.assertEqual(out[3][0], "WARN")
        self.assertIn("사용자 요청", out[-1][1])
        self.assertEqual(check_game.apply_waive(res, None), res)

    def test_spec_validation(self):
        self.assertTrue(any("waive" in e for e in specs.validate({"mechanic": "quiz", "items": [], "waive": ["contrast"]})))


if __name__ == "__main__":
    unittest.main()
