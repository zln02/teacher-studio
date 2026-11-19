#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Full-page screenshot of a report (for review). Needs Playwright (system Chrome first, audio muted). Nothing leaves the computer.

    python3 shots.py report.html out.png [--width 1100] [--mobile]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tdata  # noqa: E402


def shoot(src: Path, out: Path, width: int = 1100, height: int = 900) -> None:
    import ensure
    from playwright.sync_api import sync_playwright
    pw_info = ensure.ensure_playwright()
    with sync_playwright() as pw:
        kw = {"channel": pw_info["channel"]} if pw_info.get("channel") else {}
        br = pw.chromium.launch(args=["--mute-audio"], **kw)
        pg = br.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        pg.route("**/*", lambda route: route.continue_() if route.request.url.startswith(("file:", "data:")) else route.abort())
        pg.goto(src.resolve().as_uri())
        pg.wait_for_selector("html[data-charts-ready='1']", state="attached", timeout=8000)
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(out), full_page=True)
        br.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--width", type=int, default=1100)
    ap.add_argument("--mobile", action="store_true")
    a = ap.parse_args()
    shoot(a.html, a.out, 390 if a.mobile else a.width, 800 if a.mobile else 900)
    print("OK", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
