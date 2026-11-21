#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Draw a .pptx as PNG so a person (or the model) can LOOK at it.

    py pptx_render.py deck.pptx --out review/ [--yes]

mode "libreoffice": real rendering (soffice -> PDF -> PNG via pypdfium2). LibreOffice is large (~350MB): only with the teacher's yes (--yes).
mode "sketch":      no browser can start here (an agent's security box): a Pillow-only rough drawing (pptx_sketch.py).
mode "approx":      no LibreOffice -> HTML+SVG drawn from the pptx XML (pptx_draw.py: shapes, lines and arrows, pictures, tables,
                    native charts, groups, master/layout art, text styles) screenshotted with the system Chrome/Edge.
                    APPROXIMATE: fonts, line breaks and autofit differ from PowerPoint. Boxes whose text is
                    estimated to overflow get a red outline. Always say so when showing it.
"""
from __future__ import annotations

import argparse
import subprocess
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
try:
    import workdir  # shared/tools: work folders without %TEMP%, the no-browser probe
except ImportError:
    workdir = None
APPROX_NOTE = "대략의 미리보기예요 (도형 위치로 그린 그림: 글꼴·줄바꿈·글자 넘침은 실제 PowerPoint와 달라요). 실제 확인은 PowerPoint에서 한 번 열어 보세요."


def _sheet(pngs, dest: Path, cols: int = 2, tw: int = 800):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in pngs]
    if not ims:
        return None
    th = int(tw * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (tw * cols, th * rows), "#222222")
    for i, im in enumerate(ims):
        sh.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    sh.save(dest)
    return dest


def pptx_to_html(path: Path, outdir: Path, overflow=()):
    """One HTML per slide, drawn from the pptx XML by pptx_draw (shapes, lines, pictures, tables, charts, groups, master/layout art).
    overflow = [(slide_no, text, ratio)] from pptx_check (outlined red)."""
    from pptx import Presentation
    import pptx_draw
    prs = Presentation(str(path))
    bad = {(n, t) for n, t, _ in overflow}
    fonts = pptx_draw.fonts_css(SKILL)
    files = []
    for i, s in enumerate(prs.slides, 1):
        f = outdir / f"_approx-{i:02d}.html"
        f.write_text(pptx_draw.slide_html(prs, s, fonts, bad, i), encoding="utf-8")
        files.append(f)
    return files


class _one_browser:
    """One preview browser at a time on this computer (two decks drawn at once make a slow PC crawl): a lock file, given up after 4 minutes."""

    def __enter__(self):
        import os
        import time
        try:
            self.p = workdir.named("teacher-studio-preview.lock") if workdir else Path(__import__("tempfile").gettempdir()) / "teacher-studio-preview.lock"
        except OSError:  # nowhere to keep a lock: draw without one
            self.p, self.own = None, False
            return self
        t0 = time.time()
        self.own = False
        while time.time() - t0 < 240:
            try:
                os.close(os.open(str(self.p), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                self.own = True
                break
            except FileExistsError:
                try:
                    if time.time() - self.p.stat().st_mtime > 300:  # left behind by a crashed run
                        self.p.unlink()
                        continue
                except OSError:
                    pass
                time.sleep(1.0)
            except OSError:
                break
        return self

    def __exit__(self, *exc):
        if self.own:
            try:
                self.p.unlink()
            except OSError:
                pass
        return False


def render(path: Path, out: Path, consent: bool = False, overflow=()) -> dict:
    """Returns {mode: 'libreoffice'|'approx', files: [sheet, png...], note}."""
    out.mkdir(parents=True, exist_ok=True)
    name = path.stem
    try:
        import ensure
    except ImportError:
        ensure = None
    lo = ensure.ensure_libreoffice(consent) if ensure and hasattr(ensure, "ensure_libreoffice") else {"ok": False, "prompt": ""}
    if lo["ok"]:
        tmp = out / ".lo-pdf"  # an ordinary folder inside the review folder (never tempfile.mkdtemp)
        tmp.mkdir(parents=True, exist_ok=True)
        subprocess.run([lo["path"], "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(path)], capture_output=True, text=True, timeout=240)
        pdf = tmp / (name + ".pdf")
        pdfium = ensure.ensure("pypdfium2", consent=True)  # tiny (~6MB), and LibreOffice is already agreed
        if pdf.exists() and pdfium["ok"]:
            import pypdfium2 as pdfium_mod
            doc = pdfium_mod.PdfDocument(str(pdf))
            pngs = []
            for i in range(len(doc)):
                p = out / f"{name}-{i + 1:02d}.png"
                doc[i].render(scale=1.2).to_pil().save(p)
                pngs.append(p)
            sheet = _sheet(pngs, out / f"{name}-sheet.png")
            doc.close()
            __import__("shutil").rmtree(tmp, ignore_errors=True)
            return {"mode": "libreoffice", "files": ([sheet] if sheet else []) + pngs, "note": "LibreOffice로 실제처럼 그렸어요. 그림을 보고 글자 넘침·겹침을 확인하세요."}
    blocked = workdir.browser_blocked() if workdir else ""
    if blocked:  # no browser can start here: do not wait for a launch to fail, draw the rough picture with Pillow instead
        return _sketch_result(path, out, overflow, blocked)
    files = pptx_to_html(path, out, overflow)  # no LibreOffice (or it failed): approximate drawing
    note = APPROX_NOTE + ("" if lo["ok"] else "  ※ " + lo["prompt"])
    try:
        from playwright.sync_api import sync_playwright
        ch = ensure.find_system_browser() if ensure else ""
        pngs = []
        with _one_browser(), sync_playwright() as pw:
            b = pw.chromium.launch(channel=ch) if ch else pw.chromium.launch()
            pg = b.new_page(viewport={"width": 1600, "height": 900})
            for f in files:
                pg.goto(f.resolve().as_uri())
                pg.wait_for_timeout(250)
                p = f.with_suffix(".png")
                pg.locator(".sl").first.screenshot(path=str(p))
                pngs.append(p)
            b.close()
        sheet = _sheet(pngs, out / f"{name}-approx-sheet.png")
        return {"mode": "approx", "files": ([sheet] if sheet else []) + pngs, "note": note}
    except Exception as exc:  # the browser did not start after all: same rough picture, the HTML files are still there
        r = _sketch_result(path, out, overflow, str(exc).splitlines()[0][:60])
        if r["mode"] == "sketch":
            return r
        return {"mode": "approx", "files": files, "note": note + f" (그림 저장은 건너뜀: {str(exc)[:60]})"}


def _sketch_result(path: Path, out: Path, overflow, why: str) -> dict:
    """The Pillow-only picture for places with no browser. One clear line, so nobody goes hunting for Chrome."""
    if workdir:
        workdir.say_no_browser(why)
    try:
        import pptx_sketch
        sheet, pngs = pptx_sketch.sketch(path, out, overflow)
        return {"mode": "sketch", "files": ([sheet] if sheet else []) + pngs, "note": pptx_sketch.SKETCH_NOTE}
    except Exception as exc:  # noqa: BLE001 - no Pillow either: the gate results still stand
        return {"mode": "none", "files": [], "note": f"미리보기 그림은 만들지 못했어요 ({str(exc)[:60]}). 점검 결과(FAIL/PASS 줄)로만 확인했어요."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--yes", action="store_true", help="the teacher agreed to install LibreOffice (large)")
    a = ap.parse_args()
    r = render(a.pptx, a.out, a.yes)
    print(r["mode"], r["note"])
    for f in r["files"][:1]:
        print("sheet:", f)
    return 0


def _no_browser_guard() -> bool:
    """True when no browser can start here (an agent's security box). shared/tools/workdir.py then prints ONE line and makes
    every screen check below skip at once instead of waiting for each launch to fail."""
    try:
        here = Path(__file__).resolve().parent
        for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
            if (d / "workdir.py").is_file():
                if str(d) not in sys.path:
                    sys.path.append(str(d))
                import workdir
                return workdir.guard_browser()
    except Exception:  # noqa: BLE001 - the guard must never stop a build
        pass
    return False


if __name__ == "__main__":
    _no_browser_guard()
    sys.exit(main())
