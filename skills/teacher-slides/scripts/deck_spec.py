# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Deck spec: normalise (aliases, legacy lesson-deck content), validate (limits that keep slides uncluttered), resolve local media.

Spec (short JSON the AI writes):
  {"purpose":"학부모 설명회", "audience":"3학년 학부모", "mood":"따뜻하게", "subject":"", "title":"...", "seed": 7 (optional),
   "design": {"style":"pastel-cute" (optional), "builds": true},
   "slides":[{"type":"title","title":"..","subtitle":"..","meta":".."}, {"type":"bullets","title":"..","items":[..]}, ... ]}
Types: title section statement bullets compare steps bignumber bignumbers quote illustration quiz timeline chart math timer qr image video closing.
Every slide may carry: kicker, note (presenter notes), build (false = all at once), layout ("bullets.cards" = force a variant),
flair {"css": scoped css, "svg": decorative svg} (sandboxed).
"""
from __future__ import annotations

import base64
import mimetypes
import re
import sys
from pathlib import Path

from deck_kit import plain

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
_V = SKILL / "shared" / "vendor" / "qrcodegen"
if not _V.exists():
    _V = SKILL.parent.parent / "shared" / "vendor" / "qrcodegen"
sys.path.insert(0, str(_V))

TYPES = ("title", "section", "statement", "bullets", "compare", "steps", "bignumber", "bignumbers", "quote", "illustration", "quiz", "timeline",
         "chart", "math", "timer", "qr", "image", "video", "closing", "table", "summary", "toc", "hero")
ALIAS = {"cover": "title", "end": "closing", "thanks": "closing", "cards": "bullets", "list": "bullets", "bigtext": "statement", "question": "statement",
         "big-number": "bignumber", "stat": "bignumber", "stats": "bignumbers", "compare-numbers": "bignumbers", "numbers": "bignumbers",
         "image-free": "illustration", "art": "illustration", "picture": "image", "photo": "image", "countdown": "timer", "quiz-reveal": "quiz",
         "formula": "math", "bignumber2": "bignumbers", "agenda": "bullets", "grid": "table", "datatable": "table", "key-points": "summary",
         "keypoints": "summary", "contents": "toc", "banner": "hero", "process": "steps", "outro": "closing", "intro": "title"}
EMOJI = re.compile("[\U0001F000-\U0001FFFF☀-➿⬀-⯿️‍←-⇿]")
URL = re.compile(r"(https?://[^\s·「」)]+|(?:[a-z0-9-]+\.)+(?:com|kr|net|org|io|me|dev|ly)(?:/[^\s·「」)]*)?)", re.I)
MAX_IMG_BYTES = 3 * 1024 * 1024
MAX_VIDEO_EMBED = 8 * 1024 * 1024

LIMITS = {"title": 44, "kicker": 32, "subtitle": 70, "meta": 70, "sub": 80, "text": 110, "caption": 90, "q": 90, "takeaway": 70, "explain": 80, "label": 24}


def clean(s):
    """Strip emoji (they render inconsistently and read as clip-art); keep the words."""
    if not isinstance(s, str):
        return s
    return re.sub(r"\s{2,}", " ", EMOJI.sub("", s)).strip()


def _walk_clean(o, skip=("note", "file", "flair")):
    if isinstance(o, dict):
        return {k: (v if k in skip else _walk_clean(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [_walk_clean(v) for v in o]
    return clean(o)


def _legacy(it: dict) -> dict:
    """Map a legacy lesson-deck item (layout/cards/...) to the new typed form."""
    lay = it.get("layout")
    if not lay or it.get("type"):
        return it
    d = {k: v for k, v in it.items() if k != "layout"}
    t = ALIAS.get(lay, lay)
    d["type"] = t
    if lay == "cards":
        d["items"] = [(c.get("title", "") + ("\\n" + c["text"] if c.get("text") else "")) if isinstance(c, dict) else c for c in it.get("cards", [])]
        d["items"] = [("**" + c.split("\\n")[0] + "**" + ("\\n" + "\\n".join(c.split("\\n")[1:]) if "\\n" in c else "")) for c in d["items"]]
    if lay == "image":
        d["type"] = "illustration"
        d["_icon_word"] = it.get("icon", "")
    if lay == "end":
        qr = it.get("qr", "")
        m = URL.search(qr or "")
        if m:
            d["url"] = m.group(1)
            d["caption"] = re.sub(r"\s*·?\s*" + re.escape(m.group(1)), "", qr).strip(" ·")
    if lay == "question":
        d["text"] = it.get("q", "")
        d["sub"] = it.get("hint", "")
    return d


def normalize(spec: dict, base: Path | None = None) -> tuple[dict, list[str], list[str]]:
    """Return (spec, warnings, errors). errors = fix hints (the build stops); warnings = advisory."""
    warns: list[str] = []
    errs: list[str] = []
    s = _walk_clean(dict(spec))
    raw = s.get("slides") or s.get("items") or []
    if not raw:
        return s, warns, ["spec.slides is empty: write 8-15 slides, e.g. {\"type\":\"title\",...} ... {\"type\":\"closing\",...}"]
    import deck_context as dctx
    caps = dctx.recipe(dctx.context_of(s)).get("caps") or {}
    out = []
    for i, it in enumerate(raw, 1):
        it = _legacy(dict(it))
        t = ALIAS.get(it.get("type", ""), it.get("type", ""))
        if t not in TYPES:
            errs.append(f"slide {i}: unknown type '{it.get('type')}' -> one of {', '.join(TYPES)}")
            continue
        it["type"] = t
        out.append(it)
        errs += check_slide(i, it, warns, caps)
    s["slides"] = out
    if len(out) > 40:
        warns.append(f"{len(out)} slides: long decks lose the audience; consider splitting")
    return s, warns, errs


def _len(it, key, errs, i, limit=None, soft=False):
    v = it.get(key)
    if isinstance(v, str) and len(plain(v)) > (limit or LIMITS.get(key, 90)):
        errs.append(f"slide {i} {it['type']}.{key}: {len(plain(v))} chars > {limit or LIMITS.get(key, 90)} -> shorten (one message per slide)")


def check_extra(i: int, it: dict) -> list[str]:
    """Limits of the context slide types (table / summary / toc / hero)."""
    e: list[str] = []
    t = it["type"]
    if t == "table":
        cols, rows = it.get("columns") or [], it.get("rows") or []
        if not 2 <= len(cols) <= 6:
            e.append(f"slide {i} table.columns: {len(cols)} columns -> use 2-6")
        if not 1 <= len(rows) <= 8:
            e.append(f"slide {i} table.rows: {len(rows)} rows -> use 1-8 (split the table)")
        for r in rows:
            if not isinstance(r, list) or len(r) != len(cols):
                e.append(f"slide {i} table: every row needs {len(cols)} cells")
                break
            if any(len(plain(str(c))) > 40 for c in r):
                e.append(f"slide {i} table: a cell is > 40 chars -> shorten (put detail in the note)")
                break
        if any(len(plain(str(c))) > 16 for c in cols):
            e.append(f"slide {i} table.columns: header <= 16 chars")
    elif t == "summary":
        pts = it.get("points") or []
        if not 2 <= len(pts) <= 5:
            e.append(f"slide {i} summary.points: {len(pts)} -> use 2-5")
        for x in pts:
            if len(plain(str(x))) > 80:
                e.append(f"slide {i} summary.points: '{plain(str(x))[:12]}...' > 80 chars")
    elif t == "toc":
        its = it.get("items") or []
        if its and not 2 <= len(its) <= 8:
            e.append(f"slide {i} toc.items: use 2-8")
        if any(len(plain(str(x))) > 30 for x in its):
            e.append(f"slide {i} toc.items: <= 30 chars each")
    elif t == "hero":
        if len(plain(str(it.get("headline", "")))) > 34:
            e.append(f"slide {i} hero.headline: {len(plain(str(it.get('headline', ''))))} chars > 34 -> short and punchy")
        if len(plain(str(it.get("cta", "")))) > 20:
            e.append(f"slide {i} hero.cta: <= 20 chars")
    return e


def check_slide(i: int, it: dict, warns: list[str], caps: dict | None = None) -> list[str]:
    e: list[str] = []
    t = it["type"]
    caps = caps or {}
    need = {"title": ["title"], "section": ["title"], "statement": ["text"], "bullets": ["title", "items"], "compare": ["title", "a", "b"], "steps": ["title", "steps"],
            "bignumber": ["value"], "bignumbers": ["items"], "quote": ["text"], "illustration": ["title"], "quiz": ["q", "choices"], "timeline": ["title", "events"],
            "chart": ["title", "labels", "series"], "math": ["tex"], "timer": [], "qr": ["url"], "image": ["file"], "video": ["file"], "closing": ["title"],
            "table": ["title", "columns", "rows"], "summary": ["points"], "toc": [], "hero": ["headline"]}[t]
    for k in need:
        if not it.get(k):
            e.append(f"slide {i} {t}: '{k}' is required")
    if e:
        return e
    e += check_extra(i, it)
    for k in ("title", "kicker", "subtitle", "meta", "sub", "caption", "q", "takeaway", "explain"):
        _len(it, k, e, i)
    for k in ("text",):
        _len(it, k, e, i, 110 if t != "statement" else 70)
    if t == "bullets":
        items = it["items"]
        lo, hi = caps.get("bullet_items", (2, 6))
        mc = caps.get("bullet_chars", 60)
        if not lo <= len(items) <= hi:
            e.append(f"slide {i} bullets.items: {len(items)} items -> use {lo}-{hi} (split into two slides)")
        for j, x in enumerate(items):
            if len(plain(x)) > mc:
                e.append(f"slide {i} bullets.items[{j}]: {len(plain(x))} chars > {mc} -> shorten")
    if t == "compare":
        for side in ("a", "b"):
            if not isinstance(it[side], dict):
                it[side] = {"label": str(it[side])}
        if not (it.get("rows") or (it["a"].get("items") and it["b"].get("items"))):
            e.append(f"slide {i} compare: give rows:[{{k,a,b}}] or a.items + b.items")
        for r in (it.get("rows") or []):
            for k in ("a", "b"):
                if len(plain(r.get(k, ""))) > 44:
                    e.append(f"slide {i} compare.rows: '{plain(r.get(k))[:12]}...' > 44 chars -> shorten")
        for side in ("a", "b"):
            for x in it[side].get("items", []):
                if len(plain(x)) > 44:
                    e.append(f"slide {i} compare.{side}.items: '{plain(x)[:12]}...' > 44 chars -> shorten")
    if t == "steps":
        n = len(it["steps"])
        if not 3 <= n <= 6:
            e.append(f"slide {i} steps: {n} steps -> use 3-6")
        for st in it["steps"]:
            if len(plain(st.get("title", ""))) > 18 or len(plain(st.get("text", ""))) > 44:
                e.append(f"slide {i} steps: title <= 18 and text <= 44 chars ('{plain(st.get('title'))[:10]}')")
    if t == "bignumbers" and not 2 <= len(it["items"]) <= 3:
        e.append(f"slide {i} bignumbers: use 2-3 numbers")
    if t == "quiz":
        if not 2 <= len(it["choices"]) <= 5:
            e.append(f"slide {i} quiz.choices: use 2-5")
        if not isinstance(it.get("answer", 0), int) or not 0 <= it.get("answer", 0) < len(it["choices"]):
            e.append(f"slide {i} quiz.answer must be a 0-based index into choices")
        for c in it["choices"]:
            if len(plain(c)) > 36:
                e.append(f"slide {i} quiz.choices: '{plain(c)[:10]}...' > 36 chars")
    if t == "timeline":
        n = len(it["events"])
        if not 3 <= n <= 6:
            e.append(f"slide {i} timeline.events: use 3-6")
        for ev in it["events"]:
            if len(plain(ev.get("when", ""))) > 12 or len(plain(ev.get("title", ""))) > 20 or len(plain(ev.get("text", ""))) > 50:
                e.append(f"slide {i} timeline: when<=12, title<=20, text<=50 chars")
    if t == "chart":
        if it.get("kind", "bar") not in ("bar", "line", "pie", "doughnut"):
            e.append(f"slide {i} chart.kind: bar | line | pie | doughnut")
        if not isinstance(it["series"], list) or any(len(s_.get("data", [])) != len(it["labels"]) for s_ in it["series"]):
            e.append(f"slide {i} chart: every series.data needs one number per label")
        if len(it["labels"]) > 8:
            e.append(f"slide {i} chart: {len(it['labels'])} labels -> use up to 8")
    if t == "timer" and not (1 <= int(it.get("minutes", 5)) <= 90):
        e.append(f"slide {i} timer.minutes: 1-90")
    if t == "closing" and len(it.get("next", [])) > 4:
        e.append(f"slide {i} closing.next: at most 4")
    total = sum(len(plain(v)) for k, v in it.items() if isinstance(v, str) and k not in ("note", "type", "file", "url", "tex", "layout", "source", "footnote", "context"))
    total += sum(len(plain(x)) for k in ("items", "next", "choices", "points") for x in it.get(k, []) if isinstance(x, str))
    cap = caps.get("total", 330)
    if total > cap:
        e.append(f"slide {i} {t}: {total} chars of text > {cap} -> split it (projection needs big, short text)")
    return e


# ---- media ---------------------------------------------------------------------------------------------------------------
def data_uri(path: Path, mime: str, data: bytes) -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def inline_image(path: Path) -> tuple[str, list[str]]:
    """Local image -> data URI, size-capped (long side <= 1920, <= 3MB; re-encoded with Pillow when available)."""
    notes: list[str] = []
    data = path.read_bytes()
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    if mime == "image/svg+xml":
        txt = data.decode("utf-8", "ignore")
        if re.search(r"<script|on\w+\s*=|https?://", txt, re.I):
            raise ValueError(f"{path.name}: SVG with scripts or external links is not allowed")
        return data_uri(path, mime, data), notes
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data))
        big = max(im.size) > 1920 or len(data) > 1_200_000
        if big:
            im.thumbnail((1920, 1920))
            buf = io.BytesIO()
            if im.mode in ("RGBA", "LA", "P") and mime == "image/png" and (im.mode != "P" or "transparency" in im.info):
                im.convert("RGBA").save(buf, "PNG", optimize=True)
                mime = "image/png"
            else:
                im.convert("RGB").save(buf, "JPEG", quality=82, optimize=True)
                mime = "image/jpeg"
            notes.append(f"{path.name}: resized {len(data) // 1024}KB -> {len(buf.getvalue()) // 1024}KB")
            data = buf.getvalue()
    except ImportError:
        notes.append(f"{path.name}: Pillow not installed, image embedded as is")
    if len(data) > MAX_IMG_BYTES:
        raise ValueError(f"{path.name}: {len(data) // 1024}KB > 3MB cap -> use a smaller image")
    return data_uri(path, mime, data), notes


def resolve_media(spec: dict, base: Path) -> tuple[list[str], list[str]]:
    """Fill _src/_href on image/video slides, _qr on qr/closing slides. Returns (notes, errors)."""
    notes, errs = [], []
    import deck_qr
    for i, it in enumerate(spec["slides"], 1):
        t = it["type"]
        if t in ("image", "video") or (t == "hero" and it.get("file")):
            p = Path(it["file"])
            p = p if p.is_absolute() else (base / p)
            if not p.exists():
                errs.append(f"slide {i} {t}.file not found: {it['file']}")
                continue
            if t in ("image", "hero"):
                try:
                    it["_src"], n = inline_image(p)
                    notes += n
                except ValueError as exc:
                    errs.append(f"slide {i}: {exc}")
            else:
                size = p.stat().st_size
                mime = mimetypes.guess_type(str(p))[0] or "video/mp4"
                if size <= MAX_VIDEO_EMBED:
                    it["_src"] = data_uri(p, mime, p.read_bytes())
                    notes.append(f"{p.name}: embedded ({size // 1024}KB)")
                else:
                    it["_href"] = p.resolve().as_uri()
                    it["_name"] = p.name
                    notes.append(f"{p.name}: {size // 1048576}MB > 8MB -> 'open video' button (file stays next to the deck)")
        if t in ("qr", "closing", "hero") and it.get("url"):
            it["_qr"] = deck_qr.svg(it["url"])
        if t == "closing" and not it.get("url") and any(URL.search(str(x)) for x in it.get("next", [])):
            pass
    return notes, errs


FLAIR_BAD = re.compile(r"@import|expression\s*\(|javascript:|url\(\s*['\"]?\s*(?:https?:|//)|behavior\s*:|position\s*:\s*fixed", re.I)


def scope_css(css: str, sid: str) -> str:
    """Prefix every selector with the slide id so flair css cannot leak to other slides."""
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        sel = ",".join(f"{sid} {x.strip()}" for x in m.group(1).split(",") if x.strip())
        out.append(f"{sel}{{{m.group(2)}}}")
    return "".join(out)


def flair(it: dict, sid: str) -> tuple[str, str, list[str]]:
    """Sandboxed custom flair: (scoped css, sanitised svg html, problems)."""
    f = it.get("flair") or {}
    probs: list[str] = []
    css, svg = f.get("css", ""), f.get("svg", "")
    if css and FLAIR_BAD.search(css):
        probs.append(f"{sid}: flair.css uses a forbidden construct (@import / external url / position:fixed ...)")
        css = ""
    if svg:
        if re.search(r"<script|<foreignObject|\son\w+\s*=|javascript:|https?://|<image|<a\s", svg, re.I):
            probs.append(f"{sid}: flair.svg must be plain shapes (no script, links, images)")
            svg = ""
        elif not svg.lstrip().startswith("<svg"):
            probs.append(f"{sid}: flair.svg must be one <svg>...</svg>")
            svg = ""
    return scope_css(css, "#" + sid) if css else "", f'<div class="bx flair" aria-hidden="true">{svg}</div>' if svg else "", probs
