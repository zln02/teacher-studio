#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Invisible author mark for every output page: <meta name="generator"> + one HTML comment (nothing visible on screen).

    from stamp import stamp
    html = stamp(html)
"""
from __future__ import annotations

import re

VERSION = "0.2.0"
NAME = "Teacher Studio (교사 스튜디오) by 박진영 (zln02)"
REPO = "https://github.com/zln02/teacher-studio"
# The mark carries the name and version only: no web address, so a finished page makes no outside reference at all (the repo is in the credits, NOTICE and README).
META = f'<meta name="generator" content="{NAME} v{VERSION}">'
COMMENT = f"<!-- {NAME} · v{VERSION} · Apache-2.0 -->"


def stamp(html: str) -> str:
    """Add the generator meta and comment inside <head> (once)."""
    if 'name="generator"' in html:
        return html
    block = META + "\n" + COMMENT
    m = re.search(r"<meta\s+charset[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + "\n" + block + html[m.end():]
    m = re.search(r"<head[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + "\n" + block + html[m.end():]
    return html
