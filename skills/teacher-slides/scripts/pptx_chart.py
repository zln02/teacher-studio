# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Native PowerPoint chart XML -> SVG (approximate preview): column / bar (clustered, stacked), line, area, pie, doughnut.

Reads the cached values in the chart part (c:cat / c:val), the series and point colours, title, legend and data-label flags.
Used by pptx_draw.py so chart slides no longer look empty in the approximate preview.
"""
from __future__ import annotations

import html
import math

from lxml import etree

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}

_XP = __import__("lxml.etree").etree._Element.xpath  # python-pptx overrides .xpath() without the namespaces argument


def X(el, path):
    return _XP(el, path, namespaces=NS) if el is not None else []


def X1(el, path):
    r = X(el, path)
    return r[0] if r else None


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def _pts(holder) -> list:
    """Cached points of a c:cat / c:val / c:tx element, in idx order."""
    cache = X1(holder, ".//c:strCache") if X1(holder, ".//c:strCache") is not None else X1(holder, ".//c:numCache")
    if cache is None:
        cache = X1(holder, ".//c:strLit") if X1(holder, ".//c:strLit") is not None else X1(holder, ".//c:numLit")
    if cache is None:
        return []
    n = int((X(cache, "./c:ptCount/@val") or ["0"])[0])
    vals = {int(p.get("idx")): (X(p, "./c:v/text()") or [""])[0] for p in X(cache, "./c:pt")}
    n = max(n, (max(vals) + 1) if vals else 0)
    return [vals.get(i, "") for i in range(n)]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _fmt(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}"
    return f"{v:,.1f}"


def _nice(vmax: float) -> tuple[float, float]:
    """(axis max, step) with 4-6 gridlines."""
    if vmax <= 0:
        return 1.0, 0.25
    raw = vmax / 5
    mag = 10 ** math.floor(math.log10(raw))
    step = next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw)
    return math.ceil(vmax / step - 1e-9) * step, step


def chart_svg(blob: bytes, w: float, h: float, dr) -> str:
    root = etree.fromstring(blob)
    th = dr.th
    from pptx_draw import color_of, css_color
    accents = [th.scheme(f"accent{i}") or "888888" for i in range(1, 7)]
    plot = X1(root, "//c:plotArea")
    if plot is None:
        raise ValueError("no plot area")
    fs = max(11.0, min(w, h) * 0.034)
    tx_el = X1(root, "//c:chartSpace/c:txPr//a:defRPr")
    tcol = css_color(color_of(X1(tx_el, "./a:solidFill"), th)) if tx_el is not None and X1(tx_el, "./a:solidFill") is not None else "#444"
    if tx_el is not None and tx_el.get("sz"):
        fs = max(10.0, int(tx_el.get("sz")) / 100 * dr.pt * 0.92)
    out = ['<svg width="%.0f" height="%.0f" viewBox="0 0 %.0f %.0f" style="font-family:inherit">' % (w, h, w, h)]
    top = 6.0
    title = "".join(X(root, "//c:chart/c:title//a:t/text()"))
    auto_del = (X(root, "//c:chart/c:autoTitleDeleted/@val") or ["0"])[0] in ("1", "true")
    series_all = []
    kinds = []
    for grp in plot:
        tag = grp.tag.split("}")[1]
        if not tag.endswith("Chart"):
            continue
        sers = []
        for s in X(grp, "./c:ser"):
            name = "".join(_pts(X1(s, "./c:tx"))) if X1(s, "./c:tx") is not None else ""
            cats = _pts(X1(s, "./c:cat")) if X1(s, "./c:cat") is not None else []
            vals = [_num(v) for v in (_pts(X1(s, "./c:val")) if X1(s, "./c:val") is not None else [])]
            fill = color_of(X1(s, "./c:spPr/a:solidFill"), th) or color_of(X1(s, "./c:spPr/a:ln/a:solidFill"), th)
            dpt = {}
            for d in X(s, "./c:dPt"):
                c = color_of(X1(d, "./c:spPr/a:solidFill"), th)
                if c:
                    dpt[int((X(d, "./c:idx/@val") or ["0"])[0])] = css_color(c)
            sers.append({"name": name, "cats": cats, "vals": vals, "color": css_color(fill) if fill else None, "dpt": dpt})
        dl = X1(grp, "./c:dLbls")
        show_val = bool(X(grp, ".//c:dLbls/c:showVal[@val='1']")) and not (dl is not None and X(dl, "./c:delete[@val='1']"))
        show_pct = bool(X(grp, ".//c:dLbls/c:showPercent[@val='1']"))
        kinds.append({"tag": tag, "sers": sers, "dir": (X(grp, "./c:barDir/@val") or ["col"])[0], "grouping": (X(grp, "./c:grouping/@val") or ["clustered"])[0],
                      "val": show_val, "pct": show_pct, "hole": int((X(grp, "./c:holeSize/@val") or ["50"])[0])})
        series_all += sers
    if not kinds:
        raise ValueError("unknown chart")
    k0 = kinds[0]
    if not title and not auto_del and len(series_all) == 1 and series_all[0]["name"]:
        title = series_all[0]["name"]
    if title:
        out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" font-weight="700" fill="%s">%s</text>' % (w / 2, top + fs * 1.2, fs * 1.15, tcol, esc(title)))
        top += fs * 2.0
    pie = k0["tag"] in ("pieChart", "doughnutChart", "pie3DChart")
    has_leg = X1(root, "//c:chart/c:legend") is not None
    leg_pos = (X(root, "//c:chart/c:legend/c:legendPos/@val") or ["r"])[0]
    leg_items = []
    if pie:
        s = k0["sers"][0] if k0["sers"] else {"cats": [], "vals": [], "dpt": {}}
        leg_items = [(s["cats"][i] if i < len(s["cats"]) else str(i + 1), s["dpt"].get(i) or "#" + accents[i % 6]) for i in range(len(s["vals"]))]
    else:
        for i, s in enumerate(series_all):
            s["color"] = s["color"] or "#" + accents[i % 6]
            leg_items.append((s["name"] or f"계열 {i + 1}", s["color"]))
    bottom = h - 6
    right = w - 8
    if has_leg and leg_items:
        if leg_pos in ("r", "tr", "l"):
            lw = min(w * 0.3, max(len(n) for n, _ in leg_items) * fs * 0.95 + fs * 2)
            for i, (n, c) in enumerate(leg_items):
                y = top + (h - top) / 2 - len(leg_items) * fs * 0.8 + i * fs * 1.6
                out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/><text x="%.1f" y="%.1f" font-size="%.1f" fill="%s">%s</text>'
                           % (w - lw, y, fs * 0.8, fs * 0.8, c, w - lw + fs * 1.1, y + fs * 0.75, fs * 0.9, tcol, esc(n)))
            right = w - lw - 10
        else:
            tw = sum(len(n) * fs * 0.95 + fs * 2.4 for n, _ in leg_items)
            x = max(4, (w - tw) / 2)
            y = (top + 2) if leg_pos == "t" else (h - fs * 1.4)
            for n, c in leg_items:
                out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/><text x="%.1f" y="%.1f" font-size="%.1f" fill="%s">%s</text>'
                           % (x, y, fs * 0.8, fs * 0.8, c, x + fs * 1.1, y + fs * 0.75, fs * 0.9, tcol, esc(n)))
                x += len(n) * fs * 0.95 + fs * 2.4
            if leg_pos == "t":
                top += fs * 1.8
            else:
                bottom -= fs * 1.9
    if pie:
        s = k0["sers"][0] if k0["sers"] else {"vals": []}
        tot = sum(v for v in s["vals"] if v > 0) or 1
        cx, cy = (8 + right) / 2, (top + bottom) / 2
        r = max(10, min(right - 8, bottom - top) / 2 - 4)
        ang = -math.pi / 2
        hole = r * k0["hole"] / 100 if k0["tag"] == "doughnutChart" else 0
        for i, v in enumerate(s["vals"]):
            if v <= 0:
                continue
            a2 = ang + 2 * math.pi * v / tot
            if v / tot > 0.999:
                a2 = ang + 2 * math.pi - 0.0001
            big = 1 if a2 - ang > math.pi else 0
            p = lambda rr, t: (cx + rr * math.cos(t), cy + rr * math.sin(t))  # noqa: E731
            d = "M%.1f %.1f A%.1f %.1f 0 %d 1 %.1f %.1f" % (*p(r, ang), r, r, big, *p(r, a2))
            d += (" L%.1f %.1f A%.1f %.1f 0 %d 0 %.1f %.1f Z" % (*p(hole, a2), hole, hole, big, *p(hole, ang))) if hole else (" L%.1f %.1f Z" % (cx, cy))
            out.append('<path d="%s" fill="%s" stroke="#fff" stroke-width="1.5"/>' % (d, leg_items[i][1]))
            if k0["val"] or k0["pct"]:
                mid = (ang + a2) / 2
                lx, ly = p((r + hole) / 2 if hole else r * 0.65, mid)
                lab = f"{v / tot * 100:.0f}%" if k0["pct"] else _fmt(v)
                out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" font-weight="700" fill="#fff" stroke="rgba(0,0,0,.35)" stroke-width=".6" paint-order="stroke">%s</text>'
                           % (lx, ly + fs * 0.35, fs, esc(lab)))
            ang = a2
        out.append("</svg>")
        return "".join(out)
    # category charts (bar / column / line / area), possibly combined
    cats = max((s["cats"] for s in series_all), key=len, default=[])
    n = max([len(cats)] + [len(s["vals"]) for s in series_all]) or 1
    cats = list(cats) + [""] * (n - len(cats))
    stacked = any(k["grouping"] in ("stacked", "percentStacked") for k in kinds if k["tag"].startswith("bar"))
    if stacked:
        bars = [s for k in kinds if k["tag"].startswith("bar") for s in k["sers"]]
        vmax = max([sum(s["vals"][i] for s in bars if i < len(s["vals"])) for i in range(n)] + [0])
    else:
        vmax = max([v for s in series_all for v in s["vals"]] + [0])
    amax, step = _nice(vmax * 1.05)
    horiz = k0["tag"].startswith("bar") and k0["dir"] == "bar"
    lab_w = max(len(_fmt(amax)) * fs * 0.62 + 8, fs * 2)
    if horiz:
        cat_w = min(w * 0.3, max(len(c) for c in cats) * fs * 0.95 + 10)
        x0, x1, y0, y1 = 8 + cat_w, right - fs * 2.5, top + 6, bottom - fs * 1.5
        v = 0.0
        while v <= amax + 1e-9:
            x = x0 + (x1 - x0) * v / amax
            out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#d5d9df" stroke-width="1"/><text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" fill="%s">%s</text>'
                       % (x, y0, x, y1, x, y1 + fs * 1.1, fs * 0.82, tcol, _fmt(v)))
            v += step
        bh = (y1 - y0) / n
        sers = k0["sers"]
        for i in range(n):
            yc = y0 + bh * (n - 1 - i) if False else y0 + bh * i
            out.append('<text x="%.1f" y="%.1f" text-anchor="end" font-size="%.1f" fill="%s">%s</text>' % (x0 - 6, yc + bh / 2 + fs * 0.35, fs * 0.9, tcol, esc(cats[i])))
            acc = 0.0
            for j, s in enumerate(sers):
                val = s["vals"][i] if i < len(s["vals"]) else 0
                col = s["dpt"].get(i) or s["color"]
                if stacked:
                    bx, bw_, by, bhh = x0 + (x1 - x0) * acc / amax, (x1 - x0) * val / amax, yc + bh * 0.18, bh * 0.64
                    acc += val
                else:
                    sub = bh * 0.7 / max(len(sers), 1)
                    bx, bw_, by, bhh = x0, (x1 - x0) * val / amax, yc + bh * 0.15 + sub * j, sub * 0.92
                out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (bx, by, max(bw_, 0), bhh, col))
                if k0["val"]:
                    out.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s">%s</text>' % (bx + bw_ + 4, by + bhh / 2 + fs * 0.32, fs * 0.85, tcol, _fmt(val)))
        out.append("</svg>")
        return "".join(out)
    x0, x1, y0, y1 = 8 + lab_w, right - 6, top + fs * 1.3, bottom - fs * 1.6
    v = 0.0
    while v <= amax + 1e-9:
        y = y1 - (y1 - y0) * v / amax
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#d5d9df" stroke-width="1"/><text x="%.1f" y="%.1f" text-anchor="end" font-size="%.1f" fill="%s">%s</text>'
                   % (x0, y, x1, y, x0 - 6, y + fs * 0.3, fs * 0.82, tcol, _fmt(v)))
        v += step
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#8a929c" stroke-width="1.2"/>' % (x0, y1, x1, y1))
    cw = (x1 - x0) / n
    for i in range(n):
        lab = cats[i]
        size = fs * 0.9 if len(lab) * fs * 0.95 <= cw else max(9.0, cw / max(len(lab), 1) / 0.95)
        out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" fill="%s">%s</text>' % (x0 + cw * (i + 0.5), y1 + fs * 1.2, size, tcol, esc(lab)))
    for kd in kinds:
        sers = kd["sers"]
        if kd["tag"].startswith("bar"):
            for i in range(n):
                acc = 0.0
                for j, s in enumerate(sers):
                    val = s["vals"][i] if i < len(s["vals"]) else 0
                    col = s["dpt"].get(i) or s["color"]
                    if stacked:
                        bw_, bx = cw * 0.56, x0 + cw * i + cw * 0.22
                        by, bhh = y1 - (y1 - y0) * (acc + val) / amax, (y1 - y0) * val / amax
                        acc += val
                    else:
                        sub = cw * 0.68 / max(len(sers), 1)
                        bw_, bx = sub * 0.9, x0 + cw * i + cw * 0.16 + sub * j
                        by, bhh = y1 - (y1 - y0) * val / amax, (y1 - y0) * val / amax
                    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (bx, by, bw_, max(bhh, 0), col))
                    if kd["val"]:
                        out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" fill="%s">%s</text>'
                                   % (bx + bw_ / 2, (by - 4) if not stacked else (by + bhh / 2 + fs * 0.3), fs * 0.82, tcol if not stacked else "#fff", _fmt(val)))
        elif kd["tag"] in ("lineChart", "areaChart", "scatterChart", "radarChart"):
            for s in sers:
                pts = [(x0 + cw * (i + 0.5), y1 - (y1 - y0) * (s["vals"][i] if i < len(s["vals"]) else 0) / amax) for i in range(min(n, len(s["vals"])))]
                if not pts:
                    continue
                if kd["tag"] == "areaChart":
                    out.append('<path d="M%.1f %.1f L%s L%.1f %.1f Z" fill="%s" opacity=".35"/>' % (pts[0][0], y1, " L".join("%.1f %.1f" % p for p in pts), pts[-1][0], y1, s["color"]))
                out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="3" stroke-linejoin="round"/>' % (" ".join("%.1f,%.1f" % p for p in pts), s["color"]))
                for i, p in enumerate(pts):
                    out.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s"/>' % (p[0], p[1], s["color"]))
                    if kd["val"]:
                        out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" fill="%s">%s</text>' % (p[0], p[1] - 9, fs * 0.82, tcol, _fmt(s["vals"][i])))
        else:
            out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%.1f" fill="%s">(%s)</text>' % ((x0 + x1) / 2, (y0 + y1) / 2, fs, tcol, esc(kd["tag"])))
    out.append("</svg>")
    return "".join(out)
