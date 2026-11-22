# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""2026-11 upgrade: calibrated speed check (no FAIL from a slow test PC), question-quality gate, official article text, lean recipes.

    py tools/test_fable_upgrade.py        # no browser, no network
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
sys.path.insert(0, str(ROOT / "shared" / "juice"))
sys.path.insert(0, str(SK / "teacher-game" / "scripts"))
sys.path.insert(0, str(SK / "teacher-law" / "scripts"))
import juice_lint  # noqa: E402
import law_fetch  # noqa: E402
import specs  # noqa: E402

GOOD_ENV = {"fps": 60.0, "ratio": 4.2, "ok": True}
SLOW_ENV = {"fps": 22.0, "ratio": 9.5, "ok": False}


def levels(res):
    return [lv for lv, _ in res]


class SpeedVerdict(unittest.TestCase):
    def test_light_page_low_fps_is_a_warning_not_a_failure(self):
        res = juice_lint.speed_verdict(12.0, 11.0, 10.5, GOOD_ENV, 4)  # this PC: software drawing, light page
        self.assertEqual(levels(res), ["PASS", "WARN"])
        self.assertIn("Not a build failure", res[1][1])

    def test_smooth_run_passes_both(self):
        self.assertEqual(levels(juice_lint.speed_verdict(58.0, 59.0, 6.0, GOOD_ENV, 4)), ["PASS", "PASS"])

    def test_heavy_page_fails_only_on_a_pc_that_can_judge(self):
        self.assertEqual(levels(juice_lint.speed_verdict(9.0, 8.0, 80.0, GOOD_ENV, 4))[0], "FAIL")
        slow = juice_lint.speed_verdict(1.4, 1.0, 109.6, SLOW_ENV, 4)  # measured while another job hogged the PC
        self.assertNotIn("FAIL", levels(slow))
        self.assertIn("too slow or busy", slow[0][1])

    def test_missing_metrics_never_fail(self):
        self.assertNotIn("FAIL", levels(juice_lint.speed_verdict(10.0, 10.0, None, GOOD_ENV, 4)))

    def test_skill_copies_match_shared(self):
        src = (ROOT / "shared" / "juice" / "juice_lint.py").read_bytes()
        for s in ("teacher-game", "teacher-class-tools"):
            self.assertEqual((SK / s / "shared" / "juice" / "juice_lint.py").read_bytes(), src, s)


def quiz(items, **kw):
    d = {"title": "t", "mechanic": "quiz", "use": "class", "device": "board", "items": items}
    d.update(kw)
    return d


def q(text, choices, answer=0, exp="까닭을 한 줄로 말해요"):
    return {"q": text, "choices": choices, "answer": answer, "exp": exp}


class ContentReview(unittest.TestCase):
    def test_every_example_spec_is_clean(self):
        for f in sorted((SK / "teacher-game" / "assets" / "spec-examples").glob("*.json")):
            self.assertEqual(specs.content_review(json.loads(f.read_text(encoding="utf-8"))), [], f.name)

    def test_longest_answer_giveaway(self):
        items = [q(f"문제 {i}", ["아주 길고 자세한 정답 설명", "짧다", "작다", "없다"]) for i in range(6)]
        self.assertTrue(any("longest" in a for a in specs.content_review(quiz(items))))

    def test_catch_all_missing_exp_label_exp_duplicates(self):
        items = [q("물이 어는 현상은?", ["응고", "증발", "모두 정답"]), q("물이 어는 현상은?", ["응고", "융해"], exp=""),
                 q("빛이 꺾이는 현상은?", ["굴절", "반사"], exp="굴절: 빛이 꺾여요")]
        adv = " | ".join(specs.content_review(quiz(items)))
        for word in ("catch-all", "no `exp`", "as a label", "same sentence"):
            self.assertIn(word, adv)

    def test_long_text_negatives_and_timer(self):
        items = [q("다음 중 옳지 않은 것은 무엇인지 아주 길게 풀어서 쓴 문제 문장이라서 뒷자리에서는 읽기 어려워요 정말로요", ["가", "나"]) for _ in range(1)]
        items += [q(f"{i}번 중 아닌 것은?", ["이것은 열여섯 글자를 훌쩍 넘는 긴 보기입니다", "나"]) for i in range(5)]
        adv = " | ".join(specs.content_review(quiz(items, teams=3)))
        for word in ("over 48 characters", "over 16 characters", "WRONG one", "timer"):
            self.assertIn(word, adv)

    def test_personal_quiz_needs_no_exp(self):
        self.assertEqual(specs.content_review(quiz([q("우리 집 막내 별명은?", ["콩이", "두부"], exp="")] * 1, use="personal")), [])

    def test_build_stops_fast_then_ok_content_builds(self):
        items = [q(f"문제 {i}은?", ["가", "나"], exp="") for i in range(4)]
        with tempfile.TemporaryDirectory() as t:
            sp, out = Path(t) / "s.json", Path(t) / "g.html"
            sp.write_text(json.dumps(quiz(items), ensure_ascii=False), encoding="utf-8")
            cmd = [sys.executable, str(SK / "teacher-game" / "scripts" / "build.py"), "--spec", str(sp), "--out", str(out), "--no-fonts"]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 3, r.stdout)
            self.assertIn("CONTENT FIX", r.stdout)
            self.assertFalse(out.exists())
            r = subprocess.run(cmd + ["--no-check"], capture_output=True, text=True, encoding="utf-8", errors="replace")  # dev path: advice only
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("CONTENT (kept as is)", r.stdout)
            self.assertTrue(out.exists())

    def test_missing_or_broken_spec_is_a_hint_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as t:
            bad = Path(t) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            for sp in (Path(t) / "none.json", bad):
                r = subprocess.run([sys.executable, str(SK / "teacher-game" / "scripts" / "build.py"), "--spec", str(sp), "--out", str(Path(t) / "x.html")],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                self.assertEqual(r.returncode, 2)
                self.assertIn("SPEC FIX NEEDED", r.stdout)
                self.assertNotIn("Traceback", r.stdout + r.stderr)


LAW_TEXT = ("제24조의2(공공저작물의 자유이용) ① 국가는 … 제25조제3항에 따라 … "
            "제25조( 학교교육 목적 등에의 이용 ) ① 교과용도서에는 공표된 저작물을 게재할 수 있다. ③ 수업 목적으로 … "
            "제26조(시사보도를 위한 이용) 방송ㆍ신문 … 제35조의5(저작물의 공정한 이용) ① 저작물을 이용할 수 있다. 제36조(번역 등에 의한 이용) ①")


class LawArticles(unittest.TestCase):
    def test_heading_not_reference_and_stops_at_next_article(self):
        blk = law_fetch.cut_article(LAW_TEXT, "25")
        self.assertTrue(blk.startswith("제25조( 학교교육"))
        self.assertIn("수업 목적", blk)
        self.assertNotIn("시사보도", blk)

    def test_branch_article_and_missing(self):
        self.assertTrue(law_fetch.cut_article(LAW_TEXT, "35의5").startswith("제35조의5(저작물의 공정한 이용)"))
        self.assertEqual(law_fetch.cut_article(LAW_TEXT, "999"), "")
        self.assertEqual(law_fetch.art_no("35의5"), "제35조의5")
        self.assertEqual(law_fetch.art_no("제25조".replace("제", "")), "제25조")

    def test_long_article_is_cut_with_a_note(self):
        blk = law_fetch.cut_article("제1조(목적) " + "가" * 3000 + " 제2조(정의) 나", "1", chars=200)
        self.assertLess(len(blk), 260)
        self.assertIn("이하 줄임", blk)


class LeanRecipes(unittest.TestCase):
    def test_skill_files_stay_small_and_name_the_one_command(self):
        # 2026-11 blanks policy: +~250 bytes in the entry skill for the one unknowns rule. 2026-11 cross-vendor fix: +~900 bytes each for the "floor, not ceiling" rule and the NO-BROWSER line (details live in references/)
        limits = {"teacher-game": 12300, "teacher-law": 7000, "teacher-studio": 16500}
        for name, cap in limits.items():
            self.assertLess(len((SK / name / "SKILL.md").read_bytes()), cap, name)
        game = (SK / "teacher-game" / "SKILL.md").read_text(encoding="utf-8")
        for needle in ("--review", "--ok-content", "helper agent", "READY", "Last message"):
            self.assertIn(needle, game)
        law = (SK / "teacher-law" / "SKILL.md").read_text(encoding="utf-8")
        for needle in ("--articles", "법률 자문이 아니에요", "확인한 날", "250 words"):
            self.assertIn(needle, law)

    def test_router_is_three_first_match_lists(self):
        sk = (SK / "teacher-studio" / "SKILL.md").read_text(encoding="utf-8")
        for needle in ("## Decision 1", "## Decision 2", "## Decision 3", "FIRST line that matches", "quick_ask"):
            self.assertIn(needle, sk)


if __name__ == "__main__":
    unittest.main(verbosity=2)
