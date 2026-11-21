#!/usr/bin/env python3
"""Build docs/training/deck-v3.html (motion-graphics deck): one offline file (three.js r128 + anime.js + Lucide icons + Noto KR subset).

One-command rebuild (Windows):  set PYTHONUTF8=1 && py docs/training/deck-v3-src/build.py
  - re-embeds the 「같은 부탁, 다른 결과」 screenshots from docs/training/compare/<case>-bare.png / <case>-harness.png
    (cases: game, parents, data, law; .png/.jpg/.webp). Missing ones become a 「결과 화면 들어갈 자리」 frame.
  - three.js: taken from --three PATH (npm pack three@0.128.0 -> package/build/three.min.js, MIT) or, by default,
    re-used from the three.js block already inside deck-v2.html. Either way the sha256 must match r128.
Reads the repo's shared/ tools read-only (vendor files, qrcodegen, font embedder). Writes only docs/training/deck-v2.html.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE.parent / "deck-v3.html"
V2 = HERE.parent / "deck-v2-src"          # 사진·모델·글꼴·three 확장은 v2 폴더 것을 읽기만 해요 (v2는 예비 덱으로 그대로)
V2_HTML = HERE.parent / "deck-v2.html"
sys.path.insert(0, str(REPO / "shared" / "fonts"))
sys.path.insert(0, str(REPO / "skills" / "teacher-slides" / "scripts"))

THREE_SHA = "9274bbcec8d96168626c732b5d31c775aa8cfb7eaa0599bec0c175908a2c1ce2"
SITE = "https://github.com/zln02/teacher-studio"
THREE_HEAD = "<script>/* three.js r128 · MIT License · Copyright (c) 2010-2021 three.js authors */\n"
COMPARE_DIR = HERE.parent / "compare"
BARE_DIR = V2 / "compare-bare"
CASES = [
    ("game", "수업", "중2 과학 빛 복습 게임", "기획 3안을 먼저 보여 주고, 고른 안으로 만들고 스스로 점검해요",
     "「첫 번째 부탁이에요. 왼쪽은 바로 만들었고, 오른쪽은 기획 3안부터 보여 줬어요. 저는 하나 골랐을 뿐이에요.」"),
    ("parents", "업무", "학부모 총회 발표자료", "누가 보는지부터 묻고, 발표 흐름을 먼저 잡아요",
     "「학부모 총회 발표자료예요. 오른쪽은 누가 보시는지, 몇 분인지부터 물어보고 흐름을 먼저 잡았어요.」"),
    ("data", "업무", "우리 반 성적 엑셀 분석", "이름은 숨기고, 그래프와 쉬운 말로 보여 줘요",
     "「성적 엑셀이에요. 오른쪽은 학생 이름을 숨기고 그래프와 쉬운 말로 정리했어요. 학생 정보는 이렇게 지켜야 해요.」"),
    ("law", "업무", "가정통신문에 이 그림 써도 돼?", "최신 법을 직접 찾아보고, 근거와 함께 알려 줘요",
     "「이 그림 써도 되나요? 왼쪽은 그럴듯하게 대답했고, 오른쪽은 최신 법을 직접 찾아 근거를 붙였어요. 그래도 마지막 판단과 책임은 사람에게, 여러분께 있어요.」"),
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
    for k, (case, area, ask, cap, note) in enumerate(CASES, 1):
        # v3: 머리글은 네 장이 같은 자리에 그대로 이어져요(움직이지 않음) · 부탁 말풍선 = 통통 · 그냥 AI = 왼쪽에서 탁 · 하네스 AI = 카드 뒤집기
        out.append(f"""<section class="slide cmp v3" data-agenda="2" data-fx="v3cmp" data-steps="2">
  <div class="hd"><div class="kicker m-k">같은 부탁, 다른 결과</div></div><div class="cno"><span class="area">{area}</span>{k} / {len(CASES)}</div>
  <div class="ask"><svg class="ic"><use href="#message-square"/></svg>「{ask}」</div>
  <div class="pair">
    <div class="shot sb"><div class="hd">그냥 AI<i>요리사 혼자, 맨손으로</i></div>{shot(case, "bare")}<p>바로 만들어요. 빈칸은 짐작으로 채워요</p></div>
    <div class="shot h"><div class="hd"><svg class="ic"><use href="#sparkles"/></svg>하네스 AI<i>하네스를 채우고</i></div>{shot(case, "harness")}<p>{cap}</p></div>
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


ASSETS = V2 / "assets"          # CC0 사진·텍스처 (prep_assets.py가 만든 작은 JPEG)
STILLS = V2 / "stills"          # WebGL 없을 때 보여 줄 같은 장면 사진 (shoot.py --stills가 만들어요)
POST = V2 / "vendor" / "three-post"
POST_FILES = ["CopyShader.js", "LuminosityHighPassShader.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js", "UnrealBloomPass.js", "GLTFLoader.js"]
PRETENDARD = V2 / "vendor" / "pretendard" / "PretendardVariable.woff2"   # Pretendard 1.3.9 (SIL OFL 1.1, RFN "Pretendard")
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
        if p.stem == "m_robot" and (HERE / "robot.js").exists():   # v3: 로봇은 코드로 만든 RobotChef(robot.js) → GLB는 안 넣어요 (약 620 KB 줄어요)
            continue
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


ILLUST = HERE / "illust"          # 그림(장면 일러스트): illust/<이름>.jpg · 그림 자리 data-il="<이름>"에 들어가요 (없으면 빈 자리 그대로)


def prep_illust(src: Path) -> None:
    """--illust-src 폴더의 그림(png/webp/jpg)을 1600px · JPEG(≤250 KB)로 줄여 illust/에 넣어요."""
    from PIL import Image
    ILLUST.mkdir(exist_ok=True)
    for p in sorted(src.glob("*")):
        if p.suffix.lower() not in (".png", ".webp", ".jpg", ".jpeg") or p.stem == "sheet":
            continue
        im = Image.open(p).convert("RGB")
        im.thumbnail((1600, 900))
        out = ILLUST / (p.stem + ".jpg")
        for q in (82, 74, 66, 58):
            im.save(out, "JPEG", quality=q, optimize=True, progressive=True)
            if out.stat().st_size <= 250 * 1024:
                break
        print(f"  illust {p.name} -> {out.name} {out.stat().st_size // 1024} KB")


def illust_assets() -> tuple[dict, str]:
    """(JS 그림 {il_이름: dataURI} · CSS [data-il=이름] 배경). 3D 장면 뒤 배경은 어둡게 한 판(il_이름_dk)도 같이."""
    import base64
    import io
    from PIL import Image, ImageEnhance
    js, css = {}, []
    for p in sorted(ILLUST.glob("*.jpg")) if ILLUST.exists() else []:
        k = p.stem
        uri = data_uri(p)
        css.append(f'[data-il="{k}"]{{background-image:url({uri})}}')
        if k not in ("cover-a", "kitchen-backdrop", "closing"):   # 3D 장면 뒤에 까는 것만 어둡게 한 판을 만들어요
            continue
        im = ImageEnhance.Brightness(Image.open(p).convert("RGB")).enhance(0.4)
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=78, optimize=True)
        js["il_" + k.replace("-", "_") + "_dk"] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    if js:
        print(f"  illustrations: {len(css)}")
    return js, "\n".join(css)


def post_fx() -> str:
    out = []
    for f in POST_FILES:
        out.append(f"/* three.js r128 examples/js/{'shaders' if 'Shader.js' in f else 'postprocessing'}/{f} · MIT License · Copyright (c) 2010-2021 three.js authors */\n"
                   + (POST / f).read_text(encoding="utf-8"))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--three", default=str(V2 / "vendor" / "three-0.128.0.min.js"))
    ap.add_argument("--no-fonts", action="store_true")
    ap.add_argument("--slides", default=str(HERE / "slides.html"), help="다른 덱(예: ai-cheating/deck-src/slides.html)을 같은 엔진으로 만들 때")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--title", default="AI에게 무기를 주면 · 교사 연수")
    ap.add_argument("--foot", default="AI에게 무기를 주면 · 박진영")
    ap.add_argument("--illust-src", default="", help="그림 폴더(예: 임시 폴더의 illust-gpt)를 줄여서 illust/에 넣고 만들어요")
    ap.add_argument("--agenda", default="", help="쉼표로 구분한 구간 이름 (비우면 본 덱 기본값)")
    a = ap.parse_args()
    three_p = Path(a.three)
    if three_p.exists():
        three = three_p.read_bytes()
    else:
        old = V2_HTML.read_text(encoding="utf-8")
        i = old.index(THREE_HEAD) + len(THREE_HEAD)
        three = old[i:old.index("\n</script>", i)].encode("utf-8")
    if hashlib.sha256(three).hexdigest() != THREE_SHA:
        raise SystemExit("three.min.js hash mismatch (expected npm three@0.128.0 build/three.min.js)")
    three = three.decode("utf-8")
    anime = (REPO / "shared/vendor/animejs/anime-4.5.0.umd.min.js").read_text(encoding="utf-8")
    css = (HERE / "deck.css").read_text(encoding="utf-8") + "\n" + (HERE / "motion.css").read_text(encoding="utf-8") + "\n" + (HERE / "motion2.css").read_text(encoding="utf-8") + "\n" + (HERE / "focus.css").read_text(encoding="utf-8")
    slides = Path(a.slides).read_text(encoding="utf-8")
    js = (HERE / "deck.js").read_text(encoding="utf-8")
    js = js.replace("/*__FOOT__*/'AI에게 무기를 주면 · 박진영'", json.dumps(a.foot, ensure_ascii=False))
    js = js.replace("/*__MOTION__*/", (HERE / "motion.js").read_text(encoding="utf-8") + (HERE / "motion2.js").read_text(encoding="utf-8"), 1)
    if a.agenda.strip():   # 다른 덱: 구간 이름을 바꿔요 ("-" 하나면 빈 목록)
        names = [x.strip() for x in a.agenda.split(",") if x.strip() and x.strip() != "-"]
        js = re.sub(r"/\*__AGENDA__\*/\[[^\]]*\]", lambda m: json.dumps(names, ensure_ascii=False), js, count=1)
    import deck_qr  # read-only use of the slides skill's QR helper (qrcodegen, MIT)
    slides = slides.replace("__QR__", deck_qr.svg(SITE)).replace("__COMPARE__", compare_slides()).replace("__ONCE__", shot("game", "harness")).replace("__HORSE__", data_uri(ASSETS / "p_horse.jpg"))
    for bad in ("?.", "??"):
        for m in re.finditer(re.escape(bad), js):
            nxt = js[m.end():m.end() + 1]
            if bad == "??" or re.match(r"[A-Za-z_$\[(]", nxt):
                raise SystemExit(f"ES2017 rule: {bad} in deck.js at {m.start()}")
    if a.illust_src:
        prep_illust(Path(a.illust_src))
    assets_js, cine_css = cine_assets()
    il_js, il_css = illust_assets()
    if il_js:
        assets_js = assets_js.rstrip("}") + ("," if assets_js.strip() != "{}" else "") + json.dumps(il_js)[1:]
    cine_css = cine_css + "\n" + il_css
    import base64 as _b64
    pup = {p.stem: "data:image/webp;base64," + _b64.b64encode(p.read_bytes()).decode() for p in sorted((HERE / "puppet").glob("*.webp"))} if 'data-scene="robot"' in slides else {}
    js = js.replace("/*__PUPPET__*/{}", json.dumps(pup))
    js = js.replace("/*__ASSETS__*/{}", assets_js).replace("/*__MODELS__*/{}", models_js())
    css = css + "\n" + cine_css
    post = post_fx()
    robot_js = (HERE / "robot.js").read_text(encoding="utf-8") if (HERE / "robot.js").exists() and 'data-scene="robot"' in slides else ""
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,minimum-scale=1">
<title>{a.title}</title>
<meta name="generator" content="교사 스튜디오 · 박진영 (hand-built deck-v3 · motion)">
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
  - Trademarks: app names on the hands-on slides are trademarks of their owners, used only to name the app to open; no endorsement implied. No company logos are embedded.
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
<script>/* RobotChef (deck-v3-src/robot.js) · 이 저장소에서 새로 만든 코드 로봇 요리사 */
{robot_js}
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
    out = Path(a.out)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html.encode('utf-8')) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
