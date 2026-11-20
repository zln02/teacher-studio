#!/usr/bin/env python3
"""「같은 부탁, 다른 결과」의 「그냥 AI」 쪽 화면을 하네스 쪽과 같은 크기(틀을 가득)로 다시 찍어요.

Usage (Windows):  set PYTHONUTF8=1 && py docs/training/deck-v2-src/recapture_bare.py
원본은 docs/training/compare/raw/<사례>/bare/ 의 결과물 그대로예요(내용은 손대지 않아요). 달라지는 것은 찍는 창 크기뿐:
결과물이 화면 가운데 좁은 기둥으로 나오는 경우(게임 · 표 · 답변 카드) 창을 그 폭에 맞춰 좁히고 배율을 올려 1600x900으로 찍어요.
그래서 하네스 쪽(1600x900 화면 가득)과 같은 크기로 읽혀요. 바깥 요청은 모두 막아요. 결과: deck-v2-src/compare-bare/<사례>-bare.png
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "compare" / "raw"
OUT = HERE / "compare-bare"
# (사례, 파일, 창 폭) : 창 높이는 폭의 9/16, 배율 = 1600 / 폭
SHOTS = [("game", "game/bare/light_game.html", 960), ("parents", "parents/bare/_render-0.html", 1600),
         ("data", "data/bare/_render.html", 860), ("law", "law/bare/_card.html", 1160)]


def main() -> int:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--mute-audio"])
        for case, rel, w in SHOTS:
            ctx = b.new_context(viewport={"width": w, "height": w * 9 // 16}, device_scale_factor=1600 / w)
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:")) else r.abort())
            pg = ctx.new_page()
            pg.goto((RAW / rel).resolve().as_uri())
            pg.wait_for_timeout(1500)
            out = OUT / f"{case}-bare.png"
            pg.screenshot(path=str(out))
            print(" ", out.name, w, "px 창")
            ctx.close()
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
