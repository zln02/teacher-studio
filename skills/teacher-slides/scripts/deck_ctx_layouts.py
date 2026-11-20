# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Layouts for the context recipes (deck_context.py): table, summary (핵심 box), toc (목차), hero (홍보 표지), the public cover and
개조식 bullet lists, plus `decorate()` = the public header (section + 기관) and the 자료/주 line on data slides.

Registered into deck_layouts.REG at import (variants are filtered per context by dz["allowed"] in deck.pick_layouts).
Same 1920x1080 stage, 120px margins, text boxes sized by deck_kit.T (Korean-aware fit). Tables are ONE real <table> (one element).
"""
from __future__ import annotations

import re

import deck_art as art
import deck_context as dctx
from deck_kit import T, box, esc, kicker, n_lines, plain, rect, rich

MX, W, H = 120, 1920, 1080
CW = W - 2 * MX
_NUM = re.compile(r"^[\s+\-−]?[\d,.]+\s*(%|명|개|원|건|회|점|시간|일|억|만|천)?$")

CSS = """
.gtbl{width:100%;height:100%;border-collapse:collapse;table-layout:fixed;color:var(--tx);word-break:keep-all;font-family:var(--fb)}
.gtbl th{background:var(--pr);color:var(--bt);font-weight:800;text-align:center;border:1.5px solid var(--pr);padding:0 16px;word-break:keep-all}
.gtbl td{border:1.5px solid var(--line);padding:0 16px;font-weight:500;word-break:keep-all;text-align:left}
.gtbl tr:nth-child(even) td{background:var(--bg2)}
.gtbl td.n{text-align:right;font-variant-numeric:tabular-nums}
.gtbl td.hi{color:var(--emc);font-weight:800}
.gbox{border:3px solid var(--pr);border-radius:6px;background:var(--bg1)}
.gtab{background:var(--pr);color:var(--bt);font-weight:800;display:flex;align-items:center;justify-content:center;border-radius:4px;word-break:keep-all}
.src{color:var(--tx);font-weight:500}
.ghead{color:var(--tx);font-weight:700;word-break:keep-all}
.gnumr{color:var(--emc);font-weight:800;font-family:var(--fd)}
.cta{background:var(--pr);border-radius:999px}
.cta .tx{color:var(--bt);font-weight:800;text-align:center}
.hscrim{background:rgba(12,12,16,.66)}
.hang .tx{padding-left:1.25em;text-indent:-1.25em}
.dgm svg{display:block;width:100%;height:100%}.dgm .dl{font-family:var(--fb)}
"""

# ------------------------------------------------------------------- helpers


def _head(ctx, it, y=150, h=110, w=CW, x=MX, mx=72, mn=44):
    return T(ctx, it.get("title", ""), x, y, w, h, mx, mn, cls="h", va="m", lh=1.14) + rect(x, y + h + 8, w, 3, "rule strong")


def _items_html(ctx, items: list, x: int, y: int, w: int, h: int, marks: str = "box", mx: int = 40) -> str:
    """개조식 list: □ / ○ / - (or 가./1)/가)) with hanging indent; one common font size that fits the whole block."""
    lv = [dctx.item_level(s) for s in items]
    cnt = {1: 0, 2: 0, 3: 0}
    rows = []
    for level, text in lv:
        m = dctx.marker(level, cnt[level], marks)
        cnt[level] += 1
        for deeper in range(level + 1, 4):
            cnt[deeper] = 0
        rows.append((level, f"{m} {text}"))
    size = int(mx * (ctx.dz.get("tscale") or {}).get("p", 1.0))
    floor = ctx.floor
    gap = 0.55

    def need(sz):
        return sum(n_lines(t, sz, w - 64 * (lvl - 1) - sz * 1.3) * sz * 1.35 + sz * gap for lvl, t in rows)
    while size > floor and need(size) > h:
        size -= 2
    size = max(size, floor)
    out, cy = [], y
    for level, text in rows:
        ind = 64 * (level - 1)
        rh = n_lines(text, size, w - ind - size * 1.3) * size * 1.35 + 4
        cls = "li p hang" + (" mu" if level == 3 else "")  # first token 'li' = already scaled, T must not scale again
        out.append(T(ctx, text, x + ind, cy, w - ind, rh + 6, size, size, cls=cls, va="t", lh=1.35))
        cy += rh + size * gap
    return "".join(out)


# ------------------------------------------------------------------- public cover / bullets


def title_gov(ctx, it):
    org, date, dept = it.get("_org", ""), it.get("_date", ""), it.get("_dept", "")
    h = [rect(0, 0, W, 28, "panel"), rect(0, H - 28, W, 28, "panel")]
    if org:
        h.append(T(ctx, org, MX, 150, CW, 60, 40, 28, cls="p ghead", va="m", align="center"))
    h.append(rect(W // 2 - 360, 236, 720, 3, "rule strong"))
    h.append(T(ctx, it["title"], MX + 60, 300, CW - 120, 300, 96, 48, cls="h", va="m", lh=1.18, align="center"))
    if it.get("subtitle"):
        h.append(T(ctx, it["subtitle"], MX + 60, 620, CW - 120, 80, 40, 28, cls="p mu", va="m", align="center"))
    h.append(rect(W // 2 - 360, 730, 720, 3, "rule strong"))
    if date:
        h.append(T(ctx, date, MX, 790, CW, 56, 40, 28, cls="p", va="m", align="center"))
    if dept:
        h.append(T(ctx, dept, MX, 860, CW, 56, 36, 28, cls="p mu", va="m", align="center"))
    return {"html": "".join(h), "role": "cover", "room": True}


def bullets_gov(ctx, it):
    h = [_head(ctx, it)]
    h.append(_items_html(ctx, it["items"], MX + 8, 300, CW - 16, 620, str(it.get("marks", "box"))))
    return {"html": "".join(h), "role": "content", "room": True}


def bullets_govsplit(ctx, it):
    lead = it.get("lead") or it.get("kicker") or ""
    h = [rect(MX, 150, 520, 790, "cd"), T(ctx, it.get("title", ""), MX + 40, 190, 440, 300, 64, 40, cls="h", va="t", lh=1.18),
         rect(MX + 40, 520, 72, 6, "bar")]
    if lead:
        h.append(T(ctx, lead, MX + 40, 560, 440, 340, 32, 24, cls="p mu", va="t", lh=1.4))
    h.append(_items_html(ctx, it["items"], 720, 170, W - MX - 720, 760, str(it.get("marks", "box"))))
    return {"html": "".join(h), "role": "content", "room": True}


# ------------------------------------------------------------------- table / summary / toc


def _cell_cls(v, j, hi) -> str:
    c = []
    if _NUM.match(plain(str(v))):
        c.append("n")
    if hi is not None and j == hi:
        c.append("hi")
    return " ".join(c)


def table_grid(ctx, it):
    cols, rows = it["columns"], it["rows"]
    pub = ctx.dz.get("context") == "public"
    top = 300 if pub else 290
    bottom = 920 if (it.get("source") or it.get("footnote") or pub) else 970
    hh = [_head(ctx, it) if pub else T(ctx, it.get("title", ""), MX, 110, CW, 140, 72, 44, cls="h", va="m", lh=1.14)]
    if it.get("unit"):
        hh.append(T(ctx, f"(단위: {it['unit']})", W - MX - 420, top - 52, 420, 44, 26, 24, cls="p", va="m", align="right"))
    th = bottom - top
    nrow = len(rows) + 1
    rh = min(110, th / nrow)
    colw = CW / len(cols)
    size = min(40, int(rh * 0.42))
    size = max(ctx.floor, min(size, 36 if pub else 40))
    while size > ctx.floor and any(n_lines(plain(str(c)), size, colw - 36) * size * 1.25 > rh - 12 for r in [cols] + rows for c in r):
        size -= 2
    hi = it.get("highlight")
    head = "".join(f"<th>{rich(c)}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f'<td class="{_cell_cls(v, j, hi)}">{rich(v)}</td>' for j, v in enumerate(r)) + "</tr>" for r in rows)
    tbl = f'<table class="gtbl" style="font-size:{size}px;line-height:1.25"><thead><tr style="height:{rh:.0f}px">{head}</tr></thead><tbody>' + body.replace("<tr>", f'<tr style="height:{rh:.0f}px">') + "</tbody></table>"
    hh.append(box(MX, top, CW, rh * nrow, tbl, "tblwrap"))
    return {"html": "".join(hh), "role": "content", "room": True}


def summary_box(ctx, it):
    pub = ctx.dz.get("context") == "public"
    hh = [_head(ctx, {**it, "title": it.get("title") or "요약"})] if pub else [T(ctx, it.get("title") or "핵심 정리", MX, 110, CW, 130, 76, 48, cls="h", va="m", lh=1.14)]
    y = 300 if pub else 280
    if it.get("text"):
        hh.append(T(ctx, it["text"], MX, y, CW, 90, 44, 28, cls="p", va="m", lh=1.3))
        y += 110
    label = it.get("label") or "핵심"
    by, bh = y + 30, 930 - y - 30
    hh.append(rect(MX, by, CW, bh, "gbox"))
    hh.append(box(MX + 48, by - 26, 180, 56, f'<div class="tx" style="font-size:{max(ctx.floor, 28)}px;text-align:center">{esc(label)}</div>', "gtab"))
    hh.append(_items_html(ctx, it["points"], MX + 64, by + 62, CW - 128, bh - 96, "box", 44))
    return {"html": "".join(hh), "role": "content", "room": True}


def toc_list(ctx, it):
    items = it.get("items") or []
    pub = ctx.dz.get("context") == "public"
    hh = [T(ctx, it.get("title") or "목차", MX, 120, 600, 140, 88, 56, cls="h", va="m"), rect(MX, 280, 96, 8, "bar")]
    n = len(items)
    two = n > 5
    colw = (CW - 80) / 2 if two else 1100
    x0 = MX if two else 700
    per = -(-n // 2) if two else n
    rh = min(130, 640 / max(per, 1))
    for i, t in enumerate(items):
        c, r_ = (i // per, i % per) if two else (0, i)
        x, y = x0 + c * (colw + 80), 330 + r_ * rh
        lab = f"{dctx.roman(i + 1)}." if pub else f"{i + 1:02d}"
        hh.append(rect(x, y + rh - 2, colw, 2, "rule"))
        hh.append(T(ctx, lab, x, y, 130, rh - 6, 52, 32, cls="p gnumr", va="m"))
        hh.append(T(ctx, re.sub(r"^\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.\s*", "", str(t)), x + 140, y, colw - 150, rh - 6, 48, 30, cls="p", va="m"))
    return {"html": "".join(hh), "role": "content", "room": True}


# ------------------------------------------------------------------- hero (promo / personal cover)


def _cta(ctx, it, x, y, w=520):
    if not it.get("cta"):
        return ""
    return T(ctx, it["cta"], x, y, w, 96, 40, 28, cls="p cta", va="m", align="center")


def hero_full(ctx, it):
    d = ctx.dz
    if it.get("_src"):
        h = [f'<div class="bx imgfull" style="left:0;top:0;width:{W}px;height:{H}px"><img src="{it["_src"]}" alt="{esc(it.get("alt", it.get("headline", "")))}"></div>',
             rect(0, 0, W, H, "hscrim")]  # whole-photo veil: bright skies / suns must still give white text >= 4.5:1
        oncls = " on-img"
    else:
        h = [rect(1240, 0, 680, H, "panel"), box(1240, 0, 680, H, art.abstract(d, 680, H, ctx.idx), "pa")]
        oncls = ""
    tw = 1180 if (it.get("_qr") or not it.get("_src")) else 1500
    h.append(kicker(ctx, it.get("kicker"), MX, 470, 900, cls="k" + oncls))
    h.append(T(ctx, it["headline"], MX, 520, tw, 300, 150, 72, cls="h" + oncls, va="b", lh=1.06))
    if it.get("sub"):
        h.append(T(ctx, it["sub"], MX, 830, tw, 70, 40, 28, cls="p" + oncls, va="t"))
    h.append(_cta(ctx, it, MX, 900 - (0 if it.get("sub") else 60)))
    if it.get("_qr"):
        h.append(f'<div class="bx qrcard" style="left:1440px;top:560px;width:360px;height:360px"><div class="qrbox">{it["_qr"]}</div></div>')
    return {"html": "".join(h), "role": "cover", "room": True}


def hero_split(ctx, it):
    d = ctx.dz
    if it.get("_src"):
        h = [f'<div class="bx imgfull" style="left:960px;top:0;width:960px;height:{H}px"><img src="{it["_src"]}" alt="{esc(it.get("alt", it.get("headline", "")))}"></div>']
    else:
        h = [rect(960, 0, 960, H, "panel"), box(960, 0, 960, H, art.abstract(d, 960, H, ctx.idx), "pa")]
    h.append(kicker(ctx, it.get("kicker"), MX, 190, 720))
    h.append(T(ctx, it["headline"], MX, 250, 760, 400, 128, 64, cls="h", va="t", lh=1.08))
    if it.get("sub"):
        h.append(T(ctx, it["sub"], MX, 670, 760, 110, 40, 28, cls="p mu", va="t", lh=1.3))
    h.append(_cta(ctx, it, MX, 800, 480))
    if it.get("_qr"):
        h.append(f'<div class="bx qrcard" style="left:640px;top:760px;width:220px;height:220px"><div class="qrbox">{it["_qr"]}</div></div>')
    return {"html": "".join(h), "role": "cover", "room": True}


def _always(it):
    return True


def diagram_canvas(ctx, it):
    """Drawn figure (deck_diagram.svg) on a card; optional notes on the right."""
    import deck_diagram
    pub = ctx.dz.get("context") == "public"
    hh = [_head(ctx, it)] if pub else [T(ctx, it.get("title", ""), MX, 96, CW, 130, 76, 48, cls="h", va="m", lh=1.14)]
    pts = it.get("points") or []
    if pts:
        w, h, x, y = 1080, 648, MX, 270
    else:
        w, h, x, y = 1150, 690, (W - 1150) // 2, 258
    hh.append(box(x, y, w, h, deck_diagram.svg(it, ctx.dz["colors"], w, h, ctx.floor, f"dg{ctx.idx}"), "dgm"))
    if pts:
        px, pw = x + w + 40, W - MX - (x + w + 40)
        rh = min(190, (h - 20 * (len(pts) - 1)) // len(pts))
        y0 = y + (h - (rh * len(pts) + 20 * (len(pts) - 1))) // 2
        for i, p in enumerate(pts):
            yy = y0 + i * (rh + 20)
            hh.append(rect(px, yy, pw, rh, "cd"))
            hh.append(rect(px, yy, 12, rh, "bar"))
            hh.append(T(ctx, p, px + 36, yy + 8, pw - 56, rh - 16, 40, 28, cls="p ct", va="m", lh=1.3))
    if it.get("caption"):
        hh.append(T(ctx, it["caption"], MX, y + h + 14, CW, 56, 32, 28, cls="p mu", va="m", align="center"))
    return {"html": "".join(hh), "role": "content", "room": True}


def register(REG: dict) -> None:
    REG.setdefault("title", [])
    if not any(v[0] == "gov" for v in REG["title"]):
        REG["title"].append(("gov", "editorial", title_gov, lambda it: it.get("_ctx") == "public"))
        REG["bullets"].append(("gov", "editorial", bullets_gov, lambda it: it.get("_ctx") == "public"))
        REG["bullets"].append(("govsplit", "split", bullets_govsplit, lambda it: it.get("_ctx") == "public"))
    REG["table"] = [("grid", "editorial", table_grid, _always)]
    REG["summary"] = [("box", "editorial", summary_box, _always)]
    REG["toc"] = [("list", "editorial", toc_list, _always)]
    REG["hero"] = [("full", "bigtype", hero_full, _always), ("split", "split", hero_split, _always)]
    REG["diagram"] = [("canvas", "split", diagram_canvas, _always)]


# ------------------------------------------------------------------- decorate: public header + 자료/주 line


def source_line(it: dict) -> str:
    parts = []
    if it.get("source"):
        parts.append(f"자료: {plain(str(it['source']))}")
    if it.get("footnote"):
        parts.append(f"주: {plain(str(it['footnote']))}")
    return "   ".join(parts)


def decorate(ctx, it: dict, res: dict, spec: dict) -> str:
    """Wrap + add context chrome. Returns the slide's inner html."""
    html = res["html"]
    pub = ctx.dz.get("context") == "public"
    src = source_line(it)
    content = res.get("role") == "content" or it["type"] not in ("title", "section", "closing", "hero")
    if not (pub or src):
        return html
    if not res.get("room") and (pub and content or src):
        # other layouts use the full stage: shrink them a little so the header / source line has room (text sizes stay >= floor in CSS px)
        ty = 64 if pub and content else 0
        html = f'<div class="bx ctxfit" style="left:0;top:0;width:{W}px;height:{H}px;transform:translateY({ty}px) scale(.86);transform-origin:50% 0">{html}</div>'
    extra = []
    if pub and content and it["type"] != "title":
        org = str(spec.get("org") or spec.get("agency") or "")
        sec = str(it.get("_section") or "")
        if sec:
            extra.append(T(ctx, sec, MX, 76, 1100, 40, 24, 24, cls="p ghead", va="m"))
        if org:
            extra.append(T(ctx, org, W - MX - 600, 76, 600, 40, 24, 24, cls="p ghead", va="m", align="right"))
        extra.append(rect(MX, 124, CW, 2, "rule"))
    if src:
        extra.append(T(ctx, src, MX, 950, CW, 52, 24, 24, cls="p src", va="m"))
    return html + "".join(extra)
