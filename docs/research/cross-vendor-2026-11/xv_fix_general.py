#!/usr/bin/env python3
"""The bracket+scoreboard task can come back as two HTML files. The generic picker took only the biggest HTML (and once a
hidden build file), so for this task every run is re-drawn from its top-level HTML files: one file -> the usual 5 screens,
two files -> the first 3 screens of each. Same rule for all four conditions.  py xv_fix_general.py"""
import json, shutil, sys, time
from pathlib import Path

sys.argv, _a = ["x"], sys.argv
import xv_eval as e  # noqa: E402

for jd in sorted((e.X / "runs").glob("general-*")):
    st = json.loads((jd / "state.json").read_text(encoding="utf-8"))
    if st.get("general_fixed"):
        continue
    wd = (e.CODEX_WORK / jd.name / "work") if st["vendor"] == "codex" else (jd / "work")
    tops = sorted((p for p in wd.glob("*.html") if not p.name.startswith(("_", "."))), key=lambda p: p.stat().st_size, reverse=True)[:2]
    if not tops:
        continue
    # bracket first when the names tell them apart
    tops.sort(key=lambda p: 0 if any(w in p.name.lower() for w in ("bracket", "대진")) else 1)
    if (jd / "render").exists():
        shutil.move(str(jd / "render"), str(jd / f"render-old-{int(time.time())}"))
    out = jd / "render"
    out.mkdir()
    pngs, notes, fails = [], [], {}
    for k, f in enumerate(tops):
        sub = jd / f"render-part{k + 1}"
        if sub.exists():
            shutil.move(str(sub), str(jd / f"render-part{k + 1}-old-{int(time.time())}"))
        ps, ns = e.render_output(f, "html", sub)
        notes += [f"[{f.name}] {n}" for n in ns]
        keep = ps if len(tops) == 1 else ps[:3]
        for p in keep:
            dst = out / f"html-{k + 1}{Path(p).name[4:]}"
            shutil.copy2(p, dst)
            pngs.append(dst.name)
        fails[f.name] = e.run_checks(f, "html", jd / f"autocheck-part{k + 1}.json")
    merged = {}
    for k, (name, res) in enumerate(fails.items()):
        for ck, v in res.items():
            merged[f"{ck}-{k + 1}"] = v
    (jd / "autocheck.json").write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
    (jd / "render.json").write_text(json.dumps(dict(pngs=pngs, notes=notes), ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copy2(tops[0], jd / "out.html")
    for k, f in enumerate(tops[1:], 2):
        shutil.copy2(f, jd / f"out{k}.html")
    st.update(general_fixed=True, file=" + ".join(p.name for p in tops))
    (jd / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    print(jd.name, [p.name for p in tops], len(pngs), flush=True)
