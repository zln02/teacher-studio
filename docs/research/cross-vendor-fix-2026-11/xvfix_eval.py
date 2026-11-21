#!/usr/bin/env python3
"""Re-test after the cross-vendor fixes, with the SAME method and code as docs/research/cross-vendor-2026-11/xv_eval.py.

  py xvfix_eval.py setup            fresh skills via scripts/setup.py (redirected home) -> isolated CODEX_HOME / CLAUDE_CONFIG_DIR, old runs copied in
  py xvfix_eval.py run-codex        GPT (Codex) + harness, 6 tasks x 2 runs           (bare GPT runs are reused from the first round)
  py xvfix_eval.py run-claude       Claude Sonnet + harness, only webapp and hwpx-notice x 2 runs (regression check)
  py xvfix_eval.py render           draw the new outputs + gates (one browser at a time)
  py xvfix_eval.py judge opus|gpt   blind A-D, 2 passes, all 6 tasks (the four outputs of a task are judged together, so everything is re-judged)
  py xvfix_eval.py second-pass class-ppt general   keep the first-pass results of these GPT tasks aside (xv2/pass1, table-pass1.json), reinstall the skills
                                    then: run-codex class-ppt general -> render -> judge opus|gpt class-ppt general -> table
  py xvfix_eval.py table            numbers -> table.json here
  py xvfix_eval.py fail             Codex command failures by cause -> codex-failures.json here

What is reused: every *-bare-* run and the Claude harness runs of the four tasks not re-run (their files, pictures and gate results are
copied unchanged). What is new: codex-harness x 12, claude-harness x 4 (webapp, hwpx-notice). Same launch flags as round 1: no permission
or sandbox bypass, install commands denied, Codex -s workspace-write with the network off, isolated CODEX_HOME, at most 2 at a time.
Nothing in the owner's ~/.claude, ~/.codex, ~/.agents is written.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cross-vendor-2026-11"))
_argv, sys.argv = sys.argv, ["x"]
import xv_eval as e  # noqa: E402
import orch  # noqa: E402
sys.argv = _argv

S = e.S
OLD = S / "xv"
NEW = S / "xv2"
e.X = NEW
orch.LOG = NEW / "eval.log"
e.CODEX_WORK = Path(r"C:\Users\User\Downloads\xv-eval-work") / "fix"
RERUN_CLAUDE = ("webapp", "hwpx-notice")
CFG_HARNESS = S / "cfg-harness2"
_claude = e.claude


def claude(prompt, model, cfg, cwd, **kw):  # the harness condition reads the freshly installed skills
    if Path(cfg).name == "cfg-harness":
        cfg = CFG_HARNESS
    return _claude(prompt, model, cfg, cwd, **kw)


e.claude = claude


def is_new(name: str) -> bool:
    t, v, c, n = name.rsplit("-", 3)
    return c == "harness" and (v == "codex" or t in RERUN_CLAUDE)


def install(agent: str, home: Path) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, USERPROFILE=str(home), HOME=str(home), TEACHER_STUDIO_HOME=str(home / ".teacher-studio"), PYTHONUTF8="1")
    r = subprocess.run([sys.executable, str(e.REPO / "scripts" / "setup.py"), "--agent", agent], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"setup.py --agent {agent}: rc={r.returncode}", r.stdout.strip().splitlines()[-1:] or r.stderr[-300:])
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return home / (".claude" if agent == "claude-code" else ".agents") / "skills"


def copy_skills(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("skills ->", dst, sorted(p.name for p in dst.iterdir()))


def cmd_setup():
    NEW.mkdir(exist_ok=True)
    (NEW / "runs").mkdir(exist_ok=True)
    # Codex: bare (also the GPT judge's home) and harness
    for cond in ("codex-bare", "codex-harness"):
        d = NEW / cond
        d.mkdir(exist_ok=True)
        for f in ("auth.json", "config.toml"):
            if not (d / f).exists():
                shutil.copyfile(OLD / "codex-bare" / f, d / f)
    copy_skills(install("codex", NEW / "home-codex"), NEW / "codex-harness" / "skills")
    # Claude: same login files as round 1's harness config, fresh skills
    CFG_HARNESS.mkdir(exist_ok=True)
    for f in (".claude.json", ".credentials.json"):
        if (S / "cfg-harness" / f).exists():
            shutil.copyfile(S / "cfg-harness" / f, CFG_HARNESS / f)
    copy_skills(install("claude-code", NEW / "home-claude"), CFG_HARNESS / "skills")
    # reused runs: files, pictures and gate results exactly as judged in round 1
    for jd in sorted((OLD / "runs").iterdir()):
        if is_new(jd.name) or not (jd / "state.json").exists():
            continue
        dst = NEW / "runs" / jd.name
        if dst.exists():
            continue
        dst.mkdir()
        for p in jd.iterdir():
            if p.is_file() and (p.name in ("state.json", "render.json", "autocheck.json") or p.name.startswith("out")):
                shutil.copy2(p, dst / p.name)
        if (jd / "render").exists():
            shutil.copytree(jd / "render", dst / "render")
    print("reused runs:", len(list((NEW / "runs").iterdir())))


def cmd_fix_general():
    """Same rule as round 1 (xv_fix_general.py): the bracket + scoreboard task is drawn from its top-level HTML files (max 2)."""
    import importlib
    sys.argv = ["x"]
    importlib.import_module("xv_fix_general")


def cmd_table():
    sys.argv = ["x"]
    import xv_table
    xv_table.HERE = HERE
    xv_table.main()


def cmd_fail():
    """Round 1's xv_codex_fail.py, unchanged, with its output written here instead of over the round-1 file."""
    src = (HERE.parent / "cross-vendor-2026-11" / "xv_codex_fail.py").read_text(encoding="utf-8")
    assert src.count("Path(__file__).parent") == 1
    sys.argv = ["x"] + [x for x in sys.argv[2:] if x == "-v"]
    exec(compile(src.replace("Path(__file__).parent", "Path(r'%s')" % HERE), "xv_codex_fail.py", "exec"), {"__name__": "__main__"})


def cmd_second_pass(tasks):
    """After the first re-test two GPT tasks were still far below bare (class-ppt, general), so the skill text got a second pass
    (coverage list; a hand-made page must be ready when it opens). Their first-pass runs, pictures and scores are kept under
    xv2/pass1/ and in table-pass1.json; the skills are reinstalled and only these tasks are made and judged again."""
    keep = NEW / "pass1"
    (keep / "runs").mkdir(parents=True, exist_ok=True)
    if (HERE / "table.json").exists() and not (HERE / "table-pass1.json").exists():
        shutil.copyfile(HERE / "table.json", HERE / "table-pass1.json")
    for t in tasks:
        for n in range(1, e.RUNS + 1):
            jd = NEW / "runs" / f"{t}-codex-harness-{n}"
            if jd.exists() and not (keep / "runs" / jd.name).exists():
                shutil.move(str(jd), str(keep / "runs" / jd.name))
        for j in ("opus", "gpt"):
            (keep / "judge" / j).mkdir(parents=True, exist_ok=True)
            for f in (NEW / "judge" / j).glob(f"{t}-*"):
                if not (keep / "judge" / j / f.name).exists():
                    shutil.move(str(f), str(keep / "judge" / j / f.name))
    copy_skills(install("codex", NEW / "home-codex"), NEW / "codex-harness" / "skills")
    copy_skills(install("claude-code", NEW / "home-claude"), CFG_HARNESS / "skills")


if __name__ == "__main__":
    a = sys.argv[1:]
    c = a[0] if a else ""
    if c == "setup":
        cmd_setup()
    elif c == "run-codex":
        sys.exit(e.cmd_run("codex", "harness", a[1:] or list(e.TASKS)))
    elif c == "run-claude":
        sys.exit(e.cmd_run("claude", "harness", a[1:] or list(RERUN_CLAUDE)))
    elif c == "render":
        e.cmd_render()
        cmd_fix_general()
    elif c == "judge":
        sys.exit(e.cmd_judge(a[1], a[2:] or list(e.TASKS)))
    elif c == "second-pass":
        cmd_second_pass(a[1:])
    elif c == "table":
        cmd_table()
    elif c == "fail":
        cmd_fail()
    else:
        print(__doc__)
