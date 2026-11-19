#!/usr/bin/env python3
"""Turn downloaded CC0 files (Poly Haven / ambientCG) into small, graded deck assets.

Usage (Windows):  set PYTHONUTF8=1 && py -I docs/training/deck-v2-src/prep_assets.py --src <download folder>
Input files are treated as untrusted data: they are only opened as images (OpenCV for .hdr, Pillow for .jpg,
the paper zip is read member-by-member and only *_Color.jpg is decoded). Nothing in them is executed.
Writes docs/training/deck-v2-src/assets/*.jpg (sources + licenses: docs/training/deck-v2-NOTICE.md).
"""
from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets"


def tonemap(path: Path, exposure: float) -> Image.Image:
    import cv2  # reads Radiance .hdr as float32
    a = cv2.imread(str(path), cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR)
    if a is None:
        raise SystemExit(f"cannot read {path}")
    a = a[:, :, ::-1].astype(np.float32) * exposure
    # ACES-ish filmic curve (Narkowicz) then sRGB
    x = np.clip((a * (2.51 * a + 0.03)) / (a * (2.43 * a + 0.59) + 0.14), 0, 1)
    x = np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    return Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))


def grade(im: Image.Image, tint, dark: float, sat: float) -> Image.Image:
    im = ImageEnhance.Color(im).enhance(sat)
    a = np.asarray(im).astype(np.float32) / 255
    t = np.array(tint, np.float32) / 255
    a = a * dark
    a = a * 0.78 + t * 0.22 * (0.4 + a)          # split-tone toward the palette
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    v = 1 - 0.55 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 1.6)) ** 2)
    a = a * np.clip(v, 0.25, 1)[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def save(im: Image.Image, name: str, q: int) -> None:
    p = OUT / name
    im.save(p, "JPEG", quality=q, optimize=True, progressive=True)
    print(f"  {name:28s} {im.size[0]}x{im.size[1]} {p.stat().st_size // 1024} KB")


def crop(im: Image.Image, fx0, fy0, fx1, fy1) -> Image.Image:
    w, h = im.size
    return im.crop((int(w * fx0), int(h * fy0), int(w * fx1), int(h * fy1)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    a = ap.parse_args()
    src = Path(a.src)
    OUT.mkdir(exist_ok=True)
    NAVY, PLUM = (40, 70, 150), (120, 50, 90)
    # 1) 길 장면: evening_road_01 (해 질 녘 시골길)
    road = tonemap(src / "evening_road_01_4k.hdr", 0.38)
    save(road.resize((1024, 512), Image.LANCZOS), "env_road.jpg", 80)
    bd = crop(road, 0.0, 0.2, 0.34, 0.545).resize((1600, 900), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.2))
    save(grade(bd, NAVY, 0.9, 1.15), "bd_road.jpg", 72)
    save(grade(bd, NAVY, 0.42, 0.7).resize((960, 540), Image.LANCZOS).filter(ImageFilter.GaussianBlur(14)), "hb_road.jpg", 70)
    # 2) 시험장 장면: school_hall (학교 강당 · 줄 맞춘 의자)
    hall = tonemap(src / "school_hall_4k.hdr", 1.0)
    save(hall.resize((1024, 512), Image.LANCZOS), "env_hall.jpg", 80)
    bd = crop(hall, 0.70, 0.33, 0.97, 0.565).resize((1600, 900), Image.LANCZOS).filter(ImageFilter.GaussianBlur(5))
    save(grade(bd, PLUM, 0.55, 0.8), "bd_hall.jpg", 72)
    save(grade(bd, PLUM, 0.36, 0.6).resize((960, 540), Image.LANCZOS).filter(ImageFilter.GaussianBlur(16)), "hb_hall.jpg", 70)
    # 3) 텍스처 (1k 색 · 512 노멀/거칠기)
    for t in ("asphalt_02", "aerial_grass_rock", "wood_table_001"):
        save(Image.open(src / f"{t}_diff_1k.jpg").convert("RGB"), f"t_{t}_diff.jpg", 74)
        save(Image.open(src / f"{t}_nor_gl_1k.jpg").convert("RGB").resize((512, 512), Image.LANCZOS), f"t_{t}_nor.jpg", 82)
        save(Image.open(src / f"{t}_rough_1k.jpg").convert("L").resize((512, 512), Image.LANCZOS).convert("RGB"), f"t_{t}_rough.jpg", 72)
    # 4) 종이 (ambientCG Paper003): zip 안의 *_Color.jpg 하나만 그림으로 읽어요
    with zipfile.ZipFile(src / "Paper003_1K-JPG.zip") as z:
        name = next(n for n in z.namelist() if n.endswith("_Color.jpg") and "/" not in n and ".." not in n)
        paper = Image.open(io.BytesIO(z.read(name))).convert("RGB").resize((512, 512), Image.LANCZOS)
    save(paper, "t_paper_diff.jpg", 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
