/* COMPONENT bingo — word bingo: a clue is called, tap the matching word on the grid. Lines give bonus points.
   items: [{word, clue, say?}]  needs >= grid*grid items.  spec: grid (3 or 4), world.speak (read word aloud), world.lang */
COMP.mech.bingo = function(items){
  var n = SPEC.grid === 3 ? 3 : 4, cells = items.slice(0, n * n), order, ci = -1, lines = 0, wrongTries = 0, busy = false, wrap = null, marked = [], ended = false;
  cells = U.shuffle(cells); order = U.shuffle(cells.slice());
  NG.state.total = cells.length;

  function lineCount(){
    var c = 0, i, j, r, k;
    for (i = 0; i < n; i++){ r = true; k = true; for (j = 0; j < n; j++){ if (!marked[i * n + j]) r = false; if (!marked[j * n + i]) k = false; } if (r) c++; if (k) c++; }
    var d1 = true, d2 = true; for (i = 0; i < n; i++){ if (!marked[i * n + i]) d1 = false; if (!marked[i * n + (n - 1 - i)]) d2 = false; }
    return c + (d1 ? 1 : 0) + (d2 ? 1 : 0);
  }
  function speak(it){
    if (!H.world("speak", false) || !window.speechSynthesis) return;
    try { var u = new SpeechSynthesisUtterance(it.say || it.word); u.lang = H.world("lang", "en-US"); u.rate = 0.9; window.speechSynthesis.speak(u); } catch (e) {}
  }
  NG.scene("ts-bingo", function(el){
    var cur = order[ci], gap = 20, areaW = 1500, cw = Math.floor((areaW - gap * (n - 1)) / n), chh = n === 3 ? 190 : 140;
    var html = '<div class="ts-wrap" style="top:130px;height:890px"><div class="ts-chips enter">' + H.chip("빙고 " + lines + "줄") + H.teamChip(NG.currentTeam()) + H.chip("남은 낱말 " + (order.length - ci)) + '</div>' +
      '<div class="card enter ts-q" data-fit="1" style="margin-top:16px;min-height:150px;font-size:' + H.qSize(cur.clue) + 'px">' + H.esc(cur.clue) + '</div>' +
      '<div style="position:relative;margin-top:22px;width:' + areaW + 'px;height:' + (n * chh + (n - 1) * gap) + 'px">';
    cells.forEach(function(c, i){
      html += '<button class="ts-tile' + (marked[i] ? " done" : "") + '" data-i="' + i + '" data-fit="1" style="left:' + (i % n) * (cw + gap) + 'px;top:' + Math.floor(i / n) * (chh + gap) + 'px;width:' + cw + 'px;height:' + chh + 'px;font-size:var(--t-c);padding:8px 14px">' + (marked[i] ? "✔ " : "") + H.esc(c.word) + '</button>';
    });
    el.insertAdjacentHTML("beforeend", html + '</div></div>'); wrap = el.lastElementChild;
    Array.prototype.forEach.call(wrap.querySelectorAll(".ts-tile"), function(b){ NG.button(b, function(){ pick(+b.getAttribute("data-i"), b); }); });
  });
  function next(){ ci++; wrongTries = 0; busy = false; NG.hud.setProgress(ci / order.length); if (ci >= order.length) return end(); NG.go("ts-bingo"); }
  function pick(i, b){
    if (busy || marked[i]) return; var cur = order[ci];
    if (cells[i] === cur){
      busy = true; marked[i] = true; b.classList.add("done"); b.textContent = "✔ " + cur.word; speak(cur);
      var before = lines; lines = lineCount();
      NG.feedback(true, b, { text: lines > before ? "빙고! " + lines + "줄" : null }); H.award(100 + (lines > before ? 200 * (lines - before) : 0), b);
      NG.after(900, function(){ NG.nextTurn(); next(); });
    } else {
      wrongTries++; NG.state.wrong++; NG.combo(false); NG.sfx("wrong"); NG.fx.wobble(b); NG.fx.badge("다시 찾아봐요", "bad", 700);
      if (wrongTries >= 2){
        busy = true; var right = wrap.querySelector('[data-i="' + cells.indexOf(cur) + '"]'); right.classList.add("sel"); NG.fx.pop(right);
        NG.state.wrongList.push(cur.clue + " → " + cur.word); NG.fx.toast("정답은 " + cur.word + " 이에요"); NG.after(1500, function(){ NG.nextTurn(); next(); });
      }
    }
  }
  function end(){
    if (ended) return; ended = true;
    H.finish({ title: lines ? "빙고 " + lines + "줄 완성!" : "게임 끝!", total: cells.length, ratio: Math.min(1, (NG.state.correct || 0) / cells.length), lines: ["낱말 " + marked.filter(Boolean).length + "개를 찾았어요"] });
  }
  return {
    start: function(){ NG.teacher.hooks = { skip: function(){ NG.nextTurn(); next(); } }; next(); },
    toText: function(){ return { mechanic: "bingo", called: ci, total: order.length, lines: lines }; },
    auto: function(){
      if (busy || !wrap || NG.sceneName !== "ts-bingo") return false;
      var cur = order[ci], right = cells.indexOf(cur), w = -1; for (var k = 0; k < cells.length; k++) if (!marked[k] && k !== right){ w = k; break; }
      if (ci === 1 && wrongTries === 0 && w >= 0) { H.click(wrap.querySelector('[data-i="' + w + '"]')); return true; }
      H.click(wrap.querySelector('[data-i="' + right + '"]')); return true;
    }
  };
};
