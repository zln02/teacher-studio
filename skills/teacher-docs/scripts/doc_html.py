# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Block model -> one A4 print-ready HTML page (Noto Serif/Sans KR embedded, only the glyphs used). Used for the PDF
(headless browser print, see pdf_tools.html_to_pdf) and as a quick look. Colours from the house design tokens
(shared/design/design.py, use=print); official documents (공문) stay black.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import docmodel

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
for _d in ("design", "fonts"):
    for _p in (SKILL / "shared" / _d, SKILL.parent.parent / "shared" / _d):
        if _p.exists():
            sys.path.insert(0, str(_p))
            break


def _tokens(mood: str = "단정") -> dict:
    try:
        import design
        return design.generate(use="print", mood=mood)["colors"]
    except Exception:  # noqa: BLE001
        return {"primary": "#1f5fbf", "text": "#17202e", "bg2": "#f1f4f8", "cardBorder": "#c9d3e0"}


def _rich(s: str) -> str:
    t = html.escape(s)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


def render(model: dict, mood: str = "단정", embed_fonts: bool = True) -> str:
    kind = model["meta"]["kind"]
    c = _tokens(mood)
    accent = "#111111" if kind == "gongmun" else c.get("primary", "#1f5fbf")
    serif = model["meta"].get("font", "batang") == "batang"
    fam = "'Noto Serif KR','함초롬바탕','Batang',serif" if serif else "'Noto Sans KR','맑은 고딕','Malgun Gothic',sans-serif"
    parts = []
    for bl in model["blocks"]:
        t = bl["t"]
        if t == "p":
            size, bold = docmodel.STYLES.get(bl.get("style", "body"), (12.5, False))
            ind = bl.get("indent", 0)
            text = bl["text"]
            st = f"font-size:{size}pt;{'font-weight:700;' if bold else ''}text-align:{bl.get('align', 'left')};"
            if bl.get("hang"):
                hang = bl["hang"] + " "
                st += f"padding-left:calc({ind}em + {len(hang) * 0.55:.2f}em);text-indent:-{len(hang) * 0.55:.2f}em;"
                text = bl["hang"] + " " + text
            elif bl.get("hang_text"):
                st += f"padding-left:calc({ind}em + 3em);text-indent:-3em;"
            elif ind:
                st += f"padding-left:{ind}em;"
            if bl.get("space_before"):
                st += "margin-top:10pt;"
            if bl.get("style") in ("heading", "title", "subtitle") and kind != "gongmun":
                st += f"color:{accent};"
            parts.append(f'<p style="{st}">{_rich(text)}</p>')
        elif t == "space":
            parts.append('<p class="sp">&nbsp;</p>')
        elif t == "rule":
            parts.append('<hr>')
        elif t == "cut":
            parts.append('<p class="cut">✂ - - - - - - - - - - - - (절 취 선) - - - - - - - - - - - -</p>')
        elif t == "table":
            kind_t = bl.get("kind", "grid")
            rows = bl["rows"]
            head = ""
            if bl.get("columns"):
                head = "<thead><tr>" + "".join(f"<th>{_rich(x)}</th>" for x in bl["columns"]) + "</tr></thead>"
            body = []
            for r, row in enumerate(rows):
                cells = []
                for ci, x in enumerate(row):
                    if (kind_t == "box" and r == 0) or (kind_t == "form" and ci == 0):
                        cells.append(f"<th>{_rich(x)}</th>")
                    else:
                        num = " class='n'" if re.match(r"^[\s+\-−]?[\d,.]+\s*\S{0,2}$", x) else ""
                        cells.append(f"<td{num}>{_rich(x)}</td>")
                body.append("<tr>" + "".join(cells) + "</tr>")
            cols = ""
            if bl.get("widths"):
                tot = sum(bl["widths"])
                cols = "<colgroup>" + "".join(f'<col style="width:{w / tot * 100:.1f}%">' for w in bl["widths"]) + "</colgroup>"
            parts.append(f'<table class="t-{kind_t}">{cols}{head}<tbody>{"".join(body)}</tbody></table>')
    css = f"""
@page{{size:A4;margin:20mm 20mm 15mm 20mm}}
html,body{{margin:0;background:#fff;color:#111}}
body{{font-family:{fam};font-size:12.5pt;line-height:1.6;word-break:keep-all;overflow-wrap:break-word}}
.doc{{max-width:170mm;margin:0 auto}}
p{{margin:0 0 2pt}} p.sp{{line-height:.8}}
hr{{border:0;border-top:1.6pt solid #222;margin:4pt 0 8pt}}
.cut{{text-align:center;font-size:10pt;color:#555;margin:14pt 0 8pt}}
table{{width:100%;border-collapse:collapse;margin:6pt 0 8pt;font-size:11pt;page-break-inside:avoid}}
th,td{{border:.8pt solid #333;padding:4pt 7pt;vertical-align:middle;word-break:keep-all}}
th{{background:#e8edf4;font-weight:700;text-align:center}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}
.t-titlebox td{{border:2pt solid #222;text-align:center;font-size:20pt;font-weight:700;padding:10pt}}
.t-box th{{background:{'#e8edf4' if kind == 'gongmun' else c.get('bg2', '#eef2f7')};text-align:left}}
@media screen{{body{{background:#e9ecef}} .doc{{background:#fff;padding:20mm;margin:16px auto;box-shadow:0 2px 10px rgba(0,0,0,.15);max-width:170mm}}}}
"""
    page = (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(model['meta'].get('title') or '문서')}</title><style>{css}</style></head><body><div class='doc'>{''.join(parts)}</div></body></html>")
    if embed_fonts:
        try:
            import embed
            page, _rep = embed.embed(page)
        except Exception:  # noqa: BLE001 - fonts are a nicety; the page still prints with system fonts
            pass
    return page
