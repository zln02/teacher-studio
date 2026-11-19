#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Quality + privacy gate for a teacher-data report.

    python3 check_report.py report.html --agg aggregates.json [--source original.csv|xlsx] [--no-play] [--yes]

Static: zero external requests / network+storage APIs, no form, old-Chrome syntax in our own script, keep-all, text-size and contrast floors,
conclusion first, units on every chart, chart data == aggregates, every number in the sentences exists in the aggregates (rounded),
no raw personal data (patterns; and with --source the actual names/phones/e-mails/ids of the original file),
readability by audience (sentence length, hard-word ratio).
Headless (Playwright, system Chrome, audio muted; skipped with --no-play): no external request, no JS error, no overflow at 1280 and 390 px,
every canvas really drawn, computed keep-all, smallest text >= 14 px.
Prints PASS/WARN/FAIL lines; exit 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import html as H
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tdata  # noqa: E402
import design  # noqa: E402

MAX_SENT = {"초등": 42, "학부모": 58, "선생님": 75, "전문가": 95}
HARD = ["표준편차", "유의", "가설", "분산", "중앙값", "귀무", "상관계수", "인과", "신뢰구간", "회귀", "효과크기", "p값", "p ="]
HARD_RATIO_MAX = {"초등": 0.0, "학부모": 0.0, "선생님": 0.04, "전문가": 0.15}
FAILS = 0


def say(level: str, msg: str) -> None:
    global FAILS
    if level == "FAIL":
        FAILS += 1
    print(f"{level} {msg}")


def strip_tags(s: str) -> str:
    return H.unescape(re.sub(r"<[^>]+>", " ", s)).strip()


def cssvars(css: str) -> dict[str, str]:
    root = re.search(r":root\{([^}]*)\}", css)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", root.group(1))) if root else {}


def numbers_in(text: str) -> list[tuple[float, int]]:
    out = []
    for m in re.finditer(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", text):
        s = m.group(0).replace(",", "")
        out.append((float(s), len(s.split(".")[1]) if "." in s else 0))
    return out


def allowed_numbers(agg: dict) -> set[float]:
    vals: set[float] = set()

    def walk(o):
        if isinstance(o, bool):
            return
        if isinstance(o, (int, float)):
            vals.add(float(o))
            vals.add(abs(float(o)))
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            for n, _ in numbers_in(o):
                vals.add(n)
    walk(agg)
    for r in agg["results"]:
        for s in r["series"]:
            xs = [v for v in s["values"] if v is not None]
            for i, a in enumerate(xs):
                for b in xs[:i] + xs[i + 1:]:
                    vals.add(abs(a - b))
        if len(r["series"]) == 2:
            for a, b in zip(r["series"][0]["values"], r["series"][1]["values"]):
                if a is not None and b is not None:
                    vals.add(abs(b - a))
        vals.add(sum(v for v in r["series"][0]["values"] if v is not None))
        vals.add(float(len(r["labels"])))
    return vals


def matches(x: float, d: int, allowed: set[float]) -> bool:
    tol = 0.5 * 10 ** -d + 1e-9
    return any(abs(a - x) <= tol for a in allowed)


def static_checks(src: str, agg: dict | None, source_path: str | None, yes: bool) -> str:
    aud = re.search(r'data-audience="([^"]+)"', src)
    aud = aud.group(1) if aud else "학부모"
    # remove vendored lib + embedded font data before scanning our own code
    own = re.sub(r'<script id="chartjs">.*?</script>', "", src, flags=re.S)
    own = re.sub(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]+", "data:", own)
    # 1. zero external requests
    ext = re.findall(r"""(?:src|href|action|poster|data)\s*=\s*["']\s*(?:https?:)?//[^"']+|url\(\s*["']?\s*(?:https?:)?//|@import|<link\b""", own, flags=re.I)
    say("FAIL" if ext else "PASS", "바깥 주소로 가는 요청 없음" + (f" ({len(ext)}곳: {ext[0][:60]})" if ext else ""))
    code = re.search(r'<script id="ts-draw">(.*?)</script>', own, flags=re.S)
    code = code.group(1) if code else ""
    bad = re.findall(r"\b(fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|importScripts|localStorage|sessionStorage|indexedDB)\b|document\.cookie|<form|<input", own)
    say("FAIL" if bad else "PASS", "네트워크·저장 기능·입력 칸 없음" + (f" ({bad[0]})" if bad else ""))
    say("FAIL" if re.search(r"\?\.(?=[A-Za-z_$\[(])|\?\?", code) else "PASS", "스크립트가 옛 크롬에서도 돌아가는 문법")
    # 2. keep-all, lang, sizes, contrast
    css = "\n".join(re.findall(r"<style>(.*?)</style>", own, flags=re.S))
    say("PASS" if "word-break:keep-all" in css.replace(" ", "") else "FAIL", "한국어 줄바꿈 keep-all")
    say("PASS" if 'lang="ko"' in own[:200] else "FAIL", "lang=ko")
    bm = re.search(r"--base:(\d+)px", css)
    base = int(bm.group(1)) if bm else 16
    sizes = [float(x) for x in re.findall(r"font-size:(\d+(?:\.\d+)?)px", css)]
    for m in re.finditer(r"font-size:calc\(var\(--base\)\*([\d.]+)\)", css):
        sizes.append(base * float(m.group(1)))
    small = [s for s in sizes if s < 14]
    say("FAIL" if small else "PASS", f"글자 크기 14px 이상 (가장 작은 값 {min(sizes) if sizes else '?'}px, 본문 {base}px)")
    v = cssvars(css)
    pairs = [("ink", "bg", 4.5), ("ink", "card", 4.5), ("muted", "card", 4.5), ("muted", "bg", 4.5), ("on-brand", "brand", 4.5), ("brand", "card", 3.0)]
    worst = min(design.contrast(v[a], v[b]) for a, b, _ in pairs if a in v and b in v) if v else 0
    badc = [f"{a}/{b}={design.contrast(v[a], v[b]):.2f}" for a, b, r in pairs if a in v and b in v and design.contrast(v[a], v[b]) < r]
    say("FAIL" if badc or not v else "PASS", f"색 대비 (가장 낮은 값 {worst:.2f}:1)" + (" " + ", ".join(badc) if badc else ""))
    # 3. conclusion first
    pc, ps, pcv = own.find('id="conclusion"'), own.find('id="summary"'), own.find("<canvas")
    say("PASS" if 0 < pc < ps < pcv else "FAIL", "결론이 맨 위, 그다음 3줄 요약, 그다음 그래프")
    head = re.search(r'<p class="headline">(.*?)</p>', own, flags=re.S)
    head_t = strip_tags(head.group(1)) if head else ""
    say("PASS" if head_t and len(head_t) <= MAX_SENT[aud] + 6 else "FAIL", f"결론은 한 문장({len(head_t)}자): {head_t}")
    sm = re.search(r'id="summary".*?</section>', own, flags=re.S)
    lines = re.findall(r"<li>(.*?)</li>", sm.group(0), flags=re.S) if sm else []
    say("PASS" if len(lines) == 3 else "FAIL", f"요약은 3줄 ({len(lines)}줄)")
    # 4. units + chart data
    figs = re.findall(r"<section class='card chart'.*?</section>", own, flags=re.S)
    miss = []
    for f in figs:
        u = re.search(r"data-unit='([^']*)'", f).group(1)
        title = strip_tags(re.search(r"<h2>(.*?)</h2>", f).group(1))
        if not u or u not in title:
            miss.append(title[:20])
    say("FAIL" if miss or not figs else "PASS", f"그래프마다 단위가 제목에 있음 ({len(figs)}개)" + (f" 빠진 곳: {miss}" if miss else ""))
    say("PASS" if "단위: " in code else "FAIL", "그래프 축에 단위 표시")
    data = json.loads(re.search(r'<script id="ts-data" type="application/json">(.*?)</script>', own, flags=re.S).group(1).replace("<\\/", "</"))
    pies = [c for c in data["charts"] if c["kind"] == "share" and len(c["labels"]) > 5]
    say("FAIL" if pies else "PASS", "원그래프는 조각 5개 이하")
    for c in data["charts"]:
        if c["kind"] == "line" and len(c["labels"]) < 2:
            say("FAIL", "꺾은선인데 점이 1개")
    texts = [head_t] + [strip_tags(x) for x in lines]
    if agg:
        ok = len(data["charts"]) == len(agg["results"])
        for c, r in zip(data["charts"], agg["results"]):
            ok = ok and c["labels"] == r["labels"] and [s["values"] for s in c["series"]] == [s["values"] for s in r["series"]]
        say("PASS" if ok else "FAIL", "그래프 숫자 = 집계 숫자")
    for f in figs:
        texts += [strip_tags(x) for x in re.findall(r"<li>(.*?)</li>", f, flags=re.S)]
        texts += [strip_tags(x) for x in re.findall(r"<p class='(?:how|note)'>(.*?)</p>", f, flags=re.S)]
    if agg:
        allowed = allowed_numbers(agg)
        wrong = [(t[:40], n) for t in texts for n, d in numbers_in(t) if not matches(n, d, allowed)]
        say("FAIL" if wrong else "PASS", f"글 속 숫자가 모두 집계에 있음 ({sum(len(numbers_in(t)) for t in texts)}개 확인)" + (f" 안 맞음: {wrong[:3]}" if wrong else ""))
    else:
        say("WARN", "--agg 없이는 숫자 대조를 건너뜁니다")
    # 6. readability
    sents = [s.strip() for t in texts for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]
    longest = max(sents, key=len) if sents else ""
    say("FAIL" if len(longest) > MAX_SENT[aud] else "PASS", f"문장 길이 {aud}용 {MAX_SENT[aud]}자 이하 (가장 긴 문장 {len(longest)}자)")
    words = sum(len(t.split()) for t in texts) or 1
    hard = sum(t.count(h) for t in texts for h in HARD)
    say("FAIL" if hard / words > HARD_RATIO_MAX[aud] else "PASS", f"어려운 말 비율 {hard}/{words} ({aud}용 허용 {HARD_RATIO_MAX[aud]:.0%})")
    # 7. personal data
    pats = [("전화번호", tdata.RE_PHONE), ("이메일", tdata.RE_EMAIL), ("주민번호", tdata.RE_RRN)]
    hit = [n for n, rx in pats if rx.search(own)]
    say("FAIL" if hit else "PASS", "글 속에 전화·이메일·주민번호 모양 없음" + (f" ({hit})" if hit else ""))
    if source_path:
        t = tdata.load(source_path, consent=yes)
        pii = tdata.detect_pii(t)
        leaks = []
        blob = own + (json.dumps(agg, ensure_ascii=False) if agg else "")
        for c in pii:
            for val in {str(x).strip() for x in t.data[c] if not tdata.is_missing(x)}:
                if len(val) >= 2 and val in blob:
                    leaks.append(f"{c}:{val[:2]}…")
        say("FAIL" if leaks else "PASS", f"원본의 개인정보 칸 {len(pii)}개({', '.join(pii) or '없음'}) 값이 결과에 없음" + (f" 새어 나옴 {leaks[:3]}" if leaks else ""))
    else:
        say("WARN", "--source 없이는 원본 이름 대조를 건너뜁니다")
    if agg:
        say("PASS" if "records" not in agg and "rows" not in agg else "FAIL", "집계 파일에 원본 줄 없음")
    return aud


def play_checks(path: Path) -> None:
    try:
        import ensure
        from playwright.sync_api import sync_playwright
    except ImportError:
        say("WARN", "Playwright가 없어 화면 점검은 건너뜁니다 (python3 shared/tools/ensure.py playwright --yes)")
        return
    info = ensure.ensure_playwright()
    if not info["ok"]:
        say("WARN", "브라우저를 못 찾아 화면 점검은 건너뜁니다")
        return
    with sync_playwright() as pw:
        kw = {"channel": info["channel"]} if info.get("channel") else {}
        br = pw.chromium.launch(args=["--mute-audio"], **kw)
        for w, h in ((1280, 800), (390, 800)):
            pg = br.new_page(viewport={"width": w, "height": h})
            ext, errs = [], []
            pg.on("request", lambda rq: ext.append(rq.url) if not rq.url.startswith(("file:", "data:", "blob:")) else None)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(path.resolve().as_uri())
            try:
                pg.wait_for_selector("html[data-charts-ready='1']", state="attached", timeout=8000)
            except Exception:
                say("FAIL", f"{w}px: 그래프가 그려지지 않았어요")
                continue
            pg.wait_for_timeout(900)
            say("FAIL" if ext else "PASS", f"{w}px: 실제로 바깥 요청 0건" + (f" ({ext[:2]})" if ext else ""))
            say("FAIL" if errs else "PASS", f"{w}px: 자바스크립트 오류 없음" + (f" {errs[:2]}" if errs else ""))
            ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            say("FAIL" if ov > 1 else "PASS", f"{w}px: 옆으로 넘치지 않음 ({ov}px)")
            blank = pg.evaluate("Array.prototype.filter.call(document.querySelectorAll('canvas'),function(c){var d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;for(var i=3;i<d.length;i+=4){if(d[i]>0)return false;}return true;}).length")
            say("FAIL" if blank else "PASS", f"{w}px: 그래프가 모두 그려짐 (빈 그래프 {blank}개)")
            if w == 1280:
                kp = pg.evaluate("getComputedStyle(document.body).wordBreak")
                say("PASS" if kp == "keep-all" else "FAIL", f"실제 줄바꿈 규칙 {kp}")
                ms = pg.evaluate("(function(){var m=99,w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),n;while(n=w.nextNode()){if(!n.nodeValue.trim())continue;var e=n.parentElement;if(!e||e.closest('script,style'))continue;var cs=getComputedStyle(e);if(cs.display==='none'||cs.visibility==='hidden')continue;var f=parseFloat(cs.fontSize);if(f<m)m=f;}return m;})()")
                say("PASS" if ms >= 14 else "FAIL", f"화면에서 가장 작은 글자 {ms:.1f}px")
            pg.close()
        br.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", type=Path)
    ap.add_argument("--agg", type=Path)
    ap.add_argument("--source")
    ap.add_argument("--no-play", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    src = a.report.read_text(encoding="utf-8")
    agg = json.loads(a.agg.read_text(encoding="utf-8")) if a.agg else None
    static_checks(src, agg, a.source, a.yes)
    try:  # colour-blind check: WARN only
        import color_check
        for lv, msg in color_check.html_results(src):
            say(lv, msg)
    except ImportError:
        pass
    if not a.no_play:
        play_checks(a.report)
    print("결과:", "FAIL" if FAILS else "PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
