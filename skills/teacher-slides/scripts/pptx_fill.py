# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""How full does a slide LOOK? A coarse ink map of a .pptx slide (no rendering needed), used by pptx_check.py.

    measure(prs, slide, index, total) -> {kind, content, bottom, top, chars, hollow: [...]}

content  share of the slide covered by real content: estimated text extent (not the whole text box), tables, charts, pictures,
         lines and small drawn shapes. Cards / panels count only through what is inside them.
bottom   how far down the content reaches (0..1). A body slide that stops above the middle looks half empty on a projector.
hollow   big filled boxes (cards) that hold almost nothing.
kind     'cover' (first / last slide), 'divider' (a few words only: section, statement, quote) or 'content'.
Thresholds (calibrated on the 12 decks of docs/research/ceiling-eval-2026-11): content slide FAIL when content < 6 % or the
content ends above 60 % of the height; cover/divider FAIL only when nearly blank (< 1.2 %).
"""
from __future__ import annotations

import pptx_fit as pfit
from pptx_draw import X, X1, leaf_boxes

GW, GH = 64, 36
EMU_PT = 12700
MIN_CONTENT, MIN_BOTTOM, MIN_BLANK = 0.06, 0.60, 0.012


def _mark(grid, x0, y0, x1, y1):
    for gy in range(max(0, int(y0 * GH)), min(GH, int(y1 * GH + 0.999))):
        row = grid[gy]
        for gx in range(max(0, int(x0 * GW)), min(GW, int(x1 * GW + 0.999))):
            row[gx] = 1


def _text_extent(el, x, y, w, h):
    """Estimated box (EMU) that the text really occupies inside its frame, plus its character count."""
    tx = X1(el, "./p:txBody")
    if tx is None:
        return None, 0
    bp = X1(tx, "./a:bodyPr")
    anchor = bp.get("anchor", "t") if bp is not None else "t"
    paras = []
    for p in X(tx, "./a:p"):
        txt = "".join(X(p, ".//a:t/text()"))
        szs = [int(v) / 100 for v in X(p, ".//a:rPr/@sz")]
        algn = (X(p, "./a:pPr/@algn") or ["l"])[0]
        sp = X(p, "./a:pPr/a:lnSpc/a:spcPct/@val")
        paras.append((txt, (max(szs) if szs else 18.0) * (int(sp[0]) / 100000 if sp else 1.0), algn, max(szs) if szs else 18.0))
    chars = sum(len(t.strip()) for t, _, _, _ in paras)
    if not chars:
        return None, 0
    wpt, hpt = max(w / EMU_PT - 14, 10), h / EMU_PT
    need = sum(pfit.lines_for(t or " ", real, wpt) * tall * pfit.LH for t, tall, _, real in paras)  # tall = size x line spacing
    need = min(need, max(hpt, 1) * 1.1)
    widest = min(wpt, max(pfit.width_em(t) * real for t, _, _, real in paras))
    al = max(set(a for _, _, a, _ in paras), key=[a for _, _, a, _ in paras].count)
    ex = x + {"ctr": (w - widest * EMU_PT) / 2, "r": w - widest * EMU_PT}.get(al, 0)
    ey = y + {"ctr": (h - need * EMU_PT) / 2, "b": h - need * EMU_PT}.get(anchor, 0)
    return (ex, max(ey, y), widest * EMU_PT, need * EMU_PT), chars


def measure(prs, slide, index: int, total: int) -> dict:
    W, H = prs.slide_width, prs.slide_height
    grid = [[0] * GW for _ in range(GH)]
    cards, chars, data = [], 0, 0
    for tag, el, x, y, w, h in leaf_boxes(prs, slide):
        fx, fy, fw, fh = x / W, y / H, w / W, h / H
        area = max(fw, 0) * max(fh, 0)
        name = (X(el, "./*/p:cNvPr/@name") or [""])[0]
        if tag in ("graphicFrame", "pic"):
            data += 1
            rows = X(el, ".//a:tbl/a:tr")
            if rows:  # a table grows with its text in PowerPoint: the declared frame height is only the minimum
                cols = [int(c.get("w")) for c in X(el, ".//a:tbl/a:tblGrid/a:gridCol")] or [w]
                est = 0.0
                for r in rows:
                    tall = 0.0
                    for ci, tc in enumerate(X(r, "./a:tc")):
                        txt = "".join(X(tc, ".//a:t/text()"))
                        szs = [int(v) / 100 for v in X(tc, ".//a:rPr/@sz")]
                        size = max(szs) if szs else 18.0
                        cw = max(cols[min(ci, len(cols) - 1)] / EMU_PT - 14, 10)
                        tall = max(tall, pfit.lines_for(txt or " ", size, cw) * size * pfit.LH + 8)
                    est += max(tall, int(r.get("h", "0")) / EMU_PT)
                fh = max(fh, est * EMU_PT / H)
            _mark(grid, fx, fy, fx + fw, fy + fh)
            continue
        prst = (X(el, "./p:spPr/a:prstGeom/@prst") or [""])[0]
        if tag == "cxnSp" or prst in ("line", "straightConnector1", "bentConnector3"):
            if X1(el, "./p:spPr/a:ln/a:noFill") is None:
                n = 24
                flip = (X(el, "./p:spPr/a:xfrm/@flipV") or ["0"])[0] in ("1", "true")
                for i in range(n + 1):
                    px, py = fx + fw * i / n, (fy + fh * (1 - i / n)) if flip else (fy + fh * i / n)
                    _mark(grid, px, py, px + 0.001, py + 0.001)
            continue
        ext, n = _text_extent(el, x, y, w, h)
        chars += n
        if ext:
            _mark(grid, ext[0] / W, ext[1] / H, (ext[0] + ext[2]) / W, (ext[1] + ext[3]) / H)
        filled = X1(el, "./p:spPr/a:noFill") is None and (X1(el, "./p:spPr/a:solidFill") is not None or X1(el, "./p:spPr/a:gradFill") is not None
                                                           or (X1(el, "./p:style") is not None and X1(el, "./p:nvSpPr/p:cNvSpPr[@txBox='1']") is None))
        lined = X1(el, "./p:spPr/a:ln/a:solidFill") is not None
        if not (filled or lined) or name in ("decor", "scrim"):
            continue
        edge_bar = (fw > 0.9 and fh < 0.12) or (fh > 0.9 and fw < 0.12)  # header / footer / side stripes
        if area >= 0.5 or edge_bar:
            continue
        if area >= 0.04:
            cards.append((fx, fy, fw, fh))
        elif not ext and name not in ("QR", "rule", "accent", "line"):
            _mark(grid, fx, fy, fx + fw, fy + fh)  # small drawn shape: an icon, a dot, a diagram part
        elif name == "QR":
            _mark(grid, fx, fy, fx + fw, fy + fh)
    cells = sum(map(sum, grid))
    rows = [i for i, r in enumerate(grid) if any(r)]
    hollow = []
    for cx, cy, cw, chh in cards:
        tot = ink = 0
        for gy in range(max(0, int(cy * GH)), min(GH, int((cy + chh) * GH + 0.999))):
            for gx in range(max(0, int(cx * GW)), min(GW, int((cx + cw) * GW + 0.999))):
                tot += 1
                ink += grid[gy][gx]
        if tot and cw * chh >= 0.10 and ink / tot < 0.03:
            hollow.append((round(cx, 2), round(cy, 2), round(ink / tot, 2)))
    kind = "cover" if index in (1, total) else ("divider" if chars <= 45 and not data else "content")
    return {"kind": kind, "content": cells / (GW * GH), "top": (rows[0] / GH) if rows else 1.0, "bottom": ((rows[-1] + 1) / GH) if rows else 0.0,
            "chars": chars, "hollow": hollow}


def problems(prs) -> list[tuple[int, str]]:
    """[(slide number, plain reason)] for slides that look empty."""
    out = []
    slides = list(prs.slides)
    for i, s in enumerate(slides, 1):
        m = measure(prs, s, i, len(slides))
        if m["kind"] == "content":
            if m["content"] < MIN_CONTENT:
                out.append((i, f"거의 비어 보여요 (내용 {m['content'] * 100:.0f}%)"))
            elif m["bottom"] < MIN_BOTTOM:
                out.append((i, f"아래쪽 절반이 비어 있어요 (내용이 위 {m['bottom'] * 100:.0f}%에서 끝남)"))
            elif len(m["hollow"]) >= 2:
                out.append((i, f"큰 상자 {len(m['hollow'])}개가 거의 비어 있어요"))
        elif m["content"] < MIN_BLANK:
            out.append((i, "글도 그림도 거의 없어요"))
    return out
