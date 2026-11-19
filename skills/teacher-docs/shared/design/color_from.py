#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Take a palette from the user's OWN material (logo, photo, PPT/Word theme, 한글 file, website CSS) and map it onto our design tokens.

This is a MEANS to honour what the user already has (template-first rule), not our own design: the user's brand colours stay, only lightness is
nudged (hue kept) so text is readable. Output is tokens-compatible JSON: {"colors": {bg1,bg2,text,card,cardText,cardBorder,primary,btnText,accent,good,bad}, ...}.

    python3 color_from.py logo.png                      # print palette JSON
    python3 color_from.py app.css premium.css tokens.css --out my-palette.json   # several files: a site whose colours live in more than one place
    python3 color_from.py theme.pptx --out my-palette.json [--dark] [--save-default]
    python3 design.py --palette-from my-palette.json    # or spec: "design": {"palette_from": "my-palette.json"}   ("saved" = the saved default)

Sources (by extension):
  .png                      decoded with the stdlib (no install); 8-bit, non-interlaced
  .jpg .jpeg .gif .bmp .webp  need Pillow (shared/tools/ensure.py pillow --yes, with the teacher's consent); a clear message is printed otherwise
  .pptx .potx .ppsx .docx .dotx .xlsx  theme XML (ppt|word|xl/theme/theme1.xml: accent1..6, dk2, lt2) read with zipfile + xml
  .hwpx                     colours found in Contents/*.xml (textColor, faceColor, border colour...). Coverage is limited: most documents are black/white.
  .css .html .htm .svg      colour frequencies (#rgb, #rrggbb, rgb()), CSS variables named primary/brand/accent get a boost

A website's own CSS variables win where they exist: names like --good/--success/--ok/--mint -> correct colour, --bad/--error/--danger/--red -> wrong colour,
--ink/--text -> text, --border/--line -> card border, --bg/--paper/--surface -> background. They are kept (hue and chroma) and only moved in lightness until they are readable,
clearly different from each other for colour-blind eyes (color_check.py) and never muddy (chroma >= 0.12). The accent also comes back unchanged as accentDeco for
decoration only (dots, stars), because the readable accent has to be darker.

--save-default stores the result as the user's default palette in ~/.teacher-studio/prefs.json (only when asked). Nothing is installed or sent anywhere.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import oklch as ok  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

KEYS = ("bg1", "bg2", "text", "card", "cardText", "cardBorder", "primary", "btnText", "accent", "good", "bad")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
OFFICE_EXT = {".pptx": "ppt", ".potx": "ppt", ".ppsx": "ppt", ".docx": "word", ".dotx": "word", ".xlsx": "xl"}
CHROMATIC = 0.04  # OKLCH chroma below this counts as grey
MERGE_DE = 0.06  # colours closer than this (OKLab) are one colour
NEEDS_PILLOW = "사진·로고 파일(JPG 등)을 읽으려면 Pillow가 필요해요. `py shared/tools/ensure.py pillow --yes`로 설치하거나(선생님 동의 후), PNG로 저장해서 다시 올려 주세요."


class ColorFromError(Exception):
    """A problem the teacher can understand (message is plain Korean + a way out)."""


# ---------- sources -> [(hex, weight)] ----------
def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def decode_png(data: bytes) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    """Stdlib PNG decoder (non-interlaced, bit depth 8 or 16, palette 1-8 bit). Returns (w, h, [(r,g,b,a)...])."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ColorFromError("PNG 파일이 아니에요.")
    pos, idat, plte, trns, hdr = 8, [], b"", b"", None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    if not hdr:
        raise ColorFromError("PNG 머리글이 없어요.")
    w, h, depth, ctype, _, _, interlace = hdr
    if interlace:
        raise ColorFromError("겹줄(interlaced) PNG는 직접 읽지 못해요. Pillow를 설치하거나 다시 저장해 주세요.")
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bpp = max(1, chans * depth // 8)
    stride = (w * chans * depth + 7) // 8
    raw = zlib.decompress(b"".join(idat))
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        cur = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride):
                cur[i] = (cur[i] + cur[i - bpp]) & 255
        elif f == 2:
            for i in range(stride):
                cur[i] = (cur[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                cur[i] = (cur[i] + (((cur[i - bpp] if i >= bpp else 0) + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                cur[i] = (cur[i] + _paeth(cur[i - bpp] if i >= bpp else 0, prev[i], prev[i - bpp] if i >= bpp else 0)) & 255
        rows.append(cur)
        prev = cur
    px: list[tuple[int, int, int, int]] = []
    for cur in rows:
        if depth == 8 and ctype in (2, 6, 0, 4):
            for x in range(w):
                o = x * chans
                if ctype == 2:
                    px.append((cur[o], cur[o + 1], cur[o + 2], 255))
                elif ctype == 6:
                    px.append((cur[o], cur[o + 1], cur[o + 2], cur[o + 3]))
                elif ctype == 0:
                    px.append((cur[o], cur[o], cur[o], 255))
                else:
                    px.append((cur[o], cur[o], cur[o], cur[o + 1]))
        elif depth == 16 and ctype in (2, 6, 0, 4):
            for x in range(w):
                o = x * chans * 2
                v = [cur[o + 2 * i] for i in range(chans)]  # high bytes
                if ctype == 2:
                    px.append((v[0], v[1], v[2], 255))
                elif ctype == 6:
                    px.append((v[0], v[1], v[2], v[3]))
                elif ctype == 0:
                    px.append((v[0], v[0], v[0], 255))
                else:
                    px.append((v[0], v[0], v[0], v[1]))
        elif ctype in (0, 3) and depth in (1, 2, 4, 8):
            mask = (1 << depth) - 1
            for x in range(w):
                bit = x * depth
                idx = (cur[bit // 8] >> (8 - depth - (bit % 8))) & mask
                if ctype == 3:
                    a = trns[idx] if idx < len(trns) else 255
                    px.append((plte[idx * 3], plte[idx * 3 + 1], plte[idx * 3 + 2], a))
                else:
                    g = idx * 255 // mask
                    px.append((g, g, g, 255))
        else:
            raise ColorFromError("이 PNG 형식은 직접 읽지 못해요. Pillow를 설치하거나 다시 저장해 주세요.")
    return w, h, px


def _pixels_pillow(path: Path):
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        raise ColorFromError(NEEDS_PILLOW)
    im = Image.open(path).convert("RGBA")
    im.thumbnail((200, 200))
    return im.size[0], im.size[1], list(im.getdata())


def image_pixels(path: Path):
    """(w, h, [(r,g,b,a)...]) from a file: stdlib for PNG, Pillow for the rest."""
    if path.suffix.lower() == ".png":
        try:
            return decode_png(path.read_bytes())
        except ColorFromError as exc:
            try:
                import PIL  # noqa: F401
            except ImportError:
                raise exc
            return _pixels_pillow(path)
    return _pixels_pillow(path)


def median_cut(pixels: list[tuple[int, int, int]], boxes: int = 8) -> list[tuple[str, int]]:
    """Median-cut quantiser (deterministic): split the box with the widest channel range at its median until `boxes`; return [(avg hex, count)]."""
    work = [list(pixels)]
    while len(work) < boxes:
        best, best_rng = -1, 0
        for i, b in enumerate(work):
            if len(b) < 2:
                continue
            rng = max(max(p[c] for p in b) - min(p[c] for p in b) for c in range(3))
            if rng * len(b) > best_rng:
                best, best_rng = i, rng * len(b)
        if best < 0 or best_rng == 0:
            break
        b = work.pop(best)
        ch = max(range(3), key=lambda c: max(p[c] for p in b) - min(p[c] for p in b))
        b.sort(key=lambda p: (p[ch], p))
        mid = len(b) // 2
        work += [b[:mid], b[mid:]]
    out = []
    for b in work:
        if b:
            out.append((ok.rgb_to_hex(*(sum(p[c] for p in b) / len(b) for c in range(3))), len(b)))
    return out


def is_background(L: float, C: float) -> bool:
    """Near-white or near-black with almost no colour: paper / screen background, not a brand colour."""
    return (L > 0.94 and C < 0.03) or (L < 0.16 and C < 0.04)


def from_image(path: Path) -> list[tuple[str, float]]:
    """Dominant colours of a photo/logo: sample pixels, drop transparent and near-white/near-black background, median-cut to 8 boxes."""
    w, h, px = image_pixels(path)
    step = max(1, len(px) // 30000)
    keep = []
    for r, g, b, a in px[::step]:
        if a < 128:
            continue
        L, C, _ = ok.hex_to_oklch(ok.rgb_to_hex(r, g, b))
        if is_background(L, C):
            continue
        keep.append((r, g, b))
    if not keep:
        raise ColorFromError("배경(흰색·검정)을 빼고 나니 남는 색이 없어요. 색이 있는 그림이나 로고를 올려 주세요.")
    return [(c, float(n)) for c, n in median_cut(keep, 8)]


def _clr(el) -> str | None:
    """a:srgbClr / a:sysClr child -> '#rrggbb'."""
    for ch in el:
        tag = ch.tag.rsplit("}", 1)[-1]
        if tag == "srgbClr" and re.fullmatch(r"[0-9a-fA-F]{6}", ch.get("val", "")):
            return "#" + ch.get("val").lower()
        if tag == "sysClr" and re.fullmatch(r"[0-9a-fA-F]{6}", ch.get("lastClr", "")):
            return "#" + ch.get("lastClr").lower()
    return None


def theme_colors(xml: bytes) -> dict[str, str]:
    """DrawingML clrScheme (dk1 lt1 dk2 lt2 accent1..6 hlink folHlink) -> {name: hex}."""
    root = ET.fromstring(xml)
    out = {}
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] == "clrScheme":
            for ch in el:
                c = _clr(ch)
                if c:
                    out[ch.tag.rsplit("}", 1)[-1]] = c
            break
    return out


def from_office(path: Path) -> tuple[list[tuple[str, float]], dict]:
    """Theme colours of a PPTX/POTX/DOCX/XLSX: accent1 first (the designers' main colour), then the other accents and dk2; weights descend."""
    folder = OFFICE_EXT[path.suffix.lower()]
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ColorFromError("파일이 열리지 않아요. 손상됐거나 암호가 걸린 파일일 수 있어요.")
    with zf:
        names = [n for n in zf.namelist() if n.startswith(f"{folder}/theme/theme") and n.endswith(".xml")]
        if not names:
            raise ColorFromError("이 파일에는 색 테마가 없어요. 슬라이드·문서 안의 그림 파일(PNG)이나 로고를 올려 주세요.")
        theme = theme_colors(zf.read(sorted(names)[0]))
    if not theme:
        raise ColorFromError("색 테마를 읽지 못했어요.")
    order = ["accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "dk2", "hlink"]
    cands = [(theme[k], 100.0 - i * 10) for i, k in enumerate(order) if k in theme]
    return cands, {"theme": theme}


_HWPX_ATTR = re.compile(r'\b(?:textColor|faceColor|hatchColor|shadeColor|color|borderColor|bgColor)="(#[0-9a-fA-F]{6})"')


def from_hwpx(path: Path) -> list[tuple[str, float]]:
    """한글(HWPX): count colour attributes in Contents/*.xml (text colour, fill, border). Only what the document actually uses; plain documents give almost nothing."""
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ColorFromError("HWPX 파일이 열리지 않아요. 한글에서 `다른 이름으로 저장 → HWPX`로 다시 저장해 주세요.")
    counts: dict[str, float] = {}
    with zf:
        for n in zf.namelist():
            if n.startswith("Contents/") and n.endswith(".xml"):
                if b"clrScheme" in (b := zf.read(n)):  # a theme inside (rare): use it
                    try:
                        th = theme_colors(b)
                        for i, k in enumerate(("accent1", "accent2", "accent3", "accent4", "accent5", "accent6")):
                            if k in th:
                                counts[th[k]] = counts.get(th[k], 0) + 100 - i * 10
                    except ET.ParseError:
                        pass
                for c in _HWPX_ATTR.findall(b.decode("utf-8", "replace")):
                    counts[c.lower()] = counts.get(c.lower(), 0) + 1
    if not counts:
        raise ColorFromError("이 한글 파일에서 색을 찾지 못했어요. 로고나 사진 파일을 올려 주세요.")
    return list(counts.items())


_CSS_HEX = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_CSS_RGB = re.compile(r"rgba?\(\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*[, ]\s*(\d{1,3})")
_CSS_VAR = re.compile(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6}\b|rgba?\([^)]*\))")
_SEM_SKIP = {"bg", "soft", "tint", "light", "muted", "on", "hover", "active", "disabled", "shadow", "alpha", "rgb"}
_SEM_SETS = {  # CSS variable name tokens -> the meaning they carry in our palette
    "good": {"good", "success", "ok", "mint", "green", "positive", "correct", "valid"},
    "bad": {"bad", "error", "danger", "red", "stop", "negative", "wrong", "invalid", "fail", "failure"},
    "text": {"ink", "text", "fg", "foreground"},
    "border": {"border", "line", "hairline", "stroke", "divider"},
    "bg": {"bg", "background", "paper", "canvas", "surface", "page"},
}
_WEAK_NAMES = {"mint", "green", "red", "stop"}  # a colour NAME, not a meaning: a site may call its blue "mint" -> a name like --ok / --error / --danger wins over it
_PRIMARY_NAMES = re.compile(r"primary|brand|main|theme|key", re.I)


def semantic_role(name: str) -> str | None:
    """CSS variable name -> 'good' | 'bad' | 'text' | 'border' | 'bg' | None  (--success, --color-danger, --ink ... ; --success-bg or --text-muted are not the role colour itself)."""
    toks = [t for t in re.split(r"[-_]+", name.lower()) if t and not t.isdigit()]
    if not toks or _PRIMARY_NAMES.search(name):
        return None
    for role, words in _SEM_SETS.items():
        if role == "bg":  # background: the whole name must be a background word (--bg, --page-bg), not --bg-soft / --card-bg-hover
            if toks[-1] in words and not (set(toks) & (_SEM_SKIP - {"bg"})) and len(toks) <= 2:
                return role
            continue
        if toks[0] in words or toks[-1] in words:
            if set(toks) & _SEM_SKIP:
                return None
            return role
    return None
_ACCENT_NAMES = re.compile(r"accent|secondary|highlight", re.I)


def _norm_css(tok: str) -> str | None:
    m = _CSS_RGB.fullmatch(tok) or _CSS_RGB.match(tok)
    if m and tok.lower().startswith("rgb"):
        return ok.rgb_to_hex(*(min(255, int(x)) for x in m.groups()))
    m = _CSS_HEX.fullmatch(tok)
    if m:
        v = m.group(1)
        return ok.rgb_to_hex(*ok.hex_to_rgb("#" + v[:6] if len(v) != 3 else "#" + v))
    return None


def from_css(text: str) -> tuple[list[tuple[str, float]], dict]:
    """Colour frequencies in CSS/HTML/SVG text. Variables whose name says primary/brand/main/theme get x20, accent/secondary/highlight x10."""
    counts: dict[str, float] = {}
    for m in _CSS_HEX.finditer(text):
        c = _norm_css("#" + m.group(1))
        if c:
            counts[c] = counts.get(c, 0) + 1
    for m in _CSS_RGB.finditer(text):
        c = ok.rgb_to_hex(*(min(255, int(x)) for x in m.groups()))
        counts[c] = counts.get(c, 0) + 1
    hints = {}
    for name, val in _CSS_VAR.findall(text):
        c = _norm_css(val)
        if not c:
            continue
        role = semantic_role(name)
        if role:
            weak = 1 if (set(re.split(r"[-_]+", name.lower())) & _WEAK_NAMES) else 0
            prio = hints.setdefault("_prio", {})
            if role not in hints or weak < prio.get(role, 1):
                hints[role], prio[role] = c, weak
            continue
        if _PRIMARY_NAMES.search(name):
            counts[c] = counts.get(c, 0) + 20
            hints.setdefault("primary", c)
        elif _ACCENT_NAMES.search(name):
            counts[c] = counts.get(c, 0) + 10
            hints.setdefault("accent", c)
    if not counts:
        raise ColorFromError("CSS·HTML 안에서 색 값을 찾지 못했어요.")
    return list(counts.items()), hints


# ---------- candidates -> seeds ----------
def cluster(cands: list[tuple[str, float]]) -> list[dict]:
    """Merge near-identical colours (ΔE_OK < 0.06, heavier one wins), drop pure backgrounds, annotate OKLCH. Heaviest first."""
    items = []
    for hexc, wgt in sorted(cands, key=lambda x: -x[1]):
        L, C, h = ok.hex_to_oklch(hexc)
        for it in items:
            if ok.delta_e(it["hex"], hexc) < MERGE_DE:
                it["w"] += wgt
                break
        else:
            items.append({"hex": hexc.lower(), "w": float(wgt), "L": L, "C": C, "h": h})
    total = sum(i["w"] for i in items) or 1.0
    for i in items:
        i["share"] = round(i["w"] / total, 3)
    return items


def pick_seeds(items: list[dict], hints: dict | None = None) -> tuple[str, str, list[str]]:
    """(primary, accent, notes). primary = heaviest colourful colour (weight x chroma); accent = the best colourful colour that differs clearly in hue
    from the primary; when the material has only one colour the accent is a complementary hue at the same lightness/chroma (harmony from oklch.py)."""
    notes: list[str] = []
    hints = hints or {}
    colorful = [i for i in items if i["C"] >= CHROMATIC and not is_background(i["L"], i["C"])]
    if not colorful:
        neutrals = [i for i in items if not (i["L"] > 0.94)] or items
        base = max(neutrals, key=lambda i: i["w"])
        notes.append("색이 거의 없는(흑백) 자료라 포인트 색은 기본 파랑 계열로 정했어요.")
        primary = base["hex"]
        _, _, h = ok.hex_to_oklch("#2b6cff")
        accent = ok.oklch_to_hex(0.55, 0.15, h)
        return primary, accent, notes
    score = lambda i: i["w"] * (i["C"] + 0.03)  # noqa: E731
    prim = next((i for i in colorful if i["hex"] == hints.get("primary")), None) or max(colorful, key=score)
    rest = [i for i in colorful if i is not prim and ok.delta_e(i["hex"], prim["hex"]) >= 0.12]
    acc_hint = next((i for i in rest if i["hex"] == hints.get("accent")), None)
    if acc_hint:
        accent = acc_hint["hex"]
    elif rest:
        far = [i for i in rest if ok.hue_distance(i["h"], prim["h"]) >= 25] or rest
        accent = max(far, key=score)["hex"]
    else:
        accent = ok.harmony(prim["hex"], "complementary")[1]
        notes.append("자료에 색이 하나뿐이라 반대 색 계열로 포인트 색을 만들었어요.")
    return prim["hex"], accent, notes


# ---------- seeds -> tokens ----------
def _hint_candidates(hint: str, dark: bool, light_band: tuple = (0.38, 0.56)) -> list[str]:
    """Colours with the hint's hue (and at least a clear chroma), lightness stepping away from the hint's own: [closest to the source ... farthest]."""
    L, C, h = ok.hex_to_oklch(hint)
    lo, hi = (0.70, 0.90) if dark else light_band  # inside this band a colour is readable on the card and not muddy (a red below 0.44 turns brown-black)
    chroma = max(C, 0.12)
    steps = sorted({round(min(hi, max(lo, L)), 3)} | {round(lo + (hi - lo) * i / 6, 3) for i in range(7)}, key=lambda v: abs(v - L))
    return [ok.oklch_to_hex(v, chroma, h) for v in steps]


def _meaning_pair(card: str, dark: bool, good_hint: str | None = None, bad_hint: str | None = None) -> tuple[str, str]:
    """good/bad colours: hue stays green/red-ish but lightness is split so they also differ for red-green colour blindness; contrast on the card >= 4.5.
    A hint (the source's own success/error colour) keeps its hue and is only moved in lightness, closest to the original first."""
    import color_check as cc
    if good_hint or bad_hint:
        gs = _hint_candidates(good_hint or ok.oklch_to_hex(0.5 if not dark else 0.8, 0.16, 150), dark, (0.34, 0.56))
        bs = _hint_candidates(bad_hint or ok.oklch_to_hex(0.5 if not dark else 0.8, 0.17, 28), dark, (0.46, 0.56))
        best_h, best_hde = None, -1.0
        pairs = sorted(((i + j, i, j) for i in range(len(gs)) for j in range(len(bs))))  # the pair closest to both source colours first
        for _, i, j in pairs:
            g, b = ok.fit_contrast(gs[i], card, 4.5), ok.fit_contrast(bs[j], card, 4.5)
            de = min([ok.delta_e(cc.simulate(g, k), cc.simulate(b, k)) for k in cc.MACHADO] + [ok.delta_e(g, b)])
            if de >= cc.MIN_DE:
                return g, b
            if de > best_hde:
                best_h, best_hde = (g, b), de
        return best_h  # type: ignore[return-value]
    best, best_de = None, -1.0
    lights = (0.78, 0.86, 0.70) if dark else (0.45, 0.52, 0.40)
    for gh, bh in ((150, 28), (170, 28), (205, 28), (250, 28)):
        for lg in lights:
            for lb in lights:
                if abs(lg - lb) < 0.12:
                    continue
                g = ok.fit_contrast(ok.oklch_to_hex(lg, 0.16, gh), card, 4.5)
                b = ok.fit_contrast(ok.oklch_to_hex(lb, 0.17, bh), card, 4.5)
                de = min([ok.delta_e(cc.simulate(g, k), cc.simulate(b, k)) for k in cc.MACHADO] + [ok.delta_e(g, b)])
                if de >= cc.MIN_DE:
                    return g, b
                if de > best_de:
                    best, best_de = (g, b), de
    return best  # type: ignore[return-value]


def tokens_from_seeds(primary: str, accent: str, dark: bool = False, hints: dict | None = None) -> dict[str, str]:
    """Map two brand colours onto the 11 colour tokens. Lightness is adjusted (hue kept) so that: text on bg1/bg2 and card >= 4.5 (aim 7),
    btnText on primary >= 4.5, primary on bg1 >= 3, accent on bg1/card >= 3, good/bad on card >= 4.5."""
    _, pc, ph = ok.hex_to_oklch(primary)
    th = ph if pc >= 0.02 else ok.hex_to_oklch(accent)[2]
    tint = min(max(pc, 0.0), 0.04)
    if dark:
        bg1, bg2 = ok.oklch_to_hex(0.20, 0.014 + tint / 6, th), ok.oklch_to_hex(0.25, 0.018 + tint / 6, th)
        card = ok.oklch_to_hex(0.28, 0.018 + tint / 6, th)
        text = ok.oklch_to_hex(0.96, 0.012, th)
    else:
        bg1, bg2 = ok.oklch_to_hex(0.975, 0.008 + tint / 4, th), ok.oklch_to_hex(0.945, 0.014 + tint / 3, th)
        card = "#ffffff"
        text = ok.oklch_to_hex(0.24, 0.025, th)
    hints = hints or {}
    if hints.get("bg") and not dark and ok.hex_to_oklch(hints["bg"])[0] >= 0.9:  # the source's own light page colour
        bg1 = hints["bg"]
        L0, C0, H0 = ok.hex_to_oklch(bg1)
        bg2 = ok.oklch_to_hex(max(0.0, L0 - 0.03), C0, H0)
    if hints.get("text"):
        text = hints["text"]
    if hints.get("text") and min(ok.contrast(text, x) for x in (bg1, bg2, card)) >= 4.5:
        text_fit = text  # the source's own ink is already readable: keep it exactly
    else:
        text_fit = ok.fit_contrast(text, [bg1, bg2, card], 7.0)
        if min(ok.contrast(text_fit, x) for x in (bg1, bg2, card)) < 4.5:
            text_fit = ok.fit_contrast(text, [bg1, bg2, card], 4.5)
    pr = ok.fit_contrast(primary, [bg1, card], 3.0)
    ac = ok.fit_contrast(accent, [bg1, card], 3.0)
    dark_btn, light_btn = ok.oklch_to_hex(0.2, 0.02, ok.hex_to_oklch(pr)[2]), "#ffffff"
    btn = max((dark_btn, light_btn), key=lambda c: ok.contrast(c, pr))
    btn = ok.fit_contrast(btn, pr, 4.5)
    good, bad = _meaning_pair(card, dark, hints.get("good"), hints.get("bad"))
    return {"bg1": bg1, "bg2": bg2, "text": text_fit, "card": card, "cardText": text_fit, "cardBorder": hints.get("border") or pr, "primary": pr, "btnText": btn,
            "accent": ac, "good": good, "bad": bad}


def fit_palette(colors: dict, dark: bool | None = None) -> dict[str, str]:
    """Complete and repair a user's colour dict (full or partial) so design.palette_issues() is empty. Given colours are kept; missing ones come from
    tokens_from_seeds(primary, accent); failing foreground colours move in lightness only (hue kept)."""
    c = {k: v.lower() for k, v in colors.items() if k in KEYS}
    for k, v in c.items():
        if not re.fullmatch(r"#[0-9a-f]{6}", v):
            raise ColorFromError(f"colors.{k}='{v}' 은(는) #rrggbb 형식이 아니에요.")
    if dark is None:
        dark = ok.luminance(c["bg1"]) < 0.3 if "bg1" in c else False
    primary = c.get("primary") or c.get("accent") or "#2b6cff"
    base = tokens_from_seeds(primary, c.get("accent") or ok.harmony(primary, "complementary")[1], dark)
    out = {**base, **c}
    bgs = [out["bg1"], out["bg2"]]
    out["text"] = ok.fit_contrast(out["text"], bgs, 4.5)
    out["cardText"] = ok.fit_contrast(out["cardText"], out["card"], 4.5)
    out["btnText"] = ok.fit_contrast(out["btnText"], out["primary"], 4.5)
    out["good"] = ok.fit_contrast(out["good"], out["card"], 3.0)
    out["bad"] = ok.fit_contrast(out["bad"], out["card"], 3.0)
    out["primary"] = ok.fit_contrast(out["primary"], out["bg1"], 3.0)
    out["btnText"] = ok.fit_contrast(out["btnText"], out["primary"], 4.5)
    return {k: out[k] for k in KEYS}


def contrast_report(colors: dict) -> dict:
    """The ratios design.py checks, rounded."""
    r = ok.contrast
    return {"text_on_bg": round(min(r(colors["text"], colors["bg1"]), r(colors["text"], colors["bg2"])), 2),
            "cardText_on_card": round(r(colors["cardText"], colors["card"]), 2),
            "btnText_on_primary": round(r(colors["btnText"], colors["primary"]), 2),
            "primary_on_bg1": round(r(colors["primary"], colors["bg1"]), 2),
            "accent_on_bg1": round(r(colors["accent"], colors["bg1"]), 2)}


def _gather(path: Path) -> tuple[list, dict, dict, str]:
    """One file -> (candidates, hints, extra, kind)."""
    path = Path(path)
    if not path.exists():
        raise ColorFromError(f"파일을 찾지 못했어요: {path}")
    ext = path.suffix.lower()
    hints: dict = {}
    extra: dict = {}
    if ext in IMAGE_EXT:
        cands, kind = from_image(path), "image"
    elif ext in OFFICE_EXT:
        cands, extra = from_office(path)
        hints = {"primary": cands[0][0].lower()}  # the theme designer's first accent is the main colour
        kind = "office-theme"
    elif ext == ".hwpx":
        cands, kind = from_hwpx(path), "hwpx"
    elif ext in (".css", ".html", ".htm", ".svg"):
        cands, hints = from_css(path.read_text(encoding="utf-8", errors="replace"))
        kind = "css"
    elif ext in (".hwp", ".ppt", ".doc"):
        raise ColorFromError("옛 형식(.hwp/.ppt/.doc)은 읽지 못해요. 한글은 HWPX, 파워포인트·워드는 PPTX·DOCX로 저장해서 올려 주세요.")
    else:
        raise ColorFromError(f"지원하지 않는 파일이에요({ext}). 사진·로고(PNG/JPG), PPTX/POTX, DOCX, HWPX, CSS/HTML을 올려 주세요.")
    return cands, hints, extra, kind


def extract(path: Path, dark: bool = False) -> dict:
    """File -> palette JSON (see module doc). Raises ColorFromError with a plain-Korean message."""
    return extract_many([Path(path)], dark)


def extract_many(paths: list, dark: bool = False) -> dict:
    """One or several files (a site's app.css + premium.css + tokens.css ...) -> ONE palette JSON. Colours are pooled; the first file that names a role wins."""
    paths = [Path(p) for p in paths]
    if not paths:
        raise ColorFromError("파일을 하나 이상 알려 주세요.")
    cands: list = []
    hints: dict = {}
    extra: dict = {}
    kinds: list = []
    for p in paths:
        c, h, e, k = _gather(p)
        cands += c
        for key, val in h.items():
            if key == "_prio":
                continue
            wk = (h.get("_prio") or {}).get(key, 0)
            if key not in hints or wk < hints.setdefault("_prio", {}).get(key, 0):
                hints[key] = val
                hints.setdefault("_prio", {})[key] = wk
        extra = extra or e
        kinds.append(k)
    items = cluster(cands)
    primary, accent, notes = pick_seeds(items, hints)
    colors = tokens_from_seeds(primary, accent, dark, hints)
    respected = {k: hints[k] for k in ("good", "bad", "text", "border", "bg") if k in hints}
    if respected:
        notes.append("원본 자료의 이름 있는 색을 그대로 따랐어요: " + ", ".join(f"{k} {v}" for k, v in respected.items()) + " (읽기 쉽게 밝기만 조정)")
    src = {"file": paths[0].name, "type": kinds[0]} if len(paths) == 1 else {"files": [p.name for p in paths], "type": "+".join(dict.fromkeys(kinds))}
    return {"version": 1, "kind": "user-palette", "palette": "user-" + paths[0].stem[:24], "source": src,
            "mode": "dark" if dark else "light", "seeds": {"primary": primary, "accent": accent}, "respected": respected,
            "accentDeco": accent,  # the accent exactly as the source has it: decoration only (no text on it); design.palette_from carries it as --accent-deco
            "swatches": [{"hex": i["hex"], "share": i["share"]} for i in items[:8]], "colors": colors, "contrast": contrast_report(colors),
            "notes": notes, **({"office": extra["theme"]} if extra else {})}


# ---------- saved default (prefs) ----------
def _prefs_module():
    """The teacher-studio prefs.py if it is installed next to us (repo or ~/.claude/skills), else None."""
    import importlib.util
    for cand in (HERE.parents[1] / "teacher-studio" / "scripts" / "prefs.py", HERE.parents[2] / "teacher-studio" / "scripts" / "prefs.py",
                 HERE.parents[1] / "skills" / "teacher-studio" / "scripts" / "prefs.py",
                 Path.home() / ".claude" / "skills" / "teacher-studio" / "scripts" / "prefs.py",
                 Path.home() / ".agents" / "skills" / "teacher-studio" / "scripts" / "prefs.py"):
        if cand.exists():
            spec = importlib.util.spec_from_file_location("ts_prefs", cand)
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            if hasattr(mod, "save_palette"):
                return mod
    return None


def prefs_path() -> Path:
    return Path.home() / ".teacher-studio" / "prefs.json"


def save_default(pal: dict) -> str:
    """Store the palette as the user's default (only called when the caller asks). Returns the file path."""
    keep = {"palette": pal["palette"], "mode": pal.get("mode", "light"), "colors": pal["colors"], "source": pal.get("source", {})}
    mod = _prefs_module()
    if mod:
        mod.save_palette(keep)
        return str(mod.PATH)
    p = prefs_path()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data = data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        data = {}
    data["palette"] = keep
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="+", help="logo/photo (PNG/JPG), PPTX/POTX, DOCX, HWPX, CSS/HTML (one or several files)")
    ap.add_argument("--out", help="write the palette JSON here (default: print)")
    ap.add_argument("--dark", action="store_true", help="dark background version (default: light)")
    ap.add_argument("--save-default", action="store_true", help="also save as the user's default palette in ~/.teacher-studio/prefs.json")
    a = ap.parse_args()
    try:
        pal = extract_many([Path(f) for f in a.file], a.dark)
    except ColorFromError as exc:
        print(f"FAIL {exc}")
        return 1
    text = json.dumps(pal, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"OK {a.out}  주색 {pal['seeds']['primary']} · 포인트 {pal['seeds']['accent']} · 글자 대비 {pal['contrast']['text_on_bg']}:1 ({pal['mode']})")
    else:
        print(text)
    if a.save_default:
        print("OK 기본 팔레트로 저장:", save_default(pal))
    return 0


if __name__ == "__main__":
    sys.exit(main())
