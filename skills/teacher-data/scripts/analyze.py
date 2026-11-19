#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Run common analyses from a small JSON plan and write ONLY aggregates (no raw rows).

    python3 analyze.py --data scores.csv --plan plan.json --out agg.json [--sheet S] [--yes]

Plan:
{"title": "...", "audience": "초등|학부모|선생님|전문가", "subject": "수학", "filters": [...],
 "analyses": [
  {"type": "groupby",  "by": "반", "value": "점수", "agg": "mean|sum|median|count|min|max", "sort": "none|desc|asc", "top": 5,
                       "test": true, "count_unit": "명", "unit": "점", "metric": "지출", "title": "...", "filter": [{"column": "시험일", "equals": "2026-11"}]},
  {"type": "distribution", "column": "학년군", "bins": [0,60,70,80,90,101], "bin_labels": [...], "order": [...], "style": "share"},
  {"type": "likert",   "columns": ["Q1", "Q2"], "scale_max": 5, "labels": {"Q1": "수업"}},
  {"type": "crosstab", "rows": "학년군", "cols": "만족도"},
  {"type": "trend",    "time": "날짜", "value": "금액", "agg": "sum", "freq": "month|week|day|year", "by": "분류", "filter": [...]},
  {"type": "change",   "by": "반", "time": "시험일", "value": "점수", "focus": "3반"},
  {"type": "correlation", "x": "공부시간", "y": "점수"},
  {"type": "overview", "columns": ["국어", "수학", "과학"] (optional: every numeric column), "group": "반" (optional: rank groups, else rows by pseudonym), "unit": "점", "bins": [...]}
 ]}
overview = ONE line for wide tables (one row per student, one column per subject): stats of every column, score bands, top/bottom, which columns move together,
and a short "what to do next" list. The headline names every column.
Filters: {"column", "equals" | "in": [...] | "min" | "max"}. A plan-level "filters" applies to every analysis.
Personal columns are pseudonymized before any number is made, and grouping by one is refused.
Defaults are safe, the teacher can switch them: "show_labels": true -> pseudonyms in top/bottom; "show_ids": true -> real 번호/학번 in top/bottom (plan level or per analysis;
local-only report, prints a caution, and the privacy check turns WARN instead of FAIL for those IDs).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tdata  # noqa: E402
from tdata import fmt_num, is_missing, josa, to_date, to_num  # noqa: E402

MIN_N_TEST = 5
AGG_NAME = {"mean": "평균", "sum": "합계", "median": "가운데 값", "count": "개수", "min": "가장 작은 값", "max": "가장 큰 값"}


_PII_KINDS: dict[str, str] = {}  # column -> kind of the table being analysed (set by run)
_RAW_IDS: dict[str, list] = {}  # ID-like column -> original values; filled by run ONLY when the plan says "show_ids": true (local-only report)
ID_CAUTION = "이 파일은 번호가 그대로 보여요. 밖으로 보내지 마세요 (메신저·메일·공유 링크 X)."


class PlanError(ValueError):
    pass


def _r(x, d=2):
    return None if x is None else round(float(x), d)


def _col(t: tdata.Table, name: str, pii: set[str], grouping: bool = False) -> str:
    if name not in t.data:
        raise PlanError(f"'{name}' 칸이 없어요. 있는 칸: {', '.join(t.cols)}")
    if grouping and name in pii:
        raise PlanError(f"'{name}'은(는) 개인정보 칸이라 이걸로 나누어 보지 않아요. 반·학년·분류 같은 칸을 써 주세요.")
    return name


def _rows(t: tdata.Table, filters: list[dict]) -> list[int]:
    idx = list(range(t.n))
    for f in filters or []:
        c = f["column"]
        if c not in t.data:
            raise PlanError(f"필터 칸 '{c}'이(가) 없어요")
        col = t.data[c]
        keep = []
        for i in idx:
            v = col[i]
            s = str(v).strip()
            if "equals" in f:
                d = to_date(v)
                ok = s == str(f["equals"]) or (d is not None and d.isoformat().startswith(str(f["equals"])))
            elif "in" in f:
                ok = s in [str(x) for x in f["in"]]
            else:
                x = to_num(v)
                ok = x is not None and x >= f.get("min", -math.inf) and x <= f.get("max", math.inf)
            if ok:
                keep.append(i)
        idx = keep
    return idx


def _agg(xs: list[float], how: str):
    if not xs:
        return None
    return {"mean": tdata.mean, "sum": sum, "median": tdata.median, "count": len, "min": min, "max": max}[how](xs)


def _sorted_labels(labels, mode):
    return sorted(labels, key=tdata.natural_key)


def _period(d, freq: str) -> str:
    if freq == "year":
        return f"{d.year}"
    if freq == "month":
        return f"{d.year}-{d.month:02d}"
    if freq == "week":
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"
    return d.isoformat()


def _period_label(key: str, freq: str, years: set[str]) -> str:
    if freq == "month":
        y, m = key.split("-")
        return f"{int(m)}월" if len(years) == 1 else f"{y}년 {int(m)}월"
    if freq == "year":
        return f"{key}년"
    return key


def _test(groups: dict[str, list[float]]) -> dict:
    ok = len(groups) >= 2 and all(len(g) >= MIN_N_TEST for g in groups.values())
    if not ok:
        return {"done": False, "note": "사람 수가 적은 모둠이 있어서 '의미 있는 차이'인지는 따지지 않았어요(모둠마다 5명 이상 필요)."}
    gs = list(groups.values())
    if len(gs) == 2:
        w = tdata.welch(gs[0], gs[1])
        d = tdata.mean(gs[0]) - tdata.mean(gs[1])
        pooled = math.sqrt((tdata.sd(gs[0]) ** 2 + tdata.sd(gs[1]) ** 2) / 2) or 1
        return {"done": True, "test": "welch", "p": _r(w["p"], 4), "effect_d": _r(d / pooled, 2), "significant": w["p"] < 0.05}
    a = tdata.anova(gs)
    return {"done": True, "test": "anova", "p": _r(a["p"], 4), "effect_eta2": _r(a["eta2"], 3), "significant": a["p"] < 0.05}


# ---------- analyses ----------
def a_groupby(t, p, idx, pii):
    by = _col(t, p["by"], pii, True)
    val = p.get("value")
    agg = p.get("agg", "mean" if val else "count")
    if val:
        _col(t, val, pii)
    groups: dict[str, list[float]] = OrderedDict()
    for i in idx:
        if is_missing(t.data[by][i]):
            continue
        x = to_num(t.data[val][i]) if val else 1.0
        if x is None:
            continue
        groups.setdefault(str(t.data[by][i]).strip(), []).append(x)
    if not groups:
        raise PlanError(f"'{by}' 별로 계산할 값이 없어요")
    labels = sorted(groups, key=tdata.natural_key)
    vals = {k: _agg(groups[k], agg) for k in labels}
    sort = p.get("sort", "none")
    if sort in ("desc", "asc"):
        labels.sort(key=lambda k: vals[k], reverse=(sort == "desc"))
    notes = []
    top = p.get("top")
    if top and len(labels) > top:
        keep, rest = labels[:top - 1], labels[top - 1:]
        if agg in ("sum", "count"):
            other = [x for k in rest for x in groups[k]]
            groups["기타"] = other
            vals["기타"] = _agg(other, agg)
            labels = keep + ["기타"]
            notes.append(f"작은 항목 {len(rest)}개는 '기타'로 묶었어요.")
        else:
            labels = keep
    count_unit = p.get("count_unit", "명" if not val else "개")
    unit = p.get("unit") or (count_unit if agg == "count" else tdata.guess_unit(val or "", [x for g in groups.values() for x in g]))
    ns = {k: len(groups[k]) for k in labels}
    series_name = (val + " " if val and agg != "count" else "") + AGG_NAME[agg] if agg != "count" else f"{by}별 {count_unit}"
    columns = [by, f"{series_name}({unit})" if unit else series_name, f"{count_unit if agg == 'count' else '자료 수'}"]
    rows = [[k, _r(vals[k], 2), ns[k]] for k in labels]
    if agg == "mean":
        columns += ["가운데 값", "가장 낮은 값", "가장 높은 값"]
        for r, k in zip(rows, labels):
            r += [_r(tdata.median(groups[k]), 2), _r(min(groups[k]), 2), _r(max(groups[k]), 2)]
    order = sorted(labels, key=lambda k: vals[k], reverse=True)
    allx = [x for k in labels for x in groups[k]]
    facts = {"agg": agg, "value": val or "", "by": by, "top_label": order[0], "top_value": _r(vals[order[0]]),
             "bottom_label": order[-1], "bottom_value": _r(vals[order[-1]]), "gap": _r(vals[order[0]] - vals[order[-1]]),
             "groups": len(labels), "n": len(allx), "overall": _r(_agg(allx, agg if agg != "count" else "sum")),
             "values": {k: _r(vals[k]) for k in labels}}
    if agg in ("sum", "count") and sum(vals[k] for k in labels):
        tot = sum(vals[k] for k in labels)
        facts["top_share_pct"] = _r(100 * vals[order[0]] / tot, 1)
        facts["total"] = _r(tot)
    if p.get("test") and agg == "mean":
        facts["test"] = _test({k: groups[k] for k in labels})
        if not facts["test"]["done"]:
            notes.append(facts["test"]["note"])
    if agg == "mean" and min(ns.values()) < 10:
        notes.append("사람(자료)이 10개보다 적은 모둠이 있어서, 차이는 참고만 해 주세요.")
    chart = "share" if p.get("style") == "share" and len(labels) <= 5 and agg in ("sum", "count") else ("hbar" if len(labels) > 6 else "bar")
    return {"chart": chart, "labels": labels, "series": [{"name": series_name, "values": [_r(vals[k]) for k in labels]}], "unit": unit,
            "table": {"columns": columns, "rows": rows}, "facts": facts, "notes": notes, "n": len(allx),
            "default_title": f"{by}별 {series_name}" + (f" ({unit})" if unit else ""),
            "how": f"막대가 길수록 {tdata.josa(series_name, '이/가')} 커요." if agg != "count" else "막대가 길수록 많아요."}


def a_distribution(t, p, idx, pii):
    c = _col(t, p["column"], pii)
    vals = [t.data[c][i] for i in idx if not is_missing(t.data[c][i])]
    if not vals:
        raise PlanError(f"'{c}' 칸에 값이 없어요")
    notes = []
    count_unit = p.get("count_unit", "명")
    nums = [to_num(v) for v in vals]
    numeric = all(x is not None for x in nums)
    counts: dict[str, int] = OrderedDict()
    if p.get("bins"):
        b = p["bins"]
        bl = p.get("bin_labels") or [f"{fmt_num(b[j])}~{fmt_num(b[j + 1] - (1 if b[j + 1] == int(b[j + 1]) else 0))}" for j in range(len(b) - 1)]
        for lab in bl:
            counts[lab] = 0
        for x in nums:
            if x is None:
                continue
            for j in range(len(b) - 1):
                if b[j] <= x < b[j + 1]:
                    counts[bl[j]] += 1
                    break
    else:
        cc: dict[str, int] = defaultdict(int)
        for v, x in zip(vals, nums):
            cc[str(int(x)) if numeric and float(x).is_integer() else (str(x) if numeric else str(v).strip())] += 1
        if p.get("order"):
            keys = [str(k) for k in p["order"] if str(k) in cc] + [k for k in cc if k not in [str(o) for o in p["order"]]]
        elif numeric:
            keys = sorted(cc, key=lambda s: float(s))
        else:
            keys = sorted(cc, key=lambda k: (-cc[k], tdata.natural_key(k))) if p.get("sort") == "desc" else sorted(cc, key=tdata.natural_key)
        for k in keys:
            counts[k] = cc[k]
    n = sum(counts.values())
    labels = list(counts)
    pct = {k: 100 * counts[k] / n for k in labels}
    order = sorted(labels, key=lambda k: counts[k], reverse=True)
    facts = {"column": c, "n": n, "top_label": order[0], "top_count": counts[order[0]], "top_pct": _r(pct[order[0]], 1),
             "bottom_label": order[-1], "parts": len(labels), "pct": {k: _r(pct[k], 1) for k in labels}}
    if numeric:
        facts["mean"] = _r(tdata.mean([x for x in nums if x is not None]), 2)
    sm = p.get("scale_max")
    if sm and numeric:
        facts["positive_pct"] = _r(100 * sum(1 for x in nums if x >= sm - 1) / n, 1)
        facts["scale_max"] = sm
    if n < 10:
        notes.append("응답이 10개보다 적어서 참고만 해 주세요.")
    share = len(labels) <= 5 and (p.get("style") == "share")
    return {"chart": "share" if share else "bar", "labels": labels, "series": [{"name": f"{count_unit}", "values": [counts[k] for k in labels]}],
            "unit": count_unit, "table": {"columns": [c, f"{count_unit}", "비율(%)"], "rows": [[k, counts[k], _r(pct[k], 1)] for k in labels]},
            "facts": facts, "notes": notes, "n": n, "default_title": f"{c}별 {count_unit} 수 ({count_unit})",
            "how": (f"막대가 길수록 그 점수대에 해당하는 {count_unit} 수가 많아요." if p.get("bins") else "막대가 길수록 그 답을 고른 사람이 많아요.") if not share else "조각이 클수록 차지하는 몫이 커요.", "pct": {k: _r(pct[k], 1) for k in labels}}


def a_likert(t, p, idx, pii):
    cols = [_col(t, c, pii) for c in p["columns"]]
    sm = p.get("scale_max", 5)
    lab = p.get("labels", {})
    labels, means, pos, ns = [], [], [], []
    for c in cols:
        xs = [x for i in idx for x in [to_num(t.data[c][i])] if x is not None]
        if not xs:
            raise PlanError(f"'{c}' 칸에 숫자가 없어요")
        labels.append(lab.get(c, c))
        means.append(tdata.mean(xs))
        pos.append(100 * sum(1 for x in xs if x >= sm - 1) / len(xs))
        ns.append(len(xs))
    order = sorted(range(len(cols)), key=lambda j: means[j], reverse=True)
    facts = {"scale_max": sm, "best_label": labels[order[0]], "best_mean": _r(means[order[0]], 2), "worst_label": labels[order[-1]],
             "worst_mean": _r(means[order[-1]], 2), "overall": _r(tdata.mean(means), 2), "n": max(ns),
             "positive_overall_pct": _r(tdata.mean(pos), 1), "means": {labels[j]: _r(means[j], 2) for j in range(len(cols))},
             "positive_pct": {labels[j]: _r(pos[j], 1) for j in range(len(cols))}}
    notes = []
    if max(ns) < 10:
        notes.append("응답이 10개보다 적어서 참고만 해 주세요.")
    return {"chart": "hbar", "labels": labels, "series": [{"name": f"평균 점수({sm}점 만점)", "values": [_r(m, 2) for m in means]}], "unit": "점",
            "axis_max": sm, "table": {"columns": ["질문", f"평균(점, {sm}점 만점)", f"{sm - 1}점 이상 비율(%)", "응답 수"],
                                       "rows": [[labels[j], _r(means[j], 2), _r(pos[j], 1), ns[j]] for j in range(len(cols))]},
            "facts": facts, "notes": notes, "n": max(ns), "default_title": f"질문별 평균 점수 (점, {sm}점 만점)",
            "how": f"막대가 길수록 점수가 높아요. 가장 오른쪽 끝은 {sm}점이에요."}


def a_crosstab(t, p, idx, pii):
    rc, cc = _col(t, p["rows"], pii, True), _col(t, p["cols"], pii, True)
    cnt: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for i in idx:
        a, b = t.data[rc][i], t.data[cc][i]
        if is_missing(a) or is_missing(b):
            continue
        x = to_num(b)
        cnt[str(a).strip()][str(int(x)) if x is not None and float(x).is_integer() else str(b).strip()] += 1
    rows_l = sorted(cnt, key=tdata.natural_key)
    cols_l = sorted({b for r in cnt.values() for b in r}, key=tdata.natural_key)
    if len(cols_l) > 7:
        raise PlanError(f"'{cc}' 칸의 종류가 너무 많아요({len(cols_l)}개). 7개 이하인 칸을 골라 주세요.")
    tot = {r: sum(cnt[r].values()) for r in rows_l}
    pct = {r: {c: 100 * cnt[r].get(c, 0) / tot[r] for c in cols_l} for r in rows_l}
    overall = {c: 100 * sum(cnt[r].get(c, 0) for r in rows_l) / sum(tot.values()) for c in cols_l}
    main_c = max(cols_l, key=lambda c: overall[c]) if p.get("focus_col") is None else str(p["focus_col"])
    top_row = max(rows_l, key=lambda r: pct[r][main_c])
    low_row = min(rows_l, key=lambda r: pct[r][main_c])
    notes = []
    if min(tot.values()) < 10:
        notes.append("사람 수가 10명보다 적은 칸이 있어서 비율은 참고만 해 주세요.")
    facts = {"rows": rc, "cols": cc, "focus_col": main_c, "top_row": top_row, "top_pct": _r(pct[top_row][main_c], 1),
             "low_row": low_row, "low_pct": _r(pct[low_row][main_c], 1), "overall_pct": _r(overall[main_c], 1), "n": sum(tot.values()),
             "pct": {r: {c: _r(pct[r][c], 1) for c in cols_l} for r in rows_l}}
    return {"chart": "stacked", "labels": rows_l, "series": [{"name": c, "values": [_r(pct[r][c], 1) for r in rows_l]} for c in cols_l], "unit": "%",
            "table": {"columns": [rc] + [f"{c}(%)" for c in cols_l] + ["전체(명)"], "rows": [[r] + [_r(pct[r][c], 1) for c in cols_l] + [tot[r]] for r in rows_l]},
            "facts": facts, "notes": notes, "n": sum(tot.values()), "default_title": f"{rc}별 '{cc}' 비율 (%)",
            "how": "막대 하나가 100%예요. 색 조각이 길수록 그 답이 많아요."}


def a_trend(t, p, idx, pii):
    tm = _col(t, p["time"], pii)
    val = p.get("value")
    agg = p.get("agg", "sum" if val else "count")
    freq = p.get("freq", "month")
    by = _col(t, p["by"], pii, True) if p.get("by") else None
    pts: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for i in idx:
        d = to_date(t.data[tm][i])
        if d is None:
            continue
        x = to_num(t.data[val][i]) if val else 1.0
        if x is None:
            continue
        pts[str(t.data[by][i]).strip() if by else "전체"][_period(d, freq)].append(x)
    if not pts:
        raise PlanError(f"'{tm}' 칸에서 날짜를 읽지 못했어요")
    keys = sorted({k for s in pts.values() for k in s})
    years = {k[:4] for k in keys}
    labels = [_period_label(k, freq, years) for k in keys]
    names = sorted(pts, key=lambda s: -sum(len(v) for v in pts[s].values()))[:5] if by else ["전체"]
    series = [{"name": s, "values": [_r(_agg(pts[s].get(k, []), agg)) if pts[s].get(k) else None for k in keys]} for s in names]
    unit = p.get("unit") or (tdata.guess_unit(val or "", []) if val else p.get("count_unit", "개"))
    allp = pts if not by else {"전체": defaultdict(list)}
    tot = defaultdict(list)
    for s in pts.values():
        for k, v in s.items():
            tot[k] += v
    tv = [_agg(tot[k], agg) if tot.get(k) else None for k in keys]
    nn = [v for v in tv if v is not None]
    last, first = nn[-1], nn[0]
    prev = nn[-2] if len(nn) > 1 else None
    peak_i = max(range(len(tv)), key=lambda j: -1 if tv[j] is None else tv[j])
    facts = {"agg": agg, "value": val or "", "first_label": labels[0], "first": _r(first), "last_label": labels[-1], "last": _r(last),
             "prev_label": labels[-2] if prev is not None else "", "prev": _r(prev) if prev is not None else None,
             "last_vs_prev": _r(last - prev) if prev is not None else None,
             "change": _r(last - first), "change_pct": _r(100 * (last - first) / first, 1) if first else None,
             "peak_label": labels[peak_i], "peak": _r(tv[peak_i]), "periods": len(keys), "freq": freq,
             "total": _r(sum(nn)) if agg in ("sum", "count") else None, "average": _r(tdata.mean(nn)),
             "consecutive": freq == "month" and len(keys) > 1 and _months_gap(keys[-2], keys[-1]) == 1,
             "values": {labels[j]: _r(tv[j]) for j in range(len(keys)) if tv[j] is not None}}
    if prev:
        facts["last_vs_prev_pct"] = _r(100 * (last - prev) / prev, 1)
    cols = ["기간"] + [f"{s['name']}({unit})" if unit else s["name"] for s in series]
    rows = [[labels[j]] + [s["values"][j] for s in series] for j in range(len(keys))]
    notes = []
    if len(keys) < 4:
        notes.append("기간이 짧아서(%d개) 오르내림이 일시적인지 알기 어려워요." % len(keys))
    nm = AGG_NAME[agg]
    return {"chart": "line", "labels": labels, "series": series, "unit": unit, "table": {"columns": cols, "rows": rows}, "facts": facts,
            "notes": notes, "n": sum(len(v) for s in pts.values() for v in s.values()),
            "default_title": f"{freq == 'month' and '달' or '기간'}별 {(val + ' ') if val else ''}{nm}" + (f" ({unit})" if unit else ""),
            "how": "선이 위로 가면 늘어난 거예요. 점 하나가 한 달(기간)이에요."}


def _months_gap(a: str, b: str) -> int:
    ya, ma = map(int, a.split("-")[:2])
    yb, mb = map(int, b.split("-")[:2])
    return (yb - ya) * 12 + (mb - ma)


def a_change(t, p, idx, pii):
    by = _col(t, p["by"], pii, True)
    tm = _col(t, p["time"], pii)
    val = _col(t, p["value"], pii)
    freq = p.get("freq", "month")
    per: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for i in idx:
        d, x = to_date(t.data[tm][i]), to_num(t.data[val][i])
        if d is None or x is None or is_missing(t.data[by][i]):
            continue
        per[_period(d, freq)][str(t.data[by][i]).strip()].append(x)
    keys = sorted(per)
    if len(keys) < 2:
        raise PlanError("비교할 기간이 2개 이상 필요해요")
    k0, k1 = (p.get("from") or keys[0]), (p.get("to") or keys[-1])
    years = {k[:4] for k in keys}
    l0, l1 = _period_label(k0, freq, years), _period_label(k1, freq, years)
    groups = sorted(set(per[k0]) & set(per[k1]), key=tdata.natural_key)
    m0 = {g: tdata.mean(per[k0][g]) for g in groups}
    m1 = {g: tdata.mean(per[k1][g]) for g in groups}
    all0 = [x for g in groups for x in per[k0][g]]
    all1 = [x for g in groups for x in per[k1][g]]
    diffs = {g: m1[g] - m0[g] for g in groups}
    best = max(groups, key=lambda g: diffs[g])
    focus = p.get("focus") if p.get("focus") in diffs else best
    unit = p.get("unit") or tdata.guess_unit(val, all1)
    nrows = [[g, _r(m0[g]), _r(m1[g]), _r(diffs[g]), len(per[k0][g]), len(per[k1][g])] for g in groups]
    notes = []
    if min(min(len(per[k0][g]), len(per[k1][g])) for g in groups) < 10:
        notes.append("모둠 사람이 10명보다 적어서, 오르내림은 참고만 해 주세요.")
    notes.append("같은 반의 두 번 평균을 비교한 거예요. 같은 학생이 아닐 수도 있어요.")
    facts = {"by": by, "value": val, "from_label": l0, "to_label": l1, "consecutive": freq == "month" and _months_gap(k0, k1) == 1,
             "best_label": best, "best_diff": _r(diffs[best]), "focus": focus, "focus_diff": _r(diffs[focus]),
             "focus_from": _r(m0[focus]), "focus_to": _r(m1[focus]), "overall_diff": _r(tdata.mean(all1) - tdata.mean(all0)),
             "overall_from": _r(tdata.mean(all0)), "overall_to": _r(tdata.mean(all1)), "n": len(all0) + len(all1),
             "diffs": {g: _r(diffs[g]) for g in groups}}
    return {"chart": "grouped", "labels": groups, "series": [{"name": l0, "values": [_r(m0[g]) for g in groups]}, {"name": l1, "values": [_r(m1[g]) for g in groups]}],
            "unit": unit, "table": {"columns": [by, f"{l0} 평균({unit})", f"{l1} 평균({unit})", f"바뀐 점수({unit})", f"{l0} 사람 수", f"{l1} 사람 수"], "rows": nrows},
            "facts": facts, "notes": notes, "n": len(all0) + len(all1), "default_title": f"{by}별 {val} 평균: {l0} 와 {l1} ({unit})",
            "how": "같은 반에서 앞의 막대와 뒤의 막대를 비교해요. 뒤가 길면 올랐어요."}


def a_correlation(t, p, idx, pii):
    xc, yc = _col(t, p["x"], pii), _col(t, p["y"], pii)
    pairs = [(to_num(t.data[xc][i]), to_num(t.data[yc][i])) for i in idx]
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(pairs) < 5:
        raise PlanError("짝지은 값이 5개보다 적어서 관계를 보기 어려워요")
    xs, ys = [a for a, _ in pairs], [b for _, b in pairs]
    r = tdata.pearson(xs, ys)
    n = len(pairs)
    pv = tdata.p_from_t(r * math.sqrt((n - 2) / max(1e-12, 1 - r * r)), n - 2) if abs(r) < 1 else 0.0
    nb = min(5, max(2, n // 5))
    srt = sorted(pairs)
    chunks = [srt[round(j * n / nb): round((j + 1) * n / nb)] for j in range(nb)]
    labels = [f"{fmt_num(c[0][0])}~{fmt_num(c[-1][0])}" for c in chunks]
    ym = [tdata.mean([b for _, b in c]) for c in chunks]
    ux, uy = tdata.guess_unit(xc, xs), p.get("unit") or tdata.guess_unit(yc, ys)
    strength = "거의 없음" if abs(r) < 0.2 else "약함" if abs(r) < 0.4 else "보통" if abs(r) < 0.7 else "강함"
    facts = {"x": xc, "y": yc, "r": _r(r, 2), "n": n, "strength": strength, "direction": "같이 오름" if r > 0 else "반대로 움직임", "p": _r(pv, 4),
             "significant": pv < 0.05 and n >= 10, "x_unit": ux, "y_unit": uy, "first_mean": _r(ym[0]), "last_mean": _r(ym[-1])}
    notes = ["두 가지가 함께 움직인다고 해서, 하나가 다른 하나의 '원인'이라는 뜻은 아니에요. (상관관계 ≠ 인과관계)"]
    if n < 30:
        notes.append("자료가 30개보다 적어서 참고만 해 주세요.")
    return {"chart": "bar", "labels": labels, "series": [{"name": f"{yc} 평균", "values": [_r(v) for v in ym]}], "unit": uy,
            "xlabel": f"{xc}" + (f" ({ux})" if ux else ""), "table": {"columns": [f"{xc} 구간" + (f"({ux})" if ux else ""), f"{yc} 평균" + (f"({uy})" if uy else ""), "자료 수"],
                                                                      "rows": [[labels[j], _r(ym[j]), len(chunks[j])] for j in range(nb)]},
            "facts": facts, "notes": notes, "n": n, "default_title": f"{tdata.josa(xc, '이/가')} 늘면 {tdata.josa(yc, '은/는')}? ({uy})" if uy else f"{xc}와 {yc}",
            "how": f"{xc}를 비슷한 사람끼리 5덩이로 나눠서 {yc} 평균을 보여 줘요."}


# ---------- overview: every numeric column, one go (wide tables like 국어·수학·과학) ----------
BANDS_100 = ([0, 60, 70, 80, 90, 101], ["60점 미만", "60점대", "70점대", "80점대", "90점 이상"])


def _num_cols(t, pii: set[str], wanted: list[str] | None) -> list[str]:
    if wanted:
        return [_col(t, c, pii) for c in wanted]
    out = []
    for c in t.cols:
        if c in pii:
            continue
        info = tdata.column_info(c, t.data[c])
        if info["kind"] == "number" and info["unique"] < t.n:  # an all-different integer column is an id, not a score
            out.append(c)
    return out


def _overview(t, p, idx, pii):
    """One plan line -> profile + bands + rank + matrix results, plus a short 'what next' list."""
    cols = _num_cols(t, pii, p.get("columns"))
    if not cols:
        raise PlanError("숫자 칸을 못 찾았어요. columns에 점수 칸 이름을 적어 주세요.")
    vals = {c: {i: to_num(t.data[c][i]) for i in idx if to_num(t.data[c][i]) is not None} for c in cols}
    cols = [c for c in cols if len(vals[c]) >= 3]
    if not cols:
        raise PlanError("숫자가 3개 이상 있는 칸이 없어요")
    unit = p.get("unit") or tdata.guess_unit(cols[0], list(vals[cols[0]].values())) or ("점" if all(0 <= x <= 100 for c in cols for x in vals[c].values()) else "")
    mean_ = {c: tdata.mean(list(vals[c].values())) for c in cols}
    med = {c: tdata.median(list(vals[c].values())) for c in cols}
    sdv = {c: tdata.sd(list(vals[c].values())) for c in cols}
    lo = {c: min(vals[c].values()) for c in cols}
    hi = {c: max(vals[c].values()) for c in cols}
    cnt = {c: len(vals[c]) for c in cols}
    order = sorted(cols, key=lambda c: mean_[c], reverse=True)
    spread = max(cols, key=lambda c: sdv[c])
    overall = tdata.mean([mean_[c] for c in cols])
    pf = {"subjects": cols, "n_subjects": len(cols), "means": {c: _r(mean_[c]) for c in cols}, "top_label": order[0], "top_value": _r(mean_[order[0]]),
          "bottom_label": order[-1], "bottom_value": _r(mean_[order[-1]]), "gap": _r(mean_[order[0]] - mean_[order[-1]]), "overall": _r(overall),
          "spread_label": spread, "spread_value": _r(sdv[spread]), "n": max(cnt.values()), "unit": unit}
    profile = {"chart": "bar", "labels": cols, "series": [{"name": "평균", "values": [_r(mean_[c]) for c in cols]}], "unit": unit,
               "table": {"columns": ["칸", f"평균({unit})" if unit else "평균", "가운데 값", "흩어진 정도(표준편차)", "가장 낮은 값", "가장 높은 값", "자료 수"],
                         "rows": [[c, _r(mean_[c]), _r(med[c]), _r(sdv[c]), _r(lo[c], 2), _r(hi[c], 2), cnt[c]] for c in cols]},
               "facts": pf, "notes": [], "n": pf["n"], "default_title": "과목별 평균" + (f" ({unit})" if unit else ""),
               "how": "막대가 길수록 평균이 높아요."}
    results = [("profile", profile)]
    # distribution: how many in each band, per column
    allv = [x for c in cols for x in vals[c].values()]
    if p.get("bins"):
        bins, blabels = p["bins"], p.get("bin_labels") or [f"{fmt_num(a)}~{fmt_num(b)}" for a, b in zip(p["bins"], p["bins"][1:])]
    elif min(allv) >= 0 and max(allv) <= 100:
        bins, blabels = BANDS_100
    else:
        lo_, hi_ = min(allv), max(allv)
        step = (hi_ - lo_) / 5 or 1
        bins = [lo_ + step * k for k in range(5)] + [hi_ + 1e-9]
        blabels = [f"{fmt_num(bins[k])}~{fmt_num(bins[k + 1] if k < 4 else hi_)}" for k in range(5)]
    counts = {c: [sum(1 for x in vals[c].values() if a <= x < b) for a, b in zip(bins, bins[1:])] for c in cols}
    low_n = {c: counts[c][0] for c in cols}
    top_band = {c: blabels[max(range(len(blabels)), key=lambda k: counts[c][k])] for c in cols}
    bf = {"bands": blabels, "counts": counts, "low_label": blabels[0], "low_counts": low_n, "low_total": sum(low_n.values()), "low_worst": max(cols, key=lambda c: low_n[c]),
          "top_bands": top_band, "n": max(cnt.values()), "subjects": cols}
    results.append(("bands", {"chart": "grouped", "labels": blabels, "series": [{"name": c, "values": counts[c]} for c in cols], "unit": "명",
                              "table": {"columns": ["점수대"] + [f"{c}(명)" for c in cols], "rows": [[blabels[k]] + [counts[c][k] for c in cols] for k in range(len(blabels))]},
                              "facts": bf, "notes": [], "n": bf["n"], "default_title": "점수대별 학생 수 (명)", "how": "과목마다 점수대별로 몇 명인지 막대로 보여 줘요."}))
    # rank: top and bottom units (groups if a group column is given, else rows with pseudonyms)
    gcol = p.get("group")
    if gcol:
        _col(t, gcol, pii, True)
    # Individual students are shown as anonymous ranks (상위 1위 ...) by default: no name, no pseudonym number, never an ID-like column (번호, 학번, id).
    # plan "show_labels": true shows the pseudonym (학생01) of a name / already-pseudonymous column.
    # plan "show_ids": true (the teacher asked to see 번호/학번) shows the real ID values: for local-only reports, with a caution (the AI still never reads the rows).
    name_col = None
    id_col = next(iter(_RAW_IDS), None) if (not gcol and p.get("show_ids")) else None
    if not gcol and not id_col and p.get("show_labels"):
        name_col = next((c for c in t.cols if c in pii and _PII_KINDS.get(c) in ("name", "pseudonym")), None)
    keycol = gcol or name_col
    units: dict[str, list[float]] = OrderedDict()
    rows_of: dict[str, list[int]] = {}
    for i in idx:
        xs = [vals[c][i] for c in cols if i in vals[c]]
        if not xs:
            continue
        if id_col:
            key = f"{id_col} {str(_RAW_IDS[id_col][i]).strip()}"
        else:
            key = str(t.data[keycol][i]).strip() if keycol else f"{len(units) + 1}번째 줄"
        units.setdefault(key, []).append(tdata.mean(xs))
        rows_of.setdefault(key, []).append(i)
    um = {k: tdata.mean(v) for k, v in units.items()}
    ranked = sorted(um, key=lambda k: um[k], reverse=True)
    show_n = 3 if len(ranked) > 6 else max(1, len(ranked) // 2)
    pick = ranked[:show_n] + [k for k in ranked[-show_n:] if k not in ranked[:show_n]]
    weakest = {k: min(cols, key=lambda c: tdata.mean([vals[c][i] for i in rows_of[k] if i in vals[c]] or [1e9])) for k in pick}
    what = "모둠" if gcol else "학생"
    if gcol or name_col or id_col:
        disp = {k: k for k in ranked}
    else:  # anonymous: rank only
        disp = {}
        for pos, k in enumerate(ranked):
            disp[k] = f"상위 {pos + 1}위" if pos < show_n else (f"하위 {len(ranked) - pos}위" if pos >= len(ranked) - show_n else k)
    hidden = not (gcol or name_col or id_col)
    rf = {"kind": what, "n_units": len(ranked), "show_n": show_n, "top": [[disp[k], _r(um[k])] for k in ranked[:show_n]], "bottom": [[disp[k], _r(um[k])] for k in ranked[-show_n:]], "hidden": hidden,
          "top_label": disp[ranked[0]], "top_value": _r(um[ranked[0]]), "bottom_label": disp[ranked[-1]], "bottom_value": _r(um[ranked[-1]]), "gap": _r(um[ranked[0]] - um[ranked[-1]]), "n": len(ranked)}
    rnotes = ["이름과 번호는 보이지 않게 하고 순위로만 보여 드려요. (가명으로 보고 싶으면 말씀해 주세요)"] if hidden else ([ID_CAUTION] if id_col else [])
    results.append(("rank", {"chart": "hbar", "labels": [disp[k] for k in pick], "series": [{"name": "과목 평균", "values": [_r(um[k]) for k in pick]}], "unit": unit or "평균",
                             "table": {"columns": [("순위" if hidden else what + ("(가명)" if name_col else "(번호)" if id_col else "")), f"과목 평균({unit})" if unit else "과목 평균", "가장 낮은 과목"],
                                       "rows": [[disp[k], _r(um[k]), weakest.get(k, "")] for k in pick]},
                             "facts": rf, "notes": rnotes, "n": len(ranked), "default_title": f"과목 평균이 높은 {what}·낮은 {what} (" + (unit or "평균") + ")",
                             "how": f"전체 {what} 중 가장 높은 쪽과 낮은 쪽만 골라 보여 줘요."}))
    # correlation between every pair of columns
    pairs = []
    for a in range(len(cols)):
        for b in range(a + 1, len(cols)):
            ca, cb = cols[a], cols[b]
            both = [i for i in vals[ca] if i in vals[cb]]
            if len(both) >= 5:
                pairs.append((ca, cb, tdata.pearson([vals[ca][i] for i in both], [vals[cb][i] for i in both]), len(both)))
    mf = {}
    if pairs:
        pairs.sort(key=lambda x: -abs(x[2]))
        pairs = pairs[:10]
        top = pairs[0]
        stg = lambda r_: "거의 없음" if abs(r_) < 0.2 else "약함" if abs(r_) < 0.4 else "보통" if abs(r_) < 0.7 else "강함"
        mf = {"pairs": {f"{a}·{b}": _r(r_, 2) for a, b, r_, _ in pairs}, "top_pair": f"{top[0]}·{top[1]}", "top_a": top[0], "top_b": top[1], "top_r": _r(top[2], 2),
              "top_strength": stg(top[2]), "top_direction": "같이 오름" if top[2] > 0 else "반대로 움직임", "weak_pair": f"{pairs[-1][0]}·{pairs[-1][1]}",
              "weak_r": _r(pairs[-1][2], 2), "n_pairs": len(pairs), "n": top[3]}
        results.append(("matrix", {"chart": "bar", "labels": [f"{a}·{b}" for a, b, _, _ in pairs], "series": [{"name": "함께 움직이는 정도", "values": [_r(r_, 2) for _, _, r_, _ in pairs]}],
                                   "unit": "함께 움직이는 정도", "axis_max": 1,
                                   "table": {"columns": ["두 과목", "함께 움직이는 정도(상관계수)", "세기", "자료 수"], "rows": [[f"{a}·{b}", _r(r_, 2), stg(r_), n_] for a, b, r_, n_ in pairs]},
                                   "facts": mf, "notes": ["함께 움직인다고 해서 한쪽이 원인이라는 뜻은 아니에요. (상관관계 ≠ 인과관계)"] + (["자료가 30개보다 적어서 참고만 해 주세요."] if top[3] < 30 else []),
                                   "n": top[3], "default_title": "과목끼리 함께 움직이는 정도 (함께 움직이는 정도)",
                                   "how": "막대가 길수록 두 과목 점수가 비슷하게 오르내려요. 1에 가까우면 거의 같이 움직여요."}))
    # what to do next: short, from the numbers above only
    if len(cols) > 1:
        nxt = [f"{josa(order[-1], '은/는')} 평균이 {fmt_num(pf['bottom_value'], unit)}으로 가장 낮아요. 이 과목 복습을 먼저 해 보세요."]
    else:
        nxt = [f"{josa(cols[0], '은/는')} 평균이 {fmt_num(pf['top_value'], unit)}이에요."]
    if bf["low_total"]:
        nxt.append(f"{bf['low_label']}인 학생은 {josa(bf['low_worst'], '이/가')} 가장 많은 {bf['low_counts'][bf['low_worst']]}명이에요. 이 친구들을 먼저 도와 주세요.")
    if len(cols) > 1 and spread != order[-1]:
        nxt.append(f"{josa(spread, '은/는')} 점수 차이가 크게 벌어져 있어요. 수준에 맞는 활동을 나눠 보세요.")
    if mf:
        nxt.append(f"{josa(mf['top_a'], '과/와')} {josa(mf['top_b'], '은/는')} 함께 오르내리는 편이에요. 같이 공부하는 활동이 도움이 돼요." if mf["top_strength"] in ("보통", "강함") and mf["top_r"] > 0
                   else "과목끼리 점수가 크게 얽혀 있지 않아요. 과목마다 따로 살펴보세요.")
    nxt.append("다음 시험 뒤에 같은 방법으로 다시 보면, 얼마나 달라졌는지 알 수 있어요.")
    return results, nxt[:5]


HANDLERS = {"groupby": a_groupby, "distribution": a_distribution, "likert": a_likert, "crosstab": a_crosstab, "trend": a_trend,
            "change": a_change, "correlation": a_correlation}


def run(table: tdata.Table, plan: dict, pii_report: dict | None = None) -> dict:
    safe, rep = (table, pii_report) if pii_report is not None else tdata.prepare(table)
    pii = {c["column"] for c in rep["pii_columns"]}
    _PII_KINDS.clear()
    _PII_KINDS.update({c["column"]: c["kind"] for c in rep["pii_columns"]})
    _RAW_IDS.clear()
    shows_ids = bool(plan.get("show_ids")) or any(a.get("show_ids") for a in plan.get("analyses", []))
    if shows_ids:  # the teacher asked to see numbers (번호/학번): take them from the ORIGINAL table, for a local-only report
        _RAW_IDS.update({c["column"]: list(table.data[c["column"]]) for c in rep["pii_columns"] if c["kind"] == "student_id"})
        shows_ids = bool(_RAW_IDS)
    base = _rows(safe, plan.get("filters", []))
    results, next_steps = [], []
    for k, a in enumerate(plan.get("analyses", []), 1):
        if a.get("type") == "overview":
            idx0 = _rows(safe, a.get("filter", [])) if a.get("filter") else base
            if a.get("filter") and plan.get("filters"):
                idx0 = [i for i in idx0 if i in set(base)]
            if plan.get("show_ids"):
                a = dict(a, show_ids=True)
            ov, nxt_ = _overview(safe, a, idx0, pii)
            base_id = a.get("id", f"a{k}")
            for sub, res in ov:
                res.update(id=f"{base_id}-{sub}" if sub != "profile" else base_id, type=sub, title=a.get("title") if (sub == "profile" and a.get("title")) else res.pop("default_title"))
                res.pop("default_title", None)
                res["unit"] = res.get("unit", "")
                res["metric"] = ""
                results.append(res)
            next_steps += nxt_
            continue
        h = HANDLERS.get(a.get("type"))
        if not h:
            raise PlanError(f"모르는 분석 종류: {a.get('type')} (쓸 수 있는 것: {', '.join(HANDLERS)})")
        idx = _rows(safe, a.get("filter", [])) if a.get("filter") else base
        if a.get("filter") and plan.get("filters"):
            idx = [i for i in idx if i in set(base)]
        res = h(safe, a, idx, pii)
        res.update(id=a.get("id", f"a{k}"), type=a["type"], title=a.get("title") or res.pop("default_title"))
        res.pop("default_title", None)
        if a.get("chart"):
            res["chart"] = a["chart"]
        res["unit"] = res.get("unit", "")
        res["metric"] = a.get("metric", "")
        results.append(res)
    return {"title": plan.get("title", "자료 분석"), "audience": plan.get("audience", "학부모"), "subject": plan.get("subject", ""),
            "narrative": plan.get("narrative"), "headline_of": plan.get("headline_of"), "next_steps": next_steps,
            "meta": {"rows": safe.n, "pseudonymized": rep["pseudonymized"], "pii_columns": [c["label"] for c in rep["pii_columns"]],
                     "warning": rep.get("warning", ""), "columns": len(safe.cols),
                     **({"shows_ids": True, "caution": ID_CAUTION} if shows_ids else {})},
            "results": results}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sheet")
    ap.add_argument("--yes", action="store_true", help="install openpyxl for .xlsx if missing")
    a = ap.parse_args()
    try:
        t = tdata.load(a.data, a.sheet, a.yes)
        plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
        out = run(t, plan)
    except tdata.NeedInstall as e:
        print(json.dumps({"need_install": e.name, "prompt": e.prompt}, ensure_ascii=False))
        return 2
    except (PlanError, FileNotFoundError, ValueError, KeyError) as e:
        print(f"FAIL {e}")
        return 1
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    if out["meta"]["warning"]:
        print("WARN " + out["meta"]["warning"], file=sys.stderr)
    print(f"OK {len(out['results'])}개 분석 -> {a.out} (집계 숫자만 저장, 원본 줄은 없음)")
    for r in out["results"]:
        print(f" - {r['id']} {r['type']}: {r['title']} / 자료 {r['n']}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
