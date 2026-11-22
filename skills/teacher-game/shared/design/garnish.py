#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""고명 (garnish): pictures that dress a finished deck / game / page, chosen by what this computer can do (stdlib; Pillow optional).

The content is finished first; garnish comes last and is skipped wherever it would hurt reading.
  1. env()      what is here: Codex CLI (native image generation) -> "codex"; otherwise "code" (SVG drawn here, CC0 packs in shared/assets).
  2. plan()     a small consistent set: 2-3 backdrops by ROLE (story / tool / calm), one base prompt (palette, light direction, grain,
                "left 55% dark", no text / logos / faces), one scene line per role from the topic. Same style for the whole set.
  3. commands   the optional Codex command for each picture (never required; nothing runs unless asked):
                codex exec --skip-git-repo-check -s workspace-write [-i ref.png] -- "<prompt>"     (`--` is required after -i)
                at most two generations at a time on a slow PC; a reference image keeps one character across the set.
  4. finish()   compress to JPEG/WebP (long side 1920, ~150-250KB), write manifest.json (file, kind, slides, prompt, tool, size_kb).
  5. svg_backdrop()  the Claude-only path: an ink field with one soft accent light, a faint blueprint grid and grain, as inline SVG.
  6. skip_reason()   readability guard: a slide with a table / chart / dense text gets no picture behind it.
Use in a slide spec: "garnish": {"backdrops": {"story": "bg-a.jpg", "calm": "bg-c.jpg"}} (+ per slide "backdrop": "story" | "none"),
or "garnish": {"mode": "code"} for drawn backdrops. Pictures are inlined (no external image at runtime) and dimmed behind the text.

CLI:
  python3 garnish.py env
  python3 garnish.py plan --topic "가정통신문 안내" --roles story,calm --out garnish/   # writes prompts + manifest skeleton, prints commands
  python3 garnish.py finish garnish/                                                 # compress *.png -> .jpg and fill size_kb
  python3 garnish.py svg --role calm --out bg.svg
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROLES = {   # role -> what it is for, opacity behind text, default scene words
    "story": {"for": "이야기 · 비유 장 (사람이 공감하는 장면)", "opacity": 0.8, "scene": "a real place connected to the topic, at dusk, dim and warm-lit, heavily defocused"},
    "tool": {"for": "도구 · 비교 · 방법 장 (작업실 느낌)", "opacity": 0.55, "scene": "a quiet workspace at night, a faint blueprint grid on the back wall (lines only), a desk lamp glow on the right, heavily defocused"},
    "calm": {"for": "글이 많은 장 · 실습 · 마무리 (추상 빛)", "opacity": 0.7, "scene": "no objects at all: soft volumetric light beams and gentle bokeh, a very faint thin blueprint grid, calm and minimal"},
}
NO_TEXT = "ABSOLUTELY no text, letters, numbers, signs, labels, logos or brand marks anywhere; no people, no faces."
DENSE_TYPES = {"table", "chart", "math", "timer", "qr", "image", "video", "toc"}
DENSE_CHARS = 220   # text on a slide above this -> no picture behind it


def env() -> dict:
    """What can make pictures here. Codex = native image generation (optional); otherwise code-drawn SVG + CC0 packs."""
    codex = shutil.which("codex") or shutil.which("codex.cmd")
    try:
        from PIL import features  # noqa: F401
        pil, webp = True, bool(features.check("webp"))
    except Exception:
        pil, webp = False, False
    packs = (HERE.parent / "assets" / "manifest.json").exists()
    return {"mode": "codex" if codex else "code", "codex": bool(codex), "pillow": pil, "webp": webp, "cc0_packs": packs,
            "note": "Codex가 있으면 그림을 새로 그리고, 없으면 코드로 그린 바탕(SVG)과 무료 그림 모음을 써요. 둘 다 없어도 내용은 그대로예요."}


def base_prompt(palette: dict | None = None, light: str = "upper right") -> str:
    p = palette or {"bg": "#121214", "acc": "#E4502F", "cool": "#3338F0"}
    return (f"16:9 landscape, 1920x1080 feel. Slide background for a dark presentation: overall neutral near-black ink ({p['bg']}, not blue) with soft warm "
            f"accent ({p['acc']}) light and a little cool ({p['cool']}) light, subtle film grain, light coming from the {light}. Low contrast, calm, atmospheric, "
            "cinematic shallow depth of field, everything slightly soft so light text placed on top stays readable. Keep the left 55% of the frame and the centre "
            f"especially dark and calm with low detail (titles go there). {NO_TEXT}")


def command(prompt: str, name: str, ref: str = "") -> list[str]:
    """The optional Codex CLI call (run in the output folder). `--` is required after -i."""
    full = (f"Generate an image with your image generation tool. {prompt} Save the final image into the current directory as {name}.png "
            "(copy it here if the tool saves it elsewhere). Reply with just the path.")
    cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write"]
    if ref:
        cmd += ["-i", ref]
    return cmd + ["--", full]


def plan(topic: str, roles=("story", "calm"), scenes: dict | None = None, palette: dict | None = None, ref: str = "") -> dict:
    """A consistent set of 2-3 backdrops (same base prompt, one scene line per role). Returns the manifest skeleton."""
    base = base_prompt(palette)
    out = {}
    for r in roles:
        if r not in ROLES:
            raise ValueError(f"role {r!r}: one of {', '.join(ROLES)}")
        scene = (scenes or {}).get(r) or f"{ROLES[r]['scene']} (topic: {topic})"
        prompt = f"{base} Scene: {scene}."
        out[f"bg-{r}"] = {"file": f"bg-{r}.jpg", "kind": "bg", "role": r, "for": ROLES[r]["for"], "prompt": prompt,
                          "tool": "Codex CLI image generation (codex exec)", "command": command(prompt, f"bg-{r}", ref), "size_kb": None}
    return out


def compress(src: Path, dst: Path, long_side: int = 1920, quality: int = 82) -> int:
    """PNG -> JPEG / WebP (by dst suffix), long side <= 1920. Returns size in KB. Needs Pillow."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    im.thumbnail((long_side, long_side))
    fmt = "WEBP" if dst.suffix.lower() == ".webp" else "JPEG"
    im.save(dst, fmt, quality=quality, optimize=True) if fmt == "JPEG" else im.save(dst, fmt, quality=quality, method=6)
    return dst.stat().st_size // 1024


def finish(folder: Path, fmt: str = ".jpg") -> dict:
    """Compress every bg-*.png that has a manifest entry; fill size_kb; drop the command lines (they stay in the log)."""
    man_p = folder / "manifest.json"
    man = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else {}
    for png in sorted(folder.glob("*.png")):
        key = png.stem
        entry = man.setdefault(key, {"kind": "bg", "prompt": "", "tool": "unknown"})
        dst = png.with_suffix(fmt)
        entry["file"] = dst.name
        entry["size_kb"] = compress(png, dst)
    man_p.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return man


def skip_reason(slide: dict) -> str:
    """Why a slide should carry no picture behind it ('' = fine)."""
    t = slide.get("type", "")
    if slide.get("backdrop") in ("none", False):
        return "끔"
    if t in DENSE_TYPES:
        return f"{t} 장은 그림 없이 (읽기 먼저)"
    if t == "panel" and len(slide.get("blocks") or []) > 2:
        return "칸이 많은 장"
    words = []

    def walk(v):
        if isinstance(v, str):
            words.append(v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if not str(k).startswith("_") and k not in ("note", "type", "layout", "icon", "icons", "backdrop", "pen", "pills"):
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(slide)
    n = sum(len(w) for w in words)
    return f"글이 많은 장 ({n}자)" if n > DENSE_CHARS else ""


def default_role(slide: dict) -> str:
    t = slide.get("type", "")
    if t in ("title", "hero", "section", "statement"):
        return "story"
    if t in ("steps", "compare", "diagram", "panel", "illustration"):
        return "tool"
    return "calm"


def svg_backdrop(role: str = "calm", seed: int = 1, pal: dict | None = None) -> str:
    """Code-made backdrop (no picture files): ink field, one soft accent light, a faint blueprint grid, fine grain. Same recipe as the
    Codex prompt, so code and generated sets look like one family. Texture only, never a picture of something."""
    p = pal or {"bg": "#121214", "acc": "#E4502F", "cool": "#3338F0", "ink": "#F0EDE6"}
    r = random.Random(int(hashlib.sha256(f"{role}|{seed}".encode()).hexdigest()[:8], 16))
    cx, cy = (1500 + r.randint(-120, 120), 120 + r.randint(-60, 80))
    grid = "".join(f'<path d="M{x} 0V1080"/>' for x in range(96, 1920, 96)) + "".join(f'<path d="M0 {y}H1920"/>' for y in range(96, 1080, 96))
    dots = "".join(f'<circle cx="{r.randint(0, 1920)}" cy="{r.randint(0, 1080)}" r="{r.choice((0.8, 1, 1.3))}"/>' for _ in range(260))
    acc_op = {"story": 0.34, "tool": 0.22, "calm": 0.26}.get(role, 0.26)
    cool = '' if role == "story" else f'<ellipse cx="260" cy="980" rx="620" ry="360" fill="url(#gc)" opacity=".5"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            f'<defs><radialGradient id="ga"><stop offset="0" stop-color="{p["acc"]}" stop-opacity="{acc_op}"/><stop offset="1" stop-color="{p["acc"]}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="gc"><stop offset="0" stop-color="{p["cool"]}" stop-opacity=".22"/><stop offset="1" stop-color="{p["cool"]}" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="1920" height="1080" fill="{p["bg"]}"/><ellipse cx="{cx}" cy="{cy}" rx="980" ry="640" fill="url(#ga)"/>{cool}'
            f'<g stroke="{p["ink"]}" stroke-opacity=".035" stroke-width="1">{grid}</g><g fill="{p["ink"]}" fill-opacity=".05">{dots}</g></svg>')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("env")
    p = sub.add_parser("plan")
    p.add_argument("--topic", required=True)
    p.add_argument("--roles", default="story,calm")
    p.add_argument("--scene", action="append", default=[], help="role=scene words (overrides the default scene)")
    p.add_argument("--ref", default="", help="reference picture that keeps one character / style across the set")
    p.add_argument("--out", type=Path, required=True)
    f = sub.add_parser("finish")
    f.add_argument("folder", type=Path)
    f.add_argument("--webp", action="store_true")
    s = sub.add_parser("svg")
    s.add_argument("--role", default="calm", choices=sorted(ROLES))
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "env":
        print(json.dumps(env(), ensure_ascii=False, indent=1))
    elif a.cmd == "plan":
        scenes = dict(x.split("=", 1) for x in a.scene if "=" in x)
        man = plan(a.topic, [r.strip() for r in a.roles.split(",") if r.strip()], scenes, ref=a.ref)
        a.out.mkdir(parents=True, exist_ok=True)
        (a.out / "manifest.json").write_text(json.dumps({k: {x: y for x, y in v.items() if x != "command"} for k, v in man.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
        e = env()
        print(f"mode: {e['mode']}  (picture folder: {a.out})")
        for k, v in man.items():
            print(f"# {k}: {v['for']}")
            print(" ".join(x if " " not in x else json.dumps(x, ensure_ascii=False) for x in v["command"]))
        if not e["codex"]:
            print("NOTE Codex가 없어요: 바탕은 코드로 그려요 (spec \"garnish\": {\"mode\": \"code\"}).")
    elif a.cmd == "finish":
        print(json.dumps(finish(a.folder, ".webp" if a.webp else ".jpg"), ensure_ascii=False, indent=1))
    elif a.cmd == "svg":
        a.out.write_text(svg_backdrop(a.role, a.seed), encoding="utf-8")
        print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
