"""Copy the design round's raw material into docs/research/ppt-design-2026-11/ and print the numbers the report needs.  py pack_d.py"""
import json, shutil, sys
from pathlib import Path

sys.argv, argv = ["x"], sys.argv
import ppt_eval as e  # noqa: E402

TAG = "d1"
OUT = e.REPO / "docs/research/ppt-design-2026-11"
OUT.mkdir(parents=True, exist_ok=True)
agg = {}
for jd in sorted(e.rdir(TAG).iterdir()):
    if not (jd / "state.json").exists():
        continue
    s = json.loads((jd / "state.json").read_text(encoding="utf-8"))
    reused = "-bare-" in jd.name and (e.rdir("r1") / jd.name).exists()
    ck = (jd / "check.txt").read_text(encoding="utf-8", errors="replace") if (jd / "check.txt").exists() else ""
    if not reused:
        a = agg.setdefault(s["cond"], dict(secs=[], cost=[], fail=0, n=0))
        a["secs"].append(s["secs"]); a["cost"].append(s["cost"]); a["n"] += 1
        a["fail"] += 1 if "RESULT: FAIL" in ck else 0
    if reused:
        continue  # the bare decks of the three re-run topics are the round-1 files already in ppt-win-2026-11/runs/r1
    d = OUT / "runs" / jd.name
    d.mkdir(parents=True, exist_ok=True)
    s["last"] = s.get("last", "")[-600:]
    (d / "state.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in ("deck.pptx", "spec.json", "check.txt"):
        if (jd / f).exists():
            shutil.copy2(jd / f, d / f)
jdir = e.HERE / f"judge-{TAG}"
jc = 0
if jdir.exists():
    (OUT / "judge").mkdir(parents=True, exist_ok=True)
    for f in jdir.glob("*-pass*.json"):
        shutil.copy2(f, OUT / "judge" / f.name)
        jc += json.loads(f.read_text(encoding="utf-8")).get("cost", 0)
    one = next(iter(sorted(jdir.glob("*/_prompt.txt"))), None)
    if one:
        shutil.copy2(one, OUT / "judge" / "_prompt-example.txt")
if (e.HERE / f"table-{TAG}.json").exists():
    shutil.copy2(e.HERE / f"table-{TAG}.json", OUT / f"table-{TAG}.json")
for f in ("ppt_eval.py", "contact.py", "pack_d.py"):
    shutil.copy2(e.HERE / f, OUT / f)
for c, a in agg.items():
    sec = sorted(a["secs"])
    print(c, f"runs={a['n']} median_secs={sec[len(sec) // 2]} max_secs={max(sec)} mean_cost=${sum(a['cost']) / len(a['cost']):.2f} total=${sum(a['cost']):.2f} gate_fail={a['fail']}")
print(f"judge cost ${jc:.2f}")
t = json.loads((e.HERE / f"table-{TAG}.json").read_text(encoding="utf-8"))
sc, notes, wins = e.collect(TAG)
grp = {}
for topic, d in sc.items():
    g = e.TOPICS[topic]["g"]
    for cond, runs in d.items():
        for ps in runs.values():
            for p in ps:
                grp.setdefault(g, {}).setdefault(cond, []).append(sum(p[k] for k in e.KEYS) / 4)
                for k in e.KEYS:
                    grp.setdefault("crit:" + ("fresh" if topic in e.FRESH_D else "rerun"), {}).setdefault(cond + ":" + k, []).append(p[k])
for g, d in grp.items():
    print(g, {c: round(sum(v) / len(v), 2) for c, v in sorted(d.items())})
for part, names in (("fresh", e.FRESH_D), ("rerun", e.RERUN_D), ("all", e.FRESH_D + e.RERUN_D)):
    rows = [r for r in t["rows"] if r["topic"] in names]
    for c in ("bare", "harness"):
        print(part, c, "mean %.2f worst %.2f" % (sum(r[c + "_mean"] for r in rows) / len(rows), min(r[c + "_worst"] for r in rows)))
    print(part, "head-to-head harness-bare-tie", sum(r["wins"]["harness"] for r in rows), sum(r["wins"]["bare"] for r in rows), sum(r["wins"]["tie"] for r in rows))
print("| 주제 | 일반 AI 평균 / 최악 | 스튜디오 평균 / 최악 | 차이 | 맞대결(스튜디오-일반-비김) |\n|---|---|---|---|---|")
for r in t["rows"]:
    w = r["wins"]
    print(f"| {r['topic']} | {r['bare_mean']:.2f} / {r['bare_worst']:.2f} | {r['harness_mean']:.2f} / {r['harness_worst']:.2f} | {r['harness_mean'] - r['bare_mean']:+.2f} | {w['harness']}-{w['bare']}-{w['tie']} |")
print({c: {k: round(v, 2) for k, v in d.items()} for c, d in t["criteria"].items()})
n = sum(1 for _ in OUT.rglob("*") if _.is_file())
print("packed", n, "files")
