# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Render a stage page (motion / typography) to an exact-frame MP4.

Usage:
    python3 render_mp4.py page.html out.mp4 [--fps 30] [--max-mb 30] [--seconds N]

Needs: Python Playwright with a browser, and ffmpeg. Both are found automatically (system Chrome/Edge first, system
ffmpeg first, else imageio-ffmpeg) via shared/tools/ensure.py; add --yes once the teacher agrees to the small installs.
Where they cannot be had (e.g. a plain chat sandbox), use the page's own 🎥 button: it records the tab in Chrome to .webm.
Frames are captured by seeking the page's registered timelines (window.__stage.seek),
so the video is smooth even on a slow machine.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE.parent / "shared" / "tools", _HERE.parent / "tools"):
    if _p.exists():
        sys.path.insert(0, str(_p))
try:
    import ensure  # shared/tools/ensure.py
except ImportError:
    ensure = None


def render(page: Path, out: Path, fps: int, max_mb: float, seconds: float | None, consent: bool = False) -> None:
    """Capture every frame with Playwright and encode with ffmpeg under a size budget."""
    channel, ffmpeg = "", shutil.which("ffmpeg")
    if ensure:
        pw_res = ensure.ensure_playwright(consent)
        if not pw_res["ok"]:
            raise SystemExit("ASK TEACHER: " + pw_res["prompt"] + "  (agree -> rerun with --yes; or use the 🎥 button in the page)")
        channel = pw_res["channel"]
        ff = ensure.ensure_ffmpeg(consent)
        if not ff["ok"]:
            raise SystemExit("ASK TEACHER: " + ff["prompt"] + "  (agree -> rerun with --yes; or use the 🎥 button in the page)")
        ffmpeg = ff["path"]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright not installed: use the 🎥 button in the page (Chrome) instead.")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found: use the 🎥 button in the page (Chrome) instead.")
    if fps <= 0 or max_mb <= 0 or (seconds is not None and seconds <= 0):
        raise ValueError("재생 시간, 프레임 수, 최대 크기는 0보다 커야 해요.")
    with tempfile.TemporaryDirectory(prefix=".teacher-video-", dir=out.parent) as staging:
        video = Path(staging) / "video.mp4"
        duration = _encode(sync_playwright, channel, ffmpeg, page, video, fps, max_mb, seconds)
        if not video.is_file() or video.stat().st_size == 0:
            raise OSError("영상 파일이 만들어지지 않았어요.")
        video.replace(out)
    print(f"\n영상 파일을 만들었어요. {out} ({out.stat().st_size / 1024 / 1024:.1f} MB, {duration:.1f}초)")


def _encode(sync_playwright, channel, ffmpeg, page, video, fps, max_mb, seconds):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel=channel) if channel else pw.chromium.launch()
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
               "-maxrate", f"{min(kbps, 12000)}k", "-bufsize", f"{min(kbps, 12000) * 2}k", "-movflags", "+faststart", str(video)]
        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as enc:
            try:
                for i in range(frames):
                    tab.evaluate(f"window.__stage.seek({i * 1000 / fps:.3f})")
                    enc.stdin.write(tab.screenshot(type="png"))
                    if i % (fps * 2) == 0:
                        print(f"\r{i}/{frames}", end="", file=sys.stderr)
                enc.stdin.close()
                if enc.wait() != 0:
                    raise OSError("영상 파일로 바꾸지 못했어요.")
            except BaseException:
                if enc.poll() is None:
                    enc.kill()
                raise
        browser.close()
    return duration_ms / 1000


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--max-mb", type=float, default=30)
    ap.add_argument("--seconds", type=float)
    ap.add_argument("--yes", action="store_true", help="the teacher agreed to install the small tools that are missing")
    a = ap.parse_args()
    try:
        render(a.page, a.out, a.fps, a.max_mb, a.seconds, a.yes)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"영상 파일을 만들지 못했어요. {exc}") from exc


if __name__ == "__main__":
    main()
