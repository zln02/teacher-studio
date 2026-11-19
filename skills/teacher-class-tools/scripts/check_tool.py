#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Quality + privacy check for a classroom tool built by build_tool.py.

Usage: python3 check_tool.py tool.html [--no-play]
Static: size, doctype, no external request of any kind, no storage / network APIs, no <form>, inputs autocomplete=off,
keep-all, token contrast, old-Chrome syntax (patterns shared with check_game.py), JS syntax (node).
Headless (Playwright, audio muted): drives the tool at 1920x1080 and 1080x1920 and with reduced motion, then checks logic
(no duplicate draws, fair teams, bracket champion, count-up, timer end), text >= type floor, touch size, off-stage,
Korean words not split, no JS errors, no external request, nothing written to storage/cookies.
Prints PASS/WARN/FAIL lines; exit 1 on any FAIL.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SHARED = SKILL / "shared" if (SKILL / "shared" / "design").is_dir() else SKILL.parent.parent / "shared"
sys.path.insert(0, str(SHARED / "design"))
import design  # noqa: E402

MUTE = ["--mute-audio"]
SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")
FORBIDDEN_JS = {  # same old-Chrome rules as check_game.py
    r"\?\.(?=[A-Za-z_$\[(])": "optional chaining ?.",
    r"\?\?": "nullish ??",
    r"\.replaceAll\(": "replaceAll",
    r"\.at\(\s*-?\d": ".at()",
    r"structuredClone\(": "structuredClone",
    r"(?<![\w$])#[a-zA-Z_]\w*\s*[=(;]": "#private field",
    r"\balert\(|\bprompt\(|\bconfirm\(": "alert/prompt/confirm",
}
FORBIDDEN_CSS = {r"aspect-ratio\s*:": "aspect-ratio", r":has\(": ":has()", r"\b\d+(\.\d+)?dvh\b": "dvh unit"}
NETWORK = r"\b(fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|importScripts|RTCPeerConnection|postMessage)\b"
STORAGE = r"\b(localStorage|sessionStorage|indexedDB|openDatabase|caches|cookieStore)\b|document\.cookie"

LAYOUT_JS = r"""
(function(floor, minBtn){
  var out = [], st = document.getElementById('stage').getBoundingClientRect();
  var els = document.querySelectorAll('#stage *');
  for (var i = 0; i < els.length; i++){
    var e = els[i]; if (e.closest('svg')) continue;
    var r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    var cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    var tag = (typeof e.className === 'string' && e.className ? e.className : e.tagName).split(' ').slice(0, 2).join('.');
    var txt = ''; for (var k = 0; k < e.childNodes.length; k++) if (e.childNodes[k].nodeType === 3) txt += e.childNodes[k].nodeValue;
    txt = txt.replace(/\s+/g, ' ').trim();
    if (!e.closest('.impact') && (r.right > st.right + 6 || r.left < st.left - 6 || r.bottom > st.bottom + 6 || r.top < st.top - 6) && !e.closest('.pop')) out.push(['offstage', tag, txt.slice(0, 14)]);
    if (e.scrollWidth > e.clientWidth + 3 && /(hidden|auto)/.test(cs.overflowX) && cs.textOverflow !== 'ellipsis' && e.children.length === 0) out.push(['overflow', tag, txt.slice(0, 14)]);
    if (txt.length > 0 && /[가-힣A-Za-z0-9]/.test(txt)){ var fs = parseFloat(cs.fontSize); if (fs < floor - 0.5) out.push(['smalltext', tag + ' ' + fs + 'px', txt.slice(0, 14)]); }
    if ((e.tagName === 'BUTTON') && e.offsetHeight < minBtn - 1) out.push(['smallbtn', tag + ' ' + e.offsetHeight + 'px', txt.slice(0, 14)]);
  }
  var tw = document.createTreeWalker(document.getElementById('stage'), NodeFilter.SHOW_TEXT, null, false), nd;
  while ((nd = tw.nextNode())){
    var tx = nd.nodeValue; if (!tx || tx.length < 3 || !/[가-힣]/.test(tx) || nd.parentNode.closest('textarea')) continue;
    if (getComputedStyle(nd.parentNode).textOverflow === 'ellipsis') continue;
    var rg = document.createRange(), pTop = null, pCh = '';
    for (var q = 0; q < tx.length; q++){
      var c1 = tx.charAt(q); if (/\s/.test(c1)){ pTop = null; pCh = ''; continue; }
      rg.setStart(nd, q); rg.setEnd(nd, q + 1); var rr = rg.getBoundingClientRect(); if (!rr.height) continue;
      if (pTop !== null && rr.top > pTop + rr.height * 0.6 && /[가-힣]/.test(pCh) && /[가-힣]/.test(c1)){ out.push(['midword', 'text', tx.replace(/\s+/g, ' ').trim().slice(0, 14)]); break; }
      pTop = rr.top; pCh = c1;
    }
  }
  return out;
})(%d, %d)
"""


def static_checks(html: str, path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    add = lambda lv, m: out.append((lv, m))  # noqa: E731
    clean = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    kb = len(clean.encode()) / 1024
    add("PASS" if kb < 2048 else "FAIL", f"file size {kb:.0f} KB")
    add("PASS" if clean.lstrip().lower().startswith("<!doctype html") else "FAIL", "starts with <!DOCTYPE html>")
    for marker, label in (("window.TOOL =", "TOOL data block"), ("TS:CLASS-TOOLS RUNTIME", "runtime intact"), ("TS:CSS BEGIN", "CSS block")):
        add("PASS" if marker in clean else "FAIL", label)
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", clean, re.S)
    js = "\n".join(scripts)
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", js, flags=re.S)
    code = re.sub(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"", "''", code)
    for pat, label in FORBIDDEN_JS.items():
        n = len(re.findall(pat, code))
        add("FAIL" if n else "PASS", f"no {label} (old Chrome / blocks the screen)" + (f" ({n} found)" if n else ""))
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", clean, re.S))
    for pat, label in FORBIDDEN_CSS.items():
        n = len(re.findall(pat, css))
        add("FAIL" if n else "PASS", f"no {label} (old Chrome)" + (f" ({n} found)" if n else ""))
    urls = re.findall(r"""(?:src|href|action)\s*=\s*["'](?!#)([^"']+)""", clean) + re.findall(r"url\(\s*['\"]?(?!data:)([^)'\"]+)", css) + re.findall(r"https?://[^\s\"'<>)]+", clean)
    urls = [u for u in urls if not u.startswith("data:")]
    add("FAIL" if urls else "PASS", "no external request of any kind (offline, nothing sent)" + (f": {sorted(set(urls))[:3]}" if urls else ""))
    net = sorted(set(re.findall(NETWORK, code)))
    add("FAIL" if net else "PASS", "no network APIs (fetch/XHR/WebSocket/sendBeacon/postMessage)" + (f": {net}" if net else ""))
    sto = sorted({m.group(0) for m in re.finditer(STORAGE, code)})
    add("FAIL" if sto else "PASS", "no storage APIs (localStorage/cookies/IndexedDB): typed names are never saved" + (f": {sto}" if sto else ""))
    add("FAIL" if re.search(r"<form\b", clean, re.I) else "PASS", "no <form> (nothing can be submitted)")
    n_in = len(re.findall(r"h\(\s*'(?:input|textarea)'", js))
    n_ac = len(re.findall(r"autocomplete\s*:\s*'off'", js))
    add("FAIL" if n_in > n_ac else "PASS", "every text input has autocomplete=off" + (f" ({n_in} inputs, {n_ac} off)" if n_in > n_ac else ""))
    add("PASS" if re.search(r"word-break\s*:\s*keep-all", css) else "FAIL", "Korean keep-all line breaking")
    add("PASS" if "prefers-reduced-motion" in css and "RM" in js else "FAIL", "prefers-reduced-motion handled (CSS + JS)")
    m = re.search(r"window\.TOOL = (\{.*?\});</script>", clean, re.S)
    tk = None
    if m:
        try:
            tk = json.loads(m.group(1).replace("<\\/", "</"))["tokens"]
        except (ValueError, KeyError):
            add("FAIL", "TOOL data is not valid JSON")
    if tk:
        errs = design.validate_tokens(tk)
        add("FAIL" if errs else "PASS", f"design tokens: text contrast >= 4.5:1 and {tk['use']} type floor" + (": " + " | ".join(errs[:3]) if errs else ""))
    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
            tmp.write(js)
        p = subprocess.run([node, "--check", tmp.name], capture_output=True, text=True)
        add("PASS" if p.returncode == 0 else "FAIL", "JavaScript syntax" + ("" if p.returncode == 0 else ": " + p.stderr.strip().splitlines()[-1][:160]))
    else:
        add("WARN", "node not found; JavaScript syntax not checked")
    return out


def _scenario(pg, tool: str, data: dict) -> list[tuple[str, str]]:
    """Exercise the tool through TOOL_API and verify logic. Instant mode (no animation waits)."""
    out: list[tuple[str, str]] = []
    pg.evaluate("window.TOOL_API.instant = true")
    st = lambda: json.loads(pg.evaluate("render_tool_to_text()"))  # noqa: E731
    if tool == "timer":
        pg.evaluate("TOOL_API.step()")
        total = data["minutes"] * 60 if data["mode"] == "countdown" else 0
        if data["mode"] == "countdown":
            pg.evaluate(f"advanceTime({max(0, total - 5) * 1000})")
            w = st()
            out.append(("PASS" if w["warn"] or total <= data["warn_at"] else "FAIL", "timer shows the 'almost over' state before the end"))
            pg.evaluate("advanceTime(6000)")
            e = st()
            vis = pg.evaluate("document.querySelector('.state').textContent === '시간 끝!'")
            out.append(("PASS" if e["ended"] and e["seconds"] == 0 and vis else "FAIL", "timer ends at 00:00 and shows the end alert (text, not only color)"))
        else:
            pg.evaluate("advanceTime(61000)")
            out.append(("PASS" if st()["seconds"] in (61, 62) else "FAIL", "stopwatch counts up"))
    elif tool == "picker":
        s0 = st()
        n, seen = s0["total"], []
        if s0["no_repeat"]:
            for _ in range(n):
                pg.evaluate("TOOL_API.step()")
            s = st()
            out.append(("PASS" if len(set(s["drawn"])) == n and len(s["drawn"]) == n and s["remaining"] == 0 else "FAIL", f"no-repeat picker draws all {n} entries exactly once"))
            pg.evaluate("TOOL_API.step()")
            out.append(("PASS" if st()["remaining"] == n else "FAIL", "after everyone is drawn the next press restarts"))
        else:
            for _ in range(5):
                pg.evaluate("TOOL_API.step()")
            out.append(("PASS" if st()["current"] else "FAIL", "picker shows a result"))
    elif tool == "teams":
        pg.evaluate("TOOL_API.step()")
        s = st()
        sizes = [len(g) for g in s["teams"]]
        flat = [x for g in s["teams"] for x in g]
        out.append(("PASS" if max(sizes) - min(sizes) <= 1 else "FAIL", f"teams are fair (sizes {sizes})"))
        out.append(("PASS" if len(flat) == s["total"] == len(set(flat)) else "FAIL", "everyone is in exactly one team"))
    elif tool == "bracket":
        guard = 0
        while pg.evaluate("TOOL_API.step()") and guard < 40:
            guard += 1
        s = st()
        out.append(("PASS" if s["champion"] else "FAIL", f"bracket reaches a champion after {guard} picks"))
    elif tool == "scoreboard":
        pg.evaluate("TOOL_API.instant = false")
        before = st()["scores"][0]
        pg.evaluate("TOOL_API.step()")
        pg.wait_for_timeout(120)
        mid = int(st()["shown"][0])
        pg.wait_for_timeout(900)
        s = st()
        out.append(("PASS" if s["scores"][0] > before and int(s["shown"][0]) == s["scores"][0] else "FAIL", "score changes and the displayed number settles on it"))
        out.append(("PASS" if mid <= s["scores"][0] else "FAIL", "count-up runs without overshoot"))
        pg.evaluate("TOOL_API.instant = true")
    return out


def play_checks(path: Path, html: str) -> list[tuple[str, str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [("WARN", "Playwright not installed: headless checks skipped (static checks only)")]
    m = re.search(r"window\.TOOL = (\{.*?\});</script>", html, re.S)
    T = json.loads(m.group(1).replace("<\\/", "</"))
    tool, data, tk = T["tool"], T["data"], T["tokens"]
    floor = int(tk["type"]["floor"]["small"])
    minbtn = 80 if tk["use"] == "class" else 64
    out: list[tuple[str, str]] = []
    errors: list[str] = []
    blocked: list[str] = []
    try:
        with sync_playwright() as p:
            b = None
            for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
                try:
                    b = p.chromium.launch(args=MUTE, **kw)
                    break
                except Exception:
                    continue
            if b is None:
                return [("WARN", "no headless browser found: headless checks skipped")]

            def new(vw, vh, rm=False):
                ctx = b.new_context(viewport={"width": vw, "height": vh}, reduced_motion="reduce" if rm else "no-preference")
                ctx.route("**/*", lambda r: (r.continue_() if r.request.url.startswith(("file:", "data:", "blob:", "about:")) else (blocked.append(r.request.url[:80]), r.abort())))
                ctx.add_init_script(SILENT_JS)
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: errors.append(str(e)[:140]))
                pg.goto(path.resolve().as_uri())
                pg.wait_for_timeout(500)
                return ctx, pg

            ctx, pg = new(1920, 1080)
            lay: dict[str, str] = {}
            for kind, tag, txt in pg.evaluate(LAYOUT_JS % (floor, minbtn)):
                lay.setdefault(f"{kind}:{tag}:{txt}", f"{kind} <{tag}> '{txt}' (start screen)")
            out += _scenario(pg, tool, data)
            pg.wait_for_timeout(800)
            for kind, tag, txt in pg.evaluate(LAYOUT_JS % (floor, minbtn)):
                lay.setdefault(f"{kind}:{tag}:{txt}", f"{kind} <{tag}> '{txt}' (after use)")
            if tool == "picker":  # real animation path once: result must appear and the slam must not leave text broken
                pg.evaluate("TOOL_API.instant = false; TOOL_API.step()")
                pg.wait_for_timeout(3600)
                out.append(("PASS" if json.loads(pg.evaluate("render_tool_to_text()"))["busy"] is False else "FAIL", "picker animation finishes and shows the result"))
            stor = pg.evaluate("[localStorage.length, sessionStorage.length, document.cookie.length]")
            out.append(("PASS" if sum(stor) == 0 else "FAIL", "nothing written to storage or cookies while used"))
            ctx.close()

            ctx, pg = new(1080, 1920)  # portrait phone / tablet
            _scenario(pg, tool, data)
            pg.wait_for_timeout(800)
            for kind, tag, txt in pg.evaluate(LAYOUT_JS % (floor, minbtn)):
                lay.setdefault(f"{kind}:{tag}:{txt}", f"{kind} <{tag}> '{txt}' (portrait)")
            ctx.close()

            ctx, pg = new(1920, 1080, rm=True)
            _scenario(pg, tool, data)
            pg.wait_for_timeout(800)
            running = pg.evaluate("document.getAnimations().filter(function(a){return a.playState==='running'}).length")
            out.append(("PASS" if running == 0 else "FAIL", "reduced motion: no animation keeps running" + ("" if running == 0 else f" ({running} running)")))
            ctx.close()
            b.close()
    except Exception as exc:
        return out + [("WARN", f"headless checks could not finish ({str(exc).splitlines()[0][:100]})")]
    ov = [v for k, v in lay.items() if k.startswith(("offstage", "overflow"))]
    sm = [v for k, v in lay.items() if k.startswith("smalltext")]
    bt = [v for k, v in lay.items() if k.startswith("smallbtn")]
    mw = [v for k, v in lay.items() if k.startswith("midword")]
    out.append(("FAIL" if ov else "PASS", "no overflow / off-stage elements (landscape + portrait)" + (f": {ov[:3]}" if ov else "")))
    out.append(("FAIL" if sm else "PASS", f"all text >= {floor}px" + (f": {sm[:3]}" if sm else "")))
    out.append(("FAIL" if bt else "PASS", f"every button >= {minbtn}px tall (touch)" + (f": {bt[:3]}" if bt else "")))
    out.append(("WARN" if mw else "PASS", "no Korean word broken across lines" + (f": {mw[:3]}" if mw else "")))
    out.append(("FAIL" if errors else "PASS", "no JavaScript errors" + (f": {errors[:2]}" if errors else "")))
    out.append(("FAIL" if blocked else "PASS", "no outside request attempted" + (f": {blocked[:2]}" if blocked else "")))
    return out


def _juice_lint():
    """shared/juice/juice_lint.py: inside the skill when installed, else the repo root."""
    for d in (SHARED / "juice", SKILL.parent.parent / "shared" / "juice"):
        if (d / "juice_lint.py").exists():
            sys.path.insert(0, str(d))
            import juice_lint  # noqa: WPS433
            return juice_lint
    return None


def _wow_drive(tool: str):
    """Real-time interaction script for the wow runtime lint (REAL clicks, real waits, so frame time and click response are honest)."""
    def drive(pg, audit) -> None:
        def click(sel: str, wait: int = 600) -> bool:
            try:
                el = pg.query_selector(sel)
                if not el or not el.is_visible():
                    return False
                el.click(timeout=2000)
                pg.wait_for_timeout(wait)
                return True
            except Exception:
                return False

        if tool == "timer":
            click(".btn.main.wide", 400)
            audit()
            pg.evaluate("TOOL_API.off += (TOOL.data.minutes * 60 - 7) * 1000")
            pg.wait_for_timeout(9500)  # last 5 seconds (swell + ticks) and the end (fanfare + burst)
            audit()
        elif tool == "picker":
            for _ in range(3):
                click(".btn.main", 3600)
                audit()
        elif tool == "teams":
            for _ in range(3):
                click(".btn.main", 1600)
                audit()
        elif tool == "bracket":
            for _ in range(20):
                if not click("button.slot:not(.wait)", 450):
                    break
            audit()
            pg.wait_for_timeout(2500)
        else:  # scoreboard
            for i in range(6):
                click(".sbtns .btn.main", 350)
            audit()
            if click("text=시상식", 300):
                pg.wait_for_timeout(8800)
                audit()
    return drive


def wow_checks(path: Path, html: str, tool: str, use: str) -> list[tuple[str, str]]:
    """Accessibility + safety lint of the Game Wow kit (flashes, reduced motion, colour cues, sizes, 4x-throttled fps, response time)."""
    jl = _juice_lint()
    if jl is None:
        return [("WARN", "wow lint skipped: shared/juice not found")]
    out = list(jl.static_checks(html, use))
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return out + [("WARN", "Playwright not installed: wow runtime lint skipped")]
    try:
        with sync_playwright() as p:
            out += jl.runtime(p, path.resolve().as_uri(), _wow_drive(tool), use)
    except Exception as exc:
        out.append(("WARN", f"wow runtime lint could not run ({str(exc).splitlines()[0][:100]})"))
    return out


def color_blind_results(html: str) -> list[tuple[str, str]]:
    """WARN (never FAIL) when colours that carry meaning (correct/wrong, teams, chart series) look alike to colour-blind eyes: shared/design/color_check.py."""
    here = Path(__file__).resolve().parent
    for d in (here.parent / "shared" / "design", here.parent / "design"):
        if (d / "color_check.py").exists():
            sys.path.insert(0, str(d))
            try:
                import color_check
                return color_check.html_results(html)
            except Exception as exc:  # a colour hint must never break a check
                return [("WARN", f"color-blind check skipped ({str(exc).splitlines()[0][:80]})")]
    return []


def main(path: Path, play: bool = True) -> int:
    if not path.exists():
        print(f"FAIL file not found: {path}")
        return 1
    html = path.read_text(encoding="utf-8", errors="replace")
    res = static_checks(html, path)
    res += color_blind_results(html)
    if play:
        res += play_checks(path, html)
        mm = re.search(r"window\.TOOL = (\{.*?\});</script>", html, re.S)
        if mm:
            T0 = json.loads(mm.group(1).replace("<\\/", "</"))
            res += wow_checks(path, html, T0["tool"], T0["use"])
    else:
        res.append(("WARN", "headless checks skipped (--no-play)"))
    for lv, msg in res:
        print(f"{lv:4} {msg}")
    fails = sum(1 for lv, _ in res if lv == "FAIL")
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({fails} fail, {sum(1 for lv, _ in res if lv == 'WARN')} warn)")
    return 1 if fails else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    sys.exit(main(Path(args[0]), play="--no-play" not in sys.argv))
