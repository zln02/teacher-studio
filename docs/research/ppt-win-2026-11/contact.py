"""Contact sheet: bare model vs harness, same topic side by side (first 6 slides of one run each).  py contact.py TAG OUT.png [run] [topics...]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.argv, argv = ["x"], sys.argv
import ppt_eval as e  # noqa: E402

tag, out = argv[1], Path(argv[2])
run = int(argv[3]) if len(argv) > 3 else 1
topics = argv[4:] or e.ROUND1


def font(sz, bold=True):
    for n in (("malgunbd.ttf",) if bold else ()) + ("malgun.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(n, sz)
        except Exception:
            pass
    return ImageFont.load_default()


TW, G = 300, 6
TH = int(TW * 9 / 16)
side = 3 * TW + 4 * G
rowh = 2 * TH + 3 * G + 64
W = 2 * side + 24
sheet = Image.new("RGB", (W, 90 + rowh * len(topics)), (236, 236, 236))
d = ImageDraw.Draw(sheet)
d.text((16, 14), "같은 요청, 같은 모델(Sonnet):  왼쪽 = 일반 AI    오른쪽 = 교사 스튜디오", fill=(0, 0, 0), font=font(34))
try:
    tb = json.loads((e.HERE / f"table-{tag}.json").read_text(encoding="utf-8"))
    rows = {r["topic"]: r for r in tb["rows"]}
except Exception:
    rows = {}
for k, t in enumerate(topics):
    y0 = 90 + k * rowh
    r = rows.get(t)
    sc = f"   심사 평균  일반 AI {r['bare_mean']:.2f}  /  스튜디오 {r['harness_mean']:.2f}" if r else ""
    d.text((16, y0 + 8), e.TOPICS[t]["p"].split(" 만들어")[0][:60] + sc, fill=(20, 20, 20), font=font(24))
    for j, cond in enumerate(("bare", "harness")):
        ps = e.slide_pngs(e.rdir(tag) / f"{t}-{cond}-{run}")[:6]
        x0 = j * (side + 24)
        for i, p in enumerate(ps):
            im = Image.open(p).convert("RGB").resize((TW, TH))
            sheet.paste(im, (x0 + G + (i % 3) * (TW + G), y0 + 52 + (i // 3) * (TH + G)))
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out)
print(out, sheet.size)
