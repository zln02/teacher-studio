/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* KIT: quiz-show — 팀 퀴즈쇼 / 강당 종 울리기 / OX (객관식·OX 혼합)
   GAME.items = [{ type:"mc"|"ox", q:"문제", choices:["보기1",...], answer:0, exp:"해설" }]
   OX는 choices 생략 가능 (answer: 0=O, 1=X). 보너스: GAME.bonusEvery (기본 4문제마다 2배)
*/
window.GAME_LOGIC = (function(){
  var U = NG.util, G = window.GAME, items, idx, locked, cur, retry = false;
  var MARKS = ["A", "B", "C", "D", "E", "F"];

  function start(list){
    retry = !!list;
    items = list || U.shuffle(G.items || []);
    idx = -1; NG.state.total = items.length;
    NG.teacher.hooks = { next: next, skip: function(){ show(idx + 1); }, reveal: function(){ if (!locked) choose(-1, null, true); } };
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
    idx = i; locked = false; NG.timer.stop();
    if (idx >= items.length) return NG.finish({ total: items.length });
    cur = items[idx];
    var isOX = cur.type === "ox" || !cur.choices || !cur.choices.length;
    var choices = isOX ? ["O", "X"] : cur.choices;
    var bonus = !retry && (G.bonusEvery || 4) > 0 && (idx + 1) % (G.bonusEvery || 4) === 0;
    cur._bonus = bonus;
    NG.hud.setProgress(idx / items.length);
    var team = NG.currentTeam();
    NG.go("q", { choices: choices, isOX: isOX, bonus: bonus, team: team });
  }

  NG.scene("q", function(el, d){
    var qlen = cur.q.length, qsize = qlen > 60 ? 54 : (qlen > 36 ? 62 : 72);
    var html = '<div style="position:absolute;left:160px;top:184px;width:1600px;height:770px;display:flex;flex-direction:column;align-items:center">' +
      '<div class="row enter">' +
      '<div class="card" style="padding:10px 36px;font-size:40px;font-weight:900">문제 ' + (idx + 1) + ' / ' + items.length + '</div>' +
      (d.team && NG.state.teams.length > 1 ? '<div class="card" style="padding:10px 36px;font-size:40px;font-weight:900;border-color:' + d.team.color + '">' + d.team.icon + ' ' + U.esc(d.team.name) + ' 차례</div>' : '') +
      (d.bonus ? '<div class="card pulse" style="padding:10px 36px;font-size:40px;font-weight:900;background:var(--primary);color:var(--btnText)">⭐ 보너스 2배</div>' : '') +
      '</div>' +
      '<div class="card enter" id="qbox" style="margin-top:26px;width:1600px;min-height:190px;padding:30px 60px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:' + qsize + 'px;font-weight:900;line-height:1.3">' + U.esc(cur.q) + '</div>';
    if (d.isOX){
      html += '<div class="row" style="margin-top:34px">' +
        '<button class="choice enter" data-i="0" style="width:520px;height:300px;justify-content:center;font-size:230px;font-family:var(--font-display);color:var(--good)">O</button>' +
        '<button class="choice enter" data-i="1" style="width:520px;height:300px;justify-content:center;font-size:230px;font-family:var(--font-display);color:var(--bad);animation-delay:.08s">X</button></div>';
    } else {
      html += '<div style="margin-top:30px;width:1600px;display:grid;grid-template-columns:780px 780px;grid-gap:24px 40px">';
      d.choices.forEach(function(c, i){ html += '<button class="choice enter" data-i="' + i + '" style="animation-delay:' + (i * 0.07) + 's"><span class="mark">' + MARKS[i] + '</span><span>' + U.esc(c) + '</span></button>'; });
      html += '</div>';
    }
    html += '</div>';
    html += '<div id="expl" style="position:absolute;left:160px;bottom:26px;width:1600px"></div>';
    el.innerHTML = html;
    if (d.bonus){ NG.fx.badge("보너스 문제!", "info", 1000); NG.sfx("powerup"); }
    Array.prototype.forEach.call(el.querySelectorAll(".choice"), function(b){
      NG.button(b, function(){ choose(+b.getAttribute("data-i"), b); });
    });
    if (G.timer) NG.timer.start(G.timer, function(){ if (!locked){ NG.fx.toast("⏰ 시간 끝!"); choose(-1, null, true); } });
  });

  function choose(i, btn, timeout){
    if (locked) return; locked = true; NG.timer.stop();
    var all = document.querySelectorAll(".choice"), ans = cur.answer | 0, ok = i === ans;
    if (btn){ btn.style.outline = "8px solid #fff"; NG.fx.press(btn); }
    NG.sfx("drumroll", 520);
    Array.prototype.forEach.call(all, function(b){ if (b !== btn) b.classList.add("dim"); });
    NG.after(560, function(){
      Array.prototype.forEach.call(all, function(b){ b.classList.remove("dim"); var k = +b.getAttribute("data-i"); if (k === ans) b.classList.add("correct"); else if (k === i) b.classList.add("wrong"); else b.classList.add("dim"); });
      var rightBtn = all[ans];
      if (ok){
        var pts = 100 * (cur._bonus ? 2 : 1);
        if (!NG.state.teams.length && G.timer && NG.timer.total) pts += Math.round(50 * (NG.timer.left / NG.timer.total));
        NG.feedback(true, btn);
        NG.addScore(pts, null, U.center(btn));
      } else {
        cur._wrong = true;
        NG.feedback(false, btn || rightBtn, { text: timeout ? "시간 초과!" : null, record: cur.q + " → " + (cur.choices && cur.choices.length ? cur.choices[ans] : (ans === 0 ? "O" : "X")) });
        if (rightBtn) NG.after(400, function(){ NG.fx.pop(rightBtn); });
      }
      showExplain(ok);
    });
  }

  function showExplain(ok){
    var box = document.getElementById("expl"); if (!box) return;
    box.innerHTML = '<div class="card enter" style="display:flex;align-items:center;justify-content:space-between;padding:22px 36px">' +
      '<div style="font-size:38px;font-weight:700;line-height:1.35;flex:1;margin-right:30px">' + (ok ? "✅ " : "💡 ") + U.esc(cur.exp || "") + '</div>' +
      '<button class="btn small" id="nextBtn">다음 ▶</button></div>';
    NG.button(document.getElementById("nextBtn"), next);
  }

  function next(){ if (!locked) return; NG.nextTurn(); show(idx + 1); }

  return {
    start: function(){ var p = GAME_LOGIC._pending; GAME_LOGIC._pending = null; start(p || null); },
    toText: function(){ return { index: idx, total: items ? items.length : 0, locked: locked, question: cur ? cur.q : null, answer: cur ? cur.answer : null }; }
  };
})();
