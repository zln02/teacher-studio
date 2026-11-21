#!/usr/bin/env python3
"""What our gates count on the new outputs -> checks.json here (read by lo_plot.py and the document).

  py lo_checks.py     (after lo_eval.py render)

- interpreter: commands refused because Python was called by full path (the Claude 가정통신문 failure of the blanks round)
- one note   : on-screen example notes in the GPT report decks (the blanks round had 7-8 per deck)
- page count : slides in each 「8장」 deck
- colour     : short labels that name a colour (초록불 · 빨간불 · 노란불 ...) and whether their fill or text is that colour
- html policy: the unknowns gate (filler · draft stamp · slots · repeated note) on every game file
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
_argv, sys.argv = sys.argv, ["x"]
import lo_eval as lo  # noqa: E402
sys.argv = _argv
REPO = lo.e.REPO
sys.path.insert(0, str(REPO / "shared" / "design"))
sys.path.insert(0, str(REPO / "shared" / "tools"))
import meaning  # noqa: E402
import placeholders as ph  # noqa: E402

RUNS = lo.NEW / "runs"
PY_PATH = re.compile(r"python[0-9.]*\.exe|[\\/]python3?(?:\s|\"|'|$)", re.I)


def near(a: str, b: str) -> bool:
    ha, hb = meaning._hue(a), meaning._hue(b)
    if ha is None or hb is None:
        return ha is None and hb is None and abs(meaning._lum(a) - meaning._lum(b)) < 0.3
    d = abs(ha - hb) % 360
    return min(d, 360 - d) <= 35


def vivid(c: str) -> bool:
    """A colour of its own (not the deck's dark ink, which often carries a little navy or brown)."""
    r, g, b = meaning._rgb(c)
    return meaning._hue(c) is not None and (max(r, g, b) - min(r, g, b)) >= 76


def colour_labels(pptx: Path) -> dict:
    """Shapes whose whole text is a short label naming one colour: right = its fill or its text is that colour, wrong = another clear hue,
    plain = no colour of its own (black text, no fill)."""
    from pptx import Presentation
    out = {"labels": 0, "right": 0, "wrong": 0, "plain": 0, "wrong_examples": []}
    for i, sl in enumerate(Presentation(str(pptx)).slides, 1):
        for sh in sl.shapes:
            if not getattr(sh, "has_text_frame", False):
                continue
            for para in sh.text_frame.paragraphs:
                runs = [r for r in para.runs if r.text.strip()]
                for r in runs:
                    t = r.text.strip()
                    want = meaning.color_of(t)
                    if not want or len(t) > 12:
                        continue
                    cols = []
                    try:
                        if r.font.color and r.font.color.type is not None and r.font.color.rgb is not None:
                            cols.append("#" + str(r.font.color.rgb))
                    except Exception:
                        pass
                    try:
                        if sh.fill.type == 1 and len(runs) == 1:
                            cols.append("#" + str(sh.fill.fore_color.rgb))
                    except Exception:
                        pass
                    hued = [c for c in cols if vivid(c)]
                    out["labels"] += 1
                    if any(near(c, want) for c in cols if vivid(c) or meaning._hue(want) is None):
                        out["right"] += 1
                    elif hued:
                        out["wrong"] += 1
                        out["wrong_examples"].append(f"{i}장 「{t}」 {hued[0]}")
                    else:
                        out["plain"] += 1
    out["wrong_examples"] = out["wrong_examples"][:4]
    return out


def deck_note_count(pptx: Path) -> dict:
    from pptx import Presentation
    body, notes = [], []
    prs = Presentation(str(pptx))
    for sl in prs.slides:
        for sh in sl.shapes:
            if getattr(sh, "has_text_frame", False):
                body.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                body += [c.text for row in sh.table.rows for c in row.cells]
        if sl.has_notes_slide:
            notes.append(sl.notes_slide.notes_text_frame.text)
    return {"slides": len(prs.slides), "on_screen_notes": ph.example_notes(body), "speaker_notes": ph.example_notes(notes), "fillers": len(ph.fillers(body)), "stamps": len(ph.stamps(body))}


def main():
    res = {"runs": {}}
    for jd in sorted(RUNS.iterdir()):
        stf = jd / "state.json"
        if not stf.exists():
            continue
        st = json.loads(stf.read_text(encoding="utf-8"))
        row = {"reused": (jd / "_reused.txt").exists(), "file": bool(st.get("file")), "secs": st.get("secs"),
               "path_denials": sum(1 for _t, c in (st.get("denials") or []) if PY_PATH.search(str(c).split(" ")[0] + " " + " ".join(str(c).split(" ")[:2]))),
               "denials": len(st.get("denials") or [])}
        kind = lo.e.TASKS[st["task"]]["kind"]
        out = jd / ("out" + lo.orch.EXT[kind])
        if out.exists():
            if kind == "pptx":
                row.update(deck_note_count(out))
                if st["task"] == "color-ppt":
                    row["colour"] = colour_labels(out)
            elif kind == "html":
                r = ph.html_checks(out.read_text(encoding="utf-8", errors="replace"))
                row["html_policy"] = {"fail": [m[:90] for l, m in r if l == "FAIL"], "warn": [m[:90] for l, m in r if l == "WARN"]}
            ac = jd / "autocheck.json"
            if ac.exists():
                try:
                    row["gate"] = json.loads(ac.read_text(encoding="utf-8")).get("result") or json.loads(ac.read_text(encoding="utf-8")).get("status")
                except ValueError:
                    pass
        res["runs"][jd.name] = row
    R = res["runs"]

    def g(name, *keys, default=None):
        v = R.get(name, {})
        for k in keys:
            v = v.get(k, {}) if isinstance(v, dict) else {}
        return v if v != {} else default

    lines = []
    h = "hwpx-notice-claude-harness-2"
    if h in R:
        lines.append(f"Claude 가정통신문 2회차: 파일 {'나옴' if R[h]['file'] else '없음'} ({R[h]['secs']}초), Python을 전체 경로로 불러 막힌 명령 {R[h]['path_denials']}개")
    pp = [n for n in ("public-ppt-codex-harness-1", "public-ppt-codex-harness-2") if n in R and "on_screen_notes" in R[n]]
    if pp:
        lines.append("GPT 공공 보고 PPT: 화면의 예시 안내 " + " · ".join(f"{R[n]['on_screen_notes']}번" for n in pp) + " (지난 측정 7~8번), 「확인 필요」 " + " · ".join(str(R[n]["fillers"]) for n in pp) + "곳")
    for vendor, lab in (("claude", "Claude"), ("codex", "GPT")):
        for cond, cl in (("bare", "일반"), ("harness", "스튜디오")):
            ns = [n for n in (f"color-ppt-{vendor}-{cond}-1", f"color-ppt-{vendor}-{cond}-2") if n in R and "slides" in R[n]]
            if ns:
                c = [R[n].get("colour") or {} for n in ns]
                lines.append(f"{lab} {cl} 저학년 PPT(8장 요청): " + " · ".join(f"{R[n]['slides']}장" for n in ns) + ", 다른 색으로 칠한 색 낱말 "
                             + " · ".join(f"{x.get('wrong', 0)}곳" for x in c) + " (제 색 " + " · ".join(str(x.get("right", 0)) for x in c) + ")")
    p1 = {}
    for jd in sorted((lo.NEW / "pass1").glob("color-ppt-*")) if (lo.NEW / "pass1").exists() else []:
        if (jd / "out.pptx").exists():
            p1[jd.name] = {**deck_note_count(jd / "out.pptx"), "colour": colour_labels(jd / "out.pptx")}
    res["pass1"] = p1
    if p1:
        lines.append("스튜디오 저학년 PPT 첫 회(고치기 전 설치본): 다른 색으로 칠한 색 낱말 " + " · ".join(f"{v['colour']['wrong']}곳" for v in p1.values()) + " (Claude 2 · GPT 2 순)")
    gm = [n for n in R if n.startswith("game-") and "html_policy" in R[n]]
    if gm:
        for cond, cl in (("bare", "일반"), ("harness", "스튜디오")):
            ns = [n for n in gm if f"-{cond}-" in n]
            lines.append(f"게임 {cl} {len(ns)}개: 빈말·도장·빈자리 FAIL {sum(1 for n in ns if R[n]['html_policy']['fail'])}개, WARN {sum(1 for n in ns if R[n]['html_policy']['warn'])}개")
    res["lines"] = lines
    short = []
    if h in R:
        short.append(f"가정통신문(Claude 2회차): 파일 {'나옴' if R[h]['file'] else '없음'}, 전체 경로 호출로 막힌 명령 {R[h]['path_denials']}개")
    if pp:
        short.append("보고 PPT(GPT 2개): 화면의 예시 안내 " + " · ".join(str(R[n]["on_screen_notes"]) for n in pp) + "번 (지난 측정 7~8번)")
    cp = [n for n in R if n.startswith("color-ppt-") and "slides" in R[n]]
    if cp:
        short.append(f"「8장」 요청 PPT {len(cp)}개(일반·스튜디오): " + ("모두 8장" if all(R[n]["slides"] == 8 for n in cp) else " · ".join(str(R[n]["slides"]) for n in cp) + "장"))
        hs = [n for n in cp if "-harness-" in n]
        bs = [n for n in cp if "-bare-" in n]
        short.append("다른 색으로 칠한 색 낱말(스튜디오 4개): " + (" · ".join(str(v["colour"]["wrong"]) for v in p1.values()) + "곳 → " if p1 else "")
                     + " · ".join(str(R[n]["colour"]["wrong"]) for n in hs) + "곳")
        short.append("  같은 셈으로 일반 AI 4개: " + " · ".join(str(R[n]["colour"]["wrong"]) for n in bs) + "곳")
    if gm:
        short.append(f"게임 {len(gm)}개(일반·스튜디오): 빈말·도장·빈자리 FAIL {sum(1 for n in gm if R[n]['html_policy']['fail'])}개 · WARN {sum(1 for n in gm if R[n]['html_policy']['warn'])}개")
    res["short"] = short
    (HERE / "checks.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
