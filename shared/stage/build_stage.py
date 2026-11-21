# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Assemble a stage page (slides / motion) without retyping the runtime.

Usage:
    python3 build_stage.py --data doc.json --show show.js [--css extra.css] --out page.html
    python3 build_stage.py --missile subject-intro --skin science --content content.json --out page.html

The runtime (stage.html) and anime.js are copied byte-for-byte; only DOC, SHOW and CSS change.
After that: --libs motion,chartjs,katex,lucide,confetti inlines extra libraries (shared/vendor, only what you name or
the page clearly uses), and Noto Sans/Serif KR are embedded cut to the page's characters (--no-fonts to skip; needs
fonttools, otherwise the Google Fonts link stays). `motion` needs --allow-modern (Chrome 80+).
--credit adds a small 「교사 스튜디오로 만듦」 on the last screen (default off).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
import html as _html


def _js_json(obj, **kw) -> str:
    """JSON for an inline <script>: < > & and U+2028/2029 become unicode escapes, so </script> or <!-- in text can never end the tag."""
    s = json.dumps(obj, ensure_ascii=False, **kw)
    for ch, esc in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), (chr(0x2028), "\\u2028"), (chr(0x2029), "\\u2029")):
        s = s.replace(ch, esc)
    return s

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
try:
    from stamp import stamp  # shared/tools/stamp.py: invisible author mark
except ImportError:
    def stamp(html: str) -> str:
        return html
RUNTIME = SKILL / "assets" / "stage.html" if (SKILL / "assets" / "stage.html").exists() else HERE / "stage.html"
VENDOR_DIR = RUNTIME.parent / "vendor"
MISSILES = SKILL / "assets" / "missiles"
DOC_RE = re.compile(r"window\.DOC = \{.*?\n\};", re.S)
SHOW_RE = re.compile(r"(/\* ===================== SHOW .*?\*/\n).*?(\n</script>\n<script>STAGE\.boot)", re.S)


def build(doc: dict, show_js: str, out: Path, css: str = "", libs: list | None = None, fonts: bool = True,
          credit: bool = False, allow_modern: bool = False, scene_html: str = "", offline: bool = True) -> int:
    """Inject DOC, SHOW, CSS and anime.js into the runtime (+ optional libs, embedded fonts); return size in bytes.

    scene_html: static markup placed inside #scene (spec-built decks keep their slides as real HTML).
    offline (default True): drop the Google Fonts links entirely (the page then uses only the embedded Noto fonts) -> zero external requests.
    A doc with "online": true keeps them (and lets the show load extra fonts).
    """
    html = RUNTIME.read_text(encoding="utf-8")
    if not DOC_RE.search(html) or not SHOW_RE.search(html):
        raise SystemExit("stage markers not found - stage.html was modified")
    vendor = (VENDOR_DIR / "anime-4.5.0.umd.min.js").read_text(encoding="utf-8")
    html = html.replace("<!--VENDOR-->", "<script>\n" + vendor + "\n</script>", 1)
    if scene_html:
        html = html.replace('<div id="scene"></div>', '<div id="scene">' + scene_html + "</div>", 1)
    if credit:
        doc = {**doc, "credit": True}
    html = DOC_RE.sub(lambda _: "window.DOC = " + _js_json(doc, indent=2) + ";", html, count=1)
    html = SHOW_RE.sub(lambda m: m.group(1) + show_js.rstrip() + m.group(2), html, count=1)
    if css:
        html = html.replace("</style>", css.rstrip() + "\n</style>", 1)
    title = doc.get("title")
    if title:
        html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{_html.escape(str(title))}</title>", html, count=1)
    if libs and inline:
        try:
            html, _ = inline.apply(html, [x for x in libs if x != "anime"], auto=True, allow_modern=allow_modern)
        except ValueError as exc:
            raise SystemExit("만들기를 멈췄어요: " + str(exc))
    elif inline and not allow_modern and "motion" in inline.detect(html):
        raise SystemExit("만들기를 멈췄어요: " + inline.MODERN_MSG)  # a page that calls Motion.* without opt-in is refused too
    if fonts and embed:
        html, rep = embed.embed(html)
        if not rep.get("embedded"):
            print("fonts: " + rep.get("reason", "not embedded"))
            if rep.get("prompt"):
                print("ASK TEACHER: " + rep["prompt"])
        else:
            print(f"fonts embedded: {rep['before_bytes'] // 1024} KB -> {rep['after_bytes'] // 1024} KB")
    if offline and doc.get("online") is not True:
        html = re.sub(r'<link[^>]+(?:fonts\.googleapis|fonts\.gstatic)[^>]*>\s*', "", html)
        html = re.sub(r"\s*<!-- Korean display fonts[^>]*-->", "", html)
        html = re.sub(r"""(["'])https://fonts\.(?:googleapis|gstatic)\.com[^"']*\1""", '""', html)  # the (unreachable offline) font loaders of a show leave no address behind
    html = stamp(html)
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
    ap.add_argument("--credit", action="store_true", help="show a small 'made with Teacher Studio' on the last screen (only when the teacher asks)")
    ap.add_argument("--allow-modern", action="store_true", help="allow Motion (needs Chrome 80+; anime.js is the safe default)")
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
    size = build(doc, show, a.out, css, [x for x in a.libs.split(",") if x], not a.no_fonts,
                 a.credit, a.allow_modern)
    print(f"built {a.out} ({size // 1024} KB)")


def _no_browser_guard() -> bool:
    """True when no browser can start here (an agent's security box). shared/tools/workdir.py then prints ONE line and makes
    every screen check below skip at once instead of waiting for each launch to fail."""
    try:
        here = Path(__file__).resolve().parent
        for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
            if (d / "workdir.py").is_file():
                if str(d) not in sys.path:
                    sys.path.append(str(d))
                import workdir
                return workdir.guard_browser()
    except Exception:  # noqa: BLE001 - the guard must never stop a build
        pass
    return False


if __name__ == "__main__":
    _no_browser_guard()
    main()
