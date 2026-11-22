
  /* =====================================================================
     deck-e 층 (build.py --skin e 일 때만 motion2.js 뒤에 붙어요 · deck-v3.html에는 안 들어가요)
     장 파일은 slides-e.html. 장마다 무엇을 할지는 장 파일의 표시로 정해요 (여기서 장을 골라내지 않아요):
       data-fx="eBig" data-e-inner="v3…"  + <div class="e-big">  큰 글자 장면을 한 단계 앞에 끼우고, 그다음은 원래 장 효과(inner)를 한 단계 뒤로
       data-fx="eCover" · "eApp" · "eKitchen" · "eFloor"         이 덱만의 장 (아래)
       <img data-puppet="head">, data-puppet-bg="kitchen"         로봇 요리사 그림 조각(PUPPET)을 넣을 자리
     모든 장: HUD 틀(네 모서리 · 아래 눈금자 · 지금 장 눈금).
     움직임 값: 들어오기 150~260ms · 움직이는 동안만 흐림 · 닿으면 가만히 (TOK를 이 덱에서만 줄여요)
     움직임 줄이기 · 뒤로 가기: 끝 모습으로 바로.
     ===================================================================== */
  // icons: building-2 bot send search file-up file-text scroll-text receipt package utensils-crossed shield-check bookmark wand-sparkles telescope plug mouse-pointer-click image
  TOK.xs = 120; TOK.s = 200; TOK.m = 260; TOK.l = 420; TOK.gap = 60; TOK.cgap = 30; TOK.lead = 520;
  // 탁 · 통통에 모션 블러: 움직이는 동안만 흐리고 닿으면 또렷
  MO.snap = function (el, at, o) {
    o = o || {}; var dx = o.dx || 0, dy = o.dy === undefined ? TOK.move : o.dy, s0 = o.s === undefined ? 1 : o.s, B = Math.min(10, 4 + Math.abs(dx + dy) / 8);
    return MO.tw(o.dur || TOK.s, at, 'snap', function (e) {
      el.style.opacity = clamp01(e * 2.2);
      if (REDUCED) { el.style.opacity = e; return; }
      tf(el, dx * (1 - e), dy * (1 - e), lerp(s0, 1, e));
      el.style.filter = e >= 1 ? '' : 'blur(' + (B * (1 - e)).toFixed(2) + 'px)';
      if (e >= 1) el.style.transform = '';
    });
  };
  MO.spring = function (el, at, o) {
    o = o || {}; var s0 = o.s === undefined ? 0.2 : o.s, dx = o.dx || 0, dy = o.dy || 0, r0 = o.r || 0;
    if (o.origin) el.style.transformOrigin = o.origin;
    return MO.tw(o.dur || TOK.l - 100, at, 'linear', function (e, t) {
      var k = (o.bouncy ? EZ.bounce : EZ.spring)(t);
      el.style.opacity = clamp01(t * 5);
      if (REDUCED) { el.style.opacity = e; return; }
      tf(el, dx * (1 - k), dy * (1 - k), lerp(s0, 1, k), r0 * (1 - k));
      el.style.filter = t >= 0.45 ? '' : 'blur(' + (6 * (1 - t / 0.45)).toFixed(2) + 'px)';
      if (t >= 1) el.style.transform = '';
    });
  };

  var ET = { inn: 200, out: 150, st: 45 };
  function eoff(el, s) { var x = 0, y = 0; while (el && el !== s) { x += el.offsetLeft; y += el.offsetTop; el = el.offsetParent; } return { x: x, y: y }; }
  function emk(tag, cls, html, parent) { var e = document.createElement(tag); e.className = cls; if (html) e.innerHTML = html; if (parent) parent.appendChild(e); return e; }
  function eInst(fn) { var keep = V3DIR; V3DIR = -1; try { fn(); } finally { V3DIR = keep; } }
  // 흐림 이동: (dx,dy)에서 와서 딱
  function eIn(el, at, o) {
    o = o || {}; var dx = o.dx || 0, dy = o.dy === undefined ? 30 : o.dy, B = o.blur === undefined ? 8 : o.blur, s0 = o.s === undefined ? 1 : o.s;
    if (REDUCED) { el.style.opacity = 1; el.style.transform = ''; el.style.filter = ''; return null; }
    return MO.tw(o.dur || ET.inn, at, 'snap', function (e) {
      el.style.opacity = clamp01(e * 2.5);
      el.style.transform = e >= 1 ? '' : 'translate(' + (dx * (1 - e)).toFixed(1) + 'px,' + (dy * (1 - e)).toFixed(1) + 'px) scale(' + lerp(s0, 1, e).toFixed(4) + ')';
      el.style.filter = e >= 1 ? '' : 'blur(' + (B * (1 - e)).toFixed(2) + 'px)';
    });
  }
  // 빠른 번짐 퇴장 (150ms)
  function eOut(el, at) {
    if (REDUCED) { el.style.opacity = 0; return null; }
    return MO.tw(ET.out, at, 'fall', function (e) {
      el.style.opacity = 1 - e;
      el.style.transform = 'translateY(' + (-70 * e).toFixed(1) + 'px) scaleY(' + (1 + 0.35 * e).toFixed(3) + ')';
      el.style.filter = 'blur(' + (12 * e).toFixed(1) + 'px)';
      if (e >= 1) { el.style.visibility = 'hidden'; el.style.transform = ''; el.style.filter = ''; }
    });
  }
  // 큰 글자: 음절마다 살짝 떨어지며 기울었다 자리 (45ms 간격)
  function eDrop(el, at) {
    var cs = MO.split(el);
    el.style.opacity = 1;
    cs.forEach(function (c, i) {
      var r = ((i * 37) % 9 - 4) * 2.2;
      if (REDUCED) { c.style.opacity = 1; c.style.transform = ''; c.style.filter = ''; return; }
      MO.tw(260, at + i * ET.st, 'linear', function (e, t) {
        var p = EZ.snap(clamp01(t / 0.7)), k = EZ.spring(t);
        c.style.opacity = clamp01(t * 6);
        c.style.transform = t >= 1 ? '' : 'translateY(' + (-0.42 * (1 - p)).toFixed(3) + 'em) rotate(' + (r * (1 - k)).toFixed(2) + 'deg)';
        c.style.filter = t >= 1 ? '' : 'blur(' + (7 * (1 - p)).toFixed(2) + 'px)';
      });
    });
  }
  function eDropSet(el, on) { MO.split(el).forEach(function (c) { c.style.opacity = on ? 1 : 0; c.style.transform = ''; c.style.filter = ''; }); el.style.opacity = 1; }
  function eDrift(el, at) {
    el.classList.add('e-bg');
    if (REDUCED) { el.style.transform = ''; return; }
    MO.tw(2600, at, 'out', function (e) { el.style.transform = e >= 1 ? '' : 'translate(' + (-26 * (1 - e)).toFixed(1) + 'px,' + (18 * (1 - e)).toFixed(1) + 'px) scale(' + lerp(1.04, 1, e).toFixed(4) + ')'; });
  }
  function eBgOff(el) { el.classList.remove('e-bg'); el.style.transform = ''; el.style.filter = ''; if (el.style.opacity !== '') el.style.opacity = ''; }
  function eBgLift(el, at) {
    eBgOff(el);
    if (REDUCED) return;
    MO.tw(220, at || 0, 'out', function (e) { el.style.opacity = e >= 1 ? '' : lerp(0.16, 1, e).toFixed(3); el.style.filter = e >= 1 ? '' : 'blur(' + (6 * (1 - e)).toFixed(2) + 'px)'; });
  }

  /* ---- 펜 주석: 살짝 흔들리는 선(씨앗 고정) + 손글씨풍 메모 ---- */
  function eRand(seed) { var x = seed * 9301 + 49297; return function () { x = (x * 9301 + 49297) % 233280; return x / 233280; }; }
  function eWob(pts, amp, seed) {
    var R = eRand(seed), p = pts.map(function (q, i) { var j = (i === 0 || i === pts.length - 1) ? 0.3 : 1; return [q[0] + (R() - 0.5) * amp * j, q[1] + (R() - 0.5) * amp * j]; });
    var d = 'M' + p[0][0].toFixed(1) + ' ' + p[0][1].toFixed(1);
    for (var i = 0; i < p.length - 1; i++) {
      var p0 = p[i - 1] || p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] || p2;
      d += ' C' + (p1[0] + (p2[0] - p0[0]) / 6).toFixed(1) + ' ' + (p1[1] + (p2[1] - p0[1]) / 6).toFixed(1) + ' ' + (p2[0] - (p3[0] - p1[0]) / 6).toFixed(1) + ' ' + (p2[1] - (p3[1] - p1[1]) / 6).toFixed(1) + ' ' + p2[0].toFixed(1) + ' ' + p2[1].toFixed(1);
    }
    return d;
  }
  function eLoop(cx, cy, rx, ry, seed) {
    var pts = [], n = 22, a0 = -2.2;
    for (var i = 0; i <= n; i++) { var a = a0 + (Math.PI * 2 + 0.5) * i / n, g = 1 + 0.05 * i / n; pts.push([cx + Math.cos(a) * rx * g, cy + Math.sin(a) * ry * g]); }
    return eWob(pts, 7, seed);
  }
  function eBox(x0, y0, x1, y1, seed) { return eWob([[x0 + 30, y0 - 4], [x1, y0 + 2], [x1 + 4, y1], [x0, y1 + 3], [x0 - 3, y0 + 8], [x0 + 60, y0 - 6]], 6, seed); }
  function eHead(x, y, ang, len) {
    var a1 = ang + 2.6, a2 = ang - 2.6;
    return 'M' + (x + Math.cos(a1) * len).toFixed(1) + ' ' + (y + Math.sin(a1) * len).toFixed(1) + ' L' + x.toFixed(1) + ' ' + y.toFixed(1) + ' L' + (x + Math.cos(a2) * len).toFixed(1) + ' ' + (y + Math.sin(a2) * len).toFixed(1);
  }
  function ePen(box) {
    var svg = box.querySelector(':scope > .e-pen');
    if (!svg) { svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'e-pen'); svg.setAttribute('viewBox', '0 0 1920 1080'); svg.setAttribute('aria-hidden', 'true'); box.appendChild(svg); }
    return svg;
  }
  function eStroke(svg, d, col, key) {
    var p = svg.querySelector('[data-key="' + key + '"]');
    if (!p) { p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('data-key', key); p.setAttribute('pathLength', '1'); svg.appendChild(p); }
    p.setAttribute('d', d); p.setAttribute('class', 'e-pn e-' + col); p.style.strokeDasharray = 1;
    return p;
  }
  function eDraw(p, at, dur) { if (REDUCED) { p.style.strokeDashoffset = 0; return; } p.style.strokeDashoffset = 1; MO.tw(dur, at, 'inout', function (e) { p.style.strokeDashoffset = (1 - e).toFixed(4); }); }
  function eNoteAt(box, key, txt, col, x, y, align) {
    var n = box.querySelector('.e-note[data-key="' + key + '"]');
    if (!n) { n = emk('div', 'e-note e-' + col, txt, box); n.setAttribute('data-key', key); }
    n.style.left = x + 'px'; n.style.top = y + 'px';
    if (align === 'r') { n.style.left = 'auto'; n.style.right = (1920 - x) + 'px'; }
    return n;
  }
  function eWrite(n, at, dur) {
    n.style.visibility = 'visible';
    if (REDUCED) { n.style.clipPath = ''; n.style.opacity = 1; return; }
    n.style.clipPath = 'inset(-20% 100% -20% -4%)';
    MO.tw(dur || 300, at, 'out', function (e) { n.style.opacity = 1; n.style.clipPath = e >= 1 ? '' : 'inset(-20% ' + ((1 - e) * 100).toFixed(1) + '% -20% -4%)'; });
  }
  function ePenSet(box, on) {
    [].forEach.call(box.querySelectorAll('.e-pen path'), function (p) { p.style.strokeDashoffset = on ? 0 : 1; p.style.opacity = ''; });
    [].forEach.call(box.querySelectorAll('.e-note'), function (n) { n.style.visibility = on ? 'visible' : 'hidden'; n.style.clipPath = ''; n.style.opacity = 1; });
  }

  /* ---- HUD 틀 (모든 장): 네 모서리 괄호 · 아래 눈금자 · 지금 장 눈금 ---- */
  function eHud(s) {
    if (s.querySelector(':scope > .e-hud')) return;
    var h = emk('div', 'e-hud', '<i class="e-c e-c1"></i><i class="e-c e-c2"></i><i class="e-c e-c3"></i><i class="e-c e-c4"></i><div class="e-rl"><i class="e-ph"></i></div>', s);
    var i = slides.indexOf(s), n = slides.length;
    h.querySelector('.e-ph').style.left = (100 * i / Math.max(1, n - 1)).toFixed(2) + '%';
  }
  function eHudIn(s, at) {
    if (REDUCED) return;
    qa(s, ':scope > .e-hud .e-c').forEach(function (c, i) { MO.tw(ET.inn, at + i * 30, 'snap', function (e) { c.style.opacity = e; c.style.transform = e >= 1 ? '' : 'scale(' + lerp(1.6, 1, e).toFixed(3) + ')'; }); });
    var ph = q(s, ':scope > .e-hud .e-ph');
    MO.tw(ET.inn + 100, at + 60, 'snap', function (e) { ph.style.transform = e >= 1 ? '' : 'translateX(' + (-60 * (1 - e)).toFixed(1) + 'px) scaleY(' + lerp(2.2, 1, e).toFixed(3) + ')'; });
  }

  /* ---- 큰 글자 장면 (장 파일의 .e-big) ---- */
  function eDot(s) { var d = q(s, ':scope > .e-dot'); if (!d) d = emk('i', 'e-dot', '', s); return d; }
  function eDotAtSlot(s) {
    var slot = q(s, '.e-big .e-slot'), d = eDot(s), o = eoff(slot, s);
    d.style.left = (o.x + slot.offsetWidth / 2 - 13) + 'px'; d.style.top = (o.y + slot.offsetHeight / 2 - 13) + 'px';
    return d;
  }
  function eBigIn(s, at) {
    var b = q(s, '.e-big'), d = eDotAtSlot(s), k = q(b, '.e-k'), h = q(b, '.e-h');
    b.style.visibility = 'visible'; b.style.opacity = 1; b.style.transform = ''; b.style.filter = '';
    if (REDUCED) { eDropSet(h, true); show(k, true); d.style.opacity = 1; d.style.transform = ''; return; }
    eDropSet(h, false); k.style.opacity = 0; d.style.opacity = 0;
    MO.tw(ET.inn, at, 'snap', function (e) { d.style.opacity = 1; d.style.transform = 'scale(' + (e < 1 ? EZ.bounce(e) : 1).toFixed(3) + ')'; });
    eDrop(h, at + 120);
    eIn(k, at + 120 + MO.split(h).length * ET.st, { dy: 12, blur: 4 });
  }
  function eBigSet(s, on) {
    var b = q(s, '.e-big'), d = eDot(s);
    b.style.visibility = on ? 'visible' : 'hidden'; b.style.opacity = 1; b.style.transform = ''; b.style.filter = '';
    eDropSet(q(b, '.e-h'), on); show(q(b, '.e-k'), true);
    if (on) { eDotAtSlot(s); d.style.opacity = 1; d.style.transform = ''; d.style.width = d.style.height = d.style.borderRadius = ''; } else d.style.opacity = 0;
  }
  // 큰 글자 빠지고 점이 (x, y)로 날아가요 (포물선 · 흐림 꼬리)
  function eDockOut(s, x1, y1, done) {
    var big = q(s, '.e-big'), d = eDot(s);
    big.style.visibility = 'visible'; eOut(big, 0);
    if (REDUCED) { d.style.opacity = 0; if (done) done(); return; }
    eDotAtSlot(s);
    if (x1 === undefined) { MO.tw(ET.out, 0, 'out', function (e) { d.style.opacity = 1 - e; }); return; }
    var x0 = parseFloat(d.style.left), y0 = parseFloat(d.style.top);
    MO.tw(220, 30, 'inout', function (e, t) { d.style.opacity = 1; d.style.left = lerp(x0, x1 - 13, e).toFixed(1) + 'px'; d.style.top = (lerp(y0, y1 - 13, e) - 80 * Math.sin(Math.PI * e)).toFixed(1) + 'px'; d.style.filter = 'blur(' + (3 * Math.sin(Math.PI * t)).toFixed(2) + 'px)'; },
      function () { d.style.filter = ''; if (done) done(); });
  }

  /* ---- 일반 큰 글자 장: 단계 0 = 큰 글자(뒤는 흐리게), 클릭 1부터 = 원래 장 효과(inner)를 한 단계 뒤로 ---- */
  function eInner(s) { return FX[s.getAttribute('data-e-inner')] || {}; }
  function eBg0(s) {   // 큰 글자 뒤에 깔 것 (원래 장의 첫 모습을 흐리게)
    var w = q(s, '.wall3'); if (s.classList.contains('crack') && w) { w.style.opacity = 1; qa(w, '.tb').forEach(function (b) { b.style.transform = ''; b.style.opacity = ''; }); }
    qa(s, '.nt, [data-k="1"]').forEach(function (e) { show(e, true); });
  }
  FX.eBig = {
    enter: function (s, st) {
      eHudIn(s, 0);
      var I = eInner(s);
      if (st === 0) {
        s.classList.add('e-0');
        eInst(function () { if (I.enter) I.enter(s, 0); }); eBg0(s);
        eBigSet(s, true);
        if (V3DIR < 0 || REDUCED) return;
        eBigIn(s, 60);
        return;
      }
      s.classList.remove('e-0'); eBigSet(s, false);
      if (I.enter) I.enter(s, st - 1);
    },
    step: function (s, st, dir) {
      MO.stop();
      var I = eInner(s);
      if (dir === -1 || REDUCED) { eInst(function () { FX.eBig.enter(s, st); }); return; }
      if (st === 1) {
        eBigSet(s, true); s.classList.remove('e-0');
        eDockOut(s);
        V3DIR = 1; if (I.enter) I.enter(s, 0);
        return;
      }
      if (I.step) I.step(s, st - 1, dir);
    }
  };


  /* ---- 허브 도식 (1 · 21장): 가운데 마디에서 가는 선이 그려져 나가고, 주황 점이 선을 따라 달려 마디에 닿으면 마디가 나타나요 ---- */
  function hubPrep(h) {
    if (h.__hub) return h.__hub;
    var svg = q(h, '.e-wires'), nodes = qa(h, '.e-node'), core = q(h, '.e-core'), W = [];
    nodes.forEach(function (n) { n.style.left = (+n.getAttribute('data-x') - n.offsetWidth / 2) + 'px'; n.style.top = (+n.getAttribute('data-y') - n.offsetHeight / 2) + 'px'; });
    var cx = +core.getAttribute('data-x'), cy = +core.getAttribute('data-y');
    nodes.forEach(function (n) {
      if (n === core) return;
      var x = +n.getAttribute('data-x'), y = +n.getAttribute('data-y'), p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      p.setAttribute('d', 'M' + cx + ' ' + cy + ' L' + x + ' ' + y); p.setAttribute('pathLength', '1'); p.setAttribute('class', 'e-wire'); p.style.strokeDasharray = 1;
      svg.insertBefore(p, svg.firstChild);
      var dot = emk('i', 'e-run', '', h);
      W.push({ n: n, p: p, x0: cx, y0: cy, x1: x, y1: y, dot: dot });
    });
    h.__hub = { core: core, W: W };
    return h.__hub;
  }
  function hubSet(h, on) {
    var H = hubPrep(h);
    show(H.core, on); H.core.style.filter = '';
    H.W.forEach(function (w) { show(w.n, on); w.n.style.filter = ''; w.p.style.strokeDashoffset = on ? 0 : 1; w.dot.style.opacity = 0; });
  }
  function hubDraw(h, at) {
    var H = hubPrep(h);
    hubSet(h, false);
    if (REDUCED) { hubSet(h, true); return; }
    eIn(H.core, at, { dy: 0, s: 0.85, blur: 8 });
    H.W.forEach(function (w, i) {
      var t0 = at + 160 + i * 60;
      MO.tw(240, t0, 'inout', function (e) {
        w.p.style.strokeDashoffset = (1 - e).toFixed(4);
        w.dot.style.opacity = e >= 1 ? 0 : 1;
        w.dot.style.left = (lerp(w.x0, w.x1, e) - 6).toFixed(1) + 'px'; w.dot.style.top = (lerp(w.y0, w.y1, e) - 6).toFixed(1) + 'px';
      });
      eIn(w.n, t0 + 200, { dy: 0, s: 0.9, blur: 8 });
    });
  }
  /* 5 하네스: 큰 글자(음절 떨어지기) → 줄기가 아래로 · 클릭 1에 「개발자」 커서가 다섯 칸을 하나씩 끌어 그려요
     (모서리에서 모서리로 끌기 → 맞춤선 · 「24」 간격 → 놓으면 칸 · 끈이 그 칸까지 · 아이콘 톡 · 이름 쳐짐 · 설명 두 줄) → 주홍 점이 끈을 한 번 달리고 → 가만히 */
  var RV = { y0: 620, h: 290, w: 332 };
  function rvParts(s) {
    var B = q(s, '.e-rv2');
    return { B: B, h: q(s, '.e-rvh'), sub: q(s, '.e-rvs'), trunk: q(B, '.e-trunk'), bl: q(B, '.e-barl'), br: q(B, '.e-barr'), brs: qa(B, '.e-br'), boxes: qa(B, '.e-box'),
      mq: q(B, '.e-marq'), gv: q(B, '.e-gv'), dist: q(B, '.e-dist'), run: q(B, '.e-run'), cur: q(B, '.e-cur') };
  }
  function rvBoxSet(b, on) {
    show(b, on); b.style.filter = ''; b.style.transform = '';
    [q(b, '.e-bi'), q(b, 'b'), q(b, 'p')].forEach(function (e) { show(e, on); e.style.filter = ''; });
    var nm = q(b, 'b'); if (nm.__full) nm.textContent = nm.__full;
  }
  function rvSet(s, st) {
    var R = rvParts(s);
    eDropSet(R.h, true); show(R.sub, true);
    [R.trunk, R.bl, R.br].concat(R.brs).forEach(function (p) { p.style.strokeDasharray = 1; p.style.strokeDashoffset = (p === R.trunk || st >= 1) ? 0 : 1; });
    R.boxes.forEach(function (b) { rvBoxSet(b, st >= 1); });
    [R.mq, R.gv, R.dist, R.run].forEach(function (e) { e.style.opacity = 0; });
    curPrep(R.cur); R.cur.style.opacity = st >= 1 ? 1 : 0; curPress(R.cur, false); curAt(R.cur, 1700, 470);
    var sc = q(s, ':scope > .e-scene'); if (sc) sc.style.transform = '';
  }
  FX.eReveal = {
    enter: function (s, st) {
      eHudIn(s, 0);
      rvSet(s, st || 0);
      if (V3DIR < 0 || REDUCED || st > 0) return;
      var R = rvParts(s);
      eDropSet(R.h, false); R.sub.style.opacity = 0; R.trunk.style.strokeDashoffset = 1;
      eDrop(R.h, 120);
      eIn(R.sub, 420, { dy: 12, blur: 4 });
      MO.tw(260, 620, 'inout', function (e) { R.trunk.style.strokeDashoffset = (1 - e).toFixed(4); });
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED) { eInst(function () { FX.eReveal.enter(s, st); }); return; }
      rvSet(s, 0);
      var R = rvParts(s), C = R.cur, SP = 640;
      R.boxes.forEach(function (b) { rvBoxSet(b, false); });
      curAt(C, 1880, 1040); C.style.opacity = 0;
      MO.tw(120, 0, 'out', function (e) { C.style.opacity = e; });
      // 바탕이 아주 조금 흘러요 (멈춘 뒤엔 가만히)
      var sc = q(s, ':scope > .e-scene');
      if (sc) MO.tw(3800, 0, 'out', function (e) { sc.style.transform = e >= 1 ? '' : 'translateX(' + (-18 * Math.sin(Math.PI * e)).toFixed(1) + 'px) scale(1.02)'; });
      R.boxes.forEach(function (b, i) {
        var T = 80 + i * SP, x = b.offsetLeft, y = RV.y0, w = RV.w, h = RV.h, nm = q(b, 'b');
        // ① 커서가 왼쪽 위 모서리로
        curGo(C, x, y, T, 180);
        tw2(1, T + 180, 'linear', function () {}, function () { curPress(C, true); });
        // ② 모서리에서 모서리로 끌기: 점선 영역이 커져요 · 끝에 맞춤선과 「24」
        tw2(220, T + 200, 'out', function (e) {
          R.mq.style.opacity = 1; bdItem(R.mq, { x: x, y: y, w: Math.max(2, w * e), h: Math.max(2, h * e) });
          C.style.transform = 'translate(' + (x + w * e).toFixed(1) + 'px,' + (y + h * e).toFixed(1) + 'px)';
          if (e > 0.85) {
            R.gv.style.opacity = 1; R.gv.style.left = (x + w) + 'px'; R.gv.style.top = (y - 30) + 'px'; R.gv.style.height = (h + 60) + 'px';
            if (i > 0) { R.dist.style.opacity = 1; R.dist.style.left = (x - 24) + 'px'; R.dist.style.top = (y + h / 2 - 14) + 'px'; }
          }
        }, function () { C.__p = { x: x + w, y: y + h }; });
        // ③ 놓으면 칸이 돼요 (살짝 자리 잡기) · 끈이 이 칸까지
        tw2(1, T + 430, 'linear', function () {}, function () { curPress(C, false); R.mq.style.opacity = 0; R.gv.style.opacity = 0; R.dist.style.opacity = 0; });
        b.style.opacity = 0;
        tw2(160, T + 430, 'out', function (e) { b.style.opacity = 1; b.style.transform = e >= 1 ? '' : 'scale(' + lerp(1.03, 1, e).toFixed(4) + ')'; });
        if (i === 0) tw2(200, T + 400, 'inout', function (e) { R.bl.style.strokeDashoffset = (1 - e).toFixed(4); });
        if (i === 3) tw2(120, T + 400, 'inout', function (e) { R.br.style.strokeDashoffset = (1 - e * 0.5).toFixed(4); });
        if (i === 4) tw2(120, T + 400, 'inout', function (e) { R.br.style.strokeDashoffset = (0.5 - e * 0.5).toFixed(4); });
        tw2(140, T + 470, 'out', function (e) { R.brs[i].style.strokeDashoffset = (1 - e).toFixed(4); });
        // ④ 아이콘 톡 → 이름 쳐짐 → 설명 두 줄
        [q(b, '.e-bi'), nm, q(b, 'p')].forEach(function (e) { e.style.opacity = 0; });
        MO.stamp(q(b, '.e-bi'), T + 470, { s: 1.5 });
        tw2(1, T + 520, 'linear', function () {}, function () { MO.type(nm, 0); });
        eIn(q(b, 'p'), T + 560, { dy: 12, blur: 4 });
      });
      // 다 그린 뒤: 커서는 오른쪽 아래로 비켜 서고, 주홍 점이 끈을 한 번 달려요 (줄기 → 왼쪽 끝 → 오른쪽 끝)
      var Tend = 80 + R.boxes.length * SP;
      curGo(C, 1700, 470, Tend, 240);
      var pts = [[960, 450], [960, 585], [248, 585], [1672, 585]], L = [135, 712, 1424], tot = L[0] + L[1] + L[2];
      tw2(700, Tend + 80, 'inout', function (e) {
        var d = e * tot, k = 0; while (k < 2 && d > L[k]) { d -= L[k]; k++; }
        var a = pts[k === 2 ? 2 : k], bb = pts[k + 1], f = Math.min(1, d / L[k]);
        if (k === 2) a = [248, 585];
        R.run.style.opacity = e >= 1 ? 0 : 1; R.run.style.left = (lerp(a[0], bb[0], f) - 6).toFixed(1) + 'px'; R.run.style.top = (lerp(a[1], bb[1], f) - 6).toFixed(1) + 'px';
      });
    }
  };
  /* 21 같이 쓰려고: 표지와 짝 · 글자는 v3made 그대로, 오른쪽 허브가 그려져요 */
  FX.eMade = {
    enter: function (s, st) {
      eHudIn(s, 0);
      FX.v3made.enter(s, st);
      var h = q(s, '.e-hub');
      if (V3DIR < 0 || REDUCED) { hubSet(h, true); return; }
      hubDraw(h, 120);
    }
  };

  /* ============ 1 표지: 점 → 선 → 큰 제목(가운데) · 클릭 1에 제목이 제자리로(FLIP) + 3D 카드 ============ */
  function coverFlip(s) { var h1 = q(s, 'h1'), o = eoff(h1, s), w = h1.offsetWidth, hh = h1.offsetHeight, K = 1.62; return { dx: 960 - (o.x + w / 2), dy: 500 - (o.y + hh / 2), k: K, w: w, h: hh }; }
  function coverPrep(s) { if (q(s, '.e-line')) return; emk('i', 'e-line', '', s); eDot(s); var h1 = q(s, 'h1'); MO.split(h1); h1.style.width = 'fit-content'; }
  function coverSet(s) {
    var h1 = q(s, 'h1'); h1.style.transform = ''; h1.style.filter = ''; eDropSet(h1, true); hubSet(q(s, '.e-hub'), true);
    q(s, '.e-line').style.opacity = 0; eDot(s).style.opacity = 0;
    [q(s, '.m-rule'), q(s, '.tag'), q(s, '.who')].forEach(function (e) { show(e, true); e.style.filter = ''; });
    q(s, '.m-rule').style.transform = 'scaleX(1)';
  }
  FX.eCover = {
    enter: function (s, st) {
      coverPrep(s); eHudIn(s, 0);
      eInst(function () { FX.v3cover.enter(s, 0); });
      if (st >= 1) { s.classList.remove('e-0'); coverSet(s); return; }
      s.classList.add('e-0');
      var inst = V3DIR < 0 || REDUCED, h1 = q(s, 'h1'), F = coverFlip(s), d = eDot(s), ln = q(s, '.e-line'), hub = q(s, '.e-hub');
      h1.style.transformOrigin = '50% 50%';
      h1.style.transform = 'translate(' + F.dx.toFixed(1) + 'px,' + F.dy.toFixed(1) + 'px) scale(' + F.k + ')';
      var base = 500 + F.h * F.k / 2 + 26, half = F.w * F.k / 2;
      ln.style.left = (960 - half) + 'px'; ln.style.width = (2 * half) + 'px'; ln.style.top = base + 'px';
      d.style.left = '947px'; d.style.top = (base - 12) + 'px';
      hubSet(hub, false);
      if (inst) { eDropSet(h1, true); ln.style.opacity = 1; ln.style.transform = ''; d.style.opacity = 0; return; }
      eDropSet(h1, false); ln.style.opacity = 0;
      MO.tw(ET.inn, 80, 'snap', function (e) { d.style.opacity = 1; d.style.transform = 'scale(' + (e < 1 ? EZ.bounce(e) : 1).toFixed(3) + ')'; });
      MO.tw(240, 300, 'snap', function (e) { ln.style.opacity = 1; ln.style.transform = 'scaleX(' + Math.max(0.012, e).toFixed(4) + ')'; d.style.opacity = 1 - e; });
      eDrop(h1, 420);
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED) { eInst(function () { FX.eCover.enter(s, st); }); return; }
      var h1 = q(s, 'h1'), F = coverFlip(s), ln = q(s, '.e-line'), hub = q(s, '.e-hub'), rule = q(s, '.m-rule'), tag = q(s, '.tag'), who = q(s, '.who'), kk = q(s, ':scope > .hd .kicker');
      eDropSet(h1, true); ln.style.opacity = 1; ln.style.transform = ''; eDot(s).style.opacity = 0;
      [rule, tag, who].forEach(function (e) { e.style.opacity = 0; });
      if (kk) kk.style.opacity = 0;
      s.classList.remove('e-0');
      MO.tw(220, 0, 'inout', function (e, t) {
        h1.style.transform = e >= 1 ? '' : 'translate(' + (F.dx * (1 - e)).toFixed(1) + 'px,' + (F.dy * (1 - e)).toFixed(1) + 'px) scale(' + lerp(F.k, 1, e).toFixed(4) + ')';
        h1.style.filter = e >= 1 ? '' : 'blur(' + (5 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      });
      var ro = eoff(rule, s), l0 = parseFloat(ln.style.left), w0 = parseFloat(ln.style.width), t0 = parseFloat(ln.style.top);
      MO.tw(240, 40, 'inout', function (e, t) {
        ln.style.left = lerp(l0, ro.x, e).toFixed(1) + 'px'; ln.style.width = lerp(w0, rule.offsetWidth, e).toFixed(1) + 'px'; ln.style.top = lerp(t0, ro.y, e).toFixed(1) + 'px';
        ln.style.filter = e >= 1 ? '' : 'blur(' + (3 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      }, function () { ln.style.opacity = 0; rule.style.opacity = 1; rule.style.transform = 'scaleX(1)'; });
      if (kk) MO.type(kk, 200);
      eIn(tag, 260, { dy: 24 }); eIn(who, 330, { dy: 24 });
      hubDraw(hub, 220);
    }
  };

  /* ============ 7 AI 앱 화면 짚기: 큰 글자 → 흉내 화면 → 한 클릭에 한 곳 (펜 동그라미 + 큰 카드 [진짜 → 비유]) ============ */
  function appPens(s) {
    var A = q(s, '.e-app'), svg = ePen(A), P = [];
    function box(el) { var o = eoff(el, s); return { x: o.x, y: o.y, w: el.offsetWidth, h: el.offsetHeight }; }
    var W = box(q(A, '.e-win')), Bb = box(q(A, '.e-wa')), I = box(q(A, '.e-wint')), L = box(q(A, '.e-wlg')), S = box(q(A, '.e-wside'));
    var G = {   // 메모 자리: 서로 겹치지 않게 (주방 = 화면 아래 왼쪽 · 요리사 = 말풍선 아래 · 주문서 = 화면 아래 가운데 · 식당 = 제목 줄 · 하네스 = 화면 아래 오른쪽)
      win: { d: eBox(W.x - 14, W.y - 14, W.x + W.w + 14, W.y + W.h + 14, 31), nx: W.x + 6, ny: W.y + W.h + 22 },
      bub: { d: eLoop(Bb.x + Bb.w / 2, Bb.y + Bb.h / 2, Bb.w / 2 + 30, Bb.h / 2 + 26, 9), nx: Bb.x + Bb.w - 230, ny: Bb.y + Bb.h + 34 },
      inp: { d: eLoop(I.x + I.w / 2, I.y + I.h / 2, I.w / 2 + 26, I.h / 2 + 22, 13), nx: I.x + 250, ny: W.y + W.h + 22 },
      logo: { d: eLoop(L.x + L.w / 2, L.y + L.h / 2, L.w / 2 + 22, L.h / 2 + 18, 17), nx: L.x + L.w + 120, ny: L.y - 4 },
      side: { d: eBox(S.x - 10, S.y - 10, S.x + S.w + 10, S.y + S.h + 10, 23), nx: S.x + 10, ny: W.y + W.h + 22 }
    };
    qa(A, '.e-card').forEach(function (c, i) { var k = c.getAttribute('data-pin'), g = G[k]; P.push({ k: k, p: eStroke(svg, g.d, c.getAttribute('data-col'), k), n: eNoteAt(A, k, c.getAttribute('data-note'), c.getAttribute('data-col'), g.nx, g.ny) }); });
    return P;
  }
  function appSet(s, st) {   // st 1~6
    var A = q(s, '.e-app'), P = appPens(s), k = st - 2, win = q(A, '.e-win');
    show(win, true); win.style.filter = ''; win.style.transform = '';
    qa(A, '.e-hl').forEach(function (e) { e.classList.remove('e-hl'); });
    qa(A, '.e-card').forEach(function (c, i) {
      var on = i <= k, cur = i === k;
      P[i].p.style.strokeDashoffset = on ? 0 : 1; P[i].p.style.opacity = cur ? 1 : 0.14;
      P[i].n.style.visibility = on ? 'visible' : 'hidden'; P[i].n.style.clipPath = ''; P[i].n.style.opacity = cur ? 1 : 0.38;
      show(c, cur); c.style.visibility = ''; c.style.filter = ''; q(c, '.e-ar path').style.strokeDashoffset = 0;
      qa(c, '.e-cr, .e-row, .e-se').forEach(function (e) { show(e, true); e.style.filter = ''; });
      if (cur) q(A, '[data-pin="' + P[i].k + '"]:not(.e-card)').classList.add('e-hl');
    });
    var al = q(A, '.e-also'); if (al) { show(al, k >= qa(A, '.e-card').length - 1); al.style.filter = ''; }
  }
  FX.eApp = {
    enter: function (s, st) {
      eHudIn(s, 0);
      var hd = q(s, ':scope > .hd'); [q(hd, 'h2'), q(hd, '.kicker')].forEach(function (e) { show(e, true); e.style.filter = ''; });
      if (st === 0) {
        s.classList.add('e-0'); q(s, '.e-app').style.display = 'none';
        eBigSet(s, true);
        if (V3DIR < 0 || REDUCED) return;
        eBigIn(s, 60);
        return;
      }
      s.classList.remove('e-0'); q(s, '.e-app').style.display = '';
      eBigSet(s, false);
      appSet(s, st);
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED) { eInst(function () { FX.eApp.enter(s, st); }); return; }
      var A = q(s, '.e-app');
      if (st === 1) {   // 큰 글자 빠짐 → 점이 로고 자리로 → 화면이 그 점에서 펼쳐져요
        s.classList.remove('e-0'); A.style.display = ''; appSet(s, 1);
        var hd = q(s, ':scope > .hd'); eIn(q(hd, 'h2'), 90, { dy: 40, blur: 10 }); eIn(q(hd, '.kicker'), 60, { dy: 20 });
        var lg = eoff(q(A, '.e-wlg'), s), win = q(A, '.e-win'), d = eDot(s);
        win.style.opacity = 0;
        eDockOut(s, lg.x + 21, lg.y + 21);
        win.style.transformOrigin = '7% 6%';
        if (!REDUCED) MO.tw(240, 250, 'snap', function (e) { d.style.opacity = 1 - e; win.style.opacity = clamp01(e * 3); win.style.transform = e >= 1 ? '' : 'scale(' + lerp(0.04, 1, e).toFixed(4) + ')'; win.style.filter = e >= 1 ? '' : 'blur(' + (6 * (1 - e)).toFixed(2) + 'px)'; });
        return;
      }
      appSet(s, st - 1);
      var k = st - 2, P = appPens(s), cards = qa(A, '.e-card'), card = cards[k], prev = cards[k - 1];
      appSet(s, st); show(card, false);
      P[k].p.style.strokeDashoffset = 1; P[k].n.style.visibility = 'hidden';
      if (prev) { show(prev, true); eOut(prev, 0); MO.tw(1, ET.out + 5, 'linear', function () {}, function () { prev.style.visibility = ''; show(prev, false); }); }
      eDraw(P[k].p, 40, 280); eWrite(P[k].n, 240, 280);
      var parts = qa(card, '.e-cr, .e-row, .e-se');
      card.style.opacity = 1; parts.forEach(function (e) { e.style.opacity = 0; });
      eIn(parts[0], 160, { dx: -40, dy: 0 });
      var ar = q(card, '.e-ar path'); ar.style.strokeDashoffset = 1; MO.draw(ar, 300, 180, 'snap');
      eIn(parts[1], 400, { dy: 30, s: 0.94, blur: 10 }); eIn(parts[2], 520, { dy: 14 });
    }
  };

  /* ============ 8 주방 하나: 가운데 큰 요리사 · 도구가 두 개씩 (이름도 같아요 · 이름이 돌아가며 · 점선 = 식당마다 달라요) · 끝에 하네스 고리 ============ */
  function kitGeo(s) { var K = q(s, '.e-kit'), ch = q(K, '.e-chef'), co = eoff(ch, s); return { K: K, ch: ch, x: co.x, y: co.y, w: ch.offsetWidth, h: ch.offsetHeight, cx: co.x + ch.offsetWidth / 2, cy: co.y + ch.offsetHeight / 2 }; }
  function kitLines(s) {
    var G = kitGeo(s), svg = q(G.K, '.e-kl'), cy = G.y + G.h * 0.45;
    return qa(G.K, '.e-tool').map(function (t, i) {
      var o = eoff(t, s), r = t.classList.contains('e-r'), x = r ? o.x - 14 : o.x + t.offsetWidth + 14, y = o.y + 52;
      var p = svg.querySelector('[data-i="' + i + '"]');
      if (!p) { p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('data-i', i); p.setAttribute('pathLength', '1'); p.setAttribute('class', 'e-kln' + (t.classList.contains('e-part') ? ' e-part' : '')); svg.appendChild(p); }
      p.setAttribute('d', 'M' + G.cx.toFixed(0) + ' ' + cy.toFixed(0) + ' L' + x.toFixed(0) + ' ' + y.toFixed(0));
      p.style.strokeDasharray = t.classList.contains('e-part') ? '' : 1;
      return p;
    });
  }
  function kitPens(s) {   // 고리(하네스) 하나
    var G = kitGeo(s), svg = ePen(G.K);
    return { ring: eStroke(svg, eLoop(G.cx, G.cy - 10, G.w / 2 + 64, G.h / 2 + 4, 41), 'acc', 'ring') };
  }
  // 단계: 0 주방 + 요리사 · 1 찾아보기 · 파일 읽기 · 2 스킬 · 그림 만들기 · 3 「이 밖에도」 한 줄 · 4 고리 + 큰 결론
  function kitSet(s, g) {
    var G = kitGeo(s), K = G.K, L = kitLines(s), P = kitPens(s);
    show(q(K, '.e-kp'), true); show(G.ch, true); G.ch.style.filter = '';
    qa(K, '.e-tool').forEach(function (t, i) {
      var on = +t.getAttribute('data-g') <= g; show(t, on); t.style.filter = '';
      L[i].style.strokeDashoffset = on ? 0 : 1; L[i].style.opacity = on ? 1 : 0;
    });
    var mo = q(K, '.e-more'); show(mo, g >= 3); mo.style.filter = '';
    q(K, '.e-kcap').style.display = g >= 4 ? 'none' : '';
    qa(K, '.e-kcap p').forEach(function (p) { show(p, g < 4); });
    P.ring.style.strokeDashoffset = g >= 4 ? 0 : 1;
    var pu = q(s, '.hxpunch'); show(pu, g >= 4); show(q(pu, '.p1'), true); show(q(pu, '.p2'), true); MO.kinSet(q(pu, '.m-kin'), g >= 4);
  }
  FX.eKitchen = {
    enter: function (s, st) {
      eHudIn(s, 0);
      v3hd(s, 60, V3DIR < 0 || st > 0 || REDUCED);
      kitSet(s, st);
      if (V3DIR < 0 || st > 0 || REDUCED) return;
      var K = q(s, '.e-kit');
      eIn(q(K, '.e-kp'), 60, { dy: 0, s: 1.02, blur: 8 });
      MO.spring(q(K, '.e-chef'), 160, { s: 0.3, dy: 40, bouncy: true });
      eIn(q(K, '.e-kcap p[data-c="0"]'), 420, { dy: 20 });
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED) { eInst(function () { FX.eKitchen.enter(s, st); }); return; }
      v3hd(s, 0, true);
      kitSet(s, st - 1);
      var G = kitGeo(s), K = G.K, tl = qa(K, '.e-tool'), L = kitLines(s), g = st;
      if (g <= 2) {   // 도구 두 개: 요리사 쪽에서 튀어나와 자리(흐림 꼬리) + 선
        tl.forEach(function (t, i) {
          if (+t.getAttribute('data-g') !== g) return;
          var o = eoff(t, s), dx = G.cx - (o.x + t.offsetWidth / 2), dy = G.cy - (o.y + 60), j = i % 2;
          t.style.opacity = 0;
          eIn(t, 40 + j * 90, { dx: dx * 0.3, dy: dy * 0.3, s: 0.9, blur: 10, dur: 230 });
          L[i].style.opacity = 1; L[i].style.strokeDashoffset = 1; MO.draw(L[i], 20 + j * 90, 200, 'snap');
        });
        return;
      }
      if (g === 3) { var mo = q(K, '.e-more'); mo.style.opacity = 0; eIn(mo, 40, { dy: 16, blur: 6 }); return; }
      MO.tw(1, ET.out, 'linear', function () {}, function () { q(K, '.e-kcap').style.display = 'none'; });
      var P2 = kitPens(s); P2.ring.style.strokeDashoffset = 1; eDraw(P2.ring, 40, 360);
      MO.gather(tl, G.cx, G.cy, 200, { dur: 360, pull: 0.08, turn: 0.05 });
      var pu = q(s, '.hxpunch'), p2 = q(pu, '.m-kin');
      show(pu, true); show(q(pu, '.p2'), true); MO.kinSet(p2, false); q(pu, '.p1').style.opacity = 0;
      eIn(q(pu, '.p1'), 420, { dy: 24 }); MO.kin(p2, 600, { gap: 30, dur: 260 });
    }
  };

  /* ============ 15 바닥: 큰 글자 → 점이 떨어져 바닥 선 → 막대 · 하네스 막대 + 펜 · 결론 + 근거 낱말 밝히기 ============ */
  function flGeo(s) {
    var lo = q(s, '.lv.lo .bar'), hi = q(s, '.lv.hi .bar'), keep = hi.style.height;
    hi.style.height = '';
    var a = eoff(lo, s), b = eoff(hi, s), r = { lx: a.x, ly: a.y, lw: lo.offsetWidth, lh: lo.offsetHeight, hx: b.x, hy: b.y, hw: hi.offsetWidth, hh: hi.offsetHeight };
    hi.style.height = keep;
    r.floor = r.ly + r.lh;
    return r;
  }
  function flPens(s) {
    var R = flGeo(s), svg = ePen(s), x = R.hx + 46, y0 = R.ly - 8, y1 = R.hy + 10;
    var p = eStroke(svg, eWob([[x, y0], [x + 2, (y0 + y1) / 2], [x, y1]], 5, 21) + ' ' + eHead(x, y1, -Math.PI / 2, 22) + ' ' + eHead(x, y0, Math.PI / 2, 22), 'red', 'gap');
    var ny = (y0 + y1) / 2 - 34, nx = R.hx - 48;
    var n = eNoteAt(s, 'gap', '못 나와도 이만큼은 나와요', 'red', nx, ny, 'r');
    var l = eStroke(svg, eWob([[nx - 4, ny + 56], [nx + 18, ny + 62], [x - 12, (y0 + y1) / 2 + 6]], 4, 5), 'red', 'gapl');
    return { p: p, n: n, l: l };
  }
  function flPills(s, st, anim) {
    qa(s, '.e-pills .e-sg').forEach(function (g, i) {
      var f = q(g, 'i'), on = i < st, cur = i === st - 1;
      g.classList.toggle('e-cur', cur); g.classList.toggle('e-done', on);
      if (anim && cur && !REDUCED) MO.tw(ET.inn + 60, 80, 'snap', function (e) { f.style.transform = 'scaleX(' + e.toFixed(4) + ')'; });
      else f.style.transform = on ? 'scaleX(1)' : 'scaleX(0)';
    });
  }
  function flEv(s, on) { if (!q(s, '.e-ev')) return; qa(s, '.e-ev .e-w').forEach(function (w) { w.classList.toggle('e-lit', on); }); }
  function flBase(s) { var b = q(s, ':scope > .e-base'); if (!b) b = emk('i', 'e-base', '', s); return b; }
  function flSet(s, st) {
    s.classList.toggle('e-0', st === 0);
    eInst(function () { FX.v3gen.enter(s, Math.max(0, st - 1)); });
    var lv = q(s, '.levels'), ev = q(s, '.e-ev'), base = flBase(s), R = flGeo(s);
    base.style.left = R.lx + 'px'; base.style.top = R.floor + 'px'; base.style.width = (R.hx + R.hw - R.lx) + 'px'; base.style.transform = '';
    q(s, '.lv.lo .bar').style.transform = '';
    flPills(s, st); flPens(s); ePenSet(s, st >= 2);
    if (ev) { ev.style.visibility = st >= 3 ? 'visible' : 'hidden'; show(ev, true); flEv(s, st >= 3); }
    var hd = q(s, ':scope > .hd'); [q(hd, 'h2'), q(hd, '.kicker')].forEach(function (e) { show(e, true); e.style.filter = ''; });
    qa(s, '[data-k], .lv .lb, .lv .ft, .lv .bar, .e-pills').forEach(function (e) { e.style.filter = ''; });
    show(q(s, '.e-pills'), true);
    if (st === 0) { eBigSet(s, true); base.style.opacity = 0; lv.classList.add('e-bg'); } else { eBigSet(s, false); base.style.opacity = 1; eBgOff(lv); }
  }
  FX.eFloor = {
    enter: function (s, st) {
      eHudIn(s, 0);
      flSet(s, st);
      if (st === 0 && !(V3DIR < 0 || REDUCED)) { eBigIn(s, 60); eDrift(q(s, '.levels'), 0); }
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED) { eInst(function () { FX.eFloor.enter(s, st); }); return; }
      if (st === 1) {
        flSet(s, 0);
        var d = eDot(s), lv = q(s, '.levels'), R = flGeo(s), base = flBase(s);
        s.classList.remove('e-0');
        eInst(function () { FX.v3gen.enter(s, 0); });
        eBgLift(lv);
        var hd = q(s, ':scope > .hd'); eIn(q(hd, 'h2'), 90, { dy: 40, blur: 10 }); eIn(q(hd, '.kicker'), 60, { dy: 20 });
        flPills(s, 1, true); eIn(q(s, '.e-pills'), 120, { dy: 8, blur: 4 });
        var lo = q(s, '.lv.lo'), bar = q(lo, '.bar'), lb = q(lo, '.lb'), ft = q(lo, '.ft'), L = R.lx, Rr = R.hx + R.hw, Y = R.floor;
        [lb, ft].forEach(function (e) { e.style.opacity = 0; });
        bar.style.transformOrigin = '50% 100%'; bar.style.transform = 'scaleY(0)';
        base.style.opacity = 0;
        eDockOut(s, L, Y, function () {
          MO.tw(230, 0, 'snap', function (e) { base.style.opacity = 1; base.style.transform = 'scaleX(' + Math.max(0.01, e).toFixed(4) + ')'; d.style.left = lerp(L - 13, Rr - 13, e).toFixed(1) + 'px'; d.style.transform = 'scale(' + lerp(0.7, 0.3, e).toFixed(3) + ')'; d.style.opacity = 1 - e; });
          MO.tw(200, 110, 'snap', function (e) { bar.style.transform = e >= 1 ? '' : 'scaleY(' + e.toFixed(4) + ')'; });
          eIn(lb, 170, { dy: 20 }); eIn(ft, 210, { dy: 14 });
        });
        return;
      }
      flSet(s, st - 1);
      eInst(function () { FX.v3gen.set(s, st - 2); });
      flPills(s, st, true);
      if (st === 2) {
        var hi = q(s, '.lv.hi'), hb = q(hi, '.bar'), H = flGeo(s).hh, P = flPens(s);
        ePenSet(s, false);
        hi.style.opacity = 1; [q(hi, '.lb'), q(hi, '.ft')].forEach(function (e) { e.style.opacity = 0; });
        MO.tw(240, 0, 'snap', function (e) { hb.style.height = lerp(0, H, e).toFixed(1) + 'px'; hb.style.filter = e >= 1 ? '' : 'blur(' + (4 * (1 - e)).toFixed(2) + 'px)'; if (e >= 1) hb.style.height = ''; });
        eIn(q(hi, '.lb'), 160, { dy: 24 }); eIn(q(hi, '.ft'), 220, { dy: 14 });
        eDraw(P.p, 230, 260); eWrite(P.n, 330, 300); eDraw(P.l, 520, 160);
      } else if (st === 3) {
        var cap = q(s, '.capline'), ev = q(s, '.e-ev'), W = ev ? qa(ev, '.e-w') : [];
        eIn(cap, 0, { dy: 30, blur: 8 });
        if (ev) { ev.style.visibility = 'visible'; flEv(s, false); eIn(ev, 120, { dy: 10, blur: 3 });
          W.forEach(function (w, i) { MO.tw(1, 320 + i * 70, 'linear', function () {}, function () { w.classList.add('e-lit'); }); }); }
      }
    }
  };



  /* 처음 한 번: 모든 장에 HUD 틀 · 로봇 요리사 그림 조각 넣기 */
  slides.forEach(function (s) { eHud(s); });
  setTimeout(function () { slides.forEach(function (s) {   // PUPPET은 deck.js 뒤쪽에서 채워져요 → 한 박자 뒤에
    [].forEach.call(s.querySelectorAll('img[data-puppet]'), function (im) { var k = im.getAttribute('data-puppet'); if (PUPPET[k]) im.src = PUPPET[k]; });
    [].forEach.call(s.querySelectorAll('[data-puppet-bg]'), function (e) { var k = e.getAttribute('data-puppet-bg'); e.style.backgroundImage = 'linear-gradient(var(--e-kshade),var(--e-kshade))' + (PUPPET[k] ? ',url(' + PUPPET[k] + ')' : ''); });
  }); }, 0);

  /* 장면 바탕 넣기: 장 파일의 data-e-bg (A 밤의 주방 · B 작업실 · C 추상 빛) · 같은 부탁 비교 4장은 B */
  slides.forEach(function (s) {
    var bg = s.getAttribute('data-e-bg') || (s.classList.contains('cmp') ? 'B' : '');
    if (!bg || s.querySelector(':scope > .e-scene')) return;
    s.setAttribute('data-e-bg', bg);
    var d = document.createElement('div'); d.className = 'e-scene'; d.setAttribute('data-il', 'e-bg-' + bg.toLowerCase());
    s.insertBefore(d, s.firstChild);
  });

  /* ============ 커서 (디자인 도구처럼): 이름표 붙은 화살표 · 누르면 쥔 손 · 끌기 · 모서리 늘이기 · 영역 고르기 · 맞춤선 · 흔적 ============
     9장 클릭 1: 하네스의 네 부분(요리사(AI) · 레시피 · 도구 · 점검)이 커서가 되어, 실제로 나온 결과 화면(10장의 하네스 AI 화면)을 끌어다 놓고 맞춰요.
     17~19장: 커서 하나가 어디를 누르는지 보여 줘요. 움직임 줄이기 · 뒤로 가기 = 끝 모습 바로. */
  // icons: hand-grab
  // 늦게 시작하는 박자: 시작 전에는 아무것도 칠하지 않아요 (MO.tw는 만들 때 시작 모습을 바로 칠하니까, 여러 박자를 미리 줄 세울 때는 이것을)
  function tw2(dur, at, ease, fn, done) { var on = false; return MO.tw(dur, at, ease, function (e, t) { if (!on) { if (t === 0) return; on = true; } fn(e, t); }, done); }
  var CUR_SVG = '<svg class="e-ptr" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2.5 L4 19.5 L8.6 15.3 L11.8 22 L14.9 20.6 L11.8 14 L18.2 13.6 Z"/></svg><svg class="ic e-hand" aria-hidden="true"><use href="#hand-grab"/></svg>';
  function curPrep(c) { if (!c.__p) { c.insertAdjacentHTML('afterbegin', CUR_SVG); c.__p = { x: 0, y: 0 }; } return c; }
  function curAt(c, x, y) { c.__p = { x: x, y: y }; c.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)'; }
  function curGo(c, x, y, at, dur, done) {   // 목적 있는 길: 빠르게 출발해 부드럽게 멈춤 (ease-out)
    var x0, y0;
    return tw2(dur || 220, at, 'out', function (e, t) {
      if (x0 === undefined) { x0 = c.__p.x; y0 = c.__p.y; }
      c.style.opacity = 1;
      var bx = lerp(x0, x, e), by = lerp(y0, y, e) - Math.sin(Math.PI * e) * 18;
      c.style.transform = 'translate(' + bx.toFixed(1) + 'px,' + by.toFixed(1) + 'px)';
      if (e >= 1) c.__p = { x: x, y: y };
    }, done);
  }
  function curPress(c, on) { c.classList.toggle('e-grab', on); }
  function curClick(c, at) {   // 누름 → 동그라미 퍼짐
    tw2(1, at, 'linear', function () {}, function () { curPress(c, true); });
    tw2(1, at + 120, 'linear', function () {}, function () { curPress(c, false); });
    var r = q(c, '.e-ring'); if (!r) r = emk('i', 'e-ring', '', c);
    tw2(260, at + 60, 'out', function (e) { r.style.opacity = (1 - e).toFixed(3); r.style.transform = 'scale(' + lerp(0.3, 1.6, e).toFixed(3) + ')'; });
  }
  /* 9장 판 */
  var BD = { W: 900, H: 506 };
  function bdFinal() { var w = BD.W - 48, h = w * 9 / 16; return { x: 24, y: (BD.H - h) / 2, w: w, h: h }; }
  function bdItem(it, r) { it.style.left = r.x.toFixed(1) + 'px'; it.style.top = r.y.toFixed(1) + 'px'; it.style.width = r.w.toFixed(1) + 'px'; it.style.height = r.h.toFixed(1) + 'px'; }
  function bdSel(s, r, on) { var e = q(s, '.e-sel'); e.style.opacity = on ? 1 : 0; if (r) bdItem(e, r); }
  function bdGuides(s, list) {   // list: [['v', x] | ['h', y] | ['c', x]], 거리 이름표
    qa(s, '.e-gd').forEach(function (g) { g.style.opacity = 0; });
    var d = q(s, '.e-dist'); d.style.opacity = 0;
    (list || []).forEach(function (g) {
      var el = q(s, g[0] === 'v' ? '.e-gv' : g[0] === 'h' ? '.e-gh' : '.e-gc');
      el.style.opacity = 1;
      if (g[0] === 'h') el.style.top = g[1] + 'px'; else el.style.left = g[1] + 'px';
      if (g[2]) { d.textContent = g[2]; d.style.left = (g[3] || 0) + 'px'; d.style.top = (g[4] || 0) + 'px'; d.style.opacity = 1; }
    });
  }
  function bdShot(s) {   // 10장의 하네스 AI 결과 화면을 그대로 써요 (지어낸 화면 없음)
    var im = q(s, '.e-shot');
    if (!im.getAttribute('src')) { var src = q(s, '.e-src img') || stage.querySelector('.cmp .shot.h .frame img'); if (src) im.src = src.src; }
    return im;
  }
  var BDCUR = { chef: [BD.W - 160, BD.H - 40], tool: [BD.W - 70, 150], recipe: [BD.W - 40, BD.H + 20], check: [BD.W - 20, -10] };
  function bdSet(s, on) {
    var B = q(s, '.e-board'), it = q(s, '.e-item');
    bdShot(s);
    B.style.visibility = on ? 'visible' : 'hidden';
    show(q(B, '.e-art'), true); q(B, '.e-art').style.filter = '';
    bdItem(it, bdFinal()); it.style.opacity = 1; it.style.transform = ''; it.style.filter = '';
    qa(it, '.e-ghost').forEach(function (g) { g.style.opacity = 0; });
    bdSel(s, null, false); q(s, '.e-marq').style.opacity = 0; bdGuides(s, []);
    var ok = q(s, '.e-ok'); ok.style.opacity = 1; ok.style.transform = '';
    qa(B, '.e-cur').forEach(function (c) { curPrep(c); var p = BDCUR[c.getAttribute('data-who')]; curAt(c, p[0], p[1]); c.style.opacity = 1; curPress(c, false); });
    show(q(B, '.e-cap'), true);
    var sp = q(s, '.e-spot'); if (sp) sp.style.opacity = on ? 0 : '';
  }
  function bdPlay(s) {
    var B = q(s, '.e-board'), it = q(s, '.e-item'), art = q(B, '.e-art'), C = {}, G = qa(it, '.e-ghost');
    qa(B, '.e-cur').forEach(function (c) { curPrep(c); C[c.getAttribute('data-who')] = c; c.style.opacity = 0; curPress(c, false); });
    bdSet(s, true);
    var sp = q(s, '.e-spot'); if (sp) { sp.style.opacity = 1; tw2(ET.out, 0, 'out', function (e) { sp.style.opacity = 1 - e; }); }
    qa(B, '.e-cur').forEach(function (c) { c.style.opacity = 0; });
    q(s, '.e-ok').style.opacity = 0; show(q(B, '.e-cap'), false);
    var F = bdFinal(), small = { x: BD.W - 250, y: BD.H - 150, w: 220, h: 124 }, mid = { x: 24, y: 24, w: 420, h: 236 };
    // 판이 열리고 → 오른쪽 아래 「받침」에 작은 결과 화면 하나
    eIn(art, 0, { dy: 0, s: 0.97, blur: 8 });
    bdItem(it, small); it.style.opacity = 0; eIn(it, 120, { dy: 16, blur: 6 });
    // ① 도구: 화면을 집어(쥔 손) 왼쪽 위로 끌어다 놓기 · 흔적 · 맞춤선 24 · 놓으면 살짝 자리 잡기
    var T = C.tool; curAt(T, BD.W + 60, 60);
    curGo(T, small.x + 110, small.y + 60, 260, 230);
    tw2(1, 500, 'linear', function () {}, function () { curPress(T, true); });
    tw2(260, 560, 'out', function (e, t) {
      var r = { x: lerp(small.x, mid.x, e), y: lerp(small.y, mid.y, e), w: lerp(small.w, mid.w, e), h: lerp(small.h, mid.h, e) };
      bdItem(it, r); it.style.filter = t >= 1 ? '' : 'blur(' + (3 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      G.forEach(function (g, i) { var k = Math.max(0, e - 0.18 * (i + 1)); g.style.opacity = t >= 1 ? 0 : (0.22 / (i + 1)).toFixed(3); g.style.transform = 'translate(' + ((lerp(small.x, mid.x, k) - r.x)).toFixed(1) + 'px,' + ((lerp(small.y, mid.y, k) - r.y)).toFixed(1) + 'px)'; });
      T.style.transform = 'translate(' + (r.x + 110 * r.w / small.w * 0.5).toFixed(1) + 'px,' + (r.y + 60).toFixed(1) + 'px)';
      if (e > 0.82) bdGuides(s, [['v', 24, '24', 30, 8], ['h', 24]]);
    }, function () { T.__p = { x: mid.x + 210, y: mid.y + 60 }; curPress(T, false); });
    tw2(140, 830, 'out', function (e) { it.style.transform = e >= 1 ? '' : 'scale(' + lerp(1.02, 1, e).toFixed(4) + ')'; });
    tw2(1, 980, 'linear', function () {}, function () { bdGuides(s, []); });
    curGo(T, BDCUR.tool[0], BDCUR.tool[1], 990, 240);
    // ② 레시피: 선택 테두리 · 오른쪽 아래 모서리 손잡이를 끌어 판 가득 늘이기 · 오른쪽 맞춤선 24
    var R = C.recipe; curAt(R, BD.W - 20, BD.H + 40);
    curGo(R, mid.x + mid.w, mid.y + mid.h, 980, 220);
    tw2(1, 1000, 'linear', function () {}, function () { bdSel(s, mid, true); });
    tw2(1, 1220, 'linear', function () {}, function () { curPress(R, true); });
    var big = { x: 24, y: 24, w: F.w, h: F.h };
    tw2(260, 1260, 'out', function (e) {
      var r = { x: 24, y: 24, w: lerp(mid.w, big.w, e), h: lerp(mid.h, big.h, e) };
      bdItem(it, r); bdSel(s, r, true);
      R.style.transform = 'translate(' + (r.x + r.w).toFixed(1) + 'px,' + (r.y + r.h).toFixed(1) + 'px)';
      if (e > 0.8) bdGuides(s, [['v', BD.W - 24, '24', BD.W - 60, 8]]);
    }, function () { R.__p = { x: big.x + big.w, y: big.y + big.h }; curPress(R, false); });
    tw2(1, 1620, 'linear', function () {}, function () { bdGuides(s, []); bdSel(s, null, false); });
    curGo(R, BDCUR.recipe[0], BDCUR.recipe[1], 1630, 220);
    // ③ 요리사(AI): 영역 끌어 고르기 → 묶음을 가운데로 옮기기 · 가운데 맞춤선
    var K = C.chef; curAt(K, -40, -30);
    var mq = q(s, '.e-marq');
    curGo(K, -14, -12, 1600, 200);
    tw2(1, 1800, 'linear', function () {}, function () { curPress(K, true); });
    tw2(240, 1820, 'out', function (e) {
      var x1 = lerp(-14, BD.W - 4, e), y1 = lerp(-12, BD.H - 4, e);
      mq.style.opacity = 1; bdItem(mq, { x: -14, y: -12, w: x1 + 14, h: y1 + 12 });
      K.style.transform = 'translate(' + x1.toFixed(1) + 'px,' + y1.toFixed(1) + 'px)';
    }, function () { K.__p = { x: BD.W - 4, y: BD.H - 4 }; curPress(K, false); mq.style.opacity = 0; bdSel(s, big, true); });
    tw2(1, 2120, 'linear', function () {}, function () { curPress(K, true); });
    tw2(220, 2150, 'out', function (e) {
      var r = { x: 24, y: lerp(24, F.y, e), w: F.w, h: F.h }; bdItem(it, r); bdSel(s, r, true);
      K.style.transform = 'translate(' + (BD.W - 160).toFixed(1) + 'px,' + (lerp(BD.H - 40 - (F.y - 24), BD.H - 40, e)).toFixed(1) + 'px)';
      if (e > 0.7) bdGuides(s, [['h', BD.H / 2], ['c', BD.W / 2]]);
    }, function () { K.__p = { x: BD.W - 160, y: BD.H - 40 }; curPress(K, false); });
    tw2(1, 2480, 'linear', function () {}, function () { bdGuides(s, []); bdSel(s, null, false); });
    // ④ 점검: 오른쪽 위로 와서 톡 → ✓
    var Kc = C.check; curAt(Kc, BD.W + 40, -60);
    curGo(Kc, BDCUR.check[0], BDCUR.check[1], 2400, 220);
    curClick(Kc, 2620);
    MO.stamp(q(s, '.e-ok'), 2660, { s: 1.6 });
    eIn(q(B, '.e-cap'), 2760, { dy: 10, blur: 3 });
  }
  FX.eSection = {
    enter: function (s, st) {
      eHudIn(s, 0);
      FX.v3section.enter(s, 0);
      bdSet(s, st >= 1);
    },
    step: function (s, st, dir) {
      MO.stop();
      eInst(function () { FX.v3section.enter(s, 0); });
      if (dir === -1 || REDUCED) { bdSet(s, st >= 1); return; }
      if (st === 1) bdPlay(s);
    }
  };
  /* 17~19 실습: 커서 하나 (data-to = 누를 곳 · data-step = 몇 번째 클릭에) */
  function labCur(s, st, anim) {
    var c = q(s, ':scope > .e-cur.e-solo'); if (!c) return;
    curPrep(c);
    var n = +c.getAttribute('data-step'), tg = q(s, c.getAttribute('data-to'));
    if (!tg || st < n) { c.style.opacity = 0; return; }
    var o = eoff(tg, s), x = o.x + tg.offsetWidth * 0.55, y = o.y + tg.offsetHeight * 0.6;
    curPress(c, false);
    if (!anim || REDUCED || st !== n) { curAt(c, x, y); c.style.opacity = 1; return; }
    c.style.opacity = 0; curAt(c, x + 260, y + 180);
    var at = n === 0 ? 1300 : 420;   // 3장은 글자가 쳐진 뒤에
    MO.tw(120, at, 'out', function (e) { c.style.opacity = e; });
    curGo(c, x, y, at, 260);
    curClick(c, at + 300);
  }
  FX.eLab = {
    enter: function (s, st) { eHudIn(s, 0); FX.v3gen.enter(s, st); var c = q(s, ':scope > .e-cur.e-solo'); labCur(s, st, V3DIR > 0 && st === 0 && c && +c.getAttribute('data-step') === 0); },
    step: function (s, st, dir) { FX.v3gen.step(s, st, dir); labCur(s, st, dir !== -1); }
  };

  /* ============ 2 여기저기서: 큰 글자 → 위 가운데로 줄어들어 머리글 자리 → 말풍선 여덟 개가 여기저기서 하나씩 「띠용」 ============
     말풍선 꼬리는 머리글 쪽을 가리켜요. 한 개 약 350ms, 사이 220ms. 움직임 줄이기 · 뒤로 = 끝 모습 바로 */
  var POUR_AT = [[150, 330], [1340, 330], [520, 500], [1200, 510], [140, 670], [860, 680], [1220, 840], [430, 840]];   // 말풍선 왼쪽 위 (무대 좌표)
  function pourPrep(s) {
    if (s.__pour) return;
    qa(s, '.e-bubs .nt').forEach(function (b, i) {
      var p = POUR_AT[i]; b.style.left = p[0] + 'px'; b.style.top = p[1] + 'px';
      var tail = q(b, '.e-tail'); if (!tail) tail = emk('i', 'e-tail', '', b);
    });
    s.__pour = true;
  }
  function pourTails(s) {   // 꼬리: 말풍선 가운데에서 머리글(가운데 위) 쪽으로 난 선이 테두리와 만나는 곳
    var hx = 960, hy = 250;
    qa(s, '.e-bubs .nt').forEach(function (b) {
      var w = b.offsetWidth, h = b.offsetHeight, cx = b.offsetLeft + w / 2, cy = b.offsetTop + h / 2, a = Math.atan2(hy - cy, hx - cx);
      var t = Math.min(Math.abs((w / 2) / (Math.cos(a) || 1e-6)), Math.abs((h / 2) / (Math.sin(a) || 1e-6)));
      var tl = q(b, '.e-tail'); tl.style.left = (w / 2 + Math.cos(a) * t - 2).toFixed(1) + 'px'; tl.style.top = (h / 2 + Math.sin(a) * t - 13).toFixed(1) + 'px';
      tl.style.transform = 'rotate(' + (a * 180 / Math.PI).toFixed(1) + 'deg)';
    });
  }
  function pourSet(s, st) {
    pourPrep(s);
    var hd = q(s, ':scope > .hd'), h2 = q(hd, 'h2'), k = q(hd, '.kicker');
    s.classList.toggle('e-0', st === 0);
    eBigSet(s, st === 0);
    MO.wipeSet(h2, true); [h2, k].forEach(function (e) { show(e, true); e.style.filter = ''; e.style.transform = ''; });
    if (k.__full) k.textContent = k.__full;
    qa(s, '.e-bubs .nt').forEach(function (b) { show(b, st >= 1); b.style.filter = ''; b.style.transform = ''; });
    pourTails(s);
  }
  function pourPop(b, at, i) {   // 띠용: 0 → 1.12 → 0.96 → 1, 살짝 기울었다 바로
    var r0 = (i % 2 ? 1 : -1) * (5 + (i % 3) * 2);
    b.style.opacity = 0;
    MO.tw(360, at, 'linear', function (e, t) {
      var k = t < 0.45 ? lerp(0, 1.12, EZ.out(t / 0.45)) : t < 0.75 ? lerp(1.12, 0.96, EZ.inout((t - 0.45) / 0.3)) : lerp(0.96, 1, EZ.out((t - 0.75) / 0.25));
      b.style.opacity = clamp01(t * 5);
      b.style.transform = t >= 1 ? '' : 'scale(' + k.toFixed(4) + ') rotate(' + (r0 * (1 - EZ.spring(t))).toFixed(2) + 'deg)';
      b.style.filter = t >= 0.3 ? '' : 'blur(' + (5 * (1 - t / 0.3)).toFixed(2) + 'px)';
    });
  }
  FX.ePour = {
    enter: function (s, st) {
      eHudIn(s, 0);
      pourSet(s, st);
      if (st === 0 && !(V3DIR < 0 || REDUCED)) eBigIn(s, 60);
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED) { eInst(function () { FX.ePour.enter(s, st); }); return; }
      // 큰 글자 → 머리글 자리로 줄어들기 (FLIP · 260ms · 움직이는 동안만 흐림)
      pourSet(s, 0);
      var big = q(s, '.e-big'), eh = q(big, '.e-h'), ek = q(big, '.e-k'), hd = q(s, ':scope > .hd'), h2 = q(hd, 'h2'), k = q(hd, '.kicker');
      var a = eoff(eh, s), b = eoff(h2, s), sc = h2.offsetWidth / eh.offsetWidth;
      var dx = (b.x + h2.offsetWidth / 2) - (a.x + eh.offsetWidth / 2), dy = (b.y + h2.offsetHeight / 2) - (a.y + eh.offsetHeight / 2);
      eDot(s).style.opacity = 0;
      eh.style.transformOrigin = '50% 50%';
      MO.tw(ET.out, 0, 'out', function (e) { ek.style.opacity = 1 - e; });
      MO.tw(280, 0, 'inout', function (e, t) {
        eh.style.transform = 'translate(' + (dx * e).toFixed(1) + 'px,' + (dy * e).toFixed(1) + 'px) scale(' + lerp(1, sc, e).toFixed(4) + ')';
        eh.style.filter = t >= 1 ? '' : 'blur(' + (4 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      }, function () { eh.style.transform = ''; eh.style.filter = ''; big.style.visibility = 'hidden'; s.classList.remove('e-0'); show(k, false); MO.tw(200, 0, 'out', function (e) { k.style.opacity = e; }); });
      var bs = qa(s, '.e-bubs .nt');
      bs.forEach(function (bb) { bb.style.opacity = 0; });
      bs.forEach(function (bb, i) { pourPop(bb, 360 + i * 220, i); });
    }
  };

  /* ============ 14 김치볶음밥 그림책 (3D 로봇 그대로): 위 알약 = 장면 1~4 · 왼쪽 위 = 장면 이름 · 왼쪽 카드 = 선생님의 부탁(쳐짐) · 오른쪽 = 로봇 말풍선(띠용) ============ */
  var STORY_SCN = ['장면 1 · 그냥 AI: 맨손으로 시작', '장면 2 · 레시피 받음', '장면 3 · 도구 · 재료 받음', '장면 4 · 하네스 완성'];
  var STORY_SUB = ['요리사 = ChatGPT · Gemini · Claude 같은 AI', '같은 AI에 레시피 · 도구를 챙겨 주면'];
  function storyGroup(st) { return st <= 3 ? 1 : st === 4 ? 2 : st === 5 ? 3 : 4; }
  function storySet(s, st) {
    var g = storyGroup(st);
    qa(s, '.e-pills4 .e-sg').forEach(function (e, i) { var f = q(e, 'i'); e.classList.toggle('e-cur', i === g - 1); e.classList.toggle('e-done', i < g); f.style.transform = i < g ? 'scaleX(1)' : 'scaleX(0)'; });
    var sc = q(s, '.e-scn'), b = q(sc, 'b'); b.textContent = STORY_SCN[g - 1]; q(sc, 'small').textContent = STORY_SUB[g > 1 ? 1 : 0]; show(sc, true); sc.__g = g;
    qa(s, '.e-rb').forEach(function (e) { show(e, +e.getAttribute('data-c') === st); e.style.filter = ''; });
    qa(s, '.ub').forEach(function (u) { if (u.__full) u.textContent = u.__full; });
  }
  function storyPlay(s, st, first) {
    var g = storyGroup(st), sc = q(s, '.e-scn');
    if (first || sc.__g !== g) {   // 장면이 바뀔 때만: 알약 채우기 · 이름 바꾸기
      var f = q(s, '.e-pills4 .e-sg:nth-child(' + g + ') i');
      if (f && !REDUCED) MO.tw(ET.inn + 60, 80, 'snap', function (e) { f.style.transform = 'scaleX(' + e.toFixed(4) + ')'; });
      if (!first) eIn(sc, 60, { dx: -24, dy: 0, blur: 6 });
    }
    var u = q(s, '.ub[data-c="' + st + '"]');   // 선생님의 부탁: 카드가 튀어나오고 글자가 쳐져요
    if (u) { MO.type(u, +u.getAttribute('data-at') || 0); if (!REDUCED) u.style.opacity = 0; }
    var rb = q(s, '.e-rb[data-c="' + st + '"]');
    if (rb) { rb.style.opacity = 0; pourPop(rb, +rb.getAttribute('data-at') || 0, st); }
  }
  FX.eStory = {
    enter: function (s, st) {
      eHudIn(s, 0);
      FX.v3story.enter(s, st);
      storySet(s, st);
      if (V3DIR < 0 || st > 0 || REDUCED) return;
      qa(s, '.e-rb').forEach(function (e) { show(e, false); });
      storyPlay(s, st, true);
    },
    step: function (s, st, dir) {
      FX.v3story.step(s, st, dir);
      if (dir === -1 || REDUCED) { storySet(s, st); return; }
      var prevG = q(s, '.e-scn').__g;
      storySet(s, st - 1);
      qa(s, '.e-rb').forEach(function (e) { show(e, false); });
      var sc = q(s, '.e-scn'); sc.__g = prevG;
      var g = storyGroup(st);
      if (g !== prevG) { q(sc, 'b').textContent = STORY_SCN[g - 1]; q(sc, 'small').textContent = STORY_SUB[g > 1 ? 1 : 0]; qa(s, '.e-pills4 .e-sg').forEach(function (e, i) { e.classList.toggle('e-cur', i === g - 1); e.classList.toggle('e-done', i < g); }); }
      storyPlay(s, st, false);
      sc.__g = g;
    }
  };


  /* ============ v4 순서: 구간 이름 · 위 줄 코드 (이 덱만) ============ */
  AGENDA = ['여는 말', '하네스', '어떻게 달라지나', '진짜 비교', '쓰는 법', '실습', '마무리'];
  SECT = ['INTRO', 'HARNESS', 'HOW', 'PROOF', 'USE', 'HANDS-ON', 'WRAP-UP'];

  /* ============ 19 모둠 미션 (v4): 판은 처음부터 · 클릭 1~4에 지금 단계 표시 (칸은 마우스로도) ============ */
  FX.eMission = {
    mark: function (s, st, anim) {
      var cur = st - 1;
      qa(s, '.seg').forEach(function (g, i) { g.classList.toggle('cur', i === cur); g.classList.toggle('done', i < cur); });
      if (anim && cur >= 0) MO.stamp(qa(s, '.seg')[cur], 0, { s: 1.12 });
    },
    enter: function (s, st) {
      eHudIn(s, 0);
      qa(s, '.seg').forEach(function (g, i) { g.onclick = function (e) { e.stopPropagation(); go(slides.indexOf(s), i + 1, 1); }; });
      var inst = V3DIR < 0 || st > 0 || REDUCED;
      v3hd(s, 60, inst);
      var parts = qa(s, '.e-warn, .board .order, .board .seg, .board .mc, .board .timer, .board .wait');
      parts.forEach(function (e) { show(e, true); e.style.filter = ''; });
      FX.eMission.mark(s, st, false);
      if (inst) return;
      parts.forEach(function (e, i) { e.style.opacity = 0; eIn(e, 200 + i * 45, { dy: 18, blur: 6 }); });
    },
    step: function (s, st, dir) { MO.stop(); FX.eMission.mark(s, st, dir !== -1 && !REDUCED); }
  };

  /* ============ 3 진입장벽 → 옛날 이야기 (v5b: 3 · 4장 합침): 클릭 1~4는 v3wall 그대로, 클릭 5에 벽이 흐려지며 내려앉고 「옛날 이야기」 카드 ============ */
  function wallOld(s, on) {
    var o = q(s, '.e-old'), w = q(s, '.wall3');
    show(o, on); o.style.filter = ''; qa(o, 'p').forEach(function (p) { show(p, on); p.style.filter = ''; });
    w.style.opacity = on ? 0.18 : ''; w.style.filter = on ? 'blur(3px)' : ''; w.style.transform = '';
  }
  FX.eWall = {
    enter: function (s, st) { eHudIn(s, 0); FX.v3wall.enter(s, Math.min(st, 4)); wallOld(s, st >= 5); },
    step: function (s, st, dir) {
      if (st <= 4) { FX.v3wall.step(s, st, dir); wallOld(s, false); return; }
      MO.stop(); v3hd(s, 0, true); FX.v3wall.set(s, 4);
      if (dir === -1 || REDUCED) { wallOld(s, true); return; }
      var w = q(s, '.wall3'), o = q(s, '.e-old'), ps = qa(o, 'p');
      MO.shake(w, 0, 9);
      MO.tw(260, 200, 'fall', function (e) { w.style.opacity = lerp(1, 0.18, e).toFixed(3); w.style.filter = 'blur(' + (3 * e).toFixed(2) + 'px)'; w.style.transform = 'translateY(' + (30 * e).toFixed(1) + 'px)'; }, function () { w.style.transform = ''; });
      show(o, true); ps.forEach(function (p) { p.style.opacity = 0; });
      eIn(ps[0], 380, { dy: 30, blur: 10, dur: 240 }); eIn(ps[1], 560, { dy: 16 });
    }
  };
