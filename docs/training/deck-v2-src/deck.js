/* deck-v2 · 진행 엔진 + 3D 장면 (ES2017 문법만) */
(function () {
  'use strict';
  var REDUCED = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  if (/[?&]reduced=1/.test(location.search)) REDUCED = true;
  var NOGL = /[?&]nogl=1/.test(location.search);
  document.documentElement.className += ' js' + (REDUCED ? ' reduced' : '');
  var wipe = document.getElementById('wipe'), lastAg = null;
  var A = window.anime;
  var stage = document.getElementById('stage');
  var slides = [].slice.call(stage.querySelectorAll('.slide'));
  var notesEl = document.getElementById('notes');
  var cur = -1, step = 0, scale = 1;
  var AGENDA = ['여는 말', '하네스', '같은 부탁 다른 결과', '김치볶음밥', '실습', '마무리', '시간이 남으면'];

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
    if (shown.length) anim(shown, { opacity: [0, 1], translateY: [28, 0], scale: [0.97, 1], filter: ['blur(10px)', 'blur(0px)'], duration: 820, delay: A.stagger(110), ease: 'outExpo',
      onComplete: function () { shown.forEach(function (e) { e.style.filter = ''; }); } });
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
      // 섹션이 바뀌면 빛 한 줄기가 화면을 훑고 지나가요
      var ag = s.getAttribute('data-agenda');
      if (!REDUCED && wipe && (s.classList.contains('section') || (lastAg !== null && ag !== lastAg))) {
        A.utils.remove(wipe);
        anim(wipe, { translateX: ['-100%', '100%'], skewX: [-12, -12], opacity: [{ to: 1, duration: 120 }, { to: 0, duration: 520, delay: 300 }], duration: 940, ease: 'inOutQuad' });
      }
      lastAg = ag;
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
  // 움직임 길이는 두 가지만: 짧게 400ms · 길게 700ms (+ 사이 간격 90ms)
  var T1 = 400, T2 = 700, GAP = 90;
  // 여기저기서: 말풍선·제목이 화면 밖에서 쏟아져 들어와요
  FX.pour = {
    enter: function (s) {
      var hb = [].slice.call(s.querySelectorAll('.hb')), st = s.querySelector('.stmt');
      if (REDUCED) { A.utils.set(hb, { opacity: 1 }); A.utils.set(st, { opacity: 1 }); return; }
      hb.forEach(function (e, i) {
        var x = parseFloat(e.style.left) < 900 ? -700 : 700, y = parseFloat(e.style.top) < 540 ? -240 : 240;
        anim(e, { opacity: [0, 1], translateX: [x, 0], translateY: [y, 0], rotate: [i % 2 ? 8 : -8, 0], duration: T2, delay: 120 + i * GAP, ease: 'outExpo' });
      });
      anim(st, { opacity: [0, 1], scale: [0.94, 1], duration: T2, delay: 120 + hb.length * GAP, ease: 'outExpo' });
    }
  };
  // 진입장벽: 생각 풍선 셋이 차례로 뜨고, 4단계에서 벽돌처럼 쌓여요
  FX.wall = {
    enter: function (s, st) { this.step(s, st, 0); },
    step: function (s, st) {
      var b = s.querySelectorAll('.brick');
      [].forEach.call(b, function (e, i) { e.classList.toggle('on', st >= i + 1); });
      s.querySelector('.wall').classList.toggle('stacked', st >= 4);
    }
  };
  // 옛날 이야기: 금이 가고 벽이 무너져요
  FX.crack = {
    enter: function (s) {
      var w = s.querySelector('.wall'), big = s.querySelector('.big');
      w.classList.remove('fallen'); w.classList.add('on');
      if (REDUCED) { w.classList.add('fallen'); A.utils.set(big, { opacity: 1 }); return; }
      A.utils.set(big, { opacity: 0 });
      later(function () { w.classList.add('cracked'); }, 350);
      later(function () { w.classList.add('fallen'); anim(big, { opacity: [0, 1], translateY: [30, 0], duration: T2, ease: 'outExpo' }); }, 1150);
    },
    step: function (s, st) { if (st >= 1) s.querySelector('.wall').classList.add('cracked', 'fallen'); },
    leave: function (s) { s.querySelector('.wall').classList.remove('cracked', 'fallen'); }
  };
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
    var m = stage.querySelector('.motto'), s = m && m.closest('.slide');
    if (!s) return;
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
  var GL = { ok: false, r: null, canvas: null, active: null, sceneEl: null, raf: 0, last: 0, slow: 0, pr: 1.5, cache: {}, fx: null, fxOn: false, env: {} };

  /* ---------- 시네마틱 층: CC0 사진 환경(Poly Haven · ambientCG) · PBR 재질 · 후처리 ----------
     사진은 만들 때 build.py가 data URI로 넣어요 (출처·라이선스: docs/training/deck-v2-NOTICE.md). 외부 요청 0개. */
  var ASSET = /*__ASSETS__*/{};
  var IMG = {};
  var FXQ = /[?&]fx=([01])/.exec(location.search), FXMODE = FXQ ? +FXQ[1] : -1;   // 1=늘 켬(점검용) · 0=끔 · -1=자동
  function preload(cb) {
    var keys = Object.keys(ASSET), left = keys.length, done = false;
    function fin() { if (!done) { done = true; cb(); } }
    if (!left || NOGL) { fin(); return; }
    keys.forEach(function (k) { var im = new Image(); im.onload = im.onerror = function () { if (im.naturalWidth) IMG[k] = im; if (--left === 0) fin(); }; im.src = ASSET[k]; });
    setTimeout(fin, 5000);
  }
  // CC0 3D 모델 (Poly Haven glTF, 파일 안에 통째로): 시작 전에 한 번 풀어 둬요
  var MODELS = /*__MODELS__*/{};
  var MDL = {};
  function loadModels(cb) {
    var keys = Object.keys(MODELS), left = keys.length, done = false;
    function fin() { if (!done) { done = true; cb(); } }
    if (!left || NOGL || !window.THREE || !THREE.GLTFLoader) { fin(); return; }
    function one() { if (--left === 0) fin(); }
    keys.forEach(function (k) {
      try {
        new THREE.GLTFLoader().parse(MODELS[k], '', function (g) {
          g.scene.traverse(function (o) {
            if (!o.isMesh) return;
            ['map', 'emissiveMap'].forEach(function (m) { if (o.material[m]) { o.material[m].encoding = THREE.LinearEncoding; o.material[m].needsUpdate = true; } });
            o.castShadow = o.receiveShadow = true;
          });
          MDL[k] = g.scene; one();
        }, one);
      } catch (e) { one(); }
    });
    setTimeout(fin, 9000);
  }
  // 모델 복제: 바닥 가운데에 놓고, 가장 긴 변이 size가 되게
  function modelOf(name, size) {
    if (!MDL[name]) return null;
    var m = MDL[name].clone(true), box = new THREE.Box3().setFromObject(m), c = box.getCenter(V(0, 0, 0)), d = box.getSize(V(0, 0, 0)), k = size / Math.max(d.x, d.y, d.z);
    var g = new THREE.Group(); m.position.set(-c.x, -box.min.y, -c.z); g.add(m); g.scale.setScalar(k); g.userData.dims = d.multiplyScalar(k);
    return g;
  }
  var _tx = {};
  function TX(key, rx, ry) {
    if (!IMG[key]) return null;
    var id = key + '|' + rx + '|' + ry;
    if (_tx[id]) return _tx[id];
    var t = new THREE.Texture(IMG[key]); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx || 1, ry || rx || 1);
    t.anisotropy = 8; t.needsUpdate = true; _tx[id] = t; return t;
  }
  // PBR 묶음: 색 · 노멀 · 거칠기 (1k CC0 텍스처)
  function pbr(set, rx, ry) {
    var o = {}, d = TX('t_' + set + '_diff', rx, ry), n = TX('t_' + set + '_nor', rx, ry), r = TX('t_' + set + '_rough', rx, ry);
    if (d) o.map = d; if (n) o.normalMap = n; if (r) o.roughnessMap = r; return o;
  }
  // 진짜처럼 보이는 재질: 플라스틱(클리어코트) · 금속 · 자동차 도장 · 유리(환경 반사만 더하기)
  var PH = {
    plastic: function (c, o) { return new THREE.MeshPhysicalMaterial(Object.assign({ color: c, roughness: 0.3, metalness: 0, clearcoat: 0.85, clearcoatRoughness: 0.1 }, o || {})); },
    metal: function (c, r, o) { return new THREE.MeshStandardMaterial(Object.assign({ color: c, roughness: r === undefined ? 0.28 : r, metalness: 1 }, o || {})); },
    paint: function (c, o) { return new THREE.MeshPhysicalMaterial(Object.assign({ color: c, roughness: 0.36, metalness: 0.5, clearcoat: 1, clearcoatRoughness: 0.05 }, o || {})); },
    glass: function (o) { return new THREE.MeshStandardMaterial(Object.assign({ color: 0x3a414c, roughness: 0.03, metalness: 1, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, envMapIntensity: 1.8 }, o || {})); },
    tint: function (c, op) { return new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.05, metalness: 0, transparent: true, opacity: op, depthWrite: false, clearcoat: 1 }); }
  };
  // 장면마다 어떤 사진 환경을 쓰는지: 길(해 질 녘 시골길) · 시험장(학교 강당)
  var SEG = { cover: 'road', reveal: 'road', horse: 'road', kitchenA: 'kitchen', kitchenB: 'kitchen', made: 'road', swap: 'hall', recap: 'hall', story: 'hall', kit: 'hall', look: 'hall' };
  function envTex(seg) {
    if (GL.env[seg] !== undefined) return GL.env[seg];
    var im = IMG['env_' + seg]; if (!im) { GL.env[seg] = null; return null; }
    var t = new THREE.Texture(im); t.mapping = THREE.EquirectangularReflectionMapping; t.needsUpdate = true;
    var pm = new THREE.PMREMGenerator(GL.r), rt = pm.fromEquirectangular(t); pm.dispose(); t.dispose();
    GL.env[seg] = rt.texture; return rt.texture;
  }
  function dress(S, kind) {
    var seg = SEG[kind] || 'road', sc = S.scene, env = envTex(seg);
    if (env) sc.environment = env;
    var bd = IMG['bd_' + seg];
    if (bd && !S.noBg) { var t = new THREE.Texture(bd); t.needsUpdate = true; t.center.set(0.5, 0.5); t.repeat.set(0.9, 0.9); sc.background = t; S.bg = t; }
    if (env) sc.traverse(function (o) { if (o.isHemisphereLight) o.intensity *= 0.3; else if (o.isDirectionalLight) o.intensity *= (S.lightK || 0.75); });
    S.fx = Object.assign({ focus: [0.5, 0.5], r: [0.62, 0.6], blur: 0.7, bloom: 0.45, grain: 0.035, vig: 0.42 }, S.fx || {});
  }
  // 후처리 마지막 단: 얕은 초점(초점 밖 흐림) · 비네트 · 필름 그레인 · 부드러운 S 곡선
  function finalShader() {
    return { uniforms: { tDiffuse: { value: null }, uRes: { value: new THREE.Vector2(1920, 1080) }, uFocus: { value: new THREE.Vector2(0.5, 0.5) }, uR: { value: new THREE.Vector2(0.6, 0.6) },
      uBlur: { value: 0.7 }, uGrain: { value: 0.035 }, uVig: { value: 0.4 }, uTime: { value: 0 } },
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
      fragmentShader: [
        'uniform sampler2D tDiffuse; uniform vec2 uRes; uniform vec2 uFocus; uniform vec2 uR; uniform float uBlur; uniform float uGrain; uniform float uVig; uniform float uTime; varying vec2 vUv;',
        'float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }',
        'void main(){',
        '  vec2 d = (vUv - uFocus) / uR; float b = smoothstep(0.7, 1.6, length(d)) * uBlur;',
        '  vec3 c = texture2D(tDiffuse, vUv).rgb;',
        '  if (b > 0.02) { vec3 acc = c; float rad = b * 7.0 * (uRes.y / 1080.0);',
        '    for (int i = 1; i < 16; i++) { float fi = float(i); float a = fi * 2.39996; float r = sqrt(fi / 15.0) * rad; acc += texture2D(tDiffuse, vUv + vec2(cos(a), sin(a)) * r / uRes).rgb; }',
        '    c = acc / 16.0; }',
        '  vec2 q = (vUv - 0.5) * vec2(uRes.x / uRes.y, 1.0); c *= 1.0 - uVig * smoothstep(0.35, 1.05, length(q));',
        '  c = mix(c, c * c * (3.0 - 2.0 * c), 0.16);',
        '  c += (h(vUv * uRes + fract(uTime * 7.13) * 100.0) - 0.5) * uGrain;',
        '  gl_FragColor = vec4(c, 1.0);',
        '}'].join('\n') };
  }
  function initFX() {
    if (!THREE.EffectComposer || !THREE.UnrealBloomPass || FXMODE === 0) return;
    try {
      var c = new THREE.EffectComposer(GL.r), rp = new THREE.RenderPass(new THREE.Scene(), new THREE.PerspectiveCamera());
      var bl = new THREE.UnrealBloomPass(new THREE.Vector2(960, 540), 0.45, 0.5, 0.9), fin = new THREE.ShaderPass(finalShader());
      c.addPass(rp); c.addPass(bl); c.addPass(fin);
      GL.fx = { c: c, rp: rp, bl: bl, fin: fin }; GL.fxOn = true;
    } catch (e) { GL.fx = null; GL.fxOn = false; }
  }
  var _fv;
  function draw(S, t, snap) {
    if (!(GL.fx && GL.fxOn)) { GL.r.render(S.scene, S.camera); return; }
    var f = S.fx || {}, u = GL.fx.fin.uniforms, fo = f.focus || [0.5, 0.5];
    if (S.focusObj) {
      if (!_fv) _fv = new THREE.Vector3();
      if (S.focusObj.isObject3D) S.focusObj.getWorldPosition(_fv); else _fv.copy(S.focusObj);
      _fv.project(S.camera); fo = [(_fv.x + 1) / 2, (_fv.y + 1) / 2];
    }
    if (!S._fo || snap) S._fo = [fo[0], fo[1], f.r[0], f.r[1], f.blur];
    var k = snap ? 1 : 0.08, F = S._fo;
    F[0] += (fo[0] - F[0]) * k; F[1] += (fo[1] - F[1]) * k; F[2] += (f.r[0] - F[2]) * k; F[3] += (f.r[1] - F[3]) * k; F[4] += (f.blur - F[4]) * k;
    GL.fx.rp.scene = S.scene; GL.fx.rp.camera = S.camera;
    GL.fx.bl.strength = f.bloom;
    u.uFocus.value.set(F[0], F[1]); u.uR.value.set(F[2], F[3]); u.uBlur.value = F[4];
    u.uGrain.value = REDUCED ? f.grain * 0.6 : f.grain; u.uVig.value = f.vig; u.uTime.value = t || 0;
    GL.fx.c.render();
  }
  // 천천히 흐르는 카메라 (트럭·달리): 장면이 정한 자리에서 아주 조금만 움직여요
  function camRestore(S) { if (S._cb) S.camera.position.copy(S._cb); }
  function camDrift(S, t) {
    if (!S._cb) S._cb = new THREE.Vector3();
    S._cb.copy(S.camera.position);
    if (S.noDrift) return;
    S.camera.updateMatrixWorld();
    var e = S.camera.matrixWorld.elements, D = Math.min(30, S.camera.position.length()), k = S.drift === undefined ? 1 : S.drift;
    var a = Math.sin(t * 0.17) * 0.012 * D * k, b = Math.sin(t * 0.13 + 1) * 0.006 * D * k, f = -(1 - Math.cos(t * 0.09)) * 0.012 * D * k;
    S.camera.position.x += e[0] * a + e[4] * b + e[8] * f;
    S.camera.position.y += e[1] * a + e[5] * b + e[9] * f;
    S.camera.position.z += e[2] * a + e[6] * b + e[10] * f;
    if (S.bg) S.bg.offset.set(Math.max(-0.045, Math.min(0.045, S.camera.position.x * 0.003)), Math.max(-0.045, Math.min(0.045, (S.camera.position.y - 2) * 0.002)));
  }
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
      initFX();
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
    if (GL.fx) {
      GL.fx.c.setPixelRatio(GL.pr); GL.fx.c.setSize(Math.round(w * scale), Math.round(h * scale));
      GL.fx.fin.uniforms.uRes.value.set(Math.round(w * scale * GL.pr), Math.round(h * scale * GL.pr));
    }
  }
  function sceneStep(s, st, entering) {
    var kind = s.getAttribute('data-scene');
    var ck = s.querySelector('[data-clock]');
    if (ck && !GL.ok) ck.textContent = (+((ck.getAttribute('data-t') || '').split(',')[st]) || 0).toFixed(1);
    if (!kind || !GL.ok) return;
    if (entering || GL.sceneEl !== s) {
      var S = GL.cache[kind];
      if (!S) { S = GL.cache[kind] = SCENES[kind](s); S.kind = kind; dress(S, kind); }
      GL.active = S; GL.sceneEl = s;
      camRestore(S);
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
  function renderOnce() { var S = GL.active; draw(S, 2.0, true); projectLabels(S); }
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
      // 느린 PC: 먼저 후처리를 끄고(점검용 fx=1이 아니면), 그래도 느리면 해상도를 낮춰요
      if (acc > 2) {
        if (acc / frames > 0.04) {
          if (GL.fxOn && FXMODE !== 1) GL.fxOn = false;
          else if (GL.pr > 0.5) { GL.pr = GL.pr > 1 ? 1 : GL.pr > 0.75 ? 0.75 : 0.5; sizeGL(); if (GL.pr <= 0.75) GL.r.shadowMap.autoUpdate = false; GL.r.shadowMap.needsUpdate = true; }
        }
        acc = 0; frames = 0;
      }
      var S = GL.active;
      camRestore(S);
      S.update(dt, now / 1000, false);
      camDrift(S, now / 1000);
      draw(S, now / 1000, false);
      projectLabels(S);
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
  var FONT = '"TS Deck Sans", "Noto Sans KR", sans-serif';
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
    var g = new THREE.Group(), fm = PH.plastic(o.frame || 0x17171d, { roughness: 0.26 }), hm = PH.metal(0xc4c9d1, 0.22);
    var lensM = PH.tint(0x9cc4d4, 0.16), lensR = PH.glass();
    if (MDL.specs) {
      var sp = MDL.specs.clone(true); sp.scale.setScalar(2.2 / 0.158); g.add(sp);
      sp.traverse(function (m) {
        if (!m.isMesh) return;
        if (/glass/.test(m.material.name)) { m.material = lensM; m.userData.noShadow = true; var rf = new THREE.Mesh(m.geometry, lensR); rf.renderOrder = 2; m.parent.add(rf); rf.position.copy(m.position); rf.quaternion.copy(m.quaternion); rf.scale.copy(m.scale); rf.userData.noShadow = true; }
        else if (o.frame) m.material = fm;
      });
    } else {
    [-1, 1].forEach(function (s) {
      var sh = rrShape(0.92, 0.66, 0.26), hole = rrShape(0.74, 0.48, 0.18);
      sh.holes.push(new THREE.Path(hole.getPoints(24)));
      var rim = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.05, bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.02, bevelSegments: 2, curveSegments: 10 }), fm);
      rim.position.set(s * 0.55, 0, -0.025); g.add(rim);
      var lg = new THREE.ShapeGeometry(rrShape(0.76, 0.5, 0.19), 10);
      var lens = noSh(new THREE.Mesh(lg, lensM)); lens.position.set(s * 0.55, 0, 0); g.add(lens);
      var lr = noSh(new THREE.Mesh(lg, lensR)); lr.position.set(s * 0.55, 0, 0.004); g.add(lr);
      var hinge = rbox(0.16, s > 0 && o.cam ? 0.2 : 0.14, 0.18, 0.05, s > 0 && o.cam ? fm : hm); hinge.position.set(s * 1.04, 0.12, -0.05); g.add(hinge);
      var temple = rbox(0.07, s > 0 && o.cam ? 0.11 : 0.07, 1.25, 0.03, fm); temple.position.set(s * 1.07, 0.12, -0.7); g.add(temple);
      var tip = rbox(0.07, 0.3, 0.08, 0.03, fm); tip.position.set(s * 1.07, -0.02, -1.3); tip.rotation.x = 0.4; g.add(tip);
    });
    var bridge = new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(V(-0.12, 0.12, 0), V(0, 0.26, 0.02), V(0.12, 0.12, 0)), 12, 0.035, 8), fm); g.add(bridge);
    }
    if (o.cam) {
      var cam = new THREE.Group(); cam.position.set(MDL.specs ? 1.04 : 1.04, MDL.specs ? 0.21 : 0.14, MDL.specs ? 0.0 : 0.05); g.add(cam);
      var bez = cyl(0.075, 0.075, 0.04, PH.metal(0x30343b, 0.3), 24); bez.rotation.x = Math.PI / 2; cam.add(bez);
      var lens2 = sph(0.045, PH.plastic(0x05060a, { roughness: 0.02, clearcoat: 1, clearcoatRoughness: 0 })); lens2.scale.z = 0.5; lens2.position.z = 0.02; cam.add(lens2);
      var spec = blob(0.022, 0, 'rgba(255,255,255,0.95)'); spec.rotation.x = 0; spec.position.set(0.014, 0.016, 0.046); cam.add(spec);
      var ring = new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.008, 8, 32), E(P.amber, 0.5)); ring.position.z = 0.022; cam.add(ring);
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
    var body = rbox(0.9, 1.8, 0.12, 0.18, PH.metal(0x2a2e36, 0.32)); g.add(body);
    var t = tex(256, 512, screen || function (c, w, h) {
      var gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#123c5c'); gr.addColorStop(1, '#081526'); c.fillStyle = gr; rr2d(c, 0, 0, w, h, 34); c.fill();
      c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineWidth = 14; c.lineCap = 'round';
      c.beginPath(); c.moveTo(90, 300); c.lineTo(90, 190); c.moveTo(60, 220); c.lineTo(90, 190); c.lineTo(120, 220); c.stroke();
      c.beginPath(); c.moveTo(166, 200); c.lineTo(166, 310); c.moveTo(136, 280); c.lineTo(166, 310); c.lineTo(196, 280); c.stroke();
      c.fillStyle = 'rgba(255,255,255,.35)'; rr2d(c, 98, 30, 60, 12, 6); c.fill();
    });
    var scr = plane(0.8, 1.68, t); scr.position.z = 0.065; g.add(scr); g.userData.screen = scr; g.userData.tex = t;
    var cover = noSh(new THREE.Mesh(new THREE.ShapeGeometry(rrShape(0.86, 1.76, 0.16), 8), PH.glass({ envMapIntensity: 1.2 }))); cover.position.z = 0.068; g.add(cover);
    var bump = rbox(0.3, 0.3, 0.06, 0.08, PH.plastic(0x101116, { roughness: 0.15 })); bump.position.set(-0.2, 0.62, -0.07); g.add(bump);
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
    var body = sph(0.5 * k, PH.plastic(0xeef0f3, { roughness: 0.2 })); body.scale.set(1, 0.88, 0.9); g.add(body);
    var tip = sph(0.3 * k, M(P.mint, { roughness: 0.7 }), -0.42 * k, 0, 0); tip.scale.set(0.8, 1, 1); g.add(tip);
    var grill = cyl(0.2 * k, 0.2 * k, 0.04, PH.metal(0x9aa1ab, 0.35), 24); grill.rotation.z = Math.PI / 2; grill.position.x = 0.47 * k; g.add(grill);
    var waves = [];
    for (var i = 0; i < 3; i++) { var w = noSh(new THREE.Mesh(new THREE.TorusGeometry((0.75 + i * 0.32) * k, 0.035 * k, 8, 30, Math.PI * 0.6), Bm(P.cool, { transparent: true, opacity: 0 }))); w.rotation.z = -Math.PI * 0.3; w.position.x = -0.35 * k; g.add(w); waves.push(w); }
    g.userData.waves = waves;
    return shadows(g);
  }
  function watchMesh() {
    var g = new THREE.Group();
    var strapM = M(0x1c2236, { roughness: 0.85 });
    var top = rbox(0.62, 1.0, 0.08, 0.04, strapM); top.position.set(0, 0.85, -0.12); top.rotation.x = -0.35; g.add(top);
    var bot = rbox(0.62, 1.0, 0.08, 0.04, strapM); bot.position.set(0, -0.85, -0.12); bot.rotation.x = 0.35; g.add(bot);
    var body = rbox(0.95, 1.1, 0.3, 0.28, PH.metal(0x3a3f48, 0.26)); g.add(body);
    var t = tex(256, 300, function (c, w, h) { c.fillStyle = '#0f1416'; rr2d(c, 0, 0, w, h, 60); c.fill(); c.fillStyle = CSS.acc; c.font = '800 120px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('③', w / 2, h / 2 + 6); });
    var scr = plane(0.78, 0.92, t); scr.position.z = 0.155; g.add(scr);
    var wg2 = noSh(new THREE.Mesh(new THREE.ShapeGeometry(rrShape(0.82, 0.96, 0.24), 8), PH.glass())); wg2.position.z = 0.158; g.add(wg2);
    var crown = cyl(0.07, 0.07, 0.1, PH.metal(0xc4c9d1, 0.25), 16); crown.rotation.z = Math.PI / 2; crown.position.set(0.5, 0.18, 0); g.add(crown);
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

  // 땅: 넓은 풀밭(CC0 PBR) · 멀리는 안개로 사진 배경과 이어져요
  function groundBox(w, d, color, x, z) {
    var has = !!IMG.t_aerial_grass_rock_diff;
    var m = new THREE.Mesh(new THREE.PlaneGeometry(90, 90), M(has ? 0x6c7766 : color, Object.assign({ roughness: 1 }, pbr('aerial_grass_rock', 26, 26))));
    m.rotation.x = -Math.PI / 2; m.position.set(x || 0, -0.002, z || 0); m.receiveShadow = true; return m;
  }
  function fogFor(scene, seg, near, far) { scene.fog = new THREE.Fog(seg === 'hall' ? 0x2a1d26 : seg === 'kitchen' ? 0x2a1810 : 0x2c3a52, near, far); }

  var SCENES = {};

  /* 표지: 공정 카드 여섯 장이 두 줄로 떠 있고, 빛이 기획 → 배포로 지나가요 */
  SCENES.cover = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 100);
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

  /* 「하네스」 한 단어: 글자 셋이 위에서 떨어져 꽂히고 → 충격파·빛 조각 → 빛이 훑고 → 카메라가 다가가 멈춰요 (약 2.6초) */
  function glyphTex(ch, fill) {
    return tex(512, 512, function (c, w, h) {
      if (fill) { var gr = c.createLinearGradient(0, 70, 0, 470); gr.addColorStop(0, '#e9f6ff'); gr.addColorStop(0.55, '#9fd8ea'); gr.addColorStop(1, '#2c8fb0'); c.fillStyle = gr; } else c.fillStyle = '#ffffff';
      c.font = '900 440px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(ch, w / 2, h / 2 + 24);
    });
  }
  SCENES.reveal = function (slideEl) {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(28, 16 / 9, 1.5, 120);
    rig(scene, false, 8, 0, 0);
    fogFor(scene, 'road', 12, 42);
    var fl = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), M(0x262c3a, Object.assign({ roughness: 0.5, metalness: 0.25, envMapIntensity: 0.5 }, pbr('asphalt_02', 24, 24))));
    fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; scene.add(fl);
    var back = new THREE.DirectionalLight(0x22d3ee, 1.4); back.position.set(0, 4, -8); scene.add(back);
    var sweepU = { value: -6 };
    var chars = ['하', '네', '스'], SZ = 2.0, GAP = 1.86, LAY = 18, DEP = 0.013;
    var sideM = [];
    var letters = chars.map(function (ch, i) {
      var g = new THREE.Group(), face = glyphTex(ch, true), mask = glyphTex(ch, false);
      var fm = new THREE.MeshStandardMaterial({ map: face, alphaTest: 0.5, metalness: 0.7, roughness: 0.26, emissive: 0x06303a, emissiveIntensity: 0.35, envMapIntensity: 0.9 });
      var front = new THREE.Mesh(new THREE.PlaneGeometry(SZ, SZ), fm); g.add(front);
      var sm = new THREE.MeshStandardMaterial({ color: 0x14203a, alphaMap: mask, alphaTest: 0.5, transparent: false, metalness: 0.85, roughness: 0.32 });
      sideM.push(sm);
      for (var k = 1; k <= LAY; k++) { var l = new THREE.Mesh(front.geometry, sm); l.position.z = -k * DEP; l.castShadow = k === LAY; g.add(l); }
      var sw = new THREE.Mesh(front.geometry, new THREE.ShaderMaterial({ uniforms: { map: { value: mask }, p: sweepU }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
        vertexShader: 'varying vec2 vUv; varying vec3 vW; void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
        fragmentShader: 'uniform sampler2D map; uniform float p; varying vec2 vUv; varying vec3 vW; void main(){ float a = texture2D(map, vUv).a; float d = vW.x * 0.9 + vW.y * 0.45 - p; float band = exp(-d * d * 5.0); gl_FragColor = vec4(vec3(1.0, 0.97, 0.88) * band * a * 1.5, 1.0); }' }));
      sw.position.z = 0.003; noSh(sw); g.add(sw);
      g.userData.x = (i - 1) * GAP; g.userData.t0 = 0.2 + i * 0.2;
      scene.add(g); return g;
    });
    // 바닥 빛 웅덩이 · 충격파 고리 셋 · 빛 조각
    var pool = blob(3.8, 0, 'rgba(34,211,238,0.14)'); pool.position.y = 0.01; scene.add(pool);
    var rings = [0, 1, 2, 3].map(function () { var r = noSh(new THREE.Mesh(new THREE.RingGeometry(0.92, 1.0, 96), Bm(0x7fe9ff, { transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }))); r.rotation.x = -Math.PI / 2; r.position.y = 0.02; scene.add(r); return r; });
    var NP = 360, ppos = new Float32Array(NP * 3), pv = [], p0 = [];
    for (var k = 0; k < NP; k++) { var a = k * 2.39996, r = (k * 0.618034) % 1; p0.push(V((r - 0.5) * 5.4, 0.05, ((k * 0.3819) % 1 - 0.5) * 0.6)); pv.push(V(Math.cos(a) * (1 + r * 3.2), 1.2 + ((k * 0.7548) % 1) * 4.2, Math.sin(a) * (0.6 + r * 2.4))); }
    var pgeo = new THREE.BufferGeometry(); pgeo.setAttribute('position', new THREE.BufferAttribute(ppos, 3));
    var pmat = new THREE.PointsMaterial({ color: 0xaef4ff, size: 0.06, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0 });
    var pts = noSh(new THREE.Points(pgeo, pmat)); pts.frustumCulled = false; scene.add(pts);
    var L = [lbl('HARNESS', 'hx', V(0, -0.35, 0.6))];
    var Y = SZ / 2 - 0.02, TI = 0.2 + 2 * 0.2 + 0.42;   // 마지막 글자가 닿는 때
    var CA = V(0, 2.4, 17), CB = V(0, 1.15, 9.6), LK = V(0, 0.95, 0);
    var S = { scene: scene, camera: cam, labels: L, age: 0, noDrift: true, lightK: 0.6, fx: { bloom: 0.5, blur: 0.5, r: [0.62, 0.5], vig: 0.5 },
      setStep: function (n, snap) { if (snap) S.age = REDUCED ? 99 : 0; },
      finish: function () { S.age = 99; },
      update: function (dt, t, snap) {
        if (!snap) S.age += dt;
        var A = S.age;
        letters.forEach(function (g, i) {
          var u = Math.max(0, Math.min(1, (A - g.userData.t0) / 0.42)), land = A - g.userData.t0 - 0.42;
          g.visible = A >= g.userData.t0;
          g.position.set(g.userData.x, Y + 7.5 * (1 - u * u), 0);
          g.rotation.set(-(1 - u) * 1.1, (1 - u) * (i - 1) * 0.4, 0);
          var sq = land > 0 ? Math.exp(-land * 9) * Math.cos(land * 26) * 0.14 : 0;
          g.scale.set(1 + sq * 0.5, 1 - sq, 1);
          if (A > 3) g.position.y += Math.sin(t * 1.1 + i * 0.9) * 0.025;
          var rg = rings[i], lt = land;
          rg.position.x = g.userData.x; rg.scale.setScalar(0.4 + Math.max(0, lt) * 3.2); rg.material.opacity = lt > 0 && lt < 0.5 ? (1 - lt / 0.5) * 0.7 : 0;
        });
        var tau = A - TI;
        var big = rings[3]; big.scale.setScalar(0.5 + Math.max(0, tau) * 11); big.material.opacity = tau > 0 && tau < 0.9 ? (1 - tau / 0.9) * 0.9 : 0;
        pool.material.opacity = tau > 0 ? Math.min(1, tau * 3) * (0.75 + 0.6 * Math.exp(-tau * 4)) : 0;
        var tt = Math.max(0, Math.min(tau, 1.8));
        for (var k = 0; k < NP; k++) { var o = p0[k], v = pv[k]; ppos[k * 3] = o.x + v.x * tt; ppos[k * 3 + 1] = Math.max(0.02, o.y + v.y * tt - 3.4 * tt * tt); ppos[k * 3 + 2] = o.z + v.z * tt; }
        pgeo.attributes.position.needsUpdate = true;
        pmat.opacity = tau > 0 && tau < 1.8 ? 1 - tau / 1.8 : 0;
        sweepU.value = -6 + Math.max(0, Math.min(1, (A - 1.3) / 0.9)) * 12;
        S.fx.bloom = 0.5 + (tau > 0 ? 1.3 * Math.exp(-tau * 3) : 0);
        var push = 1 - Math.pow(1 - Math.min(1, A / 2.6), 3);
        cam.position.lerpVectors(CA, CB, push);
        if (tau > 0 && tau < 0.6) { cam.position.x += Math.sin(tau * 70) * 0.05 * Math.exp(-tau * 7); cam.position.y += Math.cos(tau * 63) * 0.04 * Math.exp(-tau * 7); }
        if (A > 2.6 && !snap) cam.position.x += Math.sin((A - 2.6) * 0.25) * 0.5;
        cam.lookAt(LK);
        var h = Math.max(0, Math.min(1, (A - 1.5) / 0.6));
        L[0].el.style.opacity = h; L[0].el.style.letterSpacing = (0.9 - h * 0.45).toFixed(3) + 'em';
      } };
    S.setStep(0, true);
    return S;
  };

  /* ---- 늘 같은 모양이 나오는 난수 (점검 사진이 매번 같게) ---- */
  function rng(seed) { var s = seed || 1; return function () { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }; }
  // 붙는 순간 반짝 고리
  function snapRing(color) {
    return noSh(new THREE.Mesh(new THREE.RingGeometry(0.8, 1.0, 64), Bm(color || P.cool, { transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending })));
  }
  function ringPop(r, pos, age, size) { r.position.copy(pos); r.scale.setScalar(0.05 + Math.min(1, age / 0.5) * (size || 0.6)); r.material.opacity = age >= 0 && age < 0.5 ? (1 - age / 0.5) * 0.9 : 0; }

  /* =====================================================================
     말과 하네스(마구): 힘센 말에 목걸이·뱃대·끄는 줄을 채워 수레를 원하는 쪽으로 끌어요 (안장 아님)
     ===================================================================== */
  // 옆에서 본 말 실루엣 (오른쪽을 봐요). 0~100 좌표 → 0.03배
  var HORSE = [[64, 74], [56, 72], [40, 71], [28, 72], [20, 70], [16, 66], [12, 60], [10, 48], [12, 39], [15, 47], [17, 57], [18, 55], [20, 46], [24, 38], [24, 26], [22, 12], [23, 2], [29, 2], [28, 12], [30, 26], [32, 36],
    [34, 30], [35, 12], [34, 2], [40, 2], [40, 12], [39, 30], [41, 40], [55, 40], [60, 37], [61, 26], [61, 12], [60, 2], [66, 2], [66, 12], [66, 28], [68, 33], [70, 26], [71, 12], [70, 2], [76, 2], [76, 12], [75, 28],
    [74, 42], [76, 52], [78, 60], [84, 69], [90, 75], [96, 71], [101, 73], [102, 79], [97, 88], [93, 96], [92, 101], [90, 105], [88, 99], [85, 97], [78, 89], [70, 81]];
  function horseMesh() {
    var m = modelOf('horse', 3.0);
    if (!m) return horseShape();
    m.updateMatrixWorld(true);
    var H = m.userData.dims.y, head = V(0, 0, 0), chest = V(0, 0, 0), nh = 0, nc = 0, v = V(0, 0, 0);
    m.traverse(function (o) {
      if (!o.isMesh || /base/.test(o.material.name)) return;
      var pa = o.geometry.attributes.position;
      for (var i = 0; i < pa.count; i += 2) { v.fromBufferAttribute(pa, i).applyMatrix4(o.matrixWorld); if (v.y > H * 0.86) { head.add(v); nh++; } else if (v.y > H * 0.5 && v.y < H * 0.64) { chest.add(v); nc++; } }
    });
    head.divideScalar(nh || 1); chest.divideScalar(nc || 1);
    var g = new THREE.Group(), turn = new THREE.Group(); turn.rotation.y = Math.atan2(head.z, head.x); turn.add(m); g.add(turn);
    turn.updateMatrixWorld(true); head.applyAxisAngle(V(0, 1, 0), turn.rotation.y); chest.applyAxisAngle(V(0, 1, 0), turn.rotation.y);
    var dir = head.clone().sub(chest).normalize();
    g.userData = { H: H, head: head, chest: chest, neck: chest.clone().lerp(head, 0.42), dir: dir };
    return shadows(g);
  }
  function horseShape() {
    var g = new THREE.Group(), K = 0.03, D = 0.62;
    var sh = new THREE.Shape(); HORSE.forEach(function (p, i) { if (i) sh.lineTo(p[0] * K, p[1] * K); else sh.moveTo(p[0] * K, p[1] * K); }); sh.closePath();
    var geo = new THREE.ExtrudeGeometry(sh, { depth: D, bevelEnabled: true, bevelThickness: 0.2, bevelSize: 0.09, bevelSegments: 8, curveSegments: 4 });
    geo.translate(-55 * K, 0, -D / 2);
    var body = new THREE.Mesh(geo, PH.metal(0x9a7552, 0.27, { envMapIntensity: 1.4 })); g.add(body);
    [-1, 1].forEach(function (s) { var eye = sph(0.045, PH.plastic(0x0a0806, { roughness: 0.05 })); eye.position.set(93 * K - 55 * K, 89 * K, s * (D / 2 + 0.17)); g.add(eye); });
    // 갈기: 목덜미를 따라 짧은 띠
    var mane = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(64 * K, 75 * K, 0), V(72 * K, 83 * K, 0), V(80 * K, 92 * K, 0), V(86 * K, 99 * K, 0)].map(function (v) { v.x -= 55 * K; return v; })), 20, 0.07, 8), PH.plastic(0x1e140e, { roughness: 0.6, clearcoat: 0.2 }));
    g.add(mane);
    g.userData = { H: 3.1, neck: V(0.7, 2.05, 0), chest: V(0.4, 1.7, 0), dir: V(0.6, 0.8, 0) };
    return shadows(g);
  }
  // 수레 (나무 + 금속 바퀴 테)
  function cartMesh() {
    var g = new THREE.Group(), wood = M(IMG.t_wood_table_001_diff ? 0xe2c9a6 : P.wood, Object.assign({ roughness: 0.7 }, pbr('wood_table_001', 0.6, 0.6))), iron = PH.metal(0x3b3d42, 0.45);
    var bed = rbox(1.9, 1.3, 0.14, 0.05, wood); bed.rotation.x = -Math.PI / 2; bed.position.set(0, 1.0, 0); g.add(bed);
    [[0, 1.25, 0.6, 1.9, 0.36, 0.08], [0, 1.25, -0.6, 1.9, 0.36, 0.08], [-0.92, 1.25, 0, 0.08, 0.36, 1.2]].forEach(function (b) { var m = rbox(b[3], b[4], b[5], 0.03, wood); m.position.set(b[0], b[1], b[2]); g.add(m); });
    var wheels = [-1, 1].map(function (s) {
      var w = new THREE.Group(); w.position.set(-0.1, 0.62, s * 0.78); g.add(w);
      var rim = new THREE.Mesh(new THREE.TorusGeometry(0.58, 0.05, 10, 40), iron); w.add(rim);
      var hub = cyl(0.1, 0.1, 0.16, iron, 16); hub.rotation.x = Math.PI / 2; w.add(hub);
      for (var k = 0; k < 8; k++) { var sp = rbox(0.05, 1.1, 0.05, 0.02, wood); sp.rotation.z = k / 8 * Math.PI; w.add(sp); }
      return w;
    });
    // 끌채 두 개: 수레에서 말 옆구리까지
    [-1, 1].forEach(function (s) { var sf = rbox(2.6, 0.07, 0.07, 0.03, wood); sf.position.set(2.15, 1.12, s * 0.5); sf.rotation.z = 0.06; g.add(sf); });
    g.userData.wheels = wheels;
    return shadows(g);
  }
  SCENES.horse = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 200);
    rig(scene, false, 8, 0, 0);
    scene.add(groundBox(30, 30, P.ground, 0, 0)); fogFor(scene, 'road', 14, 48);
    var rig2 = new THREE.Group(); scene.add(rig2);
    var horse = horseMesh(); horse.position.set(0.5, 0, 0); rig2.add(horse);
    var hd = horse.userData, NK = hd.neck.clone().add(horse.position), CH = hd.chest.clone().add(horse.position);
    var cart = cartMesh(); cart.position.set(-3.3, 0, 0); rig2.add(cart);
    // 하네스 부품: 목걸이(가죽 + 놋쇠) · 가슴띠 · 끄는 줄 둘
    var leather = PH.plastic(0x3a2416, { roughness: 0.42, clearcoat: 0.5 }), brass = PH.metal(0xd4ab52, 0.22);
    var parts = [];
    function part(obj, seat, i) { obj.userData.seat = seat; obj.userData.from = seat.clone().add(V(1.2 - i * 0.5, 2.2 + i * 0.25, 1.8)); obj.userData.snapT = -1; var r = snapRing(0x7fe9ff); scene.add(r); obj.userData.ring = r; parts.push(obj); rig2.add(obj); return obj; }
    var collar = new THREE.Group();
    var c1 = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.065, 14, 40), leather); c1.scale.set(1, 1.3, 1); collar.add(c1);
    var c2 = new THREE.Mesh(new THREE.TorusGeometry(0.29, 0.022, 8, 40), brass); c2.scale.set(1, 1.3, 1); collar.add(c2);
    collar.quaternion.setFromUnitVectors(V(0, 0, 1), hd.dir);
    part(collar, NK, 0);
    var girth = new THREE.Group();
    var gb = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.045, 10, 48), leather); gb.scale.set(1, 1.15, 1); girth.add(gb);
    var buckle = rbox(0.1, 0.14, 0.04, 0.02, brass); buckle.position.set(0, -0.4, 0.02); girth.add(buckle);
    girth.quaternion.setFromUnitVectors(V(0, 0, 1), hd.dir.clone().lerp(V(1, 0, 0), 0.5).normalize());
    part(girth, CH, 1);
    [-1, 1].forEach(function (s2, i) {
      var st = V(0, 0, 0), en = V(-3.3 + 2.05 - NK.x, 1.12 - NK.y, s2 * 0.5);
      var tr = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([st, st.clone().lerp(en, 0.5).add(V(0, -0.35, s2 * 0.05)), en]), 40, 0.028, 8), leather);
      part(tr, NK.clone().add(V(0, -0.05, s2 * 0.12)), 2 + i);
    });
    var arrow = new THREE.Group(); scene.add(arrow);
    var am = Bm(P.cool, { transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
    for (var k = 0; k < 5; k++) { var ch = new THREE.Shape(); ch.moveTo(0, 0.5); ch.lineTo(0.45, 0); ch.lineTo(0, -0.5); ch.lineTo(-0.2, -0.5); ch.lineTo(0.25, 0); ch.lineTo(-0.2, 0.5); ch.closePath(); var m = noSh(new THREE.Mesh(new THREE.ShapeGeometry(ch), am.clone())); m.rotation.x = -Math.PI / 2; m.position.set(3.4 + k * 0.75, 0.03, 0); arrow.add(m); }
    var L = [lbl('힘센 말', 'tag', horse, [0, 3.4, 0]), lbl('하네스(마구) 채우기', 'ck', collar, [0, 0.75, 0]), lbl('원하는 방향으로', 'tag cool', V(5.2, 0.4, 0.4))];
    var S = { scene: scene, camera: cam, labels: L, st: 0, time: 0, f: 0, go: 0, cp: V(6.4, 2.6, 8.4), cl: V(0.4, 1.6, 0), drift: 0.7, fx: { r: [0.55, 0.55], blur: 0.8 },
      setStep: function (n, snap) {
        S.st = n;
        if (snap) { S.f = n >= 1 ? 1 : 0; S.go = n >= 2 ? 1 : 0; parts.forEach(function (p) { p.userData.snapT = n >= 1 ? -9 : -1; }); }
        S.focusObj = n === 1 ? collar : horse;
      },
      update: function (dt, t, snap) {
        if (!snap) S.time += dt;
        S.f += ((S.st >= 1 ? 1 : 0) - S.f) * (snap ? 1 : damp(1.4, dt));
        S.go += ((S.st >= 2 ? 1 : 0) - S.go) * (snap ? 1 : damp(0.7, dt));
        var flash = 0;
        parts.forEach(function (p, i) {
          var d = p.userData, q = ease(Math.max(0, Math.min(1, S.f * 1.5 - i * 0.15)));
          p.position.lerpVectors(d.from, d.seat, q); p.position.y += Math.sin(Math.PI * q) * 0.6;

          if (q > 0.995 && d.snapT === -1) d.snapT = S.time;
          if (q < 0.99 && S.st < 1) d.snapT = -1;
          var age = d.snapT < 0 ? 99 : S.time - d.snapT; flash = Math.max(flash, age < 0.6 ? 1 - age / 0.6 : 0);
          ringPop(d.ring, rig2.localToWorld(d.seat.clone()), age, 0.9); d.ring.lookAt(cam.position);
        });
        var gx = ease(S.go) * 0.9;
        rig2.position.x = gx; rig2.rotation.y = 0.55 * (1 - ease(S.go));
        cart.userData.wheels.forEach(function (w) { w.rotation.z = -gx / 0.58; });
        arrow.children.forEach(function (m, k) { m.material.opacity = S.go * (snap ? 0.7 : 0.35 + 0.45 * Math.max(0, Math.sin(t * 4 - k * 0.9))); });
        if (S.fx) S.fx.bloom = 0.55 + flash * 0.8;
        var tp = S.st === 1 ? V(4.6, 2.9, 5.2) : S.st === 2 ? V(7.2, 2.4, 9.2) : V(6.4, 2.6, 8.4), tl = S.st === 1 ? V(1.6, 1.9, 0) : S.st === 2 ? V(1.4, 1.3, 0) : V(0.4, 1.6, 0);
        var k2 = snap ? 1 : damp(1.2, dt); S.cp.lerp(tp, k2); S.cl.lerp(tl, k2); cam.position.copy(S.cp); cam.lookAt(S.cl);
        L[0].el.style.opacity = S.st === 0 ? 1 : 0; L[1].el.style.opacity = S.st === 1 && S.f > 0.9 ? 1 : 0; L[2].el.style.opacity = S.go > 0.5 ? 1 : 0;
      } };
    S.setStep(0, true);
    return S;
  };

  /* =====================================================================
     김치볶음밥 이야기: 진짜 부엌(CC0 HDRI) · 대리석 조리대 · 웍 · 그릇 · 밥알 · 김치 · 달걀
     harness=false 「그냥 AI」: 레시피·도구 없이 허둥대다 맨밥 → 다시 찾아서 밥과 김치를 따로
     harness=true  「하네스 AI」: 하네스 상자를 열면 셰프 레시피·좋은 재료·전문 도구 → 한 번에 완성
     ===================================================================== */
  function lathe(pts, mat, seg) { return new THREE.Mesh(new THREE.LatheGeometry(pts.map(function (p) { return new THREE.Vector2(p[0], p[1]); }), seg || 48), mat); }
  function bowlMesh() {
    var m = lathe([[0.001, 0], [0.22, 0], [0.24, 0.03], [0.42, 0.2], [0.5, 0.36], [0.48, 0.37], [0.4, 0.22], [0.22, 0.07], [0.001, 0.07]], PH.plastic(0xf3efe6, { roughness: 0.18, side: THREE.DoubleSide }));
    return shadows(m);
  }
  function plateMesh(r) { r = r || 0.75; return shadows(lathe([[0.001, 0], [r * 0.7, 0], [r * 0.74, 0.02], [r, 0.08], [r * 0.98, 0.1], [r * 0.7, 0.045], [0.001, 0.045]], PH.plastic(0xf7f4ee, { roughness: 0.15, side: THREE.DoubleSide }), 64)); }
  // 밥 무더기: 낟알 하나하나 (instanced). tint: 함수(rand)→색
  function riceMound(n, R, H, tint, seed) {
    var r = rng(seed || 7), geo = new THREE.SphereGeometry(0.028, 6, 4), mat = PH.plastic(0xffffff, { roughness: 0.35, clearcoat: 0.4 });
    var im = new THREE.InstancedMesh(geo, mat, n), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = V(1, 0.55, 0.55), p = V(0, 0, 0), c = new THREE.Color();
    for (var i = 0; i < n; i++) {
      var rr = R * Math.sqrt(r()), a = r() * Math.PI * 2, y = H * (1 - Math.pow(rr / R, 2)) * (0.85 + r() * 0.2);
      p.set(Math.cos(a) * rr, y, Math.sin(a) * rr); e.set(r() * 3, r() * 3, r() * 3); q.setFromEuler(e); m4.compose(p, q, s); im.setMatrixAt(i, m4);
      c.setHex(tint ? tint(r) : 0xfbf8f0); im.setColorAt(i, c);
    }
    im.castShadow = true; im.receiveShadow = true;
    return im;
  }
  function kimchiPieces(n, R, H, seed) {
    var r = rng(seed || 11), geo = new THREE.BoxGeometry(0.16, 0.018, 0.1), mat = PH.plastic(0xffffff, { roughness: 0.3, clearcoat: 0.7 });
    var im = new THREE.InstancedMesh(geo, mat, n), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = V(1, 1, 1), p = V(0, 0, 0), c = new THREE.Color();
    var cols = [0xc8361f, 0xd9502d, 0xb52a18, 0xe46a3a, 0xf1e2b8];
    for (var i = 0; i < n; i++) {
      var rr = R * Math.sqrt(r()), a = r() * Math.PI * 2, y = H * (1 - Math.pow(rr / R, 2)) + 0.01;
      p.set(Math.cos(a) * rr, y, Math.sin(a) * rr); e.set((r() - 0.5) * 1.2, r() * 6, (r() - 0.5) * 1.2); q.setFromEuler(e); s.set(0.6 + r() * 0.8, 1, 0.6 + r() * 0.7); m4.compose(p, q, s); im.setMatrixAt(i, m4);
      c.setHex(cols[Math.floor(r() * (i % 9 === 0 ? 5 : 4))]); im.setColorAt(i, c);
    }
    im.castShadow = true;
    return im;
  }
  function eggMesh() {
    var g = new THREE.Group(), r = rng(5), sh = new THREE.Shape();
    for (var i = 0; i <= 24; i++) { var a = i / 24 * Math.PI * 2, rr = 0.3 * (0.88 + r() * 0.2); if (i) sh.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); else sh.moveTo(Math.cos(a) * rr, Math.sin(a) * rr); }
    var white = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.02, bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.03, bevelSegments: 3 }), PH.plastic(0xfdfbf4, { roughness: 0.25 }));
    white.rotation.x = -Math.PI / 2; g.add(white);
    var yolk = sph(0.11, PH.plastic(0xffa514, { roughness: 0.12, clearcoat: 1 })); yolk.scale.y = 0.55; yolk.position.set(0.03, 0.05, -0.02); g.add(yolk);
    return shadows(g);
  }
  function friedRice() {
    var g = new THREE.Group();
    var rice = riceMound(900, 0.58, 0.36, function (r) { var k = r(); return k < 0.55 ? 0xe2552c : k < 0.8 ? 0xf07a3a : k < 0.93 ? 0xc93a1f : 0xf6e7c8; }, 21); g.add(rice);
    var kim = kimchiPieces(40, 0.5, 0.34, 23); g.add(kim);
    var egg = eggMesh(); egg.position.set(0, 0.36, 0); egg.rotation.y = 0.4; g.add(egg);
    var r = rng(31), seedM = PH.plastic(0xf6e9c8, { roughness: 0.4 }), onionM = PH.plastic(0x4caf50, { roughness: 0.4 });
    for (var i = 0; i < 26; i++) { var a = r() * 6.28, rr = 0.1 + r() * 0.4, y = 0.36 * (1 - Math.pow(rr / 0.58, 2)) + 0.02; var sd = sph(0.012, i % 3 ? seedM : onionM); sd.scale.set(i % 3 ? 1.6 : 2.4, 0.7, 1); sd.position.set(Math.cos(a) * rr, y + (rr < 0.3 ? 0.06 : 0), Math.sin(a) * rr); g.add(sd); }
    return g;
  }
  function wokMesh() {
    var g = new THREE.Group();
    var pts = []; for (var i = 0; i <= 16; i++) { var a = i / 16 * Math.PI * 0.5; pts.push([Math.sin(a) * 0.95 + 0.001, 0.4 - Math.cos(a) * 0.4]); }
    var bowl = lathe(pts, PH.metal(0x2b2b30, 0.42, { side: THREE.DoubleSide }), 64); g.add(bowl);
    var lip = new THREE.Mesh(new THREE.TorusGeometry(0.95, 0.025, 8, 64), PH.metal(0x3a3a40, 0.35)); lip.rotation.x = Math.PI / 2; lip.position.y = 0.4; g.add(lip);
    var h = cyl(0.045, 0.05, 1.0, M(IMG.t_wood_table_001_diff ? 0xd9b48a : P.wood, Object.assign({ roughness: 0.6 }, pbr('wood_table_001', 0.2, 0.2))), 12); h.rotation.z = Math.PI / 2; h.position.set(1.4, 0.42, 0); g.add(h);
    var hm = cyl(0.03, 0.03, 0.25, PH.metal(0x55555c, 0.3), 10); hm.rotation.z = Math.PI / 2; hm.position.set(0.98, 0.41, 0); g.add(hm);
    return shadows(g);
  }
  function chefAI() {
    var g = new THREE.Group(), body = cloudMesh(true); body.scale.setScalar(0.42); g.add(body);
    var hatM = PH.plastic(0xffffff, { roughness: 0.6, clearcoat: 0.1 });
    var band = cyl(0.3, 0.3, 0.26, hatM, 32); band.position.set(0.05, 0.62, -0.05); g.add(band);
    [[-0.17, 0.85, 0], [0.17, 0.86, 0], [0, 0.92, 0.12], [0, 0.9, -0.15], [0.05, 0.98, 0]].forEach(function (p) { var s = sph(0.2, hatM, p[0] + 0.05, p[1], p[2] - 0.05); g.add(s); });
    var hands = [-1, 1].map(function (s) { var h = sph(0.11, PH.plastic(0xf3ebe0, { roughness: 0.5 })); h.position.set(s * 0.72, -0.15, 0.35); g.add(h); return h; });
    var spat = new THREE.Group(); spat.add(new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.015, 0.16), PH.metal(0xc9ced6, 0.25))); var sh2 = cyl(0.02, 0.02, 0.5, M(0x3a2a1e), 8); sh2.rotation.x = Math.PI / 2; sh2.position.z = 0.32; spat.add(sh2);
    spat.position.set(0, -0.05, 0.08); hands[1].add(spat); spat.rotation.set(0.6, 0, 0);
    g.userData = { body: body, hands: hands, spat: spat, star: body.userData.star };
    return shadows(g);
  }
  // 하네스 상자: 유리 뚜껑 + 금속 틀 (열리면 안에서 빛)
  function harnessCase() {
    var g = new THREE.Group(), frame = PH.metal(0xb7bec9, 0.3);
    var base = rbox(1.5, 0.36, 1.0, 0.08, PH.plastic(0x10202a, { roughness: 0.3 })); base.position.y = 0.18; g.add(base);
    var rim = rbox(1.56, 0.06, 1.06, 0.03, frame); rim.position.y = 0.37; g.add(rim);
    var lid = new THREE.Group(); lid.position.set(0, 0.4, -0.5); g.add(lid);
    var lp = rbox(1.5, 0.08, 1.0, 0.05, PH.tint(0x9fe8f5, 0.35)); lp.position.set(0, 0, 0.5); lid.add(lp);
    var lr = rbox(1.56, 0.04, 1.06, 0.03, PH.glass()); lr.position.set(0, 0.03, 0.5); lid.add(lr);
    var glow = blob(0.9, 0, 'rgba(34,211,238,0.85)'); glow.position.y = 0.42; g.add(glow);
    var t = tex(512, 128, function (c, w, h) { c.fillStyle = '#22d3ee'; c.font = '900 64px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('하네스', w / 2, h / 2 + 4); });
    var lab = plane(0.9, 0.22, t); lab.position.set(0, 0.2, 0.505); g.add(lab);
    g.userData = { lid: lid, glow: glow };
    return shadows(g);
  }
  function recipeCard() {
    var t = tex(360, 480, function (c, w, h) {
      c.fillStyle = '#fffaf0'; rr2d(c, 0, 0, w, h, 26); c.fill(); if (IMG.t_paper_diff) { c.globalAlpha = 0.5; c.drawImage(IMG.t_paper_diff, 0, 0, w, h); c.globalAlpha = 1; }
      c.fillStyle = '#b4321c'; c.font = '900 40px ' + FONT; c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText('셰프 레시피', 28, 26);
      c.fillStyle = '#2b2019'; c.font = '800 28px ' + FONT; c.fillText('김치볶음밥', 28, 82);
      c.fillStyle = '#8b7a66'; for (var i = 0; i < 6; i++) { c.fillRect(28, 140 + i * 50, i % 2 ? 240 : 290, 12); c.fillStyle = i % 2 ? '#8b7a66' : '#c9a24a'; }
      c.fillStyle = '#c9a24a'; c.beginPath(); c.arc(w - 60, h - 60, 30, 0, 7); c.fill();
    });
    var g = new THREE.Group(); var p = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.8), M(0xffffff, { map: t, roughness: 0.8, side: THREE.DoubleSide })); g.add(p);
    return shadows(g);
  }
  function jarMesh() {
    var g = new THREE.Group();
    var glass = lathe([[0.001, 0], [0.28, 0], [0.3, 0.04], [0.3, 0.5], [0.24, 0.58], [0.24, 0.64], [0.001, 0.64]], PH.tint(0xd8f0f0, 0.25)); g.add(glass);
    var refl = lathe([[0.001, 0], [0.285, 0], [0.305, 0.04], [0.305, 0.5], [0.245, 0.58], [0.245, 0.64]], PH.glass()); g.add(refl);
    var fill = kimchiPieces(60, 0.26, 0.42, 41); fill.position.y = 0.04; g.add(fill);
    var cap = cyl(0.26, 0.26, 0.08, PH.metal(0xc9a24a, 0.3), 32); cap.position.y = 0.68; g.add(cap);
    return shadows(g);
  }
  function buildKitchen(harness) {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 100);
    rig(scene, true, 6, 0, 0);
    scene.fog = new THREE.Fog(0x2a1810, 14, 30);
    var warm = new THREE.PointLight(0xff8a3d, 0, 5, 2); warm.position.set(-1.3, 1.4, 0.2); scene.add(warm);
    // 조리대: 대리석 상판 + 어두운 나무 몸통
    var top = rbox(10, 3.4, 0.14, 0.05, M(IMG.t_marble_01_diff ? 0x8a847c : 0x6e6a64, Object.assign({ roughness: 0.32, envMapIntensity: 0.6 }, pbr('marble_01', 0.35, 0.35)))); top.rotation.x = -Math.PI / 2; top.position.set(0, -0.07, 0); top.receiveShadow = true; scene.add(top);
    var cab = rbox(10, 2.2, 3.2, 0.04, M(0x2a1c14, Object.assign({ roughness: 0.6 }, pbr('wood_table_001', 0.5, 0.5)))); cab.position.set(0, -1.25, -0.05); scene.add(cab);
    // 화구: 검은 유리판 + 불 고리
    var hob = rbox(1.9, 1.5, 0.03, 0.06, PH.plastic(0x060608, { roughness: 0.05, clearcoat: 1 })); hob.rotation.x = -Math.PI / 2; hob.position.set(-1.3, 0.016, 0.0); scene.add(hob);
    var fire = noSh(new THREE.Mesh(new THREE.RingGeometry(0.42, 0.5, 48), Bm(0xff6a1f, { transparent: true, opacity: 0.15, blending: THREE.AdditiveBlending, depthWrite: false }))); fire.rotation.x = -Math.PI / 2; fire.position.set(-1.3, 0.035, 0.0); scene.add(fire);
    var wok = wokMesh(); wok.position.set(-1.3, 0.05, 0.0); wok.scale.setScalar(0.62); scene.add(wok);
    var chef = chefAI(); chef.position.set(0.1, 0.85, -1.2); scene.add(chef);
    var serve = V(1.55, 0.0, 0.75);
    var bowl = bowlMesh(); var plainRice = riceMound(380, 0.38, 0.2, null, 3); plainRice.position.y = 0.2; bowl.add(plainRice); scene.add(bowl);
    var side = plateMesh(0.42); var sideK = kimchiPieces(34, 0.3, 0.12, 9); sideK.position.y = 0.05; side.add(sideK); scene.add(side);
    var plate = plateMesh(0.8), fr = friedRice(); fr.position.y = 0.05; plate.add(fr); scene.add(plate);
    var wokRice = riceMound(260, 0.4, 0.12, function (r) { return harness ? (r() < 0.7 ? 0xe2552c : 0xf6e7c8) : 0xfbf8f0; }, 13); wokRice.position.set(0, 0.06, 0); wok.add(wokRice);
    var toss = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: harness ? 0xf07a3a : 0xffffff, size: 0.05, map: dotTex(), transparent: true, depthWrite: false }));
    var NT = 80, tpos = new Float32Array(NT * 3); toss.geometry.setAttribute('position', new THREE.BufferAttribute(tpos, 3)); toss.frustumCulled = false; noSh(toss); scene.add(toss);
    var steam = [0, 1, 2, 3].map(function (i) { var b = blob(0.35, 0, 'rgba(255,255,255,0.22)'); b.rotation.x = 0; scene.add(b); return b; });
    var sparkle = [0, 1, 2, 3, 4, 5].map(function (i) { var b = blob(0.12, 0, 'rgba(255,240,200,0.95)'); b.rotation.x = 0; scene.add(b); return b; });
    var L = [lbl('「김치볶음밥 해 줘」', 'say user', V(-3.3, 2.3, 0.6))];
    var items = [], hcase = null, recipe = null, jar = null, egg = null, spatPro = null;
    if (harness) {
      hcase = harnessCase(); hcase.position.set(2.6, 0, -0.55); scene.add(hcase);
      recipe = recipeCard(); jar = jarMesh(); egg = eggMesh(); spatPro = new THREE.Group();
      var sb = rbox(0.34, 0.02, 0.26, 0.02, PH.metal(0xd9dde3, 0.18)); spatPro.add(sb); var sh3 = cyl(0.025, 0.025, 0.7, PH.metal(0x9aa1ab, 0.25), 10); sh3.rotation.x = Math.PI / 2; sh3.position.z = 0.45; spatPro.add(sh3); shadows(spatPro);
      [[recipe, V(3.3, 1.35, 0.1), V(0, -0.35, 0.1)], [jar, V(1.9, 0.0, -0.9), V(0, 0, 0)], [egg, V(3.6, 0.0, 0.7), V(0, 0, 0)], [spatPro, V(2.4, 0.03, 0.75), V(0, 0.9, 0)]].forEach(function (d, i) {
        var o = d[0]; o.userData.seat = d[1]; o.userData.rot = d[2]; o.userData.snapT = -1; var r = snapRing(0x7fe9ff); scene.add(r); o.userData.ring = r; scene.add(o); items.push(o);
      });
      L.push(lbl('셰프 레시피', 'tag cool', recipe, [0, 0.62, 0]), lbl('좋은 재료', 'tag cool', jar, [0, 0.95, 0]), lbl('전문 도구', 'tag cool', spatPro, [0, 0.3, 0.3]), lbl('한 번에 완성 ✓', 'ck', plate, [0, 1.1, 0]));
    } else {
      L.push(lbl('레시피도, 도구도 없어요…', 'think', chef, [0, 1.35, 0]), lbl('「김치 왜 안 넣었어?」', 'say user', V(-3.3, 2.3, 0.6)), lbl('레시피 검색 중…', 'think', chef, [0, 1.35, 0]), lbl('「…따로 주면 어떡해」', 'say user bad', V(-3.3, 2.3, 0.6)));
    }
    var CAM = harness
      ? [[V(0.6, 3.0, 9.0), V(0.4, 0.8, -0.3)], [V(2.4, 2.6, 6.6), V(2.4, 0.6, -0.4)], [V(-0.4, 2.5, 6.4), V(-1.0, 0.7, -0.2)], [V(1.4, 2.3, 6.0), V(1.5, 0.45, 0.6)]]
      : [[V(0.6, 3.0, 9.0), V(0.4, 0.8, -0.3)], [V(0.0, 2.7, 7.0), V(-0.3, 1.0, -0.6)], [V(1.2, 2.4, 6.2), V(1.4, 0.5, 0.5)], [V(0.2, 2.7, 7.0), V(0.1, 1.0, -0.5)], [V(1.0, 2.5, 6.4), V(1.3, 0.45, 0.5)]];
    var S = { scene: scene, camera: cam, labels: L, st: 0, time: 0, a: 0, cp: CAM[0][0].clone(), cl: CAM[0][1].clone(), drift: 0.5, lightK: 0.45, fx: { r: [0.5, 0.5], blur: 0.9 },
      setStep: function (n, snap) {
        S.st = n; if (n !== S.lastN) { S.a = snap ? 9 : 0; S.lastN = n; }
        if (snap) { S.a = 9; items.forEach(function (o) { o.userData.snapT = n >= 1 ? -9 : -1; }); }
        S.focusObj = harness ? [null, hcase, wok, plate][n] : [null, chef, bowl, chef, bowl][n];
      },
      update: function (dt, t, snap) {
        if (!snap) { S.time += dt; S.a += dt; }
        var n = S.st, A = S.a, cm = CAM[Math.min(n, CAM.length - 1)];
        var k = snap ? 1 : damp(1.4, dt); S.cp.lerp(cm[0], k); S.cl.lerp(cm[1], k); cam.position.copy(S.cp); cam.lookAt(S.cl);
        var U = chef.userData, live = !snap;
        // 셰프 AI 기본 둥실
        chef.position.y = 0.85 + (live ? Math.sin(t * 1.4) * 0.05 : 0); chef.rotation.set(0, 0, 0);
        U.star.rotation.z = live ? t * 0.8 : 0.3;
        U.hands[0].position.set(-0.72, -0.15, 0.35); U.hands[1].position.set(0.72, -0.15, 0.35);
        var cooking = false, fumble = false;
        bowl.visible = side.visible = plate.visible = false;
        if (!harness) {
          fumble = n === 1 || n === 3;
          if (fumble && live) { chef.rotation.z = Math.sin(t * 13) * 0.12; chef.position.x = 0.1 + Math.sin(t * 9) * 0.08; U.hands[0].position.y += Math.sin(t * 15) * 0.12; U.hands[1].position.y += Math.cos(t * 13) * 0.12; } else chef.position.x = 0.1;
          bowl.visible = n >= 2; side.visible = n >= 4 || n === 3;
          var bq = ease(Math.min(1, n === 2 ? A / 0.8 : 1));
          bowl.position.set(serve.x - (n >= 4 ? 0.55 : 0), 0.0 + (1 - bq) * 0.6, serve.z); bowl.rotation.y = 0.3;
          var sq = ease(Math.min(1, (n === 3 ? A / 0.9 : 1)));
          side.position.set(n >= 4 ? serve.x + 0.55 : 0.6 + (1 - sq) * 0.4, (1 - sq) * 1.2, n >= 4 ? serve.z + 0.15 : -0.5);
          wokRice.visible = false;
          L[1].el.style.opacity = n === 1 ? 1 : 0; L[2].el.style.opacity = n === 2 ? 1 : 0; L[3].el.style.opacity = n === 3 ? 1 : 0; L[4].el.style.opacity = n === 4 ? 1 : 0;
          L[0].el.style.opacity = n === 0 || n === 1 ? 1 : 0;
          if (S.fx) S.fx.bloom = 0.5;
        } else {
          var lidOpen = n >= 1 ? ease(Math.min(1, n === 1 ? A / 0.8 : 1)) : 0;
          hcase.userData.lid.rotation.x = -lidOpen * 1.9; hcase.userData.glow.material.opacity = lidOpen * (n === 1 ? 1 : 0.5); face(hcase.userData.glow, cam);
          var flash = 0;
          items.forEach(function (o, i) {
            var d = o.userData, q = n >= 1 ? ease(Math.max(0, Math.min(1, (n === 1 && !snap ? (A - 0.5 - i * 0.22) / 0.7 : 1)))) : 0;
            var from = V(hcase.position.x, 0.5, hcase.position.z);
            o.visible = q > 0.01;
            o.position.lerpVectors(from, d.seat, q); o.position.y += Math.sin(Math.PI * q) * 1.0;
            o.rotation.set(d.rot.x, d.rot.y + (1 - q) * 3, d.rot.z); o.scale.setScalar(0.2 + 0.8 * q);
            if (q > 0.995 && d.snapT === -1) d.snapT = S.time;
            if (n < 1) d.snapT = -1;
            var age = d.snapT < 0 ? 99 : S.time - d.snapT; flash = Math.max(flash, age < 0.6 ? 1 - age / 0.6 : 0);
            ringPop(d.ring, d.seat, age, 0.6); d.ring.rotation.x = -Math.PI / 2;
          });
          if (recipe && live) recipe.rotation.y = d0(recipe) + Math.sin(t * 0.8) * 0.12;
          cooking = n === 2;
          wokRice.visible = n === 2;
          plate.visible = n >= 3;
          var pq = ease(Math.min(1, n === 3 ? A / 0.9 : 1));
          plate.position.set(serve.x, (1 - pq) * 0.8, serve.z); plate.rotation.y = 0.5 + (1 - pq) * 1.2;
          if (cooking && live) { U.hands[1].position.set(-0.9 + Math.sin(t * 6) * 0.15, -0.5, 0.75); U.hands[0].position.set(-1.3, -0.55, 0.3); }
          sparkle.forEach(function (b, i) { var a2 = i / 6 * Math.PI * 2 + t * 0.6; b.position.set(serve.x + Math.cos(a2) * 0.9, 0.55 + Math.sin(t * 2 + i) * 0.15, serve.z + Math.sin(a2) * 0.5); b.material.opacity = n >= 3 ? (snap ? 0.8 : 0.5 + 0.5 * Math.sin(t * 5 + i * 1.3)) : 0; face(b, cam); });
          L[0].el.style.opacity = n === 0 ? 1 : 0;
          [1, 2, 3].forEach(function (j) { L[j].el.style.opacity = n === 1 || n === 2 ? 1 : 0; }); L[4].el.style.opacity = n >= 3 ? 1 : 0;
          if (S.fx) S.fx.bloom = 0.55 + flash * 0.7 + (n >= 3 ? 0.25 : 0);
        }
        // 불 · 웍 흔들기 · 밥알 튀기 · 김
        fire.material.opacity = cooking ? (live ? 0.75 + Math.sin(t * 20) * 0.15 : 0.8) : 0.12;
        warm.intensity = cooking ? 2.2 : 0;
        wok.rotation.z = cooking && live ? Math.sin(t * 6) * 0.08 : 0; wok.position.x = -1.3 + (cooking && live ? Math.sin(t * 6) * 0.05 : 0);
        for (var i = 0; i < NT; i++) {
          var ph = ((live ? t * 1.6 : 0.4) + i / NT) % 1, ang = i * 2.39996, sp2 = 0.3 + (i % 7) / 14;
          tpos[i * 3] = -1.3 + Math.cos(ang) * sp2 * ph * 0.9; tpos[i * 3 + 1] = cooking ? 0.25 + ph * 1.8 - ph * ph * 2.0 : -9; tpos[i * 3 + 2] = Math.sin(ang) * sp2 * ph * 0.5;
        }
        toss.geometry.attributes.position.needsUpdate = true;
        steam.forEach(function (b, i) { var ph = ((live ? t * 0.35 : 0.3) + i / 4) % 1; b.position.set(-1.3 + Math.sin(i * 2 + ph * 3) * 0.2, 0.4 + ph * 1.4, 0); b.scale.setScalar(0.6 + ph * 1.2); b.material.opacity = (cooking || (harness && n >= 3)) ? (1 - ph) * 0.9 : 0; face(b, cam); });
      } };
    function d0(o) { return o.userData.rot.y; }
    S.setStep(0, true);
    return S;
  }
  SCENES.kitchenA = function () { return buildKitchen(false); };
  SCENES.kitchenB = function () { return buildKitchen(true); };

  /* 어두운 구간 공통 바닥 */
  function darkFloor(scene, w, d, y) { var f = rbox(w, d, 0.3, 0.2, M(0x2a2019, { roughness: 0.95 })); f.rotation.x = -Math.PI / 2; f.position.y = (y || 0) - 0.15; f.receiveShadow = true; scene.add(f); return f; }

  /* 평소 AI 쓰기 vs 부정행위 · 가운데 AI는 그대로, 입구와 출구만 바뀌어요 (recap=true면 마무리 그림) */
  function buildSwap(slideEl, recap) {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 100);
    rig(scene, true, 10, 0, 0);
    var Y0 = 1.55, Y1 = -1.15, XI = -4.4, XO = 4.4;
    var sh = catcher(22, 12, 0.22); sh.position.y = -3.2; scene.add(sh);
    function rowBase(y, op) { var b = rbox(12.4, 2.2, 0.12, 0.06, M(IMG.t_wood_table_001_diff ? 0xd8c2a8 : P.dk2, Object.assign({ roughness: 0.72, transparent: true, opacity: op }, pbr('wood_table_001', 0.5, 0.5)))); b.rotation.x = -Math.PI / 2; b.position.set(0, y - 0.72, -0.2); b.receiveShadow = true; scene.add(b); return b; }
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
    var wood = M(IMG.t_wood_table_001_diff ? 0xffffff : P.wood, Object.assign({ roughness: 0.75 }, pbr('wood_table_001', 1.4, 1.4))), metal = PH.metal(0x8a9099, 0.4);
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
      c.fillStyle = '#fffcf6'; c.fillRect(0, 0, w, h); if (IMG.t_paper_diff) { c.globalAlpha = 0.9; c.drawImage(IMG.t_paper_diff, 0, 0, w, h); c.globalAlpha = 1; } c.fillStyle = '#2b2019'; c.font = '800 30px ' + FONT; c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText('시험지', 24, 18);
      for (var i = 0; i < 5; i++) { var y = 74 + i * 66; c.fillStyle = i === 2 ? 'rgba(245,158,11,.45)' : 'rgba(0,0,0,0)'; c.fillRect(12, y - 8, w - 24, 58); c.fillStyle = '#2b2019'; c.font = '800 24px ' + FONT; c.fillText((i + 1) + '.', 22, y); c.fillStyle = '#b3a08a'; c.fillRect(60, y + 6, 200 - i * 12, 9); c.fillRect(60, y + 26, 150, 9); }
    });
    var paperHl = tex(300, 420, function (c, w, h) { c.strokeStyle = '#f2a65a'; c.lineWidth = 8; rr2d(c, 10, 74 + 2 * 66 - 10, w - 20, 62, 12); c.stroke(); });
    var paper = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 0.42), M(0xffffff, { map: paperT, roughness: 0.9 })); paper.rotation.x = -Math.PI / 2; paper.position.set(-0.04, 0.799, 0.5); paper.receiveShadow = true; g.add(paper);
    var hl = plane(0.3, 0.42, paperHl, { opacity: 0 }); hl.rotation.x = -Math.PI / 2; hl.position.set(-0.04, 0.801, 0.5); g.add(hl);
    g.userData = { phone: phone, head: head, glasses: gls, bud: bud, pen: pen, paperHl: hl, paper: paper };
    return shadows(g);
  }
  // 가까운 무선: 작은 점들이 이어진 짧은 길 (청록)
  function beads(curve, gap, color) {
    var L = curve.getLength(), n = Math.max(4, Math.floor(L / gap)), pos = new Float32Array(n * 3);
    for (var i = 0; i < n; i++) { var p = curve.getPointAt(i / (n - 1)); pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z; }
    var g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    return noSh(new THREE.Points(g, new THREE.PointsMaterial({ color: color, size: 0.03, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })));
  }
  var _dot;
  function dotTex() { if (!_dot) _dot = tex(64, 64, function (c) { var gr = c.createRadialGradient(32, 32, 1, 32, 32, 30); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,.85)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); c.fillStyle = gr; c.fillRect(0, 0, 64, 64); }); return _dot; }
  // 휴대폰 인터넷: 굵은 끊긴 선이 멀리 흘러가요 (호박색)
  function dashTube(curve, r, color) {
    var t = tex(64, 8, function (c) { c.fillStyle = '#fff'; c.fillRect(0, 0, 38, 8); });
    t.wrapS = THREE.RepeatWrapping; t.repeat.set(Math.max(2, curve.getLength() / 0.16), 1);
    return noSh(new THREE.Mesh(new THREE.TubeGeometry(curve, 120, r, 8, false), Bm(color, { map: t, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending })));
  }
  // 나무 바닥 (학교 강당 바닥처럼, CC0 PBR)
  function woodFloor(size, tint) {
    var m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), M(IMG.t_wood_table_001_diff ? tint : 0x2a2019, Object.assign({ roughness: 0.62 }, pbr('wood_table_001', size / 2.2, size / 2.2))));
    m.rotation.x = -Math.PI / 2; m.position.y = -0.001; m.receiveShadow = true; return m;
  }
  // 나무 책상 판 (상판 위가 y=0)
  function woodTop(w, d, tint) {
    var m = rbox(w, d, 0.12, 0.05, M(IMG.t_wood_table_001_diff ? (tint || 0xffffff) : P.dk2, Object.assign({ roughness: 0.7 }, pbr('wood_table_001', 0.5, 0.5))));
    m.rotation.x = -Math.PI / 2; m.position.y = -0.06; m.receiveShadow = true; return m;
  }
  SCENES.story = function (slideEl) {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.12, 60);
    fogFor(scene, 'hall', 7, 26);
    var key = rig(scene, true, 3, 0, 0.2);
    key.position.set(3, 6, 4);
    scene.add(woodFloor(40, 0x9a7a5c));
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
    var tubes = curves.map(function (c, i) { var m = (i === 0 || i === 3) ? beads(c, 0.022, P.cool) : dashTube(c, 0.016, P.amber); m.material.opacity = 0; scene.add(m); return m; });
    var pulse = pulseMesh(0.028, P.cool), pulseNet = pulseMesh(0.028, P.amber); scene.add(pulse); scene.add(pulseNet);
    var photo = plane(0.18, 0.155, photoTex()); scene.add(photo);
    var bubble = plane(0.2, 0.156, bubbleTex()); scene.add(bubble);
    var flash = blob(0.25, 0, 'rgba(255,240,210,0.9)'); flash.rotation.x = 0; scene.add(flash);
    var phGlow = blob(0.2, 0, 'rgba(34,211,238,0.8)'); phGlow.rotation.x = 0; phGlow.position.copy(phPt); scene.add(phGlow);
    var thinking = [0, 1, 2].map(function (i) { var d = noSh(sph(0.12, Bm(P.amber, { transparent: true, opacity: 0 }))); d.position.set(clPt.x - 0.26 + i * 0.26, clPt.y - 0.85, clPt.z + 0.7); d.scale.setScalar(0.55); scene.add(d); return d; });
    var L = [lbl('안경 카메라', 'tag cool', U.glasses.userData.cam, [0.16, 0.05, 0]), lbl('주머니 속 휴대폰', 'tag cool', U.phone, [0.2, -0.05, 0]),
      lbl('멀리 있는 AI', 'tag ai', cloud, [0, 1.05, 0]), lbl('귀 속 이어폰', 'tag cool', U.bud, [0.17, -0.04, 0]),
      lbl('<i class="hop1"></i>가까운 무선', 'tag hop cool', c1.getPointAt(0.5), [-0.2, 0, 0.05]), lbl('<i class="hop2"></i>휴대폰 인터넷', 'tag hop ai', c2.getPointAt(0.5), [0, 0.22, 0])];
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
        tubes[1].material.map.offset.x -= snap ? 0 : dt * 1.6; tubes[2].material.map.offset.x -= snap ? 0 : dt * 1.6;
        photo.visible = n === 2 || n === 3; bubble.visible = n === 5 || n === 6;
        var net = travel === 1 || travel === 2; pulse.visible = travel !== undefined && !net; pulseNet.visible = travel !== undefined && net;
        if (net) { pulse.position.copy(curves[travel].getPointAt(Math.min(1, pp))); }
        if (travel !== undefined) {
          var pos = curves[travel].getPointAt(Math.min(1, pp));
          pulse.position.copy(pos); face(pulse.userData.halo, cam);
          var far = travel === 1 || travel === 2;
          var sc = far ? 1 + Math.sin(Math.PI * Math.min(1, pp)) * 1.6 + (travel === 1 ? pp * 1.4 : (1 - pp) * 1.4) : 1;
          var item = photo.visible ? photo : bubble;
          item.position.copy(pos).add(V(0, far ? 0.12 * sc : 0.06, 0)); item.scale.setScalar(sc); face(item, cam);
          pulse.scale.setScalar(far ? sc : 1); pulseNet.position.copy(pulse.position); pulseNet.scale.copy(pulse.scale); face(pulseNet.userData.halo, cam);
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
        var showL = [[1, 1, 1, 1, 0, 0], [0, 0, 0, 0, 0, 0], [1, 1, 0, 0, 1, 0], [0, 1, 1, 0, 0, 1], [0, 0, 1, 0, 0, 0], [0, 1, 1, 0, 0, 1], [0, 1, 0, 1, 1, 0], [0, 0, 0, 0, 0, 0]][n];
        S.focusObj = n === 4 ? cloud : (n === 0 || n === 3 || n === 5 || n === 7) ? null : U.head;
        if (S.fx) { S.fx.r = S.focusObj ? [0.3, 0.42] : [0.62, 0.6]; S.fx.blur = S.focusObj ? 1.0 : 0.6; }
        L.forEach(function (l, i) { l.el.style.opacity = showL[i]; });
      } };
    S.setStep(0, true);
    return S;
  };

  /* 들어가는 기기 여섯: 한 줄로 놓고 아래에 이름표 카드 */
  SCENES.kit = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 100);
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
      var base = cyl(0.95, 1.0, 0.06, PH.metal(0x2c2f36, 0.42), 64); base.position.set(X[i], -0.87, 0); scene.add(shadows(base));
      var ring = noSh(new THREE.Mesh(new THREE.TorusGeometry(1.0, 0.012, 6, 64), Bm(P.amber, { transparent: true, opacity: 0.4 }))); ring.rotation.x = Math.PI / 2; ring.position.set(X[i], -0.85, 0); scene.add(ring);
      o.position.set(X[i], 0.0, 0); o.scale.setScalar(sc[i]); o.rotation.y = ry[i]; o.userData.ry = ry[i]; scene.add(o);
    });
    if (objs[2].userData.waves) objs[2].userData.waves.forEach(function (w, i) { w.material.opacity = 0.6 - i * 0.18; });
    var desk = woodTop(16.5, 4.2); desk.position.y = -0.9 - 0.06; scene.add(desk); fogFor(scene, 'hall', 18, 40);
    var D = [['카메라 안경', '안경테에 작은 카메라.<br>문제를 찍어요'], ['화면 안경', '렌즈 안쪽 작은 화면.<br>답이 떠요'], ['초소형 이어폰', '귀 속에 쏙.<br>답을 소리로 읽어 줘요'],
      ['휴대폰', '주머니 속 중계소.<br>사진을 보내고 답을 받아요'], ['스마트워치', '손목 위 작은 화면.<br>글자를 보여 줘요'], ['노트북·클라우드 AI', '멀리서 문제를 읽고<br>답을 만들어요']];
    var L = D.map(function (d, i) { return lbl('<b>' + d[0] + '</b><span>' + d[1] + '</span>', 'kc', V(X[i], -2.3, 0.6)); });
    cam.position.set(0, 1.6, 16.2); cam.lookAt(0, -0.75, 0);
    var S = { scene: scene, camera: cam, labels: L, st: 0,
      setStep: function (n) { S.st = n; S.focusObj = n ? objs[n - 1] : null; if (S.fx) { S.fx.r = n ? [0.13, 0.3] : [0.7, 0.62]; S.fx.blur = n ? 1.1 : 0.5; } },
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
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 100);
    rig(scene, true, 8, 4.6, 0);
    var tray = woodTop(9.5, 5.6); tray.position.set(5.6, -0.06, 0); scene.add(tray); fogFor(scene, 'hall', 10, 30);
    var slotA = noSh(new THREE.Mesh(new THREE.RingGeometry(1.45, 1.52, 64), Bm(P.amber, { transparent: true, opacity: 0.5, side: THREE.DoubleSide }))); slotA.rotation.x = -Math.PI / 2; slotA.position.set(4.3, 0.01, 0.5); scene.add(slotA);
    var A = glassesMesh({}), B = glassesMesh({ cam: true });
    var PA = V(4.3, 0.45, 0.5), PB = V(7.0, 0.45, -0.6);
    [A, B].forEach(function (g) { g.rotation.set(-0.1, -0.35, 0); g.scale.setScalar(0.8); scene.add(g); });
    var mag = noSh(new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.03, 8, 40), Bm(P.cool, { transparent: true, opacity: 0 }))); scene.add(mag);
    var L = [lbl('보통 안경', 'tag', A, [0, -0.85, 0.6]), lbl('카메라 안경', 'tag', B, [0, -0.85, 0.6]), lbl('작은 카메라', 'tag cool', B.userData.cam, [0.2, 0.55, 0]),
      lbl('확인할 때 ✓', 'tag ok', V(4.3, 1.7, 0.5)), lbl('시작한 뒤', 'tag bad', V(4.3, 1.7, 0.5))];
    var S = { scene: scene, camera: cam, labels: L, st: 0, w: 0,
      setStep: function (n, snap) { S.st = n; if (snap) S.w = n >= 2 ? 1 : 0; S.focusObj = n === 1 ? B.userData.cam : null; if (S.fx) { S.fx.r = n === 1 ? [0.16, 0.24] : [0.55, 0.55]; S.fx.blur = n === 1 ? 1.2 : 0.7; } },
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
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(32, 16 / 9, 0.5, 100);
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
    settle: function () { if (GL.active) { camRestore(GL.active); GL.active.setStep(step, true); if (GL.active.finish) GL.active.finish(); GL.active.update(0, 2.0, true); renderOnce(); } },
    freeze: function (on) { if (on) { stopLoop(); document.documentElement.classList.add('freeze'); if (GL.active) renderOnce(); } else { document.documentElement.classList.remove('freeze'); if (GL.active) startLoop(); } },
    active: function () { return GL.active; }, redraw: function () { if (GL.active) renderOnce(); },
    models: function () { var o = {}; Object.keys(MDL).forEach(function (k) { var n = []; MDL[k].traverse(function (m) { if (m.isMesh) n.push(m.name + ':' + m.material.name); }); var b = new THREE.Box3().setFromObject(MDL[k]); o[k] = { meshes: n, min: b.min.toArray(), max: b.max.toArray() }; }); return o; },
    find: function (kind) { for (var i = 0; i < slides.length; i++) if (slides[i].getAttribute('data-scene') === kind) return i; return -1; },
    // 점검용: 3D 물건 하나를 따로 찍어요 (shoot.py --closeup)
    closeup: function (name, warm) {
      var K = { '카메라 안경': function () { return glassesMesh({ cam: true }); }, '화면 안경': function () { var g = glassesMesh({ disp: true }); g.userData.disp.material.opacity = 0.95; return g; },
        '초소형 이어폰': function () { var e = earbudMesh(1); e.userData.waves.forEach(function (w, i) { w.material.opacity = 0.7 - i * 0.2; }); return e; }, '휴대폰': function () { return phoneMesh(); },
        '스마트워치': watchMesh, '노트북': laptopMesh, '클라우드 AI': function () { return cloudMesh(true); }, '키보드와 손': keyboardMesh, '모니터 대화창': monitorMesh,
        '학생과 책상': studentMesh, '말 모델(원본)': function () { return modelOf('horse', 3); }, '안경 모델(원본)': function () { return modelOf('specs', 2.2); }, '말(조각)': horseMesh, '수레': cartMesh, '웍': wokMesh, '밥그릇': function () { var b = bowlMesh(); var r = riceMound(380, 0.38, 0.2, null, 3); r.position.y = 0.2; b.add(r); return b; },
        '김치볶음밥': function () { var p = plateMesh(0.8); var f = friedRice(); f.position.y = 0.05; p.add(f); return p; }, '김치 병': jarMesh, '셰프 레시피': recipeCard, '셰프 AI': chefAI, '하네스 상자': harnessCase,
        '연필': pencilMesh, '도구 카드': function () { return card(1.6, 1.1, P.terra, '게임', null, 'gamepad-2'); } };
      if (name === 'list') return Object.keys(K);
      var c = document.createElement('canvas'), r = new THREE.WebGLRenderer({ canvas: c, antialias: true, alpha: true, preserveDrawingBuffer: true });
      r.setSize(480, 400, false); r.setClearColor(0x000000, 0); r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
      var sc = new THREE.Scene(), o = K[name](); sc.add(o);
      if (IMG.env_hall || IMG.env_road) { var et = new THREE.Texture(IMG[warm && IMG.env_hall ? 'env_hall' : 'env_road'] || IMG.env_hall); et.mapping = THREE.EquirectangularReflectionMapping; et.needsUpdate = true; var pmg = new THREE.PMREMGenerator(r); sc.environment = pmg.fromEquirectangular(et).texture; pmg.dispose(); }
      var box = new THREE.Box3().setFromObject(o), ctr = box.getCenter(V(0, 0, 0)), sz = box.getSize(V(0, 0, 0)), R = Math.max(sz.x, sz.y, sz.z);
      rig(sc, !!warm, R * 2, ctr.x, ctr.z);
      var fl = catcher(R * 6, R * 6, 0.35); fl.position.set(ctr.x, box.min.y - 0.001, ctr.z); sc.add(fl);
      var cm = new THREE.PerspectiveCamera(30, 1.2, R * 0.01, R * 40);
      cm.position.set(ctr.x + R * 1.1, ctr.y + R * 0.75, ctr.z + R * 1.9); cm.lookAt(ctr);
      r.render(sc, cm);
      var url = c.toDataURL('image/png'); r.dispose(); return url;
    },
    state: function () { return { slide: cur, step: step, gl: GL.ok, reduced: REDUCED, fx: !!(GL.fx && GL.fxOn), assets: Object.keys(IMG).length, active: GL.active ? GL.active.kind : null }; }
  };
  function boot() { preload(function () { loadModels(start); }); }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(boot, boot); else boot();
})();
