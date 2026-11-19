#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Entry point kept for the game skill: the 12-style taxonomy lives in shared/design/styles.py (shared with slides).

(tools/sync_shared.py copies shared/design into this skill's shared/ folder so the skill stays self-contained.)
Usage is unchanged:  python3 style_auto.py --words "우주 미니멀" --seed 3
Preview exactly what build.py will pick (same chooser, same words/title/subject/seed):  python3 style_auto.py --spec spec.json
Order of authority: design.style > design.words/design.mood > title/subtitle/subject > seed.
"""
import importlib.util
import json
import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent.parent / "shared" / "design" / "styles.py"
if not _CORE.exists():  # running from the repo root copy
    _CORE = Path(__file__).resolve().parents[3] / "shared" / "design" / "styles.py"
_spec = importlib.util.spec_from_file_location("ts_styles_core", _CORE)
_core = importlib.util.module_from_spec(_spec)
sys.modules["ts_styles_core"] = _core
_spec.loader.exec_module(_core)
globals().update({k: v for k, v in vars(_core).items() if not k.startswith("__")})


def preview_spec(path: str) -> dict:
    """What build.py will choose for this spec file (style + why + recipe), using theme_auto.compose itself."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import theme_auto  # lazy: theme_auto imports this module
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    d = spec.setdefault("design", {})
    d.setdefault("seed", 0)
    au = theme_auto.compose(spec)
    return {"style": au["style"], "why": au["style_why"], "recipe": au["recipe"], "seed": d["seed"]}


if __name__ == "__main__":
    if "--spec" in sys.argv:
        print(json.dumps(preview_spec(sys.argv[sys.argv.index("--spec") + 1]), ensure_ascii=False))
        sys.exit(0)
    sys.exit(_core.main())
