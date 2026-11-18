/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME sun-temple — 태양 신전. progress awakens the sun emblem + floor glyph tablets, misses lower the ceiling slab and drain the hourglass,
   cheer flares the torches, win = golden light burst, lose = slab slams down and the torches die. Works with every mechanic (reads only COMP.S). */
COMP.themes["sun-temple"] = (function(){
  var TAU = 6.2832, base = null, P = 0, Mi = 0, Wn = 0, Ls = 0, pop = 0, lastParts = 0, dust = [], spk = [], spT = 0, FL = 900;
  function mk(w, h){ var c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
  function clamp(v, a, b){ return v < a ? a : (v > b ? b : v); }
  function lg(c, y0, y1, a, b){ var g = c.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, a); g.addColorStop(1, b); return g; }
  (function(){ for (var i = 0; i < 46; i++) dust.push({ x: Math.random() * 1920, v: 60 + Math.random() * 90, p: Math.random() * 900 }); })();

  /* ---- art (ported from the escape-room temple skin: emblem, bricks, glyphs, torch, hourglass) ---- */
  function emblem(c, x, y, r, lit, n, t, power){
    n = Math.max(1, n);
    c.save(); c.translate(x, y);
    if (power > 0){ var rg = c.createRadialGradient(0, 0, r * 0.3, 0, 0, r * 1.8); rg.addColorStop(0, "rgba(255,220,120," + (0.55 * power) + ")"); rg.addColorStop(1, "rgba(255,200,80,0)"); c.fillStyle = rg; c.beginPath(); c.arc(0, 0, r * 1.8, 0, TAU); c.fill(); }
    c.fillStyle = "#4a3826"; c.strokeStyle = "#1e140a"; c.lineWidth = r * 0.07; c.beginPath(); c.arc(0, 0, r, 0, TAU); c.fill(); c.stroke();
    var gap = 0.09, a0 = -Math.PI / 2;
    for (var i = 0; i < n; i++){
      var s = a0 + i * TAU / n + gap, e = a0 + (i + 1) * TAU / n - gap, on = i < lit;
      c.beginPath(); c.arc(0, 0, r * 0.9, s, e); c.arc(0, 0, r * 0.56, e, s, true); c.closePath();
      if (on){ var gg = c.createLinearGradient(0, -r, 0, r); gg.addColorStop(0, "#fff0a8"); gg.addColorStop(1, "#e0a530"); c.fillStyle = gg; c.fill(); c.strokeStyle = "#5a3a10"; c.lineWidth = r * 0.04; c.setLineDash([]); c.stroke();
        var m = (s + e) / 2; c.fillStyle = "#8a5a14"; c.beginPath(); c.arc(Math.cos(m) * r * 0.73, Math.sin(m) * r * 0.73, r * 0.06, 0, TAU); c.fill(); }
      else { c.setLineDash([r * 0.08, r * 0.07]); c.strokeStyle = "rgba(255,215,150,.55)"; c.lineWidth = r * 0.035; c.stroke(); c.setLineDash([]); }
    }
    var full = lit >= n;
    c.beginPath(); c.arc(0, 0, r * 0.42, 0, TAU); c.fillStyle = full ? "#ffe680" : "#3a2a1a"; c.fill(); c.strokeStyle = full ? "#7a4a10" : "rgba(255,215,150,.55)"; c.lineWidth = r * 0.04; c.stroke();
    c.strokeStyle = full ? "#7a4a10" : "rgba(255,215,150,.45)"; c.lineWidth = r * 0.05;
    c.beginPath(); c.moveTo(-r * 0.2, -r * 0.02); c.quadraticCurveTo(0, -r * 0.22, r * 0.2, -r * 0.02); c.quadraticCurveTo(0, r * 0.18, -r * 0.2, -r * 0.02); c.stroke();
    c.fillStyle = full ? "#7a4a10" : "rgba(255,215,150,.45)"; c.beginPath(); c.arc(0, -r * 0.02, r * 0.07, 0, TAU); c.fill();
    if (full){ c.strokeStyle = "rgba(255,240,170,.9)"; c.lineWidth = r * 0.04; for (var k = 0; k < 12; k++){ var aa = k * TAU / 12 + t * 0.4, rr = r * (1.18 + 0.05 * Math.sin(t * 5 + k)); c.beginPath(); c.moveTo(Math.cos(aa) * r * 1.04, Math.sin(aa) * r * 1.04); c.lineTo(Math.cos(aa) * rr, Math.sin(aa) * rr); c.stroke(); } }
    c.restore();
  }
  function bricks(c, x0, y0, W, H, bw, bh, base, light){
    c.fillStyle = base; c.fillRect(x0, y0, W, H);
    for (var row = 0, y = y0; y < y0 + H; y += bh, row++){
      for (var x = x0 - (row % 2) * bw / 2; x < x0 + W; x += bw){
        var v = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453; v = v - Math.floor(v);
        if (v > 0.6){ c.fillStyle = light; c.fillRect(x + 3, y + 3, bw - 6, bh - 6); }
        c.fillStyle = "rgba(0,0,0,.38)"; c.fillRect(x, y, 4, bh); }
      c.fillStyle = "rgba(0,0,0,.38)"; c.fillRect(x0, y, W, 4);
      c.fillStyle = "rgba(255,220,160,.05)"; c.fillRect(x0, y + 4, W, 3);
    }
  }
  function glyph(c, x, y, k, sc){
    c.beginPath();
    if (k === 0){ c.moveTo(x - 20 * sc, y + 16 * sc); c.lineTo(x, y - 18 * sc); c.lineTo(x + 20 * sc, y + 16 * sc); c.closePath(); }
    else if (k === 1){ c.ellipse(x, y, 22 * sc, 12 * sc, 0, 0, TAU); c.moveTo(x + 5 * sc, y); c.arc(x, y, 5 * sc, 0, TAU); }
    else { c.moveTo(x - 24 * sc, y); for (var j = 0; j < 4; j++) c.quadraticCurveTo(x + (-18 + j * 12) * sc, y - 12 * sc * (j % 2 ? -1 : 1), x + (-12 + j * 12) * sc, y); }
    c.stroke();
  }
  function glyphs(c, x0, y0, W, H, step){
    c.strokeStyle = "rgba(255,210,140,.10)"; c.lineWidth = 5;
    for (var y = y0 + step / 2; y < y0 + H; y += step) for (var x = x0 + step / 2 + ((y / step) % 2) * step / 2; x < x0 + W; x += step * 1.6) glyph(c, x, y, Math.floor(x / 97 + y / 61) % 3, 1);
  }
  function torch(c, x, y, s, t, k, power){
    c.fillStyle = "#4a2f18"; c.fillRect(x - 6 * s, y, 12 * s, 40 * s);
    c.fillStyle = "#2a1c10"; c.fillRect(x - 12 * s, y - 4 * s, 24 * s, 10 * s);
    if (power <= 0.02) return;
    var f = (1 + 0.12 * Math.sin(t * 13 + k)) * (0.5 + 0.5 * power);
    c.fillStyle = "rgba(255,150,40," + (0.25 * power) + ")"; c.beginPath(); c.arc(x, y - 18 * s, 40 * s * f, 0, TAU); c.fill();
    c.fillStyle = "#ff8a2a"; c.beginPath(); c.moveTo(x - 12 * s, y - 4 * s); c.quadraticCurveTo(x - 14 * s, y - 30 * s * f, x, y - 44 * s * f); c.quadraticCurveTo(x + 14 * s, y - 30 * s * f, x + 12 * s, y - 4 * s); c.fill();
    c.fillStyle = "#ffe07a"; c.beginPath(); c.moveTo(x - 6 * s, y - 4 * s); c.quadraticCurveTo(x - 6 * s, y - 18 * s * f, x, y - 26 * s * f); c.quadraticCurveTo(x + 6 * s, y - 18 * s * f, x + 6 * s, y - 4 * s); c.fill();
  }
  function hourglass(c, x, y, s, rem, ticking){
    c.save(); c.translate(x, y); c.scale(s, s);
    c.fillStyle = "#8a6a40"; c.fillRect(-26, -40, 52, 8); c.fillRect(-26, 32, 52, 8);
    c.strokeStyle = "#f0e2b8"; c.lineWidth = 4; c.beginPath(); c.moveTo(-18, -32); c.lineTo(18, -32); c.lineTo(3, 0); c.lineTo(18, 32); c.lineTo(-18, 32); c.lineTo(-3, 0); c.closePath(); c.stroke();
    c.fillStyle = "#ffd27a";
    var th = 26 * rem; c.beginPath(); c.moveTo(-14 * rem - 2, -2 - th); c.lineTo(14 * rem + 2, -2 - th); c.lineTo(2, -2); c.lineTo(-2, -2); c.closePath(); c.fill();
    var bh = 26 * (1 - rem); c.beginPath(); c.moveTo(-15, 30); c.lineTo(15, 30); c.lineTo(15 * (1 - bh / 30), 30 - bh); c.lineTo(-15 * (1 - bh / 30), 30 - bh); c.closePath(); c.fill();
    if (ticking && rem > 0.02) c.fillRect(-1.5, 0, 3, 30 - bh);
    c.restore();
  }

  function build(){
    base = mk(1920, 1080); var c = base.getContext("2d"), i, x;
    bricks(c, 0, 0, 1920, FL, 180, 76, "#2a1b0e", "#33220f");
    glyphs(c, 0, 0, 1920, FL, 228);
    var vg = c.createRadialGradient(960, 480, 300, 960, 480, 1100); vg.addColorStop(0, "rgba(20,10,4,.45)"); vg.addColorStop(1, "rgba(10,5,2,.65)"); c.fillStyle = vg; c.fillRect(0, 0, 1920, FL);
    /* side pillars */
    for (i = 0; i < 2; i++){ var px = i ? 1858 : 0; c.fillStyle = lg(c, 0, 0, "#5a4128", "#5a4128"); var pg = c.createLinearGradient(px, 0, px + 62, 0); pg.addColorStop(0, "#3a2716"); pg.addColorStop(0.5, "#7a5a36"); pg.addColorStop(1, "#3a2716"); c.fillStyle = pg; c.fillRect(px, 0, 62, FL);
      c.fillStyle = "rgba(0,0,0,.3)"; for (var yy = 60; yy < FL; yy += 90) c.fillRect(px, yy, 62, 5); c.fillStyle = "#c99a3e"; c.fillRect(px, 0, 62, 10); c.fillRect(px, FL - 14, 62, 14); }
    /* floor with gold trim */
    c.fillStyle = lg(c, FL, 1080, "#4a3420", "#241608"); c.fillRect(0, FL, 1920, 1080 - FL);
    c.fillStyle = "rgba(0,0,0,.35)"; for (x = 0; x < 1920; x += 160) c.fillRect(x, FL + 8, 4, 1080 - FL); c.fillRect(0, FL + 8, 1920, 6);
    c.fillStyle = "#c99a3e"; c.fillRect(0, FL - 6, 1920, 8); c.fillStyle = "#5a3a1a"; c.beginPath(); c.moveTo(0, FL + 2); for (x = 0; x <= 1920; x += 24) c.lineTo(x, (x / 24) % 2 ? FL + 14 : FL + 2); c.lineTo(1920, FL + 2); c.fill();
    /* six empty tablets in the floor wall */
    for (i = 0; i < 6; i++){ var tx = 390 + i * 232; c.fillStyle = "#2c1d10"; c.fillRect(tx, 936, 150, 100); c.strokeStyle = "#7a5530"; c.lineWidth = 6; c.strokeRect(tx, 936, 150, 100); }
  }

  function paint(c, t, dt, W, Hh, TK, S){
    if (!base) build();
    var k = TK.motion === "calm" ? 0.4 : 1, d = dt > 0.1 ? 0.1 : (dt || 0.016), i;
    P += (S.progress - P) * Math.min(1, d * 3);
    Mi += (clamp(S.misses / 6, 0, 1) - Mi) * Math.min(1, d * 1.6);
    Wn += (S.win - Wn) * Math.min(1, d * 1.1); Ls += (S.lose - Ls) * Math.min(1, d * 1.6);
    var lit = S.progress >= 0.999 ? 6 : Math.floor(S.progress * 6 + 0.0001);
    if (lit > lastParts) pop = 1; lastParts = lit; pop = Math.max(0, pop - d * 1.3);
    var thr = clamp(Mi + Ls * 0.6, 0, 1) * (1 - Wn), tpow = clamp(1 - Ls * 0.85 + S.cheer * 0.4, 0, 1.3);
    c.drawImage(base, 0, 0);
    /* big dim sun emblem etched in the wall (stays calm behind the cards) */
    emblem(c, 960, 520, 330, lit, 6, t, 0);
    c.fillStyle = "rgba(24,14,6," + (0.74 - 0.06 * Wn - 0.1 * (lit / 6)) + ")"; c.beginPath(); c.arc(960, 520, 420, 0, TAU); c.fill();
    /* torch glow on the walls */
    var fl = 0.8 + 0.2 * Math.sin(t * 9) + S.cheer * 0.4, tp = [[106, 760], [1814, 760]];
    for (i = 0; i < 2; i++){ var gx = tp[i][0], gy = tp[i][1] - 30, rg = c.createRadialGradient(gx, gy, 20, gx, gy, 460); rg.addColorStop(0, "rgba(255,160,60," + (0.34 * fl * tpow) + ")"); rg.addColorStop(1, "rgba(255,160,60,0)"); c.fillStyle = rg; c.fillRect(gx - 460, gy - 460, 920, 920); }
    torch(c, 106, 760, 1.5, t * k, 0, tpow); torch(c, 1814, 760, 1.5, t * k, 2, tpow);
    /* tablets light up with progress */
    for (i = 0; i < 6; i++){ var tx = 390 + i * 232, on = lit > i, a = on ? 1 : 0; c.fillStyle = on ? "#e8b84a" : "#2c1d10"; c.fillRect(tx + 4, 940, 142, 92);
      if (on){ var tg = c.createRadialGradient(tx + 75, 986, 10, tx + 75, 986, 150); tg.addColorStop(0, "rgba(255,230,140," + (0.5 + 0.2 * Math.sin(t * 3 + i)) + ")"); tg.addColorStop(1, "rgba(255,200,80,0)"); c.fillStyle = tg; c.fillRect(tx - 60, 880, 270, 200); }
      c.strokeStyle = on ? "#fffbe0" : "rgba(255,215,150,.26)"; c.lineWidth = 6; glyph(c, tx + 75, 986, i % 3, 1.5); }
    /* emblem on the right column + hourglass on the left column */
    emblem(c, 1818, 420, 56, lit, 6, t, Math.max(pop, Wn, S.cheer * 0.6));
    hourglass(c, 100, 480, 1.4, 1 - thr, true);
    /* ceiling slab = misses */
    var sb = 30 + thr * 150 + S.miss * 26 + Ls * 70 + Math.sin(t * 40) * S.miss * 2;
    var sg = c.createLinearGradient(0, 0, 0, sb); sg.addColorStop(0, "#3d2d1d"); sg.addColorStop(1, "#7a5c3a"); c.fillStyle = sg; c.fillRect(0, 0, W, sb);
    c.fillStyle = "#5e4529"; c.fillRect(0, sb - 22, W, 22);
    c.fillStyle = "#2a1c10"; for (i = 0; i < W; i += 60){ c.beginPath(); c.moveTo(i + 6, sb); c.lineTo(i + 30, sb + 26); c.lineTo(i + 54, sb); c.closePath(); c.fill(); }
    c.strokeStyle = "rgba(255,210,140,.25)"; c.lineWidth = 3; c.beginPath(); for (i = 0; i < W; i += 40){ c.moveTo(i, sb - 18); c.lineTo(i + 20, sb - 6); c.lineTo(i + 40, sb - 18); } c.stroke();
    if (thr > 0.35){ c.strokeStyle = "rgba(0,0,0,.55)"; c.lineWidth = 4; c.beginPath(); var cx = [300, 760, 1180, 1600]; for (i = 0; i < 4; i++){ c.moveTo(cx[i], sb - 22); c.lineTo(cx[i] + 18, sb - 12); c.lineTo(cx[i] - 6, sb + 4); } c.stroke(); }
    /* falling dust */
    var nd = Wn > 0.3 ? 0 : Math.floor(6 + thr * 36 + S.miss * 20); c.fillStyle = "rgba(230,200,150,.55)";
    for (i = 0; i < nd && i < dust.length; i++){ var q = dust[i], dy = sb + ((t * q.v * k + q.p) % (FL - sb)); c.fillRect(q.x, dy, 3, 3); }
    /* win: golden light + rising sparks */
    if (Wn > 0.02){
      c.save(); c.globalAlpha = Wn * 0.07; c.fillStyle = "#fff0b0"; for (i = 0; i < 12; i++){ var ba = i * TAU / 12 + t * 0.25; c.beginPath(); c.moveTo(1818, 420); c.arc(1818, 420, 1800, ba, ba + 0.1); c.closePath(); c.fill(); } c.restore();
      c.fillStyle = "rgba(255,200,90," + (0.08 * Wn) + ")"; c.fillRect(0, 0, W, Hh);
      spT -= d; if (spT <= 0){ spT = 0.04 / k; spk.push({ x: Math.random() < 0.5 ? 90 + Math.random() * 200 : 1630 + Math.random() * 200, y: FL, vx: (Math.random() - 0.5) * 50, vy: -(140 + Math.random() * 220), l: 2.8 }); }
    }
    for (i = spk.length - 1; i >= 0; i--){ var p = spk[i]; p.l -= d; if (p.l <= 0){ spk.splice(i, 1); continue; } p.x += p.vx * d; p.y += p.vy * d; c.globalAlpha = clamp(p.l, 0, 1); c.fillStyle = i % 3 ? "#ffe680" : "#fff6d0"; c.fillRect(p.x - 3, p.y - 3, 6, 6); } c.globalAlpha = 1;
    if (S.miss > 0.05){ var vg = c.createRadialGradient(W / 2, Hh / 2, 380, W / 2, Hh / 2, 1150); vg.addColorStop(0, "rgba(120,50,20,0)"); vg.addColorStop(1, "rgba(120,50,20," + (S.miss * 0.4) + ")"); c.fillStyle = vg; c.fillRect(0, 0, W, Hh); }
    if (Ls > 0.01){ c.fillStyle = "rgba(8,4,2," + (0.5 * Ls) + ")"; c.fillRect(0, 0, W, Hh); }
  }

  /* ---- host: 탐험가 (ported from the legacy explorer) ---- */
  function face(m){
    var ink = "#2a1c10";
    if (m === "happy") return '<path d="M72 102 q10 -14 20 0 M108 102 q10 -14 20 0" stroke="' + ink + '" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M82 122 q18 22 36 0z" fill="#9a3020" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>';
    if (m === "sad") return '<circle cx="82" cy="100" r="7" fill="' + ink + '"/><circle cx="118" cy="100" r="7" fill="' + ink + '"/><path d="M70 84 l20 6 M130 84 l-20 6" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/><path d="M88 130 q12 -9 24 0" stroke="' + ink + '" stroke-width="5" fill="none" stroke-linecap="round"/>';
    if (m === "wow") return '<circle cx="82" cy="100" r="10" fill="#fff" stroke="' + ink + '" stroke-width="4"/><circle cx="118" cy="100" r="10" fill="#fff" stroke="' + ink + '" stroke-width="4"/><circle cx="83" cy="101" r="5" fill="' + ink + '"/><circle cx="119" cy="101" r="5" fill="' + ink + '"/><ellipse cx="100" cy="128" rx="9" ry="11" fill="#9a3020" stroke="' + ink + '" stroke-width="5"/>';
    return '<circle cx="82" cy="100" r="6" fill="' + ink + '"/><circle cx="118" cy="100" r="6" fill="' + ink + '"/><path d="M88 126 q12 12 24 0" stroke="' + ink + '" stroke-width="5" fill="none" stroke-linecap="round"/>';
  }
  function explorer(m){
    var ink = "#2a1c10";
    return '<g transform="translate(0 60) scale(1.5)"><ellipse cx="100" cy="240" rx="74" ry="9" fill="rgba(0,0,0,.3)"/>' +
      '<path d="M36 240 q0 -92 64 -100 q64 8 64 100z" fill="#c9a86a" stroke="' + ink + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M66 150 l12 90 M134 150 l-12 90" stroke="#6b4423" stroke-width="11"/>' +
      '<rect x="88" y="196" width="24" height="20" rx="3" fill="#a88a50" stroke="' + ink + '" stroke-width="4"/>' +
      '<path d="M76 144 q24 20 48 0 l-10 28 -14 -10 -14 10z" fill="#d8452f" stroke="' + ink + '" stroke-width="5" stroke-linejoin="round"/>' +
      '<path d="M170 236 l12 -92" stroke="#6b4423" stroke-width="11" stroke-linecap="round"/>' +
      '<path d="M182 146 q-22 -22 -2 -52 q6 20 16 24 q8 20 -14 28z" fill="#ffb02e" stroke="#c8402f" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M182 140 q-10 -12 -2 -26 q4 10 8 12 q2 10 -6 14z" fill="#ffe680"/>' +
      '<circle cx="176" cy="196" r="12" fill="#e8b98a" stroke="' + ink + '" stroke-width="5"/>' +
      '<circle cx="100" cy="102" r="52" fill="#e8b98a" stroke="' + ink + '" stroke-width="7"/>' +
      '<path d="M50 90 q2 18 10 26 M150 90 q-2 18 -10 26" stroke="#6b3a1e" stroke-width="8" fill="none" stroke-linecap="round"/>' +
      '<circle cx="70" cy="118" r="2.5" fill="#a0603a"/><circle cx="62" cy="112" r="2.5" fill="#a0603a"/><circle cx="130" cy="118" r="2.5" fill="#a0603a"/><circle cx="138" cy="112" r="2.5" fill="#a0603a"/>' +
      face(m) +
      '<ellipse cx="100" cy="66" rx="86" ry="17" fill="#e8d7a8" stroke="' + ink + '" stroke-width="6"/>' +
      '<path d="M46 66 q0 -60 54 -60 q54 0 54 60z" fill="#f2e3b8" stroke="' + ink + '" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M48 54 q52 12 104 0" stroke="#8a5a2b" stroke-width="9" fill="none"/>' +
      '<circle cx="100" cy="8" r="7" fill="#e8d7a8" stroke="' + ink + '" stroke-width="4"/></g>';
  }
  function hostSvg(){
    var out = '<svg viewBox="0 0 300 440" width="300" height="440" xmlns="http://www.w3.org/2000/svg">', ms = ["idle", "happy", "sad", "wow"];
    for (var i = 0; i < 4; i++) out += '<g class="f f-' + ms[i] + '">' + explorer(ms[i]) + "</g>";
    return out + "</svg>";
  }

  function deco(){
    return '<style>.st-edge{position:absolute;left:0;top:0;width:1920px;height:1080px;pointer-events:none;box-shadow:inset 0 0 160px 40px rgba(0,0,0,.55)}' +
      '.st-edge.warn{animation:stqk .5s}@keyframes stqk{0%,100%{transform:translate(0,0)}20%{transform:translate(0,4px)}50%{transform:translate(0,-3px)}80%{transform:translate(0,2px)}}</style><div class="st-edge"></div>';
  }
  function sfx(){
    if (!NG.defineSfx) return;
    NG.defineSfx("stRumble", function(){ NG.tone({ type: "noise", freq: 140, q: 0.7, dur: 0.9, vol: 0.3, filter: "lowpass" }); NG.tone({ type: "sine", freq: 70, slide: -30, dur: 0.8, vol: 0.3, jitter: 0 }); });
    NG.defineSfx("stSun", function(){ [1, 1.5, 2, 3].forEach(function(r, i){ NG.tone({ type: "sine", freq: 392 * r, dur: 1.6 - i * 0.2, vol: 0.2 / (1 + i * 0.4), jitter: 0, delay: i * 0.12, attack: 0.01 }); }); });
  }
  function onReact(kind){
    try {
      var e = document.querySelector("#ts-deco .st-edge");
      if (kind === "wrong"){ NG.sfx("stRumble"); if (e){ e.classList.remove("warn"); void e.offsetWidth; e.classList.add("warn"); } }
      else if (kind === "win"){ NG.sfx("stSun"); }
      else if (kind === "lose"){ NG.sfx("stRumble"); }
    } catch (e2) {}
  }
  return {
    paint: paint, deco: deco, sfx: sfx, onReact: onReact,
    host: { svg: hostSvg, name: "탐험가", lines: {
      title: ["신전의 봉인을 풀자!", "탐험을 시작할까?"], start: ["신전 입장!", "조심조심 가자!"],
      correct: ["문양이 깨어난다!", "봉인이 풀렸다!", "좋았어!"], wrong: ["천장이 내려온다!", "앗, 먼지가!", "서둘러!"],
      win: ["신전 탈출 성공!", "태양이 깨어났다!"], lose: ["천장이 내려앉았다!", "다시 도전하자!"] } }
  };
})();
