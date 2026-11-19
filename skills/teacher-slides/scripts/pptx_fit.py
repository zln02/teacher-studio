# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Text-fit estimate for .pptx text boxes (shared by deck_pptx, which shrinks, and pptx_check, which verifies).

Metrics: Hangul/CJK glyph = 1.0 em, digit/Latin ~0.56 em (capitals 0.66), space 0.28 em, punctuation 0.38 em.
Line height = LH * size * line_spacing (Noto Sans KR ~1.45 natural, Malgun Gothic ~1.33; LH=1.35 is a middle value).
Approximate on purpose: it says "clearly too long", it never replaces looking at the slide in PowerPoint.
"""
from __future__ import annotations

import math

LH = 1.35


def char_em(c: str) -> float:
    o = ord(c)
    if c == " ":
        return 0.28
    if o >= 0x1100:
        return 1.0 if not (0xFF61 <= o <= 0xFF9F) else 0.5
    if c.isdigit():
        return 0.56
    if c.isupper():
        return 0.66
    if c.isalpha():
        return 0.55
    return 0.38


def width_em(s: str) -> float:
    return sum(char_em(c) for c in s)


def lines_for(text: str, size_pt: float, width_pt: float) -> int:
    """Greedy wrap: Latin words stay whole, Korean breaks anywhere."""
    if width_pt <= 0:
        return 99
    cap = width_pt / max(size_pt, 1)  # em per line
    n, cur = 1, 0.0
    for word in text.split(" "):
        w = width_em(word)
        sp = 0.28 if cur > 0 else 0.0
        if cur + sp + w <= cap:
            cur += sp + w
            continue
        if w <= cap and cur > 0:
            n, cur = n + 1, w
            continue
        # a long word: break by characters
        if cur > 0:
            n, cur = n + 1, 0.0
        for c in word:
            cw = char_em(c)
            if cur + cw > cap:
                n, cur = n + 1, 0.0
            cur += cw
    return n


def need_height_pt(paragraphs, width_pt: float, spacing: float = 1.12) -> float:
    """paragraphs: [(text, size_pt)]  -> points of height the wrapped text needs."""
    total = 0.0
    for text, size in paragraphs:
        total += lines_for(text, size, width_pt) * size * LH * spacing
    return total


def fit_size(paragraph_texts, size_pt: float, width_pt: float, height_pt: float, spacing: float = 1.12, floor: float = 0.6, min_pt: float = 12.0):
    """Largest size <= size_pt (never below max(min_pt, floor*size_pt)) at which the text fits. Returns (size, fits)."""
    lo = max(min_pt, size_pt * floor)
    s = float(size_pt)
    while s >= lo - 1e-6:
        if need_height_pt([(t, s) for t in paragraph_texts], width_pt, spacing) <= height_pt * 1.03:
            return s, True
        s -= 1
    return min(size_pt, math.ceil(lo)), False
