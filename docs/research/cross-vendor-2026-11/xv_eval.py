#!/usr/bin/env python3
"""Cross-vendor eval: bare model vs Teacher Studio harness, makers Claude Sonnet and GPT (Codex CLI), judges Claude Opus and GPT.

  py xv_eval.py run VENDOR COND [task...]   VENDOR = claude | codex, COND = bare | harness; 2 runs per task, 2 at a time
  py xv_eval.py render                      draw every output (one browser at a time) + run our gates
  py xv_eval.py judge JUDGE [task...]       JUDGE = opus | gpt; blind A-D (random labels), 2 passes (order changed)
  py xv_eval.py table                       numbers -> table.json (+ printed)

Reuses the ceiling eval helpers (docs/research/ceiling-eval-2026-11/raw/orch.py): claude() wrapper, renderers, gates.
Isolated settings (nothing in the owner's ~/.claude, ~/.codex, ~/.agents is written):
Launch flags (no permission or sandbox bypass anywhere; earlier rounds used bypassPermissions, so numbers are not directly comparable):
  claude maker: claude -p --model sonnet --permission-mode acceptEdits --allowedTools <ALLOW_MAKER> --disallowedTools <DENY>
  opus judge  : claude -p --model opus --permission-mode default --allowedTools Read --disallowedTools <DENY_JUDGE>
  codex maker : codex exec --skip-git-repo-check -m gpt-6.2-sol -s workspace-write (network off);  gpt judge: -s read-only
  claude bare    = CLAUDE_CONFIG_DIR scratch/cfg-bare (login only)
  claude harness = CLAUDE_CONFIG_DIR scratch/cfg-harness + skills/ from `setup.py --agent claude-code` run with a redirected home
  codex bare     = CODEX_HOME scratch/xv/codex-bare (copy of auth.json + 3-line config.toml)
  codex harness  = same + skills/ = the 8 folders `setup.py --agent codex` installed into a redirected home
"""
import json, os, random, shutil, subprocess, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(r"C:\Users\User\Downloads\teacher-studio")
sys.path.insert(0, str(REPO / "docs/research/ceiling-eval-2026-11/raw"))
import orch  # noqa: E402
from orch import S, usage_of, extract_json, find_deliverable, render_output, run_checks  # noqa: E402

X = S / "xv"
orch.LOG = X / "eval.log"
SUFFIX = orch.SUFFIX  # " 알아서 끝까지 만들어 줘. 결과 파일은 지금 폴더에 저장해 줘."
RUNS = int(os.environ.get("XV_RUNS", "2"))
CAP = 1500
CODEX_JS = r"C:\Users\User\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
GPT = "gpt-6.2-sol"
# six topics never used in this repo's evals, fixtures or docs (checked with git grep), fixed before any run
TASKS = {
    "class-ppt": dict(kind="pptx", name="수업 PPT", p="중학교 3학년 역사 '조선 후기 실학의 등장' 수업용 PPT 만들어 줘 (10장 정도, 파워포인트 파일로)"),
    "public-ppt": dict(kind="pptx", name="공공 보고 PPT", p="교육지원청 보고용 '2026학년도 늘봄학교 운영 결과' 발표자료 만들어 줘 (파워포인트 파일로)"),
    "hwpx-notice": dict(kind="hwpx", name="가정통신문(hwpx)", p="3학년 생존 수영 실기교육 안내 가정통신문을 한글 파일(hwpx)로 만들어 줘"),
    "game": dict(kind="html", name="복습 게임", p="초등학교 6학년 과학 '우리 몸의 소화 기관' 복습 게임 만들어 줘"),
    "webapp": dict(kind="html", name="수업 도우미", p="중학교 2학년 수학 '경우의 수'를 직접 해 보며 익히는 수업 도우미 프로그램 만들어 줘"),
    "general": dict(kind="html", name="일반(동호회)", p="동네 배드민턴 동호회 월례 대회에서 쓸 대진표와 점수판 만들어 줘"),
}
# Codex's Windows sandbox cannot write under %TEMP% (access denied), so Codex work folders live outside it and outside any git repo
CODEX_WORK = Path(r"C:\Users\User\Downloads\xv-eval-work")
# Restricted launch (this round): no permission bypass. Bare and harness get the identical tool set; only the skills differ.
ALLOW_MAKER = ["Read", "Write", "Edit", "Glob", "Grep", "Skill", "Bash(py:*)", "Bash(python:*)", "Bash(python3:*)", "Bash(node:*)",
               "PowerShell(py:*)", "PowerShell(python:*)", "PowerShell(python3:*)", "PowerShell(node:*)"]  # same four programs in the Windows shell tool
_DENY_CMDS = ["winget", "msiexec", "choco", "scoop", "pip install", "pip3 install", "py -m pip", "python -m pip", "python3 -m pip", "npm install", "npm i", "npx"]
DENY = ([f"{t}({c}:*)" for t in ("Bash", "PowerShell") for c in _DENY_CMDS]
        + [f"{t}(*{w}*)" for t in ("Bash", "PowerShell") for w in ("winget", "msiexec", "choco ", "scoop ", "pip install", "-m pip", "npm install", "npm i ", "npx ", "Install-", "Start-Process", "setx ", "reg add")])
ALLOW_JUDGE = ["Read"]
DENY_JUDGE = ["Bash", "PowerShell", "Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch", "Agent", "Task"]


def claude(prompt, model, cfg, cwd, session_id=None, cap=CAP, mode="acceptEdits", allow=ALLOW_MAKER, deny=DENY):
    """claude -p without bypass: --permission-mode acceptEdits (makers) / default (judge) + --allowedTools/--disallowedTools."""
    orch.sync_creds()
    cmd = [orch.CLAUDE, "-p", "--model", model, "--permission-mode", mode, "--output-format", "json",
           "--allowedTools", ",".join(allow), "--disallowedTools", ",".join(deny)]
    if session_id:
        cmd += ["--session-id", session_id]
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg), PYTHONUTF8="1")
    p = None
    for _try in range(30):  # claude.exe replaces itself during an auto-update; wait for the new file
        try:
            p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            break
        except OSError as ex:
            orch.log("Popen OSError, retry", _try, str(ex)[:80])
            time.sleep(20)
    if p is None:
        raise RuntimeError("LOGIN/LIMIT-like stop: cannot start claude.exe")
    t0 = time.time()
    timed_out = False
    try:
        out, err = p.communicate(prompt.encode("utf-8"), timeout=cap)
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)  # only the tree this call started
        try:
            out, err = p.communicate(timeout=20)
        except Exception:
            out, err = b"", b""
    txt = out.decode("utf-8", "replace")
    data = None
    for line in [txt] + list(reversed(txt.strip().splitlines())):
        try:
            data = json.loads(line)
            break
        except Exception:
            pass
    return dict(secs=time.time() - t0, timed_out=timed_out, rc=p.returncode, raw=txt, err=err.decode("utf-8", "replace")[:2000], data=data)


CONDS = [("claude", "bare"), ("claude", "harness"), ("codex", "bare"), ("codex", "harness")]
LIMIT_WORDS = ("usage limit", "rate limit", "login", "authenticate", "credit", "quota", "unauthorized", "401", "not supported", "hit your")


def codex(prompt, home, cwd, sandbox="workspace-write", images=(), cap=CAP, outdir=None):
    outdir = Path(outdir or cwd)
    last = outdir / "_codex_last.txt"
    cmd = ["node", CODEX_JS, "exec"]
    for im in images:
        cmd += ["-i", str(im)]
    cmd += ["--skip-git-repo-check", "-m", GPT, "-s", sandbox, "--json", "-o", str(last), "-C", str(cwd), "-"]
    env = dict(os.environ, CODEX_HOME=str(home), PYTHONUTF8="1")
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        out, err = p.communicate(prompt.encode("utf-8"), timeout=cap)
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)  # only the tree this call started
        try:
            out, err = p.communicate(timeout=20)
        except Exception:
            out, err = b"", b""
    secs = time.time() - t0
    txt = out.decode("utf-8", "replace")
    (outdir / "_codex_events.jsonl").write_text(txt, encoding="utf-8")
    (outdir / "_codex_err.txt").write_text(err.decode("utf-8", "replace")[-6000:], encoding="utf-8")
    tok = dict(input=0, cached=0, output=0, reasoning=0)
    errors, cmds, failed_cmds = [], 0, 0
    for line in txt.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        t = e.get("type", "")
        if t == "turn.completed":
            u = e.get("usage", {})
            tok["input"] += u.get("input_tokens", 0); tok["cached"] += u.get("cached_input_tokens", 0)
            tok["output"] += u.get("output_tokens", 0); tok["reasoning"] += u.get("reasoning_output_tokens", 0)
        elif t in ("error", "turn.failed"):
            errors.append(json.dumps(e, ensure_ascii=False)[:400])
        elif t == "item.completed" and e.get("item", {}).get("type") == "command_execution":
            cmds += 1
            if e["item"].get("exit_code") not in (0, None):
                failed_cmds += 1
    res = last.read_text(encoding="utf-8", errors="replace") if last.exists() else ""
    return dict(secs=secs, timed_out=timed_out, rc=p.returncode, result=res, tok=tok, errors=errors, cmds=cmds, failed_cmds=failed_cmds)


def is_limit(text):
    low = text.lower()
    return any(w in low for w in LIMIT_WORDS)


def opens_ok(f, kind):
    try:
        if kind == "pptx":
            from pptx import Presentation
            return len(Presentation(str(f)).slides) > 0
        if kind == "hwpx":
            import zipfile
            z = zipfile.ZipFile(str(f))
            return any(n.startswith("Contents/section") for n in z.namelist()) and z.testzip() is None
        return f.stat().st_size > 500
    except Exception:
        return False


def run_one(task, vendor, cond, n):
    name = f"{task}-{vendor}-{cond}-{n}"
    jd = X / "runs" / name
    if (jd / "state.json").exists():
        return json.loads((jd / "state.json").read_text(encoding="utf-8"))
    wd = (CODEX_WORK / name / "work") if vendor == "codex" else (jd / "work")
    if wd.exists():
        (X / "discarded").mkdir(exist_ok=True)
        shutil.move(str(wd), str(X / "discarded" / f"{name}-work-{int(time.time())}"))
    wd.mkdir(parents=True)
    jd.mkdir(parents=True, exist_ok=True)
    kind = TASKS[task]["kind"]
    prompt = TASKS[task]["p"] + SUFFIX
    if vendor == "claude":
        r = claude(prompt, "sonnet", S / ("cfg-harness" if cond == "harness" else "cfg-bare"), wd, session_id=str(uuid.uuid4()), cap=CAP)
        d = r["data"] or {}
        res = str(d.get("result", ""))
        (jd / "_result.json").write_text(r["raw"], encoding="utf-8")
        if d.get("is_error") and is_limit(res):
            raise RuntimeError(f"LOGIN/LIMIT claude: {res[:200]}")
        st = dict(secs=round(r["secs"]), timed_out=r["timed_out"], cost=usage_of(d)["cost"], out_tok=usage_of(d)["out_tok"], turns=d.get("num_turns"),
                  is_error=bool(d.get("is_error")) or not d, last=res[-1500:],
                  denials=[(x.get("tool_name"), str((x.get("tool_input") or {}).get("command", ""))[:200]) for x in (d.get("permission_denials") or [])][:40])
    else:
        r = codex(prompt, X / ("codex-harness" if cond == "harness" else "codex-bare"), wd, outdir=jd)
        if r["errors"] and is_limit(" ".join(r["errors"])) and not r["result"]:
            raise RuntimeError(f"LOGIN/LIMIT codex: {r['errors'][0][:300]}")
        st = dict(secs=round(r["secs"]), timed_out=r["timed_out"], cost=None, out_tok=r["tok"]["output"], tok=r["tok"], turns=r["cmds"], failed_cmds=r["failed_cmds"],
                  is_error=bool(r["errors"]) or r["rc"] != 0, errors=r["errors"][:3], last=r["result"][-1500:])
    f = find_deliverable(wd, kind)
    st.update(name=name, task=task, vendor=vendor, cond=cond, run=n, file=f.name if f else None,
              all_files=sorted(str(p.relative_to(wd)) for p in wd.rglob("*") if p.is_file() and "node_modules" not in str(p))[:40])
    if f:
        shutil.copy2(f, jd / ("out" + orch.EXT[kind]))
        st["opens"] = opens_ok(f, kind)
    (jd / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    orch.log("ran", name, st["secs"], st["cost"], st["file"])
    print("ran", name, st["secs"], "s", st["cost"], st["file"], "ERR" if st["is_error"] else "", flush=True)
    return st


def pool(fn, jobs):
    stop = []

    def go(j):
        if stop:
            return None
        try:
            return fn(*j)
        except RuntimeError as e:
            stop.append(str(e))
            print("STOP", e, flush=True)
        except Exception as e:
            print("EXC", j, repr(e)[:300], flush=True)
    with ThreadPoolExecutor(int(os.environ.get("EVAL_WORKERS", "2"))) as ex:
        list(ex.map(go, jobs))
    if stop:
        print("STOPPED on login/limit error:", stop[0])
        return 2
    return 0


def cmd_run(vendor, cond, tasks):
    return pool(run_one, [(t, vendor, cond, n) for n in range(1, RUNS + 1) for t in tasks])


def out_file(jd, kind):
    f = jd / ("out" + orch.EXT[kind])
    return f if f.exists() else None


def cmd_render():
    for jd in sorted((X / "runs").iterdir()):
        stf = jd / "state.json"
        if not stf.exists() or (jd / "render.json").exists():
            continue
        st = json.loads(stf.read_text(encoding="utf-8"))
        kind = TASKS[st["task"]]["kind"]
        f = out_file(jd, kind)
        if not f:
            (jd / "render.json").write_text(json.dumps(dict(pngs=[], notes=["no deliverable"]), ensure_ascii=False), encoding="utf-8")
            continue
        pngs, notes = render_output(f, kind, jd / "render")
        run_checks(f, kind, jd / "autocheck.json")
        (jd / "render.json").write_text(json.dumps(dict(pngs=[Path(p).name for p in pngs], notes=notes), ensure_ascii=False, indent=1), encoding="utf-8")
        print("rendered", jd.name, len(pngs), flush=True)


def out_pngs(jd, kind):
    d = jd / "render"
    if not d.exists():
        return []
    if kind == "hwpx":
        return sorted(d.glob("hwpx-*.png"))
    return sorted(p for p in d.glob("*.png") if "sheet" not in p.name and p.name != "full.png")


def montage(imgs, out, cols=3, w=640, label=None):
    from PIL import Image, ImageDraw, ImageFont

    def font(sz):
        for n in ("malgunbd.ttf", "malgun.ttf", "arial.ttf"):
            try:
                return ImageFont.truetype(n, sz)
            except Exception:
                pass
        return ImageFont.load_default()
    ims = [Image.open(p).convert("RGB") for p in imgs]
    top = 70 if label else 0
    if not ims:
        im = Image.new("RGB", (w * 2, 260), "white")
        d = ImageDraw.Draw(im)
        d.text((16, 6), label or "", fill=(0, 0, 0), font=font(54))
        d.text((16, 110), "NO OUTPUT (요청한 형식의 결과 파일이 없음)", fill="red", font=font(40))
        im.save(out)
        return out
    ts = [im.resize((w, int(im.height * w / im.width))) for im in ims]
    rows = [ts[i:i + cols] for i in range(0, len(ts), cols)]
    rh = [max(t.height for t in r) for r in rows]
    sheet = Image.new("RGB", (cols * (w + 8) + 8, sum(rh) + 8 * (len(rows) + 1) + top), (225, 225, 225))
    d = ImageDraw.Draw(sheet)
    if label:
        d.text((16, 6), label, fill=(0, 0, 0), font=font(54))
    y = top + 8
    for r, h in zip(rows, rh):
        for i, t in enumerate(r):
            sheet.paste(t, (8 + i * (w + 8), y))
        y += h + 8
    sheet.save(out)
    return out


JUDGE = """너는 공정한 심사위원이야. 같은 요청에 대해 서로 다른 4곳(A, B, C, D)이 만든 결과물이 있어. 어느 쪽이 어떤 AI·어떤 방식으로 만들었는지는 모르고, 알려 하지도 마.

[요청]
{req}

[보는 법] {how} 각 그림은 한 결과물의 화면을 순서대로 이어 붙인 것이고, 왼쪽 위에 글자(A~D)가 있어. 「A (2)」처럼 번호가 붙은 그림은 같은 결과물의 뒤쪽 장이야.
결과물 형식: {fmt}
명령 실행이나 파일 수정은 하지 말고 그림만 보고 평가해.

[채점] 각 결과물을 항목마다 1~5점(정수)으로:
- content: 내용의 질 (사실이 맞는가, 구체적인가, 실제 자료·예시·수치가 있는가, 깊이와 완결성, 채우지 않은 빈칸이 없는가)
- design: 디자인 (색·구성·시각적 위계·정돈된 느낌, 알맞은 표현 방식, 단조롭지 않음)
- readability: 가독성 (글자가 읽히는 크기인가, 대비, 겹침·잘림·빈 화면 없음, 정보량이 알맞은가)
- fit: 목적 적합성 (요청한 대상·용도·분량·형식에 맞고, 고치지 않고 바로 쓸 수 있는가)
그림에 안 보이는 것은 추측하지 말고 보이는 대로만 평가해. 결과물이 없거나 깨졌으면 네 항목 모두 1점. 마지막에 1위부터 4위까지 순위(동점 없이)를 매겨.

[출력] 마지막 답변은 JSON 하나만 (코드블록·다른 말 없이):
{{"A":{{"content":0,"design":0,"readability":0,"fit":0,"note":"한두 문장: 강점과 약점"}},"B":{{"content":0,"design":0,"readability":0,"fit":0,"note":"..."}},"C":{{"content":0,"design":0,"readability":0,"fit":0,"note":"..."}},"D":{{"content":0,"design":0,"readability":0,"fit":0,"note":"..."}},"ranking":["1위 글자","2위","3위","4위"]}}
"""
FMT = {"pptx": ".pptx 슬라이드 (이 PC에 PowerPoint가 없어 파일 안의 도형·글·표·차트를 그대로 읽어 그린 근사 그림. 글꼴·줄바꿈이 실제와 조금 다를 수 있고 모든 결과물에 똑같이 적용됨)",
       "hwpx": "한글(.hwpx) 문서 (같은 미리보기 도구로 근사해 그린 그림. 모든 결과물에 똑같이 적용됨)",
       "html": "브라우저에서 여는 HTML 한 파일 (시작 화면, 버튼을 3번 눌러 본 화면, 맨 아래 화면을 이어 붙인 그림. 움직임·소리는 안 보임)"}
KEYS = ("content", "design", "readability", "fit")


def judge_one(judge, task, n, pn):
    jd = X / "judge" / judge / f"{task}-{n}-pass{pn}"
    resf = X / "judge" / judge / f"{task}-{n}-pass{pn}.json"
    if resf.exists():
        return json.loads(resf.read_text(encoding="utf-8"))
    rnd = random.Random(f"xv-{task}-{n}")  # same label order for both judges
    perm = CONDS[:]
    rnd.shuffle(perm)
    if pn == 2:
        perm = perm[::-1]
        perm = perm[1:] + perm[:1]
    if jd.exists():
        shutil.rmtree(jd)
    jd.mkdir(parents=True)
    kind = TASKS[task]["kind"]
    files, mapping = [], {}
    for lab, (v, c) in zip("ABCD", perm):
        mapping[lab] = f"{v}-{c}"
        ps = out_pngs(X / "runs" / f"{task}-{v}-{c}-{n}", kind)[:12]
        for k in range(0, max(len(ps), 1), 6):
            fn = f"{lab}{'' if k == 0 else k // 6 + 1}.png"
            montage(ps[k:k + 6], jd / fn, label=lab + ("" if k == 0 else f" ({k // 6 + 1})"))
            files.append(fn)
    if judge == "opus":
        how = f"현재 폴더에 {', '.join(files)} 가 있어. Read 도구로 모두 직접 열어서 봐."
    else:
        how = f"이 메시지에 그림 {len(files)}장이 붙어 있어 ({', '.join(files)} 순서). 모두 봐."
    prompt = JUDGE.format(req=TASKS[task]["p"], how=how, fmt=FMT[kind])
    (jd / "_prompt.txt").write_text(prompt, encoding="utf-8")
    if judge == "opus":
        r = claude(prompt, "opus", S / "cfg-reviewer", jd, cap=900, mode="default", allow=ALLOW_JUDGE, deny=DENY_JUDGE)
        d = r["data"] or {}
        res = str(d.get("result", ""))
        if d.get("is_error") and is_limit(res):
            raise RuntimeError(f"LOGIN/LIMIT opus judge: {res[:200]}")
        cost, secs = usage_of(d)["cost"], r["secs"]
    else:
        r = codex(prompt, X / "codex-bare", jd, sandbox="read-only", images=[jd / f for f in files], cap=900)
        res = r["result"]
        if r["errors"] and is_limit(" ".join(r["errors"])) and not res:
            raise RuntimeError(f"LOGIN/LIMIT gpt judge: {r['errors'][0][:300]}")
        cost, secs = None, r["secs"]
    j = extract_json(res)
    ok = bool(j) and all(isinstance(j.get(l), dict) and all(k in j[l] for k in KEYS) for l in "ABCD")
    rec = dict(judge=judge, task=task, run=n, pass_=pn, mapping=mapping, result=j, cost=cost, secs=round(secs), raw=res[:2500])
    if ok:
        resf.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print("judged", judge, task, n, pn, ok, flush=True)
    return rec


def cmd_judge(judge, tasks):
    return pool(lambda *a: judge_one(judge, *a), [(t, n, pn) for t in tasks for n in range(1, RUNS + 1) for pn in (1, 2)])


if __name__ == "__main__":
    a = sys.argv[1:]
    c = a[0] if a else ""
    if c == "run":
        sys.exit(cmd_run(a[1], a[2], a[3:] or list(TASKS)))
    elif c == "render":
        cmd_render()
    elif c == "judge":
        sys.exit(cmd_judge(a[1], a[2:] or list(TASKS)))
    elif c == "table":
        import xv_table
        xv_table.main()
    else:
        print(__doc__)
