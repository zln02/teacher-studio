
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

  /* ============ 1 표지: 점 → 선 → 큰 제목(가운데) · 클릭 1에 제목이 제자리로(FLIP) + 3D 카드 ============ */
  function coverFlip(s) { var h1 = q(s, 'h1'), o = eoff(h1, s), w = h1.offsetWidth, hh = h1.offsetHeight, K = 1.62; return { dx: 960 - (o.x + w / 2), dy: 500 - (o.y + hh / 2), k: K, w: w, h: hh }; }
  function coverPrep(s) { if (q(s, '.e-line')) return; emk('i', 'e-line', '', s); eDot(s); var h1 = q(s, 'h1'); MO.split(h1); h1.style.width = 'fit-content'; }
  function coverSet(s) {
    var h1 = q(s, 'h1'), gl = q(s, '.gl'); h1.style.transform = ''; h1.style.filter = ''; eDropSet(h1, true); eBgOff(gl);
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
      var inst = V3DIR < 0 || REDUCED, h1 = q(s, 'h1'), F = coverFlip(s), d = eDot(s), ln = q(s, '.e-line'), gl = q(s, '.gl');
      h1.style.transformOrigin = '50% 50%';
      h1.style.transform = 'translate(' + F.dx.toFixed(1) + 'px,' + F.dy.toFixed(1) + 'px) scale(' + F.k + ')';
      var base = 500 + F.h * F.k / 2 + 26, half = F.w * F.k / 2;
      ln.style.left = (960 - half) + 'px'; ln.style.width = (2 * half) + 'px'; ln.style.top = base + 'px';
      d.style.left = '947px'; d.style.top = (base - 12) + 'px';
      gl.classList.add('e-bg');
      if (inst) { eDropSet(h1, true); ln.style.opacity = 1; ln.style.transform = ''; d.style.opacity = 0; gl.style.transform = ''; return; }
      eDropSet(h1, false); ln.style.opacity = 0;
      MO.tw(ET.inn, 80, 'snap', function (e) { d.style.opacity = 1; d.style.transform = 'scale(' + (e < 1 ? EZ.bounce(e) : 1).toFixed(3) + ')'; });
      MO.tw(240, 300, 'snap', function (e) { ln.style.opacity = 1; ln.style.transform = 'scaleX(' + Math.max(0.012, e).toFixed(4) + ')'; d.style.opacity = 1 - e; });
      eDrop(h1, 420);
      eDrift(gl, 0);
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED) { eInst(function () { FX.eCover.enter(s, st); }); return; }
      var h1 = q(s, 'h1'), F = coverFlip(s), ln = q(s, '.e-line'), gl = q(s, '.gl'), rule = q(s, '.m-rule'), tag = q(s, '.tag'), who = q(s, '.who'), kk = q(s, ':scope > .hd .kicker');
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
      eBgLift(gl);
      if (GL.active && GL.sceneEl === s) GL.active.age = 0;
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
  function kitPens(s) {
    var G = kitGeo(s), svg = ePen(G.K), T = qa(G.K, '.e-tool'), t7 = T[6], t8 = T[7], a = eoff(t7, s), b = eoff(t8, s);
    var ring = eStroke(svg, eLoop(G.cx, G.cy - 10, G.w / 2 + 64, G.h / 2 + 4, 41), 'acc', 'ring');
    var ny = G.y + G.h + 52, n = eNoteAt(G.K, 'part', '식당마다 달라요', 'red', G.cx - 128, ny);   // 고리 아래로 비켜서
    var ay = a.y + 64, by = b.y + 64;
    var ar = eStroke(svg, eWob([[G.cx - 140, ny + 26], [G.cx - 220, ny + 22], [a.x + t7.offsetWidth + 20, ay]], 5, 3) + ' ' + eHead(a.x + t7.offsetWidth + 20, ay, Math.PI + 0.25, 18) + ' ' +
      eWob([[G.cx + 140, ny + 26], [G.cx + 220, ny + 22], [b.x - 20, by]], 5, 5) + ' ' + eHead(b.x - 20, by, -0.25, 18), 'red', 'partar');
    return { ring: ring, n: n, ar: ar };
  }
  function kitSet(s, g) {
    var G = kitGeo(s), K = G.K, L = kitLines(s), P = kitPens(s);
    show(q(K, '.e-kp'), true); show(G.ch, true); G.ch.style.filter = '';
    qa(K, '.e-tool').forEach(function (t, i) {
      var on = +t.getAttribute('data-g') <= g; show(t, on); t.style.filter = '';
      L[i].style.strokeDashoffset = on ? 0 : 1; L[i].style.opacity = on ? 1 : 0;
      var cy = q(t, '.e-cy'); if (cy) { cy.textContent = cy.getAttribute('data-names').split('|').join(' · '); cy.style.transform = ''; cy.style.opacity = 1; }
      var ch = q(t, '.e-chip:not(.e-cy)'); if (ch) { ch.style.opacity = 1; ch.style.transform = ''; }
    });
    q(K, '.e-kcap').style.display = g >= 5 ? 'none' : '';
    qa(K, '.e-kcap p').forEach(function (p) { show(p, +p.getAttribute('data-c') === g); });
    P.ring.style.strokeDashoffset = g >= 5 ? 0 : 1;
    P.n.style.visibility = g >= 4 ? 'visible' : 'hidden'; P.n.style.clipPath = ''; P.n.style.opacity = 1;
    P.ar.style.strokeDashoffset = g >= 4 ? 0 : 1;
    var pu = q(s, '.hxpunch'); show(pu, g >= 5); show(q(pu, '.p1'), true); show(q(pu, '.p2'), true); MO.kinSet(q(pu, '.m-kin'), g >= 5);
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
      var old = q(K, '.e-kcap p[data-c="' + (g - 1) + '"]');
      if (old) MO.tw(ET.out, 0, 'out', function (e) { old.style.opacity = 1 - e; old.style.transform = 'translateY(' + (-20 * e).toFixed(1) + 'px)'; if (e >= 1) { old.style.opacity = 0; old.style.transform = ''; } });
      if (g <= 4) {
        var nu = q(K, '.e-kcap p[data-c="' + g + '"]');
        tl.forEach(function (t, i) {
          if (+t.getAttribute('data-g') !== g) return;
          var o = eoff(t, s), dx = G.cx - (o.x + t.offsetWidth / 2), dy = G.cy - (o.y + 60), j = i % 2;
          t.style.opacity = 0;
          eIn(t, 40 + j * 70, { dx: dx * 0.3, dy: dy * 0.3, s: 0.9, blur: 10, dur: 230 });
          if (!t.classList.contains('e-part')) { L[i].style.opacity = 1; L[i].style.strokeDashoffset = 1; MO.draw(L[i], 20 + j * 70, 200, 'snap'); }
          else { L[i].style.opacity = 0; (function (p) { MO.tw(200, 60 + j * 70, 'out', function (e) { p.style.opacity = e; }); })(L[i]); }
          var chip = q(t, '.e-chip');
          if (chip && !chip.classList.contains('e-cy')) { chip.style.opacity = 0; MO.stamp(chip, 330 + j * 70, { s: 1.5 }); }
          if (chip && chip.classList.contains('e-cy')) {   // 이름이 한 번 돌아가며 바뀌고(한 이름 0.3초) → 세 이름이 한 줄로 멈춰요
            var names = chip.getAttribute('data-names').split('|'), at0 = 320 + j * 140;
            chip.style.opacity = 0;
            names.forEach(function (nm, ni) { MO.tw(150, at0 + ni * 300, 'snap', function (e) { chip.textContent = nm; chip.style.opacity = 1; chip.style.transform = e >= 1 ? '' : 'perspective(400px) rotateX(' + (80 * (1 - e)).toFixed(1) + 'deg)'; }); });
            MO.tw(180, at0 + names.length * 300, 'snap', function (e) { chip.textContent = names.join(' · '); chip.style.transform = e >= 1 ? '' : 'perspective(400px) rotateX(' + (80 * (1 - e)).toFixed(1) + 'deg)'; });
          }
        });
        if (nu) eIn(nu, 200, { dy: 20 });
        if (g === 4) { var P = kitPens(s); P.ar.style.strokeDashoffset = 1; P.n.style.visibility = 'hidden'; eWrite(P.n, 380, 280); eDraw(P.ar, 520, 260); }
        return;
      }
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
    var n = eNoteAt(s, 'gap', '출발점이 이만큼 달라요', 'red', nx, ny, 'r');
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
  function flEv(s, on) { qa(s, '.e-ev .e-w').forEach(function (w) { w.classList.toggle('e-lit', on); }); }
  function flBase(s) { var b = q(s, ':scope > .e-base'); if (!b) b = emk('i', 'e-base', '', s); return b; }
  function flSet(s, st) {
    s.classList.toggle('e-0', st === 0);
    eInst(function () { FX.v3gen.enter(s, Math.max(0, st - 1)); });
    var lv = q(s, '.levels'), ev = q(s, '.e-ev'), base = flBase(s), R = flGeo(s);
    base.style.left = R.lx + 'px'; base.style.top = R.floor + 'px'; base.style.width = (R.hx + R.hw - R.lx) + 'px'; base.style.transform = '';
    q(s, '.lv.lo .bar').style.transform = '';
    flPills(s, st); flPens(s); ePenSet(s, st >= 2);
    ev.style.visibility = st >= 3 ? 'visible' : 'hidden'; show(ev, true); flEv(s, st >= 3);
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
        var cap = q(s, '.capline'), ev = q(s, '.e-ev'), W = qa(ev, '.e-w');
        eIn(cap, 0, { dy: 30, blur: 8 });
        ev.style.visibility = 'visible'; flEv(s, false);
        eIn(ev, 120, { dy: 10, blur: 3 });
        W.forEach(function (w, i) { MO.tw(1, 320 + i * 70, 'linear', function () {}, function () { w.classList.add('e-lit'); }); });
      }
    }
  };

  /* 3D 「같이 쓰려고 준비했어요」 카드: 따뜻한 호박색 대신 표지와 같은 석판 + 주황 (이 덱만) */
  setTimeout(function () {
    if (typeof SCENES === 'undefined' || !SCENES.made) return;
    var made0 = SCENES.made;
    SCENES.made = function (a) { var keep = P.amber, S; P.amber = P.dacc; try { S = made0(a); } finally { P.amber = keep; } S.noBg = true; S.scene.background = new THREE.Color(0x161a20); return S; };   // 바탕도 표지처럼 평평한 석판
  }, 0);

  /* 처음 한 번: 모든 장에 HUD 틀 · 로봇 요리사 그림 조각 넣기 */
  slides.forEach(function (s) { eHud(s); });
  setTimeout(function () { slides.forEach(function (s) {   // PUPPET은 deck.js 뒤쪽에서 채워져요 → 한 박자 뒤에
    [].forEach.call(s.querySelectorAll('img[data-puppet]'), function (im) { var k = im.getAttribute('data-puppet'); if (PUPPET[k]) im.src = PUPPET[k]; });
    [].forEach.call(s.querySelectorAll('[data-puppet-bg]'), function (e) { var k = e.getAttribute('data-puppet-bg'); e.style.backgroundImage = 'linear-gradient(var(--e-kshade),var(--e-kshade))' + (PUPPET[k] ? ',url(' + PUPPET[k] + ')' : ''); });
  }); }, 0);
