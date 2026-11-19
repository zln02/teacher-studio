#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Review gate for an editable .pptx (the counterpart of slides_review.py for the web deck).

    py pptx_check.py deck.pptx [--spec deck.json] [--fillins "학교명,담임 이름"] [--render DIR] [--yes]

Checks (FAIL = fix before handing over):
  placeholders  no `[대괄호]` blanks, `20XX`, `OO`/`○○`, `000`, 「학교명」 ... unless the spec lists them in "fillins" (then they are only
                reported as 「바꿔 넣을 곳」)
  text fit      estimated text height vs. its box (pptx_fit.py, same metrics deck_pptx shrinks with): FAIL when clearly over
  geometry      shapes inside the slide, no empty text placeholders
  notes         placeholders in speaker notes count too
--render DIR    also draws the slides as PNG: real LibreOffice rendering when installed (or --yes to install it, large), else an
                APPROXIMATE preview from the shapes (labelled as such; fonts and line breaks differ from PowerPoint).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import placeholders as ph  # noqa: E402
import pptx_fit as pfit  # noqa: E402

EMU = 914400


def _frames(slide):
    """Yield (shape, text_frame, label) for every text holder on a slide (text boxes, shapes, table cells, groups)."""
    def walk(shapes):
        for sh in shapes:
            if sh.shape_type == 6:  # group
                yield from walk(sh.shapes)
                continue
            if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
                yield sh, sh.text_frame, sh.name
            if getattr(sh, "has_table", False) and sh.has_table:
                for r in sh.table.rows:
                    for c in r.cells:
                        yield sh, c.text_frame, sh.name + " (표)"
    yield from walk(slide.shapes)


def frame_overflow(sh, tf):
    """(need_pt, have_pt, ratio) for one text frame, or None when it is not a measurable box (tables are skipped)."""
    if getattr(sh, "has_table", False) and sh.has_table:
        return None
    ml = (tf.margin_left if tf.margin_left is not None else 91440) / EMU
    mr = (tf.margin_right if tf.margin_right is not None else 91440) / EMU
    mt = (tf.margin_top if tf.margin_top is not None else 45720) / EMU
    mb = (tf.margin_bottom if tf.margin_bottom is not None else 45720) / EMU
    bw = (sh.width / EMU - ml - mr) * 72
    bh = (sh.height / EMU - mt - mb) * 72
    paras = []
    spacing = 1.0
    for p in tf.paragraphs:
        size = max([r.font.size.pt for r in p.runs if r.font.size] or [18])
        if p.line_spacing and isinstance(p.line_spacing, float):
            spacing = p.line_spacing
        paras.append(("".join(r.text for r in p.runs) or " ", size))
    if not any(t.strip() for t, _ in paras):
        return None
    need = pfit.need_height_pt(paras, bw, spacing or 1.0)
    return need, bh, need / max(bh, 1)


def check_pptx(path: Path, fillins=(), tol: float = 1.12) -> dict:
    """Returns {results:[(level,msg)], fillins:[...], texts:[per-slide text], overflow:[(slide, text, ratio)]}."""
    from pptx import Presentation
    prs = Presentation(str(path))
    W, H = prs.slide_width, prs.slide_height
    results: list[tuple[str, str]] = []
    left_over, listed, texts_all, over, off, empty = [], [], [], [], [], []
    for i, s in enumerate(prs.slides, 1):
        texts = []
        for sh, tf, label in _frames(s):
            t = tf.text or ""
            texts.append(t)
            if not t.strip() and sh.is_placeholder:
                empty.append((i, sh.name))
            ov = frame_overflow(sh, tf)
            if ov and ov[2] > tol:
                over.append((i, t.strip().split("\n")[0][:20], round(ov[2], 2)))
        if s.has_notes_slide:
            texts.append(s.notes_slide.notes_text_frame.text or "")
        txt = "\n".join(texts)
        texts_all.append(txt)
        for m in ph.leftovers(txt, fillins):
            left_over.append((i, m))
        for m in ph.fillin_list([txt], fillins):
            if m not in listed:
                listed.append(m)
        for sh in s.shapes:
            if sh.name in ("decor", "QR") or sh.left is None:
                continue
            if not (getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()) and sh.shape_type != 13:
                continue  # decoration without text may bleed off the edge on purpose
            if sh.left < -0.1 * EMU or sh.top < -0.1 * EMU or sh.left + sh.width > W + 0.1 * EMU or sh.top + sh.height > H + 0.1 * EMU:
                off.append((i, sh.name))
    results.append(("FAIL" if left_over else "PASS",
                    "no placeholders left (대괄호 빈칸, 20XX, OO, 000, 학교명 ...)" + (f": {left_over[:8]}{' ...(+%d)' % (len(left_over) - 8) if len(left_over) > 8 else ''}" if left_over else "")))
    results.append(("FAIL" if over else "PASS", "text fits its box (estimate)" + (f": {over[:6]}" if over else "")))
    results.append(("FAIL" if off else "PASS", "every shape inside the slide" + (f": {off[:4]}" if off else "")))
    results.append(("FAIL" if empty else "PASS", "no empty placeholder" + (f": {empty[:4]}" if empty else "")))
    return {"results": results, "fillins": listed, "texts": texts_all, "overflow": over, "slides": len(prs.slides)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path)
    ap.add_argument("--spec", type=Path, help="deck.json: its \"fillins\" list is allowed (reported, not failed)")
    ap.add_argument("--allow-blanks", action="store_true", help="the user wants a template / 양식 with blanks: report them as 「바꿔 넣을 곳」, do not FAIL")
    ap.add_argument("--fillins", default="", help="comma-separated fill-ins allowed to remain")
    ap.add_argument("--render", type=Path, help="also draw PNGs into this folder (LibreOffice if present, else an approximate preview)")
    ap.add_argument("--yes", action="store_true", help="with --render: the teacher agreed to install LibreOffice")
    a = ap.parse_args()
    fills = [x.strip() for x in a.fillins.split(",") if x.strip()]
    tb = False
    if a.spec:
        sp = json.loads(a.spec.read_text(encoding="utf-8"))
        fills += [str(x) for x in (sp.get("fillins") or [])]
        tb = sp.get("template_blanks") is True  # the user asked for a 양식: same as --allow-blanks
    if a.allow_blanks or tb:
        fills = ph.with_blanks(fills, True)
        print("NOTE 양식 모드: 빈칸을 일부러 남긴 파일이에요. 사용하기 전에 채워 주세요.")
    r = check_pptx(a.pptx, fills)
    for lv, msg in r["results"]:
        print(f"{lv:4} {msg}")
    if r["fillins"]:
        print("바꿔 넣을 곳: " + ", ".join(r["fillins"]))
    if a.render:
        import pptx_render
        rr = pptx_render.render(a.pptx, a.render, consent=a.yes, overflow=r["overflow"])
        print(("PASS " if rr["mode"] == "libreoffice" else "NOTE ") + rr["note"])
        for p in rr.get("files", [])[:1]:
            print(f"sheet: {p}")
    fails = sum(1 for lv, _ in r["results"] if lv == "FAIL")
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({fails} fail)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
