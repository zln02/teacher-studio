#!/usr/bin/env python3
"""Young-room lesson PPT re-test (2026-11-21): did the harness fix close the one cell where Claude with the studio lost to bare Claude?

  py yp_eval.py setup            fresh skills (scripts/setup.py into a redirected home) -> the skills/ folder of the isolated Claude config
                                 (cfg-harness4) and of the isolated Codex home (xv4/codex-harness). No login file is copied anywhere.
  py yp_eval.py run              Claude studio vs bare x2 on the tuned topic and on a fresh topic + GPT studio x1 on the tuned topic
  py yp_eval.py render           draw every new output (one browser at a time) + our gates
  py yp_eval.py judge opus|gpt   blind, labels shuffled and swapped between the 2 passes
  py yp_eval.py table            numbers -> table.json here
  py yp_eval.py collect          states, final files, gate results, judge records -> raw/ here

Same code and launch flags as the three rounds before (docs/research/leftovers-2026-11/lo_eval.py <- blanks-policy <- cross-vendor):
claude -p --permission-mode acceptEdits + allow list (py / python / python3 / node and their full paths) + install deny list;
codex exec -s workspace-write (network off), isolated CODEX_HOME with [windows] sandbox = "unelevated". Never bypassPermissions.
One `claude -p` at a time (makers and the Opus judge alike), a Codex run may go beside it; one browser at a time.
Login: the isolated config folders made in the earlier rounds are used as they are. The earlier rounds refreshed them from the
owner's ~/.claude (orch.sync_creds); that copy is switched off here, so a failed login stops the round instead.
Codex work folders: C:\\Users\\User\\Downloads\\xv-eval-work\\young\\ (deleted after the round).

Judged units (A-D or A-B, labels shuffled per unit, reversed and rotated for pass 2):
  tuned topic, run 1: Claude bare (new), Claude studio (new), GPT studio (new), GPT bare (leftovers run 1 file, unchanged)
  tuned topic, run 2: Claude bare (new), Claude studio (new), GPT studio + GPT bare (leftovers run 2 files, unchanged: old skills)
  fresh topic, runs 1 and 2: Claude bare (new), Claude studio (new)
"""
import json, random, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "leftovers-2026-11"))
_argv, sys.argv = sys.argv, ["x"]
import lo_eval as lo  # noqa: E402  (sets up bp_eval as lo.bp, xv_eval as lo.e)
sys.argv = _argv
e, orch, S, bp = lo.e, lo.orch, lo.S, lo.bp

orch.sync_creds = lambda: None   # never copy a login file (owner's or between configs); an expired login stops the round
OLD = S / "xv4"                  # the leftovers round: its isolated Codex homes and its unchanged GPT files
NEW = S / "xv5"
e.X = NEW
orch.LOG = NEW / "eval.log"
e.CODEX_WORK = Path(r"C:\Users\User\Downloads\xv-eval-work") / "young"
bp.CFG_HARNESS = S / "cfg-harness4"
e.TASKS = {
    "color-ppt": lo.e.TASKS["color-ppt"],  # the tuned topic: same sentence as the leftovers round
    # fresh topic, never used in this repo's evals, fixtures or docs (git grep before any run), fixed before any run
    "safety-sign-ppt": dict(kind="pptx", name="저학년 수업 PPT(새 주제)", p="초등학교 1학년 안전한 생활 '학교에서 만나는 안전 표지와 색깔' 수업용 PPT 만들어 줘 (10장 정도, 파워포인트 파일로)"),
}
_codex = e.codex
# the Codex homes of the leftovers round (their own login file stays where it is; nothing is copied)
e.codex = lambda prompt, home, cwd, **kw: _codex(prompt, OLD / Path(home).name if Path(home).parent == NEW else home, cwd, **kw)

RUNS = [("color-ppt", "claude", c, n) for n in (1, 2) for c in ("harness", "bare")] + [("color-ppt", "codex", "harness", 1)] \
    + [("safety-sign-ppt", "claude", c, n) for n in (1, 2) for c in ("harness", "bare")]
UNITS = {("color-ppt", 1): ["claude-bare", "claude-harness", "codex-bare", "codex-harness"],
         ("color-ppt", 2): ["claude-bare", "claude-harness", "codex-bare", "codex-harness"],
         ("safety-sign-ppt", 1): ["claude-bare", "claude-harness"], ("safety-sign-ppt", 2): ["claude-bare", "claude-harness"]}
REUSED = ["color-ppt-codex-bare-1", "color-ppt-codex-bare-2", "color-ppt-codex-harness-2"]


def cmd_setup():
    NEW.mkdir(exist_ok=True)
    (NEW / "runs").mkdir(exist_ok=True)
    for h in (NEW / "home-codex", NEW / "home-claude"):
        if h.exists():
            shutil.rmtree(h)
    bp.copy_skills(bp.install("codex", NEW / "home-codex"), OLD / "codex-harness" / "skills")
    bp.copy_skills(bp.install("claude-code", NEW / "home-claude"), bp.CFG_HARNESS / "skills")
    for name in REUSED:
        src, dst = OLD / "runs" / name, NEW / "runs" / name
        if dst.exists() or not src.exists():
            continue
        dst.mkdir(parents=True)
        for p in src.iterdir():
            if p.is_file() and (p.name in ("state.json", "render.json", "autocheck.json") or p.name.startswith("out")):
                shutil.copy2(p, dst / p.name)
        if (src / "render").is_dir():
            shutil.copytree(src / "render", dst / "render")
        (dst / "_reused.txt").write_text("copied unchanged from the leftovers round (xv4): made with the skills before this fix", encoding="utf-8")
        print("reused", name)
    e.CODEX_WORK.mkdir(parents=True, exist_ok=True)


def judge_one(judge, task, n, pn):
    jd = NEW / "judge" / judge / f"{task}-{n}-pass{pn}"
    resf = NEW / "judge" / judge / f"{task}-{n}-pass{pn}.json"
    if resf.exists():
        return json.loads(resf.read_text(encoding="utf-8"))
    conds = UNITS[(task, n)][:]
    random.Random(f"yp-{task}-{n}").shuffle(conds)  # same label order for both judges
    if pn == 2:  # swapped: reversed and rotated, so no output keeps its label or its place
        conds = conds[::-1]
        conds = conds[1:] + conds[:1]
    if jd.exists():
        shutil.rmtree(jd)
    jd.mkdir(parents=True)
    kind = e.TASKS[task]["kind"]
    labs = "ABCD"[:len(conds)]
    files, mapping = [], {}
    for lab, who in zip(labs, conds):
        mapping[lab] = who
        ps = e.out_pngs(NEW / "runs" / f"{task}-{who}-{n}", kind)[:12]
        for k in range(0, max(len(ps), 1), 6):
            fn = f"{lab}{'' if k == 0 else k // 6 + 1}.png"
            e.montage(ps[k:k + 6], jd / fn, label=lab + ("" if k == 0 else f" ({k // 6 + 1})"))
            files.append(fn)
    if judge == "opus":
        how = f"현재 폴더에 {', '.join(files)} 가 있어. Read 도구로 모두 직접 열어서 봐."
    else:
        how = f"이 메시지에 그림 {len(files)}장이 붙어 있어 ({', '.join(files)} 순서). 모두 봐."
    prompt = e.JUDGE.format(req=e.TASKS[task]["p"], how=how, fmt=e.FMT[kind])
    if len(conds) != 4:
        out_tpl = "{" + ",".join(f'"{l}":{{"content":0,"design":0,"readability":0,"fit":0,"note":"..."}}' for l in labs) + ',"ranking":[' + ",".join(f'"{i + 1}위"' for i in range(len(labs))) + "]}"
        prompt = (prompt.replace("서로 다른 4곳(A, B, C, D)", f"서로 다른 {len(labs)}곳({', '.join(labs)})").replace("(A~D)", f"({labs[0]}~{labs[-1]})")
                  .replace("1위부터 4위까지", f"1위부터 {len(labs)}위까지"))
        prompt = prompt[:prompt.index("[출력]")] + "[출력] 마지막 답변은 JSON 하나만 (코드블록·다른 말 없이):\n" + out_tpl + "\n"
    (jd / "_prompt.txt").write_text(prompt, encoding="utf-8")
    if judge == "opus":
        r = e.claude(prompt, "opus", S / "cfg-reviewer", jd, cap=900, mode="default", allow=e.ALLOW_JUDGE, deny=e.DENY_JUDGE)
        d = r["data"] or {}
        res = str(d.get("result", ""))
        if (d.get("is_error") or not d) and e.is_limit(res + r.get("err", "")):
            raise RuntimeError(f"LOGIN/LIMIT opus judge: {(res or r.get('err', ''))[:200]}")
        cost, secs = orch.usage_of(d)["cost"], r["secs"]
    else:
        r = e.codex(prompt, NEW / "codex-bare", jd, sandbox="read-only", images=[jd / f for f in files], cap=900)
        res = r["result"]
        if r["errors"] and e.is_limit(" ".join(r["errors"])) and not res:
            raise RuntimeError(f"LOGIN/LIMIT gpt judge: {r['errors'][0][:300]}")
        cost, secs = None, r["secs"]
    j = orch.extract_json(res)
    ok = bool(j) and all(isinstance(j.get(l), dict) and all(k in j[l] for k in e.KEYS) for l in labs)
    rec = dict(judge=judge, task=task, run=n, pass_=pn, mapping=mapping, result=j, cost=cost, secs=round(secs), raw=res[:2500])
    if ok:
        resf.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print("judged", judge, task, n, pn, ok, flush=True)
    return rec


def cmd_table():
    lo.NEW = NEW
    sc = lo._scores()
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
            row.update(secs=st.get("secs"), cost=st.get("cost"), file=st.get("file"), denials=len(st.get("denials") or []),
                       reused=(stf.parent / "_reused.txt").exists())
        rows.append(row)
    summary = {}
    for task in e.TASKS:
        for vendor in ("claude", "codex"):
            b = [r["mean"] for r in rows if r["task"] == task and r["who"] == f"{vendor}-bare" and r["mean"] is not None]
            h = [r["mean"] for r in rows if r["task"] == task and r["who"] == f"{vendor}-harness" and r["mean"] is not None]
            if b and h:
                summary[f"{task}|{vendor}"] = {"bare": round(sum(b) / len(b), 2), "harness": round(sum(h) / len(h), 2), "diff": round(sum(h) / len(h) - sum(b) / len(b), 2),
                                               "harness_runs": h, "bare_runs": b}
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
        for spec in (jd / "work").rglob("*.json") if (jd / "work").exists() else []:
            if "review" not in spec.parts and spec.stat().st_size < 200_000:
                shutil.copy2(spec, dst / ("spec-" + spec.name))
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
        sys.exit(e.pool(e.run_one, RUNS))
    elif c == "render":
        e.cmd_render()
    elif c == "judge":
        sys.exit(e.pool(lambda *x: judge_one(a[1], *x), [(t, n, pn) for (t, n) in UNITS for pn in (1, 2)]))
    elif c == "table":
        cmd_table()
    elif c == "collect":
        cmd_collect()
    else:
        print(__doc__)
