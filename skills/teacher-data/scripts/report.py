#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Build a one-file offline HTML report from aggregates.json (made by analyze.py): conclusion first, 3 lines, then charts.

    python3 report.py --agg agg.json --out report.html [--audience 초등|학부모|선생님|전문가] [--xlsx out.xlsx] [--csv out.csv] [--palette name] [--yes]

Chart.js comes from shared/vendor (inlined), Korean fonts from shared/fonts (embedded when fonttools is available), colours from shared/design.
Bar for comparing, line for change over time, pie only for <= 5 parts. Numbers are rounded and always carry their unit.
The AI may override the wording with "narrative": {"headline": "...", "summary": ["...", "...", "..."]} in the plan
(check_report.py still verifies every number against the aggregates).
"""
from __future__ import annotations

import argparse
import html as H
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tdata  # noqa: E402
from tdata import fmt_num, josa  # noqa: E402

import design  # noqa: E402  (shared/design, read only)

SHARED = tdata.SHARED
CHART_JS = SHARED / "vendor" / "chartjs" / "chart-4.6.1.umd.min.js"
AUDIENCES = ("초등", "학부모", "선생님", "전문가")
PALETTE_BY_AUD = {"초등": "sky-fresh", "학부모": "linen-soft", "선생님": "mint-study", "전문가": "clean-white"}
BASE_PX = {"초등": 20, "학부모": 18, "선생님": 17, "전문가": 16}
CATEGORICAL = ["#2563eb", "#b45309", "#15803d", "#7e22ce", "#be185d", "#0f766e", "#52525b"]
HARD_WORDS = ["표준편차", "유의", "가설", "분산", "중앙값", "귀무", "상관계수", "인과", "신뢰구간", "회귀", "효과크기", "p값"]


# ---------- colour helpers ----------
def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _to_hex(r, g, b) -> str:
    return "#%02x%02x%02x" % (max(0, min(255, round(r))), max(0, min(255, round(g))), max(0, min(255, round(b))))


def _mix(a: str, b: str, t: float) -> str:
    ra, rb = _hex(a), _hex(b)
    return _to_hex(*(x + (y - x) * t for x, y in zip(ra, rb)))


def _ensure(color: str, bg: str, ratio: float) -> str:
    """Nudge `color` toward black or white until it reaches `ratio` against `bg`."""
    target = "#000000" if design._lum(bg) > 0.4 else "#ffffff"
    c = color
    for k in range(1, 21):
        if design.contrast(c, bg) >= ratio:
            return c
        c = _mix(color, target, k / 20)
    return c


def theme(aud: str, palette: str | None) -> dict:
    pal = design.load()["palettes"][palette or PALETTE_BY_AUD[aud]]
    bg, card, ink = pal["bg1"], pal["card"], pal["text"]
    muted = _ensure(_mix(ink, card, 0.38), card, 4.8)
    muted = _ensure(muted, bg, 4.8)
    brand = _ensure(pal["primary"], card, 4.5)
    return {"bg": bg, "card": card, "ink": ink, "muted": muted, "brand": brand, "on_brand": pal["btnText"] if design.contrast(pal["btnText"], brand) >= 4.5 else "#ffffff",
            "line": _mix(ink, card, 0.82), "name": pal.get("name", palette or PALETTE_BY_AUD[aud])}


# ---------- wording ----------
def _u(v, unit):
    return fmt_num(v, unit)


def _metric(r: dict) -> str:
    return r.get("metric") or r["facts"].get("value") or "개수"


def _strip_hard(s: str, aud: str) -> str:
    if aud in ("초등", "학부모"):
        s = s.replace(" (상관관계 ≠ 인과관계)", "")
    return s


def texts(r: dict, aud: str) -> dict:
    """headline / bullets / emoji for one analysis result, in the audience's voice. Every number comes from r['facts']."""
    f, unit, kid = r["facts"], r.get("unit", ""), aud == "초등"
    t = r["type"]
    b: list[str] = []
    emoji = ""
    if t == "groupby":
        top, bot, agg = f["top_label"], f["bottom_label"], f["agg"]
        if agg == "mean":
            head = (f"{josa(top, '이/가')} 평균 {josa(_u(f['top_value'], unit), '으로/로')} 가장 높아요" if kid else
                    f"{top}의 {_metric(r)} 평균이 {josa(_u(f['top_value'], unit), '으로/로')} 가장 높습니다")
            emoji = "🥇"
            b.append(f"가장 낮은 곳은 {bot}, {_u(f['bottom_value'], unit)}이에요. 두 곳 차이는 {_u(f['gap'], unit)}예요." if kid else
                     f"가장 낮은 곳은 {bot}({_u(f['bottom_value'], unit)})이며, 차이는 {_u(f['gap'], unit)}입니다.")
            ts = f.get("test")
            if ts and ts.get("done"):
                if ts["significant"]:
                    b.append("이 차이는 우연으로 보기엔 꽤 커요." if kid else "이 차이는 우연이라고 보기 어려운 수준입니다." + (f" (p = {ts['p']})" if aud == "전문가" else ""))
                else:
                    b.append("차이가 아주 크지는 않아서, 서로 비슷하다고 봐도 돼요." if kid else "통계적으로 뚜렷한 차이는 아닙니다." + (f" (p = {ts['p']})" if aud == "전문가" else ""))
            b.append(f"자료는 모두 {f['n']}개를 썼어요.")
        else:
            m = _metric(r)
            head = f"{josa(top, '이/가')} {josa(_u(f['top_value'], unit), '으로/로')} 가장 " + ("많아요" if kid else "많습니다")
            emoji = "💰" if unit == "원" else "🥇"
            if f.get("top_share_pct") is not None:
                b.append(f"{josa(top, '은/는')} 전체의 {fmt_num(f['top_share_pct'], '%')}를 차지해요." if kid else f"{top} 비중은 전체의 {fmt_num(f['top_share_pct'], '%')}입니다.")
            b.append(f"가장 적은 곳은 {bot}, {_u(f['bottom_value'], unit)}이에요.")
            if f.get("total") is not None:
                b.append(f"모두 합치면 {_u(f['total'], unit)}이에요.")
    elif t == "change":
        d, foc = f["focus_diff"], f["focus"]
        prev = "지난달" if f["consecutive"] else f["from_label"]
        word, emoji = (("올랐어요", "📈") if d > 0.5 else ("내려갔어요", "📉") if d < -0.5 else ("비슷해요", "➖"))
        if kid:
            head = f"{foc} 평균이 {prev}보다 {_u(abs(d), unit)} {word}" if word != "비슷해요" else f"{foc} 평균은 {prev}와 비슷해요"
        else:
            vb = {"올랐어요": "올랐습니다", "내려갔어요": "내려갔습니다", "비슷해요": "비슷합니다"}[word]
            head = f"{foc}의 {f['value']} 평균이 {prev}보다 {_u(abs(d), unit)} {vb}" if word != "비슷해요" else f"{foc}의 {f['value']} 평균은 {prev}와 비슷합니다"
        b.append(f"{foc}: {f['from_label']} {_u(f['focus_from'], unit)} → {f['to_label']} {_u(f['focus_to'], unit)}")
        others = [f"{g} {'+' if v >= 0 else '-'}{fmt_num(abs(v), unit)}" for g, v in f["diffs"].items() if g != foc]
        if others:
            b.append("다른 곳은 " + ", ".join(others) + ("이에요." if kid else "입니다."))
        b.append(f"전체 평균은 {_u(f['overall_from'], unit)}에서 {_u(f['overall_to'], unit)}로 {'바뀌었어요' if kid else '바뀌었습니다'}.")
    elif t == "trend":
        m = _metric(r)
        lv = f["last_vs_prev"]
        if lv is not None:
            word, emoji = (("늘었어요", "📈") if lv > 0 else ("줄었어요", "📉") if lv < 0 else ("같아요", "➖"))
            if not kid:
                word = {"늘었어요": "늘었습니다", "줄었어요": "줄었습니다", "같아요": "같습니다"}[word]
            head = f"{f['last_label']} {josa(m, '은/는')} {_u(f['last'], unit)}으로, {f['prev_label']}보다 {_u(abs(lv), unit)} {word}" if unit == "원" else \
                   f"{f['last_label']} {josa(m, '은/는')} {josa(_u(f['last'], unit), '으로/로')}, {f['prev_label']}보다 {_u(abs(lv), unit)} {word}"
        else:
            head = f"{f['last_label']} {josa(m, '은/는')} {_u(f['last'], unit)}{'이에요' if kid else '입니다'}"
        b.append(f"가장 컸던 때는 {f['peak_label']}({_u(f['peak'], unit)})이에요." if kid else f"가장 컸던 때는 {f['peak_label']}({_u(f['peak'], unit)})입니다.")
        if f.get("total") is not None:
            b.append(f"{f['periods']}번을 모두 합치면 {_u(f['total'], unit)}이에요." if kid else f"{f['periods']}개 기간을 합치면 {_u(f['total'], unit)}입니다.")
        b.append(f"한 번 평균은 {_u(f['average'], unit)}이에요." if kid else f"기간 평균은 {_u(f['average'], unit)}입니다.")
    elif t == "distribution":
        top = f["top_label"] + ("점" if f["top_label"].isdigit() else "")
        head = (f"{josa(top, '이/가')} 전체의 {fmt_num(f['top_pct'], '%')}로 가장 많아요" if kid else
                f"{josa(top, '이/가')} 전체의 {fmt_num(f['top_pct'], '%')}로 가장 많습니다")
        emoji = "🙂"
        b.append(f"{josa(top, '은/는')} {f['top_count']}명이에요." if kid else f"{top} 응답은 {f['top_count']}명입니다.")
        if f.get("positive_pct") is not None:
            b.append(f"{f['scale_max'] - 1}점 이상을 준 사람은 {fmt_num(f['positive_pct'], '%')}예요.")
        if f.get("mean") is not None:
            b.append(f"평균은 {_u(f['mean'], '점')}이에요.")
        b.append(f"모두 {f['n']}명의 답이에요." if kid else f"응답자는 모두 {f['n']}명입니다.")
    elif t == "likert":
        head = (f"{josa(f['best_label'], '이/가')} 평균 {josa(_u(f['best_mean'], '점'), '으로/로')} 가장 높아요" if kid else
                f"{josa(f['best_label'], '은/는')} 평균 {josa(_u(f['best_mean'], '점'), '으로/로')} 가장 높게 나왔습니다")
        emoji = "😊"
        b.append(f"가장 낮은 것은 {f['worst_label']}, {_u(f['worst_mean'], '점')}이에요." if kid else f"가장 낮은 항목은 {f['worst_label']}({_u(f['worst_mean'], '점')})입니다.")
        b.append(f"{f['scale_max']}점 만점에 전체 평균은 {_u(f['overall'], '점')}이에요. {fmt_num(f['positive_overall_pct'], '%')}가 {f['scale_max'] - 1}점 이상을 줬어요." if kid else
                 f"{f['scale_max']}점 만점에 전체 평균 {_u(f['overall'], '점')}, {f['scale_max'] - 1}점 이상 응답은 {fmt_num(f['positive_overall_pct'], '%')}입니다.")
        b.append(f"응답은 {f['n']}명이에요." if kid else f"응답자는 {f['n']}명입니다.")
    elif t == "crosstab":
        head = f"{f['top_row']}에서 '{f['focus_col']}' 비율이 {fmt_num(f['top_pct'], '%')}로 가장 높아요" if kid else \
               f"{f['top_row']}에서 '{f['focus_col']}' 비율이 {fmt_num(f['top_pct'], '%')}로 가장 높습니다"
        emoji = "📊"
        b.append(f"가장 낮은 곳은 {f['low_row']}({fmt_num(f['low_pct'], '%')})예요." if kid else f"가장 낮은 곳은 {f['low_row']}({fmt_num(f['low_pct'], '%')})입니다.")
        b.append(f"전체에서는 {fmt_num(f['overall_pct'], '%')}예요. 응답은 {f['n']}명이에요.")
    else:  # correlation
        s, rr = f["strength"], f["r"]
        up = rr > 0
        tail = {"거의 없음": "관계가 거의 없어요", "약함": "관계가 약해요", "보통": "관계가 보통이에요", "강함": "관계가 뚜렷해요"}[s]
        if s == "거의 없음":
            head = f"{josa(f['x'], '과/와')} {f['y']} 사이에는 {tail}" if kid else f"{josa(f['x'], '과/와')} {f['y']} 사이의 관계는 거의 없습니다"
        else:
            head = (f"{josa(f['x'], '이/가')} 늘수록 {f['y']}도 {'오르는' if up else '내려가는'} 편이고, {tail}" if kid else
                    f"{josa(f['x'], '이/가')} 늘수록 {josa(f['y'], '은/는')} {'높아지는' if up else '낮아지는'} 경향이 있습니다 ({s})")
        emoji = "🔍"
        b.append(f"{f['x']} 구간 중 가장 낮은 쪽은 {_u(f['first_mean'], f['y_unit'])}, 가장 높은 쪽은 {_u(f['last_mean'], f['y_unit'])}이에요." if kid else
                 f"가장 낮은 구간 평균 {_u(f['first_mean'], f['y_unit'])}, 가장 높은 구간 평균 {_u(f['last_mean'], f['y_unit'])}입니다.")
        if aud in ("선생님", "전문가"):
            b.append(f"상관계수 r = {fmt_num(f['r'])}" + (f", p = {f['p']}" if aud == "전문가" else "") + f" (자료 {f['n']}개)")
        b.append("함께 움직인다고 해서 하나가 다른 하나의 원인이라는 뜻은 아니에요." if kid else
                 "함께 움직인다고 해서 한쪽이 다른 쪽의 원인이라는 뜻은 아닙니다.")
    head = H.unescape(head)
    return {"headline": head, "emoji": emoji, "bullets": b, "how": r.get("how", "")}


def pick_chart(r: dict) -> str:
    c = r.get("chart", "bar")
    if c == "share" and len(r["labels"]) > 5:
        return "bar"
    if c == "line" and len(r["labels"]) < 2:
        return "bar"
    return c


def build_story(agg: dict, aud: str) -> dict:
    res = agg["results"]
    tx = [texts(r, aud) for r in res]
    hi = 0
    if agg.get("headline_of"):
        hi = next((i for i, r in enumerate(res) if r["id"] == agg["headline_of"]), 0)
    nar = agg.get("narrative") or {}
    headline = nar.get("headline") or (tx[hi]["headline"] + (" " + tx[hi]["emoji"] if tx[hi]["emoji"] else ""))
    lines = list(nar.get("summary") or [])
    if not lines:
        for i, x in enumerate(tx):
            lines.append(x["bullets"][0] if i == hi else x["headline"])
        for x in tx:
            for bl in x["bullets"][1:]:
                if len(lines) >= 3:
                    break
                lines.append(bl)
    lines = lines[:3]
    return {"headline": headline, "summary": lines, "tx": tx}


# ---------- html ----------
CSS = """
:root{--bg:%(bg)s;--card:%(card)s;--ink:%(ink)s;--muted:%(muted)s;--brand:%(brand)s;--on-brand:%(on_brand)s;--line:%(line)s;--base:%(px)dpx}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Sans KR","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;font-size:var(--base);line-height:1.65;word-break:keep-all;overflow-wrap:break-word}
.wrap{max-width:980px;margin:0 auto;padding:24px 16px 56px}
header.top{padding:8px 4px 20px}
h1{font-size:calc(var(--base)*1.55);line-height:1.3;margin:0 0 6px;font-weight:800}
.meta{font-size:14px;color:var(--muted);margin:0}
.hero{background:var(--brand);color:var(--on-brand);border-radius:24px;padding:28px 28px 30px;margin:8px 0 20px}
.hero .kicker{font-size:15px;font-weight:700;letter-spacing:.02em;opacity:1;margin:0 0 8px}
.hero .headline{font-size:calc(var(--base)*1.75);line-height:1.4;font-weight:800;margin:0}
.card{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:22px 24px;margin:0 0 20px}
.card h2{font-size:calc(var(--base)*1.2);margin:0 0 8px;line-height:1.4;font-weight:800}
.summary ol{margin:0;padding-left:1.5em}
.summary li{margin:6px 0}
.how{margin:0 0 12px;color:var(--muted);font-size:calc(var(--base)*.9)}
.chartbox{position:relative;width:100%%}
figure{margin:0}
.facts{margin:14px 0 0;padding-left:1.3em}
.facts li{margin:4px 0}
.note{margin:12px 0 0;padding:10px 14px;border-left:4px solid var(--brand);background:rgba(127,127,127,.08);border-radius:8px;font-size:calc(var(--base)*.9)}
details{margin-top:12px}
summary{cursor:pointer;font-weight:700;color:var(--ink);padding:8px 0;min-height:44px}
table{border-collapse:collapse;width:100%%;font-size:calc(var(--base)*.9)}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}
th{font-weight:700;background:rgba(127,127,127,.08)}
.tablewrap{overflow-x:auto}
footer{font-size:14px;color:var(--muted);padding:8px 4px}
@media(max-width:600px){.hero{padding:22px 18px}.card{padding:18px 16px}.hero .headline{font-size:calc(var(--base)*1.45)}}
@media print{body{background:#fff}.hero{-webkit-print-color-adjust:exact;print-color-adjust:exact}.card{break-inside:avoid}}
"""

JS = r"""
(function(){
var D=JSON.parse(document.getElementById('ts-data').textContent);
var css=getComputedStyle(document.documentElement);
var INK=css.getPropertyValue('--ink').trim(),LINE=css.getPropertyValue('--line').trim();
var FAM='"Noto Sans KR","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif';
var FS=D.fontSize;
var reduce=false;try{reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(e){}
function fmt(v){if(v===null||v===undefined)return '';var a=Math.abs(v);var d=(a>=1000||Math.round(v)===v)?0:(a>=1?1:2);return v.toLocaleString('ko-KR',{maximumFractionDigits:d});}
function lum(h){var n=parseInt(h.slice(1),16),r=(n>>16)&255,g=(n>>8)&255,b=n&255;return 0.299*r+0.587*g+0.114*b;}
var labelsPlugin={id:'tsLabels',afterDatasetsDraw:function(ch){
 var ctx=ch.ctx,t=ch.config.type,o=ch.options.tsKind;
 ctx.save();ctx.font='700 '+FS+'px '+FAM;ctx.textBaseline='middle';
 ch.data.datasets.forEach(function(ds,di){
  var meta=ch.getDatasetMeta(di);if(meta.hidden)return;
  meta.data.forEach(function(el,i){
   var v=ds.data[i];if(v===null||v===undefined)return;
   var p=el.tooltipPosition();
   if(t==='pie'){
     var tot=ds.data.reduce(function(a,b){return a+b;},0),pc=100*v/tot;if(pc<6)return;
     ctx.fillStyle=lum(ds.backgroundColor[i])>150?'#111':'#fff';ctx.textAlign='center';
     var m=(el.startAngle+el.endAngle)/2,rr=(el.innerRadius+el.outerRadius)/2;
     ctx.fillText(fmt(Math.round(pc*10)/10)+'%',el.x+Math.cos(m)*rr*0.95,el.y+Math.sin(m)*rr*0.95);return;}
   if(o==='stacked'){if(v<7)return;ctx.fillStyle=lum(ds.backgroundColor)>150?'#111':'#fff';ctx.textAlign='center';
     ctx.fillText(fmt(v)+'%',(el.x+el.base)/2,el.y);return;}
   if(o==='hbar'){ctx.fillStyle=INK;ctx.textAlign='left';ctx.fillText(fmt(v),el.x+8,el.y);return;}
   if(o==='line'){ctx.fillStyle=INK;var last=ds.data.length-1;ctx.textAlign=i===0?'left':(i===last?'right':'center');ctx.fillText(fmt(v),i===0?el.x-4:(i===last?el.x+4:el.x),el.y-18);return;}
   ctx.fillStyle=INK;ctx.textAlign='center';ctx.fillText(fmt(v),el.x,el.y-14);
  });
 });ctx.restore();}};
function axisTitle(text){return {display:!!text,text:text,color:INK,font:{size:FS,weight:'700'}};}
function draw(){
 Chart.defaults.font.family=FAM;Chart.defaults.font.size=FS;Chart.defaults.color=INK;
 Chart.defaults.animation=reduce?false:{duration:450};
 D.charts.forEach(function(c){
  var cv=document.getElementById(c.id);if(!cv)return;
  var kind=c.kind,type=kind==='share'?'pie':(kind==='line'?'line':'bar');
  var ds=c.series.map(function(s,i){
   var col=c.colors[i%c.colors.length];
   if(kind==='share')return {label:s.name,data:s.values,backgroundColor:c.labels.map(function(_,j){return c.colors[j%c.colors.length];}),borderColor:'#fff',borderWidth:3};
   if(kind==='line')return {label:s.name,data:s.values,borderColor:col,backgroundColor:col,borderWidth:4,pointRadius:6,pointHoverRadius:8,tension:0,spanGaps:true};
   return {label:s.name,data:s.values,backgroundColor:col,borderRadius:6,maxBarThickness:kind==='hbar'?34:72};});
  var o={responsive:true,maintainAspectRatio:false,tsKind:kind,layout:{padding:{top:30,left:kind==='line'?10:0,right:kind==='hbar'?60:12}},plugins:{legend:{display:c.series.length>1||kind==='share',position:kind==='share'?'right':'top',labels:{font:{size:FS},boxWidth:18,boxHeight:18,
     generateLabels:kind==='share'?function(ch){var d=ch.data.datasets[0].data,tot=d.reduce(function(a,b){return a+b;},0);return ch.data.labels.map(function(l,i){return {text:l+' ('+fmt(Math.round(1000*d[i]/tot)/10)+'%)',fillStyle:ch.data.datasets[0].backgroundColor[i],strokeStyle:'#fff',index:i,fontColor:INK};});}:undefined}},tooltip:{enabled:true}}};
  if(kind!=='share'){
   var vAxis={beginAtZero:true,grace:kind==='line'?'18%':(c.axisMax?0:'12%'),grid:{color:LINE},ticks:{font:{size:FS},callback:function(v){return fmt(v);}},title:axisTitle(c.unit?('단위: '+c.unit):'')};
   if(kind==='stacked'){vAxis.max=100;}
   if(c.axisMax){vAxis.max=c.axisMax;}
   var cAxis={grid:{display:false},ticks:{font:{size:FS}},title:axisTitle(c.xlabel||'')};
   if(kind==='hbar'){o.indexAxis='y';o.scales={x:vAxis,y:cAxis};}
   else{o.scales={x:cAxis,y:vAxis};}
   if(kind==='stacked'){o.scales.x.stacked=true;o.scales.y.stacked=true;}
  }
  new Chart(cv.getContext('2d'),{type:type,data:{labels:c.labels,datasets:ds},options:o,plugins:[labelsPlugin]});
 });
 document.documentElement.setAttribute('data-charts-ready','1');
}
var done=false;function go(){if(done)return;done=true;draw();}
try{Promise.all([document.fonts.load('400 16px "Noto Sans KR"'),document.fonts.load('700 16px "Noto Sans KR"')]).then(go,go);setTimeout(go,1500);}catch(e){go();}
})();
"""


def _table_html(r: dict) -> str:
    cols, rows = r["table"]["columns"], r["table"]["rows"]
    th = "".join(f"<th scope='col'>{H.escape(str(c))}</th>" for c in cols)
    body = ""
    for row in rows:
        tds = "".join(f"<td>{H.escape(fmt_num(v) if isinstance(v, (int, float)) else str(v if v is not None else '-'))}</td>" for v in row)
        body += f"<tr>{tds}</tr>"
    return f"<div class='tablewrap'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>"


def _colors(kind: str, brand: str, card: str, n_series: int) -> list[str]:
    if kind == "grouped":
        base = ["#6b7280", brand]
    elif kind in ("bar", "hbar"):
        base = [brand]
    else:
        base = [brand] + [c for c in CATEGORICAL if sum((x - y) ** 2 for x, y in zip(_hex(c), _hex(brand))) > 110 ** 2]
    return [_ensure(c, card, 3.0) for c in base]


def build(agg: dict, aud: str | None = None, palette: str | None = None, embed_fonts: bool = True, consent: bool = False) -> tuple[str, dict]:
    aud = aud or agg.get("audience") or "학부모"
    if aud not in AUDIENCES:
        raise ValueError(f"audience must be one of {', '.join(AUDIENCES)}")
    th = theme(aud, palette)
    story = build_story(agg, aud)
    meta = agg["meta"]
    px = BASE_PX[aud]
    fs = 16 if aud == "초등" else 14
    charts, secs = [], []
    for i, (r, x) in enumerate(zip(agg["results"], story["tx"]), 1):
        kind = pick_chart(r)
        if kind == "bar" and len(r["labels"]) > 6:
            kind = "hbar"
        cid = f"chart{i}"
        cols = _colors(kind, th["brand"], th["card"], len(r["series"]))
        charts.append({"id": cid, "kind": kind, "labels": r["labels"], "series": r["series"], "unit": r.get("unit", ""), "xlabel": r.get("xlabel", ""),
                       "axisMax": r.get("axis_max"), "colors": cols})
        n = len(r["labels"])
        h = 380 if kind in ("bar", "line", "grouped", "stacked") else (max(260, n * 52 + 90) if kind == "hbar" else 360)
        alt = ", ".join(f"{l} {fmt_num(s['values'][j], r.get('unit', ''))}" for s in r["series"][:1] for j, l in enumerate(r["labels"]) if s["values"][j] is not None)
        notes = "".join(f"<p class='note'>{H.escape(_strip_hard(nt, aud))}</p>" for nt in r.get("notes", []))
        facts = "".join(f"<li>{H.escape(b)}</li>" for b in x["bullets"])
        secs.append(
            f"<section class='card chart' id='sec{i}'><h2>{H.escape(r['title'])}</h2><p class='how'>{H.escape(x['how'])}</p>"
            f"<figure data-unit='{H.escape(r.get('unit', ''))}' data-kind='{kind}'><div class='chartbox' style='height:{h}px'>"
            f"<canvas id='{cid}' role='img' aria-label='{H.escape(r['title'] + ': ' + alt)}'></canvas></div></figure>"
            f"<ul class='facts'>{facts}</ul>{notes}"
            f"<details><summary>숫자로 보기</summary>{_table_html(r)}</details></section>")
    summary = "".join(f"<li>{H.escape(s)}</li>" for s in story["summary"])
    privacy = ("학생 이름은 가명으로 바꿔서 분석했어요. " if "이름" in meta.get("pii_columns", []) else ("개인정보 칸은 가려서 분석했어요. " if meta.get("pseudonymized") else "")) + "이 보고서는 선생님 컴퓨터 안에서만 만들었고, 자료는 어디로도 보내지 않았어요."
    n_total = meta["rows"]
    sub = f"자료 {n_total:,}줄을 살펴봤어요"
    page = f"""<!doctype html>
<html lang="ko" data-audience="{aud}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(agg['title'])}</title>
<style>{CSS % {**th, 'px': px}}</style>
</head>
<body><div class="wrap">
<header class="top"><h1>{H.escape(agg['title'])}</h1><p class="meta">{H.escape(sub)}</p></header>
<main>
<section class="hero" id="conclusion"><p class="kicker">한 줄 결론</p><p class="headline">{H.escape(story['headline'])}</p></section>
<section class="card summary" id="summary"><h2>세 줄 요약</h2><ol>{summary}</ol></section>
{''.join(secs)}
</main>
<footer>{H.escape(privacy)}</footer>
</div>
<script id="ts-data" type="application/json">{json.dumps({'fontSize': fs, 'charts': charts}, ensure_ascii=False).replace('</', '<\\/')}</script>
<script id="chartjs">/* Chart.js 4.6.1, MIT, see NOTICE */
{CHART_JS.read_text(encoding='utf-8')}
</script>
<script id="ts-draw">{JS}</script>
</body></html>
"""
    rep = {"fonts": None}
    if embed_fonts:
        try:
            import embed
            page, rep["fonts"] = embed.embed(page, consent=consent)
        except Exception as e:  # fonts are a nicety, never a blocker
            rep["fonts"] = {"embedded": False, "reason": str(e)}
    return page, {"audience": aud, "palette": th["name"], "headline": story["headline"], "summary": story["summary"], "fonts": rep["fonts"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audience", choices=AUDIENCES)
    ap.add_argument("--palette")
    ap.add_argument("--xlsx")
    ap.add_argument("--csv")
    ap.add_argument("--no-fonts", action="store_true")
    ap.add_argument("--yes", action="store_true", help="install fonttools/openpyxl if missing")
    a = ap.parse_args()
    agg = json.loads(Path(a.agg).read_text(encoding="utf-8"))
    page, info = build(agg, a.audience, a.palette, not a.no_fonts, a.yes)
    Path(a.out).write_text(page, encoding="utf-8")
    print(f"OK {a.out} ({len(page) // 1024}KB) 대상={info['audience']} 색={info['palette']}")
    print("결론:", info["headline"])
    if info["fonts"] and not info["fonts"].get("embedded") and info["fonts"].get("prompt"):
        print("글꼴 안내:", info["fonts"]["prompt"])
    if a.xlsx or a.csv:
        import export
        try:
            export.write(agg, a.xlsx, a.csv, info["headline"], info["summary"], a.yes)
        except tdata.NeedInstall as e:
            print(json.dumps({"need_install": e.name, "prompt": e.prompt}, ensure_ascii=False))
            return 2
        for p in (a.xlsx, a.csv):
            if p:
                print("OK", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
