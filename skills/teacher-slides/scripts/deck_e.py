# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Preset E + garnish for the web deck (deck.py calls this; nothing here changes a deck that does not use it).

- E mode (style "ink-poster"): body.e-motion, the preset's components and motion vocabulary (shared/design/preset_e.py, motion_e.js),
  a HUD frame on every slide, big-type opening ONLY on key-message slides (title / hero / section / statement), the accent dot that
  becomes the rule under a statement, the takeaway lit word by word on the last click, fast blur-in for every other build.
- Any style may use: slide "pen" (hand-drawn marks + notes found by their text), slide "pills" + "pill" (where we are in a sequence).
- Garnish (고명): spec "garnish": {"backdrops": {role: file}} or {"mode": "code"}; slide "backdrop": role | file | "none".
  Pictures are inlined once as CSS classes, dimmed behind the text, and skipped on dense slides (shared/design/garnish.py skip_reason).
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
_SHARED = SKILL / "shared" if (SKILL / "shared" / "design").exists() else SKILL.parent.parent / "shared"

import sys  # noqa: E402
sys.path.insert(0, str(_SHARED / "design"))
import garnish  # noqa: E402
import preset_e  # noqa: E402

KEY_TYPES = ("title", "hero", "section", "statement")   # big-type opening belongs to key-message slides only


def active(dz: dict) -> bool:
    return dz.get("style") == "ink-poster"


def uses_motion(spec: dict, dz: dict) -> bool:
    return active(dz) or any(isinstance(it, dict) and (it.get("pen") or it.get("pills")) for it in spec.get("slides") or [])


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def css(dz: dict) -> str:
    """Preset E components with the deck's own colours (a user palette keeps winning)."""
    c = dz["colors"]
    mode = "dark" if dz.get("dark") else "light"
    base = preset_e.css(mode, ":root")
    bind = (f":root{{--e-bg:{c['bg1']};--e-bg2:{c['bg2']};--e-surf:{c['card']};--e-ink:{c['tx']};--e-sub:{c['mu']};--e-mute:{c['mu']};"
            f"--e-line:{c['line']};--e-line2:{c['cb']};--e-acc:{c['pr']};--e-cool:{c['ac'] if active(dz) else c['emc']}}}")
    extra = (".e-note.e-acc{color:var(--e-acc)}.sl>.e-pills{position:absolute;top:46px;left:646px;width:628px;z-index:7}"
             ".sl>.e-pen{z-index:7}.e-motion .b{transition:none!important;transform:none}.e-motion .b:not(.on){opacity:0}"
             ".sl .e-scene{z-index:0}.sl .e-scene~.bx{z-index:1}.sl .e-scene~.art{display:none}"  # the backdrop is the picture: no second drawing on top
             ".sl .e-hl .e-w.e-lit,.sl .e-hl .e-w.e-num.e-lit{color:inherit}.sl .e-hl .e-w.e-num{font-weight:800}")
    return "\n".join([base, bind, extra])


def js() -> str:
    return preset_e.motion_js()


def dress(html: str, it: dict, dz: dict, max_b: int, builds: bool) -> tuple[str, list[str]]:
    """Attach E motion words to one slide's html and add pen / pills. Returns (html, notes)."""
    notes: list[str] = []
    nxt = max_b + 1
    if active(dz):
        if it.get("type") in KEY_TYPES:
            html = re.sub(r'class="bx h(?=[ "])([^"]*)"', lambda m: f'class="bx h{m.group(1)}" data-e="big"', html, count=1)
        if it.get("type") == "statement":
            html = re.sub(r'class="bx bar"', 'class="bx bar" data-e="dot"', html, count=1)
        if it.get("takeaway") and builds and 'class="bx p on-b st' in html:
            html = html.replace('class="bx p on-b st', f'data-e="hl" data-b="{nxt}" class="e-hl bx p on-b st', 1)
            nxt += 1
    pills = it.get("pills")
    if isinstance(pills, list) and 2 <= len(pills) <= 6:
        cur = int(it.get("pill", 0) or 0)
        cur = max(0, min(len(pills) - 1, cur))
        spans = "".join(f"<span><i></i>{_esc(p)}</span>" for p in pills)
        html += f'<div class="e-pills" data-e="pills" data-e-cur="{cur}" aria-hidden="true">{spans}</div>'  # a place marker like the page number (HUD level)
    elif pills:
        notes.append("pills: 2~6 short words (e.g. [\"준비\", \"만들기\", \"점검\"])")
    pen = it.get("pen")
    if isinstance(pen, list) and pen:
        marks = []
        for m in pen[:3]:
            if isinstance(m, dict) and (m.get("text") or m.get("w")):
                marks.append({k: m[k] for k in ("mark", "text", "x", "y", "w", "h", "note", "color") if k in m})
        if marks:
            at = f' data-b="{nxt}"' if builds else ""
            html += (f'<svg class="e-pen" data-e="pen"{at} viewBox="0 0 1920 1080" aria-hidden="true" '
                     f"data-e-marks='{_esc(json.dumps(marks, ensure_ascii=False))}'></svg>")
            notes += [f"pen note {m['note']!r}" for m in marks if m.get("note") and len(str(m["note"])) > 12]
    return html, notes


def _data_uri(p: Path) -> str:
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml"}.get(p.suffix.lower(), "image/jpeg")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def garnish_plan(spec: dict, dz: dict, base: Path) -> tuple[str, dict[int, str], list[str], list[str]]:
    """(css, {slide index: class}, notes, errors). Roles map to pictures; dense slides get none."""
    g = spec.get("garnish")
    if not isinstance(g, dict) or not g:
        return "", {}, [], []
    notes: list[str] = []
    errs: list[str] = []
    c = dz["colors"]
    pal = {"bg": c["bg1"], "acc": c["pr"], "cool": c["ac"], "ink": c["tx"]}
    srcs: dict[str, str] = {}
    for role, f in (g.get("backdrops") or {}).items():
        p = Path(f)
        p = p if p.is_absolute() else base / p
        if not p.exists():
            errs.append(f"garnish.backdrops.{role}: file not found: {f}")
            continue
        if p.stat().st_size > 600_000:
            notes.append(f"garnish {p.name}: {p.stat().st_size // 1024}KB - shrink with `garnish.py finish` (JPEG/WebP, ~200KB)")
        srcs[role] = _data_uri(p)
    code = g.get("mode") == "code"
    dark = bool(dz.get("dark"))
    scrim = c["bg1"]
    rules, assign, skipped = [], {}, []
    used: set[str] = set()
    for i, it in enumerate(spec.get("slides") or []):
        want = it.get("backdrop")
        why = garnish.skip_reason(it)
        if why:
            if want not in (None, "none", False):
                skipped.append(f"{i + 1}장: {why}")
            continue
        role = want if isinstance(want, str) and want else garnish.default_role(it)
        if role in srcs or (code and role in garnish.ROLES):
            assign[i] = f"gx-{role}"
            used.add(role)
    for role in sorted(used):
        if role in srcs:
            url = srcs[role]
        else:
            svg = garnish.svg_backdrop(role, int(dz.get("seed") or 1), pal)
            url = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
        op = garnish.ROLES.get(role, {}).get("opacity", 0.6) * (1 if dark else 0.35)
        rules.append(f".sl .gx-{role}{{background-image:url({url});opacity:{op:.2f}}}")
    if rules:
        r, gg, b = (int(scrim[k:k + 2], 16) for k in (1, 3, 5))
        rules.append(f".sl .e-scene{{--e-bg:{scrim};--e-scrim:rgba({r},{gg},{b},.62)}}")  # scrim in the deck's own background colour
    if skipped:
        notes.append("고명 생략 (읽기 먼저): " + ", ".join(skipped))
    return "\n".join(rules), assign, notes, errs
