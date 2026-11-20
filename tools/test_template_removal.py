# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Template removal (2026-11): content recipes wired in, examples are fixtures, example-likeness WARN, content-driven structure,
wider game layouts, a no-drag path for drag games, Chart.js parses as ES2017.
Browser tests skip when no headless Chrome/Edge is found.   Run: py tools/test_template_removal.py"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
GAME = SK / "teacher-game"
os.environ.setdefault("PYTHONUTF8", "1")
sys.path.insert(0, str(GAME / "scripts"))
SILENT = ("(function(){try{window.speechSynthesis.speak=function(){};}catch(e){}try{var oc=AudioNode.prototype.connect;"
          "AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}catch(e){}})()")


def browser(p):
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(args=["--mute-audio"], **kw)
        except Exception:
            continue
    return None


def build_game(spec: Path, out: Path, seed: int = 5) -> None:
    subprocess.run([sys.executable, str(GAME / "scripts" / "build.py"), "--spec", str(spec), "--out", str(out), "--no-fonts", "--no-check", "--seed", str(seed)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)


class NoDragPath(unittest.TestCase):
    """content-items.md: a sort / drag task must be doable without dragging (tap, tap) and by keyboard."""

    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("playwright not installed")
        cls.tmp = Path(tempfile.mkdtemp(prefix="nodrag-"))
        cls.html = cls.tmp / "sort.html"
        build_game(GAME / "assets" / "spec-examples" / "f-sort-recycle.json", cls.html)
        cls.pw = sync_playwright().start()
        cls.b = browser(cls.pw)
        if cls.b is None:
            cls.pw.stop()
            raise unittest.SkipTest("no headless browser")

    @classmethod
    def tearDownClass(cls):
        cls.b.close()
        cls.pw.stop()

    def page(self):
        pg = self.b.new_page(viewport={"width": 1920, "height": 1080})
        pg.add_init_script(SILENT)
        pg.goto(self.html.resolve().as_uri())
        pg.wait_for_timeout(600)
        pg.evaluate("advanceTime(1500)")
        pg.click("#t-start")
        pg.wait_for_timeout(3700)
        pg.evaluate("advanceTime(1200)")
        pg.wait_for_timeout(300)
        self.addCleanup(pg.close)
        return pg

    def state(self, pg):
        return json.loads(pg.evaluate("render_game_to_text()"))

    def right_bin(self, pg) -> int:
        """Index of the bin the card on screen belongs to (read from the page's own spec, by the card text)."""
        return pg.evaluate("(function(){var q=document.getElementById('ts-card').textContent,its=window.GAME.items||window.GAME.spec.items,a='';"
                           "its.forEach(function(it){if(it.q===q)a=it.a;});var b=-1;Array.prototype.forEach.call(document.querySelectorAll('.ts-bin'),"
                           "function(e,i){if(e.getAttribute('aria-label').indexOf(a+' 통')===0)b=i;});return b;})()")

    def test_number_key_places_the_card(self):
        pg = self.page()
        st = self.state(pg)
        pg.keyboard.press(str(self.right_bin(pg) + 1))
        pg.wait_for_timeout(200)
        self.assertEqual(self.state(pg)["correct"], st.get("correct", 0) + 1)

    def test_tab_enter_places_the_card(self):
        pg = self.page()
        n = self.right_bin(pg)
        pg.focus("#ts-card")
        pg.keyboard.press("Enter")
        self.assertTrue(pg.evaluate("document.getElementById('ts-card').classList.contains('sel')"))
        self.assertEqual(pg.evaluate("document.querySelectorAll('.ts-bin')[0].getAttribute('role')+document.querySelectorAll('.ts-bin')[0].tabIndex"), "button0")
        pg.evaluate(f"document.querySelectorAll('.ts-bin')[{n}].focus()")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(200)
        self.assertEqual(self.state(pg)["correct"], 1)

    def test_tap_then_tap_places_the_card(self):
        pg = self.page()
        n = self.right_bin(pg)
        pg.click("#ts-card")  # a tap (no movement) picks the card up
        self.assertTrue(pg.evaluate("document.getElementById('ts-card').classList.contains('sel')"))
        pg.evaluate(f"document.querySelectorAll('.ts-bin')[{n}].click()")
        pg.wait_for_timeout(200)
        self.assertEqual(self.state(pg)["correct"], 1)

    def test_bins_are_labelled_without_colour(self):
        pg = self.page()
        labels = pg.evaluate("Array.prototype.map.call(document.querySelectorAll('.ts-bin .ts-bin-k'),function(e){return e.textContent})")
        self.assertEqual(labels, [str(i + 1) for i in range(len(labels))])
        self.assertGreaterEqual(len(labels), 2)


class ChartJsIsES2017(unittest.TestCase):
    def test_vendored_chartjs_has_no_class_fields(self):
        import hashlib
        man = json.loads((ROOT / "shared" / "vendor" / "manifest.json").read_text(encoding="utf-8"))["libs"]["chartjs"]
        data = (ROOT / "shared" / "vendor" / man["dir"] / man["js"]).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), man["sha256"])
        self.assertEqual(len(data), man["bytes"])
        self.assertNotIn(b"static defaults=", data)
        self.assertNotIn(b"{...", data)


class ContentRecipesWiredIn(unittest.TestCase):
    POINTERS = {"teacher-studio": "references/content-writing.md", "teacher-slides": "references/content-slides.md", "teacher-game": "references/content-items.md",
                "teacher-docs": "references/content-docs.md", "teacher-data": "references/content-data.md", "teacher-motion": "references/content-motion.md"}

    def test_every_skill_points_at_its_recipe_and_the_gate(self):
        for sk, rec in self.POINTERS.items():
            t = (SK / sk / "SKILL.md").read_text(encoding="utf-8")
            line = next((ln for ln in t.splitlines() if ln.startswith("Content quality first:")), "")
            self.assertIn(rec, line, sk)
            self.assertIn("shared/content/CONTENT-RULES.md", line, sk)
            self.assertTrue((SK / sk / rec).is_file(), (sk, rec))
        studio = (SK / "teacher-studio" / "SKILL.md").read_text(encoding="utf-8")
        for rec in ("content-lesson.md", "content-promo.md", "content-plan.md", "content-webapp.md"):
            self.assertIn("references/" + rec, studio)

    def test_installed_skills_carry_the_content_rules(self):
        src = (ROOT / "shared" / "content" / "CONTENT-RULES.md").read_bytes()
        for sk in self.POINTERS:
            self.assertEqual((SK / sk / "shared" / "content" / "CONTENT-RULES.md").read_bytes(), src, sk)


class FixturesNotPatterns(unittest.TestCase):
    FOLDERS = ("teacher-game/assets/spec-examples", "teacher-slides/assets/spec-examples", "teacher-slides/assets/spec-examples/context", "teacher-docs/assets/examples",
               "teacher-data/assets/spec-examples", "teacher-studio/assets/webapp/examples", "teacher-class-tools/assets/spec-examples")

    def test_every_example_is_marked_as_a_fixture(self):
        n = 0
        for folder in self.FOLDERS:
            for f in sorted((SK / folder).glob("*.json")):
                self.assertIn("not a pattern", json.loads(f.read_text(encoding="utf-8")).get("_fixture", ""), f.name)
                n += 1
        self.assertGreaterEqual(n, 40)

    def test_fixtures_do_not_pin_a_look(self):
        for f in sorted((GAME / "assets" / "spec-examples").glob("*.json")):
            self.assertNotIn("seed", json.loads(f.read_text(encoding="utf-8")).get("design") or {}, f.name)
        apps = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((SK / "teacher-studio/assets/webapp/examples").glob("*.json"))]
        shared = set.intersection(*[set(str(a.get("words", "")).split()) for a in apps])
        self.assertEqual(shared, set(), "web app fixtures share a look word")

    def test_recipes_do_not_tell_the_model_to_copy_an_example(self):
        files = [f for sk in SK.iterdir() for f in [sk / "SKILL.md", *sorted((sk / "references").glob("*.md"))] if f.is_file()]
        for f in files:
            t = f.read_text(encoding="utf-8")
            for bad in ("closest file from", "closest example", "copy an example", "copy from `assets", "start from `assets/examples"):
                self.assertNotIn(bad, t, f"{f.parent.name}/{f.name}")
        slides = (SK / "teacher-slides" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("빛의 반사와 굴절", slides)   # the class recipe no longer carries one unit as its example
        self.assertNotIn("빛과 파동", (GAME / "SKILL.md").read_text(encoding="utf-8"))

    def test_a_topic_word_does_not_pull_a_whole_legacy_scene(self):
        import theme_auto
        base = {"mechanic": "quiz", "items": [{"q": "세포막이 하는 일은?", "choices": ["가", "나", "다", "라"], "answer": 0}] * 4}
        for title in ("세포 퀴즈쇼", "재활용 분리배출 퀴즈", "우리 반 퀴즈쇼"):
            au = theme_auto.compose({**base, "title": title, "design": {"seed": 3}})
            self.assertFalse(au.get("named"), (title, au.get("named")))
        named = theme_auto.compose({**base, "title": "우리 반 퀴즈", "design": {"seed": 3, "words": ["방송국"]}})
        self.assertEqual(named.get("named"), "tv-studio")


class ExampleLikeness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "shared" / "tools"))
        import example_likeness
        cls.el = example_likeness
        cls.decks = SK / "teacher-slides" / "assets" / "spec-examples"
        cls.fix = json.loads((cls.decks / "context" / "class-water-cycle.json").read_text(encoding="utf-8"))

    def level(self, res):
        return res[0][0] if res else ""

    def test_fixture_itself_passes_and_a_fresh_spec_passes(self):
        self.assertIn("fixture", self.el.check_spec(self.fix, [self.decks])[0][1])
        fresh = {"title": "우리 마을 지도 읽기", "slides": [{"type": "title", "title": "우리 마을 지도 읽기"}, {"type": "statement", "text": "지도에서 학교는 어디에 있을까요?"},
                 {"type": "steps", "title": "방위 찾는 차례", "steps": [{"title": "북쪽 표시 찾기"}, {"title": "기준 건물 정하기"}, {"title": "방향 말하기"}]},
                 {"type": "closing", "title": "다음 시간에는 축척을 배워요"}]}
        self.assertEqual(self.level(self.el.check_spec(fresh, [self.decks])), "PASS")

    def test_copied_sentences_warn(self):
        spec = json.loads(json.dumps(self.fix))
        spec.pop("_fixture")
        spec["slides"][0]["title"] = "제목만 바꾼 덱"
        res = self.el.check_spec(spec, [self.decks])
        self.assertEqual(self.level(res), "WARN")
        self.assertIn("예시를 그대로 따라간 것 같아요", res[0][1])
        spec["_fixture"] = "left in"   # the mark does not excuse a changed copy
        self.assertEqual(self.level(self.el.check_spec(spec, [self.decks])), "WARN")

    def test_same_skeleton_with_other_words_warns(self):
        spec = json.loads(json.dumps(self.fix))
        spec.pop("_fixture")
        count = [0]

        def swap(o):
            if isinstance(o, dict):
                return {k: (v if k in self.el.CONFIG_KEYS else swap(v)) for k, v in o.items()}
            if isinstance(o, list):
                return [swap(v) for v in o]
            if isinstance(o, str) and len(o) >= 4:
                count[0] += 1
                return ("바꾼 문장 %d번 " % count[0] + "가" * len(o))[:max(len(o), 8)]
            return o
        res = self.el.check_spec(swap(spec), [self.decks])
        self.assertEqual(self.level(res), "WARN", res)
        self.assertIn("뼈대", res[0][1])

    def test_finished_page_is_checked_too(self):
        ex = SK / "teacher-studio" / "assets" / "webapp" / "examples"
        sys.path.insert(0, str(SK / "teacher-studio" / "scripts"))
        import build_webapp
        import check_webapp
        spec = json.loads((ex / "speed-sim.json").read_text(encoding="utf-8"))
        page, _ = build_webapp.build(spec, fonts=False)
        like = [m for lv, m in check_webapp.static_checks(page) if "example-likeness" in m or "예시를" in m]
        self.assertIn("fixture", like[0])
        spec.pop("_fixture")
        spec["title"] = "빠르기 실험실"
        page, _ = build_webapp.build(spec, fonts=False)
        warn = [m for lv, m in check_webapp.static_checks(page) if lv == "WARN" and "예시를 그대로 따라간 것 같아요" in m]
        self.assertEqual(len(warn), 1)
        spec = {"title": "분수 막대", "subtitle": "초4 수학", "words": "수학 종이", "ai": "none", "about": "분모와 분자를 바꾸면 막대가 어떻게 나뉘는지 보여 줘요.",
                "parts": [{"type": "custom", "name": "막대 나누기", "html": '<label for="n">분모</label><input id="n" type="number" value="4" autocomplete="off">', "js": ""}]}
        page, _ = build_webapp.build(spec, fonts=False)
        self.assertEqual([lv for lv, m in check_webapp.static_checks(page) if "example-likeness" in m], ["PASS"])


class ContentDrivenStructure(unittest.TestCase):
    def test_slide_type_follows_the_shape_of_the_content(self):
        sys.path.insert(0, str(SK / "teacher-slides" / "scripts"))
        import deck_shape as S
        slides = [{"title": "텃밭 보고"}, {"type": "auto", "title": "숫자", "items": ["3명: 물 주기 당번", "12개: 심은 모종"]},
                  {"title": "달력", "items": ["3월 4일: 씨앗 준비", "4월 2일: 모종 옮기기", "6월 20일: 수확"]}, {"q": "싹이 트려면?", "choices": ["물", "돌"], "answer": 0},
                  {"title": "도구", "items": ["삽: 흙을 뒤집는다", "호미: 풀을 뽑는다", "물뿌리개: 물을 준다"]}, {"title": "둘 비교", "a": {"label": "봄", "items": ["씨"]}, "b": {"label": "가을", "items": ["열매"]}},
                  {"text": "기르는 일은 기다리는 일이다"}, {"title": "고맙습니다"}]
        got = [x["type"] for x in S.resolve(slides)]
        self.assertEqual(got, ["title", "bignumbers", "timeline", "quiz", "table", "compare", "statement", "closing"])
        typed = [{"type": "bullets", "title": "차례", "items": ["먼저 흙을 고른다", "다음 씨앗을 넣는다", "마지막으로 물을 준다"]}]
        self.assertEqual(S.resolve(typed), typed)                      # a typed slide is never changed
        self.assertTrue(any("steps" in n for n in S.notes(typed)))     # it gets a NOTE instead

    def test_auto_slides_build_into_a_deck(self):
        sys.path.insert(0, str(SK / "teacher-slides" / "scripts"))
        import deck
        spec = {"title": "텃밭 보고", "purpose": "발표", "slides": [{"type": "title", "title": "텃밭 보고"}, {"type": "auto", "title": "숫자로 보기", "items": ["3명: 물 주기 당번", "12개: 심은 모종"]},
                {"type": "auto", "title": "달력", "items": ["3월 4일: 씨앗 준비", "4월 2일: 모종 옮기기", "6월 20일: 수확"]}, {"type": "closing", "title": "고맙습니다"}]}
        with tempfile.TemporaryDirectory() as td:
            rep = deck.build_deck(spec, Path(td), Path(td) / "d.html", seed=3)
            self.assertTrue(rep["ok"], rep.get("errors"))
            html = (Path(td) / "d.html").read_text(encoding="utf-8")
            self.assertIn("모종 옮기기", html)

    def test_game_layouts_cover_different_parts_of_the_stage(self):
        import itertools
        import re as _re
        import layout_auto as L
        css = (GAME / "assets" / "layouts" / "layouts.css").read_text(encoding="utf-8")
        boxes = {"stack": [(0, 0, 1, 1)]}
        for name, body in _re.findall(r"body\[data-layout=(\w+)\]\{(--qx:[^}]+)\}", css):
            v = {k: float(x) for k, x in _re.findall(r"--(\w+):([\d.]+)", body)}
            boxes[name] = [(v["qx"], v["qy"], v["qw"], v["qh"]), (v["ax"], v["ay"], v["aw"], v["ah"])]
        self.assertEqual(set(boxes), set(L.LAYOUTS))

        def cells(rects):
            return {(x, y) for x in range(40) for y in range(40) if any(r[0] <= (x + .5) / 40 <= r[0] + r[2] and r[1] <= (y + .5) / 40 <= r[1] + r[3] for r in rects)}
        cs = {k: cells(v) for k, v in boxes.items()}
        pairs = [len(cs[a] & cs[b]) / len(cs[a] | cs[b]) for a, b in itertools.combinations(sorted(cs), 2)]
        self.assertLess(sum(pairs) / len(pairs), 0.6)                       # the footprints overlap by well under two thirds on average
        self.assertGreaterEqual(sum(1 for p in pairs if p < 0.5), len(pairs) // 3)

    def test_game_layout_rules_follow_the_content(self):
        import layout_auto as L
        short = {"mechanic": "quiz", "items": [{"q": "가장 큰 행성은?", "choices": ["목성", "토성", "지구", "화성"]}] * 6}
        medium = {"mechanic": "quiz", "items": [{"q": "긴 보기", "choices": ["보기가 조금 긴 첫째 문장", "둘째", "셋째", "넷째"]}] * 6}
        long_ = {"mechanic": "quiz", "items": [{"q": "긴 보기", "choices": ["보기가 아주 아주 긴 첫째 문장이에요 정말", "둘째", "셋째", "넷째"]}] * 6}
        w = L.layout_weights({}, L.content_features(short))
        self.assertEqual(set(w), set(L.LAYOUTS))
        self.assertEqual(set(L.layout_weights({}, L.content_features(medium))) & set(L.ROW_LAYOUTS), set())
        self.assertEqual(set(L.layout_weights({}, L.content_features(long_))), {"stack", "split"})
        self.assertNotIn("news", L.layout_weights({}, L.content_features(short), "escape"))                         # escape: never the lower third
        self.assertIn("left", L.layout_weights({}, L.content_features(short), "escape"))                             # short answers: the side block fits
        self.assertEqual(set(L.layout_weights({}, L.content_features(medium), "escape")) & set(L.ESCAPE_OUT), set())  # longer answers: it does not
        self.assertEqual(L.compose({**short, "design": {"seed": 1, "layout": "left"}})["ans"], "two")
        self.assertEqual(L.compose({**medium, "design": {"seed": 1, "layout": "left"}})["ans"], "list")

    def test_web_apps_without_a_style_word_do_not_share_one_default_style(self):
        sys.path.insert(0, str(SK / "teacher-studio" / "scripts"))
        import build_webapp as W
        part = [{"type": "custom", "name": "계산", "html": "<p>x</p>"}]
        specs = [{"title": t, "subtitle": "모임", "parts": part} for t in ("회비 나누기", "걸음 수 기록", "책 대출 장부", "화분 물 주기", "달리기 기록", "용돈 계획")]
        self.assertGreaterEqual(len({W.make_tokens(sp)["picked"] for sp in specs}), 3)
        self.assertEqual(W.make_tokens(specs[0])["picked"], W.make_tokens(dict(specs[0]))["picked"])     # same request -> same look
        self.assertEqual(W.make_tokens({**specs[0], "style": "minimal-premium"})["picked"], "minimal-premium")

    def test_different_requests_with_one_seed_get_different_compositions(self):
        import layout_auto as L
        seen = set()
        for i in range(12):
            spec = {"mechanic": "quiz", "title": f"퀴즈 {i}", "items": [{"q": f"{i}번 주제의 문제 {k}", "choices": ["가", "나", "다", "라"]} for k in range(6)], "design": {"seed": 7}}
            seen.add(L.compose(spec, None, "", "minimal-premium")["layout"])
            self.assertEqual(L.compose(spec)["layout"], L.compose(json.loads(json.dumps(spec)))["layout"])   # same request + seed -> same game
        self.assertGreaterEqual(len(seen), 4, seen)


if __name__ == "__main__":
    unittest.main(verbosity=1)
