# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Small kit shared by the slide layouts: text metrics (Korean-aware wrapping), markup helpers, absolute boxes, build indexes."""
from __future__ import annotations

import html as _html
import re

FACTOR = {"h": 1.03, "l": 0.60, "s": 0.30, "p": 0.42}  # em widths: hangul/CJK, latin+digits (bold), space, punctuation


def esc(s) -> str:
    return _html.escape("" if s is None else str(s), quote=True)


def rich(s) -> str:
    """Escape, then **word** -> <em>word</em> and \\n -> <br>."""
    t = esc(s).replace("\\n", "\n")
    t = re.sub(r"\*\*(.+?)\*\*", r"<em>\1</em>", t, flags=re.S)
    return t.replace("\n", "<br>")


def plain(s) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(s or "")).replace("\\n", "\n")


def _cw(ch: str) -> float:
    if ch.isspace():
        return FACTOR["s"]
    if "가" <= ch <= "힣" or "㄰" <= ch <= "㆏" or "一" <= ch <= "鿿" or ch in "「」『』【】":
        return FACTOR["h"]
    if ch.isalnum():
        return FACTOR["l"]
    return FACTOR["p"] if ord(ch) < 0x2000 else 1.05  # emoji and symbols ~ full width


def text_w(s: str, size: float) -> float:
    return sum(_cw(c) for c in s) * size


def n_lines(s: str, size: float, w: float) -> int:
    """Greedy keep-all wrap (breaks only at spaces; a word wider than the box is hard-broken)."""
    total = 0
    for para in plain(s).split("\n"):
        words = para.split(" ")
        cur, lines = 0.0, 1
        for wd in words:
            ww = text_w(wd, size)
            sp = FACTOR["s"] * size
            if cur == 0:
                cur = ww
            elif cur + sp + ww <= w:
                cur += sp + ww
            else:
                lines += 1
                cur = ww
            while cur > w:  # hard break inside a very long word
                lines += 1
                cur -= w
        total += lines
    return total


def fit(s: str, w: float, h: float, mx: int, mn: int, lh: float = 1.25) -> int:
    """Largest font size (step 2) between mn..mx whose wrapped text fits w x h."""
    size = int(mx)
    while size > mn and n_lines(s, size, w * 0.97) * size * lh > h:
        size -= 2
    return max(size, int(mn))


class Ctx:
    """Per-slide context: design, slide index, build counter."""

    def __init__(self, dz: dict, idx: int, builds: bool = True):
        self.dz, self.idx, self.builds = dz, idx, builds
        self.floor = dz["floor"]
        self._b = 0
        self.max_b = 0

    def b(self, step: int | None = None) -> str:
        """class+attr snippet for the next build step (empty when builds are off)."""
        if not self.builds:
            return ""
        if step is None:
            self._b += 1
            step = self._b
        self.max_b = max(self.max_b, step)
        return f' data-b="{step}"'


def style_of(x, y, w, h, extra: str = "") -> str:
    return f"left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px;{extra}"


def box(x, y, w, h, inner: str = "", cls: str = "", extra: str = "", attrs: str = "") -> str:
    return f'<div class="bx {cls}"{attrs} style="{style_of(x, y, w, h, extra)}">{inner}</div>'


def T(ctx: Ctx, text, x, y, w, h, mx, mn=None, cls: str = "p", va: str = "m", lh: float = 1.25, step: int | None = -1, extra: str = "", align: str = "") -> str:
    """Text box with a Python-estimated font size (and data-fit for the runtime safety net). step=-1 -> no build; None -> next build."""
    sc = (ctx.dz.get("tscale") or {}).get((cls.split() or ["p"])[0], 1.0)  # context type scale (deck_context recipes)
    if sc != 1.0:
        mx, mn = int(mx * sc), int((mn or ctx.floor) * sc)
    mn = max(ctx.floor, mn or ctx.floor)
    mx = max(mx, mn)
    s = fit(plain(text), w, h, mx, mn, lh)
    battr = "" if step == -1 else ctx.b(step)
    bcls = "" if step == -1 or not ctx.builds else " b"
    al = f"text-align:{align};" if align else ""
    return (f'<div class="bx {cls} va-{va}{bcls}"{battr} data-fit="{mx},{mn}" '
            f'style="{style_of(x, y, w, h, f"font-size:{s}px;line-height:{lh};{al}{extra}")}"><div class="tx">{rich(text)}</div></div>')


def kicker(ctx: Ctx, text, x, y, w=900, cls: str = "k") -> str:
    if not text:
        return ""
    fs = max(28, ctx.floor)  # a context with a higher floor (class = 32px) lifts the kicker too
    return f'<div class="bx {cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{fs + 16}px;font-size:{fs}px">{esc(text)}</div>'


def rect(x, y, w, h, cls: str = "", extra: str = "") -> str:
    return f'<div class="bx {cls}" aria-hidden="true" style="{style_of(x, y, w, h, extra)}"></div>'
