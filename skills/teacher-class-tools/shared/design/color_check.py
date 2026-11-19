#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Colour-blind check (stdlib only): do colours that carry meaning (correct/wrong, team colours, chart series) stay apart for people with colour-vision deficiency?

Simulation: Machado, Oliveira & Fernandes (2009), "A Physiologically-based Model for Simulation of Color Vision Deficiency", severity 1.0 matrices,
applied in LINEAR RGB (protan = no red cones, deutan = no green, tritan = no blue). Distance: OKLab Euclidean (ΔE_OK, see oklch.py).

Threshold: MIN_DE = 0.10. ΔE_OK ~0.02 is the just-noticeable difference side by side; 0.10 is "clearly different at TV distance on a classroom wall".
Pairs below 0.10 in ANY of the three simulations are reported. It is a WARN only (never FAIL): shapes, icons and text (○ ✕ 정답/오답) fix it too.

    from color_check import check_pairs, check_tokens, check_html, warn_lines
    check_pairs({"정답": "#0f8a4a", "오답": "#c4163a"})        # -> [{"a","b","kind","de",...}, ...]
    warn_lines(check_tokens(tokens))                            # -> ["빨강·초록만으로 ..."]  (one plain-Korean line per problem group)

CLI:  python3 color_check.py "#0f8a4a" "#c4163a" "#2b6cff"     # all pairs among the colours
      python3 color_check.py --tokens tokens.json | --html page.html
Exit code is always 0 (it only warns).
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oklch  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

MIN_DE = 0.10
# Machado 2009, severity 1.0, applied to linear RGB column vectors
MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}
KIND_LABEL = {"protan": "적색약(빨간색을 약하게 봄)", "deutan": "녹색약(초록색을 약하게 봄)", "tritan": "청황색약(파랑·노랑이 헷갈림)"}


def simulate(hexc: str, kind: str) -> str:
    """The colour as seen with protan / deutan / tritan vision (Machado 2009, severity 1.0, linear RGB)."""
    m = MACHADO[kind]
    v = oklch.hex_to_linear(hexc)
    return oklch.linear_to_hex(*(sum(m[i][j] * v[j] for j in range(3)) for i in range(3)))


def check_pairs(colors: dict, threshold: float = MIN_DE, pairs: list | None = None) -> list[dict]:
    """Pairs of named colours that look too alike in some simulation. `pairs` limits which name pairs are compared (default: all pairs).

    Returns [{a, b, ca, cb, kind, de, normal_de}] worst first; a pair is listed once, for its worst simulation.
    Pairs that are already too close with normal vision are skipped (that is a plain design problem, not a colour-blind one)."""
    names = list(colors)
    todo = pairs if pairs is not None else list(itertools.combinations(names, 2))
    out = []
    for a, b in todo:
        if a not in colors or b not in colors:
            continue
        ca, cb = colors[a], colors[b]
        normal = oklch.delta_e(ca, cb)
        if normal < threshold:
            continue
        worst = min(((oklch.delta_e(simulate(ca, k), simulate(cb, k)), k) for k in MACHADO))
        if worst[0] < threshold:
            out.append({"a": a, "b": b, "ca": ca, "cb": cb, "kind": worst[1], "de": round(worst[0], 3), "normal_de": round(normal, 3)})
    return sorted(out, key=lambda x: x["de"])


def check_tokens(tokens: dict) -> list[dict]:
    """Meaning-bearing pairs inside design tokens: good/bad (correct/wrong). Add `series`/`teams` lists to tokens to check those too."""
    c = tokens.get("colors", {})
    found = check_pairs({k: c[k] for k in ("good", "bad") if k in c}, pairs=[("good", "bad")])
    for key in ("series", "teams"):
        lst = tokens.get(key)
        if isinstance(lst, list) and len(lst) > 1:
            found += check_pairs({f"{key}{i + 1}": x for i, x in enumerate(lst) if _is_hex(x)})
    return found


def _is_hex(x) -> bool:
    return isinstance(x, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", x) is not None


_VAR = re.compile(r"--(good|bad|ok|wrong|correct|team\d|c\d)\s*:\s*(#[0-9a-fA-F]{6})\b")


def _groups(html: str) -> list[tuple[dict, list]]:
    """[(named colours, pairs to compare)] found in a built page: good/bad, team variables, chart series."""
    named: dict[str, str] = {}
    for k, v in _VAR.findall(html):
        named.setdefault(k, v.lower())
    for k in ("good", "bad"):
        m = re.search(r'"%s"\s*:\s*"(#[0-9a-fA-F]{6})"' % k, html)
        if m:
            named.setdefault(k, m.group(1).lower())
    pairs = [("good", "bad")] if "good" in named and "bad" in named else []
    for a, b in (("ok", "wrong"), ("correct", "wrong")):
        if a in named and b in named:
            pairs.append((a, b))
    teams = sorted(k for k in named if re.fullmatch(r"team\d|c\d", k))
    pairs += list(itertools.combinations(teams, 2))
    groups = [(named, pairs)] if pairs else []
    seen_sets = set()
    for series in [_chart_series(html)] + _color_lists(html):
        if len(series) > 1 and tuple(series) not in seen_sets:
            seen_sets.add(tuple(series))
            groups.append(({f"series{i + 1}": c for i, c in enumerate(series)}, None))
    return groups


def check_html(html: str) -> list[dict]:
    """Find meaning colours in a built page and check them: CSS variables --good/--bad (and --team1.., --c1..), tokens JSON "good"/"bad", chart series
    colours ("colors":[...] lists, Chart.js backgroundColor/borderColor with 2+ datasets). Returns problem pairs (see check_pairs)."""
    out: list[dict] = []
    for named, pairs in _groups(html):
        out += check_pairs(named, pairs=pairs)
    return out


def html_results(html: str) -> list[tuple[str, str]]:
    """For the checkers: [("WARN", plain-Korean hint)...] or one PASS line when meaning colours were found and are fine; [] when there was nothing to check.
    Also carries the anti AI-default-look result (ai_look.py: cream + clay + serif, blue-purple gradient + emoji)."""
    return _cvd_results(html) + _ai_look_results(html)


def _ai_look_results(html: str) -> list[tuple[str, str]]:
    """Anti AI-default-look hint (ai_look.py) rides along so every checker that calls html_results gets it."""
    try:
        import ai_look
        return ai_look.html_results(html)
    except Exception:  # never break a check
        return []


def _cvd_results(html: str) -> list[tuple[str, str]]:
    groups = _groups(html)
    if not groups:
        return []
    found = [f for named, pairs in groups for f in check_pairs(named, pairs=pairs)]
    if not found:
        return [("PASS", f"color-blind safe: meaning colours stay apart in protan/deutan/tritan (OKLab ΔE >= {MIN_DE})")]
    return [("WARN", line) for line in warn_lines(found)]


def _color_lists(html: str) -> list[list[str]]:
    """JSON colour lists such as "colors":["#2563eb","#b45309",...] (data-report chart configs), first 8 colours of each."""
    out = []
    for m in re.finditer(r'"colors"\s*:\s*\[([^\]]*)\]', html):
        cols = [c.lower() for c in re.findall(r'"(#[0-9a-fA-F]{6})"', m.group(1))]
        if len(cols) > 1:
            out.append(cols[:8])
    return out


def _chart_series(html: str) -> list[str]:
    """Distinct hex colours used as dataset colours (`backgroundColor` / `borderColor` / `color`), in order of first use, capped at 8."""
    seen: list[str] = []
    for m in re.finditer(r"(?:backgroundColor|borderColor)\s*:\s*['\"](#[0-9a-fA-F]{6})['\"]", html):
        c = m.group(1).lower()
        if c not in seen:
            seen.append(c)
    return seen[:8]


def _name(key: str) -> str:
    """Plain-Korean label for a colour key."""
    fixed = {"good": "정답색", "bad": "오답색", "ok": "정답색", "correct": "정답색", "wrong": "오답색"}
    if key in fixed:
        return fixed[key]
    m = re.fullmatch(r"series(\d+)", key)
    if m:
        return f"그래프 {m.group(1)}번째 색"
    m = re.fullmatch(r"(?:team|teams)(\d+)", key)
    if m:
        return f"{m.group(1)}모둠 색"
    return key


def warn_lines(found: list[dict]) -> list[str]:
    """One plain-Korean WARN sentence per problem (no jargon): what is confusing, who sees it, one fix."""
    out = []
    for f in found:
        who = KIND_LABEL[f["kind"]]
        a, b = _name(f["a"]), _name(f["b"])
        if f["kind"] in ("protan", "deutan") and {f["a"], f["b"]} == {"good", "bad"}:
            fix = "빨강·초록만으로 구분하고 있어요. 모양이나 글자(○ ✕, 정답/오답)도 같이 써 주세요."
        else:
            fix = "색만으로 구분하고 있어요. 모양·글자·무늬도 같이 써 주세요."
        out.append(f"색 구분: {a}과(와) {b}이(가) {who}에게 거의 같아 보여요 (차이 {f['de']:.2f} < {MIN_DE:.2f}). {fix}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("colors", nargs="*", help="#rrggbb colours (all pairs are compared)")
    ap.add_argument("--tokens", help="tokens JSON (design.py output)")
    ap.add_argument("--html", help="built HTML page")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.tokens:
        found = check_tokens(json.loads(Path(a.tokens).read_text(encoding="utf-8")))
    elif a.html:
        found = check_html(Path(a.html).read_text(encoding="utf-8", errors="replace"))
    else:
        found = check_pairs({f"색{i + 1}({c})": c for i, c in enumerate(a.colors)})
    if a.json:
        print(json.dumps(found, ensure_ascii=False, indent=1))
    else:
        print("\n".join("WARN " + x for x in warn_lines(found)) if found else f"PASS 색 구분: 적색약·녹색약·청황색약에서도 색이 구분돼요 (차이 >= {MIN_DE})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
