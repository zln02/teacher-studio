#!/usr/bin/env python3
"""Build docs/training/deck-v2.html: one offline file (three.js r128 + anime.js + Lucide icons + Noto KR subset).

One-command rebuild (Windows):  set PYTHONUTF8=1 && py docs/training/deck-v2-src/build.py
  - re-embeds the 「같은 부탁, 다른 결과」 screenshots from docs/training/compare/<case>-bare.png / <case>-harness.png
    (cases: game, parents, data, law; .png/.jpg/.webp). Missing ones become a 「결과 화면 들어갈 자리」 frame.
  - three.js: taken from --three PATH (npm pack three@0.128.0 -> package/build/three.min.js, MIT) or, by default,
    re-used from the three.js block already inside deck-v2.html. Either way the sha256 must match r128.
Reads the repo's shared/ tools read-only (vendor files, qrcodegen, font embedder). Writes only docs/training/deck-v2.html.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE.parent / "deck-v2.html"
sys.path.insert(0, str(REPO / "shared" / "fonts"))
sys.path.insert(0, str(REPO / "skills" / "teacher-slides" / "scripts"))

THREE_SHA = "9274bbcec8d96168626c732b5d31c775aa8cfb7eaa0599bec0c175908a2c1ce2"
SITE = "https://github.com/zln02/teacher-studio"
THREE_HEAD = "<script>/* three.js r128 · MIT License · Copyright (c) 2010-2021 three.js authors */\n"
COMPARE_DIR = HERE.parent / "compare"
CASES = [
    ("game", "중2 과학 빛 복습 게임", "기획 3안을 먼저 보여 주고, 고른 안으로 만들고 스스로 점검해요",
     "「첫 번째 부탁이에요. 왼쪽은 바로 만들었고, 오른쪽은 기획 3안부터 보여 줬어요. 저는 하나 골랐을 뿐이에요.」"),
    ("parents", "학부모 총회 발표자료", "누가 보는지부터 묻고, 발표 흐름을 먼저 잡아요",
     "「학부모 총회 발표자료예요. 오른쪽은 누가 보시는지, 몇 분인지부터 물어보고 흐름을 먼저 잡았어요.」"),
    ("data", "우리 반 성적 엑셀 분석", "이름은 숨기고, 그래프와 쉬운 말로 보여 줘요",
     "「성적 엑셀이에요. 오른쪽은 학생 이름을 숨기고 그래프와 쉬운 말로 정리했어요. 학생 정보는 이렇게 지켜야 해요.」"),
    ("law", "가정통신문에 이 그림 써도 돼?", "최신 법을 직접 찾아보고, 근거와 함께 알려 줘요",
     "「이 그림 써도 되나요? 왼쪽은 그럴듯하게 대답했고, 오른쪽은 최신 법을 직접 찾아 근거를 붙였어요. 그래도 마지막 판단과 책임은 선생님께 있어요.」"),
]


def shot(case: str, side: str) -> str:
    """<img> as a data URI when docs/training/compare/<case>-<side>.* exists, else a placeholder frame."""
    import base64
    import io
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = COMPARE_DIR / f"{case}-{side}.{ext}"
        if p.exists():
            from PIL import Image
            im = Image.open(p).convert("RGB")
            im.thumbnail((1616, 910))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=84, optimize=True)
            print(f"  embedded {p.name} {im.size[0]}x{im.size[1]} {len(buf.getvalue()) // 1024} KB")
            return ('<div class="frame"><img alt="%s 결과 화면" src="data:image/jpeg;base64,%s"></div>'
                    % ("맨몸" if side == "bare" else "하네스", base64.b64encode(buf.getvalue()).decode()))
    print(f"  placeholder {case}-{side}")
    return '<div class="frame ph"><svg class="ic"><use href="#image"/></svg>결과 화면 들어갈 자리</div>'


def compare_slides() -> str:
    out = []
    for k, (case, ask, cap, note) in enumerate(CASES, 1):
        out.append(f"""<section class="slide" data-agenda="2">
  <div class="kicker">같은 부탁, 다른 결과</div><div class="cno">{k} / {len(CASES)}</div>
  <div class="ask"><svg class="ic"><use href="#message-square"/></svg>「{ask}」</div>
  <div class="pair">
    <div class="shot" data-b="1"><div class="hd">내비 없이<i>ChatGPT·Claude 그대로</i></div>{shot(case, "bare")}<p>바로 만들어요. 빈칸은 짐작으로 채워요</p></div>
    <div class="shot h" data-b="2"><div class="hd"><svg class="ic"><use href="#navigation"/></svg>내비 켜고<i>하네스</i></div>{shot(case, "harness")}<p>{cap}</p></div>
  </div>
  <aside class="note">[10~18분] {note} 화면은 시연 때 실제로 받은 결과예요. 재지 않은 시간·숫자는 말하지 않아요.</aside>
</section>""")
    return "\n".join(out)


def icons(html: str, js: str = "") -> str:
    sprite = (REPO / "shared/vendor/lucide/lucide-1.75.0-sprite.svg").read_text(encoding="utf-8")
    want = set(re.findall(r'href="#([a-z0-9-]+)"', html))
    for m in re.finditer(r"icons:([a-z0-9 -]+)", js):  # 3D 카드에 그리는 아이콘 (deck.js 주석 목록)
        want.update(m.group(1).split())
    want = sorted(want)
    out = []
    for name in want:
        m = re.search(r'<symbol id="%s".*?</symbol>' % re.escape(name), sprite, re.S)
        if not m:
            raise SystemExit(f"icon missing: {name}")
        out.append(re.sub(r"\s+", " ", m.group(0)))
    return '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><!-- Lucide icons 1.75.0 · ISC License · Copyright (c) 2026 Lucide Icons and Contributors --><defs>' + "".join(out) + "</defs></svg>"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--three", default=str(HERE / "vendor" / "three-0.128.0.min.js"))
    ap.add_argument("--no-fonts", action="store_true")
    a = ap.parse_args()
    three_p = Path(a.three)
    if three_p.exists():
        three = three_p.read_bytes()
    else:
        old = OUT.read_text(encoding="utf-8")
        i = old.index(THREE_HEAD) + len(THREE_HEAD)
        three = old[i:old.index("\n</script>", i)].encode("utf-8")
    if hashlib.sha256(three).hexdigest() != THREE_SHA:
        raise SystemExit("three.min.js hash mismatch (expected npm three@0.128.0 build/three.min.js)")
    three = three.decode("utf-8")
    anime = (REPO / "shared/vendor/animejs/anime-4.5.0.umd.min.js").read_text(encoding="utf-8")
    css = (HERE / "deck.css").read_text(encoding="utf-8")
    slides = (HERE / "slides.html").read_text(encoding="utf-8")
    js = (HERE / "deck.js").read_text(encoding="utf-8")
    import deck_qr  # read-only use of the slides skill's QR helper (qrcodegen, MIT)
    slides = slides.replace("__QR__", deck_qr.svg(SITE)).replace("__COMPARE__", compare_slides()).replace("__ONCE__", shot("game", "harness"))
    for bad in ("?.", "??"):
        for m in re.finditer(re.escape(bad), js):
            nxt = js[m.end():m.end() + 1]
            if bad == "??" or re.match(r"[A-Za-z_$\[(]", nxt):
                raise SystemExit(f"ES2017 rule: {bad} in deck.js at {m.start()}")
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI에게 무기를 주면 · 교사 연수</title>
<meta name="generator" content="교사 스튜디오 · 박진영 (hand-built deck-v2)">
<!--
  Third-party code inlined below (see docs/training/deck-v2-NOTICE.md):
  - three.js r128 (npm three@0.128.0, build/three.min.js) · MIT License · Copyright (c) 2010-2021 three.js authors
  - anime.js 4.5.0 · MIT License · Copyright (c) 2025 Julian Garnier
  - Lucide icons 1.75.0 · ISC License · Copyright (c) 2026 Lucide Icons and Contributors
  - Noto Sans KR / Noto Serif KR subsets · SIL Open Font License 1.1
  - QR Code generator (Project Nayuki) · MIT License (drawn at build time)
-->
<style>
{css}
</style>
</head>
<body>
{icons(slides, js)}
<div id="stage">
{slides}
</div>
<div id="notes"></div>
<div id="black"></div>
<div id="bar"><button id="bprev" aria-label="이전">◀</button><button id="bnext" aria-label="다음">▶</button><button id="bnotes">노트 N</button><button id="bfs">전체 화면 F</button></div>
{THREE_HEAD}{three}
</script>
<script>/* anime.js 4.5.0 · MIT License · Copyright (c) 2025 Julian Garnier */
{anime}
</script>
<script>
{js}
</script>
</body>
</html>
"""
    if not a.no_fonts:
        from embed import embed
        html, rep = embed(html)
        print("fonts:", {k: v for k, v in rep.items() if k != "prompt"})
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html.encode('utf-8')) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
