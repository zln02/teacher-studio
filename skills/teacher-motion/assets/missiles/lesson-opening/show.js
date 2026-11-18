/* lesson-opening — 수업 시작 화면 (10~15s)
   Countdown N→1 (kinetic numbers) → 「오늘의 주제」 title + one-line goal (+ optional step chips)
   → holds with a subtle idle loop until click / Space / Enter / → / PageDown, then folds into a header.
   Skins: bold-pop (bright geometric pop) · calm-paper (soft paper cut-out). All text from DOC. */
(function(){
"use strict";
var A = window.anime, S = window.STAGE, D = window.DOC || {};
var R = {}, FITS = [];

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
function outCubic(x){ x = clamp(x, 0, 1); return 1 - Math.pow(1 - x, 3); }

/* tl.add + apply [from, …] values now so elements wait in their start state */
function add(tl, targets, params, t){
  var init = {}, has = false;
  for (var k in params){
    var v = params[k];
    if (k !== "delay" && Array.isArray(v) && v.length > 1 && typeof v[0] !== "object"){ init[k] = v[0]; has = true; }
  }
  if (has) A.utils.set(targets, init);
  tl.add(targets, params, Math.max(0, t));
}
/* fixed-size frame (.lo-box) + inner text block (.lo-t, returned); fit with STAGE.fitText on a plain clone */
function box(parent, cls, text, x, y, w, h, maxPx, minPx){
  var b = el("div", "lo-box word-break " + (cls || ""), parent, "left:" + x + "px;top:" + y + "px;width:" + w + "px;height:" + h + "px");
  var e = el("div", "lo-t", b);
  e.textContent = str(text);
  if (maxPx){ var f = [b, maxPx, minPx || 28, str(text)]; FITS.push(f); fitOne(f); }
  return e;
}
function fitOne(f){
  var b = f[0], c = b.cloneNode(false), t = el("div", "lo-t", c);
  t.textContent = f[3];
  c.style.visibility = "hidden"; c.style.transform = "none"; c.style.opacity = "1";
  b.parentNode.appendChild(c);
  var size = S.fitText(c, f[1], f[2]);
  c.parentNode.removeChild(c);
  b.style.fontSize = size + "px";
}
function refit(){ FITS.forEach(function(f){ if (f[0].parentNode) fitOne(f); }); }
function loadFonts(){
  var fams = D.fonts || [];
  if (fams.length && !document.getElementById("lo-fonts")){
    var l = el("link", "", document.head);
    l.id = "lo-fonts"; l.rel = "stylesheet";
    l.href = "https://fonts.googleapis.com/css2?" + fams.map(function(f){ return "family=" + String(f).replace(/ /g, "+"); }).join("&") + "&display=swap";
  }
  if (document.fonts && document.fonts.addEventListener) document.fonts.addEventListener("loadingdone", refit);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(refit);
}

/* ---------- plan ---------- */
function makePlan(n){
  var p = {n: n, lead: 700, step: 1000};
  p.numAt = function(k){ return p.lead + (n - k) * p.step; };   /* k = n … 1 */
  p.title = p.lead + n * p.step;                                  /* countdown ends */
  p.settled = p.title + 3000;                                     /* everything on screen */
  p.total = Math.max(p.settled + 3000, 10000);                    /* video length incl. idle hold */
  return p;
}
function palette(){ return [R.c.primary, R.c.accent, R.c.mint, R.c.bg2, R.c.ink]; }

/* ======================================================================
   SKIN 1 · bold-pop — bright flat colours, circle wipes, sticker numbers
   ====================================================================== */
var POP = {
  shapes: (function(){
    var r = rng(42), out = [];
    for (var i = 0; i < 22; i++) out.push({x: r(), y: r(), s: 26 + r() * 70, k: Math.floor(r() * 4), rot: r() * 6.28, spin: (r() - 0.5) * 1.2, ph: r() * 6.28, c: Math.floor(r() * 4)});
    return out;
  })(),
  painter: function(ctx, t, W, H){
    var P = R.plan, c = R.c, ms = t * 1000, pal = palette();
    var base = c.bg1, k = -1;
    for (var j = P.n; j >= 1; j--){ if (ms >= P.numAt(j)) k = P.n - j; }
    var colorAt = function(idx){ return idx < 0 ? c.bg1 : pal[idx % pal.length]; };
    var cur = colorAt(k), prev = colorAt(k - 1), start = k < 0 ? 0 : P.numAt(P.n - k);
    if (ms >= P.title){ cur = c.bg1; prev = colorAt(P.n - 1); start = P.title; }
    ctx.fillStyle = prev; ctx.fillRect(0, 0, W, H);
    var pr = outCubic((ms - start) / 420);
    ctx.fillStyle = cur; ctx.beginPath(); ctx.arc(W / 2, H / 2 + 20, 1250 * pr + 1, 0, 6.283); ctx.fill();
    base = cur;
    ctx.globalAlpha = 0.12; ctx.fillStyle = base === c.ink ? "#ffffff" : c.ink;
    var off = (t * 14) % 48;
    for (var y = -48; y < H + 48; y += 48){
      for (var x = -48; x < W + 48; x += 48){
        var dx = x + ((y / 48) % 2 ? 24 : 0) + off, dy = y + off;
        var rr = 3 + 3 * (0.5 + 0.5 * Math.sin((dx + dy) * 0.004 + t));
        ctx.beginPath(); ctx.arc(dx, dy, rr, 0, 6.283); ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
    var cols = [c.primary, c.accent, c.mint, c.ink];
    POP.shapes.forEach(function(s, i){
      var col = cols[s.c]; if (col === cur) col = cols[(s.c + 1) % 4];
      var sx = s.x * W + Math.sin(t * 0.6 + s.ph) * 26, sy = s.y * H + Math.cos(t * 0.5 + s.ph) * 22;
      var inTitle = ms >= P.title;
      if (inTitle){ var edge = s.x < 0.5 ? -1 : 1; sx = (edge < 0 ? s.x * 260 + 30 : W - (1 - s.x) * 260 - 30) + Math.sin(t * 0.6 + s.ph) * 18; }
      ctx.save(); ctx.translate(sx, sy); ctx.rotate(s.rot + t * s.spin);
      ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 10; ctx.lineCap = "round"; ctx.lineJoin = "round";
      var z = s.s;
      if (s.k === 0){ ctx.beginPath(); ctx.arc(0, 0, z * 0.5, 0, 6.283); ctx.stroke(); }
      else if (s.k === 1){ ctx.beginPath(); ctx.moveTo(0, -z * 0.55); ctx.lineTo(z * 0.5, z * 0.4); ctx.lineTo(-z * 0.5, z * 0.4); ctx.closePath(); ctx.fill(); }
      else if (s.k === 2){ ctx.beginPath(); ctx.moveTo(-z * 0.6, 0); for (var q = 1; q <= 4; q++) ctx.lineTo(-z * 0.6 + q * z * 0.3, q % 2 ? -z * 0.22 : z * 0.22); ctx.stroke(); }
      else { ctx.fillRect(-z * 0.12, -z * 0.45, z * 0.24, z * 0.9); ctx.fillRect(-z * 0.45, -z * 0.12, z * 0.9, z * 0.24); }
      ctx.restore();
    });
  },
  ready: function(tl, P, root){
    var w = obj(D.world);
    if (!w.ready) return;
    var pill = el("div", "pop-ready", root);
    pill.textContent = w.ready;
    add(tl, pill, {translateY: [-160, 0], rotate: [-8, -2], duration: 700, ease: "outBack(1.8)"}, 100);
    add(tl, pill, {opacity: [1, 0], duration: 250, ease: "linear"}, P.title - 200);
  },
  number: function(tl, P, root, k){
    var t0 = P.numAt(k), wrap = el("div", "pop-num", root), inner = el("div", "pop-num-o", wrap);
    var disc = el("div", "pop-disc", inner), digit = el("div", "pop-digit", inner);
    disc.style.background = palette()[(P.n - k + 1) % 5];
    digit.textContent = String(k);
    add(tl, wrap, {opacity: [0, 1], duration: 1, ease: "linear"}, t0);
    add(tl, disc, {scale: [0, 1], duration: 520, ease: "outBack(2.2)"}, t0);
    add(tl, digit, {scale: [0.2, 1], rotate: [-28, 0], translateY: [120, 0], duration: 620, ease: "outElastic(1, .55)"}, t0 + 40);
    add(tl, inner, {scale: [1, 1.7], opacity: [1, 0], rotate: [0, 14], duration: 230, ease: "inQuad"}, t0 + P.step - 230);
  },
  dots: function(tl, P, root){
    var row = el("div", "pop-dots", root);
    for (var i = 0; i < P.n; i++){
      var d = el("i", "", row), f = el("b", "", d);
      add(tl, f, {scale: [0, 1], duration: 300, ease: "outBack(3)"}, P.numAt(P.n - i) + 100);
    }
    add(tl, row, {opacity: [1, 0], translateY: [0, 60], duration: 300, ease: "inQuad"}, P.title - 150);
  },
  title: function(tl, P, root){
    var w = obj(D.world), t0 = P.title;
    var card = el("div", "pop-card", root), bob = el("div", "pop-card-bob", card), face = el("div", "pop-card-face", bob);
    R.card = card; R.bob = bob;
    add(tl, card, {translateY: [1250, 0], rotate: [8, 0], duration: 900, ease: "outBack(1.3)"}, t0 + 50);
    if (D.label){
      var lab = el("div", "pop-label", face); lab.textContent = D.label;
      add(tl, lab, {scale: [0, 1], rotate: [-20, -3], duration: 520, ease: "outBack(2.5)"}, t0 + 600);
    }
    if (D.meta){
      var meta = el("div", "pop-meta", face); meta.textContent = D.meta;
      add(tl, meta, {opacity: [0, 1], translateX: [40, 0], duration: 500, ease: "outExpo"}, t0 + 700);
    }
    var mark = el("div", "pop-mark", face), solo = !str(D.goal).trim();
    var topic = box(face, "pop-topic", D.topic, 80, 150, 1440, solo ? 420 : 280, solo ? 200 : 170, 70);
    if (solo) mark.style.top = "590px";
    add(tl, S.split(topic), {translateY: [80, 0], scale: [0.4, 1], opacity: [0, 1], duration: 650, delay: A.stagger(28), ease: "outBack(2)"}, t0 + 750);
    add(tl, mark, {scaleX: [0, 1], duration: 600, ease: "outExpo"}, t0 + 1400);
    if (!solo){
      var gl = el("div", "pop-goal-chip", face); gl.textContent = str(w.goalLabel) || "목표";
      var gx = Math.max(240, gl.offsetLeft + gl.offsetWidth + 28);
      var goal = box(face, "pop-goal", D.goal, gx, 466, 1520 - gx, 110, 52, 28);
      add(tl, gl, {scale: [0, 1], duration: 420, ease: "outBack(2.5)"}, t0 + 1650);
      add(tl, S.split(goal, "word"), {opacity: [0, 1], translateY: [24, 0], duration: 420, delay: A.stagger(45), ease: "outBack(1.6)"}, t0 + 1750);
    }
    POP.steps(tl, P, root, t0 + 2200);
    if (w.hint){
      var hint = el("div", "pop-hint", root), hi = el("span", "", hint); hi.textContent = w.hint;
      R.hint = hint;
      add(tl, hint, {opacity: [0, 1], translateY: [30, 0], duration: 500, ease: "outBack(2)"}, t0 + 2800);
      R.loops.push(A.animate(hi, {scale: [1, 1.06], duration: 700, loop: true, alternate: true, ease: "inOutSine"}));
    }
    R.loops.push(A.animate(bob, {translateY: [-6, 6], rotate: [-0.4, 0.4], duration: 2200, loop: true, alternate: true, ease: "inOutSine"}));
  },
  steps: function(tl, P, root, t0){
    var items = (D.items || []).slice(0, 5);
    if (!items.length) return;
    var w = obj(D.world), row = el("div", "pop-steps", root);
    R.steps = row;
    var sl = null;
    if (w.stepsLabel){ sl = el("div", "pop-steps-label", row); sl.textContent = w.stepsLabel; }
    var chips = items.map(function(it, i){
      var c = el("div", "pop-step", row), n = el("b", "", c), s = el("span", "", c);
      n.textContent = String(i + 1); s.textContent = str(obj(it).text || it);
      c.style.setProperty("--chip", palette()[i % 4]);
      return c;
    });
    if (sl) add(tl, sl, {opacity: [0, 1], duration: 300, ease: "linear"}, t0);
    add(tl, chips, {translateY: [80, 0], opacity: [0, 1], duration: 500, delay: A.stagger(90), ease: "outBack(2.2)"}, t0 + 80);
  },
  outro: function(tl){
    var w = obj(D.world), root = R.root;
    add(tl, R.card, {translateY: [0, -90], scale: [1, 0.46], duration: 800, ease: "inOutBack(1.2)"}, 0);
    if (R.steps) add(tl, R.steps, {opacity: [1, 0], translateY: [0, 120], duration: 400, ease: "inQuad"}, 0);
    if (R.hint) add(tl, R.hint, {opacity: [1, 0], duration: 250, ease: "linear"}, 0);
    if (w.start){
      var go = el("div", "pop-go", root), gi = el("div", "", go); gi.textContent = w.start;
      add(tl, gi, {scale: [0, 1.15, 1], rotate: [-12, 3, -2], duration: 700, ease: "outBack(2)"}, 350);
      add(tl, go, {opacity: [1, 0], scale: [1, 0.7], duration: 450, ease: "inBack(2)"}, 2300);
    }
    var r = rng(9), bits = [];
    for (var i = 0; i < 26; i++){
      var b = el("i", "pop-bit", root);
      b.style.background = palette()[i % 4];
      b.style.borderRadius = i % 3 ? "50%" : "4px";
      bits.push({e: b, a: r() * 6.283, d: 380 + r() * 520});
    }
    bits.forEach(function(b){
      add(tl, b.e, {translateX: [0, Math.cos(b.a) * b.d], translateY: [0, Math.sin(b.a) * b.d * 0.7], scale: [1.4, 0], rotate: [0, 360], duration: 1300, ease: "outCubic"}, 380);
    });
  }
};

/* ======================================================================
   SKIN 2 · calm-paper — warm paper, layered paper hills, sunrise, flip-card numbers
   ====================================================================== */
function grain(c){
  var cv = document.createElement("canvas"); cv.width = 1920; cv.height = 1080;
  var x = cv.getContext("2d"), r = rng(77);
  var g = x.createLinearGradient(0, 0, 0, 1080);
  g.addColorStop(0, c.bg1); g.addColorStop(1, c.bg2);
  x.fillStyle = g; x.fillRect(0, 0, 1920, 1080);
  var sm = document.createElement("canvas"); sm.width = 640; sm.height = 360;
  var sx = sm.getContext("2d"), id = sx.createImageData(640, 360);
  for (var i = 0; i < id.data.length; i += 4){ var v = 120 + r() * 135; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 18; }
  sx.putImageData(id, 0, 0);
  x.globalCompositeOperation = "multiply"; x.drawImage(sm, 0, 0, 1920, 1080); x.globalCompositeOperation = "source-over";
  return cv;
}
var PAPER = {
  painter: function(ctx, t, W, H){
    var P = R.plan, c = R.c, ms = t * 1000;
    if (!R.grain) R.grain = grain(c);
    ctx.drawImage(R.grain, 0, 0);
    var rise = smooth((ms - P.lead) / (P.title - P.lead + 600));
    var sunY = 900 - 560 * rise, sunX = 1460;
    ctx.save();
    ctx.shadowColor = "rgba(90,70,40,.18)"; ctx.shadowBlur = 30; ctx.shadowOffsetY = 10;
    ctx.fillStyle = c.accent; ctx.beginPath(); ctx.arc(sunX, sunY, 120, 0, 6.283); ctx.fill();
    ctx.shadowColor = "rgba(0,0,0,0)";
    ctx.globalAlpha = 0.35; ctx.fillStyle = "#ffffff"; ctx.beginPath(); ctx.arc(sunX - 30, sunY - 34, 46, 0, 6.283); ctx.fill();
    ctx.restore();
    var clouds = [[260, 230, 1.0, 0.012], [1180, 150, 0.8, 0.02], [700, 330, 0.6, 0.016]];
    clouds.forEach(function(cl, i){
      var x = ((cl[0] + t * 1920 * cl[3]) % 2300) - 200, y = cl[1] + Math.sin(t * 0.4 + i) * 6, s = cl[2];
      ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
      ctx.shadowColor = "rgba(90,70,40,.16)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 10;
      ctx.fillStyle = c.paper;
      ctx.beginPath(); ctx.arc(0, 0, 60, Math.PI, 0); ctx.arc(80, -24, 70, Math.PI, 0); ctx.arc(160, 0, 54, Math.PI, 0); ctx.closePath(); ctx.fill();
      ctx.restore();
    });
    var hills = [[c.sky, 790, 70, 0.6, 1.0], [c.primary, 860, 60, 0.9, 2.3], [c.mint, 940, 46, 1.3, 4.1], [c.paperDark, 1010, 34, 1.7, 5.7]];
    hills.forEach(function(h, i){
      ctx.save();
      ctx.shadowColor = "rgba(70,55,30,.22)"; ctx.shadowBlur = 26; ctx.shadowOffsetY = -6;
      ctx.fillStyle = h[0];
      ctx.beginPath(); ctx.moveTo(-40, H + 40);
      for (var x = -40; x <= W + 40; x += 30){
        var y = h[1] - h[2] * (0.6 * Math.sin(x * 0.0021 * h[3] + h[4] + Math.sin(t * 0.25 + i) * 0.25) + 0.4 * Math.sin(x * 0.0057 + h[4] * 2));
        ctx.lineTo(x, y);
      }
      ctx.lineTo(W + 40, H + 40); ctx.closePath(); ctx.fill();
      ctx.restore();
    });
  },
  ready: function(tl, P, root){
    var w = obj(D.world);
    if (!w.ready) return;
    var tx = el("div", "paper-ready", root); tx.textContent = w.ready;
    add(tl, tx, {opacity: [0, 1], translateY: [24, 0], duration: 900, ease: "outCubic"}, 100);
    add(tl, tx, {opacity: [1, 0], duration: 400, ease: "linear"}, P.title - 350);
  },
  number: function(tl, P, root, k){
    var t0 = P.numAt(k), wrap = el("div", "paper-num", root), mid = el("div", "paper-num-m", wrap), inner = el("div", "paper-num-o", mid);
    var disc = el("div", "paper-disc", inner), digit = el("div", "paper-digit", inner);
    disc.style.background = [R.c.sky, R.c.mint, R.c.accent, R.c.primary, R.c.paperDark][(P.n - k) % 5];
    digit.textContent = String(k);
    add(tl, wrap, {opacity: [0, 1], duration: 1, ease: "linear"}, t0 - 80);
    add(tl, inner, {rotateX: [-95, 0], translateY: [40, 0], duration: 620, ease: "outCubic"}, t0 - 80);
    add(tl, digit, {translateY: [18, 0], duration: 800, ease: "outCubic"}, t0);
    add(tl, mid, {rotateX: [0, 75], opacity: [1, 0], translateY: [0, -30], duration: 260, ease: "inCubic"}, t0 + P.step - 280);
  },
  dots: function(tl, P, root){
    var row = el("div", "paper-dots", root);
    for (var i = 0; i < P.n; i++){
      var d = el("i", "", row), f = el("b", "", d);
      add(tl, f, {scale: [0, 1], opacity: [0, 1], duration: 500, ease: "outCubic"}, P.numAt(P.n - i) + 150);
    }
    add(tl, row, {opacity: [1, 0], duration: 400, ease: "linear"}, P.title - 200);
  },
  title: function(tl, P, root){
    var w = obj(D.world), t0 = P.title;
    var card = el("div", "paper-card", root), bob = el("div", "paper-card-bob", card), face = el("div", "paper-card-face", bob);
    el("i", "paper-tape l", face); el("i", "paper-tape r", face);
    R.card = card; R.bob = bob;
    add(tl, card, {translateY: [1200, 0], rotate: [-5, -1], duration: 1300, ease: "outQuart"}, t0);
    if (D.label){
      var lab = el("div", "paper-label", face); lab.textContent = D.label;
      add(tl, lab, {opacity: [0, 1], translateY: [16, 0], duration: 700, ease: "outCubic"}, t0 + 900);
    }
    if (D.meta){
      var meta = el("div", "paper-meta", face); meta.textContent = D.meta;
      add(tl, meta, {opacity: [0, 1], duration: 700, ease: "outCubic"}, t0 + 1000);
    }
    var solo = !str(D.goal).trim();
    var topic = box(face, "paper-topic", D.topic, 90, 160, 1420, solo ? 410 : 270, solo ? 190 : 160, 64);
    add(tl, S.split(topic), {opacity: [0, 1], translateY: [30, 0], rotate: [-6, 0], duration: 700, delay: A.stagger(35), ease: "outCubic"}, t0 + 1000);
    var line = el("div", "paper-line", face);
    if (solo) line.style.top = "596px";
    add(tl, line, {scaleX: [0, 1], duration: 900, ease: "inOutCubic"}, t0 + 1700);
    if (!solo){
      var gl = el("div", "paper-goal-chip", face); gl.textContent = str(w.goalLabel) || "목표";
      var gx = Math.max(230, gl.offsetLeft + gl.offsetWidth + 28);
      var goal = box(face, "paper-goal", D.goal, gx, 470, 1520 - gx, 110, 50, 28);
      add(tl, gl, {opacity: [0, 1], scale: [0.8, 1], duration: 600, ease: "outCubic"}, t0 + 1900);
      add(tl, S.split(goal, "word"), {opacity: [0, 1], filter: ["blur(6px)", "blur(0px)"], duration: 700, delay: A.stagger(55), ease: "outCubic"}, t0 + 2000);
    }
    PAPER.steps(tl, P, root, t0 + 2500);
    if (w.hint){
      var hint = el("div", "paper-hint", root), hi = el("span", "", hint); hi.textContent = w.hint;
      R.hint = hint;
      add(tl, hint, {opacity: [0, 1], duration: 900, ease: "outCubic"}, t0 + 3100);
      R.loops.push(A.animate(hi, {opacity: [1, 0.45], duration: 1500, loop: true, alternate: true, ease: "inOutSine"}));
    }
    R.loops.push(A.animate(bob, {rotate: [-0.5, 0.5], translateY: [-4, 4], duration: 3200, loop: true, alternate: true, ease: "inOutSine"}));
  },
  steps: function(tl, P, root, t0){
    var items = (D.items || []).slice(0, 5);
    if (!items.length) return;
    var w = obj(D.world), row = el("div", "paper-steps", root);
    R.steps = row;
    var sl = null;
    if (w.stepsLabel){ sl = el("div", "paper-steps-label", row); sl.textContent = w.stepsLabel; }
    var tags = items.map(function(it, i){
      var c = el("div", "paper-step", row), n = el("b", "", c), s = el("span", "", c);
      n.textContent = String(i + 1); s.textContent = str(obj(it).text || it);
      c.style.setProperty("--tag", [R.c.sky, R.c.mint, R.c.accent, R.c.primary][i % 4]);
      return c;
    });
    if (sl) add(tl, sl, {opacity: [0, 1], duration: 600, ease: "linear"}, t0);
    tags.forEach(function(c, i){
      var tilt = (i % 2 ? 1 : -1) * (1 + i % 3);
      add(tl, c, {translateY: [60, 0], rotate: [tilt * 4, tilt], opacity: [0, 1], duration: 800, ease: "outCubic"}, t0 + 100 + i * 140);
    });
  },
  outro: function(tl){
    var w = obj(D.world), root = R.root;
    add(tl, R.card, {translateY: [0, -80], scale: [1, 0.46], duration: 1100, ease: "inOutCubic"}, 0);
    if (R.steps) add(tl, R.steps, {opacity: [1, 0], translateY: [0, 60], duration: 600, ease: "inCubic"}, 0);
    if (R.hint) add(tl, R.hint, {opacity: [1, 0], duration: 400, ease: "linear"}, 0);
    if (w.start){
      var go = el("div", "paper-go", root), gi = el("div", "", go); gi.textContent = w.start;
      add(tl, gi, {opacity: [0, 1], translateY: [40, 0], duration: 900, ease: "outCubic"}, 500);
      add(tl, go, {opacity: [1, 0], duration: 900, ease: "inOutSine"}, 2600);
    }
    var r = rng(3), bits = [];
    for (var i = 0; i < 18; i++){
      var b = el("i", "paper-bit", root);
      b.style.left = (120 + r() * 1680) + "px";
      b.style.background = [R.c.sky, R.c.mint, R.c.accent, R.c.primary][i % 4];
      bits.push({e: b, d: 900 + r() * 400, sway: (r() - 0.5) * 220, delay: r() * 800});
    }
    bits.forEach(function(b){
      add(tl, b.e, {translateY: [-80, b.d], translateX: [0, b.sway], rotate: [0, 260], opacity: [1, 1, 1, 0], duration: 2600, ease: "inOutSine"}, 300 + b.delay);
    });
  }
};

var SKINS = {"bold-pop": POP, "calm-paper": PAPER};

/* ---------- show ---------- */
function advance(){
  if (!R.root) return;
  if (R.done) return;
  var now = S.now() * 1000;
  if (now < R.plan.settled - 400){ S.seek(R.plan.settled); return; }   /* first press during the countdown: jump to the title */
  R.done = true;
  var tl = A.createTimeline({autoplay: true});
  R.skin.outro(tl);
  S.timeline(tl, 1);
}
window.SHOW = {
  start: function(){
    FITS = []; R = {loops: []};
    D = window.DOC || {};
    var skin = R.skin = SKINS[D.skin] || POP;
    R.c = {bg1: cssv("bg1", "#ffd400"), bg2: cssv("bg2", "#ff7a2e"), text: cssv("text", "#111111"), ink: cssv("ink", "#111111"),
           primary: cssv("primary", "#2440ff"), accent: cssv("accent", "#ff2e88"), mint: cssv("mint", "#16d3a0"),
           sky: cssv("sky", "#a9c6d8"), paper: cssv("paper", "#fffdf8"), paperDark: cssv("paperDark", "#c9b79a")};
    var n = clamp(parseInt(D.count, 10) || 5, 3, 10);
    var P = R.plan = makePlan(n);
    R.root = el("div", "lo-root", S.el.scene);
    S.bg(skin.painter);
    var tl = R.tl = A.createTimeline({autoplay: true});
    skin.ready(tl, P, R.root);
    for (var k = n; k >= 1; k--) skin.number(tl, P, R.root, k);
    skin.dots(tl, P, R.root);
    skin.title(tl, P, R.root);
    tl.add(R.root, {opacity: [1, 1], duration: 1, ease: "linear"}, P.total - 1);
    S.timeline(tl, P.total);
    R.loops.forEach(function(l){ S.timeline(l, 1); });
    if (!window.__loClick){
      window.__loClick = true;
      S.el.stage.addEventListener("click", function(){ advance(); });
    }
    loadFonts();
  },
  onKey: function(e){
    if (e.key === " " || e.key === "Enter" || e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === "PageDown"){
      if (e.preventDefault) e.preventDefault();
      advance();
      return true;
    }
    return false;
  },
  toText: function(){
    return [str(D.label), str(D.topic), str(D.goal)].concat((D.items || []).map(function(it, i){ return (i + 1) + ". " + str(obj(it).text || it); })).join("\n");
  }
};
})();
