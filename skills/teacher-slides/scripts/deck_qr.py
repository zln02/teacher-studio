# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""QR code as inline SVG, drawn at build time with the vendored Nayuki qrcodegen (MIT). Black on white, 4-module quiet zone, ECC medium."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE.parent / "shared" / "vendor" / "qrcodegen", _HERE.parent.parent.parent / "shared" / "vendor" / "qrcodegen"):
    if _p.exists():
        sys.path.insert(0, str(_p))
        break
import qrcodegen  # noqa: E402


def svg(text: str, border: int = 4) -> str:
    """One <svg> (viewBox in modules) for the text; raises ValueError when it is too long for a QR code."""
    if not text.lower().startswith(("http://", "https://", "mailto:", "tel:")) and "." in text and " " not in text:
        text = "https://" + text
    qr = qrcodegen.QrCode.encode_text(text, qrcodegen.QrCode.Ecc.MEDIUM)
    n = qr.get_size()
    d = []
    for y in range(n):
        x = 0
        while x < n:
            if qr.get_module(x, y):
                x0 = x
                while x < n and qr.get_module(x, y):
                    x += 1
                d.append(f"M{x0 + border} {y + border}h{x - x0}v1h-{x - x0}z")
            else:
                x += 1
    s = n + 2 * border
    return (f'<svg viewBox="0 0 {s} {s}" shape-rendering="crispEdges" role="img" aria-label="QR code"><rect width="{s}" height="{s}" fill="#fff"/>'
            f'<path d="{"".join(d)}" fill="#111"/></svg>')
