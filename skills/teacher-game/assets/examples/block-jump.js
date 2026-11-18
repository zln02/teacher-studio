/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) */
/* EXAMPLE: 정답 블록 점프 — 에셋 팩(kenney-platformer-core) 사용 플랫포머형 퀴즈
   세계관: 언덕길 모험 / 동작: 정답이 적힌 ? 블록을 눌러 캐릭터가 달려가 머리로 치기 / 배치: 횡스크롤 지형
   시그니처: 정답 블록에서 코인이 튀어 올라 HUD 코인함으로 날아감, 끝에 깃발이 펄럭이며 도착
   필요: GAME.packs 에 "kenney-platformer-core" (또는 CDN 스크립트)
*/
window.GAME_LOGIC = (function(){
  var U = NG.util, G = window.GAME, items, idx = -1, cur, locked = false, coins = 0;
  var world, player, playerSpr, groundX = 0, bgX = 0, cloudX = 0, blocks = [], hearts = 3, walking = 0;
  var TILE = 96, GROUND_Y = 880, PX = 330;
  var COLORS = ["beige", "green", "pink", "purple", "yellow"];

  function color(){ var t = NG.state.teams.length ? NG.state.turn : 0; return COLORS[t % COLORS.length]; }
  function frames(pose){ var c = color(); return pose === "walk" ? ["char_" + c + "_walk_a", "char_" + c + "_walk_b"] : ["char_" + c + "_" + pose]; }

  function sceneBase(el){
    el.innerHTML = "";
    var sky = U.h("div", {style:"position:absolute;left:0;top:0;width:1920px;height:1080px;background:#cfe9ff url(" + NG.img("background_solid_sky") + ") repeat;background-size:256px"});
    var hills = U.h("div", {id:"hills", style:"position:absolute;left:0;top:240px;width:1920px;height:768px;background:url(" + NG.img("background_color_hills") + ") repeat-x;background-size:768px 768px"});
    var clouds = U.h("div", {id:"clouds", style:"position:absolute;left:0;top:40px;width:1920px;height:384px;background:url(" + NG.img("background_clouds") + ") repeat-x;background-size:384px 384px;opacity:.9"});
    world = U.h("div", {style:"position:absolute;left:0;top:0;width:1920px;height:1080px"});
    var ground = U.h("div", {id:"ground", style:"position:absolute;left:0;top:" + GROUND_Y + "px;width:1920px;height:" + (1080 - GROUND_Y) + "px;background:url(" + NG.img("terrain_grass_block_top") + ") repeat-x top/" + TILE + "px " + TILE + "px,url(" + NG.img("terrain_grass_block_center") + ") repeat 0 " + TILE + "px/" + TILE + "px " + TILE + "px"});
    el.appendChild(sky); el.appendChild(clouds); el.appendChild(hills); el.appendChild(ground); el.appendChild(world);
    return world;
  }

  NG.scene("title", function(el){
    NG.state.phase = "title"; NG.hud.show = false; NG.hud.render(); NG.timer.stop(); NG.bg.set("none");
    sceneBase(el);
    var box = U.h("div", {style:"position:absolute;left:0;top:140px;width:1920px;text-align:center"},
      '<div class="title shine" style="font-size:150px;color:#fff;text-shadow:0 10px 0 #2e7d32,0 0 30px rgba(0,0,0,.25)">' + U.esc(G.title) + '</div>' +
      '<div class="subtitle" style="color:#1b4d2e;font-size:46px;margin-top:10px">' + U.esc(G.subtitle || "") + '</div>' +
      '<div class="row" id="t-teams" style="margin-top:36px"></div><button class="btn pulse" id="t-start" style="margin-top:32px">▶ 모험 시작</button>');
    el.appendChild(box);
    COLORS.slice(0, 4).forEach(function(c, i){ var im = NG.imgEl("char_" + c + "_idle", {style:"position:absolute;top:" + (GROUND_Y - 128) + "px;left:" + (220 + i * 160) + "px;width:128px"}); el.appendChild(im); NG.after(400 + i * 180, function(){ NG.anim(im, [{transform:"translateY(0)"}, {transform:"translateY(-90px)"}, {transform:"translateY(0)"}], {duration:520, easing:"cubic-bezier(.33,1.4,.6,1)"}); }); });
    ["coin_gold", "gem_blue", "star"].forEach(function(n, i){ var im = NG.imgEl(n, {style:"position:absolute;top:" + (560 + i * 30) + "px;left:" + (1300 + i * 170) + "px;width:96px"}); el.appendChild(im); NG.anim(im, [{transform:"translateY(0)"}, {transform:"translateY(-24px)"}, {transform:"translateY(0)"}], {duration:1400 + i * 200, iterations:Infinity, easing:"ease-in-out"}); });
    var teams = G.teams || 0, tb = el.querySelector("#t-teams");
    [0, 2, 3, 4].forEach(function(n){ var b = U.h("button", {class:"btn small " + (n === teams ? "" : "secondary")}, n === 0 ? "혼자" : n + "모둠"); NG.button(b, function(){ teams = n; Array.prototype.forEach.call(tb.children, function(c){ c.classList.add("secondary"); }); b.classList.remove("secondary"); NG.fx.pop(b); }); tb.appendChild(b); });
    NG.button(el.querySelector("#t-start"), function(){ NG.unlockAudio(); NG.setupTeams(teams); NG.go("countdown", {transition:"iris"}); });
  });

  NG.scene("run", function(el){
    sceneBase(el);
    player = NG.imgEl(frames("idle")[0], {style:"position:absolute;left:" + PX + "px;top:" + (GROUND_Y - 128) + "px;width:128px;z-index:5;transform-origin:50% 100%"});
    world.appendChild(player); playerSpr = NG.sprite(player, frames("idle"), 8);
    var hud = U.h("div", {id:"phud", style:"position:absolute;right:340px;top:22px;display:flex;align-items:center;z-index:6"});
    world.appendChild(hud); renderHud();
    world.appendChild(U.h("div", {id:"sign", class:"card", style:"position:absolute;left:260px;top:150px;width:1400px;min-height:130px;padding:20px 40px;display:flex;align-items:center;justify-content:center;text-align:center;font-weight:900;font-size:58px;line-height:1.3;background:#fff8e1;color:#4e342e;border-color:#8d6e63"}));
    next(true);
  });

  function renderHud(){
    var h = document.getElementById("phud"); if (!h) return;
    var html = "";
    if (!NG.state.teams.length) for (var i = 0; i < 3; i++) html += '<img src="' + NG.img(i < hearts ? "hud_heart" : "hud_heart_empty") + '" style="width:64px;margin-right:6px">';
    html += '<img id="coinIcon" src="' + NG.img("hud_coin") + '" style="width:64px;margin-left:18px"><b style="font-family:var(--font-display);font-size:60px;color:#fff;text-shadow:0 4px 0 #8a5a00;margin-left:8px" id="coinN">' + coins + '</b>';
    h.innerHTML = html;
  }

  NG.onUpdate(function(dt){
    if (NG.sceneName !== "run") return;
    if (walking > 0){
      var d = 420 * dt; walking = Math.max(0, walking - d); groundX -= d; bgX -= d * 0.35; cloudX -= d * 0.15;
      blocks.forEach(function(b){ b.x -= d; place(b); });
      if (walking === 0){ playerSpr.set(frames("idle")); }
    }
    cloudX -= 12 * dt;
    var g = document.getElementById("ground"), hl = document.getElementById("hills"), cl = document.getElementById("clouds");
    if (g) g.style.backgroundPosition = groundX.toFixed(0) + "px 0," + groundX.toFixed(0) + "px " + TILE + "px";
    if (hl) hl.style.backgroundPosition = bgX.toFixed(0) + "px 0"; if (cl) cl.style.backgroundPosition = cloudX.toFixed(0) + "px 0";
  });

  function place(b){ b.el.style.transform = "translate(" + b.x.toFixed(0) + "px," + b.y + "px)"; }

  function start(){
    items = U.shuffle(G.items || []); idx = -1; coins = 0; hearts = 3; NG.state.total = items.length;
    NG.teacher.hooks = {next:function(){ if (locked) next(); }, skip:function(){ next(); }, reveal:function(){ if (!locked) reveal(); }};
    NG.go("run", {transition:"wipe"});
  }

  function next(first){
    if (!first) NG.nextTurn();
    idx++; locked = false;
    blocks.forEach(function(b){ b.el.remove(); }); blocks = [];
    var exp = document.querySelector(".explain"); if (exp) exp.remove();
    if (idx >= items.length) return finale();
    cur = items[idx]; NG.hud.setProgress(idx / items.length);
    var isOX = cur.type === "ox" || !cur.choices || !cur.choices.length, choices = isOX ? ["O", "X"] : cur.choices;
    var sign = document.getElementById("sign"), team = NG.currentTeam();
    sign.style.fontSize = (cur.q.length > 36 ? 50 : 58) + "px";
    sign.innerHTML = (team && NG.state.teams.length > 1 ? '<img src="' + NG.img("hud_player_" + color()) + '" style="width:64px;margin-right:18px">' : "") + U.esc(cur.q);
    NG.fx.pop(sign);
    playerSpr.set(frames("walk"), 10);
    var many = choices.length > 2, gap = many ? 300 : 520, firstX = many ? 560 : 720, startX = firstX + 1240;
    choices.forEach(function(c, i){
      var el = U.h("div", {style:"position:absolute;left:0;top:0;width:300px;cursor:pointer;touch-action:none;display:flex;flex-direction:column;align-items:center"},
        '<div class="card" style="padding:12px 20px;min-width:260px;text-align:center;font-weight:900;font-size:' + (c.length > 10 ? 32 : 40) + 'px;color:#3e2723;background:#fff;margin-bottom:14px;white-space:nowrap">' + U.esc(c) + '</div>');
      var blk = NG.imgEl("block_exclamation", {style:"width:112px"}); el.appendChild(blk);
      world.appendChild(el);
      var b = {el:el, blk:blk, i:i, x:startX + i * gap, y:470};
      place(b); blocks.push(b);
      el.addEventListener("pointerdown", function(e){ e.preventDefault(); if (!NG.paused) choose(b); });
      NG.anim(blk, [{transform:"translateY(0)"}, {transform:"translateY(-8px)"}, {transform:"translateY(0)"}], {duration:900 + i * 120, iterations:Infinity, easing:"ease-in-out"});
    });
    walking = startX - firstX;
    if (G.timer) NG.after(walking / 420 * 1000 + 100, function(){ if (!locked && cur === items[idx]) NG.timer.start(G.timer, function(){ if (!locked){ NG.fx.toast("⏰ 시간 끝!"); reveal(true); } }); });
  }

  function choose(b){
    if (locked || walking > 0) return; locked = true; NG.timer.stop();
    var ok = b.i === (cur.answer | 0), target = b.x + 150 - 64, from = PX + (player._x || 0);
    playerSpr.set(frames("walk"), 12);
    var dx = target - PX;
    NG.anim(player, [{transform:"translateX(" + (player._x || 0) + "px)"}, {transform:"translateX(" + dx + "px)"}], {duration:420, easing:"ease-in-out", fill:"forwards"});
    player._x = dx;
    NG.after(430, function(){
      playerSpr.set(frames("jump")); NG.sfx("jump");
      NG.anim(player, [{transform:"translateX(" + dx + "px) translateY(0)"}, {transform:"translateX(" + dx + "px) translateY(-250px)"}, {transform:"translateX(" + dx + "px) translateY(0)"}], {duration:560, easing:"cubic-bezier(.3,1.25,.6,1)", fill:"forwards"});
      NG.after(250, function(){ hit(b, ok); });
      NG.after(560, function(){ playerSpr.set(frames(ok ? "idle" : "hit")); NG.fx.squash ? 0 : 0; });
    });
  }

  function hit(b, ok){
    var c = U.center(b.blk);
    NG.anim(b.blk, [{transform:"translateY(0)"}, {transform:"translateY(-30px)"}, {transform:"translateY(0)"}], {duration:220});
    if (ok){
      b.blk.src = NG.img("block_exclamation_active"); NG.sfx("coin");
      var coin = NG.imgEl("coin_gold", {style:"position:absolute;left:" + (c.x - 40) + "px;top:" + (c.y - 120) + "px;width:80px;z-index:9"});
      world.appendChild(coin);
      var hudC = U.center(document.getElementById("coinIcon"));
      NG.anim(coin, [{transform:"translate(0,0) scale(1)"}, {transform:"translate(0,-160px) scale(1.3)", offset:.35}, {transform:"translate(" + (hudC.x - c.x) + "px," + (hudC.y - c.y + 120) + "px) scale(.6)"}], {duration:900, easing:"cubic-bezier(.5,0,.5,1)", fill:"forwards"});
      NG.after(900, function(){ coin.remove(); coins++; renderHud(); NG.fx.pop(document.getElementById("coinIcon")); NG.sfx("pop"); });
      NG.fx.burst(c.x, c.y - 40, {count:30, colors:["#ffd54f", "#fff59d", "#ffffff"]});
      NG.feedback(true, b.el, {text:U.pick(["코인 획득!", "정답!", "최고예요!"])});
      NG.addScore(100, null, c);
    } else {
      b.blk.src = NG.img("block_empty"); cur._wrong = true;
      var slime = NG.imgEl("slime_normal_walk_a", {style:"position:absolute;left:" + (PX + player._x + 260) + "px;top:" + (GROUND_Y - 64) + "px;width:96px;z-index:4"});
      world.appendChild(slime); NG.sprite(slime, ["slime_normal_walk_a", "slime_normal_walk_b"], 6);
      NG.anim(slime, [{transform:"translateX(0)"}, {transform:"translateX(-170px)"}], {duration:500, fill:"forwards"});
      NG.after(520, function(){ NG.sfx("hit"); NG.fx.shake(0.5); if (!NG.state.teams.length){ hearts = Math.max(0, hearts - 1); renderHud(); } NG.anim(slime, [{opacity:1}, {opacity:0}], {duration:600, delay:500, fill:"forwards"}); });
      NG.feedback(false, b.el, {text:"앗, 빈 블록!", record:cur.q + " → " + answerText()});
      var right = blocks[cur.answer | 0]; if (right) NG.after(700, function(){ right.blk.src = NG.img("block_exclamation_active"); NG.fx.pop(right.el); });
    }
    NG.after(900, function(){ explain(ok); });
  }

  function reveal(timeout){ locked = true; var right = blocks[cur.answer | 0]; if (right){ right.blk.src = NG.img("block_exclamation_active"); NG.fx.pop(right.el); } cur._wrong = true; NG.feedback(false, right ? right.el : null, {text: timeout ? "시간 초과!" : "정답은 여기!", record:cur.q + " → " + answerText()}); explain(false); }
  function answerText(){ return cur.choices && cur.choices.length ? cur.choices[cur.answer | 0] : ((cur.answer | 0) === 0 ? "O" : "X"); }

  function explain(ok){
    var box = U.h("div", {class:"card enter explain", style:"position:absolute;left:260px;top:300px;width:1400px;display:flex;align-items:center;justify-content:space-between;padding:18px 32px;z-index:8;background:#fff8e1;color:#4e342e;border-color:#8d6e63"},
      '<div style="font-size:36px;font-weight:700;flex:1;margin-right:24px">' + (ok ? "🪙 " : "💡 ") + U.esc(cur.exp || "") + '</div><button class="btn small">계속 ▶</button>');
    world.appendChild(box);
    var b = box.querySelector("button");
    NG.button(b, function(){ if (b._used) return; b._used = true; NG.anim(player, [{transform:"translateX(" + (player._x || 0) + "px)"}, {transform:"translateX(0)"}], {duration:300, fill:"forwards"}); player._x = 0; NG.after(300, function(){ next(); }); });
  }

  function finale(){
    NG.timer.stop(); playerSpr.set(frames("walk"), 10);
    var flag = NG.imgEl("flag_green_a", {style:"position:absolute;left:1500px;top:" + (GROUND_Y - 128) + "px;width:128px"}); world.appendChild(flag); NG.sprite(flag, ["flag_green_a", "flag_green_b"], 4);
    NG.anim(player, [{transform:"translateX(0)"}, {transform:"translateX(1040px)"}], {duration:1600, easing:"ease-in-out", fill:"forwards"});
    NG.after(1650, function(){ playerSpr.set(frames("front")); NG.sfx("levelup"); NG.fx.confetti(); NG.fx.rain("🪙", {count:26}); });
    NG.finish({total:items.length, title:"🏁 도착! 코인 " + coins + "개"});
  }

  return {
    start: start,
    toText: function(){ return {index:idx, total:items ? items.length : 0, coins:coins, hearts:hearts, locked:locked, walking:Math.round(walking), question:cur ? cur.q : null, answer:cur ? cur.answer : null, blocks:blocks.map(function(b){ return Math.round(b.x); })}; }
  };
})();
