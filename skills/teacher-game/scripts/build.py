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
import random
import re
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
import layout_auto  # noqa: E402
import theme_auto  # noqa: E402

for _sub in ("fonts", "vendor", "tools", "design"):
    sys.path.insert(0, str(SKILL / "shared" / _sub))
import embed  # noqa: E402  (shared/fonts/embed.py)
import system as ds  # noqa: E402  (shared/design/system.py: type, motion, polish layer)
import inline  # noqa: E402  (shared/vendor/inline.py)
from build_game import build  # noqa: E402


_SVG_DROP_BLOCK = re.compile(r"<\s*(script|foreignObject|iframe|object|embed|style|animate|set)\b.*?<\s*/\s*\1\s*>", re.I | re.S)
_SVG_DROP_TAG = re.compile(r"<\s*/?\s*(script|foreignObject|iframe|object|embed|style|animate|set)\b[^>]*>", re.I)
_SVG_ON_ATTR = re.compile(r"""\s+on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", re.I)
_SVG_HREF_BAD = re.compile(r"""\s+(?:xlink:)?href\s*=\s*(?:"\s*(?:javascript|data|vbscript):[^"]*"|'\s*(?:javascript|data|vbscript):[^']*')""", re.I)


def sanitize_svg(svg: str) -> str:
    """custom_svg is AI-written and later set via innerHTML: drop script/foreignObject/iframe, on* handlers and javascript: links."""
    s = str(svg)
    prev = None
    while prev != s:  # repeat so nested payloads like <scr<script>ipt> cannot re-form
        prev = s
        s = _SVG_DROP_BLOCK.sub("", s)
        s = _SVG_DROP_TAG.sub("", s)
        s = _SVG_ON_ATTR.sub("", s)
        s = _SVG_HREF_BAD.sub("", s)
    return s


def sanitize_css(css: str) -> str:
    """custom_css goes into the page's <style>: no '<' (so '</style>' cannot close it), no @import, no javascript:/expression()."""
    s = str(css).replace("<", "")
    return re.sub(r"@import[^;]*;?|expression\s*\([^)]*\)|javascript:", "", s, flags=re.I)

# Game Wow kit (shared/juice): inside the skill when installed (sync copies it), else the repo root
JUICE = SKILL / "shared" / "juice" if (SKILL / "shared" / "juice" / "juice.js").exists() else SKILL.parent.parent / "shared" / "juice"
USE_JUICE = True  # --no-juice builds the same spec without the kit (before/after comparison)
PORTRAIT_MECHS = ("quiz",)  # mechanics that have a real portrait layout (assets/layouts/portrait.css); other mechanics on a phone ask to turn it
FONT_CHOICES = ("sans", "serif", "rounded", "system")  # design.font: sans/rounded = the embedded studio face (TS Sans), serif = Noto Serif KR; system = no embedded font at all
HEAD_META_NAMES = ("robots", "description", "theme-color", "author")
COMP = SKILL / "assets" / "components"
THEMES = SKILL / "assets" / "themes"
LAYOUTS = SKILL / "assets" / "layouts"
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


def layout_for(spec: dict, tokens: dict) -> tuple[dict, str, dict | None]:
    """(layout config, theme id, auto-theme composition or None). THE chooser: build.py and the preview tools (style_auto.py / layout_auto.py --spec) all call it."""
    th = theme_for(tokens, spec)
    au = theme_auto.compose(spec, tokens) if th == "auto" else None
    return layout_auto.compose(spec, tokens, (au["recipe"] if au else th), (au["style"] if au else "")), th, au


def look_line(lay: dict, au: dict | None) -> str:
    """One line that says what was chosen (so nobody has to open the picture to know)."""
    why = (au or {}).get("style_why", "")
    return "look: style=%s%s layout=%s choice=%s card=%s score=%s title=%s" % (lay.get("style") or "-", f"({why})" if why else "", lay.get("layout"), lay.get("choice"),
                                                                          lay.get("card"), lay.get("score"), lay.get("title"))


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
            tk["palette"] = "auto-" + au["style"]
            tk["contrast"] = {"text_on_bg": round(min(design.contrast(tk["colors"]["text"], tk["colors"]["bg1"]), design.contrast(tk["colors"]["text"], tk["colors"]["bg2"])), 2),
                              "cardText_on_card": round(design.contrast(tk["colors"]["cardText"], tk["colors"]["card"]), 2),
                              "btnText_on_primary": round(design.contrast(tk["colors"]["btnText"], tk["colors"]["primary"]), 2)}
        if au.get("baseTheme"):
            tk["baseTheme"] = au["baseTheme"]
        if au.get("fonts"):
            tk["fonts"] = {**au["fonts"], "embeddable": au["fonts"]["display"] in ("TS Sans", "Noto Sans KR", "Noto Serif KR")}
        if au.get("motion") and tk["motion"] != "calm":
            tk["motion"] = au["motion"]
        meta = {"host": True, "music": au.get("music")}
    if meta.get("fonts"):
        tk["fonts"] = {"display": meta["fonts"]["display"], "body": meta["fonts"].get("body", tk["fonts"]["body"]), "embeddable": False}
    if meta.get("motion") and tk["motion"] != "calm":
        tk["motion"] = meta["motion"]
    if d.get("palette_from"):  # the user's own logo/template colours win over the theme's (design.palette_from: file | "saved")
        design.apply_palette_from(tk, d["palette_from"])
    font = d.get("font") or spec.get("font")
    if font in FONT_CHOICES:  # design.font beats the theme's font (the font files for the unused family are then not embedded either)
        fam = "Noto Serif KR" if font == "serif" else "TS Sans"
        tk["fonts"] = {"display": fam, "body": fam, "embeddable": font != "system"}
        tk["fontChoice"] = font
    return tk


def _on(bg: str) -> str:
    """Text colour (black or white) with the better contrast on a state colour (>= 4.5 when the palette allows it)."""
    return "#0b0b0b" if design.contrast("#0b0b0b", bg) >= design.contrast("#ffffff", bg) else "#ffffff"


def tokens_css(tk: dict) -> str:
    """CSS variables + font pair from the tokens (appended after the engine styles)."""
    t = tk["type"]
    f = tk["fonts"]
    serif = {"Gowun Batang", "Noto Serif KR", "Nanum Myeongjo", "Song Myung"}
    body_fb = '"Noto Serif KR","TS Sans","Noto Sans KR"' if f["body"] in serif else '"TS Sans","Pretendard","Noto Sans KR"'
    disp_fb = '"Noto Serif KR"' if f["display"] in serif else '"TS Sans","Pretendard","Noto Sans KR"'
    sys_fb = '"Apple SD Gothic Neo","Malgun Gothic",sans-serif'
    colors = tk["colors"]
    dark = sum(int(colors["bg1"][i:i + 2], 16) for i in (1, 3, 5)) < 330
    vig = ":root{--vig:%s}\n" % (".35" if dark else "0")  # the dark edge only helps on dark scenes; on a light scene it only makes the corners look dirty
    if tk.get("accentDeco"):  # the source's own accent for dots/stars (custom_css / custom_svg may use var(--accent-deco)); never used for text
        vig += ":root{--accent-deco:%s}\n" % tk["accentDeco"]
    choice = tk.get("fontChoice")
    if choice == "system":
        stack = 'system-ui,-apple-system,"Segoe UI","Malgun Gothic","Apple SD Gothic Neo",sans-serif'
        return ("/* TS:CSS BEGIN */\n:root{--t-title:%dpx;--t-q:%dpx;--t-c:%dpx;--t-b:%dpx;--t-s:%dpx;--btn-h:%dpx;--font-body:%s;--font-display:%s!important}\n"
                % (t["title"], t["question"], t["choice"], t["body"], t["small"], t["floor"]["button_h"], stack, stack) + vig
                + ".title{font-size:var(--t-title)}\n" + ":root{--on-good:%s;--on-bad:%s}\n" % (_on(colors["good"]), _on(colors["bad"])))
    extra = ".title,.h1,.h2{font-weight:800}\n" if choice == "rounded" else ""
    # the embedded Noto fonts come right after the chosen font and before system fonts, so it also looks right offline
    return ("/* TS:CSS BEGIN */\n:root{--t-title:%dpx;--t-q:%dpx;--t-c:%dpx;--t-b:%dpx;--t-s:%dpx;--btn-h:%dpx;"
            "--font-body:\"%s\",%s,%s;--font-display:\"%s\",%s,%s!important}\n"
            % (t["title"], t["question"], t["choice"], t["body"], t["small"], t["floor"]["button_h"],
               f["body"], body_fb, sys_fb, f["display"], disp_fb, sys_fb)
            + vig + extra + ".title{font-size:var(--t-title)}\n"
            + ":root{--on-good:%s;--on-bad:%s}\n" % (_on(tk["colors"]["good"]), _on(tk["colors"]["bad"])))


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
    lay, _th, _au = layout_for(spec, tokens)
    info["look"] = look_line(lay, _au)
    info["layout"] = lay
    spec_out["layoutCfg"] = lay
    if spec.get("custom_svg"):
        spec_out["customSvg"] = sanitize_svg(spec["custom_svg"])
    spec_out.pop("custom_css", None)
    spec_out.pop("custom_svg", None)
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
        "transition": lay["transition"], "credit": spec.get("credit") is True, "teams": teams, "teamChoice": device == "board" or teams > 0, "timer": spec.get("timer", 0),
        "music": bool(tokens["sound"]["music"]) and spec.get("music", True), "calm": tokens["motion"] == "calm",
        "mascots": device != "phone" and use == "class" and theme not in ("auto",) and not theme_meta(theme).get("host"), "items": items, "spec": spec_out,
        "portrait": device == "phone" and mech in PORTRAIT_MECHS,
    }
    if spec.get("credit") is True:
        data["creditUrl"] = "https://github.com/zln02/teacher-studio"  # only a game that asked for the credit carries an outside address
    if isinstance(spec.get("back"), dict) and spec["back"].get("href"):
        data["back"] = {"href": str(spec["back"]["href"]), "label": str(spec["back"].get("label") or "돌아가기")}
    parts = [(COMP / "core.js").read_text(encoding="utf-8"), (COMP / f"{mech}.js").read_text(encoding="utf-8"),
             (THEMES / "default.js").read_text(encoding="utf-8")]
    if theme == "auto":  # parts of ported themes (hosts, staging) used by the composed look
        for pt in theme_auto.compose(spec, tokens)["config"]["partThemes"]:
            parts.append((THEMES / f"{pt}.js").read_text(encoding="utf-8"))
    if theme != "default":
        parts.append((THEMES / f"{theme}.js").read_text(encoding="utf-8"))
    juice_on = USE_JUICE and spec.get("juice") is not False and (JUICE / "juice.js").exists()
    pre = ""
    if juice_on:  # kit first (globals), tuned by spec.juice (optional JSON); the adapter goes last so it wraps the final engine hooks
        pre = (JUICE / "juice.js").read_text(encoding="utf-8") + "\n" + (JUICE / "juice-motion.js").read_text(encoding="utf-8") + "\n"
        if isinstance(spec.get("juice"), dict):
            pre += "Juice.configure(" + json.dumps(spec["juice"], ensure_ascii=False) + ");\n"
        parts.append((COMP / "juice-game.js").read_text(encoding="utf-8"))
    logic = "/* TS:BUILD v1 */\n/* TS:COMPONENTS BEGIN */\n" + pre + HEAD + "\n".join(parts) + FOOT + "/* TS:COMPONENTS END */\n"
    css = tokens_css(tokens) + (COMP / "components.css").read_text(encoding="utf-8")
    css += "\n" + ds.polish_css("game")  # shared finishing layer: before the layout/style packs, the theme and the user's custom_css (those win)
    css += "\n" + (LAYOUTS / "layouts.css").read_text(encoding="utf-8")
    if data["portrait"]:
        css += "\n" + (LAYOUTS / "portrait.css").read_text(encoding="utf-8")
    if juice_on:
        css += "\n" + (JUICE / "juice.css").read_text(encoding="utf-8")
    if (THEMES / f"{theme}.css").exists():
        css += "\n" + (THEMES / f"{theme}.css").read_text(encoding="utf-8")
    if spec.get("custom_css"):  # AI-written extra flair; validated by specs.validate, scanned by check_game like all other css
        css += "\n/* custom_css */\n" + sanitize_css(spec["custom_css"])
    css += "\n/* TS:CSS END */\n"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "d.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        (td / "l.js").write_text(logic, encoding="utf-8")
        (td / "s.css").write_text(css, encoding="utf-8")
        size = build(td / "d.json", td / "l.js", out, td / "s.css", online=spec.get("online") is True)
    info["theme"] = theme
    return size, info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--tokens", type=Path)
    ap.add_argument("--seed", type=int, default=None, help="reproduce a look (same as design.seed in the spec); default = a fresh random look")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--ok-content", action="store_true", help="build even when the question review has advice (the user supplied these exact questions, or you already revised once)")
    ap.add_argument("--verbose", action="store_true", help="print every check line (default: only FAIL/WARN lines and the RESULT line)")
    ap.add_argument("--review", nargs="?", const="", default=None, metavar="DIR", help="after the check, also write the design contact sheet PNG (design_review.py) into DIR (default: a review/ folder next to --out)")
    ap.add_argument("--no-juice", action="store_true", help="build without the Game Wow kit (for before/after comparison only)")
    ap.add_argument("--no-fonts", action="store_true", help="do not embed Noto KR (the page then uses system fonts; a Google Fonts link is added only when the spec has \"online\": true)")
    ap.add_argument("--yes", action="store_true", help="agree to install the small font tool (fonttools) if it is missing")
    a = ap.parse_args()
    global USE_JUICE
    USE_JUICE = not a.no_juice
    try:
        spec = json.loads(a.spec.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"SPEC FIX NEEDED:\n - spec file not found: {a.spec} (write the spec first; examples: {HERE.parent / 'assets' / 'spec-examples'})")
        return 2
    except ValueError as exc:
        print(f"SPEC FIX NEEDED:\n - the spec is not valid JSON: {exc} (check commas, quotes and brackets)")
        return 2
    if not isinstance(spec, dict):
        print("SPEC FIX NEEDED:\n - the spec must be one JSON object {...}")
        return 2
    try:  # a shipped fixture built as itself is stamped, so the likeness check reports it as a test build
        import example_likeness
        is_fixture = bool(example_likeness.is_fixture(spec, [SKILL / "assets" / "spec-examples"]))
    except ImportError:
        is_fixture = False
    d0 = spec.setdefault("design", {})
    if a.seed is not None:
        d0["seed"] = a.seed
    elif "seed" not in d0:  # variety by default: a fresh combination every build; the seed is printed and stored in the page
        d0["seed"] = random.SystemRandom().randrange(1, 100000)
        print(f"design.seed={d0['seed']} (같은 모양으로 다시 만들려면 spec의 design.seed에 이 숫자를 적어요)")
    errs = specs.validate(spec)
    if errs:
        print("SPEC FIX NEEDED:\n - " + "\n - ".join(errs))
        return 2
    advice = specs.content_review(spec)
    if advice and not a.ok_content and not a.no_check:  # stop in a second, before the slow part: content is the one thing only the author can fix
        print("CONTENT FIX (edit these questions in the spec and run the same command again; nothing was built):" + "".join(chr(10) + " - " + x for x in advice))
        print("If the user supplied these exact questions, or you already revised once, add --ok-content to build as is.")
        return 3
    if d0.get("palette_from"):
        d0["palette_from"] = design.resolve_palette_from(d0["palette_from"], a.spec.resolve().parent)
    try:
        tokens = json.loads(a.tokens.read_text(encoding="utf-8")) if a.tokens else make_tokens(spec)
    except ValueError as exc:  # e.g. design.palette_from file missing / unreadable colours
        print(f"SPEC FIX NEEDED:\n - design.palette_from: {exc}")
        return 2
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
    online = spec.get("online") is True
    fchoice = (d0.get("font") or spec.get("font") or "")
    if not a.no_fonts and fchoice != "system":
        fams = ["TS Sans" if "TS Sans" in html else "Noto Sans KR"] + (["Noto Serif KR"] if fchoice in ("", "serif") and "Noto Serif KR" in html else [])
        html, frep = embed.embed(html, families=fams, consent=a.yes)
        if frep.get("embedded"):
            note += f", fonts embedded ({frep['before_bytes'] // 1024} KB -> {frep['after_bytes'] // 1024} KB)"
        else:
            note += ", fonts: " + frep.get("reason", "not embedded")
            if frep.get("prompt"):
                print("ASK TEACHER: " + frep["prompt"] + "  (agree -> rerun with --yes)")
    if not online:
        html = embed.go_offline(html)
    metas = f'<meta name="ts-seed" content="{d0["seed"]}">\n<meta name="ts-look" content="{info["look"][6:]}">'
    if is_fixture:
        metas += '\n<meta name="ts-fixture" content="1">'
    for hm in spec.get("head_meta") or []:
        if isinstance(hm, dict) and hm.get("name") in HEAD_META_NAMES:
            metas += '\n<meta name="%s" content="%s">' % (hm["name"], str(hm.get("content", "")).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;"))
    html = html.replace("<head>", "<head>\n" + metas, 1) if "<head>" in html else html
    a.out.write_text(html, encoding="utf-8")
    size = len(html.encode("utf-8"))
    print(info["look"])
    if spec.get("device") == "phone" and spec["mechanic"] not in PORTRAIT_MECHS:
        print(f"NOTE: {spec['mechanic']} has no portrait layout yet: held upright, the phone asks to be turned sideways (quiz has a full portrait layout)")
    print(f"built {spec['mechanic']} -> {a.out} ({size // 1024} KB, palette={tokens['palette']}, theme={info['theme']}, balanced={info.get('balanced', 0)}{note})")
    for line in advice:  # built anyway on --ok-content: keep the advice visible
        print("CONTENT (kept as is) " + line)
    if a.no_check:
        print(f"PARTIAL {a.out.resolve()} (checks disabled)")
        return 0
    r = subprocess.run([sys.executable, str(HERE / "check_game.py"), str(a.out)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = r.stdout.strip().splitlines()
    if a.verbose:
        print("\n".join(lines))
    else:  # short by default: the lines to act on + the verdict
        shown = [ln for ln in lines if ln.startswith(("FAIL", "WARN", "SKIP", "RESULT"))]
        passed = sum(1 for ln in lines if ln.startswith("PASS"))
        print("\n".join(shown) if shown else "\n".join(lines[-3:]))
        print(f"({passed} checks passed; --verbose lists them)")
    codes = [r.returncode]
    if a.review is not None and r.returncode in (0, 2):
        rdir = Path(a.review) if a.review else a.out.resolve().parent / "review"
        try:
            rv = subprocess.run([sys.executable, str(HERE / "design_review.py"), str(a.out), "--out", str(rdir)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            print((rv.stdout or rv.stderr).strip())
            codes.append(rv.returncode)
        except subprocess.TimeoutExpired:
            print("SKIP 화면 점검을 정해진 시간 안에 끝내지 못했어요.")
            codes.append(2)
    if any(code not in (0, 2) for code in codes):
        print(f"NOT READY {a.out.resolve()}")
        return 1
    if 2 in codes:
        print(f"PARTIAL {a.out.resolve()}")
        return 2
    print(f"READY {a.out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
