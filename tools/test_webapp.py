# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Web app route: build_webapp.py spec validation + page, check_webapp.py static rules, router entry wording.
Fast (no browser, no fonts). One optional browser test runs only with TS_BROWSER=1.   Run: py tools/test_webapp.py"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TS = ROOT / "skills" / "teacher-studio"
sys.path.insert(0, str(TS / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("PYTHONUTF8", "1")
import build_webapp  # noqa: E402
import check_webapp  # noqa: E402
import router_eval  # noqa: E402

EX = TS / "assets" / "webapp" / "examples"


def load(name: str) -> dict:
    return json.loads((EX / name).read_text(encoding="utf-8"))


def fails(html: str) -> list[str]:
    return [m for lvl, m in check_webapp.static_checks(html) if lvl == "FAIL"]


class SpecTests(unittest.TestCase):
    def test_examples_valid_and_build_clean(self):
        for name in ("coding-helper.json", "speed-sim.json"):
            spec = load(name)
            self.assertEqual(build_webapp.validate(spec), [], name)
            page, rep = build_webapp.build(spec, fonts=False)
            self.assertEqual(fails(page), [], name)
            self.assertIn(rep["style"], build_webapp.styles.STYLES)

    def test_page_has_classroom_controls_and_honesty(self):
        page, _ = build_webapp.build(load("coding-helper.json"), fonts=False)
        for need in ('id="wa-reset"', 'id="wa-proj"', 'id="wa-bigger"', 'id="wa-smaller"', 'id="wa-about"', 'lang="ko"', "인터넷에 연결된 AI(챗GPT 같은 것)가 아니에요"):
            self.assertIn(need, page)
        self.assertNotIn("localStorage", page)

    def test_rejects_bad_specs(self):
        base = load("coding-helper.json")
        cases = {
            "no title": lambda s: s.pop("title"),
            "live ai": lambda s: s.__setitem__("ai", "openai"),
            "python runner": lambda s: s["parts"][1].__setitem__("lang", "python"),
            "empty intents": lambda s: s["parts"][0].__setitem__("intents", []),
            "too many parts": lambda s: s.__setitem__("parts", s["parts"] * 2),
        }
        for why, mut in cases.items():
            s = copy.deepcopy(base)
            mut(s)
            self.assertTrue(build_webapp.validate(s), why)
        sim = load("speed-sim.json")
        sim["parts"][0]["js"] = "var x = a?.b ?? 1;"
        self.assertTrue(any("?." in e for e in build_webapp.validate(sim)))
        sim = load("speed-sim.json")
        sim["parts"][0]["html"] += "<script>alert(1)</script>"
        self.assertTrue(build_webapp.validate(sim))

    def test_user_palette_wins(self):
        spec = load("speed-sim.json")
        spec["palette"] = {"primary": "#123456"}
        page, _ = build_webapp.build(spec, fonts=False)
        self.assertIn("--sk-pr:#123456", page)

    def test_custom_text_is_escaped_in_title(self):
        spec = load("speed-sim.json")
        spec["title"] = "<b>속력</b>"
        page, _ = build_webapp.build(spec, fonts=False)
        self.assertIn("&lt;b&gt;속력", page)


class StaticCheckTests(unittest.TestCase):
    OK = '<!DOCTYPE html><html lang="ko"><head><meta name="viewport" content="width=device-width"><title>앱</title></head><body>{}</body></html>'

    def test_clean_page_passes(self):
        self.assertEqual(fails(self.OK.format("<p>안녕</p><script>var a = 1; console.log('뭐예요?.');</script>")), [])

    def test_flags(self):
        bad = {
            "cdn": '<script src="https://cdn.jsdelivr.net/npm/pyodide/pyodide.js"></script>',
            "font": '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=X">',
            "optional chaining": "<script>var b = a?.c;</script>",
            "storage": "<script>localStorage.setItem('a', 1)</script>",
            "fetch": "<script>fetch('/x')</script>",
            "key": "<script>var k = 'sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAAAAAA';</script>",
            "identity": '<label for="n">학생 이름</label><input id="n">',
            "form": '<form action="/send"></form>',
        }
        for why, body in bad.items():
            self.assertTrue(fails(self.OK.format(body)), why)
        self.assertTrue(fails("<html><body>no title</body></html>"))

    def test_strings_do_not_count_as_syntax(self):
        js = "<script>var s = \"a?.b ?? c\"; // x?.y\n</script>"
        self.assertEqual(fails(self.OK.format(js)), [])


class RouterTests(unittest.TestCase):
    def test_entry_description_covers_make_requests(self):
        _n, desc = router_eval.frontmatter(TS / "SKILL.md")
        for w in ("프로그램", "앱", "웹페이지", "도우미", "계산기", "시뮬레이션", "알아서", "묻지 말고"):
            self.assertIn(w, desc)
        self.assertLessEqual(len(desc), 1024)

    def test_skill_routes_web_apps_and_keeps_tools_on_quick_requests(self):
        body = (TS / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/webapp.md", body)
        self.assertIn("not the tools", body)
        self.assertNotIn("mobile apps, websites", body)
        self.assertTrue((TS / "references" / "webapp.md").exists())

    def test_cases_have_webapp_and_demo(self):
        cases = router_eval.load_cases()
        web = [c for c in cases if "webapp" in c.get("tags", [])]
        self.assertGreaterEqual(len(web), 6)
        self.assertTrue(any("알아서" in c["request"] for c in web) and any("알아서" not in c["request"] and "묻지" not in c["request"] for c in web))
        self.assertIn("webapp", router_eval.ROUTES)

    def test_trigger_scoring(self):
        case = {"trigger": ["teacher-studio"]}
        self.assertEqual(router_eval.score_trigger(case, {"skill": "teacher-studio"})["score"], 1.0)
        self.assertEqual(router_eval.score_trigger(case, {"skill": "plugin:teacher-studio"})["score"], 1.0)
        self.assertEqual(router_eval.score_trigger(case, {"skill": "none"})["score"], 0.0)
        self.assertEqual(router_eval.score_trigger(case, None)["score"], 0.0)


@unittest.skipUnless(os.environ.get("TS_BROWSER") == "1", "set TS_BROWSER=1 to run the headless check")
class BrowserTests(unittest.TestCase):
    def test_example_passes_browser_check(self):
        page, _ = build_webapp.build(load("coding-helper.json"), fonts=False)
        f = Path(tempfile.mkdtemp()) / "app.html"
        f.write_text(page, encoding="utf-8")
        self.assertEqual(check_webapp.run(f, browser=True, deep=True), 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
