/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* MISSILE: quiz-show — 팀 퀴즈쇼 / 골든벨 / OX (객관식·OX 혼합) + 세계관 무대
   Based on assets/kits/quiz-show.js (kit itself is untouched).
   GAME.items = [{ type:"mc"|"ox", q:"문제", choices:["보기1",...], answer:0, exp:"해설" }]
     OX는 choices 생략 가능 (answer: 0=O, 1=X). 보너스: GAME.bonusEvery (기본 4문제마다 2배)
   GAME.world = { skin:"tv-studio"|"golden-bell"|"space-quiz", hostName, howto, lines:{...}, colors:{...}, ...texts }
   All words and colors come from GAME / GAME.world. Art is drawn here per world.skin.
*/
window.GAME_LOGIC = (function(){
  var U = NG.util, G = window.GAME || {}, WD = G.world || {};
  var SKIN = WD.skin || "tv-studio";
  if (["tv-studio", "golden-bell", "space-quiz"].indexOf(SKIN) < 0) SKIN = "tv-studio";
  var COL = WD.colors || {}, LINES = WD.lines || {};
  var items = [], idx = -1, locked = false, cur = null, retry = false, shown = 0;
  var results = [], teamHits = [], powered = 0, host = null, uid = 0;
  var MARKS = WD.marks || ["A", "B", "C", "D", "E", "F"];
  var BGS = { cheer: 0, warp: 0, stars: null, motes: null };

  /* ---------- world helpers ---------- */
  function T(k, d){ var v = WD[k]; return (v === undefined || v === null) ? (d === undefined ? "" : d) : v; }
  function C(k, d){ return COL[k] || d; }
  function esc(s){ return U.esc(String(s == null ? "" : s)); }
  function line(k, team){
    var l = LINES[k], s = "";
    if (typeof l === "string") s = l; else if (l && l.length) s = U.pick(l);
    return String(s).split("{team}").join(team ? team.name : "");
  }
  function fill(s, n, total){ return String(s || "").split("{n}").join(n).split("{total}").join(total); }
  function applyWorld(){
    if (!document.body) return;
    document.body.setAttribute("data-world", SKIN);
    Object.keys(COL).forEach(function(k){ if (typeof COL[k] === "string") document.body.style.setProperty("--w-" + k, COL[k]); });
  }
  applyWorld();

  /* ---------- sounds (synth, no files) ---------- */
  NG.defineSfx("qsBell", function(){
    var f = 587;
    [1, 2.0, 2.76, 4.07, 5.4].forEach(function(r, i){ NG.tone({ type:"sine", freq:f * r, dur:2.2 - i * 0.32, vol:0.34 / (i + 1), jitter:0, attack:0.004 }); });
  });
  NG.defineSfx("qsClap", function(){
    for (var i = 0; i < 34; i++) NG.tone({ type:"noise", freq:1200 + Math.random() * 2200, q:1.4, dur:0.05 + Math.random() * 0.05, vol:0.14 + Math.random() * 0.12, delay:Math.random() * 1.5, attack:0.002 });
    NG.tone({ type:"triangle", freq:784, dur:0.18, vol:0.18, jitter:0 }); NG.tone({ type:"triangle", freq:1046, dur:0.3, vol:0.18, jitter:0, delay:0.14 });
  });
  NG.defineSfx("qsPower", function(){
    NG.tone({ type:"sawtooth", freq:160, slide:960, dur:0.34, vol:0.16 });
    NG.tone({ type:"sine", freq:1318, dur:0.45, vol:0.22, jitter:0, delay:0.3 });
    NG.tone({ type:"sine", freq:1760, dur:0.5, vol:0.14, jitter:0, delay:0.38 });
  });
  NG.defineSfx("qsWarp", function(){
    NG.tone({ type:"sine", freq:140, slide:2400, dur:1.4, vol:0.26 });
    NG.tone({ type:"noise", freq:900, q:0.6, dur:1.5, vol:0.16, filter:"lowpass" });
  });

  /* ---------- host characters (original SVG) ---------- */
  function humanFaces(o){
    function eye(x, r, pr, dy){
      return '<ellipse cx="' + x + '" cy="' + (140 + dy) + '" rx="' + r + '" ry="' + (r * 1.2) + '" fill="#fff" stroke="' + o + '" stroke-width="4"/>' +
        '<circle cx="' + (x + 2) + '" cy="' + (143 + dy) + '" r="' + pr + '" fill="#1b1b2f"/><circle cx="' + (x + 5) + '" cy="' + (137 + dy) + '" r="3.2" fill="#fff"/>';
    }
    return '<g class="f f-idle">' + eye(114, 13, 7, 0) + eye(186, 13, 7, 0) + '<path d="M96 112 L128 108 M172 108 L204 112" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/><path d="M126 184 Q150 204 174 184" fill="none" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/></g>' +
      '<g class="f f-happy"><path d="M98 146 Q114 124 130 146 M170 146 Q186 124 202 146" fill="none" stroke="' + o + '" stroke-width="7" stroke-linecap="round"/><path d="M120 176 Q150 224 180 176 Z" fill="#8a1f33" stroke="' + o + '" stroke-width="5" stroke-linejoin="round"/><path d="M134 198 Q150 188 166 198 Q150 214 134 198Z" fill="#ff7a8a"/></g>' +
      '<g class="f f-sad">' + eye(114, 12, 6, 4) + eye(186, 12, 6, 4) + '<path d="M96 110 L128 120 M204 110 L172 120" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/><path d="M132 198 Q150 186 168 198" fill="none" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/></g>' +
      '<g class="f f-wow">' + eye(114, 17, 9, -2) + eye(186, 17, 9, -2) + '<path d="M94 100 Q112 90 130 98 M170 98 Q188 90 206 100" fill="none" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/><ellipse cx="150" cy="194" rx="13" ry="17" fill="#8a1f33" stroke="' + o + '" stroke-width="5"/></g>';
  }
  function arm(d, fillc, o){ return '<path d="' + d + '" fill="none" stroke="' + o + '" stroke-width="36" stroke-linecap="round"/><path d="' + d + '" fill="none" stroke="' + fillc + '" stroke-width="23" stroke-linecap="round"/>'; }

  function tvHostSVG(){
    var o = C("outline", "#1a0f2e"), sk = C("skin", "#ffd6b0"), suit = C("hostMain", "#e8344e"), suit2 = C("hostSub", "#a81a35"), hair = C("hair", "#2a1a14"), bow = C("prop", "#ffd23f"), ch = C("cheek", "#ff8fa3");
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
      humanFaces(o) +
      arm("M210 272 Q256 262 240 226", suit, o) + '<circle cx="238" cy="222" r="18" fill="' + sk + '" stroke="' + o + '" stroke-width="5"/>' +
      '<rect x="230" y="170" width="16" height="56" rx="7" fill="#2b2b35" stroke="' + o + '" stroke-width="4" transform="rotate(-14 238 198)"/>' +
      '<rect x="229" y="182" width="18" height="9" fill="' + bow + '" transform="rotate(-14 238 198)"/>' +
      '<circle cx="230" cy="164" r="19" fill="#b8c0d0" stroke="' + o + '" stroke-width="5"/><path d="M216 158 L244 158 M214 168 L246 168" stroke="#6b7385" stroke-width="3"/>' +
      '</svg>';
  }

  function bellHostSVG(){
    var o = C("outline", "#2b1a0e"), sk = C("skin", "#ffdcbc"), top = C("hostMain", "#3f8f5a"), top2 = C("hostSub", "#2c6a41"), hair = C("hair", "#5a3420"), pr = C("prop", "#c8372d"), ch = C("cheek", "#ff8fa3");
    return '<svg viewBox="0 0 300 440" width="300" height="440">' +
      '<ellipse cx="150" cy="430" rx="92" ry="11" fill="rgba(0,0,0,.3)"/>' +
      '<rect x="116" y="360" width="26" height="58" rx="10" fill="' + sk + '" stroke="' + o + '" stroke-width="6"/><rect x="158" y="360" width="26" height="58" rx="10" fill="' + sk + '" stroke="' + o + '" stroke-width="6"/>' +
      '<path d="M100 424 Q104 410 130 412 L144 414 L144 428 Z" fill="' + pr + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/><path d="M200 424 Q196 410 170 412 L156 414 L156 428 Z" fill="' + pr + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M84 330 L216 330 L234 384 L66 384 Z" fill="' + C("skirt", "#3b3f6b") + '" stroke="' + o + '" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M50 120 Q40 34 150 32 Q262 34 250 120 L256 222 Q234 238 212 222 L208 130 L92 130 L88 222 Q66 238 44 222 Z" fill="' + hair + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M80 252 Q150 228 220 252 L230 344 Q150 362 70 344 Z" fill="' + top + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M124 244 L150 288 L176 244 Z" fill="#fffaf0" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/><path d="M124 244 L138 270 L150 252 L162 270 L176 244" fill="#fffaf0" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M150 288 L150 342" stroke="' + top2 + '" stroke-width="5"/><circle cx="150" cy="304" r="5" fill="#fff"/><circle cx="150" cy="326" r="5" fill="#fff"/>' +
      arm("M90 268 Q60 300 118 318", top, o) + arm("M210 268 Q246 300 196 318", top, o) +
      '<g transform="rotate(-8 160 300)"><rect x="112" y="262" width="98" height="74" rx="8" fill="#fffef8" stroke="' + o + '" stroke-width="5"/><path d="M126 282 L196 282 M126 298 L190 298 M126 314 L178 314" stroke="' + C("ink", "#4a6fb5") + '" stroke-width="5" stroke-linecap="round"/></g>' +
      '<circle cx="118" cy="320" r="15" fill="' + sk + '" stroke="' + o + '" stroke-width="5"/><circle cx="198" cy="318" r="15" fill="' + sk + '" stroke="' + o + '" stroke-width="5"/>' +
      '<circle cx="150" cy="142" r="94" fill="' + sk + '" stroke="' + o + '" stroke-width="7"/>' +
      '<path d="M58 130 Q66 46 150 44 Q234 46 242 130 Q214 92 176 98 Q160 76 140 98 Q96 92 58 130 Z" fill="' + hair + '" stroke="' + o + '" stroke-width="7" stroke-linejoin="round"/>' +
      '<path d="M208 70 l10 -14 l10 14 l-10 14 z" fill="' + pr + '" stroke="' + o + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<ellipse cx="94" cy="180" rx="15" ry="8" fill="' + ch + '" opacity=".55"/><ellipse cx="206" cy="180" rx="15" ry="8" fill="' + ch + '" opacity=".55"/>' +
      humanFaces(o) +
      '<g fill="rgba(255,255,255,.14)" stroke="' + C("glasses", "#7a3b1e") + '" stroke-width="6"><circle cx="114" cy="141" r="27"/><circle cx="186" cy="141" r="27"/></g><path d="M141 138 Q150 130 159 138" fill="none" stroke="' + C("glasses", "#7a3b1e") + '" stroke-width="6"/>' +
      '</svg>';
  }

  function robotSVG(){
    var o = C("outline", "#0d1626"), m = C("hostMain", "#dfe7f2"), s = C("hostSub", "#8fa3c0"), g = C("glow", "#5cf2ff"), a = C("prop", "#ff9f43");
    function face(){
      var st = ' fill="none" stroke="' + g + '" stroke-linecap="round" ';
      return '<g class="f f-idle"><rect x="104" y="124" width="24" height="36" rx="11" fill="' + g + '"/><rect x="172" y="124" width="24" height="36" rx="11" fill="' + g + '"/><path d="M134 182 Q150 190 166 182"' + st + 'stroke-width="6"/></g>' +
        '<g class="f f-happy"><path d="M100 150 Q116 124 132 150 M168 150 Q184 124 200 150"' + st + 'stroke-width="9"/><path d="M126 172 Q150 198 174 172"' + st + 'stroke-width="7"/></g>' +
        '<g class="f f-sad"><path d="M102 132 L130 144 M198 132 L170 144"' + st + 'stroke-width="8"/><path d="M134 186 Q150 174 166 186"' + st + 'stroke-width="6"/></g>' +
        '<g class="f f-wow"><circle cx="116" cy="140" r="17"' + st + 'stroke-width="8"/><circle cx="184" cy="140" r="17"' + st + 'stroke-width="8"/><circle cx="150" cy="184" r="9" fill="' + g + '"/></g>';
    }
    return '<svg viewBox="0 0 300 440" width="300" height="440">' +
      '<ellipse cx="150" cy="432" rx="70" ry="9" fill="rgba(0,0,0,.35)"/>' +
      '<g class="qs-flame"><path d="M122 384 Q150 452 178 384 Z" fill="' + a + '"/><path d="M136 384 Q150 428 164 384 Z" fill="#fff6b0"/></g>' +
      '<rect x="112" y="372" width="76" height="22" rx="10" fill="' + s + '" stroke="' + o + '" stroke-width="5"/>' +
      '<g class="qs-wave">' + arm("M94 292 Q52 292 46 240", s, o) + '<circle cx="46" cy="232" r="17" fill="' + m + '" stroke="' + o + '" stroke-width="5"/><path d="M36 220 L32 206 M56 220 L60 206" stroke="' + o + '" stroke-width="6" stroke-linecap="round"/></g>' +
      arm("M206 292 Q250 312 244 352", s, o) + '<circle cx="244" cy="358" r="17" fill="' + m + '" stroke="' + o + '" stroke-width="5"/>' +
      '<rect x="88" y="248" width="124" height="134" rx="46" fill="' + m + '" stroke="' + o + '" stroke-width="7"/>' +
      '<rect x="112" y="280" width="76" height="56" rx="14" fill="#0b1530" stroke="' + o + '" stroke-width="4"/>' +
      '<circle class="qs-blink" cx="132" cy="308" r="8" fill="' + g + '"/><circle class="qs-blink d2" cx="150" cy="308" r="8" fill="' + a + '"/><circle class="qs-blink d3" cx="168" cy="308" r="8" fill="#7dff8a"/>' +
      '<rect x="134" y="226" width="32" height="28" rx="8" fill="' + s + '" stroke="' + o + '" stroke-width="5"/>' +
      '<rect x="28" y="118" width="24" height="60" rx="11" fill="' + s + '" stroke="' + o + '" stroke-width="5"/><rect x="248" y="118" width="24" height="60" rx="11" fill="' + s + '" stroke="' + o + '" stroke-width="5"/>' +
      '<line x1="150" y1="66" x2="150" y2="30" stroke="' + o + '" stroke-width="6"/><circle class="qs-blink" cx="150" cy="24" r="13" fill="' + a + '" stroke="' + o + '" stroke-width="4"/>' +
      '<rect x="46" y="64" width="208" height="168" rx="56" fill="' + m + '" stroke="' + o + '" stroke-width="7"/>' +
      '<rect x="70" y="88" width="160" height="120" rx="38" fill="#08122a" stroke="' + o + '" stroke-width="5"/>' +
      '<g class="qs-face">' + face() + '</g>' +
      '<path d="M86 104 Q108 94 138 96" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="6" stroke-linecap="round"/>' +
      '</svg>';
  }

  function hostSVG(){ return SKIN === "space-quiz" ? robotSVG() : (SKIN === "golden-bell" ? bellHostSVG() : tvHostSVG()); }
  function hostHTML(cls){
    return '<div class="abs qs-host ' + (cls || "") + '" data-mood="idle"><div class="qs-bubble empty"><span></span></div><div class="qs-bob">' + hostSVG() + '</div></div>';
  }
  function hostCtl(el){
    if (!el) return { say:function(){}, hop:function(){}, mood:function(){} };
    var bub = el.querySelector(".qs-bubble"), sp = bub.querySelector("span");
    return {
      el: el,
      mood: function(m){ el.setAttribute("data-mood", m || "idle"); },
      say: function(text, m){
        if (m) el.setAttribute("data-mood", m);
        if (text){ sp.textContent = text; bub.classList.remove("empty"); NG.fx.pop(bub); } else bub.classList.add("empty");
      },
      hop: function(){ el.classList.remove("hop"); void el.offsetWidth; el.classList.add("hop"); NG.after(750, function(){ el.classList.remove("hop"); }); }
    };
  }

  /* ---------- golden bell ---------- */
  function bellSVG(size){
    var id = "qsbg" + (++uid), g1 = C("bell", "#ffd54a"), g2 = C("bellDeep", "#c98a12"), o = C("bellLine", "#6b3f05");
    return '<svg class="qs-bellsvg" viewBox="0 0 200 230" width="' + size + '" height="' + Math.round(size * 1.15) + '"><defs><linearGradient id="' + id + '" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="' + g2 + '"/><stop offset=".32" stop-color="' + g1 + '"/><stop offset=".52" stop-color="#fff6c8"/><stop offset=".72" stop-color="' + g1 + '"/><stop offset="1" stop-color="' + g2 + '"/></linearGradient></defs>' +
      '<path d="M100 0 L100 18" stroke="' + o + '" stroke-width="7"/>' +
      '<g class="qs-swing"><circle cx="100" cy="26" r="11" fill="none" stroke="' + o + '" stroke-width="7"/>' +
      '<circle class="qs-clap" cx="100" cy="204" r="16" fill="' + g2 + '" stroke="' + o + '" stroke-width="6"/>' +
      '<path d="M100 34 C66 34 54 66 52 104 C50 140 40 160 22 180 L178 180 C160 160 150 140 148 104 C146 66 134 34 100 34 Z" fill="url(#' + id + ')" stroke="' + o + '" stroke-width="6" stroke-linejoin="round"/>' +
      '<path d="M46 152 Q100 166 154 152" fill="none" stroke="' + o + '" stroke-width="4" opacity=".55"/><path d="M58 88 Q100 98 142 88" fill="none" stroke="' + o + '" stroke-width="4" opacity=".4"/>' +
      '<rect x="14" y="176" width="172" height="18" rx="9" fill="' + g2 + '" stroke="' + o + '" stroke-width="6"/>' +
      '<path d="M76 58 Q64 98 66 140" stroke="#fff" stroke-opacity=".65" stroke-width="9" fill="none" stroke-linecap="round"/></g></svg>';
  }
  function bellInner(size){ return '<div class="qs-bellglow"></div><div class="qs-bellring">' + bellSVG(size) + '</div>'; }
  function applyBell(box, lvl, ring){
    if (!box) return;
    var svg = box.querySelector("svg"), glow = box.querySelector(".qs-bellglow"), rg = box.querySelector(".qs-bellring");
    lvl = U.clamp(lvl, 0, 1);
    svg.style.filter = "brightness(" + (0.7 + lvl * 0.5).toFixed(2) + ") saturate(" + (0.55 + lvl * 0.65).toFixed(2) + ")";
    glow.style.opacity = (0.08 + lvl * 0.92).toFixed(2);
    glow.style.transform = "scale(" + (0.6 + lvl * 0.7).toFixed(2) + ")";
    rg.style.transform = "scale(" + (0.84 + lvl * 0.24).toFixed(3) + ")";
    if (ring){
      var sw = box.querySelector(".qs-swing");
      sw.classList.remove("ring"); void sw.getBoundingClientRect(); sw.classList.add("ring");
      var c = U.center(box); NG.fx.sparkle(c.x, c.y, 16 + Math.round(lvl * 20));
    }
  }
  function studentsHTML(up){
    var h = '<div class="qs-students">', hairs = [C("hair", "#5a3420"), "#1f1a17", "#3b2a20", "#2a2320"], board = T("boardText", "O");
    for (var i = 0; i < 8; i++){
      h += '<div class="qs-stu' + (up ? " up" : "") + '" style="left:' + (440 + i * 176) + 'px;transition-delay:' + (i * 0.05) + 's">' +
        '<svg viewBox="0 0 140 150" width="140" height="150"><g class="qs-board"><rect x="26" y="8" width="88" height="64" rx="6" fill="#fff" stroke="#3a2a1a" stroke-width="5"/>' +
        '<text x="70" y="56" text-anchor="middle" font-size="44" font-weight="900" fill="' + C("ink", "#1d3c8f") + '">' + esc(board) + '</text></g>' +
        '<path d="M14 150 Q18 104 70 100 Q122 104 126 150 Z" fill="' + C("uniform", "#2f4f8f") + '" stroke="#1a1410" stroke-width="5"/>' +
        '<circle cx="70" cy="82" r="30" fill="' + C("skin", "#ffdcbc") + '" stroke="#1a1410" stroke-width="5"/>' +
        '<path d="M40 80 Q40 48 70 48 Q100 48 100 80 Q86 64 70 66 Q54 64 40 80 Z" fill="' + hairs[i % 4] + '" stroke="#1a1410" stroke-width="4"/></svg></div>';
    }
    return h + "</div>";
  }

  /* ---------- tv studio ---------- */
  function teamList(){
    var t = NG.state.teams;
    return t.length ? t : [{ name:T("soloLabel", ""), icon:T("soloIcon", ""), color:C("solo", "#ffd23f") }];
  }
  function podiumsHTML(big){
    var list = teamList(), multi = NG.state.teams.length > 0, cap = Math.max(1, Math.ceil(items.length / list.length));
    var best = 0; list.forEach(function(t){ best = Math.max(best, multi ? t.score : NG.state.score); });
    var h = '<div class="qs-podiums' + (big ? " big" : "") + '">';
    list.forEach(function(tm, i){
      var on = multi ? (NG.state.turn === i) : true, hits = Math.min(cap, teamHits[i] || 0), lamps = "";
      var lw = Math.max(10, Math.min(30, Math.floor(250 / cap) - 8));
      for (var k = 0; k < cap; k++) lamps += '<i class="' + (k < hits ? "lit" : "") + '" style="width:' + lw + 'px"></i>';
      var sc = multi ? tm.score : NG.state.score, win = big && best > 0 && sc === best;
      var hgt = big ? Math.round(170 + 150 * (best ? sc / best : 0)) : 0;
      h += '<div class="qs-pod' + (on && !big ? " on" : "") + (win ? " win" : "") + '" data-i="' + i + '" style="--tc:' + tm.color + (big ? ';height:' + hgt + 'px' : '') + '">' +
        (win ? '<div class="qs-crown">' + esc(T("winIcon", "👑")) + '</div>' : '') +
        '<div class="qs-pod-top"></div><div class="qs-pod-face"><div class="qs-pod-name">' + esc(tm.icon) + ' ' + esc(tm.name) + '</div><div class="qs-lamps">' + lamps + '</div></div></div>';
    });
    return h + "</div>";
  }
  function applauseOn(el, ms){
    if (!el) return;
    el.classList.add("on");
    NG.after(ms || 2600, function(){ el.classList.remove("on"); });
  }

  /* ---------- space station ---------- */
  function stationHTML(big){
    var n = items.length, h = '<div class="qs-station' + (big ? " big" : "") + '"><div class="qs-truss"></div><div class="qs-solar"></div>';
    for (var i = 0; i < n; i++){
      var cls = results[i] === true ? "on" : (results[i] === false ? "miss" : (i === idx && !big ? "cur" : ""));
      if (big) cls = "";
      h += '<div class="qs-mod ' + cls + '" data-i="' + i + '"><i></i><i></i><i></i></div>';
    }
    return h + '<div class="qs-solar"></div></div>';
  }
  function gaugeHTML(){
    var n = items.length || 1, p = powered / n, r = 54, circ = 2 * Math.PI * r;
    return '<div class="qs-gauge"><svg viewBox="0 0 140 140" width="136" height="136"><circle cx="70" cy="70" r="' + r + '" class="trk"/>' +
      '<circle cx="70" cy="70" r="' + r + '" class="val" stroke-dasharray="' + circ.toFixed(1) + '" stroke-dashoffset="' + (circ * (1 - p)).toFixed(1) + '" transform="rotate(-90 70 70)"/></svg>' +
      '<div class="qs-gauge-n">' + Math.round(p * 100) + '%</div></div><div class="qs-gauge-txt"><div>' + esc(T("powerLabel", "")) + '</div><b>' + powered + ' / ' + n + '</b></div>';
  }

  /* ---------- canvas backgrounds (static parts cached once, small moving parts per frame) ---------- */
  function layer(draw){ var c = document.createElement("canvas"); c.width = 1920; c.height = 1080; draw(c.getContext("2d")); return c; }
  function rr(ctx, x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath(); }
  var CACHE = {};

  function bgTV(ctx, t, dt, W, H){
    BGS.cheer = Math.max(0, BGS.cheer - dt * 0.42);
    if (!CACHE.tv) CACHE.tv = layer(function(c){
      var g = c.createLinearGradient(0, 0, 0, 1080);
      g.addColorStop(0, C("bgTop", "#0a0620")); g.addColorStop(0.72, C("bgMid", "#26093f")); g.addColorStop(1, C("bgBottom", "#08030f"));
      c.fillStyle = g; c.fillRect(0, 0, 1920, 1080);
      c.fillStyle = "rgba(255,255,255,.05)";
      for (var r = 0; r < 13; r++) for (var k = 0; k < 32; k++) c.fillRect(22 + k * 60, 142 + r * 58, 22, 22);
      c.fillStyle = "#14102a"; c.fillRect(0, 112, 1920, 16);
      var fg = c.createLinearGradient(0, 900, 0, 1080);
      fg.addColorStop(0, C("floor", "#1d0f36")); fg.addColorStop(1, "#05020c");
      c.fillStyle = fg; c.fillRect(0, 900, 1920, 180);
      c.strokeStyle = "rgba(255,255,255,.08)"; c.lineWidth = 2;
      for (k = -8; k <= 8; k++){ c.beginPath(); c.moveTo(960 + k * 60, 900); c.lineTo(960 + k * 260, 1080); c.stroke(); }
    });
    ctx.save(); ctx.scale(W / 1920, H / 1080);
    ctx.drawImage(CACHE.tv, 0, 0);
    var l1 = C("led1", "#ff3d7f"), l2 = C("led2", "#3fd0ff"), ch = BGS.cheer, r, c;
    for (r = 0; r < 13; r++){
      for (c = 0; c < 32; c++){
        var w = 0.5 + 0.5 * Math.sin(c * 0.5 + r * 0.7 - t * 2.1);
        if (w < 0.35 && ch < 0.05) continue;
        ctx.globalAlpha = 0.1 + 0.3 * w + 0.55 * ch * w;
        ctx.fillStyle = Math.sin(c * 0.26 - r * 0.14 + t * 0.7) > 0 ? l1 : l2;
        ctx.fillRect(22 + c * 60, 142 + r * 58, 22, 22);
      }
    }
    ctx.globalAlpha = 1;
    var bulb = C("bulb", "#ffd23f"), step = Math.floor(t * 4);
    ctx.fillStyle = bulb;
    for (c = 0; c < 40; c++) if ((step + c) % 3 === 0) ctx.fillRect(20 + c * 48, 116, 9, 9);
    ctx.globalCompositeOperation = "lighter";
    var xs = [260, 760, 1180, 1680];
    for (var i = 0; i < 4; i++){
      var sw = Math.sin(t * 0.6 + i * 1.7) * 0.38, toC = (960 - xs[i]) / 1300;
      var ang = sw * (1 - ch) + toC * ch, x0 = xs[i], y0 = 100, len = 1050;
      var bx = x0 + Math.sin(ang) * len, by = y0 + Math.cos(ang) * len, half = 170 + ch * 60;
      ctx.globalAlpha = 0.16 + ch * 0.16;
      ctx.fillStyle = "#fffad8"; ctx.beginPath(); ctx.moveTo(x0 - 12, y0); ctx.lineTo(x0 + 12, y0);
      ctx.lineTo(bx + Math.cos(ang) * half, by - Math.sin(ang) * half); ctx.lineTo(bx - Math.cos(ang) * half, by + Math.sin(ang) * half); ctx.closePath(); ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 0.6 + 0.4 * Math.sin(t * 3); ctx.fillStyle = l1; ctx.fillRect(0, 898, 1920, 5);
    ctx.globalAlpha = 1; ctx.restore();
  }

  function bgBell(ctx, t, dt, W, H){
    BGS.cheer = Math.max(0, BGS.cheer - dt * 0.4);
    if (!CACHE.bell) CACHE.bell = layer(function(c){
      var g = c.createLinearGradient(0, 0, 0, 1080), i, x;
      g.addColorStop(0, C("wallTop", "#2a140a")); g.addColorStop(1, C("wall", "#5a2f17"));
      c.fillStyle = g; c.fillRect(0, 0, 1920, 1080);
      for (i = 0; i < 17; i++){ c.fillStyle = i % 2 ? "rgba(255,210,150,.05)" : "rgba(0,0,0,.08)"; c.fillRect(i * 120, 0, 120, 900); }
      c.fillStyle = "rgba(0,0,0,.25)"; c.fillRect(0, 560, 1920, 14);
      [520, 960, 1400].forEach(function(sx){
        var rg = c.createRadialGradient(sx, 980, 10, sx, 980, 520);
        rg.addColorStop(0, "rgba(255,226,150,.3)"); rg.addColorStop(1, "rgba(255,226,150,0)");
        c.fillStyle = rg; c.fillRect(0, 300, 1920, 780);
      });
      var fy = 900, fg = c.createLinearGradient(0, fy, 0, 1080);
      fg.addColorStop(0, C("floor", "#c98b4c")); fg.addColorStop(1, C("floorDeep", "#7a4b22"));
      c.fillStyle = fg; c.fillRect(0, fy, 1920, 180);
      c.strokeStyle = "rgba(60,30,10,.45)"; c.lineWidth = 3;
      for (i = 0; i < 5; i++){ var yy = fy + 8 + i * i * 8; c.beginPath(); c.moveTo(0, yy); c.lineTo(1920, yy); c.stroke(); }
      for (i = -10; i <= 10; i++){ c.beginPath(); c.moveTo(960 + i * 90, fy); c.lineTo(960 + i * 150, 1080); c.stroke(); }
      c.fillStyle = C("trim", "#e0a84a"); c.fillRect(0, fy - 6, 1920, 8);
      function curtain(x0, dir){
        for (var k = 0; k < 7; k++){
          var cx = x0 + dir * k * 26, cg = c.createLinearGradient(cx, 0, cx + dir * 26, 0);
          cg.addColorStop(0, C("curtainDark", "#5e0d14")); cg.addColorStop(0.5, C("curtain", "#b3202d")); cg.addColorStop(1, C("curtainDark", "#5e0d14"));
          c.fillStyle = cg; c.fillRect(Math.min(cx, cx + dir * 26), 0, 26, 1080);
        }
      }
      curtain(0, 1); curtain(1920, -1);
      c.fillStyle = C("curtain", "#b3202d"); c.beginPath(); c.moveTo(0, 0); c.lineTo(1920, 0); c.lineTo(1920, 30);
      for (x = 1920; x >= 80; x -= 80) c.quadraticCurveTo(x - 40, 70, x - 80, 30);
      c.closePath(); c.fill();
      c.strokeStyle = C("trim", "#e0a84a"); c.lineWidth = 6; c.beginPath(); c.moveTo(0, 30);
      for (x = 0; x < 1920; x += 80) c.quadraticCurveTo(x + 40, 70, x + 80, 30);
      c.stroke();
    });
    if (!CACHE.bellGlow) CACHE.bellGlow = layer(function(c){
      var rg = c.createRadialGradient(960, 700, 20, 960, 700, 900);
      rg.addColorStop(0, "rgba(255,226,140,.55)"); rg.addColorStop(1, "rgba(255,226,140,0)");
      c.fillStyle = rg; c.fillRect(0, 0, 1920, 1080);
    });
    ctx.save(); ctx.scale(W / 1920, H / 1080);
    ctx.drawImage(CACHE.bell, 0, 0);
    if (BGS.cheer > 0.02){ ctx.globalAlpha = BGS.cheer; ctx.drawImage(CACHE.bellGlow, 0, 0); ctx.globalAlpha = 1; }
    if (!BGS.motes){ BGS.motes = []; for (var i = 0; i < 40; i++) BGS.motes.push({ x:U.rand(200, 1720), y:U.rand(300, 1000), v:U.rand(6, 20), p:U.rand(0, 6.28) }); }
    ctx.fillStyle = "#ffebb4";
    BGS.motes.forEach(function(m){ m.y -= m.v * dt; if (m.y < 280) m.y = 1000; ctx.globalAlpha = 0.25 + 0.25 * Math.sin(t + m.p); ctx.fillRect(m.x + Math.sin(t * 0.7 + m.p) * 14, m.y, 4, 4); });
    ctx.globalAlpha = 1; ctx.restore();
  }

  var WIN = { x:40, y:126, w:1840, h:770 };
  function bgSpace(ctx, t, dt, W, H){
    BGS.cheer = Math.max(0, BGS.cheer - dt * 0.4);
    if (!CACHE.space) CACHE.space = layer(function(c){
      c.fillStyle = C("wall", "#1a2233"); c.fillRect(0, 0, 1920, 1080);
      var sg = c.createLinearGradient(0, WIN.y, 0, WIN.y + WIN.h);
      sg.addColorStop(0, C("space1", "#03061a")); sg.addColorStop(1, C("space2", "#1a0f3d"));
      c.save(); rr(c, WIN.x, WIN.y, WIN.w, WIN.h, 70); c.clip();
      c.fillStyle = sg; c.fillRect(WIN.x, WIN.y, WIN.w, WIN.h);
      var nb = c.createRadialGradient(1250, 420, 20, 1250, 420, 520);
      nb.addColorStop(0, "rgba(180,90,255,.28)"); nb.addColorStop(1, "rgba(180,90,255,0)");
      c.fillStyle = nb; c.fillRect(WIN.x, WIN.y, WIN.w, WIN.h);
      c.restore();
    });
    if (!CACHE.spaceTop) CACHE.spaceTop = layer(function(c){
      var i;
      c.save(); rr(c, WIN.x, WIN.y, WIN.w, WIN.h, 70); c.clip();
      var eg = c.createRadialGradient(960, 2050, 1000, 960, 2050, 1220);
      eg.addColorStop(0, C("earth1", "#1d6fd1")); eg.addColorStop(0.92, C("earth2", "#59c3ff")); eg.addColorStop(1, "rgba(120,220,255,0)");
      c.fillStyle = eg; c.beginPath(); c.arc(960, 2050, 1220, 0, 6.283); c.fill();
      c.fillStyle = "rgba(70,170,90,.55)"; c.beginPath(); c.ellipse(700, 900, 220, 40, 0.1, 0, 6.283); c.ellipse(1320, 930, 160, 30, -0.1, 0, 6.283); c.fill();
      c.restore();
      c.lineWidth = 26; c.strokeStyle = C("frame", "#3a4a66"); rr(c, WIN.x, WIN.y, WIN.w, WIN.h, 70); c.stroke();
      c.lineWidth = 4; c.strokeStyle = "rgba(255,255,255,.18)"; rr(c, WIN.x + 14, WIN.y + 14, WIN.w - 28, WIN.h - 28, 58); c.stroke();
      var fg = c.createLinearGradient(0, 910, 0, 1080);
      fg.addColorStop(0, C("floor", "#222c40")); fg.addColorStop(1, "#0b0f18");
      c.fillStyle = fg; c.fillRect(0, 910, 1920, 170);
      c.strokeStyle = "rgba(120,160,220,.16)"; c.lineWidth = 2;
      for (i = 0; i < 40; i++){ c.beginPath(); c.moveTo(i * 50, 910); c.lineTo(i * 50 - 60, 1080); c.stroke(); }
    });
    ctx.save(); ctx.scale(W / 1920, H / 1080);
    ctx.drawImage(CACHE.space, 0, 0);
    if (!BGS.stars){ BGS.stars = []; for (var i = 0; i < 200; i++) BGS.stars.push({ x:U.rand(0, 1920), y:U.rand(WIN.y + 10, WIN.y + WIN.h - 10), z:U.rand(0.2, 1), p:U.rand(0, 6.28) }); }
    var warp = BGS.warp;
    ctx.fillStyle = "#fff";
    BGS.stars.forEach(function(s){
      s.x -= (6 + warp * 1600) * s.z * dt;
      if (s.x < WIN.x){ s.x += WIN.w; s.y = U.rand(WIN.y + 10, WIN.y + WIN.h - 10); }
      ctx.globalAlpha = 0.35 + 0.65 * s.z * (0.6 + 0.4 * Math.sin(t * 2 + s.p));
      var sz = 1.5 + s.z * 2.5;
      ctx.fillRect(s.x, s.y, sz + warp * 260 * s.z, warp > 0.05 ? 1 + s.z * 2 : sz);
    });
    ctx.globalAlpha = 1;
    var drift = Math.sin(t * 0.15) * 12, px = 1700 + drift, py = 260;
    ctx.strokeStyle = C("ring", "rgba(255,230,180,.75)"); ctx.lineWidth = 10;
    ctx.beginPath(); ctx.ellipse(px, py, 170, 38, -0.3, Math.PI, 2 * Math.PI); ctx.stroke();
    ctx.fillStyle = C("planet2", "#c2672b"); ctx.beginPath(); ctx.arc(px, py, 92, 0, 6.283); ctx.fill();
    ctx.fillStyle = C("planet1", "#ffd28a"); ctx.beginPath(); ctx.arc(px - 16, py - 16, 70, 0, 6.283); ctx.fill();
    ctx.fillStyle = "rgba(160,80,30,.35)"; ctx.fillRect(px - 80, py - 6, 150, 12); ctx.fillRect(px - 70, py + 26, 130, 9);
    ctx.beginPath(); ctx.ellipse(px, py, 170, 38, -0.3, 0, Math.PI); ctx.stroke();
    var mx = 1430 - drift, my = 214;
    ctx.fillStyle = "#cfd6e6"; ctx.beginPath(); ctx.arc(mx, my, 40, 0, 6.283); ctx.fill();
    ctx.fillStyle = "rgba(90,100,130,.5)"; ctx.beginPath(); ctx.arc(mx - 10, my - 8, 9, 0, 6.283); ctx.arc(mx + 14, my + 12, 6, 0, 6.283); ctx.fill();
    ctx.drawImage(CACHE.spaceTop, 0, 0);
    var on = Math.floor(t * 2);
    ctx.fillStyle = C("glow", "#5cf2ff");
    for (i = 0; i < 16; i++) if ((on + i) % 5 === 0) ctx.fillRect(134 + i * 110, WIN.y + WIN.h - 4, 12, 12);
    if (BGS.cheer > 0){ ctx.globalAlpha = BGS.cheer * 0.12; ctx.fillRect(0, 0, 1920, 1080); ctx.globalAlpha = 1; }
    ctx.restore();
  }
  var PAINT = { "tv-studio": bgTV, "golden-bell": bgBell, "space-quiz": bgSpace };
  function setBg(){ NG.bg.custom(PAINT[SKIN]); }

  /* ---------- game flow (kit logic, kept) ---------- */
  function start(list){
    retry = !!list;
    items = list || U.shuffle((G.items || []).slice());
    idx = -1; results = []; teamHits = []; powered = 0; NG.state.total = items.length;
    BGS.cheer = 0; BGS.warp = 0; applyWorld(); setBg();
    NG.teacher.hooks = {
      next: next,
      skip: function(){ if (NG.sceneName === "q") show(idx + 1); },
      reveal: function(){ if (!locked && cur && NG.sceneName === "q") choose(-1, null, "reveal"); }
    };
    NG.retryWrong = function(){
      var wrongItems = items.filter(function(it){ return it._wrong; });
      if (!wrongItems.length) return;
      var teams = NG.state.teams.length;
      NG.state = { score:0, combo:0, maxCombo:0, correct:0, wrong:0, total:0, wrongList:[], teams:[], turn:0, phase:"play" };
      NG.setupTeams(teams); retry = true;
      wrongItems.forEach(function(it){ it._wrong = false; });
      NG.go("countdown");
      GAME_LOGIC._pending = wrongItems;
    };
    show(0);
  }

  function show(i){
    idx = i; locked = false; shown++; NG.timer.stop();
    if (idx >= items.length) return toFinale();
    cur = items[idx];
    var isOX = cur.type === "ox" || !cur.choices || !cur.choices.length;
    cur._isOX = isOX;
    var choices = isOX ? ["O", "X"] : cur.choices;
    var every = G.bonusEvery == null ? 4 : G.bonusEvery;
    var bonus = !retry && every > 0 && (idx + 1) % every === 0;
    cur._bonus = bonus;
    NG.hud.setProgress(idx / items.length);
    NG.go("q", { choices: choices, isOX: isOX, bonus: bonus, team: NG.currentTeam() });
  }

  function leftColumn(){
    var h = "";
    if (SKIN === "tv-studio") h += '<div class="abs qs-onair">' + esc(T("onAirText", "ON AIR")) + '</div><div class="abs qs-signbox"><div class="qs-applause">' + esc(T("signText", "APPLAUSE")) + '</div></div>';
    if (SKIN === "golden-bell") h += '<div class="abs qs-bellbox">' + bellInner(170) + '</div>';
    if (SKIN === "space-quiz") h += '<div class="abs qs-gaugebox">' + gaugeHTML() + '</div>';
    return h + hostHTML("qs-host-play");
  }
  function setDeco(){
    if (SKIN === "tv-studio") return podiumsHTML(false);
    if (SKIN === "golden-bell") return studentsHTML(false);
    return stationHTML(false);
  }

  NG.scene("q", function(el, d){
    var qlen = String(cur.q).length, qsize = qlen > 56 ? 60 : (qlen > 32 ? 66 : 76);
    var team = d.team, multi = NG.state.teams.length > 1;
    var html = '<div class="abs qs-set">' + setDeco() + '</div>' + leftColumn() +
      '<div class="abs qs-main"><div class="qs-head enter">' +
      '<div class="qs-chip">' + esc(T("qLabel", "문제")) + ' ' + (idx + 1) + ' / ' + items.length + '</div>' +
      (team && multi ? '<div class="qs-chip qs-team" style="border-color:' + team.color + '">' + esc(team.icon) + ' ' + esc(team.name) + ' ' + esc(T("turnText", "차례")) + '</div>' : '') +
      (d.bonus ? '<div class="qs-chip qs-bonus pulse">' + esc(T("bonusText", "⭐ 보너스 2배")) + '</div>' : '') +
      '</div><div class="qs-q enter" id="qbox" style="font-size:' + qsize + 'px">' + esc(cur.q) + '</div>';
    if (d.isOX){
      html += '<div class="qs-ox">' +
        '<button class="choice qs-oxbtn o enter" data-i="0"><span class="qs-oxch">O</span></button>' +
        '<button class="choice qs-oxbtn x enter" data-i="1" style="animation-delay:.08s"><span class="qs-oxch">X</span></button></div>';
    } else {
      html += '<div class="qs-grid' + (d.choices.length > 4 ? " many" : "") + '">';
      d.choices.forEach(function(c, i){ html += '<button class="choice enter" data-i="' + i + '" style="animation-delay:' + (i * 0.07) + 's"><span class="mark">' + esc(MARKS[i] || (i + 1)) + '</span><span class="qs-ct">' + esc(c) + '</span></button>'; });
      html += '</div>';
    }
    html += '<div id="expl"></div></div>';
    el.innerHTML = html;
    host = hostCtl(el.querySelector(".qs-host-play"));
    var say = (idx === 0) ? (retry ? (line("retry") || line("q")) : line("start")) :
      (d.bonus ? line("bonus") : (idx === items.length - 1 ? line("last") : ((multi && LINES.teamQ) ? line("teamQ", team) : line("q"))));
    host.say(say, d.bonus ? "wow" : "idle");
    if (SKIN === "golden-bell") applyBell(el.querySelector(".qs-bellbox"), items.length ? powered / items.length : 0, false);
    if (d.bonus){ NG.fx.badge(T("bonusBadge", "보너스 문제!"), "info", 1000); NG.sfx("powerup"); }
    var token = shown;
    el.setAttribute("data-qs", token);
    Array.prototype.forEach.call(el.querySelectorAll(".qs-main .choice"), function(b){
      NG.button(b, function(){ if (token === shown && el.parentNode) choose(+b.getAttribute("data-i"), b); });
    });
    if (G.timer) NG.timer.start(G.timer, function(){ if (!locked){ NG.fx.toast(T("timeoutToast", "⏰ 시간 끝!")); choose(-1, null, "timeout"); } });
  });

  function choose(i, btn, how){
    if (locked || !cur) return;
    var live = NG.el.scene.querySelector('.screen[data-qs="' + shown + '"]');
    if (!live) return;
    locked = true; NG.timer.stop();
    var my = shown, all = live.querySelectorAll(".qs-main .choice"), ans = cur.answer | 0, ok = i === ans;
    if (btn){ btn.classList.add("picked"); NG.fx.press(btn); }
    if (host) host.say(line("wait"), "wow");
    NG.sfx("drumroll", 520);
    Array.prototype.forEach.call(all, function(b){ if (b !== btn) b.classList.add("dim"); });
    NG.after(620, function(){
      if (my !== shown || NG.sceneName !== "q") return;
      var rightBtn = null;
      Array.prototype.forEach.call(all, function(b){
        b.classList.remove("dim"); var k = +b.getAttribute("data-i");
        if (k === ans){ b.classList.add("correct"); rightBtn = b; tick(b, "✔"); }
        else if (k === i){ b.classList.add("wrong"); tick(b, "✖"); }
        else b.classList.add("dim");
      });
      var t = NG.state.teams.length ? NG.state.turn : 0;
      if (ok){
        var pts = 100 * (cur._bonus ? 2 : 1);
        if (!NG.state.teams.length && G.timer && NG.timer.total) pts += Math.round(50 * (NG.timer.left / NG.timer.total));
        NG.feedback(true, btn);
        NG.addScore(pts, null, U.center(btn));
        results[idx] = true; teamHits[t] = (teamHits[t] || 0) + 1; powered++;
        if (host){ host.say(line("correct"), "happy"); host.hop(); }
      } else {
        cur._wrong = true; results[idx] = false;
        var ansText = cur._isOX ? (ans === 0 ? "O" : "X") : cur.choices[ans];
        NG.feedback(false, btn || rightBtn, { text: how === "timeout" ? T("timeoutText", "시간 초과!") : (how === "reveal" ? T("revealText", "정답 공개") : null), record: cur.q + " → " + ansText });
        if (rightBtn) NG.after(400, function(){ NG.fx.pop(rightBtn); });
        if (host) host.say(line(how || "wrong") || line("wrong"), how === "reveal" ? "wow" : "sad");
      }
      signature(ok, t);
      showExplain(ok, ans);
    });
  }

  function tick(b, sym){
    var m = b.querySelector(".mark");
    if (m) m.textContent = sym; else b.insertAdjacentHTML("beforeend", '<span class="qs-tick">' + sym + '</span>');
  }

  /* signature moment on each answer — one per world */
  function signature(ok, t){
    var scene = NG.el.scene.querySelector('.screen[data-qs="' + shown + '"]') || NG.el.scene;
    if (SKIN === "tv-studio"){
      var pod = scene.querySelector('.qs-pod[data-i="' + t + '"]');
      if (pod){
        var lamps = pod.querySelectorAll(".qs-lamps i"), n = Math.min(lamps.length, teamHits[t] || 0);
        Array.prototype.forEach.call(lamps, function(l, k){ l.className = k < n ? "lit" : ""; });
      }
      if (ok){
        BGS.cheer = 1; NG.sfx("qsClap");
        applauseOn(scene.querySelector(".qs-applause"), 2600);
        if (pod){ pod.classList.add("flash"); NG.after(1600, function(){ pod.classList.remove("flash"); }); }
      }
    } else if (SKIN === "golden-bell"){
      if (ok){
        BGS.cheer = 1; NG.sfx("qsBell");
        applyBell(scene.querySelector(".qs-bellbox"), powered / items.length, true);
        var st = scene.querySelectorAll(".qs-stu");
        Array.prototype.forEach.call(st, function(s){ s.classList.add("up"); });
        NG.after(1900, function(){ Array.prototype.forEach.call(st, function(s){ s.classList.remove("up"); }); });
      }
    } else {
      var mod = scene.querySelector('.qs-mod[data-i="' + idx + '"]');
      if (mod){ mod.classList.remove("cur"); mod.classList.add(ok ? "on" : "miss"); if (ok) mod.classList.add("just"); }
      var gb = scene.querySelector(".qs-gaugebox"); if (gb) gb.innerHTML = gaugeHTML();
      if (ok){
        BGS.cheer = 1; NG.sfx("qsPower");
        if (mod){ var c = U.center(mod); NG.fx.burst(c.x, c.y, { count:26, colors:[C("glow", "#5cf2ff"), C("prop", "#ff9f43"), "#ffffff"] }); }
      }
    }
  }

  function showExplain(ok, ans){
    var live = NG.el.scene.querySelector('.screen[data-qs="' + shown + '"]'), box = live ? live.querySelector("#expl") : null;
    if (!box) return;
    var ansText = cur._isOX ? (ans === 0 ? "O" : "X") : cur.choices[ans];
    var last = idx >= items.length - 1;
    box.innerHTML = '<div class="qs-expl enter"><div class="qs-expl-body">' +
      '<div class="qs-ans"><span class="qs-ansmark">' + (ok ? "✔" : "➜") + '</span> ' + esc(T("answerLabel", "정답")) + ' : <b>' + esc(ansText) + '</b></div>' +
      (cur.exp ? '<div class="qs-exp">' + esc(cur.exp) + '</div>' : '') +
      '</div><button class="btn small" id="nextBtn">' + esc(last ? T("lastNextText", T("nextText", "다음 ▶")) : T("nextText", "다음 ▶")) + '</button></div>';
    NG.button(box.querySelector("#nextBtn"), next);
  }

  function next(){ if (!locked || NG.sceneName !== "q") return; NG.nextTurn(); show(idx + 1); }

  /* ---------- finale (before result) ---------- */
  function toFinale(){
    NG.timer.stop(); NG.hud.setProgress(1);
    if (!items.length) return NG.finish({ total: 0 });
    if (NG.sceneName === "finale") return;
    NG.go("finale", {});
  }

  NG.scene("finale", function(el){
    var done = false, n = NG.state.correct, total = items.length;
    function go(){ if (done) return; done = true; NG.teacher.hooks = {}; BGS.warp = 0; NG.finish({ total: total }); }
    NG.teacher.hooks = { next: go, skip: go, reveal: function(){} };
    var art = "";
    if (SKIN === "tv-studio") art = '<div class="abs qs-fin-sign"><div class="qs-applause on">' + esc(T("signText", "APPLAUSE")) + '</div></div><div class="abs qs-fin-pods">' + podiumsHTML(true) + '</div>';
    else if (SKIN === "golden-bell") art = '<div class="abs qs-fin-bell">' + bellInner(300) + '</div><div class="abs qs-set">' + studentsHTML(false) + '</div>';
    else art = '<div class="abs qs-fin-station">' + stationHTML(true) + '</div>';
    el.innerHTML = art + '<div class="abs qs-fin-title">' + esc(fill(T("finaleTitle", ""), n, total)) + '</div>' +
      '<div class="abs qs-fin-sub">' + esc(fill(T("finaleSub", ""), n, total)) + '</div>' +
      hostHTML("qs-host-fin") + '<button class="btn abs qs-fin-btn">' + esc(T("resultText", "결과 보기 ▶")) + '</button>';
    host = hostCtl(el.querySelector(".qs-host-fin"));
    host.say(fill(line("finale"), n, total), "happy"); host.hop();
    NG.button(el.querySelector(".qs-fin-btn"), go);
    if (SKIN === "tv-studio"){
      BGS.cheer = 1; NG.sfx("qsClap"); NG.after(300, function(){ NG.fx.confetti(); });
      NG.after(1700, function(){ BGS.cheer = 1; NG.sfx("qsClap"); host.hop(); });
      NG.after(3200, function(){ BGS.cheer = 1; NG.fx.confetti(); NG.sfx("fanfare"); });
    } else if (SKIN === "golden-bell"){
      var box = el.querySelector(".qs-fin-bell"), lvl = Math.max(0.35, n / total);
      applyBell(box, 0.2, false);
      [400, 1500, 2600].forEach(function(ms, k){
        NG.after(ms, function(){ BGS.cheer = 1; applyBell(box, 0.2 + (lvl - 0.2) * (k + 1) / 3, true); NG.sfx("qsBell"); if (k === 2) NG.fx.rain(T("rainIcon", "✨")); });
      });
      NG.after(2700, function(){ Array.prototype.forEach.call(el.querySelectorAll(".qs-stu"), function(s){ s.classList.add("up"); }); host.hop(); });
    } else {
      var mods = el.querySelectorAll(".qs-mod"), k2 = 0;
      Array.prototype.forEach.call(mods, function(m, i){
        if (results[i] !== true) return;
        var at = 300 + (k2++) * 220;
        NG.after(at, function(){ m.classList.add("on", "just"); NG.sfx("coin"); var c = U.center(m); NG.fx.sparkle(c.x, c.y, 10); });
      });
      var endAt = 400 + k2 * 220;
      NG.after(endAt, function(){ host.say(fill(line("launch") || line("finale"), n, total), "wow"); NG.sfx("qsWarp"); NG.fx.flash("#ffffff", 0.3); });
      var warpGo = false;
      NG.onUpdate(function warpUp(dt){
        if (NG.sceneName !== "finale"){ NG.offUpdate(warpUp); BGS.warp = 0; return; }
        if (warpGo) BGS.warp = Math.min(1, BGS.warp + dt * 0.8);
      });
      NG.after(endAt, function(){ warpGo = true; });
      NG.after(endAt + 1600, function(){ host.mood("happy"); host.hop(); NG.fx.confetti(); NG.sfx("fanfare"); });
    }
    NG.after(SKIN === "space-quiz" ? Math.max(5600, 2600 + items.length * 220) : 5600, go);
  });

  /* ---------- title & result dressing (engine scenes wrapped, not replaced) ---------- */
  var baseTitle = NG.scenes && NG.scenes.title;
  if (baseTitle) NG.scene("title", function(el, d){
    applyWorld(); BGS.warp = 0; BGS.cheer = 0; setBg();
    baseTitle(el, d);
    var prop = "";
    if (SKIN === "tv-studio") prop = '<div class="abs qs-title-prop"><div class="qs-onair big">' + esc(T("onAirText", "ON AIR")) + '</div><div class="qs-applause on">' + esc(T("signText", "APPLAUSE")) + '</div></div>';
    else if (SKIN === "golden-bell") prop = '<div class="abs qs-title-prop qs-title-bell">' + bellInner(250) + '</div>';
    else prop = '<div class="abs qs-title-prop qs-plaque">' + esc(T("stationName", "")) + '</div>';
    el.insertAdjacentHTML("beforeend", hostHTML("qs-host-title") + prop + (T("hostName", "") ? '<div class="abs qs-nameplate">' + esc(T("hostName")) + '</div>' : ''));
    if (T("howto", "")) el.insertAdjacentHTML("beforeend", '<div class="subtitle enter qs-howto" style="animation-delay:1s">' + esc(T("howto")) + '</div>');
    var hc = hostCtl(el.querySelector(".qs-host-title"));
    hc.say(line("title"), "happy");
    if (SKIN === "golden-bell"){
      var tb = el.querySelector(".qs-title-bell");
      applyBell(tb, 0.9, false);
      (function loop(){ if (NG.sceneName !== "title" || !tb.parentNode) return; applyBell(tb, 0.9, true); NG.after(2800, loop); })();
    }
  });
  var baseResult = NG.scenes && NG.scenes.result;
  if (baseResult) NG.scene("result", function(el, d){
    BGS.warp = 0; BGS.cheer = 0.6;
    baseResult(el, d);
    el.insertAdjacentHTML("beforeend", hostHTML("qs-host-result"));
    hostCtl(el.querySelector(".qs-host-result")).mood("happy");
  });

  return {
    start: function(){ var p = GAME_LOGIC._pending; GAME_LOGIC._pending = null; start(p || null); },
    toText: function(){
      return { skin: SKIN, index: idx, total: items ? items.length : 0, locked: locked, question: cur ? cur.q : null, answer: cur ? cur.answer : null,
        isOX: cur ? !!cur._isOX : null, bonus: cur ? !!cur._bonus : null, powered: powered, results: results.slice(), teamHits: teamHits.slice(), retry: retry };
    }
  };
})();
