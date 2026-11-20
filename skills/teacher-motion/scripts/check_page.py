#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Static quality check for a Teacher Studio game HTML game.

Usage: python3 check_game.py game.html [--no-play]
Games built by build.py (spec path) also get spec/token/text-size/bias checks and a headless autoplay (needs Playwright; --no-play skips it).
Exit 0 = PASS, 1 = FAIL, 2 = PARTIAL (one or more checks could not run).
"""
from __future__ import annotations

import re
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")  # tests stay silent
MUTE = ["--mute-audio"]
sys.path.insert(0, str(HERE))
from clipcheck import CLIP_JS  # noqa: E402
for folder in (HERE.parent / "shared" / "tools", HERE.parent / "tools"):
    if (folder / "syntax_check.py").is_file():
        sys.path.insert(0, str(folder))
        break
from syntax_check import checks as syntax_checks  # noqa: E402
try:
    import example_likeness  # noqa: E402  (shared/tools: 「예시를 그대로 따라간 것 같아요」)
except ImportError:  # an older install without the module: the check is skipped
    example_likeness = None

# Windows consoles (cp949) cannot encode emoji/check marks: never crash on output.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding=None if _s.isatty() else "utf-8", errors="replace")

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
_XW3 = "http://www.w3.org/"
_EXT = r"(?:https?:)?//(?!www\.w3\.org/)"
EXTERNAL_PATTERNS = (  # what makes a page ask the internet for something while it loads or plays
    ("tag", re.compile(r"""<(?:link|script|img|source|iframe|video|audio|embed|object|track)\b[^>]*?\b(?:src|href|data|poster)\s*=\s*["']?(""" + _EXT + r"""[^"'\s>]+)""", re.I)),
    ("css url()", re.compile(r"""url\(\s*["']?(""" + _EXT + r"""[^)"']+)""", re.I)),
    ("@import", re.compile(r"""@import\s+(?:url\(\s*)?["']?([^"')\s;]+)""", re.I)),
    ("script fetch", re.compile(r"""\b(?:fetch|importScripts)\s*\(\s*["'`](""" + _EXT + r"""[^"'`]+)""")),
    ("script host", re.compile(r"""["'`](https?://[^"'`\s]*(?:fonts\.googleapis|fonts\.gstatic|cdnjs\.cloudflare|cdn\.jsdelivr|unpkg\.com|googletagmanager|google-analytics)[^"'`\s]*)""", re.I)),
    ("script request", re.compile(r"""\b(new\s+(?:XMLHttpRequest|WebSocket|EventSource)\b|navigator\.sendBeacon\b)""")),
)
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
    /* orphan: the last line holds a single syllable (「써」「줘」 alone) */
    var rg2 = document.createRange(), tops = [], cnt = [];
    for (var q2 = 0; q2 < tx.length; q2++){
      if (/\s/.test(tx.charAt(q2))) continue;
      rg2.setStart(nd, q2); rg2.setEnd(nd, q2 + 1); var r2 = rg2.getBoundingClientRect(); if (!r2.height) continue;
      if (!tops.length || Math.abs(r2.top - tops[tops.length - 1]) > r2.height * 0.6){ tops.push(r2.top); cnt.push(1); } else cnt[cnt.length - 1]++;
    }
    if (tops.length >= 2 && cnt[cnt.length - 1] === 1 && tx.replace(/\s/g, '').length >= 5) out.push(['orphan', 'text', tx.replace(/\s+/g, ' ').trim().slice(0, 14)]);
  }
  return out;
})(%d)
"""


# The user wins: spec "waive": [...] turns these quality FAILs into WARNs (default = checked). Text must match the check's message.
WAIVE_KEYS = {"text_size": ("component text sizes", "all in-game text >=", "smallest text"),
              "overflow": ("no text overflow", "nothing outside the screen"),
              "hud": ("top bar parts",),
              "phone": ("phone ", "390x844", "844x390", "portrait", "landscape", "every button/answer", "smallest text", "nothing outside")}


def apply_waive(results: list[tuple[str, str]], waive) -> list[tuple[str, str]]:
    """FAIL -> WARN for the checks the user explicitly turned off, plus ONE caution line. Unknown keys are ignored (specs.validate reports them)."""
    keys = [k for k in (waive or []) if k in WAIVE_KEYS]
    if not keys:
        return results
    out, hit = [], []
    for lv, msg in results:
        k = next((k for k in keys if lv == "FAIL" and "JavaScript" not in msg and any(s in msg for s in WAIVE_KEYS[k])), None)
        if k:
            lv = "WARN"
            msg = "(사용자 요청으로 허용) " + msg
            hit.append(k)
        out.append((lv, msg))
    if hit:
        out.append(("WARN", f"점검 {len(hit)}개를 사용자 요청으로 주의로 낮췄어요 ({', '.join(dict.fromkeys(hit))}): 글자가 작거나 잘려 보일 수 있어요"))
    return out


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
    comp = re.sub(r"/\* TS:PORTRAIT BEGIN \*/.*?/\* TS:PORTRAIT END \*/", "", comp, flags=re.S)  # the portrait stage is 600 units wide: phone_check measures real CSS px there
    small = sorted({float(x) for x in FONT_PX.findall(comp) if float(x) < fl["small"]})
    out.append(("FAIL" if small else "PASS", f"component text sizes >= {fl['small']}px" + (f": found {small} -> raise the type scale (design.large) or shorten the text" if small else "")))
    if re.search(r"<input|<textarea|contenteditable", comp):
        out.append(("FAIL", "no text input fields in game components (student-info rule)"))
    if play:
        out += autoplay(path, tokens)
        out += wow_checks(path, tokens, html)
        if spec.get("device") == "phone":  # 390x844 upright + 844x390 sideways: readable, nothing outside, buttons >= 44px
            try:
                import phone_check
                out += [(("SKIP" if lv == "WARN" and "skipped" in msg else lv), msg)
                        for lv, msg in phone_check.checks(path, spec)]
            except ImportError:
                out.append(("SKIP", "phone checks unavailable"))
    else:
        out.append(("SKIP", "autoplay skipped (--no-play)"))
    return apply_waive(out, spec.get("waive"))


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
    for i in range(8):  # 8 answers show every effect; more only repeat them
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
    pg.wait_for_timeout(4500)
    audit()


def wow_checks(path: Path, tokens: dict, html: str) -> list[tuple[str, str]]:
    """Accessibility + safety lint of the Game Wow kit (flashes, reduced motion, colour cues, sizes, fps, response time)."""
    jl = _juice_lint()
    if jl is None:
        return [("SKIP", "wow lint skipped: shared/juice not found")]
    out = list(jl.static_checks(html, tokens.get("use", "class")))
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return out + [("SKIP", "Playwright not installed: wow runtime lint skipped")]
    try:
        with sync_playwright() as p:
            out += [("SKIP" if lv == "WARN" and "skipped" in msg else lv, msg)
                    for lv, msg in jl.runtime(p, path.resolve().as_uri(), _wow_drive, tokens.get("use", "class"))]
    except Exception as exc:
        out.append(("SKIP", f"wow runtime lint could not run ({str(exc).splitlines()[0][:100]})"))
    return out


HUD_JS = r"""(function(){
  var out = [], hs = document.querySelectorAll('#hud .timer, #hud .timer-num, #hud .scoreboard .team, #hud .icon-btn, #hud .combo');
  var sc = document.querySelectorAll('#scene .card, #scene .choice, #scene .btn, #scene .title, #scene .subtitle, #scene .ts-chip, #scene .qs-chip, #scene [data-fit]');
  function vis(e){ var c = getComputedStyle(e), q = e.getBoundingClientRect(); return q.width > 2 && q.height > 2 && c.visibility !== 'hidden' && c.display !== 'none' && parseFloat(c.opacity) > 0.2; }
  for (var i = 0; i < hs.length; i++){
    if (!vis(hs[i])) continue;
    var a = hs[i].getBoundingClientRect(), n = (hs[i].className || hs[i].id || 'hud').toString().split(' ')[0];
    for (var j = 0; j < sc.length; j++){
      if (!vis(sc[j])) continue;
      var b = sc[j].getBoundingClientRect();
      if (a.left < b.right - 6 && b.left < a.right - 6 && a.top < b.bottom - 6 && b.top < a.bottom - 6){
        out.push(['hudoverlap', n, ((sc[j].textContent || '').replace(/\s+/g, ' ').trim().slice(0, 14)) || sc[j].className.toString().split(' ')[0]]);
        break;
      }
    }
  }
  return out;
})()"""


def quiz_interactions(pg) -> list[tuple[str, str]]:
    """Exercise the quiz paths users can reach from the title and keyboard."""
    state = lambda: json.loads(pg.evaluate("render_game_to_text()"))
    pg.keyboard.press("r")
    restarted = state()
    results = [("PASS" if restarted["scene"] == "title" and not (restarted["correct"] or restarted["wrong"])
                else "FAIL", "R restarts the quiz and clears the score")]
    try:
        # Keep question order predictable for the deliberate wrong answer.
        pg.evaluate("GAME.spec.shuffle = false")
        pg.locator("#t-start").click(timeout=4000)
        pg.evaluate("advanceTime(4000)")
        pg.locator(".choice[data-i]").first.wait_for(timeout=4000)
        question_count = state()["game"]["total"]
        wrong = pg.evaluate("(Number(GAME.items[0].answer) + 1) % document.querySelectorAll('.choice[data-i]').length")
        pg.locator(f'.choice[data-i="{wrong}"]').click(timeout=3000)
        pg.evaluate("advanceTime(700)")
        pg.locator(".choice.wrong").first.wait_for(timeout=3000)
        results.append(("PASS" if state()["wrong"] == 1 else "FAIL", "a wrong answer is visibly marked and counted"))
        pg.keyboard.press("ArrowRight")
        if question_count == 1:
            pg.wait_for_function("NG.sceneName === 'result'", timeout=3000)
        else:
            pg.wait_for_function("(function(){ var game = JSON.parse(render_game_to_text()).game; return game.index === 1 && !game.locked; })()", timeout=3000)
        results.append(("PASS", "Right Arrow advances the quiz"))
        if question_count > 1 and pg.evaluate("GAME.spec.timer > 0"):
            remaining = state()["timer"]
            if remaining is None:
                return results + [("FAIL", "the next question did not start its timer")]
            pg.evaluate("seconds => advanceTime((seconds + 1) * 1000)", remaining)
            pg.wait_for_function("JSON.parse(render_game_to_text()).game.locked", timeout=3000)
            pg.evaluate("advanceTime(700)")
            pg.wait_for_function("JSON.parse(render_game_to_text()).wrong === 2", timeout=3000)
            results.append(("PASS", "time expiry marks an unanswered question as missed"))
    except Exception as exc:
        results.append(("FAIL", f"quiz interaction did not complete: {str(exc).splitlines()[0][:100]}"))
    return results


def autoplay(path: Path, tokens: dict) -> list[tuple[str, str]]:
    """Play the game headlessly through GAME_LOGIC.auto(); report stalls, JS errors, overflow, small text."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [("SKIP", "Playwright not installed: autoplay skipped (static checks only)")]
    problems: dict[str, str] = {}
    errors: list[str] = []
    final, steps, idle = "", 0, 0
    interactions = []
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
                return [("SKIP", "no headless browser found (playwright chromium / Chrome / Edge): autoplay skipped, static checks only")]
            pg = b.new_page(viewport={"width": 1920, "height": 1080})
            pg.add_init_script(SILENT_JS)
            pg.add_init_script(CLIP_JS)
            pg.on("pageerror", lambda e: errors.append(str(e)[:160]))
            pg.goto(path.resolve().as_uri())
            pg.wait_for_timeout(400)
            pg.click("#t-start")
            pg.evaluate("advanceTime(3300)")  # the game clock is virtual: no need to sit through the real 3.7 s countdown
            pg.wait_for_timeout(300)
            checked: set = set()  # one overflow/clip measurement per question screen, not one per step
            while steps < 500:
                st = json.loads(pg.evaluate("render_game_to_text()"))
                final = st["scene"]
                if final == "result":
                    break
                acted = pg.evaluate("window.GAME_LOGIC.auto()")
                idle = 0 if acted else idle + 1
                if idle > 25:
                    break
                pg.wait_for_timeout(40)
                pg.evaluate("advanceTime(600)")
                st2 = json.loads(pg.evaluate("render_game_to_text()"))
                now = st2["scene"]
                key = (now, str(st2.get("question") or st2.get("index") or steps))
                if now == final and final not in ("title", "countdown", "result") and key not in checked:
                    checked.add(key)
                    pg.wait_for_timeout(350)  # let the entrance animation finish so sizes are real
                    for kind, tag, txt in pg.evaluate(OVERFLOW_JS % floor) + pg.evaluate("window.__tsClip()") + pg.evaluate(HUD_JS):
                        problems.setdefault(f"{kind}:{tag}:{txt}", f"{kind} in scene {final}: <{tag}> '{txt}'")
                steps += 1
            if final == "result" and st.get("game", {}).get("mechanic") == "quiz":
                interactions = quiz_interactions(pg)
            b.close()
    except Exception as exc:  # browser missing etc.
        if errors:
            return [("FAIL", f"JavaScript errors while playing: {errors[:2]}")]
        return [("SKIP", f"autoplay could not run ({str(exc).splitlines()[0][:100]}): static checks only")]
    out: list[tuple[str, str]] = []
    out.append(("PASS" if final == "result" else "FAIL", f"autoplay reaches the result screen ({steps} steps)" + ("" if final == "result" else f": stuck at scene '{final}' -> check item counts/answers in the spec")))
    out.append(("FAIL" if errors else "PASS", "no JavaScript errors while playing" + (f": {errors[:2]}" if errors else "")))
    ov = [v for k, v in problems.items() if k.startswith(("overflow", "offstage", "clipped"))]
    sm = [v for k, v in problems.items() if k.startswith("smalltext")]
    out.append(("FAIL" if ov else "PASS", "no text overflow / clipped answers / off-stage elements" + (f": {ov[:3]} -> shorten the text, use fewer choices, or a layout with wider buttons (design.layout split|stack)" if ov else "")))
    hv = [v for k, v in problems.items() if k.startswith("hudoverlap")]
    out.append(("FAIL" if hv else "PASS", "top bar parts (timer, score, buttons, combo) never cover question boxes or '차례' tags" + (f": {hv[:3]} -> move the box down (H.top()) or pick another design.layout" if hv else "")))
    mw = [v for k, v in problems.items() if k.startswith("midword")]
    out.append(("WARN" if mw else "PASS", "no Korean word broken across lines" + (f": {mw[:3]} -> shorten the text so words are not split" if mw else "")))
    orph = [v for k, v in problems.items() if k.startswith("orphan")]
    out.append(("WARN" if orph else "PASS", "no one-syllable last line" + (f": {orph[:3]} -> shorten the text, or use fewer/shorter answers (design.layout split|stack)" if orph else "")))
    out.append(("FAIL" if sm else "PASS", f"all in-game text >= {floor}px" + (f": {sm[:3]}" if sm else "")))
    return out + interactions


def smoke_check(path: Path, stage: bool) -> tuple[str, str]:
    """Verify that a legacy game or a stage page boots in a real browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "SKIP", "browser opening check: Playwright unavailable"
    errors = []
    try:
        with sync_playwright() as pw:
            browser = None
            for candidate in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
                try:
                    browser = pw.chromium.launch(timeout=5000, args=MUTE, **candidate)
                    break
                except Exception:
                    continue
            if browser is None:
                return "SKIP", "browser opening check: no browser could launch"
            try:
                page = browser.new_page()
                page.on("pageerror", lambda exc: errors.append(str(exc)[:160]))
                page.goto(path.resolve().as_uri(), timeout=5000)
                expression = ("window.__stage && window.__stage.ready" if stage
                              else "window.NG && NG.sceneName === 'title' && document.querySelector('#scene').children.length")
                page.wait_for_function(expression, timeout=5000)
            finally:
                browser.close()
    except Exception as exc:
        if errors:
            return "FAIL", f"browser opening check: {errors[:2]}"
        return "SKIP", f"browser opening check could not finish: {str(exc).splitlines()[0][:100]}"
    return ("FAIL", f"browser opening check: {errors[:2]}") if errors else ("PASS", "page opens in a browser")


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
                return [("SKIP", f"color-blind check skipped ({str(exc).splitlines()[0][:80]})")]
    return []


def main(path: Path, play: bool = True, consent: bool = False) -> int:
    """Run all checks and print a report. Returns process exit code."""
    if not path.exists():
        print(f"FAIL file not found: {path}")
        return 1
    html = path.read_text(encoding="utf-8", errors="replace")
    syntax_results = syntax_checks(html, consent=consent, allow_modern="ts-allow-modern" in html)
    # only pages built from a spec (game build.py, deck.py); an old skin fired with its own sample content is a demo, not a copy
    spec_built = "TS:BUILD" in html or 'name="ts-deck"' in html
    likeness = example_likeness.check_text(html, [HERE.parent / "assets" / "spec-examples"]) if example_likeness and spec_built else []
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)  # ignore HTML comments
    results: list[tuple[str, str]] = list(likeness)

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

    online = bool(re.search(r'"online"\s*:\s*true', html))  # the spec opted in (spec "online": true / DOC online): only then may the page use the internet
    refs = sorted({(kind, m.group(1)) for kind, pat in EXTERNAL_PATTERNS for m in pat.finditer(html)})
    if online:
        bad = sorted({u for _, u in refs if not any(h in u for h in ALLOWED_HOSTS)})
        add("FAIL" if bad else "PASS", "online opt-in: outside resources only from cdnjs / jsdelivr npm / unpkg / Google Fonts" + (f": {bad[:3]}" if bad else ""))
    else:
        add("FAIL" if refs else "PASS", "offline: no outside request or address (link, script, img, css url/@import, fetch)" +
            (f": {[f'{k} {u[:60]}' for k, u in refs[:3]]} -> rebuild with the current build.py (offline is the default); only a spec with online:true may use the internet" if refs else ""))
    if re.search(r"""<a\b[^>]*\bhref\s*=\s*["']https?://""", html, re.I):
        add("WARN", "a link to an outside page (<a href=http...>): fine for a link people tap, but the page then needs the internet for that tap")
    cdn = re.findall(r"cdnjs\.cloudflare\.com/ajax/libs/[^/]+/([^/]+)/", html)
    cdn += re.findall(r"cdn\.jsdelivr\.net/npm/(?:@[^/]+/)?[^@/]+@([^/]+)/", html)
    if any(not re.match(r"\d+\.\d+", v) for v in cdn):
        add("FAIL", "cdnjs URLs must pin an exact version")
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

    for level, message in syntax_results:
        add(level, message)

    if "TS:BUILD" in html:
        for level, msg in spec_checks(html, path, play):
            add(level, msg)
    else:
        add(*(smoke_check(path, is_stage) if play else ("SKIP", "browser opening check disabled")))

    for level, msg in color_blind_results(html):
        add(level, msg)

    for level, msg in results:
        print(f"{level:4} {msg}")
    fails = sum(1 for lv, _ in results if lv == "FAIL")
    skipped = sum(lv == "SKIP" for lv, _ in results)
    status = "FAIL" if fails else "PARTIAL" if skipped else "PASS"
    print(f"\nRESULT: {status} ({fails} fail, {skipped} unchecked, {sum(lv == 'WARN' for lv, _ in results)} warn)")
    return 1 if fails else 2 if skipped else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    sys.exit(main(Path(args[0]), play="--no-play" not in sys.argv, consent="--yes" in sys.argv))
