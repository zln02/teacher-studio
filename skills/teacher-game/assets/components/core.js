/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* COMPONENT core — shared runtime for spec-built games (rounds, question/answer flow, timer, reveal, finish).
   Uses only the engine API (NG.*). All sizes/colors come from tokens (CSS variables --t-*, --good ...).
   Mechanics register as COMP.mech.<name> = function(items){ return {start, toText, auto}; }  */
var COMP = { mech: {}, themes: {} };
var H = COMP.H = {};
var MARKS = ["A", "B", "C", "D"];

H.esc = function(s){ return U.esc(String(s == null ? "" : s)); };
H.say = function(s, vars){ var out = String(s || ""); for (var k in vars) out = out.split("{" + k + "}").join(vars[k]); return out; };
H.world = function(k, d){ var w = SPEC.world || {}; return (w[k] === undefined || w[k] === null) ? d : w[k]; };
H.qSize = function(text){
  var n = String(text).length, base = TK.type.question, f = n > 70 ? 0.86 : (n > 44 ? 0.93 : 1);
  return Math.max(TK.type.floor.question, Math.round(base * f));
};
H.click = function(el){ if (!el) return; el.dispatchEvent(new Event("pointerdown", { bubbles: true })); el.click(); };

/* items: shuffle (seeded by Math.random: fine for play) and cut to rounds */
H.prepItems = function(){
  var list = (G.items || []).map(function(x){ var c = {}; for (var k in x) c[k] = x[k]; return c; });
  if (SPEC.shuffle !== false) list = U.shuffle(list);
  if (SPEC.rounds && SPEC.rounds > 0) list = list.slice(0, SPEC.rounds);
  return list;
};

/* normalise a question item to {isOX, choices, answer} */
H.norm = function(it){
  var isOX = it.type === "ox" || !it.choices || !it.choices.length;
  return { isOX: isOX, choices: isOX ? ["O", "X"] : it.choices, answer: it.answer | 0 };
};

/* themed card back (match): emblem on a patterned colour card; plain "?" only when no emblem exists */
H.back = function(){
  var e = COMP.emblem || '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="' + TK.colors.accent + '" stroke="#1a1030" stroke-width="1.2"/><path d="M12 5 L14 10 L19 10.4 L15.2 13.6 L16.4 18.6 L12 16 L7.6 18.6 L8.8 13.6 L5 10.4 L10 10Z" fill="#fff"/></svg>';
  return '<span class="ts-emblem">' + e + '</span>';
};
H.top = function(){ return SPEC.timer ? 200 : 150; };  /* leave room for the engine timer bar */
H.chip = function(text, extra){ return '<div class="card ts-chip' + (extra || "") + '">' + text + '</div>'; };

/* scoring: team turn aware */
H.award = function(points, el){ NG.addScore(points, null, el ? U.center(el) : null); };
H.teamChip = function(team){
  if (!team || NG.state.teams.length < 2) return "";
  return '<div class="card ts-chip" style="border-color:' + team.color + '">' + team.icon + " " + H.esc(team.name) + " 차례</div>";
};

/* ---- the shared question/answer flow ----
   o: {index,total,team,bonus,top,height,chips,onAnswer(ok,timeout),onDone(),nextLabel,showNext}
   returns {locked(), force()} */
H.ask = function(el, it, o){
  o = o || {};
  var n = H.norm(it), locked = false, ctl = {};
  var chips = o.noChips ? '' : '<div class="ts-chips enter">' + H.chip(H.world("qLabel", "문제") + " " + (o.index + 1) + " / " + o.total) + H.teamChip(o.team) +
    (o.bonus ? H.chip("⭐ 보너스 2배", " pulse ts-bonus") : "") + (o.chips || "") + '</div>';
  var qhtml = '<div class="card enter ts-q" data-fit="1" style="font-size:' + H.qSize(it.q) + 'px">' + H.esc(it.q) + '</div>';
  var body = "";
  if (n.isOX){
    body = '<div class="ts-oxrow">' +
      '<button class="choice enter ts-ox" data-i="0" style="color:var(--good)">O</button>' +
      '<button class="choice enter ts-ox" data-i="1" style="color:var(--bad);animation-delay:.08s">X</button></div>';
  } else {
    body = '<div class="ts-grid c' + n.choices.length + '">';
    n.choices.forEach(function(c, i){ body += '<button class="choice enter ts-choice" data-fit="1" data-i="' + i + '" style="animation-delay:' + (i * 0.07) + 's"><span class="mark">' + MARKS[i] + '</span><span>' + H.esc(c) + '</span></button>'; });
    body += '</div>';
  }
  var top = o.top == null ? 150 : o.top;
  el.insertAdjacentHTML("beforeend", '<div class="ts-wrap ts-ask" style="top:' + top + 'px;height:' + (1020 - top) + 'px">' + chips + qhtml + body + '<div class="ts-expl"></div></div>');
  var wrap = el.lastElementChild, all = wrap.querySelectorAll(".choice");
  /* a question that does not fit its box in a composed layout: step the font down to the type floor (the box never grows over the answers) */
  var qel = wrap.querySelector(".ts-q");
  if (qel && document.body.getAttribute("data-layout")){
    var qf = parseFloat(getComputedStyle(qel).fontSize), qmin = (TK.type.floor && TK.type.floor.question) || 40, qg = 0;
    while (qel.scrollHeight > qel.clientHeight + 2 && qf > qmin && qg++ < 14){ qf -= 2; qel.style.fontSize = qf + "px"; }
  }
  /* answers that do not fit their (rounded) button: step the font down (never below the 34px floor) until the text clears the shape */
  Array.prototype.forEach.call(wrap.querySelectorAll(".ts-choice"), function(b){
    var fs = parseFloat(getComputedStyle(b).fontSize), cr = parseFloat(getComputedStyle(b).borderTopLeftRadius) || 0;
    function tight(){ var r = b.getBoundingClientRect(), sc = b.offsetWidth ? r.width / b.offsetWidth : 1, inner = b.lastElementChild; if (!inner) return false;
      var q = inner.getBoundingClientRect(), pad = 26 * sc + Math.min(cr * sc, r.height / 2) * 0.28; return q.height > r.height - 2 * pad || q.width > r.width - 2 * pad || b.scrollHeight > b.clientHeight + 2; }
    var guard = 0; while (tight() && fs > 34 && guard++ < 12){ fs -= 2; b.style.fontSize = fs + "px"; }
  });
  function rightText(){ return n.isOX ? (n.answer === 0 ? "O" : "X") : MARKS[n.answer] + ". " + n.choices[n.answer]; }
  function choose(i, btn, timeout){
    if (locked) return;
    var ok = i === n.answer;
    if (!ok && o.retryOnWrong && btn && !timeout){
      btn.classList.add("wrong"); btn.disabled = true; btn.insertAdjacentHTML("beforeend", '<span class="ts-sym">✖</span>');
      NG.feedback(false, btn, { record: it.q + " → " + rightText() });
      if (o.onAnswer) o.onAnswer(false, false, btn);
      return;
    }
    locked = true; ctl.isLocked = true; if (!o.keepTimer) NG.timer.stop();
    if (btn){ btn.style.outline = "8px solid var(--text)"; NG.fx.press(btn); }
    NG.sfx("drumroll", 520);
    Array.prototype.forEach.call(all, function(b){ if (b !== btn) b.classList.add("dim"); });
    NG.after(520, function(){
      Array.prototype.forEach.call(all, function(b){
        b.classList.remove("dim"); var k = +b.getAttribute("data-i");
        if (k === n.answer){ b.classList.add("correct"); if (!b.querySelector(".ts-sym")) b.insertAdjacentHTML("beforeend", '<span class="ts-sym">✔</span>'); }
        else if (k === i){ b.classList.add("wrong"); b.insertAdjacentHTML("beforeend", '<span class="ts-sym">✖</span>'); }
        else b.classList.add("dim");
      });
      NG.feedback(ok, btn || all[n.answer], { text: timeout ? "시간 초과!" : null, record: it.q + " → " + rightText() });
      if (!ok && all[n.answer]) NG.after(400, function(){ NG.fx.pop(all[n.answer]); });
      if (o.onAnswer) o.onAnswer(ok, timeout, btn || all[n.answer]);
      var expl = wrap.querySelector(".ts-expl");
      expl.innerHTML = '<div class="card enter ts-explcard" data-fit="1"><div class="ts-expltext">' + (ok ? "✅ " : "💡 ") + "정답: " + H.esc(rightText()) +
        (it.exp ? " — " + H.esc(it.exp) : "") + '</div>' + (o.showNext === false ? "" : '<button class="btn small ts-next">' + H.esc(o.nextLabel || "다음 ▶") + '</button>') + '</div>';
      var nb = expl.querySelector(".ts-next");
      if (nb) NG.button(nb, function(){ if (o.onDone) o.onDone(ok); });
      else if (o.onDone) NG.after(1500, function(){ o.onDone(ok); });
    });
  }
  Array.prototype.forEach.call(all, function(b){ NG.button(b, function(){ choose(+b.getAttribute("data-i"), b); }); });
  if (o.timer) NG.timer.start(o.timer, function(){ if (!locked){ NG.fx.toast("⏰ 시간 끝!"); choose(-1, null, true); } });
  ctl.force = function(){ if (!locked) choose(-1, null, false); };
  ctl.auto = function(wantRight){
    if (!locked){ var i = wantRight ? n.answer : (n.answer + 1) % n.choices.length; H.click(all[i]); return true; }
    var nb = wrap.querySelector(".ts-next"); if (nb){ H.click(nb); return true; }
    return false;
  };
  ctl.isLocked = false;
  return ctl;
};

/* end of game: one place for the result card */
H.finish = function(extra){
  var s = NG.state, d = extra || {};
  if (d.total == null) d.total = s.total || (s.correct + s.wrong) || 1;
  NG.hud.setProgress(1);
  NG.finish(d);
};

/* ---- theme runtime ----
   A theme is COMP.themes[id] = { paint(ctx,t,dt,W,H,TK,S), host:{svg(TK),name,lines:{title,start,correct,wrong,win,lose}},
   deco(TK)->html, sfx(), onReact(kind,S,TK), celebrate(S,TK) }. The metadata (palette, fonts, moods) lives in <id>.json.
   S = COMP.S is the shared show state: progress 0..1 (from NG.hud.setProgress), cheer/miss pulses (decay to 0),
   misses (count), win (0/1 after the game ends). Every mechanic feeds it, so any theme works with any mechanic. */
var S = COMP.S = { progress: 0, cheer: 0, miss: 0, misses: 0, win: 0, lose: 0, scene: "title" };
H.theme = function(){ return COMP.themes[TK.theme] || COMP.themes["default"]; };
H.lines = function(kind){ var h = H.theme().host, l = h && h.lines && h.lines[kind]; return l && l.length ? U.pick(l) : ""; };
H.hostEl = function(){ return document.querySelector("#ts-deco .ts-host"); };
H.mood = function(m){ var e = H.hostEl(); if (e) e.setAttribute("data-mood", m || "idle"); };
H.sayHost = function(text, ms){
  var b = document.getElementById("ts-bubble"); if (!b) return;
  if (!text){ b.className = "empty"; return; }
  b.firstChild.textContent = text; b.className = ""; NG.fx.pop(b);
  if (H._bt) NG.cancel(H._bt);
  H._bt = NG.after(ms || 2400, function(){ b.className = "empty"; });
};
H.react = function(kind){
  var th = H.theme(), e = H.hostEl();
  if (kind === "correct"){ S.cheer = 1; } else if (kind === "wrong"){ S.miss = 1; S.misses++; }
  else if (kind === "win"){ S.win = 1; S.cheer = 1; } else if (kind === "lose"){ S.lose = 1; S.miss = 1; }
  var mood = { correct: "happy", win: "happy", wrong: "sad", lose: "sad", start: "wow" }[kind] || "idle";
  if (e){
    H.mood(mood); e.classList.remove("hop"); void e.offsetWidth; e.classList.add("hop");
    NG.after(1900, function(){ if (!S.win && !S.lose) H.mood("idle"); e.classList.remove("hop"); });
  }
  if (kind !== "title") H.sayHost(H.lines(kind), kind === "win" || kind === "lose" ? 6000 : 2400);
  if (th.onReact) th.onReact(kind, S, TK);
};
H.mountLayer = function(){
  var stage = document.getElementById("stage"), th = H.theme(); if (!stage) return;
  var old = document.getElementById("ts-deco"); if (old) old.parentNode.removeChild(old);
  old = document.getElementById("ts-bubble"); if (old) old.parentNode.removeChild(old);
  var d = document.createElement("div"); d.id = "ts-deco"; d.setAttribute("data-scene", "title");
  d.innerHTML = (th.deco ? th.deco(TK) : "") + (th.host ? '<div class="ts-host" data-mood="idle"><div class="ts-bob">' + th.host.svg(TK) + "</div></div>" : "");
  stage.insertBefore(d, document.getElementById("scene"));
  if (th.host){
    var b = document.createElement("div"); b.id = "ts-bubble"; b.className = "empty"; b.innerHTML = "<span></span>"; stage.appendChild(b);
  }
  if (th.sfx) th.sfx();
  /* optional staging parts: wide host column, team podium row */
  var col = th.host && (th.hostCol || (SPEC.design && SPEC.design.hostCol)) && ["quiz", "survival", "escape"].indexOf(SPEC.mechanic) >= 0 && SPEC.device === "board";
  document.body.setAttribute("data-hostcol", col ? "1" : "");
  if (th.podiums || (SPEC.design && SPEC.design.podiums)){
    var pd = document.createElement("div"); pd.className = "ts-podiums"; d.appendChild(pd); H.podiumEl = pd; S.hits = [];
  } else H.podiumEl = null;
  if (th.sfx) th.sfx();
  if (SPEC.customSvg){ var cu = document.createElement("div"); cu.className = "ts-custom"; cu.innerHTML = SPEC.customSvg; d.appendChild(cu); }
  H.applyLayout();
};
H.updatePodiums = function(){
  var pd = H.podiumEl; if (!pd) return;
  var t = NG.state.teams, n = t.length, key = n + ":" + NG.state.turn + ":" + (S.hits || []).join(",");
  if (pd._key === key) return; pd._key = key;
  var list = n ? t : [{ name: "도전자", icon: "🎤", color: TK.colors.primary }], cap = Math.max(3, Math.min(10, Math.ceil((NG.state.total || 8) / list.length))), h = "";
  list.forEach(function(tm, i){
    var hits = (S.hits && S.hits[i]) || 0, lamps = "";
    for (var k = 0; k < cap; k++) lamps += '<i class="' + (k < hits ? "lit" : "") + '"></i>';
    h += '<div class="ts-pod' + (n && NG.state.turn === i ? " on" : "") + '" style="--tc:' + tm.color + '"><b>' + H.esc(tm.icon) + " " + H.esc(tm.name) + '</b><span class="ts-lamps">' + lamps + "</span></div>";
  });
  pd.innerHTML = h;
};
/* layout + component variants (scripts/layout_auto.py -> SPEC.layoutCfg): body[data-*] attributes read by assets/layouts/layouts.css */
H.lay = function(){ return SPEC.layoutCfg || {}; };
H.applyLayout = function(){
  var c = H.lay(), b = document.body; if (!b) return;
  function set(k, v){ if (v && v !== "default" && v !== "center" && v !== "md") b.setAttribute(k, v); else b.removeAttribute(k); }
  set("data-layout", c.layout === "stack" ? "" : c.layout); set("data-ans", c.ans); set("data-choice", c.choice); set("data-card", c.card); set("data-score", c.score);
  set("data-title", c.title); set("data-title-scale", c.titleScale); set("data-tpos", c.tpos);
  b.setAttribute("data-mech", SPEC.mechanic); set("data-style", c.css);
  set("data-lockpos", SPEC.mechanic === "escape" && c.mech === "side" && b.getAttribute("data-hostcol") !== "1" ? "side" : "");
  set("data-sv", SPEC.mechanic === "survival" ? c.mech : ""); set("data-sortv", SPEC.mechanic === "sort" ? c.mech : "");
};
H.applyTheme = function(){
  var th = H.theme();
  try { document.body.setAttribute("data-world", TK.theme); } catch (e) {}
  if (!H._advWrapped && window.advanceTime){  /* test hook advanceTime() runs many virtual frames: skip the (costly) scenery paint inside it */
    H._advWrapped = true; var adv = window.advanceTime;
    window.advanceTime = function(ms){ S.fast = true; try { return adv.apply(window, arguments); } finally { S.fast = false; } };
  }
  NG.bg.custom(function(ctx, t, dt, W, Hh){ if (S.fast) return; th.paint(ctx, t, dt, W, Hh, TK, S); });
  H.mountLayer();
};
(function(){
  var orig = NG.setTheme;
  NG.setTheme = function(n, o){ orig(n, o); H.applyTheme(); };
  var fb = NG.feedback;
  NG.feedback = function(ok){
    if (ok){ var ti = NG.state.teams.length ? NG.state.turn : 0; S.hits = S.hits || []; S.hits[ti] = (S.hits[ti] || 0) + 1; }
    var r = fb.apply(NG, arguments); H.react(ok ? "correct" : "wrong"); return r;
  };
  var fin = NG.finish;
  NG.finish = function(d){
    var ok = d && d.ratio != null ? d.ratio >= 0.5 : (NG.state.correct >= NG.state.wrong);
    H.react(ok ? "win" : "lose"); return fin.apply(NG, arguments);
  };
  var sp = NG.hud.setProgress;
  NG.hud.setProgress = function(p){ S.progress = p; return sp.apply(NG.hud, arguments); };
  var last = "";
  NG.onUpdate(function(dt){
    H.updatePodiums();
    S.cheer = Math.max(0, S.cheer - dt * 0.42); S.miss = Math.max(0, S.miss - dt * 0.5);
    var sn = NG.sceneName || "";
    if (sn !== last){
      last = sn; var d = document.getElementById("ts-deco"); if (d) d.setAttribute("data-scene", sn);
      document.body.setAttribute("data-scene", sn);
      if (sn === "title" || sn === "countdown"){ S.win = 0; S.lose = 0; S.progress = 0; S.misses = 0; S.hits = []; H.mood("idle"); H.sayHost(""); }
      if (sn === "title" && H.theme().host) NG.after(500, function(){ H.sayHost(H.lines("title"), 4000); });
    }
  });
})();

COMP.boot = function(){
  var factory = COMP.mech[SPEC.mechanic], inst = null;
  if (!factory) throw new Error("unknown mechanic: " + SPEC.mechanic);
  return {
    start: function(){ S.progress = 0; S.misses = 0; S.win = 0; S.lose = 0; H.react("start"); NG.teacher.hooks = {}; var list = COMP.pending || H.prepItems(); COMP.pending = null; inst = factory(list); inst.start(); },
    toText: function(){ return inst && inst.toText ? inst.toText() : {}; },
    auto: function(){ return inst && inst.auto ? inst.auto() : false; }
  };
};
