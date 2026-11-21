"""Contact sheet: 6 tasks x 4 conditions (first 4 screens of one run each, with both judges' mean).  py contact.py OUT.png [run]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.argv, argv = ["x"], sys.argv
import xv_eval as e  # noqa: E402

out = Path(argv[1])
run = int(argv[2]) if len(argv) > 2 else 1


def font(sz, bold=True):
    for n in (("malgunbd.ttf",) if bold else ()) + ("malgun.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(n, sz)
        except Exception:
            pass
    return ImageFont.load_default()


try:
    tb = json.loads((Path(__file__).parent / "table.json").read_text(encoding="utf-8"))
    sc = {(r["task"], r["maker"], r["cond"], r["run"]): r["scores"] for r in tb["runs"]}
except Exception:
    sc = {}
TW, TH, G = 236, 133, 4
cellw = 2 * TW + 3 * G
rowh = 2 * TH + 3 * G + 78
W = 4 * cellw + 5 * 10
names = {("claude", "bare"): "Claude Sonnet 일반", ("claude", "harness"): "Claude Sonnet + 스튜디오", ("codex", "bare"): "GPT(Codex) 일반", ("codex", "harness"): "GPT(Codex) + 스튜디오"}
sheet = Image.new("RGB", (W, 70 + rowh * len(e.TASKS)), (236, 236, 236))
d = ImageDraw.Draw(sheet)
d.text((14, 12), f"같은 요청 · 네 조건 (실행 {run})   점수 = 심사 평균 (Opus / GPT)", fill=(0, 0, 0), font=font(30))
for k, (t, info) in enumerate(e.TASKS.items()):
    y0 = 70 + k * rowh
    d.text((14, y0 + 4), f"{info['name']}: " + info["p"].split(" 만들어")[0][:70], fill=(20, 20, 20), font=font(21))
    for j, (v, c) in enumerate(e.CONDS):
        x0 = 10 + j * (cellw + 10)
        s = sc.get((t, v, c, run)) or {}
        f = lambda x: "-" if x is None else f"{x:.2f}"
        d.text((x0 + 2, y0 + 38), f"{names[(v, c)]}  {f(s.get('opus'))} / {f(s.get('gpt'))}", fill=(150, 40, 20) if c == "bare" else (20, 80, 150), font=font(18))
        ps = e.out_pngs(e.X / "runs" / f"{t}-{v}-{c}-{run}", info["kind"])[:4]
        if not ps:
            d.text((x0 + 20, y0 + 120), "결과 파일 없음", fill=(200, 0, 0), font=font(26))
        for i, p in enumerate(ps):
            im = Image.open(p).convert("RGB")
            if im.height > im.width:  # document page: keep the top part
                im = im.crop((0, 0, im.width, int(im.width * TH / TW)))
            sheet.paste(im.resize((TW, TH)), (x0 + G + (i % 2) * (TW + G), y0 + 66 + (i // 2) * (TH + G)))
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out)
print(out, sheet.size)
