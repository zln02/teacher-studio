# SPDX-License-Identifier: Apache-2.0
"""Handout front: step pictures (①~④) from a real ChatGPT Work screenshot + the real hwpx result.

  py make_steps.py <work-screenshot.png>   -> steps/step1.png .. step4.png

Only the Chat|Work toggle and the input box are cropped (never the suggestion cards / names / recent lists).
Cursor, circles and the example text are drawn on top and marked 「예시」.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "steps"
WORK_RESULT = HERE.parent / "deck-v3-src" / "compare-e" / "work" / "cowork-1.png"   # 한 쪽 hwpx 미리보기 윗부분
W, H = 1400, 700
BG = (24, 24, 26)
VERM = (228, 80, 47)
F = "C:/Windows/Fonts/malgunbd.ttf"


def font(n):
    try:
        return ImageFont.truetype(F, n)
    except OSError:
        return ImageFont.load_default()


def fit(crop: Image.Image, scale: float) -> tuple[Image.Image, float, int, int]:
    c = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
    can = Image.new("RGB", (W, H), BG)
    x, y = (W - c.width) // 2, (H - c.height) // 2
    can.paste(c, (x, y))
    return can, scale, x, y


def cursor(d: ImageDraw.ImageDraw, x: int, y: int, s: float = 2.2):
    pts = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]
    P = [(x + px * s, y + py * s) for px, py in pts]
    d.polygon(P, fill=(255, 255, 255), outline=(0, 0, 0))
    d.line(P + [P[0]], fill=(0, 0, 0), width=4)


def badge(d, n):
    d.ellipse((24, 24, 124, 124), fill=VERM)
    f = font(64)
    d.text((74, 72), str(n), font=f, fill="white", anchor="mm")


def label(d, x, y, text, size=44):
    f = font(size)
    b = d.textbbox((x, y), text, font=f, anchor="lm")
    d.rounded_rectangle((b[0] - 18, b[1] - 12, b[2] + 18, b[3] + 12), 14, fill=VERM)
    d.text((x, y), text, font=f, fill="white", anchor="lm")


def main(src: Path):
    OUT.mkdir(exist_ok=True)
    im = Image.open(src).convert("RGB")
    sx, sy = im.width / 1580, im.height / 828   # coordinates below are for a 1580×828 shot

    def C(x0, y0, x1, y1):
        return im.crop((int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)))

    # ① Chat | Work
    x0, y0 = 600, 0
    can, s, ox, oy = fit(C(x0, y0, 1000, 60), 3.0)
    d = ImageDraw.Draw(can)
    wx, wy = ox + (839 - x0) * s / sx * sx, oy + (20 - y0) * s
    d.ellipse((wx - 170, wy - 70, wx + 170, wy + 70), outline=VERM, width=10)
    cursor(d, int(wx + 40), int(wy + 20))
    label(d, int(wx - 330), int(wy + 190), "「Work」 누르기")
    badge(d, 1)
    can.save(OUT / "step1.png")

    # ② 파일 button
    x0, y0, x1, y1 = 447, 392, 1140, 555
    base = C(x0, y0, x1, y1)
    can, s, ox, oy = fit(base, 1.85)
    d = ImageDraw.Draw(can)
    fx, fy = ox + (624 - x0) * s, oy + (530 - y0) * s
    d.ellipse((fx - 95, fy - 48, fx + 95, fy + 48), outline=VERM, width=9)
    cursor(d, int(fx + 30), int(fy + 10))
    label(d, int(fx + 140), int(fy + 120), "우리 학교 양식 붙이기")
    badge(d, 2)
    can.save(OUT / "step2.png")

    # ③ 입력칸 + 보내기
    base = C(x0, y0, x1, y1).copy()
    bd = ImageDraw.Draw(base)
    bd.rectangle((10, 14, 520, 46), fill=base.getpixel((300, 60)))
    bd.text((16, 30), "다음 주 시설 안전 점검 안내문 한글 파일로 만들어 줘", font=font(19), fill=(240, 240, 240), anchor="lm")
    can, s, ox, oy = fit(base, 1.85)
    d = ImageDraw.Draw(can)
    tx, ty = ox + 6 * s, oy + 30 * s
    label(d, int(tx + 20), int(ty - 92), "예시", 34)
    bx, by = ox + (1115 - x0) * s, oy + (485 - y0) * s
    d.ellipse((bx - 50, by - 50, bx + 50, by + 50), outline=VERM, width=9)
    cursor(d, int(bx + 10), int(by + 14))
    badge(d, 3)
    can.save(OUT / "step3.png")

    # ④ 결과 예 (실제 hwpx 미리보기)
    r = Image.open(WORK_RESULT).convert("RGB")
    r.thumbnail((W - 80, H - 40))
    can = Image.new("RGB", (W, H), (236, 236, 236))
    can.paste(r, ((W - r.width) // 2, (H - r.height) // 2))
    d = ImageDraw.Draw(can)
    badge(d, 4)
    can.save(OUT / "step4.png")
    print("ok", [p.name for p in sorted(OUT.glob("step*.png"))])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
