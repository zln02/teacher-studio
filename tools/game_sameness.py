#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""How alike do game question screens look? (the design_review fingerprint: 24x14 cells covered by cards and big text, Jaccard overlap 0..1)

  different requests  = mean pairwise overlap between different specs built with the same seed, averaged over the seeds
  same request        = mean pairwise overlap between seeds of one spec, averaged over the specs
Targets: different <= 0.5, same <= 0.8. Lower = the compositions differ more.

Usage: python3 tools/game_sameness.py [--seeds 1 2 3] [--specs a.json b.json ...] [--json out.json] [--shots DIR]
Default specs: every quiz / escape example in skills/teacher-game/assets/spec-examples (the mechanics that share the question screen).
"""
from __future__ import annotations

import argparse
import io
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "skills" / "teacher-game"
sys.path.insert(0, str(GAME / "scripts"))
import design_review as dr  # noqa: E402


def build(spec: Path, seed: int, out: Path) -> None:
    r = subprocess.run([sys.executable, str(GAME / "scripts" / "build.py"), "--spec", str(spec), "--out", str(out), "--no-fonts", "--no-check", "--seed", str(seed)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not out.exists():
        raise SystemExit(f"build failed: {spec.name} seed {seed}\n{r.stdout[-400:]}{r.stderr[-400:]}")


def question_probe(pg, html: Path, shot: Path | None = None) -> dict:
    pg.goto(html.resolve().as_uri())
    pg.wait_for_timeout(700)
    pg.evaluate("advanceTime(1500)")
    pg.click("#t-start")
    pg.wait_for_timeout(3700)
    pg.evaluate("advanceTime(1200)")
    pg.wait_for_timeout(500)
    if shot:
        from PIL import Image
        Image.open(io.BytesIO(pg.screenshot())).convert("RGB").resize((960, 540)).save(shot)
    return pg.evaluate(dr.PROBE_JS)


def mean_pairs(fps: list[str]) -> float:
    pairs = [dr.similarity(a, b) for a, b in itertools.combinations(fps, 2)]
    return sum(pairs) / len(pairs) if pairs else 0.0


def measure(specs: list[Path], seeds: list[int], shots: Path | None = None) -> dict:
    from playwright.sync_api import sync_playwright
    tmp = Path(tempfile.mkdtemp(prefix="sameness-"))
    fps: dict = {}
    layouts: dict = {}
    with sync_playwright() as p:
        b = dr._launch(p)
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.add_init_script(dr.SILENT_JS)
        for sp in specs:
            for sd in seeds:
                f = tmp / f"{sp.stem}-{sd}.html"
                build(sp, sd, f)
                fps[(sp.stem, sd)] = dr.fingerprint(question_probe(pg, f, shots / f"{sp.stem}-{sd}.png" if shots else None))
                layouts[f"{sp.stem}@{sd}"] = (dr.game_spec(f).get("layoutCfg") or {}).get("layout")
        b.close()
    diff = [mean_pairs([fps[(sp.stem, sd)] for sp in specs]) for sd in seeds]
    same = [mean_pairs([fps[(sp.stem, sd)] for sd in seeds]) for sp in specs]
    return {"different_requests": round(sum(diff) / len(diff), 3), "same_request": round(sum(same) / len(same), 3),
            "per_seed": dict(zip(map(str, seeds), [round(x, 3) for x in diff])), "per_spec": dict(zip([s.stem for s in specs], [round(x, 3) for x in same])),
            "layouts": layouts, "specs": len(specs), "seeds": seeds}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--specs", type=Path, nargs="+")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--shots", type=Path)
    a = ap.parse_args()
    specs = a.specs
    if not specs:
        specs = [f for f in sorted((GAME / "assets" / "spec-examples").glob("*.json")) if json.loads(f.read_text(encoding="utf-8")).get("mechanic") in ("quiz", "escape")]
    if a.shots:
        a.shots.mkdir(parents=True, exist_ok=True)
    res = measure(specs, a.seeds, a.shots)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.json:
        a.json.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = res["different_requests"] <= 0.5 and res["same_request"] <= 0.8
    print(f"different requests {res['different_requests']} (target <= 0.5) · same request {res['same_request']} (target <= 0.8) -> {'OK' if ok else 'TOO ALIKE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
