import json, glob, os, re, shutil, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from post import S, JOBS, TASKS, CONDS, load, final_pngs, montage, font
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
for f in (r"C:\Windows\Fonts\malgun.ttf",):
    font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

DEST = Path(r"C:\Users\User\Downloads\teacher-studio\docs\research\ceiling-eval-2026-11")
DEST.mkdir(parents=True, exist_ok=True)
NAMES = {"class-ppt": "수업 PPT", "promo-ppt": "홍보 PPT", "public-ppt": "공공 보고 PPT", "hwpx-notice": "가정통신문(hwpx)",
         "pdf-guide": "PDF 안내문(+신청서)", "game": "복습 게임", "webapp": "수학 프로그램", "unseen": "역할 정하기 도구(처음 보는 요청)"}
NEUTRAL_EXCL = ("GAME_LOGIC", "NG.boot", "engine block", "mute button", "teacher menu", "GAME.items", "GAME data", "no reset button", "spec", "token", "bias", "house look")


def autosum(t, m, c):
    f = JOBS / f"{t}-{m}-{c}" / "autocheck.json"
    if not f.exists(): return dict(fails=None, lines=[])
    d = json.loads(f.read_text(encoding="utf-8"))
    fails = []; warns = []
    for k, v in d.items():
        if not isinstance(v, dict): continue
        for ln in v["out"].splitlines():
            if ln.startswith("FAIL") and not any(x in ln for x in NEUTRAL_EXCL):
                fails.append(ln[:110])
            if ln.startswith("WARN"): warns.append(ln[:110])
    return dict(fails=len(fails), warns=len(warns), lines=fails)


# judge
J = {}
for f in glob.glob(str(S / "post/judge/*-pass*.json")):
    d = json.load(open(f, encoding="utf-8"))
    t = d["task"]
    for lab, cond in d["mapping"].items():
        sc = d["judge"].get(lab, {})
        dims = [sc.get(k, 0) for k in ("design", "accuracy", "fit", "ready")]
        rank = d["judge"]["ranking"].index(lab) + 1 if lab in d["judge"].get("ranking", []) else None
        J.setdefault((t, cond), []).append(dict(dims=dims, rank=rank, note=sc.get("note", ""), pass_=d["pass_"]))

rows = []
for t in TASKS:
    for m, c in CONDS:
        st = load(t, m, c)
        js = J.get((t, f"{m}-{c}"), [])
        q = sum(sum(x["dims"]) / 4 for x in js) / max(1, len(js))
        rk = sum(x["rank"] for x in js if x["rank"]) / max(1, len(js))
        dimavg = [sum(x["dims"][i] for x in js) / max(1, len(js)) for i in range(4)]
        a = autosum(t, m, c)
        rows.append(dict(task=t, model=m, cond=c, first=st["first_secs"], tta=st["time_to_acceptable"], rounds=st["n_fix_rounds"],
                         accepted=st["accepted"], cost=st["gen_cost"], rcost=st["review_cost"], q=q, rank=rk, dims=dimavg,
                         fails=a["fails"], warns=a["warns"], faillines=a["lines"], notes=[x["note"] for x in js],
                         out_tok=st["out_tok"], size=st["rounds"][-1].get("size")))
json.dump(rows, open(DEST / "results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
R = {(r["task"], r["model"], r["cond"]): r for r in rows}

# criteria
crit = []
for t in TASKS:
    sh, fb, fh, sb = R[(t, "sonnet", "harness")], R[(t, "fable", "bare")], R[(t, "fable", "harness")], R[(t, "sonnet", "bare")]
    crit.append(dict(task=t, a=sh["q"] - fb["q"], b=fh["q"] - fb["q"], c=sh["q"] - sb["q"], d=fh["q"] - sb["q"]))
json.dump(crit, open(DEST / "criteria.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# chart
fig, ax = plt.subplots(figsize=(11, 7.2))
col = {("fable", "bare"): "#d94f3d", ("fable", "harness"): "#1f77b4", ("sonnet", "bare"): "#f0a030", ("sonnet", "harness"): "#2a9d6e"}
lab = {("fable", "bare"): "fable 일반 AI", ("fable", "harness"): "fable 교사 스튜디오", ("sonnet", "bare"): "sonnet 일반 AI", ("sonnet", "harness"): "sonnet 교사 스튜디오"}
mk = {"fable": "o", "sonnet": "s"}
seen = set()
rnd = random.Random(3)
for r in rows:
    k = (r["model"], r["cond"])
    ax.scatter(r["tta"] / 60, r["q"] + rnd.uniform(-0.03, 0.03), c=col[k], marker=mk[r["model"]], s=95, edgecolor="black", linewidth=0.6,
               label=lab[k] if k not in seen else None, alpha=0.9)
    seen.add(k)
ax.set_xscale("log")
ax.set_xticks([1, 2, 3, 5, 10, 20]); ax.set_xticklabels(["1", "2", "3", "5", "10", "20"])
ax.set_xlabel("쓸 만해질 때까지 걸린 시간 (분, 로그 눈금) — 왼쪽일수록 빠름")
ax.set_ylabel("익명 심사 점수 (1~5, 심사 2회 평균) — 위쪽일수록 좋음")
ax.set_title("8개 과제 x 4조건 = 32개 결과 (점 하나 = 실행 1회)")
ax.grid(alpha=0.3); ax.legend(loc="lower right")
fig.tight_layout(); fig.savefig(DEST / "chart.png", dpi=130)

# ab-pack
ab = DEST / "ab-pack"; ab.mkdir(exist_ok=True)
key = {}
for i, t in enumerate(TASKS, 1):
    rr = random.Random(f"ab-{t}")
    order = [("fable", "bare"), ("fable", "harness")]
    rr.shuffle(order)
    ims = []
    for L, (m, c) in zip("AB", order):
        pngs = final_pngs(t, m, c)
        tmp = S / "post" / f"ab_{t}_{L}.png"
        montage(pngs[:6], tmp, cols=3, w=520, label="「%s」" % L)
        ims.append(Image.open(tmp))
    h = max(im.height for im in ims)
    W = sum(im.width for im in ims) + 30
    sheet = Image.new("RGB", (W, h + 90), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), f"{i}. {NAMES[t]} — 요청: {TASKS[t]['p'][:60]}", fill=(0, 0, 0), font=font(34))
    x = 10
    for im in ims:
        sheet.paste(im, (x, 80)); x += im.width + 10
    fn = f"{i:02d}-{t}.png"
    sheet.save(ab / fn)
    key[fn] = {"A": "%s-%s" % order[0], "B": "%s-%s" % order[1]}
json.dump(dict(note="A/B가 어느 쪽인지 보려면 이 파일을 연다. bare=일반 AI, harness=교사 스튜디오. 둘 다 fable 모델.", key=key), open(ab / "key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# raw copy (no work dirs)
raw = DEST / "raw"
if raw.exists(): shutil.rmtree(raw)
for j in JOBS.iterdir():
    dst = raw / "jobs" / j.name
    shutil.copytree(j, dst, ignore=shutil.ignore_patterns("work", "review-*/*.png"))
    # keep review prompts/results but not duplicate pngs; keep round renders
shutil.copytree(S / "post/judge", raw / "judge", ignore=shutil.ignore_patterns("*.png"))
for f in ("orch.py", "post.py", "agg.py"):
    shutil.copy2(S / f, raw / f)
for f in ("orch.log", "orch.log.1", "orch.log.2"):
    if (S / f).exists(): shutil.copy2(S / f, raw / f)

# trim raw
jobsd = raw / "jobs"
for d in jobsd.glob("*/review-*"):
    for f in d.iterdir():
        if f.is_file() and not f.name.startswith("_prompt") and not f.name.startswith("_result"): f.unlink()
for j in jobsd.iterdir():
    rs = sorted(j.glob("round*"))
    for r in rs[:-1]:
        shutil.rmtree(r / "render", ignore_errors=True)
for p in list(jobsd.rglob("render/*.html")) + list(jobsd.rglob("*sheet.png")) + list(jobsd.rglob("full.png")): p.unlink()
for p in list(jobsd.rglob("*.png")):
    im = Image.open(p).convert("RGB")
    if im.width > 1100: im = im.resize((1100, int(im.height * 1100 / im.width)))
    im.save(p.with_suffix(".jpg"), quality=70); p.unlink()
big = []
for p in DEST.rglob("*"):
    if p.is_file() and p.stat().st_size > 5 * 1024 * 1024: big.append(str(p.relative_to(DEST)).replace("\\", "/"))
(DEST / ".gitignore").write_text("\n".join(big) + ("\n" if big else ""), encoding="utf-8")
print("big files:", big)
print("done")
