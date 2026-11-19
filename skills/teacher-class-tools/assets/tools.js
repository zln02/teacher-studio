/* TS:CLASS-TOOLS RUNTIME. Offline single page: no network, nothing stored, nothing sent. Names typed here live only in this page. */
(function () {
  'use strict';
  var T = window.TOOL, D = T.data;
  var RM = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var stage = document.getElementById('stage'), main = document.getElementById('main');
  var API = { instant: false, off: 0, relayout: null, step: function () { return false; }, advance: function () {}, state: function () { return {}; } };
  window.TOOL_API = API;
  var soundOn = !!T.sound;
  var AC = null;
  var J = window.Juice || null;                /* Game Wow kit (shared/juice); everything below still works without it */
  var OSRM = RM, userRM = false;
  if (J) {
    J.install({ camera: main });
    J.hooks.reduced = function () { return RM; };
    J.hooks.muted = function () { return !soundOn; };
  }
  var ICONS = { '호랑이': '🐯', '토끼': '🐰', '거북이': '🐢', '독수리': '🦅', '돌고래': '🐬', '여우': '🦊', '판다': '🐼', '사자': '🦁' };
  var TEAMC = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9', '#8C8C8C', '#7A5195'];
  var HINT = '실제 이름보다 번호(1번, 2번…)를 쓰는 걸 추천해요. 입력한 내용은 이 화면에만 있고 저장하거나 어디로 보내지 않아요. 창을 닫으면 사라져요.';

  function h(tag, cls, text, attrs) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function btn(label, cls, fn) {
    var b = h('button', 'btn ' + (cls || ''), label, { type: 'button' });
    b.addEventListener('click', fn);
    return b;
  }
  function rnd(n) {
    if (window.crypto && crypto.getRandomValues) { var a = new Uint32Array(1); crypto.getRandomValues(a); return a[0] % n; }
    return Math.floor(Math.random() * n);
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = rnd(i + 1), t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function beep(freq, dur, delay) {
    if (!soundOn) return;
    try {
      AC = AC || new (window.AudioContext || window.webkitAudioContext)();
      var o = AC.createOscillator(), g = AC.createGain(), t0 = AC.currentTime + (delay || 0);
      o.type = 'sine'; o.frequency.value = freq;
      g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.25, t0 + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      o.connect(g); g.connect(AC.destination); o.start(t0); o.stop(t0 + dur + 0.05);
    } catch (e) { /* sound is optional */ }
  }
  /* sound by meaning: the kit's presets when present, the old beeps otherwise */
  function snd(name, o) {
    if (!soundOn) return;
    if (J) { J.sound.play(name, o); return; }
    var f = { click: [660, 0.1], pop: [700, 0.1], correct: [880, 0.15], wrong: [330, 0.1], fanfare: [1047, 0.4], tickLast: [900, 0.08], tick: [500, 0.05] }[name] || [660, 0.1];
    beep(f[0], f[1]);
  }
  function impact() {
    if (RM || API.instant) return;
    if (J) { J.fx.impactFrame(); J.kick(); return; }
    var d = h('div', 'impact');
    stage.appendChild(d);
    main.classList.remove('shake'); void main.offsetWidth; main.classList.add('shake');
    setTimeout(function () { if (d.parentNode) d.parentNode.removeChild(d); main.classList.remove('shake'); }, 450);
  }
  function fit(el, max, min, maxW) {
    var fs = max; el.style.fontSize = fs + 'px';
    while (el.scrollWidth > maxW && fs > min) { fs -= 8; el.style.fontSize = fs + 'px'; }
  }
  function parseLines(txt, limit) {
    var seen = {}, out = [], ls = txt.split(/\r?\n/);
    for (var i = 0; i < ls.length; i++) {
      var s = ls[i].replace(/\s+/g, ' ').trim().slice(0, 14);
      if (s && !seen[s]) { seen[s] = 1; out.push(s); }
    }
    return out.slice(0, limit);
  }
  function fmt(sec) {
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  /* shared editor: one name per line. Nothing is stored. */
  function editor(o) {
    var ov = h('div', 'ov'), card = h('div', 'ovcard card');
    card.appendChild(h('h2', '', o.title));
    card.appendChild(h('p', 'hint', o.hint || HINT));
    var ta = h('textarea', 'ta', null, { autocomplete: 'off', spellcheck: 'false', 'aria-label': o.title });
    ta.value = o.lines.join('\n');
    card.appendChild(ta);
    var num;
    if (o.fill) {
      var row = h('div', 'row');
      row.appendChild(h('span', 'hint', '인원 수'));
      num = h('input', 'num', null, { type: 'number', min: '1', max: String(o.limit), value: String(o.lines.length || 28), autocomplete: 'off', 'aria-label': '인원 수' });
      row.appendChild(num);
      row.appendChild(btn('번호로 채우기', 'sm', function () {
        var n = Math.max(1, Math.min(o.limit, parseInt(num.value, 10) || 1)), a = [];
        for (var i = 1; i <= n; i++) a.push(i + '번');
        ta.value = a.join('\n');
      }));
      card.appendChild(row);
    }
    var act = h('div', 'row');
    function close() { if (ov.parentNode) ov.parentNode.removeChild(ov); API.editor = null; }
    act.appendChild(btn('저장', 'main', function () {
      var ls = parseLines(ta.value, o.limit);
      if (ls.length < o.min) { msg.textContent = o.min + '줄 이상 적어 주세요.'; return; }
      close(); o.onSave(ls);
    }));
    act.appendChild(btn('닫기', '', close));
    var msg = h('span', 'hint', '');
    act.appendChild(msg);
    card.appendChild(act);
    ov.appendChild(card);
    main.appendChild(ov);
    API.editor = { ta: ta, close: close };
    ta.focus();
  }

  /* ---------- timer ---------- */
  function timer() {
    var mode = D.mode, total = D.minutes * 60000, elapsed = 0, running = false, last = 0, ended = false, raf = 0;
    var C = 2 * Math.PI * 350, lastSec = -1;
    var root = h('div', 'timer');
    var box = h('div', 'ringbox');
    box.innerHTML = '<svg viewBox="0 0 800 800" aria-hidden="true"><circle class="outer" cx="400" cy="400" r="388"/><circle class="trk" cx="400" cy="400" r="350"/>' +
      '<circle class="prog" cx="400" cy="400" r="350" stroke-dasharray="' + C.toFixed(2) + '" stroke-dashoffset="0"/><g class="orb"><circle class="orbit-dot" cx="400" cy="50" r="32"/></g></svg>';
    var digits = h('div', 'digits'), state = h('div', 'state')
    box.appendChild(digits); box.appendChild(state);
    var prog = box.querySelector('.prog'), orb = box.querySelector('.orb');
    var ctl = h('div', 'controls');
    var startB = btn('시작', 'main wide', toggle);
    ctl.appendChild(startB);
    ctl.appendChild(btn('처음으로', '', reset));
    var modeB = btn('', '', function () { mode = mode === 'countdown' ? 'stopwatch' : 'countdown'; reset(); });
    ctl.appendChild(modeB);
    var presetRow = h('div', 'controls wide');
    presetRow.style.cssText = 'grid-column:1/3;display:grid;grid-template-columns:repeat(4,1fr);width:auto;gap:12px';
    D.presets.forEach(function (m) { presetRow.appendChild(btn(m + '분', 'sm', function () { setMin(m); })); });
    ctl.appendChild(presetRow);
    var minus = btn('−1분', 'sm', function () { setMin(Math.max(1, total / 60000 - 1)); });
    var plus = btn('+1분', 'sm', function () { setMin(Math.min(180, total / 60000 + 1)); });
    ctl.appendChild(minus); ctl.appendChild(plus);
    root.appendChild(box); root.appendChild(ctl);
    main.appendChild(root);

    function now() { return performance.now() + API.off; }
    function setMin(m) { if (mode !== 'countdown') return; total = m * 60000; reset(true); }
    function reset(keep) {
      running = false; ended = false; elapsed = 0; cancelAnimationFrame(raf);
      if (!keep && mode === 'countdown' && !total) total = D.minutes * 60000;
      draw();
    }
    function toggle() {
      if (ended) { reset(true); return; }
      running = !running;
      if (running) { last = now(); snd('click'); raf = requestAnimationFrame(tick); } else cancelAnimationFrame(raf);
      draw();
    }
    function tick() {
      if (running) { var n = now(); elapsed += n - last; last = n; }
      if (mode === 'countdown' && elapsed >= total && !ended) {
        elapsed = total; running = false; ended = true;
        impact(); snd('fanfare');
        if (J && !RM && !API.instant) { var rc = J.center(box); J.burst(rc.x, rc.y, { count: 22, scale: 1.2 }); J.confetti({ count: 50 }); }
        if (!J) { beep(880, 0.35, 0); beep(880, 0.35, 0.5); beep(1175, 0.6, 1.0); }
      }
      if (mode === 'countdown' && running) { var sl = Math.ceil((total - elapsed) / 1000); if (sl !== lastSec) { lastSec = sl; if (sl <= 5 && sl > 0) snd('tickLast'); } }
      draw();
      if (running) raf = requestAnimationFrame(tick);
    }
    function draw() {
      var cd = mode === 'countdown', ms = cd ? Math.max(0, total - elapsed) : elapsed;
      var sec = cd ? Math.ceil(ms / 1000) : Math.floor(ms / 1000);
      digits.textContent = fmt(sec);
      var frac = cd ? (total ? ms / total : 0) : (elapsed % 60000) / 60000;
      prog.style.strokeDashoffset = (C * (1 - frac)).toFixed(2);
      orb.setAttribute('transform', 'rotate(' + (frac * 360).toFixed(2) + ' 400 400)');
      var warn = cd && running && sec <= D.warn_at && sec > 0;
      if (J) J.timerPulse(digits, cd && running ? ms / 1000 : 99, 'translateY(-58%)');
      root.classList.toggle('running', running); root.classList.toggle('warn', warn); root.classList.toggle('ended', ended);
      state.textContent = ended ? '시간 끝!' : warn ? '곧 끝나요!' : running ? '진행 중' : (elapsed > 0 ? '멈춤' : '준비');
      startB.textContent = ended ? '다시 하기' : running ? '멈춤' : (elapsed > 0 ? '이어서' : '시작');
      modeB.textContent = cd ? '스톱워치로' : '카운트다운으로';
      presetRow.style.display = minus.style.display = plus.style.display = cd ? '' : 'none';
      if (presetRow.style.display === '') presetRow.style.display = 'grid';
    }
    API.advance = function (ms) { API.off += ms; if (running) tick(); };
    API.step = function () { if (!running && !ended) { toggle(); return true; } return false; };
    API.state = function () { return { tool: 'timer', mode: mode, running: running, ended: ended, seconds: Math.round((mode === 'countdown' ? Math.max(0, total - elapsed) : elapsed) / 1000), warn: root.classList.contains('warn') }; };
    API.action = toggle;
    draw();
  }

  /* ---------- picker ---------- */
  function picker() {
    var items = D.items.slice(), noRep = D.no_repeat, pool = [], drawn = [], busy = false, cur = '', reveals = 0;
    var root = h('div', 'picker'), rev = h('div', 'reveal card'), lab = h('div', 'lab', D.label), big = h('div', 'picked', '?');
    rev.appendChild(lab); rev.appendChild(big);
    var bar = h('div', 'bar'), left = h('div', 'col'), chips = h('div', 'chips'), info = h('div', 'hint');
    left.appendChild(info); left.appendChild(chips);
    var go = btn('뽑기!', 'main', draw);
    var rep = btn('', 'sm', function () { noRep = !noRep; resetAll(); });
    var tb = document.getElementById('tb');
    tb.insertBefore(btn('목록 바꾸기', 'sm', edit), tb.firstChild);
    var rr = h('div', 'row'); rr.appendChild(rep); rr.appendChild(go);
    bar.appendChild(left); bar.appendChild(rr);
    root.appendChild(rev); root.appendChild(bar); main.appendChild(root);
    function resetAll() { pool = items.map(function (_, i) { return i; }); drawn = []; cur = ''; big.textContent = '?'; big.style.fontSize = ''; chips.textContent = ''; update(); }
    function update() {
      rep.textContent = '중복 없이 뽑기: ' + (noRep ? '켜짐' : '꺼짐');
      info.textContent = noRep ? ('남은 ' + pool.length + ' / 전체 ' + items.length + (pool.length ? '' : ' · 모두 뽑았어요!')) : ('전체 ' + items.length);
      go.textContent = noRep && !pool.length ? '처음부터 다시' : '뽑기!';
      chips.textContent = '';
      drawn.slice(-8).forEach(function (s) { chips.appendChild(h('span', 'chip', s)); });
    }
    function show(s, slam) {
      big.textContent = s; big.className = 'picked' + (slam ? ' slam' : ' spin');
      fit(big, 340, 120, rev.clientWidth * 0.9);
    }
    function draw() {
      if (busy) return;
      if (noRep && !pool.length) { resetAll(); return; }
      var idx, pi;
      if (noRep) { pi = rnd(pool.length); idx = pool.splice(pi, 1)[0]; } else idx = rnd(items.length);
      var res = items[idx];
      function done() {
        busy = false; cur = res; drawn.push(res); reveals++;
        show(res, true); if (RM) big.className = 'picked fade'; impact(); update();
        if (J) { snd('correct', { streak: 6 }); if (!RM && !API.instant) { var pc = J.center(big); J.burst(pc.x, pc.y, { count: 22, scale: 1.3 }); J.squash(big); J.hitStop(); J.fx.rackFocus(rev, [chips, info], { clear: true }); } } else { beep(784, 0.15); beep(1046, 0.3, 0.14); }
      }
      if (RM || API.instant || items.length < 2) { done(); return; }
      busy = true; var n = 0, total = 16;
      if (J) { snd('drumroll', { ms: 2300 }); J.fx.rackFocus(rev, [chips, info]); }
      (function loop() {
        if (n >= total) { done(); return; }
        show(items[rnd(items.length)], false); if (!J) beep(300 + n * 18, 0.05);
        n++; setTimeout(loop, 60 + n * n * 1.1);
      })();
    }
    function edit() {
      editor({ title: '뽑기 목록 (한 줄에 하나)', lines: items, fill: true, limit: 60, min: 2, onSave: function (ls) { items = ls; resetAll(); } });
    }
    API.step = function () { if (busy) return false; draw(); return true; };
    API.action = draw;
    API.state = function () { return { tool: 'picker', current: cur, drawn: drawn.slice(), remaining: pool.length, no_repeat: noRep, busy: busy, total: items.length }; };
    resetAll();
  }

  /* ---------- teams ---------- */
  function teams() {
    var names = D.items.slice(), k = D.team_count, groups = null, tn = D.team_names;
    var root = h('div', 'teams'), area = h('div', 'tgrid'), bar = h('div', 'row');
    var kLab = h('span', 'chip', ''), minus = btn('−', 'sm', function () { k = Math.max(2, k - 1); groups = null; draw(); });
    var plus = btn('+', 'sm', function () { k = Math.min(Math.min(8, names.length), k + 1); groups = null; draw(); });
    var go = btn('모둠 나누기', 'main', split);
    document.getElementById('tb').insertBefore(btn('명단 바꾸기', 'sm', edit), document.getElementById('tb').firstChild);
    bar.appendChild(h('span', 'hint', '모둠 수')); bar.appendChild(minus); bar.appendChild(kLab); bar.appendChild(plus); bar.appendChild(go);
    root.appendChild(area); root.appendChild(bar); main.appendChild(root);
    function split() {
      var s = shuffle(names); groups = [];
      for (var i = 0; i < k; i++) groups.push([]);
      s.forEach(function (n, i) { groups[i % k].push(n); });
      draw(true);
    }
    function draw(anim) {
      k = Math.max(2, Math.min(k, Math.min(8, names.length)));
      kLab.textContent = k + '모둠'; go.textContent = groups ? '다시 섞기' : '모둠 나누기';
      area.textContent = '';
      if (!groups) {
        area.style.display = 'flex'; area.style.alignContent = '';
        var e = h('div', 'empty'); e.appendChild(h('div', '', '모두 ' + names.length + '명을 ' + k + '모둠으로 나눠요'));
        e.appendChild(h('div', 'hint', '모둠당 ' + Math.floor(names.length / k) + (names.length % k ? '~' + Math.ceil(names.length / k) : '') + '명'));
        area.appendChild(e); return;
      }
      var cols = k <= 3 ? k : (k <= 6 ? 3 : 4), rows = Math.ceil(k / cols);
      area.style.display = 'grid'; area.style.gridTemplateColumns = 'repeat(' + cols + ',1fr)'; area.style.gridTemplateRows = 'repeat(' + rows + ',1fr)';
      groups.forEach(function (g, i) {
        var c = h('div', 'tcard card' + (anim && !RM && !J ? ' pop' : '')); c.style.setProperty('--i', i);
        c.appendChild(h('h3', '', (tn[i] || ((i + 1) + '모둠')) + ' · ' + g.length + '명'));
        var ch = h('div', 'chips'); g.forEach(function (n) { ch.appendChild(h('span', 'chip', n)); }); c.appendChild(ch);
        area.appendChild(c);
      });
      if (anim) {
        if (J) { snd('whoosh'); if (!RM && !API.instant) { J.fx.layerExplode(area, { mode: 'in', radius: 160, ms: 560 }); J.kick(); setTimeout(function () { snd('pop'); }, 420); } }
        else { impact(); beep(660, 0.1); beep(880, 0.2, 0.12); }
      }
    }
    function edit() {
      editor({ title: '모둠 명단 (한 줄에 한 명)', lines: names, fill: true, limit: 60, min: 2, onSave: function (ls) { names = ls; groups = null; k = Math.min(k, Math.max(2, ls.length)); draw(); } });
    }
    API.step = function () { split(); return true; };
    API.action = split;
    API.state = function () { return { tool: 'teams', teams: groups ? groups.map(function (g) { return g.slice(); }) : null, total: names.length, k: k }; };
    draw();
  }

  /* ---------- bracket ---------- */
  function seedOrder(n) {
    var a = [1];
    while (a.length < n) { var m = a.length * 2 + 1; a = a.reduce(function (r, s) { r.push(s, m - s); return r; }, []); }
    return a;
  }
  function bracket() {
    var names = D.items.slice(), size, R, slots, W, hist = [];
    var root = h('div', 'bracket'), champ = h('div', 'champ'), cols = h('div', 'cols'), bar = h('div', 'row');
    var tb = document.getElementById('tb');
    tb.insertBefore(btn('명단 바꾸기', 'sm', edit), tb.firstChild);
    var undoB = btn('되돌리기', 'sm', function () { if (hist.length) { W = JSON.parse(hist.pop()); draw(); } });
    bar.appendChild(btn('자리 섞기', 'sm', function () { names = shuffle(names); init(); }));
    bar.appendChild(undoB);
    bar.appendChild(h('span', 'hint', '이긴 쪽을 눌러요.'));
    root.appendChild(champ); root.appendChild(cols); root.appendChild(bar); main.appendChild(root);
    function init() {
      size = 2; while (size < names.length) size *= 2;
      R = Math.round(Math.log(size) / Math.LN2);
      slots = seedOrder(size).map(function (s) { return s <= names.length ? names[s - 1] : null; });
      W = [];
      for (var r = 0; r < R; r++) { W.push([]); for (var m = 0; m < size / Math.pow(2, r + 1); m++) W[r].push(null); }
      for (var m2 = 0; m2 < size / 2; m2++) { if (slots[2 * m2] === null) W[0][m2] = slots[2 * m2 + 1]; else if (slots[2 * m2 + 1] === null) W[0][m2] = slots[2 * m2]; }
      hist = []; draw();
    }
    function players(r, m) { return r === 0 ? [slots[2 * m], slots[2 * m + 1]] : [W[r - 1][2 * m], W[r - 1][2 * m + 1]]; }
    function pick(r, m, who) {
      if (W[r][m] === who) return;
      hist.push(JSON.stringify(W));
      W[r][m] = who;
      var j = m; for (var rr = r + 1; rr < R; rr++) { j = j >> 1; W[rr][j] = null; }
      snd('pop'); draw(r === R - 1);
    }
    function label(r) { var n = size / Math.pow(2, r); return n === 2 ? '결승' : n + '강'; }
    function matchEl(r, m) {
      var p = players(r, m), bye = r === 0 && (p[0] === null || p[1] === null), active = !bye && p[0] !== null && p[1] !== null, box = h('div', 'match');
      p.forEach(function (name) {
        var win = name !== null && W[r][m] === name;
        var el = active ? h('button', 'slot', null, { type: 'button' }) : h('div', 'slot');
        if (name === null) el.classList.add('wait');
        if (win) el.classList.add('win');
        el.appendChild(h('span', '', name === null ? (bye ? '부전승' : '…') : name));
        if (win) el.appendChild(h('span', '', '승'));
        if (active) el.addEventListener('click', function () { pick(r, m, name); });
        box.appendChild(el);
      });
      return box;
    }
    function colEl(r, from, to, fin) {
      var c = h('div', 'rcol' + (fin ? ' fin' : ''));
      c.appendChild(h('div', 'rlab', label(r)));
      var wrap = h('div', ''); wrap.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:space-around';
      for (var m = from; m < to; m++) wrap.appendChild(matchEl(r, m));
      c.appendChild(wrap); return c;
    }
    function draw(celebrate) {
      cols.textContent = '';
      var mirror = size >= 8 && stage.className !== 'port';
      for (var r = 0; r < R; r++) {
        var cnt = size / Math.pow(2, r + 1);
        if (r === R - 1) { cols.appendChild(colEl(r, 0, 1, true)); if (mirror) break; continue; }
        cols.appendChild(colEl(r, 0, mirror ? cnt / 2 : cnt, false));
      }
      if (mirror) for (var r2 = R - 2; r2 >= 0; r2--) { var c2 = size / Math.pow(2, r2 + 1); cols.appendChild(colEl(r2, c2 / 2, c2, false)); }
      var w = W[R - 1][0];
      champ.className = 'champ' + (w ? ' on' : ''); champ.textContent = w ? '우승: ' + w : ('대진표 · ' + names.length + '명');
      if (w && celebrate) {
        impact(); snd('fanfare');
        if (J && !RM && !API.instant) { var bc = J.center(champ); J.burst(bc.x, bc.y, { count: 22, scale: 1.2 }); J.confetti({ count: 50 }); J.squash(champ); }
        if (!J) { beep(784, 0.15); beep(1046, 0.15, 0.15); beep(1318, 0.4, 0.3); }
      }
      undoB.style.opacity = hist.length ? '1' : '.6';
    }
    function edit() {
      editor({ title: '대진표 명단 (2~16명, 한 줄에 하나)', lines: names, fill: true, limit: 16, min: 2, onSave: function (ls) { names = D.shuffle_on_edit ? shuffle(ls) : ls; init(); } });
    }
    API.step = function () {
      for (var r = 0; r < R; r++) for (var m = 0; m < W[r].length; m++) {
        var p = players(r, m);
        if (!W[r][m] && p[0] !== null && p[1] !== null) { pick(r, m, p[0]); return true; }
      }
      return false;
    };
    API.relayout = function () { draw(); };
    API.state = function () { return { tool: 'bracket', champion: W[R - 1][0], rounds: W.map(function (x) { return x.slice(); }), entries: names.length }; };
    init();
  }

  /* ---------- scoreboard ---------- */
  function scoreboard() {
    var names = D.teams.slice(), score = [], shown = [], hist = [], steps = D.steps, armed = 0, anim = {};
    var root = h('div', 'score'), vals = [], badges = [];
    names.forEach(function () { score.push(D.start); shown.push(D.start); });
    var tb = document.getElementById('tb');
    var reset = btn('0점으로', 'sm', function () {
      if (!armed) { armed = 1; reset.textContent = '한 번 더 누르면 0점'; setTimeout(function () { armed = 0; reset.textContent = '0점으로'; }, 3000); return; }
      armed = 0; reset.textContent = '0점으로'; hist.push(score.slice()); score = names.map(function () { return D.start; }); update();
    });
    tb.insertBefore(reset, tb.firstChild);
    if (J) tb.insertBefore(btn('🏆 시상식', 'sm', podium), tb.firstChild);
    tb.insertBefore(btn('되돌리기', 'sm', function () { if (hist.length) { score = hist.pop(); update(); } }), tb.firstChild);
    tb.insertBefore(btn('모둠 이름', 'sm', function () {
      editor({ title: '모둠 이름 (한 줄에 하나, 2~8개)', lines: names, fill: false, limit: 8, min: 2, hint: '모둠 이름은 이 화면에만 있고 저장하거나 어디로 보내지 않아요.', onSave: function (ls) {
        var old = names; names = ls; score = ls.map(function (_, i) { return i < old.length ? score[i] : D.start; }); shown = score.slice(); hist = []; build(); } });
    }), tb.firstChild);
    main.appendChild(root);
    function sizes() {
      var n = names.length, cols = n <= 4 ? n : Math.ceil(n / 2), rows = n <= 4 ? 1 : 2;
      var sv = n <= 3 ? 300 : n === 4 ? 220 : n <= 6 ? 150 : 120;
      if (stage.className === 'port') { cols = n <= 4 ? 1 : 2; rows = Math.ceil(n / cols); sv = n <= 2 ? 260 : n <= 4 ? 190 : 130; }
      return { cols: cols, rows: rows, sv: sv };
    }
    function build() {
      var z = sizes(); root.textContent = ''; vals = []; badges = [];
      root.style.gridTemplateColumns = 'repeat(' + z.cols + ',1fr)'; root.style.gridTemplateRows = 'repeat(' + z.rows + ',1fr)';
      names.forEach(function (nm, i) {
        var c = h('div', 'scard card'), v = h('div', 'sval', String(shown[i])), b = h('div', 'badge', '1위');
        v.style.fontSize = z.sv + 'px'; b.style.display = 'none';
        c.appendChild(h('h3', '', nm)); c.appendChild(b); c.appendChild(v);
        var sb = h('div', 'sbtns');
        steps.forEach(function (s) { sb.appendChild(btn('+' + s, 'main sm', function () { add(i, s); })); });
        sb.appendChild(btn('−1', 'sm', function () { add(i, -1); }));
        c.appendChild(sb); root.appendChild(c); vals.push(v); badges.push(b);
      });
      update(true);
    }
    function add(i, d) {
      hist.push(score.slice()); score[i] += d; update();
      if (d > 0) { snd('correct', { streak: Math.min(8, 1 + d) }); if (J && !RM && !API.instant && vals[i]) { J.squash(vals[i]); var sc = J.center(vals[i]); J.burst(sc.x, sc.y, { count: 12 + Math.min(10, d) }); } } else snd('click');
    }
    function update(skip) {
      var max = Math.max.apply(null, score), top = score.filter(function (s) { return s === max; }).length;
      badges.forEach(function (b, i) { b.style.display = max > D.start && score[i] === max ? '' : 'none'; b.textContent = top > 1 ? '공동 1위' : '1위'; });
      score.forEach(function (s, i) { countTo(i, s, skip); });
    }
    function countTo(i, target, skip) {
      var from = shown[i], t0 = performance.now(), dur = 600;
      anim[i] = (anim[i] || 0) + 1; var id = anim[i];
      if (RM || API.instant || skip || from === target) { shown[i] = target; vals[i].textContent = String(target); return; }
      (function f(t) {
        if (anim[i] !== id) return;
        var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
        shown[i] = Math.round(from + (target - from) * e); vals[i].textContent = String(shown[i]);
        if (p < 1) requestAnimationFrame(f); else { shown[i] = target; vals[i].textContent = String(target); }
      })(t0);
    }
    /* podium: teams only, 3rd -> 2nd -> 1st (never individuals); a drumroll first, tap anywhere to skip */
    function podium() {
      var max = Math.max.apply(null, score), ov = h('div', 'ov'), card = h('div', 'ovcard card'), host = h('div', 'pbox'), ctl = null, tm = 0;
      function close() { clearTimeout(tm); if (ctl) ctl.skip(); if (ov.parentNode) ov.parentNode.removeChild(ov); API.podiumEl = null; }
      card.appendChild(h('h2', '', '🏆 시상식'));
      if (max <= D.start) { card.appendChild(h('p', 'hint', '아직 점수가 없어요. 점수를 올린 뒤 다시 눌러 주세요.')); }
      else card.appendChild(host);
      var row = h('div', 'row'); row.appendChild(btn('닫기', 'main', close)); card.appendChild(row); ov.appendChild(card); main.appendChild(ov); API.podiumEl = host;
      if (max > D.start) {
        var teamsArr = names.map(function (n, i) { return { name: n, icon: ICONS[n] || '⭐', color: TEAMC[i % TEAMC.length], score: score[i] }; });
        var go = function () { ctl = J.podium(host, teamsArr, { onDone: function () { if (!RM && !API.instant) { J.fx.impactFrame(); } } }); };
        if (RM || API.instant) go(); else { host.appendChild(h('div', 'hint', '🥁 결과를 발표해요!')); snd('drumroll', { ms: 1500 }); tm = setTimeout(go, 1500); }
        card.addEventListener('pointerdown', function (e) { if (!/BUTTON/.test(e.target.tagName)) { if (ctl) ctl.skip(); else { clearTimeout(tm); host.textContent = ''; go(); if (ctl) ctl.skip(); } } });
      }
    }
    API.podium = podium;
    API.step = function () { add(0, steps[0]); return true; };
    API.state = function () { return { tool: 'scoreboard', teams: names.slice(), scores: score.slice(), shown: vals.map(function (v) { return v.textContent; }) }; };
    API.relayout = build;
    build();
  }

  /* ---------- shell ---------- */
  function resize() {
    var w = window.innerWidth, hh = window.innerHeight, port = hh > w * 1.15, W = port ? 1080 : 1920, H = port ? 1920 : 1080, s = Math.min(w / W, hh / H);
    stage.style.width = W + 'px'; stage.style.height = H + 'px'; stage.style.transform = 'scale(' + s + ')';
    stage.style.left = ((w - W * s) / 2) + 'px'; stage.style.top = ((hh - H * s) / 2) + 'px';
    var was = stage.className; stage.className = port ? 'port' : 'land';
    if (was !== stage.className && API.relayout) API.relayout();
  }
  var tb = document.getElementById('tb');
  var sndB = btn('', 'sm', function () { soundOn = !soundOn; paintSnd(); snd('click'); });
  function paintSnd() { sndB.textContent = soundOn ? '🔇 소리 끄기' : '🔊 소리 켜기'; sndB.setAttribute('aria-pressed', soundOn ? 'false' : 'true'); }
  var fxB = btn('', 'sm', function () { if (OSRM) return; userRM = !userRM; RM = userRM; if (J) J.setReduce(userRM); paintFx(); });
  function paintFx() { fxB.textContent = RM ? '✨ 효과 켜기' : '🌙 효과 줄이기'; fxB.setAttribute('aria-pressed', RM ? 'true' : 'false'); if (OSRM) { fxB.title = '기기 설정에서 이미 효과가 줄어 있어요'; } }
  paintSnd(); paintFx(); tb.appendChild(fxB); tb.appendChild(sndB);
  tb.appendChild(btn('전체화면', 'sm', function () {
    var d = document, el = d.documentElement;
    try { if (d.fullscreenElement) d.exitFullscreen(); else if (el.requestFullscreen) el.requestFullscreen(); } catch (e) { /* not allowed */ }
  }));
  window.addEventListener('resize', resize);
  resize();
  ({ timer: timer, picker: picker, teams: teams, bracket: bracket, scoreboard: scoreboard })[T.tool]();
  document.addEventListener('keydown', function (e) {
    if (e.target !== document.body) return;
    if ((e.key === ' ' || e.key === 'Enter') && API.action) { e.preventDefault(); API.action(); }
  });
  window.render_tool_to_text = function () { return JSON.stringify(API.state()); };
  window.advanceTime = function (ms) { API.advance(ms); };
})();
