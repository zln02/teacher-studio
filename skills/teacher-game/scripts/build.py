#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Build a game from a short spec.json (content + mechanic + design direction). Additive to fire.py.

Usage:
    python3 build.py --spec spec.json --out game.html [--tokens tokens.json] [--no-check]

spec.json (see references/spec-schema.md): {title, subtitle, mechanic, use, device, teams, timer, rounds,
  design:{subject,grade,mood,seed,theme,large}, world:{...}, items:[...], <mechanic options>}
Steps: validate spec -> design tokens (shared design system via scripts/design.py, or --tokens) -> assemble engine +
core + the chosen mechanic component + theme + tokens CSS -> inline only the libraries the spec asks for ("libs":
["confetti","katex",...], see shared/vendor) -> embed Korean fonts (Noto Sans/Serif KR cut to the page's characters;
skipped with --no-fonts or when fonttools is missing) -> check_game.py. The engine is copied byte-for-byte.
Options: --no-fonts  --yes (agree to install the small font tool when it is missing)
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import design  # noqa: E402  (shim -> shared/design/design.py)
import specs  # noqa: E402
import theme_auto  # noqa: E402

for _sub in ("fonts", "vendor", "tools"):
    sys.path.insert(0, str(SKILL / "shared" / _sub))
import embed  # noqa: E402  (shared/fonts/embed.py)
import inline  # noqa: E402  (shared/vendor/inline.py)
from build_game import build  # noqa: E402

COMP = SKILL / "assets" / "components"
THEMES = SKILL / "assets" / "themes"
HEAD = "window.GAME_LOGIC = (function(){\nvar G = window.GAME, SPEC = G.spec, TK = SPEC.tokens, U = NG.util;\n"
FOOT = "\nreturn COMP.boot();\n})();\n"


def theme_for(tokens: dict, spec: dict) -> str:
    """Pick the theme module: explicit design.theme, else default."""
    t = (spec.get("design") or {}).get("theme") or tokens.get("theme") or "auto"  # auto is the default look
    if t == "auto":
        named = theme_auto.compose(spec)["named"]  # a request that clearly names one ported world uses it as is
        t = named or "auto"
    return t if (THEMES / f"{t}.js").exists() else "auto"


def theme_meta(theme: str) -> dict:
    """assets/themes/<id>.json: title, palette, fonts, host(bool), moods, subjects (Python-side facts about a theme)."""
    f = THEMES / f"{theme}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def make_tokens(spec: dict) -> dict:
    """Tokens from the design block (deterministic)."""
    d = spec.get("design") or {}
    tk = design.generate(d.get("subject", ""), int(d.get("grade", 5)), d.get("mood", ""), spec.get("use", "class"),
                         int(d.get("seed", 0)), bool(d.get("large", False)), d.get("theme", "auto"))
    th = theme_for(tk, spec)
    tk["theme"] = th
    meta = theme_meta(th)
    if meta.get("palette"):  # a ported theme brings its own scene palette (contrast is re-validated below)
        tk["colors"].update(meta["palette"])
        tk["palette"] = th
        for k in ("baseTheme", "bgType"):
            if meta.get(k):
                tk[k] = meta[k]
        tk["contrast"] = {"text_on_bg": round(min(design.contrast(tk["colors"]["text"], tk["colors"]["bg1"]), design.contrast(tk["colors"]["text"], tk["colors"]["bg2"])), 2),
                          "cardText_on_card": round(design.contrast(tk["colors"]["cardText"], tk["colors"]["card"]), 2),
                          "btnText_on_primary": round(design.contrast(tk["colors"]["btnText"], tk["colors"]["primary"]), 2)}
    if th == "auto":  # mood words -> composed look (scripts/theme_auto.py)
        au = theme_auto.compose(spec, tk)
        if au.get("palette"):
            tk["colors"].update(au["palette"])
            tk["palette"] = "auto-" + au["recipe"]
            tk["contrast"] = {"text_on_bg": round(min(design.contrast(tk["colors"]["text"], tk["colors"]["bg1"]), design.contrast(tk["colors"]["text"], tk["colors"]["bg2"])), 2),
                              "cardText_on_card": round(design.contrast(tk["colors"]["cardText"], tk["colors"]["card"]), 2),
                              "btnText_on_primary": round(design.contrast(tk["colors"]["btnText"], tk["colors"]["primary"]), 2)}
        if au.get("baseTheme"):
            tk["baseTheme"] = au["baseTheme"]
        if au.get("fonts"):
            tk["fonts"] = {**au["fonts"], "embeddable": au["fonts"]["display"].startswith("Noto")}
        if au.get("motion") and tk["motion"] != "calm":
            tk["motion"] = au["motion"]
        meta = {"host": True, "music": au.get("music")}
    if meta.get("fonts"):
        tk["fonts"] = {"display": meta["fonts"]["display"], "body": meta["fonts"].get("body", tk["fonts"]["body"]), "embeddable": False}
    if meta.get("motion") and tk["motion"] != "calm":
        tk["motion"] = meta["motion"]
    return tk


def tokens_css(tk: dict) -> str:
    """CSS variables + font pair from the tokens (appended after the engine styles)."""
    t = tk["type"]
    f = tk["fonts"]
    serif = {"Gowun Batang", "Noto Serif KR", "Nanum Myeongjo", "Song Myung"}
    body_fb = '"Noto Serif KR","Noto Sans KR"' if f["body"] in serif else '"Noto Sans KR"'
    disp_fb = '"Noto Serif KR"' if f["display"] in serif else '"Noto Sans KR"'
    sys_fb = '"Apple SD Gothic Neo","Malgun Gothic",sans-serif'
    # the embedded Noto fonts come right after the chosen font and before system fonts, so it also looks right offline
    return ("/* TS:CSS BEGIN */\n:root{--t-title:%dpx;--t-q:%dpx;--t-c:%dpx;--t-b:%dpx;--t-s:%dpx;--btn-h:%dpx;"
            "--font-body:\"%s\",%s,%s;--font-display:\"%s\",%s,%s!important}\n"
            % (t["title"], t["question"], t["choice"], t["body"], t["small"], t["floor"]["button_h"],
               f["body"], body_fb, sys_fb, f["display"], disp_fb, sys_fb)
            + ".title{font-size:var(--t-title)}\n")


def assemble(spec: dict, tokens: dict, out: Path) -> tuple[int, dict]:
    """Write the HTML. Returns (bytes, info)."""
    spec = copy.deepcopy(spec)
    info: dict = {}
    mech = spec["mechanic"]
    items = spec["items"]
    if spec.get("shuffleChoices", True) and mech in specs.QUIZ_LIKE:
        info["balanced"] = specs.balance_choices(items, int((spec.get("design") or {}).get("seed", 0)))
    c = tokens["colors"]
    use = spec.get("use", "class")
    device = spec.get("device", "board" if use == "class" else "tablet")
    teams = spec.get("teams", 0)
    spec_out = {k: v for k, v in spec.items() if k not in ("items", "title", "subtitle")}
    spec_out["tokens"] = tokens
    music = theme_meta(theme_for(tokens, spec)).get("music")
    if theme_for(tokens, spec) == "auto":
        au = theme_auto.compose(spec, tokens)
        spec_out["autoTheme"] = au["config"]
        music = au.get("music")
    spec_out["device"] = device
    theme = theme_for(tokens, spec)
    data = {
        "title": spec["title"], "subtitle": spec.get("subtitle", ""), "theme": tokens["baseTheme"],
        "themeOverride": {"primary": c["primary"], "accent": c["accent"], "bg1": c["bg1"], "bg2": c["bg2"], "text": c["text"], "muted": c["text"],
                          "card": c["card"], "cardBorder": c["cardBorder"], "cardText": c["cardText"], "btnText": c["btnText"],
                          "good": c["good"], "bad": c["bad"], "font": '"%s"' % tokens["fonts"]["display"], "glow": "none", **({"mood": music} if music else {})},
        "credit": spec.get("credit") is True, "teams": teams, "teamChoice": device == "board" or teams > 0, "timer": spec.get("timer", 0),
        "music": bool(tokens["sound"]["music"]) and spec.get("music", True), "calm": tokens["motion"] == "calm",
        "mascots": device != "phone" and use == "class" and theme not in ("auto",) and not theme_meta(theme).get("host"), "items": items, "spec": spec_out,
    }
    parts = [(COMP / "core.js").read_text(encoding="utf-8"), (COMP / f"{mech}.js").read_text(encoding="utf-8"),
             (THEMES / "default.js").read_text(encoding="utf-8")]
    if theme == "auto":  # parts of ported themes (hosts, staging) used by the composed look
        for pt in theme_auto.compose(spec, tokens)["config"]["partThemes"]:
            parts.append((THEMES / f"{pt}.js").read_text(encoding="utf-8"))
    if theme != "default":
        parts.append((THEMES / f"{theme}.js").read_text(encoding="utf-8"))
    logic = "/* TS:BUILD v1 */\n/* TS:COMPONENTS BEGIN */\n" + HEAD + "\n".join(parts) + FOOT + "/* TS:COMPONENTS END */\n"
    css = tokens_css(tokens) + (COMP / "components.css").read_text(encoding="utf-8")
    if (THEMES / f"{theme}.css").exists():
        css += "\n" + (THEMES / f"{theme}.css").read_text(encoding="utf-8")
    css += "\n/* TS:CSS END */\n"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "d.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        (td / "l.js").write_text(logic, encoding="utf-8")
        (td / "s.css").write_text(css, encoding="utf-8")
        size = build(td / "d.json", td / "l.js", out, td / "s.css")
    info["theme"] = theme
    return size, info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--tokens", type=Path)
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--no-fonts", action="store_true", help="keep the Google Fonts link instead of embedding Noto KR")
    ap.add_argument("--yes", action="store_true", help="agree to install the small font tool (fonttools) if it is missing")
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text(encoding="utf-8"))
    errs = specs.validate(spec)
    if errs:
        print("SPEC FIX NEEDED:\n - " + "\n - ".join(errs))
        return 2
    tokens = json.loads(a.tokens.read_text(encoding="utf-8")) if a.tokens else make_tokens(spec)
    terr = design.validate_tokens(tokens)
    if terr:
        print("TOKENS FIX NEEDED:\n - " + "\n - ".join(terr))
        return 2
    size, info = assemble(spec, tokens, a.out)
    html = a.out.read_text(encoding="utf-8")
    note = ""
    if spec.get("libs"):
        try:
            html, lrep = inline.apply(html, list(spec["libs"]), auto=True, allow_modern=spec.get("allow_modern") is True)
        except ValueError as exc:
            print("SPEC FIX NEEDED:\n - " + str(exc))
            return 2
        note += f", libs={'+'.join(lrep['inlined'])}"
    if not a.no_fonts:
        html, frep = embed.embed(html, consent=a.yes)
        if frep.get("embedded"):
            note += f", fonts embedded ({frep['before_bytes'] // 1024} KB -> {frep['after_bytes'] // 1024} KB)"
        else:
            note += ", fonts: " + frep.get("reason", "not embedded")
            if frep.get("prompt"):
                print("ASK TEACHER: " + frep["prompt"] + "  (agree -> rerun with --yes)")
    a.out.write_text(html, encoding="utf-8")
    size = len(html.encode("utf-8"))
    print(f"built {spec['mechanic']} -> {a.out} ({size // 1024} KB, palette={tokens['palette']}, theme={info['theme']}, balanced={info.get('balanced', 0)}{note})")
    if a.no_check:
        return 0
    r = subprocess.run([sys.executable, str(HERE / "check_game.py"), str(a.out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip())
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
