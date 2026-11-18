#!/usr/bin/env python3
"""Put only the vendored libraries a page really uses into that page (one self-contained HTML file).

    from inline import apply
    html, report = apply(html, libs=["confetti"], auto=True)

- libs : ids from manifest.json (anime, motion, confetti, chartjs, katex, lucide, phaser) added explicitly.
- auto : also add libs the page's own code clearly uses (Motion., new Chart(, confetti(, katex., anime.).
         phaser is never added automatically (large): ask for it in libs.
- placeholders `<!--TS:LIB motion-->` mark exactly where a lib goes; `<!--TS:ICONS star,check-->` adds Lucide icons.
- icons: write `<svg class="i"><use href="#lucide-star"/></svg>`; only the <symbol>s named on the page are inlined.
- axe-core is checker-only: it is never inlined into an output page.

CLI:  python3 inline.py page.html [--libs motion,chartjs] [--no-auto] [--out out.html]   |   python3 inline.py --list
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
USAGE = {
    "motion": re.compile(r"\bMotion\.\w+"),
    "chartjs": re.compile(r"\bnew\s+Chart\s*\("),
    "confetti": re.compile(r"(?<![\w.])confetti\s*\("),
    "katex": re.compile(r"\bkatex\.(?:render|renderToString)\b"),
    "anime": re.compile(r"(?<![\w.])anime\.(?:animate|createTimeline|stagger|utils)\b"),
}
ICON_USE = re.compile(r"#lucide-([a-z0-9-]+)")
KATEX_BASIC = ("Main-Regular", "Main-Bold", "Main-Italic", "Math-Italic", "AMS-Regular", "Size1-Regular", "Size2-Regular")


def manifest() -> dict:
    """The libs actually present next to this file (a skill's copy holds only the libs that skill uses)."""
    data = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))["libs"]
    return {k: v for k, v in data.items() if (HERE / v["dir"]).exists()}


def _read(lib: dict, key: str) -> str:
    return (HERE / lib["dir"] / lib[key]).read_text(encoding="utf-8")


def _script(lib_id: str, lib: dict) -> str:
    """<script> block for one JS library (an `</script` inside the code is escaped)."""
    code = _read(lib, "js").replace("</script", "<\\/script")
    return f"<script>/* TS:VENDOR {lib_id} {lib['version']} ({lib['license']}) */\n{code}\n</script>\n"


def _katex(lib: dict, fonts: str) -> str:
    """KaTeX css (fonts as base64 WOFF2, only the common ones unless fonts == 'all') + js."""
    css = _read(lib, "css")
    fdir = HERE / lib["dir"] / lib["fonts_dir"]

    def face(m: re.Match) -> str:
        name = re.search(r"url\(fonts/KaTeX_([A-Za-z0-9-]+)\.woff2\)", m.group(0)).group(1)
        if fonts != "all" and name not in KATEX_BASIC:
            return ""
        b64 = base64.b64encode((fdir / f"KaTeX_{name}.woff2").read_bytes()).decode("ascii")
        return re.sub(r"src:.*\}$", 'src:url(data:font/woff2;base64,%s) format("woff2")}' % b64, m.group(0))

    css = re.sub(r"@font-face\{[^}]*\}", face, css)
    return f"<style>/* TS:VENDOR katex {lib['version']} ({lib['license']}) */\n{css}\n</style>\n" + _script("katex", lib)


def icon_sprite(names: list[str], lib: dict | None = None) -> str:
    """Hidden <svg> holding only the named Lucide icons as <symbol id="lucide-NAME">."""
    lib = lib or manifest()["lucide"]
    src = _read(lib, "sprite")
    out, missing = [], []
    for n in sorted(set(names)):
        m = re.search(r'<symbol id="%s"([^>]*)>(.*?)</symbol>' % re.escape(n), src, re.S)
        if not m:
            missing.append(n)
            continue
        inner = re.sub(r"\s+", " ", m.group(2)).strip()
        out.append(f'<symbol id="lucide-{n}"{m.group(1)} fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{inner}</symbol>')
    if missing:
        raise KeyError("unknown Lucide icons: " + ", ".join(missing))
    return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><!-- TS:VENDOR lucide {lib["version"]} (ISC) -->{"".join(out)}</svg>\n'


def detect(html: str) -> list[str]:
    """Libraries the page's own code clearly uses (never phaser, never axe-core)."""
    own = re.sub(r"<script>/\* TS:VENDOR.*?</script>", "", html, flags=re.S)  # ignore already-inlined libraries
    found = [k for k, rx in USAGE.items() if rx.search(own)]
    if ICON_USE.search(html):
        found.append("lucide")
    return found


def apply(html: str, libs: list[str] | None = None, auto: bool = True, katex_fonts: str = "basic") -> tuple[str, dict]:
    """Inline the requested (and, with auto, the clearly used) libraries. Returns (html, report)."""
    man = manifest()
    want: list[str] = list(libs or [])
    for m in re.finditer(r"<!--TS:LIB ([a-z-]+)-->", html):
        want.append(m.group(1))
    if auto:
        want += detect(html)
    names = ICON_USE.findall(re.sub(r"<!--TS:ICONS.*?-->", "", html))
    for m in re.finditer(r"<!--TS:ICONS ([a-z0-9, -]+)-->", html):
        names += [x.strip() for x in m.group(1).split(",") if x.strip()]
    if names:
        want.append("lucide")
    ordered: list[str] = []
    for w in want:
        if w not in ordered:
            ordered.append(w)
    report: dict = {"inlined": {}, "icons": sorted(set(names))}
    for w in ordered:
        lib = man.get(w)
        if not lib:
            raise KeyError(f"library '{w}' is not available here (have: {', '.join(sorted(man))})")
        if lib.get("checker_only"):
            raise ValueError(f"{w} is checker-only and is never inlined into an output page")
        if f"TS:VENDOR {w} " in html:
            continue
        if w == "lucide":
            block = icon_sprite(names or [], lib)
            html = re.sub(r"<!--TS:ICONS[^>]*-->", "", html)
            html = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + block, html, count=1) if "<body" in html else block + html
            report["inlined"][w] = len(block)
            continue
        block = _katex(lib, katex_fonts) if w == "katex" else _script(w, lib)
        marker = f"<!--TS:LIB {w}-->"
        if marker in html:
            html = html.replace(marker, block, 1)
        else:
            i = html.find("<script")
            html = html[:i] + block + html[i:] if i >= 0 else html.replace("</body>", block + "</body>", 1)
        report["inlined"][w] = len(block.encode("utf-8"))
    return html, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", nargs="?", type=Path)
    ap.add_argument("--libs", default="")
    ap.add_argument("--no-auto", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.page:
        for k, v in manifest().items():
            flag = " [only when asked]" if v.get("on_request_only") else (" [checker only]" if v.get("checker_only") else "")
            print(f"{k:9} {v['name']} {v['version']} {v['license']} {v['bytes'] // 1024} KB{flag} - {v['use']}")
        return 0
    html, rep = apply(a.page.read_text(encoding="utf-8"), [x for x in a.libs.split(",") if x], not a.no_auto)
    (a.out or a.page).write_text(html, encoding="utf-8")
    print(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
