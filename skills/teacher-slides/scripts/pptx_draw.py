# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Draw a .pptx slide as HTML+SVG straight from its XML (no LibreOffice): the approximate preview used by pptx_render.py.

Drawn: slide / layout / master background and their decorative shapes, preset shapes (rect, roundRect, ellipse, triangle, arrows,
arc, homePlate, ...), lines and connectors (dash, arrow heads, flips), freeforms (custGeom), groups, rotation, solid / gradient /
picture fills with alpha, outlines, pictures (crop, embedded as data URI), tables (cell fills, borders, merged cells, the default
banded style), native charts (column / bar / line / area / pie / doughnut with data labels and legend), text (runs, sizes, colours,
bullets, alignment, anchors, insets, inherited placeholder position and styles, normAutofit scale).
Still approximate: font metrics and line breaks differ from PowerPoint; SmartArt, 3-D, effects other than fills are not drawn.
Works for any .pptx (python-pptx, pptxgenjs, PowerPoint), so two decks can be compared with the same eyes.
"""
from __future__ import annotations

import base64
import colorsys
import html
import math
from pathlib import Path

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
RID = "{%s}" % NS["r"]
STAGE = 1600.0  # px width of the drawn slide
DEF_ACCENTS = ["4472C4", "ED7D31", "A5A5A5", "FFC000", "5B9BD5", "70AD47"]
MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml", "bmp": "image/bmp", "webp": "image/webp"}

_XP = __import__("lxml.etree").etree._Element.xpath  # python-pptx overrides .xpath() without the namespaces argument


def X(el, path):
    return _XP(el, path, namespaces=NS) if el is not None else []


def X1(el, path):
    r = X(el, path)
    return r[0] if r else None


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


# ---- colours -------------------------------------------------------------------------------------------------------------
class Theme:
    def __init__(self, master):
        self.colors = {"dk1": "000000", "lt1": "FFFFFF", "dk2": "44546A", "lt2": "E7E6E6", "hlink": "0563C1", "folHlink": "954F72"}
        for i, c in enumerate(DEF_ACCENTS, 1):
            self.colors[f"accent{i}"] = c
        self.map = {"bg1": "lt1", "tx1": "dk1", "bg2": "lt2", "tx2": "dk2"}
        self.major = self.minor = ""
        try:
            for rel in master.part.rels.values():
                if rel.reltype.endswith("/theme"):
                    from lxml import etree
                    th = etree.fromstring(rel.target_part.blob)
                    for el in X(th, "//a:clrScheme/*"):
                        name = el.tag.split("}")[1]
                        v = X(el, "./a:srgbClr/@val") or X(el, "./a:sysClr/@lastClr")
                        if v:
                            self.colors[name] = v[0]
                    self.major = (X(th, "//a:majorFont/a:ea/@typeface") or X(th, "//a:majorFont/a:latin/@typeface") or [""])[0]
                    self.minor = (X(th, "//a:minorFont/a:ea/@typeface") or X(th, "//a:minorFont/a:latin/@typeface") or [""])[0]
            cm = X1(master._element, "./p:clrMap")
            if cm is not None:
                for k in ("bg1", "tx1", "bg2", "tx2"):
                    if cm.get(k):
                        self.map[k] = cm.get(k)
        except Exception:
            pass

    def scheme(self, name: str, ph: str | None = None) -> str | None:
        if name == "phClr":
            return ph
        return self.colors.get(self.map.get(name, name))


def _mods(hex_: str, el) -> tuple[str, float]:
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (0, 2, 4))
    alpha = 1.0
    for m in el:
        tag = m.tag.split("}")[1]
        try:
            v = int(m.get("val", "100000")) / 100000
        except ValueError:
            continue
        if tag == "alpha":
            alpha = v
        elif tag in ("lumMod", "lumOff"):
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            l = min(1, max(0, l * v if tag == "lumMod" else l + v))
            r, g, b = colorsys.hls_to_rgb(h, l, s)
        elif tag == "tint":
            r, g, b = (c + (1 - c) * (1 - v) for c in (r, g, b))
        elif tag == "shade":
            r, g, b = (c * v for c in (r, g, b))
    return "%02X%02X%02X" % tuple(int(round(min(1, max(0, c)) * 255)) for c in (r, g, b)), alpha


def color_of(el, th: Theme, ph: str | None = None):
    """(hex, alpha) from an element that CONTAINS a colour child (a:solidFill, a:gs, a:fgClr ...), or None."""
    if el is None:
        return None
    for c in el:
        tag = c.tag.split("}")[1] if "}" in c.tag else c.tag
        base = None
        if tag == "srgbClr":
            base = c.get("val")
        elif tag == "schemeClr":
            base = th.scheme(c.get("val", ""), ph)
        elif tag == "sysClr":
            base = c.get("lastClr") or ("FFFFFF" if c.get("val") == "window" else "000000")
        elif tag == "prstClr":
            base = {"black": "000000", "white": "FFFFFF", "red": "FF0000", "blue": "0000FF", "green": "008000", "yellow": "FFFF00", "gray": "808080"}.get(c.get("val", ""), "808080")
        if base and len(base) == 6:
            try:
                return _mods(base, c)
            except ValueError:
                return None
    return None


def css_color(ca) -> str:
    if not ca:
        return "transparent"
    h, a = ca
    if a >= 0.999:
        return "#" + h
    return "rgba(%d,%d,%d,%.3f)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ---- drawing context --------------------------------------------------------------------------------------------------
class Draw:
    def __init__(self, prs, slide):
        self.prs, self.slide = prs, slide
        self.W, self.H = prs.slide_width, prs.slide_height
        self.k = STAGE / self.W  # px per EMU
        self.pt = STAGE / (self.W / 914400) / 72  # px per pt
        self.layout = slide.slide_layout
        self.master = self.layout.slide_master
        self.th = Theme(self.master)
        self.part = slide.part
        self.defs: list[str] = []
        self._id = 0
        try:
            self.no = [s.slide_id for s in prs.slides].index(slide.slide_id) + 1
        except Exception:
            self.no = 0

    def uid(self, p="m") -> str:
        self._id += 1
        return f"{p}{self._id}"

    # -- fills / lines
    def fill_css(self, pr, part, ph=None, style=None):
        """Return (css background or None when not specified, svg fill value, has_image). 'none' = explicitly empty."""
        if pr is not None:
            if X1(pr, "./a:noFill") is not None:
                return "none"
            sf = X1(pr, "./a:solidFill")
            if sf is not None:
                return css_color(color_of(sf, self.th, ph))
            gf = X1(pr, "./a:gradFill")
            if gf is not None:
                stops = []
                for gs in X(gf, "./a:gsLst/a:gs"):
                    stops.append((int(gs.get("pos", "0")) / 1000, css_color(color_of(gs, self.th, ph))))
                stops.sort()
                ang = int((X(gf, "./a:lin/@ang") or ["5400000"])[0]) / 60000
                if stops:
                    return "linear-gradient(%.0fdeg,%s)" % (ang + 90, ",".join(f"{c} {p:.0f}%" for p, c in stops))
            bf = X1(pr, "./a:blipFill")
            if bf is not None:
                uri = self.image_uri(bf, part)
                if uri:
                    return f"url('{uri}') center/cover no-repeat"
            pf = X1(pr, "./a:pattFill")
            if pf is not None:
                return css_color(color_of(X1(pf, "./a:fgClr"), self.th, ph))
            if X1(pr, "./a:grpFill") is not None:
                return None
        if style is not None:
            fr = X1(style, "./a:fillRef")
            if fr is not None and fr.get("idx", "0") != "0":
                return css_color(color_of(fr, self.th))
        return None

    def line_of(self, pr, style=None):
        """(css colour, width px, dash css array or '', head, tail) or None."""
        ln = X1(pr, "./a:ln") if pr is not None else None
        col, w = None, None
        if ln is not None:
            if X1(ln, "./a:noFill") is not None:
                return None
            col = color_of(X1(ln, "./a:solidFill"), self.th)
            if ln.get("w"):
                w = int(ln.get("w")) * self.k
        if col is None and style is not None:
            lr = X1(style, "./a:lnRef")
            if lr is not None and lr.get("idx", "0") != "0":
                col = color_of(lr, self.th)
                if col and w is None:
                    w = 12700 * self.k * (1 if lr.get("idx") == "1" else 2)
        if col is None:
            return None
        w = max(w if w is not None else 9525 * self.k, 0.8)
        dash = (X(ln, "./a:prstDash/@val") or ["solid"])[0] if ln is not None else "solid"
        da = {"dash": f"{4 * w:.1f} {3 * w:.1f}", "sysDash": f"{3 * w:.1f} {w:.1f}", "dot": f"{w:.1f} {2 * w:.1f}", "sysDot": f"{w:.1f} {w:.1f}",
              "lgDash": f"{8 * w:.1f} {3 * w:.1f}", "dashDot": f"{4 * w:.1f} {3 * w:.1f} {w:.1f} {3 * w:.1f}"}.get(dash, "")
        head = (X(ln, "./a:headEnd/@type") or ["none"])[0] if ln is not None else "none"
        tail = (X(ln, "./a:tailEnd/@type") or ["none"])[0] if ln is not None else "none"
        return css_color(col), w, da, head, tail

    def image_uri(self, holder, part) -> str:
        rid = (X(holder, ".//a:blip/@r:embed") or [""])[0]
        if not rid:
            return ""
        try:
            ip = part.related_part(rid)
            ext = str(ip.partname).rsplit(".", 1)[-1].lower()
            if ext not in MIME:
                return ""
            return "data:%s;base64,%s" % (MIME[ext], base64.b64encode(ip.blob).decode("ascii"))
        except Exception:
            return ""

    # -- placeholders
    def ph_chain(self, sp):
        """[layout placeholder sp, master placeholder sp] matching this shape's <p:ph> (may be empty)."""
        ph = X1(sp, "./p:nvSpPr/p:nvPr/p:ph")
        if ph is None:
            return [], ""
        typ, idx = ph.get("type", "body" if ph.get("idx") else "body"), ph.get("idx")
        out = []
        lay = None
        for cand in X(self.layout._element, ".//p:sp[p:nvSpPr/p:nvPr/p:ph]"):
            cp = X1(cand, "./p:nvSpPr/p:nvPr/p:ph")
            if (idx is not None and cp.get("idx") == idx) or (idx is None and cp.get("type", "body") == typ):
                lay = cand
                break
        if lay is not None:
            out.append(lay)
            typ = X1(lay, "./p:nvSpPr/p:nvPr/p:ph").get("type", typ)
        mt = {"ctrTitle": "title", "subTitle": "body", "obj": "body"}.get(typ, typ)
        for cand in X(self.master._element, ".//p:sp[p:nvSpPr/p:nvPr/p:ph]"):
            if X1(cand, "./p:nvSpPr/p:nvPr/p:ph").get("type", "body") == mt:
                out.append(cand)
                break
        return out, typ

    def xfrm(self, el, chain=()):
        for cand in (el, *chain):
            xf = None
            for path in ("./p:spPr/a:xfrm", "./p:grpSpPr/a:xfrm", "./p:xfrm"):
                xf = X1(cand, path)
                if xf is not None:
                    break
            if xf is not None and X1(xf, "./a:off") is not None:
                off, ext = X1(xf, "./a:off"), X1(xf, "./a:ext")
                return (int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy")), int(xf.get("rot", "0")) / 60000,
                        xf.get("flipH") in ("1", "true"), xf.get("flipV") in ("1", "true"), xf)
        return None

    # -- text
    def text_defaults(self, sp, chain, typ, lvl: int):
        d = {"sz": 18.0, "color": None, "b": False, "algn": "l", "bullet": None, "font": ""}
        srcs = []
        ts = X1(self.master._element, "./p:txStyles")
        if chain or typ:
            key = "titleStyle" if typ in ("title", "ctrTitle") else ("bodyStyle" if typ in ("body", "subTitle", "obj") else "otherStyle")
            if ts is not None:
                srcs.append(X1(ts, f"./p:{key}/a:lvl{lvl}pPr"))
            for c in reversed(chain):
                srcs.append(X1(c, f"./p:txBody/a:lstStyle/a:lvl{lvl}pPr"))
        srcs.append(X1(sp, f"./p:txBody/a:lstStyle/a:lvl{lvl}pPr"))
        for s in srcs:
            if s is None:
                continue
            if s.get("algn"):
                d["algn"] = s.get("algn")
            if X1(s, "./a:buNone") is not None:
                d["bullet"] = None
            elif X(s, "./a:buChar/@char"):
                d["bullet"] = X(s, "./a:buChar/@char")[0]
            rp = X1(s, "./a:defRPr")
            if rp is not None:
                if rp.get("sz"):
                    d["sz"] = int(rp.get("sz")) / 100
                if rp.get("b"):
                    d["b"] = rp.get("b") in ("1", "true")
                c = color_of(X1(rp, "./a:solidFill"), self.th)
                if c:
                    d["color"] = c
                f = (X(rp, "./a:ea/@typeface") or X(rp, "./a:latin/@typeface") or [""])[0]
                if f:
                    d["font"] = f
        return d

    def font_css(self, name: str) -> str:
        name = {"+mj-lt": self.th.major, "+mn-lt": self.th.minor, "+mj-ea": self.th.major, "+mn-ea": self.th.minor}.get(name, name)
        return ("'%s'," % name.replace("'", "")) if name else ""

    def text_html(self, txbody, sp=None, chain=(), typ="", default_color=None, cell=False) -> tuple[str, str]:
        """(inner html, extra css for the holder) of an <p:txBody>/<a:txBody>."""
        if txbody is None:
            return "", ""
        bp = X1(txbody, "./a:bodyPr")
        bps = [bp] + [X1(c, "./p:txBody/a:bodyPr") for c in chain]

        def battr(name, dflt):
            for b in bps:
                if b is not None and b.get(name) is not None:
                    return b.get(name)
            return dflt
        ins = [int(battr(n, d)) * self.k for n, d in (("lIns", "91440"), ("tIns", "45720"), ("rIns", "91440"), ("bIns", "45720"))]
        anchor = battr("anchor", "t")
        scale = 1.0
        na = X1(bp, "./a:normAutofit") if bp is not None else None
        if na is not None and na.get("fontScale"):
            scale = int(na.get("fontScale")) / 100000
        wrap = battr("wrap", "square")
        out = []
        num = {}
        for p in X(txbody, "./a:p"):
            ppr = X1(p, "./a:pPr")
            lvl = int(ppr.get("lvl", "0")) + 1 if ppr is not None else 1
            d = self.text_defaults(sp, list(chain), typ, lvl) if sp is not None else {"sz": 18.0, "color": None, "b": False, "algn": "l", "bullet": None, "font": ""}
            algn = (ppr.get("algn") if ppr is not None and ppr.get("algn") else d["algn"])
            bullet = d["bullet"]
            if ppr is not None:
                if X1(ppr, "./a:buNone") is not None:
                    bullet = None
                elif X(ppr, "./a:buChar/@char"):
                    bullet = X(ppr, "./a:buChar/@char")[0]
                elif X1(ppr, "./a:buAutoNum") is not None:
                    num[lvl] = num.get(lvl, 0) + 1
                    bullet = f"{num[lvl]}."
            runs = []
            psz = None
            for r in p:
                tag = r.tag.split("}")[1]
                if tag == "br":
                    runs.append("<br>")
                    continue
                if tag not in ("r", "fld"):
                    continue
                rp = X1(r, "./a:rPr")
                sz = (int(rp.get("sz")) / 100 if rp is not None and rp.get("sz") else d["sz"]) * scale
                psz = max(psz or 0, sz)
                col = color_of(X1(rp, "./a:solidFill"), self.th) if rp is not None else None
                col = col or d["color"] or default_color
                bold = (rp.get("b") in ("1", "true")) if rp is not None and rp.get("b") else d["b"]
                ital = rp is not None and rp.get("i") in ("1", "true")
                und = rp is not None and rp.get("u") not in (None, "none")
                font = ((X(rp, "./a:ea/@typeface") or X(rp, "./a:latin/@typeface") or [""])[0] if rp is not None else "") or d["font"]
                hl = color_of(X1(rp, "./a:highlight"), self.th) if rp is not None else None
                st = "font-size:%.1fpx;color:%s;font-weight:%s;" % (sz * self.pt, css_color(col) if col else "#000", "700" if bold else "400")
                if ital:
                    st += "font-style:italic;"
                if und:
                    st += "text-decoration:underline;"
                if font:
                    st += "font-family:%s'Noto Sans KR','Malgun Gothic',sans-serif;" % self.font_css(font)
                if hl:
                    st += "background:%s;" % css_color(hl)
                txt = "".join(X(r, "./a:t/text()"))
                if tag == "fld" and r.get("type") == "slidenum" and self.no:
                    txt = str(self.no)  # PowerPoint fills this field in; the stored text is only a cache
                runs.append('<span style="%s">%s</span>' % (st, esc(txt).replace("\n", "<br>").replace("\x0b", "<br>")))
            if psz is None:
                ep = X1(p, "./a:endParaRPr")
                psz = (int(ep.get("sz")) / 100 if ep is not None and ep.get("sz") else d["sz"]) * scale
            ls = 1.2
            lsp = X(ppr, "./a:lnSpc/a:spcPct/@val") if ppr is not None else []
            if lsp:
                ls = 1.2 * int(lsp[0]) / 100000
            pst = "text-align:%s;line-height:%.2f;font-size:%.1fpx;" % ({"ctr": "center", "r": "right", "just": "justify"}.get(algn, "left"), ls, psz * self.pt)
            mar = (int(ppr.get("marL", "0")) if ppr is not None and ppr.get("marL") else (342900 * lvl if bullet and not cell else 0)) * self.k
            for tag_, key in (("spcBef", "margin-top"), ("spcAft", "margin-bottom")):
                v = X(ppr, f"./a:{tag_}/a:spcPts/@val") if ppr is not None else []
                if v:
                    pst += "%s:%.1fpx;" % (key, int(v[0]) / 100 * self.pt)
            if bullet and runs:
                pst += "padding-left:%.1fpx;text-indent:-%.1fpx;" % (max(mar, psz * self.pt), psz * self.pt)
                runs.insert(0, '<span style="display:inline-block;width:%.1fpx;text-indent:0;color:inherit">%s</span>' % (psz * self.pt, esc(bullet)))
            elif mar:
                pst += "padding-left:%.1fpx;" % mar
            out.append('<div style="%s">%s</div>' % (pst, "".join(runs) or "&nbsp;"))
        css = "padding:%.1fpx %.1fpx %.1fpx %.1fpx;justify-content:%s;" % (ins[1], ins[2], ins[3], ins[0], {"ctr": "center", "b": "flex-end"}.get(anchor, "flex-start"))
        if wrap == "none":
            css += "white-space:nowrap;"
        return "".join(out), css


# ---- geometry -----------------------------------------------------------------------------------------------------------
def _poly(pts) -> str:
    return "M" + " L".join("%.1f %.1f" % p for p in pts) + " Z"


def geom_path(prst: str, w: float, h: float, adj: dict) -> str | None:
    """SVG path for a preset shape in a w x h box (None -> plain rectangle via CSS)."""
    a = lambda n, d: adj.get(n, d) / 100000  # noqa: E731
    m = min(w, h)
    if prst in ("triangle", "isosTriangle"):
        return _poly([(w * a("adj", 50000), 0), (w, h), (0, h)])
    if prst == "rtTriangle":
        return _poly([(0, 0), (w, h), (0, h)])
    if prst == "diamond":
        return _poly([(w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2)])
    if prst == "parallelogram":
        o = m * a("adj", 25000)
        return _poly([(o, 0), (w, 0), (w - o, h), (0, h)])
    if prst == "trapezoid":
        o = m * a("adj", 25000)
        return _poly([(o, 0), (w - o, 0), (w, h), (0, h)])
    if prst == "hexagon":
        o = m * a("adj", 25000)
        return _poly([(o, 0), (w - o, 0), (w, h / 2), (w - o, h), (o, h), (0, h / 2)])
    if prst in ("homePlate", "pentagon") and prst == "homePlate":
        o = m * a("adj", 50000)
        return _poly([(0, 0), (w - o, 0), (w, h / 2), (w - o, h), (0, h)])
    if prst == "chevron":
        o = m * a("adj", 50000)
        return _poly([(0, 0), (w - o, 0), (w, h / 2), (w - o, h), (0, h), (o, h / 2)])
    if prst == "pentagon":
        return _poly([(w / 2, 0), (w, h * 0.38), (w * 0.81, h), (w * 0.19, h), (0, h * 0.38)])
    if prst in ("rightArrow", "leftArrow", "upArrow", "downArrow"):
        t, hd = a("adj1", 50000), a("adj2", 50000)
        if prst in ("rightArrow", "leftArrow"):
            o, y1, y2 = min(w, h * hd), h * (1 - t) / 2, h * (1 + t) / 2
            pts = [(0, y1), (w - o, y1), (w - o, 0), (w, h / 2), (w - o, h), (w - o, y2), (0, y2)]
            if prst == "leftArrow":
                pts = [(w - x, y) for x, y in pts]
        else:
            o, x1, x2 = min(h, w * hd), w * (1 - t) / 2, w * (1 + t) / 2
            pts = [(x1, 0), (x1, h - o), (0, h - o), (w / 2, h), (w, h - o), (x2, h - o), (x2, 0)]
            if prst == "upArrow":
                pts = [(x, h - y) for x, y in pts]
        return _poly(pts)
    if prst in ("star5", "star4", "star6", "star8"):
        n = int(prst[4:])
        pts = []
        for i in range(2 * n):
            r = 1 if i % 2 == 0 else 0.42
            t = math.pi * i / n - math.pi / 2
            pts.append((w / 2 + w / 2 * r * math.cos(t), h / 2 + h / 2 * r * math.sin(t)))
        return _poly(pts)
    if prst == "teardrop":
        return "M%.1f 0 L%.1f 0 L%.1f %.1f A%.1f %.1f 0 1 1 %.1f 0 Z" % (w / 2, w, w, h / 2, w / 2, h / 2, w / 2)
    if prst == "donut":
        t = m * a("adj", 25000)
        return ("M0 %.1f A%.1f %.1f 0 1 0 %.1f %.1f A%.1f %.1f 0 1 0 0 %.1f Z M%.1f %.1f A%.1f %.1f 0 1 1 %.1f %.1f A%.1f %.1f 0 1 1 %.1f %.1f Z"
                % (h / 2, w / 2, h / 2, w, h / 2, w / 2, h / 2, h / 2, t, h / 2, w / 2 - t, h / 2 - t, w - t, h / 2, w / 2 - t, h / 2 - t, t, h / 2))
    if prst in ("arc", "pie", "chord", "blockArc"):
        d1, d2 = (16200000, 0) if prst == "arc" else (0, 16200000)
        s, e = adj.get("adj1", d1) / 60000, adj.get("adj2", d2) / 60000
        sw = (e - s) % 360 or 360
        p0 = (w / 2 + w / 2 * math.cos(math.radians(s)), h / 2 + h / 2 * math.sin(math.radians(s)))
        p1 = (w / 2 + w / 2 * math.cos(math.radians(s + sw)), h / 2 + h / 2 * math.sin(math.radians(s + sw)))
        arc = "M%.1f %.1f A%.1f %.1f 0 %d 1 %.1f %.1f" % (p0[0], p0[1], w / 2, h / 2, 1 if sw > 180 else 0, p1[0], p1[1])
        return arc if prst == "arc" else arc + " L%.1f %.1f Z" % (w / 2, h / 2)
    if prst in ("plus", "mathPlus"):
        o = m * a("adj", 25000)
        return _poly([(o, 0), (w - o, 0), (w - o, o), (w, o), (w, h - o), (w - o, h - o), (w - o, h), (o, h), (o, h - o), (0, h - o), (0, o), (o, o)])
    if prst in ("wedgeRectCallout", "wedgeRoundRectCallout", "wedgeEllipseCallout", "cloud", "cloudCallout"):
        return None
    return None


def cust_path(cg, w: float, h: float) -> str:
    """<a:custGeom> -> SVG path scaled to the w x h box."""
    out = []
    for path in X(cg, "./a:pathLst/a:path"):
        pw, ph = float(path.get("w") or 0) or None, float(path.get("h") or 0) or None
        sx = (w / pw) if pw else None
        sy = (h / ph) if ph else None

        def pt(e):
            x, y = float(e.get("x", "0")), float(e.get("y", "0"))
            return (x * sx if sx else x, y * sy if sy else y)
        for cmd in path:
            tag = cmd.tag.split("}")[1]
            pts = [pt(e) for e in X(cmd, "./a:pt")]
            if tag == "moveTo" and pts:
                out.append("M%.1f %.1f" % pts[0])
            elif tag == "lnTo" and pts:
                out.append("L%.1f %.1f" % pts[0])
            elif tag == "cubicBezTo" and len(pts) == 3:
                out.append("C%.1f %.1f %.1f %.1f %.1f %.1f" % (*pts[0], *pts[1], *pts[2]))
            elif tag == "quadBezTo" and len(pts) == 2:
                out.append("Q%.1f %.1f %.1f %.1f" % (*pts[0], *pts[1]))
            elif tag == "close":
                out.append("Z")
    return " ".join(out)


def _marker(dr: Draw, color: str, kind: str, start: bool) -> str:
    mid = dr.uid("ar")
    if kind in ("oval", "diamond"):
        shape = '<circle cx="5" cy="5" r="3.2" fill="%s"/>' % color
    else:
        shape = '<path d="M1 1.5 L9 5 L1 8.5 Z" fill="%s"/>' % color
    dr.defs.append('<marker id="%s" viewBox="0 0 10 10" refX="%s" refY="5" markerWidth="4.2" markerHeight="4.2" orient="%s">%s</marker>'
                   % (mid, "7" if kind not in ("oval", "diamond") else "5", "auto-start-reverse" if start else "auto", shape))
    return mid


# ---- shapes -------------------------------------------------------------------------------------------------------------
def draw_shape(dr: Draw, sp, part, tf=None, master_layer=False) -> str:
    """One <p:sp> / <p:cxnSp> / <p:pic> / <p:graphicFrame> / <p:grpSp> -> html. tf maps child EMU coords inside groups."""
    tag = sp.tag.split("}")[1]
    tf = tf or (lambda x, y, w, h: (x, y, w, h))
    if tag == "grpSp":
        g = dr.xfrm(sp)
        inner_tf = tf
        if g:
            xf = g[7]
            co, ce = X1(xf, "./a:chOff"), X1(xf, "./a:chExt")
            if co is not None and ce is not None and int(ce.get("cx")) and int(ce.get("cy")):
                gx, gy, gw, gh = tf(g[0], g[1], g[2], g[3])
                cx0, cy0, cw, chh = int(co.get("x")), int(co.get("y")), int(ce.get("cx")), int(ce.get("cy"))
                inner_tf = lambda x, y, w, h: (gx + (x - cx0) * gw / cw, gy + (y - cy0) * gh / chh, w * gw / cw, h * gh / chh)  # noqa: E731
        return "".join(draw_shape(dr, ch, part, inner_tf, master_layer) for ch in sp if ch.tag.split("}")[1] in ("sp", "cxnSp", "pic", "graphicFrame", "grpSp"))
    chain, typ = (dr.ph_chain(sp) if tag == "sp" and part is dr.part else ([], ""))
    if master_layer and X1(sp, "./p:nvSpPr/p:nvPr/p:ph") is not None:
        return ""  # layout/master placeholders are prompts, not content
    g = dr.xfrm(sp, chain)
    if not g:
        return ""
    x, y, w, h = tf(g[0], g[1], g[2], g[3])
    rot, fh, fv = g[4], g[5], g[6]
    k = dr.k
    px, py, pw, ph_ = x * k, y * k, w * k, h * k
    st = "left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;" % (px, py, pw, ph_)
    if rot:
        st += "transform:rotate(%.2fdeg);" % rot
    flip = ("scale(%d,%d)" % (-1 if fh else 1, -1 if fv else 1)) if (fh or fv) else ""
    spPr = X1(sp, "./p:spPr")
    style = X1(sp, "./p:style")
    if tag == "graphicFrame":
        tbl = X1(sp, ".//a:tbl")
        if tbl is not None:
            return '<div class="sh" style="%s">%s</div>' % (st, table_html(dr, tbl, pw, ph_))
        cid = (X(sp, ".//c:chart/@r:id") or [""])[0]
        if cid:
            try:
                import pptx_chart
                return '<div class="sh" style="%s">%s</div>' % (st, pptx_chart.chart_svg(part.related_part(cid).blob, pw, ph_, dr))
            except Exception as exc:  # unknown chart kind: say so instead of leaving a hole
                return '<div class="sh ph" style="%s">차트 (%s)</div>' % (st, esc(str(exc)[:40]))
        return '<div class="sh ph" style="%s">개체</div>' % st
    if tag == "pic":
        uri = dr.image_uri(X1(sp, "./p:blipFill"), part)
        prst = (X(spPr, "./a:prstGeom/@prst") or ["rect"])[0]
        rad = "border-radius:50%;" if prst == "ellipse" else ("border-radius:%.1fpx;" % (min(pw, ph_) * 0.1) if prst == "roundRect" else "")
        if not uri:
            return '<div class="sh ph" style="%s%s">그림</div>' % (st, rad)
        sr = X1(sp, "./p:blipFill/a:srcRect")
        l, t, r, b = ((int(sr.get(n, "0")) / 100000 for n in ("l", "t", "r", "b")) if sr is not None else (0, 0, 0, 0))
        iw, ih = pw / max(0.05, 1 - l - r), ph_ / max(0.05, 1 - t - b)
        img = '<img src="%s" style="position:absolute;left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx">' % (uri, -l * iw, -t * ih, iw, ih)
        ln = dr.line_of(spPr, style)
        bd = "outline:%.1fpx solid %s;" % (ln[1], ln[0]) if ln else ""
        return '<div class="sh" style="%soverflow:hidden;%s%s">%s</div>' % (st, rad, bd, img)
    # sp / cxnSp
    prst = (X(spPr, "./a:prstGeom/@prst") or [""])[0]
    adj = {}
    for gd in X(spPr, "./a:prstGeom/a:avLst/a:gd"):
        try:
            adj[gd.get("name")] = int(gd.get("fmla", "val 0").split()[-1])
        except ValueError:
            pass
    is_txbox = X1(sp, "./p:nvSpPr/p:cNvSpPr[@txBox='1']") is not None
    fill = dr.fill_css(spPr, part, style=None if is_txbox else style)
    if fill is None and chain:
        for c in chain:
            fill = dr.fill_css(X1(c, "./p:spPr"), dr.layout.part)
            if fill is not None:
                break
    ln = dr.line_of(spPr, None if is_txbox else style)
    cg = X1(spPr, "./a:custGeom")
    is_line = tag == "cxnSp" or prst in ("line", "straightConnector1", "bentConnector2", "bentConnector3", "curvedConnector3")
    body = ""
    box_css = ""
    if is_line:
        if ln:
            col, lw, da, head, tail = ln
            m1 = ' marker-start="url(#%s)"' % _marker(dr, col, head, True) if head != "none" else ""
            m2 = ' marker-end="url(#%s)"' % _marker(dr, col, tail, False) if tail != "none" else ""
            if prst == "bentConnector3":
                mx = pw * adj.get("adj1", 50000) / 100000
                d = "M0 0 L%.1f 0 L%.1f %.1f L%.1f %.1f" % (mx, mx, ph_, pw, ph_)
            elif prst == "bentConnector2":
                d = "M0 0 L%.1f 0 L%.1f %.1f" % (pw, pw, ph_)
            else:
                d = "M0 0 L%.1f %.1f" % (pw, ph_)
            body = ('<svg class="g" width="%.1f" height="%.1f" style="overflow:visible;%s"><path d="%s" fill="none" stroke="%s" stroke-width="%.2f"%s%s%s stroke-linecap="round"/></svg>'
                    % (max(pw, 1), max(ph_, 1), ("transform:%s;" % flip) if flip else "", d, col, lw, ' stroke-dasharray="%s"' % da if da else "", m1, m2))
    else:
        path = cust_path(cg, pw, ph_) if cg is not None else geom_path(prst, pw, ph_, adj)
        img_fill = isinstance(fill, str) and fill.startswith("url(")
        grad = isinstance(fill, str) and fill.startswith("linear-gradient")
        if path:
            svg_fill = "none" if fill in (None, "none") or prst == "arc" else fill
            if grad or img_fill:  # gradients / pictures inside a non-rect shape: clip a filled div
                cid = dr.uid("cp")
                dr.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, path))
                body = '<div class="g" style="inset:0;background:%s;clip-path:url(#%s);%s"></div>' % (fill, cid, ("transform:%s;" % flip) if flip else "")
                svg_fill = "none"
            stroke = ' stroke="%s" stroke-width="%.2f"%s' % (ln[0], ln[1], ' stroke-dasharray="%s"' % ln[2] if ln[2] else "") if ln else ""
            body += ('<svg class="g" width="%.1f" height="%.1f" style="overflow:visible;%s"><path d="%s" fill="%s"%s stroke-linejoin="round"/></svg>'
                     % (max(pw, 1), max(ph_, 1), ("transform:%s;" % flip) if flip else "", path, svg_fill, stroke))
        else:
            if fill not in (None, "none"):
                box_css += "background:%s;" % fill
            if ln:
                box_css += "border:%.2fpx %s %s;" % (ln[1], "dashed" if ln[2] else "solid", ln[0])
            if prst in ("ellipse", "flowChartConnector"):
                box_css += "border-radius:50%;"
            elif prst in ("roundRect", "flowChartAlternateProcess", "wedgeRoundRectCallout", "round2SameRect", "snipRoundRect"):
                box_css += "border-radius:%.1fpx;" % (min(pw, ph_) * min(0.5, adj.get("adj", 16667) / 100000))
            elif prst in ("flowChartTerminator",):
                box_css += "border-radius:%.1fpx;" % (min(pw, ph_) / 2)
    tx = X1(sp, "./p:txBody")
    thtml, tcss = "", ""
    if tx is not None and "".join(X(tx, ".//a:t/text()")).strip():
        fr = X1(style, "./a:fontRef") if style is not None else None
        dcol = color_of(fr, dr.th) if fr is not None else None
        thtml, tcss = dr.text_html(tx, sp, chain, typ, dcol or (dr.th.scheme("tx1"), 1.0))
        thtml = '<div class="t" style="%s">%s</div>' % (tcss, thtml)
    if not (body or box_css or thtml):
        return ""
    return '<div class="sh" style="%s%s">%s%s</div>' % (st, box_css, body, thtml)


def table_html(dr: Draw, tbl, pw: float, ph: float) -> str:
    cols = [int(c.get("w")) for c in X(tbl, "./a:tblGrid/a:gridCol")]
    tot = sum(cols) or 1
    pr = X1(tbl, "./a:tblPr")
    first, band = (pr is not None and pr.get("firstRow") in ("1", "true")), (pr is not None and pr.get("bandRow") in ("1", "true"))
    styled = bool(X(pr, "./a:tableStyleId")) if pr is not None else False
    acc = dr.th.scheme("accent1") or "4472C4"
    rows = X(tbl, "./a:tr")
    hsum = sum(int(r.get("h", "0")) for r in rows) or 1
    out = ['<table style="width:100%%;height:%.1fpx;border-collapse:collapse;table-layout:fixed">' % ph, "<colgroup>"]
    out += ['<col style="width:%.2f%%">' % (c / tot * 100) for c in cols]
    out.append("</colgroup>")
    for ri, r in enumerate(rows):
        out.append('<tr style="height:%.1fpx">' % (int(r.get("h", "0")) / hsum * ph))
        for tc in X(r, "./a:tc"):
            if tc.get("hMerge") in ("1", "true") or tc.get("vMerge") in ("1", "true"):
                continue
            tcp = X1(tc, "./a:tcPr")
            fill = dr.fill_css(tcp, dr.part) if tcp is not None else None
            dcol = None
            if fill is None and styled:
                if first and ri == 0:
                    fill, dcol = "#" + acc, ("FFFFFF", 1.0)
                elif band:
                    fill = css_color(_mods(acc, [_Mod("tint", 40000 if (ri - (1 if first else 0)) % 2 == 0 else 20000)]))
            css = "background:%s;" % fill if fill not in (None, "none") else ""
            for side, name in (("L", "left"), ("R", "right"), ("T", "top"), ("B", "bottom")):
                lnel = X1(tcp, f"./a:ln{side}") if tcp is not None else None
                if lnel is not None and X1(lnel, "./a:noFill") is None:
                    c = color_of(X1(lnel, "./a:solidFill"), dr.th)
                    if c:
                        css += "border-%s:%.1fpx solid %s;" % (name, max(1, int(lnel.get("w", "12700")) * dr.k), css_color(c))
                elif lnel is None and styled:
                    css += "border-%s:1px solid #fff;" % name
            anchor = tcp.get("anchor", "t") if tcp is not None else "t"
            thtml, tcss = dr.text_html(X1(tc, "./a:txBody"), None, (), "", dcol or (dr.th.scheme("tx1"), 1.0), cell=True)
            if styled and first and ri == 0:
                thtml = "<b>%s</b>" % thtml
            css += "vertical-align:%s;" % {"ctr": "middle", "b": "bottom"}.get(anchor, "top")
            pad = [int(tcp.get(n, d)) * dr.k if tcp is not None else int(d) * dr.k for n, d in (("marT", "45720"), ("marR", "91440"), ("marB", "45720"), ("marL", "91440"))]
            css += "padding:%.1fpx %.1fpx %.1fpx %.1fpx;" % tuple(pad)
            span = (' colspan="%s"' % tc.get("gridSpan") if tc.get("gridSpan") else "") + (' rowspan="%s"' % tc.get("rowSpan") if tc.get("rowSpan") else "")
            out.append('<td%s style="%soverflow:hidden">%s</td>' % (span, css, thtml))
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


class _Mod:
    """Tiny stand-in for a colour-modifier element (tag + val)."""

    def __init__(self, name, val):
        self.tag = "{x}" + name
        self._v = str(val)

    def get(self, k, d=None):
        return self._v if k == "val" else d


def background(dr: Draw) -> str:
    for holder, part in ((dr.slide, dr.part), (dr.layout, dr.layout.part), (dr.master, dr.master.part)):
        bg = X1(holder._element, "./p:cSld/p:bg")
        if bg is None:
            continue
        f = dr.fill_css(X1(bg, "./p:bgPr"), part)
        if f not in (None, "none"):
            return f
        ref = X1(bg, "./p:bgRef")
        if ref is not None:
            c = color_of(ref, dr.th)
            if c:
                return css_color(c)
    return "#" + (dr.th.scheme("bg1") or "FFFFFF")


def slide_html(prs, slide, fonts_css: str = "", bad: set | None = None, slide_no: int = 0) -> str:
    """A full HTML document that draws one slide at 1600px wide."""
    dr = Draw(prs, slide)
    parts = []
    show_master = slide._element.get("showMasterSp", "1") not in ("0", "false") and dr.layout._element.get("showMasterSp", "1") not in ("0", "false")
    layers = ([(dr.master, True)] if show_master else []) + [(dr.layout, True), (slide, False)]
    for holder, is_master in layers:
        tree = X1(holder._element, "./p:cSld/p:spTree")
        if tree is None:
            continue
        for ch in tree:
            if ch.tag.split("}")[1] not in ("sp", "cxnSp", "pic", "graphicFrame", "grpSp"):
                continue
            try:
                h_ = draw_shape(dr, ch, holder.part, None, is_master)
            except Exception as exc:  # one odd shape must not kill the preview
                h_ = "<!-- skipped: %s -->" % esc(str(exc)[:80])
            if h_ and bad and not is_master:
                first = "".join(X(ch, ".//a:t/text()")).strip()[:20]
                if first and any(first.startswith(b[1][:20]) and b[0] == slide_no for b in bad if b[1]):
                    h_ = h_.replace('class="sh"', 'class="sh" data-over="1"', 1)
            parts.append(h_)
    hpx = STAGE * dr.H / dr.W
    css = (fonts_css + "html,body{margin:0;background:#222}"
           ".sl{position:relative;width:%dpx;height:%.1fpx;overflow:hidden;font-family:'Noto Sans KR','Malgun Gothic',sans-serif;word-break:keep-all;overflow-wrap:anywhere}"
           ".sh{position:absolute;box-sizing:border-box}.g{position:absolute;left:0;top:0}"
           ".t{position:absolute;inset:0;display:flex;flex-direction:column;box-sizing:border-box}"
           ".ph{display:flex;align-items:center;justify-content:center;background:#e9edf2;color:#667;border:2px dashed #9aa;font-size:22px}"
           "[data-over]{outline:3px solid #ff2d2d}td{box-sizing:border-box}" % (STAGE, hpx))
    return ('<!doctype html><meta charset=utf-8><style>%s</style><div class=sl style="background:%s"><svg width="0" height="0" style="position:absolute"><defs>%s</defs></svg>%s</div>'
            % (css, background(dr), "".join(dr.defs), "".join(parts)))


def fonts_css(skill_dir: Path) -> str:
    """@font-face for the bundled Noto fonts (so the preview matches decks that name them even when the PC lacks the font)."""
    out = []
    for base in (skill_dir / "shared" / "fonts", skill_dir.parent.parent / "shared" / "fonts"):
        if not base.exists():
            continue
        for f in sorted(base.glob("*.woff2")) + sorted(base.glob("*.ttf")) + sorted(base.glob("*.otf")):
            n = f.name.lower()
            fam = "Noto Serif KR" if "serif" in n else ("Noto Sans KR" if "noto" in n and "sans" in n else "")
            if not fam:
                continue
            wt = "700" if "bold" in n or "-700" in n or "black" in n else ("400" if "regular" in n or "-400" in n else "400 700" if "variable" in n or "vf" in n or "wght" in n else "")
            if wt:
                out.append("@font-face{font-family:'%s';src:url('%s');font-weight:%s}" % (fam, f.resolve().as_uri(), wt))
        break
    return "".join(out)


def leaf_boxes(prs, slide):
    """Yield (tag, element, x, y, w, h) in EMU for every drawable leaf of a slide (group transforms applied; placeholders get
    their inherited position). Used by pptx_fill.py to measure how full a slide looks."""
    dr = Draw(prs, slide)

    def walk(el, tf):
        tag = el.tag.split("}")[1]
        if tag == "grpSp":
            g = dr.xfrm(el)
            inner = tf
            if g:
                xf = g[7]
                co, ce = X1(xf, "./a:chOff"), X1(xf, "./a:chExt")
                if co is not None and ce is not None and int(ce.get("cx")) and int(ce.get("cy")):
                    gx, gy, gw, gh = tf(g[0], g[1], g[2], g[3])
                    cx0, cy0, cw, chh = int(co.get("x")), int(co.get("y")), int(ce.get("cx")), int(ce.get("cy"))
                    inner = lambda x, y, w, h: (gx + (x - cx0) * gw / cw, gy + (y - cy0) * gh / chh, w * gw / cw, h * gh / chh)  # noqa: E731
            for ch in el:
                if ch.tag.split("}")[1] in ("sp", "cxnSp", "pic", "graphicFrame", "grpSp"):
                    yield from walk(ch, inner)
            return
        chain, _ = dr.ph_chain(el) if tag == "sp" else ([], "")
        g = dr.xfrm(el, chain)
        if g:
            yield (tag, el) + tuple(tf(g[0], g[1], g[2], g[3]))
    tree = X1(slide._element, "./p:cSld/p:spTree")
    for ch in (tree if tree is not None else []):
        if ch.tag.split("}")[1] in ("sp", "cxnSp", "pic", "graphicFrame", "grpSp"):
            yield from walk(ch, lambda x, y, w, h: (x, y, w, h))
