/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME antidote-lab — 해독제 실험실. progress fills the antidote flask, misses spread alarm light + fog,
   cheer bubbles the flask, win = antidote spray clears the fog, lose = dark red lab. Works with every mechanic (reads only COMP.S). */
COMP.themes["antidote-lab"] = (function(){
  var TAU = 6.2832, base = null, cloudSpr = null, P = 0, Mi = 0, Wn = 0, Ls = 0, pop = 0, lastParts = 0, spray = [], spT = 0, bub = [], beat = [];
  var BENCH = 900;
  function mk(w, h){ var c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
  function clamp(v, a, b){ return v < a ? a : (v > b ? b : v); }
  function lg(c, y0, y1, a, b){ var g = c.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, a); g.addColorStop(1, b); return g; }

  /* ---- art (ported from the escape-room lab skin: flask, fog cloud, siren, lab room) ---- */
  function flask(c, x, y, s, p, t, ticks, lit){
    c.save(); c.translate(x, y); c.scale(s, s); c.lineJoin = "round";
    function body(){ c.beginPath(); c.moveTo(-22, -222); c.lineTo(-22, -150); c.lineTo(-96, -14); c.quadraticCurveTo(-102, 0, -84, 0); c.lineTo(84, 0); c.quadraticCurveTo(102, 0, 96, -14); c.lineTo(22, -150); c.lineTo(22, -222); c.closePath(); }
    if (p >= 0.999){ var rg = c.createRadialGradient(0, -80, 10, 0, -80, 210); rg.addColorStop(0, "rgba(120,255,180," + (0.45 + 0.15 * Math.sin(t * 4)) + ")"); rg.addColorStop(1, "rgba(120,255,180,0)"); c.fillStyle = rg; c.fillRect(-220, -300, 440, 340); }
    body(); c.fillStyle = "rgba(200,240,255,.14)"; c.fill();
    var level = clamp(p, 0, 1) * 196, b;
    if (level > 1){
      c.save(); body(); c.clip();
      var g = c.createLinearGradient(0, -level, 0, 0); g.addColorStop(0, "#9dffc8"); g.addColorStop(1, "#14b873"); c.fillStyle = g;
      c.beginPath(); c.moveTo(-110, 0);
      for (var xx = -110; xx <= 110; xx += 10) c.lineTo(xx, -level + Math.sin(xx / 14 + t * 5) * 3);
      c.lineTo(110, 0); c.closePath(); c.fill();
      c.fillStyle = "rgba(255,255,255,.7)";
      for (b = 0; b < 7; b++){ var by = -((t * 60 + b * 37) % Math.max(12, level)), bx = Math.sin(b * 2.1 + t) * 44 * (1 + by / 260); c.beginPath(); c.arc(bx, by, 3 + (b % 3), 0, TAU); c.fill(); }
      c.restore();
    }
    body(); c.strokeStyle = "#e9fbff"; c.lineWidth = 6; c.stroke();
    c.strokeStyle = "rgba(255,255,255,.5)"; c.lineWidth = 5; c.beginPath(); c.moveTo(-12, -210); c.lineTo(-12, -150); c.lineTo(-70, -40); c.stroke();
    for (var k = 1; k <= ticks; k++){ var hy = -k / ticks * 196, hx = hy > -150 ? 96 - 74 * (-hy / 150) : 22;
      c.strokeStyle = k <= lit ? "#ffd84d" : "rgba(233,251,255,.75)"; c.lineWidth = 5; c.beginPath(); c.moveTo(hx - 4, hy); c.lineTo(hx - 26, hy); c.stroke(); }
    c.fillStyle = "#a0673a"; c.strokeStyle = "#3b2414"; c.lineWidth = 5; c.fillRect(-26, -246, 52, 30); c.strokeRect(-26, -246, 52, 30);
    c.restore();
  }
  function cloudSprite(){
    var s = mk(300, 230), c = s.getContext("2d"), r = 100, x = 150, y = 120, i, q, px, py;
    var pts = [[-1, 0.15, 0.62], [-0.45, -0.25, 0.8], [0.25, -0.32, 0.86], [0.85, 0.05, 0.66], [0.05, 0.3, 0.8]];
    for (i = 0; i < pts.length; i++){ q = pts[i]; px = x + q[0] * r * 0.8; py = y + q[1] * r * 0.8; c.fillStyle = "#6f7f86"; c.beginPath(); c.arc(px, py + r * 0.06, q[2] * r * 0.8, 0, TAU); c.fill(); }
    for (i = 0; i < pts.length; i++){ q = pts[i]; px = x + q[0] * r * 0.8; py = y + q[1] * r * 0.8; c.fillStyle = "#a9b8bd"; c.beginPath(); c.arc(px - q[2] * r * 0.1, py - q[2] * r * 0.1, q[2] * r * 0.66, 0, TAU); c.fill(); }
    return s;
  }
  function siren(c, x, y, s, t, green, thr){
    c.save(); c.translate(x, y); c.scale(s, s);
    c.fillStyle = "#2b3a40"; c.fillRect(-26, 0, 52, 14);
    var on = green ? 1 : 0.5 + 0.5 * Math.abs(Math.sin(t * (2 + thr * 7)));
    c.fillStyle = green ? "rgba(90,255,140," + on + ")" : "rgba(255,60,40," + on + ")";
    c.beginPath(); c.arc(0, 0, 22, Math.PI, 0); c.fill();
    c.strokeStyle = "#11191c"; c.lineWidth = 4; c.stroke();
    c.fillStyle = "rgba(255,255,255,.6)"; c.beginPath(); c.arc(-8, -10, 5, 0, TAU); c.fill();
    c.restore();
  }

  function build(){
    base = mk(1920, 1080); var c = base.getContext("2d"), x, y, i;
    c.fillStyle = lg(c, 0, BENCH, "#071820", "#15404b"); c.fillRect(0, 0, 1920, BENCH);
    c.strokeStyle = "rgba(140,220,230,.08)"; c.lineWidth = 2;
    for (x = 0; x <= 1920; x += 96){ c.beginPath(); c.moveTo(x, 0); c.lineTo(x, BENCH); c.stroke(); }
    for (y = 0; y <= BENCH; y += 96){ c.beginPath(); c.moveTo(0, y); c.lineTo(1920, y); c.stroke(); }
    c.fillStyle = "rgba(140,220,230,.05)"; for (y = 6; y < BENCH; y += 96) for (x = ((y / 96) % 2) * 48; x < 1920; x += 96) if (((x + y) / 48) % 5 < 1) c.fillRect(x + 4, y + 4, 88, 88);
    /* pipe along the top wall with valves */
    c.fillStyle = "#2c4f5c"; c.fillRect(0, 124, 1920, 20); c.fillStyle = "rgba(255,255,255,.18)"; c.fillRect(0, 127, 1920, 4);
    for (i = 0; i < 7; i++){ var vx = 130 + i * 290; c.fillStyle = "#3d6c7c"; c.fillRect(vx - 14, 118, 28, 32); c.strokeStyle = "#0b1d24"; c.lineWidth = 3; c.strokeRect(vx - 14, 118, 28, 32);
      c.strokeStyle = "#e05a3a"; c.lineWidth = 5; c.beginPath(); c.arc(vx, 104, 13, 0, TAU); c.moveTo(vx - 13, 104); c.lineTo(vx + 13, 104); c.moveTo(vx, 91); c.lineTo(vx, 117); c.stroke(); }
    /* two shelves of bottles at the sides (above the cards) */
    var cols = ["#ff6b9a", "#6bd1ff", "#ffd84d", "#b48cff", "#7dffb2", "#ff9a3d"], sh = [190, 1290];
    for (var q = 0; q < 2; q++){
      c.fillStyle = "#3c5a66"; c.fillRect(sh[q], 206, 440, 10);
      for (i = 0; i < 6; i++){ var bx = sh[q] + 14 + i * 70, bh = 34 + ((i + q) % 3) * 12; c.fillStyle = "rgba(220,245,255,.25)"; c.fillRect(bx, 206 - bh, 36, bh); c.fillStyle = cols[(i + q * 2) % 6]; c.fillRect(bx + 3, 206 - bh * 0.55, 30, bh * 0.55 - 2); c.fillStyle = "#cfe6ee"; c.fillRect(bx + 8, 198 - bh, 20, 10); }
    }
    /* floor / bench */
    c.fillStyle = "#123540"; c.fillRect(0, BENCH - 30, 1920, 30);
    c.fillStyle = lg(c, BENCH, 1080, "#a9bcc4", "#6c848d"); c.fillRect(0, BENCH, 1920, 70);
    c.fillStyle = "#24404b"; c.fillRect(0, BENCH + 70, 1920, 10);
    c.fillStyle = "#9fb4bc"; c.fillRect(0, BENCH - 6, 1920, 8);
    for (x = 0; x < 1920; x += 40){ c.fillStyle = (x / 40) % 2 ? "#1a1a1a" : "#ffcf1a"; c.beginPath(); c.moveTo(x, BENCH + 2); c.lineTo(x + 40, BENCH + 2); c.lineTo(x + 30, BENCH + 12); c.lineTo(x - 10, BENCH + 12); c.closePath(); c.fill(); }
    c.fillStyle = "rgba(0,0,0,.18)"; for (x = 0; x < 1920; x += 240) c.fillRect(x, BENCH + 14, 4, 56);
    /* test-tube rack + beakers on the bench */
    c.fillStyle = "#5a3a1e"; c.fillRect(250, BENCH + 44, 300, 14);
    for (i = 0; i < 6; i++){ var tx = 270 + i * 46; c.fillStyle = "rgba(220,245,255,.35)"; c.fillRect(tx, BENCH + 4, 26, 48); c.fillStyle = cols[i]; c.fillRect(tx + 2, BENCH + 24, 22, 26); c.fillStyle = "#cfe6ee"; c.fillRect(tx - 2, BENCH + 2, 30, 5); }
    c.fillStyle = "rgba(220,245,255,.3)"; c.fillRect(1290, BENCH - 24, 60, 70); c.fillStyle = "#ffd84d"; c.fillRect(1293, BENCH + 8, 54, 36); c.fillStyle = "rgba(220,245,255,.3)"; c.fillRect(1370, BENCH - 6, 50, 52); c.fillStyle = "#6bd1ff"; c.fillRect(1373, BENCH + 18, 44, 26);
    c.fillStyle = "#3b4a50"; c.fillRect(1440, BENCH + 36, 160, 16);
    /* monitor frame in the middle of the bench */
    c.fillStyle = "#1b3640"; c.fillRect(630, BENCH - 6, 560, 76); c.strokeStyle = "#7fd8f0"; c.lineWidth = 5; c.strokeRect(630, BENCH - 6, 560, 76);
    cloudSpr = cloudSprite();
  }

  function paint(c, t, dt, W, Hh, TK, S){
    if (!base) build();
    var k = TK.motion === "calm" ? 0.4 : 1, d = dt > 0.1 ? 0.1 : (dt || 0.016), i;
    P += (S.progress - P) * Math.min(1, d * 3);
    Mi += (clamp(S.misses / 6, 0, 1) - Mi) * Math.min(1, d * 1.6);
    Wn += (S.win - Wn) * Math.min(1, d * 1.0); Ls += (S.lose - Ls) * Math.min(1, d * 1.5);
    var lit = S.progress >= 0.999 ? 6 : Math.floor(S.progress * 6 + 0.0001);
    if (lit > lastParts) pop = 1; lastParts = lit; pop = Math.max(0, pop - d * 1.3);
    var thr = clamp(Mi + Ls * 0.6, 0, 1) * (1 - Wn);
    c.drawImage(base, 0, 0);
    /* monitor: heartbeat trace (green -> red with danger) + 6 build lights */
    var my = BENCH + 30, red = thr > 0.5;
    c.fillStyle = "#04140f"; c.fillRect(640, BENCH + 2, 540, 62);
    c.strokeStyle = red ? "#ff6a5a" : "#6dff9e"; c.lineWidth = 3; c.beginPath();
    var amp = 8 + thr * 22 + S.cheer * 10, sp = 1.4 + thr * 3;
    for (i = 0; i <= 90; i++){ var px = 648 + i * 4.2, ph = (px / 70 - t * sp) % 1; if (ph < 0) ph += 1; var yy = my + (ph < 0.08 ? -amp * 1.6 * ph / 0.08 : ph < 0.16 ? -amp * 1.6 + amp * 2.4 * (ph - 0.08) / 0.08 : ph < 0.22 ? amp * 0.8 - amp * 0.8 * (ph - 0.16) / 0.06 : 0); if (i) c.lineTo(px, yy); else c.moveTo(px, yy); }
    c.stroke();
    for (i = 0; i < 6; i++){ c.fillStyle = lit > i ? "#6dff9e" : "rgba(127,216,240,.25)"; c.fillRect(1032 + i * 24, BENCH + 50, 16, 8); }
    /* pressure gauge (left) = danger, antidote tube (right) = progress */
    c.save(); c.translate(86, 600); c.fillStyle = "#0e2a33"; c.beginPath(); c.arc(0, 0, 50, 0, TAU); c.fill(); c.strokeStyle = "#7fd8f0"; c.lineWidth = 6; c.stroke();
    c.lineWidth = 4; for (i = 0; i <= 8; i++){ var ga = -2.4 + i * 0.35; c.strokeStyle = i > 5 ? "#ff6a5a" : "#bff3ff"; c.beginPath(); c.moveTo(Math.cos(ga) * 36, Math.sin(ga) * 36); c.lineTo(Math.cos(ga) * 44, Math.sin(ga) * 44); c.stroke(); }
    var na = -2.4 + clamp(thr + S.miss * 0.2, 0, 1) * 2.8 + Math.sin(t * 20) * 0.02 * thr; c.strokeStyle = "#ffd84d"; c.lineWidth = 5; c.beginPath(); c.moveTo(0, 0); c.lineTo(Math.cos(na) * 38, Math.sin(na) * 38); c.stroke(); c.fillStyle = "#ffd84d"; c.beginPath(); c.arc(0, 0, 6, 0, TAU); c.fill(); c.restore();
    var tubeX = 1840, tubeT = 250, tubeH = 500, lvl = clamp(P, 0, 1) * (tubeH - 20);
    c.fillStyle = "rgba(200,240,255,.12)"; c.fillRect(tubeX - 28, tubeT, 56, tubeH);
    if (lvl > 1){ var tg = c.createLinearGradient(0, tubeT + tubeH - lvl, 0, tubeT + tubeH); tg.addColorStop(0, "#9dffc8"); tg.addColorStop(1, "#14b873"); c.fillStyle = tg; c.fillRect(tubeX - 24, tubeT + tubeH - 10 - lvl, 48, lvl);
      c.fillStyle = "rgba(255,255,255,.7)"; for (i = 0; i < 4; i++){ c.beginPath(); c.arc(tubeX + Math.sin(t * 2 + i * 2) * 12, tubeT + tubeH - 14 - ((t * 50 + i * 120) % Math.max(20, lvl)), 4, 0, TAU); c.fill(); } }
    c.strokeStyle = "#e9fbff"; c.lineWidth = 5; c.strokeRect(tubeX - 28, tubeT, 56, tubeH); for (i = 1; i < 6; i++){ c.strokeStyle = lit >= i ? "#ffd84d" : "rgba(233,251,255,.6)"; c.lineWidth = 4; c.beginPath(); c.moveTo(tubeX - 28, tubeT + tubeH - i * (tubeH - 20) / 6 - 10); c.lineTo(tubeX - 6, tubeT + tubeH - i * (tubeH - 20) / 6 - 10); c.stroke(); }
    c.fillStyle = "#a0673a"; c.fillRect(tubeX - 34, tubeT - 14, 68, 16); c.fillRect(tubeX - 34, tubeT + tubeH - 2, 68, 16);
    /* flask on the bench (right) */
    flask(c, 1520, BENCH + 4 + (Ls > 0.1 ? 0 : Math.sin(t * 1.5 * k) * 0), 0.9 + 0.08 * pop, P, t, 6, lit);
    if (S.cheer > 0.05){ c.fillStyle = "rgba(190,255,220," + (S.cheer * 0.9) + ")"; for (i = 0; i < 6; i++){ c.beginPath(); c.arc(1520 + Math.sin(i * 2.3 + t * 3) * 70, BENCH - 100 - (1 - S.cheer) * 160 - i * 14, 5 + i % 3 * 2, 0, TAU); c.fill(); } }
    /* sirens on the side walls + sweeping red beam */
    var green = Wn > 0.5, sx = [92, 1828];
    for (i = 0; i < 2; i++){
      if (thr > 0.25 && !green){ c.save(); c.globalAlpha = 0.16 * Math.min(1, (thr - 0.25) * 2 + S.miss) * (0.6 + 0.4 * Math.sin(t * 6)); c.fillStyle = "#ff3a2a"; c.translate(sx[i], 380); c.rotate(t * (2 + thr * 3) * (i ? -1 : 1)); c.beginPath(); c.moveTo(0, 0); c.arc(0, 0, 900, -0.2, 0.2); c.closePath(); c.fill(); c.restore(); }
      siren(c, sx[i], 380, 1.4, t * k, green, thr);
    }
    /* fog = misses */
    if (thr > 0.02){
      var cnt = 18, dr = t * k;
      c.fillStyle = "rgba(100,118,124," + (0.3 * thr) + ")"; c.fillRect(0, 0, W, Hh);
      for (i = 0; i < cnt; i++){
        var a = clamp(thr * cnt - i, 0, 1) * 0.82; if (a <= 0) continue;
        var fx = ((i * 397) % 2100) - 90 + Math.sin(dr * 0.35 + i) * 40, fy = 130 + ((i * 211) % 880) + Math.cos(dr * 0.3 + i * 2) * 24, sc = 1.1 + (i % 4) * 0.3;
        c.globalAlpha = a; c.drawImage(cloudSpr, fx - 150 * sc, fy - 115 * sc, 300 * sc, 230 * sc);
      } c.globalAlpha = 1;
    }
    if (S.miss > 0.05){ var vg = c.createRadialGradient(W / 2, Hh / 2, 380, W / 2, Hh / 2, 1150); vg.addColorStop(0, "rgba(255,40,20,0)"); vg.addColorStop(1, "rgba(255,40,20," + (S.miss * 0.36) + ")"); c.fillStyle = vg; c.fillRect(0, 0, W, Hh); }
    /* win: antidote spray + bubbles, green tint */
    if (Wn > 0.05){
      c.fillStyle = "rgba(90,255,170," + (0.07 * Wn) + ")"; c.fillRect(0, 0, W, Hh);
      spT -= d; if (spT <= 0){ spT = 0.03 / k; var sxp = Math.random() < 0.5 ? 20 + Math.random() * 280 : 1620 + Math.random() * 280; spray.push({ x: sxp, y: 112, vx: (Math.random() - 0.5) * 60, vy: 220 + Math.random() * 260, l: 2.2 }); }
    }
    for (i = spray.length - 1; i >= 0; i--){ var p = spray[i]; p.l -= d; if (p.l <= 0 || p.y > Hh){ spray.splice(i, 1); continue; } p.x += p.vx * d; p.y += p.vy * d; c.globalAlpha = clamp(p.l, 0, 1) * 0.8; c.fillStyle = "#9dffc8"; c.beginPath(); c.arc(p.x, p.y, 5, 0, TAU); c.fill(); } c.globalAlpha = 1;
    if (Ls > 0.01){ c.fillStyle = "rgba(10,6,10," + (0.5 * Ls) + ")"; c.fillRect(0, 0, W, Hh); c.fillStyle = "rgba(255,40,30," + (0.07 * Ls * (0.5 + 0.5 * Math.sin(t * 7))) + ")"; c.fillRect(0, 0, W, Hh); }
  }

  /* ---- host: 연구원 (ported from the legacy researcher) ---- */
  function face(m){
    var ink = "#1d2b33";
    if (m === "happy") return '<path d="M72 104 q10 -14 20 0 M108 104 q10 -14 20 0" stroke="' + ink + '" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M84 124 q16 20 32 0z" fill="#c2414b" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/><circle cx="66" cy="120" r="8" fill="#ff9aa2" opacity=".7"/><circle cx="134" cy="120" r="8" fill="#ff9aa2" opacity=".7"/>';
    if (m === "sad") return '<circle cx="82" cy="102" r="7" fill="' + ink + '"/><circle cx="118" cy="102" r="7" fill="' + ink + '"/><path d="M70 86 l20 6 M130 86 l-20 6" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/><path d="M88 130 q12 -9 24 0" stroke="' + ink + '" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M152 84 q10 14 0 22 q-10 -8 0 -22z" fill="#8fd7ff" stroke="' + ink + '" stroke-width="3"/>';
    if (m === "wow") return '<circle cx="82" cy="102" r="10" fill="#fff" stroke="' + ink + '" stroke-width="4"/><circle cx="118" cy="102" r="10" fill="#fff" stroke="' + ink + '" stroke-width="4"/><circle cx="83" cy="103" r="5" fill="' + ink + '"/><circle cx="119" cy="103" r="5" fill="' + ink + '"/><ellipse cx="100" cy="132" rx="9" ry="11" fill="#c2414b" stroke="' + ink + '" stroke-width="5"/>';
    return '<circle cx="82" cy="102" r="6" fill="' + ink + '"/><circle cx="118" cy="102" r="6" fill="' + ink + '"/><path d="M88 128 q12 12 24 0" stroke="' + ink + '" stroke-width="5" fill="none" stroke-linecap="round"/>';
  }
  function researcher(m){
    var ink = "#1d2b33";
    return '<g transform="translate(0 60) scale(1.5)"><ellipse cx="100" cy="240" rx="74" ry="9" fill="rgba(0,0,0,.3)"/>' +
      '<path d="M32 240 q2 -92 68 -100 q66 8 68 100z" fill="#f4f8fa" stroke="' + ink + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M82 144 l18 38 18 -38z" fill="#2bb59a" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>' +
      '<path d="M82 144 l-8 54 26 -16z M118 144 l8 54 -26 -16z" fill="#dbe6ec" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>' +
      '<line x1="100" y1="184" x2="100" y2="238" stroke="' + ink + '" stroke-width="4"/>' +
      '<rect x="120" y="200" width="28" height="24" rx="3" fill="#dbe6ec" stroke="' + ink + '" stroke-width="4"/><path d="M128 202 v-14 M138 202 v-16" stroke="#e5484d" stroke-width="5" stroke-linecap="round"/>' +
      '<path d="M30 150 h12 v18 l16 30 q3 7 -5 7 h-34 q-8 0 -5 -7 l16 -30z" fill="#d8fbe8" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>' +
      '<path d="M20 186 h32 l6 12 q3 7 -5 7 h-34 q-8 0 -5 -7z" fill="#36d38a"/><circle cx="36" cy="194" r="3" fill="#fff"/>' +
      '<circle cx="36" cy="170" r="11" fill="#f6d2ae" stroke="' + ink + '" stroke-width="5"/>' +
      '<circle cx="100" cy="30" r="20" fill="#4a2c1d" stroke="' + ink + '" stroke-width="6"/>' +
      '<circle cx="100" cy="104" r="52" fill="#f6d2ae" stroke="' + ink + '" stroke-width="7"/>' +
      '<path d="M48 104 q-6 -60 52 -62 q58 2 52 62 q-8 -30 -30 -34 q-30 16 -56 4 q-14 10 -18 30z" fill="#4a2c1d" stroke="' + ink + '" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M50 74 q50 -18 100 0" stroke="#2bb59a" stroke-width="9" fill="none"/>' +
      '<circle cx="80" cy="68" r="15" fill="#bff0ff" stroke="' + ink + '" stroke-width="6"/><circle cx="120" cy="68" r="15" fill="#bff0ff" stroke="' + ink + '" stroke-width="6"/>' +
      '<circle cx="75" cy="63" r="4" fill="#fff"/><circle cx="115" cy="63" r="4" fill="#fff"/>' + face(m) + '</g>';
  }
  function hostSvg(){
    var out = '<svg viewBox="0 0 300 440" width="300" height="440" xmlns="http://www.w3.org/2000/svg">', ms = ["idle", "happy", "sad", "wow"];
    for (var i = 0; i < 4; i++) out += '<g class="f f-' + ms[i] + '">' + researcher(ms[i]) + "</g>";
    return out + "</svg>";
  }

  function deco(){
    return '<style>.al-p{position:absolute;top:0;bottom:0;width:26px;background:linear-gradient(90deg,#1c3a46,#4d7c8c 45%,#1c3a46);box-shadow:0 0 24px rgba(0,0,0,.55)}' +
      '.al-p.l{left:0}.al-p.r{right:0}' +
      '.al-p:before{content:"";position:absolute;left:-5px;right:-5px;top:0;bottom:0;background:repeating-linear-gradient(0deg,transparent 0,transparent 150px,#2b3a40 150px,#2b3a40 170px)}' +
      '.al-lite{position:absolute;top:96px;width:200px;height:10px;border-radius:5px;background:#e8fbff;box-shadow:0 0 30px 10px rgba(190,240,255,.35);animation:alfl 3.1s infinite}.al-lite.a{left:1010px}.al-lite.b{left:1280px;animation-delay:-1.4s}' +
      '.al-lite.warn{background:#ff6a5a;box-shadow:0 0 40px 14px rgba(255,60,40,.7)}.al-lite.ok{background:#7dffb2;box-shadow:0 0 40px 14px rgba(90,255,150,.7)}' +
      '@keyframes alfl{0%,92%,100%{opacity:1}94%{opacity:.4}97%{opacity:.9}}</style>' +
      '<div class="al-p l"></div><div class="al-p r"></div><div class="al-lite a"></div><div class="al-lite b"></div>';
  }
  function sfx(){
    if (!NG.defineSfx) return;
    NG.defineSfx("alAlarm", function(){ for (var i = 0; i < 3; i++){ NG.tone({ type: "square", freq: 880, dur: 0.12, vol: 0.12, delay: i * 0.22, jitter: 0 }); NG.tone({ type: "square", freq: 660, dur: 0.12, vol: 0.12, delay: i * 0.22 + 0.11, jitter: 0 }); } });
    NG.defineSfx("alSpray", function(){ NG.tone({ type: "noise", freq: 3000, q: 0.5, dur: 1.4, vol: 0.14, filter: "highpass" }); NG.tone({ type: "sine", freq: 523, dur: 0.3, vol: 0.2, jitter: 0 }); NG.tone({ type: "sine", freq: 784, dur: 0.5, vol: 0.2, jitter: 0, delay: 0.18 }); });
  }
  function lights(cls, ms){
    var e = document.querySelectorAll("#ts-deco .al-lite");
    for (var i = 0; i < e.length; i++){ e[i].classList.add(cls); (function(x){ setTimeout(function(){ x.classList.remove(cls); }, ms); })(e[i]); }
  }
  function onReact(kind){
    try {
      if (kind === "wrong"){ lights("warn", 1000); NG.sfx("alAlarm"); }
      else if (kind === "correct"){ lights("ok", 700); }
      else if (kind === "win"){ lights("ok", 5000); NG.sfx("alSpray"); }
      else if (kind === "lose"){ lights("warn", 4000); NG.sfx("alAlarm"); }
    } catch (e) {}
  }
  return {
    paint: paint, deco: deco, sfx: sfx, onReact: onReact,
    host: { svg: hostSvg, name: "연구원", lines: {
      title: ["해독제를 완성하자!", "실험 시작할까?"], start: ["실험 시작!", "집중, 집중!"],
      correct: ["해독제가 차오른다!", "좋아, 성공!", "바로 그거야!"], wrong: ["연기가 퍼진다!", "앗, 경보 울려!", "침착해!"],
      win: ["해독제 완성! 대성공!", "실험실을 구했다!"], lose: ["환기하고 다시 해 보자!", "괜찮아, 다시 도전!"] } }
  };
})();
