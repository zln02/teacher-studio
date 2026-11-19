/* SPDX-License-Identifier: Apache-2.0 */
/* feel-capture overlay: PREVIEW ONLY (inject with `diagnose.py inject FILE`, never into the final shared file).
   Collects the teacher's "feel" in <30 s: rating, 5 sliders, A/B picks, tap-to-mark, chips, one line. No network, no storage,
   no personal data. Result -> window.__tsFeelResult + 'ts-feel-done' event + copy/download feel.json -> `diagnose.py feel feel.json`.
   Optional: window.FEEL_VARIANTS=[{axis,label,a,b,positive}] (css strings) replaces the default A/B pairs. ES2017 only. */
(function () {
  if (window.__tsFeel) return;
  window.__tsFeel = true;
  var AXES = [
    ['calm_vivid', '차분', '화려'], ['simple_rich', '단순', '풍부'], ['warm_cool', '따뜻', '시원'],
    ['cute_premium', '귀여움', '고급'], ['text_size', '글씨 작게', '글씨 크게']
  ];
  var CHIPS = ['밝게', '어둡게', '깔끔하게', '재밌게', '고급스럽게', '귀엽게', '촌스러움 빼기'];
  var SEL = 'body>*:not(#ts-feel)';
  var VARS = window.FEEL_VARIANTS || [
    { axis: 'calm_vivid', a: SEL + '{filter:saturate(.75) contrast(.95)}', b: SEL + '{filter:saturate(1.35) contrast(1.05)}', positive: 'B', la: '더 차분', lb: '더 화려' },
    { axis: 'warm_cool', a: SEL + '{filter:sepia(.28) saturate(1.05)}', b: SEL + '{filter:hue-rotate(28deg) saturate(1.05)}', positive: 'B', la: '더 따뜻', lb: '더 시원' },
    { axis: 'text_size', a: SEL + '{zoom:1}', b: SEL + '{zoom:1.15}', positive: 'B', la: '지금 크기', lb: '더 크게' }
  ];
  var standalone = !!window.FEEL_STANDALONE;
  var S = { rating: 0, sliders: {}, chips: [], note: '', marks: [], ab: [] };
  var round = 0, marking = false, styleEl = null;

  function el(tag, attrs, kids) {
    var e = document.createElement(tag), k;
    for (k in (attrs || {})) { if (k === 'text') e.textContent = attrs[k]; else if (k === 'style') e.style.cssText = attrs[k]; else e.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { e.appendChild(c); });
    return e;
  }
  var root = el('div', { id: 'ts-feel', style: 'position:fixed;right:16px;bottom:16px;z-index:2147483647;font:16px/1.4 system-ui,"Malgun Gothic",sans-serif;color:#111;word-break:keep-all' });
  var btn = el('button', { text: '느낌 남기기', style: 'min-height:48px;padding:0 20px;border-radius:24px;border:0;background:#111;color:#fff;font:600 16px system-ui,"Malgun Gothic";box-shadow:0 4px 16px #0006;cursor:pointer' });
  var panel = el('div', { style: 'display:none;width:min(420px,92vw);max-height:80vh;overflow:auto;background:#fff;border:1px solid #bbb;border-radius:14px;padding:14px;box-shadow:0 8px 32px #0005' });
  root.appendChild(panel); root.appendChild(btn);

  function chipBtn(label, on, fn) {
    var b = el('button', { text: label, style: 'min-height:40px;margin:3px;padding:0 12px;border-radius:20px;border:1px solid #888;background:' + (on ? '#111' : '#fff') + ';color:' + (on ? '#fff' : '#111') + ';font:15px system-ui,"Malgun Gothic";cursor:pointer' });
    b.onclick = fn; return b;
  }
  function section(t) { return el('div', { text: t, style: 'font-weight:700;margin:12px 0 4px' }); }

  function setVariant(css) {
    if (!styleEl) { styleEl = el('style', { id: 'ts-feel-var' }); document.head.appendChild(styleEl); }
    styleEl.textContent = css || '';
  }
  function clearVariant() { if (styleEl) styleEl.textContent = ''; }

  function selOf(e) {
    var p = [];
    while (e && e.nodeType === 1 && e !== document.body && p.length < 4) {
      var s = e.tagName.toLowerCase();
      if (e.id) { p.unshift(s + '#' + e.id); break; }
      if (e.classList && e.classList.length) s += '.' + e.classList[0];
      p.unshift(s); e = e.parentElement;
    }
    return p.join('>');
  }
  function onMark(ev) {
    if (!marking) return;
    var t = ev.target;
    if (root.contains(t)) return;
    ev.preventDefault(); ev.stopPropagation();
    marking = false; document.body.style.cursor = '';
    var txt = (t.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30);
    S.marks.push({ sel: selOf(t), tag: t.tagName.toLowerCase(), text: txt, x: Math.round(ev.clientX / innerWidth * 100) / 100, y: Math.round(ev.clientY / innerHeight * 100) / 100 });
    var ring = el('div', { style: 'position:fixed;left:' + (ev.clientX - 24) + 'px;top:' + (ev.clientY - 24) + 'px;width:48px;height:48px;border:4px solid #e11;border-radius:50%;z-index:2147483646;pointer-events:none' });
    document.body.appendChild(ring);
    panel.style.display = 'block'; render();
  }
  document.addEventListener('click', onMark, true);

  function render() {
    panel.textContent = '';
    panel.appendChild(el('div', { text: '30초면 돼요. 아무것도 안 골라도 괜찮아요.', style: 'font-weight:700;font-size:17px' }));
    panel.appendChild(section('1. 전체 점수'));
    var row = el('div');
    [1, 2, 3, 4, 5].forEach(function (n) { row.appendChild(chipBtn(n + '점', S.rating === n, function () { S.rating = n; render(); })); });
    panel.appendChild(row);
    panel.appendChild(section('2. 느낌 (가운데 = 그대로)'));
    AXES.forEach(function (a) {
      var v = S.sliders[a[0]] || 0;
      var inp = el('input', { type: 'range', min: '-2', max: '2', step: '1', value: String(v), style: 'width:100%;height:32px' });
      inp.oninput = function () { S.sliders[a[0]] = Number(inp.value); };
      panel.appendChild(el('div', { style: 'display:flex;justify-content:space-between;font-size:14px' }, [el('span', { text: a[1] }), el('span', { text: a[2] })]));
      panel.appendChild(inp);
    });
    panel.appendChild(section('3. A/B 골라 보기 (' + round + '/' + VARS.length + ')'));
    if (round >= VARS.length) { panel.appendChild(el('div', { text: '끝났어요.' })); clearVariant(); }
    else {
      var v = VARS[round], r2 = el('div');
      function pick(letter) { S.ab.push({ round: round + 1, axis: v.axis, pick: letter, positive: v.positive || 'B' }); round++; clearVariant(); render(); }
      var ba = chipBtn('A ' + (v.la || ''), false, function () { pick('A'); }), bb = chipBtn('B ' + (v.lb || ''), false, function () { pick('B'); });
      if (!standalone) {
        ba.onmouseenter = ba.onfocus = function () { setVariant(v.a); };
        bb.onmouseenter = bb.onfocus = function () { setVariant(v.b); };
        ba.onmouseleave = bb.onmouseleave = clearVariant;
      }
      r2.appendChild(ba); r2.appendChild(bb);
      panel.appendChild(r2);
      panel.appendChild(el('div', { text: standalone ? '' : '버튼에 손을 올리면(꾹 누르면) 화면이 바뀌어 보여요.', style: 'font-size:13px;color:#555' }));
    }
    panel.appendChild(section('4. 아쉬운 곳 콕 찍기 (' + S.marks.length + '곳)'));
    var mb = chipBtn(marking ? '화면을 눌러 주세요…' : '콕 찍기', marking, function () { marking = true; document.body.style.cursor = 'crosshair'; panel.style.display = 'none'; });
    panel.appendChild(mb);
    panel.appendChild(section('5. 끌리는 말'));
    var cr = el('div');
    CHIPS.forEach(function (c) {
      cr.appendChild(chipBtn(c, S.chips.indexOf(c) >= 0, function () { var i = S.chips.indexOf(c); if (i >= 0) S.chips.splice(i, 1); else S.chips.push(c); render(); }));
    });
    panel.appendChild(cr);
    var note = el('input', { type: 'text', maxlength: '120', placeholder: '한 줄 (선택)', value: S.note, autocomplete: 'off', style: 'width:100%;height:44px;margin-top:8px;font-size:16px;padding:0 10px;box-sizing:border-box' });
    note.oninput = function () { S.note = note.value; };
    panel.appendChild(note);
    var done = chipBtn('완료', true, finish);
    done.style.cssText += ';margin-top:12px;min-height:48px;padding:0 28px';
    panel.appendChild(done);
  }

  function finish() {
    clearVariant();
    var out = { v: 1, rating: S.rating || null, sliders: S.sliders, ab: S.ab, marks: S.marks, chips: S.chips, note: S.note };
    window.__tsFeelResult = out;
    var json = JSON.stringify(out);
    try { document.dispatchEvent(new CustomEvent('ts-feel-done', { detail: out })); } catch (e) {}
    panel.textContent = '';
    panel.appendChild(el('div', { text: '고마워요! 이 느낌으로 고쳐 볼게요.', style: 'font-weight:700;font-size:17px' }));
    var ta = el('textarea', { readonly: 'readonly', style: 'width:100%;height:90px;margin-top:8px;font-size:12px' });
    ta.value = json; panel.appendChild(ta);
    var cp = chipBtn('복사', false, function () { try { ta.select(); navigator.clipboard.writeText(json); } catch (e) { document.execCommand('copy'); } });
    var dl = chipBtn('feel.json 저장', false, function () {
      var a = el('a', { href: URL.createObjectURL(new Blob([json], { type: 'application/json' })), download: 'feel.json' });
      document.body.appendChild(a); a.click(); a.remove();
    });
    panel.appendChild(cp); panel.appendChild(dl);
  }

  btn.onclick = function () { var open = panel.style.display === 'block'; panel.style.display = open ? 'none' : 'block'; if (!open) render(); };
  document.body.appendChild(root);
  if (standalone) { panel.style.display = 'block'; render(); btn.style.display = 'none'; }
})();
