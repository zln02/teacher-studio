#!/usr/bin/env python3
"""Re-measure sonnet-harness on class-ppt / public-ppt / pdf-guide with the ceiling-eval method (orch.py), then re-judge the four
conditions with ONE renderer for every deck (the new pptx_draw preview).

  py rerun.py sync            copy the repo skills into the harness config (cfg-harness/skills)
  py rerun.py run TASK [TAG]  one job, sequential (TASK = class-ppt | public-ppt | pdf-guide), results in jobs-<TAG>/
  py rerun.py render [TAG]    draw the final pptx of all four conditions with the current renderer (old three from raw/jobs/*/final)
  py rerun.py judge  [TAG]    2 blind passes per task, same prompt / same letter shuffle as post.py
  py rerun.py table  [TAG]    before / after numbers
"""
import json, os, random, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import orch  # noqa: E402  (the original orchestrator: prompts, reviewer, claude() wrapper)
from orch import S, REPO, TASKS, claude, usage_of, extract_json, log  # noqa: E402

RAW = REPO / "docs/research/ceiling-eval-2026-11/raw"
THREE = ["class-ppt", "public-ppt", "pdf-guide"]
CONDS = [("fable", "bare"), ("fable", "harness"), ("sonnet", "bare"), ("sonnet", "harness")]


def tagdir(tag):
    return S / f"jobs-{tag}"


def cmd_sync():
    dst = S / "cfg-harness" / "skills"
    for sk in sorted((REPO / "skills").iterdir()):
        if not (sk / "SKILL.md").exists():
            continue
        t = dst / sk.name
        if t.exists():
            shutil.rmtree(t)
        shutil.copytree(sk, t, ignore=shutil.ignore_patterns("__pycache__"))
        print("synced", sk.name)


def cmd_run(task, tag):
    orch.JOBS = tagdir(tag)
    orch.JOBS.mkdir(exist_ok=True)
    st = orch.run_job(task, "harness", "sonnet")
    print(json.dumps({k: st.get(k) for k in ("name", "first_secs", "time_to_acceptable", "n_fix_rounds", "gen_cost", "review_cost", "accepted", "final")}, ensure_ascii=False))
    fin = list((orch.JOBS / st["name"] / "final").glob("*"))
    if fin:
        orch.run_checks(fin[0], TASKS[task]["kind"], orch.JOBS / st["name"] / "autocheck.json")


def final_file(task, m, c, tag):
    base = tagdir(tag) if (m, c) == ("sonnet", "harness") else RAW / "jobs"
    fs = [f for f in (base / f"{task}-{m}-{c}" / "final").glob("*")]
    return fs[0] if fs else None


def cmd_render(tag):
    out = S / f"rerender-{tag}"
    for task in THREE:
        kind = TASKS[task]["kind"]
        for m, c in CONDS:
            f = final_file(task, m, c, tag)
            d = out / f"{task}-{m}-{c}"
            if d.exists() and any(d.glob("*.png")):
                continue
            if not f:
                print("no final", task, m, c); continue
            d.mkdir(parents=True, exist_ok=True)
            if kind == "pptx":
                subprocess.run(["py", str(REPO / "skills/teacher-slides/scripts/pptx_render.py"), str(f), "--out", str(d)], capture_output=True, timeout=900)
            else:
                import fitz
                doc = fitz.open(str(f))
                for i, page in enumerate(doc):
                    if i >= 12: break
                    page.get_pixmap(dpi=80).save(str(d / f"pdf-{i+1:02d}.png"))
            print("rendered", task, m, c, len(list(d.glob('*.png'))))


def pngs_of(task, m, c, tag):
    d = S / f"rerender-{tag}" / f"{task}-{m}-{c}"
    return sorted(p for p in d.glob("*.png") if "sheet" not in p.name)


def judge_one(task, pn, tag):
    import post
    rnd = random.Random(f"{task}-judge")
    perm = CONDS[:]
    rnd.shuffle(perm)
    if pn == 2: perm = perm[::-1]
    if pn == 2: perm = perm[1:] + perm[:1]
    jd = S / f"judge-{tag}" / task / f"pass{pn}"
    if jd.exists(): shutil.rmtree(jd)
    jd.mkdir(parents=True)
    mapping = {}
    for lab, (m, c) in zip("ABCD", perm):
        mapping[lab] = f"{m}-{c}"
        pngs = pngs_of(task, m, c, tag)
        post.montage(pngs[:6], jd / f"{lab}.png", cols=3, w=640, label=lab)
        if len(pngs) > 6:
            post.montage(pngs[6:12], jd / f"{lab}2.png", cols=3, w=640, label=lab + " (2)")
    kind = TASKS[task]["kind"]
    fmt = {"pptx": ".pptx 슬라이드 (이 PC에 LibreOffice가 없어 파일 안 도형으로 근사해 그린 그림이라 글꼴·줄바꿈이 실제와 약간 다를 수 있음; 모든 결과물에 똑같이 적용)",
           "pdf": "PDF 문서 (실제 쪽 그림)"}[kind]
    req = TASKS[task]["p"] + (" 그리고 같은 대화에서 이어서: " + TASKS[task]["step2"] if "step2" in TASKS[task] else "")
    extra = "한 결과물은 PDF 끝에 신청서 페이지가 붙어 있어야 한다는 두 번째 요청도 포함이야." if "step2" in TASKS[task] else ""
    prompt = post.JUDGE.format(req=req, fmtnote=fmt, extra=extra)
    (jd / "_prompt.txt").write_text(prompt, encoding="utf-8")
    r = claude(prompt, "opus", S / "cfg-reviewer", jd, cap=900)
    j = extract_json((r["data"] or {}).get("result", ""))
    res = dict(task=task, pass_=pn, mapping=mapping, judge=j, cost=usage_of(r["data"])["cost"], raw=(r["data"] or {}).get("result", "")[:1500])
    (S / f"judge-{tag}" / f"{task}-pass{pn}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("judged", task, pn, bool(j), round(res["cost"], 2))


def cmd_judge(tag, only=None):
    for task in THREE:
        if only and task not in only: continue
        for pn in (1, 2):
            judge_one(task, pn, tag)


def scores(jdir, task):
    out = {}
    for pn in (1, 2):
        f = jdir / f"{task}-pass{pn}.json"
        if not f.exists(): continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("judge"): continue
        for lab, cond in d["mapping"].items():
            v = d["judge"][lab]
            out.setdefault(cond, []).append(dict(mean=sum(v[k] for k in ("design", "accuracy", "fit", "ready")) / 4, rank=d["judge"]["ranking"].index(lab) + 1, note=v.get("note", ""),
                                                 **{k: v[k] for k in ("design", "accuracy", "fit", "ready")}))
    return {c: dict(mean=round(sum(x["mean"] for x in v) / len(v), 2), rank=round(sum(x["rank"] for x in v) / len(v), 2), passes=v) for c, v in out.items()}


def cmd_table(tag):
    res = {}
    for task in THREE:
        before = scores(RAW / "judge", task)
        after = scores(S / f"judge-{tag}", task)
        stf = tagdir(tag) / f"{task}-sonnet-harness" / "state.json"
        st = json.loads(stf.read_text(encoding="utf-8")) if stf.exists() else {}
        old = json.loads((RAW / "jobs" / f"{task}-sonnet-harness" / "state.json").read_text(encoding="utf-8"))
        bare = json.loads((RAW / "jobs" / f"{task}-sonnet-bare" / "state.json").read_text(encoding="utf-8"))
        ac = tagdir(tag) / f"{task}-sonnet-harness" / "autocheck.json"
        res[task] = dict(before=before, after=after,
                         run=dict(first_secs=st.get("first_secs"), total_secs=st.get("time_to_acceptable"), fixes=st.get("n_fix_rounds"), gen_cost=st.get("gen_cost"), review_cost=st.get("review_cost"),
                                  autocheck=json.loads(ac.read_text(encoding="utf-8")) if ac.exists() else None),
                         old_run=dict(first_secs=old.get("first_secs"), total_secs=old.get("time_to_acceptable"), fixes=old.get("n_fix_rounds"), gen_cost=old.get("gen_cost")),
                         bare_run=dict(first_secs=bare.get("first_secs"), total_secs=bare.get("time_to_acceptable"), fixes=bare.get("n_fix_rounds"), gen_cost=bare.get("gen_cost")))
        b, a = before, after
        print(f"{task}: before sonnet-bare {b.get('sonnet-bare', {}).get('mean')} vs sonnet-harness {b.get('sonnet-harness', {}).get('mean')}  |  "
              f"after (same renderer) sonnet-bare {a.get('sonnet-bare', {}).get('mean')} vs sonnet-harness {a.get('sonnet-harness', {}).get('mean')}  "
              f"[fable-bare {a.get('fable-bare', {}).get('mean')}, fable-harness {a.get('fable-harness', {}).get('mean')}]  gen ${st.get('gen_cost')}")
    (S / f"rerun-{tag}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    c = sys.argv[1]
    tag = "r1"
    if c == "sync": cmd_sync()
    elif c == "run": cmd_run(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else tag)
    elif c == "render": cmd_render(sys.argv[2] if len(sys.argv) > 2 else tag)
    elif c == "judge": cmd_judge(sys.argv[2] if len(sys.argv) > 2 else tag, sys.argv[3:] or None)
    elif c == "table": cmd_table(sys.argv[2] if len(sys.argv) > 2 else tag)
