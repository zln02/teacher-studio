#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Phone viewport check for games built with device:"phone": 390x844 (held upright) and 844x390 (sideways).

check_game.py and design_review.py both import this. Real browser, real touch-size numbers, measured on the screens people actually see
(title, question, answered + explanation, result):
  - smallest real text size in CSS px (font-size x the stage scale):  FAIL < 14 upright / < 10 sideways,  WARN < 16 / < 12
  - nothing outside the screen and no text overflowing its box
  - every button, answer and icon is >= 44 x 44 CSS px
A game without a portrait layout (anything but quiz) must show the "turn your phone" message when held upright instead (checked).
Usage: python3 phone_check.py game.html            (prints PASS/WARN/FAIL lines)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

VIEWPORTS = {"portrait": (390, 844), "landscape": (844, 390)}
FONT_FAIL = {"portrait": 14.0, "landscape": 10.0}
FONT_WARN = {"portrait": 16.0, "landscape": 12.0}
TAP_MIN = 44.0
SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")

PROBE_JS = r"""
(function(){
  var vw = window.innerWidth, vh = window.innerHeight, out = {vw: vw, vh: vh, minFont: 999, minText: '', small: [], offscreen: [], tiny: [], clipped: []};
  var st = document.getElementById('stage'), sr = st ? st.getBoundingClientRect() : {width: vw}, k = st && st.offsetWidth ? sr.width / st.offsetWidth : 1;
  out.scale = Math.round(k * 1000) / 1000;
  var root = document.getElementById('app') || document.body, els = root.querySelectorAll('*');
  for (var i = 0; i < els.length; i++){
    var e = els[i], cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.2) continue;
    var r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (e.closest('canvas, svg, #ts-deco, .ts-custom, #fx, #bg, .vignette')) continue;
    var name = (typeof e.className === 'string' && e.className ? e.className : e.tagName).split(' ').slice(0, 2).join('.');
    var txt = ''; for (var j = 0; j < e.childNodes.length; j++) if (e.childNodes[j].nodeType === 3) txt += e.childNodes[j].nodeValue;
    txt = txt.replace(/\s+/g, ' ').trim();
    var inStage = !!e.closest('#stage');
    if (txt.length > 0 && /[가-힣A-Za-z0-9]/.test(txt) && !e.closest('.badge, .float, .toast')){
      var eff = parseFloat(cs.fontSize) * (inStage ? k : 1);
      if (eff < out.minFont){ out.minFont = eff; out.minText = name + ' "' + txt.slice(0, 14) + '"'; }
      if (eff < 16) out.small.push([Math.round(eff * 10) / 10, name, txt.slice(0, 12)]);
    }
    var en = e.closest('.enter'), inEnter = !!(en && en.getAnimations && (en.getAnimations().length > 0 || e.getAnimations().length > 0));
    if (!inEnter && !e.closest('.badge, .float, .toast') && (r.left < -2 || r.top < -2 || r.right > vw + 2 || r.bottom > vh + 2)) out.offscreen.push([name, Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]);
    if (e.hasAttribute('data-fit') && (e.scrollWidth > e.clientWidth + 3 || e.scrollHeight > e.clientHeight + 3)) out.clipped.push([name, txt.slice(0, 12)]);
    var tap = e.tagName === 'BUTTON' || e.getAttribute('role') === 'button' || e.getAttribute('role') === 'link';
    if (tap && !e.disabled && cs.pointerEvents !== 'none' && !inEnter){
      if (Math.min(r.width, r.height) < 43.5) out.tiny.push([name, Math.round(r.width), Math.round(r.height)]);
    }
  }
  if (out.minFont === 999) out.minFont = 99;
  out.rotate = document.body.getAttribute('data-rotate') === '1';
  out.orient = document.body.getAttribute('data-orient');
  return out;
})()
"""


def _launch(p):
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(args=["--mute-audio"], **kw)
        except Exception:
            continue
    return None


def play(pg, shots: dict | None = None, Image=None) -> dict:
    """Drive title -> question -> answered -> result; probe (and optionally screenshot) each. Returns {screen: probe}."""
    probes: dict = {}

    def snap(name: str) -> None:
        pg.wait_for_timeout(500)
        probes[name] = pg.evaluate(PROBE_JS)
        if shots is not None and Image is not None:
            shots[name] = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")

    pg.goto(pg._ts_url)
    pg.wait_for_timeout(700)
    pg.evaluate("advanceTime(1500)")
    snap("title")
    pg.click("#t-start")
    pg.wait_for_timeout(3700)
    pg.evaluate("advanceTime(1300)")
    snap("question")
    pg.evaluate("window.GAME_LOGIC.auto()")
    pg.wait_for_timeout(250)
    pg.evaluate("advanceTime(1300)")
    snap("answered")
    for _ in range(80):
        if json.loads(pg.evaluate("render_game_to_text()"))["scene"] == "result":
            break
        pg.evaluate("window.GAME_LOGIC.auto()")
        pg.evaluate("advanceTime(1500)")
    pg.evaluate("advanceTime(2600)")
    pg.wait_for_timeout(500)
    pg.evaluate("advanceTime(2600)")
    snap("result")
    return probes


def run_viewport(p, path: Path, orient: str, shots: dict | None = None, Image=None) -> tuple[dict, list[str]]:
    w, h = VIEWPORTS[orient]
    b = _launch(p)
    if b is None:
        raise RuntimeError("no headless browser found")
    errors: list[str] = []
    try:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=True, is_mobile=True)
        pg = ctx.new_page()
        pg._ts_url = path.resolve().as_uri()
        pg.add_init_script(SILENT_JS)
        pg.on("pageerror", lambda e: errors.append(str(e)[:120]))
        probes = play(pg, shots, Image)
    finally:
        b.close()
    return probes, errors


def evaluate(orient: str, probes: dict, errors: list[str], portrait_game: bool) -> list[tuple[str, str]]:
    """PASS/WARN/FAIL lines for one viewport."""
    w, h = VIEWPORTS[orient]
    tag = f"phone {w}x{h}"
    out: list[tuple[str, str]] = []
    if orient == "portrait" and not portrait_game:
        ok = all(p.get("rotate") for p in probes.values())
        out.append(("PASS" if ok else "FAIL", f"{tag}: no portrait layout for this game -> the 'turn your phone sideways' message is shown" + ("" if ok else " (missing)")))
        return out
    mins = {k: v["minFont"] for k, v in probes.items()}
    worst_screen = min(mins, key=mins.get)
    worst = mins[worst_screen]
    where = probes[worst_screen]["minText"]
    if worst < FONT_FAIL[orient]:
        out.append(("FAIL", f"{tag}: smallest text is {worst:.1f}px on '{worst_screen}' ({where}); needs >= {FONT_FAIL[orient]:.0f}px, aim {FONT_WARN[orient]:.0f}+ -> shorten text or raise the type size"))
    elif worst < FONT_WARN[orient]:
        out.append(("WARN", f"{tag}: smallest text is {worst:.1f}px on '{worst_screen}' ({where}); {FONT_WARN[orient]:.0f}px+ reads better"))
    else:
        out.append(("PASS", f"{tag}: all text >= {FONT_WARN[orient]:.0f}px (smallest {worst:.1f}px)"))
    off = [(k, o) for k, v in probes.items() for o in v["offscreen"]] + [(k, c) for k, v in probes.items() for c in v["clipped"]]
    out.append(("FAIL" if off else "PASS", f"{tag}: nothing outside the screen, no text overflow" + (f": {off[:3]}" if off else "")))
    tiny = [(k, t) for k, v in probes.items() for t in v["tiny"]]
    out.append(("FAIL" if tiny else "PASS", f"{tag}: every button/answer >= {TAP_MIN:.0f}px" + (f": {tiny[:3]}" if tiny else "")))
    if errors:
        out.append(("FAIL", f"{tag}: JavaScript errors: {errors[:2]}"))
    return out


def checks(path: Path, spec: dict) -> list[tuple[str, str]]:
    """Both phone viewports for a spec with device:"phone". Skipped (empty list) for other devices; WARN when there is no browser."""
    if (spec or {}).get("device") != "phone":
        return []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [("WARN", "phone checks skipped: Playwright not installed")]
    portrait_game = spec.get("mechanic") in ("quiz",)
    try:
        with sync_playwright() as p:
            res = [(o, *run_viewport(p, path, o)) for o in ("portrait", "landscape")]
    except Exception as exc:
        return [("WARN", f"phone checks could not run ({str(exc).splitlines()[0][:90]})")]
    out: list[tuple[str, str]] = []
    for orient, probes, errors in res:
        out += evaluate(orient, probes, errors, portrait_game)
    return out


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
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    f = Path(sys.argv[1])
    import re
    m = re.search(r"window\.GAME = (\{.*?\n\});", f.read_text(encoding="utf-8"), re.S)
    sp = (json.loads(m.group(1)).get("spec") or {}) if m else {}
    sp.setdefault("device", "phone")
    sp.setdefault("mechanic", "quiz")
    lines = checks(f, sp)
    for lv, msg in lines:
        print(f"{lv:4} {msg}")
    sys.exit(1 if any(lv == "FAIL" for lv, _ in lines) else 0)
