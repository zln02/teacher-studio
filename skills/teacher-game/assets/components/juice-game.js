/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* ADAPTER juice-game - wires the shared Game Wow kit (shared/juice/juice.js) into the engine, so ALL mechanics get the same feel:
   correct = squash + hit-stop + particles + kick + 3-layer chime (pitch rises with the streak), wrong = one soft shake + icon + text,
   streak tiers 3/5/10, last-5s timer swell, tempo ramp before the last question, final reveal (drumroll -> decelerating number -> burst)
   and a team podium (3rd -> 2nd -> 1st). White-hat only: praise and progress, no loss messaging, no individual ranking of low scores.
   Runs last (after mechanic + theme), only wraps engine hooks, and does nothing when the kit is missing. */
(function(){
  var J = window.Juice; if (!J) return;
  var FX = NG.fx, P = J.params, lastEl = null, suppress = false, streakNow = false;
  J.configure({ sound: { master: 0.3 } });                       /* match the engine's own SFX/music bus balance (SFX about 2x music) */
  J.install({ camera: NG.el.scene });
  J.hooks.reduced = function(){ return !!(NG.reduceMotion || NG.calm); };
  J.hooks.muted = function(){ return !!(NG.audio && NG.audio.muted); };
  J.hooks.lite = function(){ return !!NG.lite; };
  var hs = FX.hitstop; J.hooks.hitstop = function(ms){ hs(ms); };
  function toClient(x, y){ var r = NG.el.stage.getBoundingClientRect(), s = NG.scale || 1; return { x: r.left + x * s, y: r.top + y * s }; }

  /* ---- fx primitives -> kit */
  var oBurst = FX.burst, oConfetti = FX.confetti, oBadge = FX.badge;
  FX.burst = function(x, y, o){
    o = o || {}; if (o.emoji) return oBurst.apply(FX, arguments);
    var c = toClient(x, y), n = Math.min(o.count || P.correct.burst.count, 24);
    J.burst(c.x, c.y, { count: n, scale: NG.scale || 1, shapes: o.shape ? [o.shape] : null, ms: P.correct.burst.ms });
  };
  FX.confetti = function(o){ if (suppress) return; if (J.reduced()) return oConfetti.apply(FX, arguments); J.confetti({ count: 60 }); };
  FX.flash = function(color, a){ if (color === "#ff0033") return; /* a wrong answer never gets a red flash */ J.flash(color, Math.min(a == null ? 0.1 : a, 0.12), 150); }; /* governed: <=2/s, faint */
  FX.shake = function(){ J.shakeEl(NG.el.scene, P.wrong.shakePx * 0.5, P.wrong.ms); };
  FX.wobble = function(el){ J.shakeEl(el, P.wrong.shakePx, P.wrong.ms); };
  FX.pop = function(el){ J.squash(el); };
  FX.press = function(el){ J.press(el); };
  FX.countUp = function(el, to, ms, suffix){ J.countUp(el, to, ms, { suffix: suffix }); };
  var SYM = /^[☀-➿\uD83C-\uD83E]/;
  FX.badge = function(text, kind, ms){ /* right/wrong is never colour alone: a symbol + words */
    var t = String(text == null ? "" : text);
    if (kind === "good" && !SYM.test(t)) t = "✔ " + t; else if (kind === "bad" && !SYM.test(t)) t = "✖ " + t;
    return oBadge.call(FX, t, kind, ms);
  };

  /* ---- sound: the engine's names -> kit presets (everything else keeps the engine's own synth) */
  var oSfx = NG.sfx, MAP = { tap: "click", select: "click", count: "tick", warn: "tickLast", pop: "pop", flip: "click", drumroll: "drumroll", fanfare: "fanfare", whoosh: "whoosh", go: "whoosh" };
  NG.sfx = function(name, arg){
    if (suppress && (name === "fanfare" || name === "lose" || name === "star")) return;
    if (name === "correct"){ if (!streakNow) J.sound.play("correct", { streak: (arg || 0) + 1 }); return; }
    if (name === "wrong"){ J.sound.play("wrong"); return; }
    if (name === "lose"){ J.sound.play("pop"); return; }          /* no sad trombone: a ending is never mocked */
    if (name === "star"){ J.sound.play("podium", { step: Math.min(2, arg || 0) }); return; }
    if (name === "powerup"){ return; }                            /* the streak tiers own this moment */
    if (name === "drumroll"){ J.sound.play("drumroll", { ms: Math.min(arg || 520, 900) }); return; }
    if (MAP[name]){ J.sound.play(MAP[name]); return; }
    return oSfx.apply(NG, arguments);
  };
  var oMute = NG.setMuted; NG.setMuted = function(m){ oMute(m); J.setMuted(m); };
  setTimeout(function(){ try { NG.unlockAudio(); } catch (e) {} J.warm(); }, 400); /* build audio + sounds while idle: the first tap is instant */
  if (navigator.webdriver) J.setMuted(true);                       /* automated checks stay silent */

  /* ---- streak tiers 3 / 5 / 10 (praise only; a miss simply resets quietly) */
  NG.combo = function(ok){
    var s = NG.state;
    if (ok){ s.combo++; s.maxCombo = Math.max(s.maxCombo, s.combo); } else s.combo = 0;
    NG.hud.render();
    streakNow = false;
    if (ok && J.tierOf(s.combo)){ streakNow = true; J.streak(s.combo, lastEl); }
    return s.combo;
  };
  var fb = NG.feedback;
  NG.feedback = function(ok, el){
    lastEl = el; var r = fb.apply(NG, arguments);
    if (ok && !J.reduced()) J.hitStop(); streakNow = false; return r;
  };

  /* ---- timer: gentle swell in the last 5 seconds; tempo ramp before the last question */
  var lastScene = "";
  NG.onUpdate(function(){
    if (NG.timer.running){ var tn = document.querySelector(".timer-num"); if (tn) J.timerPulse(tn, NG.timer.left); }
    var sn = NG.sceneName || "";
    if (sn !== lastScene){ lastScene = sn; if (sn === "countdown" && NG.music.setTempo) NG.music.setTempo(1); }
  });
  var sp = NG.hud.setProgress;
  NG.hud.setProgress = function(p){
    var n = NG.state.total || 0;
    if (n > 1 && p >= (n - 1) / n - 0.001 && p < 1 && NG.music.setTempo) NG.music.setTempo(1.25); /* the music quickens for the last question */
    return sp.apply(NG.hud, arguments);
  };

  /* ---- visible words on the mute button (the icon alone is not enough) */
  function labelMute(){
    var b = document.getElementById("ng-mute"); if (!b) return;
    var t = NG.audio && NG.audio.muted ? "소리 켜기" : "소리 끄기";
    if (b.getAttribute("aria-label") !== t){ b.setAttribute("aria-label", t); b.title = t + " (M)"; }
  }
  try { new MutationObserver(labelMute).observe(NG.el.hud, { childList: true, subtree: true }); } catch (e) {}
  labelMute();

  /* ---- start: a paper tear instead of the iris on some looks (variety by seed) */
  var oGo = NG.go, tearing = false;
  NG.go = function(name, data){
    if (name === "countdown" && NG.sceneName === "title" && !tearing && !J.reduced() && ((SPEC.design && SPEC.design.seed) | 0) % 3 === 0 && J.fx){
      tearing = true; var col = TK.colors.card || "#f4efe4";
      J.fx.paperTear({ color: col, onMid: function(){ tearing = false; oGo.call(NG, name, data); } });
      return;
    }
    return oGo.call(NG, name, data);
  };

  /* ---- result: tension then burst (solo) / podium 3rd -> 2nd -> 1st (teams) */
  var oResult = NG.scenes.result;
  NG.scene("result", function(el, d){
    suppress = !J.reduced(); oResult(el, d); NG.after(1400, function(){ suppress = false; });
    if (J.reduced()) return;
    var s = NG.state, skipCtl = null, host = null;
    function skip(e){ if (e && e.target && e.target.closest && e.target.closest("button")) return; if (skipCtl) skipCtl.skip(); }
    el.addEventListener("pointerdown", skip);
    var keySkip = function(e){ if (e.key === " " || e.key === "Enter") skip(); };
    window.addEventListener("keydown", keySkip);
    NG.after(9000, function(){ window.removeEventListener("keydown", keySkip); });
    if (s.teams.length > 1){
      var bars = el.querySelector(".bars"); if (!bars) return;
      var win = null; Array.prototype.forEach.call(el.querySelectorAll(".h2"), function(h){ if (/우승/.test(h.textContent)) win = h; });
      host = document.createElement("div"); host.className = "juice-podium-host"; bars.parentNode.replaceChild(host, bars);
      if (win) win.style.visibility = "hidden";
      host.innerHTML = '<div class="subtitle" style="font-size:44px">🥁 결과를 발표해요!</div>';
      J.sound.play("drumroll", { ms: P.reveal.minTensionMs });
      var live = true, t = NG.after(P.reveal.minTensionMs, function(){
        if (!live) return;
        skipCtl = J.podium(host, s.teams.map(function(x){ return { name: x.name, icon: x.icon, color: x.color, score: x.score }; }), {
          onDone: function(){ if (win) win.style.visibility = ""; if (J.fx){ J.fx.impactFrame(); var c1 = host.querySelector(".jp-col.r1 .jp-block"); if (c1) J.fx.dollyZoom(c1, host, { amount: 0.06 }); } }
        });
      });
      skipCtl = { skip: function(){ live = false; skipCtl = J.podium(host, s.teams.map(function(x){ return { name: x.name, icon: x.icon, color: x.color, score: x.score }; }), { onDone: function(){ if (win) win.style.visibility = ""; } }); skipCtl.skip(); } };
    } else {
      var scoreEl = el.querySelector("#r-score"), stars = el.querySelector(".stars"); if (!scoreEl) return;
      var total = d.total || s.total || (s.correct + s.wrong) || 1, ratio = d.ratio != null ? d.ratio : s.correct / total, to = d.score != null ? d.score : s.score;
      J.countUp(scoreEl, 0, 1, { from: 0 }); scoreEl.textContent = "0";   /* cancels the engine's quick count-up */
      if (stars) stars.style.visibility = "hidden";
      var n = ratio >= 0.9 ? 3 : (ratio >= 0.6 ? 2 : (ratio > 0 ? 1 : 0)), sps = stars ? stars.querySelectorAll("span") : [];
      skipCtl = J.reveal(scoreEl, to, { tensionMs: P.reveal.tensionMs, unit: "", celebrate: ratio >= 0.6, onDone: function(){
        if (stars){ stars.style.visibility = ""; Array.prototype.forEach.call(sps, function(x){ x.classList.remove("on"); }); }
        for (var i = 0; i < n; i++) (function(i){ NG.after(300 + i * 260, function(){ if (sps[i]) sps[i].classList.add("on"); J.sound.play("podium", { step: i }); var c = J.center(sps[i]); J.burst(c.x, c.y, { count: 12, shapes: ["star"] }); }); })(i);
        if (J.fx && ratio >= 0.6){ J.fx.impactFrame(); var h1 = el.querySelector(".h1"); if (h1) NG.after(500, function(){ J.fx.sketchWords(h1, { color: "var(--accent)" }); }); }
      } });
    }
  });
})();
