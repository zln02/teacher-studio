#!/usr/bin/env python3
"""Motion QA for deck-v2.html: frame strips of every build step on a stepped (fake) clock + numbers.

Usage: set PYTHONUTF8=1 && py docs/training/deck-v2-src/motion_qa.py --out DIR [--only 7,13] [--reduced] [--sheet]
  - The page clock is faked (Playwright page.clock): requestAnimationFrame / performance.now / setTimeout only move
    when this script advances them, so software WebGL being slow does not change what each frame shows.
  - CSS animations and transitions do not follow that clock, so they are paused and their currentTime is set by hand
    from the same stepped time.
  - Per build step: 10 frames at fixed offsets -> DIR/sNN.jpg (one row per step), plus metrics.json:
    settle (ms after which nothing changes), first (share of the change that happens in the first frame = "pop"),
    flash (direction changes of mean brightness per second).
  - --reduced: one end frame per step with reduced motion; reports steps whose end frame equals the previous one.
  - --sheet: write docs/training/deck-v2-motion-qa.png from the key frames (needs a full normal run in DIR).
One browser, one page at a time.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
DECK = HERE.parent / "deck-v2.html"
SHEET = HERE.parent / "deck-v2-motion-qa.png"
ARGS = ["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
OFF_2D = [0, 80, 160, 240, 340, 460, 620, 820, 1100, 1500]
OFF_3D = [0, 150, 300, 500, 750, 1050, 1450, 2000, 2700, 3600]
FW, FH = 384, 216

SYNC = """(t) => { var n = 0; document.getAnimations().forEach(function (a) {
  if (a.__done) return;
  if (a.__q === undefined) a.__q = t;
  try {
    var ct = Math.max(0, t - a.__q), end = a.effect && a.effect.getComputedTiming ? a.effect.getComputedTiming().endTime : Infinity;
    if (isFinite(end) && ct >= end) { a.finish(); a.__done = true; }   // 끝난 것은 한 번만 끝 상태로 (계속 건드리면 반투명 층이 덧칠돼 하얗게 떠요)
    else { a.pause(); a.currentTime = ct; }
    n++;
  } catch (e) {} }); return n; }"""


def launch(p):
    for ch in ("chrome", "msedge", None):
        try:
            return p.chromium.launch(channel=ch, args=ARGS) if ch else p.chromium.launch(args=ARGS)
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit("no Chromium found")


def font(sz):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", sz)
    except OSError:
        return ImageFont.load_default()


class Stage:
    def __init__(self, b, reduced):
        self.b, self.reduced, self.t = b, reduced, 0
        self.errors = []
        self.open()

    def open(self):
        self.ctx = self.b.new_context(viewport={"width": 960, "height": 540}, device_scale_factor=1,
                                      reduced_motion="reduce" if self.reduced else "no-preference")
        self.pg = self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.errors.append(str(e)))
        self.pg.clock.install(time=0)
        self.t = 0
        self.pg.goto(DECK.as_uri() + ("?reduced=1" if self.reduced else ""))
        for _ in range(400):
            self.adv(50)
            if self.pg.evaluate("!!(window.__deck && window.__deck.state().slide === 0)"):
                self.pg.clock.pause_at(3600000)   # 여기서부터 시간은 이 스크립트가 움직일 때만 가요
                self.adv(100)
                return
        raise SystemExit("deck did not boot")

    def reopen(self):
        self.ctx.close()
        self.open()

    def adv(self, ms):
        if ms > 0:
            self.pg.clock.run_for(ms)
            self.t += ms
        self.pg.evaluate(SYNC, self.t)

    def shot(self):
        return Image.open(io.BytesIO(self.pg.screenshot(timeout=180000))).convert("RGB")


def metrics(frames, offs):
    g = [f.resize((240, 135)).convert("L") for f in frames]
    d = [ImageStat.Stat(ImageChops.difference(g[k], g[k + 1])).mean[0] for k in range(len(g) - 1)]
    tot = ImageStat.Stat(ImageChops.difference(g[0], g[-1])).mean[0]
    eps = 0.12
    settle = 0
    for k in range(len(d) - 1, -1, -1):
        if d[k] > eps:
            settle = offs[k + 1]
            break
    lum = [ImageStat.Stat(x).mean[0] for x in g]
    flips, last = 0, 0
    for k in range(1, len(lum)):
        s = lum[k] - lum[k - 1]
        if abs(s) > 1.5:
            sg = 1 if s > 0 else -1
            if last and sg != last:
                flips += 1
            last = sg
    return {"settle": settle, "first": round(d[0] / max(1e-6, sum(d)), 2) if sum(d) > 0.3 else 0, "total": round(tot, 2),
            "moved": round(sum(d), 2), "flash": round(flips / (offs[-1] / 1000), 2), "d": [round(x, 2) for x in d]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--reduced", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.sheet:
        return sheet(out)
    res = {}
    with sync_playwright() as p:
        b = launch(p)
        S = Stage(b, a.reduced)
        n = S.pg.evaluate("window.__deck.count")
        only = [int(x) for x in a.only.split(",") if x] if a.only else list(range(1, n + 1))
        f18 = font(18)
        for i in range(n):
            if i + 1 not in only:
                continue
            S.reopen()   # 장마다 새 창: 소프트웨어 WebGL이 오래 돌면 메모리가 새요
            steps = S.pg.evaluate(f"window.__deck.steps({i})")
            is3d = S.pg.evaluate(f"!!document.querySelectorAll('.slide')[{i}].getAttribute('data-scene')")
            offs = OFF_3D if is3d else OFF_2D
            rows, prev_end = [], None
            for st in range(0, steps + 1):
                S.pg.evaluate(f"window.__deck.go({i}, {st})")
                if a.reduced:
                    S.adv(0)
                    S.adv(300)
                    S.adv(600)
                    end = S.shot()
                    same = prev_end is not None and ImageStat.Stat(ImageChops.difference(end.convert("L"), prev_end.convert("L"))).mean[0] < 0.05
                    res[f"{i + 1}.{st}"] = {"same_as_prev": bool(same)}
                    rows.append([end])
                    prev_end = end
                    continue
                fr, t0 = [], S.t
                S.adv(0)
                for k, o in enumerate(offs):
                    S.adv(t0 + o - S.t)
                    fr.append(S.shot())
                res[f"{i + 1}.{st}"] = metrics(fr, offs)
                rows.append(fr)
            cols = max(len(r) for r in rows)
            im = Image.new("RGB", (cols * FW, len(rows) * (FH + 22)), (10, 11, 13))
            dr = ImageDraw.Draw(im)
            for r, fr in enumerate(rows):
                for k, f in enumerate(fr):
                    im.paste(f.resize((FW, FH), Image.LANCZOS), (k * FW, r * (FH + 22) + 22))
                    lab = f"s{i + 1} step {r}" + ("" if a.reduced else f"  +{offs[k]}ms")
                    dr.text((k * FW + 6, r * (FH + 22)), lab, fill=(200, 196, 186), font=f18)
            im.save(out / f"s{i + 1:02d}.jpg", quality=80)
            for r, fr in enumerate(rows):   # 열쇠 장면(끝 모습)은 따로: 시트용
                fr[-1].save(out / f"k{i + 1:02d}_{r}.jpg", quality=84)
                if not a.reduced and len(fr) > 4:
                    fr[4].save(out / f"m{i + 1:02d}_{r}.jpg", quality=84)
            print(f"{i + 1:02d} steps={steps}", " ".join(
                (("=" if v.get("same_as_prev") else "ok") if a.reduced else f"{v['settle']}/{v['first']}/{v['flash']}")
                for k2, v in res.items() if k2.startswith(f"{i + 1}.")), flush=True)
        b.close()
        if S.errors:
            print("page errors:", S.errors[:5])
    name = "metrics-reduced.json" if a.reduced else "metrics.json"
    old = json.loads((out / name).read_text(encoding="utf-8")) if (out / name).exists() and a.only else {}
    old.update(res)
    (out / name).write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def sheet(out: Path) -> int:
    """Key frames after the fixes: for every slide, the mid-motion frame and the end frame of each build step."""
    ks = sorted(out.glob("k*_*.jpg"))
    slides = sorted({int(p.stem[1:3]) for p in ks})
    tw, th, pad, lab = 240, 135, 6, 20
    items = []
    for s in slides:
        steps = sorted(int(p.stem.split("_")[1]) for p in out.glob(f"k{s:02d}_*.jpg"))
        for st in steps:
            m = out / f"m{s:02d}_{st}.jpg"
            if st and m.exists():
                items.append((f"{s}.{st} 움직이는 중", m))
            items.append((f"{s}.{st} 끝", out / f"k{s:02d}_{st}.jpg"))
    cols = 12
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad), (14, 16, 19))
    dr = ImageDraw.Draw(im)
    f = font(14)
    for k, (name, p) in enumerate(items):
        x, y = pad + (k % cols) * (tw + pad), pad + (k // cols) * (th + lab + pad)
        im.paste(Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y + lab))
        dr.text((x + 2, y), name, fill=(243, 240, 233), font=f)
    im.save(SHEET, optimize=True)
    print("sheet:", SHEET, im.size, f"{SHEET.stat().st_size / 1e6:.2f} MB", len(items), "frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
