/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* COMPONENT match — memory-style pair matching: flip two cards, a matching pair stays open.
   items: [{a:"낱말", b:"짝(뜻·그림·바른 표기)"}]  3-8 pairs. Team turns rotate on a miss. */
COMP.mech.match = function(items){
  var pairs = items.slice(0, 8), cards = [], first = null, busy = false, tries = 0, found = 0, ended = false, wrap = null;
  NG.state.total = pairs.length;
  pairs.forEach(function(p, i){ cards.push({ pair: i, text: p.a }); cards.push({ pair: i, text: p.b }); });
  cards = U.shuffle(cards);
  var cols = cards.length <= 6 ? 3 : 4, rows = Math.ceil(cards.length / cols), gap = 24, areaW = 1600, areaH = 800;
  var cw = Math.floor((areaW - gap * (cols - 1)) / cols), ch = Math.min(220, Math.floor((areaH - gap * (rows - 1)) / rows));

  NG.scene("ts-match", function(el){
    var html = '<div class="ts-wrap" style="top:140px;height:880px"><div class="ts-chips enter">' + H.chip("짝 " + found + " / " + pairs.length) + H.teamChip(NG.currentTeam()) + H.chip("시도 " + tries) + '</div>' +
      '<div style="position:relative;width:' + areaW + 'px;height:' + (rows * ch + (rows - 1) * gap) + 'px;margin-top:26px">';
    cards.forEach(function(c, i){
      var x = (i % cols) * (cw + gap), y = Math.floor(i / cols) * (ch + gap);
      html += '<button class="ts-tile enter' + (c.done ? "" : " back") + '" data-i="' + i + '" data-fit="1" style="left:' + x + 'px;top:' + y + 'px;width:' + cw + 'px;height:' + ch + 'px;font-size:var(--t-b);padding:10px 16px;animation-delay:' + (i * 0.03) + 's">' + (c.done ? "✔ " + H.esc(c.text) : H.back()) + '</button>';
    });
    el.insertAdjacentHTML("beforeend", html + "</div></div>"); wrap = el.lastElementChild;
    Array.prototype.forEach.call(wrap.querySelectorAll(".ts-tile"), function(b){ NG.button(b, function(){ flip(+b.getAttribute("data-i"), b); }); });
  });
  function chips(){ var c = wrap.querySelector(".ts-chips"); if (c) c.innerHTML = H.chip("짝 " + found + " / " + pairs.length) + H.teamChip(NG.currentTeam()) + H.chip("시도 " + tries); }
  function flip(i, b){
    var c = cards[i]; if (busy || c.done || first === i) return;
    b.textContent = c.text; b.classList.remove("back"); b.classList.add("sel"); NG.sfx("flip");
    if (first === null){ first = i; return; }
    busy = true; tries++; var a = first, ab = wrap.querySelector('[data-i="' + a + '"]'); first = null;
    NG.after(750, function(){
      if (cards[a].pair === c.pair){
        cards[a].done = c.done = true; found++;
        [ab, b].forEach(function(x){ x.classList.remove("sel"); x.classList.add("done"); x.textContent = "✔ " + x.textContent; });
        NG.feedback(true, b, { text: H.world("goodText", "짝 맞춤!") }); H.award(100, b); NG.hud.setProgress(found / pairs.length);
        busy = false;
        if (found >= pairs.length) finish(); else chips();
      } else {
        NG.sfx("flip"); NG.fx.wobble(ab); NG.fx.wobble(b);
        NG.after(650, function(){ [ab, b].forEach(function(x){ x.classList.remove("sel"); x.classList.add("back"); x.innerHTML = H.back(); }); NG.nextTurn(); chips(); busy = false; });
      }
    });
  }
  function finish(){
    if (ended) return; ended = true;
    NG.after(600, function(){ H.finish({ title: "모두 찾았어요!", total: pairs.length, ratio: Math.min(1, pairs.length / Math.max(tries, 1) * 1.2), lines: ["시도 " + tries + "번 만에 " + pairs.length + "쌍을 찾았어요"] }); });
  }
  return {
    start: function(){ NG.teacher.hooks = { skip: function(){ finish(); } }; NG.go("ts-match"); },
    toText: function(){ return { mechanic: "match", found: found, total: pairs.length, tries: tries }; },
    auto: function(){
      if (busy || !wrap || NG.sceneName !== "ts-match") return false;
      for (var i = 0; i < cards.length; i++){
        if (cards[i].done) continue;
        for (var j = i + 1; j < cards.length; j++) if (cards[j].pair === cards[i].pair){
          if (tries === 0 && found === 0 && !SPEC._autoMissed){ SPEC._autoMissed = true; var k = 0; while (k < cards.length && (k === i || cards[k].pair === cards[i].pair)) k++; H.click(wrap.querySelector('[data-i="' + i + '"]')); H.click(wrap.querySelector('[data-i="' + k + '"]')); return true; }
          H.click(wrap.querySelector('[data-i="' + i + '"]')); H.click(wrap.querySelector('[data-i="' + j + '"]')); return true;
        }
      }
      return false;
    }
  };
};
