#!/usr/bin/env python3
"""Leftovers re-test (2026-11-21): ONLY the cells the fixes touch, with the same code as the two rounds before
(docs/research/cross-vendor-2026-11/xv_eval.py through docs/research/blanks-policy-2026-11/bp_eval.py).

  py lo_eval.py setup            fresh skills via scripts/setup.py (redirected home) + the unchanged runs of the blanks round copied in
  py lo_eval.py run STAGE        STAGE = rerun  : Claude 가정통신문 run 2 (harness) + GPT 공공 보고 PPT runs 1, 2 (harness)
                                         color  : fresh lower-elementary class PPT with colour words, 4 conditions x 2 runs
                                         game   : fresh review game, 4 conditions x 2 runs
  py lo_eval.py render           draw every new output (one browser at a time) + our gates
  py lo_eval.py judge opus|gpt [task...]   blind A-D, 2 passes (order changed)
  py lo_eval.py table            numbers -> table.json + checks.json here
  py lo_eval.py collect          states, final files, gate results, judge records -> raw/ here

Re-run cells replace only their own run folder; the other three outputs a judge sees next to them (bare Claude, bare GPT, the other
vendor's harness run) are the files of the blanks round, copied unchanged and judged again blind (four outputs are always scored together).
Launch flags are the restricted ones of the earlier rounds: claude -p --permission-mode acceptEdits + allow list + install deny list;
codex exec -s workspace-write (network off), isolated CODEX_HOME with [windows] sandbox = "unelevated"; at most 2 makers or judges at a
time and never two `claude -p` at once; one browser at a time. Codex work folders: C:\\Users\\User\\Downloads\\xv-eval-work\\leftovers\\ (deleted after the round).
Nothing in the owner's ~/.claude, ~/.codex, ~/.agents is written.
"""
import json, os, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "blanks-policy-2026-11"))
_argv, sys.argv = sys.argv, ["x"]
import bp_eval as bp  # noqa: E402  (sets up xv_eval as bp.e)
sys.argv = _argv
e, orch, S = bp.e, bp.orch, bp.S

PREV = S / "xv3"                       # the blanks round (source of the unchanged runs)
NEW = S / "xv4"
bp.NEW = NEW
bp.CFG_HARNESS = S / "cfg-harness4"
e.X = NEW
orch.LOG = NEW / "eval.log"
e.CODEX_WORK = Path(r"C:\Users\User\Downloads\xv-eval-work") / "leftovers"
BLANKS = dict(bp.e.TASKS)
e.TASKS = {
    "hwpx-notice": BLANKS["hwpx-notice"],   # same sentence as the blanks round
    "public-ppt": BLANKS["public-ppt"],     # same sentence as the blanks round
    # two topics not used in this repo's evals, fixtures or docs (git grep before any run), fixed before any run
    "color-ppt": dict(kind="pptx", name="저학년 수업 PPT(색 낱말)", p="초등학교 2학년 안전한 생활 '신호등 색깔과 교통안전 표지판' 수업용 PPT 만들어 줘 (8장, 파워포인트 파일로)"),
    "game": dict(kind="html", name="복습 게임", p="초등학교 4학년 사회 '우리 지역의 공공 기관' 복습 게임 만들어 줘"),
}
# one `claude -p` at a time (another agent on this PC uses the same login); a Codex run may still go beside it, so at most 2 processes
_CLAUDE_ONE = __import__("threading").Lock()
_bp_claude = e.claude


def _claude_one(*a, **kw):
    with _CLAUDE_ONE:
        return _bp_claude(*a, **kw)


e.claude = _claude_one
RERUN = [("hwpx-notice", "claude", "harness", 2), ("public-ppt", "codex", "harness", 1), ("public-ppt", "codex", "harness", 2)]
JUDGE_UNITS = {"hwpx-notice": [2], "public-ppt": [1, 2], "color-ppt": [1, 2], "game": [1, 2]}
STAGES = {
    "rerun": RERUN,
    "color": [("color-ppt", v, c, n) for n in (1, 2) for v, c in e.CONDS],
    "game": [("game", v, c, n) for n in (1, 2) for v, c in e.CONDS],
    # second pass of the colour deck, studio condition only: the first pass showed two gaps (an emphasised colour word kept the deck's
    # accent colour; a hand-made deck was not checked for it), both fixed, skills installed again, these four cells made again
    "color2": [("color-ppt", v, "harness", n) for n in (1, 2) for v in ("claude", "codex")],
}


def cmd_pass1():
    """Set the first-pass studio colour decks aside (kept in raw/pass1) before they are made again."""
    dst = NEW / "pass1"
    dst.mkdir(exist_ok=True)
    for t, v, c, n in STAGES["color2"]:
        jd = NEW / "runs" / f"{t}-{v}-{c}-{n}"
        if jd.exists() and not (dst / jd.name).exists():
            shutil.move(str(jd), str(dst / jd.name))
            print("pass1 <-", jd.name)


def cmd_setup():
    bp.cmd_setup()
    rerun = {f"{t}-{v}-{c}-{n}" for t, v, c, n in RERUN}
    for task, runs in (("hwpx-notice", [2]), ("public-ppt", [1, 2])):
        for n in runs:
            for v, c in e.CONDS:
                name = f"{task}-{v}-{c}-{n}"
                src, dst = PREV / "runs" / name, NEW / "runs" / name
                if name in rerun or dst.exists() or not src.exists():
                    continue
                dst.mkdir(parents=True)
                for p in src.iterdir():
                    if p.is_file() and (p.name in ("state.json", "render.json", "autocheck.json") or p.name.startswith("out")):
                        shutil.copy2(p, dst / p.name)
                if (src / "render").is_dir():
                    shutil.copytree(src / "render", dst / "render")
                (dst / "_reused.txt").write_text("copied unchanged from the blanks round (xv3)", encoding="utf-8")
                print("reused", name)


def cmd_judge(judge, tasks):
    jobs = [(t, n, pn) for t in tasks for n in JUDGE_UNITS[t] for pn in (1, 2)]
    return e.pool(lambda *a: e.judge_one(judge, *a), jobs)


def _scores():
    """{(task, run, 'vendor-cond'): {judge: mean of 4 items over the 2 passes}} + per-item means."""
    out = {}
    for j in ("opus", "gpt"):
        for f in sorted((NEW / "judge" / j).glob("*-pass*.json")):
            rec = json.loads(f.read_text(encoding="utf-8"))
            for lab, who in rec["mapping"].items():
                r = rec["result"][lab]
                d = out.setdefault((rec["task"], rec["run"], who), {}).setdefault(j, {"n": 0, **{k: 0.0 for k in e.KEYS}, "notes": []})
                d["n"] += 1
                for k in e.KEYS:
                    d[k] += float(r[k])
                d["notes"].append(str(r.get("note", ""))[:300])
    return out


def cmd_table():
    sc = _scores()
    rows = []
    for (task, run, who), js in sorted(sc.items()):
        row = {"task": task, "run": run, "who": who}
        allm = []
        for j, d in js.items():
            m = sum(d[k] for k in e.KEYS) / (4 * d["n"])
            row[j] = round(m, 2)
            row[j + "_items"] = {k: round(d[k] / d["n"], 2) for k in e.KEYS}
            row[j + "_notes"] = d["notes"]
            allm.append(m)
        row["mean"] = round(sum(allm) / len(allm), 2) if allm else None
        stf = NEW / "runs" / f"{task}-{who}-{run}" / "state.json"
        if stf.exists():
            st = json.loads(stf.read_text(encoding="utf-8"))
            row.update(secs=st.get("secs"), cost=st.get("cost"), file=st.get("file"), denials=len(st.get("denials") or []), failed_cmds=st.get("failed_cmds"),
                       reused=(stf.parent / "_reused.txt").exists())
        rows.append(row)
    summary = {}
    for task in e.TASKS:
        for vendor in ("claude", "codex"):
            b = [r["mean"] for r in rows if r["task"] == task and r["who"] == f"{vendor}-bare" and r["mean"] is not None]
            h = [r["mean"] for r in rows if r["task"] == task and r["who"] == f"{vendor}-harness" and r["mean"] is not None]
            if b and h:
                summary[f"{task}|{vendor}"] = {"bare": round(sum(b) / len(b), 2), "harness": round(sum(h) / len(h), 2), "diff": round(sum(h) / len(h) - sum(b) / len(b), 2),
                                               "runs": len(h), "harness_runs": h, "bare_runs": b}
    (HERE / "table.json").write_text(json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in summary.items():
        print(k, v)


def cmd_collect():
    raw = HERE / "raw"
    for jd in sorted((NEW / "runs").iterdir()):
        if not (jd / "state.json").exists() or (jd / "_reused.txt").exists():
            continue
        dst = raw / "runs" / jd.name
        dst.mkdir(parents=True, exist_ok=True)
        for p in jd.iterdir():
            if p.is_file() and (p.name in ("state.json", "render.json", "autocheck.json") or p.name.startswith("out")):
                shutil.copy2(p, dst / p.name)
    for jd in sorted((NEW / "pass1").glob("*")) if (NEW / "pass1").exists() else []:
        dst = raw / "pass1" / jd.name
        dst.mkdir(parents=True, exist_ok=True)
        for p in jd.iterdir():
            if p.is_file() and (p.name == "state.json" or p.name.startswith("out")):
                shutil.copy2(p, dst / p.name)
    for j in ("opus", "gpt"):
        (raw / "judge" / j).mkdir(parents=True, exist_ok=True)
        for f in (NEW / "judge" / j).glob("*-pass*.json"):
            shutil.copy2(f, raw / "judge" / j / f.name)
    print("collected ->", raw)


if __name__ == "__main__":
    a = sys.argv[1:]
    c = a[0] if a else ""
    if c == "setup":
        cmd_setup()
    elif c == "run":
        sys.exit(e.pool(e.run_one, STAGES[a[1]]))
    elif c == "pass1":
        cmd_pass1()
    elif c == "render":
        e.cmd_render()
    elif c == "judge":
        sys.exit(cmd_judge(a[1], a[2:] or list(e.TASKS)))
    elif c == "table":
        cmd_table()
    elif c == "collect":
        cmd_collect()
    else:
        print(__doc__)
