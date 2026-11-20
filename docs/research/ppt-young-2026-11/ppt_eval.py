#!/usr/bin/env python3
"""New-topic PPT eval: bare model vs Teacher Studio harness (same prompt, Sonnet maker, Opus blind A/B judge).

  py ppt_eval.py sync                       copy the INSTALLED skills (~/.claude/skills/teacher-*, from scripts/setup.py) into the harness config
  py ppt_eval.py run COND [TAG] [topic...]  COND = bare | harness; 2 runs per topic, 2 claude -p at a time; results in runs-<TAG>/
  py ppt_eval.py render [TAG]               draw every deck with the repo's pptx preview (same renderer for both conditions)
  py ppt_eval.py judge [TAG] [topic...]     blind A/B (random labels), 2 passes per pair (labels swapped), Opus
  py ppt_eval.py table [TAG]                mean and worst per topic and condition
"""
import json, os, random, shutil, subprocess, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(r"C:\Users\User\Downloads\teacher-studio")
RAW = REPO / "docs/research/ceiling-eval-2026-11/raw"
sys.path.insert(0, str(RAW))
import orch  # noqa: E402  (claude() wrapper, credential sync, the same config folders as the ceiling eval)
from orch import S, claude, usage_of, extract_json  # noqa: E402

HERE = S / "pptwin"
orch.LOG = HERE / "eval.log"
SUFFIX = " 알아서 끝까지 만들어 줘. 결과 파일은 지금 폴더에 저장해 줘."
RUNS = 2
TOPICS = {
    # round 1: six topics never used in this repo's evals, fixtures or docs
    "class-volcano": dict(g="class", p="초등학교 4학년 과학 '화산과 지진' 수업용 PPT 만들어 줘 (10장 정도, 파워포인트 파일로)"),
    "class-market": dict(g="class", p="고1 통합사회 '시장 경제와 합리적 선택' 수업용 PPT 만들어 줘 (12장 정도, 파워포인트 파일로)"),
    "public-violence": dict(g="public", p="교육청 제출용 '2026학년도 학교폭력 예방 교육 운영 결과 보고' 발표자료 만들어 줘 (파워포인트 파일로)"),
    "public-resident": dict(g="public", p="구청 보고용 '2026년 주민 자치 프로그램 운영 성과와 내년 계획' 발표자료 만들어 줘 (파워포인트 파일로)"),
    "promo-phone": dict(g="promo", p="주민센터 '어르신 스마트폰 교실' 수강생 모집 홍보용 PPT 만들어 줘 (6장, 파워포인트 파일로)"),
    "company-bakery": dict(g="company", p="동네 빵집 창업 1년을 돌아보는 직원 회의 발표용 PPT 만들어 줘 (8장 정도, 파워포인트 파일로)"),
    # fresh topics kept back for the re-test after a change
    "class-ads": dict(g="class", p="중3 국어 '광고 속 설득 전략 읽기' 수업용 PPT 만들어 줘 (10장 정도, 파워포인트 파일로)"),
    "public-career": dict(g="public", p="시청 보고용 '2026년 청소년 진로 체험 프로그램 운영 결과' 발표자료 만들어 줘 (파워포인트 파일로)"),
    "promo-choir": dict(g="promo", p="직장인 합창단 신입 단원 모집 홍보용 PPT 만들어 줘 (6장, 파워포인트 파일로)"),
    "personal-hike": dict(g="personal", p="등산 동호회 송년 모임에서 틀 '올해 산행 돌아보기' PPT 만들어 줘 (8장 정도, 파워포인트 파일로)"),
    # design round (ppt-design-2026-11): four topics never used before, written down before any of them was run
    "class-mimic": dict(g="class", p="초등학교 2학년 국어 '흉내 내는 말' 수업용 PPT 만들어 줘 (8장 정도, 파워포인트 파일로)"),
    "class-goryeo": dict(g="class", p="중학교 1학년 역사 '고려의 건국과 후삼국 통일' 수업용 PPT 만들어 줘 (10장 정도, 파워포인트 파일로)"),
    "promo-bookcamp": dict(g="promo", p="구립 도서관 '주말 가족 독서 캠프' 참가 가족 모집 홍보용 PPT 만들어 줘 (6장, 파워포인트 파일로)"),
    "public-afterschool": dict(g="public", p="교육지원청 보고용 '2026학년도 방과후학교 운영 결과' 발표자료 만들어 줘 (파워포인트 파일로)"),
    # young-room round (ppt-young-2026-11): three lower-elementary lessons in different subjects + one report, never used before, fixed before any run
    "class-shapes": dict(g="class", p="초등학교 1학년 수학 '여러 가지 모양' 수업용 PPT 만들어 줘 (8장 정도, 파워포인트 파일로)"),
    "class-lifecycle": dict(g="class", p="초등학교 3학년 과학 '동물의 한살이' 수업용 PPT 만들어 줘 (10장 정도, 파워포인트 파일로)"),
    "class-crossing": dict(g="class", p="초등학교 2학년 안전한 생활 '안전하게 길 건너기' 수업용 PPT 만들어 줘 (8장 정도, 파워포인트 파일로)"),
    "public-library": dict(g="public", p="교육지원청 보고용 '2026학년도 학교 도서관 운영 결과' 발표자료 만들어 줘 (파워포인트 파일로)"),
}
ROUND1 = list(TOPICS)[:6]
FRESH_Y = ["class-shapes", "class-lifecycle", "class-crossing", "public-library"]
RERUN_Y = ["class-goryeo"]  # the clearest win of the design round: its bare decks are reused, the harness is rebuilt
FRESH_D = ["class-mimic", "class-goryeo", "promo-bookcamp", "public-afterschool"]
RERUN_D = ["promo-phone", "class-volcano", "class-market"]  # the three biggest losses of the last round


def rdir(tag):
    d = HERE / f"runs-{tag}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_sync():
    src = Path.home() / ".claude" / "skills"
    dst = S / "cfg-harness" / "skills"
    n = 0
    for sk in sorted(src.glob("teacher-*")):
        t = dst / sk.name
        if t.exists():
            shutil.rmtree(t)
        shutil.copytree(sk, t, ignore=shutil.ignore_patterns("__pycache__"))
        n += 1
    bare = [p.name for p in (S / "cfg-bare" / "skills").glob("teacher-*")]
    print("synced", n, "installed skills into cfg-harness; teacher skills in cfg-bare:", bare)


def find_pptx(wd):
    c = [f for f in Path(wd).rglob("*.pptx") if not f.name.startswith(("~$", "_")) and not any(x in str(f).replace("\\", "/") for x in ("/node_modules/", "/shared/", "/.claude/", "/assets/"))]
    c.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return c[0] if c else None


def run_one(tag, topic, cond, n):
    name = f"{topic}-{cond}-{n}"
    jd = rdir(tag) / name
    if (jd / "state.json").exists():
        return json.loads((jd / "state.json").read_text(encoding="utf-8"))
    wd = jd / "work"
    if wd.exists():
        shutil.rmtree(wd, ignore_errors=True)
    wd.mkdir(parents=True)
    r = claude(TOPICS[topic]["p"] + SUFFIX, "sonnet", S / ("cfg-harness" if cond == "harness" else "cfg-bare"), wd, session_id=str(uuid.uuid4()))
    d = r["data"] or {}
    res = str(d.get("result", ""))
    low = res.lower()
    if d.get("is_error") and any(w in low for w in ("limit", "login", "authenticate", "credit", "quota")):
        (jd / "_error.json").write_text(json.dumps(dict(result=res[:600], err=r["err"]), ensure_ascii=False), encoding="utf-8")
        raise RuntimeError(f"LOGIN/LIMIT: {res[:200]}")
    f = find_pptx(wd)
    st = dict(name=name, topic=topic, cond=cond, run=n, secs=round(r["secs"]), timed_out=r["timed_out"], cost=usage_of(d)["cost"], turns=d.get("num_turns"),
              file=f.name if f else None, last=res[-1500:], is_error=bool(d.get("is_error")))
    if f:
        shutil.copy2(f, jd / "deck.pptx")
        specs = [p for p in wd.rglob("*.json") if "slides" in p.read_text(encoding="utf-8", errors="ignore")[:20000] and "node_modules" not in str(p)]
        if specs:
            shutil.copy2(sorted(specs, key=lambda p: p.stat().st_mtime)[-1], jd / "spec.json")
    (jd / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    orch.log("ran", name, st["secs"], st["cost"], st["file"])
    print("ran", name, st["secs"], "s", f"${st['cost']:.2f}", st["file"], flush=True)
    return st


def cmd_run(cond, tag, topics):
    jobs = [(tag, t, cond, n) for t in topics for n in range(1, RUNS + 1)]
    stop = []

    def go(j):
        if stop:
            return None
        try:
            return run_one(*j)
        except RuntimeError as e:
            stop.append(str(e))
            print("STOP", e, flush=True)
    with ThreadPoolExecutor(int(os.environ.get("EVAL_WORKERS", "2"))) as ex:
        list(ex.map(go, jobs))
    if stop:
        print("STOPPED on login/limit error:", stop[0])
        return 2
    return 0


def cmd_render(tag):
    for jd in sorted(rdir(tag).iterdir()):
        f = jd / "deck.pptx"
        out = jd / "render"
        if not f.exists() or (out.exists() and any(out.glob("*.png"))):
            continue
        subprocess.run(["py", str(REPO / "skills/teacher-slides/scripts/pptx_render.py"), str(f), "--out", str(out)], capture_output=True, timeout=900)
        ck = subprocess.run(["py", str(REPO / "skills/teacher-slides/scripts/pptx_check.py"), str(f)], capture_output=True, timeout=300)
        (jd / "check.txt").write_bytes(ck.stdout)
        print("rendered", jd.name, len(list(out.glob("*.png"))) if out.exists() else 0, flush=True)


def slide_pngs(jd):
    d = jd / "render"
    ps = sorted(p for p in d.glob("*.png") if "sheet" not in p.name) if d.exists() else []
    return ps or sorted(d.glob("*.jpg")) if d.exists() else []


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
    if not ims:
        im = Image.new("RGB", (w, 200), "white")
        ImageDraw.Draw(im).text((10, 10), "NO OUTPUT", fill="red", font=font(30))
        im.save(out)
        return out
    ts = [im.resize((w, int(im.height * w / im.width))) for im in ims]
    rows = [ts[i:i + cols] for i in range(0, len(ts), cols)]
    rh = [max(t.height for t in r) for r in rows]
    top = 70 if label else 0
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


JUDGE = """너는 공정한 심사위원이야. 같은 요청에 대해 서로 다른 두 곳(A, B)이 만든 파워포인트가 있어. 어느 쪽이 어떤 방식으로 만들었는지는 모르고, 알려 하지도 마.

[요청]
{req}

[보는 법] 현재 폴더에 {files} 가 있어. Read 도구로 모두 직접 열어서 봐. 각 그림은 슬라이드를 순서대로 이어 붙인 것이고(한 그림에 6장), 왼쪽 위에 글자(A 또는 B)가 있어. 이 PC에는 PowerPoint가 없어서 pptx 파일 안의 도형·글·표·차트를 그대로 읽어 그린 근사 그림이야(글꼴·줄바꿈이 실제와 조금 다를 수 있고, 두 결과물에 똑같이 적용됨).

[채점] 각 결과물을 항목마다 1~5점(정수)으로:
- content: 내용의 질 (사실이 맞는가, 구체적인가, 실제 자료·예시·수치가 있는가, 깊이와 완결성, 채우지 않은 빈칸이 없는가)
- design: 디자인 (색·구성·시각적 위계·정돈된 느낌, 장마다 알맞은 표현 방식, 단조롭지 않음)
- readability: 가독성 (발표 화면에서 글자가 읽히는 크기인가, 대비, 겹침·잘림·빈 장 없음, 한 장의 정보량이 알맞은가)
- fit: 목적 적합성 (요청한 청중·용도·분량·형식에 맞고, 고치지 않고 바로 쓸 수 있는가)
그림에 안 보이는 것은 추측하지 말고 보이는 대로만 평가해. 결과물이 없거나 깨졌으면 1점. 마지막에 전체적으로 더 나은 쪽(winner: "A" 또는 "B", 정말 같으면 "tie")을 정해.

[출력] 마지막 답변은 JSON 하나만:
{{"A":{{"content":0,"design":0,"readability":0,"fit":0,"note":"한두 문장: 강점과 약점"}},"B":{{"content":0,"design":0,"readability":0,"fit":0,"note":"..."}},"winner":"A"}}
"""


def judge_pair(tag, topic, n, pn):
    out = HERE / f"judge-{tag}" / f"{topic}-{n}-pass{pn}"
    resf = HERE / f"judge-{tag}" / f"{topic}-{n}-pass{pn}.json"
    if resf.exists():
        return json.loads(resf.read_text(encoding="utf-8"))
    rnd = random.Random(f"{tag}-{topic}-{n}")
    order = ["bare", "harness"]
    rnd.shuffle(order)
    if pn == 2:
        order = order[::-1]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    files = []
    for lab, cond in zip("AB", order):
        ps = slide_pngs(rdir(tag) / f"{topic}-{cond}-{n}")[:18]
        for k in range(0, max(len(ps), 1), 6):
            fn = f"{lab}{'' if k == 0 else k // 6 + 1}.png"
            montage(ps[k:k + 6], out / fn, label=lab + ("" if k == 0 else f" ({k // 6 + 1})"))
            files.append(fn)
    prompt = JUDGE.format(req=TOPICS[topic]["p"], files=", ".join(files))
    (out / "_prompt.txt").write_text(prompt, encoding="utf-8")
    r = claude(prompt, "opus", S / "cfg-reviewer", out, cap=900)
    d = r["data"] or {}
    res = str(d.get("result", ""))
    if d.get("is_error") and any(w in res.lower() for w in ("limit", "login", "authenticate", "credit", "quota")):
        raise RuntimeError(f"LOGIN/LIMIT: {res[:200]}")
    j = extract_json(res)
    rec = dict(topic=topic, run=n, pass_=pn, mapping=dict(zip("AB", order)), judge=j, cost=usage_of(d)["cost"], raw=res[:2000])
    if j:
        resf.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print("judged", topic, n, pn, bool(j), flush=True)
    return rec


def cmd_judge(tag, topics):
    jobs = [(tag, t, n, pn) for t in topics for n in range(1, RUNS + 1) for pn in (1, 2)]
    stop = []

    def go(j):
        if stop:
            return
        try:
            judge_pair(*j)
        except RuntimeError as e:
            stop.append(str(e))
            print("STOP", e, flush=True)
    with ThreadPoolExecutor(int(os.environ.get("EVAL_WORKERS", "2"))) as ex:
        list(ex.map(go, jobs))
    return 2 if stop else 0


KEYS = ("content", "design", "readability", "fit")


def collect(tag):
    """{topic: {cond: {run: mean score over keys and passes}}} + notes + wins."""
    sc, notes, wins = {}, [], {}
    for f in sorted((HERE / f"judge-{tag}").glob("*-pass*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        j = r["judge"]
        for lab, cond in r["mapping"].items():
            v = j[lab]
            sc.setdefault(r["topic"], {}).setdefault(cond, {}).setdefault(r["run"], []).append({k: v[k] for k in KEYS})
            notes.append((r["topic"], r["run"], r["pass_"], cond, sum(v[k] for k in KEYS) / 4, v.get("note", "")))
        w = j.get("winner")
        wins.setdefault(r["topic"], []).append(r["mapping"].get(w, "tie"))
    return sc, notes, wins


def cmd_table(tag):
    sc, notes, wins = collect(tag)
    rows = []
    allv = {"bare": [], "harness": []}
    print("topic | bare mean / worst run | harness mean / worst run | diff | wins (harness-bare-tie)")
    for t, d in sc.items():
        cell = {}
        for cond in ("bare", "harness"):
            per_run = [sum(sum(p[k] for k in KEYS) / 4 for p in ps) / len(ps) for _, ps in sorted(d.get(cond, {}).items())]
            cell[cond] = (sum(per_run) / len(per_run), min(per_run)) if per_run else (0, 0)
            allv[cond] += per_run
        w = wins.get(t, [])
        rows.append(dict(topic=t, bare_mean=cell["bare"][0], bare_worst=cell["bare"][1], harness_mean=cell["harness"][0], harness_worst=cell["harness"][1],
                         wins=dict(harness=w.count("harness"), bare=w.count("bare"), tie=w.count("tie"))))
        print(f"{t} | {cell['bare'][0]:.2f} / {cell['bare'][1]:.2f} | {cell['harness'][0]:.2f} / {cell['harness'][1]:.2f} | {cell['harness'][0] - cell['bare'][0]:+.2f} | {w.count('harness')}-{w.count('bare')}-{w.count('tie')}")
    for cond in ("bare", "harness"):
        v = allv[cond]
        if v:
            print(f"ALL {cond}: mean {sum(v) / len(v):.2f} worst {min(v):.2f} (n={len(v)} runs)")
    crit = {c: {k: [] for k in KEYS} for c in ("bare", "harness")}
    for t, d in sc.items():
        for c, runs in d.items():
            for ps in runs.values():
                for p in ps:
                    for k in KEYS:
                        crit[c][k].append(p[k])
    for c in crit:
        print(c, {k: round(sum(v) / len(v), 2) for k, v in crit[c].items() if v})
    (HERE / f"table-{tag}.json").write_text(json.dumps(dict(rows=rows, criteria={c: {k: (sum(v) / len(v) if v else 0) for k, v in crit[c].items()} for c in crit},
                                                         notes=notes), ensure_ascii=False, indent=1), encoding="utf-8")
    for n in notes:
        print(f"  {n[0]} run{n[1]} pass{n[2]} {n[3]} {n[4]:.2f}: {n[5]}")


if __name__ == "__main__":
    a = sys.argv[1:]
    c = a[0] if a else ""
    if c == "sync":
        cmd_sync()
    elif c == "run":
        sys.exit(cmd_run(a[1], a[2] if len(a) > 2 else "r1", a[3:] or ROUND1))
    elif c == "render":
        cmd_render(a[1] if len(a) > 1 else "r1")
    elif c == "judge":
        sys.exit(cmd_judge(a[1] if len(a) > 1 else "r1", a[2:] or ROUND1))
    elif c == "table":
        cmd_table(a[1] if len(a) > 1 else "r1")
    else:
        print(__doc__)
