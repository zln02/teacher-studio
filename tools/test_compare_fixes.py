# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Fixes from docs/training/compare: clipped answers in rounded buttons (clipcheck), decoration keep-out, law_fetch fail-fast, cream+serif house look.
Run: py tools/test_compare_fixes.py   (browser tests skip when Playwright / Chrome is missing)"""
from __future__ import annotations

import http.server
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "skills" / "teacher-game" / "scripts"), str(ROOT / "skills" / "teacher-law" / "scripts"), str(ROOT / "shared" / "design")]
os.environ.setdefault("PYTHONUTF8", "1")
import ai_look  # noqa: E402
import clipcheck  # noqa: E402
import law_fetch  # noqa: E402

PAGE = """<!doctype html><meta charset=utf-8><body style="margin:0"><div id=scene><div class=screen>
<button class="choice ts-choice" style="position:absolute;left:20px;top:20px;width:390px;height:310px;border:6px solid #000;border-radius:999px;font:48px/1.5 sans-serif;padding:0;text-align:center">빛을 퍼뜨려 작은 허상을 만든다 그리고 더 길게</button>
<button class="choice ts-choice" style="position:absolute;left:440px;top:20px;width:390px;height:310px;border:6px solid #000;border-radius:72px;font:40px/1.3 sans-serif;padding:20px 30px">빛을 모아 실상을</button>
</div></div></body>"""


class Clip(unittest.TestCase):
    def test_pill_clips_and_roomy_button_does_not(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright missing")
        with sync_playwright() as p:
            b = None
            for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
                try:
                    b = p.chromium.launch(**kw)
                    break
                except Exception:
                    continue
            if b is None:
                self.skipTest("no browser")
            pg = b.new_page(viewport={"width": 900, "height": 400})
            pg.set_content(PAGE)
            pg.evaluate(clipcheck.CLIP_JS)
            res = pg.evaluate("window.__tsClip()")
            b.close()
        self.assertEqual(len(res), 1, res)
        self.assertIn("빛을 퍼뜨려", res[0][2])

    def test_decoration_keeps_out_of_text_band(self):
        js = (ROOT / "skills" / "teacher-game" / "assets" / "themes" / "auto.js").read_text(encoding="utf-8")
        self.assertIn("function clear(", js)
        # 2026-11 design overhaul: the scattered memphis / bunting / confetti backdrops were retired. The matte backdrops draw only on the
        # stage edges and corners (blocks, papercut, halftone ...), so nothing can sit behind the title / question / answers band.
        for retired in ('kind === "memphis"', 'kind === "bunting"', 'kind === "neongrid"', 'kind === "glassblobs"'):
            self.assertNotIn(retired, js)
        for kept in ('kind === "blocks"', 'kind === "papercut"', 'kind === "dotgrid"', 'kind === "planes"'):
            self.assertIn(kept, js)


class Law(unittest.TestCase):
    def test_fail_fast_and_memory(self):
        law_fetch.MEMO = Path(tempfile.mkdtemp()) / "blocked.json"

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/slow":
                    time.sleep(3)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(("<title>t</title>" + "법 조문 " * 80).encode())

            def log_message(self, *a):
                pass
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_port}"
        t0 = time.time()
        r = law_fetch.run([(base + "/slow", "공식"), (base + "/ok", "보조")], timeout=1.0, budget=20, chars=200)
        self.assertLess(time.time() - t0, 5)
        self.assertEqual(r["result"]["label"], "보조")  # official one timed out ONCE, then the labelled fallback answered
        self.assertEqual(len(r["tries"]), 2)
        r2 = law_fetch.run([(base + "/slow", "공식"), (base + "/ok", "보조")], timeout=1.0, budget=20, chars=200)
        self.assertTrue(r2["tries"][0]["secs"] == 0.0 and "건너뜀" in r2["tries"][0]["why"])  # remembered, no second wait
        srv.shutdown()


class House(unittest.TestCase):
    def test_cream_serif_any_accent(self):
        self.assertTrue(ai_look.is_house("#f6f4ef", ["#b08d3c"], "Noto Serif KR"))
        sys.path.insert(0, str(ROOT / "shared" / "design"))
        import styles
        p = styles.STYLES["minimal-premium"]
        self.assertFalse(ai_look.is_house(p["pal"]["bg1"], [p["pal"]["accent"]], p["font"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
