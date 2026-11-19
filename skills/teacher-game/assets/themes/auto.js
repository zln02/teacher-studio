/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME auto — runtime of scripts/theme_auto.py. Draws a designed scene from SPEC.autoTheme (background generator + pattern +
   floating icon props + celebration particles) and hosts a DiceBear (CC0) character. Colors come from the tokens.
   bg kinds: aurora waves hills city bokeh sunburst ink pitch geometric mesh. All procedural (no image files). */
COMP.themes.auto = (function(){
  var A = SPEC.autoTheme || { bg: "mesh", pattern: "dots", cel: "confetti", seed: 1, icons: {}, props: [], host: null };
  var CV = {}, imgs = {}, parts = [], prevCheer = 0, seedv = A.seed || 1, ready = false;
  function rnd(){ seedv |= 0; seedv = (seedv + 0x6D2B79F5) | 0; var t = Math.imul(seedv ^ (seedv >>> 15), 1 | seedv); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
  function hx(h){ h = String(h).replace("#", ""); return [parseInt(h.substr(0, 2), 16), parseInt(h.substr(2, 2), 16), parseInt(h.substr(4, 2), 16)]; }
  function rgba(h, a){ var c = hx(h); return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")"; }
  function mix(a, b, t){ var x = hx(a), y = hx(b), o = []; for (var i = 0; i < 3; i++) o.push(Math.round(x[i] + (y[i] - x[i]) * t)); return "rgb(" + o.join(",") + ")"; }
  function lum(h){ var c = hx(h); return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255; }
  /* text keep-out: title, question and answers live in this band of the 1920x1080 stage; decoration is drawn around it, never behind it */
  var KEEP = [150, 170, 1770, 890];
  function clear(x, y, r){ return x + r < KEEP[0] || x - r > KEEP[2] || y + r < KEEP[1] || y - r > KEEP[3]; }
  function layer(draw){ var c = document.createElement("canvas"); c.width = 1920; c.height = 1080; draw(c.getContext("2d")); return c; }
  function colors(TK){ return TK.colors; }

  function pattern(c, kind, col){
    c.save(); c.globalAlpha = 0.09; c.fillStyle = col; c.strokeStyle = col; c.lineWidth = 2;
    var x, y;
    if (kind === "dots"){ for (y = 40; y < 1080; y += 72) for (x = (y / 72) % 2 ? 36 : 0; x < 1920; x += 72){ c.beginPath(); c.arc(x, y, 5, 0, 6.283); c.fill(); } }
    else if (kind === "stars" || kind === "sparkle"){ for (var i = 0; i < 90; i++){ x = rnd() * 1920; y = rnd() * 1080; var r = 5 + rnd() * 10; c.beginPath(); c.moveTo(x, y - r); c.lineTo(x + r * 0.25, y - r * 0.25); c.lineTo(x + r, y); c.lineTo(x + r * 0.25, y + r * 0.25); c.lineTo(x, y + r); c.lineTo(x - r * 0.25, y + r * 0.25); c.lineTo(x - r, y); c.lineTo(x - r * 0.25, y - r * 0.25); c.closePath(); c.fill(); } }
    else if (kind === "grid"){ for (x = 0; x < 1920; x += 80){ c.beginPath(); c.moveTo(x, 0); c.lineTo(x, 1080); c.stroke(); } for (y = 0; y < 1080; y += 80){ c.beginPath(); c.moveTo(0, y); c.lineTo(1920, y); c.stroke(); } }
    else if (kind === "diamond"){ for (y = 0; y < 1180; y += 90) for (x = (y / 90) % 2 ? 45 : 0; x < 1920; x += 90){ c.beginPath(); c.moveTo(x, y - 18); c.lineTo(x + 18, y); c.lineTo(x, y + 18); c.lineTo(x - 18, y); c.closePath(); c.stroke(); } }
    else if (kind === "waves"){ for (y = 60; y < 1080; y += 70){ c.beginPath(); for (x = 0; x <= 1920; x += 20) c.lineTo(x, y + Math.sin(x * 0.03 + y) * 8); c.stroke(); } }
    else if (kind === "leaves"){ for (var j = 0; j < 60; j++){ x = rnd() * 1920; y = rnd() * 1080; c.save(); c.translate(x, y); c.rotate(rnd() * 6.28); c.beginPath(); c.ellipse(0, 0, 18, 8, 0, 0, 6.283); c.fill(); c.restore(); } }
    else if (kind === "stripes"){ for (x = -1080; x < 1920; x += 60){ c.beginPath(); c.moveTo(x, 1080); c.lineTo(x + 1080, 0); c.lineWidth = 14; c.stroke(); } }
    c.restore();
  }

  function base(c, a, b){ var g = c.createLinearGradient(0, 0, 0, 1080); g.addColorStop(0, a); g.addColorStop(1, b); c.fillStyle = g; c.fillRect(0, 0, 1920, 1080); }
  function hillLayer(c, y0, amp, col, k, ph){ c.fillStyle = col; c.beginPath(); c.moveTo(0, 1080); for (var x = 0; x <= 1920; x += 20) c.lineTo(x, y0 + Math.sin(x * k + ph) * amp + Math.sin(x * k * 2.3 + ph * 2) * amp * 0.4); c.lineTo(1920, 1080); c.closePath(); c.fill(); }

  function buildStatic(TK){
    var C = colors(TK), kind = A.bg, dark = lum(C.bg1) < 0.5, pc = dark ? "#ffffff" : C.text;
    CV.base = layer(function(c){
      base(c, C.bg1, C.bg2);
      if (kind === "hills"){
        c.fillStyle = rgba("#ffffff", 0.55); c.beginPath(); c.arc(1560, 220, 110, 0, 6.283); c.fill();
        hillLayer(c, 780, 40, mix(C.bg2, C.accent, 0.25), 0.004, 1); hillLayer(c, 860, 36, mix(C.bg2, C.primary, 0.35), 0.006, 3); hillLayer(c, 950, 28, mix(C.bg2, C.accent, 0.5), 0.009, 5);
        for (var i = 0; i < 26; i++){ var fx = rnd() * 1920, fy = 900 + rnd() * 150; c.fillStyle = i % 2 ? C.primary : "#ffffff"; c.beginPath(); c.arc(fx, fy, 6 + rnd() * 6, 0, 6.283); c.fill(); }
      } else if (kind === "ink"){
        c.fillStyle = rgba(C.primary, 0.85); c.beginPath(); c.arc(1480, 250, 96, 0, 6.283); c.fill();
        hillLayer(c, 620, 90, rgba(C.text, 0.12), 0.003, 2); hillLayer(c, 740, 80, rgba(C.text, 0.2), 0.004, 4); hillLayer(c, 880, 60, rgba(C.text, 0.32), 0.006, 6);
      } else if (kind === "city"){
        c.fillStyle = rgba("#ffffff", 0.85); c.beginPath(); c.arc(1500, 230, 70, 0, 6.283); c.fill(); c.fillStyle = C.bg1; c.beginPath(); c.arc(1530, 215, 62, 0, 6.283); c.fill();
        var x = 0; CV.win = [];
        while (x < 1920){ var w = 90 + rnd() * 130, h = 200 + rnd() * 330; c.fillStyle = mix(C.bg1, "#000000", 0.35 + rnd() * 0.3); c.fillRect(x, 1000 - h, w, h + 80);
          for (var wy = 1000 - h + 24; wy < 990; wy += 40) for (var wx = x + 14; wx < x + w - 20; wx += 30) if (rnd() > 0.55) CV.win.push([wx, wy]);
          x += w + 6; }
      } else if (kind === "pitch"){
        for (var s = 0; s < 16; s++){ c.fillStyle = s % 2 ? rgba("#ffffff", 0.05) : rgba("#000000", 0.07); c.fillRect(s * 120, 0, 120, 1080); }
        c.strokeStyle = rgba("#ffffff", 0.35); c.lineWidth = 8; c.beginPath(); c.ellipse(960, 700, 340, 120, 0, 0, 6.283); c.stroke(); c.beginPath(); c.moveTo(0, 700); c.lineTo(1920, 700); c.stroke();
      } else if (kind === "waves"){
        c.fillStyle = rgba("#ffffff", 0.8); c.beginPath(); c.arc(1600, 200, 90, 0, 6.283); c.fill();
      }
      if (kind === "neongrid"){
        var hz = 640, gg = c.createLinearGradient(0, hz - 260, 0, hz); gg.addColorStop(0, rgba(C.accent, 0)); gg.addColorStop(1, rgba(C.accent, 0.38)); c.fillStyle = gg; c.fillRect(0, hz - 260, 1920, 260);
        c.fillStyle = rgba(C.bg1, 0.9); c.fillRect(0, hz, 1920, 440);
        c.strokeStyle = rgba(C.primary, 0.55); c.lineWidth = 2;
        for (var gi = -24; gi <= 24; gi++){ c.beginPath(); c.moveTo(960 + gi * 40, hz); c.lineTo(960 + gi * 300, 1080); c.stroke(); }
        for (var gj = 0; gj < 12; gj++){ var gy = hz + Math.pow(gj / 11, 2.2) * 440; c.beginPath(); c.moveTo(0, gy); c.lineTo(1920, gy); c.stroke(); }
        c.fillStyle = rgba(C.accent, 0.9); c.beginPath(); c.arc(960, hz - 40, 150, Math.PI, 0); c.fill();
        c.fillStyle = rgba(C.bg1, 0.55); for (var sl = 0; sl < 7; sl++) c.fillRect(810, hz - 190 + sl * 24 + sl * sl * 2, 300, 4 + sl);
      }
      if (kind === "memphis"){
        var mc = [C.primary, C.accent, "#ffffff", mix(C.primary, "#ffe14a", 0.5), mix(C.accent, "#ffffff", 0.4)];
        for (var mi = 0; mi < 40; mi++){
          var mx = rnd() * 1920, my = rnd() * 1080, ms = 28 + rnd() * 70, mt = mi % 4;
          for (var tryn = 0; tryn < 14 && !clear(mx, my, ms * 0.8); tryn++){ mx = rnd() * 1920; my = rnd() * 1080; }   /* never behind the title / question / answers */
          if (!clear(mx, my, ms * 0.8)) continue; c.save(); c.translate(mx, my); c.rotate(rnd() * 6.28); c.fillStyle = mc[mi % mc.length]; c.strokeStyle = C.text; c.lineWidth = 5;
          if (mt === 0){ c.beginPath(); c.arc(0, 0, ms * 0.5, 0, 6.283); c.fill(); c.stroke(); }
          else if (mt === 1){ c.beginPath(); c.moveTo(0, -ms * 0.6); c.lineTo(ms * 0.55, ms * 0.4); c.lineTo(-ms * 0.55, ms * 0.4); c.closePath(); c.fill(); c.stroke(); }
          else if (mt === 2){ c.beginPath(); for (var zz = -3; zz <= 3; zz++) c.lineTo(zz * ms * 0.2, (zz % 2 ? -1 : 1) * ms * 0.18); c.lineWidth = 9; c.stroke(); }
          else { c.fillRect(-ms * 0.12, -ms * 0.5, ms * 0.24, ms); c.fillRect(-ms * 0.5, -ms * 0.12, ms, ms * 0.24); }
          c.restore();
        }
      }
      if (kind === "bunting"){
        var bc = [C.primary, C.accent, "#5cc8ff", "#7dff9a", "#ffffff"];
        for (var bi = 0; bi < 2; bi++){
          var by0 = 120 + bi * 120; c.strokeStyle = rgba("#ffffff", 0.7); c.lineWidth = 4; c.beginPath(); c.moveTo(0, by0); c.quadraticCurveTo(960, by0 + 150, 1920, by0); c.stroke();
          for (var fi = 0; fi < 22; fi++){ var ft = (fi + 0.5) / 22, fx = ft * 1920, fy = (1 - ft) * (1 - ft) * by0 + 2 * ft * (1 - ft) * (by0 + 150) + ft * ft * by0; c.fillStyle = bc[(fi + bi) % bc.length]; c.beginPath(); c.moveTo(fx - 30, fy); c.lineTo(fx + 30, fy); c.lineTo(fx, fy + 62); c.closePath(); c.fill(); }
        }
        var bl = [[110, 860, C.primary], [1800, 840, C.accent], [260, 720, "#5cc8ff"], [1690, 700, "#7dff9a"]];
        for (var li = 0; li < bl.length; li++){ c.fillStyle = bl[li][2]; c.beginPath(); c.ellipse(bl[li][0], bl[li][1], 56, 70, 0, 0, 6.283); c.fill(); c.strokeStyle = rgba("#ffffff", 0.7); c.lineWidth = 4; c.beginPath(); c.moveTo(bl[li][0], bl[li][1] + 70); c.quadraticCurveTo(bl[li][0] + 24, bl[li][1] + 150, bl[li][0], bl[li][1] + 220); c.stroke(); }
      }
      if (kind === "stage"){
        c.fillStyle = rgba("#000000", 0.35); c.fillRect(0, 118, 1920, 18);
        for (var sr = 0; sr < 9; sr++) for (var sc = 0; sc < 30; sc++){ c.fillStyle = rgba(sc % 2 ? C.accent : C.primary, 0.1 + ((sr + sc) % 5) * 0.03); c.fillRect(46 + sc * 62, 160 + sr * 62, 40, 40); }
        var fg = c.createLinearGradient(0, 860, 0, 1080); fg.addColorStop(0, rgba(C.primary, 0.3)); fg.addColorStop(1, rgba("#000000", 0.7)); c.fillStyle = fg; c.fillRect(0, 860, 1920, 220);
        c.fillStyle = rgba(C.primary, 0.9); c.fillRect(0, 856, 1920, 6);
      }
      if (kind === "speed"){
        c.save(); c.translate(960, 500);
        for (var sp = 0; sp < 64; sp++){ var sa = sp * 0.0982 + rnd() * 0.04, w0 = 0.02 + rnd() * 0.03; c.fillStyle = rgba(sp % 3 ? "#ffffff" : C.primary, 0.22); c.beginPath(); c.moveTo(Math.cos(sa) * 360, Math.sin(sa) * 360); c.lineTo(Math.cos(sa - w0) * 1700, Math.sin(sa - w0) * 1700); c.lineTo(Math.cos(sa + w0) * 1700, Math.sin(sa + w0) * 1700); c.closePath(); c.fill(); }
        c.restore();
        c.fillStyle = rgba(C.accent, 0.35); for (var hy = 0; hy < 14; hy++) for (var hx = 0; hx < 12; hx++){ var hr = Math.max(0, 14 - hx * 1.3 - hy * 0.6); if (hr > 1){ c.beginPath(); c.arc(40 + hx * 36, 1040 - hy * 36, hr * 0.8, 0, 6.283); c.fill(); c.beginPath(); c.arc(1880 - hx * 36, 1040 - hy * 36, hr * 0.8, 0, 6.283); c.fill(); } }
      }
      if (kind === "pixel"){
        var pc2 = document.createElement("canvas"); pc2.width = 80; pc2.height = 45; var pg = pc2.getContext("2d");
        for (var py = 0; py < 45; py++){ pg.fillStyle = mix(C.bg1, C.bg2, py / 45); pg.fillRect(0, py, 80, 1); }
        pg.fillStyle = mix(C.accent, "#ffffff", 0.2); pg.fillRect(60, 6, 6, 6); pg.fillRect(61, 5, 4, 8); pg.fillRect(59, 7, 8, 4);
        pg.fillStyle = mix(C.bg2, "#000000", 0.35); var hh = 0; for (var px = 0; px < 80; px++){ hh = 30 + Math.round(Math.sin(px * 0.19) * 3 + Math.sin(px * 0.07) * 4); pg.fillRect(px, hh, 1, 45 - hh); }
        pg.fillStyle = mix(C.primary, C.bg1, 0.55); for (var px2 = 0; px2 < 80; px2++){ var h2 = 38 + Math.round(Math.sin(px2 * 0.3 + 1) * 2); pg.fillRect(px2, h2, 1, 45 - h2); }
        pg.fillStyle = "#ffffff"; for (var sk = 0; sk < 26; sk++) pg.fillRect(Math.floor(rnd() * 80), Math.floor(rnd() * 24), 1, 1);
        c.imageSmoothingEnabled = false; c.drawImage(pc2, 0, 0, 80, 45, 0, 0, 1920, 1080);
        c.fillStyle = rgba("#000000", 0.12); for (var sy = 0; sy < 1080; sy += 8) c.fillRect(0, sy, 1920, 2);
      }
      if (kind === "minimal"){
        c.strokeStyle = rgba(C.text, 0.14); c.lineWidth = 2; c.beginPath(); c.moveTo(160, 120); c.lineTo(1760, 120); c.moveTo(160, 1020); c.lineTo(1760, 1020); c.stroke();
        c.strokeStyle = rgba(C.accent, 0.5); c.lineWidth = 3; c.beginPath(); c.arc(1980, 1180, 560, Math.PI, Math.PI * 1.5); c.stroke(); c.beginPath(); c.arc(1980, 1180, 640, Math.PI, Math.PI * 1.5); c.stroke();
        c.fillStyle = rgba(C.accent, 0.8); c.fillRect(160, 112, 120, 8);
      }
      if (kind === "chalk"){
        c.fillStyle = rgba("#ffffff", 0.05); for (var ck = 0; ck < 12; ck++){ c.beginPath(); c.ellipse(rnd() * 1920, rnd() * 1000, 160 + rnd() * 260, 40 + rnd() * 80, rnd() * 3, 0, 6.283); c.fill(); }
        c.strokeStyle = "#8a5a2b"; c.lineWidth = 30; c.strokeRect(15, 15, 1890, 1050); c.strokeStyle = "#5a3818"; c.lineWidth = 6; c.strokeRect(30, 30, 1860, 1020);
        c.fillStyle = "#6e4420"; c.fillRect(15, 1040, 1890, 40);
        c.fillStyle = "#f5f5ef"; c.fillRect(1500, 1022, 70, 14); c.fillStyle = "#ffe066"; c.fillRect(1600, 1022, 60, 14); c.fillStyle = "#ff9e9e"; c.fillRect(1690, 1022, 50, 14);
      }
      pattern(c, A.pattern, pc);
    });
    ready = true;
  }

  function loadIcons(TK){
    try { document.body.setAttribute("data-auto", "1"); document.body.style.setProperty("--ts-pat", A.pat || "none"); document.body.style.setProperty("--ts-pat-back", A.patBack || "none"); } catch (e) {}
    COMP.emblem = A.emblem || "";
    A.props.forEach(function(n){
      var svg = String(A.icons[n] || "");
      if (!/<svg[^>]* width=/.test(svg)) svg = svg.replace("<svg ", '<svg width="96" height="96" ');
      var im = new Image(); im.onload = function(){ imgs[n] = im; }; im.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    });
  }
  var SLOTS = [[40, 170, 150], [28, 410, 120], [60, 620, 140], [1780, 190, 150], [1765, 450, 130], [1778, 720, 140], [1785, 920, 120]];

  function drawProps(ctx, t, TK){
    var C = colors(TK), glow = C.accent;
    A.props.forEach(function(n, i){
      var im = imgs[n], sl = SLOTS[i % SLOTS.length]; if (!im) return;
      var bob = Math.sin(t * 0.9 + i * 1.3) * 14, sz = sl[2] * (1 + S.cheer * 0.18), x = sl[0] + 10, y = sl[1] + bob;
      var g = ctx.createRadialGradient(x + sz / 2, y + sz / 2, 4, x + sz / 2, y + sz / 2, sz * 0.8); g.addColorStop(0, rgba(glow, 0.28 + S.cheer * 0.3)); g.addColorStop(1, rgba(glow, 0));
      ctx.fillStyle = g; ctx.fillRect(x - sz * 0.4, y - sz * 0.4, sz * 1.8, sz * 1.8);
      ctx.save(); ctx.translate(x + sz / 2, y + sz / 2); ctx.rotate(Math.sin(t * 0.6 + i) * 0.12); ctx.globalAlpha = 0.92; ctx.drawImage(im, -sz / 2, -sz / 2, sz, sz); ctx.restore();
    });
  }

  function dyn(ctx, t, dt, TK){
    var C = colors(TK), kind = A.bg, i, x, y, g;
    if (kind === "aurora"){
      for (i = 0; i < 3; i++){ g = ctx.createLinearGradient(0, 120, 0, 560); var ac = i % 2 ? C.accent : C.primary; g.addColorStop(0, rgba(ac, 0)); g.addColorStop(0.5, rgba(ac, 0.22)); g.addColorStop(1, rgba(ac, 0));
        ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, 560); for (x = 0; x <= 1920; x += 40) ctx.lineTo(x, 300 + i * 50 + Math.sin(x * 0.004 + t * 0.4 + i * 2) * 90); ctx.lineTo(1920, 560); ctx.closePath(); ctx.fill(); }
      if (!CV.stars){ CV.stars = []; for (i = 0; i < 170; i++) CV.stars.push([rnd() * 1920, rnd() * 1000, rnd(), rnd() * 6.28]); }
      ctx.fillStyle = "#ffffff"; for (i = 0; i < CV.stars.length; i++){ var s = CV.stars[i]; ctx.globalAlpha = 0.25 + 0.75 * s[2] * (0.6 + 0.4 * Math.sin(t * 2 + s[3])); ctx.fillRect(s[0], s[1], 1.5 + s[2] * 2.5, 1.5 + s[2] * 2.5); }
      ctx.globalAlpha = 1;
      var px = 1560 + Math.sin(t * 0.15) * 14, py = 780; ctx.fillStyle = mix(C.bg2, C.accent, 0.5); ctx.beginPath(); ctx.arc(px, py, 150, 0, 6.283); ctx.fill();
      ctx.fillStyle = rgba("#ffffff", 0.12); ctx.beginPath(); ctx.arc(px - 40, py - 40, 110, 0, 6.283); ctx.fill();
      ctx.strokeStyle = rgba(C.primary, 0.6); ctx.lineWidth = 10; ctx.beginPath(); ctx.ellipse(px, py, 260, 44, -0.3, 0, 6.283); ctx.stroke();
    } else if (kind === "waves"){
      for (i = 0; i < 4; i++){ ctx.fillStyle = rgba(i % 2 ? "#ffffff" : C.accent, 0.12 + i * 0.05); ctx.beginPath(); ctx.moveTo(0, 1080);
        for (x = 0; x <= 1920; x += 24) ctx.lineTo(x, 800 + i * 55 + Math.sin(x * 0.006 + t * (0.7 + i * 0.2) + i * 2) * (26 - i * 3)); ctx.lineTo(1920, 1080); ctx.closePath(); ctx.fill(); }
      if (!CV.bub){ CV.bub = []; for (i = 0; i < 26; i++) CV.bub.push([rnd() * 1920, 700 + rnd() * 380, 5 + rnd() * 12, 20 + rnd() * 40]); }
      ctx.strokeStyle = rgba("#ffffff", 0.5); ctx.lineWidth = 3;
      for (i = 0; i < CV.bub.length; i++){ var b = CV.bub[i]; b[1] -= b[3] * dt; if (b[1] < 120){ b[1] = 1080; b[0] = rnd() * 1920; } ctx.beginPath(); ctx.arc(b[0] + Math.sin(t + i) * 12, b[1], b[2], 0, 6.283); ctx.stroke(); }
    } else if (kind === "hills"){
      if (!CV.cl){ CV.cl = []; for (i = 0; i < 6; i++) CV.cl.push([rnd() * 1920, 90 + rnd() * 300, 0.6 + rnd() * 0.8, 10 + rnd() * 16]); }
      ctx.fillStyle = rgba("#ffffff", 0.7);
      for (i = 0; i < CV.cl.length; i++){ var cl = CV.cl[i]; cl[0] += cl[3] * dt; if (cl[0] > 2100) cl[0] = -220; ctx.beginPath(); ctx.arc(cl[0], cl[1], 46 * cl[2], 0, 6.283); ctx.arc(cl[0] + 56 * cl[2], cl[1] + 8, 58 * cl[2], 0, 6.283); ctx.arc(cl[0] + 118 * cl[2], cl[1] + 12, 42 * cl[2], 0, 6.283); ctx.fill(); }
    } else if (kind === "city"){
      if (CV.win){ ctx.fillStyle = C.primary; for (i = 0; i < CV.win.length; i++){ var w = CV.win[i]; ctx.globalAlpha = 0.35 + 0.4 * (Math.sin(t * 1.3 + i * 7.1) > 0.2 ? 1 : 0.2); ctx.fillRect(w[0], w[1], 14, 20); } ctx.globalAlpha = 1; }
      ctx.globalCompositeOperation = "lighter";
      for (i = 0; i < 2; i++){ var ang = Math.sin(t * 0.5 + i * 3) * 0.5, x0 = 400 + i * 1100; ctx.fillStyle = rgba("#ffffff", 0.07); ctx.beginPath(); ctx.moveTo(x0 - 14, 1000); ctx.lineTo(x0 + 14, 1000); ctx.lineTo(x0 + 14 + Math.sin(ang) * 900 + 120, 0); ctx.lineTo(x0 - 14 + Math.sin(ang) * 900 - 120, 0); ctx.closePath(); ctx.fill(); }
      ctx.globalCompositeOperation = "source-over";
      g = ctx.createLinearGradient(0, 760, 0, 1080); g.addColorStop(0, rgba(C.bg2, 0)); g.addColorStop(1, rgba(C.bg2, 0.8)); ctx.fillStyle = g; ctx.fillRect(0, 760, 1920, 320);
    } else if (kind === "bokeh"){
      if (!CV.bk){ CV.bk = []; for (i = 0; i < 38; i++) CV.bk.push([rnd() * 1920, rnd() * 1080, 14 + rnd() * 60, 6 + rnd() * 20, rnd() * 6.28]); }
      ctx.globalCompositeOperation = "lighter";
      for (i = 0; i < CV.bk.length; i++){ var k = CV.bk[i]; k[1] -= k[3] * dt; if (k[1] < -80) { k[1] = 1160; k[0] = rnd() * 1920; } g = ctx.createRadialGradient(k[0], k[1], 0, k[0], k[1], k[2]); g.addColorStop(0, rgba(C.primary, 0.32 + 0.12 * Math.sin(t + k[4]))); g.addColorStop(1, rgba(C.primary, 0)); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(k[0], k[1], k[2], 0, 6.283); ctx.fill(); }
      for (i = 0; i < 5; i++){ ctx.fillStyle = rgba(C.accent, 0.05); ctx.beginPath(); ctx.moveTo(300 + i * 330 - 20, 0); ctx.lineTo(300 + i * 330 + 20, 0); ctx.lineTo(300 + i * 330 + 160 + Math.sin(t * 0.4 + i) * 60, 1080); ctx.lineTo(300 + i * 330 - 160 + Math.sin(t * 0.4 + i) * 60, 1080); ctx.closePath(); ctx.fill(); }
      ctx.globalCompositeOperation = "source-over";
    } else if (kind === "sunburst"){
      ctx.save(); ctx.translate(960, 300); ctx.rotate(t * 0.03); ctx.fillStyle = rgba("#ffffff", 0.16);
      for (i = 0; i < 16; i++){ ctx.rotate(6.283 / 16); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-90, -1500); ctx.lineTo(90, -1500); ctx.closePath(); ctx.fill(); } ctx.restore();
      if (!CV.bl){ CV.bl = []; for (i = 0; i < 12; i++) CV.bl.push([rnd() * 1920, rnd() * 1080, 40 + rnd() * 110, 6 + rnd() * 10, i % 2 ? C.primary : C.accent]); }
      for (i = 0; i < CV.bl.length; i++){ var bl = CV.bl[i]; bl[1] -= bl[3] * dt; if (bl[1] < -140) bl[1] = 1220; ctx.fillStyle = rgba(bl[4], 0.14); ctx.beginPath(); ctx.arc(bl[0] + Math.sin(t * 0.4 + i) * 20, bl[1], bl[2], 0, 6.283); ctx.fill(); }
    } else if (kind === "ink"){
      for (i = 0; i < 3; i++){ var mx = ((t * (14 + i * 6) + i * 700) % 2400) - 240; g = ctx.createLinearGradient(mx, 0, mx + 600, 0); g.addColorStop(0, rgba("#ffffff", 0)); g.addColorStop(0.5, rgba("#ffffff", 0.32)); g.addColorStop(1, rgba("#ffffff", 0)); ctx.fillStyle = g; ctx.fillRect(mx, 520 + i * 120, 600, 70); }
    } else if (kind === "pitch"){
      ctx.globalCompositeOperation = "lighter";
      for (i = 0; i < 3; i++){ var a2 = Math.sin(t * 0.7 + i * 2) * 0.4, x1 = 300 + i * 660; ctx.fillStyle = rgba("#ffffff", 0.07 + S.cheer * 0.1); ctx.beginPath(); ctx.moveTo(x1 - 16, 0); ctx.lineTo(x1 + 16, 0); ctx.lineTo(x1 + 220 + Math.sin(a2) * 500, 1000); ctx.lineTo(x1 - 220 + Math.sin(a2) * 500, 1000); ctx.closePath(); ctx.fill(); }
      ctx.globalCompositeOperation = "source-over";
    } else if (kind === "geometric"){
      if (!CV.geo){ CV.geo = []; for (i = 0; i < 22; i++) CV.geo.push([rnd() * 1920, rnd() * 1080, 30 + rnd() * 70, rnd() * 6.28, 3 + Math.floor(rnd() * 4), (rnd() - 0.5) * 0.4]); }
      ctx.lineWidth = 3;
      for (i = 0; i < CV.geo.length; i++){ var q = CV.geo[i]; q[3] += q[5] * dt; q[1] -= 6 * dt; if (q[1] < -100) q[1] = 1180; ctx.strokeStyle = rgba(i % 2 ? C.accent : C.primary, 0.3); ctx.beginPath();
        for (var v = 0; v <= q[4]; v++){ var an = q[3] + v * 6.283 / q[4]; ctx.lineTo(q[0] + Math.cos(an) * q[2], q[1] + Math.sin(an) * q[2]); } ctx.stroke(); }
    } else if (kind === "neongrid"){
      ctx.globalCompositeOperation = "lighter"; var sy2 = 640 + ((t * 80) % 440); ctx.fillStyle = rgba(C.primary, 0.12); ctx.fillRect(0, sy2, 1920, 6);
      if (!CV.sp) { CV.sp = []; for (i = 0; i < 60; i++) CV.sp.push([rnd() * 1920, rnd() * 560, rnd(), rnd() * 6.28]); }
      for (i = 0; i < CV.sp.length; i++){ var s2 = CV.sp[i]; ctx.fillStyle = rgba("#ffffff", 0.2 + 0.6 * s2[2] * (0.5 + 0.5 * Math.sin(t * 2 + s2[3]))); ctx.fillRect(s2[0], s2[1], 3, 3); }
      ctx.globalCompositeOperation = "source-over";
    } else if (kind === "bunting" || kind === "memphis"){
      if (!CV.cf) { CV.cf = []; for (i = 0; i < (kind === "bunting" ? 46 : 18); i++) CV.cf.push([rnd() * 1920, rnd() * 1080, 14 + rnd() * 26, 30 + rnd() * 50, rnd() * 6.28, i % 3]); }
      for (i = 0; i < CV.cf.length; i++){ var f2 = CV.cf[i]; f2[1] += f2[3] * dt; f2[4] += dt * 2; if (f2[1] > 1120){ f2[1] = -40; f2[0] = rnd() * 1920; } ctx.save(); ctx.translate(f2[0] + Math.sin(t + i) * 18, f2[1]); ctx.rotate(f2[4]); ctx.fillStyle = f2[5] === 0 ? C.primary : (f2[5] === 1 ? C.accent : "#ffffff"); ctx.globalAlpha = clear(f2[0], f2[1], f2[2]) ? 0.85 : 0.22; ctx.fillRect(-f2[2] / 2, -f2[2] / 4, f2[2], f2[2] / 2); ctx.restore(); }
    } else if (kind === "stage"){
      ctx.globalCompositeOperation = "lighter";
      for (i = 0; i < 3; i++){ var an2 = Math.sin(t * 0.6 + i * 2.1) * 0.5, x3 = 400 + i * 560; ctx.fillStyle = rgba(i % 2 ? C.accent : C.primary, 0.09); ctx.beginPath(); ctx.moveTo(x3 - 18, 120); ctx.lineTo(x3 + 18, 120); ctx.lineTo(x3 + 230 + Math.sin(an2) * 420, 900); ctx.lineTo(x3 - 230 + Math.sin(an2) * 420, 900); ctx.closePath(); ctx.fill(); }
      for (i = 0; i < 24; i++){ ctx.fillStyle = rgba(i % 2 ? C.accent : C.primary, 0.06 + 0.12 * Math.max(0, Math.sin(t * 3 + i * 1.7))); ctx.fillRect(46 + ((i * 7) % 30) * 62, 160 + ((i * 5) % 9) * 62, 40, 40); }
      ctx.globalCompositeOperation = "source-over";
    } else if (kind === "glassblobs"){
      if (!CV.gb){ CV.gb = []; var gc = [C.primary, C.accent, "#6a7bff", "#ff9a6b", "#7cf2e6", "#c06bff"]; for (i = 0; i < 6; i++) CV.gb.push([rnd() * 1920, rnd() * 1080, 240 + rnd() * 260, rnd() * 6.28, gc[i]]); }
      for (i = 0; i < CV.gb.length; i++){ var b2 = CV.gb[i], bx2 = b2[0] + Math.sin(t * 0.25 + b2[3]) * 160, by2 = b2[1] + Math.cos(t * 0.2 + b2[3]) * 110; g = ctx.createRadialGradient(bx2 - b2[2] * 0.3, by2 - b2[2] * 0.3, 10, bx2, by2, b2[2]); g.addColorStop(0, rgba(b2[4], 0.55)); g.addColorStop(1, rgba(b2[4], 0)); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(bx2, by2, b2[2], 0, 6.283); ctx.fill();
        ctx.strokeStyle = "rgba(255,255,255,.12)"; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(bx2, by2, b2[2] * 0.62, 0.3, 2.2); ctx.stroke(); }
    } else if (kind === "speed"){
      ctx.fillStyle = rgba("#ffffff", 0.06 + 0.05 * Math.sin(t * 6)); ctx.fillRect(0, 0, 1920, 1080);
    } else if (kind === "pixel"){
      if (!CV.px) { CV.px = []; for (i = 0; i < 22; i++) CV.px.push([Math.floor(rnd() * 120) * 16, Math.floor(rnd() * 40) * 16, rnd() * 6.28]); }
      for (i = 0; i < CV.px.length; i++){ var q2 = CV.px[i]; ctx.fillStyle = rgba("#ffffff", 0.2 + 0.7 * Math.max(0, Math.sin(t * 3 + q2[2]))); ctx.fillRect(q2[0], q2[1], 8, 8); }
    } else if (kind === "minimal" || kind === "chalk"){
      if (kind === "chalk"){ if (!CV.du){ CV.du = []; for (i = 0; i < 40; i++) CV.du.push([rnd() * 1920, rnd() * 1000, 6 + rnd() * 10, rnd() * 6.28]); }
        for (i = 0; i < CV.du.length; i++){ var d2 = CV.du[i]; d2[1] -= d2[2] * dt; if (d2[1] < 40) d2[1] = 1000; ctx.fillStyle = rgba("#ffffff", 0.12 + 0.1 * Math.sin(t + d2[3])); ctx.fillRect(d2[0] + Math.sin(t * 0.5 + d2[3]) * 20, d2[1], 4, 4); } }
    } else {
      if (!CV.bm){ CV.bm = []; for (i = 0; i < 7; i++) CV.bm.push([rnd() * 1920, rnd() * 1080, 260 + rnd() * 320, 8 + rnd() * 14, rnd() * 6.28, i % 2 ? C.accent : C.primary]); }
      for (i = 0; i < CV.bm.length; i++){ var m = CV.bm[i], mx2 = m[0] + Math.sin(t * 0.2 + m[4]) * 120, my2 = m[1] + Math.cos(t * 0.17 + m[4]) * 80; g = ctx.createRadialGradient(mx2, my2, 0, mx2, my2, m[2]); g.addColorStop(0, rgba(m[5], 0.32)); g.addColorStop(1, rgba(m[5], 0)); ctx.fillStyle = g; ctx.fillRect(mx2 - m[2], my2 - m[2], m[2] * 2, m[2] * 2); }
    }
  }

  /* signature element: one request-specific picture (A.sig), drawn procedurally, large and partly hidden behind the cards */
  function drawSig(ctx, t, TK){
    var C = colors(TK), g, i, k = A.sig;
    if (!k) return;
    ctx.save();
    if (k === "solar" && A.style === "minimal-premium"){
      ctx.fillStyle = C.accent; ctx.beginPath(); ctx.arc(150, 1000, 120, 0, 6.283); ctx.fill();
      ctx.strokeStyle = rgba(C.text, 0.55); ctx.lineWidth = 2;
      var mr = [210, 320, 450, 600, 780];
      for (i = 0; i < 5; i++){
        ctx.beginPath(); ctx.ellipse(150, 1000, mr[i], mr[i] * 0.42, -0.1, 0, 6.283); ctx.stroke();
        var ma = t * (0.25 - i * 0.035) + i * 1.7; ctx.fillStyle = C.text; ctx.beginPath(); ctx.arc(150 + Math.cos(ma) * mr[i], 1000 + Math.sin(ma) * mr[i] * 0.42, 7 + i * 2.5, 0, 6.283); ctx.fill();
      }
    } else if (k === "solar"){
      g = ctx.createRadialGradient(150, 1000, 40, 150, 1000, 340); g.addColorStop(0, "#fff3b0"); g.addColorStop(0.35, "#ffb02e"); g.addColorStop(1, "rgba(255,120,30,0)");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(150, 1000, 340, 0, 6.283); ctx.fill();
      ctx.fillStyle = "#ffd25a"; ctx.beginPath(); ctx.arc(150, 1000, 210, 0, 6.283); ctx.fill();
      var cols = ["#b9a79a", "#e8b36a", "#4aa3df", "#d9674a", "#e0b070"], rr = [330, 470, 620, 790, 980];
      for (i = 0; i < 5; i++){
        ctx.strokeStyle = "rgba(255,255,255,.16)"; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(150, 1000, rr[i], rr[i] * 0.42, -0.1, 0, 6.283); ctx.stroke();
        var a = t * (0.35 - i * 0.05) + i * 1.7, px = 150 + Math.cos(a) * rr[i], py = 1000 + Math.sin(a) * rr[i] * 0.42 - Math.cos(a) * 20;
        ctx.fillStyle = cols[i]; ctx.beginPath(); ctx.arc(px, py, 20 + i * 5, 0, 6.283); ctx.fill();
        if (i === 4){ ctx.strokeStyle = "rgba(255,230,180,.8)"; ctx.lineWidth = 6; ctx.beginPath(); ctx.ellipse(px, py, 56, 14, -0.3, 0, 6.283); ctx.stroke(); }
      }
    } else if (k === "island"){
      var wy = 880;
      ctx.fillStyle = "rgba(10,60,110,.55)"; ctx.fillRect(1100, wy, 820, 200);
      ctx.fillStyle = "#6d7a86"; ctx.beginPath(); ctx.moveTo(1380, wy + 30); ctx.lineTo(1470, wy - 190); ctx.lineTo(1520, wy - 150); ctx.lineTo(1560, wy - 230); ctx.lineTo(1680, wy + 30); ctx.closePath(); ctx.fill();
      ctx.fillStyle = "#4f5d68"; ctx.beginPath(); ctx.moveTo(1700, wy + 30); ctx.lineTo(1760, wy - 110); ctx.lineTo(1830, wy - 70); ctx.lineTo(1900, wy + 30); ctx.closePath(); ctx.fill();
      ctx.fillStyle = "#3f9a58"; ctx.beginPath(); ctx.ellipse(1520, wy - 150, 40, 12, 0, 0, 6.283); ctx.ellipse(1560, wy - 232, 24, 8, 0, 0, 6.283); ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,.7)"; ctx.lineWidth = 5;
      for (i = 0; i < 4; i++){ ctx.beginPath(); for (var x = 1100; x <= 1920; x += 20) ctx.lineTo(x, wy + 36 + i * 30 + Math.sin(x * 0.02 + t * 1.4 + i) * 8); ctx.stroke(); }
      var bx = 1250 + Math.sin(t * 0.5) * 60, by = 330 + Math.sin(t * 1.1) * 12; ctx.strokeStyle = "#fff"; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(bx - 40, by); ctx.quadraticCurveTo(bx - 20, by - 26, bx, by); ctx.quadraticCurveTo(bx + 20, by - 26, bx + 40, by); ctx.stroke();
    } else if (k === "clock"){
      var cx = 1560, cy = 300, R = 190, now = t * 0.2;
      g = ctx.createRadialGradient(cx, cy, 20, cx, cy, R + 60); g.addColorStop(0, "rgba(255,216,107,.25)"); g.addColorStop(1, "rgba(255,216,107,0)"); ctx.fillStyle = g; ctx.fillRect(cx - R - 60, cy - R - 60, 2 * R + 120, 2 * R + 120);
      ctx.strokeStyle = "#e0b44c"; ctx.lineWidth = 12; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.stroke();
      ctx.lineWidth = 4; for (i = 0; i < 12; i++){ var an = i * 0.5236; ctx.beginPath(); ctx.moveTo(cx + Math.sin(an) * (R - 28), cy - Math.cos(an) * (R - 28)); ctx.lineTo(cx + Math.sin(an) * (R - 8), cy - Math.cos(an) * (R - 8)); ctx.stroke(); }
      ctx.fillStyle = "#fff4d6"; ctx.font = "900 54px serif"; ctx.textAlign = "center"; ctx.fillText("12", cx, cy - R + 84);
      ctx.strokeStyle = "#fff4d6"; ctx.lineWidth = 14; ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx, cy - 100); ctx.stroke();
      ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.sin(now) * 0 , cy - 140); ctx.stroke();
      ctx.fillStyle = "#e0b44c"; ctx.beginPath(); ctx.arc(cx, cy, 14, 0, 6.283); ctx.fill();
    } else if (k === "pyramid"){
      ctx.fillStyle = "rgba(255,190,90,.9)"; ctx.beginPath(); ctx.arc(1560, 260, 100, 0, 6.283); ctx.fill();
      var tri = [[1100, 1000, 300, 340, "#d9a35a"], [1420, 1000, 400, 440, "#e6b56b"], [1800, 1000, 240, 260, "#c9904a"]];
      for (i = 0; i < 3; i++){ var T = tri[i]; ctx.fillStyle = T[4]; ctx.beginPath(); ctx.moveTo(T[0] - T[2] / 2, T[1]); ctx.lineTo(T[0], T[1] - T[3]); ctx.lineTo(T[0] + T[2] / 2, T[1]); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "rgba(0,0,0,.18)"; ctx.beginPath(); ctx.moveTo(T[0], T[1] - T[3]); ctx.lineTo(T[0] + T[2] / 2, T[1]); ctx.lineTo(T[0], T[1]); ctx.closePath(); ctx.fill(); }
      ctx.fillStyle = "#c9904a"; ctx.fillRect(1000, 990, 920, 90);
    } else if (k === "mountain"){
      ctx.fillStyle = "rgba(255,255,255,.85)"; ctx.beginPath(); ctx.arc(1620, 230, 70, 0, 6.283); ctx.fill();
      var pk = [[1180, 1000, 420, 520, "#6b7f98"], [1560, 1000, 500, 640, "#566b86"], [1860, 1000, 360, 420, "#7a8da6"]];
      for (i = 0; i < 3; i++){ var P = pk[i]; ctx.fillStyle = P[4]; ctx.beginPath(); ctx.moveTo(P[0] - P[2] / 2, P[1]); ctx.lineTo(P[0], P[1] - P[3]); ctx.lineTo(P[0] + P[2] / 2, P[1]); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#ffffff"; ctx.beginPath(); ctx.moveTo(P[0], P[1] - P[3]); ctx.lineTo(P[0] - P[2] * 0.12, P[1] - P[3] * 0.78); ctx.lineTo(P[0] - P[2] * 0.03, P[1] - P[3] * 0.84); ctx.lineTo(P[0] + P[2] * 0.05, P[1] - P[3] * 0.76); ctx.lineTo(P[0] + P[2] * 0.12, P[1] - P[3] * 0.78); ctx.closePath(); ctx.fill(); }
    } else if (k === "palace"){
      ctx.fillStyle = "rgba(20,10,5,.55)"; var rx = 1180, ry = 760;
      ctx.beginPath(); ctx.moveTo(rx, ry + 40); ctx.quadraticCurveTo(rx + 120, ry + 40, rx + 260, ry - 70); ctx.lineTo(rx + 560, ry - 70); ctx.quadraticCurveTo(rx + 700, ry + 40, rx + 820, ry + 40); ctx.lineTo(rx + 760, ry + 70); ctx.lineTo(rx + 60, ry + 70); ctx.closePath(); ctx.fill();
      ctx.fillRect(rx + 120, ry + 70, 580, 270); ctx.fillStyle = "rgba(150,40,40,.7)"; for (i = 0; i < 6; i++) ctx.fillRect(rx + 140 + i * 95, ry + 80, 28, 250);
    }
    ctx.restore();
  }

  function spawn(kind, n, TK, burst){
    var C = colors(TK), pal = [C.primary, C.accent, "#ffffff", mix(C.primary, "#ffffff", 0.5)];
    for (var i = 0; i < n; i++){
      var p = { kind: kind, x: burst ? 960 + (Math.random() - 0.5) * 900 : Math.random() * 1920, y: burst ? 300 : -40, vx: (Math.random() - 0.5) * 220, vy: 120 + Math.random() * 260,
        rot: Math.random() * 6.28, vr: (Math.random() - 0.5) * 6, life: 2.4 + Math.random() * 1.6, size: 10 + Math.random() * 16, c: pal[i % pal.length], age: 0 };
      if (kind === "bubbles" || kind === "hearts"){ p.y = 1100; p.vy = -(120 + Math.random() * 180); }
      if (kind === "sparks"){ p.x = 960 + (Math.random() - 0.5) * 300; p.y = 420; var an = Math.random() * 6.28, sp = 300 + Math.random() * 500; p.vx = Math.cos(an) * sp; p.vy = Math.sin(an) * sp; p.life = 1; }
      if (kind === "gold"){ p.c = i % 2 ? "#ffd86b" : "#fff2c0"; p.vy = 160 + Math.random() * 200; }
      if (kind === "stars"){ p.c = i % 2 ? "#ffe066" : "#ffffff"; }
      if (kind === "petals"){ p.c = i % 2 ? "#ffb7d5" : "#ffffff"; p.vy = 90 + Math.random() * 120; }
      parts.push(p);
    }
    if (parts.length > 260) parts.splice(0, parts.length - 260);
  }
  function drawParts(ctx, dt){
    for (var i = parts.length - 1; i >= 0; i--){
      var p = parts[i]; p.age += dt; if (p.age > p.life || p.y > 1160 || p.y < -200){ parts.splice(i, 1); continue; }
      p.x += p.vx * dt + (p.kind === "petals" ? Math.sin(p.age * 3) * 40 * dt : 0); p.y += p.vy * dt; p.rot += p.vr * dt;
      if (p.kind === "sparks") { p.vx *= 0.97; p.vy *= 0.97; }
      ctx.save(); ctx.globalAlpha = Math.max(0, 1 - p.age / p.life); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.fillStyle = p.c; ctx.strokeStyle = p.c;
      var s = p.size;
      if (p.kind === "confetti" || p.kind === "gold") ctx.fillRect(-s / 2, -s / 4, s, s / 2);
      else if (p.kind === "stars"){ ctx.beginPath(); for (var k = 0; k < 10; k++){ var r = k % 2 ? s * 0.4 : s; ctx.lineTo(Math.cos(k * 0.6283) * r, Math.sin(k * 0.6283) * r); } ctx.closePath(); ctx.fill(); }
      else if (p.kind === "bubbles"){ ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, 0, s * 0.8, 0, 6.283); ctx.stroke(); }
      else if (p.kind === "petals"){ ctx.beginPath(); ctx.ellipse(0, 0, s * 0.7, s * 0.35, 0, 0, 6.283); ctx.fill(); }
      else if (p.kind === "hearts"){ ctx.beginPath(); ctx.moveTo(0, s * 0.4); ctx.bezierCurveTo(-s, -s * 0.3, -s * 0.4, -s, 0, -s * 0.4); ctx.bezierCurveTo(s * 0.4, -s, s, -s * 0.3, 0, s * 0.4); ctx.fill(); }
      else { ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(s * 0.8, 0); ctx.stroke(); }
      ctx.restore();
    }
  }

  /* parts mixing: the host may come from a ported theme (COMP.themes[id].host), staging (deco/reactions/sfx) from another */
  var hostSrc = A.host && A.host.theme && COMP.themes[A.host.theme] ? COMP.themes[A.host.theme].host : null;
  var stage = A.stage && COMP.themes[A.stage] ? COMP.themes[A.stage] : null;
  var host = A.host && (A.host.svg || A.host.theme) ? { svg: hostSrc ? hostSrc.svg : function(){ return A.host.svg; }, name: hostSrc ? hostSrc.name : A.host.name, lines: A.host.lines } : null;
  var built = false;
  return {
    host: host,
    hostCol: !!A.hostCol, podiums: !!(stage && stage.podiums),
    deco: function(TK){ return stage && stage.deco ? stage.deco(TK) : ""; },
    sfx: function(){ if (stage && stage.sfx) stage.sfx(); if (hostSrc && A.host.theme && COMP.themes[A.host.theme].sfx) COMP.themes[A.host.theme].sfx(); },
    onReact: function(k, St, TK){ if (stage && stage.onReact) stage.onReact(k, St, TK); },
    paint: function(ctx, t, dt, W, Hh, TK){
      if (!built){ built = true; buildStatic(TK); loadIcons(TK); }
      ctx.save(); ctx.scale(W / 1920, Hh / 1080);
      ctx.drawImage(CV.base, 0, 0);
      dyn(ctx, t, dt, TK);
      drawSig(ctx, t, TK);
      drawProps(ctx, t, TK);
      if (S.cheer > 0.98 && prevCheer <= 0.98) spawn(A.cel, S.win ? 30 : 14, TK, true);
      prevCheer = S.cheer;
      if (S.win && Math.random() < 0.35) spawn(A.cel, 2, TK, false);
      drawParts(ctx, dt);
      if (S.miss > 0.02){ var g = ctx.createRadialGradient(960, 540, 420, 960, 540, 1100); g.addColorStop(0, "rgba(255,40,60,0)"); g.addColorStop(1, "rgba(255,40,60," + (S.miss * 0.3).toFixed(2) + ")"); ctx.fillStyle = g; ctx.fillRect(0, 0, 1920, 1080); }
      if (S.lose){ ctx.fillStyle = "rgba(0,0,0,.3)"; ctx.fillRect(0, 0, 1920, 1080); }
      ctx.restore();
    }
  };
})();
