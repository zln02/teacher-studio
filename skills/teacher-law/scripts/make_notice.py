#!/usr/bin/env python3
"""Fill the one-page printable legal notice (A4 HTML) from a JSON file.

Usage: python3 make_notice.py --data notice.json [--out ~/TeacherStudio/law-notice-<date>.html]
JSON keys: title, question, conclusion, reasons[], sources[{name, article, effective, url}], safe_options[], checked_date
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import sys
from pathlib import Path

# Windows consoles (cp949) cannot encode emoji/check marks: never crash on output.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(errors="replace")

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "notice-template.html"
OUT_DIR = Path.home() / "TeacherStudio"


def esc(s: object) -> str:
    """HTML-escape any value."""
    return html.escape(str(s if s is not None else ""))


def li(items: list) -> str:
    """Render a list of strings as <li> items."""
    return "".join("<li>%s</li>" % esc(i) for i in items)


def source_li(s: dict) -> str:
    """Render one source; unknown parts become 확인 필요."""
    name = esc(s.get("name") or "확인 필요")
    art = esc(s.get("article") or "확인 필요")
    eff = esc(s.get("effective") or "확인 필요")
    url = s.get("url") or ""
    link = '<a href="%s">%s</a>' % (esc(url), esc(url)) if url.startswith("http") else "확인 필요"
    return "<li>%s · %s · 시행일 %s · %s</li>" % (name, art, eff, link)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    d = json.loads(Path(a.data).read_text(encoding="utf-8"))
    checked = d.get("checked_date") or datetime.date.today().isoformat()
    fills = {
        "TITLE": esc(d.get("title") or "법률 안내"),
        "QUESTION": esc(d.get("question")),
        "CONCLUSION": esc(d.get("conclusion") or "확인 필요"),
        "REASONS": li(d.get("reasons") or ["확인 필요"]),
        "SOURCES": "".join(source_li(s) for s in (d.get("sources") or [{}])),
        "SAFE_OPTIONS": li(d.get("safe_options") or ["학교 관리자·교육청에 확인하세요"]),
        "CHECKED_DATE": esc(checked),
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    for k, v in fills.items():
        page = page.replace("{{%s}}" % k, v)
    out = Path(a.out).expanduser() if a.out else OUT_DIR / ("law-notice-%s.html" % checked)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print("READY", out)


if __name__ == "__main__":
    main()
