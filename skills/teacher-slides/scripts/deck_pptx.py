#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Deck spec -> editable PowerPoint (.pptx). Same spec, same style/palette as the HTML deck (`deck.py --pptx` calls this).

    py deck_pptx.py --spec deck.json --out deck.pptx [--seed N] [--template my.pptx|my.potx] [--yes]

What becomes what (everything stays editable in PowerPoint):
  text -> real text boxes / the slide's title placeholder; cards -> rounded rectangles; chart -> native PowerPoint chart;
  compare rows -> native table; QR -> small squares; presenter note -> speaker notes (quiz answers go there too).
  Not possible natively: animations/builds, countdown timer, math typesetting (shown as plain text), icon illustrations (a calm shape instead).
Template-first: with --template the file's own slide master/layouts are used (title + body placeholders filled, nothing left empty);
  colours of cards/charts still come from our palette unless the spec has design.palette_from.
python-pptx is installed on first need through shared/tools/ensure.py (asks consent; --yes = the teacher agreed).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
for _p in (SKILL / "shared" / "tools", SKILL.parent.parent / "shared" / "tools"):
    if _p.exists():
        sys.path.insert(0, str(_p))
        break
sys.path.insert(0, str(HERE))
import deck_context as dctx  # noqa: E402
import deck_spec as dspec  # noqa: E402
import deck_style as dstyle  # noqa: E402
import pptx_fit as pfit  # noqa: E402
from deck_kit import plain  # noqa: E402

SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
SUP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")


def tex_plain(t: str) -> str:
    """Small LaTeX -> readable text (subscripts, arrows, \\text{}, \\frac). Good enough to edit by hand afterwards."""
    t = re.sub(r"\\xrightarrow\{\\text\{([^}]*)\}\}", r" →(\1) ", t)
    t = re.sub(r"\\xrightarrow\{([^}]*)\}", r" →(\1) ", t)
    t = re.sub(r"\\text\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", t)
    t = re.sub(r"\\sqrt\{([^}]*)\}", r"√(\1)", t)
    for a, b in (("\\rightarrow", "→"), ("\\to", "→"), ("\\times", "×"), ("\\cdot", "·"), ("\\div", "÷"), ("\\pm", "±"), ("\\le", "≤"), ("\\ge", "≥"),
                 ("\\neq", "≠"), ("\\approx", "≈"), ("\\pi", "π"), ("\\Delta", "Δ"), ("\\,", " "), ("\\ ", " "), ("\\left", ""), ("\\right", "")):
        t = t.replace(a, b)
    t = re.sub(r"_\{([^}]*)\}", lambda m: m.group(1).translate(SUB), t)
    t = re.sub(r"_(\w)", lambda m: m.group(1).translate(SUB), t)
    t = re.sub(r"\^\{([^}]*)\}", lambda m: m.group(1).translate(SUP), t)
    t = re.sub(r"\^(\w)", lambda m: m.group(1).translate(SUP), t)
    return re.sub(r"[{}\\]", "", t).strip()


def _need_pptx(consent: bool):
    try:
        import ensure
    except ImportError:
        ensure = None
    if ensure:
        res = ensure.ensure("python-pptx", consent=consent)
        if not res["ok"]:
            raise SystemExit("ASK TEACHER: " + res["prompt"] + "  (agree -> rerun with --yes)")
    import pptx  # noqa: F401


def build_pptx(spec: dict, base: Path, out: Path, seed: int | None = None, overrides: dict | None = None, template: Path | None = None) -> dict:
    """Build the .pptx. Returns {ok, slides, errors, warnings, style, seed, template}."""
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    spec = dict(spec)
    spec.update({k: v for k, v in (overrides or {}).items() if v})
    spec = dctx.pre(spec)
    spec, warns, errs = dspec.normalize(spec, base)
    rep = {"ok": False, "warnings": warns, "errors": errs}
    if errs:
        return rep
    spec = dctx.post(spec)
    cerrs, cwarns = dctx.lint(spec)
    rep["warnings"] += cwarns
    if cerrs:
        rep["errors"] = cerrs
        return rep
    pf = (spec.get("design") or {}).get("palette_from")
    if isinstance(pf, str) and pf.strip().lower() not in ("saved", "prefs") and not Path(pf).is_absolute():
        spec = {**spec, "design": {**spec["design"], "palette_from": str((base / pf).resolve())}}
    seed = int(seed if seed is not None else (spec.get("seed") or 7))
    dz = dstyle.resolve(spec, seed)
    if dstyle.contrast_report(dz):
        dz = dstyle.resolve({**spec, "design": {**(spec.get("design") or {}), "style": dz["style"]}}, seed + 1000)
    C = dz["colors"]
    ctx_name = dz.get("context", "")
    from deck_ctx_layouts import source_line as ctx_source
    serif = dz["lang"]["font"] == "serif"
    fdisp, fbody = ("Noto Serif KR" if serif else "Noto Sans KR"), "Noto Sans KR"

    prs = Presentation(str(template)) if template else Presentation()
    if not template:
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    else:  # a template may already hold sample slides: drop them, keep masters/layouts
        ids = prs.slides._sldIdLst
        for sid in list(ids):
            prs.part.drop_rel(sid.rId)
            ids.remove(sid)
    W, H = prs.slide_width / 914400, prs.slide_height / 914400  # inches
    k = W / 13.333  # scale from the 13.333 x 7.5 design grid
    I = lambda v: Emu(int(round(v * k * 914400)))  # noqa: E731
    rgb = lambda h: RGBColor.from_string(h.lstrip("#").upper())  # noqa: E731

    def layout_for(kind: str):
        """Template layouts: title-ish layout for title/closing/section, 'title only' else (placeholders by type, never by name)."""
        ls = list(prs.slide_layouts)
        def has(l, t):
            return any(p.placeholder_format.type is not None and int(p.placeholder_format.type) in t for p in l.placeholders)
        TITLE, CTR, BODY = (1, 3), (3,), (2, 7)  # TITLE, CENTER_TITLE | BODY, OBJECT
        if template:
            if kind == "cover":
                for l in ls:
                    if has(l, CTR):
                        return l
            for l in ls:  # title + nothing else (best for our own shapes)
                tl = [p for p in l.placeholders if int(p.placeholder_format.type) in (1, 3)]
                other = [p for p in l.placeholders if int(p.placeholder_format.type) not in (1, 3, 13, 15, 16)]
                if tl and not other:
                    return l
            for l in ls:
                if has(l, TITLE):
                    return l
            return ls[0]
        return ls[5] if len(ls) > 5 else ls[0]

    fit_log: list[dict] = []
    cur = [0]

    def set_font(run, size, color=None, bold=False, name=None, italic=False):
        f = run.font
        f.size = Pt(size)
        f.bold = bold
        f.italic = italic
        if not template or name == "fixed":
            f.name = fdisp if name == "disp" else fbody
        if color and not (template and color == "THEME"):
            f.color.rgb = rgb(color)

    def fill_runs(p, text, size, color, emc, bold=False, name="body", themed=False):
        """**x** becomes an emphasised run (accent colour + bold)."""
        for j, part in enumerate(re.split(r"\*\*(.+?)\*\*", str(text).replace("\\n", "\n"))):
            if not part:
                continue
            r = p.add_run()
            r.text = part
            set_font(r, size, color if j % 2 == 0 else emc, bold or j % 2 == 1, name)

    def tbox(s, x, y, w, h, text, size, color, bold=False, align="l", anchor="t", name="body", emc=None, spacing=1.12, shape=None):
        tb = shape or s.shapes.add_textbox(I(x), I(y), I(w), I(h))
        tf = tb.text_frame
        tf.word_wrap = True
        # text fit: shrink (never below 60% / 12pt) so the text stays inside its box; what still does not fit is reported (split / shorten it)
        if shape is None or not template:
            bw, bh = (w * k - 0.16) * 72, (h * k - 0.08) * 72
        else:
            bw, bh = (tb.width / 914400 - 0.16) * 72, (tb.height / 914400 - 0.08) * 72
        plain_lines = [re.sub(r"\*\*", "", ln) for ln in str(text).replace("\\n", "\n").split("\n")]
        new_size, fits = pfit.fit_size(plain_lines, size, bw, bh, spacing)
        if new_size < size or not fits:
            fit_log.append({"slide": cur[0], "text": plain_lines[0][:24], "from": size, "to": new_size, "fits": fits})
            size = new_size
            if not fits:
                from pptx.enum.text import MSO_AUTO_SIZE
                tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        tf.margin_left = tf.margin_right = I(0.08)
        tf.margin_top = tf.margin_bottom = I(0.04)
        lines = str(text).replace("\\n", "\n").split("\n")
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            p.line_spacing = spacing
            fill_runs(p, ln, size, color, emc or C["emc"], bold, name)
        return tb

    def rect(s, x, y, w, h, fill, line=None, round_=True, shape=None, lw=1.5):
        sh = s.shapes.add_shape(shape or (MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE), I(x), I(y), I(w), I(h))
        if round_ and shape is None:
            sh.adjustments[0] = min(0.5, dz["lang"]["rad"] / 100.0 * 0.9 / max(0.2, h / 2) * 0.5) if dz["lang"]["rad"] else 0.02
        if fill:
            sh.fill.solid()
            sh.fill.fore_color.rgb = rgb(fill)
        else:
            sh.fill.background()
        if line:
            sh.line.color.rgb = rgb(line)
            sh.line.width = Pt(lw)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def put_title(s, text, x=0.8, y=0.55, w=11.7, h=1.15, size=36, color=None, align="l", anchor="m"):
        """The slide's real title placeholder (outline view / accessibility), restyled to our design."""
        ph = s.shapes.title
        if ph is None:
            return tbox(s, x, y, w, h, text, size, color or C["tx"], True, align, anchor, "disp")
        if not template:
            ph.left, ph.top, ph.width, ph.height = I(x), I(y), I(w), I(h)
        ph.text_frame.clear()
        tbox(s, x, y, w, h, text, size, color or C["tx"], True, align, anchor, "disp", shape=ph)
        return ph

    def kicker(s, text, y=0.38):
        if text:
            tbox(s, 0.8, y, 11.7, 0.4, str(text).upper(), 14, C["emc"], True)

    def drop_empty(s):
        for ph in list(s.placeholders):
            if ph.has_text_frame and not ph.text_frame.text.strip():
                ph._element.getparent().remove(ph._element)

    def bg(s, kind="content"):
        f = s.background.fill
        f.solid()
        f.fore_color.rgb = rgb(C["bg1"])
        if kind in ("title", "closing", "section"):
            c = rect(s, W / k - 4.2, -1.6, 6.2, 6.2, C["bg2"], round_=False, shape=MSO_SHAPE.OVAL)
            c.name = "decor"
        rect(s, 0, 7.5 - 0.14, 13.333, 0.14, C["pr"], round_=False).name = "decor"

    def qr_shapes(s, url, x, y, size):
        import deck_qr
        qrcodegen = sys.modules["qrcodegen"]
        t = url if url.lower().startswith(("http://", "https://", "mailto:", "tel:")) else "https://" + url
        q = qrcodegen.QrCode.encode_text(t, qrcodegen.QrCode.Ecc.MEDIUM)
        n = q.get_size()
        cell = size / (n + 8)
        rect(s, x, y, size, size, "#ffffff", round_=False).name = "QR"
        for yy in range(n):
            xx = 0
            while xx < n:
                if q.get_module(xx, yy):
                    x0 = xx
                    while xx < n and q.get_module(xx, yy):
                        xx += 1
                    rect(s, x + (x0 + 4) * cell, y + (yy + 4) * cell, (xx - x0) * cell, cell, "#111111", round_=False).name = "QR"
                else:
                    xx += 1

    def card(s, x, y, w, h, fill=None):
        c = rect(s, x, y, w, h, fill or C["card"], line=C["line"] if dz["lang"]["card"] in ("hair", "chalk", "glass") else None)
        return c

    slides = spec["slides"]
    n_sec = 0
    for idx, it in enumerate(slides):
        t = it["type"]
        cur[0] = idx + 1
        s = prs.slides.add_slide(layout_for("cover" if t in ("title", "closing") else "other"))
        bg(s, t)
        kicker(s, it.get("kicker"))
        notes = [it.get("note", "")] if it.get("note") else []
        pub = ctx_name == "public"
        if pub and t not in ("title", "section", "closing"):  # public header: section name left, 기관 right, thin rule
            sec, org = str(it.get("_section") or ""), str(spec.get("org") or spec.get("agency") or "")
            if sec:
                tbox(s, 0.8, 0.12, 7.5, 0.36, sec, 12, C["mu"], True)
            if org:
                tbox(s, 7.5, 0.12, 5.0, 0.36, org, 12, C["mu"], True, "r")
            rect(s, 0.8, 0.5, 11.7, 0.02, C["line"], round_=False).name = "rule"
        src = ctx_source(it)
        if src:  # 자료/주 line on data slides
            tbox(s, 0.8, 6.85, 11.7, 0.4, src, 12, C["mu"])
        if t == "title" and pub:
            rect(s, 0, 0, 13.333, 0.2, C["pr"], round_=False).name = "decor"
            if it.get("_org"):
                tbox(s, 0.8, 1.0, 11.7, 0.5, it["_org"], 20, C["mu"], True, "c")
            rect(s, 3.9, 1.7, 5.5, 0.03, C["pr"], round_=False).name = "rule"
            put_title(s, plain(it["title"]), 1.2, 2.0, 10.9, 2.2, 40, align="c", anchor="m")
            if it.get("subtitle"):
                tbox(s, 1.2, 4.25, 10.9, 0.6, it["subtitle"], 20, C["mu"], align="c")
            rect(s, 3.9, 5.0, 5.5, 0.03, C["pr"], round_=False).name = "rule"
            if it.get("_date"):
                tbox(s, 0.8, 5.35, 11.7, 0.5, it["_date"], 20, C["tx"], align="c")
            if it.get("_dept"):
                tbox(s, 0.8, 5.9, 11.7, 0.5, it["_dept"], 18, C["mu"], align="c")
        elif t == "bullets" and pub:
            put_title(s, plain(it["title"]), 0.8, 0.65, 11.7, 0.85, 28)
            rect(s, 0.8, 1.55, 11.7, 0.03, C["pr"], round_=False).name = "rule"
            cnt = {1: 0, 2: 0, 3: 0}
            lines = []
            for x_ in it["items"]:
                lv, tx_ = dctx.item_level(x_)
                m = dctx.marker(lv, cnt[lv], str(it.get("marks", "box")))
                cnt[lv] += 1
                for dd in range(lv + 1, 4):
                    cnt[dd] = 0
                lines.append(("    " * (lv - 1)) + m + " " + plain(tx_))
            tbox(s, 0.9, 1.8, 11.5, 4.9, "\n".join(lines), 20, C["tx"], spacing=1.35)
        elif t == "table":
            put_title(s, plain(it["title"]), 0.8, 0.65 if pub else 0.45, 11.7, 0.85, 28 if pub else 34)
            cols, rows = it["columns"], it["rows"]
            if it.get("unit"):
                tbox(s, 8.5, 1.5, 4.0, 0.35, f"(단위: {it['unit']})", 12, C["mu"], align="r")
            gt = s.shapes.add_table(len(rows) + 1, len(cols), I(0.8), I(1.9), I(11.7), I(min(4.8, 0.62 * (len(rows) + 1))))
            tb = gt.table
            hi = it.get("highlight")
            for r in range(len(rows) + 1):
                for c_ in range(len(cols)):
                    cell = tb.cell(r, c_)
                    txt = plain(str(cols[c_] if r == 0 else rows[r - 1][c_]))
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(C["pr"] if r == 0 else ("#ffffff" if r % 2 else C["bg2"]))
                    tf = cell.text_frame
                    tf.paragraphs[0].text = ""
                    num_ = bool(re.match(r"^[\s+\-]?[\d,.]+\s*\S{0,2}$", txt))
                    tf.paragraphs[0].alignment = PP_ALIGN.CENTER if r == 0 else (PP_ALIGN.RIGHT if num_ else PP_ALIGN.LEFT)
                    fill_runs(tf.paragraphs[0], txt, 16, C["bt"] if r == 0 else (C["emc"] if hi == c_ else C["tx"]), C["emc"], bold=(r == 0 or hi == c_))
                    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        elif t == "summary":
            put_title(s, plain(it.get("title") or "요약"), 0.8, 0.65 if pub else 0.45, 11.7, 0.85, 28 if pub else 34)
            y0 = 1.8
            if it.get("text"):
                tbox(s, 0.8, y0, 11.7, 0.6, it["text"], 20, C["tx"], True)
                y0 += 0.8
            rect(s, 0.8, y0 + 0.2, 11.7, 6.6 - y0 - 0.2, None, line=C["pr"], round_=False, lw=2.5)
            lab = rect(s, 1.1, y0, 1.4, 0.42, C["pr"], round_=False)
            tbox(s, 1.1, y0, 1.4, 0.42, it.get("label") or "핵심", 16, C["bt"], True, "c", "m", shape=lab)
            tbox(s, 1.2, y0 + 0.75, 10.9, 6.3 - y0 - 0.9, "\n".join("□ " + plain(x_) for x_ in it["points"]), 22, C["tx"], spacing=1.4)
        elif t == "toc":
            put_title(s, plain(it.get("title") or "목차"), 0.8, 0.6, 5, 1.0, 40)
            rect(s, 0.8, 1.7, 0.7, 0.07, C["pr"], round_=False).name = "accent"
            its = it.get("items") or []
            rh = min(0.8, 4.6 / max(len(its), 1))
            for i_, x_ in enumerate(its):
                y = 2.0 + i_ * rh
                lab = f"{dctx.roman(i_ + 1)}." if pub else f"{i_ + 1:02d}"
                tbox(s, 4.6, y, 1.0, rh, lab, 24, C["emc"], True, anchor="m", name="disp")
                tbox(s, 5.6, y, 6.9, rh, re.sub(r"^\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.\s*", "", plain(str(x_))), 24, C["tx"], anchor="m")
                rect(s, 4.6, y + rh - 0.02, 7.9, 0.015, C["line"], round_=False).name = "rule"
        elif t == "hero":
            if it.get("file"):
                p_ = Path(it["file"])
                p_ = p_ if p_.is_absolute() else base / p_
                pic = s.shapes.add_picture(str(p_), 0, 0, prs.slide_width, prs.slide_height)
                pic.name = "image"
                pic._element.nvPicPr.cNvPr.set("descr", plain(it.get("headline", "")))
                sc_ = rect(s, 0, 3.4, 13.333, 4.1, "#000000", round_=False)
                sc_.name = "scrim"
                from pptx.oxml.ns import qn
                sf = sc_.fill._xPr.find(qn("a:solidFill"))
                if sf is not None and len(sf):
                    sf[0].append(sf[0].makeelement(qn("a:alpha"), {"val": "55000"}))
                hc, mc = "#ffffff", "#f2f2f2"
            else:
                rect(s, 8.6, 0, 4.733, 7.5, C["pr"], round_=False).name = "decor"
                hc, mc = C["tx"], C["mu"]
            if it.get("kicker"):
                tbox(s, 0.8, 3.6, 7.6, 0.4, it["kicker"], 16, mc, True)
            put_title(s, plain(it["headline"]), 0.8, 4.0, 7.6 if not it.get("file") else 9.0, 1.6, 54, hc)
            if it.get("sub"):
                tbox(s, 0.8, 5.65, 9.0, 0.6, it["sub"], 20, mc)
            if it.get("cta"):
                b_ = rect(s, 0.8, 6.4, 3.2, 0.7, C["pr"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
                tbox(s, 0.8, 6.4, 3.2, 0.7, it["cta"], 20, C["bt"], True, "c", "m", shape=b_)
            if it.get("url"):
                qr_shapes(s, it["url"], 10.2, 4.1, 2.4)
        elif t == "title":
            rect(s, 0.8, 2.0, 0.18, 2.3, C["pr"], round_=False).name = "accent"
            put_title(s, plain(it["title"]).replace("\n", "\n"), 1.25, 1.8, 10.5, 2.6, 54, align="l", anchor="m")
            if it.get("subtitle"):
                tbox(s, 1.25, 4.6, 10.5, 0.7, it["subtitle"], 24, C["mu"], name="body")
            if it.get("meta"):
                tbox(s, 1.25, 5.5, 10.5, 0.5, it["meta"], 16, C["mu"])
        elif t == "section":
            n_sec += 1
            tbox(s, 0.8, 1.7, 4, 1.4, f"{n_sec:02d}", 80, C["emc"], True, name="disp")
            put_title(s, plain(it["title"]), 0.8, 3.2, 11.5, 1.5, 44)
            if it.get("sub"):
                tbox(s, 0.8, 4.8, 11.5, 0.7, it["sub"], 22, C["mu"])
        elif t == "statement":
            put_title(s, it["text"], 1.0, 1.5, 11.3, 3.4, 48, align="c")
            if it.get("sub"):
                tbox(s, 1.0, 5.1, 11.3, 0.8, it["sub"], 24, C["mu"], align="c")
        elif t == "bullets":
            put_title(s, plain(it["title"]))
            items = it["items"]
            n = len(items)
            gap = 0.18
            ch = min(1.1, (5.2 - gap * (n - 1)) / n)
            for i, x in enumerate(items):
                y = 1.95 + i * (ch + gap)
                card(s, 0.8, y, 11.7, ch)
                rect(s, 0.8, y, 0.14, ch, C["pr"], round_=False).name = "accent"
                tbox(s, 1.15, y, 11.2, ch, x, 22, C["ct"], anchor="m", emc=C["emcc"])
        elif t == "compare":
            put_title(s, plain(it["title"]))
            if it.get("rows"):
                rows = it["rows"]
                gt = s.shapes.add_table(len(rows) + 1, 3, I(0.8), I(1.95), I(11.7), I(0.7 * (len(rows) + 1)))
                tb = gt.table
                tb.columns[0].width, tb.columns[1].width, tb.columns[2].width = I(3.1), I(4.3), I(4.3)
                head = ["", it["a"].get("label", "A"), it["b"].get("label", "B")]
                for r in range(len(rows) + 1):
                    for c_ in range(3):
                        cell = tb.cell(r, c_)
                        txt = head[c_] if r == 0 else (rows[r - 1].get("k", "") if c_ == 0 else rows[r - 1].get("a" if c_ == 1 else "b", ""))
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = rgb(C["pr"] if r == 0 else (C["card"] if r % 2 else C["bg2"]))
                        tf = cell.text_frame
                        tf.paragraphs[0].text = ""
                        fill_runs(tf.paragraphs[0], plain(txt), 20, C["bt"] if r == 0 else C["ct"], C["emcc"], bold=(r == 0 or c_ == 0))
                        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            else:
                for j, side in enumerate(("a", "b")):
                    x = 0.8 + j * 6.0
                    card(s, x, 1.95, 5.7, 4.9)
                    hd = rect(s, x, 1.95, 5.7, 0.9, C["pr"] if j == 0 else C["ac"])
                    tbox(s, x, 1.95, 5.7, 0.9, it[side].get("label", side.upper()), 26, C["bt"], True, "c", "m", "disp", emc=C["bt"])
                    for i, x_ in enumerate(it[side].get("items", [])[:5]):
                        tbox(s, x + 0.3, 3.05 + i * 0.75, 5.1, 0.7, "• " + plain(x_), 20, C["ct"], emc=C["emcc"])
        elif t == "steps":
            put_title(s, plain(it["title"]))
            st = it["steps"]
            n = len(st)
            cw = 11.7 / n
            rect(s, 0.8 + cw / 2, 2.85, 11.7 - cw, 0.05, C["line"], round_=False).name = "line"
            for i, x_ in enumerate(st):
                cx = 0.8 + i * cw
                d = rect(s, cx + cw / 2 - 0.45, 2.45, 0.9, 0.9, C["pr"], shape=MSO_SHAPE.OVAL)
                tbox(s, cx + cw / 2 - 0.45, 2.45, 0.9, 0.9, str(i + 1), 28, C["bt"], True, "c", "m", "disp", emc=C["bt"], shape=d)
                tbox(s, cx + 0.1, 3.65, cw - 0.2, 0.8, x_.get("title", ""), 22, C["tx"], True, "c", name="disp")
                tbox(s, cx + 0.1, 4.45, cw - 0.2, 1.6, x_.get("text", ""), 17, C["mu"], align="c")
        elif t == "bignumber":
            if it.get("title"):
                put_title(s, plain(it["title"]))
            else:
                put_title(s, plain(it["value"]) + str(it.get("unit", "")), 0.8, 0.4, 11.7, 0.4, 12, C["bg1"])
            tbox(s, 0.8, 1.9, 11.7, 2.6, f"{plain(it['value'])}{it.get('unit', '')}", 120, C["emc"], True, "c", "m", "disp")
            if it.get("caption") or it.get("label"):
                tbox(s, 0.8, 4.7, 11.7, 1.0, it.get("caption") or it.get("label"), 28, C["tx"], align="c")
        elif t == "bignumbers":
            put_title(s, plain(it.get("title", "")) or "숫자로 보기")
            its = it["items"]
            n = len(its)
            cw = (11.7 - 0.3 * (n - 1)) / n
            for i, x_ in enumerate(its):
                x = 0.8 + i * (cw + 0.3)
                card(s, x, 2.0, cw, 4.3)
                tbox(s, x, 2.5, cw, 1.9, f"{plain(x_.get('value', ''))}{x_.get('unit', '')}", 72 if n == 2 else 60, C["emcc"], True, "c", "m", "disp")
                tbox(s, x + 0.2, 4.6, cw - 0.4, 1.3, x_.get("caption", x_.get("label", "")), 22, C["ct"], align="c")
        elif t == "quote":
            tbox(s, 1.0, 0.3, 2.5, 2.3, "“", 120, C["emc"], True, name="disp")
            put_title(s, it["text"], 1.3, 2.0, 10.7, 3.4, 44)
            if it.get("who"):
                tbox(s, 1.3, 5.6, 10.7, 0.6, "— " + it["who"], 20, C["mu"])
        elif t == "illustration":
            put_title(s, plain(it["title"]), 0.8, 0.55, 7.2, 1.6)
            if it.get("text"):
                tbox(s, 0.8, 2.5, 7.0, 3.2, it["text"], 26, C["mu"])
            rect(s, 8.7, 1.9, 3.8, 3.8, C["bg2"], shape=MSO_SHAPE.OVAL).name = "decor"
            rect(s, 9.4, 2.6, 2.4, 2.4, C["pr"], shape=MSO_SHAPE.OVAL).name = "decor"
            notes.append("(그림 자리: 웹 슬라이드의 아이콘 그림은 PPT에서는 도형으로 바꿨어요. 원하는 그림을 직접 넣어 보세요.)")
        elif t == "quiz":
            put_title(s, it["q"], 0.8, 1.0, 11.7, 1.8, 38)
            ch = it["choices"]
            cols = 2 if len(ch) > 3 else 1
            rows = (len(ch) + cols - 1) // cols
            bw = (11.7 - 0.3 * (cols - 1)) / cols
            bh = min(1.0, (3.9 - 0.2 * (rows - 1)) / rows)
            for i, x_ in enumerate(ch):
                x = 0.8 + (i % cols) * (bw + 0.3)
                y = 3.0 + (i // cols) * (bh + 0.2)
                b = card(s, x, y, bw, bh)
                tbox(s, x + 0.2, y, bw - 0.3, bh, f"{'ABCDE'[i]}.  {plain(x_)}", 24, C["ct"], anchor="m", emc=C["emcc"])
            ans = int(it.get("answer", 0))
            notes.append(f"정답: {'ABCDE'[ans]}. {plain(ch[ans])}" + (f" - {plain(it['explain'])}" if it.get("explain") else ""))
        elif t == "timeline":
            put_title(s, plain(it["title"]))
            ev = it["events"]
            n = len(ev)
            cw = 11.7 / n
            rect(s, 0.8 + cw / 2, 3.18, 11.7 - cw, 0.06, C["line"], round_=False).name = "line"
            for i, e in enumerate(ev):
                cx = 0.8 + i * cw
                tbox(s, cx, 2.3, cw, 0.6, e.get("when", ""), 22, C["emc"], True, "c", name="disp")
                rect(s, cx + cw / 2 - 0.16, 3.05, 0.32, 0.32, C["pr"], shape=MSO_SHAPE.OVAL)
                tbox(s, cx + 0.05, 3.7, cw - 0.1, 0.7, e.get("title", ""), 22, C["tx"], True, "c", name="disp")
                tbox(s, cx + 0.05, 4.4, cw - 0.1, 1.6, e.get("text", ""), 17, C["mu"], align="c")
        elif t == "chart":
            put_title(s, plain(it["title"]), h=1.0)
            cd = CategoryChartData()
            cd.categories = [plain(x) for x in it["labels"]]
            for se in it["series"]:
                cd.add_series(se.get("name", ""), se["data"])
            kind = it.get("kind", "bar")
            ct = {"bar": XL_CHART_TYPE.COLUMN_CLUSTERED, "line": XL_CHART_TYPE.LINE_MARKERS, "pie": XL_CHART_TYPE.PIE, "doughnut": XL_CHART_TYPE.DOUGHNUT}[kind]
            has_t = bool(it.get("takeaway"))
            gf = s.shapes.add_chart(ct, I(0.8), I(1.75), I(11.7), I(4.2 if has_t else 5.0), cd)
            ch = gf.chart
            ch.font.size = Pt(16)
            ch.font.color.rgb = rgb(C["tx"])
            ch.has_legend = kind in ("pie", "doughnut") or len(it["series"]) > 1
            if ch.has_legend:
                ch.legend.position = XL_LEGEND_POSITION.BOTTOM
                ch.legend.include_in_layout = False
            pal = [C["pr"], C["ac"], C["good"], C["bad"], C["mu"], C["emc"], C["line"], C["cb"]]
            plot = ch.plots[0]
            if kind in ("pie", "doughnut"):
                plot.has_data_labels = True
                plot.data_labels.font.size = Pt(16)
                for pi, pt in enumerate(plot.series[0].points):
                    pt.format.fill.solid()
                    pt.format.fill.fore_color.rgb = rgb(pal[pi % len(pal)])
            else:
                plot.has_data_labels = True
                plot.data_labels.font.size = Pt(16)
                plot.data_labels.font.color.rgb = rgb(C["tx"])
                for si, se in enumerate(plot.series):
                    if kind == "bar":
                        se.format.fill.solid()
                        se.format.fill.fore_color.rgb = rgb(pal[si % len(pal)])
                    else:
                        se.format.line.color.rgb = rgb(pal[si % len(pal)])
                        se.format.line.width = Pt(3.5)
                ch.value_axis.has_major_gridlines = True
                ch.value_axis.major_gridlines.format.line.color.rgb = rgb(C["line"])
                if it.get("unit"):
                    ch.value_axis.has_title = True
                    ch.value_axis.axis_title.text_frame.text = str(it["unit"])
                    ch.value_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
                    ch.value_axis.axis_title.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(C["mu"])
            if has_t:
                tbox(s, 0.8, 6.1, 11.7, 0.8, it["takeaway"], 24, C["tx"], align="c")
        elif t == "math":
            put_title(s, plain(it["title"]) if it.get("title") else "수식", h=1.0)
            card(s, 0.8, 2.0, 11.7, 2.2)
            tbox(s, 0.8, 2.0, 11.7, 2.2, tex_plain(it["tex"]), 40, C["ct"], True, "c", "m", "disp")
            if it.get("text"):
                tbox(s, 0.8, 4.6, 11.7, 1.6, it["text"], 24, C["mu"], align="c")
            notes.append("수식 원본(TeX): " + it["tex"] + "  (PPT에서는 읽기 쉬운 글자로 바꿨어요. 필요하면 [삽입 > 수식]으로 다시 쓰세요.)")
        elif t == "timer":
            put_title(s, plain(it.get("title", "")) or "활동 시간", h=1.2)
            tbox(s, 0.8, 2.3, 11.7, 3.0, f"{int(it.get('minutes', 5)):02d}:00", 150, C["emc"], True, "c", "m", "disp")
            tbox(s, 0.8, 5.5, 11.7, 0.6, f"{int(it.get('minutes', 5))}분", 24, C["mu"], align="c")
            notes.append("웹 슬라이드의 카운트다운은 PPT에서 움직이지 않아요. 시간은 교실 타이머를 쓰세요.")
        elif t == "qr":
            put_title(s, plain(it["title"]), 0.8, 0.55, 6.5, 1.8)
            if it.get("caption"):
                tbox(s, 0.8, 2.6, 6.5, 1.5, it["caption"], 24, C["mu"])
            tbox(s, 0.8, 4.4, 6.5, 0.6, it["url"], 18, C["emc"])
            qr_shapes(s, it["url"], 8.0, 1.6, 4.5)
        elif t == "image":
            if it.get("title"):
                put_title(s, plain(it["title"]), h=0.9)
            p = Path(it["file"])
            p = p if p.is_absolute() else base / p
            from PIL import Image
            iw, ih = Image.open(p).size
            top = 1.6 if it.get("title") else 0.5
            maxw, maxh = 11.7, 7.0 - top
            sc = min(maxw / iw, maxh / ih)
            w_, h_ = iw * sc, ih * sc
            pic = s.shapes.add_picture(str(p), I(0.8 + (maxw - w_) / 2), I(top + (maxh - h_) / 2), I(w_), I(h_))
            pic.name = "image"
            pic._element.nvPicPr.cNvPr.set("descr", plain(it.get("caption") or it.get("title") or p.stem))
            if it.get("caption"):
                tbox(s, 0.8, 6.85 - 0.1, 11.7, 0.4, it["caption"], 14, C["mu"], align="c")
        elif t == "video":
            put_title(s, plain(it.get("title", "")) or "영상", h=1.0)
            card(s, 2.5, 2.2, 8.3, 3.6)
            tbox(s, 2.5, 2.2, 8.3, 3.6, f"영상 파일: {Path(it['file']).name}\n[삽입 > 비디오]로 이 자리에 넣어 주세요", 24, C["ct"], align="c", anchor="m")
        elif t == "closing":
            put_title(s, plain(it["title"]), 0.8, 1.2, 7.4, 2.4, 52, anchor="m")
            if it.get("sub"):
                tbox(s, 0.8, 3.8, 7.4, 0.9, it["sub"], 24, C["mu"])
            for i, x_ in enumerate(it.get("next", [])[:4]):
                tbox(s, 0.8, 4.9 + i * 0.55, 7.4, 0.5, "→ " + plain(x_), 20, C["tx"])
            if it.get("url"):
                qr_shapes(s, it["url"], 8.9, 1.4, 3.6)
                tbox(s, 8.4, 5.1, 4.6, 0.9, it["url"], 12, C["mu"], align="c")
        if notes:
            s.notes_slide.notes_text_frame.text = "\n".join(plain(n) for n in notes if n)
        drop_empty(s)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.core_properties.title = str(spec.get("title") or slides[0].get("title", ""))
    prs.core_properties.author = ""
    prs.save(str(out))
    for f in fit_log:
        if f["fits"]:
            rep["warnings"].append(f"slide {f['slide']}: 글이 길어서 {f['from']:g}pt -> {f['to']:g}pt로 줄였어요 ('{f['text']}...')")
    rep["overflow"] = [f for f in fit_log if not f["fits"]]
    for f in rep["overflow"]:
        rep["warnings"].append(f"slide {f['slide']}: 줄여도 글이 상자를 넘쳐요 ('{f['text']}...') -> 글을 줄이거나 두 장으로 나누세요")
    rep.update(ok=True, slides=len(slides), fit=fit_log, style=dz["style"], seed=seed, template=str(template) if template else "",
               font_note=f"글꼴 {fdisp}/{fbody}이(가) PC에 없으면 PowerPoint가 비슷한 글꼴로 바꿔 보여요. 글꼴 파일은 shared/fonts에 있어요.")
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--purpose", default="")
    ap.add_argument("--mood", default="")
    ap.add_argument("--template", type=Path, help="the teacher's own .pptx/.potx: its masters and layouts are used")
    ap.add_argument("--yes", action="store_true", help="the teacher agreed to install python-pptx")
    a = ap.parse_args()
    _need_pptx(a.yes)
    spec = json.loads(a.spec.read_text(encoding="utf-8"))
    out = a.out or a.spec.with_suffix(".pptx")
    rep = build_pptx(spec, a.spec.resolve().parent, out, a.seed, {"purpose": a.purpose, "mood": a.mood}, a.template)
    for w in rep["warnings"]:
        print("NOTE", w)
    if not rep["ok"]:
        for e in rep["errors"]:
            print("FIX ", e)
        return 1
    print(f"built {out} slides={rep['slides']} style={rep['style']} seed={rep['seed']}")
    print("NOTE", rep["font_note"])
    print(f"READY {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
