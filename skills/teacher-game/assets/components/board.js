/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* COMPONENT board — dice board game: roll, move along a snake path, quiz tiles ask a question (right = 1 extra step).
   items: quiz items (same as quiz). spec: tiles (default 24), maxTurns (turns per team, default 8) */
COMP.mech.board = function(items){
  var N = Math.max(12, Math.min(30, SPEC.tiles || 24)), cols = 8, pool = items.slice(), qi = -1, turns = 0, ended = false, asked = 0, rolling = false, bw = null, ctl = null, curItem = null, extra = false;
  var maxTurns = SPEC.maxTurns || 8, teams = NG.state.teams;
  var players = teams.length ? teams.map(function(t, i){ return { icon: t.icon, color: t.color, pos: 0, team: i }; }) : [{ icon: "🙂", color: "#888888", pos: 0, team: -1 }];
  var types = [];
  (function(){ for (var i = 0; i < N; i++){ types[i] = i === 0 ? "start" : (i === N - 1 ? "goal" : (i % 6 === 4 ? "star" : (i % 9 === 7 ? "back" : (i % 8 === 5 ? "gift" : "quiz")))); } })();
  var ICON = { start: "🏁", goal: "🏆", star: "⭐", back: "↩", gift: "🎁", quiz: "❓" };
  var LABEL = { start: "출발", goal: "도착", star: "+200", back: "-2칸", gift: "한 번 더", quiz: "" };
  function turnIdx(){ return NG.state.teams.length ? NG.state.turn : 0; }
  function nextQ(){ qi++; if (qi >= pool.length){ pool = U.shuffle(pool); qi = 0; } return pool[qi]; }
  function place(i){
    var r = Math.floor(i / cols), c = i % cols, x = 160 + (r % 2 ? cols - 1 - c : c) * 200, y = 300 + r * 200;
    var bv = H.lay().mech || "snake";
    if (bv === "wave") y += (c % 2 ? 26 : -10);
    if (bv === "stair") x += r * 56;
    return { x: x, y: y };
  }

  NG.scene("ts-board", function(el){
    el.insertAdjacentHTML("beforeend", '<div class="ts-center"></div>'); bw = el.lastElementChild; render();
  });
  function render(){
    if (!bw || NG.sceneName !== "ts-board") return;
    var p0 = players[turnIdx()], html = '<div class="ts-chips" style="position:absolute;left:0;width:1920px;top:128px">' + H.teamChip(NG.currentTeam()) + H.chip("🎲 " + (players.length > 1 ? p0.icon + " " : "") + "던질 차례") + '</div>';
    for (var i = 0; i < N; i++){
      var pt = place(i);
      html += '<div class="ts-tile" style="left:' + pt.x + 'px;top:' + pt.y + 'px;width:180px;height:170px;flex-direction:column;font-size:var(--t-s);cursor:default;line-height:1.2"><span style="font-size:56px">' + ICON[types[i]] + '</span><span>' + (LABEL[types[i]] || (i + 1)) + '</span>';
      players.filter(function(p){ return p.pos === i; }).forEach(function(p, k){ html += '<span class="ts-token" style="position:absolute;left:' + (8 + k * 42) + 'px;top:-30px;font-size:48px;filter:drop-shadow(0 3px 0 ' + p.color + ')">' + p.icon + '</span>'; });
      html += '</div>';
    }
    html += '<button class="btn pulse" id="ts-roll" style="position:absolute;left:660px;top:900px;width:600px;min-height:var(--btn-h)">🎲 주사위 굴리기</button><div id="ts-dice" class="ts-big" style="position:absolute;left:1420px;top:880px;width:140px;font-size:100px"></div>';
    bw.innerHTML = html; NG.button(bw.querySelector("#ts-roll"), roll);
  }
  function roll(){
    if (rolling || ended) return; rolling = true; var die = bw.querySelector("#ts-dice"), t = 0, v = 1 + Math.floor(Math.random() * 6);
    NG.sfx("drumroll", 400);
    (function spin(){ if (t++ < 8){ die.textContent = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][Math.floor(Math.random() * 6)]; NG.after(80, spin); } else { die.textContent = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][v - 1]; NG.fx.pop(die); NG.after(350, function(){ move(v); }); } })();
  }
  function tokenEl(){ return bw.querySelectorAll(".ts-token"); }
  function move(steps){
    var p = players[turnIdx()], dir = steps > 0 ? 1 : -1, left = Math.abs(steps);
    (function step(){
      if (left <= 0) return NG.after(300, land);
      p.pos = Math.max(0, Math.min(N - 1, p.pos + dir)); left--; NG.sfx("tick"); render();
      NG.after(260, step);
    })();
  }
  function land(){
    var p = players[turnIdx()], ty = types[p.pos];
    if (p.pos >= N - 1) return end(p);
    if (ty === "star"){ NG.addScore(200, p.team >= 0 ? p.team : null); NG.fx.badge("⭐ +200", "good", 900); NG.sfx("coin"); return after(); }
    if (ty === "gift"){ NG.fx.badge("🎁 한 번 더!", "info", 900); NG.sfx("powerup"); extra = true; return after(); }
    if (ty === "back"){ NG.fx.badge("↩ 2칸 뒤로", "info", 900); return NG.after(700, function(){ var l = 2; (function st(){ if (l-- <= 0 || p.pos <= 0) return NG.after(300, after); p.pos--; render(); NG.after(260, st); })(); }); }
    if (ty === "quiz"){ curItem = nextQ(); asked++; NG.state.total = asked; return NG.go("ts-bq"); }
    after();
  }
  NG.scene("ts-bq", function(el){
    ctl = H.ask(el, curItem, {
      index: asked - 1, total: Math.max(asked, items.length), team: NG.currentTeam(), top: 150, chips: H.chip("🎯 정답이면 1칸 더!"),
      nextLabel: "말판으로 ▶",
      onAnswer: function(ok, timeout, btn){ if (ok){ H.award(100, btn); } },
      onDone: function(ok){
        var p = players[turnIdx()];
        if (ok && p.pos < N - 1){ p.pos++; NG.go("ts-board"); NG.after(900, function(){ if (p.pos >= N - 1) end(p); else after(); }); }
        else after();
      }
    });
  });
  function after(){
    rolling = false; if (ended) return;
    if (!extra){ NG.nextTurn(); if (!NG.state.teams.length || NG.state.turn === 0) turns++; } else extra = false;
    NG.hud.setProgress(Math.max(turns / maxTurns, Math.max.apply(null, players.map(function(q){ return q.pos; })) / (N - 1)));
    if (turns >= maxTurns) return end(null);
    if (NG.sceneName === "ts-board") render(); else NG.go("ts-board");
  }
  function end(winner){
    if (ended) return; ended = true; rolling = false;
    var far = winner || players.slice().sort(function(a, b){ return b.pos - a.pos; })[0];
    if (winner && winner.team >= 0) NG.addScore(500, winner.team);
    H.finish({ title: winner ? "🏆 도착! " + far.icon : "게임 끝!", total: Math.max(asked, 1), ratio: asked ? NG.state.correct / asked : 0.5,
      lines: [winner ? "결승선에 가장 먼저 도착했어요!" : "가장 멀리 간 말: " + far.icon + " (" + (far.pos + 1) + "번 칸)"] });
  }
  return {
    start: function(){ NG.teacher.hooks = { skip: function(){ if (!rolling) after(); }, reveal: function(){ if (ctl && NG.sceneName === "ts-bq") ctl.force(); } }; NG.go("ts-board"); },
    toText: function(){ return { mechanic: "board", positions: players.map(function(p){ return p.pos; }), turns: turns, asked: asked }; },
    auto: function(){
      if (NG.sceneName === "ts-bq") return ctl ? ctl.auto(asked % 3 !== 0) : false;
      if (NG.sceneName === "ts-board" && bw && !rolling){ var b = bw.querySelector("#ts-roll"); if (b){ H.click(b); return true; } }
      return false;
    }
  };
};
