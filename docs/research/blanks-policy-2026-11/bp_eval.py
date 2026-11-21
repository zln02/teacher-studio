#!/usr/bin/env python3
"""Blanks policy (「섞기」) re-test on FRESH tasks, with the same method and code as docs/research/cross-vendor-2026-11/xv_eval.py.

  py bp_eval.py setup                 fresh skills via scripts/setup.py (redirected home) -> isolated CODEX_HOME / CLAUDE_CONFIG_DIR
  py bp_eval.py run VENDOR COND       VENDOR = claude | codex, COND = bare | harness; 4 tasks x 2 runs, 2 at a time
  py bp_eval.py render                (PDF task: two saved PDFs -> one, guide then form) draw every output (one browser at a time) + our gates
  py bp_eval.py judge opus|gpt        blind A-D, 2 passes (order changed)
  py bp_eval.py table                 numbers -> table.json + policy.json here
  py bp_eval.py collect               copy states, final files, gate results and judge records into raw/ here

Four tasks never used in this repo's evals, fixtures or docs (checked with git grep before any run), fixed before any run.
Same launch flags as the two cross-vendor rounds: no permission or sandbox bypass, install commands denied, Codex -s workspace-write
with the network off, isolated CODEX_HOME with [windows] sandbox = "unelevated", at most 2 makers or judges at a time, one browser at a
time. Codex work folders: C:\\Users\\User\\Downloads\\xv-eval-work\\blanks\\ (deleted after the round). Nothing in the owner's ~/.claude,
~/.codex, ~/.agents is written.
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
NEW = S / "xv3"
e.X = NEW
orch.LOG = NEW / "eval.log"
e.CODEX_WORK = Path(r"C:\Users\User\Downloads\xv-eval-work") / "blanks"
CFG_HARNESS = S / "cfg-harness3"
e.TASKS = {
    "hwpx-notice": dict(kind="hwpx", name="가정통신문(hwpx)", p="2학년 스케이트 체험학습 안내 가정통신문을 한글 파일(hwpx)로 만들어 줘"),
    "public-ppt": dict(kind="pptx", name="공공 보고 PPT", p="교육지원청 보고용 '2026학년도 학교 급식 잔반 줄이기 사업 운영 결과' 발표자료 만들어 줘 (파워포인트 파일로)"),
    "promo-ppt": dict(kind="pptx", name="홍보 PPT", p="우리 학교 가족 걷기 대회 홍보용 PPT 만들어 줘 (6장, 파워포인트 파일로)"),
    "pdf-guide": dict(kind="pdf", name="안내문+신청서(PDF)", p="겨울방학 코딩 캠프 참가 안내문과 신청서를 PDF로 만들어 줘"),
}
e.FMT["pdf"] = "PDF 문서 (각 쪽을 그대로 그림으로 바꾼 것. 모든 결과물에 똑같이 적용됨)"
_claude = e.claude


def interpreter_rules() -> list[str]:
    """Allow rules for the SAME four programs when a maker calls them by full path instead of by name.

    Round 1 of this eval allowed only commands that start with py / python / python3 / node. One Claude run called Python as
    "C:/Users/.../Python313/python.exe" script.py and was refused, so no file came out (hwpx-notice-claude-harness-2). The path is the same
    program the name resolves to, so it is allowed too: every path `py`, `python`, `python3`, `node` and this interpreter resolve to on
    this PC, written with back or forward slashes or the Git Bash /c/ form, bare or quoted.
    Checked 2026-11-21 with a one-command probe: Bash `"C:/.../python.exe" -c ...` now runs. PowerShell's call-operator form
    (`& "C:/.../python.exe" ...`) is still refused by the permission layer itself ("contains multiple operations") whatever allow rule
    is given (path, quoted path, *python.exe*, python.exe:*), so it stays refused; the same run then falls back to Bash or `py`.
    Nothing else is opened: the install deny list still wins over every allow rule."""
    paths = {str(Path(sys.executable))}
    for name in ("py", "python", "python3", "node"):
        w = shutil.which(name)
        if w and "WindowsApps" not in w:  # the Store stub is not an interpreter
            paths.add(str(Path(w)))
            try:
                paths.add(str(Path(w).resolve()))
            except OSError:
                pass
    rules: list[str] = []
    for p in sorted(paths):
        fwd = p.replace("\\", "/")
        forms = {p, fwd}
        if len(fwd) > 2 and fwd[1] == ":":
            forms.add("/" + fwd[0].lower() + fwd[2:])
        for f in sorted(forms):
            for tool, heads in (("Bash", (f, f'"{f}"', f"'{f}'")), ("PowerShell", (f, f'"{f}"', f"'{f}'"))):
                rules += [f"{tool}({h}:*)" for h in heads]
    return rules


ALLOW_MAKER = list(e.ALLOW_MAKER) + interpreter_rules()


def claude(prompt, model, cfg, cwd, **kw):  # the harness condition reads the freshly installed skills
    if Path(cfg).name == "cfg-harness":
        cfg = CFG_HARNESS
    if kw.get("mode", "acceptEdits") == "acceptEdits":  # makers only (bare and harness alike); the judge keeps its Read-only list
        kw.setdefault("allow", ALLOW_MAKER)
    return _claude(prompt, model, cfg, cwd, **kw)


e.claude = claude


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
    for cond in ("codex-bare", "codex-harness"):  # bare is also the GPT judge's home
        d = NEW / cond
        d.mkdir(exist_ok=True)
        for f in ("auth.json", "config.toml"):
            if not (d / f).exists():
                shutil.copyfile(OLD / "codex-bare" / f, d / f)
    for h in (NEW / "home-codex", NEW / "home-claude"):
        if h.exists():
            shutil.rmtree(h)
    copy_skills(install("codex", NEW / "home-codex"), NEW / "codex-harness" / "skills")
    CFG_HARNESS.mkdir(exist_ok=True)
    for f in (".claude.json", ".credentials.json"):
        if (S / "cfg-harness" / f).exists():
            shutil.copyfile(S / "cfg-harness" / f, CFG_HARNESS / f)
    copy_skills(install("claude-code", NEW / "home-claude"), CFG_HARNESS / "skills")
    e.CODEX_WORK.mkdir(parents=True, exist_ok=True)


def cmd_fix_pdf():
    """The PDF task asks for two things (안내문 + 신청서). A run that saved them as two files is drawn from both: the guide first,
    then the form, merged into the judged out.pdf (same rule for every condition; like round 1's two-HTML rule for the club task).
    A run with one PDF, or with one PDF that already holds both, is left as it is."""
    from pypdf import PdfReader, PdfWriter
    for jd in sorted((NEW / "runs").glob("pdf-guide-*")):
        stf = jd / "state.json"
        if not stf.exists():
            continue
        st = json.loads(stf.read_text(encoding="utf-8"))
        if st.get("merged") is not None:
            continue
        wd = (e.CODEX_WORK / jd.name / "work") if st["vendor"] == "codex" else (jd / "work")
        pdfs = [f for f in sorted(wd.rglob("*.pdf")) if not f.name.startswith(("_", "~$"))
                and not any(x in str(f).replace("\\", "/") for x in ("/node_modules/", "/shared/", "/.claude/", "/_review/", "/vendor/"))]
        st["merged"] = []
        if len(pdfs) >= 2:
            def has(f, w):
                try:
                    return w in "".join((pg.extract_text() or "") for pg in PdfReader(str(f)).pages).replace(" ", "")
                except Exception:
                    return False
            both = [f for f in pdfs if has(f, "신청서") and has(f, "안내") and len(PdfReader(str(f)).pages) >= 2 and "신청" in f.stem and "안내" in f.stem]
            if both:
                shutil.copy2(both[0], jd / "out.pdf")
                st["merged"] = [both[0].name]
            else:
                guide = [f for f in pdfs if "안내" in f.stem and "신청" not in f.stem] or [f for f in pdfs if "신청" not in f.stem]
                form = [f for f in pdfs if "신청" in f.stem and f not in guide[:1]]
                pick = (guide[:1] + form[:1]) if (guide and form) else pdfs[:2]
                w = PdfWriter()
                for f in pick:
                    for pg in PdfReader(str(f)).pages:
                        w.add_page(pg)
                with open(jd / "out.pdf", "wb") as fh:
                    w.write(fh)
                st["merged"] = [f.name for f in pick]
            for x in ("render.json", "autocheck.json"):
                if (jd / x).exists():
                    (jd / x).unlink()
            print("pdf", jd.name, "->", st["merged"])
        stf.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_table():
    sys.argv = ["x"]
    import xv_table
    xv_table.HERE = HERE
    xv_table.main()
    import bp_policy
    bp_policy.main(NEW, e, HERE)


def cmd_collect():
    """What the document cites: every run's state, final file, gate result and (hwpx / pptx) spec, and every judge record."""
    raw = HERE / "raw"
    for jd in sorted((NEW / "runs").iterdir()):
        if not (jd / "state.json").exists():
            continue
        dst = raw / "runs" / jd.name
        dst.mkdir(parents=True, exist_ok=True)
        for p in jd.iterdir():
            if p.is_file() and (p.name in ("state.json", "render.json", "autocheck.json") or p.name.startswith("out")):
                shutil.copy2(p, dst / p.name)
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
        sys.exit(e.cmd_run(a[1], a[2], a[3:] or list(e.TASKS)))
    elif c == "render":
        cmd_fix_pdf()
        e.cmd_render()
    elif c == "judge":
        sys.exit(e.cmd_judge(a[1], a[2:] or list(e.TASKS)))
    elif c == "table":
        cmd_table()
    elif c == "collect":
        cmd_collect()
    else:
        print(__doc__)
