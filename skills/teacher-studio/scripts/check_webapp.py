#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Fast check for one offline web app HTML file (any page, not only build_webapp.py output).

Usage:
    python3 check_webapp.py app.html [--no-browser] [--shot shot.png] [--deep]

Static (no browser): external addresses (scripts, styles, images, fonts, @import), ?. / ?? (old school Chrome), storage/network APIs,
API keys or secrets in the file, inputs that ask for student identity (이름·학번·전화), <title>/lang/viewport.
Headless (ONE Chromium, audio muted, ~5-10 s): JS errors, outside requests, horizontal scroll, clipped or vertically broken button text,
overlapping controls, unnamed buttons / unlabeled inputs, tiny text, text contrast (solid backgrounds) at 1600x900, projector mode and
390x844 phone; clicks one item per part, then 「처음으로」 must clear it. --deep also proves the runner stops an endless loop.
Prints PASS/WARN/FAIL lines; exit 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

MUTE = ["--mute-audio"]
_EXT = r"(?:https?:)?//(?!www\.w3\.org/)"
EXTERNAL = [
    re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"']?" + _EXT, re.I),
    re.compile(r"<link\b[^>]*\bhref\s*=\s*[\"']?" + _EXT, re.I),
    re.compile(r"<(?:img|iframe|audio|video|source|embed)\b[^>]*\bsrc\s*=\s*[\"']?" + _EXT, re.I),
    re.compile(r"url\(\s*[\"']?" + _EXT, re.I),
    re.compile(r"@import\s+(?:url\()?\s*[\"']?" + _EXT, re.I),
    re.compile(r"\bimport\s*\(\s*[\"']" + _EXT, re.I),
]
NET_STORAGE = re.compile(r"\bfetch\s*\(|new\s+XMLHttpRequest|new\s+WebSocket|new\s+EventSource|sendBeacon|localStorage|sessionStorage|indexedDB|document\.cookie")
SECRET = re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}|\bAIza[0-9A-Za-z_-]{30,}|\bgh[po]_[A-Za-z0-9]{30,}|"
                    r"(?:api[_-]?key|secret|bearer)\s*[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']", re.I)
ES_BAD = re.compile(r"\?\.(?![0-9])|\?\?")
SCRIPT = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)
FIELD = re.compile(r"<(?:input|textarea)\b[^>]*>|<label\b[^>]*>.*?</label>", re.S | re.I)
IDENTITY = re.compile(r"학번|실명|전화번호|주민|(?:학생|너의|네|본인|자기)\s*이름|이름을?\s*(?:입력|적어|써)", re.I)
_DATA = re.compile(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]+")


def _strip_js_strings(js: str) -> str:
    """Remove string/template literals and comments so ?. inside Korean text ("뭐예요?.") is not counted."""
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    js = re.sub(r"(?m)(^|[^:\\])//[^\n]*", r"\1", js)
    return re.sub(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`", '""', js)


def static_checks(html: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    body = _DATA.sub("data:", html)
    ext = [m.group(0)[:80] for p in EXTERNAL for m in p.finditer(body)]
    out.append(("FAIL", "outside address (needs internet): " + " | ".join(ext[:3])) if ext else ("PASS", "no outside address: works offline"))
    js = "\n".join(SCRIPT.findall(body))
    bad = sorted(set(ES_BAD.findall(_strip_js_strings(js))))
    out.append(("FAIL", f"{' '.join(bad)} in script: old school Chrome cannot run it") if bad else ("PASS", "script syntax ES2017 (no ?. / ??)"))
    net = sorted(set(m.group(0) for m in NET_STORAGE.finditer(js)))
    out.append(("FAIL", "network/storage API in script: " + ", ".join(net)) if net else ("PASS", "no network or storage API"))
    sec = SECRET.search(body)
    out.append(("FAIL", "a key or secret is written in the file: remove it") if sec else ("PASS", "no API key or secret in the file"))
    ids = [f[:60] for f in FIELD.findall(body) if IDENTITY.search(f)]
    out.append(("FAIL", "asks for student identity: " + ids[0]) if ids else ("PASS", "no student identity fields"))
    miss = [n for n, ok in (("<title>", re.search(r"<title>\s*\S", body)), ('lang=', re.search(r"<html\b[^>]*\blang=", body, re.I)),
                            ("viewport", re.search(r"name=[\"']viewport", body, re.I))) if not ok]
    out.append(("FAIL", "missing " + ", ".join(miss)) if miss else ("PASS", "title, lang and viewport present"))
    if re.search(r"<form\b[^>]*\baction=", body, re.I):
        out.append(("FAIL", "<form action=...> would send typed text somewhere"))
    kb = len(html.encode("utf-8")) // 1024
    out.append(("WARN", f"file is {kb} KB (big for a school PC)") if kb > 3000 else ("PASS", f"file size {kb} KB"))
    return out


LAYOUT_JS = r"""
() => {
  const clipR = e => { let r = e.getBoundingClientRect(); r = {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
    for (let n = e.parentElement; n && n !== document.body; n = n.parentElement) { const s = getComputedStyle(n);
      if (s.overflow !== 'visible' || s.overflowX !== 'visible' || s.overflowY !== 'visible') { const q = n.getBoundingClientRect();
        r = {left: Math.max(r.left, q.left), top: Math.max(r.top, q.top), right: Math.min(r.right, q.right), bottom: Math.min(r.bottom, q.bottom)}; } }
    return r; };
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e), c = clipR(e); return r.width > 1 && r.height > 1 && r.right > 0 && c.right - c.left > 1 && c.bottom - c.top > 1 && s.visibility !== 'hidden' && s.display !== 'none' && !e.closest('dialog:not([open])'); };
  const name = e => (e.innerText || '').trim() || e.getAttribute('aria-label') || e.getAttribute('title') || '';
  const lab = e => (e.labels && e.labels.length) || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby') || e.getAttribute('title');
  const res = {hscroll: document.documentElement.scrollWidth > innerWidth + 1, clipped: [], vertical: [], overlap: [], unnamed: [], unlabeled: [], small: [], lowc: [], offscreen: []};
  const ctl = [...document.querySelectorAll('button,a[href],input,select,textarea,[role=button]')].filter(vis);
  for (const e of ctl) {
    const r = e.getBoundingClientRect(), t = name(e).slice(0, 24);
    if ((e.tagName === 'BUTTON' || e.getAttribute('role') === 'button') && !name(e)) res.unnamed.push(e.outerHTML.slice(0, 60));
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.tagName) && e.type !== 'hidden' && !lab(e)) res.unlabeled.push(e.outerHTML.slice(0, 60));
    if (e.tagName === 'BUTTON' && e.scrollWidth > e.clientWidth + 2) res.clipped.push(t);
    if (e.tagName === 'BUTTON' && t.length > 1 && r.height > r.width * 1.5 && r.height > 60) res.vertical.push(t);
    if (r.right > innerWidth + 1 || r.left < -1) res.offscreen.push(t || e.tagName);
  }
  for (let i = 0; i < ctl.length; i++) for (let j = i + 1; j < ctl.length; j++) {
    const a = ctl[i], b = ctl[j];
    if (a.contains(b) || b.contains(a)) continue;
    const p = clipR(a), q = clipR(b);
    const w = Math.min(p.right, q.right) - Math.max(p.left, q.left), h = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top);
    if (w > 2 && h > 2) res.overlap.push(name(a).slice(0, 14) + ' / ' + name(b).slice(0, 14));
  }
  for (const h of document.querySelectorAll('h1,h2,h3,label,.wa-chip')) if (vis(h) && h.scrollWidth > h.clientWidth + 2 && getComputedStyle(h).overflow !== 'visible') res.clipped.push((h.innerText || '').slice(0, 24));
  const rgb = c => { const m = c.match(/[\d.]+/g); return m ? m.map(Number) : null; };
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const bgOf = e => { for (let n = e; n && n.nodeType === 1; n = n.parentElement) { const s = getComputedStyle(n); if (s.backgroundImage && s.backgroundImage !== 'none') return null; const c = rgb(s.backgroundColor); if (c && (c.length < 4 || c[3] > 0.95)) return c; } return null; };
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode, e = n.parentElement;
    if (!e || !n.textContent.trim() || seen.has(e) || !vis(e) || e.closest('.wa-sr,.wa-skip,script,style')) continue;
    seen.add(e);
    const s = getComputedStyle(e), px = parseFloat(s.fontSize);
    if (px < 14) res.small.push(Math.round(px) + 'px ' + n.textContent.trim().slice(0, 16));
    const fg = rgb(s.color), bg = bgOf(e);
    if (fg && bg) { const a = lum(fg), b = lum(bg), cr = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05), big = px >= 24 || (px >= 18.6 && +s.fontWeight >= 700);
      if (cr < (big ? 3 : 4.5)) res.lowc.push(cr.toFixed(1) + ':1 ' + n.textContent.trim().slice(0, 16)); }
  }
  return res;
}
"""


def _layout_findings(tag: str, r: dict) -> list[tuple[str, str]]:
    out = []
    for key, lvl, msg in (("hscroll", "FAIL", "page scrolls sideways"), ("clipped", "FAIL", "text cut off"), ("vertical", "FAIL", "button text breaks vertically"),
                          ("overlap", "FAIL", "controls overlap"), ("offscreen", "FAIL", "control outside the screen"), ("unnamed", "FAIL", "button without a name"),
                          ("unlabeled", "FAIL", "input without a label"), ("lowc", "FAIL", "low text contrast"), ("small", "WARN", "text under 14px")):
        v = r.get(key)
        if v:
            items = v if isinstance(v, list) else []
            out.append((lvl, f"[{tag}] {msg}" + (": " + " | ".join(sorted(set(items))[:4]) if items else "")))
    if not out:
        out.append(("PASS", f"[{tag}] layout, names, labels, contrast OK"))
    return out


def _launch(p):
    last = None
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(args=MUTE, **kw)
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise RuntimeError(f"no Chromium: {last}")


def browser_checks(path: Path, shot: str | None = None, deep: bool = False) -> list[tuple[str, str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [("WARN", "Playwright not installed: browser checks skipped (static checks only)")]
    out: list[tuple[str, str]] = []
    url = path.resolve().as_uri()
    errors: list[str] = []
    outside: list[str] = []

    def watch(pg):
        pg.on("pageerror", lambda e: errors.append(str(e)[:120]))
        pg.on("console", lambda m: errors.append(m.text[:120]) if m.type == "error" else None)
        pg.on("request", lambda r: outside.append(r.url[:80]) if not r.url.startswith(("file:", "data:", "blob:", "about:")) else None)

    with sync_playwright() as p:
        b = _launch(p)
        try:
            pg = b.new_page(viewport={"width": 1600, "height": 900})
            watch(pg)
            pg.goto(url)
            pg.wait_for_timeout(250)
            out += _layout_findings("1600x900", pg.evaluate(LAYOUT_JS))
            # one action per part: first chip / send for helpers, run for runners
            acted = pg.evaluate("""() => { let n = 0;
              document.querySelectorAll('.wa-card').forEach(c => { const b = c.querySelector('.wa-chips .wa-chip') || c.querySelector('.wa-run') || c.querySelector('.wa-custom button, button'); if (b) { b.click(); n++; } });
              return n; }""")
            pg.wait_for_timeout(600)
            if shot:
                pg.screenshot(path=shot)
            state = pg.evaluate("""() => ({msgs: document.querySelectorAll('.wa-log .wa-msg').length, out: [...document.querySelectorAll('.wa-out')].map(o => o.textContent.trim().length)})""")
            if pg.locator(".wa-run").count():
                ok = all(n > 0 for n in state["out"])
                out.append(("PASS" if ok else "FAIL", "runner printed a result" if ok else "runner showed nothing after 실행"))
            if pg.locator(".wa-log").count():
                ok = state["msgs"] >= 3
                out.append(("PASS" if ok else "FAIL", "helper answered a question" if ok else "helper did not answer the first question"))
            for sel in ("#wa-bigger", "#wa-bigger", "#wa-proj"):
                if pg.locator(sel).count():
                    pg.click(sel)
            pg.wait_for_timeout(150)
            out += _layout_findings("projector", pg.evaluate(LAYOUT_JS))
            pg.keyboard.press("p")  # keyboard: P toggles projector back off
            if pg.evaluate("document.documentElement.classList.contains('projector')"):
                out.append(("FAIL", "P key did not toggle projector mode"))
            if pg.locator("#wa-reset").count():
                pg.click("#wa-reset")
                pg.wait_for_timeout(150)
                st = pg.evaluate("""() => ({msgs: document.querySelectorAll('.wa-log .wa-msg').length, out: [...document.querySelectorAll('.wa-out')].map(o => o.textContent.trim().length)})""")
                ok = st["msgs"] <= len(pg.locator(".wa-log").all()) and all(n == 0 for n in st["out"])
                out.append(("PASS" if ok else "FAIL", "처음으로 clears the screen" if ok else "처음으로 did not clear everything"))
            else:
                out.append(("FAIL", "no reset button (#wa-reset)"))
            if pg.locator("#wa-about-btn").count():
                pg.click("#wa-about-btn")
                opened = pg.evaluate("!!document.querySelector('dialog[open]')")
                pg.keyboard.press("Escape")
                out.append(("PASS" if opened else "FAIL", "「이 프로그램은?」 panel opens" if opened else "about panel did not open"))
            if deep and pg.locator(".wa-run").count():
                pg.fill(".wa-code", "while (true) {}")
                pg.click(".wa-run")
                pg.wait_for_timeout(3800)
                stopped = "멈췄어요" in pg.inner_text(".wa-out")
                out.append(("PASS" if stopped else "FAIL", "endless loop is stopped" if stopped else "endless loop was not stopped"))
            out.append(("PASS", f"clicked {acted} part(s)"))
            ph = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
            watch(ph)
            ph.goto(url)
            ph.wait_for_timeout(200)
            out += _layout_findings("phone 390", ph.evaluate(LAYOUT_JS))
        finally:
            b.close()
    errs = sorted(set(errors))
    out.append(("FAIL", "JS errors: " + " | ".join(errs[:3])) if errs else ("PASS", "no JS errors"))
    out.append(("FAIL", "outside requests: " + " | ".join(sorted(set(outside))[:3])) if outside else ("PASS", "no outside requests while running"))
    return out


def run(path: Path, browser: bool = True, shot: str | None = None, deep: bool = False) -> int:
    html = Path(path).read_text(encoding="utf-8", errors="replace")
    res = static_checks(html)
    if browser:
        try:
            res += browser_checks(Path(path), shot, deep)
        except Exception as exc:  # noqa: BLE001 - a missing browser is a warning, not a crash
            res.append(("WARN", f"browser checks skipped: {str(exc)[:120]}"))
    for lvl, msg in res:
        print(f"{lvl} {msg}")
    fails = sum(1 for lvl, _ in res if lvl == "FAIL")
    print(f"check: {'PASS' if not fails else f'FAIL ({fails})'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", type=Path)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--shot")
    ap.add_argument("--deep", action="store_true")
    a = ap.parse_args()
    return run(a.page, not a.no_browser, a.shot, a.deep)


if __name__ == "__main__":
    sys.exit(main())
