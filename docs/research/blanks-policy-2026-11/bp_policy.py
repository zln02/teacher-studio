#!/usr/bin/env python3
"""Policy counts for the blanks-policy eval: per output file, with the repo's own detectors (shared/tools/placeholders.py).

  filler      「확인 필요」「집계 필요」「미정」 ... in the text a reader sees (slides without speaker notes; document lines)
  stamp       「교사 초안」「배포 전 확인」 ... in that text
  slots       bracket / ○○ / 20XX placeholders in that text
  note        lines that say 「… 예시입니다 / 예시 자료(가상 수치) / 예시 … 바꿔 주세요」: on the page, and in speaker notes
  slip        (가정통신문, 안내문 + 신청서) a hand-filled part exists: a heading naming it followed by □ / (서명) / an underline
  body_blanks underline blanks before the slip (or anywhere, when there is no slip)
  listed      the maker's last message names what to replace (「바꿔 넣을 곳」, 「예시」 + 바꿔 / 확인 / 수정)

Called by bp_eval.py table -> policy.json next to this file + markdown on stdout.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "shared" / "tools"), str(REPO / "skills" / "teacher-docs" / "scripts")]
import placeholders as ph  # noqa: E402

SLIP_TASKS = ("hwpx-notice", "pdf-guide")
LISTED = re.compile(r"바꿔 넣을 곳|예시[^\n]{0,60}(?:바꿔|바꾸|확인|수정|교체)|(?:바꿔|바꾸|확인|수정|교체)[^\n]{0,60}예시|가정한|임의로")


def texts(f: Path, kind: str):
    """(seen lines, speaker-note lines)"""
    if kind == "pptx":
        from pptx import Presentation
        seen, notes = [], []

        def walk(shapes):
            for sh in shapes:
                if sh.shape_type == 6:
                    yield from walk(sh.shapes)
                    continue
                if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
                    yield sh.text_frame.text or ""
                if getattr(sh, "has_table", False) and sh.has_table:
                    for r in sh.table.rows:
                        for c in r.cells:
                            yield c.text_frame.text or ""
        for s in Presentation(str(f)).slides:
            seen += [ln for t in walk(s.shapes) for ln in t.split("\n")]
            if s.has_notes_slide:
                notes += (s.notes_slide.notes_text_frame.text or "").split("\n")
        return seen, notes
    if kind == "hwpx":
        try:
            import hwpx_edit
            return list(hwpx_edit.text(f)), []
        except Exception:  # a hand-made hwpx our reader cannot walk: every <hp:t> run, one line per paragraph
            out = []
            with zipfile.ZipFile(f) as z:
                for n in sorted(z.namelist()):
                    if re.match(r"Contents/section\d+\.xml$", n):
                        x = z.read(n).decode("utf-8", "replace")
                        for p in re.findall(r"<hp:p[ >].*?</hp:p>", x, re.S):
                            out.append("".join(re.findall(r"<hp:t(?: [^>]*)?>([^<]*)</hp:t>", p)))
            return out, []
    if kind == "pdf":
        from pypdf import PdfReader
        return [ln.replace("\xa0", " ") for pg in PdfReader(str(f)).pages for ln in (pg.extract_text() or "").split("\n")], []
    return [], []


def one(f: Path, kind: str, task: str, last: str) -> dict:
    seen, notes = texts(f, kind)
    cut = ph.slip_start(seen)
    return dict(filler=len(ph.fillers(seen)), stamp=len(ph.stamps(seen)), slots=len([m for ln in seen for m in ph.find(ln)]),
                note_page=ph.example_notes(seen), note_notes=ph.example_notes(notes),
                slip=(cut < len(seen)) if task in SLIP_TASKS else None,
                body_blanks=sum(1 for ln in seen[:cut] if ph.UNDERLINE.search(ln)),
                listed=bool(LISTED.search(last or "")), lines=len(seen))


def main(X: Path, e, here: Path) -> None:
    rows = []
    for jd in sorted((X / "runs").iterdir()):
        if not (jd / "state.json").exists():
            continue
        st = json.loads((jd / "state.json").read_text(encoding="utf-8"))
        kind = e.TASKS[st["task"]]["kind"]
        f = jd / ("out." + kind)
        r = dict(task=st["task"], maker=st["vendor"], cond=st["cond"], run=st["run"], file=bool(st.get("file")))
        if f.exists():
            try:
                r.update(one(f, kind, st["task"], st.get("last", "")))
            except Exception as ex:  # noqa: BLE001
                r["error"] = repr(ex)[:200]
        rows.append(r)
    agg = {}
    for v, c in e.CONDS:
        rs = [r for r in rows if (r["maker"], r["cond"]) == (v, c)]
        ok = [r for r in rs if "filler" in r]
        slip = [r for r in ok if r["slip"] is not None]
        expected_slip = sum(1 for r in rs if r["task"] in SLIP_TASKS)
        agg[f"{v}-{c}"] = dict(runs=len(rs), files=len(ok), filler_total=sum(r["filler"] for r in ok), files_with_filler=sum(r["filler"] > 0 for r in ok),
                               stamp_files=sum(r["stamp"] > 0 for r in ok), slot_total=sum(r["slots"] for r in ok),
                               slip_expected=expected_slip, slip_present=sum(bool(r["slip"]) for r in slip), slip_missing=expected_slip - sum(bool(r["slip"]) for r in slip),
                               note_present=sum((r["note_page"] + r["note_notes"]) > 0 for r in ok), note_exactly_one=sum((r["note_page"] + r["note_notes"]) == 1 for r in ok),
                               note_repeated_on_page=sum(r["note_page"] > 1 for r in ok), body_blank_files=sum(r["body_blanks"] > 0 for r in ok),
                               listed_in_last_message=sum(r["listed"] for r in ok))
    (here / "policy.json").write_text(json.dumps(dict(summary=agg, runs=rows), ensure_ascii=False, indent=1), encoding="utf-8")
    P = print
    P("\n## policy counts (our detectors on the final files)")
    P("| condition | files | filler phrases (files with any) | draft stamp files | slots | reply slip present / expected | example note present | exactly one | repeated on the page | body underline blanks (files) | last message lists what to replace |")
    P("|---|---|---|---|---|---|---|---|---|---|---|")
    for k, a in agg.items():
        P(f"| {k} | {a['files']}/{a['runs']} | {a['filler_total']} ({a['files_with_filler']}) | {a['stamp_files']} | {a['slot_total']} | {a['slip_present']}/{a['slip_expected']} | "
          f"{a['note_present']} | {a['note_exactly_one']} | {a['note_repeated_on_page']} | {a['body_blank_files']} | {a['listed_in_last_message']} |")
    for r in rows:
        P(r)
