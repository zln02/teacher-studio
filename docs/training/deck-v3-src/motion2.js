
  /* =====================================================================
     deck-v3 phase 2 (8~21장) · motion.js와 같은 토큰(TOK) · 같은 어휘(MO). build.py가 motion.js 바로 뒤에 붙여요
     ===================================================================== */
  var V3PREV = null;   // 바로 앞 장 (같은 머리글이 이어지면 움직이지 않고 그대로 둬요)
  // 바탕 빛: 장에 들어올 때 한 번만 천천히 제자리로 (TOK.l), 그다음엔 가만히
  MO.light = function (s) {
    MO.tw(TOK.l, 0, 'out', function (e) { s.style.setProperty('--ldx', (-90 * (1 - e)).toFixed(1) + 'px'); });
  };
  // 카드 뒤집어 들어오기: 옆으로 선 카드(−90°)가 돌아 정면에서 살짝 넘쳤다 멈춰요
  MO.flipIn = function (el, at) {
    el.style.transformOrigin = '50% 50%';
    return MO.tw(TOK.l - 80, at, 'linear', function (e, t) {
      el.style.opacity = t > 0.02 ? 1 : 0;
      if (REDUCED) { el.style.opacity = e; el.style.transform = ''; return; }
      el.style.transform = t >= 1 ? '' : 'rotateY(' + (-90 * (1 - EZ.spring(t))).toFixed(2) + 'deg)';
    });
  };
  // 돌며 모이기(흩어진 조각 → 한 줄): 조각마다 다른 자리 · 각도에서 돌아 들어와 제자리
  MO.assemble = function (parts, at) {
    parts.forEach(function (p, i) {
      var a = i * 2.39996, r = 220 + (i % 3) * 70, dx = Math.cos(a) * r, dy = Math.sin(a) * r * 0.6 - 120, rot = (i % 2 ? 1 : -1) * (160 + i * 25);
      MO.tw(TOK.l - 120, at + i * TOK.gap / 2, 'linear', function (e, t) {
        var k = EZ.inout(t), sp = EZ.spring(t);
        p.style.opacity = clamp01(t * 4);
        if (REDUCED || t >= 1) { p.style.transform = ''; return; }
        p.style.transform = 'translate(' + (dx * (1 - k)).toFixed(1) + 'px,' + (dy * (1 - k)).toFixed(1) + 'px) rotate(' + (rot * (1 - k)).toFixed(1) + 'deg) scale(' + lerp(0.6, 1, sp).toFixed(3) + ')';
      });
    });
  };

  /* 8 섹션: 제목 가림막 → V · S가 양쪽에서 탁 부딪힘(떨림 한 번) → 순서 막대가 차례로 서고 지금 구간에 줄이 그어져요 */
  FX.v3section = {
    enter: function (s) {
      var ag = q(s, '.agenda'), c = +s.getAttribute('data-agenda'), inst = V3DIR < 0;
      ag.innerHTML = AGENDA.map(function (a, i) { return '<div class="' + (i === c ? 'cur' : i < c ? 'done' : '') + '">' + a + (i === c ? '<u></u>' : '') + '</div>'; }).join('');
      var v = q(s, '.bigno .v'), sv = q(s, '.bigno .s'), items = qa(ag, 'div'), u = q(ag, 'u');
      v3hd(s, TOK.gap, inst);
      if (inst) { [v, sv].concat(items).forEach(function (e) { show(e, true); }); u.style.transform = 'scaleX(1)'; return; }
      MO.snap(v, TOK.s, { dx: -TOK.big * 4, dy: 0, dur: TOK.s });
      MO.snap(sv, TOK.s, { dx: TOK.big * 4, dy: 0, dur: TOK.s });
      MO.shake(q(s, '.bigno'), 2 * TOK.s, 10);
      items.forEach(function (e, i) { MO.snap(e, TOK.m + i * TOK.gap / 2, { dy: TOK.move }); });
      MO.tw(TOK.m - TOK.xs, TOK.m + AGENDA.length * TOK.gap / 2 + TOK.s, 'snap', function (e) { u.style.transform = 'scaleX(' + e.toFixed(4) + ')'; });
    }
  };

  /* 9~12 같은 부탁, 다른 결과: 머리글은 네 장에 걸쳐 그대로(앞 장도 같은 꼴이면 움직이지 않음) · 번호 탁 · 부탁 말풍선 통통
     클릭 1: 그냥 AI가 왼쪽에서 탁 / 클릭 2: 하네스 AI가 카드 뒤집기로 들어와요 */
  FX.v3cmp = {
    set: function (s, st) { show(q(s, '.shot.sb'), st >= 1); show(q(s, '.shot.h'), st >= 2); },
    enter: function (s, st) {
      var carry = V3PREV && V3PREV.classList.contains('cmp'), inst = V3DIR < 0 || st > 0;
      FX.v3cmp.set(s, st);
      v3hd(s, 0, carry || inst);
      var cno = q(s, '.cno'), ask = q(s, '.ask');
      if (inst) { show(cno, true); show(ask, true); return; }
      MO.stamp(cno, carry ? 0 : TOK.s, { s: 1.5 });
      MO.spring(ask, carry ? TOK.gap : TOK.s + TOK.gap, { s: 0.3, dx: -TOK.big, origin: '0% 50%' });
    },
    step: function (s, st, dir) {
      MO.stop();
      v3hd(s, 0, true); show(q(s, '.cno'), true); show(q(s, '.ask'), true);
      if (dir === -1) { FX.v3cmp.set(s, st); return; }
      FX.v3cmp.set(s, st - 1);
      if (st === 1) MO.snap(q(s, '.shot.sb'), 0, { dx: -TOK.big * 2, dy: 0, dur: TOK.m - TOK.xs });
      if (st === 2) MO.flipIn(q(s, '.shot.h'), 0);
    }
  };

  /* 13 김치볶음밥 그림책: 3D 로봇이 주인공. 글자는 3D 박자(data-at, ms)에 맞춰 따라와요 */
  FX.v3story = {
    set: function (s, st) {
      qa(s, '.ub, .kcp').forEach(function (e) { show(e, +e.getAttribute('data-c') === st); });
      qa(s, '.stamp').forEach(function (e) { show(e, st >= +e.getAttribute('data-k')); });
      var pu = q(s, '.punch'); show(pu, st >= 8); show(q(pu, '.p2'), true); MO.kinSet(q(pu, '.m-kin'), st >= 8);
      qa(pu, '.pi').forEach(function (e) { show(e, true); });
    },
    play: function (s, st, first) {
      var kc = q(s, '.kcp[data-c="' + st + '"]'), ub = q(s, '.ub[data-c="' + st + '"]');
      if (kc) MO.snap(kc, first ? TOK.lead : TOK.xs + TOK.gap, { dy: TOK.move });
      if (ub) MO.spring(ub, +ub.getAttribute('data-at') || 0, { s: 0.3, origin: '100% 100%', bouncy: true });
      qa(s, '.stamp[data-k="' + st + '"]').forEach(function (e) { MO.stamp(e, +e.getAttribute('data-at') || 0, { s: 1.7 }); });
      if (st === 8) {
        var pu = q(s, '.punch'), kin = q(pu, '.m-kin');
        MO.tw(TOK.s, 0, 'out', function (e) { pu.style.opacity = e; });
        MO.kinSet(kin, false);
        MO.kin(kin, TOK.s, { gap: TOK.gap / 2 });
        MO.snap(q(pu, '.p2'), TOK.s + TOK.m, { dy: TOK.move });
        qa(pu, '.pi').forEach(function (e, i) { MO.spring(e, TOK.s + TOK.m + TOK.s + i * TOK.gap * 2, { s: 0.2, bouncy: true }); });
      }
    },
    enter: function (s, st) {
      FX.v3story.set(s, st);
      if (V3DIR < 0 || st > 0) return;
      qa(s, '.ub, .kcp').forEach(function (e) { show(e, false); });
      FX.v3story.play(s, st, true);
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1) { FX.v3story.set(s, st); return; }
      var old = qa(s, '.ub[data-c="' + (st - 1) + '"], .kcp[data-c="' + (st - 1) + '"]');
      FX.v3story.set(s, st - 1);
      qa(s, '.ub, .kcp').forEach(function (e) { if (old.indexOf(e) < 0) show(e, false); });
      old.forEach(function (o) { MO.tw(TOK.xs, 0, 'out', function (e) { o.style.opacity = 1 - e; o.style.transform = 'translateY(' + (-TOK.move * e).toFixed(1) + 'px)'; if (e >= 1) { o.style.opacity = 0; o.style.transform = ''; } }); });
      FX.v3story.play(s, st, false);
    }
  };

  /* 14~19 · 21: 단계 하나에 [data-k="n"] 요소들이 data-m(움직임 이름)대로 들어와요. calm(실습 장)은 이동 거리를 줄이고 튀지 않아요 */
  function genSet(e, on) {
    var m = e.getAttribute('data-m');
    show(e, on);
    if (m === 'grow') q(e, '.bar').style.height = '';
    if (m === 'draw') { var p = q(e, 'path'); p.style.strokeDasharray = 1; p.style.strokeDashoffset = on ? 0 : 1; }
    if (m === 'tip') { MO.kinSet(q(e, 'h3'), on); [q(e, '.n'), q(e, 'p')].forEach(function (x) { show(x, true); }); }
    if (m === 'wipe') e.style.clipPath = '';
    qa(e, '.gcs i, .illust-slot, .lb, .ft').forEach(function (x) { show(x, true); });
  }
  function genPlay(s, e, at) {
    var m = e.getAttribute('data-m') || 'snap', calm = s.classList.contains('calm');
    if (m === 'snap') MO.snap(e, at, { dy: calm ? 14 : TOK.move });
    else if (m === 'fade') MO.tw(TOK.s, at, 'out', function (k) { e.style.opacity = k; });
    else if (m === 'spring') MO.spring(e, at, calm ? { s: 0.96, dy: 14 } : { s: 0.55, dy: TOK.big });
    else if (m === 'grow') {   // 막대가 아래에서 솟아 딱 멈춰요 (결과 = 탁)
      var bar = q(e, '.bar'), h1 = bar.offsetHeight || 300, lb = q(e, '.lb'), ft = q(e, '.ft');
      e.style.opacity = 1;
      MO.tw(TOK.m, at, 'snap', function (k) { bar.style.height = lerp(90, h1, k).toFixed(1) + 'px'; if (k >= 1) bar.style.height = ''; });
      [lb, ft].forEach(function (x, i) { MO.snap(x, at + TOK.s + i * TOK.gap); });
    }
    else if (m === 'draw') { e.style.opacity = 1; MO.draw(q(e, 'path'), at, TOK.m - TOK.xs, 'snap'); }
    else if (m === 'tip') {   // 줄이 탁 → 번호 도장 → 핵심 문장 글자 움직임 → 설명 탁
      var n = q(e, '.n'), h3 = q(e, 'h3'), p = q(e, 'p');
      MO.snap(e, at, { dx: -TOK.move, dy: 0 });
      MO.stamp(n, at + TOK.xs, { s: 1.8 });
      MO.kinSet(h3, false); MO.kin(h3, at + TOK.s);
      MO.snap(p, at + TOK.s + TOK.m, { dy: 14 });
    }
    else if (m === 'wipe') MO.reveal(e, at, TOK.m);
    var g = qa(e, '.gcs i');
    if (g.length) MO.assemble(g, at + TOK.s);
  }
  FX.v3gen = {
    set: function (s, st) { qa(s, '[data-k]').forEach(function (e) { genSet(e, st >= +e.getAttribute('data-k')); }); },
    enter: function (s, st) {
      FX.v3gen.set(s, st);
      v3hd(s, TOK.gap, V3DIR < 0 || st > 0);
      if (q(s, '[data-type]')) FX.install.enter(s);
    },
    step: function (s, st, dir) {
      MO.stop();
      v3hd(s, 0, true);
      if (dir === -1) { FX.v3gen.set(s, st); return; }
      FX.v3gen.set(s, st - 1);
      qa(s, '[data-k="' + st + '"]').forEach(function (e) { genPlay(s, e, +e.getAttribute('data-at') || 0); });
    }
  };

  /* 20 같이 쓰려고 준비했어요: 표지와 짝. 3D 카드가 먼저 돌며 내려앉고(TOK.lead) 글자가 같은 박자로 */
  FX.v3made = {
    enter: function (s) {
      var h1 = q(s, 'h1'), rule = q(s, '.m-rule'), sub = q(s, '.sub'), inst = V3DIR < 0, L = TOK.lead;
      v3hd(s, L, inst);
      if (inst) { MO.wordsSet(h1, true); var u0 = MO.kwu(h1); if (u0) u0.style.transform = 'scaleX(1)'; [rule, sub].forEach(function (e) { show(e, true); }); rule.style.transform = 'scaleX(1)'; return; }
      MO.words(h1, L + TOK.xs + TOK.gap); var u1 = MO.kwu(h1); if (u1) u1.style.transform = 'scaleX(0)'; MO.underline(h1, L + TOK.m + TOK.l);
      MO.tw(TOK.s, L + TOK.m + TOK.gap, 'snap', function (e) { rule.style.transform = 'scaleX(' + e.toFixed(4) + ')'; });
      MO.snap(sub, L + TOK.m + 2 * TOK.gap);
    }
  };

  /* 7 오늘의 비유 지도 → 식당들도: 처음 두 단계는 비유 지도(앞면 = 진짜), 클릭 1에 카드가 차례로 뒤집혀 비유(카드 뒤집기 = 전 → 후)
     클릭 2부터는 식당 장면(FX.v3hx)에 단계 −2로 넘겨요 */
  FX.v3map = {
    mapSet: function (s, st) {
      s.classList.toggle('map', st < 2);
      var hm = q(s, '.hd.hm'); show(hm, true); show(q(hm, '.kicker'), true); MO.wipeSet(q(hm, 'h2'), true);
      qa(s, '.amap .fc').forEach(function (c) { show(c, true); });
      qa(s, '.amap .fi').forEach(function (f) { f.style.transform = st >= 1 ? 'rotateY(180deg)' : ''; });
    },
    enter: function (s, st) {
      if (st >= 2) { s.classList.remove('map'); FX.v3hx.enter(s, st - 2); return; }
      s.classList.add('map');
      FX.v3hx.prep(s); FX.v3hx.set(s, 0);
      FX.v3map.mapSet(s, st);
      if (V3DIR < 0 || st > 0) return;
      var hm = q(s, '.hd.hm');
      MO.reveal(q(hm, '.kicker'), TOK.gap);
      MO.wipe(q(hm, 'h2'), TOK.gap + TOK.xs);
      qa(s, '.amap .fc').forEach(function (c, i) { MO.snap(c, TOK.m + i * TOK.gap, { dy: TOK.big }); });
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1) {
        if (st >= 2) { s.classList.remove('map'); FX.v3hx.step(s, st - 2, -1); }
        else FX.v3map.mapSet(s, st);
        return;
      }
      if (st === 1) {
        FX.v3map.mapSet(s, 0);
        qa(s, '.amap .fi').forEach(function (f, i) { MO.flip(f, i * TOK.gap * 2); });
      } else if (st === 2) {
        FX.v3map.mapSet(s, 1);
        var out = [q(s, '.hd.hm'), q(s, '.amap')];
        out.forEach(function (o) { MO.tw(TOK.xs, 0, 'out', function (e) { o.style.opacity = 1 - e; o.style.transform = 'translateY(' + (-TOK.move * e).toFixed(1) + 'px)'; if (e >= 1) { o.style.opacity = ''; o.style.transform = ''; } }); });
        MO.tw(1, TOK.xs, 'linear', function () {}, function () { s.classList.remove('map'); V3DIR = 1; FX.v3hx.enter(s, 0); });
      } else FX.v3hx.step(s, st - 2, dir);
    }
  };

  /* 19 실습 4 + 모둠 미션: (가) 두 화면 비교 → 클릭 1 (나) 미션 판 → 클릭 2~5 지금 단계 표시 (단계 칸은 마우스로도) */
  FX.v3duo = {
    set: function (s, st) {
      var A = st === 0;
      [q(s, '.hd.ha'), q(s, '.duoA')].forEach(function (e) { show(e, A); });
      [q(s, '.hd.hb'), q(s, '.board')].forEach(function (e) { show(e, !A); });
      MO.kinSet(q(s, '.order .m-kin'), !A);
      qa(s, '.hd .kicker, .board .seg, .board .seqbar i, .board .menu li, .board .menu .mh, .board .timer, .board .wait, .duoA .prompt, .duoA .screens').forEach(function (e) { show(e, true); });
      qa(s, '.hd h2').forEach(function (h) { MO.wipeSet(h, true); });
      FX.v3duo.mark(s, st, false);
    },
    mark: function (s, st, anim) {
      var cur = st - 1;
      qa(s, '.seg').forEach(function (g, i) { g.classList.toggle('cur', i === cur); g.classList.toggle('done', i < cur); });
      qa(s, '.seqbar i').forEach(function (b, i) { b.classList.toggle('done', i < cur); });
      if (anim && cur >= 0) MO.stamp(qa(s, '.seg')[cur], 0, { s: 1.18 });
    },
    enter: function (s, st) {
      qa(s, '.seg').forEach(function (g, i) { g.onclick = function (e) { e.stopPropagation(); go(slides.indexOf(s), i + 1, 1); }; });
      FX.v3duo.set(s, st);
      if (V3DIR < 0 || st > 0) return;
      v3hd(s, TOK.gap, false);
      MO.snap(q(s, '.duoA .prompt'), TOK.m, { dy: 14 });
      MO.snap(q(s, '.duoA .screens'), TOK.m + TOK.s, { dy: 14 });
    },
    step: function (s, st, dir) {
      MO.stop();
      if (dir === -1 || st > 1) { FX.v3duo.set(s, st); if (dir !== -1) FX.v3duo.mark(s, st, true); return; }
      // 클릭 1: (가)가 위로 빠지고 (나) 미션 판이 들어와요. 주문 한 줄은 글자 움직임(핵심 문장)
      FX.v3duo.set(s, 0);
      [q(s, '.hd.ha'), q(s, '.duoA')].forEach(function (o) { MO.tw(TOK.xs, 0, 'out', function (e) { o.style.opacity = 1 - e; o.style.transform = 'translateY(' + (-TOK.move * e).toFixed(1) + 'px)'; if (e >= 1) { o.style.opacity = 0; o.style.transform = ''; } }); });
      var hb = q(s, '.hd.hb'), bd = q(s, '.board');
      hb.style.opacity = 1; bd.style.opacity = 1;
      MO.reveal(q(hb, '.kicker'), TOK.xs);
      MO.wipe(q(hb, 'h2'), TOK.xs + TOK.gap);
      MO.kin(q(s, '.order .m-kin'), TOK.m, { gap: TOK.gap / 3 });
      var B = TOK.m + TOK.l;
      qa(s, '.seg').forEach(function (g, i) { MO.snap(g, B + i * TOK.gap / 2, { dy: 14 }); });
      qa(s, '.seqbar i').forEach(function (b, i) { MO.tw(TOK.s, B + i * TOK.gap / 2 + TOK.xs, 'snap', function (e) { b.style.opacity = 1; b.style.transform = 'scaleX(' + e.toFixed(4) + ')'; if (e >= 1) b.style.transform = ''; }); });
      MO.snap(q(s, '.menu .mh'), B + TOK.s, { dy: 14 });
      qa(s, '.menu li').forEach(function (l, i) { MO.snap(l, B + TOK.s + i * TOK.gap / 2, { dy: 14 }); });
      MO.snap(q(s, '.board .timer'), B + TOK.s, { dy: 14 });
      MO.snap(q(s, '.board .wait'), B + TOK.m + TOK.s, { dy: 14 });
      FX.v3duo.mark(s, 1, false);
      MO.stamp(qa(s, '.seg')[0], B + TOK.m, { s: 1.18 });
    }
  };
