#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Cut the studio's default UI/display face ("TS Sans") once from Pretendard Variable (SIL OFL 1.1).

    python3 tools/build_ts_sans.py [path/to/PretendardVariable.woff2]

Pretendard 1.3.9, Copyright (c) 2021 Kil Hyung-jin, Reserved Font Name "Pretendard". A subset is a Modified Version, so the
file is renamed "TS Sans" (the reserved name is never used as a family name); copyright and licence records stay in the font.
Coverage = the same characters as shared/fonts/base/NotoSansKR-ksx1001 (KS X 1001 + Latin + punctuation), weights 100-900,
features kept: kern, locl, tnum (tabular figures), case, ss05/ss06 are dropped (not used). Output: shared/fonts/base/TSSans-ksx1001-wght100-900.woff2
"""
import io
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "training" / "deck-v2-src" / "vendor" / "pretendard" / "PretendardVariable.woff2"
BASE = ROOT / "shared" / "fonts" / "base"
OUT = BASE / "TSSans-ksx1001-wght100-900.woff2"
NAME = "TS Sans"


def main() -> int:
    cover = set(TTFont(str(BASE / "NotoSansKR-ksx1001-wght400-900.woff2")).getBestCmap())
    cover |= {0x300C, 0x300D, 0x300E, 0x300F, 0x00B7, 0x2026, 0x2013, 0x2014, 0x2192, 0x2190, 0x2191, 0x2193, 0x00D7, 0x2212, 0x2022, 0x201C, 0x201D, 0x2018, 0x2019}
    f = TTFont(str(SRC), lazy=False)
    o = subset.Options()
    o.flavor = "woff2"
    o.layout_features = ["kern", "locl", "tnum", "case", "ccmp", "mark", "mkmk"]
    o.name_IDs = ["*"]
    o.hinting = False
    o.notdef_outline = True
    s = subset.Subsetter(o)
    s.populate(unicodes=sorted(cover))
    s.subset(f)
    nm = f["name"]
    nm.names = [r for r in nm.names if r.nameID not in (1, 3, 4, 6, 16, 17, 21, 22, 25)]
    for nid, val in ((1, NAME), (4, NAME), (6, NAME.replace(" ", "")), (16, NAME), (3, NAME + " (subset of Pretendard 1.3.9, SIL OFL 1.1)")):
        nm.setName(val, nid, 3, 1, 0x409)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    OUT.write_bytes(buf.getvalue())
    print(f"{OUT.name}: {len(buf.getvalue()) // 1024} KB, {len(f.getBestCmap())} characters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
