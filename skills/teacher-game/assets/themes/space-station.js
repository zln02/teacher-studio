/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME space-station — a station control room with a big spaceship window (twinkling stars, ringed planet, moon, Earth limb),
   a robot host, a power gauge and a row of station modules that light up with progress; the window goes to warp on a win and
   flashes red alert on a miss. Reads only the shared show state S, so it works with every mechanic. Original art. */
COMP.themes["space-station"] = (function(){
  var WIN = { x: 40, y: 126, w: 1840, h: 770 }, MODS = 10;
  var bg = null, top = null, stars = null, warp = 0, lastK = 0, flash = [], uid = 0;
  var CY = "#5cf2ff", OR = "#ff9f43";
  function layer(draw){ var c = document.createElement("canvas"); c.width = 1920; c.height = 1080; draw(c.getContext("2d")); return c; }
  function rr(ctx, x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath(); }
  function rnd(a, b){ return a + Math.random() * (b - a); }

  function build(){
    bg = layer(function(c){
      c.fillStyle = "#1a2233"; c.fillRect(0, 0, 1920, 1080);
      c.fillStyle = "rgba(255,255,255,.03)"; for (var i = 0; i < 16; i++) c.fillRect(i * 124 + 6, 0, 3, 126);
      c.fillStyle = "#0e1424"; c.fillRect(0, 0, 1920, 112);
      c.fillStyle = "rgba(92,242,255,.18)"; c.fillRect(0, 108, 1920, 4);
      var sg = c.createLinearGradient(0, WIN.y, 0, WIN.y + WIN.h);
      sg.addColorStop(0, "#03061a"); sg.addColorStop(1, "#1a0f3d");
      c.save(); rr(c, WIN.x, WIN.y, WIN.w, WIN.h, 70); c.clip();
      c.fillStyle = sg; c.fillRect(WIN.x, WIN.y, WIN.w, WIN.h);
      var nb = c.createRadialGradient(1250, 420, 20, 1250, 420, 520);
      nb.addColorStop(0, "rgba(180,90,255,.28)"); nb.addColorStop(1, "rgba(180,90,255,0)");
      c.fillStyle = nb; c.fillRect(WIN.x, WIN.y, WIN.w, WIN.h);
      var nb2 = c.createRadialGradient(420, 360, 10, 420, 360, 380);
      nb2.addColorStop(0, "rgba(60,160,255,.18)"); nb2.addColorStop(1, "rgba(60,160,255,0)");
      c.fillStyle = nb2; c.fillRect(WIN.x, WIN.y, WIN.w, WIN.h);
      c.restore();
    });
    top = layer(function(c){
      var i;
      c.save(); rr(c, WIN.x, WIN.y, WIN.w, WIN.h, 70); c.clip();
      var eg = c.createRadialGradient(960, 2050, 1000, 960, 2050, 1220);
      eg.addColorStop(0, "#1d6fd1"); eg.addColorStop(0.92, "#59c3ff"); eg.addColorStop(1, "rgba(120,220,255,0)");
      c.fillStyle = eg; c.beginPath(); c.arc(960, 2050, 1220, 0, 6.283); c.fill();
      c.fillStyle = "rgba(70,170,90,.55)"; c.beginPath(); c.ellipse(700, 900, 220, 40, 0.1, 0, 6.283); c.ellipse(1320, 930, 160, 30, -0.1, 0, 6.283); c.fill();
      c.restore();
      c.lineWidth = 26; c.strokeStyle = "#3a4a66"; rr(c, WIN.x, WIN.y, WIN.w, WIN.h, 70); c.stroke();
      c.lineWidth = 4; c.strokeStyle = "rgba(255,255,255,.18)"; rr(c, WIN.x + 14, WIN.y + 14, WIN.w - 28, WIN.h - 28, 58); c.stroke();
      /* rivets on the frame */
      c.fillStyle = "#8fa3c0";
      for (i = 0; i < 24; i++){ c.beginPath(); c.arc(WIN.x + 120 + i * 72, WIN.y - 1, 5, 0, 6.283); c.arc(WIN.x + 120 + i * 72, WIN.y + WIN.h + 1, 5, 0, 6.283); c.fill(); }
      var fg = c.createLinearGradient(0, 910, 0, 1080);
      fg.addColorStop(0, "#222c40"); fg.addColorStop(1, "#0b0f18");
      c.fillStyle = fg; c.fillRect(0, 910, 1920, 170);
      c.strokeStyle = "rgba(120,160,220,.16)"; c.lineWidth = 2;
      for (i = 0; i < 40; i++){ c.beginPath(); c.moveTo(i * 50, 910); c.lineTo(i * 50 - 60, 1080); c.stroke(); }
      /* truss that carries the modules */
      c.fillStyle = "#3a4a66"; c.fillRect(250, 1048, 1620, 8);
    });
    stars = []; for (var k = 0; k < 190; k++) stars.push({ x: rnd(WIN.x, WIN.x + WIN.w), y: rnd(WIN.y + 10, WIN.y + WIN.h - 10), z: rnd(0.2, 1), p: rnd(0, 6.28) });
  }

  function solar(ctx, x, y){
    ctx.fillStyle = "#1d3f8a"; ctx.strokeStyle = "#8fa3c0"; ctx.lineWidth = 4; ctx.fillRect(x, y, 112, 54); ctx.strokeRect(x, y, 112, 54);
    ctx.strokeStyle = "#2a5bc2"; ctx.lineWidth = 2;
    for (var i = 1; i < 6; i++){ ctx.beginPath(); ctx.moveTo(x + i * 18.6, y); ctx.lineTo(x + i * 18.6, y + 54); ctx.stroke(); }
  }

  function paint(ctx, t, dt, W, Hh, TK, S){
    if (!bg) build();
    var p = S.progress, ch = Math.max(S.cheer, S.win * 0.6), ms = S.miss, i;
    var tgt = S.win ? 1 : 0; warp += (tgt - warp) * Math.min(1, dt * 0.9); if (warp < 0.002 && !tgt) warp = 0;
    ctx.save(); ctx.scale(W / 1920, Hh / 1080);
    ctx.drawImage(bg, 0, 0);
    /* inside the window */
    ctx.save(); rr(ctx, WIN.x, WIN.y, WIN.w, WIN.h, 70); ctx.clip();
    ctx.fillStyle = "#fff";
    for (i = 0; i < stars.length; i++){
      var s = stars[i];
      s.x -= (6 + warp * 1600) * s.z * dt;
      if (s.x < WIN.x){ s.x += WIN.w; s.y = rnd(WIN.y + 10, WIN.y + WIN.h - 10); }
      ctx.globalAlpha = 0.35 + 0.65 * s.z * (0.6 + 0.4 * Math.sin(t * 2 + s.p));
      var sz = 1.5 + s.z * 2.5;
      ctx.fillRect(s.x, s.y, sz + warp * 260 * s.z, warp > 0.05 ? 1 + s.z * 2 : sz);
    }
    ctx.globalAlpha = 1;
    var drift = Math.sin(t * 0.15) * 12, px = 1790 + drift, py = 300;
    ctx.strokeStyle = "rgba(255,230,180,.75)"; ctx.lineWidth = 10;
    ctx.beginPath(); ctx.ellipse(px, py, 170, 38, -0.3, Math.PI, 2 * Math.PI); ctx.stroke();
    ctx.fillStyle = "#c2672b"; ctx.beginPath(); ctx.arc(px, py, 92, 0, 6.283); ctx.fill();
    ctx.fillStyle = "#ffd28a"; ctx.beginPath(); ctx.arc(px - 16, py - 16, 70, 0, 6.283); ctx.fill();
    ctx.fillStyle = "rgba(160,80,30,.35)"; ctx.fillRect(px - 80, py - 6, 150, 12); ctx.fillRect(px - 70, py + 26, 130, 9);
    ctx.beginPath(); ctx.ellipse(px, py, 170, 38, -0.3, 0, Math.PI); ctx.stroke();
    var mx = 100 - drift, my = 560;
    ctx.fillStyle = "#cfd6e6"; ctx.beginPath(); ctx.arc(mx, my, 40, 0, 6.283); ctx.fill();
    ctx.fillStyle = "rgba(90,100,130,.5)"; ctx.beginPath(); ctx.arc(mx - 10, my - 8, 9, 0, 6.283); ctx.arc(mx + 14, my + 12, 6, 0, 6.283); ctx.fill();
    /* the window glows cyan on a cheer, flashes red alert on a miss */
    if (ch > 0.02){ ctx.fillStyle = "rgba(92,242,255," + (ch * 0.12).toFixed(3) + ")"; ctx.fillRect(WIN.x, WIN.y, WIN.w, WIN.h); }
    if (ms > 0.02){ ctx.fillStyle = "rgba(255,40,70," + (ms * 0.22).toFixed(3) + ")"; ctx.fillRect(WIN.x, WIN.y, WIN.w, WIN.h); }
    ctx.restore();
    ctx.drawImage(top, 0, 0);
    /* blinking status lights along the sill */
    var on = Math.floor(t * 2);
    ctx.fillStyle = ms > 0.05 ? "#ff4466" : CY;
    for (i = 0; i < 16; i++) if ((on + i) % 5 === 0) ctx.fillRect(134 + i * 110, WIN.y + WIN.h - 4, 12, 12);

    /* power gauge (left edge) */
    var gx = 80, gy = 250, gr = 54, pp = Math.max(0, Math.min(1, p));
    ctx.lineWidth = 16; ctx.strokeStyle = "#24324a"; ctx.fillStyle = "#0b1530";
    ctx.beginPath(); ctx.arc(gx, gy, gr, 0, 6.2832); ctx.fill(); ctx.stroke();
    if (pp > 0.002){
      ctx.strokeStyle = ms > 0.3 ? "#ff6b8b" : CY; ctx.lineCap = "round"; ctx.shadowColor = CY; ctx.shadowBlur = 10 + ch * 14;
      ctx.beginPath(); ctx.arc(gx, gy, gr, -Math.PI / 2, -Math.PI / 2 + pp * 6.2832); ctx.stroke();
      ctx.shadowBlur = 0; ctx.lineCap = "butt";
    }
    ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.font = "34px " + (TK.fonts && TK.fonts.display ? '"' + TK.fonts.display + '",' : "") + "sans-serif";
    ctx.fillText(Math.round(pp * 100) + "%", gx, gy + 2);
    ctx.fillStyle = CY; ctx.font = "34px " + (TK.fonts && TK.fonts.display ? '"' + TK.fonts.display + '",' : "") + "sans-serif";
    ctx.fillText("⚡ 전력", gx, gy + 92);
    ctx.textAlign = "start"; ctx.textBaseline = "alphabetic";

    /* module row along the bottom: lights up as progress grows */
    var k = Math.min(MODS, Math.floor(pp * MODS + 0.001));
    if (S.win) k = MODS;
    if (k > lastK){ for (i = lastK; i < k; i++) flash[i] = 1; }
    lastK = k;
    solar(ctx, 250, 1022); solar(ctx, 1760, 1022);
    for (i = 0; i < MODS; i++){
      var mx2 = 380 + i * 140, my2 = 1026, onm = i < k, f = flash[i] || 0;
      if (f > 0) flash[i] = Math.max(0, f - dt * 1.4);
      ctx.save();
      if (onm){ ctx.shadowColor = CY; ctx.shadowBlur = 18 + f * 30 + ch * 12; }
      ctx.fillStyle = onm ? "#1b8fa8" : "#2a3550"; ctx.strokeStyle = onm ? CY : (i === k ? "#ffffff" : "#8fa3c0"); ctx.lineWidth = 5;
      rr(ctx, mx2, my2, 100, 48, 16); ctx.fill(); ctx.stroke();
      ctx.restore();
      for (var d = 0; d < 3; d++){ ctx.fillStyle = onm ? "#eaffff" : "#121a2c"; ctx.beginPath(); ctx.arc(mx2 + 30 + d * 20, my2 + 24, 6, 0, 6.283); ctx.fill(); }
      if (i === k && !S.win){ ctx.globalAlpha = 0.25 + 0.25 * Math.sin(t * 5); ctx.fillStyle = "#fff"; rr(ctx, mx2, my2, 100, 48, 16); ctx.fill(); ctx.globalAlpha = 1; }
    }
    if (S.lose > 0){ ctx.fillStyle = "rgba(4,6,16,.45)"; ctx.fillRect(0, 0, 1920, 1080); }
    ctx.restore();
  }

  var K = { o: "#0d1626", m: "#dfe7f2", s: "#8fa3c0", g: "#5cf2ff", a: "#ff9f43" };
  function arm(d, f, o){ return '<path d="' + d + '" fill="none" stroke="' + o + '" stroke-width="36" stroke-linecap="round"/><path d="' + d + '" fill="none" stroke="' + f + '" stroke-width="23" stroke-linecap="round"/>'; }
  function hostSvg(){
    var o = K.o, m = K.m, s = K.s, g = K.g, a = K.a;
    var st = ' fill="none" stroke="' + g + '" stroke-linecap="round" ';
    var face = '<g class="f f-idle"><rect x="104" y="124" width="24" height="36" rx="11" fill="' + g + '"/><rect x="172" y="124" width="24" height="36" rx="11" fill="' + g + '"/><path d="M134 182 Q150 190 166 182"' + st + 'stroke-width="6"/></g>' +
      '<g class="f f-happy"><path d="M100 150 Q116 124 132 150 M168 150 Q184 124 200 150"' + st + 'stroke-width="9"/><path d="M126 172 Q150 198 174 172"' + st + 'stroke-width="7"/></g>' +
      '<g class="f f-sad"><path d="M102 132 L130 144 M198 132 L170 144"' + st + 'stroke-width="8"/><path d="M134 186 Q150 174 166 186"' + st + 'stroke-width="6"/></g>' +
      '<g class="f f-wow"><circle cx="116" cy="140" r="17"' + st + 'stroke-width="8"/><circle cx="184" cy="140" r="17"' + st + 'stroke-width="8"/><circle cx="150" cy="184" r="9" fill="' + g + '"/></g>';
    return '<svg viewBox="0 0 300 440" width="300" height="440">' +
      '<ellipse cx="150" cy="432" rx="70" ry="9" fill="rgba(0,0,0,.35)"/>' +
      '<g class="ss-flame"><path d="M122 384 Q150 452 178 384 Z" fill="' + a + '"/><path d="M136 384 Q150 428 164 384 Z" fill="#fff6b0"/></g>' +
      '<rect x="112" y="372" width="76" height="22" rx="10" fill="' + s + '" stroke="' + o + '" stroke-width="5"/>' +
      '<g class="ss-wave">' + arm("M94 292 Q52 292 46 240", s, o) + '<circle cx="46" cy="232" r="17" fill="' + m + '" stroke="' + o + '" stroke-width="5"/><path d="M36 220 L32 206 M56 220 L60 206" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/></g>' +
      arm("M206 292 Q250 312 244 352", s, o) + '<circle cx="244" cy="358" r="17" fill="' + m + '" stroke="' + o + '" stroke-width="5"/>' +
      '<rect x="88" y="248" width="124" height="134" rx="46" fill="' + m + '" stroke="' + o + '" stroke-width="7"/>' +
      '<rect x="112" y="280" width="76" height="56" rx="14" fill="#0b1530" stroke="' + o + '" stroke-width="4"/>' +
      '<circle class="ss-blink" cx="132" cy="308" r="8" fill="' + g + '"/><circle class="ss-blink d2" cx="150" cy="308" r="8" fill="' + a + '"/><circle class="ss-blink d3" cx="168" cy="308" r="8" fill="#7dff8a"/>' +
      '<rect x="134" y="226" width="32" height="28" rx="8" fill="' + s + '" stroke="' + o + '" stroke-width="5"/>' +
      '<rect x="28" y="118" width="24" height="60" rx="11" fill="' + s + '" stroke="' + o + '" stroke-width="5"/><rect x="248" y="118" width="24" height="60" rx="11" fill="' + s + '" stroke="' + o + '" stroke-width="5"/>' +
      '<line x1="150" y1="66" x2="150" y2="30" stroke="' + o + '" stroke-width="6"/><circle class="ss-blink" cx="150" cy="24" r="13" fill="' + a + '" stroke="' + o + '" stroke-width="4"/>' +
      '<rect x="46" y="64" width="208" height="168" rx="56" fill="' + m + '" stroke="' + o + '" stroke-width="7"/>' +
      '<rect x="70" y="88" width="160" height="120" rx="38" fill="#08122a" stroke="' + o + '" stroke-width="5"/>' +
      '<g class="ss-face">' + face + '</g>' +
      '<path d="M86 104 Q108 94 138 96" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="6" stroke-linecap="round"/>' +
      '</svg>';
  }

  function deco(){
    return '<style>' +
      '#ts-deco .ss-flame{animation:ssFlame .18s steps(2) infinite;transform-origin:150px 384px}' +
      '@keyframes ssFlame{0%{transform:scaleY(1)}100%{transform:scaleY(.8)}}' +
      '#ts-deco .ss-wave{transform-origin:94px 292px;animation:ssWave 1.6s ease-in-out infinite}' +
      '@keyframes ssWave{0%,100%{transform:rotate(0)}50%{transform:rotate(-14deg)}}' +
      '#ts-deco .ss-blink{animation:ssLed 1.2s steps(2) infinite}#ts-deco .ss-blink.d2{animation-delay:.4s}#ts-deco .ss-blink.d3{animation-delay:.8s}' +
      '@keyframes ssLed{0%{opacity:1}100%{opacity:.3}}' +
      '#ts-deco .ss-face{filter:drop-shadow(0 0 6px #5cf2ff)}' +
      'body.reduce #ts-deco .ss-flame,body.reduce #ts-deco .ss-wave,body.reduce #ts-deco .ss-blink{animation:none!important}' +
      '</style>';
  }

  function sfx(){
    NG.defineSfx("ssPower", function(){
      NG.tone({ type: "sawtooth", freq: 160, slide: 960, dur: 0.34, vol: 0.14 });
      NG.tone({ type: "sine", freq: 1318, dur: 0.45, vol: 0.2, jitter: 0, delay: 0.3 });
      NG.tone({ type: "sine", freq: 1760, dur: 0.5, vol: 0.13, jitter: 0, delay: 0.38 });
    });
    NG.defineSfx("ssWarp", function(){
      NG.tone({ type: "sine", freq: 140, slide: 2400, dur: 1.4, vol: 0.24 });
      NG.tone({ type: "noise", freq: 900, q: 0.6, dur: 1.5, vol: 0.14, filter: "lowpass" });
    });
  }

  function onReact(kind){
    if (kind === "correct") NG.sfx("ssPower");
    else if (kind === "win"){ NG.sfx("ssWarp"); NG.fx.flash("#ffffff", 0.3); NG.after(1600, function(){ NG.fx.confetti(); }); }
    else if (kind === "start"){ lastK = 0; flash = []; }
  }

  return {
    paint: paint, deco: deco, sfx: sfx, onReact: onReact,
    host: { svg: hostSvg, name: "로봇 코비", lines: {
      title: ["별빛호에 어서 와요!"], start: ["첫 모듈을 켜 봐요!"],
      correct: ["모듈 가동! 삐빅!", "전력 충전 완료!"], wrong: ["괜찮아요, 기록해 둘게요", "다음 모듈에서 만회해요"],
      win: ["워프 엔진 점화!"], lose: ["점검 끝! 다시 도전해요"] } }
  };
})();
