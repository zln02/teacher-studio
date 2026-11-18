/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* COMPONENT escape — staged lock progression. Each item is one lock guarded by a question; wrong answers cost time
   (and the wrong choice is struck out, answer not revealed); all locks open before the clock ends = escape.
   items: [{q, choices|type:"ox", answer, clue?, exp?}]   spec: seconds (total time, default 60 per lock), penalty (sec, default 10) */
COMP.mech.escape = function(items){
  var idx = -1, ctl = null, cur = null, opened = [], clues = [], firstTry = 0, missed = false, ended = false;
  var total = items.length, penalty = SPEC.penalty == null ? 10 : SPEC.penalty, seconds = SPEC.seconds || total * 60;
  var lockName = H.world("lockName", "자물쇠");
  NG.state.total = total;

  function strip(){
    var h = '<div class="ts-lockstrip">';
    for (var i = 0; i < total; i++){
      var open = i < opened.length, now = i === idx && !open;
      h += '<div class="ts-lock' + (open ? " open" : "") + (now ? " now" : "") + '"><span class="ico">' + (open ? "🔓" : "🔒") + '</span><span>' + (i + 1) + '</span></div>';
    }
    return h + "</div>";
  }
  function show(i){
    idx = i; missed = false;
    if (idx >= total) return win();
    cur = items[idx]; NG.hud.setProgress(idx / total); NG.go("ts-esc");
  }
  NG.scene("ts-esc", function(el){
    el.insertAdjacentHTML("beforeend", strip());
    ctl = H.ask(el, cur, {
      index: idx, total: total, top: 330, noChips: true, retryOnWrong: true, keepTimer: true, nextLabel: idx + 1 >= total ? "문 열기 ▶" : "다음 자물쇠 ▶",
      onAnswer: function(ok, timeout, btn){
        if (!ok){ missed = true; NG.timer.left = Math.max(1, NG.timer.left - penalty); NG.fx.toast("⏰ -" + penalty + "초"); return; }
        if (!missed) firstTry++;
        opened.push(idx); if (cur.clue) clues.push(cur.clue);
        H.award(missed ? 50 : 100, btn); NG.sfx("coin");
        var locks = document.querySelectorAll(".ts-lock"); if (locks[idx]){ locks[idx].classList.add("open"); locks[idx].querySelector(".ico").textContent = "🔓"; NG.fx.pop(locks[idx]); }
      },
      onDone: function(ok){ NG.nextTurn(); show(idx + 1); }
    });
    var cl = cur.clue;
    if (cl && !cur._clueAdded){ cur._clueAdded = true; cur.exp = (cur.exp ? cur.exp + " · " : "") + "단서: " + cl; }
  });
  function win(){
    if (ended) return; ended = true; NG.timer.stop();
    var left = Math.max(0, Math.round(NG.timer.left || 0)); NG.addScore(left * 5);
    NG.sfx("fanfare");
    H.finish({ title: "🚪 탈출 성공!", ratio: firstTry / total, total: total,
      lines: ["남은 시간 " + left + "초" + (clues.length ? " · 얻은 단서: " + clues.join(" → ") : "")] });
  }
  function lose(){
    if (ended) return; ended = true;
    H.finish({ title: "⏰ 시간이 다 됐어요 — 다시 도전!", ratio: opened.length / total, total: total, lines: [lockName + " " + opened.length + "/" + total + "개를 열었어요"] });
  }
  return {
    start: function(){
      NG.teacher.hooks = { skip: function(){ show(idx + 1); }, reveal: function(){ if (ctl) ctl.force(); } };
      NG.timer.start(seconds, lose); show(0);
    },
    toText: function(){ return { mechanic: "escape", index: idx, opened: opened.length, total: total, seconds: Math.round(NG.timer.left || 0) }; },
    auto: function(){ return ctl ? ctl.auto(!(idx === 1 && !missed)) : false; }
  };
};
