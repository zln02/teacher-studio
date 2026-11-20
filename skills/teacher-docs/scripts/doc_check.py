#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""One gate for every document (HWPX / DOCX / PDF / HTML, or the doc spec JSON):

  placeholders  [학교명] 20XX OO 000 ... (shared placeholders.py; FAIL unless listed in fillins / template_blanks)
  privacy       주민등록번호 FAIL · 휴대전화 / 전자우편 / 「성명: 홍길동」 / 「3학년 2반 15번」 WARN
  공문 format   item marks in order (1. 가. 1) 가) (1) (가) ① ㉮), single-item mark, 끝 with two spaces, 붙임 without colon,
                수신/제목 lines, dates 2026. 11. 19., 24-hour time        (--kind gongmun, or auto when 수신+제목 are found)
  spacing       a few safe 띄어쓰기 rules (할 수, 하는 것, 그동안, 방과 후, 50% 이상 ...), WARN only - never rewrites
  opens         HWPX structure (mimetype first+stored, XML parses, every charPr/paraPr/borderFill reference exists), DOCX/PDF reopen
  fonts         HWPX/DOCX fonts are common Korean fonts; PDF fonts embedded; HTML fonts embedded

    py doc_check.py file.hwpx [--kind gongmun] [--fillins 학교명,전화] [--allow-blanks] [--json]
Exit 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
for _p in (SKILL / "shared" / "tools", SKILL.parent.parent / "shared" / "tools", SKILL.parent / "teacher-slides" / "scripts"):
    if (_p / "placeholders.py").exists():
        sys.path.insert(0, str(_p))
        break
sys.path.insert(0, str(HERE))
import placeholders as ph  # noqa: E402

COMMON_FONTS = ("함초롬바탕", "함초롬돋움", "한컴바탕", "한컴돋움", "맑은 고딕", "Malgun Gothic", "바탕", "Batang", "돋움", "Dotum", "굴림", "Gulim", "궁서",
                "나눔고딕", "NanumGothic", "나눔명조", "NanumMyeongjo", "휴먼명조", "HY헤드라인M", "Noto Sans KR", "Noto Serif KR", "Calibri", "Arial",
                "Times New Roman", "Cambria", "Symbol")

# ---------------------------------------------------------------------------------------------------------- text extraction


def texts_of(path: Path) -> list[str]:
    suf = path.suffix.lower()
    if suf == ".hwpx":
        import hwpx_edit
        return hwpx_edit.text(path)
    if suf == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        out = []
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
            out.append("".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", p)))
        import html as _h
        return [_h.unescape(t) for t in out]
    if suf == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return []
        return [ln.replace("\xa0", " ") for pg in PdfReader(str(path)).pages for ln in (pg.extract_text() or "").split("\n")]
    if suf in (".html", ".htm"):
        h = path.read_text(encoding="utf-8")
        h = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
        h = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>", "\n", h)
        import html as _h
        return [_h.unescape(re.sub(r"<[^>]+>", "", ln)).strip() for ln in h.split("\n")]
    if suf == ".json":
        import docmodel
        return docmodel.plain_lines(docmodel.build(json.loads(path.read_text(encoding="utf-8"))))
    return path.read_text(encoding="utf-8", errors="replace").split("\n")


# ---------------------------------------------------------------------------------------------------------- checks
RRN = re.compile(r"(?<!\d)\d{6}\s?-\s?[1-4]\d{6}(?!\d)")
MOBILE = re.compile(r"(?<!\d)01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NAMED = re.compile(r"(?:성명|이름|학생명|보호자명|학생\s*이름)\s*[:：]\s*([가-힣]{2,4})(?![가-힣])")
STUDENT_ID = re.compile(r"\d\s*학년\s*\d{1,2}\s*반\s*\d{1,2}\s*번")


def check_privacy(lines: list[str]) -> list[tuple[str, str]]:
    res = []
    txt = "\n".join(lines)
    r = RRN.findall(txt)
    res.append(("FAIL" if r else "PASS", "주민등록번호 형식 없음" + (f": {len(r)}개 발견 -> 지우세요" if r else "")))
    m = [x for x in MOBILE.findall(txt) if not re.fullmatch(r"[0-9\-. ]*0000[0-9\-. ]*", x)]
    if m:
        res.append(("WARN", f"휴대전화 번호 {len(m)}개: 개인 번호면 학교 대표 번호로 바꾸세요 ({m[0][:4]}…)"))
    e = EMAIL.findall(txt)
    if e:
        res.append(("WARN", f"전자우편 주소 {len(e)}개: 공용 주소인지 확인하세요"))
    n = NAMED.findall(txt)
    if n:
        res.append(("WARN", f"이름이 적힌 칸 {len(n)}개 ('{n[0][0]}○○'): 학생·보호자 실명은 빼거나 가리세요"))
    s = STUDENT_ID.findall(txt)
    if s:
        res.append(("WARN", f"학년·반·번호 {len(s)}곳: 학생을 알아볼 수 있는 정보예요"))
    return res


GANA = "가나다라마바사아자차카타파하"
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
CIRC_GA = "㉮㉯㉰㉱㉲㉳㉴㉵㉶㉷㉸㉹㉺㉻"
MARKS = [
    (re.compile(r"^(\d{1,2})\.\s"), lambda g: int(g) - 1),
    (re.compile(r"^([가-하])\.\s"), lambda g: GANA.index(g)),
    (re.compile(r"^(\d{1,2})\)\s"), lambda g: int(g) - 1),
    (re.compile(r"^([가-하])\)\s"), lambda g: GANA.index(g)),
    (re.compile(r"^\((\d{1,2})\)\s"), lambda g: int(g) - 1),
    (re.compile(r"^\(([가-하])\)\s"), lambda g: GANA.index(g)),
    (re.compile(r"^([①-⑮])\s"), lambda g: CIRC.index(g)),
    (re.compile(r"^([㉮-㉻])\s"), lambda g: CIRC_GA.index(g)),
]
SYMS = ["1.", "가.", "1)", "가)", "(1)", "(가)", "①", "㉮"]


def mark_of(line: str):
    s = line.strip()
    for lv, (rx, idx) in enumerate(MARKS):
        m = rx.match(s)
        if m:
            g = m.group(1)
            if lv in (1, 3, 5) and g not in GANA:
                return None
            return lv, idx(g)
    return None


def check_gongmun(lines: list[str], lenient_space: bool = False) -> list[tuple[str, str]]:
    res = []
    L = [ln.rstrip() for ln in lines]
    has_recv = any(re.match(r"^\s*수신\s", ln) or ln.strip() == "수신" for ln in L)
    has_title = any(re.match(r"^\s*제목\s", ln) for ln in L)
    res.append(("PASS" if has_recv and has_title else "WARN", "수신·제목 줄" + ("" if has_recv and has_title else ": 공문은 「수신」과 「제목」 줄이 있어야 해요")))
    probs = []
    stack: list[list[int]] = []  # [level, last index]
    in_att = False
    for ln in L:
        s = ln.strip()
        if s.startswith("붙임"):
            in_att = True
            continue
        if in_att or not s:
            continue
        m = mark_of(s)
        if not m:
            continue
        lv, ix = m
        while stack and stack[-1][0] > lv:
            stack.pop()
        if stack and stack[-1][0] == lv:
            if ix != stack[-1][1] + 1:
                probs.append(f"'{s[:12]}' 앞 번호 다음은 {SYMS[lv].replace('1', str(stack[-1][1] + 2)) if lv in (0, 2, 4) else '다음 기호'}")
            stack[-1][1] = ix
        else:
            parent = stack[-1][0] if stack else -1
            if lv != parent + 1:
                probs.append(f"'{s[:12]}': {SYMS[parent + 1] if parent + 1 < 8 else ''} 단계를 건너뛰었어요 (1. → 가. → 1) → 가) → (1) → (가) → ① → ㉮)")
            if ix != 0:
                probs.append(f"'{s[:12]}': 새 단계는 {SYMS[lv]}부터 시작해요")
            stack.append([lv, ix])
    res.append(("WARN" if probs else "PASS", "항목 번호 순서 (1. 가. 1) 가) (1) (가) ① ㉮)" + (": " + " / ".join(probs[:3]) if probs else "")))
    full = "\n".join(L)
    end_ok = bool(re.search(r"\S {2}끝\.\s*$", full, re.M)) or bool(re.search(r"^\s{0,2}끝\.\s*$", full, re.M))
    if lenient_space:  # PDF text extraction collapses runs of spaces: only check that 끝. is there
        end_ok = end_ok or bool(re.search(r"\S ?끝\.\s*$", full, re.M))
    end_one = bool(re.search(r"\S ?끝\.\s*$", full, re.M)) and not end_ok
    res.append(("PASS" if end_ok else "WARN", "「끝」 표시" + ("" if end_ok else (": 본문 끝에서 두 칸 띄우고 「끝.」" if end_one else ": 본문(또는 붙임) 마지막에 두 칸 띄우고 「끝.」이 없어요"))))
    if re.search(r"붙임\s*:", full):
        res.append(("WARN", "「붙임:」 -> 쌍점 없이 「붙임  1. 계획서 1부.」"))
    return res


DATE_BAD = [
    (re.compile(r"(?<!\d)(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?!\d)"), "날짜는 「{0}. {1}. {2}.」처럼 온점으로"),
    (re.compile(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일"), "공문 날짜는 「{0}. {1}. {2}.」"),
    (re.compile(r"(?<!\d)(\d{4})\.(\d{1,2})\.(\d{1,2})\.?(?!\d)"), "온점 뒤를 한 칸씩: 「{0}. {1}. {2}.」"),
    (re.compile(r"(?<!\d)(\d{4})\. 0(\d)\. "), "월·일 앞의 0은 빼요: 「{0}. {1}.」"),
    (re.compile(r"(?<!\d)(\d{4})\. (\d{1,2})\. (\d{1,2})(?![\d.])"), "날짜 끝에도 온점: 「{0}. {1}. {2}.」"),
]


def check_dates(lines: list[str], official: bool) -> list[tuple[str, str]]:
    txt = "\n".join(lines)
    probs = []
    for i, (rx, msg) in enumerate(DATE_BAD):
        if i == 1 and not official:
            continue
        for m in rx.finditer(txt):
            g = [str(int(x)) if x.isdigit() and len(x) <= 2 else x for x in m.groups()]
            probs.append(f"'{m.group(0)}' -> " + msg.format(*g))
    if official:
        for m in re.finditer(r"(오전|오후)\s*(\d{1,2})시(\s*(\d{1,2})분)?", txt):
            probs.append(f"'{m.group(0)}' -> 24시각제 「15:00」")
    return [("WARN" if probs else "PASS", "날짜·시간 형식 (2026. 11. 19. / 15:00)" + (": " + " / ".join(probs[:3]) if probs else ""))]


SPACING = [  # (pattern, suggestion) - simple, safe rules only (한글 맞춤법 제41~45항, 경기도교육청 2023 공문서 작성법 p.10)
    (r"그 동안", "그동안"), (r"첫 해", "첫해"), (r"수 차례", "수차례"), (r"안됩니다", "안 됩니다"), (r"변동없음", "변동 없음"),
    (r"사용중(?=[인이에])", "사용 중"), (r"방과후", "방과 후"), (r"학교간(?=[^\w]|$)", "학교 간"), (r"기한내", "기한 내"), (r"참여시(?=[^\w]|$)", "참여 시"),
    (r"(\d)%(이상|이하|미만|초과)", r"\1% \2"), (r"(할|될|볼|갈|올|줄|알|있을|없을)수(?=\s|있|없|도)", r"\1 수"),
    (r"(하는|있는|없는|되는|했던|하던)것(?=[이을은도])", r"\1 것"), (r"\)\s+(까지|부터|에서|으로)(?=\s|$)", r")\1"), (r"(두|세|네)(가지|개|명)(?![가-힣])", r"\1 \2"),
]


def check_spacing(lines: list[str]) -> list[tuple[str, str]]:
    hits = []
    for ln in lines:
        for pat, rep in SPACING:
            for m in re.finditer(pat, ln):
                hits.append(f"'{m.group(0)}' -> '{m.expand(rep) if chr(92) in rep else rep}'")
    hits = list(dict.fromkeys(hits))
    return [("WARN" if hits else "PASS", "띄어쓰기 (간단 규칙)" + (f": {len(hits)}곳 - " + ", ".join(hits[:5]) if hits else ""))]


def check_placeholders(lines: list[str], fillins: list) -> list[tuple[str, str]]:
    left = list(dict.fromkeys(m for ln in lines for m in ph.leftovers(ln, fillins)))
    res = [("FAIL" if left else "PASS", "빈칸 없음 ([학교명], 20XX, OO, 000 ...)" + (f": {left[:8]} -> 채우거나 fillins에 적어 「바꿔 넣을 곳」으로 알리기" if left else ""))]
    listed = ph.fillin_list(lines, fillins)
    if listed:
        res.append(("WARN", "바꿔 넣을 곳: " + ", ".join(listed)))
    return res


def check_open(path: Path) -> list[tuple[str, str]]:
    suf = path.suffix.lower()
    try:
        if suf == ".hwpx":
            return hwpx_structure(path)
        if suf == ".docx":
            try:
                import docx
                d = docx.Document(str(path))
                return [("PASS", f"워드 파일이 열려요 (문단 {len(d.paragraphs)}개, 표 {len(d.tables)}개)")]
            except ImportError:
                with zipfile.ZipFile(path) as z:
                    ET.fromstring(z.read("word/document.xml"))
                return [("PASS", "워드 파일 구조 정상 (python-docx 없이 XML만 확인)")]
        if suf == ".pdf":
            from pypdf import PdfReader
            r = PdfReader(str(path))
            return [("PASS", f"PDF가 열려요 ({len(r.pages)}쪽)")]
    except Exception as exc:  # noqa: BLE001
        return [("FAIL", f"파일이 열리지 않아요: {type(exc).__name__}: {str(exc)[:120]}")]
    return []


def hwpx_structure(path: Path) -> list[tuple[str, str]]:
    probs = []
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if not infos or infos[0].filename != "mimetype" or infos[0].compress_type != zipfile.ZIP_STORED:
            probs.append("mimetype이 첫 항목(압축 안 함)이 아니에요")
        elif z.read("mimetype") != b"application/hwp+zip":
            probs.append("mimetype 내용이 application/hwp+zip이 아니에요")
        for need in ("Contents/content.hpf", "Contents/header.xml", "META-INF/container.xml", "version.xml"):
            if need not in z.namelist():
                probs.append(f"{need} 없음")
        trees = {}
        for i in infos:
            if i.filename.endswith((".xml", ".hpf", ".rdf")):
                try:
                    trees[i.filename] = ET.fromstring(z.read(i.filename))
                except ET.ParseError as exc:
                    probs.append(f"{i.filename}: XML 오류 {exc}")
        hdr = z.read("Contents/header.xml").decode("utf-8") if "Contents/header.xml" in z.namelist() else ""
        ids = {k: set(re.findall(rf'<hh:{k} id="(\d+)"', hdr)) for k in ("charPr", "paraPr", "borderFill", "style")}
        for k, tag in (("charProperties", "charPr"), ("paraProperties", "paraPr"), ("borderFills", "borderFill")):
            m = re.search(rf'<hh:{k} itemCnt="(\d+)"', hdr)
            if m and int(m.group(1)) != len(ids[tag]):
                probs.append(f"header {k} itemCnt {m.group(1)} != {len(ids[tag])}")
        for n in z.namelist():
            if re.match(r"Contents/section\d+\.xml$", n):
                s = z.read(n).decode("utf-8")
                for attr, key in (("charPrIDRef", "charPr"), ("paraPrIDRef", "paraPr"), ("borderFillIDRef", "borderFill"), ("styleIDRef", "style")):
                    bad = set(re.findall(rf'{attr}="(\d+)"', s)) - ids[key]
                    if bad:
                        probs.append(f"{n}: {attr} {sorted(bad)[:4]} 가 header에 없어요")
        hpf = trees.get("Contents/content.hpf")
        if hpf is not None:
            for it in hpf.iter("{http://www.idpf.org/2007/opf/}item"):
                if it.get("href") not in z.namelist():
                    probs.append(f"content.hpf: {it.get('href')} 없음")
    return [("FAIL" if probs else "PASS", "한글 파일 구조 (mimetype·XML·참조 번호)" + (": " + "; ".join(probs[:4]) if probs else ""))]


def check_fonts(path: Path) -> list[tuple[str, str]]:
    suf = path.suffix.lower()
    used: set = set()
    if suf == ".hwpx":
        with zipfile.ZipFile(path) as z:
            used = set(re.findall(r'<hh:font id="\d+" face="([^"]+)"', z.read("Contents/header.xml").decode("utf-8")))
    elif suf == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
            sty = z.read("word/styles.xml").decode("utf-8") if "word/styles.xml" in z.namelist() else ""
            dd = re.search(r"<w:docDefaults>.*?</w:docDefaults>", sty, re.S)
            for src in (xml, dd.group(0) if dd else ""):  # fonts really used: runs + document defaults (not every unused built-in style)
                for rf in re.findall(r"<w:rFonts [^>]*>", src):
                    used |= set(re.findall(r'w:(?:ascii|eastAsia|hAnsi)="([^"]+)"', rf))
    elif suf == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return []
        missing = set()
        for pg in PdfReader(str(path)).pages:
            fonts = (pg.get("/Resources") or {}).get("/Font") or {}
            for _, ref in fonts.items():
                f = ref.get_object()
                if f.get("/Subtype") == "/Type3":  # glyphs drawn inside the PDF itself (Chrome prints web fonts this way)
                    continue
                desc = f.get("/FontDescriptor")
                if desc is None and f.get("/DescendantFonts"):
                    desc = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
                desc = desc.get_object() if desc is not None else None
                if desc is None or not any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                    missing.add(str(f.get("/BaseFont")))
        return [("WARN" if missing else "PASS", "PDF 글꼴 포함" + (f": 포함 안 된 글꼴 {sorted(missing)[:3]} (다른 PC에서 모양이 바뀔 수 있어요)" if missing else ""))]
    elif suf in (".html", ".htm"):
        h = path.read_text(encoding="utf-8")
        ok = "@font-face" in h and "data:font/woff2" in h
        return [("PASS" if ok else "WARN", "웹 문서 글꼴 포함" + ("" if ok else ": 글꼴이 파일 안에 없어요 (인쇄 PC 글꼴로 보여요)"))]
    else:
        return []
    odd = sorted(f for f in used if f not in COMMON_FONTS)
    return [("WARN" if odd else "PASS", "글꼴이 흔한 한글 글꼴" + (f": {odd[:3]}는 PC에 없으면 다른 글꼴로 바뀌어요" if odd else f" ({', '.join(sorted(used))[:60]})"))]


def is_gongmun(lines: list[str]) -> bool:
    return any(re.match(r"^\s*수신\s", ln) for ln in lines) and any(re.match(r"^\s*제목\s", ln) for ln in lines)


def run(path, kind: str = "", fillins=(), allow_blanks: bool = False, max_pages: int | None = None, min_font: float | None = None) -> list[tuple[str, str]]:
    path = Path(path)
    fills = ph.with_blanks(list(fillins or []), allow_blanks)
    res = []
    res += check_open(path)
    if res and res[0][0] == "FAIL":
        return res
    lines = texts_of(path)
    res += check_placeholders(lines, fills)
    res += check_privacy(lines)
    official = kind == "gongmun" or (not kind and is_gongmun(lines))
    if official:
        res += check_gongmun(lines, lenient_space=path.suffix.lower() == ".pdf")
    res += check_dates(lines, official)
    res += check_spacing(lines)
    res += check_fonts(path)
    if path.suffix.lower() == ".pdf":  # page count (limit), how full each page is, smallest text size
        import doc_look
        res += doc_look.checks(path, max_pages, min_font)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--kind", default="")
    ap.add_argument("--fillins", default="")
    ap.add_argument("--allow-blanks", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-pages", type=int, help="PDF: FAIL when the file has more pages")
    ap.add_argument("--min-font", type=float, help="PDF: FAIL when the smallest text is below this many pt")
    a = ap.parse_args()
    res = run(a.file, a.kind, [x for x in a.fillins.split(",") if x], a.allow_blanks, a.max_pages, a.min_font)
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        for lv, msg in res:
            print(f"{lv:4} {msg}")
    return 1 if any(lv == "FAIL" for lv, _ in res) else 0


if __name__ == "__main__":
    raise SystemExit(main())
