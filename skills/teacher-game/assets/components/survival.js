/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* COMPONENT survival — OX survival by team: every team answers each question at once, wrong = lose a life,
   last team standing (or most lives at the end) wins. Solo play = one player with lives.
   items: [{q, answer:0|1, exp?}]   spec: lives (default 3) */
COMP.mech.survival = function(items){
  var lives0 = SPEC.lives || 3, idx = -1, picks = [], revealed = false, wrap = null, players, cur = null, ended = false;
  var teams = NG.state.teams;
  players = teams.length ? teams.map(function(t, i){ return { name: t.name, icon: t.icon, color: t.color, lives: lives0, team: i }; })
    : [{ name: "나", icon: "🙂", color: "#888888", lives: lives0, team: -1 }];
  NG.state.total = items.length;

  function alive(){ return players.filter(function(p){ return p.lives > 0; }); }
  function hearts(p){ var s = ""; for (var i = 0; i < lives0; i++) s += i < p.lives ? "❤️" : "🖤"; return s; }
  function show(i){
    idx = i; revealed = false; picks = []; NG.timer.stop();
    if (idx >= items.length || (players.length > 1 && alive().length <= 1) || !alive().length) return end();
    cur = items[idx]; NG.hud.setProgress(idx / items.length); NG.go("ts-surv");
  }
  NG.scene("ts-surv", function(el){
    var html = '<div class="ts-wrap" style="top:' + H.top() + 'px;height:' + (1020 - H.top()) + 'px"><div class="ts-chips enter">' + H.chip("문제 " + (idx + 1) + " / " + items.length) + H.chip("살아있는 팀 " + alive().length + " / " + players.length) + '</div>' +
      '<div class="card enter ts-q" data-fit="1" style="font-size:' + H.qSize(cur.q) + 'px">' + H.esc(cur.q) + '</div><div class="ts-teamrow">';
    players.forEach(function(p, i){
      html += '<div class="ts-teambox enter' + (p.lives <= 0 ? " out" : "") + '" data-p="' + i + '" style="border-color:' + p.color + '"><div class="nm">' + p.icon + " " + H.esc(p.name) + '</div><div class="ts-life">' + hearts(p) + '</div>' +
        (p.lives > 0 ? '<div class="ts-oxbtns"><button data-p="' + i + '" data-v="0">O</button><button data-p="' + i + '" data-v="1">X</button></div>' : '<div class="ts-note">탈락</div>') + '</div>';
    });
    html += '</div><div class="ts-expl"><div class="card ts-explcard" data-fit="1"><div class="ts-expltext" id="ts-hint">모둠이 의논해서 O 또는 X를 눌러요</div><button class="btn small ts-next" id="ts-rev">정답 공개 ▶</button></div></div></div>';
    el.insertAdjacentHTML("beforeend", html); wrap = el.lastElementChild;
    Array.prototype.forEach.call(wrap.querySelectorAll(".ts-oxbtns button"), function(b){
      NG.button(b, function(){
        if (revealed) return; var p = +b.getAttribute("data-p"); picks[p] = +b.getAttribute("data-v");
        Array.prototype.forEach.call(wrap.querySelectorAll('.ts-oxbtns button[data-p="' + p + '"]'), function(x){ x.classList.remove("pick"); });
        b.classList.add("pick");
      });
    });
    NG.button(wrap.querySelector("#ts-rev"), function(){ if (!revealed) reveal(); else show(idx + 1); });
    if (SPEC.timer) NG.timer.start(SPEC.timer, function(){ if (!revealed){ NG.fx.toast("⏰ 시간 끝!"); reveal(); } });
  });
  function reveal(){
    if (revealed) return; revealed = true; NG.timer.stop();
    var ans = cur.answer | 0, lost = [], kept = [];
    players.forEach(function(p, i){
      if (p.lives <= 0) return;
      var box = wrap.querySelector('.ts-teambox[data-p="' + i + '"]'), ok = picks[i] === ans;
      if (ok){ kept.push(p); if (p.team >= 0) NG.addScore(100, p.team, U.center(box)); else NG.addScore(100, null, U.center(box)); NG.state.correct++; box.insertAdjacentHTML("beforeend", '<div class="ts-note">✔ 정답</div>'); }
      else { p.lives--; lost.push(p); NG.state.wrong++; box.insertAdjacentHTML("beforeend", '<div class="ts-note">✖ 라이프 -1</div>'); NG.fx.wobble(box); box.querySelector(".ts-life").textContent = hearts(p); }
    });
    NG.sfx(lost.length ? "wrong" : "correct");
    if (kept.length) NG.fx.confetti();
    var hint = wrap.querySelector("#ts-hint");
    hint.textContent = "정답: " + (ans === 0 ? "O" : "X") + (cur.exp ? " — " + cur.exp : "");
    wrap.querySelector("#ts-rev").textContent = idx + 1 >= items.length || (players.length > 1 && alive().length <= 1) ? "결과 보기 ▶" : "다음 ▶";
    Array.prototype.forEach.call(wrap.querySelectorAll(".ts-oxbtns button"), function(b){ b.disabled = true; });
  }
  function end(){
    if (ended) return; ended = true;
    var best = Math.max.apply(null, players.map(function(p){ return p.lives; })), win = players.filter(function(p){ return p.lives === best && best > 0; });
    win.forEach(function(p){ if (p.team >= 0) NG.addScore(300, p.team); });
    var line = win.length ? "끝까지 살아남은 " + win.map(function(p){ return p.icon + " " + p.name; }).join(", ") + " (라이프 " + best + ")" : "모두 탈락! 다시 도전해 볼까요?";
    H.finish({ title: win.length ? "🏆 서바이벌 끝!" : "서바이벌 끝!", lines: [line], total: items.length, ratio: win.length ? 1 : 0.3 });
  }
  return {
    start: function(){
      NG.teacher.hooks = { next: function(){ if (revealed) show(idx + 1); }, skip: function(){ show(idx + 1); }, reveal: reveal };
      show(0);
    },
    toText: function(){ return { mechanic: "survival", index: idx, total: items.length, alive: alive().length, revealed: revealed }; },
    auto: function(){
      if (!wrap || NG.sceneName !== "ts-surv") return false;
      if (revealed){ H.click(wrap.querySelector("#ts-rev")); return true; }
      players.forEach(function(p, i){ if (p.lives > 0){ var v = (i === 0 ? (cur.answer | 0) : (idx % 2 ? (cur.answer | 0) : 1 - (cur.answer | 0))); H.click(wrap.querySelector('.ts-oxbtns button[data-p="' + i + '"][data-v="' + v + '"]')); } });
      H.click(wrap.querySelector("#ts-rev")); return true;
    }
  };
};
