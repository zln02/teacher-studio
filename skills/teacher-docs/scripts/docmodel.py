# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Document spec -> a small block model that every writer (HWPX, DOCX, HTML/PDF) renders the same way.

Spec (short JSON the AI writes):
  {"kind": "gongmun | notice | guide | report", "org": "우리 학교", "title": "...", "date": "2026-11-19",
   "receiver": "수신자 참조 | 내부결재 | ○○학교장", "via": "", "receivers": [...], "sender": "우리학교장",
   "body": ["항목", ["하위 항목", ["더 하위"]], "다음 항목", {"p": "번호 없는 문단"}, {"h": "소제목"}, {"table": {...}}, {"box": [...], "label": "요약"},
            {"note": "※ 참고"}],
   "attachments": ["운영 계획 1부"], "footer": {"시행": "...", "전화": "..."},      # gongmun
   "greeting": "학부모님, 안녕하십니까?", "number": "제2026-35호", "reply": {"title": "참가 신청서", "fields": ["참가 여부 (□ 참가  □ 불참)"]},  # notice
   "fillins": [every example value you wrote for something the user did not give: "체험 날짜 2026. 12. 3.(목)", "참가비 15,000원"] -> the builder adds
             ONE line at the foot of the body (「※ … 예시입니다 …」; "example_note": "own wording" | false) and prints the list for the last message,
   "template_blanks": false, "design": {"mood": "단정", "font": "batang|dotum", "font_size": 12.5 | "large" | "small", "line": 1.6},
   "max_pages": 1 (PDF: shrink a little to fit, FAIL when it still does not), "min_font": 10}
  kind "form" = a one-page 신청서 / 동의서: {"kind":"form","org","title","intro","fields":["학년 / 반", ["상담 방법", "□ 방문   □ 전화"]],"body":[...],
                                              "statement":"위와 같이 신청합니다.","sign":"보호자:            (서명)","to":"우리 학교장"}
  body extras: {"pagebreak": true} | {"image": "photo.png", "width_mm": 80, "caption": ""} | {"qr": "https://...", "caption": "", "size_mm": 28}
               | {"form": {"title": "", "fields": [...], "sign": ""}}
  "reply" works for notice AND guide; "reply": {..., "page": true} puts the 회신서/신청서 on its own page instead of under a cut line.

공문 rules applied here (sources: ../references/gongmun-format.md):
  item marks 1. 가. 1) 가) (1) (가) ① ㉮ ; first level at the left margin, each lower level 2타(= one Hangul character) further in ;
  a group with a single item gets no mark ; `끝.` two spaces after the last body text, or after the last 붙임 line, or under a final table ;
  붙임 without a colon, numbered only when there are two or more ; dates 2026. 11. 19.
Blocks: {"t":"p", text, style, align, indent (chars), hang (mark)} | {"t":"table", columns, rows, widths, kind} | {"t":"space"} | {"t":"rule"} | {"t":"cut"}
        | {"t":"pagebreak"} | {"t":"image", file, width_mm, caption, align} | {"t":"qr", url, size_mm, caption}
"""
from __future__ import annotations

import re

STYLES = {  # pt sizes / weight (house type scale for A4 documents)
    "org": (16, True), "title": (20, True), "subtitle": (14, True), "heading": (14, True), "body": (12.5, False), "bold": (12.5, True),
    "small": (10, False), "sender": (17, True), "table": (11, False), "thead": (11, True), "label": (12.5, True), "note": (10.5, False),
}
BASE_PT = 12.5
SIZE_WORDS = {"small": 11.0, "작게": 11.0, "normal": 12.5, "보통": 12.5, "large": 14.0, "크게": 14.0, "큰 글씨": 14.0, "xlarge": 16.0, "아주 크게": 16.0}


def scale_of(spec: dict) -> float:
    """Print scale from design.font_size (pt of the body text, or small / large / xlarge): every style scales with it."""
    v = (spec.get("design") or {}).get("font_size") or spec.get("font_size")
    if v in (None, ""):
        return 1.0
    try:
        pt = float(SIZE_WORDS.get(str(v).strip().lower(), v))
    except (TypeError, ValueError):
        return 1.0
    return min(18.0, max(9.0, pt)) / BASE_PT


GANA = "가나다라마바사아자차카타파하"
GANA2 = "거너더러머버서어저처커터퍼허"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
CIRCLED_GA = "㉮㉯㉰㉱㉲㉳㉴㉵㉶㉷㉸㉹㉺㉻"
ROMAN = "Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ".split()


def _ga(i: int) -> str:
    return GANA[i] if i < len(GANA) else GANA2[(i - len(GANA)) % len(GANA2)]


def gongmun_mark(level: int, i: int) -> str:
    """level 0..7 -> 1. 가. 1) 가) (1) (가) ① ㉮ (편람 항목 구분)."""
    n = i + 1
    return [f"{n}.", f"{_ga(i)}.", f"{n})", f"{_ga(i)})", f"({n})", f"({_ga(i)})",
            CIRCLED[i] if i < len(CIRCLED) else f"({n})", CIRCLED_GA[i] if i < len(CIRCLED_GA) else f"({_ga(i)})"][min(level, 7)]


def report_mark(level: int, i: int) -> str:
    return ("□", "○", "-", "ㆍ")[min(level, 3)]


def gov_date(s) -> str:
    """'2026-11-19' / '2026.11.19' / '2026년 11월 19일' -> '2026. 11. 19.'; anything else unchanged."""
    m = re.search(r"(\d{4})\s*[-./년]\s*(\d{1,2})\s*[-./월]\s*(\d{1,2})\s*일?\.?", str(s or ""))
    if not m:
        return str(s or "")
    y, mo, d = m.groups()
    return f"{y}. {int(mo)}. {int(d)}."


def _txt(v) -> str:
    """A list / tuple given where one string was expected becomes its lines, never a Python repr such as "['a', 'b']"."""
    if isinstance(v, (list, tuple)):
        return "\n".join(_txt(x) for x in v)
    if isinstance(v, dict):
        return " ".join(_txt(x) for x in v.values())
    return "" if v is None else str(v)


def P(text, style="body", align="left", indent=0.0, hang="", **kw) -> dict:
    return {"t": "p", "text": _txt(text), "style": style, "align": align, "indent": indent, "hang": hang, **kw}


# what the builder could not place (model["meta"]["issues"]): the gate FAILs on it instead of shipping a silently shorter file
_ISSUES: list = []
SECTION_HEAD = ("h", "heading", "title", "name")
SECTION_TEXT = ("body", "items", "bullets", "points", "list", "content", "text", "p", "lines")
SECTION_EXTRA = ("table", "note", "box", "notes")
NUM_PREFIX = re.compile(r"^\s*(?:\d{1,2}|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[가-하])\s*[.)]\s+")


def strip_number(h) -> str:
    """「1. 일정」 given as a heading: the builder numbers it, so its own number goes (no 「1. 1. 일정」)."""
    return NUM_PREFIX.sub("", _txt(h), count=1)


def _as_table(t) -> dict:
    if isinstance(t, dict):
        return {"table": t}
    rows = [r if isinstance(r, list) else [r] for r in (t or [])]
    if rows and len(rows) > 1 and all(isinstance(c, str) for c in rows[0]):
        return {"table": {"columns": rows[0], "rows": rows[1:]}}
    return {"table": {"rows": rows}}


def body_of(d: dict, where: str = "") -> list:
    """The content of a section (or of the whole spec) whatever key the writer used: body / items / bullets / text / table / note ...
    Unknown keys are reported (meta.issues), never dropped in silence."""
    out: list = []
    for k in SECTION_TEXT:
        v = d.get(k)
        if v is None or v == "" or v == []:
            continue
        if isinstance(v, str):
            out.append(v if k in ("body", "items", "bullets", "points", "list", "lines") else {"p": v})
        elif isinstance(v, list):
            out.extend(v)
        elif isinstance(v, dict):
            out.append(v)
    if d.get("table") is not None:
        out.append(_as_table(d["table"]))
    for k in ("box",):
        if d.get(k):
            out.append({"box": d[k] if isinstance(d[k], list) else [d[k]], "label": d.get("label", "요약")})
    for k in ("note", "notes"):
        v = d.get(k)
        for n in (v if isinstance(v, list) else [v] if v else []):
            out.append({"note": n})
    known = set(SECTION_HEAD) | set(SECTION_TEXT) | set(SECTION_EXTRA) | {"label", "id", "number", "level"}
    for k in d:
        if where and k not in known:
            _ISSUES.append(f"{where}: 모르는 칸 「{k}」은(는) 문서에 넣지 못했어요 (body · items · table · note 중 하나로)")
    return out


def head_of(d: dict) -> str:
    for k in SECTION_HEAD:
        if d.get(k):
            return strip_number(d[k])
    return ""


# ---------------------------------------------------------------------------------------------------------------- body walk
def _walk(body: list, mark, level: int, out: list, base_indent: float, numbered: bool = True) -> None:
    """Nested list: a string is an item, a list right after it holds its children. Dict entries are special blocks."""
    entries = []  # (item_text_or_block, children)
    for x in body or []:
        if isinstance(x, list):
            if entries and isinstance(entries[-1][0], str):
                entries[-1] = (entries[-1][0], entries[-1][1] + x)
            else:
                entries.append((None, x))
        else:
            entries.append((x, []))
    n_items = sum(1 for e, _ in entries if isinstance(e, str))
    k = 0
    for e, kids in entries:
        if isinstance(e, str):
            m = mark(level, k) if (numbered and n_items > 1) else ""
            k += 1
            out.append(P(e, "body", "justify", base_indent + level * 1.0, m, level=level))
            if kids:
                _walk(kids, mark, level + 1, out, base_indent, numbered)
        elif isinstance(e, dict):
            out.extend(special(e, base_indent + level * 1.0))
        elif e is None and kids:
            _walk(kids, mark, level + 1, out, base_indent, numbered)


def table_block(tb: dict, kind="grid") -> dict:
    return {"t": "table", "columns": [str(c) for c in tb.get("columns") or []], "rows": [[str(c) for c in r] for r in tb.get("rows") or []],
            "widths": tb.get("widths"), "kind": tb.get("kind", kind), "caption": tb.get("caption", ""), "source": tb.get("source", ""),
            "unit": tb.get("unit", "")}


def special(e: dict, indent: float = 0.0) -> list:
    if "p" in e:
        return [P(e["p"], "body", e.get("align", "justify"), indent)]
    if "h" in e:
        return [P(e["h"], "heading", "left", 0, "", space_before=True)]
    if "note" in e:
        return [P(e["note"], "note", "left", indent)]
    if "table" in e:
        tb = table_block(e["table"])
        out = []
        if tb["unit"]:
            out.append(P(f"(단위: {tb['unit']})", "small", "right"))
        out.append(tb)
        if tb["source"]:
            out.append(P(f"자료: {tb['source']}", "small", "left"))
        return out
    if "box" in e:
        lines = [("□ " if not str(x).startswith(("□", "○", "-", "※")) else "") + str(x) for x in e["box"]]
        return [{"t": "table", "columns": [], "rows": [[e.get("label", "요약")], ["\n".join(lines)]], "widths": None, "kind": "box"}]
    if "space" in e:
        return [{"t": "space"}]
    if e.get("pagebreak") or e.get("page_break") or e.get("newpage"):
        return [{"t": "pagebreak"}]
    if "image" in e:
        return [{"t": "image", "file": str(e["image"]), "width_mm": float(e.get("width_mm") or 80), "caption": str(e.get("caption", "")), "align": e.get("align", "center")}]
    if "qr" in e:
        return [{"t": "qr", "url": str(e["qr"]), "size_mm": float(e.get("size_mm") or 28), "caption": str(e.get("caption", "")), "align": e.get("align", "center")}]
    if "form" in e:
        return form_blocks(e["form"] if isinstance(e["form"], dict) else {"fields": e["form"]})
    if any(k in e for k in SECTION_TEXT + ("items",)):   # a nested section-like object: keep its content
        out = [P(head_of(e), "heading", "left", 0, "", space_before=True)] if head_of(e) else []
        tmp: list = []
        _walk(body_of(e), gongmun_mark, 0, tmp, indent)
        return out + tmp
    _ISSUES.append("본문 칸 " + ", ".join(f"「{k}」" for k in e) + "을(를) 넣지 못했어요 (p · h · note · table · box 중 하나로)")
    return []


def form_rows(fields) -> list:
    """["학년 / 반", ["상담 방법", "□ 방문  □ 전화"]] -> [[label, value]] (an empty value = a blank to write in by hand)."""
    rows = []
    for f in fields or []:
        if isinstance(f, (list, tuple)):
            rows.append([str(f[0]), str(f[1]) if len(f) > 1 else ""])
        elif isinstance(f, dict):
            rows.append([str(f.get("label", "")), str(f.get("value", ""))])
        else:
            rows.append([str(f), ""])
    return rows


def form_blocks(fm: dict) -> list:
    out = []
    if fm.get("title"):
        out.append(P(fm["title"], "subtitle", "center"))
    out.append({"t": "table", "columns": [], "rows": form_rows(fm.get("fields")), "widths": fm.get("widths") or [0.34, 0.66], "kind": "form"})
    if fm.get("sign"):
        out.append(P(fm["sign"], "body", "right"))
    return out


# ---------------------------------------------------------------------------------------------------------------- unknowns
EXAMPLE_NOTE_DOC = "※ 날짜·장소·금액 등 일부 내용은 예시입니다. 확정된 내용으로 바꾼 뒤 이 줄을 지워 주세요."
_EX_NOTE = re.compile(r"예시(?:\s?(?:값|자료|수치|일정|내용))?\s?(?:입니다|이에요|예요|임(?![가-힣]))|가상\s?수치|예시[^\n]{0,30}(?:바꿔|바꾸|교체|확정|실제)")


def example_note(spec: dict) -> list:
    """The ONE example note of a document (CONTENT-RULES, 「Unknowns」): a small line at the foot of the body, only when the spec lists
    example values in "fillins". Not added when the spec already says it, when the user wants blanks, or with "example_note": false."""
    v = spec.get("example_note")
    fills = [x for x in (spec.get("fillins") or []) if str(x).strip()]
    if v is False or spec.get("template_blanks") is True or not fills:
        return []
    if isinstance(v, str) and v.strip():
        return [P(v.strip(), "note", "left")]
    if any(_EX_NOTE.search(x) for x in walk_strings(spec)):
        return []
    return [P(EXAMPLE_NOTE_DOC, "note", "left")]


# ---------------------------------------------------------------------------------------------------------------- kinds
def build(spec: dict) -> dict:
    """spec -> {"blocks": [...], "meta": {...}}"""
    kind = str(spec.get("kind") or "gongmun").lower()
    kind = {"공문": "gongmun", "기안문": "gongmun", "가정통신문": "notice", "통신문": "notice", "안내문": "guide", "안내": "guide",
            "보고서": "report", "계획서": "report", "결과보고서": "report"}.get(kind, kind)
    kind = {"신청서": "form", "동의서": "form", "회신서": "form", "양식": "form"}.get(kind, kind)
    fn = {"gongmun": _gongmun, "notice": _notice, "guide": _guide, "report": _report, "form": _form}.get(kind, _gongmun)
    _ISSUES.clear()
    blocks = fn(spec)
    issues = list(_ISSUES)
    design = spec.get("design") or {}
    try:
        line = float(design.get("line") or 1.6)
    except (TypeError, ValueError):
        line = 1.6
    return {"blocks": blocks, "meta": {"kind": kind, "title": str(spec.get("title", "")), "org": str(spec.get("org", "")),
                                       "date": gov_date(spec.get("date", "")), "font": design.get("font", "batang"),
                                       "scale": scale_of(spec), "line": min(2.2, max(1.2, line)), "issues": issues}}


def top_body(spec: dict) -> list:
    """The whole document's body: "body", or "items" / "text" / "table", or "sections" turned into headed groups (each heading numbered once)."""
    body = body_of({k: spec[k] for k in SECTION_TEXT + ("table", "notes") if k in spec})
    for i, sct in enumerate(spec.get("sections") or []):
        if isinstance(sct, dict):
            h = head_of(sct)
            if h:
                body.append(h)
                kids = body_of(sct, f"{i + 1}번째 절")
                if kids:
                    body.append(kids)
            else:
                body.extend(body_of(sct, f"{i + 1}번째 절"))
        elif isinstance(sct, (str, list)):
            body.append(sct)
    return body


def _end_mark(blocks: list, after: int | None = None) -> None:
    """Add `끝.` per 편람: two spaces after the last text; a separate line under a table that ends the body."""
    last = blocks[-1] if blocks else None
    if last is None:
        return
    if last["t"] == "table":
        blocks.append(P("  끝.", "body", "left", 0))
    elif last["t"] == "p" and not last["text"].rstrip().endswith("끝."):
        last["text"] = last["text"].rstrip() + "  끝."


def _attachments(att: list, indent: float = 0.0) -> list:
    out = []
    att = [str(a).rstrip(" .") + "." if not str(a).rstrip().endswith(".") else str(a) for a in att or []]
    if not att:
        return out
    if len(att) == 1:
        return [P(f"붙임  {att[0]}", "body", "left", indent, "", hang_text="붙임  ")]
    for i, a in enumerate(att):
        lead = "붙임  " if i == 0 else ""
        out.append(P(f"{lead}{i + 1}. {a}", "body", "left", indent if i == 0 else indent + 2.5, "", hang_text=lead))
    return out


def _gongmun(spec: dict) -> list:
    b: list = []
    if spec.get("org"):
        b.append(P(spec["org"], "org", "center"))
        b.append({"t": "space"})
    recv = str(spec.get("receiver") or "내부결재")
    b.append(P(f"수신  {recv}", "label", "left"))
    b.append(P(f"(경유)  {spec['via']}" if spec.get("via") else "(경유)", "label", "left"))
    b.append(P(f"제목  {spec.get('title', '')}", "label", "left"))
    b.append({"t": "rule"})
    body: list = []
    _walk(top_body(spec), gongmun_mark, 0, body, 0.0)
    b.extend(body)
    att = _attachments(spec.get("attachments") or [])
    if att:
        b.append({"t": "space"})
        b.extend(att)
    _end_mark(b)
    if recv != "내부결재" and spec.get("sender"):
        b.append({"t": "space"})
        b.append({"t": "space"})
        b.append(P(spec["sender"], "sender", "center"))
    if spec.get("receivers"):
        b.append(P("수신자  " + ", ".join(str(x) for x in spec["receivers"]), "small", "left"))
    ft = spec.get("footer") or {}
    if ft:
        b.append({"t": "rule"})
        for k in ("기안자", "검토자", "결재권자", "협조자"):
            if ft.get(k):
                b.append(P(f"{k} {ft[k]}", "small", "left"))
        line1 = "  ".join(f"{k} {ft[k]}" for k in ("시행", "접수") if ft.get(k))
        line2 = "  ".join(str(ft[k]) if k == "주소" else f"{k} {ft[k]}" for k in ("우", "주소", "홈페이지") if ft.get(k))
        line3 = "  ".join(f"{k} {ft[k]}" for k in ("전화", "전송", "전자우편", "공개구분") if ft.get(k))
        for ln in (line1, line2, line3):
            if ln:
                b.append(P(ln, "small", "left"))
    b.extend(example_note(spec))
    return b


def _notice(spec: dict) -> list:
    b: list = []
    top = "  ".join(x for x in (str(spec.get("org", "")), str(spec.get("number", ""))) if x)
    if top:
        b.append(P(top, "small", "left"))
    b.append(P(spec.get("heading") or "가정통신문", "title", "center"))
    if spec.get("title"):
        b.append(P(spec["title"], "subtitle", "center"))
    b.append({"t": "rule"})
    if spec.get("greeting"):
        b.append(P(spec["greeting"], "body", "justify"))
        b.append({"t": "space"})
    body: list = []
    _walk(top_body(spec), gongmun_mark, 0, body, 0.0)
    b.extend(body)
    b.extend(example_note(spec))
    b.append({"t": "space"})
    if spec.get("date"):
        b.append(P(gov_date(spec["date"]), "body", "center"))
    if spec.get("sender"):
        b.append(P(spec["sender"], "sender", "center"))
    b.extend(_reply(spec))
    return b


def _reply(spec: dict) -> list:
    """회신서 / 신청서: under a cut line (default) or on its own page ("page": true)."""
    rp = spec.get("reply")
    if not rp:
        return []
    b: list = []
    own_page = bool(rp.get("page"))
    if own_page:
        b.append({"t": "pagebreak"})
        if spec.get("org"):
            b.append(P(str(spec["org"]), "small", "center"))
        b.append(P(rp.get("title") or "회신서", "title", "center"))
        if rp.get("intro"):
            b.append(P(rp["intro"], "body", "justify"))
        b.append({"t": "space"})
    else:
        b.append({"t": "space"})
        b.append({"t": "cut"})
        b.append(P(rp.get("title") or "회신서", "subtitle", "center"))
    fields = rp.get("fields") or ["참가 여부 (□ 참가   □ 불참)"]
    b.append({"t": "table", "columns": [], "rows": form_rows(fields), "widths": rp.get("widths") or [0.38, 0.62], "kind": "form", "tall": own_page})
    for n in rp.get("notes") or []:
        b.append(P(str(n), "note", "left"))
    if own_page:
        b.append({"t": "space"})
        b.append(P(rp.get("statement") or "위와 같이 신청합니다.", "body", "center"))
        b.append(P(rp.get("date_line") or "년        월        일", "body", "center"))
    b.append(P(rp.get("sign") or "보호자 확인:                (서명)", "body", "right"))
    if spec.get("sender"):
        b.append(P(f"{spec['sender']} 귀하", "label", "center"))
    return b


def _form(spec: dict) -> list:
    """One-page 신청서 / 동의서 (kind "form"): title, short intro, a write-in table, statement, date line, signature, addressee."""
    b: list = []
    if spec.get("org"):
        b.append(P(str(spec["org"]), "small", "center"))
    b.append(P(spec.get("title", "신청서"), "title", "center"))
    if spec.get("intro"):
        b.append(P(spec["intro"], "body", "justify"))
    b.append({"t": "space"})
    b.append({"t": "table", "columns": [], "rows": form_rows(spec.get("fields")), "widths": spec.get("widths") or [0.3, 0.7], "kind": "form", "tall": True})
    body: list = []
    _walk(top_body(spec), gongmun_mark, 0, body, 0.0)
    b.extend(body)
    b.extend(example_note(spec))
    b.append({"t": "space"})
    b.append(P(spec.get("statement") or "위와 같이 신청합니다.", "body", "center"))
    b.append(P(gov_date(spec["date"]) if spec.get("date") else (spec.get("date_line") or "년        월        일"), "body", "center"))
    b.append(P(spec.get("sign") or "신청인(보호자):                    (서명)", "body", "right"))
    if spec.get("to") or spec.get("sender"):
        b.append({"t": "space"})
        b.append(P(f"{spec.get('to') or spec.get('sender')} 귀하", "sender", "center"))
    return b


def _guide(spec: dict) -> list:
    b: list = []
    if spec.get("org"):
        b.append(P(spec["org"], "small", "center"))
    b.append(P(spec.get("title", "안내"), "title", "center"))
    if spec.get("lead"):
        b.append({"t": "table", "columns": [], "rows": [[spec.get("lead_label", "한눈에")], [_txt(spec["lead"])]], "widths": None, "kind": "box"})
    b.append({"t": "space"})
    secs = spec.get("sections")
    if secs:
        pre: list = []
        _walk(body_of({k: spec[k] for k in SECTION_TEXT + ("table", "notes") if k in spec}), gongmun_mark, 0, pre, 0.0)
        b.extend(pre)
        for i, sct in enumerate(secs):
            sct = sct if isinstance(sct, dict) else {"body": sct if isinstance(sct, list) else [sct]}
            b.append(P(f"{i + 1}. {head_of(sct)}", "heading", "left", space_before=True))
            body: list = []
            _walk(body_of(sct, f"{i + 1}번째 절"), lambda lv, k: gongmun_mark(lv + 1, k), 0, body, 1.0)
            b.extend(body)
    else:
        body = []
        _walk(top_body(spec), gongmun_mark, 0, body, 0.0)
        b.extend(body)
    if spec.get("contact"):
        b.append({"t": "space"})
        b.append(P(f"※ 문의: {spec['contact']}", "note", "left"))
    b.extend(example_note(spec))
    if spec.get("date") or spec.get("sender"):
        b.append({"t": "space"})
        if spec.get("date"):
            b.append(P(gov_date(spec["date"]), "body", "center"))
        if spec.get("sender"):
            b.append(P(spec["sender"], "sender", "center"))
    b.extend(_reply(spec))
    return b


def _report(spec: dict) -> list:
    b: list = [{"t": "table", "columns": [], "rows": [[str(spec.get("title", "보고서"))]], "widths": None, "kind": "titlebox"}]
    meta = "  ".join(x for x in (gov_date(spec.get("date", "")), str(spec.get("dept", "")), str(spec.get("org", ""))) if x)
    if meta:
        b.append(P(meta, "small", "right"))
    if spec.get("summary"):
        b.append({"t": "space"})
        b.extend(special({"box": spec["summary"], "label": "요약"}))
    secs = spec.get("sections") or [{"h": "", "body": top_body(spec)}]
    for i, sct in enumerate(secs):
        sct = sct if isinstance(sct, dict) else {"body": sct if isinstance(sct, list) else [sct]}
        if head_of(sct):
            b.append(P(f"{ROMAN[i] if i < len(ROMAN) else i + 1}. {head_of(sct)}", "heading", "left", space_before=True))
        body: list = []
        _walk(body_of(sct, f"{i + 1}번째 절" if spec.get("sections") else ""), report_mark, 0, body, 0.0, numbered=True)
        for x in body:  # report marks are symbols: keep them even for a single item
            if x["t"] == "p" and x.get("level") is not None and not x["hang"]:
                x["hang"] = report_mark(x["level"], 0)
        b.extend(body)
    b.extend(example_note(spec))
    return b


# ---------------------------------------------------------------------------------------------------------------- text
def block_text(bl: dict) -> str:
    if bl["t"] == "p":
        return ((bl["hang"] + " ") if bl.get("hang") else "") + bl["text"]
    if bl["t"] == "table":
        return "\n".join(" | ".join(r) for r in ([bl["columns"]] if bl["columns"] else []) + bl["rows"])
    if bl["t"] in ("image", "qr"):
        return " ".join(x for x in (bl.get("caption", ""), bl.get("url", "")) if x)
    return ""


def plain_lines(model: dict) -> list[str]:
    out = []
    for bl in model["blocks"]:
        t = block_text(bl)
        if t:
            out.extend(t.replace("**", "").split("\n"))
    return out


CONTENT_SKIP = {"kind", "file", "template", "font", "mood", "date", "date_line", "sign", "statement", "fields", "widths", "align", "label",
                "lead_label", "heading", "number", "receiver", "via", "receivers", "sender", "to", "org", "dept", "footer", "attachments",
                "example_note", "fillins", "design", "reply", "url", "qr", "image", "caption", "kind", "style", "source", "unit"}


def content_strings(spec) -> list[str]:
    """The strings a reader must find in the finished file (titles, section text, items, table cells, notes, the lead box).
    Labels the builder rewrites (dates, signature lines, form fields, sender) are left out."""
    out: list[str] = []

    def w(v, key=""):
        if isinstance(v, str):
            if key not in CONTENT_SKIP and len(v.strip()) >= 2:
                out.append(strip_number(v) if key in SECTION_HEAD else v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in CONTENT_SKIP and not str(k).startswith("_"):
                    w(x, k)
        elif isinstance(v, list):
            for x in v:
                w(x, key)
    w(spec)
    return out


def _norm(t: str) -> str:
    return re.sub(r"[\s*·•□○◦\-–—|]+", "", str(t)).lower()


def missing_content(spec: dict, lines: list[str]) -> list[str]:
    """Spec strings that do not appear in the output text (whitespace and bullet marks ignored)."""
    hay = _norm("".join(lines))
    miss = []
    for s_ in content_strings(spec):
        n = _norm(s_)
        if len(n) >= 2 and n not in hay and s_ not in miss:
            miss.append(s_)
    return miss


def walk_strings(spec) -> list[str]:
    out: list[str] = []

    def w(v, key=""):
        if isinstance(v, str):
            if key not in ("kind", "file", "template", "font", "mood"):
                out.append(v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in ("fillins", "design", "example_note"):
                    w(x, k)
        elif isinstance(v, list):
            for x in v:
                w(x, key)
    w(spec)
    return out
