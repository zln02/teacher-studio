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


# ---------------------------------------------------------------------------------------------------------- unknowns policy
# shared/content/CONTENT-RULES.md, 「Unknowns」: what the user did not give is an example value in the body, a blank only where a hand
# writes (회신서 · 신청서 · 서명란 · 학생/보호자 칸), ONE short example note per file, never 「확인 필요」 filler or a 「교사 초안」 stamp.
FILLER = re.compile(r"(?:확인|집계|파악|입력|작성|기재|조사)\s?필요|추후\s?(?:확정|기재|결정)|(?<![가-힣])미정(?![가-힣])")
STAMP = re.compile(r"교사\s?용?\s?초안|검토용\s?초안|(?:배포|제출|결재|발송)\s?전\s?(?:확인|검토)(?:본|용)?|(?<![A-Za-z])DRAFT(?![A-Za-z])")
EXAMPLE_NOTE = re.compile(r"예시(?:\s?(?:값|자료|수치|일정|내용))?\s?(?:입니다|이에요|예요|임(?![가-힣]))|가상\s?수치|(?:자료|출처)\s?[:：]\s?(?:예시|가상)|예시[^\n]{0,30}(?:바꿔|바꾸|교체|확정|실제)")
UNDERLINE = re.compile(r"_{3,}|＿{2,}")
SLIP = re.compile(r"(?:회신서|신청서|동의서|희망서|확인서|응답서)\s*[\]>】)〉」]?\s*$|절취|자르는\s?선|✂")
EXAMPLE_NOTE_DOC = "※ 날짜·장소·금액 등 일부 내용은 예시입니다. 확정된 내용으로 바꾼 뒤 이 줄을 지워 주세요."
EXAMPLE_NOTE_DECK = "[예시 값 안내] 이 자료의 일부 날짜·장소·수치는 예시입니다. 쓰기 전에 실제 값으로 바꿔 주세요."


def fillers(texts) -> list[str]:
    """Every 「확인 필요」-type filler phrase (a count, not a set: 45 cells of 「확인 필요」 are 45 hits)."""
    return [m.group(0) for t in texts for m in FILLER.finditer(t or "")]


def stamps(texts) -> list[str]:
    return [m.group(0) for t in texts for m in STAMP.finditer(t or "")]


def example_notes(texts) -> int:
    """How many lines say 「…은 예시입니다 / 예시 자료(가상 수치) / 예시 … 바꿔 주세요」."""
    return sum(1 for t in texts for ln in (t or "").split("\n") if EXAMPLE_NOTE.search(ln))


def slip_start(lines) -> int:
    """Index of the first line of the hand-filled part (회신서 · 신청서 · 동의서 under a cut line or on its own page); len(lines) when none.
    A slip = a short heading line naming it (or a cut line), followed by something a hand fills in: □, (서명), (인), an underline."""
    L = list(lines)
    for i, ln in enumerate(L):
        s = (ln or "").strip()
        if s and len(s) <= 34 and SLIP.search(s) and not re.search(r"안내|붙임|첨부|제출|통신문", s):
            rest = "\n".join(L[i:])
            if re.search(r"□|☐|\(\s?서명\s?\)|\(\s?인\s?\)|서명|_{3,}|년\s{2,}월\s{2,}일", rest):
                return i
    return len(L)


def policy_checks(body, notes=(), fillins=(), deck: bool = False, lesson: bool = False) -> list[tuple[str, str]]:
    """The unknowns policy on a finished file. body = the text a reader sees (document lines, or slide texts); notes = speaker notes.
    WARN for a slip or two, FAIL when the file is plainly a draft (filler everywhere, a draft stamp)."""
    res: list[tuple[str, str]] = []
    allow = ALLOW_ALL in (fillins or [])  # the user asked for a 양식: blanks are theirs to fill, only the stamp still counts
    fl = fillers(body)
    if fl:
        lv = "FAIL" if len(fl) >= 3 and not allow else "WARN"
        res.append((lv, f"「확인 필요」 같은 빈말 {len(fl)}곳 ({', '.join(list(dict.fromkeys(fl))[:3])}) -> 본문·표에는 그럴듯한 예시 값을 쓰고 fillins에 적어 "
                        "마지막 안내의 「바꿔 넣을 곳」으로 알리세요 (손으로 쓰는 회신서·신청서 칸만 빈칸)"))
    else:
        res.append(("PASS", "「확인 필요」 같은 빈말 없음"))
    st = stamps(body)
    res.append(("FAIL" if st else "PASS", "본문에 「교사 초안」 도장 없음" + (f": {list(dict.fromkeys(st))[:3]} -> 파일에서 지우고, 확인할 것은 마지막 안내에만 적으세요" if st else "")))
    if allow:
        return res
    n_body, n_notes = example_notes(body), example_notes(notes)
    if n_body + n_notes > 1 and n_body > 1:
        where = "발표자 메모(첫 장)나 첫 자료 표 아래 한 줄" if deck else "본문 맨 아래 한 줄"
        res.append(("WARN", f"예시 안내가 {n_body}번 되풀이돼요 -> 파일 전체에서 한 번만 ({where}), 나머지는 지우고 마지막 안내에 목록으로"))
    elif [f for f in (fillins or []) if f != ALLOW_ALL] and not lesson and n_body + n_notes == 0:
        res.append(("WARN", "예시 값을 썼는데(fillins) 예시 안내 한 줄이 없어요 -> " + ("첫 장 발표자 메모에 한 줄" if deck else "본문 맨 아래에 「" + EXAMPLE_NOTE_DOC + "」")))
    return res
