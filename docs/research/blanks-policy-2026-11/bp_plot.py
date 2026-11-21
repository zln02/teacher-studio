#!/usr/bin/env python3
"""Picture for blanks-policy-2026-11.md: per task, bare vs harness, for each maker (both judges' mean) + the policy counts.
   py bp_plot.py  ->  ../blanks-policy-2026-11.png   (reads table.json and policy.json here)"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

HERE = Path(__file__).resolve().parent
T = json.loads((HERE / "table.json").read_text(encoding="utf-8"))
POL = json.loads((HERE / "policy.json").read_text(encoding="utf-8"))["summary"]
NAMES = {"hwpx-notice": "가정통신문\n(hwpx)", "public-ppt": "공공 보고 PPT", "promo-ppt": "홍보 PPT", "pdf-guide": "안내문+신청서\n(PDF)"}
for f in ("C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
C_BARE, C_HAR = "#8a8983", "#2a78d6"  # same identity colours as the two cross-vendor pictures: bare = grey, harness now = blue


def panel(ax, maker, title):
    rows = {r["task"]: r["both"] for r in T["per_task"] if r["maker"] == maker}
    tasks = [t for t in NAMES if t in rows]
    w = 0.34
    for i, t in enumerate(tasks):
        for k, (v, c) in enumerate(((rows[t]["bare"], C_BARE), (rows[t]["harness"], C_HAR))):
            x = i + (k - 0.5) * (w + 0.03)
            ax.bar(x, v - 1, w, bottom=1, color=c, edgecolor=SURF, linewidth=1.5, zorder=3)
            ax.text(x, v + 0.04, f"{v:.2f}", ha="center", va="bottom", fontsize=9.5, color=INK, zorder=4)
    ax.set_xticks(range(len(tasks)))
    ax.set_xticklabels([NAMES[t] for t in tasks], fontsize=10, color=INK)
    ax.set_ylim(1, 5.3)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.tick_params(axis="y", labelsize=9, colors=MUTED, length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    s = T["summary"][f"{maker}/both"]
    w_, l_, t_ = s["h2h"]
    ax.set_title(f"{title}   평균: 일반 {s['bare']:.2f} · 스튜디오 {s['harness']:.2f} ({s['harness'] - s['bare']:+.2f}) · 맞대결 {w_}승 {l_}패 {t_}무",
                 loc="left", fontsize=11.5, color=INK, pad=10)
    ax.set_ylabel("두 심사 평균 (1~5점)", fontsize=9, color=MUTED)
    pb, ph_ = POL[f"{maker}-bare"], POL[f"{maker}-harness"]
    line = (f"「확인 필요」 같은 말: 일반 {pb['filler_total']}곳 · 스튜디오 {ph_['filler_total']}곳      "
            f"회신서·신청서: 일반 {pb['slip_present']}/{pb['slip_expected']} · 스튜디오 {ph_['slip_present']}/{ph_['slip_expected']}      "
            f"예시 안내 한 줄: 일반 {pb['note_present']}/{pb['files']} · 스튜디오 {ph_['note_present']}/{ph_['files']}")
    ax.text(0.0, -0.3, line, transform=ax.transAxes, fontsize=9.5, color=MUTED, ha="left", va="top")


fig, axes = plt.subplots(2, 1, figsize=(11, 9), facecolor=SURF)
for ax in axes:
    ax.set_facecolor(SURF)
panel(axes[0], "codex", "GPT(Codex)가 만든 것")
panel(axes[1], "claude", "Claude Sonnet이 만든 것")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (C_BARE, C_HAR)]
fig.legend(handles, ["일반 AI (스튜디오 없음)", "스튜디오 (빈칸 규칙 「섞기」 적용)"], loc="upper center", ncol=2, frameon=False, fontsize=10, bbox_to_anchor=(0.5, 0.955))
fig.suptitle("처음 쓰는 과제 4개: 빈칸 규칙을 하나로 정한 뒤 (실행 2회, Opus·GPT 두 심사 평균)", fontsize=13, color=INK, x=0.5, y=0.99)
fig.text(0.5, 0.012, "실행 2회·과제 4개라 과제 하나의 ±0.3은 흔들림 범위. 결과 파일이 없는 실행은 네 항목 모두 1점.", ha="center", fontsize=8.5, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 0.92), h_pad=4.2)
out = HERE.parent / "blanks-policy-2026-11.png"
fig.savefig(out, dpi=140, facecolor=SURF)
print("wrote", out)
