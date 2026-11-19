#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""ref_analyze: learn design PATTERNS from one public page the user points to. Never copies.

Usage:  python ref_analyze.py URL|local.html [--out DIR] [--scroll-video] [--ignore-robots-local]
Outputs (default DIR = ~/TeacherStudio/ref/<host-or-name>/):
    analysis.json, analysis.html (one-page contact sheet), tokens-suggestion.json,
    shot-mobile-full.png, shot-mobile-fold.png, shot-desktop-full.png, shot-desktop-fold.png
Rules (enforced here):
  - one page, one load per viewport (390x844, 1440x900). No crawling, no login, no clicking.
  - http(s) only: robots.txt is read first and the run STOPS if the path is disallowed.
  - nothing from the page is saved except our own screenshots + numbers (no HTML, images, fonts, scripts).
  - values are rounded "inspired by" numbers. Text, logos, images and code are never reused.
  - Chrome runs muted (--mute-audio).
Needs: playwright (ensure.py playwright) + system Chrome.
"""
from __future__ import annotations

import argparse
import colorsys
import html
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter
from pathlib import Path

UA = "TeacherStudioRefAnalyzer/1.0 (single page, design-pattern study)"
VIEWPORTS = {"mobile": (390, 844), "desktop": (1440, 900)}
LEGAL_KO = "구조와 느낌만 배우고, 글·그림·로고·코드는 가져오지 않아요."

# ---------------------------------------------------------------- in-page extraction
JS = r"""
() => {
  const vw = innerWidth, vh = innerHeight;
  const page = {w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight};
  const parse = c => { const m = c && c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}; };
  const hex = c => '#' + [c.r,c.g,c.b].map(v => Math.round(v).toString(16).padStart(2,'0')).join('');
  const all = [...document.body.querySelectorAll('*')].slice(0, 5000);
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05; };
  const bgOf = el => { let e = el; while (e) { const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0.9) return c; e = e.parentElement; } return {r:255,g:255,b:255,a:1}; };
  const lum = c => { const f = v => { v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055,2.4); };
    return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b); };
  const ratio = (a,b) => { const x = lum(a), y = lum(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
  const bgArea = {}, textArea = {}, fonts = {}, sizes = {}, weights = {}, lines = {}, spacing = {}, radii = {}, shadows = {},
        maxw = {}, trans = {}, anims = {}, easing = {}, contrastPairs = {}, headings = {};
  const add = (o,k,n=1) => { if (k === undefined || k === null || k === '') return; o[k] = (o[k]||0) + n; };
  let tapTotal = 0, tapSmall = 0;
  const comps = {buttons:0, cards:0, chips:0, tabs:0, nav:0, inputs:0, images:0, icons_svg:0, forms:0};
  const cardSigs = {};
  const area = Math.max(1, page.w * page.h);
  for (const el of all) {
    if (!vis(el)) continue;
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    const a = r.width * r.height;
    const bg = parse(s.backgroundColor);
    if (bg && bg.a > 0.2 && a / area < 1.5) add(bgArea, hex(bg), a / 1000 * Math.min(1, bg.a + .2));
    // text: only elements with direct text
    let tl = 0; for (const n of el.childNodes) if (n.nodeType === 3) tl += n.textContent.trim().length;
    if (tl > 0) {
      const tc = parse(s.color), fs = parseFloat(s.fontSize);
      if (tc) add(textArea, hex(tc), tl * fs);
      add(fonts, s.fontFamily.split(',')[0].replace(/["']/g,'').trim(), tl);
      add(sizes, Math.round(fs), tl); add(weights, s.fontWeight, tl);
      if (s.lineHeight !== 'normal') add(lines, (parseFloat(s.lineHeight)/fs).toFixed(2), tl);
      if (tc) { const b = bgOf(el), cr = ratio(tc, b); const k = hex(tc)+' on '+hex(b);
        if (!contrastPairs[k]) contrastPairs[k] = {fg:hex(tc), bg:hex(b), ratio:+cr.toFixed(2), size:fs, weight:+s.fontWeight, n:0};
        contrastPairs[k].n += tl; }
    }
    if (/^H[1-6]$/.test(el.tagName)) { const k = el.tagName.toLowerCase();
      if (!headings[k]) headings[k] = {size:parseFloat(s.fontSize), weight:+s.fontWeight, lh:s.lineHeight, family:s.fontFamily.split(',')[0].replace(/["']/g,'').trim()}; }
    for (const p of ['paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginBottom','rowGap','columnGap'])
      { const v = parseFloat(s[p]); if (v > 0 && v <= 200) add(spacing, Math.round(v)); }
    const br = s.borderTopLeftRadius; if (br && br !== '0px') add(radii, br.includes('%') ? '50%' : Math.min(999, Math.round(parseFloat(br))) + 'px');
    if (s.boxShadow && s.boxShadow !== 'none') add(shadows, s.boxShadow.replace(/rgba?\([^)]*\)/g, m => { const c = parse(m); return c ? hex(c)+(c.a<1?'@'+c.a:'') : m; }).slice(0, 90));
    if (s.maxWidth !== 'none' && s.maxWidth.endsWith('px') && (s.marginLeft === 'auto' || s.marginRight === 'auto' || parseFloat(s.marginLeft) > 0))
      add(maxw, Math.round(parseFloat(s.maxWidth)));
    if (s.transitionDuration && s.transitionDuration !== '0s') {
      const durs = s.transitionDuration.split(',').map(x => x.trim()); const props = s.transitionProperty.split(',').map(x => x.trim());
      durs.forEach((d,i) => { if (d !== '0s') { add(trans, (props[i % props.length]) + ' ' + d); } });
      add(easing, s.transitionTimingFunction.split(/,(?![^(]*\))/)[0].trim());
    }
    if (s.animationName && s.animationName !== 'none') { add(anims, s.animationName + ' ' + s.animationDuration + ' ' + s.animationTimingFunction.split(/,(?![^(]*\))/)[0]); }
    // tap targets
    const tag = el.tagName;
    if (tag === 'A' || tag === 'BUTTON' || tag === 'INPUT' || tag === 'SELECT' || el.getAttribute('role') === 'button' || el.getAttribute('role') === 'tab') {
      tapTotal++; if (Math.min(r.width, r.height) < 44) tapSmall++;
    }
    // components
    const role = el.getAttribute('role');
    if (tag === 'BUTTON' || role === 'button' || (tag === 'A' && /btn|button/i.test(el.className + ''))) comps.buttons++;
    if (role === 'tab') comps.tabs++;
    if (tag === 'NAV') comps.nav++;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') comps.inputs++;
    if (tag === 'FORM') comps.forms++;
    if (tag === 'IMG' || tag === 'PICTURE' || tag === 'VIDEO') comps.images++;
    if (tag === 'svg') comps.icons_svg++;
    const rad = parseFloat(br) || 0;
    if (r.height <= 44 && r.height >= 18 && r.width < 220 && rad >= r.height / 2 - 1 && (bg && bg.a > 0.05 || s.borderTopWidth !== '0px') && tl > 0 && tl < 28) comps.chips++;
    if (rad >= 4 && r.width > 140 && r.height > 80 && r.width < vw * 0.9 && (s.boxShadow !== 'none' || s.borderTopWidth !== '0px' || (bg && bg.a > .9)) && el.querySelector('h1,h2,h3,h4,p,img')) {
      const sig = Math.round(r.width/20) + 'x' + el.className.toString().split(' ')[0];
      cardSigs[sig] = (cardSigs[sig]||0) + 1;
    }
  }
  comps.cards = Object.values(cardSigs).filter(n => n >= 2).reduce((a,b) => a+b, 0);
  // keyframes count
  let keyframes = 0; try { for (const sh of document.styleSheets) { try { for (const rule of sh.cssRules) if (rule.type === 7) keyframes++; } catch(e){} } } catch(e){}
  // sections
  const root = document.querySelector('main') || document.body;
  let kids = [...document.body.children].filter(vis);
  if (kids.length <= 3 && root !== document.body) kids = [document.body.children[0], ...root.children].filter(x => x && vis(x));
  const sections = [];
  const seen = new Set();
  const addSec = el => {
    if (seen.has(el)) return; seen.add(el);
    const r = el.getBoundingClientRect(); if (r.height < 40) return;
    const s = getComputedStyle(el);
    const kidsEls = [...el.querySelectorAll(':scope > * > *, :scope > *')];
    const sig = {}; kidsEls.forEach(k => { const kr = k.getBoundingClientRect(); if (kr.width > 80 && kr.height > 60) { const key = k.tagName + Math.round(kr.width/30); sig[key] = (sig[key]||0)+1; } });
    const repeat = Math.max(0, ...Object.values(sig));
    const roleGuess = [];
    const top = r.top + scrollY;
    if (el.tagName === 'HEADER' || (top < 120 && el.querySelector('nav') && r.height < 200)) roleGuess.push('header/nav');
    if (el.tagName === 'FOOTER' || top > page.h - r.height - 40 && el.querySelector('a') && r.height < 700 && top > page.h * 0.7) roleGuess.push('footer');
    if (el.querySelector('h1')) roleGuess.push('hero');
    if (el.querySelector('input[type=search],[role=search],input[placeholder*=earch]')) roleGuess.push('search');
    if (el.querySelector('[role=tablist]')) roleGuess.push('tabs');
    if (repeat >= 3) roleGuess.push('card-grid(' + repeat + ')');
    if (el.querySelector('video')) roleGuess.push('video');
    if (!roleGuess.length) roleGuess.push('content');
    sections.push({tag: el.tagName.toLowerCase(), top: Math.round(top), height: Math.round(r.height), roles: roleGuess,
      display: s.display, columns: s.display === 'grid' ? s.gridTemplateColumns.split(' ').length : null,
      bg: hex(bgOf(el)), headingsN: el.querySelectorAll('h1,h2,h3').length});
  };
  kids.forEach(k => { const r = k.getBoundingClientRect();
    if (r.height > 1200 && k.children.length) [...k.children].filter(vis).forEach(addSec); else addSec(k); });
  // widest centered content block
  let content = 0; const midx = vw / 2;
  for (const el of all) { const r = el.getBoundingClientRect(); if (r.width > 200 && r.width < vw - 1 && Math.abs((r.left + r.width/2) - midx) < 8 && r.height > 60) content = Math.max(content, Math.round(r.width)); }
  const top = (o, n=8) => Object.entries(o).sort((a,b) => b[1]-a[1]).slice(0, n);
  return {vw, vh, page, bgArea: top(bgArea, 12), textArea: top(textArea, 8), fonts: top(fonts, 5), sizes: top(sizes, 14),
    weights: top(weights, 6), lineHeights: top(lines, 6), spacing: top(spacing, 24), radii: top(radii, 6), shadows: top(shadows, 5),
    maxWidths: top(maxw, 5), contentWidth: content, transitions: top(trans, 10), easings: top(easing, 5), animations: top(anims, 6),
    keyframes, headings, comps, sections: sections.slice(0, 24),
    contrast: Object.values(contrastPairs).sort((a,b) => b.n-a.n).slice(0, 10),
    tap: {total: tapTotal, small: tapSmall}, lang: document.documentElement.lang || '', title_len: document.title.length,
    hasVideo: !!document.querySelector('video'), htmlBg: hex(bgOf(document.body))};
}
"""

# ---------------------------------------------------------------- helpers

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in c)


def hsv(h):
    r, g, b = [v / 255 for v in hex_to_rgb(h)]
    return colorsys.rgb_to_hsv(r, g, b)


def lum(h):
    def f(v):
        v /= 255
        return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(h)
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def ratio(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + .05) / (min(x, y) + .05)


def soften(h, step=8):
    """round each channel to a multiple of `step`: inspired-by, not a pixel clone."""
    return rgb_to_hex([round(v / step) * step for v in hex_to_rgb(h)])


def merge_close(items, tol=18):
    """merge near-identical colors; items = [(hex, weight)]"""
    out = []
    for h, w in items:
        for o in out:
            if sum(abs(a - b) for a, b in zip(hex_to_rgb(h), hex_to_rgb(o[0]))) <= tol:
                o[1] += w
                break
        else:
            out.append([h, w])
    return sorted(out, key=lambda x: -x[1])


def grid_unit(spacing):
    vals = [(int(k), n) for k, n in spacing if int(k) >= 2]
    total = sum(n for _, n in vals) or 1
    best = (0, 4)
    for u in (4, 5, 6, 8):
        fit = sum(n for v, n in vals if v % u == 0) / total
        score = fit + (0.04 if u == 8 else 0.02 if u == 4 else 0)
        if score > best[0]:
            best = (score, u)
    return best[1], round(best[0], 2)


def robots_ok(url):
    p = urllib.parse.urlparse(url)
    ru = f"{p.scheme}://{p.netloc}/robots.txt"
    try:
        req = urllib.request.Request(ru, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read(500_000).decode("utf-8", "replace")
    except Exception as e:  # no robots.txt (404) = allowed; network error = report and allow nothing silently
        code = getattr(e, "code", None)
        if code in (404, 410):
            return True, "robots.txt not found (allowed)"
        return False, f"could not read robots.txt ({e}); stopping to be safe"
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(body.splitlines())
    ok = rp.can_fetch(UA, url) and rp.can_fetch("*", url)
    return ok, "robots.txt allows this path" if ok else "robots.txt DISALLOWS this path"


# ---------------------------------------------------------------- analysis

def analyze_viewport(page, name, w, h, url, out):
    page.set_viewport_size({"width": w, "height": h})
    page.goto(url, wait_until="load", timeout=45000)
    try:
        page.wait_for_load_state("networkidle", timeout=6000)
    except Exception:
        pass
    # trigger lazy layout once by scrolling through, then return (still the same single load)
    total = page.evaluate("document.documentElement.scrollHeight")
    for y in range(0, min(total, 12000), h):
        page.evaluate(f"window.scrollTo(0,{y})")
        page.wait_for_timeout(120)
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(400)
    data = page.evaluate(JS)
    page.screenshot(path=str(out / f"shot-{name}-fold.png"))
    try:
        page.screenshot(path=str(out / f"shot-{name}-full.png"), full_page=True)
    except Exception:
        pass
    data["has_h_scroll"] = data["page"]["w"] > w + 2
    return data


def summarize(d):
    """build merged palette + tokens from the desktop (fallback mobile) data"""
    bgs = merge_close([(h, w) for h, w in d["bgArea"]])
    txt = merge_close([(h, w) for h, w in d["textArea"]])
    page_bg = d["htmlBg"]
    if not bgs or bgs[0][0] != page_bg:
        bgs.insert(0, [page_bg, 1e9])
        bgs = merge_close([(h, w) for h, w in bgs])
    sat = []
    for h, w in merge_close([(h, w) for h, w in d["bgArea"] + d["textArea"]]):
        s, v = hsv(h)[1], hsv(h)[2]
        if s > 0.35 and 0.25 < v:
            sat.append((h, w, s))
    sat.sort(key=lambda x: -(x[1] ** 0.5) * x[2])
    return bgs, txt, sat


def make_tokens(data, src):
    d = data["desktop"]
    bgs, txt, sat = summarize(d)
    bg1 = bgs[0][0]
    dark = lum(bg1) < 0.25
    bg2 = next((h for h, _ in bgs[1:] if h != bg1), bg1)
    text = next((h for h, _ in txt if ratio(h, bg1) >= 4.5), "#f5f5f5" if dark else "#1b1b1b")
    primary = sat[0][0] if sat else (txt[0][0] if txt else "#2563eb")
    accent = next((h for h, _, _ in sat[1:] if sum(abs(a - b) for a, b in zip(hex_to_rgb(h), hex_to_rgb(primary))) > 120), None)
    if not accent:
        hh, ss, vv = hsv(primary)
        accent = rgb_to_hex([c * 255 for c in colorsys.hsv_to_rgb((hh + 0.08) % 1, min(1, ss + .1), min(1, vv))])
    card = next((h for h, _ in bgs if h not in (bg1,) and abs(lum(h) - lum(bg1)) < 0.35), bg2)
    cardText = text if ratio(text, card) >= 4.5 else ("#ffffff" if lum(card) < .4 else "#1b1b1b")
    btnText = "#ffffff" if ratio("#ffffff", primary) >= ratio("#111111", primary) else "#111111"
    unit, fit = grid_unit(d["spacing"])
    h1 = float(d["headings"].get("h1", {}).get("size") or (max(int(x[0]) for x in d["sizes"]) if d["sizes"] else 40))
    body_sz = int(d["sizes"][0][0]) if d["sizes"] else 16
    k = 1920 / 1440  # written for our 1920x1080 stage
    fam = d["fonts"][0][0] if d["fonts"] else ""
    disp = d["headings"].get("h1", {}).get("family") or fam
    radii_px = [int(r[0][:-2]) for r in d["radii"] if r[0].endswith("px") and int(r[0][:-2]) < 100]
    radius = round(sorted(radii_px, key=lambda r: -dict(d["radii"]).get(f"{r}px", 0))[0] / 2) * 2 if radii_px else 8
    maxw = int(d["maxWidths"][0][0]) if d["maxWidths"] else d["contentWidth"]
    return {
        "version": 1, "use": "web", "palette": "ref-inspired",
        "colors": {"bg1": soften(bg1), "bg2": soften(bg2), "text": soften(text), "card": soften(card), "cardText": soften(cardText),
                   "cardBorder": soften(rgb_to_hex([(a + b) / 2 for a, b in zip(hex_to_rgb(card), hex_to_rgb(cardText))]) if False else
                                        rgb_to_hex([a * .85 + b * .15 for a, b in zip(hex_to_rgb(card), hex_to_rgb(cardText))])),
                   "primary": soften(primary), "btnText": btnText, "accent": soften(accent), "good": "#16a34a", "bad": "#dc2626"},
        "fonts": {"display": "(choose our own: " + (disp or "sans") + "-like feel)", "body": "(choose our own: " + (fam or "sans") + "-like feel)"},
        "type": {"title": max(40, round(h1 * k / 4) * 4), "question": max(24, round(h1 * k * .6 / 4) * 4),
                 "choice": max(18, round(body_sz * k * 1.2 / 2) * 2), "body": max(16, round(body_sz * k / 2) * 2),
                 "small": max(12, round(body_sz * k * .8 / 2) * 2),
                 "floor": {"question": 24, "choice": 18, "body": 16, "small": 12, "button_h": 44}},
        "canvas": "1920x1080", "motion": "normal", "sound": {"sfx": False, "music": False},
        "_inspired_by": {
            "source": src, "note": "Rounded, softened values. Use as a starting point, never as a clone. " + LEGAL_KO,
            "dark_theme": dark, "spacing_unit_px": unit, "spacing_unit_fit": fit, "radius_px": radius,
            "container_max_width_px": maxw, "type_ratio_h1_to_body": round(h1 / max(1, body_sz), 2),
            "font_note": "Fonts are only REPORTED. Do not download or embed them; pick a font from shared/fonts with a similar feel.",
            "motion_feel_ms": [x[0] for x in d["transitions"][:3]], "easing": [x[0] for x in d["easings"][:2]],
        },
    }


def patterns_ko(data, tokens):
    """3-5 plain-Korean pattern lines drawn from the numbers (AI should refine after looking at the screenshots)."""
    d, m = data["desktop"], data["mobile"]
    ins = tokens["_inspired_by"]
    out = []
    out.append(("어두운 바탕 위에 글씨를 밝게" if ins["dark_theme"] else "밝은 바탕에 진한 글씨") +
               f"로, 색은 바탕·글씨 말고 강조색 하나({tokens['colors']['primary']} 계열)만 눈에 띄게 써요.")
    ratio_h = ins["type_ratio_h1_to_body"]
    out.append(f"제목이 본문의 약 {ratio_h}배로 커서 한눈에 위계가 보여요." if ratio_h >= 2.2 else f"제목과 본문 크기 차이가 작아(약 {ratio_h}배) 차분하고 읽기 중심이에요.")
    out.append(f"간격은 {ins['spacing_unit_px']}px 단위로 맞추고(맞는 비율 {int(ins['spacing_unit_fit']*100)}%), 모서리는 약 {ins['radius_px']}px로 통일해요.")
    if ins["container_max_width_px"]:
        out.append(f"내용 폭을 약 {ins['container_max_width_px']}px 안으로 모아 넓은 화면에서도 읽기 편해요.")
    roles = [r for s in d["sections"] for r in s["roles"]]
    if any(r.startswith("card-grid") for r in roles):
        out.append("카드를 격자로 반복해 훑어보기 쉬운 구성이에요.")
    if d["transitions"]:
        out.append(f"움직임은 {d['transitions'][0][0]} 정도의 짧은 전환 위주예요.")
    return out[:5]


def build_html(out, name, url, data, tokens, patterns):
    d = data["desktop"]
    bgs, txt, sat = summarize(d)
    sw = lambda h, lab="": f'<div class="sw"><i style="background:{html.escape(str(h))}"></i><b>{html.escape(str(h))}</b><small>{html.escape(lab)}</small></div>'
    colors = "".join(sw(h, f"area {int(w)}") for h, w in bgs[:6]) + "".join(sw(h, "text") for h, _ in txt[:4]) + "".join(sw(h, "accent") for h, _, _ in sat[:3])
    tok = "".join(sw(v, k) for k, v in tokens["colors"].items())
    sizes = "".join(f'<span style="font-size:{min(int(k), 60)}px">{k}px<small> ×{n}</small></span>' for k, n in sorted(d["sizes"], key=lambda x: -int(x[0])))
    sp = "".join(f'<span class="chip"><i style="width:{min(int(k), 120)}px"></i>{k}px<small> ×{n}</small></span>' for k, n in d["spacing"][:12])
    rad = "".join(f'<span class="chip"><i class="r" style="border-radius:{html.escape(str(r))}"></i>{html.escape(str(r))}</span>' for r, _ in d["radii"])
    secs = "".join(f"<li>{s['top']}px · {s['height']}px · {html.escape(', '.join(str(x) for x in s['roles']))}</li>" for s in d["sections"][:14])
    comps = ", ".join(html.escape(f"{k}: {v}") for k, v in d["comps"].items() if v)
    con = "".join(f"<li>{html.escape(str(c['fg']))} on {html.escape(str(c['bg']))} = <b class=\"{'ok' if c['ratio'] >= 4.5 else 'warn'}\">{c['ratio']}</b></li>" for c in d["contrast"][:6])
    pat = "".join(f"<li>{html.escape(p)}</li>" for p in patterns)
    css = """body{font:15px/1.5 system-ui,'Malgun Gothic',sans-serif;margin:0;background:#f6f6f4;color:#1b1b1b}
main{max-width:1200px;margin:auto;padding:24px}h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 8px;border-bottom:1px solid #ddd;padding-bottom:4px}
.shots{display:flex;gap:16px;align-items:flex-start}.shots img{border:1px solid #ccc;border-radius:8px;background:#fff}
.sws{display:flex;flex-wrap:wrap;gap:8px}.sw{width:92px;font-size:11px}.sw i{display:block;height:44px;border-radius:6px;border:1px solid #0002}.sw b{display:block;font-family:monospace}
.chip{display:inline-flex;align-items:center;gap:6px;margin:3px 8px 3px 0;font-size:12px}.chip i{display:inline-block;height:10px;background:#4a6cf7;border-radius:2px}.chip i.r{width:28px;height:28px;background:#ddd;border:1px solid #999}
small{color:#777}.ok{color:#16a34a}.warn{color:#dc2626}.legal{background:#fff7d6;padding:8px 12px;border-radius:8px;margin:12px 0}ul{margin:4px 0 4px 18px;padding:0}
.type span{display:block;line-height:1.25;margin:2px 0}"""
    page = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><title>reference analysis - {html.escape(name)}</title><style>{css}</style><main>
<h1>참고 분석: {html.escape(name)}</h1><small>{html.escape(url)} · 구조와 느낌만 배우는 자료예요</small>
<div class="legal">{LEGAL_KO} 값은 반올림·약화한 「영감」 수치이며 그대로 복제하지 않아요 (상표·트레이드드레스 주의).</div>
<h2>좋은 점 3~5가지 (자동 초안, AI가 화면을 보고 다듬기)</h2><ul>{pat}</ul>
<h2>화면 (데스크톱 / 모바일 첫 화면)</h2><div class="shots"><img src="shot-desktop-fold.png" width="640"><img src="shot-mobile-fold.png" width="200"><img src="shot-mobile-full.png" width="120"></div>
<h2>색 (면적순 / 글씨 / 강조)</h2><div class="sws">{colors}</div>
<h2>우리 토큰 제안 (약화된 값)</h2><div class="sws">{tok}</div>
<h2>글자 크기 척도 (본문 {d['sizes'][0][0] if d['sizes'] else '?'}px · 글꼴: {html.escape(', '.join(f[0] for f in d['fonts'][:3]))} · 굵기 {html.escape(', '.join(str(w[0]) for w in d['weights'][:4]))})</h2><div class="type">{sizes}</div>
<h2>간격 리듬 (추정 단위 {tokens['_inspired_by']['spacing_unit_px']}px)</h2>{sp}
<h2>모서리</h2>{rad}<h2>그림자</h2><ul>{''.join(f'<li><code>{html.escape(s[0])}</code> ×{s[1]}</li>' for s in d['shadows'][:4]) or '<li>거의 없음</li>'}</ul>
<h2>구조 (위에서 아래로)</h2><ul>{secs}</ul><small>폭: 내용 {d['contentWidth']}px · max-width {html.escape(str(d['maxWidths'][:3]))}</small>
<h2>부품 수</h2><p>{comps}</p>
<h2>움직임</h2><ul>{''.join(f'<li>{html.escape(t[0])} ×{t[1]}</li>' for t in d['transitions'][:6]) or '<li>전환 거의 없음</li>'}</ul><small>easing {html.escape(str(d['easings'][:3]))} · keyframes {html.escape(str(d['keyframes']))} · 애니메이션 {html.escape(str(d['animations'][:3]))}</small>
<h2>접근성 신호</h2><ul>{con}</ul><small>모바일 탭 대상 {data['mobile']['tap']['small']}/{data['mobile']['tap']['total']}개가 44px 미만 · 모바일 가로 스크롤 {'있음' if data['mobile']['has_h_scroll'] else '없음'}</small>
</main></html>"""
    (out / "analysis.html").write_text(page, encoding="utf-8")


def scroll_video(url, out):
    """optional: record 5s of the same single page load scrolling, then hand it to video_eyes."""
    from playwright.sync_api import sync_playwright
    vdir = out / "_rec"
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True, args=["--mute-audio"])
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(vdir), record_video_size={"width": 960, "height": 600}, user_agent=UA)
        pg = ctx.new_page()
        pg.goto(url, wait_until="load", timeout=45000)
        for i in range(10):
            pg.evaluate("window.scrollBy(0, 500)")
            pg.wait_for_timeout(500)
        ctx.close()
        b.close()
    vids = list(vdir.glob("*.webm"))
    if not vids:
        return None
    ve = Path(__file__).resolve().parents[2] / "shared" / "tools" / "video_eyes.py"
    if not ve.exists():
        ve = Path(__file__).resolve().parents[1] / "shared" / "tools" / "video_eyes.py"
    subprocess.run([sys.executable, str(ve), str(vids[0]), "--out", str(out / "scroll-eyes"), "--max", "12"], check=False)
    vids[0].unlink(missing_ok=True)  # keep only our frames, not a recording of their page
    try:
        vdir.rmdir()
    except OSError:
        pass
    return str(out / "scroll-eyes" / "sheet.png")


def main():
    ap = argparse.ArgumentParser(description="learn design patterns from one public page (never copies)")
    ap.add_argument("target", help="http(s) URL or local .html file")
    ap.add_argument("--out", help="output dir (default ~/TeacherStudio/ref/<name>)")
    ap.add_argument("--scroll-video", action="store_true", help="also record a 5s scroll and make a contact sheet via video_eyes")
    a = ap.parse_args()

    t = a.target
    if re.match(r"^https?://", t, re.I):
        url = t
        host = urllib.parse.urlparse(t).netloc
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", host)
        ok, why = robots_ok(url)
        print(f"robots: {why}")
        if not ok:
            print("중단: 이 페이지는 사이트가 자동 열람을 허용하지 않아요. 스크린샷을 직접 주시면 그걸로 배울게요.")
            return 3
    else:
        p = Path(t).expanduser().resolve()
        if not p.exists():
            print("file not found:", t)
            return 2
        url = p.as_uri()
        name = p.parent.name or p.stem
    out = Path(a.out) if a.out else Path.home() / "TeacherStudio" / "ref" / name
    out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright
    data = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True, args=["--mute-audio"])
        for vname, (w, h) in VIEWPORTS.items():
            ctx = b.new_context(viewport={"width": w, "height": h}, user_agent=UA, accept_downloads=False,
                                is_mobile=(vname == "mobile"), has_touch=(vname == "mobile"))
            ctx.route("**/*", lambda route: route.abort() if route.request.resource_type in ("media",) else route.continue_())
            page = ctx.new_page()
            data[vname] = analyze_viewport(page, vname, w, h, url, out)
            ctx.close()
        b.close()

    tokens = make_tokens(data, url if url.startswith("http") else "local file")
    patterns = patterns_ko(data, tokens)
    d = data["desktop"]
    result = {"source": url if url.startswith("http") else "local file", "legal": LEGAL_KO,
              "caution": "Only structure/feel is studied. Text, images, logos, code and fonts are not copied; trade dress may be protected.",
              "patterns_ko_draft": patterns, "desktop": data["desktop"], "mobile": data["mobile"],
              "fonts_report": {"families": d["fonts"], "note": "report only; may be licensed. Do not embed."}}
    if a.scroll_video:
        result["scroll_sheet"] = scroll_video(url, out)
    (out / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "tokens-suggestion.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=1), encoding="utf-8")
    build_html(out, name, result["source"], data, tokens, patterns)
    print(f"done: {out / 'analysis.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
