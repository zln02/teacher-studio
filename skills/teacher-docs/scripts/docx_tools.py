# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Word (.docx) with python-docx (MIT, installed on first need via shared/tools/ensure.py):

    write(model, out, template=None)   block model -> .docx (A4, 20mm margins, house type scale, hanging marks, styled tables)
    replace(path, out, values)         {{키}} / [키] / exact text -> value, run-aware (formatting kept), tables included
    text(path)                         paragraph strings

The user's own .docx/.dotx as `template` wins: its styles, margins and headers are kept, we only add paragraphs.
For tracked changes, comments or complex layout hand the file to the official docx skill if it is installed.
"""
from __future__ import annotations

import re
from pathlib import Path

import docmodel

FONTS = {"batang": "바탕", "dotum": "맑은 고딕"}
HEAD_FILL = "E8EDF4"


def _need():
    try:
        import docx  # noqa: F401
        return True
    except ImportError:
        return False


def _shade(cell, hexfill: str):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexfill)
    tcPr.append(sh)


def _bottom_border(par, size=12):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    pPr = par._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), str(size))
    b.set(qn("w:space"), "1")
    b.set(qn("w:color"), "222222")
    bdr.append(b)
    pPr.append(bdr)


def _font(run, name: str, size: float, bold: bool):
    from docx.oxml.ns import qn
    from docx.shared import Pt
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        from docx.oxml import OxmlElement
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia"):
        rf.set(qn(k), name)


def _runs(par, text: str, font: str, size: float, bold: bool):
    for j, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not part:
            continue
        lines = part.split("\n")
        for k, ln in enumerate(lines):
            r = par.add_run(ln)
            _font(r, font, size, bold or j % 2 == 1)
            if k < len(lines) - 1:
                r.add_break()


def write(model: dict, out, template=None) -> Path:
    import docx
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Mm, Pt

    d = docx.Document(str(template)) if template else docx.Document()
    if not template:
        for s in d.sections:
            s.page_width, s.page_height = Mm(210), Mm(297)
            s.left_margin = s.right_margin = s.top_margin = Mm(20)
            s.bottom_margin = Mm(15)
        st = d.styles["Normal"]
        st.font.size = Pt(docmodel.STYLES["body"][0])
        st.paragraph_format.space_after = Pt(2)
        st.paragraph_format.line_spacing = 1.35
    font = FONTS.get(model["meta"].get("font", "batang"), "바탕")
    AL = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER, "right": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}
    from hwpx_write import text_w
    for bl in model["blocks"]:
        t = bl["t"]
        if t == "p":
            size, bold = docmodel.STYLES.get(bl.get("style", "body"), (12.5, False))
            par = d.add_paragraph()
            par.alignment = AL[bl.get("align", "left")]
            pf = par.paragraph_format
            unit = size  # one Hangul character = font size in pt
            left = bl.get("indent", 0) * unit
            text = bl["text"]
            if bl.get("hang"):
                hw = text_w(bl["hang"] + " ", size) / 100
                pf.left_indent = Pt(left + hw)
                pf.first_line_indent = Pt(-hw)
                text = f"{bl['hang']} {text}"
            elif bl.get("hang_text"):
                hw = text_w(bl["hang_text"], size) / 100
                pf.left_indent = Pt(left + hw)
                pf.first_line_indent = Pt(-hw)
            elif left:
                pf.left_indent = Pt(left)
            if bl.get("space_before"):
                pf.space_before = Pt(10)
            _runs(par, text, font, size, bold)
        elif t == "space":
            d.add_paragraph()
        elif t == "rule":
            par = d.add_paragraph()
            _bottom_border(par)
        elif t == "cut":
            par = d.add_paragraph()
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _runs(par, "✂ - - - - - - - - - - - - - (절 취 선) - - - - - - - - - - - - -", font, 10, False)
        elif t == "table":
            rows = ([bl["columns"]] if bl.get("columns") else []) + bl["rows"]
            ncol = max(len(r) for r in rows)
            tb = d.add_table(rows=len(rows), cols=ncol)
            tb.style = "Table Grid"
            tb.alignment = WD_TABLE_ALIGNMENT.CENTER
            kind = bl.get("kind", "grid")
            widths = bl.get("widths") or [1 / ncol] * ncol
            for r, row in enumerate(rows):
                for c in range(ncol):
                    cell = tb.cell(r, c)
                    cell.width = Mm(170 * widths[c] / sum(widths))
                    txt = row[c] if c < len(row) else ""
                    head = (bl.get("columns") and r == 0) or (kind == "box" and r == 0) or (kind == "form" and c == 0)
                    style = "thead" if head else ("title" if kind == "titlebox" else ("body" if kind in ("box", "form") else "table"))
                    size, bold = docmodel.STYLES[style]
                    par = cell.paragraphs[0]
                    num = bool(re.match(r"^[\s+\-−]?[\d,.]+\s*\S{0,2}$", txt))
                    par.alignment = (WD_ALIGN_PARAGRAPH.CENTER if head or kind == "titlebox" else
                                     (WD_ALIGN_PARAGRAPH.RIGHT if num else WD_ALIGN_PARAGRAPH.LEFT))
                    _runs(par, txt, font, size, bold)
                    if head:
                        _shade(cell, HEAD_FILL)
            d.add_paragraph()
    d.core_properties.title = model["meta"].get("title", "")
    d.core_properties.author = ""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(out))
    return out


def _iter_pars(d):
    for p in d.paragraphs:
        yield p
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def _replace_runs(par, find: str, repl: str) -> int:
    n = 0
    while True:
        runs = par.runs
        texts = [r.text for r in runs]
        full = "".join(texts)
        i = full.find(find)
        if i < 0:
            return n
        j, pos, first = i + len(find), 0, True
        for r, s in zip(runs, texts):
            a, b = pos, pos + len(s)
            pos = b
            if b <= i or a >= j:
                continue
            lo, hi = max(i, a) - a, min(j, b) - a
            r.text = s[:lo] + (repl if first else "") + s[hi:]
            first = False
        n += 1
        if find in repl:
            return n


def replace(path, out, values: dict) -> dict:
    import docx
    if Path(out).resolve() == Path(path).resolve():
        raise ValueError("out must differ from the source (원본을 덮어쓰지 않아요)")
    d = docx.Document(str(path))
    done = []
    for k, v in values.items():
        keys = [k] if (k.startswith("{{") or k.startswith("[")) else ["{{" + k + "}}", "[" + k + "]", "{{ " + k + " }}"]
        for kk in keys:
            hit = sum(_replace_runs(p, kk, str(v)) for p in _iter_pars(d))
            if hit:
                done.append(k)
                break
    d.save(str(out))
    return {"filled": done, "missing": [k for k in values if k not in done], "out": str(out)}


def text(path) -> list[str]:
    import docx
    return [p.text for p in _iter_pars(docx.Document(str(path)))]
