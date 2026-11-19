#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Teacher Studio documents: one entry point.

  make    --spec doc.json --out 공문.hwpx|.docx|.html|.pdf [--template mine.docx] [--yes]   new 공문 / 가정통신문 / 안내문 / 보고서
  fill    FILE --set 키=값 [--set ...] | --values v.json --out new.hwpx|.docx|.pdf           fill a form's blanks, formatting kept
  patch   FILE.hwpx --edits edits.json --out new.hwpx                                         edit an HWPX in place (exit 2 if an edit was not applied)
  check   FILE [--kind gongmun] [--fillins a,b] [--allow-blanks]                              the document gate (doc_check.py)
  preview FILE.hwpx --out preview.html                                                        our own HWPX preview (approximation)
  text    FILE                                                                                text of hwpx/docx/pdf
  pdf     merge a.pdf b.pdf --out all.pdf | split a.pdf --out dir [--pages 1-3,5] | watermark a.pdf --text DRAFT --out b.pdf
          | fields a.pdf | tables a.pdf | png a.pdf --out dir
  where   which helpers exist here (hwp-docs skill, official docx/pdf skills, 한글 program, browser)
Old binary .hwp: never upload it. Ask the teacher to 「다른 이름으로 저장 → HWPX」 in 한글, or convert with their own 한글
(`where` tells if it is installed); the hwp-docs skill (kordoc) can read .hwp text if it is installed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import doc_check  # noqa: E402
import docmodel  # noqa: E402

OUT_DIR = Path.home() / "TeacherStudio"


def find_skill(name: str) -> str:
    """Path of an installed Agent Skill folder with SKILL.md (user skills, synced skills, plugin caches), or ''. Never copied - only pointed to."""
    home = Path.home() / ".claude"
    cands = [home / "skills" / name, home / "skills" / "synced", home / "plugins"]
    for c in cands:
        if (c / "SKILL.md").exists() and c.name == name:
            return str(c)
        if c.exists():
            try:
                for p in c.rglob("SKILL.md"):
                    if p.parent.name == name and ".trash" not in p.parts:
                        return str(p.parent)
            except OSError:
                pass
    return ""


def find_hangul() -> str:
    """The teacher's own 한글 (Hwp.exe), if installed (Windows)."""
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
        root = Path(base) / "Hnc"
        if root.exists():
            for p in root.rglob("Hwp.exe"):
                return str(p)
    return shutil.which("hwp") or ""


def where() -> dict:
    import pdf_tools
    return {"hwp-docs": find_skill("hwp-docs"), "docx": find_skill("docx"), "pdf": find_skill("pdf"), "hangul": find_hangul(),
            "node": shutil.which("node") or "", "browser": pdf_tools.has_browser()}


def old_hwp_message(path: Path) -> str:
    w = where()
    lines = [f"「{path.name}」은 옛 한글 형식(.hwp)이에요. 파일을 어디에도 올리지 않고 이 컴퓨터에서만 다뤄요.",
             "가장 좋은 방법: 한글에서 열고 [파일 → 다른 이름으로 저장 → 파일 형식: HWPX]로 저장해 주세요. 그 파일로 이어서 할게요."]
    if w["hangul"]:
        lines.append("이 컴퓨터에 한글이 있어요: 원하시면 한글로 열어 HWPX로 저장하는 방법을 하나씩 안내할게요.")
    if w["hwp-docs"] and w["node"]:
        lines.append("내용만 읽으면 되는 경우: 설치된 hwp-docs 스킬(kordoc)로 글자를 읽을 수 있어요 (서식 수정은 HWPX에서).")
    return "\n".join(lines)


def _values(a) -> dict:
    vals = {}
    if a.values:
        vals.update(json.loads(Path(a.values).read_text(encoding="utf-8")))
    for kv in a.set or []:
        k, _, v = kv.partition("=")
        vals[k.strip()] = v
    return vals


def make(spec: dict, out: Path, template=None, yes: bool = False) -> dict:
    model = docmodel.build(spec)
    suf = out.suffix.lower()
    out.parent.mkdir(parents=True, exist_ok=True)
    if suf == ".hwpx":
        import hwpx_write
        hwpx_write.write(model, out)
    elif suf == ".docx":
        import pdf_tools
        pdf_tools.need("python-docx", yes)
        import docx_tools
        docx_tools.write(model, out, template)
    elif suf in (".html", ".htm"):
        import doc_html
        out.write_text(doc_html.render(model, (spec.get("design") or {}).get("mood", "단정")), encoding="utf-8")
    elif suf == ".pdf":
        import doc_html
        import pdf_tools
        tmp = out.with_suffix(".print.html")
        tmp.write_text(doc_html.render(model, (spec.get("design") or {}).get("mood", "단정")), encoding="utf-8")
        r = pdf_tools.html_to_pdf(tmp, out)
        if not r["ok"]:
            return {"ok": False, "error": r["error"], "html": str(tmp)}
    else:
        return {"ok": False, "error": f"모르는 형식 {suf}: .hwpx .docx .pdf .html 중 하나"}
    return {"ok": True, "out": str(out), "kind": model["meta"]["kind"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--spec", required=True, type=Path)
    m.add_argument("--out", type=Path)
    m.add_argument("--template", type=Path)
    m.add_argument("--yes", action="store_true")
    f = sub.add_parser("fill")
    f.add_argument("file", type=Path)
    f.add_argument("--set", action="append")
    f.add_argument("--values")
    f.add_argument("--out", type=Path, required=True)
    f.add_argument("--yes", action="store_true")
    p = sub.add_parser("patch")
    p.add_argument("file", type=Path)
    p.add_argument("--edits", required=True)
    p.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("check")
    c.add_argument("file", type=Path)
    c.add_argument("--kind", default="")
    c.add_argument("--fillins", default="")
    c.add_argument("--allow-blanks", action="store_true")
    v = sub.add_parser("preview")
    v.add_argument("file", type=Path)
    v.add_argument("--out", type=Path)
    t = sub.add_parser("text")
    t.add_argument("file", type=Path)
    d = sub.add_parser("pdf")
    d.add_argument("op", choices=["merge", "split", "watermark", "fields", "tables", "png", "fill"])
    d.add_argument("files", nargs="+", type=Path)
    d.add_argument("--out", type=Path)
    d.add_argument("--pages", default="")
    d.add_argument("--text", default="DRAFT")
    d.add_argument("--set", action="append")
    d.add_argument("--values")
    d.add_argument("--yes", action="store_true")
    sub.add_parser("where")
    a = ap.parse_args()

    src = getattr(a, "file", None)
    if src is not None and Path(src).suffix.lower() == ".hwp":
        print(old_hwp_message(Path(src)))
        return 3
    if a.cmd == "where":
        print(json.dumps(where(), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "make":
        spec = json.loads(a.spec.read_text(encoding="utf-8"))
        out = a.out or OUT_DIR / f"{a.spec.stem}.hwpx"
        r = make(spec, out, a.template, a.yes)
        if not r["ok"]:
            print("FIX", r["error"])
            return 1
        print(f"built {out} ({r['kind']})")
        res = doc_check.run(out, "gongmun" if r["kind"] == "gongmun" else "", spec.get("fillins") or [], spec.get("template_blanks") is True)
        for lv, msg in res:
            print(f"{lv:4} {msg}")
        if out.suffix.lower() == ".hwpx":
            import hwpx_preview
            pv = out.with_suffix(".preview.html")
            pv.write_text(hwpx_preview.render(out), encoding="utf-8")
            print(f"preview {pv} (한글 화면의 근사치)")
        print(f"READY {out}")
        return 1 if any(lv == "FAIL" for lv, _ in res) else 0
    if a.cmd == "fill":
        vals = _values(a)
        suf = a.file.suffix.lower()
        if suf == ".hwpx":
            import hwpx_edit
            r = hwpx_edit.fill(a.file, a.out, vals)
        elif suf == ".docx":
            import pdf_tools
            pdf_tools.need("python-docx", a.yes)
            import docx_tools
            r = docx_tools.replace(a.file, a.out, vals)
        elif suf == ".pdf":
            import pdf_tools
            pdf_tools.need("pypdf", a.yes)
            r = pdf_tools.fill_form(a.file, a.out, vals)
        else:
            print("FIX .hwpx .docx .pdf 양식만 채울 수 있어요")
            return 1
        print(json.dumps(r, ensure_ascii=False))
        return 2 if r["missing"] else 0
    if a.cmd == "patch":
        import hwpx_edit
        edits = json.loads(Path(a.edits).read_text(encoding="utf-8")) if Path(a.edits).exists() else json.loads(a.edits)
        r = hwpx_edit.patch(a.file, a.out, edits)
        print(json.dumps({"applied": len(r["applied"]), "unapplied": r["unapplied"], "out": r["out"]}, ensure_ascii=False))
        return 2 if r["unapplied"] else 0
    if a.cmd == "check":
        res = doc_check.run(a.file, a.kind, [x for x in a.fillins.split(",") if x], a.allow_blanks)
        for lv, msg in res:
            print(f"{lv:4} {msg}")
        return 1 if any(lv == "FAIL" for lv, _ in res) else 0
    if a.cmd == "preview":
        import hwpx_preview
        out = a.out or a.file.with_suffix(".preview.html")
        out.write_text(hwpx_preview.render(a.file), encoding="utf-8")
        print(f"READY {out}")
        return 0
    if a.cmd == "text":
        for ln in doc_check.texts_of(a.file):
            print(ln)
        return 0
    if a.cmd == "pdf":
        import pdf_tools
        pdf_tools.need("pdfplumber" if a.op == "tables" else ("pypdfium2" if a.op == "png" else "pypdf"), a.yes)
        if a.op == "merge":
            print("READY", pdf_tools.merge(a.files, a.out))
        elif a.op == "split":
            for x in pdf_tools.split(a.files[0], a.out or a.files[0].parent, a.pages):
                print("READY", x)
        elif a.op == "watermark":
            print("READY", pdf_tools.watermark(a.files[0], a.out, a.text))
        elif a.op == "fields":
            print(json.dumps(pdf_tools.fields(a.files[0]), ensure_ascii=False, default=str))
        elif a.op == "tables":
            print(json.dumps(pdf_tools.extract_tables(a.files[0]), ensure_ascii=False))
        elif a.op == "png":
            for x in pdf_tools.to_png(a.files[0], a.out or a.files[0].parent):
                print("READY", x)
        elif a.op == "fill":
            print(json.dumps(pdf_tools.fill_form(a.files[0], a.out, _values(a)), ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
