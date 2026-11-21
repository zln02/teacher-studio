  /* =====================================================================
     deck-v3 · 모션 어휘 (MO). 뜻에 따라 움직임을 골라요 (ES2017 · anime.js 4.5.0 시계만 빌려 써요)
       spring  통통 튀며 자리 잡기 (넘쳤다 돌아와요)  → 친근한 것: 로봇 · 요리사 · 재료 · 생각 풍선
       snap    빠르게 와서 딱 멈추기                → 결과 · 숫자 · 답 · 판정
       flip    카드 뒤집기                          → 전 → 후, 그냥 AI → 하네스 AI
       gather  돌며 모이기                          → 부품(레시피 · 도구 · 재료)이 「하네스」로 모여요
       wipe    색 막대 가림막                        → 제목 · 구간 바뀜
       kin     글자 하나하나 움직임                   → 핵심 낱말·문장에만 (「하네스」 · 「기획부터 같이 해 줘」 · 가져가실 세 가지)
     한 박자는 0.3~0.9초. 글자는 자리 잡으면 가만히. 글자 뒤 끝없는 반복 없음.
     움직임 줄이기(prefers-reduced-motion 또는 ?reduced=1): 옮겨 다니지 않고 0.2초 나타나기만 해요.
     장 안의 모든 움직임은 MO.run 목록에 모여 있어서, 장을 떠나거나 뒤로 갈 때 한 번에 멈추고 끝 모습으로 맞춰요.
     ===================================================================== */
  /* 한 벌의 움직임 값(토큰): 2D · 글자 · 카드 · 3D가 모두 이것만 써요 (3D 장면은 초 단위로 TOK.sec())
     박자: xs 160 · s 320 · m 620 · l 900 ms | 사이 간격(stagger) 90 ms · 글자 36 ms | 거리: 이동 26 px · 크게 46 px
     방향: 들어올 때는 아래(+y) 또는 왼쪽(−x)에서, 나갈 때는 위로. 넘어지는 벽처럼 무게가 뜻인 것만 아래로 떨어져요.
     안무: 3D가 있는 장은 3D가 먼저 내려앉고(TOK.lead) 글자가 같은 박자로 따라와요 */
  var TOK = { xs: 160, s: 320, m: 620, l: 900, gap: 90, cgap: 36, move: 26, big: 46, lead: 900,
    sec: function (ms) { return ms / 1000; } };
  var EZ = {
    linear: function (t) { return t; },
    out: function (t) { return 1 - Math.pow(1 - t, 3); },
    snap: function (t) { return 1 - Math.pow(1 - t, 5); },                     // 빠르게 들어와 딱 멈춤
    inout: function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; },
    fall: function (t) { return t * t; },                                      // 무게 있게 떨어짐
    spring: function (t) { return t >= 1 ? 1 : 1 - Math.exp(-6.2 * t) * Math.cos(12.5 * t); },   // 약 16% 넘쳤다 돌아옴
    bounce: function (t) { return t >= 1 ? 1 : 1 - Math.exp(-5.2 * t) * Math.cos(16 * t); }      // 더 통통
  };
  function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  var MO = { run: [] };
  // 한 박자: upd(e, raw)를 0→1로 불러요. 시작 모습은 바로 칠해요 (anime는 지연 동안 칠하지 않으니까요)
  MO.tw = function (dur, delay, ease, upd, done) {
    var f = EZ[ease] || EZ.out, p = { t: 0 };
    upd(f(0), 0);
    if (REDUCED) { dur = Math.min(dur, 200); delay = Math.min(delay || 0, 200); }
    var a = A.animate(p, { t: 1, duration: dur, delay: delay || 0, ease: 'linear',
      onUpdate: function () { upd(f(p.t), p.t); },
      onComplete: function () { upd(1, 1); if (done) done(); } });
    MO.run.push(a);
    return a;
  };
  MO.stop = function () { MO.run.forEach(function (a) { try { a.pause(); } catch (e) {} }); MO.run = []; };
  function tf(el, x, y, s, r, extra) {
    el.style.transform = 'translate(' + (x || 0).toFixed(1) + 'px,' + (y || 0).toFixed(1) + 'px) scale(' + (s === undefined ? 1 : s).toFixed(4) + ')' + (r ? ' rotate(' + r.toFixed(2) + 'deg)' : '') + (extra || '');
  }
  function show(el, on) { el.style.opacity = on ? '1' : '0'; if (on) el.style.transform = ''; }
  MO.show = show;

  // 가림막: 색 막대가 왼쪽에서 덮고(0~45%) → 글자를 두고 오른쪽으로 걷혀요(45~100%). 약 0.62초
  MO.prepWipe = function (el) {
    if (el.__w) return el.__w;
    var wt = document.createElement('span'); wt.className = 'wt';
    while (el.firstChild) wt.appendChild(el.firstChild);
    var bar = document.createElement('i'); bar.className = 'wbar';
    el.appendChild(wt); el.appendChild(bar);
    el.__w = { wt: wt, bar: bar };
    return el.__w;
  };
  MO.wipe = function (el, at, dur) {
    var w = MO.prepWipe(el); dur = dur || TOK.m;
    if (REDUCED) { w.bar.style.transform = 'scaleX(0)'; w.wt.style.clipPath = ''; return MO.tw(200, at, 'out', function (e) { w.wt.style.opacity = e; }); }
    return MO.tw(dur, at, 'linear', function (e, t) {
      var a = EZ.inout(clamp01(t / 0.45)), b = EZ.out(clamp01((t - 0.45) / 0.55));
      if (t < 0.45) { w.bar.style.transformOrigin = '0 50%'; w.bar.style.transform = 'scaleX(' + a.toFixed(4) + ')'; w.wt.style.opacity = 0; }
      else { w.bar.style.transformOrigin = '100% 50%'; w.bar.style.transform = 'scaleX(' + (1 - b).toFixed(4) + ')'; w.wt.style.opacity = 1; }
      w.wt.style.transform = t < 0.45 ? 'translateX(-16px)' : 'translateX(' + (-16 * (1 - b)).toFixed(1) + 'px)';
    });
  };
  MO.wipeSet = function (el, on) { var w = MO.prepWipe(el); w.bar.style.transform = 'scaleX(0)'; w.wt.style.opacity = on ? 1 : 0; w.wt.style.transform = ''; };
  // 가림 막대 없이 왼쪽부터 드러나기 (머리글 kicker)
  MO.reveal = function (el, at, dur) {
    return MO.tw(dur || TOK.m - TOK.xs, at, 'out', function (e) {
      el.style.opacity = REDUCED ? e : 1;
      if (!REDUCED) { el.style.clipPath = 'inset(-10% ' + ((1 - e) * 100).toFixed(2) + '% -10% 0)'; el.style.transform = 'translateX(' + (-14 * (1 - e)).toFixed(1) + 'px)'; }
      if (e >= 1) { el.style.clipPath = ''; el.style.transform = ''; }
    });
  };
  // 탁: 아래(또는 dx, dy)에서 빠르게 와서 딱 멈춰요
  MO.snap = function (el, at, o) {
    o = o || {}; var dx = o.dx || 0, dy = o.dy === undefined ? TOK.move : o.dy, s0 = o.s === undefined ? 1 : o.s;
    return MO.tw(o.dur || TOK.s, at, 'snap', function (e) {
      el.style.opacity = clamp01(e * 2.2);
      if (REDUCED) { el.style.opacity = e; return; }
      tf(el, dx * (1 - e), dy * (1 - e), lerp(s0, 1, e));
      if (e >= 1) el.style.transform = '';
    });
  };
  // 통통: 작게 시작해 넘쳤다 돌아와요 (origin: 'x% y%')
  MO.spring = function (el, at, o) {
    o = o || {}; var s0 = o.s === undefined ? 0.2 : o.s, dx = o.dx || 0, dy = o.dy || 0, r0 = o.r || 0;
    if (o.origin) el.style.transformOrigin = o.origin;
    return MO.tw(o.dur || TOK.l - 140, at, 'linear', function (e, t) {
      var k = (o.bouncy ? EZ.bounce : EZ.spring)(t);
      el.style.opacity = clamp01(t * 5);
      if (REDUCED) { el.style.opacity = e; return; }
      tf(el, dx * (1 - k), dy * (1 - k), lerp(s0, 1, k), r0 * (1 - k));
      if (t >= 1) el.style.transform = '';
    });
  };
  // 도장: 크게 와서 쾅 (판정 · 이름표)
  MO.stamp = function (el, at, o) {
    o = o || {};
    return MO.tw(o.dur || TOK.s, at, 'snap', function (e) {
      el.style.opacity = clamp01(e * 3);
      if (REDUCED) { el.style.opacity = e; return; }
      tf(el, 0, 0, lerp(o.s || 1.6, 1, e));
      if (e >= 1) el.style.transform = '';
    });
  };
  // 떨림 한 번 (부딪힘): 0.32초
  MO.shake = function (el, at, amp) {
    if (REDUCED) return null;
    amp = amp || 8;
    return MO.tw(TOK.s, at, 'linear', function (e, t) { el.style.transform = t >= 1 ? '' : 'translateX(' + (Math.sin(t * 40) * amp * (1 - t)).toFixed(1) + 'px)'; });
  };
  // 글자 움직임: 낱말을 안 끊기게 감싸고, 글자마다 아래에서 통통 올라와요
  MO.split = function (el) {
    if (el.__k) return el.__k;
    var chars = [];
    (function walk(node) {
      [].slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(function (w) {
            if (!w) return;
            if (/^\s+$/.test(w)) { frag.appendChild(document.createTextNode(w)); return; }
            var kw = document.createElement('span'); kw.className = 'kw';
            for (var i = 0; i < w.length; i++) { var c = document.createElement('span'); c.className = 'kc'; c.textContent = w[i]; kw.appendChild(c); chars.push(c); }
            frag.appendChild(kw);
          });
          node.replaceChild(frag, n);
        } else if (n.nodeType === 1 && n.tagName !== 'BR' && n.tagName !== 'svg') walk(n);
      });
    })(el);
    el.__k = chars;
    return chars;
  };
  MO.kin = function (el, at, o) {
    o = o || {}; var cs = MO.split(el), gap = o.gap || TOK.cgap, last = 0;
    el.style.opacity = 1;
    cs.forEach(function (c, i) {
      last = MO.tw(o.dur || TOK.m, at + i * gap, 'linear', function (e, t) {
        var k = EZ.spring(t);
        c.style.opacity = clamp01(t * 4);
        if (REDUCED) { c.style.opacity = e; return; }
        c.style.transform = t >= 1 ? '' : 'translateY(' + (0.55 * (1 - k)).toFixed(3) + 'em) rotate(' + (12 * (1 - k)).toFixed(2) + 'deg) scale(' + lerp(0.5, 1, k).toFixed(3) + ')';
      });
    });
    return last;
  };
  MO.kinSet = function (el, on) { MO.split(el).forEach(function (c) { c.style.opacity = on ? 1 : 0; c.style.transform = ''; }); el.style.opacity = 1; };
  // 낱말 단위로 아래 가림막에서 올라와요 (큰 제목)
  MO.words = function (el, at, o) {
    o = o || {};
    if (!el.__wd) {
      MO.split(el);
      el.__wd = [].slice.call(el.querySelectorAll('.kw'));
    }
    el.style.opacity = 1;
    el.__wd.forEach(function (w, i) {
      MO.tw(o.dur || TOK.m, at + i * (o.gap || TOK.gap + 20), 'snap', function (e) {
        w.style.opacity = clamp01(e * 2.5);
        if (REDUCED) { w.style.opacity = e; return; }
        w.style.clipPath = 'inset(-20% -10% ' + '-30% -10%)';
        w.style.transform = e >= 1 ? '' : 'translateY(' + (0.5 * (1 - e)).toFixed(3) + 'em) skewY(' + (5 * (1 - e)).toFixed(2) + 'deg)';
      });
    });
  };
  MO.wordsSet = function (el, on) { MO.split(el); [].forEach.call(el.querySelectorAll('.kw'), function (w) { w.style.opacity = on ? 1 : 0; w.style.transform = ''; }); el.style.opacity = 1; };
  // 카드 뒤집기 (.fi 안에 .f 앞면 · .b 뒷면)
  MO.flip = function (fi, at, dur) {
    return MO.tw(dur || TOK.m + 80, at, 'linear', function (e, t) {
      if (REDUCED) { fi.style.transform = t >= 1 ? 'rotateY(180deg)' : ''; return; }
      var k = EZ.inout(t), lift = Math.sin(Math.PI * t);
      fi.style.transform = 'translateZ(' + (lift * 80).toFixed(1) + 'px) rotateY(' + (180 * k).toFixed(2) + 'deg)';
    });
  };
  // 돌며 모이기: 부품들이 가운데(cx, cy)를 돌아 안쪽으로 모였다가 제자리로 (끼워지는 느낌)
  MO.gather = function (parts, cx, cy, at, o) {
    o = o || {};
    parts.forEach(function (p, i) {
      var px = p.offsetLeft + p.offsetWidth / 2 - cx, py = p.offsetTop + p.offsetHeight / 2 - cy;
      MO.tw(o.dur || TOK.l - 140, at + i * (o.gap || TOK.gap / 3), 'linear', function (e, t) {
        if (REDUCED || t >= 1) { p.style.transform = ''; return; }
        var pull = Math.sin(Math.PI * EZ.out(t)) * (o.pull || 0.22), th = (o.turn || 0.5) * Math.sin(Math.PI * t);
        var x = px * (1 - pull), y = py * (1 - pull);
        var rx = x * Math.cos(th) - y * Math.sin(th), ry = x * Math.sin(th) + y * Math.cos(th);
        p.style.transform = 'translate(' + (rx - px).toFixed(1) + 'px,' + (ry - py).toFixed(1) + 'px) scale(' + (1 - pull * 0.6).toFixed(3) + ')';
      });
    });
  };
  // SVG 선 그리기 (pathLength="1")
  MO.draw = function (el, at, dur, ease) {
    return MO.tw(dur || TOK.m, at, ease || 'out', function (e) { el.style.strokeDashoffset = (1 - e).toFixed(4); });
  };
  function q(s, sel) { return s.querySelector(sel); }
  function qa(s, sel) { return [].slice.call(s.querySelectorAll(sel)); }
  // 장에 들어올 때: 앞으로 오면 움직이고, 뒤로 오거나(←) 바로 그 단계로 뛰면 끝 모습으로
  var V3DIR = 1;
  function v3hd(s, at, instant) {
    var k = q(s, '.hd .kicker'), h = q(s, '.hd h2');
    if (instant) { if (k) { k.style.opacity = 1; k.style.clipPath = ''; k.style.transform = ''; } if (h) MO.wipeSet(h, true); return; }
    if (k) MO.reveal(k, at);
    if (h) MO.wipe(h, at + TOK.xs);
  }

  /* 1 표지: 머리글 → 제목 낱말이 차례로 올라오고 → 강조 줄 → 한 줄 → 이름 (3D 카드는 장면 쪽에서 통통) */
  FX.v3cover = {
    enter: function (s, st) {
      var h1 = q(s, 'h1'), rule = q(s, '.m-rule'), tag = q(s, '.tag'), who = q(s, '.who'), inst = V3DIR < 0;
      var L = TOK.lead;   // 3D 카드가 먼저 통통 내려앉고(장면 쪽 COVER_IN), 글자가 같은 박자로 따라와요
      v3hd(s, L, inst);
      if (inst) { MO.wordsSet(h1, true); [rule, tag, who].forEach(function (e) { show(e, true); }); return; }
      MO.words(h1, L + TOK.xs + TOK.gap);
      MO.tw(TOK.s, L + TOK.m, 'snap', function (e) { rule.style.transform = 'scaleX(' + e.toFixed(4) + ')'; });
      MO.snap(tag, L + TOK.m + TOK.gap);
      MO.snap(who, L + TOK.m + 2 * TOK.gap);
    }
  };
  /* 2 여기저기서: 제목 가림막 → 알림 카드 여덟 장이 위에서 탁탁 (격자 순서대로) */
  FX.v3pour = {
    enter: function (s) {
      var inst = V3DIR < 0, nt = qa(s, '.nt');
      v3hd(s, 60, inst);
      if (inst) { nt.forEach(function (e) { show(e, true); }); return; }
      nt.forEach(function (e, i) { MO.snap(e, TOK.m + i * TOK.gap, { dy: TOK.big, s: 0.92 }); });
    }
  };
  /* 3 진입장벽: 생각 풍선이 꼬리 쪽에서 통통 (클릭 1~3) → 클릭 4: 가운데로 옮겨 붙으며 벽돌로, 「진입장벽」 도장 */
  FX.v3wall = {
    bubble: function (b, on) { b.style.left = ''; b.style.width = ''; b.style.borderRadius = ''; b.style.justifyContent = ''; q(b, '.mortar').style.opacity = 0; show(b, on); },
    brick: function (b) { b.style.left = '362px'; b.style.width = '940px'; b.style.borderRadius = '14px'; b.style.justifyContent = 'center'; q(b, '.mortar').style.opacity = 1; show(b, true); },
    set: function (s, st) {
      var bs = qa(s, '.tb'), tag = q(s, '.wtag3');
      bs.forEach(function (b, i) { if (st >= 4) FX.v3wall.brick(b); else FX.v3wall.bubble(b, st >= i + 1); });
      tag.style.opacity = st >= 4 ? 1 : 0; tag.style.transform = '';
    },
    enter: function (s, st) {
      FX.v3wall.set(s, st);
      v3hd(s, 60, V3DIR < 0 || st > 0);
    },
    step: function (s, st, dir) {
      MO.stop();
      v3hd(s, 0, true);
      if (dir === -1) { FX.v3wall.set(s, st); return; }
      var bs = qa(s, '.tb'), tag = q(s, '.wtag3'), wall = q(s, '.wall3');
      if (st <= 3) { FX.v3wall.set(s, st - 1); MO.spring(bs[st - 1], 0, { s: 0.25, r: -6, origin: '8% 100%', bouncy: true, dur: TOK.l - 80 }); return; }
      FX.v3wall.set(s, 3);
      bs.forEach(function (b, i) {
        var l0 = b.offsetLeft, w0 = b.offsetWidth, m = q(b, '.mortar');
        b.style.justifyContent = 'center';
        MO.tw(TOK.s + 100, i * TOK.gap, 'linear', function (e, t) {
          var k = EZ.snap(t);
          b.style.left = lerp(l0, 362, k).toFixed(1) + 'px'; b.style.width = lerp(w0, 940, k).toFixed(1) + 'px';
          b.style.borderRadius = lerp(56, 14, k).toFixed(1) + 'px ' + lerp(56, 14, k).toFixed(1) + 'px ' + lerp(56, 14, k).toFixed(1) + 'px 14px';
          m.style.opacity = k.toFixed(3);
          b.style.transform = t >= 1 ? '' : 'translateY(' + (-34 * (1 - EZ.fall(t))).toFixed(1) + 'px)';
        });
      });
      MO.stamp(tag, 2 * TOK.gap + TOK.s, { s: 1.3 });
      MO.shake(wall, 2 * TOK.gap + TOK.s + TOK.s - 60, 7);
    }
  };
  /* 4 옛날 이야기: (같은 자리의 벽) 금이 그려지고 → 벽돌이 무게 있게 떨어지고 → 제목 가림막
     클릭 1: 의심 카드가 탁 들어와서 뒤집히면 답 / 클릭 2: 「하나만」 한 줄, 낱말이 쾅 */
  FX.v3crack = {
    set: function (s, st) {
      var wall = q(s, '.wall3'), fc = q(s, '.fc'), fi = q(s, '.fi'), one = q(s, '.one');
      wall.style.opacity = 0;
      v3hd(s, 0, true);
      show(fc, st >= 1); fi.style.transform = st >= 1 ? 'rotateY(180deg)' : '';
      show(one, st >= 2); q(one, 'em').style.transform = '';
    },
    enter: function (s, st) {
      var wall = q(s, '.wall3'), bs = qa(s, '.tb'), tag = q(s, '.wtag3'), path = q(s, '.cracks3 path'), k = q(s, '.hd .kicker'), h = q(s, '.hd h2');
      bs.forEach(function (b) { b.style.transform = ''; b.style.opacity = ''; });
      tag.style.transform = ''; tag.style.opacity = '';
      path.style.strokeDashoffset = 1; q(s, '.cracks3').style.opacity = '';
      if (V3DIR < 0 || st > 0 || REDUCED) { FX.v3crack.set(s, st); if (REDUCED && !(V3DIR < 0 || st > 0)) { wall.style.opacity = 0; } return; }
      wall.style.opacity = 1;
      show(q(s, '.fc'), false); q(s, '.fi').style.transform = ''; show(q(s, '.one'), false);
      k.style.opacity = 0; MO.wipeSet(h, false);
      MO.draw(path, TOK.s, TOK.m - TOK.xs, 'snap');
      MO.shake(wall, TOK.s, 5);
      var rot = [-16, 12, -8], dx = [-90, 70, -30];
      bs.concat([tag]).forEach(function (b, i) {
        MO.tw(TOK.l - TOK.xs, TOK.s + TOK.m - 80 + i * TOK.gap, 'linear', function (e, t) {
          var f = EZ.fall(t);
          b.style.transform = 'translate(' + ((dx[i] || 0) * t).toFixed(1) + 'px,' + (720 * f).toFixed(1) + 'px) rotate(' + ((rot[i] || 6) * t).toFixed(2) + 'deg)';
          b.style.opacity = (1 - clamp01((t - 0.55) / 0.45)).toFixed(3);
        });
      });
      MO.tw(1, TOK.s + TOK.m - 80 + 3 * TOK.gap + TOK.l, 'linear', function (e) { if (e >= 1) wall.style.opacity = 0; });
      MO.tw(TOK.xs, TOK.s + TOK.m - 80, 'out', function (e) { q(s, '.cracks3').style.opacity = 1 - e; });
      MO.reveal(k, TOK.s + TOK.m + TOK.s + TOK.gap);
      MO.wipe(h, TOK.s + TOK.m + TOK.s + TOK.gap + TOK.xs);
    },
    step: function (s, st, dir) {
      MO.stop();
      FX.v3crack.set(s, dir === -1 ? st : st - 1);
      if (dir === -1) return;
      if (st === 1) {
        var fc = q(s, '.fc'), fi = q(s, '.fi');
        MO.snap(fc, 0, { dx: -TOK.big, dy: 0 });
        MO.flip(fi, TOK.s + TOK.gap);
      } else if (st === 2) {
        var one = q(s, '.one'), em = q(one, 'em');
        MO.snap(one, 0);
        MO.stamp(em, TOK.s - TOK.gap + 30, { s: 1.45 });
      }
    }
  };
  /* 6 하네스의 유래: 사진이 천천히 다가가고(26초 한 번) · 제목 가림막 → 표시 점 탁 → 줄이 위로 그려짐 → 이름표 → 뜻 한 줄 + 밑줄 */
  FX.v3horse = {
    enter: function (s) {
      var kb = q(s, '.kb'), pin = q(s, '.pin'), dot = q(pin, 'i'), lead = q(pin, 'u'), lab = q(pin, 'b'), mean = q(s, '.mean'), p = q(mean, 'p');
      var ul = q(p, 'u');
      if (!ul) { ul = document.createElement('u'); p.appendChild(ul); }
      var inst = V3DIR < 0 || REDUCED;
      MO.tw(26000, 0, 'linear', function (e, t) {
        var k = 1 - Math.pow(1 - t, 2.2);
        kb.style.transform = 'scale(' + lerp(1.02, 1.13, k).toFixed(4) + ') translate3d(' + lerp(1.2, -1.4, k).toFixed(3) + '%,' + lerp(0.6, -0.8, k).toFixed(3) + '%,0)';
      });
      if (REDUCED) kb.style.transform = 'scale(1.08)';
      v3hd(s, TOK.gap, inst);
      if (inst) { [dot, lead, lab, mean].forEach(function (e) { show(e, true); }); ul.style.transform = 'scaleX(1)'; return; }
      var B = TOK.gap + TOK.m;   // 머리글이 끝나는 박자에서 표시 → 줄 → 이름표 → 뜻 한 줄이 같은 간격(TOK.s)으로 이어져요
      MO.stamp(dot, B, { s: 2.2 });
      lead.style.transformOrigin = '50% 100%';
      MO.tw(TOK.s, B + TOK.s, 'snap', function (e) { lead.style.opacity = 1; lead.style.transform = 'scaleY(' + e.toFixed(4) + ')'; });
      MO.tw(TOK.s + 100, B + 2 * TOK.s, 'out', function (e) { lab.style.opacity = 1; lab.style.clipPath = 'inset(0 ' + ((1 - e) * 100).toFixed(2) + '% 0 0)'; if (e >= 1) lab.style.clipPath = ''; });
      MO.snap(mean, B + 3 * TOK.s + TOK.xs);
      MO.tw(TOK.m - 100, B + 4 * TOK.s + TOK.xs, 'inout', function (e) { ul.style.transform = 'scaleX(' + e.toFixed(4) + ')'; });
    }
  };
  /* 7 식당들도: 식당 셋이 탁탁 → 요리사가 통통 → 클릭마다 도구가 요리사에게서 통통 튀어나와 자리 (선이 따라 그려져요)
     「없음」은 탁 + 떨림(판정) · 설명 줄은 위로 빠지고 새 줄이 탁 · 클릭 5: 둘레 고리(하네스)가 돌며 감기고 도구가 한 번 모였다 풀려요 → 「하네스를 끼워」 글자 움직임 */
  FX.v3hx = {
    prep: function (s) {
      qa(s, '.hxcore').forEach(function (core) {
        var g = q(core, '.ln'), cx = core.offsetWidth / 2, cy = core.offsetHeight / 2;
        while (g.firstChild) g.removeChild(g.firstChild);
        qa(core, '.hc').forEach(function (c) {
          c.style.transform = '';
          var fx = c.offsetLeft + c.offsetWidth / 2 - cx, fy = c.offsetTop + c.offsetHeight / 2 - cy;
          var ln = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          ln.setAttribute('x1', cx); ln.setAttribute('y1', cy); ln.setAttribute('x2', cx + fx); ln.setAttribute('y2', cy + fy);
          ln.setAttribute('pathLength', '1'); ln.style.strokeDasharray = 1; g.appendChild(ln);
          c.__g = { fx: fx, fy: fy, ln: ln };
        });
      });
    },
    set: function (s, st) {
      qa(s, '.hc').forEach(function (c) { var on = st >= +c.getAttribute('data-s'); show(c, on); c.__g.ln.style.strokeDashoffset = on ? 0 : 1; });
      qa(s, '.hxcap p').forEach(function (p) { show(p, +p.getAttribute('data-c') === st); });
      qa(s, '.strap').forEach(function (e) { e.style.strokeDashoffset = st >= 5 ? 0 : 1; });
      qa(s, '.spin').forEach(function (g) { g.setAttribute('transform', ''); });
      var pu = q(s, '.hxpunch'); show(pu, st >= 5); show(q(pu, '.p1'), true); show(q(pu, '.p2'), true); MO.kinSet(q(pu, '.m-kin'), st >= 5);
    },
    enter: function (s, st) {
      FX.v3hx.prep(s);
      var inst = V3DIR < 0 || st > 0;
      FX.v3hx.set(s, st);
      v3hd(s, 60, inst);
      var apps = qa(s, '.hxapp'), brains = qa(s, '.brain'), orb = qa(s, '.o1');
      if (inst) { apps.concat(brains).forEach(function (e) { show(e, true); }); orb.forEach(function (e) { e.style.opacity = 1; }); return; }
      var B = TOK.gap + TOK.m - TOK.gap;
      apps.forEach(function (a, i) { MO.snap(a, B + i * TOK.gap, { dy: TOK.big }); });
      brains.forEach(function (b, i) { MO.spring(b, B + TOK.s + i * TOK.gap, { s: 0.1, bouncy: true }); });
      orb.forEach(function (o, i) { MO.tw(TOK.m - TOK.xs, B + TOK.s + TOK.xs + i * TOK.gap, 'out', function (e) { o.style.opacity = e; }); });
      var cap = q(s, '.hxcap p[data-c="0"]'); MO.snap(cap, B + TOK.s + TOK.m + TOK.gap);
    },
    chip: function (c, at, verdict) {
      var G = c.__g;
      if (verdict) {   // 「없음」: 제자리에 탁 + 떨림
        MO.stamp(c, at + TOK.xs, { s: 1.5 });
        MO.shake(c, at + TOK.xs + TOK.s, 9);
        MO.draw(G.ln, at, TOK.s, 'snap');
        return;
      }
      MO.tw(TOK.l - 120, at, 'linear', function (e, t) {
        var k = EZ.spring(t);
        c.style.opacity = clamp01(t * 6);
        c.style.transform = t >= 1 ? '' : 'translate(' + (-G.fx * (1 - k)).toFixed(1) + 'px,' + (-G.fy * (1 - k)).toFixed(1) + 'px) scale(' + lerp(0.3, 1, k).toFixed(3) + ')';
        G.ln.style.strokeDashoffset = (1 - EZ.out(clamp01(t * 1.6))).toFixed(4);
      });
    },
    step: function (s, st, dir) {
      MO.stop();
      v3hd(s, 0, true);
      if (dir === -1 || REDUCED) { FX.v3hx.set(s, st); return; }
      FX.v3hx.set(s, st - 1);
      // 설명 줄 바꾸기: 지난 줄은 위로 빠르게 빠지고(0.16초) 새 줄이 탁
      var old = q(s, '.hxcap p[data-c="' + (st - 1) + '"]'), nu = q(s, '.hxcap p[data-c="' + st + '"]');
      if (old) MO.tw(TOK.xs, 0, 'out', function (e) { old.style.opacity = 1 - e; old.style.transform = 'translateY(' + (-TOK.move * e).toFixed(1) + 'px)'; if (e >= 1) { old.style.opacity = 0; old.style.transform = ''; } });
      if (st <= 4) {
        var k = 0;
        qa(s, '.hc[data-s="' + st + '"]').forEach(function (c) { FX.v3hx.chip(c, (TOK.gap / 2) * (k % 2) + TOK.gap * Math.floor(k / 2), c.classList.contains('no')); k++; });
        if (nu) MO.snap(nu, TOK.xs + TOK.gap);
        return;
      }
      // 클릭 5: 고리가 돌며 감기고(0.9초) 도구들이 한 번 모였다 풀려요 → 두 줄
      qa(s, '.hxcore').forEach(function (core, i) {
        var strap = q(core, '.strap'), spin = q(core, '.spin');
        MO.tw(TOK.l, i * TOK.gap, 'linear', function (e, t) {
          var kk = EZ.inout(t);
          strap.style.strokeDashoffset = (1 - kk).toFixed(4);
          spin.setAttribute('transform', t >= 1 ? '' : 'rotate(' + (-200 * (1 - EZ.out(t))).toFixed(2) + ' 270 250)');
        });
        MO.gather(qa(core, '.hc'), core.offsetWidth / 2, core.offsetHeight / 2, TOK.gap + i * TOK.gap, { pull: 0.2, turn: 0.35 });
      });
      var pu = q(s, '.hxpunch'), p1 = q(pu, '.p1'), p2 = q(pu, '.p2'), kin = q(p2, '.m-kin');
      pu.style.opacity = 1;
      MO.kinSet(kin, false);
      MO.snap(p1, TOK.l);
      MO.snap(p2, TOK.l + TOK.s - TOK.gap);
      MO.kin(kin, TOK.l + TOK.s);
    }
  };
