/* SPDX-License-Identifier: Apache-2.0
   Copyright 2026 박진영 (zln02)
   TSVoice: picks the most natural voice the browser has and reads text aloud (speechSynthesis wrapper).
   ES2017 only. API: TSVoice.speak(text, {lang, rate, pitch, onend}) / cancel() / pick(lang) / info(lang) / ready(cb)
   - waits for `voiceschanged` (max 1.5 s), scores voices (Natural/Online/Neural/Premium/Enhanced/Google/Yuna, local = lower)
   - long text is cut into sentences (~120 chars) and read through a queue (Chrome stops one long utterance after ~15 s)
   - iOS: unlocked by the first touch/click; never speaks in the same tick as cancel() */
(function(){
"use strict";
var synth = window.speechSynthesis, Utter = window.SpeechSynthesisUtterance;
var V = window.TSVoice = {supported: !!(synth && Utter), used: false, lastVoice: null, lastLang: ""};
if (!V.supported){ V.speak = V.cancel = V.ready = function(cb){ if (typeof cb === "function") cb([]); }; V.pick = function(){ return null; }; V.info = function(){ return {name: "", lang: "", note: ""}; }; return; }

var voices = [], loaded = false, waiting = [], gen = 0, queue = [], keep = null, curUtter = null;

function load(){ voices = synth.getVoices() || []; if (voices.length){ loaded = true; flush(); } }
function flush(){ var w = waiting; waiting = []; w.forEach(function(cb){ try { cb(voices); } catch (e) {} }); }
V.ready = function(cb){
  if (loaded){ cb(voices); return; }
  waiting.push(cb);
};
load();
if (!loaded){
  if (synth.addEventListener) synth.addEventListener("voiceschanged", load); else synth.onvoiceschanged = load;
  setTimeout(function(){ if (!loaded){ loaded = true; voices = synth.getVoices() || []; flush(); } }, 1500);
}

function norm(l){ return String(l || "").replace(/_/g, "-").toLowerCase(); }
function score(v, wantLang){
  var n = String(v.name || ""), s = 0, premium = /premium|enhanced/i.test(n);
  if (/natural|online/i.test(n)) s += 50;
  if (/neural|premium|enhanced/i.test(n)) s += 40;
  if (/google/i.test(n)) s += 20;
  if (/yuna/i.test(n) && premium) s += 30;
  if (v.localService) s -= 10;
  if (norm(v.lang) === wantLang) s += 100;
  return s;
}
/* best voice for a language such as ko-KR / en-US / en-GB (null = let the browser choose by lang) */
V.pick = function(lang){
  var want = norm(lang || "ko-KR"), prefix = want.split("-")[0], best = null, bs = -1e9;
  for (var i = 0; i < voices.length; i++){
    var v = voices[i];
    if (norm(v.lang).split("-")[0] !== prefix) continue;
    var sc = score(v, want);
    if (sc > bs){ bs = sc; best = v; }
  }
  return best;
};
V.info = function(lang){
  var v = V.pick(lang);
  if (!v) return {name: "", lang: lang || "", note: "기본 목소리"};
  return {name: v.name, lang: v.lang, note: v.localService ? "이 기기 목소리" : "인터넷 목소리"};
};

/* sentence queue */
function chunks(text){
  var parts = String(text).replace(/\s+/g, " ").trim().match(/[^.!?。！？…\n]+[.!?。！？…]*/g) || [], out = [], cur = "";
  parts.forEach(function(p){
    p = p.trim(); if (!p) return;
    while (p.length > 160){
      var cut = p.lastIndexOf(",", 120); if (cut < 40) cut = p.lastIndexOf(" ", 120); if (cut < 40) cut = 120;
      if (cur){ out.push(cur); cur = ""; }
      out.push(p.slice(0, cut + 1)); p = p.slice(cut + 1).trim();
    }
    if (!p) return;
    if (cur && (cur + " " + p).length > 120){ out.push(cur); cur = p; } else cur = cur ? cur + " " + p : p;
  });
  if (cur) out.push(cur);
  return out.filter(function(x){ return x; });
}
function stopKeep(){ if (keep){ clearInterval(keep); keep = null; } }
function startKeep(v){
  stopKeep();
  if (v && v.localService) return;          /* the 15 s cut-off only hits network voices */
  keep = setInterval(function(){ if (synth.speaking && !synth.paused){ synth.pause(); synth.resume(); } }, 8000);
}
function next(g, o, v){
  if (g !== gen) return;
  if (!queue.length){ stopKeep(); curUtter = null; if (typeof o.onend === "function") { try { o.onend(); } catch (e) {} } return; }
  var u = new Utter(queue.shift());
  u.lang = o.lang || "ko-KR"; u.rate = o.rate || 0.95; u.pitch = o.pitch || 1.0;
  if (v){ try { u.voice = v; } catch (e) {} }
  u.onend = function(){ next(g, o, v); };
  u.onerror = function(){ next(g, o, v); };
  curUtter = u;                              /* keep a reference: Chrome may drop it mid-speech otherwise */
  try { synth.speak(u); } catch (e) { stopKeep(); }
}
V.cancel = function(){ gen++; queue = []; stopKeep(); try { synth.cancel(); } catch (e) {} };
V.speak = function(text, opts){
  var o = opts || {}, lang = o.lang || "ko-KR";
  text = String(text == null ? "" : text); if (!text.trim()) return;
  V.used = true; V.lastLang = lang;
  var busy = synth.speaking || synth.pending, g = ++gen;
  queue = []; stopKeep();
  if (busy){ try { synth.cancel(); } catch (e) {} }
  var start = function(){
    if (g !== gen) return;
    V.ready(function(){
      if (g !== gen) return;
      var v = V.pick(lang); V.lastVoice = v ? v.name : null;
      queue = chunks(text);
      startKeep(v);
      next(g, {lang: lang, rate: o.rate, pitch: o.pitch, onend: o.onend}, v);
    });
  };
  if (busy) setTimeout(start, 120); else start();   /* iOS: no speak() right after cancel() */
};

/* iOS / Safari only allow speech after a user gesture: a silent utterance on the first touch unlocks it */
var unlocked = false;
function unlock(){
  if (unlocked) return; unlocked = true;
  try { var u = new Utter(" "); u.volume = 0; synth.speak(u); } catch (e) {}
  ["pointerdown", "touchend", "keydown", "click"].forEach(function(t){ document.removeEventListener(t, unlock, true); });
}
["pointerdown", "touchend", "keydown", "click"].forEach(function(t){ document.addEventListener(t, unlock, true); });
})();
