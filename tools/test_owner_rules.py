# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Owner rules 2026-11-23: the end-of-job delivery menu is ALWAYS shown (even after 「알아서」), and simple requests take the light path
(step aside when the plain agent is already good).   Run: py tools/test_owner_rules.py"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TS = ROOT / "skills" / "teacher-studio"
sys.path.insert(0, str(TS / "scripts"))
os.environ.setdefault("PYTHONUTF8", "1")
import deliver  # noqa: E402
import light_check  # noqa: E402

MENU_HEAD = "✅ 다 만들었어요! 어떻게 받으시겠어요? (추천: "


class DeliveryMenu(unittest.TestCase):
    def test_menu_has_the_five_ways_and_marks_the_made_one(self):
        m = deliver.delivery_menu("game", "tv")
        self.assertTrue(m.startswith(MENU_HEAD + "TV·화면)"))
        for w in ("① TV·화면", "② 단톡방·메신저", "③ 학생 태블릿", "④ 인쇄·PDF", "⑤ 고쳐 쓸 파일(한글·PPT)"):
            self.assertIn(w, m)
        self.assertEqual(m.count("이미 만들어 뒀어요"), 1)
        self.assertIn("개인정보", m)                       # sharing keeps the privacy check first
        self.assertIn("추천: 단톡방·메신저", deliver.delivery_menu("doc"))
        self.assertNotIn("이미 만들어 뒀어요", deliver.delivery_menu("doc"))   # nothing made yet -> no claim

    def test_cli_always_ends_with_the_menu_even_on_auto(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        f = d / "quiz.html"
        f.write_text("<!doctype html><title>빛 퀴즈</title><p>퀴즈</p>", encoding="utf-8")
        for args in (["--use", "auto", "--dry-run"], ["--use", "tv", "--dry-run"], []):
            r = subprocess.run([sys.executable, str(TS / "scripts" / "deliver.py"), str(f)] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertIn(MENU_HEAD, r.stdout, args)

    def test_docs_say_always(self):
        sk = (TS / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ALWAYS close with its menu", sk)
        self.assertIn("ALWAYS, even after 「알아서」", (TS / "references" / "classroom-use.md").read_text(encoding="utf-8"))


class LightPath(unittest.TestCase):
    def test_route(self):
        for req in ("가족 제주 여행 3박 4일 일정표 웹페이지 만들어 줘", "우리 동아리 소개 페이지 하나", "준비물 체크리스트 만들어 줘"):
            self.assertEqual(light_check.route(req), "light", req)
        for req in ("중2 과학 퀴즈 게임 만들어 줘", "학부모 설명회 PPT", "가정통신문 한글 파일로", "이 엑셀 성적 분석해 줘", "만든 페이지 단톡방에 올려 줘",
                    "수업 시작용 뭐 재밌는 거"):
            self.assertEqual(light_check.route(req), "full", req)

    def test_check_catches_privacy_blanks_outside_requests_and_modern_syntax(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        good = d / "good.html"
        good.write_text('<!doctype html><meta name="viewport" content="width=device-width"><title>여행</title><p>12월 3일 제주</p><script>var a = 1;</script>', encoding="utf-8")
        self.assertFalse([m for lv, m in light_check.check(good) if lv == "FAIL"])
        bad = d / "bad.html"
        bad.write_text('<!doctype html><title>t</title><img src="https://x.org/a.png"><p>연락처 010-1234-5678, [학교명]</p><script>var b = a?.c;</script>', encoding="utf-8")
        fails = " ".join(m for lv, m in light_check.check(bad) if lv == "FAIL")
        for w in ("개인정보", "인터넷", "?."):
            self.assertIn(w, fails)
        r = subprocess.run([sys.executable, str(TS / "scripts" / "light_check.py"), str(good)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertIn("RESULT: PASS", r.stdout)
        self.assertIn(MENU_HEAD, r.stdout)

    def test_routing_rule_is_documented(self):
        self.assertIn("references/light-path.md", (TS / "SKILL.md").read_text(encoding="utf-8"))
        ref = (TS / "references" / "light-path.md").read_text(encoding="utf-8")
        for w in ("14 minutes", "44 seconds", "light_check.py", "--route"):
            self.assertIn(w, ref)


if __name__ == "__main__":
    unittest.main()
