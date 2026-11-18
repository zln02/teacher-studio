/* COMPONENT quiz — multiple choice / OX, solo or team turns, timer, bonus rounds, retry-wrong.
   items: [{q, choices:[..2-4], answer, exp?} | {type:"ox", q, answer:0|1, exp?}] */
COMP.mech.quiz = function(items){
  var idx = -1, ctl = null, cur = null, retry = !!COMP.retry, bonusEvery = SPEC.bonusEvery == null ? 4 : SPEC.bonusEvery;
  COMP.retry = false;
  NG.state.total = items.length;

  function show(i){
    idx = i; NG.timer.stop();
    if (idx >= items.length) return H.finish({ total: items.length });
    cur = items[idx];
    cur._bonus = !retry && bonusEvery > 0 && (idx + 1) % bonusEvery === 0;
    NG.hud.setProgress(idx / items.length);
    NG.go("ts-q");
  }
  NG.scene("ts-q", function(el){
    ctl = H.ask(el, cur, {
      top: H.top(), index: idx, total: items.length, team: NG.currentTeam(), bonus: cur._bonus, timer: SPEC.timer || 0,
      nextLabel: idx + 1 >= items.length ? "결과 보기 ▶" : "다음 ▶",
      onAnswer: function(ok, timeout, btn){
        if (ok){
          var pts = 100 * (cur._bonus ? 2 : 1);
          if (!NG.state.teams.length && SPEC.timer && NG.timer.total) pts += Math.round(50 * (NG.timer.left / NG.timer.total));
          H.award(pts, btn);
        } else cur._wrong = true;
      },
      onDone: function(){ NG.nextTurn(); show(idx + 1); }
    });
    if (cur._bonus){ NG.fx.badge("보너스 문제!", "info", 1000); NG.sfx("powerup"); }
  });
  NG.retryWrong = function(){
    var wrong = items.filter(function(it){ return it._wrong; });
    if (!wrong.length) return;
    var teams = NG.state.teams.length;
    NG.state = { score: 0, combo: 0, maxCombo: 0, correct: 0, wrong: 0, total: 0, wrongList: [], teams: [], turn: 0, phase: "play" };
    NG.setupTeams(teams); COMP.retry = true; COMP.pending = wrong.map(function(w){ var c = {}; for (var k in w) c[k] = w[k]; c._wrong = false; return c; });
    NG.go("countdown");
  };
  return {
    start: function(){
      NG.teacher.hooks = { next: function(){ if (ctl && ctl.isLocked) { NG.nextTurn(); show(idx + 1); } }, skip: function(){ show(idx + 1); }, reveal: function(){ if (ctl) ctl.force(); } };
      show(0);
    },
    toText: function(){ return { mechanic: "quiz", index: idx, total: items.length, locked: !!(ctl && ctl.isLocked), question: cur ? cur.q : null }; },
    auto: function(){ return ctl ? ctl.auto(idx % 4 !== 1) : false; }
  };
};
