# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Play a finished game page with a scripted 'student' and record a GIF (used by capture_example.py).

The player reads each question from the page, looks the right answer up in the same
content.json that built the game, and clicks it - so the GIF is a real play-through.
Only the first stretch and the finale are recorded; the middle is played without frames.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from capture_example import open_page, realtime, save_gif


def _wait_click(tab, selector: str, timeout: int = 12000) -> None:
    tab.wait_for_selector(selector, state="visible", timeout=timeout)
    tab.click(selector)


def play_quiz(tab, content: dict, frames, durs, rec_questions: int) -> None:
    """quiz-show: answer every question correctly; record title, first questions, result."""
    answers = {i["q"]: i for i in content["items"]}
    realtime(tab, frames, durs, 1500)
    tab.click("#t-start")
    for n in range(len(content["items"])):
        tab.wait_for_selector(".choice, .qs-oxch button", state="visible", timeout=15000)
        text = tab.inner_text("body")
        item = next(v for q, v in answers.items() if q in text)
        rec = n < rec_questions
        if rec:
            realtime(tab, frames, durs, 1100)
        if item["type"] == "mc":
            tab.locator(".choice", has_text=item["choices"][item["answer"]]).first.click()
        else:
            tab.locator(".qs-oxch button, .choice").nth(item["answer"]).click()
        if rec:
            realtime(tab, frames, durs, 1900)
        else:
            tab.wait_for_timeout(700)
        for _ in range(12):  # press the visible 'next' style button (or Space) until the next question shows
            nxt = tab.locator("button.btn:visible").first
            if nxt.count():
                nxt.click()
                break
            tab.keyboard.press("Space")
            tab.wait_for_timeout(500)
        tab.wait_for_timeout(500)
    realtime(tab, frames, durs, 2200)  # finale scene
    tab.locator("button.btn:visible").first.click()  # 'see result'
    realtime(tab, frames, durs, 2600)


def play_drag(tab, content: dict, frames, durs, rec_items: int) -> None:
    """drag-deliver: send every item to its right place with real mouse drags."""
    answers = {i["q"]: i["a"] for i in content["items"]}
    realtime(tab, frames, durs, 1500)
    tab.click("#t-start")
    for n in range(len(content["items"])):
        tab.wait_for_selector(".dd-q", state="visible", timeout=15000)
        tab.wait_for_timeout(900)
        q = tab.inner_text(".dd-q").strip()
        dest = tab.locator(".dd-dest", has=tab.locator(".dd-lab", has_text=answers[q])).first
        item = tab.locator(".dd-q").first
        rec = n < rec_items
        if rec:
            realtime(tab, frames, durs, 800)
        ib, db = item.bounding_box(), dest.bounding_box()
        tab.mouse.move(ib["x"] + ib["width"] / 2, ib["y"] + ib["height"] / 2)
        tab.mouse.down()
        steps = 8
        for s in range(1, steps + 1):
            tab.mouse.move(ib["x"] + ib["width"] / 2 + (db["x"] + db["width"] / 2 - ib["x"] - ib["width"] / 2) * s / steps,
                           ib["y"] + ib["height"] / 2 + (db["y"] + db["height"] / 3 - ib["y"] - ib["height"] / 2) * s / steps)
            if rec:
                realtime(tab, frames, durs, 60)
        tab.mouse.up()
        if rec:
            realtime(tab, frames, durs, 2200)
        else:
            tab.wait_for_timeout(900)
        for _ in range(10):
            nxt = tab.locator(".dd-next:visible, button.btn:visible").first
            if nxt.count():
                nxt.click()
                break
            tab.wait_for_timeout(400)
    realtime(tab, frames, durs, 2200)
    if tab.locator("button.btn:visible").count():
        tab.locator("button.btn:visible").first.click()
    realtime(tab, frames, durs, 2600)


def do_play(page: Path, out: Path, script: str, content: Path | None = None, rec: int = 2) -> None:
    from playwright.sync_api import sync_playwright
    data = json.loads(content.read_text(encoding="utf-8")) if content else {}
    with sync_playwright() as pw:
        browser, tab, errors = open_page(pw, page)
        frames, durs = [], []
        (play_quiz if script == "quiz" else play_drag)(tab, data, frames, durs, rec)
        browser.close()
    print("page errors:", errors or 0)
    save_gif(frames, durs, out, 40)
