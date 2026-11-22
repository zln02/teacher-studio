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
sys.path.insert(0, str((HERE.parent / "shared" / "design") if (HERE.parent / "shared" / "design").exists() else (HERE.parents[2] / "shared" / "design")))
import system as ds  # noqa: E402  (shared/design/system.py: type scale, tracking, motion, polish layer)
import build_stage  # noqa: E402
import deck_art as art  # noqa: E402
import deck_context as dctx  # noqa: E402
import deck_ctx_layouts as ctxlay  # noqa: E402
import deck_layouts as lay  # noqa: E402
import deck_spec as dspec  # noqa: E402
import deck_style as dstyle  # noqa: E402
from deck_kit import Ctx, esc  # noqa: E402
for _folder in (SKILL / "shared" / "tools", HERE.parents[2] / "shared" / "tools"):
    if (_folder / "example_likeness.py").is_file():
        sys.path.insert(0, str(_folder))
        break
try:
    import example_likeness  # noqa: E402
except ImportError:
    example_likeness = None
try:
    import workdir  # noqa: E402  (shared/tools: work folders that do not need %TEMP%, the no-browser probe)
except ImportError:
    workdir = None

ASSETS = SKILL / "assets" / "deck"
PURPOSE_ICON = {"학부모 설명회": "heart-handshake", "수업": "graduation-cap", "연수": "lightbulb", "발표": "megaphone", "동아리": "rocket", "개인": "sparkles"}
RECENT = Path.home() / "TeacherStudio" / ".recent-styles.json"
SEEDS = Path.home() / "TeacherStudio" / ".deck-seeds.json"  # spec file -> the seed of its last build (a rebuild keeps the look)


def kept_seed(spec_path: Path, title: str = ""):
    """The seed this spec file was last built with (same file, same deck title), or None. Fixing a FAIL must not change the look that was just reviewed."""
    try:
        e = json.loads(SEEDS.read_text(encoding="utf-8")).get(str(spec_path.resolve()))
        return (int(e["seed"]), list(e.get("avoid") or [])) if e and e.get("title", "") == title else None
    except Exception:
        return None


def keep_seed(spec_path: Path, seed: int, title: str = "", avoid=()) -> None:
    try:
        d = json.loads(SEEDS.read_text(encoding="utf-8")) if SEEDS.exists() else {}
        d.pop(str(spec_path.resolve()), None)
        d[str(spec_path.resolve())] = {"seed": int(seed), "title": title, "avoid": list(avoid or [])}
        SEEDS.parent.mkdir(parents=True, exist_ok=True)
        SEEDS.write_text(json.dumps(dict(list(d.items())[-60:]), ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
OUT_DIR = Path.home() / "TeacherStudio"


def hex_rgba(h: str, a: float) -> str:
    r, g, b = dstyle._rgb(h)
    return f"rgba({r},{g},{b},{a})"


# Card, title and emphasis treatments. All matte: ONE neutral falling shadow at most, never a coloured glow, never a translucent blur
# (shared/design/DESIGN-RULES.md). "glass" / "glow" / "stack3d" stay as accepted names and are drawn the new way.
CARD_CSS = {
    "round": ".cd{box-shadow:0 28px 56px -32px rgba(0,0,0,.3)}",
    "flat": ".cd{border:1.5px solid var(--line);box-shadow:none}",
    "soft": ".cd{border:1px solid var(--line);box-shadow:0 34px 60px -36px rgba(0,0,0,.6)}",
    "glass": ".cd{border:1px solid var(--line);box-shadow:0 34px 60px -36px rgba(0,0,0,.6)}",
    "hair": ".cd{background:transparent;border:1.5px solid var(--line)}",
    "sticker": ".cd{border:3px solid var(--tx);box-shadow:8px 8px 0 var(--tx)}.ch{border:3px solid var(--tx)}",
    "ticket": ".cd{border-left:12px solid var(--pr);border-radius:calc(var(--rad)*.5)}",
    "polaroid": ".cd{box-shadow:0 24px 48px -28px rgba(0,0,0,.4);border-radius:8px}",
    "pixel": ".cd{border:4px solid var(--tx);box-shadow:6px 6px 0 var(--tx);border-radius:0}.ch,.tbtn,.vbtn,.chl{border-radius:0}.disc,.dot,.dotb,.chip{border-radius:0}",
    "chalk": ".cd{background:transparent;border:3px dashed var(--line)}",
    "e": ".cd{background:var(--card);border:1.5px solid var(--line);box-shadow:none;border-radius:12px}",  # preset E: flat, hairline, no shadow
}
TITLE_CSS = {
    "rule": "", "glow": "", "stack3d": "", "chalk": "", "plain": "", "serif": "", "underline": "", "stamp": "",
    "pixel": ".h{letter-spacing:.02em}",
}
EM_CSS = {
    "color": "em{color:var(--emc)}",
    "marker": "em{background:linear-gradient(transparent 78%,var(--hl) 78%,var(--hl) 94%,transparent 94%);padding:0 .04em}",
    "underline": "em{box-shadow:inset 0 -0.1em 0 var(--pr)}",
}


def style_css(dz: dict) -> str:
    c, lang, f = dz["colors"], dz["lang"], dz["fonts"]
    serif = lang["font"] == "serif"
    fam = lambda n: (ds.STACK_SERIF if "Serif" in n else ds.STACK_SANS)  # the studio face first, then Noto, then system fonts
    v = (f":root{{--bg1:{c['bg1']};--bg2:{c['bg2']};--tx:{c['tx']};--mu:{c['mu']};--card:{c['card']};--ct:{c['ct']};--line:{c['line']};--pr:{c['pr']};--bt:{c['bt']};--ac:{c['ac']};"
         f"--emc:{c['emc']};--emcc:{c['emcc']};--hl:{c['hl']};--hlc:{c['hlc']};--glow:{hex_rgba(c['pr'], .55)};--good:{c['good']};--bad:{c['bad']};"
         f"--rad:{lang['rad']}px;--tw:{lang['tw']};--tls:{lang['ls']}em;--fd:{fam(f['display'])};--fb:{fam(f['body'])}}}")
    em = EM_CSS[lang["em"]] + (".ex em,.ch em{box-shadow:none}" if lang["em"] != "color" else "")
    extra = ".q,.lead{font-family:var(--fd)}" if serif else ""
    return "\n".join([v, CARD_CSS[lang["card"]], TITLE_CSS.get(lang["title"], ""), em, extra, f"body{{background:{c['bg1']}}}", ds.css_vars("stage"), ds.polish_css("deck")])


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
        allowed = (dz.get("allowed") or {}).get(it["type"])
        if allowed and not it.get("layout"):  # context recipe: only its layout set (e.g. public = 개조식 lists, table compare)
            opts = [o for o in opts if o[0] in allowed] or opts
        forced = str(it.get("layout", "")) or ("left" if it["type"] == "title" and it.get("shapes") and it.get("_ctx") != "public" else "")
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
    spec = dctx.pre(spec)  # context recipe: objectives / recap / toc / summary slides, gov date, no builds for public
    spec, warns, errs = dspec.normalize(spec, base)
    rep = {"ok": False, "warnings": warns, "errors": errs}
    if errs:
        return rep
    spec = dctx.post(spec)  # public numbering Ⅰ. / 1., toc items, cover fields
    cerrs, cwarns = dctx.lint(spec)
    rep["warnings"] += cwarns
    if cerrs:
        rep["errors"] = cerrs
        return rep
    spec = dspec.pics_inline(spec)  # a young room's word pictures stand in front of their words
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
    import deck_e  # preset E motion words, pen / pills, garnish (고명)
    gcss, gassign, gnotes, gerrs = deck_e.garnish_plan(spec, dz, base)
    rep["warnings"] += gnotes
    if gerrs:
        rep["errors"] = gerrs
        return rep
    picks = pick_layouts(dz, spec["slides"])
    builds_on = (spec.get("design") or {}).get("builds", True) is not False
    parts, css_extra, fp, types = [], [], [], set()
    for i, (it, (var, fam, fn)) in enumerate(zip(spec["slides"], picks)):
        ctx = Ctx(dz, i, builds_on and it.get("build", True) is not False or it["type"] == "quiz")
        res = fn(ctx, it)
        res["html"] = ctxlay.decorate(ctx, it, res, spec)
        res["html"], enotes = deck_e.dress(res["html"], it, dz, ctx.max_b, ctx.builds)
        rep["warnings"] += enotes
        sid = f"s{i + 1}"
        fcss, fsvg, probs = dspec.flair(it, sid)
        rep["warnings"] += probs
        if fcss:
            css_extra.append(fcss)
        role = res.get("role", "content")
        solve = f' data-solve="{res["solve"]}"' if res.get("solve") else ""
        note = f' data-note="{esc(it["note"])}"' if it.get("note") else ""
        layout_id = f"{it['type']}.{var}"
        if it["type"] == "panel":  # a panel's look is its mix of blocks: two panels with different blocks are different layouts
            layout_id = "panel." + "-".join(str(b.get("kind")) for b in it.get("blocks") or [])
        fp.append(layout_id)
        types.add(it["type"])
        if it["type"] == "panel" and any(b.get("kind") == "chart" for b in it.get("blocks") or []):
            types.add("chart")
        scene = f'<div class="e-scene {gassign[i]}" aria-hidden="true"></div>' if i in gassign else ""
        parts.append(f'<section class="sl tr-{dz["lang"]["trans"]}" id="{sid}" data-type="{it["type"]}" data-layout="{layout_id}" data-family="{fam}"{solve}{note}>'
                     f'{art.background(dz, i, role)}{scene}{fsvg}{res["html"]}</section>')
    js = (ASSETS / "deck.js").read_text(encoding="utf-8")
    for tag, used in (("chart", "chart" in types), ("math", "math" in types), ("timer", "timer" in types)):
        js = re.sub(rf"/\*#{tag}\*/(.*?)/\*#end\*/", (lambda m: m.group(1)) if used else "", js, flags=re.S)
    css = (ASSETS / "deck.css").read_text(encoding="utf-8") + "\n" + ctxlay.CSS + __import__("deck_panel").CSS + style_css(dz) + "\n" + "\n".join(css_extra)
    e_on = deck_e.uses_motion(spec, dz)
    if e_on or gassign:
        css += "\n" + deck_e.css(dz) + "\n" + gcss
    if e_on:
        js = deck_e.js() + "\n" + js
    scene = ('<div id="deck">' + "".join(parts) + '</div><div id="chrome"><div class="prog"></div><div class="pn"></div></div><div id="notes"></div><div id="black"></div>')
    import placeholders as ph_
    doc = {"title": spec.get("title") or spec["slides"][0].get("title", "슬라이드"), "skin": "deck",
           "deck": {"style": dz["style"], "palette": dz["palette"], "seed": seed, "purpose": dz["purpose"], "why": dz["why"], "layouts": fp, "context": dz.get("context", ""),
                    "colors": {k: dz["colors"][k] for k in ("bg1", "tx", "pr")}, "floor": dz["floor"],
                    "fillins": [str(x) for x in ph_.with_blanks(spec.get("fillins"), spec.get("template_blanks"))]}}
    libs = ["lucide"] + (["chartjs"] if "chart" in types else []) + (["katex"] if "math" in types else [])
    size = build_stage.build(doc, js, out, css, libs, True, False, False, scene, True)
    html = out.read_text(encoding="utf-8")
    html = html.replace("</head>", f'<meta name="ts-deck" content="style={dz["style"]};seed={seed}">\n</head>', 1)
    if deck_e.active(dz):
        html = html.replace("<body>", '<body class="e-motion">', 1)
    out.write_text(html, encoding="utf-8")
    if (spec.get("seed") is None and seed is not None and avoid is not None) or True:
        try:
            hist = json.loads(RECENT.read_text(encoding="utf-8")) if RECENT.exists() else []
            RECENT.parent.mkdir(parents=True, exist_ok=True)
            RECENT.write_text(json.dumps((hist + [dz["style"]])[-6:]), encoding="utf-8")
        except Exception:
            pass
    rep.update(ok=True, garnish=sorted(set(gassign.values())), seed=seed, avoid=list(avoid or []), style=dz["style"], palette=dz["palette"], fingerprint=fp, size=size, purpose=dz["purpose"], why=dz["why"], slides=len(parts),
               context=dz.get("context", ""))
    return rep


def example_note(spec: dict) -> bool:
    """CONTENT-RULES 「Unknowns」: a deck with example values ("fillins") says so ONCE, in the first slide's speaker notes. Added here
    unless the spec already says it somewhere (a footnote under the first data table), the user wants blanks, it is a lesson deck
    (its content is simply filled and correct) or "example_note" is false. Returns True when the line was added."""
    import placeholders as ph
    fills = [x for x in (spec.get("fillins") or []) if str(x).strip()]
    slides = spec.get("slides") or []
    if (not fills or not slides or spec.get("template_blanks") is True or spec.get("example_note") is False
            or dctx.context_of(spec) == "class"):
        return False
    if ph.example_notes(dctx._strings(slides, skip=("file", "url", "tex", "fillins"))):
        return False
    first = slides[0]
    if not isinstance(first, dict):
        return False
    v = spec.get("example_note")
    line = v.strip() if isinstance(v, str) and v.strip() else ph.EXAMPLE_NOTE_DECK
    first["note"] = (str(first.get("note") or "").rstrip() + "\n" + line).strip()
    return True


def placeholder_gate(spec: dict):
    """(leftover placeholders, listed fill-ins found) over every string in the spec (titles, items, notes ...)."""
    import placeholders as ph
    texts: list[str] = []

    def walk(v):
        if isinstance(v, str):
            texts.append(v.replace(ph.EXAMPLE_NOTE_DECK, ""))  # our own one-line example note (speaker notes) is not a leftover blank
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in ("fillins", "file", "url", "palette_from", "seed", "tex", "garnish"):
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
    ap.add_argument("--fresh", action="store_true", help="pick a new look even though this spec file was built before (default: a rebuild keeps the look)")
    ap.add_argument("--purpose", default="")
    ap.add_argument("--mood", default="")
    ap.add_argument("--style", default="")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--pptx", nargs="?", const="auto", metavar="OUT.pptx", help="ALSO write an editable PowerPoint (.pptx) from the same spec (python-pptx, installed on first need)")
    ap.add_argument("--pptx-only", action="store_true", help="the user asked only for a PowerPoint file: skip the web-deck checks and screenshots (faster), keep the .pptx gate and preview")
    ap.add_argument("--template", type=Path, help="with --pptx: the teacher's own .pptx/.potx - its masters and layouts are used (template-first)")
    ap.add_argument("--yes", action="store_true", help="the teacher agreed to install python-pptx")
    ap.add_argument("--yes-libreoffice", action="store_true", help="the teacher agreed to install LibreOffice (~350MB) so the .pptx can be drawn for real")
    ap.add_argument("--review", type=Path, help="also write the contact sheet + metrics into this folder")
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text(encoding="utf-8"))
    only = bool(a.pptx_only and a.pptx)
    scratch = None
    if only and not a.out:  # PowerPoint only: the web page is just a by-product (kept out of the user's folder)
        if a.pptx == "auto":
            a.pptx = str(a.spec.with_suffix(".pptx"))
        # an ordinary folder beside the .pptx (never tempfile.mkdtemp: an agent's security box cannot write into those), removed at the end
        scratch = workdir.make("deck", near=Path(a.pptx)) if workdir else Path(a.pptx).resolve().parent / f".deck-work-{time.strftime('%H%M%S')}"
        scratch.mkdir(parents=True, exist_ok=True)
        a.out = scratch / "deck.html"
    if workdir:
        workdir.guard_browser()  # no browser in this environment: say it once, skip the screen checks without waiting
    try:
        return _run(a, spec, only)
    finally:
        if only and scratch is not None:
            (workdir.cleanup(scratch) if workdir else __import__("shutil").rmtree(scratch, ignore_errors=True))


def _run(a, spec, only) -> int:
    out = a.out or OUT_DIR / f"deck-{a.spec.stem}-{time.strftime('%m%d-%H%M%S')}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    ov: dict = {"purpose": a.purpose, "mood": a.mood}
    if a.style:
        ov["design"] = {**(spec.get("design") or {}), "style": a.style}
    title_ = str(spec.get("title") or "")
    avoid_ = None
    if a.seed is None and spec.get("seed") is None and not a.fresh and not a.style:
        kept = kept_seed(a.spec, title_)  # same spec file, built again (a fix round): the look that was reviewed stays
        if kept:
            a.seed, avoid_ = kept
            print(f"NOTE 같은 모양으로 다시 만들어요 (seed {a.seed}). 다른 모양을 원하면 --fresh")
    if example_note(spec):
        print("NOTE 예시 값 안내 한 줄을 첫 장 발표자 메모에 넣었어요 (슬라이드에는 따로 적지 않아요)")
    rep = build_deck(spec, a.spec.resolve().parent, out, a.seed, ov, avoid=avoid_)
    if rep.get("seed") is not None:
        keep_seed(a.spec, rep["seed"], title_, rep.get("avoid"))
    for w in rep["warnings"]:
        print("WARN" if w.startswith("장수:") else "NOTE", w)  # a missed page count is a WARN the author fixes before reporting
    if not rep["ok"]:
        for e in rep["errors"]:
            print("FIX ", e)
        print(f"\n고칠 곳 {len(rep['errors'])}개 - spec을 고친 뒤 다시 실행하세요.")
        return 1
    print(f"built {out} ({rep['size'] // 1024} KB) slides={rep['slides']} style={rep['style']} palette={rep['palette']} context={rep.get('context') or '-'} seed={rep['seed']} (같은 모양을 다시 만들려면 --seed {rep['seed']})")
    code = 0
    if example_likeness and example_likeness.is_fixture(spec, [SKILL / "assets" / "spec-examples"]):  # a shipped fixture built as itself: the page says so
        out.write_text(out.read_text(encoding="utf-8").replace("<head>", '<head><meta name="ts-fixture" content="1">', 1), encoding="utf-8")
    if spec.get("template_blanks") is True:  # the user asked for blanks to fill in: the page checker reports them, it does not fail them
        out.write_text(out.read_text(encoding="utf-8").replace("<head>", '<head><meta name="ts-template-blanks" content="1">', 1), encoding="utf-8")
    if example_likeness:  # same slide sequence + the example's headings (copied sentences are caught by the page checker)
        for lv, msg in example_likeness.check_spec(spec, [SKILL / "assets" / "spec-examples"], skeleton_only=True):
            if lv == "WARN":
                print(lv, msg)
    left, listed = placeholder_gate(spec)  # blanks must never ship: FAIL unless the spec lists them as "fillins"
    if left:
        code = 1
        print(f"FAIL placeholders left in the deck: {left[:10]}  -> 실제 값이나 그럴듯한 가정(오늘 날짜, 2026학년도, '우리 학교')으로 채우거나, spec의 \"fillins\"에 적어 마지막에 「바꿔 넣을 곳」으로 알리세요")
    ph_ = __import__("placeholders")  # the unknowns rule on what the audience sees (speaker notes are read separately)
    for lv_, msg_ in ph_.policy_checks(list(dctx._strings(spec.get("slides") or [])), [str(x.get("note") or "") for x in spec.get("slides") or [] if isinstance(x, dict)],
                                       ph_.with_blanks(spec.get("fillins"), spec.get("template_blanks")), deck=True, lesson=dctx.context_of(spec) == "class"):
        if lv_ != "PASS":
            print(f"{lv_:4} {msg_}")
            code = code or (1 if lv_ == "FAIL" else 0)
    ex_ = [str(x) for x in (spec.get("fillins") or []) if str(x).strip() and str(x) not in listed]
    if ex_ and spec.get("template_blanks") is not True:  # the unknowns rule: every example value is named in the last message
        print("바꿔 넣을 곳 (예시로 채운 값: 마지막 안내에 하나도 빠짐없이 적어 주세요): " + " · ".join(ex_))
    if listed:
        print("바꿔 넣을 곳 (선생님께 마지막에 알려 주세요): " + ", ".join(listed))
        if spec.get("template_blanks") is True:
            print("NOTE 양식 모드: 빈칸을 일부러 남겼어요. 사용하기 전에 위 곳을 채워 주세요.")
    if not a.no_check and not only:
        # the page is opened once in a headless browser (a few seconds): without it the result is PARTIAL, never PASS
        code = subprocess.run([sys.executable, str(HERE / "check_page.py"), str(out)]).returncode or code
    if a.review and not only:
        code = subprocess.run([sys.executable, str(HERE / "slides_review.py"), str(out), "--out", str(a.review), "--fix-small"]).returncode or code
    if a.pptx:
        px = out.with_suffix(".pptx") if a.pptx == "auto" else Path(a.pptx)
        import deck_pptx
        deck_pptx._need_pptx(a.yes)
        pr_ = deck_pptx.build_pptx(spec, a.spec.resolve().parent, px, rep["seed"], ov, a.template, avoid=rep.get("avoid"))  # same seed + same steering = the style and colours of the HTML
        if pr_["ok"]:
            print(f"built {px} (편집할 수 있는 PPT) slides={pr_['slides']}")
            print("NOTE", pr_["font_note"])
            print("NOTE PPT에서는 단계별 나타나기·타이머·수식·아이콘 그림이 단순해져요.")
            for w_ in pr_["warnings"]:
                if "줄여" in w_ or "넘쳐" in w_:
                    print("NOTE", w_)
            if pr_.get("audience") == "young" and not a.template:  # 유치원-초3: the words are read from the back row
                sm_ = deck_pptx.small_text(px)
                if sm_:
                    print("WARN pptx: 저학년 글씨: slide " + ", ".join(str(n_) for n_, _ in sm_) + "에 22pt보다 작은 글이 많아요 (저학년은 24pt 넘게) -> 그 장의 말을 줄이거나"
                          " (한 칸에 한 줄, 낱말 위주), 칸 수를 줄이거나, 내용을 한 장 더 나눠 크게 (그림의 이름표·옆 칸 설명도 포함)")
            import pptx_check
            ck = pptx_check.check_pptx(px, __import__("placeholders").with_blanks(spec.get("fillins"), spec.get("template_blanks")),
                                       lesson=dctx.context_of(spec) == "class")
            for lv, msg in ck["results"]:
                print(f"{lv:4} pptx: {msg}")
                if lv == "FAIL":
                    code = code or 1
            if a.review:  # look at it: real LibreOffice drawing when installed, else an APPROXIMATE preview (labelled)
                import pptx_render
                rr = pptx_render.render(px, a.review, consent=a.yes_libreoffice, overflow=ck["overflow"])
                print(("PASS " if rr["mode"] == "libreoffice" else "NOTE ") + "pptx 그림: " + rr["note"])
                print("sheet:", (rr["files"] or ["-"])[0])
            if any(lv == "FAIL" for lv, _ in ck["results"]):  # hard gate: a failing .pptx is never "ready"
                print(f"NOT DONE {px}: 위 pptx FAIL을 spec에서 고치고 같은 명령을 다시 실행하세요 (PASS가 될 때까지 완료 보고 금지). "
                      "빈칸은 「우리 학교」·오늘 날짜 같은 그럴듯한 값으로 채우고, 비어 보이는 장은 내용을 더 넣거나 옆 장과 합치세요.")
            else:
                print(f"READY {px}")
        else:
            code = code or 1
            print("FIX pptx:", "; ".join(pr_["errors"]))
    if only:
        return code
    if code == 2:  # nothing failed, but a check could not run (no browser on this computer): say so, do not send the author hunting for a FAIL
        print(f"PARTIAL {out}: 실패한 점검은 없지만 위 SKIP 줄의 점검을 하지 못했어요 (어떤 점검이 빠졌는지 함께 알려 주세요)")
        return code
    print(f"READY {out}" if not code else f"NOT DONE {out}: 위 FAIL을 고치고 다시 실행하세요 (PASS가 될 때까지 완료 보고 금지)")
    return code


if __name__ == "__main__":
    sys.exit(main())
