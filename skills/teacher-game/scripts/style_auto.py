#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Entry point kept for the game skill: the 12-style taxonomy lives in shared/design/styles.py (shared with slides).

(tools/sync_shared.py copies shared/design into this skill's shared/ folder so the skill stays self-contained.)
Usage is unchanged:  python3 style_auto.py --words "우주 미니멀" --seed 3
"""
import importlib.util
import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent.parent / "shared" / "design" / "styles.py"
_spec = importlib.util.spec_from_file_location("ts_styles_core", _CORE)
_core = importlib.util.module_from_spec(_spec)
sys.modules["ts_styles_core"] = _core
_spec.loader.exec_module(_core)
globals().update({k: v for k, v in vars(_core).items() if not k.startswith("__")})

if __name__ == "__main__":
    sys.exit(_core.main())
