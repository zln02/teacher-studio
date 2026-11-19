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
Design = shared design system (styles.py style + shell kit tokens, icons, spot illustration, Noto Sans KR embedded).
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
    custom_css = "\n".join(str(p.get("css") or "") for p in parts if p["type"] == "custom")
    custom_js = "\n".join(";(function(){\n%s\n})();" % p["js"] for p in parts if p["type"] == "custom" and p.get("js"))
    tb = lambda id_, ic, lab, extra="": (f'<button type="button" class="wa-tb" id="{id_}" aria-label="{esc(lab)}" title="{esc(lab)}"{extra}>'  # noqa: E731
                                         f'{_icon(ic, 20)}<span class="wa-lbl">{esc(lab)}</span></button>')
    tools = (tb("wa-smaller", "minus", "글자 작게") + tb("wa-bigger", "plus", "글자 크게") + tb("wa-proj", "eye", "프로젝터", ' aria-pressed="false"')
             + tb("wa-reset", "refresh", "처음으로") + tb("wa-about-btn", "info-circle", "이 프로그램은?"))
    brand_icon = str(spec.get("icon") or shell.icon_for(title + " " + sub))
    cols = {1: "", 2: " cols2", 3: " cols3"}[len(parts)]
    cfg = {"title": title, "ai": spec.get("ai", "none"), "style": t["picked"],
           "parts": [{k: v for k, v in p.items() if k not in ("html", "css", "js")} for p in parts]}
    page = ('<!DOCTYPE html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{esc(title)}</title>\n<style>:root{{{root_vars}}}\n{shell.css()}\n{css}\n{custom_css}</style></head>\n<body>'
            '<a class="wa-skip" href="#wa-main">본문으로 건너뛰기</a>'
            f'<header class="wa-top"><div class="wa-brand">{shell.spot(brand_icon if brand_icon in shell.icon_names() else "sparkles", t, 60)}'
            f'<div><h1 class="wa-title">{esc(title)}</h1>' + (f'<p class="wa-sub">{esc(sub)}</p>' if sub else "") + "</div></div>"
            f'<div class="wa-tools" role="toolbar" aria-label="화면 도구">{tools}</div></header>\n'
            f'<main id="wa-main" class="wa-main{cols}">' + "".join(part_html(i, p) for i, p in enumerate(parts)) + "</main>\n"
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
        return 0
    import check_webapp
    rc = check_webapp.run(out, browser=not a.no_browser, shot=a.shot)
    print(f"{'READY' if rc == 0 else 'NOT READY'} {out.resolve()} ({time.time() - t0:.1f}s)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
