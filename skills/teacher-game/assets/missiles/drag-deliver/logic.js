/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* drag-deliver missile · 끌어서 보내기
   Drag (or tap) the item to the right destination. All text comes from GAME.items + GAME.world.
   items: [{q, a, wrong?:[..], exp?, say?}]   world.skin: post-office | cell-feed | recycle
   Modes: per-question destinations (a + wrong / auto distractors, shuffled) or fixed bins
   (world.bins, or automatically when the items use 2-4 different answers and no item has wrong). */
window.GAME_LOGIC = (function(){
  var U = NG.util, G = window.GAME, WD = G.world || {};
  var SKIN = WD.skin || "post-office";
  try { document.body.setAttribute("data-world", SKIN); } catch (e) {}

  function T(k, d){ var v = WD[k]; return (v === undefined || v === null || v === "") ? d : v; }
  function fillT(s, map){ s = String(s); for (var k in map) s = s.split("{" + k + "}").join(String(map[k])); return s; }
  function $(id){ return document.getElementById(id); }
  function units(s){ var u = 0, i, c; s = String(s); for (i = 0; i < s.length; i++){ c = s.charCodeAt(i); u += c === 32 ? 0.32 : (c < 128 ? (c >= 65 && c <= 90 ? 0.7 : 0.58) : 1.02); } return u; }
  /* largest font size (step 2) so the text fits width x lines */
  function fit(text, base, min, width, lines){ var u = units(text), fs = base; while (fs > min && Math.ceil(u * fs / width) > lines) fs -= 2; return fs; }
  /* measured pass: shrink until the box no longer overflows (then allow breaking long words) */
  function shrink(el, box, min){
    if (!el) return; box = box || el;
    var fs = parseFloat(el.style.fontSize) || 40, n = 0;
    function over(){ return box.scrollHeight > box.clientHeight + 2 || box.scrollWidth > box.clientWidth + 2; }
    while (n++ < 40 && fs > min && over()){ fs -= 2; el.style.fontSize = fs + "px"; }
    if (over()){ el.style.wordBreak = "break-all"; n = 0; while (n++ < 6 && over()){ fs -= 2; el.style.fontSize = fs + "px"; } }
  }
  function uniq(arr){ var seen = {}, out = []; arr.forEach(function(x){ x = String(x); if (!seen[x]){ seen[x] = 1; out.push(x); } }); return out; }
  function fx(){ return !NG.calm; }

  /* ---------- speech (optional) ---------- */
  function speakText(it){ if (!it) return ""; if (it.say) return String(it.say); return WD.speak ? String(it.q) : ""; }
  function say(text){
    if (!text) return;
    try {
      if (NG.audio.muted || !window.TSVoice || !TSVoice.supported) return;
      var rt = +T("rate", 0);
      TSVoice.speak(text, rt ? {lang: T("lang", "en-US"), rate: rt} : {lang: T("lang", "en-US")});
    } catch (e) {}
  }

  /* =====================================================================
     SKIN 1 · post-office — 달밤 우체국 마을 (cat mailman, houses, village lamps, fireworks)
     ===================================================================== */
  var ROOF = ["#e4572e", "#3a86ff", "#1fa89a", "#8e5bd9"];
  function catSvg(mood, size){
    var eyes, mouth, ink = "#6b3a14";
    if (mood === "happy"){
      eyes = '<path d="M68 100 q10 -14 20 0 M112 100 q10 -14 20 0" stroke="' + ink + '" stroke-width="6" fill="none" stroke-linecap="round"/>';
      mouth = '<path d="M84 116 q16 24 32 0 Z" fill="#7a1f3d" stroke="' + ink + '" stroke-width="4" stroke-linejoin="round"/>';
    } else if (mood === "sad"){
      eyes = '<path d="M66 84 l20 6 M134 84 l-20 6" stroke="' + ink + '" stroke-width="4" stroke-linecap="round"/><circle cx="78" cy="100" r="7" fill="#1b1b2f"/><circle cx="122" cy="100" r="7" fill="#1b1b2f"/>';
      mouth = '<path d="M88 126 q12 -10 24 0" fill="none" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/>';
    } else {
      eyes = '<ellipse cx="78" cy="96" rx="10" ry="12" fill="#fff" stroke="' + ink + '" stroke-width="3"/><ellipse cx="122" cy="96" rx="10" ry="12" fill="#fff" stroke="' + ink + '" stroke-width="3"/><circle cx="80" cy="98" r="6" fill="#1b1b2f"/><circle cx="124" cy="98" r="6" fill="#1b1b2f"/>';
      mouth = mood === "wow" ? '<ellipse cx="100" cy="124" rx="8" ry="10" fill="#7a1f3d" stroke="' + ink + '" stroke-width="3"/>' : '<path d="M86 120 q14 12 28 0" fill="none" stroke="' + ink + '" stroke-width="5" stroke-linecap="round"/>';
    }
    return '<svg viewBox="0 0 200 220" width="' + size + '" height="' + Math.round(size * 1.1) + '">' +
      '<ellipse cx="100" cy="212" rx="60" ry="8" fill="rgba(0,0,0,.25)"/>' +
      '<path d="M150 172 C192 162 198 122 176 104" fill="none" stroke="#a85a14" stroke-width="18" stroke-linecap="round"/>' +
      '<path d="M150 172 C192 162 198 122 176 104" fill="none" stroke="#ffa94d" stroke-width="10" stroke-linecap="round"/>' +
      '<ellipse cx="100" cy="160" rx="54" ry="48" fill="#ffa94d" stroke="#a85a14" stroke-width="6"/>' +
      '<ellipse cx="100" cy="172" rx="30" ry="28" fill="#ffe3c2"/>' +
      '<path d="M62 126 L134 194" stroke="#6b3a14" stroke-width="10" stroke-linecap="round"/>' +
      '<rect x="110" y="170" width="52" height="38" rx="8" fill="#8a4b1c" stroke="#4e2a0e" stroke-width="5"/>' +
      '<rect x="116" y="178" width="40" height="8" rx="3" fill="#ffd23f"/>' +
      '<path d="M52 66 L56 20 L90 46 Z" fill="#ffa94d" stroke="#a85a14" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M148 66 L144 20 L110 46 Z" fill="#ffa94d" stroke="#a85a14" stroke-width="6" stroke-linejoin="round"/>' +
      '<circle cx="100" cy="90" r="50" fill="#ffa94d" stroke="#a85a14" stroke-width="6"/>' +
      '<path d="M52 72 C56 22 144 22 148 72 Z" fill="#2f6fe0" stroke="#173f8f" stroke-width="6" stroke-linejoin="round"/>' +
      '<rect x="96" y="64" width="72" height="12" rx="6" fill="#173f8f"/>' +
      '<circle cx="100" cy="46" r="11" fill="#ffd23f" stroke="#b8860b" stroke-width="3"/>' + eyes +
      '<path d="M94 108 L106 108 L100 115 Z" fill="#ff7a9a"/>' + mouth +
      '<ellipse cx="66" cy="114" rx="9" ry="6" fill="#ff7a9a" opacity=".45"/><ellipse cx="134" cy="114" rx="9" ry="6" fill="#ff7a9a" opacity=".45"/>' +
      '<path d="M56 108 L34 104 M56 116 L34 122 M144 108 L166 104 M144 116 L166 122" stroke="#6b3a14" stroke-width="3" stroke-linecap="round"/></svg>';
  }
  function mailboxSvg(size){
    return '<svg viewBox="0 0 180 220" width="' + size + '" height="' + Math.round(size * 1.22) + '">' +
      '<rect x="68" y="120" width="24" height="96" fill="#7a4a22"/>' +
      '<path d="M20 120 L20 70 Q80 10 140 70 L140 120 Z" fill="#d93a3f" stroke="#7d1f1f" stroke-width="6"/>' +
      '<rect x="44" y="82" width="72" height="12" rx="6" fill="#3b0d0d"/>' +
      '<rect x="140" y="50" width="8" height="52" fill="#7a4a22"/><polygon points="148,50 176,60 148,72" fill="#ffd23f" stroke="#b8860b" stroke-width="3"/></svg>';
  }
  function houseSvg(kind, col){
    var dk = NG.shade(col, -0.4), roof;
    if (kind === 0) roof = '<polygon points="16,122 200,12 384,122" fill="' + col + '" stroke="' + dk + '" stroke-width="6" stroke-linejoin="round"/>';
    else if (kind === 1) roof = '<rect x="20" y="84" width="360" height="46" rx="10" fill="' + col + '" stroke="' + dk + '" stroke-width="6"/><line x1="320" y1="84" x2="320" y2="26" stroke="#7a4a22" stroke-width="6"/><polygon points="320,26 374,42 320,58" fill="#ffd23f" stroke="#b8860b" stroke-width="4"/>';
    else if (kind === 2) roof = '<path d="M30 126 Q200 -40 370 126 Z" fill="' + col + '" stroke="' + dk + '" stroke-width="6" stroke-linejoin="round"/>';
    else roof = '<rect x="290" y="30" width="44" height="76" fill="#a85a3a" stroke="#6b3a24" stroke-width="5"/><polygon points="16,122 200,40 384,122" fill="' + col + '" stroke="' + dk + '" stroke-width="6" stroke-linejoin="round"/>';
    return '<svg viewBox="0 0 400 320" width="400" height="320"><rect x="40" y="108" width="320" height="208" rx="12" fill="#f6dfb4" stroke="#7a4a22" stroke-width="6"/>' + roof +
      '<rect class="win" x="60" y="138" width="50" height="30" rx="6"/><rect class="win" x="290" y="138" width="50" height="30" rx="6"/></svg>';
  }
  function lampSvg(size){
    return '<svg class="lamp" viewBox="0 0 64 64" width="' + size + '" height="' + size + '"><polygon points="4,30 32,6 60,30" fill="#c0482a"/><rect x="10" y="28" width="44" height="30" fill="#e9d3a8"/><rect class="win" x="24" y="36" width="16" height="14" rx="2"/></svg>';
  }
  var nightStars = [], nightCity = [], i0;
  for (i0 = 0; i0 < 90; i0++) nightStars.push({x:(i0 * 197) % 1920, y:(i0 * 83) % 520 + 10, s:1 + (i0 % 3), p:i0 * 1.3});
  for (i0 = 0; i0 < 22; i0++) nightCity.push({x:i0 * 92 - 20, w:70 + (i0 * 37) % 40, h:70 + (i0 * 53) % 120, p:i0 * 0.9});
  function paintNight(c, t, dt, W, H){
    var i, s, b, g;
    g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "#1d1450"); g.addColorStop(1, "#6a2a78"); c.fillStyle = g; c.fillRect(0, 0, W, H);
    for (i = 0; i < nightStars.length; i++){ s = nightStars[i]; c.globalAlpha = 0.35 + 0.65 * Math.abs(Math.sin(t * 0.8 + s.p)); c.fillStyle = "#fff"; c.fillRect(s.x, s.y, s.s * 2, s.s * 2); }
    g = c.createRadialGradient(1640, 190, 10, 1640, 190, 150); g.addColorStop(0, "rgba(255,243,196,.95)"); g.addColorStop(0.4, "rgba(255,243,196,.35)"); g.addColorStop(1, "rgba(255,243,196,0)");
    c.globalAlpha = 1; c.fillStyle = g; c.fillRect(1480, 30, 320, 320);
    c.fillStyle = "#fff3c4"; c.beginPath(); c.arc(1640, 190, 58, 0, 6.283); c.fill();
    for (i = 0; i < 3; i++){ var cx = (t * 14 * (i + 1) + i * 700) % (W + 400) - 200; c.globalAlpha = 0.16; c.fillStyle = "#ffd6f2"; c.beginPath(); c.ellipse(cx, 330 + i * 70, 190, 34, 0, 0, 6.283); c.fill(); }
    c.globalAlpha = 1;
    c.fillStyle = "rgba(40,14,70,.55)"; c.beginPath(); c.moveTo(0, H);
    for (i = 0; i <= W; i += 40) c.lineTo(i, 880 + Math.sin(i / 260) * 40);
    c.lineTo(W, H); c.fill();
    for (i = 0; i < nightCity.length; i++){
      b = nightCity[i]; c.fillStyle = "rgba(26,10,56,.7)"; c.fillRect(b.x, 940 - b.h, b.w, b.h + 140);
      c.fillStyle = "rgba(255,224,102," + (0.35 + 0.35 * Math.abs(Math.sin(t * 0.5 + b.p))) + ")"; c.fillRect(b.x + 14, 940 - b.h + 18, 12, 14); c.fillRect(b.x + b.w - 28, 940 - b.h + 18, 12, 14);
    }
    c.fillStyle = "rgba(20,8,46,.75)"; c.beginPath(); c.moveTo(0, H);
    for (i = 0; i <= W; i += 40) c.lineTo(i, 990 + Math.sin(i / 180 + 1) * 24);
    c.lineTo(W, H); c.fill();
    var cols = ["#ff5a8a", "#ffd23f", "#3ee6ff", "#9b7bff", "#2ecf8f"];
    c.globalAlpha = 0.85;
    for (i = 0; i < 24; i++){
      var fx0 = 40 + i * 80, fy = 22 + Math.sin(i * 0.5 + t * 1.2) * 4 - Math.pow((i % 6) / 3 - 1, 2) * 10;
      c.fillStyle = cols[i % 5]; c.beginPath(); c.moveTo(fx0 - 20, fy); c.lineTo(fx0 + 20, fy); c.lineTo(fx0, fy + 38); c.closePath(); c.fill();
    }
    c.globalAlpha = 1;
  }
  var POST = {
    L: {dest:{x0:40, x1:1880, y:410, w:400, h:320}, lab:{w:320, base:62, min:40}, item:{x:660, y:790, w:600, h:228, base:96, min:52, lines:1}, banner:{w:1500, base:50, min:36, lines:1}, after:{x:330, y:790, w:1500, h:228, head:66}, hero:200},
    bg: paintNight,
    hero: function(mood){ return catSvg(mood, 200); },
    dest: function(k){ return houseSvg(k % 4, ROOF[k % 4]); },
    itemEnter: [{transform:"translateY(260px) scale(.6)", opacity:0}, {transform:"translateY(0) scale(1)", opacity:1}],
    titleArt: function(){ return '<div class="dd-ta1">' + catSvg("happy", 300) + '</div><div class="dd-ta2">' + mailboxSvg(250) + '</div>'; },
    growth: {
      n:0, lit:0,
      build: function(el, n){
        this.n = n; this.lit = 0;
        var size = Math.max(36, Math.min(72, Math.floor(1460 / n) - 8)), w = n * (size + 8), lh = "", i;
        for (i = 0; i < n; i++) lh += lampSvg(size);
        el.innerHTML = '<div id="dd-gn" class="dd-gn">' + U.esc(T("growLabel", "💡")) + ' 0 / ' + n + '</div>' +
          '<div id="dd-lamps" class="dd-lamps" style="left:' + Math.round((1920 - w) / 2) + 'px;width:' + w + 'px">' + lh + '</div>';
      },
      add: function(i, kind){
        if (kind !== "first" && kind !== "second") return null;
        this.lit++;
        var lp = document.querySelectorAll("#dd-lamps .lamp")[i];
        if (lp){ lp.setAttribute("class", "lamp lit"); var c = U.center(lp); NG.fx.sparkle(c.x, c.y, 16); NG.anim(lp, [{transform:"scale(1)"}, {transform:"scale(1.5)"}, {transform:"scale(1)"}], {duration:420}); }
        var gn = $("dd-gn"); if (gn) gn.textContent = T("growLabel", "💡") + " " + this.lit + " / " + this.n;
        return null;
      },
      count: function(){ return this.lit; }
    },
    finale: function(){
      var n = Math.min(10, Math.max(5, POST.growth.lit)), k, cols = ["#ff5a8a", "#ffd23f", "#3ee6ff", "#9b7bff", "#2ecf8f", "#ffffff"];
      for (k = 0; k < n; k++) (function(k){
        NG.after(300 + k * 300, function(){
          if (fx()) NG.sfx("explode");
          NG.fx.burst(U.rand(300, 1620), U.rand(420, 760), {count:fx() ? 60 : 20, speed:800, gravity:450, life:1.4, colors:[cols[k % 6], cols[(k + 2) % 6], "#ffffff"]});
        });
      })(k);
      Array.prototype.forEach.call(document.querySelectorAll("#dd-lamps .lamp"), function(lp, j){ NG.after(j * 60, function(){ NG.anim(lp, [{transform:"translateY(0)"}, {transform:"translateY(-18px)"}, {transform:"translateY(0)"}], {duration:420}); }); });
      return 300 + n * 300 + 700;
    }
  };

  /* =====================================================================
     SKIN 2 · cell-feed — 몸속 마을 먹이 주기 (Mongle evolves, tower of levels grows)
     ===================================================================== */
  var INK = "#3b2a4a";
  function mFace(cx, cy, s, m){
    var e = 11 * s, o = "<g>";
    if (m === "happy") o += '<path d="M' + (cx - 45 * s) + " " + cy + " q" + 11 * s + " " + (-16 * s) + " " + 22 * s + ' 0 M' + (cx + 23 * s) + " " + cy + " q" + 11 * s + " " + (-16 * s) + " " + 22 * s + ' 0" stroke="' + INK + '" stroke-width="' + 7 * s + '" fill="none" stroke-linecap="round"/>';
    else o += '<circle cx="' + (cx - 34 * s) + '" cy="' + cy + '" r="' + e + '" fill="' + INK + '"/><circle cx="' + (cx + 34 * s) + '" cy="' + cy + '" r="' + e + '" fill="' + INK + '"/><circle cx="' + (cx - 30 * s) + '" cy="' + (cy - 4 * s) + '" r="' + 4 * s + '" fill="#fff"/><circle cx="' + (cx + 38 * s) + '" cy="' + (cy - 4 * s) + '" r="' + 4 * s + '" fill="#fff"/>';
    o += '<ellipse cx="' + (cx - 58 * s) + '" cy="' + (cy + 22 * s) + '" rx="' + 13 * s + '" ry="' + 8 * s + '" fill="#ff7aa8" opacity=".55"/><ellipse cx="' + (cx + 58 * s) + '" cy="' + (cy + 22 * s) + '" rx="' + 13 * s + '" ry="' + 8 * s + '" fill="#ff7aa8" opacity=".55"/>';
    var my = cy + 30 * s;
    if (m === "wow" || m === "happy") o += '<ellipse cx="' + cx + '" cy="' + (my + 8 * s) + '" rx="' + 22 * s + '" ry="' + (m === "wow" ? 26 : 18) * s + '" fill="#7a1f3d" stroke="' + INK + '" stroke-width="' + 5 * s + '"/><ellipse cx="' + cx + '" cy="' + (my + 18 * s) + '" rx="' + 12 * s + '" ry="' + 7 * s + '" fill="#ff8fb0"/>';
    else if (m === "sad") o += '<path d="M' + (cx - 20 * s) + " " + (my + 18 * s) + " Q" + cx + " " + (my - 4 * s) + " " + (cx + 20 * s) + " " + (my + 18 * s) + '" stroke="' + INK + '" stroke-width="' + 7 * s + '" fill="none" stroke-linecap="round"/>';
    else o += '<path d="M' + (cx - 22 * s) + " " + my + " Q" + cx + " " + (my + 24 * s) + " " + (cx + 22 * s) + " " + my + '" stroke="' + INK + '" stroke-width="' + 7 * s + '" fill="none" stroke-linecap="round"/>';
    return o + "</g>";
  }
  function nuc(x, y, r){ return '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="#b78cf0" stroke="#7c4dcc" stroke-width="6"/><circle cx="' + (x + r * 0.2) + '" cy="' + (y + r * 0.1) + '" r="' + r * 0.35 + '" fill="#7c4dcc"/>'; }
  function mongle(stage, m, size){
    var s = '<svg viewBox="0 0 400 400" width="' + size + '" height="' + size + '"><ellipse cx="200" cy="378" rx="120" ry="14" fill="rgba(60,30,70,.2)"/>';
    if (stage <= 0){
      s += '<path d="M200 80 C300 70 350 150 335 240 C320 330 240 350 180 345 C90 340 55 270 65 190 C75 110 120 85 200 80z" fill="#ffd1dc" stroke="#e0709a" stroke-width="8"/>' + nuc(140, 150, 36) + '<circle cx="290" cy="300" r="12" fill="#ffb6cb"/><circle cx="80" cy="290" r="9" fill="#ffb6cb"/>' + mFace(215, 235, 1, m);
    } else if (stage === 1){
      s += '<circle cx="110" cy="250" r="84" fill="#ffe0a8" stroke="#e08a3a" stroke-width="7"/>' + nuc(90, 230, 24) + '<circle cx="290" cy="250" r="84" fill="#c9f0d4" stroke="#3fae6d" stroke-width="7"/>' + nuc(312, 230, 24) + '<circle cx="200" cy="130" r="84" fill="#d6e6ff" stroke="#5b8de0" stroke-width="7"/>' + nuc(160, 112, 24) +
        '<circle cx="200" cy="245" r="96" fill="#ffd1dc" stroke="#e0709a" stroke-width="8"/>' + nuc(150, 205, 26) + mFace(215, 255, 0.8, m);
    } else if (stage === 2){
      s += '<path d="M135 105 C135 55 235 55 255 105 C285 165 335 225 285 300 C245 350 135 345 112 275 C95 225 135 190 135 105z" fill="#ff9a8b" stroke="#d9534f" stroke-width="8"/><path d="M150 70 C140 40 170 30 175 20 M240 75 C262 48 235 30 248 14" stroke="#d9534f" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M150 230 q30 25 62 0" stroke="#ffd0c8" stroke-width="7" fill="none" opacity=".7"/>' + mFace(205, 215, 0.95, m);
    } else if (stage === 3){
      s += '<ellipse cx="200" cy="215" rx="125" ry="140" fill="#ffe3a3" stroke="#d99a2b" stroke-width="8"/><ellipse cx="200" cy="300" rx="78" ry="48" fill="#fff6dc" stroke="#d99a2b" stroke-width="5"/><path d="M150 300 q15 -24 30 0 t30 0 t30 0" stroke="#ff8fa3" stroke-width="9" fill="none" stroke-linecap="round"/><path d="M200 262 c-20 -22 -44 6 0 30 c44 -24 20 -52 0 -30z" fill="#ff5a6e"/>' + mFace(200, 175, 0.95, m);
    } else {
      s += '<path d="M135 140 C95 20 135 0 160 90z" fill="#fff" stroke="#8a6a86" stroke-width="7"/><path d="M265 140 C305 20 265 0 240 90z" fill="#fff" stroke="#8a6a86" stroke-width="7"/><path d="M143 120 C122 50 140 30 152 88z" fill="#ffb6cb"/><path d="M257 120 C278 50 260 30 248 88z" fill="#ffb6cb"/>' +
        '<ellipse cx="200" cy="300" rx="100" ry="70" fill="#fff" stroke="#8a6a86" stroke-width="7"/><circle cx="200" cy="190" r="100" fill="#fff" stroke="#8a6a86" stroke-width="7"/><ellipse cx="130" cy="362" rx="46" ry="20" fill="#fff" stroke="#8a6a86" stroke-width="6"/><ellipse cx="270" cy="362" rx="46" ry="20" fill="#fff" stroke="#8a6a86" stroke-width="6"/><path d="M188 222 l12 12 12 -12z" fill="#ff7aa8"/>' + mFace(200, 185, 0.95, m);
    }
    return s + "</svg>";
  }
  var CELLC = [["#ffc2d4", "#e0709a"], ["#bdf0cc", "#3fae6d"], ["#ffe596", "#d99a2b"], ["#c4dbff", "#5b8de0"]];
  var CELLP = [
    "M150 16 C228 16 278 60 278 112 C278 164 228 204 150 204 C72 204 22 164 22 112 C22 60 72 16 150 16Z",
    "M58 48 C108 4 212 12 254 50 C294 88 284 166 228 190 C170 214 92 208 50 172 C12 138 20 82 58 48Z",
    "M68 40 C120 0 196 30 232 28 C282 26 292 120 252 170 C210 214 108 210 64 178 C18 146 24 76 68 40Z",
    "M62 20 L238 20 Q282 20 282 64 L282 160 Q282 204 238 204 L62 204 Q18 204 18 160 L18 64 Q18 20 62 20Z"
  ];
  function cellRoom(k){
    var c = CELLC[k % 4], p = CELLP[k % 4], org;
    if (k % 4 === 0) org = nuc(78, 76, 24) + '<circle cx="236" cy="160" r="9" fill="' + c[1] + '" opacity=".5"/>';
    else if (k % 4 === 1) org = '<ellipse cx="236" cy="78" rx="26" ry="14" fill="#ff9f6b" stroke="#c4602a" stroke-width="4" transform="rotate(-20 236 78)"/><path d="M216 80 q8 -8 14 0 t14 0 t14 0" stroke="#c4602a" stroke-width="3" fill="none" transform="rotate(-20 236 78)"/>' + nuc(74, 92, 20);
    else if (k % 4 === 2) org = '<circle cx="84" cy="66" r="10" fill="' + c[1] + '" opacity=".55"/><circle cx="226" cy="64" r="14" fill="' + c[1] + '" opacity=".45"/><circle cx="70" cy="170" r="8" fill="' + c[1] + '" opacity=".5"/>' + nuc(232, 156, 18);
    else org = '<rect x="32" y="34" width="236" height="156" rx="34" fill="none" stroke="' + c[1] + '" stroke-width="4" stroke-dasharray="10 8" opacity=".7"/><ellipse cx="66" cy="66" rx="18" ry="11" fill="#5cc98a" stroke="#2f8a57" stroke-width="3"/><ellipse cx="236" cy="168" rx="18" ry="11" fill="#5cc98a" stroke="#2f8a57" stroke-width="3"/><ellipse cx="240" cy="62" rx="18" ry="11" fill="#5cc98a" stroke="#2f8a57" stroke-width="3"/>';
    return '<svg viewBox="0 0 300 210" width="300" height="210"><path d="' + p + '" fill="' + c[0] + '" stroke="' + c[1] + '" stroke-width="8"/>' + org +
      '<circle cx="126" cy="106" r="10" fill="' + INK + '"/><circle cx="174" cy="106" r="10" fill="' + INK + '"/><circle cx="129" cy="102" r="3.5" fill="#fff"/><circle cx="177" cy="102" r="3.5" fill="#fff"/>' +
      '<ellipse cx="104" cy="126" rx="11" ry="7" fill="#ff7aa8" opacity=".5"/><ellipse cx="196" cy="126" rx="11" ry="7" fill="#ff7aa8" opacity=".5"/>' +
      '<path class="hv-off" d="M136 132 Q150 146 164 132" stroke="' + INK + '" stroke-width="6" fill="none" stroke-linecap="round"/>' +
      '<g class="hv-on"><ellipse cx="150" cy="142" rx="20" ry="24" fill="#7a1f3d" stroke="' + INK + '" stroke-width="5"/><ellipse cx="150" cy="154" rx="11" ry="7" fill="#ff8fb0"/></g></svg>';
  }
  var blobs = [];
  for (i0 = 0; i0 < 18; i0++) blobs.push({x:(i0 * 263) % 1920, y:(i0 * 151) % 1080, r:30 + (i0 * 37) % 90, v:10 + (i0 * 7) % 20, p:i0 * 0.7});
  function paintBody(c, t, dt, W, H){
    var g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "#fff4e6"); g.addColorStop(1, "#ffd9e8"); c.fillStyle = g; c.fillRect(0, 0, W, H);
    c.strokeStyle = "rgba(224,112,154,.16)"; c.lineWidth = 46; c.lineCap = "round";
    c.beginPath(); c.moveTo(-50, 1000); c.bezierCurveTo(500, 900, 700, 1080, 1200, 980); c.bezierCurveTo(1500, 920, 1700, 1040, 1980, 960); c.stroke();
    blobs.forEach(function(b){
      b.y -= b.v * dt; if (b.y < -b.r){ b.y = H + b.r; b.x = Math.random() * W; }
      var x = b.x + Math.sin(t * 0.6 + b.p) * 30;
      c.fillStyle = "rgba(255,150,190,0.15)"; c.beginPath(); c.arc(x, b.y, b.r, 0, 6.283); c.fill();
      c.strokeStyle = "rgba(224,112,154,0.22)"; c.lineWidth = 6; c.stroke();
      c.fillStyle = "rgba(160,120,230,0.18)"; c.beginPath(); c.arc(x + b.r * 0.2, b.y - b.r * 0.15, b.r * 0.32, 0, 6.283); c.fill();
    });
  }
  var FCOL = ["#ff9fbf", "#ffb877", "#ffe16b", "#8fdca4", "#8cc8ff"];
  var CELL = {
    L: {dest:{x0:540, x1:1880, y:150, w:300, h:340}, lab:{w:262, base:50, min:34}, item:{x:560, y:580, w:900, h:250, base:54, min:40, lines:3}, banner:{w:920, base:34, min:30, lines:2}, after:{x:540, y:560, w:940, h:300, head:50}, hero:380},
    bg: paintBody,
    hero: function(mood, stage){ return mongle(stage || 0, mood, 380); },
    dest: function(k){ return cellRoom(k); },
    destStyle: function(k){ return "border-color:" + CELLC[k % 4][1]; },
    itemEnter: [{transform:"translateY(200px) scale(.5,.3)", opacity:0}, {transform:"translateY(-20px) scale(1.05,.95)", opacity:1, offset:.7}, {transform:"translateY(0) scale(1)", opacity:1}],
    titleArt: function(){ return '<div class="dd-ta1">' + mongle(0, "happy", 460) + '</div><div class="dd-ta2">' + mongle(4, "idle", 220) + '</div>'; },
    growth: {
      n:0, filled:0, sizes:[], starts:[], done:0,
      build: function(el, n){
        var nf = Math.max(1, Math.min(5, n)), f, html = "", lv = T("levels", ["1층", "2층", "3층", "4층", "5층"]), fh = 112, gap = 12;
        this.n = n; this.filled = 0; this.sizes = []; this.starts = []; this.done = 0;
        var acc = 0;
        for (f = 0; f < nf; f++){ var s = Math.floor(n / nf) + (f < n % nf ? 1 : 0); this.sizes.push(s); this.starts.push(acc); acc += s; }
        var top = 1000 - nf * (fh + gap);
        html += '<div class="dd-roof" style="top:' + (top - 150) + 'px"><svg viewBox="0 0 460 140" width="460" height="140"><path d="M20 136 Q230 -20 440 136 Z" fill="#ffd1dc" stroke="#e0709a" stroke-width="8"/><circle cx="230" cy="56" r="16" fill="#fff" stroke="#e0709a" stroke-width="5"/></svg><div id="dd-flag" class="dd-flag">🚩</div><div class="dd-roof-t">' + U.esc(T("towerTitle", "")) + '</div></div>';
        for (f = 0; f < nf; f++){
          var sz = Math.max(30, Math.min(78, Math.floor((236 - 8 * (this.sizes[f] - 1)) / this.sizes[f]))), sl = "", j;
          for (j = 0; j < this.sizes[f]; j++) sl += '<span class="dd-slot" id="dd-sl' + (this.starts[f] + j) + '" style="width:' + sz + 'px;height:' + Math.min(70, sz) + 'px;font-size:' + Math.round(Math.min(70, sz) * 0.55) + 'px"></span>';
          html += '<div class="dd-floor" id="dd-fl' + f + '" style="top:' + (1000 - (f + 1) * (fh + gap) + gap) + 'px;height:' + fh + 'px"><span class="dd-fn">' + U.esc(lv[f] != null ? lv[f] : (f + 1) + "층") + '</span><span class="dd-slots">' + sl + '</span></div>';
        }
        el.innerHTML = '<div class="dd-tower">' + html + '</div>';
      },
      add: function(i, kind){
        var sl = $("dd-sl" + i); if (!sl || sl.getAttribute("data-on")) return null;
        sl.setAttribute("data-on", "1"); this.filled++;
        var f = 0; while (f + 1 < this.starts.length && i >= this.starts[f + 1]) f++;
        sl.className = "dd-slot on " + kind; sl.style.background = kind === "first" || kind === "second" ? FCOL[f % 5] : "#efe6ee";
        sl.textContent = kind === "first" ? "★" : (kind === "second" ? "✓" : "·"); NG.fx.pop(sl);
        var full = true, j; for (j = 0; j < this.sizes[f]; j++){ var e = $("dd-sl" + (this.starts[f] + j)); if (!e || !e.getAttribute("data-on")) full = false; }
        if (full){
          var fl = $("dd-fl" + f); fl.classList.add("lit"); this.done++;
          if (this.done >= this.sizes.length){ var fg = $("dd-flag"); if (fg) fg.style.opacity = 1; }
          return {level: fl.querySelector(".dd-fn").textContent, stage: Math.min(4, this.done)};
        }
        return null;
      },
      count: function(){ return this.filled; }
    },
    finale: function(){
      var h = $("dd-hero");
      setStage(4); setMood("happy");
      if (h){ h.classList.add("big"); }
      [0, 1, 2].forEach(function(k){ NG.after(200 + k * 520, function(){ if (h) NG.anim(h.firstChild, [{transform:"translateY(0) scale(1)"}, {transform:"translateY(-90px) scale(1.08,.95)"}, {transform:"translateY(0) scale(1)"}], {duration:480, easing:"cubic-bezier(.33,1.4,.6,1)"}); if (fx()) NG.sfx("jump"); }); });
      Array.prototype.forEach.call(document.querySelectorAll(".dd-floor"), function(fl, j){ NG.after(j * 140, function(){ fl.classList.add("lit"); NG.fx.pop(fl); }); });
      NG.after(500, function(){ if (fx()){ NG.fx.confetti(); NG.fx.rain("✨", {count:24}); } else NG.fx.sparkle(1680, 640, 20); });
      return 2600;
    }
  };

  /* =====================================================================
     SKIN 3 · recycle — 분리수거 로봇 공장 (robot, conveyor belt, bins, battery that charges)
     ===================================================================== */
  var BINC = ["#2fb36d", "#2f86e0", "#f2b01e", "#e2574c"];
  function robotSvg(mood, w){
    var scr = mood === "sad" ? "#ffb3a7" : "#7cf7c8", eye, mouth;
    if (mood === "happy") eye = '<path d="M80 96 q14 -20 28 0 M132 96 q14 -20 28 0" stroke="' + scr + '" stroke-width="9" fill="none" stroke-linecap="round"/>';
    else if (mood === "sad") eye = '<path d="M80 78 l24 8 M160 78 l-24 8" stroke="' + scr + '" stroke-width="7" stroke-linecap="round"/><rect x="84" y="92" width="20" height="14" rx="6" fill="' + scr + '"/><rect x="136" y="92" width="20" height="14" rx="6" fill="' + scr + '"/>';
    else if (mood === "wow") eye = '<circle cx="94" cy="88" r="15" fill="' + scr + '"/><circle cx="146" cy="88" r="15" fill="' + scr + '"/><circle cx="99" cy="83" r="5" fill="#0f2233"/><circle cx="151" cy="83" r="5" fill="#0f2233"/>';
    else eye = '<rect x="84" y="72" width="20" height="30" rx="9" fill="' + scr + '"/><rect x="136" y="72" width="20" height="30" rx="9" fill="' + scr + '"/>';
    if (mood === "happy") mouth = '<path d="M100 108 q20 16 40 0" stroke="' + scr + '" stroke-width="7" fill="none" stroke-linecap="round"/>';
    else if (mood === "sad") mouth = '<path d="M104 118 q16 -10 32 0" stroke="' + scr + '" stroke-width="7" fill="none" stroke-linecap="round"/>';
    else if (mood === "wow") mouth = '<ellipse cx="120" cy="114" rx="8" ry="9" fill="' + scr + '"/>';
    else mouth = '<rect x="106" y="110" width="28" height="7" rx="3.5" fill="' + scr + '"/>';
    var chest = mood === "sad" ? "#ff8a7a" : (mood === "happy" ? "#5dff9d" : "#ffd23f");
    return '<svg viewBox="0 0 240 300" width="' + w + '" height="' + Math.round(w * 1.25) + '">' +
      '<ellipse cx="120" cy="292" rx="88" ry="8" fill="rgba(0,0,0,.3)"/>' +
      '<rect x="44" y="246" width="152" height="40" rx="20" fill="#2b3440" stroke="#11161d" stroke-width="6"/>' +
      '<circle cx="70" cy="266" r="10" fill="#8a96a6"/><circle cx="120" cy="266" r="10" fill="#8a96a6"/><circle cx="170" cy="266" r="10" fill="#8a96a6"/>' +
      '<path d="M58 182 Q22 196 24 234" stroke="#11161d" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M58 182 Q22 196 24 234" stroke="#9aa7b8" stroke-width="11" fill="none" stroke-linecap="round"/>' +
      '<path d="M10 236 q14 22 30 0" stroke="#11161d" stroke-width="9" fill="none" stroke-linecap="round"/>' +
      '<path d="M182 182 Q220 166 222 128" stroke="#11161d" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M182 182 Q220 166 222 128" stroke="#9aa7b8" stroke-width="11" fill="none" stroke-linecap="round"/>' +
      '<path d="M206 126 q16 -24 32 0" stroke="#11161d" stroke-width="9" fill="none" stroke-linecap="round"/>' +
      '<rect x="52" y="150" width="136" height="104" rx="24" fill="#ff9f43" stroke="#7a3d0c" stroke-width="7"/>' +
      '<rect x="80" y="170" width="80" height="58" rx="12" fill="#1c2a3b" stroke="#7a3d0c" stroke-width="4"/>' +
      '<path d="M124 176 l-18 26 h14 l-6 20 l24 -30 h-14 l8 -16z" fill="' + chest + '"/>' +
      '<circle cx="66" cy="240" r="5" fill="#7a3d0c"/><circle cx="174" cy="240" r="5" fill="#7a3d0c"/>' +
      '<rect x="104" y="132" width="32" height="24" fill="#5b6675" stroke="#11161d" stroke-width="5"/>' +
      '<rect x="16" y="66" width="20" height="42" rx="7" fill="#5b6675" stroke="#11161d" stroke-width="5"/><rect x="204" y="66" width="20" height="42" rx="7" fill="#5b6675" stroke="#11161d" stroke-width="5"/>' +
      '<rect x="30" y="34" width="180" height="106" rx="32" fill="#3ecbb8" stroke="#145e57" stroke-width="7"/>' +
      '<rect x="52" y="54" width="136" height="74" rx="22" fill="#0f2233"/>' + eye + mouth +
      '<line x1="120" y1="34" x2="120" y2="12" stroke="#11161d" stroke-width="6"/><circle class="dd-ant" cx="120" cy="11" r="10" fill="#ff5a8a" stroke="#11161d" stroke-width="4"/></svg>';
  }
  function flameSvg(){ return '<svg viewBox="0 0 120 120" width="120" height="120"><path d="M60 0 C90 40 100 70 60 120 C20 70 30 40 60 0Z" fill="#ffb02e"/><path d="M60 24 C78 52 80 76 60 104 C40 76 42 52 60 24Z" fill="#fff1a8"/></svg>'; }
  function binSvg(k){
    var col = BINC[k % 4], dk = NG.shade(col, -0.38), lt = NG.shade(col, 0.22);
    return '<svg viewBox="0 0 380 300" width="380" height="300">' +
      '<g class="dd-lid"><rect x="22" y="22" width="336" height="30" rx="12" fill="' + lt + '" stroke="' + dk + '" stroke-width="6"/><rect x="160" y="6" width="60" height="22" rx="8" fill="' + dk + '"/></g>' +
      '<path d="M38 62 L342 62 L316 284 L64 284 Z" fill="' + col + '" stroke="' + dk + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<rect x="28" y="52" width="324" height="24" rx="9" fill="' + dk + '"/>' +
      '<path d="M98 92 L112 272 M282 92 L268 272" stroke="' + dk + '" stroke-width="6" opacity=".4" stroke-linecap="round"/>' +
      '<circle cx="104" cy="288" r="11" fill="#2b3440" stroke="#11161d" stroke-width="4"/><circle cx="276" cy="288" r="11" fill="#2b3440" stroke="#11161d" stroke-width="4"/></svg>';
  }
  var gears = [{x:1800, y:250, r:120, n:12, s:0.18}, {x:1640, y:130, r:70, n:9, s:-0.3}, {x:110, y:120, r:80, n:10, s:0.24}];
  var sparks = []; for (i0 = 0; i0 < 26; i0++) sparks.push({x:(i0 * 331) % 1920, y:(i0 * 197) % 1080, v:16 + (i0 * 7) % 24, p:i0});
  function gearPath(c, r, n){
    c.beginPath(); var k, a;
    for (k = 0; k < n * 4; k++){ a = k * Math.PI * 2 / (n * 4); var rr = (k % 4 < 2) ? r : r * 0.82; c.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
    c.closePath();
  }
  function paintFactory(c, t, dt, W, H){
    var g = c.createLinearGradient(0, 0, 0, H), i, x;
    g.addColorStop(0, "#13293a"); g.addColorStop(1, "#24485a"); c.fillStyle = g; c.fillRect(0, 0, W, H);
    for (i = 0; i < 4; i++){
      x = 250 + i * 430;
      c.fillStyle = "rgba(110,200,235,.09)"; c.fillRect(x, 120, 300, 280);
      c.strokeStyle = "rgba(150,215,240,.16)"; c.lineWidth = 10; c.strokeRect(x, 120, 300, 280);
      c.beginPath(); c.moveTo(x + 150, 120); c.lineTo(x + 150, 400); c.moveTo(x, 260); c.lineTo(x + 300, 260); c.stroke();
    }
    c.lineCap = "butt";
    c.strokeStyle = "rgba(255,159,67,.20)"; c.lineWidth = 30; c.beginPath(); c.moveTo(0, 585); c.lineTo(W, 585); c.stroke();
    c.strokeStyle = "rgba(62,203,184,.16)"; c.lineWidth = 22; c.beginPath(); c.moveTo(1890, 0); c.lineTo(1890, 585); c.stroke();
    for (i = 0; i < gears.length; i++){
      var gg = gears[i]; c.save(); c.translate(gg.x, gg.y); c.rotate(t * gg.s);
      gearPath(c, gg.r, gg.n); c.fillStyle = "rgba(255,255,255,.07)"; c.fill();
      c.beginPath(); c.arc(0, 0, gg.r * 0.32, 0, 6.283); c.fillStyle = "rgba(0,0,0,.25)"; c.fill(); c.restore();
    }
    for (i = 0; i < sparks.length; i++){
      var s = sparks[i]; s.y -= s.v * dt; if (s.y < 0) s.y = H;
      c.globalAlpha = 0.25 + 0.25 * Math.sin(t * 2 + s.p); c.fillStyle = "#ffd23f"; c.fillRect(s.x, s.y, 4, 4);
    }
    c.globalAlpha = 1;
    c.fillStyle = "#18262f"; c.fillRect(0, 1004, W, 76);
    for (x = -80; x < W + 80; x += 90){ c.fillStyle = "#f2b01e"; c.beginPath(); c.moveTo(x, 1012); c.lineTo(x + 45, 1012); c.lineTo(x + 5, 1080); c.lineTo(x - 40, 1080); c.closePath(); c.fill(); }
  }
  var RECY = {
    L: {dest:{x0:200, x1:1880, y:620, w:380, h:370}, lab:{w:262, base:56, min:40}, item:{x:780, y:272, w:600, h:188, base:76, min:48, lines:2}, banner:{w:1130, base:46, min:34, lines:1}, after:{x:470, y:164, w:1130, h:296, head:58}, hero:240},
    bg: paintFactory,
    hero: function(mood){ return robotSvg(mood, 240); },
    dest: function(k){ return binSvg(k); },
    deco: function(){
      var r = "", i; for (i = 0; i < 15; i++) r += '<circle cx="' + (40 + i * 114) + '" cy="32" r="18" fill="#5b6675" stroke="#11161d" stroke-width="4"/>';
      return '<div class="dd-belt"><div class="dd-belt-run"></div><svg class="dd-roll" viewBox="0 0 1700 64" width="1700" height="64">' + r + '</svg></div>';
    },
    itemEnter: [{transform:"translateX(-640px)", opacity:0}, {transform:"translateX(-640px)", opacity:1, offset:.05}, {transform:"translateX(20px)", opacity:1, offset:.85}, {transform:"translateX(0)", opacity:1}],
    titleArt: function(){ return '<div class="dd-ta1">' + robotSvg("happy", 330) + '</div><div class="dd-ta2">' + binSvg(0) + '</div><div class="dd-ta3">' + binSvg(1) + '</div>'; },
    growth: {
      n:0, on:0,
      build: function(el, n){
        this.n = n; this.on = 0;
        var top = 160, h = 760, segH = Math.max(14, Math.min(64, Math.floor((h - 40 - 8 * (n + 1)) / n))), segs = "", i;
        for (i = 0; i < n; i++) segs += '<div class="dd-seg" id="dd-seg' + i + '" style="height:' + segH + 'px"></div>';
        var bh = n * (segH + 8) + 8;
        el.innerHTML = '<div class="dd-bat" style="top:' + (top + 30 + (h - 40 - bh)) + 'px;height:' + bh + 'px"><div class="dd-bat-cap"></div>' + segs + '</div>' +
          '<div id="dd-gn" class="dd-gn">' + U.esc(T("growLabel", "⚡")) + ' 0/' + n + '</div>';
      },
      add: function(i, kind){
        var s = $("dd-seg" + i); if (!s || s.getAttribute("data-on")) return null;
        s.setAttribute("data-on", "1"); s.className = "dd-seg " + kind;
        if (kind === "first" || kind === "second"){ this.on++; s.textContent = "⚡"; var c = U.center(s); NG.fx.sparkle(c.x, c.y, 12); }
        var gn = $("dd-gn"); if (gn) gn.textContent = T("growLabel", "⚡") + " " + this.on + "/" + this.n;
        return null;
      },
      count: function(){ return this.on; }
    },
    finale: function(){
      var h = $("dd-hero"); setMood("wow");
      Array.prototype.forEach.call(document.querySelectorAll(".dd-seg"), function(s, j){ NG.after(j * 70, function(){ s.classList.add("flash"); }); });
      NG.after(700, function(){
        setMood("happy");
        if (h){ h.classList.add("fly"); h.appendChild(U.h("div", {class:"dd-flame"}, flameSvg())); NG.anim(h, [{transform:"translate(0,0)"}, {transform:"translate(40px,30px)", offset:.15}, {transform:"translate(760px,-900px) rotate(12deg)"}], {duration:1700, easing:"cubic-bezier(.5,0,.7,.4)", fill:"forwards"}); }
        if (fx()){ NG.sfx("whoosh"); NG.fx.rain("⚙️", {count:22}); }
      });
      NG.after(1500, function(){ if (fx()){ NG.sfx("explode"); NG.fx.confetti(); } NG.fx.burst(1150, 300, {count:fx() ? 70 : 20, speed:900, colors:["#ffd23f", "#3ecbb8", "#ff9f43", "#ffffff"]}); });
      return 3000;
    }
  };

  var SKINS = {"post-office":POST, "cell-feed":CELL, "recycle":RECY};
  var ART = SKINS[SKIN] || POST, L = ART.L;

  /* ---------- content ---------- */
  var ALL = (G.items || []).filter(function(it){ return it && it.q != null && it.a != null && String(it.a) !== ""; });
  var BINS = null;
  (function(){
    var hasWrong = ALL.some(function(it){ return it.wrong && it.wrong.length; }), ua = uniq(ALL.map(function(it){ return it.a; }));
    var wb = WD.bins && WD.bins.length >= 2 ? uniq(WD.bins).slice(0, 4) : null;
    if (wb && ua.every(function(a){ return wb.indexOf(a) >= 0; })) BINS = wb;
    else if (!hasWrong && ua.length >= 2 && ua.length <= 4) BINS = ua;
  })();
  function buildOptions(it){
    var a = String(it.a);
    if (BINS && BINS.indexOf(a) >= 0) return BINS.slice();
    var n = U.clamp(+T("dests", 4) || 4, 2, 4), wrong;
    if (it.wrong && it.wrong.length) wrong = uniq(it.wrong).filter(function(w){ return w !== a; });
    else wrong = U.shuffle(uniq(ALL.map(function(x){ return x.a; })).filter(function(x){ return x !== a; }));
    return U.shuffle([a].concat(wrong.slice(0, n - 1)));
  }

  /* ---------- state ---------- */
  var items = [], idx = -1, cur = null, opts = [], correctK = 0, destEls = [], destKey = "", itemEl = null;
  var locked = true, done = true, tries = 0, maxTries = 2, missed = false, retry = false, grown = 0, firstOk = 0;
  var mood = "idle", stage = 0, moodTimer = null, handAnim = null;

  /* ---------- hero ---------- */
  function drawHero(){ var h = $("dd-hero"); if (h) h.firstChild.innerHTML = ART.hero(mood, stage); }
  function setMood(m){ if (m === mood) return; mood = m; drawHero(); }
  function setStage(s){ if (s === stage) return; stage = s; drawHero(); }
  function heroReact(ok){
    setMood(ok ? "happy" : "sad"); NG.cancel(moodTimer);
    var h = $("dd-hero");
    if (h && ok) NG.anim(h.firstChild, [{transform:"translateY(0)"}, {transform:"translateY(-80px)"}, {transform:"translateY(0)"}], {duration:480, easing:"cubic-bezier(.33,1.4,.6,1)"});
    else if (h) NG.fx.wobble(h.firstChild);
    moodTimer = NG.after(1100, function(){ if (cur && !done) setMood("idle"); });
  }
  function talk(key){
    var b = $("dd-talk"), lines = WD.talk || null;
    if (!b || !lines || !lines[key]) return;
    b.style.display = "block"; b.textContent = lines[key]; NG.fx.pop(b);
  }

  /* ---------- small UI helpers ---------- */
  function turnText(){ var t = NG.currentTeam(); return t && NG.state.teams.length > 1 ? t.icon + " " + t.name + " 차례 · " : ""; }
  function setBanner(txt){ var b = $("dd-banner"), B = L.banner; if (b){ b.textContent = txt; if (B && txt){ b.style.wordBreak = ""; b.style.fontSize = fit(txt, B.base, B.min, B.w - 60, B.lines) + "px"; shrink(b, null, B.min - 4); } b.style.visibility = txt ? "visible" : "hidden"; } }
  function clearAfter(){ var a = $("dd-after-box"); if (a) a.innerHTML = ""; }
  function recordOf(it){ return it.q + " → " + it.a; }
  function clearHand(){ if (handAnim){ try { handAnim.cancel(); } catch (e) {} handAnim = null; } var h = $("dd-hand"); if (h) h.style.display = "none"; }
  function showHand(){
    var h = $("dd-hand"); if (!h || !destEls.length) return;
    var a = {x:L.item.x + L.item.w / 2, y:L.item.y + L.item.h / 2}, d0 = destEls[0], dl = destEls[destEls.length - 1];
    var b = {x:(parseFloat(d0.style.left) + parseFloat(dl.style.left) + parseFloat(dl.style.width)) / 2, y:parseFloat(d0.style.top) + parseFloat(d0.style.height) / 2};
    var dx = Math.round(b.x - a.x), dy = Math.round(b.y - a.y);
    h.style.left = (a.x - 30) + "px"; h.style.top = (a.y - 20) + "px"; h.style.display = "block";
    handAnim = NG.anim(h, [{transform:"translate(0,0)", opacity:0}, {transform:"translate(0,0)", opacity:1, offset:.15}, {transform:"translate(" + dx + "px," + dy + "px)", opacity:1, offset:.75}, {transform:"translate(" + dx + "px," + dy + "px)", opacity:0}], {duration:2300, iterations:Infinity, easing:"ease-in-out"});
    setBanner(T("guide", "👆 끌어다 놓아요 · 눌러서 골라도 돼요"));
  }
  function hoverAt(k){ destEls.forEach(function(d, j){ d.classList.toggle("hover", j === k); }); }
  function hoverIndex(){ if (!itemEl) return -1; var c = U.center(itemEl), k; for (k = 0; k < destEls.length; k++) if (NG.hitTest(c, destEls[k])) return k; return -1; }
  function mark(d, ok){
    var old = d.querySelector(".dd-mk"); if (old) old.parentNode.removeChild(old);
    var m = U.h("div", {class:"dd-mk " + (ok ? "ok" : "no")}, ok ? "✔" : "✖"); d.appendChild(m);
    NG.anim(m, [{transform:"scale(0) rotate(-40deg)"}, {transform:"scale(1.25)"}, {transform:"scale(1)"}], {duration:380, easing:"ease-out"});
  }
  function flyInto(d){
    if (!itemEl) return; var it = itemEl; it.style.pointerEvents = "none"; NG.snap(it, d);
    NG.after(280, function(){
      var tr = "translate(" + (it._dx || 0) + "px," + (it._dy || 0) + "px)";
      NG.anim(it, [{transform:tr + " scale(1)", opacity:1}, {transform:tr + " scale(.15)", opacity:0}], {duration:320, easing:"ease-in", fill:"forwards"});
      NG.after(330, function(){ it.style.visibility = "hidden"; });
    });
  }

  /* ---------- title ---------- */
  NG.scene("title", function(el){
    NG.state.phase = "title"; NG.hud.show = false; NG.hud.render(); NG.timer.stop(); NG.bg.custom(ART.bg);
    var teams = G.teams || 0, title = String(G.title || ""), tw = SKIN === "post-office" ? 1500 : 1000, tb = SKIN === "post-office" ? 180 : 140;
    var fs = fit(title, tb, 100, tw, 1); if (Math.ceil(units(title) * fs / tw) > 1) fs = fit(title, tb, 72, tw, 2);
    var ci = 0, chars = title.split(" ").map(function(word){
      return '<span style="white-space:nowrap;display:inline-block">' + Array.prototype.map.call(word, function(c){ ci++; return '<span class="ch" style="animation-delay:' + (ci * 0.06) + 's">' + U.esc(c) + "</span>"; }).join("") + "</span>";
    }).join(" ");
    var how = T("how", []); if (typeof how === "string") how = [how];
    var tablet = teams === 0 && G.teamChoice === false;
    el.innerHTML = '<div class="dd-title">' +
      (T("titleTag", "") ? '<div class="dd-ttag enter">' + U.esc(T("titleTag", "")) + '</div>' : "") +
      '<div class="title dd-tname"style="font-size:' + fs + 'px">' + chars + '</div>' +
      '<div class="dd-tsub enter" style="animation-delay:.3s">' + U.esc(G.subtitle || "") + '</div>' +
      (how.length ? '<div class="dd-how enter" style="animation-delay:.45s">' + how.map(U.esc).join("<br>") + '</div>' : "") +
      (tablet ? '<div class="dd-rot enter">' + U.esc(T("rotateHint", "📱 태블릿을 가로로 돌려 주세요")) + '</div>' : "") +
      '<div class="row dd-teams enter" id="t-teams" style="animation-delay:.6s"></div>' +
      '<button class="btn pulse enter" id="t-start" style="animation-delay:.75s">' + U.esc(T("startLabel", "▶ 시작!")) + '</button></div>' +
      '<div class="dd-tart">' + ART.titleArt() + '</div>';
    var box = el.querySelector("#t-teams");
    if (G.teamChoice !== false){
      [0, 2, 3, 4].forEach(function(n){
        var b = U.h("button", {class:"btn small " + (n === teams ? "" : "secondary")}, n === 0 ? "개인" : n + "팀");
        NG.button(b, function(){ teams = n; Array.prototype.forEach.call(box.children, function(c){ c.classList.add("secondary"); }); b.classList.remove("secondary"); NG.fx.pop(b); });
        box.appendChild(b);
      });
    } else box.style.display = "none";
    var a1 = el.querySelector(".dd-ta1");
    NG.after(900, function(){ if (a1) NG.anim(a1, [{transform:"translateY(0)"}, {transform:"translateY(-90px)"}, {transform:"translateY(0)"}], {duration:560, easing:"cubic-bezier(.33,1.4,.6,1)"}); });
    NG.button(el.querySelector("#t-start"), function(){ NG.unlockAudio(); NG.setupTeams(teams); NG.sfx("select"); NG.go("countdown"); });
  });

  /* ---------- play scene ---------- */
  NG.scene("dd-play", function(el){
    NG.bg.custom(ART.bg);
    el.innerHTML = '<div class="dd-layer" id="dd-grow"></div>' +
      '<div class="dd-layer">' + (ART.deco ? ART.deco() : "") + '</div>' +
      '<div class="dd-banner" id="dd-banner"></div>' +
      '<div class="dd-layer" id="dd-dests"></div>' +
      '<div class="dd-hero" id="dd-hero"><div class="dd-hero-in"></div></div>' +
      '<div class="dd-talk" id="dd-talk" style="display:none"></div>' +
      '<div class="dd-layer" id="dd-itembox"></div>' +
      '<div class="dd-layer" id="dd-after-box"></div>' +
      '<div class="dd-hand" id="dd-hand">👆</div>';
    ART.growth.build($("dd-grow"), items.length);
    mood = "idle"; stage = 0; drawHero(); destKey = "";
    talk("start");
    show(0);
  });

  function start(list){
    retry = !!list;
    var base = ALL.slice();
    items = list || (T("shuffle", true) === false ? base : U.shuffle(base));
    idx = -1; grown = 0; firstOk = 0; cur = null; locked = true; done = true; NG.state.total = items.length;
    NG.teacher.hooks = {
      next: function(){ if (done) next(); },
      skip: function(){ if (!cur) return; if (done) next(); else skip(); },
      reveal: function(){ if (cur && !done) reveal(false); }
    };
    NG.retryWrong = function(){
      var w = items.filter(function(it){ return it._wrong; });
      if (!w.length) return;
      var tn = NG.state.teams.length;
      NG.state = {score:0, combo:0, maxCombo:0, correct:0, wrong:0, total:0, wrongList:[], teams:[], turn:0, phase:"play"};
      NG.setupTeams(tn); w.forEach(function(it){ it._wrong = false; });
      GAME_LOGIC._pending = w; NG.go("countdown");
    };
    items.forEach(function(it){ it._wrong = false; });
    if (!items.length){ NG.finish({total:1, title:T("emptyLine", "문제가 없어요")}); return; }
    NG.go("dd-play");
  }

  function show(i){
    idx = i; NG.timer.stop(); clearHand();
    if (idx >= items.length) return finale();
    cur = items[idx]; tries = 0; missed = false; done = false; locked = false;
    opts = buildOptions(cur); correctK = opts.indexOf(String(cur.a));
    maxTries = Math.max(1, Math.min(+T("tries", 2) || 2, opts.length - 1));
    var be = G.bonusEvery == null ? 4 : (G.bonusEvery | 0);
    cur._bonus = !retry && be > 0 && (idx + 1) % be === 0;
    NG.hud.setProgress(idx / items.length);
    setBanner(turnText() + T("instruction", "알맞은 곳으로 끌어다 놓아요!"));
    clearAfter(); buildDests(); buildItem();
    if (idx > 0) talk(stage >= 3 ? "almost" : "next");
    if (cur._bonus){ NG.fx.badge(T("bonusBadge", "⭐ 보너스!"), "info", 1000); NG.sfx("powerup"); }
    if (G.timer) NG.timer.start(G.timer, function(){ if (!done) reveal(true); });
    var st = speakText(cur); if (st && T("autoSpeak", true) !== false) NG.after(500, function(){ if (cur && !done) say(st); });
    if (idx === 0 && !retry && T("tutorial", true) !== false) NG.after(700, function(){ if (idx === 0 && !done && itemEl && !itemEl._touched) showHand(); });
  }

  function buildDests(){
    var key = opts.join("\u0001"), box = $("dd-dests");
    if (key === destKey){
      destEls.forEach(function(d){ d.className = "dd-dest"; var m = d.querySelector(".dd-mk"); if (m) m.parentNode.removeChild(m); });
      return;
    }
    destKey = key; box.innerHTML = ""; destEls = [];
    var D = L.dest, n = opts.length, gap = (D.x1 - D.x0 - n * D.w) / (n + 1);
    var hints = WD.destHints || {};
    opts.forEach(function(lab, k){
      var fs = fit(lab, L.lab.base, L.lab.min, L.lab.w * 0.9, 2), x = Math.round(D.x0 + gap + k * (D.w + gap));
      var d = U.h("div", {class:"dd-dest", "data-k":k, "data-label":lab, style:"left:" + x + "px;top:" + D.y + "px;width:" + D.w + "px;height:" + D.h + "px"},
        ART.dest(k, n) + '<div class="dd-lab" style="font-size:' + fs + 'px;' + (ART.destStyle ? ART.destStyle(k) : "") + '">' + U.esc(lab) + '</div>' +
        (hints[lab] ? '<div class="dd-hint">' + U.esc(hints[lab]) + '</div>' : ""));
      d.addEventListener("pointerdown", function(e){ if (NG.paused || locked || done || d.classList.contains("tried")) return; e.preventDefault(); NG.sfx("tap"); deliver(k, true); });
      box.appendChild(d); destEls.push(d); shrink(d.querySelector(".dd-lab"), null, L.lab.min);
      NG.anim(d, [{transform:"translateY(70px) scale(.9)", opacity:0}, {transform:"translateY(0) scale(1)", opacity:1}], {duration:420, delay:k * 80, easing:"cubic-bezier(.34,1.56,.64,1)", fill:"backwards"});
    });
  }

  function buildItem(){
    var box = $("dd-itembox"); box.innerHTML = "";
    var I = L.item, q = String(cur.q), fs = fit(q, I.base, I.min, I.w - 90, I.lines);
    var tag = cur._bonus ? T("bonusTag", "⭐ 보너스 · 점수 2배") : T("itemTag", "");
    itemEl = U.h("div", {class:"dd-item" + (cur._bonus ? " gold" : ""), style:"left:" + I.x + "px;top:" + I.y + "px;width:" + I.w + "px;height:" + I.h + "px"},
      '<div class="dd-item-in">' + (tag ? '<div class="dd-tag">' + U.esc(tag) + '</div>' : "") + '<div class="dd-q" style="font-size:' + fs + 'px">' + U.esc(q) + '</div></div>' +
      (speakText(cur) ? '<div class="dd-say" title="듣기">🔊</div>' : ""));
    box.appendChild(itemEl); shrink(itemEl.querySelector(".dd-q"), itemEl.querySelector(".dd-item-in"), I.min);
    NG.anim(itemEl, ART.itemEnter, {duration:SKIN === "recycle" ? 800 : 480, delay:150, easing:"cubic-bezier(.3,1.2,.6,1)", fill:"backwards"});
    var my = itemEl;
    NG.drag(itemEl, {
      onStart: function(){ my._touched = true; clearHand(); if (cur && !done) setMood("wow"); },
      onMove: function(){ if ((my._moved || 0) > 18) my.classList.add("drag"); hoverAt(hoverIndex()); },
      onDrop: function(c){
        hoverAt(-1); if (locked || done || my !== itemEl) return false;
        for (var k = 0; k < destEls.length; k++) if (NG.hitTest(c, destEls[k]) && !destEls[k].classList.contains("tried")) return deliver(k, false);
        if (cur && !done) setMood("idle");
        return false;
      },
      onTap: function(e){
        var t = e && e.target;
        if (t && t.closest && t.closest(".dd-say")){ say(speakText(cur)); if (cur && !done) setMood("idle"); return false; }
        if (locked || done) return false;
        my.classList.add("sel"); setBanner(turnText() + T("tapHint", "👆 이제 보낼 곳을 눌러요")); if (cur && !done) setMood("idle");
        return false;
      },
      onEnd: function(ok){ hoverAt(-1); if (!ok) my.classList.remove("drag"); }
    });
  }

  function growthAdd(kind){
    var r = ART.growth.add(idx, kind);
    if (r && r.stage != null){
      var before = stage; setStage(r.stage);
      if (r.stage > before){
        NG.sfx("levelup"); if (fx()) NG.fx.flash("#ffffff", 0.4);
        NG.after(450, function(){ NG.fx.badge(fillT(T("levelBadge", "{level} 완성!"), {level:r.level}), "good", 1500); });
        talk("grow");
      }
    }
  }

  function deliver(k, viaTap){
    if (locked || done) return false;
    var d = destEls[k]; if (!d || d.classList.contains("tried")) return false;
    clearHand(); if (itemEl) itemEl._touched = true;
    if (k === correctK){
      done = true; locked = true; NG.timer.stop();
      var first = !missed, pts = (first ? 100 : 50) * (cur._bonus ? 2 : 1), c = U.center(d);
      flyInto(d); d.classList.add("open"); mark(d, true);
      if (first){ firstOk++; NG.feedback(true, d, {text:T("goodBadge", "정답!")}); }
      else { NG.sfx("correct"); NG.fx.sparkle(c.x, c.y, 18); NG.fx.badge("✔ " + T("secondBadge", "정답!"), "good", 900); }
      NG.addScore(pts, null, c);
      grown++; growthAdd(first ? "first" : "second");
      heroReact(true); talk("good");
      if (fx() && T("rain", "")) NG.fx.rain(T("rain", ""), {count:14});
      var st = speakText(cur); if (st) NG.after(550, function(){ say(st); });
      showAfter(true);
      return true;
    }
    tries++;
    d.classList.add("tried"); mark(d, false);
    if (!missed){ cur._wrong = true; NG.feedback(false, d, {text:T("wrongBadge", "다시 해 봐요!"), record:recordOf(cur)}); }
    else { NG.sfx("wrong"); NG.fx.wobble(d); }
    missed = true; heroReact(false); talk("wrong");
    if (tries >= maxTries){ locked = true; NG.after(850, function(){ reveal(false); }); }
    else setBanner(turnText() + T("retryLine", "🙌 한 번 더 생각해 봐요!"));
    return false;
  }

  function reveal(timeout){
    if (!cur || done) return;
    done = true; locked = true; NG.timer.stop(); clearHand();
    var d = destEls[correctK];
    if (!missed){ cur._wrong = true; NG.feedback(false, d, {silentBadge:true, record:recordOf(cur)}); }
    missed = true;
    NG.fx.badge(timeout ? T("timeUp", "⏰ 시간 끝!") : T("revealBadge", "정답은 여기!"), "info", 1000);
    if (d){ d.classList.add("open"); mark(d, true); flyInto(d); }
    growthAdd("miss"); setMood("idle");
    var st = speakText(cur); if (st) NG.after(550, function(){ say(st); });
    showAfter(false);
  }

  function skip(){
    if (!cur || done) return;
    done = true; locked = true; NG.timer.stop(); clearHand();
    growthAdd("skip");
    NG.nextTurn(); show(idx + 1);
  }

  function showAfter(ok){
    var box = $("dd-after-box"); if (!box || !cur) return;
    var A = L.after, last = idx + 1 >= items.length;
    var head = WD.pairJoin != null ? (cur.q + WD.pairJoin + cur.a) : (T("answerPrefix", "정답: ") + cur.a);
    var sub = cur.exp || (ok ? T("afterGood", "") : T("afterBad", ""));
    var hfs = fit((ok ? "✔ " : "💡 ") + head, A.head, 36, A.w - 420, 2);
    box.innerHTML = '<div class="dd-after card enter" style="left:' + A.x + 'px;top:' + A.y + 'px;width:' + A.w + 'px;min-height:' + A.h + 'px">' +
      '<div class="dd-after-t"><div class="dd-after-h" style="font-size:' + hfs + 'px">' + (ok ? "✔ " : "💡 ") + U.esc(head) + '</div>' +
      (sub ? '<div class="dd-after-s">' + U.esc(sub) + '</div>' : "") + '</div>' +
      '<button class="btn dd-next" id="dd-next">' + U.esc(last ? T("lastLabel", "결과 보기 ▶") : T("nextLabel", "다음 ▶")) + '</button></div>';
    var hb = $("dd-banner"); if (hb && SKIN === "recycle") hb.style.visibility = "hidden";
    NG.button($("dd-next"), next);
  }

  function next(){
    if (!done || !cur) return;
    cur = null; NG.nextTurn(); show(idx + 1);
  }

  /* signature finale: each skin's big scene, then the result */
  function finale(){
    locked = true; done = true; cur = null; NG.timer.stop(); NG.hud.setProgress(1); clearHand();
    clearAfter(); var ib = $("dd-itembox"); if (ib) ib.innerHTML = ""; var db = $("dd-dests"); if (db) db.innerHTML = ""; destEls = []; destKey = "";
    var all = grown === items.length;
    setBanner(all ? T("finaleLine", "🎉 완성!") : T("finaleLineSome", T("finaleLine", "🎉 완성!")));
    NG.fx.badge(T("finaleBadge", "🎉 완성!"), "info", 2000); NG.sfx("fanfare");
    talk("end");
    var ms = ART.finale(all) || 2000;
    NG.after(ms, function(){
      NG.finish({total:items.length, title:all ? T("endAll", "모두 성공!") : T("endSome", "끝까지 해냈어요!"),
        lines:[fillT(T("countLine", "{n} / {total}"), {n:grown, total:items.length})], unit:T("unit", "점")});
    });
  }

  return {
    start: function(){ var p = GAME_LOGIC._pending; GAME_LOGIC._pending = null; start(p || null); },
    toText: function(){
      return {skin:SKIN, index:idx, total:items.length, locked:locked, done:done, q:cur ? cur.q : null, answer:cur ? String(cur.a) : null,
        answerIndex:cur ? correctK : -1, dests:opts.slice(), fixedBins:!!BINS, tries:tries, maxTries:maxTries, grown:grown, firstTry:firstOk, stage:stage, bonus:!!(cur && cur._bonus)};
    }
  };
})();
