/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME cell-feeding — the whole stage is the inside of a friendly cell: a beaded membrane frames the screen, organelles (nucleus, mitochondria,
   ER, Golgi, vacuoles) sit in the margins and wake up (color + glow) as S.progress rises. The cell host grows and glows with progress.
   Nutrient particles drift toward the nucleus: cheer = more/faster, miss = they scatter and gray out, win = glow burst, lose = dim.
   Static membrane is cached once; organelles and particles are cheap per-frame draws. */
COMP.themes["cell-feeding"] = (function(){
  var FCOL = ["#ff9fbf", "#ffb877", "#ffe16b", "#8fdca4", "#8cc8ff"];
  var base = null, bw = 0, bh = 0, sp = 0, nut = [], burst = [], lastHost = -1, scatter = 0, glowHost = 0;
  var i0;
  for (i0 = 0; i0 < 46; i0++) nut.push({ x: (i0 * 263) % 1920, y: (i0 * 151) % 1080, r: 7 + (i0 * 5) % 10, v: 14 + (i0 * 7) % 26, p: i0 * 0.7, c: FCOL[i0 % 5], ox: 0, oy: 0 });
  function clamp(v, a, b){ return v < a ? a : (v > b ? b : v); }
  function mk(W, Hh){ var c = document.createElement("canvas"); c.width = W; c.height = Hh; return c; }
  function lerp(a, b, k){ return a + (b - a) * k; }
  function hex(h){ h = h.replace("#", ""); return [parseInt(h.substr(0, 2), 16), parseInt(h.substr(2, 2), 16), parseInt(h.substr(4, 2), 16)]; }
  /* mix a vivid color with a pale gray-pink by life k (0..1) */
  function mix(h, k){ var a = hex(h), g = [236, 214, 224], r = []; for (var i = 0; i < 3; i++) r.push(Math.round(lerp(g[i], a[i], k))); return "rgb(" + r.join(",") + ")"; }
  function wob(t, p, a){ return Math.sin(t * 0.9 + p) * a; }

  function buildBase(W, Hh){
    var c = mk(W, Hh), x = c.getContext("2d"), i, g, px, py, ang, n, step;
    g = x.createLinearGradient(0, 0, 0, Hh); g.addColorStop(0, "#fff4e6"); g.addColorStop(1, "#ffd9e8"); x.fillStyle = g; x.fillRect(0, 0, W, Hh);
    /* soft cytoplasm streams */
    x.strokeStyle = "rgba(224,112,154,.14)"; x.lineWidth = 46; x.lineCap = "round";
    x.beginPath(); x.moveTo(-50, 1000); x.bezierCurveTo(500, 900, 700, 1080, 1200, 980); x.bezierCurveTo(1500, 920, 1700, 1040, 1980, 960); x.stroke();
    x.beginPath(); x.moveTo(-50, 160); x.bezierCurveTo(400, 60, 900, 220, 1300, 120); x.bezierCurveTo(1600, 60, 1800, 180, 1980, 100); x.stroke();
    /* ribosome dots */
    x.fillStyle = "rgba(160,120,230,.22)";
    for (i = 0; i < 70; i++){ px = (i * 389) % W; py = (i * 211) % Hh; x.beginPath(); x.arc(px, py, 4 + (i % 3) * 2, 0, 6.283); x.fill(); }
    /* beaded membrane around the screen edge: double bead rows + lipid tails */
    x.fillStyle = "rgba(255,150,190,.30)"; x.fillRect(0, 0, W, 22); x.fillRect(0, Hh - 22, W, 22); x.fillRect(0, 0, 22, Hh); x.fillRect(W - 22, 0, 22, Hh);
    step = 34;
    function bead(bx, by, dx, dy){
      x.strokeStyle = "rgba(224,112,154,.55)"; x.lineWidth = 4; x.beginPath(); x.moveTo(bx + dx * 8, by + dy * 8); x.lineTo(bx + dx * 30, by + dy * 30); x.stroke();
      x.fillStyle = "#ffb0cc"; x.strokeStyle = "#e0709a"; x.lineWidth = 3; x.beginPath(); x.arc(bx, by, 9, 0, 6.283); x.fill(); x.stroke();
    }
    for (px = 17; px < W; px += step){ bead(px, 14, 0, 1); bead(px, Hh - 14, 0, -1); }
    for (py = 17; py < Hh; py += step){ bead(14, py, 1, 0); bead(W - 14, py, -1, 0); }
    /* channel proteins (green gates) on the membrane */
    x.fillStyle = "#5cc98a"; x.strokeStyle = "#2f8a57"; x.lineWidth = 3;
    for (i = 0; i < 7; i++){ px = 160 + i * 270; x.beginPath(); x.moveTo(px - 18, 0); x.lineTo(px + 18, 0); x.lineTo(px + 12, 40); x.lineTo(px - 12, 40); x.closePath(); x.fill(); x.stroke(); x.beginPath(); x.moveTo(px - 18, Hh); x.lineTo(px + 18, Hh); x.lineTo(px + 12, Hh - 40); x.lineTo(px - 12, Hh - 40); x.closePath(); x.fill(); x.stroke(); }
    return c;
  }
  function nucleus(c, x, y, r, k, t, cheer){
    var gl = 20 + cheer * 30 + k * 18, g = c.createRadialGradient(x, y, r * 0.8, x, y, r + gl); g.addColorStop(0, "rgba(183,140,240," + (0.2 + k * 0.4) + ")"); g.addColorStop(1, "rgba(183,140,240,0)");
    c.fillStyle = g; c.fillRect(x - r - gl, y - r - gl, (r + gl) * 2, (r + gl) * 2);
    c.fillStyle = mix("#b78cf0", k); c.strokeStyle = mix("#7c4dcc", k); c.lineWidth = 8; c.beginPath(); c.arc(x, y, r + Math.sin(t * 1.2) * 3, 0, 6.283); c.fill(); c.stroke();
    c.fillStyle = mix("#7c4dcc", k); c.beginPath(); c.arc(x - r * 0.25, y + r * 0.1, r * 0.35, 0, 6.283); c.fill();
    c.fillStyle = "rgba(255,255,255,.55)"; for (var i = 0; i < 8; i++){ var a = i * 0.8 + 0.3; c.beginPath(); c.arc(x + Math.cos(a) * r * 0.82, y + Math.sin(a) * r * 0.82, 6, 0, 6.283); c.fill(); }
  }
  function mito(c, x, y, rot, k, t, cheer, ph){
    c.save(); c.translate(x, y + wob(t, ph, 8)); c.rotate(rot + wob(t, ph + 1, 0.06));
    if (k > 0.2){ var g = c.createRadialGradient(0, 0, 10, 0, 0, 130); g.addColorStop(0, "rgba(255,170,90," + (0.3 * k + cheer * 0.25) + ")"); g.addColorStop(1, "rgba(255,170,90,0)"); c.fillStyle = g; c.fillRect(-130, -130, 260, 260); }
    c.fillStyle = mix("#ff9f6b", k); c.strokeStyle = mix("#c4602a", k); c.lineWidth = 6; c.beginPath(); c.ellipse(0, 0, 100, 46, 0, 0, 6.283); c.fill(); c.stroke();
    c.beginPath(); c.moveTo(-70, 0); for (var i = 0; i < 7; i++){ c.lineTo(-70 + i * 23 + 11, i % 2 ? 22 : -22); c.lineTo(-70 + (i + 1) * 23, 0); } c.stroke();
    c.restore();
  }
  function er(c, x, y, w, k, t, ph){
    c.strokeStyle = mix("#e0709a", k * 0.9); c.lineWidth = 10; c.lineCap = "round";
    for (var j = 0; j < 4; j++){ c.beginPath(); for (var i = 0; i <= 10; i++){ var px = x + i * w / 10, py = y + j * 28 + Math.sin(i * 1.3 + t + ph + j) * 8; if (i) c.lineTo(px, py); else c.moveTo(px, py); } c.stroke(); }
  }
  function golgi(c, x, y, k, t){
    for (var j = 0; j < 5; j++){ c.strokeStyle = mix(["#5b8de0", "#4a7fd9", "#3fae6d", "#e8b84a", "#e0709a"][j], k); c.lineWidth = 12; c.lineCap = "round"; c.beginPath(); c.moveTo(x - 70 + j * 6, y + j * 22); c.quadraticCurveTo(x, y - 24 + j * 22 + Math.sin(t + j) * 3, x + 70 - j * 6, y + j * 22); c.stroke(); }
  }
  function vac(c, x, y, r, k, t, ph){
    c.fillStyle = mix("#bdf0cc", k); c.strokeStyle = mix("#3fae6d", k); c.lineWidth = 5; c.beginPath(); c.arc(x, y + wob(t, ph, 6), r, 0, 6.283); c.fill(); c.stroke();
    c.fillStyle = "rgba(255,255,255,.55)"; c.beginPath(); c.arc(x - r * 0.3, y - r * 0.3 + wob(t, ph, 6), r * 0.22, 0, 6.283); c.fill();
  }
  function spark(c, x, y, r){ c.beginPath(); c.moveTo(x, y - r); c.quadraticCurveTo(x, y, x + r, y); c.quadraticCurveTo(x, y, x, y + r); c.quadraticCurveTo(x, y, x - r, y); c.quadraticCurveTo(x, y, x, y - r); c.fill(); }

  return {
    paint: function(c, t, dt, W, Hh, TK, S){
      var i, k, calm = TK.motion === "calm", n, p;
      if (!base || bw !== W || bh !== Hh){ base = buildBase(W, Hh); bw = W; bh = Hh; }
      sp += (clamp(S.progress, 0, 1) - sp) * Math.min(1, dt * 3);
      scatter += ((S.miss > 0.05 ? 1 : 0) - scatter) * Math.min(1, dt * 4);
      c.drawImage(base, 0, 0);
      k = clamp(0.18 + sp * 0.82 + S.cheer * 0.2, 0, 1);
      /* organelles in the margins; they wake up with progress */
      nucleus(c, 1884, 600, 150, k, t, S.cheer);
      mito(c, 40, 400, -0.5, k, t, S.cheer, 0.3); mito(c, 70, 700, 0.55, k, t, S.cheer, 2.1);
      er(c, 4, 134, 150, k, t, 0); er(c, 1770, 130, 140, k, t, 2);
      golgi(c, 1850, 900, k, t); vac(c, 1850, 1010, 40, k, t, 1.1); vac(c, 640, 1052, 36, k, t, 0.4); vac(c, 1290, 1056, 30, k, t, 2.2);
      /* the lit halo that grows around the whole cell as it thrives */
      if (sp > 0.02 || S.cheer > 0.02){
        var al = 0.06 + sp * 0.12 + S.cheer * 0.12, g = c.createRadialGradient(W / 2, Hh / 2, 500, W / 2, Hh / 2, 1100); g.addColorStop(0, "rgba(255,240,150,0)"); g.addColorStop(1, "rgba(255,225,120," + al + ")");
        c.fillStyle = g; c.fillRect(0, 0, W, Hh);
      }
      /* nutrient particles drifting toward the nucleus (up and to the right) */
      n = Math.round(lerp(20, nut.length, clamp(0.3 + sp * 0.4 + S.cheer, 0, 1))); if (calm) n = Math.min(n, 18);
      for (i = 0; i < n; i++){
        p = nut[i]; var sp2 = p.v * (1 + S.cheer * 3) * (calm ? 0.5 : 1);
        p.y -= sp2 * dt; p.x += sp2 * 0.5 * dt;
        if (scatter > 0.05){ p.ox += (Math.random() - 0.5) * 40 * dt * 10; p.oy += (Math.random() - 0.5) * 40 * dt * 10; }
        p.ox *= 0.96; p.oy *= 0.96;
        if (p.y < -p.r || p.x > W + p.r){ p.y = Hh + p.r; p.x = Math.random() * W; }
        var px = p.x + Math.sin(t * 0.6 + p.p) * 30 + p.ox, py = p.y + p.oy;
        c.globalAlpha = 0.55 - scatter * 0.25; c.fillStyle = scatter > 0.3 ? "#bcaab7" : p.c; c.beginPath(); c.arc(px, py, p.r, 0, 6.283); c.fill();
        c.globalAlpha = 0.5; c.fillStyle = "#fff"; c.beginPath(); c.arc(px - p.r * 0.3, py - p.r * 0.3, p.r * 0.28, 0, 6.283); c.fill();
      }
      c.globalAlpha = 1;
      /* bursts of food reaching the nucleus */
      for (i = burst.length - 1; i >= 0; i--){
        var b = burst[i]; b.life += dt; if (b.life < 0) continue; var q = b.life / b.max; if (q >= 1){ burst.splice(i, 1); continue; }
        var bx = lerp(b.x, 1860, q * q), by = lerp(b.y, 600, q * q) - Math.sin(q * 3.14) * 120;
        c.globalAlpha = 1 - q * 0.5; c.fillStyle = b.c; c.beginPath(); c.arc(bx, by, b.r * (1 - q * 0.4), 0, 6.283); c.fill();
        c.globalAlpha = (1 - q) * 0.9; c.fillStyle = "#fff"; spark(c, bx + 14, by - 14, 10);
      }
      c.globalAlpha = 1;
      if (S.miss > 0.02){ c.fillStyle = "rgba(190,90,120," + (S.miss * 0.18) + ")"; c.fillRect(0, 0, W, Hh); }
      if (S.lose > 0){ c.fillStyle = "rgba(60,30,70," + (0.32 * S.lose) + ")"; c.fillRect(0, 0, W, Hh); }
      /* the host cell grows and glows with progress (updates only when the value moves) */
      var want = Math.round((sp + S.cheer * 0.06 + S.win * 0.1) * 100);
      if (want !== lastHost){
        lastHost = want; var h = document.querySelector("#ts-deco .cf-body");
        if (h){
          var sc = 1 + sp * 0.28 + S.win * 0.08, glow = 4 + sp * 22 + S.cheer * 18;
          h.style.transform = "scale(" + sc.toFixed(3) + ")"; h.style.filter = "drop-shadow(0 0 " + glow.toFixed(0) + "px rgba(255,214,77," + (0.25 + sp * 0.6).toFixed(2) + "))";
          var o1 = document.querySelector("#ts-deco .cf-o1"), o2 = document.querySelector("#ts-deco .cf-o2"), o3 = document.querySelector("#ts-deco .cf-o3");
          if (o1) o1.style.opacity = clamp((sp - 0.15) * 6, 0, 1); if (o2) o2.style.opacity = clamp((sp - 0.4) * 6, 0, 1); if (o3) o3.style.opacity = clamp((sp - 0.65) * 6, 0, 1);
        }
      }
    },
    onReact: function(kind, S){
      var i;
      if (kind === "correct" || kind === "win"){ for (i = 0; i < (kind === "win" ? 14 : 5); i++) burst.push({ x: 120 + Math.random() * 600, y: 700 + Math.random() * 300, life: -i * 0.08, max: 1.1 + Math.random() * 0.4, c: FCOL[i % 5], r: 11 + Math.random() * 6 }); }
    },
    host: {
      name: "몽글이",
      lines: {
        title: ["안녕! 나는 몽글이야", "먹이를 줘!"], start: ["냠냠! 먹이를 줘!", "맛있게 먹을게!"],
        correct: ["맛있다! 냠냠!", "나 쑥쑥 자라는 중!", "고마워!"], wrong: ["으음, 그건 아닌 것 같아…", "다시 해 볼까?"],
        win: ["다 컸다! 고마워!", "우와, 나 자랐어!"], lose: ["배고파…", "다음엔 맛있게 줘!"]
      },
      svg: function(TK){
        var INK = "#3b2a4a";
        function face(m){
          var cx = 205, cy = 250, s = 0.8, o = '<g class="f f-' + m + '">';
          if (m === "happy") o += '<path d="M' + (cx - 45 * s) + " " + cy + " q" + 11 * s + " " + (-16 * s) + " " + 22 * s + ' 0 M' + (cx + 23 * s) + " " + cy + " q" + 11 * s + " " + (-16 * s) + " " + 22 * s + ' 0" stroke="' + INK + '" stroke-width="' + 7 * s + '" fill="none" stroke-linecap="round"/>';
          else o += '<circle cx="' + (cx - 34 * s) + '" cy="' + cy + '" r="' + 11 * s + '" fill="' + INK + '"/><circle cx="' + (cx + 34 * s) + '" cy="' + cy + '" r="' + 11 * s + '" fill="' + INK + '"/><circle cx="' + (cx - 30 * s) + '" cy="' + (cy - 4 * s) + '" r="' + 4 * s + '" fill="#fff"/><circle cx="' + (cx + 38 * s) + '" cy="' + (cy - 4 * s) + '" r="' + 4 * s + '" fill="#fff"/>';
          if (m === "sad") o += '<path d="M' + (cx - 40 * s) + " " + (cy - 22 * s) + " l" + 20 * s + " " + 6 * s + " M" + (cx + 40 * s) + " " + (cy - 22 * s) + " l" + (-20 * s) + " " + 6 * s + '" stroke="' + INK + '" stroke-width="' + 5 * s + '" stroke-linecap="round"/>';
          o += '<ellipse cx="' + (cx - 58 * s) + '" cy="' + (cy + 22 * s) + '" rx="' + 13 * s + '" ry="' + 8 * s + '" fill="#ff7aa8" opacity=".55"/><ellipse cx="' + (cx + 58 * s) + '" cy="' + (cy + 22 * s) + '" rx="' + 13 * s + '" ry="' + 8 * s + '" fill="#ff7aa8" opacity=".55"/>';
          var my = cy + 30 * s;
          if (m === "wow" || m === "happy") o += '<ellipse cx="' + cx + '" cy="' + (my + 8 * s) + '" rx="' + 22 * s + '" ry="' + (m === "wow" ? 26 : 18) * s + '" fill="#7a1f3d" stroke="' + INK + '" stroke-width="' + 5 * s + '"/><ellipse cx="' + cx + '" cy="' + (my + 18 * s) + '" rx="' + 12 * s + '" ry="' + 7 * s + '" fill="#ff8fb0"/>';
          else if (m === "sad") o += '<path d="M' + (cx - 20 * s) + " " + (my + 18 * s) + " Q" + cx + " " + (my - 4 * s) + " " + (cx + 20 * s) + " " + (my + 18 * s) + '" stroke="' + INK + '" stroke-width="' + 7 * s + '" fill="none" stroke-linecap="round"/>';
          else o += '<path d="M' + (cx - 22 * s) + " " + my + " Q" + cx + " " + (my + 24 * s) + " " + (cx + 22 * s) + " " + my + '" stroke="' + INK + '" stroke-width="' + 7 * s + '" fill="none" stroke-linecap="round"/>';
          return o + "</g>";
        }
        /* body drawn in the legacy 400x400 space, shrunk into the 300x440 host box; .cf-body is scaled/glowed from paint() */
        return '<svg viewBox="0 0 300 440" width="300" height="440"><g transform="translate(6,120) scale(.72)">' +
          '<ellipse cx="200" cy="378" rx="120" ry="14" fill="rgba(60,30,70,.2)"/>' +
          '<g class="cf-body" style="transform-box:fill-box;transform-origin:50% 100%;transition:transform .5s,filter .5s">' +
          '<path d="M200 80 C300 70 350 150 335 240 C320 330 240 350 180 345 C90 340 55 270 65 190 C75 110 120 85 200 80z" fill="#ffd1dc" stroke="#e0709a" stroke-width="8"/>' +
          '<circle cx="140" cy="150" r="36" fill="#b78cf0" stroke="#7c4dcc" stroke-width="6"/><circle cx="148" cy="154" r="13" fill="#7c4dcc"/>' +
          '<circle cx="290" cy="300" r="12" fill="#ffb6cb"/><circle cx="80" cy="290" r="9" fill="#ffb6cb"/>' +
          '<ellipse class="cf-o1" cx="270" cy="170" rx="30" ry="16" fill="#ff9f6b" stroke="#c4602a" stroke-width="4" transform="rotate(-20 270 170)" style="opacity:0;transition:opacity .5s"/>' +
          '<ellipse class="cf-o2" cx="105" cy="300" rx="24" ry="14" fill="#8fdca4" stroke="#3fae6d" stroke-width="4" style="opacity:0;transition:opacity .5s"/>' +
          '<g class="cf-o3" style="opacity:0;transition:opacity .5s"><path d="M150 96 C140 56 170 48 176 30 M240 96 C262 66 238 48 250 30" stroke="#e0709a" stroke-width="10" fill="none" stroke-linecap="round"/><circle cx="176" cy="30" r="9" fill="#ffe16b"/><circle cx="250" cy="30" r="9" fill="#ffe16b"/></g>' +
          face("idle") + face("happy") + face("sad") + face("wow") +
          "</g></g></svg>";
      }
    }
  };
})();
