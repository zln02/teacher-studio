"""Build a Teacher Studio asset pack (JS file with base64 data URIs) from Kenney CC0 sources.

Usage: python3 build_assets.py <kenney_root> <out.js>
The output registers itself as: (window.NGA_PACKS = window.NGA_PACKS || []).push({...})
"""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

PLAT = "new-platformer-pack/Sprites"
CHAR_COLORS = ["beige", "green", "pink", "purple", "yellow"]
CHAR_POSES = ["idle", "walk_a", "walk_b", "jump", "hit", "front"]
ENEMIES = ["slime_normal_rest", "slime_normal_walk_a", "slime_normal_walk_b", "slime_normal_flat", "bee_a", "bee_b",
           "fish_blue_swim_a", "fish_blue_swim_b", "frog_idle", "frog_jump", "snail_walk_a", "snail_walk_b",
           "ladybug_walk_a", "ladybug_walk_b"]
TILES = ["terrain_grass_block_top", "terrain_grass_block_center", "terrain_grass_horizontal_left",
         "terrain_grass_horizontal_middle", "terrain_grass_horizontal_right", "terrain_grass_cloud_left",
         "terrain_grass_cloud_middle", "terrain_grass_cloud_right", "block_yellow", "block_blue", "block_green",
         "block_red", "block_exclamation", "block_exclamation_active", "block_coin", "block_empty", "coin_gold",
         "coin_silver", "gem_blue", "gem_green", "gem_red", "gem_yellow", "star", "heart", "key_yellow",
         "lock_yellow", "flag_green_a", "flag_green_b", "flag_red_a", "flag_red_b", "sign", "bush", "mushroom_red",
         "cactus", "rock", "spring", "hud_heart", "hud_heart_empty", "hud_coin"]
BACKGROUNDS = ["background_color_hills", "background_color_trees", "background_color_desert",
               "background_color_mushrooms", "background_clouds", "background_solid_sky"]
SOUNDS = {"ui_click": "click_002", "ui_select": "select_002", "ui_confirm": "confirmation_001",
          "ui_confirm2": "confirmation_002", "ui_error": "error_004", "ui_drop": "drop_002",
          "ui_pickup": "maximize_006", "ui_question": "question_001", "ui_glass": "glass_002",
          "ui_toggle": "toggle_002", "ui_tick": "tick_001", "ui_bong": "bong_001", "ui_pluck": "pluck_001",
          "ui_open": "open_002", "ui_back": "back_002"}


def png_data_uri(path: Path, colors: int = 160) -> str:
    """Quantize a PNG (keeping alpha) and return a data URI."""
    img = Image.open(path).convert("RGBA")
    q = img.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    q.save(buf, format="PNG", optimize=True)
    raw = buf.getvalue()
    orig = path.read_bytes()
    data = raw if len(raw) < len(orig) else orig
    return "data:image/png;base64," + base64.b64encode(data).decode()


def mp3_data_uri(path: Path) -> str:
    """Encode a short sound to mono 22 kHz MP3 and return a data URI."""
    with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", "22050",
                        "-b:a", "48k", tmp.name], check=True)
        return "data:audio/mpeg;base64," + base64.b64encode(Path(tmp.name).read_bytes()).decode()


def main(root: Path, out: Path) -> None:
    """Collect the selected sprites and sounds into one JS asset pack."""
    img: dict[str, str] = {}
    for c in CHAR_COLORS:
        for p in CHAR_POSES:
            img[f"char_{c}_{p}"] = png_data_uri(root / PLAT / "Characters/Default" / f"character_{c}_{p}.png")
    for n in ENEMIES:
        img[n] = png_data_uri(root / PLAT / "Enemies/Default" / f"{n}.png")
    for n in TILES:
        img[n] = png_data_uri(root / PLAT / "Tiles/Default" / f"{n}.png")
    for n in BACKGROUNDS:
        img[n] = png_data_uri(root / PLAT / "Backgrounds/Default" / f"{n}.png", colors=96)
    snd_dir = next(root.glob("kenney-interface-sounds-zip/*/addons/kenney_interface_sounds"))
    snd = {k: mp3_data_uri(snd_dir / f"{v}.wav") for k, v in SOUNDS.items()}
    pack = {"name": "kenney-platformer-core", "version": "0.1.0",
            "license": "CC0-1.0 (assets by Kenney, kenney.nl)", "img": img, "snd": snd}
    js = ("/* Teacher Studio asset pack: kenney-platformer-core 0.1.0 — sprites & sounds by Kenney (kenney.nl), CC0 1.0 */\n"
          "(window.NGA_PACKS = window.NGA_PACKS || []).push(" + json.dumps(pack, separators=(",", ":")) + ");\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(js, encoding="utf-8")
    print(f"{out}: {len(img)} images, {len(snd)} sounds, {len(js.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
