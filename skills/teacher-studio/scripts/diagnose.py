#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""diagnose: turn a VAGUE complaint (「별로야」 「밤티야」 「뭔가 아쉬워」) into a ranked list of likely problems + fix recipes.

Local only. Never edits your output (writes screenshots/JSON into --out). See references/vague-fix.md.

Usage:
  diagnose.py scan  OUT.html|.png|.mp4 [--feedback "밤티야"] [--kind auto|game|tool|page|slides|video]
                    [--prev A.html B.html] [--metrics X-metrics.json] [--feel feel.json] [--out DIR] [--shots N] [--no-render] [--json]
  diagnose.py snapshot FILE [--with spec.json ...] [--label TEXT]     keep a version before every fix
  diagnose.py versions FILE | restore FILE [--to N|prev]               「아까가 나았어」 (restore snapshots the current state first)
  diagnose.py inject FILE.html [--out PREVIEW.html]                    add the feel-capture overlay to a PREVIEW copy (never the final file)
  diagnose.py feel feel.json [--no-save]                               overlay answers -> token tweaks + taste
  diagnose.py taste [show|add PHRASE...|reset]                         ~/.teacher-studio/prefs.json `taste` list
Signals (measured): contrast, text size, overflow, overlap, colour count, element/text count, emptiness, hierarchy, motion/fps,
Korean mid-word breaks, sameness vs other outputs, stock phrasing. Exit 0 always (advisory).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SKILLS = SKILL.parent
sys.path.insert(0, str(HERE))
import prefs  # noqa: E402

MUTE = ["--mute-audio"]  # ALWAYS: a headless page must never make sound
SILENT_JS = ("(function(){try{if(window.speechSynthesis){window.speechSynthesis.speak=function(){};}}catch(e){}"
             "try{if(window.AudioNode&&window.AudioDestinationNode){var oc=AudioNode.prototype.connect;AudioNode.prototype.connect=function(d){if(d instanceof AudioDestinationNode)return d;return oc.apply(this,arguments);};}}catch(e){}})()")

# ---- complaint map: words -> (label, {hypothesis id: boost}) ----
COMPLAINTS = [
    (r"밤티|촌스|구리|구려|올드|싸구려", "촌스러움", {"clutter": .4, "palette_noisy": .4, "weak_hierarchy": .3, "stock_look": .2}),
    (r"심심|밋밋|평범|재미없|휑|허전|단조", "밋밋함", {"no_focal": .4, "no_motion": .4, "flat_palette": .3, "empty": .3}),
    (r"안 ?보|작아|잘 ?안|흐려|흐릿|못 ?읽|읽기", "안 보임", {"small_text": .5, "low_contrast": .5, "overflow": .2}),
    (r"복잡|어지러|정신없|산만|빽빽|너무 ?많", "복잡함", {"clutter": .4, "density": .5, "palette_noisy": .3}),
    (r"ai ?티|AI ?티|기계|티 ?나|뻔해|뻔하|다 ?비슷|똑같|획일", "AI 티", {"sameness": .5, "stock_look": .4, "generic_layout": .3}),
    (r"아까|이전|전이|원래|되돌|돌려", "되돌리기", {"revert": 1.0}),
    (r"느려|버벅|끊겨|렉", "버벅임", {"low_fps": .6}),
    (r"어색|깨져|깨짐|줄바꿈|잘려|짤려", "깨짐", {"overflow": .4, "overlap": .4, "korean_break": .4}),
]
GENERIC = re.compile(r"별로|이상|아쉬|더 ?좋|맘에 ?안|마음에 ?안|그냥 ?그래|애매|뭔가|글쎄|아닌데|아니야")

# ---- hypotheses: id -> (teacher label, kind of fix, recipe for the AI) ----
HYP = {
    "low_contrast": ("글자 색이 배경과 비슷", "legibility", "Darken/lighten text or put it on an opaque card; target WCAG >= 4.5 (>= 7 on a board TV). Game: raise card opacity or change design.style; tool: use --text/--cardText tokens."),
    "small_text": ("글씨가 작음", "legibility", "Raise body/button text to the type floor (board/TV >= 34px, tablet >= 28px, PC >= 20px); shorten the text instead of shrinking it."),
    "overflow": ("글자가 화면 밖으로 나감", "layout", "Shorten copy, allow wrapping (keep-all), reduce columns; verify at 1920x1080 and 1080x1920."),
    "overlap": ("글자/그림이 겹침", "layout", "Re-space the layout (change layout/seed), move decoration to the edges, keep the area around text empty."),
    "clutter": ("너무 많이 들어 있음", "look", "Cut decoration and secondary elements by ~40%, keep ONE focal element, one card style, fewer outlines/shadows."),
    "palette_noisy": ("색이 너무 많음", "look", "Reduce to 1 background family + 1 accent + 1 feedback pair (good/bad); desaturate decoration; pick a calmer style/palette."),
    "weak_hierarchy": ("제목·핵심이 안 눈에 띔", "look", "Make the key text 2.5-4x the median size, weight contrast, one reading order: title > options > decoration."),
    "no_focal": ("눈이 갈 곳이 없음", "look", "Add ONE focal element (big title/number/illustration) with contrast and scale; remove equal-weight competitors."),
    "flat_palette": ("색이 밋밋", "look", "Add a real accent colour on a darker/lighter base, a gradient or tonal layers; avoid all-grey/one-hue screens."),
    "empty": ("휑함", "look", "Fill with purposeful structure (scene, pattern at edges, bigger content) rather than more small items."),
    "no_motion": ("움직임·반응이 없음", "motion", "Add entrance builds, press/hit feedback, correct/streak juice; game: a juice preset; slide/video: staggered reveal. Keep prefers-reduced-motion."),
    "low_fps": ("화면이 버벅임", "motion", "Remove heavy blur/shadow/filters and large animated layers; animate transform/opacity only."),
    "korean_break": ("한글 단어가 중간에서 끊김", "layout", "word-break: keep-all; widen the box or shorten the phrase; avoid fixed narrow widths."),
    "density": ("글이 너무 많음", "content", "Cut text to <= 1 idea per screen; move detail to notes; larger type with fewer words."),
    "sameness": ("전에 만든 것과 비슷", "look", "Change style/seed/layout/palette family to a clearly different direction (not a recolour); show 3 distinct options."),
    "stock_look": ("뻔한 문구·틀", "content", "Replace generic phrases with concrete, subject-specific wording; avoid default emoji/clip-art; use the teacher's own context."),
    "generic_layout": ("뻔한 배치", "look", "Change composition (asymmetry, scale jump, different grid), not just colour."),
    "revert": ("아까 버전이 나았음", "revert", "Run `diagnose.py restore FILE --to prev` (current is snapshotted first), then re-apply only the part that was asked for."),
}
STOCK = ["최고의", "혁신적", "다양한", "함께 성장", "즐거운 시간", "무한한 가능성", "새로운 시작", "알아보아요", "Lorem", "Click here", "여러분의 꿈"]
LOOK_FIXES = {"look", "motion"}  # deserve 2-3 alternative directions as swatches


def _rgba(s):
    v = [float(x) for x in re.findall(r"[\d.]+", s or "")][:4]
    return (v[0], v[1], v[2], v[3] if len(v) > 3 else 1.0) if len(v) >= 3 else (0, 0, 0, 0)


def _lum(c):
    def f(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _ratio(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _bg(bgs):
    layers = [_rgba(b) for b in bgs if _rgba(b)[3] > 0]
    top = next((i for i, c in enumerate(layers) if c[3] >= 0.9), None)
    if top is None:
        return None
    base = layers[top][:3]
    for r, g, b, a in reversed(layers[:top]):
        base = tuple(base[i] * (1 - a) + (r, g, b)[i] * a for i in range(3))
    return base


PROBE_JS = r"""
(function(){
  function bgs(e){var l=[];while(e&&e.nodeType===1){var c=getComputedStyle(e),bi=c.backgroundImage,m=bi&&bi!=='none'?bi.match(/rgba?\([^)]*\)/):null;l.push(m?m[0]:c.backgroundColor);e=e.parentElement;}return l;}
  var out={texts:[],n:0,overflow:0,breaks:[],anim:0};
  var els=document.body.querySelectorAll('*');
  for(var i=0;i<els.length;i++){
    var e=els[i],cs=getComputedStyle(e),r=e.getBoundingClientRect();
    if(e.closest&&e.closest('#ts-feel'))continue;
    if(!r.width||!r.height||cs.display==='none'||cs.visibility==='hidden'||parseFloat(cs.opacity)<0.2||/SCRIPT|STYLE/.test(e.tagName))continue;
    out.n++;
    var txt='';for(var k=0;k<e.childNodes.length;k++)if(e.childNodes[k].nodeType===3)txt+=e.childNodes[k].nodeValue;
    txt=txt.replace(/\s+/g,' ').trim();
    if(!txt||!/[가-힣A-Za-z0-9]/.test(txt))continue;
    out.texts.push({t:txt.slice(0,24),r:[r.left,r.top,r.width,r.height],fs:parseFloat(cs.fontSize),color:cs.color,bgs:bgs(e),w:txt.length});
    if(r.right>innerWidth+4||r.bottom>innerHeight+4||r.left<-4||(e.scrollWidth>e.clientWidth+3&&/hidden|clip/.test(cs.overflowX)))out.overflow++;
    if(out.breaks.length<6&&out.texts.length<160&&/[가-힣]{3,}/.test(txt)){
      try{var tn=null;for(var k2=0;k2<e.childNodes.length;k2++)if(e.childNodes[k2].nodeType===3&&/[가-힣]{3,}/.test(e.childNodes[k2].nodeValue)){tn=e.childNodes[k2];break;}
        if(tn){var re=/[가-힣]{3,}/g,m2;while((m2=re.exec(tn.nodeValue))){var rg=document.createRange();rg.setStart(tn,m2.index);rg.setEnd(tn,m2.index+m2[0].length);var rs=rg.getClientRects(),ys={};for(var q=0;q<rs.length;q++)ys[Math.round(rs[q].top/4)]=1;if(Object.keys(ys).length>1){out.breaks.push(m2[0]);break;}}}}catch(x){}}
  }
  try{out.anim=document.getAnimations().length;}catch(x){}
  return out;
})()
"""
FPS_JS = "new Promise(function(res){var n=0,t0=performance.now();function f(){n++;if(performance.now()-t0<1000)requestAnimationFrame(f);else res(n/((performance.now()-t0)/1000));}requestAnimationFrame(f);})"


def _launch(p):
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(args=MUTE, **kw)
        except Exception:
            continue
    return None


def render(html_path: Path, out_png: Path, shots: int = 1):
    """Render at 1920x1080 (muted, offline). Returns (probe, fps, png_paths); (None, None, []) when no browser."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None, None, []
    with sync_playwright() as p:
        b = _launch(p)
        if not b:
            return None, None, []
        try:
            ctx = b.new_context(viewport={"width": 1920, "height": 1080})
            ctx.add_init_script(SILENT_JS)
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:", "about:")) else r.abort())
            pg = ctx.new_page()
            pg.goto(html_path.resolve().as_uri())
            pg.wait_for_timeout(900)
            probe = pg.evaluate(PROBE_JS)
            pngs = []
            for i in range(max(1, shots)):
                f = out_png if i == 0 else out_png.with_name(out_png.stem + f"-{i + 1}.png")
                pg.screenshot(path=str(f))
                pngs.append(f)
                if i + 1 < shots:
                    pg.keyboard.press("ArrowRight")
                    pg.wait_for_timeout(700)
            pg.wait_for_timeout(500)
            tmp = out_png.with_name(out_png.stem + "-t2.png")
            pg.screenshot(path=str(tmp))
            probe["t2"] = str(tmp)
            return probe, pg.evaluate(FPS_JS), pngs
        finally:
            b.close()


def pixel_signals(png: Path, png2: Path | None = None) -> dict:
    try:
        from PIL import Image
    except Exception:
        return {}
    im = Image.open(png).convert("RGB")
    sm = im.resize((192, 108))
    cnt: dict = {}
    for px in sm.getdata():
        k = (px[0] >> 4, px[1] >> 4, px[2] >> 4)
        cnt[k] = cnt.get(k, 0) + 1
    tot = 192 * 108
    colors = sum(1 for v in cnt.values() if v / tot >= 0.004)
    top = [k for k, _ in sorted(cnt.items(), key=lambda kv: -kv[1])[:6]]
    g = im.convert("L").resize((48 * 4, 27 * 4))
    px = g.load()
    flat = 0
    for cy in range(27):
        for cx in range(48):
            vals = [px[cx * 4 + i, cy * 4 + j] for i in range(4) for j in range(4)]
            m = sum(vals) / 16
            flat += (sum((v - m) ** 2 for v in vals) / 16) ** 0.5 < 4
    hp = list(g.resize((9, 8)).getdata())
    dh = 0
    for y in range(8):
        for x in range(8):
            dh = (dh << 1) | (hp[y * 9 + x] > hp[y * 9 + x + 1])
    motion = None
    if png2 and png2.exists():
        a = list(im.convert("L").resize((96, 54)).getdata())
        c = list(Image.open(png2).convert("L").resize((96, 54)).getdata())
        motion = round(sum(abs(x - y) for x, y in zip(a, c)) / len(a) / 255, 4)
    return {"colors": colors, "empty_ratio": round(flat / (48 * 27), 3), "dhash": dh, "palette": top, "motion_diff": motion}


def sameness(a: dict, b: dict) -> float:
    if not a or not b or "dhash" not in a or "dhash" not in b:
        return 0.0
    ham = bin(a["dhash"] ^ b["dhash"]).count("1")
    pal = len(set(a["palette"][:4]) & set(b["palette"][:4])) / 4
    return round(0.55 * (1 - ham / 64) + 0.45 * pal, 3)


def static_signals(html: str) -> dict:
    sizes = [float(x) for x in re.findall(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", html)]
    return {"bytes": len(html.encode("utf-8")), "css_colors": len(set(re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", html))),
            "keyframes": len(re.findall(r"@keyframes", html)), "transitions": len(re.findall(r"transition\s*:", html)),
            "keep_all": bool(re.search(r"word-break\s*:\s*keep-all", html)), "min_css_px": min(sizes) if sizes else None,
            "stock": [s for s in STOCK if s in html], "feel_overlay": "data-feel-preview" in html}


def detect_kind(path: Path, html: str) -> str:
    n = path.suffix.lower()
    if n in (".mp4", ".webm", ".mov"):
        return "video"
    if n in (".png", ".jpg", ".jpeg"):
        return "image"
    if "class-tools" in path.name.lower() or "class-tools" in str(path).lower() or "check_tool" in html:
        return "tool"
    if re.search(r"ts-host|ts-deco|escape-room|quiz-show|drag-deliver", html) or "game" in path.name.lower():
        return "game"
    if re.search(r"slide|deck", html[:6000], re.I):
        return "slides"
    return "page"


def checker_commands(kind: str, path: Path, out: Path) -> list[str]:
    py = "py" if sys.platform == "win32" else "python3"
    if kind == "game":
        return [f'{py} "{SKILLS / "teacher-game/scripts/check_game.py"}" "{path}"',
                f'{py} "{SKILLS / "teacher-game/scripts/design_review.py"}" "{path}" --out "{out}"   # then LOOK at <name>-sheet.png; pass its -metrics.json via --metrics']
    if kind == "tool":
        return [f'{py} "{SKILLS / "teacher-class-tools/scripts/check_tool.py"}" "{path}"', "diagnose.py already wrote a screenshot -> LOOK at it"]
    if kind == "video":
        return ["video frames + sheet.png are written by diagnose.py (video_eyes) -> LOOK at sheet.png"]
    return ["diagnose.py wrote a screenshot -> LOOK at it (slides: --shots 3 for the first 3 slides)"]


def analyse(a) -> dict:
    path = Path(a.target)
    out = Path(a.out or path.parent / ".ts-diagnose")
    out.mkdir(parents=True, exist_ok=True)
    html = path.read_text(encoding="utf-8", errors="replace") if path.suffix.lower() in (".html", ".htm") else ""
    kind = a.kind if a.kind != "auto" else detect_kind(path, html)
    sig: dict = {"kind": kind}
    if kind == "video":
        ve = next((p for p in (SKILL / "shared/tools/video_eyes.py", SKILLS.parent / "shared/tools/video_eyes.py") if p.exists()), None)
        if ve and not a.no_render:
            subprocess.run([sys.executable, str(ve), str(path), "--out", str(out / "video-eyes"), "--max", "16", "--yes"], capture_output=True, text=True, encoding="utf-8", errors="replace")
            fj = out / "video-eyes" / "frames.json"
            if fj.exists():
                fr = json.loads(fj.read_text(encoding="utf-8"))
                sig["duration"], sig["frames"] = fr.get("duration"), len(fr.get("frames", []))
                sig["sheet"] = str(out / "video-eyes" / "sheet.png")
                files = [out / "video-eyes" / x["file"] for x in fr.get("frames", []) if (out / "video-eyes" / x["file"]).exists()]
                try:
                    from PIL import Image
                    ds = []
                    for f1, f2 in zip(files, files[1:]):
                        x = list(Image.open(f1).convert("L").resize((64, 36)).getdata())
                        y = list(Image.open(f2).convert("L").resize((64, 36)).getdata())
                        ds.append(sum(abs(p - q) for p, q in zip(x, y)) / len(x) / 255)
                    sig["motion_diff"] = round(sum(ds) / len(ds), 4) if ds else None
                    if files:
                        sig.update({k: v for k, v in pixel_signals(files[len(files) // 2]).items() if k != "motion_diff"})
                except Exception:
                    pass
            else:
                sig["note"] = "video_eyes produced no frames (ffmpeg/Pillow missing? run it by hand: it asks consent)"
        else:
            sig["note"] = "video_eyes not found or --no-render"
    elif kind == "image":
        sig.update(pixel_signals(path))
    else:
        sig["static"] = static_signals(html)
        if not a.no_render:
            png = out / f"{path.stem}-diag.png"
            probe, fps, pngs = render(path, png, a.shots)
            if probe:
                t2 = Path(probe.pop("t2"))
                sig.update(pixel_signals(png, t2))
                sig["screenshot"], sig["screenshots"] = str(png), [str(x) for x in pngs]
                sig["fps"] = round(fps, 1) if fps else None
                sig["elements"], sig["texts"], sig["animations"] = probe["n"], len(probe["texts"]), probe["anim"]
                sig["breaks"], sig["overflow"] = probe["breaks"], probe["overflow"]
                tx = probe["texts"]
                fss = [t["fs"] for t in tx]
                if fss:
                    med = sorted(fss)[len(fss) // 2]
                    sig["min_font_px"], sig["median_font_px"], sig["max_font_px"] = min(fss), med, max(fss)
                    sig["hierarchy"] = round(max(fss) / med, 2) if med else None
                cs = []
                for t in tx:
                    bg = _bg(t["bgs"]) if t["fs"] >= 24 else None
                    if bg:
                        cs.append(_ratio(_rgba(t["color"])[:3], bg))
                sig["min_contrast"] = round(min(cs), 2) if cs else None
                ov = 0
                for i in range(len(tx)):
                    for j in range(i + 1, len(tx)):
                        A, B = tx[i]["r"], tx[j]["r"]
                        w = min(A[0] + A[2], B[0] + B[2]) - max(A[0], B[0])
                        h = min(A[1] + A[3], B[1] + B[3]) - max(A[1], B[1])
                        if w > 6 and h > 6 and w * h > 0.25 * min(A[2] * A[3], B[2] * B[3]):
                            ov += 1
                sig["overlaps"] = ov
                sig["text_chars"] = sum(t["w"] for t in tx)
            else:
                sig["note"] = "no headless browser (Playwright): static signals only"
    if a.metrics and Path(a.metrics).exists():  # design_review.py output: measured on real game screens, trust it
        m = json.loads(Path(a.metrics).read_text(encoding="utf-8")).get("summary", {})
        for k in ("colors", "empty_ratio", "hierarchy", "min_contrast", "deco_density", "overlaps"):
            if k in m:
                sig[k] = m[k]
        sig["metrics_file"] = str(a.metrics)
    prevs = [Path(x) for x in (a.prev or [])]
    if not prevs and not a.no_render and kind in ("game", "tool", "page", "slides"):
        prevs = [p for p in sorted(path.parent.glob("*.html"), key=lambda p: -p.stat().st_mtime) if p.resolve() != path.resolve() and path.stem.split('.')[0] not in p.stem and p.stem.split('.')[0] not in path.stem][:3]
    sims = []
    if "dhash" in sig:
        for pv in prevs[:4]:
            try:
                if pv.suffix.lower() in (".png", ".jpg"):
                    ps = pixel_signals(pv)
                else:
                    _, _, pn = render(pv, out / f"{pv.stem}-prev.png")
                    ps = pixel_signals(pn[0]) if pn else {}
                if ps:
                    sims.append((pv.name, sameness(sig, ps)))
            except Exception:
                continue
    sig["sameness"] = sorted(sims, key=lambda x: -x[1])[:3]
    return sig


def _versions_dir(f: Path) -> Path:
    return f.parent / ".ts-versions" / f.stem


def _vlist(f: Path) -> list:
    try:
        return json.loads((_versions_dir(f) / "versions.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def snapshot(f: Path, extra=(), label="") -> int:
    d = _versions_dir(f)
    d.mkdir(parents=True, exist_ok=True)
    vs = _vlist(f)
    n = (vs[-1]["n"] if vs else 0) + 1
    files = {}
    for src in [f, *map(Path, extra)]:
        if src.exists():
            dst = d / f"v{n:03d}-{src.name}"
            shutil.copy2(src, dst)
            files[src.name] = dst.name
    vs.append({"n": n, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "label": label[:60], "files": files})
    (d / "versions.json").write_text(json.dumps(vs, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def restore(f: Path, to: str) -> str:
    vs = _vlist(f)
    if not vs:
        return "저장된 이전 버전이 없어요."
    d = _versions_dir(f)
    target = vs[-1] if to == "prev" else next((v for v in vs if str(v["n"]) == to), None)
    if not target:
        return f"버전 {to}이(가) 없어요. 목록: {[v['n'] for v in vs]}"
    if to == "prev" and f.exists() and len(vs) > 1:
        last = d / target["files"].get(f.name, "")
        if last.exists() and hashlib.md5(last.read_bytes()).hexdigest() == hashlib.md5(f.read_bytes()).hexdigest():
            target = vs[-2]  # newest snapshot already equals the current file: step back one more
    keep = snapshot(f, label="before restore")  # nothing is ever lost
    for name, stored in target["files"].items():
        shutil.copy2(d / stored, f.parent / name)
    return f"v{target['n']}({target['time']})로 되돌렸어요. 되돌리기 직전 상태는 v{keep}로 보관돼 있어요."


def rank(sig: dict, feedback: str, f: Path | None):
    base: dict = {}
    S = sig.get("static", {})

    def put(k, v, ev):
        if v > 0 and (k not in base or v > base[k][0]):
            base[k] = (round(min(v, 1.0), 2), ev)
    mc = sig.get("min_contrast")
    if mc is not None and mc < 4.5:
        put("low_contrast", .5 + (4.5 - mc) / 4.5 * .5, f"가장 낮은 글자 대비 {mc} (기준 4.5)")
    mf = sig.get("min_font_px")
    if mf is not None and mf < 30:
        put("small_text", .45 + (30 - mf) / 30 * .55, f"가장 작은 글씨 {mf}px (칠판 기준 34px 이상)")
    if sig.get("overflow"):
        put("overflow", min(.5 + .1 * sig["overflow"], 1), f"화면 밖/잘린 글자 상자 {sig['overflow']}개")
    if sig.get("overlaps"):
        put("overlap", min(.5 + .15 * sig["overlaps"], 1), f"글자끼리 겹침 {sig['overlaps']}곳")
    c = sig.get("colors")
    lim = 44 if sig.get("kind") in ("game", "slides") else 24  # game scenes are legitimately colourful
    if c is not None and c >= lim:
        put("palette_noisy", min(.4 + (c - lim) / 30, 1), f"화면의 색 {c}가지 (기준 {lim})")
        if c >= lim + 8:
            put("clutter", .45, f"색 {c}가지(장식 과다 가능)")
    n, t, ch = sig.get("elements"), sig.get("texts"), sig.get("text_chars")
    if (n or 0) > 250 or (t or 0) > 28:
        put("clutter", min(((n or 0) / 250 + (t or 0) / 28) / 3, 1), f"요소 {n}개, 글 상자 {t}개")
    if (ch or 0) > 220 or (t or 0) > 22:
        put("density", min(((ch or 0) / 220 + (t or 0) / 22) / 2.5, 1), f"한 화면 글자 약 {ch}자, 글 상자 {t}개")
    h = sig.get("hierarchy")
    if h is not None and h < 2.2:
        put("weak_hierarchy", .45 + (2.2 - h) / 2.2 * .5, f"가장 큰 글씨/보통 글씨 = {h}배 (2.5배 이상이 좋음)")
        put("no_focal", .35 + (2.2 - h) / 2.2 * .3, "시선이 모일 큰 요소가 약함")
    e = sig.get("empty_ratio")
    if e is not None and e > .72:
        put("empty", min((e - .6) * 2.5, 1), f"평평한 빈 영역 {int(e * 100)}%")
    if c is not None and c <= 6 and (e or 0) > .6:
        put("flat_palette", .6, f"색 {c}가지 + 빈 영역 {int((e or 0) * 100)}%")
    md, an = sig.get("motion_diff"), sig.get("animations")
    if md is not None and md < .004 and not an and sig.get("kind") != "image":
        put("no_motion", .55, f"0.7초 사이 화면 변화 {md:.3%}, 애니메이션 0")
    elif S and not S.get("keyframes") and not S.get("transitions") and sig.get("kind") in ("game", "slides", "page"):
        put("no_motion", .35, "CSS 애니메이션·전환 없음")
    if sig.get("fps") and sig["fps"] < 40:
        put("low_fps", min((50 - sig["fps"]) / 40, 1), f"초당 {sig['fps']}프레임")
    if sig.get("breaks"):
        put("korean_break", .55 + .1 * len(sig["breaks"]), f"단어 중간 줄바꿈: {sig['breaks'][:3]}")
    elif S and not S.get("keep_all"):
        put("korean_break", .3, "word-break: keep-all 없음")
    if sig.get("sameness") and sig["sameness"][0][1] >= .7:
        put("sameness", sig["sameness"][0][1], f"{sig['sameness'][0][0]}와(과) {int(sig['sameness'][0][1] * 100)}% 비슷")
    if S.get("stock"):
        put("stock_look", .4 + .1 * len(S["stock"]), f"뻔한 문구: {S['stock'][:3]}")
    if S.get("feel_overlay"):
        sig["warning"] = "이 파일에 feel 미리보기 오버레이가 들어 있어요: 공유용 최종 파일로 쓰면 안 돼요."
    tags: list = []
    boost: dict = {}
    fb = feedback or ""
    for rx, label, hs in COMPLAINTS:
        if re.search(rx, fb, re.I):
            tags.append(label)
            for k, v in hs.items():
                boost[k] = max(boost.get(k, 0), v)
    mode = "mapped" if tags else ("generic" if fb.strip() else "none")
    if "revert" in boost and f is not None and not _vlist(f):
        boost.pop("revert")
        tags.remove("되돌리기")
    ranked = []
    for k in set(base) | set(boost):
        b, ev = base.get(k, (0.0, "측정 신호는 약함 (말투에서 추정)"))
        sc = round(min(b + boost.get(k, 0) * .8, 1.0), 2)
        if k == "revert":
            ev = "이전 버전이 보관돼 있어요"
        if sc >= .2:
            ranked.append({"id": k, "score": sc, "teacher_label": HYP[k][0], "evidence": ev, "type": HYP[k][1], "fix": HYP[k][2]})
    ranked.sort(key=lambda r: -r["score"])
    return ranked, tags, mode


TASTE_NOTES = {
    "덜 화려하게": "덜 화려하게: 장식·색 수·움직임 강도를 낮은 쪽으로",
    "더 화려하게": "더 화려하게: juice/움직임/악센트 색을 한 단계 올리기",
    "글씨 크게": "글씨 크게: type floor보다 한 단계 크게, 글은 더 짧게",
    "단순하게": "단순하게: 요소 수 줄이기, 카드 스타일 하나",
}


def directions(taste: list) -> list:
    d = [("차분하게", "한 색 계열 + 포인트 1개, 장식 최소, 글씨 크게"), ("또렷하게", "대비 큰 두 색 + 큰 제목, 움직임은 한 번 크게"), ("재미있게", "밝은 악센트 + 반응 효과·움직임 추가")]
    if "덜 화려하게" in taste:
        d = [x for x in d if x[0] != "재미있게"] + [("고급스럽게", "짙은 바탕 + 금속 느낌 한 색, 얇은 선, 여백")]
    return d


def cmd_scan(a) -> None:
    sig = analyse(a)
    f = Path(a.target)
    fe = None
    if a.feel:
        fe = feel_tweaks(json.loads(Path(a.feel).read_text(encoding="utf-8")))
        a.feedback = (a.feedback or "") + " " + " ".join(fe["complaint_words"])
    ranked, tags, mode = rank(sig, a.feedback or "", f)
    kind = sig["kind"]
    out = Path(a.out or f.parent / ".ts-diagnose")
    taste = prefs.load_taste()
    res = {"file": str(f), "kind": kind, "feedback_tags": tags, "mode": mode, "ranked": ranked[:6],
           "signals": {k: v for k, v in sig.items() if k not in ("static", "dhash", "palette", "screenshots")},
           "run_checkers": checker_commands(kind, f, out), "taste": taste,
           "taste_notes": [TASTE_NOTES.get(t, f"{t}: 이번에도 반영") for t in taste], "versions": len(_vlist(f))}
    if fe:
        res["feel"] = fe
    res["apply"] = [r["id"] for r in ranked[:2]]
    show_alt = bool(ranked and ranked[0]["type"] in LOOK_FIXES) or any(t in tags for t in ("촌스러움", "밋밋함"))
    res["directions"] = directions(taste) if show_alt else []
    amb = (not ranked) or ranked[0]["score"] < .4 or (len(ranked) > 1 and ranked[0]["score"] - ranked[1]["score"] < .05 and ranked[0]["type"] != ranked[1]["type"])
    res["ambiguous"] = bool(amb)
    if amb:
        res["ask_one"] = "어느 쪽이 더 아쉬우세요? (추천: 4번) 1) 너무 복잡·화려해요  2) 밋밋하고 심심해요  3) 글씨가 안 보여요  4) 잘 모르겠어요(보기를 보여 드릴게요)"
    res["say"] = "이렇게 고쳐 봤어요: <무엇을 어떻게 바꿨는지 한 줄>. 이 중 더 마음에 드는 쪽 있으세요?"
    if sig.get("warning"):
        res["warning"] = sig["warning"]
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{f.stem}-diagnosis.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return
    print(f"진단: {f.name} [{kind}]  불평 해석: {', '.join(tags) or '말투만(' + mode + ')'}")
    s = res["signals"]
    keys = ["colors", "elements", "texts", "min_font_px", "hierarchy", "min_contrast", "empty_ratio", "overflow", "overlaps", "animations", "fps", "motion_diff", "breaks"]
    print("측정:", ", ".join(f"{k}={s[k]}" for k in keys if k in s and s[k] is not None))
    if s.get("sameness"):
        print("비슷함:", s["sameness"])
    for k, lab in (("screenshot", "화면 캡처"), ("sheet", "영상 접촉 시트")):
        if s.get(k):
            print(f"{lab}(직접 눈으로 볼 것): {s[k]}")
    if s.get("note"):
        print("참고:", s["note"])
    print("\n추정 원인(높은 순):")
    for i, r in enumerate(ranked[:6], 1):
        print(f" {i}. [{r['score']:.2f}] {r['id']} - {r['teacher_label']} | 근거: {r['evidence']}\n      고치기: {r['fix']}")
    if not ranked:
        print(" (측정 신호가 약해요: 화면을 직접 보고 판단하세요)")
    print("\n다음: 상위 1~2개 적용 -> 전/후" + (" + 방향 보기: " + ", ".join(x[0] for x in res["directions"]) if res["directions"] else "") + " (고치기 전에 snapshot!)")
    for n in res["taste_notes"]:
        print("  취향:", n)
    if res["ambiguous"]:
        print("애매함 -> 질문은 딱 하나:", res["ask_one"])
    for c in res["run_checkers"]:
        print("  점검:", c)
    if res.get("warning"):
        print("경고:", res["warning"])
    print("말투:", res["say"])


# ---- feel-capture overlay answers -> tweaks ----
AXES = {  # slider value -2..+2 : (negative phrase, positive phrase, what to change)
    "calm_vivid": ("덜 화려하게", "더 화려하게", "palette saturation/accent colour and juice/motion intensity"),
    "simple_rich": ("단순하게", "풍부하게", "decoration/element count and secondary info"),
    "warm_cool": ("따뜻한 색", "시원한 색", "palette hue family (warm = amber/coral, cool = blue/teal)"),
    "cute_premium": ("귀엽게", "고급스럽게", "corner radius/illustration vs thin lines, darker base, restrained accent"),
    "text_size": ("글씨 작게", "글씨 크게", "type scale (font-size tokens) and copy length"),
}
CHIP_TASTE = {"밝게": "밝게", "어둡게": "어둡게", "깔끔하게": "단순하게", "재밌게": "더 화려하게", "고급스럽게": "고급스럽게", "귀엽게": "귀엽게"}


def feel_tweaks(d: dict) -> dict:
    taste, words, tweaks = [], [], []
    for r in d.get("ab") or []:  # {"axis","pick":"A"|"B","positive":"A"|"B"}: positive = the letter that was the "more <pos>" variant
        if r.get("axis") in AXES and r.get("pick") in ("A", "B"):
            taste.append(AXES[r["axis"]][1 if r["pick"] == r.get("positive", "B") else 0])
    for c in d.get("chips") or []:
        if c in CHIP_TASTE:
            taste.append(CHIP_TASTE[c])
        if c == "촌스러움 빼기":
            words.append("밤티")
    sl = d.get("sliders") or {}
    for k, (neg, pos, what) in AXES.items():  # explicit sliders last = they win over A/B on the same axis
        v = sl.get(k)
        if isinstance(v, (int, float)) and abs(v) >= 1:
            tweaks.append({"axis": k, "value": v, "do": f"{'slightly' if abs(v) < 2 else 'strongly'} toward {pos if v > 0 else neg}: adjust {what}"})
            taste.append(pos if v > 0 else neg)
    for a_, b_ in ((n, p) for n, p, _ in AXES.values()):  # keep only the last of an opposite pair
        ia = max((i for i, t in enumerate(taste) if t == a_), default=-1)
        ib = max((i for i, t in enumerate(taste) if t == b_), default=-1)
        if ia >= 0 and ib >= 0:
            taste = [t for i, t in enumerate(taste) if not (t == (b_ if ia > ib else a_))]
    rating = d.get("rating")
    if isinstance(rating, int) and rating <= 2:
        words.append("별로")
    marks = [{"where": m.get("sel") or m.get("tag"), "text": (m.get("text") or "")[:30], "xy": [m.get("x"), m.get("y")], "do": "fix THIS element first (size/contrast/placement/removal)"} for m in (d.get("marks") or [])[:8]]
    seen: list = []
    for t in taste:
        if t not in seen:
            seen.append(t)
    return {"tweaks": tweaks, "taste": seen, "marks": marks, "note": (d.get("note") or "")[:120], "rating": rating, "chips": d.get("chips") or [], "complaint_words": words}


def cmd_feel(a) -> None:
    r = feel_tweaks(json.loads(Path(a.file).read_text(encoding="utf-8")))
    if r["taste"] and not a.no_save:
        prefs.add_taste(r["taste"])
    print(json.dumps(r, ensure_ascii=False, indent=1))


def cmd_inject(a) -> None:
    src = Path(a.file)
    js = (SKILL / "assets" / "feel.js").read_text(encoding="utf-8")
    html = re.sub(r"<script data-feel-preview>.*?</script>", "", src.read_text(encoding="utf-8"), flags=re.S)
    dst = Path(a.out) if a.out else src.with_name(src.stem + ".feel-preview.html")
    if dst.resolve() == src.resolve():
        sys.exit("미리보기 복사본에만 넣어요 (원본에는 넣지 않아요).")
    tag = "<script data-feel-preview>" + js.replace("</script>", "<\\/script>") + "</script>"
    html = html.replace("</body>", tag + "</body>", 1) if "</body>" in html else html + tag
    dst.write_text(html, encoding="utf-8")
    print("PREVIEW", dst, "(미리보기 전용: 공유용 최종 파일이 아니에요)")


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] not in {"scan", "snapshot", "versions", "restore", "inject", "feel", "taste"} and not argv[0].startswith("-"):
        argv = ["scan"] + argv
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("scan")
    s.add_argument("target")
    s.add_argument("--feedback", default="")
    s.add_argument("--kind", default="auto", choices=["auto", "game", "tool", "page", "slides", "video", "image"])
    s.add_argument("--prev", nargs="*")
    s.add_argument("--metrics")
    s.add_argument("--feel")
    s.add_argument("--out")
    s.add_argument("--shots", type=int, default=1)
    s.add_argument("--no-render", action="store_true")
    s.add_argument("--json", action="store_true")
    sn = sp.add_parser("snapshot")
    sn.add_argument("file")
    sn.add_argument("--with", dest="extra", nargs="*", default=[])
    sn.add_argument("--label", default="")
    sp.add_parser("versions").add_argument("file")
    r = sp.add_parser("restore")
    r.add_argument("file")
    r.add_argument("--to", default="prev")
    i = sp.add_parser("inject")
    i.add_argument("file")
    i.add_argument("--out")
    fe = sp.add_parser("feel")
    fe.add_argument("file")
    fe.add_argument("--no-save", action="store_true")
    t = sp.add_parser("taste")
    t.add_argument("action", nargs="?", default="show", choices=["show", "add", "reset"])
    t.add_argument("items", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "scan":
        cmd_scan(a)
    elif a.cmd == "snapshot":
        print(f"v{snapshot(Path(a.file), a.extra, a.label)} 보관했어요 ({_versions_dir(Path(a.file))})")
    elif a.cmd == "versions":
        for x in _vlist(Path(a.file)):
            print(x["n"], x["time"], x["label"], list(x["files"]))
    elif a.cmd == "restore":
        print(restore(Path(a.file), a.to))
    elif a.cmd == "inject":
        cmd_inject(a)
    elif a.cmd == "feel":
        cmd_feel(a)
    elif a.action == "add":
        print("취향 기억:", " · ".join(prefs.add_taste(a.items)) or "없음")
    elif a.action == "reset":
        subprocess.run([sys.executable, str(HERE / "prefs.py"), "taste-reset"])
    else:
        print(json.dumps(prefs.load_taste(), ensure_ascii=False))


if __name__ == "__main__":
    main()
