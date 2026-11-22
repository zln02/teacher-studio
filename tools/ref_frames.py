# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Study reference videos: dense frame strips -> one contact sheet per video (dev tool, not a skill dependency; no ffmpeg).

How: Playwright opens the video in Edge (channel="msedge"; falls back to the bundled Chromium), seeks the <video> element to each time,
screenshots just the video, and Pillow lays the frames out with their timestamps. Works for local files (mp4/webm the browser can play)
and for pages that hold a <video> element (a direct video URL, or a page such as a video site: the first playing <video> is used).
Respect the source's terms: frames are for studying motion and layout, never for re-publishing.

    py tools/ref_frames.py clip.mp4 https://example.com/v.mp4 --every 0.5 --out ref-frames/
    py tools/ref_frames.py clip.mp4 --count 48 --start 10 --end 22 --cols 8 --width 320
Writes <out>/<name>-sheet.png (+ the single frames with --keep). One browser at a time; closes it on exit.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


def times(duration: float, every: float = 0.0, count: int = 0, start: float = 0.0, end: float = 0.0, cap: int = 240) -> list[float]:
    """Seek times (seconds) inside [start, end): every N seconds, or `count` evenly spaced; never more than `cap`."""
    end = min(end or duration, duration)
    start = max(0.0, min(start, end))
    span = max(0.0, end - start)
    if span <= 0:
        return [round(start, 3)]
    if count:
        n = max(1, min(count, cap))
        return [round(start + span * (i + 0.5) / n, 3) for i in range(n)]
    step = every or max(span / 48, 0.1)
    out, t = [], start
    while t < end and len(out) < cap:
        out.append(round(t, 3))
        t += step
    return out


def label(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def slug(src: str) -> str:
    base = re.sub(r"[?#].*$", "", src.rstrip("/")).split("/")[-1] or "video"
    return re.sub(r"[^\w가-힣.-]+", "_", Path(base).stem)[:48] or "video"


def sheet(frames: list, labels: list[str], dest: Path, cols: int = 6, width: int = 320) -> Path:
    """Contact sheet: frames (PIL images) in a grid, each with its timestamp under it."""
    from PIL import Image, ImageDraw
    if not frames:
        raise ValueError("no frames")
    w = width
    h = max(1, round(frames[0].height * w / max(1, frames[0].width)))
    lab = 22
    rows = (len(frames) + cols - 1) // cols
    out = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + lab + 8) + 8), (24, 24, 26))
    d = ImageDraw.Draw(out)
    for i, (im, tx) in enumerate(zip(frames, labels)):
        x, y = 8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + lab + 8)
        out.paste(im.convert("RGB").resize((w, h)), (x, y))
        d.text((x + 2, y + h + 4), tx, fill=(220, 218, 212))
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest)
    return dest


PAGE = """<!doctype html><meta charset="utf-8"><body style="margin:0;background:#000">
<video id="v" src="%s" muted playsinline preload="auto" style="display:block;max-width:100vw;max-height:100vh"></video>"""

SEEK_JS = """async (t) => {
  const v = document.querySelector('video'); if (!v) return false;
  v.pause();
  await new Promise(r => { const done = () => { v.removeEventListener('seeked', done); r(); }; v.addEventListener('seeked', done); v.currentTime = t; setTimeout(done, 4000); });
  return true;
}"""


def capture(src: str, out: Path, every: float, count: int, start: float, end: float, cols: int, width: int, keep: bool) -> Path:
    from playwright.sync_api import sync_playwright
    from PIL import Image
    import io
    out.mkdir(parents=True, exist_ok=True)
    name = slug(src)
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="msedge")
        except Exception:
            b = p.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": 1280, "height": 720})
            if re.match(r"^https?://", src) and not re.search(r"\.(mp4|webm|m4v|mov|ogv)(\?|$)", src, re.I):
                pg.goto(src, wait_until="domcontentloaded", timeout=60000)
            else:
                url = src if re.match(r"^https?://", src) else Path(src).resolve().as_uri()
                html = out / f".{name}-player.html"
                html.write_text(PAGE % url, encoding="utf-8")
                pg.goto(html.resolve().as_uri())
            pg.wait_for_function("() => { const v = document.querySelector('video'); return v && v.readyState >= 1 && isFinite(v.duration) && v.duration > 0; }", timeout=60000)
            dur = pg.evaluate("document.querySelector('video').duration")
            ts = times(dur, every, count, start, end)
            frames, labs = [], []
            vid = pg.locator("video").first
            for i, t in enumerate(ts):
                pg.evaluate(SEEK_JS, t)
                png = vid.screenshot()
                im = Image.open(io.BytesIO(png))
                frames.append(im)
                labs.append(label(t))
                if keep:
                    im.save(out / f"{name}-{i:03d}.png")
            dest = sheet(frames, labs, out / f"{name}-sheet.png", cols, width)
            print(f"{src}: {len(frames)} frames over {dur:.1f}s -> {dest}")
            return dest
        finally:
            b.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", help="video files or URLs")
    ap.add_argument("--every", type=float, default=0.0, help="seconds between frames (default: 48 frames over the span)")
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=0.0)
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--width", type=int, default=320)
    ap.add_argument("--keep", action="store_true", help="also save every frame")
    ap.add_argument("--out", type=Path, default=Path("ref-frames"))
    a = ap.parse_args()
    bad = 0
    for src in a.sources:   # one video, one browser at a time
        try:
            capture(src, a.out, a.every, a.count, a.start, a.end, a.cols, a.width, a.keep)
        except Exception as exc:  # noqa: BLE001 - report and go on with the next video
            bad += 1
            print(f"FAIL {src}: {str(exc).splitlines()[0][:160]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
