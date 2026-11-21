# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Colour with meaning: a word that names a colour is drawn in that colour, never in the next colour of a rotation.

「초록불」 on an orange head and 「빨간불」 on a purple one teach a small child the wrong thing. Every place that hands out colours in
turn (slide compare heads, list badges, game sort bins, team chips, medals) asks here first.

    color_of("🟢 초록불")              -> "#1E9E50"      (None when the text names no colour, or two different ones)
    key_of("빨강 팀")                   -> "red"
    assign(["초록불", "빨간불"], tones)  -> ["#1E9E50", "#E5352B"]   meaning first; the others keep the rotation, skipping look-alikes
    on(hex)                             -> "#ffffff" | "#111111"    text colour on that fill
    js()                                -> the same table as a small ES2017 script: window.TSMeaning.color(text) / .assign(labels, tones)

Rules: only short labels are read (a head, a name, the first words of a line); one colour word decides, two different ones do not.
「금 · 은 · 동」 count only as whole labels or as 금메달 · 은상 · 🥉 (금요일, 지금, 운동 are not colours). 「파란불」 is the green light.
"""
from __future__ import annotations

import json
import re

# key -> (hex, words matched anywhere in the label, whole-label tokens)
TABLE = [
    ("green", "#1E9E50", ["초록불", "파란불", "푸른불", "녹색불", "초록", "녹색", "풀색", "녹팀", "🟢", "🟩", "💚"], ["녹"]),
    ("red", "#E5352B", ["빨간불", "빨강", "빨간", "빨갛", "빨개", "붉은", "적색", "홍팀", "적팀", "레드", "🔴", "🟥", "❤️", "❤"], ["적", "홍"]),
    ("amber", "#F2A100", ["노란불", "주황불", "황색불"], []),
    ("orange", "#F28C1E", ["주황", "귤색", "오렌지색", "오렌지 팀", "오렌지팀", "🟠", "🟧", "🧡"], ["오렌지"]),
    ("yellow", "#F2C200", ["노랑", "노란", "노랗", "황색", "황팀", "옐로", "🟡", "🟨", "💛"], ["황"]),
    ("lime", "#7CB518", ["연두", "연둣빛"], []),
    ("sky", "#3FA9E8", ["하늘색", "하늘빛"], []),
    ("navy", "#23357A", ["남색", "감색", "네이비"], []),
    ("blue", "#1F6FE0", ["파랑", "파란", "파랗", "청색", "청팀", "블루", "🔵", "🟦", "💙"], ["청"]),
    ("purple", "#8A4FD0", ["보라색", "보랏빛", "보라 팀", "보라팀", "자주색", "퍼플", "🟣", "🟪", "💜"], ["보라"]),
    ("pink", "#F06FA8", ["분홍", "핑크", "🩷"], []),
    ("brown", "#8B5A2B", ["갈색", "밤색", "고동색", "🟤", "🟫", "🤎"], []),
    ("gold", "#D4A017", ["금메달", "금상", "금색", "황금", "🥇"], ["금"]),
    ("silver", "#9AA3AD", ["은메달", "은상", "은색", "은빛", "🥈"], ["은"]),
    ("bronze", "#B0703A", ["동메달", "구릿빛", "청동", "🥉"], ["동", "동상"]),
    ("black", "#222222", ["검정", "검은", "까만", "까망", "흑색", "흑팀", "⚫", "⬛", "🖤"], ["흑"]),
    ("white", "#F1F1EC", ["하양", "하얀", "하얗", "흰색", "백색", "백팀", "⚪", "⬜", "🤍"], ["백", "흰"]),
    ("grey", "#8A8F98", ["회색", "잿빛"], []),
]
# Opposites that carry a colour only as a PAIR on one screen: 「안전 / 위험」 side by side is green / red (a lone 「안전하게 건너요」 is not green)
PAIRS = [("green", ["안전", "해도 돼요", "좋은 행동", "바른 행동", "올바른"]), ("red", ["위험", "금지", "안 돼요", "하면 안", "나쁜 행동", "잘못된"])]
# words that only look like a colour word
NOT = ["파란만장", "푸른곰팡이", "황금연휴", "황금률", "빨간펜 선생님", "동상이몽", "초록동색", "금상첨화", "은상어"]
MAX_LEN = 26  # a label, not a sentence: longer text is read up to its first clause

_HEX = {k: h for k, h, _w, _t in TABLE}
_WORDS = sorted(((w, k) for k, _h, ws, _t in TABLE for w in ws), key=lambda x: -len(x[0]))  # longest first: 「노란불」 before 「노란」
_TOKENS = {t: k for k, _h, _w, ts in TABLE for t in ts}
_EDGE = re.compile(r"^[\s!-/:-@\[-`{-~·•]+|[\s!-/:-@\[-`{-~·•]+$")
_CLAUSE = re.compile(r"[:：,，.。!?()（）\n]| - | – | — ")
_SUFFIX = re.compile(r"\s*(?:팀|모둠|조|반|색|메달|불|편|군)$")


def _label(text) -> str:
    s = re.sub(r"\*\*|__|`", "", str(text or "")).strip()
    if len(s) > MAX_LEN:
        s = _CLAUSE.split(s, 1)[0].strip()
    return s if len(s) <= MAX_LEN else ""


def keys_in(text) -> list[str]:
    """Every colour the label names, in reading order (a colour named twice counts once)."""
    s = _label(text)
    if not s:
        return []
    for n in NOT:
        s = s.replace(n, " ")
    bare = _SUFFIX.sub("", _EDGE.sub("", re.sub(r"[\U0001F000-\U0001FAFF☀-➿️]", "", s))).strip()
    found: list[tuple[int, str]] = []
    if bare in _TOKENS:
        found.append((0, _TOKENS[bare]))
    rest = s
    for w, k in _WORDS:
        i = rest.find(w)
        while i >= 0:
            found.append((i, k))
            rest = rest[:i] + "\x00" * len(w) + rest[i + len(w):]  # 「노란불」 is amber, not also yellow
            i = rest.find(w)
    out: list[str] = []
    for _i, k in sorted(found):
        if k not in out:
            out.append(k)
    return out


def key_of(text):
    ks = keys_in(text)
    return ks[0] if len(ks) == 1 else None


def color_of(text):
    """The colour this label names, as a hex; None when it names none or more than one."""
    k = key_of(text)
    return _HEX[k] if k else None


def _rgb(h: str):
    h = str(h).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        return (128, 128, 128)  # not a plain hex (a CSS variable): treated as a grey, never as a look-alike of a hue
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(h: str) -> float:
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def on(fill: str) -> str:
    """Text colour on a fill of this colour (white when it reads, else near-black)."""
    cw, cb = contrast("#ffffff", fill), contrast("#111111", fill)
    return "#ffffff" if (cw >= 4.0 or cw > cb) else "#111111"


def _hue(h: str):
    r, g, b = (v / 255.0 for v in _rgb(h))
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d < 0.12:
        return None  # a grey has no hue
    if mx == r:
        x = ((g - b) / d) % 6
    elif mx == g:
        x = (b - r) / d + 2
    else:
        x = (r - g) / d + 4
    return x * 60.0


def alike(a: str, b: str) -> bool:
    """Two fills a child would call the same colour (hues within 40 degrees, or two greys)."""
    ha, hb = _hue(a), _hue(b)
    if ha is None or hb is None:
        return ha is None and hb is None and abs(_lum(a) - _lum(b)) < 0.25
    d = abs(ha - hb) % 360
    return min(d, 360 - d) < 40


def pair_key(text):
    """'green' / 'red' when a short label is one side of a safe / danger pair (used only when both sides are on the screen)."""
    s = _label(text)
    hit = [k for k, ws in PAIRS if any(w in s for w in ws)] if s else []
    return hit[0] if len(hit) == 1 else None


def named(labels) -> list:
    """The colour each label names (hex or None): a colour word, else its side of a safe / danger pair when both sides are present."""
    out = [color_of(x) for x in labels]
    pk = [None if out[i] else pair_key(x) for i, x in enumerate(labels)]
    if len({k for k in pk if k}) >= 2:
        out = [c or (_HEX[pk[i]] if pk[i] else None) for i, c in enumerate(out)]
    return out


def assign(labels, tones, start: int = 0) -> list:
    """One colour per label. A label that names a colour gets it; the others take the rotation (tones[(start + i) % n]) but never a
    colour that looks like a named one on the same screen (the next free tone, else a neutral grey). Unchanged when nothing is named."""
    tones = list(tones) or ["#666666"]
    nm = named(labels)
    if not any(nm):
        return [tones[(start + i) % len(tones)] for i in range(len(nm))]
    taken = [c for c in nm if c]
    out = []
    for i, c in enumerate(nm):
        if c:
            out.append(c)
            continue
        pick = None
        for j in range(len(tones)):
            t = tones[(start + i + j) % len(tones)]
            if not any(alike(t, m) for m in taken):
                pick = t
                break
        out.append(pick or "#6B7280")
    return out


def any_named(labels) -> bool:
    return any(named(list(labels)))


def js() -> str:
    """The same table for pages that colour things while they run (sort bins, team chips): window.TSMeaning. ES2017, no lookbehind."""
    data = {"hex": _HEX, "words": [[w, k] for w, k in _WORDS], "tokens": _TOKENS, "not": NOT, "max": MAX_LEN, "pairs": PAIRS}
    return ("/* TS:MEANING colour words -> their own colour (shared/design/meaning.py) */\n(function(){var D=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
            r"""
function label(t){var s=String(t==null?"":t).replace(/\*\*|__|`/g,"").trim();if(s.length>D.max){s=s.split(/[:：,，.。!?()（）\n]| - | – | — /)[0].trim();}return s.length<=D.max?s:"";}
function keys(t){var s=label(t),out=[],found=[],i,j,k;if(!s)return out;
for(i=0;i<D.not.length;i++){s=s.split(D.not[i]).join(" ");}
var bare=s.replace(/[☀-➿️]|[\uD83C-\uD83E][\uDC00-\uDFFF]/g,"").replace(/^[\s!-\/:-@\[-`{-~·•]+|[\s!-\/:-@\[-`{-~·•]+$/g,"").replace(/\s*(?:팀|모둠|조|반|색|메달|불|편|군)$/,"").trim();
if(Object.prototype.hasOwnProperty.call(D.tokens,bare))found.push([0,D.tokens[bare]]);
var rest=s;for(i=0;i<D.words.length;i++){var w=D.words[i][0];j=rest.indexOf(w);while(j>=0){found.push([j,D.words[i][1]]);k=new Array(w.length+1).join("\u0000");rest=rest.slice(0,j)+k+rest.slice(j+w.length);j=rest.indexOf(w);}}
found.sort(function(a,b){return a[0]-b[0];});for(i=0;i<found.length;i++){if(out.indexOf(found[i][1])<0)out.push(found[i][1]);}return out;}
function color(t){var k=keys(t);return k.length===1?D.hex[k[0]]:null;}
function rgb(h){h=String(h).replace("#","");if(h.length===3)h=h.charAt(0)+h.charAt(0)+h.charAt(1)+h.charAt(1)+h.charAt(2)+h.charAt(2);if(!/^[0-9a-fA-F]{6}$/.test(h))return [128,128,128];return [parseInt(h.substr(0,2),16),parseInt(h.substr(2,2),16),parseInt(h.substr(4,2),16)];}
function lum(h){var c=rgb(h).map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2];}
function contrast(a,b){var la=lum(a),lb=lum(b);return (Math.max(la,lb)+0.05)/(Math.min(la,lb)+0.05);}
function on(f){var cw=contrast("#ffffff",f),cb=contrast("#111111",f);return (cw>=4||cw>cb)?"#ffffff":"#111111";}
function hue(h){var c=rgb(h),r=c[0]/255,g=c[1]/255,b=c[2]/255,mx=Math.max(r,g,b),mn=Math.min(r,g,b),d=mx-mn,x;if(d<0.12)return null;
if(mx===r)x=(((g-b)/d)%6+6)%6;else if(mx===g)x=(b-r)/d+2;else x=(r-g)/d+4;return x*60;}
function alike(a,b){var ha=hue(a),hb=hue(b);if(ha===null||hb===null)return ha===null&&hb===null&&Math.abs(lum(a)-lum(b))<0.25;var d=Math.abs(ha-hb)%360;return Math.min(d,360-d)<40;}
function pairKey(t){var s=label(t),hit=[];if(!s)return null;D.pairs.forEach(function(p){if(p[1].some(function(w){return s.indexOf(w)>=0;}))hit.push(p[0]);});return hit.length===1?hit[0]:null;}
function namedAll(labels){var out=labels.map(color),pk=labels.map(function(x,i){return out[i]?null:pairKey(x);}),ks=pk.filter(Boolean).filter(function(k,i,a){return a.indexOf(k)===i;});
if(ks.length>=2)out=out.map(function(c,i){return c||(pk[i]?D.hex[pk[i]]:null);});return out;}
function assign(labels,tones,start){tones=(tones&&tones.length)?tones:["#666666"];start=start||0;var named=namedAll(labels),taken=named.filter(Boolean),any=taken.length>0;
return named.map(function(c,i){if(c)return c;if(!any)return tones[(start+i)%tones.length];for(var j=0;j<tones.length;j++){var t=tones[(start+i+j)%tones.length];if(!taken.some(function(m){return alike(t,m);}))return t;}return "#6B7280";});}
window.TSMeaning={color:color,keys:keys,assign:assign,on:on};})();
""")


if __name__ == "__main__":
    import sys
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    for a in sys.argv[1:]:
        print(a, "->", key_of(a), color_of(a))
