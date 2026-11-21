# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""The one rule for what the user did not give (shared/content/CONTENT-RULES.md, 「Unknowns」; owner's choice 「섞기」,
docs/research/blanks-policy-2026-11.md): example values in the body, blanks only where a hand writes, ONE example note per file,
no 「확인 필요」 filler, no 「교사 초안」 stamp, every example value printed for the last message. Rule text, the shared detector,
the document gate and the PPT gate.   No browser needed.   Run: py tools/test_unknowns_policy.py"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS, SL = ROOT / "skills" / "teacher-docs", ROOT / "skills" / "teacher-slides"
sys.path[:0] = [str(DOCS / "scripts"), str(SL / "scripts"), str(ROOT / "shared" / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")
import doc_check  # noqa: E402
import docmodel  # noqa: E402
import docs  # noqa: E402
import hwpx_edit  # noqa: E402
import placeholders as ph  # noqa: E402

try:
    import pptx  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False

WORK = ROOT / "tools" / ".unknowns-test-work"  # an ordinary folder (an agent's security box cannot write into tempfile.mkdtemp folders)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def notice(**kw) -> dict:
    s = {"kind": "notice", "org": "우리 학교", "title": "3학년 숲 체험 안내", "greeting": "보호자님, 안녕하십니까?",
         "body": ["숲 체험에 참가하려면 아래 동의서를 12. 1.(화)까지 담임 교사에게 내 주세요.",
                  {"table": {"columns": ["구분", "내용"], "rows": [["일시", "2026. 12. 4.(금) 09:00∼12:00"], ["장소", "시립 수목원"], ["참가비", "5,000원"]]}}],
         "date": "2026-11-23", "sender": "우리 학교장",
         "reply": {"title": "숲 체험 참가 동의서", "fields": [["학년 / 반 / 번호", ""], ["학생 이름", ""], ["참가 여부", "□ 참가   □ 불참"]]}}
    s.update(kw)
    return s


class RuleText(unittest.TestCase):
    def test_one_rule_in_content_rules(self):
        t = read("shared/content/CONTENT-RULES.md")
        self.assertIn("## Unknowns — example values in the body, blanks only where a hand writes", t)
        for must in ("a fact the user gave is used as given", "**Body → a plausible example value.**", "**Hand-filled parts → blanks.**",
                     "**One note per file.**", "**The final message lists every example value**", "**The user wins.**"):
            self.assertIn(must, t)
        for gone in ("Release status", "(c) marked 「확인 필요」", "the output is a **「교사 초안」**", "예시(가상 수치)」 on the same screen"):
            self.assertNotIn(gone, t)

    def test_no_file_tells_the_model_to_mark_or_stamp(self):
        # the sentences GPT read literally (docs/research/cross-vendor-fix-2026-11.md, 「빈칸 방식」) are gone from every skill
        bad = ("never fill with a plausible guess", "is a 「교사 초안」", "state it as 「확인 필요」", "Unsure facts -> mark 「확인 필요」",
               "unsure facts -> note 「확인 필요」", "labelled on EVERY slide", "labelled 「교사 초안」", "the deck is a 「교사 초안」")
        for f in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "skills").glob("*/references/content-*.md")) + [ROOT / "shared/content/CONTENT-RULES.md"]:
            t = f.read_text(encoding="utf-8")
            for b in bad:
                self.assertNotIn(b, t, f"{f.relative_to(ROOT)}: {b}")

    def test_docs_skill_applies_the_rule_to_every_format(self):
        t = read("skills/teacher-docs/SKILL.md")
        a, b = t.index("## What the user did not give (every format: HWPX, Word, PDF)"), t.index("## PDF: the short path")
        self.assertLess(a, b)
        self.assertIn("「알아서」", t[a:b])       # was inside the PDF section only, so a HWPX job never read it
        self.assertNotIn("「알아서」", t[b:t.index("## Spec")])
        for must in ('"fillins"', '"reply": false', '"template_blanks": true', "「교사 초안」"):
            self.assertIn(must, t[a:b])

    def test_slides_and_entry_skill_point_to_the_same_rule(self):
        for rel in ("skills/teacher-slides/SKILL.md", "skills/teacher-studio/SKILL.md", "skills/teacher-docs/references/content-docs.md",
                    "skills/teacher-slides/references/content-slides.md"):
            self.assertIn("Unknowns", read(rel), rel)
        s = read("skills/teacher-slides/SKILL.md")
        self.assertIn("first slide's speaker notes", s)
        self.assertIn("a lesson deck is simply filled, no note", s)


class Detector(unittest.TestCase):
    def test_filler_counts_every_cell(self):
        self.assertEqual(len(ph.fillers(["수영장 | 확인 필요", "참가비 | 확인필요", "인원: 집계 필요", "이동 방법 미정"])), 4)
        self.assertEqual(ph.fillers(["확인했습니다", "미정이 학생", "필요한 준비물"]), [])

    def test_stamp(self):
        for s in ("교사 초안 · 배포 전 확인", "【교사용 초안】", "제출 전 검토본", "DRAFT"):
            self.assertTrue(ph.stamps([s]), s)
        self.assertEqual(ph.stamps(["계획서 초안을 함께 검토했습니다", "배포 일정"]), [])

    def test_example_note_lines(self):
        self.assertEqual(ph.example_notes([ph.EXAMPLE_NOTE_DOC]), 1)
        self.assertEqual(ph.example_notes([ph.EXAMPLE_NOTE_DECK]), 1)
        self.assertEqual(ph.example_notes(["자료: 예시 자료(가상 수치), 실제 집계로 교체\n※ 수치는 예시입니다."]), 2)
        self.assertEqual(ph.example_notes(["예시: 사과, 배", "다음 예시를 읽어 봅시다"]), 0)
        # seen in the 2026-11 eval: a report deck that wrote 「자료: 가상 …」 under every table repeats the note on every slide
        self.assertEqual(ph.example_notes(["자료: 가상 잔반 계량대장 · 2026. 11. 20. 집계 기준", "자료: 예시 계량표 (2026. 11. 13.)", "자료: 우리 학교 자체 집계(2026. 11.)"]), 2)

    def test_slip_starts_at_its_heading_not_at_the_title(self):
        L = ["가정통신문", "숲 체험 참가 신청 안내", "동의서를 내 주세요.", "붙임  참가 동의서 1부.", "숲 체험 참가 동의서", "참가 여부 | □ 참가 □ 불참", "보호자 확인:      (서명)"]
        self.assertEqual(ph.slip_start(L), 4)
        self.assertEqual(ph.slip_start(L[:4]), 4)  # no slip: everything is body

    def test_policy_levels(self):
        lv = lambda res, key: next(l for l, m in res if key in m)  # noqa: E731
        self.assertEqual(lv(ph.policy_checks(["확인 필요"]), "빈말"), "WARN")
        self.assertEqual(lv(ph.policy_checks(["확인 필요", "집계 필요\n확인 필요"]), "빈말"), "FAIL")
        self.assertEqual(lv(ph.policy_checks(["확인 필요"] * 5, fillins=[ph.ALLOW_ALL]), "빈말"), "WARN")  # the user asked for a 양식
        self.assertEqual(lv(ph.policy_checks(["교사 초안"]), "도장"), "FAIL")
        self.assertEqual(lv(ph.policy_checks(["가", "나"]), "도장"), "PASS")
        self.assertTrue(any(l == "WARN" and "예시 안내 한 줄이 없어요" in m for l, m in ph.policy_checks(["본문"], fillins=["참가비 5,000원"])))
        self.assertFalse(any("예시 안내" in m for l, m in ph.policy_checks(["본문"], fillins=["참가비 5,000원"], lesson=True)))
        self.assertFalse(any("예시 안내" in m for l, m in ph.policy_checks(["본문"], notes=[ph.EXAMPLE_NOTE_DECK], fillins=["x"], deck=True)))
        self.assertTrue(any(l == "WARN" and "되풀이" in m for l, m in ph.policy_checks(["자료: 예시 자료(가상 수치)", "자료: 예시 자료(가상 수치)"], deck=True)))


class DocGate(unittest.TestCase):
    def setUp(self):
        WORK.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, WORK, True)

    def make(self, spec: dict, name="n.hwpx"):
        out = WORK / name
        r = docs.make(spec, out)
        self.assertTrue(r["ok"], r)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = docs.finish(out, r["kind"], spec)
        return code, buf.getvalue(), hwpx_edit.text(out)

    def test_notice_with_examples_is_ready_with_one_note_before_the_slip(self):
        code, log, lines = self.make(notice(fillins=["체험 날짜 2026. 12. 4.(금)", "장소 시립 수목원", "참가비 5,000원"]))
        self.assertEqual(code, 0, log)
        self.assertIn("READY", log)
        self.assertEqual(ph.example_notes(lines), 1)
        note_at = next(i for i, ln in enumerate(lines) if "예시입니다" in ln)
        self.assertLess(note_at, ph.slip_start(lines))  # at the foot of the body, never inside the part the family writes on
        self.assertIn("바꿔 넣을 곳 (예시로 채운 값", log)
        for item in ("체험 날짜 2026. 12. 4.(금)", "장소 시립 수목원", "참가비 5,000원"):
            self.assertIn(item, log)
        self.assertIn("가정통신문 회신서 있음", log)

    def test_no_examples_no_note(self):
        code, log, lines = self.make(notice())
        self.assertEqual((code, ph.example_notes(lines)), (0, 0), log)
        self.assertNotIn("바꿔 넣을 곳", log)

    def test_own_note_or_switch_is_not_doubled(self):
        own = notice(fillins=["참가비"])
        own["body"].append({"note": "※ 참가비는 예시입니다. 확정 금액으로 바꿔 주세요."})
        self.assertEqual(ph.example_notes(self.make(own)[2]), 1)
        self.assertEqual(ph.example_notes(self.make(notice(fillins=["참가비"], example_note=False))[2]), 0)
        self.assertEqual(ph.example_notes(self.make(notice(fillins=["참가비"], template_blanks=True))[2]), 0)
        for kind in ("guide", "report", "gongmun", "form"):
            sp = {"kind": kind, "org": "우리 학교", "title": "독서 행사 안내", "body": ["일시: 2026. 12. 4.(금) 14:00"], "fields": ["학년 / 반"],
                  "sender": "우리 학교장", "fillins": ["행사 날짜"]}
            self.assertEqual(ph.example_notes(docmodel.plain_lines(docmodel.build(sp))), 1, kind)

    def test_notice_that_asks_but_has_no_reply_slip(self):
        sp = notice()
        del sp["reply"]
        code, log, _ = self.make(sp)
        self.assertEqual(code, 1, log)
        self.assertIn("FAIL 가정통신문에 회신서가 없어요", log)
        self.assertIn("NOT DONE", log)
        code, log, _ = self.make(notice(reply=False))  # the author says there is nothing to answer
        self.assertEqual(code, 0, log)
        self.assertIn("회신서 필요 없음", log)
        quiet = {"kind": "notice", "org": "우리 학교", "title": "겨울 방학 안내", "body": ["방학은 2026. 12. 30.(수)부터입니다."], "sender": "우리 학교장"}
        code, log, _ = self.make(quiet)
        self.assertEqual(code, 0, log)
        self.assertIn("WARN 가정통신문에 회신서가 없어요", log)

    def test_lone_file_without_slip_is_a_warning(self):
        sp = notice()
        del sp["reply"]
        out = WORK / "lone.hwpx"
        self.assertTrue(docs.make(sp, out)["ok"])
        res = doc_check.run(out)  # no spec: a file made by hand or by another tool
        self.assertIn("WARN", [lv for lv, m in res if "회신서가 없어요" in m])
        self.assertFalse(any(lv == "FAIL" for lv, _ in res), res)

    def test_filler_and_stamp(self):
        sp = notice()
        sp["body"][1]["table"]["rows"] = [["일시", "확인 필요"], ["장소", "확인 필요"], ["참가비", "확인 필요"]]
        code, log, _ = self.make(sp)
        self.assertEqual(code, 1)
        self.assertIn("FAIL 「확인 필요」 같은 빈말 3곳", log)
        sp["body"][1]["table"]["rows"] = [["일시", "2026. 12. 4.(금)"], ["장소", "시립 수목원"], ["버스", "확인 필요"]]
        code, log, _ = self.make(sp)
        self.assertEqual(code, 0, log)
        self.assertIn("WARN 「확인 필요」 같은 빈말 1곳", log)
        code, log, _ = self.make(notice(number="교사 초안 · 배포 전 확인"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL 본문에 「교사 초안」 도장 없음", log)

    def test_blanks_only_where_a_hand_writes(self):
        ok = notice()
        ok["reply"]["fields"].append(["보호자 연락처", "__________"])
        code, log, _ = self.make(ok)
        self.assertEqual(code, 0, log)
        self.assertNotIn("밑줄 빈칸", log)
        bad = notice()
        bad["body"].insert(0, "일시: 2026년 ___월 ___일")
        code, log, _ = self.make(bad)
        self.assertEqual(code, 0, log)
        self.assertIn("WARN 본문에 밑줄 빈칸 1곳", log)
        code, log, _ = self.make(dict(bad, template_blanks=True))  # 「빈칸으로 둬」: the user wins
        self.assertNotIn("밑줄 빈칸", log)
        form = {"kind": "form", "org": "우리 학교", "title": "상담 신청서", "fields": ["학년 / 반", ["이름", "__________"]], "to": "우리 학교장"}
        code, log, _ = self.make(form)
        self.assertEqual(code, 0, log)
        self.assertNotIn("밑줄 빈칸", log)


@unittest.skipUnless(HAVE, "python-pptx missing")
class DeckGate(unittest.TestCase):
    def setUp(self):
        WORK.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, WORK, True)

    def build(self, slides, **extra):
        import deck
        import deck_pptx
        import pptx_check
        spec = {"title": "운영 결과", "slides": slides, **extra}
        added = deck.example_note(spec)
        out = WORK / "d.pptx"
        rep = deck_pptx.build_pptx(spec, Path("."), out, seed=3)
        self.assertTrue(rep["ok"], rep)
        return added, pptx_check.check_pptx(out, extra.get("fillins") or [], lesson=extra.get("context") == "class"), out

    SL = [{"type": "title", "title": "방과후학교 운영 결과"},
          {"type": "table", "title": "참여 학생", "columns": ["구분", "인원"], "rows": [["1학기", "120명"], ["2학기", "134명"]]},
          {"type": "closing", "title": "감사합니다"}]

    def msgs(self, ck, key):
        return [(lv, m) for lv, m in ck["results"] if key in m]

    def test_example_note_goes_to_the_first_slides_notes_once(self):
        from pptx import Presentation
        added, ck, out = self.build(json.loads(json.dumps(self.SL)), fillins=["참여 학생 수 120명·134명"])
        self.assertTrue(added)
        prs = Presentation(str(out))
        notes = [s.notes_slide.notes_text_frame.text if s.has_notes_slide else "" for s in prs.slides]
        self.assertEqual(ph.example_notes(notes[:1]), 1)
        self.assertEqual(ph.example_notes(notes[1:]), 0)
        self.assertFalse(self.msgs(ck, "예시 안내"), ck["results"])       # present once, not on the slides: nothing to say
        self.assertEqual(self.msgs(ck, "빈말")[0][0], "PASS")

    def test_lesson_deck_and_template_get_no_note(self):
        self.assertFalse(self.build(json.loads(json.dumps(self.SL)), fillins=["x"], context="class")[0])
        self.assertFalse(self.build(json.loads(json.dumps(self.SL)), fillins=["x"], template_blanks=True)[0])
        self.assertFalse(self.build(json.loads(json.dumps(self.SL)))[0])
        own = json.loads(json.dumps(self.SL))
        own[1]["footnote"] = "※ 수치는 예시입니다. 실제 집계로 바꿔 주세요."
        self.assertFalse(self.build(own, fillins=["참여 학생 수"])[0])      # the author already wrote the one line under the first table

    def test_filler_stamp_and_repeats(self):
        sl = json.loads(json.dumps(self.SL))
        sl[1]["rows"] = [["1학기", "확인 필요"], ["2학기", "집계 필요"], ["합계", "확인 필요"]]
        _, ck, _ = self.build(sl)
        self.assertEqual(self.msgs(ck, "빈말")[0][0], "FAIL")
        sl = json.loads(json.dumps(self.SL))
        sl[0]["subtitle"] = "교사 초안"
        _, ck, _ = self.build(sl)
        self.assertEqual(self.msgs(ck, "도장")[0][0], "FAIL")
        sl = json.loads(json.dumps(self.SL))
        sl.insert(2, {"type": "table", "title": "예산", "columns": ["항목", "금액"], "rows": [["강사비", "300만 원"]], "footnote": "예시 자료(가상 수치), 실제 집계로 교체"})
        sl[1]["footnote"] = "예시 자료(가상 수치), 실제 집계로 교체"
        _, ck, _ = self.build(sl)
        self.assertEqual(self.msgs(ck, "되풀이")[0][0], "WARN")


if __name__ == "__main__":
    unittest.main(verbosity=1)
