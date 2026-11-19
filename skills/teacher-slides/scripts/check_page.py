#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Static quality check for a Teacher Studio game HTML game.

Usage: python3 check_game.py game.html [--no-play]
Games built by build.py (spec path) also get spec/token/text-size/bias checks and a headless autoplay (needs Playwright; --no-play skips it).
Prints PASS/WARN/FAIL lines and exits 1 if any FAIL.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")  # tests stay silent
MUTE = ["--mute-audio"]
sys.path.insert(0, str(HERE))

# Windows consoles (cp949) cannot encode emoji/check marks: never crash on output.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(errors="replace")

ALLOWED_HOSTS = ("cdnjs.cloudflare.com", "cdn.jsdelivr.net/npm/", "unpkg.com", "fonts.googleapis.com", "fonts.gstatic.com")
FORBIDDEN_JS = {
    r"\?\.(?=[A-Za-z_$\[(])": "optional chaining ?. (old Chrome)",
    r"\?\?": "nullish ?? (old Chrome)",
    r"\.replaceAll\(": "replaceAll (old Chrome)",
    r"\.at\(\s*-?\d": ".at() (old Chrome)",
    r"structuredClone\(": "structuredClone (old Chrome)",
    r"(?<![\w$])#[a-zA-Z_]\w*\s*[=(;]": "#private field (old Chrome)",
    r"\balert\(|\bprompt\(|\bconfirm\(": "alert/prompt/confirm blocks the game",
}
FORBIDDEN_CSS = {
    r"aspect-ratio\s*:": "aspect-ratio (old Chrome)",
    r":has\(": ":has() (old Chrome)",
    r"\b\d+(\.\d+)?dvh\b": "dvh unit (old Chrome)",
}
MODERN_LIBS = {"motion"}  # vendored libs that use ?. / ?? (reported as a warning, not a failure)
STUDENT_DATA = re.compile(r"(학번|이름을?\s*입력|실명|student\s*name|전화번호)", re.I)


def _bracket_body(src: str, i: int) -> str:
    """Return the text inside the [ ... ] that opens at index i."""
    depth, quote, prev = 0, "", ""
    for j in range(i, len(src)):
        ch = src[j]
        if quote:
            if ch == quote and prev != "\\":
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                return src[i + 1:j]
        prev = ch
    return src[i + 1:]


def _top_level_objects(src: str) -> int:
    """Count {...} objects at depth 0 of an array body (ignores braces inside strings)."""
    depth, n, quote, prev = 0, 0, "", ""
    for ch in src:
        if quote:
            if ch == quote and prev != "\\":
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            if depth == 0:
                n += 1
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        prev = ch
    return n



GAME_RE = re.compile(r"window\.GAME = (\{.*?\n\});", re.S)
FONT_PX = re.compile(r"font-size\s*:\s*(\d+(?:\.\d+)?)px")

OVERFLOW_JS = r"""
(function(floor){
  var out = [], st = document.getElementById('stage').getBoundingClientRect();
  var scene = document.querySelector('#scene .screen'); if (!scene) return out;
  var els = scene.querySelectorAll('*');
  for (var i = 0; i < els.length; i++){
    var e = els[i], r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    var cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    var tag = (typeof e.className === 'string' && e.className ? e.className : e.tagName).split(' ').slice(0, 2).join('.');
    var txt = ''; for (var k = 0; k < e.childNodes.length; k++) if (e.childNodes[k].nodeType === 3) txt += e.childNodes[k].nodeValue;
    txt = txt.replace(/\s+/g, ' ').trim();
    if (e.hasAttribute('data-fit') && (e.scrollWidth > e.clientWidth + 3 || e.scrollHeight > e.clientHeight + 3)) out.push(['overflow', tag, txt.slice(0, 14)]);
    if (!e.closest('.enter') && (r.right > st.right + 6 || r.left < st.left - 6 || r.bottom > st.bottom + 6 || r.top < st.top - 6)) out.push(['offstage', tag, txt.slice(0, 14)]);
    if (txt.length > 1 && /[가-힣A-Za-z0-9]/.test(txt)){ var fs = parseFloat(cs.fontSize); if (fs < floor - 0.5) out.push(['smalltext', tag + ' ' + fs + 'px', txt.slice(0, 14)]); }
  }
  /* a Korean word split across two lines (line ends inside a word) */
  var tw = document.createTreeWalker(scene, NodeFilter.SHOW_TEXT, null, false), nd;
  while ((nd = tw.nextNode())){
    var tx = nd.nodeValue; if (!tx || tx.length < 3 || !/[가-힣]/.test(tx)) continue;
    var rg = document.createRange(), pTop = null, pCh = '';
    for (var q = 0; q < tx.length; q++){
      var c1 = tx.charAt(q); if (/\s/.test(c1)){ pTop = null; pCh = ''; continue; }
      rg.setStart(nd, q); rg.setEnd(nd, q + 1); var rr = rg.getBoundingClientRect(); if (!rr.height) continue;
      if (pTop !== null && rr.top > pTop + rr.height * 0.6 && /[가-힣]/.test(pCh) && /[가-힣]/.test(c1)){ out.push(['midword', 'text', tx.replace(/\s+/g, ' ').trim().slice(0, 14)]); break; }
      pTop = rr.top; pCh = c1;
    }
  }
  return out;
})(%d)
"""


def spec_checks(html: str, path: Path, play: bool) -> list[tuple[str, str]]:
    """Checks for games built by build.py: spec rules, tokens, text floors, bias, forbidden input, autoplay."""
    import design
    import specs

    out: list[tuple[str, str]] = []
    m = GAME_RE.search(html)
    if not m:
        return [("FAIL", "GAME data not found (build.py output expected)")]
    try:
        game = json.loads(m.group(1))
    except ValueError as exc:
        return [("FAIL", f"GAME data is not valid JSON: {exc}")]
    sp = dict(game.get("spec") or {})
    tokens = sp.get("tokens")
    if not tokens:
        return [("FAIL", "spec.tokens missing -> rebuild with scripts/build.py")]
    spec = {k: v for k, v in sp.items() if k != "tokens"}
    spec["items"], spec["title"], spec["subtitle"] = game.get("items", []), game.get("title", ""), game.get("subtitle", "")
    errs = specs.validate(spec)
    out.append(("FAIL" if errs else "PASS", "spec rules" + ("" if not errs else ": " + " | ".join(errs[:4]))))
    terr = design.validate_tokens(tokens)
    out.append(("FAIL" if terr else "PASS", "design tokens: text contrast >= 4.5:1 and %s type floor" % tokens["use"] + ("" if not terr else ": " + " | ".join(terr[:4]))))
    bias = specs.answer_bias(spec["items"])
    out.append(("WARN" if bias else "PASS", "answer positions balanced" + (f": {bias}" if bias else "")))
    fl = tokens["type"]["floor"]
    comp = "\n".join(re.findall(r"/\* TS:COMPONENTS BEGIN \*/(.*?)/\* TS:COMPONENTS END \*/", html, re.S) + re.findall(r"/\* TS:CSS BEGIN \*/(.*?)/\* TS:CSS END \*/", html, re.S))
    small = sorted({float(x) for x in FONT_PX.findall(comp) if float(x) < fl["small"]})
    out.append(("FAIL" if small else "PASS", f"component text sizes >= {fl['small']}px" + (f": found {small} -> raise the type scale (design.large) or shorten the text" if small else "")))
    if re.search(r"<input|<textarea|contenteditable", comp):
        out.append(("FAIL", "no text input fields in game components (student-info rule)"))
    if play:
        out += autoplay(path, tokens)
        out += wow_checks(path, tokens, html)
    else:
        out.append(("WARN", "autoplay skipped (--no-play)"))
    return out


def _juice_lint():
    """shared/juice/juice_lint.py: inside the skill when installed, else the repo root."""
    for d in (HERE.parent / "shared" / "juice", HERE.parent.parent.parent / "shared" / "juice"):
        if (d / "juice_lint.py").exists():
            sys.path.insert(0, str(d))
            import juice_lint  # noqa: WPS433
            return juice_lint
    return None


def _wow_drive(pg, audit) -> None:
    """Play in REAL time (effects need real frames): countdown, up to 16 answers/nexts, then force the finale (reveal/podium/confetti)."""
    pg.click("#t-start")
    pg.wait_for_timeout(4000)
    audit()
    for i in range(16):
        try:
            if json.loads(pg.evaluate("render_game_to_text()"))["scene"] == "result":
                break
            pg.evaluate("window.GAME_LOGIC.auto()")
        except Exception:
            break
        pg.wait_for_timeout(1100)
        if i % 3 == 0:
            audit()
    try:
        if json.loads(pg.evaluate("render_game_to_text()"))["scene"] != "result":
            pg.evaluate("NG.finish({total: Math.max(1, NG.state.total || 1)})")
    except Exception:
        pass
    pg.wait_for_timeout(8000)
    audit()


def wow_checks(path: Path, tokens: dict, html: str) -> list[tuple[str, str]]:
    """Accessibility + safety lint of the Game Wow kit (flashes, reduced motion, colour cues, sizes, fps, response time)."""
    jl = _juice_lint()
    if jl is None:
        return [("WARN", "wow lint skipped: shared/juice not found")]
    out = list(jl.static_checks(html, tokens.get("use", "class")))
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return out + [("WARN", "Playwright not installed: wow runtime lint skipped")]
    try:
        with sync_playwright() as p:
            out += jl.runtime(p, path.resolve().as_uri(), _wow_drive, tokens.get("use", "class"))
    except Exception as exc:
        out.append(("WARN", f"wow runtime lint could not run ({str(exc).splitlines()[0][:100]})"))
    return out


def autoplay(path: Path, tokens: dict) -> list[tuple[str, str]]:
    """Play the game headlessly through GAME_LOGIC.auto(); report stalls, JS errors, overflow, small text."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [("WARN", "Playwright not installed: autoplay skipped (static checks only)")]
    problems: dict[str, str] = {}
    errors: list[str] = []
    final, steps, idle = "", 0, 0
    floor = int(tokens["type"]["floor"]["small"])
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
                return [("WARN", "no headless browser found (playwright chromium / Chrome / Edge): autoplay skipped, static checks only")]
            pg = b.new_page(viewport={"width": 1920, "height": 1080})
            pg.add_init_script(SILENT_JS)
            pg.on("pageerror", lambda e: errors.append(str(e)[:160]))
            pg.goto(path.resolve().as_uri())
            pg.wait_for_timeout(600)
            pg.click("#t-start")
            pg.wait_for_timeout(3700)
            while steps < 500:
                st = json.loads(pg.evaluate("render_game_to_text()"))
                final = st["scene"]
                if final == "result":
                    break
                acted = pg.evaluate("window.GAME_LOGIC.auto()")
                idle = 0 if acted else idle + 1
                if idle > 25:
                    break
                pg.wait_for_timeout(260)
                pg.evaluate("advanceTime(600)")
                pg.wait_for_timeout(260)
                now = json.loads(pg.evaluate("render_game_to_text()"))["scene"]
                if now == final and final not in ("title", "countdown", "result"):
                    for kind, tag, txt in pg.evaluate(OVERFLOW_JS % floor):
                        problems.setdefault(f"{kind}:{tag}:{txt}", f"{kind} in scene {final}: <{tag}> '{txt}'")
                steps += 1
            b.close()
    except Exception as exc:  # browser missing etc.
        return [("WARN", f"autoplay could not run ({str(exc).splitlines()[0][:100]}): static checks only")]
    out: list[tuple[str, str]] = []
    out.append(("PASS" if final == "result" else "FAIL", f"autoplay reaches the result screen ({steps} steps)" + ("" if final == "result" else f": stuck at scene '{final}' -> check item counts/answers in the spec")))
    out.append(("FAIL" if errors else "PASS", "no JavaScript errors while playing" + (f": {errors[:2]}" if errors else "")))
    ov = [v for k, v in problems.items() if k.startswith(("overflow", "offstage"))]
    sm = [v for k, v in problems.items() if k.startswith("smalltext")]
    out.append(("FAIL" if ov else "PASS", "no text overflow / off-stage elements" + (f": {ov[:3]} -> shorten the text or use fewer choices" if ov else "")))
    mw = [v for k, v in problems.items() if k.startswith("midword")]
    out.append(("WARN" if mw else "PASS", "no Korean word broken across lines" + (f": {mw[:3]} -> shorten the text so words are not split" if mw else "")))
    out.append(("FAIL" if sm else "PASS", f"all in-game text >= {floor}px" + (f": {sm[:3]}" if sm else "")))
    return out


def main(path: Path, play: bool = True) -> int:
    """Run all checks and print a report. Returns process exit code."""
    if not path.exists():
        print(f"FAIL file not found: {path}")
        return 1
    html = path.read_text(encoding="utf-8", errors="replace")
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)  # ignore HTML comments
    results: list[tuple[str, str]] = []

    def add(level: str, msg: str) -> None:
        results.append((level, msg))

    size_kb = len(html.encode()) / 1024
    add("PASS" if size_kb < 2048 else "FAIL", f"file size {size_kb:.0f} KB")
    add("PASS" if html.lstrip().lower().startswith("<!doctype html") else "FAIL", "starts with <!DOCTYPE html>")
    is_stage = "STAGE RUNTIME (do not edit" in html
    markers = (
        (("window.DOC =", "DOC data block"), ("window.SHOW", "SHOW block"), ("STAGE.boot()", "STAGE.boot() call"),
         ("STAGE RUNTIME (do not edit", "stage runtime intact"), ("b-full", "fullscreen button kept"),
         ("Anime.js", "anime.js inlined"))
        if is_stage else
        (("window.GAME =", "GAME data block"), ("window.GAME_LOGIC", "GAME_LOGIC block"),
         ("NG.boot()", "NG.boot() call"), ("ENGINE (do not edit", "engine block intact"),
         ("ng-mute", "mute button kept"), ("Teacher.open", "teacher menu kept"))
    )
    for marker, label in markers:
        add("PASS" if marker in html else "FAIL", label)

    # Vendored libraries (shared/vendor, pinned + license-checked) are third-party code: not linted line by line.
    for kind, lib, ver in re.findall(r"<(script|style)>/\* TS:VENDOR (\S+) (\S+)", html):
        if lib in MODERN_LIBS and kind == "script":
            if "ts-allow-modern" in html:
                add("WARN", f"{lib} {ver} needs Chrome 80+ (2020); allowed on purpose (allow_modern), use anime.js/CSS for very old PCs")
            else:
                add("FAIL", f"{lib} {ver} needs Chrome 80+ but was not allowed -> remove it (use anime.js/CSS) or opt in with allow_modern:true / --allow-modern")
    html = re.sub(r"<(script|style)>/\* TS:VENDOR .*?</\1>", r"<\1></\1>", html, flags=re.S)
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
    js = "\n".join(scripts)
    js_nostr = re.sub(r"//[^\n]*|/\*.*?\*/", "", js, flags=re.S)
    js_nostr = re.sub(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"", "''", js_nostr)
    for pat, label in FORBIDDEN_JS.items():
        hits = len(re.findall(pat, js_nostr))
        add("FAIL" if hits else "PASS", f"no {label}" + (f" ({hits} found)" if hits else ""))
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)) + "\n" + " ".join(re.findall(r'style="([^"]*)"', html))
    for pat, label in FORBIDDEN_CSS.items():
        hits = len(re.findall(pat, css))
        add("FAIL" if hits else "PASS", f"no {label}" + (f" ({hits} found)" if hits else ""))

    urls = re.findall(r"""(?:src|href)\s*=\s*["'](https?://[^"']+)""", html) + re.findall(r"url\(\s*['\"]?(https?://[^)'\"]+)", html)
    bad = sorted({u for u in urls if not any(h in u for h in ALLOWED_HOSTS)})
    add("FAIL" if bad else "PASS", "external resources only from cdnjs / jsdelivr npm / unpkg / Google Fonts" + (f": {bad[:3]}" if bad else ""))
    cdn = re.findall(r"cdnjs\.cloudflare\.com/ajax/libs/[^/]+/([^/]+)/", html)
    cdn += re.findall(r"cdn\.jsdelivr\.net/npm/(?:@[^/]+/)?[^@/]+@([^/]+)/", html)
    if any(not re.match(r"\d+\.\d+", v) for v in cdn):
        add("FAIL", "cdnjs URLs must pin an exact version")
    if re.search(r"<img[^>]+src=[\"']https?:", html):
        add("FAIL", "no external <img>")
    if re.search(r"\bdraggable\s*=\s*[\"']?true", html) or "dragstart" in js_nostr:
        add("WARN", "HTML5 drag API does not work on tablets; use NG.drag")
    if STUDENT_DATA.search(html):
        add("WARN", "possible student personal data field (이름/학번) — remove unless clearly fictional")
    logs = len(re.findall(r"console\.log\(", js_nostr))
    if logs:
        add("WARN", f"{logs} console.log left")

    g = -1 if is_stage else html.find("window.GAME")
    m = re.compile(r"[\"']?items[\"']?\s*:\s*\[").search(html, g) if g >= 0 else None
    count = _top_level_objects(_bracket_body(html, m.end() - 1)) if m else 0
    add("PASS" if count or not m else "WARN", f"GAME.items has {count} entries")

    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
            tmp.write(js)
        proc = subprocess.run([node, "--check", tmp.name], capture_output=True, text=True)
        add("PASS" if proc.returncode == 0 else "FAIL", "JavaScript syntax" + ("" if proc.returncode == 0 else ": " + proc.stderr.strip().splitlines()[-1][:160]))
    else:
        add("WARN", "node not found; JavaScript syntax not checked")

    if "TS:BUILD" in html:
        for level, msg in spec_checks(html, path, play):
            add(level, msg)

    for level, msg in results:
        print(f"{level:4} {msg}")
    fails = sum(1 for lv, _ in results if lv == "FAIL")
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({fails} fail, {sum(1 for lv, _ in results if lv == 'WARN')} warn)")
    return 1 if fails else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    sys.exit(main(Path(args[0]), play="--no-play" not in sys.argv))
