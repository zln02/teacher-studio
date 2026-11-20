# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""No-regret fixes after the ceiling eval (docs/research/ceiling-eval-2026-11/rerun-ppt-pdf.md):
placeholder slots like (학교명 입력) / ○○학교 / (예시), the .pptx hard gate (NOT DONE), the empty-looking-slide check, the
approximate preview that now draws tables / charts / lines / pictures, the `diagram` slide and the quiz answer slide,
and the documents path: font size, page break, QR / image blocks, 신청서 (form / reply page), page-count and smallest-text checks.
No browser, no network.   Run: py tools/test_ppt_pdf_rerun.py"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "skills" / "teacher-slides"
DOCS = ROOT / "skills" / "teacher-docs"
sys.path[:0] = [str(SLIDES / "scripts"), str(DOCS / "scripts"), str(ROOT / "shared" / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")
import placeholders as ph  # noqa: E402

try:
    import pptx  # noqa: F401
    HAVE_PPTX = True
except ImportError:
    HAVE_PPTX = False


def have(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


class Placeholders(unittest.TestCase):
    def test_new_slots_are_caught(self):
        for s in ("(학교명 입력)", "(기관명을 입력하세요)", "○○학교", "OOO 선생님", "(예시)", "[교육지원청명을 넣어 주세요]", "△△부", "<학교명>",
                  "(추후 확정)", "00월 00일", "0월 0일", "여기에 내용을 입력", "(날짜 기입)", "(실제 값으로 바꿔 주세요)", "(수정 필요)", "(미정)"):
            self.assertTrue(ph.find(s), s)

    def test_ordinary_text_is_not_a_slot(self):
        for s in ("우리 학교", "2026. 11. 20.", "10월 20일", "예시 자료(가상 수치)", "(공기 → 물)", "성명: ______ (서명)", "교사: ________", "________ 중학교", "결석 0일", "(활동지에 적어 보기)",
                  "물을 컵에 넣어 주세요", "(학생이 직접 작성)", "○ 추진 배경", "□ 요약", "(단위: 명)", "a < b > c", "(뒷면)", "1,000명", "30.0%"):
            self.assertEqual(ph.find(s), [], s)

    def test_one_detector_for_slides_and_docs(self):
        self.assertEqual((ROOT / "shared" / "tools" / "placeholders.py").read_bytes(), (SLIDES / "scripts" / "placeholders.py").read_bytes())


@unittest.skipUnless(HAVE_PPTX, "python-pptx not installed")
class PptxGate(unittest.TestCase):
    def _deck(self, spec, td):
        import deck_pptx
        out = Path(td) / "d.pptx"
        rep = deck_pptx.build_pptx(spec, Path(td), out, 7)
        self.assertTrue(rep["ok"], rep.get("errors"))
        return out, rep

    def test_slot_text_fails_and_the_file_is_not_done(self):
        import pptx_check
        spec = {"title": "t", "slides": [{"type": "title", "title": "추진 현황", "subtitle": "(학교명 입력)"},
                                         {"type": "bullets", "title": "배경", "items": ["○○학교 사례", "둘째 항목", "셋째 항목"]}, {"type": "closing", "title": "감사합니다"}]}
        with tempfile.TemporaryDirectory() as td:
            out, _ = self._deck(spec, td)
            r = pptx_check.check_pptx(out)
            lv = dict((m.split(" (")[0].split(":")[0], l) for l, m in r["results"])
            self.assertEqual(lv["no placeholders left"], "FAIL")
            main = (SLIDES / "scripts" / "pptx_check.py").read_text(encoding="utf-8")
            self.assertIn("NOT DONE", main)
            self.assertIn("NOT DONE", (SLIDES / "scripts" / "deck.py").read_text(encoding="utf-8"))

    def test_empty_looking_slide_fails(self):
        from pptx import Presentation
        from pptx.util import Inches, Pt
        import pptx_fill
        prs = Presentation()
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
        for k in range(4):
            s = prs.slides.add_slide(prs.slide_layouts[6])
            tb = s.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11), Inches(1))
            tb.text_frame.text = "제목이 있는 장 %d" % k
            tb.text_frame.paragraphs[0].runs[0].font.size = Pt(34)
            if k != 2:  # slide 3 keeps only a title and one short line near the top
                for j in range(4):
                    b = s.shapes.add_textbox(Inches(0.8), Inches(2 + j * 1.2), Inches(11), Inches(1))
                    b.text_frame.text = "내용이 충분히 들어 있는 줄입니다. 설명이 이어지고 예시도 있습니다."
                    b.text_frame.paragraphs[0].runs[0].font.size = Pt(22)
            else:
                b = s.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11), Inches(0.8))
                b.text_frame.text = "여기에는 본문이 두 줄뿐이라서 화면의 아래쪽이 텅 비어 보입니다. 다음 장과 합치면 좋습니다."
                b.text_frame.paragraphs[0].runs[0].font.size = Pt(20)
        bad = [n for n, _ in pptx_fill.problems(prs)]
        self.assertEqual(bad, [3])

    def test_examples_have_no_empty_looking_slides(self):
        from pptx import Presentation
        import pptx_fill
        for f in sorted((SLIDES / "assets" / "spec-examples" / "context").glob("*.json")):
            spec = json.loads(f.read_text(encoding="utf-8"))
            with tempfile.TemporaryDirectory() as td:
                import deck_pptx
                out = Path(td) / "d.pptx"
                rep = deck_pptx.build_pptx(spec, f.parent, out, spec.get("seed") or 7)
                self.assertTrue(rep["ok"], (f.name, rep.get("errors")))
                self.assertEqual(pptx_fill.problems(Presentation(str(out))), [], f.name)

    def test_diagram_and_quiz_answer_slide(self):
        from pptx import Presentation
        spec = json.loads((SLIDES / "assets" / "spec-examples" / "context" / "class-light-reflection.json").read_text(encoding="utf-8"))
        n_quiz = sum(1 for s in spec["slides"] if s["type"] == "quiz")
        with tempfile.TemporaryDirectory() as td:
            out, rep = self._deck(spec, td)
            prs = Presentation(str(out))
            self.assertEqual(rep["slides"], len(prs.slides))
            texts = ["\n".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame) for s in prs.slides]
            ans = [t for t in texts if "확인 문제 정답" in t]
            self.assertEqual(len(ans), 1)                       # one answers slide, before the closing
            self.assertEqual(ans[0].count("정답 "), n_quiz)       # one answer line per question
            self.assertIn("확인 문제 정답", texts[-2])
            xml = "".join(s._element.xml for s in prs.slides)
            self.assertIn("<p:cxnSp>", xml)       # rays are real lines
            self.assertIn("tailEnd", xml)         # with arrow heads
            self.assertIn('prst="arc"', xml)      # angle marks

    def test_target_slides_stops_a_deck_that_runs_long(self):
        import deck_context as dctx
        base = {"context": "class", "target_slides": 4, "slides": [{"type": "title", "title": "t"}] + [{"type": "bullets", "title": "a", "items": ["x", "y"]}] * 5}
        self.assertTrue(any("요청 4장" in e for e in dctx.lint(base)[0]))
        self.assertFalse([e for e in dctx.lint({**base, "target_slides": 6})[0] if "요청" in e])

    def test_diagram_spec_errors_are_fix_lines(self):
        import deck_spec
        bad = {"slides": [{"type": "diagram", "title": "그림", "shapes": [{"kind": "blob", "x": 1, "y": 1}, {"kind": "line", "x1": 0, "y1": 0, "x2": 300, "y2": 10}]}]}
        _s, _w, errs = deck_spec.normalize(bad)
        self.assertTrue(any("kind" in e for e in errs))
        self.assertTrue(any("outside the canvas" in e for e in errs))

    def test_preview_draws_tables_charts_and_lines(self):
        from pptx import Presentation
        import pptx_draw
        spec = json.loads((SLIDES / "assets" / "spec-examples" / "context" / "public-ai-edu-report.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            out, _ = self._deck(spec, td)
            prs = Presentation(str(out))
            html = "".join(pptx_draw.slide_html(prs, s) for s in prs.slides)
        self.assertIn("<table", html)                                   # native tables
        self.assertRegex(html, r"<svg[^>]*viewBox[^>]*>.*?<rect")        # chart bars
        self.assertNotIn(">차트 (", html)                                # no chart fell back to a grey box
        spec2 = json.loads((SLIDES / "assets" / "spec-examples" / "context" / "class-light-reflection.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            out, _ = self._deck(spec2, td)
            prs = Presentation(str(out))
            html = "".join(pptx_draw.slide_html(prs, s) for s in prs.slides)
        self.assertIn("marker-end", html)                               # arrows
        self.assertIn("stroke-dasharray", html)                         # the dashed normal

    def test_preview_draws_pictures(self):
        from PIL import Image
        from pptx import Presentation
        from pptx.util import Inches
        import pptx_draw
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "p.png"
            Image.new("RGB", (40, 30), (200, 30, 30)).save(img)
            prs = Presentation()
            s = prs.slides.add_slide(prs.slide_layouts[6])
            s.shapes.add_picture(str(img), Inches(1), Inches(1), Inches(3), Inches(2))
            self.assertIn("data:image/png;base64,", pptx_draw.slide_html(prs, s))


class SkillText(unittest.TestCase):
    def test_slides_skill_claims_powerpoint_and_names_the_gate(self):
        t = (SLIDES / "SKILL.md").read_text(encoding="utf-8")
        desc = re.search(r"^description:\s*(.*)$", t, re.M).group(1)
        for w in ("PPT", "PowerPoint", ".pptx", "파워포인트", "before any generic pptx skill"):
            self.assertIn(w, desc)
        self.assertLessEqual(len(desc), 1024)
        for w in ("NOT DONE", "READY", "--pptx-only", "pptx_check.py", "우리 학교", "diagram", "explain"):
            self.assertIn(w, t)

    def test_docs_skill_names_the_one_command_and_the_look(self):
        t = (DOCS / "SKILL.md").read_text(encoding="utf-8")
        for w in ("docs.py append", "preview.png", "max_pages", "font_size", "pagebreak", '"qr"', "NOT DONE"):
            self.assertIn(w, t)


class DocsPath(unittest.TestCase):
    def test_font_size_scales_every_style(self):
        import doc_html
        import docmodel
        spec = {"kind": "guide", "title": "안내", "body": ["첫째 항목입니다", "둘째 항목입니다"], "design": {"font_size": "large"}}
        m = docmodel.build(spec)
        self.assertAlmostEqual(m["meta"]["scale"], 14 / 12.5)
        h = doc_html.render(m, embed_fonts=False)
        self.assertIn("font-size:14pt", h)        # body 12.5 -> 14
        self.assertIn("font-size:22.4pt", h)      # title 20 -> 22.4
        self.assertEqual(docmodel.build({"kind": "guide", "title": "a", "body": ["x", "y"]})["meta"]["scale"], 1.0)

    def test_pagebreak_image_qr_and_form_blocks(self):
        import doc_html
        import docmodel
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            Image.new("RGB", (20, 20), (0, 90, 200)).save(Path(td) / "a.png")
            spec = {"kind": "guide", "title": "안내", "body": ["첫 쪽", {"image": "a.png", "width_mm": 40, "caption": "그림 설명"}, {"qr": "example.com/x", "caption": "신청 주소"},
                                                            {"pagebreak": True}, {"form": {"title": "신청서", "fields": ["학년 / 반", ["방법", "□ 방문  □ 전화"]], "sign": "보호자:      (서명)"}}]}
            m = docmodel.build(spec)
            kinds = [b["t"] for b in m["blocks"]]
            for k in ("image", "qr", "pagebreak"):
                self.assertIn(k, kinds)
            h = doc_html.render(m, embed_fonts=False, base=Path(td))
        self.assertIn('class="pb"', h)
        self.assertIn("break-before:page", h)
        self.assertIn("data:image/png;base64,", h)
        self.assertRegex(h, r'<svg[^>]*width="28(\.0)?mm"')
        self.assertIn("□ 방문", h)  # the box stays with its word (no line break between them)

    def test_guide_reply_on_its_own_page_and_form_kind(self):
        import docmodel
        spec = json.loads((DOCS / "assets" / "examples" / "guide-parent-counseling.json").read_text(encoding="utf-8"))
        m = docmodel.build(spec)
        kinds = [b["t"] for b in m["blocks"]]
        self.assertIn("pagebreak", kinds)
        self.assertNotIn("cut", kinds)
        text = "\n".join(docmodel.plain_lines(m))
        for w in ("학생 이름", "희망 날짜 1지망", "(서명)", "귀하"):
            self.assertIn(w, text)
        self.assertEqual(ph.find(text), [])
        f = docmodel.build({"kind": "신청서", "title": "상담 신청서", "org": "우리 학교", "fields": ["학년 / 반", "학생 이름"], "to": "우리 학교장"})
        self.assertEqual(f["meta"]["kind"], "form")
        self.assertIn("우리 학교장 귀하", "\n".join(docmodel.plain_lines(f)))

    def test_hwpx_gets_the_page_break_and_stays_valid(self):
        import doc_check
        import docmodel
        import hwpx_write
        spec = json.loads((DOCS / "assets" / "examples" / "guide-parent-counseling.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "g.hwpx"
            hwpx_write.write(docmodel.build(spec), out)
            import zipfile
            sec = zipfile.ZipFile(out).read("Contents/section0.xml").decode("utf-8")
            self.assertEqual(sec.count('pageBreak="1"'), 1)
            self.assertFalse([m for lv, m in doc_check.run(out) if lv == "FAIL"])

    @unittest.skipUnless(have("pypdfium2") and have("pypdf"), "pypdfium2 / pypdf not installed")
    def test_page_count_and_smallest_text_checks(self):
        import doc_look
        import pdf_tools
        with tempfile.TemporaryDirectory() as td:
            pdf = pdf_tools.mini_pdf([["First page line"] * 6, ["Second"], ["Third"]], Path(td) / "m.pdf")
            r = doc_look.info(pdf)
            self.assertEqual(r["pages"], 3)
            self.assertEqual(len(r["fill"]), 3)
            lv = [l for l, _ in doc_look.checks(pdf, max_pages=2)]
            self.assertIn("FAIL", lv)
            self.assertNotIn("FAIL", [l for l, _ in doc_look.checks(pdf, max_pages=3)])
            if r["min_pt"]:
                self.assertIn("FAIL", [l for l, _ in doc_look.checks(pdf, min_font=r["min_pt"] + 4)])
            png = doc_look.sheet(pdf, Path(td) / "s.png")
            self.assertTrue(png and png.exists())

    def test_docs_cli_has_append_and_limits(self):
        src = (DOCS / "scripts" / "docs.py").read_text(encoding="utf-8")
        for w in ('sub.add_parser("append")', "--max-pages", "--min-font", "--font-size", "NOT DONE", "def look("):
            self.assertIn(w, src)


if __name__ == "__main__":
    unittest.main(verbosity=1)
