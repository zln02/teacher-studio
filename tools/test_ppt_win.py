# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""What a bare model did better on PPT, folded into the harness (docs/research/ppt-win-2026-11.md):
the `panel` slide (one claim + 2-4 blocks of evidence), the `takeaway` band, the deck-variety notes,
the small-text / text-only checks on any .pptx, and the cover ornament that must stay behind the title.
No browser, no network.   Run: py tools/test_ppt_win.py"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "skills" / "teacher-slides"
sys.path[:0] = [str(SLIDES / "scripts"), str(ROOT / "shared" / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")

try:
    import pptx  # noqa: F401
    HAVE_PPTX = True
except ImportError:
    HAVE_PPTX = False

import deck_panel as dp  # noqa: E402
import deck_shape  # noqa: E402
import deck_spec  # noqa: E402

DIAGRAM = {"kind": "diagram", "shapes": [{"kind": "line", "x1": 10, "y1": 50, "x2": 90, "y2": 50}, {"kind": "arrow", "x1": 20, "y1": 10, "x2": 50, "y2": 50},
                                         {"kind": "label", "x": 70, "y": 20, "text": "들어오는 빛"}]}
ALL_BLOCKS = [
    {"type": "panel", "title": "숫자와 그 근거를 한 장에", "takeaway": "참여 학급이 1년 사이 두 배가 됨", "source": "우리 학교 자체 집계(2026. 11.)",
     "blocks": [{"kind": "kpis", "items": [{"value": "24", "unit": "학급", "caption": "참여 학급"}, {"value": "83.3", "unit": "%", "caption": "참여율 (24/30)"}, {"value": "2", "unit": "배", "caption": "전년 대비"}]},
                {"kind": "chart", "chart": "line", "labels": ["3월", "6월", "9월"], "series": [{"name": "학급", "data": [12, 18, 24]}], "unit": "학급"},
                {"kind": "list", "title": "읽는 법", "items": ["2학기에 증가 폭이 큼", "저학년 참여가 늦음"]}]},
    {"type": "panel", "title": "누가 무엇을 하는가", "blocks": [{"kind": "tree", "root": "운영 위원회", "children": [{"title": "기획", "items": ["일정", "예산"]}, {"title": "운영", "items": ["수업", "기록"]}, "평가"]},
                                                        {"kind": "note", "label": "원칙", "text": "결정은 위원회가, 실행은 각 팀이 맡음"}]},
    {"type": "panel", "title": "표와 다음 할 일", "source": "우리 학교 자체 집계(2026. 11.)",
     "blocks": [{"kind": "table", "columns": ["학년", "학급", "참여"], "rows": [["1학년", "10", "6"], ["2학년", "10", "8"], ["3학년", "10", "10"]], "highlight": 2},
                {"kind": "flow", "items": [{"title": "원인 찾기", "text": "저학년 시간표"}, {"title": "조정"}, {"title": "다시 재기", "text": "12월"}]}]},
    {"type": "panel", "title": "그림과 규칙", "blocks": [DIAGRAM, {"kind": "cards", "items": [{"title": "들어오는 각", "text": "수직선과 이루는 각"}, {"title": "나가는 각", "items": ["크기가 같다", "반대쪽으로"]}]}]},
]


def spec(slides, **kw):
    return {"title": "점검용", "slides": [{"type": "title", "title": "점검용"}] + slides + [{"type": "closing", "title": "끝"}], **kw}


class PanelSpec(unittest.TestCase):
    def test_every_block_kind_is_accepted(self):
        s, warns, errs = deck_spec.normalize(spec(ALL_BLOCKS))
        self.assertEqual(errs, [])
        kinds = {b["kind"] for it in s["slides"] if it["type"] == "panel" for b in it["blocks"]}
        self.assertEqual(kinds, set(dp.KINDS))

    def test_bad_panels_are_fix_lines(self):
        for bad, word in (({"blocks": [{"kind": "blob"}, {"kind": "note", "text": "x"}]}, "kind"),
                          ({"blocks": [{"kind": "note", "text": "하나뿐"}]}, "plain slide"),
                          ({"blocks": [{"kind": "kpis", "items": [{"value": "1"}]}, {"kind": "note", "text": "x"}]}, "kpis"),
                          ({"blocks": [{"kind": "chart", "labels": ["a"], "series": [{"data": [1, 2]}]}, {"kind": "note", "text": "x"}]}, "chart"),
                          ({"blocks": [DIAGRAM, dict(DIAGRAM), {"kind": "chart", "labels": ["a"], "series": [{"data": [1]}]}]}, "at most two"),
                          ({"blocks": [{"kind": "list", "items": ["가" * 56] * 6}, {"kind": "list", "items": ["나" * 56] * 6}]}, "chars of text")):
            _, _, errs = deck_spec.normalize(spec([{"type": "panel", "title": "t", **bad}]))
            self.assertTrue(any(word in e for e in errs), (word, errs))

    def test_aliases(self):
        s, _, errs = deck_spec.normalize(spec([{"type": "dashboard", "title": "t", "blocks": [{"kind": "stats", "items": [{"value": "1", "caption": "a"}, {"value": "2", "caption": "b"}]}, {"kind": "callout", "text": "x"}]}]))
        self.assertEqual(errs, [])
        self.assertEqual([b["kind"] for b in s["slides"][1]["blocks"]], ["kpis", "note"])

    def test_public_panel_with_numbers_needs_a_source(self):
        import deck_context as dctx
        sp = spec([{**ALL_BLOCKS[0], "source": ""}], context="public", org="우리 학교", date="2026. 11. 20.")
        s, _, errs = deck_spec.normalize(dctx.pre(sp))
        self.assertEqual(errs, [])
        errs, _ = dctx.lint(dctx.post(s))
        self.assertTrue(any("panel" in e and "source" in e for e in errs), errs)


class Regions(unittest.TestCase):
    def _r(self, kinds, layout=None):
        mk = {"kpis": {"items": [{}] * 3}, "cards": {"items": [{"title": "a"}] * 3}, "list": {"items": ["a"] * 3}, "table": {"rows": [[1]] * 3}, "note": {"text": "x"},
              "flow": {"items": [{"title": "a"}] * 3}}
        return dp.regions([{"kind": k, **mk.get(k, {})} for k in kinds], layout, 0.8, 1.6, 11.7, 5.0)

    def test_inside_the_body_and_no_overlap(self):
        for kinds in (["kpis", "chart"], ["chart", "list"], ["kpis", "chart", "list"], ["table", "flow"], ["tree", "note"], ["diagram", "cards", "note"],
                      ["chart", "list", "cards"], ["cards", "cards", "list", "chart"], ["kpis", "flow", "note"], ["chart", "table", "list", "note"]):
            for lay in (None, "rows", "cols", "side"):
                rs = self._r(kinds, lay)
                self.assertEqual(len(rs), len(kinds))
                for _, x, y, w, h in rs:
                    self.assertGreaterEqual(x, 0.8 - 1e-6)
                    self.assertGreaterEqual(y, 1.6 - 1e-6)
                    self.assertLessEqual(x + w, 12.5 + 1e-6, (kinds, lay))
                    self.assertLessEqual(y + h, 6.6 + 1e-6, (kinds, lay))
                    self.assertGreater(w, 1.0)
                    self.assertGreater(h, 0.4, (kinds, lay))
                for i in range(len(rs)):
                    for j in range(i + 1, len(rs)):
                        a, b = rs[i], rs[j]
                        apart = a[1] + a[3] <= b[1] + 1e-6 or b[1] + b[3] <= a[1] + 1e-6 or a[2] + a[4] <= b[2] + 1e-6 or b[2] + b[4] <= a[2] + 1e-6
                        self.assertTrue(apart, (kinds, lay))

    def test_wide_kinds_take_a_row_and_others_share_one(self):
        rs = self._r(["kpis", "chart", "list"])
        self.assertAlmostEqual(rs[0][3], 11.7, places=3)
        self.assertAlmostEqual(rs[1][2], rs[2][2], places=3)  # chart and list on the same row
        self.assertGreater(rs[1][3], rs[2][3])                # the chart gets the wider share
        self.assertLess(rs[0][4], rs[1][4])                   # number cards stay a strip; the chart gets the height


@unittest.skipUnless(HAVE_PPTX, "python-pptx not installed")
class PanelPptx(unittest.TestCase):
    def _build(self, sp, td):
        import deck_pptx
        out = Path(td) / "d.pptx"
        rep = deck_pptx.build_pptx(sp, Path(td), out, 7)
        self.assertTrue(rep["ok"], rep.get("errors"))
        return out, rep

    def test_all_blocks_build_and_pass_the_gate(self):
        import pptx_check
        from pptx import Presentation
        for ctx in ("public", "class", ""):
            with tempfile.TemporaryDirectory() as td:
                kw = {"context": ctx, "org": "우리 학교", "date": "2026. 11. 20."} if ctx == "public" else ({"context": ctx} if ctx else {})
                out, rep = self._build(spec(ALL_BLOCKS, **kw), td)
                self.assertEqual(rep["overflow"], [], ctx)
                r = pptx_check.check_pptx(out)
                self.assertEqual([m for lv, m in r["results"] if lv == "FAIL"], [], ctx)
                prs = Presentation(str(out))
                s2 = [s for s in prs.slides if any(sh.name == "takeaway" for sh in s.shapes)][0]
                self.assertTrue(any(getattr(sh, "has_chart", False) and sh.has_chart for sh in s2.shapes))
                band = [sh for sh in s2.shapes if sh.name == "takeaway"][0]
                for sh in s2.shapes:  # nothing of the body runs under the conclusion band
                    if sh.name in ("takeaway", "decor") or sh.top is None or sh.top < 914400 * 1.5 or sh.top >= band.top:
                        continue
                    self.assertLessEqual(sh.top + sh.height, band.top + 9144, (ctx, sh.name))
                self.assertTrue(any(getattr(sh, "has_table", False) and sh.has_table for s in prs.slides for sh in s.shapes))
                self.assertGreaterEqual(sum(1 for s in prs.slides for sh in s.shapes if sh.shape_type == 9 or "Connector" in sh.name), 4)  # tree lines, flow arrows, diagram

    def test_takeaway_band_on_simple_types(self):
        from pptx import Presentation
        sl = [{"type": "bullets", "title": "세 가지", "items": ["첫째 항목", "둘째 항목", "셋째 항목"], "takeaway": "그래서 이것을 한다"},
              {"type": "table", "title": "표", "columns": ["가", "나"], "rows": [["1", "2"], ["3", "4"]], "takeaway": "표가 뜻하는 것"},
              {"type": "chart", "title": "그래프", "labels": ["a", "b"], "series": [{"name": "s", "data": [1, 2]}], "takeaway": "그래프가 뜻하는 것"},
              {"type": "steps", "title": "순서", "steps": [{"title": "하나", "text": "가"}, {"title": "둘", "text": "나"}, {"title": "셋", "text": "다"}], "takeaway": "순서의 결론"}]
        with tempfile.TemporaryDirectory() as td:
            out, _ = self._build(spec(sl), td)
            prs = Presentation(str(out))
            for s in list(prs.slides)[1:5]:
                band = [sh for sh in s.shapes if sh.name == "takeaway"]
                self.assertEqual(len(band), 1)
                for sh in s.shapes:
                    if sh.name in ("takeaway", "decor") or sh.top is None or sh.top < 914400 * 1.5 or sh.top >= band[0].top:
                        continue
                    if sh.left + sh.width <= band[0].left or sh.left >= band[0].left + band[0].width:
                        continue  # beside the band (a title field at the left), not under it
                    self.assertLessEqual(sh.top + sh.height, band[0].top + 9144, sh.name)

    def test_cover_ornament_is_behind_the_title(self):
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as td:
            out, _ = self._build(spec([ALL_BLOCKS[1]], context="public", org="우리 학교", date="2026. 11. 20."), td)
            s = Presentation(str(out)).slides[0]
            names = [sh.name for sh in s.shapes]
            oval = [i for i, sh in enumerate(s.shapes) if sh.name == "decor" and sh.width == sh.height][0]
            title = [i for i, sh in enumerate(s.shapes) if sh.is_placeholder][0]
            self.assertLess(oval, title, names)

    def test_poly_oval_and_cover_drawing(self):
        from pptx import Presentation
        shapes = [{"kind": "poly", "points": [[20, 52], [50, 10], [80, 52]], "fill": "ac", "text": "산"}, {"kind": "circle", "cx": 80, "cy": 12, "rx": 9, "ry": 5, "fill": "sun"},
                  {"kind": "label", "x": 50, "y": 57, "text": "땅"}]
        sl = [{"type": "diagram", "title": "그림", "shapes": shapes},
              {"type": "panel", "title": "두 쪽", "blocks": [{"kind": "cards", "numbered": False, "items": [{"title": "한쪽", "items": ["가나다", "라마바"]}, {"title": "다른 쪽", "text": "사아자"}]}, {"kind": "note", "text": "둘의 차이"}]}]
        with tempfile.TemporaryDirectory() as td:
            sp = spec(sl)
            sp["slides"][0]["shapes"] = shapes[:2]  # a cover drawing needs no label
            out, _ = self._build(sp, td)
            prs = Presentation(str(out))
            cover, dia, pan = prs.slides[0], prs.slides[1], prs.slides[2]
            self.assertTrue(any(sh.shape_type == 5 for sh in cover.shapes), [sh.shape_type for sh in cover.shapes])  # freeform
            self.assertTrue(any(sh.shape_type == 5 for sh in dia.shapes))
            oval = [sh for sh in dia.shapes if sh.name == "diagram" and sh.shape_type == 1 and sh.width != sh.height]
            self.assertTrue(oval)
            title = [sh for sh in cover.shapes if sh.is_placeholder][0]
            pic = [sh for sh in cover.shapes if sh.shape_type == 5][0]
            self.assertLessEqual(title.left + title.width, pic.left)  # the title makes room for the drawing
            heads = [sh for sh in pan.shapes if sh.has_text_frame and sh.text_frame.text in ("한쪽", "다른 쪽")]
            self.assertEqual(len(heads), 2)
            self.assertTrue(all(h.fill.type == 1 for h in heads))  # filled heading bands (the second takes the accent colour when the palette has a distinct one)
        _, _, errs = deck_spec.normalize(spec([{"type": "diagram", "title": "t", "shapes": [{"kind": "poly", "points": [[1, 1], [2, 2]]}, {"kind": "label", "x": 50, "y": 50, "text": "a"}]}]))
        self.assertTrue(any("poly" in e for e in errs), errs)

    def test_one_preview_browser_at_a_time(self):
        import threading
        import time
        import pptx_render
        seen, live = [], [0]

        def work():
            with pptx_render._one_browser():
                live[0] += 1
                seen.append(live[0])
                time.sleep(0.3)
                live[0] -= 1
        ts = [threading.Thread(target=work) for _ in range(3)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(seen, [1, 1, 1])

    def test_a_rebuild_keeps_the_look(self):
        import json
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            sp = Path(td) / "d.json"
            sp.write_text(json.dumps(spec([ALL_BLOCKS[1]], context="class", objectives=["하나를 말할 수 있다", "둘을 말할 수 있다"], recap=["하나", "둘"]), ensure_ascii=False), encoding="utf-8")
            env = dict(os.environ, USERPROFILE=td, HOME=td, PYTHONUTF8="1")  # the seed memory lives under the home folder: keep the test out of the real one
            looks = []
            for extra in ([], [], ["--fresh"]):
                r = subprocess.run([sys.executable, str(SLIDES / "scripts" / "deck.py"), "--spec", str(sp), "--pptx", str(Path(td) / "d.pptx"), "--pptx-only"] + extra,
                                   capture_output=True, text=True, encoding="utf-8", env=env)
                m = __import__("re").search(r"style=(\S+) palette=(\S+) .*seed=(\d+)", r.stdout)
                self.assertTrue(m, r.stdout[-400:] + r.stderr[-400:])
                from pptx import Presentation
                looks.append((m.group(1), m.group(2), m.group(3), str(Presentation(str(Path(td) / "d.pptx")).slides[1].background.fill.fore_color.rgb)))
            self.assertEqual(looks[0], looks[1])          # a fix round: same seed, same style, same colours in the .pptx
            self.assertNotEqual(looks[0][2], looks[2][2])  # --fresh: a new seed

    def test_hero_kicker_is_printed_once(self):
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as td:
            sp = {"title": "모집", "context": "promo", "slides": [{"type": "hero", "headline": "함께 노래해요", "kicker": "신입 단원 모집", "cta": "지금 신청"},
                                                              {"type": "closing", "title": "기다릴게요"}]}
            out, _ = self._build(sp, td)
            texts = [sh.text_frame.text for sh in Presentation(str(out)).slides[0].shapes if sh.has_text_frame]
            self.assertEqual(sum(1 for t in texts if "신입 단원 모집" in t or "신입 단원 모집".upper() in t), 1, texts)

    def test_small_text_and_text_only_checks_work_on_any_pptx(self):
        import pptx_check
        from pptx import Presentation
        from pptx.util import Inches, Pt
        with tempfile.TemporaryDirectory() as td:
            prs = Presentation()
            for i in range(8):
                s = prs.slides.add_slide(prs.slide_layouts[6])
                tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(4))
                r = tb.text_frame.paragraphs[0].add_run()
                r.text = "본문 글자가 들어 있는 장입니다 " * 3
                r.font.size = Pt(8 if i == 3 else (12 if i == 4 else 20))
            p = Path(td) / "x.pptx"
            prs.save(str(p))
            res = pptx_check.check_pptx(p)["results"]
            self.assertTrue(any(lv == "FAIL" and "large enough" in m for lv, m in res), res)
            self.assertTrue(any(lv == "NOTE" and "11-14pt" in m for lv, m in res), res)
            self.assertTrue(any(lv == "NOTE" and "글만" in m for lv, m in res), res)

    def test_web_deck_builds_a_panel(self):
        import deck
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "d.html"
            rep = deck.build_deck(spec(ALL_BLOCKS + [{"type": "bullets", "title": "세 가지", "items": ["첫째", "둘째", "셋째"], "takeaway": "그래서 이것을 한다"}]), Path(td), out, 7)
            self.assertTrue(rep["ok"], rep.get("errors"))
            html = out.read_text(encoding="utf-8")
            self.assertIn('data-layout="panel.kpis-chart-list"', html)
            self.assertIn("canvas data-cfg", html)
            self.assertIn("pnl-tk", html)


class Variety(unittest.TestCase):
    def test_notes(self):
        b = lambda: {"type": "bullets", "title": "t", "items": ["가나다라", "마바사아"]}  # noqa: E731
        other = [{"type": "compare"}, {"type": "steps"}, {"type": "diagram"}, {"type": "quote"}, {"type": "statement"}]
        self.assertTrue(any("세 장" in n for n in deck_shape.variety([b(), b(), b()] + other)))
        self.assertTrue(any("글머리표예요" in n for n in deck_shape.variety([b(), {"type": "steps"}, b(), {"type": "compare"}, b(), {"type": "quote"}])))
        self.assertTrue(any("panel" in n for n in deck_shape.variety([{"type": "bignumbers"}, {"type": "chart"}])))
        self.assertTrue(any("takeaway" in n for n in deck_shape.variety([{"type": "chart"}, {"type": "table"}])))
        self.assertEqual(deck_shape.variety([{"type": "chart", "takeaway": "x"}, {"type": "compare"}, {"type": "steps"}, {"type": "diagram"}, b(), {"type": "panel", "blocks": []}]), [])

    def test_wrong_weekday_stops_the_build(self):
        import deck_context as dctx
        ok = spec([{"type": "bullets", "title": "접수 2026. 12. 1.(화) ~ 12. 23.(수)", "items": ["첫 수업 2027. 1. 12.(화)", "마감 12월 18일(금)"]}])
        self.assertEqual(dctx.weekday_errors(ok), [])
        bad = spec([{"type": "table", "title": "일정", "columns": ["항목", "내용"], "rows": [["마감", "2026. 12. 5.(금)"], ["시작", "12월 9일(수)"]]}])
        e = dctx.weekday_errors(bad)
        self.assertEqual(len(e), 1)
        self.assertIn("(토)", e[0])
        self.assertTrue(any("요일" in x for x in dctx.lint(bad)[0]))
        self.assertEqual(dctx.weekday_errors(spec([{"type": "statement", "text": "3월 2일(월)에 만나요"}])), [])  # no year anywhere: left alone
        self.assertTrue(dctx.weekday_errors(spec([{"type": "statement", "text": "2026. 2. 30.(월)"}])))

    def test_skill_text_names_the_tools(self):
        t = (SLIDES / "SKILL.md").read_text(encoding="utf-8")
        for w in ("`panel`", "takeaway", "kpis", "tree", "flow", "text large enough to project"):
            self.assertIn(w, t)
        self.assertIn("panel", (SLIDES / "references" / "content-slides.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
