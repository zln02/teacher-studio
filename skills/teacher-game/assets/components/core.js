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
  el.insertAdjacentHTML("beforeend", '<div class="ts-wrap" style="top:' + top + 'px;height:' + (1020 - top) + 'px">' + chips + qhtml + body + '<div class="ts-expl"></div></div>');
  var wrap = el.lastElementChild, all = wrap.querySelectorAll(".choice");
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

/* background from the chosen theme (default derives everything from tokens) */
H.applyTheme = function(){
  var th = COMP.themes[TK.theme] || COMP.themes["default"];
  NG.bg.custom(function(ctx, t, dt, W, Hh){ th.paint(ctx, t, dt, W, Hh, TK); });
};
(function(){
  var orig = NG.setTheme;
  NG.setTheme = function(n, o){ orig(n, o); H.applyTheme(); };
})();

COMP.boot = function(){
  var factory = COMP.mech[SPEC.mechanic], inst = null;
  if (!factory) throw new Error("unknown mechanic: " + SPEC.mechanic);
  return {
    start: function(){ NG.teacher.hooks = {}; var list = COMP.pending || H.prepItems(); COMP.pending = null; inst = factory(list); inst.start(); },
    toText: function(){ return inst && inst.toText ? inst.toText() : {}; },
    auto: function(){ return inst && inst.auto ? inst.auto() : false; }
  };
};
