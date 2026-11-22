# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Printed handout for 「AI에게 무기를 주면」 (2026-11-23).

  py build_handout.py          -> handout.html, handout.pdf, handout-preview.png (+ handout.hwpx via docs.py, page 2 break patched)

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


EXAMPLES = [   # 예시일 뿐 · 일상 → 업무 → 수업 (deck-e 18장 · deck-v3 19장과 같은 순서)
    ("plane", "일상 · 가족 여행 일정표", "다음 달 가족 여행 2박 3일 일정표, 기획부터 같이 해 줘."),
    ("users", "일상 · 모임 안내문", "동호회 정기 모임 안내문, 기획부터 같이 해 줘."),
    ("mail", "업무 · 안내문·공문 (한글)", "체험학습 안내문을 한글 파일로, 기획부터 같이 해 줘."),
    ("calculator", "업무 · 엑셀 → 보고서", "이 엑셀을 한눈에 보는 보고서로. 이름은 빼고."),
    ("device-gamepad-2", "수업 · 게임", "중2 과학 「빛의 반사」 복습 퀴즈 게임, 기획부터 같이 해 줘."),
    ("stopwatch", "수업 · 수업 도구", "발표 순서 뽑기 + 3분 타이머. 교실 TV에서 크게 보이게."),
]

TIPS = [   # deck-v3 13장 끝 · 19장 미션 판 · 21장과 같은 이름 (deck-e는 네 단계: 8장 끝 · 18장 · 19장)
    ("주문서 쓰기", "누구에게 · 어디에 · 어떤 느낌 · 어떤 재료"),
    ("기획 같이 하기", "AI가 묻고 내가 고르기 · 「기획부터 같이 해 줘」"),
    ("만들고 한 번 고치기", "「여기만 고쳐 줘」 한 번 더"),
    ("확인하기", "사실·숫자 / 남의 개인정보(학생·학부모·교직원·가족 등) / 저작권"),
    ("공유하기", "폰으로 보내고 같이 쓰기"),
]

MAP = [("chef-hat", "AI", "요리사"), ("building-store", "AI를 만드는 회사", "식당"), ("tools-kitchen-2", "AI 앱", "그 식당의 주방"),
       ("book", "하네스", "레시피·밀키트·주방도구·시식·위생 규칙"), ("receipt", "내 부탁(프롬프트)", "주문서")]


def build_html() -> str:
    head = (f'<div class="meta">교사 연수 &nbsp;·&nbsp; 2026. 11. 23.(월) 14:00 &nbsp;·&nbsp; 60분 &nbsp;·&nbsp; AI교육코디네이터 박진영</div>')

    # ---------------------------------------------------------------- page 1: follow along
    harness = (f'<div class="harness"><div class="hx-text"><b>하네스</b> = AI 요리사에게 <b>도구</b>와 <b>레시피</b>를 주는 것</div>'
               f'<div class="hx-pic" aria-hidden="true">'
               f'<span class="chip">{ic("flame", 20)}도구</span><span class="op">+</span>'
               f'<span class="chip">{ic("book", 20)}레시피</span><span class="op">=</span>'
               f'<span class="chip strong">{ic("egg", 20)}김치볶음밥</span></div></div>')
    amap = '<div class="amap">' + "".join(f'<div class="am"><div class="am-r">{e(r)}</div><div class="am-a">{ic(n, 18)}<b>{e(v)}</b></div></div>' for n, r, v in MAP) + '</div>'
    steps = "".join([
        step(1, "우리가 쓸 식당", "모둠 노트북에 하네스를 <b>미리 채워 두었어요</b> &nbsp;<span class='real'>(식당 ① Claude 앱 / 식당 ② ChatGPT 앱)</span>"),
        step(2, "파일을 만드는 「주방」 열기", "앱을 열고 <b>Cowork</b> 탭 &nbsp;<span class='real'>(식당 ② 개인 계정은 Codex 앱)</span>"),
        step(3, "한 줄로 확인", "", '<div class="say">「교사 스튜디오 시작」 → 「무엇을 만들까요?」가 뜨면 성공</div>'),
        step(4, "모둠 미션: 오늘 진짜 필요한 것 하나", "일상이든 업무든 수업이든. 처음엔 내 일상 것부터 해 봐도 돼요",
             '<div class="prompt">① 주문서 쓰기 → ② 기획 같이 하기 → ③ 만들고 한 번 고치기 → ④ 확인하기 → ⑤ 공유하기</div>'),
    ])
    planb = (f'<div class="planb"><div class="pb-h">{ic("home", 22)} 집에서 설치하기</div>'
             f'<ol><li>Cowork 탭(또는 Codex 앱)에서 <b>{REPO}</b> + 「내가 준 링크에 하네스 세팅해 줘」</li>'
             f'<li>안 되면: <b>dist</b> 폴더에서 zip 받기 → 식당 ① <b>Customize → Skills</b>에 올리기</li>'
             f'<li>코드 실행 켜기: <b>Settings → Capabilities</b></li></ol></div>')
    p1 = (f'<section class="page">{head}<h1>AI에게 무기를 주면</h1><div class="sub">따라 하기 안내지 &nbsp;·&nbsp; 1쪽 따라 하기 / 2쪽 가져가기</div>'
          f'<div class="motto"><div class="m-l">오늘의 한 줄</div><div class="m-t">「바로 만들어」 말고, <b>「기획부터 같이 해 줘」</b></div></div>'
          f'{amap}<h2>오늘 실습 (보기 · 미션)</h2><div class="steps">{steps}</div>{planb}</section>')

    # ---------------------------------------------------------------- page 2: take home
    tips = "".join(f'<li><span class="tn">{i + 1}</span><b>{a}</b><span class="td">{b}</span></li>' for i, (a, b) in enumerate(TIPS))
    cards = "".join(f'<div class="card"><div class="c-h">{ic(n, 22)}<b>{e(t)}</b></div><div class="c-q">「{e(q)}」</div></div>'
                    for n, t, q in EXAMPLES)
    qr = deck_qr.svg(SITE)
    p2 = (f'<section class="page">{head}<h2 class="first">가져가실 다섯 단계</h2><ol class="tips">{tips}</ol>'
          f'<div class="nextstep"><b>다음 한 걸음</b> 오늘 저녁, 내 일상 하나부터 써 보기 → 2주 안에 업무나 수업에도 한 번 · 사이트에 한 줄 남기기</div><h2>이렇게 써 보세요 <small>(예시일 뿐)</small></h2><div class="cards">{cards}</div>'
          f'<div class="site"><div class="qr">{qr}</div><div class="site-t"><div class="st-big">연수 내용과 쓰는 법은<br>사이트에 있어요</div>'
          f'<div class="st-url">{e(SITE)}</div><div class="st-s">휴대폰 카메라로 QR을 비추면 열려요</div></div></div>'
          f'<footer><b>AI가 만들어도, 마지막 확인과 책임은 여러분께</b></footer></section>')

    css = f"""
@page{{size:A4;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:#fff;color:{INK}}}
body{{font-family:'Noto Sans KR','맑은 고딕','Malgun Gothic',sans-serif;font-size:13.5pt;line-height:1.45;word-break:keep-all;overflow-wrap:break-word;
-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:210mm;height:297mm;padding:13mm 15mm 11mm;overflow:hidden;page-break-after:always;break-after:page;position:relative;display:flex;flex-direction:column}}
.page:last-child{{page-break-after:auto;break-after:auto}}
.meta{{font-size:10.5pt;color:#333;border-bottom:1.2pt solid {INK};padding-bottom:2.5mm}}
h1{{font-size:30pt;font-weight:900;margin:4mm 0 0;letter-spacing:-.02em;line-height:1.15}}
.sub{{font-size:11pt;color:#444;margin-top:1mm}}
h2{{font-size:17pt;font-weight:900;margin:6mm 0 2.5mm;padding-left:3mm;border-left:2.2mm solid {INK};line-height:1.2}}
h2.first{{margin-top:5mm}}
.motto{{margin-top:5mm;border:2.4pt solid {INK};border-radius:3mm;padding:3.5mm 5mm;display:flex;gap:5mm;align-items:center}}
.m-l{{font-size:11pt;font-weight:800;background:{INK};color:#fff;border-radius:1.5mm;padding:1mm 2.5mm;white-space:nowrap}}
.m-t{{font-size:19pt;font-weight:500;letter-spacing:-.02em}}
.m-t b{{font-weight:900}}
.harness{{margin-top:4mm;display:flex;align-items:center;justify-content:space-between;gap:4mm;background:{SOFT};border:.8pt solid {LINE};border-radius:3mm;padding:3mm 4.5mm}}
.hx-text{{font-size:14pt}}
.hx-pic{{display:flex;align-items:center;gap:1.5mm;white-space:nowrap}}
.chip{{display:inline-flex;align-items:center;gap:1mm;font-size:11pt;font-weight:700;border:1pt solid {INK};border-radius:5mm;padding:.6mm 2.4mm;background:#fff}}
.chip.strong{{background:{INK};color:#fff}}
.op{{font-weight:900;font-size:13pt}}
.steps{{display:flex;flex-direction:column;gap:2.2mm}}
.amap{{display:grid;grid-template-columns:repeat(5,1fr);gap:1.6mm;margin-top:3mm}}
.am{{border:.8pt solid {LINE};border-radius:2mm;padding:1.6mm 2mm}}
.am-r{{font-size:9.5pt;color:#444}}
.am-a{{display:flex;align-items:center;gap:1mm;font-size:10pt;line-height:1.25}}
.am-a b{{font-weight:800}}
.nextstep{{margin-top:3mm;border:1.4pt solid {INK};border-radius:2mm;padding:2.2mm 3.5mm;font-size:11.5pt}}
.nextstep b{{margin-right:2mm}}
h2 small{{font-size:11pt;font-weight:600}}
.step{{display:flex;gap:3.5mm;align-items:flex-start;border:1pt solid {LINE};border-radius:3mm;padding:2mm 3.5mm}}
.num{{flex:0 0 10mm;height:10mm;border-radius:50%;background:{INK};color:#fff;font-size:21pt;font-weight:900;display:flex;align-items:center;justify-content:center;line-height:1}}
.sbody{{flex:1}}
.stitle{{font-size:14.5pt;font-weight:900;line-height:1.25}}
.sdetail{{font-size:11.5pt;margin-top:.8mm}}
.tag{{font-size:10.5pt;font-weight:700;border:1pt solid {INK};border-radius:1.2mm;padding:0 1.6mm;vertical-align:2px}}
.code{{display:inline-block;margin-top:1.5mm;font-size:16pt;font-weight:800;letter-spacing:.01em;border:1.6pt solid {INK};border-radius:1.8mm;padding:.8mm 3mm;background:{SOFT}}}
.say{{font-size:12.5pt;font-weight:700;margin-top:1.5mm}}
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
.site{{margin-top:auto;display:flex;align-items:center;gap:6mm;border:2.4pt solid {INK};border-radius:3mm;padding:3mm 5mm}}
.qr{{flex:0 0 36mm;width:36mm;height:36mm}}
.qr svg{{width:100%;height:100%;display:block}}
.st-big{{font-size:20pt;font-weight:900;line-height:1.3}}
.st-url{{font-size:13.5pt;font-weight:700;margin-top:2mm;word-break:break-all}}
.st-s{{font-size:11pt;color:#333;margin-top:1mm}}
footer{{margin-top:4mm;border-top:1.2pt solid {INK};padding-top:2.5mm;display:flex;justify-content:center;align-items:baseline;font-size:13pt}}
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
    print("hwpx page break:", patch_hwpx_page_break(HERE / "handout.hwpx", "가져가실 다섯 단계"))


if __name__ == "__main__":
    main()
