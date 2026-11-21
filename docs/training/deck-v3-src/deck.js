/* deck-v2 · 진행 엔진 + 3D 장면 (ES2017 문법만) */
(function () {
  'use strict';
  var REDUCED = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  if (/[?&]reduced=1/.test(location.search)) REDUCED = true;
  var NOGL = /[?&]nogl=1/.test(location.search);
  document.documentElement.className += ' js' + (REDUCED ? ' reduced' : '') + (/[?&]slots=1/.test(location.search) ? ' show-slots' : '');
  var wipe = document.getElementById('wipe'), lastAg = null;
  var A = window.anime;
  var stage = document.getElementById('stage');
  var slides = [].slice.call(stage.querySelectorAll('.slide'));
  var notesEl = document.getElementById('notes');
  var cur = -1, step = 0, scale = 1;
  var AGENDA = /*__AGENDA__*/['여는 말', '하네스', '같은 부탁 다른 결과', '김치볶음밥', '실습', '마무리'];   // AI 커닝은 따로 덱(ai-cheating/)
  var FOOT = /*__FOOT__*/'AI에게 무기를 주면 · 박진영';

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
      // data-replay: 숨길 때 display를 꺼 둬요 → 보일 때 CSS 등장 움직임(도장 · 결론 문구)이 그 순간부터 다시 시작해요
      if (e.hasAttribute('data-replay')) e.style.display = vis ? '' : 'none';
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
      V3PREV = cur >= 0 ? slides[cur] : null;
      if (cur >= 0) { leave(slides[cur]); slides[cur].classList.remove('on'); }
      cur = i; step = st;
      s.classList.add('on');
      [].forEach.call(s.querySelectorAll('[data-b],[data-only]'), function (e) { e.__vis = undefined; A.utils.set(e, { opacity: 0 }); });
      setBuilds(s, st, true);
      MO.stop();
      V3DIR = dir === -1 ? -1 : 1;
      if (s.classList.contains('v3') && /(cover|section|made3)/.test(s.className)) MO.light(s);   // 바탕 빛은 표지 · 섹션에서만
      if (s.classList.contains('v3')) { if (!REDUCED) anim(s, { opacity: [0, 1], duration: 240, ease: 'outQuad' }); }
      else if (!REDUCED) anim(s, { opacity: [0, 1], scale: [1.012, 1], duration: 560, ease: 'outCubic' });
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
      f.innerHTML = '<span>' + FOOT + '</span><span><b>' + pad(i + 1) + '</b> / ' + pad(slides.length) + '</span>';
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
    var si = slides.indexOf(s); later(function () { prebuild(si); }, 1800);
    [].forEach.call(s.querySelectorAll('.stw'), swInit);
  }
  function leave(s) {
    clearTimers();
    MO.stop();
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

  /* AI 회사들도 하네스로: 두뇌 둘레에 기능 알약이 소용돌이로 날아와 끼워지고(선이 따라 그려져요), 마지막에 고리가 닫혀요 */
  FX.hx = {
    enter: function (s, st) {
      [].forEach.call(s.querySelectorAll('.hxcore'), function (core) {
        var g = core.querySelector('.ln'), cx = core.offsetWidth / 2, cy = core.offsetHeight / 2;
        while (g.firstChild) g.removeChild(g.firstChild);
        [].forEach.call(core.querySelectorAll('.hc'), function (c) {
          var fx = c.offsetLeft + c.offsetWidth / 2 - cx, fy = c.offsetTop + c.offsetHeight / 2 - cy;
          var ln = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          ln.setAttribute('x1', cx); ln.setAttribute('y1', cy); ln.setAttribute('x2', cx + fx); ln.setAttribute('y2', cy + fy);
          var len = Math.sqrt(fx * fx + fy * fy);
          ln.style.strokeDasharray = len; g.appendChild(ln);
          c.__g = { fx: fx, fy: fy, th: Math.atan2(fy, fx), r: len, ln: ln, len: len }; c.__on = false;
          FX.hx.draw(c, 0);
        });
      });
      FX.hx.apply(s, st, false);
      if (!st) anim(s.querySelectorAll('.brain'), { scale: [0.72, 1], duration: 760, delay: A.stagger(110, { start: 180 }), ease: 'outBack' });
    },
    draw: function (c, t) {
      var G = c.__g, th = G.th - 1.35 * (1 - t), r = G.r * (0.12 + 0.88 * t);
      var x = Math.cos(th) * r - G.fx, y = Math.sin(th) * r - G.fy;
      c.style.transform = t >= 1 ? '' : 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px) scale(' + (0.5 + 0.5 * t).toFixed(3) + ')';
      c.style.opacity = Math.min(1, t * 2.5);
      G.ln.style.strokeDashoffset = G.len * (1 - Math.max(0, (t - 0.35) / 0.65));
    },
    apply: function (s, st, move) {
      var k = 0;
      s.classList.toggle('done', st >= 5);
      [].forEach.call(s.querySelectorAll('.hc'), function (c) {
        var vis = st >= +c.getAttribute('data-s');
        if (vis === c.__on) return;
        if (c.__an) { c.__an.pause(); c.__an = null; }
        c.__on = vis;
        if (!vis || !move || REDUCED) { FX.hx.draw(c, vis ? 1 : 0); return; }
        var o = { t: 0 }, d = 60 * (k % 2) + 70 * Math.floor(k / 2); k++;
        c.__an = A.animate(o, { t: 1, duration: 760, delay: d, ease: 'outCubic', onUpdate: function () { FX.hx.draw(c, o.t); }, onComplete: function () { FX.hx.draw(c, 1); } });
      });
    },
    step: function (s, st, dir) { FX.hx.apply(s, st, dir !== -1); },
    leave: function (s) { [].forEach.call(s.querySelectorAll('.hc'), function (c) { if (c.__an) { c.__an.pause(); c.__an = null; } }); }
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
/*__MOTION__*/
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
      // 무너진 모습에서 되돌릴 때는 전환을 끄고 바로 세워요 (안 그러면 벽돌이 바닥에서 거꾸로 날아올라요: motion QA)
      w.classList.add('reset'); w.classList.remove('fallen', 'cracked'); w.classList.add('on'); void w.offsetWidth; w.classList.remove('reset');
      if (REDUCED) { w.classList.add('fallen'); A.utils.set(big, { opacity: 1 }); return; }
      A.utils.set(big, { opacity: 0 });
      later(function () { w.classList.add('cracked'); }, 350);
      later(function () { w.classList.add('fallen'); anim(big, { opacity: [0, 1], translateY: [30, 0], duration: T2, ease: 'outExpo' }); }, 1150);
    },
    step: function (s, st) { if (st >= 1) s.querySelector('.wall').classList.add('cracked', 'fallen'); },
    leave: function (s) { s.querySelector('.wall').classList.remove('cracked', 'fallen'); }
  };
  // 바닥이 올라가요: 하네스 AI 기둥이 맨밥 높이에서 셰프 레시피 높이로 자라요
  FX.floor = {
    enter: function (s, st) { this.step(s, st); },
    step: function (s, st) { s.querySelector('.levels').classList.toggle('up', st >= 1); },
    leave: function (s) { s.querySelector('.levels').classList.remove('up'); }
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

  /* ---------- 시연 스톱워치: 시계 하나를 여러 장(.sw)이 같이 보여 줘요. 장을 넘겨도 계속 돌아요 ---------- */
  var SW = { run: false, t0: 0, acc: 0, iv: 0, laps: [] };
  function swNow() { return SW.acc + (SW.run ? Date.now() - SW.t0 : 0); }
  function swFmt(ms) { var d = Math.floor(ms / 100), s = Math.floor(d / 10), m = Math.floor(s / 60); s = s % 60; return m + ':' + (s < 10 ? '0' : '') + s + '.' + (d % 10); }
  function swDraw() {
    var ms = swNow(), txt = swFmt(ms);
    [].forEach.call(document.querySelectorAll('.stw'), function (w) {
      w.querySelector('.swt').textContent = txt;
      var sp = w.querySelector('.sws');
      if (sp) sp.textContent = SW.run ? '재는 중 · T 멈춤' : (ms > 0 ? '멈춤 · T 계속 · R 처음으로' : (w.classList.contains('mini') ? 'T 시작 · R 처음으로' : '눌러서 시작 · T'));
      w.classList.toggle('run', SW.run);
    });
    [].forEach.call(document.querySelectorAll('.relay .rn'), function (n) {
      var i = +n.getAttribute('data-i'), v = SW.laps[i];
      n.classList.toggle('on', v !== undefined);
      n.querySelector('.swst').textContent = v === undefined ? '·' : swFmt(v);
    });
  }
  function swToggle() {
    if (SW.run) { SW.acc += Date.now() - SW.t0; SW.run = false; clearInterval(SW.iv); }
    else { SW.t0 = Date.now(); SW.run = true; SW.iv = setInterval(swDraw, 50); }
    swDraw();
  }
  function swReset() { if (SW.run) clearInterval(SW.iv); SW.run = false; SW.acc = 0; SW.laps = []; swDraw(); }
  function swLap(i) {
    if (!SW.run && !swNow()) return;
    if (i === undefined) { i = 0; while (i < 4 && SW.laps[i] !== undefined) i++; }
    if (i < 4) SW.laps[i] = swNow();
    swDraw();
  }
  function swInit(w) {
    if (w.__init) return; w.__init = true;
    w.addEventListener('click', function (e) {
      e.stopPropagation();
      var t = e.target.closest ? e.target.closest('button') : null;
      if (t && t.classList.contains('swre')) swReset();
      else if (t && t.classList.contains('swlap')) swLap();
      else swToggle();
    });
    var rel = w.parentNode.querySelector('.relay');
    if (rel) [].forEach.call(rel.querySelectorAll('.rn'), function (n) { n.addEventListener('click', function (e) { e.stopPropagation(); swLap(+n.getAttribute('data-i')); }); });
    swDraw();
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
  var MDL = {}, MDLA = {};
  function loadModels(cb) {
    var keys = Object.keys(MODELS), left = keys.length, done = false;
    function fin() { if (!done) { done = true; cb(); } }
    if (!left || NOGL || !window.THREE || !THREE.GLTFLoader) { fin(); return; }
    function one() { if (--left === 0) fin(); }
    keys.forEach(function (k) {
      try {
        var src = MODELS[k];
        if (src.slice(0, 4) === 'glb:') { var bin = atob(src.slice(4)), buf = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i); src = buf.buffer; }
        new THREE.GLTFLoader().parse(src, '', function (g) {
          g.scene.traverse(function (o) {
            if (!o.isMesh) return;
            ['map', 'emissiveMap'].forEach(function (m) { if (o.material[m]) { o.material[m].encoding = THREE.LinearEncoding; o.material[m].needsUpdate = true; } });
            o.castShadow = o.receiveShadow = true;
          });
          MDL[k] = g.scene; MDLA[k] = g.animations || []; one();
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
  var SEG = { cover: 'hall', reveal: 'road', kitchenA: 'kitchen', kitchenB: 'kitchen', robot: 'none', made: 'hall', swap: 'hall', recap: 'hall', story: 'hall', kit: 'hall', look: 'hall' };
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
    // v3: 그림이 있으면 3D 장면 뒤 배경을 어둡게 한 그림으로 (3D가 주인공, 그림은 뒤에)
    var il = { cover: 'il_cover_a_dk', robot: 'il_kitchen_backdrop_dk', made: 'il_closing_dk' }[kind];
    if (il && IMG[il]) bd = IMG[il];
    if (bd && !S.noBg) { var t = new THREE.Texture(bd); t.needsUpdate = true; t.center.set(0.5, 0.5); t.repeat.set(0.9, 0.9); sc.background = t; S.bg = t; }
    if (env) sc.traverse(function (o) { if (o.isHemisphereLight) o.intensity *= 0.3; else if (o.isDirectionalLight) o.intensity *= (S.lightK || 0.75); });
    S.fx = Object.assign({ focus: [0.5, 0.5], r: [0.62, 0.6], blur: 0.7, bloom: 0.14, bloomT: 0.93, grain: 0.028, vig: 0.4 }, S.fx || {});
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
      var bl = new THREE.UnrealBloomPass(new THREE.Vector2(960, 540), 0.14, 0.5, 0.93), fin = new THREE.ShaderPass(finalShader());
      c.addPass(rp); c.addPass(bl); c.addPass(fin);
      GL.fx = { c: c, rp: rp, bl: bl, fin: fin }; GL.fxOn = true;
    } catch (e) { GL.fx = null; GL.fxOn = false; }
  }
  // 색 다루기: S.linear 장면은 선형으로 계산 → ACES 필름 곡선 → sRGB로 내보내요 (툰 부엌). 나머지 장면은 예전 그대로(사진에 맞춘 색).
  //   후처리를 켰을 때는 장면을 그리는 판(렌더 타깃)이 sRGB라, 블룸·마지막 셰이더는 늘 화면 색 그대로 받아요.
  function colorMode(S) {
    var on = !!S.linear, r = GL.r, enc = on ? THREE.sRGBEncoding : THREE.LinearEncoding;
    r.toneMapping = on ? THREE.ACESFilmicToneMapping : THREE.NoToneMapping; r.toneMappingExposure = on ? (S.exposure || 1) : 1; r.outputEncoding = enc;
    if (GL.fx) { GL.fx.c.renderTarget1.texture.encoding = enc; GL.fx.c.renderTarget2.texture.encoding = enc; }
  }
  var _fv;
  function draw(S, t, snap) {
    colorMode(S);
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
    GL.fx.bl.strength = f.bloom; GL.fx.bl.threshold = f.bloomT || 0.9;
    u.uFocus.value.set(F[0], F[1]); u.uR.value.set(F[2], F[3]); u.uBlur.value = F[4];
    u.uGrain.value = REDUCED ? f.grain * 0.6 : f.grain; u.uVig.value = f.vig; u.uTime.value = t || 0;
    GL.fx.c.render();
  }
  // 천천히 흐르는 카메라 (트럭·달리): 장면이 정한 자리에서 아주 조금만 움직여요
  function camRestore(S) { if (S._cb) S.camera.position.copy(S._cb); }
  function camDrift(S, t) {
    if (!S._cb) S._cb = new THREE.Vector3();
    S._cb.copy(S.camera.position);
    if (S.noDrift || (GL.sceneEl && GL.sceneEl.classList.contains('v3'))) return;   // v3: 카메라는 자리 잡으면 멈춰요
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
      GL.r.shadowMap.needsUpdate = true;   // 그림자 갱신을 멈춘 느린 PC에서도, 장면에 들어올 때는 한 번 새로 그려요
      S.setStep(st, true);
      S.update(0, 2.0, true);
      renderOnce();
      startLoop();
    } else {
      GL.active.setStep(st, REDUCED);
      if (REDUCED) { GL.active.update(0, 2.0, true); renderOnce(); }
    }
  }
  // v3: 다음 3D 장면을 미리 만들어 둬요 (처음 들어갈 때 멈칫하지 않게: 셰이더 · 텍스처를 작은 화면에 한 번 그려 둠)
  function prebuild(from) {
    if (!GL.ok) return;
    for (var j = from + 1; j <= Math.min(slides.length - 1, from + 3); j++) {
      var kind = slides[j].getAttribute('data-scene');
      if (!kind || GL.cache[kind] || !SCENES[kind]) continue;
      try {
        var S = GL.cache[kind] = SCENES[kind](slides[j]); S.kind = kind; dress(S, kind);
        S.setStep(0, true); S.update(0, 2.0, true);
        var rt = new THREE.WebGLRenderTarget(160, 90); GL.r.setRenderTarget(rt); GL.r.render(S.scene, S.camera); GL.r.setRenderTarget(null); rt.dispose();
      } catch (e) { GL.r.setRenderTarget(null); }
      return;   // 한 번에 하나만
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
      var dt = Math.max(0, Math.min(0.2, (now - GL.last) / 1000)); GL.last = now;
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
      // 느린 PC(그림자 자동 갱신 꺼짐): 움직이는 장면의 그림자가 굳지 않게 여섯 프레임에 한 번만 다시 그려요
      if (!GL.r.shadowMap.autoUpdate && frames % 6 === 0) GL.r.shadowMap.needsUpdate = true;
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
  var P = { cream: 0x4b4f5a, stone2: 0x646976, paper: 0xece8df, slab: 0x1d2026, sand: 0x7d8088, ground: 0x15171b, road: 0x0c0d10, curb: 0x2c2f37, roadBad: 0x25272e,
    terra: 0x8fc4d6, terra2: 0x8fc4d6, teal: 0x8fc4d6, teal2: 0x6fa9be, car: 0x4a6a7a, ink: 0x101114, brown: 0x2f3138, wood: 0x6b5442, amber: 0xd9a85c,
    mint: 0x8fc4d6, cool: 0x8fc4d6, coral: 0xd5806a, dk: 0x141210, dk2: 0x1f1c19, skin: 0xe9bb97, hair: 0x1c130f, leaf: 0x3d6b54, idle: 0x3d4048 };
  var CSS = { acc: '#8fc4d6', acc2: '#8fc4d6', warm: '#d9a85c', ink: '#0e1418', paper: '#f3f0e9' };
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
    var fill = new THREE.DirectionalLight(warmSeg ? 0xe8c48a : 0xa9b6c8, warmSeg ? 0.3 : 0.28); fill.position.set(-8, 4, 6); scene.add(fill);
    var rim = new THREE.DirectionalLight(warmSeg ? 0xf1dcb8 : 0xcfe0e8, warmSeg ? 0.5 : 0.55); rim.position.set(-4, 7, -10); scene.add(rim);
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
  // 카메라 옮기기: 처음 0.45초는 천천히 출발(덜컥 시작하지 않게), 그 뒤 1초 남짓이면 자리를 잡아요 (motion QA)
  function camK(rate, since, dt) { var r = Math.max(0, Math.min(1, since / 0.45)); return damp(rate * (0.12 + 0.88 * r * r * (3 - 2 * r)), dt); }
  function V(x, y, z) { return new THREE.Vector3(x, y, z); }
  function backOut(u) { u = Math.max(0, Math.min(1, u)); var c = 1.70158; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); }
  function ease(u) { u = Math.max(0, Math.min(1, u)); return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; }

  // 글씨 + 아이콘 카드 (앞면 +z)
  function card(w, h, color, text, fg, icon) {
    // 색은 하나로: 짙은 남색 유리 타일 + 강조색 아이콘 (color가 호박색이면 따뜻한 강조). 카드마다 다른 색을 쓰지 않아요.
    var g = new THREE.Group(), warm = color === P.amber, acc = warm ? '#f2a94e' : CSS.acc;   // v3: 호박색이면 따뜻한 먹빛 카드
    var body = rbox(w, h, 0.16, Math.min(w, h) * 0.16, PH.plastic(warm ? 0x2a2119 : 0x1b1d22, { roughness: 0.6, clearcoat: 0.12, envMapIntensity: 0.5 })); g.add(body);
    var W = 512, H = Math.round(512 * h / w), img = null;
    var t = tex(W, H, paint);
    function paint(c) {
      var gr = c.createLinearGradient(0, 0, W * 0.4, H); gr.addColorStop(0, warm ? '#3b2e22' : '#2b2e36'); gr.addColorStop(1, warm ? '#2a2119' : '#1b1d22');
      c.fillStyle = gr; rr2d(c, 3, 3, W - 6, H - 6, 58); c.fill();
      var sh = c.createLinearGradient(0, 0, 0, H * 0.5); sh.addColorStop(0, 'rgba(255,255,255,.06)'); sh.addColorStop(1, 'rgba(255,255,255,0)'); c.fillStyle = sh; rr2d(c, 3, 3, W - 6, H * 0.5, 58); c.fill();
      c.strokeStyle = warm ? 'rgba(242,169,78,.35)' : 'rgba(243,240,233,.2)'; c.lineWidth = 3; rr2d(c, 5, 5, W - 10, H - 10, 56); c.stroke();
      c.fillStyle = warm ? '#f6eee2' : '#f3f0e9'; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.font = '700 ' + (text.length > 4 ? 60 : 74) + 'px ' + FONT;
      if (icon) { if (img) { c.drawImage(img, W / 2 - 60, H * 0.35 - 60, 120, 120); } c.fillText(text, W / 2, H * 0.76); }
      else c.fillText(text, W / 2, H / 2 + 4);
    }
    if (icon) iconImg(icon, acc, function (im) { img = im; t.redraw(paint); });
    var face = plane(w * 0.97, h * 0.97, t); face.position.z = 0.085; g.add(face);
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
      var t = tex(256, 160, function (c, w, h) { c.fillStyle = 'rgba(143,196,214,0.92)'; rr2d(c, 8, 8, w - 16, h - 16, 26); c.fill(); c.fillStyle = '#0d2a30'; c.font = '800 96px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(o.dispText || '③', w / 2, h / 2 + 4); });
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
      c.fillStyle = '#f3f0e9'; c.fillRect(0, 0, w, h);
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
    var h = blob(r * 4, 0, color === P.amber ? 'rgba(217,168,92,0.3)' : 'rgba(143,196,214,0.3)'); h.rotation.x = 0; g.add(h); g.userData.halo = h;
    return g;
  }
  function pathTube(curve, r, color, op) { return noSh(new THREE.Mesh(new THREE.TubeGeometry(curve, 80, r, 8, false), Bm(color || P.cool, { transparent: true, opacity: op === undefined ? 0.25 : op, depthWrite: false }))); }
  function face(o, cam) { o.quaternion.copy(cam.quaternion); }

  function fogFor(scene, seg, near, far) { scene.fog = new THREE.Fog(seg === 'hall' ? 0x241f1a : seg === 'kitchen' ? 0x2a1810 : 0x23262c, near, far); }

  var SCENES = {};

  /* 표지: 공정 카드 여섯 장이 두 줄로 떠 있고, 빛이 기획 → 배포로 지나가요 */
  SCENES.cover = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 100);
    cam.position.set(0, 0.4, 19); cam.lookAt(0.4, 0, 0);
    rig(scene, false, 9, 5.5, 0);
    var grp = new THREE.Group(); grp.position.set(5.65, 0.0, 0); grp.scale.setScalar(0.92); scene.add(grp);
    var defs = [['기획', P.amber, null, 'lightbulb'], ['대본', P.amber, null, 'file-text'], ['콘티', P.amber, null, 'layout-grid'],
      ['제작', P.amber, null, 'hammer'], ['수정', P.amber, null, 'pencil'], ['배포', P.amber, null, 'send']];
    var pos = [[-2.45, 1.15, 0.3], [0, 1.45, -0.2], [2.45, 1.15, 0.3], [-2.45, -1.25, 0.1], [0, -0.95, -0.3], [2.45, -1.25, 0.1]];
    var items = defs.map(function (d, i) {
      var c = card(2.15, 1.5, d[1], d[0], d[2], d[3]);
      c.userData = { p: V(pos[i][0], pos[i][1], pos[i][2]), ph: i * 1.1 };
      grp.add(c); return c;
    });
    var path = new THREE.CatmullRomCurve3(pos.map(function (p) { return V(p[0], p[1], p[2] + 0.2); }), false, 'catmullrom', 0.4);
    var tube = pathTube(path, 0.035, P.amber, 0.35); tube.position.z = -0.35; grp.add(tube);
    var pulse = pulseMesh(0.1, P.amber); grp.add(pulse);
    var sh = catcher(14, 8, 0.12); sh.position.set(0, -2.6, 0); grp.add(sh);
    var mx = 0, my = 0;
    window.addEventListener('mousemove', function (e) { mx = e.clientX / window.innerWidth - 0.5; my = e.clientY / window.innerHeight - 0.5; });
    // v3: 카드가 차례로 통통 튀어 들어와요 (spring: 넘쳤다 돌아옴, 한 장 0.8초 · 0.09초 간격)
    var S = { scene: scene, camera: cam, labels: [], pu: 0, age: 99,
      setStep: function (n, snap) { if (snap) { S.age = (REDUCED || V3DIR < 0) ? 99 : 0; S.pu = 0; } },
      finish: function () { S.age = 99; },
      update: function (dt, t, snap) {
        if (!snap) S.age += dt;
        items.forEach(function (c, i) {
          var u = c.userData, ta = Math.max(0, (S.age - TOK.sec(TOK.xs) - i * TOK.sec(TOK.gap)) / TOK.sec(TOK.m)), k = ta >= 1 ? 1 : EZ.bounce(ta);
          c.scale.setScalar(Math.max(0.001, k));
          c.position.copy(u.p);   // v3: 내려앉은 뒤에는 가만히 (반복 움직임 없음)
          c.position.y -= (1 - Math.min(1, k)) * 0.9;
          c.rotation.set(-0.05, -0.22 - (1 - Math.min(1, ta)) * (1 - Math.min(1, ta)) * 3.1, 0);   // 돌면서 자리에
        });
        S.pu = snap ? 0.42 : Math.min(1, S.pu + dt * 0.35); pulse.visible = S.pu < 1;   // 빛 한 번만 지나가요
        pulse.position.copy(path.getPointAt(S.pu)); pulse.position.z += 0.1; face(pulse.userData.halo, cam);
        var tx = 0, ty = 0.4;   // v3: 마우스를 따라 움직이지 않아요
        cam.position.x += (tx - cam.position.x) * (snap ? 1 : damp(2, dt)); cam.position.y += (ty - cam.position.y) * (snap ? 1 : damp(2, dt));
        cam.lookAt(0.4, 0, 0);
      } };
    return S;
  };

  /* 「하네스」 한 단어: 글자 셋이 위에서 떨어져 꽂히고 → 충격파·빛 조각 → 빛이 훑고 → 카메라가 다가가 멈춰요 (약 2.6초) */
  function glyphTex(ch, fill) {
    return tex(512, 512, function (c, w, h) {
      if (fill) { var gr = c.createLinearGradient(0, 70, 0, 470); gr.addColorStop(0, '#fbf8f1'); gr.addColorStop(0.55, '#f1ebdf'); gr.addColorStop(1, '#d8cfbd'); c.fillStyle = gr; } else c.fillStyle = '#ffffff';
      c.font = '900 440px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(ch, w / 2, h / 2 + 24);
    });
  }
  SCENES.reveal = function (slideEl) {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(28, 16 / 9, 1.5, 120);
    rig(scene, false, 8, 0, 0);
    fogFor(scene, 'road', 12, 42);
    var fl = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), M(0x1f2023, Object.assign({ roughness: 0.82, metalness: 0.0, envMapIntensity: 0.25 }, pbr('asphalt_02', 24, 24))));
    fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; scene.add(fl);
    var back = new THREE.DirectionalLight(0xffe6c2, 0.55); back.position.set(-3, 5, -8); scene.add(back);
    var sweepU = { value: -6 };
    var chars = ['하', '네', '스'], SZ = 2.0, GAP = 1.72, LAY = 18, DEP = 0.013;
    var sideM = [];
    var letters = chars.map(function (ch, i) {
      var g = new THREE.Group(), face = glyphTex(ch, true), mask = glyphTex(ch, false);
      var fm = new THREE.MeshStandardMaterial({ map: face, alphaTest: 0.5, metalness: 0.0, roughness: 0.62, emissive: 0xffffff, emissiveMap: face, emissiveIntensity: 0.46, envMapIntensity: 0.3 });
      var front = new THREE.Mesh(new THREE.PlaneGeometry(SZ, SZ), fm); g.add(front);
      var sm = new THREE.MeshStandardMaterial({ color: 0x8a6d3e, alphaMap: mask, alphaTest: 0.5, transparent: false, metalness: 0.75, roughness: 0.42, emissive: 0x3a2c14, emissiveIntensity: 0.3 });
      sideM.push(sm);
      for (var k = 1; k <= LAY; k++) { var l = new THREE.Mesh(front.geometry, sm); l.position.z = -k * DEP; l.castShadow = k === LAY; g.add(l); }
      var sw = new THREE.Mesh(front.geometry, new THREE.ShaderMaterial({ uniforms: { map: { value: mask }, p: sweepU }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
        vertexShader: 'varying vec2 vUv; varying vec3 vW; void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
        fragmentShader: 'uniform sampler2D map; uniform float p; varying vec2 vUv; varying vec3 vW; void main(){ float a = texture2D(map, vUv).a; float d = vW.x * 0.9 + vW.y * 0.45 - p; float band = exp(-d * d * 5.0); gl_FragColor = vec4(vec3(1.0, 0.96, 0.86) * band * a * 0.55, 1.0); }' }));
      sw.position.z = 0.003; noSh(sw); g.add(sw);
      g.userData.x = (i - 1) * GAP; g.userData.t0 = 0.2 + i * 0.2;
      scene.add(g); return g;
    });
    // 바닥 빛 웅덩이 · 충격파 고리 셋 · 빛 조각
    var pool = blob(4.6, 0, 'rgba(255,232,196,0.07)'); pool.position.y = 0.01; scene.add(pool);
    var rings = [0, 1, 2, 3].map(function () { var r = noSh(new THREE.Mesh(new THREE.RingGeometry(0.92, 1.0, 96), Bm(0xe9e2d2, { transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide }))); r.rotation.x = -Math.PI / 2; r.position.y = 0.02; scene.add(r); return r; });
    var NP = 360, ppos = new Float32Array(NP * 3), pv = [], p0 = [];
    for (var k = 0; k < NP; k++) { var a = k * 2.39996, r = (k * 0.618034) % 1; p0.push(V((r - 0.5) * 5.4, 0.05, ((k * 0.3819) % 1 - 0.5) * 0.6)); pv.push(V(Math.cos(a) * (1 + r * 3.2), 1.2 + ((k * 0.7548) % 1) * 4.2, Math.sin(a) * (0.6 + r * 2.4))); }
    var pgeo = new THREE.BufferGeometry(); pgeo.setAttribute('position', new THREE.BufferAttribute(ppos, 3));
    var pmat = new THREE.PointsMaterial({ color: 0xcfc4ae, size: 0.045, map: dotTex(), transparent: true, depthWrite: false, opacity: 0 });
    var pts = noSh(new THREE.Points(pgeo, pmat)); pts.frustumCulled = false; scene.add(pts);
    var L = [lbl('HARNESS', 'hx', V(0, -0.35, 0.6))];
    var Y = SZ / 2 - 0.02, TI = 0.2 + 2 * 0.2 + 0.42;   // 마지막 글자가 닿는 때
    var CA = V(0, 2.4, 17), CB = V(0, 1.15, 9.6), LK = V(0, 0.95, 0);
    var S = { scene: scene, camera: cam, labels: L, age: 0, noDrift: true, lightK: 0.6, fx: { bloom: 0.1, blur: 0.5, r: [0.62, 0.5], vig: 0.46 },
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

          var rg = rings[i], lt = land;
          rg.position.x = g.userData.x; rg.scale.setScalar(0.4 + Math.max(0, lt) * 3.2); rg.material.opacity = lt > 0 && lt < 0.5 ? (1 - lt / 0.5) * 0.16 : 0;
        });
        var tau = A - TI;
        var big = rings[3]; big.scale.setScalar(0.5 + Math.max(0, tau) * 11); big.material.opacity = tau > 0 && tau < 0.9 ? (1 - tau / 0.9) * 0.2 : 0;
        pool.material.opacity = tau > 0 ? Math.min(1, tau * 3) * (0.75 + 0.6 * Math.exp(-tau * 4)) : 0;
        var tt = Math.max(0, Math.min(tau, 1.8));
        for (var k = 0; k < NP; k++) { var o = p0[k], v = pv[k]; ppos[k * 3] = o.x + v.x * tt; ppos[k * 3 + 1] = Math.max(0.02, o.y + v.y * tt - 3.4 * tt * tt); ppos[k * 3 + 2] = o.z + v.z * tt; }
        pgeo.attributes.position.needsUpdate = true;
        pmat.opacity = tau > 0 && tau < 1.8 ? (1 - tau / 1.8) * 0.5 : 0;
        sweepU.value = -6 + Math.max(0, Math.min(1, (A - 1.3) / 0.9)) * 12;
        S.fx.bloom = 0.1 + (tau > 0 ? 0.22 * Math.exp(-tau * 3) : 0);
        var push = 1 - Math.pow(1 - Math.min(1, A / 2.6), 3);
        cam.position.lerpVectors(CA, CB, push);
        if (tau > 0 && tau < 0.6) { cam.position.x += Math.sin(tau * 70) * 0.05 * Math.exp(-tau * 7); cam.position.y += Math.cos(tau * 63) * 0.04 * Math.exp(-tau * 7); }

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
    var glow = blob(0.9, 0, 'rgba(143,196,214,0.85)'); glow.position.y = 0.42; g.add(glow);
    var t = tex(512, 128, function (c, w, h) { c.fillStyle = '#8fc4d6'; c.font = '900 64px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('하네스', w / 2, h / 2 + 4); });
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
        var o = d[0]; o.userData.seat = d[1]; o.userData.rot = d[2]; o.userData.snapT = -1; var r = snapRing(0xe9e2d2); scene.add(r); o.userData.ring = r; scene.add(o); items.push(o);
      });
      L.push(lbl('셰프 레시피', 'tag cool', recipe, [0, 0.62, 0]), lbl('좋은 재료', 'tag cool', jar, [0, 0.95, 0]), lbl('전문 도구', 'tag cool', spatPro, [0, 0.3, 0.3]), lbl('제대로 완성 ✓', 'ck', plate, [0, 1.1, 0]));
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

  /* =====================================================================
     김치볶음밥 그림책 (포근한 툰 부엌 · 창으로 드는 햇살 · 로봇 주인공)
     로봇: three.js 예제 RobotExpressive.glb (Tomás Laulhé, CC0 1.0) — 걷기·뛰기·도리도리·끄덕·엄지척 애니메이션
     0 걸어 들어와 「김치볶음밥 해 줘!」 → 1 레시피·도구 없이 허둥지둥, 맨밥 → 2 「김치 왜 안 넣었어?」 → 3 급히 찾아와 밥 따로 김치 따로
     4 셰프 레시피가 날아와 펼쳐짐 → 5 도구·재료가 하나씩 날아와 착착 → 6 척척 요리 → 7 완벽한 김치볶음밥 · 엄지척 → 8 「이게 하네스!」
     ===================================================================== */
  /* --- 툰 재질 (이 장면만 색을 제대로 다뤄요: 선형 계산 → ACES 필름 곡선 → sRGB 출력. S.linear = true) ---
     색은 화면에서 보는 sRGB 값으로 적고 TM이 선형으로 바꿔요. 3단 램프(그늘 0.22 · 중간 0.62 · 빛 1) + 가장자리 빛(프레넬) */
  var _ramp = null, _felt = null;
  function toonRamp() {
    if (_ramp) return _ramp;
    var d = new Uint8Array([56, 56, 56, 56, 158, 158, 255, 255]); _ramp = new THREE.DataTexture(d, 8, 1, THREE.LuminanceFormat);
    _ramp.minFilter = _ramp.magFilter = THREE.LinearFilter; _ramp.generateMipmaps = false; _ramp.needsUpdate = true; return _ramp;
  }
  function sx(t) { t.encoding = THREE.sRGBEncoding; t.needsUpdate = true; return t; }
  function lin(c) { return (c && c.isColor) ? c : new THREE.Color(c).convertSRGBToLinear(); }
  // 펠트·점토 느낌: 아주 옅은 얼룩 텍스처
  function feltTex() {
    if (_felt) return _felt;
    var r = rng(77);
    _felt = tex(128, 128, function (c, w, h) { c.fillStyle = '#f6f6f6'; c.fillRect(0, 0, w, h); for (var i = 0; i < 900; i++) { var v = 232 + Math.floor(r() * 23); c.fillStyle = 'rgb(' + v + ',' + v + ',' + v + ')'; c.fillRect(r() * w, r() * h, 1 + r() * 2.5, 1 + r() * 2.5); } });
    _felt.wrapS = _felt.wrapT = THREE.RepeatWrapping; _felt.generateMipmaps = true; _felt.minFilter = THREE.LinearMipmapLinearFilter; _felt.repeat.set(3, 3); return sx(_felt);
  }
  // 가장자리 빛: 윤곽이 배경에서 또렷이 떨어지게 (위·뒤쪽 가장자리에 따뜻한 빛 한 줄)
  function toonRim(sh) {
    sh.fragmentShader = sh.fragmentShader.replace('gl_FragColor = vec4( outgoingLight, diffuseColor.a );',
      'float rimF = pow( 1.0 - clamp( dot( normalize( vViewPosition ), normal ), 0.0, 1.0 ), 3.0 );\n' +
      'outgoingLight += vec3( 1.0, 0.86, 0.66 ) * rimF * 0.42 * ( 0.35 + 0.65 * clamp( normal.y * 0.5 + 0.6, 0.0, 1.0 ) );\n' +
      'gl_FragColor = vec4( outgoingLight, diffuseColor.a );');
  }
  function TM(color, o) { var m = new THREE.MeshToonMaterial(Object.assign({ color: lin(color), gradientMap: toonRamp(), map: feltTex() }, o || {})); m.onBeforeCompile = toonRim; return m; }
  function BmL(color, o) { return Bm(lin(color), o); }
  function rb(w, h, d, r, color) { return rbox(w, h, d, r, TM(color)); }
  function puff(scale, color) { var g = new THREE.Group(), m = TM(color || 0xffffff); [[0, 0, 0, 0.3], [0.26, 0.05, 0, 0.22], [-0.24, 0.02, 0.02, 0.2], [0.05, 0.2, 0, 0.2]].forEach(function (b) { g.add(sph(b[3], m, b[0], b[1], b[2])); }); g.scale.setScalar(scale || 1); return g; }
  // 닿는 자리 그늘(가짜 AO): 물건 밑 · 조리대 밑 · 벽 모서리
  function contact(r, op) { var b = blob(r, op === undefined ? 0.5 : op); sx(b.material.map); b.renderOrder = 2; return b; }
  function shadeStrip(w, h, op) {
    var t = sx(tex(8, 64, function (c, W, H) { var g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(40,18,30,' + op + ')'); g.addColorStop(1, 'rgba(40,18,30,0)'); c.fillStyle = g; c.fillRect(0, 0, W, H); }));
    return noSh(new THREE.Mesh(new THREE.PlaneGeometry(w, h), Bm(0xffffff, { map: t, transparent: true, depthWrite: false })));
  }
  var KP = { wall: '#f1c88e', wallLo: '#d99a5e', floor: '#c58a55', floorLine: '#9c6436', cab: 0x1f6f7a, door: 0x2b8792, top: 0xfff0d8, knob: 0xf2b53a, wood: 0xb5733c,
    tomato: 0xe24a2c, mustard: 0xf2b53a, leaf: 0x58b45c, mintJar: 0x7fcbbb, white: 0xffffff, steel: 0x3b3f4e, robot: 0x4fa8c4, robotJoint: 0xf2f6fb, robotEye: 0x17203a };
  function toonKitchen(scene) {
    var Y = -1.2, WZ = -3.4;
    // 벽: 가운데가 밝고 모서리·바닥 쪽이 어두운 그림(구워 넣은 그늘)
    var wallT = sx(tex(512, 256, function (c, w, h) {
      c.fillStyle = KP.wall; c.fillRect(0, 0, w, h);
      var g = c.createLinearGradient(0, 0, 0, h); g.addColorStop(0, 'rgba(150,70,40,.34)'); g.addColorStop(0.3, 'rgba(150,70,40,0)'); g.addColorStop(0.62, 'rgba(150,70,40,0)'); g.addColorStop(1, 'rgba(120,50,40,.5)'); c.fillStyle = g; c.fillRect(0, 0, w, h);
      var v = c.createRadialGradient(w * 0.5, h * 0.45, h * 0.3, w * 0.5, h * 0.45, w * 0.62); v.addColorStop(0, 'rgba(110,45,35,0)'); v.addColorStop(1, 'rgba(110,45,35,.3)'); c.fillStyle = v; c.fillRect(0, 0, w, h);
    }));
    var wall = new THREE.Mesh(new THREE.PlaneGeometry(34, 13), TM(0xffffff, { map: wallT })); wall.position.set(0, Y + 6.5, WZ); noSh(wall); scene.add(wall);
    var base = rb(34, 0.5, 0.14, 0.05, 0xfff3de); base.position.set(0, Y + 0.25, WZ + 0.07); scene.add(base);
    // 바닥: 따뜻한 나무 널 + 가장자리 어둠
    var floorT = sx(tex(1024, 512, function (c, w, h) {
      c.fillStyle = KP.floor; c.fillRect(0, 0, w, h); var r = rng(11);
      for (var i = 0; i < 32; i++) { var x = i * 32; c.fillStyle = 'rgba(255,220,170,' + (r() * 0.16).toFixed(3) + ')'; c.fillRect(x, 0, 32, h); c.fillStyle = KP.floorLine; c.fillRect(x, 0, 2, h); var o = r() * h; c.fillRect(x, o, 32, 2); }
      var v = c.createRadialGradient(w * 0.5, h * 0.45, h * 0.25, w * 0.5, h * 0.45, w * 0.6); v.addColorStop(0, 'rgba(70,25,20,0)'); v.addColorStop(1, 'rgba(70,25,20,.55)'); c.fillStyle = v; c.fillRect(0, 0, w, h);
    }));
    var floor = new THREE.Mesh(new THREE.PlaneGeometry(34, 17), TM(0xffffff, { map: floorT })); floor.rotation.x = -Math.PI / 2; floor.position.set(0, Y, WZ + 8.5); floor.receiveShadow = true; scene.add(floor);
    var corner = shadeStrip(34, 1.6, 0.5); corner.rotation.x = -Math.PI / 2; corner.position.set(0, Y + 0.012, WZ + 0.95); scene.add(corner);
    // 창 + 커튼 + 화분 + 햇살
    var WX = -3.5, WY = 2.3;
    var sky = sx(tex(256, 256, function (c, w, h) { var g = c.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#8fd0ff'); g.addColorStop(0.65, '#d9f0ff'); g.addColorStop(1, '#ffe2a6'); c.fillStyle = g; c.fillRect(0, 0, w, h); c.fillStyle = 'rgba(255,255,255,.95)'; [[60, 80, 26], [92, 72, 20], [176, 128, 22], [204, 122, 16]].forEach(function (b) { c.beginPath(); c.arc(b[0], b[1], b[2], 0, 7); c.fill(); }); c.fillStyle = '#7cc46a'; c.beginPath(); c.arc(40, 300, 90, 0, 7); c.arc(200, 320, 100, 0, 7); c.fill(); }));
    var glassM = Bm(0xffffff, { map: sky }); glassM.color.setRGB(1.25, 1.25, 1.2);
    var glass = noSh(new THREE.Mesh(new THREE.PlaneGeometry(2.6, 2.4), glassM)); glass.position.set(WX, WY, WZ + 0.04); scene.add(glass);
    [[0, 1.26, 3.0, 0.2], [0, -1.26, 3.0, 0.24], [-1.4, 0, 0.2, 2.7], [1.4, 0, 0.2, 2.7], [0, 0, 0.1, 2.4], [0, 0.1, 2.6, 0.08]].forEach(function (f) { var m = rb(f[2], f[3], 0.22, 0.05, KP.white); m.position.set(WX + f[0], WY + f[1], WZ + 0.12); scene.add(m); });
    var sill = rb(3.4, 0.16, 0.56, 0.07, KP.white); sill.position.set(WX, WY - 1.4, WZ + 0.3); scene.add(sill);
    var rod = cyl(0.05, 0.05, 4.6, TM(KP.wood), 10); rod.rotation.z = Math.PI / 2; rod.position.set(WX, WY + 1.68, WZ + 0.3); scene.add(rod);
    [-1, 1].forEach(function (s) { for (var k = 0; k < 4; k++) { var cu = cyl(0.14, 0.19, 3.1, TM(k % 2 ? 0xc93a22 : KP.tomato), 12); cu.position.set(WX + s * (1.62 + k * 0.19), WY + 0.08, WZ + 0.34 + (k % 2) * 0.07); scene.add(cu); } });
    var pot0 = cyl(0.24, 0.18, 0.34, TM(0xf6ead6), 16); pot0.position.set(WX - 0.6, WY - 1.15, WZ + 0.34); scene.add(pot0); var bush = puff(0.8, KP.leaf); bush.position.set(WX - 0.6, WY - 0.82, WZ + 0.34); scene.add(bush);
    var beamT = tex(64, 256, function (c, w, h) { var g = c.createLinearGradient(0, 0, 0, h); g.addColorStop(0, 'rgba(255,226,170,.95)'); g.addColorStop(1, 'rgba(255,226,170,0)'); c.fillStyle = g; c.fillRect(0, 0, w, h); var g2 = c.createLinearGradient(0, 0, w, 0); g2.addColorStop(0, 'rgba(0,0,0,1)'); g2.addColorStop(0.5, 'rgba(0,0,0,0)'); g2.addColorStop(1, 'rgba(0,0,0,1)'); c.globalCompositeOperation = 'destination-out'; c.fillStyle = g2; c.fillRect(0, 0, w, h); });
    var beams = [-0.6, 0.25].map(function (o, k) { var b = noSh(new THREE.Mesh(new THREE.PlaneGeometry(1.1 + k * 0.3, 7), Bm(0xffffff, { map: beamT, transparent: true, opacity: 0.1, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }))); b.position.set(WX + 1.9 + o, WY - 1.9, WZ + 1.5); b.rotation.set(0.5, 0.1, 0.6); scene.add(b); return b; });
    var NM = 46, mp = new Float32Array(NM * 3), r = rng(5); for (var m = 0; m < NM; m++) { mp[m * 3] = WX + 0.4 + r() * 4; mp[m * 3 + 1] = Y + 1.4 + r() * 3.6; mp[m * 3 + 2] = WZ + 0.6 + r() * 1.6; }
    var mg = new THREE.BufferGeometry(); mg.setAttribute('position', new THREE.BufferAttribute(mp, 3));
    var motes = noSh(new THREE.Points(mg, new THREE.PointsMaterial({ color: 0xfff1cc, size: 0.045, map: dotTex(), transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending }))); scene.add(motes);
    // 선반 + 병 + 작은 화분
    var SXp = 3.3, SYp = 3.15;
    var shelf = rb(2.8, 0.16, 0.6, 0.06, KP.wood); shelf.position.set(SXp, SYp, WZ + 0.32); scene.add(shelf);
    [-1, 1].forEach(function (s) { var br = rb(0.12, 0.34, 0.4, 0.04, 0x8f5528); br.position.set(SXp + s * 1.05, SYp - 0.22, WZ + 0.24); scene.add(br); });
    [[-1.0, KP.mustard, 0.5], [-0.5, KP.tomato, 0.36], [0.0, KP.mintJar, 0.46]].forEach(function (j) { var jar = cyl(0.19, 0.19, j[2], TM(j[1]), 16); jar.position.set(SXp + j[0], SYp + 0.08 + j[2] / 2, WZ + 0.34); scene.add(jar); var lid = cyl(0.2, 0.2, 0.07, TM(0xfff6e6), 16); lid.position.set(SXp + j[0], SYp + 0.115 + j[2], WZ + 0.34); scene.add(lid); });
    var pot2 = cyl(0.2, 0.15, 0.3, TM(0xf6ead6), 16); pot2.position.set(SXp + 0.85, SYp + 0.23, WZ + 0.34); scene.add(pot2); var b2 = puff(0.7, KP.leaf); b2.position.set(SXp + 0.85, SYp + 0.52, WZ + 0.34); scene.add(b2);
    // 큰 화분 (오른쪽 바닥)
    var pot1 = cyl(0.46, 0.36, 0.7, TM(0xf6ead6), 18); pot1.position.set(6.3, Y + 0.35, WZ + 1.0); scene.add(pot1); var pl = puff(1.7, KP.leaf); pl.position.set(6.3, Y + 1.3, WZ + 1.0); scene.add(pl); var pl2 = puff(1.2, 0x6cc56f); pl2.position.set(6.45, Y + 1.95, WZ + 1.0); scene.add(pl2);
    var pc = contact(1.1, 0.5); pc.position.set(6.3, Y + 0.015, WZ + 1.0); scene.add(pc);
    // 조리대: 밝은 상판(무대) + 짙은 청록 몸통 + 문짝 · 손잡이
    var top = rb(10.4, 2.5, 0.26, 0.12, KP.top); top.rotation.x = -Math.PI / 2; top.position.set(0, -0.13, 0.1); scene.add(top);
    var body = rb(9.9, 1.02, 2.1, 0.1, KP.cab); body.position.set(0, Y + 0.51, 0.08); scene.add(body);
    for (var d = 0; d < 5; d++) { var door = rb(1.7, 0.74, 0.08, 0.08, KP.door); door.position.set(-3.8 + d * 1.9, Y + 0.5, 1.14); scene.add(door); var kn = sph(0.075, TM(KP.knob)); kn.position.set(-3.8 + d * 1.9, Y + 0.76, 1.21); scene.add(kn); }
    var under = shadeStrip(10.0, 0.5, 0.62); under.position.set(0, -0.5, 1.19); scene.add(under);
    var foot = contact(1, 0.62); foot.scale.set(6.4, 2.3, 1); foot.position.set(0.3, Y + 0.014, 0.6); scene.add(foot);
    // 화구
    var SVX = -1.5;
    var stove = rb(2.0, 1.5, 0.12, 0.1, 0x2c3140); stove.rotation.x = -Math.PI / 2; stove.position.set(SVX, 0.06, 0.2); scene.add(stove);
    var ring = new THREE.Mesh(new THREE.TorusGeometry(0.4, 0.05, 10, 32), TM(0x596074)); ring.rotation.x = Math.PI / 2; ring.position.set(SVX, 0.13, 0.2); scene.add(ring);
    [-0.5, 0.5].forEach(function (o) { var k = cyl(0.07, 0.07, 0.05, TM(KP.tomato), 12); k.rotation.x = Math.PI / 2; k.position.set(SVX + o, 0.06, 0.96); scene.add(k); });
    var fire = noSh(new THREE.Mesh(new THREE.RingGeometry(0.26, 0.48, 32), Bm(0xff7a2a, { transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }))); fire.rotation.x = -Math.PI / 2; fire.position.set(SVX, 0.15, 0.2); scene.add(fire);
    // 매달린 등 둘 (따뜻한 빛의 이유)
    var lamps = [0.55].map(function (x) { var g = new THREE.Group(); var cord = cyl(0.02, 0.02, 3, TM(0x4a3020), 6); cord.position.y = 1.9; g.add(cord);
      var shade = new THREE.Mesh(new THREE.ConeGeometry(0.62, 0.5, 28, 1, true), TM(KP.mustard, { side: THREE.DoubleSide })); shade.position.y = 0.25; g.add(shade);
      var bulbM = Bm(0xffffff); bulbM.color.setRGB(1.5, 1.2, 0.8); var bulb = noSh(sph(0.16, bulbM)); bulb.position.y = 0.06; g.add(bulb);
      var gl = blob(0.9, 0, 'rgba(255,196,110,0.5)'); gl.rotation.x = 0; gl.position.set(0, 0.0, 0.2); g.add(gl); g.userData.glow = gl;
      g.traverse(function (o) { if (o.isMesh) noSh(o); }); g.position.set(x, 4.0, 0.2); scene.add(g); return g; });
    scene.traverse(function (o) { if (o.isMesh && !o.userData.noShadow) { o.castShadow = true; o.receiveShadow = true; } });
    return { Y: Y, WZ: WZ, SVX: SVX, beams: beams, motes: motes, mp: mp, fire: fire, lamps: lamps, WX: WX };
  }
  // 툰 소품 (밑에 닿는 그늘을 하나씩 달아요)
  function grounded(g, r, op) { var c = contact(r, op === undefined ? 0.55 : op); c.position.y = 0.012; g.add(c); return g; }
  function toonBowl(fill) { var g = new THREE.Group(); g.add(lathe([[0.001, 0], [0.2, 0], [0.22, 0.03], [0.4, 0.2], [0.47, 0.36], [0.44, 0.37], [0.37, 0.22], [0.2, 0.07], [0.001, 0.07]], TM(0xffffff, { side: THREE.DoubleSide }))); var stripe = new THREE.Mesh(new THREE.TorusGeometry(0.43, 0.022, 6, 32), TM(0x2f8fd0)); stripe.rotation.x = Math.PI / 2; stripe.position.y = 0.3; g.add(stripe); if (fill) { var d = sph(0.36, TM(fill)); d.scale.y = 0.55; d.position.y = 0.3; g.add(d); } shadows(g); return grounded(g, 0.62); }
  function toonPlate(r) { var g = new THREE.Group(); g.add(lathe([[0.001, 0], [r * 0.7, 0], [r, 0.07], [r * 0.97, 0.1], [r * 0.7, 0.05], [0.001, 0.05]], TM(0xffffff, { side: THREE.DoubleSide }))); var rim = new THREE.Mesh(new THREE.TorusGeometry(r * 0.93, 0.014, 6, 40), TM(0x2f8fd0)); rim.rotation.x = Math.PI / 2; rim.position.y = 0.088; g.add(rim); shadows(g); return grounded(g, r * 1.35); }
  function toonKimchi(n, R, seed) { var g = new THREE.Group(), r = rng(seed || 3), cols = [0xd9301f, 0xee4a2a, 0xc22416, 0xf6dc9a]; for (var i = 0; i < n; i++) { var p = sph(0.09, TM(cols[i % 4])); p.scale.set(1.3, 0.35, 0.9); var a = r() * 6.28, rr = R * Math.sqrt(r()); p.position.set(Math.cos(a) * rr, 0.04 + r() * 0.08, Math.sin(a) * rr); p.rotation.y = r() * 3; g.add(p); } return shadows(g); }
  function toonEgg() { var g = new THREE.Group(); var w = sph(0.28, TM(0xffffff)); w.scale.set(1, 0.16, 0.85); g.add(w); var y = sph(0.11, TM(0xffab00)); y.scale.y = 0.6; y.position.set(0.03, 0.05, 0); g.add(y); return shadows(g); }
  function toonFriedRice() { var g = new THREE.Group(); var d = sph(0.5, TM(0xf07a2c)); d.scale.y = 0.5; d.position.y = 0.06; g.add(d); var k = toonKimchi(14, 0.42, 9); k.position.y = 0.22; g.add(k); var e = toonEgg(); e.position.y = 0.32; g.add(e); var r = rng(4); for (var i = 0; i < 10; i++) { var s = sph(0.038, TM(i % 2 ? 0x4fb356 : 0xfff3d6)); s.position.set((r() - 0.5) * 0.7, 0.3, (r() - 0.5) * 0.6); g.add(s); } return shadows(g); }
  function toonWok() { var g = new THREE.Group(), pts = []; for (var i = 0; i <= 12; i++) { var a = i / 12 * Math.PI * 0.5; pts.push([Math.sin(a) * 0.7 + 0.001, 0.3 - Math.cos(a) * 0.3]); } g.add(lathe(pts, TM(KP.steel, { side: THREE.DoubleSide }))); var h = cyl(0.055, 0.065, 0.8, TM(0xd08a44), 10); h.rotation.z = Math.PI / 2; h.position.set(1.05, 0.32, 0); g.add(h); var rice = sph(0.48, TM(0xf07a2c)); rice.scale.y = 0.32; rice.position.y = 0.1; rice.visible = false; g.add(rice); g.userData.rice = rice; return shadows(g); }
  function toonSpatula() { var g = new THREE.Group(); var b = rb(0.36, 0.04, 0.28, 0.03, 0xdfe6ee); g.add(b); var s = cyl(0.03, 0.03, 0.8, TM(0xd08a44), 8); s.rotation.x = Math.PI / 2; s.position.z = 0.52; g.add(s); return shadows(g); }
  function toonJar() { var g = new THREE.Group(); var j = cyl(0.25, 0.25, 0.55, TM(0xe3f4f0, { transparent: true, opacity: 0.8 }), 18); j.position.y = 0.28; g.add(j); var k = toonKimchi(12, 0.17, 5); k.position.y = 0.1; k.scale.setScalar(1.1); g.add(k); var l = cyl(0.27, 0.27, 0.1, TM(KP.tomato), 18); l.position.y = 0.6; g.add(l); shadows(g); return grounded(g, 0.42); }
  function toonOil() { var g = new THREE.Group(); var b = cyl(0.13, 0.15, 0.6, TM(0xffc93a), 14); b.position.y = 0.3; g.add(b); var n = cyl(0.05, 0.08, 0.18, TM(0xffc93a), 10); n.position.y = 0.68; g.add(n); var c = cyl(0.06, 0.06, 0.08, TM(0x2f9b57), 10); c.position.y = 0.8; g.add(c); shadows(g); return grounded(g, 0.28); }
  // 셰프 레시피 카드: 토마토색 머리띠 + 순서 네 줄 (장면에서 가장 선명한 종이)
  function toonRecipe() {
    var t = sx(tex(360, 480, function (c, w, h) {
      c.fillStyle = '#fff8ea'; rr2d(c, 0, 0, w, h, 30); c.fill();
      c.save(); rr2d(c, 0, 0, w, h, 30); c.clip(); c.fillStyle = '#e24a2c'; c.fillRect(0, 0, w, 112); c.restore();
      c.fillStyle = '#ffffff'; c.font = '900 50px ' + FONT; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText('셰프 레시피', 30, 60);
      c.fillStyle = '#3a2416'; c.font = '900 38px ' + FONT; c.fillText('김치볶음밥', 30, 160);
      for (var i = 0; i < 4; i++) { var y = 228 + i * 58; c.fillStyle = '#f2b53a'; c.beginPath(); c.arc(50, y, 19, 0, 7); c.fill(); c.fillStyle = '#3a2416'; c.font = '900 24px ' + FONT; c.textAlign = 'center'; c.fillText('' + (i + 1), 50, y + 2); c.textAlign = 'left';
        c.fillStyle = '#d9c7ae'; rr2d(c, 84, y - 8, i % 2 ? 170 : 210, 16, 8); c.fill();
        c.strokeStyle = '#2f9b57'; c.lineWidth = 7; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath(); c.moveTo(308, y); c.lineTo(318, y + 10); c.lineTo(336, y - 12); c.stroke(); }
    }));
    var g = new THREE.Group(); var back = rbox(0.64, 0.84, 0.03, 0.04, TM(0xf3dfc0)); g.add(back);
    var p = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.8), TM(0xffffff, { map: t })); p.position.z = 0.017; g.add(p);
    var halo = blob(0.8, 0, 'rgba(255,205,110,0.7)'); halo.rotation.x = 0; halo.position.z = -0.03; g.add(halo); g.userData.halo = halo;
    return shadows(g);
  }
  function markTex(ch, bg) { return sx(tex(128, 128, function (c, w, h) { c.fillStyle = bg; c.beginPath(); c.arc(64, 64, 58, 0, 7); c.fill(); c.fillStyle = '#ffffff'; c.font = '900 92px ' + FONT; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(ch, 64, 70); })); }
  // 로봇: CC0 모델의 재질을 툰으로 바꾸고(청록 몸 · 흰 관절 · 남색 눈), 요리사 모자를 씌우고, 애니메이션 묶음을 준비해요
  function robotRig() {
    var src = MDL.robot; if (!src) return null;
    if (src.parent) src.parent.remove(src);
    if (!src.userData.toon) {
      var mats = {};
      src.traverse(function (o) {
        if (!o.isMesh) return;
        var nm = o.material.name, col = nm === 'Main' ? KP.robot : nm === 'Grey' ? KP.robotJoint : KP.robotEye, key = nm + (o.isSkinnedMesh ? 's' : '') + (o.morphTargetInfluences ? 'm' : '');
        if (!mats[key]) mats[key] = TM(col, { skinning: !!o.isSkinnedMesh, morphTargets: !!o.morphTargetInfluences, map: null });
        o.material = mats[key]; o.castShadow = true; o.receiveShadow = false; o.frustumCulled = false;
      });
      var box = new THREE.Box3().setFromObject(src), k = 3.4 / (box.max.y - box.min.y); src.scale.multiplyScalar(k); src.position.y -= box.min.y * k; src.userData.toon = true;
    }
    var root = new THREE.Group(), body = new THREE.Group(); body.add(src); root.add(body);
    var mixer = new THREE.AnimationMixer(src), acts = {};
    (MDLA.robot || []).forEach(function (cl) { acts[cl.name] = mixer.clipAction(cl); });
    ['ThumbsUp', 'No', 'Yes', 'Wave'].forEach(function (n) { if (acts[n]) { acts[n].setLoop(THREE.LoopOnce, 1); acts[n].clampWhenFinished = true; } });
    var face = null, headEnd = null, head = null;
    src.traverse(function (o) { if (o.morphTargetDictionary && o.morphTargetDictionary.Surprised !== undefined) face = o; if (/^Head_end/.test(o.name)) headEnd = o; else if (o.isBone && o.name === 'Head') head = o; });
    // 요리사 모자: 머리뼈 끝을 따라다녀요
    var hat = new THREE.Group(), hm = TM(0xffffff); var band = cyl(0.4, 0.37, 0.3, hm, 22); band.position.y = 0.12; hat.add(band);
    [[0, 0.5, 0, 0.38], [0.3, 0.42, 0.02, 0.27], [-0.3, 0.42, 0.02, 0.27], [0.02, 0.44, 0.24, 0.26], [0, 0.44, -0.24, 0.26]].forEach(function (b) { hat.add(sph(b[3], hm, b[0], b[1], b[2])); });
    hat.traverse(function (o) { if (o.isMesh) o.castShadow = true; });
    return { root: root, body: body, mixer: mixer, acts: acts, cur: null, face: face, hat: hat, headEnd: headEnd || head };
  }
  function play(R, name, ts, snap) {
    var a = R.acts[name]; if (!a) return;
    a.timeScale = ts || 1;
    if (R.cur === name) return;
    var old = R.acts[R.cur];
    a.reset(); a.enabled = true; a.setEffectiveWeight(1);
    if (old && !snap) { a.play(); old.crossFadeTo(a, 0.22, false); } else { if (old) old.stop(); a.play(); }
    R.cur = name;
  }
  function robot3dScene() {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(28, 16 / 9, 0.5, 80);
    scene.background = lin(0x6b3a22);
    // 빛 셋: 키(따뜻한 앞-왼쪽 위, 그림자) · 필(하늘빛 반구광, 그늘이 푸르스름하게) · 림(재질의 가장자리 빛 + 뒤쪽 약한 빛)
    scene.add(new THREE.HemisphereLight(lin(0xc4d8ff), lin(0xd8935c), 0.46));
    var sun = new THREE.DirectionalLight(lin(0xffe9c8), 1.3); sun.position.set(-6, 10, 8); sun.target.position.set(0.5, 0, -0.5); scene.add(sun); scene.add(sun.target);
    sun.castShadow = true; var sc2 = sun.shadow.camera; sc2.left = -10; sc2.right = 10; sc2.top = 7; sc2.bottom = -7; sc2.near = 1; sc2.far = 34; sun.shadow.mapSize.set(1024, 1024); sun.shadow.radius = 5; sun.shadow.bias = -0.0008; sun.shadow.normalBias = 0.035;
    var K = toonKitchen(scene), Y = K.Y, RZ = -1.75, HOME = 0.6;
    // v3: 코드로 만든 3D 로봇 요리사(robot.js의 RobotChef)가 주인공. 없으면 예전 GLB 로봇으로
    var RCH = (typeof window.RobotChef === 'function') ? window.RobotChef(THREE, { reduced: REDUCED, outline: true }) : null;
    var RBI = RCH ? RCH.beats.map(function (x) { return x.id; }) : [];
    var CLICK = [{ b: 'enter', wok: false }, { b: 'puzzle', wok: false }, { b: 'puzzle', wok: false }, { b: 'turn', wok: false },
      { b: 'wave', wok: false }, { b: 'enter', wok: true, end: true }, { b: 'toss', wok: true }, { b: 'bow', wok: true }];
    var R = RCH ? null : robotRig(), robot;
    if (RCH) { robot = new THREE.Group(); robot.position.set(HOME - 1.1 * 1.35, Y, RZ); robot.scale.setScalar(1.35); robot.add(RCH.root); }
    else { robot = R ? R.root : chefAI(); robot.position.set(HOME, R ? Y : Y + 1.0, RZ); }
    scene.add(robot);
    if (R) scene.add(R.hat);
    var rsh = contact(1.25, 0.6); scene.add(rsh);
    var qm = plane(0.62, 0.62, markTex('?', '#7c6cf0')); scene.add(qm);
    var em = plane(0.62, 0.62, markTex('!', '#ff8a1f')); scene.add(em);
    // 소품
    var serveA = V(1.5, 0.0, 0.55), serveB = V(2.6, 0.0, 0.5), HERO = V(0.75, 0.0, 0.62);
    var bowl = toonBowl(0xfffaf0); scene.add(bowl);
    var side = toonPlate(0.42); side.add(toonKimchi(10, 0.28, 8)); scene.add(side);
    var plate = toonPlate(0.86), fr = toonFriedRice(); fr.position.y = 0.05; fr.scale.setScalar(1.08); plate.add(fr); scene.add(plate);
    var recipe = toonRecipe(); scene.add(recipe);
    var stand = rb(0.9, 0.08, 0.34, 0.03, KP.wood); stand.position.set(-3.75, 0.04, 0.05); stand.rotation.y = 0.3; stand.visible = false; scene.add(stand);
    var wok = toonWok(), spat = toonSpatula(), jar = toonJar(), rice = toonBowl(0xfffaf0), egg = toonEgg(), oil = toonOil();
    var FL = [[wok, V(K.SVX, 0.14, 0.2), 0.62, V(-7, 5.5, 3)], [spat, V(-0.35, 0.05, 0.72), 0.9, V(-6, 6, 4)], [jar, V(2.35, 0.0, -0.25), 0.95, V(7, 6, 2)], [rice, V(3.35, 0.0, 0.5), 0.8, V(8, 5, 2)], [egg, V(2.35, 0.05, 0.72), 0.9, V(7, 7, 4)], [oil, V(3.15, 0.0, -0.45), 0.95, V(8, 7, 0)]];
    FL.forEach(function (f, i) { var o = f[0]; o.userData.seat = f[1]; o.userData.k = f[2]; o.userData.from = f[3]; o.userData.t0 = 0.15 + i * 0.5; scene.add(o); var r = snapRing(0xffd47a); scene.add(r); o.userData.ring = r;
      var tg = new THREE.BufferGeometry(); tg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(10 * 3), 3)); var tr = noSh(new THREE.Points(tg, new THREE.PointsMaterial({ color: 0xffd98a, size: 0.15, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }))); tr.frustumCulled = false; scene.add(tr); o.userData.trail = tr; });
    var tossN = 26, tossP = new Float32Array(tossN * 3), tossG = new THREE.BufferGeometry(); tossG.setAttribute('position', new THREE.BufferAttribute(tossP, 3));
    var toss = noSh(new THREE.Points(tossG, new THREE.PointsMaterial({ color: lin(0xf07a2c), size: 0.12, map: dotTex(), transparent: true, depthWrite: false }))); toss.frustumCulled = false; scene.add(toss);
    var sizzN = 30, sizzP = new Float32Array(sizzN * 3), sizzG = new THREE.BufferGeometry(); sizzG.setAttribute('position', new THREE.BufferAttribute(sizzP, 3));
    var sizz = noSh(new THREE.Points(sizzG, new THREE.PointsMaterial({ color: 0xffd36b, size: 0.07, map: dotTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }))); sizz.frustumCulled = false; scene.add(sizz);
    var steam = [0, 1, 2].map(function () { var p = puff(0.5); noSh(p); p.traverse(function (o) { o.castShadow = false; o.receiveShadow = false; }); scene.add(p); return p; });
    var spark = [0, 1, 2, 3, 4, 5, 6, 7].map(function () { var b = blob(0.09, 0, 'rgba(255,214,120,1)'); b.rotation.x = 0; scene.add(b); return b; });
    var L = [lbl('레시피 검색 중…', 'think', V(5.6, 2.3, -1.0))];
    var H = Math.PI / 2;
    function cl(u) { return Math.max(0, Math.min(1, u)); }
    function seg(A, a, b) { return cl((A - a) / (b - a)); }
    function mix(a, b, u) { return a + (b - a) * u; }
    function eo(u) { return 1 - Math.pow(1 - u, 3); }
    function back(u) { u = cl(u); var c = 1.70158; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); }
    function antic(A, t, d) { var u = (A - t) / d; return u > 0 && u < 1 ? Math.sin(Math.PI * u) * 0.13 : 0; }           // 움츠리기 (움직이기 전)
    function land(A, t) { var g = A - t; return g > 0 && g < 0.7 ? Math.exp(-g * 7) * Math.sin(g * 22) * 0.15 : 0; }        // 멈출 때 출렁
    function hop(A, t, d, h) { var u = (A - t) / d; return u > 0 && u < 1 ? 4 * u * (1 - u) * h : 0; }                        // 포물선 뛰기
    function squash(o, age, k) { var s = age > 0 && age < 0.6 ? Math.exp(-age * 7) * Math.sin(age * 26) * 0.24 : 0, pop = age < 0 ? 0 : back(age / 0.22); if (age > 8) pop = 1; o.scale.set(k * pop * (1 + s * 0.6), k * pop * (1 - s), k * pop * (1 + s * 0.6)); }
    // 로봇 연기표: 단계 n, 그 단계가 시작된 뒤 A초 → 자리 · 방향 · 동작 · 찌그러짐 · 뛰기 · 표정
    function act(n, A) {
      var p = { x: HOME, ry: 0, an: 'Idle', ts: 1, sq: 0, hop: 0, q: 0, e: 0, sad: 0, sur: 0 }, u;
      if (n === 0) {
        u = seg(A, 0, 2.3); p.x = mix(-9.2, HOME, 1 - (1 - u) * (1 - u));
        if (A < 2.2) { p.ry = H; p.an = 'Walking'; p.ts = 1.25; } else if (A < 4.3) p.an = 'Wave';
        p.sq = land(A, 2.25); p.q = A > 4.5 ? back((A - 4.5) / 0.3) : 0;
      } else if (n === 1) {
        if (A < 1.5) { p.x = mix(HOME, -2.6, ease(seg(A, 0.3, 1.5))); if (A > 0.3) { p.ry = -H; p.an = 'Running'; p.ts = 0.8; } }
        else if (A < 2.6) { p.x = -2.6; p.an = 'No'; p.ts = 0.9; }
        else if (A < 3.9) { p.x = mix(-2.6, 3.1, ease(seg(A, 2.6, 3.9))); p.ry = H; p.an = 'Running'; p.ts = 0.9; }
        else if (A < 4.9) { p.x = 3.1; p.an = 'No'; p.ts = 0.9; }
        else if (A < 5.7) { p.x = mix(3.1, HOME, ease(seg(A, 4.9, 5.7))); p.ry = -H; p.an = 'Walking'; p.ts = 1.3; }
        p.sq = antic(A, 0, 0.3) + land(A, 1.5) + land(A, 3.9) + land(A, 5.7); p.q = A < 5.7 ? 1 : cl(1 - (A - 5.7) / 0.2);
      } else if (n === 2) {
        p.hop = hop(A, 0.12, 0.42, 0.5); p.sq = land(A, 0.54) - (p.hop > 0 ? 0.08 : 0); p.sad = 0.9;
        if (A > 0.8 && A < 2.8) { p.an = 'No'; p.ts = 0.7; }
      } else if (n === 3) {
        p.sad = 0.6; u = seg(A, 0.3, 1.1);
        if (A < 1.1) { p.x = mix(HOME, 10, u * u); if (A > 0.3) { p.ry = H; p.an = 'Running'; p.ts = 1.1; } }
        else if (A < 2.2) { p.x = 10; p.ry = H; }
        else if (A < 3.0) { p.x = mix(10, HOME, eo(seg(A, 2.2, 3.0))); p.ry = -H; p.an = 'Running'; p.ts = 1.1; }
        p.sq = antic(A, 0, 0.3) + land(A, 3.0);
      } else if (n === 4) {
        p.ry = A < 1.3 ? 0.45 * ease(seg(A, 0.2, 0.7)) : -0.35 * ease(seg(A, 1.3, 1.7));
        p.sq = antic(A, 1.25, 0.22) + land(A, 1.95) - (hop(A, 1.47, 0.48, 1) > 0 ? 0.1 : 0); p.hop = hop(A, 1.47, 0.48, 0.75);
        p.sur = cl((A - 1.3) * 4); p.e = A > 1.45 ? back((A - 1.45) / 0.25) : 0;
        if (A > 2.3) p.an = 'Yes';
      } else if (n === 5) {
        var cur = null; FL.forEach(function (f) { var d = f[0].userData; if (A > d.t0 && A < d.t0 + 1.2) cur = d; p.sq += land(A, d.t0 + 0.8) * 0.45; });
        p.ry = cur ? Math.max(-0.6, Math.min(0.6, (cur.seat.x - HOME) * 0.22)) : 0; p.sur = 0.3;
      } else if (n === 6) {
        p.x = mix(HOME, K.SVX, ease(seg(A, 0.15, 0.85)));
        if (A < 0.85) { if (A > 0.15) { p.ry = -H; p.an = 'Walking'; p.ts = 1.5; } } else { p.an = 'Punch'; p.ts = 1.15; }
        p.sq = antic(A, 0, 0.18) + land(A, 0.85);
      } else {
        p.x = mix(K.SVX, HOME, ease(seg(A, 0, 0.6)));
        if (A < 0.6) { p.ry = H; p.an = 'Walking'; p.ts = 1.5; } else if (A > 1.5) p.an = 'ThumbsUp';
        p.hop = hop(A, 0.95, 0.5, 0.8); p.sq = land(A, 0.6) + antic(A, 0.75, 0.2) + land(A, 1.45) - (p.hop > 0 ? 0.1 : 0); p.sur = 0.35;
      }
      return p;
    }
    var _hp = V(0, 0, 0), _hq = new THREE.Quaternion();
    var S = { scene: scene, camera: cam, labels: L, st: 0, a: 0, time: 0, noBg: true, drift: 0.3, ry: 0, linear: true, exposure: 0.92,
      fx: { focus: [0.5, 0.5], r: [1.05, 0.62], blur: 0.3, bloom: 0.16, bloomT: 0.94, grain: 0.012, vig: 0.26 },
      setStep: function (n, snap) { S.st = n; S.a = snap && REDUCED ? 99 : 0; },
      finish: function () { S.a = 99; },
      update: function (dt, t, snap) {
        if (!snap) { S.a += dt; S.time += dt; }
        var n = S.st, A = S.a, live = !snap;
        // 로봇 연기
        var p, wokHeld = false;
        if (RCH) {   // 클릭 → 로봇 박자 (pose는 시간만의 함수: ← · 줄인 움직임은 끝 모습)
          var c = CLICK[Math.min(7, n)], bi = RBI.indexOf(c.b);
          wokHeld = c.wok && (n > 5 || A > FL[0][0].userData.t0 + 0.8 || snap);
          var P = RCH.pose(bi, (snap || c.end || REDUCED) ? 99 : A); P.wokOn = wokHeld;
          RCH.apply(P, t);
          p = { hop: 0, q: 0, e: 0 };
        } else {
          p = act(n, A); robot.position.x = p.x; robot.position.z = RZ;
          S.ry += (p.ry - S.ry) * (snap ? 1 : damp(10, dt)); robot.rotation.y = S.ry;
        }
        if (R) {
          play(R, p.an, p.ts, snap);
          if (snap) { var ac = R.acts[R.cur]; if (ac) { ac.time = R.cur === 'ThumbsUp' ? ac.getClip().duration * 0.55 : R.cur === 'Punch' ? ac.getClip().duration * 0.4 : 0.3; } R.mixer.update(0); } else R.mixer.update(dt);
          var breathe = (R.cur === 'Idle' && live) ? Math.sin(t * 2.2) * 0.012 : 0, s = p.sq + breathe;
          R.body.position.y = p.hop; R.body.scale.set(1 + s * 0.55, 1 - s, 1 + s * 0.55);
          if (R.face) { var md = R.face.morphTargetDictionary, mi = R.face.morphTargetInfluences;
            if (md.Surprised !== undefined) mi[md.Surprised] += (p.sur - mi[md.Surprised]) * (snap ? 1 : damp(8, dt));
            if (md.Sad !== undefined) mi[md.Sad] += (p.sad - mi[md.Sad]) * (snap ? 1 : damp(6, dt)); }
          if (R.headEnd) { robot.updateMatrixWorld(true); R.headEnd.getWorldPosition(_hp); R.headEnd.getWorldQuaternion(_hq); R.hat.position.copy(_hp); R.hat.quaternion.copy(_hq); R.hat.scale.set(1 + s * 0.5, 1 - s, 1 + s * 0.5); R.hat.visible = true; } else R.hat.visible = false;
        }
        rsh.visible = qm.visible = em.visible = !RCH;
        rsh.position.set(robot.position.x, Y + 0.016, RZ + 0.05); rsh.material.opacity = 1 - Math.min(0.5, p.hop * 0.6); rsh.scale.setScalar(1 - Math.min(0.3, p.hop * 0.35));
        var head = V(robot.position.x + 1.0, Y + 4.25 + p.hop, RZ + 0.2);
        qm.position.copy(head); qm.position.y += live ? Math.sin(t * 3) * 0.05 : 0; face(qm, cam); qm.rotation.z += 0.18; qm.scale.setScalar(Math.max(0.001, p.q));
        em.position.copy(head); face(em, cam); em.scale.setScalar(Math.max(0.001, p.e));
        L[0].el.style.opacity = n === 3 && A > 1.0 && A < 2.2 ? 1 : 0;
        // 맨밥 · 따로 김치
        var gone = n >= 4 ? cl(1 - A / 0.35) : 1; if (n >= 5) gone = 0;
        var BW = RCH ? 1.6 : 6.0;
        bowl.visible = ((n === 1 && (A > BW || snap)) || n === 2 || n === 3 || n === 4) && gone > 0.01;
        bowl.position.copy(serveA); squash(bowl, n === 1 && !snap ? A - BW : 9, gone);
        var SW = RCH ? 4.2 : 3.2;
        side.visible = ((n === 3 && (A > SW || snap)) || n === 4) && gone > 0.01;
        side.position.copy(serveB); squash(side, n === 3 && !snap ? A - SW : 9, gone);
        // 레시피 카드: 휙 날아와 펼쳐지고, 다음부터는 조리대 왼쪽 받침에 세워 둬요
        var rc = recipe; rc.visible = n >= 4; stand.visible = n >= 5;
        if (n === 4) {
          var u = ease(cl((A - 0.3) / 1.0)), p0 = V(8, 6.5, 3), p2 = V(HOME - 1.75, 1.55, 0.3), p1 = V(2, 6.0, 2.5);
          rc.position.set((1 - u) * (1 - u) * p0.x + 2 * (1 - u) * u * p1.x + u * u * p2.x, (1 - u) * (1 - u) * p0.y + 2 * (1 - u) * u * p1.y + u * u * p2.y + (live ? Math.sin(t * 1.6) * 0.04 * u : 0), (1 - u) * (1 - u) * p0.z + 2 * (1 - u) * u * p1.z + u * u * p2.z);
          var open = back(cl((A - 1.25) / 0.4)); rc.scale.set(2.0 * (0.2 + 0.8 * open), 2.0 * (0.7 + 0.3 * u), 2.0); rc.rotation.set(-0.12, (1 - u) * 2.5 + 0.18, (1 - u) * 0.6 - 0.04);
          rc.userData.halo.material.opacity = cl(open) * 0.9;
        } else if (n > 4) { rc.position.set(-3.75, 0.72, 0.05); rc.scale.setScalar(1.55); rc.rotation.set(-0.2, 0.3, 0); rc.userData.halo.material.opacity = 0.35; }
        face(rc.userData.halo, cam);
        // 도구 · 재료: 하나씩 포물선으로 날아와 착 (빛 꼬리 + 찌그러졌다 펴짐)
        var flash = 0;
        FL.forEach(function (f) {
          var o = f[0], d = o.userData, u2 = n === 5 ? cl((A - d.t0) / 0.8) : n > 5 ? 1 : 0, q = u2 * u2 * (3 - 2 * u2);
          o.visible = u2 > 0;
          var mid = d.from.clone().lerp(d.seat, 0.55); mid.y += 2.6;
          o.position.set((1 - q) * (1 - q) * d.from.x + 2 * (1 - q) * q * mid.x + q * q * d.seat.x, (1 - q) * (1 - q) * d.from.y + 2 * (1 - q) * q * mid.y + q * q * d.seat.y, (1 - q) * (1 - q) * d.from.z + 2 * (1 - q) * q * mid.z + q * q * d.seat.z);
          var age = n === 5 ? A - d.t0 - 0.8 : n > 5 ? 9 : -1;
          squash(o, u2 < 1 ? 9 : age, d.k); if (u2 < 1) o.rotation.set((1 - q) * 3, (1 - q) * 4, 0); else o.rotation.set(0, 0.3, 0);
          ringPop(d.ring, d.seat, age, 0.7); d.ring.rotation.x = -Math.PI / 2; d.ring.position.y += 0.03;
          flash = Math.max(flash, age > 0 && age < 0.5 ? 1 - age / 0.5 : 0);
          var tp = d.trail.geometry.attributes.position;
          for (var k = 0; k < 10; k++) { var q0 = cl(u2 - k * 0.035), qq = q0 * q0 * (3 - 2 * q0), vis = u2 > 0 && u2 < 1; tp.setXYZ(k, vis ? (1 - qq) * (1 - qq) * d.from.x + 2 * (1 - qq) * qq * mid.x + qq * qq * d.seat.x : 0, vis ? (1 - qq) * (1 - qq) * d.from.y + 2 * (1 - qq) * qq * mid.y + qq * qq * d.seat.y : -50, vis ? (1 - qq) * (1 - qq) * d.from.z + 2 * (1 - qq) * qq * mid.z + qq * qq * d.seat.z : 0); }
          tp.needsUpdate = true;
        });
        if (RCH && wokHeld) wok.visible = false;   // 로봇이 든 웍이 내려앉은 그 웍이에요
        // 요리: 불 · 웍 흔들기 · 뒤집개 · 밥알 튀기 · 지글 불꽃 · 만화 김 (v3: 반복 입자 · 김 · 반짝이는 꺼요)
        var cooking = n === 6 && A > 0.85, SV = K.SVX;
        if (!RCH && n === 6 && A > 0.4) { spat.position.set(SV + 0.25, 0.62 + (live ? Math.sin(t * 9) * 0.12 : 0.06), 0.0); spat.rotation.set(-0.9, 0.2, 0.3); }
        if (n >= 7) { rice.visible = false; egg.visible = false; }
        K.fire.material.opacity = cooking && !RCH ? 0.85 : 0;
        wok.userData.rice.visible = cooking;
        if (n >= 6) { wok.rotation.z = cooking && live ? Math.sin(t * 7) * 0.12 : 0; wok.position.y = 0.14 + (cooking && live ? Math.abs(Math.sin(t * 7)) * 0.06 : 0); }
        for (var i = 0; i < tossN; i++) { var ph = ((live ? t * 1.3 : 0.45) + i / tossN) % 1, an = i * 2.39996, sp = 0.2 + (i % 5) * 0.06; tossP[i * 3] = SV + Math.cos(an) * sp * ph; tossP[i * 3 + 1] = cooking ? 0.45 + ph * 1.6 - ph * ph * 1.8 : -50; tossP[i * 3 + 2] = 0.2 + Math.sin(an) * sp * ph * 0.6; }
        tossG.attributes.position.needsUpdate = true; toss.visible = !RCH;
        for (var j = 0; j < sizzN; j++) { var ph2 = ((live ? t * 2.2 : 0.3) + j / sizzN) % 1, an2 = j * 1.7; sizzP[j * 3] = SV + Math.cos(an2) * (0.5 + ph2 * 0.5); sizzP[j * 3 + 1] = cooking ? 0.3 + ph2 * 0.6 : -50; sizzP[j * 3 + 2] = 0.2 + Math.sin(an2) * (0.4 + ph2 * 0.4); }
        sizzG.attributes.position.needsUpdate = true; sizz.visible = false;
        var served = n >= 7 && A > 0.6;
        steam.forEach(function (pf, k) { var ph3 = ((live ? t * 0.35 : 0.4) + k / 3) % 1, src = n >= 7 ? V(HERO.x + 0.1, 0.55, HERO.z) : V(SV, 0.55, 0.2), on = cooking || served; pf.position.set(src.x + Math.sin(k * 2 + ph3 * 4) * 0.22, src.y + ph3 * 1.5, src.z - 0.1); pf.scale.setScalar(on ? (0.2 + ph3 * 0.42) * (1 - ph3 * 0.75) : 0.001); });
        // 완성 접시 · 반짝이
        steam.forEach(function (pf) { pf.visible = false; });
        plate.visible = served && !RCH; plate.position.copy(HERO); squash(plate, n >= 7 ? A - 0.6 : -1, 1);
        spark.forEach(function (b, k) { var a2 = k / 8 * 6.28 + (live ? t * 0.7 : 0.4); b.position.set(HERO.x + Math.cos(a2) * 1.15, 0.55 + Math.sin(t * 2 + k) * 0.22, HERO.z + Math.sin(a2) * 0.5); b.material.opacity = served && A > 0.8 ? (snap ? 0.8 : 0.45 + 0.45 * Math.sin(t * 5 + k)) : 0; face(b, cam); });
        // 햇살 · 먼지 · 등
        K.beams.forEach(function (b) { b.material.opacity = 0.085; });   // v3: 가만히
        K.lamps.forEach(function (g) { face(g.userData.glow, cam); });
        if (false) { var mp = K.mp; for (var m = 0; m < mp.length; m += 3) { mp[m + 1] += Math.sin(t * 0.5 + m) * 0.0015; mp[m] += 0.0012; if (mp[m] > K.WX + 4.4) mp[m] -= 4; } K.motes.geometry.attributes.position.needsUpdate = true; }
        S.fx.bloom = 0.16 + flash * 0.35 + (served ? 0.1 : 0);
        // 그림책 카메라: 무대처럼 조금 위에서. 장면마다 한 번만 천천히 다가가요
        var cp = n === 6 ? V(-0.9, 4.3, 10.6) : n === 4 ? V(-0.5, 4.0, 10.8) : n >= 7 ? V(0.7, 3.9, 9.9) : n === 5 ? V(0.5, 5.2, 13.6) : V(0.3, 5.0, 13.9);
        var cl2 = n === 6 ? V(-1.0, 0.95, -0.5) : n === 4 ? V(-0.5, 1.25, -0.6) : n >= 7 ? V(0.7, 0.85, -0.4) : n === 5 ? V(0.5, 0.75, -0.5) : V(0.3, 0.85, -0.6);
        if (!S.cp) { S.cp = cp.clone(); S.cl = cl2.clone(); }
        var kk = snap ? 1 : camK(2.4, A, dt); S.cp.lerp(cp, kk); S.cl.lerp(cl2, kk); cam.position.copy(S.cp); cam.lookAt(S.cl);
        S.focusObj = n === 4 ? recipe : n === 6 ? wok : n >= 7 ? plate : robot;
      } };
    spark.forEach(function (b) { b.visible = false; });
    S.setStep(0, true);
    return S;
  }

  /* 종이 인형 로봇 (예비): 진짜 그래픽 칩이 없는 PC(소프트웨어 렌더링)에서 쓰는 가벼운 판. 같은 여덟 박자
     그림 조각은 build.py가 PUPPET에 넣어요 (deck-v3-src/puppet/*.webp). 반복 움직임 없음, 카메라 고정 */
  var PUPPET = /*__PUPPET__*/{};
  function robotPuppetScene() {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 120);
    scene.background = new THREE.Color(0x221a13);
    function ptex(key) { var t = new THREE.Texture(); var im = new Image(); im.onload = function () { t.image = im; t.needsUpdate = true; }; if (PUPPET[key]) im.src = PUPPET[key]; t.minFilter = THREE.LinearFilter; return t; }
    function pplane(key, w, h, o) { return new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial(Object.assign({ map: ptex(key), transparent: true, depthWrite: false }, o || {}))); }
    var PART = { head: ['head', 453, 428, 227, 418], torso: ['torso', 432, 355, 216, 346], armL: ['armL', 145, 360, 86, 42], armR: ['armR', 144, 363, 58, 42], wok: ['wok', 596, 234, 548, 62], base: ['base', 436, 262, 218, 254] };
    function part(name, ord) {
      var P = PART[name], w = P[1] / 100, h = P[2] / 100, ox = (P[1] / 2 - P[3]) / 100, oy = -(P[2] / 2 - P[4]) / 100, g = new THREE.Group();
      var sh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: ptex(P[0]), color: 0x000000, transparent: true, opacity: 0.28, depthWrite: false }));
      sh.position.set(ox + 0.07, oy - 0.1, -0.02); sh.renderOrder = ord; g.add(sh);
      var m = pplane(P[0], w, h); m.position.set(ox, oy, 0); m.renderOrder = ord + 1; g.add(m); return g;
    }
    var wall = pplane('kitchen', 46.4, 26.1, { transparent: false, depthWrite: true, color: 0x9a9088 }); wall.position.set(0, 6.98, -10); wall.renderOrder = -10; scene.add(wall);
    var LW = 34, LH = 34 * 106 / 1672, lip = pplane('lip', LW, LH, { transparent: false }); lip.position.set(0, -0.29 - LH / 2, 3); lip.renderOrder = 100; scene.add(lip);
    var root = new THREE.Group(), body = new THREE.Group(); scene.add(root); root.add(body);
    var base = part('base', 10); base.position.z = -0.05; body.add(base);
    var upper = new THREE.Group(); upper.position.y = 2.12; body.add(upper); upper.add(part('torso', 20));
    var neck = new THREE.Group(); neck.position.set(0, 3.0, 0.25); upper.add(neck);
    var armL = new THREE.Group(); armL.position.set(-1.92, 2.36, 0.12); upper.add(armL); armL.add(part('armL', 30));
    var armR = new THREE.Group(); armR.position.set(1.92, 2.36, 0.14); upper.add(armR);
    var wokG = new THREE.Group(); wokG.position.set(0.27, -2.58, -0.05); armR.add(wokG); wokG.add(part('wok', 40));
    armR.add(part('armR', 50)); neck.add(part('head', 60));
    cam.position.set(0, 5.74, 30.6); cam.lookAt(0, 5.74, 0);
    var HOME = 4.6;
    function c01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
    function seg(t, a, d) { return c01((t - a) / d); }
    function bump(u) { return u <= 0 || u >= 1 ? 0 : Math.sin(Math.PI * u); }
    // 여덟 박자 (ms): 0 들어오기 · 1·2 갸우뚱 · 3 뒤돌아 다녀오기 · 4 찡긋(손 인사) · 5 웍이 손에 · 6 웍 휙휙 · 7 꾸벅
    function pose(n, t) {
      var o = { x: HOME, hop: 0, lean: 0, upX: 0, upR: 0, headZ: 0, headX: 0, aL: 0.08, aR: 0.32, wokR: 0, wokY: 0, wok: n >= 5 ? 1 : 0 };
      if (n === 0) { var u = seg(t, 0, 1800), e = EZ.out(u); o.x = HOME + 15 * (1 - e); o.hop = Math.abs(Math.sin(u * Math.PI * 3)) * 0.6 * (u < 1 ? 1 : 0); o.lean = -0.09 * (1 - e); }
      else if (n === 1 || n === 2) { var q = EZ.spring(seg(t, 0, TOK.m)); o.headZ = (n === 1 ? 0.22 : -0.22) * q; o.aL = 0.08 - 0.9 * q; o.aR = 0.32 + 0.9 * q; o.hop = bump(seg(t, 0, 380)) * 0.3; }
      else if (n === 3) { var a = seg(t, 200, 900), b = seg(t, 2300, 900); o.x = HOME + 6 * (EZ.inout(a) - EZ.inout(b)); o.lean = 0.06 * (bump(a) - bump(b)); }
      else if (n === 4) { var r1 = EZ.spring(seg(t, 0, TOK.m)), w = seg(t, TOK.m, 1800), down = EZ.inout(seg(t, 2600, TOK.m)); o.aL = 0.08 + (-2.55 + Math.sin(w * Math.PI * 4) * 0.25 * (w < 1 ? 1 : 0) - 0.08) * r1 * (1 - down); o.headZ = 0.13 * r1 * (1 - down); }
      else if (n === 5) { o.wok = EZ.spring(seg(t, 300, TOK.m)); o.aR = 0.32 + 0.3 * o.wok; }
      else if (n === 6) { var up = EZ.spring(seg(t, 0, TOK.m)); o.aR = 0.32 + 0.73 * up; o.aL = 0.08 + 0.37 * up; for (var k = 0; k < 3; k++) { var tu = seg(t, 700 + k * 820, 640); o.wokY += bump(c01(tu * 3)) * 0.32; o.wokR += bump(c01(tu * 3)) * 0.22; o.headX += bump(tu) * -0.08; } }
      else { var bw = EZ.inout(seg(t, 200, TOK.l)), rise = EZ.spring(seg(t, 1900, TOK.l)), d = bw * (1 - rise); o.upX = 0.62 * d; o.headX = 0.35 * d; o.aL = 0.08 + 0.42 * d; o.aR = 0.32 + 0.28 * d; o.hop = bump(seg(t, 2500, 520)) * 0.5; }
      return o;
    }
    var S = { scene: scene, camera: cam, labels: [], st: 0, a: 0, noBg: true, noDrift: true, puppet: true, fx: { bloom: 0, blur: 0, grain: 0, vig: 0.2 },
      setStep: function (n, snap) { S.st = n; S.a = (snap && (REDUCED || V3DIR < 0)) ? 99 : 0; },
      finish: function () { S.a = 99; },
      update: function (dt, t, snap) {
        if (!snap) S.a += dt;
        var o = pose(Math.min(7, S.st), (snap || REDUCED) ? 1e6 : S.a * 1000);
        root.position.set(o.x, o.hop, 0); root.rotation.z = o.lean;
        upper.rotation.x = o.upX; upper.rotation.z = o.upR; neck.rotation.z = o.headZ; neck.rotation.x = o.headX;
        armL.rotation.z = o.aL; armR.rotation.z = o.aR;
        wokG.visible = o.wok > 0.01; wokG.scale.setScalar(Math.max(0.001, o.wok)); wokG.rotation.z = -o.aR + 0.12 + o.wokR; wokG.position.y = -2.58 + o.wokY;
      } };
    S.setStep(0, true);
    return S;
  }

  /* 로봇 고르기: ?robot=3d · ?robot=puppet · 기본은 자동(소프트웨어 렌더링이면 종이 인형). R 키로 바로 바꿔요 */
  var ROBOT_Q = /[?&]robot=puppet/.test(location.search) ? 'puppet' : /[?&]robot=3d/.test(location.search) ? '3d' : 'auto';
  var ROBOT_MODE = null;
  function softGL() {
    try { var g = GL.r.getContext(), ext = g.getExtension('WEBGL_debug_renderer_info'), s = ext ? g.getParameter(ext.UNMASKED_RENDERER_WEBGL) : ''; return /SwiftShader|llvmpipe|Basic Render|Software/i.test(String(s)); } catch (e) { return false; }
  }
  SCENES.robot = function (el) {
    if (!ROBOT_MODE) ROBOT_MODE = ROBOT_Q !== 'auto' ? ROBOT_Q : (softGL() ? 'puppet' : '3d');
    var S = ROBOT_MODE === 'puppet' ? robotPuppetScene() : robot3dScene(el);
    S.mode = ROBOT_MODE;
    if (S.mode === '3d' && ROBOT_Q === 'auto') {   // 처음 1초 동안 초당 20장이 안 되면 종이 인형으로 바꿔요
      var u0 = S.update, n0 = 0, t0 = 0;
      S.update = function (dt, t, snap) { u0(dt, t, snap); if (!snap && !S.checked) { n0++; t0 += dt; if (t0 >= 1) { S.checked = true; if (n0 < 20) setTimeout(function () { robotSwitch('puppet'); }, 0); } } };
    }
    return S;
  };
  function robotSwitch(mode) {
    ROBOT_MODE = mode || (ROBOT_MODE === 'puppet' ? '3d' : 'puppet');
    delete GL.cache.robot;
    var s = slides[cur];
    if (s && s.getAttribute('data-scene') === 'robot') { var lb = s.querySelector('.labels'); while (lb && lb.firstChild) lb.removeChild(lb.firstChild); sceneStep(s, step, true); }
  }

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
    var hlA = blob(1.6, 0, 'rgba(217,168,92,0.28)'), hlB = blob(1.6, 0, 'rgba(217,168,92,0.28)'); hlA.position.copy(aiA.position); hlB.position.copy(aiB.position); hlA.rotation.x = hlB.rotation.x = 0; scene.add(hlA); scene.add(hlB);
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
        S.pu = snap ? 0.55 : (((S.pu + dt * 0.28) % 1) + 1) % 1; if (!(S.pu >= 0)) S.pu = 0;   // 멈췄다 다시 돌 때 dt가 음수여도 곡선 밖으로 나가지 않게
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
      for (var i = 0; i < 5; i++) { var y = 74 + i * 66; c.fillStyle = i === 2 ? 'rgba(217,168,92,.45)' : 'rgba(0,0,0,0)'; c.fillRect(12, y - 8, w - 24, 58); c.fillStyle = '#2b2019'; c.font = '800 24px ' + FONT; c.fillText((i + 1) + '.', 22, y); c.fillStyle = '#b3a08a'; c.fillRect(60, y + 6, 200 - i * 12, 9); c.fillRect(60, y + 26, 150, 9); }
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
    var cloudGlow = blob(2.6, 0, 'rgba(217,168,92,0.3)'); cloudGlow.rotation.x = 0; cloudGlow.position.copy(cloud.position); scene.add(cloudGlow);
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
    var phGlow = blob(0.2, 0, 'rgba(143,196,214,0.8)'); phGlow.rotation.x = 0; phGlow.position.copy(phPt); scene.add(phGlow);
    var thinking = [0, 1, 2].map(function (i) { var d = noSh(sph(0.12, Bm(P.amber, { transparent: true, opacity: 0 }))); d.position.set(clPt.x - 0.26 + i * 0.26, clPt.y - 0.85, clPt.z + 0.7); d.scale.setScalar(0.55); scene.add(d); return d; });
    var L = [lbl('안경 카메라', 'tag cool', U.glasses.userData.cam, [0.16, 0.05, 0]), lbl('주머니 속 휴대폰', 'tag cool', U.phone, [0.2, -0.05, 0]),
      lbl('멀리 있는 AI', 'tag ai', cloud, [0, 1.05, 0]), lbl('귀 속 이어폰', 'tag cool', U.bud, [0.17, -0.04, 0]),
      lbl('<i class="hop1"></i>가까운 무선', 'tag hop cool', c1.getPointAt(0.5), [-0.2, 0, 0.05]), lbl('<i class="hop2"></i>휴대폰 인터넷', 'tag hop ai', c2.getPointAt(0.5), [0, 0.22, 0])];
    var clockEl = slideEl.querySelector('[data-clock]');
    var T = [0, 0, 1, 2, 5, 6, 7, 7];
    // 카메라 자리 [위치, 바라보는 곳]
    var Wd = [V(1.8, 1.55, 4.5), V(1.55, 0.98, -0.9)], N1 = [V(1.25, 1.8, 2.15), V(0.05, 0.92, 0.3)], N2 = [V(1.05, 1.6, 2.0), V(0.12, 1.12, 0.05)];
    var CAM = [Wd, N1, N2, Wd, [V(2.0, 1.4, 3.5), V(3.6, 0.95, -2.6)], Wd, N2, [V(2.1, 1.9, 3.8), V(0.7, 1.0, -0.2)]];
    var S = { scene: scene, camera: cam, labels: L, st: 0, p: 0, clock: 0, cp: CAM[0][0].clone(), cl: CAM[0][1].clone(),
      setStep: function (n, snap) {
        if (n !== S.st || snap) S.p = snap ? 0.62 : 0;
        S.st = n;
        if (snap) { S.cp.copy(CAM[n][0]); S.cl.copy(CAM[n][1]); S.clock = T[n]; }
      },
      update: function (dt, t, snap) {
        var n = S.st, k = snap ? 1 : camK(2.4, S.p * 2.6, dt);
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
      var sh = blob(0.62, 0.5); sh.position.set(X[i], -0.835, 0); scene.add(sh);   // 받침 위에 떠 있는 물건 밑의 그늘 (motion QA: 그늘이 없어 붙여 놓은 것처럼 보였어요)
    });
    if (objs[2].userData.waves) objs[2].userData.waves.forEach(function (w, i) { w.material.opacity = 0.6 - i * 0.18; });
    var desk = woodTop(16.5, 4.2); desk.position.y = -0.9 - 0.06; scene.add(desk); fogFor(scene, 'hall', 18, 40);
    var D = [['카메라 안경', '안경테에 작은 카메라.<br>문제를 찍어요'], ['화면 안경', '렌즈 안쪽 작은 화면.<br>답이 떠요'], ['초소형 이어폰', '귀 속에 쏙.<br>답을 소리로 읽어 줘요'],
      ['휴대폰', '주머니 속에서<br>보내고 받아요'], ['스마트워치', '손목 위 작은 화면.<br>글자를 보여 줘요'], ['멀리 있는 AI', '멀리서 문제를 읽고<br>답을 만들어요']];
    var L = D.map(function (d, i) { return lbl('<b>' + d[0] + '</b><span>' + d[1] + '</span>', 'kc', V(X[i], -2.3, 0.6)); });
    cam.position.set(0, 1.6, 16.2); cam.lookAt(0, -0.75, 0);
    var S = { scene: scene, camera: cam, labels: L, st: 0,
      setStep: function (n) { S.st = n; S.focusObj = n ? objs[n - 1] : null; if (S.fx) { S.fx.r = n ? [0.13, 0.3] : [0.7, 0.62]; S.fx.blur = n ? 0.7 : 0.4; } },
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

  /* 마무리: 표지와 짝. 무기 카드 여섯 장이 하나씩 날아와 두 줄로 자리 잡아요 (표지 = 지나갈 일, 마무리 = 손에 쥔 무기) */
  SCENES.made = function () {
    var scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 16 / 9, 0.5, 100);
    cam.position.set(0, 0.4, 19); cam.lookAt(0.4, 0, 0);
    rig(scene, false, 9, 5.5, 0);
    var grp = new THREE.Group(); grp.position.set(5.65, -0.1, 0); grp.scale.setScalar(0.92); scene.add(grp);
    var names = [['게임', 'gamepad-2'], ['슬라이드', 'presentation'], ['영상', 'clapperboard'], ['수업 도구', 'timer'], ['데이터', 'chart-column'], ['법 확인', 'scale']];
    var pos = [[-2.45, 1.15, 0.3], [0, 1.45, -0.2], [2.45, 1.15, 0.3], [-2.45, -1.25, 0.1], [0, -0.95, -0.3], [2.45, -1.25, 0.1]];
    var cards = names.map(function (n, i) { var c = card(2.15, 1.5, P.amber, n[0], null, n[1]); c.userData = { p: V(pos[i][0], pos[i][1], pos[i][2]), ph: i * 1.1, t0: TOK.sec(TOK.xs) + i * TOK.sec(TOK.gap) }; grp.add(c); return c; });
    var glow = blob(4.6, 0, 'rgba(242,169,78,0.12)'); glow.rotation.x = 0; glow.position.z = -1.2; grp.add(glow);
    var sh = catcher(14, 8, 0.12); sh.position.set(0, -2.6, 0); grp.add(sh);
    var S = { scene: scene, camera: cam, labels: [], a: 0,
      setStep: function (n, snap) { if (snap) S.a = (REDUCED || V3DIR < 0) ? 9 : 0; },
      finish: function () { S.a = 9; },
      update: function (dt, t, snap) {
        if (!snap) S.a += dt;
        cards.forEach(function (c) {
          // v3: 표지와 같은 움직임 값(TOK.m · 간격 TOK.gap) · 같은 통통 곡선 (짝을 이루는 처음과 끝)
          var u = c.userData, q = Math.max(0, Math.min(1, (S.a - u.t0) / TOK.sec(TOK.m))), e = 1 - Math.pow(1 - q, 3), live = !snap;
          c.visible = q > 0;
          c.position.set(u.p.x + (1 - e) * 5, u.p.y + (1 - e) * (u.p.y > 0 ? 2.4 : -2.4), u.p.z - (1 - e) * 6);
          c.rotation.set(-0.05 + (live ? Math.sin(t * 0.5 + u.ph) * 0.04 : 0), -0.22 + (1 - e) * 1.4 + (live ? Math.sin(t * 0.4 + u.ph) * 0.06 : 0), (1 - e) * 0.3);
          c.scale.setScalar(Math.max(0.001, q >= 1 ? 1 : EZ.bounce(q)));
        });
        glow.material.opacity = Math.min(1, S.a / 1.5);
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
    else if (k === 't' || k === 'T') { var tm = slides[cur].querySelector('.timer'); if (tm && tm.toggle) tm.toggle(); else if (slides[cur].querySelector('.stw')) swToggle(); }
    else if ((k === 'r' || k === 'R') && slides[cur].getAttribute('data-scene') === 'robot') robotSwitch();
    else if ((k === 'r' || k === 'R') && slides[cur].querySelector('.stw')) swReset();
    else if ((k === 'l' || k === 'L') && slides[cur].querySelector('.stw')) swLap();
    else if (/^[0-9]$/.test(k)) { jump += k; }
    else if (k === 'Enter' && jump) { go(+jump - 1, 0); jump = ''; }
    else if (k === 'Escape') { jump = ''; }
  });
  stage.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('.timer,.stw,.relay')) return; if (e.clientX < window.innerWidth * 0.2) prev(); else next(); });
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
    freeze: function (on) { if (on) { stopLoop(); if (document.getAnimations) document.getAnimations().forEach(function (a) { try { a.finish(); } catch (e) {} }); document.documentElement.classList.add('freeze'); if (GL.active) renderOnce(); } else { document.documentElement.classList.remove('freeze'); if (GL.active) startLoop(); } },
    active: function () { return GL.active; }, at: function (a) { var S = GL.active; if (!S) return -1; if (S.a !== undefined) S.a = a; if (S.age !== undefined) S.age = a; return a; }, redraw: function () { if (GL.active) renderOnce(); },
    models: function () { var o = {}; Object.keys(MDL).forEach(function (k) { var n = []; MDL[k].traverse(function (m) { if (m.isMesh) n.push(m.name + ':' + m.material.name); }); var b = new THREE.Box3().setFromObject(MDL[k]); o[k] = { meshes: n, min: b.min.toArray(), max: b.max.toArray() }; }); return o; },
    find: function (kind) { for (var i = 0; i < slides.length; i++) if (slides[i].getAttribute('data-scene') === kind) return i; return -1; },
    // 점검용: 3D 물건 하나를 따로 찍어요 (shoot.py --closeup)
    closeup: function (name, warm) {
      var K = { '카메라 안경': function () { return glassesMesh({ cam: true }); }, '화면 안경': function () { var g = glassesMesh({ disp: true }); g.userData.disp.material.opacity = 0.95; return g; },
        '초소형 이어폰': function () { var e = earbudMesh(1); e.userData.waves.forEach(function (w, i) { w.material.opacity = 0.7 - i * 0.2; }); return e; }, '휴대폰': function () { return phoneMesh(); },
        '스마트워치': watchMesh, '노트북': laptopMesh, '클라우드 AI': function () { return cloudMesh(true); }, '키보드와 손': keyboardMesh, '모니터 대화창': monitorMesh,
        '학생과 책상': studentMesh, '안경 모델(원본)': function () { return modelOf('specs', 2.2); }, '웍': wokMesh, '밥그릇': function () { var b = bowlMesh(); var r = riceMound(380, 0.38, 0.2, null, 3); r.position.y = 0.2; b.add(r); return b; },
        '김치볶음밥': function () { var p = plateMesh(0.8); var f = friedRice(); f.position.y = 0.05; p.add(f); return p; }, '김치 병': jarMesh, '셰프 레시피': recipeCard, '셰프 AI': chefAI, '하네스 상자': harnessCase, '로봇 (툰)': function () { var src = MDL.robot; if (!src) return chefAI(); var home = src.parent, R = robotRig(); R.root.updateMatrixWorld(true); if (R.headEnd) { R.headEnd.getWorldPosition(R.hat.position); R.root.add(R.hat); } var g = new THREE.Group(); g.add(R.root); g.userData.home = home; g.userData.src = src; return g; }, '툰 웍': toonWok, '툰 김치볶음밥': function () { var p = toonPlate(0.8); var f = toonFriedRice(); f.position.y = 0.05; p.add(f); return p; },
        '연필': pencilMesh, '도구 카드': function () { return card(1.6, 1.1, P.terra, '게임', null, 'gamepad-2'); } };
      if (name === 'list') return Object.keys(K);
      var c = document.createElement('canvas'), r = new THREE.WebGLRenderer({ canvas: c, antialias: true, alpha: true, preserveDrawingBuffer: true });
      r.setSize(480, 400, false); r.setClearColor(0x000000, 0); r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
      if (/툰/.test(name)) { r.outputEncoding = THREE.sRGBEncoding; r.toneMapping = THREE.ACESFilmicToneMapping; }   // 툰 물건은 장면과 같은 색 다루기로
      var sc = new THREE.Scene(), o = K[name](), home = o.userData && o.userData.home; sc.add(o);
      if (IMG.env_hall || IMG.env_road) { var et = new THREE.Texture(IMG[warm && IMG.env_hall ? 'env_hall' : 'env_road'] || IMG.env_hall); et.mapping = THREE.EquirectangularReflectionMapping; et.needsUpdate = true; var pmg = new THREE.PMREMGenerator(r); sc.environment = pmg.fromEquirectangular(et).texture; pmg.dispose(); }
      var box = new THREE.Box3().setFromObject(o), ctr = box.getCenter(V(0, 0, 0)), sz = box.getSize(V(0, 0, 0)), R = Math.max(sz.x, sz.y, sz.z);
      rig(sc, !!warm, R * 2, ctr.x, ctr.z);
      var fl = catcher(R * 6, R * 6, 0.35); fl.position.set(ctr.x, box.min.y - 0.001, ctr.z); sc.add(fl);
      var cm = new THREE.PerspectiveCamera(30, 1.2, R * 0.01, R * 40);
      cm.position.set(ctr.x + R * 1.1, ctr.y + R * 0.75, ctr.z + R * 1.9); cm.lookAt(ctr);
      r.render(sc, cm);
      var url = c.toDataURL('image/png'); r.dispose(); if (home) home.add(o.userData.src || o.children[0]); return url;
    },
    state: function () { return { slide: cur, step: step, pr: GL.pr, shadowAuto: GL.r ? GL.r.shadowMap.autoUpdate : null, gl: GL.ok, reduced: REDUCED, fx: !!(GL.fx && GL.fxOn), assets: Object.keys(IMG).length, active: GL.active ? GL.active.kind : null }; }
  };
  function boot() { preload(function () { loadModels(start); }); }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(boot, boot); else boot();
})();
