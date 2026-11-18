/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME recycle-robot — recycling station with a robot host. The grimy factory gets cleaner as S.progress rises:
   litter disappears, a battery on the right charges, plants sprout; cheer = sparkles + fast belt, miss = red alarm + jammed belt,
   win = confetti + all lit, lose = dim. Static layers are cached in offscreen canvases; only small things move per frame. */
COMP.themes["recycle-robot"] = (function(){
  var BINC = ["#2fb36d", "#2f86e0", "#f2b01e", "#e2574c"];
  var base = null, grime = null, bw = 0, bh = 0, sp = 0, belt = 0, spin = 0, parts = [], beam = 0, seed = 7;
  var gears = [{ x: 1800, y: 250, r: 120, n: 12, s: 0.18 }, { x: 1640, y: 130, r: 70, n: 9, s: -0.3 }, { x: 110, y: 120, r: 80, n: 10, s: 0.24 }, { x: 70, y: 860, r: 64, n: 9, s: -0.26 }];
  var sparks = [], litter = [], i0;
  for (i0 = 0; i0 < 24; i0++) sparks.push({ x: (i0 * 331) % 1920, y: (i0 * 197) % 1080, v: 16 + (i0 * 7) % 24, p: i0 });
  /* litter: kind 0 paper 1 can 2 bottle 3 peel; zones = left strip, right strip floor, floor, top-left */
  var LP = [[40, 330, 0], [110, 430, 1], [50, 540, 2], [118, 640, 3], [46, 740, 1], [100, 250, 0], [1790, 960, 2], [1860, 985, 3], [1815, 1005, 0],
    [380, 990, 1], [820, 996, 0], [1210, 990, 3], [1560, 996, 2], [600, 985, 1]];
  for (i0 = 0; i0 < LP.length; i0++) litter.push({ x: LP[i0][0], y: LP[i0][1], k: LP[i0][2], thr: 0.05 + i0 * 0.066, rot: (i0 * 1.7) % 6.28 });

  function rr(c, x, y, w, h, r){ c.beginPath(); c.moveTo(x + r, y); c.lineTo(x + w - r, y); c.quadraticCurveTo(x + w, y, x + w, y + r); c.lineTo(x + w, y + h - r); c.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    c.lineTo(x + r, y + h); c.quadraticCurveTo(x, y + h, x, y + h - r); c.lineTo(x, y + r); c.quadraticCurveTo(x, y, x + r, y); c.closePath(); }
  function clamp(v, a, b){ return v < a ? a : (v > b ? b : v); }
  function mk(W, Hh){ var c = document.createElement("canvas"); c.width = W; c.height = Hh; return c; }
  function gearPath(c, r, n){ c.beginPath(); var k, a, q; for (k = 0; k < n * 4; k++){ a = k * Math.PI * 2 / (n * 4); q = (k % 4 < 2) ? r : r * 0.82; c.lineTo(Math.cos(a) * q, Math.sin(a) * q); } c.closePath(); }
  function rnd(){ seed = (seed * 16807) % 2147483647; return seed / 2147483647; }

  function buildBase(W, Hh){
    var c = mk(W, Hh), x = c.getContext("2d"), i, g = x.createLinearGradient(0, 0, 0, Hh);
    g.addColorStop(0, "#13293a"); g.addColorStop(1, "#24485a"); x.fillStyle = g; x.fillRect(0, 0, W, Hh);
    /* wall panel seams */
    x.strokeStyle = "rgba(255,255,255,.045)"; x.lineWidth = 4;
    for (i = 0; i < 9; i++){ x.beginPath(); x.moveTo(i * 240 + 60, 0); x.lineTo(i * 240 + 60, 1004); x.stroke(); }
    /* factory windows */
    for (i = 0; i < 4; i++){
      var wx = 250 + i * 430;
      x.fillStyle = "rgba(110,200,235,.09)"; x.fillRect(wx, 120, 300, 280);
      x.strokeStyle = "rgba(150,215,240,.16)"; x.lineWidth = 10; x.strokeRect(wx, 120, 300, 280);
      x.beginPath(); x.moveTo(wx + 150, 120); x.lineTo(wx + 150, 400); x.moveTo(wx, 260); x.lineTo(wx + 300, 260); x.stroke();
    }
    /* pipes */
    x.strokeStyle = "rgba(255,159,67,.20)"; x.lineWidth = 30; x.beginPath(); x.moveTo(0, 585); x.lineTo(W, 585); x.stroke();
    x.strokeStyle = "rgba(62,203,184,.20)"; x.lineWidth = 22; x.beginPath(); x.moveTo(1890, 0); x.lineTo(1890, 585); x.stroke();
    x.strokeStyle = "rgba(62,203,184,.14)"; x.beginPath(); x.moveTo(22, 140); x.lineTo(22, 1004); x.stroke();
    x.fillStyle = "rgba(255,255,255,.10)";
    for (i = 0; i < 6; i++){ x.fillRect(12, 200 + i * 130, 20, 12); x.fillRect(1880, 80 + i * 90 > 585 ? 80 : 80 + i * 90, 20, 12); }
    /* left strip: tall rack with crates */
    x.fillStyle = "rgba(10,22,32,.55)"; x.fillRect(0, 300, 160, 8); x.fillRect(0, 520, 160, 8); x.fillRect(0, 740, 160, 8);
    x.fillStyle = "rgba(255,255,255,.05)"; x.fillRect(0, 300, 6, 704);
    /* floor */
    x.fillStyle = "#18262f"; x.fillRect(0, 1004, W, 76);
    x.fillStyle = "rgba(255,255,255,.06)"; x.fillRect(0, 1004, W, 4);
    /* four small sorting bins on the floor (visible on title) */
    for (i = 0; i < 4; i++){
      var bx = 420 + i * 270, col = BINC[i], dk = "rgba(0,0,0,.35)"; x.globalAlpha = 0.5;
      x.fillStyle = col; rr(x, bx, 906, 150, 98, 12); x.fill(); x.fillStyle = dk; x.fillRect(bx - 6, 898, 162, 16);
      x.fillStyle = "rgba(255,255,255,.35)"; x.fillRect(bx + 20, 930, 8, 60); x.fillRect(bx + 122, 930, 8, 60); x.globalAlpha = 1;
    }
    /* floor caution stripes behind the belt */
    for (i = -80; i < W + 80; i += 90){ x.fillStyle = "rgba(242,176,30,.22)"; x.beginPath(); x.moveTo(i, 1070); x.lineTo(i + 45, 1070); x.lineTo(i + 20, 1080); x.lineTo(i - 25, 1080); x.closePath(); x.fill(); }
    /* battery frame (right strip) */
    x.fillStyle = "rgba(8,16,24,.7)"; rr(x, 1790, 250, 92, 700, 18); x.fill();
    x.strokeStyle = "#8a96a6"; x.lineWidth = 6; rr(x, 1790, 250, 92, 700, 18); x.stroke();
    x.fillStyle = "#8a96a6"; rr(x, 1816, 226, 40, 26, 8); x.fill();
    return c;
  }
  function buildGrime(W, Hh){
    var c = mk(W, Hh), x = c.getContext("2d"), i, g, px, py, pr;
    seed = 11;
    for (i = 0; i < 34; i++){
      px = rnd() * W; py = rnd() * 1000; pr = 60 + rnd() * 160;
      /* keep most grime near the edges where it can be seen */
      if (px > 260 && px < 1660 && rnd() < 0.6) px = rnd() < 0.5 ? rnd() * 240 : 1680 + rnd() * 240;
      g = x.createRadialGradient(px, py, 4, px, py, pr); g.addColorStop(0, "rgba(54,40,22,.55)"); g.addColorStop(1, "rgba(54,40,22,0)");
      x.fillStyle = g; x.fillRect(px - pr, py - pr, pr * 2, pr * 2);
    }
    for (i = 0; i < 9; i++){ /* drip streaks */
      px = (i < 5 ? 20 + i * 32 : 1780 + (i - 5) * 28); py = 150 + rnd() * 300;
      g = x.createLinearGradient(0, py, 0, py + 260); g.addColorStop(0, "rgba(40,30,18,.5)"); g.addColorStop(1, "rgba(40,30,18,0)");
      x.fillStyle = g; x.fillRect(px, py, 10, 260);
    }
    return c;
  }
  function drawLitter(c, L, a){
    c.save(); c.translate(L.x, L.y - (1 - a) * 46); c.rotate(L.rot * 0.2 + (1 - a) * 1.4); c.globalAlpha = a; var s = 0.7 + a * 0.3; c.scale(s, s);
    if (L.k === 0){ c.fillStyle = "#cfd6dd"; c.strokeStyle = "#7d8995"; c.lineWidth = 3; c.beginPath(); c.moveTo(-18, -4); c.lineTo(-6, -20); c.lineTo(12, -14); c.lineTo(20, 4); c.lineTo(6, 18); c.lineTo(-12, 14); c.closePath(); c.fill(); c.stroke(); c.beginPath(); c.moveTo(-6, -8); c.lineTo(8, 6); c.moveTo(-8, 4); c.lineTo(4, -10); c.stroke(); }
    else if (L.k === 1){ c.fillStyle = "#b9c3cf"; c.strokeStyle = "#5a6574"; c.lineWidth = 3; rr(c, -14, -22, 28, 44, 5); c.fill(); c.stroke(); c.fillStyle = "#e2574c"; c.fillRect(-14, -8, 28, 14); c.fillStyle = "#5a6574"; c.fillRect(-10, -26, 20, 5); }
    else if (L.k === 2){ c.fillStyle = "rgba(120,190,240,.85)"; c.strokeStyle = "#3d7fb4"; c.lineWidth = 3; rr(c, -11, -14, 22, 40, 8); c.fill(); c.stroke(); c.fillRect(-5, -28, 10, 16); c.fillStyle = "#f2b01e"; c.fillRect(-6, -32, 12, 6); }
    else { c.strokeStyle = "#a8801a"; c.lineWidth = 3; c.fillStyle = "#ffd84a"; c.beginPath(); c.moveTo(-22, 8); c.quadraticCurveTo(0, -26, 22, 6); c.quadraticCurveTo(0, -2, -22, 8); c.closePath(); c.fill(); c.stroke(); }
    c.restore();
  }
  function itemOnBelt(c, k, x, y){
    c.save(); c.translate(x, y); var col = BINC[k % 4];
    if (k % 3 === 0){ c.fillStyle = "#cfd6dd"; rr(c, -14, -24, 28, 40, 4); c.fill(); c.fillStyle = col; c.fillRect(-14, -12, 28, 12); }
    else if (k % 3 === 1){ c.fillStyle = "rgba(130,200,245,.9)"; rr(c, -10, -22, 20, 38, 7); c.fill(); c.fillRect(-5, -34, 10, 14); c.fillStyle = col; c.fillRect(-6, -37, 12, 5); }
    else { c.fillStyle = "#e8d4a2"; rr(c, -22, -16, 44, 32, 4); c.fill(); c.fillStyle = col; c.fillRect(-22, -4, 44, 8); }
    c.restore();
  }
  function star(c, x, y, r){ c.beginPath(); c.moveTo(x, y - r); c.quadraticCurveTo(x, y, x + r, y); c.quadraticCurveTo(x, y, x, y + r); c.quadraticCurveTo(x, y, x - r, y); c.quadraticCurveTo(x, y, x, y - r); c.fill(); }
  function spawn(x, y, n, cols, spread, up){
    for (var i = 0; i < n; i++){ var a = Math.random() * 6.283, v = (0.3 + Math.random()) * spread; parts.push({ x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - (up || 0), life: 0, max: 0.9 + Math.random() * 0.9, c: cols[i % cols.length], r: 4 + Math.random() * 7, g: 380 }); }
  }

  var theme = {
    paint: function(c, t, dt, W, Hh, TK, S){
      var i, g, a, j, calm = TK.motion === "calm";
      if (!base || bw !== W || bh !== Hh){ base = buildBase(W, Hh); grime = buildGrime(W, Hh); bw = W; bh = Hh; }
      sp += (clamp(S.progress, 0, 1) - sp) * Math.min(1, dt * 3);
      var cheer = S.cheer, miss = S.miss, lose = S.lose, win = S.win, jam = miss > 0.15 || lose > 0;
      c.drawImage(base, 0, 0);
      /* window daylight returns as the place gets clean */
      c.fillStyle = "rgba(255,244,200," + (0.04 + sp * 0.16 + cheer * 0.06) + ")";
      for (i = 0; i < 4; i++) c.fillRect(250 + i * 430, 120, 300, 280);
      /* grime fades away */
      c.globalAlpha = (1 - sp) * 0.9; c.drawImage(grime, 0, 0); c.globalAlpha = 1;
      /* gears */
      spin += dt * (jam ? 0.1 : 1 + cheer * 3) * (calm ? 0.5 : 1);
      for (i = 0; i < gears.length; i++){
        var gg = gears[i]; c.save(); c.translate(gg.x, gg.y); c.rotate(spin * gg.s * 1.0);
        gearPath(c, gg.r, gg.n); c.fillStyle = "rgba(255,255,255," + (0.05 + sp * 0.04) + ")"; c.fill();
        c.beginPath(); c.arc(0, 0, gg.r * 0.32, 0, 6.283); c.fillStyle = "rgba(0,0,0,.25)"; c.fill(); c.restore();
      }
      /* beacon on the left strip: orange sweep, green on cheer, red alarm on miss */
      beam += dt * (1.6 + cheer * 3 + miss * 6);
      var bx = 82, by = 205, bcol = miss > 0.05 ? "255,70,60" : (cheer > 0.05 ? "90,255,160" : "255,170,60"), ba = 0.35 + 0.35 * Math.abs(Math.sin(beam));
      g = c.createRadialGradient(bx, by, 4, bx, by, 110); g.addColorStop(0, "rgba(" + bcol + "," + (ba * 0.8) + ")"); g.addColorStop(1, "rgba(" + bcol + ",0)");
      c.fillStyle = g; c.fillRect(bx - 110, by - 110, 220, 220);
      c.fillStyle = "#2b3440"; c.fillRect(bx - 26, by + 14, 52, 14); c.fillStyle = "rgba(" + bcol + ",.95)"; c.beginPath(); c.arc(bx, by, 24, Math.PI, 0); c.lineTo(bx + 24, by + 14); c.lineTo(bx - 24, by + 14); c.closePath(); c.fill();
      c.save(); c.translate(bx, by); c.rotate(beam); c.fillStyle = "rgba(" + bcol + ",.10)"; c.beginPath(); c.moveTo(0, 0); c.lineTo(-90, -230); c.lineTo(90, -230); c.closePath(); c.fill(); c.restore();
      /* floating dust sparks */
      for (i = 0; i < sparks.length; i++){
        var s = sparks[i]; s.y -= s.v * dt * (0.4 + cheer); if (s.y < 0) s.y = Hh;
        c.globalAlpha = (0.12 + 0.2 * Math.abs(Math.sin(t * 2 + s.p))) * (0.5 + sp); c.fillStyle = sp > 0.5 ? "#9ff7d6" : "#ffd23f"; c.fillRect(s.x, s.y, 4, 4);
      }
      c.globalAlpha = 1;
      /* litter disappears one by one */
      for (i = 0; i < litter.length; i++){ a = clamp(1 - (sp - litter[i].thr) * 14, 0, 1); if (a > 0.01) drawLitter(c, litter[i], a); }
      /* battery charge (right strip) */
      var n = 10, lit = sp * n, sx = 1802, sw = 68, segH = 54, gap = 8, top = 250 + 700 - 14;
      for (i = 0; i < n; i++){
        var f = clamp(lit - i, 0, 1), sy = top - (i + 1) * (segH + gap) + gap;
        c.fillStyle = "rgba(255,255,255,.07)"; rr(c, sx, sy, sw, segH, 8); c.fill();
        if (f > 0){
          c.globalAlpha = 0.4 + 0.6 * f; c.fillStyle = i < 3 ? "#ffb02e" : (i < 6 ? "#c9f06a" : "#7cf7c8"); rr(c, sx, sy, sw, segH, 8); c.fill();
          c.globalAlpha = 0.25 * f; c.fillStyle = "#fff"; c.fillRect(sx + 8, sy + 6, sw - 16, 10); c.globalAlpha = 1;
        }
      }
      if (lit > 0.1){
        var gy = top - clamp(lit, 0, n) * (segH + gap); g = c.createRadialGradient(sx + 34, gy, 4, sx + 34, gy, 90 + cheer * 60); g.addColorStop(0, "rgba(124,247,200," + (0.35 + cheer * 0.4) + ")"); g.addColorStop(1, "rgba(124,247,200,0)");
        c.fillStyle = g; c.fillRect(sx - 60, gy - 150, 190, 300);
      }
      c.fillStyle = "#ffd23f"; c.beginPath(); c.moveTo(1846, 540); c.lineTo(1824, 576); c.lineTo(1840, 576); c.lineTo(1830, 610); c.lineTo(1860, 568); c.lineTo(1844, 568); c.closePath(); c.globalAlpha = sp > 0.02 ? 0.9 : 0.25; c.fill(); c.globalAlpha = 1;
      /* plants sprout when it is clean */
      var pl = [[1760, 1002, 0.35], [140, 1002, 0.6], [1700, 1002, 0.85]];
      for (i = 0; i < pl.length; i++){
        var gr = clamp((sp - pl[i][2]) * 6, 0, 1); if (gr <= 0) continue;
        c.save(); c.translate(pl[i][0], pl[i][1]); c.scale(gr, gr); c.fillStyle = "#c4602a"; c.beginPath(); c.moveTo(-18, 0); c.lineTo(18, 0); c.lineTo(13, -26); c.lineTo(-13, -26); c.closePath(); c.fill();
        c.fillStyle = "#3fae6d"; for (j = -1; j <= 1; j++){ c.beginPath(); c.ellipse(j * 14, -44 - (j === 0 ? 8 : 0), 8, 20, j * 0.5, 0, 6.283); c.fill(); } c.restore();
      }
      /* conveyor belt along the bottom */
      belt += dt * (jam ? 0 : (70 + cheer * 260)) * (calm ? 0.6 : 1);
      c.fillStyle = "#2b3440"; rr(c, 0, 1012, W, 52, 14); c.fill(); c.strokeStyle = "#11161d"; c.lineWidth = 4; rr(c, 0, 1012, W, 52, 14); c.stroke();
      c.strokeStyle = "rgba(255,255,255,.14)"; c.lineWidth = 6; c.beginPath();
      for (i = -2; i < W / 50 + 2; i++){ var xx = i * 50 + (belt % 50); c.moveTo(xx, 1018); c.lineTo(xx + 14, 1058); } c.stroke();
      c.fillStyle = "#5b6675"; for (i = 0; i < 16; i++){ c.beginPath(); c.arc(40 + i * 120, 1070, 9, 0, 6.283); c.fill(); }
      for (i = 0; i < 8; i++){ var ix = ((i * 260 + belt) % (W + 260)) - 130, jit = jam ? Math.sin(t * 40 + i) * 3 : 0; itemOnBelt(c, i, ix + jit, 1012); }
      /* red alarm edge when a miss happens */
      if (miss > 0.02){
        a = Math.min(0.5, miss * 0.45) * (0.6 + 0.4 * Math.sin(t * 18));
        g = c.createLinearGradient(0, 0, 220, 0); g.addColorStop(0, "rgba(255,50,40," + a + ")"); g.addColorStop(1, "rgba(255,50,40,0)"); c.fillStyle = g; c.fillRect(0, 0, 220, Hh);
        g = c.createLinearGradient(W, 0, W - 220, 0); g.addColorStop(0, "rgba(255,50,40," + a + ")"); g.addColorStop(1, "rgba(255,50,40,0)"); c.fillStyle = g; c.fillRect(W - 220, 0, 220, Hh);
      }
      /* cheer glints along the clean edges */
      if (sp > 0.05){
        c.fillStyle = "rgba(255,255,255,.9)";
        for (i = 0; i < 7; i++){
          var tw = Math.abs(Math.sin(t * 1.4 + i * 1.9)); if (tw < 0.55) continue;
          var gx = i % 2 ? 1790 + (i * 37) % 100 : 20 + (i * 53) % 130, gy2 = 260 + (i * 211) % 640; c.globalAlpha = (tw - 0.5) * 2 * sp; star(c, gx, gy2, 14 + tw * 12);
        }
        c.globalAlpha = 1;
      }
      /* particles */
      for (i = parts.length - 1; i >= 0; i--){
        var p = parts[i]; p.life += dt; if (p.life > p.max){ parts.splice(i, 1); continue; }
        p.vy += p.g * dt; p.x += p.vx * dt; p.y += p.vy * dt;
        c.globalAlpha = 1 - p.life / p.max; c.fillStyle = p.c; c.fillRect(p.x, p.y, p.r, p.r);
      }
      c.globalAlpha = 1;
      if (win > 0 && !calm && Math.random() < dt * 14) spawn(Math.random() * W, -10, 1, ["#ffd23f", "#7cf7c8", "#ff9f43", "#ffffff"], 40, -40);
      if (lose > 0){ c.fillStyle = "rgba(8,12,20," + (0.38 * lose) + ")"; c.fillRect(0, 0, W, Hh); }
    },
    host: {
      name: "로봇",
      lines: {
        title: ["삐빅! 분리수거 시작!", "같이 정리해요!"], start: ["공장 가동!", "배터리를 채워요!"],
        correct: ["분류 완료!", "배터리 충전!", "깔끔해졌어요!"], wrong: ["삐빅! 다시 생각해요", "이 통이 아니에요"],
        win: ["배터리 100%!", "출동 준비 끝!"], lose: ["배터리가 모자라요", "다음엔 해내요!"]
      },
      svg: function(TK){
        function face(m){
          var scr = m === "sad" ? "#ffb3a7" : "#7cf7c8", eye, mouth, chest = m === "sad" ? "#ff8a7a" : (m === "happy" ? "#5dff9d" : "#ffd23f");
          if (m === "happy") eye = '<path d="M80 96 q14 -20 28 0 M132 96 q14 -20 28 0" stroke="' + scr + '" stroke-width="9" fill="none" stroke-linecap="round"/>';
          else if (m === "sad") eye = '<path d="M80 78 l24 8 M160 78 l-24 8" stroke="' + scr + '" stroke-width="7" stroke-linecap="round"/><rect x="84" y="92" width="20" height="14" rx="6" fill="' + scr + '"/><rect x="136" y="92" width="20" height="14" rx="6" fill="' + scr + '"/>';
          else if (m === "wow") eye = '<circle cx="94" cy="88" r="15" fill="' + scr + '"/><circle cx="146" cy="88" r="15" fill="' + scr + '"/><circle cx="99" cy="83" r="5" fill="#0f2233"/><circle cx="151" cy="83" r="5" fill="#0f2233"/>';
          else eye = '<rect x="84" y="72" width="20" height="30" rx="9" fill="' + scr + '"/><rect x="136" y="72" width="20" height="30" rx="9" fill="' + scr + '"/>';
          if (m === "happy") mouth = '<path d="M100 108 q20 16 40 0" stroke="' + scr + '" stroke-width="7" fill="none" stroke-linecap="round"/>';
          else if (m === "sad") mouth = '<path d="M104 118 q16 -10 32 0" stroke="' + scr + '" stroke-width="7" fill="none" stroke-linecap="round"/>';
          else if (m === "wow") mouth = '<ellipse cx="120" cy="114" rx="8" ry="9" fill="' + scr + '"/>';
          else mouth = '<rect x="106" y="110" width="28" height="7" rx="3.5" fill="' + scr + '"/>';
          return '<g class="f f-' + m + '">' + eye + mouth + '<path d="M124 176 l-18 26 h14 l-6 20 l24 -30 h-14 l8 -16z" fill="' + chest + '"/></g>';
        }
        return '<svg viewBox="0 0 300 440" width="300" height="440"><g transform="translate(6,52) scale(1.2)">' +
          '<ellipse cx="120" cy="292" rx="88" ry="8" fill="rgba(0,0,0,.3)"/>' +
          '<rect x="44" y="246" width="152" height="40" rx="20" fill="#2b3440" stroke="#11161d" stroke-width="6"/>' +
          '<circle cx="70" cy="266" r="10" fill="#8a96a6"/><circle cx="120" cy="266" r="10" fill="#8a96a6"/><circle cx="170" cy="266" r="10" fill="#8a96a6"/>' +
          '<path d="M58 182 Q22 196 24 234" stroke="#11161d" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M58 182 Q22 196 24 234" stroke="#9aa7b8" stroke-width="11" fill="none" stroke-linecap="round"/>' +
          '<path d="M10 236 q14 22 30 0" stroke="#11161d" stroke-width="9" fill="none" stroke-linecap="round"/>' +
          '<path d="M182 182 Q220 166 222 128" stroke="#11161d" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M182 182 Q220 166 222 128" stroke="#9aa7b8" stroke-width="11" fill="none" stroke-linecap="round"/>' +
          '<path d="M206 126 q16 -24 32 0" stroke="#11161d" stroke-width="9" fill="none" stroke-linecap="round"/>' +
          '<rect x="52" y="150" width="136" height="104" rx="24" fill="#ff9f43" stroke="#7a3d0c" stroke-width="7"/>' +
          '<rect x="80" y="170" width="80" height="58" rx="12" fill="#1c2a3b" stroke="#7a3d0c" stroke-width="4"/>' +
          '<circle cx="66" cy="240" r="5" fill="#7a3d0c"/><circle cx="174" cy="240" r="5" fill="#7a3d0c"/>' +
          '<rect x="104" y="132" width="32" height="24" fill="#5b6675" stroke="#11161d" stroke-width="5"/>' +
          '<rect x="16" y="66" width="20" height="42" rx="7" fill="#5b6675" stroke="#11161d" stroke-width="5"/><rect x="204" y="66" width="20" height="42" rx="7" fill="#5b6675" stroke="#11161d" stroke-width="5"/>' +
          '<rect x="30" y="34" width="180" height="106" rx="32" fill="#3ecbb8" stroke="#145e57" stroke-width="7"/>' +
          '<rect x="52" y="54" width="136" height="74" rx="22" fill="#0f2233"/>' +
          face("idle") + face("happy") + face("sad") + face("wow") +
          '<line x1="120" y1="34" x2="120" y2="12" stroke="#11161d" stroke-width="6"/><circle cx="120" cy="11" r="10" fill="#ff5a8a" stroke="#11161d" stroke-width="4"/></g></svg>';
      }
    },
    onReact: function(kind, S){
      if (kind === "correct"){ var y = 936 - S.progress * 640; spawn(1836, clamp(y, 300, 930), 16, ["#7cf7c8", "#ffd23f", "#ffffff"], 260, 120); }
      else if (kind === "wrong"){ spawn(82, 205, 14, ["#ff6a5f", "#ffb02e"], 280, 60); }
      else if (kind === "win"){ spawn(960, 540, 60, ["#ffd23f", "#7cf7c8", "#ff9f43", "#ffffff"], 700, 300); }
    }
  };
  return theme;
})();
