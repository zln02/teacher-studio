# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Placeholder detector: a deliverable must never ship `[학교명]`, `(학교명 입력)`, `○○학교`, `OOO`, `(예시)`, `20XX`, `000-0000` or other blanks.

    find(text)                       -> ['[학교명]', '20XX', ...]   (raw matches)
    leftovers(text, fillins)         -> matches that the spec did NOT list as fill-ins
    fillin_list(texts, fillins)      -> the short 「바꿔 넣을 곳」 list (listed fill-ins that really are in the file)

Rule: fill blanks with a plausible stated assumption (today's date / school year, generic 「우리 학교」) or list them in the spec as
`"fillins": ["학교명", ...]` - those are shown at the final checkpoint as 「바꿔 넣을 곳」 and do not FAIL the review.
The user wins: if they ask for a template / 양식 / 빈칸 있는 틀, set `"template_blanks": true` in the spec - every blank is then only reported as 「바꿔 넣을 곳」.
"""
from __future__ import annotations

import re

_BRACKET = re.compile(r"\[([^\[\]\n]{1,40})\]|【([^【】\n]{1,40})】|\{\{[^{}\n]{1,40}\}\}|[<＜〈]([^<>＜＞〈〉\n]{1,16}(?:명|이름|날짜|입력|번호))[>＞〉]")
_OTHER = [
    re.compile(r"(?<![0-9A-Za-z])20[Xx＊*○〇]{2}(?![0-9A-Za-z])"),          # 20XX
    re.compile(r"(?<![A-Za-z])[OＯ]{2,}(?![A-Za-z])"),                      # OO팀, OOO
    re.compile(r"[○〇◯□■◇△▢]{2,}"),                                        # ○○학교, △△부
    re.compile(r"(?<![A-Za-z])[X×Ｘ]{2,}(?![A-Za-z])"),                    # XX
    re.compile(r"(?<![\d,.])0{3,}(?![\d,])"),                              # 000-0000 (not 1,000 / 2000)
    re.compile(r"(?<![\d.:])00 ?[월일](?![가-힣])|(?<![\d.:])0 ?월 ?0 ?일"),   # 00월 00일, 0월 0일 (not 10월, 20일)
    re.compile(r"학교명|담임명|교사명|담당자명|선생님 ?성함|OO ?초|OO ?중|OO ?고|\bTBD\b|\bTODO\b|\bFIXME\b|Lorem ipsum|(?:제목|내용|텍스트|이름)[을를] 입력"),
    # a note that tells the reader to fill the slot: (학교명 입력) · (기관명을 입력하세요) · (날짜 기입) · (실제 값으로 바꿔 주세요) · (수정 필요)
    re.compile(r"[(（][^()（）\n]{1,24}(?:입력|기입|기재)(?:하세요|해 ?주세요|하십시오| ?요망| ?필요| ?바람| ?란)?[)）]"),
    re.compile(r"[(（][^()（）\n]{1,24}(?:넣어|적어|바꿔|써|채워) ?주세요[)）]|[(（][^()（）\n]{0,20}(?:교체|수정|변경) ?(?:필요|요망)[)）]"),
    re.compile(r"[(（] ?(?:예시|샘플|가칭|미정|추후 ?(?:확정|안내|기재|결정)|작성 ?예) ?[)）]"),   # (예시) (미정) (추후 확정)
    re.compile(r"여기에 [^\n.]{0,16}(?:입력|기입|작성|넣으|적으)"),                             # 여기에 내용을 입력
]


def _bracket_is_ui(inner: str) -> bool:
    """`[1]`, `[x]`, our own UI hints like `[삽입 > 비디오]` are not blanks."""
    s = inner.strip()
    return (not s) or s.isdigit() or ">" in s or "삽입" in s or s.lower() in ("x", "enter", "esc", "space")


def find(text: str) -> list[str]:
    t = text or ""
    out: list[str] = []
    for m in _BRACKET.finditer(t):
        inner = m.group(1) or m.group(2) or m.group(3) or m.group(0)
        if not _bracket_is_ui(inner):
            out.append(m.group(0))
    for rx in _OTHER:
        out += [m.group(0) for m in rx.finditer(t)]
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def _norm(s: str) -> str:
    return re.sub(r"[\[\]【】{}\s]", "", s or "")


ALLOW_ALL = "*"  # fillins containing "*" = the user wants a template / 양식 with blanks: every blank is reported as 「바꿔 넣을 곳」, none fails


def with_blanks(fillins, template_blanks) -> list:
    """The spec's fillins, plus the allow-all marker when the spec says "template_blanks": true."""
    return list(fillins or []) + ([ALLOW_ALL] if template_blanks is True else [])


def _listed(match: str, fillins) -> bool:
    if ALLOW_ALL in (fillins or []):
        return True
    m = _norm(match)
    return any(_norm(f) and (_norm(f) == m or _norm(f) in m) for f in (fillins or []))


def leftovers(text: str, fillins=()) -> list[str]:
    return [m for m in find(text) if not _listed(m, fillins)]


def fillin_list(texts, fillins=()) -> list[str]:
    """The listed fill-ins that actually appear (what the teacher still has to replace), in order."""
    found: list[str] = []
    for t in texts:
        for m in find(t):
            if _listed(m, fillins) and m not in found:
                found.append(m)
    return found
