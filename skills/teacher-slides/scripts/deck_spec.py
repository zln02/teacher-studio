# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Deck spec: normalise (aliases, legacy lesson-deck content), validate (limits that keep slides uncluttered), resolve local media.

Spec (short JSON the AI writes):
  {"purpose":"학부모 설명회", "audience":"3학년 학부모", "mood":"따뜻하게", "subject":"", "title":"...", "seed": 7 (optional),
   "design": {"style":"pastel-cute" (optional), "builds": true},
   "slides":[{"type":"title","title":"..","subtitle":"..","meta":".."}, {"type":"bullets","title":"..","items":[..]}, ... ]}
Types: panel (one claim + 2-4 blocks of evidence on one slide: deck_panel.py) title section statement bullets compare steps bignumber bignumbers quote illustration quiz timeline chart math timer qr image video closing
       table summary toc hero diagram (drawn figure from lines / arrows / shapes / labels: deck_diagram.py).
Every slide may carry: kicker, note (presenter notes), build (false = all at once), layout ("bullets.cards" = force a variant),
flair {"css": scoped css, "svg": decorative svg} (sandboxed).
"""
from __future__ import annotations

import base64
import mimetypes
import json
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
         "chart", "math", "timer", "qr", "image", "video", "closing", "table", "summary", "toc", "hero", "diagram", "panel")
ALIAS = {"cover": "title", "end": "closing", "thanks": "closing", "cards": "bullets", "list": "bullets", "bigtext": "statement", "question": "statement",
         "big-number": "bignumber", "stat": "bignumber", "stats": "bignumbers", "compare-numbers": "bignumbers", "numbers": "bignumbers",
         "image-free": "illustration", "art": "illustration", "picture": "image", "photo": "image", "countdown": "timer", "quiz-reveal": "quiz",
         "formula": "math", "bignumber2": "bignumbers", "agenda": "bullets", "grid": "table", "datatable": "table", "key-points": "summary",
         "keypoints": "summary", "contents": "toc", "figure": "diagram", "drawing": "diagram", "그림": "diagram", "도식": "diagram", "banner": "hero", "process": "steps", "outro": "closing", "intro": "title", "combo": "panel", "dashboard": "panel", "board": "panel", "mixed": "panel"}
EMOJI = re.compile("[\U0001F000-\U0001FFFF☀-➿⬀-⯿️‍]")  # arrows (← → ↔ ⇒) stay: 「공기 → 물」 loses its meaning without them
URL = re.compile(r"(https?://[^\s·「」)]+|(?:[a-z0-9-]+\.)+(?:com|kr|net|org|io|me|dev|ly)(?:/[^\s·「」)]*)?)", re.I)
MAX_IMG_BYTES = 3 * 1024 * 1024
MAX_VIDEO_EMBED = 8 * 1024 * 1024

LIMITS = {"title": 44, "kicker": 32, "subtitle": 70, "meta": 70, "sub": 80, "text": 110, "caption": 90, "q": 90, "takeaway": 80, "explain": 80, "label": 24}


def clean(s):
    """Strip emoji (they render inconsistently and read as clip-art); keep the words."""
    if not isinstance(s, str):
        return s
    return re.sub(r"\s{2,}", " ", EMOJI.sub("", s)).strip()


# ---- pictures for a young room ------------------------------------------------------------------------------------------------
# One emoji in front of a word (「🐶 멍멍」) is not decoration there: for children who are still learning to read it IS the word's picture.
# It is lifted out of the text into "pics" / "pic" (so headings and sentences stay emoji-free) and drawn large beside the word.
_PB = "(?:[\U0001F1E6-\U0001F1FF]{2}|[\U0001F300-\U0001FAFF☀-⛿⭐⭕✨❄❤✂✈✋✏][️\U0001F3FB-\U0001F3FF]?)"
_PC = "(?:%s(?:‍%s)*)" % (_PB, _PB)
PIC_LEAD = re.compile(r"^\s*(%s)\s*(?=\S)" % _PC)
PIC_TAIL = re.compile(r"(?<=\S)\s*(%s)\s*$" % _PC)
PIC_ONLY = re.compile(r"^\s*%s\s*$" % _PC)


def is_pic(x) -> bool:
    """True for one emoji (a picture), not for a word or an icon name."""
    return isinstance(x, str) and bool(PIC_ONLY.match(x))


def _lift(text):
    """「🐶 멍멍: 강아지 소리」 -> ("🐶", "멍멍: 강아지 소리"); (None, text) when the line carries no picture of its own."""
    if not isinstance(text, str):
        return None, text
    t = re.sub(r"^(\s*\*\*)\s*(%s)\s*" % _PC, r"\2 \1", text)  # a bold word with its picture inside the stars: the picture moves in front
    m = PIC_LEAD.match(t) or PIC_TAIL.search(t)
    if not m:
        return None, text
    return m.group(1), (t[:m.start()] + " " + t[m.end():]).strip()


def lift_pics(spec: dict) -> dict:
    """Pictures the author put in front of words become "pics" (lists) / "pic" (one thing); an emoji given as an icon moves there too."""
    def lst(d, key, out="pics"):
        v = d.get(key)
        if not isinstance(v, list) or not v or not all(isinstance(x, str) for x in v):
            return
        got = [_lift(x) for x in v]
        have = [x if is_pic(x) else None for x in (d.get(out) or [])] if isinstance(d.get(out), list) else []
        ic = d.get("icons") if isinstance(d.get("icons"), list) else []
        pics = [(have[i] if i < len(have) else None) or (ic[i] if i < len(ic) and is_pic(ic[i]) else None) or got[i][0] for i in range(len(v))]
        if any(pics):
            d[key] = [g[1] if g[0] else x for g, x in zip(got, v)]
            d[out] = pics

    def one(d, key="title"):
        if is_pic(d.get("icon")):
            d["pic"] = d.pop("icon")
        if is_pic(d.get("pic")):
            return
        pc, rest = _lift(d.get(key))
        if pc:
            d["pic"], d[key] = pc, rest

    s = dict(spec)
    slides = []
    for it in s.get("slides") or []:
        if not isinstance(it, dict):
            slides.append(it)
            continue
        it = json.loads(json.dumps(it))
        lst(it, "items")
        lst(it, "choices")
        for q in it.get("questions") or []:
            if isinstance(q, dict):
                lst(q, "choices")
        for side in ("a", "b"):
            if isinstance(it.get(side), dict):
                lst(it[side], "items")
        for k in ("steps", "events"):
            for st in it.get(k) or []:
                if isinstance(st, dict):
                    one(st)
        for b in it.get("blocks") or []:
            if isinstance(b, dict):
                for m in b.get("items") or []:
                    if isinstance(m, dict):
                        one(m)
        if str(it.get("type")) in ("title", "cover", "intro", "closing", "end", "illustration"):
            if is_pic(it.get("icon")):
                it["pic"] = it.pop("icon")
        slides.append(it)
    s["slides"] = slides
    return s


def pics_inline(spec: dict) -> dict:
    """The web deck shows a lifted picture in front of its word again (the .pptx draws it as its own large shape)."""
    for it in spec.get("slides") or []:
        for d in (it, it.get("a") or {}, it.get("b") or {}):
            for key in ("items", "choices"):
                pics = d.get("pics") if key == "items" or d is it and not it.get("items") else None
                if isinstance(d.get(key), list) and isinstance(pics, list):
                    d[key] = [(f"{pics[i]} {x}" if i < len(pics) and is_pic(pics[i]) and isinstance(x, str) else x) for i, x in enumerate(d[key])]
        for st in it.get("steps") or []:
            if isinstance(st, dict) and is_pic(st.get("pic")):
                st["title"] = f"{st['pic']} {st.get('title', '')}".strip()
        for q in it.get("questions") or []:
            if isinstance(q, dict) and isinstance(q.get("choices"), list) and isinstance(q.get("pics"), list):
                q["choices"] = [(f"{q['pics'][i]} {x}" if i < len(q["pics"]) and is_pic(q["pics"][i]) and isinstance(x, str) else x) for i, x in enumerate(q["choices"])]
    return spec


def _walk_clean(o, skip=("note", "file", "flair", "pics", "pic")):
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
    s = dict(spec)
    import deck_style
    if deck_style.audience_band(s) == "young":  # only a young room reads pictures as words; elsewhere emoji are stripped as before
        s = lift_pics(s)
    else:  # other rooms: no emoji anywhere, a picture key included
        s["slides"] = [({k: v for k, v in it.items() if not (k in ("pic", "pics") and (is_pic(v) or isinstance(v, list)))} if isinstance(it, dict) else it) for it in s.get("slides") or []]
    s = _walk_clean(s)
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
    elif t == "diagram":
        import deck_diagram
        e += deck_diagram.check(i, it)
    elif t == "title" and it.get("shapes"):  # a small drawing of the topic on the cover (same shapes as a diagram; labels optional)
        import deck_diagram
        e += [m for m in deck_diagram.check(i, {**it, "points": []}) if "add labels" not in m]
    elif t == "hero":
        if len(plain(str(it.get("headline", "")))) > 34:
            e.append(f"slide {i} hero.headline: {len(plain(str(it.get('headline', ''))))} chars > 34 -> short and punchy")
        if len(plain(str(it.get("cta", "")))) > 20:
            e.append(f"slide {i} hero.cta: <= 20 chars")
        facts = it.get("facts") or []
        if not isinstance(facts, list) or len(facts) > 3 or any(len(plain(str(x))) > 22 for x in facts):
            e.append(f"slide {i} hero.facts: up to 3 short facts (<= 22 chars each: 날짜, 장소, 비용)")
    return e


def quiz_set(it: dict) -> list:
    """The questions of a quiz slide: [it] for one question, or its 2-3 `questions` (a short deck checks several on one slide)."""
    qs = it.get("questions")
    if isinstance(qs, list) and qs and all(isinstance(q, dict) for q in qs):
        return qs
    return [it]


def check_slide(i: int, it: dict, warns: list[str], caps: dict | None = None) -> list[str]:
    e: list[str] = []
    t = it["type"]
    caps = caps or {}
    if t == "quiz" and it.get("questions") is not None:  # several check questions on one slide: the first one also fills q / choices / answer
        qs = it["questions"]
        if not isinstance(qs, list) or not 2 <= len(qs) <= 3 or not all(isinstance(q, dict) and q.get("q") and isinstance(q.get("choices"), list) for q in qs):
            return [f"slide {i} quiz.questions: 2-3 questions [{{\"q\":..,\"choices\":[..],\"answer\":0,\"explain\":..}}] (one question -> q / choices / answer)"]
        for n_, q in enumerate(qs, 1):
            if not 2 <= len(q["choices"]) <= 4:
                e.append(f"slide {i} quiz.questions[{n_}]: choices 2-4")
            if not isinstance(q.get("answer", 0), int) or not 0 <= q.get("answer", 0) < len(q["choices"]):
                e.append(f"slide {i} quiz.questions[{n_}].answer must be a 0-based index into its choices")
            if len(plain(str(q["q"]))) > 50:
                e.append(f"slide {i} quiz.questions[{n_}].q: {len(plain(str(q['q'])))} chars > 50 -> shorter (several questions share the slide)")
            for c in q["choices"]:
                if len(plain(str(c))) > 24:
                    e.append(f"slide {i} quiz.questions[{n_}].choices: '{plain(str(c))[:10]}...' > 24 chars")
            if len(plain(str(q.get("explain") or ""))) > 80:
                e.append(f"slide {i} quiz.questions[{n_}].explain: <= 80 chars")
        if e:
            return e
        it.setdefault("title", "확인 문제")
        it["q"], it["choices"], it["answer"] = qs[0]["q"], qs[0]["choices"], qs[0].get("answer", 0)
        if qs[0].get("explain"):
            it["explain"] = qs[0]["explain"]
    need = {"title": ["title"], "section": ["title"], "statement": ["text"], "bullets": ["title", "items"], "compare": ["title", "a", "b"], "steps": ["title", "steps"],
            "bignumber": ["value"], "bignumbers": ["items"], "quote": ["text"], "illustration": ["title"], "quiz": ["q", "choices"], "timeline": ["title", "events"],
            "chart": ["title", "labels", "series"], "math": ["tex"], "timer": [], "qr": ["url"], "image": ["file"], "video": ["file"], "closing": ["title"],
            "table": ["title", "columns", "rows"], "summary": ["points"], "toc": [], "hero": ["headline"], "diagram": ["title", "shapes"], "panel": ["title", "blocks"]}[t]
    for k in need:
        if not it.get(k):
            e.append(f"slide {i} {t}: '{k}' is required")
    if e:
        return e
    e += check_extra(i, it)
    if t == "panel":
        import deck_panel
        e += deck_panel.check(i, it, caps.get("total", 330))
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
