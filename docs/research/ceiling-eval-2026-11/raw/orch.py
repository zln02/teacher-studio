#!/usr/bin/env python3
"""Ceiling eval orchestrator. Usage: py orch.py run [--only task-cond ...]"""
import json, os, sys, time, uuid, shutil, subprocess, threading, re, glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

os.environ["PYTHONUTF8"] = "1"
S = Path(r"C:\Users\User\AppData\Local\Temp\claude\30da2aaa5cef6c30\c8098317-2fbb-4131-bf8f-07218752ac6e\scratchpad")
REPO = Path(r"C:\Users\User\Downloads\teacher-studio")
CLAUDE = r"C:\Users\User\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
JOBS = S / "jobs"
SK = REPO / "skills"
CAP = 1500
SUFFIX = " 알아서 끝까지 만들어 줘. 결과 파일은 지금 폴더에 저장해 줘."
BROWSER = threading.Lock()
LOG = S / "orch.log"
MODELS = {"fable": "claude-fable-5-2", "sonnet": "sonnet"}

TASKS = {
 "class-ppt": dict(kind="pptx", p="중2 과학 '빛의 반사와 굴절' 수업용 PPT 만들어 줘 (10장 정도, 파워포인트 파일로)"),
 "promo-ppt": dict(kind="pptx", p="우리 학교 가을 축제 홍보용 PPT 만들어 줘 (6장, 파워포인트 파일로)"),
 "public-ppt": dict(kind="pptx", p="교육청 보고용 '2026년 AI 활용 교육 추진 현황' 발표자료 만들어 줘 (파워포인트 파일로)"),
 "hwpx-notice": dict(kind="hwpx", p="현장체험학습 안내 가정통신문을 한글 파일(hwpx)로 만들어 줘. 참가 동의서도 붙여 줘"),
 "pdf-guide": dict(kind="pdf", p="학부모 상담 주간 안내문을 PDF로 만들어 줘", step2="이 PDF 끝에 신청서 페이지를 하나 붙여 줘"),
 "game": dict(kind="html", p="초5 사회 '우리 지역의 문화유산' 복습 게임 만들어 줘"),
 "webapp": dict(kind="html", p="고1 수학 일차함수 그래프를 직접 바꿔 보며 익히는 프로그램 만들어 줘"),
 "unseen": dict(kind="html", p="학급 1인 1역할 정하기를 공정하게 도와주는 도구 만들어 줘"),
}
EXT = {"pptx": ".pptx", "hwpx": ".hwpx", "pdf": ".pdf", "html": ".html"}


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def cfg_for(cond, model_key):
    return S / ("cfg-harness" if cond == "harness" else "cfg-bare")


CRED_LOCK = threading.Lock()
def sync_creds():
    import glob as _g
    with CRED_LOCK:
        best = None; bexp = -1
        for f in _g.glob(str(S / "cfg-*" / ".credentials.json")) + [os.path.expanduser("~/.claude/.credentials.json")]:
            try:
                e = json.load(open(f, encoding="utf-8")).get("claudeAiOauth", {}).get("expiresAt", 0)
            except Exception:
                continue
            if e > bexp: bexp, best = e, f
        for d in _g.glob(str(S / "cfg-*")):
            tgt = os.path.join(d, ".credentials.json")
            if best and os.path.abspath(tgt) != os.path.abspath(best):
                try:
                    cur = json.load(open(tgt, encoding="utf-8")).get("claudeAiOauth", {}).get("expiresAt", 0)
                except Exception:
                    cur = -1
                if cur < bexp: shutil.copy2(best, tgt)


def claude(prompt, model, cfg, cwd, session_id=None, resume=None, cap=CAP):
    sync_creds()
    cmd = [CLAUDE, "-p", "--model", model, "--permission-mode", "bypassPermissions", "--output-format", "json"]
    if resume:
        cmd += ["--resume", resume]
    elif session_id:
        cmd += ["--session-id", session_id]
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg), PYTHONUTF8="1")
    t0 = time.time()
    p = None
    for _try in range(30):
        try:
            p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            break
        except OSError as e:
            log("Popen OSError, retry", _try, str(e)[:80]); time.sleep(20)
    if p is None: raise RuntimeError("cannot start claude")
    t0 = time.time()
    timed_out = False
    try:
        out, err = p.communicate(prompt.encode("utf-8"), timeout=cap)
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
        try:
            out, err = p.communicate(timeout=20)
        except Exception:
            out, err = b"", b""
    secs = time.time() - t0
    txt = out.decode("utf-8", "replace")
    data = None
    try:
        data = json.loads(txt)
    except Exception:
        # sometimes multiple JSON lines
        for line in reversed(txt.strip().splitlines()):
            try:
                data = json.loads(line); break
            except Exception:
                pass
    if data and data.get("is_error") and "authenticate" in str(data.get("result", "")):
        log("AUTH FAIL", str(data.get("result"))[:100]); raise RuntimeError("AUTH FAIL")
    return dict(secs=secs, timed_out=timed_out, rc=p.returncode, raw=txt, err=err.decode("utf-8", "replace")[:2000], data=data)


def usage_of(d):
    if not d: return dict(cost=0, out_tok=0, in_tok=0)
    u = d.get("usage", {}) or {}
    return dict(cost=d.get("total_cost_usd", 0) or 0, out_tok=u.get("output_tokens", 0),
                in_tok=(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)))


def find_deliverable(wd, kind):
    ext = EXT[kind]
    cands = []
    for f in Path(wd).rglob("*" + ext):
        s = str(f).replace("\\", "/")
        if any(x in s for x in ("/node_modules/", "/shared/", "/.claude/", "/_review/", "/_snap/", "/vendor/", "/__pycache__/")):
            continue
        if f.name.startswith("_") or f.name.startswith("~$"):
            continue
        cands.append(f)
    if not cands: return None
    if kind == "html":
        # prefer the biggest recently modified html (the app) - not preview/spec helper files
        cands.sort(key=lambda f: (f.stat().st_size), reverse=True)
        return cands[0]
    cands.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return cands[0]


# ---------------- rendering ----------------
def pw_launch(p):
    try:
        return p.chromium.launch(channel="chrome", args=["--mute-audio"])
    except Exception:
        return p.chromium.launch(args=["--mute-audio"])


def render_output(f, kind, outdir):
    """returns list of png paths + notes. Holds the browser lock."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    notes = []
    pngs = []
    with BROWSER:
        try:
            if kind == "pptx":
                r = subprocess.run(["py", str(SK / "teacher-slides/scripts/pptx_render.py"), str(f), "--out", str(outdir)],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
                notes.append((r.stdout or "")[-400:])
                pngs = sorted(p for p in outdir.glob("*.png") if "sheet" not in p.name)
                if not pngs:
                    pngs = sorted(outdir.glob("*.png"))
            elif kind == "hwpx":
                h = outdir / "preview.html"
                r = subprocess.run(["py", str(SK / "teacher-docs/scripts/hwpx_preview.py"), str(f), "--out", str(h)],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
                notes.append((r.stdout + r.stderr)[-300:])
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    b = pw_launch(p)
                    pg = b.new_page(viewport={"width": 900, "height": 1250})
                    pg.goto(h.resolve().as_uri()); pg.wait_for_timeout(400)
                    h_total = pg.evaluate("document.documentElement.scrollHeight")
                    n = max(1, min(6, int(h_total // 1200) + 1))
                    for i in range(n):
                        pth = outdir / f"hwpx-{i+1:02d}.png"
                        pg.screenshot(path=str(pth), full_page=False, clip=None) if n == 1 else None
                        if n > 1:
                            pg.evaluate(f"window.scrollTo(0,{i*1200})"); pg.wait_for_timeout(100)
                            pg.screenshot(path=str(pth))
                        pngs.append(pth)
                    pg.screenshot(path=str(outdir / "full.png"), full_page=True)
                    b.close()
            elif kind == "pdf":
                import fitz
                doc = fitz.open(str(f))
                for i, page in enumerate(doc):
                    if i >= 12: break
                    pth = outdir / f"pdf-{i+1:02d}.png"
                    page.get_pixmap(dpi=80).save(str(pth)); pngs.append(pth)
                notes.append(f"pages={len(doc)}")
            elif kind == "html":
                from playwright.sync_api import sync_playwright
                errs = []
                with sync_playwright() as p:
                    b = pw_launch(p)
                    pg = b.new_page(viewport={"width": 1600, "height": 900})
                    pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
                    pg.goto(Path(f).resolve().as_uri()); pg.wait_for_timeout(1200)
                    p1 = outdir / "html-01-start.png"; pg.screenshot(path=str(p1)); pngs.append(p1)
                    # click a primary-looking button, 3 times, shoot after each
                    sel = "button:visible, [role=button]:visible, a.btn:visible, input[type=button]:visible"
                    names = ["시작", "start", "Start", "플레이", "뽑기", "만들기", "다음", "게임"]
                    for k in range(3):
                        try:
                            clicked = False
                            for nm in names:
                                loc = pg.locator(sel, has_text=nm)
                                if loc.count() > 0:
                                    loc.first.click(timeout=2000); clicked = True; break
                            if not clicked:
                                loc = pg.locator(sel)
                                if loc.count() > 0:
                                    loc.first.click(timeout=2000); clicked = True
                            pg.wait_for_timeout(900)
                            pp = outdir / f"html-{k+2:02d}-click{k+1}.png"; pg.screenshot(path=str(pp)); pngs.append(pp)
                            if not clicked: break
                        except Exception as e:
                            notes.append("click: " + str(e)[:100]); break
                    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(300)
                    pe = outdir / "html-90-bottom.png"; pg.screenshot(path=str(pe)); pngs.append(pe)
                    b.close()
                notes.append("js_errors=" + json.dumps(errs, ensure_ascii=False))
        except Exception as e:
            notes.append("RENDER FAIL: " + repr(e)[:300])
    return [str(p) for p in pngs], notes


# ---------------- automated checks ----------------
def run_checks(f, kind, outpath):
    res = {}
    with BROWSER:
        try:
            if kind == "pptx":
                cmd = ["py", str(SK / "teacher-slides/scripts/pptx_check.py"), str(f)]
            elif kind in ("hwpx", "pdf"):
                cmd = ["py", str(SK / "teacher-docs/scripts/doc_check.py"), str(f)]
            else:
                cmds = []
            if kind == "html":
                r1 = subprocess.run(["py", str(SK / "teacher-game/scripts/check_game.py"), str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
                r2 = subprocess.run(["py", str(SK / "teacher-studio/scripts/check_webapp.py"), str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
                res = dict(check_game=dict(rc=r1.returncode, out=(r1.stdout + r1.stderr)[-3500:]),
                           check_webapp=dict(rc=r2.returncode, out=(r2.stdout + r2.stderr)[-3500:]))
            else:
                r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
                res = dict(check=dict(rc=r.returncode, out=(r.stdout + r.stderr)[-3500:]))
        except Exception as e:
            res = dict(error=repr(e))
    Path(outpath).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


# ---------------- reviewer ----------------
REVIEW_TMPL = """너는 깐깐하지만 공정한 검수자야. 선생님이 AI에게 아래 요청을 했고, AI가 만든 결과물이 지금 폴더에 있어.

[선생님의 원래 요청]
{req}

[결과물 파일] {fname}  (종류: {kind})
[화면 그림] 현재 폴더의 png 파일들 ({pngs}). {rnote}
이 그림을 Read 도구로 직접 열어서 보고, 필요하면 파일 자체도(압축 해제, 텍스트 추출 등) 열어 확인해.
{extra}

[고정 점검표] 아래 9가지를 하나씩 확인해:
1 열리고 작동하나 (파일이 정상, 게임/프로그램이면 눌러서 동작)
2 남은 빈칸 ([학교명], 20XX, OO, ○○, 000 같은 채우지 않은 자리)
3 글자 잘림·겹침·넘침
4 읽기 쉬운가 (글자 크기, 대비, 교실/TV에서)
5 요청한 형식이 맞나 (진짜 .pptx/.hwpx/.pdf/HTML 한 파일 등)
6 내용이 정확한가 (사실, 정답, 수식, 날짜)
7 개인정보 (실제 학생 이름·전화번호 등 넣지 않았나, 학생 정보 칸 없나)
8 인터넷 없이 되나 (외부 주소 요청 없음)
9 요청한 것에 맞나 (빠뜨린 것 없나, 분량·장수)

[할 일]
- 선생님이 열어 보고 "고쳐 주세요"라고 할 만한 실제 문제만 찾아. 취향 차이나 사소한 것은 무시해.
- 고칠 것이 있으면 가장 중요한 순서로 최대 3개, 선생님이 AI에게 말하듯 쉬운 한국어로 구체적으로 적어 (어디가 어떻게 문제인지, 어떻게 고치면 되는지). 개발 용어는 쓰지 마.
- 선생님이 그대로 써도 되는 수준이면 verdict를 「충분해요」로 해.
- 고쳐 달라는 말은 서로 모순되지 않게, 그리고 선생님이 실제로 불편해할 문제만 써. 학교 이름·담임 이름처럼 AI가 알 수 없는 정보를 손으로 채우도록 밑줄 빈칸으로 두고 안내했다면 그것은 문제로 보지 마(안내 없이 [학교명]·20XX·OO가 남은 것만 문제).
- 남은 것이 사소한 다듬기 수준이면 「충분해요」로 해.
- 근사 그림(approx)은 글꼴·줄바꿈이 실제와 다를 수 있으니 글자 넘침은 파일의 박스 크기/글자 길이도 함께 보고 판단해.

[출력] 마지막 답변은 아래 JSON 하나만 (코드블록·다른 말 없이):
{{"verdict": "충분해요" 또는 "고쳐요", "checklist": {{"1_열림작동": "OK 또는 문제 한 줄", "2_빈칸": "...", "3_잘림겹침": "...", "4_가독성": "...", "5_형식": "...", "6_정확성": "...", "7_개인정보": "...", "8_오프라인": "...", "9_요청부합": "..."}}, "fixes": ["고쳐 달라는 말 1", "..."]}}
"""


def extract_json(txt):
    if not txt: return None
    m = re.search(r"\{.*\}", txt, re.S)
    if not m: return None
    s = m.group(0)
    try:
        return json.loads(s)
    except Exception:
        # try trimming to last balanced
        for end in range(len(s), 0, -1):
            if s[end - 1] == "}":
                try:
                    return json.loads(s[:end])
                except Exception:
                    continue
    return None


def review(job, rd, f, kind, pngs, rnote, wd_logs, step_label):
    rdir = job / f"review-{step_label}"
    if rdir.exists(): shutil.rmtree(rdir)
    rdir.mkdir(parents=True)
    shutil.copy2(f, rdir / Path(f).name)
    pnames = []
    for p in pngs:
        shutil.copy2(p, rdir / Path(p).name); pnames.append(Path(p).name)
    extra = ""
    if kind == "html":
        extra = "HTML이면 파일을 직접 열어 소스도 훑어보고(외부 주소, 정답 오류), 필요하면 playwright로 직접 눌러 봐도 돼."
    if kind == "pdf" and rd.get("step2_done"):
        extra = "이 결과물은 먼저 안내문 PDF를 만들고, 이어서 「이 PDF 끝에 신청서 페이지를 하나 붙여 줘」라는 두 번째 요청까지 처리한 것이야. 두 요청을 모두 평가해."
    prompt = REVIEW_TMPL.format(req=rd["request_text"], fname=Path(f).name, kind=kind, pngs=", ".join(pnames[:14]), rnote=rnote, extra=extra)
    (rdir / "_prompt.txt").write_text(prompt, encoding="utf-8")
    r = claude(prompt, "opus", S / "cfg-reviewer", rdir, cap=900)
    (rdir / "_result.json").write_text(r["raw"], encoding="utf-8")
    d = r["data"] or {}
    txt = d.get("result", "") if isinstance(d, dict) else ""
    j = extract_json(txt)
    cost = usage_of(d)["cost"]
    if not j:
        log("REVIEW PARSE FAIL", job.name, txt[:200])
        j = dict(verdict="파싱실패", fixes=[], checklist={}, raw=txt[:500])
    j["_cost"] = cost; j["_secs"] = r["secs"]
    return j


# ---------------- job ----------------
def run_job(task, cond, mkey):
    name = f"{task}-{mkey}-{cond}"
    job = JOBS / name
    job.mkdir(parents=True, exist_ok=True)
    stf = job / "state.json"
    if stf.exists():
        st = json.loads(stf.read_text(encoding="utf-8"))
        if st.get("done"): return st
    t = TASKS[task]; kind = t["kind"]; model = MODELS[mkey]
    wd = job / "work"
    st = dict(name=name, task=task, cond=cond, model=mkey, rounds=[], done=False)
    if wd.exists(): shutil.rmtree(wd)
    wd.mkdir(parents=True)
    save = lambda: stf.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    cfg = cfg_for(cond, mkey)
    req1 = t["p"] + SUFFIX
    sid = str(uuid.uuid4())
    log("START", name)
    # base run (retry once on crash)
    r = claude(req1, model, cfg, wd, session_id=sid)
    attempts = [dict(secs=r["secs"], rc=r["rc"], timed_out=r["timed_out"], err=r["err"][:300])]
    if not r["timed_out"] and (not r["data"] or r["data"].get("is_error")):
        log("CRASH retry", name, r["err"][:200], (r["raw"] or "")[:200])
        shutil.rmtree(wd); wd.mkdir(parents=True)
        sid = str(uuid.uuid4())
        r2 = claude(req1, model, cfg, wd, session_id=sid)
        attempts.append(dict(secs=r2["secs"], rc=r2["rc"], timed_out=r2["timed_out"], err=r2["err"][:300]))
        r = r2
    st["attempts"] = attempts
    (job / "_base_result.json").write_text(r["raw"], encoding="utf-8")
    u = usage_of(r["data"])
    cur_sid = (r["data"] or {}).get("session_id") or sid
    total_secs = r["secs"]; total_cost = u["cost"]; out_tok = u["out_tok"]
    first_secs = r["secs"]
    final_text = (r["data"] or {}).get("result", "")
    st.update(first_secs=first_secs, first_cost=u["cost"], first_out_tok=u["out_tok"], first_timed_out=r["timed_out"],
              first_ok=bool(r["data"]) and not r["timed_out"], first_final_text=final_text[:1500],
              first_turns=(r["data"] or {}).get("num_turns"))
    rd = dict(request_text=req1)
    if "step2" in t:
        req2 = t["step2"] + SUFFIX
        r = claude(req2, model, cfg, wd, resume=cur_sid)
        (job / "_step2_result.json").write_text(r["raw"], encoding="utf-8")
        u2 = usage_of(r["data"])
        total_secs += r["secs"]; total_cost += u2["cost"]; out_tok += u2["out_tok"]
        cur_sid = (r["data"] or {}).get("session_id") or cur_sid
        st["step2"] = dict(secs=r["secs"], cost=u2["cost"], timed_out=r["timed_out"], rc=r["rc"])
        rd = dict(request_text="1) " + req1 + "\n2) (같은 대화에서 이어서) " + req2, step2_done=True)
    review_cost = 0.0
    rnd = 0
    accepted = False
    while True:
        snap = job / f"round{rnd}"
        if snap.exists(): shutil.rmtree(snap)
        snap.mkdir()
        f = find_deliverable(wd, kind)
        entry = dict(round=rnd, cum_secs=total_secs, cum_cost=total_cost, deliverable=None)
        if not f:
            entry["note"] = "산출물 없음"
            st["rounds"].append(entry)
            # reviewer cannot look; ask once to save properly then stop
            if rnd >= 3: break
            fixes = ["결과 파일이 지금 폴더에 보이지 않아요. 파일을 이 폴더에 저장해 주세요."]
            verdict = "고쳐요"
            j = dict(verdict=verdict, fixes=fixes)
        else:
            shutil.copy2(f, snap / f.name)
            entry["deliverable"] = f.name; entry["size"] = f.stat().st_size
            pngs, notes = render_output(f, kind, snap / "render")
            entry["render_notes"] = notes
            rnote = "(PPT는 이 PC에 LibreOffice가 없어 파일 안 도형으로 근사해서 그린 그림이라 글꼴·줄바꿈이 실제와 다를 수 있어.)" if kind == "pptx" else ("(한글 파일은 우리 미리보기로 근사한 그림이야.)" if kind == "hwpx" else "")
            j = review(job, rd, f, kind, pngs, rnote, None, f"r{rnd}")
            review_cost += j.get("_cost", 0)
            entry["review"] = j
            st["rounds"].append(entry)
        save()
        v = j.get("verdict", "")
        if "충분" in v:
            accepted = True; break
        if rnd >= 3: break
        fixes = (j.get("fixes") or [])[:3]
        if not fixes: break
        rnd += 1
        msg = "확인해 봤는데 아래 부분을 고쳐야 해요. 같은 파일을 고쳐서 이 폴더에 다시 저장해 줘. 알아서 끝까지 해 줘.\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(fixes))
        (job / f"_fixmsg{rnd}.txt").write_text(msg, encoding="utf-8")
        r = claude(msg, model, cfg, wd, resume=cur_sid)
        (job / f"_fix{rnd}_result.json").write_text(r["raw"], encoding="utf-8")
        u3 = usage_of(r["data"])
        total_secs += r["secs"]; total_cost += u3["cost"]; out_tok += u3["out_tok"]
        cur_sid = (r["data"] or {}).get("session_id") or cur_sid
        st["rounds"][-1]["fix_after"] = dict(secs=r["secs"], cost=u3["cost"], timed_out=r["timed_out"], rc=r["rc"])
    st.update(accepted=accepted, n_fix_rounds=rnd, time_to_acceptable=total_secs, gen_cost=total_cost, out_tok=out_tok, review_cost=review_cost, done=True)
    f = find_deliverable(wd, kind)
    st["final"] = str(f) if f else None
    if f:
        fin = job / "final"; fin.mkdir(exist_ok=True)
        shutil.copy2(f, fin / f.name)
    save()
    log("DONE", name, f"first={first_secs:.0f}s total={total_secs:.0f}s rounds={rnd} acc={accepted} cost={total_cost:.2f}+{review_cost:.2f}")
    return st


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1:])
    jobs = []
    for task in TASKS:
        for mkey in ("fable", "sonnet"):
            for cond in ("bare", "harness"):
                n = f"{task}-{mkey}-{cond}"
                if only and n not in only and task not in only: continue
                jobs.append((task, cond, mkey))
    log("JOBS", len(jobs))
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(run_job, *j) for j in jobs]
        for fu in futs:
            try: fu.result()
            except Exception as e:
                import traceback; log("JOB EXC", traceback.format_exc()[-800:])


if __name__ == "__main__":
    main()
