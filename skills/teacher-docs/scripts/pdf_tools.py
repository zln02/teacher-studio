# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""PDF tools. pypdf (BSD-3) and pdfplumber (MIT) are installed on first need (shared/tools/ensure.py, after consent).

    html_to_pdf(html_path, pdf)        our A4 HTML -> PDF with the PC's Chrome/Edge (headless print), else Playwright
    merge(inputs, out)                 several PDFs -> one
    split(src, outdir, ranges=None)    "1-3,5" -> files (default: one file per page)
    fields(src) / fill_form(src, out, values)    PDF form (AcroForm) text fields / check boxes
    extract_text(src) / extract_tables(src)      text per page (pypdf) / tables (pdfplumber)
    watermark(src, out, text)          diagonal translucent stamp on every page (ASCII text drawn by us; Korean text via the HTML route)
    to_png(src, outdir)                pages -> PNG with pypdfium2 (for looking at the result)
    mini_pdf(pages, out, fields=None)  tiny stdlib PDF writer (Helvetica): stamps and test fixtures
Never upload a PDF anywhere: everything runs on this computer.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
for _p in (SKILL / "shared" / "tools", SKILL.parent.parent / "shared" / "tools"):
    if _p.exists():
        sys.path.insert(0, str(_p))
        break
import workdir  # noqa: E402  (shared/tools/workdir.py: work folders that never need %TEMP%, the no-browser probe)


def need(name: str, consent: bool = False) -> None:
    """Install pypdf / pdfplumber / pypdfium2 on first need (asks first)."""
    try:
        import ensure
    except ImportError:
        return
    r = ensure.ensure(name, consent=consent)
    if not r["ok"]:
        raise SystemExit("ASK TEACHER: " + r["prompt"] + "  (agree -> rerun with --yes)")


# ------------------------------------------------------------------------------------------------ stdlib mini writer
def _pdf_str(s: str) -> str:
    return "(" + s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ")"


def mini_pdf(pages: list, out, fields: list | None = None, size=(595, 842)) -> Path:
    """pages: list of either list[str] (lines of text) or {"stamp": "TEXT", "alpha": .18}. fields: [{"name","x","y","w","h","type":"text|check"}] on page 1."""
    objs: list[bytes] = []

    def add(b: str | bytes) -> int:
        objs.append(b.encode("latin-1") if isinstance(b, str) else b)
        return len(objs)
    font = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    gs = add("<< /Type /ExtGState /ca 0.18 /CA 0.18 >>")
    page_ids, annots_all = [], []
    pages_id_placeholder = len(objs) + 1
    add("PAGES")  # placeholder, replaced below
    for pi, pg in enumerate(pages):
        if isinstance(pg, dict) and pg.get("stamp"):
            a = float(pg.get("alpha", 0.18))
            objs[gs - 1] = f"<< /Type /ExtGState /ca {a} /CA {a} >>".encode()
            txt = str(pg["stamp"])
            fs = max(28, min(96, int(900 / max(len(txt), 1))))
            stream = f"q /GS1 gs 0.45 0.45 0.45 rg BT /F1 {fs} Tf 0.7071 0.7071 -0.7071 0.7071 {size[0] * 0.22:.0f} {size[1] * 0.28:.0f} Tm {_pdf_str(txt)} Tj ET Q"
        else:
            lines = [str(x) for x in (pg or [])]
            stream = "BT /F1 14 Tf 16 TL 56 780 Td " + " ".join(f"{_pdf_str(ln)} Tj T*" for ln in lines) + " ET"
        sb = stream.encode("latin-1", "replace")
        cid = add(b"<< /Length %d >>\nstream\n" % len(sb) + sb + b"\nendstream")
        annots = []
        if pi == 0 and fields:
            for f in fields:
                x, y, w, h = f.get("x", 56), f.get("y", 600), f.get("w", 200), f.get("h", 20)
                if f.get("type") == "check":
                    on = add(f"<< /Length 0 >>\nstream\n\nendstream")
                    annots.append(add(f"<< /Type /Annot /Subtype /Widget /FT /Btn /T {_pdf_str(f['name'])} /Rect [{x} {y} {x + h} {y + h}] /V /Off /AS /Off "
                                      f"/AP << /N << /Yes {on} 0 R /Off {on} 0 R >> >> /F 4 >>"))
                else:
                    annots.append(add(f"<< /Type /Annot /Subtype /Widget /FT /Tx /T {_pdf_str(f['name'])} /Rect [{x} {y} {x + w} {y + h}] /V () /DA (/F1 12 Tf 0 g) /F 4 >>"))
            annots_all += annots
        ann = (" /Annots [" + " ".join(f"{a} 0 R" for a in annots) + "]") if annots else ""
        page_ids.append(add(f"<< /Type /Page /Parent {pages_id_placeholder} 0 R /MediaBox [0 0 {size[0]} {size[1]}] "
                            f"/Resources << /Font << /F1 {font} 0 R >> /ExtGState << /GS1 {gs} 0 R >> >> /Contents {cid} 0 R{ann} >>"))
    objs[pages_id_placeholder - 1] = f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] /Count {len(page_ids)} >>".encode()
    acro = ""
    if annots_all:
        acro = f" /AcroForm << /Fields [{' '.join(f'{a} 0 R' for a in annots_all)}] /DA (/F1 12 Tf 0 g) /DR << /Font << /F1 {font} 0 R >> >> /NeedAppearances true >>"
    cat = add(f"<< /Type /Catalog /Pages {pages_id_placeholder} 0 R{acro} >>")
    buf = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(buf))
        buf += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(buf)
    buf += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    buf += f"trailer\n<< /Size {len(objs) + 1} /Root {cat} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(buf))
    return out


# ------------------------------------------------------------------------------------------------ pypdf / pdfplumber
def merge(inputs: list, out) -> Path:
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in inputs:
        w.append(str(p))
    with open(out, "wb") as f:
        w.write(f)
    return Path(out)


def _ranges(spec: str, n: int) -> list[list[int]]:
    groups = []
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            groups.append(list(range(int(a) - 1, min(int(b), n))))
        else:
            groups.append([int(part) - 1])
    return groups or [[i] for i in range(n)]


def split(src, outdir, ranges: str = "") -> list[Path]:
    from pypdf import PdfReader, PdfWriter
    r = PdfReader(str(src))
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    outs = []
    for gi, grp in enumerate(_ranges(ranges, len(r.pages)), 1):
        w = PdfWriter()
        for i in grp:
            if 0 <= i < len(r.pages):
                w.add_page(r.pages[i])
        p = outdir / f"{Path(src).stem}-{gi:02d}.pdf"
        with open(p, "wb") as f:
            w.write(f)
        outs.append(p)
    return outs


def fields(src) -> dict:
    from pypdf import PdfReader
    return {k: (v.get("/V") if isinstance(v, dict) else v) for k, v in (PdfReader(str(src)).get_fields() or {}).items()}


def fill_form(src, out, values: dict) -> dict:
    from pypdf import PdfReader, PdfWriter
    if Path(out).resolve() == Path(src).resolve():
        raise ValueError("out must differ from the source")
    r = PdfReader(str(src))
    w = PdfWriter(clone_from=r)
    names = set((r.get_fields() or {}).keys())
    vals = {k: ("/Yes" if v is True else ("/Off" if v is False else str(v))) for k, v in values.items() if k in names}
    for page in w.pages:
        w.update_page_form_field_values(page, vals, auto_regenerate=False)
    w.set_need_appearances_writer(True)
    with open(out, "wb") as f:
        w.write(f)
    return {"filled": list(vals), "missing": [k for k in values if k not in names], "out": str(out)}


def extract_text(src) -> list[str]:
    from pypdf import PdfReader
    return [(p.extract_text() or "") for p in PdfReader(str(src)).pages]


def extract_tables(src) -> list[list]:
    import pdfplumber
    out = []
    with pdfplumber.open(str(src)) as pdf:
        for pg in pdf.pages:
            out.append(pg.extract_tables())
    return out


def watermark(src, out, text: str = "DRAFT", alpha: float = 0.18, stamp_pdf=None) -> Path:
    """Stamp every page. ASCII text is drawn here; for Korean text make a stamp PDF via the HTML route and pass stamp_pdf."""
    from pypdf import PdfReader, PdfWriter
    r = PdfReader(str(src))
    if stamp_pdf is None:
        if any(ord(ch) > 255 for ch in text):
            raise ValueError("한글 워터마크는 stamp_pdf가 필요해요 (doc_html로 만든 한 쪽 PDF)")
        made = workdir.make("stamp", near=out)
        tmp = made / "stamp.pdf"
        box = r.pages[0].mediabox
        mini_pdf([{"stamp": text, "alpha": alpha}], tmp, size=(float(box.width), float(box.height)))
        stamp_pdf = tmp
    else:
        made = None
    try:
        stamp = PdfReader(str(stamp_pdf)).pages[0]
        w = PdfWriter(clone_from=r)
        for pg in w.pages:
            pg.merge_page(stamp)
        with open(out, "wb") as f:
            w.write(f)
    finally:
        if made is not None:
            workdir.cleanup(made)
    return Path(out)


def to_png(src, outdir, scale: float = 1.4) -> list[Path]:
    import pypdfium2 as pdfium
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(src))
    outs = []
    for i in range(len(doc)):
        img = doc[i].render(scale=scale).to_pil()
        p = outdir / f"{Path(src).stem}-p{i + 1}.png"
        img.save(p)
        outs.append(p)
    return outs


# ------------------------------------------------------------------------------------------------ HTML -> PDF (heavy: opens a browser)
def _browser_exe() -> str:
    """Path of Chrome / Edge on this PC ('' if none). ensure.find_system_browser() gives only the Playwright channel name."""
    import os
    local = os.environ.get("LOCALAPPDATA", "")
    for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              str(Path(local) / "Google" / "Chrome" / "Application" / "chrome.exe") if local else "",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/microsoft-edge"):
        if c and Path(c).exists():
            return c
    for n in ("google-chrome", "chromium", "chrome", "msedge"):
        if shutil.which(n):
            return shutil.which(n)
    return ""


def html_to_pdf(html_path, pdf) -> dict:
    """Print our A4 HTML to PDF: Playwright with the PC's Chrome/Edge (or its own Chromium), else the browser's --print-to-pdf."""
    html_path, pdf = Path(html_path).resolve(), Path(pdf).resolve()
    blocked = workdir.browser_blocked()
    if blocked:  # an agent's security box: neither Playwright nor Chrome's own print can start, so do not wait for both to fail
        workdir.say_no_browser(blocked)
        return {"ok": False, "how": "", "path": "", "no_browser": True,
                "error": "이 실행 환경에서는 브라우저를 띄울 수 없어 PDF로 바꾸지 못했어요: 만든 웹 문서를 크롬/엣지에서 열고 Ctrl+P → PDF로 저장 (또는 보안 상자 밖에서 같은 명령을 다시 실행)"}
    channel = ""
    try:
        import ensure
        channel = ensure.find_system_browser()
    except Exception:  # noqa: BLE001
        pass
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                b = p.chromium.launch(channel=channel) if channel else p.chromium.launch()
            except Exception:  # noqa: BLE001
                b = p.chromium.launch()
            pg = b.new_page()
            pg.goto(html_path.as_uri())
            pg.wait_for_timeout(300)
            pg.pdf(path=str(pdf), format="A4", print_background=True, prefer_css_page_size=True)
            b.close()
        if pdf.exists():
            return {"ok": True, "how": "playwright" + (f" ({channel})" if channel else ""), "path": str(pdf)}
    except Exception:  # noqa: BLE001
        pass
    exe = _browser_exe()
    if exe:
        with workdir.temp_dir("chrome-profile", near=pdf) as prof:
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={prof}",
                            f"--print-to-pdf={pdf}", html_path.as_uri()], capture_output=True, timeout=120)
        if pdf.exists() and pdf.stat().st_size > 800:
            return {"ok": True, "how": "browser print", "path": str(pdf)}
    return {"ok": False, "how": "", "path": "", "error": "PDF로 바꿀 브라우저가 없어요: 만든 웹 문서를 크롬/엣지에서 열고 Ctrl+P → PDF로 저장"}


def has_browser() -> bool:
    try:
        import ensure
        return bool(ensure.find_system_browser()) or bool(_browser_exe())
    except Exception:  # noqa: BLE001
        return False
