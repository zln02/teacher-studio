# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Light path (가벼운 길): for simple requests a plain agent already does well (a short web page, a plain notice text, a list),
make it directly and run only this: privacy, blanks, offline, old-Chrome syntax, then the closing delivery menu. No pipeline,
no storyboard, no screenshots. Seconds, not minutes (fair comparison 2026-11-22: 14 min with the full pipeline vs 44 s plain).

    python3 light_check.py page.html            # or notice.md / notice.txt
    python3 light_check.py --route "<request>"  # light | full: should this request take the light path?
Rule (references/light-path.md): light = ONE simple file (a page, a short notice or list) with no game, deck, video, 한글/워드 form,
data file, student data or outward sharing in it. Everything else goes the full way.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for d in (HERE.parent / "shared" / "tools", HERE.parents[1] / "shared" / "tools"):
    if d.is_dir():
        sys.path.insert(0, str(d))
        break
sys.path.insert(0, str(HERE))

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HEAVY = re.compile(r"게임|퀴즈|방탈출|빙고|PPT|피피티|파워포인트|슬라이드|발표\s*자료|영상|동영상|오프닝|한글\s*파일|hwp|워드|docx|공문|"
                   r"엑셀|CSV|csv|설문\s*분석|데이터|보고서|계획서|신청서|동의서|타이머|뽑기|모둠\s*나누|점수판|대진표|단톡|올려|공유|게시|"
                   r"학생\s*명단|성적|생기부|상담", re.I)
LIGHT = re.compile(r"웹\s*페이지|페이지|일정표|안내\s*글|안내문\s*(?:글|문구)|목록|체크리스트|메모|글\s*써|문구|소개\s*글|초대\s*글")
RRN = re.compile(r"(?<!\d)\d{6}\s?-\s?[1-4]\d{6}(?!\d)")
MOBILE = re.compile(r"(?<!\d)01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)")
STUDENT_ID = re.compile(r"\d\s*학년\s*\d{1,2}\s*반\s*\d{1,2}\s*번")
NAMED = re.compile(r"(?:성명|이름|학생명|보호자명)\s*[:：]\s*[가-힣]{2,4}(?![가-힣])")
EXTERNAL = re.compile(r"""<(?:script|img|link|iframe|video|audio|source)\b[^>]*(?:src|href)\s*=\s*["']?(?:https?:)?//""", re.I)
CSS_URL = re.compile(r"url\(\s*['\"]?(?:https?:)?//|@import", re.I)


def route(request: str) -> str:
    """light | full. Light only when the request is one simple page / short text and names nothing heavy."""
    req = request or ""
    if HEAVY.search(req) or len(req) > 140:
        return "full"
    return "light" if LIGHT.search(req) else "full"


def check(path: Path) -> list[tuple[str, str]]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    is_html = path.suffix.lower() in (".html", ".htm")
    plain = re.sub(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", " ", txt, flags=re.S) if is_html else txt
    out: list[tuple[str, str]] = []
    pv = [("주민등록번호", RRN), ("휴대전화 번호", MOBILE), ("학년·반·번호", STUDENT_ID), ("실명 칸", NAMED)]
    hits = [lab for lab, rx in pv if rx.search(plain)]
    out.append(("FAIL", "개인정보가 보여요: " + ", ".join(hits) + " -> 지우거나 예시로 바꾸기") if hits else ("PASS", "no personal data (주민번호 · 휴대전화 · 학년반번호 · 실명 칸)"))
    try:
        import placeholders as ph
        if is_html:
            out += [(lv, m) for lv, m in ph.html_checks(txt) if lv in ("FAIL", "WARN")] or [("PASS", "no blanks left")]
        else:
            left = ph.find(plain)
            out.append(("FAIL", f"빈칸이 남았어요 {left[:5]} -> 그럴듯한 예시 값으로") if left else ("PASS", "no blanks left"))
    except ImportError:
        out.append(("SKIP", "blank check unavailable"))
    if is_html:
        ext = EXTERNAL.findall(txt) + CSS_URL.findall(txt)
        out.append(("FAIL", "인터넷이 있어야 열려요 (외부 그림·스크립트·글꼴) -> 파일 안에 넣기") if ext else ("PASS", "offline: no outside script, image or style"))
        mod = re.search(r"\?\.(?!\d)|\?\?(?!=)", "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", txt, re.S)))
        out.append(("FAIL", "오래된 학교 크롬에서 안 돌아가는 문법(?. ??)") if mod else ("PASS", "old-Chrome safe (no ?. ??)"))
        out.append(("PASS" if "<meta name=\"viewport\"" in txt or "name='viewport'" in txt else "WARN", "phone-friendly viewport"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", type=Path)
    ap.add_argument("--route", default=None, help="print light | full for a request")
    a = ap.parse_args()
    if a.route is not None:
        print(route(a.route))
        return 0
    if not a.file or not a.file.is_file():
        ap.error("file required")
    res = check(a.file)
    for lv, m in res:
        print(f"{lv:4} {m}")
    fails = sum(1 for lv, _ in res if lv == "FAIL")
    print(f"RESULT: {'FAIL' if fails else 'PASS'} ({fails} fail)")
    if not fails:
        import deliver
        doc = a.file.suffix.lower() in (".md", ".txt")   # the page itself is already the TV / screen way; a text goes to the messenger
        print(deliver.delivery_menu("doc" if doc else "tool", "share" if doc else "tv"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
