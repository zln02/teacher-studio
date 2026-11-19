#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Slide design review gate: screenshot every slide (after build animations finished), measure, write a contact sheet + metrics.

Usage:
    python3 slides_review.py deck.html [--out DIR] [--name NAME]        # DIR/NAME-sheet.png, DIR/NAME-metrics.json, DIR/NAME/NN.png
    python3 slides_review.py --compare a.html b.html [c.html ...]        # sameness between decks (layout fingerprints + palette)
Flow in SKILL.md: build -> check_page -> slides_review -> AI LOOKS at the sheet (would a professional designer ship this?) -> fix spec -> rebuild (max 2 loops).

Measured per slide (all numbers, none guessed):
  external requests = 0 (anything not file:/data:/blob:)   contrast >= 4.5 (real pixels under each text, text hidden for the probe)
  min font >= floor (28px; 24 personal)                    overflow / off-stage / outside the 96px safe margin
  keep-all (word-break) + no Korean word split             visual weight (share of non-flat 40px cells) - not empty
  CLUTTER caps: elements <= 36, icons <= 3, big colour bins <= 6 (<= 9 on photo/chart slides)
Deck: no 3 consecutive identical layouts; layout variety. Compare: deck distance >= 0.35 (style, layout set, accent colour).
Exit 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}"
             "try{var A=window.AudioContext||window.webkitAudioContext;if(A){A.prototype.resume=function(){return Promise.resolve();}}}catch(e){}})()")
MUTE = ["--mute-audio"]
CAPS = {"elements": 36, "icons": 3, "colors": 6, "colors_media": 9}
SAFE = 96

PROBE_JS = r"""
(function(floor, safe){
  var sl = document.querySelector('.sl.on'), out = {texts: [], overflow: [], offstage: [], small: [], midword: [], keepall: [], elements: 0, icons: 0, media: false}, st = {w: 1920, h: 1080};
  var scale = document.getElementById('stage').getBoundingClientRect().width / 1920;
  function R(e){ var r = e.getBoundingClientRect(); return [r.left / scale, r.top / scale, r.width / scale, r.height / scale]; }
  var all = sl.querySelectorAll('*');
  for (var i = 0; i < all.length; i++){
    var e = all[i], cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (e.closest('.bgart, .flair, defs, symbol')) continue;
    var r = R(e); if (!r[2] || !r[3]) continue;
    var cls = typeof e.className === 'string' ? e.className : '';
    var deco = !!e.closest('[aria-hidden="true"]') || /\bdeco\b/.test(cls);
    var txt = ''; for (var k = 0; k < e.childNodes.length; k++) if (e.childNodes[k].nodeType === 3) txt += e.childNodes[k].nodeValue;
    txt = txt.replace(/\s+/g, ' ').trim();
    var tag = (cls || e.tagName).split(' ').slice(0, 2).join('.');
    var isText = txt.length > 0 && /[가-힣A-Za-z0-9]/.test(txt);
    if (e.tagName === 'IMG' || e.tagName === 'VIDEO' || e.tagName === 'CANVAS') out.media = true;
    if (e.closest('.katex')) { if (e.classList.contains('katex')) out.elements++; if (isText && !deco) out.texts.push({t: txt.slice(0, 14), r: r, fs: parseFloat(cs.fontSize), color: cs.color, math: true}); continue; }
    if (/\b(bx)\b/.test(cls) && !/\bgrp\b/.test(cls) && !/\btx\b/.test(cls)) out.elements++;
    if (e.tagName === 'use' && /lucide/.test(e.getAttribute('href') || '')) out.icons++;
    if (isText && !deco){
      var tr = r; try { var rg0 = document.createRange(); var rs = []; for (var k2 = 0; k2 < e.childNodes.length; k2++) if (e.childNodes[k2].nodeType === 3 && e.childNodes[k2].nodeValue.trim()){ rg0.selectNodeContents(e.childNodes[k2]); var b0 = rg0.getBoundingClientRect(); rs.push(b0); }
        if (rs.length){ var l0 = Math.min.apply(null, rs.map(function(x){ return x.left; })), t0 = Math.min.apply(null, rs.map(function(x){ return x.top; })), r0 = Math.max.apply(null, rs.map(function(x){ return x.right; })), b1 = Math.max.apply(null, rs.map(function(x){ return x.bottom; })); tr = [l0 / scale, t0 / scale, (r0 - l0) / scale, (b1 - t0) / scale]; } } catch (e0) {}
      out.texts.push({t: txt.slice(0, 14), r: tr, fs: parseFloat(cs.fontSize), color: cs.color});
      if (parseFloat(cs.fontSize) < floor - 0.5) out.small.push([tag, parseFloat(cs.fontSize), txt.slice(0, 14)]);
      if (/[가-힣]/.test(txt) && cs.wordBreak !== 'keep-all') out.keepall.push([tag, txt.slice(0, 14)]);
      if (r[0] < safe - 2 || r[0] + r[2] > 1920 - safe + 2 || r[1] < safe - 2 - 24 || r[1] + r[3] > 1080 - safe + 2 + 24){
        if (!/\bon-img\b|\bchip\b|\bpn\b/.test(cls)) out.offstage.push([tag, txt.slice(0, 14), Math.round(r[0]), Math.round(r[1]), Math.round(r[2]), Math.round(r[3])]);
      }
    }
    if (e.hasAttribute('data-fit')){ var tx = e.querySelector('.tx') || e; if (tx.offsetHeight > e.clientHeight + 2 || tx.scrollWidth > e.clientWidth + 2) out.overflow.push([tag, txt.slice(0, 14) || (tx.textContent || '').slice(0, 14)]); }
    if (!e.closest('.grp.hidden') && (r[0] + r[2] > 1920 + 8 || r[0] < -8 || r[1] + r[3] > 1080 + 8 || r[1] < -8) && !/\b(imgfull|scrim|band|panel|half-a|half-b|stripe|pa|grp|flair|gnum|qmark)\b/.test(cls) && !e.closest('.imgfull, .pa, .grp') ) out.offstage.push([tag, 'box', Math.round(r[0]), Math.round(r[1]), Math.round(r[2]), Math.round(r[3])]);
  }
  var tw = document.createTreeWalker(sl, NodeFilter.SHOW_TEXT, null, false), nd;
  while ((nd = tw.nextNode())){
    var tx2 = nd.nodeValue; if (!tx2 || tx2.length < 3 || !/[가-힣]/.test(tx2)) continue;
    if (nd.parentNode.closest && nd.parentNode.closest('.bgart, .katex, [aria-hidden="true"]')) continue;
    var rg = document.createRange(), pTop = null, pCh = '';
    for (var q = 0; q < tx2.length; q++){
      var c1 = tx2.charAt(q); if (/\s/.test(c1)){ pTop = null; pCh = ''; continue; }
      rg.setStart(nd, q); rg.setEnd(nd, q + 1); var rr = rg.getBoundingClientRect(); if (!rr.height) continue;
      if (pTop !== null && rr.top > pTop + rr.height * 0.6 && /[가-힣]/.test(pCh) && /[가-힣]/.test(c1)){ out.midword.push(tx2.replace(/\s+/g, ' ').trim().slice(0, 14)); break; }
      pTop = rr.top; pCh = c1;
    }
  }
  return out;
})(%d, %d)
"""


def _lum(c) -> float:
    def f(x):
        x /= 255.0
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _ratio(a, b) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _rgb(s: str):
    m = re.findall(r"[\d.]+", s)
    return tuple(float(x) for x in m[:3]) if len(m) >= 3 else (0, 0, 0)


def contrast_under(img, rect, color) -> float:
    """Worst contrast between the text colour and the pixels under its box (img = the slide rendered WITHOUT text)."""
    import numpy as np
    x, y, w, h = [int(v) for v in rect]
    y, h = y + int(h * 0.2), max(2, int(h * 0.5))  # glyph body only: underline/marker decoration sits at the bottom of the line box
    x0, y0, x1, y1 = max(0, x), max(0, y), min(img.shape[1], x + w), min(img.shape[0], y + h)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return 21.0
    reg = img[y0:y1, x0:x1].reshape(-1, 3).astype(float)
    lum = np.array([_lum(p) for p in reg[:: max(1, len(reg) // 400)]])
    sub = reg[:: max(1, len(reg) // 400)]
    tl = _lum(color)
    # compare against the pixel on the side of the text that is closest in luminance (worst case), ignoring 5% outliers
    order = np.argsort(np.abs(lum - tl))
    worst = sub[order[: max(1, int(len(order) * 0.95))][:: 1]]
    sel = worst[np.argsort(np.abs(np.array([_lum(p) for p in worst]) - tl))[:3]]
    return min(_ratio(color, tuple(p)) for p in sel)


def pixel_metrics(img) -> dict:
    """visual weight (share of non-flat 40px cells) and distinct big colour bins."""
    import numpy as np
    g = (0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2])
    H, W = g.shape
    cells = g[: H // 40 * 40, : W // 40 * 40].reshape(H // 40, 40, W // 40, 40).std(axis=(1, 3))
    weight = float((cells > 7).mean())
    small = img[::12, ::12] // 32
    keys = small[..., 0] * 64 + small[..., 1] * 8 + small[..., 2]
    vals, counts = np.unique(keys, return_counts=True)
    big = int((counts / keys.size >= 0.03).sum())
    return {"weight": round(weight, 3), "colors": big}


def _launch(p):
    for kw in ({"channel": "chrome"}, {}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(args=MUTE, **kw)
        except Exception:
            continue
    return None


def review(path: Path, out: Path | None, name: str = "") -> dict:
    """Screenshots + metrics. Returns {"results": [(level, msg)], "slides": [...], "fingerprint": [...]}."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"results": [("WARN", "Playwright not installed: slide review skipped")], "slides": [], "fingerprint": []}
    try:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        have_px = True
    except ImportError:
        have_px = False
    name = name or path.stem
    results: list[tuple[str, str]] = []
    slides: list[dict] = []
    fingerprint: list[str] = []
    errors: list[str] = []
    external: list[str] = []
    shots = []
    with sync_playwright() as p:
        b = _launch(p)
        if b is None:
            return {"results": [("WARN", "no headless browser found: slide review skipped")], "slides": [], "fingerprint": []}
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.add_init_script(SILENT_JS)
        pg.on("pageerror", lambda e: errors.append(str(e)[:160]))
        pg.on("request", lambda r: external.append(r.url[:80]) if not r.url.startswith(("file:", "data:", "blob:", "about:")) else None)
        pg.goto(path.resolve().as_uri() + "?static=1")
        pg.wait_for_function("window.__stage && window.__stage.ready")
        pg.wait_for_timeout(500)
        n = pg.evaluate("window.__deck.count")
        floor = pg.evaluate("(window.DOC.deck||{}).floor || 28")
        for i in range(n):
            pg.evaluate(f"window.__deck.go({i}, true)")
            pg.wait_for_timeout(450)  # animations are off (?static=1); this is for chart canvases / fonts
            info = pg.evaluate(PROBE_JS % (floor, SAFE))
            lay = pg.evaluate("document.querySelector('.sl.on').getAttribute('data-layout')")
            fingerprint.append(lay)
            png = pg.screenshot()
            clean = None
            if have_px:
                pg.add_style_tag(content="#__hide *{}")
                pg.evaluate("(function(){var s=document.createElement('style');s.id='__notext';s.textContent='.sl.on *{color:transparent!important;text-shadow:none!important;-webkit-text-fill-color:transparent!important;-webkit-text-stroke:0!important}.sl.on em{background:none!important;box-shadow:none!important}.sl.on canvas,.sl.on img,.sl.on video{visibility:hidden!important}';document.head.appendChild(s);})()")
                pg.wait_for_timeout(80)
                clean = pg.screenshot()
                pg.evaluate("document.getElementById('__notext').remove()")
            shots.append(png)
            m = {"n": i + 1, "layout": lay, "elements": info["elements"], "icons": info["icons"], "media": info["media"], "texts": len(info["texts"])}
            if have_px:
                arr = np.array(Image.open(io.BytesIO(png)).convert("RGB"))
                m.update(pixel_metrics(arr))
                carr = np.array(Image.open(io.BytesIO(clean)).convert("RGB"))
                low = []
                for t in info["texts"]:
                    r = contrast_under(carr, t["r"], _rgb(t["color"]))
                    if r < 4.5:
                        low.append((round(r, 2), t["t"]))
                m["min_contrast"] = round(min([x[0] for x in low] + [21.0]), 2) if low else None
                m["low_contrast"] = low[:3]
            for k in ("small", "overflow", "offstage", "midword", "keepall"):
                m[k] = info[k][:3]
            slides.append(m)
        b.close()
    # ---- results
    results.append(("FAIL" if external else "PASS", "external requests = 0" + (f": {external[:3]}" if external else "")))
    results.append(("FAIL" if errors else "PASS", "no JavaScript errors" + (f": {errors[:2]}" if errors else "")))
    try:  # colour-blind check: WARN only (shared/design/color_check.py via the page checker)
        from check_page import color_blind_results
        results += color_blind_results(Path(path).read_text(encoding="utf-8", errors="replace"))
    except ImportError:
        pass

    def agg(key, label, level="FAIL", fmt=None):
        bad = [(s["n"], s[key]) for s in slides if s.get(key)]
        results.append((level if bad else "PASS", label + (f": {[(a, b_[:2]) for a, b_ in bad[:4]]}" if bad else "")))

    agg("small", f"all text >= {floor}px")
    agg("overflow", "no text overflow")
    agg("offstage", "everything inside the stage and the 96px safe margin", "FAIL")
    agg("keepall", "keep-all line breaking on Korean text")
    agg("midword", "no Korean word split across lines", "FAIL")
    if have_px:
        bad = [(s["n"], s["low_contrast"]) for s in slides if s.get("low_contrast")]
        results.append(("FAIL" if bad else "PASS", "contrast >= 4.5:1 on real pixels" + (f": {bad[:4]}" if bad else "")))
        bad = [(s["n"], s["weight"]) for s in slides if s["weight"] < 0.05]
        results.append(("FAIL" if bad else "PASS", "no empty-looking slide (visual weight >= 0.05)" + (f": {bad}" if bad else "")))
        wv = [s["weight"] for s in slides]
        results.append(("PASS", f"visual weight min {min(wv):.2f} / mean {sum(wv) / len(wv):.2f}"))
        bad = [(s["n"], s["colors"]) for s in slides if s["colors"] > (CAPS["colors_media"] if s["media"] else CAPS["colors"])]
        results.append(("FAIL" if bad else "PASS", f"CLUTTER colours: <= {CAPS['colors']} big colour bins per slide" + (f": {bad}" if bad else "")))
    else:
        results.append(("WARN", "numpy/Pillow missing: contrast, weight and colour metrics skipped"))
    bad = [(s["n"], s["elements"]) for s in slides if s["elements"] > CAPS["elements"]]
    results.append(("FAIL" if bad else "PASS", f"CLUTTER elements: <= {CAPS['elements']} per slide" + (f": {bad}" if bad else "")))
    bad = [(s["n"], s["icons"]) for s in slides if s["icons"] > CAPS["icons"]]
    results.append(("FAIL" if bad else "PASS", f"CLUTTER icons: <= {CAPS['icons']} per slide" + (f": {bad}" if bad else "")))
    run = [i + 1 for i in range(len(fingerprint) - 2) if fingerprint[i] == fingerprint[i + 1] == fingerprint[i + 2]]
    results.append(("FAIL" if run else "PASS", "no 3 consecutive identical layouts" + (f": from slide {run}" if run else "")))
    adj = [i + 1 for i in range(len(fingerprint) - 1) if fingerprint[i] == fingerprint[i + 1]]
    results.append(("WARN" if adj else "PASS", "no identical layout twice in a row" + (f": slides {adj}" if adj else "")))
    variety = len(set(fingerprint)) / max(1, len(fingerprint))
    results.append(("WARN" if variety < 0.6 and len(fingerprint) > 5 else "PASS", f"layout variety {len(set(fingerprint))}/{len(fingerprint)}"))
    if out and shots:
        out.mkdir(parents=True, exist_ok=True)
        (out / name).mkdir(exist_ok=True)
        for i, png in enumerate(shots, 1):
            (out / name / f"{i:02d}.png").write_bytes(png)
        if have_px:
            sheet(shots, fingerprint, out / f"{name}-sheet.png")
        (out / f"{name}-metrics.json").write_text(json.dumps({"file": path.name, "caps": CAPS, "slides": slides, "fingerprint": fingerprint,
                                                              "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"results": results, "slides": slides, "fingerprint": fingerprint}


def sheet(shots: list[bytes], labels: list[str], dest: Path, cols: int = 4, tw: int = 480) -> None:
    from PIL import Image, ImageDraw, ImageFont
    th = tw * 9 // 16
    rows = -(-len(shots) // cols)
    pad = 14
    img = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad + 26) + pad), (28, 28, 32))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for i, png in enumerate(shots):
        im = Image.open(io.BytesIO(png)).convert("RGB").resize((tw, th), Image.LANCZOS)
        x, y = pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + pad + 26)
        img.paste(im, (x, y))
        d.text((x, y + th + 4), f"{i + 1:02d}  {labels[i]}", fill=(220, 220, 230), font=font)
    img.save(dest)


def fingerprint_of(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    lay = re.findall(r'data-layout="([^"]+)"', html)
    m = re.search(r'"style": "([^"]+)"', html)
    pr = re.search(r'"pr": "(#[0-9a-fA-F]{6})"', html)
    return {"layouts": lay, "style": m.group(1) if m else "", "pr": pr.group(1) if pr else "#000000"}


def distance(a: dict, b: dict) -> float:
    """0 = same deck look, 1 = completely different: style (0.4) + layout set (0.3) + accent colour (0.3)."""
    sa, sb = set(a["layouts"]), set(b["layouts"])
    jac = len(sa & sb) / max(1, len(sa | sb))
    ca = [int(a["pr"][i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b["pr"][i:i + 2], 16) for i in (1, 3, 5)]
    dist = sum((x - y) ** 2 for x, y in zip(ca, cb)) ** 0.5
    seq = sum(1 for x, y in zip(a["layouts"], b["layouts"]) if x == y) / max(1, min(len(a["layouts"]), len(b["layouts"])))
    return round(0.4 * (a["style"] != b["style"]) + 0.3 * (1 - 0.5 * jac - 0.5 * seq) + 0.3 * min(1.0, dist / 150), 3)


def compare(paths: list[Path], min_dist: float = 0.35) -> list[tuple[str, str]]:
    fps = [fingerprint_of(p) for p in paths]
    out = []
    for i in range(len(fps)):
        for j in range(i + 1, len(fps)):
            d = distance(fps[i], fps[j])
            out.append(("PASS" if d >= min_dist else "FAIL", f"sameness {paths[i].name} vs {paths[j].name}: distance {d} (styles {fps[i]['style']} / {fps[j]['style']}; need >= {min_dist})"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", nargs="?", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--name", default="")
    ap.add_argument("--compare", nargs="+", type=Path)
    a = ap.parse_args()
    if a.compare:
        res = compare(a.compare)
        for lv, msg in res:
            print(f"{lv:4} {msg}")
        return 1 if any(lv == "FAIL" for lv, _ in res) else 0
    if not a.deck:
        ap.error("deck.html or --compare required")
    r = review(a.deck, a.out, a.name)
    for lv, msg in r["results"]:
        print(f"{lv:4} {msg}")
    fails = sum(1 for lv, _ in r["results"] if lv == "FAIL")
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({fails} fail, {sum(1 for lv, _ in r['results'] if lv == 'WARN')} warn)")
    if a.out:
        print(f"sheet: {a.out / ((a.name or a.deck.stem) + '-sheet.png')}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
