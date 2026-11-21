#!/usr/bin/env python3
"""Picture for leftovers-2026-11.md.
   py lo_plot.py  ->  ../leftovers-2026-11.png
   reads here: table.json (re-run cells), sameness-*.json (game variety), color-before.png / color-after.png (the same spec built before and after)"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

HERE = Path(__file__).resolve().parent
T = json.loads((HERE / "table.json").read_text(encoding="utf-8"))
for f in ("C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
C_BARE, C_HAR, C_OLD = "#8a8983", "#2a78d6", "#c9c8c2"  # bare = grey, studio = blue (as in the earlier pictures); before the fix = light grey


def clean(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="y", labelsize=9, colors=MUTED, length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.set_facecolor(SURF)


fig = plt.figure(figsize=(12, 10.2), facecolor=SURF)
gs = fig.add_gridspec(3, 2, height_ratios=[0.5, 1.0, 0.9], hspace=0.42, wspace=0.14, left=0.065, right=0.975, top=0.905, bottom=0.085)

# 1. colour with meaning: the same spec, before and after
for k, (name, title) in enumerate((("color-before.png", "고치기 전: 초록불이 주황, 빨간불이 보라 (색을 순서대로 돌려 씀)"), ("color-after.png", "고친 뒤: 낱말이 색 이름이면 그 색"))):
    ax = fig.add_subplot(gs[0, k])
    ax.imshow(mpimg.imread(str(HERE / name)))
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_title(title, loc="left", fontsize=10.5, color=INK, pad=8)

# 2. the re-run cells: bare vs studio (both judges' mean)
ax = fig.add_subplot(gs[1, :])
clean(ax)
CELLS = [("hwpx-notice|claude", "가정통신문\nClaude · 2회차"), ("public-ppt|codex", "공공 보고 PPT\nGPT · 2회"), ("color-ppt|claude", "저학년 수업 PPT\nClaude · 2회"), ("color-ppt|codex", "저학년 수업 PPT\nGPT · 2회"),
         ("game|claude", "복습 게임\nClaude · 2회"), ("game|codex", "복습 게임\nGPT · 2회")]
PREV = {"hwpx-notice|claude": 1.00, "public-ppt|codex": 3.81}  # the same cells in the blanks round (studio): the run with no file, and the two report decks
w = 0.26
xs, labels = [], []
for i, (key, lab) in enumerate(CELLS):
    s = T["summary"].get(key)
    if not s:
        continue
    bars = [(s["bare"], C_BARE)] + ([(PREV[key], C_OLD)] if key in PREV else []) + [(s["harness"], C_HAR)]
    for k, (v, c) in enumerate(bars):
        x = i + (k - (len(bars) - 1) / 2) * (w + 0.02)
        ax.bar(x, v - 1, w, bottom=1, color=c, edgecolor=SURF, linewidth=1.5, zorder=3)
        ax.text(x, v + 0.05, f"{v:.2f}", ha="center", va="bottom", fontsize=9.5, color=INK, zorder=4)
    xs.append(i)
    labels.append(lab)
ax.set_xticks(xs)
ax.set_xticklabels(labels, fontsize=9.5, color=INK)
ax.set_ylim(1, 5.4)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_ylabel("두 심사 평균 (1~5점)", fontsize=9, color=MUTED)
ax.set_title("다시 만든 칸만: 일반 AI와 스튜디오 (Opus·GPT 두 심사, 가리고 채점)", loc="left", fontsize=11.5, color=INK, pad=10)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (C_BARE, C_OLD, C_HAR)]
ax.legend(handles, ["일반 AI", "스튜디오 · 지난 측정(같은 칸)", "스튜디오 · 이번"], loc="upper right", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(1.0, 1.17))

# 3. game variety
ax = fig.add_subplot(gs[2, 0])
clean(ax)
S = {n: json.loads((HERE / n).read_text(encoding="utf-8")) for n in ("sameness-seeds-1-3.json", "sameness-seeds-4-6.json", "sameness-holdout-before.json", "sameness-holdout-after.json") if (HERE / n).exists()}
bars = [("지난 측정\n예시 6개", 0.502, C_OLD)]
for n, lab in (("sameness-seeds-1-3.json", "이번 1회\n시드 1·2·3"), ("sameness-seeds-4-6.json", "이번 2회\n시드 4·5·6")):
    if n in S:
        bars.append((lab, S[n]["different_requests"], C_HAR))
if "sameness-holdout-before.json" in S:
    bars.append(("새 요청 6개\n고치기 전", S["sameness-holdout-before.json"]["different_requests"], C_OLD))
if "sameness-holdout-after.json" in S:
    bars.append(("새 요청 6개\n고친 뒤", S["sameness-holdout-after.json"]["different_requests"], C_HAR))
for i, (lab, v, c) in enumerate(bars):
    ax.bar(i, v, 0.56, color=c, edgecolor=SURF, linewidth=1.5, zorder=3)
    ax.text(i, v + 0.008, f"{v:.3f}", ha="center", va="bottom", fontsize=9.5, color=INK, zorder=4)
ax.axhline(0.5, color=INK, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
ax.text(len(bars) - 0.55, 0.512, "목표 0.5 이하", ha="right", va="bottom", fontsize=9, color=MUTED)
ax.set_xticks(range(len(bars)))
ax.set_xticklabels([b[0] for b in bars], fontsize=9, color=INK)
ax.set_ylim(0.3, 0.58)
ax.set_title("게임: 서로 다른 요청의 화면이 겹치는 정도 (낮을수록 다름)", loc="left", fontsize=11, color=INK, pad=10)

# 4. the numbers the gates count
ax = fig.add_subplot(gs[2, 1])
ax.axis("off")
ck = json.loads((HERE / "checks.json").read_text(encoding="utf-8")) if (HERE / "checks.json").exists() else {}
lines = ck.get("short") or ck.get("lines") or []
ax.text(0.0, 1.0, "점검기가 센 것", fontsize=11, color=INK, va="top", ha="left", transform=ax.transAxes)
ax.text(0.0, 0.88, "\n".join(lines), fontsize=10, color=INK, va="top", ha="left", transform=ax.transAxes, linespacing=1.75)

fig.suptitle("남은 일 6가지를 고치고, 바뀐 칸만 다시 잰 결과 (2026-11-21)", fontsize=13.5, color=INK, x=0.5, y=0.975)
fig.text(0.5, 0.018, "칸마다 실행 1~2회라 ±0.3은 흔들림 범위. 다시 만들지 않은 결과물(같이 채점한 나머지 셋)은 지난 측정의 파일 그대로.", ha="center", fontsize=8.5, color=MUTED)
out = HERE.parent / "leftovers-2026-11.png"
fig.savefig(out, dpi=140, facecolor=SURF)
print("wrote", out)
