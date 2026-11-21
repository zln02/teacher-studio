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
  visual weight no body slide that looks mostly empty (pptx_fill.py: content < 6 % of the slide, or content ends above 60 % of the height)
  notes         placeholders in speaker notes count too
  unknowns      CONTENT-RULES 「Unknowns」: 「확인 필요」-type filler on slides (1-2 WARN, 3+ FAIL), a 「교사 초안」 stamp on a slide (FAIL),
                the example note repeated on slides or missing although the spec lists example values in "fillins" (WARN; a lesson deck
                needs none), underline blanks on a slide that is not a 양식 (WARN)
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


def check_pptx(path: Path, fillins=(), tol: float = 1.12, lesson: bool = False) -> dict:
    """Returns {results:[(level,msg)], fillins:[...], texts:[per-slide text], overflow:[(slide, text, ratio)]}."""
    from pptx import Presentation
    prs = Presentation(str(path))
    W, H = prs.slide_width, prs.slide_height
    results: list[tuple[str, str]] = []
    left_over, listed, texts_all, over, off, empty = [], [], [], [], [], []
    tiny, small, plain_n, body_n = [], [], 0, 0
    seen_txt, note_txt = [], []  # what the audience sees / the speaker notes (the unknowns policy treats them differently)
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
            for p_ in tf.paragraphs:  # text too small to project (page numbers and footers at the very bottom are not body text)
                for r_ in p_.runs:
                    if r_.font.size and r_.text.strip() and len(r_.text.strip()) > 2 and (sh.top or 0) < H * 0.9:
                        if r_.font.size.pt < 11:
                            tiny.append((i, r_.text.strip()[:14], r_.font.size.pt))
                        elif r_.font.size.pt < 14:
                            small.append((i, r_.text.strip()[:14], r_.font.size.pt))
        seen_txt.append("\n".join(texts))
        if s.has_notes_slide:
            texts.append(s.notes_slide.notes_text_frame.text or "")
            note_txt.append(texts[-1])
        txt = "\n".join(texts)
        texts_all.append(txt)
        if 1 < i < len(prs.slides):  # body slides: is anything on it besides text? (table, chart, picture, line, a grid of 3+ boxes)
            body_n += 1
            kinds = [sh.shape_type for sh in s.shapes]
            boxes = sum(1 for sh in s.shapes if sh.shape_type == 1 and sh.width and sh.width > W * 0.08 and sh.height > H * 0.08 and sh.width * sh.height < W * H * 0.5)
            if not (any(k in (3, 13, 19, 6, 9) for k in kinds) or any(getattr(sh, "has_chart", False) and sh.has_chart for sh in s.shapes)
                    or any(getattr(sh, "has_table", False) and sh.has_table for sh in s.shapes) or boxes >= 3):
                plain_n += 1
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
    pol = ph.policy_checks(seen_txt, note_txt, fillins, deck=True, lesson=lesson)
    if ph.ALLOW_ALL not in (fillins or []):
        ul = [(i, m.group(0)[:8]) for i, t in enumerate(seen_txt, 1) for m in ph.UNDERLINE.finditer(t)]
        if ul:
            pol.append(("WARN", f"슬라이드에 밑줄 빈칸 {len(ul)}곳 (예: {ul[0][0]}번) -> 그럴듯한 예시 값으로 채우고 fillins에 적으세요. 빈칸을 원하신 경우만 \"template_blanks\": true"))
    results += pol
    results.append(("FAIL" if over else "PASS", "text fits its box (estimate)" + (f": {over[:6]}" if over else "")))
    results.append(("FAIL" if off else "PASS", "every shape inside the slide" + (f": {off[:4]}" if off else "")))
    results.append(("FAIL" if empty else "PASS", "no empty placeholder" + (f": {empty[:4]}" if empty else "")))
    results.append(("FAIL" if tiny else "PASS", "text large enough to project (>= 11pt)" + (f": {len(tiny)} runs under 11pt, e.g. {tiny[:3]} -> 글자를 키우고 내용을 줄이거나 두 장으로" if tiny else "")))
    if small:
        results.append(("NOTE", f"{len(small)} text runs are 11-14pt (e.g. {small[:2]}): 뒷자리에서는 읽기 어려워요. 꼭 필요한 주석이 아니면 14pt 이상으로"))
    if body_n >= 6 and plain_n / body_n > 0.6:
        results.append(("NOTE", f"본문 {body_n}장 가운데 {plain_n}장이 글만 있어요 (표·그래프·그림·카드 없음) -> 내용 모양에 맞는 장으로 바꾸면 덜 단조로워요"))
    try:  # visual weight: a body slide that is mostly empty (or stops above the middle) reads as unfinished on a projector
        import pptx_fill
        thin = pptx_fill.problems(prs)
    except Exception as exc:  # the ink map must never block a deck it cannot read
        thin = []
        results.append(("NOTE", f"slide fill not measured ({str(exc)[:60]})"))
    results.append(("FAIL" if thin else "PASS", "no empty-looking slide (visual weight)" + (": " + "; ".join(f"{n}번 {why}" for n, why in thin[:6])
                    + " -> 그 장에 내용(표·그림·활동·예시)을 더 넣거나 옆 장과 합치세요" if thin else "")))
    return {"results": results, "fillins": listed, "texts": texts_all, "overflow": over, "slides": len(prs.slides), "thin": thin}


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
    tb = lesson = False
    if a.spec:
        sp = json.loads(a.spec.read_text(encoding="utf-8"))
        fills += [str(x) for x in (sp.get("fillins") or [])]
        lesson = str(sp.get("context") or "").strip().lower() in ("class", "수업")
        tb = sp.get("template_blanks") is True  # the user asked for a 양식: same as --allow-blanks
    if a.allow_blanks or tb:
        fills = ph.with_blanks(fills, True)
        print("NOTE 양식 모드: 빈칸을 일부러 남긴 파일이에요. 사용하기 전에 채워 주세요.")
    r = check_pptx(a.pptx, fills, lesson=lesson)
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
    if fails:
        print("NOT DONE: 위 FAIL을 고치고 이 점검을 다시 돌리세요. PASS가 될 때까지는 「다 됐어요」라고 하지 않아요. "
              "(모르는 값은 「우리 학교」·오늘 날짜처럼 그럴듯한 값으로 채우고 마지막에 한 줄로 알리기. 양식을 원한 경우만 --allow-blanks)")
    return 1 if fails else 0


def _no_browser_guard() -> bool:
    """True when no browser can start here (an agent's security box). shared/tools/workdir.py then prints ONE line and makes
    every screen check below skip at once instead of waiting for each launch to fail."""
    try:
        here = Path(__file__).resolve().parent
        for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
            if (d / "workdir.py").is_file():
                if str(d) not in sys.path:
                    sys.path.append(str(d))
                import workdir
                return workdir.guard_browser()
    except Exception:  # noqa: BLE001 - the guard must never stop a build
        pass
    return False


if __name__ == "__main__":
    _no_browser_guard()
    sys.exit(main())
