"""Time / cost / gate / slide-count per condition, and the score tables as Markdown.  py stats.py"""
import json, re, sys
from pathlib import Path

sys.argv, argv = ["x"], sys.argv
import ppt_eval as e  # noqa: E402

for tag in ("r1", "r2"):
    agg = {}
    for jd in sorted(e.rdir(tag).iterdir()):
        st = jd / "state.json"
        if not st.exists():
            continue
        s = json.loads(st.read_text(encoding="utf-8"))
        ck = (jd / "check.txt").read_text(encoding="utf-8", errors="replace") if (jd / "check.txt").exists() else ""
        n = len(e.slide_pngs(jd))
        a = agg.setdefault(s["cond"], dict(secs=[], cost=[], fail=0, n=0, slides=[]))
        a["secs"].append(s["secs"]); a["cost"].append(s["cost"]); a["n"] += 1; a["slides"].append(n)
        a["fail"] += 1 if "RESULT: FAIL" in ck else 0
    for c, a in agg.items():
        sec = sorted(a["secs"])
        print(tag, c, f"runs={a['n']} median_secs={sec[len(sec) // 2]} mean_secs={sum(sec) / len(sec):.0f} max_secs={max(sec)} mean_cost=${sum(a['cost']) / len(a['cost']):.2f} total=${sum(a['cost']):.2f} gate_fail={a['fail']}")
    jc = sum(json.loads(f.read_text(encoding='utf-8')).get("cost", 0) for f in (e.HERE / f"judge-{tag}").glob("*-pass*.json")) if (e.HERE / f"judge-{tag}").exists() else 0
    print(tag, f"judge cost ${jc:.2f}")
    tb = e.HERE / f"table-{tag}.json"
    if tb.exists():
        t = json.loads(tb.read_text(encoding="utf-8"))
        print("| 주제 | 일반 AI 평균 / 최악 | 스튜디오 평균 / 최악 | 차이 | 맞대결(스튜디오-일반-비김) |\n|---|---|---|---|---|")
        for r in t["rows"]:
            w = r["wins"]
            print(f"| {r['topic']} | {r['bare_mean']:.2f} / {r['bare_worst']:.2f} | {r['harness_mean']:.2f} / {r['harness_worst']:.2f} | {r['harness_mean'] - r['bare_mean']:+.2f} | {w['harness']}-{w['bare']}-{w['tie']} |")
        print({c: {k: round(v, 2) for k, v in d.items()} for c, d in t["criteria"].items()})
