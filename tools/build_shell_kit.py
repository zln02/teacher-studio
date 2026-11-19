# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Build shared/shell/ assets from the already-vetted design arsenal in shared/assets (no download, no new license).

- icons.json      : every Tabler outline icon in shared/assets/icons/tabler (MIT, LICENSE read and copied as LICENSE-tabler.txt),
                    stored as the inner SVG markup of a 24x24 stroke icon (xmlns / class / the empty bounding path removed).
- characters/*.svg: four DiceBear "thumbs" faces (CC0 1.0, LICENSE copied) for game title screens.

Run after shared/assets changes:  py tools/build_shell_kit.py   (then py tools/sync_shared.py)
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLER = ROOT / "shared" / "assets" / "icons" / "tabler"
DICE = ROOT / "shared" / "assets" / "characters" / "dicebear"
OUT = ROOT / "shared" / "shell"


def inner(svg: str) -> str:
    body = re.search(r"<svg\b[^>]*>(.*)</svg>", svg, re.S).group(1)
    body = re.sub(r'<path stroke="none" d="M0 0h24v24H0z" fill="none"\s*/>', "", body)
    body = re.sub(r"\s+", " ", body).replace("> <", "><").strip()
    return body


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    icons = {}
    for f in sorted(TABLER.glob("*.svg")):
        icons[f.stem] = inner(f.read_text(encoding="utf-8"))
    blob = json.dumps({"_source": "Tabler Icons (outline, MIT) - copied from shared/assets/icons/tabler by tools/build_shell_kit.py; see LICENSE-tabler.txt",
                       "viewBox": "0 0 24 24", "icons": icons}, ensure_ascii=False, separators=(",", ":"))
    (OUT / "icons.json").write_text(blob, encoding="utf-8")
    shutil.copyfile(TABLER / "LICENSE", OUT / "LICENSE-tabler.txt")
    chars = OUT / "characters"
    chars.mkdir(exist_ok=True)
    for seed in "abcd":
        shutil.copyfile(DICE / "thumbs" / f"{seed}.svg", chars / f"thumbs-{seed}.svg")
    shutil.copyfile(DICE / "LICENSE-thumbs.txt", chars / "LICENSE-thumbs.txt")
    h = hashlib.sha256()
    for f in sorted(p for p in OUT.rglob("*") if p.is_file() and p.suffix in (".json", ".svg", ".txt")):
        h.update(f"{f.relative_to(OUT).as_posix()}\t{hashlib.sha256(f.read_bytes()).hexdigest()}\n".encode())
    print(f"icons={len(icons)} bytes={len(blob)} sha256={h.hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
