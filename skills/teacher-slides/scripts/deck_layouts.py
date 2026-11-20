# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Layout generators: one function per (slide type, variant). Each returns {"html", "role"} for a 1920x1080 stage.

Rules baked in (owner's bar: restraint): ONE focal element per slide, 120px side margins on an 8-pt grid, generous whitespace,
one accent colour, text first. Variants differ in COMPOSITION (asymmetric split, full-bleed type, bento cards, editorial rows ...),
not in colour. Families (split, bigtype, bento, editorial, stack, poster, center) are what a style's `prefer` weights choose between.
Every function takes (ctx, it) where `it` is the normalised slide dict.
"""
from __future__ import annotations

import json
import re

import deck_art as art
from deck_kit import Ctx, T, box, esc, fit, kicker, plain, rect, rich, text_w

MX = 120
W, H = 1920, 1080
CW = W - 2 * MX  # 1680


def grp(ctx: Ctx, inner: str, step: int | None = None, cls: str = "") -> str:
    """Wrap pieces that must appear together (card + its text) in one build step."""
    if step == 0:
        return f'<div class="bx grp {cls}" style="left:0;top:0;width:{W}px;height:{H}px">{inner}</div>'
    b = ctx.b(step)
    bc = " b" if b else ""
    return f'<div class="bx grp{bc} {cls}"{b} style="left:0;top:0;width:{W}px;height:{H}px">{inner}</div>'


def _u(url: str) -> str:
    """URL for display: allow line breaks after slashes (zero-width space)."""
    return str(url).replace("/", "/​")


def num(n: int) -> str:
    return f"{n:02d}"


def pad_items(items: list, n: int) -> list:
    return items[:n]


def head(ctx: Ctx, it: dict, x=MX, y=96, w=CW, h=150, mx=84, mn=56, kick=True, va="t") -> str:
    k = kicker(ctx, it.get("kicker"), x, y) if kick and it.get("kicker") else ""
    ty = y + (56 if k else 0)
    return k + T(ctx, it.get("title", ""), x, ty, w, h - (56 if k else 0), mx, mn, cls="h", va=va, lh=1.14)


def cardrect(x, y, w, h, extra: str = "", cls: str = "") -> str:
    return rect(x, y, w, h, "cd " + cls, extra)


# ===================================================== cover
def cover_left(ctx, it):
    d = ctx.dz
    h = [rect(1280, 0, 640, H, "panel"), box(1280, 0, 640, H, art.abstract(d, 640, H, ctx.idx), "pa"),
         rect(MX, 200, 96, 8, "bar"), kicker(ctx, it.get("kicker"), MX, 124, 1000),
         T(ctx, it["title"], MX, 240, 1060, 480, 148, 72, cls="h", va="m", lh=1.1)]
    if it.get("subtitle"):
        h.append(T(ctx, it["subtitle"], MX, 740, 1060, 130, 44, cls="p mu", va="t"))
    if it.get("meta"):
        h.append(T(ctx, it["meta"], MX, 920, 1060, 60, 28, cls="p mu small", va="b"))
    if it.get("shapes"):  # the cover drawing sits on the right panel
        import deck_diagram
        h.append(box(1290, 351, 620, 372, deck_diagram.svg(it, d["colors"], 620, 372, ctx.floor, f"cv{ctx.idx}"), "dgm"))
    return {"html": "".join(h), "role": "cover"}


def cover_bottom(ctx, it):
    h = [kicker(ctx, it.get("kicker"), MX, 96, 1200),
         T(ctx, it["title"], MX, 190, CW, 600, 176, 80, cls="h", va="b", lh=1.06),
         rect(MX, 836, CW, 2, "rule")]
    if it.get("subtitle"):
        h.append(T(ctx, it["subtitle"], MX, 870, 1100, 110, 40, cls="p mu", va="t"))
    if it.get("meta"):
        h.append(T(ctx, it["meta"], 1240, 884, 560, 100, 28, cls="p mu small", va="t", align="right"))
    return {"html": "".join(h), "role": "cover"}


def cover_center(ctx, it):
    h = [kicker(ctx, it.get("kicker"), 240, 250, 1440, "k kc"),
         T(ctx, it["title"], 240, 310, 1440, 380, 132, 72, cls="h", va="m", lh=1.1, align="center"),
         rect(912, 720, 96, 8, "bar")]
    if it.get("subtitle"):
        h.append(T(ctx, it["subtitle"], 360, 770, 1200, 110, 40, cls="p mu", va="t", align="center"))
    if it.get("meta"):
        h.append(T(ctx, it["meta"], 360, 930, 1200, 50, 28, cls="p mu small", va="b", align="center"))
    return {"html": "".join(h), "role": "cover"}


def cover_poster(ctx, it):
    h = [rect(0, 0, 72, H, "stripe"), kicker(ctx, it.get("kicker"), 216, 140, 1200),
         T(ctx, it["title"], 216, 200, 1500, 560, 168, 80, cls="h", va="m", lh=1.06)]
    if it.get("subtitle"):
        h.append(T(ctx, it["subtitle"], 216, 790, 1200, 110, 44, cls="p mu", va="t"))
    if it.get("meta"):
        h.append(T(ctx, it["meta"], 216, 930, 1200, 50, 28, cls="p mu small", va="b"))
    return {"html": "".join(h), "role": "cover"}


# ===================================================== section
def section_num(ctx, it):
    n = it.get("num") or num(it.get("_secno", 1))
    h = [f'<div class="bx deco gnum" aria-hidden="true" style="left:{MX - 20}px;top:170px;width:720px;height:640px;font-size:520px">{esc(n)}</div>',
         T(ctx, it["title"], 840, 280, 960, 400, 104, 60, cls="h", va="b", lh=1.12),
         rect(840, 708, 96, 8, "bar")]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], 840, 748, 900, 140, 40, cls="p mu", va="t"))
    return {"html": "".join(h), "role": "section"}


def section_band(ctx, it):
    n = it.get("num") or num(it.get("_secno", 1))
    h = [rect(0, 320, W, 400, "band"), kicker(ctx, "PART " + n, MX, 240, 800),
         T(ctx, it["title"], MX, 340, CW, 360, 120, 64, cls="h on-band", va="m", lh=1.1)]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], MX, 770, 1300, 140, 40, cls="p mu", va="t"))
    return {"html": "".join(h), "role": "section"}


def section_center(ctx, it):
    n = it.get("num") or num(it.get("_secno", 1))
    h = [kicker(ctx, n, 240, 270, 1440, "k kc big"),
         T(ctx, it["title"], 240, 350, 1440, 330, 112, 60, cls="h", va="m", lh=1.12, align="center"),
         rect(912, 710, 96, 8, "bar")]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], 360, 760, 1200, 130, 40, cls="p mu", va="t", align="center"))
    return {"html": "".join(h), "role": "section"}


# ===================================================== bullets
def bullets_rows(ctx, it):
    items = it["items"]
    n = len(items)
    h = [head(ctx, it, MX, 96, 640, 700, 80, 52)]
    rh = min(160, 800 // n)
    y0 = 140 + (800 - rh * n) // 2
    for i, t in enumerate(items):
        y = y0 + i * rh
        inner = rect(860, y, 940, 2, "rule") + f'<div class="bx idx" style="left:860px;top:{y + 8}px;width:90px;height:{rh - 8}px;font-size:36px">{num(i + 1)}</div>'
        inner += T(ctx, t, 970, y + 8, 830, rh - 8, 44, 30, cls="p", va="m", lh=1.3)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def bullets_cards(ctx, it):
    items = it["items"]
    n = len(items)
    h = [head(ctx, it, MX, 96, CW, 190, 80, 52)]
    cols = n if n <= 3 else (2 if n == 4 else 3)
    rows = -(-n // cols)
    gap = 32
    cw = (CW - gap * (cols - 1)) / cols
    top, bh = 340, 984 - 340
    ch = (bh - gap * (rows - 1)) / rows
    for i, t in enumerate(items):
        c, r_ = i % cols, i // cols
        x, y = MX + c * (cw + gap), top + r_ * (ch + gap)
        inner = cardrect(x, y, cw, ch) + f'<div class="bx idx" style="left:{x + 40:.0f}px;top:{y + 32:.0f}px;width:200px;height:56px;font-size:32px">{num(i + 1)}</div>'
        inner += T(ctx, t, x + 40, y + 96, cw - 80, ch - 128, 44 if rows == 1 else 38, 30, cls="p ct", va="t", lh=1.3)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def bullets_lead(ctx, it):
    items = it["items"]
    h = [head(ctx, it, MX, 96, CW, 150, 72, 52), rect(MX, 330, 8, 220, "bar-v"),
         grp(ctx, T(ctx, items[0], MX + 48, 330, 1500, 220, 64, 36, cls="p lead", va="m", lh=1.25))]
    rest = items[1:4]
    n = len(rest)
    gap = 48
    cw = (CW - gap * (n - 1)) / n
    for i, t in enumerate(rest):
        x = MX + i * (cw + gap)
        inner = rect(x, 660, cw, 2, "rule") + T(ctx, t, x, 686, cw, 280, 38, 30, cls="p", va="t", lh=1.3)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def bullets_stack(ctx, it):
    items = it["items"]
    n = len(items)
    h = [head(ctx, it, MX, 96, 1400, 190, 80, 52)]
    rh = min(150, 640 // n)
    y0 = 340
    for i, t in enumerate(items):
        y = y0 + i * rh
        inner = f'<div class="bx dot" aria-hidden="true" style="left:{MX}px;top:{y + rh / 2 - 14:.0f}px;width:28px;height:28px"></div>'
        inner += T(ctx, t, MX + 72, y, 1500, rh, 52 if n <= 4 else 44, 32, cls="p", va="m", lh=1.25)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


# ===================================================== compare
def _side_items(side: dict, rows: list, key: str) -> list:
    if side.get("items"):
        return side["items"]
    return [r.get(key, "") for r in rows]


def compare_panels(ctx, it):
    a, b_, rows = it["a"], it["b"], it.get("rows") or []
    h = [head(ctx, it, MX, 96, CW, 150, 76, 52)]
    for si, (side, x, key) in enumerate(((a, MX, "a"), (b_, MX + 860, "b"))):
        items = _side_items(side, rows, key)[:5]
        inner = cardrect(x, 300, 820, 684, "", "alt" if si else "")
        inner += T(ctx, side.get("label", ""), x + 48, 336, 724, 80, 48, 32, cls="h cl", va="m")
        inner += rect(x + 48, 432, 724, 2, "rule")
        ih = 520 // max(1, len(items))
        for i, t in enumerate(items):
            inner += T(ctx, t, x + 48, 452 + i * ih, 724, min(ih, 130), 38, 30, cls="p ct", va="m", lh=1.25)
        h.append(grp(ctx, inner))
    h.append(f'<div class="bx chip" aria-hidden="true" style="left:{W / 2 - 40:.0f}px;top:{300 + 342 - 40:.0f}px;width:80px;height:80px;font-size:28px">VS</div>')
    return {"html": "".join(h), "role": "content"}


def compare_table(ctx, it):
    a, b_, rows = it["a"], it["b"], it.get("rows") or []
    if not rows:
        ai, bi = _side_items(a, rows, "a"), _side_items(b_, rows, "b")
        rows = [{"k": "", "a": x, "b": y} for x, y in zip(ai, bi)]
    rows = rows[:5]
    h = [head(ctx, it, MX, 96, CW, 150, 76, 52)]
    kx, ax, bx_, cw = MX, MX + 360, MX + 360 + 660, 640
    h.append(T(ctx, a.get("label", ""), ax, 290, cw, 70, 44, 30, cls="h cl", va="m"))
    h.append(T(ctx, b_.get("label", ""), bx_, 290, cw, 70, 44, 30, cls="h cl acc", va="m"))
    h.append(rect(MX, 370, CW, 4, "rule strong"))
    rh = min(150, 600 // len(rows))
    for i, r_ in enumerate(rows):
        y = 380 + i * rh
        inner = rect(MX, y + rh - 2, CW, 2, "rule")
        inner += T(ctx, r_.get("k", ""), kx, y, 320, rh, 32, 28, cls="p mu", va="m")
        inner += T(ctx, r_.get("a", ""), ax, y, cw, rh, 38, 28, cls="p", va="m", lh=1.25)
        inner += T(ctx, r_.get("b", ""), bx_, y, cw, rh, 38, 28, cls="p strongc", va="m", lh=1.25)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def compare_versus(ctx, it):
    a, b_, rows = it["a"], it["b"], it.get("rows") or []
    h = [rect(0, 260, 960, 820, "half-a"), rect(960, 260, 960, 820, "half-b"), T(ctx, it.get("title", ""), MX, 80, CW, 150, 64, 40, cls="h", va="m", lh=1.14)]
    for si, (side, x, key) in enumerate(((a, MX, "a"), (b_, 1020, "b"))):
        items = _side_items(side, rows, key)[:4]
        cls = "on-b" if si else ""
        inner = T(ctx, side.get("label", ""), x, 300, 740, 110, 64, 36, cls=f"h {cls}", va="m")
        ih = 520 // max(1, len(items))
        for i, t in enumerate(items):
            inner += rect(x, 440 + i * ih, 740, 2, f"rule {cls}") + T(ctx, t, x, 450 + i * ih, 740, min(ih - 10, 120), 38, 30, cls=f"p {cls}", va="m", lh=1.25)
        h.append(grp(ctx, inner))
    h.append(f'<div class="bx chip" aria-hidden="true" style="left:{W / 2 - 40:.0f}px;top:{260 + 410 - 40}px;width:80px;height:80px;font-size:28px">VS</div>')
    return {"html": "".join(h), "role": "content"}


# ===================================================== steps
def steps_row(ctx, it):
    st = it["steps"]
    n = len(st)
    h = [head(ctx, it, MX, 96, CW, 190, 80, 52)]
    gap = 40
    cw = (CW - gap * (n - 1)) / n
    ly = 400
    h.append(rect(MX, ly + 39, CW, 4, "rule strong"))
    for i, s in enumerate(st):
        x = MX + i * (cw + gap)
        inner = f'<div class="bx disc" style="left:{x:.0f}px;top:{ly}px;width:82px;height:82px;font-size:36px">{i + 1}</div>'
        inner += T(ctx, s.get("title", ""), x, ly + 120, cw, 130, 44, 30, cls="h st", va="t", lh=1.2)
        if s.get("text"):
            inner += T(ctx, s["text"], x, ly + 260, cw, 300, 34, 28, cls="p mu", va="t", lh=1.35)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def steps_stair(ctx, it):
    st = it["steps"]
    n = len(st)
    h = [head(ctx, it, MX, 96, 900, 300, 76, 52)]
    gap = 24
    cw = (CW - gap * (n - 1)) / n
    for i, s in enumerate(st):
        x = MX + i * (cw + gap)
        top = 984 - (350 + i * (440 // max(1, n - 1)) * 0.78)
        hh = 984 - top
        inner = cardrect(x, top, cw, hh, "", "step" + (" last" if i == n - 1 else ""))
        inner += f'<div class="bx idx" style="left:{x + 32:.0f}px;top:{top + 24:.0f}px;width:160px;height:48px;font-size:32px">{num(i + 1)}</div>'
        inner += T(ctx, s.get("title", ""), x + 32, top + 80, cw - 64, 110, 40, 28, cls="h st ct", va="t", lh=1.2)
        if s.get("text"):
            inner += T(ctx, s["text"], x + 32, top + 196, cw - 64, max(60, hh - 220), 30, 28, cls="p ct", va="t", lh=1.3)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def steps_list(ctx, it):
    st = it["steps"][:6]
    n = len(st)
    h = [head(ctx, it, MX, 96, 600, 700, 76, 52)]
    two = n > 4
    rows = -(-n // 2) if two else n
    rh = min(190, 800 // rows)
    colw = 480 if two else 900
    for i, s in enumerate(st):
        c, r_ = (i // rows, i % rows) if two else (0, i)
        x = 800 + c * (colw + 40) if two else 860
        y = 140 + (800 - rh * rows) // 2 + r_ * rh
        inner = rect(x, y, colw if two else 940, 2, "rule")
        inner += f'<div class="bx bignum" style="left:{x}px;top:{y + 10}px;width:110px;height:{rh - 12}px;font-size:64px">{i + 1}</div>'
        inner += T(ctx, s.get("title", ""), x + 120, y + 14, (colw if two else 940) - 120, 60 if s.get("text") else rh - 16, 40, 30, cls="h st", va="m" if not s.get("text") else "b", lh=1.15)
        if s.get("text"):
            inner += T(ctx, s["text"], x + 120, y + 76, (colw if two else 940) - 120, rh - 86, 32, 28, cls="p mu", va="t", lh=1.3)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


# ===================================================== bignumber
def _numbox(ctx, value, unit, x, y, w, h, mx, cls="big", align=""):
    s = fit(str(value), w * (0.78 if unit else 0.97), h, mx, 80, 1.0)
    us = max(ctx.floor, int(s * 0.34))
    u = f'<span class="unit" style="font-size:{us}px">{esc(unit)}</span>' if unit else ""
    al = f"text-align:{align};" if align else ""
    return (f'<div class="bx {cls} va-m" data-fit="{mx},80" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;font-size:{s}px;line-height:1;{al}">'
            f'<div class="tx">{esc(value)}{u}</div></div>')


def bignumber_giant(ctx, it):
    h = [kicker(ctx, it.get("kicker") or it.get("title"), MX, 140, 1200),
         _numbox(ctx, it["value"], it.get("unit", ""), MX, 220, CW, 520, 440),
         rect(MX, 770, 96, 8, "bar")]
    if it.get("caption"):
        h.append(T(ctx, it["caption"], MX, 810, 1300, 170, 48, 32, cls="p", va="t", lh=1.3))
    return {"html": "".join(h), "role": "content"}


def bignumber_split(ctx, it):
    h = [rect(0, 0, 1040, H, "panel"), kicker(ctx, it.get("kicker") or it.get("title"), MX, 140, 800, "k on-panel"),
         _numbox(ctx, it["value"], it.get("unit", ""), MX, 260, 820, 560, 320, "big on-panel")]
    if it.get("caption"):
        h.append(T(ctx, it["caption"], 1160, 240, 640, 600, 52, 32, cls="p", va="m", lh=1.35))
    return {"html": "".join(h), "role": "content"}


def bignumber_center(ctx, it):
    h = [kicker(ctx, it.get("kicker") or it.get("title"), 240, 150, 1440, "k kc"),
         _numbox(ctx, it["value"], it.get("unit", ""), 160, 230, 1600, 480, 400, "big", "center"),
         rect(912, 740, 96, 8, "bar")]
    if it.get("caption"):
        h.append(T(ctx, it["caption"], 360, 790, 1200, 190, 48, 32, cls="p", va="t", lh=1.3, align="center"))
    return {"html": "".join(h), "role": "content"}


# ===================================================== bignumbers (2-3 side by side)
def bignumbers_duo(ctx, it):
    its = it["items"][:2]
    h = [head(ctx, it, MX, 96, CW, 150, 72, 52)]
    for i, m in enumerate(its):
        x = MX + i * 900
        inner = _numbox(ctx, m["value"], m.get("unit", ""), x, 300, 780, 380, 280, "big" + (" acc" if i else ""))
        inner += rect(x, 700, 96, 8, "bar" if i == 0 else "bar alt")
        inner += T(ctx, m.get("caption", ""), x, 740, 780, 230, 44, 30, cls="p", va="t", lh=1.3)
        h.append(grp(ctx, inner))
    h.append(rect(959, 300, 2, 680, "rule"))
    h.append(f'<div class="bx chip" aria-hidden="true" style="left:{W / 2 - 40:.0f}px;top:{H / 2 - 40 + 40:.0f}px;width:80px;height:80px;font-size:28px">VS</div>')
    return {"html": "".join(h), "role": "content"}


def bignumbers_cols(ctx, it):
    its = it["items"][:3]
    n = len(its)
    gap = 56
    cw = (CW - gap * (n - 1)) / n
    h = [head(ctx, it, MX, 96, CW, 150, 72, 52)]
    for i, m in enumerate(its):
        x = MX + i * (cw + gap)
        inner = rect(x, 300, cw, 6, "rule strong") + _numbox(ctx, m["value"], m.get("unit", ""), x, 340, cw, 340, 240, "big")
        inner += T(ctx, m.get("caption", ""), x, 700, cw, 270, 40, 30, cls="p", va="t", lh=1.3)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def _numval(v):
    m = re.search(r"-?\d[\d,]*\.?\d*", str(v))
    return float(m.group(0).replace(",", "")) if m else None


def bignumbers_bars(ctx, it):
    its = it["items"][:3]
    vals = [_numval(m["value"]) or 0 for m in its]
    top = max(vals) or 1
    h = [head(ctx, it, MX, 96, CW, 150, 72, 52)]
    rh = min(230, 660 // len(its))
    for i, m in enumerate(its):
        y = 300 + i * (rh + 8)
        bw = 760 * vals[i] / top
        inner = rect(MX, y + rh - 20, 1000, 2, "rule")
        inner += _numbox(ctx, m["value"], m.get("unit", ""), MX, y, 640, rh - 60, 150, "big" + (" acc" if i == 0 else ""))
        inner += rect(MX + 700, y + (rh - 60) / 2 - 20, bw, 40, "bar-h" + ("" if i == 0 else " alt"))
        inner += T(ctx, m.get("caption", ""), MX, y + rh - 56, 1000, 50, 32, 28, cls="p mu", va="m")
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


# ===================================================== quote
def quote_big(ctx, it):
    h = [f'<div class="bx deco qmark" aria-hidden="true" style="left:{MX}px;top:60px;width:400px;height:360px;font-size:420px">“</div>',
         T(ctx, it["text"], 240, 280, 1440, 520, 80, 44, cls="h q", va="m", lh=1.3)]
    if it.get("source"):
        h.append(rect(240, 842, 96, 6, "bar") + T(ctx, it["source"], 360, 820, 1200, 50, 32, cls="p mu", va="m"))
    return {"html": "".join(h), "role": "content"}


def quote_side(ctx, it):
    h = [rect(MX, 200, 12, 640, "bar-v"), T(ctx, it["text"], MX + 72, 200, 1400, 580, 76, 44, cls="h q", va="m", lh=1.3)]
    if it.get("source"):
        h.append(T(ctx, it["source"], MX + 72, 800, 1200, 50, 32, cls="p mu", va="m"))
    return {"html": "".join(h), "role": "content"}


def quote_center(ctx, it):
    h = [f'<div class="bx deco qmark kc" aria-hidden="true" style="left:760px;top:120px;width:400px;height:240px;font-size:300px;text-align:center">“</div>',
         T(ctx, it["text"], 260, 340, 1400, 420, 72, 44, cls="h q", va="m", lh=1.3, align="center")]
    if it.get("source"):
        h.append(T(ctx, it["source"], 360, 800, 1200, 50, 32, cls="p mu", va="m", align="center"))
    return {"html": "".join(h), "role": "content"}


# ===================================================== statement (one big sentence)
def statement_big(ctx, it):
    h = [kicker(ctx, it.get("kicker"), MX, 150, 1200), T(ctx, it["text"], MX, 210, 1160, 560, 124, 56, cls="h", va="m", lh=1.2), rect(MX, 810, 96, 8, "bar"),
         box(1400, 250, 400, 460, art.hero(ctx.dz, ["arc", "rings", "blocks"][(ctx.dz["seed"] + ctx.idx) % 3], it.get("_icons") or ["sparkles"], 400, 460, ctx.idx), "art")]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], MX, 840, 1300, 140, 40, cls="p mu", va="t", lh=1.35))
    return {"html": "".join(h), "role": "content"}


def statement_center(ctx, it):
    h = [kicker(ctx, it.get("kicker"), 240, 190, 1440, "k kc"), T(ctx, it["text"], 240, 250, 1440, 520, 108, 52, cls="h", va="m", lh=1.22, align="center"), rect(912, 800, 96, 8, "bar")]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], 360, 840, 1200, 140, 40, cls="p mu", va="t", align="center", lh=1.35))
    return {"html": "".join(h), "role": "content"}


def statement_split(ctx, it):
    h = [rect(0, 0, 40, H, "stripe"), kicker(ctx, it.get("kicker"), 200, 150, 900), T(ctx, it["text"], 200, 210, 1100, 600, 112, 52, cls="h", va="m", lh=1.2)]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], 1400, 260, 400, 560, 36, 28, cls="p mu", va="m", lh=1.4))
    return {"html": "".join(h), "role": "content"}


# ===================================================== illustration
def illu_right(ctx, it):
    kind = it.get("art") or ["rings", "blocks", "arc"][(ctx.dz["seed"] + ctx.idx) % 3]
    names = it.get("_icons") or ["sparkles"]
    h = [kicker(ctx, it.get("kicker"), MX, 200, 800), T(ctx, it.get("title", ""), MX, 256, 860, 380, 84, 52, cls="h", va="t", lh=1.14),
         rect(MX, 660, 96, 8, "bar")]
    if it.get("text"):
        h.append(T(ctx, it["text"], MX, 704, 820, 280, 40, 30, cls="p mu", va="t", lh=1.4))
    h.append(box(1000, 140, 800, 800, art.hero(ctx.dz, kind, names, 800, 800, ctx.idx), "art"))
    return {"html": "".join(h), "role": "content"}


def illu_left(ctx, it):
    kind = it.get("art") or ["arc", "rings", "blocks"][(ctx.dz["seed"] + ctx.idx) % 3]
    names = it.get("_icons") or ["sparkles"]
    h = [box(120, 140, 800, 800, art.hero(ctx.dz, kind, names, 800, 800, ctx.idx), "art"),
         kicker(ctx, it.get("kicker"), 1040, 200, 760), T(ctx, it.get("title", ""), 1040, 256, 760, 380, 80, 52, cls="h", va="t", lh=1.14),
         rect(1040, 660, 96, 8, "bar")]
    if it.get("text"):
        h.append(T(ctx, it["text"], 1040, 704, 760, 280, 40, 30, cls="p mu", va="t", lh=1.4))
    return {"html": "".join(h), "role": "content"}


# ===================================================== quiz
def _choices(ctx, it, x, y, w, rh, size=44, cols=1, gap=20):
    out = ""
    ch = it["choices"]
    ans = int(it.get("answer", 0))
    cw = (w - gap * (cols - 1)) / cols
    for i, t in enumerate(ch):
        c, r_ = i % cols, i // cols
        cx, cy = x + c * (cw + gap), y + r_ * (rh + gap)
        ok = " ok" if i == ans else ""
        inner = f'<div class="bx ch{ok}" style="left:{cx:.0f}px;top:{cy:.0f}px;width:{cw:.0f}px;height:{rh}px"></div>'
        inner += f'<div class="bx chl{ok}" aria-hidden="true" style="left:{cx + 24:.0f}px;top:{cy + (rh - 64) / 2:.0f}px;width:64px;height:64px;font-size:32px">{"ABCD"[i]}</div>'
        inner += T(ctx, t, cx + 112, cy + 8, cw - 136, rh - 16, size, 30, cls=f"p chx{ok}", va="m", lh=1.2)
        out += grp(ctx, inner, 0 if ctx.builds else None)
    return out


def _explain(ctx, it, x, y, w, h):
    if not it.get("explain"):
        return ""
    return f'<div class="bx ex b" data-b="1" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">' + T(ctx, "**정답** " + it["explain"], 0, 0, w - 28, h, 36, 28, cls="p", va="m", lh=1.3) + "</div>"


def quiz_list(ctx, it):
    n = len(it["choices"])
    rh = 100 if n > 3 else 112
    h = [kicker(ctx, it.get("kicker") or "QUIZ", MX, 96, 600), T(ctx, it["q"], MX, 150, CW, 210, 72, 44, cls="h", va="t", lh=1.2),
         _choices(ctx, it, MX, 390, 1100, rh, 44)]
    ctx.max_b = max(ctx.max_b, 1)
    h.append(_explain(ctx, it, 1280, 390, 520, 420))
    return {"html": "".join(h), "role": "content", "solve": 1}


def quiz_grid(ctx, it):
    n = len(it["choices"])
    h = [kicker(ctx, it.get("kicker") or "QUIZ", MX, 96, 600), T(ctx, it["q"], MX, 150, CW, 190, 72, 44, cls="h", va="t", lh=1.2),
         _choices(ctx, it, MX, 380, CW, 220 if n > 2 else 300, 40, 2, 24)]
    ctx.max_b = max(ctx.max_b, 1)
    h.append(_explain(ctx, it, MX, 880, CW, 100))
    return {"html": "".join(h), "role": "content", "solve": 1}


def quiz_side(ctx, it):
    h = [kicker(ctx, it.get("kicker") or "QUIZ", MX, 140, 600), T(ctx, it["q"], MX, 200, 700, 520, 68, 44, cls="h", va="t", lh=1.2),
         _choices(ctx, it, 920, 150, 880, 150 if len(it["choices"]) <= 4 else 120, 40)]
    ctx.max_b = max(ctx.max_b, 1)
    h.append(_explain(ctx, it, MX, 760, 700, 220))
    return {"html": "".join(h), "role": "content", "solve": 1}


# ===================================================== timeline
def timeline_rail(ctx, it):
    ev = it["events"][:6]
    n = len(ev)
    h = [head(ctx, it, MX, 96, CW, 190, 80, 52)]
    gap = 32
    cw = (CW - gap * (n - 1)) / n
    ly = 470
    h.append(rect(MX, ly - 2, CW, 4, "rule strong"))
    for i, e in enumerate(ev):
        x = MX + i * (cw + gap)
        inner = T(ctx, e.get("when", ""), x, ly - 110, cw, 70, 48, 32, cls="h acc", va="b", lh=1.1)
        inner += f'<div class="bx dotb" aria-hidden="true" style="left:{x:.0f}px;top:{ly - 16}px;width:32px;height:32px"></div>'
        inner += T(ctx, e.get("title", ""), x, ly + 44, cw, 120, 36, 28, cls="h st", va="t", lh=1.2)
        if e.get("text"):
            inner += T(ctx, e["text"], x, ly + 176, cw, 330, 30, 28, cls="p mu", va="t", lh=1.35)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


def timeline_vertical(ctx, it):
    ev = it["events"][:6]
    n = len(ev)
    h = [head(ctx, it, MX, 96, 560, 700, 76, 52), rect(1010, 120, 4, 840, "rule strong")]
    rh = min(150, 840 // n)
    y0 = 120 + (840 - rh * n) // 2
    for i, e in enumerate(ev):
        y = y0 + i * rh
        inner = T(ctx, e.get("when", ""), 700, y, 270, rh, 44, 30, cls="h acc", va="m", align="right", lh=1.1)
        inner += f'<div class="bx dotb" aria-hidden="true" style="left:1000px;top:{y + rh / 2 - 12:.0f}px;width:24px;height:24px"></div>'
        inner += T(ctx, e.get("title", ""), 1070, y + 4, 730, 58 if e.get("text") else rh - 8, 40, 30, cls="h st", va="b" if e.get("text") else "m", lh=1.1)
        if e.get("text"):
            inner += T(ctx, e["text"], 1070, y + 64, 730, rh - 70, 30, 28, cls="p mu", va="t", lh=1.3)
        h.append(grp(ctx, inner))
    return {"html": "".join(h), "role": "content"}


# ===================================================== chart / math
def _chart_cfg(it) -> str:
    return esc(json.dumps({"kind": it.get("kind", "bar"), "labels": it["labels"], "series": it["series"], "unit": it.get("unit", "")}, ensure_ascii=False))


def chart_side(ctx, it):
    h = [head(ctx, it, MX, 96, CW, 190, 76, 52),
         f'<div class="bx cd chartbox b" data-b="1" style="left:{MX}px;top:310px;width:1060px;height:674px"><canvas data-cfg="{_chart_cfg(it)}" width="1012" height="626"></canvas></div>']
    ctx.max_b = max(ctx.max_b, 1)
    if it.get("takeaway"):
        h.append(rect(1280, 330, 8, 240, "bar-v") + T(ctx, it["takeaway"], 1320, 310, 480, 500, 48, 30, cls="h q", va="t", lh=1.3, step=2))
    return {"html": "".join(h), "role": "content"}


def chart_full(ctx, it):
    h = [head(ctx, it, MX, 96, CW, 150, 72, 52),
         f'<div class="bx chartbox plain" style="left:{MX}px;top:290px;width:{CW}px;height:{"560" if it.get("takeaway") else "694"}px"><canvas data-cfg="{_chart_cfg(it)}" width="{CW}" height="{"560" if it.get("takeaway") else "694"}"></canvas></div>']
    if it.get("takeaway"):
        h.append(T(ctx, it["takeaway"], MX, 880, CW, 100, 40, 28, cls="p", va="m", step=1))
        ctx.max_b = max(ctx.max_b, 1)
    return {"html": "".join(h), "role": "content"}


def math_center(ctx, it):
    h = [head(ctx, it, MX, 96, CW, 150, 72, 52),
         box(MX, 300, CW, 380, f'<div class="tex" data-tex="{esc(it["tex"])}"></div>', "cd texbox")]
    if it.get("text"):
        h.append(T(ctx, it["text"], MX, 720, CW, 240, 40, 30, cls="p mu", va="t", lh=1.4, step=1))
        ctx.max_b = max(ctx.max_b, 1)
    return {"html": "".join(h), "role": "content"}


def math_split(ctx, it):
    h = [head(ctx, it, MX, 96, 600, 700, 76, 52),
         box(780, 180, 1020, 560, f'<div class="tex" data-tex="{esc(it["tex"])}"></div>', "cd texbox")]
    if it.get("text"):
        h.append(T(ctx, it["text"], 780, 780, 1020, 200, 38, 28, cls="p mu", va="t", lh=1.4, step=1))
        ctx.max_b = max(ctx.max_b, 1)
    return {"html": "".join(h), "role": "content"}


# ===================================================== timer
def _timer_ui(ctx, x, y, w, cls_extra=""):
    btn = lambda act, label, ex="": f'<button class="tbtn {ex}" data-act="{act}" type="button">{label}</button>'
    return f'<div class="bx tctl" style="left:{x}px;top:{y}px;width:{w}px;height:96px">{btn("toggle", "시작", "main")}{btn("reset", "처음으로")}{btn("minus", "−1분")}{btn("plus", "+1분")}</div>'


def timer_big(ctx, it):
    mins = int(it.get("minutes", 5))
    h = [kicker(ctx, it.get("kicker") or "TIMER", MX, 130, 800), T(ctx, it.get("title", ""), MX, 186, CW, 120, 64, 40, cls="h", va="m"),
         f'<div class="bx tdisp big" data-min="{mins}" style="left:{MX}px;top:330px;width:{CW}px;height:400px;font-size:360px;line-height:1">{mins:02d}:00</div>',
         f'<div class="bx tbar" aria-hidden="true" style="left:{MX}px;top:760px;width:{CW}px;height:16px"><i></i></div>',
         _timer_ui(ctx, MX, 840, 1100)]
    return {"html": "".join(h), "role": "content", "timer": True}


def timer_ring(ctx, it):
    mins = int(it.get("minutes", 5))
    R = 300
    c = 2 * 3.14159265 * R
    ring = (f'<svg class="bx tring" aria-hidden="true" viewBox="0 0 700 700" style="left:1000px;top:190px;width:700px;height:700px"><circle cx="350" cy="350" r="{R}" class="trk"/>'
            f'<circle cx="350" cy="350" r="{R}" class="tprog" stroke-dasharray="{c:.1f}" stroke-dashoffset="0" transform="rotate(-90 350 350)"/></svg>')
    h = [kicker(ctx, it.get("kicker") or "TIMER", MX, 250, 800), T(ctx, it.get("title", ""), MX, 306, 800, 360, 80, 48, cls="h", va="t", lh=1.15), ring,
         f'<div class="bx tdisp" data-min="{mins}" data-circ="{c:.1f}" style="left:1000px;top:420px;width:700px;height:260px;font-size:170px;line-height:1;text-align:center">{mins:02d}:00</div>',
         _timer_ui(ctx, MX, 720, 1100)]
    return {"html": "".join(h), "role": "content", "timer": True}


# ===================================================== qr
def qr_split(ctx, it):
    h = [kicker(ctx, it.get("kicker"), MX, 200, 800), T(ctx, it.get("title", ""), MX, 256, 900, 300, 84, 52, cls="h", va="t", lh=1.14),
         T(ctx, _u(it["url"]), MX, 600, 900, 130, 48, 28, cls="p urltxt", va="m", lh=1.2)]
    if it.get("caption"):
        h.append(T(ctx, it["caption"], MX, 750, 880, 200, 36, 28, cls="p mu", va="t", lh=1.35))
    h.append(f'<div class="bx qrcard" style="left:1100px;top:170px;width:700px;height:740px"><div class="qrbox">{it["_qr"]}</div></div>')
    return {"html": "".join(h), "role": "content"}


def qr_center(ctx, it):
    h = [T(ctx, it.get("title", ""), 240, 70, 1440, 130, 68, 44, cls="h", va="m", align="center", lh=1.1),
         f'<div class="bx qrcard" style="left:660px;top:220px;width:600px;height:600px"><div class="qrbox">{it["_qr"]}</div></div>',
         T(ctx, _u(it["url"]), 240, 850, 1440, 80, 44, 28, cls="p urltxt", va="m", align="center")]
    if it.get("caption"):
        h.append(T(ctx, it["caption"], 360, 930, 1200, 60, 32, 28, cls="p mu", va="m", align="center"))
    return {"html": "".join(h), "role": "content"}


# ===================================================== image / video
def image_full(ctx, it):
    h = [f'<div class="bx imgfull" style="left:0;top:0;width:{W}px;height:{H}px"><img src="{it["_src"]}" alt="{esc(it.get("alt", it.get("title", "")))}"></div>', rect(0, 700, W, 380, "scrim")]
    if it.get("title"):
        h.append(T(ctx, it["title"], MX, 780, 1500, 140, 76, 44, cls="h on-img", va="b", lh=1.12))
    if it.get("caption"):
        h.append(T(ctx, it["caption"], MX, 930, 1500, 56, 32, 28, cls="p on-img", va="m"))
    return {"html": "".join(h), "role": "content"}


def image_frame(ctx, it):
    h = [f'<div class="bx imgframe" style="left:{MX}px;top:120px;width:1100px;height:840px"><img src="{it["_src"]}" alt="{esc(it.get("alt", it.get("title", "")))}"></div>',
         kicker(ctx, it.get("kicker"), 1300, 180, 500), T(ctx, it.get("title", ""), 1300, 236, 500, 420, 56, 36, cls="h", va="t", lh=1.15),
         rect(1300, 680, 96, 8, "bar")]
    if it.get("caption"):
        h.append(T(ctx, it["caption"], 1300, 716, 500, 240, 32, 28, cls="p mu", va="t", lh=1.4))
    return {"html": "".join(h), "role": "content"}


def image_split(ctx, it):
    h = [f'<div class="bx imgfull" style="left:900px;top:0;width:1020px;height:{H}px"><img src="{it["_src"]}" alt="{esc(it.get("alt", it.get("title", "")))}"></div>',
         kicker(ctx, it.get("kicker"), MX, 260, 700), T(ctx, it.get("title", ""), MX, 316, 700, 380, 76, 44, cls="h", va="t", lh=1.15), rect(MX, 720, 96, 8, "bar")]
    if it.get("caption"):
        h.append(T(ctx, it["caption"], MX, 756, 700, 220, 34, 28, cls="p mu", va="t", lh=1.4))
    return {"html": "".join(h), "role": "content"}


def video_frame(ctx, it):
    if it.get("_src"):
        media = f'<video controls preload="metadata" src="{it["_src"]}"></video>'
    else:
        media = (f'<div class="vopen"><div class="vname">{esc(it.get("_name", ""))}</div>'
                 f'<a class="vbtn" href="{esc(it.get("_href", "#"))}" target="_blank" rel="noopener">영상 열기</a>'
                 f'<div class="vhint">크기가 커서 파일에 넣지 않았어요. 버튼이 안 열리면 파일을 더블클릭하세요.</div></div>')
    h = [head(ctx, it, MX, 96, CW, 130, 64, 44), f'<div class="bx videobox" style="left:{MX}px;top:260px;width:{CW}px;height:724px">{media}</div>']
    return {"html": "".join(h), "role": "content"}


# ===================================================== closing
def closing_big(ctx, it):
    nx = it.get("next", [])[:4]
    h = [kicker(ctx, it.get("kicker"), MX, 150, 800), T(ctx, it["title"], MX, 210, 1100, 360, 190, 80, cls="h", va="m", lh=1.05), rect(MX, 610, 96, 8, "bar"),
         box(1340, 110, 460, 520, art.hero(ctx.dz, ["rings", "arc", "blocks"][(ctx.dz["seed"] + ctx.idx) % 3], it.get("_icons") or ["sparkles"], 460, 520, ctx.idx), "art")]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], MX, 640, 1100, 100, 40, cls="p mu", va="t"))
    if nx:
        gap = 40
        cw = (CW - gap * (len(nx) - 1)) / len(nx)
        for i, t in enumerate(nx):
            x = MX + i * (cw + gap)
            h.append(grp(ctx, rect(x, 780, cw, 2, "rule") + T(ctx, t, x, 800, cw, 180, 34, 28, cls="p", va="t", lh=1.3)))
    return {"html": "".join(h), "role": "cover"}


def closing_split(ctx, it):
    nx = it.get("next", [])[:4]
    has_qr = bool(it.get("_qr"))
    left_w = 960 if has_qr else 1500
    h = [kicker(ctx, it.get("kicker"), MX, 150, 800), T(ctx, it["title"], MX, 210, left_w, 330, 150, 72, cls="h", va="m", lh=1.08), rect(MX, 570, 96, 8, "bar")]
    if it.get("sub"):
        h.append(T(ctx, it["sub"], MX, 600, left_w, 100, 40, cls="p mu", va="t"))
    ny = 740
    for i, t in enumerate(nx[:3]):
        h.append(grp(ctx, T(ctx, t, MX, ny + i * 82, left_w, 70, 34, 28, cls="p", va="m", lh=1.2)))
    if has_qr:
        h.append(f'<div class="bx qrcard" style="left:1200px;top:180px;width:600px;height:600px"><div class="qrbox">{it["_qr"]}</div></div>')
        if it.get("url"):
            h.append(T(ctx, _u(it["url"]), 1200, 810, 600, 90, 32, 28, cls="p urltxt", va="m", align="center"))
    return {"html": "".join(h), "role": "cover"}


# ===================================================== registry: type -> [(variant, family, fn, applies)]
def _always(it):
    return True


REG: dict[str, list] = {
    "title": [("left", "split", cover_left, _always), ("bottom", "bigtype", cover_bottom, _always), ("center", "center", cover_center, _always), ("poster", "poster", cover_poster, _always)],
    "section": [("num", "editorial", section_num, _always), ("band", "poster", section_band, _always), ("center", "center", section_center, _always)],
    "statement": [("big", "bigtype", statement_big, _always), ("center", "center", statement_center, _always), ("split", "poster", statement_split, _always)],
    "bullets": [("rows", "editorial", bullets_rows, lambda it: len(it["items"]) >= 2), ("cards", "bento", bullets_cards, lambda it: len(it["items"]) >= 2),
                ("lead", "split", bullets_lead, lambda it: 3 <= len(it["items"]) <= 4), ("stack", "stack", bullets_stack, _always)],
    "compare": [("panels", "bento", compare_panels, _always), ("table", "editorial", compare_table, _always), ("versus", "poster", compare_versus, _always)],
    "steps": [("row", "stack", steps_row, lambda it: len(it["steps"]) <= 5), ("stair", "bento", steps_stair, lambda it: 3 <= len(it["steps"]) <= 5), ("list", "editorial", steps_list, _always)],
    "bignumber": [("giant", "bigtype", bignumber_giant, _always), ("split", "split", bignumber_split, _always), ("center", "center", bignumber_center, _always)],
    "bignumbers": [("duo", "split", bignumbers_duo, lambda it: len(it["items"]) == 2), ("cols", "editorial", bignumbers_cols, _always),
                   ("bars", "bento", bignumbers_bars, lambda it: all(_numval(m["value"]) is not None for m in it["items"]) and min(_numval(m["value"]) for m in it["items"]) >= 0.2 * max(_numval(m["value"]) for m in it["items"]))],
    "quote": [("big", "poster", quote_big, _always), ("side", "editorial", quote_side, _always), ("center", "center", quote_center, _always)],
    "illustration": [("right", "split", illu_right, _always), ("left", "bento", illu_left, _always)],
    "quiz": [("list", "stack", quiz_list, lambda it: len(it["choices"]) <= 5), ("grid", "bento", quiz_grid, lambda it: len(it["choices"]) <= 4), ("side", "split", quiz_side, _always)],
    "timeline": [("rail", "stack", timeline_rail, lambda it: len(it["events"]) <= 5), ("vertical", "editorial", timeline_vertical, _always)],
    "chart": [("side", "split", chart_side, _always), ("full", "bigtype", chart_full, _always)],
    "math": [("center", "center", math_center, _always), ("split", "split", math_split, _always)],
    "timer": [("big", "bigtype", timer_big, _always), ("ring", "split", timer_ring, _always)],
    "qr": [("split", "split", qr_split, _always), ("center", "center", qr_center, _always)],
    "image": [("full", "bigtype", image_full, _always), ("frame", "split", image_frame, _always), ("split", "poster", image_split, _always)],
    "video": [("frame", "stack", video_frame, _always)],
    "closing": [("big", "bigtype", closing_big, lambda it: not it.get("_qr")), ("split", "split", closing_split, _always)],
}


# context recipe layouts (table / summary / toc / hero / public cover + 개조식 lists) - see deck_ctx_layouts.py
import deck_ctx_layouts as _ctxlay  # noqa: E402

_ctxlay.register(REG)
