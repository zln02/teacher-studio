"""Render a stage page (motion / typography) to an exact-frame MP4.

Usage:
    python3 render_mp4.py page.html out.mp4 [--fps 30] [--max-mb 30] [--seconds N]

Needs: Python Playwright with Chromium, and ffmpeg. Where these are missing (e.g. a plain
chat sandbox), use the page's own 🎥 button instead: it records the tab in Chrome to .webm.
Frames are captured by seeking the page's registered timelines (window.__stage.seek),
so the video is smooth even on a slow machine.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def render(page: Path, out: Path, fps: int, max_mb: float, seconds: float | None) -> None:
    """Capture every frame with Playwright and encode with ffmpeg under a size budget."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright not installed: use the 🎥 button in the page (Chrome) instead.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found: use the 🎥 button in the page (Chrome) instead.")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        tab = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        tab.goto(page.resolve().as_uri())
        tab.wait_for_function("window.__stage && window.__stage.ready", timeout=15000)
        tab.wait_for_timeout(1200)  # fonts
        duration_ms = seconds * 1000 if seconds else tab.evaluate("window.__stage.duration")
        if not duration_ms:
            raise SystemExit("page registered no timeline (STAGE.timeline) - nothing to render")
        tab.evaluate("window.__stage.manual()")
        frames = int(duration_ms / 1000 * fps) + 1
        kbps = int(max_mb * 8 * 1024 * 0.92 / max(duration_ms / 1000, 1))
        cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-b:v", f"{min(kbps, 12000)}k",
               "-maxrate", f"{min(kbps, 12000)}k", "-bufsize", f"{min(kbps, 12000) * 2}k", "-movflags", "+faststart", str(out)]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        assert enc.stdin is not None
        for i in range(frames):
            tab.evaluate(f"window.__stage.seek({i * 1000 / fps:.3f})")
            enc.stdin.write(tab.screenshot(type="png"))
            if i % (fps * 2) == 0:
                print(f"\r{i}/{frames} frames", end="", file=sys.stderr)
        enc.stdin.close()
        enc.wait()
        browser.close()
    print(f"\nrendered {out} ({out.stat().st_size / 1024 / 1024:.1f} MB, {duration_ms / 1000:.1f}s @ {fps}fps)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--max-mb", type=float, default=30)
    ap.add_argument("--seconds", type=float)
    a = ap.parse_args()
    render(a.page, a.out, a.fps, a.max_mb, a.seconds)


if __name__ == "__main__":
    main()
