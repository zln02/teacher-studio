/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* subject-intro — 과목 소개 영상 (35~45s, 16:9)
   Beats: hook → subject reveal → "만날 것" keyword scenes (2~6) → teacher message → closing card.
   Skins are separate worlds: science-neon · korean-brush · english-news (own painter, art, type, transitions).
   All text comes from DOC; icons are picked by name (item.icon) from the line-art library below. */
(function(){
"use strict";
var A = window.anime, S = window.STAGE, D = window.DOC || {};
var NS = "http://www.w3.org/2000/svg";
var R = {};          // runtime refs (root, layers, colors, plan)
var FITS = [];

/* ---------- small helpers ---------- */
function str(v){ return v == null ? "" : String(v); }
function obj(v){ return v && typeof v === "object" ? v : {}; }
function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }
function el(tag, cls, parent, styleText){
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (styleText) e.style.cssText = styleText;
  if (parent) parent.appendChild(e);
  return e;
}
function svg(tag, attrs, parent){
  var e = document.createElementNS(NS, tag);
  for (var k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function cssv(name, dflt){
  var v = getComputedStyle(document.documentElement).getPropertyValue("--" + name);
  v = v ? v.trim() : "";
  return v || dflt;
}
function rng(seed){
  var s = seed >>> 0;
  return function(){
    s = (s + 0x6D2B79F5) >>> 0;
    var t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function smooth(x){ x = clamp(x, 0, 1); return x * x * (3 - 2 * x); }
function win(t, a, b, fade){ return smooth((t - a) / fade) * (1 - smooth((t - b) / fade)); }
function pad2(n){ return n < 10 ? "0" + n : String(n); }

/* text box: absolutely positioned fixed-size frame (.si-box, centers vertically) + inner text block (.si-t, returned).
   Auto-fits with STAGE.fitText on a plain clone, and re-fits when web fonts arrive. */
function box(parent, cls, text, x, y, w, h, maxPx, minPx){
  var b = el("div", "si-box word-break " + (cls || ""), parent,
    "left:" + x + "px;top:" + y + "px;width:" + w + "px;height:" + h + "px");
  var e = el("div", "si-t", b);
  e.textContent = str(text);
  if (maxPx){ var f = [b, maxPx, minPx || 28, str(text)]; FITS.push(f); fitOne(f); }
  return e;
}
function fitOne(f){
  var b = f[0], c = b.cloneNode(false), t = el("div", "si-t", c);
  t.textContent = f[3];
  c.style.visibility = "hidden"; c.style.transform = "none"; c.style.opacity = "1"; c.style.clipPath = "none";
  b.parentNode.appendChild(c);
  var size = S.fitText(c, f[1], f[2]);
  c.parentNode.removeChild(c);
  b.style.fontSize = size + "px";
}
function refit(){ FITS.forEach(function(f){ if (f[0].parentNode) fitOne(f); }); }
function chars(e){ return S.split(e); }
function words(e){ return S.split(e, "word"); }
function loadFonts(){
  var fams = D.fonts || [];
  if (fams.length && !document.getElementById("si-fonts")){
    var l = el("link", "", document.head);
    l.id = "si-fonts"; l.rel = "stylesheet";
    l.href = "https://fonts.googleapis.com/css2?" + fams.map(function(f){ return "family=" + String(f).replace(/ /g, "+"); }).join("&") + "&display=swap";
  }
  if (document.fonts && document.fonts.addEventListener) document.fonts.addEventListener("loadingdone", refit);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(refit);
}

/* beat = scene wrapper (.si-sc: entrance props) + inner (.si-o: exit props) — one tween per prop per element */
function beat(cls){
  var sc = el("div", "si-sc " + (cls || ""), R.stack);
  var o = el("div", "si-o", sc);
  return {sc: sc, o: o};
}
/* tl.add + apply each [from, …] value now, so elements wait in their start state (anime renders tweens only once reached) */
function add(tl, targets, params, t){
  var init = {}, has = false;
  for (var k in params){
    var v = params[k];
    if (k !== "delay" && Array.isArray(v) && v.length > 1 && typeof v[0] !== "object"){ init[k] = v[0]; has = true; }
  }
  if (has) A.utils.set(targets, init);
  tl.add(targets, params, Math.max(0, t));
}
function on(tl, target, t){ add(tl, target, {opacity: [0, 1], duration: 1, ease: "linear"}, Math.max(0, t)); }
function off(tl, target, t){ add(tl, target, {opacity: [1, 0], duration: 1, ease: "linear"}, Math.max(0, t)); }

/* ---------- original line-art icon library (200x200 viewBox) ---------- */
function C(cx, cy, r){ return "M" + (cx - r) + " " + cy + " a" + r + " " + r + " 0 1 0 " + (2 * r) + " 0 a" + r + " " + r + " 0 1 0 " + (-2 * r) + " 0"; }
function E(cx, cy, rx, ry){ return "M" + (cx - rx) + " " + cy + " a" + rx + " " + ry + " 0 1 0 " + (2 * rx) + " 0 a" + rx + " " + ry + " 0 1 0 " + (-2 * rx) + " 0"; }
function helix(phase){
  var d = "", n = 40;
  for (var i = 0; i <= n; i++){
    var y = 22 + i * (156 / n), x = 100 + 38 * Math.sin(i / n * Math.PI * 2.5 + phase);
    d += (i ? " L" : "M") + x.toFixed(1) + " " + y.toFixed(1);
  }
  return d;
}
function rungs(){
  var out = [];
  for (var i = 1; i < 10; i++){
    var k = i / 10 * 40, y = 22 + k * (156 / 40), a = k / 40 * Math.PI * 2.5;
    out.push("M" + (100 + 38 * Math.sin(a)).toFixed(1) + " " + y.toFixed(1) + " L" + (100 + 38 * Math.sin(a + Math.PI)).toFixed(1) + " " + y.toFixed(1));
  }
  return out;
}
var ICONS = {
  beaker: ["M76 28 H124", "M86 28 V80 L44 160 Q38 172 52 172 H148 Q162 172 156 160 L114 80 V28", "M60 132 Q80 124 100 132 T140 132", C(96, 152, 7), C(118, 112, 5)],
  atom: [C(100, 100, 10), [E(100, 100, 84, 30), 0], [E(100, 100, 84, 30), 60], [E(100, 100, 84, 30), -60]],
  dna: [helix(0), helix(Math.PI)].concat(rungs()),
  planet: [C(100, 104, 46), [E(100, 104, 90, 22), -16], "M42 40 l4 10 l10 4 l-10 4 l-4 10 l-4 -10 l-10 -4 l10 -4 Z", C(160, 168, 4)],
  magnet: ["M54 36 H86 V108 A14 14 0 0 0 114 108 V36 H146 V108 A46 46 0 0 1 54 108 Z", "M54 62 H86", "M114 62 H146"],
  leaf: ["M40 160 C40 80 90 36 166 34 C164 110 120 160 40 160 Z", "M40 160 C80 120 110 90 140 62", "M82 120 L80 94", "M106 96 L128 100"],
  bolt: ["M112 20 L52 112 H96 L84 180 L148 84 H104 Z"],
  book: ["M100 52 C80 40 52 38 26 44 V160 C52 154 80 156 100 168 C120 156 148 154 174 160 V44 C148 38 120 40 100 52 Z", "M100 52 V168", "M44 72 C60 70 74 72 86 78", "M44 98 C60 96 74 98 86 104", "M114 78 C126 72 140 70 156 72", "M114 104 C126 98 140 96 156 98"],
  brush: ["M138 24 L156 42 L94 114 L76 96 Z", "M76 96 L94 114 C90 140 72 162 40 174 C46 146 54 114 76 96 Z", "M110 58 L122 70"],
  speech: ["M40 44 H160 Q172 44 172 56 V120 Q172 132 160 132 H92 L60 162 L66 132 H40 Q28 132 28 120 V56 Q28 44 40 44 Z", C(70, 88, 6), C(100, 88, 6), C(130, 88, 6)],
  paper: ["M60 28 H124 L150 54 V172 H60 Z", "M124 28 V54 H150", "M80 84 H130", "M80 108 H130", "M80 132 H112"],
  pen: ["M144 28 L172 56 L76 152 L40 164 L52 128 Z", "M128 44 L156 72", "M52 128 L76 152"],
  globe: [C(100, 100, 72), E(100, 100, 30, 72), "M28 100 H172", "M37.6 64 H162.4", "M37.6 136 H162.4"],
  mic: ["M78 44 A22 22 0 0 1 122 44 V100 A22 22 0 0 1 78 100 Z", "M56 94 A44 44 0 0 0 144 94", "M100 138 V168", "M72 170 H128"],
  chat: ["M30 50 H120 Q130 50 130 60 V104 Q130 114 120 114 H70 L48 136 L52 114 H30 Q20 114 20 104 V60 Q20 50 30 50 Z", "M146 84 H170 Q180 84 180 94 V138 Q180 148 170 148 H162 L166 170 L144 148 H108 Q98 148 98 138 V128"],
  plane: ["M24 96 L176 28 L132 172 L100 116 Z", "M100 116 L176 28", "M100 116 L96 150 L118 132"],
  music: ["M80 150 V48 L156 32 V132", E(62, 150, 19, 14), E(138, 134, 19, 14), "M80 74 L156 58"],
  numbers: ["M40 40 H160 V160 H40 Z", "M100 40 V160", "M40 100 H160", "M58 70 H82", "M70 58 V82", "M118 70 H142", "M60 120 L80 140", "M80 120 L60 140", "M118 124 H142", "M118 136 H142"],
  bulb: ["M70 112 C50 96 50 74 54 64 C62 40 82 30 100 30 C118 30 138 40 146 64 C150 74 150 96 130 112 C122 120 120 128 120 138 H80 C80 128 78 120 70 112 Z", "M80 154 H120", "M86 170 H114", "M92 92 L100 110 L108 92"],
  heart: ["M100 168 C60 136 28 108 28 74 C28 50 46 34 68 34 C82 34 94 42 100 54 C106 42 118 34 132 34 C154 34 172 50 172 74 C172 108 140 136 100 168 Z"],
  star: ["M100 24 L121 74 L174 78 L134 112 L146 166 L100 138 L54 166 L66 112 L26 78 L79 74 Z"],
  people: [C(72, 70, 22), C(134, 80, 17), "M30 168 C30 128 50 110 72 110 C94 110 114 128 114 168", "M120 168 C120 140 128 124 142 120 C160 124 172 140 172 168"],
  palette: ["M100 28 C150 28 176 64 176 96 C176 124 156 132 140 128 C124 124 116 134 122 148 C128 164 118 174 100 174 C56 174 24 140 24 100 C24 60 56 28 100 28 Z", C(64, 92, 9), C(88, 60, 9), C(126, 60, 9), C(66, 132, 9)],
  ball: [C(100, 100, 72), "M28 100 C60 86 140 86 172 100", "M100 28 C80 60 80 140 100 172", "M100 28 C120 60 120 140 100 172"],
  clock: [C(100, 100, 72), "M100 56 V100 L132 118", "M100 36 V44", "M164 100 H156", "M100 164 V156", "M36 100 H44"],
  school: ["M30 90 L100 34 L170 90", "M46 78 V166 H154 V78", "M86 166 V122 H114 V166", "M62 100 H82 V118 H62 Z", "M118 100 H138 V118 H118 Z"],
  hanok: ["M18 88 Q100 40 182 88", "M34 84 Q28 70 18 66", "M166 84 Q172 70 182 66", "M44 88 V166 H156 V88", "M44 124 H156", "M100 88 V166", "M72 88 V166", "M128 88 V166"],
  magnifier: [C(86, 86, 50), "M122 122 L170 170", "M62 70 A28 28 0 0 1 86 58"],
  map: ["M24 48 L70 32 L130 52 L176 36 V152 L130 168 L70 148 L24 164 Z", "M70 32 V148", "M130 52 V168", "M92 96 C92 80 112 80 112 96 C112 108 102 116 102 124 C102 116 92 108 92 96 Z"],
  wave: ["M20 80 C40 60 60 60 80 80 S120 100 140 80 S170 60 180 70", "M20 120 C40 100 60 100 80 120 S120 140 140 120 S170 100 180 110"],
  gear: [C(100, 100, 26), "M100 30 L112 30 L116 50 L132 58 L150 46 L158 54 L146 72 L152 88 L172 92 V108 L152 112 L146 128 L158 146 L150 154 L132 142 L116 150 L112 170 H88 L84 150 L68 142 L50 154 L42 146 L54 128 L48 112 L28 108 V92 L48 88 L54 72 L42 54 L50 46 L68 58 L84 50 L88 30 Z"]
};
/* build an icon: returns {svg, paths[]} ; style per skin via CSS (.si-ico path) */
function icon(parent, name, x, y, size, cls){
  var def = ICONS[str(name).toLowerCase()] || ICONS.star;
  var s = svg("svg", {viewBox: "0 0 200 200", width: size, height: size, "class": "si-ico " + (cls || "")}, parent);
  s.style.left = x + "px"; s.style.top = y + "px";
  var g = svg("g", {}, s), paths = [];
  def.forEach(function(p){
    var d = typeof p === "string" ? p : p[0], rot = typeof p === "string" ? 0 : p[1];
    var a = {d: d};
    if (rot) a.transform = "rotate(" + rot + " 100 100)";
    paths.push(svg("path", a, g));
  });
  return {svg: s, g: g, paths: paths};
}
function drawIn(tl, paths, t, dur, stag, ease){
  var d = A.svg.createDrawable(paths);
  add(tl, d, {draw: ["0 0", "0 1"], duration: dur, delay: A.stagger(stag || 0), ease: ease || "inOutQuad"}, t);
  return d;
}

/* ---------- plan ---------- */
function makePlan(n){
  var p = {};
  p.per = clamp(Math.round(20000 / Math.max(n, 1)), 4000, 6000);
  p.hook = 0; p.reveal = 5600; p.meet = 12000; p.items = 12900;
  p.msg = p.items + n * p.per; p.close = p.msg + 6000; p.total = p.close + 5200;
  p.itemAt = function(i){ return p.items + i * p.per; };
  return p;
}
function closingInfo(){
  var c = obj(D.closing);
  return [c.school, c.grade, c.teacher].map(str).filter(function(s){ return s.trim().length > 0; });
}

/* ======================================================================
   SKIN 1 · science-neon — dark lab, neon line drawings, flicker + scan wipes
   ====================================================================== */
var NEON = {
  painter: function(ctx, t, W, H){
    var c = R.c, P = R.plan, ts = t * 1000;
    var g = ctx.createRadialGradient(W / 2, H * 0.45, 80, W / 2, H * 0.5, W * 0.75);
    g.addColorStop(0, c.bg2); g.addColorStop(1, c.bg1);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    var hz = 720, pulse = 0.6 + 0.4 * win(ts, P.reveal + 600, P.meet, 500);
    ctx.strokeStyle = c.primary; ctx.lineWidth = 1.5;
    for (var i = -14; i <= 14; i++){
      ctx.globalAlpha = 0.09 * pulse;
      ctx.beginPath(); ctx.moveTo(W / 2 + i * 36, hz); ctx.lineTo(W / 2 + i * 260, H); ctx.stroke();
    }
    var off = (t * 0.35) % 1;
    for (var k = 0; k < 14; k++){
      var z = (k + off) / 14, y = hz + (H - hz) * z * z;
      ctx.globalAlpha = (0.03 + 0.14 * z) * pulse;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
    var hg = ctx.createLinearGradient(0, hz - 60, 0, hz + 4);
    hg.addColorStop(0, "rgba(0,0,0,0)"); hg.addColorStop(1, c.primary);
    ctx.globalAlpha = 0.16 * pulse; ctx.fillStyle = hg; ctx.fillRect(0, hz - 60, W, 64);
    var r = rng(7);
    for (var p = 0; p < 90; p++){
      var px = (r() * W + t * (8 + r() * 26)) % W, py = (r() * H - t * (6 + r() * 18) % H + H) % H;
      ctx.globalAlpha = (0.18 + 0.32 * (0.5 + 0.5 * Math.sin(t * (1 + r() * 2) + p))) * (r() < 0.25 ? 1 : 0.5);
      ctx.fillStyle = r() < 0.7 ? c.primary : c.accent;
      ctx.beginPath(); ctx.arc(px, py, 1 + r() * 2.2, 0, 6.283); ctx.fill();
    }
    var sy = ((t / 6.5) % 1) * (H + 300) - 150, sg = ctx.createLinearGradient(0, sy - 120, 0, sy + 120);
    sg.addColorStop(0, "rgba(0,0,0,0)"); sg.addColorStop(0.5, c.primary); sg.addColorStop(1, "rgba(0,0,0,0)");
    ctx.globalAlpha = 0.045; ctx.fillStyle = sg; ctx.fillRect(0, sy - 120, W, 240);
    var v = ctx.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, W * 0.72);
    v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,0.7)");
    ctx.globalAlpha = 1; ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  },
  flickerOut: function(tl, target, t){ add(tl, target, {opacity: [1, 0.1, 1, 0, 0.7, 0], duration: 460, ease: "linear"}, t - 460); },
  hook: function(tl, P){
    var h = obj(D.hook), w = obj(D.world), b = beat("neon-hook");
    on(tl, b.sc, 0);
    var deco = svg("svg", {viewBox: "0 0 1920 1080", width: 1920, height: 1080, "class": "si-full neon-deco"}, b.o);
    var rg = svg("g", {"class": "neon-spin"}, deco), orbits = [];
    [0, 60, 120].forEach(function(a){ orbits.push(svg("path", {d: E(960, 540, 560, 170), transform: "rotate(" + a + " 960 540)"}, rg)); });
    drawIn(tl, orbits, 900, 1600, 220, "inOutSine");
    add(tl, rg, {rotate: [0, 50], duration: P.reveal, ease: "linear"}, 0);
    if (w.hookTag || h.kicker){
      var k = box(b.o, "neon-kicker", (w.hookTag ? w.hookTag + "  " : "") + str(h.kicker), 120, 104, 1680, 60);
      add(tl, k, {opacity: [0, 1], translateX: [-30, 0], duration: 700, ease: "outExpo"}, 250);
    }
    var q = box(b.o, "neon-hook-text", h.text, 160, 290, 1600, 500, 150, 64);
    var cs = chars(q), caretW = el("span", "neon-caretw", q), caret = el("span", "neon-caret", caretW);
    add(tl, cs, {opacity: [0, 1], duration: 30, delay: A.stagger(55), ease: "linear"}, 650);
    add(tl, caretW, {opacity: [0, 1], duration: 1, ease: "linear"}, 650 + cs.length * 55);
    R.loops.push(A.animate(caret, {opacity: [1, 1, 0, 0], duration: 900, loop: true, ease: "linear"}));
    NEON.flickerOut(tl, b.o, P.reveal);
  },
  reveal: function(tl, P){
    var s = obj(D.subject), b = beat("neon-reveal"), t0 = P.reveal;
    on(tl, b.sc, t0);
    var deco = svg("svg", {viewBox: "0 0 1920 1080", width: 1920, height: 1080, "class": "si-full neon-deco2"}, b.o);
    var ring = svg("path", {d: C(960, 540, 420), "class": "neon-ring"}, deco);
    var ring2 = svg("path", {d: C(960, 540, 372), "class": "neon-ring2"}, deco);
    drawIn(tl, [ring], t0 + 100, 1100, 0, "inOutQuart");
    drawIn(tl, [ring2], t0 + 400, 1300, 0, "inOutQuart");
    var spin = svg("g", {"class": "neon-spin"}, deco);
    svg("circle", {cx: 960, cy: 120, r: 12, "class": "neon-electron"}, spin);
    svg("circle", {cx: 960, cy: 960, r: 8, "class": "neon-electron b"}, spin);
    add(tl, spin, {rotate: [0, 300], opacity: [0, 1], duration: P.meet - t0, ease: "linear"}, t0 + 600);
    if (s.sub){
      var sub = box(b.o, "neon-sub", s.sub, 360, 300, 1200, 60, 40, 24);
      add(tl, sub, {opacity: [0, 1], letterSpacing: ["0.6em", "0.28em"], duration: 1000, ease: "outExpo"}, t0 + 1300);
    }
    var name = box(b.o, "neon-name", s.name, 260, 380, 1400, 300, 260, 110);
    add(tl, name, {opacity: [0, 1, 0.12, 0.9, 0.25, 1], scale: [1.06, 1], duration: 1000, ease: "linear"}, t0 + 700);
    if (s.en){
      var en = box(b.o, "neon-en", s.en, 260, 690, 1400, 70, 46, 24);
      add(tl, en, {opacity: [0, 1], letterSpacing: ["0.05em", "0.62em"], duration: 1600, ease: "outExpo"}, t0 + 1500);
    }
    add(tl, b.o, {opacity: [1, 0], scale: [1, 1.22], filter: ["blur(0px)", "blur(14px)"], duration: 520, ease: "inQuad"}, P.meet - 520);
  },
  meet: function(tl, P, n){
    var w = obj(D.world), b = beat("neon-meet"), t0 = P.meet;
    on(tl, b.sc, t0);
    var lab = box(b.o, "neon-meet-label", w.meet, 120, 86, 1100, 64);
    add(tl, chars(lab), {opacity: [0, 1], translateY: [24, 0], duration: 500, delay: A.stagger(28), ease: "outExpo"}, t0 + 100);
    var line = el("div", "neon-meet-line", b.o);
    add(tl, line, {scaleX: [0, 1], duration: 900, ease: "outExpo"}, t0 + 200);
    var cnt = el("div", "neon-count", b.o);
    for (var i = 0; i < n; i++){
      var outer = el("span", "", cnt), sp = el("span", "", outer);
      sp.textContent = pad2(i + 1) + " / " + pad2(n);
      add(tl, sp, {opacity: [0, 1], translateY: ["60%", "0%"], duration: 500, ease: "outExpo"}, P.itemAt(i) + 200);
      if (i < n - 1) add(tl, outer, {opacity: [1, 0], duration: 200, ease: "linear"}, P.itemAt(i + 1) - 200);
    }
    add(tl, b.o, {opacity: [1, 0], duration: 400, ease: "linear"}, P.msg - 400);
    R.neonCount = cnt;
  },
  item: function(tl, P, i, it, n){
    var a0 = i > 0 ? P.itemAt(i) - 250 : P.itemAt(i);   /* internal choreography starts with the incoming transition */
    var b = beat("neon-item"), t0 = P.itemAt(i), t1 = t0 + P.per;
    var hue = ["primary", "accent", "neon3"][i % 3];
    b.sc.setAttribute("data-hue", hue);
    var wipeIn = i > 0;
    if (wipeIn){
      on(tl, b.sc, t0 - 320);
      add(tl, b.sc, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 640, ease: "inOutCubic"}, t0 - 320);
    } else on(tl, b.sc, t0);
    var frame = svg("svg", {viewBox: "0 0 200 200", width: 520, height: 520, "class": "si-ico neon-frame"}, b.o);
    frame.style.left = "260px"; frame.style.top = "280px";
    var fr = [svg("path", {d: C(100, 100, 96)}, frame), svg("path", {d: "M100 0 V12 M200 100 H188 M100 200 V188 M0 100 H12"}, frame)];
    drawIn(tl, fr, a0 + 60, 800, 120, "inOutCubic");
    var floatW = el("div", "si-float", b.o);
    var ic = icon(floatW, it.icon, 340, 360, 360, "neon-icon");
    drawIn(tl, ic.paths, a0 + 260, 1100, 110, "inOutQuad");
    add(tl, floatW, {translateY: [10, -14], duration: P.per, ease: "inOutSine"}, t0);
    var num = box(b.o, "neon-num", pad2(i + 1) + " ───", 900, 270, 600, 50);
    add(tl, num, {opacity: [0, 1], translateX: [-24, 0], duration: 600, ease: "outExpo"}, a0 + 250);
    var word = box(b.o, "neon-word", it.word, 900, 330, 900, 250, 210, 90);
    add(tl, chars(word), {translateY: ["108%", "0%"], duration: 900, delay: A.stagger(45), ease: "outExpo"}, a0 + 380);
    var bar = el("div", "neon-bar", b.o, "left:904px;top:592px");
    add(tl, bar, {scaleX: [0, 1], duration: 800, ease: "outExpo"}, a0 + 700);
    var line = box(b.o, "neon-line", it.line, 900, 620, 900, 170, 50, 30);
    add(tl, words(line), {opacity: [0, 1], translateY: [22, 0], filter: ["blur(6px)", "blur(0px)"], duration: 700, delay: A.stagger(60), ease: "outCubic"}, a0 + 950);
    if (i < n - 1){
      add(tl, b.o, {clipPath: ["inset(0% 0% 0% 0%)", "inset(0% 0% 0% 100%)"], duration: 640, ease: "inOutCubic"}, t1 - 320);
      var scan = el("div", "neon-scan", R.fg);
      add(tl, scan, {translateX: [-160, 2080], opacity: [0, 1, 1, 1, 1, 0], duration: 640, ease: "inOutCubic"}, t1 - 320);
    } else NEON.flickerOut(tl, b.o, t1);
  },
  message: function(tl, P){
    var m = obj(D.message), b = beat("neon-msg"), t0 = P.msg;
    on(tl, b.sc, t0);
    var deco = svg("svg", {viewBox: "0 0 1920 1080", width: 1920, height: 1080, "class": "si-full neon-brackets"}, b.o);
    var br = [svg("path", {d: "M300 290 H220 V790 H300"}, deco), svg("path", {d: "M1620 290 H1700 V790 H1620"}, deco)];
    drawIn(tl, br, t0 + 150, 900, 0, "inOutCubic");
    if (m.label){
      var lab = box(b.o, "neon-msg-label", m.label, 360, 300, 1200, 70, 40, 24);
      add(tl, lab, {opacity: [0, 1, 0.3, 1], duration: 600, ease: "linear"}, t0 + 500);
    }
    var tx = box(b.o, "neon-msg-text", m.text, 320, 390, 1280, 340, 86, 40);
    add(tl, words(tx), {opacity: [0, 1], translateY: [26, 0], filter: ["blur(10px)", "blur(0px)"], duration: 800, delay: A.stagger(80), ease: "outCubic"}, t0 + 800);
    NEON.flickerOut(tl, b.o, P.close);
  },
  closing: function(tl, P){
    var s = obj(D.subject), cl = obj(D.closing), b = beat("neon-close"), t0 = P.close;
    on(tl, b.sc, t0);
    var crt = el("div", "neon-crt", b.o);
    add(tl, crt, {scaleX: [0, 1], duration: 320, ease: "outExpo"}, t0);
    add(tl, crt, {scaleY: [0.006, 1], duration: 460, ease: "outExpo"}, t0 + 300);
    var glow = el("div", "si-full", crt);
    var name = box(glow, "neon-name close", s.name, 260, 300, 1400, 240, 190, 90);
    R.loops.push(A.animate(glow, {opacity: [1, 0.82], duration: 1300, loop: true, alternate: true, ease: "inOutSine"}));
    if (cl.line){
      var ln = box(crt, "neon-close-line", cl.line, 260, 560, 1400, 100, 58, 30);
      add(tl, ln, {opacity: [0, 1], translateY: [20, 0], duration: 700, ease: "outExpo"}, t0 + 900);
    }
    var info = closingInfo();
    if (info.length){
      var row = el("div", "neon-info-row", crt);
      var l1 = el("i", "l", row), it = el("span", "", row), l2 = el("i", "r", row);
      it.textContent = info.join("   ·   ");
      add(tl, it, {opacity: [0, 1], letterSpacing: ["0.4em", "0.14em"], duration: 900, ease: "outExpo"}, t0 + 1200);
      add(tl, [l1, l2], {scaleX: [0, 1], duration: 900, ease: "outExpo"}, t0 + 1300);
    }
    var orb = svg("svg", {viewBox: "0 0 1920 1080", width: 1920, height: 1080, "class": "si-full neon-deco"}, b.o);
    var og = svg("g", {"class": "neon-spin"}, orb), op = [];
    [20, -20].forEach(function(a){ op.push(svg("path", {d: E(960, 430, 640, 120), transform: "rotate(" + a + " 960 430)"}, og)); });
    og.style.transformOrigin = "960px 430px";
    orb.parentNode.insertBefore(orb, orb.parentNode.firstChild);
    drawIn(tl, op, t0 + 700, 1600, 200, "inOutSine");
    add(tl, og, {rotate: [0, 18], duration: 5200, ease: "linear"}, t0 + 700);
  }
};

/* ======================================================================
   SKIN 2 · korean-brush — 한지 paper, ink spread, brush stroke, 낙관 stamp
   ====================================================================== */
function paperTexture(c){
  var cv = document.createElement("canvas"); cv.width = 1920; cv.height = 1080;
  var x = cv.getContext("2d"), r = rng(1234);
  var g = x.createLinearGradient(0, 0, 1920, 1080);
  g.addColorStop(0, c.bg1); g.addColorStop(1, c.bg2);
  x.fillStyle = g; x.fillRect(0, 0, 1920, 1080);
  var small = document.createElement("canvas"); small.width = 480; small.height = 270;
  var sx = small.getContext("2d"), id = sx.createImageData(480, 270);
  for (var i = 0; i < id.data.length; i += 4){
    var v = r() * 255;
    id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 26;
  }
  sx.putImageData(id, 0, 0);
  x.globalCompositeOperation = "multiply";
  x.imageSmoothingEnabled = true; x.drawImage(small, 0, 0, 1920, 1080);
  x.globalCompositeOperation = "source-over";
  x.strokeStyle = c.text; x.lineCap = "round";
  for (var f = 0; f < 900; f++){
    var fx = r() * 1920, fy = r() * 1080, len = 10 + r() * 60, a = r() * 6.283;
    x.globalAlpha = 0.025 + r() * 0.05; x.lineWidth = 0.6 + r() * 1.2;
    x.beginPath(); x.moveTo(fx, fy);
    x.quadraticCurveTo(fx + Math.cos(a + 1) * len * 0.6, fy + Math.sin(a + 1) * len * 0.6, fx + Math.cos(a) * len, fy + Math.sin(a) * len);
    x.stroke();
  }
  for (var s = 0; s < 40; s++){
    x.globalAlpha = 0.03; x.fillStyle = "#ffffff";
    x.beginPath(); x.arc(r() * 1920, r() * 1080, 30 + r() * 120, 0, 6.283); x.fill();
  }
  var v = x.createRadialGradient(960, 540, 300, 960, 540, 1150);
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(60,40,10,0.22)");
  x.globalAlpha = 1; x.fillStyle = v; x.fillRect(0, 0, 1920, 1080);
  return cv;
}
function ridge(seed, base, amp, t, speed){
  var r = rng(seed), k = [r() * 6, r() * 6, r() * 6], pts = [];
  for (var x = -20; x <= 1940; x += 20){
    var u = x / 1920 + t * speed;
    pts.push([x, base - amp * (0.55 * Math.sin(u * 5.1 + k[0]) + 0.3 * Math.sin(u * 11.7 + k[1]) + 0.15 * Math.sin(u * 23.3 + k[2]))]);
  }
  return pts;
}
var BRUSH = {
  painter: function(ctx, t, W, H){
    var c = R.c, P = R.plan, ts = t * 1000;
    if (!R.paper) R.paper = paperTexture(c);
    ctx.drawImage(R.paper, 0, 0);
    var sun = 0.25 + 0.75 * Math.max(win(ts, P.reveal + 800, P.meet, 700), win(ts, P.close + 300, P.total + 9e9, 900));
    ctx.globalAlpha = 0.22 * sun; ctx.fillStyle = c.accent;
    ctx.beginPath(); ctx.arc(1530, 250, 120, 0, 6.283); ctx.fill();
    var lift = 0.55 + 0.45 * Math.max(win(ts, P.close, P.total + 9e9, 800), 1 - smooth((ts - P.hook - 4000) / 1600));
    var layers = [[11, 860, 90, 0.004, 0.10], [23, 930, 70, 0.008, 0.16], [37, 1000, 60, 0.014, 0.24]];
    layers.forEach(function(L){
      var pts = ridge(L[0], L[1] + (1 - lift) * 80, L[2], t, L[3]);
      var g = ctx.createLinearGradient(0, L[1] - L[2] - 40, 0, H);
      g.addColorStop(0, c.text); g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.globalAlpha = L[4] * lift; ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(-20, H);
      pts.forEach(function(p){ ctx.lineTo(p[0], p[1]); });
      ctx.lineTo(1940, H); ctx.closePath(); ctx.fill();
    });
    ctx.globalAlpha = 1;
  },
  defs: function(){
    var s = svg("svg", {width: 0, height: 0, "class": "si-defs"}, R.root);
    var d = svg("defs", {}, s);
    var f1 = svg("filter", {id: "inkRough", x: "-10%", y: "-10%", width: "120%", height: "120%"}, d);
    svg("feTurbulence", {type: "fractalNoise", baseFrequency: "0.035", numOctaves: "2", seed: "3", result: "n"}, f1);
    svg("feDisplacementMap", {"in": "SourceGraphic", in2: "n", scale: "7", xChannelSelector: "R", yChannelSelector: "G"}, f1);
    var f3 = svg("filter", {id: "inkBrush", x: "-5%", y: "-20%", width: "110%", height: "140%"}, d);
    svg("feTurbulence", {type: "fractalNoise", baseFrequency: "0.006 0.08", numOctaves: "3", seed: "11", result: "n"}, f3);
    svg("feDisplacementMap", {"in": "SourceGraphic", in2: "n", scale: "26", xChannelSelector: "R", yChannelSelector: "G"}, f3);
    var f2 = svg("filter", {id: "inkBleed", x: "-30%", y: "-30%", width: "160%", height: "160%"}, d);
    svg("feTurbulence", {type: "fractalNoise", baseFrequency: "0.012", numOctaves: "3", seed: "8", result: "n"}, f2);
    svg("feDisplacementMap", {"in": "SourceGraphic", in2: "n", scale: "70", xChannelSelector: "R", yChannelSelector: "G", result: "d"}, f2);
    svg("feGaussianBlur", {"in": "d", stdDeviation: "3"}, f2);
  },
  /* filled brush-stroke silhouette: round loaded start, tapering ragged tail, dry-brush gaps (비백) */
  stroke: function(x0, x1, yc, w0, seed){
    var r = rng(seed), top = [], bot = [], n = 70, cl = [];
    for (var i = 0; i <= n; i++){
      var u = i / n, x = x0 + (x1 - x0) * u, y = yc + 24 * Math.sin(u * 3.3 + 0.3) - 34 * u;
      var w = w0 * (u < 0.06 ? 0.8 + 0.2 * Math.sqrt(u / 0.06) : 1 - 0.58 * Math.pow((u - 0.06) / 0.94, 2.4));
      top.push([x, y - w * (1 + (r() - 0.5) * 0.08)]); bot.push([x, y + w * (1 + (r() - 0.5) * 0.08)]); cl.push([x, y, w]);
    }
    var f = function(p){ return p[0].toFixed(1) + " " + p[1].toFixed(1); };
    var d = "M" + f(bot[0]) + " Q" + (x0 - w0 * 1.05).toFixed(1) + " " + yc + " " + f(top[0]);
    for (i = 1; i <= n; i++) d += " L" + f(top[i]);
    var e = cl[n], tips = 7;
    for (var k = 1; k < tips; k++){
      var yy = top[n][1] + (bot[n][1] - top[n][1]) * k / tips;
      d += " L" + (e[0] + 30 + r() * 90).toFixed(1) + " " + yy.toFixed(1) + " L" + (e[0] - r() * 20).toFixed(1) + " " + (yy + 4).toFixed(1);
    }
    for (i = n; i >= 0; i--) d += " L" + f(bot[i]);
    d += " Z";
    var gaps = [];
    for (k = 0; k < 9; k++){
      var off = (r() * 2 - 1) * 0.8, from = Math.floor(n * (0.68 + r() * 0.14)), gd = "";
      for (i = from; i <= n; i += 2) gd += (gd ? " L" : "M") + cl[i][0].toFixed(1) + " " + (cl[i][1] + off * cl[i][2]).toFixed(1);
      gaps.push(gd);
    }
    return {d: d, gaps: gaps};
  },
  washOut: function(tl, target, t){ add(tl, target, {opacity: [1, 0], filter: ["blur(0px)", "blur(18px)"], duration: 760, ease: "inQuad"}, t - 760); },
  inkChars: function(tl, cs, t, stag){ add(tl, cs, {opacity: [0, 1], filter: ["blur(16px)", "blur(0px)"], scale: [1.22, 1], duration: 900, delay: A.stagger(stag), ease: "outCubic"}, t); },
  blot: function(parent, cx, cy, r, cls){
    var s = svg("svg", {viewBox: "0 0 1920 1080", width: 1920, height: 1080, "class": "si-full brush-blot " + (cls || "")}, parent);
    var g = svg("g", {"class": "brush-blotg"}, s);
    g.style.transformOrigin = cx + "px " + cy + "px";
    svg("circle", {cx: cx, cy: cy, r: r}, g);
    return g;
  },
  seal: function(parent, x, y, size){
    var w = obj(D.world), txt = str(w.seal) || str(obj(D.subject).name).charAt(0);
    var s = el("div", "brush-seal", parent, "left:" + x + "px;top:" + y + "px;width:" + size + "px;height:" + size + "px");
    var inner = el("div", "brush-seal-t", s);
    inner.textContent = txt;
    inner.style.fontSize = Math.round(size * (txt.length <= 1 ? 0.62 : txt.length <= 2 ? 0.4 : 0.32)) + "px";
    if (txt.length > 2) inner.style.height = Math.round(size * 0.72) + "px";
    return s;
  },
  hook: function(tl, P){
    var h = obj(D.hook), b = beat("brush-hook");
    on(tl, b.sc, 0);
    var blot = BRUSH.blot(b.o, 960, 540, 330);
    add(tl, blot, {scale: [0.15, 1], opacity: [0, 0.9], duration: 2600, ease: "outCubic"}, 300);
    if (h.kicker){
      var k = el("div", "brush-vert", b.o, "right:150px;top:150px;height:560px");
      k.textContent = h.kicker;
      add(tl, k, {opacity: [0, 1], translateY: [-30, 0], duration: 1200, ease: "outCubic"}, 200);
      var dot = el("div", "brush-dot", b.o, "right:168px;top:112px");
      add(tl, dot, {scale: [0, 1], duration: 600, ease: "outBack(2)"}, 150);
    }
    var q = box(b.o, "brush-hook-text", h.text, 200, 300, 1420, 480, 136, 60);
    BRUSH.inkChars(tl, chars(q), 800, 75);
    BRUSH.washOut(tl, b.o, P.reveal);
  },
  reveal: function(tl, P){
    var s = obj(D.subject), b = beat("brush-reveal"), t0 = P.reveal;
    on(tl, b.sc, t0);
    var shake = el("div", "si-full", b.o);
    var reveal = el("div", "si-full", shake);
    var art = svg("svg", {viewBox: "0 0 1920 1080", width: 1920, height: 1080, "class": "si-full brush-stroke"}, reveal);
    var g = svg("g", {filter: "url(#inkBrush)"}, art);
    var shape = BRUSH.stroke(330, 1640, 560, 150, 77);
    svg("path", {d: shape.d, "class": "body"}, g);
    shape.gaps.forEach(function(d, k){ svg("path", {d: d, "class": "gap", "stroke-width": 3 + (k % 3) * 3}, g); });
    var name = box(reveal, "brush-name", s.name, 300, 400, 1320, 300, 230, 100);
    add(tl, reveal, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 1000, ease: "inOutQuad"}, t0 + 300);
    add(tl, name, {filter: ["blur(10px)", "blur(0px)"], opacity: [0.3, 1], duration: 1100, ease: "outCubic"}, t0 + 650);
    var seal = BRUSH.seal(shake, 1520, 640, 170);
    add(tl, seal, {opacity: [0, 1], scale: [2.2, 1], rotate: [-16, -5], duration: 360, ease: "inQuad"}, t0 + 1900);
    add(tl, shake, {translateX: [0, -6, 5, -3, 2, 0], translateY: [0, 4, -4, 2, -1, 0], duration: 420, ease: "linear"}, t0 + 2260);
    if (s.en){
      var en = el("div", "brush-vert small", shake, "left:118px;top:250px;height:620px");
      en.textContent = s.en;
      add(tl, en, {opacity: [0, 1], translateY: [-24, 0], duration: 1000, ease: "outCubic"}, t0 + 1500);
    }
    if (s.sub){
      var sub = box(shake, "brush-sub", s.sub, 360, 800, 1200, 70, 44, 26);
      add(tl, words(sub), {opacity: [0, 1], filter: ["blur(8px)", "blur(0px)"], duration: 900, delay: A.stagger(90), ease: "outCubic"}, t0 + 2400);
    }
    BRUSH.washOut(tl, b.o, P.meet);
  },
  meet: function(tl, P){
    var w = obj(D.world), b = beat("brush-meet"), t0 = P.meet;
    on(tl, b.sc, t0);
    var k = el("div", "brush-vert", b.o, "right:120px;top:150px;height:640px");
    k.textContent = str(w.meet);
    add(tl, k, {opacity: [0, 1], clipPath: ["inset(0% 0% 100% 0%)", "inset(0% 0% 0% 0%)"], duration: 1100, ease: "inOutQuad"}, t0 + 100);
    var rule = el("div", "brush-rule", b.o, "right:104px;top:150px;height:680px");
    add(tl, rule, {scaleY: [0, 1], duration: 1400, ease: "outCubic"}, t0 + 200);
    var dot = el("div", "brush-dot", b.o, "right:136px;top:108px");
    add(tl, dot, {scale: [0, 1], duration: 500, ease: "outBack(2)"}, t0 + 100);
    add(tl, b.o, {opacity: [1, 0], duration: 600, ease: "linear"}, P.msg - 600);
  },
  item: function(tl, P, i, it, n){
    var a0 = i > 0 ? P.itemAt(i) - 300 : P.itemAt(i);   /* internal choreography starts with the incoming transition */
    var w = obj(D.world), b = beat("brush-item"), t0 = P.itemAt(i), t1 = t0 + P.per;
    var num = (w.numerals && w.numerals[i]) ? w.numerals[i] : String(i + 1);
    add(tl, b.sc, {opacity: [0, 1], filter: ["blur(14px)", "blur(0px)"], duration: 760, ease: "outCubic"}, Math.max(0, t0 - 380));
    var art = svg("svg", {viewBox: "0 0 1920 1080", width: 1920, height: 1080, "class": "si-full brush-enso"}, b.o);
    var g = svg("g", {filter: "url(#inkRough)"}, art);
    var ang0 = -1.2 + i * 0.7, r = 250, cx = 560, cy = 520, d = "", d2 = "";
    for (var k = 0; k <= 64; k++){
      var a = ang0 + k / 64 * 5.9, rr = r + 10 * Math.sin(k / 64 * 9);
      d += (k ? " L" : "M") + (cx + Math.cos(a) * rr).toFixed(1) + " " + (cy + Math.sin(a) * rr).toFixed(1);
      if (k > 6 && k < 52) d2 += (d2 ? " L" : "M") + (cx + Math.cos(a) * (rr - 14)).toFixed(1) + " " + (cy + Math.sin(a) * (rr - 14)).toFixed(1);
    }
    var e1 = svg("path", {d: d, "class": "e1"}, g), e2 = svg("path", {d: d2, "class": "e2"}, g);
    drawIn(tl, [e1, e2], a0 + 80, 1000, 60, "inOutSine");
    var ic = icon(b.o, it.icon, 380, 340, 360, "brush-icon");
    ic.g.setAttribute("filter", "url(#inkRough)");
    drawIn(tl, ic.paths, a0 + 450, 1100, 130, "inOutSine");
    var seal = BRUSH.seal(b.o, 1000, 250, 96);
    seal.firstChild.textContent = num;
    seal.firstChild.style.fontSize = (String(num).length > 1 ? 40 : 56) + "px";
    seal.firstChild.style.height = "auto";
    add(tl, seal, {opacity: [0, 1], scale: [1.8, 1], rotate: [-12, -4], duration: 300, ease: "inQuad"}, a0 + 300);
    var word = box(b.o, "brush-word", it.word, 1000, 360, 700, 240, 190, 90);
    BRUSH.inkChars(tl, chars(word), a0 + 500, 110);
    var lineArt = svg("svg", {viewBox: "0 0 800 40", width: 800, height: 40, "class": "brush-under"}, b.o);
    lineArt.style.left = "1000px"; lineArt.style.top = "602px";
    var ul = svg("path", {d: "M6 24 C 200 10, 420 32, 640 16", filter: "url(#inkRough)"}, lineArt);
    drawIn(tl, [ul], a0 + 900, 700, 0, "outCubic");
    var line = box(b.o, "brush-line", it.line, 1000, 650, 700, 170, 48, 30);
    add(tl, words(line), {opacity: [0, 1], filter: ["blur(8px)", "blur(0px)"], translateY: [10, 0], duration: 900, delay: A.stagger(80), ease: "outCubic"}, a0 + 1100);
    BRUSH.washOut(tl, b.o, t1 + (i < n - 1 ? 380 : 0));
  },
  message: function(tl, P){
    var m = obj(D.message), b = beat("brush-msg"), t0 = P.msg;
    on(tl, b.sc, t0);
    var q1 = el("div", "brush-quote l", b.o), q2 = el("div", "brush-quote r", b.o);
    q1.textContent = "「"; q2.textContent = "」";
    add(tl, [q1, q2], {opacity: [0, 0.5], filter: ["blur(12px)", "blur(0px)"], duration: 1000, ease: "outCubic"}, t0 + 100);
    if (m.label){
      var lab = box(b.o, "brush-msg-label", m.label, 460, 250, 1000, 70, 42, 24);
      add(tl, lab, {opacity: [0, 1], letterSpacing: ["0.5em", "0.3em"], duration: 1000, ease: "outCubic"}, t0 + 300);
    }
    var tx = box(b.o, "brush-msg-text", m.text, 340, 350, 1240, 380, 82, 40);
    add(tl, chars(tx), {opacity: [0, 1], filter: ["blur(10px)", "blur(0px)"], duration: 600, delay: A.stagger(45), ease: "outCubic"}, t0 + 700);
    BRUSH.washOut(tl, b.o, P.close);
  },
  closing: function(tl, P){
    var s = obj(D.subject), cl = obj(D.closing), b = beat("brush-close"), t0 = P.close;
    on(tl, b.sc, t0);
    var bl1 = BRUSH.blot(b.o, 300, 860, 150, "soft"), bl2 = BRUSH.blot(b.o, 1680, 200, 110, "soft");
    add(tl, [bl1, bl2], {scale: [0.1, 1], opacity: [0, 0.55], duration: 2200, delay: A.stagger(300), ease: "outCubic"}, t0 + 200);
    var name = box(b.o, "brush-close-name", s.name, 360, 270, 1200, 240, 200, 90);
    BRUSH.inkChars(tl, chars(name), t0 + 200, 160);
    if (cl.line){
      var ln = box(b.o, "brush-close-line", cl.line, 360, 520, 1200, 100, 56, 30);
      add(tl, words(ln), {opacity: [0, 1], filter: ["blur(8px)", "blur(0px)"], duration: 900, delay: A.stagger(90), ease: "outCubic"}, t0 + 1000);
    }
    var info = closingInfo();
    if (info.length){
      var row = box(b.o, "brush-info", info.join("  ·  "), 360, 680, 1200, 70, 38, 22);
      add(tl, row, {opacity: [0, 1], translateY: [14, 0], duration: 900, ease: "outCubic"}, t0 + 1500);
    }
    var seal = BRUSH.seal(b.o, 1450, 470, 150);
    add(tl, seal, {opacity: [0, 1], scale: [2.2, 1], rotate: [-14, 4], duration: 340, ease: "inQuad"}, t0 + 2000);
  }
};

/* ======================================================================
   SKIN 3 · english-news — broadcast package: LIVE bug, ticker, stingers, lower thirds
   ====================================================================== */
var NEWS = {
  painter: function(ctx, t, W, H){
    var c = R.c;
    var g = ctx.createRadialGradient(W * 0.68, H * 0.42, 60, W * 0.6, H * 0.5, W * 0.85);
    g.addColorStop(0, c.bg2); g.addColorStop(1, c.bg1);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalAlpha = 0.06; ctx.fillStyle = "#ffffff";
    for (var b = 0; b < 4; b++){
      var x = ((t * 60 + b * 560) % 2600) - 500;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 180, 0); ctx.lineTo(x - 320, H); ctx.lineTo(x - 500, H); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
    var cx = 1440, cy = 500, r = 430, rot = t * 0.25;
    ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1.4;
    ctx.globalAlpha = 0.13;
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, 6.283); ctx.stroke();
    for (var la = -60; la <= 60; la += 20){
      var yy = cy - Math.sin(la * Math.PI / 180) * r, rr = Math.cos(la * Math.PI / 180) * r;
      ctx.globalAlpha = 0.08; ctx.beginPath(); ctx.ellipse(cx, yy, rr, rr * 0.12, 0, 0, 6.283); ctx.stroke();
    }
    for (var lo = 0; lo < 12; lo++){
      var a = rot + lo * Math.PI / 12, w = Math.abs(Math.cos(a)) * r;
      ctx.globalAlpha = 0.05 + 0.08 * Math.abs(Math.sin(a));
      ctx.beginPath(); ctx.ellipse(cx, cy, w, r, 0, 0, 6.283); ctx.stroke();
    }
    var rr2 = rng(5);
    for (var d = 0; d < 70; d++){
      var la2 = (rr2() - 0.5) * 2.4, lo2 = rr2() * 6.283 + rot, z = Math.cos(lo2);
      if (z < 0) continue;
      ctx.globalAlpha = 0.5 * z; ctx.fillStyle = rr2() < 0.3 ? c.accent : "#ffffff";
      ctx.beginPath(); ctx.arc(cx + Math.sin(lo2) * Math.cos(la2) * r, cy - Math.sin(la2) * r * 0.95, 2.4, 0, 6.283); ctx.fill();
    }
    ctx.globalAlpha = 0.05; ctx.fillStyle = "#000000";
    for (var y = 0; y < H; y += 4) ctx.fillRect(0, y, W, 1);
    ctx.globalAlpha = 1;
  },
  chrome: function(tl){
    var w = obj(D.world), fg = R.fg;
    var bug = el("div", "news-bug", fg);
    var live = el("div", "news-live", bug); el("i", "", live);
    var lt = el("span", "", live); lt.textContent = str(w.live) || "LIVE";
    R.loops.push(A.animate(live.firstChild, {opacity: [1, 0.2], duration: 700, loop: true, alternate: true, ease: "inOutSine"}));
    if (w.channel){ var ch = el("div", "news-channel", bug); ch.textContent = w.channel; }
    add(tl, bug, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 700, ease: "outExpo"}, 300);
    if (w.time){
      var tm = el("div", "news-time", fg); tm.textContent = w.time;
      add(tl, tm, {opacity: [0, 1], translateY: [-20, 0], duration: 600, ease: "outExpo"}, 500);
    }
    var tick = el("div", "news-ticker", fg);
    if (w.tickerLabel){ var tlb = el("div", "news-ticker-label", tick); tlb.textContent = w.tickerLabel; }
    var viewport = el("div", "news-ticker-view", tick), track = el("div", "news-ticker-track", viewport);
    var list = (w.ticker && w.ticker.length) ? w.ticker : [str(obj(D.subject).en || obj(D.subject).name)];
    var half = el("div", "news-ticker-half", track), guard = 0;
    var fill = function(){ list.forEach(function(s){ var sp = el("span", "", half); sp.textContent = s; el("b", "", half); }); };
    fill();
    while (half.scrollWidth < 1900 && guard++ < 12) fill();   /* short ticker: repeat so the loop never shows a gap */
    track.appendChild(half.cloneNode(true));
    add(tl, tick, {translateY: ["220%", "0%"], duration: 700, ease: "outExpo"}, 700);
    var halfW = Math.max(800, track.firstChild.scrollWidth);
    R.loops.push(A.animate(track, {translateX: [0, -halfW], duration: halfW / 120 * 1000, loop: true, ease: "linear"}));
  },
  stinger: function(tl, t){
    var wrap = el("div", "news-sting", R.fg);
    var bars = ["r", "w", "n"].map(function(k){ var o = el("div", "news-sting-bar " + k, wrap); el("div", "", o); return o; });
    add(tl, bars, {translateX: [-3900, 2100], duration: 900, delay: A.stagger(60), ease: "inOutSine"}, t - 570);
  },
  hook: function(tl, P){
    var h = obj(D.hook), w = obj(D.world), b = beat("news-hook");
    on(tl, b.sc, 0);
    var band = el("div", "news-band", b.o);
    add(tl, band, {scaleX: [0, 1], duration: 650, ease: "outExpo"}, 900);
    var bt = box(band, "news-band-text", w.breaking || "BREAKING NEWS", 120, 0, 1400, 150, 110, 50);
    add(tl, bt, {translateX: [-200, 0], opacity: [0, 1], duration: 800, ease: "outExpo"}, 1150);
    if (h.kicker){
      var k = el("div", "news-tag gold", b.o, "left:120px;top:478px");
      k.textContent = h.kicker;
      add(tl, k, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 600, ease: "outExpo"}, 1700);
    }
    var q = box(b.o, "news-headline", h.text, 120, 560, 1680, 300, 120, 56);
    var ws = words(q);
    add(tl, ws, {translateY: [80, 0], opacity: [0, 1], duration: 700, delay: A.stagger(70), ease: "outExpo"}, 1900);
    add(tl, b.o, {opacity: [1, 0], duration: 1, ease: "linear"}, P.reveal);
    NEWS.stinger(tl, P.reveal);
  },
  reveal: function(tl, P){
    var s = obj(D.subject), w = obj(D.world), b = beat("news-reveal"), t0 = P.reveal;
    on(tl, b.sc, t0);
    if (w.topStory){
      var ts = el("div", "news-tag gold", b.o, "left:120px;top:220px");
      ts.textContent = w.topStory;
      add(tl, ts, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 600, ease: "outExpo"}, t0 + 250);
    }
    var big = box(b.o, "news-giant", s.en || s.name, 110, 290, 1700, 360, 330, 120);
    add(tl, chars(big), {translateY: ["105%", "0%"], skewX: [-14, 0], duration: 700, delay: A.stagger(55), ease: "outExpo"}, t0 + 400);
    var flash = el("div", "news-flash", b.o);
    add(tl, flash, {opacity: [0.55, 0], duration: 600, ease: "outQuad"}, t0 + 650);
    var tag = el("div", "news-kr-tag", b.o);
    tag.textContent = str(s.name);
    add(tl, tag, {translateX: [-500, 0], duration: 800, ease: "outExpo"}, t0 + 1200);
    if (s.sub){
      var lt = el("div", "news-l3", b.o, "left:120px;top:800px;width:1200px;height:96px");
      var lb = box(lt, "news-l3-text", s.sub, 36, 0, 1128, 96, 50, 26);
      add(tl, lt, {scaleX: [0, 1], duration: 600, ease: "outExpo"}, t0 + 1700);
      add(tl, lb, {opacity: [0, 1], translateX: [-20, 0], duration: 500, ease: "outExpo"}, t0 + 2000);
    }
    add(tl, b.o, {opacity: [1, 0], duration: 1, ease: "linear"}, P.meet);
    NEWS.stinger(tl, P.meet);
  },
  meet: function(tl, P){
    var w = obj(D.world), b = beat("news-meet"), t0 = P.meet;
    on(tl, b.sc, t0);
    if (w.meet){
      var k = el("div", "news-tag", b.o, "left:120px;top:150px");
      k.textContent = w.meet;
      add(tl, k, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 600, ease: "outExpo"}, t0 + 200);
    }
    add(tl, b.o, {opacity: [1, 0], duration: 1, ease: "linear"}, P.msg);
  },
  item: function(tl, P, i, it, n){
    var a0 = i > 0 ? P.itemAt(i) - 330 : P.itemAt(i);   /* internal choreography starts with the incoming transition */
    var w = obj(D.world), b = beat("news-item"), t0 = P.itemAt(i), t1 = t0 + P.per;
    if (i === 0) on(tl, b.sc, t0 - 100);
    else {
      on(tl, b.sc, t0 - 350);
      add(tl, b.sc, {translateX: ["100%", "0%"], duration: 700, ease: "inOutQuart"}, t0 - 350);
    }
    var mon = el("div", "news-monitor", b.o);
    var mbar = el("div", "news-monitor-bar", mon);
    mbar.textContent = (w.story ? w.story + " " : "") + pad2(i + 1);
    var screen = el("div", "news-monitor-screen", mon);
    var ic = icon(screen, it.icon, 130, 110, 380, "news-icon");
    add(tl, mon, {scale: [0.8, 1], opacity: [0, 1], duration: 650, ease: "outBack(1.4)"}, a0 + 50);
    drawIn(tl, ic.paths, a0 + 350, 750, 70, "outCubic");
    add(tl, ic.svg, {scale: [1, 1.08], duration: P.per, ease: "linear"}, t0);
    var word = box(b.o, "news-word", it.word, 880, 270, 920, 300, 210, 90);
    add(tl, chars(word), {translateY: ["105%", "0%"], duration: 650, delay: A.stagger(35), ease: "outExpo"}, a0 + 300);
    var red = el("div", "news-redline", b.o);
    add(tl, red, {scaleX: [0, 1], duration: 600, ease: "outExpo"}, a0 + 600);
    var l3 = el("div", "news-l3", b.o, "left:880px;top:640px;width:920px;height:120px");
    var lt = box(l3, "news-l3-text", it.line, 32, 0, 856, 120, 48, 28);
    add(tl, l3, {scaleX: [0, 1], duration: 600, ease: "outExpo"}, a0 + 800);
    add(tl, lt, {opacity: [0, 1], translateY: [24, 0], duration: 500, ease: "outExpo"}, a0 + 1050);
    if (i < n - 1) add(tl, b.o, {translateX: ["0%", "-100%"], duration: 700, ease: "inOutQuart"}, t1 - 350);
    else add(tl, b.o, {opacity: [1, 0], duration: 1, ease: "linear"}, t1);
  },
  message: function(tl, P){
    var m = obj(D.message), cl = obj(D.closing), w = obj(D.world), b = beat("news-msg"), t0 = P.msg;
    on(tl, b.sc, t0);
    NEWS.stinger(tl, t0);
    if (w.interview){
      var it = el("div", "news-tag", b.o, "left:120px;top:150px");
      it.textContent = w.interview;
      add(tl, it, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 600, ease: "outExpo"}, t0 + 300);
    }
    var qm = el("div", "news-qmark", b.o); qm.textContent = "“";
    add(tl, qm, {opacity: [0, 1], translateY: [60, 0], duration: 700, ease: "outExpo"}, t0 + 400);
    var tx = box(b.o, "news-msg-text", m.text, 300, 270, 1500, 420, 84, 40);
    add(tl, words(tx), {opacity: [0, 1], translateY: [40, 0], duration: 600, delay: A.stagger(60), ease: "outExpo"}, t0 + 600);
    if (m.label || cl.teacher){
      var nt = el("div", "news-nametag", b.o);
      if (m.label){ var a = el("div", "a", nt); a.textContent = m.label; }
      if (cl.teacher){ var bb = el("div", "b", nt); bb.textContent = cl.teacher; }
      add(tl, nt, {clipPath: ["inset(0% 100% 0% 0%)", "inset(0% 0% 0% 0%)"], duration: 700, ease: "outExpo"}, t0 + 1500);
    }
    add(tl, b.o, {opacity: [1, 0], duration: 1, ease: "linear"}, P.close);
  },
  closing: function(tl, P){
    var s = obj(D.subject), cl = obj(D.closing), w = obj(D.world), b = beat("news-close"), t0 = P.close;
    on(tl, b.sc, t0);
    NEWS.stinger(tl, t0);
    var so = box(b.o, "news-signoff", w.signoff || s.en || s.name, 160, 250, 1600, 260, 230, 100);
    add(tl, chars(so), {translateY: ["105%", "0%"], duration: 700, delay: A.stagger(45), ease: "outExpo"}, t0 + 300);
    var tag = el("div", "news-kr-tag center", b.o);
    tag.textContent = str(s.name) + (cl.line ? "  |  " + cl.line : "");
    add(tl, tag, {clipPath: ["inset(0% 50% 0% 50%)", "inset(0% 0% 0% 0%)"], duration: 700, ease: "outExpo"}, t0 + 900);
    var info = closingInfo();
    if (info.length){
      var row = box(b.o, "news-credits", info.join("   /   "), 360, 720, 1200, 64, 38, 22);
      add(tl, row, {opacity: [0, 1], translateY: [20, 0], duration: 700, ease: "outExpo"}, t0 + 1400);
    }
  }
};

var SKINS = {"science-neon": NEON, "korean-brush": BRUSH, "english-news": NEWS};

/* ---------- show ---------- */
window.SHOW = {
  start: function(){
    FITS = []; R = {loops: []};
    D = window.DOC || {};
    var skin = SKINS[D.skin] || NEON;
    R.c = {bg1: cssv("bg1", "#05070d"), bg2: cssv("bg2", "#101a30"), text: cssv("text", "#ffffff"), primary: cssv("primary", "#3ef2ff"), accent: cssv("accent", "#ff4fd8"), neon3: cssv("neon3", "#c6ff4a")};
    var items = (D.items || []).slice(0, 6);
    var P = R.plan = makePlan(items.length);
    R.root = el("div", "si-root", S.el.scene);
    R.stack = el("div", "si-full", R.root);
    R.fg = el("div", "si-full si-fg", R.root);
    if (skin.defs) skin.defs();
    S.bg(skin.painter);
    var tl = A.createTimeline({autoplay: true});
    if (skin.chrome) skin.chrome(tl);
    skin.hook(tl, P);
    skin.reveal(tl, P);
    skin.meet(tl, P, items.length);
    items.forEach(function(it, i){ skin.item(tl, P, i, obj(it), items.length); });
    skin.message(tl, P);
    skin.closing(tl, P);
    tl.add(R.root, {opacity: [1, 1], duration: 1, ease: "linear"}, P.total - 1);
    S.timeline(tl, P.total);
    R.loops.forEach(function(l){ S.timeline(l, 1); });
    loadFonts();
  },
  toText: function(){
    var s = obj(D.subject), out = [str(obj(D.hook).text), str(s.name) + " " + str(s.en)];
    (D.items || []).forEach(function(it, i){ out.push((i + 1) + ". " + str(it.word) + " — " + str(it.line)); });
    out.push(str(obj(D.message).text), closingInfo().join(" · "));
    return out.join("\n");
  }
};
})();
