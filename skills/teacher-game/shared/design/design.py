#!/usr/bin/env python3
"""Shared design system for Teacher Studio: deterministic design tokens (no AI needed).

One generator for games, slides, motion, posters, invitations, print and web pages, so a mood word
such as "따뜻하게" or "고급스럽게" looks the same everywhere.

Usage:
    python3 design.py --subject 과학 --grade 5 --mood 긴장감 [--use class|personal|present|poster|invite|print|web]
                      [--large] [--seed N] [--theme ID]
    python3 design.py --validate        # check every palette in palettes.json
    python3 design.py --list            # uses, moods, palettes

Prints tokens JSON (schema: tokens.schema.json). Same input -> same output.
- class    : large type floor (question 60 / choice 48 / small 34 px on the 1920x1080 stage), motion by mood
- personal : normal type floor (question 44 / choice 36); --large (e.g. for grandparents) = class floor
- present  : slides (1920x1080) | poster: A3 | invite: 5x7in card | print: A4 handout | web: responsive page
  (tokens.canvas names the reference canvas the sizes are written for)
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


def generate(subject: str = "", grade: int = 5, mood: str = "", use: str = "class", seed: int = 0,
             large: bool = False, theme: str = "default") -> dict:
    """Build tokens from the request words. Deterministic for the same inputs."""
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
    return {
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
    print(json.dumps(generate(a.subject, a.grade, a.mood, a.use, a.seed, a.large, a.theme), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
