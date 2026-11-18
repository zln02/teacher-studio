"""Assemble a stage page (slides / motion) without retyping the runtime.

Usage:
    python3 build_stage.py --data doc.json --show show.js [--css extra.css] --out page.html
    python3 build_stage.py --missile subject-intro --skin science --content content.json --out page.html

The runtime (stage.html) and anime.js are copied byte-for-byte; only DOC, SHOW and CSS change.
After that: --libs motion,chartjs,katex,lucide,confetti inlines extra libraries (shared/vendor, only what you name or
the page clearly uses), and Noto Sans/Serif KR are embedded cut to the page's characters (--no-fonts to skip; needs
fonttools, otherwise the Google Fonts link stays).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SHARED = SKILL / "shared" if (SKILL / "shared").exists() else HERE.parent  # skill copy, or the repo's shared/ itself
for _sub in ("fonts", "vendor", "tools"):
    if (SHARED / _sub).exists():
        sys.path.insert(0, str(SHARED / _sub))
try:
    import embed  # shared/fonts/embed.py
except ImportError:
    embed = None
try:
    import inline  # shared/vendor/inline.py
except ImportError:
    inline = None
RUNTIME = SKILL / "assets" / "stage.html" if (SKILL / "assets" / "stage.html").exists() else HERE / "stage.html"
VENDOR_DIR = RUNTIME.parent / "vendor"
MISSILES = SKILL / "assets" / "missiles"
DOC_RE = re.compile(r"window\.DOC = \{.*?\n\};", re.S)
SHOW_RE = re.compile(r"(/\* ===================== SHOW .*?\*/\n).*?(\n</script>\n<script>STAGE\.boot)", re.S)


def build(doc: dict, show_js: str, out: Path, css: str = "", libs: list | None = None, fonts: bool = True) -> int:
    """Inject DOC, SHOW, CSS and anime.js into the runtime (+ optional libs, embedded fonts); return size in bytes."""
    html = RUNTIME.read_text(encoding="utf-8")
    if not DOC_RE.search(html) or not SHOW_RE.search(html):
        raise SystemExit("stage markers not found - stage.html was modified")
    vendor = (VENDOR_DIR / "anime-4.5.0.umd.min.js").read_text(encoding="utf-8")
    html = html.replace("<!--VENDOR-->", "<script>\n" + vendor + "\n</script>", 1)
    html = DOC_RE.sub(lambda _: "window.DOC = " + json.dumps(doc, ensure_ascii=False, indent=2) + ";", html, count=1)
    html = SHOW_RE.sub(lambda m: m.group(1) + show_js.rstrip() + m.group(2), html, count=1)
    if css:
        html = html.replace("</style>", css.rstrip() + "\n</style>", 1)
    title = doc.get("title")
    if title:
        html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{title}</title>", html, count=1)
    if libs and inline:
        html, _ = inline.apply(html, [x for x in libs if x != "anime"], auto=True)
    if fonts and embed:
        html, rep = embed.embed(html)
        if not rep.get("embedded"):
            print("fonts: " + rep.get("reason", "not embedded"))
            if rep.get("prompt"):
                print("ASK TEACHER: " + rep["prompt"])
        else:
            print(f"fonts embedded: {rep['before_bytes'] // 1024} KB -> {rep['after_bytes'] // 1024} KB")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return len(html.encode("utf-8"))


def merge(base: dict, content: dict) -> dict:
    """Overlay content on a skin preset; dict values merge one level deep."""
    out = dict(base)
    for key, value in content.items():
        out[key] = {**base.get(key, {}), **value} if isinstance(value, dict) and isinstance(base.get(key), dict) else value
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path)
    ap.add_argument("--show", type=Path)
    ap.add_argument("--css", type=Path)
    ap.add_argument("--missile")
    ap.add_argument("--skin")
    ap.add_argument("--content", type=Path)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--libs", default="", help="comma list: motion,chartjs,katex,lucide,confetti")
    ap.add_argument("--no-fonts", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.list:
        for m in sorted(p for p in MISSILES.iterdir() if p.is_dir()):
            print(f"{m.name}: {', '.join(sorted(s.stem for s in (m / 'skins').glob('*.json')))}")
        return
    if a.missile:
        base = MISSILES / a.missile
        doc = json.loads((base / "skins" / f"{a.skin}.json").read_text(encoding="utf-8"))
        if a.content:
            doc = merge(doc, json.loads(a.content.read_text(encoding="utf-8")))
        show = (base / "show.js").read_text(encoding="utf-8")
        css = (base / "style.css").read_text(encoding="utf-8") if (base / "style.css").exists() else ""
    else:
        if not (a.data and a.show):
            ap.error("--data and --show (or --missile/--skin) are required")
        doc = json.loads(a.data.read_text(encoding="utf-8"))
        show = a.show.read_text(encoding="utf-8")
        css = a.css.read_text(encoding="utf-8") if a.css else ""
    if not a.out:
        ap.error("--out is required")
    size = build(doc, show, a.out, css, [x for x in a.libs.split(",") if x], not a.no_fonts)
    print(f"built {a.out} ({size // 1024} KB)")


if __name__ == "__main__":
    main()
