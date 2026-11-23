# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""배포 꾸러미 (delivery pack): given a finished file, print a short Korean note on how to hand it out. Never uploads anything.

Usage:
    python3 deliver.py FILE [--url https://link.you/already/have --qr qr.svg|qr.png] [--used PATH] [--since DAYS]
    python3 deliver.py FILE --use tv|tablet|print|lms|home|archive|screen|share|sns|drive [--audience auto|teacher|general]
                       [--kind game|deck|doc|data|video|tool] [--grade 초3] [--spec deck.json] [--yes] [--dry-run]

--use = 활용·전달 단계 (references/classroom-use.md): makes the matching files next to FILE with the existing weapons
(HTML -> PDF via teacher-docs pdf_tools, CSV <-> XLSX, HTML tables -> CSV, deck -> PPTX via teacher-slides deck.py --pptx,
office files -> PDF via LibreOffice when present), checks which program opens each file on THIS computer (env_programs.py),
and prints the 「수업 활용 꾸러미」 (teacher) or 「활용·전달 꾸러미」 (everyone else). Nothing is installed without --yes.

Prints: size, offline OK or not, how to open on phone/TV, print/PDF hint, privacy checklist, and the 출처 line from the skill_scout log
(~/.teacher-studio/used.json) when something else was used. The QR (only for a URL YOU give) is drawn offline with the bundled
qrcodegen (shared/vendor) as SVG or PNG; without the library it says so and skips.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import struct
import sys
import zlib
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
EXT_KIND = {".html": "html", ".htm": "html", ".mp4": "video", ".webm": "video", ".pdf": "pdf", ".docx": "doc", ".pptx": "doc", ".xlsx": "doc",
            ".hwp": "doc", ".hwpx": "doc", ".png": "image", ".jpg": "image", ".jpeg": "image", ".svg": "image"}
EXTERNAL = re.compile(r"""(?:<(?:script|img|link|iframe|source|video|audio)\b[^>]*?\b(?:src|href)\s*=\s*["']?(?:https?:)?//|url\(\s*["']?https?://|@import\s+(?:url\()?\s*["']?https?://)""", re.I)


def human_size(n: int) -> str:
    for unit, div in (("MB", 1 << 20), ("KB", 1 << 10)):
        if n >= div:
            return "%.1f%s" % (n / div, unit)
    return "%d바이트" % n


def offline_check(path: Path, kind: str):
    """(ok: bool|None, note). Only html is scanned; other kinds are self-contained files."""
    if kind != "html":
        return None, "파일 하나로 되어 있어요."
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, "읽지 못했어요."
    hits = EXTERNAL.findall(text)
    if hits:
        return False, "바깥 주소에서 가져오는 부분이 %d곳 있어서 인터넷이 없으면 일부가 안 보일 수 있어요." % len(hits)
    return True, "인터넷 없이도 열려요."


def open_lines(kind: str) -> list:
    if kind == "html":
        return ["TV·칠판: 파일을 더블클릭해 열고 F11(전체 화면)", "폰: 파일을 메신저로 보내 열거나, 링크가 있으면 링크로 열기 (QR은 링크가 있을 때 만들어 드려요)",
                "인쇄·PDF: Ctrl+P → PDF로 저장 (배경 그래픽 켜기)"]
    if kind == "video":
        return ["TV: USB나 클라우드로 옮겨 재생 (mp4가 가장 잘 열려요)", "폰: 메신저로 보내기 (큰 파일은 링크로)", "올리는 곳(유튜브·학급 사이트)은 선생님이 직접 올려 주세요"]
    if kind == "pdf":
        return ["TV·폰 모두 PDF 열기로 열려요", "인쇄: 그대로 인쇄 (용지 크기 A4 확인)"]
    if kind == "doc":
        return ["컴퓨터의 한글·워드·파워포인트·엑셀로 열어요", "폰은 PDF로 저장해서 보내면 더 잘 보여요", "인쇄: 미리보기에서 쪽 나눔 확인"]
    if kind == "image":
        return ["TV·폰 모두 그림 열기로 열려요", "인쇄: 사진 인쇄 설정에서 크기 맞춤"]
    return ["열어 보기: 파일을 더블클릭", "인쇄가 필요하면 PDF로 저장해서 확인"]


PRIVACY = ["학생 실명·학번·사진·목소리가 들어 있지 않은가요? (있으면 가명으로)", "다른 사람의 글·그림·음악을 허락 없이 쓰지 않았나요? (출처 표시, 이용 허락 확인)",
           "학부모·학생에게 보내거나 인터넷에 올리는 건 선생님이 직접 확인하고 보내세요 (저는 보내지 않아요)"]


def find_qrcodegen():
    cands = [SKILL / "shared" / "vendor" / "qrcodegen", *sorted(SKILL.parent.glob("*/shared/vendor/qrcodegen")), SKILL.parent.parent / "shared" / "vendor" / "qrcodegen"]
    for d in cands:
        if (d / "qrcodegen.py").exists():
            return d
    return None


def qr_matrix(url: str):
    """Boolean matrix with a 4-module quiet zone, or None if the library is missing."""
    d = find_qrcodegen()
    if not d:
        return None
    sys.path.insert(0, str(d))
    import qrcodegen  # type: ignore
    qr = qrcodegen.QrCode.encode_text(url, qrcodegen.QrCode.Ecc.MEDIUM)
    n, b = qr.get_size(), 4
    return [[(0 <= x - b < n and 0 <= y - b < n and qr.get_module(x - b, y - b)) for x in range(n + 2 * b)] for y in range(n + 2 * b)]


def qr_svg(m) -> str:
    n = len(m)
    path = "".join("M%d,%dh1v1h-1z" % (x, y) for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges"><rect width="100%%" height="100%%" fill="#fff"/>'
            '<path d="%s" fill="#000"/></svg>' % (n, n, path))


def qr_png(m, scale: int = 10) -> bytes:
    n = len(m)
    raw = bytearray()
    for row in m:
        line = bytearray()
        for v in row:
            line += (b"\x00" if v else b"\xff") * scale
        raw += (b"\x00" + bytes(line)) * scale

    def chunk(t, data):
        c = struct.pack(">I", len(data)) + t + data
        return c + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)
    size = n * scale
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def valid_url(u: str) -> bool:
    return bool(re.fullmatch(r"https?://[^\s<>\"']{4,500}", u or ""))


def make_qr(url: str, out: Path) -> str:
    if not valid_url(url):
        return "QR: http:// 또는 https:// 로 시작하는 주소만 만들 수 있어요."
    m = qr_matrix(url)
    if m is None:
        return "QR: QR 도구가 이 설치에 없어서 만들지 못했어요 (링크를 그대로 써 주세요)."
    if out.suffix.lower() == ".png":
        out.write_bytes(qr_png(m))
    else:
        out.write_text(qr_svg(m), encoding="utf-8")
    return "QR: %s 에 그렸어요. (주소는 선생님이 올린 곳의 것 그대로, 인터넷 없이 만들었어요)" % out


def credit_lines(used: Path | None, since_days: int = 7, today=None) -> list:
    path = used or Path(os.environ.get("TEACHER_STUDIO_HOME") or Path.home() / ".teacher-studio") / "used.json"
    try:
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    today = today or datetime.date.today()
    out = []
    for r in rows if isinstance(rows, list) else []:
        try:
            age = (today - datetime.date.fromisoformat(str(r.get("date")))).days
        except ValueError:
            continue
        if 0 <= age <= since_days and r.get("name"):
            out.append("출처: %s (%s, %s)" % (r["name"], r.get("source", ""), r.get("license", "unknown")))
    return out[-3:]


def pack(path: Path, url: str = "", qr_out: Path | None = None, used: Path | None = None, since: int = 7) -> str:
    kind = EXT_KIND.get(path.suffix.lower(), "other")
    size = path.stat().st_size
    ok, note = offline_check(path, kind)
    mark = {True: "OK", False: "주의", None: "확인"}[ok]
    lines = ["배포 꾸러미: %s" % path.name, "크기: %s" % human_size(size) + ("  (메신저로 보내기엔 넉넉해요)" if size < 20 << 20 else "  (크다: 링크나 USB가 나아요)"),
             "인터넷 없이: %s - %s" % (mark, note), "열기:"]
    lines += ["  - " + s for s in open_lines(kind)]
    if url or qr_out:
        lines.append(make_qr(url, qr_out or Path("qr.svg")))
    else:
        lines.append("QR: 링크가 있으면 주소를 알려 주세요 (제가 올리지는 않아요).")
    lines.append("보내기 전 확인:")
    lines += ["  [ ] " + s for s in PRIVACY]
    cr = credit_lines(used, since)
    lines.append(cr[0] if len(cr) == 1 else ("\n".join(cr) if cr else "출처: 다른 도구·자료를 쓰지 않았다면 줄 필요 없어요."))
    return "\n".join(lines)


# ---------------------------------------------------------------- 활용·전달 단계 (--use) -- references/classroom-use.md
import csv  # noqa: E402
import html.parser  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402


def _load_workdir():
    """shared/tools/workdir.py: work folders that never need %TEMP% (an agent's security box cannot use tempfile's private folders) + the no-browser probe."""
    here = Path(__file__).resolve().parent
    for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
        if (d / "workdir.py").is_file():
            if str(d) not in sys.path:
                sys.path.append(str(d))
            import workdir as _w
            return _w
    raise ImportError("shared/tools/workdir.py not found (run tools/sync_shared.py)")


workdir = _load_workdir()

# use -> (audience, Korean label, base use for formats). Teacher names and general names share one format table.
USES = {
    "tv": ("teacher", "교실 TV·프로젝터", "tv"), "tablet": ("teacher", "학생 태블릿·폰에 나눠 주기", "tablet"),
    "print": ("both", "인쇄", "print"), "lms": ("teacher", "클래스룸·패들렛·학급 홈페이지에 올리기", "lms"),
    "home": ("teacher", "가정에 보내기", "home"), "archive": ("both", "다음에 고칠 원본으로 보관", "archive"),
    "screen": ("general", "회의실 화면·발표", "tv"), "share": ("general", "카톡·메일로 공유", "home"),
    "sns": ("general", "SNS·블로그·홈페이지에 올리기", "lms"), "drive": ("general", "팀 공유 폴더(드라이브)", "lms"),
}
DEFAULT_USE = {"teacher": "tv", "general": "screen"}  # 「알아서」: screen + a PDF
OUTWARD = {"tablet", "lms", "home"}  # base uses that leave this computer -> the privacy check comes first


# End-of-job delivery menu (owner rule 2026-11-23): ALWAYS shown, even after 「알아서」. The recommended way is made already;
# the others are one word away. Sharing ways (②③) keep the privacy check first.
MENU = [("tv", "TV·화면"), ("share", "단톡방·메신저"), ("tablet", "학생 태블릿"), ("print", "인쇄·PDF"), ("archive", "고쳐 쓸 파일(한글·PPT)")]
MENU_NUM = "①②③④⑤"
MENU_USE = {"tv": "tv", "share": "share", "tablet": "tablet", "print": "print", "archive": "archive"}


def recommend_use(kind: str, audience: str = "teacher") -> str:
    """deck / game / tool / video -> TV·화면; 안내문·문서 -> 단톡방·메신저 (a PDF to send); data -> 고쳐 쓸 파일."""
    return {"doc": "share", "data": "archive"}.get(kind, "tv")


def delivery_menu(kind: str, made: str = "", audience: str = "teacher") -> str:
    """The one closing message: 「✅ 다 만들었어요! 어떻게 받으시겠어요? (추천: …)」 + ① … ⑤, the recommended one marked as made."""
    rec = made if made in dict(MENU) else recommend_use(kind, audience)
    if rec in ("screen",):
        rec = "tv"
    labels = dict(MENU)
    items = []
    for i, (k, lab) in enumerate(MENU):
        tail = " ← 이미 만들어 뒀어요" if (k == rec and made) else ""
        if k == "tablet" and audience != "teacher":
            lab = "휴대폰·태블릿"
        items.append(f"{MENU_NUM[i]} {lab}{tail}")
    return (f"✅ 다 만들었어요! 어떻게 받으시겠어요? (추천: {labels[rec]})\n" + "  ".join(items)
            + "\n번호만 말씀하시면 바로 그 모양으로 드려요. 밖으로 보내는 ②③은 개인정보부터 함께 확인해요.")


def audience_of(use: str, audience: str = "auto", prefs: Path | None = None) -> str:
    """teacher | general. Never asked: the use name decides, else saved prefs (school level) say teacher."""
    if audience in ("teacher", "general"):
        return audience
    a = USES.get(use, ("both",))[0]
    if a != "both":
        return a
    p = prefs or Path(os.environ.get("TEACHER_STUDIO_HOME") or Path.home() / ".teacher-studio") / "prefs.json"
    try:
        return "teacher" if json.loads(Path(p).read_text(encoding="utf-8")).get("level") else "general"
    except (OSError, ValueError, AttributeError):
        return "general"


def _head(path: Path, n: int = 200000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:n]
    except OSError:
        return ""


def is_deck(path: Path) -> bool:
    ext = path.suffix.lower()
    return ext == ".pptx" or (ext in (".html", ".htm") and 'name="ts-deck"' in _head(path, 20000))


def has_table(path: Path) -> bool:
    ext = path.suffix.lower()
    return ext in (".csv", ".xlsx") or (ext in (".html", ".htm") and "<table" in _head(path).lower())


def kind_of(path: Path, kind: str = "") -> str:
    if kind:
        return kind
    ext = path.suffix.lower()
    if is_deck(path):
        return "deck"
    if ext in (".csv", ".xlsx"):
        return "data"
    if ext in (".mp4", ".webm"):
        return "video"
    if ext in (".html", ".htm"):
        title = re.search(r"<title>([^<]{0,120})", _head(path, 20000), re.I)
        if title and re.search(r"타이머|뽑기|모둠|대진표|점수판|timer|picker|scoreboard|bracket", title.group(1), re.I):
            return "tool"
        return "game"
    return "doc"


def plan_formats(use: str, path: Path) -> list:
    """File types to ADD next to the source for this use (the source itself is always kept)."""
    base = USES[use][2]
    ext = path.suffix.lower()
    html_src = ext in (".html", ".htm")
    if ext in (".mp4", ".webm", ".png", ".jpg", ".jpeg", ".svg"):
        return []
    if base == "tv":
        return [".pdf"] if ext in (".docx", ".hwpx", ".hwp") else []
    if base == "tablet":
        return [] if html_src or ext == ".pdf" else [".pdf"]
    if base in ("print", "home"):
        return [] if ext == ".pdf" else [".pdf"]
    if base == "lms":
        out = [] if ext == ".pdf" else ([".xlsx"] if ext == ".csv" else [".csv"] if ext == ".xlsx" else [".pdf"])
        if html_src and has_table(path):
            out.append(".csv")
        return out
    if base == "archive":
        if html_src and is_deck(path):
            return [".pptx"]
        if ext == ".csv":
            return [".xlsx"]
        return [".csv"] if html_src and has_table(path) else []
    return []


def _sibling_scripts(skill: str) -> Path | None:
    for d in (SKILL.parent / skill / "scripts", SKILL.parent.parent / "skills" / skill / "scripts"):
        if d.is_dir():
            return d
    return None


def _ensure_mod():
    for d in (SKILL / "shared" / "tools", SKILL.parent.parent / "shared" / "tools"):
        if (d / "ensure.py").exists():
            if str(d) not in sys.path:
                sys.path.insert(0, str(d))
            try:
                import ensure  # type: ignore
                return ensure
            except ImportError:
                return None
    return None


def conv_pdf(src: Path, dest: Path, yes: bool = False, spec: Path | None = None) -> dict:
    """HTML -> PDF through the docs weapon (pdf_tools.html_to_pdf, A4); office files -> PDF through LibreOffice if present."""
    ext = src.suffix.lower()
    if ext in (".html", ".htm"):
        d = _sibling_scripts("teacher-docs")
        if not d:
            return {"ok": False, "error": "PDF 도구(teacher-docs)가 없어요: 크롬/엣지에서 열고 Ctrl+P → PDF로 저장"}
        _ensure_mod()
        sys.path.insert(0, str(d))
        import pdf_tools  # type: ignore
        return pdf_tools.html_to_pdf(src, dest)
    em = _ensure_mod()
    soffice = em.find_libreoffice() if em else (shutil.which("soffice") or "")
    if soffice:
        with workdir.temp_dir("pdf", near=dest) as td:
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", td, str(src)], capture_output=True, timeout=180)
            got = Path(td) / (src.stem + ".pdf")
            if got.exists():
                shutil.copyfile(got, dest)
                return {"ok": True, "how": "LibreOffice"}
    app = {".hwpx": "한글", ".hwp": "한글", ".docx": "워드(또는 한글)", ".pptx": "PowerPoint"}.get(ext, "그 프로그램")
    return {"ok": False, "error": "%s에서 파일을 열고 「PDF로 저장」(또는 인쇄 → PDF)으로 바꿔 주세요" % app}


def conv_table(src: Path, dest: Path, yes: bool = False, spec: Path | None = None) -> dict:
    """csv -> xlsx, xlsx -> csv, html <table> -> csv. Copies cells only."""
    s, d = src.suffix.lower(), dest.suffix.lower()
    if s in (".html", ".htm") and d == ".csv":
        rows = html_tables(_head(src, 5_000_000))
        if not rows:
            return {"ok": False, "error": "표를 찾지 못했어요"}
        with open(dest, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerows(rows)
        return {"ok": True, "how": "표 → CSV"}
    try:
        import openpyxl  # type: ignore
    except ImportError:
        em = _ensure_mod()
        if not (em and yes):
            return {"ok": False, "offer": "엑셀 파일(.xlsx)을 만들려면 작은 도구(openpyxl, 약 3MB)가 필요해요. 설치할까요?"}
        r = em.ensure("openpyxl", consent=True)
        if not r.get("ok"):
            return {"ok": False, "error": r.get("prompt", "엑셀 도구 설치 실패")}
        import openpyxl  # type: ignore  # noqa: F811
    if s == ".csv" and d == ".xlsx":
        wb = openpyxl.Workbook()
        ws = wb.active
        with open(src, encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                ws.append(row)
        wb.save(dest)
        return {"ok": True, "how": "CSV → 엑셀"}
    if s == ".xlsx" and d == ".csv":
        wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
        with open(dest, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            for row in wb.worksheets[0].iter_rows(values_only=True):
                w.writerow(["" if v is None else v for v in row])
        return {"ok": True, "how": "엑셀 → CSV (첫 시트)"}
    return {"ok": False, "error": "바꿀 수 없는 조합"}


def conv_pptx(src: Path, dest: Path, yes: bool = False, spec: Path | None = None) -> dict:
    """Deck HTML -> editable PPTX through the slides weapon (deck.py --pptx; needs the deck's spec.json)."""
    if not spec or not Path(spec).is_file():
        return {"ok": False, "error": "고칠 수 있는 PPT를 만들려면 슬라이드를 만들 때 쓴 spec(deck.json)이 필요해요 (--spec)"}
    d = _sibling_scripts("teacher-slides")
    if not d:
        return {"ok": False, "error": "슬라이드 도구(teacher-slides)가 없어요"}
    with workdir.temp_dir("pptx", near=dest) as td:
        cmd = [sys.executable, str(d / "deck.py"), "--spec", str(spec), "--out", str(Path(td) / "deck.html"), "--pptx", str(dest), "--no-check"]
        if yes:
            cmd.append("--yes")
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    if dest.exists():
        return {"ok": True, "how": "슬라이드 도구 --pptx"}
    tail = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-1:]
    return {"ok": False, "offer": "PPT 파일을 만들려면 작은 도구(python-pptx, 약 6MB)가 필요할 수 있어요. 설치할까요?",
            "error": tail[0] if tail else "PPT 만들기 실패"}


CONVERTERS = {".pdf": conv_pdf, ".csv": conv_table, ".xlsx": conv_table, ".pptx": conv_pptx}


class _TableParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell, self._in = [], None, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in += 1
        elif tag == "tr" and self._in:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
        elif tag == "table" and self._in:
            self._in -= 1

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def html_tables(text: str) -> list:
    p = _TableParser()
    p.feed(text)
    return p.rows


def mobile_check(path: Path) -> str:
    if path.suffix.lower() not in (".html", ".htm"):
        return "폰·태블릿: PDF·그림은 그대로 열려요."
    t = _head(path)
    if 'name="viewport"' not in t:
        return "폰·태블릿 화면: 주의 - 작은 화면 설정이 없어서 글자가 작게 보일 수 있어요 (한 번 열어 봐 주세요)."
    if re.search(r"\bmin-width\s*:\s*(?:[89]\d\d|\d{4,})px", t):
        return "폰·태블릿 화면: 주의 - 넓은 화면 기준이라 옆으로 밀어야 할 수 있어요."
    return "폰·태블릿 화면: OK - 작은 화면 설정이 들어 있어요 (가로로 돌리면 더 커요)."


HOWTO = {
    "tv": ["파일을 더블클릭해 열고 F11 = 전체 화면 (끝낼 때 Esc)", "TV·프로젝터 연결: HDMI를 꽂고 Win+P → 「복제」",
           "글자가 작으면 Ctrl + 더하기(+)로 키우기. 인터넷이 없어도 열려요"],
    "tablet": ["인터넷 없이: 파일 자체를 메신저·클래스룸으로 보내면 기기에서 바로 열려요 (보내기는 직접 해 주세요)",
               "링크가 있으면 --url 로 QR을 만들어 TV에 띄우면 학생들이 찍어서 들어와요 (제가 올리지는 않아요)"],
    "print": ["용지 A4, 크기 「실제 크기(100%)」로 인쇄", "색이 필요하면 「배경 그래픽」 켜기, 흑백이면 미리보기로 글자 대비 확인"],
    "lms": ["올리기는 직접: 클래스룸은 「자료」 만들기 → 파일 추가, 패들렛은 + → 업로드, 학급 홈페이지는 글쓰기 → 첨부",
            "HTML은 내려받아 열어야 하는 곳이 많아서 PDF를 함께 올리면 바로 보여요"],
    "home": ["PDF가 폰에서 가장 잘 열려요. 학교 알림 앱에 직접 첨부해 주세요", "학교 양식 결재는 한글(HWPX) 파일로 올려요"],
    "archive": ["만든 원본(spec·편집 파일)을 결과물과 같은 폴더에 두세요: 다음에 「이거 고쳐 줘」 하면 이어서 고쳐요",
                "PPTX·DOCX·HWPX·XLSX는 직접 열어 고칠 수 있어요"],
}
HOWTO_GENERAL = {
    "tv": ["파일을 더블클릭해 열고 F11 = 전체 화면 (끝낼 때 Esc)", "회의실 화면 연결: HDMI를 꽂고 Win+P → 「복제」", "인터넷이 없어도 열려요"],
    "home": ["카톡·메일엔 PDF가 가장 잘 열려요 (보내기는 직접 해 주세요)", "파일이 크면 드라이브에 올리고 링크로 보내요"],
    "lms": ["올리기는 직접: SNS·블로그는 그림(PNG)이나 PDF 한 장이 좋아요 (그림이 필요하면 말씀해 주세요)",
            "팀 드라이브엔 원본 + PDF를 같이 두면 누구나 열 수 있어요"],
}
IDEAS = {
    "teacher": {
        "game": ["도입 5분 퀴즈로 지난 시간 복습", "모둠 대항전: 모둠이 돌아가며 답하고 점수 겨루기", "출구 티켓: 수업 끝 마지막 3문제로 이해 확인"],
        "deck": ["도입: 첫 장만 띄우고 질문 하나 던지기", "모둠마다 한 장씩 맡아 친구들에게 설명하기", "마지막 장을 정리 퀴즈로 바꿔 출구 티켓처럼"],
        "doc": ["활동지로 나눠 주고 짝과 바꿔 확인하기", "출구 티켓: 마지막 5분에 한 칸만 채우기", "가정 연계 과제로 보내고 다음 시간 나누기"],
        "data": ["그래프 한 장 띄우고 「무엇이 보이나요?」 묻기", "모둠별로 해석 한 줄 쓰기", "다음 목표 세우기 자료로"],
        "video": ["수업 시작 1분 주의 집중", "영상 보고 질문 하나씩 만들기", "끝나고 한 줄 소감 나누기"],
        "tool": ["모둠 활동 시간을 TV에 크게 띄워 두기", "발표 순서·역할을 그 자리에서 뽑기", "정리 1분 알림으로 수업 마무리"],
    },
    "general": {
        "game": ["회의·모임 시작 5분 아이스브레이킹", "팀 대항전으로 분위기 띄우기", "행사 마지막 경품 퀴즈로"],
        "deck": ["회의 시작 5분 요약용으로 앞 세 장만", "핵심 한 장을 모임 공지 카드로", "마지막 장에서 질문 받기"],
        "doc": ["모임 공지 카드로 단톡방에", "인쇄해서 게시판·매장에 붙이기", "회의 전에 미리 보내 읽고 오기"],
        "data": ["회의에서 그래프 한 장으로 결론부터", "월별 비교를 팀과 공유", "다음 목표 세우기 자료로"],
        "video": ["행사 오프닝으로", "SNS 짧은 홍보로", "매장 화면에 반복 재생"],
        "tool": ["회의 발언 시간 재기", "모임 순서·경품 뽑기", "팀 나누기를 화면에 띄워 바로 시작"],
    },
}
PRIVACY_GENERAL = ["다른 사람의 연락처·얼굴 사진·고객 정보가 들어 있지 않은가요?", "남의 글·그림·음악·로고를 허락 없이 쓰지 않았나요? (출처 표시)",
                   "보내거나 올리는 건 직접 확인하고 해 주세요 (저는 올리지 않아요)"]


def ideas(kind: str, audience: str, grade: str = "") -> list:
    out = list(IDEAS["teacher" if audience == "teacher" else "general"].get(kind) or IDEAS["general"]["doc"])
    if audience == "teacher" and kind == "game" and grade:
        if "초" in grade:
            out[1] = "몸으로 OX: 정답 쪽으로 일어서거나 손 들기"
        elif "고" in grade:
            out[2] = "출구 티켓: 한 문제를 골라 이유를 한 줄로 쓰기"
    return out[:3]


def _josa(word: str, pair: str) -> str:
    """Korean particle by the last syllable: pair '으로/로' or '이/가'. Latin/digit endings count as no final consonant."""
    a, b = pair.split("/")
    ch = (word or " ").rstrip(")")[-1:] or " "
    if "가" <= ch <= "힣":
        final = (ord(ch) - 0xAC00) % 28
        if a == "으로":
            return word + (b if final in (0, 8) else a)  # ㄹ받침 takes 로
        return word + (a if final else b)
    return word + b


def dest_for(src: Path, ext: str, use: str) -> Path:
    d = src.with_suffix(ext)
    return d if not d.exists() else src.with_name("%s-%s%s" % (src.stem, use, ext))


def make_for_use(use: str, src: Path, spec: Path | None = None, yes: bool = False, dry: bool = False, converters: dict | None = None) -> dict:
    conv = converters or CONVERTERS
    made, notes, offers = [], [], []
    for ext in plan_formats(use, src):
        dest = dest_for(src, ext, use)
        if dry:
            made.append(dest)
            continue
        try:
            r = conv[ext](src, dest, yes=yes, spec=spec)
        except Exception as e:  # noqa: BLE001 - never crash the pack; say what to do instead
            r = {"ok": False, "error": str(e)[:120]}
        if r.get("ok") and dest.exists():
            made.append(dest)
        else:
            if r.get("offer"):
                offers.append(r["offer"])
            notes.append("%s 못 만듦: %s" % (ext[1:].upper(), r.get("error") or "도구가 필요해요"))
    return {"made": made, "notes": notes, "offers": offers}


def _env_programs():
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import env_programs  # type: ignore
    return env_programs


def use_pack(path: Path, use: str, audience: str = "auto", kind: str = "", grade: str = "", spec: Path | None = None, yes: bool = False,
             dry: bool = False, url: str = "", qr_out: Path | None = None, progs: dict | None = None, converters: dict | None = None) -> str:
    """The 「수업 활용 꾸러미」 (teacher) / 「활용·전달 꾸러미」 (everyone else): files made, how to open them HERE, ideas, privacy."""
    aud = audience_of(use, audience)
    base = USES[use][2]
    res = make_for_use(use, path, spec, yes, dry, converters)
    envp = _env_programs()
    if progs is None:
        progs = envp.load()
    title = "수업 활용 꾸러미" if aud == "teacher" else "활용·전달 꾸러미"
    lines = ["%s: %s → %s" % (title, path.name, USES[use][1])]
    if base in OUTWARD:
        lines.append("먼저 확인 (밖으로 나가기 전):")
        lines += ["  [ ] " + s for s in (PRIVACY if aud == "teacher" else PRIVACY_GENERAL)]
    lines.append("만든 파일:")
    for f in [path] + res["made"]:
        o = envp.opener(f.suffix.lower(), progs)
        how = ("%s 열려요 (더블클릭)" % _josa(o["program"], "으로/로")) if o["ok"] else "이 컴퓨터에서 열 프로그램을 못 찾았어요"
        lines.append("  - %s  (%s, %s)" % (f, "원본" if f == path else ("만들 예정" if dry else "새로 만듦"), how))
        if o.get("offer"):
            lines.append("    → " + o["offer"])
    lines += ["  ! " + n for n in res["notes"]]
    lines += ["  ? " + s for s in res["offers"]]
    lines.append("쓰는 법:")
    how_lines = (HOWTO_GENERAL.get(base) if aud != "teacher" else None) or HOWTO[base]
    if base == "tv" and path.suffix.lower() == ".pptx":
        how_lines = ["PowerPoint에서 F5 = 처음부터 슬라이드 쇼 (끝낼 때 Esc)"] + how_lines[1:]
    lines += ["  - " + s for s in how_lines]
    if base == "tablet":
        lines.append("  - " + mobile_check(path))
        if url or qr_out:
            lines.append("  - " + make_qr(url, qr_out or path.with_name(path.stem + "-qr.svg")))
    lines.append(("수업에 이렇게: " if aud == "teacher" else "이렇게 써 보세요: ") + " · ".join(ideas(kind_of(path, kind), aud, grade)))
    if base not in OUTWARD:
        who = _josa("학생 실명·사진" if aud == "teacher" else "다른 사람 정보", "이/가")
        lines.append("개인정보: %s 없는지 보고, 밖으로 보낼 땐 직접 확인해 주세요 (저는 올리지 않아요)." % who)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--url", default="")
    ap.add_argument("--qr", help="write the QR here (.svg or .png)")
    ap.add_argument("--used", help="path of used.json (default ~/.teacher-studio/used.json)")
    ap.add_argument("--since", type=int, default=7, help="credit lines from the last N days")
    ap.add_argument("--use", choices=list(USES) + ["auto"], help="활용·전달 단계: make the matching files + the 꾸러미 (auto = 「알아서」 default)")
    ap.add_argument("--audience", choices=["auto", "teacher", "general"], default="auto")
    ap.add_argument("--kind", choices=["game", "deck", "doc", "data", "video", "tool"], default="")
    ap.add_argument("--grade", default="", help="e.g. 초3, 중2, 고1 (only shapes the lesson ideas)")
    ap.add_argument("--spec", type=Path, help="deck spec.json (archive: editable PPTX)")
    ap.add_argument("--yes", action="store_true", help="the user agreed to install a small helper (openpyxl / python-pptx)")
    ap.add_argument("--dry-run", action="store_true", help="say what would be made; make nothing")
    ap.add_argument("--menu", action="store_true", help="only print the closing delivery menu (the recommended way is made by --use)")
    a = ap.parse_args()
    p = Path(a.file)
    if not p.is_file():
        print("파일을 찾을 수 없어요: %s" % a.file)
        return 1
    if a.menu:
        print(delivery_menu(kind_of(p, a.kind), "", audience_of("print", a.audience)))
        return 0
    if not a.use:
        print(pack(p, a.url, Path(a.qr) if a.qr else None, Path(a.used) if a.used else None, a.since))
        print(delivery_menu(kind_of(p, a.kind), "", audience_of("print", a.audience)))
        return 0
    use = DEFAULT_USE[audience_of("print", a.audience)] if a.use == "auto" else a.use
    out = use_pack(p, use, a.audience, a.kind, a.grade, a.spec, a.yes, a.dry_run, a.url, Path(a.qr) if a.qr else None)
    if a.use == "auto":  # 「알아서」 = TV/screen + a PDF for printing
        r = make_for_use("print", p, a.spec, a.yes, a.dry_run)
        out += "\n" + "\n".join(["인쇄용 PDF: %s" % f for f in r["made"]] + ["  ! " + n for n in r["notes"]])
    made = {"screen": "tv", "home": "share", "lms": "share", "sns": "share", "drive": "share"}.get(use, use)
    print(out)
    print(delivery_menu(kind_of(p, a.kind), made, audience_of(use, a.audience)))
    return 0


def _no_browser_guard() -> bool:
    """True when no browser can start here (an agent's security box). shared/tools/workdir.py then prints ONE line and makes
    every screen check below skip at once instead of waiting for each launch to fail."""
    try:
        here = Path(__file__).resolve().parent
        for d in (here, here.parent / "shared" / "tools", here.parent / "tools", here.parents[2] / "shared" / "tools"):
            if (d / "workdir.py").is_file():
                if str(d) not in sys.path:
                    sys.path.append(str(d))
                import workdir
                return workdir.guard_browser(quiet=True)  # this script rarely needs a browser: the line is printed only where one is needed
    except Exception:  # noqa: BLE001 - the guard must never stop a build
        pass
    return False


if __name__ == "__main__":
    _no_browser_guard()
    sys.exit(main())
