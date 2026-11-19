# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Our own HWPX preview: any .hwpx (ours or the user's) -> one A4 HTML page that approximates how 한글 lays it out
(paragraph alignment / indents / hanging marks, character size / bold / colour, tables with header fill, paragraph rules).
It is an approximation, not 한글 itself: say so when showing it. 1 HWPUNIT = 1/7200 inch -> px = v / 75.

    py hwpx_preview.py doc.hwpx --out doc.html
"""
from __future__ import annotations

import argparse
import html
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph", "hh": "http://www.hancom.co.kr/hwpml/2011/head",
      "hc": "http://www.hancom.co.kr/hwpml/2011/core", "hs": "http://www.hancom.co.kr/hwpml/2011/section"}
HP = "{%s}" % NS["hp"]
HUNIT = 75.0


def px(v) -> float:
    return float(v or 0) / HUNIT


def _header(xml: bytes) -> tuple[dict, dict, dict, dict]:
    root = ET.fromstring(xml)
    fonts = {}
    for ff in root.iter("{%s}fontface" % NS["hh"]):
        if ff.get("lang") == "HANGUL":
            for f in ff.findall("hh:font", NS):
                fonts[f.get("id")] = f.get("face")
    chars = {}
    for c in root.iter("{%s}charPr" % NS["hh"]):
        fr = c.find("hh:fontRef", NS)
        chars[c.get("id")] = {"pt": int(c.get("height", "1000")) / 100, "bold": c.find("hh:bold", NS) is not None,
                              "color": c.get("textColor", "#000000"), "font": fonts.get(fr.get("hangul") if fr is not None else "0", "")}
    bfs = {}
    for b in root.iter("{%s}borderFill" % NS["hh"]):
        bb = b.find("hh:bottomBorder", NS)
        top = b.find("hh:topBorder", NS)
        wb = b.find(".//hc:winBrush", NS)
        bfs[b.get("id")] = {"bottom": bb is not None and bb.get("type") != "NONE", "box": top is not None and top.get("type") != "NONE",
                            "width": (bb.get("width") if bb is not None else "0.1 mm"), "fill": (wb.get("faceColor") if wb is not None else None)}
    paras = {}
    for p in root.iter("{%s}paraPr" % NS["hh"]):
        al = p.find("hh:align", NS)
        case = p.find("hp:switch/hp:case/hh:margin", NS)
        mg = case if case is not None else p.find(".//hh:margin", NS)
        val = lambda tag: int((mg.find(f"hc:{tag}", NS).get("value") if mg is not None and mg.find(f"hc:{tag}", NS) is not None else 0))  # noqa: E731
        ls = p.find("hp:switch/hp:case/hh:lineSpacing", NS)
        ls = ls if ls is not None else p.find(".//hh:lineSpacing", NS)
        bd = p.find("hh:border", NS)
        paras[p.get("id")] = {"align": (al.get("horizontal") if al is not None else "JUSTIFY").lower(), "left": val("left"), "intent": val("intent"),
                              "prev": val("prev"), "next": val("next"), "line": int(ls.get("value", "160")) if ls is not None else 160,
                              "border": bd.get("borderFillIDRef") if bd is not None else None}
    return fonts, chars, paras, bfs


def render(path) -> str:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        header = z.read("Contents/header.xml")
        secs = sorted((n for n in names if re.match(r"Contents/section\d+\.xml$", n)), key=lambda n: int(re.findall(r"\d+", n)[-1]))
        sec_xml = [z.read(n) for n in secs]
    _, chars, paras, bfs = _header(header)
    PARAS.clear()
    PARAS.update(paras)
    out = []
    margin = {"left": 5669, "right": 5669, "top": 5669, "bottom": 4252}
    for xml in sec_xml:
        root = ET.fromstring(xml)
        mg = root.find(".//hp:pagePr/hp:margin", NS)
        if mg is not None:
            margin = {k: int(mg.get(k, v)) for k, v in margin.items()}
        for p in root.findall("hp:p", NS):
            out.append(_p(p, chars, paras, bfs))
    css = ("body{margin:0;background:#e9ecef;font-family:'Noto Serif KR','함초롬바탕','Batang',serif;color:#000}"
           f".page{{width:794px;min-height:1123px;margin:24px auto;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.18);box-sizing:border-box;"
           f"padding:{px(margin['top']):.0f}px {px(margin['right']):.0f}px {px(margin['bottom']):.0f}px {px(margin['left']):.0f}px}}"
           "p{margin:0;word-break:keep-all;overflow-wrap:break-word;white-space:pre-wrap}"
           "table{border-collapse:collapse;width:100%;margin:2px 0}td{vertical-align:middle;padding:3px 7px;word-break:keep-all}"
           ".note{font:12px sans-serif;color:#555;text-align:center;margin:8px}")
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>HWPX 미리보기</title>"
            f"<style>{css}</style></head><body><div class='note'>한글 문서 미리보기(근사치) - 실제 한글 화면과 줄바꿈이 조금 다를 수 있어요</div>"
            f"<div class='page'>{''.join(out)}</div></body></html>")


def _runs(p, chars) -> str:
    h = []
    for run in p.findall("hp:run", NS):
        c = chars.get(run.get("charPrIDRef"), {"pt": 10, "bold": False, "color": "#000000", "font": ""})
        style = f"font-size:{c['pt'] * 96 / 72:.1f}px;" + ("font-weight:700;" if c["bold"] else "") + (f"color:{c['color']};" if c["color"] not in ("#000000", "none") else "")
        if "돋움" in (c.get("font") or "") or "고딕" in (c.get("font") or ""):
            style += "font-family:'Noto Sans KR','함초롬돋움','Malgun Gothic',sans-serif;"
        for el in run:
            if el.tag == HP + "t":
                s = el.text or ""
                for sub in el:
                    s += "\n" if sub.tag.endswith("lineBreak") else ("\t" if sub.tag.endswith("tab") else "")
                    s += sub.tail or ""
                h.append(f'<span style="{style}">{html.escape(s)}</span>')
            elif el.tag == HP + "tbl":
                h.append(_tbl(el, chars))
    return "".join(h)


def _p(p, chars, paras, bfs) -> str:
    pp = paras.get(p.get("paraPrIDRef"), {"align": "justify", "left": 0, "intent": 0, "prev": 0, "next": 0, "line": 160, "border": None})
    st = (f"text-align:{ {'distribute': 'justify'}.get(pp['align'], pp['align']) };padding-left:{px(pp['left']):.1f}px;text-indent:{px(pp['intent']):.1f}px;"
          f"margin-top:{px(pp['prev']):.1f}px;margin-bottom:{px(pp['next']):.1f}px;line-height:{pp['line'] / 100:.2f};")
    bf = bfs.get(pp.get("border") or "", {})
    if bf.get("bottom") and not bf.get("box"):
        st += "border-bottom:2px solid #222;"
    inner = _runs(p, chars)
    if not re.sub(r"<[^>]+>", "", inner).strip() and "<table" not in inner:
        inner = "&nbsp;"
    return f'<p style="{st}">{inner}</p>'


def _tbl(t, chars) -> str:
    rows = []
    for tr in t.findall("hp:tr", NS):
        cells = []
        for tc in tr.findall("hp:tc", NS):
            span = tc.find("hp:cellSpan", NS)
            cs, rs = (span.get("colSpan", "1"), span.get("rowSpan", "1")) if span is not None else ("1", "1")
            sz = tc.find("hp:cellSz", NS)
            w = px(sz.get("width")) if sz is not None else 0
            inner = "".join(_p_simple(p, chars) for p in tc.findall("hp:subList/hp:p", NS))
            hdr = tc.get("header") == "1"
            bg = "background:#e8edf4;" if hdr else ""
            cells.append(f'<td colspan="{cs}" rowspan="{rs}" style="border:1px solid #333;width:{w:.0f}px;{bg}">{inner}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>" + "".join(rows) + "</table>"


PARAS: dict = {}


def _p_simple(p, chars) -> str:
    al = PARAS.get(p.get("paraPrIDRef"), {}).get("align", "left")
    al = {"distribute": "justify"}.get(al, al)
    return f'<p style="text-align:{al}">{_runs(p, chars) or "&nbsp;"}</p>'



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hwpx", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    out = a.out or a.hwpx.with_suffix(".preview.html")
    out.write_text(render(a.hwpx), encoding="utf-8")
    print(f"READY {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
