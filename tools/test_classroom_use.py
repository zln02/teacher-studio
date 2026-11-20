# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Unit tests: 활용·전달 단계 - env_programs.py (mocked registry / paths) and deliver.py --use mapping. No network, no browser.

Run: py tools/test_classroom_use.py
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "skills" / "teacher-studio" / "scripts"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ep = load("env_programs", STUDIO / "env_programs.py")
dv = load("deliver_use", STUDIO / "deliver.py")

HWP = r"C:\HNC\Hwp.exe"
CHROME = r"C:\Chrome\chrome.exe"
PPT = r"C:\Office\POWERPNT.EXE"


def fake_probe(system="win32", apppaths=None, uninstall=None, files=(), cmds=None, apps_version="16.80"):
    files = set(files) | set((apppaths or {}).values())
    cmds = cmds or {}
    return ep.probe(system=system, registry={"apppaths": apppaths or {}, "uninstall": uninstall or []},
                    which=lambda c: cmds.get(c), exists=lambda p: str(p) in files, version_of=lambda w: "3.12.1" if "py" in w else "20.1.0",
                    mac_version=lambda p: apps_version)


class EnvProgramsTests(unittest.TestCase):
    def test_windows_registry(self):
        r = fake_probe(apppaths={"hwp.exe": HWP, "chrome.exe": CHROME}, uninstall=[("한컴오피스 2024", "13.0.0.1"), ("Google Chrome", "130.0")],
                       cmds={"py": r"C:\py.exe"})
        self.assertTrue(r["hwp"]["ok"])
        self.assertEqual(r["hwp"]["version"], "13.0.0.1")
        self.assertTrue(r["chrome"]["ok"])
        self.assertFalse(r["powerpoint"]["ok"])
        self.assertTrue(r["python"]["ok"])
        self.assertFalse(r["node"]["ok"])
        self.assertTrue(r["pdf_reader"]["ok"])  # the browser counts as a PDF reader
        self.assertEqual(r["pdf_reader"]["how"], "browser")

    def test_microsoft_365_alone_is_not_powerpoint(self):
        r = fake_probe(uninstall=[("Microsoft 365 - ko-kr", "16.0.1")])
        self.assertFalse(r["powerpoint"]["ok"])
        r = fake_probe(apppaths={"powerpnt.exe": PPT}, uninstall=[("Microsoft 365 - ko-kr", "16.0.1")])
        self.assertTrue(r["powerpoint"]["ok"])
        self.assertEqual(r["powerpoint"]["version"], "16.0.1")

    def test_apppath_must_exist(self):
        r = ep.probe(system="win32", registry={"apppaths": {"powerpnt.exe": PPT}, "uninstall": []}, which=lambda c: None, exists=lambda p: False)
        self.assertFalse(r["powerpoint"]["ok"])

    def test_outdated(self):
        r = fake_probe(apppaths={"powerpnt.exe": PPT}, uninstall=[("Microsoft Office 2007", "12.0.4518")])
        self.assertTrue(r["powerpoint"]["outdated"])
        o = ep.opener(".pptx", r)
        self.assertTrue(o["ok"])
        self.assertIn("업데이트", o["offer"])
        r = fake_probe(uninstall=[("한글 2010", "8.5.0")])
        self.assertTrue(r["hwp"]["outdated"])

    def test_macos_applications(self):
        r = fake_probe(system="darwin", files={"/Applications/Microsoft PowerPoint.app", "/System/Applications/Preview.app"})
        self.assertTrue(r["powerpoint"]["ok"])
        self.assertEqual(r["powerpoint"]["version"], "16.80")
        self.assertTrue(r["pdf_reader"]["ok"])
        self.assertFalse(r["hwp"]["ok"])

    def test_linux_which(self):
        r = fake_probe(system="linux", cmds={"soffice": "/usr/bin/soffice", "chromium": "/usr/bin/chromium", "python3": "/usr/bin/python3"})
        self.assertTrue(r["libreoffice"]["ok"])
        self.assertTrue(r["chrome"]["ok"])
        self.assertTrue(r["python"]["ok"])
        self.assertEqual(ep.opener(".pptx", r)["program"], "LibreOffice")

    def test_missing_program_is_an_offer_not_an_install(self):
        r = fake_probe()
        o = ep.opener(".pptx", r)
        self.assertFalse(o["ok"])
        self.assertIn("MB", o["offer"])
        self.assertIn("할까요", o["offer"])
        src = (STUDIO / "env_programs.py").read_text(encoding="utf-8")
        for bad in ("winget install", "pip install", "urllib.request", "import requests"):
            self.assertNotIn(bad, src)

    def test_cache_keeps_other_keys_and_expires(self):
        with tempfile.TemporaryDirectory() as t:
            c = Path(t) / "env.json"
            c.write_text(json.dumps({"agent": "claude-code"}), encoding="utf-8")
            kw = dict(system="linux", registry={}, which=lambda x: None, exists=lambda p: False)
            day = datetime.date(2026, 11, 20)
            ep.load(cache=c, today=day, **kw)
            d = json.loads(c.read_text(encoding="utf-8"))
            self.assertEqual(d["agent"], "claude-code")
            self.assertIn("programs", d)
            self.assertEqual(d["programs_checked"], "2026-11-20")
            d["programs"]["chrome"]["ok"] = True  # the cached value is served while fresh
            c.write_text(json.dumps(d), encoding="utf-8")
            self.assertTrue(ep.load(cache=c, today=day + datetime.timedelta(days=3), **kw)["chrome"]["ok"])
            self.assertFalse(ep.load(cache=c, today=day + datetime.timedelta(days=30), **kw)["chrome"]["ok"])


class DeliverUseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.game = self.d / "quiz.html"
        self.game.write_text('<html><head><meta name="viewport" content="width=device-width"><title>퀴즈</title></head><body>q</body></html>', encoding="utf-8")
        self.deck = self.d / "deck.html"
        self.deck.write_text('<meta name="ts-deck" content="style=x"><title>연수</title>', encoding="utf-8")
        self.table = self.d / "report.html"
        self.table.write_text("<table><tr><th>반</th><th>평균</th></tr><tr><td>1반</td><td>3.2</td></tr></table>", encoding="utf-8")
        self.csv = self.d / "data.csv"
        self.csv.write_text("a,b\n1,2\n", encoding="utf-8")
        self.hwpx = self.d / "notice.hwpx"
        self.hwpx.write_bytes(b"PK")

    def tearDown(self):
        self.tmp.cleanup()

    def test_mapping(self):
        P = dv.plan_formats
        self.assertEqual(P("tv", self.game), [])
        self.assertEqual(P("screen", self.game), [])
        self.assertEqual(P("tv", self.hwpx), [".pdf"])
        self.assertEqual(P("tablet", self.game), [])
        self.assertEqual(P("print", self.game), [".pdf"])
        self.assertEqual(P("home", self.hwpx), [".pdf"])
        self.assertEqual(P("share", self.game), [".pdf"])
        self.assertEqual(P("lms", self.game), [".pdf"])
        self.assertEqual(P("lms", self.table), [".pdf", ".csv"])
        self.assertEqual(P("lms", self.csv), [".xlsx"])
        self.assertEqual(P("archive", self.deck), [".pptx"])
        self.assertEqual(P("archive", self.csv), [".xlsx"])
        self.assertEqual(P("archive", self.table), [".csv"])
        self.assertEqual(P("print", self.d / "x.mp4"), [])

    def test_audience(self):
        self.assertEqual(dv.audience_of("tablet"), "teacher")
        self.assertEqual(dv.audience_of("share"), "general")
        self.assertEqual(dv.audience_of("print", prefs=self.d / "none.json"), "general")
        p = self.d / "prefs.json"
        p.write_text(json.dumps({"level": "중학교"}), encoding="utf-8")
        self.assertEqual(dv.audience_of("print", prefs=p), "teacher")
        self.assertEqual(dv.audience_of("tablet", "general"), "general")
        self.assertEqual(dv.DEFAULT_USE, {"teacher": "tv", "general": "screen"})

    def test_kind(self):
        self.assertEqual(dv.kind_of(self.deck), "deck")
        self.assertEqual(dv.kind_of(self.game), "game")
        self.assertEqual(dv.kind_of(self.csv), "data")
        self.assertEqual(dv.kind_of(self.hwpx), "doc")

    def test_html_table_to_csv(self):
        dest = self.d / "out.csv"
        r = dv.conv_table(self.table, dest)
        self.assertTrue(r["ok"])
        self.assertEqual(dest.read_text(encoding="utf-8-sig").splitlines(), ["반,평균", "1반,3.2"])

    def test_pptx_needs_spec(self):
        r = dv.conv_pptx(self.deck, self.d / "deck.pptx")
        self.assertFalse(r["ok"])
        self.assertIn("spec", r["error"])

    def fake_conv(self, calls):
        def c(src, dest, yes=False, spec=None):
            calls.append(dest.suffix)
            dest.write_bytes(b"x")
            return {"ok": True}
        return {".pdf": c, ".csv": c, ".xlsx": c, ".pptx": c}

    def test_pack_teacher_tablet(self):
        calls = []
        progs = fake_probe(apppaths={"chrome.exe": CHROME})
        out = dv.use_pack(self.game, "tablet", url="https://example.com/q", qr_out=self.d / "q.svg", progs=progs, converters=self.fake_conv(calls))
        self.assertTrue(out.startswith("수업 활용 꾸러미"))
        self.assertLess(out.index("먼저 확인"), out.index("만든 파일"))  # privacy before anything outward
        self.assertIn("크롬으로 열려요", out)
        self.assertIn("폰·태블릿 화면: OK", out)
        self.assertIn("수업에 이렇게", out)
        self.assertIn("출구 티켓", out)
        self.assertEqual(calls, [])

    def test_pack_general_print_makes_pdf(self):
        calls = []
        progs = fake_probe(apppaths={"chrome.exe": CHROME})
        out = dv.use_pack(self.game, "print", audience="general", progs=progs, converters=self.fake_conv(calls))
        self.assertEqual(calls, [".pdf"])
        self.assertTrue((self.d / "quiz.pdf").exists())
        self.assertTrue(out.startswith("활용·전달 꾸러미"))
        self.assertIn("A4", out)
        self.assertIn("이렇게 써 보세요", out)
        self.assertNotIn("수업", out)
        self.assertIn("저는 올리지 않아요", out)

    def test_pack_reports_failure_and_offer(self):
        def fail(src, dest, yes=False, spec=None):
            return {"ok": False, "offer": "작은 도구(openpyxl, 약 3MB)가 필요해요. 설치할까요?"}
        out = dv.use_pack(self.csv, "lms", progs=fake_probe(), converters={".xlsx": fail})
        self.assertIn("XLSX 못 만듦", out)
        self.assertIn("3MB", out)

    def test_dry_run_makes_nothing(self):
        out = dv.use_pack(self.game, "home", dry=True, progs=fake_probe(), converters={})
        self.assertIn("만들 예정", out)
        self.assertFalse((self.d / "quiz.pdf").exists())

    def test_existing_file_not_overwritten(self):
        (self.d / "quiz.pdf").write_bytes(b"mine")
        self.assertEqual(dv.dest_for(self.game, ".pdf", "print").name, "quiz-print.pdf")

    def test_ideas_by_grade(self):
        self.assertIn("몸으로 OX", " ".join(dv.ideas("game", "teacher", "초3")))
        self.assertEqual(len(dv.ideas("deck", "general")), 3)

    def test_josa(self):
        self.assertEqual(dv._josa("크롬", "으로/로"), "크롬으로")
        self.assertEqual(dv._josa("엣지", "으로/로"), "엣지로")
        self.assertEqual(dv._josa("한글(한컴오피스)", "으로/로"), "한글(한컴오피스)로")
        self.assertEqual(dv._josa("다른 사람 정보", "이/가"), "다른 사람 정보가")

    def test_never_uploads(self):
        src = (STUDIO / "deliver.py").read_text(encoding="utf-8")
        for bad in ("urllib.request", "import requests", "socket", "http.client", "smtplib", "ftplib"):
            self.assertNotIn(bad, src)


class UseScoreTests(unittest.TestCase):
    def test_use_part(self):
        ev = load("router_eval_use", ROOT / "tools" / "router_eval.py")
        case = {"id": "u", "request": "r", "route": "game", "direction": None, "max_questions": 1, "must_not": [],
                "use": {"use": ["tv"], "asks_use": False, "audience": "teacher", "formats_any": ["html"]}}
        good = {"route": "game", "first_reply": "", "use": "tv", "asks_use": False, "audience": "teacher", "use_formats": ["HTML", "pdf"]}
        self.assertEqual(ev.score(case, good)["score"], 1.0)
        bad = dict(good, use="print", asks_use=True)
        r = ev.score(case, bad)
        self.assertAlmostEqual(r["parts"]["use"], 0.5)
        self.assertLess(r["score"], 1.0)
        cases = json.loads((ROOT / "tools" / "router_cases.json").read_text(encoding="utf-8"))["cases"]
        use_cases = [c for c in cases if c.get("use")]
        self.assertGreaterEqual(len(use_cases), 9)
        self.assertGreaterEqual(sum(1 for c in use_cases if c["use"].get("audience") == "general"), 3)


if __name__ == "__main__":
    unittest.main(verbosity=1)
