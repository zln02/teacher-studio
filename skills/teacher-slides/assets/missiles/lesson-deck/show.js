/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* lesson-deck — keynote-quality slide deck. One DOC.items entry = one slide.
   Every word comes from DOC (items + world). Skins change type, art, painter and transitions.
   Keys: → Space PageDown Enter = next build/slide · ← PageUp Backspace = back · Home/End · digits+Enter = jump
         N = teacher notes · B or . = blackout · tap right/left half · swipe.            */
(function(){
"use strict";
var S = window.STAGE, D = window.DOC || {}, W = 1920, H = 1080;
var WORLD = D.world || {};
var SKIN_NAME = D.skin || "clean-keynote";
var ITEMS = (D.items || []).filter(function(x){ return x && typeof x === "object"; });
var esc = S.esc;

/* ---------- small utils ---------- */
function q(el, s){ return el ? el.querySelector(s) : null; }
function qa(el, s){ return el ? Array.prototype.slice.call(el.querySelectorAll(s)) : []; }
function arr(x){ return Array.isArray(x) ? x : (x == null || x === "" ? [] : [x]); }
function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }
function txt(v){ return v == null ? "" : String(v); }
function plain(s){ return txt(s).split("**").join(""); }
function rng(seed){ var s = seed >>> 0; return function(){ s = (s + 0x6D2B79F5) | 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function hash(str){ var h = 2166136261; str = txt(str); for (var i = 0; i < str.length; i++){ h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
function label(key, fallback){ var L = WORLD.labels || {}; return L[key] != null ? txt(L[key]) : fallback; }
function cssVar(name, fb){ var v = getComputedStyle(document.documentElement).getPropertyValue("--" + name); return (v && v.trim()) || fb; }

/* ---------- rich text: **keyword** marks, words kept whole (Korean-safe, like STAGE.split) ---------- */
var CHARS = SKIN_NAME === "chalkboard";
function tokens(text){
  var out = [], word = [], kw = false, buf = "", src = txt(text);
  function run(){ if (buf){ word.push({s:buf, kw:kw}); buf = ""; } }
  function push(){ run(); if (word.length){ out.push(word); word = []; } }
  for (var i = 0; i < src.length; i++){
    var c = src.charAt(i);
    if (c === "*" && src.charAt(i + 1) === "*"){ run(); kw = !kw; i++; continue; }
    if (c === "\n"){ push(); out.push("br"); continue; }
    if (/\s/.test(c)){ push(); continue; }
    buf += c;
  }
  push();
  return out;
}
function rt(text){
  return tokens(text).map(function(w){
    if (w === "br") return "<br>";
    return '<span class="w"><span class="wi">' + w.map(function(r){
      var inner = CHARS ? Array.from(r.s).map(function(c){ return '<span class="ch">' + esc(c) + "</span>"; }).join("") : esc(r.s);
      return r.kw ? '<span class="kw">' + inner + "</span>" : inner;
    }).join("") + "</span></span>";
  }).join(" ");
}

/* ---------- icon set (64 grid, one stroke style, duotone fill) ---------- */
function cP(cx, cy, r){ return "M" + (cx - r) + " " + cy + "a" + r + " " + r + " 0 1 0 " + (2 * r) + " 0a" + r + " " + r + " 0 1 0 " + (-2 * r) + " 0"; }
function eP(cx, cy, rx, ry){ return "M" + (cx - rx) + " " + cy + "a" + rx + " " + ry + " 0 1 0 " + (2 * rx) + " 0a" + rx + " " + ry + " 0 1 0 " + (-2 * rx) + " 0"; }
function rP(x, y, w, h, r){ return "M" + (x + r) + " " + y + "h" + (w - 2 * r) + "a" + r + " " + r + " 0 0 1 " + r + " " + r + "v" + (h - 2 * r) + "a" + r + " " + r + " 0 0 1 " + (-r) + " " + r + "h" + (-(w - 2 * r)) + "a" + r + " " + r + " 0 0 1 " + (-r) + " " + (-r) + "v" + (-(h - 2 * r)) + "a" + r + " " + r + " 0 0 1 " + r + " " + (-r) + "z"; }
function hexP(cx, cy, r){ var p = []; for (var k = 0; k < 6; k++){ var a = Math.PI / 180 * (60 * k - 90); p.push((cx + r * Math.cos(a)).toFixed(1) + " " + (cy + r * Math.sin(a)).toFixed(1)); } return "M" + p.join("L") + "z"; }
var HEX = [[22.5,15],[41.5,15],[13,31.5],[32,31.5],[51,31.5],[22.5,48],[41.5,48]];
var ICONS = {
  flask:{s:["M24 6h16","M28 6v18L13 50a6 6 0 0 0 5.2 9h27.6a6 6 0 0 0 5.2-9L36 24V6","M20.5 40h23"], f:["M20.5 40h23l6.6 11.5A4 4 0 0 1 46.6 58H17.4a4 4 0 0 1-3.5-6.5z"], d:[cP(28,49,2.2),cP(37,52,1.6)]},
  book:{s:["M32 17C25 11 16 10 7 12v39c9-2 18-1 25 5 7-6 16-7 25-5V12c-9-2-18-1-25 5z","M32 17v39","M14 22c4-1 8-1 12 1","M14 30c4-1 8-1 12 1","M38 23c4-2 8-2 12-1"], f:["M32 17C25 11 16 10 7 12v39c9-2 18-1 25 5z"]},
  globe:{s:[cP(32,32,24),"M32 8c-7 7-10.5 15-10.5 24S25 49 32 56c7-7 10.5-15 10.5-24S39 15 32 8z","M9.5 24h45","M9.5 40h45"], f:[cP(32,32,24)]},
  lightbulb:{s:["M23 44c0-5-9-9-9-20a18 18 0 0 1 36 0c0 11-9 15-9 20z","M24 50h16","M27 56h10","M27 36l-2-8 7 4 7-4-2 8"], f:["M23 44c0-5-9-9-9-20a18 18 0 0 1 36 0c0 11-9 15-9 20z"]},
  chart:{s:["M8 8v48h48",rP(16,34,8,16,2),rP(30,24,8,26,2),rP(44,14,8,36,2)], f:[rP(16,34,8,16,2),rP(30,24,8,26,2),rP(44,14,8,36,2)]},
  people:{s:[cP(23,22,8),cP(44,25,6.5),"M8 54c0-9.4 6.7-17 15-17s15 7.6 15 17","M36.5 40.5c2.2-1.6 4.8-2.5 7.5-2.5 6.6 0 12 5.6 12 14"], f:[cP(23,22,8)]},
  school:{s:["M6 56h52","M12 56V30l20-12 20 12v26","M32 18V7l11 4-11 4","M26 56V44h12v12",cP(32,32,4.5),"M17 38h5","M42 38h5"], f:["M12 30l20-12 20 12v26H12z"]},
  robot:{s:[rP(13,20,38,30,9),"M32 20v-8",cP(32,9,3),"M9 31v10","M55 31v10","M25 43h14",cP(25,33,3.5),cP(39,33,3.5),"M22 50v6h20v-6"], f:[rP(13,20,38,30,9)]},
  calendar:{s:[rP(8,12,48,44,7),"M8 25h48","M21 6v12","M43 6v12","M18 35h6","M29 35h6","M40 35h6","M18 45h6","M29 45h6"], f:[rP(38,40,10,10,2)]},
  check:{s:[cP(32,32,24),"M20.5 33l8 8 15.5-16.5"], f:[cP(32,32,24)]},
  star:{s:["M32 7l7.6 15.6 17.2 2.5-12.4 12.1 2.9 17.1L32 46.2l-15.3 8.1 2.9-17.1L7.2 25.1l17.2-2.5z"], f:["M32 7l7.6 15.6 17.2 2.5-12.4 12.1 2.9 17.1L32 46.2l-15.3 8.1 2.9-17.1L7.2 25.1l17.2-2.5z"]},
  heart:{s:["M32 55S7 41 7 23.5A12.5 12.5 0 0 1 32 18a12.5 12.5 0 0 1 25 5.5C57 41 32 55 32 55z"], f:["M32 55S7 41 7 23.5A12.5 12.5 0 0 1 32 18a12.5 12.5 0 0 1 25 5.5C57 41 32 55 32 55z"]},
  music:{s:["M24 46V15l28-7v31","M24 23l28-7",cP(17.5,46,6.5),cP(45.5,39,6.5)], f:[cP(17.5,46,6.5),cP(45.5,39,6.5)]},
  leaf:{s:["M11 53C11 27 27 11 54 10c0 27-16 43-43 43z","M11 53L40 24","M23 41h11","M30 34v-10"], f:["M11 53C11 27 27 11 54 10c0 27-16 43-43 43z"]},
  atom:{s:[[eP(32,32,25,9.5)],[eP(32,32,25,9.5),"rotate(60 32 32)"],[eP(32,32,25,9.5),"rotate(120 32 32)"]], f:[cP(32,32,5)], d:[cP(32,32,3)]},
  cell:{s:["M32 7c14.5 0 25 10 25 24.5S46 57 31 57 7 47 7 32 17.5 7 32 7z",cP(29,30,9),"M42 44c2.2-2.5 6.5-1.5 6.5 1.5s-4.3 4-6.5 1.5","M15 41c1.5-2 4.5-1.5 4.5 1","M44 17c2 0 4 1.5 4 3.5"], f:[cP(29,30,9)]},
  tissue:{s:HEX.map(function(c){ return hexP(c[0], c[1], 10.2); }), f:[hexP(32,31.5,10.2)], d:HEX.map(function(c){ return cP(c[0], c[1], 2.2); })},
  person:{s:[cP(32,19,10),"M12 57c0-11.6 9-21 20-21s20 9.4 20 21"], f:[cP(32,19,10)]},
  microscope:{s:["M25 8l10 5.5-9 16.5-10-5.5z","M30 29l3 2","M37 24a15 15 0 0 1-5 26","M10 57h44","M22 50h20","M16 40h16"], f:["M25 8l10 5.5-9 16.5-10-5.5z"]},
  chat:{s:["M14 12h36a8 8 0 0 1 8 8v18a8 8 0 0 1-8 8H30L18 56V46h-4a8 8 0 0 1-8-8V20a8 8 0 0 1 8-8z"], f:["M14 12h36a8 8 0 0 1 8 8v18a8 8 0 0 1-8 8H30L18 56V46h-4a8 8 0 0 1-8-8V20a8 8 0 0 1 8-8z"], d:[cP(21,29,3),cP(32,29,3),cP(43,29,3)]},
  target:{s:[cP(30,34,22),cP(30,34,13),"M30 34L52 12","M45 11h8v8"], f:[cP(30,34,22)], d:[cP(30,34,4.5)]},
  pencil:{s:["M43 8l13 13L23 54H10V41z","M36 15l13 13"], f:["M10 41v13h13z"]},
  sparkle:{s:["M28 6c2 14 6 18 20 20-14 2-18 6-20 20-2-14-6-18-20-20 14-2 18-6 20-20z","M50 40c1 6 2.5 7.5 8 8.5-5.5 1-7 2.5-8 8.5-1-6-2.5-7.5-8-8.5 5.5-1 7-2.5 8-8.5z"], f:["M28 6c2 14 6 18 20 20-14 2-18 6-20 20-2-14-6-18-20-20 14-2 18-6 20-20z"]},
  clock:{s:[cP(32,32,24),"M32 17v15l10 6"], f:[cP(32,32,24)]},
  puzzle:{s:["M10 18h13a6 6 0 1 1 12 0h13v13a6 6 0 1 0 0 12v13H35a6 6 0 1 0-12 0H10V43a6 6 0 1 1 0-12z"], f:["M10 18h13a6 6 0 1 1 12 0h13v13a6 6 0 1 0 0 12v13H35a6 6 0 1 0-12 0H10V43a6 6 0 1 1 0-12z"]},
  search:{s:[cP(27,27,17),"M39.5 39.5L56 56"], f:[cP(27,27,17)]},
  home:{s:["M7 31L32 9l25 22","M14 25v31h36V25","M26 56V41h12v15"], f:["M14 25L32 10l18 15v31H14z"]},
  phone:{s:[rP(17,5,30,54,7),"M28 50h8"], f:[rP(21,12,22,32,2)]},
  question:{s:[cP(32,32,24),"M24.5 25a7.5 7.5 0 1 1 10.5 6.9c-2 .9-3 2.6-3 4.6V39"], f:[cP(32,32,24)], d:[cP(32,46.5,2.6)]},
  megaphone:{s:["M8 27v10h9l23 13V14L17 27z","M17 37l4 15h7l-3-13","M48 24c3.5 3 3.5 13 0 16","M54 18c6.5 6.5 6.5 21.5 0 28"], f:["M17 27l23-13v36L17 37z"]},
  mail:{s:[rP(8,14,48,36,6),"M10 18l22 17 22-17"], f:[rP(8,14,48,36,6)]},
  shield:{s:["M32 6l22 8v16c0 14-9 23-22 28C19 53 10 44 10 30V14z","M22 31l7 7 13-14"], f:["M32 6l22 8v16c0 14-9 23-22 28C19 53 10 44 10 30V14z"]},
  warning:{s:["M32 8L58 54H6z","M32 24v14"], f:["M32 8L58 54H6z"], d:[cP(32,46,2.6)]},
  game:{s:[rP(6,20,52,28,14),"M20 28v12","M14 34h12"], f:[rP(6,20,52,28,14)], d:[cP(42,31,3),cP(49,37,3)]}
};
var ICON_ALIAS = {
  "실험":"flask","과학":"flask","플라스크":"flask","책":"book","독서":"book","국어":"book","교과서":"book","지구":"globe","세계":"globe","사회":"globe","지리":"globe",
  "아이디어":"lightbulb","전구":"lightbulb","생각":"lightbulb","idea":"lightbulb","그래프":"chart","통계":"chart","자료":"chart","결과":"chart","graph":"chart",
  "사람들":"people","친구":"people","모둠":"people","학생":"people","선생님":"people","학교":"school","교실":"school","ai":"robot","인공지능":"robot","로봇":"robot",
  "일정":"calendar","달력":"calendar","날짜":"calendar","확인":"check","완료":"check","정답":"check","ok":"check","별":"star","칭찬":"star","하트":"heart","심장":"heart","사랑":"heart","기관":"heart",
  "음악":"music","노래":"music","잎":"leaf","식물":"leaf","자연":"leaf","환경":"leaf","원자":"atom","물질":"atom","세포":"cell","조직":"tissue","사람":"person","개체":"person","나":"person",
  "현미경":"microscope","대화":"chat","질문":"chat","말":"chat","주문":"chat","목표":"target","과녁":"target","연필":"pencil","글쓰기":"pencil","쓰기":"pencil","고치기":"pencil",
  "반짝":"sparkle","마법":"sparkle","새로움":"sparkle","시간":"clock","시계":"clock","퍼즐":"puzzle","찾기":"search","검색":"search","돋보기":"search","집":"home","가정":"home",
  "휴대폰":"phone","스마트폰":"phone","폰":"phone","물음표":"question","궁금":"question","안내":"megaphone","공지":"megaphone","편지":"mail","가정통신문":"mail","안전":"shield","보호":"shield","주의":"warning","경고":"warning","게임":"game","놀이":"game"
};
function iconKey(k){ k = txt(k).trim(); if (!k) return ""; var lk = k.toLowerCase(); if (ICONS[lk]) return lk; if (ICON_ALIAS[lk]) return ICON_ALIAS[lk]; if (ICON_ALIAS[k]) return ICON_ALIAS[k]; return ""; }
function isEmoji(k){ return /[←-⯿㊗㊙]|[\uD83C-\uDBFF][\uDC00-\uDFFF]/.test(txt(k)); }
function icon(k, cls){
  var key = iconKey(k);
  if (!key){
    if (k && isEmoji(k)) return '<span class="emo ' + (cls || "") + '">' + esc(k) + "</span>";
    key = "sparkle";
  }
  var I = ICONS[key], h = '<svg class="ic ' + (cls || "") + '" viewBox="0 0 64 64" aria-hidden="true">';
  if (I.f) h += '<g class="icf">' + I.f.map(function(d){ return '<path d="' + d + '"/>'; }).join("") + "</g>";
  h += '<g class="ics">' + I.s.map(function(x){ var d = Array.isArray(x) ? x[0] : x, tr = Array.isArray(x) && x[1] ? ' transform="' + x[1] + '"' : ""; return '<path class="dr" pathLength="1" d="' + d + '"' + tr + "/>"; }).join("") + "</g>";
  if (I.d) h += '<g class="icd">' + I.d.map(function(d){ return '<path d="' + d + '"/>'; }).join("") + "</g>";
  return h + "</svg>";
}

/* ---------- hand-drawn geometry (seeded, so every replay/print is identical) ---------- */
function wobbleLine(r, w, h, y){
  var n = 4, p = "M" + (2 + r() * 3).toFixed(1) + " " + (y + (r() - .5) * h * .3).toFixed(1);
  for (var i = 1; i <= n; i++){ var x = w * i / n - (i === n ? 2 : 0); p += " Q" + (x - w / n / 2).toFixed(1) + " " + (y + (r() - .5) * h * .9).toFixed(1) + " " + x.toFixed(1) + " " + (y + (r() - .5) * h * .35).toFixed(1); }
  return p;
}
function roughRect(r, w, h, j){
  j = j || 5;
  function J(){ return ((r() - .5) * 2 * j).toFixed(1); }
  var x0 = 6, y0 = 6, x1 = w - 6, y1 = h - 6;
  return "M" + (x0 + 14) + " " + (y0 + +J()) + " L" + (x1 + +J()) + " " + (y0 + +J()) + " L" + (x1 + +J()) + " " + (y1 + +J()) + " L" + (x0 + +J()) + " " + (y1 + +J()) + " L" + (x0 + +J()) + " " + (y0 + +J()) + " L" + (x0 + 40) + " " + (y0 + 2 + +J());
}
function roughLoop(r, w, h){
  var cx = w / 2, cy = h / 2, rx = w / 2 - 8, ry = h / 2 - 8, pts = [], turns = 1.12, steps = 40, a0 = -2.3 + r() * .4;
  for (var i = 0; i <= steps; i++){ var a = a0 + Math.PI * 2 * turns * i / steps, k = 1 + (r() - .5) * .06 + (i / steps) * .05; pts.push((cx + Math.cos(a) * rx * k).toFixed(1) + " " + (cy + Math.sin(a) * ry * k).toFixed(1)); }
  return "M" + pts.join(" L");
}
function svgDeco(cls, w, h, d, extra){ return '<svg class="' + cls + '" viewBox="0 0 ' + w + " " + h + '" preserveAspectRatio="none" aria-hidden="true"><path class="dr" pathLength="1" d="' + d + '"' + (extra || "") + "/></svg>"; }

/* ---------- timeline helper: absolute positions + initial "from" state for deterministic seek ---------- */
var CID = 0;
function mkA(tl){
  var cid = ++CID;
  var A = {
    tl: tl,
    add: function(targets, params, at){
      var t = targets && targets.length != null && !(targets instanceof Element) ? Array.prototype.slice.call(targets) : [targets];
      t = t.filter(function(x){ return x; });
      if (!t.length) return at;
      var from = {};
      for (var k in params){ if (Array.isArray(params[k]) && params[k].length === 2) from[k] = params[k][0]; }
      t.forEach(function(el){
        if (el.__cid !== cid){ el.__cid = cid; el.__set = {}; }
        var f = {}, any = false;
        for (var k in from){ if (!el.__set[k]){ el.__set[k] = 1; f[k] = from[k]; any = true; } }
        if (any) anime.utils.set(el, f);
      });
      tl.add(t.length === 1 ? t[0] : t, params, Math.max(0, at));
      return at;
    },
    end: function(){ return tl.duration || 0; }
  };
  return A;
}
function stag(ms){ return anime.stagger(ms); }

/* ---------- skins: type, motion vocabulary, art, painter, transition ---------- */
var noiseURL = "";
function chalkNoise(){
  if (noiseURL) return noiseURL;
  var c = document.createElement("canvas"), n = 160; c.width = c.height = n;
  var g = c.getContext("2d"), img = g.createImageData(n, n), r = rng(11);
  for (var p = 0; p < n * n; p++){ var v = r(); img.data[p * 4 + 3] = v < .2 ? Math.floor(r() * 150) : Math.floor(205 + r() * 50); }
  g.putImageData(img, 0, 0);
  noiseURL = c.toDataURL("image/png");
  return noiseURL;
}
var texCache = null;
function tex(build){ if (!texCache){ texCache = document.createElement("canvas"); texCache.width = W; texCache.height = H; build(texCache.getContext("2d")); } return texCache; }

var SK_BASE = {
  fade: function(A, el, t, dy){ A.add(el, {opacity:[0, 1], translateY:[dy == null ? 24 : dy, 0], duration:800, ease:"outExpo"}, t); return t + 500; },
  drawIn: function(A, paths, t, dur, st){ A.add(paths, {strokeDashoffset:[1.1, 0], duration:dur || 700, ease:"inOutQuad", delay:stag(st || 90)}, t); return t + (dur || 700); },
  emph: function(){ },
  art: function(){ return ""; },
  decorate: function(){ }
};
function skin(o){ var k; var out = {}; for (k in SK_BASE) out[k] = SK_BASE[k]; for (k in o) out[k] = o[k]; return out; }

var SKINS = {};
SKINS["clean-keynote"] = skin({
  text: function(A, box, t, o){
    var w = qa(box, ".wi"); if (!w.length) return t;
    var st = o && o.fast ? 26 : 46;
    A.add(w, {translateY:["115%", "0%"], duration:1100, ease:"outExpo", delay:stag(st)}, t);
    return t + 420 + w.length * st;
  },
  pop: function(A, els, t){ A.add(els, {opacity:[0, 1], translateY:[70, 0], duration:1100, ease:"outExpo", delay:stag(90)}, t); return t + 450; },
  trans: function(A, old, el, t){
    if (old) A.add(old, {opacity:[1, 0], translateY:[0, -36], duration:520, ease:"inOutQuad"}, t);
    A.add(el, {opacity:[0, 1], duration:240, ease:"linear"}, t + (old ? 300 : 0));
    return t + (old ? 330 : 60);
  },
  art: function(layout){
    if (layout === "cover") return '<div class="art cv-ring"><svg viewBox="0 0 600 600"><path class="dr" pathLength="1" d="' + cP(300, 300, 270) + '"/><path class="dr dr2" pathLength="1" d="' + cP(300, 300, 200) + '"/></svg><i class="ap dot"></i></div>';
    if (layout === "question") return '<div class="art qs-glyph ap">?</div>';
    return "";
  },
  painter: function(ctx, t){
    ctx.fillStyle = cssVar("bg1", "#fbfbfd"); ctx.fillRect(0, 0, W, H);
    var a = t * 0.07;
    var x1 = 1500 + Math.sin(a) * 140, y1 = 260 + Math.cos(a * .8) * 90;
    var g1 = ctx.createRadialGradient(x1, y1, 0, x1, y1, 900);
    g1.addColorStop(0, cssVar("glow1", "rgba(0,102,255,.10)")); g1.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = g1; ctx.fillRect(0, 0, W, H);
    var x2 = 300 + Math.cos(a * .9) * 120, y2 = 980 + Math.sin(a) * 60;
    var g2 = ctx.createRadialGradient(x2, y2, 0, x2, y2, 760);
    g2.addColorStop(0, cssVar("glow2", "rgba(0,194,168,.08)")); g2.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = g2; ctx.fillRect(0, 0, W, H);
  }
});

SKINS.chalkboard = skin({
  text: function(A, box, t, o){
    var c = qa(box, ".ch"); if (!c.length) return t;
    var per = clamp(Math.round((o && o.fast ? 700 : 1150) / c.length), 9, 48);
    A.add(c, {opacity:[0, 1], scale:[.7, 1], duration:180, ease:"outQuad", delay:stag(per)}, t);
    return t + 180 + per * c.length;
  },
  pop: function(A, els, t){ A.add(els, {opacity:[0, 1], duration:520, ease:"outQuad", delay:stag(110)}, t); return t + 300; },
  emph: function(A, root, t){ return this.drawIn(A, qa(root, ".kwu path"), t, 520, 160); },
  trans: function(A, old, el, t){
    var fx = document.getElementById("dk-eraser");
    if (old){
      A.add(old, {clipPath:["inset(0px 0px 0px 0px)", "inset(0px 0px 0px 1960px)"], duration:820, ease:"inOutSine"}, t);
      if (fx) A.add(fx, {translateX:[-420, 2080], opacity:[1, 1], duration:820, ease:"inOutSine"}, t);
      if (fx) A.add(fx, {opacity:[1, 0], duration:160, ease:"linear"}, t + 820);
    }
    A.add(el, {opacity:[0, 1], duration:200, ease:"linear"}, t + (old ? 640 : 0));
    return t + (old ? 700 : 80);
  },
  art: function(layout, it){
    if (layout === "cover") return '<div class="art cv-doodle">' + icon(it.icon || "star") + "</div>";
    if (layout === "question") return '<div class="art qs-doodle">' + svgDeco("", 300, 420, "M70 120 C70 40 230 30 236 118 C240 190 150 190 150 270 L150 300", ' ') + '<i class="ap qs-dot"></i></div>';
    if (layout === "quote") return "";
    if (layout === "end") return '<div class="art en-doodle">' + icon(it.icon || "heart") + "</div>";
    return "";
  },
  decorate: function(el, it, idx){
    var r = rng(hash(it.layout + idx + plain(it.title || it.text || it.q || "")));
    qa(el, ".kw").forEach(function(k){ k.insertAdjacentHTML("beforeend", svgDeco("kwu", 100, 14, wobbleLine(r, 100, 14, 8))); });
    qa(el, ".cbox, .chbox, .sk-box").forEach(function(b){
      var w = b.offsetWidth, h = b.offsetHeight; if (!w || !h) return;
      b.insertAdjacentHTML("afterbegin", svgDeco("rough", w, h, roughRect(r, w, h, 4)));
    });
    qa(el, ".ring-me").forEach(function(b){
      var w = b.offsetWidth + 60, h = b.offsetHeight + 50;
      b.insertAdjacentHTML("beforeend", svgDeco("ring", w, h, roughLoop(r, w, h)));
    });
    if (q(el, ".cv-title")) el.insertAdjacentHTML("beforeend", svgDeco("cv-ul", 1200, 30, wobbleLine(r, 1200, 30, 15)));
  },
  painter: function(ctx, t){
    ctx.drawImage(tex(function(g){
      var b1 = cssVar("bg1", "#2b5546"), b2 = cssVar("bg2", "#173229"), r = rng(7);
      var grd = g.createRadialGradient(960, 470, 120, 960, 540, 1250); grd.addColorStop(0, b1); grd.addColorStop(1, b2);
      g.fillStyle = grd; g.fillRect(0, 0, W, H);
      g.lineCap = "round";
      for (var i = 0; i < 34; i++){
        g.strokeStyle = "rgba(255,255,255," + (0.012 + r() * 0.03).toFixed(3) + ")"; g.lineWidth = 50 + r() * 110;
        var x = r() * W, y = r() * H; g.beginPath(); g.moveTo(x, y);
        g.bezierCurveTo(x + (r() - .5) * 700, y + (r() - .5) * 240, x + (r() - .5) * 700, y + (r() - .5) * 240, x + (r() - .5) * 900, y + (r() - .5) * 200); g.stroke();
      }
      for (var j = 0; j < 22; j++){
        g.strokeStyle = "rgba(255,255,255," + (0.03 + r() * 0.04).toFixed(3) + ")"; g.lineWidth = 1.5 + r() * 2;
        var sx = r() * W, sy = r() * H; g.beginPath(); g.moveTo(sx, sy);
        for (var k = 0; k < 6; k++){ sx += 20 + r() * 40; sy += (r() - .5) * 26; g.lineTo(sx, sy); } g.stroke();
      }
      for (var d = 0; d < 14000; d++){ g.fillStyle = "rgba(255,255,255," + (r() * 0.07).toFixed(3) + ")"; g.fillRect(r() * W, r() * H, 1 + r() * 1.6, 1 + r() * 1.6); }
      var fw = 22, wood = g.createLinearGradient(0, 0, 0, fw); wood.addColorStop(0, "#8a5a33"); wood.addColorStop(1, "#5d3a1e");
      g.fillStyle = "#6e4526"; g.fillRect(0, 0, W, fw); g.fillRect(0, H - fw, W, fw); g.fillRect(0, 0, fw, H); g.fillRect(W - fw, 0, fw, H);
      g.fillStyle = wood; g.fillRect(0, 0, W, fw);
      g.strokeStyle = "rgba(0,0,0,.35)"; g.lineWidth = 6; g.strokeRect(fw + 3, fw + 3, W - 2 * fw - 6, H - 2 * fw - 6);
      g.fillStyle = "#4f311a"; g.fillRect(260, H - fw - 12, W - 520, 16);
      [["#f6f2e6", 1320, 120], ["#ffe27a", 1470, 90], ["#ff9fb2", 1590, 70]].forEach(function(c){ g.fillStyle = c[0]; g.fillRect(c[1], H - fw - 24, c[2], 13); });
      g.fillStyle = "#3a3a44"; g.fillRect(420, H - fw - 34, 170, 24); g.fillStyle = "#c9b28a"; g.fillRect(420, H - fw - 40, 170, 8);
    }), 0, 0);
    for (var m = 0; m < 16; m++){
      var rr = rng(100 + m), x0 = rr() * W, y0 = rr() * H, sp = 6 + rr() * 10;
      var x = (x0 + t * sp) % W, y = (y0 - t * sp * .5 + H * 10) % H, al = .05 + .05 * Math.sin(t * .8 + m);
      ctx.fillStyle = "rgba(255,255,255," + al.toFixed(3) + ")"; ctx.beginPath(); ctx.arc(x, y, 1.6 + rr() * 2, 0, 6.283); ctx.fill();
    }
  }
});

SKINS["notebook-pastel"] = skin({
  fitScale: 1.16,
  text: function(A, box, t, o){
    var w = qa(box, ".wi"); if (!w.length) return t;
    var st = o && o.fast ? 34 : 58;
    A.add(w, {opacity:[0, 1], translateY:[30, 0], scale:[.55, 1], duration:720, ease:"outBack(2.2)", delay:stag(st)}, t);
    return t + 360 + w.length * st;
  },
  pop: function(A, els, t){ A.add(els, {opacity:[0, 1], translateY:[-60, 0], scale:[1.12, 1], duration:760, ease:"outBack(1.7)", delay:stag(110)}, t); return t + 380; },
  emph: function(A, root, t){ A.add(qa(root, ".kwh"), {scaleX:[0, 1], duration:520, ease:"outQuad", delay:stag(120)}, t); return t + 500; },
  trans: function(A, old, el, t){
    if (old) A.add(old, {opacity:[1, 0], translateX:[0, -180], rotate:[0, -3], duration:520, ease:"inQuad"}, t);
    A.add(el, {opacity:[0, 1], duration:200, ease:"linear"}, t + (old ? 360 : 0));
    return t + (old ? 380 : 60);
  },
  art: function(layout, it, idx){
    var r = rng(hash("nb" + idx)), h = "";
    function star(x, y, s){ return '<svg class="art doodle" style="left:' + x + "px;top:" + y + "px;width:" + s + "px;height:" + s + 'px" viewBox="0 0 64 64"><path class="dr" pathLength="1" d="' + ICONS.star.s[0] + '"/></svg>'; }
    function squiggle(x, y, w){ return '<svg class="art doodle" style="left:' + x + "px;top:" + y + "px;width:" + w + 'px;height:40px" viewBox="0 0 ' + w + ' 40"><path class="dr" pathLength="1" d="' + wobbleLine(r, w, 40, 20) + '"/></svg>'; }
    if (layout === "cover") h = '<div class="art nb-paper ap"><i class="tape tl"></i><i class="tape tr"></i></div>' + star(1650, 120, 90) + star(1760, 230, 54) + squiggle(1420, 960, 300);
    else if (layout === "section") h = star(1700, 160, 70) + squiggle(840, 800, 300);
    else if (layout === "question") h = '<div class="art nb-q ap">?</div>' + star(1690, 760, 64);
    else if (layout === "quote") h = '<div class="art nb-card"><i class="tape tc"></i></div>';
    else if (layout === "bigtext") h = star(1690, 150, 72) + squiggle(130, 900, 220);
    else if (layout === "end") h = star(1100, 160, 80) + star(1200, 280, 50);
    else if (layout === "bignumber") h = star(300, 300, 70) + star(1560, 620, 56);
    return h;
  },
  decorate: function(el){
    qa(el, ".kw").forEach(function(k){ k.insertAdjacentHTML("afterbegin", '<i class="kwh"></i>'); });
  },
  painter: function(ctx){
    ctx.drawImage(tex(function(g){
      var r = rng(5);
      g.fillStyle = cssVar("bg1", "#fffdf6"); g.fillRect(0, 0, W, H);
      for (var d = 0; d < 9000; d++){ g.fillStyle = "rgba(120,100,60," + (r() * 0.035).toFixed(3) + ")"; g.fillRect(r() * W, r() * H, 1 + r() * 2, 1); }
      g.strokeStyle = cssVar("grid", "rgba(120,170,220,.28)"); g.lineWidth = 1.5;
      for (var x = 48; x < W; x += 48){ g.beginPath(); g.moveTo(x + .5, 0); g.lineTo(x + .5, H); g.stroke(); }
      for (var y = 48; y < H; y += 48){ g.beginPath(); g.moveTo(0, y + .5); g.lineTo(W, y + .5); g.stroke(); }
      g.strokeStyle = cssVar("margin", "rgba(240,120,130,.55)"); g.lineWidth = 2.5;
      [92, 100].forEach(function(mx){ g.beginPath(); g.moveTo(mx, 0); g.lineTo(mx, H); g.stroke(); });
      [190, 540, 890].forEach(function(hy){
        g.fillStyle = "rgba(0,0,0,.08)"; g.beginPath(); g.arc(48, hy + 3, 17, 0, 6.283); g.fill();
        g.fillStyle = cssVar("bg2", "#efe9db"); g.beginPath(); g.arc(46, hy, 16, 0, 6.283); g.fill();
      });
    }), 0, 0);
  }
});
var SK = SKINS[SKIN_NAME] || SKINS["clean-keynote"];

/* ---------- layouts: html(item) + enter(A, el, item, t) → ready time + item(A, el, item, i, t) for builds ---------- */
var sectionNo = {};
(function(){ var n = 0; ITEMS.forEach(function(it, i){ if (it.layout === "section") sectionNo[i] = ++n; }); })();
function pad2(n){ return n < 10 ? "0" + n : String(n); }
function kicker(it, fb){ var k = it.kicker != null ? it.kicker : fb; return k ? '<div class="kicker">' + esc(k) + "</div>" : ""; }
function head(it){ return '<header class="hd">' + kicker(it) + '<div class="ttl fit" data-fit="84,46,1"><div class="tx">' + rt(it.title) + "</div></div></header>"; }
function headIn(A, el, t){
  SK.fade(A, q(el, ".hd .kicker"), t, 16);
  var e = SK.text(A, q(el, ".hd .ttl"), t + 80, {fast:1});
  SK.emph(A, q(el, ".hd"), e);
  A.add(q(el, ".hd-rule"), {scaleX:[0, 1], duration:900, ease:"outExpo"}, t + 120);
  return Math.min(e, t + 650);
}
function fitSpec(box, max, min, al){ return '<div class="' + box + ' fit" data-fit="' + max + "," + min + "," + (al == null ? 0 : al) + '"><div class="tx">'; }

var LAY = {};
LAY.cover = {
  html: function(it){
    return '<div class="cv-kicker">' + esc(it.kicker || "") + "</div>" +
      fitSpec("cv-title", 200, 92, 1) + rt(it.title) + "</div></div>" +
      (it.subtitle ? fitSpec("cv-sub", 54, 30, 0) + rt(it.subtitle) + "</div></div>" : "") +
      (it.meta ? '<div class="cv-meta"><i class="rule"></i><span>' + esc(it.meta) + "</span></div>" : "");
  },
  enter: function(A, el, it, t){
    SK.fade(A, q(el, ".cv-kicker"), t + 100, 20);
    var e = SK.text(A, q(el, ".cv-title"), t + 220);
    SK.drawIn(A, qa(el, ".cv-ul path"), e - 100, 700);
    SK.emph(A, el, e);
    SK.text(A, q(el, ".cv-sub"), e - 250, {fast:1});
    A.add(q(el, ".cv-meta"), {opacity:[0, 1], translateX:[-30, 0], duration:900, ease:"outExpo"}, e + 50);
    return e;
  }
};
LAY.section = {
  html: function(it, idx){
    var num = it.num != null ? txt(it.num) : pad2(sectionNo[idx] || 1);
    return '<div class="sc-num ring-me"><span>' + esc(num) + "</span></div>" +
      '<div class="sc-body">' + kicker(it) + fitSpec("sc-t", 140, 64, 1) + rt(it.title) + "</div></div>" +
      (it.sub ? '<div class="sc-sub">' + esc(it.sub) + "</div>" : "") + "</div>";
  },
  enter: function(A, el, it, t){
    A.add(q(el, ".sc-num span"), {opacity:[0, 1], translateY:[120, 0], scale:[.86, 1], duration:1300, ease:"outExpo"}, t);
    SK.drawIn(A, qa(el, ".sc-num .ring path"), t + 300, 900);
    SK.fade(A, q(el, ".sc-body .kicker"), t + 250, 16);
    var e = SK.text(A, q(el, ".sc-t"), t + 380);
    SK.emph(A, el, e);
    SK.fade(A, q(el, ".sc-sub"), e - 200, 20);
    return e;
  }
};
LAY.question = {
  count: function(it){ return it.hint ? 1 : 0; }, always: true,
  html: function(it){
    return '<div class="qs-kicker">' + esc(it.kicker != null ? it.kicker : label("question", "생각해 볼까요?")) + "</div>" +
      fitSpec("qs-q", 150, 64, .5) + rt(it.q || it.title) + "</div></div>" +
      (it.hint ? '<div class="qs-hint" data-b="0"><span class="hint-l">' + esc(label("hint", "힌트")) + '</span><span class="hint-x">' + rt(it.hint) + "</span></div>" : "");
  },
  enter: function(A, el, it, t){
    SK.fade(A, q(el, ".qs-kicker"), t, 20);
    var e = SK.text(A, q(el, ".qs-q"), t + 150);
    SK.emph(A, el, e);
    return e;
  },
  item: function(A, el, it, i, t){ var h = q(el, ".qs-hint"); A.add(h, {opacity:[0, 1], translateY:[40, 0], duration:900, ease:"outExpo"}, t); SK.emph(A, h, t + 300); return 900; }
};
LAY.bigtext = {
  html: function(it){
    return (it.kicker ? '<div class="bt-kicker">' + esc(it.kicker) + "</div>" : "") + fitSpec("bt-x", 170, 70, .5) + rt(it.text || it.title) + "</div></div>" +
      (it.sub ? '<div class="bt-sub">' + rt(it.sub) + "</div>" : "");
  },
  enter: function(A, el, it, t){
    SK.fade(A, q(el, ".bt-kicker"), t, 16);
    var e = SK.text(A, q(el, ".bt-x"), t + 100);
    SK.emph(A, el, e);
    SK.fade(A, q(el, ".bt-sub"), e + 100, 24);
    return e;
  }
};
LAY.cards = {
  count: function(it){ return Math.min(4, arr(it.cards).length); }, stagger: 160,
  html: function(it){
    var cs = arr(it.cards).slice(0, 4);
    return head(it) + '<div class="cards n' + cs.length + '">' + cs.map(function(c, i){
      return '<div class="card" data-b="' + i + '"><div class="cbox" style="--r:' + [-1.6, 1.2, -.8, 1.8][i] + "deg;--pc:var(--pc" + (i + 1) + ')">' +
        '<i class="tape"></i><div class="c-ic">' + icon(c.icon) + "</div>" +
        fitSpec("c-t", 50, 30, 0) + rt(c.title) + "</div></div>" + fitSpec("c-x", cs.length <= 3 ? 40 : 34, 22, 0) + rt(c.text) + "</div></div></div></div>";
    }).join("") + "</div>";
  },
  enter: function(A, el, it, t){ return headIn(A, el, t); },
  item: function(A, el, it, i, t){
    var c = qa(el, ".card")[i];
    SK.pop(A, c, t);
    SK.drawIn(A, qa(c, ".rough path"), t + 60, 650);
    SK.drawIn(A, qa(c, ".c-ic .dr"), t + 160, 700, 70);
    A.add(qa(c, ".icf, .icd"), {opacity:[0, 1], duration:500, ease:"linear"}, t + 600);
    SK.text(A, q(c, ".c-t"), t + 200, {fast:1});
    SK.emph(A, c, t + 700);
    SK.fade(A, q(c, ".c-x .tx"), t + 360, 16);
    return 950;
  }
};
LAY.compare = {
  count: function(it){ return Math.min(5, arr(it.rows).length); }, stagger: 140,
  html: function(it){
    var a = it.a || {}, b = it.b || {}, rows = arr(it.rows).slice(0, 5);
    function side(s, cls){ return '<div class="' + cls + '">' + (s.icon ? icon(s.icon) : "") + "<span>" + esc(s.label || "") + "</span></div>"; }
    return head(it) + '<div class="cmp n' + rows.length + '"><div class="cmp-h">' + side(a, "cmp-a") + '<div class="vs">' + esc(label("vs", "VS")) + "</div>" + side(b, "cmp-b") + "</div>" +
      '<div class="cmp-rows">' + rows.map(function(r, i){
        return '<div class="cmp-row" data-b="' + i + '">' + fitSpec("ca sk-box", 40, 22, .5) + rt(r.a) + "</div></div>" +
          '<div class="ck">' + esc(r.k || "") + "</div>" + fitSpec("cb sk-box", 40, 22, .5) + rt(r.b) + "</div></div></div>";
      }).join("") + "</div></div>";
  },
  enter: function(A, el, it, t){
    var r = headIn(A, el, t);
    A.add(q(el, ".cmp-a"), {opacity:[0, 1], translateX:[-60, 0], duration:900, ease:"outExpo"}, r);
    A.add(q(el, ".cmp-b"), {opacity:[0, 1], translateX:[60, 0], duration:900, ease:"outExpo"}, r + 80);
    A.add(q(el, ".vs"), {opacity:[0, 1], scale:[0, 1], rotate:[-90, 0], duration:800, ease:"outBack(2)"}, r + 200);
    SK.drawIn(A, qa(el, ".cmp-h .dr"), r + 100, 600, 40);
    return r + 400;
  },
  item: function(A, el, it, i, t){
    var row = qa(el, ".cmp-row")[i];
    A.add(q(row, ".ca"), {opacity:[0, 1], translateX:[-50, 0], duration:900, ease:"outExpo"}, t);
    A.add(q(row, ".ck"), {opacity:[0, 1], duration:500, ease:"linear"}, t + 120);
    A.add(q(row, ".cb"), {opacity:[0, 1], translateX:[50, 0], duration:900, ease:"outExpo"}, t + 220);
    SK.drawIn(A, qa(row, ".rough path"), t, 600, 160);
    SK.emph(A, row, t + 500);
    return 950;
  }
};
LAY.steps = {
  count: function(it){ return Math.min(6, arr(it.steps).length); }, stagger: 220,
  html: function(it){
    var st = arr(it.steps).slice(0, 6), n = st.length || 1;
    var segs = st.map(function(s, i){ return i ? '<i class="seg" data-b="' + i + '" style="left:' + ((i - .5) / n * 100) + "%;width:" + (100 / n) + '%"></i>' : ""; }).join("");
    return head(it) + '<div class="stp n' + n + '"><div class="stp-track">' + segs + "</div>" + st.map(function(s, i){
      return '<div class="st" data-b="' + i + '"><div class="sbox" style="--r:' + [-1.5, 1.2, -1, 1.6, -1.2, 1][i] + "deg;--pc:var(--pc" + (i % 4 + 1) + ')"><div class="st-num">' + (s.icon ? icon(s.icon) : "<span>" + (i + 1) + "</span>") + "</div>" +
        fitSpec("st-t", n <= 4 ? 56 : 50, 26, 0) + rt(s.title) + "</div></div>" + fitSpec("st-x", n <= 4 ? 36 : 32, 21, 0) + rt(s.text) + "</div></div></div></div>";
    }).join("") + "</div>";
  },
  enter: function(A, el, it, t){ return headIn(A, el, t); },
  item: function(A, el, it, i, t){
    var s = qa(el, ".st")[i], seg = qa(el, ".seg").filter(function(x){ return x.getAttribute("data-b") === String(i); })[0];
    var t0 = t;
    if (seg){ A.add(seg, {scaleX:[0, 1], duration:520, ease:"inOutQuad"}, t); t0 = t + 380; }
    A.add(q(s, ".st-num"), {opacity:[0, 1], scale:[.3, 1], duration:800, ease:"outBack(2.4)"}, t0);
    SK.drawIn(A, qa(s, ".st-num .dr"), t0 + 120, 600, 60);
    SK.text(A, q(s, ".st-t"), t0 + 180, {fast:1});
    SK.emph(A, s, t0 + 600);
    SK.fade(A, q(s, ".st-x .tx"), t0 + 300, 16);
    return t0 - t + 820;
  }
};
LAY.timeline = {
  count: function(it){ return Math.min(6, arr(it.events).length); }, stagger: 200,
  html: function(it){
    var ev = arr(it.events).slice(0, 6), n = ev.length || 1;
    var segs = ev.map(function(e, i){ return '<i class="seg" data-b="' + i + '" style="left:' + (i ? (i - .5) / n * 100 : 0) + "%;width:" + (i ? 100 / n : 50 / n) + '%"></i>'; }).join("");
    return head(it) + '<div class="tml n' + n + '"><div class="tml-line"><i class="base"></i>' + segs + "</div>" + ev.map(function(e, i){
      return '<div class="ev" data-b="' + i + '" style="left:' + (i / n * 100) + "%;width:" + (100 / n) + '%">' +
        fitSpec("ev-when", 60, 30, 1) + rt(e.when) + "</div></div><i class=\"ev-dot\"></i>" +
        fitSpec("ev-t", 40, 24, 0) + rt(e.title) + "</div></div>" + fitSpec("ev-x", 30, 20, 0) + rt(e.text) + "</div></div></div>";
    }).join("") + "</div>";
  },
  enter: function(A, el, it, t){ var r = headIn(A, el, t); A.add(q(el, ".tml-line .base"), {scaleX:[0, 1], duration:1200, ease:"inOutQuad"}, r - 200); return r + 300; },
  item: function(A, el, it, i, t){
    var e = qa(el, ".ev")[i], seg = qa(el, ".seg")[i];
    A.add(seg, {scaleX:[0, 1], duration:480, ease:"inOutQuad"}, t);
    A.add(q(e, ".ev-dot"), {scale:[0, 1], duration:700, ease:"outBack(3)"}, t + 380);
    SK.text(A, q(e, ".ev-when"), t + 420, {fast:1});
    SK.text(A, q(e, ".ev-t"), t + 520, {fast:1});
    SK.emph(A, e, t + 900);
    SK.fade(A, q(e, ".ev-x .tx"), t + 640, 16);
    return 1050;
  }
};
function numParts(v){
  var s = txt(v), m = s.match(/-?\d[\d,]*(\.\d+)?/);
  if (!m) return null;
  var raw = m[0].replace(/,/g, ""), dec = (raw.split(".")[1] || "").length;
  return {pre:s.slice(0, m.index), num:parseFloat(raw), dec:dec, post:s.slice(m.index + m[0].length), comma:m[0].indexOf(",") >= 0 || Math.abs(parseFloat(raw)) >= 10000};
}
function fmtNum(v, dec, comma){ var s = v.toFixed(dec); if (comma){ var p = s.split("."); p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ","); s = p.join("."); } return s; }
LAY.bignumber = {
  html: function(it){
    var p = numParts(it.value);
    var val = p ? '<span class="val" data-n="' + p.num + '" data-d="' + p.dec + '" data-c="' + (p.comma ? 1 : 0) + '">' + esc(fmtNum(p.num, p.dec, p.comma)) + "</span>" : '<span class="val">' + esc(it.value) + "</span>";
    return (it.kicker || it.title ? '<div class="bn-kicker">' + esc(it.kicker || it.title) + "</div>" : "") +
      '<div class="bn-num" data-fit="380,140,0"><span class="pre">' + esc((it.prefix || "") + (p ? p.pre : "")) + "</span>" + val + '<span class="unit">' + esc((p ? p.post : "") + (it.unit || "")) + "</span></div>" +
      '<i class="bn-rule"></i>' + fitSpec("bn-cap", 52, 28, 0) + rt(it.caption) + "</div></div>";
  },
  enter: function(A, el, it, t){
    SK.fade(A, q(el, ".bn-kicker"), t, 16);
    var v = q(el, ".val"), n = v && v.getAttribute("data-n");
    A.add(q(el, ".bn-num"), {opacity:[0, 1], translateY:[80, 0], duration:1200, ease:"outExpo"}, t + 120);
    if (n != null){
      var target = parseFloat(n), dec = +v.getAttribute("data-d"), cm = v.getAttribute("data-c") === "1", o = {v:0};
      v.textContent = fmtNum(0, dec, cm);
      A.add(o, {v:[0, target], duration:1800, ease:"outExpo", onUpdate:function(){ v.textContent = fmtNum(o.v, dec, cm); }}, t + 160);
    }
    A.add(q(el, ".bn-rule"), {scaleX:[0, 1], duration:900, ease:"outExpo"}, t + 900);
    SK.text(A, q(el, ".bn-cap"), t + 1000, {fast:1});
    SK.emph(A, el, t + 1700);
    return t + 1500;
  }
};
LAY.quote = {
  html: function(it){
    return '<div class="qt-mark">“</div>' + fitSpec("qt-x", 92, 44, .5) + rt(it.text || it.quote) + "</div></div>" +
      (it.source ? '<div class="qt-src"><i class="rule"></i>' + esc(it.source) + "</div>" : "");
  },
  enter: function(A, el, it, t){
    A.add(q(el, ".nb-card"), {opacity:[0, 1], rotate:[-6, -1.2], scale:[1.08, 1], duration:900, ease:"outBack(1.6)"}, t);
    A.add(q(el, ".qt-mark"), {opacity:[0, 1], translateY:[60, 0], scale:[.6, 1], duration:1100, ease:"outExpo"}, t + 100);
    var e = SK.text(A, q(el, ".qt-x"), t + 250);
    SK.emph(A, el, e);
    SK.fade(A, q(el, ".qt-src"), e, 20);
    return e;
  }
};
LAY.image = {
  html: function(it){
    return '<div class="im-art"><i class="im-bg ring-me"></i>' + icon(it.icon || it.image || it.emoji, "big") + "</div>" +
      '<div class="im-body">' + kicker(it) + fitSpec("im-t", 104, 54, 1) + rt(it.title) + "</div></div>" + fitSpec("im-x", 42, 26, 0) + rt(it.text) + "</div></div></div>";
  },
  enter: function(A, el, it, t){
    A.add(q(el, ".im-bg"), {opacity:[0, 1], scale:[.6, 1], duration:1300, ease:"outExpo"}, t);
    SK.drawIn(A, qa(el, ".im-bg .ring path"), t + 100, 900);
    SK.drawIn(A, qa(el, ".im-art .ic .dr"), t + 250, 1100, 120);
    A.add(qa(el, ".im-art .icf, .im-art .icd"), {opacity:[0, 1], duration:700, ease:"linear"}, t + 1000);
    A.add(q(el, ".im-art .emo"), {opacity:[0, 1], scale:[.3, 1], duration:900, ease:"outBack(2)"}, t + 250);
    SK.fade(A, q(el, ".im-body .kicker"), t + 300, 16);
    var e = SK.text(A, q(el, ".im-t"), t + 420);
    SK.emph(A, el, e);
    SK.fade(A, q(el, ".im-x .tx"), e - 150, 20);
    return e;
  }
};
LAY.quiz = {
  count: function(it){ return it.reveal === false ? 0 : 1; }, always: true, reveal: true,
  html: function(it){
    var ch = arr(it.choices).slice(0, 4), ans = +it.answer || 0, marks = WORLD.choiceMarks || ["1", "2", "3", "4"];
    return '<div class="qz-kicker">' + esc(it.kicker != null ? it.kicker : label("quiz", "QUIZ")) + "</div>" +
      fitSpec("qz-q", 80, 44, .5) + rt(it.q || it.title) + "</div></div>" +
      '<div class="qz-ch n' + ch.length + '">' + ch.map(function(c, i){
        return '<div class="ch-i' + (i === ans ? " ok" : "") + '"><div class="chbox' + (i === ans ? " ring-me" : "") + '"><span class="ch-k">' + esc(marks[i] || i + 1) + "</span>" +
          fitSpec("ch-t", ch.length <= 2 ? 64 : 46, 24, .5) + rt(c) + '</div></div><span class="ch-mark">' + (i === ans ? esc(label("correctMark", "✔ " + label("answer", "정답"))) : "") + "</span></div></div>";
      }).join("") + "</div>" +
      (it.explain ? '<div class="qz-ex" data-b="0"><b>' + esc(label("answer", "정답")) + "</b>" + fitSpec("qz-ex-x", 36, 22, .5) + rt(it.explain) + "</div></div></div>" : "");
  },
  enter: function(A, el, it, t){
    SK.fade(A, q(el, ".qz-kicker"), t, 16);
    var e = SK.text(A, q(el, ".qz-q"), t + 100, {fast:1});
    SK.emph(A, q(el, ".qz-q"), e);
    var c = qa(el, ".ch-i");
    SK.pop(A, c, Math.min(e, t + 700));
    SK.drawIn(A, qa(el, ".chbox .rough path"), Math.min(e, t + 700), 600, 110);
    return e + 300;
  },
  item: function(A, el, it, i, t){
    var wrong = qa(el, ".ch-i:not(.ok)"), ok = q(el, ".ch-i.ok");
    A.add(wrong, {opacity:[1, .3], scale:[1, .97], duration:500, ease:"outQuad"}, t);
    A.add(q(ok, ".chbox"), {scale:[.94, 1], duration:900, ease:"outElastic(1,.55)"}, t + 150);
    A.add(q(ok, ".ch-mark"), {opacity:[0, 1], scale:[2.2, 1], rotate:[-25, -8], duration:600, ease:"outBack(2)"}, t + 300);
    SK.drawIn(A, qa(ok, ".ring path"), t + 150, 700);
    A.add(q(el, ".qz-ex"), {opacity:[0, 1], translateY:[50, 0], duration:900, ease:"outExpo"}, t + 500);
    SK.emph(A, q(el, ".qz-ex"), t + 900);
    return 1200;
  }
};
LAY.end = {
  html: function(it){
    var nx = arr(it.next);
    return fitSpec("en-t", 190, 90, 1) + rt(it.title || label("thanks", "감사합니다")) + "</div></div>" +
      (it.sub ? '<div class="en-sub">' + rt(it.sub) + "</div>" : "") +
      (nx.length ? '<ol class="en-next">' + nx.slice(0, 4).map(function(x, i){ return '<li><b>' + (i + 1) + "</b><span>" + rt(x) + "</span></li>"; }).join("") + "</ol>" : "") +
      (it.qr ? '<div class="en-qr"><div class="qr-box"><i class="f f1"></i><i class="f f2"></i><i class="f f3"></i><span>' + esc(label("qr", "QR")) + '</span></div><div class="qr-cap">' + esc(it.qr) + "</div></div>" : "");
  },
  enter: function(A, el, it, t){
    var e = SK.text(A, q(el, ".en-t"), t + 100);
    SK.emph(A, el, e);
    SK.fade(A, q(el, ".en-sub"), e - 300, 20);
    A.add(qa(el, ".en-next li"), {opacity:[0, 1], translateX:[-40, 0], duration:800, ease:"outExpo", delay:stag(120)}, e);
    A.add(q(el, ".en-qr"), {opacity:[0, 1], scale:[.85, 1], rotate:[4, 0], duration:1000, ease:"outBack(1.6)"}, e - 100);
    return e;
  }
};
var LAYOUT_ALIAS = {title:"cover", "표지":"cover", divider:"section", "big-text":"bigtext", statement:"bigtext", number:"bignumber", stat:"bignumber", vs:"compare", process:"steps", picture:"image", thanks:"end"};
function layoutOf(it){ var l = it.layout || "bigtext"; l = LAYOUT_ALIAS[l] || l; return LAY[l] ? l : "bigtext"; }
function buildsOf(it){
  var L = LAY[layoutOf(it)], n = L.count ? L.count(it) : 0;
  if (!n) return 0;
  if (L.always) return it.build === false && !L.reveal ? 0 : n;
  var flag = it.build != null ? it.build : (WORLD.builds != null ? WORLD.builds : true);
  return flag ? n : 0;
}

/* ---------- render one slide (state = how many builds are shown) ---------- */
function fitAll(el){
  var k = SK.fitScale || 1;
  el.classList.add("fitting");
  qa(el, "[data-fit]").forEach(function(b){
    var f = b.getAttribute("data-fit").split(","), tx = b.firstElementChild;
    if (tx) tx.style.marginTop = "0px";
    S.fitText(b, Math.round(+f[0] * k), Math.round(+f[1] * k));
    var al = +f[2] || 0;
    if (tx && al){ var free = b.clientHeight - tx.offsetHeight; if (free > 0) tx.style.marginTop = Math.floor(free * al) + "px"; }
  });
  el.classList.remove("fitting");
}
function render(parent, it, idx, upto){
  var name = layoutOf(it), L = LAY[name], nb = buildsOf(it);
  var el = S.h("section", {class:"slide L-" + name + (it.align ? " al-" + it.align : "")});
  el.innerHTML = L.html(it, idx) + SK.art(name, it, idx);
  if (q(el, ".hd")) q(el, ".hd").insertAdjacentHTML("beforeend", '<i class="hd-rule"></i>');
  parent.appendChild(el);
  qa(el, "[data-b]").forEach(function(b){ var k = +b.getAttribute("data-b"); if (k < nb && k >= upto) b.classList.add("pre"); });
  if (L.reveal && (upto >= 1 || !nb)) el.classList.add("rev");
  fitAll(el);
  SK.decorate(el, it, idx);
  el.__fit = function(){ fitAll(el); };
  return el;
}
function compose(A, el, it, t, upto, gap){
  var L = LAY[layoutOf(it)], nb = buildsOf(it), cnt = L.count ? L.count(it) : 0, starts = [];
  var ready = L.enter(A, el, it, t);
  A.add(qa(el, ".art .dr"), {strokeDashoffset:[1.1, 0], duration:1000, ease:"inOutQuad", delay:stag(160)}, t + 300);
  A.add(qa(el, ".art.ap, .art .ap"), {opacity:[0, 1], scale:[.7, 1], duration:1000, ease:"outBack(1.6)", delay:stag(120)}, t + 150);
  A.add(qa(el, ".art .icf, .art .icd"), {opacity:[0, 1], duration:600, ease:"linear"}, t + 1100);
  if (!nb){
    for (var i = 0; i < cnt; i++){ var s = ready + i * (L.stagger || 150); A.cur = s; L.item(A, el, it, i, s); }
  } else {
    for (var j = 0; j < Math.min(upto, nb); j++){ var st = A.end() + (gap || 0); starts.push(st); A.cur = st; L.item(A, el, it, j, st); }
  }
  return {starts:starts, end:A.end()};
}

/* ---------- deck chrome: progress, page number, notes, blackout, eraser ---------- */
var chrome = {};
function mountChrome(){
  var st = S.el.stage;
  if (!document.getElementById("dk-ui")){
    st.insertAdjacentHTML("beforeend",
      '<div id="dk-fx"><div id="dk-eraser"><i></i></div></div>' +
      '<div id="dk-ui"><div class="dk-prog"><i></i></div><div class="dk-num"></div></div>' +
      '<div id="dk-note"><div class="nt-l"></div><div class="nt-x"></div></div>' +
      '<div id="dk-black"></div><div id="dk-jump"></div>');
  }
  chrome.ui = document.getElementById("dk-ui"); chrome.bar = q(chrome.ui, ".dk-prog i"); chrome.num = q(chrome.ui, ".dk-num");
  chrome.note = document.getElementById("dk-note"); chrome.black = document.getElementById("dk-black"); chrome.jump = document.getElementById("dk-jump");
  q(chrome.note, ".nt-l").textContent = label("notes", "선생님 메모") + "  ·  N";
}
var uiTimer = null;
function pokeUI(){
  if (!chrome.ui) return;
  chrome.ui.classList.add("on"); clearTimeout(uiTimer);
  uiTimer = setTimeout(function(){ chrome.ui.classList.remove("on"); }, 2600);
}
function updateChrome(){
  var n = ITEMS.length, i = cur.i, nb = buildsOf(ITEMS[i] || {}), frac = n ? (i + (nb ? (cur.k + 1) / (nb + 1) : 1)) / n : 0;
  chrome.bar.style.width = (frac * 100).toFixed(2) + "%";
  chrome.num.textContent = (i + 1) + " / " + n;
  var it = ITEMS[i] || {};
  q(chrome.note, ".nt-x").textContent = it.note ? txt(it.note) : label("noNote", "이 장에는 메모가 없어요.");
  pokeUI();
}

/* ---------- navigation ---------- */
var cur = {i:0, k:0, el:null};
var manual = function(){ return document.body.classList.contains("recording"); };
function dropTimelines(){ S.timelines.forEach(function(x){ try { x.tl.revert(); } catch(e){ try { x.tl.pause(); } catch(e2){} } }); S.timelines.length = 0; S.duration = 0; }
function clearOld(keep){ qa(S.el.scene, ".slide").forEach(function(s){ if (s !== keep) s.remove(); }); }
function go(i, k, mode){
  if (!ITEMS.length) return;
  i = clamp(i, 0, ITEMS.length - 1); k = clamp(k, 0, buildsOf(ITEMS[i]));
  dropTimelines();
  var fx = document.getElementById("dk-eraser");
  if (fx) anime.utils.set(fx, {opacity:0, translateX:-420});
  if (chrome.ui) chrome.ui.style.display = "";
  var old = cur.el && cur.el.parentNode ? cur.el : null;
  clearOld(old);
  var sameSlide = old && cur.i === i;
  if (sameSlide || mode === "back") { if (old) old.remove(); }
  var el = render(S.el.scene, ITEMS[i], i, k);
  var tl = anime.createTimeline({autoplay:false}), A = mkA(tl);
  var t0 = 0;
  if (mode === "enter") t0 = SK.trans(A, sameSlide ? null : old, el, 0);
  var r = compose(A, el, ITEMS[i], t0, k, 0);
  S.timeline(tl, r.end);
  if (mode === "build" && r.starts.length){ tl.seek(r.starts[r.starts.length - 1]); if (!manual()) tl.play(); }
  else if (mode === "back"){ tl.seek(r.end); }
  else if (!manual()) tl.play();
  if (mode === "back" && old && !sameSlide){
    var fade = anime.createTimeline({autoplay:!manual()});
    fade.add(el, {opacity:[0, 1], duration:280, ease:"linear"}, 0);
    S.timeline(fade, 280);
  }
  cur = {i:i, k:k, el:el, tl:tl};
  S.creditManual = true;
  if (S.credit) S.credit(i === ITEMS.length - 1 && k >= buildsOf(ITEMS[i]));
  updateChrome();
}
function next(){
  if (blackOn()){ setBlack(false); return; }
  var nb = buildsOf(ITEMS[cur.i] || {});
  if (cur.k < nb) go(cur.i, cur.k + 1, "build");
  else if (cur.i < ITEMS.length - 1) go(cur.i + 1, 0, "enter");
  else { S.toast(label("lastSlide", "마지막 장이에요")); pokeUI(); }
}
function prev(){
  if (blackOn()){ setBlack(false); return; }
  if (cur.k > 0) go(cur.i, cur.k - 1, "back");
  else if (cur.i > 0) go(cur.i - 1, buildsOf(ITEMS[cur.i - 1]), "back");
  else pokeUI();
}
function blackOn(){ return chrome.black && chrome.black.classList.contains("on"); }
function setBlack(on){ chrome.black.classList.toggle("on", !!on); }
function toggleNote(){ chrome.note.classList.toggle("on"); }
var jumpBuf = "", jumpTimer = null;
function digit(d){
  jumpBuf = (jumpBuf + d).slice(-3); chrome.jump.textContent = jumpBuf; chrome.jump.classList.add("on");
  clearTimeout(jumpTimer); jumpTimer = setTimeout(commitJump, 900);
}
function commitJump(){
  clearTimeout(jumpTimer); chrome.jump.classList.remove("on");
  var n = parseInt(jumpBuf, 10); jumpBuf = "";
  if (n >= 1 && n <= ITEMS.length && n - 1 !== cur.i) go(n - 1, 0, "enter");
}

/* ---------- reel: whole deck as one timeline (🎥 button, render_mp4, DOC.reel) ---------- */
function reel(){
  var tl = anime.createTimeline({autoplay:!manual()}), A = mkA(tl), prevEl = null, t = 0;
  var dwell = +WORLD.reelBuildGap || 1300, hold = +WORLD.reelHold || 2400;
  ITEMS.forEach(function(it, i){
    var el = render(S.el.scene, it, i, buildsOf(it));
    var t0 = SK.trans(A, prevEl, el, t);
    var r = compose(A, el, it, t0, buildsOf(it), dwell);
    t = r.end + hold + (layoutOf(it) === "quiz" ? 600 : 0);
    prevEl = el;
  });
  S.timeline(tl, t);
  cur = {i:ITEMS.length - 1, k:buildsOf(ITEMS[ITEMS.length - 1]), el:prevEl, tl:tl};
  if (chrome.ui) chrome.ui.style.display = "none";
}

/* ---------- print: every slide as one landscape page, final state (Chrome → PDF) ---------- */
function buildPrint(){
  var root = document.getElementById("dk-print");
  if (!root){ root = S.h("div", {id:"dk-print"}); document.body.appendChild(root); }
  root.innerHTML = "";
  root.style.cssText = "display:block;position:absolute;left:-30000px;top:0;width:1920px";
  var bg = "";
  try { var c = document.createElement("canvas"); c.width = W; c.height = H; if (SK.painter) SK.painter(c.getContext("2d"), 0, W, H); bg = c.toDataURL("image/jpeg", .9); } catch(e){ bg = ""; }
  ITEMS.forEach(function(it, i){
    var pg = S.h("div", {class:"pp"});
    if (bg) pg.style.backgroundImage = "url(" + bg + ")";
    root.appendChild(pg);
    render(pg, it, i, buildsOf(it));
  });
  root.style.cssText = "";
}
window.addEventListener("beforeprint", buildPrint);

/* ---------- input ---------- */
var down = null;
function onPointerDown(e){ down = {x:e.clientX, y:e.clientY, t:Date.now()}; }
function onPointerUp(e){
  if (!down || (e.button != null && e.button > 0)) return;
  var t = e.target;
  if (t && t.closest && (t.closest("#ui") || t.closest("#dk-note.on"))) { down = null; return; }
  var dx = e.clientX - down.x, dy = e.clientY - down.y; down = null;
  if (manual()) return;
  if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy)){ if (dx < 0) next(); else prev(); return; }
  if (Math.abs(dx) > 20 || Math.abs(dy) > 20) return;
  if (e.clientX >= window.innerWidth / 2) next(); else prev();
}

window.SHOW = {
  start: function(){
    var fl = WORLD.extraFonts;
    if (fl && D.online === true && !document.getElementById("dk-font")){  /* outside fonts only when the doc opts in (online:true); offline is the default */ var lk = S.h("link", {id:"dk-font", rel:"stylesheet", href:"https://fonts.googleapis.com/css2?family=" + fl + "&display=swap"}); document.head.appendChild(lk); }
    if (SKIN_NAME === "chalkboard") document.documentElement.style.setProperty("--chalk-noise", "url(" + chalkNoise() + ")");
    mountChrome();
    texCache = null;
    if (SK.painter) S.bg(SK.painter);
    if (!SHOW._wired){
      SHOW._wired = true;
      document.addEventListener("pointerdown", onPointerDown);
      document.addEventListener("pointerup", onPointerUp);
      var refit = function(){ qa(S.el.scene, ".slide").forEach(function(s){ if (s.__fit) s.__fit(); }); };
      if (document.fonts && document.fonts.ready){ document.fonts.ready.then(refit); if (document.fonts.addEventListener) document.fonts.addEventListener("loadingdone", refit); }
    }
    cur = {i:0, k:0, el:null};
    if (!ITEMS.length){ S.el.scene.innerHTML = '<div class="dk-empty">DOC.items</div>'; return; }
    if (D.reel || S.recording) reel(); else go(0, 0, "enter");
  },
  onKey: function(e){
    if (e.__dk) return true; e.__dk = 1;
    if (e.ctrlKey || e.metaKey || e.altKey) return false;
    var k = e.key, c = e.code || "";
    if (k === "ArrowRight" || k === "ArrowDown" || k === "PageDown" || k === " " || k === "Spacebar"){ e.preventDefault(); next(); return true; }
    if (k === "Enter"){ e.preventDefault(); if (jumpBuf) commitJump(); else next(); return true; }
    if (k === "ArrowLeft" || k === "ArrowUp" || k === "PageUp" || k === "Backspace"){ e.preventDefault(); prev(); return true; }
    if (k === "Home"){ go(0, 0, "enter"); return true; }
    if (k === "End"){ go(ITEMS.length - 1, 0, "enter"); return true; }
    if (/^[0-9]$/.test(k)){ digit(k); return true; }
    if (c === "KeyN" || k === "n" || k === "N"){ toggleNote(); return true; }
    if (c === "KeyB" || k === "b" || k === "B" || k === "."){ setBlack(!blackOn()); return true; }
    if (k === "Escape"){ setBlack(false); chrome.note.classList.remove("on"); return true; }
    return false;
  },
  toText: function(){
    var it = ITEMS[cur.i] || {};
    return "slide " + (cur.i + 1) + "/" + ITEMS.length + " · " + layoutOf(it) + " · " + plain(it.title || it.q || it.text || "") +
      " · build " + cur.k + "/" + buildsOf(it) + " · notes " + (chrome.note && chrome.note.classList.contains("on") ? "on" : "off") + " · black " + (blackOn() ? "on" : "off");
  },
  go: function(i, k){ go(i, k || 0, "enter"); },
  printPrep: buildPrint
};
})();
