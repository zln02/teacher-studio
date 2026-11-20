# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Look at a PDF without reading it into the conversation: page count, how full each page is, the smallest text size,
and ONE small preview picture of all pages side by side.

    info(pdf)            -> {"pages": 2, "fill": [0.93, 0.41], "min_pt": 10.0, "sizes": {10.0: 120, 12.5: 900}}
    sheet(pdf, out_png)  -> one PNG (max 6 pages, about 420px per page): open THIS instead of the PDF (cheap to look at)
    checks(pdf, max_pages, min_font) -> [(level, message)] for doc_check / docs.py

fill = how far down the ink reaches on the page (0..1). A last page under 15 % means a few lines spilled over: set "max_pages"
in the spec (the builder then shrinks the print scale a little) or shorten the text.
Uses pypdfium2 (already needed for `docs.py pdf png`); without it the checks say so instead of guessing.
"""
from __future__ import annotations

from pathlib import Path

SMALLEST_OK = 9.0  # pt: below this a printed A4 notice is hard to read


def _open(pdf):
    import pypdfium2 as pdfium
    return pdfium, pdfium.PdfDocument(str(pdf))


def info(pdf) -> dict:
    pdfium, doc = _open(pdf)
    fills, sizes = [], {}
    try:  # Chrome / Edge print PDFs (Skia) draw text in CSS px inside a 0.75 page scale: the reported size is 4/3 of the real pt
        k = 0.75 if "skia" in str(doc.get_metadata_dict().get("Producer", "")).lower() else 1.0
    except Exception:  # noqa: BLE001
        k = 1.0
    for i in range(len(doc)):
        page = doc[i]
        im = page.render(scale=0.35).to_pil().convert("L")
        w, h = im.size
        px = im.load()
        last = 0
        for y in range(h - 1, -1, -1):
            if any(px[x, y] < 200 for x in range(0, w, 2)):
                last = y + 1
                break
        fills.append(round(last / h, 2))
        try:
            tp = page.get_textpage()
            n = tp.count_chars()
            raw = pdfium.raw
            for ci in range(0, n, 3):
                if raw.FPDFText_GetUnicode(tp, ci) <= 32:
                    continue
                s = round(raw.FPDFText_GetFontSize(tp, ci) * k * 2) / 2
                if s > 0:
                    sizes[s] = sizes.get(s, 0) + 1
        except Exception:  # noqa: BLE001 - sizes are optional; fill and pages still count
            pass
    total = sum(sizes.values())
    real = [s for s, c in sizes.items() if c >= max(3, total * 0.004)]  # ignore a stray glyph or two
    n_pages = len(doc)
    doc.close()  # Windows: an open handle would lock the file the caller may still want to move or delete
    return {"pages": n_pages, "fill": fills, "min_pt": min(real) if real else None, "sizes": dict(sorted(sizes.items()))}


def sheet(pdf, out_png, max_pages: int = 6, page_w: int = 420) -> Path | None:
    """All pages side by side in one small picture (thin grey gap). Returns the path or None when nothing could be drawn."""
    try:
        from PIL import Image
        _, doc = _open(pdf)
    except Exception:  # noqa: BLE001
        return None
    ims = []
    for i in range(min(len(doc), max_pages)):
        im = doc[i].render(scale=1.0).to_pil().convert("RGB")
        ims.append(im.resize((page_w, int(im.height * page_w / im.width))))
    doc.close()
    if not ims:
        return None
    gap = 10
    sh = Image.new("RGB", (len(ims) * (page_w + gap) + gap, max(i.height for i in ims) + 2 * gap), (120, 124, 130))
    for n, im in enumerate(ims):
        sh.paste(im, (gap + n * (page_w + gap), gap))
    out_png = Path(out_png)
    sh.save(out_png)
    return out_png


def checks(pdf, max_pages: int | None = None, min_font: float | None = None) -> list[tuple[str, str]]:
    try:
        r = info(pdf)
    except Exception as exc:  # noqa: BLE001
        return [("NOTE", f"쪽수·글자 크기를 재지 못했어요 ({type(exc).__name__}: pypdfium2가 있으면 잴 수 있어요)")]
    out = []
    pct = " · ".join(f"{i + 1}쪽 {int(f * 100)}%" for i, f in enumerate(r["fill"]))
    if max_pages and r["pages"] > max_pages:
        out.append(("FAIL", f"쪽수 {r['pages']}쪽 > 상한 {max_pages}쪽 (채움: {pct}) -> 글을 줄이거나 design.font_size를 조금 낮추기"))
    else:
        out.append(("PASS", f"쪽수 {r['pages']}쪽" + (f" (상한 {max_pages}쪽)" if max_pages else "") + f" · 채움 {pct}"))
    if r["pages"] > 1 and r["fill"][-1] < 0.15:
        out.append(("WARN", f"마지막 쪽에 몇 줄만 넘어갔어요 ({int(r['fill'][-1] * 100)}%) -> spec에 \"max_pages\": {r['pages'] - 1} 을 넣으면 한 쪽 줄여 맞춰요"))
    if r["min_pt"] is not None:
        floor = float(min_font) if min_font else SMALLEST_OK
        if r["min_pt"] < floor - 0.26:
            out.append(("FAIL" if min_font else "WARN", f"가장 작은 글자 {r['min_pt']:g}pt < {floor:g}pt -> 인쇄하면 읽기 어려워요 (design.font_size를 키우거나 글을 줄이기)"))
        else:
            out.append(("PASS", f"가장 작은 글자 {r['min_pt']:g}pt (하한 {floor:g}pt)"))
    return out
