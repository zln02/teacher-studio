#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Young-room lesson PPT (docs/research/young-ppt-fix-2026-11.md): drawings that look like the real thing (diagram `icon`),
larger drawing words for children, several check questions on one slide, a lesson frame that never outnumbers the content,
and soft notes for bare shapes and labels said twice."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
for p in (ROOT / "shared" / "design", ROOT / "shared" / "tools", SK / "teacher-slides" / "scripts"):
    sys.path.insert(0, str(p))
import deck_context as dctx  # noqa: E402
import deck_diagram as dg  # noqa: E402
import deck_spec as dspec  # noqa: E402

SIGNS = [  # three road signs drawn with their real outline and the mark inside
    {"kind": "poly", "points": [[17, 4], [30, 27], [4, 27]], "fill": "#FBC02D", "color": "#D32F2F"},
    {"kind": "icon", "name": "baby", "x": 17, "y": 19, "size": 10, "color": "black"},
    {"kind": "circle", "cx": 50, "cy": 16, "r": 12, "fill": "white", "color": "#D32F2F"},
    {"kind": "icon", "name": "person-standing", "x": 50, "y": 16, "size": 14},
    {"kind": "rect", "x": 72, "y": 4, "w": 24, "h": 24, "fill": "#1E88E5"},
    {"kind": "icon", "name": "자전거", "x": 84, "y": 16, "size": "l", "color": "white"},
    {"kind": "label", "x": 17, "y": 38, "text": "어린이 보호"}, {"kind": "label", "x": 50, "y": 38, "text": "보행 금지"},
    {"kind": "label", "x": 84, "y": 38, "text": "자전거 전용"}]
BARE = [{"kind": "poly", "points": [[10, 26], [22, 26], [16, 10]], "fill": "#FBC02D"}, {"kind": "circle", "cx": 50, "cy": 18, "r": 9, "fill": "#E53935"},
        {"kind": "rect", "x": 74, "y": 9, "w": 18, "h": 18, "fill": "#1E88E5"},
        {"kind": "label", "x": 16, "y": 36, "text": "노란 삼각형"}, {"kind": "label", "x": 50, "y": 36, "text": "빨간 동그라미"}, {"kind": "label", "x": 83, "y": 36, "text": "파란 네모"}]
LIGHT = [{"kind": "rect", "x": 38, "y": 4, "w": 24, "h": 52, "fill": "#333333"}, {"kind": "circle", "cx": 50, "cy": 15, "r": 7, "fill": "#E53935"},
         {"kind": "circle", "cx": 50, "cy": 30, "r": 7, "fill": "#FBC02D"}, {"kind": "circle", "cx": 50, "cy": 45, "r": 7, "fill": "#43A047"},
         {"kind": "label", "x": 75, "y": 15, "text": "멈춰요"}]
QUIZ3 = {"type": "quiz", "title": "확인 문제", "questions": [
    {"q": "빨간불일 때 나는?", "choices": ["🏃 뛰어 건너요", "🛑 멈춰서 기다려요"], "answer": 1, "explain": "빨간불은 멈춤이에요."},
    {"q": "초록불이 깜빡이면?", "choices": ["🚶 새로 건너요", "✋ 다음 초록불을 기다려요"], "answer": 1, "explain": "곧 빨간불이 돼요."},
    {"q": "이 표지판은 무슨 뜻일까요?", "choices": ["🚲 자전거 길", "🚗 자동차 길", "🐶 강아지 길"], "answer": 0, "explain": "자전거 전용 표지예요."}]}


def deck(slides, target=8, audience="초등학교 2학년"):
    return {"context": "class", "audience": audience, "subject": "안전한 생활", "title": "신호등과 표지판", "target_slides": target, "slides": slides}


SHORT = [  # what the Claude studio run made: cover, goals, three idea slides, two one-question quizzes (+ the answers page) = 8
    {"type": "title", "title": "신호등과 표지판", "subtitle": "초등학교 2학년 안전한 생활"},
    {"type": "objectives", "items": ["신호등 색깔의 뜻을 말해요", "표지판을 보고 뜻을 알아요"]},
    {"type": "diagram", "title": "신호등 색깔은 무슨 뜻일까요?", "shapes": LIGHT},
    {"type": "steps", "title": "횡단보도는 이렇게 건너요", "steps": [{"title": "멈춰요", "text": "보도에 서요"}, {"title": "살펴요", "text": "양쪽을 봐요"}, {"title": "건너요", "text": "손 들고 걸어요"}]},
    {"type": "diagram", "title": "길에서 만나는 표지판", "shapes": BARE},
    {"type": "quiz", "q": "빨간불이면?", "choices": ["멈춰요", "뛰어요"], "answer": 0, "explain": "멈춰요."},
    {"type": "quiz", "q": "초록불이면?", "choices": ["살피고 건너요", "눈 감고 뛰어요"], "answer": 0, "explain": "먼저 살펴요."}]


class DiagramIcon(unittest.TestCase):
    def test_icon_by_lucide_name_or_korean_word(self):
        self.assertEqual(dg.icon_name({"name": "bike"}), "bike")
        self.assertEqual(dg.icon_name({"name": "자전거"}), "bike")
        self.assertIsNone(dg.icon_name({"name": "no-such-picture-xyz"}))
        self.assertEqual(dg.icon_size({"size": "l"}), 18.0)
        self.assertEqual(dg.icon_size({"size": 99}), 40.0)

    def test_check_accepts_icons_and_names_an_unknown_one(self):
        self.assertEqual(dg.check(3, {"shapes": SIGNS}), [])
        errs = dg.check(3, {"shapes": SIGNS + [{"kind": "icon", "name": "zzz-none", "x": 5, "y": 5}]})
        self.assertTrue(any("not in the icon set" in e and "person-standing" in e for e in errs), errs)
        self.assertTrue(any("missing" in e for e in dg.check(3, {"shapes": SIGNS + [{"kind": "icon", "name": "car"}]})))

    def test_web_svg_draws_the_pictogram_inline(self):
        html = dg.svg({"shapes": SIGNS}, {"card": "#ffffff", "ct": "#111111", "pr": "#c0392b", "ac": "#2e86de", "line": "#cccccc", "bg2": "#eeeeee"}, 600, 360)
        self.assertEqual(html.count('stroke-linecap="round" stroke-linejoin="round"><path'), 3)
        self.assertNotIn("<use", html)  # no sprite reference: the drawing stands alone

    def test_white_icon_on_a_light_card_is_made_legible(self):
        sh = [{"kind": "icon", "name": "bike", "x": 50, "y": 30, "color": "white"}, {"kind": "label", "x": 50, "y": 50, "text": "자전거"}]
        col = dg.legible("#ffffff", sh, 0, {"card": "#ffffff", "pr": "#c0392b", "ac": "#2e86de", "ct": "#111111", "tx": "#111111"})
        self.assertNotEqual(col.lower(), "#ffffff")


class Pptx(unittest.TestCase):
    def build(self, spec, seed=5):
        import deck_pptx
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "d.pptx"
            rep = deck_pptx.build_pptx(json.loads(json.dumps(spec)), Path(td), out, seed)
            self.assertTrue(rep.get("ok"), rep)
            prs = Presentation(str(out))
            return prs, rep

    def test_icons_are_editable_outlines_in_the_pptx(self):
        prs, _ = self.build(deck([{"type": "title", "title": "표지판", "subtitle": "2학년"},
                                  {"type": "diagram", "title": "표지판은 모양과 그림으로 알아요", "shapes": SIGNS}], target=0))
        icons = [sh for sh in prs.slides[1].shapes if sh.name == "diagram icon"]
        self.assertEqual(len(icons), 3)
        self.assertTrue(all(sh._element.spPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}custGeom") is not None for sh in icons))

    def _label_pt(self, audience):
        prs, _ = self.build({"context": "class", "audience": audience, "title": "빛", "slides": [
            {"type": "title", "title": "빛의 반사", "subtitle": "과학"}, {"type": "diagram", "title": "빛은 거울에서 꺾여요", "shapes": BARE}]})
        sizes = [r.font.size.pt for sh in prs.slides[1].shapes if sh.name == "diagram label" for p in sh.text_frame.paragraphs for r in p.runs if r.font.size]
        return min(sizes)

    def test_young_room_reads_a_drawing_from_the_back(self):
        young, adult = self._label_pt("초등학교 2학년"), self._label_pt("교직원")
        self.assertGreaterEqual(young, 19.0)
        self.assertGreater(young, adult)

    def test_three_questions_on_one_slide_and_all_in_the_answers(self):
        prs, rep = self.build(deck([{"type": "title", "title": "신호등과 표지판", "subtitle": "2학년"}, QUIZ3,
                                    {"type": "closing", "title": "안전하게 건너요", "sub": "멈추고 살피고 걸어요"}], target=4))
        self.assertEqual(len(prs.slides), 4)  # cover, questions, answers, closing
        qtext = " ".join(sh.text_frame.text for sh in prs.slides[1].shapes if sh.has_text_frame)
        for q in QUIZ3["questions"]:
            self.assertIn(q["q"], qtext)
        atext = " ".join(sh.text_frame.text for sh in prs.slides[2].shapes if sh.has_text_frame)
        self.assertIn("확인 문제 정답", atext)
        for want in ("멈춰서 기다려요", "다음 초록불을 기다려요", "자전거 길"):
            self.assertIn(want, atext)
        notes = prs.slides[1].notes_slide.notes_text_frame.text
        self.assertIn("3. 정답: A", notes)
        texts = [sh.text_frame.text.strip() for sh in prs.slides[1].shapes if sh.has_text_frame]
        self.assertIn("멈춰서 기다려요", texts)  # a young room's emoji is its own picture beside the word, not left inside it
        self.assertIn("🛑", texts)


class SmallText(unittest.TestCase):
    def test_small_words_in_a_young_room_are_flagged(self):
        import deck_pptx
        from pptx import Presentation
        from pptx.util import Inches, Pt
        with tempfile.TemporaryDirectory() as td:
            prs = Presentation()
            for size in (16, 28):
                sl = prs.slides.add_slide(prs.slide_layouts[6])
                tb = sl.shapes.add_textbox(Inches(1), Inches(2), Inches(6), Inches(2))
                r = tb.text_frame.paragraphs[0].add_run()
                r.text, r.font.size = "빨간불은 멈추라는 약속이에요 차가 지나가요", Pt(size)
                k = sl.shapes.add_textbox(Inches(1), Inches(0.3), Inches(4), Inches(0.3)).text_frame.paragraphs[0].add_run()
                k.text, k.font.size = "학습 목표 안내 띠 글씨", Pt(14)  # the kicker strip at the top is not counted
            f = Path(td) / "y.pptx"
            prs.save(str(f))
            self.assertEqual([n for n, _ in deck_pptx.small_text(f)], [1])


class QuizSpec(unittest.TestCase):
    def test_questions_validate_and_fill_the_first(self):
        it = json.loads(json.dumps(QUIZ3))
        self.assertEqual(dspec.check_slide(4, it, []), [])
        self.assertEqual(it["q"], QUIZ3["questions"][0]["q"])
        self.assertEqual(len(dspec.quiz_set(it)), 3)
        self.assertEqual(len(dspec.quiz_set({"type": "quiz", "q": "?", "choices": ["a", "b"]})), 1)

    def test_one_or_four_questions_are_refused(self):
        for qs in (QUIZ3["questions"][:1], QUIZ3["questions"] + QUIZ3["questions"][:1]):
            self.assertTrue(dspec.check_slide(4, {"type": "quiz", "questions": qs}, []))
        bad = json.loads(json.dumps(QUIZ3))
        bad["questions"][0]["answer"] = 5
        self.assertTrue(any("answer" in e for e in dspec.check_slide(4, bad, [])))

    def test_young_room_lifts_the_pictures_of_every_question(self):
        s, _w, e = dspec.normalize(deck([{"type": "title", "title": "신호등"}, QUIZ3]))
        self.assertEqual(e, [])
        q2 = s["slides"][1]["questions"][1]
        self.assertEqual(q2["pics"], ["🚶", "✋"])
        self.assertEqual(q2["choices"][0], "새로 건너요")

    def test_web_deck_picks_the_set_layout(self):
        import deck_layouts as lay
        it = dict(QUIZ3, q="x", choices=["a", "b"])
        ok = [o[0] for o in lay.REG["quiz"] if o[3](it)]
        self.assertEqual(ok, ["set"])
        self.assertNotIn("set", [o[0] for o in lay.REG["quiz"] if o[3]({"q": "x", "choices": ["a", "b"]})])


class Lint(unittest.TestCase):
    def notes(self, spec):
        return " | ".join(dctx.lint(dctx.pre(json.loads(json.dumps(spec))))[1])

    def test_frame_outnumbering_the_content_is_noted(self):
        self.assertIn("내용 장이 3장뿐이에요", self.notes(deck(SHORT)))

    def test_a_short_deck_folds_the_frame(self):
        folded = [SHORT[0], SHORT[2], SHORT[3], SHORT[4], {"type": "compare", "title": "자동차 신호와 보행자 신호", "a": {"label": "자동차", "items": ["세 가지 색"]},
                                                          "b": {"label": "보행자", "items": ["두 가지 색"]}},
                  QUIZ3, {"type": "closing", "title": "안전하게 건너요", "sub": "멈추고 살피고 걸어요"}]
        n = self.notes(deck(folded))
        self.assertNotIn("내용 장이", n)
        self.assertNotIn("학습 목표 장이 없어요", n)  # the goal is on the cover of a short deck
        self.assertNotIn("정리 장이 없어요", n)      # the recap is the closing's line
        self.assertNotIn("확인 문제가", n)           # three questions on one slide count as three
        long_ = self.notes(deck(folded, target=12))
        self.assertIn("학습 목표 장이 없어요", long_)  # a full-length deck still has its own goals page

    def test_bare_shapes_are_noted_and_real_drawings_are_not(self):
        self.assertTrue(dctx.drawing_notes(5, BARE))
        self.assertEqual(dctx.drawing_notes(5, SIGNS), [])
        self.assertEqual(dctx.drawing_notes(3, LIGHT), [])  # a traffic light: lamps inside their housing
        flow = BARE + [{"kind": "arrow", "x1": 22, "y1": 18, "x2": 40, "y2": 18}]
        self.assertEqual(dctx.drawing_notes(5, flow), [])   # boxes joined by arrows are a flow chart

    def test_labels_said_again_beside_the_drawing_are_noted(self):
        sh = [{"kind": "label", "x": 20, "y": 50, "text": "어린이 보호"}, {"kind": "label", "x": 50, "y": 50, "text": "횡단보도"},
              {"kind": "label", "x": 80, "y": 50, "text": "자전거"}, {"kind": "rect", "x": 5, "y": 5, "w": 20, "h": 20, "fill": "#ffcc00"}]
        cards = [{"title": "어린이 보호", "items": ["어린이가 있으니 조심"]}, {"title": "횡단보도", "items": ["사람이 건너는 길"]}]
        self.assertTrue(any("다시 말해요" in m for m in dctx.drawing_notes(4, sh, cards)))
        other = [{"title": "왜 노란색일까요?", "items": ["멀리서도 잘 보여요"]}, {"title": "헷갈리는 짝", "items": ["자동차 신호와 보행자 신호"]}]
        self.assertFalse(any("다시 말해요" in m for m in dctx.drawing_notes(4, sh, other)))

    def test_panel_drawing_notes_come_out_of_the_lint(self):
        pn = {"type": "panel", "title": "표지판", "blocks": [{"kind": "diagram", "shapes": BARE},
                                                          {"kind": "cards", "numbered": False, "items": [{"title": "노란 삼각형", "items": ["조심해요"]},
                                                                                                          {"title": "빨간 동그라미", "items": ["하면 안 돼요"]}]}]}
        n = self.notes(deck([SHORT[0], pn]))
        self.assertIn("맨 도형", n)
        self.assertIn("다시 말해요", n)


class WebCompare(unittest.TestCase):
    def test_named_pill_passes_the_page_contrast(self):
        import deck_layouts as lay
        import meaning

        class C:
            dz = {"colors": {"pr": "#c2410c", "ac": "#4f46e5", "bg1": "#fffaf3"}}
        named = lay._named_sides(C(), {"label": "안전해요"}, {"label": "위험해요"})
        for fill, ink, _t in named:
            self.assertGreaterEqual(meaning.contrast(ink, fill), 4.5)
        self.assertLess(meaning._hue(named[1][0]) % 360, 30)  # still red


class Docs(unittest.TestCase):
    def test_the_skill_names_the_criteria(self):
        sk = (SK / "teacher-slides" / "SKILL.md").read_text(encoding="utf-8")
        for want in ("recognisable as that thing", "`icon`", "`questions`", "keeps the frame small", "short is the sentence, not the lesson", "aim for 24pt", "저학년 글씨"):
            self.assertIn(want, sk)
        self.assertNotIn("3 items or fewer per slide", sk)
        rules = (ROOT / "shared" / "content" / "CONTENT-RULES.md").read_text(encoding="utf-8")
        self.assertIn("A drawing of a real thing is recognisable as that thing", rules)
        self.assertIn("The frame shrinks before the content", rules)


if __name__ == "__main__":
    unittest.main()
