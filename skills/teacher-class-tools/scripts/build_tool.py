#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Build a classroom tool (timer / picker / teams / bracket / scoreboard) as ONE offline HTML file from a short spec.

Usage:
    python3 build_tool.py --spec spec.json --out tool.html [--no-check] [--no-fonts] [--yes]

spec (see SKILL.md): {tool, title, use:"class"|"personal", sound, design:{subject,grade,mood,seed,large}, <tool options>}
Steps: validate spec -> design tokens (shared design system) -> assemble CSS + runtime + data -> embed Korean fonts
(skipped with --no-fonts / when fonttools is missing; --yes agrees to install that small tool) -> check_tool.py.
Nothing is stored or sent by the page: names a teacher types live in that page only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
import html as _html


def _js_json(obj, **kw) -> str:
    """JSON for an inline <script>: < > & and U+2028/2029 become unicode escapes, so </script> or <!-- in text can never end the tag."""
    s = json.dumps(obj, ensure_ascii=False, **kw)
    for ch, esc in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), (chr(0x2028), "\\u2028"), (chr(0x2029), "\\u2029")):
        s = s.replace(ch, esc)
    return s

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
# shared/ lives inside the skill when installed (tools/sync_shared.py copies it); in the repo it is two levels up.
SHARED = SKILL / "shared" if (SKILL / "shared" / "design").is_dir() else SKILL.parent.parent / "shared"
for _sub in ("design", "fonts", "tools"):
    sys.path.insert(0, str(SHARED / _sub))
import design  # noqa: E402

JUICE = SHARED / "juice" if (SHARED / "juice" / "juice.js").exists() else SKILL.parent.parent / "shared" / "juice"  # Game Wow kit (shared/juice): sound presets, particles, flash governor, podium, motion effects
USE_JUICE = True  # --no-juice builds without the kit (before/after comparison only)

TOOLS = ("timer", "picker", "teams", "bracket", "scoreboard")
ANIMALS = ["호랑이", "토끼", "거북이", "독수리", "돌고래", "여우", "판다", "사자"]
LIMITS = {"picker": (2, 60), "teams": (2, 60), "bracket": (2, 16)}


def _items(spec: dict, block: dict, tool: str) -> tuple[list[str], list[str]]:
    errs: list[str] = []
    lo, hi = LIMITS[tool]
    if "items" in block:
        items = [str(x).strip() for x in block["items"] if str(x).strip()]
    else:
        nm = block.get("numbers") or {}
        a, b = int(nm.get("from", 1)), int(nm.get("to", 28 if tool != "bracket" else 8))
        items = [f"{i}번" for i in range(a, b + 1)]
    items = list(dict.fromkeys(items))
    if not lo <= len(items) <= hi:
        errs.append(f"{tool}: needs {lo}-{hi} entries (got {len(items)}). Use block.items or block.numbers {{from,to}}")
    if any(len(x) > 14 for x in items):
        errs.append(f"{tool}: entries must be 14 characters or fewer")
    return items, errs


def normalize(spec: dict) -> tuple[dict, list[str]]:
    """Validate the spec and return (data for the page, errors)."""
    errs: list[str] = []
    tool = spec.get("tool")
    if tool not in TOOLS:
        return {}, [f"tool must be one of {', '.join(TOOLS)}"]
    if spec.get("use", "class") not in ("class", "personal"):
        errs.append("use must be class or personal")
    block = dict(spec.get(tool) or {})
    if tool == "timer":
        mode = block.get("mode", "countdown")
        if mode not in ("countdown", "stopwatch"):
            errs.append("timer.mode must be countdown or stopwatch")
        mins = float(block.get("minutes", 5))
        if not 0.1 <= mins <= 180:
            errs.append("timer.minutes must be 0.1-180")
        presets = [int(x) for x in block.get("presets", [1, 3, 5, 10])][:4]
        while len(presets) < 4:
            presets.append((presets[-1] if presets else 0) + 5)
        data = {"mode": mode, "minutes": mins, "presets": presets, "warn_at": int(block.get("warn_at", 10))}
    elif tool in ("picker", "teams", "bracket"):
        items, e = _items(spec, block, tool)
        errs += e
        data = {"items": items}
        if tool == "picker":
            data.update(no_repeat=bool(block.get("no_repeat", True)), label=str(block.get("label", "오늘의 뽑기"))[:16])
        elif tool == "teams":
            k = int(block.get("team_count") or (-(-len(items) // int(block["team_size"])) if block.get("team_size") else 4))
            k = max(2, min(8, k, max(2, len(items))))
            names = [str(x) for x in block.get("team_names", ANIMALS)][:8]
            data.update(team_count=k, team_names=names)
        else:
            data["shuffle_on_edit"] = bool(block.get("shuffle", False))
    else:
        teams = [str(x).strip() for x in block.get("teams", ANIMALS[:4]) if str(x).strip()]
        if not 2 <= len(teams) <= 8:
            errs.append("scoreboard.teams needs 2-8 names")
        steps = [int(x) for x in block.get("steps", [1, 5, 10])][:3] or [1]
        data = {"teams": teams, "steps": steps, "start": int(block.get("start", 0))}
    return data, errs


def make_tokens(spec: dict) -> dict:
    d = spec.get("design") or {}
    tk = design.generate(d.get("subject", ""), int(d.get("grade", 5)), d.get("mood", ""), spec.get("use", "class"),
                         int(d.get("seed", 0)), bool(d.get("large", False)), "default")
    tk["fonts"].update(display="TS Sans", body="TS Sans", embeddable=True)  # one embeddable family: offline-safe
    if d.get("palette_from"):  # the user's own colours (design.palette_from: file | "saved")
        design.apply_palette_from(tk, d["palette_from"])
    return tk


def css_vars(tk: dict) -> str:
    c, t, cls = tk["colors"], tk["type"], tk["use"] == "class"
    v = {f"--{k}": val for k, val in c.items()}
    v.update({"--fs-h": f"{t['question']}px", "--fs-btn": f"{t['choice']}px", "--fs-body": f"{t['body']}px", "--fs-small": f"{t['floor']['small']}px",
              "--btn-h": f"{t['floor']['button_h'] - (6 if cls else 0)}px", "--btn-sm": "80px" if cls else "64px"})
    return ":root{" + ";".join(f"{k}:{x}" for k, x in v.items()) + "}"


def build(spec: dict, fonts: bool = True, yes: bool = False) -> tuple[str, dict]:
    data, errs = normalize(spec)
    if errs:
        raise ValueError("; ".join(errs))
    tk = make_tokens(spec)
    terr = design.validate_tokens(tk)
    if terr:
        raise ValueError("design tokens: " + "; ".join(terr))
    title = str(spec.get("title") or {"timer": "타이머", "picker": "뽑기", "teams": "모둠 편성", "bracket": "대진표", "scoreboard": "점수판"}[spec["tool"]])[:30]
    sound = bool(spec.get("sound", spec["tool"] == "timer"))
    payload = {"tool": spec["tool"], "title": title, "use": tk["use"], "sound": sound, "tokens": tk, "data": data}
    js = (SKILL / "assets" / "tools.js").read_text(encoding="utf-8")
    css = (SKILL / "assets" / "tools.css").read_text(encoding="utf-8")
    blob = _js_json(payload)
    import meaning  # shared/design: a team named 청팀 · 백팀 · 빨강 wears that colour
    kit_js, kit_css = meaning.js() + "\n", ""
    if USE_JUICE and (JUICE / "juice.js").exists():
        kit_js += (JUICE / "juice.js").read_text(encoding="utf-8") + "\n" + (JUICE / "juice-motion.js").read_text(encoding="utf-8") + "\n"
        kit_css = (JUICE / "juice.css").read_text(encoding="utf-8") + "\n"
    html = ('<!DOCTYPE html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{_html.escape(title)}</title>\n<style>/* TS:CSS BEGIN */{css_vars(tk)}\n{css}{kit_css}/* TS:CSS END */</style></head>\n'
            f'<body><div id="stage" class="land"><header><h1>{_html.escape(title)}</h1><div class="tools" id="tb"></div></header><main id="main"></main></div>\n'
            f'<script>window.TOOL = {blob};</script>\n<script>{kit_js}</script>\n<script>{js}</script>\n</body></html>\n')
    report: dict = {"embedded": False}
    if fonts:
        try:
            import embed
            html, report = embed.embed(html, consent=yes)
        except Exception as exc:  # fonts are a nicety, never a blocker
            report = {"embedded": False, "reason": str(exc)}
    return html, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--no-fonts", action="store_true")
    ap.add_argument("--no-juice", action="store_true", help="build without the Game Wow kit (before/after comparison only)")
    ap.add_argument("--yes", action="store_true", help="agree to install the small font tool when missing")
    a = ap.parse_args()
    global USE_JUICE
    USE_JUICE = not a.no_juice
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    if (spec.get("design") or {}).get("palette_from"):
        spec["design"]["palette_from"] = design.resolve_palette_from(spec["design"]["palette_from"], Path(a.spec).resolve().parent)
    try:
        html, rep = build(spec, not a.no_fonts, a.yes)
    except ValueError as exc:
        print(f"FAIL spec: {exc}")
        return 1
    Path(a.out).write_text(html, encoding="utf-8")
    note = "fonts embedded" if rep.get("embedded") else (rep.get("prompt") or rep.get("reason") or "fonts not embedded")
    print(f"wrote {a.out} ({len(html) // 1024} KB, {note})")
    if a.no_check:
        print(f"PARTIAL {a.out} (checks disabled)")
        return 0
    result = subprocess.call([sys.executable, str(HERE / "check_tool.py"), a.out])
    status = {0: "READY", 2: "PARTIAL"}.get(result, "NOT READY")
    print(f"{status} {Path(a.out).resolve()}")
    return result


def _no_browser_guard() -> bool:
    """True when no browser can start here (an agent's security box). shared/tools/workdir.py then prints ONE line and makes
    every screen check below skip at once instead of waiting for each launch to fail."""
    try:
        here = Path(__file__).resolve().parent
        for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
            if (d / "workdir.py").is_file():
                if str(d) not in sys.path:
                    sys.path.append(str(d))
                import workdir
                return workdir.guard_browser()
    except Exception:  # noqa: BLE001 - the guard must never stop a build
        pass
    return False


if __name__ == "__main__":
    _no_browser_guard()
    sys.exit(main())
