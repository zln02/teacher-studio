# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Spec rules shared by build.py and check_game.py. Messages are written as spec-fix hints (what to change in spec.json)."""
from __future__ import annotations

import random
import re

QUIZ_LIKE = ("quiz", "escape", "board")
LIMITS = {  # mechanic: (min items, max items)
    "quiz": (3, 40), "survival": (3, 40), "escape": (3, 6), "match": (3, 8), "bingo": (9, 30), "board": (6, 40), "sort": (4, 30),
}
FREE_ORDER_WORDS = ("모두", "위의", "둘 다", "모든 것", "①", "②", "ㄱ,")


def _quiz_item(i: int, it: dict, errs: list[str], ox_only: bool = False) -> None:
    """Validate one question item."""
    p = f"items[{i}]"
    if not isinstance(it.get("q"), str) or not it["q"].strip():
        errs.append(f"{p}.q (문제 문장)를 적어 주세요")
        return
    ox = it.get("type") == "ox" or not it.get("choices")
    if ox_only and not ox:
        errs.append(f'{p}: 이 게임은 OX 문제만 써요 → "type":"ox" 로 바꾸고 choices를 지워 주세요')
    if ox:
        if it.get("answer") not in (0, 1):
            errs.append(f"{p}.answer: OX 문제는 0(O) 또는 1(X)")
        return
    ch = it["choices"]
    if not isinstance(ch, list) or not 2 <= len(ch) <= 4:
        errs.append(f"{p}.choices: 보기는 2~4개 (지금 {len(ch) if isinstance(ch, list) else '?'}개)")
        return
    if len(set(map(str, ch))) != len(ch):
        errs.append(f"{p}.choices: 같은 보기가 있어요")
    if not isinstance(it.get("answer"), int) or not 0 <= it["answer"] < len(ch):
        errs.append(f"{p}.answer: 0~{len(ch) - 1} 사이의 정답 번호(0부터 셈)")
    for c in ch:
        if len(str(c)) > 40:
            errs.append(f"{p}.choices: 보기가 너무 길어요(40자 이내) → '{str(c)[:12]}…'")
            break

LIBS = ("anime", "motion", "confetti", "chartjs", "katex", "lucide", "phaser")  # shared/vendor ids a spec may ask for


def validate(spec: dict) -> list[str]:
    """Return a list of spec-fix hints (empty = spec is valid)."""
    errs: list[str] = []
    mech = spec.get("mechanic")
    if mech not in LIMITS:
        return [f'mechanic: "{mech}" 은(는) 없어요 → {" | ".join(LIMITS)} 중 하나']
    if not str(spec.get("title", "")).strip():
        errs.append("title: 게임 이름을 적어 주세요")
    if spec.get("use", "class") not in ("class", "personal"):
        errs.append('use: "class" 또는 "personal"')
    if spec.get("device", "board") not in ("board", "tablet", "phone"):
        errs.append('device: "board"(칠판) | "tablet" | "phone"')
    items = spec.get("items")
    if not isinstance(items, list):
        return errs + ["items: 문제·낱말 목록(배열)이 필요해요"]
    lo, hi = LIMITS[mech]
    if not lo <= len(items) <= hi:
        errs.append(f"items: {mech} 은(는) {lo}~{hi}개가 알맞아요 (지금 {len(items)}개)")
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            errs.append(f"items[{i}]: 객체 {{...}} 여야 해요")
        elif mech in QUIZ_LIKE or mech == "survival":
            _quiz_item(i, it, errs, ox_only=(mech == "survival"))
        elif mech == "match":
            if not it.get("a") or not it.get("b"):
                errs.append(f'items[{i}]: 짝 맞추기는 {{"a":"낱말","b":"짝"}} 형식')
        elif mech == "bingo":
            if not it.get("word") or not it.get("clue"):
                errs.append(f'items[{i}]: 빙고는 {{"word":"칸에 적힐 낱말","clue":"불러 주는 힌트"}} 형식')
        elif mech == "sort":
            if not it.get("q") or not it.get("a"):
                errs.append(f'items[{i}]: 분류는 {{"q":"카드 글자","a":"정답 통 이름"}} 형식')
    if mech == "bingo":
        g = spec.get("grid", 4)
        if g not in (3, 4):
            errs.append("grid: 3 또는 4")
        elif len(items) < g * g:
            errs.append(f"items: {g}x{g} 빙고는 낱말이 {g * g}개 이상 필요해요 (지금 {len(items)}개)")
    if mech == "sort":
        bins = spec.get("bins") or sorted({str(i.get("a")) for i in items if isinstance(i, dict)})
        if not 2 <= len(bins) <= 4:
            errs.append(f"bins/a: 통은 2~4개 (지금 {len(bins)}개) → items의 a 값을 묶어 주세요")
        else:
            miss = {i.get("a") for i in items if isinstance(i, dict)} - set(bins)
            if miss:
                errs.append(f"bins: items에 쓰인 통 이름이 bins에 없어요 → {sorted(map(str, miss))}")
    if mech == "survival" and spec.get("teams", 0) == 1:
        errs.append("teams: 서바이벌은 0(혼자) 또는 2~4팀")
    if spec.get("teams", 0) not in (0, 2, 3, 4):
        errs.append("teams: 0(개인) 또는 2~4")
    libs = spec.get("libs", [])
    if not isinstance(libs, list) or any(x not in LIBS for x in libs):
        errs.append(f"libs: 쓸 수 있는 부품만 → {', '.join(LIBS)} (예: [\"confetti\"])")
    if "motion" in (libs if isinstance(libs, list) else []) and spec.get("allow_modern") is not True:
        errs.append('libs: motion(움직임 부품)은 오래된 크롬에서 안 돌아가요 → 빼고 "anime"나 CSS를 쓰거나, 꼭 필요하면 allow_modern:true 를 함께 적어 주세요')
    if spec.get("allow_modern", False) not in (True, False) or spec.get("credit", False) not in (True, False):
        errs.append("allow_modern · credit: true 또는 false")
    errs += validate_custom(spec)
    design = spec.get("design", {})
    if design and not isinstance(design, dict):
        errs.append("design: {subject, grade, mood, seed, theme} 객체")
    elif isinstance(design, dict) and design.get("font") not in (None, "sans", "serif", "rounded", "system"):
        errs.append('design.font: "sans" | "serif" | "rounded" | "system" (글꼴은 이 넷 중에서만 골라요)')
    wv = spec.get("waive")
    if wv is not None and not (isinstance(wv, list) and all(x in WAIVE_OK for x in wv)):
        errs.append('waive: 사용자가 점검을 꺼 달라고 했을 때만. ' + " · ".join(WAIVE_OK) + ' 중에서 고르세요 (예: ["overflow"]). 점검은 주의로 낮아지고 한 줄 경고가 나와요')
    if spec.get("online", False) not in (True, False):
        errs.append('online: true 또는 false (기본 false = 인터넷 없이 열리는 파일. true일 때만 Google 글꼴·CDN 주소를 허용)')
    bk = spec.get("back")
    if bk is not None and not (isinstance(bk, dict) and isinstance(bk.get("href"), str) and re.fullmatch(r"(?!\s*(?:[a-z][a-z0-9+.-]*:|//))[^\s<>\"']+", bk["href"], re.I)):
        errs.append('back: {"href":"../index.html","label":"돌아가기"} (사이트 안의 상대 주소만, http:·javascript: 는 안 돼요)')
    hm = spec.get("head_meta")
    if hm is not None and not (isinstance(hm, list) and all(isinstance(x, dict) and x.get("name") in ("robots", "description", "theme-color", "author") and isinstance(x.get("content", ""), str) for x in hm)):
        errs.append('head_meta: [{"name":"robots","content":"noindex"}] (name은 robots · description · theme-color · author)')
    return errs


WAIVE_OK = ("text_size", "overflow", "hud", "phone")  # quality checks the user may turn off (check_game.apply_waive)
CUSTOM_CSS_MAX = 6000
CUSTOM_SVG_MAX = 12000
_BAD_COMMON = (
    (re.compile(r"https?:|//|@import|expression\s*\(|javascript:|\?\.|\?\?", re.I), "바깥 주소(http, //), @import, javascript:, ?. ?? 는 쓸 수 없어요"),
)


def validate_custom(spec: dict) -> list[str]:
    """custom_css / custom_svg: the AI's own extra flair. Sandboxed: size caps, no external resources, no scripts, plain old-Chrome syntax."""
    errs: list[str] = []
    css, svg = spec.get("custom_css"), spec.get("custom_svg")
    if css is not None:
        if not isinstance(css, str) or len(css) > CUSTOM_CSS_MAX:
            errs.append(f"custom_css: 글자(문자열) {CUSTOM_CSS_MAX}자 이내")
        else:
            for pat, msg in _BAD_COMMON:
                if pat.search(css.replace("/*", " ").replace("*/", " ")):
                    errs.append("custom_css: " + msg)
            if re.search(r"aspect-ratio|:has\(|\bdvh\b|behavior\s*:|-moz-binding", css):
                errs.append("custom_css: aspect-ratio / :has() / dvh 는 오래된 크롬에서 안 돌아가요")
            if re.search(r"url\(\s*['\"]?(?!data:image/svg)", css):
                errs.append("custom_css: url(...)은 쓸 수 없어요 (그림은 custom_svg로)")
    if svg is not None:
        if not isinstance(svg, str) or len(svg) > CUSTOM_SVG_MAX:
            errs.append(f"custom_svg: 글자(문자열) {CUSTOM_SVG_MAX}자 이내")
        else:
            if re.search(r"<\s*(script|foreignObject|iframe|image|use)\b|\son\w+\s*=|javascript:|https?:|//|\bhref\s*=", svg, re.I) and not re.search(r"xmlns\s*=\s*[\"']http://www\.w3\.org/2000/svg[\"']", svg):
                errs.append("custom_svg: script·foreignObject·image·use·onclick·href·바깥 주소는 쓸 수 없어요")
            elif re.search(r"<\s*(script|foreignObject|iframe|image|use)\b|\son\w+\s*=|javascript:|\bhref\s*=", svg, re.I):
                errs.append("custom_svg: script·foreignObject·image·use·onclick·href는 쓸 수 없어요")
            elif re.search(r"https?:", svg.replace("http://www.w3.org/2000/svg", "")):
                errs.append("custom_svg: 바깥 주소(http)는 쓸 수 없어요")
            if re.search(r"\?\.|\?\?", svg):
                errs.append("custom_svg: ?. ?? 는 쓸 수 없어요")
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(svg)
                if not root.tag.endswith("svg"):
                    errs.append('custom_svg: 맨 바깥은 <svg viewBox="0 0 1920 1080"> 이어야 해요')
            except Exception as exc:  # malformed
                errs.append(f"custom_svg: SVG 형식 오류 ({str(exc)[:60]})")
    return errs


def answer_bias(items: list[dict]) -> str | None:
    """Return a hint if correct answers pile up on one position (>=5 multiple-choice items)."""
    mc = [i for i in items if isinstance(i, dict) and i.get("choices") and i.get("type") != "ox" and isinstance(i.get("answer"), int)]
    if len(mc) < 5:
        return None
    counts: dict[int, int] = {}
    for i in mc:
        counts[i["answer"]] = counts.get(i["answer"], 0) + 1
    pos, n = max(counts.items(), key=lambda kv: kv[1])
    if n / len(mc) > 0.5:
        return f"정답이 {'ABCD'[pos]}번에 {n}/{len(mc)}개 쏠려 있어요 → spec에 shuffleChoices:true(기본)를 두거나 answer 위치를 고루 나눠 주세요"
    return None


def balance_choices(items: list[dict], seed: int = 0) -> int:
    """Deterministically spread correct answers over positions (in place). Returns how many items moved."""
    rng = random.Random(seed)
    mc = [i for i in items if i.get("choices") and i.get("type") != "ox" and not i.get("keepOrder")
          and not any(w in " ".join(map(str, i["choices"])) for w in FREE_ORDER_WORDS)]
    moved = 0
    order: list[int] = []
    for it in mc:
        if not order:
            order = [0, 1, 2, 3]
            rng.shuffle(order)
        want = order.pop() % len(it["choices"])
        right = it["choices"][it["answer"]]
        rest = [c for k, c in enumerate(it["choices"]) if k != it["answer"]]
        rng.shuffle(rest)
        rest.insert(want, right)
        if rest != it["choices"]:
            moved += 1
        it["choices"], it["answer"] = rest, want
    return moved


NEGATIVE_Q = ("아닌", "않은", "않는", "틀린", "잘못", "없는 것")
CATCH_ALL = ("모두 정답", "모두 맞", "위의 모두", "위 모두", "정답 없음", "답 없음", "둘 다", "all of the above", "none of the above")


def content_review(spec: dict) -> list[str]:
    """Advice on the QUESTIONS (not the code): what an experienced teacher would fix before class.
    Never blocks a build; build.py prints each line as `CONTENT ...`. Fix the spec once, do not loop."""
    items = [i for i in (spec.get("items") or []) if isinstance(i, dict)]
    mc = [i for i in items if isinstance(i.get("choices"), list) and len(i["choices"]) >= 2 and i.get("type") != "ox"
          and isinstance(i.get("answer"), int) and 0 <= i["answer"] < len(i["choices"])]
    asked = [i for i in items if isinstance(i.get("q"), str)]
    out: list[str] = []
    board = spec.get("use", "class") == "class" and spec.get("device", "board") == "board"
    if len(mc) >= 5:
        longest = [k for k, i in enumerate(mc) if all(len(str(i["choices"][i["answer"]])) > len(str(c)) + 1
                                                     for j, c in enumerate(i["choices"]) if j != i["answer"])]
        if len(longest) / len(mc) > 0.5:
            out.append(f"the correct choice is the longest one in {len(longest)}/{len(mc)} questions (students guess by length) -> make wrong choices about as long as the right one")
    catch = [k + 1 for k, i in enumerate(mc) if any(w in str(c).lower() for c in i["choices"] for w in CATCH_ALL)]
    if catch:
        out.append(f"question {catch[:4]} uses a catch-all choice (모두 정답 / 정답 없음 / 둘 다) -> replace it with a real, plausible wrong answer")
    if spec.get("mechanic") in QUIZ_LIKE and spec.get("use", "class") == "class":
        noexp = [k + 1 for k, i in enumerate(asked) if not str(i.get("exp", "")).strip()]
        if noexp:
            out.append(f"{len(noexp)} question(s) have no `exp` (first: {noexp[:4]}) -> add one line that says WHY the answer is right; a wrong team learns from it")
    echo = [k + 1 for k, i in enumerate(mc)
            if re.match(re.escape(str(i["choices"][i["answer"]]).strip()) + r"\s*[:：=—–-]", str(i.get("exp", "")).strip())]
    if echo:
        out.append(f"`exp` of question {echo[:4]} starts with the answer as a label (「토큰: …」); the screen already prints 「정답: 토큰 — 」 before it -> start with the reason")
    seen: dict[str, int] = {}
    for k, i in enumerate(asked):
        key = re.sub(r"\s+", "", i["q"])
        if key in seen:
            out.append(f"questions {seen[key] + 1} and {k + 1} are the same sentence -> change one")
            break
        seen[key] = k
    if board:
        longq = [k + 1 for k, i in enumerate(asked) if len(i["q"]) > 48]
        if longq:
            out.append(f"{len(longq)} question(s) are over 48 characters (first: {longq[:4]}): hard to read from the back row -> one sentence, about 25-40 characters")
        longc = [k + 1 for k, i in enumerate(mc) if any(len(str(c)) > 16 for c in i["choices"])]
        if longc:
            out.append(f"{len(longc)} question(s) have a choice over 16 characters (first: {longc[:4]}): it will shrink or wrap -> shorten to a word or short phrase")
    neg = [k + 1 for k, i in enumerate(asked) if any(w in i["q"] for w in NEGATIVE_Q)]
    if len(asked) >= 5 and len(neg) / len(asked) > 0.3:
        out.append(f"{len(neg)}/{len(asked)} questions ask for the WRONG one (아닌/않은/틀린) -> keep at most 2 in 10")
    if board and spec.get("mechanic") == "quiz" and (spec.get("teams") or 0) >= 2 and not spec.get("timer"):
        out.append('team game on the board without a timer -> add "timer": 20 (20-30 s keeps turns moving)')
    return out
