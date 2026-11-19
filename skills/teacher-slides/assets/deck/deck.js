/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02) · Deck runtime for `studio.py build slides` (ES2017). Optional parts are cut out by deck.py when unused. */
window.SHOW = (function(){
"use strict";
var S = window.STAGE, deck = document.getElementById("deck");
var slides = [].slice.call(deck.querySelectorAll(".sl")), cur = -1, step = 0, buf = "", notesOn = false, hideT = null;
var chrome = document.getElementById("chrome"), pn = chrome.querySelector(".pn"), prog = chrome.querySelector(".prog"), notes = document.getElementById("notes"), black = document.getElementById("black");
function qa(el, s){ return [].slice.call(el.querySelectorAll(s)); }
function cssVar(n){ return getComputedStyle(document.documentElement).getPropertyValue("--" + n).trim(); }
function maxStep(sl){ var m = 0; qa(sl, "[data-b]").forEach(function(e){ m = Math.max(m, +e.getAttribute("data-b")); }); return m; }
function applyStep(sl, k){
  qa(sl, "[data-b]").forEach(function(e){ e.classList.toggle("on", +e.getAttribute("data-b") <= k); });
  var sv = sl.getAttribute("data-solve");
  sl.classList.toggle("solved", sv !== null && k >= +sv);
}
function fitAll(sl){
  qa(sl, "[data-fit]").forEach(function(b){
    var p = b.getAttribute("data-fit").split(","), mn = +p[1] || 28, tx = b.querySelector(".tx") || b, size = parseFloat(getComputedStyle(b).fontSize);
    var guard = 60;
    while (guard-- > 0 && size > mn && (tx.offsetHeight > b.clientHeight + 1 || tx.scrollWidth > b.clientWidth + 1)){ size -= 2; b.style.fontSize = size + "px"; }
  });
}
function show(i, all){
  if (i < 0 || i >= slides.length) return;
  cur = i; var sl = slides[i];
  slides.forEach(function(s){ s.classList.remove("on"); });
  void sl.offsetWidth; sl.classList.add("on");
  var m = maxStep(sl); step = all ? m : 0; applyStep(sl, step);
  fitAll(sl);
  /*#chart*/ initCharts(sl); /*#end*/
  /*#math*/ initMath(sl); /*#end*/
  /*#timer*/ initTimer(sl); /*#end*/
  pn.textContent = (i + 1) + " / " + slides.length; prog.style.width = ((i + 1) / slides.length * 100) + "%";
  notes.textContent = sl.getAttribute("data-note") || "";
  notes.classList.toggle("on", notesOn && !!notes.textContent);
  if (location.hash !== "#" + (i + 1)) { try { history.replaceState(null, "", "#" + (i + 1)); } catch (e) {} }
}
function next(){ var sl = slides[cur], m = maxStep(sl); if (step < m){ step++; applyStep(sl, step); } else if (cur < slides.length - 1){ show(cur + 1); } else { S.toast("마지막 장이에요"); } }
function prev(){ var sl = slides[cur]; if (step > 0){ step--; applyStep(sl, step); } else if (cur > 0){ show(cur - 1, true); } }
function setBlack(on){ black.classList.toggle("on", on); }
/*#timer*/
function fmt(s){ s = Math.max(0, Math.ceil(s)); var m = Math.floor(s / 60), r = s % 60; return (m < 10 ? "0" : "") + m + ":" + (r < 10 ? "0" : "") + r; }
function beep(){ try { var A = window.AudioContext || window.webkitAudioContext, c = new A(), o = c.createOscillator(), g = c.createGain(); o.frequency.value = 880; g.gain.value = 0.15; o.connect(g); g.connect(c.destination); o.start(); setTimeout(function(){ o.stop(); c.close(); }, 700); } catch (e) {} }
function initTimer(sl){
  var d = sl.querySelector(".tdisp"); if (!d || d.__t) return;
  var t = d.__t = {total: (+d.getAttribute("data-min")) * 60, left: 0, run: false, last: 0, id: null};
  t.left = t.total;
  var bar = sl.querySelector(".tbar i"), prg = sl.querySelector(".tprog"), circ = +d.getAttribute("data-circ") || 0, main = sl.querySelector('[data-act="toggle"]');
  function draw(){
    d.textContent = fmt(t.left); var f = t.total ? t.left / t.total : 0;
    if (bar) bar.style.transform = "scaleX(" + f + ")";
    if (prg) prg.style.strokeDashoffset = String(circ * (1 - f));
    d.classList.toggle("done", t.left <= 0 && t.total > 0);
    main.textContent = t.run ? "멈춤" : (t.left <= 0 ? "다시" : "시작");
  }
  function tick(){ var now = Date.now(); t.left -= (now - t.last) / 1000; t.last = now; if (t.left <= 0){ t.left = 0; t.run = false; clearInterval(t.id); beep(); } draw(); }
  t.toggle = function(){ if (t.left <= 0) t.left = t.total; t.run = !t.run; if (t.run){ t.last = Date.now(); t.id = setInterval(tick, 200); } else clearInterval(t.id); draw(); };
  t.reset = function(){ t.run = false; clearInterval(t.id); t.left = t.total; draw(); };
  t.add = function(m){ t.total = Math.max(60, t.total + m * 60); t.left = Math.max(0, t.left + m * 60); if (t.left > t.total) t.left = t.total; draw(); };
  qa(sl, ".tbtn").forEach(function(b){ b.addEventListener("click", function(e){ e.stopPropagation(); var a = b.getAttribute("data-act"); if (a === "toggle") t.toggle(); else if (a === "reset") t.reset(); else t.add(a === "plus" ? 1 : -1); b.blur(); }); b.addEventListener("pointerup", function(e){ e.stopPropagation(); }); });
  draw();
}
function curTimer(){ var d = slides[cur].querySelector(".tdisp"); return d && d.__t; }
/*#end*/
/*#chart*/
function rgba(hex, a){ var h = hex.replace("#", ""); if (h.length === 3) h = h.replace(/(.)/g, "$1$1"); return "rgba(" + parseInt(h.substr(0, 2), 16) + "," + parseInt(h.substr(2, 2), 16) + "," + parseInt(h.substr(4, 2), 16) + "," + a + ")"; }
function initCharts(sl){
  qa(sl, "canvas[data-cfg]").forEach(function(cv){
    if (cv.__c) return;
    var cfg = JSON.parse(cv.getAttribute("data-cfg")), pr = cssVar("pr"), tx = cssVar("tx"), mu = cssVar("mu"), line = cssVar("line"), kind = cfg.kind;
    var animate = !document.body.classList.contains("noanim");
    var tints = [1, 0.72, 0.5, 0.36, 0.26, 0.2, 0.16, 0.12];
    var ds = cfg.series.map(function(s, k){
      var base = k === 0 ? pr : mu;
      var o = {label: s.name || "", data: s.data, borderWidth: kind === "line" ? 6 : 0, borderColor: base, tension: 0.35, pointRadius: kind === "line" ? 8 : 0, pointBackgroundColor: base, borderRadius: 14, maxBarThickness: 120};
      if (kind === "pie" || kind === "doughnut"){ o.backgroundColor = s.data.map(function(_, j){ return rgba(pr, tints[j % tints.length]); }); o.borderColor = cssVar("bg1"); o.borderWidth = 4; }
      else if (kind === "line"){ o.backgroundColor = rgba(base, 0.14); o.fill = k === 0; }
      else { o.backgroundColor = base; }
      return o;
    });
    var valuePlugin = {id: "vals", afterDatasetsDraw: function(ch){
      if (kind === "line") return; var c = ch.ctx; c.save(); c.fillStyle = tx; c.font = "700 30px " + getComputedStyle(document.body).fontFamily; c.textAlign = "center"; c.textBaseline = "middle";
      ch.data.datasets.forEach(function(d, di){ ch.getDatasetMeta(di).data.forEach(function(el, i){ var v = d.data[i];
        if (kind === "bar") c.fillText(v + (cfg.unit || ""), el.x, el.y - 24); else { var a = (el.startAngle + el.endAngle) / 2, r = (el.innerRadius + el.outerRadius) / 2; c.fillText(v, el.x + Math.cos(a) * r, el.y + Math.sin(a) * r); } }); });
      c.restore(); }};
    cv.__c = new Chart(cv.getContext("2d"), {type: kind, data: {labels: cfg.labels, datasets: ds}, plugins: [valuePlugin], options: {
      responsive: false, animation: animate ? {duration: 900} : false, layout: {padding: {top: 40, right: 24}},
      plugins: {legend: {display: cfg.series.length > 1 || kind === "pie" || kind === "doughnut", position: "bottom", labels: {color: tx, font: {size: 28, weight: "600"}, boxWidth: 24, padding: 20}}, tooltip: {enabled: false}},
      scales: (kind === "pie" || kind === "doughnut") ? {} : {x: {grid: {display: false}, border: {color: line}, ticks: {color: tx, font: {size: 28, weight: "600"}}}, y: {beginAtZero: true, grid: {color: line}, border: {display: false}, ticks: {color: mu, font: {size: 28}, maxTicksLimit: 5}}}}});
  });
}
/*#end*/
/*#math*/
function initMath(sl){
  qa(sl, ".tex").forEach(function(el){
    if (el.__k) return; el.__k = 1;
    try { katex.render(el.getAttribute("data-tex"), el, {displayMode: true, throwOnError: false, output: "html"}); } catch (e) { el.textContent = el.getAttribute("data-tex"); }
    var box = el.parentNode, size = 96; el.style.fontSize = size + "px";
    while (size > 40 && (el.scrollWidth > box.clientWidth - 80 || el.scrollHeight > box.clientHeight - 40)){ size -= 4; el.style.fontSize = size + "px"; }
  });
}
/*#end*/
var down = null;
function onDown(e){ down = {x: e.clientX, y: e.clientY, t: Date.now(), tg: e.target}; }
function onUp(e){
  if (!down) return; var dx = e.clientX - down.x, dy = e.clientY - down.y, tg = down.tg; down = null;
  if (tg.closest && tg.closest("button, a, video, .tctl")) return;
  if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.5){ dx < 0 ? next() : prev(); return; }
  if (Math.abs(dx) < 12 && Math.abs(dy) < 12){ (e.clientX > window.innerWidth * 0.35) ? next() : prev(); }
}
function onKey(e){
  var k = e.key;
  if (/^[0-9]$/.test(k)){ buf += k; clearTimeout(hideT); hideT = setTimeout(function(){ buf = ""; }, 1800); S.toast("→ " + buf + "번 (Enter)", 1500); return true; }
  if (k === "Enter" && buf){ var n = parseInt(buf, 10); buf = ""; if (n >= 1 && n <= slides.length) show(n - 1); return true; }
  if (k === "n" || k === "N"){ notesOn = !notesOn; notes.classList.toggle("on", notesOn && !!notes.textContent); if (notesOn && !notes.textContent) S.toast("이 장에는 메모가 없어요"); return true; }
  if (k === "b" || k === "B" || k === "."){ setBlack(!black.classList.contains("on")); return true; }
  if (black.classList.contains("on")){ setBlack(false); return true; }
  /*#timer*/ var tm = curTimer(); if (tm && (k === " " || k === "s" || k === "S")){ e.preventDefault(); tm.toggle(); return true; } /*#end*/
  if (k === "ArrowRight" || k === "PageDown" || k === "Enter" || k === " " || k === "ArrowDown"){ e.preventDefault(); next(); return true; }
  if (k === "ArrowLeft" || k === "PageUp" || k === "ArrowUp" || k === "Backspace"){ e.preventDefault(); prev(); return true; }
  if (k === "Home"){ show(0); return true; }
  if (k === "End"){ show(slides.length - 1, true); return true; }
  return false;
}
function allOn(on){
  document.body.classList.toggle("printing", on);
  slides.forEach(function(sl){ if (on){ sl.classList.add("on"); applyStep(sl, 99); /*#chart*/ initCharts(sl); /*#end*/ /*#math*/ initMath(sl); /*#end*/ fitAll(sl); } else { sl.classList.remove("on"); } });
  if (!on && cur >= 0) show(cur, true);
}
window.addEventListener("beforeprint", function(){ allOn(true); });
window.addEventListener("afterprint", function(){ allOn(false); });
window.__deck = {go: function(i, all){ show(i, all !== false); }, count: slides.length, noanim: function(){ document.body.classList.add("noanim"); }, step: function(){ return step; }, next: next, prev: prev};
return {
  start: function(){
    document.addEventListener("pointerdown", onDown); document.addEventListener("pointerup", onUp);
    S.restart = function(){ /*#timer*/ var t = curTimer(); if (t) t.reset(); /*#end*/ };
    var h = parseInt((location.hash || "").replace("#", ""), 10), q = /[?&]static=1/.test(location.search);
    if (q) document.body.classList.add("noanim");
    show(h >= 1 && h <= slides.length ? h - 1 : 0, q);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function(){ if (cur >= 0) fitAll(slides[cur]); });
    window.addEventListener("hashchange", function(){ var n = parseInt(location.hash.replace("#", ""), 10); if (n >= 1 && n <= slides.length && n - 1 !== cur) show(n - 1); });
  },
  onKey: onKey,
  toText: function(){ return JSON.stringify({slide: cur + 1, of: slides.length, step: step}); }
};
})();
