#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Check shared/assets against manifest.json: files exist, bytes + sha256 match, license_file exists, license allowed.

    python3 verify_assets.py        (exit 0 = ok, 1 = problems)
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALLOWED = {"MIT", "ISC", "Apache-2.0", "OFL-1.1", "CC0-1.0"}


def listing(paths):
    files = []
    for p in paths:
        q = HERE / p
        if q.is_dir():
            files += [f for f in q.rglob("*") if f.is_file()]
        elif q.is_file():
            files.append(q)
        else:
            files.append(None)
            print(f"  missing path: {p}")
    return files


def main():
    data = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    problems = 0
    total = 0
    for id_, it in data["items"].items():
        files = listing(it["paths"])
        if None in files:
            problems += 1
            continue
        files = sorted(set(files), key=lambda f: f.relative_to(HERE).as_posix())
        lines = "".join(f"{f.relative_to(HERE).as_posix()}\t{hashlib.sha256(f.read_bytes()).hexdigest()}\n" for f in files)
        size = sum(f.stat().st_size for f in files)
        total += size
        errs = []
        if len(files) != it["files"]:
            errs.append(f"file count {len(files)} != {it['files']}")
        if size != it["bytes"]:
            errs.append(f"bytes {size} != {it['bytes']}")
        if hashlib.sha256(lines.encode()).hexdigest() != it["sha256"]:
            errs.append("sha256 mismatch")
        if not (HERE / it.get("license_file", "")).is_file():
            errs.append(f"license_file missing: {it.get('license_file')}")
        if it.get("license") not in ALLOWED:
            errs.append(f"license not allowed: {it.get('license')}")
        print(f"{'FAIL' if errs else 'ok  '} {id_} ({len(files)} files, {size} bytes)" + "".join(f"\n  {e}" for e in errs))
        problems += bool(errs)
    print(f"{len(data['items'])} items, {total} bytes counted; {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
