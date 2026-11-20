#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""PPT young-room round: crayon-bright (never neon) colours for 유치원 ~ 초3, a picture per key word (an emoji lifted out of the text),
a large answer slide, and the report check that names a required part (예산, 성과, 계획 ...) no slide covers.   Run: py tools/test_ppt_young.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "skills" / "teacher-slides"
sys.path.insert(0, str(SLIDES / "scripts"))
sys.path.insert(0, str(ROOT / "shared" / "design"))
import deck_context  # noqa: E402
import deck_pptx  # noqa: E402
import deck_spec  # noqa: E402
import deck_style  # noqa: E402

YOUNG = {"context": "class", "audience": "초등학교 2학년", "subject": "국어", "title": "흉내 내는 말",
         "objectives": ["흉내 내는 말을 알아요", "문장에 넣어 써요"],
         "slides": [{"type": "title", "title": "흉내 내는 말", "subtitle": "소리와 모양을 말로 그려요", "pic": "🐰"},
                    {"type": "bullets", "title": "소리를 흉내 내는 말", "items": ["🐶 멍멍: 강아지가 짖어요", "🐱 야옹: 고양이가 울어요", "🐸 개굴개굴: 개구리가 울어요"]},
                    {"type": "bullets", "title": "모양을 흉내 내는 말", "items": ["🐰 깡충깡충", "⭐ 반짝반짝", "🐢 엉금엉금", "👶 아장아장"]},
                    {"type": "compare", "title": "소리일까, 모양일까?", "a": {"label": "소리", "items": ["🐮 음매", "🔔 딸랑딸랑"]}, "b": {"label": "모양", "items": ["🦋 팔랑팔랑", "⚽ 데굴데굴"]}},
                    {"type": "activity", "title": "짝과 문장 만들기", "minutes": 5, "steps": [{"title": "🎴 말 고르기", "text": "하나 골라요"}, {"title": "💬 말하기", "text": "문장으로 말해요"}, {"title": "👏 칭찬하기", "text": "짝을 칭찬해요"}]},
                    {"type": "quiz", "q": "별이 (    ) 빛나요. 알맞은 말은?", "choices": ["🐶 멍멍", "⭐ 반짝반짝", "⚽ 데굴데굴"], "answer": 1, "explain": "별이 빛나는 모양은 반짝반짝이에요."},
                    {"type": "closing", "title": "참 잘했어요"}]}
REPORT = {"context": "public", "org": "우리 학교", "date": "2026. 11. 21.", "title": "2026학년도 방과후학교 운영 결과",
          "request": "교육지원청 보고용 '2026학년도 방과후학교 운영 결과' 발표자료 만들어 줘",
          "slides": [{"type": "title", "title": "2026학년도 방과후학교 운영 결과"},
                     {"type": "table", "title": "영역별 참여 현황", "columns": ["영역", "강좌", "참여 학생"], "rows": [["체육", "6개", "120명"], ["예술", "5개", "96명"]], "source": "우리 학교, 방과후학교 운영 대장(2026)"},
                     {"type": "bignumbers", "title": "만족도와 성과", "items": [{"value": "92", "unit": "%", "caption": "학생 만족도"}, {"value": "88", "unit": "%", "caption": "학부모 만족도"}], "source": "우리 학교, 만족도 설문(2026)"},
                     {"type": "timeline", "title": "2027학년도 추진 계획", "events": [{"when": "2월", "title": "수요 조사", "text": "학생·학부모 설문"}, {"when": "3월", "title": "강좌 개설", "text": "강사 선정"}, {"when": "7월", "title": "중간 점검", "text": "만족도 조사"}]},
                     {"type": "closing", "title": "감사합니다"}]}
BUDGET = {"type": "table", "title": "예산 편성과 집행", "columns": ["재원", "편성액", "집행액", "집행률"], "rows": [["교육청 지원금", "3,000만 원", "2,850만 원", "95.0%"], ["수익자 부담", "1,200만 원", "1,140만 원", "95.0%"]],
          "source": "우리 학교, 방과후학교 회계 결산(2026)", "footnote": "예시 자료(가상 수치), 실제 집계로 교체"}


def build(spec, seed, **kw):
    out = Path(tempfile.mkdtemp()) / "d.pptx"
    rep = deck_pptx.build_pptx(json.loads(json.dumps(spec)), ROOT, out, seed=seed, **kw)
    assert rep["ok"], rep
    return out, rep


def pictures(prs):
    return [sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.name == "picture"]


class Pictures(unittest.TestCase):
    def test_an_emoji_in_front_of_a_word_is_lifted_out_of_the_text(self):
        self.assertEqual(deck_spec._lift("🐶 멍멍: 강아지 소리"), ("🐶", "멍멍: 강아지 소리"))
        self.assertEqual(deck_spec._lift("깡충깡충 🐰"), ("🐰", "깡충깡충"))
        self.assertEqual(deck_spec._lift("**🐸 개굴개굴**"), ("🐸", "**개굴개굴**"))
        self.assertEqual(deck_spec._lift("그냥 하는 말"), (None, "그냥 하는 말"))
        self.assertEqual(deck_spec._lift("✔ 손 씻기")[0], None)  # a tick is a mark, not a picture
        self.assertTrue(deck_spec.is_pic("☀️") and not deck_spec.is_pic("sun") and not deck_spec.is_pic("🐶🐱"))
        s, _, errs = deck_spec.normalize(deck_context.pre(json.loads(json.dumps(YOUNG))))
        self.assertEqual(errs, [])
        b = s["slides"][2]
        self.assertEqual(b["pics"], ["🐶", "🐱", "🐸"])
        self.assertEqual(b["items"][0], "멍멍: 강아지가 짖어요")
        self.assertEqual(s["slides"][4]["a"]["pics"], ["🐮", "🔔"])
        self.assertEqual(s["slides"][5]["steps"][0]["pic"], "🎴")
        self.assertEqual(s["slides"][6]["pics"][1], "⭐")
        self.assertFalse(any(deck_spec.EMOJI.search(str(x.get("title", ""))) for x in s["slides"]))  # titles stay words

    def test_other_rooms_still_lose_their_emoji(self):
        older = {**YOUNG, "audience": "중학교 1학년"}
        s, _, _ = deck_spec.normalize(deck_context.pre(json.loads(json.dumps(older))))
        self.assertNotIn("pics", s["slides"][2])
        self.assertEqual(s["slides"][2]["items"][0], "멍멍: 강아지가 짖어요")
        from pptx import Presentation
        self.assertEqual(pictures(Presentation(str(build(older, 3)[0]))), [])

    def test_pictures_are_drawn_beside_their_words_in_the_pptx(self):
        import pptx_check
        from pptx import Presentation
        seen = set()
        for sd in range(1, 7):
            out, rep = build(YOUNG, sd)
            prs = Presentation(str(out))
            pics = pictures(prs)
            for ch in ("🐰", "🐶", "🐱", "🐸", "⭐", "🐢", "🐮", "🦋", "🎴"):
                self.assertIn(ch, pics, (sd, ch))
            self.assertFalse(any(sh.shape_type == 13 for s in prs.slides for sh in s.shapes))  # still no picture files: emoji are text
            self.assertIn("bullets.tiles", rep["variants"])
            self.assertEqual(rep["overflow"], [])
            self.assertEqual([m for lv, m in pptx_check.check_pptx(out)["results"] if lv == "FAIL"], [], (sd, rep["variants"]))
            seen.update(rep["variants"])
            texts = " ".join(sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.has_text_frame and sh.name != "picture")
            self.assertNotRegex(texts, deck_spec.EMOJI)  # no emoji left inside a sentence or a title
        self.assertGreaterEqual(len([v for v in seen if v.startswith("bullets.")]), 2, sorted(seen))  # not one template: the list forms still rotate
        self.assertGreaterEqual(len([v for v in seen if v.startswith("cover.")]), 2, sorted(seen))

    def test_web_deck_keeps_the_picture_in_front_of_the_word(self):
        s, _, _ = deck_spec.normalize(deck_context.pre(json.loads(json.dumps(YOUNG))))
        s = deck_spec.pics_inline(s)
        self.assertEqual(s["slides"][2]["items"][0], "🐶 멍멍: 강아지가 짖어요")
        self.assertEqual(s["slides"][6]["choices"][1], "⭐ 반짝반짝")

    def test_a_young_lesson_without_pictures_is_told_so(self):
        bare = json.loads(deck_spec.EMOJI.sub("", json.dumps(YOUNG, ensure_ascii=False)))
        bare["slides"][0].pop("pic")
        s, _, _ = deck_spec.normalize(deck_context.pre(bare))
        warns = deck_context.lint(deck_context.post(s))[1]
        self.assertTrue(any("낱말에 그림" in w for w in warns), warns)
        self.assertTrue(any("표지에 그림" in w for w in warns), warns)
        s, _, _ = deck_spec.normalize(deck_context.pre(json.loads(json.dumps(YOUNG))))
        warns = deck_context.lint(deck_context.post(s))[1]
        self.assertFalse(any("그림" in w for w in warns), warns)


class Look(unittest.TestCase):
    def test_young_colours_are_bright_distinct_and_never_neon(self):
        import oklch
        import system
        hues = set()
        for title in ("흉내 내는 말", "여름 날씨와 우리 생활", "덧셈과 뺄셈", "우리 동네 동물", "안전한 등굣길", "시계 보기", "가족"):
            for sd in range(1, 13):
                dz = deck_style.resolve({"context": "class", "audience": "초등학교 2학년", "title": title}, sd)
                self.assertTrue(dz["crayon"])
                self.assertFalse(dz["dark"])
                self.assertEqual(deck_style.contrast_report(dz), [], (title, sd))
                self.assertEqual(len(dz["tones"]), 3, (title, sd, dz["tones"]))
                self.assertFalse([c for c in dz["tones"] if system.is_neon(c)], (title, sd, dz["tones"]))
                lch = [oklch.hex_to_oklch(c) for c in dz["tones"]]
                self.assertTrue(all(c >= 0.09 for _, c, _ in lch), (title, sd, lch))            # saturated, not pastel (sea green cannot go higher on a screen)
                self.assertGreaterEqual(min(oklch.hue_distance(lch[i][2], lch[j][2]) for i in range(3) for j in range(i)), 60, (title, sd))  # three clear hues
                hues.add(round(lch[0][2] / 30))
        self.assertGreaterEqual(len(hues), 4, hues)  # not one house colour: the main hue moves with the topic and the seed

    def test_older_rooms_and_reports_keep_their_own_colours(self):
        self.assertFalse(deck_style.resolve({"context": "class", "audience": "초등학교 5학년", "title": "화산과 지진"}, 3)["crayon"])
        self.assertFalse(deck_style.resolve({"context": "class", "audience": "고1", "title": "시장 경제"}, 3)["crayon"])
        self.assertFalse(deck_style.resolve({"context": "public", "title": "초등학교 2학년 돌봄 운영 결과", "org": "우리 학교"}, 3)["crayon"])

    def test_the_user_palette_and_template_still_win(self):
        from pptx import Presentation
        pal = Path(tempfile.mkdtemp()) / "pal.json"
        pal.write_text(json.dumps({"bg1": "#ffffff", "bg2": "#f1f1f1", "text": "#111111", "card": "#ffffff", "cardText": "#111111", "cardBorder": "#cccccc",
                                   "primary": "#7a1f5c", "btnText": "#ffffff", "accent": "#1f6f7a", "good": "#1d4ed8", "bad": "#b42318"}), encoding="utf-8")
        dz = deck_style.resolve({**YOUNG, "design": {"palette_from": str(pal)}}, 3)
        self.assertEqual(dz["colors"]["pr"].lower(), "#7a1f5c")
        self.assertFalse(dz["crayon"])
        self.assertTrue(set(c.lower() for c in dz["tones"]) <= {"#7a1f5c", "#1f6f7a"}, dz["tones"])
        tpl = Path(tempfile.mkdtemp()) / "mine.pptx"
        p = Presentation()
        p.save(str(tpl))
        out, rep = build(YOUNG, 3, template=tpl)
        self.assertNotIn("bullets.tiles", rep["variants"])  # the user's template keeps the plain forms
        prs = Presentation(str(out))
        W, H = prs.slide_width, prs.slide_height
        for s in prs.slides:
            self.assertFalse([sh.name for sh in s.shapes if sh.name == "decor" and sh.width * sh.height > W * H * 0.3 and sh.width != sh.height])

    def test_the_answer_slide_is_large(self):
        from pptx import Presentation
        for sd in (1, 4):
            prs = Presentation(str(build(YOUNG, sd)[0]))
            ans = [s for s in prs.slides if any(sh.has_text_frame and "확인 문제 정답" in sh.text_frame.text for sh in s.shapes)][0]
            sizes = {sh.text_frame.text[:8]: r.font.size.pt for sh in ans.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs if r.font.size and r.text.strip()}
            big = [v for k, v in sizes.items() if k.startswith("정답 B")]
            self.assertTrue(big and big[0] >= 32, sizes)
            self.assertGreaterEqual(min(v for k, v in sizes.items() if k[:2] in ("별이",)), 26, sizes)  # the question and its reason


class Required(unittest.TestCase):
    def lint(self, spec):
        s, _, errs = deck_spec.normalize(deck_context.pre(json.loads(json.dumps(spec))))
        self.assertEqual(errs, [])
        return deck_context.lint(deck_context.post(s))[1]

    def test_a_results_report_without_its_budget_is_told_so(self):
        warns = self.lint(REPORT)
        self.assertTrue(any("꼭 담을 내용이 빠졌어요" in w and "「예산」" in w for w in warns), warns)
        self.assertFalse(any("「성과」" in w or "「계획」" in w or "「실적」" in w for w in warns), warns)
        full = {**REPORT, "slides": REPORT["slides"][:2] + [BUDGET] + REPORT["slides"][2:]}
        self.assertFalse(any("꼭 담을 내용" in w for w in self.lint(full)), self.lint(full))
        self.assertFalse(any("꼭 담을 내용" in w for w in self.lint({**REPORT, "omit": ["예산"]})))

    def test_a_part_named_only_in_passing_does_not_count(self):
        sp = json.loads(json.dumps(REPORT))
        sp["slides"].insert(1, {"type": "summary", "title": "요약", "points": ["예산 집행 양호", "만족도 92%"]})
        self.assertTrue(any("「예산」" in w for w in self.lint(sp)))

    def test_what_the_request_names_is_required_in_any_context(self):
        sp = {"context": "personal", "title": "동호회 한 해 돌아보기", "request": "올해 활동 성과와 내년 계획, 회비 예산을 정리한 발표자료",
              "slides": [{"type": "title", "title": "동호회 한 해 돌아보기"}, {"type": "bullets", "title": "올해 한 일", "items": ["정기 모임 12회", "봄 소풍"]},
                         {"type": "closing", "title": "고맙습니다"}]}
        miss = deck_context.missing_parts(deck_spec.normalize(deck_context.pre(sp))[0])
        self.assertEqual(sorted(miss), sorted(["성과", "계획", "예산"]))
        self.assertEqual(deck_context.missing_parts({"context": "class", "title": "화산과 지진", "slides": [{"type": "title", "title": "화산과 지진"}]}), [])
        self.assertIn("안전 교육", deck_context.required_parts({"context": "public", "title": "현황 보고", "must": ["안전 교육"]}))

    def test_a_thin_report_is_told_to_speak_in_figures(self):
        sp = json.loads(json.dumps(REPORT))
        sp["slides"] = sp["slides"][:2] + [{"type": "bullets", "title": f"운영 내용 {i}", "items": ["강좌 운영함", "학생 참여함"]} for i in range(6)] + sp["slides"][-1:]
        self.assertTrue(any("수치가 든 장" in w for w in self.lint(sp)))


if __name__ == "__main__":
    unittest.main(verbosity=1)
