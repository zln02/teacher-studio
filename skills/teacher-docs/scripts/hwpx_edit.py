# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Read, fill and patch an existing HWPX in place (standard library). Formatting is kept: only <hp:t> text changes;
runs, charPr/paraPr references, tables and every other zip entry stay byte-identical.

    text(path)                         -> list of paragraph strings (body + table cells, in order)
    blanks(path)                       -> blanks found: {{키}}, [키], 「  」-style empty label cells
    fill(path, out, values)            -> {"filled": [...], "missing": [...]}   values: {"성명": "…", "{{날짜}}": "…"}
    patch(path, out, edits)            -> {"applied": [...], "unapplied": [...]} edits: [{"find","replace"} | {"para": n, "text"} | {"after", "insert"}]

Rules: never overwrite the user's file (out must differ), drop <hp:linesegarray> of touched paragraphs (한글 re-lays them out),
keep the root element's original namespace declarations, mimetype first and stored.
"""
from __future__ import annotations

import copy
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import hwpx_write

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
T = f"{{{HP}}}t"
P_ = f"{{{HP}}}p"
RUN = f"{{{HP}}}run"
TC = f"{{{HP}}}tc"
LSA = f"{{{HP}}}linesegarray"
BLANK = re.compile(r"\{\{\s*([^{}\n]{1,40}?)\s*\}\}|\[\s*([^\[\]\n]{1,40}?)\s*\]")


def _read(path: Path):
    with zipfile.ZipFile(path) as z:
        order = [i.filename for i in z.infolist()]
        files = {n: z.read(n) for n in order}
    return files, order


def sections(files: dict) -> list[str]:
    return sorted((n for n in files if re.match(r"Contents/section\d+\.xml$", n)), key=lambda n: int(re.findall(r"\d+", n)[-1]))


def _register(xml: bytes) -> str:
    """Register every xmlns prefix of the document (so ET writes hp:/hs:/hh: back, not ns0:) and return the original root start tag."""
    s = xml.decode("utf-8")
    for pre, uri in re.findall(r'xmlns:(\w+)="([^"]+)"', s[:5000]):
        ET.register_namespace(pre, uri)
    m = re.search(r"<(?!\?)[^>]+>", s)
    return m.group(0)


def _serialize(root: ET.Element, orig_start: str) -> bytes:
    body = ET.tostring(root, encoding="unicode")
    body = re.sub(r"^<[^>]+>", lambda _: orig_start.replace("/>", ">") if orig_start.endswith("/>") else orig_start, body, count=1)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>' + body).encode("utf-8")


def para_text(p: ET.Element) -> str:
    out = []
    for el in p.iter():
        if el.tag == T:
            out.append("".join(el.itertext()))
        elif el.tag == P_ and el is not p:
            pass
    return "".join(out)


def _own_ts(p: ET.Element) -> list[ET.Element]:
    """<hp:t> of this paragraph only (not of paragraphs nested in its tables)."""
    res = []

    def walk(e):
        for c in e:
            if c.tag == P_:
                continue
            if c.tag == T:
                res.append(c)
            else:
                walk(c)
    walk(p)
    return res


def _t_text(t: ET.Element) -> str:
    return (t.text or "") + "".join((c.tail or "") for c in t)


def _set_t(t: ET.Element, s: str) -> None:
    for c in list(t):  # inline markers (lineBreak/tab) inside a replaced span are dropped
        t.remove(c)
    t.text = s


def _paragraphs(root: ET.Element) -> list[ET.Element]:
    return [e for e in root.iter(P_)]


def text(path) -> list[str]:
    files, _ = _read(Path(path))
    out = []
    for n in sections(files):
        root = ET.fromstring(files[n])
        for p in _paragraphs(root):
            out.append("".join(_t_text(t) for t in _own_ts(p)))
    return out


def blanks(path) -> list[str]:
    found = []
    for line in text(path):
        for m in BLANK.finditer(line):
            if m.group(0) not in found:
                found.append(m.group(0))
    return found


def _replace_in_para(p: ET.Element, find: str, repl: str, count: int = 0) -> int:
    """Run-aware replace: the match may span several <hp:t>; the replacement goes into the first one, the rest of the span is removed."""
    ts = _own_ts(p)
    if not ts:
        return 0
    n = 0
    while True:
        texts = [_t_text(t) for t in ts]
        full = "".join(texts)
        i = full.find(find)
        if i < 0 or (count and n >= count):
            return n
        j = i + len(find)
        pos = 0
        first = True
        for t, s in zip(ts, texts):
            a, b = pos, pos + len(s)
            pos = b
            if b <= i or a >= j:
                continue
            lo, hi = max(i, a) - a, min(j, b) - a
            new = s[:lo] + (repl if first else "") + s[hi:]
            first = False
            _set_t(t, new)
        n += 1
        if repl.find(find) >= 0:  # avoid an endless loop when the replacement contains the search text
            return n


def _touch(p: ET.Element) -> None:
    for lsa in list(p.findall(LSA)):
        p.remove(lsa)


def _save(files, order, out: Path, src: Path) -> None:
    if Path(out).resolve() == Path(src).resolve():
        raise ValueError("결과는 새 파일로 저장해요 (원본을 덮어쓰지 않아요): out must differ from the source")
    hwpx_write.save(files, order, Path(out))


def fill(path, out, values: dict) -> dict:
    """Fill {{키}} / [키] blanks and label cells (a table cell whose text is the label -> the next cell to the right)."""
    path, out = Path(path), Path(out)
    files, order = _read(path)
    filled, keys = [], dict(values)
    for n in sections(files):
        start = _register(files[n])
        root = ET.fromstring(files[n])
        changed = False
        for p in _paragraphs(root):
            txt = "".join(_t_text(t) for t in _own_ts(p))
            for m in list(BLANK.finditer(txt)):
                k = (m.group(1) or m.group(2) or "").strip()
                for cand in (m.group(0), k):
                    if cand in keys:
                        if _replace_in_para(p, m.group(0), str(keys[cand]), 1):
                            filled.append(m.group(0))
                            _touch(p)
                            changed = True
                        break
        # label cells: <hp:tr> rows, label in one cell, value goes to the next empty cell
        for tr in root.iter(f"{{{HP}}}tr"):
            cells = tr.findall(TC)
            for ci, tc in enumerate(cells[:-1]):
                label = re.sub(r"\s+", "", "".join(_t_text(t) for t in tc.iter(T)))
                hit = next((k for k in keys if re.sub(r"\s+", "", k) == label and not BLANK.fullmatch(k)), None)
                if not hit:
                    continue
                nxt = cells[ci + 1]
                if re.sub(r"\s+", "", "".join(_t_text(t) for t in nxt.iter(T))):
                    continue  # already has content: leave it
                ps = list(nxt.iter(P_))
                if not ps:
                    continue
                p0 = ps[0]
                ts = _own_ts(p0)
                if ts:
                    _set_t(ts[0], str(keys[hit]))
                else:
                    run = p0.find(RUN)
                    if run is None:
                        run = ET.SubElement(p0, RUN, {"charPrIDRef": "0"})
                    ET.SubElement(run, T).text = str(keys[hit])
                _touch(p0)
                filled.append(hit)
                changed = True
        if changed:
            files[n] = _serialize(root, start)
    _save(files, order, out, path)
    missing = [k for k in values if k not in filled and f"{{{{{k}}}}}" not in filled and f"[{k}]" not in filled]
    return {"filled": filled, "missing": missing, "out": str(out)}


def patch(path, out, edits: list) -> dict:
    """Apply edits in place. Unapplied edits are reported (the caller must say so, never claim success)."""
    path, out = Path(path), Path(out)
    files, order = _read(path)
    applied, unapplied = [], []
    roots = {}
    starts = {}
    for n in sections(files):
        starts[n] = _register(files[n])
        roots[n] = ET.fromstring(files[n])
    allp = [(n, p) for n in roots for p in _paragraphs(roots[n])]
    for ed in edits:
        ok = False
        if "find" in ed:
            for n, p in allp:
                k = _replace_in_para(p, str(ed["find"]), str(ed.get("replace", "")), int(ed.get("count", 0)))
                if k:
                    _touch(p)
                    ok = True
                    if ed.get("count") == 1:
                        break
        elif "para" in ed:
            idx = int(ed["para"])
            if 0 <= idx < len(allp):
                n, p = allp[idx]
                ts = _own_ts(p)
                if ts:
                    _set_t(ts[0], str(ed["text"]))
                    for t in ts[1:]:
                        _set_t(t, "")
                    _touch(p)
                    ok = True
        elif "after" in ed:
            for n, p in allp:
                if str(ed["after"]) in "".join(_t_text(t) for t in _own_ts(p)):
                    parent = next((e for e in roots[n].iter() if p in list(e)), None)
                    if parent is None:
                        break
                    newp = copy.deepcopy(p)
                    for sub in list(newp):
                        if sub.tag == RUN:
                            for c in list(sub):
                                if c.tag != T:
                                    sub.remove(c)  # no copied tables / controls in the new paragraph
                    ts = _own_ts(newp)
                    if not ts:
                        break
                    _set_t(ts[0], str(ed["insert"]))
                    for t in ts[1:]:
                        _set_t(t, "")
                    _touch(newp)
                    newp.set("id", str(abs(hash((ed["insert"], len(applied)))) % 2147483647))
                    parent.insert(list(parent).index(p) + 1, newp)
                    ok = True
                    break
        (applied if ok else unapplied).append(ed)
    for n in roots:
        files[n] = _serialize(roots[n], starts[n])
    _save(files, order, out, path)
    return {"applied": applied, "unapplied": unapplied, "out": str(out)}
