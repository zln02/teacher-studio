# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Block model -> 한글 HWPX file, standard library only (zipfile + string XML).

Base: assets/hwpx/Skeleton.hwpx (a blank HWPX from python-hwpx 6.12.0, Apache-2.0; LICENSE/NOTICE next to it). We keep its package
files and header, append our own character shapes (charPr), paragraph shapes (paraPr) and border fills, and write section0.xml.
Paragraph margins are written as Hancom does: the HwpUnitChar case holds the value, the default branch holds it doubled.
1pt = 100 HWPUNIT, 1mm = 283.465 HWPUNIT. A4 = 59528 x 84186.
"""
from __future__ import annotations

import re
import time
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import docmodel

HERE = Path(__file__).resolve().parent
SKELETON = HERE.parent / "assets" / "hwpx" / "Skeleton.hwpx"
MM = 283.465
PAGE_W, PAGE_H = 59528, 84186
MARGIN = {"left": 20, "right": 20, "top": 20, "bottom": 15, "header": 10, "footer": 10}  # mm (house default; 편람 has no official 기안문 margin)
TEXT_W = int(PAGE_W - (MARGIN["left"] + MARGIN["right"]) * MM)
FONT_ID = {"dotum": "0", "batang": "1"}  # skeleton fontfaces: 0 = 함초롬돋움, 1 = 함초롬바탕 (both ship with 한글)


def _char_w(ch: str, size_pt: float) -> float:
    """Approximate glyph width in HWPUNIT (Hangul ~ 1 em, latin/digits/punct ~ 0.5 em)."""
    em = size_pt * 100
    return em if ("가" <= ch <= "힣" or ch in "①②③④⑤⑥⑦⑧⑨⑩㉮㉯㉰㉱㉲㉳□○") else em * 0.5


def text_w(s: str, size_pt: float) -> int:
    return int(sum(_char_w(c, size_pt) for c in s))


class Header:
    """Collects charPr / paraPr / borderFill additions and patches header.xml."""

    def __init__(self, xml: str):
        self.xml = xml
        self.n_char = int(re.search(r'<hh:charProperties itemCnt="(\d+)"', xml).group(1))
        self.n_para = int(re.search(r'<hh:paraProperties itemCnt="(\d+)"', xml).group(1))
        self.n_bf = int(re.search(r'<hh:borderFills itemCnt="(\d+)"', xml).group(1))
        self.chars: dict = {}
        self.paras: dict = {}
        self.bfs: dict = {}
        self.new_chars: list[str] = []
        self.new_paras: list[str] = []
        self.new_bfs: list[str] = []

    def char(self, size: float, bold: bool = False, color: str = "#000000", font: str = "batang") -> str:
        key = (round(size * 100), bold, color.upper(), font)
        if key in self.chars:
            return self.chars[key]
        cid = str(self.n_char + len(self.new_chars))
        f = FONT_ID.get(font, "1")
        langs = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
        a = lambda v: " ".join(f'{l}="{v}"' for l in langs)  # noqa: E731
        self.new_chars.append(
            f'<hh:charPr id="{cid}" height="{key[0]}" textColor="{key[2]}" shadeColor="none" useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">'
            f'<hh:fontRef {a(f)}/><hh:ratio {a(100)}/><hh:spacing {a(0)}/><hh:relSz {a(100)}/><hh:offset {a(0)}/>'
            + ("<hh:bold/>" if bold else "")
            + '<hh:underline type="NONE" shape="SOLID" color="#000000"/><hh:strikeout shape="NONE" color="#000000"/><hh:outline type="NONE"/>'
              '<hh:shadow type="NONE" color="#C0C0C0" offsetX="10" offsetY="10"/></hh:charPr>')
        self.chars[key] = cid
        return cid

    def para(self, align: str = "JUSTIFY", left: int = 0, intent: int = 0, prev: int = 0, nxt: int = 0, line: int = 160, border: str = "2") -> str:
        key = (align, int(left), int(intent), int(prev), int(nxt), int(line), border)
        if key in self.paras:
            return self.paras[key]
        pid = str(self.n_para + len(self.new_paras))

        def margin(k):
            return (f'<hh:margin><hc:intent value="{intent * k}" unit="HWPUNIT"/><hc:left value="{left * k}" unit="HWPUNIT"/><hc:right value="0" unit="HWPUNIT"/>'
                    f'<hc:prev value="{prev * k}" unit="HWPUNIT"/><hc:next value="{nxt * k}" unit="HWPUNIT"/></hh:margin><hh:lineSpacing type="PERCENT" value="{line}" unit="HWPUNIT"/>')
        self.new_paras.append(
            f'<hh:paraPr id="{pid}" tabPrIDRef="0" condense="0" fontLineHeight="0" snapToGrid="1" suppressLineNumbers="0" checked="0" textDir="LTR">'
            f'<hh:align horizontal="{align}" vertical="BASELINE"/><hh:heading type="NONE" idRef="0" level="0"/>'
            '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD" widowOrphan="0" keepWithNext="0" keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/>'
            '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
            f'<hp:switch><hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">{margin(1)}</hp:case><hp:default>{margin(2)}</hp:default></hp:switch>'
            f'<hh:border borderFillIDRef="{border}" offsetLeft="0" offsetRight="0" offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/></hh:paraPr>')
        self.paras[key] = pid
        return pid

    def border_fill(self, solid: bool = True, fill: str | None = None, width: str = "0.12 mm", bottom_only: bool = False) -> str:
        key = (solid, fill, width, bottom_only)
        if key in self.bfs:
            return self.bfs[key]
        bid = str(self.n_bf + len(self.new_bfs) + 1)  # borderFill ids start at 1
        t = "SOLID" if solid else "NONE"

        def side(name, on=True):
            return f'<hh:{name} type="{t if on else "NONE"}" width="{width}" color="#000000"/>'
        sides = (side("leftBorder", not bottom_only) + side("rightBorder", not bottom_only) + side("topBorder", not bottom_only) + side("bottomBorder"))
        brush = f'<hc:fillBrush><hc:winBrush faceColor="{fill}" hatchColor="#999999" alpha="0"/></hc:fillBrush>' if fill else ""
        self.new_bfs.append(f'<hh:borderFill id="{bid}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
                            '<hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
                            f'{sides}<hh:diagonal type="NONE" width="0.1 mm" color="#000000"/>{brush}</hh:borderFill>')
        self.bfs[key] = bid
        return bid

    def render(self) -> str:
        x = self.xml
        if self.new_chars:
            x = x.replace("</hh:charProperties>", "".join(self.new_chars) + "</hh:charProperties>", 1)
            x = re.sub(r'<hh:charProperties itemCnt="\d+"', f'<hh:charProperties itemCnt="{self.n_char + len(self.new_chars)}"', x, count=1)
        if self.new_paras:
            x = x.replace("</hh:paraProperties>", "".join(self.new_paras) + "</hh:paraProperties>", 1)
            x = re.sub(r'<hh:paraProperties itemCnt="\d+"', f'<hh:paraProperties itemCnt="{self.n_para + len(self.new_paras)}"', x, count=1)
        if self.new_bfs:
            x = x.replace("</hh:borderFills>", "".join(self.new_bfs) + "</hh:borderFills>", 1)
            x = re.sub(r'<hh:borderFills itemCnt="\d+"', f'<hh:borderFills itemCnt="{self.n_bf + len(self.new_bfs)}"', x, count=1)
        return x


class Writer:
    def __init__(self, header_xml: str, font: str = "batang"):
        self.h = Header(header_xml)
        self.font = font
        self.pid = 1
        self.oid = int(time.time()) % 100000000
        self.parts: list[str] = []

    def _id(self) -> str:
        self.pid += 1
        return str(self.pid)

    def runs(self, text: str, size: float, bold: bool, color: str = "#000000") -> str:
        """**x** -> bold run."""
        out = []
        for j, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
            if part == "":
                continue
            cid = self.h.char(size, bold or j % 2 == 1, color, self.font)
            lines = part.split("\n")
            inner = '<hp:lineBreak/>'.join(escape(ln) for ln in lines)
            out.append(f'<hp:run charPrIDRef="{cid}"><hp:t>{inner}</hp:t></hp:run>')
        if not out:
            out.append(f'<hp:run charPrIDRef="{self.h.char(size, bold, color, self.font)}"><hp:t/></hp:run>')
        return "".join(out)

    def p(self, bl: dict) -> str:
        size, bold = docmodel.STYLES.get(bl.get("style", "body"), (12.5, False))
        align = {"left": "LEFT", "center": "CENTER", "right": "RIGHT", "justify": "JUSTIFY"}[bl.get("align", "left")]
        unit = size * 100  # 2타 = one Hangul character of the body size
        left = int(bl.get("indent", 0) * unit)
        hang = bl.get("hang", "")
        text = bl["text"]
        intent = 0
        if hang:
            hw = text_w(hang + " ", size)
            left += hw
            intent = -hw
            text = f"{hang} {text}"
        elif bl.get("hang_text"):
            hw = text_w(bl["hang_text"], size)
            left += hw
            intent = -hw
        prev = 600 if bl.get("space_before") else 0
        pid = self.h.para(align, left, intent, prev, 0, 160)
        return (f'<hp:p id="{self._id()}" paraPrIDRef="{pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                f'{self.runs(text, size, bold)}</hp:p>')

    def empty(self, size: float = 8) -> str:
        pid = self.h.para("LEFT", 0, 0, 0, 0, 100)
        return f'<hp:p id="{self._id()}" paraPrIDRef="{pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">{self.runs("", size, False)}</hp:p>'

    def rule(self) -> str:
        bf = self.h.border_fill(True, None, "0.4 mm", bottom_only=True)
        pid = self.h.para("LEFT", 0, 0, 0, 300, 100, border=bf)
        return f'<hp:p id="{self._id()}" paraPrIDRef="{pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">{self.runs("", 4, False)}</hp:p>'

    def cut(self) -> str:
        return self.p(docmodel.P("✂ - - - - - - - - - - - - - - - - (절 취 선) - - - - - - - - - - - - - - - -", "small", "center"))

    def cell(self, text: str, col: int, row: int, w: int, h: int, bf: str, style: str, align: str, header: bool = False) -> str:
        size, bold = docmodel.STYLES[style]
        pid = self.h.para(align, 0, 0, 0, 0, 140)
        paras = "".join(f'<hp:p id="{self._id()}" paraPrIDRef="{pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">{self.runs(ln, size, bold)}</hp:p>'
                        for ln in (text.split("\n") if text else [""]))
        return (f'<hp:tc name="" header="{1 if header else 0}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{bf}">'
                f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
                f'{paras}</hp:subList><hp:cellAddr colAddr="{col}" rowAddr="{row}"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
                f'<hp:cellSz width="{w}" height="{h}"/><hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')

    def table(self, bl: dict) -> str:
        kind = bl.get("kind", "grid")
        rows = ([bl["columns"]] if bl.get("columns") else []) + bl["rows"]
        ncol = max(len(r) for r in rows)
        widths = bl.get("widths") or [1 / ncol] * ncol
        tot = sum(widths)
        cw = [int(TEXT_W * w / tot) for w in widths]
        line = self.h.border_fill(True, None)
        head = self.h.border_fill(True, "#E8EDF4")
        thick = self.h.border_fill(True, None, "0.4 mm")
        trs = []
        for r, row in enumerate(rows):
            tcs = []
            for c in range(ncol):
                txt = row[c] if c < len(row) else ""
                is_head = bool(bl.get("columns")) and r == 0
                if kind == "box":
                    bf, style, al = (head, "thead", "CENTER") if r == 0 else (line, "body", "LEFT")
                elif kind == "titlebox":
                    bf, style, al = thick, "title", "CENTER"
                elif kind == "form":
                    bf, style, al = (head, "label", "CENTER") if c == 0 else (line, "body", "LEFT")
                else:
                    num = bool(re.match(r"^[\s+\-−]?[\d,.]+\s*\S{0,2}$", txt))
                    bf, style, al = (head, "thead", "CENTER") if is_head else (line, "table", "RIGHT" if num else ("CENTER" if c == 0 else "LEFT"))
                h = 2400 if kind != "titlebox" else 4200
                tcs.append(self.cell(txt, c, r, cw[c], h, bf, style, al, is_head))
            trs.append("<hp:tr>" + "".join(tcs) + "</hp:tr>")
        self.oid += 1
        total_h = 2400 * len(rows)
        tbl = (f'<hp:tbl id="{self.oid}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" '
               f'repeatHeader="{1 if bl.get("columns") else 0}" rowCnt="{len(rows)}" colCnt="{ncol}" cellSpacing="0" borderFillIDRef="{line}" noAdjust="0">'
               f'<hp:sz width="{sum(cw)}" widthRelTo="ABSOLUTE" height="{total_h}" heightRelTo="ABSOLUTE" protect="0"/>'
               '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
               '<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="510" right="510" top="141" bottom="141"/>'
               + "".join(trs) + "</hp:tbl>")
        pid = self.h.para("CENTER", 0, 0, 200, 200, 100)
        cid = self.h.char(10, False, "#000000", self.font)
        return f'<hp:p id="{self._id()}" paraPrIDRef="{pid}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{cid}">{tbl}<hp:t/></hp:run></hp:p>'

    def block(self, bl: dict) -> str:
        t = bl["t"]
        if t == "p":
            return self.p(bl)
        if t == "table":
            return self.table(bl)
        if t == "space":
            return self.empty()
        if t == "rule":
            return self.rule()
        if t == "cut":
            return self.cut()
        return ""


def _section(skel_sec: str, body: str) -> str:
    """Keep the skeleton's first paragraph (it carries secPr = page setup) with our margins, then our paragraphs."""
    m = {k: int(v * MM) for k, v in MARGIN.items()}
    sec = re.sub(r'<hp:margin header="\d+" footer="\d+" gutter="0" left="\d+" right="\d+" top="\d+" bottom="\d+"/>',
                 f'<hp:margin header="{m["header"]}" footer="{m["footer"]}" gutter="0" left="{m["left"]}" right="{m["right"]}" top="{m["top"]}" bottom="{m["bottom"]}"/>', skel_sec, count=1)
    sec = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", sec, count=1, flags=re.S)
    return sec.replace("</hs:sec>", body + "</hs:sec>", 1)


def write(model: dict, out: Path, title: str = "") -> Path:
    """Write an .hwpx. Returns the path."""
    with zipfile.ZipFile(SKELETON) as z:
        files = {i.filename: z.read(i.filename) for i in z.infolist()}
        order = [i.filename for i in z.infolist()]
    w = Writer(files["Contents/header.xml"].decode("utf-8"), model.get("meta", {}).get("font", "batang"))
    body = "".join(w.block(b) for b in model["blocks"])
    files["Contents/section0.xml"] = _section(files["Contents/section0.xml"].decode("utf-8"), body).encode("utf-8")
    files["Contents/header.xml"] = w.h.render().encode("utf-8")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    hpf = files["Contents/content.hpf"].decode("utf-8")
    hpf = re.sub(r"<opf:title/>|<opf:title>.*?</opf:title>", f"<opf:title>{escape(title or model['meta'].get('title', ''))}</opf:title>", hpf, count=1)
    hpf = re.sub(r'(<opf:meta name="(?:creator|lastsaveby)" content="text">)[^<]*', r"\1Teacher Studio", hpf)
    hpf = re.sub(r'(<opf:meta name="(?:CreatedDate|ModifiedDate)" content="text">)[^<]*', rf"\g<1>{now}", hpf)
    hpf = re.sub(r'(<opf:meta name="date" content="text">)[^<]*', r"\1", hpf)
    files["Contents/content.hpf"] = hpf.encode("utf-8")
    files["Preview/PrvText.txt"] = "\r\n".join(docmodel.plain_lines(model))[:1000].encode("utf-8")  # HWPX preview text is UTF-8
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    save(files, order, out)
    return out


def save(files: dict, order: list, out: Path) -> None:
    """HWPX/OCF rule: `mimetype` first and STORED (uncompressed); the rest deflated."""
    with zipfile.ZipFile(out, "w") as z:
        names = ["mimetype"] + [n for n in order if n != "mimetype"] + [n for n in files if n not in order and n != "mimetype"]
        for n in names:
            if n not in files:
                continue
            ct = zipfile.ZIP_STORED if n == "mimetype" else zipfile.ZIP_DEFLATED
            z.writestr(zipfile.ZipInfo(n, date_time=time.localtime()[:6]), files[n], compress_type=ct)
