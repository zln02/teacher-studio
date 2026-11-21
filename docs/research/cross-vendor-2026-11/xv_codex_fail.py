#!/usr/bin/env python3
"""Why commands failed inside Codex runs (sandbox, network, encoding) and which harness scripts ran.  py xv_codex_fail.py [-v]"""
import collections, json, re, sys
from pathlib import Path

VERBOSE = "-v" in sys.argv
sys.argv = ["x"]
import xv_eval as e  # noqa: E402

BS = chr(92)
cat = collections.defaultdict(collections.Counter)
ex = {}
rows = []
for d in sorted((e.X / "runs").glob("*-codex-*")):
    cond = "harness" if "-harness-" in d.name else "bare"
    n, used = 0, set()
    for line in (d / "_codex_events.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        it = ev.get("item", {})
        if ev.get("type") != "item.completed" or it.get("type") != "command_execution":
            continue
        n += 1
        c = it.get("command", "")
        o = it.get("aggregated_output") or ""
        for m in re.findall(r"(teacher-[\w-]+)/+scripts/+([\w.]+)", c.replace(BS, "/")):
            used.add(m[0] + "/" + m[1])
        if it.get("exit_code") in (0, None):
            continue
        k = "other (script error, assertion, wrong argument)"
        if "PermissionError" in o and ("Temp" in o or "deck-" in o or "tmp" in o.lower()):
            k = "temp folder write denied (PermissionError)"
        elif "PermissionError" in o or "액세스가 거부" in o or "Access is denied" in o or "UnauthorizedAccess" in o or "Access to the path" in o:
            k = "access denied (other path or process)"
        elif "crashpad" in o or "BrowserType.launch" in o or "Target page, context or browser has been closed" in o:
            k = "headless browser could not start"
        elif "10061" in o or "getaddrinfo" in o or "ConnectionRefused" in o:
            k = "network blocked"
        elif "blocked by policy" in o:
            k = "blocked by policy"
        elif "not recognized" in o or "CommandNotFound" in o or "인식되지" in o:
            k = "command not found"
        elif "UnicodeEncodeError" in o or "cp949" in o:
            k = "cp949 encoding error"
        cat[cond][k] += 1
        ex.setdefault((cond, k), []).append((d.name, c.split("-Command", 1)[-1][:160].replace("\n", " "), o[-300:].replace("\n", " | ")))
    rows.append(dict(run=d.name, cmds=n, scripts=sorted(used)))
    print(d.name, "cmds", n, "scripts", sorted(used))
for c in cat:
    print(c, dict(cat[c]))
if VERBOSE:
    for (c, k), v in ex.items():
        print("\n##", c, k, len(v))
        for x in v[:4]:
            print("  ", x[0], "\n     CMD", x[1], "\n     OUT", x[2])
(Path(__file__).parent / "codex-failures.json").write_text(json.dumps(dict(runs=rows, categories={c: dict(v) for c, v in cat.items()},
                                                                         examples={f"{c}|{k}": v[:5] for (c, k), v in ex.items()}), ensure_ascii=False, indent=1), encoding="utf-8")
