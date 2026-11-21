# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Draw a .pptx as a rough picture with Pillow only - the preview for places where no browser can start
(an agent's security box, a server). Rougher than pptx_draw.py's HTML drawing: boxes with their fill colour, text wrapped
in its box at its own size, table grids, grey stand-ins for pictures and charts. Enough to see what sits where, how full
each slide is and which box is too small for its text. Always labelled as a sketch.

    from pptx_sketch import sketch
    sheet, pngs = sketch(Path("deck.pptx"), Path("review"), overflow=[(slide_no, text, ratio), ...])
"""
from __future__ import annotations

from pathlib import Path

import pptx_draw
from pptx_draw import X, X1, color_of

W = 1280  # px width of one drawn slide
SKETCH_NOTE = ("밑그림 미리보기예요 (이 환경에서는 브라우저를 띄울 수 없어 도형 위치·색·글만 그렸어요: 그림·차트·글꼴·줄바꿈은 실제와 달라요). "
               "무엇이 어디에 있는지와 장이 비어 보이는지만 이 그림으로 확인하세요.")


def _font(size: int, skill: Path):
    from PIL import ImageFont
    cands = []
    for base in (skill / "shared" / "fonts", skill.parent.parent / "shared" / "fonts"):
        if base.exists():
            cands += sorted(base.rglob("*.ttf")) + sorted(base.rglob("*.otf"))
    cands += [Path(p) for p in ("C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")]
    for c in cands:
        try:
            return ImageFont.truetype(str(c), size)
        except Exception:  # noqa: BLE001 - woff2 or a missing file: try the next one
            continue
    return ImageFont.load_default()


def _rgb(ca, default):
    if not ca:
        return default
    h, a = ca
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if a < 0.999:  # blend on white
        r, g, b = (int(255 - (255 - v) * a) for v in (r, g, b))
    return (r, g, b)


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _wrap(draw, text: str, font, width: float) -> list[str]:
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if draw.textlength(cur + ch, font=font) > width and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


def _paras(txbody, th=None) -> list[tuple]:
    """[(text, size in hundredths of a point or 0, (hex, alpha) of the first coloured run or None)] per paragraph."""
    out = []
    for p in X(txbody, "./a:p"):
        t = "".join(X(p, ".//a:t/text()"))
        sz = X(p, ".//a:rPr/@sz") or X(p, "./a:pPr/a:defRPr/@sz") or X(p, "./a:endParaRPr/@sz")
        if t.strip():
            col = None
            for rp in X(p, ".//a:rPr/a:solidFill"):
                col = color_of(rp, th) if th is not None else None
                if col:
                    break
            out.append((t, int(sz[0]) if sz else 0, col))
    return out


def _slide_png(prs, slide, no: int, bad: set, skill: Path, fonts: dict):
    from PIL import Image, ImageDraw
    dr = pptx_draw.Draw(prs, slide)
    sx = W / dr.W
    H = int(W * dr.H / dr.W)
    bg = (255, 255, 255)
    try:
        b = pptx_draw.background(dr)
        if b.startswith("#") and len(b) == 7:
            bg = tuple(int(b[i:i + 2], 16) for i in (1, 3, 5))
    except Exception:  # noqa: BLE001
        pass
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)

    def font(px: int):
        px = max(9, min(120, int(px)))
        if px not in fonts:
            fonts[px] = _font(px, skill)
        return fonts[px]

    def text_in(paras, box, fill_bg, default_pt=18):
        x0, y0, x1, y1 = box
        y = y0 + 6
        auto = (25, 25, 25) if _lum(fill_bg) > 140 else (250, 250, 250)
        for t, sz, col in paras:
            px = (sz / 100 if sz else default_pt) * 12700 * sx  # points -> EMU -> px
            f = font(px)
            ink = _rgb(col, auto)
            for ln in _wrap(d, t, f, max(20, x1 - x0 - 12)):
                if y > y1 + px:  # ran past its box: stop drawing, the caller marks it
                    return
                d.text((x0 + 6, y), ln, font=f, fill=ink)
                y += px * 1.25

    for tag, el, x, y, w, h in pptx_draw.leaf_boxes(prs, slide):
        try:
            box = (x * sx, y * sx, (x + w) * sx, (y + h) * sx)
            if box[2] - box[0] < 2 and box[3] - box[1] < 2:
                continue
            if tag == "cxnSp" or (w * sx < 4 or h * sx < 4):  # a line
                ln = color_of(X1(el, "./p:spPr/a:ln/a:solidFill"), dr.th)
                d.line(box, fill=_rgb(ln, (120, 120, 120)), width=2)
                continue
            if tag == "pic":
                d.rectangle(box, fill=(225, 229, 235), outline=(150, 155, 165))
                d.text((box[0] + 8, box[1] + 8), "[그림]", font=font(16), fill=(90, 95, 105))
                continue
            if tag == "graphicFrame":
                tbl = X1(el, ".//a:tbl")
                if tbl is None:
                    d.rectangle(box, fill=(238, 240, 244), outline=(150, 155, 165))
                    d.text((box[0] + 8, box[1] + 8), "[차트]", font=font(16), fill=(90, 95, 105))
                    continue
                cols = [int(c) for c in X(tbl, "./a:tblGrid/a:gridCol/@w")] or [w]
                rows = X(tbl, "./a:tr")
                tot_w, tot_h = sum(cols) or 1, sum(int(r.get("h", 0)) for r in rows) or 1
                cy = box[1]
                for ri, r in enumerate(rows):
                    rh = int(r.get("h", 0)) / tot_h * (box[3] - box[1])
                    cx = box[0]
                    for ci, tc in enumerate(X(r, "./a:tc")[:len(cols)]):
                        cw = cols[ci] / tot_w * (box[2] - box[0])
                        fc = _rgb(color_of(X1(tc, "./a:tcPr/a:solidFill"), dr.th), (232, 236, 242) if ri == 0 else bg)
                        d.rectangle((cx, cy, cx + cw, cy + rh), fill=fc, outline=(165, 170, 180))
                        text_in(_paras(X1(tc, "./a:txBody"), dr.th), (cx, cy, cx + cw, cy + rh), fc, 14)
                        cx += cw
                    cy += rh
                continue
            fill = color_of(X1(el, "./p:spPr/a:solidFill"), dr.th)
            if fill is None and X1(el, "./p:spPr/a:gradFill") is not None:
                fill = color_of(X1(el, "./p:spPr/a:gradFill/a:gsLst/a:gs"), dr.th)
            line = color_of(X1(el, "./p:spPr/a:ln/a:solidFill"), dr.th)
            fc = _rgb(fill, None)
            prst = (X(el, "./p:spPr/a:prstGeom/@prst") or ["rect"])[0]
            if fc is not None or line is not None:
                kw = dict(fill=fc, outline=_rgb(line, None), width=2)
                if prst == "ellipse":
                    d.ellipse(box, **kw)
                elif prst in ("roundRect", "round2SameRect", "snipRoundRect"):
                    d.rounded_rectangle(box, radius=max(2, int(min(box[2] - box[0], box[3] - box[1]) * 0.12)), **kw)
                else:
                    d.rectangle(box, **kw)
            tb = X1(el, "./p:txBody")
            if tb is not None:
                paras = _paras(tb, dr.th)
                if paras:
                    text_in(paras, box, fc if fc is not None else bg)
                    first = paras[0][0].strip()[:20]
                    if first and any(n == no and t and first.startswith(t[:20]) for n, t in bad):
                        d.rectangle(box, outline=(255, 45, 45), width=4)
        except Exception:  # noqa: BLE001 - one odd shape must not kill the sketch
            continue
    d.rectangle((0, 0, W - 1, H - 1), outline=(120, 120, 120))
    d.text((8, H - 24), str(no), font=font(16), fill=(110, 110, 110))
    return im


def sketch(path: Path, out: Path, overflow=(), cols: int = 2):
    """Write <name>-sketch-NN.png per slide and <name>-sketch-sheet.png. Returns (sheet path or None, [png paths])."""
    from PIL import Image
    from pptx import Presentation
    out.mkdir(parents=True, exist_ok=True)
    skill = Path(__file__).resolve().parent.parent
    prs = Presentation(str(path))
    bad = {(n, t) for n, t, _ in overflow}
    fonts: dict = {}
    pngs, ims = [], []
    for i, s in enumerate(prs.slides, 1):
        im = _slide_png(prs, s, i, bad, skill, fonts)
        p = out / f"{path.stem}-sketch-{i:02d}.png"
        im.save(p)
        pngs.append(p)
        ims.append(im)
    if not ims:
        return None, []
    tw = 800
    th = int(tw * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows), "#222222")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    dest = out / f"{path.stem}-sketch-sheet.png"
    sheet.save(dest)
    return dest, pngs
