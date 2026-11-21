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
    if _no_browser_guard():
        print("SKIP 화면 그림은 건너뜀 (이 환경에서는 브라우저를 띄울 수 없어요)")
        return 2
    shoot(a.html, a.out, 390 if a.mobile else a.width, 800 if a.mobile else 900)
    print("OK", a.out)
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
