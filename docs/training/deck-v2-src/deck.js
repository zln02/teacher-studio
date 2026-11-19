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
  var AGENDA = ['여는 말', '내비로 이해', '같은 부탁 다른 결과', '설치', '모둠 미션', '시험 부정행위', '마무리'];

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
      if (acc > 2) { if (acc / frames > 0.04 && GL.pr > 0.5) { GL.pr = GL.pr > 1 ? 1 : GL.pr > 0.75 ? 0.75 : 0.5; sizeGL(); } acc = 0; frames = 0; }
      GL.active.update(dt, now / 1000, false);
      GL.r.render(GL.active.scene, GL.active.camera);
      projectLabels(GL.active);
    }
    GL.raf = requestAnimationFrame(loop);
  }
  function stopLoop() { if (GL.raf) cancelAnimationFrame(GL.raf); GL.raf = 0; }
  function glLeave() { stopLoop(); GL.active = null; GL.sceneEl = null; }
  document.addEventListener('visibilitychange', function () { if (document.hidden) stopLoop(); else if (GL.active) startLoop(); });

  /* ---- 3D 도우미 ---- */
  function M(color, o) { return new THREE.MeshStandardMaterial(Object.assign({ color: color, flatShading: true, roughness: 0.78, metalness: 0.02 }, o || {})); }
  function lights(scene, warm) {
    scene.add(new THREE.HemisphereLight(warm ? 0xfff2e2 : 0xffe8d0, warm ? 0x8a6447 : 0x2a1d14, warm ? 0.62 : 0.75));
    var d = new THREE.DirectionalLight(0xfff8f0, warm ? 0.55 : 0.9); d.position.set(4, 9, 7); scene.add(d);
    var f = new THREE.DirectionalLight(warm ? 0xffd2a8 : 0xf2a65a, warm ? 0.2 : 0.45); f.position.set(-6, 2, 4); scene.add(f);
  }
  function rrShape(w, h, r) {
    var s = new THREE.Shape(), x = -w / 2, y = -h / 2;
    s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
    s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
    s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
    return s;
  }
  function texCard(text, bg, fg, w, h, sub) {
    var c = document.createElement('canvas'); c.width = 512; c.height = Math.round(512 * h / w);
    var g = c.getContext('2d');
    var r = 46;
    g.fillStyle = bg; g.beginPath();
    g.moveTo(r, 0); g.lineTo(c.width - r, 0); g.quadraticCurveTo(c.width, 0, c.width, r); g.lineTo(c.width, c.height - r); g.quadraticCurveTo(c.width, c.height, c.width - r, c.height);
    g.lineTo(r, c.height); g.quadraticCurveTo(0, c.height, 0, c.height - r); g.lineTo(0, r); g.quadraticCurveTo(0, 0, r, 0); g.fill();
    g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle';
    var fs = text.length > 5 ? 64 : 84;
    g.font = '800 ' + fs + 'px "Noto Sans KR", sans-serif';
    g.fillText(text, c.width / 2, c.height / 2 + (sub ? -22 : 4));
    if (sub) { g.globalAlpha = 0.75; g.font = '700 36px "Noto Sans KR", sans-serif'; g.fillText(sub, c.width / 2, c.height / 2 + 52); }
    var t = new THREE.CanvasTexture(c); t.minFilter = THREE.LinearFilter; t.generateMipmaps = false;
    return t;
  }
  // 둥근 카드: 몸통(돌출) + 앞면 글씨 판
  function card(w, h, color, text, fg, sub) {
    var g = new THREE.Group();
    var body = new THREE.Mesh(new THREE.ExtrudeGeometry(rrShape(w, h, Math.min(w, h) * 0.12), { depth: 0.08, bevelEnabled: false, curveSegments: 4 }), M(color));
    body.position.z = -0.08; g.add(body);
    if (text) {
      var face = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: texCard(text, '#' + new THREE.Color(color).getHexString(), fg || '#ffffff', w, h, sub), transparent: true }));
      face.position.z = 0.006; g.add(face); g.face = face;
    }
    g.body = body;
    return g;
  }
  function blob(r, opacity, color) {
    var c = document.createElement('canvas'); c.width = c.height = 128;
    var g = c.getContext('2d'), gr = g.createRadialGradient(64, 64, 4, 64, 64, 62);
    gr.addColorStop(0, 'rgba(60,35,20,' + opacity + ')'); gr.addColorStop(1, 'rgba(60,35,20,0)');
    if (color) { gr = g.createRadialGradient(64, 64, 4, 64, 64, 62); gr.addColorStop(0, color); gr.addColorStop(1, 'rgba(0,0,0,0)'); }
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    var m = new THREE.Mesh(new THREE.PlaneGeometry(r * 2, r * 2), new THREE.MeshBasicMaterial({ map: noMip(new THREE.CanvasTexture(c)), transparent: true, depthWrite: false }));
    m.rotation.x = -Math.PI / 2;
    return m;
  }
  function lbl(text, cls, objOrPos, off) {
    var e = document.createElement('div'); e.className = 'lbl ' + (cls || ''); e.innerHTML = text;
    var l = { el: e, off: off ? new THREE.Vector3(off[0], off[1], off[2]) : null };
    if (objOrPos && objOrPos.isObject3D) l.obj = objOrPos; else l.pos = objOrPos;
    return l;
  }
  function noMip(t) { t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; return t; }
  function damp(k, dt) { return 1 - Math.exp(-k * dt); }
  function V(x, y, z) { return new THREE.Vector3(x, y, z); }

  var SCENES = {};

  /* 표지: 공정 카드가 떠 있는 장면 */
  SCENES.cover = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.1, 100);
    cam.position.set(0, 0.6, 18); cam.lookAt(0.6, 0, 0);
    lights(scene, true);
    var grp = new THREE.Group(); grp.position.set(5.0, -0.2, 0); scene.add(grp);
    var defs = [['기획', 0xa8471c], ['대본', 0x2f6b66], ['콘티', 0xfff6ea, '#2b2019'], ['제작', 0xc4622d], ['수정', 0xe4cfb3, '#2b2019'], ['배포', 0x2b2019]];
    var items = [];
    defs.forEach(function (d, i) {
      var c = card(2.3, 1.5, d[1], d[0], d[2]);
      var a = i / defs.length * Math.PI * 2;
      c.userData = { a: a, y: Math.sin(a * 2) * 0.9, ph: i * 1.3 };
      grp.add(c); items.push(c);
    });
    var tor = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.22, 10, 28), M(0x2f6b66)); tor.position.set(-2.2, 2.1, -1); grp.add(tor);
    var ico = new THREE.Mesh(new THREE.IcosahedronGeometry(0.62, 0), M(0xc4622d)); ico.position.set(2.4, -2.4, 0.6); grp.add(ico);
    var sph = new THREE.Mesh(new THREE.SphereGeometry(0.42, 18, 12), M(0xfff6ea)); sph.position.set(2.7, 2.3, -0.5); grp.add(sph);
    var sh = blob(4.5, 0.22); sh.position.set(0, -3.4, 0); grp.add(sh);
    var mx = 0, my = 0;
    window.addEventListener('mousemove', function (e) { mx = e.clientX / window.innerWidth - 0.5; my = e.clientY / window.innerHeight - 0.5; });
    var S = { scene: scene, camera: cam, labels: [], spin: 0,
      setStep: function () {},
      update: function (dt, t, snap) {
        S.spin += dt * 0.18;
        items.forEach(function (c, i) {
          var u = c.userData, a = u.a + S.spin;
          c.position.set(Math.cos(a) * 2.9, u.y + Math.sin(t * 0.9 + u.ph) * 0.18, Math.sin(a) * 2.2);
          c.rotation.set(Math.sin(t * 0.5 + u.ph) * 0.12 - 0.08, -a + Math.PI / 2 + Math.PI * 0.5 * 0 + 0.0, Math.sin(t * 0.7 + u.ph) * 0.06);
          c.lookAt(cam.position.x * 0.4, c.position.y, cam.position.z);
        });
        tor.rotation.set(t * 0.4, t * 0.3, 0); ico.rotation.set(t * 0.3, t * 0.5, 0);
        var tx = mx * 1.2, ty = 0.6 - my * 0.8;
        cam.position.x += (tx - cam.position.x) * (snap ? 1 : damp(2, dt)); cam.position.y += (ty - cam.position.y) * (snap ? 1 : damp(2, dt));
        cam.lookAt(0.6, 0, 0);
      } };
    return S;
  };

  /* ---- 길·차·건물 부품 (내비 장면과 공정 장면이 같이 써요) ---- */
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
    var m = new THREE.Mesh(g, mat); m.userData.segs = segs; return m;
  }
  function reveal(rib, u) { rib.geometry.setDrawRange(0, Math.floor(rib.userData.segs * Math.max(0, Math.min(1, u))) * 6); }
  function dashes(curve, every, color, y, parent) {
    var L = curve.getLength(), n = Math.floor(L / every), geo = new THREE.BoxGeometry(0.07, 0.01, every * 0.45), mat = new THREE.MeshBasicMaterial({ color: color });
    for (var i = 0; i < n; i++) { var u = (i + 0.5) / n, p = curve.getPointAt(u), t = curve.getTangentAt(u); var d = new THREE.Mesh(geo, mat); d.position.set(p.x, y, p.z); d.lookAt(p.x + t.x, y, p.z + t.z); parent.add(d); }
  }
  function carMesh(color) {
    var g = new THREE.Group();
    var body = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.26, 1.2), M(color)); body.position.y = 0.3; g.add(body);
    var cab = new THREE.Mesh(new THREE.BoxGeometry(0.54, 0.24, 0.62), M(0xcfe5e1)); cab.position.set(0, 0.55, -0.06); g.add(cab);
    var roof = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.05, 0.52), M(color)); roof.position.set(0, 0.69, -0.06); g.add(roof);
    var wg = new THREE.CylinderGeometry(0.15, 0.15, 0.1, 10), wm = M(0x1f1712);
    [[-0.35, 0.4], [0.35, 0.4], [-0.35, -0.4], [0.35, -0.4]].forEach(function (p) { var w = new THREE.Mesh(wg, wm); w.rotation.z = Math.PI / 2; w.position.set(p[0], 0.16, p[1]); g.add(w); });
    var hl = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.06, 0.02), new THREE.MeshBasicMaterial({ color: 0xfff1c9 })); hl.position.set(0, 0.32, 0.61); g.add(hl);
    var sh = blob(0.85, 0.32); sh.position.y = 0.02; g.add(sh);
    return g;
  }
  function museumMesh() {
    var g = new THREE.Group();
    var step = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.22, 2.1), M(0xe4cfb3)); step.position.y = 0.11; g.add(step);
    var body = new THREE.Mesh(new THREE.BoxGeometry(3.0, 1.3, 1.5), M(0xfff6ea)); body.position.set(0, 0.87, -0.15); g.add(body);
    var colG = new THREE.CylinderGeometry(0.09, 0.1, 1.1, 8), colM = M(0xfffaf3);
    for (var i = 0; i < 6; i++) { var c = new THREE.Mesh(colG, colM); c.position.set(-1.3 + i * 0.52, 0.77, 0.78); g.add(c); }
    var ent = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.14, 0.5), M(0xe4cfb3)); ent.position.set(0, 1.4, 0.7); g.add(ent);
    var ped = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 3), M(0xa8471c)); ped.rotation.set(0, 0, Math.PI / 2); ped.rotation.y = Math.PI / 2; ped.scale.set(0.55, 1.65, 1.0);
    ped.rotation.set(Math.PI / 2, 0, Math.PI / 2); ped.scale.set(0.55, 3.3, 0.55); ped.position.set(0, 1.72, 0.25);
    var pg = new THREE.Group(); var tri = new THREE.Shape(); tri.moveTo(-1.7, 0); tri.lineTo(1.7, 0); tri.lineTo(0, 0.62); tri.lineTo(-1.7, 0);
    var pm = new THREE.Mesh(new THREE.ExtrudeGeometry(tri, { depth: 2.0, bevelEnabled: false }), M(0xa8471c)); pm.position.set(0, 1.47, -1.0); g.add(pm);
    var gate = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.08, 8, 20, Math.PI), M(0x2f6b66, { emissive: 0x2f6b66, emissiveIntensity: 0 })); gate.position.set(0, 0.2, 1.55); g.add(gate);
    var side = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.06, 8, 16, Math.PI), M(0x8a7564, { emissive: 0xa8471c, emissiveIntensity: 0 })); side.position.set(1.95, 0.2, -0.3); side.rotation.y = Math.PI / 2; g.add(side);
    g.userData = { gate: gate, side: side };
    var sh = blob(2.6, 0.2); sh.position.y = 0.01; g.add(sh);
    return g;
  }
  function schoolMesh() {
    var g = new THREE.Group();
    var b = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.9, 0.9), M(0xfff6ea)); b.position.y = 0.45; g.add(b);
    var r = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.75, 0.55, 4), M(0xc4622d)); r.rotation.y = Math.PI / 4; r.scale.set(1.6, 1, 0.9); r.position.y = 1.17; g.add(r);
    for (var i = 0; i < 3; i++) { var w = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.24, 0.03), M(0x86c9bf)); w.position.set(-0.5 + i * 0.5, 0.55, 0.46); g.add(w); }
    var p = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.9, 6), M(0x6a5444)); p.position.set(-0.95, 0.45, 0.2); g.add(p);
    var f = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.2, 0.02), M(0xa8471c)); f.position.set(-0.78, 0.8, 0.2); g.add(f);
    return g;
  }
  function postMesh(color) {
    var g = new THREE.Group();
    var pole = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.9, 6), M(0x6a5444)); pole.position.y = 0.45; g.add(pole);
    var ball = new THREE.Mesh(new THREE.SphereGeometry(0.16, 14, 10), M(0xb9ab9a, { emissive: color, emissiveIntensity: 0 })); ball.position.y = 0.98; g.add(ball);
    var glow = blob(0.42, 0, 'rgba(134,201,191,0.55)'); glow.position.y = 0.98; glow.rotation.x = 0; glow.material.opacity = 0; g.add(glow);
    g.userData = { ball: ball, glow: glow, v: 0, color: color };
    return g;
  }
  function lightPost(p, on, dt, snap, cam) {
    var d = p.userData; d.v += ((on ? 1 : 0) - d.v) * (snap ? 1 : damp(4, dt));
    d.ball.material.emissiveIntensity = d.v * 0.9; d.ball.material.color.setHex(on ? d.color : 0xb9ab9a);
    d.glow.material.opacity = d.v * 0.6; if (cam) d.glow.lookAt(cam.position);
  }
  function drive(c, curve, u) {
    u = Math.max(0, Math.min(1, u));
    var p = curve.getPointAt(u), t = curve.getTangentAt(u);
    c.position.set(p.x, 0.02, p.z); c.lookAt(p.x + t.x, 0.02, p.z + t.z);
  }

  /* 같은 목적지, 두 길: 왼쪽은 헤매고, 오른쪽은 곧게 */
  SCENES.nav = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 100);
    lights(scene, true);
    var ground = new THREE.Mesh(new THREE.BoxGeometry(23.5, 0.3, 11.6), M(0xdcc6a6)); ground.position.y = -0.15; scene.add(ground);
    var mid = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.02, 11), new THREE.MeshBasicMaterial({ color: 0xd2bb9c })); mid.position.y = 0.01; scene.add(mid);
    var CX = [-5.2, 5.2];
    var parts = CX.map(function (cx, side) {
      var sc = schoolMesh(); sc.position.set(cx, 0, 4.2); scene.add(sc);
      var mu = museumMesh(); mu.position.set(cx, 0, -4.0); scene.add(mu);
      var pts = side === 0
        ? [V(cx, 0, 3.5), V(cx - 2.4, 0, 2.7), V(cx - 1.0, 0, 1.3), V(cx + 2.2, 0, 1.8), V(cx + 2.6, 0, 0.3), V(cx + 0.2, 0, -0.5), V(cx - 2.3, 0, -0.1), V(cx - 2.9, 0, -1.8), V(cx - 1.0, 0, -2.5), V(cx + 2.5, 0, -2.3), V(cx + 2.7, 0, -4.3), V(cx + 2.2, 0, -4.3)]
        : [V(cx, 0, 3.5), V(cx, 0, 1.0), V(cx, 0, -1.4), V(cx, 0, -2.45)];
      var curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.5);
      var road = ribbon(curve, side === 0 ? 0.6 : 0.85, 220, M(side === 0 ? 0xd8c4a8 : 0x3a2c22, { side: THREE.DoubleSide }), 0.012); scene.add(road);
      var lit = ribbon(curve, 0.16, 220, new THREE.MeshBasicMaterial({ color: side === 0 ? 0xc98a62 : 0x86c9bf, side: THREE.DoubleSide }), 0.02); scene.add(lit); reveal(lit, 0);
      if (side === 1) dashes(curve, 0.7, 0xf2d9b8, 0.018, scene);
      var car = carMesh(0xa8471c); scene.add(car); drive(car, curve, 0);
      var posts = [];
      if (side === 1) [0.22, 0.42, 0.62, 0.8, 0.95].forEach(function (u) { var p = postMesh(0x2f6b66); var q = curve.getPointAt(u); p.position.set(q.x + 0.75, 0, q.z); p.userData.u = u; scene.add(p); posts.push(p); });
      return { curve: curve, lit: lit, car: car, mu: mu, sc: sc, posts: posts, u: 0, dur: side === 0 ? 5.2 : 3.2 };
    });
    var L = [lbl('출발: 학교', 'st', parts[0].sc, [-2.1, 0.4, 0.2]), lbl('출발: 학교', 'st', parts[1].sc, [-2.1, 0.4, 0.2]),
      lbl('박물관', 'st', parts[0].mu, [0, 2.7, 0]), lbl('박물관', 'st', parts[1].mu, [0, 2.7, 0]),
      lbl('엉뚱한 문', 'ck bad', parts[0].mu, [2.4, 1.2, -0.3]), lbl('✓ 정문', 'ck', parts[1].mu, [0, 1.25, 1.6])];
    L[4].el.style.opacity = 0; L[5].el.style.opacity = 0;
    cam.position.set(0, 25, 12.5); cam.lookAt(0, 0, -1.9);
    var S = { scene: scene, camera: cam, labels: L, st: 0,
      setStep: function (n, snap) { S.st = n; if (snap) { parts[0].u = n >= 1 ? 1 : 0; parts[1].u = n >= 2 ? 1 : 0; } },
      update: function (dt, t, snap) {
        parts.forEach(function (P, side) {
          var go = S.st >= side + 1;
          if (!go) P.u = 0; else if (!snap) P.u = Math.min(1, P.u + dt / P.dur);
          var e = side === 0 ? P.u : (P.u < 0.5 ? 2 * P.u * P.u : 1 - Math.pow(-2 * P.u + 2, 2) / 2);
          drive(P.car, P.curve, e); reveal(P.lit, e);
          if (side === 0 && go && P.u < 1 && !snap) P.car.rotation.z = Math.sin(t * 6) * 0.03;
          P.posts.forEach(function (p) { lightPost(p, e >= p.userData.u - 0.02, dt, snap, cam); });
          var arrived = P.u >= 1;
          if (side === 0) { P.mu.userData.side.material.emissiveIntensity = arrived ? 0.7 : 0; L[4].el.style.opacity = arrived ? 1 : 0; }
          else { P.mu.userData.gate.material.emissiveIntensity = arrived ? 0.9 : 0; L[5].el.style.opacity = arrived ? 1 : 0; }
        });
      } };
    return S;
  };

  /* 내비 경유지 다섯: 경로 3개, 이 길 맞나요?, 블랙박스, 차량 점검, 정문 */
  SCENES.route = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(34, 16 / 9, 0.1, 120);
    scene.fog = new THREE.Fog(0xf2e7d8, 16, 46);
    lights(scene, true);
    var ground = new THREE.Mesh(new THREE.BoxGeometry(40, 0.3, 70), M(0xdcc6a6)); ground.position.set(0, -0.15, -18); scene.add(ground);
    var WZ = [-1, -10, -19, -28, -38.6];
    var curve = new THREE.CatmullRomCurve3([V(0, 0, 7), V(0, 0, -10), V(0, 0, -39.2)], false, 'catmullrom', 0.5);
    var road = ribbon(curve, 1.5, 120, M(0x3a2c22, { side: THREE.DoubleSide }), 0.012); scene.add(road);
    var lit = ribbon(curve, 0.14, 240, new THREE.MeshBasicMaterial({ color: 0x86c9bf, side: THREE.DoubleSide }), 0.022); scene.add(lit); reveal(lit, 0);
    dashes(curve, 1.2, 0xf2d9b8, 0.018, scene);
    var L0 = curve.getLength();
    function uOf(z) { return (7 - z) / (7 + 39.2); }
    // 1: 갈림길 세 개 (가운데가 추천)
    var br = [-1, 0, 1].map(function (k) {
      var c = new THREE.CatmullRomCurve3([V(0, 0, 2.2), V(k * 1.4, 0, -0.5), V(k * 3.4, 0, -4.5), V(k * 4.6, 0, -8)], false, 'catmullrom', 0.5);
      var m = ribbon(c, k === 0 ? 0.9 : 0.75, 60, new THREE.MeshStandardMaterial({ color: k === 0 ? 0x2f6b66 : 0xcbb79c, transparent: true, opacity: 0.0, side: THREE.DoubleSide, flatShading: true }), k === 0 ? 0.03 : 0.008);
      if (k === 0) m.visible = false;
      scene.add(m); return m;
    });
    // 2: 표지판
    var sign = card(2.6, 1.0, 0x2f6b66, '이 길 맞나요?', '#ffffff'); sign.position.set(2.6, 2.0, WZ[1]); sign.rotation.y = -0.35; scene.add(sign);
    var sp = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.6, 6), M(0x6a5444)); sp.position.set(2.6, 0.8, WZ[1] - 0.05); scene.add(sp);
    // 3: 블랙박스 (차 위 작은 상자)
    var car = carMesh(0xa8471c); scene.add(car);
    var bbox = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.14, 0.2), M(0x1f1712)); bbox.position.set(0, 0.79, 0.05); car.add(bbox);
    var dot = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 6), new THREE.MeshBasicMaterial({ color: 0xff5a3c })); dot.position.set(0, 0.8, 0.16); car.add(dot);
    // 4: 점검 고리
    var scan = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.06, 8, 40), new THREE.MeshBasicMaterial({ color: 0x86c9bf, transparent: true, opacity: 0.0 })); scene.add(scan);
    var arch = new THREE.Mesh(new THREE.TorusGeometry(1.5, 0.1, 8, 28, Math.PI), M(0x2f6b66)); arch.position.set(0, 0, WZ[3]); scene.add(arch);
    // 5: 박물관
    var mu = museumMesh(); mu.position.set(0, 0, -41); scene.add(mu);
    var posts = WZ.slice(0, 4).map(function (z) { var p = postMesh(0x2f6b66); p.position.set(-1.25, 0, z); scene.add(p); return p; });
    var names = ['경로 3개', '이 길 맞나요?', '블랙박스', '차량 점검', '정문'];
    var L = names.map(function (n, i) { return lbl((i + 1) + ' ' + n, 'st', i < 4 ? posts[i] : mu, i < 4 ? [-0.9, 1.5, 0] : [0, 2.9, 0]); });
    var rec = lbl('추천', 'ck', V(0, 0.4, -6.5)); L.push(rec);
    var S = { scene: scene, camera: cam, labels: L, st: 0, u: uOf(4.5), cx: 0, cz: 0,
      setStep: function (n, snap) { S.st = n; S.target = n === 0 ? uOf(4.5) : uOf(WZ[n - 1] + (n === 5 ? 0 : 1.0)); if (snap) S.u = S.target; },
      update: function (dt, t, snap) {
        S.u += (S.target - S.u) * (snap ? 1 : damp(1.3, dt));
        drive(car, curve, S.u); reveal(lit, S.u);
        var cz = car.position.z;
        // 카메라: 차 뒤 왼쪽 위에서 따라가요 (길은 화면 오른쪽)
        var ax = -4.8, ay = 5.6, az = cz + 12;
        cam.position.set(ax, ay, az); cam.lookAt(-3.4, 0.2, cz - 7);
        var b1 = S.st >= 1 ? 1 : 0;
        br.forEach(function (m, i) { var tgt = i === 1 ? b1 : (S.st === 1 ? 0.85 : S.st > 1 ? 0.25 : 0); m.material.opacity += (tgt - m.material.opacity) * (snap ? 1 : damp(3, dt)); m.visible = i !== 1 || S.st >= 1; });
        rec.el.style.opacity = S.st === 1 ? 1 : 0;
        sign.position.y = 2.0 + (S.st === 2 && !snap ? Math.sin(t * 2) * 0.06 : 0);
        dot.visible = S.st >= 3 && (snap || Math.sin(t * Math.PI * 2 * 0.8) > -0.2);
        var sOn = S.st === 4;
        scan.material.opacity += ((sOn ? 0.9 : 0) - scan.material.opacity) * (snap ? 1 : damp(4, dt));
        scan.position.set(0, 0.5, cz + (snap ? 0 : Math.sin(t * 2.2) * 0.9));
        arch.material.emissive = arch.material.emissive || new THREE.Color(0); arch.material.emissive.setHex(0x2f6b66); arch.material.emissiveIntensity = S.st >= 4 ? 0.7 : 0;
        mu.userData.gate.material.emissiveIntensity = S.st >= 5 ? 0.9 : 0;
        posts.forEach(function (p, i) { lightPost(p, S.st >= i + 1, dt, snap, cam); });
        L.forEach(function (l, i) { if (i < 5) l.el.className = 'lbl st' + (S.st === i + 1 ? ' on' : '') + (S.st && S.st < i + 1 ? ' dim' : ''); });
      } };
    S.setStep(0, true);
    return S;
  };

  /* 공정: 같은 길 위의 여섯 정거장 */
  SCENES.pipeline = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(34, 16 / 9, 0.1, 100);
    scene.fog = new THREE.Fog(0xf0e4d4, 24, 48);
    lights(scene, true);
    var names = ['기획', '대본', '콘티', '제작', '수정', '배포'];
    var pts = [V(-9, 0, 1.2), V(-5.4, 0, -0.9), V(-1.8, 0, 0.9), V(1.8, 0, -0.9), V(5.4, 0, 0.9), V(9, 0, -1.2)];
    var curve = new THREE.CatmullRomCurve3([V(-13, 0, 2.2)].concat(pts, [V(12.5, 0, -2.2)]), false, 'catmullrom', 0.5);
    var base = new THREE.Mesh(new THREE.BoxGeometry(32, 0.3, 10), M(0xdcc6a6)); base.position.y = -0.15; scene.add(base);
    var road = ribbon(curve, 1.3, 260, M(0x3a2c22, { side: THREE.DoubleSide }), 0.014); scene.add(road);
    dashes(curve, 0.9, 0xf2d9b8, 0.02, scene);
    var lit = ribbon(curve, 0.16, 400, new THREE.MeshBasicMaterial({ color: 0xc4622d, side: THREE.DoubleSide }), 0.026); scene.add(lit); reveal(lit, 0);
    var tAt = pts.map(function (p) { var best = 0, bd = 1e9; for (var i = 0; i <= 400; i++) { var q = curve.getPointAt(i / 400); var d = q.distanceToSquared(p); if (d < bd) { bd = d; best = i / 400; } } return best; });
    var icons = [new THREE.OctahedronGeometry(0.3, 0), new THREE.BoxGeometry(0.44, 0.56, 0.08), new THREE.BoxGeometry(0.6, 0.4, 0.08), new THREE.IcosahedronGeometry(0.3, 0), new THREE.TorusGeometry(0.22, 0.09, 6, 16), new THREE.ConeGeometry(0.28, 0.55, 4)];
    var stations = pts.map(function (p, i) {
      var g = new THREE.Group(); g.position.copy(p); scene.add(g);
      var pad = new THREE.Mesh(new THREE.CylinderGeometry(1.15, 1.2, 0.06, 28), M(0xfff6ea)); pad.position.y = 0.0; g.add(pad);
      var ring = new THREE.Mesh(new THREE.TorusGeometry(1.15, 0.06, 6, 40), M(0xd8c3a6, { emissive: 0xc4622d, emissiveIntensity: 0 })); ring.rotation.x = Math.PI / 2; ring.position.y = 0.04; g.add(ring);
      var puls = new THREE.Mesh(new THREE.RingGeometry(1.15, 1.32, 40), new THREE.MeshBasicMaterial({ color: 0xc4622d, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false })); puls.rotation.x = -Math.PI / 2; puls.position.y = 0.05; g.add(puls);
      var post = postMesh(0xc4622d); post.position.set(0, 0, -1.55); post.scale.setScalar(1.4); g.add(post);
      var ic = new THREE.Mesh(icons[i], M(0x6a5444)); ic.position.set(0, 2.05, -1.55); g.add(ic);
      g.userData = { ring: ring, puls: puls, glow: 0, pt: 0, icon: ic, post: post };
      return g;
    });
    var gateAt = [(tAt[0] + tAt[1]) / 2, (tAt[2] + tAt[3]) / 2, (tAt[4] + tAt[5]) / 2], gateStep = [1, 3, 6];
    var gates = gateAt.map(function (u) {
      var p = curve.getPointAt(u), tg = curve.getTangentAt(u);
      var g = new THREE.Group(); g.position.copy(p); g.lookAt(p.x + tg.x, 0, p.z + tg.z); scene.add(g);
      var arch = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.09, 8, 24, Math.PI), M(0x9bb5b0, { emissive: 0x2f6b66, emissiveIntensity: 0 })); g.add(arch);
      g.userData = { arch: arch, glow: 0 };
      return g;
    });
    var car = carMesh(0xa8471c); car.scale.setScalar(1.25); scene.add(car);
    var labels = stations.map(function (g, i) { return lbl((i + 1) + ' ' + names[i], 'st', g, [0, -0.3, 1.75]); });
    var ckl = gates.map(function (g) { return lbl('✓ 선생님 확인', 'ck', g, [0, 1.9, 0]); });
    var S = { scene: scene, camera: cam, labels: labels.concat(ckl), st: 0, u: 0.03, camX: 0,
      setStep: function (n, snap) { S.st = n; S.target = n === 0 ? 0.03 : tAt[n - 1]; if (snap) { S.u = S.target; stations.forEach(function (g, i) { g.userData.glow = n >= i + 1 ? 1 : 0; }); gates.forEach(function (g, i) { g.userData.glow = n >= gateStep[i] ? 1 : 0; }); } },
      update: function (dt, t, snap) {
        S.u += (S.target - S.u) * (snap ? 1 : damp(1.4, dt));
        drive(car, curve, S.u); reveal(lit, S.u);
        var p = car.position;
        stations.forEach(function (g, i) {
          var on = S.st >= i + 1, here = S.st === i + 1, d = g.userData;
          d.glow += ((on ? 1 : 0) - d.glow) * (snap ? 1 : damp(3, dt));
          d.ring.material.emissiveIntensity = d.glow * 0.9; d.ring.material.color.setHex(on ? 0xc4622d : 0xd8c3a6);
          d.icon.material.color.setHex(here ? 0xa8471c : on ? 0x8a6a50 : 0x6a5444);
          d.icon.rotation.y = t * (here ? 1.4 : 0.3) + i;
          d.icon.position.y = 2.05 + (here && !snap ? Math.sin(t * 3) * 0.08 : 0);
          lightPost(d.post, on, dt, snap, cam);
          if (here && !snap) { d.pt = (d.pt + dt * 0.8) % 1; d.puls.scale.setScalar(1 + d.pt * 0.8); d.puls.material.opacity = (1 - d.pt) * 0.55; } else d.puls.material.opacity = 0;
          labels[i].el.className = 'lbl st' + (here ? ' on' : '') + (S.st && !on ? ' dim' : '');
        });
        gates.forEach(function (g, i) {
          var on = S.st >= gateStep[i], d = g.userData; d.glow += ((on ? 1 : 0) - d.glow) * (snap ? 1 : damp(3, dt));
          d.arch.material.emissiveIntensity = d.glow * 0.8; d.arch.material.color.setHex(on ? 0x3b8a82 : 0x9bb5b0);
          ckl[i].el.style.opacity = d.glow;
        });
        var wide = S.st === 0, cx = wide ? 0 : p.x * 0.7;
        S.camX += (cx - S.camX) * (snap ? 1 : damp(1.4, dt));
        var cz = wide ? 24 : 16.5, cy = wide ? 12.5 : 8.6;
        cam.position.x = S.camX; cam.position.y += (cy - cam.position.y) * (snap ? 1 : damp(1.4, dt)); cam.position.z += (cz - cam.position.z) * (snap ? 1 : damp(1.4, dt));
        cam.lookAt(S.camX, -0.6, -0.4);
      } };
    cam.position.set(0, 12.5, 24);
    return S;
  };

  /* 부정행위 여섯 칸: 신호가 지나가고, 한 칸씩 살펴요 (추상 도형만) */
  SCENES.cheat = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.1, 100);
    scene.fog = new THREE.Fog(0x1a1511, 20, 42);
    lights(scene, false);
    var names = ['사전', '입력', '전송', '연산', '출력', '기타'];
    var X = [-8.5, -5.1, -1.7, 1.7, 5.1, 8.5];
    var floor = new THREE.Mesh(new THREE.BoxGeometry(30, 0.2, 7), M(0x2a211a)); floor.position.y = -0.95; scene.add(floor);
    var line = new THREE.Mesh(new THREE.BoxGeometry(19, 0.04, 0.06), new THREE.MeshBasicMaterial({ color: 0x5a4636 })); line.position.set(0, 0.0, 0); scene.add(line);
    var amber = 0xf2a65a, cream = 0xf6ecdf, mint = 0x86c9bf;
    var objs = names.map(function (n, i) {
      var g = new THREE.Group(); g.position.set(X[i], 0, 0); scene.add(g);
      var pl = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 1.15, 0.3, 24), M(0x382c22)); pl.position.y = -0.7; g.add(pl);
      var rim = new THREE.Mesh(new THREE.TorusGeometry(1.08, 0.03, 6, 40), new THREE.MeshBasicMaterial({ color: amber, transparent: true, opacity: 0.25 })); rim.rotation.x = Math.PI / 2; rim.position.y = -0.54; g.add(rim);
      var shape = new THREE.Group(); shape.position.y = 0.55; g.add(shape);
      var mats = [];
      function add(geo, color, x, y, z) { var m = M(color, { emissive: color, emissiveIntensity: 0.05 }); mats.push(m); var me = new THREE.Mesh(geo, m); me.position.set(x || 0, y || 0, z || 0); shape.add(me); return me; }
      if (i === 0) { for (var k = 0; k < 3; k++) { var sl = add(new THREE.BoxGeometry(1.1, 0.08, 0.8), cream, 0, -0.3 + k * 0.2, 0); sl.rotation.y = (k - 1) * 0.22; } }
      if (i === 1) { add(new THREE.TorusGeometry(0.55, 0.11, 8, 28), cream); add(new THREE.SphereGeometry(0.2, 14, 10), amber); }
      if (i === 2) { for (var a = 0; a < 3; a++) { var arc = add(new THREE.TorusGeometry(0.25 + a * 0.22, 0.05, 6, 20, Math.PI * 0.6), a === 0 ? amber : mint); arc.rotation.z = Math.PI * 0.2; arc.position.x = -0.25; } }
      if (i === 3) { add(new THREE.IcosahedronGeometry(0.55, 0), mint); var w = new THREE.Mesh(new THREE.IcosahedronGeometry(0.78, 0), new THREE.MeshBasicMaterial({ color: mint, wireframe: true, transparent: true, opacity: 0.35 })); shape.add(w); }
      if (i === 4) { for (var b = 0; b < 3; b++) { var rr = add(new THREE.TorusGeometry(0.2 + b * 0.16, 0.05, 6, 24), b === 0 ? amber : cream); rr.rotation.y = Math.PI / 2; rr.position.x = b * 0.18 - 0.2; } }
      if (i === 5) { var P = [V(-0.42, -0.25, 0), V(0.42, -0.25, 0), V(0, 0.42, 0)]; P.forEach(function (p) { add(new THREE.SphereGeometry(0.2, 12, 10), cream, p.x, p.y, p.z); }); [[0, 1], [1, 2], [2, 0]].forEach(function (e) { var a1 = P[e[0]], b1 = P[e[1]]; var len = a1.distanceTo(b1); var cyl = add(new THREE.CylinderGeometry(0.035, 0.035, len, 6), 0x8a7564); cyl.position.copy(a1.clone().add(b1).multiplyScalar(0.5)); cyl.lookAt(b1.x + g.position.x, b1.y + 0.55, b1.z); cyl.rotateX(Math.PI / 2); }); }
      g.userData = { shape: shape, mats: mats, rim: rim, f: 0 };
      return g;
    });
    // 신호 점
    var N = 14, sig = [];
    var sgeo = new THREE.SphereGeometry(0.11, 10, 8);
    for (var s = 0; s < N; s++) { var m = new THREE.Mesh(sgeo, new THREE.MeshBasicMaterial({ color: amber, transparent: true })); m.userData.u = s / N; scene.add(m); sig.push(m); }
    var halo = blob(0.5, 0, 'rgba(242,166,90,0.55)');
    var halos = sig.map(function (m) { var h = halo.clone(); h.material = halo.material.clone(); h.rotation.x = 0; scene.add(h); return h; });
    // 막는 벽 (전송 칸 앞)
    var wallX = (X[1] + X[2]) / 2;
    var wall = new THREE.Mesh(new THREE.BoxGeometry(0.16, 2.6, 3.2), new THREE.MeshStandardMaterial({ color: mint, emissive: mint, emissiveIntensity: 0.35, transparent: true, opacity: 0.0, flatShading: true }));
    wall.position.set(wallX, 0.4, 0); scene.add(wall);
    var labels = objs.map(function (g, i) { return lbl(names[i], 'st', g, [0, -1.0, 1.6]); });
    var S = { scene: scene, camera: cam, labels: labels, st: 0, wallO: 0, cx: 0, cy: 6, cz: 23, lx: 0,
      setStep: function (n, snap) { S.st = n; if (snap) { S.wallO = n === 7 ? 1 : 0; S.place(); S.cx = S.tx; S.cy = S.ty; S.cz = S.tz; S.lx = S.tlx; objs.forEach(function (g, i) { g.userData.f = n === i + 1 ? 1 : 0; }); } else S.place(); },
      place: function () {
        var n = S.st;
        if (n >= 1 && n <= 6) { var x = X[n - 1]; S.tx = x + 3.4; S.ty = 2.6; S.tz = 9.5; S.tlx = x + 3.0; }
        else { S.tx = 0; S.ty = 5.4; S.tz = 20; S.tlx = 0; }
      },
      update: function (dt, t, snap) {
        var k = snap ? 1 : damp(1.6, dt);
        S.cx += (S.tx - S.cx) * k; S.cy += (S.ty - S.cy) * k; S.cz += (S.tz - S.cz) * k; S.lx += (S.tlx - S.lx) * k;
        cam.position.set(S.cx, S.cy, S.cz); cam.lookAt(S.lx, 0.2, 0);
        S.wallO += ((S.st === 7 ? 1 : 0) - S.wallO) * (snap ? 1 : damp(3, dt));
        wall.material.opacity = S.wallO * 0.45; wall.scale.y = 0.05 + S.wallO * 0.95; wall.position.y = -0.85 + S.wallO * 1.25;
        objs.forEach(function (g, i) {
          var d = g.userData, focus = S.st === i + 1, dim = S.st >= 1 && S.st <= 6 && !focus;
          d.f += ((focus ? 1 : 0) - d.f) * (snap ? 1 : damp(4, dt));
          d.shape.rotation.y = snap ? 0.5 : t * (0.35 + d.f * 0.5) + i;
          d.shape.position.y = 0.55 + (snap ? 0 : Math.sin(t * 1.6 + i) * 0.06) + d.f * 0.2;
          d.shape.scale.setScalar(1 + d.f * 0.25);
          d.mats.forEach(function (m) { m.emissiveIntensity = 0.05 + d.f * 0.35; m.opacity = 1; });
          d.rim.material.opacity = 0.25 + d.f * 0.7;
          labels[i].el.className = 'lbl st' + (focus ? ' on' : '') + (dim ? ' dim' : '');
        });
        var blocked = S.wallO > 0.5;
        sig.forEach(function (m, j) {
          var u = m.userData.u;
          if (!snap) u = (u + dt * 0.07) % 1;
          m.userData.u = u;
          var x = -10 + u * 20;
          var vis = 1;
          if (blocked && x > wallX - 0.2) { vis = 0; }
          var local = ((x - X[0]) / (X[1] - X[0])) % 1; if (local < 0) local += 1;
          var y = 0.12 + Math.sin(local * Math.PI) * 0.9;
          if (x < X[0] || x > X[5]) y = 0.12;
          m.position.set(x, y, 0);
          var edge = Math.min(1, (x + 10) / 1.2, (10 - x) / 1.2);
          m.material.opacity = vis * Math.max(0, edge);
          halos[j].position.copy(m.position); halos[j].lookAt(cam.position);
          halos[j].material.opacity = m.material.opacity * 0.9;
        });
      } };
    S.place();
    return S;
  };

  /* 마무리: 일곱 무기 카드가 고리를 이루며 돌아요 */
  SCENES.made = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.1, 100);
    lights(scene, false);
    var root = new THREE.Group(); root.position.set(5.2, 0.2, 0); scene.add(root);
    var core = new THREE.Mesh(new THREE.IcosahedronGeometry(1.0, 1), M(0xf2a65a, { emissive: 0xf2a65a, emissiveIntensity: 0.35 })); root.add(core);
    var glow = blob(2.6, 0, 'rgba(242,166,90,0.35)'); glow.rotation.x = 0; root.add(glow);
    var names = [['게임', 0xa8471c], ['슬라이드', 0x2f6b66], ['영상', 0xc4622d], ['수업 도구', 0xf6ecdf, '#2b2019'], ['데이터', 0x3b8a82], ['법 확인', 0xe4cfb3, '#2b2019'], ['기획', 0xf2a65a, '#1a1511']];
    var ring = new THREE.Group(); ring.rotation.x = 0.32; ring.rotation.z = -0.12; root.add(ring);
    var cards = names.map(function (n, i) { var c = card(1.7, 1.1, n[1], n[0], n[2]); c.userData.a = i / names.length * Math.PI * 2; c.userData.r0 = 9 + i; ring.add(c); return c; });
    cam.position.set(0, 0.8, 18); cam.lookAt(0.4, 0, 0);
    var S = { scene: scene, camera: cam, labels: [], spin: 0, arrive: 0,
      setStep: function (n, snap) { if (snap && REDUCED) S.arrive = 1; },
      update: function (dt, t, snap) {
        if (!snap) { S.spin += dt * 0.22; S.arrive += (1 - S.arrive) * damp(1.3, dt); } else if (REDUCED) S.arrive = 1;
        cards.forEach(function (c, i) {
          var r = 3.3 + (1 - S.arrive) * c.userData.r0, a = c.userData.a + S.spin + (1 - S.arrive) * 2;
          c.position.set(Math.cos(a) * r, Math.sin(t * 1.1 + i) * 0.12, Math.sin(a) * r);
          c.lookAt(cam.position.x - root.position.x, c.position.y, cam.position.z);
        });
        core.rotation.set(t * 0.2, t * 0.3, 0);
        glow.lookAt(cam.position);
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
    state: function () { return { slide: cur, step: step, gl: GL.ok, reduced: REDUCED, active: GL.active ? GL.active.kind : null }; }
  };
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(start, start); else start();
})();
