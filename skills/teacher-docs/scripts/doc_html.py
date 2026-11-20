# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Block model -> one A4 print-ready HTML page (TS Sans / Noto Serif KR embedded, only the glyphs used). Used for the PDF
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
    t = re.sub(r"(\d)\. (?=\d)", "\\1.\u00a0", t)  # 12. 11.(금) never breaks inside the date
    t = re.sub(r"([□☐■]) (?=\S)", "\\1\u00a0", t)  # a check box stays with its word
    return t.replace("\n", "<br>")


def _image_uri(path: str, base: Path | None) -> str:
    import base64
    import mimetypes
    p = Path(path)
    if not p.is_absolute() and base is not None:
        p = base / p
    if not p.exists():
        raise FileNotFoundError(f"그림 파일이 없어요: {path}")
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def qr_svg(url: str, size_mm: float) -> str:
    """Offline QR (qrcodegen, MIT) as inline SVG: black on white, 4-module quiet zone, prints well in grayscale."""
    for vp in (SKILL / "shared" / "vendor" / "qrcodegen", SKILL.parent.parent / "shared" / "vendor" / "qrcodegen", SKILL.parent / "teacher-slides" / "shared" / "vendor" / "qrcodegen"):
        if vp.exists() and str(vp) not in sys.path:
            sys.path.insert(0, str(vp))
    import qrcodegen
    t = url if re.match(r"^(https?://|mailto:|tel:)", url, re.I) else "https://" + url
    q = qrcodegen.QrCode.encode_text(t, qrcodegen.QrCode.Ecc.MEDIUM)
    n = q.get_size()
    rects = "".join(f'<rect x="{x + 4}" y="{y + 4}" width="1" height="1"/>' for y in range(n) for x in range(n) if q.get_module(x, y))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n + 8} {n + 8}" width="{size_mm}mm" height="{size_mm}mm" shape-rendering="crispEdges">'
            f'<rect width="{n + 8}" height="{n + 8}" fill="#fff"/><g fill="#000">{rects}</g></svg>')


def render(model: dict, mood: str = "단정", embed_fonts: bool = True, base: Path | None = None, scale: float | None = None) -> str:
    kind = model["meta"]["kind"]
    k = float(scale if scale is not None else model["meta"].get("scale", 1.0))  # print scale: every pt size is multiplied by it
    lh = float(model["meta"].get("line", 1.6))
    pt = lambda v: f"{v * k:.2f}".rstrip("0").rstrip(".")  # noqa: E731
    dressed = kind in ("notice", "guide", "form")  # a quiet title band + accent headings (공문·보고서 stay plain black)
    c = _tokens(mood)
    accent = "#111111" if kind == "gongmun" else c.get("primary", "#1f5fbf")
    serif = model["meta"].get("font", "batang") == "batang"
    sans = "'TS Sans','Pretendard','Noto Sans KR','맑은 고딕','Malgun Gothic',sans-serif"   # the studio face (shared/design/system.py)
    fam = "'Noto Serif KR','함초롬바탕','Batang',serif" if serif else sans
    head_fam = sans if dressed else fam   # 안내문·통신문·신청서: sans headings over the body face (editorial pairing); 공문·보고서 keep one face
    try:
        import system as _ds
        polish = _ds.polish_css("print")
    except Exception:  # noqa: BLE001
        polish = ""
    parts = []
    for bl in model["blocks"]:
        t = bl["t"]
        if t == "p":
            size, bold = docmodel.STYLES.get(bl.get("style", "body"), (12.5, False))
            ind = bl.get("indent", 0)
            text = bl["text"]
            st = f"font-size:{pt(size)}pt;{'font-weight:700;' if bold else ''}text-align:{bl.get('align', 'left')};"
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
            cls = ""
            if bl.get("style") in ("heading", "title", "subtitle") and kind != "gongmun":
                st += f"color:{accent};"
                if dressed and bl.get("style") == "title":
                    cls = ' class="band"'
                elif dressed and bl.get("style") == "heading":
                    cls = ' class="hd"'
            parts.append(f'<p{cls} style="{st}">{_rich(text)}</p>')
        elif t == "pagebreak":
            parts.append('<div class="pb"></div>')
        elif t in ("image", "qr"):
            al = {"left": "flex-start", "right": "flex-end"}.get(bl.get("align", "center"), "center")
            if t == "image":
                inner = f'<img src="{_image_uri(bl["file"], base)}" style="width:{bl["width_mm"]}mm;max-width:100%;height:auto" alt="{html.escape(bl.get("caption", ""))}">'
            else:
                inner = qr_svg(bl["url"], bl["size_mm"])
            cap = f'<figcaption style="font-size:{pt(10)}pt">{_rich(bl["caption"])}</figcaption>' if bl.get("caption") else ""
            parts.append(f'<figure style="align-items:{al}">{inner}{cap}</figure>')
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
            parts.append(f'<table class="t-{kind_t}{" tall" if bl.get("tall") else ""}">{cols}{head}<tbody>{"".join(body)}</tbody></table>')
    css = f"""
@page{{size:A4;margin:20mm 20mm 15mm 20mm}}
html,body{{margin:0;background:#fff;color:#111}}
body{{font-family:{fam};font-size:{pt(12.5)}pt;line-height:{lh};word-break:keep-all;overflow-wrap:break-word}}
.pb{{break-before:page;page-break-before:always;height:0}}
figure{{margin:6pt 0 8pt;display:flex;flex-direction:column;gap:3pt;break-inside:avoid}} figcaption{{color:#333}}
.band{{font-family:{head_fam};color:#111!important;font-weight:700;letter-spacing:-.03em;line-height:1.25;text-align:left!important;padding:{pt(10)}pt 0 {pt(9)}pt;margin:{pt(2)}pt 0 {pt(10)}pt;border-top:{pt(3)}pt solid {accent};border-bottom:.6pt solid #9aa1aa;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.hd{{font-family:{head_fam};letter-spacing:-.02em;border-left:{pt(3)}pt solid {accent};padding-left:{pt(7)}pt;margin-bottom:{pt(3)}pt;break-after:avoid}}
.t-form.tall th,.t-form.tall td{{padding:{pt(9)}pt {pt(8)}pt}}
.doc{{max-width:170mm;margin:0 auto}}
p{{margin:0 0 2pt;white-space:pre-wrap}} p.sp{{line-height:.8}}
hr{{border:0;border-top:1.6pt solid #222;margin:4pt 0 8pt}}
.cut{{text-align:center;font-size:{pt(10)}pt;color:#555;margin:14pt 0 8pt}}
table{{width:100%;border-collapse:collapse;margin:6pt 0 8pt;font-size:{pt(11)}pt;page-break-inside:avoid}}
th,td{{border:{'.8pt solid #333' if not dressed else '.6pt solid #6b7280'};padding:4pt 7pt;vertical-align:middle;word-break:keep-all;white-space:pre-wrap}}
th{{background:{'#e8edf4' if not dressed else '#f0f2f5'};font-weight:700;text-align:center{';font-family:' + head_fam if dressed else ''}}}
thead th{{border-bottom-width:1.2pt}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}
.t-titlebox td{{border:2pt solid #222;text-align:center;font-size:{pt(20)}pt;font-weight:700;padding:10pt}}
.t-box th{{background:{'#e8edf4' if kind == 'gongmun' else c.get('bg2', '#eef2f7')};text-align:left}}
{polish}
p{{white-space:pre-wrap;text-wrap:initial}}
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
