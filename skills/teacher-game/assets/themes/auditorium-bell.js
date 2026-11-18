/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME auditorium-bell — school auditorium stage: red curtains, wooden stage, warm spot beams, a big brass bell that brightens with progress
   and rings on every right answer, a row of students whose answer boards pop up when the class cheers, a kind teacher host.
   Reads only the shared show state S, so it works with every mechanic. Original art. */
COMP.themes["auditorium-bell"] = (function(){
  var bgLayer = null, glowLayer = null, motes = null, lastP = -1, lastG = -1, uid = 0;
  var GOLD = "#ffd54a", GOLD2 = "#c98a12", BLINE = "#6b3f05", TRIM = "#e0a84a";
  var HAIRS = ["#5a3420", "#1f1a17", "#3b2a20", "#2a2320"], UNI = ["#2f4f8f", "#3b6a52", "#7a3b3b", "#4a3f7a"];
  function layer(draw){ var c = document.createElement("canvas"); c.width = 1920; c.height = 1080; draw(c.getContext("2d")); return c; }
  function build(){
    bgLayer = layer(function(c){
      var g = c.createLinearGradient(0, 0, 0, 1080), i, x;
      g.addColorStop(0, "#2a140a"); g.addColorStop(1, "#5a2f17");
      c.fillStyle = g; c.fillRect(0, 0, 1920, 1080);
      for (i = 0; i < 17; i++){ c.fillStyle = i % 2 ? "rgba(255,210,150,.05)" : "rgba(0,0,0,.08)"; c.fillRect(i * 120, 0, 120, 900); }
      c.fillStyle = "rgba(0,0,0,.25)"; c.fillRect(0, 560, 1920, 14);
      [520, 960, 1400].forEach(function(sx){
        var rg = c.createRadialGradient(sx, 980, 10, sx, 980, 520);
        rg.addColorStop(0, "rgba(255,226,150,.3)"); rg.addColorStop(1, "rgba(255,226,150,0)");
        c.fillStyle = rg; c.fillRect(0, 300, 1920, 780);
      });
      var fy = 900, fg = c.createLinearGradient(0, fy, 0, 1080);
      fg.addColorStop(0, "#c98b4c"); fg.addColorStop(1, "#7a4b22");
      c.fillStyle = fg; c.fillRect(0, fy, 1920, 180);
      c.strokeStyle = "rgba(60,30,10,.45)"; c.lineWidth = 3;
      for (i = 0; i < 5; i++){ var yy = fy + 8 + i * i * 8; c.beginPath(); c.moveTo(0, yy); c.lineTo(1920, yy); c.stroke(); }
      for (i = -10; i <= 10; i++){ c.beginPath(); c.moveTo(960 + i * 90, fy); c.lineTo(960 + i * 150, 1080); c.stroke(); }
      c.fillStyle = TRIM; c.fillRect(0, fy - 6, 1920, 8);
      function curtain(x0, dir){
        for (var k = 0; k < 7; k++){
          var cx = x0 + dir * k * 26, cg = c.createLinearGradient(cx, 0, cx + dir * 26, 0);
          cg.addColorStop(0, "#5e0d14"); cg.addColorStop(0.5, "#b3202d"); cg.addColorStop(1, "#5e0d14");
          c.fillStyle = cg; c.fillRect(Math.min(cx, cx + dir * 26), 0, 26, 1080);
        }
        /* tie-back rope */
        c.strokeStyle = TRIM; c.lineWidth = 9; c.beginPath(); c.moveTo(x0, 640); c.quadraticCurveTo(x0 + dir * 100, 700, x0 + dir * 182, 650); c.stroke();
      }
      curtain(0, 1); curtain(1920, -1);
      c.fillStyle = "#b3202d"; c.beginPath(); c.moveTo(0, 0); c.lineTo(1920, 0); c.lineTo(1920, 30);
      for (x = 1920; x >= 80; x -= 80) c.quadraticCurveTo(x - 40, 70, x - 80, 30);
      c.closePath(); c.fill();
      c.strokeStyle = TRIM; c.lineWidth = 6; c.beginPath(); c.moveTo(0, 30);
      for (x = 0; x < 1920; x += 80) c.quadraticCurveTo(x + 40, 70, x + 80, 30);
      c.stroke();
      /* proscenium trim bar under the valance */
      c.fillStyle = "rgba(0,0,0,.35)"; c.fillRect(0, 100, 1920, 12);
    });
    glowLayer = layer(function(c){
      var rg = c.createRadialGradient(960, 640, 20, 960, 640, 900);
      rg.addColorStop(0, "rgba(255,226,140,.5)"); rg.addColorStop(1, "rgba(255,226,140,0)");
      c.fillStyle = rg; c.fillRect(0, 0, 1920, 1080);
    });
    motes = []; for (var i = 0; i < 36; i++) motes.push({ x: 200 + Math.random() * 1520, y: 300 + Math.random() * 700, v: 6 + Math.random() * 14, p: Math.random() * 6.28 });
  }

  function student(ctx, x, i, rise, t){
    var by = 1080, hy = 1000, bw = 0.9 - rise * 0.0;
    var wob = Math.sin(t * 2 + i) * 2 * rise;
    /* board (raised on cheer, otherwise tucked behind the body) */
    var up = rise * 165;
    ctx.save(); ctx.translate(x, by); ctx.rotate(Math.sin(t * 6 + i * 1.3) * 0.05 * rise);
    ctx.fillStyle = "#fff"; ctx.strokeStyle = "#3a2a1a"; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.rect(-40, -62 - up + 40, 80, 58); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#1d3c8f"; ctx.font = "900 40px sans-serif"; ctx.textAlign = "center"; ctx.fillText("O", 0, -62 - up + 40 + 44);
    ctx.restore();
    ctx.fillStyle = UNI[i % 4]; ctx.strokeStyle = "#1a1410"; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(x - 62, by); ctx.quadraticCurveTo(x - 58, hy + 30 + wob, x, hy + 30 + wob); ctx.quadraticCurveTo(x + 58, hy + 30 + wob, x + 62, by); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#ffdcbc"; ctx.beginPath(); ctx.arc(x, hy + wob, 30, 0, 6.2832); ctx.fill(); ctx.stroke();
    ctx.fillStyle = HAIRS[i % 4]; ctx.beginPath(); ctx.moveTo(x - 32, hy - 2 + wob); ctx.quadraticCurveTo(x - 32, hy - 34 + wob, x, hy - 34 + wob); ctx.quadraticCurveTo(x + 32, hy - 34 + wob, x + 32, hy - 2 + wob);
    ctx.quadraticCurveTo(x + 16, hy - 18 + wob, x, hy - 16 + wob); ctx.quadraticCurveTo(x - 16, hy - 18 + wob, x - 32, hy - 2 + wob); ctx.fill(); ctx.stroke();
  }

  var bellEls = null;
  function paint(ctx, t, dt, W, Hh, TK, S){
    if (!bgLayer) build();
    var p = S.progress, ch = Math.max(S.cheer, S.win * 0.8), i;
    ctx.save(); ctx.scale(W / 1920, Hh / 1080);
    ctx.drawImage(bgLayer, 0, 0);
    /* warm spot beams from the valance */
    ctx.globalCompositeOperation = "lighter";
    var xs = [560, 960, 1360];
    for (i = 0; i < 3; i++){
      var a = Math.sin(t * 0.5 + i * 2.1) * 0.12 * (1 - ch * 0.5), x0 = xs[i];
      ctx.globalAlpha = (0.05 + p * 0.06 + ch * 0.08) * (1 - S.lose * 0.8);
      ctx.fillStyle = "#ffeab0"; ctx.beginPath(); ctx.moveTo(x0 - 14, 70); ctx.lineTo(x0 + 14, 70);
      ctx.lineTo(x0 + Math.sin(a) * 900 + 190, 960); ctx.lineTo(x0 + Math.sin(a) * 900 - 190, 960); ctx.closePath(); ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
    var gl = Math.min(1, ch + p * 0.35);
    if (gl > 0.02){ ctx.globalAlpha = gl * (1 - S.lose * 0.8); ctx.drawImage(glowLayer, 0, 0); }
    ctx.globalAlpha = 1;
    ctx.fillStyle = "#ffebb4";
    for (i = 0; i < motes.length; i++){
      var m = motes[i]; m.y -= m.v * dt; if (m.y < 280) m.y = 1000;
      ctx.globalAlpha = 0.25 + 0.25 * Math.sin(t + m.p); ctx.fillRect(m.x + Math.sin(t * 0.7 + m.p) * 14, m.y, 4, 4);
    }
    ctx.globalAlpha = 1;
    /* students: boards pop up when the class cheers */
    var rise = Math.min(1, ch * 2.2);
    if (NG.sceneName !== "result") for (i = 0; i < 10; i++) student(ctx, 270 + i * 168, i, rise, t);
    if (S.miss > 0.02){ ctx.fillStyle = "rgba(120,10,20," + (S.miss * 0.2).toFixed(3) + ")"; ctx.fillRect(0, 0, 1920, 1080); }
    if (S.lose > 0){ ctx.fillStyle = "rgba(18,8,4,.4)"; ctx.fillRect(0, 0, 1920, 1080); }
    ctx.restore();
    /* the bell (DOM) brightens with progress and glows with the cheer */
    var g = Math.min(1, p * 0.9 + ch * 0.5);
    if (Math.abs(p - lastP) > 0.004 || Math.abs(g - lastG) > 0.02){
      lastP = p; lastG = g;
      var box = document.querySelector("#ts-deco .bl-bell");
      if (box){
        var svg = box.querySelector("svg"), glow = box.querySelector(".bl-glow");
        if (svg) svg.style.filter = "brightness(" + (0.72 + g * 0.5).toFixed(2) + ") saturate(" + (0.6 + g * 0.65).toFixed(2) + ")";
        if (glow){ glow.style.opacity = (0.1 + g * 0.9).toFixed(2); glow.style.transform = "scale(" + (0.6 + g * 0.7).toFixed(2) + ")"; }
      }
    }
  }

  function bellSvg(size){
    var id = "blg" + (++uid);
    return '<svg viewBox="0 0 200 230" width="' + size + '" height="' + Math.round(size * 1.15) + '"><defs><linearGradient id="' + id + '" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="' + GOLD2 + '"/><stop offset=".32" stop-color="' + GOLD + '"/><stop offset=".52" stop-color="#fff6c8"/><stop offset=".72" stop-color="' + GOLD + '"/><stop offset="1" stop-color="' + GOLD2 + '"/></linearGradient></defs>' +
      '<path d="M100 0 L100 18" stroke="' + BLINE + '" stroke-width="7"/>' +
      '<g class="bl-swing"><circle cx="100" cy="26" r="11" fill="none" stroke="' + BLINE + '" stroke-width="7"/>' +
      '<circle cx="100" cy="204" r="16" fill="' + GOLD2 + '" stroke="' + BLINE + '" stroke-width="6"/>' +
      '<path d="M100 34 C66 34 54 66 52 104 C50 140 40 160 22 180 L178 180 C160 160 150 140 148 104 C146 66 134 34 100 34 Z" fill="url(#' + id + ')" stroke="' + BLINE + '" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M46 152 Q100 166 154 152" fill="none" stroke="' + BLINE + '" stroke-width="4" opacity=".55"/><path d="M58 88 Q100 98 142 88" fill="none" stroke="' + BLINE + '" stroke-width="4" opacity=".4"/>' +
      '<rect x="14" y="176" width="172" height="18" rx="9" fill="' + GOLD2 + '" stroke="' + BLINE + '" stroke-width="6"/>' +
      '<path d="M76 58 Q64 98 66 140" stroke="#fff" stroke-opacity=".65" stroke-width="9" fill="none" stroke-linecap="round"/></g></svg>';
  }

  var K = { o: "#2b1a0e", sk: "#ffdcbc", top: "#3f8f5a", top2: "#2c6a41", hair: "#5a3420", pr: "#c8372d", ch: "#ff8fa3", skirt: "#3b3f6b", glass: "#7a3b1e", ink: "#4a6fb5" };
  function faces(o){
    function eye(x, r, pr, dy){
      return '<ellipse cx="' + x + '" cy="' + (140 + dy) + '" rx="' + r + '" ry="' + (r * 1.2) + '" fill="#fff" stroke="' + o + '" stroke-width="4"/>' +
        '<circle cx="' + (x + 2) + '" cy="' + (143 + dy) + '" r="' + pr + '" fill="#1b1b2f"/><circle cx="' + (x + 5) + '" cy="' + (137 + dy) + '" r="3.2" fill="#fff"/>';
    }
    return '<g class="f f-idle">' + eye(114, 13, 7, 0) + eye(186, 13, 7, 0) + '<path d="M96 112 L128 108 M172 108 L204 112" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/><path d="M126 184 Q150 204 174 184" fill="none" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/></g>' +
      '<g class="f f-happy"><path d="M98 146 Q114 124 130 146 M170 146 Q186 124 202 146" fill="none" stroke="' + o + '" stroke-width="7" stroke-linecap="round"/><path d="M120 176 Q150 224 180 176 Z" fill="#8a1f33" stroke="' + o + '" stroke-width="5" stroke-linejoin="round"/><path d="M134 198 Q150 188 166 198 Q150 214 134 198Z" fill="#ff7a8a"/></g>' +
      '<g class="f f-sad">' + eye(114, 12, 6, 4) + eye(186, 12, 6, 4) + '<path d="M96 110 L128 120 M204 110 L172 120" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/><path d="M132 198 Q150 186 168 198" fill="none" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/></g>' +
      '<g class="f f-wow">' + eye(114, 17, 9, -2) + eye(186, 17, 9, -2) + '<path d="M94 100 Q112 90 130 98 M170 98 Q188 90 206 100" fill="none" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/><ellipse cx="150" cy="194" rx="13" ry="17" fill="#8a1f33" stroke="' + o + '" stroke-width="5"/></g>';
  }
  function arm(d, f, o){ return '<path d="' + d + '" fill="none" stroke="' + o + '" stroke-width="36" stroke-linecap="round"/><path d="' + d + '" fill="none" stroke="' + f + '" stroke-width="23" stroke-linecap="round"/>'; }
  function hostSvg(){
    var o = K.o, sk = K.sk, top = K.top, top2 = K.top2, hair = K.hair, pr = K.pr, ch = K.ch;
    return '<svg viewBox="0 0 300 440" width="300" height="440">' +
      '<ellipse cx="150" cy="430" rx="92" ry="11" fill="rgba(0,0,0,.3)"/>' +
      '<rect x="116" y="360" width="26" height="58" rx="10" fill="' + sk + '" stroke="' + o + '" stroke-width="6"/><rect x="158" y="360" width="26" height="58" rx="10" fill="' + sk + '" stroke="' + o + '" stroke-width="6"/>' +
      '<path d="M100 424 Q104 410 130 412 L144 414 L144 428 Z" fill="' + pr + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/><path d="M200 424 Q196 410 170 412 L156 414 L156 428 Z" fill="' + pr + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M84 330 L216 330 L234 384 L66 384 Z" fill="' + K.skirt + '" stroke="' + o + '" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M50 120 Q40 34 150 32 Q262 34 250 120 L256 222 Q234 238 212 222 L208 130 L92 130 L88 222 Q66 238 44 222 Z" fill="' + hair + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M80 252 Q150 228 220 252 L230 344 Q150 362 70 344 Z" fill="' + top + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M124 244 L150 288 L176 244 Z" fill="#fffaf0" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/><path d="M124 244 L138 270 L150 252 L162 270 L176 244" fill="#fffaf0" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M150 288 L150 342" stroke="' + top2 + '" stroke-width="5"/><circle cx="150" cy="304" r="5" fill="#fff"/><circle cx="150" cy="326" r="5" fill="#fff"/>' +
      arm("M90 268 Q60 300 118 318", top, o) + arm("M210 268 Q246 300 196 318", top, o) +
      '<g transform="rotate(-8 160 300)"><rect x="112" y="262" width="98" height="74" rx="8" fill="#fffef8" stroke="' + o + '" stroke-width="5"/><path d="M126 282 L196 282 M126 298 L190 298 M126 314 L178 314" stroke="' + K.ink + '" stroke-width="5" stroke-linecap="round"/></g>' +
      '<circle cx="118" cy="320" r="15" fill="' + sk + '" stroke="' + o + '" stroke-width="5"/><circle cx="198" cy="318" r="15" fill="' + sk + '" stroke="' + o + '" stroke-width="5"/>' +
      '<circle cx="150" cy="142" r="94" fill="' + sk + '" stroke="' + o + '" stroke-width="7"/>' +
      '<path d="M58 130 Q66 46 150 44 Q234 46 242 130 Q214 92 176 98 Q160 76 140 98 Q96 92 58 130 Z" fill="' + hair + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M208 70 l10 -14 l10 14 l-10 14 z" fill="' + pr + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<ellipse cx="94" cy="180" rx="15" ry="8" fill="' + ch + '" opacity=".55"/><ellipse cx="206" cy="180" rx="15" ry="8" fill="' + ch + '" opacity=".55"/>' +
      faces(o) +
      '<g fill="rgba(255,255,255,.14)" stroke="' + K.glass + '" stroke-width="6"><circle cx="114" cy="141" r="27"/><circle cx="186" cy="141" r="27"/></g><path d="M141 138 Q150 130 159 138" fill="none" stroke="' + K.glass + '" stroke-width="6"/>' +
      '</svg>';
  }

  function deco(){
    return '<style>' +
      '#ts-deco .bl-bell{position:absolute;right:14px;top:128px;width:132px;height:152px;display:flex;justify-content:center;transform-origin:50% 0;transition:all .6s}' +
      '#ts-deco .bl-glow{position:absolute;left:50%;top:50%;width:300px;height:300px;margin:-150px 0 0 -150px;border-radius:50%;opacity:.1;background:radial-gradient(circle,rgba(255,230,120,.95) 0%,rgba(255,210,80,.35) 40%,rgba(255,200,60,0) 70%);transition:opacity .6s,transform .6s}' +
      '#ts-deco .bl-bell svg{position:relative;display:block;transition:filter .6s}' +
      '#ts-deco .bl-swing{transform-origin:100px 18px}' +
      '#ts-deco .bl-swing.ring{animation:blRing 1.4s ease-out}' +
      '@keyframes blRing{0%{transform:rotate(0)}12%{transform:rotate(16deg)}28%{transform:rotate(-13deg)}44%{transform:rotate(9deg)}60%{transform:rotate(-6deg)}78%{transform:rotate(3deg)}100%{transform:rotate(0)}}' +
      '#ts-deco[data-scene=title] .bl-bell,#ts-deco[data-scene=result] .bl-bell{right:auto;left:150px;top:150px;transform:scale(2.3)}' +
      'body.reduce #ts-deco .bl-swing{animation:none!important}' +
      '</style><div class="bl-bell"><div class="bl-glow"></div>' + bellSvg(132) + '</div>';
  }

  function sfx(){
    NG.defineSfx("blBell", function(){
      var f = 587;
      [1, 2.0, 2.76, 4.07, 5.4].forEach(function(r, i){ NG.tone({ type: "sine", freq: f * r, dur: 2.2 - i * 0.32, vol: 0.3 / (i + 1), jitter: 0, attack: 0.004 }); });
    });
  }

  function ring(strong){
    var sw = document.querySelector("#ts-deco .bl-swing"), box = document.querySelector("#ts-deco .bl-bell");
    if (sw){ sw.classList.remove("ring"); void sw.getBoundingClientRect(); sw.classList.add("ring"); }
    NG.sfx("blBell");
    if (box){ var c = U.center(box); NG.fx.sparkle(c.x, c.y, strong ? 30 : 16); }
  }
  function onReact(kind){
    if (kind === "correct") ring(false);
    else if (kind === "win"){ ring(true); NG.after(1500, function(){ ring(true); }); NG.after(700, function(){ NG.fx.confetti(); }); }
  }

  return {
    paint: paint, deco: deco, sfx: sfx, onReact: onReact,
    host: { svg: hostSvg, name: "종소리 선생님", lines: {
      title: ["종을 울려 볼까요?"], start: ["첫 문제! 집중해요"],
      correct: ["딩동댕! 종이 울려요!", "정답이에요!", "훌륭해요!"], wrong: ["아쉬워요, 같이 봐요", "괜찮아요! 다음에!"],
      win: ["종이 울렸어요!", "모두 멋진 도전!"], lose: ["다음엔 꼭 울려요"] } }
  };
})();
