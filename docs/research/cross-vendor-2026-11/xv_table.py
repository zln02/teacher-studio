#!/usr/bin/env python3
"""Numbers for the cross-vendor eval: py xv_table.py  ->  table.json next to this file + markdown on stdout."""
import json, statistics, sys
from pathlib import Path

sys.argv, _argv = ["x"], sys.argv
import xv_eval as e  # noqa: E402

HERE = Path(__file__).parent
NEUTRAL_EXCL = ("GAME_LOGIC", "NG.boot", "engine block", "mute button", "teacher menu", "GAME.items", "GAME data", "no reset button", "spec", "token", "bias", "house look")
JUDGES = ("opus", "gpt")
VENDORS = ("claude", "codex")
mean = lambda v: sum(v) / len(v) if v else float("nan")


def gate(jd):
    f = jd / "autocheck.json"
    if not f.exists():
        return None, []
    d = json.loads(f.read_text(encoding="utf-8"))
    fails = []
    for v in d.values():
        if isinstance(v, dict):
            fails += [ln[:140] for ln in v.get("out", "").splitlines() if ln.startswith("FAIL") and not any(x in ln for x in NEUTRAL_EXCL)]
    return len(fails), fails


def load():
    runs = {}
    for jd in sorted((e.X / "runs").iterdir()):
        if not (jd / "state.json").exists():
            continue
        st = json.loads((jd / "state.json").read_text(encoding="utf-8"))
        rd = json.loads((jd / "render.json").read_text(encoding="utf-8")) if (jd / "render.json").exists() else dict(pngs=[], notes=[])
        nf, fl = gate(jd)
        js_err = any("js_errors=" in n and "js_errors=[]" not in n for n in rd["notes"])
        st.update(n_png=len(rd["pngs"]), render_notes=rd["notes"], gate_fails=nf, gate_lines=fl, js_err=js_err,
                  first_try=bool(st.get("file")) and st.get("opens", False) and not st["timed_out"] and len(rd["pngs"]) > 0 and not js_err)
        runs[(st["task"], st["vendor"], st["cond"], st["run"])] = st
    sc = {}  # (task, run, vendor, cond) -> judge -> list of dict(keys.., rank, note)
    for j in JUDGES:
        for f in sorted((e.X / "judge" / j).glob("*-pass*.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            rk = r["result"].get("ranking") or []
            for lab, vc in r["mapping"].items():
                v, c = vc.split("-")
                x = r["result"][lab]
                sc.setdefault((r["task"], r["run"], v, c), {}).setdefault(j, []).append(
                    dict({k: float(x[k]) for k in e.KEYS}, rank=(rk.index(lab) + 1 if lab in rk else None), note=x.get("note", ""), pass_=r["pass_"]))
    return runs, sc


def score(sc, key, judge):
    """mean of the 4 criteria over the passes; judge = opus | gpt | both (mean of the two judges)"""
    d = sc.get(key, {})
    per = [mean([mean([p[k] for k in e.KEYS]) for p in d[j]]) for j in (JUDGES if judge == "both" else (judge,)) if d.get(j)]
    return mean(per) if per else None


def main():
    runs, sc = load()
    units = sorted({(t, n) for (t, n, _, _) in sc})
    out = dict(tasks={k: v["p"] for k, v in e.TASKS.items()}, summary={}, per_task=[], self_pref={}, criteria={}, ops={}, runs=[], notes=[])
    P = print
    P("## vendor x judge: bare vs harness (mean / worst run / head-to-head harness-bare-tie over task-runs)")
    P("| maker | judge | bare mean | harness mean | diff | bare worst | harness worst | H2H |")
    P("|---|---|---|---|---|---|---|---|")
    for v in VENDORS:
        for j in JUDGES + ("both",):
            b = [score(sc, (t, n, v, "bare"), j) for t, n in units]
            h = [score(sc, (t, n, v, "harness"), j) for t, n in units]
            pairs = [(x, y) for x, y in zip(b, h) if x is not None and y is not None]
            if not pairs:
                continue
            w = sum(y > x + 1e-9 for x, y in pairs); l = sum(x > y + 1e-9 for x, y in pairs); tie = len(pairs) - w - l
            row = dict(maker=v, judge=j, bare=mean([x for x, _ in pairs]), harness=mean([y for _, y in pairs]), bare_worst=min(x for x, _ in pairs),
                       harness_worst=min(y for _, y in pairs), h2h=[w, l, tie], n=len(pairs))
            out["summary"][f"{v}/{j}"] = row
            P(f"| {v} | {j} | {row['bare']:.2f} | {row['harness']:.2f} | {row['harness'] - row['bare']:+.2f} | {row['bare_worst']:.2f} | {row['harness_worst']:.2f} | {w}-{l}-{tie} |")
    P("\n## per task (mean over runs; cells = bare -> harness (diff))")
    P("| task | maker | opus | gpt | both | no-regret? |")
    P("|---|---|---|---|---|---|")
    for t in e.TASKS:
        for v in VENDORS:
            cell = {}
            for j in JUDGES + ("both",):
                b = [s for s in (score(sc, (t, n, v, "bare"), j) for n in range(1, e.RUNS + 1)) if s is not None]
                h = [s for s in (score(sc, (t, n, v, "harness"), j) for n in range(1, e.RUNS + 1)) if s is not None]
                cell[j] = (mean(b), mean(h), b, h) if b and h else None
            if not cell["both"]:
                continue
            ok = cell["both"][1] >= cell["both"][0] - 1e-9
            out["per_task"].append(dict(task=t, maker=v, **{j: dict(bare=c[0], harness=c[1], bare_runs=c[2], harness_runs=c[3]) for j, c in cell.items() if c}, no_regret=ok))
            f = lambda c: f"{c[0]:.2f} -> {c[1]:.2f} ({c[1] - c[0]:+.2f})" if c else "-"
            P(f"| {e.TASKS[t]['name']} | {v} | {f(cell['opus'])} | {f(cell['gpt'])} | {f(cell['both'])} | {'yes' if ok else 'NO'} |")
    P("\n## self-preference: mean score each judge gives to outputs by maker vendor")
    P("| judge | claude-made | codex-made | claude minus codex | bare: claude / codex | harness: claude / codex |")
    P("|---|---|---|---|---|---|")
    for j in JUDGES:
        g = {}
        for (t, n, v, c), d in sc.items():
            s = score(sc, (t, n, v, c), j)
            if s is not None:
                g.setdefault((v, c), []).append(s)
        cm, xm = mean(g.get(("claude", "bare"), []) + g.get(("claude", "harness"), [])), mean(g.get(("codex", "bare"), []) + g.get(("codex", "harness"), []))
        out["self_pref"][j] = dict(claude_made=cm, codex_made=xm, by={f"{v}-{c}": mean(x) for (v, c), x in g.items()})
        P(f"| {j} | {cm:.2f} | {xm:.2f} | {cm - xm:+.2f} | {mean(g.get(('claude', 'bare'), [])):.2f} / {mean(g.get(('codex', 'bare'), [])):.2f} | {mean(g.get(('claude', 'harness'), [])):.2f} / {mean(g.get(('codex', 'harness'), [])):.2f} |")
    P("\n## mean rank (1 = best of 4) per condition and judge")
    for j in JUDGES:
        g = {}
        for (t, n, v, c), d in sc.items():
            g.setdefault(f"{v}-{c}", []).extend(p["rank"] for p in d.get(j, []) if p["rank"])
        out.setdefault("rank", {})[j] = {k: mean(x) for k, x in g.items()}
        P(j, {k: round(mean(x), 2) for k, x in sorted(g.items())})
    P("\n## criteria (both judges)")
    for v, c in e.CONDS:
        g = {k: [] for k in e.KEYS}
        for (t, n, vv, cc), d in sc.items():
            if (vv, cc) == (v, c):
                for j in JUDGES:
                    for p in d.get(j, []):
                        for k in e.KEYS:
                            g[k].append(p[k])
        out["criteria"][f"{v}-{c}"] = {k: mean(x) for k, x in g.items()}
        P(f"{v}-{c}", {k: round(mean(x), 2) for k, x in g.items()})
    P("\n## time, cost, first try, gate")
    P("| condition | runs | median s | mean s | cost sum | out tokens mean | first-try ok | no file | timed out | gate pass (0 neutral FAIL) | gate FAIL lines | blocked or failed commands per run (claude: permission denials, codex: non-zero exits) |")
    P("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for v, c in e.CONDS:
        rs = [st for (t, vv, cc, n), st in runs.items() if (vv, cc) == (v, c)]
        if not rs:
            continue
        secs = [r["secs"] for r in rs]
        cost = sum(r["cost"] or 0 for r in rs) if v == "claude" else None
        gp = sum(1 for r in rs if r["gate_fails"] == 0)
        row = dict(n=len(rs), median_s=statistics.median(secs), mean_s=mean(secs), cost=cost, out_tok=mean([r.get("out_tok") or 0 for r in rs]),
                   first_try=sum(r["first_try"] for r in rs), no_file=sum(not r.get("file") for r in rs), timed_out=sum(r["timed_out"] for r in rs),
                   gate_pass=gp, gate_fail_lines=sum(r["gate_fails"] or 0 for r in rs),
                   blocked_mean=mean([len(r.get("denials") or []) if v == "claude" else (r.get("failed_cmds") or 0) for r in rs]))
        out["ops"][f"{v}-{c}"] = row
        P(f"| {v}-{c} | {row['n']} | {row['median_s']:.0f} | {row['mean_s']:.0f} | {('$%.2f' % cost) if cost is not None else 'n/a (subscription)'} | {row['out_tok']:.0f} | {row['first_try']}/{row['n']} | {row['no_file']} | {row['timed_out']} | {gp}/{row['n']} | {row['gate_fail_lines']} | {row['blocked_mean']:.1f} |")
    P("\n## every run")
    for (t, v, c, n), st in sorted(runs.items()):
        s = {j: score(sc, (t, n, v, c), j) for j in JUDGES + ("both",)}
        out["runs"].append(dict(task=t, maker=v, cond=c, run=n, secs=st["secs"], cost=st["cost"], out_tok=st.get("out_tok"), file=st.get("file"), first_try=st["first_try"],
                                timed_out=st["timed_out"], gate_fails=st["gate_fails"], gate_lines=st["gate_lines"][:6], js_err=st["js_err"], scores=s,
                                failed_cmds=st.get("failed_cmds"), denials=len(st.get("denials") or []), turns=st.get("turns")))
        f = lambda x: "-" if x is None else f"{x:.2f}"
        P(f"{t} {v}-{c} #{n}: {st['secs']}s file={st.get('file')} first_try={st['first_try']} gate_fails={st['gate_fails']} opus={f(s['opus'])} gpt={f(s['gpt'])} both={f(s['both'])}")
    for (t, n, v, c), d in sorted(sc.items()):
        for j in JUDGES:
            for p in d.get(j, []):
                out["notes"].append(dict(task=t, run=n, maker=v, cond=c, judge=j, pass_=p["pass_"], score=mean([p[k] for k in e.KEYS]), rank=p["rank"], note=p["note"]))
    (HERE / "table.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
