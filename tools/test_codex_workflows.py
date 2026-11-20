# SPDX-License-Identifier: Apache-2.0
"""Regressions for installation rollback, case routing, and incomplete checks."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def load(path):
    path = ROOT / path
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load("scripts/setup.py")
eval_router = load("tools/router_eval.py")
doctor = load("skills/teacher-studio/scripts/doctor.py")
studio = load("skills/teacher-studio/scripts/studio.py")
webapp = load("skills/teacher-studio/scripts/check_webapp.py")
design_review = load("skills/teacher-game/scripts/design_review.py")
profile = load("skills/teacher-data/scripts/profile_data.py")
law = load("skills/teacher-law/scripts/law_fetch.py")


class InstallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        self.source, self.dest = base / "bundle", base / "user" / ".agents" / "skills"
        for name in setup.SKILL_NAMES:
            for root, value in ((self.source, "새 파일"), (self.dest, "기존 파일")):
                folder = root / name
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(f"---\nname: {name}\n---\n{value}", encoding="utf-8")
        for override in (patch.object(setup, "SKILLS", self.source), patch.dict(setup.TARGETS, {"codex": self.dest})):
            override.start()
            self.addCleanup(override.stop)

    def assert_old_install(self):
        for name in setup.SKILL_NAMES:
            self.assertIn("기존 파일", (self.dest / name / "SKILL.md").read_text(encoding="utf-8"))

    def test_missing_source_leaves_existing_bundle(self):
        (self.source / "teacher-docs" / "SKILL.md").unlink()
        with self.assertRaises(ValueError):
            setup.install("codex")
        self.assert_old_install()

    def test_failed_activation_rolls_back_and_allows_retry(self):
        rename = Path.rename

        def once(src, dst):
            if src.parent.name == "new" and src.name == "teacher-game":
                raise OSError("simulated activation error")
            return rename(src, dst)

        with patch.object(Path, "rename", once), self.assertRaises(OSError):
            setup.install("codex")
        self.assert_old_install()
        with contextlib.redirect_stdout(io.StringIO()):
            setup.install("codex")
        self.assertIn("새 파일", (self.dest / "teacher-game" / "SKILL.md").read_text(encoding="utf-8"))


class CapabilityAndCheckTests(unittest.TestCase):
    def test_doctor_probes_output_and_keeps_host_features_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "한글 작업 공간"
            with patch.object(doctor, "_browser_ready", return_value=False), patch.object(
                doctor.ensure, "status", return_value={"present": [], "on_first_need": [], "network": False}
            ):
                result = doctor.report("codex", output=out, host_skills=["docx"], web_search="yes")
        self.assertTrue(result["writable"])
        self.assertFalse(out.exists())
        self.assertFalse(result["shell_network"])
        self.assertEqual(result["web_search"], "yes")
        self.assertEqual(result["preview"], "unknown")

    def test_webapp_skip_and_failure_are_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            page = Path(temp) / "app.html"
            page.write_text("<!doctype html>", encoding="utf-8")
            with patch.object(webapp, "static_checks", return_value=[]), patch.object(
                webapp, "syntax_checks", return_value=[]
            ), patch.object(webapp, "browser_checks", side_effect=TimeoutError), contextlib.redirect_stdout(io.StringIO()) as log:
                self.assertEqual(webapp.run(page), 2)
                self.assertIn("PARTIAL", log.getvalue())
            with patch.object(webapp, "static_checks", return_value=[("FAIL", "broken")]), patch.object(
                webapp, "syntax_checks", return_value=[]
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(webapp.run(page, browser=False), 1)

    def test_design_review_failure_and_unavailable_exit_codes(self):
        for verdict, code in [("FAIL", 1), ("PARTIAL", 2), ("PASS", 0)]:
            with patch.object(sys, "argv", ["design_review.py", "example.html"]), patch.object(
                design_review, "review", return_value={"verdict": verdict, "hints": []}
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(design_review.main(), code)

    def test_fire_does_not_claim_video_ready_after_encoder_failure(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(
            studio, "_run", side_effect=[0, 0, 1]
        ), contextlib.redirect_stdout(io.StringIO()) as log:
            out = Path(temp) / "화면.html"
            self.assertEqual(studio.cmd_fire("motion/lesson-opening/bold-pop", None, out, False, True), 1)
        self.assertNotIn("\nREADY ", "\n" + log.getvalue())

    def test_trigger_uses_codex_trigger_schema(self):
        case = {"id": "x", "request": "5분 타이머", "trigger": "teacher-class-tools"}
        with patch.object(eval_router, "ask_codex", return_value=('{"skill":"teacher-class-tools"}', 0)) as ask:
            self.assertEqual(eval_router.run_one("codex", case, eval_router.trigger_context(), True)["score"], 1)
        self.assertEqual(ask.call_args.kwargs["schema"], eval_router.TRIGGER_SCHEMA)
        self.assertEqual(eval_router.score_trigger({"trigger": "none"}, {"route": "bare"})["score"], 0)


class DataTests(unittest.TestCase):
    def test_constant_missing_and_extreme_statistics(self):
        stats = profile.tdata
        self.assertIsNone(stats.pearson([1, 1, 1], [1, 2, 3]))
        self.assertAlmostEqual(stats.pearson([1e308, float("inf"), 0, -1e308], [2, 100, 4, 6]), -1)
        self.assertIsNone(stats.welch([1, 1, 1], [5, 5, 5]))
        self.assertIsNone(stats.anova([[1, 1], [], [4, 4]]))
        self.assertIsNone(stats.anova([[1, 1], [4, 4]]))
        sample = stats.welch([1, 2, 3], [2, 3, 4])
        extreme = stats.welch([1e307, 2e307, 3e307], [2e307, 3e307, 4e307])
        self.assertAlmostEqual(sample["t"], -math.sqrt(1.5))
        self.assertAlmostEqual(sample["p"], 0.2878641347)
        self.assertAlmostEqual(sample["p"], extreme["p"])

    def test_profile_outputs_no_row_or_free_text(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "grades.csv"
            path.write_text("이름,수학 점수,메모\n김가상,17,비밀 문구\n이가상,89,다른 문구\n", encoding="utf-8")
            output = json.dumps(profile.profile(str(path)), ensure_ascii=False)
        for sentinel in ("김가상", "17", "89", "비밀", "sample_rows_masked"):
            self.assertNotIn(sentinel, output)


class LawTests(unittest.TestCase):
    def test_partial_fetch_preserves_read_articles_and_missing(self):
        with patch.object(law, "_memo", return_value={}), patch.object(
            law, "_get", side_effect=['<input id="lsiSeq" value="12"><input name="efYd" value="20261120">',
                                      "제1조(시험용 제목) 예시 문장"]
        ):
            result = law.law_articles("시험용 이름", ["1", "2"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["missing"], ["제2조"])
        self.assertEqual(result["articles"][0]["no"], "제1조")


if __name__ == "__main__":
    unittest.main()
