# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Spec rules shared by build.py and check_game.py. Messages are written as spec-fix hints (what to change in spec.json)."""
from __future__ import annotations

import random

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
    design = spec.get("design", {})
    if design and not isinstance(design, dict):
        errs.append("design: {subject, grade, mood, seed, theme} 객체")
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
