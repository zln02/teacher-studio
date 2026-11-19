/* Teacher Studio web app runtime (ES2017, no network, no storage). Parts: helper (rule-based Q&A), runner (JS practice pad), custom.
   Custom part code gets window.APP: APP.el(id) · APP.onReset(fn) · APP.say(text) · APP.toRunner(code) · APP.cfg */
(function () {
  'use strict';
  var CFG = window.WEBAPP || { parts: [] };
  var root = document.documentElement;
  var resets = [];
  var APP = window.APP = {
    cfg: CFG,
    el: function (id) { return document.getElementById(id); },
    onReset: function (fn) { if (typeof fn === 'function') resets.push(fn); },
    say: function (text) { var l = document.getElementById('wa-live'); if (l) { l.textContent = ''; setTimeout(function () { l.textContent = String(text); }, 30); } },
    toRunner: null
  };

  function clean(s) { // never show markdown marks as text
    return String(s == null ? '' : s).replace(/\*\*|__|`/g, '').replace(/^#+\s*/gm, '');
  }
  function norm(s) { return String(s == null ? '' : s).toLowerCase().replace(/[\s?!.,~'"]+/g, ''); }

  /* ---------- toolbar: text size, projector, reset, about ---------- */
  var level = 0, LV = { '-1': 'lv-1', '1': 'lv1', '2': 'lv2' };
  function setLevel(n) {
    level = Math.max(-1, Math.min(2, n));
    root.classList.remove('lv-1', 'lv1', 'lv2');
    if (LV[String(level)]) root.classList.add(LV[String(level)]);
    APP.say('글자 크기 ' + (level + 2) + '단계');
  }
  function toggleProjector(force) {
    var on = typeof force === 'boolean' ? force : !root.classList.contains('projector');
    root.classList.toggle('projector', on);
    var b = APP.el('wa-proj');
    if (b) b.setAttribute('aria-pressed', on ? 'true' : 'false');
    APP.say(on ? '프로젝터 모드 켬' : '프로젝터 모드 끔');
  }
  function resetAll() {
    var scope = document.querySelectorAll('.wa-custom input, .wa-custom textarea, .wa-custom select');
    for (var i = 0; i < scope.length; i++) {
      var e = scope[i];
      if (e.type === 'checkbox' || e.type === 'radio') e.checked = e.defaultChecked;
      else if (e.tagName === 'SELECT') { for (var j = 0; j < e.options.length; j++) e.options[j].selected = e.options[j].defaultSelected; }
      else e.value = e.defaultValue;
    }
    for (var k = 0; k < resets.length; k++) { try { resets[k](); } catch (err) { if (window.console) console.error(err); } }
    APP.say('처음 상태로 돌아갔어요');
  }
  function bind(id, fn) { var b = APP.el(id); if (b) b.addEventListener('click', fn); }
  bind('wa-smaller', function () { setLevel(level - 1); });
  bind('wa-bigger', function () { setLevel(level + 1); });
  bind('wa-proj', function () { toggleProjector(); });
  bind('wa-reset', resetAll);
  var dlg = APP.el('wa-about');
  function openAbout() { if (dlg && typeof dlg.showModal === 'function') { if (!dlg.open) dlg.showModal(); } else if (dlg) dlg.setAttribute('open', ''); }
  bind('wa-about-btn', openAbout);
  bind('wa-about-close', function () { if (dlg && typeof dlg.close === 'function') dlg.close(); else if (dlg) dlg.removeAttribute('open'); });
  document.addEventListener('keydown', function (ev) {
    var t = ev.target, tag = (t && t.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (t && t.isContentEditable) || ev.ctrlKey || ev.metaKey || ev.altKey) return;
    if (ev.key === 'p' || ev.key === 'P') { toggleProjector(); ev.preventDefault(); }
    else if (ev.key === '+' || ev.key === '=') { setLevel(level + 1); ev.preventDefault(); }
    else if (ev.key === '-') { setLevel(level - 1); ev.preventDefault(); }
    else if (ev.key === '?') { openAbout(); ev.preventDefault(); }
  });

  /* ---------- runner: JavaScript practice pad in a Worker with a time limit ---------- */
  var FRIENDLY = {
    ReferenceError: '아직 만들지 않은 이름을 썼어요. 철자나 let/const 선언을 확인해 보세요.',
    SyntaxError: '문법이 맞지 않아요. 괄호 ( ) { }, 따옴표, 쉼표를 확인해 보세요.',
    TypeError: '값의 종류가 맞지 않아요. 함수가 아닌 것을 부르거나 없는 값을 쓴 건 아닌지 확인해 보세요.',
    RangeError: '숫자 범위를 벗어났어요. 함수가 자기 자신을 끝없이 부르고 있지 않은지 확인해 보세요.'
  };
  var PRE = [
    'var __o=function(t,a){var s=[];for(var i=0;i<a.length;i++){var v=a[i];if(typeof v==="string"){s.push(v)}else{try{s.push(JSON.stringify(v))}catch(e){s.push(String(v))}}}postMessage({t:t,m:s.join(" ")})};',
    'var console={log:function(){__o("log",arguments)},info:function(){__o("log",arguments)},warn:function(){__o("log",arguments)},error:function(){__o("err",arguments)}};',
    'var print=console.log,alert=console.log;var prompt=function(q){__o("log",[String(q==null?"":q)+" (이 연습장에서는 입력을 받을 수 없어 빈칸으로 처리해요)"]);return ""};',
    '["fetch","XMLHttpRequest","WebSocket","EventSource","importScripts"].forEach(function(k){try{self[k]=undefined}catch(e){}});',
    'onmessage=function(ev){try{(0,eval)(ev.data);postMessage({t:"done"})}catch(e){postMessage({t:"x",n:e&&e.name,m:String(e&&e.message)})}};'
  ].join('\n');

  function runner(part, box) {
    var code = box.querySelector('.wa-code'), out = box.querySelector('.wa-out'), sel = box.querySelector('.wa-sel');
    var limit = part.timeout_ms || 3000, worker = null, timer = null;
    var examples = part.examples || [];
    function line(text, cls) { var d = document.createElement('div'); if (cls) d.className = cls; d.textContent = text; out.appendChild(d); out.scrollTop = out.scrollHeight; }
    function stop() { if (timer) clearTimeout(timer); timer = null; if (worker) { worker.terminate(); worker = null; } }
    function explain(name, msg) { line('오류: ' + (name || 'Error') + ': ' + msg, 'err'); if (FRIENDLY[name]) line('도움말: ' + FRIENDLY[name], 'err'); }
    function run() {
      stop(); out.textContent = '';
      var src = code.value, printed = false;
      try {
        worker = new Worker(URL.createObjectURL(new Blob([PRE], { type: 'text/javascript' })));
      } catch (e) { worker = null; }
      if (!worker) { // very old browser: run here without the time limit
        try { var logs = []; var fake = { log: function () { logs.push([].slice.call(arguments).join(' ')); } };
          (new Function('console', 'print', src))(fake, fake.log); logs.forEach(function (l) { line(l); }); line('끝 (시간 제한 없이 실행했어요)', 'ok');
        } catch (e2) { explain(e2.name, e2.message); }
        return;
      }
      worker.onmessage = function (ev) {
        var d = ev.data || {};
        if (d.t === 'log') { printed = true; line(d.m); }
        else if (d.t === 'err') { printed = true; line(d.m, 'err'); }
        else if (d.t === 'x') { explain(d.n, d.m); stop(); }
        else if (d.t === 'done') { if (!printed) line('(출력 없음: console.log(...)로 값을 보여 줄 수 있어요)'); line('끝', 'ok'); stop(); }
      };
      timer = setTimeout(function () { stop(); line('너무 오래 걸려서 ' + Math.round(limit / 1000) + '초 만에 멈췄어요. 반복문이 끝나는 조건을 확인해 보세요.', 'err'); }, limit);
      worker.postMessage(src);
    }
    function load(i) { if (examples[i]) { code.value = examples[i].code; out.textContent = ''; } }
    box.querySelector('.wa-run').addEventListener('click', run);
    var clr = box.querySelector('.wa-clear'); if (clr) clr.addEventListener('click', function () { stop(); out.textContent = ''; });
    if (sel) sel.addEventListener('change', function () { load(sel.selectedIndex); });
    code.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); run(); }
      else if (ev.key === 'Tab' && !ev.shiftKey) { ev.preventDefault(); var s = code.selectionStart, e = code.selectionEnd; code.value = code.value.slice(0, s) + '  ' + code.value.slice(e); code.selectionStart = code.selectionEnd = s + 2; }
      else if (ev.key === 'Escape') { box.querySelector('.wa-run').focus(); }
    });
    APP.toRunner = function (src) { code.value = src; out.textContent = ''; code.focus(); APP.say('코드를 연습장에 넣었어요'); };
    APP.onReset(function () { stop(); code.value = code.defaultValue; out.textContent = ''; if (sel) sel.selectedIndex = 0; });
  }

  /* ---------- helper: rule-based answers (no internet AI) ---------- */
  function helper(part, box) {
    var log = box.querySelector('.wa-log'), inp = box.querySelector('.wa-in'), send = box.querySelector('.wa-send');
    var intents = part.intents || [];
    function add(who, text, code) {
      var d = document.createElement('div'); d.className = 'wa-msg ' + who; d.textContent = clean(text);
      if (code) {
        var pre = document.createElement('pre'); pre.textContent = code; d.appendChild(pre);
        if (APP.toRunner) { var b = document.createElement('button'); b.type = 'button'; b.className = 'wa-chip'; b.textContent = '연습장에서 해 보기'; b.addEventListener('click', function () { APP.toRunner(code); }); d.appendChild(b); }
      }
      log.appendChild(d); log.scrollTop = log.scrollHeight;
    }
    function best(q) {
      var n = norm(q), top = null, topScore = 0;
      for (var i = 0; i < intents.length; i++) {
        var keys = intents[i].keys || [], sc = 0;
        for (var j = 0; j < keys.length; j++) { var k = norm(keys[j]); if (k && n.indexOf(k) >= 0) sc += k.length; }
        if (sc > topScore) { topScore = sc; top = intents[i]; }
      }
      return top;
    }
    function ask(q) {
      q = String(q || '').trim(); if (!q) { inp.focus(); return; }
      add('me', q); inp.value = '';
      var hit = best(q);
      if (hit) add('bot', hit.answer, hit.code);
      else add('bot', part.fallback || '그 질문은 아직 준비된 답이 없어요. 아래 버튼의 질문을 눌러 보거나 선생님께 물어보세요.');
      APP.say('답이 나왔어요');
    }
    send.addEventListener('click', function () { ask(inp.value); });
    inp.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' && !ev.isComposing) { ev.preventDefault(); ask(inp.value); } });
    var chips = box.querySelectorAll('.wa-chips .wa-chip');
    for (var i = 0; i < chips.length; i++) chips[i].addEventListener('click', function () { ask(this.textContent); });
    function start() { log.textContent = ''; add('bot', part.greeting || '안녕하세요! 궁금한 것을 적거나 아래 버튼을 눌러 보세요.'); inp.value = ''; }
    APP.onReset(start); start();
  }

  var parts = CFG.parts || [];
  // runner first so helper answers can offer 「연습장에서 해 보기」
  parts.forEach(function (p, i) { var box = APP.el('wa-part-' + i); if (box && p.type === 'runner') runner(p, box); });
  parts.forEach(function (p, i) { var box = APP.el('wa-part-' + i); if (box && p.type === 'helper') helper(p, box); });
})();
