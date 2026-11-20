#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Build an interactive web app / program (helper, tutor, calculator, simulation, practice pad, dashboard) as ONE offline HTML file.

Usage:
    python3 build_webapp.py --spec app.json --out app.html [--shot shot.png] [--no-check] [--no-browser] [--no-fonts]

spec (references/webapp.md):
    {"title": "...", "subtitle": "...", "words": "코딩 중학생", "style": "<optional style id>", "palette": {"primary": "#..."},
     "ai": "rules" | "none", "about": "what it does", "can": [...], "cannot": [...],
     "parts": [ {"type": "helper", "name", "greeting", "fallback", "placeholder", "chips": [...], "intents": [{"keys": [...], "answer": "...", "code": "..."}]},
                {"type": "runner", "name", "starter", "examples": [{"name", "code"}], "timeout_ms": 3000},
                {"type": "custom", "name", "icon", "html": "...", "css": "...", "js": "..."} ]}
Design = shared design system (styles.py style + system.py type/spacing + shell kit tokens, icons, TS Sans embedded).
Layout = picked from the content and a seed (pick_layout): focus | aside | wide, cols2 | lead2 | stack, cols3 | lead3 | stack; header bar | hero | rail.
The page has: 가-/가+, projector mode (P), reset (처음으로), an honest 「이 프로그램은?」 panel, keyboard support, no storage, no network.
Then check_webapp.py runs (static + one headless browser, fast settings).
"""
from __future__ import annotations

import argparse
import html as _html
import json
import re
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SHARED = SKILL / "shared" if (SKILL / "shared" / "shell" / "shell.py").exists() else SKILL.parent.parent / "shared"
for _sub in ("design", "shell", "fonts", "tools"):
    sys.path.insert(0, str(SHARED / _sub))
sys.path.insert(0, str(HERE))
import shell  # noqa: E402
import styles  # noqa: E402

ASSETS = SKILL / "assets" / "webapp"
PART_TYPES = ("helper", "runner", "custom")
AI_MODES = ("rules", "none")
ES_BAD = re.compile(r"\?\.(?![0-9])|\?\?")
DEFAULT_ICON = {"helper": "robot", "runner": "pencil", "custom": "sparkles"}


def esc(s) -> str:
    return _html.escape(str(s if s is not None else ""), quote=True)


def js_json(obj) -> str:
    """JSON safe inside <script>: < > & and U+2028/2029 escaped."""
    s = json.dumps(obj, ensure_ascii=False)
    for ch, e in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), (chr(0x2028), "\\u2028"), (chr(0x2029), "\\u2029")):
        s = s.replace(ch, e)
    return s


def validate(spec: dict) -> list[str]:
    errs: list[str] = []
    title = str(spec.get("title") or "").strip()
    if not title:
        errs.append("title is required")
    elif len(title) > 40:
        errs.append("title must be 40 characters or fewer")
    if spec.get("ai", "none") not in AI_MODES:
        errs.append("ai must be 'rules' (prepared answers) or 'none' (plain program). A live AI needs an API key in the file, which we never do")
    parts = spec.get("parts")
    if not isinstance(parts, list) or not 1 <= len(parts) <= 3:
        return errs + ["parts: 1-3 parts (helper / runner / custom)"]
    for i, p in enumerate(parts):
        t = (p or {}).get("type")
        if t not in PART_TYPES:
            errs.append(f"parts[{i}].type must be one of {', '.join(PART_TYPES)}")
            continue
        if t == "helper":
            ints = p.get("intents") or []
            if not ints:
                errs.append(f"parts[{i}] helper needs intents [{{keys, answer}}]")
            for j, it in enumerate(ints):
                if not it.get("keys") or not str(it.get("answer") or "").strip():
                    errs.append(f"parts[{i}].intents[{j}] needs keys and answer")
        elif t == "runner":
            if str(p.get("lang", "js")).lower() not in ("js", "javascript"):
                errs.append(f"parts[{i}] runner: only JavaScript runs offline. Python in the browser needs a big download from the internet (CDN); "
                            "use JavaScript, or show Python code as read-only examples in a helper")
            for j, ex in enumerate(p.get("examples") or []):
                if not str(ex.get("code") or "").strip():
                    errs.append(f"parts[{i}].examples[{j}] needs code")
        else:
            if not str(p.get("html") or "").strip():
                errs.append(f"parts[{i}] custom needs html")
            if re.search(r"<script\b", str(p.get("html") or ""), re.I):
                errs.append(f"parts[{i}] custom: put scripts in js, not inside html")
            if ES_BAD.search(str(p.get("js") or "")):
                errs.append(f"parts[{i}] custom js uses ?. or ?? (not allowed: old school Chrome). Use a && a.b and (x != null ? x : y)")
            cases = p.get("cases", [])
            valid_id = lambda key: isinstance(key, str) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key))
            if not isinstance(cases, list) or len(cases) > 5:
                errs.append(f"parts[{i}].cases: up to five test cases")
            else:
                for j, case in enumerate(cases):
                    if (not isinstance(case, dict) or not isinstance(case.get("inputs"), dict)
                        or not all(valid_id(k) and isinstance(v, (str, int, float)) for k, v in case["inputs"].items())
                        or not isinstance(case.get("output"), str) or not valid_id(case["output"])
                        or not isinstance(case.get("expected"), (str, int, float))):
                        errs.append(f"parts[{i}].cases[{j}]: expected inputs, output id and expected text")
    return errs


def make_tokens(spec: dict) -> dict:
    forced = spec.get("style") if spec.get("style") in styles.STYLES else ""
    words = " ".join(str(spec.get(k) or "") for k in ("words", "mood"))
    text = " ".join(str(spec.get(k) or "") for k in ("title", "subtitle"))
    sid, _why = styles.pick_style(text, "generic", int(spec.get("seed", 0) or 0), forced, words)
    pal = spec.get("palette") if isinstance(spec.get("palette"), dict) else None
    t = shell.tokens(sid, user=pal)
    t["picked"] = sid
    return t


LAYOUTS = {1: ("focus", "aside", "wide"), 2: ("cols2", "lead2", "stack"), 3: ("cols3", "lead3", "stack")}
HEADS = ("bar", "hero", "rail")


def _pick(opts: dict, key: str) -> str:
    import hashlib
    items = sorted((k, w) for k, w in opts.items() if w > 0)
    r = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:10], 16) % sum(w for _, w in items)
    for k, w in items:
        if r < w:
            return k
        r -= w
    return items[0][0]


def pick_layout(spec: dict) -> tuple[str, str]:
    """(body layout, header treatment) chosen from the CONTENT and a seed, so two programs do not share one skeleton.

    Content: how many parts, what they are (a helper wants a tall column; one custom tool wants the stage to itself), whether the spec explains
    what the program can / cannot do (then that gets its own side panel). Seed: spec.seed walks the options best-fit first (seed 1, 2, 3 = three
    different skeletons); without a seed the title decides (same request -> same page).
    spec.layout / spec.head name a choice directly."""
    parts = spec["parts"]
    n = len(parts)
    types = [p["type"] for p in parts]
    seed = spec.get("seed")
    key = ("s%s" % seed) if seed not in (None, "", 0) else ("t" + str(spec.get("title", "")))
    explained = bool(spec.get("can") or spec.get("cannot") or spec.get("about"))
    if n == 1:
        w = {"focus": 3, "aside": 4 if explained else 2, "wide": 3 if types[0] == "runner" else 1}
    elif n == 2:
        w = {"cols2": 3, "lead2": 4 if types[0] != types[1] else 2, "stack": 2 if "runner" in types else 1}
    else:
        w = {"cols3": 3 if len(set(types)) == 1 else 2, "lead3": 4, "stack": 1}
    hw = {"bar": 3, "hero": 3 if n <= 2 else 2, "rail": 3 if "helper" in types else 1}
    if isinstance(seed, int) and seed > 0:
        # an explicit seed walks the options in order of fit (best first): seeds 1, 2, 3 are three different skeletons, 1..9 all nine pairs
        lo = sorted(w, key=lambda k: (-w[k], k))
        ho = sorted(hw, key=lambda k: (-hw[k], k))
        lay_pick, head_pick = lo[(seed - 1) % len(lo)], ho[((seed - 1) + (seed - 1) // len(lo)) % len(ho)]
    else:
        lay_pick, head_pick = _pick(w, key + "|L"), _pick(hw, key + "|H")
    lay = spec.get("layout") if spec.get("layout") in LAYOUTS[n] else lay_pick
    head = spec.get("head") if spec.get("head") in HEADS else head_pick
    return lay, head


def note_html(spec: dict) -> str:
    """The side panel of the "aside" layout: what the program does and does not do, in the spec's own words (never invented)."""
    li = lambda xs: "".join(f"<li>{esc(x)}</li>" for x in xs)  # noqa: E731
    out = '<aside class="wa-card wa-note" aria-label="이 프로그램 안내">'
    if spec.get("about"):
        out += f'<p class="wa-lede">{esc(spec["about"])}</p>'
    if spec.get("can"):
        out += f'<h3>할 수 있는 것</h3><ul>{li(spec["can"][:4])}</ul>'
    if spec.get("cannot"):
        out += f'<h3>못 하는 것</h3><ul>{li(spec["cannot"][:4])}</ul>'
    if not (spec.get("about") or spec.get("can") or spec.get("cannot")):
        out += "<h3>쓰는 법</h3><ul><li>P = 프로젝터 모드</li><li>+ / − = 글자 크게 / 작게</li><li>? = 안내</li></ul>"
    return out + "</aside>"


def _icon(name: str, size: int = 22) -> str:
    return shell.icon(name if name in shell.icon_names() else "sparkles", size)


def part_html(i: int, p: dict) -> str:
    t = p["type"]
    name = esc(p.get("name") or {"helper": "도우미", "runner": "연습장", "custom": "활동"}[t])
    icon = _icon(str(p.get("icon") or DEFAULT_ICON[t]))
    head = f'<h2 id="wa-h-{i}">{icon}<span>{name}</span></h2>'
    if t == "helper":
        chips = "".join(f'<button type="button" class="wa-chip">{esc(c)}</button>' for c in (p.get("chips") or [])[:6])
        n = len(p.get("intents") or [])
        return (f'<section class="wa-card" id="wa-part-{i}" aria-labelledby="wa-h-{i}">{head}'
                f'<div class="wa-log" role="log" aria-live="polite" aria-label="대화"></div>'
                + (f'<div class="wa-chips wa-row">{chips}</div>' if chips else "") +
                f'<div class="wa-row"><label class="wa-sr" for="wa-q-{i}">질문</label>'
                f'<input id="wa-q-{i}" class="wa-in" type="text" autocomplete="off" placeholder="{esc(p.get("placeholder") or "궁금한 것을 적어 보세요")}">'
                f'<button type="button" class="wa-btn wa-send">{_icon("arrow-right", 20)}<span>묻기</span></button></div>'
                f'<p class="wa-hint">미리 준비한 설명 {n}개 중에서 골라 답해요 (인터넷 AI가 아니에요).</p></section>')
    if t == "runner":
        ex = p.get("examples") or []
        starter = p.get("starter") or (ex[0]["code"] if ex else 'console.log("안녕하세요!");')
        sel = ""
        if ex:
            opts = "".join(f"<option>{esc(e.get('name') or f'예제 {k + 1}')}</option>" for k, e in enumerate(ex))
            sel = f'<div class="wa-row"><label for="wa-ex-{i}">예제</label><select id="wa-ex-{i}" class="wa-sel">{opts}</select></div>'
        secs = max(1, round(int(p.get("timeout_ms", 3000)) / 1000))
        return (f'<section class="wa-card" id="wa-part-{i}" aria-labelledby="wa-h-{i}">{head}{sel}'
                f'<label class="wa-sr" for="wa-code-{i}">코드</label>'
                f'<textarea id="wa-code-{i}" class="wa-code" spellcheck="false" autocomplete="off" autocapitalize="off">{esc(starter)}</textarea>'
                f'<div class="wa-row"><button type="button" class="wa-btn wa-run">{_icon("player-play", 20)}<span>실행</span></button>'
                f'<button type="button" class="wa-btn ghost wa-clear">{_icon("eraser", 20)}<span>결과 지우기</span></button></div>'
                f'<pre class="wa-out" aria-live="polite" aria-label="실행 결과"></pre>'
                f'<p class="wa-hint">Ctrl+Enter = 실행 · Tab = 들여쓰기 · Esc = 편집기에서 나가기 · 끝나지 않는 반복은 {secs}초 뒤 자동으로 멈춰요.</p></section>')
    return f'<section class="wa-card wa-custom" id="wa-part-{i}" aria-labelledby="wa-h-{i}">{head}{p.get("html", "")}</section>'


def about_html(spec: dict) -> str:
    ai = spec.get("ai", "none")
    n = sum(len(p.get("intents") or []) for p in spec["parts"] if p.get("type") == "helper")
    if ai == "rules":
        what_ai = (f"인터넷에 연결된 AI(챗GPT 같은 것)가 아니에요. 미리 준비한 설명 {n}개 중에서 질문 낱말과 가장 잘 맞는 것을 골라 보여 줘요. "
                   "그래서 준비하지 않은 질문에는 답하지 못해요. 대신 인터넷·계정·API 키·비용이 필요 없고, 학생이 AI 서비스를 직접 쓰지 않아요.")
        can = spec.get("can") or ["준비한 질문에 늘 같은 답을 바로 보여 줘요", "인터넷이 끊겨도 동작해요"]
        cannot = spec.get("cannot") or ["자유로운 질문에 새 답을 지어내지 못해요", "학생 코드를 이해해서 고쳐 주지는 못해요"]
    else:
        what_ai = "AI를 쓰지 않는 프로그램이에요. 정해진 계산과 규칙대로만 움직여요. 인터넷·계정·API 키가 필요 없어요."
        can = spec.get("can") or ["정해진 규칙대로 바로 계산하고 보여 줘요", "인터넷이 끊겨도 동작해요"]
        cannot = spec.get("cannot") or ["질문을 이해해서 대화하지는 못해요"]
    li = lambda xs: "".join(f"<li>{esc(x)}</li>" for x in xs)  # noqa: E731
    return ('<dialog id="wa-about" class="wa-about" aria-labelledby="wa-about-h"><h2 id="wa-about-h">이 프로그램은?</h2>'
            + (f"<p>{esc(spec['about'])}</p>" if spec.get("about") else "") +
            f"<h3>AI인가요?</h3><p>{esc(what_ai)}</p><h3>할 수 있는 것</h3><ul>{li(can)}</ul><h3>못 하는 것</h3><ul>{li(cannot)}</ul>"
            "<h3>개인정보</h3><p>입력한 내용은 이 화면에만 있어요. 저장하거나 보내지 않고, 새로고침하면 사라져요. 학생 이름·번호는 넣지 마세요.</p>"
            "<h3>단축키</h3><ul><li>P = 프로젝터 모드</li><li>+ / − = 글자 크게 / 작게</li><li>? = 이 안내</li><li>Esc = 닫기</li></ul>"
            f'<p><button type="button" class="wa-btn" id="wa-about-close">{_icon("x", 20)}<span>닫기</span></button></p></dialog>')


def build(spec: dict, fonts: bool = True) -> tuple[str, dict]:
    errs = validate(spec)
    if errs:
        raise ValueError("; ".join(errs))
    t = make_tokens(spec)
    parts = spec["parts"]
    title = str(spec["title"]).strip()
    sub = str(spec.get("subtitle") or "").strip()
    root_vars = shell.vars_style(t) + ";--app-bg:%s;--app-top:%s;--app-tint:%s" % (
        shell.pattern(t), shell.rgba(t["bg"], 0.86), shell.mix(t["surface"], t["primary"], 0.1))
    css = (ASSETS / "app.css").read_text(encoding="utf-8")
    try:
        import system as _ds  # shared/design/system.py (next to styles.py)
        ds_css = _ds.css_vars("web") + "\n" + _ds.polish_css("web")
    except Exception:  # noqa: BLE001
        ds_css = ""
    custom_css = "\n".join(str(p.get("css") or "") for p in parts if p["type"] == "custom")
    custom_js = "\n".join(";(function(){\n%s\n})();" % p["js"] for p in parts if p["type"] == "custom" and p.get("js"))
    tb = lambda id_, ic, lab, extra="": (f'<button type="button" class="wa-tb" id="{id_}" aria-label="{esc(lab)}" title="{esc(lab)}"{extra}>'  # noqa: E731
                                         f'{_icon(ic, 20)}<span class="wa-lbl">{esc(lab)}</span></button>')
    tools = (tb("wa-smaller", "minus", "글자 작게") + tb("wa-bigger", "plus", "글자 크게") + tb("wa-proj", "eye", "프로젝터", ' aria-pressed="false"')
             + tb("wa-reset", "refresh", "처음으로") + tb("wa-about-btn", "info-circle", "이 프로그램은?"))
    brand_icon = str(spec.get("icon") or shell.icon_for(title + " " + sub))
    layout, head = pick_layout(spec)
    cols = " " + layout
    cfg = {"title": title, "ai": spec.get("ai", "none"), "style": t["picked"], "layout": layout, "head": head,
           "parts": [{k: v for k, v in p.items() if k not in ("html", "css", "js")} for p in parts]}
    page = ('<!DOCTYPE html>\n<html lang="ko"><head><meta charset="utf-8">' + ('<meta name="ts-fixture" content="1">' if spec.get("_fixture") else "") + '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{esc(title)}</title>\n<style>:root{{{root_vars}}}\n{shell.css()}\n{ds_css}\n{css}\n{custom_css}</style></head>\n<body data-wa-layout="{layout}" data-wa-head="{head}">'
            '<a class="wa-skip" href="#wa-main">본문으로 건너뛰기</a>'
            f'<header class="wa-top"><div class="wa-brand">{shell.spot(brand_icon if brand_icon in shell.icon_names() else "sparkles", t, 60)}'
            f'<div><h1 class="wa-title">{esc(title)}</h1>' + (f'<p class="wa-sub">{esc(sub)}</p>' if sub else "") + "</div></div>"
            f'<div class="wa-tools" role="toolbar" aria-label="화면 도구">{tools}</div></header>\n'
            f'<main id="wa-main" class="wa-main{cols}">' + "".join(part_html(i, p) for i, p in enumerate(parts)) + (note_html(spec) if layout == "aside" else "") + "</main>\n"
            '<footer class="wa-foot">인터넷 없이 동작해요 · 입력한 내용은 저장되거나 전송되지 않아요 · 단축키 P 프로젝터 · +/− 글자 · ? 안내</footer>\n'
            + about_html(spec) + '<div id="wa-live" class="wa-sr" aria-live="polite"></div>\n'
            f"<script>window.WEBAPP = {js_json(cfg)};</script>\n<script>{(ASSETS / 'app.js').read_text(encoding='utf-8')}</script>\n"
            + (f"<script>{custom_js}</script>\n" if custom_js else "") + "</body></html>\n")
    report = {"style": t["picked"], "embedded": False}
    if fonts:
        out = shell.embed_fonts(page)
        report["embedded"] = out is not page and "ts-fonts" in out
        page = out
    return page, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shot", help="save a 1600x900 screenshot here (after one click on each part)")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--no-browser", action="store_true", help="static checks only (no headless browser)")
    ap.add_argument("--no-fonts", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    try:
        page, rep = build(spec, not a.no_fonts)
    except ValueError as exc:
        print(f"FAIL spec: {exc}")
        return 1
    out = Path(a.out)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(page.encode('utf-8')) // 1024} KB, style {rep['style']}, fonts {'embedded' if rep['embedded'] else 'not embedded'})")
    if a.no_check:
        print(f"PARTIAL {out.resolve()} (checks disabled)")
        return 0
    import check_webapp
    rc = check_webapp.run(out, browser=not a.no_browser, shot=a.shot)
    status = {0: "READY", 2: "PARTIAL"}.get(rc, "NOT READY")
    print(f"{status} {out.resolve()} ({time.time() - t0:.1f}s)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
