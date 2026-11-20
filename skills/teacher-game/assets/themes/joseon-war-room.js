/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME joseon-war-room — 조선 수군 작전실. progress builds the turtle ship part by part, misses bring the enemy fleet closer,
   cheer lights lanterns, win = dawn + fireworks, lose = dim + smoke. Works with every mechanic (reads only COMP.S). */
COMP.themes["joseon-war-room"] = (function(){
  var TAU = 6.2832, TX = 1560, base = null, fg = null, P = 0, Mi = 0, Wn = 0, Ls = 0, pop = 0, lastParts = 0, fw = [], fwT = 0, smoke = [];
  var stars = []; (function(){ for (var i = 0; i < 90; i++) stars.push({ x: Math.random() * 1920, y: Math.random() * 520, s: Math.random() * 2 + 1, p: Math.random() * 6 }); })();
  var HZ = 650, TABLE = 900;
  function mk(w, h){ var c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
  function clamp(v, a, b){ return v < a ? a : (v > b ? b : v); }
  function ease(p){ p = clamp(p, 0, 1); return p * p * (3 - 2 * p); }
  function lg(c, y0, y1, a, b){ var g = c.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, a); g.addColorStop(1, b); return g; }

  /* ---- art (ported from the escape-room skin: enemy ship, turtle ship in 6 parts, waves) ---- */
  function enemy(c, x, y, s, a){
    c.save(); c.translate(x, y); c.scale(s, s); c.globalAlpha = a;
    c.fillStyle = "#3b2418"; c.beginPath(); c.moveTo(-64, -16); c.lineTo(-44, 8); c.lineTo(52, 8); c.lineTo(72, -20); c.closePath(); c.fill();
    c.fillStyle = "#6e4a2e"; c.fillRect(-52, -26, 112, 10);
    c.fillStyle = "#2a1810"; c.fillRect(-2, -92, 5, 68);
    c.fillStyle = "#e7ddc2"; c.fillRect(-34, -88, 68, 48);
    c.fillStyle = "#2a1810"; c.fillRect(-34, -66, 68, 5);
    c.fillStyle = "#b53a2a"; c.beginPath(); c.moveTo(3, -92); c.lineTo(30, -84); c.lineTo(3, -76); c.fill();
    c.restore();
  }
  function turtle(c, x, y, s, parts, t, glow){
    c.save(); c.translate(x, y); c.scale(s, s); c.lineJoin = "round";
    function st(on){ if (on){ c.setLineDash([]); c.lineWidth = 6; c.strokeStyle = "#140d08"; } else { c.setLineDash([10, 8]); c.lineWidth = 4; c.strokeStyle = "rgba(255,235,180,.7)"; } }
    var on = [], q, j; for (q = 0; q < 6; q++) on.push(parts > q);
    if (glow > 0){ var rg = c.createRadialGradient(0, -60, 20, 0, -60, 280); rg.addColorStop(0, "rgba(255,220,120," + (0.5 * glow) + ")"); rg.addColorStop(1, "rgba(255,200,80,0)"); c.fillStyle = rg; c.fillRect(-300, -300, 600, 360); }
    for (j = 0; j < 6; j++){ var ox = -95 + j * 38; c.setLineDash(on[4] ? [] : [10, 8]); c.beginPath(); c.moveTo(ox, -10); c.lineTo(ox - 26 + Math.sin(t * 3 + j) * (on[4] ? 5 : 0), 30); c.lineWidth = on[4] ? 8 : 4; c.strokeStyle = on[4] ? "#5a3a1e" : "rgba(255,235,180,.7)"; c.stroke(); }
    st(on[0]); c.beginPath(); c.moveTo(-150, -34); c.lineTo(-118, 2); c.lineTo(120, 2); c.lineTo(152, -34); c.closePath();
    if (on[0]){ c.fillStyle = "#7a4a26"; c.fill(); } c.stroke();
    st(on[1]); c.beginPath(); c.moveTo(-128, -34); c.quadraticCurveTo(0, -150, 128, -34); c.closePath();
    if (on[1]){ c.fillStyle = "#4b6b4a"; c.fill(); } c.stroke();
    if (on[1]){ c.strokeStyle = "rgba(20,13,8,.5)"; c.lineWidth = 3; c.setLineDash([]); for (j = -3; j <= 3; j++){ c.beginPath(); c.moveTo(j * 30, -36); c.lineTo(j * 22, -86 + Math.abs(j) * 8); c.stroke(); } }
    if (on[2]){ c.fillStyle = "#e4e4ec"; c.strokeStyle = "#140d08"; c.lineWidth = 2; c.setLineDash([]); for (j = -4; j <= 4; j++){ var px = j * 26, py = -34 - 58 * (1 - (px / 128) * (px / 128)); c.beginPath(); c.moveTo(px - 7, py + 3); c.lineTo(px, py - 24); c.lineTo(px + 7, py + 3); c.fill(); c.stroke(); } }
    else { st(false); for (j = -4; j <= 4; j += 2){ var qx = j * 26, qy = -34 - 58 * (1 - (qx / 128) * (qx / 128)); c.beginPath(); c.moveTo(qx - 7, qy + 3); c.lineTo(qx, qy - 24); c.lineTo(qx + 7, qy + 3); c.stroke(); } }
    st(on[3]); c.beginPath(); c.ellipse(-170, -54, 32, 24, 0, 0, TAU);
    if (on[3]){ c.fillStyle = "#c8402f"; c.fill(); } c.stroke();
    if (on[3]){ c.fillStyle = "#fff"; c.beginPath(); c.arc(-160, -62, 7, 0, TAU); c.fill(); c.fillStyle = "#140d08"; c.beginPath(); c.arc(-158, -62, 3.5, 0, TAU); c.fill();
      c.fillStyle = "#ffd84d"; c.beginPath(); c.moveTo(-170, -76); c.lineTo(-160, -98); c.lineTo(-150, -76); c.fill(); c.beginPath(); c.moveTo(-190, -70); c.lineTo(-196, -92); c.lineTo(-178, -74); c.fill();
      c.fillStyle = "rgba(255,190,80,.85)"; c.beginPath(); c.arc(-204, -50, 6 + Math.sin(t * 6) * 2, 0, TAU); c.fill(); }
    st(on[5]); c.beginPath(); c.moveTo(0, -92); c.lineTo(0, -190); c.stroke();
    if (on[5]){ c.fillStyle = "#c8402f"; c.beginPath(); c.moveTo(0, -190); c.lineTo(-76 + Math.sin(t * 4) * 6, -174); c.lineTo(0, -158); c.closePath(); c.fill(); }
    c.setLineDash([]); c.restore();
  }
  function wave(c, y0, W, t, k, col){
    c.fillStyle = col; c.beginPath(); c.moveTo(0, y0 + 220);
    for (var x = 0; x <= W; x += 40) c.lineTo(x, y0 + Math.sin(x / 110 + t * (1 + k * 0.3) + k) * 8);
    c.lineTo(W, y0 + 220); c.fill();
  }
  function pavilion(c, x, y, s){
    c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = "#0b1627";
    c.fillRect(-60, -50, 120, 50); c.fillRect(-70, -4, 140, 8);
    c.beginPath(); c.moveTo(-96, -50); c.quadraticCurveTo(-60, -44, -40, -84); c.lineTo(40, -84); c.quadraticCurveTo(60, -44, 96, -50); c.quadraticCurveTo(0, -62, -96, -50); c.fill();
    c.fillRect(-4, -100, 8, 18); c.restore();
  }

  /* ---- cached static layers ---- */
  function build(TK){
    base = mk(1920, 1080); var c = base.getContext("2d"), i;
    c.fillStyle = lg(c, 0, HZ, "#070d22", "#2b4378"); c.fillRect(0, 0, 1920, HZ);
    c.fillStyle = "#fff"; for (i = 0; i < stars.length; i++){ c.globalAlpha = 0.35 + 0.4 * (stars[i].p % 1); c.fillRect(stars[i].x, stars[i].y, stars[i].s, stars[i].s); } c.globalAlpha = 1;
    var mg = c.createRadialGradient(1640, 190, 10, 1640, 190, 200); mg.addColorStop(0, "rgba(255,240,190,.5)"); mg.addColorStop(1, "rgba(255,240,190,0)"); c.fillStyle = mg; c.fillRect(1400, 0, 500, 420);
    c.fillStyle = "#ffe9a8"; c.beginPath(); c.arc(1640, 190, 54, 0, TAU); c.fill(); c.fillStyle = "rgba(210,180,110,.5)"; c.beginPath(); c.arc(1622, 176, 12, 0, TAU); c.arc(1660, 208, 9, 0, TAU); c.fill();
    c.fillStyle = "#0e1a30"; c.beginPath(); c.moveTo(0, HZ); c.lineTo(0, 560); c.lineTo(160, 590); c.lineTo(340, 548); c.lineTo(520, 596); c.lineTo(700, HZ); c.fill();
    c.beginPath(); c.moveTo(1260, HZ); c.lineTo(1460, 590); c.lineTo(1640, 556); c.lineTo(1780, 576); c.lineTo(1920, 548); c.lineTo(1920, HZ); c.fill();
    pavilion(c, 1780, 598, 1.0);
    c.fillStyle = lg(c, HZ, 1080, "#17407a", "#06182f"); c.fillRect(0, HZ, 1920, 430);
    c.fillStyle = "rgba(255,240,190,.10)"; for (i = 0; i < 26; i++) c.fillRect(1520 + Math.sin(i * 1.7) * 90, HZ + 6 + i * 9, 120 - i * 3, 3);
    fg = mk(1920, 1080); c = fg.getContext("2d");
    c.fillStyle = lg(c, TABLE, 1080, "#4a2f1a", "#1c110a"); c.fillRect(0, TABLE, 1920, 1080 - TABLE);
    c.fillStyle = "rgba(0,0,0,.28)"; for (i = 0; i < 17; i++) c.fillRect(i * 120 + 40, TABLE + 8, 4, 1080 - TABLE);
    c.fillStyle = "#c9a24a"; c.fillRect(0, TABLE - 4, 1920, 8); c.fillStyle = "#6b4423"; c.fillRect(0, TABLE + 4, 1920, 6);
    c.fillStyle = "rgba(255,230,160,.12)"; c.fillRect(0, TABLE + 10, 1920, 3);
    /* the map on the table */
    c.save(); c.shadowColor = "rgba(0,0,0,.5)"; c.shadowBlur = 0; c.fillStyle = "#e3cf9a";
    c.beginPath(); c.moveTo(352, 940); c.lineTo(1216, 940); c.lineTo(1250, 1066); c.lineTo(318, 1066); c.closePath(); c.fill(); c.restore();
    c.fillStyle = "#cfe0d2"; c.beginPath(); c.moveTo(362, 944); c.lineTo(1206, 944); c.lineTo(1236, 1062); c.lineTo(332, 1062); c.closePath(); c.fill();
    c.fillStyle = "#a8bf90"; c.beginPath(); c.moveTo(362, 944); c.lineTo(470, 944); c.quadraticCurveTo(450, 990, 410, 1010); c.quadraticCurveTo(360, 1030, 340, 1060); c.lineTo(332, 1062); c.closePath(); c.fill();
    c.beginPath(); c.moveTo(1206, 944); c.lineTo(1090, 944); c.quadraticCurveTo(1120, 996, 1170, 1004); c.quadraticCurveTo(1220, 1020, 1236, 1062); c.closePath(); c.fill();
    c.strokeStyle = "rgba(90,130,170,.5)"; c.lineWidth = 2; for (i = 0; i < 6; i++){ c.beginPath(); c.moveTo(560 + i * 90, 962 + (i % 2) * 14); c.quadraticCurveTo(590 + i * 90, 950, 620 + i * 90, 962 + (i % 2) * 14); c.stroke(); }
    c.setLineDash([12, 10]); c.strokeStyle = "#7a4a26"; c.lineWidth = 4; c.beginPath(); c.moveTo(430, 1010); c.quadraticCurveTo(780, 960, 1140, 1010); c.stroke(); c.setLineDash([]);
    c.fillStyle = "#8a2a1f"; c.beginPath(); c.arc(1180, 1008, 11, 0, TAU); c.fill(); c.fillStyle = "#ffe29a"; c.fillRect(1176, 1004, 8, 8);
    /* inkstone + brush + seal */
    c.fillStyle = "#111"; c.fillRect(1380, 960, 120, 72); c.fillStyle = "#2a2a30"; c.fillRect(1388, 968, 104, 40); c.fillStyle = "#0a0a0c"; c.beginPath(); c.ellipse(1440, 988, 38, 16, 0, 0, TAU); c.fill();
    c.strokeStyle = "#5a3a1e"; c.lineWidth = 8; c.beginPath(); c.moveTo(1520, 1040); c.lineTo(1640, 970); c.stroke(); c.strokeStyle = "#111"; c.lineWidth = 8; c.beginPath(); c.moveTo(1640, 970); c.lineTo(1670, 952); c.stroke();
    c.fillStyle = "#b53a2a"; c.fillRect(1700, 990, 54, 54); c.fillStyle = "#e8c25e"; c.fillRect(1712, 1002, 30, 30);
    c.fillStyle = "rgba(255,255,255,.18)"; c.fillRect(0, 1074, 1920, 6);
  }

  function burst(x, y, col){ for (var i = 0; i < 26; i++){ var a = i / 26 * TAU, v = 160 + Math.random() * 190; fw.push({ x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, l: 1.5, c: col }); } }
  var COLS = ["#ffd84d", "#ff7a5a", "#8fe0ff", "#ffffff", "#b8ff8a"];

  function paint(c, t, dt, W, Hh, TK, S){
    if (!base) build(TK);
    var k = TK.motion === "calm" ? 0.4 : 1, d = dt > 0.1 ? 0.1 : (dt || 0.016);
    P += (S.progress - P) * Math.min(1, d * 3);
    Mi += (clamp(S.misses / 6, 0, 1) - Mi) * Math.min(1, d * 1.6);
    Wn += (S.win - Wn) * Math.min(1, d * 1.2); Ls += (S.lose - Ls) * Math.min(1, d * 1.5);
    var parts = S.progress >= 0.999 ? 6 : Math.ceil(S.progress * 6 - 0.0001);
    if (parts > lastParts) pop = 1; lastParts = parts; pop = Math.max(0, pop - d * 1.4);
    var i, thr = Math.min(1, Mi + Ls * 0.5);
    c.drawImage(base, 0, 0);
    /* twinkle + dawn */
    c.fillStyle = "#fff"; for (i = 0; i < 18; i++){ var s = stars[i]; c.globalAlpha = (0.2 + 0.7 * Math.abs(Math.sin(t * 1.4 + s.p))) * (1 - Wn); c.fillRect(s.x, s.y, 3, 3); } c.globalAlpha = 1;
    if (Wn > 0.01){
      c.globalAlpha = Wn * 0.85; c.fillStyle = lg(c, 0, HZ, "#27407a", "#f5a05e"); c.fillRect(0, 0, W, HZ); c.globalAlpha = 1;
      var sy = HZ - 30 * ease(Wn) , sr = 120; c.save(); c.beginPath(); c.rect(0, 0, W, HZ); c.clip();
      c.fillStyle = "rgba(255,225,150," + (0.42 * Wn) + ")"; c.beginPath(); c.arc(960, HZ + 100 - 190 * ease(Wn), sr, 0, TAU); c.fill();
      c.fillStyle = "rgba(255,230,150," + (0.07 * Wn) + ")"; for (i = 0; i < 9; i++){ var ra = -Math.PI + i * Math.PI / 8 + 0.2; c.beginPath(); c.moveTo(960, HZ + 100 - 190 * ease(Wn)); c.arc(960, HZ + 100 - 190 * ease(Wn), 1500, ra, ra + 0.09); c.closePath(); c.fill(); }
      c.restore();
    }
    /* far fleet on the horizon (sinks on win) */
    for (i = 0; i < 5; i++) enemy(c, 880 + i * 120 + (i % 2) * 20, HZ + 22 + Math.sin(t * 1.2 + i) * 2 + Wn * 40, 0.3, 0.55 * (1 - Wn));
    wave(c, 700, W, t * k, 0, "rgba(120,180,255,.10)"); wave(c, 760, W, t * k, 1, "rgba(120,180,255,.12)");
    /* near enemy fleet: distance follows misses */
    var scl = (0.8 + thr * 0.75), wl = 810 + thr * 70 + 4, front = 280 + thr * 1030 + S.miss * 26, ea = 1 - Wn;
    for (i = 3; i >= 0; i--){ var ex = front - i * 215 * scl * 0.8 - (i % 2) * 24; if (ex < -130) continue;
      enemy(c, ex, wl + (i % 3) * 8 + Math.sin(t * 1.6 * k + i) * 4 + Wn * 60 + Ls * (i % 2 ? 6 : -4), scl, ea); }
    if (S.miss > 0.05 && Ls < 0.5){ c.fillStyle = "rgba(255,170,60," + (S.miss * 0.9) + ")"; c.beginPath(); c.arc(front + 80 * scl, wl - 40 * scl, 26 * S.miss + 6, 0, TAU); c.fill(); }
    /* turtle ship */
    var sn = NG.sceneName || ""; TX += (((sn === "title" || sn === "countdown") ? 1130 : 1560) - TX) * Math.min(1, d * 2.5); var tx = TX, ty = 884 + Math.sin(t * 1.3 * k) * 4 + Ls * 26, ts = 1.0 + 0.12 * ease(Wn) + 0.04 * pop;
    c.save(); if (Ls > 0.05){ c.translate(tx, ty); c.rotate(0.1 * Ls); c.translate(-tx, -ty); }
    turtle(c, tx, ty, ts, parts, t, Math.max(pop * 0.7, S.cheer * 0.7, Wn * 0.6));
    c.restore();
    if (S.cheer > 0.02){ c.strokeStyle = "rgba(255,226,130," + S.cheer + ")"; c.lineWidth = 5; for (i = 0; i < 8; i++){ var ca = i * TAU / 8 + t, cr = 90 + (1 - S.cheer) * 170; c.beginPath(); c.moveTo(tx - 20 + Math.cos(ca) * cr, ty - 90 + Math.sin(ca) * cr * 0.6); c.lineTo(tx - 20 + Math.cos(ca) * (cr + 20), ty - 90 + Math.sin(ca) * (cr + 20) * 0.6); c.stroke(); } }
    wave(c, 862, W, t * k + 1, 2, "rgba(10,40,80,.55)"); wave(c, 880, W, t * k + 2, 1, "rgba(8,28,56,.9)");
    c.drawImage(fg, 0, 0);
    /* map table markers: enemy fleet, port, 6 build seals */
    var mx = 430 + thr * 710, my = 1012 - Math.sin(thr * 3.14) * 28;
    c.fillStyle = "#b53a2a"; c.fillRect(mx - 2, my - 36, 4, 36); c.beginPath(); c.moveTo(mx + 2, my - 36); c.lineTo(mx + 34, my - 28); c.lineTo(mx + 2, my - 20); c.fill();
    c.fillStyle = "#2a1810"; c.beginPath(); c.moveTo(mx - 22, my); c.lineTo(mx - 14, my + 10); c.lineTo(mx + 14, my + 10); c.lineTo(mx + 22, my); c.fill();
    for (i = 0; i < 6; i++){ var on = parts > i; c.beginPath(); c.arc(610 + i * 62, 1048, 13, 0, TAU); c.fillStyle = on ? "#c8402f" : "rgba(60,40,20,.25)"; c.fill(); c.lineWidth = 3; c.strokeStyle = on ? "#7a1d12" : "rgba(60,40,20,.5)"; c.stroke(); if (on){ c.fillStyle = "#ffe29a"; c.fillRect(605 + i * 62, 1043, 10, 10); } }
    /* fireworks + smoke */
    if (Wn > 0.3){ fwT -= d; if (fwT <= 0){ fwT = 0.55 / k; var left = Math.random() < 0.5; burst(left ? 80 + Math.random() * 320 : 1520 + Math.random() * 340, 130 + Math.random() * 420, COLS[(Math.random() * COLS.length) | 0]); } }
    for (i = fw.length - 1; i >= 0; i--){ var f = fw[i]; f.l -= d; if (f.l <= 0){ fw.splice(i, 1); continue; } f.x += f.vx * d; f.y += f.vy * d; f.vy += 160 * d; f.vx *= 0.985; c.globalAlpha = clamp(f.l, 0, 1); c.fillStyle = f.c; c.fillRect(f.x - 3, f.y - 3, 6, 6); } c.globalAlpha = 1;
    if (Ls > 0.2){ if (Math.random() < d * 14) smoke.push({ x: 1380 + Math.random() * 300, y: 800, l: 3 }); }
    for (i = smoke.length - 1; i >= 0; i--){ var m = smoke[i]; m.l -= d; if (m.l <= 0){ smoke.splice(i, 1); continue; } m.y -= 60 * d; m.x += 12 * d; c.globalAlpha = clamp(m.l / 3, 0, 1) * 0.5; c.fillStyle = "#555a60"; c.beginPath(); c.arc(m.x, m.y, 30 + (3 - m.l) * 18, 0, TAU); c.fill(); } c.globalAlpha = 1;
    /* danger vignette + lose dim */
    var al = Math.max(S.miss * 0.38, Mi > 0.6 ? (Mi - 0.6) * 0.3 * (0.6 + 0.4 * Math.sin(t * 5)) : 0);
    if (al > 0.01){ var vg = c.createRadialGradient(W / 2, Hh / 2, 380, W / 2, Hh / 2, 1150); vg.addColorStop(0, "rgba(200,30,20,0)"); vg.addColorStop(1, "rgba(200,30,20," + al + ")"); c.fillStyle = vg; c.fillRect(0, 0, W, Hh); }
    if (Ls > 0.01){ c.fillStyle = "rgba(6,8,20," + (0.5 * Ls) + ")"; c.fillRect(0, 0, W, Hh); }
  }

  /* ---- host: 수군 장교 (ported from the legacy officer) ---- */
  function face(m){
    var ink = "#1b1b2f";
    if (m === "happy") return '<path d="M70 94 q10 -14 20 0 M110 94 q10 -14 20 0" stroke="' + ink + '" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M82 118 q18 22 36 0z" fill="#8a2a1f" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>';
    if (m === "sad") return '<circle cx="80" cy="94" r="7" fill="' + ink + '"/><circle cx="120" cy="94" r="7" fill="' + ink + '"/><path d="M68 76 l22 6 M132 76 l-22 6" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/><path d="M86 126 q14 -10 28 0" stroke="' + ink + '" stroke-width="5" fill="none" stroke-linecap="round"/>';
    if (m === "wow") return '<circle cx="80" cy="94" r="10" fill="#fff" stroke="' + ink + '" stroke-width="4"/><circle cx="120" cy="94" r="10" fill="#fff" stroke="' + ink + '" stroke-width="4"/><circle cx="82" cy="95" r="5" fill="' + ink + '"/><circle cx="122" cy="95" r="5" fill="' + ink + '"/><ellipse cx="100" cy="124" rx="9" ry="11" fill="#8a2a1f" stroke="' + ink + '" stroke-width="5"/>';
    return '<circle cx="80" cy="94" r="6" fill="' + ink + '"/><circle cx="120" cy="94" r="6" fill="' + ink + '"/><path d="M86 122 q14 12 28 0" stroke="' + ink + '" stroke-width="5" fill="none" stroke-linecap="round"/>';
  }
  function officer(m){
    return '<g transform="translate(0 60) scale(1.5)"><ellipse cx="100" cy="240" rx="72" ry="9" fill="rgba(0,0,0,.3)"/>' +
      '<path d="M38 238 q0 -92 62 -98 q62 6 62 98z" fill="#27406b" stroke="#111d36" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M76 142 l24 34 24 -34z" fill="#c8402f" stroke="#111d36" stroke-width="5" stroke-linejoin="round"/>' +
      '<rect x="60" y="196" width="80" height="18" rx="4" fill="#c9a24a" stroke="#111d36" stroke-width="5"/>' +
      '<circle cx="100" cy="98" r="52" fill="#f3c9a0" stroke="#111d36" stroke-width="7"/>' + face(m) +
      '<path d="M84 112 q16 -8 32 0" stroke="#3a2a22" stroke-width="5" fill="none" stroke-linecap="round"/>' +
      '<ellipse cx="100" cy="62" rx="82" ry="17" fill="#2b2b36" stroke="#111d36" stroke-width="6"/>' +
      '<path d="M50 62 q0 -54 50 -54 q50 0 50 54z" fill="#3a3a4a" stroke="#111d36" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M100 8 q-12 -30 14 -40 q-6 20 10 26" fill="#c8402f" stroke="#7a1d12" stroke-width="4" stroke-linejoin="round"/></g>';
  }
  function hostSvg(){
    var out = '<svg viewBox="0 0 300 440" width="300" height="440" xmlns="http://www.w3.org/2000/svg">', ms = ["idle", "happy", "sad", "wow"];
    for (var i = 0; i < 4; i++) out += '<g class="f f-' + ms[i] + '">' + officer(ms[i]) + "</g>";
    return out + "</svg>";
  }

  function deco(){
    return '<style>.jw-p{position:absolute;top:0;bottom:0;width:46px;background:linear-gradient(90deg,#1c110a,#5a3a1e 45%,#24160c);box-shadow:0 0 30px rgba(0,0,0,.6)}' +
      '.jw-p.l{left:0}.jw-p.r{right:0}.jw-p:before{content:"";position:absolute;left:-4px;right:-4px;top:0;height:22px;background:#c9a24a;border-bottom:6px solid #7b5a14}' +
      '.jw-p:after{content:"";position:absolute;left:-4px;right:-4px;bottom:178px;height:14px;background:#c9a24a;opacity:.85}' +
      '.jw-lamp{position:absolute;top:120px;width:48px;height:74px;border-radius:24px 24px 18px 18px;background:radial-gradient(ellipse at 50% 55%,#ffd27a 0,#e0533a 60%,#8a2a1f 100%);border:4px solid #3a1d10;box-shadow:0 0 40px 10px rgba(255,150,60,.55);animation:jwfl 2.4s ease-in-out infinite}' +
      '.jw-lamp:before{content:"";position:absolute;left:19px;top:-122px;width:4px;height:120px;background:#3a1d10}.jw-lamp.l{left:56px}.jw-lamp.r{right:56px;animation-delay:-1.1s}' +
      '.jw-lamp.hot{box-shadow:0 0 60px 26px rgba(255,40,20,.8);filter:saturate(1.6)}.jw-lamp.glad{box-shadow:0 0 70px 30px rgba(255,230,120,.9)}' +
      '@keyframes jwfl{0%,100%{opacity:1}50%{opacity:.82}}</style><div class="jw-p l"></div><div class="jw-p r"></div><div class="jw-lamp l"></div><div class="jw-lamp r"></div>';
  }
  function sfx(){
    if (!NG.defineSfx) return;
    NG.defineSfx("jwDrum", function(){ NG.tone({ type: "sine", freq: 150, slide: -90, dur: 0.35, vol: 0.4, jitter: 0 }); NG.tone({ type: "noise", freq: 300, q: 0.8, dur: 0.12, vol: 0.14, filter: "lowpass" }); });
    NG.defineSfx("jwGong", function(){ [1, 2.4, 3.9].forEach(function(r, i){ NG.tone({ type: "sine", freq: 196 * r, dur: 1.8 - i * 0.4, vol: 0.28 / (i + 1), jitter: 0, attack: 0.01 }); }); });
  }
  function lamps(cls, ms){
    var e = document.querySelectorAll("#ts-deco .jw-lamp");
    for (var i = 0; i < e.length; i++){ e[i].classList.add(cls); (function(x){ setTimeout(function(){ x.classList.remove(cls); }, ms); })(e[i]); }
  }
  function onReact(kind){
    try {
      if (kind === "wrong"){ lamps("hot", 900); NG.sfx("jwDrum"); }
      else if (kind === "correct"){ lamps("glad", 700); }
      else if (kind === "win"){ lamps("glad", 4000); NG.sfx("jwGong"); }
      else if (kind === "lose"){ lamps("hot", 3000); NG.sfx("jwDrum"); }
      else if (kind === "start"){ NG.sfx("jwDrum"); }
    } catch (e) {}
  }
  return {
    paint: paint, deco: deco, sfx: sfx, onReact: onReact,
    host: { svg: hostSvg, name: "수군 장교", lines: {
      title: ["거북선을 지어 볼까?", "적선을 막아라!"], start: ["작전 개시!", "출항 준비!"],
      correct: ["좋아, 한 칸 완성!", "거북선이 자란다!", "훌륭하다!"], wrong: ["적선이 다가온다!", "정신 차려라!", "침착하게!"],
      win: ["대승리! 적 함대 격파!", "거북선, 출항!"], lose: ["포기하지 마라!", "다시 도전하자!"] } }
  };
})();
