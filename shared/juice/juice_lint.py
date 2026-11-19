# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Accessibility + safety lint for the Game Wow kit, shared by check_game.py and check_tool.py.

static_checks(html, use)           -> [(level, message)]   no browser needed
runtime(browser, url, drive, use)  -> [(level, message)]   real Chrome, CPU throttled 4x (CDP), audio stubbed + muted
  drive(page, audit)  is supplied by the caller: it plays the page in REAL time (clicks, waits) and calls audit() on screens worth auditing.

Rules (WCAG 2.2 / XAG 117 / classroom):
  flashes  <= 3 per second and flash area <= 341x256 CSS px (WCAG 2.3.1)   - the kit logs every flash; CSS loops faster than 3/s fail
  motion   prefers-reduced-motion honoured + an in-page "효과 줄이기" switch (XAG 117)
  colour   right/wrong is never colour alone (a symbol or words are always present)
  size     class use: body text >= 28px at 1080p; tap targets >= 44px
  speed    >= 30 fps with the CPU throttled 4x; first response <= 100 ms after a click
"""
from __future__ import annotations

import json
import re

SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")

# in-page recorders: frame times + "click -> next frame" latency (input delay + handler + frame = what the user feels, like INP)
INIT_JS = r"""
(function(){
  var W = window.__wow = {frames: [], resp: []};
  (function loop(ts){ W.frames.push(ts); if (W.frames.length > 20000) W.frames.splice(0, 5000); requestAnimationFrame(loop); })(0);
  document.addEventListener('click', function(e){
    var t0 = e.timeStamp || performance.now();
    requestAnimationFrame(function(){ W.resp.push(performance.now() - t0); });
  }, true);
})();
"""

# per-screen audit: tap targets, text size, right/wrong cues
AUDIT_JS = r"""
(function(useClass){
  var out = {tap: [], text: [], cue: []}, root = document.body;
  var SYM = /[✔✖✓✗✘❌⭕✅❎☑☒⭐✅💡🎉⚠]/;
  var els = root.querySelectorAll('button, [role=button], a, input, select, .btn, .choice, .ts-cell, .ts-tile, .ts-bin');
  for (var i = 0; i < els.length; i++){
    var e = els[i], r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.2 || e.closest('.juice-fx,[aria-hidden=true]')) continue;
    if (e.disabled || e.hasAttribute('data-nolint')) continue;
    if (Math.min(r.width, r.height) < 43.5) out.tap.push((e.id || (typeof e.className === 'string' ? e.className : e.tagName)).toString().slice(0, 30) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
  }
  if (useClass){
    var all = root.querySelectorAll('*');
    for (var j = 0; j < all.length; j++){
      var n = all[j], rr = n.getBoundingClientRect(), c2 = getComputedStyle(n);
      if (!rr.width || !rr.height || c2.visibility === 'hidden' || c2.display === 'none' || parseFloat(c2.opacity) < 0.2) continue;
      var txt = ''; for (var k = 0; k < n.childNodes.length; k++) if (n.childNodes[k].nodeType === 3) txt += n.childNodes[k].nodeValue;
      txt = txt.replace(/\s+/g, ' ').trim();
      if (txt.length > 1 && /[가-힣A-Za-z0-9]/.test(txt) && parseFloat(c2.fontSize) < 27.5) out.text.push(parseFloat(c2.fontSize) + 'px ' + txt.slice(0, 12));
    }
  }
  var st = root.querySelectorAll('[class*=correct], [class*=wrong]');
  for (var q = 0; q < st.length; q++){
    var s = st[q], cls = typeof s.className === 'string' ? s.className : '';
    if (!/(^|\s)(choice|btn|ts-cell|ts-tile|cell|card|slot|opt|item|key|lock)[\w-]*(\s|$)/.test(cls) && !/(^|\s)(correct|wrong)(\s|$)/.test(cls)) continue;
    var b = s.getBoundingClientRect(); if (b.width < 60 || b.height < 40) continue;
    var cs3 = getComputedStyle(s); if (cs3.display === 'none' || cs3.visibility === 'hidden') continue;
    var has = SYM.test(s.textContent || '') || !!s.querySelector('svg, img, .ts-sym') || (getComputedStyle(s, '::before').content || 'none') !== 'none' || (getComputedStyle(s, '::after').content || 'none') !== 'none';
    if (!has) out.cue.push(cls.slice(0, 40));
  }
  return out;
})(%s)
"""


def static_checks(html: str, use: str = "class", kit_expected: bool = True) -> list[tuple[str, str]]:
    """No-browser rules. `html` is the whole page."""
    out: list[tuple[str, str]] = []
    has_kit = "TS:JUICE v" in html
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    # 1. a CSS loop faster than 3 cycles per second is a flashing hazard (period < 0.34 s)
    fast: list[str] = []
    for m in re.finditer(r"animation(?:-duration)?\s*:\s*([^;}]*)", css):
        body = m.group(1)
        if "infinite" not in body and "animation-duration" not in m.group(0) and "alternate" not in body:
            continue
        d = re.search(r"(?<![\w.])(\d*\.?\d+)(ms|s)\b", body)
        if d and "infinite" in body:
            sec = float(d.group(1)) / (1000 if d.group(2) == "ms" else 1)
            if sec < 0.34 and "none" not in body.split()[:1]:
                fast.append(body.strip()[:40])
    out.append(("FAIL" if fast else "PASS", "no CSS loop faster than 3/second (WCAG 2.3.1 flashes)" + (f": {fast[:2]}" if fast else "")))
    # 2. reduced motion
    rm = "prefers-reduced-motion" in html
    out.append(("PASS" if rm else "FAIL", "honours prefers-reduced-motion" + ("" if rm else " -> add a @media (prefers-reduced-motion: reduce) rule or include the Game Wow kit")))
    # 3. in-game switches (XAG 117 + classroom sound control), visible words
    out.append(("PASS" if "효과 줄이기" in html else "FAIL", "in-game 「효과 줄이기」 switch present (XAG 117)"))
    out.append(("PASS" if "소리 끄기" in html else "FAIL", "in-game 「소리 끄기」 switch present"))
    if not has_kit:
        out.append(("WARN" if not kit_expected else "FAIL", "Game Wow kit (shared/juice) is not in this file: juice, flash governor and podium are missing"))
    else:
        out.append(("PASS", "Game Wow kit present (flash governor, reduced-motion fallbacks, ZzFX-style sounds)"))
    if re.search(r"https?://[^\"')\s]*(zzfx|tone)", html, re.I):
        out.append(("FAIL", "sound libraries must be inlined (no external requests)"))
    return out


def _fps(frames: list[float], start_ts: float) -> tuple[float, float, float]:
    """(average fps, median 1s-window fps, worst 1s-window fps)"""
    fr = [t for t in frames if t >= start_ts]
    if len(fr) < 10:
        return 0.0, 0.0, 0.0
    span = (fr[-1] - fr[0]) / 1000
    avg = (len(fr) - 1) / span if span > 0 else 0.0
    wins, t = [], fr[0]
    while t + 1000 <= fr[-1]:
        wins.append(float(sum(1 for x in fr if t <= x < t + 1000)))
        t += 500
    wins.sort()
    return round(avg, 1), (wins[len(wins) // 2] if wins else avg), (wins[0] if wins else avg)


def runtime(p, url: str, drive, use: str = "class", throttle: int = 4, viewport=(1920, 1080), need_kit: bool = True) -> list[tuple[str, str]]:
    """p = a started sync_playwright() instance. Returns lint lines (also attaches .metrics dict on the function for reports)."""
    b = None
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            b = p.chromium.launch(args=["--mute-audio"], **kw)
            break
        except Exception:
            continue
    if b is None:
        return [("WARN", "no headless browser: wow runtime lint skipped")]
    res: list[tuple[str, str]] = []
    agg = {"tap": set(), "text": set(), "cue": set()}
    m: dict = {}
    try:
        pg = b.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        pg.add_init_script(SILENT_JS)
        pg.add_init_script(INIT_JS)
        pg.goto(url)
        pg.wait_for_timeout(500)

        def audit() -> None:
            r = pg.evaluate(AUDIT_JS % ("true" if use == "class" else "false"))
            for k in agg:
                agg[k].update(r.get(k, []))

        cdp = pg.context.new_cdp_session(pg)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": throttle})
        t_start = pg.evaluate("performance.now()")
        audit()
        drive(pg, audit)
        audit()
        w = pg.evaluate("({f: window.__wow.frames, r: window.__wow.resp, j: window.Juice ? window.Juice.stats : null, lite: window.Juice ? window.Juice.env.lite : null})")
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        avg, med_w, worst = _fps(w["f"], t_start)
        resp = sorted(w["r"])
        med = resp[len(resp) // 2] if resp else None
        mx = resp[-1] if resp else None
        m.update(fps_avg=avg, fps_median=med_w, fps_worst=worst, resp_median=med, resp_max=mx, clicks=len(resp), errors=errs)
        fl = (w["j"] or {})
        res.append(("PASS" if avg >= 30 and med_w >= 30 else "FAIL", f"frame rate with CPU throttled {throttle}x: {avg} fps average, median 1s window {med_w:.0f} fps (>= 30 required)"))
        if worst < 30:
            res.append(("WARN", f"worst 1s window {worst:.0f} fps while throttled {throttle}x (scene changes redraw the whole stage; fine on real classroom PCs, check on a very old one)"))
        if resp:
            lvl = "PASS" if med <= 100 and mx <= 100 else ("WARN" if med <= 100 else "FAIL")
            res.append((lvl, f"first response after a click: median {med:.0f} ms, max {mx:.0f} ms over {len(resp)} clicks (<= 100 ms; measured while throttled {throttle}x)"))
        else:
            res.append(("WARN", "no clicks measured for response time"))
        if w["j"] is not None:
            bad = fl.get("maxFlashPerSec", 0) > 3 or fl.get("maxFlashAreaOverAlpha", 0) > 0
            res.append(("FAIL" if bad else "PASS", f"flashes: max {fl.get('maxFlashPerSec', 0)}/s (<= 3), none above 341x256 px at strong alpha (WCAG 2.3.1); {fl.get('flashSkipped', 0)} skipped by the governor"))
        elif need_kit:
            res.append(("WARN", "flash governor not available (kit missing): flashes not measured"))
        tap = sorted(agg["tap"])
        res.append(("FAIL" if tap else "PASS", "tap targets >= 44px" + (f": {tap[:4]}" if tap else "")))
        if use == "class":
            tx = sorted(agg["text"])
            res.append(("FAIL" if tx else "PASS", "classroom body text >= 28px at 1080p" + (f": {tx[:4]}" if tx else "")))
        cue = sorted(agg["cue"])
        res.append(("FAIL" if cue else "PASS", "right/wrong is never colour alone (symbol or words present)" + (f": {cue[:3]}" if cue else "")))
        if errs:
            res.append(("FAIL", f"JavaScript errors during the wow run: {errs[:2]}"))
        m["flashes"] = fl
    finally:
        b.close()
    runtime.metrics = m  # type: ignore[attr-defined]
    return res
