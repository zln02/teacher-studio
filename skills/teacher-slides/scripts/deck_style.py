# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Slide style language: spec words -> one of the 12 shared styles + palette + composition rules (deterministic per seed).

The 12 styles come from shared/design/styles.py (same taxonomy as games). Here each style also gets a SLIDE composition language:
title treatment, card style, emphasis style, background generator, transition and which layout families it prefers.
Palettes: the style's own palette, or (seeded) a validated shared/design palette with the same light/dark tone.
Everything derived from colours is contrast-guarded here (muted text, emphasis colour, marker tints) so the page checker never has to.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
_SHARED = SKILL / "shared" if (SKILL / "shared" / "design").exists() else SKILL.parent.parent / "shared"
sys.path.insert(0, str(_SHARED / "design"))
import design as design_core  # noqa: E402
import styles as style_core  # noqa: E402

sys.path.insert(0, str(HERE))
import deck_context as dctx  # noqa: E402

STYLES = style_core.STYLES

# ---- composition language per style --------------------------------------------------------------------------------
# font: sans | serif   tw: title weight   ls: title letter-spacing(em)   title: treatment   card: card style   em: emphasis style
# bg: background generator   trans: slide entrance   prefer: layout family weights   rad: radius px
# The slide language follows the shared style table (shared/design/styles.py: grid, type weight/tracking, radius, ornaments). No glow, no 3D title,
# no weight above 800 (system.MAX_WEIGHT); the backdrop names are the matte set drawn by deck_art.background.
LANG: dict[str, dict] = {
    "neon-cyber": dict(font="sans", tw=700, ls=-0.04, title="rule", card="hair", em="color", bg="dotgrid", trans="fade", rad=6,
                       prefer={"editorial": 4, "split": 3, "stack": 3, "bigtype": 2, "bento": 1, "poster": 1}),
    "gold-luxury": dict(font="serif", tw=600, ls=-0.02, title="serif", card="hair", em="color", bg="frame", trans="fade", rad=2,
                        prefer={"poster": 4, "editorial": 4, "split": 2, "bigtype": 1, "bento": 1, "stack": 1}),
    "pop-colorful": dict(font="sans", tw=800, ls=-0.045, title="plain", card="sticker", em="marker", bg="blocks", trans="iris", rad=20,
                         prefer={"bento": 4, "bigtype": 4, "poster": 2, "split": 2, "stack": 1, "editorial": 1}),
    "festival-party": dict(font="sans", tw=800, ls=-0.04, title="plain", card="round", em="marker", bg="papercut", trans="iris", rad=28,
                           prefer={"stack": 4, "poster": 3, "bento": 2, "bigtype": 2, "split": 1, "editorial": 1}),
    "tv-gameshow": dict(font="sans", tw=800, ls=-0.035, title="rule", card="ticket", em="color", bg="panels", trans="wipe", rad=10,
                        prefer={"split": 5, "bigtype": 3, "bento": 1, "poster": 1, "stack": 1, "editorial": 1}),
    "glass-3d": dict(font="sans", tw=700, ls=-0.035, title="plain", card="soft", em="color", bg="planes", trans="fade", rad=28,
                     prefer={"bento": 5, "split": 3, "poster": 1, "editorial": 1, "stack": 1, "bigtype": 2}),
    "anime-cartoon": dict(font="sans", tw=800, ls=-0.045, title="plain", card="sticker", em="marker", bg="halftone", trans="wipe", rad=12,
                          prefer={"split": 4, "bigtype": 4, "bento": 2, "poster": 1, "stack": 1, "editorial": 1}),
    "pastel-cute": dict(font="sans", tw=760, ls=-0.035, title="underline", card="round", em="marker", bg="hills", trans="iris", rad=40,
                        prefer={"bento": 4, "stack": 3, "center": 2, "split": 2, "poster": 1, "editorial": 1, "bigtype": 1}),
    "retro-pixel": dict(font="sans", tw=800, ls=0.02, title="pixel", card="pixel", em="color", bg="pixel", trans="wipe", rad=0,
                        prefer={"split": 3, "bento": 3, "bigtype": 2, "stack": 2, "poster": 1, "editorial": 1}),
    "minimal-premium": dict(font="sans", tw=700, ls=-0.04, title="plain", card="hair", em="underline", bg="minimal", trans="fade", rad=2,
                            prefer={"editorial": 5, "poster": 3, "split": 2, "bigtype": 2, "stack": 1, "bento": 1}),
    "chalk-paper": dict(font="sans", tw=700, ls=-0.02, title="chalk", card="chalk", em="underline", bg="chalk", trans="fade", rad=14,
                        prefer={"stack": 4, "split": 3, "editorial": 2, "bento": 1, "poster": 1, "bigtype": 1}),
    "nature-calm": dict(font="sans", tw=700, ls=-0.035, title="underline", card="flat", em="color", bg="bands", trans="fade", rad=20,
                        prefer={"editorial": 3, "stack": 3, "split": 2, "poster": 2, "bento": 1, "bigtype": 1}),
}

# slides use the style's own (already restrained) palette: the calmer slide-only copies were retired with the neon looks
SLIDE_PAL: dict[str, dict] = {}

# what each purpose naturally looks like (weights; a mood word or an explicit style beats these)
PURPOSE_STYLE = {
    "수업": {"chalk-paper": 3, "nature-calm": 3, "pop-colorful": 3, "pastel-cute": 2, "glass-3d": 3, "anime-cartoon": 2, "minimal-premium": 1, "tv-gameshow": 2, "neon-cyber": 1, "retro-pixel": 1},
    "연수": {"minimal-premium": 4, "glass-3d": 4, "gold-luxury": 2, "nature-calm": 2, "neon-cyber": 2, "tv-gameshow": 1, "pastel-cute": 1, "chalk-paper": 1},
    "학부모 설명회": {"pastel-cute": 4, "nature-calm": 4, "minimal-premium": 2, "festival-party": 1, "gold-luxury": 1, "glass-3d": 1, "chalk-paper": 1},
    "발표": {"minimal-premium": 4, "gold-luxury": 3, "glass-3d": 3, "neon-cyber": 2, "nature-calm": 1, "tv-gameshow": 1},
    "동아리": {"pop-colorful": 4, "neon-cyber": 3, "anime-cartoon": 3, "retro-pixel": 3, "festival-party": 3, "tv-gameshow": 2, "glass-3d": 2},
    "개인": {k: 1 for k in STYLES},
}
# everyday mood words -> style weights (added on top of the purpose weights, x3)
MOOD_STYLE = {
    "따뜻": {"pastel-cute": 3, "nature-calm": 3, "chalk-paper": 1},
    "포근": {"pastel-cute": 3, "nature-calm": 3},
    "부드": {"pastel-cute": 3, "nature-calm": 2, "glass-3d": 1},
    "귀엽": {"pastel-cute": 4, "pop-colorful": 1},
    "깔끔": {"minimal-premium": 4, "glass-3d": 2, "nature-calm": 1},
    "단정": {"minimal-premium": 4, "gold-luxury": 1},
    "세련": {"minimal-premium": 3, "glass-3d": 3, "gold-luxury": 2},
    "고급": {"gold-luxury": 4, "minimal-premium": 2},
    "우아": {"gold-luxury": 3, "minimal-premium": 2, "pastel-cute": 1},
    "신나": {"pop-colorful": 3, "festival-party": 3, "anime-cartoon": 3, "tv-gameshow": 2},
    "신남": {"pop-colorful": 3, "festival-party": 3, "anime-cartoon": 3, "tv-gameshow": 2},
    "발랄": {"pop-colorful": 3, "pastel-cute": 2, "festival-party": 2},
    "힙": {"neon-cyber": 4, "retro-pixel": 3, "anime-cartoon": 2, "pop-colorful": 2, "glass-3d": 2},
    "트렌디": {"neon-cyber": 3, "glass-3d": 3, "pop-colorful": 2},
    "미래": {"neon-cyber": 4, "glass-3d": 3},
    "차분": {"nature-calm": 3, "minimal-premium": 3, "chalk-paper": 2},
    "자연": {"nature-calm": 5},
    "진지": {"minimal-premium": 2, "gold-luxury": 2, "chalk-paper": 2},
    "재미": {"pop-colorful": 2, "anime-cartoon": 2, "tv-gameshow": 2, "festival-party": 2},
    "레트로": {"retro-pixel": 5},
    "칠판": {"chalk-paper": 5},
}
SUBJECT_STYLE = {
    "과학": {"glass-3d": 2, "nature-calm": 2, "neon-cyber": 1, "chalk-paper": 2},
    "수학": {"chalk-paper": 2, "minimal-premium": 2, "glass-3d": 1},
    "역사": {"gold-luxury": 2, "minimal-premium": 2, "chalk-paper": 1},
    "영어": {"pop-colorful": 2, "pastel-cute": 1},
    "미술": {"pop-colorful": 2, "pastel-cute": 2},
    "음악": {"neon-cyber": 1, "pop-colorful": 1, "festival-party": 1},
    "체육": {"anime-cartoon": 2, "tv-gameshow": 2, "pop-colorful": 2},
}
PURPOSES = ("수업", "연수", "학부모 설명회", "발표", "동아리", "개인")
PURPOSE_ALIAS = {"수업": "수업", "학급": "수업", "교실": "수업", "연수": "연수", "교원": "연수", "학부모": "학부모 설명회", "설명회": "학부모 설명회",
                  "발표": "발표", "강연": "발표", "동아리": "동아리", "홍보": "동아리", "모집": "동아리", "개인": "개인", "lesson": "수업", "training": "연수",
                  "parents": "학부모 설명회", "talk": "발표", "club": "동아리", "personal": "개인"}


def purpose_of(text: str) -> str:
    """Normalise a purpose word ('학부모 설명회', 'training' ...) to one of PURPOSES."""
    t = (text or "").lower()
    for k, v in PURPOSE_ALIAS.items():
        if k in t:
            return v
    return "개인" if not t else "발표"


# ---- colour helpers --------------------------------------------------------------------------------------------------
def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(c) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in c)


def mix(a: str, b: str, t: float) -> str:
    """Blend colour a toward b by t (0..1)."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def is_dark(h: str) -> bool:
    return design_core._lum(h) < 0.25


def legible(fg: str, bg: str, need: float = 4.5) -> str:
    """Move fg toward white/black (whichever the bg needs) until it reaches the contrast; returns a hex."""
    if design_core.contrast(fg, bg) >= need:
        return fg
    target = "#ffffff" if design_core._lum(bg) < 0.4 else "#000000"
    for i in range(1, 21):
        c = mix(fg, target, i / 20)
        if design_core.contrast(c, bg) >= need:
            return c
    return target


def worst_bg(colors: list[str]) -> list[str]:
    return colors


def _h(key: str) -> int:
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:10], 16)


def weighted(opts: dict, key: str) -> str:
    """Seeded weighted pick (deterministic)."""
    items = sorted((k, w) for k, w in opts.items() if w > 0)
    total = sum(w for _, w in items)
    r = _h(key) % total
    for k, w in items:
        if r < w:
            return k
        r -= w
    return items[0][0]


def pick_style(purpose: str, mood: str, subject: str, seed: int, forced: str = "", avoid: list | None = None, context: str = "") -> tuple[str, str]:
    """(style id, why): an explicit design.style wins; else mood words + purpose (or the context recipe) + subject weights with a seeded pick."""
    if forced in STYLES:
        return forced, "style"
    rc = dctx.recipe(context)
    if rc.get("style"):
        return rc["style"], "context"
    w = {k: float(v) for k, v in (rc.get("styles") or PURPOSE_STYLE.get(purpose, PURPOSE_STYLE["발표"])).items()}
    why = "context" if rc else "purpose"
    words = f"{mood} {subject}"
    for key, add in MOOD_STYLE.items():
        if key in words:
            for s, v in add.items():
                w[s] = w.get(s, 0) + v * 3
            why = "mood"
    for key, add in SUBJECT_STYLE.items():
        if key in words or key in subject:
            for s, v in add.items():
                w[s] = w.get(s, 0) + v
    for sid, v in STYLES.items():  # a style's own keywords in the words ("미니멀", "네온") count strongly
        if any(k in words for k in v["keys"]):
            w[sid] = w.get(sid, 0) + 8
            why = "words"
    if rc:  # a context keeps to its own style family: mood/subject words only re-weight inside it
        w = {k: v for k, v in w.items() if k in rc["styles"]}
    for a in (avoid or []):  # styles used in the last builds are much less likely (same request -> visibly different looks)
        if a in w:
            w[a] *= 0.02
    return weighted({k: max(1, int(v * 10)) for k, v in w.items()}, f"style|{seed}|{purpose}"), why


def palette_for(style: str, mood: str, seed: int) -> tuple[dict, str]:
    """The style's own palette, or a validated shared palette of the same tone that matches the mood (seeded)."""
    own = dict(STYLES[style]["pal"])
    if style in SLIDE_PAL:  # slides want a calmer base than the game version of this style
        return dict(SLIDE_PAL[style]), style
    if style in ("minimal-premium", "chalk-paper", "retro-pixel", "tv-gameshow", "anime-cartoon", "neon-cyber"):
        return own, style  # these need their signature colours
    data = design_core.load()
    mood_n = design_core.normalize_mood(mood or "", data)
    dark = bool(STYLES[style]["dark"])
    cands = []
    for name, p in data["palettes"].items():
        if "present" not in p.get("uses", []) or bool(p["dark"]) != dark or design_core.palette_issues(name, p):
            continue
        score = 3 if mood_n and mood_n in p["mood"] else 0
        cands.append((score, name, p))
    opts = {"@own": 3}
    for score, name, p in cands:
        opts[name] = 2 + score
    pick = weighted({k: v for k, v in opts.items()}, f"pal|{style}|{seed}")
    if pick == "@own":
        return own, style
    p = data["palettes"][pick]
    keys = ("bg1", "bg2", "text", "card", "cardText", "cardBorder", "primary", "btnText", "accent", "good", "bad")
    return {k: p[k] for k in keys}, pick


def resolve(spec: dict, seed: int, avoid: list | None = None) -> dict:
    """Design object used by every layout: style, language, colours (+ guarded derived colours), floors, fonts."""
    d = spec.get("design") or {}
    purpose = purpose_of(spec.get("purpose", ""))
    context = dctx.context_of(spec)
    rc = dctx.recipe(context)
    mood = " ".join(spec.get("mood") if isinstance(spec.get("mood"), list) else [str(spec.get("mood", ""))])
    if rc and not mood.strip():
        mood = rc["mood"]
    words = " ".join([mood, str(spec.get("title", ""))])
    style, why = pick_style(purpose, words, str(spec.get("subject", "")), seed, str(d.get("style", "")), avoid, context)
    lang = dict(LANG[style])
    pal, pal_name = palette_for(style, mood, seed)
    if rc.get("palettes") and not d.get("style"):  # public: restrained navy/slate/teal, seeded
        pal_name = weighted({k: 1 for k in rc["palettes"]}, f"gov|{seed}")
        pal = dict(dctx.PUBLIC_PALETTES[pal_name])
        lang.update(em="color", card="hair", rad=4, bg="minimal", trans="fade", tw=800)
    if rc:
        fam = rc.get("family") or {}
        lang["prefer"] = {k: max(1, round(v * fam.get(k, 1.0))) for k, v in lang["prefer"].items()}
    if d.get("palette_from"):  # the user's own colours (logo / template): they replace the style's palette; the style's composition stays
        pal, pal_name = design_core.load_user_palette(d["palette_from"]), "user"
    bg1, bg2, tx = pal["bg1"], pal["bg2"], pal["text"]
    dark = is_dark(bg1)
    # restraint: bg + text + muted + ONE accent. The card is a quiet tint of the background (never a second colour), text on it is the normal text colour.
    card = mix(bg1, "#ffffff", 0.08) if dark else mix(bg1, "#ffffff", 0.7)
    ct = tx
    pr = legible(pal["primary"], bg1, 3.0) if design_core.contrast(pal["primary"], bg1) < 3 else pal["primary"]
    ac = pal["accent"]
    # text colours that must pass 4.5:1 on BOTH the slide background and the card
    emc = legible(pr, bg1, 5.6)
    emc = emc if design_core.contrast(emc, bg2) >= 5.6 else legible(emc, bg2, 5.6)
    emcc = legible(pr, card, 4.5)
    emc2 = emcc
    mu = mix(tx, bg1, 0.14)
    mu = mu if min(design_core.contrast(mu, bg1), design_core.contrast(mu, bg2)) >= 4.5 else legible(mu, bg2, 4.5)
    cmu = mix(ct, card, 0.25)
    cmu = cmu if design_core.contrast(cmu, card) >= 4.5 else legible(cmu, card, 4.5)
    hl = mix(bg1, pr, 0.30)  # marker tint: tx must stay >= 4.5 on it, else lighten
    if design_core.contrast(tx, hl) < 4.5:
        hl = mix(bg1, pr, 0.16)
    hl_card = mix(card, pr, 0.28)
    if design_core.contrast(ct, hl_card) < 4.5:
        hl_card = mix(card, pr, 0.14)
    # meaning colours: blue vs orange keep apart for colour-blind eyes (checked with shared/design/color_check.py); the layouts also say it in words (정답/오답)
    purpose_floor = 24 if purpose == "개인" else 28
    if rc:
        purpose_floor = rc["floor"]
    return {
        "style": style, "why": why, "purpose": purpose, "palette": pal_name, "seed": seed, "lang": lang, "dark": dark,
        "colors": {"bg1": bg1, "bg2": bg2, "tx": tx, "mu": mu, "card": card, "ct": ct, "cmu": cmu, "cb": mix(tx, bg1, 0.82), "line": mix(tx, bg1, 0.84), "pr": pr, "bt": pal["btnText"],
                   "ac": ac, "good": "#6ea8ff" if dark else "#1d4ed8", "bad": "#ffb454" if dark else "#c2410c", "emc": emc, "emcc": emcc, "emc2": emc2, "hl": hl, "hlc": hl_card,
                   "ink": "#1a1a1a" if not dark else "#f5f5f5"},
        "fonts": {"display": "Noto Serif KR" if lang["font"] == "serif" else "TS Sans", "body": "TS Sans"},
        "floor": purpose_floor, "motion": STYLES[style]["motion"],
        "context": context, "tscale": dict(rc.get("tscale") or {}), "allowed": dict(rc.get("allowed") or {}),
    }


def contrast_report(dz: dict) -> list[str]:
    """Contrast problems of the resolved design (empty = fine); used by the build and by tests."""
    c, out = dz["colors"], []
    for fg, bg, need in (("tx", "bg1", 4.5), ("tx", "bg2", 4.5), ("mu", "bg1", 4.5), ("mu", "bg2", 4.5), ("ct", "card", 4.5), ("cmu", "card", 4.5),
                         ("emc", "bg1", 4.5), ("emcc", "card", 4.5), ("tx", "hl", 4.5), ("ct", "hlc", 4.5), ("bt", "pr", 4.5)):
        r = design_core.contrast(c[fg], c[bg])
        if r < need:
            out.append(f"{fg} on {bg} = {r:.2f} (< {need})")
    return out


if __name__ == "__main__":
    import json
    for purpose, mood in (("학부모 설명회", "따뜻하게"), ("연수", "깔끔하게"), ("수업", "신나게"), ("동아리", "힙하게")):
        for sd in range(4):
            dz = resolve({"purpose": purpose, "mood": mood}, sd)
            print(purpose, mood, sd, dz["style"], dz["palette"], contrast_report(dz))
    bad = []
    for s in STYLES:
        for sd in range(12):
            dz = resolve({"purpose": "개인", "mood": "", "design": {"style": s}}, sd)
            bad += [f"{s}/{sd}/{dz['palette']}: {x}" for x in contrast_report(dz)]
    print(json.dumps(bad[:20], ensure_ascii=False, indent=0))
