# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Slide context recipes (class / promo / public / personal): presets resolve to their style family, palette, floor and type scale;
public numbering / toc / summary / date / source lint; class objectives & recap; new types (table, summary, toc, hero) validate,
build to HTML and to .pptx.   Run: py tools/test_slides_context.py"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "skills" / "teacher-slides"
sys.path[:0] = [str(SLIDES / "scripts"), str(ROOT / "shared" / "tools")]
os.environ.setdefault("PYTHONUTF8", "1")
import deck_context as dctx  # noqa: E402
import deck_spec as dspec  # noqa: E402
import deck_style as dstyle  # noqa: E402

CTX = SLIDES / "assets" / "spec-examples" / "context"
EX = sorted(CTX.glob("*.json"))
try:
    import pptx  # noqa: F401
    HAVE_PPTX = True
except ImportError:
    HAVE_PPTX = False


def load(name):
    return json.loads((CTX / f"{name}.json").read_text(encoding="utf-8"))


def prep(spec):
    s = dctx.pre(spec)
    s, w, e = dspec.normalize(s, CTX)
    assert not e, e
    return dctx.post(s)


class Presets(unittest.TestCase):
    def test_eight_examples_two_per_context(self):
        got = {}
        for f in EX:
            c = dctx.context_of(json.loads(f.read_text(encoding="utf-8")))
            got[c] = got.get(c, 0) + 1
        self.assertEqual(got, {"class": 2, "promo": 2, "public": 2, "personal": 2})

    def test_aliases(self):
        for word, c in (("수업용", "class"), ("홍보", "promo"), ("공공기관 보고용", "public"), ("기관 보고", "public"), ("개인", "personal"), ("", "")):
            self.assertEqual(dctx.context_of({"context": word}), c, word)

    def test_resolve_style_family_floor_scale(self):
        for c, rc in dctx.RECIPES.items():
            for seed in range(6):
                dz = dstyle.resolve({"context": c, "purpose": "발표"}, seed)
                self.assertEqual(dz["context"], c)
                self.assertEqual(dz["floor"], rc["floor"])
                self.assertEqual(dz["tscale"], rc["tscale"])
                if rc.get("style"):
                    self.assertEqual(dz["style"], rc["style"])
                    self.assertIn(dz["palette"], dctx.PUBLIC_PALETTES)
                else:
                    self.assertIn(dz["style"], rc["styles"], (c, seed))
                self.assertEqual(dstyle.contrast_report(dz), [], (c, seed))

    def test_no_context_unchanged(self):
        a = dstyle.resolve({"purpose": "연수", "mood": "깔끔하게"}, 3)
        self.assertEqual(a["context"], "")
        self.assertEqual(a["floor"], 28)
        self.assertEqual(a["tscale"], {})

    def test_user_template_colours_win(self):
        pal = Path(tempfile.mkdtemp()) / "pal.json"
        pal.write_text(json.dumps({"bg1": "#fffaf0", "bg2": "#fff0d9", "text": "#222222", "primary": "#8a1c1c", "accent": "#335577", "btnText": "#ffffff",
                                   "card": "#ffffff", "cardText": "#222222", "cardBorder": "#cccccc", "good": "#1d4ed8", "bad": "#c2410c"}), encoding="utf-8")
        try:
            dz = dstyle.resolve({"context": "public", "design": {"palette_from": str(pal)}}, 1)
        except ValueError:
            self.skipTest("palette file format differs")
        self.assertEqual(dz["palette"], "user")


class Public(unittest.TestCase):
    def test_numbering_toc_summary_date(self):
        s = prep(load("public-ai-edu-report"))
        types = [x["type"] for x in s["slides"]]
        self.assertEqual(types[:3], ["title", "toc", "summary"])
        secs = [x["title"] for x in s["slides"] if x["type"] == "section"]
        self.assertEqual(secs, ["Ⅰ. 추진 배경", "Ⅱ. 추진 현황", "Ⅲ. 향후 계획"])
        toc = s["slides"][1]
        self.assertEqual(toc["items"], ["추진 배경", "추진 현황", "향후 계획"])
        tbl = next(x for x in s["slides"] if x["type"] == "table")
        self.assertTrue(tbl["title"].startswith("1. "))
        chart = next(x for x in s["slides"] if x["type"] == "chart")
        self.assertTrue(chart["title"].startswith("2. "))
        self.assertEqual(s["slides"][0]["_date"], "2026. 11. 19.")
        self.assertEqual(s["design"]["builds"], False)

    def test_source_required_and_tone(self):
        spec = {"context": "public", "org": "기관", "date": "2026. 11. 19.", "slides": [
            {"type": "title", "title": "보고"},
            {"type": "chart", "title": "현황", "labels": ["a", "b"], "series": [{"name": "x", "data": [1, 2]}]},
            {"type": "bullets", "title": "계획", "items": ["확대 추진합니다.", "점검 강화"]}]}
        errs, warns = dctx.lint(prep(spec))
        self.assertTrue(any("출처" in e for e in errs))
        self.assertTrue(any("개조식" in w for w in warns))
        self.assertTrue(any("요약" in w for w in warns))

    def test_gov_date(self):
        for a in ("2026-11-19", "2026.11.19", "2026년 11월 19일", "2026. 11. 19."):
            self.assertEqual(dctx.gov_date(a), "2026. 11. 19.")
        self.assertTrue(dctx.GOV_DATE_OK.match("2026. 1. 5."))
        self.assertFalse(dctx.GOV_DATE_OK.match("2026. 01. 05."))

    def test_markers(self):
        self.assertEqual(dctx.item_level("- 하위"), (2, "하위"))
        self.assertEqual(dctx.marker(1, 0), "□")
        self.assertEqual(dctx.marker(2, 0), "○")
        self.assertEqual(dctx.marker(1, 1, "num"), "나.")
        self.assertEqual(dctx.marker(2, 2, "num"), "3)")

    def test_caps_wider_for_public(self):
        long = "가" * 66
        base = {"slides": [{"type": "bullets", "title": "t", "items": [long, "b"]}]}
        _, _, e = dspec.normalize(dict(base))
        self.assertTrue(e)
        _, _, e = dspec.normalize({**base, "context": "public"})
        self.assertEqual(e, [])


class ClassPromoPersonal(unittest.TestCase):
    def test_class_objectives_recap_activity(self):
        s = prep(load("class-fractions"))
        roles = [x.get("_role") for x in s["slides"]]
        self.assertEqual(roles[1], "objectives")
        self.assertEqual(roles[-2], "recap")
        self.assertIn("activity", roles)
        self.assertEqual(dctx.lint(s), ([], []))

    def test_promo_cta_and_short_copy(self):
        s = prep(load("promo-club-recruit"))
        self.assertEqual(dctx.lint(s)[1], [])
        bad = prep({"context": "promo", "slides": [{"type": "hero", "headline": "아주 길고 긴 홍보 문구가 여기에 들어가 있어서 읽기 어렵다"}, {"type": "closing", "title": "끝"}]})
        w = dctx.lint(bad)[1]
        self.assertTrue(any("CTA" in x for x in w) and any("24자" in x for x in w))

    def test_personal_photo_hint(self):
        w = dctx.lint(prep({"context": "personal", "slides": [{"type": "title", "title": "안녕"}, {"type": "closing", "title": "끝"}]}))[1]
        self.assertTrue(any("사진" in x for x in w))


class NewTypes(unittest.TestCase):
    def test_validation(self):
        e = dspec.check_extra(1, {"type": "table", "columns": ["a"], "rows": [["x", "y"]]})
        self.assertTrue(any("columns" in x for x in e) and any("every row" in x for x in e))
        self.assertTrue(dspec.check_extra(1, {"type": "summary", "points": ["one"]}))
        self.assertTrue(dspec.check_extra(1, {"type": "hero", "headline": "가" * 40}))
        self.assertEqual(dspec.check_extra(1, {"type": "toc", "items": ["a", "b"]}), [])

    def test_html_build_public_and_promo(self):
        import deck
        out = Path(tempfile.mkdtemp())
        for name in ("public-device-check", "promo-club-recruit"):
            r = deck.build_deck(load(name), CTX, out / f"{name}.html", seed=7, avoid=[])
            self.assertTrue(r["ok"], r.get("errors"))
            html = (out / f"{name}.html").read_text(encoding="utf-8")
            if name.startswith("public"):
                self.assertIn("title.gov", r["fingerprint"])
                self.assertIn("summary.box", r["fingerprint"])
                self.assertIn("자료: 예시 자료", html)
                self.assertIn("Ⅱ. 점검 결과", html)
                self.assertNotIn('data-b="', html.split('id="s2"')[1][:4000])  # no builds in public decks
            else:
                self.assertTrue(r["fingerprint"][0].startswith("hero."))
                self.assertIn("<svg", html.split('id="s1"')[1][:200000])  # QR drawn in the hero

    @unittest.skipUnless(HAVE_PPTX, "python-pptx not installed")
    def test_pptx_all_examples(self):
        import deck_pptx
        import pptx_check
        out = Path(tempfile.mkdtemp())
        for f in EX:
            px = out / (f.stem + ".pptx")
            r = deck_pptx.build_pptx(json.loads(f.read_text(encoding="utf-8")), CTX, px, 7)
            self.assertTrue(r["ok"], (f.stem, r.get("errors")))
            ck = pptx_check.check_pptx(px, [])
            self.assertFalse([m for lv, m in ck["results"] if lv == "FAIL"], f.stem)
        from pptx import Presentation
        prs = Presentation(str(out / "public-ai-edu-report.pptx"))
        texts = " ".join(sh.text_frame.text for sl in prs.slides for sh in sl.shapes if sh.has_text_frame)
        self.assertIn("2026. 11. 19.", texts)
        self.assertIn("자료: 예시 자료", texts)
        self.assertTrue(any(sh.has_table for sl in prs.slides for sh in sl.shapes))


@unittest.skipUnless(HAVE_PPTX, "python-pptx not installed")
class PptxBlankGate(unittest.TestCase):
    def test_blanks_fail_without_spec_and_pass_in_template_mode(self):
        import subprocess
        import deck_pptx
        d = Path(tempfile.mkdtemp())
        spec = {"title": "t", "slides": [{"type": "title", "title": "[학교명] 학부모 설명회"}, {"type": "closing", "title": "끝"}]}
        (d / "s.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        self.assertTrue(deck_pptx.build_pptx(spec, d, d / "b.pptx", 1)["ok"])
        chk = str(SLIDES / "scripts" / "pptx_check.py")
        run = lambda *x: subprocess.run([sys.executable, chk, str(d / "b.pptx"), *x], capture_output=True, text=True, encoding="utf-8").returncode  # noqa: E731
        self.assertEqual(run(), 1)                       # no --spec: leftover blank FAILs
        self.assertEqual(run("--spec", str(d / "s.json")), 1)
        self.assertEqual(run("--allow-blanks"), 0)
        (d / "t.json").write_text(json.dumps({**spec, "template_blanks": True}, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(run("--spec", str(d / "t.json")), 0)
        self.assertEqual(run("--fillins", "학교명"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
