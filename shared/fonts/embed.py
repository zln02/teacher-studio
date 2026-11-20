#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Embed Korean fonts into one HTML file so it looks right offline.

TS Sans (the studio's default face: a renamed subset of Pretendard, SIL OFL 1.1), Noto Sans KR and Noto Serif KR (SIL OFL 1.1)
are cut down to the characters the page really uses (fonttools) and written into the page as base64 WOFF2. Everything else stays as is.

Usage:
    python3 embed.py page.html [--out page.html] [--yes]      # embed in place / to --out
    from embed import embed;  html, report = embed(html)       # in a builder

If fonttools is missing the page is returned untouched (Google Fonts link + system fonts stay), and the
report carries a plain-Korean `prompt` the AI can show to the teacher. Pass consent=True / --yes to install.

Files (shared/fonts/base): KS X 1001 subsets of the official variable fonts (wght 400-900), cut once from
google/fonts NotoSansKR[wght].ttf / NotoSerifKR[wght].ttf. Syllables outside KS X 1001 fall back to system fonts.
TS Sans = Pretendard 1.3.9 (Copyright (c) 2021 Kil Hyung-jin, Reserved Font Name "Pretendard"), same KS X 1001 coverage, wght 100-900, cut by
tools/build_ts_sans.py and renamed because a subset is a Modified Version (OFL-Pretendard.txt). Tabular figures (tnum) are kept.
OFL notes: OFL-NotoSansKR.txt (Reserved Font Name 'Source' - never used as a name here), OFL-NotoSerifKR.txt.
"""
from __future__ import annotations

import argparse
import base64
import io
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
BASE = {
    "TS Sans": HERE / "base" / "TSSans-ksx1001-wght100-900.woff2",
    "Noto Sans KR": HERE / "base" / "NotoSansKR-ksx1001-wght400-900.woff2",
    "Noto Serif KR": HERE / "base" / "NotoSerifKR-ksx1001-wght400-900.woff2",
}
KEEP_NAME_IDS = [0, 1, 2, 3, 4, 6, 13, 14]  # keep copyright + license notices in the font
STYLE_ID = "ts-fonts"
_DATA_URI = re.compile(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]+")


def _chars(html: str) -> str:
    """Every distinct character on the page (data URIs removed so base64 noise is not counted)."""
    return "".join(sorted(set(_DATA_URI.sub("", html))))


def _have_tools() -> tuple[bool, str]:
    """True when fonttools and brotli (WOFF2) can be imported."""
    try:
        import fontTools  # noqa: F401
        import brotli  # noqa: F401
    except ImportError as exc:
        return False, f"{exc.name} 없음"
    return True, ""


def subset_woff2(family: str, text: str) -> bytes:
    """Cut one family's base font down to the characters in `text`; returns WOFF2 bytes."""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(str(BASE[family]), lazy=False)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "locl", "tnum", "case"]
    opts.name_IDs = KEEP_NAME_IDS
    opts.hinting = False
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def font_face_css(family: str, woff2: bytes) -> str:
    """One @font-face rule covering weights 400-900 from a variable subset."""
    b64 = base64.b64encode(woff2).decode("ascii")
    return ('@font-face{font-family:"%s";font-style:normal;font-weight:%s;font-display:swap;'
            'src:url(data:font/woff2;base64,%s) format("woff2")}' % (family, "100 900" if family == "TS Sans" else "400 900", b64))


def families_used(html: str) -> list[str]:
    """Which embeddable families the page names. A page that names TS Sans gets TS Sans (Noto Sans KR then stays a name in the stack only:
    same coverage, so embedding both would double the file for nothing); any other page gets Noto Sans KR as the safety net."""
    out = ["TS Sans"] if "TS Sans" in html else ["Noto Sans KR"]
    if "Noto Serif KR" in html:
        out.append("Noto Serif KR")
    return out


_EXT_LINK = re.compile(r"""\s*<link\b[^>]*(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^>]*>""", re.I)


def go_offline(html: str) -> str:
    """Remove every Google Fonts <link> / preconnect (and the comment that explains them). Fonts that are not embedded then fall back to system fonts.
    Builders call this by default; a spec that opts in with "online": true keeps the links."""
    html = _EXT_LINK.sub("", html)
    return re.sub(r"\s*<!-- Korean display fonts[^>]*-->", "", html)


def embed(html: str, families: list[str] | None = None, consent: bool = False) -> tuple[str, dict]:
    """Return (html with embedded fonts, report). Never raises for a missing tool: returns the page untouched."""
    report: dict = {"embedded": False, "before_bytes": len(html.encode("utf-8")), "families": {}}
    if STYLE_ID in html:
        report.update(embedded=True, reason="이미 들어 있음", after_bytes=report["before_bytes"])
        return html, report
    ok, why = _have_tools()
    if not ok:
        try:
            import ensure
            res = ensure.ensure("fonttools", consent=consent)
            ok = res["ok"]
            if not ok:
                report["prompt"] = res["prompt"]
        except ImportError:
            pass
        if not ok:
            report["reason"] = f"글꼴 도구 없음({why}) - 기존 방식(Google 글꼴 + 시스템 글꼴) 유지"
            report["after_bytes"] = report["before_bytes"]
            return html, report
    text = _chars(html)
    css = []
    fams = list(families or families_used(html))
    if fams and fams[0] == "Noto Sans KR" and ("TS Sans" in html):
        fams[0] = "TS Sans"   # callers that still ask for the old safety net get the studio face when the page names it
    for fam in fams:
        data = subset_woff2(fam, text)
        report["families"][fam] = len(data)
        css.append(font_face_css(fam, data))
    block = '<style id="%s">/* TS Sans = Pretendard subset (c) 2021 Kil Hyung-jin, renamed; Noto KR (c) Adobe / Google. SIL OFL 1.1, cut to this page: see NOTICE */\n%s\n</style>\n' % (STYLE_ID, "\n".join(css))
    # Noto is now inside the file: drop it from the Google Fonts request (other display fonts stay online-only).
    html = re.sub(r"&family=Noto\+(?:Sans|Serif)\+KR(?::[^&\"']*)?", "", html)
    html = re.sub(r"family=Noto\+(?:Sans|Serif)\+KR(?::[^&\"']*)?&", "", html)
    if "</head>" in html:
        html = html.replace("</head>", block + "</head>", 1)
    else:
        html = block + html
    report.update(embedded=True, after_bytes=len(html.encode("utf-8")), chars=len(text))
    return html, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--yes", action="store_true", help="install fonttools if it is missing")
    a = ap.parse_args()
    html, rep = embed(a.page.read_text(encoding="utf-8"), consent=a.yes)
    if rep["embedded"]:
        (a.out or a.page).write_text(html, encoding="utf-8")
    print(rep.get("prompt") or f"embedded={rep['embedded']} {rep['before_bytes'] // 1024}KB -> {rep['after_bytes'] // 1024}KB {rep['families']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
