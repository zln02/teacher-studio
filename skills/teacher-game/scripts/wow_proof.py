#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Evidence for the Game Wow kit: short GIFs of the key moments + a before/after contact sheet for the SAME spec.

Usage:
    python3 wow_proof.py --spec assets/spec-examples/j-tv-quiz-dokdo.json --seed 21 --out ../../../examples/design-review
Builds the spec twice (with the kit and with --no-juice), then in headless Chrome (audio muted/stubbed):
    wow-correct.gif   the correct-answer moment (squash, hit-stop, burst, kick, badge)      <= 3 MB
    wow-streak5.gif   the 5-in-a-row celebration
    wow-podium.gif    the final reveal: drumroll -> podium 3rd -> 2nd -> 1st (teams)
    wow-compare.png   before (no kit) / after (kit): question, correct moment, streak, final
GIF frames are real screenshots taken as fast as the machine allows (about 12-20 fps).
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
REPO = SKILL.parent.parent
sys.path.insert(0, str(REPO / "shared" / "juice"))
import juice_lint  # noqa: E402

VW, VH = 960, 540  # small viewport = fast screenshots; the stage scales to fit


def build(spec: Path, out: Path, seed: int, juice: bool) -> None:
    cmd = [sys.executable, str(HERE / "build.py"), "--spec", str(spec), "--out", str(out), "--seed", str(seed), "--no-fonts", "--no-check"]
    if not juice:
        cmd.append("--no-juice")
    subprocess.run(cmd, check=True, capture_output=True)


def launch(p):
    for kw in ({"channel": "chrome"}, {}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(args=["--mute-audio"], **kw)
        except Exception:
            continue
    raise SystemExit("no headless browser")


def new_page(b, html: Path):
    pg = b.new_page(viewport={"width": VW, "height": VH})
    pg.add_init_script(juice_lint.SILENT_JS)
    pg.goto(html.resolve().as_uri())
    pg.wait_for_timeout(900)
    pg.click("#t-start")
    pg.wait_for_timeout(4300)
    return pg


def grab(pg) -> Image.Image:
    return Image.open(io.BytesIO(pg.screenshot(type="jpeg", quality=72))).convert("RGB")


def record(pg, seconds: float, action=None, fire_at: float = 0.25):
    """Take screenshots for `seconds`; run `action` once after `fire_at` seconds. Returns [(t, image)]."""
    frames, t0, fired = [], time.time(), False
    while time.time() - t0 < seconds:
        t = time.time() - t0
        if action and not fired and t >= fire_at:
            action()
            fired = True
        frames.append((t, grab(pg)))
    return frames


def save_gif(frames, path: Path, width: int = 560, max_mb: float = 2.9, step: int = 1) -> int:
    sel = frames[::step]
    for colors, w in ((64, width), (48, int(width * 0.85)), (32, int(width * 0.7)), (32, int(width * 0.55))):
        imgs = []
        for _, im in sel:
            h = int(im.height * w / im.width)
            imgs.append(im.resize((w, h), Image.LANCZOS).quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE))
        durs = []
        for i, (t, _) in enumerate(sel):
            nxt = sel[i + 1][0] if i + 1 < len(sel) else t + 0.4
            durs.append(max(20, int((nxt - t) * 1000)))
        imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durs, loop=0, optimize=True, disposal=1)
        size = path.stat().st_size
        if size <= max_mb * 1024 * 1024:
            return size
    return path.stat().st_size


def click_correct(pg):
    pg.evaluate("window.GAME_LOGIC.auto()")  # the quiz autoplayer answers the first question correctly


def wait_feedback(pg, timeout=3.0):
    """Wait until the correct counter goes up (feedback just fired)."""
    t0 = time.time()
    base = pg.evaluate("NG.state.correct")
    while time.time() - t0 < timeout:
        if pg.evaluate("NG.state.correct") > base:
            return True
        pg.wait_for_timeout(15)
    return False


def font(size):
    for f in ("C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--seed", type=int, default=21)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    tmp = a.out / "_wow_tmp"
    tmp.mkdir(exist_ok=True)
    fixed = tmp / "spec.json"  # same questions in the same order for both builds
    sp = json.loads(a.spec.read_text(encoding="utf-8"))
    sp["shuffle"] = False
    fixed.write_text(json.dumps(sp, ensure_ascii=False), encoding="utf-8")
    after, before = tmp / "after.html", tmp / "before.html"
    build(fixed, after, a.seed, True)
    build(fixed, before, a.seed, False)
    from playwright.sync_api import sync_playwright

    sheet: dict[str, list[Image.Image]] = {"before": [], "after": []}
    with sync_playwright() as p:
        b = launch(p)
        for label, html in (("before", before), ("after", after)):
            # --- A. the correct-answer moment
            pg = new_page(b, html)
            q = grab(pg)
            frames = []
            t0 = time.time()
            pg.evaluate("window.GAME_LOGIC.auto()")
            fb = False
            shot = None
            while time.time() - t0 < 2.4:
                im = grab(pg)
                frames.append((time.time() - t0, im))
                if not fb and pg.evaluate("NG.state.correct") > 0:
                    fb = True
                    fb_t = time.time()
                if fb and shot is None and time.time() - fb_t > 0.22:
                    shot = im
            if label == "after":
                # trim: start 0.15s before the click, end 1.5 s after
                save_gif([(t, f) for t, f in frames if t <= 1.9], a.out / "wow-correct.gif", 540)
            sheet[label] += [q, shot or frames[-1][1]]
            pg.close()
            # --- B. streak 5 (combo preloaded with 4, then a correct answer)
            pg = new_page(b, html)
            pg.evaluate("NG.state.combo = 4; NG.state.maxCombo = 4")
            frames = []
            t0 = time.time()
            pg.evaluate("window.GAME_LOGIC.auto()")
            fb = False
            shot = None
            while time.time() - t0 < 2.6:
                im = grab(pg)
                frames.append((time.time() - t0, im))
                if not fb and pg.evaluate("NG.state.correct") > 0:
                    fb, fb_t = True, time.time()
                if fb and shot is None and time.time() - fb_t > 0.3:
                    shot = im
            if label == "after":
                save_gif([(t, f) for t, f in frames if t <= 2.2], a.out / "wow-streak5.gif", 540)
            sheet[label].append(shot or frames[-1][1])
            pg.close()
            # --- C. final: teams podium
            pg = new_page(b, html)
            pg.evaluate("(function(){ var s = NG.state; if (s.teams.length) { s.teams.forEach(function(t, i){ t.score = [850, 620, 410, 300, 200, 100][i]; }); } else { s.score = 850; s.correct = 8; } s.total = 10; NG.finish({total: 10, ratio: 0.8}); })()")
            frames = record(pg, 8.6)
            # the sheet takes the frame at ~6.8s (podium nearly complete); the old results screen is long settled by then
            fin = min(frames, key=lambda f: abs(f[0] - 6.8))[1]
            if label == "after":
                save_gif(frames[::2], a.out / "wow-podium.gif", 480, step=1)
            sheet[label].append(fin)
            pg.close()
        b.close()
    # contact sheet
    cw, ch, pad, head = 560, 315, 14, 96
    cols = ["문제 화면", "정답 직후 0.2초", "5연속 순간", "마지막 결과 (6.8초)"]
    W = pad + (cw + pad) * 4 + 150
    H = head + (ch + pad + 46) * 2 + pad
    img = Image.new("RGB", (W, H), (24, 24, 30))
    d = ImageDraw.Draw(img)
    d.text((pad, 14), "같은 spec · 같은 seed: 위 = 키트 없음(before), 아래 = Game Wow kit(after)", font=font(30), fill=(255, 255, 255))
    for ci, name in enumerate(cols):
        d.text((150 + pad + ci * (cw + pad), 62), name, font=font(22), fill=(255, 214, 90))
    for ri, label in enumerate(("before", "after")):
        y = head + ri * (ch + pad + 46)
        d.text((pad, y + ch // 2 - 14), "BEFORE" if label == "before" else "AFTER", font=font(34), fill=(255, 120, 120) if label == "before" else (120, 255, 160))
        for ci, im in enumerate(sheet[label]):
            x = 150 + pad + ci * (cw + pad)
            img.paste(im.resize((cw, ch), Image.LANCZOS), (x, y))
    img.save(a.out / "wow-compare.png", optimize=True)
    for f in ("wow-correct.gif", "wow-streak5.gif", "wow-podium.gif", "wow-compare.png"):
        fp = a.out / f
        print(f, round(fp.stat().st_size / 1024), "KB")
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    return 0


if __name__ == "__main__":
    sys.exit(main())
