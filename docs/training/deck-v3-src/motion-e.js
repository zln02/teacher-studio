
  /* =====================================================================
     deck-e 샘플 층 (build.py --skin e 일 때만 motion2.js 뒤에 붙어요 · 본 덱 deck-v3.html에는 안 들어가요)
     1 · 7 · 14장만 바꿔요. 장 파일(slides.html)은 그대로 두고, 여기서 세 장에 「큰 글자 장면」 단계를 하나 앞에 끼워요.
       큰 글자 장면  들어오면 핵심 문장 하나가 화면 가운데를 가득 (음절마다 45ms, 살짝 떨어지며 기울었다 자리) → 클릭 1에 머리글로 빠지고 내용이 와요
       빠르게 와서 오래 멈춤  들어오기 150~250ms, 움직이는 동안만 흐림(모션 블러), 닿으면 또렷 · 그다음엔 가만히
       이어받기(match cut)  주황 점 하나가 다음 모습이 돼요: 표지 = 점 → 선 → 제목 밑줄 · 7장 = 점 → 요리사 칸 · 14장 = 점 → 바닥 선
       펜 주석  손으로 그린 듯 살짝 흔들리는 선(SVG 그리기) + 짧은 손글씨풍 메모, 가리키는 것이 닿는 순간 같이 그려져요
       단계 알약 · 낱말 밝히기 · HUD 틀(모서리 · 눈금자)
     움직임 줄이기: 모두 끝 모습으로 바로. 뒤로 가기: 끝 모습으로 바로.
     ===================================================================== */
  var ET = { inn: 200, out: 150, st: 45, drift: 2600 };
  function eoff(el, s) { var x = 0, y = 0; while (el && el !== s) { x += el.offsetLeft; y += el.offsetTop; el = el.offsetParent; } return { x: x, y: y }; }
  function emk(tag, cls, html, parent) { var e = document.createElement(tag); e.className = cls; if (html) e.innerHTML = html; if (parent) parent.appendChild(e); return e; }
  // 흐림 이동: (dx,dy)에서 와서 딱 · 움직이는 동안만 흐려요
  function eIn(el, at, o) {
    o = o || {}; var dx = o.dx || 0, dy = o.dy === undefined ? 30 : o.dy, B = o.blur === undefined ? 8 : o.blur, s0 = o.s === undefined ? 1 : o.s;
    if (REDUCED) { el.style.opacity = 1; el.style.transform = ''; el.style.filter = ''; return null; }
    return MO.tw(o.dur || ET.inn, at, 'snap', function (e) {
      el.style.opacity = clamp01(e * 2.5);
      el.style.transform = e >= 1 ? '' : 'translate(' + (dx * (1 - e)).toFixed(1) + 'px,' + (dy * (1 - e)).toFixed(1) + 'px) scale(' + lerp(s0, 1, e).toFixed(4) + ')';
      el.style.filter = e >= 1 ? '' : 'blur(' + (B * (1 - e)).toFixed(2) + 'px)';
    });
  }
  // 빠른 번짐 퇴장: 위로 늘어나며 흐려져 사라져요 (150ms)
  function eOut(el, at) {
    if (REDUCED) { el.style.opacity = 0; return null; }
    return MO.tw(ET.out, at, 'fall', function (e) {
      el.style.opacity = 1 - e;
      el.style.transform = 'translateY(' + (-70 * e).toFixed(1) + 'px) scaleY(' + (1 + 0.35 * e).toFixed(3) + ')';
      el.style.filter = 'blur(' + (12 * e).toFixed(1) + 'px)';
      if (e >= 1) { el.style.visibility = 'hidden'; el.style.transform = ''; el.style.filter = ''; }
    });
  }
  // 큰 글자: 음절마다 위에서 살짝 떨어지며(기울었다) 자리 · 45ms 간격 · 떨어지는 동안만 흐림
  function eDrop(el, at) {
    var cs = MO.split(el);
    el.style.opacity = 1;
    cs.forEach(function (c, i) {
      var r = ((i * 37) % 9 - 4) * 2.2;   // 음절마다 다른 기울기 (−9° ~ +9°, 같은 값이 반복되지 않게)
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
  // 바탕 흐름: 뒤의 카드가 흐리고 옅게, 아주 천천히 흘러와 멈춰요 (멈춘 뒤엔 가만히)
  function eDrift(el, at) {
    el.classList.add('e-bg');
    if (REDUCED) { el.style.transform = ''; return; }
    MO.tw(ET.drift, at, 'out', function (e) { el.style.transform = e >= 1 ? '' : 'translate(' + (-26 * (1 - e)).toFixed(1) + 'px,' + (18 * (1 - e)).toFixed(1) + 'px) scale(' + lerp(1.04, 1, e).toFixed(4) + ')'; });
  }
  function eBgOff(el) { el.classList.remove('e-bg'); el.style.transform = ''; el.style.filter = ''; if (el.style.opacity !== '') el.style.opacity = ''; }
  // 바탕이 걷히며 또렷해져요 (220ms) · 뒤로 갈 때는 eBgOff로 바로
  function eBgLift(el, at) {
    eBgOff(el);
    if (REDUCED) return;
    MO.tw(220, at || 0, 'out', function (e) { el.style.opacity = e >= 1 ? '' : lerp(0.16, 1, e).toFixed(3); el.style.filter = e >= 1 ? '' : 'blur(' + (6 * (1 - e)).toFixed(2) + 'px)'; });
  }

  /* ---- 펜: 살짝 흔들리는 선 (씨앗 고정 → 매번 같은 모양) ---- */
  function eRand(seed) { var x = seed * 9301 + 49297; return function () { x = (x * 9301 + 49297) % 233280; return x / 233280; }; }
  function eWob(pts, amp, seed) {
    var R = eRand(seed), p = pts.map(function (q, i) { var j = (i === 0 || i === pts.length - 1) ? 0.3 : 1; return [q[0] + (R() - 0.5) * amp * j, q[1] + (R() - 0.5) * amp * j]; });
    var d = 'M' + p[0][0].toFixed(1) + ' ' + p[0][1].toFixed(1);
    for (var i = 0; i < p.length - 1; i++) {   // Catmull-Rom → 베지어
      var p0 = p[i - 1] || p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] || p2;
      d += ' C' + (p1[0] + (p2[0] - p0[0]) / 6).toFixed(1) + ' ' + (p1[1] + (p2[1] - p0[1]) / 6).toFixed(1) + ' ' + (p2[0] - (p3[0] - p1[0]) / 6).toFixed(1) + ' ' + (p2[1] - (p3[1] - p1[1]) / 6).toFixed(1) + ' ' + p2[0].toFixed(1) + ' ' + p2[1].toFixed(1);
    }
    return d;
  }
  function eLoop(cx, cy, rx, ry, seed) {   // 한 번에 휙 두른 동그라미: 시작과 끝이 살짝 겹치고 어긋나요
    var pts = [], n = 22, a0 = -2.2;
    for (var i = 0; i <= n; i++) { var a = a0 + (Math.PI * 2 + 0.5) * i / n, g = 1 + 0.05 * i / n; pts.push([cx + Math.cos(a) * rx * g, cy + Math.sin(a) * ry * g]); }
    return eWob(pts, 7, seed);
  }
  function eHead(x, y, ang, len) {   // 화살촉: 두 획
    var a1 = ang + 2.6, a2 = ang - 2.6;
    return 'M' + (x + Math.cos(a1) * len).toFixed(1) + ' ' + (y + Math.sin(a1) * len).toFixed(1) + ' L' + x.toFixed(1) + ' ' + y.toFixed(1) + ' L' + (x + Math.cos(a2) * len).toFixed(1) + ' ' + (y + Math.sin(a2) * len).toFixed(1);
  }
  function ePen(s) {
    var svg = s.querySelector('.epen');
    if (!svg) { svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'epen'); svg.setAttribute('viewBox', '0 0 1920 1080'); svg.setAttribute('aria-hidden', 'true'); s.appendChild(svg); }
    return svg;
  }
  function eStroke(svg, d, col, key) {
    var p = svg.querySelector('[data-key="' + key + '"]');
    if (!p) { p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('data-key', key); p.setAttribute('pathLength', '1'); svg.appendChild(p); }
    p.setAttribute('d', d); p.setAttribute('class', 'pn ' + col); p.style.strokeDasharray = 1;
    return p;
  }
  function eDraw(p, at, dur) { if (REDUCED) { p.style.strokeDashoffset = 0; return; } p.style.strokeDashoffset = 1; MO.tw(dur, at, 'inout', function (e) { p.style.strokeDashoffset = (1 - e).toFixed(4); }); }
  function eNoteAt(s, key, txt, col, x, y, align) {
    var n = s.querySelector('.enote[data-key="' + key + '"]');
    if (!n) { n = emk('div', 'enote ' + col, txt, s); n.setAttribute('data-key', key); }
    n.style.left = x + 'px'; n.style.top = y + 'px';
    if (align === 'r') { n.style.left = 'auto'; n.style.right = (1920 - x) + 'px'; }
    return n;
  }
  // 손글씨처럼 왼쪽부터 써져요
  function eWrite(n, at, dur) {
    n.style.visibility = 'visible';
    if (REDUCED) { n.style.clipPath = ''; n.style.opacity = 1; return; }
    MO.tw(dur || 300, at, 'out', function (e) { n.style.opacity = 1; n.style.clipPath = e >= 1 ? '' : 'inset(-20% ' + ((1 - e) * 100).toFixed(1) + '% -20% -4%)'; });
  }
  function ePenSet(s, on) {
    [].forEach.call(s.querySelectorAll('.epen path'), function (p) { p.style.strokeDashoffset = on ? 0 : 1; });
    [].forEach.call(s.querySelectorAll('.enote'), function (n) { n.style.visibility = on ? 'visible' : 'hidden'; n.style.clipPath = ''; n.style.opacity = 1; });
  }

  /* ---- HUD 틀: 네 모서리 괄호 · 아래 눈금자 · 지금 장 표시(주황 눈금) ---- */
  function eHud(s) {
    if (s.querySelector('.ehud')) return;
    var h = emk('div', 'ehud', '<i class="c tl"></i><i class="c tr"></i><i class="c bl"></i><i class="c br"></i><div class="rl"><i class="ph"></i></div>', s);
    var i = slides.indexOf(s), n = slides.length;
    h.querySelector('.ph').style.left = (100 * i / Math.max(1, n - 1)).toFixed(2) + '%';
  }
  function eHudIn(s, at) {
    var cs = [].slice.call(s.querySelectorAll('.ehud .c')), ph = q(s, '.ehud .ph');
    if (REDUCED) return;
    cs.forEach(function (c, i) { MO.tw(ET.inn, at + i * 30, 'snap', function (e) { c.style.opacity = e; c.style.transform = 'scale(' + lerp(1.6, 1, e).toFixed(3) + ')'; if (e >= 1) c.style.transform = ''; }); });
    MO.tw(ET.inn + 100, at + 60, 'snap', function (e) { ph.style.transform = e >= 1 ? '' : 'translateX(' + (-60 * (1 - e)).toFixed(1) + 'px) scaleY(' + lerp(2.2, 1, e).toFixed(3) + ')'; });
  }

  /* ---- 큰 글자 장면 부품 ---- */
  function eBig(s, kick, html) {
    var b = q(s, '.ebig');
    if (!b) { b = emk('div', 'ebig', '<div class="ek">' + kick + '</div><p class="eh">' + html + '<i class="eslot"></i></p>', s); emk('i', 'edot', '', s); }
    return b;
  }
  function eDotAtSlot(s) {   // 점을 큰 글자 끝자리(eslot)에 둬요
    var slot = q(s, '.eslot'), d = q(s, '.edot'), o = eoff(slot, s);
    d.style.left = (o.x + slot.offsetWidth / 2 - 13) + 'px'; d.style.top = (o.y + slot.offsetHeight / 2 - 13) + 'px';
    return d;
  }
  function eBigIn(s, at) {
    var b = q(s, '.ebig'), d = eDotAtSlot(s), k = q(b, '.ek'), h = q(b, '.eh');
    b.style.visibility = 'visible'; b.style.opacity = 1; b.style.transform = ''; b.style.filter = '';
    if (REDUCED) { eDropSet(h, true); show(k, true); d.style.opacity = 1; d.style.transform = ''; return; }
    eDropSet(h, false); k.style.opacity = 0; d.style.opacity = 0;
    MO.tw(ET.inn, at, 'snap', function (e) { d.style.opacity = 1; d.style.transform = 'scale(' + (e < 1 ? EZ.bounce(e) * 1 : 1).toFixed(3) + ')'; });   // 점이 먼저 톡
    eDrop(h, at + 120);
    eIn(k, at + 120 + MO.split(h).length * ET.st, { dy: 12, blur: 4 });
  }
  function eBigSet(s, on) {
    var b = q(s, '.ebig'), d = q(s, '.edot');
    b.style.visibility = on ? 'visible' : 'hidden'; b.style.opacity = 1; b.style.transform = ''; b.style.filter = '';
    eDropSet(q(b, '.eh'), on); show(q(b, '.ek'), true);
    if (on) { eDotAtSlot(s); d.style.opacity = 1; d.style.transform = ''; d.style.width = d.style.height = ''; d.style.borderRadius = ''; } else d.style.opacity = 0;
  }

  /* ---- 겉감: 기존 장 효과(inner)를 한 단계 뒤로 밀어요 ---- */
  function eInst(fn) { var keep = V3DIR; V3DIR = -1; try { fn(); } finally { V3DIR = keep; } }
  function eWrap(name, o) {
    FX[name] = {
      enter: function (s, st) {
        o.prep(s); eHud(s);
        if (st === 0) {
          s.classList.add('e0');
          o.base(s, 0);
          if (V3DIR < 0 || REDUCED) { o.e0(s, true); return; }
          eHudIn(s, 0);
          o.e0(s, false);
          return;
        }
        s.classList.remove('e0');
        o.base(s, st - 1, V3DIR < 0 ? false : true);
        o.set(s, st);
      },
      step: function (s, st, dir) {
        MO.stop();
        if (dir === -1 || REDUCED) {
          if (st === 0) { s.classList.add('e0'); o.base(s, 0); o.e0(s, true); return; }
          s.classList.remove('e0');
          o.back(s, st - 1);
          o.set(s, st);
          return;
        }
        if (st === 1) { o.dock(s); return; }
        o.set(s, st - 1);   // 지난 단계가 아직 움직이던 중이면 끝 모습으로 맞추고
        o.play(s, st);
      }
    };
  }

  /* ============ 1 표지: 점 → 선 → 큰 제목(가운데 가득) · 클릭 1에 제목이 왼쪽 자리로 쏙(FLIP) + 3D 카드 ============ */
  function coverFlip(s) {   // h1의 제자리 → 가운데 크게 놓을 때의 이동 · 배율
    var h1 = q(s, 'h1'), o = eoff(h1, s), w = h1.offsetWidth, hh = h1.offsetHeight, K = 1.62;
    var tw = MO.split(h1).length ? w : w;
    return { dx: 960 - (o.x + tw / 2), dy: 500 - (o.y + hh / 2), k: K, x: o.x, y: o.y, w: w, h: hh };
  }
  eWrap('eCover', {
    prep: function (s) {
      if (q(s, '.eline')) return;
      emk('i', 'eline', '', s); emk('i', 'edot', '', s);
      var h1 = q(s, 'h1'); MO.split(h1); h1.style.width = 'fit-content';
    },
    base: function (s) { eInst(function () { FX.v3cover.enter(s, 0); }); },
    e0: function (s, inst) {
      var h1 = q(s, 'h1'), F = coverFlip(s), d = q(s, '.edot'), ln = q(s, '.eline'), gl = q(s, '.gl');
      h1.style.transformOrigin = '50% 50%';
      h1.style.transform = 'translate(' + F.dx.toFixed(1) + 'px,' + F.dy.toFixed(1) + 'px) scale(' + F.k + ')';
      var base = 500 + F.h * F.k / 2 + 26, half = F.w * F.k / 2;   // 큰 제목 밑 선
      ln.style.left = (960 - half) + 'px'; ln.style.width = (2 * half) + 'px'; ln.style.top = base + 'px';
      d.style.left = '947px'; d.style.top = (base - 12) + 'px';
      gl.classList.add('e-bg');
      if (inst) { eDropSet(h1, true); ln.style.opacity = 1; ln.style.transform = ''; d.style.opacity = 0; gl.style.transform = ''; return; }
      // 점 톡 → 양옆으로 늘어나 선 → 음절이 떨어져 선 위에 앉아요
      eDropSet(h1, false); ln.style.opacity = 0;
      MO.tw(ET.inn, 80, 'snap', function (e) { d.style.opacity = 1; d.style.transform = 'scale(' + (e < 1 ? EZ.bounce(e) : 1).toFixed(3) + ')'; });
      MO.tw(240, 300, 'snap', function (e) { ln.style.opacity = 1; ln.style.transform = 'scaleX(' + Math.max(0.012, e).toFixed(4) + ')'; d.style.opacity = 1 - e; });
      eDrop(h1, 420);
      eDrift(gl, 0);
    },
    dock: function (s) {
      var h1 = q(s, 'h1'), F = coverFlip(s), ln = q(s, '.eline'), gl = q(s, '.gl'), rule = q(s, '.m-rule'), tag = q(s, '.tag'), who = q(s, '.who'), kk = q(s, ':scope > .hd .kicker');
      eDropSet(h1, true); ln.style.opacity = 1; ln.style.transform = ''; q(s, '.edot').style.opacity = 0;
      [rule, tag, who].forEach(function (e) { e.style.opacity = 0; });
      if (kk) kk.style.opacity = 0;
      s.classList.remove('e0');
      // 제목: 가운데 → 제자리 (220ms, 움직이는 동안만 흐림)
      MO.tw(220, 0, 'inout', function (e, t) {
        h1.style.transform = e >= 1 ? '' : 'translate(' + (F.dx * (1 - e)).toFixed(1) + 'px,' + (F.dy * (1 - e)).toFixed(1) + 'px) scale(' + lerp(F.k, 1, e).toFixed(4) + ')';
        h1.style.filter = e >= 1 ? '' : 'blur(' + (5 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      });
      // 선이 줄어들며 강조 줄(m-rule) 자리로 → 강조 줄이 돼요 (이어받기)
      var ro = eoff(rule, s), l0 = parseFloat(ln.style.left), w0 = parseFloat(ln.style.width), t0 = parseFloat(ln.style.top);
      MO.tw(240, 40, 'inout', function (e, t) {
        ln.style.left = lerp(l0, ro.x, e).toFixed(1) + 'px'; ln.style.width = lerp(w0, rule.offsetWidth, e).toFixed(1) + 'px'; ln.style.top = lerp(t0, ro.y, e).toFixed(1) + 'px';
        ln.style.filter = e >= 1 ? '' : 'blur(' + (3 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      }, function () { ln.style.opacity = 0; rule.style.opacity = 1; rule.style.transform = 'scaleX(1)'; });
      if (kk) MO.type(kk, 200);
      eIn(tag, 260, { dy: 24 }); eIn(who, 330, { dy: 24 });
      // 3D: 흐림이 걷히고 카드가 다시 통통 (장면 시계를 처음으로)
      eBgLift(gl);
      if (GL.active && GL.sceneEl === s) GL.active.age = 0;
    },
    play: function () {},
    back: function (s) { eInst(function () { FX.v3cover.enter(s, 0); }); },
    set: function (s) {
      var h1 = q(s, 'h1'), gl = q(s, '.gl'); h1.style.transform = ''; h1.style.filter = ''; eDropSet(h1, true); eBgOff(gl);
      q(s, '.eline').style.opacity = 0; q(s, '.edot').style.opacity = 0;
      [q(s, '.m-rule'), q(s, '.tag'), q(s, '.who')].forEach(function (e) { show(e, true); e.style.filter = ''; });
      q(s, '.m-rule').style.transform = 'scaleX(1)';
    }
  });

  /* ============ 7 비유 지도: 큰 글자 「오늘은 AI를 식당으로」 → 점이 요리사 칸이 돼요 → 클릭 2 뒤집기 + 펜 주석 ============ */
  function mapGeo(s) {
    var am = q(s, '.amap'), ao = eoff(am, s), fc = qa(s, '.amap .fc').map(function (c) { return { x: ao.x + c.offsetLeft, y: ao.y + c.offsetTop, w: c.offsetWidth, h: c.offsetHeight }; });
    return { hub: fc[0], tl: fc[1], tr: fc[2], br: fc[3], bl: fc[4] };
  }
  function mapPens(s) {
    var G = mapGeo(s), svg = ePen(s), H = G.hub, cx = H.x + H.w / 2, cy = H.y + H.h / 2;
    var a = eStroke(svg, eLoop(cx, cy, H.w / 2 + 40, H.h / 2 + 30, 7), 'red', 'hub');
    var ny = H.y - 112;   // 요리사 칸 위 메모 + 짧은 화살표
    var na = eNoteAt(s, 'hub', 'AI = 요리사!', 'red', cx + 40, ny);
    var a2 = eStroke(svg, eWob([[cx + 30, ny + 52], [cx + 8, ny + 74], [cx - 6, H.y - 34]], 4, 3) + ' ' + eHead(cx - 6, H.y - 34, Math.PI / 2 + 0.35, 18), 'red', 'hubar');
    var B = G.br, bx = B.x - 14, by = B.y + B.h - 46;   // 하네스 칸 왼쪽 아래로 휘어 들어가는 파란 화살표
    var nx = H.x + 10, nyy = H.y + H.h + 86;
    var nb = eNoteAt(s, 'har', '오늘 우리가 끼울 것', 'blue', nx, nyy);
    var b = eStroke(svg, eWob([[nx + 350, nyy + 30], [nx + 410, nyy + 40], [bx - 70, by + 30], [bx, by]], 5, 11) + ' ' + eHead(bx, by, -0.42, 20), 'blue', 'har');
    return { a: a, a2: a2, na: na, b: b, nb: nb };
  }
  eWrap('eMap', {
    prep: function (s) {
      eBig(s, '// 오늘의 비유 지도', '오늘은 AI를<br><em>식당</em>으로');
    },
    base: function (s, st, anim) {
      if (st >= 2) { s.classList.remove('map'); if (anim) FX.v3hx.enter(s, st - 2); else eInst(function () { FX.v3hx.enter(s, st - 2); }); return; }
      eInst(function () { FX.v3map.enter(s, st); });
    },
    e0: function (s, inst) {
      var am = q(s, '.amap');
      ePen(s); mapPens(s); ePenSet(s, false);
      qa(s, '.amap .fi').forEach(function (f) { f.style.transform = ''; });
      eBigSet(s, true);
      am.classList.add('e-bg');
      if (inst) { am.style.transform = ''; return; }
      eBigIn(s, 60);
      eDrift(am, 0);
    },
    dock: function (s) {
      var big = q(s, '.ebig'), d = q(s, '.edot'), am = q(s, '.amap'), hm = q(s, '.hd.hm'), G = mapGeo(s), H = G.hub;
      s.classList.remove('e0');
      eInst(function () { FX.v3map.enter(s, 0); });
      eBgLift(am);
      eOut(big, 0);
      // 머리글: 가림막 대신 빠른 흐림 들어오기
      var h2 = q(hm, 'h2'), kk = q(hm, '.kicker');
      MO.wipeSet(h2, true); eIn(h2, 90, { dy: 40, blur: 10 }); eIn(kk, 60, { dy: 20 });
      // 점이 요리사 칸 가운데로 날아가(흐림 꼬리) → 퍼져서 칸이 돼요
      var x0 = parseFloat(d.style.left), y0 = parseFloat(d.style.top), x1 = H.x + H.w / 2 - 13, y1 = H.y + H.h / 2 - 13;
      var cards = qa(s, '.amap .fc'); cards.forEach(function (c) { c.style.opacity = 0; });
      if (REDUCED) { d.style.opacity = 0; cards.forEach(function (c) { show(c, true); }); return; }
      MO.tw(220, 40, 'inout', function (e, t) {
        d.style.opacity = 1;
        d.style.left = lerp(x0, x1, e).toFixed(1) + 'px'; d.style.top = (lerp(y0, y1, e) - 90 * Math.sin(Math.PI * e)).toFixed(1) + 'px';
        d.style.transform = 'scale(' + (1 + 0.6 * Math.sin(Math.PI * t)).toFixed(3) + ',' + (1 - 0.25 * Math.sin(Math.PI * t)).toFixed(3) + ')';
        d.style.filter = 'blur(' + (3 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      }, function () { d.style.filter = ''; d.style.transform = ''; });
      MO.tw(200, 260, 'snap', function (e) {   // 점 → 칸 (둥근 점이 칸 크기로 퍼져요)
        d.style.left = lerp(x1, H.x, e).toFixed(1) + 'px'; d.style.top = lerp(y1, H.y, e).toFixed(1) + 'px';
        d.style.width = lerp(26, H.w, e).toFixed(1) + 'px'; d.style.height = lerp(26, H.h, e).toFixed(1) + 'px'; d.style.borderRadius = lerp(13, 10, e).toFixed(1) + 'px';
        d.style.opacity = 1 - clamp01((e - 0.6) / 0.4);
      }, function () { d.style.opacity = 0; d.style.width = d.style.height = d.style.borderRadius = ''; });
      eIn(cards[0], 330, { dy: 0, s: 0.9, blur: 6 });
      // 네 모서리 칸은 요리사에게서 바깥으로 튀어나가 자리 (이어받기)
      var hc = { x: H.x + H.w / 2, y: H.y + H.h / 2 };
      cards.slice(1).forEach(function (c, i) {
        var g = [G.tl, G.tr, G.br, G.bl][i], dx = hc.x - (g.x + g.w / 2), dy = hc.y - (g.y + g.h / 2);
        eIn(c, 420 + i * ET.st, { dx: dx * 0.35, dy: dy * 0.35, s: 0.92, blur: 10 });
      });
    },
    play: function (s, st) {
      if (st === 2) {   // 뒤집기(빠르게) → 선 → 펜 주석이 닿는 순간 같이 그려져요
        eInst(function () { FX.v3map.mapSet(s, 0); });
        var fi = qa(s, '.amap .fi'), P = mapPens(s);
        ePenSet(s, false);
        fi.forEach(function (f, i) { MO.flip(f, i * 70, 300); });
        qa(s, '.amap .alines path').forEach(function (p, i) { p.style.strokeDashoffset = 1; MO.draw(p, 260 + i * 50, 220, 'snap'); });
        eDraw(P.a, 300, 300); eWrite(P.na, 520, 260); eDraw(P.a2, 640, 160);
        eDraw(P.b, 560, 320); eWrite(P.nb, 520, 320);
        return;
      }
      if (st === 3 && !REDUCED) { [ePen(s)].concat(qa(s, '.enote')).forEach(function (e) { MO.tw(ET.out, 0, 'out', function (k) { e.style.opacity = 1 - k; }); }); }
      FX.v3map.step(s, st - 1, 1);
    },
    back: function (s, st) { if (st >= 2) { s.classList.remove('map'); FX.v3hx.step(s, st - 2, -1); } else { s.classList.add('map'); FX.v3map.mapSet(s, st); } },
    set: function (s, st) {
      eBigSet(s, false); eBgOff(q(s, '.amap')); ePen(s).style.opacity = '';
      if (st >= 3) ePenSet(s, false);
      if (st <= 2) { mapPens(s); ePenSet(s, st === 2); qa(s, '.amap .fc').forEach(function (c) { show(c, true); c.style.filter = ''; }); var hm = q(s, '.hd.hm'); [q(hm, 'h2'), q(hm, '.kicker')].forEach(function (e) { show(e, true); e.style.filter = ''; }); }
    }
  });

  /* ============ 14 바닥: 큰 글자 → 점이 떨어져 바닥 선 → 막대 · 클릭 2 하네스 막대 + 펜 · 클릭 3 결론 + 근거 낱말 밝히기 ============ */
  var FL_PILLS = ['그냥 AI', '하네스 AI', '바닥이 올라가요'];
  function flGeo(s) {
    var lo = q(s, '.lv.lo .bar'), hi = q(s, '.lv.hi .bar'), keep = hi.style.height;
    hi.style.height = '';
    var a = eoff(lo, s), b = eoff(hi, s), r = { lx: a.x, ly: a.y, lw: lo.offsetWidth, lh: lo.offsetHeight, hx: b.x, hy: b.y, hw: hi.offsetWidth, hh: hi.offsetHeight };
    hi.style.height = keep;
    r.floor = r.ly + r.lh;   // 바닥 선 (두 막대 아래)
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
    var P = qa(s, '.epills .sg');
    P.forEach(function (g, i) {
      var f = q(g, 'i'), on = i < st, cur = i === st - 1;
      g.classList.toggle('cur', cur); g.classList.toggle('done', on);
      if (anim && cur && !REDUCED) MO.tw(ET.inn + 60, 80, 'snap', function (e) { f.style.transform = 'scaleX(' + e.toFixed(4) + ')'; });
      else f.style.transform = on ? 'scaleX(1)' : 'scaleX(0)';
    });
  }
  function flEv(s, on) { qa(s, '.eev .w').forEach(function (w) { w.classList.toggle('lit', on); w.style.filter = ''; }); }
  eWrap('eFloor', {
    prep: function (s) {
      if (q(s, '.ebig')) return;
      eBig(s, '// 그래서 오늘부터', '바닥이<br><em>셰프 레시피</em>에서<br>시작해요');
      emk('i', 'ebase', '', s);
      emk('div', 'epills', FL_PILLS.map(function (t, i) { return '<span class="sg"><i></i><b>' + (i + 1) + ' · ' + t + '</b></span>'; }).join(''), s);
      // 근거 줄: 아래 쪽 줄에서 본문으로 올려 낱말마다 밝혀요 (글자는 그대로)
      var src = s.getAttribute('data-src') || '';
      s.removeAttribute('data-src');
      emk('p', 'eev', src.split(/(\s+)/).map(function (w) { return /^\s+$/.test(w) ? w : '<span class="w' + (/\d/.test(w) ? ' n' : '') + '">' + w + '</span>'; }).join(''), s);
    },
    base: function (s, st, anim) {
      if (anim && st === 0) { FX.v3gen.enter(s, 0); return; }
      eInst(function () { FX.v3gen.enter(s, st); });
    },
    e0: function (s, inst) {
      var lv = q(s, '.levels'), ev = q(s, '.eev');
      flPens(s); ePenSet(s, false); flPills(s, 0); flEv(s, false); ev.style.visibility = 'hidden';
      q(s, '.ebase').style.opacity = 0;
      eBigSet(s, true);
      lv.classList.add('e-bg');
      if (inst) { lv.style.transform = ''; return; }
      eBigIn(s, 60);
      eDrift(lv, 0);
    },
    dock: function (s) {
      var big = q(s, '.ebig'), d = q(s, '.edot'), lv = q(s, '.levels'), R = flGeo(s), base = q(s, '.ebase');
      s.classList.remove('e0');
      eInst(function () { FX.v3gen.enter(s, 0); });
      eBgLift(lv);
      eOut(big, 0);
      var hd = q(s, ':scope > .hd'), h2 = q(hd, 'h2'), kk = q(hd, '.kicker');
      eIn(h2, 90, { dy: 40, blur: 10 }); eIn(kk, 60, { dy: 20 });
      flPills(s, 1, true); eIn(q(s, '.epills'), 120, { dy: 8, blur: 4 });
      var lo = q(s, '.lv.lo'), bar = q(lo, '.bar'), lb = q(lo, '.lb'), ft = q(lo, '.ft');
      var L = R.lx, Rr = R.hx + R.hw, Y = R.floor;
      base.style.left = L + 'px'; base.style.top = Y + 'px'; base.style.width = (Rr - L) + 'px';
      if (REDUCED) { d.style.opacity = 0; base.style.opacity = 1; base.style.transform = ''; return; }
      [lb, ft].forEach(function (e) { e.style.opacity = 0; });
      bar.style.transformOrigin = '50% 100%'; bar.style.transform = 'scaleY(0)';
      // 점이 떨어져(늘어나며) 바닥 왼쪽 끝에 탁 → 선으로 쭉 (= 바닥)
      var x0 = parseFloat(d.style.left), y0 = parseFloat(d.style.top);
      MO.tw(220, 40, 'fall', function (e, t) {
        d.style.opacity = 1; d.style.left = lerp(x0, L - 13, e).toFixed(1) + 'px'; d.style.top = lerp(y0, Y - 13, e).toFixed(1) + 'px';
        d.style.transform = 'scale(' + (1 - 0.3 * e).toFixed(3) + ',' + (1 + 0.8 * Math.sin(Math.PI * t)).toFixed(3) + ')'; d.style.filter = 'blur(' + (2.5 * Math.sin(Math.PI * t)).toFixed(2) + 'px)';
      }, function () { d.style.filter = ''; });
      MO.tw(230, 270, 'snap', function (e) {
        base.style.opacity = 1; base.style.transform = 'scaleX(' + Math.max(0.01, e).toFixed(4) + ')';
        d.style.left = lerp(L - 13, Rr - 13, e).toFixed(1) + 'px'; d.style.transform = 'scale(' + lerp(0.7, 0.3, e).toFixed(3) + ')'; d.style.opacity = 1 - e;
      });
      MO.tw(200, 380, 'snap', function (e) { bar.style.transform = e >= 1 ? '' : 'scaleY(' + e.toFixed(4) + ')'; });
      eIn(lb, 440, { dy: 20 }); eIn(ft, 480, { dy: 14 });
    },
    play: function (s, st) {
      FX.v3gen.set(s, st - 2); v3hd(s, 0, true);
      flPills(s, st, true);
      if (st === 2) {   // 하네스 막대가 아래에서 솟아 딱(흐림 꼬리) → 닿는 순간 빨간 펜 화살표 · 메모
        var hi = q(s, '.lv.hi'), bar = q(hi, '.bar'), H = flGeo(s).hh, P = flPens(s);
        ePenSet(s, false);
        hi.style.opacity = 1; [q(hi, '.lb'), q(hi, '.ft')].forEach(function (e) { e.style.opacity = 0; });
        MO.tw(240, 0, 'snap', function (e) { bar.style.height = lerp(0, H, e).toFixed(1) + 'px'; bar.style.filter = e >= 1 ? '' : 'blur(' + (4 * (1 - e)).toFixed(2) + 'px)'; if (e >= 1) bar.style.height = ''; });
        eIn(q(hi, '.lb'), 160, { dy: 24 }); eIn(q(hi, '.ft'), 220, { dy: 14 });
        eDraw(P.p, 230, 260); eWrite(P.n, 330, 300); eDraw(P.l, 520, 160);
      } else if (st === 3) {   // 결론 탁 → 근거 줄이 흐리게 놓이고 낱말이 차례로 밝아져요
        var cap = q(s, '.capline'), ev = q(s, '.eev'), W = qa(ev, '.w');
        eIn(cap, 0, { dy: 30, blur: 8 });
        ev.style.visibility = 'visible'; flEv(s, false);
        eIn(ev, 120, { dy: 10, blur: 3 });
        W.forEach(function (w, i) { MO.tw(1, 320 + i * 70, 'linear', function () {}, function () { w.classList.add('lit'); }); });
      }
    },
    back: function (s, st) { FX.v3gen.step(s, st, -1); },
    set: function (s, st) {
      eBigSet(s, false); eBgOff(q(s, '.levels')); show(q(s, '.epills'), true); q(s, '.epills').style.filter = '';
      var R = flGeo(s), base = q(s, '.ebase');
      base.style.left = R.lx + 'px'; base.style.top = R.floor + 'px'; base.style.width = (R.hx + R.hw - R.lx) + 'px'; base.style.opacity = 1; base.style.transform = '';
      q(s, '.lv.lo .bar').style.transform = '';
      flPills(s, st);
      flPens(s); ePenSet(s, st >= 2);
      q(s, '.eev').style.visibility = st >= 3 ? 'visible' : 'hidden'; flEv(s, st >= 3); show(q(s, '.eev'), true);
      var hd = q(s, ':scope > .hd'); [q(hd, 'h2'), q(hd, '.kicker')].forEach(function (e) { show(e, true); e.style.filter = ''; });
      qa(s, '[data-k], .lv .lb, .lv .ft, .lv .bar').forEach(function (e) { e.style.filter = ''; });
    }
  });

  /* 세 장을 샘플 효과로 바꿔요: 효과 이름 · 단계 +1 · 발표자 노트 앞에 한 줄 */
  (function () {
    var map = [['.slide.cover.v3', 'eCover', '들어오면 제목만 화면 가운데 크게. <b>클릭 1</b>: 제목이 왼쪽 자리로 들어가고 오른쪽 그림이 와요. 그다음은 원래 노트 그대로.'],
      ['.slide.hx.v3.map', 'eMap', '들어오면 「오늘은 AI를 식당으로」만 크게. <b>클릭 1</b>: 머리글 + 다섯 칸(앞면). <b>클릭 2</b>: 뒤집기 + 펜 메모. 아래 노트의 「클릭 n」은 하나씩 밀려요.'],
      ['.slide.floor.v3', 'eFloor', '들어오면 제목만 크게. <b>클릭 1</b>: 그냥 AI 막대. <b>클릭 2</b>: 하네스 AI 막대 + 펜. <b>클릭 3</b>: 결론 + 근거 줄. 아래 노트의 「클릭 n」은 하나씩 밀려요.']];
    map.forEach(function (m) {
      var s = stage.querySelector(m[0]); if (!s) return;
      s.setAttribute('data-fx', m[1]);
      s.setAttribute('data-steps', (+(s.getAttribute('data-steps') || 0)) + 1);
      s.classList.add('e');
      var n = s.querySelector('.note'); if (n) n.innerHTML = '<b>[샘플 E]</b> ' + m[2] + '<br>' + n.innerHTML;
    });
  })();
