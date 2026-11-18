/* COMPONENT sort — drag-and-drop targets (works by touch): drag each card into the right bin; tap the card then a bin also works.
   items: [{q:"카드 글자", a:"정답 통 이름", exp?}]  spec: bins (optional order, 2-4; default = distinct a values) */
COMP.mech.sort = function(items){
  var bins = SPEC.bins && SPEC.bins.length ? SPEC.bins.slice(0, 4) : [], idx = -1, cur = null, locked = false, wrap = null, tries = 0, picked = null, ended = false;
  items.forEach(function(it){ if (bins.indexOf(it.a) < 0 && bins.length < 4) bins.push(it.a); });
  NG.state.total = items.length;

  function show(i){ idx = i; locked = false; tries = 0; NG.hud.setProgress(i / items.length); if (i >= items.length) return end(); cur = items[i]; NG.go("ts-sort"); }
  NG.scene("ts-sort", function(el){
    var bw = Math.floor((1600 - 28 * (bins.length - 1)) / bins.length);
    var html = '<div class="ts-wrap" style="top:140px;height:880px"><div class="ts-chips enter">' + H.chip("카드 " + (idx + 1) + " / " + items.length) + H.teamChip(NG.currentTeam()) + H.chip("끌어서 알맞은 통에 넣어요") + '</div>' +
      '<div style="position:relative;width:1600px;height:230px;margin-top:20px"><button class="ts-tile enter" id="ts-card" data-fit="1" style="left:480px;top:20px;width:640px;min-height:170px;font-size:' + H.qSize(cur.q) + 'px;padding:14px 24px;cursor:grab;touch-action:none">' + H.esc(cur.q) + '</button></div>' +
      '<div class="ts-bins" style="display:flex;gap:28px;margin-top:40px;width:1600px">';
    bins.forEach(function(b, i){ html += '<div class="card ts-bin" data-b="' + i + '" data-fit="1" style="width:' + bw + 'px;height:330px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:var(--t-c);font-weight:900;border-width:6px;background:var(--card);color:var(--cardText)">' + H.esc(b) + '</div>'; });
    html += '</div><div class="ts-expl"><div class="ts-expltext ts-note" id="ts-msg">&nbsp;</div></div></div>';
    el.insertAdjacentHTML("beforeend", html); wrap = el.lastElementChild;
    var card = wrap.querySelector("#ts-card"), binEls = wrap.querySelectorAll(".ts-bin");
    NG.drag(card, {
      onDrop: function(c){ for (var i = 0; i < binEls.length; i++) if (NG.hitTest(c, binEls[i])) return drop(i, card, binEls[i]); return false; },
      onTap: function(){ picked = !picked; card.classList.toggle("sel", picked); return false; }
    });
    Array.prototype.forEach.call(binEls, function(bn, i){ NG.button(bn, function(){ if (picked) { picked = false; card.classList.remove("sel"); drop(i, card, bn); } }); });
  });
  function drop(i, card, bin){
    if (locked) return false; tries++;
    var ok = bins[i] === cur.a;
    if (ok){
      locked = true; NG.snap(card, bin); bin.classList.add("done"); card.classList.add("done");
      NG.feedback(true, bin); H.award(tries === 1 ? 100 : 50, bin);
      wrap.querySelector("#ts-msg").textContent = "✔ " + (cur.exp || cur.q + " → " + cur.a);
      NG.after(1100, function(){ NG.nextTurn(); show(idx + 1); });
      return true;
    }
    NG.feedback(false, bin, { record: cur.q + " → " + cur.a, silentBadge: false, text: "다른 통이에요" });
    wrap.querySelector("#ts-msg").textContent = "✖ 다시 생각해 봐요";
    return false;
  }
  function end(){ if (ended) return; ended = true; H.finish({ total: items.length, ratio: items.length ? NG.state.correct / (NG.state.correct + NG.state.wrong) : 1, lines: ["카드 " + items.length + "장을 모두 넣었어요"] }); }
  return {
    start: function(){ NG.teacher.hooks = { skip: function(){ show(idx + 1); } }; show(0); },
    toText: function(){ return { mechanic: "sort", index: idx, total: items.length, bins: bins }; },
    auto: function(){
      if (locked || !wrap || NG.sceneName !== "ts-sort") return false;
      var card = wrap.querySelector("#ts-card"), binEls = wrap.querySelectorAll(".ts-bin"), right = bins.indexOf(cur.a);
      if (idx === 1 && tries === 0){ drop((right + 1) % bins.length, card, binEls[(right + 1) % bins.length]); return true; }
      drop(right, card, binEls[right]); return true;
    }
  };
};
