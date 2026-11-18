/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* 미사일: escape-room (반 전체 협동 방탈출, 자물쇠 3~6개, 위기 게이지)
   - 글자는 전부 GAME.items + GAME.world 에서 온다. 그림은 GAME.world.skin 으로 고른다.
   - 스킨: joseon(조선 수군 작전실) · lab(폭주하는 실험실) · temple(고대 신전)
   - 문제 종류(kind): order(순서 누르기) · dial(숫자 다이얼, 부호 가능) · match(끌어서 짝짓기) · fake(가짜 찾기)
   - 시그니처: 자물쇠가 열릴 때마다 보상 그림(거북선/해독제/신전 문양)이 완성되고, 다 열면 대장면 */
window.GAME_LOGIC = (function(){
  var U = NG.util, G = window.GAME || {}, W0 = G.world || {};
  var KINDS = {order: 1, dial: 1, match: 1, fake: 1};
  var items = (G.items || []).filter(function(it){
    if (!it || !KINDS[it.kind]) return false;
    if (it.kind === "order") return it.cards && it.cards.length >= 2;
    if (it.kind === "match") return it.pairs && it.pairs.length >= 2;
    if (it.kind === "fake") return it.lines && it.lines.length >= 1 && it.fake;
    return it.answer !== undefined && String(it.answer).length > 0;
  }).slice(0, 6);
  var N = items.length;
  var SECONDS = +W0.seconds > 0 ? +W0.seconds : 480;
  var DRAIN = 100 / SECONDS, PENALTY = 10, HINT = 8, RELIEF = 12;
  var ORD = ["첫째", "둘째", "셋째", "넷째", "다섯째", "여섯째"];
  var CALM = !!G.calm;

  /* generic (non-subject) fallbacks; every skin JSON overrides these */
  var DEF = {
    threatLabel: "남은 시간", threatDanger: "⚠ 서둘러요!", hintBtn: "💡 힌트 (−{h})", hintFloat: "−{h}",
    wrongMsg: "✖ 아쉬워요!", costFmt: "−{p}", lockName: "자물쇠", openHead: "{ord} 자물쇠가 열렸다!", openBadge: "🔓 열렸다!",
    startBtn: "▶ 시작!", nextBtn: "다음으로 ▶", finaleBtn: "🏁 탈출!", finaleBanner: "탈출 성공!", finaleWin: "🏆 대성공!",
    resultTitle: "🏆 탈출 성공!", resultPerfect: "🏆 완벽한 탈출!", resultLine: "🔓 자물쇠 {n}개 모두 열기 성공!",
    loseTitle: "⏰ 시간이 다 됐어요!", loseMsg: "괜찮아요! 다시 의논해서 도전해요.", retryHere: "🔁 이 문제부터 다시", retryAll: "↩ 처음부터",
    againBtn: "🔁 다시 하기", clueTitle: "📜 단서", dialBtn: "🔑 열어 보기", dialWrong: "✖ 숫자가 맞지 않아요!",
    matchWrong: "✖ 짝이 아니에요!", fakeWrong: "✖ 이건 진짜 정보!", orderNote: "누른 차례대로 번호가 찍혀요. 모둠이 의논해서 한 명이 눌러요. 틀리면 처음부터!",
    matchNote: "", mistakesLine: "틀린 횟수 {m}번 · 힌트 {k}번", teamTurn: "{team} 차례",
    rules: ["🤝 모두 함께 의논해서, 한 명이 눌러요", "⏳ 틀리거나 힌트를 쓰면 시간이 줄어요", "🔓 자물쇠 {n}개를 모두 열면 탈출!"]
  };
  function T(key, vars){
    var s = W0[key] !== undefined && W0[key] !== null ? W0[key] : DEF[key];
    s = String(s === undefined || s === null ? "" : s);
    var v = {n: N, p: PENALTY, h: HINT, m: mistakes, k: hints};
    if (vars) for (var a in vars) v[a] = vars[a];
    for (var b in v) s = s.split("{" + b + "}").join(v[b]);
    return s;
  }
  function fill(s){ return String(s).split("{n}").join(N); }

  var threat = 20, built = 0, cur = 0, ticking = false, locked = false, lost = false, finale = false;
  var cleared = false, ftStart = -1, mistakes = 0, hints = 0, ft = 0, warnT = 0, lastTempo = 1, hooked = false;
  var revealFn = null, advanceFn = null, area = null, lockEls = [];

  function shake(a){ if (!CALM) NG.fx.shake(a); }
  function flash(c, a){ if (!CALM) NG.fx.flash(c, a); }
  function ease(p){ p = U.clamp(p, 0, 1); return p * p * (3 - 2 * p); }
  var TAU = 6.2832;

  /* ================================================================ ART: JOSEON */
  var stars = []; for (var si = 0; si < 80; si++) stars.push({x: Math.random() * 1920, y: Math.random() * 130, s: Math.random() * 2 + 1, p: Math.random() * 6});

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

  /* turtle ship in 6 parts: hull, shell, spikes, dragon head, oars, flag */
  function turtle(c, x, y, s, parts, t){
    c.save(); c.translate(x, y); c.scale(s, s); c.lineJoin = "round";
    function st(on){ if (on){ c.setLineDash([]); c.lineWidth = 6; c.strokeStyle = "#140d08"; } else { c.setLineDash([10, 8]); c.lineWidth = 4; c.strokeStyle = "rgba(255,235,180,.6)"; } }
    var on = []; for (var q = 0; q < 6; q++) on.push(parts > q);
    var j;
    for (j = 0; j < 6; j++){ var ox = -95 + j * 38; c.setLineDash(on[4] ? [] : [10, 8]); c.beginPath(); c.moveTo(ox, -10); c.lineTo(ox - 26 + Math.sin(t * 3 + j) * (on[4] ? 5 : 0), 30); c.lineWidth = on[4] ? 8 : 4; c.strokeStyle = on[4] ? "#5a3a1e" : "rgba(255,235,180,.6)"; c.stroke(); }
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
      c.fillStyle = "rgba(255,190,80,.8)"; c.beginPath(); c.arc(-204, -50, 6 + Math.sin(t * 6) * 2, 0, TAU); c.fill(); }
    st(on[5]); c.beginPath(); c.moveTo(0, -92); c.lineTo(0, -190); c.stroke();
    if (on[5]){ c.fillStyle = "#c8402f"; c.beginPath(); c.moveTo(0, -190); c.lineTo(-76 + Math.sin(t * 4) * 6, -174); c.lineTo(0, -158); c.closePath(); c.fill(); }
    c.setLineDash([]); c.restore();
  }

  function wave(c, y0, W, t, k, col){
    c.fillStyle = col; c.beginPath(); c.moveTo(0, y0 + 200);
    for (var x = 0; x <= W; x += 40) c.lineTo(x, y0 + Math.sin(x / 110 + t * (1 + k * 0.3) + k) * 8);
    c.lineTo(W, y0 + 200); c.fill();
  }
  function parts6(){ return built >= N ? 6 : Math.ceil(built / Math.max(1, N) * 6); }

  function joseonBand(c, t, dt, W, H){
    var g = c.createLinearGradient(0, 0, 0, 150); g.addColorStop(0, "#070d22"); g.addColorStop(1, "#24396b"); c.fillStyle = g; c.fillRect(0, 0, W, 150);
    for (var i = 0; i < stars.length; i++){ var s = stars[i]; c.globalAlpha = 0.4 + 0.6 * Math.abs(Math.sin(t * 1.4 + s.p)); c.fillStyle = "#fff"; c.fillRect(s.x, s.y, s.s, s.s); } c.globalAlpha = 1;
    var g2 = c.createLinearGradient(0, 150, 0, 282); g2.addColorStop(0, "#14386a"); g2.addColorStop(1, "#071b36"); c.fillStyle = g2; c.fillRect(0, 150, W, 132);
    wave(c, 168, W, t, 0, "rgba(120,180,255,.10)"); wave(c, 214, W, t, 1, "rgba(120,180,255,.12)");
    c.fillStyle = "#0b1627"; c.beginPath(); c.moveTo(1400, 282); c.lineTo(1500, 170); c.lineTo(1620, 150); c.lineTo(1760, 130); c.lineTo(1920, 150); c.lineTo(1920, 282); c.fill();
    c.fillStyle = "#3a2616"; c.fillRect(1340, 262, 580, 20);
    for (i = 0; i < 2; i++){ var tx = i ? 1860 : 1380, ty = i ? 236 : 246; c.fillStyle = "#5a3a1e"; c.fillRect(tx - 3, ty, 6, 26); c.fillStyle = "rgba(255,170,60," + (0.8 + 0.2 * Math.sin(t * 9 + i)) + ")"; c.beginPath(); c.arc(tx, ty - 6, 11 + Math.sin(t * 11 + i) * 2, 0, TAU); c.fill(); }
    var fx = 60 + (threat / 100) * 1230;
    if (!cleared) for (i = 4; i >= 0; i--) enemy(c, fx - i * 98 - (i % 2) * 18, 208 + (i % 3) * 16 + Math.sin(t * 1.6 + i) * 3, 0.9, 1);
    turtle(c, 1640, 266, 0.78, parts6(), t);
    var g3 = c.createLinearGradient(0, 282, 0, 1080); g3.addColorStop(0, "#2a1c12"); g3.addColorStop(1, "#130c07"); c.fillStyle = g3; c.fillRect(0, 282, W, H - 282);
    c.fillStyle = "rgba(0,0,0,.28)"; for (i = 0; i < 17; i++) c.fillRect(i * 120, 282, 4, H - 282);
    c.fillStyle = "#c9a24a"; c.fillRect(0, 280, W, 8); c.fillStyle = "#6b4423"; c.fillRect(0, 288, W, 6);
  }

  var JOSEON_HITS = [{x: 90, y: 820}, {x: 195, y: 820}, {x: 300, y: 820}, {x: 405, y: 820}, {x: 510, y: 820}];
  function joseonFinale(c, t, dt, W, H){
    var g = c.createLinearGradient(0, 0, 0, 580); g.addColorStop(0, "#1d2f5a"); g.addColorStop(1, "#f09a5e"); c.fillStyle = g; c.fillRect(0, 0, W, 580);
    c.fillStyle = "#ffe29a"; c.beginPath(); c.arc(1500, 500, 100, 0, TAU); c.fill();
    var g2 = c.createLinearGradient(0, 580, 0, 1080); g2.addColorStop(0, "#1f5a86"); g2.addColorStop(1, "#091f3a"); c.fillStyle = g2; c.fillRect(0, 580, W, 500);
    wave(c, 640, W, t, 0, "rgba(255,255,255,.08)"); wave(c, 760, W, t, 1, "rgba(255,255,255,.08)"); wave(c, 900, W, t, 2, "rgba(0,0,0,.12)");
    for (var k = 0; k < 5; k++){ var sk = U.clamp((ft - (5.6 + k * hitGap())) / 1.2, 0, 1); if (sk < 1) enemy(c, JOSEON_HITS[k].x, 800 + (k % 2) * 30 + sk * 110 + Math.sin(t * 1.5 + k) * 4, 1.6, 1 - sk); }
    var p = ease((ft - 1.5) / 3.5);
    turtle(c, 1560 - 560 * p, 905, 2.0, 6, t);
  }

  function svgOfficer(mood, w){
    var eyes = mood === "worried" ? '<circle cx="80" cy="92" r="7" fill="#1b1b2f"/><circle cx="120" cy="92" r="7" fill="#1b1b2f"/><path d="M68 74 l22 6 M132 74 l-22 6" stroke="#1b1b2f" stroke-width="5" stroke-linecap="round"/>' :
      '<path d="M70 94 q10 -14 20 0 M110 94 q10 -14 20 0" stroke="#1b1b2f" stroke-width="6" fill="none" stroke-linecap="round"/>';
    var mouth = mood === "worried" ? '<path d="M86 124 q14 -10 28 0" stroke="#1b1b2f" stroke-width="5" fill="none" stroke-linecap="round"/>' : '<path d="M82 118 q18 22 36 0z" fill="#8a2a1f" stroke="#1b1b2f" stroke-width="5" stroke-linejoin="round"/>';
    return '<svg viewBox="0 -40 200 290" width="' + w + '" height="' + Math.round(w * 1.45) + '"><ellipse cx="100" cy="240" rx="72" ry="9" fill="rgba(0,0,0,.3)"/>' +
      '<path d="M38 238 q0 -92 62 -98 q62 6 62 98z" fill="#27406b" stroke="#111d36" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M76 142 l24 34 24 -34z" fill="#c8402f" stroke="#111d36" stroke-width="5" stroke-linejoin="round"/>' +
      '<rect x="60" y="196" width="80" height="18" rx="4" fill="#c9a24a" stroke="#111d36" stroke-width="5"/>' +
      '<circle cx="100" cy="98" r="52" fill="#f3c9a0" stroke="#111d36" stroke-width="7"/>' + eyes + mouth +
      '<path d="M84 112 q16 -8 32 0" stroke="#3a2a22" stroke-width="5" fill="none" stroke-linecap="round"/>' +
      '<ellipse cx="100" cy="62" rx="82" ry="17" fill="#2b2b36" stroke="#111d36" stroke-width="6"/>' +
      '<path d="M50 62 q0 -54 50 -54 q50 0 50 54z" fill="#3a3a4a" stroke="#111d36" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M100 8 q-12 -30 14 -40 q-6 20 10 26" fill="#c8402f" stroke="#7a1d12" stroke-width="4" stroke-linejoin="round"/></svg>';
  }
  function lockJoseon(open){
    var shackle = open ? '<path d="M70 46 V30 A20 20 0 0 0 30 30 V36" fill="none" stroke="#e8c25e" stroke-width="10" stroke-linecap="round" transform="rotate(-28 70 46) translate(0 -8)"/>' :
      '<path d="M30 46 V32 A20 20 0 0 1 70 32 V46" fill="none" stroke="#9a7a3a" stroke-width="10"/>';
    return '<svg viewBox="0 0 100 100" width="100%" height="100%">' + (open ? '<circle cx="50" cy="60" r="44" fill="rgba(255,220,120,.25)"/>' : '') + shackle +
      '<rect x="18" y="44" width="64" height="48" rx="10" fill="' + (open ? "#ffd84d" : "#c9a24a") + '" stroke="#3b2616" stroke-width="6"/>' +
      '<circle cx="50" cy="63" r="7" fill="#3b2616"/><rect x="47" y="65" width="6" height="15" rx="2" fill="#3b2616"/></svg>';
  }

  /* ================================================================ ART: LAB */
  function flask(c, x, y, s, p, t, ticks, lit){
    c.save(); c.translate(x, y); c.scale(s, s); c.lineJoin = "round";
    function body(){ c.beginPath(); c.moveTo(-22, -222); c.lineTo(-22, -150); c.lineTo(-96, -14); c.quadraticCurveTo(-102, 0, -84, 0); c.lineTo(84, 0); c.quadraticCurveTo(102, 0, 96, -14); c.lineTo(22, -150); c.lineTo(22, -222); c.closePath(); }
    if (p >= 1){ var rg = c.createRadialGradient(0, -80, 10, 0, -80, 210); rg.addColorStop(0, "rgba(120,255,180," + (0.45 + 0.15 * Math.sin(t * 4)) + ")"); rg.addColorStop(1, "rgba(120,255,180,0)"); c.fillStyle = rg; c.fillRect(-220, -300, 440, 340); }
    body(); c.fillStyle = "rgba(200,240,255,.14)"; c.fill();
    var level = U.clamp(p, 0, 1) * 196;
    if (level > 0){
      c.save(); body(); c.clip();
      var lg = c.createLinearGradient(0, -level, 0, 0); lg.addColorStop(0, "#9dffc8"); lg.addColorStop(1, "#14b873"); c.fillStyle = lg;
      c.beginPath(); c.moveTo(-110, 0);
      for (var xx = -110; xx <= 110; xx += 10) c.lineTo(xx, -level + Math.sin(xx / 14 + t * 5) * 3);
      c.lineTo(110, 0); c.closePath(); c.fill();
      c.fillStyle = "rgba(255,255,255,.7)";
      for (var b = 0; b < 7; b++){ var by = -((t * 60 + b * 37) % Math.max(12, level)); var bx = Math.sin(b * 2.1 + t) * 44 * (1 + by / 260); c.beginPath(); c.arc(bx, by, 3 + (b % 3), 0, TAU); c.fill(); }
      c.restore();
    }
    body(); c.strokeStyle = "#e9fbff"; c.lineWidth = 6; c.stroke();
    c.strokeStyle = "rgba(255,255,255,.5)"; c.lineWidth = 5; c.beginPath(); c.moveTo(-12, -210); c.lineTo(-12, -150); c.lineTo(-70, -40); c.stroke();
    for (var k = 1; k <= ticks; k++){ var hy = -k / ticks * 196; var hx = hy > -150 ? 96 - 74 * (-hy / 150) : 22;
      c.strokeStyle = k <= lit ? "#ffd84d" : "rgba(233,251,255,.75)"; c.lineWidth = 5; c.beginPath(); c.moveTo(hx - 4, hy); c.lineTo(hx - 26, hy); c.stroke(); }
    if (p >= 1){ c.fillStyle = "#a0673a"; c.strokeStyle = "#3b2414"; c.lineWidth = 5; c.fillRect(-26, -246, 52, 30); c.strokeRect(-26, -246, 52, 30); }
    c.restore();
  }

  function cloud(c, x, y, r, a, t, k){
    c.globalAlpha = a;
    var pts = [[-1, 0.15, 0.62], [-0.45, -0.25, 0.8], [0.25, -0.32, 0.86], [0.85, 0.05, 0.66], [0.05, 0.3, 0.8]];
    for (var i = 0; i < pts.length; i++){ var q = pts[i]; var px = x + q[0] * r + Math.sin(t * 0.9 + k + i) * r * 0.05, py = y + q[1] * r + Math.cos(t * 0.8 + k * 2 + i) * r * 0.05;
      c.fillStyle = "#6f7f86"; c.beginPath(); c.arc(px, py + r * 0.08, q[2] * r, 0, TAU); c.fill(); }
    for (i = 0; i < pts.length; i++){ q = pts[i]; px = x + q[0] * r + Math.sin(t * 0.9 + k + i) * r * 0.05; py = y + q[1] * r + Math.cos(t * 0.8 + k * 2 + i) * r * 0.05;
      c.fillStyle = "#a9b8bd"; c.beginPath(); c.arc(px - q[2] * r * 0.12, py - q[2] * r * 0.12, q[2] * r * 0.82, 0, TAU); c.fill(); }
    c.globalAlpha = 1;
  }

  function siren(c, x, y, s, t, green){
    c.save(); c.translate(x, y); c.scale(s, s);
    c.fillStyle = "#2b3a40"; c.fillRect(-26, 0, 52, 14);
    var on = green ? 1 : 0.55 + 0.45 * Math.abs(Math.sin(t * (3 + threat / 15)));
    c.fillStyle = green ? "rgba(90,255,140," + on + ")" : "rgba(255,60,40," + on + ")";
    c.beginPath(); c.arc(0, 0, 22, Math.PI, 0); c.fill();
    c.strokeStyle = "#11191c"; c.lineWidth = 4; c.stroke();
    c.fillStyle = "rgba(255,255,255,.6)"; c.beginPath(); c.arc(-8, -10, 5, 0, TAU); c.fill();
    c.restore();
  }

  function labRoom(c, W, H, top){
    var g3 = c.createLinearGradient(0, top, 0, H); g3.addColorStop(0, "#123540"); g3.addColorStop(1, "#08171d"); c.fillStyle = g3; c.fillRect(0, top, W, H - top);
    c.fillStyle = "rgba(140,220,230,.06)";
    for (var y = top + 6; y < H; y += 96) for (var x = ((y - top) / 96 % 2) * 48; x < W; x += 96) if (((x + y) / 48) % 5 < 1) c.fillRect(x + 4, y + 4, 88, 88);
    c.fillStyle = "rgba(0,0,0,.35)"; for (x = 0; x < W; x += 96) c.fillRect(x, top, 3, H - top); for (y = top; y < H; y += 96) c.fillRect(0, y, W, 3);
  }

  function labBand(c, t, dt, W, H){
    var g = c.createLinearGradient(0, 0, 0, 282); g.addColorStop(0, "#071820"); g.addColorStop(1, "#15404b"); c.fillStyle = g; c.fillRect(0, 0, W, 282);
    c.strokeStyle = "rgba(140,220,230,.08)"; c.lineWidth = 2;
    for (var x = 0; x <= W; x += 64){ c.beginPath(); c.moveTo(x, 0); c.lineTo(x, 282); c.stroke(); }
    for (var y = 0; y <= 282; y += 64){ c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
    // pipes
    c.fillStyle = "#2c4f5c"; c.fillRect(0, 126, W, 20); c.fillStyle = "rgba(255,255,255,.18)"; c.fillRect(0, 129, W, 4);
    for (var i = 0; i < 5; i++){ var vx = 220 + i * 300; c.fillStyle = "#3d6c7c"; c.fillRect(vx - 14, 120, 28, 32); c.strokeStyle = "#0b1d24"; c.lineWidth = 3; c.strokeRect(vx - 14, 120, 28, 32);
      c.save(); c.translate(vx, 112); c.rotate(t * 0.5 + i); c.strokeStyle = "#e05a3a"; c.lineWidth = 5; c.beginPath(); c.arc(0, 0, 13, 0, TAU); c.moveTo(-13, 0); c.lineTo(13, 0); c.moveTo(0, -13); c.lineTo(0, 13); c.stroke(); c.restore(); }
    // shelf with bottles
    c.fillStyle = "#3c5a66"; c.fillRect(760, 204, 470, 10);
    var cols = ["#ff6b9a", "#6bd1ff", "#ffd84d", "#b48cff", "#7dffb2", "#ff9a3d"];
    for (i = 0; i < 6; i++){ var bx = 790 + i * 74, bh = 34 + (i % 3) * 12;
      c.fillStyle = "rgba(220,245,255,.25)"; c.fillRect(bx, 204 - bh, 36, bh); c.fillStyle = cols[i]; c.fillRect(bx + 3, 204 - bh * 0.55, 30, bh * 0.55 - 2);
      c.fillStyle = "#cfe6ee"; c.fillRect(bx + 8, 196 - bh, 20, 10); }
    // sirens
    siren(c, 1010, 70, 1.4, t, cleared); siren(c, 1290, 70, 1.4, t, cleared);
    // smoke = threat front
    var fx = -160 + (threat / 100) * 1420;
    if (!cleared){ c.fillStyle = "rgba(120,135,140,.22)"; c.fillRect(0, 0, Math.max(0, fx), 282); }
    for (i = 16; i >= 0 && !cleared; i--){ var cx = fx - i * 82 + Math.sin(t * 0.8 + i) * 10; if (cx < -140) continue;
      cloud(c, cx, 178 + (i % 3) * 30 + Math.sin(t * 1.1 + i * 1.7) * 6, 44 + (i % 4) * 8, 0.92, t, i); }
    if (threat > 50 && !cleared){ c.save(); c.globalAlpha = 0.18 * Math.min(1, (threat - 50) / 25); c.fillStyle = "#ff3a2a"; c.translate(1010, 70); c.rotate(t * 3); c.beginPath(); c.moveTo(0, 0); c.arc(0, 0, 420, -0.18, 0.18); c.closePath(); c.fill(); c.restore(); }
    // bench + reward flask
    c.fillStyle = "#8fa6ae"; c.fillRect(1300, 262, 620, 20); c.fillStyle = "#5b737c"; c.fillRect(1300, 276, 620, 6);
    c.fillStyle = "#3b4a50"; c.fillRect(1380, 246, 160, 16);
    flask(c, 1460, 250, 0.84, built / Math.max(1, N), t, N, built);
    labRoom(c, W, H, 282);
    c.fillStyle = "#9fb4bc"; c.fillRect(0, 280, W, 8);
    for (x = 0; x < W; x += 40){ c.fillStyle = (x / 40) % 2 ? "#1a1a1a" : "#ffcf1a"; c.beginPath(); c.moveTo(x, 288); c.lineTo(x + 40, 288); c.lineTo(x + 30, 296); c.lineTo(x - 10, 296); c.closePath(); c.fill(); }
  }

  var LAB_HITS = [{x: 230, y: 470}, {x: 1690, y: 470}, {x: 590, y: 370}, {x: 1330, y: 370}, {x: 420, y: 650}, {x: 1500, y: 650}];
  function labFinale(c, t, dt, W, H){
    var g = c.createLinearGradient(0, 0, 0, 780); g.addColorStop(0, "#0b222b"); g.addColorStop(1, "#1a4a57"); c.fillStyle = g; c.fillRect(0, 0, W, 780);
    c.strokeStyle = "rgba(140,220,230,.09)"; c.lineWidth = 2;
    for (var x = 0; x <= W; x += 96){ c.beginPath(); c.moveTo(x, 0); c.lineTo(x, 780); c.stroke(); }
    for (var y = 0; y <= 780; y += 96){ c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
    var clear = ft > 8.8;
    siren(c, 160, 150, 2.2, t, clear); siren(c, 1760, 150, 2.2, t, clear);
    c.fillStyle = "#a9bcc4"; c.fillRect(0, 780, W, 34); c.fillStyle = "#6c848d"; c.fillRect(0, 806, W, 8);
    c.fillStyle = "#24404b"; c.fillRect(0, 814, W, H - 814);
    c.fillStyle = "rgba(0,0,0,.25)"; for (x = 0; x < W; x += 320) c.fillRect(x, 814, 6, H - 814);
    var gone = 0;
    for (var k = 0; k < LAB_HITS.length; k++){ var sk = U.clamp((ft - (5.6 + k * hitGap())) / 0.9, 0, 1); if (sk >= 1){ gone++; continue; }
      cloud(c, LAB_HITS[k].x, LAB_HITS[k].y, 110 * (1 - sk * 0.5), 1 - sk, t, k); }
    c.fillStyle = "rgba(130,145,150," + (0.32 * (1 - gone / LAB_HITS.length)) + ")"; c.fillRect(0, 0, W, H);
    var p = ease((ft - 1.2) / 3.5);
    var fxp = 960, sc = 1.1 + 0.9 * p;
    flask(c, fxp, 800, sc, U.clamp(ft / 1.2, 0.35, 1), t, 0, 0);
    if (ft > 5){ c.save(); c.globalAlpha = U.clamp((7.8 - ft) / 1.2, 0, 1) * 0.7; c.strokeStyle = "#8dffc0"; c.lineWidth = 10; c.setLineDash([4, 26]); c.lineDashOffset = -t * 300;
      for (var r = 0; r < LAB_HITS.length; r++){ c.beginPath(); c.moveTo(fxp, 800 - 246 * sc); c.quadraticCurveTo((fxp + LAB_HITS[r].x) / 2, 120, LAB_HITS[r].x, LAB_HITS[r].y); c.stroke(); } c.restore(); }
  }

  function svgResearcher(mood, w){
    var worried = mood === "worried";
    var eyes = worried ? '<circle cx="82" cy="102" r="7" fill="#1d2b33"/><circle cx="118" cy="102" r="7" fill="#1d2b33"/><path d="M70 86 l20 6 M130 86 l-20 6" stroke="#1d2b33" stroke-width="5" stroke-linecap="round"/>' :
      '<path d="M72 104 q10 -14 20 0 M108 104 q10 -14 20 0" stroke="#1d2b33" stroke-width="6" fill="none" stroke-linecap="round"/>';
    var mouth = worried ? '<path d="M88 130 q12 -9 24 0" stroke="#1d2b33" stroke-width="5" fill="none" stroke-linecap="round"/>' : '<path d="M84 124 q16 20 32 0z" fill="#c2414b" stroke="#1d2b33" stroke-width="5" stroke-linejoin="round"/>';
    var sweat = worried ? '<path d="M152 84 q10 14 0 22 q-10 -8 0 -22z" fill="#8fd7ff" stroke="#1d2b33" stroke-width="3"/>' : '<circle cx="66" cy="120" r="8" fill="#ff9aa2" opacity=".7"/><circle cx="134" cy="120" r="8" fill="#ff9aa2" opacity=".7"/>';
    return '<svg viewBox="0 -40 200 290" width="' + w + '" height="' + Math.round(w * 1.45) + '"><ellipse cx="100" cy="240" rx="74" ry="9" fill="rgba(0,0,0,.3)"/>' +
      '<path d="M32 240 q2 -92 68 -100 q66 8 68 100z" fill="#f4f8fa" stroke="#1d2b33" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M82 144 l18 38 18 -38z" fill="#2bb59a" stroke="#1d2b33" stroke-width="5" stroke-linejoin="round"/>' +
      '<path d="M82 144 l-8 54 26 -16z M118 144 l8 54 -26 -16z" fill="#dbe6ec" stroke="#1d2b33" stroke-width="5" stroke-linejoin="round"/>' +
      '<line x1="100" y1="184" x2="100" y2="238" stroke="#1d2b33" stroke-width="4"/>' +
      '<rect x="120" y="200" width="28" height="24" rx="3" fill="#dbe6ec" stroke="#1d2b33" stroke-width="4"/><path d="M128 202 v-14 M138 202 v-16" stroke="#e5484d" stroke-width="5" stroke-linecap="round"/>' +
      '<path d="M30 150 h12 v18 l16 30 q3 7 -5 7 h-34 q-8 0 -5 -7 l16 -30z" fill="#d8fbe8" stroke="#1d2b33" stroke-width="5" stroke-linejoin="round"/>' +
      '<path d="M20 186 h32 l6 12 q3 7 -5 7 h-34 q-8 0 -5 -7z" fill="#36d38a"/><circle cx="36" cy="194" r="3" fill="#fff"/>' +
      '<circle cx="36" cy="170" r="11" fill="#f6d2ae" stroke="#1d2b33" stroke-width="5"/>' +
      '<circle cx="100" cy="30" r="20" fill="#4a2c1d" stroke="#1d2b33" stroke-width="6"/>' +
      '<circle cx="100" cy="104" r="52" fill="#f6d2ae" stroke="#1d2b33" stroke-width="7"/>' +
      '<path d="M48 104 q-6 -60 52 -62 q58 2 52 62 q-8 -30 -30 -34 q-30 16 -56 4 q-14 10 -18 30z" fill="#4a2c1d" stroke="#1d2b33" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M50 74 q50 -18 100 0" stroke="#2bb59a" stroke-width="9" fill="none"/>' +
      '<circle cx="80" cy="68" r="15" fill="#bff0ff" stroke="#1d2b33" stroke-width="6"/><circle cx="120" cy="68" r="15" fill="#bff0ff" stroke="#1d2b33" stroke-width="6"/>' +
      '<circle cx="75" cy="63" r="4" fill="#fff"/><circle cx="115" cy="63" r="4" fill="#fff"/>' + eyes + mouth + sweat + '</svg>';
  }
  function lockLab(open){
    var led = open ? "#3ad16b" : "#ff4a3a";
    var keys = ""; for (var r = 0; r < 2; r++) for (var q = 0; q < 3; q++) keys += '<rect x="' + (26 + q * 18) + '" y="' + (54 + r * 16) + '" width="12" height="10" rx="2" fill="#7fa9b6"/>';
    return '<svg viewBox="0 0 100 100" width="100%" height="100%">' + (open ? '<circle cx="50" cy="50" r="48" fill="rgba(90,255,140,.18)"/>' : '') +
      '<rect x="16" y="8" width="68" height="86" rx="12" fill="#1b3640" stroke="' + (open ? "#7dffb2" : "#7fd8f0") + '" stroke-width="5"/>' +
      '<rect x="24" y="18" width="52" height="28" rx="4" fill="#0b2b1f"/>' +
      (open ? '<path d="M38 32 l8 8 l16 -16" fill="none" stroke="#7dffb2" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>' : '<path d="M40 24 l20 16 M60 24 l-20 16" stroke="#ff6a5a" stroke-width="6" stroke-linecap="round"/>') +
      keys + '<circle cx="50" cy="86" r="5" fill="' + led + '"/></svg>';
  }

  /* ================================================================ ART: TEMPLE */
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
    c.beginPath(); c.arc(0, 0, r * 0.42, 0, TAU);
    c.fillStyle = full ? "#ffe680" : "#3a2a1a"; c.fill(); c.strokeStyle = full ? "#7a4a10" : "rgba(255,215,150,.55)"; c.lineWidth = r * 0.04; c.stroke();
    c.strokeStyle = full ? "#7a4a10" : "rgba(255,215,150,.45)"; c.lineWidth = r * 0.05;
    c.beginPath(); c.moveTo(-r * 0.2, -r * 0.02); c.quadraticCurveTo(0, -r * 0.22, r * 0.2, -r * 0.02); c.quadraticCurveTo(0, r * 0.18, -r * 0.2, -r * 0.02); c.stroke();
    c.fillStyle = full ? "#7a4a10" : "rgba(255,215,150,.45)"; c.beginPath(); c.arc(0, -r * 0.02, r * 0.07, 0, TAU); c.fill();
    if (full){ c.strokeStyle = "rgba(255,240,170,.9)"; c.lineWidth = r * 0.04; for (var k = 0; k < 12; k++){ var aa = k * TAU / 12 + t * 0.4; c.beginPath(); c.moveTo(Math.cos(aa) * r * 1.04, Math.sin(aa) * r * 1.04); c.lineTo(Math.cos(aa) * r * (1.18 + 0.05 * Math.sin(t * 5 + k)), Math.sin(aa) * r * (1.18 + 0.05 * Math.sin(t * 5 + k))); c.stroke(); } }
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
  function glyphs(c, x0, y0, W, H, step){
    c.strokeStyle = "rgba(255,210,140,.10)"; c.lineWidth = 5;
    for (var y = y0 + step / 2; y < y0 + H; y += step) for (var x = x0 + step / 2 + ((y / step) % 2) * step / 2; x < x0 + W; x += step * 1.6){
      var k = Math.floor(x / 97 + y / 61) % 3; c.beginPath();
      if (k === 0){ c.moveTo(x - 20, y + 16); c.lineTo(x, y - 18); c.lineTo(x + 20, y + 16); c.closePath(); }
      else if (k === 1){ c.ellipse(x, y, 22, 12, 0, 0, TAU); c.moveTo(x + 5, y); c.arc(x, y, 5, 0, TAU); }
      else { c.moveTo(x - 24, y); for (var j = 0; j < 4; j++) c.quadraticCurveTo(x - 18 + j * 12, y - 12 * (j % 2 ? -1 : 1), x - 12 + j * 12, y); }
      c.stroke(); }
  }
  function torch(c, x, y, s, t, k){
    c.fillStyle = "#4a2f18"; c.fillRect(x - 6 * s, y, 12 * s, 40 * s);
    c.fillStyle = "#2a1c10"; c.fillRect(x - 12 * s, y - 4 * s, 24 * s, 10 * s);
    var f = 1 + 0.12 * Math.sin(t * 13 + k);
    c.fillStyle = "rgba(255,150,40,.25)"; c.beginPath(); c.arc(x, y - 18 * s, 40 * s * f, 0, TAU); c.fill();
    c.fillStyle = "#ff8a2a"; c.beginPath(); c.moveTo(x - 12 * s, y - 4 * s); c.quadraticCurveTo(x - 14 * s, y - 30 * s * f, x, y - 44 * s * f); c.quadraticCurveTo(x + 14 * s, y - 30 * s * f, x + 12 * s, y - 4 * s); c.fill();
    c.fillStyle = "#ffe07a"; c.beginPath(); c.moveTo(x - 6 * s, y - 4 * s); c.quadraticCurveTo(x - 6 * s, y - 18 * s * f, x, y - 26 * s * f); c.quadraticCurveTo(x + 6 * s, y - 18 * s * f, x + 6 * s, y - 4 * s); c.fill();
  }
  var dust = []; for (var di = 0; di < 40; di++) dust.push({x: Math.random() * 1400, v: 60 + Math.random() * 80, p: Math.random() * 300});

  function templeBand(c, t, dt, W, H){
    var g = c.createLinearGradient(0, 0, 0, 282); g.addColorStop(0, "#1a1009"); g.addColorStop(1, "#3c2817"); c.fillStyle = g; c.fillRect(0, 0, W, 282);
    c.globalAlpha = 0.6; bricks(c, 0, 0, W, 282, 120, 46, "rgba(0,0,0,0)", "rgba(255,210,150,.05)"); c.globalAlpha = 1;
    // door alcove with emblem (reward)
    c.fillStyle = "#120a05"; c.beginPath(); c.moveTo(1520, 282); c.lineTo(1520, 150); c.quadraticCurveTo(1640, 70, 1760, 150); c.lineTo(1760, 282); c.fill();
    c.strokeStyle = "#7a5530"; c.lineWidth = 10; c.stroke();
    c.fillStyle = "#5a4128"; c.fillRect(1470, 120, 34, 162); c.fillRect(1776, 120, 34, 162); c.fillStyle = "#8a6a40"; c.fillRect(1462, 112, 50, 14); c.fillRect(1768, 112, 50, 14);
    torch(c, 1430, 170, 1, t, 0); torch(c, 1850, 170, 1, t, 2);
    emblem(c, 1640, 200, 66, built, N, t, built >= N ? 1 : 0.25 * built / Math.max(1, N));
    // falling dust
    var sb = 26 + threat * 1.45;
    c.fillStyle = "rgba(230,200,150,.55)";
    var nd = cleared ? 0 : Math.floor(8 + threat / 3);
    for (var i = 0; i < nd && i < dust.length; i++){ var d = dust[i]; var dy = sb + ((t * d.v + d.p) % (282 - sb + 20)); c.fillRect(d.x, dy, 3, 3); }
    // descending ceiling slab = threat
    var sg = c.createLinearGradient(0, 0, 0, sb); sg.addColorStop(0, "#3d2d1d"); sg.addColorStop(1, "#7a5c3a"); c.fillStyle = sg; c.fillRect(0, 0, W, sb);
    c.fillStyle = "#5e4529"; c.fillRect(0, sb - 22, W, 22);
    c.fillStyle = "#2a1c10"; for (var x = 0; x < W; x += 60){ c.beginPath(); c.moveTo(x + 6, sb); c.lineTo(x + 30, sb + 26); c.lineTo(x + 54, sb); c.closePath(); c.fill(); }
    c.strokeStyle = "rgba(255,210,140,.25)"; c.lineWidth = 3; c.beginPath(); for (x = 0; x < W; x += 40){ c.moveTo(x, sb - 18); c.lineTo(x + 20, sb - 6); c.lineTo(x + 40, sb - 18); } c.stroke();
    if (threat > 45){ c.strokeStyle = "rgba(0,0,0,.55)"; c.lineWidth = 4; c.beginPath(); var cx = [300, 760, 1180];
      for (i = 0; i < 3; i++){ c.moveTo(cx[i], sb - 22); c.lineTo(cx[i] + 18, sb - 50); c.lineTo(cx[i] - 6, sb - 70); c.lineTo(cx[i] + 14, sb - 96); } c.stroke(); }
    // room
    bricks(c, 0, 282, W, H - 282, 180, 76, "#2c1d10", "#36251a");
    glyphs(c, 0, 300, W, H - 300, 228);
    c.fillStyle = "rgba(0,0,0,.25)"; c.fillRect(0, 282, W, H - 282);
    c.fillStyle = "#c99a3e"; c.fillRect(0, 280, W, 8);
    c.fillStyle = "#5a3a1a"; c.beginPath(); c.moveTo(0, 288); for (x = 0; x <= W; x += 24) c.lineTo(x, (x / 24) % 2 ? 300 : 288); c.lineTo(W, 288); c.fill();
  }
  function hourglass(c, x, y, t){
    var rem = 1 - threat / 100;
    c.save(); c.translate(x, y);
    c.fillStyle = "#8a6a40"; c.fillRect(-26, -40, 52, 8); c.fillRect(-26, 32, 52, 8);
    c.strokeStyle = "#f0e2b8"; c.lineWidth = 4; c.beginPath(); c.moveTo(-18, -32); c.lineTo(18, -32); c.lineTo(3, 0); c.lineTo(18, 32); c.lineTo(-18, 32); c.lineTo(-3, 0); c.closePath(); c.stroke();
    c.fillStyle = "#ffd27a";
    var th = 26 * rem; c.beginPath(); c.moveTo(-14 * rem - 2, -2 - th); c.lineTo(14 * rem + 2, -2 - th); c.lineTo(2, -2); c.lineTo(-2, -2); c.closePath(); c.fill();
    var bh = 26 * (1 - rem); c.beginPath(); c.moveTo(-15, 30); c.lineTo(15, 30); c.lineTo(15 * (1 - bh / 30), 30 - bh); c.lineTo(-15 * (1 - bh / 30), 30 - bh); c.closePath(); c.fill();
    if (ticking){ c.fillRect(-1.5, 0, 3, 30 - bh); }
    c.restore();
  }

  var TEMPLE_HITS = [{x: 960, y: 400}, {x: 960, y: 510}, {x: 960, y: 620}, {x: 960, y: 730}, {x: 960, y: 840}];
  function templeFinale(c, t, dt, W, H){
    var DY = 270, DH = 690, CY = DY + DH / 2;
    bricks(c, 0, 0, W, 960, 160, 64, "#2a1b0e", "#33220f");
    glyphs(c, 0, 0, W, 960, 200);
    c.fillStyle = "rgba(0,0,0,.3)"; c.fillRect(0, 0, W, 960);
    c.fillStyle = "#4a3420"; c.fillRect(0, 960, W, 120); c.fillStyle = "rgba(0,0,0,.35)"; for (var x = 0; x < W; x += 160) c.fillRect(x, 960, 4, 120); c.fillRect(0, 960, W, 6);
    var open = ease((ft - 5.6) / 2.6) * 410;
    c.save(); c.beginPath(); c.rect(550, DY, 820, DH); c.clip();
    var lg = c.createRadialGradient(960, CY, 40, 960, CY, 520); lg.addColorStop(0, "#fffbe0"); lg.addColorStop(0.5, "#ffd56a"); lg.addColorStop(1, "#b0661a"); c.fillStyle = lg; c.fillRect(550, DY, 820, DH);
    if (open > 10){
      c.fillStyle = "#ffcf3a"; c.strokeStyle = "#7a4a10"; c.lineWidth = 6; c.beginPath(); c.moveTo(860, DY + DH); c.lineTo(900, DY + DH - 80); c.lineTo(1020, DY + DH - 80); c.lineTo(1060, DY + DH); c.closePath(); c.fill(); c.stroke();
      c.fillStyle = "#fff4b0"; c.beginPath(); c.arc(960, DY + DH - 100, 36, 0, TAU); c.fill(); c.stroke(); }
    var lit = Math.min(N, Math.floor(ease((ft - 1.5) / 3.2) * N + 0.0001));
    if (ft > 4.7) lit = N;
    for (var side = 0; side < 2; side++){
      c.save(); var dx = side ? open : -open;
      c.beginPath(); c.rect((side ? 960 : 550) + dx, DY, 410, DH); c.clip(); c.translate(dx, 0);
      var dg = c.createLinearGradient(550, 0, 1370, 0); dg.addColorStop(0, "#5a4128"); dg.addColorStop(0.5, "#7a5a36"); dg.addColorStop(1, "#5a4128"); c.fillStyle = dg; c.fillRect(550, DY, 820, DH);
      c.strokeStyle = "rgba(0,0,0,.4)"; c.lineWidth = 6; for (var yy = DY + 60; yy < DY + DH; yy += 90){ c.beginPath(); c.moveTo(560, yy); c.lineTo(1360, yy); c.stroke(); }
      c.fillStyle = "#1e140a"; c.fillRect(956, DY, 8, DH);
      emblem(c, 960, CY, 230, lit, N, t, ft > 4.7 ? 1 : lit / Math.max(1, N) * 0.6);
      c.restore();
    }
    c.restore();
    if (open > 10){ c.save(); c.globalAlpha = Math.min(1, open / 300) * 0.35; c.fillStyle = "#fff6c8"; for (var b = 0; b < 8; b++){ var ba = b * TAU / 8 + t * 0.3; c.beginPath(); c.moveTo(960, CY); c.arc(960, CY, 1400, ba, ba + 0.16); c.closePath(); c.fill(); } c.restore(); }
    c.fillStyle = "#3a2716"; c.fillRect(500, DY - 50, 920, 50); c.fillRect(500, DY - 50, 50, DH + 50); c.fillRect(1370, DY - 50, 50, DH + 50);
    c.strokeStyle = "#c99a3e"; c.lineWidth = 6; c.strokeRect(500, DY - 50, 920, DH + 50); c.strokeRect(550, DY, 820, DH);
    torch(c, 330, 560, 2.2, t, 1); torch(c, 1590, 560, 2.2, t, 3);
    if (ft < 8.8){ c.fillStyle = "rgba(230,200,150,.6)"; for (var i = 0; i < dust.length; i++){ var d = dust[i]; c.fillRect(d.x * 1.37, (t * d.v * 2 + d.p) % 960, 4, 4); } }
  }

  function svgExplorer(mood, w){
    var worried = mood === "worried";
    var eyes = worried ? '<circle cx="82" cy="100" r="7" fill="#2a1c10"/><circle cx="118" cy="100" r="7" fill="#2a1c10"/><path d="M70 84 l20 6 M130 84 l-20 6" stroke="#2a1c10" stroke-width="5" stroke-linecap="round"/>' :
      '<path d="M72 102 q10 -14 20 0 M108 102 q10 -14 20 0" stroke="#2a1c10" stroke-width="6" fill="none" stroke-linecap="round"/>';
    var mouth = worried ? '<path d="M88 130 q12 -9 24 0" stroke="#2a1c10" stroke-width="5" fill="none" stroke-linecap="round"/>' : '<path d="M82 122 q18 22 36 0z" fill="#9a3020" stroke="#2a1c10" stroke-width="5" stroke-linejoin="round"/>';
    return '<svg viewBox="0 -40 200 290" width="' + w + '" height="' + Math.round(w * 1.45) + '"><ellipse cx="100" cy="240" rx="74" ry="9" fill="rgba(0,0,0,.3)"/>' +
      '<path d="M36 240 q0 -92 64 -100 q64 8 64 100z" fill="#c9a86a" stroke="#2a1c10" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M66 150 l12 90 M134 150 l-12 90" stroke="#6b4423" stroke-width="11"/>' +
      '<rect x="88" y="196" width="24" height="20" rx="3" fill="#a88a50" stroke="#2a1c10" stroke-width="4"/>' +
      '<path d="M76 144 q24 20 48 0 l-10 28 -14 -10 -14 10z" fill="#d8452f" stroke="#2a1c10" stroke-width="5" stroke-linejoin="round"/>' +
      '<path d="M170 236 l12 -92" stroke="#6b4423" stroke-width="11" stroke-linecap="round"/>' +
      '<path d="M182 146 q-22 -22 -2 -52 q6 20 16 24 q8 20 -14 28z" fill="#ffb02e" stroke="#c8402f" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M182 140 q-10 -12 -2 -26 q4 10 8 12 q2 10 -6 14z" fill="#ffe680"/>' +
      '<circle cx="176" cy="196" r="12" fill="#e8b98a" stroke="#2a1c10" stroke-width="5"/>' +
      '<circle cx="100" cy="102" r="52" fill="#e8b98a" stroke="#2a1c10" stroke-width="7"/>' +
      '<path d="M50 90 q2 18 10 26 M150 90 q-2 18 -10 26" stroke="#6b3a1e" stroke-width="8" fill="none" stroke-linecap="round"/>' +
      '<circle cx="70" cy="118" r="2.5" fill="#a0603a"/><circle cx="62" cy="112" r="2.5" fill="#a0603a"/><circle cx="130" cy="118" r="2.5" fill="#a0603a"/><circle cx="138" cy="112" r="2.5" fill="#a0603a"/>' +
      eyes + mouth +
      '<ellipse cx="100" cy="66" rx="86" ry="17" fill="#e8d7a8" stroke="#2a1c10" stroke-width="6"/>' +
      '<path d="M46 66 q0 -60 54 -60 q54 0 54 60z" fill="#f2e3b8" stroke="#2a1c10" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M48 54 q52 12 104 0" stroke="#8a5a2b" stroke-width="9" fill="none"/>' +
      '<circle cx="100" cy="8" r="7" fill="#e8d7a8" stroke="#2a1c10" stroke-width="4"/></svg>';
  }
  function lockTemple(open){
    var glyph = '<path d="M30 58 L50 26 L70 58 Z" fill="none" stroke="' + (open ? "#fffbe0" : "#2a1c10") + '" stroke-width="5" stroke-linejoin="round"/><circle cx="50" cy="48" r="6" fill="' + (open ? "#fffbe0" : "#2a1c10") + '"/>';
    return '<svg viewBox="0 0 100 100" width="100%" height="100%">' + (open ? '<circle cx="50" cy="50" r="49" fill="rgba(255,220,120,.25)"/>' : '') +
      '<circle cx="50" cy="50" r="40" fill="' + (open ? "#e8b84a" : "#6a5236") + '" stroke="#2a1c10" stroke-width="6"/>' +
      '<circle cx="50" cy="50" r="31" fill="none" stroke="' + (open ? "#8a5a14" : "rgba(0,0,0,.35)") + '" stroke-width="3"/>' + glyph +
      '<path d="M34 72 h32" stroke="' + (open ? "#fffbe0" : "#2a1c10") + '" stroke-width="5" stroke-linecap="round"/>' +
      (open ? '' : '<path d="M14 14 L86 86 M86 14 L14 86" stroke="#8b9096" stroke-width="9" stroke-linecap="round"/><path d="M14 14 L86 86 M86 14 L14 86" stroke="#c6cbd1" stroke-width="3" stroke-dasharray="6 6"/>') + '</svg>';
  }

  /* ================================================================ skin registry */
  var ART = {
    joseon: {band: joseonBand, finale: joseonFinale, guide: svgOfficer, lock: lockJoseon, hits: JOSEON_HITS, shot: {x: 660, y: 880},
      ink: "#fff3c4", hits_colors: ["#ffd84d", "#ff7a3a", "#fff"]},
    lab: {band: labBand, finale: labFinale, guide: svgResearcher, lock: lockLab, hits: LAB_HITS, shot: {x: 960, y: 300},
      ink: "#e8fbff", hits_colors: ["#9dffc8", "#e8fbff", "#5ad1ff"]},
    temple: {band: templeBand, finale: templeFinale, guide: svgExplorer, lock: lockTemple, hits: TEMPLE_HITS, shot: {x: 960, y: 615},
      ink: "#fff1cc", hits_colors: ["#ffe680", "#fff6c8", "#ffb02e"], extra: function(c, t){ hourglass(c, 950, 76, t); }}
  };
  var SKIN = ART[W0.skin] ? W0.skin : "joseon", A = ART[SKIN];
  function markWorld(){ try { document.body.setAttribute("data-world", SKIN); } catch (e) {} }
  markWorld();

  function paint(c, t, dt, W, H){
    A.band(c, t, dt, W, H);
    var rem = 1 - threat / 100, col = threat > 75 ? "#ff4a3a" : (threat > 50 ? "#ffcf3a" : "#7fe08a");
    c.font = "900 36px sans-serif"; c.textBaseline = "middle"; c.fillStyle = A.ink; c.shadowColor = "#000"; c.shadowBlur = 8;
    c.fillText(threat > 75 ? T("threatDanger") : T("threatLabel"), 40, 48); c.shadowBlur = 0;
    c.fillStyle = "rgba(0,0,0,.65)"; c.fillRect(40, 76, 760, 34); c.fillStyle = col; c.fillRect(44, 80, 752 * rem, 26);
    c.fillStyle = "rgba(0,0,0,.5)"; for (var i = 1; i < 10; i++) c.fillRect(40 + i * 76, 76, 3, 34);
    c.font = "800 34px sans-serif"; c.fillStyle = A.ink; c.shadowColor = "#000"; c.shadowBlur = 6; c.fillText(Math.round(rem * 100) + "%", 820, 94); c.shadowBlur = 0;
    if (A.extra) A.extra(c, t);
    if (threat > 70 && !CALM){ var a = (0.15 + 0.2 * Math.abs(Math.sin(t * 5))) * Math.min(1, (threat - 70) / 20); var rg = c.createRadialGradient(W / 2, H / 2, 380, W / 2, H / 2, 1150); rg.addColorStop(0, "rgba(255,0,0,0)"); rg.addColorStop(1, "rgba(255,30,10," + a + ")"); c.fillStyle = rg; c.fillRect(0, 0, W, H); }
  }
  function hitGap(){ return 2.5 / Math.max(1, A.hits.length); }
  /* finale clock follows the engine's virtual time (same clock as NG.after), not frame count */
  function paintFinale(c, t, dt, W, H){ if (ftStart < 0) ftStart = t; ft = Math.max(0, t - ftStart); A.finale(c, t, dt, W, H); }

  /* ================================================================ helpers */
  function el(parent, cls, style, html){ var d = document.createElement("div"); d.className = cls; d.style.cssText = style || ""; if (html) d.innerHTML = html; parent.appendChild(d); return d; }
  function btn(parent, cls, style, html, fn){ var b = document.createElement("div"); b.className = cls; b.style.cssText = style; b.innerHTML = html; parent.appendChild(b); NG.button(b, fn); return b; }
  /* shrink font until the text fits its box (runs again after the scene is attached) */
  function fit(node, min){
    function run(){
      if (!node || !node.parentNode) return;
      var fs = parseFloat(node.style.fontSize) || parseFloat(window.getComputedStyle(node).fontSize) || 40, guard = 0;
      while ((node.scrollHeight > node.clientHeight + 2 || node.scrollWidth > node.clientWidth + 2) && fs > min && guard++ < 40){ fs -= 2; node.style.fontSize = fs + "px"; }
    }
    run(); NG.after(40, run);
    return node;
  }
  function guide(mood, w){ return A.guide(mood, w); }
  function teamsOn(){ return NG.state.teams && NG.state.teams.length >= 2; }
  function teamIdx(){ return teamsOn() ? cur % NG.state.teams.length : -1; }

  function bump(a){ threat += a; if (threat >= 100){ threat = 100; lose(); } }
  function penalty(target, msg){
    if (lost || locked) return; mistakes++; bump(PENALTY);
    if (target) NG.feedback(false, target, {text: (msg || T("wrongMsg")) + " (" + T("costFmt") + ")"});
    shake(0.5); flash("#ff2a1a", 0.22);
  }
  function lose(){
    if (lost || finale) return; lost = true; ticking = false; NG.sfx("lose"); NG.music.setTempo(1); lastTempo = 1;
    NG.after(500, function(){ NG.go("lose", {transition: "fade"}); });
  }
  function tick(dt){
    if (!ticking || NG.paused) return;
    threat += DRAIN * dt;
    if (threat >= 100){ threat = 100; lose(); return; }
    var tempo = threat > 80 ? 1.35 : (threat > 60 ? 1.2 : 1);
    if (tempo !== lastTempo){ lastTempo = tempo; NG.music.setTempo(tempo); }
    if (threat > 75){ warnT -= dt; if (warnT <= 0){ warnT = 3.5; NG.sfx("warn"); } }
  }

  /* ================================================================ flow */
  function start(){
    threat = 20; built = 0; cur = 0; mistakes = 0; hints = 0; lost = false; finale = false; lastTempo = 1; revealFn = null; advanceFn = null;
    NG.state.total = N; markWorld();
    if (!hooked){ hooked = true; NG.onUpdate(tick); }
    NG.teacher.hooks = {
      next: function(){ if (advanceFn) advanceFn(); },
      skip: function(){ if (advanceFn) advanceFn(); else if (!locked && revealFn) revealFn(); },
      reveal: function(){ if (!locked && revealFn) revealFn(); }
    };
    if (!N){ NG.go("lose", {transition: "fade"}); return; }
    NG.go("stage", {i: 0, transition: "iris"});
  }

  function solved(){
    if (locked || lost) return; locked = true; ticking = false; revealFn = null;
    built = cur + 1; threat = Math.max(0, threat - RELIEF);
    var lk = lockEls[cur];
    if (lk){ lk.className = "nx-lock open"; lk.querySelector(".ic").innerHTML = A.lock(true); NG.fx.pop(lk); var p = U.center(lk); NG.fx.burst(p.x, p.y, {count: 40, speed: 600, colors: A.hits_colors}); NG.feedback(true, lk, {text: T("openBadge")}); }
    var ti = teamIdx(); if (ti >= 0) NG.addScore(100, ti);
    NG.sfx("levelup"); flash("#ffe9a0", 0.3); NG.hud.setProgress(built / N);
    NG.after(1100, showExplain);
  }

  function showExplain(){
    if (!area) return;
    var it = items[cur], last = cur >= N - 1;
    area.innerHTML = "";
    var ofc = el(area, "nx-abs", "left:0;top:40px;width:270px", guide("happy", 250)); NG.fx.pop(ofc);
    var sc = el(area, "nx-scroll enter", "left:300px;top:0;width:1270px;height:410px;padding:26px 38px",
      '<div class="nx-head" style="font-size:48px;font-weight:900;margin-bottom:12px">✔ ' + U.esc(T("openHead", {ord: ORD[cur]})) + '</div>' +
      '<div class="nx-ex" style="font-size:42px;line-height:1.4;height:300px;overflow:hidden">' + U.esc(it.explain || "") + '</div>');
    fit(sc.querySelector(".nx-ex"), 30);
    var label = last ? T("finaleBtn") : T("nextBtn");
    btn(area, "nx-btn pulse", "left:300px;top:440px;width:640px;height:116px", U.esc(label), function(){ advance(); });
    advanceFn = advance;
  }
  function advance(){
    if (!advanceFn) return; advanceFn = null;
    if (cur >= N - 1) NG.go("finale", {transition: "wipe"}); else NG.go("stage", {i: cur + 1, transition: "wipe"});
  }

  /* ================================================================ puzzles */
  function shuffledNot(arr, same){
    var out = U.shuffle(arr.slice()), guard = 0;
    while (arr.length > 1 && same(out) && guard++ < 20) out = U.shuffle(arr.slice());
    return out;
  }
  var puz = {};

  puz.order = function(it){
    var picked = 0, cards = [], busy = false, m = it.cards.length;
    var list = shuffledNot(it.cards.map(function(c, k){ return {t: typeof c === "string" ? c : c.t, d: typeof c === "string" ? "" : (c.d || ""), k: k}; }), function(a){ return a.every(function(x, i){ return x.k === i; }); });
    var rows = Math.ceil(m / 2), pitch = Math.min(230, Math.floor(470 / rows)), hgt = pitch - 26, fs = hgt >= 180 ? 52 : 46;
    list.forEach(function(cd, i){
      var lonely = m % 2 === 1 && i === m - 1, left = lonely ? 400 : (i % 2) * 800;
      var b = U.h("button", {class: "nx-card", style: "left:" + left + "px;top:" + (Math.floor(i / 2) * pitch) + "px;width:770px;height:" + hgt + "px;font-size:" + fs + "px"},
        '<span class="nx-stamp"></span><span class="nx-tx">' + U.esc(cd.t) + '<small></small></span>');
      area.appendChild(b); cards.push({el: b, k: cd.k, d: cd.d, done: false});
      fit(b, 34);
      NG.button(b, function(){
        var o = cards[i]; if (locked || busy || o.done) return;
        if (o.k === picked){ o.done = true; picked++; b.className = "nx-card got"; b.querySelector(".nx-stamp").textContent = picked; NG.sfx("select"); NG.fx.pop(b); if (picked === m) solved(); }
        else {
          busy = true; b.className = "nx-card bad"; b.querySelector(".nx-stamp").textContent = "✖"; penalty(b);
          NG.after(900, function(){ cards.forEach(function(x){ x.done = false; x.el.className = "nx-card"; x.el.querySelector(".nx-stamp").textContent = ""; }); picked = 0; busy = false; });
        }
      });
    });
    el(area, "nx-note", "left:0;top:" + (rows * pitch + 14) + "px;width:1570px", U.esc(T("orderNote")));
    function nextCard(){ for (var q = 0; q < cards.length; q++) if (cards[q].k === picked) return cards[q]; return null; }
    return {
      hint: function(){
        var any = cards.some(function(x){ return x.d; }), shown = cards.some(function(x){ return x.el.querySelector("small").textContent; });
        if (any && !shown){ cards.forEach(function(x){ x.el.querySelector("small").textContent = x.d; fit(x.el, 30); }); return true; }
        var nc = nextCard(); if (!nc || busy) return false;
        nc.done = true; picked++; nc.el.className = "nx-card got"; nc.el.querySelector(".nx-stamp").textContent = picked; NG.fx.pop(nc.el);
        if (picked === m) NG.after(300, solved); return true;
      },
      reveal: function(){ cards.forEach(function(x){ x.done = true; x.el.className = "nx-card got"; x.el.querySelector(".nx-stamp").textContent = x.k + 1; x.el.querySelector("small").textContent = x.d; }); solved(); }
    };
  };

  puz.dial = function(it){
    var ans = String(it.answer).split("−").join("-").replace(/\s/g, "").slice(0, 6).split("");
    var m = ans.length, wheels = [], els = [], i;
    var col = m <= 4 ? 230 : (m === 5 ? 190 : 160), w = col - 30, dfs = w >= 190 ? 130 : (w >= 150 ? 104 : 88);
    for (i = 0; i < m; i++){
      var sign = ans[i] === "-" || ans[i] === "+";
      var set = sign ? ["+", "-"] : ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];
      var target = set.indexOf(ans[i]); if (target < 0) target = 0;
      wheels.push({set: set, v: sign ? (target + 1) % 2 : (target + 3 + i) % 10});
    }
    function show(k){ var s = wheels[k].set[wheels[k].v]; return s === "-" ? "−" : s; }
    function refresh(){ for (var k = 0; k < m; k++) els[k].textContent = show(k); }
    for (i = 0; i < m; i++) (function(k){
      var x = k * col, len = wheels[k].set.length;
      btn(area, "nx-btn arrow", "left:" + x + "px;top:0;width:" + w + "px;height:110px", "▲", function(){ if (locked) return; wheels[k].v = (wheels[k].v + 1) % len; refresh(); NG.sfx("tick"); NG.fx.pop(els[k]); });
      els[k] = el(area, "nx-dial", "left:" + x + "px;top:118px;width:" + w + "px;height:150px;font-size:" + dfs + "px", show(k));
      btn(area, "nx-btn arrow", "left:" + x + "px;top:276px;width:" + w + "px;height:110px", "▼", function(){ if (locked) return; wheels[k].v = (wheels[k].v + len - 1) % len; refresh(); NG.sfx("tick"); NG.fx.pop(els[k]); });
    })(i);
    var openW = Math.max(m * col - 30, 600), clueL = Math.max(m * col, openW + 30) + 30;
    var clue = el(area, "nx-scroll", "left:" + clueL + "px;top:0;width:" + (1570 - clueL) + "px;height:386px;padding:20px 30px;font-size:40px;line-height:1.4",
      '<div class="nx-head" style="font-size:44px;font-weight:900;margin-bottom:8px">' + U.esc(T("clueTitle")) + '</div><div class="nx-cl" style="height:290px;overflow:hidden;white-space:pre-line">' + U.esc(it.clue || "") + '</div>');
    fit(clue.querySelector(".nx-cl"), 30);
    var open = btn(area, "nx-btn gold", "left:0;top:416px;width:" + openW + "px;height:112px", U.esc(T("dialBtn")), function(){
      if (locked) return;
      var ok = true; for (var k = 0; k < m; k++) if (wheels[k].set[wheels[k].v] !== ans[k]) ok = false;
      if (ok) solved();
      else { penalty(open, T("dialWrong")); NG.fx.wobble(els[0]); }
    });
    return {
      hint: function(){
        var h = String(it.hint !== undefined ? it.hint : ans[0]).split("−").join("-").split(""), changed = false;
        for (var k = 0; k < h.length && k < m; k++){ var idx = wheels[k].set.indexOf(h[k]); if (idx >= 0 && wheels[k].v !== idx){ wheels[k].v = idx; changed = true; } }
        refresh(); return changed;
      },
      reveal: function(){ for (var k = 0; k < m; k++){ var idx = wheels[k].set.indexOf(ans[k]); wheels[k].v = idx < 0 ? 0 : idx; } refresh(); solved(); }
    };
  };

  puz.match = function(it){
    var n = it.pairs.length, idx = it.pairs.map(function(p, k){ return k; });
    var chipOrder = U.shuffle(idx.slice()), descOrder = shuffledNot(idx, function(a){ return a.every(function(x, i){ return x === chipOrder[i]; }); });
    var socks = [], chips = [], sel = null, placed = 0;
    var pitch = Math.min(150, Math.floor(570 / n)), hgt = pitch - 16, cfs = hgt >= 120 ? 56 : 46;
    function finishPlace(chip, sk, quiet){
      sk.full = true; chip.done = true; sk.el.className = "nx-sock full"; sk.el.textContent = ""; NG.snap(chip.el, sk.el); chip.el.classList.remove("sel"); chip.el.style.cursor = "default"; placed++; sel = null;
      if (!quiet){ NG.sfx("correct"); NG.fx.pop(sk.el); var p = U.center(sk.el); NG.fx.sparkle(p.x, p.y, 14); }
    }
    function tryPlace(chip, sk){
      if (locked || sk.full) return false;
      if (chip.k === sk.k){ finishPlace(chip, sk); if (placed === n) NG.after(300, solved); return true; }
      penalty(chip.el, T("matchWrong")); return false;
    }
    function sockFor(k){ for (var q = 0; q < socks.length; q++) if (socks[q].k === k) return socks[q]; return null; }
    descOrder.forEach(function(k, row){
      var top = row * pitch;
      var s = el(area, "nx-sock", "left:480px;top:" + top + "px;width:380px;height:" + hgt + "px", "");
      var sk = {el: s, k: k, full: false}; socks.push(sk);
      NG.button(s, function(){ if (sel && !sk.full) tryPlace(sel, sk); });
      fit(el(area, "nx-desc", "left:890px;top:" + top + "px;width:680px;height:" + hgt + "px", U.esc(it.pairs[k].what)), 28);
    });
    chipOrder.forEach(function(k, row){
      var b = el(area, "nx-chip", "left:0;top:" + (row * pitch) + "px;width:380px;height:" + hgt + "px;font-size:" + cfs + "px", '<span>' + U.esc(it.pairs[k].who) + '</span>');
      fit(b, 32);
      var chip = {el: b, k: k, done: false}; chips.push(chip);
      NG.drag(b, {
        onStart: function(){ if (chip.done) return; NG.sfx("pop"); },
        onDrop: function(center){ if (chip.done || locked) return false; for (var s = 0; s < socks.length; s++){ if (NG.hitTest(center, socks[s].el)) return tryPlace(chip, socks[s]); } return false; },
        onTap: function(){ if (chip.done || locked) return; chips.forEach(function(c){ c.el.classList.remove("sel"); }); sel = chip; b.classList.add("sel"); NG.sfx("select"); }
      });
    });
    if (T("matchNote")) el(area, "nx-note", "left:0;top:" + (n * pitch + 6) + "px;width:1570px", U.esc(T("matchNote")));
    return {
      hint: function(){ for (var r = 0; r < chips.length; r++){ if (!chips[r].done){ finishPlace(chips[r], sockFor(chips[r].k)); if (placed === n) NG.after(300, solved); return true; } } return false; },
      reveal: function(){ chips.forEach(function(c){ if (!c.done) finishPlace(c, sockFor(c.k), true); }); NG.after(300, solved); }
    };
  };

  puz.fake = function(it){
    var all = it.lines.map(function(t){ return {t: t, fake: false}; }); all.push({t: it.fake, fake: true});
    var list = U.shuffle(all), cards = [], m = list.length;
    var pitch = Math.min(114, Math.floor(566 / m)), hgt = pitch - 8, fs = m > 5 ? 40 : 46, st = Math.min(70, hgt - 16);
    list.forEach(function(o, i){
      var b = U.h("button", {class: "nx-card", style: "left:0;top:" + (i * pitch) + "px;width:1570px;height:" + hgt + "px;font-size:" + fs + "px"}, '<span class="nx-stamp" style="width:' + st + 'px;height:' + st + 'px;font-size:' + Math.round(st * 0.62) + 'px"></span><span class="nx-tx">' + U.esc(o.t) + '</span>');
      area.appendChild(b); var c = {el: b, o: o, used: false}; cards.push(c);
      fit(b, 30);
      NG.button(b, function(){
        if (locked || c.used) return; c.used = true;
        if (o.fake){ b.className = "nx-card got"; b.querySelector(".nx-stamp").textContent = "✔"; solved(); }
        else { b.className = "nx-card bad dim"; b.querySelector(".nx-stamp").textContent = "✖"; penalty(b, T("fakeWrong")); }
      });
    });
    return {
      hint: function(){ for (var q = 0; q < cards.length; q++){ var c = cards[q]; if (!c.o.fake && !c.used){ c.used = true; c.el.className = "nx-card dim"; c.el.querySelector(".nx-stamp").textContent = "✔"; return true; } } return false; },
      reveal: function(){ cards.forEach(function(c){ if (c.o.fake){ c.used = true; c.el.className = "nx-card got"; c.el.querySelector(".nx-stamp").textContent = "✔"; } }); solved(); }
    };
  };

  /* ================================================================ scenes */
  NG.scene("title", function(e){
    markWorld();
    cleared = false; NG.state.phase = "title"; NG.hud.show = false; NG.hud.render(); NG.timer.stop(); ticking = false; finale = false; threat = 20; built = 0; NG.bg.custom(paint);
    fit(el(e, "nx-banner nx-sub enter", "top:318px;height:60px;font-size:44px;white-space:nowrap;overflow:hidden", U.esc(fill(G.subtitle || ""))), 30);
    fit(el(e, "nx-banner shine", "top:380px;height:180px;font-size:150px;white-space:nowrap;overflow:hidden", U.esc(fill(G.title || ""))), 80);
    var lines = (W0.rules && W0.rules.length ? W0.rules : DEF.rules).slice(0, 4).map(function(x){ return U.esc(fill(x)); });
    var panel = el(e, "nx-scroll enter", "left:430px;top:600px;width:1060px;height:270px;padding:24px 36px;font-size:40px;line-height:1.5;overflow:hidden", lines.join("<br>"));
    fit(panel, 30);
    var o = el(e, "nx-abs", "left:150px;top:560px", guide("worried", 250));
    btn(e, "nx-btn pulse enter", "left:610px;top:900px;width:700px;height:120px", U.esc(T("startBtn")), function(){
      NG.unlockAudio(); var tn = +G.teams; NG.setupTeams(tn >= 2 ? Math.min(6, tn) : 0); NG.go("countdown", {transition: "wipe"}); });
    NG.after(500, function(){ NG.fx.pop(o); });
  });

  NG.scene("stage", function(e, data){
    cleared = false; cur = data.i; locked = false; lost = false; finale = false; advanceFn = null; ticking = true; lastTempo = 1; NG.music.setTempo(1);
    NG.state.phase = "play"; NG.hud.show = false; NG.hud.render(); NG.bg.custom(paint);
    var it = items[cur];
    var col = el(e, "nx-lockcol", ""); lockEls = [];
    var lh = Math.min(170, Math.floor((720 - (N - 1) * 14) / N)), icon = Math.min(80, Math.round(lh * 0.46)), lfs = Math.max(30, Math.min(36, Math.round(lh * 0.22)));
    for (var i = 0; i < N; i++){ var open = i < built;
      lockEls.push(el(col, "nx-lock" + (open ? " open" : (i === cur ? " cur" : "")), "height:" + lh + "px",
        '<div class="ic" style="width:' + icon + 'px;height:' + icon + 'px">' + A.lock(open) + '</div><div class="lb" style="font-size:' + lfs + 'px">' + U.esc(ORD[i] + " " + T("lockName")) + '</div>')); }
    var pr = el(e, "nx-scroll nx-prompt enter", "left:290px;top:296px;width:1070px;height:124px;font-size:60px", '<span>' + U.esc(it.q || "") + '</span>');
    fit(pr, 40);
    var ti = teamIdx();
    if (ti >= 0){ var tm = NG.state.teams[ti]; el(e, "nx-team", "left:310px;top:236px;border-color:" + (tm.color || "#fff"), U.esc(T("teamTurn", {team: (tm.icon || "") + " " + (tm.name || "")}))); }
    area = el(e, "nx-abs", "left:290px;top:452px;width:1570px;height:570px");
    var pz = puz[it.kind](it);
    revealFn = pz.reveal;
    var hb = btn(e, "nx-btn gold", "left:1390px;top:296px;width:470px;height:124px;font-size:42px", U.esc(T("hintBtn")), function(){
      if (locked || lost) return; if (pz.hint()){ hints++; NG.sfx("pop"); bump(HINT); NG.fx.float(T("hintFloat"), 1620, 280, "#ff8a7a"); }
    });
    fit(hb, 30);
    NG.fx.pop(lockEls[cur]);
  });

  NG.scene("finale", function(e){
    finale = true; ticking = false; ft = 0; ftStart = NG.now() / 1000; NG.state.phase = "play"; NG.hud.show = false; NG.hud.render(); NG.bg.custom(paintFinale); NG.music.setTempo(1);
    var ban = fit(el(e, "nx-banner enter", "top:60px;height:150px;font-size:120px;white-space:nowrap;overflow:hidden", U.esc(T("finaleBanner"))), 64);
    var done = false;
    function end(){ if (done) return; done = true; advanceFn = null;
      var perfect = mistakes === 0 && hints === 0;
      NG.finish({total: N, title: perfect ? T("resultPerfect") : T("resultTitle"), lines: [T("resultLine"), T("mistakesLine")]}); }
    advanceFn = end;
    NG.sfx("drumroll");
    NG.after(1500, function(){ NG.sfx("whoosh"); });
    NG.after(5000, function(){ NG.sfx("shoot"); NG.fx.burst(A.shot.x, A.shot.y, {count: 40, speed: 700, colors: A.hits_colors}); shake(0.4); });
    A.hits.forEach(function(h, kk){ NG.after(5600 + kk * hitGap() * 1000, function(){ NG.sfx("explode"); NG.fx.burst(h.x, h.y, {count: 50, speed: 800, colors: A.hits_colors}); shake(0.5); if (!CALM) NG.fx.hitstop(60); }); });
    NG.after(8800, function(){ NG.sfx("fanfare"); NG.fx.confetti(); ban.textContent = T("finaleWin"); ban.style.fontSize = "120px"; fit(ban, 64); });
    NG.after(11500, end);
  });

  NG.scene("result", function(e, d){
    markWorld();
    ticking = false; threat = 0; built = N; cleared = true; NG.state.phase = "result"; NG.hud.show = false; NG.hud.render(); NG.bg.custom(paint);
    var sc = mistakes + hints, stars = sc <= 1 ? 3 : (sc <= 4 ? 2 : 1), st = "";
    for (var q = 0; q < 3; q++) st += q < stars ? "⭐" : "☆";
    fit(el(e, "nx-banner enter", "top:320px;height:130px;font-size:100px;white-space:nowrap;overflow:hidden", U.esc((d && d.title) || T("resultTitle"))), 60);
    var body = '<div style="font-size:80px;line-height:1.2">' + st + '</div>' + U.esc(T("resultLine")) + '<br>' + U.esc(T("mistakesLine"));
    if (teamsOn()) body += '<div style="font-size:36px;margin-top:6px">' + NG.state.teams.map(function(tm){ return U.esc((tm.icon || "") + " " + tm.name + " " + tm.score); }).join(" · ") + '</div>';
    fit(el(e, "nx-scroll enter", "left:430px;top:490px;width:1060px;height:320px;padding:20px 36px;font-size:44px;line-height:1.5;text-align:center;overflow:hidden", body), 30);
    el(e, "nx-abs", "left:150px;top:520px", guide("happy", 250));
    btn(e, "nx-btn pulse enter", "left:610px;top:880px;width:700px;height:120px", U.esc(T("againBtn")), function(){ NG.restart(); });
    NG.fx.confetti();
  });

  NG.scene("lose", function(e){
    markWorld();
    cleared = false; NG.state.phase = "play"; NG.hud.show = false; NG.hud.render(); ticking = false; threat = 100; NG.bg.custom(paint);
    fit(el(e, "nx-banner enter", "top:340px;height:140px;font-size:110px;white-space:nowrap;overflow:hidden", U.esc(N ? T("loseTitle") : "문제가 없어요 (items 확인)")), 60);
    fit(el(e, "nx-scroll enter", "left:430px;top:540px;width:1060px;height:150px;padding:20px 36px;font-size:44px;line-height:1.4;display:flex;align-items:center;justify-content:center;text-align:center", U.esc(T("loseMsg"))), 30);
    el(e, "nx-abs", "left:140px;top:520px", guide("worried", 250));
    if (!N) return;
    btn(e, "nx-btn pulse", "left:440px;top:760px;width:640px;height:120px", U.esc(T("retryHere")), function(){ threat = 45; lost = false; NG.go("stage", {i: cur, transition: "wipe"}); });
    btn(e, "nx-btn gold", "left:1110px;top:760px;width:480px;height:120px", U.esc(T("retryAll")), function(){ built = 0; threat = 20; lost = false; mistakes = 0; hints = 0; NG.go("stage", {i: 0, transition: "wipe"}); });
  });

  return {
    start: start,
    toText: function(){
      var it = items[cur] || {};
      return {skin: SKIN, phase: NG.state.phase, stage: cur + 1, stages: N, kind: it.kind || "", locksOpen: built, threat: Math.round(threat),
        mistakes: mistakes, hints: hints, lost: lost, finale: finale, teams: teamsOn() ? NG.state.teams.map(function(t){ return t.score; }) : 0};
    }
  };
})();
