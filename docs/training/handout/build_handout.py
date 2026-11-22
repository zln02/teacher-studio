# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Printed handout for 「AI에게 무기를 주면」 (2026-11-23) · deck-e v5: one A4 page, how to open Claude Cowork / ChatGPT Codex.

  py build_handout.py          -> handout.html, handout.pdf, handout-preview.png (+ handout.hwpx via docs.py)

Uses the harness itself: house tokens (shared/design, use=print, large), shell icons (Tabler), qrcodegen QR via
teacher-slides/deck_qr.py, Noto Sans KR subset embedding, teacher-docs pdf_tools (A4 print + PNG) and docs.py (HWPX + gate).
One headless browser at a time (only html_to_pdf opens one).
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for p in ("shared/design", "shared/shell", "skills/teacher-docs/scripts", "skills/teacher-slides/scripts", "shared/tools"):
    sys.path.insert(0, str(ROOT / p))

import design  # noqa: E402
import shell  # noqa: E402
import deck_qr  # noqa: E402
import pdf_tools  # noqa: E402

SITE = "https://zln02.github.io/noan-ai/training/s2.html"
REPO = "github.com/zln02/teacher-studio"

T = design.generate(use="print", mood="단정", large=True)["colors"]
INK = T["text"]          # near-black: everything that must survive black-and-white printing
ACC = T["primary"]       # one accent; prints as mid-grey, never the only carrier of meaning
SOFT = T["bg2"]
LINE = T["cardBorder"]

e = html.escape


def ic(name: str, size: int = 22, color: str = "currentColor", stroke: float = 2.0) -> str:
    return shell.icon(name, size, color, stroke)


def step(n: int, title: str, detail: str, extra: str = "") -> str:
    return (f'<div class="step"><div class="num">{n}</div><div class="sbody"><div class="stitle">{title}</div>'
            f'<div class="sdetail">{detail}</div>{extra}</div></div>')


def shot_uri() -> str:
    import base64
    return "data:image/png;base64," + base64.b64encode((HERE / "work-screen.png").read_bytes()).decode()


def build_html() -> str:
    """deck-e v5: 한 쪽 · Claude Cowork / ChatGPT Codex 들어가는 법만 (교사 스튜디오 설치 안내는 뺐어요)."""
    head = (f'<div class="meta">교사 연수 &nbsp;·&nbsp; 2026. 11. 23.(월) 14:00 &nbsp;·&nbsp; 60분 &nbsp;·&nbsp; AI교육코디네이터 박진영</div>')
    steps = "".join([
        step(1, '앱 열기', "컴퓨터용 <b>ChatGPT 앱</b>"),
        step(2, '위쪽 「Chat | Work」에서 「Work」 누르기', "「ChatGPT로 Work 시작」 칸이 보이면 준비 끝 &nbsp;(아래 그림 ①)"),
        step(3, '한 줄로 부탁', "",
             '<div class="say">예) 「물품 구입 안내문 만들어 줘」</div>'
             f'<div class="att">+ 있으면 <b>「파일」</b>(아래 그림 ②)로 <b>우리 학교 양식</b>을 같이 붙여요 &nbsp;·&nbsp; 규칙 한 줄(예: 학생 이름은 넣지 않기)</div>'),
        step(4, '받아서 확인', "사실 · 숫자 / 남의 개인정보 / 저작권 &nbsp;·&nbsp; 고칠 곳은 <b>「여기 고쳐 줘」</b> 한 줄"),
    ])
    qr = deck_qr.svg(SITE)
    p1 = (f'<section class="page">{head}<h1>AI에게 무기를 주면</h1><div class="sub">ChatGPT 「Work」(작업 모드) 시작 안내지</div>'
          f'<div class="motto"><div class="m-l">오늘의 한 줄</div><div class="m-t">물어볼 땐 <b>채팅</b>, 맡길 땐 <b>작업 모드(Work)</b></div></div>'
          f'<h2>이렇게 시작해요</h2><div class="steps">{steps}</div><div class="shot"><img alt="ChatGPT 앱 Work 화면" src="{shot_uri()}"></div>'
          f'<div class="warn">⚠ <b>남의 개인정보는 넣지 않아요</b>&nbsp; (학생 · 학부모 · 교직원 · 가족 누구 것이든)</div>'
          f'<div class="fine">컴퓨터용 ChatGPT 앱의 Work는 모든 요금제에서 · 내 폴더 파일까지 읽어요 (공식 안내 기준 2026-11) &nbsp;·&nbsp; 메뉴 이름은 앱 · 요금제마다 달라요</div>'
          f'<div class="site"><div class="qr">{qr}</div><div class="site-t"><div class="st-big">오늘 연수 내용 ·<br>막혔을 때는 사이트에</div>'
          f'<div class="st-url">{e(SITE)}</div><div class="st-s">휴대폰 카메라로 QR을 비추면 열려요</div></div></div>'
          f'<footer><b>AI가 만들어도, 마지막 확인과 책임은 여러분께</b></footer></section>')
    p2 = ""

    css = f"""
@page{{size:A4;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:#fff;color:{INK}}}
body{{font-family:'Noto Sans KR','맑은 고딕','Malgun Gothic',sans-serif;font-size:13.5pt;line-height:1.45;word-break:keep-all;overflow-wrap:break-word;
-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:210mm;height:297mm;padding:13mm 15mm 11mm;overflow:hidden;page-break-after:always;break-after:page;position:relative;display:flex;flex-direction:column}}
.page:last-child{{page-break-after:auto;break-after:auto}}
.meta{{font-size:10.5pt;color:#333;border-bottom:1.2pt solid {INK};padding-bottom:2.5mm}}
h1{{font-size:26pt;font-weight:900;margin:3mm 0 0;letter-spacing:-.02em;line-height:1.15}}
.sub{{font-size:11pt;color:#444;margin-top:1mm}}
h2{{font-size:15pt;font-weight:900;margin:4mm 0 2mm;padding-left:3mm;border-left:2.2mm solid {INK};line-height:1.2}}
h2.first{{margin-top:5mm}}
.motto{{margin-top:3.5mm;border:2.4pt solid {INK};border-radius:3mm;padding:3.5mm 5mm;display:flex;gap:5mm;align-items:center}}
.m-l{{font-size:11pt;font-weight:800;background:{INK};color:#fff;border-radius:1.5mm;padding:1mm 2.5mm;white-space:nowrap}}
.m-t{{font-size:19pt;font-weight:500;letter-spacing:-.02em}}
.m-t b{{font-weight:900}}
.harness{{margin-top:4mm;display:flex;align-items:center;justify-content:space-between;gap:4mm;background:{SOFT};border:.8pt solid {LINE};border-radius:3mm;padding:3mm 4.5mm}}
.hx-text{{font-size:14pt}}
.hx-pic{{display:flex;align-items:center;gap:1.5mm;white-space:nowrap}}
.chip{{display:inline-flex;align-items:center;gap:1mm;font-size:11pt;font-weight:700;border:1pt solid {INK};border-radius:5mm;padding:.6mm 2.4mm;background:#fff}}
.chip.strong{{background:{INK};color:#fff}}
.op{{font-weight:900;font-size:13pt}}
.steps{{display:flex;flex-direction:column;gap:2mm}}
.amap{{display:grid;grid-template-columns:repeat(5,1fr);gap:1.6mm;margin-top:3mm}}
.am{{border:.8pt solid {LINE};border-radius:2mm;padding:1.6mm 2mm}}
.am-r{{font-size:9.5pt;color:#444}}
.am-a{{display:flex;align-items:center;gap:1mm;font-size:10pt;line-height:1.25}}
.am-a b{{font-weight:800}}
.nextstep{{margin-top:3mm;border:1.4pt solid {INK};border-radius:2mm;padding:2.2mm 3.5mm;font-size:11.5pt}}
.nextstep b{{margin-right:2mm}}
h2 small{{font-size:11pt;font-weight:600}}
.step{{display:flex;gap:4mm;align-items:flex-start;border:1.2pt solid {LINE};border-radius:3mm;padding:2mm 4.5mm}}
.num{{flex:0 0 12mm;height:12mm;border-radius:50%;background:{INK};color:#fff;font-size:21pt;font-weight:900;display:flex;align-items:center;justify-content:center;line-height:1}}
.sbody{{flex:1}}
.stitle{{font-size:17pt;font-weight:900;line-height:1.25;display:flex;align-items:center;gap:2mm}}
.sdetail{{font-size:13pt;margin-top:.6mm}}
.att{{font-size:13pt;margin-top:1.5mm}}
.shot{{margin-top:2mm;text-align:center}}
.shot img{{width:80mm;border-radius:2mm;border:1pt solid {LINE}}}
.warn{{margin-top:2.5mm;font-size:13.5pt;border:2pt solid {INK};border-radius:3mm;padding:2.5mm 4.5mm}}
.fine{{margin-top:1.5mm;font-size:11pt;color:#333}}
.tag{{font-size:10.5pt;font-weight:700;border:1pt solid {INK};border-radius:1.2mm;padding:0 1.6mm;vertical-align:2px}}
.code{{display:inline-block;margin-top:1.5mm;font-size:16pt;font-weight:800;letter-spacing:.01em;border:1.6pt solid {INK};border-radius:1.8mm;padding:.8mm 3mm;background:{SOFT}}}
.say{{font-size:14.5pt;font-weight:800;margin-top:1.5mm;border:1.4pt dashed {INK};border-radius:2mm;padding:1.5mm 3mm;display:inline-block}}
.prompt{{margin-top:1.5mm;font-size:11.5pt;font-weight:600;border:1.6pt dashed {INK};border-radius:2.5mm;padding:2.5mm 3.5mm;background:{SOFT};line-height:1.5}}
.planb{{margin-top:3mm;border:1.6pt dashed {INK};border-radius:3mm;padding:2.2mm 4mm}}
.pb-h{{font-size:15pt;font-weight:900;display:flex;align-items:center;gap:2mm}}
.planb ol{{margin:1mm 0 0;padding-left:6mm;font-size:11pt}}
.planb li{{margin:.6mm 0}}
.tips{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2.5mm}}
.tips li{{display:flex;align-items:center;gap:3mm;border:1pt solid {LINE};border-radius:3mm;padding:2mm 3.5mm;font-size:11.5pt}}
.tips b{{font-size:13.5pt;font-weight:900;white-space:nowrap}}
.tn{{flex:0 0 10mm;height:10mm;border-radius:50%;border:1.8pt solid {INK};font-weight:900;font-size:15pt;display:flex;align-items:center;justify-content:center}}
.td{{color:#222}}
.real{{font-size:.82em;color:#444}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:2.5mm;margin-bottom:3mm}}
.card{{border:1pt solid {LINE};border-radius:3mm;padding:2.2mm 3.5mm;break-inside:avoid}}
.c-h{{display:flex;align-items:center;gap:2mm;font-size:12.5pt}}
.c-h b{{font-weight:900}}
.c-q{{font-size:11.5pt;margin-top:1mm;line-height:1.45}}
.site{{margin-top:2.5mm;display:flex;align-items:center;gap:5mm;border:2.4pt solid {INK};border-radius:3mm;padding:2mm 5mm}}
.qr{{flex:0 0 30mm;width:30mm;height:30mm}}
.qr svg{{width:100%;height:100%;display:block}}
.st-big{{font-size:15pt;font-weight:900;line-height:1.3}}
.st-url{{font-size:13.5pt;font-weight:700;margin-top:2mm;word-break:break-all}}
.st-s{{font-size:11pt;color:#333;margin-top:1mm}}
footer{{margin-top:2.5mm;border-top:1.2pt solid {INK};padding-top:2.5mm;display:flex;justify-content:center;align-items:baseline;font-size:13pt}}
footer span{{font-size:11pt;color:#333}}
@media screen{{body{{background:#d9dde3}} .page{{background:#fff;margin:8mm auto;box-shadow:0 2px 10px rgba(0,0,0,.18)}}}}
"""
    page = (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>AI에게 무기를 주면 · 안내지</title><style>{css}</style></head><body>{p1}{p2}</body></html>")
    return shell.embed_fonts(page)


def patch_hwpx_page_break(path: Path, before_text: str) -> bool:
    """docs.py has no page break: set pageBreak="1" on the paragraph whose text contains before_text (mimetype kept first + stored)."""
    tmp = path.with_suffix(".tmp")
    done = False
    with zipfile.ZipFile(path) as zi, zipfile.ZipFile(tmp, "w") as zo:
        for info in zi.infolist():
            data = zi.read(info.filename)
            if info.filename.startswith("Contents/section") and info.filename.endswith(".xml"):
                s = data.decode("utf-8")
                i = s.find(before_text)
                if i > 0:
                    j = s.rfind("<hp:p ", 0, i)
                    s = s[:j] + s[j:].replace('pageBreak="0"', 'pageBreak="1"', 1)
                    data, done = s.encode("utf-8"), True
            zo.writestr(info, data, compress_type=zipfile.ZIP_STORED if info.filename == "mimetype" else zipfile.ZIP_DEFLATED)
    tmp.replace(path)
    return done


def main() -> None:
    env = dict(os.environ, PYTHONUTF8="1")
    out_html = HERE / "handout.html"
    out_html.write_text(build_html(), encoding="utf-8")
    r = pdf_tools.html_to_pdf(out_html, HERE / "handout.pdf")
    print("pdf:", r)
    pngs = pdf_tools.to_png(HERE / "handout.pdf", Path(tempfile.mkdtemp()), scale=1.5)
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in pngs]
    gap = 30
    w = sum(i.width for i in ims) + gap * (len(ims) + 1)
    h = max(i.height for i in ims) + gap * 2
    sheet = Image.new("RGB", (w, h), (200, 205, 212))
    x = gap
    for im in ims:
        sheet.paste(im, (x, gap))
        x += im.width + gap
    sheet.save(HERE / "handout-preview.png", optimize=True)
    print("preview pages:", len(ims))
    docs = ROOT / "skills/teacher-docs/scripts/docs.py"
    subprocess.run([sys.executable, str(docs), "make", "--spec", str(HERE / "handout.spec.json"), "--out", str(HERE / "handout.hwpx")],
                   check=True, env=env)


if __name__ == "__main__":
    main()
