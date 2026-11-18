/* EXAMPLE: 등대지기의 밤바다 — 정답 섬으로 점프하는 횡스크롤 게임 (퀴즈쇼와 다른 세계관·동작·배치 예시)
   세계관: 밤바다의 등대지기 갈매기 / 동작: 다가오는 섬 중 정답 섬을 눌러 점프 / 배치: 횡스크롤 바다
   시그니처: 정답마다 등대의 창이 하나씩 켜지고, 다 켜지면 빛줄기가 바다를 비추며 불꽃
   GAME.items: quiz-show와 같은 형식 (mc / ox)
*/
window.GAME_LOGIC = (function(){
  var U = NG.util, G = window.GAME, items, idx = -1, cur, locked = false, lit = 0, islands = [], bird, birdLane = 1;
  var LANES_4 = [440, 600, 760, 920], LANES_2 = [560, 840];
  var SPEED = 150;

  /* ---- custom night-sea background with the lighthouse that lights up ---- */
  var stars = []; for (var i = 0; i < 90; i++) stars.push({x:Math.random() * 1920, y:Math.random() * 420, s:Math.random() * 2 + 1, p:Math.random() * 6});
  function paint(c, t, dt, W, H){
    var sky = c.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#050b24"); sky.addColorStop(0.55, "#112a5c"); sky.addColorStop(1, "#0b3d6b"); c.fillStyle = sky; c.fillRect(0, 0, W, H);
    stars.forEach(function(s){ c.globalAlpha = 0.4 + 0.6 * Math.abs(Math.sin(t * 1.5 + s.p)); c.fillStyle = "#fff"; c.fillRect(s.x, s.y, s.s, s.s); }); c.globalAlpha = 1;
    c.fillStyle = "#fff6d5"; c.beginPath(); c.arc(260, 150, 54, 0, 6.28); c.fill(); c.fillStyle = "#112a5c"; c.beginPath(); c.arc(284, 136, 50, 0, 6.28); c.fill();
    var total = items ? items.length : 10, ratio = total ? lit / total : 0;
    // lighthouse on the far right rock
    c.fillStyle = "#1a2b45"; c.beginPath(); c.moveTo(1560, 380); c.lineTo(1880, 380); c.lineTo(1920, 470); c.lineTo(1520, 470); c.fill();
    c.fillStyle = "#e9edf5"; c.beginPath(); c.moveTo(1660, 380); c.lineTo(1780, 380); c.lineTo(1755, 120); c.lineTo(1685, 120); c.fill();
    c.fillStyle = "#d64545"; for (var k = 0; k < 3; k++){ c.fillRect(1668 + k * 4, 180 + k * 80, 104 - k * 8, 26); }
    var wins = Math.min(total, 10);
    for (k = 0; k < wins; k++){ var on = k < Math.round(ratio * wins); c.fillStyle = on ? "#ffd84d" : "#3a4660"; c.fillRect(1700 + (k % 2) * 26, 360 - Math.floor(k / 2) * 46, 16, 22); }
    c.fillStyle = "#2b3a55"; c.fillRect(1675, 92, 90, 30); c.fillStyle = ratio >= 1 ? "#fff3a0" : (lit ? "#ffd84d" : "#55607a"); c.fillRect(1690, 60, 60, 34);
    if (lit){ c.save(); c.translate(1720, 77); c.rotate(Math.sin(t * 0.8) * 0.5 - 2.7); var beam = c.createLinearGradient(0, 0, 900, 0); beam.addColorStop(0, "rgba(255,240,160," + (0.25 + 0.4 * ratio) + ")"); beam.addColorStop(1, "rgba(255,240,160,0)"); c.fillStyle = beam; c.beginPath(); c.moveTo(0, 0); c.lineTo(1100, -120 - 200 * ratio); c.lineTo(1100, 120 + 200 * ratio); c.fill(); c.restore(); }
    for (k = 0; k < 4; k++){ var wy = 470 + k * 150; c.fillStyle = "rgba(120,190,255," + (0.08 + k * 0.05) + ")"; c.beginPath(); c.moveTo(0, H); for (var x = 0; x <= W; x += 40) c.lineTo(x, wy + Math.sin(x / 120 + t * (1.2 + k * 0.4) + k) * 12); c.lineTo(W, H); c.fill(); }
  }

  function birdSvg(){
    return '<svg viewBox="0 0 200 160" width="190" height="152" class="ng-char"><ellipse cx="100" cy="150" rx="60" ry="8" fill="rgba(0,0,0,.3)"/>' +
      '<g class="rig"><path class="wing" d="M70 80 q-60 -40 -60 10 q30 -5 60 10z" fill="#dfe7f2" stroke="#7d8aa3" stroke-width="6"/>' +
      '<ellipse cx="100" cy="90" rx="58" ry="46" fill="#ffffff" stroke="#7d8aa3" stroke-width="7"/>' +
      '<path d="M150 82 l34 10 -34 12z" fill="#ffb02e" stroke="#c77700" stroke-width="5" stroke-linejoin="round"/>' +
      '<circle cx="128" cy="76" r="9" fill="#1b1b2f"/><circle cx="131" cy="73" r="3" fill="#fff"/>' +
      '<path d="M60 40 h70 l-8 -24 h-54z" fill="#1f3c88" stroke="#0e1f4d" stroke-width="5"/><rect x="54" y="38" width="82" height="10" rx="5" fill="#0e1f4d"/>' +
      '<circle cx="96" cy="26" r="6" fill="#ffd84d"/></g></svg>';
  }

  NG.scene("title", function(el){
    NG.state.phase = "title"; NG.hud.show = false; NG.hud.render(); NG.timer.stop(); NG.bg.custom(paint);
    el.innerHTML = '<div style="position:absolute;left:150px;top:230px;width:1250px;text-align:center">' +
      '<div class="subtitle enter">' + U.esc(G.subtitle || "") + '</div>' +
      '<div class="title shine" style="font-size:140px;margin-top:18px">' + U.esc(G.title) + '</div>' +
      '<div class="subtitle enter" style="margin-top:22px;font-size:40px">정답 섬을 눌러 갈매기를 점프시키고 등대에 불을 켜 주세요!</div>' +
      '<div class="row enter" id="t-teams" style="margin-top:40px"></div>' +
      '<button class="btn pulse enter" id="t-start" style="margin-top:36px">⛵ 출항!</button></div>';
    var b = U.h("div", {class:"mascot"}, birdSvg()); b.style.left = "560px"; b.style.top = "780px"; el.appendChild(b);
    NG.after(700, function(){ NG.anim(b, [{transform:"translateY(0)"}, {transform:"translateY(-80px)"}, {transform:"translateY(0)"}], {duration:600, iterations:2, easing:"cubic-bezier(.33,1.4,.6,1)"}); });
    var teams = G.teams || 0, box = el.querySelector("#t-teams");
    [0, 2, 3, 4].forEach(function(n){ var btn = U.h("button", {class:"btn small " + (n === teams ? "" : "secondary")}, n === 0 ? "혼자" : n + "모둠"); NG.button(btn, function(){ teams = n; Array.prototype.forEach.call(box.children, function(c){ c.classList.add("secondary"); }); btn.classList.remove("secondary"); NG.fx.pop(btn); }); box.appendChild(btn); });
    NG.button(el.querySelector("#t-start"), function(){ NG.unlockAudio(); NG.setupTeams(teams); NG.go("countdown", {transition:"wipe"}); });
  });

  NG.scene("sea", function(el){
    el.innerHTML = '<div id="sign" class="card enter" style="position:absolute;left:330px;top:180px;width:1160px;min-height:150px;padding:22px 44px;display:flex;align-items:center;justify-content:center;text-align:center;font-weight:900;line-height:1.3"></div>' +
      '<div id="lanes" style="position:absolute;left:0;top:0;width:1920px;height:1080px;pointer-events:none"></div>';
    bird = U.h("div", {class:"mascot", style:"left:140px;top:0;z-index:5;transition:none"}, birdSvg());
    el.appendChild(bird);
    next(true);
  });

  function start(){ items = U.shuffle(G.items || []); idx = -1; lit = 0; NG.state.total = items.length;
    NG.teacher.hooks = {next:function(){ if (locked) next(); }, skip:function(){ clearIslands(); next(); }, reveal:function(){ if (!locked) reveal(); }};
    NG.go("sea", {transition:"iris"}); }

  function clearIslands(){ islands.forEach(function(it){ it.el.remove(); }); islands = []; Array.prototype.forEach.call(document.querySelectorAll('#lanes .explain'), function(e){ e.remove(); }); }

  function next(first){
    if (!first) NG.nextTurn();
    idx++; locked = false; clearIslands();
    if (idx >= items.length){ NG.fx.confetti(); NG.fx.rain("✨", {count:30}); NG.sfx("levelup"); return NG.finish({total:items.length, title:lit === items.length ? "🗼 등대가 모두 밝혀졌어요!" : "항해 끝!"}); }
    cur = items[idx]; NG.hud.setProgress(idx / items.length);
    var isOX = cur.type === "ox" || !cur.choices || !cur.choices.length, choices = isOX ? ["O 맞아요", "X 아니에요"] : cur.choices, lanes = isOX ? LANES_2 : LANES_4.slice(0, choices.length);
    var sign = document.getElementById("sign"); sign.style.fontSize = (cur.q.length > 36 ? 52 : 62) + "px";
    var team = NG.currentTeam();
    sign.innerHTML = (team && NG.state.teams.length > 1 ? '<span style="font-size:34px;margin-right:18px">' + team.icon + '</span>' : '') + U.esc(cur.q);
    NG.fx.pop(sign);
    birdLane = Math.floor(lanes.length / 2); bird.style.top = (lanes[birdLane] - 120) + "px";
    choices.forEach(function(c, i){
      var el = U.h("button", {class:"choice", style:"pointer-events:auto;position:absolute;left:0;top:0;width:660px;min-height:118px;border-radius:60px 60px 30px 30px;justify-content:center;text-align:center;white-space:nowrap;font-size:" + (c.length > 12 ? 36 : 44) + "px"}, '<span>🏝️ ' + U.esc(c) + '</span>');
      document.getElementById("lanes").appendChild(el);
      var it = {el:el, i:i, x:1980 + i * 140, y:lanes[i] - 60};
      el.style.transform = "translate(" + it.x + "px," + it.y + "px)";
      /* moving targets: answer on pointerdown (a click can miss when the island moves between down and up) */
      el.addEventListener("pointerdown", function(e){ e.preventDefault(); if (!NG.paused) choose(it); });
      islands.push(it);
    });
    NG.sfx("whoosh");
  }

  NG.onUpdate(function(dt){
    if (NG.sceneName !== "sea" || locked || !islands.length) return;
    var gone = false;
    islands.forEach(function(it){ it.x -= SPEED * dt * (it.x > 1300 ? 4 : 1); it.el.style.transform = "translate(" + it.x.toFixed(1) + "px," + it.y + "px)"; if (it.x < 330) gone = true; });
    var lead = islands.reduce(function(m, it){ return Math.min(m, it.x); }, 9999);
    var secs = Math.max(0, Math.ceil((lead - 330) / SPEED)); if (secs <= 3 && secs !== GAME_LOGIC._lastWarn){ GAME_LOGIC._lastWarn = secs; if (secs > 0) NG.sfx("warn"); }
    if (gone) reveal(true);
  });

  function jumpTo(it, done){
    var fromY = parseFloat(bird.style.top), toX = it.x + 160, toY = it.y - 120;
    NG.sfx("jump");
    var a = NG.anim(bird, [{transform:"translate(0,0)"}, {transform:"translate(" + (toX - 140) / 2 + "px," + ((toY - fromY) / 2 - 160) + "px)"}, {transform:"translate(" + (toX - 140) + "px," + (toY - fromY) + "px)"}], {duration:520, easing:"ease-in-out", fill:"forwards"});
    NG.after(520, done);
  }

  function choose(it){
    if (locked) return; locked = true;
    var ok = it.i === (cur.answer | 0);
    jumpTo(it, function(){
      var c = U.center(it.el);
      if (ok){
        lit++; it.el.classList.add("correct"); NG.feedback(true, it.el, {text: lit === items.length ? "등대 완성!" : "불이 켜졌어요!"}); NG.addScore(100, null, c);
        NG.fx.burst(1720, 300, {count:30, colors:["#ffd84d", "#fff3a0", "#ffffff"], gravity:300});
      } else {
        it.el.classList.add("wrong"); NG.sfx("hit"); NG.feedback(false, it.el, {text:"풍덩!", record: cur.q + " → " + answerText()});
        NG.fx.burst(c.x, c.y + 40, {count:26, colors:["#bfe9ff", "#ffffff"], angle:-Math.PI / 2, spread:0.9, speed:900});
        var right = islands[cur.answer | 0]; if (right) right.el.classList.add("correct");
      }
      explain(ok);
    });
  }

  function reveal(timeout){
    locked = true; var right = islands[cur.answer | 0]; if (right) right.el.classList.add("correct");
    NG.feedback(false, right ? right.el : null, {text: timeout ? "섬이 지나갔어요!" : "정답은 여기!", record: cur.q + " → " + answerText()});
    explain(false);
  }

  function answerText(){ return cur.choices && cur.choices.length ? cur.choices[cur.answer | 0] : ((cur.answer | 0) === 0 ? "O" : "X"); }

  function explain(ok){
    var sign = document.getElementById("sign");
    sign.innerHTML = '<div class="explain" style="display:flex;align-items:center;justify-content:space-between;width:100%"><div style="font-size:38px;font-weight:700;text-align:left;flex:1;margin-right:24px">' + (ok ? "🗼 " : "💡 ") + U.esc(cur.exp || "") + '</div><button class="btn small">다음 섬 ▶</button></div>';
    NG.fx.pop(sign);
    var b = sign.querySelector("button");
    NG.button(b, function(){ if (b._used) return; b._used = true; if (bird.getAnimations) bird.getAnimations().forEach(function(a){ a.cancel(); }); next(); });
  }

  return {
    start: start,
    toText: function(){ return {index:idx, total:items ? items.length : 0, lit:lit, locked:locked, question:cur ? cur.q : null, answer:cur ? cur.answer : null, islands:islands.map(function(i){ return Math.round(i.x); })}; }
  };
})();
