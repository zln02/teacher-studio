# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Editable PowerPoint export: build the 4 example decks to .pptx, reopen with python-pptx, check slide count, notes, no empty placeholders,
shapes inside the slide, rough text fit; a template (.pptx) is honoured.   Run: py tools/test_pptx_export.py"""
from __future__ import annotations

import json
import math
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
    HAVE = True
except ImportError:
    HAVE = False
import deck_pptx  # noqa: E402
import deck_spec  # noqa: E402

EX = sorted((SLIDES / "assets" / "spec-examples").glob("*.json"))


def overflow(shape, w_in):
    """Rough estimate: Korean glyph ~ 0.95 em wide, line ~ 1.3 em. Returns True when the text clearly needs more height than the box."""
    tf = shape.text_frame
    need, box_w = 0.0, max(shape.width / 12700 - 12, 10)
    for p in tf.paragraphs:
        size = max([r.font.size.pt for r in p.runs if r.font.size] or [18])
        chars = sum(len(r.text) for r in p.runs)
        per = max(1, box_w / (size * 0.95))
        need += math.ceil(max(chars, 1) / per) * size * 1.3
    return need > shape.height / 12700 * 1.25 + 8


@unittest.skipUnless(HAVE, "python-pptx not installed")
class PptxExport(unittest.TestCase):
    def build(self, f, **kw):
        out = Path(tempfile.mkdtemp()) / (f.stem + ".pptx")
        spec = json.loads(f.read_text(encoding="utf-8"))
        rep = deck_pptx.build_pptx(spec, f.parent, out, seed=5, **kw)
        self.assertTrue(rep["ok"], rep)
        return spec, out

    def test_examples(self):
        from pptx import Presentation
        for f in EX:
            with self.subTest(f.name):
                spec, out = self.build(f)
                prs = Presentation(str(out))
                norm = deck_spec.normalize(dict(spec), f.parent)[0]["slides"]
                n = len(norm) + (1 if any(x["type"] == "quiz" for x in norm) else 0)  # the .pptx adds one 「확인 문제 정답」 slide before the closing
                self.assertEqual(len(prs.slides), n)
                W, H = prs.slide_width, prs.slide_height
                for i, s in enumerate(prs.slides, 1):
                    self.assertIsNotNone(s.shapes.title, f"slide {i} has no title placeholder")
                    for ph in s.placeholders:
                        self.assertTrue(ph.text_frame.text.strip(), f"slide {i}: empty placeholder")
                    for sh in s.shapes:
                        if sh.name in ("decor",):
                            continue
                        self.assertGreaterEqual(sh.left, -10, f"slide {i} {sh.name}")
                        self.assertLessEqual(sh.left + sh.width, W + 10, f"slide {i} {sh.name} right edge")
                        self.assertLessEqual(sh.top + sh.height, H + 10, f"slide {i} {sh.name} bottom edge")
                        if sh.has_text_frame and sh.text_frame.text.strip():
                            self.assertFalse(overflow(sh, 0), f"slide {i}: text may overflow: {sh.text_frame.text[:30]!r}")
                own = [s for s in prs.slides if not (s.shapes.title is not None and s.shapes.title.text_frame.text.startswith("확인 문제 정답"))]
                for it, s in zip(norm, own):
                    if it.get("note"):
                        self.assertTrue(s.has_notes_slide and it["note"][:8] in s.notes_slide.notes_text_frame.text, "speaker note lost")
                    if it["type"] == "quiz":
                        self.assertIn("정답", s.notes_slide.notes_text_frame.text)
                    if it["type"] == "chart":
                        self.assertTrue(any(sh.has_chart for sh in s.shapes), "chart is not a native chart")

    def test_template_first(self):
        from pptx import Presentation
        tpl = Path(tempfile.mkdtemp()) / "mine.pptx"
        p = Presentation()
        p.slide_width, p.slide_height = 9144000, 5143500  # 16:9, 10in wide: different from ours
        p.slides.add_slide(p.slide_layouts[1]).shapes.title.text = "sample to be dropped"
        p.save(str(tpl))
        spec, out = self.build(EX[0], template=tpl)
        prs = Presentation(str(out))
        self.assertEqual(prs.slide_width, 9144000)
        self.assertEqual(len(prs.slide_layouts), 11)
        self.assertNotIn("sample to be dropped", " ".join(sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.has_text_frame))
        for s in prs.slides:
            for ph in s.placeholders:
                self.assertTrue(ph.text_frame.text.strip())


if __name__ == "__main__":
    unittest.main(verbosity=1)
