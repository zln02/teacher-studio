/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME post-office-night — moonlit post office town with a cat postman host. Windows of the town light up as S.progress rises,
   festival bunting fills the top edge, cheer = envelopes fly to the moon + lamps glow, miss = a gust of dark cloud, win = fireworks, lose = lights dim.
   Static layers are cached in an offscreen canvas; only stars, clouds, lit windows and small particles are drawn per frame. */
COMP.themes["post-office-night"] = (function(){
  var ROOF = ["#e4572e", "#3a86ff", "#1fa89a", "#8e5bd9"], FW = ["#ff5a8a", "#ffd23f", "#3ee6ff", "#9b7bff", "#2ecf8f", "#ffffff"];
  var base = null, bw = 0, bh = 0, sp = 0, parts = [], env = [], gust = 0, wins = [], lamps = [], stars = [], bunting = 24, rockets = [];
  var i0;
  for (i0 = 0; i0 < 90; i0++) stars.push({ x: (i0 * 197) % 1920, y: (i0 * 83) % 520 + 10, s: 1 + (i0 % 3), p: i0 * 1.3 });
  function clamp(v, a, b){ return v < a ? a : (v > b ? b : v); }
  function mk(W, Hh){ var c = document.createElement("canvas"); c.width = W; c.height = Hh; return c; }
  function rr(c, x, y, w, h, r){ c.beginPath(); c.moveTo(x + r, y); c.lineTo(x + w - r, y); c.quadraticCurveTo(x + w, y, x + w, y + r); c.lineTo(x + w, y + h - r); c.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    c.lineTo(x + r, y + h); c.quadraticCurveTo(x, y + h, x, y + h - r); c.lineTo(x, y + r); c.quadraticCurveTo(x, y, x + r, y); c.closePath(); }
  /* a house: body, roof kind, windows registered for the dynamic lighting layer */
  function house(x, c, bx, by, w, h, roofKind, col){
    var dk = "rgba(20,8,46,.85)", wx, wy, cols = Math.max(1, Math.floor(w / 56)), rows = Math.max(1, Math.floor(h / 70)), ix, iy;
    x.fillStyle = "#3a2a62"; x.strokeStyle = "#1a0a38"; x.lineWidth = 5; x.fillRect(bx, by, w, h); x.strokeRect(bx, by, w, h);
    x.fillStyle = col; x.strokeStyle = "#1a0a38";
    x.beginPath();
    if (roofKind === 0){ x.moveTo(bx - 12, by); x.lineTo(bx + w / 2, by - 70); x.lineTo(bx + w + 12, by); }
    else if (roofKind === 1){ x.moveTo(bx - 8, by); x.lineTo(bx - 8, by - 26); x.lineTo(bx + w + 8, by - 26); x.lineTo(bx + w + 8, by); }
    else { x.moveTo(bx - 10, by); x.quadraticCurveTo(bx + w / 2, by - 110, bx + w + 10, by); }
    x.closePath(); x.fill(); x.stroke();
    for (iy = 0; iy < rows; iy++) for (ix = 0; ix < cols; ix++){
      wx = bx + (w - cols * 56) / 2 + ix * 56 + 12; wy = by + 22 + iy * 70;
      if (wy + 36 > by + h - 10) continue;
      x.fillStyle = "#2a2450"; x.fillRect(wx, wy, 32, 38); wins.push({ x: wx, y: wy, w: 32, h: 38, thr: 0 });
    }
    return dk;
  }
  function lampPost(x, c, px, py){
    x.fillStyle = "#1a0a38"; x.fillRect(px - 4, py - 90, 8, 90); x.fillRect(px - 16, py - 4, 32, 6);
    x.fillStyle = "#2a2450"; x.beginPath(); x.arc(px, py - 100, 14, 0, 6.283); x.fill();
    lamps.push({ x: px, y: py - 100, thr: 0 });
  }
  function buildBase(W, Hh){
    var c = mk(W, Hh), x = c.getContext("2d"), i, g, b, hx;
    wins = []; lamps = [];
    g = x.createLinearGradient(0, 0, 0, Hh); g.addColorStop(0, "#1d1450"); g.addColorStop(0.7, "#5a2870"); g.addColorStop(1, "#7a2f7d"); x.fillStyle = g; x.fillRect(0, 0, W, Hh);
    /* rolling far hills */
    x.fillStyle = "rgba(40,14,70,.55)"; x.beginPath(); x.moveTo(0, Hh);
    for (i = 0; i <= W; i += 40) x.lineTo(i, 860 + Math.sin(i / 260) * 40);
    x.lineTo(W, Hh); x.fill();
    /* distant town block silhouettes */
    for (i = 0; i < 22; i++){ var bhh = 70 + (i * 53) % 120, bww = 70 + (i * 37) % 40; x.fillStyle = "rgba(26,10,56,.72)"; x.fillRect(i * 92 - 20, 940 - bhh, bww, bhh + 140); }
    x.fillStyle = "rgba(20,8,46,.8)"; x.beginPath(); x.moveTo(0, Hh);
    for (i = 0; i <= W; i += 40) x.lineTo(i, 990 + Math.sin(i / 180 + 1) * 24);
    x.lineTo(W, Hh); x.fill();
    /* tall houses on both edges (these stay visible while the cards cover the middle) */
    house(x, c, 6, 330, 150, 650, 0, ROOF[0]);
    house(x, c, 1766, 420, 148, 560, 2, ROOF[1]);
    /* the post office in the middle (visible on title / result) */
    var px0 = 640, py0 = 650, pw = 640, ph = 350;
    x.fillStyle = "#4a3374"; x.strokeStyle = "#1a0a38"; x.lineWidth = 6; x.fillRect(px0, py0, pw, ph); x.strokeRect(px0, py0, pw, ph);
    x.fillStyle = ROOF[0]; x.beginPath(); x.moveTo(px0 - 30, py0); x.lineTo(px0 + pw / 2, py0 - 150); x.lineTo(px0 + pw + 30, py0); x.closePath(); x.fill(); x.stroke();
    x.fillStyle = "#fff3c4"; x.beginPath(); x.arc(px0 + pw / 2, py0 - 70, 38, 0, 6.283); x.fill(); x.strokeStyle = "#7a4a22"; x.lineWidth = 5; x.stroke();
    x.beginPath(); x.moveTo(px0 + pw / 2, py0 - 70); x.lineTo(px0 + pw / 2, py0 - 96); x.moveTo(px0 + pw / 2, py0 - 70); x.lineTo(px0 + pw / 2 + 18, py0 - 62); x.stroke();
    x.fillStyle = "#ffd23f"; rr(x, px0 + pw / 2 - 130, py0 + 16, 260, 46, 12); x.fill(); x.strokeStyle = "#7a4a22"; x.lineWidth = 4; x.stroke();
    x.fillStyle = "#7a4a22"; for (i = 0; i < 4; i++) x.fillRect(px0 + pw / 2 - 100 + i * 52, py0 + 28, 36, 22); /* sign letters as blocks */
    x.fillStyle = "#3a1f10"; rr(x, px0 + pw / 2 - 50, py0 + ph - 180, 100, 180, 14); x.fill();
    for (i = 0; i < 4; i++){ var wx2 = i < 2 ? px0 + 50 + i * 120 : px0 + pw - 50 - 76 - (i - 2) * 120; x.fillStyle = "#2a2450"; x.fillRect(wx2, py0 + 100, 76, 90); x.fillRect(wx2, py0 + 220, 76, 90); wins.push({ x: wx2, y: py0 + 100, w: 76, h: 90, thr: 0 }); wins.push({ x: wx2, y: py0 + 220, w: 76, h: 90, thr: 0 }); }
    /* small side houses */
    house(x, c, 280, 780, 200, 230, 1, ROOF[2]); house(x, c, 1420, 770, 210, 240, 0, ROOF[3]);
    /* ground and cobble path */
    x.fillStyle = "#1a0a38"; x.fillRect(0, 1010, W, 70);
    x.fillStyle = "rgba(255,255,255,.06)"; for (i = 0; i < W; i += 70) x.fillRect(i + ((i / 70) % 2) * 20, 1030 + ((i / 70) % 3) * 12, 44, 12);
    for (i = 0; i < 6; i++) lampPost(x, c, 60 + i * 340, 1010);
    /* assign light-up order: spread across progress, edges first (those stay visible during play) */
    var order = wins.map(function(w, k){ return k; });
    order.sort(function(a, b){ var ea = Math.min(wins[a].x, 1920 - wins[a].x), eb = Math.min(wins[b].x, 1920 - wins[b].x); return ((ea > 220 ? 1 : 0) - (eb > 220 ? 1 : 0)) || ((a * 7) % 13) - ((b * 7) % 13); });
    for (i = 0; i < order.length; i++) wins[order[i]].thr = 0.04 + 0.9 * (i / order.length);
    for (i = 0; i < lamps.length; i++) lamps[i].thr = 0.1 + i * 0.14;
    return c;
  }
  function envelope(c, x, y, s, rot, a, col){
    c.save(); c.translate(x, y); c.rotate(rot); c.globalAlpha = a; c.fillStyle = col || "#fff4dc"; c.strokeStyle = "#8a5a2b"; c.lineWidth = 3; c.fillRect(-s, -s * 0.65, s * 2, s * 1.3); c.strokeRect(-s, -s * 0.65, s * 2, s * 1.3);
    c.beginPath(); c.moveTo(-s, -s * 0.65); c.lineTo(0, 0); c.lineTo(s, -s * 0.65); c.stroke(); c.restore();
  }
  function burst(x, y, n){
    var col = FW[(Math.random() * 5) | 0], i, a, v;
    for (i = 0; i < n; i++){ a = i / n * 6.283; v = 260 + Math.random() * 220; parts.push({ x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0, max: 1.1 + Math.random() * 0.5, c: i % 3 ? col : "#ffffff", r: 5 }); }
  }

  return {
    paint: function(c, t, dt, W, Hh, TK, S){
      var i, g, a, calm = TK.motion === "calm", n;
      if (!base || bw !== W || bh !== Hh){ base = buildBase(W, Hh); bw = W; bh = Hh; }
      sp += (clamp(S.progress, 0, 1) - sp) * Math.min(1, dt * 3);
      gust += ((S.miss > 0.05 ? 1 : 0) - gust) * Math.min(1, dt * 5);
      c.drawImage(base, 0, 0);
      /* twinkling stars (only the top sky; cheap fillRects) */
      for (i = 0; i < stars.length; i++){ var s = stars[i]; c.globalAlpha = (0.35 + 0.65 * Math.abs(Math.sin(t * 0.8 + s.p))) * (calm ? 0.8 : 1); c.fillStyle = "#fff"; c.fillRect(s.x, s.y, s.s * 2, s.s * 2); }
      c.globalAlpha = 1;
      /* moon in the right margin; glows brighter when the answer is right */
      var mx = 1836, my = 196, gl = 150 + S.cheer * 70 + sp * 40;
      g = c.createRadialGradient(mx, my, 10, mx, my, gl); g.addColorStop(0, "rgba(255,243,196,.95)"); g.addColorStop(0.4, "rgba(255,243,196," + (0.3 + S.cheer * 0.25) + ")"); g.addColorStop(1, "rgba(255,243,196,0)");
      c.fillStyle = g; c.fillRect(mx - gl, my - gl, gl * 2, gl * 2);
      c.fillStyle = "#fff3c4"; c.beginPath(); c.arc(mx, my, 58, 0, 6.283); c.fill();
      c.fillStyle = "rgba(220,200,150,.55)"; c.beginPath(); c.arc(mx - 18, my - 10, 10, 0, 6.283); c.moveTo(mx + 27, my + 16); c.arc(mx + 20, my + 16, 7, 0, 6.283); c.moveTo(mx + 13, my - 28); c.arc(mx + 8, my - 28, 5, 0, 6.283); c.fill();
      /* drifting pink clouds */
      for (i = 0; i < 3; i++){ var cx = (t * 14 * (i + 1) * (calm ? 0.4 : 1) + i * 700) % (W + 400) - 200; c.globalAlpha = 0.16 + gust * 0.14; c.fillStyle = gust > 0.3 ? "#6a4aa0" : "#ffd6f2"; c.beginPath(); c.ellipse(cx, 330 + i * 70, 190, 34, 0, 0, 6.283); c.fill(); }
      c.globalAlpha = 1;
      /* lit windows: the town wakes up as progress rises */
      for (i = 0; i < wins.length; i++){
        var w = wins[i]; a = clamp((sp - w.thr) * 12, 0, 1); if (a <= 0) continue;
        var fl = 0.8 + 0.2 * Math.sin(t * 1.3 + i); c.globalAlpha = a * fl; c.fillStyle = "#ffe066"; c.fillRect(w.x, w.y, w.w, w.h);
        c.globalAlpha = a * 0.5; c.fillStyle = "#fff6c0"; c.fillRect(w.x + 4, w.y + 4, w.w / 2 - 4, w.h - 8);
        c.globalAlpha = a * 0.16; c.fillStyle = "#ffd23f"; c.fillRect(w.x - 10, w.y - 10, w.w + 20, w.h + 20);
      }
      c.globalAlpha = 1;
      /* street lamps */
      for (i = 0; i < lamps.length; i++){
        var lp = lamps[i]; a = clamp((sp - lp.thr) * 10, 0, 1) * (1 - gust * 0.5) + S.cheer * 0.35; a = clamp(a, 0, 1); if (a <= 0.02) continue;
        g = c.createRadialGradient(lp.x, lp.y, 2, lp.x, lp.y, 90); g.addColorStop(0, "rgba(255,224,102," + (0.85 * a) + ")"); g.addColorStop(1, "rgba(255,224,102,0)");
        c.fillStyle = g; c.fillRect(lp.x - 90, lp.y - 90, 180, 180); c.fillStyle = "rgba(255,240,170," + a + ")"; c.beginPath(); c.arc(lp.x, lp.y, 12, 0, 6.283); c.fill();
      }
      /* festival bunting grows from the corners as progress rises (small, at the very top edge) */
      n = Math.ceil(sp * bunting);
      for (i = 0; i < n; i++){
        var order = i % 2 ? bunting - 1 - (i >> 1) : (i >> 1), fx = 40 + order * 80, fy = 8 + Math.sin(order * 0.5 + t * 1.2) * 3 - Math.pow((order % 6) / 3 - 1, 2) * 4;
        c.globalAlpha = 0.9; c.fillStyle = FW[order % 5]; c.beginPath(); c.moveTo(fx - 18, fy); c.lineTo(fx + 18, fy); c.lineTo(fx, fy + 28); c.closePath(); c.fill();
      }
      c.globalAlpha = 1;
      /* envelopes flying up to the moon on correct answers */
      for (i = env.length - 1; i >= 0; i--){
        var e = env[i]; e.life += dt; var k = e.life / e.max; if (k >= 1){ env.splice(i, 1); continue; } if (k < 0) continue;
        var ex = e.x + (mx - e.x) * k + Math.sin(k * 9 + e.p) * 30, ey = e.y + (my - e.y) * k - Math.sin(k * 3.14) * 140;
        envelope(c, ex, ey, 26 * (1 - k * 0.5), Math.sin(k * 7 + e.p) * 0.4, 1 - k * 0.6, e.col);
      }
      /* fireworks / particles */
      for (i = parts.length - 1; i >= 0; i--){
        var p = parts[i]; p.life += dt; if (p.life > p.max){ parts.splice(i, 1); continue; }
        p.vy += 380 * dt; p.vx *= 0.99; p.x += p.vx * dt; p.y += p.vy * dt; c.globalAlpha = 1 - p.life / p.max; c.fillStyle = p.c; c.fillRect(p.x, p.y, p.r, p.r);
      }
      c.globalAlpha = 1;
      for (i = rockets.length - 1; i >= 0; i--){
        var r = rockets[i]; r.life += dt; if (r.life < r.at) continue; if (!r.done){ burst(r.x, r.y, calm ? 20 : 44); r.done = 1; }
        if (r.life > r.at + 0.1) rockets.splice(i, 1);
      }
      if (S.win > 0 && !calm && Math.random() < dt * 1.6) rockets.push({ x: 120 + Math.random() * 1680, y: 120 + Math.random() * 420, at: 0, life: 0 });
      /* sad: the lights dim */
      if (S.lose > 0){ c.fillStyle = "rgba(10,6,30," + (0.45 * S.lose) + ")"; c.fillRect(0, 0, W, Hh); }
    },
    deco: function(){
      return '<div class="po-mail" style="position:absolute;left:1764px;top:800px;width:150px;height:200px"><svg viewBox="0 0 180 220" width="150" height="183">' +
        '<rect x="68" y="120" width="24" height="96" fill="#7a4a22"/><path d="M20 120 L20 70 Q80 10 140 70 L140 120 Z" fill="#d93a3f" stroke="#7d1f1f" stroke-width="6"/>' +
        '<rect x="44" y="82" width="72" height="12" rx="6" fill="#3b0d0d"/>' +
        '<g class="po-flag" style="transform-origin:144px 100px;transition:transform .4s;transform:rotate(0deg)"><rect x="140" y="50" width="8" height="52" fill="#7a4a22"/><polygon points="148,50 176,60 148,72" fill="#ffd23f" stroke="#b8860b" stroke-width="3"/></g></svg></div>';
    },
    onReact: function(kind, S){
      var f = document.querySelector("#ts-deco .po-flag");
      if (kind === "correct" || kind === "win"){
        env.push({ x: 1840, y: 860, life: 0, max: 1.8, p: Math.random() * 6, col: "#fff4dc" }); env.push({ x: 1780, y: 880, life: -0.2, max: 1.8, p: Math.random() * 6, col: "#ffe9a8" });
        if (f) f.style.transform = "rotate(-70deg)";
        if (kind === "win"){ var k; for (k = 0; k < 6; k++) rockets.push({ x: 200 + k * 300, y: 160 + (k % 3) * 120, at: 0.2 + k * 0.28, life: 0 }); }
      } else if (f){ f.style.transform = "rotate(0deg)"; }
      if (kind === "correct" && f) setTimeout(function(){ f.style.transform = "rotate(0deg)"; }, 1600);
    },
    host: {
      name: "우체부 고양이",
      lines: {
        title: ["단어 편지 배달 시작!", "달밤에 배달해요!"], start: ["배달 시작!", "편지를 전해요!"],
        correct: ["배달 완료!", "창문에 불이 켜졌어요!", "야옹! 잘했어요!"], wrong: ["다시 해 봐요!", "괜찮아요, 야옹!"],
        win: ["마을에 불이 모두 켜졌어요!", "단어 축제예요!"], lose: ["편지가 남았어요…", "다음엔 꼭 배달해요!"]
      },
      svg: function(TK){
        var ink = "#6b3a14";
        function face(m){
          var eyes, mouth;
          if (m === "happy"){ eyes = '<path d="M68 100 q10 -14 20 0 M112 100 q10 -14 20 0" stroke="' + ink + '" stroke-width="6" fill="none" stroke-linecap="round"/>'; mouth = '<path d="M84 116 q16 24 32 0 Z" fill="#7a1f3d" stroke="' + ink + '" stroke-width="4" stroke-linejoin="round"/>'; }
          else if (m === "sad"){ eyes = '<path d="M66 84 l20 6 M134 84 l-20 6" stroke="' + ink + '" stroke-width="4" stroke-linecap="round"/><circle cx="78" cy="100" r="7" fill="#1b1b2f"/><circle cx="122" cy="100" r="7" fill="#1b1b2f"/>'; mouth = '<path d="M88 126 q12 -10 24 0" fill="none" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/>'; }
          else { eyes = '<ellipse cx="78" cy="96" rx="10" ry="12" fill="#fff" stroke="' + ink + '" stroke-width="3"/><ellipse cx="122" cy="96" rx="10" ry="12" fill="#fff" stroke="' + ink + '" stroke-width="3"/><circle cx="80" cy="98" r="6" fill="#1b1b2f"/><circle cx="124" cy="98" r="6" fill="#1b1b2f"/>';
            mouth = m === "wow" ? '<ellipse cx="100" cy="124" rx="8" ry="10" fill="#7a1f3d" stroke="' + ink + '" stroke-width="3"/>' : '<path d="M86 120 q14 12 28 0" fill="none" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/>'; }
          return '<g class="f f-' + m + '">' + eyes + '<path d="M94 108 L106 108 L100 115 Z" fill="#ff7a9a"/>' + mouth + '</g>';
        }
        return '<svg viewBox="0 0 300 440" width="300" height="440"><g transform="translate(20,70) scale(1.4)">' +
          '<ellipse cx="100" cy="212" rx="60" ry="8" fill="rgba(0,0,0,.3)"/>' +
          '<path d="M150 172 C192 162 198 122 176 104" fill="none" stroke="#a85a14" stroke-width="18" stroke-linecap="round"/><path d="M150 172 C192 162 198 122 176 104" fill="none" stroke="#ffa94d" stroke-width="10" stroke-linecap="round"/>' +
          '<ellipse cx="100" cy="160" rx="54" ry="48" fill="#ffa94d" stroke="#a85a14" stroke-width="6"/><ellipse cx="100" cy="172" rx="30" ry="28" fill="#ffe3c2"/>' +
          '<path d="M62 126 L134 194" stroke="#6b3a14" stroke-width="10" stroke-linecap="round"/>' +
          '<rect x="110" y="170" width="52" height="38" rx="8" fill="#8a4b1c" stroke="#4e2a0e" stroke-width="5"/><rect x="116" y="178" width="40" height="8" rx="3" fill="#ffd23f"/>' +
          '<path d="M52 66 L56 20 L90 46 Z" fill="#ffa94d" stroke="#a85a14" stroke-width="6" stroke-linejoin="round"/><path d="M148 66 L144 20 L110 46 Z" fill="#ffa94d" stroke="#a85a14" stroke-width="6" stroke-linejoin="round"/>' +
          '<circle cx="100" cy="90" r="50" fill="#ffa94d" stroke="#a85a14" stroke-width="6"/>' +
          '<path d="M52 72 C56 22 144 22 148 72 Z" fill="#2f6fe0" stroke="#173f8f" stroke-width="6" stroke-linejoin="round"/><rect x="96" y="64" width="72" height="12" rx="6" fill="#173f8f"/>' +
          '<circle cx="100" cy="46" r="11" fill="#ffd23f" stroke="#b8860b" stroke-width="3"/>' +
          face("idle") + face("happy") + face("sad") + face("wow") +
          '<ellipse cx="66" cy="114" rx="9" ry="6" fill="#ff7a9a" opacity=".45"/><ellipse cx="134" cy="114" rx="9" ry="6" fill="#ff7a9a" opacity=".45"/>' +
          '<path d="M56 108 L34 104 M56 116 L34 122 M144 108 L166 104 M144 116 L166 122" stroke="#6b3a14" stroke-width="3" stroke-linecap="round"/></g></svg>';
      }
    }
  };
})();
