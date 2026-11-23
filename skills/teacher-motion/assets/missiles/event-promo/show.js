/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02)
   event-promo missile: 30 s event opening / promo (kinetic type -> hero picture -> date -> program cards -> kinetic words -> end card).
   All words come from DOC (skins/*.json + content.json). DOC.hero = picture (data URI or a file next to the content; optional:
   without one a code-drawn scene in the skin colours stands in, so nothing is fetched). Adapted from the 2026-11-22 showcase piece. */
(function(){
"use strict";
var A = window.anime, S = window.STAGE, D = window.DOC || {};
var TOTAL = 30000;

function el(tag, cls, parent, css){
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (css) e.style.cssText = css;
  if (parent) parent.appendChild(e);
  return e;
}
function add(tl, targets, params, t){
  var init = {}, has = false;
  for (var k in params){
    var v = params[k];
    if (k !== "delay" && Array.isArray(v) && v.length > 1 && typeof v[0] !== "object"){ init[k] = v[0]; has = true; }
  }
  if (has) A.utils.set(targets, init);
  tl.add(targets, params, Math.max(0, t));
}

/* the hero picture: the user's / generated picture, or a drawn stand-in (stage, lights, bunting) in the skin's colours */
function heroSrc(){
  if (D.hero) return D.hero;
  var v = D.vars || {}, a = v.primary || "#F6C453", b = v.accent || "#E4572E", c = v.bg2 || "#3A1F3D", d = v.bg1 || "#1E1226";
  var flags = "", i;
  for (i = 0; i < 14; i++){ var x = 80 + i * 128; flags += '<path d="M' + x + ' 150 l64 0 l-32 70z" fill="' + (i % 2 ? a : b) + '" opacity=".9"/>'; }
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080"><defs><radialGradient id="g" cx=".5" cy=".35" r=".7"><stop offset="0" stop-color="' + c + '"/><stop offset="1" stop-color="' + d + '"/></radialGradient></defs>' +
    '<rect width="1920" height="1080" fill="url(#g)"/><path d="M40 150 Q960 260 1880 150" stroke="' + a + '" stroke-width="4" fill="none"/>' + flags +
    '<ellipse cx="960" cy="930" rx="760" ry="120" fill="' + b + '" opacity=".55"/><rect x="420" y="560" width="1080" height="380" rx="24" fill="' + d + '" opacity=".75"/>' +
    '<path d="M560 420 L760 980 L360 980z" fill="' + a + '" opacity=".14"/><path d="M1360 420 L1560 980 L1160 980z" fill="' + a + '" opacity=".14"/>' +
    '<circle cx="560" cy="420" r="26" fill="' + a + '"/><circle cx="1360" cy="420" r="26" fill="' + a + '"/></svg>';
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}
/* seeded random */
function rng(seed){ var s = seed >>> 0; return function(){ s = (s + 0x6D2B79F5) >>> 0; var t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

/* ---------- background: plum dusk + falling maple leaves + warm bokeh (pure function of t) ---------- */
var R = rng(7), LEAVES = [], BOKEH = [];
for (var i = 0; i < 26; i++) LEAVES.push({x: R() * 1920, sp: 60 + R() * 90, sw: 40 + R() * 80, ph: R() * 6.28, sz: 18 + R() * 26, rot: R() * 6.28, vr: (R() - .5) * 2.2, c: ["#E4572E", "#F2A33A", "#C8402A", "#F6C453"][i % 4], y0: R() * 1300});
for (var j = 0; j < 22; j++) BOKEH.push({x: R() * 1920, y: R() * 1080, r: 20 + R() * 70, ph: R() * 6.28});
function leaf(ctx, s){
  ctx.beginPath();
  ctx.moveTo(0, -s);
  ctx.bezierCurveTo(s * .35, -s * .55, s * .9, -s * .5, s * .62, -s * .05);
  ctx.bezierCurveTo(s * .95, s * .15, s * .55, s * .35, s * .3, s * .3);
  ctx.lineTo(0, s * .95);
  ctx.lineTo(-s * .3, s * .3);
  ctx.bezierCurveTo(-s * .55, s * .35, -s * .95, s * .15, -s * .62, -s * .05);
  ctx.bezierCurveTo(-s * .9, -s * .5, -s * .35, -s * .55, 0, -s);
  ctx.fill();
}
S.bg(function(ctx, t, W, H){
  var g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, "#1E1230"); g.addColorStop(.6, "#3A1C3A"); g.addColorStop(1, "#5A2A35");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (var b = 0; b < BOKEH.length; b++){
    var k = BOKEH[b], a = .05 + .05 * Math.sin(t * .8 + k.ph);
    ctx.fillStyle = "rgba(246,196,83," + a.toFixed(3) + ")";
    ctx.beginPath(); ctx.arc(k.x, k.y, k.r, 0, 6.283); ctx.fill();
  }
  for (var i = 0; i < LEAVES.length; i++){
    var L = LEAVES[i], y = ((L.y0 + t * L.sp) % 1300) - 110, x = L.x + Math.sin(t * .9 + L.ph) * L.sw;
    ctx.save(); ctx.translate(x, y); ctx.rotate(L.rot + t * L.vr); ctx.globalAlpha = .55;
    ctx.fillStyle = L.c; leaf(ctx, L.sz); ctx.restore();
  }
});

/* ---------- icons (original line drawings) ---------- */
var ICON = {
  stage: '<svg viewBox="0 0 120 120"><path d="M60 18a14 14 0 0 1 14 14v22a14 14 0 0 1-28 0V32a14 14 0 0 1 14-14z"/><path d="M36 52a24 24 0 0 0 48 0M60 76v18M44 98h32"/><path d="M20 30l8 4M100 30l-8 4M18 56h9M102 56h-9"/></svg>',
  booth: '<svg viewBox="0 0 120 120"><path d="M18 46l8-22h68l8 22z"/><path d="M18 46c0 7 7 12 14 12s14-5 14-12c0 7 7 12 14 12s14-5 14-12c0 7 7 12 14 12s14-5 14-12"/><path d="M26 58v40h68V58M50 98V74h20v24"/></svg>',
  food: '<svg viewBox="0 0 120 120"><path d="M38 14v92"/><circle cx="38" cy="32" r="12"/><circle cx="38" cy="58" r="12"/><circle cx="38" cy="84" r="10"/><path d="M70 50h38l-5 48H75z"/><path d="M80 50c0-12 4-18 9-18s9 6 9 18M78 66h22"/></svg>'
};

window.SHOW = {
  start: function(){
    var sc = S.el.scene;
    S.clear();
    var tl = A.createTimeline({autoplay: true});
    var loops = [];

    /* ===== 1. HOOK 0–4.2s ===== */
    var s1 = el("div", "fx-s1", sc);
    var s1in = el("div", "fx-in", s1);
    var kick = el("div", "fx-kick", s1in); kick.textContent = D.hook_small;
    var w1 = el("div", "fx-big fx-w1", s1in); w1.textContent = D.hook_a;
    var w2 = el("div", "fx-big fx-w2", s1in); w2.textContent = D.hook_b;
    add(tl, kick, {opacity: [0, 1], translateY: [40, 0], duration: 600, ease: "outExpo"}, 200);
    add(tl, w1, {opacity: [0, 1], scale: [1.8, 1], duration: 650, ease: "outBack(1.7)"}, 700);
    add(tl, w2, {opacity: [0, 1], scale: [2.2, 1], rotate: [-8, -3], duration: 700, ease: "outBack(2)"}, 1350);
    add(tl, s1in, {translateX: [0, -14, 12, -8, 6, 0], duration: 420, ease: "linear"}, 1400);
    add(tl, s1, {opacity: [1, 0], translateY: [0, -90], duration: 450, ease: "inQuad"}, 3800);

    /* ===== 2. HERO 4.2–10.2s ===== */
    var s2 = el("div", "fx-s2", sc);
    var frame = el("div", "fx-frame", s2);
    var img = el("img", "fx-img", frame); img.src = heroSrc(); img.alt = "";
    var shade = el("div", "fx-shade", frame);
    var tWrap = el("div", "fx-title", s2);
    var t1 = el("div", "fx-t1", tWrap); t1.textContent = D.school;
    var t2 = el("div", "fx-t2", tWrap); t2.textContent = D.title;
    var t3 = el("div", "fx-t3", tWrap); t3.textContent = D.tagline;
    add(tl, frame, {clipPath: ["inset(0% 0% 0% 100%)", "inset(0% 0% 0% 0%)"], duration: 900, ease: "outExpo"}, 4200);
    add(tl, img, {scale: [1.18, 1.02], translateX: [40, -20], duration: 6200, ease: "linear"}, 4200);
    add(tl, t1, {opacity: [0, 1], translateY: [50, 0], duration: 600, ease: "outExpo"}, 4900);
    var t2c = S.split(t2);
    add(tl, t2c, {opacity: [0, 1], translateY: [120, 0], rotate: [12, 0], duration: 700, delay: A.stagger(70), ease: "outBack(1.4)"}, 5150);
    add(tl, t3, {opacity: [0, 1], translateX: [-40, 0], duration: 600, ease: "outExpo"}, 5900);
    add(tl, s2, {opacity: [1, 0], scale: [1, 1.06], duration: 500, ease: "inQuad"}, 9700);

    /* ===== 3. DATE 10.2–15.2s ===== */
    var s3 = el("div", "fx-s3", sc);
    var ring = el("div", "fx-ring", s3);
    ring.innerHTML = '<svg viewBox="0 0 800 800"><circle cx="400" cy="400" r="380"/><circle class="r2" cx="400" cy="400" r="340"/></svg>';
    var date = el("div", "fx-date", s3);
    var dd = String(D.date_num || "");
    var cells = [];
    for (var c = 0; c < dd.length; c++){
      var m = el("span", "fx-dmask", date), d = el("span", "fx-dch", m);
      d.textContent = dd.charAt(c); cells.push(d);
    }
    var dow = el("div", "fx-dow", s3); dow.textContent = D.date_day;
    var chips = el("div", "fx-chips", s3);
    (D.date_chips || []).forEach(function(x){ var ch = el("span", "fx-chip", chips); ch.textContent = x; });
    var draw = A.svg.createDrawable(ring.querySelectorAll("circle"));
    add(tl, ring, {opacity: [0, 1], duration: 200, ease: "linear"}, 10200);
    add(tl, draw, {draw: ["0 0", "0 1"], duration: 1100, delay: A.stagger(160), ease: "inOutQuad"}, 10200);
    add(tl, cells, {translateY: ["110%", "0%"], duration: 650, delay: A.stagger(90), ease: "outExpo"}, 10450);
    add(tl, dow, {opacity: [0, 1], scale: [.6, 1], duration: 500, ease: "outBack(2)"}, 11200);
    add(tl, chips.children, {opacity: [0, 1], translateY: [30, 0], duration: 500, delay: A.stagger(140), ease: "outExpo"}, 11500);
    add(tl, s3, {opacity: [1, 0], translateY: [0, 80], duration: 450, ease: "inQuad"}, 14750);

    /* ===== 4. PROGRAM 15.2–22.6s ===== */
    var s4 = el("div", "fx-s4", sc);
    var h4 = el("div", "fx-h4", s4); h4.textContent = D.program_head;
    var row = el("div", "fx-row", s4), cards = [], inners = [];
    (D.program || []).forEach(function(p, i){
      var cw = el("div", "fx-cw", row), card = el("div", "fx-card c" + i, cw);
      var ic = el("div", "fx-ic", card); ic.innerHTML = ICON[p.icon] || "";
      var nm = el("div", "fx-nm", card); nm.textContent = p.name;
      var ds = el("div", "fx-ds", card); ds.textContent = p.desc;
      cards.push(cw); inners.push(card);
    });
    add(tl, h4, {opacity: [0, 1], translateY: [-40, 0], duration: 600, ease: "outExpo"}, 15200);
    add(tl, cards, {opacity: [0, 1], translateY: [260, 0], rotate: [function(_, i){ return [-14, 6, 12][i % 3]; }, function(_, i){ return [-3, 1, 3][i % 3]; }], duration: 900, delay: A.stagger(220), ease: "outBack(1.3)"}, 15600);
    add(tl, row.querySelectorAll(".fx-ic svg"), {scale: [0, 1], duration: 600, delay: A.stagger(220), ease: "outElastic(1,.6)"}, 16100);
    add(tl, s4, {opacity: [1, 0], scale: [1, .94], duration: 450, ease: "inQuad"}, 22150);

    /* ===== 5. KINETIC 22.6–26.6s ===== */
    var s5 = el("div", "fx-s5", sc);
    var band = el("div", "fx-band", s5);
    var words = (D.kinetic || []).map(function(w, i){ var o = el("div", "fx-kw k" + i, s5), inn = el("div", "fx-kwi", o); inn.textContent = w; return [o, inn]; });
    add(tl, band, {scaleX: [0, 1], duration: 500, ease: "outExpo"}, 22600);
    words.forEach(function(p, i){
      var t0 = 22700 + i * 1250;
      add(tl, p[0], {opacity: [0, 1], translateY: [140, 0], duration: 450, ease: "outExpo"}, t0);
      if (i < words.length - 1) add(tl, p[1], {opacity: [1, 0], translateY: [0, -140], duration: 380, ease: "inQuad"}, t0 + 900);
    });
    add(tl, s5, {opacity: [1, 0], duration: 400, ease: "inQuad"}, 26300);

    /* ===== 6. END CARD 26.7–30s (holds 2.5s+) ===== */
    var s6 = el("div", "fx-s6", sc);
    var pic = el("div", "fx-pic", s6); var pimg = el("img", "", pic); pimg.src = heroSrc(); pimg.alt = "";
    var info = el("div", "fx-info", s6);
    var e1 = el("div", "fx-e1", info); e1.textContent = D.school;
    var e2 = el("div", "fx-e2", info); e2.textContent = D.title;
    var e3 = el("div", "fx-e3", info); e3.textContent = D.end_when;
    var e4 = el("div", "fx-e4", info); e4.textContent = D.end_line;
    add(tl, pic, {opacity: [0, 1], scale: [.8, 1], rotate: [6, 2], duration: 700, ease: "outBack(1.5)"}, 26700);
    add(tl, [e1, e2, e3, e4], {opacity: [0, 1], translateX: [-60, 0], duration: 600, delay: A.stagger(120), ease: "outExpo"}, 26800);

    S.timeline(tl, TOTAL);
    /* gentle idle bob on program cards (registered loop) */
    loops.push(A.animate(inners, {translateY: [0, -10], duration: 1400, loop: true, alternate: true, delay: A.stagger(200), ease: "inOutSine"}));
    loops.forEach(function(l){ S.timeline(l, 1); });
  },
  toText: function(){ return [D.hook_small, D.hook_a, D.hook_b, D.school + " " + D.title, D.date_num + " " + D.date_day].concat(D.kinetic || []).join("\n"); }
};
})();
