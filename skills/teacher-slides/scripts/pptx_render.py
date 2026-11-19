#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Draw a .pptx as PNG so a person (or the model) can LOOK at it.

    py pptx_render.py deck.pptx --out review/ [--yes]

mode "libreoffice": real rendering (soffice -> PDF -> PNG via pypdfium2). LibreOffice is large (~350MB): only with the teacher's yes (--yes).
mode "approx":      no LibreOffice -> an HTML drawn from the pptx shapes (position, colour, text, alignment) screenshotted with the
                    system Chrome/Edge. APPROXIMATE: fonts, line breaks and autofit differ from PowerPoint. Boxes whose text is
                    estimated to overflow get a red outline. Always say so when showing it.
"""
from __future__ import annotations

import argparse
import html
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
for _p in (SKILL / "shared" / "tools", SKILL.parent.parent / "shared" / "tools"):
    if _p.exists():
        sys.path.insert(0, str(_p))
        break
sys.path.insert(0, str(HERE))
APPROX_NOTE = "대략의 미리보기예요 (도형 위치로 그린 그림: 글꼴·줄바꿈·글자 넘침은 실제 PowerPoint와 달라요). 실제 확인은 PowerPoint에서 한 번 열어 보세요."


def _sheet(pngs, dest: Path, cols: int = 2, tw: int = 800):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in pngs]
    if not ims:
        return None
    th = int(tw * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (tw * cols, th * rows), "#222222")
    for i, im in enumerate(ims):
        sh.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    sh.save(dest)
    return dest


def pptx_to_html(path: Path, outdir: Path, overflow=()):
    """One HTML per slide, drawn from the shapes. overflow = [(slide_no, text, ratio)] from pptx_check (outlined red)."""
    from pptx import Presentation
    prs = Presentation(str(path))
    W, H = prs.slide_width, prs.slide_height
    bad = {(n, t) for n, t, _ in overflow}
    files = []
    for i, s in enumerate(prs.slides, 1):
        bg = "#fff"
        try:
            m = s._element.cSld.xpath("./p:bg//a:srgbClr/@val")
            if m:
                bg = "#" + m[0]
        except Exception:
            pass
        parts = []
        for sh in s.shapes:
            if sh.left is None:
                continue
            st = "left:%.2f%%;top:%.2f%%;width:%.2f%%;height:%.2f%%;" % (sh.left / W * 100, sh.top / H * 100, sh.width / W * 100, sh.height / H * 100)
            try:
                c = sh._element.spPr.xpath("./a:solidFill/a:srgbClr/@val")
                if c:
                    st += "background:#%s;" % c[0]
                g = sh._element.spPr.xpath("./a:prstGeom/@prst")
                if g and g[0] == "ellipse":
                    st += "border-radius:50%;"
                elif g and g[0] == "roundRect":
                    st += "border-radius:1.6cqw;"
            except Exception:
                pass
            t = ""
            first = ""
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    runs = para.runs
                    if not runs:
                        t += "<div>&nbsp;</div>"
                        continue
                    f = runs[0].font
                    sz = f.size.pt if f.size else 18
                    col = "#333"
                    m = para._p.xpath(".//a:rPr/a:solidFill/a:srgbClr/@val")
                    if m:
                        col = "#" + m[0]
                    al = para._p.xpath("./a:pPr/@algn")
                    al = al[0] if al else "l"
                    first = first or para.text.strip()[:20]
                    t += '<div style="text-align:%s;font-size:%.2fcqw;color:%s;font-weight:%s">%s</div>' % (
                        {"ctr": "center", "r": "right"}.get(al, "left"), sz / 960 * 100, col, "700" if f.bold else "400", html.escape(para.text))
                anchor = {"ctr": "center", "b": "flex-end"}.get((sh.text_frame._txBody.xpath("./a:bodyPr/@anchor") or ["t"])[0], "flex-start")
                st += "display:flex;flex-direction:column;justify-content:%s;" % anchor
            if (i, first) in bad:
                st += "outline:3px solid #ff2d2d;"
            parts.append('<div class=sh style="%s">%s</div>' % (st, t))
        doc = ('<meta charset=utf-8><style>body{margin:0;background:#222;display:flex;justify-content:center;align-items:center;height:100vh}'
               '.sl{position:relative;height:100vh;container-type:inline-size;overflow:hidden;font-family:"Noto Sans KR","Malgun Gothic",sans-serif}'
               '.sh{position:absolute;box-sizing:border-box;padding:.3cqw .6cqw;line-height:1.3}</style>'
               '<div class=sl style="background:%s;aspect-ratio:%d/%d">%s</div>' % (bg, W, H, "".join(parts)))
        f = outdir / f"_approx-{i:02d}.html"
        f.write_text(doc, encoding="utf-8")
        files.append(f)
    return files


def render(path: Path, out: Path, consent: bool = False, overflow=()) -> dict:
    """Returns {mode: 'libreoffice'|'approx', files: [sheet, png...], note}."""
    out.mkdir(parents=True, exist_ok=True)
    name = path.stem
    try:
        import ensure
    except ImportError:
        ensure = None
    lo = ensure.ensure_libreoffice(consent) if ensure and hasattr(ensure, "ensure_libreoffice") else {"ok": False, "prompt": ""}
    if lo["ok"]:
        tmp = Path(tempfile.mkdtemp())
        subprocess.run([lo["path"], "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(path)], capture_output=True, text=True, timeout=240)
        pdf = tmp / (name + ".pdf")
        pdfium = ensure.ensure("pypdfium2", consent=True)  # tiny (~6MB), and LibreOffice is already agreed
        if pdf.exists() and pdfium["ok"]:
            import pypdfium2 as pdfium_mod
            doc = pdfium_mod.PdfDocument(str(pdf))
            pngs = []
            for i in range(len(doc)):
                p = out / f"{name}-{i + 1:02d}.png"
                doc[i].render(scale=1.2).to_pil().save(p)
                pngs.append(p)
            sheet = _sheet(pngs, out / f"{name}-sheet.png")
            return {"mode": "libreoffice", "files": ([sheet] if sheet else []) + pngs, "note": "LibreOffice로 실제처럼 그렸어요. 그림을 보고 글자 넘침·겹침을 확인하세요."}
    files = pptx_to_html(path, out, overflow)  # no LibreOffice (or it failed): approximate drawing
    note = APPROX_NOTE + ("" if lo["ok"] else "  ※ " + lo["prompt"])
    try:
        from playwright.sync_api import sync_playwright
        ch = ensure.find_system_browser() if ensure else ""
        pngs = []
        with sync_playwright() as pw:
            b = pw.chromium.launch(channel=ch) if ch else pw.chromium.launch()
            pg = b.new_page(viewport={"width": 1600, "height": 900})
            for f in files:
                pg.goto(f.resolve().as_uri())
                pg.wait_for_timeout(250)
                p = f.with_suffix(".png")
                pg.screenshot(path=str(p))
                pngs.append(p)
            b.close()
        sheet = _sheet(pngs, out / f"{name}-approx-sheet.png")
        return {"mode": "approx", "files": ([sheet] if sheet else []) + pngs, "note": note}
    except Exception as exc:  # no browser: the HTML files are still there
        return {"mode": "approx", "files": files, "note": note + f" (그림 저장은 건너뜀: {str(exc)[:60]})"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--yes", action="store_true", help="the teacher agreed to install LibreOffice (large)")
    a = ap.parse_args()
    r = render(a.pptx, a.out, a.yes)
    print(r["mode"], r["note"])
    for f in r["files"][:1]:
        print("sheet:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
