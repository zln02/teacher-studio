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
BARE_DIR = HERE / "compare-bare"
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
        p = BARE_DIR / f"{case}-{side}.{ext}"      # 「그냥 AI」 쪽: 화면 가득 다시 찍은 사진이 있으면 그것부터 (recapture_bare.py)
        if side != "bare" or not p.exists():
            p = COMPARE_DIR / f"{case}-{side}.{ext}"
        if p.exists():
            from PIL import Image
            im = Image.open(p).convert("RGB")
            if im.height * 16 > im.width * 9:      # 틀(16:9)을 가득 채우게: 긴 그림은 윗부분만
                im = im.crop((0, 0, im.width, im.width * 9 // 16))
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
    <div class="shot" data-b="1"><div class="hd">그냥 AI<i>ChatGPT·Claude 그대로</i></div>{shot(case, "bare")}<p>바로 만들어요. 빈칸은 짐작으로 채워요</p></div>
    <div class="shot h" data-b="2"><div class="hd"><svg class="ic"><use href="#sparkles"/></svg>하네스 AI<i>하네스를 채우고</i></div>{shot(case, "harness")}<p>{cap}</p></div>
  </div>
  <aside class="note">[8~15분] {note} 화면은 시연 때 실제로 받은 결과예요. 재지 않은 시간·숫자는 말하지 않아요.</aside>
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


ASSETS = HERE / "assets"          # CC0 사진·텍스처 (prep_assets.py가 만든 작은 JPEG)
STILLS = HERE / "stills"          # WebGL 없을 때 보여 줄 같은 장면 사진 (shoot.py --stills가 만들어요)
POST = HERE / "vendor" / "three-post"
POST_FILES = ["CopyShader.js", "LuminosityHighPassShader.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js", "UnrealBloomPass.js", "GLTFLoader.js"]
PRETENDARD = HERE / "vendor" / "pretendard" / "PretendardVariable.woff2"   # Pretendard 1.3.9 (SIL OFL 1.1, RFN "Pretendard")
DECK_FONT = "TS Deck Sans"   # OFL: 잘라 낸 글꼴(수정본)은 예약 이름(Pretendard)을 쓰지 않아요


def deck_font_css(html: str) -> str:
    """Pretendard 가변 글꼴을 이 페이지 글자만 남기고 잘라, 이름을 바꿔 WOFF2로 넣어요 (저작권·라이선스 이름표는 그대로)."""
    import base64
    import io
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from embed import _chars
    f = TTFont(str(PRETENDARD), lazy=False)
    o = subset.Options()
    o.flavor = "woff2"; o.layout_features = ["kern", "locl", "tnum"]; o.name_IDs = ["*"]; o.hinting = False; o.notdef_outline = True
    sub = subset.Subsetter(o); sub.populate(text=_chars(html)); sub.subset(f)
    nm = f["name"]
    nm.names = [r for r in nm.names if r.nameID not in (1, 3, 4, 6, 16, 17, 21, 22, 25)]
    for nid, val in ((1, DECK_FONT), (4, DECK_FONT), (6, DECK_FONT.replace(" ", "")), (16, DECK_FONT), (3, DECK_FONT + " (subset of Pretendard 1.3.9, OFL)")):
        nm.setName(val, nid, 3, 1, 0x409)
    buf = io.BytesIO(); f.flavor = "woff2"; f.save(buf)
    b = buf.getvalue()
    print(f"  deck font (Pretendard subset): {len(b) // 1024} KB")
    return ('<style id="deck-font">/* %s = Pretendard 1.3.9 subset · Copyright (c) 2021 Kil Hyung-jin · SIL OFL 1.1 (renamed per Reserved Font Name) */\n'
            '@font-face{font-family:"%s";font-style:normal;font-weight:45 920;font-display:swap;src:url(data:font/woff2;base64,%s) format("woff2")}</style>\n'
            % (DECK_FONT, DECK_FONT, base64.b64encode(b).decode()))


def models_js() -> str:
    import json
    import base64
    out = {p.stem[2:]: p.read_text(encoding="utf-8") for p in sorted(ASSETS.glob("m_*.gltf"))}
    for p in sorted(ASSETS.glob("m_*.glb")):   # 뼈대·애니메이션이 있는 모델은 glb 그대로 (RobotExpressive, CC0)
        out[p.stem[2:]] = "glb:" + base64.b64encode(p.read_bytes()).decode()
    print(f"  models: {list(out)} ({sum(len(v) for v in out.values()) // 1024} KB)")
    return json.dumps(out)


def data_uri(p: Path) -> str:
    import base64
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def svg_uri(p: Path) -> str:
    """공식 로고 SVG를 받은 그대로(바이트 그대로) 넣어요: 색·비율·여백을 건드리지 않아요."""
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(p.read_bytes()).decode()


def ink_uri(p: Path, sat: float, tint, k: float) -> str:
    """흐린 배경 사진(bd_* · hb_*)의 색을 빼고 먹빛 쪽으로 기울여요: 사진은 질감으로만 남고, 색은 덱의 강조색 둘만 남아요."""
    import base64
    import io
    from PIL import Image, ImageEnhance
    im = ImageEnhance.Color(Image.open(p).convert("RGB")).enhance(sat)
    im = Image.blend(im, Image.new("RGB", im.size, tint), k)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


INK = {"road": (0.32, (30, 33, 38), 0.34), "hall": (0.5, (38, 31, 25), 0.3), "kitchen": (1.0, (0, 0, 0), 0.0)}


def backdrop_uri(p: Path) -> str:
    sat, tint, k = INK.get(p.stem.split("_", 1)[1], (1.0, (0, 0, 0), 0.0))
    return ink_uri(p, sat, tint, k) if k else data_uri(p)


def cine_assets() -> tuple[str, str]:
    """(JS object of 3D assets, CSS with photo backdrops + no-WebGL stills)."""
    import json
    js = {p.stem: (backdrop_uri(p) if p.stem.startswith("bd_") else data_uri(p)) for p in sorted(ASSETS.glob("*.jpg")) if not p.stem.startswith(("hb_", "p_"))}
    css = [":root{" + "".join(f"--hb-{p.stem[3:]}:url({backdrop_uri(p)});" for p in sorted(ASSETS.glob("hb_*.jpg"))) + "}"]
    for p in sorted(STILLS.glob("*.jpg")):
        k = p.stem
        css.append(f'.slide[data-scene="{k}"] .fb{{background-image:url({data_uri(p)})}}'
                   f'.slide[data-scene="{k}"] .fbcards,.slide[data-scene="{k}"] .fbword{{display:none}}'
                   f'.slide[data-scene="{k}"] .fbrow{{top:auto;bottom:300px}}')
    kb = sum(len(v) for v in js.values()) // 1024
    print(f"  cine assets: {len(js)} textures/env ({kb} KB b64), stills: {len(list(STILLS.glob('*.jpg')))}")
    return json.dumps(js), "\n".join(css)


def post_fx() -> str:
    out = []
    for f in POST_FILES:
        out.append(f"/* three.js r128 examples/js/{'shaders' if 'Shader.js' in f else 'postprocessing'}/{f} · MIT License · Copyright (c) 2010-2021 three.js authors */\n"
                   + (POST / f).read_text(encoding="utf-8"))
    return "\n".join(out)


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
    slides = slides.replace("__QR__", deck_qr.svg(SITE)).replace("__COMPARE__", compare_slides()).replace("__ONCE__", shot("game", "harness")).replace("__HORSE__", data_uri(ASSETS / "p_horse.jpg"))
    slides = slides.replace("__LOGO_OPENAI__", svg_uri(ASSETS / "logo_openai_blossom_white.svg"))
    for bad in ("?.", "??"):
        for m in re.finditer(re.escape(bad), js):
            nxt = js[m.end():m.end() + 1]
            if bad == "??" or re.match(r"[A-Za-z_$\[(]", nxt):
                raise SystemExit(f"ES2017 rule: {bad} in deck.js at {m.start()}")
    assets_js, cine_css = cine_assets()
    js = js.replace("/*__ASSETS__*/{}", assets_js).replace("/*__MODELS__*/{}", models_js())
    css = css + "\n" + cine_css
    post = post_fx()
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,minimum-scale=1">
<title>AI에게 무기를 주면 · 교사 연수</title>
<meta name="generator" content="교사 스튜디오 · 박진영 (hand-built deck-v2)">
<!--
  Third-party code inlined below (see docs/training/deck-v2-NOTICE.md):
  - three.js r128 (npm three@0.128.0, build/three.min.js) · MIT License · Copyright (c) 2010-2021 three.js authors
  - three.js r128 examples/js post-processing (EffectComposer, RenderPass, ShaderPass, UnrealBloomPass, CopyShader, LuminosityHighPassShader) · MIT
  - CC0 photos/textures: Poly Haven (evening_road_01, school_hall, blinds, asphalt_02, wood_table_001, marble_01), ambientCG (Paper003)
  - anime.js 4.5.0 · MIT License · Copyright (c) 2025 Julian Garnier
  - Lucide icons 1.75.0 · ISC License · Copyright (c) 2026 Lucide Icons and Contributors
  - Pretendard 1.3.9 subset, renamed "TS Deck Sans" · SIL Open Font License 1.1 · Copyright (c) 2021 Kil Hyung-jin
  - Noto Sans KR subset (fallback) · SIL Open Font License 1.1
  - CC0 models: Poly Haven round_spectacles (glTF, textures shrunk); RobotExpressive.glb by Tomás Laulhé (CC0 1.0, from three.js examples)
  - CC0 photo: "Three horse power." by Bernard Spragg. NZ (Wikimedia Commons, CC0 1.0), cropped and graded
  - Trademark: OpenAI Blossom logo (official file from openai.com/brand, unaltered, identification only). OpenAI, ChatGPT, Anthropic, Claude, Google and Gemini are trademarks of their owners; no endorsement implied.
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
<div id="wipe"></div>
</div>
<div id="notes"></div>
<div id="black"></div>
<div id="bar"><button id="bprev" aria-label="이전">◀</button><button id="bnext" aria-label="다음">▶</button><button id="bnotes">노트 N</button><button id="bfs">전체 화면 F</button></div>
{THREE_HEAD}{three}
</script>
<script>
{post}
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
        html, rep = embed(html, families=["Noto Sans KR"])   # 본문은 Pretendard(TS Deck Sans), Noto Sans KR는 대비용
        html = html.replace("</head>", deck_font_css(html) + "</head>", 1)
        print("fonts:", {k: v for k, v in rep.items() if k != "prompt"})
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html.encode('utf-8')) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
