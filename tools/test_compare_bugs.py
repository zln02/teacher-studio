# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Bugs found in the fair bare-vs-harness comparison (2026-11-22, scratchpad compare-2026-11-22/summary.md):
docs dropped section content written under items/table, printed a list `lead` as "['…']", numbered headings twice, and still said READY;
the game allowed only 2-4 teams; game decorations overlapped text; 「알아서」 asked nothing.   Run: py tools/test_compare_bugs.py"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "skills" / "teacher-docs" / "scripts"
GAME = ROOT / "skills" / "teacher-game" / "scripts"
sys.path[:0] = [str(DOCS), str(GAME), str(ROOT / "skills" / "teacher-studio" / "scripts")]
os.environ.setdefault("PYTHONUTF8", "1")
import doc_check  # noqa: E402
import docmodel  # noqa: E402

BAD = {"kind": "guide", "org": "우리 학교", "title": "교직원 시설 안전 점검 안내",
       "lead": ["언제: 12. 1.(화) ~ 12. 3.(목)", "어디: 본관 · 체육관 · 급식실"],
       "sections": [{"h": "1. 점검 일정", "table": {"columns": ["날짜", "장소"], "rows": [["12. 1.(화)", "본관 소화기"]]}},
                    {"title": "점검 내용", "items": ["소화기 압력 확인", "비상구 유도등 점등"]},
                    {"h": "협조 사항", "text": "점검 시간에는 해당 공간 사용을 잠시 멈춰 주세요."}],
       "contact": "행정실 시설 담당"}


class DocsKeepContent(unittest.TestCase):
    def lines(self, spec):
        return docmodel.plain_lines(docmodel.build(spec))

    def test_items_table_text_and_list_lead_are_kept(self):
        txt = "\n".join(self.lines(BAD))
        for s in ("본관 소화기", "소화기 압력 확인", "비상구 유도등 점등", "잠시 멈춰 주세요", "어디: 본관"):
            self.assertIn(s, txt)
        self.assertNotIn("['", txt)
        self.assertEqual(docmodel.missing_content(BAD, self.lines(BAD)), [])
        self.assertEqual(docmodel.build(BAD)["meta"]["issues"], [])

    def test_headings_are_numbered_once(self):
        heads = [b["text"] for b in docmodel.build(BAD)["blocks"] if b.get("style") == "heading"]
        self.assertEqual(heads, ["1. 점검 일정", "2. 점검 내용", "3. 협조 사항"])
        rep = dict(docmodel.build({"kind": "report", "title": "t", "sections": [{"h": "Ⅰ. 추진 배경", "body": ["가"]}]}))
        self.assertIn("Ⅰ. 추진 배경", [b["text"] for b in rep["blocks"] if b.get("style") == "heading"])

    def test_notice_and_gongmun_accept_sections(self):
        for kind in ("notice", "gongmun"):
            spec = {"kind": kind, "title": "안내", "sections": [{"h": "일정", "items": ["12. 1.(화) 점검"]}]}
            self.assertIn("12. 1.(화) 점검", "\n".join(self.lines(spec)), kind)

    def test_unknown_keys_fail_loudly(self):
        spec = {"kind": "guide", "title": "t", "sections": [{"h": "일정", "schedule_rows": ["1일"]}], "body": [{"weird": "x"}]}
        issues = docmodel.build(spec)["meta"]["issues"]
        self.assertTrue(any("schedule_rows" in i for i in issues))
        self.assertTrue(any("weird" in i for i in issues))
        self.assertIn("FAIL", [l for l, _ in doc_check.check_content(spec, self.lines(spec))])

    def test_gate_catches_dropped_content_repr_and_double_numbers(self):
        res = doc_check.check_content(BAD, ["교직원 시설 안전 점검 안내", "1. 점검 일정"])
        self.assertEqual([l for l, _ in res], ["PASS", "FAIL"])
        leaks = doc_check.check_leaks(["['언제: 12. 1.', '어디: 본관']", "1. 1. 점검 일정"])
        self.assertEqual([l for l, _ in leaks], ["FAIL", "FAIL"])
        self.assertEqual([l for l, _ in doc_check.check_leaks(["1. 점검 일정", "가. 소화기"])], ["PASS", "PASS"])

    def test_make_end_to_end_is_ready_and_complete(self):
        import subprocess
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        sp = d / "bad.json"
        sp.write_text(json.dumps(BAD, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(DOCS / "docs.py"), "make", "--spec", str(sp), "--out", str(d / "bad.hwpx")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertIn("READY", r.stdout, r.stdout[-800:])
        self.assertIn("content preserved", r.stdout)
        txt = "\n".join(doc_check.texts_of(d / "bad.hwpx"))
        self.assertIn("비상구 유도등 점등", txt)


GAME_SPEC = {"title": "빛의 반사 퀴즈", "mechanic": "quiz", "device": "board", "teams": 6, "timer": 25,
             "items": [{"q": f"문제 {i}번: 입사각과 반사각은?", "choices": ["같다", "다르다", "반대", "없다"], "answer": 0, "exp": "반사 법칙이에요"} for i in range(6)]}


class GameTeamsAndDecor(unittest.TestCase):
    def test_two_to_six_teams(self):
        import specs
        for n in (0, 2, 3, 4, 5, 6):
            self.assertEqual([e for e in specs.validate({**GAME_SPEC, "teams": n}) if e.startswith("teams")], [], n)
        for n in (1, 7):
            self.assertTrue([e for e in specs.validate({**GAME_SPEC, "teams": n}) if e.startswith("teams")], n)
        eng = (ROOT / "skills" / "teacher-game" / "assets" / "engine.html").read_text(encoding="utf-8")
        self.assertIn("opts = [0, 2, 3, 4, 5, 6]", eng)
        self.assertIn(".team:first-child:nth-last-child(n+5)", eng)            # 5-6 teams fit one row
        self.assertIn('"enum": [0, 2, 3, 4, 5, 6]', (ROOT / "skills" / "teacher-game" / "references" / "spec.schema.json").read_text(encoding="utf-8"))

    def test_decorations_yield_and_the_gate_fails_overlaps(self):
        g = ROOT / "skills" / "teacher-game"
        auto = (g / "assets" / "themes" / "auto.js").read_text(encoding="utf-8")
        self.assertIn("hitsBusy(", auto)                 # a prop that would touch words is not drawn
        self.assertIn("clipBusy(ctx, busyRects(t))", auto)  # the signature drawing is clipped out of the word boxes
        self.assertIn("window.__tsDecoRects", auto)
        self.assertIn("ts-yield", (g / "assets" / "components" / "core.js").read_text(encoding="utf-8"))  # host / signs / bubble step back
        chk = (g / "scripts" / "check_game.py").read_text(encoding="utf-8")
        self.assertIn("pg.evaluate(DECO_JS)", chk)
        self.assertIn('out.append(("FAIL" if dv else "PASS", "decorations', chk)
        self.assertIn("TS_GAME_RETRY", (g / "scripts" / "build.py").read_text(encoding="utf-8"))   # our own look is swapped when it overlaps


class AskFirst(unittest.TestCase):
    def build(self, req):
        import direction
        return direction.build(req, {})

    def test_the_comparison_requests_now_ask_the_facts_only_the_user_knows(self):
        d = self.build("다음 주 교직원 대상 시설 안전 점검 일정 안내문 한글 파일로 만들어 줘")
        self.assertEqual(d["mode"], "ask_then_build")
        self.assertIn("date", [q["key"] for q in d["quick_questions"]])
        d = self.build("중2 과학 빛의 반사·굴절 복습 퀴즈 게임 만들어 줘. TV에 띄워서 모둠 대항")
        self.assertEqual([q["key"] for q in d["quick_questions"]][:1], ["teams"])
        self.assertEqual(d["quick_questions"][0]["recommended"], "6모둠")
        d = self.build("가족 제주 여행 3박 4일 일정표 웹페이지 만들어 줘. 부모님이랑 초등학생 아이 둘")
        self.assertIn("date", [q["key"] for q in d["quick_questions"]])       # 「3박 4일」 is a length, not a date
        for d in (self.build("알아서 퀴즈 하나 만들어 줘"), self.build("모둠 대항 퀴즈 알아서 만들어 줘")):
            self.assertLessEqual(d["question_budget"], 2)
            self.assertTrue(d["quick_ask"].startswith("바로 만들게요"))
            for w in ("기획", "콘티", "프롬프트"):
                self.assertNotIn(w, d["quick_ask"])

    def test_said_facts_are_not_asked_again(self):
        for req in ("12월 3일 6모둠 대항 빛 퀴즈 게임, 중2 수업 도입용", "중2 과학 빛과 파동 방탈출, 칠판용"):
            d = self.build(req)
            self.assertEqual(d["question_budget"], 0, req)


if __name__ == "__main__":
    unittest.main()
