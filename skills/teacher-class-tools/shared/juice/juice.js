/* TS:JUICE v1 - Game Wow kit (core). Vanilla ES2017, no dependencies, no network, no storage. Own code (MIT-compatible).
   Presets are tunable: Juice.configure({correct:{burst:{count:20}}}). See shared/juice/README.md for every parameter.
   Safety by construction: flashes go through one governor (<=3/s, small area or low alpha), reduced-motion and the
   in-page "effects off" switch turn every motion into a still, wrong answers use icon + text (never colour alone). */
(function (root) {
  'use strict';
  var doc = root.document;
  var J = root.Juice = { version: 1, hooks: {}, camera: null };

  /* ---------------------------------------------------------------- params (JSON-tunable) */
  var PARAMS = J.params = {
    input: { respondMs: 100 },
    press: { hover: 1.05, press: 0.95, backMs: 120, anticipate: 0.97 },
    correct: {
      hitStopMs: 60, kickPx: 3, kickMs: 110,
      squash: { x: 1.15, y: 0.9, ms: 150 },
      burst: { count: 18, ms: 750 }
    },
    wrong: { shakePx: 6, ms: 250 },
    score: { countMs: 650, minMs: 500, maxMs: 800 },
    timer: { pulseFrom: 5, pulseScale: 1.08 },
    streak: { tiers: [3, 5, 10], repeatEvery: 5 },
    reveal: { tensionMs: 2200, minTensionMs: 1500, maxTensionMs: 3000, podiumStepMs: 1200 },
    lowEnd: { cores: 4, memory: 4, fpsProbe: true, probeMs: 600, minFps: 40, burstScale: 0.5 },
    particles: { max: 80 },
    flash: { maxPerSec: 2, maxAlpha: 0.12, maxAlphaSmall: 0.5, maxArea: 341 * 256 },
    sound: { master: 0.9, sfx: 1.0, music: 0.5 }
  };
  function merge(a, b) {
    for (var k in b) {
      if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k])) { if (!a[k] || typeof a[k] !== 'object') a[k] = {}; merge(a[k], b[k]); } else a[k] = b[k];
    }
    return a;
  }
  J.configure = function (o) { merge(PARAMS, o || {}); return J; };

  /* ---------------------------------------------------------------- environment */
  var env = J.env = { lite: false, reduce: false, fps: 60 };
  var mq = null;
  try { mq = root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)'); } catch (e) { mq = null; }
  try {
    var nav = root.navigator || {};
    if ((nav.hardwareConcurrency && nav.hardwareConcurrency <= PARAMS.lowEnd.cores) || (nav.deviceMemory && nav.deviceMemory <= PARAMS.lowEnd.memory)) env.lite = true;
  } catch (e2) { /* keep default */ }
  /* reduced = the OS setting, the in-page "효과 줄이기" switch, or the host (engine) switch */
  J.reduced = function () { return !!(env.reduce || (mq && mq.matches) || (J.hooks.reduced && J.hooks.reduced())); };
  J.setReduce = function (b) {
    env.reduce = !!b;
    if (doc && doc.body) doc.body.classList.toggle('juice-reduce', J.reduced());
    return env.reduce;
  };
  J.probeFps = function (done) { /* a half-second rAF probe: slow machines get half the particles */
    if (!PARAMS.lowEnd.fpsProbe || !root.requestAnimationFrame) { if (done) done(env.fps); return; }
    var n = 0, t0 = 0;
    (function f(ts) {
      if (!t0) t0 = ts;
      n++;
      if (ts - t0 < PARAMS.lowEnd.probeMs) { root.requestAnimationFrame(f); return; }
      env.fps = Math.round(n * 1000 / (ts - t0));
      if (env.fps < PARAMS.lowEnd.minFps) env.lite = true;
      if (done) done(env.fps);
    })(0);
  };

  /* ---------------------------------------------------------------- stats (read by the checkers) */
  var stats = J.stats = { flashes: [], maxFlashPerSec: 0, maxFlashAreaOverAlpha: 0, flashSkipped: 0, burst: 0, shakes: 0, sounds: 0, soundNames: {}, hitStops: 0 };

  /* ---------------------------------------------------------------- tiny helpers */
  function rand(a, b) { return a + Math.random() * (b - a); }
  function pick(a) { return a[Math.floor(Math.random() * a.length)]; }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function eoCubic(k) { return 1 - Math.pow(1 - k, 3); }
  function eoQuart(k) { return 1 - Math.pow(1 - k, 4); }
  J.ease = { outCubic: eoCubic, outQuart: eoQuart, backOut: function (k) { var c = 1.70158; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); } };
  function an(el, frames, opts) { /* WAAPI helper: nothing happens when reduced / unsupported */
    if (!el || !el.animate || J.reduced()) return null;
    try { return el.animate(frames, opts); } catch (e) { return null; }
  }
  J.anim = an;
  function later(fn, ms) { return root.setTimeout(fn, ms); }
  J.rand = rand; J.pick = pick; J.clamp = clamp;
  function center(el) { var r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }
  J.center = center;
  function palette() {
    var out = [];
    try {
      var cs = root.getComputedStyle(doc.documentElement);
      ['--primary', '--accent', '--good'].forEach(function (v) { var c = cs.getPropertyValue(v).trim(); if (c) out.push(c); });
    } catch (e) { /* defaults below */ }
    return out.concat(['#ffd447', '#ffffff', '#ff8fd8']);
  }

  /* ---------------------------------------------------------------- particles (one light canvas, runs only while alive) */
  var parts = [], cv = null, cx = null, raf = 0, lastTs = 0, freezeUntil = 0, DPR = 1;
  function sizeCanvas() {
    DPR = Math.min(root.devicePixelRatio || 1, 1.5);
    cv.width = Math.round(root.innerWidth * DPR); cv.height = Math.round(root.innerHeight * DPR);
  }
  function ensureCanvas() {
    if (cv) return true;
    if (!doc || !doc.body) return false;
    cv = doc.createElement('canvas'); cv.className = 'juice-fx'; cv.setAttribute('aria-hidden', 'true');
    doc.body.appendChild(cv); cx = cv.getContext('2d'); sizeCanvas();
    root.addEventListener('resize', sizeCanvas);
    return !!cx;
  }
  function star(c, r) {
    c.beginPath();
    for (var i = 0; i < 10; i++) { var rr = i % 2 ? r * 0.45 : r, a = i * Math.PI / 5 - Math.PI / 2; c.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
    c.closePath(); c.fill();
  }
  function frame(ts) {
    var dt = Math.min(0.05, (ts - lastTs) / 1000); lastTs = ts;
    if (ts < freezeUntil) dt = 0; /* hit-stop: the burst hangs in the air for a beat */
    cx.setTransform(DPR, 0, 0, DPR, 0, 0); cx.clearRect(0, 0, root.innerWidth, root.innerHeight);
    for (var i = parts.length - 1; i >= 0; i--) {
      var p = parts[i]; p.t += dt;
      if (p.t >= p.life) { parts.splice(i, 1); continue; }
      p.vx *= p.drag; p.vy = p.vy * p.drag + p.g * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.vr * dt;
      var k = 1 - p.t / p.life;
      cx.save(); cx.globalAlpha = Math.min(1, k * 1.8); cx.translate(p.x, p.y); cx.rotate(p.rot); cx.fillStyle = p.color;
      if (p.shape === 'star') star(cx, p.size * 0.75);
      else if (p.shape === 'circle') { cx.beginPath(); cx.arc(0, 0, p.size * 0.5, 0, 6.2832); cx.fill(); }
      else if (p.shape === 'ribbon') { p.wob += dt * 12; cx.scale(1, Math.cos(p.wob)); cx.fillRect(-p.size * 0.6, -p.size * 0.22, p.size * 1.2, p.size * 0.44); }
      else cx.fillRect(-p.size * 0.5, -p.size * 0.35, p.size, p.size * 0.7);
      cx.restore();
    }
    if (parts.length) raf = root.requestAnimationFrame(frame); else { raf = 0; cx.clearRect(0, 0, root.innerWidth, root.innerHeight); }
  }
  /* burst(x, y, {count, ms, scale, colors, shapes, spread, angle, power}) - client pixels. Returns how many particles. */
  J.burst = function (x, y, o) {
    if (J.reduced() || !ensureCanvas()) return 0;
    o = o || {};
    var lite = env.lite || (J.hooks.lite && J.hooks.lite()), base = o.count || PARAMS.correct.burst.count, n = Math.round(base * (lite ? PARAMS.lowEnd.burstScale : 1));
    n = Math.max(1, Math.min(n, PARAMS.particles.max - parts.length));
    var sc = o.scale || 1, life = (o.ms || PARAMS.correct.burst.ms) / 1000, cols = o.colors || palette(), shapes = o.shapes || ['star', 'circle', 'rect'];
    var spread = o.spread == null ? Math.PI : o.spread, ang = o.angle == null ? 0 : o.angle, pw = o.power || 1;
    for (var i = 0; i < n; i++) {
      var a = ang + (spread >= Math.PI ? (i / n) * 6.2832 + rand(-0.25, 0.25) : rand(-spread, spread)), sp = rand(260, 700) * sc * pw;
      parts.push({ x: x, y: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - (o.lift == null ? 80 : o.lift) * sc, g: 1000 * sc, life: life * rand(0.7, 1), t: 0, size: rand(8, 16) * sc,
        color: pick(cols), shape: pick(shapes), rot: rand(0, 6.28), vr: rand(-9, 9), drag: 0.975, wob: rand(0, 6.28) });
    }
    stats.burst++;
    if (!raf) { lastTs = root.performance.now(); raf = root.requestAnimationFrame(frame); }
    return n;
  };
  J.confetti = function (o) { /* two side cannons, ribbons; 2x lighter on slow machines */
    if (J.reduced() || !ensureCanvas()) return 0;
    o = o || {};
    var n = Math.round((o.count || 70) * ((env.lite || (J.hooks.lite && J.hooks.lite())) ? PARAMS.lowEnd.burstScale : 1)), cols = palette(), W = root.innerWidth, H = root.innerHeight;
    n = Math.min(n, Math.max(0, PARAMS.particles.max + 40 - parts.length));
    for (var i = 0; i < n; i++) {
      var side = i % 2 ? 1 : -1, a = side < 0 ? rand(-1.3, -0.8) : rand(-2.35, -1.85), sp = rand(900, 1500) * (H / 1080);
      parts.push({ x: side < 0 ? -10 : W + 10, y: H * rand(0.6, 0.95), vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 1100, life: rand(1.8, 2.8), t: 0, size: rand(10, 18) * (H / 1080),
        color: pick(cols), shape: 'ribbon', rot: rand(0, 6.28), vr: rand(-10, 10), drag: 0.975, wob: rand(0, 6.28) });
    }
    stats.burst++;
    if (!raf) { lastTs = root.performance.now(); raf = root.requestAnimationFrame(frame); }
    return n;
  };
  J.hitStop = function (ms) { /* freeze the particle sim; hosts with their own clock also freeze via hooks.hitstop */
    ms = ms == null ? PARAMS.correct.hitStopMs : ms;
    if (J.reduced() || ms <= 0) return;
    freezeUntil = root.performance.now() + ms; stats.hitStops++;
    if (J.hooks.hitstop) J.hooks.hitstop(ms);
  };

  /* ---------------------------------------------------------------- flash governor (WCAG 2.3.1) */
  /* One door for every flash: <=maxPerSec per second; a flash bigger than 341x256 CSS px is capped to a faint tint
     (alpha <= maxAlpha) so it can never be a "general flash"; every flash is logged for the checker. */
  J.flash = function (color, alpha, ms, rect) {
    if (J.reduced() || !doc || !doc.body) return false;
    var F = PARAMS.flash, now = root.performance.now(), log = stats.flashes;
    while (log.length && now - log[0].t > 1000) log.shift();
    if (log.length >= F.maxPerSec) { stats.flashSkipped++; return false; }
    var w = rect ? rect.w : root.innerWidth, h = rect ? rect.h : root.innerHeight, area = w * h;
    var a = alpha == null ? 0.1 : alpha;
    a = Math.min(a, area > F.maxArea ? F.maxAlpha : F.maxAlphaSmall);
    log.push({ t: now, area: area, alpha: a });
    stats.maxFlashPerSec = Math.max(stats.maxFlashPerSec, log.length);
    if (area > F.maxArea && a > F.maxAlpha + 1e-9) stats.maxFlashAreaOverAlpha++;
    var d = doc.createElement('div'); d.className = 'juice-flash'; d.setAttribute('aria-hidden', 'true');
    d.style.background = color || '#fff';
    if (rect) { d.style.left = rect.x + 'px'; d.style.top = rect.y + 'px'; d.style.width = w + 'px'; d.style.height = h + 'px'; d.style.right = d.style.bottom = 'auto'; }
    doc.body.appendChild(d);
    var an1 = an(d, [{ opacity: a }, { opacity: 0 }], { duration: ms || 180, easing: 'ease-out' });
    later(function () { if (d.parentNode) d.parentNode.removeChild(d); }, (an1 ? (ms || 180) : 20) + 30);
    return true;
  };

  /* ---------------------------------------------------------------- element juice */
  J.squash = function (el, o) { /* squash & stretch 1.15x / 0.9y in 150ms, then settle */
    var s = PARAMS.correct.squash;
    return an(el, [{ transform: 'scale(1,1)' }, { transform: 'scale(' + s.x + ',' + s.y + ')', offset: 0.4 }, { transform: 'scale(0.96,1.05)', offset: 0.72 }, { transform: 'scale(1,1)' }],
      { duration: s.ms + 140, easing: 'cubic-bezier(.34,1.56,.64,1)' });
  };
  J.shakeEl = function (el, px, ms) { /* ONE decaying shake: 6px, 250ms; never repeated */
    px = px == null ? PARAMS.wrong.shakePx : px; ms = ms || PARAMS.wrong.ms; stats.shakes++;
    return an(el, [{ transform: 'translateX(0)' }, { transform: 'translateX(' + (-px) + 'px)', offset: 0.18 }, { transform: 'translateX(' + (px * 0.7) + 'px)', offset: 0.4 },
      { transform: 'translateX(' + (-px * 0.4) + 'px)', offset: 0.62 }, { transform: 'translateX(' + (px * 0.15) + 'px)', offset: 0.82 }, { transform: 'translateX(0)' }], { duration: ms, easing: 'ease-out' });
  };
  J.kick = function (px, dir) { /* camera kick 2-4px: the whole scene nudges and settles */
    var cam = J.camera; if (!cam) return null;
    px = px == null ? PARAMS.correct.kickPx : px;
    var a = dir == null ? rand(0, 6.28) : dir, x = Math.cos(a) * px, y = Math.sin(a) * px;
    return an(cam, [{ transform: 'translate(0,0)' }, { transform: 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)', offset: 0.3 }, { transform: 'translate(0,0)' }], { duration: PARAMS.correct.kickMs * 1.6, easing: 'ease-out' });
  };
  J.press = function (el) { /* programmatic press: anticipation then back-out */
    return an(el, [{ transform: 'scale(1)' }, { transform: 'scale(' + PARAMS.press.press + ')', offset: 0.4 }, { transform: 'scale(1.03)', offset: 0.8 }, { transform: 'scale(1)' }], { duration: PARAMS.press.backMs + 60, easing: 'cubic-bezier(.34,1.56,.64,1)' });
  };
  J.pop = function (el) { return an(el, [{ transform: 'scale(.6)', opacity: 0 }, { transform: 'scale(1.08)', opacity: 1, offset: 0.65 }, { transform: 'scale(1)', opacity: 1 }], { duration: 380, easing: 'cubic-bezier(.22,1,.36,1)' }); };

  var counts = typeof WeakMap === 'function' ? new WeakMap() : null;
  /* countUp(el, to, ms, {from, suffix, tick, free}) - ease-out; duration clamped to 500-800ms unless free:true */
  J.countUp = function (el, to, ms, o) {
    if (!el) return;
    o = o || {};
    var S = PARAMS.score, d = o.free ? (ms || S.countMs) : clamp(ms || S.countMs, S.minMs, S.maxMs), suffix = o.suffix || '';
    var from = o.from != null ? o.from : (parseInt(String(el.textContent).replace(/[^0-9\-]/g, ''), 10) || 0);
    var token = {}; if (counts) counts.set(el, token); else el._jc = token;
    if (J.reduced() || from === to) { el.textContent = Math.round(to) + suffix; return; }
    var t0 = root.performance.now(), lastTick = 0;
    (function f(ts) {
      if ((counts ? counts.get(el) : el._jc) !== token) return;
      var k = clamp((ts - t0) / d, 0, 1), v = Math.round(from + (to - from) * eoCubic(k));
      el.textContent = v + suffix;
      if (o.tick && ts - lastTick > 70 && k < 1) { lastTick = ts; J.sound.play('tick'); }
      if (k < 1) root.requestAnimationFrame(f); else el.textContent = Math.round(to) + suffix;
    })(t0);
  };
  /* timer pulse: last 5s a gentle once-per-second swell 1.0 -> 1.08 (no blinking). Call every frame with seconds left. */
  J.timerPulse = function (el, left, base) { /* base: a transform the element already needs, e.g. 'translateY(-58%)' */
    if (!el) return; base = base ? base + ' ' : '';
    var T = PARAMS.timer;
    if (J.reduced() || left <= 0 || left > T.pulseFrom) { if (el._jp) { el.style.transform = ''; el._jp = false; } return; }
    var ph = 1 - (left - Math.floor(left)); /* 0..1 inside the current second */
    var s = 1 + (T.pulseScale - 1) * Math.sin(Math.PI * Math.min(1, ph * 1.6));
    el.style.transform = base + 'scale(' + s.toFixed(3) + ')'; el._jp = true;
  };

  /* ---------------------------------------------------------------- banner + streak tiers (white-hat: only praise, never loss) */
  var live = null;
  J.banner = function (text, tier) {
    if (!doc || !doc.body) return null;
    if (!live) { live = doc.createElement('div'); live.className = 'juice-live'; live.setAttribute('aria-live', 'polite'); doc.body.appendChild(live); }
    var b = doc.createElement('div'); b.className = 'juice-banner t' + (tier || 1); b.textContent = text; live.appendChild(b);
    var a = an(b, [{ transform: 'translate(-50%,-30px) scale(.6)', opacity: 0 }, { transform: 'translate(-50%,0) scale(1.08)', opacity: 1, offset: 0.2 }, { transform: 'translate(-50%,0) scale(1)', opacity: 1, offset: 0.75 }, { transform: 'translate(-50%,-14px) scale(1)', opacity: 0 }], { duration: 1500, easing: 'cubic-bezier(.22,1,.36,1)' });
    later(function () { if (b.parentNode) b.parentNode.removeChild(b); }, a ? 1500 : 1400);
    return b;
  };
  /* tierOf(n) -> 0 none, 1 (3 in a row), 2 (5), 3 (10 and every 5 after) ; only fires exactly on a threshold */
  J.tierOf = function (n) {
    var t = PARAMS.streak.tiers, e = PARAMS.streak.repeatEvery;
    if (n === t[2] || (n > t[2] && (n - t[2]) % e === 0)) return 3;
    if (n === t[1]) return 2;
    if (n === t[0]) return 1;
    return 0;
  };
  var STREAK_TEXT = ['', '🔥 3연속!', '⚡ 5연속! 대단해요', '🌟 10연속! 최고예요'];
  J.streak = function (n, anchor) {
    var tier = J.tierOf(n); if (!tier) return 0;
    var c = anchor ? center(anchor) : { x: root.innerWidth / 2, y: root.innerHeight / 2 };
    J.sound.play('comboUp', { streak: n });
    J.banner(n > 10 ? '🌟 ' + n + '연속! 최고예요' : STREAK_TEXT[tier], tier);
    J.burst(c.x, c.y, { count: [0, 14, 22, 28][tier], scale: [1, 1, 1.15, 1.3][tier] });
    if (tier >= 2) J.kick(PARAMS.correct.kickPx + 1);
    if (tier === 3) { J.confetti({ count: 50 }); if (J.fx && J.fx.impactFrame) J.fx.impactFrame(); J.sound.play('fanfare'); }
    return tier;
  };

  /* ---------------------------------------------------------------- the standard feel (host-independent) */
  J.correct = function (el, o) {
    o = o || {};
    var c = el ? center(el) : { x: root.innerWidth / 2, y: root.innerHeight / 2 };
    J.squash(el); J.burst(c.x, c.y, { count: o.count, scale: o.scale }); J.kick();
    J.sound.play('correct', { streak: o.streak || 1 }); J.hitStop(); J.flash('#ffffff', 0.08, 140);
  };
  J.wrong = function (el) { /* icon + text are added by the host (never colour alone); this is only the motion + soft sound */
    J.shakeEl(el); J.sound.play('wrong');
  };

  /* ---------------------------------------------------------------- reveal tension + podium */
  /* reveal(el, to, {tensionMs, onDone, unit}) : drumroll, a number that decelerates (fast, fast, ... slow) then a burst. skip() ends it. */
  J.reveal = function (el, to, o) {
    o = o || {};
    var R = PARAMS.reveal, d = clamp(o.tensionMs || R.tensionMs, R.minTensionMs, R.maxTensionMs), unit = o.unit || '', done = false;
    function finish(skipped) {
      if (done) return; done = true; el.textContent = Math.round(to) + unit;
      if (!skipped && !J.reduced()) {
        var c = center(el);
        if (o.celebrate === false) { J.squash(el); J.burst(c.x, c.y, { count: 12, shapes: ['star'] }); J.sound.play('pop'); } /* gentle ending: still warm, never a fanfare for a low score */
        else { J.squash(el); J.burst(c.x, c.y, { count: 22, scale: 1.2 }); J.sound.play('fanfare'); J.hitStop(); }
      } else if (skipped) J.sound.play('pop');
      if (o.onDone) o.onDone(!!skipped);
    }
    var ctl = { skip: function () { finish(true); } };
    if (J.reduced()) { finish(true); return ctl; }
    J.sound.play('drumroll', { ms: d });
    var t0 = root.performance.now();
    (function f(ts) {
      if (done) return;
      var k = clamp((ts - t0) / d, 0, 1);
      el.textContent = Math.round(to * eoQuart(k)) + unit; /* quartic ease-out: the last digits crawl */
      if (k < 1) root.requestAnimationFrame(f); else finish(false);
    })(t0);
    return ctl;
  };
  function onColor(hex) { /* readable text on a team colour: black or white, whichever contrasts more */
    var m = /^#?([0-9a-f]{6})$/i.exec(String(hex || '')); if (!m) return '#ffffff';
    var n = parseInt(m[1], 16), ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    var L = 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]; return (1.05 / (L + 0.05)) >= ((L + 0.05) / 0.05) ? '#ffffff' : '#111111';
  }
  /* podium(container, teams[{name,icon,color,score}], {stepMs, onDone}) : 3rd -> 2nd -> 1st, one every 1.2s. Teams only (never individuals). */
  J.podium = function (box, teams, o) {
    o = o || {};
    var step = o.stepMs || PARAMS.reveal.podiumStepMs, list = teams.slice().sort(function (a, b) { return b.score - a.score; });
    var rank = [], r = 0; list.forEach(function (t, i) { if (i && t.score < list[i - 1].score) r = i; rank.push(r + 1); });
    var top = list.slice(0, 3), maxS = Math.max(1, list[0] ? list[0].score : 1);
    box.textContent = ''; box.classList.add('juice-podium');
    var stage = doc.createElement('div'); stage.className = 'jp-stage'; box.appendChild(stage);
    var order = top.length === 3 ? [1, 0, 2] : top.length === 2 ? [1, 0] : [0]; /* visual order: 2nd | 1st | 3rd */
    var cols = [];
    order.forEach(function (idx) {
      var t = top[idx], col = doc.createElement('div'); col.className = 'jp-col r' + rank[idx];
      var hh = Math.round(120 + 200 * (t.score / maxS)); if (top.length === 3) hh = [300, 220, 160][idx];
      col.innerHTML = '<div class="jp-who"><span class="jp-ico"></span><span class="jp-name"></span></div><div class="jp-block"><b class="jp-rank"></b><span class="jp-score"></span></div>';
      col.querySelector('.jp-ico').textContent = (rank[idx] === 1 ? '👑' : '') + (t.icon || '⭐'); col.querySelector('.jp-name').textContent = t.name;
      col.querySelector('.jp-rank').textContent = rank[idx] + '위'; col.querySelector('.jp-score').textContent = '0점';
      col.querySelector('.jp-block').style.height = hh + 'px'; col.querySelector('.jp-block').style.background = t.color || 'var(--primary)'; col.querySelector('.jp-block').style.color = /^#[0-9a-f]{6}$/i.test(String(t.color || '')) ? onColor(t.color) : '';
      col.style.visibility = 'hidden'; stage.appendChild(col); cols.push({ el: col, t: t, idx: idx, rank: rank[idx] });
    });
    var restEl = null;
    if (list.length > top.length) { /* everyone else is shown too: plain chips, no rank, no shaming */
      restEl = doc.createElement('div'); restEl.className = 'jp-rest';
      list.slice(top.length).forEach(function (t) { var c = doc.createElement('span'); c.className = 'jp-chip'; c.textContent = (t.icon || '') + ' ' + t.name + ' ' + t.score + '점'; restEl.appendChild(c); });
      box.appendChild(restEl);
    }
    var seq = top.map(function (t, i) { return top.length - 1 - i; }); /* 3rd, 2nd, 1st */
    var timers = [], finished = false;
    function show(i, quick) {
      var c = cols.filter(function (x) { return x.idx === seq[i]; })[0]; if (!c) return;
      c.el.style.visibility = 'visible';
      var sc = c.el.querySelector('.jp-score'); J.countUp(sc, c.t.score, 600, { from: 0, suffix: '점', free: true });
      if (quick || J.reduced()) { sc.textContent = c.t.score + '점'; return; }
      an(c.el, [{ transform: 'translateY(60px) scale(.85)', opacity: 0 }, { transform: 'translateY(0) scale(1.05)', opacity: 1, offset: 0.6 }, { transform: 'translateY(0) scale(1)', opacity: 1 }], { duration: 520, easing: 'cubic-bezier(.22,1,.36,1)' });
      var p = center(c.el.querySelector('.jp-block'));
      J.sound.play('podium', { step: i });
      J.burst(p.x, p.y - 30, { count: i === seq.length - 1 ? 26 : 14, scale: i === seq.length - 1 ? 1.3 : 1 });
      if (i === seq.length - 1) { J.confetti({ count: 60 }); J.hitStop(); if (restEl) restEl.style.visibility = 'visible'; }
    }
    function end(skipped) {
      if (finished) return; finished = true; timers.forEach(clearTimeout);
      if (skipped) seq.forEach(function (_, i) { show(i, true); });
      if (restEl) restEl.style.visibility = 'visible';
      if (o.onDone) o.onDone(!!skipped);
    }
    var ctl = { skip: function () { end(true); } };
    if (J.reduced()) { end(true); return ctl; }
    seq.forEach(function (_, i) { timers.push(later(function () { show(i, false); if (i === seq.length - 1) timers.push(later(function () { end(false); }, 500)); }, (o.delay || 0) + i * step)); });
    return ctl;
  };

  /* ---------------------------------------------------------------- sound: ZzFX-style parametric synth (own implementation) */
  var AC = null, master = null, sfxG = null, musG = null, muted = false, BUF = {}, SR = 44100;
  try { muted = !!(root.navigator && root.navigator.webdriver); } catch (e3) { muted = false; } /* automated checks start silent */
  J.setMuted = function (m) { muted = !!m; if (master) master.gain.value = muted ? 0 : PARAMS.sound.master; };
  J.isMuted = function () { return !!(muted || (J.hooks.muted && J.hooks.muted())); };
  function audio() {
    if (AC) return AC;
    var C = root.AudioContext || root.webkitAudioContext; if (!C) return null;
    try { AC = new C(); } catch (e) { AC = null; return null; }
    master = AC.createGain(); master.gain.value = muted ? 0 : PARAMS.sound.master; master.connect(AC.destination);
    sfxG = AC.createGain(); sfxG.gain.value = PARAMS.sound.sfx; sfxG.connect(master);
    musG = AC.createGain(); musG.gain.value = PARAMS.sound.music; musG.connect(master); /* SFX is 2x the music: 1.0 vs 0.5 */
    SR = AC.sampleRate || 44100;
    return AC;
  }
  J.unlock = function () { var c = audio(); if (c && c.state === 'suspended') { try { c.resume(); } catch (e) { /* ignore */ } } };
  if (root.addEventListener) { ['pointerdown', 'keydown'].forEach(function (ev) { root.addEventListener(ev, J.unlock, { passive: true }); }); }
  /* p = [volume, randomness, frequency, attack, sustain, release, shape, shapeCurve, slide, deltaSlide, pitchJump, pitchJumpTime,
          repeatTime, noise, modulation, bitCrush, delay, sustainVolume, decay, tremolo]   (same slots as ZzFX) -> Float32Array */
  function synth(p, sr) {
    sr = sr || 44100;
    var TAU = Math.PI * 2, vol = p[0] == null ? 1 : p[0], rnd = p[1] == null ? 0 : p[1], freq = p[2] == null ? 220 : p[2], atk = p[3] || 0, sus = p[4] || 0, rel = p[5] == null ? 0.1 : p[5];
    var shape = p[6] || 0, curve = p[7] == null ? 1 : p[7], slide = p[8] || 0, dslide = p[9] || 0, pj = p[10] || 0, pjt = p[11] || 0, rep = p[12] || 0, noise = p[13] || 0, mod = p[14] || 0, crush = p[15] || 0;
    var dly = p[16] || 0, sv = p[17] == null ? 1 : p[17], dec = p[18] || 0, trem = p[19] || 0;
    var f = freq * (1 + rnd * (Math.random() * 2 - 1)) * TAU / sr, f0 = f, sl = slide * 500 * TAU / sr / sr, sl0 = sl, ds = dslide * 500 * TAU / sr / sr / sr;
    pj = pj * TAU / sr; pjt = pjt * sr; rep = rep * sr | 0; mod = mod * TAU / sr;
    atk = atk * sr + 9; dec = dec * sr; sus = sus * sr; rel = rel * sr; dly = dly * sr;
    var len = (atk + dec + sus + rel + dly) | 0, out = new Float32Array(len), t = 0, tm = 0, j = 0, r = 0, c = 0, s = 0, i, k;
    for (i = 0; i < len; i++) {
      if (!crush || (++c % ((crush * 100) | 0)) === 0) {
        if (shape === 0) s = Math.sin(t);
        else if (shape === 1) s = 1 - 4 * Math.abs(Math.round(t / TAU) - t / TAU); /* triangle */
        else if (shape === 2) s = 1 - (((2 * t / TAU) % 2) + 2) % 2; /* saw */
        else if (shape === 3) s = Math.max(-1, Math.min(1, Math.tan(t))); /* clipped tan: reedy */
        else s = Math.sin(Math.pow(t % TAU, 3));
        var env_ = i < atk ? i / atk : i < atk + dec ? 1 - ((i - atk) / dec) * (1 - sv) : i < atk + dec + sus ? sv : i < len - dly ? (len - i - dly) / rel * sv : 0;
        k = (rep ? 1 - trem + trem * Math.sin(TAU * i / rep) : 1);
        s = k * (s < 0 ? -1 : 1) * Math.pow(Math.abs(s), curve) * vol * env_;
        if (dly) s = s / 2 + (dly > i ? 0 : (i < len - dly ? 1 : (len - i) / dly) * out[(i - dly) | 0] / 2);
      }
      out[i] = s;
      f += sl += ds; k = f * Math.cos(mod * tm++);
      t += k - k * noise * (1 - (Math.sin(i) + 1) * 1e9 % 2);
      if (pj && ++j > pjt) { f += pj; f0 += pj; j = 0; }
      if (rep && !(++r % rep)) { f = f0; sl = sl0; j = j || 1; }
    }
    return out;
  }
  J.synth = synth;
  function mf(m) { return 440 * Math.pow(2, (m - 69) / 12); } /* MIDI -> Hz */
  /* each preset returns parts [{p: zzfx params, at: seconds, vol: 0..1}] ; "streak" lifts the pitch one semitone per streak step (max +12) */
  var SND = J.presets = {
    click: function () { return [{ p: [0.45, 0, 1500, 0, 0.004, 0.02, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.6] }]; },
    pop: function () { return [{ p: [0.6, 0, 380, 0.002, 0.02, 0.09, 0, 1.4, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0.6] }]; },
    /* correct = 3 layers: soft pluck body + two-note chime + airy sparkle */
    correct: function (o) {
      var s = Math.min(12, ((o && o.streak) || 1) - 1);
      return [{ p: [0.55, 0, mf(60 + s), 0.003, 0.05, 0.16, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7], at: 0 },
        { p: [0.4, 0, mf(72 + s), 0.003, 0.04, 0.3, 0, 1, 0, 0, mf(76 + s) - mf(72 + s), 0.06, 0, 0, 0, 0, 0, 0.7], at: 0.01 },
        { p: [0.16, 0, 3800, 0.002, 0.015, 0.22, 0, 1, -2, 0, 0, 0, 0, 0.5, 0, 0, 0, 0.5], at: 0.05 }];
    },
    /* wrong = a soft low "bonk" that sinks: friendly, not a buzzer */
    wrong: function () { return [{ p: [0.55, 0, 230, 0.005, 0.07, 0.2, 1, 1, -0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0.6] }, { p: [0.3, 0, 115, 0.005, 0.04, 0.16, 0, 1, -0.2], at: 0.01 }]; },
    comboUp: function (o) {
      var s = Math.min(12, ((o && o.streak) || 3) - 1);
      return [{ p: [0.45, 0, mf(72 + s), 0.003, 0.05, 0.14, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7], at: 0 }, { p: [0.45, 0, mf(79 + s), 0.003, 0.06, 0.3, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7], at: 0.09 }];
    },
    tick: function () { return [{ p: [0.28, 0, 1800, 0, 0.003, 0.014, 0, 1] }]; },
    tickLast: function () { return [{ p: [0.42, 0, 1050, 0, 0.012, 0.06, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0.8] }]; },
    reveal: function () { return [{ p: [0.4, 0, 260, 0.12, 0.1, 0.35, 1, 1, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0.8], at: 0 }, { p: [0.5, 0, mf(84), 0.003, 0.06, 0.5, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7], at: 0.5 }]; },
    drumroll: function (o) { /* soft snare hits that speed up and swell, ending on a thump */
      var ms = (o && o.ms) || 1800, out = [], t = 0, gap = 0.13, n = 0;
      while (t * 1000 < ms - 120) { out.push({ p: [0.24 + 0.3 * Math.min(1, t * 1000 / ms), 0, 190, 0, 0.004, 0.05, 0, 1, 0, 0, 0, 0, 0, 1.4], at: t }); gap = Math.max(0.045, gap * 0.955); t += gap; n++; if (n > 80) break; }
      out.push({ p: [0.5, 0, 90, 0.002, 0.05, 0.25, 0, 1, -0.3], at: ms / 1000 - 0.1 });
      return out;
    },
    fanfare: function () {
      var seq = [[60, 0], [64, 0.12], [67, 0.24], [72, 0.4]], out = seq.map(function (x) { return { p: [0.3, 0, mf(x[0]), 0.01, 0.1, 0.18, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.6], at: x[1] }; });
      [72, 76, 79].forEach(function (m) { out.push({ p: [0.26, 0, mf(m), 0.01, 0.3, 0.5, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.6], at: 0.7 }); });
      return out;
    },
    podium: function (o) {
      var st = (o && o.step) || 0, m = [67, 72, 79][Math.min(2, st)];
      var out = [{ p: [0.5, 0, mf(m), 0.003, 0.08, 0.35, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7] }, { p: [0.3, 0, mf(m + 12), 0.003, 0.05, 0.25, 1, 1], at: 0.05 }];
      if (st >= 2) [76, 79, 84].forEach(function (x) { out.push({ p: [0.25, 0, mf(x), 0.01, 0.3, 0.5, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.6], at: 0.18 }); });
      return out;
    },
    whoosh: function () { return [{ p: [0.3, 0, 520, 0.09, 0.04, 0.22, 0, 1, -2.5, 0, 0, 0, 0, 1.6, 0, 0, 0, 0.5] }]; }
  };
  J.sound = {
    names: Object.keys(SND),
    play: function (name, o) {
      stats.sounds++; stats.soundNames[name] = (stats.soundNames[name] || 0) + 1;
      if (J.isMuted() || !SND[name]) return 0;
      var c = audio(); if (!c) return 0;
      if (c.state === 'suspended') { try { c.resume(); } catch (e) { /* ignore */ } }
      o = o || {}; var parts_ = SND[name](o), end = 0, t0 = c.currentTime + (o.delay || 0) + 0.005;
      parts_.forEach(function (pt) {
        var key = name + ':' + JSON.stringify(pt.p) + ':' + SR, b = BUF[key];
        if (!b) {
          var d = synth(pt.p, SR); if (!d.length) return;
          b = c.createBuffer(1, d.length, SR); b.getChannelData(0).set(d); BUF[key] = b;
        }
        var src = c.createBufferSource(), g = c.createGain(); src.buffer = b; g.gain.value = (pt.vol == null ? 1 : pt.vol) * (o.vol == null ? 1 : o.vol);
        src.connect(g); g.connect(sfxG); src.start(t0 + (pt.at || 0)); end = Math.max(end, (pt.at || 0) + b.duration);
      });
      return end;
    }
  };
  /* warm(): create the audio context and pre-render the common sounds while idle, so the first click is never slow */
  J.warm = function (names) {
    var c = audio(); if (!c) return;
    var list = (names || ['click', 'tick', 'correct', 'wrong', 'pop', 'tickLast', 'comboUp', 'whoosh', 'fanfare', 'podium']).slice(), i = 0;
    (function next() {
      if (i >= list.length) return;
      var parts_ = SND[list[i++]]({ streak: 1, step: 0 });
      parts_.forEach(function (pt) {
        var key = list[i - 1] + ':' + JSON.stringify(pt.p) + ':' + SR;
        if (!BUF[key]) { var d = synth(pt.p, SR); if (d.length) { var b = c.createBuffer(1, d.length, SR); b.getChannelData(0).set(d); BUF[key] = b; } }
      });
      later(next, 40);
    })();
  };
  /* optional background loop (WebAudio, no files). tempo can be ramped, e.g. before the last question. Music sits at half the SFX volume. */
  var mus = { on: false, step: 0, next: 0, tempo: 1, target: 1, bpm: 104, timer: 0 };
  var CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]];
  J.music = {
    start: function (o) {
      o = o || {}; mus.bpm = o.bpm || 104; mus.tempo = mus.target = 1; if (mus.on) return;
      var c = audio(); if (!c) return; mus.on = true; mus.next = c.currentTime + 0.1; mus.step = 0;
      mus.timer = root.setInterval(function () {
        if (!mus.on || J.isMuted()) { if (AC) mus.next = Math.max(mus.next, AC.currentTime); return; }
        mus.tempo += (mus.target - mus.tempo) * 0.05;
        while (mus.next < AC.currentTime + 0.2) {
          var st = mus.step, ch = CH[Math.floor(st / 8) % 4], dur = 60 / (mus.bpm * mus.tempo) / 2, f = mf(ch[st % 3] + (st % 8 > 3 ? 12 : 0));
          var k = 'mus:' + f.toFixed(1), b = BUF[k];
          if (!b) { var d = synth([0.22, 0, f, 0.004, 0.06, 0.2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.6], SR); b = AC.createBuffer(1, d.length, SR); b.getChannelData(0).set(d); BUF[k] = b; }
          var s = AC.createBufferSource(); s.buffer = b; s.connect(musG); s.start(mus.next);
          mus.next += dur; mus.step++;
        }
      }, 40);
    },
    stop: function () { mus.on = false; if (mus.timer) { root.clearInterval(mus.timer); mus.timer = 0; } },
    ramp: function (factor) { mus.target = clamp(factor, 0.6, 1.6); }
  };

  /* ---------------------------------------------------------------- install: press feel + input timing + low-end probe */
  J.install = function (o) {
    o = o || {};
    if (o.camera) J.camera = o.camera;
    if (doc && doc.body) { doc.body.classList.add('juice-on'); doc.body.classList.toggle('juice-reduce', J.reduced()); }
    if (o.probe !== false) J.probeFps();
    if (o.warm !== false) later(function () { J.warm(); }, 400); /* audio + sounds built while idle: the first tap is instant */
    return J;
  };
  /* "effects off" and "sound off" controls (visible words, >= 44px); host pages that have their own simply don't call this */
  J.mountToggles = function (box, o) {
    o = o || {}; var wrap = doc.createElement('div'); wrap.className = 'juice-toggles';
    function mk(txt, fn) { var b = doc.createElement('button'); b.type = 'button'; b.className = 'juice-toggle'; b.textContent = txt; b.addEventListener('click', fn); wrap.appendChild(b); return b; }
    var eb = mk('', function () { J.setReduce(!env.reduce); paint(); if (o.onReduce) o.onReduce(env.reduce); });
    var sb = mk('', function () { J.setMuted(!muted); paint(); if (!muted) J.sound.play('click'); if (o.onMute) o.onMute(muted); });
    function paint() { eb.textContent = env.reduce ? '✨ 효과 켜기' : '🌙 효과 줄이기'; sb.textContent = muted ? '🔊 소리 켜기' : '🔇 소리 끄기'; }
    paint(); box.appendChild(wrap); return { paint: paint, el: wrap };
  };
})(typeof window !== 'undefined' ? window : this);
