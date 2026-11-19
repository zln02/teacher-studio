# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""배포 꾸러미 (delivery pack): given a finished file, print a short Korean note on how to hand it out. Reads the file only; never uploads anything.

Usage:
    python3 deliver.py FILE [--url https://link.you/already/have --qr qr.svg|qr.png] [--used PATH] [--since DAYS]

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--url", default="")
    ap.add_argument("--qr", help="write the QR here (.svg or .png)")
    ap.add_argument("--used", help="path of used.json (default ~/.teacher-studio/used.json)")
    ap.add_argument("--since", type=int, default=7, help="credit lines from the last N days")
    a = ap.parse_args()
    p = Path(a.file)
    if not p.is_file():
        print("파일을 찾을 수 없어요: %s" % a.file)
        return 1
    print(pack(p, a.url, Path(a.qr) if a.qr else None, Path(a.used) if a.used else None, a.since))
    return 0


if __name__ == "__main__":
    sys.exit(main())
