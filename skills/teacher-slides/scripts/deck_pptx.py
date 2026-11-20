#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Deck spec -> editable PowerPoint (.pptx). Same spec, same style/palette as the HTML deck (`deck.py --pptx` calls this).

    py deck_pptx.py --spec deck.json --out deck.pptx [--seed N] [--template my.pptx|my.potx] [--yes]

What becomes what (everything stays editable in PowerPoint):
  text -> real text boxes / the slide's title placeholder; cards -> rounded rectangles; chart -> native PowerPoint chart;
  compare rows -> native table; QR -> small squares; presenter note -> speaker notes (quiz answers go there too).
  icon -> one editable freeform outline (Lucide, picked by meaning: deck_icons.py).
  Not possible natively: animations/builds, countdown timer, math typesetting (shown as plain text).
Variety: each slide type has several layouts; one is picked from the content and the seed, never the same twice running (choose()).
Colours: the primary plus up to two marker tones from deck_style (dz['tones']); type starts larger for young and older audiences (dz['audience']).
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


def split_head(x: str):
    """「용암: 땅 위로 흐르는 마그마」 -> ("용암", "땅 위로 ..."): a short name and its detail (two levels of text read faster than one long line)."""
    m = re.match(r"^\s*\**([^:：\n*]{1,14}?)\**\s*[:：]\s+(\S.*)$", str(x))
    return (m.group(1).strip(), m.group(2).strip()) if m else None


def build_pptx(spec: dict, base: Path, out: Path, seed: int | None = None, overrides: dict | None = None, template: Path | None = None, avoid: list | None = None) -> dict:
    """Build the .pptx. Returns {ok, slides, errors, warnings, style, seed, template, variants}."""
    import math
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml import parse_xml
    from pptx.oxml.ns import qn
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
    dz = dstyle.resolve(spec, seed, avoid)
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
    tpl = bool(template)
    pub = ctx_name == "public"
    aud = dz.get("audience", "")                      # young | kid | senior | "": who reads the screen
    soft = aud in ("young", "kid")                    # friendlier shapes for children
    MINPT = 16.0 if aud else 14.0                     # nothing on a slide shrinks below this; what still does not fit is reported
    zb = (1.18 if ctx_name in ("class", "promo") else 1.0) * (1.1 if aud else 1.0)  # rooms and posters are read from far away
    T1 = 40 if aud else (38 if ctx_name in ("class", "promo", "personal") else 36)  # body-slide title
    SM = 14                                           # sources, footnotes, captions
    TONES = list(dz.get("tones") or [C["pr"]])        # the colours a badge, a card head or a band may take (primary first; at most three)
    tone = lambda i: TONES[i % len(TONES)]  # noqa: E731
    tint = lambda c, a=0.14: dstyle.mix(C["bg1"], c, a)  # noqa: E731
    import deck_diagram as _dg
    import deck_icons as dicons

    def ink(c: str) -> str:
        """Text / icon colour on a filled tone."""
        if c == C["pr"]:
            return C["bt"]
        cw_, cb_ = _dg._contrast("#ffffff", c), _dg._contrast("#111111", c)
        return "#ffffff" if (cw_ >= 4.0 or cw_ > cb_) else "#111111"

    hsh = lambda key: dstyle._h(f"{key}|{seed}")  # noqa: E731
    chrome = "plain" if (tpl or pub) else ("tab", "rule", "chip")[hsh("chrome") % 3]            # how a body title is dressed, one way per deck
    motif = "base" if (tpl or pub) else ("bubbles" if soft else ("base", "trio", "side", "corner")[hsh("motif") % 4])  # the deck's one running ornament
    DEF_ICON = {"class": "graduation-cap", "promo": "megaphone", "personal": "sparkles", "public": "file-text"}.get(ctx_name, "presentation")
    used: dict = {}
    last_v = [""]
    variants: list = []

    def choose(kind: str, opts: list, it_: dict | None = None) -> str:
        """One of the layouts this content allows: the deck's seed sets where the rotation starts, a type that comes back takes the next one."""
        want = str((it_ or {}).get("layout") or "").split(".")[-1]
        if want in opts:
            v_ = want
        elif len(opts) == 1:
            v_ = opts[0]
        else:
            o = hsh("v|" + kind) % len(opts)
            order = opts[o:] + opts[:o]
            n_ = used.get(kind, 0)
            v_ = order[n_ % len(order)]
            if f"{kind}.{v_}" == last_v[0]:
                v_ = order[(n_ + 1) % len(order)]
        used[kind] = used.get(kind, 0) + 1
        last_v[0] = f"{kind}.{v_}"
        variants.append(last_v[0])
        return v_

    def layout_for(kind: str):
        """Template layouts: title-ish layout for title/closing/section, 'title only' else (placeholders by type, never by name)."""
        ls = list(prs.slide_layouts)
        def has(l, t):
            return any(p.placeholder_format.type is not None and int(p.placeholder_format.type) in t for p in l.placeholders)
        TITLE, CTR = (1, 3), (3,)  # TITLE, CENTER_TITLE
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
        # text fit: shrink (never below 60% / the deck's minimum size) so the text stays inside its box; what still does not fit is reported (split / shorten it)
        if shape is None or not template:
            bw, bh = (w * k - 0.16) * 72, (h * k - 0.08) * 72
        else:
            bw, bh = (tb.width / 914400 - 0.16) * 72, (tb.height / 914400 - 0.08) * 72
        plain_lines = [re.sub(r"\*\*", "", ln) for ln in str(text).replace("\\n", "\n").split("\n")]
        new_size, fits = pfit.fit_size(plain_lines, size, bw, bh, spacing, min_pt=min(MINPT, size))
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

    RAD = dz["lang"]["rad"]

    def rect(s, x, y, w, h, fill, line=None, round_=True, shape=None, lw=1.5, pill=False):
        sh = s.shapes.add_shape(shape or (MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE), I(x), I(y), I(w), I(h))
        if round_ and shape is None:
            sh.adjustments[0] = 0.5 if pill else (min(0.5, RAD / 100.0 * 0.9 / max(0.2, h / 2) * 0.5) if RAD else 0.02)
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

    n_back = [0]

    def behind(sh):
        """Send a backdrop shape under the title placeholder (a title must never be covered by a block or an ornament)."""
        tree_ = sh._element.getparent()
        tree_.remove(sh._element)
        tree_.insert(2 + n_back[0], sh._element)
        n_back[0] += 1
        sh.name = "decor"
        return sh

    def icon(s, nm, x, y, size, color, weight=1.0):
        """A Lucide outline as ONE editable freeform (round caps, the deck's colour): no picture file, recolourable in PowerPoint."""
        ol = dicons.outline(nm) if nm else []
        if not ol:
            return None
        sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(x), I(y), I(size), I(size))
        sp_ = sh._element.spPr
        old = sp_.find(qn("a:prstGeom"))
        paths = []
        for filled, cm in ol:
            seg = []
            for c_ in cm:
                pt = lambda j: '<a:pt x="%d" y="%d"/>' % (round(c_[j] * 1000), round(c_[j + 1] * 1000))  # noqa: E731
                if c_[0] == "M":
                    seg.append("<a:moveTo>%s</a:moveTo>" % pt(1))
                elif c_[0] == "L":
                    seg.append("<a:lnTo>%s</a:lnTo>" % pt(1))
                elif c_[0] == "C":
                    seg.append("<a:cubicBezTo>%s%s%s</a:cubicBezTo>" % (pt(1), pt(3), pt(5)))
                else:
                    seg.append("<a:close/>")
            paths.append('<a:path w="24000" h="24000" fill="%s">%s</a:path>' % ("norm" if filled else "none", "".join(seg)))
        cg = parse_xml('<a:custGeom xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
                       '<a:rect l="0" t="0" r="r" b="b"/><a:pathLst>%s</a:pathLst></a:custGeom>' % "".join(paths))
        sp_.replace(old, cg)
        sh.fill.solid()
        sh.fill.fore_color.rgb = rgb(color)
        sh.line.color.rgb = rgb(color)
        sh.line.width = Pt(max(1.5, size * k * 72 / 24 * 2 * weight))
        ln_ = sh.line._get_or_add_ln()
        ln_.set("cap", "rnd")
        ln_.append(ln_.makeelement(qn("a:round"), {}))
        sh.shadow.inherit = False
        sh.name = "icon"
        return sh

    def badge(s, x, y, d, c, label=None, ic=None, sq=False):
        """A filled disc (or tile) in a tone: the icon the line names, else its number / letter."""
        b_ = rect(s, x, y, d, d, c) if sq else rect(s, x, y, d, d, c, shape=MSO_SHAPE.OVAL)
        b_.name = "badge"
        if ic and dicons.exists(ic):
            icon(s, ic, x + d * 0.24, y + d * 0.24, d * 0.52, ink(c))
        elif label is not None:
            tbox(s, x, y, d, d, str(label), max(14, round(d * 72 * 0.4)), ink(c), True, "c", "m", "disp", emc=ink(c), shape=b_)
        return b_

    def ring(s, cx, cy, d, nm, on=None):
        """The cover picture when the author drew none: the topic's icon on a calm double disc, with two small tone dots."""
        outer = dstyle.mix(on, C["bt"], 0.16) if on else tint(C["pr"], 0.16)
        rect(s, cx - d / 2, cy - d / 2, d, d, outer, shape=MSO_SHAPE.OVAL).name = "decor"
        di = d * 0.74
        rect(s, cx - di / 2, cy - di / 2, di, di, C["bg1"] if on else C["card"], line=None if on else C["pr"], shape=MSO_SHAPE.OVAL, lw=2.5).name = "decor"
        icon(s, nm, cx - d * 0.21, cy - d * 0.21, d * 0.42, C["pr"])
        for j, (ang, rr) in enumerate(((-42, 0.11), (150, 0.075))):
            if len(TONES) > j + 1:
                px, py = cx + d / 2 * math.cos(math.radians(ang)), cy - d / 2 * math.sin(math.radians(ang))
                rect(s, px - d * rr, py - d * rr, 2 * d * rr, 2 * d * rr, TONES[j + 1], shape=MSO_SHAPE.OVAL).name = "decor"

    def put_title(s, text, x=0.8, y=0.55, w=11.7, h=1.15, size=36, color=None, align="l", anchor="m", emc=None):
        """The slide's real title placeholder (outline view / accessibility), restyled to our design."""
        ph = s.shapes.title
        if ph is None:
            return tbox(s, x, y, w, h, text, size, color or C["tx"], True, align, anchor, "disp", emc=emc)
        if not template:
            ph.left, ph.top, ph.width, ph.height = I(x), I(y), I(w), I(h)
        ph.text_frame.clear()
        tbox(s, x, y, w, h, text, size, color or C["tx"], True, align, anchor, "disp", emc=emc, shape=ph)
        return ph

    def kicker(s, text, y=0.38, x=0.8, color=None):
        if text:
            tbox(s, x, y, 11.7 - (x - 0.8), 0.4, str(text).upper(), 15, color or C["emc"], True, emc=color or C["emc"])

    def head(s, it, title, h=1.15, w=11.7):
        """A body slide's kicker + title, dressed the deck's one way (a tab, a short rule, or a filled label)."""
        k_ = it.get("kicker")
        if pub:
            kicker(s, k_)
            return put_title(s, title, 0.8, 0.65, w, 0.85, 28)
        if chrome == "plain":
            kicker(s, k_)
            return put_title(s, title, w=w, h=h)
        if chrome == "tab":
            rect(s, 0.8, 0.74, 0.16, 0.82, C["pr"], round_=False).name = "accent"
            kicker(s, k_, 0.32, 1.16)
            return put_title(s, title, 1.16, 0.58, w - 0.36, h, T1)
        if chrome == "rule":
            kicker(s, k_, 0.32)
            ph = put_title(s, title, 0.8, 0.58, w, h - 0.08, T1)
            rect(s, 0.88, 1.66, 1.3, 0.08, TONES[1 % len(TONES)], round_=False).name = "accent"
            return ph
        if k_:  # chip
            cw_ = min(5.0, pfit.width_em(str(k_).upper()) * 15 / 72 + 0.55)
            c_ = rect(s, 0.8, 0.36, cw_, 0.42, C["pr"], pill=True)
            tbox(s, 0.8, 0.36, cw_, 0.42, str(k_).upper(), 15, C["bt"], True, "c", "m", emc=C["bt"], shape=c_)
        return put_title(s, title, 0.8, 0.68 if k_ else 0.58, w, h - (0.1 if k_ else 0), T1)

    extra_slides = [0]
    quizzes: list = []  # (number, quiz slide) waiting for the answers slide
    deco: list = []     # this slide's running ornament (dropped when a full-bleed layout takes the page)

    def answers_slide():
        """「확인 문제 정답」: every check question with its answer and one-line reason, on one slide (two when there are more than four)."""
        pend = quizzes[:]
        del quizzes[:]
        for k0 in range(0, len(pend), 4):
            part = pend[k0:k0 + 4]
            sl = prs.slides.add_slide(layout_for("other"))
            n_back[0] = 0
            bg(sl, "bullets")
            head(sl, {"kicker": "정답"}, "확인 문제 정답" + (f" ({k0 // 4 + 1})" if len(pend) > 4 else ""))
            gap = 0.2
            few = len(part) <= 2  # one or two answers: bigger cards and type, not a strip lost on the page
            rh = min(2.1 if few else 1.6, (4.9 - gap * (len(part) - 1)) / len(part))
            y0 = 1.95 + max(0.0, (4.9 - (rh * len(part) + gap * (len(part) - 1))) / 2)
            for i, (no, q) in enumerate(part):
                y = y0 + i * (rh + gap)
                a_ = int(q.get("answer", 0))
                card(sl, 0.8, y, 11.7, rh)
                badge(sl, 1.05, y + rh / 2 - 0.36, 0.72, tone(i), no)
                tbox(sl, 2.05, y + 0.05, 10.3, rh * 0.42, plain(q["q"]), 22 if few else 18, C["ct"], anchor="m", emc=C["emcc"])
                line2 = f"**정답 {'ABCDE'[a_]}. {plain(q['choices'][a_])}**" + (f"   {plain(q['explain'])}" if q.get("explain") else "")
                tbox(sl, 2.05, y + rh * 0.45, 10.3, rh * 0.5, line2, 26 if few else 21, C["ct"], anchor="m", emc=C["emcc"])
            drop_empty(sl)
            extra_slides[0] += 1

    def drop_empty(s):
        for ph in list(s.placeholders):
            if ph.has_text_frame and not ph.text_frame.text.strip():
                ph._element.getparent().remove(ph._element)

    def bg(s, kind="content"):
        f = s.background.fill
        f.solid()
        f.fore_color.rgb = rgb(C["bg1"])
        del deco[:]
        cover_ = kind in ("title", "closing", "section", "hero")
        if tpl or pub:
            if kind in ("title", "closing", "section"):
                c = rect(s, W / k - 4.2, -1.6, 6.2, 6.2, C["bg2"], round_=False, shape=MSO_SHAPE.OVAL)
                behind(c)  # behind the title placeholder: a long title must never be covered by the ornament
            rect(s, 0, 7.5 - 0.14, 13.333, 0.14, C["pr"], round_=False).name = "decor"
            return
        if cover_:
            return  # covers, dividers and closings compose their own page
        if motif == "base":
            deco.append(rect(s, 0, 7.36, 13.333, 0.14, C["pr"], round_=False))
        elif motif == "trio":
            x_ = 0.0
            for j, part in enumerate((0.62, 0.24, 0.14)[:max(1, len(TONES))] if len(TONES) >= 3 else ((0.7, 0.3) if len(TONES) == 2 else (1.0,))):
                deco.append(rect(s, x_, 7.34, 13.333 * part + 0.01, 0.16, TONES[j], round_=False))
                x_ += 13.333 * part
        elif motif == "side":
            deco.append(rect(s, 0, 0, 0.26, 7.5, C["pr"], round_=False))
        elif motif == "corner":
            deco.append(rect(s, 13.333 - 1.25, -1.25, 2.5, 2.5, tint(C["pr"], 0.2), shape=MSO_SHAPE.OVAL))
            deco.append(rect(s, 0.8, 7.28, 1.6, 0.1, C["pr"], round_=False))
        else:  # bubbles: soft discs in the corner, for a young room
            deco.append(rect(s, 13.333 - 1.5, -1.3, 2.7, 2.7, tint(tone(1), 0.26), shape=MSO_SHAPE.OVAL))
            deco.append(rect(s, 13.333 - 0.95, 1.62, 0.36, 0.36, tone(2), shape=MSO_SHAPE.OVAL))  # below the title line, never under a long title
            deco.append(rect(s, -0.7, 6.6, 1.7, 1.7, tint(C["pr"], 0.22), shape=MSO_SHAPE.OVAL))
        for d_ in deco:
            behind(d_)

    def clear_deco():
        for d_ in deco:
            d_._element.getparent().remove(d_._element)
            n_back[0] -= 1
        del deco[:]

    def block(s, x, y, w, h, c=None):
        """A full-bleed colour field under the slide's text."""
        return behind(rect(s, x, y, w, h, c or C["pr"], round_=False))

    def qr_shapes(s, url, x, y, size):
        import deck_qr  # noqa: F401  (puts qrcodegen on the path)
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
        f_ = fill or C["card"]
        # a card the colour of the page is invisible (white on white): it gets a hairline so lists, choices and panels keep their shape
        same = _dg._contrast(f_, C["bg1"]) < 1.07
        c = rect(s, x, y, w, h, f_, line=C["line"] if (same or dz["lang"]["card"] in ("hair", "chalk", "glass")) else None, lw=1.25 if same else 1.5)
        return c

    def edge(s, x, y, w, h, c, top=False):
        """A card's tone edge (left bar or top bar). Square bars poke out of very round cards, so those go without."""
        if RAD >= 20:
            return
        (rect(s, x, y, w, 0.1, c, round_=False) if top else rect(s, x, y, 0.12, h, c, round_=False)).name = "accent"

    def line(s, x1, y1, x2, y2, color, w=2.0, arrow=False, dash=False):
        from pptx.enum.dml import MSO_LINE
        from pptx.enum.shapes import MSO_CONNECTOR
        cn = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2))
        cn.line.color.rgb = rgb(color)
        cn.line.width = Pt(w)
        if dash:
            cn.line.dash_style = MSO_LINE.DASH
        if arrow:
            ln_ = cn.line._get_or_add_ln()
            ln_.append(ln_.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
        return cn

    _NUMCELL = re.compile(r"^[\s+\-−]?[\d,.]+\s*(?:%p?|명|개|원|건|회|점|교|학급|시간|차시|만 ?원|억 ?원|천 ?원|권|대|곳|가구|세대)?$")

    def draw_table(s, cols, rows, x, y, w, h, fs, hi=None):
        fs = max(fs, 16)  # a table read from the back of the room: never under 16pt
        gt = s.shapes.add_table(len(rows) + 1, len(cols), I(x), I(y), I(w), I(h))
        tb = gt.table
        # the first column names the rows when it is words and the others are figures: it is set apart (bold on a quiet tint)
        label0 = len(cols) >= 3 and not any(_NUMCELL.match(plain(str(r[0]))) for r in rows)
        for r in range(len(rows) + 1):
            for c_ in range(len(cols)):
                cell = tb.cell(r, c_)
                txt = plain(str(cols[c_] if r == 0 else rows[r - 1][c_]))
                cell.fill.solid()
                lab = label0 and c_ == 0 and r > 0
                cell.fill.fore_color.rgb = rgb(C["pr"] if r == 0 else (tint(C["pr"], 0.16) if lab else (C["card"] if r % 2 else C["bg2"])))
                tf = cell.text_frame
                tf.paragraphs[0].text = ""
                # a number with an optional unit is right-aligned; a label that starts with a digit (1학년, 3분기, 2026년) is not
                num_ = c_ > 0 and bool(_NUMCELL.match(txt))
                tf.paragraphs[0].alignment = PP_ALIGN.CENTER if r == 0 else (PP_ALIGN.RIGHT if num_ else PP_ALIGN.LEFT)
                tcol = C["bt"] if r == 0 else (C["emcc"] if hi == c_ else C["tx"])
                fill_runs(tf.paragraphs[0], txt, fs, tcol, tcol if r == 0 else C["emc"], bold=(r == 0 or hi == c_ or lab))
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left = cell.margin_right = I(0.12)
        return gt

    def draw_chart(s, it, x, y, w, h, fs=16):
        fs = max(fs, 14)
        cd = CategoryChartData()
        cd.categories = [plain(x_) for x_ in it["labels"]]
        for se in it["series"]:
            cd.add_series(se.get("name", ""), se["data"])
        kind = it.get("kind", "bar")
        ct = {"bar": XL_CHART_TYPE.COLUMN_CLUSTERED, "line": XL_CHART_TYPE.LINE_MARKERS, "pie": XL_CHART_TYPE.PIE, "doughnut": XL_CHART_TYPE.DOUGHNUT}[kind]
        gf = s.shapes.add_chart(ct, I(x), I(y), I(w), I(h), cd)
        ch = gf.chart
        ch.font.size = Pt(fs)
        ch.font.color.rgb = rgb(C["tx"])
        ch.has_legend = kind in ("pie", "doughnut") or len(it["series"]) > 1
        if ch.has_legend:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        pal = TONES + [c_ for c_ in (C["ac"], C["good"], C["bad"], C["mu"], C["emc"], C["line"], C["cb"]) if c_ not in TONES]
        plot = ch.plots[0]
        if kind in ("pie", "doughnut"):
            plot.has_data_labels = True
            plot.data_labels.font.size = Pt(fs)
            for pi, pt in enumerate(plot.series[0].points):
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = rgb(pal[pi % len(pal)])
        else:
            plot.has_data_labels = True
            plot.data_labels.font.size = Pt(fs)
            plot.data_labels.font.color.rgb = rgb(C["tx"])
            for si, se in enumerate(plot.series):
                if kind == "bar":
                    se.format.fill.solid()
                    se.format.fill.fore_color.rgb = rgb(pal[si % len(pal)])
                else:
                    se.format.line.color.rgb = rgb(pal[si % len(pal)])
                    se.format.line.width = Pt(3.5 if fs >= 16 else 2.5)
            ch.value_axis.has_major_gridlines = True
            ch.value_axis.major_gridlines.format.line.color.rgb = rgb(C["line"])
            if it.get("unit"):
                ch.value_axis.has_title = True
                ch.value_axis.axis_title.text_frame.text = str(it["unit"])
                ch.value_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(max(SM, fs - 2))
                ch.value_axis.axis_title.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(C["mu"])
        return gf

    def band(s, text, y=6.0, h=0.76, x=0.8, w=11.7):
        """The slide's conclusion in a filled band (the answer to 'so what')."""
        b_ = rect(s, x, y, w, h, C["pr"], round_=not RAD < 12)
        b_.name = "takeaway"
        tbox(s, x, y, w, h, text, 22, C["bt"], True, "c", "m", emc=C["bt"], shape=b_)

    def draw_diagram(s, it, cx0, cy0, cw_, backing=True):
        import deck_diagram as dg
        ch_ = cw_ * 0.6
        if backing:
            card(s, cx0, cy0, cw_, ch_)
        u = cw_ / 100.0
        fz = min(1.0, max(0.86 if ctx_name == "class" else 0.78, cw_ / 7.6))  # a small canvas (inside a panel) gets smaller labels, never tiny ones
        lo_ = 14.0
        for n_, sh_ in enumerate(it["shapes"]):
            kd = dg.kind_of(sh_)
            col = dg.legible(dg.color(sh_.get("color"), C, "ct" if kd in ("label", "line", "dash") else "pr"), it["shapes"], n_, C)
            if kd in ("line", "dash", "arrow", "dasharrow"):
                cn = line(s, cx0 + float(sh_["x1"]) * u, cy0 + float(sh_["y1"]) * u, cx0 + float(sh_["x2"]) * u, cy0 + float(sh_["y2"]) * u,
                          col, max(2.0, float(sh_.get("w", 4)) * 0.75), "arrow" in kd, "dash" in kd)
                cn.name = "diagram"
            elif kd in ("rect", "circle"):
                fill_ = None if sh_.get("fill") == "none" else dg.color(sh_.get("fill"), C, "bg2")
                line_ = dg.color(sh_.get("color"), C, "line") if (sh_.get("color") or fill_ is None) else None
                if kd == "rect":
                    bx = (cx0 + float(sh_["x"]) * u, cy0 + float(sh_["y"]) * u, float(sh_["w"]) * u, float(sh_["h"]) * u)
                    g_ = rect(s, *bx, fill_, line=line_, round_=False, lw=2)
                else:
                    rx_, ry_ = (v * u for v in dg.radii(sh_))
                    bx = (cx0 + float(sh_["cx"]) * u - rx_, cy0 + float(sh_["cy"]) * u - ry_, 2 * rx_, 2 * ry_)
                    g_ = rect(s, *bx, fill_, line=line_, shape=MSO_SHAPE.OVAL, lw=2)
                g_.name = "diagram"
                if sh_.get("text"):
                    tc_ = dg.ink_on(fill_) if fill_ else C["ct"]
                    tbox(s, bx[0], bx[1], bx[2], bx[3], plain(sh_["text"]), max(lo_, 17 * fz), tc_, True, "c", "m", emc=tc_, shape=g_)
            elif kd == "poly":
                pts = [(cx0 + float(p_[0]) * u, cy0 + float(p_[1]) * u) for p_ in sh_["points"]]
                fb_ = s.shapes.build_freeform(I(pts[0][0]), I(pts[0][1]))
                fb_.add_line_segments([(I(px), I(py)) for px, py in pts[1:]], close=True)
                g_ = fb_.convert_to_shape()
                fill_ = None if sh_.get("fill") == "none" else dg.color(sh_.get("fill"), C, "bg2")
                if fill_:
                    g_.fill.solid()
                    g_.fill.fore_color.rgb = rgb(fill_)
                else:
                    g_.fill.background()
                if sh_.get("color") or fill_ is None:
                    g_.line.color.rgb = rgb(dg.color(sh_.get("color"), C, "line"))
                    g_.line.width = Pt(2)
                else:
                    g_.line.fill.background()
                g_.shadow.inherit = False
                g_.name = "diagram"
                if sh_.get("text"):
                    tc_ = dg.ink_on(fill_) if fill_ else C["ct"]
                    mx_, my_ = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
                    tbox(s, mx_ - 1.1, my_ - 0.28, 2.2, 0.56, plain(sh_["text"]), max(lo_, 17 * fz), tc_, True, "c", "m", emc=tc_).name = "diagram label"
            elif kd == "arc":
                acx, acy, ar, a0, a1 = dg.arc_points(sh_)
                ar *= u
                g_ = s.shapes.add_shape(MSO_SHAPE.ARC, I(cx0 + acx * u - ar), I(cy0 + acy * u - ar), I(2 * ar), I(2 * ar))
                av = g_._element.spPr.find(qn("a:prstGeom")).find(qn("a:avLst"))
                if av is None:
                    pg_ = g_._element.spPr.find(qn("a:prstGeom"))
                    av = pg_.makeelement(qn("a:avLst"), {})
                    pg_.append(av)
                for old_ in list(av):
                    av.remove(old_)
                for nm_, vv in (("adj1", a0), ("adj2", a1)):
                    av.append(av.makeelement(qn("a:gd"), {"name": nm_, "fmla": "val %d" % int(round(vv * 60000))}))
                g_.fill.background()
                g_.line.color.rgb = rgb(col)
                g_.line.width = Pt(2.5)
                g_.shadow.inherit = False
                g_.name = "diagram"
            elif kd == "label":
                fs_ = max(lo_, {"s": 15, "m": 19, "l": 25}.get(str(sh_.get("size", "m")), 19) * fz)
                al_ = str(sh_.get("align", "c"))[:1]
                al_ = al_ if al_ in ("l", "c", "r") else "c"
                wd_ = max(1.2 * fz, pfit.width_em(plain(sh_["text"])) * fs_ / 72 + 0.45)
                lx = cx0 + float(sh_["x"]) * u - {"l": 0.08, "r": wd_ - 0.08}.get(al_, wd_ / 2)
                lx = max(0.05, min(lx, 13.283 - wd_))  # a bigger label must still end inside the slide
                tbox(s, lx, cy0 + float(sh_["y"]) * u - 0.29, wd_, 0.58, plain(sh_["text"]), fs_, col, True, al_, "m", emc=col).name = "diagram label"

    import types as _types
    import deck_panel as dpanel
    KIT = _types.SimpleNamespace(tbox=tbox, rect=rect, card=card, line=line, chart=draw_chart, table=draw_table, diagram=draw_diagram, C=C, OVAL=MSO_SHAPE.OVAL,
                                 ink=ink, tone=tone, tones=TONES, badge=badge, icon=icon, edge=edge, picks=dicons.pick_all, pick=dicons.pick,
                                 z=(1.25 if ctx_name == "promo" else (1.18 if ctx_name == "class" else 1.0)) * (1.08 if aud else 1.0),
                                 lo=16.0 if (aud or ctx_name in ("class", "promo")) else 14.0, soft=soft)
    TAKE = ("bullets", "compare", "steps", "timeline", "bignumbers", "table", "panel")  # types whose "takeaway" becomes a band under the body
    BT, BH = 1.95, 4.9  # body top and height (inches) under a normal title

    def two_text(x, br=False):
        hd = split_head(x)
        if not hd or "**" in str(x):
            return str(x)
        return f"**{hd[0]}**" + ("\n" if br else "  ") + hd[1]

    def draw_rows(s, items, ics, bx, by, bw, bh, labels=None):
        """A list as cards in rows: a tone disc (the line's icon, else its number) and the text."""
        n = len(items)
        gap = 0.2 if n <= 4 else 0.15
        ch = min(1.6, (bh - gap * (n - 1)) / n)  # cards grow to fill the body; a short list is centred, not stuck to the top
        y0 = by + max(0.0, (bh - (ch * n + gap * (n - 1))) / 2)
        fs = (30 if n <= 3 else (27 if n == 4 else (24 if n == 5 else 22))) * (1.12 if aud else 1.0)
        d = max(0.5, min(0.8, ch - 0.28))
        for i, x in enumerate(items):
            y = y0 + i * (ch + gap)
            card(s, bx, y, bw, ch)
            edge(s, bx, y, bw, ch, tone(i))
            badge(s, bx + 0.34, y + ch / 2 - d / 2, d, tone(i), (labels[i] if labels else i + 1), ics[i] if ics else None)
            tx0 = bx + 0.34 + d + 0.28
            tbox(s, tx0, y + 0.04, bx + bw - tx0 - 0.2, ch - 0.08, two_text(x, br=ch >= 1.25 and n <= 4), fs, C["ct"], anchor="m", emc=C["emcc"])

    slides = spec["slides"]
    n_sec = 0
    for idx, it in enumerate(slides):
        t = it["type"]
        cur[0] = idx + 1
        if pub and t == "section":  # 보고 자료: no divider pages; the section name is in every slide's header band
            n_sec += 1
            extra_slides[0] -= 1
            continue
        if t == "closing" and quizzes:
            answers_slide()
        s = prs.slides.add_slide(layout_for("cover" if t in ("title", "closing") else "other"))
        n_back[0] = 0
        bg(s, t)
        notes = [it.get("note", "")] if it.get("note") else []
        if pub and t not in ("title", "section", "closing"):  # public header: section name left, 기관 right, thin rule
            sec, org = str(it.get("_section") or ""), str(spec.get("org") or spec.get("agency") or "")
            rect(s, 0, 0, 13.333, 0.56, C["pr"], round_=False).name = "decor"  # header band: gives every page the accent colour
            if sec:
                tbox(s, 0.8, 0.05, 7.5, 0.46, sec, 14, C["bt"], True, anchor="m", emc=C["bt"])
            if org:
                tbox(s, 7.5, 0.05, 5.0, 0.46, org, 14, C["bt"], True, "r", "m", emc=C["bt"])
        src = ctx_source(it)
        cut = 1.0 if (t in TAKE and it.get("takeaway")) else 0.0  # room taken at the bottom of the body by the takeaway band
        bx0, bw0 = 0.8, 11.7  # where the band and the source line sit (a side layout moves them)
        if t == "title" and pub:
            kicker(s, it.get("kicker"))
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
            rect(s, 0, 6.75, 13.333, 0.61, C["pr"], round_=False).name = "decor"
        elif t == "bullets" and pub:
            head(s, it, plain(it["title"]))
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
            nl = len(lines)
            rect(s, 0.8, 1.72, 11.7, 5.0 - cut - (0.15 if cut else 0), C["bg2"], round_=False).name = "panel"
            rect(s, 0.8, 1.72, 0.1, 5.0 - cut - (0.15 if cut else 0), C["pr"], round_=False).name = "accent"
            tbox(s, 1.15, 1.85, 11.2, 4.75 - cut - (0.15 if cut else 0), "\n".join(lines), 28 if nl <= 3 else (26 if nl == 4 else (22 if nl <= 6 else 20)), C["tx"],
                 spacing=2.3 if nl <= 3 else (2.1 if nl == 4 else (1.7 if nl == 5 else (1.5 if nl == 6 else 1.35))))
        elif t == "table":
            head(s, it, plain(it["title"]), h=1.0)
            cols, rows = it["columns"], it["rows"]
            top_ = 1.9 if pub else BT
            kv = (not tpl and len(cols) == 2 and len(rows) <= 7 and plain(str(cols[0])).strip() in ("항목", "구분", "내용", "분류", "사항", "")
                  and max(len(plain(str(r[0]))) for r in rows) <= 9)
            v = choose("table", ["kv"] if kv else ["grid"], it)
            if v == "kv":  # 항목 | 내용: a label tile and its value per row reads faster (and larger) than a two-column grid
                n = len(rows)
                bh_ = BH - cut - (0.25 if src else 0)
                gap = 0.14
                rh = min(1.0, (bh_ - gap * (n - 1)) / n)
                y0 = top_ + max(0.0, (bh_ - (rh * n + gap * (n - 1))) / 2)
                lw_ = min(3.6, max(2.3, max(pfit.width_em(plain(str(r[0]))) for r in rows) * 22 * zb / 72 + (1.1 if rh >= 0.7 else 0.5)))
                ics = dicons.pick_all([plain(str(r[0])) for r in rows], it.get("icons"))
                fs = 24 * zb if n <= 5 else 22 * zb
                for i, r in enumerate(rows):
                    y = y0 + i * (rh + gap)
                    lab = rect(s, 0.8, y, lw_, rh, C["pr"])
                    lab.name = "label"
                    ix = 0.0
                    if ics and rh >= 0.7:
                        icon(s, ics[i], 1.0, y + rh / 2 - 0.2, 0.4, C["bt"])
                        ix = 0.5
                    tbox(s, 0.9 + ix, y, lw_ - 0.2 - ix, rh, plain(str(r[0])), min(fs, 22 * zb), C["bt"], True, "c" if not ix else "l", "m", "disp", emc=C["bt"])
                    card(s, 0.8 + lw_ + 0.14, y, 11.7 - lw_ - 0.14, rh, tint(C["pr"], 0.09))
                    tbox(s, 0.8 + lw_ + 0.4, y, 11.7 - lw_ - 0.7, rh, str(r[1]), fs, C["tx"], anchor="m")
            else:
                if it.get("unit"):
                    tbox(s, 8.5, top_ - 0.42, 4.0, 0.38, f"(단위: {it['unit']})", SM, C["mu"], align="r")
                nr_, nc_ = len(rows), len(cols)
                fs = (24 if nc_ <= 3 else 22) if nr_ <= 4 else ((22 if nc_ <= 4 else 20) if nr_ <= 6 else (20 if nc_ <= 4 else 18))
                draw_table(s, cols, rows, 0.8, top_, 11.7, min(4.8 - cut, (1.0 if nr_ <= 4 else 0.86) * (nr_ + 1)), fs * (1.1 if aud and nr_ <= 5 else 1.0), it.get("highlight"))
        elif t == "summary":
            head(s, it, plain(it.get("title") or "요약"), h=1.0)
            y0 = 1.8
            if it.get("text"):
                tbox(s, 0.8, y0, 11.7, 0.6, it["text"], 20, C["tx"], True)
                y0 += 0.8
            rect(s, 0.8, y0 + 0.2, 11.7, 6.6 - y0 - 0.2, None, line=C["pr"], round_=False, lw=2.5)
            lab = rect(s, 1.1, y0, 1.4, 0.42, C["pr"], round_=False)
            tbox(s, 1.1, y0, 1.4, 0.42, it.get("label") or "핵심", 16, C["bt"], True, "c", "m", shape=lab)
            np_ = len(it["points"])
            tbox(s, 1.2, y0 + 0.75, 10.9, 6.3 - y0 - 0.9, "\n".join("□ " + plain(x_) for x_ in it["points"]), 26 if np_ <= 3 else (24 if np_ == 4 else 22), C["tx"],
                 spacing=2.0 if np_ <= 3 else (1.7 if np_ == 4 else 1.4))
        elif t == "toc":
            kicker(s, it.get("kicker"))
            put_title(s, plain(it.get("title") or "목차"), 0.8, 0.6, 5, 1.0, 40)
            rect(s, 0.8, 1.7, 0.7, 0.07, C["pr"], round_=False).name = "accent"
            its = it.get("items") or []
            rh = min(1.05, 4.7 / max(len(its), 1))  # rows use the whole page width and height (a short 목차 must not look empty)
            for i_, x_ in enumerate(its):
                y = 2.0 + i_ * rh
                lab = f"{dctx.roman(i_ + 1)}." if pub else f"{i_ + 1:02d}"
                tbox(s, 1.3, y, 1.2, rh, lab, 28, dstyle.legible(tone(i_), C["bg1"], 4.5), True, anchor="m", name="disp")
                tbox(s, 2.6, y, 9.9, rh, re.sub(r"^\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.\s*", "", plain(str(x_))), 28, C["tx"], anchor="m")
                rect(s, 1.3, y + rh - 0.02, 11.2, 0.015, C["line"], round_=False).name = "rule"
        elif t == "hero":
            facts = [str(x_) for x_ in (it.get("facts") or [])][:3]
            nm = dicons.name(it.get("icon")) or dicons.pick(str(spec.get("title") or "")) or dicons.pick(str(it.get("kicker") or "") + " " + plain(it["headline"])) or DEF_ICON
            if it.get("file"):
                v = "photo"
                p_ = Path(it["file"])
                p_ = p_ if p_.is_absolute() else base / p_
                pic = s.shapes.add_picture(str(p_), 0, 0, prs.slide_width, prs.slide_height)
                pic.name = "image"
                pic._element.nvPicPr.cNvPr.set("descr", plain(it.get("headline", "")))
                sc_ = rect(s, 0, 3.4, 13.333, 4.1, "#000000", round_=False)
                sc_.name = "scrim"
                sf = sc_.fill._xPr.find(qn("a:solidFill"))
                if sf is not None and len(sf):
                    sf[0].append(sf[0].makeelement(qn("a:alpha"), {"val": "55000"}))
                hc, mc = "#ffffff", "#f2f2f2"
                if it.get("kicker"):
                    tbox(s, 0.8, 3.6, 7.6, 0.4, it["kicker"], 16, mc, True)
                put_title(s, plain(it["headline"]), 0.8, 4.0, 9.0, 1.6, 54, hc)
                if it.get("sub"):
                    tbox(s, 0.8, 5.65, 9.0, 0.6, it["sub"], 20, mc)
                if it.get("cta"):
                    b_ = rect(s, 0.8, 6.4, 3.2, 0.7, C["pr"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
                    tbox(s, 0.8, 6.4, 3.2, 0.7, it["cta"], 20, C["bt"], True, "c", "m", shape=b_)
                if it.get("url"):
                    qr_shapes(s, it["url"], 10.2, 4.1, 2.4)
            else:
                v = "right" if tpl else choose("hero", ["right", "left"] + ([] if (facts or it.get("url")) else ["full"]), it)
                full = v == "full"
                bx_, bw_ = (8.45, 4.883) if v == "right" else ((0.0, 4.9) if v == "left" else (0.0, 13.333))
                tx_, tw_ = (0.8, 7.2) if v != "left" else (5.5, 7.1)
                blk = rect(s, bx_, 0, bw_, 7.5, C["pr"], round_=False)
                behind(blk) if not tpl else setattr(blk, "name", "decor")
                hc, mc = (C["bt"], C["bt"]) if full else (C["tx"], C["mu"])
                acx = bx_ + bw_ / 2 if not full else 10.2  # the colour field carries the picture and the facts a reader acts on
                if it.get("url"):
                    qr_shapes(s, it["url"], acx - 1.4, 2.35, 2.8)
                elif facts:
                    ring(s, acx, 1.75, 2.2, nm, on=C["pr"])
                    fh = min(1.0, 3.6 / len(facts) - 0.16)
                    fy = 3.3 + (3.6 - (fh + 0.16) * len(facts) + 0.16) / 2
                    fics = [dicons.pick(plain(f_)) for f_ in facts]
                    for j, f_ in enumerate(facts):
                        y = fy + j * (fh + 0.16)
                        rect(s, bx_ + 0.4, y, bw_ - 0.8, fh, C["bg1"]).name = "fact"
                        ox = 0.0
                        if fics[j]:
                            icon(s, fics[j], bx_ + 0.62, y + fh / 2 - 0.2, 0.4, C["pr"])
                            ox = 0.55
                        tbox(s, bx_ + 0.55 + ox, y, bw_ - 1.1 - ox, fh, f_, 22, C["tx"], True, anchor="m")
                else:
                    ring(s, acx, 3.75, 3.5 if not full else 3.9, nm, on=C["pr"])
                y_ = 1.35
                if it.get("kicker"):
                    kt = str(it["kicker"])
                    kc = tone(1) if (len(TONES) > 1 and not full) else (C["bg1"] if full else C["pr"])
                    cw_ = min(tw_, pfit.width_em(kt) * 18 / 72 + 0.7)
                    c_ = rect(s, tx_, y_, cw_, 0.56, kc, pill=True)
                    ki = C["pr"] if full else ink(kc)
                    tbox(s, tx_, y_, cw_, 0.56, kt, 18, ki, True, "c", "m", emc=ki, shape=c_)
                put_title(s, plain(it["headline"]), tx_, 2.1, tw_, 2.3, 54, hc, anchor="m", emc=hc)
                if it.get("sub"):
                    tbox(s, tx_, 4.5, tw_, 1.05, it["sub"], 24, mc, emc=mc)
                if it.get("cta"):
                    cc = C["bg1"] if full else (tone(1) if len(TONES) > 1 else C["pr"])
                    ci = C["pr"] if full else ink(cc)
                    bwid = min(tw_, max(3.4, pfit.width_em(plain(it["cta"])) * 22 / 72 + 1.0))
                    b_ = rect(s, tx_, 5.8, bwid, 0.86, cc, pill=True)
                    tbox(s, tx_, 5.8, bwid, 0.86, it["cta"], 22, ci, True, "c", "m", emc=ci, shape=b_)
        elif t == "title":
            has_draw = bool(it.get("shapes"))
            nm = dicons.name(it.get("icon")) or dicons.pick(plain(it["title"])) or dicons.pick(str(spec.get("subject") or "")) or DEF_ICON
            v = "plain" if tpl else choose("cover", ["block", "band", "plain"], it)
            if v == "block":
                bw_ = 5.6
                block(s, 0, 0, bw_, 7.5)
                kicker(s, it.get("kicker"), 1.15, 0.7, C["bt"])
                put_title(s, plain(it["title"]), 0.7, 1.7, bw_ - 1.2, 2.8, 46, C["bt"], "l", "m", emc=C["bt"])
                rect(s, 0.78, 4.62, 1.1, 0.09, TONES[1] if len(TONES) > 1 else C["bt"], round_=False).name = "accent"
                if it.get("subtitle"):
                    tbox(s, 0.7, 4.85, bw_ - 1.2, 1.3, it["subtitle"], 22, C["bt"], emc=C["bt"])
                if it.get("meta"):
                    tbox(s, 0.7, 6.2, bw_ - 1.2, 1.05, it["meta"], 16, C["bt"], anchor="b", emc=C["bt"])
                if has_draw:
                    draw_diagram(s, it, 6.35, 1.75, 6.3)
                else:
                    ring(s, 9.45, 3.75, 4.0, nm)
            elif v == "band":
                block(s, 0, 0, 13.333, 4.6)
                tw_ = 6.9 if has_draw else 7.6
                kicker(s, it.get("kicker"), 0.7, 0.9, C["bt"])
                put_title(s, plain(it["title"]), 0.9, 1.2, tw_, 3.0, 50, C["bt"], "l", "m", emc=C["bt"])
                if it.get("subtitle"):
                    tbox(s, 0.9, 4.9, tw_, 0.95, it["subtitle"], 24, C["tx"])
                if it.get("meta"):
                    tbox(s, 0.9, 5.9, tw_, 0.8, it["meta"], 16, C["mu"])
                for j in range(min(3, len(TONES))):
                    rect(s, 0.98 + j * 0.9, 6.78, 0.75, 0.12, TONES[j], round_=False).name = "decor"
                if has_draw:
                    draw_diagram(s, it, 8.05, 1.9, 4.6)
                else:
                    ring(s, 10.5, 4.3, 3.6, nm, on=None)
            else:
                tw_ = 6.0 if (has_draw or not tpl) else 10.5  # the cover picture takes the right side
                kicker(s, it.get("kicker"), 1.2, 1.25)
                rect(s, 0.8, 2.0, 0.18, 2.3, C["pr"], round_=False).name = "accent"
                put_title(s, plain(it["title"]), 1.25, 1.8, tw_, 2.6, 54, align="l", anchor="m")
                if it.get("subtitle"):
                    tbox(s, 1.25, 4.6, tw_, 1.35, it["subtitle"], 24, C["mu"], name="body")
                if it.get("meta"):
                    tbox(s, 1.25, 6.0, tw_, 0.95, it["meta"], 16, C["mu"])
                if has_draw:
                    draw_diagram(s, it, 7.55, 1.75, 5.0)
                elif not tpl:
                    ring(s, 10.0, 3.7, 4.0, nm)
                    x_ = 0.0
                    for j in range(len(TONES)):
                        wd_ = 13.333 * ((0.62, 0.24, 0.14)[j] if len(TONES) == 3 else (1.0 / len(TONES)))
                        rect(s, x_, 7.3, wd_ + 0.01, 0.2, TONES[j], round_=False).name = "decor"
                        x_ += wd_
        elif t == "section":
            n_sec += 1
            num_ = str(it.get("num") or f"{n_sec:02d}")
            v = "num" if tpl else choose("section", ["num", "block"], it)
            if v == "block":
                block(s, 0, 0, 4.4, 7.5)
                tbox(s, 0.6, 2.4, 3.2, 2.2, num_, 110, C["bt"], True, "c", "m", name="disp", emc=C["bt"])
                kicker(s, it.get("kicker"), 2.0, 5.1)
                put_title(s, plain(it["title"]), 5.1, 2.5, 7.4, 1.8, 44)
                rect(s, 5.18, 4.4, 1.2, 0.09, tone(1), round_=False).name = "accent"
                if it.get("sub"):
                    tbox(s, 5.1, 4.7, 7.4, 1.0, it["sub"], 22, C["mu"])
            else:
                kicker(s, it.get("kicker"))
                tbox(s, 0.8, 1.7, 4, 1.4, num_, 80, C["emc"], True, name="disp")
                put_title(s, plain(it["title"]), 0.8, 3.2, 11.5, 1.5, 44)
                if it.get("sub"):
                    tbox(s, 0.8, 4.8, 11.5, 0.7, it["sub"], 22, C["mu"])
                if not tpl:
                    rect(s, 0, 7.3, 13.333, 0.2, C["pr"], round_=False).name = "decor"
        elif t == "statement":
            q_ = plain(it["text"]).rstrip().endswith(("?", "까", "까요"))
            v = "center" if (tpl or pub) else choose("statement", ["center", "block", "bar"], it)
            if v == "block":
                clear_deco()
                block(s, 0, 0, 13.333, 7.5)
                kicker(s, it.get("kicker"), 0.9, 1.0, C["bt"])
                if q_:
                    rect(s, 6.17, 0.85, 1.0, 1.0, C["bg1"], shape=MSO_SHAPE.OVAL).name = "badge"
                    icon(s, "circle-help", 6.41, 1.09, 0.52, C["pr"])
                put_title(s, it["text"], 1.0, 1.9, 11.3, 3.1, 48, C["bt"], align="c", emc=C["bt"])
                if it.get("sub"):
                    c_ = rect(s, 2.2, 5.25, 8.9, 0.9, C["bg1"], pill=True)
                    tbox(s, 2.2, 5.25, 8.9, 0.9, it["sub"], 22, C["tx"], False, "c", "m", shape=c_)
            elif v == "bar":
                kicker(s, it.get("kicker"), 1.1, 1.5)
                rect(s, 0.9, 1.6, 0.22, 3.6, C["pr"], round_=False).name = "accent"
                put_title(s, it["text"], 1.5, 1.5, 10.6, 3.8, 46, align="l")
                if it.get("sub"):
                    tbox(s, 1.5, 5.45, 10.6, 0.9, it["sub"], 24, C["mu"])
            else:
                kicker(s, it.get("kicker"))
                if q_ and not (tpl or pub):
                    badge(s, 6.17, 0.8, 1.0, C["pr"], None, "circle-help")
                else:
                    rect(s, 6.07, 1.25, 1.2, 0.09, C["pr"], round_=False).name = "accent"
                put_title(s, it["text"], 1.0, 1.85, 11.3, 3.1, 48, align="c")
                if it.get("sub"):
                    tbox(s, 1.0, 5.15, 11.3, 0.9, it["sub"], 24, C["mu"], align="c")
        elif t == "bullets":
            items = it["items"]
            n = len(items)
            pl = [plain(x) for x in items]
            mx = max(len(p_) for p_ in pl)
            ics = dicons.pick_all(pl, it.get("icons"))
            mins = it.get("minutes") if it.get("_role") == "activity" else None
            opts = ["rows"]
            if not tpl:
                def roomy(w_in, h_in, at=21.0):  # a layout is offered only when every line stays readable in it
                    return all(pfit.fit_size([p_], at, (w_in - 0.16) * 72, (h_in - 0.08) * 72, 1.12, min_pt=at)[1] for p_ in pl)
                gc_ = n if n <= 3 else (2 if n == 4 else 3)
                gw_ = (11.7 - 0.26 * (gc_ - 1)) / gc_
                if n in (2, 3, 4, 6) and (roomy(gw_ - 0.44, 1.7, 22) if n <= 3 else roomy(gw_ - 1.5, (BH - cut - 0.26) / 2 - 0.12)):
                    opts.append("grid")
                if n <= 5 and len(plain(it["title"])) <= 22 and not mins and roomy(5.9, min(1.6, ((5.15 if cut else 5.9) - 0.2 * (n - 1)) / n) - 0.08):
                    opts.append("side")
            v = choose("bullets", opts, it)
            if v == "side":  # the title stands on a colour field at the left, the list has the rest of the page
                clear_deco()
                pw_ = 4.5
                block(s, 0, 0, pw_, 7.5)
                kicker(s, it.get("kicker"), 0.95, 0.6, C["bt"])
                put_title(s, plain(it["title"]), 0.6, 1.4, pw_ - 1.0, 2.7, 36, C["bt"], "l", "t", emc=C["bt"])
                nm = dicons.name(it.get("icon")) or dicons.pick(plain(it["title"])) or {"objectives": "target", "recap": "list-checks", "activity": "puzzle"}.get(it.get("_role", ""), "")
                if nm:
                    icon(s, nm, 0.7, 4.95, 1.6, dstyle.mix(C["pr"], C["bt"], 0.6))
                bx0, bw0 = pw_ + 0.45, 12.533 - (pw_ + 0.45)
                draw_rows(s, items, ics, bx0, 0.8, bw0, (5.95 if cut else 6.7) - 0.8)
            else:
                head(s, it, plain(it["title"]), w=9.6 if mins else 11.7)
                if mins:  # an activity says how long it takes
                    c_ = rect(s, 10.55, 0.78, 1.95, 0.7, tint(tone(1), 0.3), pill=True)
                    c_.name = "time"
                    icon(s, "clock", 10.78, 0.93, 0.4, C["tx"])
                    tbox(s, 11.2, 0.78, 1.25, 0.7, f"{int(mins)}분", 22, C["tx"], True, "l", "m")
                if v == "grid":  # short items stand side by side as tiles
                    cols = n if n <= 3 else (2 if n == 4 else 3)
                    rws = (n + cols - 1) // cols
                    g = 0.26
                    bh_ = BH - cut
                    cw = (11.7 - g * (cols - 1)) / cols
                    ch = (bh_ - g * (rws - 1)) / rws
                    if rws == 1:
                        ch = min(ch, 3.8 if mx > 16 else 3.1)  # tiles as tall as their words need, centred in the body
                    y0 = BT + (bh_ - (ch * rws + g * (rws - 1))) / 2
                    d = min(1.1, ch * 0.3) if rws == 1 else min(0.78, ch - 0.4)
                    fs = (29 if rws == 1 else 24) * (1.14 if aud else 1.0)
                    for i, x in enumerate(items):
                        cx, cy = 0.8 + (i % cols) * (cw + g), y0 + (i // cols) * (ch + g)
                        card(s, cx, cy, cw, ch)
                        edge(s, cx, cy, cw, ch, tone(i), top=True)
                        if rws == 1:
                            badge(s, cx + cw / 2 - d / 2, cy + 0.42, d, tone(i), i + 1, ics[i] if ics else None)
                            tbox(s, cx + 0.22, cy + 0.42 + d + 0.22, cw - 0.44, ch - (0.42 + d + 0.22) - 0.2, two_text(x, br=True), fs, C["ct"], align="c", emc=C["emcc"])
                        else:
                            badge(s, cx + 0.3, cy + ch / 2 - d / 2, d, tone(i), i + 1, ics[i] if ics else None)
                            tx0 = cx + 0.3 + d + 0.24
                            tbox(s, tx0, cy + 0.06, cx + cw - tx0 - 0.18, ch - 0.12, two_text(x, br=True), fs, C["ct"], anchor="m", emc=C["emcc"])
                else:
                    draw_rows(s, items, ics, 0.8, BT, 11.7, BH - cut)
        elif t == "compare":
            head(s, it, plain(it["title"]))
            ca, cb_ = C["pr"], (TONES[1] if len(TONES) > 1 else C["ac"])
            if it.get("rows"):
                rows = it["rows"]
                gt = s.shapes.add_table(len(rows) + 1, 3, I(0.8), I(BT), I(11.7), I(min(BH - cut, (1.0 if len(rows) <= 3 else 0.9) * (len(rows) + 1))))
                tb = gt.table
                tb.columns[0].width, tb.columns[1].width, tb.columns[2].width = I(3.1), I(4.3), I(4.3)
                hd_ = ["", it["a"].get("label", "A"), it["b"].get("label", "B")]
                fs = 22 if len(rows) <= 4 else 20
                for r in range(len(rows) + 1):
                    for c_ in range(3):
                        cell = tb.cell(r, c_)
                        txt = hd_[c_] if r == 0 else (rows[r - 1].get("k", "") if c_ == 0 else rows[r - 1].get("a" if c_ == 1 else "b", ""))
                        cell.fill.solid()
                        hf = (C["bg1"] if c_ == 0 else (ca if c_ == 1 else cb_))
                        cell.fill.fore_color.rgb = rgb(hf if r == 0 else (tint(C["pr"], 0.16) if c_ == 0 else (C["card"] if r % 2 else C["bg2"])))
                        tf = cell.text_frame
                        tf.paragraphs[0].text = ""
                        tc_ = (ink(hf) if c_ else C["tx"]) if r == 0 else (C["tx"] if c_ == 0 else C["ct"])
                        if r == 0:
                            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
                        fill_runs(tf.paragraphs[0], plain(txt), fs + (2 if r == 0 else 0), tc_, tc_ if r == 0 else C["emcc"], bold=(r == 0 or c_ == 0))
                        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                        cell.margin_left = cell.margin_right = I(0.14)
            else:
                v = "cards" if tpl else choose("compare", ["cards", "versus"], it)
                bh_ = BH - cut
                for j, side in enumerate(("a", "b")):
                    cj = ca if j == 0 else cb_
                    its_ = it[side].get("items", [])[:5]
                    lab_ = it[side].get("label", side.upper())
                    fs = (26 if len(its_) <= 3 else (22 if len(its_) == 4 else 20)) * (1.12 if aud else 1.0)
                    if v == "versus":  # two tinted fields facing each other, a round 'VS' between them
                        x = 0.8 + j * 6.1
                        rect(s, x, BT, 5.6, bh_, tint(cj, 0.16)).name = "panel"
                        cw_ = min(4.6, max(2.2, pfit.width_em(plain(lab_)) * 26 / 72 + 0.9))
                        hd = rect(s, x + (5.6 - cw_) / 2, BT + 0.3, cw_, 0.8, cj, pill=True)
                        tbox(s, x + (5.6 - cw_) / 2, BT + 0.3, cw_, 0.8, lab_, 26, ink(cj), True, "c", "m", "disp", emc=ink(cj), shape=hd)
                        tbox(s, x + 0.4, BT + 1.25, 4.8, bh_ - 1.4, "\n".join("• " + plain(x_) for x_ in its_), fs, C["tx"], anchor="m",
                             spacing=1.5 if len(its_) <= 3 else 1.28)
                    else:
                        x = 0.8 + j * 6.0
                        card(s, x, BT, 5.7, bh_)
                        hd = rect(s, x, BT, 5.7, 0.95, cj)
                        tbox(s, x, BT, 5.7, 0.95, lab_, 26, ink(cj), True, "c", "m", "disp", emc=ink(cj), shape=hd)
                        tbox(s, x + 0.3, BT + 1.05, 5.1, bh_ - 1.15, "\n".join("• " + plain(x_) for x_ in its_), fs, C["ct"], anchor="m", emc=C["emcc"],
                             spacing=1.5 if len(its_) <= 3 else 1.28)
                if v == "versus":
                    vs_ = rect(s, 6.666 - 0.5, BT + bh_ / 2 - 0.5, 1.0, 1.0, C["tx"], shape=MSO_SHAPE.OVAL)
                    vs_.name = "vs"
                    tbox(s, 6.166, BT + bh_ / 2 - 0.5, 1.0, 1.0, "VS", 20, C["bg1"], True, "c", "m", "disp", emc=C["bg1"], shape=vs_)
        elif t == "steps":
            st = it["steps"]
            n = len(st)
            mins = it.get("minutes") if it.get("_role") == "activity" else None
            head(s, it, plain(it["title"]), w=9.6 if mins else 11.7)
            if mins:
                c_ = rect(s, 10.55, 0.78, 1.95, 0.7, tint(tone(1), 0.3), pill=True)
                c_.name = "time"
                icon(s, "clock", 10.78, 0.93, 0.4, C["tx"])
                tbox(s, 11.2, 0.78, 1.25, 0.7, f"{int(mins)}분", 22, C["tx"], True, "l", "m")
            ics = dicons.pick_all([plain(x_.get("title", "")) + " " + plain(x_.get("text", "")) for x_ in st], [x_.get("icon") for x_ in st] if any(x_.get("icon") for x_ in st) else it.get("icons"))
            longest = max(len(plain(x_.get("text", ""))) for x_ in st)
            opts = ["track"] + ([] if tpl else (["arrows"] if n <= 5 else []) + (["ladder"] if (n >= 4 or longest > 22) else []))
            if not tpl and longest > (34 if n <= 3 else 26):
                opts = ["ladder"]  # long instructions need the full width of a row
            v = choose("steps", opts, it)
            bh_ = BH - cut
            cw = 11.7 / n
            if v == "ladder":  # one row per step: the number tile, the name, what to do
                gap = 0.16
                rh = min(1.25, (bh_ - gap * (n - 1)) / n)
                y0 = BT + max(0.0, (bh_ - (rh * n + gap * (n - 1))) / 2)
                tw_ = min(3.6, max(2.4, max(pfit.width_em(plain(x_.get("title", ""))) for x_ in st) * 26 * min(zb, 1.1) / 72 + 0.6))
                for i, x_ in enumerate(st):
                    y = y0 + i * (rh + gap)
                    badge(s, 0.8, y, rh, tone(i), i + 1, ics[i] if ics else None, sq=True)
                    card(s, 0.8 + rh + 0.14, y, 11.7 - rh - 0.14, rh)
                    tbox(s, 0.8 + rh + 0.34, y, tw_, rh, x_.get("title", ""), 26 * min(zb, 1.1), C["ct"], True, anchor="m", name="disp", emc=C["emcc"])
                    tbox(s, 0.8 + rh + 0.44 + tw_, y, 11.7 - rh - 0.74 - tw_, rh, x_.get("text", ""), 24 * min(zb, 1.15), C["ct"], anchor="m", emc=C["emcc"])
            elif v == "arrows":  # block arrows in the deck's tones carry the names, the detail sits under each
                for i, x_ in enumerate(st):
                    cx = 0.8 + i * cw
                    ar = rect(s, cx + 0.04, BT, cw - 0.08, 1.15, tone(i), shape=MSO_SHAPE.PENTAGON if i < n - 1 else MSO_SHAPE.RECTANGLE)
                    ar.name = "step"
                    tbox(s, cx + 0.1, BT, cw - 0.55, 1.15, f"{i + 1}. {plain(x_.get('title', ''))}", 22 * min(zb, 1.1), ink(tone(i)), True, "c", "m", "disp", emc=ink(tone(i)))
                    ch_ = min(bh_ - 1.35, 2.7 if longest <= 18 else 9.9)
                    card(s, cx + 0.04, BT + 1.35, cw - 0.2, ch_)
                    if ics:
                        icon(s, ics[i], cx + cw / 2 - 0.42, BT + 1.6, 0.7, dstyle.legible(tone(i), C["card"], 3.0))
                    oy = 1.05 if ics else 0.12
                    tbox(s, cx + 0.16, BT + 1.35 + oy, cw - 0.44, ch_ - oy - 0.1, x_.get("text", ""), 23 * zb, C["ct"], align="c", anchor="t" if ics else "m", emc=C["emcc"])
            else:
                rect(s, 0.8 + cw / 2, 2.92, 11.7 - cw, 0.06, C["line"], round_=False).name = "line"
                for i, x_ in enumerate(st):
                    cx = 0.8 + i * cw
                    badge(s, cx + cw / 2 - 0.5, 2.45, 1.0, tone(i), i + 1, ics[i] if ics else None)
                    card(s, cx + 0.1, 3.7, cw - 0.2, 3.15 - cut)
                    tbox(s, cx + 0.2, 3.78, cw - 0.4, 0.85, x_.get("title", ""), 23 * zb, C["ct"], True, "c", "m", name="disp", emc=C["emcc"])
                    tbox(s, cx + 0.2, 4.65, cw - 0.4, 2.1 - cut, x_.get("text", ""), 20 * zb, C["ct"], align="c", emc=C["emcc"])
        elif t == "bignumber":
            if it.get("title"):
                head(s, it, plain(it["title"]))
            else:
                kicker(s, it.get("kicker"))
                put_title(s, plain(it["value"]) + str(it.get("unit", "")), 0.8, 0.4, 11.7, 0.4, 12, C["bg1"])
            tbox(s, 0.8, 1.9, 11.7, 2.6, f"{plain(it['value'])}{it.get('unit', '')}", 120, C["emc"], True, "c", "m", "disp")
            if not tpl:
                rect(s, 6.07, 4.5, 1.2, 0.1, tone(1), round_=False).name = "accent"
            if it.get("caption") or it.get("label"):
                tbox(s, 0.8, 4.8, 11.7, 1.1, it.get("caption") or it.get("label"), 28, C["tx"], align="c")
        elif t == "bignumbers":
            head(s, it, plain(it.get("title", "")) or "숫자로 보기")
            its = it["items"]
            n = len(its)
            v = "cards" if tpl else choose("bignumbers", ["cards", "filled"], it)
            cw = (11.7 - 0.3 * (n - 1)) / n
            for i, x_ in enumerate(its):
                x = 0.8 + i * (cw + 0.3)
                tc_ = tone(i)
                if v == "filled":
                    rect(s, x, BT + 0.05, cw, 4.3 - cut, tc_).name = "card"
                    nc_, cc_ = ink(tc_), ink(tc_)
                else:
                    card(s, x, BT + 0.05, cw, 4.3 - cut)
                    edge(s, x, BT + 0.05, cw, 4.3 - cut, tc_, top=True)
                    nc_, cc_ = dstyle.legible(tc_, C["card"], 4.5), C["ct"]
                tbox(s, x, 2.5 - cut * 0.35, cw, 1.9 - cut * 0.3, f"{plain(x_.get('value', ''))}{x_.get('unit', '')}", 72 if n == 2 else 60, nc_, True, "c", "m", "disp", emc=nc_)
                tbox(s, x + 0.2, 4.6 - cut * 0.75, cw - 0.4, 1.4 - cut * 0.2, x_.get("caption", x_.get("label", "")), 24, cc_, align="c", emc=cc_)
        elif t == "quote":
            kicker(s, it.get("kicker"))
            tbox(s, 1.0, 0.3, 2.5, 2.3, "“", 120, C["emc"], True, name="disp")
            put_title(s, it["text"], 1.3, 2.0, 10.7, 3.4, 44)
            if it.get("who"):
                tbox(s, 1.3, 5.6, 10.7, 0.6, "— " + it["who"], 20, C["mu"])
        elif t == "illustration":
            kicker(s, it.get("kicker"))
            put_title(s, plain(it["title"]), 0.8, 0.55, 7.2, 1.6, T1)
            if it.get("text"):
                tbox(s, 0.8, 2.5, 7.0, 3.2, it["text"], 26, C["mu"])
            nm = dicons.name(it.get("motif")) or dicons.name(it.get("_icon_word")) or dicons.pick(plain(it["title"])) or DEF_ICON
            ring(s, 10.4, 3.9, 4.0, nm)
        elif t == "quiz":
            ch = it["choices"]
            ans = int(it.get("answer", 0))
            kicker(s, it.get("kicker"), 0.5)
            if tpl:
                put_title(s, it["q"], 0.8, 1.0, 11.7, 1.8, 38)
            else:
                badge(s, 0.8, 1.2, 1.1, C["pr"], "Q")
                put_title(s, it["q"], 2.15, 0.95, 10.35, 1.6, 36 * (1.06 if aud else 1.0))
            maxc = max(len(plain(x_)) for x_ in ch)
            cols = 2 if (len(ch) >= 4 or (len(ch) == 2 and maxc <= 14)) else 1
            rows_ = (len(ch) + cols - 1) // cols
            bw = (11.7 - 0.3 * (cols - 1)) / cols
            top, room = 2.95, 3.95
            bh = min(1.5 if cols == 2 else 1.25, (room - 0.22 * (rows_ - 1)) / rows_)
            top += (room - (bh * rows_ + 0.22 * (rows_ - 1))) / 2
            d = min(0.8, bh - 0.3)
            for i, x_ in enumerate(ch):
                x = 0.8 + (i % cols) * (bw + 0.3)
                y = top + (i // cols) * (bh + 0.22)
                card(s, x, y, bw, bh)
                badge(s, x + 0.28, y + bh / 2 - d / 2, d, tone(i), "ABCDE"[i])
                tbox(s, x + 0.28 + d + 0.25, y, bw - (0.28 + d + 0.25) - 0.2, bh, plain(x_), 27 * (1.07 if aud else 1.0), C["ct"], anchor="m", emc=C["emcc"])
            quizzes.append((len(quizzes) + 1, it))
            notes.append(f"정답: {'ABCDE'[ans]}. {plain(ch[ans])}" + (f" - {plain(it['explain'])}" if it.get("explain") else "") + " (뒤쪽 「확인 문제 정답」 장에 모아 두었어요)")
        elif t == "timeline":
            head(s, it, plain(it["title"]))
            ev = it["events"]
            n = len(ev)
            longest = max(len(plain(e.get("text", ""))) for e in ev)
            v = choose("timeline", ["rows"] if (not tpl and longest > (34 if n <= 3 else 26)) else ["track"] + ([] if tpl else (["rows"] if (n >= 4 or longest > 24) else [])), it)
            bh_ = BH - cut
            if v == "rows":  # one row per date: the date tile, what happens
                gap = 0.16
                rh = min(1.2, (bh_ - gap * (n - 1)) / n)
                y0 = BT + max(0.0, (bh_ - (rh * n + gap * (n - 1))) / 2)
                ww = min(3.2, max(1.9, max(pfit.width_em(plain(e.get("when", ""))) for e in ev) * 22 / 72 + 0.6))
                line(s, 0.8 + ww / 2, y0 + rh / 2, 0.8 + ww / 2, y0 + (n - 1) * (rh + gap) + rh / 2, C["line"], 3).name = "line"
                for i, e in enumerate(ev):
                    y = y0 + i * (rh + gap)
                    c_ = rect(s, 0.8, y + 0.1, ww, rh - 0.2, tone(i), pill=True)
                    tbox(s, 0.8, y + 0.1, ww, rh - 0.2, e.get("when", ""), 22, ink(tone(i)), True, "c", "m", "disp", emc=ink(tone(i)), shape=c_)
                    card(s, 0.8 + ww + 0.2, y, 11.7 - ww - 0.2, rh)
                    tw_ = min(3.8, max(2.2, max(pfit.width_em(plain(e_.get("title", ""))) for e_ in ev) * 23 / 72 + 0.4))
                    tbox(s, 0.8 + ww + 0.4, y, tw_, rh, e.get("title", ""), 23, C["ct"], True, anchor="m", name="disp", emc=C["emcc"])
                    tbox(s, 0.8 + ww + 0.5 + tw_, y, 11.7 - ww - 0.9 - tw_, rh, e.get("text", ""), 20 * min(zb, 1.15), C["ct"], anchor="m", emc=C["emcc"])
            else:
                cw = 11.7 / n
                rect(s, 0.8 + cw / 2, 3.2, 11.7 - cw, 0.06, C["line"], round_=False).name = "line"
                for i, e in enumerate(ev):
                    cx = 0.8 + i * cw
                    c_ = rect(s, cx + 0.2, 2.05, cw - 0.4, 0.66, tone(i), pill=True)
                    tbox(s, cx + 0.2, 2.05, cw - 0.4, 0.66, e.get("when", ""), 21, ink(tone(i)), True, "c", "m", "disp", emc=ink(tone(i)), shape=c_)
                    rect(s, cx + cw / 2 - 0.16, 3.07, 0.32, 0.32, tone(i), shape=MSO_SHAPE.OVAL).name = "dot"
                    card(s, cx + 0.1, 3.7, cw - 0.2, 3.15 - cut)
                    tbox(s, cx + 0.2, 3.78, cw - 0.4, 0.8, e.get("title", ""), 23 * zb, C["ct"], True, "c", "m", name="disp", emc=C["emcc"])
                    tbox(s, cx + 0.2, 4.6, cw - 0.4, 2.15 - cut, e.get("text", ""), 20 * zb, C["ct"], align="c", emc=C["emcc"])
        elif t == "chart":
            head(s, it, plain(it["title"]), h=1.0)
            has_t = bool(it.get("takeaway"))
            draw_chart(s, it, 0.8, 1.8, 11.7, 4.05 if has_t else 4.95, 18 if (aud or ctx_name == "class") else 16)
            if has_t:
                band(s, it["takeaway"], 6.0 if (src or pub) else 6.1)
        elif t == "math":
            head(s, it, plain(it["title"]) if it.get("title") else "수식", h=1.0)
            card(s, 0.8, 2.0, 11.7, 2.2)
            tbox(s, 0.8, 2.0, 11.7, 2.2, tex_plain(it["tex"]), 40, C["ct"], True, "c", "m", "disp")
            if it.get("text"):
                tbox(s, 0.8, 4.6, 11.7, 1.6, it["text"], 24, C["mu"], align="c")
            notes.append("수식 원본(TeX): " + it["tex"] + "  (PPT에서는 읽기 쉬운 글자로 바꿨어요. 필요하면 [삽입 > 수식]으로 다시 쓰세요.)")
        elif t == "timer":
            head(s, it, plain(it.get("title", "")) or "활동 시간", h=1.2)
            tbox(s, 0.8, 2.3, 11.7, 3.0, f"{int(it.get('minutes', 5)):02d}:00", 150, C["emc"], True, "c", "m", "disp")
            tbox(s, 0.8, 5.5, 11.7, 0.6, f"{int(it.get('minutes', 5))}분", 24, C["mu"], align="c")
            notes.append("웹 슬라이드의 카운트다운은 PPT에서 움직이지 않아요. 시간은 교실 타이머를 쓰세요.")
        elif t == "qr":
            kicker(s, it.get("kicker"))
            put_title(s, plain(it["title"]), 0.8, 0.55, 6.5, 1.8)
            if it.get("caption"):
                tbox(s, 0.8, 2.6, 6.5, 1.5, it["caption"], 24, C["mu"])
            tbox(s, 0.8, 4.4, 6.5, 0.6, it["url"], 18, C["emc"])
            qr_shapes(s, it["url"], 8.0, 1.6, 4.5)
        elif t == "image":
            kicker(s, it.get("kicker"))
            if it.get("title"):
                put_title(s, plain(it["title"]), h=0.9)
            p = Path(it["file"])
            p = p if p.is_absolute() else base / p
            from PIL import Image
            with Image.open(p) as im_:
                iw, ih = im_.size
            top = 1.6 if it.get("title") else 0.5
            maxw, maxh = 11.7, 7.0 - top
            sc = min(maxw / iw, maxh / ih)
            w_, h_ = iw * sc, ih * sc
            pic = s.shapes.add_picture(str(p), I(0.8 + (maxw - w_) / 2), I(top + (maxh - h_) / 2), I(w_), I(h_))
            pic.name = "image"
            pic._element.nvPicPr.cNvPr.set("descr", plain(it.get("caption") or it.get("title") or p.stem))
            if it.get("caption"):
                tbox(s, 0.8, 6.85 - 0.1, 11.7, 0.4, it["caption"], SM, C["mu"], align="c")
        elif t == "video":
            head(s, it, plain(it.get("title", "")) or "영상", h=1.0)
            card(s, 2.5, 2.2, 8.3, 3.6)
            tbox(s, 2.5, 2.2, 8.3, 3.6, f"영상 파일: {Path(it['file']).name}\n[삽입 > 비디오]로 이 자리에 넣어 주세요", 24, C["ct"], align="c", anchor="m")
        elif t == "diagram":
            head(s, it, plain(it["title"]), h=1.0)
            pts_ = it.get("points") or []
            cw_ = 7.6 if pts_ else 8.2
            ch_ = cw_ * 0.6
            cx0, cy0 = (0.8 if pts_ else (13.333 - cw_) / 2), 1.8
            draw_diagram(s, it, cx0, cy0, cw_)
            if pts_:
                px_, pw_ = cx0 + cw_ + 0.3, 12.5 - (cx0 + cw_ + 0.3)
                rh_ = min(1.4, (ch_ - 0.2 * (len(pts_) - 1)) / len(pts_))
                y0_ = cy0 + (ch_ - (rh_ * len(pts_) + 0.2 * (len(pts_) - 1))) / 2
                for i, x_ in enumerate(pts_):
                    yy = y0_ + i * (rh_ + 0.2)
                    card(s, px_, yy, pw_, rh_)
                    rect(s, px_, yy, 0.12, rh_, tone(i), round_=False).name = "accent"
                    tbox(s, px_ + 0.25, yy, pw_ - 0.35, rh_, x_, 21, C["ct"], anchor="m", emc=C["emcc"])
            if it.get("caption"):
                tbox(s, 0.8, cy0 + ch_ + 0.08, 11.7, 0.5, it["caption"], 17, C["mu"], align="c")
        elif t == "panel":
            if pub:
                head(s, it, plain(it["title"]))
                rect(s, 0.8, 1.55, 11.7, 0.03, C["pr"], round_=False).name = "rule"
            else:
                head(s, it, plain(it["title"]), h=1.0)
            top_ = 1.75 if pub else 1.85
            dpanel.draw_pptx(KIT, s, it, 0.8, top_, 11.7, ((6.0 if (src or pub) else 6.1) - 0.16 if cut else (6.72 if (src or pub) else 6.9)) - top_)
        elif t == "closing":
            nxt = [plain(x_) for x_ in it.get("next", [])[:4]]
            nm = dicons.name(it.get("icon")) or dicons.pick(plain(it["title"])) or {"class": "circle-check", "promo": "megaphone"}.get(ctx_name, "smile")
            v = "plain" if (tpl or pub) else choose("closing", ["plain", "block"], it)
            if v == "block":
                block(s, 0, 0, 13.333, 7.5)
                kicker(s, it.get("kicker"), 1.0, 0.9, C["bt"])
                lw_ = 6.4 if (nxt or it.get("url")) else 7.2
                put_title(s, plain(it["title"]), 0.9, 1.5, lw_, 2.5, 52, C["bt"], anchor="m", emc=C["bt"])
                rect(s, 0.98, 4.1, 1.2, 0.09, C["bg1"], round_=False).name = "accent"
                if it.get("sub"):
                    tbox(s, 0.9, 4.35, lw_, 1.3, it["sub"], 24, C["bt"], emc=C["bt"])
                if it.get("url"):
                    qr_shapes(s, it["url"], 8.6, 1.5, 3.4)
                    tbox(s, 7.9, 5.0, 4.8, 0.6, it["url"], SM, C["bt"], align="c", emc=C["bt"])
                    for i, x_ in enumerate(nxt[:2]):
                        tbox(s, 0.9, 5.7 + i * 0.6, lw_, 0.55, "→ " + x_, 20, C["bt"], emc=C["bt"])
                elif nxt:
                    rh = min(1.15, (5.5 - 0.18 * (len(nxt) - 1)) / len(nxt))
                    y0 = 1.0 + (5.5 - (rh * len(nxt) + 0.18 * (len(nxt) - 1))) / 2
                    for i, x_ in enumerate(nxt):
                        y = y0 + i * (rh + 0.18)
                        rect(s, 7.6, y, 4.95, rh, C["bg1"]).name = "next"
                        badge(s, 7.82, y + rh / 2 - 0.3, 0.6, tone(i + 1), i + 1)
                        tbox(s, 8.6, y, 3.8, rh, x_, 21, C["tx"], anchor="m")
                else:
                    ring(s, 10.3, 3.75, 3.8, nm, on=C["pr"])
            else:
                kicker(s, it.get("kicker"))
                put_title(s, plain(it["title"]), 0.8, 1.2, 7.4, 2.4, 52, anchor="m")
                if it.get("sub"):
                    tbox(s, 0.8, 3.8, 7.4, 0.9, it["sub"], 24, C["mu"])
                for i, x_ in enumerate(nxt):
                    tbox(s, 0.8, 4.9 + i * 0.58, 7.4, 0.55, "→ " + x_, 21, C["tx"])
                if it.get("url"):
                    qr_shapes(s, it["url"], 8.9, 1.4, 3.6)
                    tbox(s, 8.4, 5.1, 4.6, 0.9, it["url"], SM, C["mu"], align="c")
                elif not (tpl or pub):
                    ring(s, 10.4, 3.6, 3.8, nm)
                    rect(s, 0, 7.3, 13.333, 0.2, C["pr"], round_=False).name = "decor"
        if cut and t != "chart":
            band(s, it["takeaway"], 6.0 if (src or pub) else 6.1, x=bx0, w=bw0)
        if src:  # 자료/주 line on data slides
            tbox(s, bx0, 6.85, bw0, 0.42, src, SM, C["mu"])
        if notes:
            s.notes_slide.notes_text_frame.text = "\n".join(plain(n) for n in notes if n)
        drop_empty(s)
    if quizzes:  # a deck without a closing slide still gets its answers
        answers_slide()
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
    rep.update(ok=True, slides=len(slides) + extra_slides[0], fit=fit_log, style=dz["style"], seed=seed, template=str(template) if template else "",
               variants=variants, tones=TONES, audience=aud,
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
