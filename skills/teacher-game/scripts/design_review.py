#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Visual design review gate: render the key screens of a game, write a contact sheet PNG + design metrics JSON.

Usage:
    python3 design_review.py game.html [--out DIR] [--yes]          # DIR/<name>-sheet.png + DIR/<name>-metrics.json
    python3 design_review.py --baseline OUTDIR_WITH_LEGACY_HTMLS     # (maintainers) measure the legacy skins -> assets/design-baseline.json
Flow in SKILL.md:  build -> check_game -> design_review -> AI LOOKS at the sheet PNG (references/design-rubric.md) -> fix spec -> rebuild (max 2 loops).

Screens: title, question, correct, wrong, result (+ "backdrop" = the scene without cards, to judge decoration).
Metrics (per screen, then summarised) - all measured, none guessed:
  deco_density   share of the backdrop (scene hidden) that has texture/detail (0..1)        - higher = more decorated
  empty_ratio    share of the NON-card area that is flat colour (0..1)                       - lower = less "휑함"
  colors         number of distinct colours that cover >= 0.4% of the screen                 - palette richness
  hierarchy      largest text size / median text size                                        - focal point strength
  min_contrast   lowest text-to-background contrast (WCAG ratio) among text >= 34px
  overlaps       text boxes that overlap each other / the host character
Compared with the legacy skins (assets/design-baseline.json): below baseline -> WARN with a concrete hint. Exit 0 always (advisory gate).
device:"phone" games are also rendered at 390x844 (upright) and 844x390 (sideways): <name>-phone.png + the real smallest text size, off-screen
parts and tap targets (scripts/phone_check.py). Unreadable text there makes the verdict FAIL.
The summary uses the WORST screen (max overlaps, min contrast over title/question/correct/wrong/result), not the average.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import statistics
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")  # tests stay silent
MUTE = ["--mute-audio"]
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "shared" / "tools"))
BASELINE = SKILL / "assets" / "design-baseline.json"
sys.path.insert(0, str(HERE))
from clipcheck import CLIP_JS  # noqa: E402

DECO_TEXT_WARN, DECO_TEXT_FAIL = 0.035, 0.08   # share of strong-edge pixels under a big text that sits straight on the scene

PROBE_JS = r"""
(function(){
  var out = {texts: [], cards: [], host: null, plain: 0}, sc = document.querySelector('#scene .screen, #scene');
  function bgs(e){ var l = []; while (e && e.nodeType === 1){ var c = getComputedStyle(e); var bi = c.backgroundImage, mm = bi && bi !== 'none' ? bi.match(/rgba?\([^)]*\)/) : null; l.push(mm ? mm[0] : c.backgroundColor); if (e.id === 'scene') break; e = e.parentElement; } return l; }
  var els = (sc || document.body).querySelectorAll('*');
  for (var i = 0; i < els.length; i++){
    var e = els[i], r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.2) continue;
    var txt = ''; for (var k = 0; k < e.childNodes.length; k++) if (e.childNodes[k].nodeType === 3) txt += e.childNodes[k].nodeValue;
    txt = txt.replace(/\s+/g, ' ').trim();
    var bg = (cs.backgroundImage !== 'none' && /rgba?\(/.test(cs.backgroundImage)) ? cs.backgroundImage.match(/rgba?\([^)]*\)/)[0] : cs.backgroundColor, a = bg.indexOf('rgba') === 0 ? parseFloat(bg.split(',')[3]) : (bg === 'transparent' ? 0 : 1);
    if (a > 0.6 && r.width > 120 && r.height > 60) out.cards.push([r.left, r.top, r.width, r.height]);
    if (a > 0.6 && r.width * r.height > 15000 && cs.backgroundImage === 'none' && !e.querySelector('svg, img') && txt.replace(/[^가-힣A-Za-z0-9]/g, '').length === 0 && /[\S]/.test(e.textContent || '') && (e.textContent || '').trim().length <= 2) out.plain++;
    if (txt && /[가-힣A-Za-z0-9]/.test(txt)) out.texts.push({t: txt.slice(0, 20), r: [r.left, r.top, r.width, r.height], fs: parseFloat(cs.fontSize), color: cs.color, bgs: bgs(e)});
  }
  var h = document.querySelector('#ts-deco .ts-host'); if (h){ var q = h.getBoundingClientRect(); out.host = [q.left, q.top, q.width, q.height]; }
  return out;
})()
"""


def _rgba(s: str) -> tuple[float, float, float, float]:
    m = re.findall(r"[\d.]+", s)
    v = [float(x) for x in m[:4]]
    return (v[0], v[1], v[2], v[3] if len(v) > 3 else 1.0) if len(v) >= 3 else (0, 0, 0, 0)


def _lum(c) -> float:
    def f(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _ratio(a, b) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _effective_bg(bgs: list[str]):
    """Composite the ancestors' backgrounds (innermost first). None when nothing opaque is behind the text."""
    layers = [_rgba(b) for b in bgs if _rgba(b)[3] > 0]
    top = next((i for i, c in enumerate(layers) if c[3] >= 0.9), None)  # innermost (nearly) opaque layer
    if top is None:
        return None
    base = layers[top][:3]
    for r, g, b, a in reversed(layers[:top]):  # translucent layers painted on top of it
        base = tuple(base[i] * (1 - a) + (r, g, b)[i] * a for i in range(3))
    return base


def _std_cells(img, cols: int, rows: int, skip) -> tuple[int, int]:
    """(textured cells, counted cells) on a luminance grid; skip(cx, cy) -> True to ignore a cell."""
    g = img.convert("L").resize((cols * 8, rows * 8))
    px = g.load()
    tex = n = 0
    for cy in range(rows):
        for cx in range(cols):
            if skip(cx / cols * 1920 + 30, cy / rows * 1080 + 30):
                continue
            vals = [px[cx * 8 + i, cy * 8 + j] for i in range(8) for j in range(8)]
            m = sum(vals) / 64
            sd = (sum((v - m) ** 2 for v in vals) / 64) ** 0.5
            n += 1
            tex += sd >= 6.5
    return tex, n


def measure(shot, backdrop, probe: dict) -> dict:
    """Metrics of one screen from its PNG (PIL image), the backdrop PNG and the DOM probe."""
    cols, rows = 48, 27
    cards = probe["cards"]

    def in_card(x, y):
        return any(c[0] - 4 <= x <= c[0] + c[2] + 4 and c[1] - 4 <= y <= c[1] + c[3] + 4 for c in cards)
    tex, n = _std_cells(shot, cols, rows, in_card)
    empty = 1 - tex / n if n else 0.0
    bt, bn = _std_cells(backdrop, cols, rows, lambda x, y: False)
    small = shot.convert("RGB").resize((240, 135))
    cnt: dict = {}
    for p in small.getdata():
        k = (p[0] >> 3, p[1] >> 3, p[2] >> 3)
        cnt[k] = cnt.get(k, 0) + 1
    total = 240 * 135
    colors = sum(1 for v in cnt.values() if v / total >= 0.004)
    texts = probe["texts"]
    sizes = [t["fs"] for t in texts if t["fs"] >= 20]
    hier = round(max(sizes) / statistics.median(sizes), 2) if sizes else 0
    mins, lows = 99.0, 0
    sg = shot.convert("RGB")
    for t in texts:
        if t["fs"] < 34:
            continue
        fg = _rgba(t["color"])[:3]
        bg = _effective_bg(t["bgs"])
        if bg is None:  # text sits straight on the scene: sample the pixels around it
            x, y, w, h = [int(v) for v in t["r"]]
            box = backdrop.convert("RGB").crop((max(0, x), max(0, y), min(1920, x + max(w, 2)), min(1080, y + max(h, 2)))).resize((6, 3))
            px = list(box.getdata())
            bg = tuple(sorted(p[i] for p in px)[len(px) // 2] for i in range(3))
        r = _ratio(fg, bg)
        mins = min(mins, r)
        lows += r < 4.5
    ov = 0
    rects = [t["r"] for t in texts if t["fs"] >= 34]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            if a[0] < b[0] + b[2] - 6 and b[0] < a[0] + a[2] - 6 and a[1] < b[1] + b[3] - 6 and b[1] < a[1] + a[3] - 6:
                ov += 1
    # decoration behind big text (title / question): strong edges of the backdrop (scene hidden) under a text that sits straight on the scene
    deco_text, deco_where = 0.0, ""
    bd = backdrop.convert("L")
    for t in texts:
        if t["fs"] < 34 or _effective_bg(t["bgs"]) is not None:
            continue
        x, y, w, h = [int(v) for v in t["r"]]
        box = bd.crop((max(0, x), max(0, y), min(1920, x + max(w, 2)), min(1080, y + max(h, 2))))
        if box.width < 8 or box.height < 8:
            continue
        box = box.resize((max(8, box.width // 2), max(8, box.height // 2)))
        px, bw, bh = box.load(), box.width, box.height
        strong = sum(1 for yy in range(bh - 1) for xx in range(bw - 1) if abs(px[xx, yy] - px[xx + 1, yy]) + abs(px[xx, yy] - px[xx, yy + 1]) > 80)
        ratio = strong / max(1, (bw - 1) * (bh - 1))
        if ratio > deco_text:
            deco_text, deco_where = ratio, t["t"]
    host_ov = 0
    if probe.get("host"):
        h = probe["host"]
        host_ov = sum(1 for r in rects if r[0] < h[0] + h[2] * 0.55 and h[0] < r[0] + r[2] and r[1] < h[1] + h[3] and h[1] < r[1] + r[3] and r[0] < 120 and r[1] > h[1])
    return {"plain_cards": probe.get("plain", 0), "deco_density": round(bt / bn, 3), "empty_ratio": round(empty, 3), "colors": colors, "hierarchy": hier,
            "min_contrast": round(mins if mins < 99 else 21, 2), "low_contrast": lows, "overlaps": ov + host_ov,
            "deco_under_text": round(deco_text, 3), "deco_text": deco_where, "clipped": [list(c) for c in probe.get("clipped", [])]}


def _launch(p):
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(args=MUTE, **kw)
        except Exception:
            continue
    return None


def capture(path: Path) -> tuple[dict, dict, dict]:
    """Play the game and grab {screen: (PIL image)}, {screen: probe}, {screen: backdrop image}."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    shots, probes, backs = {}, {}, {}

    def snap(pg, name):
        pg.wait_for_timeout(700)
        shots[name] = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        probes[name] = pg.evaluate(PROBE_JS)
        probes[name]["clipped"] = pg.evaluate("window.__tsClip()")
        pg.evaluate("(function(){['scene','hud','fx'].forEach(function(i){var e=document.getElementById(i);if(e)e.style.visibility='hidden';});})()")
        backs[name] = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        pg.evaluate("(function(){['scene','hud','fx'].forEach(function(i){var e=document.getElementById(i);if(e)e.style.visibility='';});})()")

    with sync_playwright() as p:
        b = _launch(p)
        if b is None:
            raise RuntimeError("no headless browser (Chrome/Edge) found")
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.add_init_script(SILENT_JS)
        pg.add_init_script(CLIP_JS)
        pg.goto(path.resolve().as_uri())
        pg.wait_for_timeout(900)
        pg.evaluate("advanceTime(1500)")
        snap(pg, "title")
        pg.click("#t-start")
        pg.wait_for_timeout(3700)
        pg.evaluate("advanceTime(1200)")
        has_auto = pg.evaluate("!!(window.GAME_LOGIC && window.GAME_LOGIC.auto)")
        st0 = json.loads(pg.evaluate("render_game_to_text()"))
        snap(pg, "question")
        seen_c, seen_w, steps, idle = st0.get("correct", 0), st0.get("wrong", 0), 0, 0
        while steps < 160 and has_auto:
            st = json.loads(pg.evaluate("render_game_to_text()"))
            if st["scene"] == "result":
                break
            acted = pg.evaluate("window.GAME_LOGIC.auto()")
            idle = 0 if acted else idle + 1
            if idle > 25:
                break
            pg.wait_for_timeout(200)
            pg.evaluate("advanceTime(700)")
            pg.wait_for_timeout(120)
            st = json.loads(pg.evaluate("render_game_to_text()"))
            if st.get("correct", 0) > seen_c and "correct" not in shots:
                snap(pg, "correct")
            if st.get("wrong", 0) > seen_w and "wrong" not in shots:
                snap(pg, "wrong")
            seen_c, seen_w = st.get("correct", 0), st.get("wrong", 0)
            steps += 1
            if ("correct" in shots and "wrong" in shots) or steps >= 24:  # fast-forward inside the page (no waits)
                pg.evaluate("(function(){for(var i=0;i<400;i++){var s=JSON.parse(render_game_to_text());if(s.scene==='result')break;try{window.GAME_LOGIC.auto();}catch(e){}advanceTime(1500);}})()")
                break
        for _ in range(6):
            pg.evaluate("advanceTime(1200)")
            pg.wait_for_timeout(250)
            if json.loads(pg.evaluate("render_game_to_text()"))["scene"] == "result":
                break
        pg.wait_for_timeout(600)
        pg.evaluate("advanceTime(2500)")
        snap(pg, "result")
        b.close()
    return shots, probes, backs


def contact_sheet(shots: dict, backs: dict, metrics: dict, out: Path) -> None:
    """3x2 sheet (title, question, correct / wrong, result, backdrop) as an optimised palette PNG (<= ~400KB)."""
    from PIL import Image, ImageDraw
    order = ["title", "question", "correct", "wrong", "result", "backdrop"]
    tw, th, cap = 560, 315, 30
    sheet = Image.new("RGB", (tw * 3 + 8 * 4, (th + cap) * 2 + 8 * 3), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(order):
        img = backs.get("question") if name == "backdrop" else (shots.get(name) or shots.get("question"))
        if img is None:
            continue
        x, y = 8 + (i % 3) * (tw + 8), 8 + (i // 3) * (th + cap + 8)
        sheet.paste(img.resize((tw, th)), (x, y + cap))
        m = metrics.get("question" if name == "backdrop" else name, {})
        label = name + ("" if name in shots or name == "backdrop" else " (n/a)")
        if m:
            label += "  empty %.2f  deco %.2f  colors %d  contrast %.1f" % (m["empty_ratio"], m["deco_density"], m["colors"], m["min_contrast"])
        d.text((x + 4, y + 6), label, fill=(235, 235, 240))
    pal = sheet.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out.parent.mkdir(parents=True, exist_ok=True)
    pal.save(out, optimize=True)
    if out.stat().st_size > 420 * 1024:
        sheet.quantize(colors=64, dither=Image.Dither.NONE).save(out, optimize=True)


def summarise(metrics: dict) -> dict:
    keys = ("deco_density", "empty_ratio", "colors", "hierarchy", "min_contrast", "overlaps")
    play = [metrics[k] for k in ("question", "correct", "wrong") if k in metrics]
    out = {k: round(statistics.mean(m[k] for m in play), 3) for k in keys if play}
    out["hierarchy"] = max(m["hierarchy"] for m in metrics.values())
    if "min_contrast" in out:
        out["min_contrast"] = round(min(m["min_contrast"] for m in metrics.values()), 2)  # worst screen, title and result included
        out["overlaps"] = max(m["overlaps"] for m in metrics.values())
    out["deco_under_text"] = max(m["deco_under_text"] for m in metrics.values())
    out["clipped"] = sum(len(m["clipped"]) for m in metrics.values())
    if "title" in metrics:
        out["title_empty_ratio"] = metrics["title"]["empty_ratio"]
        out["title_deco_density"] = metrics["title"]["deco_density"]
    return out


def judge(summary: dict, style: str = "") -> tuple[str, list[str]]:
    """Hints in plain Korean. design-baseline.json is only a MINIMUM floor (measured on older skins), not the target: the target is the commercial-quality traits in design-rubric.md."""
    hints: list[str] = []
    fail = False
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else None
    if summary.get("min_contrast", 21) < 2.0:
        fail = True
        hints.append("글자와 바탕의 대비가 2보다 낮아 안 읽혀요 → 카드 색(cardText/card)을 바꾸거나 design.mood를 차분하게 바꿔 보세요")
    elif summary.get("min_contrast", 21) < 4.5:
        hints.append("글자 대비가 4.5보다 낮은 곳이 있어요 → 글자 색이나 카드 색을 더 진하게 해 보세요")
    if summary.get("clipped", 0) > 0:
        fail = True
        hints.append(f"보기·버튼 안의 글자가 잘려요({summary['clipped']}곳) → 보기 글을 줄이거나 보기 수를 줄이거나, design.layout을 split·stack으로 바꿔 보세요")
    if summary.get("deco_under_text", 0) >= DECO_TEXT_FAIL:
        fail = True
        hints.append("배경 장식이 제목·문제 글자 뒤를 지나가서 읽기 어려워요 → 장면이 덜 복잡한 style이나 design.mood(차분하게)로 바꿔 보세요")
    elif summary.get("deco_under_text", 0) >= DECO_TEXT_WARN:
        hints.append("배경 장식이 제목·문제 글자와 겹쳐요 → 장식이 가장자리에만 있는 style/layout을 써 보세요")
    if summary.get("overlaps", 0) > 0:
        hints.append("글자 상자가 서로(또는 도우미 캐릭터와) 겹쳐요 → 문제·보기 글을 줄이거나 보기 수를 줄여 보세요")
    if summary.get("hierarchy", 9) < 1.25:
        hints.append("가장 큰 글자와 보통 글자 크기 차이가 작아 시선이 흩어져요 → 문제를 더 짧게 하거나 design.large를 켜 보세요")
    if base and style != "minimal-premium":  # minimal-premium: whitespace is the design, so only the minimum floor is skipped
        t = base["thresholds"]
        if summary.get("deco_density", 1) < t["deco_density_min"]:
            hints.append("배경 장식이 최소 기준보다 적어요 → 장면이 있는 스타일(design.style: 네온·글래스·팝·파스텔 …)이나 분위기 낱말을 더해 보세요")
        if summary.get("empty_ratio", 0) > t["empty_ratio_max"]:
            hints.append("화면이 휑해요(빈 면이 넓음) → 장면이 있는 테마(auto/이식 테마)로 바꾸거나 소품이 많은 분위기 낱말을 넣어 보세요")
        if summary.get("colors", 99) < t["colors_min"]:
            hints.append("색이 너무 적어 밋밋해요 → mood를 바꿔 다른 색 세트를 쓰거나 theme:auto의 분위기 낱말을 추가해 보세요")
    return ("FAIL" if fail else ("WARN" if hints else "PASS")), hints


def fingerprint(probe: dict, cols: int = 24, rows: int = 14) -> str:
    """Layout fingerprint: which cells of a 24x14 grid are covered by cards/text boxes on the question screen (string of 0/1)."""
    boxes = list(probe.get("cards", [])) + [t["r"] for t in probe.get("texts", []) if t["fs"] >= 34]
    out = []
    for cy in range(rows):
        for cx in range(cols):
            x, y = (cx + 0.5) * 1920 / cols, (cy + 0.5) * 1080 / rows
            out.append("1" if any(b[0] <= x <= b[0] + b[2] and b[1] <= y <= b[1] + b[3] for b in boxes) else "0")
    return "".join(out)


def similarity(a: str, b: str) -> float:
    inter = sum(1 for x, y in zip(a, b) if x == "1" and y == "1")
    union = sum(1 for x, y in zip(a, b) if x == "1" or y == "1")
    return inter / union if union else 0.0


def game_spec(html: Path) -> dict:
    m = re.search(r"window\.GAME = (\{.*?\n\});", html.read_text(encoding="utf-8"), re.S)
    try:
        return (json.loads(m.group(1)).get("spec") or {}) if m else {}
    except ValueError:
        return {}


def sameness(out_dir: Path, me: str, mech: str, fp: str) -> list[tuple[str, float]]:
    """Other reviewed games of the same mechanic in the output folder whose layout looks (nearly) the same."""
    out = []
    for f in out_dir.glob("*-metrics.json"):
        if f.name == f"{me}-metrics.json":
            continue
        try:
            o = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if o.get("mechanic") == mech and o.get("fingerprint"):
            out.append((o.get("file", f.name), round(similarity(fp, o["fingerprint"]), 2)))
    return sorted(out, key=lambda x: -x[1])


def prop_relevance(html: Path) -> dict:
    """auto theme: every prop must carry a tag of the world's tag set (props that do not fit the story are listed)."""
    m = re.search(r"window\.GAME = (\{.*?\n\});", html.read_text(encoding="utf-8"), re.S)
    try:
        cfg = (json.loads(m.group(1)).get("spec") or {}).get("autoTheme") or {} if m else {}
    except ValueError:
        cfg = {}
    tags, world = cfg.get("propTags") or {}, set(cfg.get("worldTags") or [])
    if not tags or not world:
        return {"checked": False, "bad": []}
    return {"checked": True, "world": sorted(world), "bad": [n for n, t in tags.items() if not (set(t) & world)]}


def review(html: Path, out_dir: Path, yes: bool = False) -> dict:
    try:
        import PIL  # noqa: F401
    except ImportError:
        import ensure
        r = ensure.ensure("pillow", consent=yes)
        if not r["ok"]:
            return {"verdict": "SKIP", "hints": [r["prompt"] + "  (동의하면 --yes 로 다시 실행)"]}
    try:
        shots, probes, backs = capture(html)
    except Exception as exc:  # no browser etc.
        return {"verdict": "SKIP", "hints": [f"화면을 열 수 없어 디자인 점검을 건너뛰었어요 ({str(exc).splitlines()[0][:80]})"]}
    backs["question"] = backs.get("question")
    metrics = {k: measure(shots[k], backs[k], probes[k]) for k in shots}
    sheet = out_dir / f"{html.stem}-sheet.png"
    contact_sheet(shots, backs, metrics, sheet)
    summ = summarise(metrics)
    verdict, hints = judge(summ, ((game_spec(html).get("layoutCfg") or {}).get("style") or ""))
    rel = prop_relevance(html)
    if rel["bad"]:
        verdict = "WARN" if verdict == "PASS" else verdict
        hints.append("이야기와 상관없는 소품이 있어요: " + ", ".join(rel["bad"]) + " → design.words에 주제 낱말(바다·우주·역사 …)을 넣어 소품을 다시 고르게 하세요")
    gs = game_spec(html)
    mech = gs.get("mechanic", "")
    fp = fingerprint(probes["question"]) if "question" in probes else ""
    same = sameness(out_dir, html.stem, mech, fp) if fp else []
    close = [(n, v) for n, v in same if v >= 0.86]
    if close:
        verdict = "WARN" if verdict == "PASS" else verdict
        hints.append("배치가 " + ", ".join(f"{n}({v})" for n, v in close[:3]) + " 와 거의 같아요 → 다른 배치로 다시: design.seed를 바꾸거나 design.layout(split·bento·news·poster)을 지정하세요")
    plain = max((m.get("plain_cards", 0) for k, m in metrics.items() if k != "title"), default=0)
    summ["plain_cards"] = plain
    if plain >= 3:
        verdict = "WARN" if verdict == "PASS" else verdict
        hints.append(f"기호만 있는 밋밋한 흰 카드가 {plain}장 보여요 → 카드 뒷면/카드에 무늬·그림을 넣으세요(자동 테마는 기본으로 넣어요, theme를 auto로 바꿔 보세요)")
    if gs.get("device") == "phone":
        try:
            ph = phone_review(html, out_dir, gs)
            summ["phone_verdict"] = ph["verdict"]
            if ph["fails"]:
                verdict = "FAIL"
                hints += ["폰 화면에서 쓸 수 없어요: " + m for m in ph["fails"]]
            elif ph["warns"]:
                verdict = "WARN" if verdict == "PASS" else verdict
                hints += ["폰 화면 주의: " + m for m in ph["warns"]]
            phone = ph
        except Exception as exc:  # no browser etc.: the main review still counts
            phone = {"error": str(exc).splitlines()[0][:80]}
            hints.append("폰 화면 점검을 건너뛰었어요 (" + phone["error"] + ")")
    else:
        phone = None
    res = {"file": html.name, "sheet": str(sheet), "screens": metrics, "phone": phone, "summary": summ, "verdict": verdict, "hints": hints,
           "missing_screens": [k for k in ("correct", "wrong") if k not in shots], "prop_relevance": rel,
           "mechanic": mech, "layout": gs.get("layoutCfg"), "fingerprint": fp, "similar_to": same[:3]}
    (out_dir / f"{html.stem}-metrics.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def phone_review(html: Path, out_dir: Path, spec: dict) -> dict:
    """390x844 + 844x390 renders of a device:"phone" game: contact sheet PNG + measured readability (phone_check.py)."""
    import phone_check
    from PIL import Image, ImageDraw
    from playwright.sync_api import sync_playwright
    portrait_game = spec.get("mechanic") in ("quiz",)
    shots: dict = {}
    res: dict = {}
    lines: list = []
    with sync_playwright() as p:
        for orient in ("portrait", "landscape"):
            sh: dict = {}
            probes, errors = phone_check.run_viewport(p, html, orient, sh, Image)
            shots[orient] = sh
            res[orient] = {k: {"min_font_px": round(v["minFont"], 1), "tiny_buttons": len(v["tiny"]), "offscreen": len(v["offscreen"]), "clipped": len(v["clipped"])} for k, v in probes.items()}
            lines += phone_check.evaluate(orient, probes, errors, portrait_game)
    cell_p, cell_l, cap = (234, 506), (506, 234), 22
    names_p = ["title", "question", "answered", "result"]
    names_l = ["question", "answered"]
    sheet = Image.new("RGB", (8 + 4 * (cell_p[0] + 8), 8 + cap + cell_p[1] + 8 + cap + cell_l[1] + 8), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names_p):
        x, y = 8 + i * (cell_p[0] + 8), 8
        d.text((x + 2, y + 4), "390x844 " + n + "  min %.1fpx" % res["portrait"][n]["min_font_px"], fill=(235, 235, 240))
        sheet.paste(shots["portrait"][n].resize(cell_p), (x, y + cap))
    for i, n in enumerate(names_l):
        x, y = 8 + i * (cell_l[0] + 8), 8 + cap + cell_p[1] + 8
        d.text((x + 2, y + 4), "844x390 " + n + "  min %.1fpx" % res["landscape"][n]["min_font_px"], fill=(235, 235, 240))
        sheet.paste(shots["landscape"][n].resize(cell_l), (x, y + cap))
    path = out_dir / f"{html.stem}-phone.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)
    fails = [m for lv, m in lines if lv == "FAIL"]
    warns = [m for lv, m in lines if lv == "WARN"]
    return {"sheet": str(path), "screens": res, "verdict": "FAIL" if fails else ("WARN" if warns else "PASS"), "fails": fails, "warns": warns}


def make_baseline(folder: Path) -> int:
    """Measure the legacy skins (fired HTML files in folder): title + play screens -> thresholds."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    rows = []
    for f in sorted(folder.glob("*.html")):
        with sync_playwright() as p:
            b = _launch(p)
            pg = b.new_page(viewport={"width": 1920, "height": 1080})
            pg.add_init_script(SILENT_JS)
            pg.goto(f.resolve().as_uri())
            pg.wait_for_timeout(900)
            pg.evaluate("advanceTime(1500)")
            res = {}
            for name, wait in (("title", 0), ("play", 1)):
                if wait:
                    try:
                        pg.click("#t-start", timeout=3000)
                    except Exception:
                        pass
                    pg.wait_for_timeout(3700)
                    pg.evaluate("advanceTime(2500)")
                shot = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
                probe = pg.evaluate(PROBE_JS)
                pg.evaluate("(function(){['scene','hud','fx'].forEach(function(i){var e=document.getElementById(i);if(e)e.style.visibility='hidden';});})()")
                back = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
                pg.evaluate("(function(){['scene','hud','fx'].forEach(function(i){var e=document.getElementById(i);if(e)e.style.visibility='';});})()")
                res[name] = measure(shot, back, probe)
            b.close()
        rows.append({"skin": f.stem, **{k: v for k, v in res.items()}})
        print(f.stem, res["play"])
    play = [r["play"] for r in rows]
    thr = {"deco_density_min": round(min(m["deco_density"] for m in play) * 0.9, 3),
           "empty_ratio_max": round(max(m["empty_ratio"] for m in play) * 1.1, 3),
           "colors_min": max(6, int(min(m["colors"] for m in play) * 0.9)),
           "median": {k: round(statistics.median(m[k] for m in play), 3) for k in ("deco_density", "empty_ratio", "colors", "hierarchy", "min_contrast")}}
    BASELINE.write_text(json.dumps({"_note": "Measured on the 9 legacy skins (play screen). Spec builds below these thresholds get a WARN with hints.", "skins": rows, "thresholds": thr}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("thresholds", thr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", nargs="?", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    if a.baseline:
        return make_baseline(a.baseline)
    if not a.html:
        ap.error("game.html needed")
    out = a.out or a.html.parent
    res = review(a.html, out, a.yes)
    print(f"DESIGN REVIEW: {res['verdict']}")
    if res.get("summary"):
        print("  " + "  ".join(f"{k}={v}" for k, v in res["summary"].items()))
        print(f"  sheet: {res['sheet']}")
        if res.get("phone") and res["phone"].get("sheet"):
            print(f"  phone sheet: {res['phone']['sheet']}  ({res['phone']['verdict']})")
    for h in res["hints"]:
        print("  - " + h)
    if res.get("missing_screens"):
        print("  (이 게임 방식에는 없는 화면: " + ", ".join(res["missing_screens"]) + ")")
    if res["verdict"] == "SKIP" or not res.get("sheet"):
        return 0
    print("  → 위 PNG를 직접 눈으로 보고 references/design-rubric.md 항목을 확인하세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
