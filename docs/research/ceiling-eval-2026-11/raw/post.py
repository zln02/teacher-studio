#!/usr/bin/env python3
"""post-processing: checks, judge, aggregate. py post.py checks|judge|agg"""
import json, os, sys, random, shutil, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path(__file__).parent))
import orch
from orch import S, JOBS, TASKS, claude, usage_of, extract_json, run_checks, log
from PIL import Image, ImageDraw, ImageFont

CONDS = [("fable", "bare"), ("fable", "harness"), ("sonnet", "bare"), ("sonnet", "harness")]
OUT = S / "post"
OUT.mkdir(exist_ok=True)


def load(task, m, c):
    f = JOBS / f"{task}-{m}-{c}" / "state.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def final_pngs(task, m, c):
    st = load(task, m, c)
    if not st or not st.get("rounds"): return []
    last = st["rounds"][-1]["round"]
    d = JOBS / f"{task}-{m}-{c}" / f"round{last}" / "render"
    ps = sorted(p for p in d.glob("*.png") if "sheet" not in p.name and p.name != "full.png")
    if TASKS[task]["kind"] == "hwpx":
        ps = sorted(d.glob("hwpx-*.png"))
    return ps


def font(sz):
    for f in (r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf"):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def montage(imgs, out, cols=3, w=640, maxn=12, label=None):
    imgs = [Image.open(p).convert("RGB") for p in imgs[:maxn]]
    if not imgs:
        im = Image.new("RGB", (w, 200), "white"); ImageDraw.Draw(im).text((10, 10), "NO OUTPUT", fill="red", font=font(30)); im.save(out); return out
    ts = []
    for im in imgs:
        h = int(im.height * w / im.width); h = min(h, int(w * 1.45))
        ts.append(im.resize((w, int(im.height * w / im.width))).crop((0, 0, w, h)))
    rows = [ts[i:i + cols] for i in range(0, len(ts), cols)]
    rh = [max(t.height for t in r) for r in rows]
    top = 70 if label else 0
    sheet = Image.new("RGB", (cols * (w + 8) + 8, sum(rh) + 8 * (len(rows) + 1) + top), (225, 225, 225))
    d = ImageDraw.Draw(sheet)
    if label: d.text((16, 6), label, fill=(0, 0, 0), font=font(54))
    y = top + 8
    for r, h in zip(rows, rh):
        for i, t in enumerate(r): sheet.paste(t, (8 + i * (w + 8), y))
        y += h + 8
    sheet.save(out)
    return out


def cmd_checks():
    jobs = [(t, m, c) for t in TASKS for m, c in CONDS]
    for t, m, c in jobs:
        st = load(t, m, c)
        if not st or not st.get("done"): continue
        fin = list((JOBS / f"{t}-{m}-{c}" / "final").glob("*"))
        outp = JOBS / f"{t}-{m}-{c}" / "autocheck.json"
        if not fin:
            outp.write_text(json.dumps(dict(error="no deliverable")), encoding="utf-8"); continue
        run_checks(fin[0], TASKS[t]["kind"], outp)
        log("checked", t, m, c)


JUDGE = """너는 공정한 심사위원이야. 선생님의 같은 요청에 대해 서로 다른 AI 4곳(A, B, C, D)이 만든 결과물이 있어. 어느 AI가 어느 조건인지는 모르고, 알려 하지도 마.

[선생님의 요청]
{req}

[보는 법] 현재 폴더에 A.png, B.png, C.png, D.png (필요하면 A2.png 처럼 뒤쪽 장도 있음)가 있어. Read 도구로 모두 직접 열어서 봐. 각 그림은 결과물 화면을 이어 붙인 것이고, 왼쪽 위에 글자(A~D)가 있어. 결과물 형식: {fmtnote}
{extra}

[채점] 각 결과물을 1~5점(정수)으로:
- design: 디자인(색, 구성, 정리된 느낌, 글자 크기, 겹침·잘림 없음)
- accuracy: 내용 정확성(사실, 정답, 수식, 날짜, 빈칸/OO/20XX 같은 채우지 않은 자리가 없는가)
- fit: 요청 부합(요청한 것을 빠짐없이, 요청한 형식·분량으로)
- ready: 교실 준비도(선생님이 고치지 않고 바로 수업/배포에 쓸 수 있나)
그리고 1위부터 4위까지 순위(동점 없이)를 매겨. 그림에 안 보이는 것은 추측하지 말고 보이는 대로만 평가해. 결과물이 없거나 깨졌으면 1점.

[출력] 마지막 답변은 JSON 하나만:
{{"A":{{"design":0,"accuracy":0,"fit":0,"ready":0,"note":"한 줄"}},"B":{{...}},"C":{{...}},"D":{{...}},"ranking":["1위 글자","2위","3위","4위"]}}
"""


def build_judge_inputs(task, perm, jd):
    if jd.exists(): shutil.rmtree(jd)
    jd.mkdir(parents=True)
    labels = "ABCD"
    mapping = {}
    for lab, (m, c) in zip(labels, perm):
        mapping[lab] = f"{m}-{c}"
        pngs = final_pngs(task, m, c)
        kind = TASKS[task]["kind"]
        # first sheet: up to 8 images, second sheet: rest up to 8
        montage(pngs[:6], jd / f"{lab}.png", cols=3 if kind in ("pptx", "html") else 3, w=640, label=lab)
        if len(pngs) > 6:
            montage(pngs[6:12], jd / f"{lab}2.png", cols=3, w=640, label=lab + " (2)")
    return mapping


def judge_one(task, pn):
    rnd = random.Random(f"{task}-judge")
    perm = CONDS[:]
    rnd.shuffle(perm)
    if pn == 2: perm = perm[::-1]
    if pn == 2: perm = perm[1:] + perm[:1]
    jd = OUT / "judge" / task / f"pass{pn}"
    mapping = build_judge_inputs(task, perm, jd)
    kind = TASKS[task]["kind"]
    fmt = {"pptx": ".pptx 슬라이드 (이 PC에 LibreOffice가 없어 파일 안 도형으로 근사해 그린 그림이라 글꼴·줄바꿈이 실제와 약간 다를 수 있음; 모든 결과물에 똑같이 적용)",
           "hwpx": "한글(.hwpx) 문서 (미리보기로 근사해 그림, 모든 결과물에 똑같이 적용)",
           "pdf": "PDF 문서 (실제 쪽 그림)", "html": "브라우저에서 여는 HTML 한 파일 (시작 화면과 몇 번 눌러 본 화면을 이어 붙인 그림; 움직임·소리는 안 보임)"}[kind]
    req = TASKS[task]["p"] + (" 그리고 같은 대화에서 이어서: " + TASKS[task]["step2"] if "step2" in TASKS[task] else "")
    extra = "한 결과물은 PDF 끝에 신청서 페이지가 붙어 있어야 한다는 두 번째 요청도 포함이야." if "step2" in TASKS[task] else ""
    prompt = JUDGE.format(req=req, fmtnote=fmt, extra=extra)
    (jd / "_prompt.txt").write_text(prompt, encoding="utf-8")
    r = claude(prompt, "opus", S / "cfg-reviewer", jd, cap=900)
    j = extract_json((r["data"] or {}).get("result", ""))
    res = dict(task=task, pass_=pn, mapping=mapping, judge=j, cost=usage_of(r["data"])["cost"], raw=(r["data"] or {}).get("result", "")[:1500])
    (OUT / "judge" / f"{task}-pass{pn}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log("judged", task, pn, bool(j))
    return res


def cmd_judge():
    (OUT / "judge").mkdir(exist_ok=True)
    items = [(t, p) for t in TASKS for p in (1, 2)]
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(lambda a: judge_one(*a), items))


if __name__ == "__main__":
    {"checks": cmd_checks, "judge": cmd_judge}[sys.argv[1]]()
