#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Shared helpers for teacher-data: read a table, guess column types, find + hide personal data, small statistics.

Everything here runs on the teacher's computer. Standard library only for CSV; .xlsx needs openpyxl (asked first via ensure.py).
The original file is only ever read. Personal-data columns are replaced by pseudonyms in memory before anything is analysed or shown.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import math
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SHARED = SKILL / "shared" if (SKILL / "shared" / "design").is_dir() else SKILL.parent.parent / "shared"
for _p in (SHARED / "tools", SHARED / "design", SHARED / "fonts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

MISSING = {"", "-", "--", "na", "n/a", "null", "none", "nan", "해당없음", "무응답"}
UNITS = r"(?:점|원|명|%|개|회|분|시간|cm|kg|번|건|일|권|km|m|세|살)"
PII_WARNING = "학생 이름이 보여요. 가명으로 바꿔서 분석할게요"


class NeedInstall(Exception):
    """Raised when a tool is missing; .prompt is plain Korean to ask the teacher."""

    def __init__(self, prompt: str, name: str):
        super().__init__(prompt)
        self.prompt, self.name = prompt, name


class Table:
    """Columns as lists; rows are positions. Values are raw (str for csv, python objects for xlsx)."""

    def __init__(self, cols: list[str], data: dict[str, list]):
        self.cols, self.data = cols, data
        self.n = len(data[cols[0]]) if cols else 0

    def copy(self) -> "Table":
        return Table(list(self.cols), {c: list(v) for c, v in self.data.items()})


# ---------- reading ----------
def _dedupe(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for i, n in enumerate(names):
        n = (str(n) if n is not None else "").strip() or f"열{i + 1}"
        if n in seen:
            seen[n] += 1
            n = f"{n}_{seen[n]}"
        else:
            seen[n] = 1
        out.append(n)
    return out


def _from_rows(rows: list[list]) -> Table:
    rows = [r for r in rows if any(str(c).strip() != "" for c in r if c is not None)]
    if not rows:
        return Table([], {})
    cols = _dedupe(rows[0])
    w = len(cols)
    data = {c: [] for c in cols}
    for r in rows[1:]:
        r = list(r) + [""] * (w - len(r))
        for c, v in zip(cols, r[:w]):
            data[c].append(v.strip() if isinstance(v, str) else v)
    return Table(cols, data)


def read_csv(path: Path) -> Table:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    head = text[:4096]
    delim = max([",", ";", "\t"], key=lambda d: head.count(d))
    return _from_rows(list(csv.reader(io.StringIO(text), delimiter=delim)))


def read_xlsx(path: Path, sheet: str | None = None, consent: bool = False) -> Table:
    try:
        import openpyxl
    except ImportError:
        import ensure
        res = ensure.ensure("openpyxl", consent=consent)
        if not res["ok"]:
            raise NeedInstall(res["prompt"], "openpyxl")
        import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return _from_rows(rows)


def load(path: str | Path, sheet: str | None = None, consent: bool = False) -> Table:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"파일이 없어요: {p.name}")
    if p.suffix.lower() in (".xlsx", ".xlsm"):
        return read_xlsx(p, sheet, consent)
    if p.suffix.lower() == ".xls":
        raise ValueError("옛날 엑셀(.xls)은 읽지 못해요. 엑셀에서 '다른 이름으로 저장 > .xlsx 또는 .csv'로 저장해 주세요.")
    return read_csv(p)


# ---------- values ----------
def is_missing(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return isinstance(v, str) and v.strip().lower() in MISSING


_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?" + UNITS + "?")


def to_num(v):
    if is_missing(v) or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return None
    s = str(v).strip().replace(",", "").replace(" ", "")
    if not _NUM_RE.fullmatch(s):
        return None
    return float(re.match(r"[-+]?\d+(?:\.\d+)?", s).group(0))


_DATE_RE = re.compile(r"^((?:19|20)\d{2})[-./](\d{1,2})(?:[-./](\d{1,2}))?(?:[ T].*)?$")


def to_date(v):
    if is_missing(v):
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    m = _DATE_RE.match(str(v).strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


def natural_key(s: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(s))]


def guess_unit(header: str, vals: list[float]) -> str:
    h = header.lower()
    table = [("%", ("%", "비율", "퍼센트", "율")), ("원", ("원", "금액", "매출", "지출", "수입", "가격", "비용", "용돈", "잔액")),
             ("점", ("점수", "점", "성적", "만족", "score")), ("명", ("인원", "학생수", "명수")), ("시간", ("시간",)),
             ("분", ("분",)), ("cm", ("키", "신장", "cm")), ("kg", ("몸무게", "체중", "kg")), ("개", ("개수", "수량", "갯수"))]
    for unit, keys in table:
        if any(k in h for k in keys):
            return unit
    if vals and all(float(x).is_integer() and 1 <= x <= 5 for x in vals):
        return "점"
    return ""


# ---------- column types ----------
def column_info(name: str, vals: list) -> dict:
    present = [v for v in vals if not is_missing(v)]
    n = len(vals)
    info = {"name": name, "missing": n - len(present), "missing_pct": round(100 * (n - len(present)) / n, 1) if n else 0.0,
            "unique": len({str(v) for v in present})}
    if not present:
        info["kind"] = "empty"
        return info
    nums = [to_num(v) for v in present]
    dates = [to_date(v) for v in present]
    if sum(d is not None for d in dates) >= 0.9 * len(present) and sum(x is not None for x in nums if x is not None and x > 3000) == 0:
        info["kind"] = "date"
        ds = sorted(d for d in dates if d)
        info.update(first=ds[0].isoformat(), last=ds[-1].isoformat())
        return info
    if sum(x is not None for x in nums) >= 0.9 * len(present):
        xs = [x for x in nums if x is not None]
        info["kind"] = "number"
        info["unit"] = guess_unit(name, xs)
        info["integer_scale"] = all(x.is_integer() for x in xs) and len(set(xs)) <= 10
        info.update(min=min(xs), max=max(xs), mean=round(sum(xs) / len(xs), 2))
        return info
    strs = [str(v) for v in present]
    avg_len = sum(len(s) for s in strs) / len(strs)
    ratio = len(set(strs)) / len(strs)
    if avg_len >= 14 and ratio > 0.5:
        info["kind"] = "text"
        info["avg_len"] = round(avg_len, 1)
    elif ratio > 0.8 and len(strs) > 15:
        info["kind"] = "id_or_text"
    else:
        info["kind"] = "category"
    return info


# ---------- personal data ----------
RE_PHONE = re.compile(r"(?<!\d)01[016-9][-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RE_RRN = re.compile(r"(?<!\d)\d{6}[-\s]?[1-4]\d{6}(?!\d)")
HEADER_PII = [("name", r"(이름|성명|학생명|보호자명|작성자|응답자명|^name$|_name$|^name_)"),
              ("phone", r"(전화|연락처|휴대|핸드폰|폰번호|phone|mobile|^tel)"),
              ("email", r"(이메일|e-?mail|메일)"),
              ("rrn", r"(주민|rrn|생년월일|birth)"),
              ("student_id", r"(학번|student.?id|사번|학생번호)"),
              ("address", r"(주소|address)")]
PII_LABEL = {"name": "이름", "phone": "전화번호", "email": "이메일", "rrn": "주민번호·생년월일", "student_id": "학번", "address": "주소"}


def detect_pii(t: Table) -> dict[str, str]:
    """column -> kind. Header words first, then value patterns (phone/email/rrn) and name-like unique Korean 2-4 letter values."""
    found: dict[str, str] = {}
    for c in t.cols:
        h = c.strip().lower()
        kind = next((k for k, rx in HEADER_PII if re.search(rx, h)), None)
        vals = [str(v) for v in t.data[c] if not is_missing(v)]
        if kind is None and vals:
            for k, rx in (("phone", RE_PHONE), ("email", RE_EMAIL), ("rrn", RE_RRN)):
                if sum(bool(rx.search(v)) for v in vals) >= 0.6 * len(vals):
                    kind = k
                    break
        if kind is None and len(vals) >= 8:
            nm = sum(bool(re.fullmatch(r"[가-힣]{2,4}", v)) for v in vals)
            if nm >= 0.85 * len(vals) and len(set(vals)) / len(vals) >= 0.6:
                kind = "name"
        if kind:
            found[c] = kind
    return found


def pseudonymize(t: Table, pii: dict[str, str]) -> tuple[Table, dict[str, dict[str, str]]]:
    """Copy of the table where personal columns are replaced (names -> 학생01.., ids -> ID001.., contact/address -> 가림).
    Free-text columns also get known names, phones and emails masked. The mapping lives only in memory."""
    out = t.copy()
    maps: dict[str, dict[str, str]] = {}
    for c, kind in pii.items():
        m: dict[str, str] = {}
        width = max(2, len(str(max(1, len({str(v) for v in t.data[c]})))))
        for i, v in enumerate(t.data[c]):
            if is_missing(v):
                continue
            key = str(v).strip()
            if kind in ("name", "student_id"):
                if key not in m:
                    m[key] = ("학생" if kind == "name" else "ID") + str(len(m) + 1).zfill(width)
                out.data[c][i] = m[key]
            else:
                out.data[c][i] = "(가림)"
        maps[c] = m
    names = sorted({k for c, k in ((c, k) for c, mm in maps.items() if pii[c] == "name" for k in mm)}, key=len, reverse=True)
    for c in out.cols:
        if c in pii:
            continue
        for i, v in enumerate(out.data[c]):
            if isinstance(v, str) and v:
                s = RE_EMAIL.sub("(가림)", RE_PHONE.sub("(가림)", RE_RRN.sub("(가림)", v)))
                for nm in names:
                    if nm in s:
                        s = s.replace(nm, "(이름)")
                out.data[c][i] = s
    return out, maps


def prepare(t: Table) -> tuple[Table, dict]:
    """Detect + pseudonymize. Returns (safe table, report)."""
    pii = detect_pii(t)
    safe, _ = pseudonymize(t, pii) if pii else (t, {})
    rep = {"pii_columns": [{"column": c, "kind": k, "label": PII_LABEL[k]} for c, k in pii.items()], "pseudonymized": bool(pii)}
    rep["warning"] = PII_WARNING if any(k == "name" for k in pii.values()) else (
        "개인정보(전화번호·이메일 등)가 보여요. 가려서 분석할게요" if pii else "")
    return safe, rep


def scrub_text(s: str, limit: int = 14) -> str:
    s = RE_EMAIL.sub("(가림)", RE_PHONE.sub("(가림)", RE_RRN.sub("(가림)", str(s))))
    return s if len(s) <= limit else s[:limit] + "…"


# ---------- statistics ----------
def mean(xs):
    return sum(xs) / len(xs)


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def sd(xs):
    n = len(xs)
    if n < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def pearson(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def _betacf(a, b, x):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 3e-12:
            break
    return h


def betainc(a, b, x):
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def p_from_t(t, df):
    return betainc(df / 2, 0.5, df / (df + t * t)) if df > 0 else 1.0


def welch(a, b):
    na, nb = len(a), len(b)
    va, vb = sd(a) ** 2 / na, sd(b) ** 2 / nb
    if va + vb == 0:
        return {"t": 0.0, "df": na + nb - 2, "p": 1.0}
    t = (mean(a) - mean(b)) / math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (na - 1) + vb ** 2 / (nb - 1))
    return {"t": t, "df": df, "p": p_from_t(t, df)}


def anova(groups):
    allx = [x for g in groups for x in g]
    n, k = len(allx), len(groups)
    gm = mean(allx)
    ssb = sum(len(g) * (mean(g) - gm) ** 2 for g in groups)
    ssw = sum((x - mean(g)) ** 2 for g in groups for x in g)
    d1, d2 = k - 1, n - k
    if ssw == 0 or d2 <= 0:
        return {"F": 0.0, "p": 1.0, "eta2": 0.0}
    f = (ssb / d1) / (ssw / d2)
    return {"F": f, "p": betainc(d2 / 2, d1 / 2, d2 / (d2 + d1 * f)), "eta2": ssb / (ssb + ssw)}


# ---------- Korean text ----------
def _has_batchim(ch: str) -> tuple[bool, bool]:
    """(has final consonant, final is ㄹ)."""
    if "가" <= ch <= "힣":
        j = (ord(ch) - 0xAC00) % 28
        return j != 0, j == 8
    if ch.lower() in "lmnr":
        return True, ch.lower() == "l"
    return False, False


def josa(word: str, kind: str) -> str:
    """word + 이/가, 은/는, 을/를, 으로/로, 과/와 chosen by the last sound."""
    w = str(word).rstrip(")] ")
    ch = w[-1] if w else ""
    digit_cons = {"0": True, "1": True, "2": False, "3": True, "4": False, "5": False, "6": True, "7": True, "8": True, "9": False}
    if ch.isdigit():
        b, rieul = digit_cons[ch], ch in "178"
    else:
        b, rieul = _has_batchim(ch)
    pair = {"이/가": ("이", "가"), "은/는": ("은", "는"), "을/를": ("을", "를"), "과/와": ("과", "와"), "으로/로": ("으로", "로")}[kind]
    if kind == "으로/로":
        return word + (pair[1] if (not b or rieul) else pair[0])
    return word + (pair[0] if b else pair[1])


def fmt_num(v: float, unit: str = "", decimals: int | None = None) -> str:
    """Rounded, kid-readable number with its unit: 78.4점, 12,300원, 5명."""
    if v is None:
        return "-"
    a = abs(v)
    if decimals is None:
        decimals = 0 if (a >= 1000 or float(v).is_integer()) else (1 if a >= 1 or a == 0 else 2)
    s = f"{v:,.{decimals}f}"
    if decimals and "." in s:
        s = s.rstrip("0").rstrip(".")
    return s + unit
