
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

  /* ============ 7 비유 지도 → 주방 하나 (샘플 E · 12단계)
     0 큰 글자 「오늘은 AI를 식당으로」
     1 AI 앱 화면(상표 없는 흉내 화면) 하나가 와요 — 실습 때 보실 화면
     2~6 화면의 한 곳에 펜 동그라미 → 오른쪽 큰 카드: [진짜 이름] → [그림 + 비유 이름] + 쉬운 한 문장 (한 박자에 한 쌍)
         앱 화면 → 주방 · 답을 써 주는 AI → 요리사 · 입력창의 부탁 → 주문서 · 만든 회사 → 식당 · 옆에 붙인 도구 → 레시피·도구(하네스)
     7 주방 하나: 가운데 큰 요리사 (식당 A·B·C 판 세 개 대신)
     8~11 도구가 두 개씩 큰 그림 아이콘 + 짧은 이름 + 쉬운 설명으로 (이름도 같아요 · 이름이 돌아가며 바뀜 · 점선 = 식당마다 달라요)
     12 요리사 둘레에 하네스 고리 + 결론 두 줄
     ============ */
  var M7 = {
    pairs: [
      { key: 'win', real: 'AI 앱 화면', an: '주방', pic: 'il:kitchen-backdrop', se: '선생님이 여시는 AI 앱 화면이에요', note: '여기가 주방', col: 'red' },
      { key: 'bub', real: '답을 써 주는 AI', an: '요리사', pic: 'chef', se: '질문에 답을 써 주는 똑똑한 프로그램', note: '여기가 요리사', col: 'red' },
      { key: 'inp', real: '입력창에 쓰는 부탁', an: '주문서', pic: 'ic:receipt', se: '내가 입력창에 쓰는 부탁(프롬프트)', note: '이게 주문서', col: 'red' },
      { key: 'logo', real: 'AI를 만드는 회사', an: '식당', pic: 'il:restaurants', se: '이 앱을 만들어 내놓은 회사', note: '만든 곳 = 식당', col: 'blue' },
      { key: 'side', real: '하네스', an: '레시피·도구', pic: 'tools', se: 'AI 옆에 붙여 주는 도구와 레시피', note: '이게 하네스', col: 'blue' }
    ],
    tools: [
      { g: 1, ic: 'search', nm: '찾아보기', sub: '= 인터넷 검색' },
      { g: 1, ic: 'file-up', nm: '파일 읽기', sub: '= 올린 파일 읽기' },
      { g: 2, ic: 'bookmark', nm: '기억', sub: '= 지난 이야기 기억', chip: '이름도 같아요' },
      { g: 2, ic: 'wand-sparkles', nm: '스킬', sub: '= 정해 둔 일 처리법', chip: '이름도 같아요' },
      { g: 3, ic: 'telescope', nm: '깊이 조사', sub: '= 오래 찾아 정리', cyc: ['심층 리서치', '리서치', '딥 리서치'] },
      { g: 3, ic: 'plug', nm: '다른 앱 연결', sub: '= 다른 앱과 이어 주기', cyc: ['플러그인', '커넥터', '연결된 앱'] },
      { g: 4, ic: 'mouse-pointer-click', nm: '대신 일해 주기', sub: '= 화면을 대신 눌러 줘요', part: true },
      { g: 4, ic: 'image', nm: '그림 · 영상', sub: '= 그림 · 영상 만들기', part: true }
    ],
    caps: ['요리사(AI) 솜씨는 식당마다 비슷해요', '찾아보기 · 파일 읽기 — 어느 주방에나 있어요', '기억 · 스킬 — <b>이름까지 같아요</b>', '깊이 조사 · 앱 연결 — 하는 일은 같은데 <b>이름이 달라요</b>', '대신 일하기 · 그림과 영상 — <b>있는 식당도, 없는 식당도</b>']
  };
  // icons: building-2 bot send search file-up file-text scroll-text receipt package utensils-crossed shield-check bookmark wand-sparkles telescope plug mouse-pointer-click image chef-hat
  function m7ic(n) { return '<svg class="ic"><use href="#' + n + '"/></svg>'; }
  function m7pic(p) {
    if (p === 'chef') return '<div class="pic chef"><img alt="" src="' + (PUPPET.head || '') + '"></div>';
    if (p === 'tools') return '<div class="pic tools">' + ['scroll-text', 'package', 'utensils-crossed', 'shield-check'].map(m7ic).join('') + '</div>';
    if (p.indexOf('il:') === 0) return '<div class="pic il" data-il="' + p.slice(3) + '"></div>';
    return '<div class="pic svg">' + m7ic(p.slice(3)) + '</div>';
  }
  function m7prep(s) {
    if (q(s, '.e7a')) return;
    eBig(s, '// 오늘의 비유 지도', '오늘은 AI를<br><em>식당</em>으로');
    var A = emk('div', 'e7a', '', s);
    A.innerHTML = '<div class="ewin">' +
      '<div class="wtb"><i></i><i></i><i></i><span class="wlg">' + m7ic('building-2') + '</span><b>AI 앱</b></div>' +
      '<div class="wbd"><div class="wchat">' +
        '<div class="wu">중2 과학 빛 복습 게임 만들어 줘</div>' +
        '<div class="wa"><span class="wav">' + m7ic('bot') + '</span><div class="wbb"><span class="wt">좋아요! 먼저 기획 세 가지를 보여 드릴게요.</span><i></i><i></i><i class="wsh"></i></div></div>' +
        '<div class="wint"><span>퀴즈는 10문제로 해 줘</span>' + m7ic('send') + '</div>' +
      '</div><div class="wside"><b>도구 · 레시피</b><span>' + m7ic('search') + '찾아보기</span><span>' + m7ic('file-text') + '파일 읽기</span><span>' + m7ic('scroll-text') + '레시피</span></div></div></div>' +
      M7.pairs.map(function (p, i) {
        return '<div class="ecard" data-i="' + i + '"><div class="rl"><span class="tg">진짜</span><b>' + p.real + '</b></div>' +
          '<svg class="ar" viewBox="0 0 40 70" aria-hidden="true"><path d="M20 4 V60 M8 48 L20 62 L32 48" pathLength="1"/></svg>' +
          '<div class="row">' + m7pic(p.pic) + '<div class="nm"><span class="tg">비유</span><b>' + p.an + '</b></div></div><p class="se">' + p.se + '</p></div>';
      }).join('');
    var B = emk('div', 'e7b', '', s);
    B.innerHTML = '<div class="kp"></div><svg class="kl" viewBox="0 0 1920 1080" aria-hidden="true"></svg>' +
      '<div class="chef"><img class="h" alt="" src="' + (PUPPET.head || '') + '"><img class="t" alt="" src="' + (PUPPET.torso || '') + '"></div>' +
      M7.tools.map(function (t, i) {
        return '<div class="tl ' + (i % 2 ? 'r' : 'l') + (t.part ? ' part' : '') + '" data-g="' + t.g + '"><span class="ci">' + m7ic(t.ic) + '</span><div class="tx"><b>' + t.nm + '</b><small>' + t.sub + '</small>' +
          (t.chip ? '<em class="chip">' + t.chip + '</em>' : '') + (t.cyc ? '<em class="chip cy">' + t.cyc.join(' · ') + '</em>' : '') + '</div></div>';
      }).join('') +
      '<div class="kcap">' + M7.caps.map(function (c, i) { return '<p data-c="' + i + '">' + c + '</p>'; }).join('') + '</div>';
    // 도구 자리: 왼쪽 · 오른쪽 네 줄
    qa(B, '.tl').forEach(function (t, i) { var row = Math.floor(i / 2); t.style.top = (302 + row * 140) + 'px'; });
    q(B, '.kp').style.backgroundImage = 'linear-gradient(var(--e-kshade),var(--e-kshade))' + (PUPPET.kitchen ? ',url(' + PUPPET.kitchen + ')' : '');
  }
  // 흉내 화면의 부분 → 펜 동그라미 · 메모 자리
  function m7pens(s) {
    var A = q(s, '.e7a'), svg = ePen(A), P = {};
    function box(el) { var o = eoff(el, s); return { x: o.x, y: o.y, w: el.offsetWidth, h: el.offsetHeight }; }
    var W = box(q(A, '.ewin')), Bb = box(q(A, '.wa')), I = box(q(A, '.wint')), L = box(q(A, '.wlg')), S = box(q(A, '.wside'));
    function rect(b, pad, seed) { var x0 = b.x - pad, y0 = b.y - pad, x1 = b.x + b.w + pad, y1 = b.y + b.h + pad; return eWob([[x0 + 30, y0 - 4], [x1, y0 + 2], [x1 + 4, y1], [x0, y1 + 3], [x0 - 3, y0 + 8], [x0 + 60, y0 - 6]], 6, seed); }
    var G = {
      win: { d: rect(W, 14, 31), nx: W.x + 10, ny: W.y + W.h + 22 },
      bub: { d: eLoop(Bb.x + Bb.w / 2, Bb.y + Bb.h / 2, Bb.w / 2 + 30, Bb.h / 2 + 26, 9), nx: Bb.x + Bb.w - 210, ny: Bb.y + Bb.h + 34 },
      inp: { d: eLoop(I.x + I.w / 2, I.y + I.h / 2, I.w / 2 + 26, I.h / 2 + 22, 13), nx: I.x + I.w - 230, ny: I.y - 70 },
      logo: { d: eLoop(L.x + L.w / 2, L.y + L.h / 2, L.w / 2 + 22, L.h / 2 + 18, 17), nx: L.x + L.w + 120, ny: L.y - 4 },
      side: { d: rect(S, 10, 23), nx: S.x - 6, ny: S.y + S.h + 20 }
    };
    M7.pairs.forEach(function (p) { var g = G[p.key]; P[p.key] = { p: eStroke(svg, g.d, p.col, p.key), n: eNoteAt(A, p.key, p.note, p.col, g.nx, g.ny) }; });
    return P;
  }
  function m7lines(s) {   // 요리사 → 도구 가는 선
    var B = q(s, '.e7b'), svg = q(B, '.kl'), ch = q(B, '.chef'), co = eoff(ch, s), cx = co.x + ch.offsetWidth / 2, cy = co.y + ch.offsetHeight * 0.45;
    return qa(B, '.tl').map(function (t, i) {
      var o = eoff(t, s), r = t.classList.contains('r'), x = r ? o.x - 14 : o.x + t.offsetWidth + 14, y = o.y + 52;
      var p = svg.querySelector('[data-i="' + i + '"]');
      if (!p) { p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('data-i', i); p.setAttribute('pathLength', '1'); p.setAttribute('class', 'kln' + (t.classList.contains('part') ? ' part' : '')); svg.appendChild(p); }
      p.setAttribute('d', 'M' + cx.toFixed(0) + ' ' + cy.toFixed(0) + ' L' + x.toFixed(0) + ' ' + y.toFixed(0));
      p.style.strokeDasharray = t.classList.contains('part') ? '' : 1;
      return p;
    });
  }
  function m7kpens(s) {   // 고리(하네스) + 「식당마다 달라요」
    var B = q(s, '.e7b'), svg = ePen(B), ch = q(B, '.chef'), co = eoff(ch, s), cx = co.x + ch.offsetWidth / 2, cy = co.y + ch.offsetHeight / 2;
    var ring = eStroke(svg, eLoop(cx, cy, ch.offsetWidth / 2 + 70, ch.offsetHeight / 2 + 34, 41), 'acc', 'ring');
    var t7 = qa(B, '.tl')[6], t8 = qa(B, '.tl')[7], a = eoff(t7, s), b = eoff(t8, s);
    var ny = co.y + ch.offsetHeight + 6, n = eNoteAt(B, 'part', '식당마다 달라요', 'red', cx - 130, ny);
    var ar = eStroke(svg, eWob([[cx - 140, ny + 30], [cx - 220, ny + 34], [a.x + t7.offsetWidth + 20, a.y + 70]], 5, 3) + ' ' + eHead(a.x + t7.offsetWidth + 20, a.y + 70, Math.PI + 0.2, 18) + ' ' +
      eWob([[cx + 140, ny + 30], [cx + 220, ny + 34], [b.x - 20, b.y + 70]], 5, 5) + ' ' + eHead(b.x - 20, b.y + 70, -0.2, 18), 'red', 'partar');
    return { ring: ring, n: n, ar: ar };
  }
  function m7setA(s, st) {   // 1~6
    var A = q(s, '.e7a'), P = m7pens(s), k = st - 2;
    show(q(A, '.ewin'), true); q(A, '.ewin').style.filter = '';
    M7.pairs.forEach(function (p, i) {
      var on = i <= k, cur = i === k;
      P[p.key].p.style.strokeDashoffset = on ? 0 : 1; P[p.key].p.style.opacity = cur ? 1 : 0.16;
      var n = P[p.key].n; n.style.visibility = on ? 'visible' : 'hidden'; n.style.clipPath = ''; n.style.opacity = cur ? 1 : 0.45;
      var c = q(A, '.ecard[data-i="' + i + '"]'); show(c, cur); c.style.filter = ''; q(c, '.ar path').style.strokeDashoffset = 0;
    });
    qa(A, '.ewin .whl').forEach(function (e) { e.classList.remove('whl'); });
    if (k >= 0) { var tg = { win: '.ewin', bub: '.wa', inp: '.wint', logo: '.wlg', side: '.wside' }[M7.pairs[k].key]; q(A, tg).classList.add('whl'); }
  }
  function m7setB(s, st) {   // 7~12
    var B = q(s, '.e7b'), g = st - 7, L = m7lines(s), K = m7kpens(s);
    show(q(B, '.kp'), true); show(q(B, '.chef'), true); q(B, '.chef').style.filter = '';
    qa(B, '.tl').forEach(function (t, i) {
      var on = +t.getAttribute('data-g') <= g; show(t, on); t.style.filter = '';
      L[i].style.strokeDashoffset = on ? 0 : 1; L[i].style.opacity = on ? 1 : 0;
      var cy = q(t, '.cy'); if (cy) { var T = M7.tools[i]; cy.textContent = T.cyc.join(' · '); cy.style.transform = ''; cy.style.opacity = 1; }
    });
    qa(B, '.kcap p').forEach(function (p) { show(p, +p.getAttribute('data-c') === g && g < 5); });
    q(B, '.kcap').style.display = g >= 5 ? 'none' : '';
    K.ring.style.strokeDashoffset = g >= 5 ? 0 : 1;
    K.n.style.visibility = g >= 4 ? 'visible' : 'hidden'; K.n.style.clipPath = ''; K.n.style.opacity = 1;
    K.ar.style.strokeDashoffset = g >= 4 ? 0 : 1;
    var pu = q(s, '.hxpunch'); show(pu, g >= 5); show(q(pu, '.p1'), true); show(q(pu, '.p2'), true); MO.kinSet(q(pu, '.m-kin'), g >= 5);
  }
  function m7set(s, st) {
    s.classList.toggle('map', st <= 6);
    s.classList.toggle('e7k', st >= 7);
    eBigSet(s, false);
    var A = q(s, '.e7a'), B = q(s, '.e7b');
    A.style.display = st <= 6 ? '' : 'none'; B.style.display = st >= 7 ? '' : 'none'; A.style.visibility = B.style.visibility = '';
    A.style.opacity = B.style.opacity = ''; A.style.transform = B.style.transform = ''; A.style.filter = B.style.filter = '';
    var hm = q(s, '.hd.hm'); [q(hm, 'h2'), q(hm, '.kicker')].forEach(function (e) { show(e, true); e.style.filter = ''; });
    MO.wipeSet(q(hm, 'h2'), true);
    v3hd(s, 0, true);
    if (st <= 6) m7setA(s, st); else m7setB(s, st);
  }
  FX.eMap = {
    enter: function (s, st) {
      m7prep(s); eHud(s);
      if (st === 0) {
        m7set(s, 1); s.classList.add('e0'); q(s, '.e7a').style.display = 'none';
        eBigSet(s, true);
        if (V3DIR < 0 || REDUCED) return;
        eHudIn(s, 0); eBigIn(s, 60);
        return;
      }
      s.classList.remove('e0');
      m7set(s, st);
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || REDUCED || st === 0) { eInst(function () { FX.eMap.enter(s, st); }); return; }
      s.classList.remove('e0');
      m7set(s, st - 1);   // 지난 단계를 끝 모습으로 맞추고
      var A = q(s, '.e7a'), B = q(s, '.e7b');
      if (st === 1) {   // 큰 글자 퇴장 → 점이 화면 왼쪽 위(로고)로 날아가 → 흉내 화면이 그 점에서 펼쳐져요
        m7set(s, 1);
        var big = q(s, '.ebig'), d = q(s, '.edot'), win = q(A, '.ewin'), lg = eoff(q(A, '.wlg'), s);
        big.style.visibility = 'visible'; eOut(big, 0);
        var hm = q(s, '.hd.hm'); eIn(q(hm, 'h2'), 90, { dy: 40, blur: 10 }); eIn(q(hm, '.kicker'), 60, { dy: 20 });
        eDotAtSlot(s); var x0 = parseFloat(d.style.left), y0 = parseFloat(d.style.top), x1 = lg.x + 10, y1 = lg.y + 10;
        MO.tw(220, 30, 'inout', function (e, t) { d.style.opacity = 1; d.style.left = lerp(x0, x1, e).toFixed(1) + 'px'; d.style.top = (lerp(y0, y1, e) - 80 * Math.sin(Math.PI * e)).toFixed(1) + 'px'; d.style.filter = 'blur(' + (3 * Math.sin(Math.PI * t)).toFixed(2) + 'px)'; }, function () { d.style.filter = ''; });
        win.style.transformOrigin = '4% 5%';
        MO.tw(240, 250, 'snap', function (e) { d.style.opacity = 1 - e; win.style.opacity = clamp01(e * 3); win.style.transform = e >= 1 ? '' : 'scale(' + lerp(0.04, 1, e).toFixed(4) + ')'; win.style.filter = e >= 1 ? '' : 'blur(' + (6 * (1 - e)).toFixed(2) + 'px)'; });
        return;
      }
      if (st <= 6) {   // 한 쌍: 펜 동그라미(지난 것은 옅게) → 카드 [진짜] ↓ [그림 + 비유] + 한 문장
        var k = st - 2, p = M7.pairs[k], P = m7pens(s), card = q(A, '.ecard[data-i="' + k + '"]'), prev = q(A, '.ecard[data-i="' + (k - 1) + '"]');
        m7setA(s, st); show(card, false);
        P[p.key].p.style.strokeDashoffset = 1; P[p.key].n.style.visibility = 'hidden';
        if (prev) { show(prev, true); eOut(prev, 0); MO.tw(1, ET.out, 'linear', function () {}, function () { prev.style.visibility = ''; show(prev, false); }); }
        eDraw(P[p.key].p, 40, 280); eWrite(P[p.key].n, 240, 280);
        var parts = [q(card, '.rl'), q(card, '.row'), q(card, '.se')];
        card.style.opacity = 1; parts.forEach(function (e) { e.style.opacity = 0; });
        eIn(parts[0], 160, { dx: -40, dy: 0 });
        var ar = q(card, '.ar path'); ar.style.strokeDashoffset = 1; MO.draw(ar, 300, 180, 'snap');
        eIn(parts[1], 400, { dy: 30, s: 0.94, blur: 10 }); eIn(parts[2], 520, { dy: 14 });
        return;
      }
      if (st === 7) {   // 화면 → 주방 하나: 흉내 화면은 번지며 빠지고, 가운데 요리사가 통통
        m7set(s, 7);
        A.style.display = ''; eOut(A, 0);
        v3hd(s, 60, false);
        eIn(q(B, '.kp'), 60, { dy: 0, s: 1.02, blur: 8 });
        MO.spring(q(B, '.chef'), 160, { s: 0.3, dy: 40, bouncy: true });
        eIn(q(B, '.kcap p[data-c="0"]'), 420, { dy: 20 });
        MO.tw(1, ET.out + 10, 'linear', function () {}, function () { A.style.display = 'none'; A.style.visibility = ''; });
        return;
      }
      var g = st - 7, tl = qa(B, '.tl'), L = m7lines(s), ch = q(B, '.chef'), co = eoff(ch, s), cx = co.x + ch.offsetWidth / 2, cy = co.y + ch.offsetHeight / 2;
      var old = q(B, '.kcap p[data-c="' + (g - 1) + '"]');
      if (old) MO.tw(ET.out, 0, 'out', function (e) { old.style.opacity = 1 - e; old.style.transform = 'translateY(' + (-20 * e).toFixed(1) + 'px)'; if (e >= 1) { old.style.opacity = 0; old.style.transform = ''; } });
      if (g <= 4) {   // 도구 두 개: 요리사 쪽에서 튀어나와 자리(흐림 꼬리) + 선
        var nu = q(B, '.kcap p[data-c="' + g + '"]');
        tl.forEach(function (t, i) {
          if (+t.getAttribute('data-g') !== g) return;
          var o = eoff(t, s), dx = cx - (o.x + t.offsetWidth / 2), dy = cy - (o.y + 60), j = i % 2;
          t.style.opacity = 0;
          eIn(t, 40 + j * 70, { dx: dx * 0.3, dy: dy * 0.3, s: 0.9, blur: 10, dur: 230 });
          L[i].style.opacity = 1; if (!t.classList.contains('part')) { L[i].style.strokeDashoffset = 1; MO.draw(L[i], 20 + j * 70, 200, 'snap'); } else { L[i].style.opacity = 0; MO.tw(200, 60 + j * 70, 'out', function (e) { L[i].style.opacity = e; }); }
          var chip = q(t, '.chip');
          if (chip && !chip.classList.contains('cy')) { chip.style.opacity = 0; MO.stamp(chip, 330 + j * 70, { s: 1.5 }); }
          if (chip && chip.classList.contains('cy')) {   // 이름이 한 번 돌아가며 바뀌고(한 이름에 0.3초) → 세 이름이 한 줄로 멈춰요
            var names = M7.tools[i].cyc, at0 = 320 + j * 140;
            names.forEach(function (nm, ni) {
              MO.tw(150, at0 + ni * 300, 'snap', function (e) { chip.textContent = nm; chip.style.opacity = 1; chip.style.transform = e >= 1 ? '' : 'perspective(400px) rotateX(' + (80 * (1 - e)).toFixed(1) + 'deg)'; });
            });
            MO.tw(180, at0 + names.length * 300, 'snap', function (e) { chip.textContent = names.join(' · '); chip.style.transform = e >= 1 ? '' : 'perspective(400px) rotateX(' + (80 * (1 - e)).toFixed(1) + 'deg)'; });
            chip.style.opacity = 0;
          }
        });
        if (nu) eIn(nu, 200, { dy: 20 });
        if (g === 4) { var K = m7kpens(s); K.ar.style.strokeDashoffset = 1; K.n.style.visibility = 'hidden'; eWrite(K.n, 380, 280); eDraw(K.ar, 520, 260); }
        return;
      }
      // 12: 하네스 고리가 요리사를 두르고, 도구가 한 번 안쪽으로 모였다 풀려요 → 결론
      MO.tw(1, ET.out, 'linear', function () {}, function () { q(B, '.kcap').style.display = 'none'; });
      var K2 = m7kpens(s); K2.ring.style.strokeDashoffset = 1; eDraw(K2.ring, 40, 360);
      MO.gather(tl, cx, cy, 200, { dur: 360, pull: 0.08, turn: 0.05 });
      var pu = q(s, '.hxpunch'), p2 = q(pu, '.m-kin');
      show(pu, true); show(q(pu, '.p2'), true); MO.kinSet(p2, false);
      eIn(q(pu, '.p1'), 420, { dy: 24 }); MO.kin(p2, 600, { gap: 30, dur: 260 });
    }
  };

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
      ['.slide.hx.v3.map', 'eMap', '[5~9분 · 샘플 E] 들어오면 「오늘은 AI를 식당으로」만 크게. 「오늘은 AI를 식당으로 바꿔서 이야기할게요.」 <b>클릭 1</b>: AI 앱 화면 하나. 「실습 때 보실 화면이 대략 이렇게 생겼어요.」 <b>클릭 2</b>: 「선생님이 여시는 이 AI 앱 화면, 이게 주방이에요.」 <b>클릭 3</b>: 「여기 질문에 답을 써 주는 똑똑한 프로그램, 이게 AI예요. 요리사라고 부를게요.」 <b>클릭 4</b>: 「아래 입력창에 쓰는 부탁, 프롬프트는 주문서예요.」 <b>클릭 5</b>: 「이 앱을 만들어 내놓은 AI 회사는 식당이에요.」 <b>클릭 6</b>: 「AI 옆에 붙여 주는 도구와 레시피, 이게 하네스예요.」 <b>어려우면 이것만: 「요리사 = AI, 레시피·도구 = 하네스.」</b> <b>클릭 7</b>: 주방 하나 + 가운데 요리사. 「사실 여러분은 이미 하네스를 쓰고 계세요. 가운데 요리사 솜씨는 식당마다 비슷해요.」 <b>클릭 8</b>: 「그 둘레에 식당마다 도구를 갖춰 놨어요. 인터넷에서 찾아보기, 파일 읽기. 이건 어느 주방에나 있어요.」 <b>클릭 9</b>: 「기억하기, 그리고 스킬. 이름까지 같아요.」 <b>클릭 10</b>: 「깊이 조사하기, 다른 앱과 연결하기. 하는 일은 같은데 이름이 달라요. 플러그인, 커넥터, 연결된 앱.」 <b>클릭 11</b>: 「대신 일해 주기, 그림과 영상. 여기는 있는 식당도 있고 없는 식당도 있어요.」 <b>클릭 12</b>: 「요리사도 중요하지만, 주방에 무엇을 갖춰 주느냐, 그러니까 하네스가 음식을 바꿔요. 그래서 오늘은 우리가 직접 하네스를 끼워 봅니다.」 기능 이름은 2026년 11월 각 앱 공식 도움말 기준이고, 몇 개는 쉬운 말로 바꿨어요. 요금제·기기마다 다르고 자주 바뀌어요. 식당이 어느 회사인지는 화면에서 말하지 않아요. 물으시면 쉬는 시간에 따로(대응표는 deck-v2-NOTICE.md). 어느 식당이 더 낫다는 말은 하지 않아요.', 12],
      ['.slide.floor.v3', 'eFloor', '들어오면 제목만 크게. <b>클릭 1</b>: 그냥 AI 막대. <b>클릭 2</b>: 하네스 AI 막대 + 펜. <b>클릭 3</b>: 결론 + 근거 줄. 아래 노트의 「클릭 n」은 하나씩 밀려요.']];
    map.forEach(function (m) {
      var s = stage.querySelector(m[0]); if (!s) return;
      s.setAttribute('data-fx', m[1]);
      s.setAttribute('data-steps', m[3] || (+(s.getAttribute('data-steps') || 0)) + 1);
      s.classList.add('e');
      var n = s.querySelector('.note'); if (n) n.innerHTML = m[3] ? m[2] : '<b>[샘플 E]</b> ' + m[2] + '<br>' + n.innerHTML;   // 7장은 노트를 새 박자로 통째로
    });
  })();
