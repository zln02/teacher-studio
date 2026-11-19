# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Unit tests for the fixes found by test-driving the harness on a real site (docs/harness-testbed in the noan-ai repo, 2026-11-19).

Covers: phone portrait stage, offline output + external-URL check, style chooser (words beat title), colour sources (several files, success/error colours),
font option, vignette by light/dark, device words (폰으로 = phone), router rows, skill descriptions. No network.

Run: py tools/test_harness_fixes.py          (the browser tests are skipped when Playwright / Chrome is missing)
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "skills" / "teacher-game"
SCRIPTS = GAME / "scripts"
STUDIO = ROOT / "skills" / "teacher-studio" / "scripts"
DESIGN = ROOT / "shared" / "design"
for p in (str(SCRIPTS), str(DESIGN)):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("PYTHONUTF8", "1")

import build  # noqa: E402  (skills/teacher-game/scripts/build.py)
import check_game  # noqa: E402
import color_check as cc  # noqa: E402
import color_from as cf  # noqa: E402
import layout_auto  # noqa: E402
import oklch as ok  # noqa: E402
import phone_check  # noqa: E402
import specs  # noqa: E402
import style_auto  # noqa: E402
import theme_auto  # noqa: E402


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


direction = load("direction_fix", STUDIO / "direction.py")
sync_shared = load("sync_shared_fix", ROOT / "tools" / "sync_shared.py")

ITEMS = [{"q": f"문제 {i}?", "choices": ["가", "나", "다", "라"], "answer": i % 4, "exp": "해설"} for i in range(4)]


def quiz_spec(**design) -> dict:
    d = {"seed": 5, **design}
    return {"title": "AI 말 복습", "subtitle": "AI 알기", "mechanic": "quiz", "use": "personal", "device": "phone", "design": d, "items": [dict(i) for i in ITEMS]}


def build_html(spec: dict, *extra: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        sp, out = Path(td) / "spec.json", Path(td) / "out.html"
        sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS / "build.py"), "--spec", str(sp), "--out", str(out), "--no-check", "--no-fonts", *extra],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, r.stdout + r.stderr
        return out.read_text(encoding="utf-8")


class PhonePortrait(unittest.TestCase):
    def test_quiz_on_a_phone_gets_the_portrait_layout(self):
        html = build_html(quiz_spec())
        self.assertIn('"portrait": true', html)
        self.assertIn("TS:PORTRAIT BEGIN", html)
        self.assertIn("body[data-orient=portrait]", html)
        self.assertNotIn("rotate(90deg)", html)  # never a rotated stage

    def test_other_mechanics_and_boards_do_not(self):
        sp = {"title": "짝", "mechanic": "match", "use": "personal", "device": "phone", "design": {"seed": 1}, "items": [{"a": f"a{i}", "b": f"b{i}"} for i in range(4)]}
        self.assertIn('"portrait": false', build_html(sp))
        sp = quiz_spec()
        sp["device"] = "board"
        html = build_html(sp)
        self.assertIn('"portrait": false', html)
        self.assertNotIn("TS:PORTRAIT BEGIN", html)

    def test_engine_fit_makes_a_portrait_stage_not_a_strip(self):
        eng = (GAME / "assets" / "engine.html").read_text(encoding="utf-8")
        self.assertIn("var PW = 600;", eng)
        self.assertIn("G.portrait === true", eng)
        self.assertIn('data-orient', eng)
        self.assertNotIn("user-scalable=no", eng)  # zoom allowed (WCAG 1.4.4)
        self.assertNotIn("github.com", eng.split("ENGINE (do not edit")[1].replace("creditUrl", ""))

    def test_phone_check_rules(self):
        ok_probe = {"minFont": 16.9, "minText": "", "tiny": [], "offscreen": [], "clipped": [], "rotate": False}
        lines = phone_check.evaluate("portrait", {"title": ok_probe, "question": ok_probe}, [], True)
        self.assertTrue(all(lv == "PASS" for lv, _ in lines), lines)
        bad = dict(ok_probe, minFont=5.2, minText='title "x"')
        self.assertEqual(phone_check.evaluate("portrait", {"title": bad}, [], True)[0][0], "FAIL")  # the 5px strip is a FAIL, not a PASS
        self.assertEqual(phone_check.evaluate("portrait", {"title": dict(ok_probe, minFont=15.0)}, [], True)[0][0], "WARN")
        self.assertEqual(phone_check.evaluate("landscape", {"q": dict(ok_probe, minFont=11.0)}, [], True)[0][0], "WARN")
        self.assertEqual(phone_check.evaluate("landscape", {"q": dict(ok_probe, minFont=8.0)}, [], True)[0][0], "FAIL")
        tiny = dict(ok_probe, tiny=[["icon-btn", 32, 32]])
        self.assertTrue(any(lv == "FAIL" and "44" in m for lv, m in phone_check.evaluate("portrait", {"t": tiny}, [], True)))
        off = dict(ok_probe, offscreen=[["x", -5, 0, 400, 20]])
        self.assertTrue(any(lv == "FAIL" for lv, m in phone_check.evaluate("portrait", {"t": off}, [], True)))

    def test_games_without_a_portrait_layout_must_show_the_turn_message(self):
        shown = {"rotate": True, "minFont": 99}
        self.assertEqual(phone_check.evaluate("portrait", {"t": shown}, [], False)[0][0], "PASS")
        self.assertEqual(phone_check.evaluate("portrait", {"t": {"rotate": False, "minFont": 99}}, [], False)[0][0], "FAIL")

    def test_phone_check_is_only_for_phone_games(self):
        self.assertEqual(phone_check.checks(Path("x.html"), {"device": "board", "mechanic": "quiz"}), [])

    def test_real_browser_portrait_is_readable(self):
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError:
            self.skipTest("Playwright not installed")
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "q.html"
            f.write_text(build_html(quiz_spec()), encoding="utf-8")
            lines = phone_check.checks(f, {"device": "phone", "mechanic": "quiz"})
        if any("could not run" in m or "skipped" in m for _, m in lines):
            self.skipTest(lines[0][1])
        self.assertFalse([m for lv, m in lines if lv == "FAIL"], lines)


class Offline(unittest.TestCase):
    def test_build_has_no_outside_address_by_default(self):
        html = build_html(quiz_spec())
        self.assertNotIn("fonts.googleapis", html)
        self.assertNotIn("fonts.gstatic", html)
        self.assertNotIn("jsdelivr", html)
        self.assertNotIn("github.com", html)
        refs = [(k, m.group(1)) for k, pat in check_game.EXTERNAL_PATTERNS for m in pat.finditer(html)]
        self.assertEqual(refs, [])

    def test_online_opt_in_keeps_the_font_link(self):
        sp = quiz_spec()
        sp["online"] = True
        self.assertIn("fonts.googleapis.com", build_html(sp))

    def test_checker_flags_every_kind_of_outside_request(self):
        def refs(html):
            return {u for _, pat in check_game.EXTERNAL_PATTERNS for u in (m.group(1) for m in pat.finditer(html))}
        self.assertTrue(refs('<link href="https://fonts.googleapis.com/css2?family=Jua" rel="stylesheet">'))
        self.assertTrue(refs('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'))
        self.assertTrue(refs('<script src="https://cdnjs.cloudflare.com/ajax/libs/x/1.0.0/x.js"></script>'))
        self.assertTrue(refs('<img src="https://example.com/a.png">'))
        self.assertTrue(refs('<img src="//example.com/a.png">'))
        self.assertTrue(refs("<style>@import url(https://x.com/a.css);</style>"))
        self.assertTrue(refs("<style>@import 'a.css';</style>"))
        self.assertTrue(refs("<style>a{background:url(https://x.com/a.png)}</style>"))
        self.assertTrue(refs('<script>fetch("https://x.com/a")</script>'))
        self.assertTrue(refs('<script>l.href = "https://fonts.googleapis.com/css2?family=Jua"</script>'))
        self.assertTrue(refs("<script>var x = new XMLHttpRequest()</script>"))
        # not a request
        self.assertFalse(refs('<svg xmlns="http://www.w3.org/2000/svg"></svg>'))
        self.assertFalse(refs('<style>a{background:url(data:image/png;base64,AAA)}</style>'))
        self.assertFalse(refs('<meta name="generator" content="Teacher Studio v0.2.0">'))

    def test_stamp_carries_no_address(self):
        sys.path.insert(0, str(ROOT / "shared" / "tools"))
        import stamp
        out = stamp.stamp("<html><head><meta charset=utf-8></head></html>")
        self.assertIn("Teacher Studio", out)
        self.assertNotIn("http", out)

    def test_go_offline_removes_google_fonts_links(self):
        sys.path.insert(0, str(ROOT / "shared" / "fonts"))
        import embed
        html = '<head>\n<!-- Korean display fonts (Google Fonts only) -->\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Jua" rel="stylesheet">\n</head>'
        self.assertNotIn("googleapis", embed.go_offline(html))

    def test_slides_and_motion_builders_default_to_offline(self):
        src = (ROOT / "shared" / "stage" / "build_stage.py").read_text(encoding="utf-8")
        self.assertIn("offline: bool = True", src)
        for f in ("skills/teacher-motion/assets/missiles/lesson-opening/show.js", "skills/teacher-motion/assets/missiles/subject-intro/show.js", "skills/teacher-slides/assets/missiles/lesson-deck/show.js"):
            self.assertIn("D.online === true", (ROOT / f).read_text(encoding="utf-8"), f)


class StyleChooser(unittest.TestCase):
    SPEC = {"title": "AI 말 2분 복습", "subtitle": "AI 알기 16편", "mechanic": "quiz", "design": {"subject": "AI 연수", "mood": "차분", "words": ["미니멀", "밝음"], "seed": 3},
            "items": ITEMS}

    def test_words_beat_a_title_keyword(self):
        sid, why = style_auto.pick_style("AI 말 코딩 미니멀", "science", 1, priority="미니멀 밝음")
        self.assertEqual((sid, why), ("minimal-premium", "words"))
        self.assertNotIn("ai", style_auto.STYLES["neon-cyber"]["keys"])
        self.assertNotIn("AI", style_auto.STYLES["neon-cyber"]["keys"])

    def test_explicit_style_beats_everything(self):
        self.assertEqual(style_auto.pick_style("네온 사이버", "space", 1, forced="chalk-paper", priority="네온"), ("chalk-paper", "design.style"))

    def test_title_words_still_work_when_nothing_else_says_a_style(self):
        self.assertEqual(style_auto.pick_style("네온 퀴즈", "", 1)[1], "title")

    def test_build_uses_the_same_chooser_as_the_preview(self):
        spec = json.loads(json.dumps(self.SPEC))
        au = theme_auto.compose(spec)
        self.assertEqual(au["style"], "minimal-premium")  # the build: words win over 「AI」 in the title
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "s.json"
            f.write_text(json.dumps(self.SPEC, ensure_ascii=False), encoding="utf-8")
            prev = style_auto.preview_spec(str(f))
            self.assertEqual(prev["style"], au["style"])
            self.assertEqual(prev["why"], au["style_why"])
            r = subprocess.run([sys.executable, str(SCRIPTS / "layout_auto.py"), "--spec", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("style=minimal-premium", r.stdout)
        html = build_html({**self.SPEC, "device": "board", "use": "class"})
        self.assertIn('name="ts-look"', html)
        self.assertIn("style=minimal-premium", html)

    def test_layout_preview_equals_build_layout(self):
        spec = json.loads(json.dumps(self.SPEC))
        spec["design"]["seed"] = 11
        tk = build.make_tokens(spec)
        lay, _, au = build.layout_for(spec, tk)
        html = build_html({**spec, "device": "board", "use": "class"})
        m = re.search(r'name="ts-look" content="([^"]+)"', html)
        self.assertEqual(m.group(1), build.look_line(lay, au)[6:])

    def test_long_answers_do_not_go_into_side_by_side_columns(self):
        items = [{"q": "긴 보기", "choices": ["보기가 아주 아주 긴 첫째 문장", "보기가 아주 아주 긴 둘째 문장", "보기가 아주 아주 긴 셋째 문장"], "answer": 0} for _ in range(4)]
        for seed in range(12):
            lay = layout_auto.compose({"mechanic": "quiz", "items": items, "design": {"seed": seed, "style": ""}}, None, "", "pop-colorful")
            self.assertNotIn(lay["layout"], ("bento", "news", "poster"), seed)


class Colours(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        d = Path(self.td.name)
        (d / "tokens.css").write_text(":root{--ink:#102A43;--mint:#2563EB;--red:#B42318;--border:#D8E2F0;--bg:#F7FAFF}", encoding="utf-8")
        (d / "app.css").write_text(":root{--brand:#1568d2;--ok:#0F6B3F;--danger:#C0392B;--accent:#ffd66b}.a{color:#1568d2}.b{color:#1568d2}", encoding="utf-8")
        self.files = [d / "tokens.css", d / "app.css"]

    def tearDown(self):
        self.td.cleanup()

    def test_several_files_make_one_palette(self):
        pal = cf.extract_many(self.files)
        self.assertEqual(pal["seeds"]["primary"], "#1568d2")
        self.assertEqual(pal["source"]["files"], ["tokens.css", "app.css"])

    def test_source_names_win_and_weak_names_lose(self):
        pal = cf.extract_many(self.files)
        r = pal["respected"]
        self.assertEqual(r["good"], "#0f6b3f")  # --ok is a meaning; --mint (a blue here) is only a name
        self.assertEqual(r["bad"], "#c0392b")  # --danger beats --red
        self.assertEqual(r["text"], "#102a43")
        self.assertEqual(pal["colors"]["text"], "#102a43")  # readable already -> kept exactly
        self.assertEqual(pal["colors"]["cardBorder"], "#d8e2f0")

    def test_correct_wrong_colours_are_clear_not_muddy_and_colour_blind_safe(self):
        pal = cf.extract_many(self.files)
        c = pal["colors"]
        for key in ("good", "bad"):
            self.assertGreaterEqual(ok.contrast(c[key], c["card"]), 4.5, key)
        self.assertGreaterEqual(ok.hex_to_oklch(c["bad"])[0], 0.44)  # not brown-black
        self.assertGreaterEqual(ok.hex_to_oklch(c["bad"])[1], 0.10)
        self.assertGreater(ok.hue_distance(ok.hex_to_oklch(c["good"])[2], ok.hex_to_oklch(c["bad"])[2]), 60)
        pairs = [x for x in cc.check_pairs(c) if {x["a"], x["b"]} == {"good", "bad"}]
        self.assertEqual(pairs, [])  # no colour-blind confusion between correct and wrong

    def test_accent_for_decoration_keeps_its_own_colour(self):
        pal = cf.extract_many(self.files)
        self.assertEqual(pal["accentDeco"], pal["seeds"]["accent"])
        self.assertNotIn("accentDeco", pal["colors"])
        sys.path.insert(0, str(DESIGN))
        import design
        tk = design.apply_palette_from({"colors": {}, "palette": "x"}, pal)
        self.assertEqual(tk["accentDeco"], pal["seeds"]["accent"])
        self.assertNotIn("accentDeco", tk["colors"])

    def test_semantic_names(self):
        self.assertEqual(cf.semantic_role("success"), "good")
        self.assertEqual(cf.semantic_role("color-danger"), "bad")
        self.assertEqual(cf.semantic_role("ink"), "text")
        self.assertIsNone(cf.semantic_role("success-bg"))
        self.assertIsNone(cf.semantic_role("text-muted"))
        self.assertIsNone(cf.semantic_role("brand-red"))

    def test_single_file_still_works(self):
        pal = cf.extract(self.files[1])
        self.assertEqual(pal["source"]["file"], "app.css")

    def test_without_hints_nothing_changes_for_good_bad(self):
        g, b = cf._meaning_pair("#ffffff", False)
        self.assertGreaterEqual(ok.contrast(g, "#ffffff"), 4.5)
        self.assertGreaterEqual(ok.contrast(b, "#ffffff"), 4.5)


class FontAndVignette(unittest.TestCase):
    def tokens(self, **design):
        sp = quiz_spec(**design)
        return sp, build.make_tokens(sp)

    def test_font_option_validates(self):
        for f in ("sans", "serif", "rounded", "system"):
            self.assertEqual([e for e in specs.validate(quiz_spec(font=f)) if "font" in e], [])
        self.assertTrue([e for e in specs.validate(quiz_spec(font="comic")) if "design.font" in e])

    def test_font_choice_beats_the_style_font(self):
        sp, tk = self.tokens(style="minimal-premium", font="sans")  # minimal-premium is a serif style
        self.assertEqual(tk["fonts"]["display"], "Noto Sans KR")
        self.assertEqual(tk["fontChoice"], "sans")
        sp, tk = self.tokens(font="serif")
        self.assertEqual(tk["fonts"]["body"], "Noto Serif KR")
        sp, tk = self.tokens(font="system")
        self.assertIn("system-ui", build.tokens_css(tk))
        self.assertNotIn("Noto", build.tokens_css(tk))

    def test_system_font_embeds_no_font_file(self):
        html = build_html(quiz_spec(font="system"))
        self.assertNotIn("data:font/woff2", html)

    def test_vignette_follows_light_and_dark(self):
        light = build.tokens_css({**build.make_tokens(quiz_spec(style="minimal-premium")), })
        sp = quiz_spec(style="neon-cyber")
        dark = build.tokens_css(build.make_tokens(sp))
        self.assertIn("--vig:0}", light)
        self.assertIn("--vig:.35}", dark)
        eng = (GAME / "assets" / "engine.html").read_text(encoding="utf-8")
        self.assertIn("rgba(0,0,0,var(--vig,.35))", eng)  # the engine reads it


class Specs(unittest.TestCase):
    def test_new_spec_keys(self):
        sp = quiz_spec()
        sp.update({"online": True, "back": {"href": "../index.html", "label": "사이트로"}, "head_meta": [{"name": "robots", "content": "noindex"}]})
        self.assertEqual(specs.validate(sp), [])
        for bad in ({"back": {"href": "https://x.com"}}, {"back": {"href": "javascript:alert(1)"}}, {"head_meta": [{"name": "http-equiv", "content": "x"}]}, {"online": "yes"}):
            self.assertTrue(specs.validate({**quiz_spec(), **bad}), bad)

    def test_back_link_and_head_meta_reach_the_page(self):
        sp = quiz_spec()
        sp.update({"back": {"href": "../index.html", "label": "사이트로"}, "head_meta": [{"name": "robots", "content": "noindex"}]})
        html = build_html(sp)
        self.assertIn('<meta name="robots" content="noindex">', html)
        self.assertIn('"back": {', html)
        self.assertNotIn('"creditUrl"', html)
        sp["credit"] = True
        self.assertIn('"creditUrl"', build_html(sp))


class DeviceWords(unittest.TestCase):
    def test_phone_words_mean_phone(self):
        for q in ("AI 용어 복습 게임, 선생님들이 연수 쉬는 시간에 폰으로 2분", "각자 폰으로 퀴즈", "핸드폰으로 보는 빙고", "스마트폰 퀴즈", "휴대폰으로 풀게 해 줘"):
            self.assertEqual(direction.infer(q)["device"], "phone", q)

    def test_tablet_board_and_non_phone_words(self):
        self.assertEqual(direction.infer("태블릿으로 빙고")["device"], "tablet")
        self.assertEqual(direction.infer("전자칠판 퀴즈")["device"], "board")
        self.assertIsNone(direction.infer("헤드폰 설명 슬라이드")["device"])
        self.assertEqual(direction.infer("폰트 바꿔서 칠판 퀴즈")["device"], "board")  # 폰트 = font

    def test_prefs_know_phone(self):
        prefs = load("prefs_fix", STUDIO / "prefs.py")
        self.assertIn("phone", prefs.DEVICES)


class Router(unittest.TestCase):
    SK = (ROOT / "skills" / "teacher-studio" / "SKILL.md").read_text(encoding="utf-8")

    def test_new_games_go_through_spec_build_not_fire(self):
        rows = [l for l in self.SK.splitlines() if l.startswith("|") and ("퀴즈" in l or "방탈출" in l or "빙고" in l)]
        self.assertTrue(rows)
        decided = [l for l in rows if "모든 새 게임" in l]
        self.assertEqual(len(decided), 1)
        self.assertIn("build game --spec", decided[0])
        self.assertNotIn("fire", decided[0].split("|")[2].replace("Never `fire` for a new request", ""))
        legacy = [l for l in self.SK.splitlines() if "옛 완제품 스킨을 이름으로 지목" in l]
        self.assertEqual(len(legacy), 1)
        self.assertIn("only then", legacy[0])
        self.assertIn("legacy skins are used only when the user names one", self.SK)


class SkillDescriptions(unittest.TestCase):
    def test_every_skill_has_a_proper_description(self):
        self.assertEqual(sync_shared.skill_meta_problems(), [])

    def test_the_teacher_data_regression_is_caught(self):
        broken = "---\nname: teacher-data\ndescription: Turns anyone's spreadsheets (CSV/XLSX: scores, surveys) into an easy report for teachers.\nlicense: Apache-2.0\n---\n# Teacher Studio - Data Analysis Weapon\n"
        problems = sync_shared.skill_meta_text_problems("skills/teacher-data/SKILL.md", broken, "teacher-data")
        self.assertTrue(any("not quoted" in p for p in problems), problems)
        fixed = broken.replace("description: Turns", 'description: "Turns').replace("report for teachers.", 'report for teachers."')
        self.assertEqual(sync_shared.skill_meta_text_problems("x", fixed, "teacher-data"), [])

    def test_short_or_useless_descriptions_fail(self):
        short = "---\nname: teacher-x\ndescription: Does things\n---\n"
        self.assertTrue(any("< 60" in p for p in sync_shared.skill_meta_text_problems("x", short, "teacher-x")))
        nouse = "---\nname: teacher-x\ndescription: Makes a colourful thing out of a short list of words and numbers quickly\n---\n"
        self.assertTrue(any("who/when" in p for p in sync_shared.skill_meta_text_problems("x", nouse, "teacher-x")))
        wrongname = "---\nname: other\ndescription: Makes things for teachers and anyone, use when a class needs something quick\n---\n"
        self.assertTrue(any("name must be" in p for p in sync_shared.skill_meta_text_problems("x", wrongname, "teacher-x")))

    def test_teacher_data_description_says_what_and_when(self):
        t = (ROOT / "skills" / "teacher-data" / "SKILL.md").read_text(encoding="utf-8")
        desc = re.search(r"^description:\s*(.*)$", t, re.M).group(1)
        self.assertTrue(desc.startswith('"') and desc.endswith('"'))
        self.assertIn("teacher or anyone", desc)
        self.assertIn("Use when", desc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
