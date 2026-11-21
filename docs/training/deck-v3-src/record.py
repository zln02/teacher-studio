#!/usr/bin/env python3
"""deck-v3: click-by-click preview video + key-frame sheet + QA (overflow, console errors, frame rate).

Usage (Windows):  set PYTHONUTF8=1 && py docs/training/deck-v3-src/record.py --out DIR [--slides 1-7] [--fps 24] [--size 1280x720]
                  ... --qa-only        (skip the video; overflow + errors + reduced-motion check)
                  ... --fps-check      (real clock, no fake time: measures frame intervals per slide)
  - The page clock is faked (Playwright page.clock, the same idea as deck-v2-src/motion_qa.py): requestAnimationFrame,
    performance.now and setTimeout only move when this script advances them, so a slow PC or software WebGL does not
    change what each frame shows. CSS animations are paused and stepped from the same time.
  - Video: DIR/preview.mp4 (ffmpeg from imageio-ffmpeg) and DIR/preview.gif (small). Sheet: DIR/sheet.png (end frame of every click).
  - QA: the teacher-motion skill's clip probe (skills/teacher-motion/scripts/clipcheck.py, read-only) on the cards, plus a
    stage-bounds probe and a text-overflow probe at the end of every step, at 1920x1080. Report: DIR/qa.json.
One browser at a time.
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DECK = HERE.parent / "deck-v3.html"
QUERY = ""   # 예: "?robot=3d"
ARGS = ["--mute-audio", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
sys.path.insert(0, str(REPO / "skills" / "teacher-motion" / "scripts"))
from clipcheck import CLIP_JS  # noqa: E402  (harness probe, read-only)

SYNC = """(t) => { var n = 0; document.getAnimations().forEach(function (a) {
  if (a.__done) return;
  if (a.__q === undefined) a.__q = t;
  try {
    var ct = Math.max(0, t - a.__q), end = a.effect && a.effect.getComputedTiming ? a.effect.getComputedTiming().endTime : Infinity;
    if (isFinite(end) && ct >= end) { a.finish(); a.__done = true; }
    else { a.pause(); a.currentTime = ct; }
    n++;
  } catch (e) {} }); return n; }"""

# 카드처럼 생긴 것에 data-fit을 달아 하네스 탐침(clipcheck)이 보게 해요
MARK = """() => { document.querySelectorAll('.slide.on .nt, .slide.on .tb, .slide.on .hc, .slide.on .pin b, .slide.on .hxapp .bar').forEach(function (e) { e.setAttribute('data-fit', ''); }); }"""
BOUNDS = """() => {
  var s = document.querySelector('.slide.on'), st = document.getElementById('stage').getBoundingClientRect(), k = st.width / 1920, out = [];
  s.querySelectorAll('h1,h2,h3,p,b,span,li,.kicker,.nt,.tb,.hc,.fi,.wtag3,.who,.mean,.ask,.shot,.kcp,.ub,.stamp,.card,.eqbar,.resp,.qr,.typebox,.timer,.scr').forEach(function (e) {
    var cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return;
    var o = 1, p = e; while (p && p !== s) { o *= parseFloat(getComputedStyle(p).opacity); p = p.parentElement; } if (o < 0.5) return;
    if (e.closest('.note') || e.closest('.labels') || e.closest('.foot')) return;
    var r = e.getBoundingClientRect(); if (r.width < 2) return;
    var x0 = (r.left - st.left) / k, y0 = (r.top - st.top) / k, x1 = (r.right - st.left) / k, y1 = (r.bottom - st.top) / k;
    var tag = (e.className && e.className.baseVal === undefined ? e.className : e.tagName) + ' 「' + (e.textContent || '').trim().slice(0, 24) + '」';
    if (x0 < 60 || y0 < 40 || x1 > 1860 || y1 > 1000) out.push(['edge', tag, Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1)]);
    if (e.scrollWidth > e.clientWidth + 2 && /hidden|clip/.test(cs.overflow + cs.overflowX)) out.push(['overflow', tag, e.scrollWidth, e.clientWidth]);
  });
  // 글자 덩어리끼리 겹침 (머리글 · 본문 블록만)
  var blocks = [].slice.call(s.querySelectorAll(':scope > .hd, .hero, .feed, .wall3, .ans, .mean, .hxgrid, .hxcap p, .hxpunch, .hxtm, .cover .who, .ask, .pair, .agenda, .kcap, .levels, .capline, .flow2, .eqbar, .body3, .timer, .tips, .resp, .qr, .bigno, .stamps, .ub')).filter(function (e) {
    var o = 1, p = e; while (p && p !== s) { o *= parseFloat(getComputedStyle(p).opacity); p = p.parentElement; } return o > 0.5 && getComputedStyle(e).visibility !== 'hidden' && e.getBoundingClientRect().width > 2; });
  for (var i = 0; i < blocks.length; i++) for (var j = i + 1; j < blocks.length; j++) {
    var a = blocks[i].getBoundingClientRect(), b = blocks[j].getBoundingClientRect();
    if (blocks[i].contains(blocks[j]) || blocks[j].contains(blocks[i])) continue;
    var ix = Math.min(a.right, b.right) - Math.max(a.left, b.left), iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ix > 4 && iy > 4) out.push(['overlap', blocks[i].className, blocks[j].className, Math.round(ix / k), Math.round(iy / k)]);
  }
  return out; }"""


def launch(p, args=ARGS):
    for ch in ("chrome", "msedge", None):
        try:
            return p.chromium.launch(channel=ch, args=args) if ch else p.chromium.launch(args=args)
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit("no Chromium found")


def font(sz):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", sz)
    except OSError:
        return ImageFont.load_default()


class Stage:
    def __init__(self, b, w, h, reduced=False, fake=True, start=1):
        self.t = 0
        self.errors = []
        self.ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1,
                                 reduced_motion="reduce" if reduced else "no-preference")
        self.pg = self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.errors.append("pageerror: " + str(e)))
        self.pg.on("console", lambda m: self.errors.append("console." + m.type + ": " + m.text) if m.type in ("error", "warning") else None)
        self.pg.add_init_script(CLIP_JS)
        self.fake = fake
        if fake:
            self.pg.clock.install(time=0)
            self.pg.clock.pause_at(1000)   # 처음부터 멈춰 둬요: 부팅 뒤에 시간을 건너뛰면 막 시작한 움직임이 한 번에 끝나 버려요
        self.pg.goto(DECK.as_uri() + QUERY + "#" + str(start))
        for _ in range(600):
            if fake:
                self.pg.clock.run_for(50)
            else:
                self.pg.wait_for_timeout(50)
            if self.pg.evaluate("!!(window.__deck && window.__deck.state().slide === %d)" % (start - 1)):
                return
        raise SystemExit("deck did not boot")

    def adv(self, ms):
        if ms > 0:
            self.pg.clock.run_for(ms)
            self.t += ms
        self.pg.evaluate(SYNC, self.t)

    def key(self, k="ArrowRight"):
        self.pg.keyboard.press(k)

    def state(self):
        return self.pg.evaluate("window.__deck.state()")

    def shot(self):
        return Image.open(io.BytesIO(self.pg.screenshot(timeout=180000))).convert("RGB")


def hold_ms(slide, step):
    if slide == 5:
        return 4200
    if slide == 6:
        return 3400
    if slide == 1:
        return 3000
    if slide == 4 and step == 0:
        return 3000
    if slide == 7 and step in (0, 2, 7):
        return 3200
    if slide == 13:
        return 4600 if step in (0, 3, 4, 5) else 3000
    if slide == 20:
        return 3600
    if slide == 19 and step == 1:
        return 3400
    if slide in (8, 21):
        return 3000
    return 2300


def video(a, out):
    w, h = map(int, a.size.split("x"))
    first, last = map(int, a.slides.split("-"))
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for f in frames_dir.glob("*.jpg"):
        f.unlink()
    keys = []
    dt = 1000 // a.fps
    n = 0
    with sync_playwright() as p:
        b = launch(p)
        S = Stage(b, w, h, start=first)
        S.adv(0)
        while True:
            st = S.state()
            sl, sp = st["slide"] + 1, st["step"]
            if sl > last:
                break
            total = hold_ms(sl, sp)
            k = 0
            while k * dt < total:
                S.adv(dt if k else 0)
                S.shot().save(frames_dir / f"f{n:05d}.jpg", quality=88)
                n += 1
                k += 1
            keys.append((sl, sp, frames_dir / f"f{n - 1:05d}.jpg"))
            print(f"  slide {sl} step {sp}: {k} frames", flush=True)
            S.key()
            S.adv(0)
            if S.state() == st:
                break
        errs = S.errors
        b.close()
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    stem = a.name or ("preview-slides%d-%d" % (first, last))
    mp4 = out / (stem + ".mp4")
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", str(frames_dir / "f%05d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(mp4)], check=True)
    gif = out / (stem + ".gif")
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
                    "fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    str(gif)], check=True)
    # 대표 장면 모음: 클릭마다 끝 모습 + 움직이는 중간 한 장씩
    tw, th = 480, 270
    cols = 4
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * (th + 34) + 12), (14, 12, 10))
    d = ImageDraw.Draw(sheet)
    f = font(18)
    for i, (sl, sp, path) in enumerate(keys):
        im = Image.open(path).resize((tw, th))
        x, y = 12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 34)
        sheet.paste(im, (x, y))
        d.text((x, y + th + 6), f"{sl}장 · 클릭 {sp} (끝 모습)", fill=(230, 220, 200), font=f)
    sheet.save(out / ("sheet-slides%d-%d.png" % (first, last)))
    print("video:", mp4, "gif:", gif, "frames:", n, "errors:", errs)
    return errs


def mid_sheet(out, picks):
    """움직이는 중간 장면들 (frame 번호 → 이름)."""
    tw, th = 480, 270
    cols = 4
    rows = (len(picks) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * (th + 34) + 12), (14, 12, 10))
    d = ImageDraw.Draw(sheet)
    f = font(18)
    for i, (fn, label) in enumerate(picks):
        im = Image.open(out / "frames" / f"f{fn:05d}.jpg").resize((tw, th))
        x, y = 12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 34)
        sheet.paste(im, (x, y))
        d.text((x, y + th + 6), label, fill=(230, 220, 200), font=f)
    sheet.save(out / "motion-beats.png")


def qa(a, out):
    first, last = map(int, a.slides.split("-"))
    rep = {"steps": [], "errors": [], "reduced": []}
    with sync_playwright() as p:
        b = launch(p)
        S = None if a.reduced_only else Stage(b, 1920, 1080, start=first)
        if S is not None:
            S.adv(0)
            while True:
                st = S.state()
                sl, sp = st["slide"] + 1, st["step"]
                if sl > last:
                    break
                # 움직이는 중간에도 넘침이 있는지: 0.15초 간격으로 훑고, 끝 모습에서 한 번 더
                issues = []
                for _ in range(int(hold_ms(sl, sp) / 150)):
                    S.adv(150)
                    for x in S.pg.evaluate(BOUNDS):
                        if x[0] == "edge" and x not in issues:
                            issues.append(x)
                S.adv(500)
                S.pg.evaluate(MARK)
                end = S.pg.evaluate(BOUNDS)
                try:
                    clip = S.pg.evaluate("window.__tsClip()")
                except Exception as e:  # noqa: BLE001  (harness probe crashed: see harness-notes.md)
                    clip = [["probe-crash", str(e)[:120]]]
                rep["steps"].append({"slide": sl, "step": sp, "during": issues, "end": end, "clip": clip})
                print(f"  {sl}.{sp}: during {len(issues)} · end {len(end)} · clip {len(clip)}", (json.dumps(issues + end + [c for c in clip if c[1] != "BUTTON"], ensure_ascii=False)[:400] if (issues or end or len(clip) > 2) else ""), flush=True)
                S.key()
                S.adv(0)
                if S.state() == st:   # 마지막 장 끝: 더 넘어가지 않아요
                    break
            # 뒤로 가기: 끝 모습이 바로 맞는지(움직임 없이) → 넘침만 다시
            for _ in range(6):
                S.key("ArrowLeft")
                S.adv(300)
                rep["steps"].append({"back": S.state(), "end": S.pg.evaluate(BOUNDS)})
            rep["errors"] += S.errors
            S.ctx.close()
        # 움직임 줄이기: 끝 모습이 다 보이는지 (0.6초 뒤)
        R = Stage(b, 1280, 720, reduced=True, start=first)
        R.adv(0)
        while True:
            st = R.state()
            sl, sp = st["slide"] + 1, st["step"]
            if sl > last:
                break
            R.adv(900)
            hidden = R.pg.evaluate("""() => { var s = document.querySelector('.slide.on'), n = [];
              s.querySelectorAll('h1,h2,.kicker,.nt,.tb,.hc,.fi,.one,.mean,.hxcap p,.hxpunch,.shot,.ask,.kcp,.ub,.stamp,[data-k],.agenda div').forEach(function (e) {
                n.push([e.className || e.tagName, getComputedStyle(e).opacity]); }); return n; }""")
            R.shot().resize((640, 360)).save(out / f"reduced-{sl:02d}-{sp}.jpg", quality=80)
            rep["reduced"].append({"slide": sl, "step": sp, "opacity": hidden})
            R.key()
            R.adv(0)
            if R.state() == st:
                break
        rep["errors"] += R.errors
        b.close()
    (out / "qa.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [s for s in rep["steps"] if s.get("during") or s.get("end") or s.get("clip")]
    print("QA steps with findings:", len(bad), "errors:", len(rep["errors"]))
    return rep


def fps_check(a, out):
    """Real clock. Per click: count rAF frames for 2.5 s, report mean fps, worst frame, share of frames over 50 ms."""
    first, last = map(int, a.slides.split("-"))
    w, h = map(int, a.size.split("x"))
    res = []
    gpu = ["--mute-audio", "--ignore-gpu-blocklist", "--enable-gpu-rasterization"] if a.gpu else ARGS
    with sync_playwright() as p:
        b = launch(p, gpu)
        S = Stage(b, w, h, fake=False, start=first)
        S.pg.wait_for_timeout(500)
        while True:
            st = S.state()
            sl, sp = st["slide"] + 1, st["step"]
            if sl > last:
                break
            S.pg.evaluate("""() => { window.__fr = []; var last = performance.now(), stop = last + 2500;
              function f(now) { window.__fr.push(now - last); last = now; if (now < stop) requestAnimationFrame(f); } requestAnimationFrame(f); }""")
            S.pg.wait_for_timeout(2700)
            fr = S.pg.evaluate("window.__fr")
            fr = fr[1:] if len(fr) > 1 else fr
            mean = sum(fr) / max(1, len(fr))
            r = {"slide": sl, "step": sp, "fps": round(1000 / mean, 1) if mean else 0, "worst_ms": round(max(fr), 1) if fr else 0,
                 "over50": round(sum(1 for x in fr if x > 50) / max(1, len(fr)), 3), "gl": st.get("gl"), "pr": st.get("pr")}
            res.append(r)
            print("  ", r, flush=True)
            S.key()
        errs = S.errors
        b.close()
    (out / ("fps-gpu.json" if a.gpu else "fps-swiftshader.json")).write_text(json.dumps({"rows": res, "errors": errs}, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--slides", default="1-7")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--qa-only", action="store_true")
    ap.add_argument("--reduced-only", action="store_true", help="QA: only the reduced-motion end frames (fast look at every click)")
    ap.add_argument("--fps-check", action="store_true")
    ap.add_argument("--gpu", action="store_true", help="fps check with the real GPU instead of SwiftShader")
    ap.add_argument("--beats", default="", help="frame:label,... -> motion-beats.png from an existing frames dir")
    ap.add_argument("--query", default="", help='주소 뒤에 붙일 것, 예: "?robot=puppet"')
    ap.add_argument("--name", default="", help="미리보기 파일 이름 앞부분 (기본: preview-slidesA-B)")
    a = ap.parse_args()
    global QUERY
    QUERY = a.query
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.beats:
        mid_sheet(out, [(int(x.split(":", 1)[0]), x.split(":", 1)[1]) for x in a.beats.split(",")])
        return 0
    if a.fps_check:
        fps_check(a, out)
        return 0
    if a.qa_only:
        qa(a, out)
        return 0
    video(a, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
