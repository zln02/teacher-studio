"""Copy the eval's raw material into docs/research/ppt-win-2026-11/ (decks, specs, run facts, judge prompts and answers, scripts)."""
import json, shutil, sys
from pathlib import Path

sys.argv, argv = ["x"], sys.argv
import ppt_eval as e  # noqa: E402

OUT = e.REPO / "docs/research/ppt-win-2026-11"
OUT.mkdir(parents=True, exist_ok=True)
for tag in ("r1", "r2"):
    for jd in sorted(e.rdir(tag).iterdir()):
        if not (jd / "state.json").exists():
            continue
        if tag == "r2" and "-bare-" in jd.name and (e.rdir("r1") / jd.name).exists():
            continue  # round 2 reused the round-1 bare decks of the first six topics: one copy is enough
        d = OUT / "runs" / tag / jd.name
        d.mkdir(parents=True, exist_ok=True)
        s = json.loads((jd / "state.json").read_text(encoding="utf-8"))
        s["last"] = s.get("last", "")[-600:]
        (d / "state.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
        for f in ("deck.pptx", "spec.json", "check.txt"):
            if (jd / f).exists():
                shutil.copy2(jd / f, d / f)
    jdir = e.HERE / f"judge-{tag}"
    if jdir.exists():
        (OUT / "judge" / tag).mkdir(parents=True, exist_ok=True)
        for f in jdir.glob("*-pass*.json"):
            shutil.copy2(f, OUT / "judge" / tag / f.name)
        one = next(iter(sorted(jdir.glob("*/_prompt.txt"))), None)
        if one:
            shutil.copy2(one, OUT / "judge" / tag / "_prompt-example.txt")
    if (e.HERE / f"table-{tag}.json").exists():
        shutil.copy2(e.HERE / f"table-{tag}.json", OUT / f"table-{tag}.json")
for f in ("ppt_eval.py", "contact.py", "stats.py", "pack.py"):
    shutil.copy2(e.HERE / f, OUT / f)
n = sum(1 for _ in OUT.rglob("*") if _.is_file())
sz = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
print("packed", n, "files", sz // 1024, "KB")
