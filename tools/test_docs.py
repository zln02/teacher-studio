# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""teacher-docs: 공문 rules in the block model, HWPX create / fill / patch roundtrip (formatting kept), our preview,
DOCX create + replace, PDF merge / split / form fill / watermark / text, and the document gate (blanks, privacy,
공문 format, dates, spacing, structure, fonts).   Run: py tools/test_docs.py"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "skills" / "teacher-docs"
sys.path[:0] = [str(DOCS / "scripts"), str(ROOT / "shared" / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")
import doc_check  # noqa: E402
import docmodel  # noqa: E402
import hwpx_edit  # noqa: E402
import hwpx_preview  # noqa: E402
import hwpx_write  # noqa: E402

EX = DOCS / "assets" / "examples"


def have(mod):
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


def spec(name):
    return json.loads((EX / f"{name}.json").read_text(encoding="utf-8"))


def tmp():
    return Path(tempfile.mkdtemp())


class GongmunModel(unittest.TestCase):
    def lines(self, s):
        return docmodel.plain_lines(docmodel.build(s))

    def test_marks_and_end(self):
        L = self.lines(spec("gongmun-training"))
        self.assertIn("수신  수신자 참조", L)
        self.assertIn("(경유)", L)
        self.assertTrue(any(x.startswith("1. 관련:") for x in L))
        self.assertTrue(any(x.startswith("가. 연수명") for x in L))
        self.assertTrue(any(x.startswith("1) 업무관리시스템") for x in L))
        self.assertIn("붙임  1. 연수 운영 계획 1부.", L)
        self.assertIn("2. 참가 신청서 1부.  끝.", L)
        self.assertIn("우리교육지원청교육장", L)

    def test_eight_levels(self):
        body = ["a", ["b", ["c", ["d", ["e", ["f", ["g", ["h", "h2"], "g2"], "f2"], "e2"], "d2"], "c2"], "b2"], "a2"]
        L = self.lines({"kind": "gongmun", "title": "t", "body": body})
        for m in ("1. a", "가. b", "1) c", "가) d", "(1) e", "(가) f", "① g", "㉮ h", "㉯ h2"):
            self.assertIn(m, L, m)

    def test_single_item_has_no_mark_and_end(self):
        L = self.lines({"kind": "gongmun", "title": "t", "receiver": "내부결재", "body": ["하나뿐인 내용입니다."], "sender": "교장"})
        self.assertIn("하나뿐인 내용입니다.  끝.", L)
        self.assertNotIn("교장", L)  # 내부결재 -> no 발신명의

    def test_single_attachment_and_table_end(self):
        L = self.lines({"kind": "gongmun", "title": "t", "body": ["a", "b"], "attachments": ["계획서 1부"]})
        self.assertIn("붙임  계획서 1부.  끝.", L)
        m = docmodel.build({"kind": "gongmun", "title": "t", "body": ["a", {"table": {"columns": ["x", "y"], "rows": [["1", "2"]]}}]})
        self.assertEqual(m["blocks"][-1]["text"], "  끝.")

    def test_dates(self):
        for a in ("2026-11-19", "2026.11.19", "2026년 11월 19일"):
            self.assertEqual(docmodel.gov_date(a), "2026. 11. 19.")


class Hwpx(unittest.TestCase):
    def test_create_all_examples_structure_and_text(self):
        d = tmp()
        for f in sorted(EX.glob("*.json")):
            s = json.loads(f.read_text(encoding="utf-8"))
            out = hwpx_write.write(docmodel.build(s), d / f"{f.stem}.hwpx")
            st = doc_check.hwpx_structure(out)
            self.assertEqual(st[0][0], "PASS", (f.stem, st))
            with zipfile.ZipFile(out) as z:
                self.assertEqual(z.infolist()[0].filename, "mimetype")
                self.assertEqual(z.infolist()[0].compress_type, zipfile.ZIP_STORED)
            res = doc_check.run(out, fillins=s.get("fillins") or [], allow_blanks=s.get("template_blanks") is True)
            self.assertFalse([m for lv, m in res if lv == "FAIL"], f.stem)
            html = hwpx_preview.render(out)
            self.assertIn("<table", html) if "table" in json.dumps(s) else None
            self.assertIn(s.get("title", "")[:6], html)

    def test_gongmun_gate_clean(self):
        out = hwpx_write.write(docmodel.build(spec("gongmun-training")), tmp() / "g.hwpx")
        res = dict((m.split(" (")[0].split(":")[0], lv) for lv, m in doc_check.run(out, "gongmun"))
        self.assertTrue(all(v == "PASS" for v in res.values()), res)

    def test_fill_keeps_formatting(self):
        d = tmp()
        src = hwpx_write.write(docmodel.build(spec("form-application")), d / "form.hwpx")
        self.assertEqual(hwpx_edit.blanks(src), ["{{신청일}}"])
        r = hwpx_edit.fill(src, d / "filled.hwpx", {"신청일": "2026. 11. 20.", "학교명": "우리초등학교", "직위": "교사", "없는칸": "x"})
        self.assertEqual(r["missing"], ["없는칸"])
        t = hwpx_edit.text(d / "filled.hwpx")
        self.assertIn("신청일: 2026. 11. 20.", t)
        self.assertIn("우리초등학교", t)
        with zipfile.ZipFile(src) as a, zipfile.ZipFile(d / "filled.hwpx") as b:
            self.assertEqual(a.read("Contents/header.xml"), b.read("Contents/header.xml"))  # styles untouched
            sa, sb = a.read("Contents/section0.xml").decode(), b.read("Contents/section0.xml").decode()
            self.assertEqual(re.findall(r'charPrIDRef="\d+"', sa), re.findall(r'charPrIDRef="\d+"', sb))
            self.assertIn("xmlns:hp10=", sb)  # original namespace declarations kept
            self.assertNotIn("ns0:", sb)
        self.assertEqual(doc_check.hwpx_structure(d / "filled.hwpx")[0][0], "PASS")

    def test_patch_applied_unapplied_and_no_overwrite(self):
        d = tmp()
        src = hwpx_write.write(docmodel.build(spec("gongmun-training")), d / "g.hwpx")
        r = hwpx_edit.patch(src, d / "p.hwpx", [{"find": "60명", "replace": "80명"}, {"after": "장소:", "insert": "준비물: 개인 노트북"},
                                                 {"find": "없는 문구", "replace": "x"}])
        self.assertEqual(len(r["applied"]), 2)
        self.assertEqual(r["unapplied"], [{"find": "없는 문구", "replace": "x"}])
        t = hwpx_edit.text(d / "p.hwpx")
        self.assertTrue(any("80명" in x for x in t))
        self.assertEqual(t[t.index("준비물: 개인 노트북") - 1][:5], "다. 장소")
        self.assertEqual(doc_check.hwpx_structure(d / "p.hwpx")[0][0], "PASS")
        with self.assertRaises(ValueError):
            hwpx_edit.patch(src, src, [])

    def test_split_run_replace(self):
        d = tmp()
        src = hwpx_write.write(docmodel.build({"kind": "guide", "title": "t", "body": [{"p": "가 **{{이**름}} 나"}]}), d / "s.hwpx")
        r = hwpx_edit.fill(src, d / "o.hwpx", {"이름": "값"})
        self.assertIn("{{이름}}", r["filled"])
        self.assertIn("가 값 나", hwpx_edit.text(d / "o.hwpx"))

    def test_old_hwp_message(self):
        import docs
        msg = docs.old_hwp_message(Path("가정통신문.hwp"))
        self.assertIn("HWPX", msg)
        self.assertIn("올리지 않고", msg)


class Gate(unittest.TestCase):
    def test_placeholders(self):
        r = doc_check.check_placeholders(["[학교명] 운영 안내", "20XX년"], [])
        self.assertEqual(r[0][0], "FAIL")
        r = doc_check.check_placeholders(["[학교명] 운영 안내"], ["학교명"])
        self.assertEqual(r[0][0], "PASS")

    def test_privacy(self):
        r = dict((m.split()[0], lv) for lv, m in doc_check.check_privacy(["주민번호 010101-3123456", "연락처 010-1234-5678", "성명: 김민수", "3학년 2반 15번"]))
        self.assertEqual(r["주민등록번호"], "FAIL")
        self.assertIn("WARN", [lv for lv, _ in doc_check.check_privacy(["연락처 010-1234-5678"])])
        self.assertTrue(any("이름" in m for _, m in doc_check.check_privacy(["성명: 김민수"])))
        self.assertTrue(any("학년" in m for _, m in doc_check.check_privacy(["3학년 2반 15번"])))
        self.assertEqual([lv for lv, _ in doc_check.check_privacy(["학교 대표 전화로 문의"])], ["PASS"])

    def test_gongmun_lint_bad(self):
        bad = ["수신  내부결재", "제목  안내", "1. 가", "3. 나", "다. 건너뜀", "붙임: 계획서 1부. 끝."]
        res = dict((m.split(" (")[0].split(":")[0], lv) for lv, m in doc_check.check_gongmun(bad))
        self.assertEqual(res["항목 번호 순서"], "WARN")
        self.assertEqual(res["「끝」 표시"], "WARN")
        self.assertTrue(any("붙임:" in m for _, m in doc_check.check_gongmun(bad)))

    def test_dates_and_time(self):
        r = doc_check.check_dates(["일시: 2026-11-19 오후 3시", "2026.11.19", "2026. 09. 06.", "2026. 11. 19 까지"], True)
        self.assertEqual(r[0][0], "WARN")
        self.assertIn("24시각제", r[0][1] + "".join(m for _, m in doc_check.check_dates(["오후 3시"], True)))
        self.assertEqual(doc_check.check_dates(["2026. 11. 19.(목) 15:00"], True)[0][0], "PASS")

    def test_spacing(self):
        r = doc_check.check_spacing(["참여할수 있는 학생", "그 동안 방과후 활동", "50%이상 참여", "(금) 까지 제출"])
        self.assertEqual(r[0][0], "WARN")
        for want in ("할 수", "그동안", "방과 후", "% 이상", ")까지"):
            self.assertIn(want, r[0][1])
        self.assertEqual(doc_check.check_spacing(["참여할 수 있는 학생 50명"])[0][0], "PASS")


@unittest.skipUnless(have("docx"), "python-docx not installed")
class Docx(unittest.TestCase):
    def test_create_replace_gate(self):
        import docx_tools
        d = tmp()
        for f in sorted(EX.glob("*.json")):
            s = json.loads(f.read_text(encoding="utf-8"))
            out = docx_tools.write(docmodel.build(s), d / f"{f.stem}.docx")
            res = doc_check.run(out, fillins=s.get("fillins") or [], allow_blanks=s.get("template_blanks") is True)
            self.assertFalse([m for lv, m in res if lv == "FAIL"], f.stem)
        r = docx_tools.replace(d / "form-application.docx", d / "f.docx", {"신청일": "2026. 11. 20."})
        self.assertEqual(r["filled"], ["신청일"])
        self.assertIn("신청일: 2026. 11. 20.", docx_tools.text(d / "f.docx"))
        g = docx_tools.text(d / "gongmun-training.docx")
        self.assertIn("2. 참가 신청서 1부.  끝.", g)


@unittest.skipUnless(have("pypdf"), "pypdf not installed")
class Pdf(unittest.TestCase):
    def test_ops(self):
        import pdf_tools
        d = tmp()
        a = pdf_tools.mini_pdf([["Page one"], ["Page two"], ["Page three"]], d / "a.pdf")
        f = pdf_tools.mini_pdf([["Form"]], d / "f.pdf", fields=[{"name": "name"}, {"name": "agree", "type": "check", "y": 560}])
        m = pdf_tools.merge([a, f], d / "m.pdf")
        self.assertEqual(len(pdf_tools.extract_text(m)), 4)
        parts = pdf_tools.split(m, d / "sp", "1-2,4")
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(pdf_tools.extract_text(parts[0])), 2)
        r = pdf_tools.fill_form(f, d / "ff.pdf", {"name": "Kim", "agree": True, "nope": "x"})
        self.assertEqual(r["missing"], ["nope"])
        flds = pdf_tools.fields(d / "ff.pdf")
        self.assertEqual(flds["name"], "Kim")
        self.assertEqual(flds["agree"], "/Yes")
        w = pdf_tools.watermark(a, d / "w.pdf", "DRAFT")
        self.assertIn("DRAFT", pdf_tools.extract_text(w)[1])
        with self.assertRaises(ValueError):
            pdf_tools.watermark(a, d / "w2.pdf", "초안")
        self.assertEqual(doc_check.check_open(w)[0][0], "PASS")
        self.assertEqual(doc_check.check_fonts(w)[0][0], "WARN")  # Helvetica is not embedded: the gate says so

    @unittest.skipUnless(have("pdfplumber"), "pdfplumber not installed")
    def test_tables_api(self):
        import pdf_tools
        a = pdf_tools.mini_pdf([["no table here"]], tmp() / "t.pdf")
        self.assertEqual(pdf_tools.extract_tables(a), [[]])


if __name__ == "__main__":
    unittest.main(verbosity=1)
