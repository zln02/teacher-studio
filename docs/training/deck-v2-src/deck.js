/* deck-v2 · 진행 엔진 + 3D 장면 (ES2017 문법만) */
(function () {
  'use strict';
  var REDUCED = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  if (/[?&]reduced=1/.test(location.search)) REDUCED = true;
  var NOGL = /[?&]nogl=1/.test(location.search);
  document.documentElement.className += ' js';
  var A = window.anime;
  var stage = document.getElementById('stage');
  var slides = [].slice.call(stage.querySelectorAll('.slide'));
  var notesEl = document.getElementById('notes');
  var cur = -1, step = 0, scale = 1;
  var AGENDA = ['여는 말', '내비로 이해', '같은 부탁 다른 결과', '설치', '모둠 미션', 'AI 커닝 사건', '마무리'];

  /* ---------- 무대 맞춤 ---------- */
  function fit() {
    scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    stage.style.transform = 'translate(-50%,-50%) scale(' + scale + ')';
    if (GL.active) sizeGL();
  }

  /* ---------- 빌드 ---------- */
  function maxStep(s) {
    var m = +(s.getAttribute('data-steps') || 0);
    [].forEach.call(s.querySelectorAll('[data-b]'), function (e) { m = Math.max(m, +e.getAttribute('data-b')); });
    return m;
  }
  function anim(t, p) { if (REDUCED) { p = Object.assign({}, p, { duration: 0, delay: 0 }); } return A.animate(t, p); }
  function setBuilds(s, n, instant) {
    var shown = [];
    [].forEach.call(s.querySelectorAll('[data-b]'), function (e) {
      var b = +e.getAttribute('data-b');
      var vis = n >= b;
      if (vis && e.__vis !== true) { if (instant) A.utils.set(e, { opacity: 1, translateY: 0 }); else shown.push(e); }
      if (!vis) { A.utils.remove(e); A.utils.set(e, { opacity: 0, translateY: 28 }); }
      e.__vis = vis;
    });
    if (shown.length) anim(shown, { opacity: [0, 1], translateY: [28, 0], duration: 760, delay: A.stagger(110), ease: 'outExpo' });
    [].forEach.call(s.querySelectorAll('[data-only]'), function (e) {
      var on = +e.getAttribute('data-only') === n;
      if (on && !e.__vis) { if (instant) A.utils.set(e, { opacity: 1, translateY: 0 }); else anim(e, { opacity: [0, 1], translateY: [24, 0], duration: 620, ease: 'outExpo' }); }
      if (!on && e.__vis) { A.utils.remove(e); if (instant) A.utils.set(e, { opacity: 0 }); else anim(e, { opacity: 0, duration: 220, ease: 'outQuad' }); }
      e.__vis = on;
    });
    [].forEach.call(s.querySelectorAll('[data-fbrow] div'), function (d, i) { d.className = (i + 1 === n) ? 'on' : ''; });
  }

  /* ---------- 이동 ---------- */
  function go(i, st, dir) {
    i = Math.max(0, Math.min(slides.length - 1, i));
    var s = slides[i];
    var ms = maxStep(s);
    if (st === 'end') st = ms;
    st = Math.max(0, Math.min(ms, st || 0));
    var changed = i !== cur;
    if (changed) {
      if (cur >= 0) { leave(slides[cur]); slides[cur].classList.remove('on'); }
      cur = i; step = st;
      s.classList.add('on');
      [].forEach.call(s.querySelectorAll('[data-b],[data-only]'), function (e) { e.__vis = undefined; A.utils.set(e, { opacity: 0 }); });
      setBuilds(s, st, true);
      if (!REDUCED) anim(s, { opacity: [0, 1], scale: [1.012, 1], duration: 560, ease: 'outCubic' });
      enter(s, st);
    } else {
      step = st;
      setBuilds(s, st, false);
      fxStep(s, st, dir);
    }
    sceneStep(s, st, !changed ? false : true);
    updateFoot();
    updateNotes();
    try { history.replaceState(null, '', '#' + (i + 1) + (st ? '.' + st : '')); } catch (e) {}
  }
  function next() { var s = slides[cur]; if (step < maxStep(s)) go(cur, step + 1, 1); else if (cur < slides.length - 1) go(cur + 1, 0, 1); }
  function prev() { if (step > 0) go(cur, step - 1, -1); else if (cur > 0) go(cur - 1, 'end', -1); }

  function updateFoot() {
    slides.forEach(function (s, i) {
      var f = s.querySelector('.foot');
      if (!f) { f = document.createElement('div'); f.className = 'foot'; s.appendChild(f); }
      f.innerHTML = '<span>AI에게 무기를 주면 · 박진영</span><span><b>' + pad(i + 1) + '</b> / ' + pad(slides.length) + '</span>';
    });
  }
  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function updateNotes() {
    var n = slides[cur].querySelector('.note');
    notesEl.innerHTML = '<h4>발표자 노트 · ' + (cur + 1) + ' / ' + slides.length + (maxStep(slides[cur]) ? ' · 단계 ' + step + '/' + maxStep(slides[cur]) : '') + '</h4>' + (n ? n.innerHTML : '');
  }

  /* ---------- 슬라이드별 움직임 ---------- */
  var FX = {};
  var timers = [];
  function later(fn, ms) { var t = setTimeout(fn, ms); timers.push(t); return t; }
  function every(fn, ms) { var t = setInterval(fn, ms); timers.push(t); return t; }
  function clearTimers() { timers.forEach(function (t) { clearTimeout(t); clearInterval(t); }); timers = []; }
  function enter(s, st) {
    var k = s.getAttribute('data-fx');
    if (k && FX[k] && FX[k].enter) FX[k].enter(s, st);
    [].forEach.call(s.querySelectorAll('.timer'), timerInit);
  }
  function leave(s) {
    clearTimers();
    var k = s.getAttribute('data-fx');
    if (k && FX[k] && FX[k].leave) FX[k].leave(s);
    if (s.getAttribute('data-scene')) glLeave();
  }
  function fxStep(s, st, dir) { var k = s.getAttribute('data-fx'); if (k && FX[k] && FX[k].step) FX[k].step(s, st, dir); }

  FX.section = {
    enter: function (s) {
      var ag = s.querySelector('.agenda'), c = +s.getAttribute('data-agenda');
      ag.innerHTML = AGENDA.map(function (a, i) { return '<div class="' + (i === c ? 'cur' : i < c ? 'done' : '') + '">' + a + '</div>'; }).join('');
      anim(s.querySelector('.bigno'), { opacity: [0, 0.9], translateX: [-60, 0], duration: 1100, ease: 'outExpo' });
      anim(s.querySelector('h2'), { opacity: [0, 1], translateY: [40, 0], duration: 1000, delay: 150, ease: 'outExpo' });
      anim(ag.children, { opacity: [0, 1], translateY: [20, 0], delay: A.stagger(60, { start: 300 }), duration: 600, ease: 'outExpo' });
    }
  };

  FX.install = {
    enter: function (s) {
      var tx = s.querySelector('[data-type]'), full = tx.getAttribute('data-type');
      if (REDUCED) { tx.textContent = full; return; }
      tx.textContent = '';
      var i = 0;
      later(function () { every(function () { if (i <= full.length) { tx.textContent = full.slice(0, i); i++; } }, 55); }, 500);
    }
  };
  FX.mission = {};
  FX.neq = {
    enter: function (s, st) { this.step(s, st, 0, true); },
    step: function (s, st, d, instant) {
      var sl = s.querySelector('.slash');
      var L = 140; sl.setAttribute('stroke-dasharray', L);
      var to = st >= 2 ? 0 : L;
      if (instant || REDUCED) sl.setAttribute('stroke-dashoffset', to);
      else anim(sl, { strokeDashoffset: to, duration: 700, ease: 'outExpo' });
    }
  };

  // 오늘의 한 줄: 취소선 긋기 (2단계)
  (function () {
    var s = slides[1];
    s.setAttribute('data-fx', 'motto');
    FX.motto = {
      enter: function (sl, st) { this.step(sl, st, 0, true); },
      step: function (sl, st, d, instant) {
        var x = sl.querySelector('.motto .q s');
        var v = st >= 2 ? 1 : 0;
        if (instant || REDUCED || !v) { x.style.setProperty('--strike', v); return; }
        var o = { v: 0 };
        A.animate(o, { v: 1, duration: 700, delay: 700, ease: 'inOutQuad', onUpdate: function () { x.style.setProperty('--strike', o.v); } });
      }
    };
  })();

  /* ---------- 타이머 ---------- */
  function timerInit(t) {
    if (t.__init) return; t.__init = true;
    var min = +t.getAttribute('data-min'), total = min * 60, left = total, run = false, last = 0, iv = 0;
    var ring = t.querySelector('.ring'), b = t.querySelector('b'), sp = t.querySelector('span');
    var C = 2 * Math.PI * 44; ring.setAttribute('stroke-dasharray', C);
    function draw() {
      var m = Math.floor(left / 60), sec = Math.floor(left % 60);
      b.textContent = m + ':' + (sec < 10 ? '0' : '') + sec;
      ring.setAttribute('stroke-dashoffset', C * (1 - left / total));
      sp.textContent = left <= 0 ? '끝났어요' : run ? '진행 중 · 눌러서 멈춤' : (left < total ? '멈춤 · 눌러서 계속' : '눌러서 시작');
      t.classList.toggle('done', left <= 0);
    }
    function tick() { var now = Date.now(); left = Math.max(0, left - (now - last) / 1000); last = now; if (left <= 0) { run = false; clearInterval(iv); } draw(); }
    t.toggle = function () { if (left <= 0) { left = total; run = false; draw(); return; } run = !run; if (run) { last = Date.now(); iv = setInterval(tick, 250); } else clearInterval(iv); draw(); };
    t.addEventListener('click', function (e) { e.stopPropagation(); t.toggle(); });
    draw();
  }

  /* =====================================================================
     3D (three.js r128) · 렌더러 하나를 돌려 쓰고, 보이는 슬라이드에서만 그려요
     ===================================================================== */
  var GL = { ok: false, r: null, canvas: null, active: null, sceneEl: null, raf: 0, last: 0, slow: 0, pr: 1.5, cache: {} };
  function initGL() {
    if (NOGL || !window.THREE) { document.body.classList.add('no-gl'); return; }
    try {
      var c = document.createElement('canvas');
      var ctx = c.getContext('webgl', { antialias: true, alpha: true, powerPreference: 'low-power' }) || c.getContext('experimental-webgl');
      if (!ctx) throw new Error('no webgl');
      var r = new THREE.WebGLRenderer({ canvas: c, context: ctx, antialias: true, alpha: true });
      GL.pr = Math.min(window.devicePixelRatio || 1, 1.5);
      r.setPixelRatio(GL.pr);
      r.setClearColor(0x000000, 0);
      r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
      GL.r = r; GL.canvas = c; GL.ok = true;
      c.addEventListener('webglcontextlost', function (e) { e.preventDefault(); GL.ok = false; stopLoop(); document.body.classList.add('no-gl'); });
    } catch (e) { GL.ok = false; document.body.classList.add('no-gl'); }
  }
  function sizeGL() {
    var box = GL.sceneEl.querySelector('.gl');
    var w = box.offsetWidth || 1920, h = box.offsetHeight || 1080;
    GL.r.setPixelRatio(GL.pr);
    GL.r.setSize(Math.round(w * scale), Math.round(h * scale), false);
    GL.canvas.style.width = w + 'px'; GL.canvas.style.height = h + 'px';
    GL.active.camera.aspect = w / h; GL.active.camera.updateProjectionMatrix();
    GL.active.W = w; GL.active.H = h;
  }
  function sceneStep(s, st, entering) {
    var kind = s.getAttribute('data-scene');
    var ck = s.querySelector('[data-clock]');
    if (ck && !GL.ok) ck.textContent = (+((ck.getAttribute('data-t') || '').split(',')[st]) || 0).toFixed(1);
    if (!kind || !GL.ok) return;
    if (entering || GL.sceneEl !== s) {
      var S = GL.cache[kind];
      if (!S) { S = GL.cache[kind] = SCENES[kind](s); S.kind = kind; }
      GL.active = S; GL.sceneEl = s;
      s.querySelector('.gl').appendChild(GL.canvas);
      var lb = s.querySelector('.labels');
      if (S.labels && !S.__lbl) { S.labels.forEach(function (l) { lb.appendChild(l.el); }); S.__lbl = true; }
      sizeGL();
      S.setStep(st, true);
      S.update(0, 2.0, true);
      renderOnce();
      startLoop();
    } else {
      GL.active.setStep(st, REDUCED);
      if (REDUCED) { GL.active.update(0, 2.0, true); renderOnce(); }
    }
  }
  function renderOnce() { var S = GL.active; GL.r.render(S.scene, S.camera); projectLabels(S); }
  var _v;
  function projectLabels(S) {
    if (!S.labels) return;
    if (!_v) _v = new THREE.Vector3();
    S.labels.forEach(function (l) {
      if (l.obj) l.obj.getWorldPosition(_v); else _v.copy(l.pos);
      if (l.off) _v.add(l.off);
      _v.project(S.camera);
      var x = (_v.x + 1) / 2 * S.W, y = (1 - _v.y) / 2 * S.H;
      l.el.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px) translate(-50%,-50%)';
    });
  }
  function startLoop() {
    stopLoop();
    if (REDUCED || document.hidden) return;
    GL.last = performance.now();
    var acc = 0, frames = 0;
    function loop(now) {
      GL.raf = requestAnimationFrame(loop);
      var dt = Math.min(0.2, (now - GL.last) / 1000); GL.last = now;
      // 느린 학교 PC: 평균 프레임이 40ms를 넘으면 해상도를 낮춰요
      acc += dt; frames++;
      if (acc > 2) { if (acc / frames > 0.04 && GL.pr > 0.5) { GL.pr = GL.pr > 1 ? 1 : GL.pr > 0.75 ? 0.75 : 0.5; sizeGL(); if (GL.pr <= 0.75) GL.r.shadowMap.autoUpdate = false; GL.r.shadowMap.needsUpdate = true; } acc = 0; frames = 0; }
      GL.active.update(dt, now / 1000, false);
      GL.r.render(GL.active.scene, GL.active.camera);
      projectLabels(GL.active);
    }
    GL.raf = requestAnimationFrame(loop);
  }
  function stopLoop() { if (GL.raf) cancelAnimationFrame(GL.raf); GL.raf = 0; }
  function glLeave() { stopLoop(); GL.active = null; GL.sceneEl = null; }
  document.addEventListener('visibilitychange', function () { if (document.hidden) stopLoop(); else if (GL.active) startLoop(); });

  /* =====================================================================
     3D 물건 상자 (KIT) · 점토 느낌 재질 + 부드러운 스튜디오 빛 + 테두리 빛 하나
     icons: lightbulb file-text layout-grid hammer pencil send gamepad-2 presentation clapperboard timer chart-column scale
     ===================================================================== */
  // 3D 재질 색은 여기 한 곳에서만 정해요 (어두운 키노트: 짙은 새틴 몸체 + 강조색 빛)
  var P = { cream: 0x47557f, stone2: 0x5b6a98, paper: 0xe6ecf8, slab: 0x1b2443, sand: 0x6f7ca6, ground: 0x111a31, road: 0x0a0f1e, curb: 0x2a3558, roadBad: 0x222b48,
    terra: 0x22d3ee, terra2: 0x22d3ee, teal: 0xa3e635, teal2: 0x84cc16, car: 0x3552a8, ink: 0x0e1322, brown: 0x2c3657, wood: 0x6b5442, amber: 0xf59e0b,
    mint: 0x22d3ee, cool: 0x22d3ee, coral: 0xfb7185, dk: 0x120d18, dk2: 0x1d1626, skin: 0xe9bb97, hair: 0x1c130f, leaf: 0x3d6b54, idle: 0x3a4466 };
  var CSS = { acc: '#22d3ee', acc2: '#a3e635', warm: '#f59e0b', ink: '#04131a', paper: '#eef2ff' };
  function M(color, o) { return new THREE.MeshStandardMaterial(Object.assign({ color: color, roughness: 0.62, metalness: 0.0 }, o || {})); }
  function MF(color, o) { return M(color, Object.assign({ flatShading: true, roughness: 0.78 }, o || {})); }
  function E(color, k, o) { return M(color, Object.assign({ emissive: color, emissiveIntensity: k === undefined ? 0.8 : k }, o || {})); }
  function Bm(color, o) { return new THREE.MeshBasicMaterial(Object.assign({ color: color }, o || {})); }
  function shadows(root) { root.traverse(function (o) { if (o.isMesh && !o.userData.noShadow) { o.castShadow = true; o.receiveShadow = true; } }); return root; }
  function noSh(m) { m.userData.noShadow = true; return m; }
  // 빛: 키 라이트(그림자) + 채움 빛 + 청록 테두리 빛 하나. warmSeg=AI 커닝 구간(채움 빛이 따뜻해요)
  function rig(scene, warmSeg, size, tx, tz) {
    scene.add(new THREE.HemisphereLight(warmSeg ? 0xffd9e6 : 0xbfd0ff, warmSeg ? 0x0d0810 : 0x070b16, 0.5));
    var key = new THREE.DirectionalLight(0xfff4ea, 0.95);
    key.position.set((tx || 0) + 6, 13, (tz || 0) + 9); key.target.position.set(tx || 0, 0, tz || 0); scene.add(key); scene.add(key.target);
    key.castShadow = true;
    var s = size || 12, c = key.shadow.camera; c.left = -s; c.right = s; c.top = s; c.bottom = -s; c.near = 1; c.far = 60;
    key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02;
    var fill = new THREE.DirectionalLight(warmSeg ? 0xf59e0b : 0x6d8cff, warmSeg ? 0.32 : 0.3); fill.position.set(-8, 4, 6); scene.add(fill);
    var rim = new THREE.DirectionalLight(0x22d3ee, warmSeg ? 0.9 : 1.0); rim.position.set(-4, 7, -10); scene.add(rim);
    return key;
  }
  function rrShape(w, h, r) {
    var s = new THREE.Shape(), x = -w / 2, y = -h / 2;
    r = Math.max(0.0005, Math.min(r, w / 2 - 0.0002, h / 2 - 0.0002));
    s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
    s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
    s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
    return s;
  }
  // 모서리가 둥근 상자 (점토 덩어리 기본형). 앞면이 +z
  function rbox(w, h, d, r, mat) {
    r = Math.min(r, w / 2 - 0.001, h / 2 - 0.001, d / 2 - 0.001);
    var b = Math.max(0.0005, r * 0.6), id = Math.max(0.0002, d - 2 * b);
    var g = new THREE.ExtrudeGeometry(rrShape(w - 2 * b, h - 2 * b, r * 0.7), { depth: id, bevelEnabled: true, bevelThickness: b, bevelSize: b, bevelSegments: 3, curveSegments: 6 });
    g.translate(0, 0, -id / 2);
    return new THREE.Mesh(g, mat);
  }
  function sph(r, mat, x, y, z) { var m = new THREE.Mesh(new THREE.SphereGeometry(r, 28, 20), mat); m.position.set(x || 0, y || 0, z || 0); return m; }
  function cyl(rt, rb, h, mat, seg) { return new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg || 24), mat); }
  function tex(w, h, draw) {
    var c = document.createElement('canvas'); c.width = w; c.height = h;
    var t = new THREE.CanvasTexture(c); t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; t.anisotropy = 4;
    t.redraw = function (fn) { var g = c.getContext('2d'); g.clearRect(0, 0, w, h); (fn || draw)(g, w, h); t.needsUpdate = true; };
    t.redraw(draw);
    return t;
  }
  function rr2d(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
  var FONT = '"Noto Sans KR", sans-serif';
  function hex(c) { return '#' + new THREE.Color(c).getHexString(); }
  // Lucide 아이콘(문서 안 스프라이트)을 그림으로
  function iconImg(name, color, cb) {
    var sym = document.getElementById(name); if (!sym) return;
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="192" height="192" fill="none" stroke="' + color + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + sym.innerHTML + '</svg>';
    var im = new Image(); im.onload = function () { cb(im); }; im.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  }
  function plane(w, h, t, o) { return noSh(new THREE.Mesh(new THREE.PlaneGeometry(w, h), Bm(0xffffff, Object.assign({ map: t, transparent: true }, o || {})))); }
  function blob(r, opacity, color) {
    var t = tex(128, 128, function (g) {
      var gr = g.createRadialGradient(64, 64, 2, 64, 64, 62);
      if (color) { gr.addColorStop(0, color); gr.addColorStop(1, 'rgba(0,0,0,0)'); } else { gr.addColorStop(0, 'rgba(60,35,20,' + opacity + ')'); gr.addColorStop(1, 'rgba(60,35,20,0)'); }
      g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    });
    var m = noSh(new THREE.Mesh(new THREE.PlaneGeometry(r * 2, r * 2), Bm(0xffffff, { map: t, transparent: true, depthWrite: false, blending: color ? THREE.AdditiveBlending : THREE.NormalBlending })));
    m.rotation.x = -Math.PI / 2;
    return m;
  }
  function catcher(w, d, op) { var m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.ShadowMaterial({ opacity: op || 0.18 })); m.rotation.x = -Math.PI / 2; m.receiveShadow = true; m.userData.noShadow = true; return m; }
  function lbl(text, cls, objOrPos, off) {
    var e = document.createElement('div'); e.className = 'lbl ' + (cls || ''); e.innerHTML = text;
    var l = { el: e, off: off ? new THREE.Vector3(off[0], off[1], off[2]) : null };
    if (objOrPos && objOrPos.isObject3D) l.obj = objOrPos; else l.pos = objOrPos;
    return l;
  }
  function damp(k, dt) { return 1 - Math.exp(-k * dt); }
  function V(x, y, z) { return new THREE.Vector3(x, y, z); }
  function ease(u) { u = Math.max(0, Math.min(1, u)); return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; }

  // 글씨 + 아이콘 카드 (앞면 +z)
  function card(w, h, color, text, fg, icon) {
    var g = new THREE.Group(), bg = hex(color), lum = new THREE.Color(color), fc = fg || ((lum.r * 0.3 + lum.g * 0.59 + lum.b * 0.11) > 0.45 ? CSS.ink : CSS.paper);
    var body = rbox(w, h, 0.16, Math.min(w, h) * 0.16, M(color, { roughness: 0.55 })); g.add(body);
    var W = 512, H = Math.round(512 * h / w), img = null;
    var t = tex(W, H, paint);
    function paint(c) {
      c.fillStyle = bg; rr2d(c, 0, 0, W, H, 60); c.fill();
      c.fillStyle = fc; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.font = '800 ' + (text.length > 4 ? 66 : 84) + 'px ' + FONT;
      if (icon) { if (img) c.drawImage(img, W / 2 - 64, H * 0.36 - 64, 128, 128); c.fillText(text, W / 2, H * 0.76); }
      else c.fillText(text, W / 2, H / 2 + 4);
    }
    if (icon) iconImg(icon, fc, function (im) { img = im; t.redraw(paint); });
    var face = plane(w * 0.96, h * 0.96, t); face.position.z = 0.085; g.add(face);
    g.body = body;
    return shadows(g);
  }

  /* ---- 시험 이야기에 나오는 물건들 (뉴스에 나오는 갈래 수준의 모양만) ---- */
  // 안경: cam=작은 카메라 점, disp=렌즈 안쪽 작은 화면. 폭 약 2.2
  function glassesMesh(o) {
    o = o || {};
    var g = new THREE.Group(), fm = M(o.frame || P.ink, { roughness: 0.45 });
    var lensM = new THREE.MeshStandardMaterial({ color: 0xbfe6ee, roughness: 0.08, metalness: 0.2, transparent: true, opacity: 0.28 });
    [-1, 1].forEach(function (s) {
      var sh = rrShape(0.92, 0.66, 0.26), hole = rrShape(0.74, 0.48, 0.18);
      sh.holes.push(new THREE.Path(hole.getPoints(24)));
      var rim = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.05, bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.02, bevelSegments: 2, curveSegments: 10 }), fm);
      rim.position.set(s * 0.55, 0, -0.025); g.add(rim);
      var lens = noSh(new THREE.Mesh(new THREE.ShapeGeometry(rrShape(0.76, 0.5, 0.19), 10), lensM)); lens.position.set(s * 0.55, 0, 0); g.add(lens);
      var hinge = rbox(0.16, s > 0 && o.cam ? 0.2 : 0.14, 0.18, 0.05, fm); hinge.position.set(s * 1.04, 0.12, -0.05); g.add(hinge);
      var temple = rbox(0.07, s > 0 && o.cam ? 0.11 : 0.07, 1.25, 0.03, fm); temple.position.set(s * 1.07, 0.12, -0.7); g.add(temple);
      var tip = rbox(0.07, 0.3, 0.08, 0.03, fm); tip.position.set(s * 1.07, -0.02, -1.3); tip.rotation.x = 0.4; g.add(tip);
    });
    var bridge = new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(V(-0.12, 0.12, 0), V(0, 0.26, 0.02), V(0.12, 0.12, 0)), 12, 0.035, 8), fm); g.add(bridge);
    if (o.cam) {
      var cam = new THREE.Group(); cam.position.set(1.04, 0.14, 0.05); g.add(cam);
      var bez = cyl(0.075, 0.075, 0.04, M(0x14100d, { roughness: 0.3 }), 20); bez.rotation.x = Math.PI / 2; cam.add(bez);
      var lens2 = sph(0.045, M(0x0b0b10, { roughness: 0.05, metalness: 0.6 })); lens2.scale.z = 0.5; lens2.position.z = 0.02; cam.add(lens2);
      var ring = new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.012, 8, 24), E(P.amber, 0.5)); ring.position.z = 0.02; cam.add(ring);
      g.userData.cam = cam; g.userData.ring = ring;
    }
    if (o.disp) {
      var t = tex(256, 160, function (c, w, h) { c.fillStyle = 'rgba(34,211,238,0.92)'; rr2d(c, 8, 8, w - 16, h - 16, 26); c.fill(); c.fillStyle = '#0d2a30'; c.font = '800 96px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(o.dispText || '③', w / 2, h / 2 + 4); });
      var d = plane(0.36, 0.22, t, { opacity: 0 }); d.position.set(0.62, 0.05, 0.012); g.add(d); g.userData.disp = d;
    }
    return shadows(g);
  }
  // 휴대폰 (세로, 앞면 +z). 높이 1.8
  function phoneMesh(screen) {
    var g = new THREE.Group();
    var body = rbox(0.9, 1.8, 0.12, 0.18, M(P.ink, { roughness: 0.35 })); g.add(body);
    var t = tex(256, 512, screen || function (c, w, h) {
      var gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#123c5c'); gr.addColorStop(1, '#081526'); c.fillStyle = gr; rr2d(c, 0, 0, w, h, 34); c.fill();
      c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineWidth = 14; c.lineCap = 'round';
      c.beginPath(); c.moveTo(90, 300); c.lineTo(90, 190); c.moveTo(60, 220); c.lineTo(90, 190); c.lineTo(120, 220); c.stroke();
      c.beginPath(); c.moveTo(166, 200); c.lineTo(166, 310); c.moveTo(136, 280); c.lineTo(166, 310); c.lineTo(196, 280); c.stroke();
      c.fillStyle = 'rgba(255,255,255,.35)'; rr2d(c, 98, 30, 60, 12, 6); c.fill();
    });
    var scr = plane(0.8, 1.68, t); scr.position.z = 0.065; g.add(scr); g.userData.screen = scr; g.userData.tex = t;
    var bump = rbox(0.3, 0.3, 0.06, 0.08, M(0x1d1612)); bump.position.set(-0.2, 0.62, -0.07); g.add(bump);
    return shadows(g);
  }
  // 구름 + 반짝이는 AI 별
  function star4(r, ri) { var s = new THREE.Shape(); for (var i = 0; i < 8; i++) { var a = i / 8 * Math.PI * 2 + Math.PI / 2, rr = i % 2 ? ri : r; var x = Math.cos(a) * rr, y = Math.sin(a) * rr; if (i) s.lineTo(x, y); else s.moveTo(x, y); } s.closePath(); return s; }
  function cloudMesh(dark) {
    var g = new THREE.Group(), cm = M(dark ? 0xf3ebe0 : 0xffffff, { roughness: 0.85, emissive: dark ? 0x3a2f26 : 0x000000, emissiveIntensity: dark ? 0.35 : 0 });
    [[0, 0.15, 0, 0.78], [-0.78, -0.12, 0.05, 0.55], [0.8, -0.08, 0.02, 0.6], [0.32, 0.5, -0.05, 0.55], [-0.38, 0.42, -0.08, 0.5], [0, -0.25, 0.25, 0.52], [-1.2, -0.3, 0, 0.36], [1.25, -0.3, 0, 0.38]]
      .forEach(function (b) { var s = sph(b[3], cm, b[0], b[1], b[2]); s.scale.y = 0.92; g.add(s); });
    var st = new THREE.Mesh(new THREE.ExtrudeGeometry(star4(0.42, 0.12), { depth: 0.08, bevelEnabled: true, bevelThickness: 0.04, bevelSize: 0.03, bevelSegments: 2 }), E(P.amber, 0.7, { roughness: 0.35 }));
    st.position.set(0, 0.05, 0.85); g.add(st);
    var s2 = new THREE.Mesh(new THREE.ExtrudeGeometry(star4(0.18, 0.05), { depth: 0.04, bevelEnabled: false }), E(P.amber, 0.7)); s2.position.set(0.48, 0.42, 0.8); g.add(s2);
    g.userData.star = st; g.userData.star2 = s2;
    return shadows(g);
  }
  // 초소형 이어폰 (콩 모양) + 소리 물결
  function earbudMesh(size) {
    var g = new THREE.Group(), k = size || 1;
    var body = sph(0.5 * k, M(P.cream, { roughness: 0.4 })); body.scale.set(1, 0.88, 0.9); g.add(body);
    var tip = sph(0.3 * k, M(P.mint, { roughness: 0.7 }), -0.42 * k, 0, 0); tip.scale.set(0.8, 1, 1); g.add(tip);
    var grill = cyl(0.2 * k, 0.2 * k, 0.04, M(0x8a7a6a, { roughness: 0.3, metalness: 0.4 }), 20); grill.rotation.z = Math.PI / 2; grill.position.x = 0.47 * k; g.add(grill);
    var waves = [];
    for (var i = 0; i < 3; i++) { var w = noSh(new THREE.Mesh(new THREE.TorusGeometry((0.75 + i * 0.32) * k, 0.035 * k, 8, 30, Math.PI * 0.6), Bm(P.cool, { transparent: true, opacity: 0 }))); w.rotation.z = -Math.PI * 0.3; w.position.x = -0.35 * k; g.add(w); waves.push(w); }
    g.userData.waves = waves;
    return shadows(g);
  }
  function watchMesh() {
    var g = new THREE.Group();
    var strapM = M(0x26304f, { roughness: 0.8 });
    var top = rbox(0.62, 1.0, 0.08, 0.04, strapM); top.position.set(0, 0.85, -0.12); top.rotation.x = -0.35; g.add(top);
    var bot = rbox(0.62, 1.0, 0.08, 0.04, strapM); bot.position.set(0, -0.85, -0.12); bot.rotation.x = 0.35; g.add(bot);
    var body = rbox(0.95, 1.1, 0.3, 0.28, M(P.ink, { roughness: 0.35 })); g.add(body);
    var t = tex(256, 300, function (c, w, h) { c.fillStyle = '#0f1416'; rr2d(c, 0, 0, w, h, 60); c.fill(); c.fillStyle = CSS.acc; c.font = '800 120px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('③', w / 2, h / 2 + 6); });
    var scr = plane(0.78, 0.92, t); scr.position.z = 0.155; g.add(scr);
    var crown = cyl(0.07, 0.07, 0.1, M(P.sand, { metalness: 0.3, roughness: 0.3 }), 16); crown.rotation.z = Math.PI / 2; crown.position.set(0.5, 0.18, 0); g.add(crown);
    return shadows(g);
  }
  function laptopMesh() {
    var g = new THREE.Group(), al = M(0xd9cbb8, { roughness: 0.4, metalness: 0.15 });
    var base = rbox(2.2, 1.5, 0.1, 0.05, al); base.rotation.x = -Math.PI / 2; base.position.y = 0.05; g.add(base);
    var kt = tex(512, 256, function (c, w, h) { c.fillStyle = '#cdbca6'; c.fillRect(0, 0, w, h); c.fillStyle = '#3a2d23'; for (var r = 0; r < 4; r++) for (var k = 0; k < 12; k++) { rr2d(c, 22 + k * 39.5, 18 + r * 38, 32, 30, 6); c.fill(); } c.fillStyle = '#bfae97'; rr2d(c, 186, 176, 140, 70, 10); c.fill(); });
    var kb = plane(2.0, 1.0, kt); kb.rotation.x = -Math.PI / 2; kb.position.set(0, 0.104, 0.18); g.add(kb);
    var lid = new THREE.Group(); lid.position.set(0, 0.1, -0.72); lid.rotation.x = -0.28; g.add(lid);
    var ls = rbox(2.2, 1.45, 0.07, 0.06, al); ls.position.y = 0.72; lid.add(ls);
    var st = tex(512, 336, function (c, w, h) { c.fillStyle = '#1d2a2b'; c.fillRect(0, 0, w, h); c.fillStyle = '#f2a65a'; c.beginPath(); var cx = w / 2, cy = h / 2 - 20; for (var i = 0; i < 8; i++) { var a = i / 8 * Math.PI * 2 + Math.PI / 2, r = i % 2 ? 18 : 64; c[i ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * r, cy - Math.sin(a) * r); } c.fill(); c.fillStyle = 'rgba(255,255,255,.75)'; rr2d(c, 110, h - 80, 292, 26, 13); c.fill(); });
    var scr = plane(2.02, 1.3, st); scr.position.set(0, 0.72, 0.04); lid.add(scr);
    return shadows(g);
  }
  // 키보드 + 치는 손 (평소 입구)
  function keyboardMesh() {
    var g = new THREE.Group();
    var base = rbox(2.0, 0.8, 0.12, 0.06, M(P.cream, { roughness: 0.5 })); base.rotation.x = -Math.PI / 2; g.add(base);
    var kt = tex(512, 200, function (c, w, h) { c.fillStyle = '#efe3d2'; c.fillRect(0, 0, w, h); c.fillStyle = '#6a5444'; for (var r = 0; r < 4; r++) for (var k = 0; k < 12; k++) { if (r === 3 && k > 2 && k < 9) continue; rr2d(c, 14 + k * 41, 14 + r * 46, 34, 38, 7); c.fill(); } rr2d(c, 137, 152, 238, 38, 7); c.fill(); });
    var kp = plane(1.9, 0.72, kt); kp.rotation.x = -Math.PI / 2; kp.position.y = 0.065; g.add(kp);
    var hand = new THREE.Group(); hand.position.set(0.25, 0.32, 0.12); g.add(hand);
    var skin = M(P.skin, { roughness: 0.7 });
    var palm = rbox(0.42, 0.14, 0.42, 0.07, skin); palm.rotation.x = -Math.PI / 2; hand.add(palm);
    var fingers = [];
    for (var i = 0; i < 4; i++) { var f = rbox(0.085, 0.085, 0.28, 0.04, skin); f.position.set(-0.15 + i * 0.1, -0.06, -0.3); f.rotation.x = 0.45; hand.add(f); fingers.push(f); }
    var th = rbox(0.09, 0.09, 0.22, 0.04, skin); th.position.set(-0.26, -0.04, -0.06); th.rotation.set(0.2, 0.7, 0); hand.add(th);
    var sleeve = rbox(0.36, 0.3, 0.5, 0.12, M(0x3a4a7a)); sleeve.position.set(0.03, 0.06, 0.42); sleeve.rotation.x = Math.PI / 2 - 0.25; hand.add(sleeve);
    g.userData.fingers = fingers; g.userData.hand = hand;
    return shadows(g);
  }
  // 모니터 + 대화창 (평소 출구)
  function monitorMesh() {
    var g = new THREE.Group();
    var frame = rbox(2.1, 1.4, 0.12, 0.1, M(P.ink, { roughness: 0.35 })); frame.position.y = 1.0; g.add(frame);
    var t = tex(512, 320, function (c, w, h) {
      c.fillStyle = '#eef2ff'; c.fillRect(0, 0, w, h);
      c.fillStyle = CSS.acc; rr2d(c, 230, 34, 250, 64, 26); c.fill(); c.fillStyle = CSS.ink; c.font = '700 30px ' + FONT; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText('3번 문제 풀어 줘', 254, 67);
      c.fillStyle = '#f1e2cf'; rr2d(c, 32, 130, 300, 120, 28); c.fill(); c.fillStyle = '#2b2019'; c.font = '800 44px ' + FONT; c.fillText('답: ③', 62, 178); c.fillStyle = '#a99784'; rr2d(c, 62, 212, 220, 14, 7); c.fill();
    });
    var scr = plane(1.94, 1.24, t); scr.position.set(0, 1.0, 0.065); g.add(scr);
    var neck = rbox(0.18, 0.5, 0.1, 0.04, M(P.brown)); neck.position.set(0, 0.25, -0.05); g.add(neck);
    var foot = rbox(0.8, 0.06, 0.45, 0.03, M(P.brown)); foot.position.set(0, 0.03, 0); g.add(foot);
    return shadows(g);
  }
  // 연필
  function pencilMesh() {
    var g = new THREE.Group();
    var b = cyl(0.07, 0.07, 0.8, M(P.amber, { roughness: 0.55 }), 6); g.add(b);
    var cone = cyl(0.0, 0.07, 0.18, M(0xf1d6b0), 6); cone.position.y = -0.49; cone.rotation.x = Math.PI; g.add(cone);
    var lead = cyl(0.0, 0.022, 0.06, M(0x2b2019), 6); lead.position.y = -0.56; lead.rotation.x = Math.PI; g.add(lead);
    var band = cyl(0.074, 0.074, 0.06, M(0xc9b9a3, { metalness: 0.4, roughness: 0.3 }), 16); band.position.y = 0.43; g.add(band);
    var er = cyl(0.068, 0.068, 0.1, M(0xe58c7a), 16); er.position.y = 0.51; g.add(er);
    return shadows(g);
  }
  // 날아가는 것: 문제 사진 / 답 말풍선 (늘 카메라를 봐요)
  function photoTex() {
    return tex(256, 220, function (c, w, h) {
      c.fillStyle = '#ffffff'; rr2d(c, 4, 4, w - 8, h - 8, 18); c.fill();
      c.fillStyle = '#f3ead9'; c.fillRect(20, 20, w - 40, h - 60);
      c.fillStyle = '#2b2019'; c.font = '800 34px ' + FONT; c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText('3.', 34, 34);
      c.fillStyle = '#9b8670'; [0, 1, 2].forEach(function (i) { rr2d(c, 80, 44 + i * 30, 130 - i * 30, 12, 6); c.fill(); });
      c.fillStyle = '#c4622d'; c.beginPath(); c.arc(w / 2, h - 22, 8, 0, Math.PI * 2); c.fill();
    });
  }
  function bubbleTex() {
    return tex(256, 200, function (c, w, h) {
      c.fillStyle = CSS.acc; rr2d(c, 6, 6, w - 12, h - 56, 40); c.fill();
      c.beginPath(); c.moveTo(70, h - 52); c.lineTo(60, h - 10); c.lineTo(112, h - 52); c.fill();
      c.fillStyle = '#0d2a30'; c.font = '800 70px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('답 ③', w / 2, (h - 50) / 2 + 6);
    });
  }
  // 빛나는 신호 점 (차가운 색 하나)
  function pulseMesh(r, color) {
    var g = new THREE.Group();
    g.add(noSh(sph(r, Bm(color || P.cool))));
    var h = blob(r * 4, 0, color === P.amber ? 'rgba(245,158,11,0.75)' : 'rgba(34,211,238,0.75)'); h.rotation.x = 0; g.add(h); g.userData.halo = h;
    return g;
  }
  function pathTube(curve, r, color, op) { return noSh(new THREE.Mesh(new THREE.TubeGeometry(curve, 80, r, 8, false), Bm(color || P.cool, { transparent: true, opacity: op === undefined ? 0.25 : op, depthWrite: false }))); }
  function face(o, cam) { o.quaternion.copy(cam.quaternion); }

  /* ---- 길·차·건물 (내비 장면과 공정 장면이 같이 써요) ---- */
  function ribbon(curve, w, segs, mat, y) {
    var pos = [], idx = [], up = V(0, 1, 0), side = V(0, 0, 0);
    for (var i = 0; i <= segs; i++) {
      var u = i / segs, p = curve.getPointAt(u), t = curve.getTangentAt(u);
      side.crossVectors(t, up).normalize().multiplyScalar(w / 2);
      pos.push(p.x - side.x, y, p.z - side.z, p.x + side.x, y, p.z + side.z);
      if (i < segs) { var a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
    }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
    var m = new THREE.Mesh(g, mat); m.userData.segs = segs; m.receiveShadow = true; return m;
  }
  function reveal(rib, u) { rib.geometry.setDrawRange(0, Math.floor(rib.userData.segs * Math.max(0, Math.min(1, u))) * 6); }
  function road(scene, curve, w, segs, dark) {
    var curb = ribbon(curve, w + 0.22, segs, M(P.curb, { side: THREE.DoubleSide }), 0.008); scene.add(curb);
    var r = ribbon(curve, w, segs, M(dark ? P.road : P.roadBad, { side: THREE.DoubleSide, roughness: 0.9 }), 0.014); scene.add(r);
    return r;
  }
  function dashes(curve, every, color, y, parent) {
    var L = curve.getLength(), n = Math.floor(L / every), geo = new THREE.BoxGeometry(0.08, 0.01, every * 0.45), mat = Bm(color);
    for (var i = 0; i < n; i++) { var u = (i + 0.5) / n, p = curve.getPointAt(u), t = curve.getTangentAt(u); var d = new THREE.Mesh(geo, mat); d.position.set(p.x, y, p.z); d.lookAt(p.x + t.x, y, p.z + t.z); parent.add(d); }
  }
  function carMesh(color) {
    var g = new THREE.Group(), body = M(color, { roughness: 0.45 }), glass = M(0x9fd0d6, { roughness: 0.15, metalness: 0.15 });
    var lower = rbox(0.78, 0.3, 1.36, 0.13, body); lower.rotation.x = 0; lower.position.y = 0.32; g.add(lower);
    var cab = rbox(0.66, 0.3, 0.74, 0.14, body); cab.position.set(0, 0.58, -0.1); g.add(cab);
    var ws = rbox(0.56, 0.22, 0.04, 0.03, glass); ws.position.set(0, 0.6, 0.27); ws.rotation.x = -0.45; g.add(ws);
    var rw = rbox(0.56, 0.2, 0.04, 0.03, glass); rw.position.set(0, 0.6, -0.47); rw.rotation.x = 0.45; g.add(rw);
    [-1, 1].forEach(function (s) { var sw = rbox(0.04, 0.17, 0.52, 0.03, glass); sw.position.set(s * 0.33, 0.6, -0.1); g.add(sw); });
    var wg = new THREE.CylinderGeometry(0.17, 0.17, 0.13, 20), wm = M(0x1f1712, { roughness: 0.8 }), hm = M(P.sand, { metalness: 0.3, roughness: 0.3 });
    [[-0.38, 0.42], [0.38, 0.42], [-0.38, -0.42], [0.38, -0.42]].forEach(function (p) {
      var w = new THREE.Mesh(wg, wm); w.rotation.z = Math.PI / 2; w.position.set(p[0], 0.17, p[1]); g.add(w);
      var hb = cyl(0.08, 0.08, 0.14, hm, 12); hb.rotation.z = Math.PI / 2; hb.position.set(p[0] * 1.03, 0.17, p[1]); g.add(hb);
    });
    [-1, 1].forEach(function (s) {
      var hl = sph(0.07, E(0xfff1c9, 1.0), s * 0.24, 0.34, 0.68); hl.scale.z = 0.4; g.add(hl);
      var tl = rbox(0.16, 0.06, 0.03, 0.02, E(0xe0533a, 0.6)); tl.position.set(s * 0.24, 0.38, -0.69); g.add(tl);
    });
    return shadows(g);
  }
  function treeMesh(k) {
    var g = new THREE.Group(); k = k || 1;
    var tr = cyl(0.06 * k, 0.09 * k, 0.6 * k, M(0x8a6447), 8); tr.position.y = 0.3 * k; g.add(tr);
    var c1 = new THREE.Mesh(new THREE.IcosahedronGeometry(0.5 * k, 1), MF(P.leaf)); c1.position.y = 0.9 * k; g.add(c1);
    var c2 = new THREE.Mesh(new THREE.IcosahedronGeometry(0.34 * k, 1), MF(0xadb47a)); c2.position.set(0.18 * k, 1.22 * k, 0.05 * k); g.add(c2);
    return shadows(g);
  }
  function gateMesh(color, w, h, text) {
    var g = new THREE.Group(), m = M(color, { emissive: color, emissiveIntensity: 0 });
    [-1, 1].forEach(function (s) { var p = rbox(0.22, h, 0.22, 0.06, m); p.position.set(s * w / 2, h / 2, 0); g.add(p); var cap = sph(0.14, m, s * w / 2, h + 0.06, 0); g.add(cap); });
    var beam = rbox(w + 0.34, 0.24, 0.26, 0.08, m); beam.position.y = h - 0.1; g.add(beam);
    if (text) { var sign = card(1.1, 0.46, P.cream, text, hex(color)); sign.position.set(0, h + 0.32, 0.02); g.add(sign); }
    g.userData.mat = m;
    return shadows(g);
  }
  function museumMesh() {
    var g = new THREE.Group(), stone = M(P.cream, { roughness: 0.7 }), trim = M(P.sand, { roughness: 0.7 });
    for (var i = 0; i < 3; i++) { var st = rbox(3.6 - i * 0.2, 2.3 - i * 0.14, 0.1, 0.03, trim); st.rotation.x = -Math.PI / 2; st.position.set(0, 0.05 + i * 0.1, 0.05 - i * 0.04); g.add(st); }
    var body = rbox(3.0, 1.3, 1.5, 0.05, stone); body.position.set(0, 0.95, -0.2); g.add(body);
    var colG = new THREE.CylinderGeometry(0.1, 0.11, 1.1, 14);
    for (var c = 0; c < 6; c++) { if (c === 2 || c === 3) continue; var cc = new THREE.Mesh(colG, stone); cc.position.set(-1.3 + c * 0.52, 0.85, 0.75); g.add(cc); var cap2 = rbox(0.3, 0.07, 0.3, 0.02, trim); cap2.position.set(cc.position.x, 1.43, 0.75); g.add(cap2); }
    var ent = rbox(3.3, 0.18, 0.62, 0.03, trim); ent.position.set(0, 1.55, 0.6); g.add(ent);
    var tri = new THREE.Shape(); tri.moveTo(-1.75, 0); tri.lineTo(1.75, 0); tri.lineTo(0, 0.66); tri.lineTo(-1.75, 0);
    var pm = new THREE.Mesh(new THREE.ExtrudeGeometry(tri, { depth: 2.1, bevelEnabled: true, bevelThickness: 0.03, bevelSize: 0.03, bevelSegments: 1 }), M(P.stone2, { roughness: 0.6 })); pm.position.set(0, 1.64, -1.2); g.add(pm);
    var badge = sph(0.14, E(P.teal, 0.6), 0, 1.86, 0.94); badge.scale.z = 0.3; g.add(badge);
    // 정문 (가운데) · 엉뚱한 문 (옆)
    var doorM = M(0x3a2d23, { emissive: P.teal, emissiveIntensity: 0 });
    var door = rbox(0.62, 0.86, 0.06, 0.04, doorM); door.position.set(0, 0.73, 0.56); g.add(door);
    var gate = gateMesh(P.teal, 1.2, 1.0); gate.position.set(0, 0.3, 1.25); g.add(gate);
    var sideM = M(0x3a2d23, { emissive: P.terra2, emissiveIntensity: 0 });
    var side = rbox(0.06, 0.6, 0.4, 0.03, sideM); side.position.set(1.52, 0.6, -0.4); g.add(side);
    g.userData = { gate: gate.userData.mat, door: doorM, side: sideM };
    return shadows(g);
  }
  function schoolMesh() {
    var g = new THREE.Group();
    var b = rbox(1.9, 0.95, 0.95, 0.05, M(P.cream, { roughness: 0.7 })); b.position.y = 0.48; g.add(b);
    var tri = new THREE.Shape(); tri.moveTo(-1.05, 0); tri.lineTo(1.05, 0); tri.lineTo(0, 0.42); tri.lineTo(-1.05, 0);
    var roof = new THREE.Mesh(new THREE.ExtrudeGeometry(tri, { depth: 1.05, bevelEnabled: false }), M(P.stone2)); roof.position.set(0, 0.95, -0.52); g.add(roof);
    for (var i = 0; i < 4; i++) { if (i === 2) continue; var w = rbox(0.26, 0.24, 0.04, 0.02, M(0x9fd0d6, { roughness: 0.2 })); w.position.set(-0.66 + i * 0.44, 0.58, 0.48); g.add(w); }
    var d = rbox(0.28, 0.42, 0.04, 0.03, M(P.brown)); d.position.set(0.22, 0.22, 0.48); g.add(d);
    var clock = cyl(0.13, 0.13, 0.04, M(P.paper), 20); clock.rotation.x = Math.PI / 2; clock.position.set(0, 1.17, 0.55); g.add(clock);
    var p = cyl(0.025, 0.025, 1.2, M(P.brown), 8); p.position.set(-1.2, 0.6, 0.3); g.add(p);
    var f = rbox(0.36, 0.22, 0.02, 0.01, M(P.terra)); f.position.set(-1.0, 1.06, 0.3); g.add(f);
    return shadows(g);
  }
  function postMesh(color) {
    var g = new THREE.Group();
    var foot = cyl(0.12, 0.14, 0.06, M(P.brown), 16); foot.position.y = 0.03; g.add(foot);
    var pole = cyl(0.035, 0.04, 1.0, M(P.brown), 10); pole.position.y = 0.5; g.add(pole);
    var ball = sph(0.17, M(P.idle, { emissive: color, emissiveIntensity: 0, roughness: 0.3 })); ball.position.y = 1.08; g.add(ball);
    var hat = cyl(0.05, 0.2, 0.1, M(P.brown), 16); hat.position.y = 1.25; g.add(hat);
    var glow = blob(0.5, 0, 'rgba(163,230,53,0.55)'); glow.position.y = 1.08; glow.rotation.x = 0; glow.material.opacity = 0; g.add(glow);
    g.userData = { ball: ball, glow: glow, v: 0, color: color };
    return shadows(g);
  }
  function lightPost(p, on, dt, snap, cam) {
    var d = p.userData; d.v += ((on ? 1 : 0) - d.v) * (snap ? 1 : damp(4, dt));
    d.ball.material.emissiveIntensity = d.v * 0.9; d.ball.material.color.setHex(on ? d.color : P.idle);
    d.glow.material.opacity = d.v * 0.6; if (cam) d.glow.quaternion.copy(cam.quaternion);
  }
  function drive(c, curve, u) {
    u = Math.max(0, Math.min(1, u));
    var p = curve.getPointAt(u), t = curve.getTangentAt(u);
    c.position.set(p.x, 0.02, p.z); c.lookAt(p.x + t.x, 0.02, p.z + t.z);
  }
  function groundBox(w, d, color, x, z) { var m = rbox(w, d, 0.3, 0.12, M(color, { roughness: 0.95 })); m.rotation.x = -Math.PI / 2; m.position.set(x || 0, -0.15, z || 0); m.receiveShadow = true; return m; }

  // 공정 정거장 물건 여섯: 전구 · 대본 · 콘티 · 톱니 · 연필 · 종이비행기
  function stationObj(i) {
    var g = new THREE.Group();
    if (i === 0) {
      var bulb = sph(0.32, M(0xfff3cf, { emissive: 0xf2c66a, emissiveIntensity: 0.25, roughness: 0.25 }), 0, 0.12, 0); g.add(bulb); g.userData.glowM = bulb.material;
      var neck = cyl(0.15, 0.13, 0.14, M(P.sand, { metalness: 0.4, roughness: 0.3 }), 16); neck.position.y = -0.24; g.add(neck);
      for (var k = 0; k < 2; k++) { var th = new THREE.Mesh(new THREE.TorusGeometry(0.13, 0.025, 8, 20), M(P.sand, { metalness: 0.4, roughness: 0.3 })); th.rotation.x = Math.PI / 2; th.position.y = -0.2 - k * 0.06; g.add(th); }
      var tipb = sph(0.07, M(P.brown), 0, -0.36, 0); g.add(tipb);
    } else if (i === 1) {
      var pg = rbox(0.52, 0.68, 0.05, 0.04, M(P.paper)); g.add(pg);
      var t1 = tex(200, 260, function (c) { c.fillStyle = '#a8471c'; c.fillRect(20, 26, 90, 16); c.fillStyle = '#9b8670'; for (var r = 0; r < 6; r++) { c.fillRect(20, 70 + r * 30, r % 3 === 2 ? 110 : 160, 10); } });
      var f1 = plane(0.48, 0.64, t1); f1.position.z = 0.03; g.add(f1);
    } else if (i === 2) {
      var bd = rbox(0.78, 0.56, 0.06, 0.04, M(P.ink)); g.add(bd);
      var t2 = tex(280, 200, function (c) { c.fillStyle = '#fffaf3'; for (var r = 0; r < 2; r++) for (var k2 = 0; k2 < 3; k2++) { rr2d(c, 14 + k2 * 88, 16 + r * 92, 76, 76, 10); c.fill(); } c.fillStyle = '#c4622d'; c.beginPath(); c.arc(52, 54, 16, 0, 7); c.fill(); c.fillStyle = '#2f6b66'; c.fillRect(118, 60, 52, 20); c.fillStyle = '#f2a65a'; c.beginPath(); c.moveTo(210, 80); c.lineTo(250, 80); c.lineTo(230, 40); c.fill(); });
      var f2 = plane(0.72, 0.5, t2); f2.position.z = 0.035; g.add(f2);
    } else if (i === 3) {
      var gs = new THREE.Shape(), n = 10;
      for (var q = 0; q < n * 2; q++) { var a = q / (n * 2) * Math.PI * 2, r = q % 2 ? 0.27 : 0.36; var a2 = a + Math.PI / (n * 2); if (!q) gs.moveTo(Math.cos(a) * r, Math.sin(a) * r); else gs.lineTo(Math.cos(a) * r, Math.sin(a) * r); gs.lineTo(Math.cos(a2) * r, Math.sin(a2) * r); }
      var hole = new THREE.Path(); hole.absarc(0, 0, 0.1, 0, Math.PI * 2, true); gs.holes.push(hole);
      var gear = new THREE.Mesh(new THREE.ExtrudeGeometry(gs, { depth: 0.1, bevelEnabled: true, bevelThickness: 0.025, bevelSize: 0.02, bevelSegments: 2 }), M(P.teal, { roughness: 0.45 })); gear.position.z = -0.05; g.add(gear);
    } else if (i === 4) {
      var pc = pencilMesh(); pc.scale.setScalar(0.85); pc.rotation.z = -0.7; g.add(pc);
    } else {
      var geo = new THREE.BufferGeometry();
      var v = [0, 0, 0.45, -0.42, 0.05, -0.32, 0, 0.02, -0.3, 0, 0.02, -0.3, 0.42, 0.05, -0.32, 0, 0, 0.45, 0, 0, 0.45, 0, 0.02, -0.3, 0, -0.16, -0.3];
      geo.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); geo.computeVertexNormals();
      var pl = new THREE.Mesh(geo, M(P.paper, { side: THREE.DoubleSide, flatShading: true })); pl.rotation.set(0.25, 0.6, 0.1); g.add(pl);
    }
    return shadows(g);
  }

  var SCENES = {};

  /* 표지: 공정 카드 여섯 장이 두 줄로 떠 있고, 빛이 기획 → 배포로 지나가요 */
  SCENES.cover = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
    cam.position.set(0, 0.4, 19); cam.lookAt(0.4, 0, 0);
    rig(scene, false, 9, 5.5, 0);
    var grp = new THREE.Group(); grp.position.set(6.0, 0.1, 0); grp.scale.setScalar(0.8); scene.add(grp);
    var defs = [['기획', P.terra, null, 'lightbulb'], ['대본', P.teal, null, 'file-text'], ['콘티', P.paper, '#2b2019', 'layout-grid'],
      ['제작', P.terra2, null, 'hammer'], ['수정', P.sand, '#2b2019', 'pencil'], ['배포', P.ink, null, 'send']];
    var pos = [[-2.45, 1.15, 0.3], [0, 1.45, -0.2], [2.45, 1.15, 0.3], [-2.45, -1.25, 0.1], [0, -0.95, -0.3], [2.45, -1.25, 0.1]];
    var items = defs.map(function (d, i) {
      var c = card(2.15, 1.5, d[1], d[0], d[2], d[3]);
      c.userData = { p: V(pos[i][0], pos[i][1], pos[i][2]), ph: i * 1.1 };
      grp.add(c); return c;
    });
    var path = new THREE.CatmullRomCurve3(pos.map(function (p) { return V(p[0], p[1], p[2] + 0.2); }), false, 'catmullrom', 0.4);
    var tube = pathTube(path, 0.035, P.terra2, 0.35); tube.position.z = -0.35; grp.add(tube);
    var pulse = pulseMesh(0.1, P.amber); grp.add(pulse);
    var sh = catcher(14, 8, 0.12); sh.position.set(0, -2.6, 0); grp.add(sh);
    var mx = 0, my = 0;
    window.addEventListener('mousemove', function (e) { mx = e.clientX / window.innerWidth - 0.5; my = e.clientY / window.innerHeight - 0.5; });
    var S = { scene: scene, camera: cam, labels: [], pu: 0,
      setStep: function () {},
      update: function (dt, t, snap) {
        items.forEach(function (c) {
          var u = c.userData;
          c.position.copy(u.p); c.position.y += snap ? 0 : Math.sin(t * 0.9 + u.ph) * 0.08;
          c.rotation.set(-0.05 + (snap ? 0 : Math.sin(t * 0.5 + u.ph) * 0.04), -0.22 + (snap ? 0 : Math.sin(t * 0.4 + u.ph) * 0.06), 0);
        });
        S.pu = snap ? 0.42 : (S.pu + dt * 0.12) % 1;
        pulse.position.copy(path.getPointAt(S.pu)); pulse.position.z += 0.1; face(pulse.userData.halo, cam);
        var tx = mx * 1.0, ty = 0.4 - my * 0.6;
        cam.position.x += (tx - cam.position.x) * (snap ? 1 : damp(2, dt)); cam.position.y += (ty - cam.position.y) * (snap ? 1 : damp(2, dt));
        cam.lookAt(0.4, 0, 0);
      } };
    return S;
  };

  // 길을 묻는 행인 (서서 한쪽 팔로 가리켜요)
  function passerMesh() {
    var g = new THREE.Group(), coat = M(P.teal2, { roughness: 0.75 }), skin = M(P.skin, { roughness: 0.7 }), dark = M(0x3b3029);
    [-0.09, 0.09].forEach(function (x) { var l = rbox(0.12, 0.5, 0.13, 0.05, dark); l.position.set(x, 0.27, 0); g.add(l); var s = rbox(0.13, 0.07, 0.22, 0.03, M(0x2b2019)); s.position.set(x, 0.035, 0.04); g.add(s); });
    var body = rbox(0.42, 0.6, 0.26, 0.12, coat); body.position.y = 0.82; g.add(body);
    var head = sph(0.15, skin, 0, 1.3, 0); g.add(head);
    var hair = new THREE.Mesh(new THREE.SphereGeometry(0.16, 28, 20, 0, Math.PI * 2, 0, Math.PI * 0.5), M(0x5a3a26)); hair.position.set(0, 1.31, -0.01); hair.rotation.x = -0.3; g.add(hair);
    var cap = cyl(0.17, 0.17, 0.05, M(P.brown), 24); cap.position.set(0, 1.43, 0); g.add(cap);
    var la = rbox(0.1, 0.46, 0.11, 0.045, coat); la.position.set(-0.27, 0.8, 0); la.rotation.z = 0.12; g.add(la);
    var arm = new THREE.Group(); arm.position.set(0.24, 1.02, 0); g.add(arm);
    var ra = rbox(0.1, 0.5, 0.11, 0.045, coat); ra.position.y = 0.22; arm.add(ra); arm.add(sph(0.055, skin, 0, 0.5, 0));
    arm.rotation.z = -1.25;
    g.userData.arm = arm;
    return shadows(g);
  }

  /* 같은 차, 다른 도착: 왼쪽은 묻고 헤매다 엉뚱한 문, 오른쪽은 곧장 정문 */
  SCENES.nav = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
    rig(scene, false, 14, 0, 0);
    scene.add(groundBox(23.5, 11.6, P.ground));
    var mid = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.02, 11), Bm(0x2a3558)); mid.position.y = 0.01; scene.add(mid);
    var CX = [-5.2, 5.2], passer = null;
    var parts = CX.map(function (cx, side) {
      var sc = schoolMesh(); sc.position.set(cx, 0, 4.3); scene.add(sc);
      var mu = museumMesh(); mu.position.set(cx, 0, -4.1); scene.add(mu);
      var pts = side === 0
        ? [V(cx, 0, 3.5), V(cx - 2.4, 0, 2.7), V(cx - 1.0, 0, 1.3), V(cx + 2.2, 0, 1.8), V(cx + 2.6, 0, 0.3), V(cx + 0.2, 0, -0.5), V(cx - 2.3, 0, -0.1), V(cx - 2.9, 0, -1.8), V(cx - 1.0, 0, -2.6), V(cx + 2.3, 0, -2.5), V(cx + 2.5, 0, -4.4), V(cx + 1.9, 0, -4.5)]
        : [V(cx, 0, 3.5), V(cx, 0, 1.0), V(cx, 0, -1.4), V(cx, 0, -2.75)];
      var curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.5);
      road(scene, curve, side === 0 ? 0.55 : 0.85, 220, side === 1);
      var lit = ribbon(curve, 0.14, 220, Bm(side === 0 ? P.amber : P.mint, { side: THREE.DoubleSide }), 0.022); scene.add(lit); reveal(lit, 0);
      if (side === 1) dashes(curve, 0.7, 0x5d6b94, 0.018, scene);
      var car = carMesh(P.car); scene.add(car); drive(car, curve, 0);
      if (side === 0) { passer = passerMesh(); passer.position.set(cx + 3.25, 0, 1.0); passer.rotation.y = -0.9; scene.add(passer); }
      return { curve: curve, lit: lit, car: car, mu: mu, sc: sc, u: 0, dur: side === 0 ? 6.0 : 3.2 };
    });
    [[-10.6, 3.5], [-10.4, -1], [-0.9, 2.6], [-0.8, -2.2], [0.9, 0.5], [10.6, 3.2], [10.5, -1.6], [-8.6, 5.0], [8.4, -0.6], [2.6, 3.9], [-2.6, 4.2], [7.9, 2.4]].forEach(function (p, i) { var t = treeMesh(0.75 + (i % 3) * 0.15); t.position.set(p[0], 0, p[1]); t.rotation.y = i; scene.add(t); });
    var L = [lbl('출발', 'st', parts[0].sc, [-2.0, 0.4, 0.2]), lbl('출발', 'st', parts[1].sc, [-2.0, 0.4, 0.2]),
      lbl('목적지', 'st', parts[0].mu, [0, 2.9, 0]), lbl('목적지', 'st', parts[1].mu, [0, 2.9, 0]),
      lbl('엉뚱한 문', 'ck bad', parts[0].mu, [2.4, 1.2, -0.4]), lbl('✓ 정문', 'ck', parts[1].mu, [0, 1.75, 1.7]),
      lbl('「아마 저쪽일걸요?」', 'say', passer, [0, 2.2, 0])];
    L[4].el.style.opacity = 0; L[5].el.style.opacity = 0; L[6].el.style.opacity = 0;
    cam.position.set(0, 31, 16.5); cam.lookAt(0, 0, -0.3);
    var S = { scene: scene, camera: cam, labels: L, st: 0,
      setStep: function (n, snap) { S.st = n; if (snap) { parts[0].u = n >= 1 ? 1 : 0; parts[1].u = n >= 2 ? 1 : 0; } },
      update: function (dt, t, snap) {
        parts.forEach(function (P2, side) {
          var go = S.st >= side + 1;
          if (!go) P2.u = 0; else if (!snap) P2.u = Math.min(1, P2.u + dt / P2.dur);
          var e = side === 0 ? P2.u : ease(P2.u);
          drive(P2.car, P2.curve, e); reveal(P2.lit, e);
          if (side === 0 && go && P2.u < 1 && !snap) P2.car.rotation.z = Math.sin(t * 6) * 0.03;
          var arrived = P2.u >= 1;
          if (side === 0) {
            P2.mu.userData.side.emissiveIntensity = arrived ? 0.8 : 0; L[4].el.style.opacity = arrived ? 1 : 0;
            var asked = go && P2.u > 0.24; L[6].el.style.opacity = asked ? 1 : 0;
            passer.userData.arm.rotation.z = -1.25 + (asked && !snap ? Math.sin(t * 4) * 0.12 : 0);
          } else { P2.mu.userData.gate.emissiveIntensity = arrived ? 0.6 : 0; P2.mu.userData.door.emissiveIntensity = arrived ? 0.9 : 0; L[5].el.style.opacity = arrived ? 1 : 0; }
        });
      } };
    return S;
  };

  /* 실제로 해 보면: 여섯 정류장 (길·차 없이, 정류장마다 그 일을 뜻하는 물건) */
  SCENES.pipeline = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.1, 100);
    rig(scene, false, 14, 0, 0);
    var names = ['기획', '대본', '콘티', '제작', '수정', '배포'];
    var X = [-8.5, -5.1, -1.7, 1.7, 5.1, 8.5];
    var pts = X.map(function (x, i) { return V(x, 0, i % 2 ? -0.5 : 0.5); });
    var sh = catcher(26, 10, 0.16); sh.position.y = -0.02; scene.add(sh);
    var curve = new THREE.CatmullRomCurve3(pts.map(function (p) { return V(p.x, 0.12, p.z + 0.9); }), false, 'catmullrom', 0.5);
    var tube = pathTube(curve, 0.04, P.sand, 0.9); scene.add(tube);
    var tubeOn = pathTube(curve, 0.05, P.terra2, 1); tubeOn.geometry.setDrawRange(0, 0); scene.add(tubeOn);
    var idxCount = tubeOn.geometry.index.count;
    var tAt = pts.map(function (p, i) { return i / (pts.length - 1); });
    var stations = pts.map(function (p, i) {
      var g = new THREE.Group(); g.position.copy(p); scene.add(g);
      var pad = cyl(1.2, 1.28, 0.16, M(P.slab, { roughness: 0.6 }), 48); pad.position.y = 0.08; g.add(shadows(pad));
      var ring = new THREE.Mesh(new THREE.TorusGeometry(1.24, 0.05, 8, 64), M(P.idle, { emissive: P.terra2, emissiveIntensity: 0 })); ring.rotation.x = Math.PI / 2; ring.position.y = 0.17; g.add(ring);
      var puls = noSh(new THREE.Mesh(new THREE.RingGeometry(1.24, 1.4, 64), Bm(P.terra2, { transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }))); puls.rotation.x = -Math.PI / 2; puls.position.y = 0.18; g.add(puls);
      var ob = stationObj(i); ob.scale.setScalar(1.6); ob.position.set(0, 1.0, 0); g.add(ob);
      g.userData = { ring: ring, puls: puls, glow: 0, pt: 0, ob: ob };
      return g;
    });
    var pulse = pulseMesh(0.11, P.amber); scene.add(pulse);
    var gateStep = [1, 3, 6];
    var labels = stations.map(function (g, i) { return lbl((i + 1) + ' ' + names[i], 'st', g, [0, -0.2, 1.7]); });
    var ckl = gateStep.map(function (s) { return lbl('✓ 내가 고르기', 'ck', stations[s - 1], [0, 2.35, 0]); });
    var S = { scene: scene, camera: cam, labels: labels.concat(ckl), st: 0, u: 0, camX: 0,
      setStep: function (n, snap) { S.st = n; S.target = n === 0 ? 0 : tAt[n - 1]; if (snap) { S.u = S.target; stations.forEach(function (g, i) { g.userData.glow = n >= i + 1 ? 1 : 0; }); } },
      update: function (dt, t, snap) {
        S.u += (S.target - S.u) * (snap ? 1 : damp(1.6, dt));
        var pu = curve.getPointAt(Math.max(0, Math.min(1, S.u)));
        pulse.position.copy(pu); pulse.position.y += 0.05; face(pulse.userData.halo, cam); pulse.visible = S.st > 0;
        tubeOn.geometry.setDrawRange(0, Math.floor(idxCount * S.u / 6) * 6);
        stations.forEach(function (g, i) {
          var on = S.st >= i + 1, here = S.st === i + 1, d = g.userData;
          d.glow += ((on ? 1 : 0) - d.glow) * (snap ? 1 : damp(3, dt));
          d.ring.material.emissiveIntensity = d.glow * 0.9; d.ring.material.color.setHex(on ? P.terra2 : P.idle);
          d.ob.rotation.y = snap ? 0.3 : Math.sin(t * (here ? 1.6 : 0.5) + i) * (here ? 0.6 : 0.25);
          d.ob.position.y = 1.0 + (here && !snap ? Math.sin(t * 3) * 0.07 : 0) + (here ? 0.2 : 0);
          d.ob.scale.setScalar(1.6 * (1 + (here ? 0.2 : 0)));
          if (d.ob.userData.glowM) d.ob.userData.glowM.emissiveIntensity = on ? 0.9 : 0.2;
          if (here && !snap) { d.pt = (d.pt + dt * 0.8) % 1; d.puls.scale.setScalar(1 + d.pt * 0.6); d.puls.material.opacity = (1 - d.pt) * 0.5; } else d.puls.material.opacity = 0;
          labels[i].el.className = 'lbl st' + (here ? ' on' : '') + (S.st && !on ? ' dim' : '');
        });
        ckl.forEach(function (l, i) { l.el.style.opacity = S.st >= gateStep[i] ? 1 : 0; });
        var cx = S.st === 0 ? 0 : pu.x * 0.45;
        S.camX += (cx - S.camX) * (snap ? 1 : damp(1.4, dt));
        cam.position.set(S.camX, 7.2, 17); cam.lookAt(S.camX, 0.2, -0.6);
      } };
    cam.position.set(0, 7.2, 17);
    return S;
  };


  /* 내비 = 길 안내 + 쓸 도구들: 도구 카드가 차 지붕에 착 붙고, 차가 맞는 길로 가요 */
  SCENES.tools = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
    rig(scene, false, 12, 4.5, -2);
    scene.add(groundBox(22, 16, P.ground, 4.5, -3));
    var start = V(4.0, 0, 3.2);
    var good = new THREE.CatmullRomCurve3([start, V(4.4, 0, 0.6), V(5.6, 0, -2.6), V(6.2, 0, -6.2)], false, 'catmullrom', 0.5);
    var bad = new THREE.CatmullRomCurve3([V(4.4, 0, 0.6), V(2.6, 0, -0.6), V(0.8, 0, -2.0), V(1.6, 0, -4.2), V(0.2, 0, -6.4)], false, 'catmullrom', 0.5);
    road(scene, bad, 0.6, 120, false);
    road(scene, good, 0.95, 160, true);
    dashes(good, 0.7, 0x5d6b94, 0.018, scene);
    var lit = ribbon(good, 0.14, 160, Bm(P.mint, { side: THREE.DoubleSide }), 0.024); scene.add(lit); reveal(lit, 0);
    var mu = museumMesh(); mu.position.set(6.4, 0, -8.6); mu.scale.setScalar(0.9); scene.add(mu);
    [[1.2, 2.4], [8.6, 1.6], [9.0, -3.4], [-0.6, -1.0], [2.4, -5.6], [8.0, -6.8], [-1.4, 3.0]].forEach(function (p, i) { var t = treeMesh(0.8 + (i % 3) * 0.15); t.position.set(p[0], 0, p[1]); scene.add(t); });
    var car = carMesh(P.car); car.scale.setScalar(1.5); scene.add(car); drive(car, good, 0);
    var rack = rbox(0.66, 0.05, 0.7, 0.02, M(P.ink)); rack.position.set(0, 0.76, -0.1); car.add(rack);
    var defs = [['게임', P.terra, null, 'gamepad-2'], ['슬라이드', P.teal, null, 'presentation'], ['영상', P.terra2, null, 'clapperboard'], ['수업 도구', P.paper, '#2b2019', 'timer'], ['데이터', P.teal2, null, 'chart-column'], ['법 확인', P.sand, '#2b2019', 'scale']];
    var tools = defs.map(function (d, i) {
      var c = card(1.25, 0.9, d[1], d[0], d[2], d[3]); scene.add(c);
      var a = (i - 2.5) * 0.42;
      c.userData = { from: V(4.0 + Math.sin(a) * 3.4, 2.6 + Math.cos(a * 1.4) * 0.5, 1.4 - Math.abs(a) * 0.6), seat: V((i % 3 - 1) * 0.22, 0.86 + Math.floor(i / 3) * 0.02, -0.28 + Math.floor(i / 3) * 0.3) };
      return c;
    });
    var L = [lbl('쓸 도구 + 사용법', 'say', V(4.0, 3.9, 1.2)), lbl('✓ 정문', 'ck', mu, [0, 1.7, 1.6]), lbl('헤매는 길', 'st', V(0.9, 0.3, -2.4))];
    var S = { scene: scene, camera: cam, labels: L, st: 0, f: 0, u: 0,
      setStep: function (n, snap) { S.st = n; if (snap) { S.f = n >= 1 ? 1 : 0; S.u = n >= 2 ? 1 : 0; } },
      update: function (dt, t, snap) {
        S.f += ((S.st >= 1 ? 1 : 0) - S.f) * (snap ? 1 : damp(2.2, dt));
        if (S.st >= 2) { if (!snap) S.u = Math.min(1, S.u + dt / 3.4); } else S.u = 0;
        var e = ease(S.u);
        drive(car, good, e * 0.97); reveal(lit, e);
        car.updateMatrixWorld(true);
        tools.forEach(function (c, i) {
          var d = c.userData, k = Math.max(0, Math.min(1, S.f * 1.25 - i * 0.05)), q = ease(k);
          var seatW = car.localToWorld(d.seat.clone());
          c.position.lerpVectors(d.from, seatW, q); c.position.y += Math.sin(Math.PI * q) * 0.8 + (snap || q > 0.99 ? 0 : Math.sin(t * 1.2 + i) * 0.06 * (1 - q));
          c.scale.setScalar(1 - q * 0.78);
          if (q > 0.99) { c.quaternion.copy(car.quaternion); c.rotateY(Math.PI); c.rotateX(-0.25); } else { c.rotation.set(-0.15, 0.25 - i * 0.04, 0); }
        });
        L[0].el.style.opacity = S.f < 0.5 ? 1 : 0;
        var arrived = S.u >= 1;
        mu.userData.gate.emissiveIntensity = arrived ? 0.6 : 0; mu.userData.door.emissiveIntensity = arrived ? 0.9 : 0;
        L[1].el.style.opacity = arrived ? 1 : 0;
        L[2].el.style.opacity = S.st >= 2 ? 0.0 : 0.85;
      } };
    cam.position.set(-1.5, 11.5, 11.5); cam.lookAt(2.2, 0, -2.4);
    return S;
  };

  /* 어두운 구간 공통 바닥 */
  function darkFloor(scene, w, d, y) { var f = rbox(w, d, 0.3, 0.2, M(0x2a2019, { roughness: 0.95 })); f.rotation.x = -Math.PI / 2; f.position.y = (y || 0) - 0.15; f.receiveShadow = true; scene.add(f); return f; }

  /* 평소 AI 쓰기 vs 부정행위 · 가운데 AI는 그대로, 입구와 출구만 바뀌어요 (recap=true면 마무리 그림) */
  function buildSwap(slideEl, recap) {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
    rig(scene, true, 10, 0, 0);
    var Y0 = 1.55, Y1 = -1.15, XI = -4.4, XO = 4.4;
    var sh = catcher(22, 12, 0.22); sh.position.y = -3.2; scene.add(sh);
    function rowBase(y, op) { var b = rbox(12.4, 2.2, 0.12, 0.06, M(P.dk2, { roughness: 0.9, transparent: true, opacity: op })); b.rotation.x = -Math.PI / 2; b.position.set(0, y - 0.72, -0.2); b.receiveShadow = true; scene.add(b); return b; }
    var baseA = rowBase(Y0, 1), baseB = rowBase(Y1, 1);
    // 위 줄: 평소
    var kbA = keyboardMesh(); kbA.position.set(XI, Y0 - 0.6, 0.2); kbA.rotation.x = 0.35; kbA.scale.setScalar(0.9); scene.add(kbA);
    var aiA = cloudMesh(true); aiA.position.set(0, Y0 + 0.05, 0); aiA.scale.setScalar(0.62); scene.add(aiA);
    var monA = monitorMesh(); monA.position.set(XO, Y0 - 0.66, 0); monA.scale.setScalar(0.62); monA.rotation.y = -0.25; scene.add(monA);
    // 아래 줄: 부정행위 (처음엔 위와 같은 키보드·화면, 바뀌면 안경·이어폰)
    var kbB = keyboardMesh(); kbB.position.set(XI, Y1 - 0.6, 0.2); kbB.rotation.x = 0.35; kbB.scale.setScalar(0.9); scene.add(kbB);
    var monB = monitorMesh(); monB.position.set(XO, Y1 - 0.66, 0); monB.scale.setScalar(0.62); monB.rotation.y = -0.25; scene.add(monB);
    var aiB = cloudMesh(true); aiB.position.set(0, Y1 + 0.05, 0); aiB.scale.setScalar(0.62); scene.add(aiB);
    var gl = glassesMesh({ cam: true, disp: true }); gl.position.set(XI, Y1, 0.3); gl.rotation.set(0.15, 0.55, 0); scene.add(gl);
    var bud = earbudMesh(0.55); bud.position.set(XO, Y1, 0.3); bud.rotation.y = -0.5; scene.add(bud);
    var ph = phoneMesh(); ph.scale.setScalar(0.5); ph.position.set(0, Y1 - 0.25, 1.5); ph.rotation.set(-0.15, 0, 0); scene.add(ph);
    // 길 (신호가 지나가요)
    var cA1 = new THREE.CatmullRomCurve3([V(XI + 0.9, Y0, 0.3), V(-2.2, Y0 + 0.35, 0.4), V(-0.9, Y0 + 0.05, 0.4)]);
    var cA2 = new THREE.CatmullRomCurve3([V(0.9, Y0 + 0.05, 0.4), V(2.2, Y0 + 0.35, 0.4), V(XO - 0.8, Y0 + 0.05, 0.3)]);
    var cB1 = new THREE.CatmullRomCurve3([V(XI + 0.9, Y1 + 0.05, 0.4), V(-2.0, Y1 - 0.3, 1.2), V(-0.25, Y1 - 0.15, 1.5)]);
    var cB2 = new THREE.CatmullRomCurve3([V(-0.15, Y1 + 0.2, 1.5), V(-0.6, Y1 + 0.6, 1.0), V(-0.35, Y1 + 0.2, 0.5)]);
    var cB3 = new THREE.CatmullRomCurve3([V(0.35, Y1 + 0.2, 0.5), V(0.6, Y1 + 0.6, 1.0), V(0.15, Y1 + 0.2, 1.5)]);
    var cB4 = new THREE.CatmullRomCurve3([V(0.25, Y1 - 0.15, 1.5), V(2.0, Y1 - 0.3, 1.2), V(XO - 0.6, Y1 + 0.05, 0.4)]);
    var cBn = new THREE.CatmullRomCurve3([V(XI + 0.9, Y1, 0.3), V(-2.2, Y1 + 0.35, 0.4), V(-0.9, Y1 + 0.05, 0.4)]);
    var cBn2 = new THREE.CatmullRomCurve3([V(0.9, Y1 + 0.05, 0.4), V(2.2, Y1 + 0.35, 0.4), V(XO - 0.8, Y1 + 0.05, 0.3)]);
    var tA = [pathTube(cA1, 0.025, P.amber, 0.35), pathTube(cA2, 0.025, P.amber, 0.35)];
    var tBn = [pathTube(cBn, 0.025, P.amber, 0), pathTube(cBn2, 0.025, P.amber, 0)];
    var tB = [cB1, cB2, cB3, cB4].map(function (c) { return pathTube(c, 0.025, P.cool, 0); });
    tA.concat(tBn, tB).forEach(function (m) { scene.add(m); });
    var pA = pulseMesh(0.07, P.amber), pB = pulseMesh(0.07, P.cool); scene.add(pA); scene.add(pB);
    var hlA = blob(1.6, 0, 'rgba(245,158,11,0.28)'), hlB = blob(1.6, 0, 'rgba(245,158,11,0.28)'); hlA.position.copy(aiA.position); hlB.position.copy(aiB.position); hlA.rotation.x = hlB.rotation.x = 0; scene.add(hlA); scene.add(hlB);
    var L = [
      lbl('평소', 'row', V(-7.1, Y0, 0)), lbl('부정행위', 'row bad', V(-7.1, Y1, 0)),
      lbl('손으로 쳐서 넣기', 'tag', kbA, [0, -0.55, 0.6]), lbl('같은 AI', 'tag ai', aiA, [0, 0.95, 0]), lbl('화면에서 눈으로 읽기', 'tag', monA, [0, -0.15, 0.6]),
      lbl('안경 카메라가 대신 봐서 넣기', 'tag cool', gl, [0, -0.7, 0.4]), lbl('같은 AI', 'tag ai', aiB, [0, 0.95, 0]), lbl('이어폰이 귀에 말해 주기 · 렌즈에 뜨기', 'tag cool', bud, [0, -0.75, 0.3]),
      lbl('주머니 속 휴대폰 · 중계만', 'tag', ph, [0, -0.72, 0])
    ];
    var verbs = recap ? [lbl('① 찍고', 'verb', gl, [0, 0.8, 0.3]), lbl('② 보내고', 'verb', V(-1.7, Y1 - 0.7, 1.4)), lbl('③ 풀고', 'verb', aiB, [0, 1.45, 0]), lbl('④ 돌려받고', 'verb', V(1.7, Y1 - 0.7, 1.4)), lbl('⑤ 듣고 적기', 'verb', bud, [0, 0.8, 0.3])] : [];
    L = L.concat(verbs);
    var S = { scene: scene, camera: cam, labels: L, st: recap ? 2 : 0, sw: recap ? 1 : 0, rowB: recap ? 1 : 0, pu: 0, pu2: 0, vs: 0,
      setStep: function (n, snap) {
        S.st = recap ? 2 : (n >= 2 ? 2 : n); S.vs = recap ? n : 0;
        if (snap) { S.sw = S.st >= 2 ? 1 : 0; S.rowB = S.st >= 1 ? 1 : 0; }
      },
      update: function (dt, t, snap) {
        var k = snap ? 1 : damp(2.2, dt);
        S.rowB += ((S.st >= 1 ? 1 : 0) - S.rowB) * k;
        S.sw += ((S.st >= 2 ? 1 : 0) - S.sw) * (snap ? 1 : damp(1.6, dt));
        var r = S.rowB, w = ease(S.sw);
        baseB.material.opacity = r;
        // 키보드·화면은 아래로 빠지고 작아지고, 안경·이어폰이 올라와요
        var out = Math.min(1, w * 1.6), inn = Math.max(0, w * 1.6 - 0.6);
        kbB.visible = monB.visible = out < 0.99 && r > 0.02;
        kbB.scale.setScalar(0.9 * r * (1 - out)); monB.scale.setScalar(0.62 * r * (1 - out));
        kbB.position.y = Y1 - 0.6 - out * 0.8; monB.position.y = Y1 - 0.66 - out * 0.8;
        aiB.visible = r > 0.02; aiB.scale.setScalar(0.62 * Math.max(0.001, r));
        gl.visible = bud.visible = ph.visible = inn > 0.01;
        var gi = Math.max(0.001, inn);
        gl.scale.setScalar(0.95 * gi); bud.scale.setScalar(gi); ph.scale.setScalar(0.5 * gi);
        gl.position.y = Y1 - 0.6 + inn * 0.6 + (snap ? 0 : Math.sin(t * 1.2) * 0.04 * inn);
        bud.position.y = Y1 - 0.6 + inn * 0.6 + (snap ? 0 : Math.sin(t * 1.2 + 1) * 0.04 * inn);
        bud.rotation.y = snap ? -0.5 : -0.5 + Math.sin(t * 0.6) * 0.2;
        gl.rotation.y = snap ? 0.55 : 0.55 + Math.sin(t * 0.5) * 0.15;
        tBn[0].material.opacity = tBn[1].material.opacity = 0.35 * r * (1 - out);
        tB.forEach(function (m) { m.material.opacity = 0.55 * inn; });
        // 신호
        S.pu = snap ? 0.55 : (S.pu + dt * 0.28) % 1;
        var u = S.pu, pa = u < 0.5 ? cA1.getPointAt(u * 2) : cA2.getPointAt(u * 2 - 1);
        pA.position.copy(pa); face(pA.userData.halo, cam);
        var curves = inn > 0.5 ? [cB1, cB2, cB3, cB4] : [cBn, cBn2];
        var seg = Math.min(curves.length - 1, Math.floor(u * curves.length)), lu = u * curves.length - seg;
        if (recap && S.vs >= 1 && S.vs <= 5) { var mp = [[0, 0.12], [0, 0.8], [1, 0.95], [2, 0.6], [3, 0.88]][S.vs - 1]; seg = mp[0]; lu = mp[1]; }
        pB.position.copy(curves[Math.min(seg, curves.length - 1)].getPointAt(Math.max(0, Math.min(1, lu)))); face(pB.userData.halo, cam);
        pB.visible = r > 0.5;
        pB.children[0].material.color.setHex(inn > 0.5 ? P.cool : P.amber);
        // AI는 그대로, 둘 다 밝게
        [aiA, aiB].forEach(function (a, i) { a.userData.star.rotation.z = snap ? 0.3 : t * 0.8 + i; a.position.y = (i ? Y1 : Y0) + 0.05 + (snap ? 0 : Math.sin(t * 1.1) * 0.04); });
        hlA.material.opacity = 0.9; hlB.material.opacity = 0.9 * r; face(hlA, cam); face(hlB, cam);
        var wv = bud.userData.waves; wv.forEach(function (m, i) { m.material.opacity = inn * (snap ? 0.7 - i * 0.2 : Math.max(0, Math.sin(t * 3 - i * 0.9)) * 0.8); });
        if (gl.userData.disp) gl.userData.disp.material.opacity = inn * 0.95;
        if (gl.userData.ring) gl.userData.ring.material.emissiveIntensity = inn * (snap ? 1 : 0.6 + Math.sin(t * 5) * 0.4);
        if (!snap && S.st === 0) kbA.userData.fingers.forEach(function (f, i) { f.position.y = -0.06 + Math.max(0, Math.sin(t * 9 + i * 1.7)) * 0.04; });
        L[1].el.style.opacity = r; L[6].el.style.opacity = r;
        L[5].el.style.opacity = inn; L[7].el.style.opacity = inn; L[8].el.style.opacity = inn;
        verbs.forEach(function (v, i) { v.el.className = 'lbl verb' + (S.vs === i + 1 ? ' on' : '') + (S.vs && S.vs <= 5 && S.vs !== i + 1 ? ' dim' : ''); });
        if (recap) { [L[0], L[2], L[4]].forEach(function (l) { l.el.style.opacity = 0.55; }); [L[3], L[5], L[6], L[7], L[8]].forEach(function (l) { l.el.style.opacity = 0; }); }
      } };
    if (recap) { cam.position.set(0, 0.6, 18.5); cam.lookAt(0, 0.25, 0); } else { cam.position.set(0, 1.2, 17.5); cam.lookAt(0, 0.1, 0); }
    S.setStep(0, true);
    return S;
  }
  SCENES.swap = function (s) { return buildSwap(s, false); };
  SCENES.recap = function (s) { return buildSwap(s, true); };

  /* 문제 하나 따라가기: 학생 · 책상 · 시험지 · 안경 · 주머니 휴대폰 · 멀리 있는 AI */
  function studentMesh() {
    var g = new THREE.Group();
    var blazer = M(0x8f4a2c, { roughness: 0.75 }), pants = M(0x3b3029, { roughness: 0.8 }), skin = M(P.skin, { roughness: 0.7 });
    var wood = M(P.wood, { roughness: 0.6 }), metal = M(0x5a4a3d, { roughness: 0.5 });
    // 의자
    var seat = rbox(0.5, 0.48, 0.06, 0.03, wood); seat.rotation.x = -Math.PI / 2; seat.position.set(0, 0.46, -0.06); g.add(seat);
    var back = rbox(0.48, 0.36, 0.05, 0.03, wood); back.position.set(0, 0.8, -0.3); g.add(back);
    [[-0.21, -0.27], [0.21, -0.27], [-0.21, 0.15], [0.21, 0.15]].forEach(function (p) { var l = cyl(0.018, 0.018, 0.46, metal, 8); l.position.set(p[0], 0.23, p[1]); g.add(l); });
    // 몸
    var hip = rbox(0.42, 0.46, 0.16, 0.07, pants); hip.rotation.x = -Math.PI / 2; hip.position.set(0, 0.56, 0.08); g.add(hip);
    [-0.11, 0.11].forEach(function (x) { var sn = rbox(0.13, 0.46, 0.14, 0.05, pants); sn.position.set(x, 0.3, 0.32); g.add(sn); var sh2 = rbox(0.14, 0.08, 0.24, 0.04, M(0x2b2019)); sh2.position.set(x, 0.05, 0.38); g.add(sh2); });
    var torso = rbox(0.46, 0.56, 0.27, 0.12, blazer); torso.position.set(0, 0.9, -0.03); torso.rotation.x = 0.1; g.add(torso);
    var shirt = rbox(0.1, 0.07, 0.03, 0.015, M(0x2c3657)); shirt.position.set(0, 1.15, 0.115); shirt.rotation.x = 0.1; g.add(shirt);
    var pocket = rbox(0.13, 0.11, 0.025, 0.015, M(0x7a3d23, { roughness: 0.8 })); pocket.position.set(0.12, 0.98, 0.115); pocket.rotation.x = 0.1; g.add(pocket);
    var phone = new THREE.Group(); phone.position.set(0.12, 1.06, 0.11); phone.rotation.x = 0.1; g.add(phone);
    var pb = rbox(0.085, 0.15, 0.016, 0.012, M(P.ink, { roughness: 0.35 })); phone.add(pb);
    var pscr = noSh(new THREE.Mesh(new THREE.PlaneGeometry(0.07, 0.13), E(P.cool, 0.35))); pscr.position.z = 0.009; phone.add(pscr);
    var neck = cyl(0.055, 0.06, 0.1, skin, 16); neck.position.set(0, 1.21, 0.0); g.add(neck);
    var head = new THREE.Group(); head.position.set(0, 1.37, 0.0); g.add(head);
    head.add(sph(0.16, skin));
    var hair = new THREE.Mesh(new THREE.SphereGeometry(0.17, 32, 24, 0, Math.PI * 2, 0, Math.PI * 0.56), M(P.hair, { roughness: 0.85 })); hair.rotation.x = -0.5; hair.position.set(0, 0.01, -0.01); head.add(hair);
    [-1, 1].forEach(function (s) { var ear = sph(0.036, skin, s * 0.158, -0.02, 0); ear.scale.set(0.6, 1, 0.9); head.add(ear); head.add(sph(0.016, M(0x2b2019), s * 0.056, 0.0, 0.148)); });
    var gls = glassesMesh({ cam: true, disp: true }); gls.scale.setScalar(0.135); gls.position.set(0, 0.005, 0.165); head.add(gls);
    var bud = sph(0.022, M(P.cream, { roughness: 0.4, emissive: P.cool, emissiveIntensity: 0 }), 0.168, -0.025, 0.004); head.add(bud);
    // 팔
    [-1, 1].forEach(function (s) {
      var ua = rbox(0.11, 0.32, 0.12, 0.05, blazer); ua.position.set(s * 0.27, 0.93, 0.06); ua.rotation.x = -0.55; g.add(ua);
      var fa = rbox(0.1, 0.1, 0.36, 0.045, blazer); fa.position.set(s * 0.21, 0.83, 0.3); fa.rotation.y = -s * 0.25; g.add(fa);
      g.add(sph(0.05, skin, s * 0.15, 0.83, 0.49));
    });
    var pen = pencilMesh(); pen.scale.setScalar(0.22); pen.position.set(0.12, 0.88, 0.52); pen.rotation.set(0.5, 0, 0.5); g.add(pen);
    // 책상 + 시험지
    var top = rbox(1.1, 0.64, 0.05, 0.02, wood); top.rotation.x = -Math.PI / 2; top.position.set(0, 0.77, 0.46); g.add(top);
    [[-0.5, 0.2], [0.5, 0.2], [-0.5, 0.72], [0.5, 0.72]].forEach(function (p) { var l = cyl(0.02, 0.02, 0.76, metal, 8); l.position.set(p[0], 0.38, p[1]); g.add(l); });
    var paperT = tex(300, 420, function (c, w, h) {
      c.fillStyle = '#fffcf6'; c.fillRect(0, 0, w, h); c.fillStyle = '#2b2019'; c.font = '800 30px ' + FONT; c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText('시험지', 24, 18);
      for (var i = 0; i < 5; i++) { var y = 74 + i * 66; c.fillStyle = i === 2 ? 'rgba(245,158,11,.45)' : 'rgba(0,0,0,0)'; c.fillRect(12, y - 8, w - 24, 58); c.fillStyle = '#2b2019'; c.font = '800 24px ' + FONT; c.fillText((i + 1) + '.', 22, y); c.fillStyle = '#b3a08a'; c.fillRect(60, y + 6, 200 - i * 12, 9); c.fillRect(60, y + 26, 150, 9); }
    });
    var paperHl = tex(300, 420, function (c, w, h) { c.strokeStyle = '#f2a65a'; c.lineWidth = 8; rr2d(c, 10, 74 + 2 * 66 - 10, w - 20, 62, 12); c.stroke(); });
    var paper = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 0.42), M(0xffffff, { map: paperT, roughness: 0.9 })); paper.rotation.x = -Math.PI / 2; paper.position.set(-0.04, 0.799, 0.5); paper.receiveShadow = true; g.add(paper);
    var hl = plane(0.3, 0.42, paperHl, { opacity: 0 }); hl.rotation.x = -Math.PI / 2; hl.position.set(-0.04, 0.801, 0.5); g.add(hl);
    g.userData = { phone: phone, head: head, glasses: gls, bud: bud, pen: pen, paperHl: hl, paper: paper };
    return shadows(g);
  }
  SCENES.story = function (slideEl) {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.03, 120);
    scene.fog = new THREE.Fog(0x0d0a14, 18, 40);
    var key = rig(scene, true, 3, 0, 0.2);
    key.position.set(3, 6, 4);
    var floor = cyl(2.2, 2.3, 0.16, M(P.dk2, { roughness: 0.9 }), 64); floor.position.y = -0.08; floor.receiveShadow = true; scene.add(floor);
    var rimRing = noSh(new THREE.Mesh(new THREE.TorusGeometry(2.25, 0.012, 6, 96), Bm(P.amber, { transparent: true, opacity: 0.35 }))); rimRing.rotation.x = Math.PI / 2; rimRing.position.y = 0.005; scene.add(rimRing);
    var st = studentMesh(); scene.add(st);
    var U = st.userData;
    var cloud = cloudMesh(true); cloud.position.set(3.4, 1.3, -2.6); cloud.scale.setScalar(0.8); scene.add(cloud);
    var cloudGlow = blob(2.6, 0, 'rgba(245,158,11,0.3)'); cloudGlow.rotation.x = 0; cloudGlow.position.copy(cloud.position); scene.add(cloudGlow);
    // 거리 표시: 멀리 점선 고리
    var W = V(0, 0, 0);
    function wp(o) { st.updateMatrixWorld(true); return o.getWorldPosition(V(0, 0, 0)); }
    var camPt = wp(U.glasses.userData.cam), phPt = wp(U.phone), earPt = wp(U.bud), clPt = cloud.position.clone();
    phPt.z += 0.02;
    var c1 = new THREE.CatmullRomCurve3([camPt, V(camPt.x + 0.07, (camPt.y + phPt.y) / 2, camPt.z + 0.04), phPt]);
    var c2 = new THREE.CatmullRomCurve3([phPt, V(1.1, 1.55, -0.2), V(2.3, 1.75, -1.3), V(clPt.x - 0.55, clPt.y - 0.05, clPt.z + 0.45)]);
    var c3 = new THREE.CatmullRomCurve3([V(clPt.x - 0.15, clPt.y - 0.5, clPt.z + 0.45), V(2.6, 0.9, -1.0), V(1.4, 0.95, -0.05), phPt]);
    var c4 = new THREE.CatmullRomCurve3([phPt, V(phPt.x + 0.1, (phPt.y + earPt.y) / 2, phPt.z + 0.02), earPt]);
    var curves = [c1, c2, c3, c4];
    var tubes = curves.map(function (c, i) { var m = pathTube(c, i === 0 || i === 3 ? 0.004 : 0.018, P.cool, 0); scene.add(m); return m; });
    var pulse = pulseMesh(0.028, P.cool); scene.add(pulse);
    var photo = plane(0.18, 0.155, photoTex()); scene.add(photo);
    var bubble = plane(0.2, 0.156, bubbleTex()); scene.add(bubble);
    var flash = blob(0.25, 0, 'rgba(255,240,210,0.9)'); flash.rotation.x = 0; scene.add(flash);
    var phGlow = blob(0.2, 0, 'rgba(34,211,238,0.8)'); phGlow.rotation.x = 0; phGlow.position.copy(phPt); scene.add(phGlow);
    var thinking = [0, 1, 2].map(function (i) { var d = noSh(sph(0.12, Bm(P.amber, { transparent: true, opacity: 0 }))); d.position.set(clPt.x - 0.26 + i * 0.26, clPt.y - 0.85, clPt.z + 0.7); d.scale.setScalar(0.55); scene.add(d); return d; });
    var L = [lbl('안경 카메라', 'tag cool', U.glasses.userData.cam, [0.16, 0.05, 0]), lbl('주머니 속 휴대폰', 'tag cool', U.phone, [0.2, -0.05, 0]),
      lbl('멀리 있는 AI', 'tag ai', cloud, [0, 1.05, 0]), lbl('귀 속 이어폰', 'tag cool', U.bud, [0.17, -0.04, 0])];
    var clockEl = slideEl.querySelector('[data-clock]');
    var T = [0, 0, 1, 2, 5, 6, 7, 7];
    // 카메라 자리 [위치, 바라보는 곳]
    var Wd = [V(1.8, 1.55, 4.5), V(1.55, 0.98, -0.9)], N1 = [V(1.25, 1.8, 2.15), V(0.05, 0.92, 0.3)], N2 = [V(1.05, 1.6, 2.0), V(0.12, 1.12, 0.05)];
    var CAM = [Wd, N1, N2, Wd, [V(2.2, 1.45, 2.6), V(3.6, 1.15, -2.6)], Wd, N2, [V(2.1, 1.9, 3.8), V(0.7, 1.0, -0.2)]];
    var S = { scene: scene, camera: cam, labels: L, st: 0, p: 0, clock: 0, cp: CAM[0][0].clone(), cl: CAM[0][1].clone(),
      setStep: function (n, snap) {
        if (n !== S.st || snap) S.p = snap ? 0.62 : 0;
        S.st = n;
        if (snap) { S.cp.copy(CAM[n][0]); S.cl.copy(CAM[n][1]); S.clock = T[n]; }
      },
      update: function (dt, t, snap) {
        var n = S.st, k = snap ? 1 : damp(1.5, dt);
        if (!snap) S.p = Math.min(1, S.p + dt / 2.6);
        S.cp.lerp(CAM[n][0], k); S.cl.lerp(CAM[n][1], k);
        cam.position.copy(S.cp); cam.lookAt(S.cl);
        S.clock += (T[n] - S.clock) * (snap ? 1 : damp(1.2, dt));
        if (clockEl) clockEl.textContent = (Math.round(S.clock * 10) / 10).toFixed(1);
        var travel = { 2: 0, 3: 1, 5: 2, 6: 3 }[n];
        tubes.forEach(function (m, i) { var tgt = travel === i ? 0.75 : (n >= 1 && n <= 6 && i <= (travel === undefined ? (n >= 4 ? 1 : -1) : travel) ? 0.18 : 0); if (n === 0) tgt = 0.12; m.material.opacity += (tgt - m.material.opacity) * (snap ? 1 : damp(4, dt)); });
        var pp = ease(S.p);
        photo.visible = n === 2 || n === 3; bubble.visible = n === 5 || n === 6; pulse.visible = travel !== undefined;
        if (travel !== undefined) {
          var pos = curves[travel].getPointAt(Math.min(1, pp));
          pulse.position.copy(pos); face(pulse.userData.halo, cam);
          var far = travel === 1 || travel === 2;
          var sc = far ? 1 + Math.sin(Math.PI * Math.min(1, pp)) * 1.6 + (travel === 1 ? pp * 1.4 : (1 - pp) * 1.4) : 1;
          var item = photo.visible ? photo : bubble;
          item.position.copy(pos).add(V(0, far ? 0.12 * sc : 0.06, 0)); item.scale.setScalar(sc); face(item, cam);
          pulse.scale.setScalar(far ? sc : 1);
          if (n === 6) { bubble.position.copy(earPt).add(V(0.17, 0.08, 0.02)); bubble.scale.setScalar(0.9); face(bubble, cam); }
        }
        // 1: 시험지 3번 / 2: 카메라 번쩍 / 3: 휴대폰 / 4: AI 생각 중 / 6: 이어폰·렌즈 / 7: 받아 적기
        U.paperHl.material.opacity += ((n >= 1 && n <= 3 ? 1 : 0) - U.paperHl.material.opacity) * (snap ? 1 : damp(4, dt));
        var camOn = n === 2;
        U.glasses.userData.ring.material.emissiveIntensity = camOn ? 1.2 : 0.15;
        flash.position.copy(camPt).add(V(0.01, 0, 0.02)); face(flash, cam);
        flash.material.opacity = camOn ? (snap ? 0.7 : Math.max(0, 1 - S.p * 2.5)) : 0;
        phGlow.material.opacity = (n === 2 && pp > 0.8) || n === 3 || n === 5 || n === 6 ? 0.9 : 0; face(phGlow, cam);
        cloud.userData.star.rotation.z = snap ? 0.4 : t * (n === 4 ? 3.5 : 0.6);
        cloud.userData.star.material.emissiveIntensity = n === 4 ? 1.3 : 0.6;
        cloudGlow.material.opacity = n === 4 ? 1 : n >= 3 && n <= 5 ? 0.6 : 0.35; face(cloudGlow, cam);
        thinking.forEach(function (d, i) { d.material.opacity = n === 4 ? (snap ? 0.9 : 0.25 + Math.max(0, Math.sin(t * 4 - i * 0.8)) * 0.75) : 0; });
        if (n === 4) { bubble.visible = pp > 0.7; if (bubble.visible) { bubble.position.set(clPt.x - 0.15, clPt.y - 0.85, clPt.z + 0.9); bubble.scale.setScalar(2.6); face(bubble, cam); thinking.forEach(function (d) { d.material.opacity = 0; }); } }
        U.bud.material.emissiveIntensity = n === 6 ? (snap ? 1 : 0.6 + Math.sin(t * 6) * 0.4) : 0;
        U.glasses.userData.disp.material.opacity = n === 6 ? 0.95 : 0;
        U.pen.position.x = 0.12 + (n === 7 && !snap ? Math.sin(t * 5) * 0.015 : 0);
        var showL = [[1, 1, 1, 1], [0, 0, 0, 0], [1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 0], [0, 1, 1, 0], [0, 1, 0, 1], [0, 0, 0, 0]][n];
        L.forEach(function (l, i) { l.el.style.opacity = showL[i]; });
      } };
    S.setStep(0, true);
    return S;
  };

  /* 들어가는 기기 여섯: 한 줄로 놓고 아래에 이름표 카드 */
  SCENES.kit = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
    rig(scene, true, 12, 0, 0);
    var X = [-6.25, -3.75, -1.25, 1.25, 3.75, 6.25];
    var objs = [
      glassesMesh({ cam: true }), glassesMesh({ disp: true, frame: 0x3a2d23 }), earbudMesh(0.8), phoneMesh(), watchMesh(), new THREE.Group()
    ];
    var lap = laptopMesh(); lap.scale.setScalar(0.62); lap.position.set(-0.35, -0.55, 0.1); objs[5].add(lap);
    var cl = cloudMesh(true); cl.scale.setScalar(0.5); cl.position.set(0.45, 0.75, -0.4); objs[5].add(cl);
    objs[1].userData.disp.material.opacity = 0.95;
    var sc = [0.95, 0.95, 1.05, 0.7, 0.85, 1.05], ry = [0.55, 0.55, -0.6, -0.3, -0.35, -0.35];
    objs.forEach(function (o, i) {
      var base = cyl(0.95, 1.05, 0.18, M(P.dk2, { roughness: 0.6 }), 48); base.position.set(X[i], -0.95, 0); scene.add(shadows(base));
      var ring = noSh(new THREE.Mesh(new THREE.TorusGeometry(1.0, 0.012, 6, 64), Bm(P.amber, { transparent: true, opacity: 0.4 }))); ring.rotation.x = Math.PI / 2; ring.position.set(X[i], -0.85, 0); scene.add(ring);
      o.position.set(X[i], 0.0, 0); o.scale.setScalar(sc[i]); o.rotation.y = ry[i]; o.userData.ry = ry[i]; scene.add(o);
    });
    if (objs[2].userData.waves) objs[2].userData.waves.forEach(function (w, i) { w.material.opacity = 0.6 - i * 0.18; });
    var sh = catcher(20, 6, 0.3); sh.position.y = -0.85; scene.add(sh);
    var D = [['카메라 안경', '안경테에 작은 카메라.<br>문제를 찍어요'], ['화면 안경', '렌즈 안쪽 작은 화면.<br>답이 떠요'], ['초소형 이어폰', '귀 속에 쏙.<br>답을 소리로 읽어 줘요'],
      ['휴대폰', '주머니 속 중계소.<br>사진을 보내고 답을 받아요'], ['스마트워치', '손목 위 작은 화면.<br>글자를 보여 줘요'], ['노트북·클라우드 AI', '멀리서 문제를 읽고<br>답을 만들어요']];
    var L = D.map(function (d, i) { return lbl('<b>' + d[0] + '</b><span>' + d[1] + '</span>', 'kc', V(X[i], -2.3, 0.6)); });
    cam.position.set(0, 1.6, 16.2); cam.lookAt(0, -0.75, 0);
    var S = { scene: scene, camera: cam, labels: L, st: 0,
      setStep: function (n) { S.st = n; },
      update: function (dt, t, snap) {
        objs.forEach(function (o, i) {
          o.rotation.y = o.userData.ry + (snap ? 0 : Math.sin(t * 0.6 + i) * 0.35);
          o.position.y = snap ? 0 : Math.sin(t * 1.1 + i * 0.7) * 0.06;
          var on = S.st === 0 || S.st === i + 1;
          L[i].el.className = 'lbl kc' + (S.st === i + 1 ? ' on' : '') + (on ? '' : ' dim');
        });
        if (objs[0].userData.ring) objs[0].userData.ring.material.emissiveIntensity = snap ? 0.9 : 0.5 + Math.sin(t * 4) * 0.4;
        if (!snap) objs[2].userData.waves.forEach(function (w, i) { w.material.opacity = Math.max(0, Math.sin(t * 3 - i * 0.9)) * 0.75; });
        objs[5].children[1].userData.star.rotation.z = snap ? 0.3 : t;
      } };
    return S;
  };

  /* 왜 잡기 어려울까: 거의 똑같은 안경 두 개, 그리고 확인 뒤 바꿔 끼기 */
  SCENES.look = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
    rig(scene, true, 8, 4.6, 0);
    var tray = rbox(7.4, 4.2, 0.14, 0.1, M(P.dk2, { roughness: 0.9 })); tray.rotation.x = -Math.PI / 2; tray.position.set(5.6, -0.07, 0); tray.receiveShadow = true; scene.add(tray);
    var slotA = noSh(new THREE.Mesh(new THREE.RingGeometry(1.45, 1.52, 64), Bm(P.amber, { transparent: true, opacity: 0.5, side: THREE.DoubleSide }))); slotA.rotation.x = -Math.PI / 2; slotA.position.set(4.3, 0.01, 0.5); scene.add(slotA);
    var A = glassesMesh({}), B = glassesMesh({ cam: true });
    var PA = V(4.3, 0.45, 0.5), PB = V(7.0, 0.45, -0.6);
    [A, B].forEach(function (g) { g.rotation.set(-0.1, -0.35, 0); g.scale.setScalar(0.8); scene.add(g); });
    var mag = noSh(new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.03, 8, 40), Bm(P.cool, { transparent: true, opacity: 0 }))); scene.add(mag);
    var L = [lbl('보통 안경', 'tag', A, [0, -0.85, 0.6]), lbl('카메라 안경', 'tag', B, [0, -0.85, 0.6]), lbl('작은 카메라', 'tag cool', B.userData.cam, [0.2, 0.55, 0]),
      lbl('확인할 때 ✓', 'tag ok', V(4.3, 1.7, 0.5)), lbl('시작한 뒤', 'tag bad', V(4.3, 1.7, 0.5))];
    var S = { scene: scene, camera: cam, labels: L, st: 0, w: 0,
      setStep: function (n, snap) { S.st = n; if (snap) S.w = n >= 2 ? 1 : 0; },
      update: function (dt, t, snap) {
        S.w += ((S.st >= 2 ? 1 : 0) - S.w) * (snap ? 1 : damp(1.4, dt));
        var w = ease(S.w), arc = Math.sin(Math.PI * w) * 1.2;
        A.position.lerpVectors(PA, PB, w); A.position.y += arc;
        B.position.lerpVectors(PB, PA, w); B.position.y += arc * 0.6; B.position.z += Math.sin(Math.PI * w) * 0.8;
        var bob = snap ? 0 : Math.sin(t * 1.2) * 0.03; A.position.y += bob; B.position.y += bob;
        var cw = B.userData.cam.getWorldPosition(V(0, 0, 0));
        var mOn = S.st === 1 ? 1 : 0;
        mag.position.copy(cw); face(mag, cam); mag.material.opacity += (mOn * 0.95 - mag.material.opacity) * (snap ? 1 : damp(5, dt));
        mag.scale.setScalar(1 + (snap ? 0 : Math.sin(t * 3) * 0.06));
        B.userData.ring.material.emissiveIntensity = S.st >= 1 ? 0.8 : 0.05;
        L[2].el.style.opacity = S.st === 1 ? 1 : 0;
        L[3].el.style.opacity = S.st === 2 && w < 0.5 ? 1 : S.st < 2 ? 0 : 0;
        L[4].el.style.opacity = S.st === 2 && w >= 0.5 ? 1 : 0;
        L[0].el.style.opacity = L[1].el.style.opacity = S.st === 2 && w > 0.1 && w < 0.9 ? 0 : 1;
        slotA.material.opacity = S.st === 2 ? 0.9 : 0;
      } };
    cam.position.set(3.0, 5.4, 9.0); cam.lookAt(3.6, 0.2, 0);
    return S;
  };

  /* 마무리: 무기 카드가 내비 핀 둘레를 돌아요 */
  SCENES.made = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.1, 100);
    rig(scene, true, 9, 5.2, 0);
    var root = new THREE.Group(); root.position.set(5.2, 0.2, 0); scene.add(root);
    var prof = []; for (var i = 0; i <= 24; i++) { var a = i / 24; var y = -1.3 + a * 2.5; var r = a < 0.55 ? Math.pow(a / 0.55, 0.9) * 0.62 : Math.sqrt(Math.max(0, 1 - Math.pow((a - 0.62) / 0.38, 2))) * 0.82; prof.push(new THREE.Vector2(Math.max(0.001, r), y)); }
    var pin = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), M(P.amber, { roughness: 0.4, emissive: P.amber, emissiveIntensity: 0.15 })); root.add(pin);
    var hole = sph(0.3, M(P.dk)); hole.position.set(0, 0.42, 0.62); hole.scale.z = 0.4; root.add(hole);
    var holeB = sph(0.3, M(P.dk)); holeB.position.set(0, 0.42, -0.62); holeB.scale.z = 0.4; root.add(holeB);
    shadows(root);
    var glow = blob(2.6, 0, 'rgba(245,158,11,0.3)'); glow.rotation.x = 0; root.add(glow);
    var dsk = catcher(10, 10, 0.25); dsk.position.y = -2.0; root.add(dsk);
    var names = [['게임', P.terra, null, 'gamepad-2'], ['슬라이드', P.teal, null, 'presentation'], ['영상', P.terra2, null, 'clapperboard'], ['수업 도구', 0xf6ecdf, '#2b2019', 'timer'], ['데이터', P.teal2, null, 'chart-column'], ['법 확인', P.sand, '#2b2019', 'scale'], ['기획', P.amber, '#1a1511', 'lightbulb']];
    var ring = new THREE.Group(); ring.rotation.x = 0.28; ring.rotation.z = -0.1; root.add(ring);
    var cards = names.map(function (n, k) { var c = card(1.7, 1.2, n[1], n[0], n[2], n[3]); c.userData.a = k / names.length * Math.PI * 2; c.userData.r0 = 9 + k; ring.add(c); return c; });
    cam.position.set(0, 0.8, 18); cam.lookAt(0.4, 0, 0);
    var S = { scene: scene, camera: cam, labels: [], spin: 0, arrive: 0,
      setStep: function (n, snap) { if (snap) S.arrive = 1; },
      update: function (dt, t, snap) {
        if (!snap) { S.spin += dt * 0.2; S.arrive += (1 - S.arrive) * damp(1.3, dt); } else S.arrive = 1;
        cards.forEach(function (c, k) {
          var r = 3.4 + (1 - S.arrive) * c.userData.r0, a = c.userData.a + S.spin + (1 - S.arrive) * 2;
          c.position.set(Math.cos(a) * r, Math.sin(t * 1.1 + k) * 0.12, Math.sin(a) * r);
          c.lookAt(cam.position.x - root.position.x, c.position.y, cam.position.z);
        });
        pin.rotation.y = hole.rotation.y = 0; root.children[0].rotation.y = 0;
        pin.position.y = holeB.position.y * 0 + (snap ? 0 : Math.sin(t * 1.2) * 0.08); hole.position.y = 0.42 + pin.position.y; holeB.position.y = 0.42 + pin.position.y;
        face(glow, cam);
      } };
    return S;
  };

  /* ---------- 입력 ---------- */
  var jump = '';
  document.addEventListener('keydown', function (e) {
    var k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ' || k === 'Enter' && !jump) { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') { e.preventDefault(); prev(); }
    else if (k === 'Home') go(0, 0);
    else if (k === 'End') go(slides.length - 1, 'end');
    else if (k === 'n' || k === 'N') notesEl.classList.toggle('on');
    else if (k === 'f' || k === 'F') toggleFS();
    else if (k === 'b' || k === 'B' || k === '.') document.getElementById('black').classList.toggle('on');
    else if (k === 't' || k === 'T') { var tm = slides[cur].querySelector('.timer'); if (tm && tm.toggle) tm.toggle(); }
    else if (/^[0-9]$/.test(k)) { jump += k; }
    else if (k === 'Enter' && jump) { go(+jump - 1, 0); jump = ''; }
    else if (k === 'Escape') { jump = ''; }
  });
  stage.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('.timer')) return; if (e.clientX < window.innerWidth * 0.2) prev(); else next(); });
  function toggleFS() {
    var d = document, el = d.documentElement;
    if (!d.fullscreenElement && !d.webkitFullscreenElement) { (el.requestFullscreen || el.webkitRequestFullscreen).call(el); }
    else { (d.exitFullscreen || d.webkitExitFullscreen).call(d); }
  }
  document.getElementById('bfs').onclick = toggleFS;
  document.getElementById('bnotes').onclick = function () { notesEl.classList.toggle('on'); };
  document.getElementById('bprev').onclick = prev;
  document.getElementById('bnext').onclick = next;
  window.addEventListener('resize', fit);

  /* ---------- 시작 ---------- */
  function start() {
    initGL();
    fit();
    var m = /#(\d+)(?:\.(\d+))?/.exec(location.hash);
    go(m ? +m[1] - 1 : 0, m && m[2] ? +m[2] : 0);
  }
  window.__deck = {
    go: function (i, st) { go(i, st); }, count: slides.length,
    steps: function (i) { return maxStep(slides[i]); },
    settle: function () { if (GL.active) { GL.active.setStep(step, true); GL.active.update(0, 2.0, true); renderOnce(); } },
    // 점검용: 3D 물건 하나를 따로 찍어요 (shoot.py --closeup)
    closeup: function (name, warm) {
      var K = { '카메라 안경': function () { return glassesMesh({ cam: true }); }, '화면 안경': function () { var g = glassesMesh({ disp: true }); g.userData.disp.material.opacity = 0.95; return g; },
        '초소형 이어폰': function () { var e = earbudMesh(1); e.userData.waves.forEach(function (w, i) { w.material.opacity = 0.7 - i * 0.2; }); return e; }, '휴대폰': function () { return phoneMesh(); },
        '스마트워치': watchMesh, '노트북': laptopMesh, '클라우드 AI': function () { return cloudMesh(true); }, '키보드와 손': keyboardMesh, '모니터 대화창': monitorMesh,
        '학생과 책상': studentMesh, '자동차': function () { return carMesh(P.car); }, '목적지 건물': museumMesh, '길 묻는 행인': passerMesh, '학교': schoolMesh, '나무': treeMesh,
        '기획 전구': function () { return stationObj(0); }, '대본': function () { return stationObj(1); }, '콘티': function () { return stationObj(2); }, '제작 톱니': function () { return stationObj(3); },
        '연필': pencilMesh, '배포 종이비행기': function () { return stationObj(5); }, '도구 카드': function () { return card(1.6, 1.1, P.terra, '게임', null, 'gamepad-2'); } };
      if (name === 'list') return Object.keys(K);
      var c = document.createElement('canvas'), r = new THREE.WebGLRenderer({ canvas: c, antialias: true, alpha: true, preserveDrawingBuffer: true });
      r.setSize(480, 400, false); r.setClearColor(0x000000, 0); r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
      var sc = new THREE.Scene(), o = K[name](); sc.add(o);
      var box = new THREE.Box3().setFromObject(o), ctr = box.getCenter(V(0, 0, 0)), sz = box.getSize(V(0, 0, 0)), R = Math.max(sz.x, sz.y, sz.z);
      rig(sc, !!warm, R * 2, ctr.x, ctr.z);
      var fl = catcher(R * 6, R * 6, 0.35); fl.position.set(ctr.x, box.min.y - 0.001, ctr.z); sc.add(fl);
      var cm = new THREE.PerspectiveCamera(30, 1.2, R * 0.01, R * 40);
      cm.position.set(ctr.x + R * 1.1, ctr.y + R * 0.75, ctr.z + R * 1.9); cm.lookAt(ctr);
      r.render(sc, cm);
      var url = c.toDataURL('image/png'); r.dispose(); return url;
    },
    state: function () { return { slide: cur, step: step, gl: GL.ok, reduced: REDUCED, active: GL.active ? GL.active.kind : null }; }
  };
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(start, start); else start();
})();
