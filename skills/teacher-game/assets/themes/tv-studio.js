/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* THEME tv-studio — live TV quiz-show set: LED wall, chasing bulbs, sweeping spotlights, podium lamps, ON AIR + APPLAUSE signs,
   host Mr. Q. Reads only the shared show state S (progress builds the lamps/wall, cheer lights everything, miss flashes red,
   win = full celebration, lose = lights down), so it works with every mechanic. Original art. */
COMP.themes["tv-studio"] = (function(){
  var bgLayer = null, vigLayer = null, tvTimer = null;
  var L1 = "#ff3d7f", L2 = "#3fd0ff", BULB = "#ffd23f", LAMPS = 36;
  function layer(draw){ var c = document.createElement("canvas"); c.width = 1920; c.height = 1080; draw(c.getContext("2d")); return c; }
  function build(){
    bgLayer = layer(function(c){
      var g = c.createLinearGradient(0, 0, 0, 1080), r, k;
      g.addColorStop(0, "#0a0620"); g.addColorStop(0.72, "#26093f"); g.addColorStop(1, "#08030f");
      c.fillStyle = g; c.fillRect(0, 0, 1920, 1080);
      c.fillStyle = "rgba(255,255,255,.05)";
      for (r = 0; r < 13; r++) for (k = 0; k < 32; k++) c.fillRect(22 + k * 60, 142 + r * 58, 22, 22);
      c.fillStyle = "#14102a"; c.fillRect(0, 112, 1920, 16);
      c.fillStyle = "#0d0820"; c.fillRect(0, 0, 1920, 112);
      c.fillStyle = "rgba(255,255,255,.04)"; c.fillRect(0, 110, 1920, 3);
      var fg = c.createLinearGradient(0, 900, 0, 1080);
      fg.addColorStop(0, "#2a1450"); fg.addColorStop(1, "#05020c");
      c.fillStyle = fg; c.fillRect(0, 900, 1920, 180);
      c.strokeStyle = "rgba(255,255,255,.09)"; c.lineWidth = 2;
      for (k = -8; k <= 8; k++){ c.beginPath(); c.moveTo(960 + k * 60, 900); c.lineTo(960 + k * 260, 1080); c.stroke(); }
      /* podium row (front edge of the stage): the lamp bulbs are drawn per frame */
      for (k = 0; k < 6; k++){
        var px = 250 + k * 280;
        c.fillStyle = "#3a2a66"; c.beginPath(); c.moveTo(px, 1010); c.lineTo(px + 250, 1010); c.lineTo(px + 262, 1080); c.lineTo(px - 12, 1080); c.closePath(); c.fill();
        c.fillStyle = "#120a24"; c.fillRect(px - 4, 1004, 258, 10);
        c.fillStyle = "rgba(255,255,255,.08)"; c.fillRect(px, 1014, 250, 6);
      }
    });
    vigLayer = layer(function(c){
      var rg = c.createRadialGradient(960, 560, 120, 960, 560, 940);
      rg.addColorStop(0, "rgba(10,6,32,.58)"); rg.addColorStop(0.55, "rgba(10,6,32,.32)"); rg.addColorStop(1, "rgba(10,6,32,0)");
      c.fillStyle = rg; c.fillRect(0, 0, 1920, 1080);
    });
  }

  function paint(ctx, t, dt, W, Hh, TK, S){
    if (!bgLayer) build();
    var p = S.progress, ch = Math.max(S.cheer, S.win * 0.75), ms = S.miss, r, c, i;
    ctx.save(); ctx.scale(W / 1920, Hh / 1080);
    ctx.drawImage(bgLayer, 0, 0);
    /* LED wall: wave of pink/cyan cells, builds up with progress, bursts on cheer, red on miss */
    var base = 0.55 + 0.45 * p, a1 = ms > 0.05 ? "#ff2a4a" : L1, a2 = ms > 0.05 ? "#ff7a3a" : L2;
    for (r = 0; r < 13; r++){
      for (c = 0; c < 32; c++){
        var w = 0.5 + 0.5 * Math.sin(c * 0.5 + r * 0.7 - t * 2.1);
        if (w < 0.35 && ch < 0.05) continue;
        ctx.globalAlpha = (0.1 + 0.3 * w) * base + 0.55 * ch * w;
        ctx.fillStyle = Math.sin(c * 0.26 - r * 0.14 + t * 0.7) > 0 ? a1 : a2;
        ctx.fillRect(22 + c * 60, 142 + r * 58, 22, 22);
      }
    }
    ctx.globalAlpha = 1;
    /* bulbs on the lighting rail */
    var step = Math.floor(t * 4), cnt = Math.max(0, 1 - S.lose * 0.8);
    ctx.fillStyle = BULB; ctx.globalAlpha = cnt;
    for (c = 0; c < 40; c++) if ((step + c) % 3 === 0 || ch > 0.5) ctx.fillRect(20 + c * 48, 116, 9, 9);
    ctx.globalAlpha = 1;
    /* spotlights: sweep, converge on the stage centre when the crowd cheers */
    ctx.globalCompositeOperation = "lighter";
    var xs = [260, 760, 1180, 1680], lit = 1 - S.lose * 0.85;
    for (i = 0; i < 4; i++){
      var sw = Math.sin(t * 0.6 + i * 1.7) * 0.38, toC = (960 - xs[i]) / 1300;
      var ang = sw * (1 - ch) + toC * ch, x0 = xs[i], y0 = 100, len = 1050;
      var bx = x0 + Math.sin(ang) * len, by = y0 + Math.cos(ang) * len, half = 150 + ch * 60;
      ctx.globalAlpha = (0.12 + ch * 0.14) * lit;
      ctx.fillStyle = "#fffad8"; ctx.beginPath(); ctx.moveTo(x0 - 12, y0); ctx.lineTo(x0 + 12, y0);
      ctx.lineTo(bx + Math.cos(ang) * half, by - Math.sin(ang) * half); ctx.lineTo(bx - Math.cos(ang) * half, by + Math.sin(ang) * half); ctx.closePath(); ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
    /* keep the middle calm for the question cards */
    ctx.drawImage(vigLayer, 0, 0);
    /* floor edge neon */
    ctx.globalAlpha = 0.6 + 0.4 * Math.sin(t * 3); ctx.fillStyle = ms > 0.05 ? "#ff2a4a" : L1; ctx.fillRect(0, 898, 1920, 5);
    ctx.globalAlpha = 1;
    /* podium lamps: one more lamp for every share of progress, all flash on cheer */
    var on = Math.round(p * LAMPS);
    for (i = 0; i < LAMPS; i++){
      var pod = Math.floor(i / 6), bi = i % 6, lx = 250 + pod * 280 + 28 + bi * 38, lit1 = i < on;
      var fl = lit1 && ch > 0.3 && ((Math.floor(t * 10) + i) % 2 === 0);
      ctx.fillStyle = lit1 ? (fl ? "#ffffff" : (pod % 2 ? L2 : BULB)) : "#2d2440";
      if (lit1){ ctx.shadowColor = pod % 2 ? L2 : BULB; ctx.shadowBlur = 14; }
      ctx.fillRect(lx, 1036, 26, 14);
      ctx.shadowBlur = 0;
    }
    /* red alarm wash on a miss, lights-down on a loss */
    if (ms > 0.02){ ctx.fillStyle = "rgba(255,30,70," + (ms * 0.2).toFixed(3) + ")"; ctx.fillRect(0, 0, 1920, 1080); }
    if (S.lose > 0){ ctx.fillStyle = "rgba(6,3,16,.45)"; ctx.fillRect(0, 0, 1920, 1080); }
    ctx.restore();
  }

  var K = { o: "#1a0f2e", sk: "#ffd6b0", suit: "#e8344e", suit2: "#a81a35", hair: "#2a1a14", bow: "#ffd23f", ch: "#ff8fa3" };
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
    var o = K.o, sk = K.sk, suit = K.suit, suit2 = K.suit2, hair = K.hair, bow = K.bow, ch = K.ch;
    return '<svg viewBox="0 0 300 440" width="300" height="440">' +
      '<ellipse cx="150" cy="430" rx="92" ry="11" fill="rgba(0,0,0,.35)"/>' +
      '<rect x="112" y="352" width="32" height="66" rx="10" fill="#26243a" stroke="' + o + '" stroke-width="6"/><rect x="156" y="352" width="32" height="66" rx="10" fill="#26243a" stroke="' + o + '" stroke-width="6"/>' +
      '<ellipse cx="122" cy="422" rx="28" ry="11" fill="#141414" stroke="' + o + '" stroke-width="4"/><ellipse cx="178" cy="422" rx="28" ry="11" fill="#141414" stroke="' + o + '" stroke-width="4"/>' +
      arm("M92 270 Q50 300 60 348", suit, o) + '<circle cx="60" cy="352" r="18" fill="' + sk + '" stroke="' + o + '" stroke-width="5"/>' +
      '<path d="M78 254 Q150 226 222 254 L236 362 Q150 384 64 362 Z" fill="' + suit + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M126 242 L150 314 L174 242 Z" fill="#fff" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M126 242 L106 302 L142 292 Z" fill="' + suit2 + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/><path d="M174 242 L194 302 L158 292 Z" fill="' + suit2 + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<circle cx="150" cy="334" r="6" fill="' + bow + '" stroke="' + o + '" stroke-width="3"/><path d="M196 288 l16 -9 l6 13 z" fill="' + bow + '" stroke="' + o + '" stroke-width="3"/>' +
      '<path d="M128 248 L150 258 L172 248 L172 274 L150 264 L128 274 Z" fill="' + bow + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/><circle cx="150" cy="261" r="7" fill="' + bow + '" stroke="' + o + '" stroke-width="3"/>' +
      '<circle cx="58" cy="150" r="20" fill="' + sk + '" stroke="' + o + '" stroke-width="6"/><circle cx="242" cy="150" r="20" fill="' + sk + '" stroke="' + o + '" stroke-width="6"/>' +
      '<circle cx="150" cy="140" r="96" fill="' + sk + '" stroke="' + o + '" stroke-width="7"/>' +
      '<path d="M58 134 Q50 46 150 40 Q252 44 244 130 Q232 92 196 86 Q160 66 120 82 Q84 92 58 134 Z" fill="' + hair + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M86 78 Q124 8 218 52 Q188 50 166 66" fill="' + hair + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/><path d="M110 58 Q140 36 178 44" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="6" stroke-linecap="round"/>' +
      '<ellipse cx="94" cy="178" rx="15" ry="8" fill="' + ch + '" opacity=".55"/><ellipse cx="206" cy="178" rx="15" ry="8" fill="' + ch + '" opacity=".55"/>' +
      faces(o) +
      arm("M210 272 Q256 262 240 226", suit, o) + '<circle cx="238" cy="222" r="18" fill="' + sk + '" stroke="' + o + '" stroke-width="5"/>' +
      '<rect x="230" y="170" width="16" height="56" rx="7" fill="#2b2b35" stroke="' + o + '" stroke-width="4" transform="rotate(-14 238 198)"/>' +
      '<rect x="229" y="182" width="18" height="9" fill="' + bow + '" transform="rotate(-14 238 198)"/>' +
      '<circle cx="230" cy="164" r="19" fill="#b8c0d0" stroke="' + o + '" stroke-width="5"/><path d="M216 158 L244 158 M214 168 L246 168" stroke="#6b7385" stroke-width="3"/>' +
      '</svg>';
  }

  function deco(){
    return '<style>' +
      '#ts-deco .tv-sign{position:absolute;display:flex;align-items:center;justify-content:center;writing-mode:vertical-rl;text-orientation:upright;font-family:var(--font-display);font-size:34px;line-height:1.05;letter-spacing:3px;padding:18px 8px;border-radius:14px;transition:all .2s}' +
      '#ts-deco .tv-applause{left:36px;top:150px;color:rgba(255,255,255,.35);background:#2a0d18;border:5px dotted #6b3a20}' +
      '#ts-deco .tv-applause.on{color:#fff;background:#ff2d55;border-color:#ffd23f;text-shadow:0 0 16px #fff;box-shadow:0 0 40px #ff2d55,0 0 90px #ff2d55;animation:tvBlink .35s steps(2) infinite}' +
      '#ts-deco .tv-onair{right:34px;top:150px;color:#fff;background:#e8243c;border:4px solid #fff;box-shadow:0 0 24px #e8243c,0 5px 0 rgba(0,0,0,.4);animation:tvOnAir 1.6s ease-in-out infinite}' +
      '@keyframes tvBlink{0%{filter:brightness(1.25)}100%{filter:brightness(.85)}}' +
      '@keyframes tvOnAir{0%,100%{opacity:1}50%{opacity:.72}}' +
      '#ts-deco[data-scene=title] .tv-applause,#ts-deco[data-scene=result] .tv-applause{left:200px;top:300px;transform:scale(1.25);transform-origin:0 0}' +
      '#ts-deco[data-scene=title] .tv-onair,#ts-deco[data-scene=result] .tv-onair{right:200px;top:300px;transform:scale(1.25);transform-origin:100% 0}' +
      'body.reduce #ts-deco .tv-sign{animation:none!important}' +
      '</style><div class="tv-sign tv-applause">APPLAUSE</div><div class="tv-sign tv-onair">ON AIR</div>';
  }

  function sfx(){
    NG.defineSfx("tvClap", function(){
      for (var i = 0; i < 30; i++) NG.tone({ type: "noise", freq: 1200 + Math.random() * 2200, q: 1.4, dur: 0.05 + Math.random() * 0.05, vol: 0.12 + Math.random() * 0.1, delay: Math.random() * 1.4, attack: 0.002 });
      NG.tone({ type: "triangle", freq: 784, dur: 0.18, vol: 0.16, jitter: 0 }); NG.tone({ type: "triangle", freq: 1046, dur: 0.3, vol: 0.16, jitter: 0, delay: 0.14 });
    });
  }

  function onReact(kind){
    var el = document.querySelector("#ts-deco .tv-applause");
    if (tvTimer){ NG.cancel(tvTimer); tvTimer = null; }
    if (kind === "correct" || kind === "win"){
      NG.sfx("tvClap");
      if (el){ el.classList.add("on"); if (kind !== "win") tvTimer = NG.after(2600, function(){ el.classList.remove("on"); }); }
    } else if (el && kind !== "lose"){ el.classList.remove("on"); }
    if (kind === "win"){ NG.after(300, function(){ NG.fx.confetti(); }); }
  }

  return {
    paint: paint, deco: deco, sfx: sfx, onReact: onReact, hostCol: true, podiums: true,
    host: { svg: hostSvg, name: "미스터 Q", lines: {
      title: ["생방송 3초 전!", "준비됐나요?"], start: ["첫 문제 나갑니다!"],
      correct: ["정답! 박수!", "대단해요!", "완벽해요!"], wrong: ["아쉬워요! 다음엔!", "괜찮아요, 힘내요"],
      win: ["여러분 모두 최고!"], lose: ["아쉽지만 멋졌어요"] } }
  };
})();
