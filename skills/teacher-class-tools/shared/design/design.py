#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Shared design system for Teacher Studio: deterministic design tokens (no AI needed).

One generator for games, slides, motion, posters, invitations, print and web pages, so a mood word
such as "따뜻하게" or "고급스럽게" looks the same everywhere.

Usage:
    python3 design.py --subject 과학 --grade 5 --mood 긴장감 [--use class|personal|present|poster|invite|print|web]
                      [--large] [--seed N] [--theme ID] [--palette-from FILE|saved]
    python3 design.py --validate        # check every palette in palettes.json
    python3 design.py --list            # uses, moods, palettes

Prints tokens JSON (schema: tokens.schema.json). Same input -> same output.
- class    : large type floor (question 60 / choice 48 / small 34 px on the 1920x1080 stage), motion by mood
- personal : normal type floor (question 44 / choice 36); --large (e.g. for grandparents) = class floor
- present  : slides (1920x1080) | poster: A3 | invite: 5x7in card | print: A4 handout | web: responsive page
  (tokens.canvas names the reference canvas the sizes are written for)
--palette-from takes the user's OWN colours (JSON from color_from.py, or "saved" = the default saved in ~/.teacher-studio/prefs.json) instead of a built-in
palette; text colours are re-fitted in lightness only so contrast stays >= 4.5. Without it nothing changes. Builders read spec "design": {"palette_from": ...}.
Moods may be given in everyday words ("따뜻하게", "고급스럽게", "깔끔하게"): see palettes.json "moods.aliases".
tokens.fonts.embeddable = true means every font in the pair can be embedded offline (Noto Sans/Serif KR, see shared/fonts).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
PAL_PATH = HERE / "palettes.json"
SCHEMA_PATH = HERE / "tokens.schema.json"
GAME_USES = ("class", "personal")
USES = ("class", "personal", "present", "poster", "invite", "print", "web")
USE_LABEL = {"class": "교실 게임·수업(칠판)", "personal": "개인·가족용", "present": "발표 슬라이드", "poster": "포스터",
             "invite": "초대장·카드", "print": "인쇄물(학습지·통신문)", "web": "웹페이지"}


def _lum(hexc: str) -> float:
    """Relative luminance (WCAG)."""
    h = hexc.lstrip("#")
    ch = []
    for i in (0, 2, 4):
        v = int(h[i:i + 2], 16) / 255
        ch.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two #rrggbb colors."""
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def palette_issues(name: str, p: dict) -> list[str]:
    """Return contrast problems for one palette (empty = valid)."""
    out = []
    for fg, bg, need in (("text", "bg1", 4.5), ("text", "bg2", 4.5), ("cardText", "card", 4.5), ("btnText", "primary", 4.5),
                         ("good", "card", 3.0), ("bad", "card", 3.0), ("primary", "bg1", 3.0)):
        r = contrast(p[fg], p[bg])
        if r < need:
            out.append(f"{name}: {fg} on {bg} = {r:.2f} (< {need})")
    return out


def load() -> dict:
    """Load palettes.json."""
    return json.loads(PAL_PATH.read_text(encoding="utf-8"))


def normalize_mood(mood: str, data: dict | None = None) -> str:
    """Map everyday wording ("따뜻하게", "고급스럽게") to a mood key; unknown words pass through."""
    data = data or load()
    return data.get("moods", {}).get("aliases", {}).get(mood, mood)


def _rank(key: str, seed: int) -> int:
    """Stable pseudo-random tiebreak."""
    return int(hashlib.sha256(f"{key}|{seed}".encode()).hexdigest()[:8], 16)


_LAST_DECO = None  # set by load_user_palette, read by apply_palette_from


def load_user_palette(src) -> dict:
    """The user's own colours as a complete, contrast-checked dict of the 11 colour keys.

    src: a dict (palette/tokens JSON: uses its "colors"), a path to such a JSON file (color_from.py output), or "saved" (the default in prefs.json).
    Partial dicts are completed and failing text colours re-fitted (lightness only) by color_from.fit_palette. Raises ValueError with a fix hint."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import color_from  # lazy: only needed when the user brings their own colours
    if isinstance(src, str):
        if src.strip().lower() in ("saved", "prefs"):
            pf = Path.home() / ".teacher-studio" / "prefs.json"
            try:
                src = (json.loads(pf.read_text(encoding="utf-8")) or {}).get("palette") or {}
            except (OSError, ValueError):
                src = {}
            if not src:
                raise ValueError("저장된 내 팔레트가 없어요. color_from.py <파일> --save-default 로 먼저 저장해 주세요. (palette_from: saved)")
        else:
            f = Path(src).expanduser()
            if not f.exists():
                raise ValueError(f"palette_from file not found: {src}")
            try:
                src = json.loads(f.read_text(encoding="utf-8"))
            except ValueError as exc:
                raise ValueError(f"palette_from is not valid JSON: {src} ({exc})")
    if not isinstance(src, dict):
        raise ValueError("palette_from must be a file path, 'saved' or a colours object")
    cols = src.get("colors") if isinstance(src.get("colors"), dict) else src
    if not any(k in cols for k in ("primary", "accent", "bg1")):
        raise ValueError("palette_from needs at least colors.primary (a #rrggbb hex)")
    try:
        fitted = color_from.fit_palette(cols, (src.get("mode") == "dark") if src.get("mode") else None)
    except color_from.ColorFromError as exc:
        raise ValueError(str(exc))
    deco = src.get("accentDeco") or cols.get("accentDeco")
    global _LAST_DECO
    _LAST_DECO = deco.lower() if isinstance(deco, str) and len(deco) == 7 and deco.startswith("#") else None  # decoration colour: the accent as the source has it (never used for text)
    issues = palette_issues("user", fitted)
    if issues:
        raise ValueError("palette_from could not be made readable: " + "; ".join(issues))
    return fitted


def resolve_palette_from(src, base) -> object:
    """A relative palette_from file name is looked up next to the spec file (`base` = that folder); "saved", dicts and absolute paths pass through."""
    if isinstance(src, str) and src.strip().lower() not in ("saved", "prefs") and not Path(src).is_absolute():
        cand = Path(base) / src
        if cand.exists():
            return str(cand.resolve())
    return src


def apply_palette_from(tokens: dict, src) -> dict:
    """Replace the colours in tokens with the user's own palette (in place; returns tokens). Everything else (type sizes, motion, fonts) is untouched."""
    cols = load_user_palette(src)
    tokens["colors"].update(cols)
    tokens["palette"] = "user"
    tokens["contrast"] = {"text_on_bg": round(min(contrast(cols["text"], cols["bg1"]), contrast(cols["text"], cols["bg2"])), 2),
                          "cardText_on_card": round(contrast(cols["cardText"], cols["card"]), 2),
                          "btnText_on_primary": round(contrast(cols["btnText"], cols["primary"]), 2)}
    tokens["userPalette"] = True
    if _LAST_DECO:
        tokens["accentDeco"] = _LAST_DECO
    return tokens


def generate(subject: str = "", grade: int = 5, mood: str = "", use: str = "class", seed: int = 0,
             large: bool = False, theme: str = "default", palette_from=None) -> dict:
    """Build tokens from the request words. Deterministic for the same inputs. palette_from (optional): the user's own colours, see load_user_palette."""
    if use not in USES:
        raise ValueError(f"use must be one of {', '.join(USES)}")
    data = load()
    mood = normalize_mood(mood, data)
    calm_moods = set(data["moods"]["calm"])
    high_moods = set(data["moods"]["high"])
    pals = {n: p for n, p in data["palettes"].items() if use in p.get("uses", GAME_USES)}
    scored = []
    for name, p in pals.items():
        score = (3 if mood and mood in p["mood"] else 0) + (2 if subject and subject in p["subject"] else 0)
        if use == "personal" and "가족" in p["subject"]:
            score += 2
        scored.append((-score, _rank(f"{subject}|{grade}|{mood}|{name}", seed), name))
    scored.sort()
    name = scored[0][2]
    p = pals[name]
    pair = next(x for x in data["fonts"]["pairs"] if x["id"] == p["font"])
    scales = data["type_scales"]
    if use == "personal":
        scale = scales["personal_large"] if large else scales["personal"]
    elif use == "class":
        scale = scales["class_lowgrade"] if grade <= 2 else scales["class"]
    else:
        scale = scales[use]
    motion = "calm" if mood in calm_moods else ("high" if mood in high_moods and use == "class" else "normal")
    game = use in GAME_USES
    keys = ("bg1", "bg2", "text", "card", "cardText", "cardBorder", "primary", "btnText", "accent", "good", "bad")
    tokens = {
        "version": 1, "use": use, "palette": name, "seed": seed,
        "colors": {k: p[k] for k in keys},
        "fonts": {"display": pair["display"], "body": pair["body"], "embeddable": bool(pair.get("embeddable"))},
        "type": {k: v for k, v in scale.items() if k != "canvas"}, "canvas": scale.get("canvas", "1920x1080"),
        "motion": motion,
        "sound": {"sfx": game, "music": game and motion != "calm"},
        "baseTheme": p["baseTheme"], "bgType": p["bgType"], "theme": theme,
        "contrast": {"text_on_bg": round(min(contrast(p["text"], p["bg1"]), contrast(p["text"], p["bg2"])), 2),
                     "cardText_on_card": round(contrast(p["cardText"], p["card"]), 2),
                     "btnText_on_primary": round(contrast(p["btnText"], p["primary"]), 2)},
    }
    return apply_palette_from(tokens, palette_from) if palette_from else tokens


def validate_tokens(t: dict) -> list[str]:
    """Validate tokens against tokens.schema.json essentials; returns spec-fix hint strings."""
    errs = []
    sch = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for k in sch["required"]:
        if k not in t:
            errs.append(f"tokens.{k} missing")
    colors = t.get("colors", {})
    for k in sch["properties"]["colors"]["required"]:
        if k not in colors:
            errs.append(f"tokens.colors.{k} missing")
    if errs:
        return errs
    errs += palette_issues(t["palette"], colors)
    fl = t["type"]["floor"]
    for k in ("question", "choice", "body", "small"):
        if t["type"][k] < fl[k]:
            errs.append(f"tokens.type.{k}={t['type'][k]} is below the {t['use']} floor {fl[k]}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", default="")
    ap.add_argument("--grade", type=int, default=5)
    ap.add_argument("--mood", default="")
    ap.add_argument("--use", choices=list(USES), default="class")
    ap.add_argument("--large", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--theme", default="default")
    ap.add_argument("--palette-from", default=None, help="user's own colours: JSON from color_from.py, or 'saved'")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        d = load()
        print("uses:", ", ".join(f"{u}({USE_LABEL[u]})" for u in USES))
        print("moods:", ", ".join(sorted({m for p in d["palettes"].values() for m in p["mood"]})))
        print("aliases:", ", ".join(f"{k}->{v}" for k, v in d["moods"]["aliases"].items()))
        for n, p in d["palettes"].items():
            print(f"  {n}: mood={'/'.join(p['mood'])} uses={'/'.join(p['uses'])}")
        return 0
    if a.validate:
        bad = []
        for n, p in load()["palettes"].items():
            bad += palette_issues(n, p)
        print("\n".join(bad) if bad else f"all {len(load()['palettes'])} palettes valid")
        return 1 if bad else 0
    try:
        tk = generate(a.subject, a.grade, a.mood, a.use, a.seed, a.large, a.theme, a.palette_from)
    except ValueError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(json.dumps(tk, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
