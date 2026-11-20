# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""`panel` slide: one claim shown with two to four pieces of evidence on the same slide (the way a hand-made report slide is built).

    {"type":"panel","title":"연수 이수율이 목표를 넘었다","takeaway":"이수율 92.5 %, 목표 90 % 초과 달성",
     "blocks":[{"kind":"kpis","items":[{"value":"92.5","unit":"%","caption":"연수 이수율 (37/40명)"}, ...]},
               {"kind":"chart","chart":"bar","labels":[..],"series":[{"name":"..","data":[..]}]},
               {"kind":"list","title":"남은 과제","items":["..",".."]}]}

block kinds
  kpis     items 2-4 [{value, unit, caption}]                     number cards
  cards    items 2-6 [{title, text} | {title, items: [..]}]       headed cards (numbered unless "numbered": false)
  list     title (optional), items 2-6                            a headed bullet list
  chart    chart ("bar" | "line" | "pie" | "doughnut"), labels, series, unit
  table    columns 2-6, rows 1-7, highlight
  note     text, label (optional)                                 one highlighted sentence (rule, formula, caution)
  flow     items 2-6 [str | {title, text}]                        boxes joined by arrows (a process, a cause chain)
  tree     root, children 2-5 [str | {title, items | text}]       one box over several (an organisation, a classification)
  diagram  shapes (same as the `diagram` slide: 100 x 60 canvas)  a drawn figure
Every block may carry "title" (a small heading). "layout": "rows" | "cols" | "side" overrides the automatic arrangement:
wide kinds (kpis, flow, note, tree) take a full row; the others share a row (side by side).
"takeaway" (any panel) = the conclusion in a band at the bottom.
The same regions (inches on the 13.333 x 7.5 slide) drive the .pptx and the web slide (x 144 = stage px).
"""
from __future__ import annotations

import json
import math

from deck_kit import T, box, esc, plain, rect, rich

KINDS = ("kpis", "cards", "list", "chart", "table", "note", "flow", "tree", "diagram")
ALIAS = {"numbers": "kpis", "stats": "kpis", "bignumbers": "kpis", "kpi": "kpis", "bullets": "list", "callout": "note", "text": "note", "steps": "flow",
         "process": "flow", "org": "tree", "hierarchy": "tree", "figure": "diagram", "card": "cards", "graph": "chart"}
WIDE = ("kpis", "flow", "note", "tree")
BIG = ("chart", "table", "diagram", "tree")
CHART_KINDS = ("bar", "line", "pie", "doughnut")


def kind_of(b: dict) -> str:
    k = str(b.get("kind") or b.get("type") or "").lower()
    return ALIAS.get(k, k)


def chart_kind(b: dict) -> str:
    v = str(b.get("chart") or b.get("kind_of") or b.get("chart_kind") or "bar").lower()
    return v if v in CHART_KINDS else "bar"


def as_chart(b: dict) -> dict:
    """A chart block in the shape the chart drawers expect."""
    return {"kind": chart_kind(b), "labels": b.get("labels") or [], "series": b.get("series") or [], "unit": b.get("unit", ""), "title": b.get("title", "")}


def _item(x) -> dict:
    return x if isinstance(x, dict) else {"title": str(x)}


def texts(it: dict) -> list[str]:
    """Every visible string of a panel (for length caps, placeholder and tone checks)."""
    out = [str(it.get("takeaway") or "")]
    for b in it.get("blocks") or []:
        if not isinstance(b, dict):
            continue
        out.append(str(b.get("title") or ""))
        out += [str(b.get(k) or "") for k in ("text", "root", "label")]
        for x in (b.get("items") or []) + (b.get("children") or []):
            if isinstance(x, dict):
                out += [str(x.get(k) or "") for k in ("value", "unit", "caption", "title", "text")] + [str(y) for y in x.get("items") or []]
            else:
                out.append(str(x))
        out += [str(c) for c in b.get("columns") or []] + [str(c) for r in b.get("rows") or [] if isinstance(r, list) for c in r]
        out += [str(c) for c in b.get("labels") or []]
        out += [str(sh.get("text") or "") for sh in b.get("shapes") or [] if isinstance(sh, dict)]
    return [t for t in out if t]


def check(i: int, it: dict, cap_total: int = 330) -> list[str]:
    e: list[str] = []
    bl = it.get("blocks")
    if not isinstance(bl, list) or not 1 <= len(bl) <= 4:
        return [f"slide {i} panel.blocks: {len(bl) if isinstance(bl, list) else 0} blocks -> use 2-4 (kinds: {', '.join(KINDS)})"]
    if len(bl) == 1 and not it.get("takeaway"):
        e.append(f"slide {i} panel: one block is a plain slide -> add a second block or a \"takeaway\"")
    L = lambda v: len(plain(str(v or "")))  # noqa: E731
    for j, b in enumerate(bl):
        where = f"slide {i} panel.blocks[{j}]"
        if not isinstance(b, dict) or kind_of(b) not in KINDS:
            e.append(f"{where}: kind '{b.get('kind') if isinstance(b, dict) else b}' -> one of {', '.join(KINDS)}")
            continue
        k = kind_of(b)
        b["kind"] = k
        if L(b.get("title")) > 28:
            e.append(f"{where} {k}.title: <= 28 chars")
        its = b.get("items") or []
        if k == "kpis":
            if not 2 <= len(its) <= 4 or any(not isinstance(x, dict) or x.get("value") in (None, "") for x in its):
                e.append(f"{where} kpis.items: 2-4 of {{value, unit, caption}}")
            elif any(L(str(x.get("value")) + str(x.get("unit", ""))) > 10 or L(x.get("caption")) > 44 for x in its):
                e.append(f"{where} kpis: value+unit <= 10 chars, caption <= 44")
        elif k == "cards":
            its = b["items"] = [_item(x) for x in its]
            if not 2 <= len(its) <= 6:
                e.append(f"{where} cards.items: 2-6 of {{title, text}}")
            for x in its:
                if not x.get("title") or L(x["title"]) > 24 or L(x.get("text")) > 80 or len(x.get("items") or []) > 4 or any(L(y) > 40 for y in x.get("items") or []):
                    e.append(f"{where} cards: title (required) <= 24, text <= 80, or items <= 4 of <= 40 chars ('{plain(str(x.get('title', '')))[:10]}')")
                    break
        elif k == "list":
            if not 2 <= len(its) <= 6 or any(L(x) > 56 for x in its):
                e.append(f"{where} list.items: 2-6 lines of <= 56 chars")
        elif k == "chart":
            lb, se = b.get("labels") or [], b.get("series") or []
            if not lb or not se or len(lb) > 8 or any(not isinstance(s_, dict) or len(s_.get("data") or []) != len(lb) for s_ in se):
                e.append(f"{where} chart: labels (<= 8) and series [{{name, data}}] with one number per label; chart: bar | line | pie | doughnut")
        elif k == "table":
            cols, rows = b.get("columns") or [], b.get("rows") or []
            if not 2 <= len(cols) <= 6 or not 1 <= len(rows) <= 7 or any(not isinstance(r, list) or len(r) != len(cols) for r in rows):
                e.append(f"{where} table: columns 2-6, rows 1-7, every row as long as the columns")
            elif any(L(c) > 30 for r in rows for c in r) or any(L(c) > 14 for c in cols):
                e.append(f"{where} table: cells <= 30 chars, headers <= 14")
        elif k == "note":
            if not b.get("text") or L(b["text"]) > 120:
                e.append(f"{where} note.text: required, <= 120 chars")
        elif k == "flow":
            its = b["items"] = [_item(x) for x in its]
            if not 2 <= len(its) <= 6 or any(not x.get("title") or L(x["title"]) > 18 or L(x.get("text")) > 44 for x in its):
                e.append(f"{where} flow.items: 2-6 of {{title <= 18, text <= 44}}")
        elif k == "tree":
            ch = b["children"] = [_item(x) for x in (b.get("children") or its)]
            if not b.get("root") or L(b["root"]) > 26 or not 2 <= len(ch) <= 5:
                e.append(f"{where} tree: root (<= 26 chars) and children 2-5")
            elif any(not x.get("title") or L(x["title"]) > 18 or L(x.get("text")) > 44 or len(x.get("items") or []) > 3 or any(L(y) > 30 for y in x.get("items") or []) for x in ch):
                e.append(f"{where} tree.children: title <= 18, items <= 3 of <= 30 chars (or text <= 44)")
        elif k == "diagram":
            import deck_diagram
            e += deck_diagram.check(i, {**b, "points": []})
    kinds = [kind_of(b) for b in bl if isinstance(b, dict)]
    if sum(1 for k in kinds if k in BIG) > 2:
        e.append(f"slide {i} panel: at most two of chart / table / diagram / tree on one slide -> move one to its own slide")
    if not e:  # does every block get the room it needs to be read? (the same regions the slide will use)
        for b, _, _, w, h in regions(bl, it.get("layout"), 0.8, 1.75, 11.7, 4.1 if it.get("takeaway") else 4.95):
            k = b["kind"]
            hh = h - (0.44 if b.get("title") and k not in ("list", "note") else 0)
            need_h = {"table": 0.4 * (len(b.get("rows") or []) + 1), "chart": 1.9, "diagram": 2.2, "kpis": 1.0, "flow": 0.8, "note": 0.5,
                      "tree": 2.0 if any(_body(x) for x in b.get("children") or []) else 1.3,
                      "list": 0.36 * len(b.get("items") or []) + (0.5 if b.get("title") else 0.1)}.get(k, 0)
            if k == "cards":
                cols, rows = _grid(len(b["items"]), w, hh, 2.3)
                need_h = rows * (1.25 if any(len(x.get("items") or []) >= 2 for x in b["items"]) else 0.85)
            need_w = {"chart": 3.8, "diagram": 3.6, "table": 0.95 * len(b.get("columns") or [])}.get(k, 0)
            if hh < need_h - 0.05 or w < need_w - 0.05:
                e.append(f"slide {i} panel: the {k} block gets {w:.1f} x {hh:.1f} in but needs about {max(need_w, 1):.1f} x {need_h:.1f} to be read from the back row "
                         f"-> move one block to its own slide, shorten it, or drop the takeaway (a panel holds one claim, not everything)")
                break
    total = sum(len(plain(t)) for t in texts(it)) + len(plain(str(it.get("title", ""))))
    cap = int(cap_total * 1.7)
    if not e and total > cap:
        e.append(f"slide {i} panel: {total} chars of text > {cap} -> fewer or shorter blocks (it must still read from the back row)")
    return e


# ---- geometry (inches) ---------------------------------------------------------------------------------------------------
def _weight(b: dict) -> float:
    k = b["kind"]
    if k == "table":
        return 0.9 + 0.32 * (len(b.get("rows") or []) + 1)
    if k == "cards":
        deep = any(len(_item(x).get("items") or []) >= 2 or len(plain(str(_item(x).get("text", "")))) > 34 for x in b.get("items") or [])
        return 1.9 if deep else 1.5
    if k == "list":
        return 0.7 + 0.3 * len(b.get("items") or [])
    return {"chart": 2.6, "diagram": 2.8, "tree": 2.4}.get(k, 1.5)


def _fixed(b: dict) -> float | None:
    """Preferred height of the kinds that should not grow with the slide."""
    k = b["kind"]
    if k == "note":
        return 0.78 if len(plain(str(b.get("text", "")))) <= 46 else 1.12
    if k == "kpis":
        return 1.75
    if k == "flow":
        return 1.75 if any(_item(x).get("text") for x in b.get("items") or []) else 1.05
    return None


def regions(blocks: list, layout: str | None, X: float, Y: float, W: float, H: float, gap: float = 0.24) -> list[tuple]:
    """[(block, x, y, w, h)] in inches."""
    bl = [b for b in blocks if isinstance(b, dict)]
    n = len(bl)
    lay = str(layout or "").lower()
    if lay == "side" or (not lay and n == 3 and not any(b["kind"] in WIDE for b in bl) and bl[0]["kind"] in BIG):
        lw = (W - gap) * (0.6 if bl[0]["kind"] in BIG else 0.5)
        out = [(bl[0], X, Y, lw, H)]
        rest = bl[1:]
        tw = sum(_weight(b) for b in rest) or 1
        y = Y
        for b in rest:
            h = (H - gap * (len(rest) - 1)) * _weight(b) / tw
            out.append((b, X + lw + gap, y, W - lw - gap, h))
            y += h + gap
        return out
    if lay == "rows":
        rows = [[b] for b in bl]
    elif lay == "cols":
        rows = [bl]
    elif n == 4 and not any(b["kind"] in WIDE for b in bl):
        rows = [bl[:2], bl[2:]]
    else:
        rows, cur = [], []
        for b in bl:
            if b["kind"] in WIDE:
                if cur:
                    rows.append(cur)
                    cur = []
                rows.append([b])
            else:
                cur.append(b)
                if len(cur) == 3:
                    rows.append(cur)
                    cur = []
        if cur:
            rows.append(cur)
    fixed = [(_fixed(r[0]) if len(r) == 1 else None) for r in rows]
    if any(b["kind"] in BIG for r in rows for b in r):  # number cards beside a chart / table / figure stay a strip: the figure needs the height
        fixed = [(min(f, 1.3) if f is not None and r[0]["kind"] == "kpis" else f) for f, r in zip(fixed, rows)]
    free = [i for i, f in enumerate(fixed) if f is None]
    room = H - gap * (len(rows) - 1)
    hs = [0.0] * len(rows)
    if free:
        fx = sum(f for f in fixed if f is not None)
        if fx > room * 0.6:  # too many fixed rows: squeeze them
            sc = room * 0.6 / fx
            fixed = [f * sc if f is not None else None for f in fixed]
            fx = room * 0.6
        tw = sum(max(_weight(b) for b in rows[i]) for i in free)
        for i, f in enumerate(fixed):
            hs[i] = f if f is not None else (room - fx) * max(_weight(b) for b in rows[i]) / tw
    else:  # only fixed kinds: share the whole height in proportion
        fx = sum(fixed)
        hs = [room * f / fx for f in fixed]
    out = []
    y = Y
    for r, h in zip(rows, hs):
        ws = [(1.35 if b["kind"] in BIG and len(r) > 1 and not all(x["kind"] in BIG for x in r) else 1.0) for b in r]
        tw = sum(ws)
        x = X
        for b, w_ in zip(r, ws):
            w = (W - gap * (len(r) - 1)) * w_ / tw
            out.append((b, x, y, w, h))
            x += w + gap
        y += h + gap
    return out


def _grid(n: int, w: float, h: float, min_w: float) -> tuple[int, int]:
    """(cols, rows) for n cards in a w x h region."""
    if w / n >= min_w:
        return n, 1
    for cols in (3, 2):
        if n > cols and w / cols >= min_w and n % cols != 1:
            return cols, math.ceil(n / cols)
    if n >= 4 and w / 2 >= min_w:
        return 2, math.ceil(n / 2)
    return 1, n


def _body(x: dict) -> str:
    if x.get("items"):
        return "\n".join("• " + str(y) for y in x["items"])
    return str(x.get("text") or "")


# ---- .pptx ---------------------------------------------------------------------------------------------------------------
_LO = [12.0]  # smallest body size inside a panel (a class deck asks for more: set by draw_pptx)


def _fit(texts, hi: float, w: float, h: float, spacing: float = 1.2, lo: float | None = None) -> float:
    """One common size for sibling boxes (w x h inches): as big as `hi`, shrunk until the longest text fits (never below `lo`)."""
    import pptx_fit as pf
    lo = lo or _LO[0]
    s = hi
    for t in texts:
        if not str(t or "").strip():
            continue
        s = min(s, pf.fit_size(plain(str(t)).split("\n"), s, (w - 0.16) * 72, (h - 0.08) * 72, spacing, floor=lo / max(s, lo), min_pt=lo)[0])
    return max(lo, s)


def draw_pptx(K, s, it: dict, X: float, Y: float, W: float, H: float) -> None:
    """K: helpers from deck_pptx (tbox, rect, card, line, chart, table, diagram, badge, icon, picks, C, z, OVAL)."""
    C, z = K.C, K.z
    _LO[0] = getattr(K, "lo", 14.0)
    edge = getattr(K, "edge", None) or (lambda s_, x_, y_, w_, h_, c_, top=False: setattr(K.rect(s_, x_, y_, w_ if top else 0.1, 0.08 if top else h_, c_, round_=False), "name", "accent"))
    for b, x, y, w, h in regions(it["blocks"], it.get("layout"), X, Y, W, H):
        k = b["kind"]
        if b.get("title") and k not in ("list", "note"):
            K.tbox(s, x, y, w, 0.42, b["title"], max(16, 15 * z), C["emc"], True, anchor="m")
            y += 0.48
            h -= 0.48
        g = 0.2
        if k == "kpis":
            its = b["items"]
            n = len(its)
            horiz = w / n >= 1.8
            cw, ch = ((w - g * (n - 1)) / n, h) if horiz else (w, (h - g * (n - 1)) / n)
            for i, m in enumerate(its):
                cx, cy = (x + i * (cw + g), y) if horiz else (x, y + i * (ch + g))
                K.card(s, cx, cy, cw, ch)
                edge(s, cx, cy, cw, ch, K.tone(i), top=True)
                val = f"{plain(str(m.get('value', '')))}{m.get('unit', '')}"
                if ch >= 1.25:
                    vs = max(24, min(44, ch * 72 * 0.3, (cw - 0.3) * 72 / max(2.2, 0.62 * len(val))))
                    K.tbox(s, cx + 0.1, cy + 0.12, cw - 0.2, ch * 0.44, val, vs, C["emcc"], True, "c", "m", "disp")
                    K.tbox(s, cx + 0.1, cy + 0.12 + ch * 0.44, cw - 0.2, ch * 0.56 - 0.2, m.get("caption", ""),
                           _fit([x_.get("caption", "") for x_ in its], 17 * z, cw - 0.2, ch * 0.56 - 0.2, 1.1), C["ct"], align="c", emc=C["emcc"], spacing=1.1)
                else:
                    K.tbox(s, cx + 0.1, cy, cw * 0.4, ch, val, max(20, min(32, ch * 72 * 0.42)), C["emcc"], True, "c", "m", "disp")
                    K.tbox(s, cx + cw * 0.42, cy, cw * 0.56, ch, m.get("caption", ""), max(_LO[0], 14 * z), C["ct"], anchor="m", emc=C["emcc"])
        elif k == "cards":
            its = b["items"]
            n = len(its)
            cols, rows = _grid(n, w, h, 2.3)
            cw, ch = (w - g * (cols - 1)) / cols, (h - g * (rows - 1)) / rows
            numbered = b.get("numbered", True) is not False
            ics = K.picks([plain(m["title"]) for m in its], [m.get("icon") for m in its] if any(m.get("icon") for m in its) else None) if hasattr(K, "picks") else []
            THIN = 1.8  # below this a card is one text box (heading line + detail), not a heading over a body
            tw_ = cw - (0.95 if numbered else 0.4)
            import pptx_fit as _pf
            th = 0.56  # a card heading that needs two lines at a readable size gets them (the body starts lower)
            if ch >= THIN and any(_pf.lines_for(plain(m["title"]), max(_LO[0], 17 * z), (cw - (1.13 if numbered else 0.4) - 0.16) * 72) > 1 for m in its):
                th = 0.92
            fb = (_fit([_body(m) for m in its], 24 * z, cw - 0.44, ch - 0.4 - th, 1.22) if ch >= THIN else
                  _fit([plain(m["title"]) + "\n" + _body(m).replace("\n", "  ") for m in its], 18 * z, tw_, ch - 0.08, 1.15))
            ft = _fit([m["title"] for m in its], min(21 * z, fb + 3), cw - (1.13 if numbered else 0.4), th, 1.1)
            for i, m in enumerate(its):
                cx, cy = x + (i % cols) * (cw + g), y + (i // cols) * (ch + g)
                K.card(s, cx, cy, cw, ch)
                tx0 = cx + 0.2
                body = _body(m)
                thin = ch < THIN
                head = not numbered and not thin and bool(body)
                tone = K.tone(i)  # neighbours alternate between the main and the accent colour
                if thin:
                    edge(s, cx, cy, cw, ch, tone)
                elif head:
                    hd = K.rect(s, cx, cy, cw, 0.62, tone)
                    ink_ = C["bt"] if tone == C["pr"] else K.ink(tone)
                    K.tbox(s, cx, cy, cw, 0.62, m["title"], ft, ink_, True, "c", "m", "disp", emc=ink_, shape=hd)
                    K.tbox(s, cx + 0.22, cy + 0.76, cw - 0.44, ch - 0.88, body, fb, C["ct"], emc=C["emcc"], spacing=1.22)
                    continue
                else:
                    edge(s, cx, cy, cw, ch, tone, top=True)
                if numbered:
                    bd = 0.56 if (thin and ch < 0.9) else 0.62
                    by = cy + (ch / 2 - bd / 2 if thin else 0.2)
                    K.badge(s, cx + 0.2, by, bd, tone, i + 1, ics[i] if ics else None)
                    tx0 = cx + 0.2 + bd + 0.16
                if thin or not body:
                    line = f"**{plain(m['title'])}**" + (("\n" if ch >= 0.95 else "  ") + body.replace("\n", "  ") if body else "")
                    K.tbox(s, tx0, cy + 0.04, cx + cw - tx0 - 0.15, ch - 0.08, line, fb if thin else ft, C["ct"], anchor="m", emc=C["emcc"], spacing=1.15)
                else:
                    K.tbox(s, tx0, cy + 0.18, cx + cw - tx0 - 0.15, th, m["title"], ft, C["ct"], True, anchor="m", name="disp", emc=C["emcc"], spacing=1.1)
                    K.tbox(s, cx + 0.22, cy + 0.28 + th, cw - 0.44, ch - 0.4 - th, body, fb, C["ct"], emc=C["emcc"], spacing=1.22)
        elif k == "list":
            K.card(s, x, y, w, h)
            edge(s, x, y, w, h, C["pr"])
            yy, hh = y + 0.12, h - 0.24
            if b.get("title"):
                K.tbox(s, x + 0.3, yy, w - 0.45, 0.46, b["title"], 17 * z, C["emcc"], True, anchor="m", name="disp", emc=C["emcc"])
                yy += 0.52
                hh -= 0.52
            n = len(b["items"])
            sp = 1.5 if n <= 3 else (1.35 if n == 4 else 1.2)
            body = "\n".join("• " + str(t) for t in b["items"])
            K.tbox(s, x + 0.3, yy, w - 0.45, hh, body, _fit([body], 22 * z, w - 0.45, hh, sp), C["ct"], anchor="m" if not b.get("title") else "t", emc=C["emcc"], spacing=sp)
        elif k == "chart":
            K.chart(s, as_chart(b), x, y, w, h, 15 if w < 7.5 else 16)
        elif k == "table":
            nr = len(b["rows"]) + 1
            K.table(s, b["columns"], b["rows"], x, y, w, min(h, 0.74 * nr), (18 if nr <= 5 else 16) if h / nr >= 0.46 else 16, b.get("highlight"))
        elif k == "note":
            K.rect(s, x, y, w, h, C["bg2"], round_=False).name = "panel"
            K.rect(s, x, y, 0.12, h, C["pr"], round_=False).name = "accent"
            tx0 = x + 0.35
            if b.get("label"):
                lw = min(2.8, 0.55 + 0.23 * len(plain(str(b["label"]))))
                lab = K.rect(s, x + 0.32, y + h / 2 - 0.22, lw, 0.44, C["pr"])
                K.tbox(s, x + 0.32, y + h / 2 - 0.22, lw, 0.44, b["label"], 15, C["bt"], True, "c", "m", emc=C["bt"], shape=lab)
                tx0 = x + 0.5 + lw
            K.tbox(s, tx0, y + 0.04, x + w - tx0 - 0.2, h - 0.08, b["text"], _fit([b["text"]], 19 * z, x + w - tx0 - 0.2, h - 0.08), C["tx"], True, anchor="m")
        elif k == "flow":
            its = b["items"]
            n = len(its)
            ag = 0.42
            horiz = (w - ag * (n - 1)) / n >= 1.45
            bw, bh = ((w - ag * (n - 1)) / n, h) if horiz else (w, (h - ag * (n - 1)) / n)
            for i, m in enumerate(its):
                bx, by = (x + i * (bw + ag), y) if horiz else (x, y + i * (bh + ag))
                tn = K.tone(1) if (i == n - 1 and n >= 3) else C["pr"]  # the last box (the result) takes the accent colour
                ink_ = C["bt"] if tn == C["pr"] else K.ink(tn)
                if m.get("text") and horiz and bh >= 1.3:
                    K.card(s, bx, by, bw, bh)
                    hd = K.rect(s, bx, by, bw, 0.56, tn)
                    K.tbox(s, bx, by, bw, 0.56, m["title"], 16 * z, ink_, True, "c", "m", "disp", emc=ink_, shape=hd)
                    K.tbox(s, bx + 0.12, by + 0.62, bw - 0.24, bh - 0.7, m["text"], _fit([x_.get("text", "") for x_ in its], 17 * z, bw - 0.24, bh - 0.7), C["ct"], align="c", anchor="m", emc=C["emcc"])
                else:
                    hd = K.rect(s, bx, by, bw, bh, tn)
                    txt = plain(m["title"]) + (("\n" if horiz else "  ") + plain(m["text"]) if m.get("text") else "")
                    K.tbox(s, bx, by, bw, bh, txt, 16 * z, ink_, True, "c", "m", emc=ink_, shape=hd)
                if i < n - 1:
                    if horiz:
                        K.line(s, bx + bw + 0.07, by + bh / 2, bx + bw + ag - 0.07, by + bh / 2, C["mu"], 2.5, True)
                    else:
                        K.line(s, bx + bw / 2, by + bh + 0.07, bx + bw / 2, by + bh + ag - 0.07, C["mu"], 2.5, True)
        elif k == "tree":
            ch_ = b["children"]
            n = len(ch_)
            rw, rh = min(w * 0.46, 4.6), 0.6
            root = K.rect(s, x + (w - rw) / 2, y, rw, rh, C["pr"])
            K.tbox(s, x + (w - rw) / 2, y, rw, rh, b["root"], 17 * z, C["bt"], True, "c", "m", "disp", emc=C["bt"], shape=root)
            cw = (w - g * (n - 1)) / n
            ymid, ytop = y + rh + 0.24, y + rh + 0.48
            K.line(s, x + w / 2, y + rh, x + w / 2, ymid, C["mu"], 2)
            K.line(s, x + cw / 2, ymid, x + w - cw / 2, ymid, C["mu"], 2)
            deep = any(_body(m) for m in ch_)
            fb = _fit([_body(m) for m in ch_], 19 * z, cw - 0.24, max(0.4, y + h - ytop - 0.56 - 0.12), 1.3)
            for i, m in enumerate(ch_):
                cx = x + i * (cw + g)
                K.line(s, cx + cw / 2, ymid, cx + cw / 2, ytop, C["mu"], 2)
                hh = 0.56 if deep else min(1.0, y + h - ytop)
                tn = K.tone(i + 1)
                hd = K.rect(s, cx, ytop, cw, hh, tn)
                ink = K.ink(tn)
                K.tbox(s, cx, ytop, cw, hh, m["title"], 15 * z, ink, True, "c", "m", "disp", emc=ink, shape=hd)
                if deep and y + h - ytop - hh > 0.5:
                    K.card(s, cx, ytop + hh, cw, y + h - ytop - hh)
                    K.tbox(s, cx + 0.12, ytop + hh + 0.06, cw - 0.24, y + h - ytop - hh - 0.12, _body(m), fb, C["ct"], anchor="m", emc=C["emcc"], spacing=1.3)
        elif k == "diagram":
            cw = min(w, h / 0.6)
            K.diagram(s, b, x + (w - cw) / 2, y + (h - cw * 0.6) / 2, cw)


# ---- web slide ----------------------------------------------------------------------------------------------------------
PX = 144.0
CSS = """
.pnl-arrow{color:var(--mu);display:flex;align-items:center;justify-content:center}.pnl-arrow svg{width:100%;height:100%}
.pnl-node{background:var(--pr);border-radius:calc(var(--rad)*.6)}.pnl-node2{background:var(--ac);border-radius:calc(var(--rad)*.6)}
.pnl-note{background:var(--bg2)}.pnl-ln{background:var(--mu)}
.pnl-tk{background:var(--pr);border-radius:calc(var(--rad)*.4)}
"""
_ARROW_H = '<svg viewBox="0 0 40 24" aria-hidden="true"><path d="M2 12H34M25 4l10 8-10 8" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
_ARROW_V = '<svg viewBox="0 0 24 40" aria-hidden="true"><path d="M12 2V34M4 25l8 10 8-10" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def takeaway_html(ctx, text: str, y: float = 870, h: float = 96) -> str:
    return rect(120, y, 1680, h, "pnl-tk") + T(ctx, text, 150, y + 4, 1620, h - 8, 40, ctx.floor, cls="p on-b st", va="m", align="center")


def web_html(ctx, it: dict, X: float, Y: float, W: float, H: float) -> str:
    """Same regions as the .pptx, in stage px (1 in = 144 px)."""
    fl = ctx.floor
    hh_: list[str] = []
    A = hh_.append
    for b, x, y, w, h in regions(it["blocks"], it.get("layout"), X, Y, W, H):
        x, y, w, h = x * PX, y * PX, w * PX, h * PX
        k = b["kind"]
        if b.get("title") and k not in ("list", "note"):
            A(T(ctx, b["title"], x, y, w, 56, 32, fl, cls="p acc st", va="m"))
            y += 64
            h -= 64
        g = 28
        if k == "kpis":
            its = b["items"]
            n = len(its)
            horiz = w / n >= 260
            cw, ch = ((w - g * (n - 1)) / n, h) if horiz else (w, (h - g * (n - 1)) / n)
            for i, m in enumerate(its):
                cx, cy = (x + i * (cw + g), y) if horiz else (x, y + i * (ch + g))
                val = f'{esc(plain(str(m.get("value", ""))))}<span class="unit">{esc(m.get("unit", ""))}</span>'
                vs = int(max(44, min(88, ch * 0.34, (cw - 40) / max(2.2, 0.62 * len(plain(str(m.get("value", ""))) + str(m.get("unit", "")))))))
                A(rect(cx, cy, cw, ch, "cd") + rect(cx, cy, cw, 10, "bar"))
                A(box(cx + 12, cy + 18, cw - 24, ch * 0.5, f'<div class="tx" style="text-align:center">{val}</div>', "big acc va-m", f"font-size:{vs}px;line-height:1.1"))
                A(T(ctx, m.get("caption", ""), cx + 16, cy + 18 + ch * 0.5, cw - 32, ch * 0.5 - 30, 34, fl, cls="p ct", va="t", align="center"))
        elif k == "cards":
            its = b["items"]
            n = len(its)
            cols, rows = _grid(n, w / PX, h / PX, 2.3)
            cw, ch = (w - g * (cols - 1)) / cols, (h - g * (rows - 1)) / rows
            numbered = b.get("numbered", True) is not False
            for i, m in enumerate(its):
                cx, cy = x + (i % cols) * (cw + g), y + (i // cols) * (ch + g)
                body = _body(m)
                thin = ch < 260
                if not numbered and not thin and body:
                    A(rect(cx, cy, cw, ch, "cd") + rect(cx, cy, cw, 90, "pnl-node2" if (n == 2 and i == 1) else "pnl-node"))
                    ink = "" if not (n == 2 and i == 1) else f"color:{__import__('deck_diagram').ink_on(ctx.dz['colors']['ac'])};"
                    A(T(ctx, m["title"], cx + 10, cy, cw - 20, 90, 34, fl, cls="p st" + ("" if ink else " on-b"), va="m", align="center", extra=ink))
                    A(T(ctx, body, cx + 30, cy + 110, cw - 60, ch - 128, 42, fl, cls="p ct", va="t", lh=1.3))
                    continue
                A(rect(cx, cy, cw, ch, "cd") + (rect(cx, cy, 12, ch, "bar") if thin else rect(cx, cy, cw, 10, "bar")))
                tx0 = cx + 30
                if numbered:
                    by = cy + (ch / 2 - 32 if thin else 34)
                    A(f'<div class="bx disc" style="left:{cx + 28:.0f}px;top:{by:.0f}px;width:64px;height:64px;font-size:{max(fl, 28)}px">{i + 1}</div>')
                    tx0 = cx + 110
                if thin or not body:
                    A(T(ctx, f"**{plain(m['title'])}**" + ("\n" + body.replace("\n", "  ") if body else ""), tx0, cy + 6, cx + cw - tx0 - 20, ch - 12, 38, fl, cls="p ct", va="m", lh=1.25))
                else:
                    A(T(ctx, m["title"], tx0, cy + 26, cx + cw - tx0 - 20, 82, 36, fl, cls="h st ct", va="m", lh=1.15))
                    A(T(ctx, body, cx + 30, cy + 122, cw - 60, ch - 140, 42, fl, cls="p ct", va="t", lh=1.3))
        elif k == "list":
            A(rect(x, y, w, h, "cd") + rect(x, y, 12, h, "bar"))
            yy, hh = y + 16, h - 32
            if b.get("title"):
                A(T(ctx, b["title"], x + 44, yy, w - 64, 66, 36, fl, cls="h st ct", va="m"))
                yy += 74
                hh -= 74
            A(T(ctx, "\n".join("• " + str(t) for t in b["items"]), x + 44, yy, w - 64, hh, 44, fl, cls="p ct", va="m" if not b.get("title") else "t", lh=1.45))
        elif k == "chart":
            cfg = esc(json.dumps({"kind": chart_kind(b), "labels": b["labels"], "series": b["series"], "unit": b.get("unit", "")}, ensure_ascii=False))
            A(f'<div class="bx cd chartbox" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px"><canvas data-cfg="{cfg}" width="{w - 48:.0f}" height="{h - 48:.0f}"></canvas></div>')
        elif k == "table":
            cols, rows = b["columns"], b["rows"]
            nr = len(rows) + 1
            rh = min(92, h / nr)
            size = max(fl, min(32, int(rh * 0.4)))
            hi = b.get("highlight")
            head = "".join(f"<th>{rich(c)}</th>" for c in cols)
            body = "".join(f'<tr style="height:{rh:.0f}px">' + "".join(f'<td class="{"hi" if hi == j else ""}">{rich(v)}</td>' for j, v in enumerate(r)) + "</tr>" for r in rows)
            A(box(x, y, w, rh * nr, f'<table class="gtbl" style="font-size:{size}px;line-height:1.2"><thead><tr style="height:{rh:.0f}px">{head}</tr></thead><tbody>{body}</tbody></table>', "tblwrap"))
        elif k == "note":
            A(rect(x, y, w, h, "pnl-note") + rect(x, y, 16, h, "bar"))
            tx0 = x + 50
            if b.get("label"):
                lw = min(380, 80 + 30 * len(plain(str(b["label"]))))
                A(box(x + 46, y + h / 2 - 32, lw, 64, f'<div class="tx" style="font-size:{max(fl, 26)}px;text-align:center">{esc(b["label"])}</div>', "gtab"))
                tx0 = x + 70 + lw
            A(T(ctx, b["text"], tx0, y + 6, x + w - tx0 - 30, h - 12, 36, fl, cls="p st", va="m", lh=1.3))
        elif k == "flow":
            its = b["items"]
            n = len(its)
            ag = 60
            horiz = (w - ag * (n - 1)) / n >= 208
            bw, bh = ((w - ag * (n - 1)) / n, h) if horiz else (w, (h - ag * (n - 1)) / n)
            for i, m in enumerate(its):
                bx, by = (x + i * (bw + ag), y) if horiz else (x, y + i * (bh + ag))
                if m.get("text") and horiz and bh >= 188:
                    A(rect(bx, by, bw, bh, "cd") + rect(bx, by, bw, 80, "pnl-node"))
                    A(T(ctx, m["title"], bx + 8, by, bw - 16, 80, 32, fl, cls="p on-b st", va="m", align="center"))
                    A(T(ctx, m["text"], bx + 16, by + 88, bw - 32, bh - 100, 28, fl, cls="p ct", va="m", align="center", lh=1.3))
                else:
                    A(rect(bx, by, bw, bh, "pnl-node"))
                    A(T(ctx, plain(m["title"]) + ("\n" + plain(m["text"]) if m.get("text") else ""), bx + 8, by + 4, bw - 16, bh - 8, 32, fl, cls="p on-b st", va="m", align="center", lh=1.25))
                if i < n - 1:
                    if horiz:
                        A(box(bx + bw + 8, by + bh / 2 - 16, ag - 16, 32, _ARROW_H, "pnl-arrow"))
                    else:
                        A(box(bx + bw / 2 - 16, by + bh + 8, 32, ag - 16, _ARROW_V, "pnl-arrow"))
        elif k == "tree":
            ch_ = b["children"]
            n = len(ch_)
            rw, rh = min(w * 0.46, 660), 86
            A(rect(x + (w - rw) / 2, y, rw, rh, "pnl-node") + T(ctx, b["root"], x + (w - rw) / 2 + 8, y, rw - 16, rh, 34, fl, cls="p on-b st", va="m", align="center"))
            cw = (w - g * (n - 1)) / n
            ymid, ytop = y + rh + 34, y + rh + 68
            A(rect(x + w / 2 - 2, y + rh, 4, 34, "pnl-ln") + rect(x + cw / 2, ymid - 2, w - cw, 4, "pnl-ln"))
            deep = any(_body(m) for m in ch_)
            for i, m in enumerate(ch_):
                cx = x + i * (cw + g)
                hh = 80 if deep else min(144, y + h - ytop)
                A(rect(cx + cw / 2 - 2, ymid, 4, 34, "pnl-ln") + rect(cx, ytop, cw, hh, "pnl-node2"))
                A(T(ctx, m["title"], cx + 6, ytop, cw - 12, hh, 30, fl, cls="p st", va="m", align="center", extra=f"color:{__import__('deck_diagram').ink_on(ctx.dz['colors']['ac'])};"))
                if deep and y + h - ytop - hh > 70:
                    A(rect(cx, ytop + hh, cw, y + h - ytop - hh, "cd"))
                    A(T(ctx, _body(m), cx + 16, ytop + hh + 8, cw - 32, y + h - ytop - hh - 16, 38, fl, cls="p ct", va="m", lh=1.3))
        elif k == "diagram":
            import deck_diagram
            cw = min(w, h / 0.6)
            A(rect(x + (w - cw) / 2, y + (h - cw * 0.6) / 2, cw, cw * 0.6, "cd"))
            A(box(x + (w - cw) / 2, y + (h - cw * 0.6) / 2, cw, cw * 0.6,
                  deck_diagram.svg({**b, "points": []}, ctx.dz["colors"], int(cw), int(cw * 0.6), fl, f"pd{ctx.idx}{int(x)}{int(y)}"), "dgm"))
    return "".join(hh_)
