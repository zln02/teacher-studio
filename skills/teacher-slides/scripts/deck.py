#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Spec -> designed slide deck (one offline HTML). `studio.py build slides --spec deck.json` calls this.

Usage:
    python3 deck.py --spec deck.json [--out deck.html] [--seed N] [--purpose 연수] [--mood 깔끔하게] [--style minimal-premium] [--review DIR] [--pptx [OUT.pptx]] [--template my.pptx]
Flow: normalise + validate spec -> pick style/palette from words (fresh seed unless --seed / spec.seed; the seed is printed) ->
      per-slide layout variants (no repeat in a row) -> HTML + CSS + runtime -> check_page (static) -> optional slides_review (screenshots, metrics).
Legacy lesson-deck content (items[].layout) is accepted too. `studio.py fire slides/...` (old missiles) is untouched.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import build_stage  # noqa: E402
import deck_art as art  # noqa: E402
import deck_layouts as lay  # noqa: E402
import deck_spec as dspec  # noqa: E402
import deck_style as dstyle  # noqa: E402
from deck_kit import Ctx, esc  # noqa: E402

ASSETS = SKILL / "assets" / "deck"
PURPOSE_ICON = {"학부모 설명회": "heart-handshake", "수업": "graduation-cap", "연수": "lightbulb", "발표": "megaphone", "동아리": "rocket", "개인": "sparkles"}
RECENT = Path.home() / "TeacherStudio" / ".recent-styles.json"
OUT_DIR = Path.home() / "TeacherStudio"


def hex_rgba(h: str, a: float) -> str:
    r, g, b = dstyle._rgb(h)
    return f"rgba({r},{g},{b},{a})"


CARD_CSS = {
    "round": ".cd{box-shadow:0 28px 56px -28px rgba(0,0,0,.28)}",
    "flat": ".cd{box-shadow:0 20px 40px -24px rgba(0,0,0,.25)}",
    "glass": ".cd{background:rgba(255,255,255,.07);border:1.5px solid rgba(255,255,255,.26);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}",
    "hair": ".cd{background:transparent;border:1.5px solid var(--line)}",
    "sticker": ".cd{border:4px solid var(--tx);box-shadow:10px 10px 0 var(--pr)}.ch{border:3px solid var(--tx)}",
    "ticket": ".cd{border-left:14px solid var(--pr);border-radius:calc(var(--rad)*.5)}",
    "polaroid": ".cd{box-shadow:0 24px 48px -24px rgba(0,0,0,.45);border-radius:10px}",
    "pixel": ".cd{border:6px solid var(--tx);box-shadow:8px 8px 0 var(--pr);border-radius:0}.ch,.tbtn,.vbtn,.chl{border-radius:0}.disc,.dot,.dotb,.chip{border-radius:0}",
    "chalk": ".cd{background:transparent;border:3px dashed var(--line)}",
}
TITLE_CSS = {
    "glow": ".h{text-shadow:0 0 36px var(--glow)}",
    "stack3d": ".h{text-shadow:4px 4px 0 var(--pr)}.on-band,.on-b,.on-panel{text-shadow:none!important}",
    "pixel": ".h{text-shadow:4px 4px 0 var(--pr)}.on-band,.on-b,.on-panel{text-shadow:none!important}",
    "chalk": ".h{text-shadow:0 0 3px rgba(255,255,255,.35)}",
    "plain": "", "serif": "", "underline": "", "stamp": "",
}
EM_CSS = {
    "color": "em{color:var(--emc)}",
    "marker": "em{background:linear-gradient(transparent 80%,var(--pr) 80%,var(--pr) 93%,transparent 93%);padding:0 .06em}",
    "underline": "em{box-shadow:inset 0 -0.13em 0 var(--pr)}",
}


def style_css(dz: dict) -> str:
    c, lang, f = dz["colors"], dz["lang"], dz["fonts"]
    serif = lang["font"] == "serif"
    fam = lambda n: f'"{n}",' + ('"Noto Serif KR",serif' if "Serif" in n else '"Apple SD Gothic Neo","Malgun Gothic",sans-serif')
    v = (f":root{{--bg1:{c['bg1']};--bg2:{c['bg2']};--tx:{c['tx']};--mu:{c['mu']};--card:{c['card']};--ct:{c['ct']};--line:{c['line']};--pr:{c['pr']};--bt:{c['bt']};--ac:{c['ac']};"
         f"--emc:{c['emc']};--emcc:{c['emcc']};--hl:{c['hl']};--hlc:{c['hlc']};--glow:{hex_rgba(c['pr'], .55)};--good:{c['good']};--bad:{c['bad']};"
         f"--rad:{lang['rad']}px;--tw:{lang['tw']};--tls:{lang['ls']}em;--fd:{fam(f['display'])};--fb:{fam(f['body'])}}}")
    em = EM_CSS[lang["em"]] + (".ex em,.ch em{box-shadow:none}" if lang["em"] != "color" else "")
    extra = ".q,.lead{font-family:var(--fd)}" if serif else ""
    return "\n".join([v, CARD_CSS[lang["card"]], TITLE_CSS.get(lang["title"], ""), em, extra, f"body{{background:{c['bg1']}}}"])


def pick_layouts(dz: dict, slides: list[dict]) -> list[tuple[str, str, object]]:
    """Choose (variant, family, fn) per slide: seeded, weighted by the style's preferences, never the same layout twice in a row,
    prefers variants not yet used in this deck."""
    prefer = dz["lang"]["prefer"]
    used: Counter = Counter()
    fams: list[str] = []
    out = []
    prev = None
    for i, it in enumerate(slides):
        opts = [o for o in lay.REG[it["type"]] if o[3](it)]
        forced = str(it.get("layout", ""))
        if forced:
            m = [o for o in opts if forced in (o[0], f"{it['type']}.{o[0]}")]
            if m:
                opts = m
        w = {}
        for var, fam, fn, _ in opts:
            key = (it["type"], var)
            if key == prev and len(opts) > 1:
                continue
            wt = 2.0 * prefer.get(fam, 1) / (1 + 2.5 * used[key])
            if fams and fams[-1] == fam and it["type"] not in ("title", "closing"):
                wt *= 0.55
            w[var] = max(1, int(wt * 10))
        var = dstyle.weighted(w, f"lay|{dz['seed']}|{i}|{it['type']}")
        sel = next(o for o in opts if o[0] == var)
        used[(it["type"], var)] += 1
        prev = (it["type"], var)
        fams.append(sel[1])
        out.append((sel[0], sel[1], sel[2]))
    return out


def prepare(spec: dict, dz: dict) -> None:
    """Fill helper fields: section numbers, icons for illustrations."""
    sec = 0
    for it in spec["slides"]:
        if it["type"] == "section":
            sec += 1
            it["_secno"] = sec
        if it["type"] in ("statement", "closing", "section") and not it.get("_icons"):
            base = it.get("motif") or spec.get("subject") or ""
            it["_icons"] = [art.icon_name(str(base), PURPOSE_ICON.get(dz["purpose"], "sparkles"))]
        if it["type"] == "illustration":
            words = it.get("icons") or [it.get("motif", ""), it.get("_icon_word", ""), spec.get("subject", ""), it.get("title", "")]
            names = []
            for wd in words if isinstance(words, list) else [words]:
                if wd:
                    n = art.icon_name(str(wd), "")
                    if n and n not in names:
                        names.append(n)
            it["_icons"] = names or ["sparkles"]


def build_deck(spec: dict, base: Path, out: Path, seed: int | None = None, overrides: dict | None = None, avoid: list | None = None) -> dict:
    """Build one deck. Returns a report dict (ok, seed, style, palette, fingerprint, warnings, errors, size)."""
    spec = dict(spec)
    spec.update({k: v for k, v in (overrides or {}).items() if v})
    spec, warns, errs = dspec.normalize(spec, base)
    rep = {"ok": False, "warnings": warns, "errors": errs}
    if errs:
        return rep
    notes, merrs = dspec.resolve_media(spec, base)
    rep["warnings"] += notes
    if merrs:
        rep["errors"] = merrs
        return rep
    pf = (spec.get("design") or {}).get("palette_from")
    if isinstance(pf, str) and pf.strip().lower() not in ("saved", "prefs"):  # the user's own colours: path relative to the spec file
        pf = str((base / pf).resolve()) if not Path(pf).is_absolute() else pf
        spec = {**spec, "design": {**spec["design"], "palette_from": pf}}
    if pf:
        try:
            dstyle.design_core.load_user_palette(pf)
        except ValueError as exc:
            rep["errors"] = [f"design.palette_from: {exc}"]
            return rep
    if seed is None:
        seed = spec.get("seed")
    if seed is None and avoid is None:  # fresh look: steer away from the styles used in the last few builds
        try:
            avoid = json.loads(RECENT.read_text(encoding="utf-8"))[-3:]
        except Exception:
            avoid = []
    if seed is None:
        seed = random.randint(1, 99999)
    seed = int(seed)
    dz = dstyle.resolve(spec, seed, avoid)
    issues = dstyle.contrast_report(dz)
    if issues:
        own = dstyle.STYLES[dz["style"]]["pal"]
        spec2 = dict(spec)
        dz = dstyle.resolve({**spec2, "design": {**(spec.get("design") or {}), "style": dz["style"]}}, seed + 1000)
        issues = dstyle.contrast_report(dz)
    if issues:
        rep["errors"] = ["palette contrast: " + "; ".join(issues)]
        return rep
    prepare(spec, dz)
    picks = pick_layouts(dz, spec["slides"])
    builds_on = (spec.get("design") or {}).get("builds", True) is not False
    parts, css_extra, fp, types = [], [], [], set()
    for i, (it, (var, fam, fn)) in enumerate(zip(spec["slides"], picks)):
        ctx = Ctx(dz, i, builds_on and it.get("build", True) is not False or it["type"] == "quiz")
        res = fn(ctx, it)
        sid = f"s{i + 1}"
        fcss, fsvg, probs = dspec.flair(it, sid)
        rep["warnings"] += probs
        if fcss:
            css_extra.append(fcss)
        role = res.get("role", "content")
        solve = f' data-solve="{res["solve"]}"' if res.get("solve") else ""
        note = f' data-note="{esc(it["note"])}"' if it.get("note") else ""
        layout_id = f"{it['type']}.{var}"
        fp.append(layout_id)
        types.add(it["type"])
        parts.append(f'<section class="sl tr-{dz["lang"]["trans"]}" id="{sid}" data-type="{it["type"]}" data-layout="{layout_id}" data-family="{fam}"{solve}{note}>'
                     f'{art.background(dz, i, role)}{fsvg}{res["html"]}</section>')
    js = (ASSETS / "deck.js").read_text(encoding="utf-8")
    for tag, used in (("chart", "chart" in types), ("math", "math" in types), ("timer", "timer" in types)):
        js = re.sub(rf"/\*#{tag}\*/(.*?)/\*#end\*/", (lambda m: m.group(1)) if used else "", js, flags=re.S)
    css = (ASSETS / "deck.css").read_text(encoding="utf-8") + "\n" + style_css(dz) + "\n" + "\n".join(css_extra)
    scene = ('<div id="deck">' + "".join(parts) + '</div><div id="chrome"><div class="prog"></div><div class="pn"></div></div><div id="notes"></div><div id="black"></div>')
    import placeholders as ph_
    doc = {"title": spec.get("title") or spec["slides"][0].get("title", "슬라이드"), "skin": "deck",
           "deck": {"style": dz["style"], "palette": dz["palette"], "seed": seed, "purpose": dz["purpose"], "why": dz["why"], "layouts": fp,
                    "colors": {k: dz["colors"][k] for k in ("bg1", "tx", "pr")}, "floor": dz["floor"],
                    "fillins": [str(x) for x in ph_.with_blanks(spec.get("fillins"), spec.get("template_blanks"))]}}
    libs = ["lucide"] + (["chartjs"] if "chart" in types else []) + (["katex"] if "math" in types else [])
    size = build_stage.build(doc, js, out, css, libs, True, False, False, scene, True)
    html = out.read_text(encoding="utf-8")
    html = html.replace("</head>", f'<meta name="ts-deck" content="style={dz["style"]};seed={seed}">\n</head>', 1)
    out.write_text(html, encoding="utf-8")
    if (spec.get("seed") is None and seed is not None and avoid is not None) or True:
        try:
            hist = json.loads(RECENT.read_text(encoding="utf-8")) if RECENT.exists() else []
            RECENT.parent.mkdir(parents=True, exist_ok=True)
            RECENT.write_text(json.dumps((hist + [dz["style"]])[-6:]), encoding="utf-8")
        except Exception:
            pass
    rep.update(ok=True, seed=seed, style=dz["style"], palette=dz["palette"], fingerprint=fp, size=size, purpose=dz["purpose"], why=dz["why"], slides=len(parts))
    return rep


def placeholder_gate(spec: dict):
    """(leftover placeholders, listed fill-ins found) over every string in the spec (titles, items, notes ...)."""
    import placeholders as ph
    texts: list[str] = []

    def walk(v):
        if isinstance(v, str):
            texts.append(v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in ("fillins", "file", "url", "palette_from", "seed", "tex"):
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(spec.get("slides") or spec.get("items") or [])
    walk(spec.get("title") or "")
    fills = ph.with_blanks(spec.get("fillins"), spec.get("template_blanks"))
    left = [m for tx in texts for m in ph.leftovers(tx, fills)]
    return list(dict.fromkeys(left)), ph.fillin_list(texts, fills)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--purpose", default="")
    ap.add_argument("--mood", default="")
    ap.add_argument("--style", default="")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--pptx", nargs="?", const="auto", metavar="OUT.pptx", help="ALSO write an editable PowerPoint (.pptx) from the same spec (python-pptx, installed on first need)")
    ap.add_argument("--template", type=Path, help="with --pptx: the teacher's own .pptx/.potx - its masters and layouts are used (template-first)")
    ap.add_argument("--yes", action="store_true", help="the teacher agreed to install python-pptx")
    ap.add_argument("--yes-libreoffice", action="store_true", help="the teacher agreed to install LibreOffice (~350MB) so the .pptx can be drawn for real")
    ap.add_argument("--review", type=Path, help="also write the contact sheet + metrics into this folder")
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text(encoding="utf-8"))
    out = a.out or OUT_DIR / f"deck-{a.spec.stem}-{time.strftime('%m%d-%H%M%S')}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    ov: dict = {"purpose": a.purpose, "mood": a.mood}
    if a.style:
        ov["design"] = {**(spec.get("design") or {}), "style": a.style}
    rep = build_deck(spec, a.spec.resolve().parent, out, a.seed, ov)
    for w in rep["warnings"]:
        print("NOTE", w)
    if not rep["ok"]:
        for e in rep["errors"]:
            print("FIX ", e)
        print(f"\n고칠 곳 {len(rep['errors'])}개 - spec을 고친 뒤 다시 실행하세요.")
        return 1
    print(f"built {out} ({rep['size'] // 1024} KB) slides={rep['slides']} style={rep['style']} palette={rep['palette']} seed={rep['seed']} (같은 모양을 다시 만들려면 --seed {rep['seed']})")
    code = 0
    left, listed = placeholder_gate(spec)  # blanks must never ship: FAIL unless the spec lists them as "fillins"
    if left:
        code = 1
        print(f"FAIL placeholders left in the deck: {left[:10]}  -> 실제 값이나 그럴듯한 가정(오늘 날짜, 2026학년도, '우리 학교')으로 채우거나, spec의 \"fillins\"에 적어 마지막에 「바꿔 넣을 곳」으로 알리세요")
    if listed:
        print("바꿔 넣을 곳 (선생님께 마지막에 알려 주세요): " + ", ".join(listed))
        if spec.get("template_blanks") is True:
            print("NOTE 양식 모드: 빈칸을 일부러 남겼어요. 사용하기 전에 위 곳을 채워 주세요.")
    if not a.no_check:
        code = subprocess.run([sys.executable, str(HERE / "check_page.py"), str(out), "--no-play"]).returncode or code
    if a.review:
        code = subprocess.run([sys.executable, str(HERE / "slides_review.py"), str(out), "--out", str(a.review)]).returncode or code
    if a.pptx:
        px = out.with_suffix(".pptx") if a.pptx == "auto" else Path(a.pptx)
        import deck_pptx
        deck_pptx._need_pptx(a.yes)
        pr_ = deck_pptx.build_pptx(spec, a.spec.resolve().parent, px, rep["seed"], ov, a.template)  # same seed = same style and colours as the HTML
        if pr_["ok"]:
            print(f"built {px} (편집할 수 있는 PPT) slides={pr_['slides']}")
            print("NOTE", pr_["font_note"])
            print("NOTE PPT에서는 단계별 나타나기·타이머·수식·아이콘 그림이 단순해져요.")
            for w_ in pr_["warnings"]:
                if "줄여" in w_ or "넘쳐" in w_:
                    print("NOTE", w_)
            import pptx_check
            ck = pptx_check.check_pptx(px, __import__("placeholders").with_blanks(spec.get("fillins"), spec.get("template_blanks")))
            for lv, msg in ck["results"]:
                print(f"{lv:4} pptx: {msg}")
                if lv == "FAIL":
                    code = code or 1
            if a.review:  # look at it: real LibreOffice drawing when installed, else an APPROXIMATE preview (labelled)
                import pptx_render
                rr = pptx_render.render(px, a.review, consent=a.yes_libreoffice, overflow=ck["overflow"])
                print(("PASS " if rr["mode"] == "libreoffice" else "NOTE ") + "pptx 그림: " + rr["note"])
                print("sheet:", (rr["files"] or ["-"])[0])
            print(f"READY {px}")
        else:
            code = code or 1
            print("FIX pptx:", "; ".join(pr_["errors"]))
    print(f"READY {out}")
    return code


if __name__ == "__main__":
    sys.exit(main())
