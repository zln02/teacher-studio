#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""PPT design round: icons by meaning (web + pptx), several layouts per slide type, two or three tones, larger minimum sizes,
a younger / older look read from the audience, a filled promo cover; the user's template and colours still win.   Run: py tools/test_ppt_design.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "skills" / "teacher-slides"
sys.path.insert(0, str(SLIDES / "scripts"))
import deck_icons  # noqa: E402
import deck_pptx  # noqa: E402
import deck_style  # noqa: E402

KID = {"context": "class", "audience": "초등학교 2학년", "title": "여름 날씨와 우리 생활", "objectives": ["여름 날씨를 말해요", "비 오는 날 준비물을 골라요"],
       "slides": [{"type": "title", "title": "여름 날씨와 우리 생활", "subtitle": "비가 오면 무엇이 달라질까?"},
                  {"type": "bullets", "title": "여름에는 이런 날씨가 있어요", "items": ["해가 쨍쨍한 날", "비가 많이 오는 날", "바람이 센 날"]},
                  {"type": "steps", "title": "비 오는 날 이렇게 해요", "steps": [{"title": "우산 챙기기", "text": "집을 나서기 전에"}, {"title": "천천히 걷기", "text": "미끄러우니까"}, {"title": "손 씻기", "text": "집에 오면 바로"}]},
                  {"type": "bullets", "title": "준비물을 골라요", "items": ["우산", "장화", "수건", "물통"]},
                  {"type": "compare", "title": "맑은 날과 비 오는 날", "a": {"label": "맑은 날", "items": ["모자를 써요", "물을 마셔요"]}, "b": {"label": "비 오는 날", "items": ["우산을 써요", "장화를 신어요"]}},
                  {"type": "quiz", "q": "비가 올 때 필요한 것은?", "choices": ["우산", "부채", "선글라스"], "answer": 0, "explain": "우산이 비를 막아 줘요"},
                  {"type": "closing", "title": "참 잘했어요"}]}
PROMO = {"context": "promo", "audience": "어르신과 가족", "title": "어르신 스마트폰 교실",
         "slides": [{"type": "hero", "headline": "스마트폰, 천천히 함께 배워요", "kicker": "수강생 모집", "cta": "방문 접수", "facts": ["12월 10일(목) 시작", "주민센터 3층", "수강료 무료"]},
                    {"type": "table", "title": "수강 안내", "columns": ["항목", "내용"], "rows": [["대상", "만 60세 이상 주민"], ["장소", "주민센터 3층"], ["수강료", "무료"]]},
                    {"type": "closing", "title": "함께 시작해요", "next": ["방문 접수", "가족이 대신 신청해도 돼요"]}]}


def build(spec, seed, **kw):
    out = Path(tempfile.mkdtemp()) / "d.pptx"
    rep = deck_pptx.build_pptx(json.loads(json.dumps(spec)), ROOT, out, seed=seed, **kw)
    assert rep["ok"], rep
    return out, rep


def sizes(prs):
    return [r.font.size.pt for s in prs.slides for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs if r.font.size and r.text.strip()]


class Icons(unittest.TestCase):
    def test_every_word_points_at_an_icon_in_the_vendored_set(self):
        self.assertEqual(sorted({v for v in deck_icons.WORDS.values() if not deck_icons.exists(v)}), [])
        self.assertTrue((ROOT / "shared/vendor/lucide/LICENSE").read_text(encoding="utf-8").startswith("ISC License"))
        self.assertIn("deck_icons", json.loads((ROOT / "shared/vendor/manifest.json").read_text(encoding="utf-8"))["libs"]["lucide"]["notes"])

    def test_picked_by_meaning_not_by_substring(self):
        self.assertEqual(deck_icons.pick("손주와 영상통화 하기"), "baby")
        self.assertEqual(deck_icons.pick("화산의 구조"), "mountain")
        self.assertEqual(deck_icons.pick("생산과 소비"), "factory")   # 산 inside 생산 is not a mountain
        self.assertIsNone(deck_icons.pick("이해하기 쉬운 설명"))      # 해 inside 이해 is not the sun
        self.assertEqual(deck_icons.name("지도"), "map")
        self.assertEqual(deck_icons.name("phone"), "phone")
        self.assertIsNone(deck_icons.name("no-such-icon-here"))

    def test_a_list_is_illustrated_whole_or_not_at_all(self):
        self.assertEqual(deck_icons.pick_all(["전화 걸기", "사진 찍기", "길 찾기"]), ["phone", "camera", "map-pin"])
        self.assertEqual(deck_icons.pick_all(["전화 걸기", "그냥 하는 말"]), [])
        self.assertEqual(deck_icons.pick_all(["화산이란", "화산의 피해"]), [])  # the same picture twice says nothing
        self.assertEqual(deck_icons.pick_all(["가", "나"], ["phone", "지도"]), ["phone", "map"])

    def test_every_outline_parses(self):
        for n in ("phone", "map-pin", "mountain", "alarm-check", "calendar-days", "circle-help", "users"):
            ol = deck_icons.outline(n)
            self.assertTrue(ol, n)
            for _, cm in ol:
                self.assertEqual(cm[0][0], "M")
                self.assertTrue(all(-4 <= v <= 28 for c in cm for v in c[1:]), n)

    def test_web_and_pptx_use_the_same_picker(self):
        import deck_art
        self.assertEqual(deck_art.icon_name("지도"), deck_icons.name("지도"))
        from pptx import Presentation
        out, _ = build(PROMO, 2)
        prs = Presentation(str(out))
        icons = [sh for s in prs.slides for sh in s.shapes if sh.name == "icon"]
        self.assertGreaterEqual(len(icons), 3)
        self.assertTrue(all(sh.shape_type == 5 for sh in icons))  # editable freeforms, not pictures
        self.assertFalse(any(sh.shape_type == 13 for s in prs.slides for sh in s.shapes))


class Look(unittest.TestCase):
    def test_audience_band(self):
        f = deck_style.audience_band
        self.assertEqual(f({"context": "class", "audience": "초등학교 2학년"}), "young")
        self.assertEqual(f({"context": "class", "audience": "초4"}), "kid")
        self.assertEqual(f({"context": "class", "audience": "유치원 7세 반"}), "young")
        self.assertEqual(f({"context": "class", "audience": "고1"}), "")
        self.assertEqual(f({"context": "class", "audience": "중학교 3학년"}), "")
        self.assertEqual(f({"context": "promo", "audience": "어르신과 가족"}), "senior")
        self.assertEqual(f({"context": "public", "title": "초등학교 3학년 돌봄 운영 결과"}), "")

    def test_young_and_senior_looks_are_light_larger_and_not_neon(self):
        sys.path.insert(0, str(ROOT / "shared" / "design"))
        import system
        from pptx import Presentation
        for spec, floor in ((KID, 16), (PROMO, 16)):
            for sd in range(1, 9):
                dz = deck_style.resolve(spec, sd)
                self.assertFalse(dz["dark"], (spec["title"], sd, dz["style"]))
                self.assertEqual(deck_style.contrast_report(dz), [])
                self.assertFalse(any(system.is_neon(c) for c in dz["tones"]), dz["tones"])
            out, rep = build(spec, 3)
            self.assertEqual(rep["overflow"], [])
            self.assertGreaterEqual(min(sizes(Presentation(str(out)))), floor - 1)  # 15pt kickers are the only thing under the floor
        older = min(sizes(Presentation(str(build({**KID, "audience": "고등학교 1학년"}, 3)[0]))))
        self.assertGreaterEqual(older, 14)

    def test_topic_colour_and_three_tones(self):
        import oklch
        dz = deck_style.resolve({"context": "class", "audience": "초등학교 4학년", "title": "화산과 지진"}, 3)
        self.assertEqual(dz["palette"], "topic")
        h = oklch.hex_to_oklch(dz["colors"]["pr"])[2]
        self.assertTrue(15 <= h <= 70, h)  # lava is warm
        self.assertEqual(len(dz["tones"]), 3)
        self.assertEqual(deck_style.topic_hues({"title": "생산과 소비의 시"}), deck_style.topic_hues({"title": "소비"}))  # 산 / 시 inside words are not topics
        pub = deck_style.resolve({"context": "public", "title": "화산 대응 훈련 결과", "org": "우리 학교"}, 3)
        self.assertNotEqual(pub["palette"], "topic")  # a report keeps its restrained palette
        self.assertGreaterEqual(len(pub["tones"]), 2)

    def test_layouts_vary_inside_a_deck_and_between_seeds(self):
        seen = set()
        for sd in range(1, 9):
            _, rep = build(KID, sd)
            v = rep["variants"]
            b = [x for x in v if x.startswith("bullets.")]
            self.assertGreaterEqual(len(set(b)), 2, v)               # three lists in one deck are not drawn the same way
            self.assertTrue(all(a != c for a, c in zip(v, v[1:])), v)  # never the same layout twice running
            seen.update(v)
        for kind, n in (("cover", 3), ("bullets", 3), ("steps", 2), ("compare", 2), ("closing", 2)):
            self.assertGreaterEqual(len([x for x in seen if x.startswith(kind + ".")]), n, (kind, sorted(seen)))
        a, b = build(KID, 5)[1]["variants"], build(KID, 5)[1]["variants"]
        self.assertEqual(a, b)  # the same seed gives the same deck

    def test_forced_layout(self):
        sp = json.loads(json.dumps(KID))
        sp["slides"][1]["layout"] = "bullets.grid"
        for sd in (1, 2, 3):
            self.assertIn("bullets.grid", build(sp, sd)[1]["variants"])

    def test_promo_cover_colour_field_is_not_empty(self):
        from pptx import Presentation
        for sd in range(1, 7):
            out, rep = build(PROMO, sd)
            s = Presentation(str(out)).slides[0]
            texts = " ".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame)
            for f in PROMO["slides"][0]["facts"]:
                self.assertIn(f, texts)
            self.assertTrue(any(sh.name == "icon" for sh in s.shapes))
            self.assertIn("table.kv", rep["variants"])  # 항목 | 내용 becomes label tiles
        import deck_spec
        bad = {**PROMO, "slides": [{**PROMO["slides"][0], "facts": ["가", "나", "다", "라"]}]}
        self.assertTrue(any("facts" in e for e in deck_spec.normalize(bad)[2]))

    def test_gate_passes_on_the_new_layouts(self):
        import pptx_check
        for spec in (KID, PROMO):
            for sd in range(1, 7):
                out, rep = build(spec, sd)
                self.assertEqual([m for lv, m in pptx_check.check_pptx(out)["results"] if lv == "FAIL"], [], (spec["title"], sd, rep["variants"]))


class UserWins(unittest.TestCase):
    def test_template_keeps_its_masters_and_gets_no_colour_fields(self):
        from pptx import Presentation
        tpl = Path(tempfile.mkdtemp()) / "mine.pptx"
        p = Presentation()
        p.slide_width, p.slide_height = 9144000, 5143500
        p.save(str(tpl))
        out, rep = build(KID, 3, template=tpl)
        prs = Presentation(str(out))
        self.assertEqual(prs.slide_width, 9144000)
        self.assertEqual(len(prs.slide_layouts), 11)
        self.assertTrue(all(v.split(".")[1] in ("plain", "rows", "track", "cards", "center", "grid", "num", "right") for v in rep["variants"]), rep["variants"])
        W, H = prs.slide_width, prs.slide_height
        for s in prs.slides:  # nothing of ours covers a third of the user's slide
            self.assertFalse([sh.name for sh in s.shapes if sh.name == "decor" and sh.width * sh.height > W * H * 0.3 and sh.width != sh.height])

    def test_user_palette_gets_no_derived_colour(self):
        pal = Path(tempfile.mkdtemp()) / "pal.json"
        pal.write_text(json.dumps({"bg1": "#ffffff", "bg2": "#f1f1f1", "text": "#111111", "card": "#ffffff", "cardText": "#111111", "cardBorder": "#cccccc",
                                   "primary": "#7a1f5c", "btnText": "#ffffff", "accent": "#1f6f7a", "good": "#1d4ed8", "bad": "#b42318"}), encoding="utf-8")
        dz = deck_style.resolve({**KID, "title": "화산과 지진", "design": {"palette_from": str(pal)}}, 3)
        self.assertEqual(dz["palette"], "user")
        self.assertEqual(dz["colors"]["pr"].lower(), "#7a1f5c")
        self.assertTrue(set(c.lower() for c in dz["tones"]) <= {"#7a1f5c", "#1f6f7a"}, dz["tones"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
