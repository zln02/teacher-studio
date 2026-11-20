# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Router eval: does the entry skill send a request the right way, with the right number of questions, for every model?

Each case (tools/router_cases.json) is shown to a model with ONLY the installed-skills context (skill descriptions + teacher-studio SKILL.md)
and the model prints its routing decision as JSON. No tools are run. Scores: route 0.4, options-first vs build-now 0.2, question count 0.2, must-not list 0.2.

Usage:
    py tools/router_eval.py --static                         # no model calls: check cases file + that SKILL.md names every route
    py tools/router_eval.py --models haiku,sonnet,opus       # 1 run each, all cases (uses `claude -p`)
    py tools/router_eval.py --models haiku --runs 3 --subset 10
    py tools/router_eval.py --models haiku --bare            # baseline: no skill context, same schema
    py tools/router_eval.py --models codex                   # `codex exec` (works only if the codex CLI is logged in)
    options: --cases ID,ID  --out results.json  --workers 6  --skill-file PATH
Report: floor = the worst run's mean score (worst single case also shown), mean = mean over runs.
Caveat: the model describes what it WOULD do; question_count is self-reported (we use the larger of it and the '?' count in first_reply).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
CASES = Path(__file__).resolve().parent / "router_cases.json"
ROUTES = {
    "game": "makes games (quiz, escape room, bingo, board) as one HTML file",
    "slides": "makes web slide decks (lessons, talks, parent meetings)",
    "motion": "makes intro videos / animated start screens / countdowns",
    "class-tools": "timer, picker, team maker, bracket, scoreboard",
    "webapp": "interactive web app / program (helper, chatbot, tutor, calculator, simulation, practice pad, dashboard) built from a spec",
    "data": "turns spreadsheets (CSV/XLSX) into a chart report without the AI reading raw rows",
    "law": "looks up current law/rules (privacy, copyright, AI rules, school records)",
    "co-plan": "plans, analysis, research done together as a one-page draft (no file is built)",
    "docs": "makes or edits documents: 한글 HWPX / Word / PDF (공문, 가정통신문, 안내문, 보고서; fill a form; fix a file; merge/split PDF)",
    "docfile": "an Excel or other office FILE made through an outside document skill",
    "scout": "look for another existing skill first",
    "bare": "answer using the host’s usual workflow and available tools",
    "greet": "show the welcome card (no request yet)",
}
SCHEMA = (
    'Output ONLY one JSON object, no other text: {"route": "<one of: ' + ", ".join(ROUTES) + '>", '
    '"shows_options_first": <true if your first reply offers 2-3 directions/options before building, false if you build or answer now>, '
    '"question_count": <number of questions in your first reply>, "reads_raw_data": <true if you would open or print raw spreadsheet rows>, '
    '"asks_student_info": <true if you would ask for real student names/scores/data>, "refuses": <true if you decline the whole request>, '
    '"privacy_note": <true if your reply mentions a privacy/law/student-info caution>, '
    '"checkpoint": "<where your first reply stops for the user to react in the production pipeline: plan = after the plan/options; storyboard = after the storyboard sheet, before building; build = you stop for a requested first-file review; deliver = before sharing/sending; none = no stop at all, you run straight through>", '
    '"skipped_stages": [<production stages you skip or merge, from: plan, script, storyboard>], '
    '"artifact": "<what your first reply shows: options | outline | storyboard | shot_list | slide_list | spec | privacy_check | file | none>", '
    '"first_reply": "<your first reply to the user, max 4 short lines>"}\n'
    "Route meanings: " + "; ".join(f"{k} = {v}" for k, v in ROUTES.items()) + ". This is a prediction-only evaluation. Do not run anything; decide what you would do for this first message."
)


REF: str | None = None  # --ref <git rev>: read SKILL.md files as they were at that revision (before/after runs)


def _read(path: Path) -> str:
    if REF:
        rel = path.resolve().relative_to(ROOT).as_posix()
        return subprocess.run(["git", "show", f"{REF}:{rel}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return path.read_text(encoding="utf-8")


def frontmatter(path: Path) -> tuple[str, str]:
    t = _read(path)
    name = re.search(r"^name:\s*(.+)$", t, re.M)
    desc = re.search(r"^description:\s*(.+)$", t, re.M)
    return (name.group(1).strip() if name else path.parent.name, desc.group(1).strip() if desc else "")


# Trigger eval: predict which skill would be selected from its metadata. It does not observe activation.
DISTRACTORS = {  # generic skills often installed next to ours (short paraphrases); used with --distractors
    "web-artifacts-builder": "Suite of tools for creating elaborate, multi-component HTML artifacts using React, Tailwind CSS, shadcn/ui.",
    "frontend-design": "Create distinctive, production-grade frontend interfaces with high design quality.",
    "canvas-design": "Create beautiful visual art in .png and .pdf documents using design philosophy.",
}
TRIGGER_SCHEMA = ('Output ONLY one JSON object: {"skill": "<the name of the ONE skill you would invoke first for this request, '
                  'or none if you would just do it yourself>", "why": "<max 12 words>"}')


def trigger_context(distractors: bool = False) -> str:
    lines = []
    for sk in sorted(SKILLS.glob("*/SKILL.md")):
        n, d = frontmatter(sk)
        lines.append(f"- {n}: {d}")
    if distractors:
        lines += [f"- {k}: {v}" for k, v in DISTRACTORS.items()]
    return ("You are an assistant working in an empty folder. The following skills are available. "
            "Choose the first skill you would use, without running it.\n" + "\n".join(lines))


def score_trigger(case: dict, out: dict | None) -> dict:
    want = case["trigger"] if isinstance(case["trigger"], list) else [case["trigger"]]
    if not isinstance((out or {}).get("skill"), str) or not out["skill"].strip():
        return {"score": 0.0, "parts": {"trigger": 0.0}, "notes": ["missing skill selection"]}
    got = str((out or {}).get("skill", "none")).split(":")[-1].strip()
    ok = got in want
    return {"score": 1.0 if ok else 0.0, "parts": {"trigger": 1.0 if ok else 0.0}, "notes": [] if ok else [f"skill {got} not in {want}"]}


def skill_context(skill_file: Path) -> str:
    lines = []
    for sk in sorted(SKILLS.glob("*/SKILL.md")):
        n, d = frontmatter(sk)
        lines.append(f"- {n}: {d}")
    body = _read(skill_file)
    body = re.sub(r"\A---.*?---\s*", "", body, flags=re.S)
    return ("You are an AI assistant for a user who may be a teacher. These skills are installed (name: description):\n" + "\n".join(lines) +
            "\n\nThe request below activates teacher-studio. Its instructions:\n\n" + body)


BARE_CONTEXT = "You are a helpful AI assistant for a user who may be a teacher. For this comparison, assume Teacher Studio is absent, and describe your normal workflow."


def load_cases(ids: str | None = None, subset: int | None = None) -> list[dict]:
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    if ids:
        want = set(ids.split(","))
        cases = [c for c in cases if c["id"] in want]
    if subset:  # a spread-out subset: every k-th case keeps the mix of clear / vague / law / data / co-plan
        step = max(1, len(cases) // subset)
        cases = cases[::step][:subset]
    return cases


def parse_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return d if isinstance(d, dict) else None
    except ValueError:
        return None


def score(case: dict, out: dict | None) -> dict:
    """Pure scoring (unit-testable). Returns {score, parts, notes}."""
    if not out:
        return {"score": 0.0, "parts": {}, "notes": ["no parsable JSON"]}
    notes, parts = [], {}
    want = case["route"] if isinstance(case["route"], list) else [case["route"]]
    parts["route"] = 0.4 if out.get("route") in want else 0.0
    if parts["route"] == 0:
        notes.append(f"route {out.get('route')} not in {want}")
    d = case.get("direction")
    parts["direction"] = 0.2 if d is None or bool(out.get("shows_options_first")) == d else 0.0
    if parts["direction"] == 0:
        notes.append(f"options_first={out.get('shows_options_first')} expected {d}")
    reply = str(out.get("first_reply", ""))
    try:
        q = max(int(out.get("question_count", 0) or 0), reply.count("?") + reply.count("？"))
    except (TypeError, ValueError):
        q = 99
    parts["questions"] = 0.2 if q <= case["max_questions"] else 0.0
    if parts["questions"] == 0:
        notes.append(f"{q} questions > {case['max_questions']}")
    bad = []
    for m in case.get("must_not", []):
        if m.startswith("route:"):
            hit = out.get("route") == m[6:]
        elif m == "no_privacy_note":
            hit = not out.get("privacy_note")
        else:
            hit = bool(out.get(m))
        if hit:
            bad.append(m)
    parts["must_not"] = 0.2 if not bad else 0.0
    if bad:
        notes.append("violated: " + ",".join(bad))
    total = sum(parts.values())
    pl = case.get("pipeline")
    if pl:  # pipeline cases: 60% routing as before, 40% did it stop at the right checkpoint / skip the right stages / show the right artifact
        checks = []
        if "checkpoint" in pl:
            checks.append(str(out.get("checkpoint", "none")) == pl["checkpoint"])
            if not checks[-1]:
                notes.append(f"checkpoint {out.get('checkpoint')} expected {pl['checkpoint']}")
        if pl.get("skips"):
            got = {str(s) for s in (out.get("skipped_stages") or [])}
            checks.append(set(pl["skips"]) <= got)
            if not checks[-1]:
                notes.append(f"should skip {pl['skips']}, skipped {sorted(got)}")
        if pl.get("artifact"):
            want_a = pl["artifact"] if isinstance(pl["artifact"], list) else [pl["artifact"]]
            checks.append(str(out.get("artifact", "none")) in want_a)
            if not checks[-1]:
                notes.append(f"artifact {out.get('artifact')} not in {want_a}")
        parts["pipeline"] = round(sum(checks) / len(checks), 3) if checks else 1.0
        total = total * 0.6 + parts["pipeline"] * 0.4
    return {"score": round(total, 3), "parts": parts, "notes": notes}


def ask_claude(model: str, system: str, request: str, timeout: int = 360, schema: str = SCHEMA) -> tuple[str, float]:
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("claude CLI not found")
    prompt = f"User request: 「{request}」\n\n{schema}"
    cwd = tempfile.mkdtemp(prefix="router-eval-")
    sf = Path(cwd) / "system.txt"  # a file, not an argument: the Windows .cmd shim garbles non-ASCII arguments
    sf.write_text(system, encoding="utf-8")
    p = subprocess.run([exe, "-p", "--model", model, "--tools", "", "--disable-slash-commands", "--no-session-persistence", "--setting-sources", "",
                        "--strict-mcp-config", "--system-prompt-file", str(sf), "--output-format", "json"], input=prompt, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout, cwd=cwd)
    try:
        d = json.loads(p.stdout)
        return d.get("result", ""), float(d.get("total_cost_usd") or 0)
    except ValueError:
        return p.stdout or p.stderr, 0.0


def ask_codex(system: str, request: str, timeout: int = 240, schema: str = SCHEMA) -> tuple[str, float]:
    exe = shutil.which("codex")
    if not exe:
        raise RuntimeError("codex CLI not found")
    prompt = f"{system}\n\nUser request: 「{request}」\n\n{schema}"
    p = subprocess.run([exe, "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-"], input=prompt, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout, cwd=tempfile.mkdtemp(prefix="router-eval-"))
    if p.returncode or not p.stdout.strip():
        raise RuntimeError("codex exec failed: " + (p.stderr or "")[-100:].replace(chr(10), " "))
    return p.stdout, 0.0


def run_one(model: str, case: dict, system: str, trigger: bool = False) -> dict:
    schema = TRIGGER_SCHEMA if trigger else SCHEMA
    try:
        if model == "codex":
            text, cost = ask_codex(system, case["request"], schema=schema)
        else:
            text, cost = ask_claude(model, system, case["request"], schema=schema)
    except Exception as e:  # noqa: BLE001 - report, never crash the batch
        return {"id": case["id"], "error": str(e)[:120], "score": 0.0, "notes": ["call failed"], "cost": 0.0}
    out = parse_json(text)
    r = score_trigger(case, out) if trigger else score(case, out)
    return {"id": case["id"], "out": out, "cost": cost, **r}


def summarize(runs: list[list[dict]]) -> dict:
    means = [statistics.mean(r["score"] for r in run) for run in runs]
    worst_case = min((r["score"] for run in runs for r in run), default=0)
    return {"runs": len(runs), "floor": round(min(means), 3), "mean": round(statistics.mean(means), 3), "worst_case": worst_case,
            "perfect_cases": sum(1 for r in runs[0] if r["score"] >= 0.999), "n": len(runs[0])}


def static_check() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    problems = []
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        problems.append("duplicate case ids")
    sk = (SKILLS / "teacher-studio" / "SKILL.md").read_text(encoding="utf-8")
    for c in cases:
        for r in (c["route"] if isinstance(c["route"], list) else [c["route"]]):
            if r not in ROUTES:
                problems.append(f"{c['id']}: unknown route {r}")
    for c in cases:
        for t in ([c["trigger"]] if isinstance(c.get("trigger"), str) else c.get("trigger") or []):
            if not (SKILLS / t / "SKILL.md").exists() and t != "none":
                problems.append(f"{c['id']}: trigger names unknown skill {t}")
    _n, desc = frontmatter(SKILLS / "teacher-studio" / "SKILL.md")
    for word in ("프로그램", "앱", "도우미", "알아서"):
        if word not in desc:
            problems.append(f"teacher-studio description lacks 「{word}」 (entry point for make/build requests)")
    if len(desc) > 1024:
        problems.append("teacher-studio description is over 1024 characters")
    for need in ("teacher-game", "teacher-slides", "teacher-motion", "teacher-class-tools", "teacher-data", "teacher-law", "teacher-docs", "co-plan", "skill_scout", "webapp.md"):
        if need not in sk:
            problems.append(f"SKILL.md never mentions {need}")
    n = len(sk.splitlines())
    if n > 150:
        problems.append(f"SKILL.md has {n} lines (> 150)")
    # dry-run rules the self-audit found
    for needle in ("유튜브 채널 기획", "학부모 상담 자료", "Never open or print raw rows"):
        if needle not in sk:
            problems.append(f"SKILL.md lacks the rule for: {needle}")
    print(f"static check: {len(cases)} cases, SKILL.md {n} lines -> " + ("OK" if not problems else "PROBLEMS\n - " + "\n - ".join(problems)))
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--models", default="haiku")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--subset", type=int)
    ap.add_argument("--cases")
    ap.add_argument("--bare", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--skill-file", default=str(SKILLS / "teacher-studio" / "SKILL.md"))
    ap.add_argument("--out")
    ap.add_argument("--trigger", action="store_true", help="only cases with a 'trigger' field: does the model invoke teacher-studio first?")
    ap.add_argument("--distractors", action="store_true", help="with --trigger: also list a few generic web/design skills")
    ap.add_argument("--tag", help="only cases with this tag (e.g. webapp)")
    ap.add_argument("--ref", help="git revision to read SKILL.md files from (before/after comparison)")
    a = ap.parse_args()
    global REF
    REF = a.ref
    if a.static:
        return static_check()
    cases = load_cases(a.cases, a.subset)
    if a.tag:
        cases = [c for c in cases if a.tag in c.get("tags", [])]
    if a.trigger:
        cases = [c for c in cases if c.get("trigger")]
        system = trigger_context(a.distractors)
    else:
        system = BARE_CONTEXT if a.bare else skill_context(Path(a.skill_file))
    if not cases:
        ap.error("no cases match the selected filters")
    result = {}
    for model in a.models.split(","):
        runs = []
        for _ in range(a.runs):
            with cf.ThreadPoolExecutor(a.workers) as ex:
                rows = list(ex.map(lambda c: run_one(model, c, system, a.trigger), cases))
            runs.append(rows)
        s = summarize(runs)
        s["cost_usd"] = round(sum(r.get("cost", 0) for run in runs for r in run), 3)
        result[model] = {"mode": "predicted-trigger" if a.trigger else "predicted-routing", "summary": s, "runs": runs}
        print(f"{model}{' (bare)' if a.bare else ''}: floor {s['floor']} mean {s['mean']} worst-case {s['worst_case']} perfect {s['perfect_cases']}/{s['n']} cost ${s['cost_usd']}")
        for r in runs[0]:
            if r["score"] < 0.999:
                print(f"  {r['id']} {r['score']}: {'; '.join(r.get('notes', []))}")
    if a.out:
        Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
