# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Gates found by the v2 comparison: placeholders / pptx text fit, pseudonym-aware privacy + ID columns, game HUD lane.
No browser needed.   Run: py tools/test_gates_v2.py"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SL, DT, GM = (ROOT / "skills" / n for n in ("teacher-slides", "teacher-data", "teacher-game"))
sys.path[:0] = [str(SL / "scripts"), str(DT / "scripts"), str(ROOT / "shared" / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")
import analyze  # noqa: E402
import placeholders as ph  # noqa: E402
import pptx_fit  # noqa: E402
import tdata  # noqa: E402

try:
    import pptx  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False


class Placeholders(unittest.TestCase):
    def test_detects(self):
        for s in ("[학교명] 총회", "20XX학년도", "OO초등학교", "○○ 선생님", "연락처 000-0000-0000", "[날짜]", "학교명을 적어 주세요"):
            self.assertTrue(ph.find(s), s)

    def test_clean_text_passes(self):
        for s in ("2026학년도 학부모 총회", "우리 학교 3학년", "참가비 100,000원, 2000명", "[1] 참고", "[삽입 > 비디오]로 넣어요", "OK 좋아요"):
            self.assertEqual(ph.find(s), [], s)

    def test_fillins_allowed_and_listed(self):
        self.assertEqual(ph.leftovers("[학교 전화번호] 로 문의", ["학교 전화번호"]), [])
        self.assertEqual(ph.fillin_list(["[학교 전화번호] 로 문의"], ["학교 전화번호"]), ["[학교 전화번호]"])
        self.assertTrue(ph.leftovers("[학교 전화번호] [담임 이름]", ["학교 전화번호"]))

    def test_examples_have_none(self):
        for f in (SL / "assets" / "spec-examples").glob("*.json"):
            spec = json.loads(f.read_text(encoding="utf-8"))
            def strings(v):
                if isinstance(v, str):
                    yield v
                elif isinstance(v, dict):
                    for x in v.values():
                        yield from strings(x)
                elif isinstance(v, list):
                    for x in v:
                        yield from strings(x)
            left = [m for s in strings(spec) for m in ph.leftovers(s, spec.get("fillins"))]
            self.assertEqual(left, [], f.name)


class Fit(unittest.TestCase):
    def test_shrinks_long_text(self):
        long = ["가나다라마바사 " * 30]
        size, fits = pptx_fit.fit_size(long, 28, 600, 120)
        self.assertLess(size, 28)
        size2, fits2 = pptx_fit.fit_size(["짧은 글"], 28, 600, 120)
        self.assertEqual((size2, fits2), (28, True))

    def test_hopeless_text_reported(self):
        self.assertFalse(pptx_fit.fit_size(["가" * 800], 28, 300, 60)[1])


@unittest.skipUnless(HAVE, "python-pptx missing")
class PptxGate(unittest.TestCase):
    def build(self, slides, **extra):
        import deck_pptx
        import pptx_check
        spec = {"title": "t", "slides": slides, **extra}
        out = Path(tempfile.mkdtemp()) / "d.pptx"
        rep = deck_pptx.build_pptx(spec, Path("."), out, seed=3)
        self.assertTrue(rep["ok"], rep)
        return rep, pptx_check.check_pptx(out, extra.get("fillins") or [])

    def lvl(self, ck, key):
        return next(lv for lv, m in ck["results"] if key in m)

    def test_placeholder_fails_and_fillin_passes(self):
        sl = [{"type": "title", "title": "총회", "meta": "[학교명] 20XX"}, {"type": "closing", "title": "감사합니다"}]
        _, ck = self.build(sl)
        self.assertEqual(self.lvl(ck, "placeholders"), "FAIL")
        _, ck = self.build([{"type": "title", "title": "총회", "meta": "[학교 전화번호]"}, sl[1]], fillins=["학교 전화번호"])
        self.assertEqual(self.lvl(ck, "placeholders"), "PASS")
        self.assertEqual(ck["fillins"], ["[학교 전화번호]"])

    def test_long_text_is_shrunk_not_overflowing(self):
        rep, ck = self.build([{"type": "title", "title": "총회", "subtitle": "아주 긴 부제 " * 8}, {"type": "closing", "title": "끝"}])
        self.assertTrue(rep["fit"])
        self.assertEqual(self.lvl(ck, "fits its box"), "PASS")


class Privacy(unittest.TestCase):
    def table(self, rows, cols):
        t = tdata.Table(cols, {c: [r[i] for r in rows] for i, c in enumerate(cols)})
        return t

    def rows(self, n=12):
        return [(i + 1, f"학생{i + 1:02d}", 60 + (i % 5) * 4, 70 - (i % 4) * 3) for i in range(n)]

    def test_existing_pseudonyms_recognised(self):
        t = self.table(self.rows(), ["번호", "이름", "국어", "수학"])
        pii = tdata.detect_pii(t)
        self.assertEqual(pii["이름"], "pseudonym")
        self.assertEqual(pii["번호"], "student_id")
        safe, rep = tdata.prepare(t)
        self.assertEqual(list(safe.data["이름"])[:2], ["학생01", "학생02"])  # kept as is
        self.assertNotIn("이름이 보여요", rep["warning"])

    def test_rank_hides_ids_and_numbers(self):
        t = self.table(self.rows(), ["번호", "이름", "국어", "수학"])
        agg = analyze.run(t, {"title": "x", "analyses": [{"id": "a", "type": "overview", "unit": "점"}]})
        rank = next(r for r in agg["results"] if r["type"] == "rank")
        self.assertTrue(all(re.match(r"(상위|하위) \d+위", x) for x in rank["labels"]), rank["labels"])
        self.assertEqual(rank["facts"]["hidden"], True)
        blob = json.dumps(agg, ensure_ascii=False)
        self.assertNotIn("학생0", blob)
        self.assertNotIn("subjects\": [\"번호", blob)

    def test_show_labels_never_shows_id_column(self):
        t = self.table([(2023000 + i, 60 + (i % 5) * 4, 70 - (i % 4) * 3) for i in range(12)], ["학번", "국어", "수학"])
        agg = analyze.run(t, {"title": "x", "analyses": [{"id": "a", "type": "overview", "show_labels": True}]})
        self.assertNotIn("2023", json.dumps(agg, ensure_ascii=False))

    def test_check_report_no_false_fail_on_pseudonyms(self):
        import subprocess
        tmp = Path(tempfile.mkdtemp())
        src = tmp / "s.csv"
        src.write_text("번호,이름,국어,수학\n" + "\n".join(f"{a},{b},{c},{d}" for a, b, c, d in self.rows()), encoding="utf-8")
        agg = analyze.run(tdata.load(src), {"title": "x", "audience": "선생님", "analyses": [{"id": "a", "type": "overview", "unit": "점"}]})
        import report
        page, _ = report.build(agg, "선생님", embed_fonts=False)
        (tmp / "r.html").write_text(page, encoding="utf-8")
        (tmp / "a.json").write_text(json.dumps(agg, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(DT / "scripts" / "check_report.py"), str(tmp / "r.html"), "--agg", str(tmp / "a.json"), "--source", str(src), "--no-play"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, "\n".join(l for l in r.stdout.splitlines() if l.startswith("FAIL")))
        self.assertIn("이미 가명", r.stdout)


class GameHud(unittest.TestCase):
    def test_timer_lane_above_content(self):
        src = (GM / "assets" / "engine.html").read_text(encoding="utf-8")
        m = re.search(r"\.timer\{[^}]*top:(\d+)px[^}]*height:(\d+)px", src)
        self.assertTrue(m)
        self.assertLessEqual(int(m.group(1)) + int(m.group(2)), 126)  # chips row starts at 128
        self.assertIn("hudoverlap", (GM / "scripts" / "check_game.py").read_text(encoding="utf-8"))
        self.assertIn("hud_overlaps", (GM / "scripts" / "design_review.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
