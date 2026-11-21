#!/usr/bin/env python3
"""Picture for cross-vendor-fix-2026-11.md: GPT (Codex) per task, bare vs harness before the fix vs harness after the fix.
   py xvfix_plot.py  ->  ../cross-vendor-fix-2026-11.png   (reads table.json here and ../cross-vendor-2026-11/table.json)"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

HERE = Path(__file__).resolve().parent
OLD = json.loads((HERE.parent / "cross-vendor-2026-11" / "table.json").read_text(encoding="utf-8"))
NEW = json.loads((HERE / "table.json").read_text(encoding="utf-8"))
NAMES = {"class-ppt": "수업 PPT", "public-ppt": "공공 보고 PPT", "hwpx-notice": "가정통신문\n(hwpx)", "game": "복습 게임", "webapp": "수업 도우미", "general": "동호회\n대진표·점수판"}
for f in ("C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
# identity colours (fixed order): bare = neutral grey, harness before = orange, harness after = blue
C_BARE, C_BEFORE, C_AFTER = "#8a8983", "#eb6834", "#2a78d6"


def per_task(tbl, maker):
    return {r["task"]: r["both"] for r in tbl["per_task"] if r["maker"] == maker}


def panel(ax, maker, title, summary_key):
    old, new = per_task(OLD, maker), per_task(NEW, maker)
    tasks = [t for t in NAMES if t in new]
    w = 0.26
    for i, t in enumerate(tasks):
        vals = [(new[t]["bare"], C_BARE), (old[t]["harness"], C_BEFORE), (new[t]["harness"], C_AFTER)]
        for k, (v, c) in enumerate(vals):
            x = i + (k - 1) * (w + 0.02)
            ax.bar(x, v - 1, w, bottom=1, color=c, edgecolor=SURF, linewidth=1.5, zorder=3)
            ax.text(x, v + 0.04, f"{v:.2f}", ha="center", va="bottom", fontsize=9, color=INK, zorder=4)
    ax.set_xticks(range(len(tasks)))
    ax.set_xticklabels([NAMES[t] for t in tasks], fontsize=10, color=INK)
    ax.set_ylim(1, 5.2)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.tick_params(axis="y", labelsize=9, colors=MUTED, length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    so, sn = OLD["summary"][summary_key], NEW["summary"][summary_key]
    ax.set_title(f"{title}   평균: 일반 {sn['bare']:.2f} · 스튜디오(고치기 전) {so['harness']:.2f} · 스튜디오(고친 뒤) {sn['harness']:.2f}",
                 loc="left", fontsize=11.5, color=INK, pad=10)
    ax.set_ylabel("두 심사 평균 (1~5점)", fontsize=9, color=MUTED)


fig, axes = plt.subplots(2, 1, figsize=(11, 8.4), facecolor=SURF)
for ax in axes:
    ax.set_facecolor(SURF)
panel(axes[0], "codex", "GPT(Codex)가 만든 것", "codex/both")
panel(axes[1], "claude", "Claude Sonnet이 만든 것 (수업 도우미·가정통신문만 다시 만듦)", "claude/both")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (C_BARE, C_BEFORE, C_AFTER)]
fig.legend(handles, ["일반 AI (스튜디오 없음, 1회차 결과물 그대로)", "스튜디오 · 고치기 전 (1회차)", "스튜디오 · 고친 뒤 (이번)"], loc="upper center", ncol=3, frameon=False, fontsize=10,
           bbox_to_anchor=(0.5, 0.955))
fig.suptitle("같은 요청 6개: 고치기 전과 뒤 (일반 AI 결과물은 다시 쓰고, 네 결과물을 함께 다시 심사)", fontsize=13, color=INK, x=0.5, y=0.99)
fig.text(0.5, 0.012, "일반 AI 점수는 이번 재심사 값. 실행 2회·과제 6개라 ±0.2는 흔들림 범위. Claude의 나머지 네 과제 「고친 뒤」 막대는 1회차 결과물을 다시 심사한 값.",
         ha="center", fontsize=8.5, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 0.92), h_pad=2.2)
out = HERE.parent / "cross-vendor-fix-2026-11.png"
fig.savefig(out, dpi=140, facecolor=SURF)
print("wrote", out)
