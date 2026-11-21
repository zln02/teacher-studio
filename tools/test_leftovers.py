#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Leftovers (docs/research/leftovers-2026-11.md): colour with meaning, the page count the user named, one example note,
the unknowns policy on HTML pages, and how the skills tell an agent to call Python."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
for p in (ROOT / "shared" / "design", ROOT / "shared" / "tools", SK / "teacher-slides" / "scripts"):
    sys.path.insert(0, str(p))
import meaning  # noqa: E402
import placeholders as ph  # noqa: E402

LABELS = ["🟢 초록불", "🔴 빨간불", "파란불", "노란불", "금", "은", "동", "(금)", "금메달", "🥇 1등", "청팀", "백팀", "홍팀", "빨강 팀", "1. 노란색 통", "보라",
          "금요일 일정", "지금 시작", "운동장", "은행나무", "이것 보라", "초록불과 빨간불", "세종대왕 동상", "신호등 색깔의 뜻", "플라스틱", "호랑이팀"]
CROSSING = {"context": "class", "audience": "초등학교 2학년", "target_slides": 6, "title": "안전하게 길 건너기", "slides": [
    {"type": "title", "title": "안전하게 길 건너기", "subtitle": "초등학교 2학년 안전한 생활"},
    {"type": "bullets", "title": "오늘 배울 것", "items": ["🚦 신호등 색깔의 뜻을 알아요", "🚸 건너는 순서를 말해요"]},
    {"type": "compare", "title": "신호등 색깔의 뜻", "a": {"label": "🟢 초록불", "items": ["🚶 건너도 돼요", "👀 먼저 살펴요"]}, "b": {"label": "🔴 빨간불", "items": ["🛑 멈춰요", "🧍 기다려요"]}},
    {"type": "bullets", "title": "약속", "items": ["🚦 초록불에 건너요", "🛑 빨간불에는 멈춰요", "👀 건너기 전에 꼭 살펴요"]},
    {"type": "quiz", "q": "빨간불일 때 어떻게 할까요?", "choices": ["🚶 뛰어서 건너요", "🛑 멈춰서 기다려요"], "answer": 1, "explain": "빨간불에는 멈춰요."},
]}


def hue(h):
    return meaning._hue(h)


class Meaning(unittest.TestCase):
    def test_words_that_name_a_colour(self):
        want = {"🟢 초록불": "green", "🔴 빨간불": "red", "파란불": "green", "노란불": "amber", "금": "gold", "은": "silver", "동": "bronze", "청팀": "blue",
                "백팀": "white", "빨강 팀": "red", "1. 노란색 통": "yellow", "🥇 1등": "gold"}
        for t, k in want.items():
            self.assertEqual(meaning.key_of(t), k, t)
        for t in ("금요일 일정", "지금 시작", "운동장", "은행나무", "이것 보라", "세종대왕 동상", "신호등 색깔의 뜻", "플라스틱", "호랑이팀"):
            self.assertIsNone(meaning.key_of(t), t)
        self.assertIsNone(meaning.color_of("초록불과 빨간불"))  # two colours in one label decide nothing
        self.assertIsNone(meaning.color_of("빨간 사과와 초록 사과를 바구니에 담아서 친구에게 가져다 주었어요 정말로"))  # a sentence is not a label

    def test_assign_keeps_meaning_and_avoids_lookalikes(self):
        tones = ["#D94A00", "#6A5AE0", "#12A150"]
        self.assertEqual(meaning.assign(["가", "나", "다"], tones), tones)                      # nothing named: the rotation, untouched
        got = meaning.assign(["초록불", "빨간불"], tones)
        self.assertEqual(got, [meaning.color_of("초록불"), meaning.color_of("빨간불")])
        got = meaning.assign(["초록불", "기다려요", "가요"], ["#12A150", "#6A5AE0", "#D94A00"])
        self.assertFalse(meaning.alike(got[1], got[0]))                                         # a neighbour never keeps a look-alike green
        for c in set(meaning._HEX.values()):
            self.assertGreaterEqual(meaning.contrast(meaning.on(c), c), 4.0, c)                 # the text on every named colour reads

    def test_safe_and_danger_are_green_and_red_only_as_a_pair(self):
        tones = ["#D94A00", "#6A5AE0", "#12A150"]
        self.assertEqual(meaning.assign(["안전한 행동", "위험한 행동"], tones), [meaning._HEX["green"], meaning._HEX["red"]])
        self.assertEqual(meaning.assign(["안전하게 건너요", "손을 들어요"], tones), tones[:2])   # one side alone decides nothing
        self.assertFalse(meaning.any_named(["안전한 생활", "안전 약속"]))
        js = "var window={};" + meaning.js() + ";console.log(JSON.stringify(window.TSMeaning.assign(['안전한 행동','위험한 행동'],['#D94A00','#6A5AE0'])));"
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "m.js"
            f.write_text(js, encoding="utf-8")
            r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            self.assertEqual(json.loads(r.stdout), [meaning._HEX["green"], meaning._HEX["red"]])

    def test_js_table_agrees_with_python(self):
        js = "var window={};" + meaning.js() + "\nconsole.log(JSON.stringify(" + json.dumps(LABELS, ensure_ascii=False) + ".map(function(t){return window.TSMeaning.color(t);})));"
        self.assertNotRegex(meaning.js(), r"\?\.|\?\?|\(\?<[=!]")                               # old school Chrome: no ?. ?? or lookbehind
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "m.js"
            f.write_text(js, encoding="utf-8")
            r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0 and "node" in (r.stderr or "").lower() and "not" in (r.stderr or "").lower():
            self.skipTest("node not available")
        self.assertEqual(json.loads(r.stdout), [meaning.color_of(t) for t in LABELS], r.stderr[:300])

    def test_pptx_compare_heads_and_list_badges_take_the_named_colour(self):
        try:
            import pptx  # noqa: F401
        except ImportError:
            self.skipTest("python-pptx not installed")
        import deck_pptx
        from pptx import Presentation
        g, r_ = meaning.color_of("초록불").lstrip("#").upper(), meaning.color_of("빨간불").lstrip("#").upper()
        for seed in (1, 2, 3, 7):
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / "d.pptx"
                rep = deck_pptx.build_pptx(json.loads(json.dumps(CROSSING)), Path(td), out, seed)
                self.assertTrue(rep.get("ok"), rep.get("errors"))
                prs = Presentation(str(out))
                fills = {}
                for sl in prs.slides:
                    for sh in sl.shapes:
                        if sh.has_text_frame and sh.text_frame.text.strip() in ("초록불", "빨간불"):
                            try:
                                fills[sh.text_frame.text.strip()] = str(sh.fill.fore_color.rgb)
                            except Exception:
                                pass
                self.assertEqual(fills.get("초록불"), g, (seed, fills))
                self.assertEqual(fills.get("빨간불"), r_, (seed, fills))

    def test_pptx_diagram_points_take_the_named_colour(self):
        try:
            import pptx  # noqa: F401
        except ImportError:
            self.skipTest("python-pptx not installed")
        import deck_pptx
        from pptx import Presentation
        spec = {"context": "class", "audience": "초등학교 2학년", "title": "신호등", "slides": [
            {"type": "title", "title": "신호등"},
            {"type": "diagram", "title": "신호등 색깔", "shapes": [{"kind": "circle", "cx": 50, "cy": 15, "r": 8, "fill": "#D62828"}, {"kind": "circle", "cx": 50, "cy": 42, "r": 8, "fill": "#1FA34A"}, {"kind": "label", "x": 70, "y": 15, "text": "멈춰요"}],
             "points": ["빨간불: 멈춰요", "노란불: 조심해요", "초록불: 건너요"]}]}
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "d.pptx"
            self.assertTrue(deck_pptx.build_pptx(spec, Path(td), out, 3).get("ok"))
            bars = ["#" + str(sh.fill.fore_color.rgb) for sh in Presentation(str(out)).slides[1].shapes if sh.name == "accent" and sh.height > sh.width * 3]
        self.assertEqual([b.upper() for b in bars[-3:]], [meaning.color_of(x).upper() for x in ("빨간불", "노란불", "초록불")])

    def test_pptx_emphasised_colour_word_is_written_in_its_colour(self):
        try:
            import pptx  # noqa: F401
        except ImportError:
            self.skipTest("python-pptx not installed")
        import deck_pptx
        from pptx import Presentation
        spec = {"context": "class", "audience": "초등학교 2학년", "title": "신호등", "slides": [
            {"type": "title", "title": "신호등"}, {"type": "bullets", "title": "약속", "items": ["**빨간불**에는 멈춰요", "**초록불**에 살피고 건너요", "**천천히** 걸어요"]}]}
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "d.pptx"
            self.assertTrue(deck_pptx.build_pptx(spec, Path(td), out, 5).get("ok"))
            runs = {}
            for sl in Presentation(str(out)).slides:
                for sh in sl.shapes:
                    if sh.has_text_frame:
                        for para in sh.text_frame.paragraphs:
                            for r in para.runs:
                                if r.text in ("빨간불", "초록불", "천천히"):
                                    runs[r.text] = "#" + str(r.font.color.rgb)

        def near(a, b):
            d = abs(hue(a) - hue(b)) % 360
            return min(d, 360 - d) < 25
        self.assertTrue(near(runs["빨간불"], meaning.color_of("빨간불")), runs)
        self.assertTrue(near(runs["초록불"], meaning.color_of("초록불")), runs)
        self.assertNotEqual(runs["빨간불"], runs["초록불"])

    def test_pptx_gate_warns_on_a_colour_word_in_another_colour(self):
        try:
            from pptx import Presentation
            from pptx.dml.color import RGBColor
            from pptx.util import Inches, Pt
        except ImportError:
            self.skipTest("python-pptx not installed")
        import pptx_check
        prs = Presentation()
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        for k, (text, rgb) in enumerate((("초록불", "CF4600"), ("빨간불", "E5352B"), ("노란불", "1F2A44"), ("초록불", "075D50"))):
            tb = sl.shapes.add_textbox(Inches(1), Inches(1 + k), Inches(3), Inches(0.8))
            r = tb.text_frame.paragraphs[0].add_run()
            r.text, r.font.size = text, Pt(28)
            r.font.color.rgb = RGBColor.from_string(rgb)
        self.assertEqual(pptx_check.colour_word_misses(prs), [(1, "초록불")])  # orange 초록불 only: dark ink and a dark green are fine

    def test_web_compare_and_game_bins_and_team_tools(self):
        import deck_layouts as dl
        src = (SK / "teacher-slides" / "scripts" / "deck_layouts.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(src.count("_named_sides(ctx, a, b_)"), 3)                       # all three compare layouts ask
        self.assertTrue(callable(dl._named_sides))
        sort_js = (SK / "teacher-game" / "assets" / "components" / "sort.js").read_text(encoding="utf-8")
        self.assertIn("TSMeaning.assign(bins, BC)", sort_js)
        self.assertNotIn("BC[i % 4] + ';width", sort_js)
        tools_js = (SK / "teacher-class-tools" / "assets" / "tools.js").read_text(encoding="utf-8")
        self.assertIn("TSMeaning.assign(names, TEAMC)", tools_js)
        for f in (SK / "teacher-game" / "scripts" / "build.py", SK / "teacher-class-tools" / "scripts" / "build_tool.py"):
            self.assertIn("meaning.js()", f.read_text(encoding="utf-8"), f.name)

    def test_built_sort_game_colours_named_bins(self):
        spec = {"title": "색깔 통에 넣기", "mechanic": "sort", "bins": ["빨강 통", "파랑 통", "노랑 통"], "design": {"seed": 3},
                "items": [{"q": "사과", "a": "빨강 통"}, {"q": "바다", "a": "파랑 통"}, {"q": "바나나", "a": "노랑 통"}, {"q": "딸기", "a": "빨강 통"},
                          {"q": "하늘", "a": "파랑 통"}, {"q": "병아리", "a": "노랑 통"}]}
        with tempfile.TemporaryDirectory() as td:
            sp, out = Path(td) / "s.json", Path(td) / "g.html"
            sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SK / "teacher-game" / "scripts" / "build.py"), "--spec", str(sp), "--out", str(out), "--no-fonts", "--no-check", "--ok-content"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertTrue(out.exists(), r.stdout[-600:] + r.stderr[-600:])
            html = out.read_text(encoding="utf-8")
        self.assertIn("window.TSMeaning=", html)
        self.assertIn("TS:MEANING", html)


class Length(unittest.TestCase):
    def setUp(self):
        import deck_context
        import deck_shape
        self.dctx, self.shape = deck_context, deck_shape
        self.body = [{"type": "bullets", "title": "a", "items": ["x", "y"]}]

    def deck(self, n, want, quiz=False):
        sl = [{"type": "title", "title": "t"}] + self.body * (n - 1 - (1 if quiz else 0)) + ([{"type": "quiz", "q": "q", "choices": ["a", "b"], "answer": 0}] if quiz else [])
        return {"context": "class", "target_slides": want, "slides": sl}

    def warn(self, spec):
        errs, warns = self.dctx.lint(spec)
        return [w for w in warns if w.startswith("장수:")], [x for x in errs if "요청" in x]

    def test_lands_on_n(self):
        self.assertEqual(self.warn(self.deck(8, 8)), ([], []))                    # N written, no quiz: N pages
        self.assertEqual(self.warn(self.deck(7, 8, quiz=True)), ([], []))         # N - 1 written + the answers slide: N pages
        self.assertEqual(self.warn(self.deck(8, 8, quiz=True)), ([], []))         # N written + the answers slide: N + 1, allowed

    def test_over_and_under_warn_far_over_stops(self):
        w, e_ = self.warn(self.deck(9, 8))                                         # one over with no answers slide to excuse it
        self.assertTrue(w and "요청은 8장인데 9장" in w[0] and not e_, (w, e_))
        w, e_ = self.warn(self.deck(11, 10, quiz=True))                            # 12 pages for 「10장」
        self.assertTrue(w and "12장" in w[0] and not e_, (w, e_))
        w, e_ = self.warn(self.deck(6, 8))
        self.assertTrue(w and "한 장 더" in w[0], w)
        w, e_ = self.warn(self.deck(12, 8))
        self.assertTrue(e_, "far over still stops the build")
        self.assertEqual(self.shape.length(self.deck(8, 8, quiz=True)), {"want": 8, "got": 9, "answers": 1, "over": 0, "under": 0, "hard": False})

    def test_deck_shape_cli_prints_the_warn(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "d.json"
            f.write_text(json.dumps(self.deck(10, 8), ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SK / "teacher-slides" / "scripts" / "deck_shape.py"), str(f)], capture_output=True, text=True, encoding="utf-8")
        self.assertIn("WARN 요청은 8장인데 10장", r.stdout)


class OneNote(unittest.TestCase):
    def test_example_words_in_two_source_lines_stop_the_build(self):
        import deck_context as dctx
        sl = [{"type": "title", "title": "운영 결과"},
              {"type": "table", "title": "실적", "columns": ["항목", "값"], "rows": [["참여", "120명"]], "source": "자료: 가상 운영 대장 · 2026. 11. 20. 기준 예시"},
              {"type": "table", "title": "예산", "columns": ["항목", "값"], "rows": [["집행", "300만 원"]], "source": "자료: 예시 예산 집행표"}]
        errs, _ = dctx.lint({"context": "public", "slides": sl})
        hit = [x for x in errs if "되풀이" in x]
        self.assertTrue(hit and "slide 2, 3" in hit[0] and "fillins" in hit[0], errs)
        sl[2]["source"] = "우리 학교, 예산 집행표(2026)"
        errs, _ = dctx.lint({"context": "public", "slides": sl})
        self.assertFalse([x for x in errs if "되풀이" in x])                     # one line is the one note

    def test_shipped_report_fixtures_follow_the_rule(self):
        import deck_context as dctx
        for f in sorted((SK / "teacher-slides" / "assets" / "spec-examples").rglob("*.json")):
            spec = json.loads(f.read_text(encoding="utf-8"))
            n = sum(1 for it in spec.get("slides") or [] if isinstance(it, dict) and dctx._EX_SRC.search(" ".join(str(it.get(k) or "") for k in ("source", "footnote", "caption"))))
            self.assertLessEqual(n, 1, f.name)

    def test_recipe_says_it(self):
        t = (SK / "teacher-slides" / "SKILL.md").read_text(encoding="utf-8") + (SK / "teacher-slides" / "references" / "content-slides.md").read_text(encoding="utf-8")
        self.assertIn("the source names the record", t)
        self.assertIn("it names the record only", t)
        self.assertIn("land on that number", t)
        self.assertIn("Colour words keep their colour", t)


GOOD = ('<!DOCTYPE html><html lang="ko"><head><title>소화 기관 퀴즈</title></head><body><h1>소화 기관 퀴즈</h1><input placeholder="답을 입력하세요" aria-label="답">'
        '<p>여기에 답을 입력하고 확인을 눌러요</p><script>var Q=[{q:"□ 안에 알맞은 말은? 위에서 ___ 이(가) 나와요",a:"위액"},{q:"[1단계] 입 → 식도",a:"000점"},'
        '{t:"대진 미정"},{t:"수도는 ○○이다"},{t:"제출 전 확인하기"},{t:"이름 입력 필요"}];</script></body></html>')
BAD = ('<!DOCTYPE html><html lang="ko"><head><title>[학교명] 퀴즈</title></head><body><h1>[학교명] 퀴즈</h1><p>교사 초안</p><p>{{이름}} 님</p>'
       '<script>var Q=[{q:"담당: 확인 필요",a:"추후 확정"},{q:"○○초 6학년",a:"집계 필요"},{q:"20XX년 (예시)",a:"(날짜 입력)"}];</script></body></html>')


class HtmlPolicy(unittest.TestCase):
    def lv(self, res, word):
        return [l for l, m in res if word in m]

    def test_a_working_page_is_not_a_gap(self):
        res = ph.html_checks(GOOD)
        self.assertEqual({l for l, _ in res}, {"PASS"}, res)                      # cloze marks, [1단계], 미정, 000점, a form's own hints

    def test_filler_stamp_and_slots_fail(self):
        res = ph.html_checks(BAD)
        self.assertEqual(self.lv(res, "빈말"), ["FAIL"])
        self.assertEqual(self.lv(res, "도장"), ["FAIL"])
        slots = [m for l, m in res if "빈자리" in m][0]
        for s in ("[학교명]", "{{이름}}", "○○초", "20XX", "(예시)", "(날짜 입력)"):
            self.assertIn(s, slots + str(ph.html_slots(*ph.html_texts(BAD))))
        self.assertEqual(self.lv(res, "빈자리"), ["FAIL"])
        one = ph.html_checks(GOOD.replace("대진 미정", "장소: 확인 필요"))
        self.assertEqual(self.lv(one, "빈말"), ["WARN"])                          # one or two = WARN, as in documents
        twice = ph.html_checks(GOOD.replace("대진 미정", "수치는 예시입니다").replace("제출 전 확인하기", "날짜는 예시입니다"))
        self.assertEqual(self.lv(twice, "되풀이"), ["WARN"])
        self.assertEqual({l for l, _ in ph.html_checks(BAD, template_blanks=True) if l == "FAIL"}, {"FAIL"})  # the stamp still fails in a 양식

    def test_vendored_code_comments_and_data_uris_are_not_read(self):
        page = GOOD.replace("</body>", "<script>/* TS:VENDOR x 1.0 */ var a='TODO 확인 필요 [학교명]';</script><!-- 교사 초안 --><img src=\"data:image/png;base64,AAAA\"></body>")
        self.assertEqual({l for l, _ in ph.html_checks(page)}, {"PASS"})

    def test_every_html_checker_runs_it(self):
        for f in (SK / "teacher-game" / "scripts" / "check_game.py", SK / "teacher-studio" / "scripts" / "check_webapp.py", SK / "teacher-class-tools" / "scripts" / "check_tool.py",
                  ROOT / "shared" / "stage" / "check_page.py"):
            self.assertIn("placeholders.html_checks(", f.read_text(encoding="utf-8"), f.name)
        for s in ("teacher-game", "teacher-studio", "teacher-class-tools", "teacher-motion", "teacher-docs"):
            self.assertTrue((SK / s / "shared" / "tools" / "placeholders.py").exists(), s)
        self.assertTrue((SK / "teacher-slides" / "scripts" / "placeholders.py").read_bytes() == (ROOT / "shared" / "tools" / "placeholders.py").read_bytes())

    def test_webapp_checker_fails_a_page_with_slots(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "a.html"
            f.write_text(BAD.replace("<head>", '<head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SK / "teacher-studio" / "scripts" / "check_webapp.py"), str(f), "--no-browser"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 1, r.stdout[-800:])
        self.assertRegex(r.stdout, r"FAIL.*빈자리")
        self.assertRegex(r.stdout, r"FAIL.*도장")


class Variety(unittest.TestCase):
    """Game question screens: the layout weights follow the measured footprint overlap (docs/research/leftovers-2026-11.md)."""

    def setUp(self):
        sys.path.insert(0, str(SK / "teacher-game" / "scripts"))
        import layout_auto
        self.la = layout_auto
        self.flat = {k: 2 for k in layout_auto.LAYOUTS}

    def test_low_overlap_layouts_are_preferred_and_none_is_removed(self):
        la = self.la
        w = la.layout_weights(self.flat, {"ox": 0, "longest": 5, "qlen": 25, "choices": 4, "media": False, "phone": False})
        self.assertEqual(set(w), set(la.LAYOUTS))                                  # what the content allows stays possible
        self.assertTrue(all(v >= 1 for v in w.values()), w)
        for low, high in (("stack", "split"), ("left", "bento"), ("right", "poster"), ("stair", "column")):
            self.assertGreater(w[low], w[high], (low, high, w))

    def test_wide_only_content_prefers_the_stack(self):
        w = self.la.layout_weights(self.flat, {"ox": 0, "longest": 11, "qlen": 28, "choices": 4, "media": False, "phone": False}, "escape")
        self.assertEqual(set(w), {"stack", "split", "bento"})
        self.assertGreater(w["stack"], w["split"] + w["bento"])

    def test_long_answers_keep_the_content_rules(self):
        w = self.la.layout_weights(self.flat, {"ox": 0, "longest": 16, "qlen": 33, "choices": 4, "media": False, "phone": False})
        self.assertEqual(set(w), {"stack", "split", "column", "left", "right"})   # the readability rules are untouched: no row / rail / stair for long answers
        self.assertGreater(w["stack"], w["column"])

    def test_recorded_measurements_are_under_the_target(self):
        d = ROOT / "docs" / "research" / "leftovers-2026-11"
        for name in ("sameness-seeds-1-3.json", "sameness-seeds-4-6.json", "sameness-holdout-after.json"):
            if not (d / name).exists():
                self.skipTest("measurement files not written yet")
            m = json.loads((d / name).read_text(encoding="utf-8"))
            self.assertLessEqual(m["different_requests"], 0.5, name)
            self.assertLessEqual(m["same_request"], 0.8, name)


class PythonByName(unittest.TestCase):
    ABS = re.compile(r"[A-Za-z]:[\\/](?:Users|Program Files|Python)[^\s`]*python[^\s`]*\.exe|/usr/(?:local/)?bin/python|AppData[\\/]Local[\\/]Programs[\\/]Python", re.I)

    def test_skills_never_show_an_interpreter_path(self):
        files = list(SK.glob("*/SKILL.md")) + list(SK.glob("*/references/*.md")) + [ROOT / "INSTALL.md", ROOT / "CLAUDE.md", ROOT / "AGENTS.md"]
        for f in files:
            self.assertIsNone(self.ABS.search(f.read_text(encoding="utf-8")), f)

    def test_every_skill_says_py_by_name(self):
        for f in SK.glob("*/SKILL.md"):
            t = f.read_text(encoding="utf-8")
            self.assertRegex(t, r"`py`", f.parent.name)
            self.assertRegex(t, r"[Nn]ever (?:type )?an interpreter's full path", f.parent.name)
        self.assertNotIn("python_path", (SK / "teacher-studio" / "SKILL.md").read_text(encoding="utf-8"))

    def test_eval_allow_list_takes_interpreter_paths(self):
        d = ROOT / "docs" / "research" / "blanks-policy-2026-11"
        src = (d / "bp_eval.py").read_text(encoding="utf-8")
        self.assertIn("def interpreter_rules()", src)
        self.assertIn('kw.setdefault("allow", ALLOW_MAKER)', src)
        ns: dict = {}
        body = src[src.index("def interpreter_rules()"):src.index("ALLOW_MAKER = list(")]
        exec("import shutil, sys\nfrom pathlib import Path\n" + body, ns)  # the function alone: importing the module needs the eval scratch folder
        rules = ns["interpreter_rules"]()
        exe = str(Path(sys.executable)).replace("\\", "/")
        self.assertIn(f'Bash("{exe}":*)', rules)
        self.assertIn(f"Bash({exe}:*)", rules)
        self.assertFalse([r for r in rules if "pip" in r or "*" in r.replace(":*)", "")])  # paths of the same programs only, no wildcard


if __name__ == "__main__":
    unittest.main(verbosity=1)
