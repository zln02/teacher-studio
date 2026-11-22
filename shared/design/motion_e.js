/* SPDX-License-Identifier: Apache-2.0 · Copyright 2026 박진영 (zln02)
   Preset E motion vocabulary (shared/design/motion_e.js) · ES2017 · no libraries · presenter / click driven.
   Learned from the 2026-11-23 training deck (docs/training/deck-v3-src/motion-e.js), rewritten as one self-contained helper.

   Rules: fast in (120-260 ms), blur only while moving, then hold still. Back, print, `?static=1` and prefers-reduced-motion
   show the FINAL state at once. Script tweens only (no CSS transitions: a recorder that freezes the clock catches them half way).

   Declarative: put data-e="<word>" on an element; data-b="n" = the click (build step) it plays on (none = when the slide opens).
     big     a big headline: syllables drop in one by one (45 ms apart), blur while falling          <h1 data-e="big">
     pen     an inline <svg> whose <path>s draw on like a pen, then its .e-note texts write in        <svg class="e-pen" data-e="pen">
     note    one hand-written note revealed left to right                                               <div class="e-note" data-e="note">
     pills   step pills: children <span data-b="k"> become current on their click                       <div class="e-pills" data-e="pills">
     hl      an evidence line lit word by word; words with digits turn accent                             <p class="e-hl" data-e="hl">
     dot     the accent dot carrier: falls in, then stretches into the rule (the element itself)         <i class="bar" data-e="dot">
     drag    a multi-cursor drag scene on a board (labelled cursors, smart guides, ends on the result)  <div class="e-board" data-e="drag">
     cursor  one demo cursor along a path, clicking where asked, ends on the real result                <div class="e-cur" data-e="cursor">
     in      the default build entrance (blur + 30px travel)                                             any [data-b] element in E mode
   API:  TSE.step(slide, k, instant)   call on every slide / step change (the slides runtime does this)
         TSE.hud(slide, i, n)          HUD frame: four corners, a tick ruler and the slide's place on it
         TSE.auto(root)                stand-alone pages: → / click = next, ← = back over [data-b] steps
*/
window.TSE = (function () {
  "use strict";
  var T = /*E_TOKENS*/null || { xs: 120, s: 200, m: 260, l: 420, gap: 60, stagger: 45, "in": 200, out: 150, blur: 8, word: 70, pen: 520, cursor: 620 };
  var RM = false;
  try { RM = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { RM = false; }
  var live = [], raf = 0, visit = 0;
  function qa(el, s) { return [].slice.call(el.querySelectorAll(s)); }
  function clamp(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  var EZ = {
    linear: function (t) { return t; },
    out: function (t) { return 1 - Math.pow(1 - t, 3); },
    snap: function (t) { return 1 - Math.pow(1 - t, 4); },
    inout: function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; },
    spring: function (t) { return t >= 1 ? 1 : 1 - Math.exp(-6 * t) * Math.cos(9 * t); }
  };
  function loop() {
    var now = performance.now(), keep = [];
    for (var i = 0; i < live.length; i++) {
      var a = live[i], t = (now - a.t0) / a.dur;
      if (t < 0) { keep.push(a); continue; }
      t = clamp(t);
      a.fn(a.ease(t), t);
      if (t < 1) keep.push(a); else if (a.done) a.done();
    }
    live = keep;
    raf = live.length ? requestAnimationFrame(loop) : 0;
  }
  // one tween: fn(eased, raw) from `delay` ms for `dur` ms. The start state is painted at once (no flash of the final state).
  // lazy = do not paint the start now (for moves that start from wherever the thing is when their turn comes).
  function tw(dur, delay, ease, fn, done, lazy) {
    var a = { t0: performance.now() + (delay || 0), dur: Math.max(1, dur), ease: EZ[ease] || EZ.out, fn: fn, done: done };
    if (!lazy) fn(a.ease(0), 0);
    live.push(a);
    if (!raf) raf = requestAnimationFrame(loop);
    return a;
  }
  function stopAll() { live = []; if (raf) cancelAnimationFrame(raf); raf = 0; }
  function clear(el) { el.style.opacity = ""; el.style.transform = ""; el.style.filter = ""; el.style.clipPath = ""; }
  function scaleOf(el) { var r = el.getBoundingClientRect(); return el.offsetWidth ? r.width / el.offsetWidth : 1; }
  function rel(el, box) {   // element rectangle in the box's own (unscaled) pixels
    var s = scaleOf(box) || 1, a = el.getBoundingClientRect(), b = box.getBoundingClientRect();
    return { x: (a.left - b.left) / s, y: (a.top - b.top) / s, w: a.width / s, h: a.height / s };
  }
  function mk(tag, cls, parent, html) { var e = document.createElement(tag); e.className = cls; if (html) e.innerHTML = html; if (parent) parent.appendChild(e); return e; }

  // ---- split text into syllables / words, keeping inline markup (<em>, <b>) ----
  function split(el, unit) {
    if (el.__split) return el.__split;
    var out = [];
    (function walk(n) {
      [].slice.call(n.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          // words stay unbreakable boxes (Korean keep-all wrapping is unchanged); syllables are boxes inside their word
          var parts = c.textContent.split(/(\s+)/);
          var frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(p)); return; }
            var s = document.createElement("span");
            s.className = unit === "word" ? "e-w" + (/\d/.test(p) ? " e-num" : "") : "e-wd";
            s.style.display = "inline-block";
            s.style.whiteSpace = "nowrap";
            if (unit === "word") { s.textContent = p; out.push(s); }
            else {
              p.split("").forEach(function (ch) { var k = document.createElement("span"); k.className = "e-ch"; k.style.display = "inline-block"; k.textContent = ch; s.appendChild(k); out.push(k); });
            }
            frag.appendChild(s);
          });
          c.parentNode.replaceChild(frag, c);
        } else if (c.nodeType === 1 && c.tagName !== "BR" && c.tagName !== "svg") { walk(c); }
      });
    })(el);
    el.__split = out;
    return out;
  }

  // ---- the vocabulary: set(el, on) paints the start (on=false) or final (on=true) state; play(el) animates start -> final ----
  var V = {};
  V["in"] = {
    set: function (el) { clear(el); },
    play: function (el, o) {
      o = o || {};
      var dy = o.dy === undefined ? 30 : o.dy, B = T.blur;
      return tw(T["in"], o.at || 0, "snap", function (e) {
        el.style.opacity = clamp(e * 2.5);
        el.style.transform = e >= 1 ? "" : "translateY(" + (dy * (1 - e)).toFixed(1) + "px)";
        el.style.filter = e >= 1 ? "" : "blur(" + (B * (1 - e)).toFixed(2) + "px)";
      }, function () { clear(el); });
    }
  };
  V.big = {
    set: function (el, on) { split(el, "ch").forEach(function (c) { c.style.opacity = on ? "" : 0; c.style.transform = ""; c.style.filter = ""; }); },
    play: function (el) {
      split(el, "ch").forEach(function (c, i) {
        var r = ((i * 37) % 9 - 4) * 2.2;
        tw(T.m, i * T.stagger, "linear", function (e, t) {
          var p = EZ.snap(clamp(t / 0.7)), k = EZ.spring(t);
          c.style.opacity = clamp(t * 6);
          c.style.transform = t >= 1 ? "" : "translateY(" + (-0.42 * (1 - p)).toFixed(3) + "em) rotate(" + (r * (1 - k)).toFixed(2) + "deg)";
          c.style.filter = t >= 1 ? "" : "blur(" + (7 * (1 - p)).toFixed(2) + "px)";
        });
      });
    }
  };
  function paths(el) { return qa(el, "path,line,polyline,circle,rect,ellipse").filter(function (p) { return !p.closest("defs"); }); }
  // ---- pen marks from data-e-marks='[{"mark":"circle|box|under|arrow","text":"83%"} | {"x":..,"y":..,"w":..,"h":..}, "note":"..","color":"cool|acc"}]' ----
  function seeded(n) { var x = n * 9301 + 49297; return function () { x = (x * 9301 + 49297) % 233280; return x / 233280; }; }
  function wob(p, amp, seed) {   // a hand-drawn line through the points (Catmull-Rom, small seeded wobble)
    var R = seeded(seed);
    p = p.map(function (q, i) { var j = (i === 0 || i === p.length - 1) ? 0.3 : 1; return [q[0] + (R() - 0.5) * amp * j, q[1] + (R() - 0.5) * amp * j]; });
    var d = "M" + p[0][0].toFixed(1) + " " + p[0][1].toFixed(1);
    for (var i = 0; i < p.length - 1; i++) {
      var a = p[i - 1] || p[i], b = p[i], c = p[i + 1], e = p[i + 2] || c;
      d += " C" + (b[0] + (c[0] - a[0]) / 6).toFixed(1) + " " + (b[1] + (c[1] - a[1]) / 6).toFixed(1) + " " + (c[0] - (e[0] - b[0]) / 6).toFixed(1) + " " + (c[1] - (e[1] - b[1]) / 6).toFixed(1) + " " + c[0].toFixed(1) + " " + c[1].toFixed(1);
    }
    return d;
  }
  function findText(sc, txt) {   // the on-screen box of the first place the slide's text holds txt, even across split syllables (slide px)
    var w = document.createTreeWalker(sc, NodeFilter.SHOW_TEXT, null, false), n, nodes = [], all = "";
    while ((n = w.nextNode())) {
      if (n.parentNode.closest && n.parentNode.closest(".e-pen, .e-note, #notes, .bgart, [aria-hidden='true']")) continue;
      nodes.push({ n: n, at: all.length }); all += n.textContent;
    }
    var i = all.indexOf(txt), j = i + txt.length;
    if (i < 0) return null;
    function pos(k, end) { for (var q = nodes.length - 1; q >= 0; q--) { if (nodes[q].at < k || (!end && nodes[q].at === k)) return [nodes[q].n, k - nodes[q].at]; } return [nodes[0].n, 0]; }
    var A = pos(i, false), B = pos(j, true), r = document.createRange();
    r.setStart(A[0], A[1]); r.setEnd(B[0], B[1]);
    var a = r.getBoundingClientRect(), b = sc.getBoundingClientRect(), s = scaleOf(sc) || 1;
    return a.width ? { x: (a.left - b.left) / s, y: (a.top - b.top) / s, w: a.width / s, h: a.height / s } : null;
  }
  function buildMarks(el) {
    if (el.__marks) return;
    var list = [];
    try { list = JSON.parse(el.getAttribute("data-e-marks") || "[]"); } catch (e) { list = []; }
    var sc = el.closest(".sl, section") || document.body, NS = "http://www.w3.org/2000/svg", keys = [];
    if (!sc.offsetWidth) return;   // not on screen yet: measure on the next call
    el.__marks = 1;
    list.forEach(function (m, k) {
      var r = m.text ? findText(sc, String(m.text)) : (m.w ? { x: +m.x, y: +m.y, w: +m.w, h: +m.h } : null);
      if (!r) return;
      var pad = 14, x0 = r.x - pad, y0 = r.y - pad * 0.6, x1 = r.x + r.w + pad, y1 = r.y + r.h + pad * 0.6, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, d, i, pts = [];
      var kind = m.mark || "circle";
      if (kind === "under") d = wob([[r.x - 4, r.y + r.h - 6], [r.x + r.w * 0.5, r.y + r.h - 1], [r.x + r.w + 6, r.y + r.h - 8]], 5, k + 3);   // inside the descent area: never on the next line
      else if (kind === "box") d = wob([[x0 + 30, y0 - 4], [x1, y0 + 2], [x1 + 4, y1], [x0, y1 + 3], [x0 - 3, y0 + 8], [x0 + 60, y0 - 6]], 6, k + 5);
      else if (kind === "arrow") { var ax = x1 + 140, ay = y0 - 90; d = wob([[ax, ay], [(ax + x1) / 2 + 20, (ay + cy) / 2 - 10], [x1 + 6, cy - 6]], 8, k + 7) + " M" + (x1 + 30).toFixed(1) + " " + (cy - 30).toFixed(1) + " L" + (x1 + 6).toFixed(1) + " " + (cy - 6).toFixed(1) + " L" + (x1 + 36).toFixed(1) + " " + (cy + 2).toFixed(1); }
      else {   // a loop that hugs the words (superellipse, n = 4): it never cuts through the neighbouring letters
        for (i = 0; i <= 26; i++) {
          var a = -2.2 + (Math.PI * 2 + 0.45) * i / 26, g = 1 + 0.04 * i / 26, ca = Math.cos(a), sa = Math.sin(a);
          pts.push([cx + (ca < 0 ? -1 : 1) * Math.sqrt(Math.abs(ca)) * ((x1 - x0) / 2 + 6) * g, cy + (sa < 0 ? -1 : 1) * Math.sqrt(Math.abs(sa)) * ((y1 - y0) / 2 + 6) * g]);
        }
        d = wob(pts, 6, k + 1);
      }
      var p = document.createElementNS(NS, "path"); p.setAttribute("d", d); if (m.color === "acc") p.setAttribute("class", "e-acc"); el.appendChild(p);
      if (m.note) {
        var n = mk("div", "e-note" + (m.color === "acc" ? " e-acc" : ""), sc); n.textContent = m.note; n.setAttribute("data-e-mark", String(k));
        var nx = kind === "arrow" ? x1 + 150 : x1 + 18, ny = kind === "arrow" ? y0 - 150 : y0 - 54;
        n.style.left = Math.max(96, Math.min(nx, 1920 - 96 - n.offsetWidth)) + "px"; n.style.top = Math.max(60, ny) + "px";
        keys.push(n);
      }
    });
    el.__notes = keys;
  }
  V.pen = {
    set: function (el, on) {
      if (el.hasAttribute("data-e-marks")) buildMarks(el);
      paths(el).forEach(function (p) { p.setAttribute("pathLength", "1"); p.style.strokeDasharray = "1"; p.style.strokeDashoffset = on ? "0" : "1"; });
      notes(el).forEach(function (n) { V.note.set(n, on); });
    },
    play: function (el) {
      if (el.hasAttribute("data-e-marks")) buildMarks(el);
      var ps = paths(el), each = T.pen / Math.max(1, ps.length) + 80;
      ps.forEach(function (p, i) { tw(each, i * each * 0.8, "inout", function (e) { p.style.strokeDashoffset = (1 - e).toFixed(4); }); });
      notes(el).forEach(function (n, i) { V.note.play(n, { at: ps.length * each * 0.8 + i * T.gap }); });
    }
  };
  function notes(el) { if (el.__notes) return el.__notes; var sc = el.closest(".sl, section, body") || document.body, key = el.getAttribute("data-e-notes"); return key ? qa(sc, key) : []; }
  V.note = {
    set: function (el, on) { el.style.visibility = on ? "visible" : "hidden"; el.style.clipPath = ""; },
    play: function (el, o) {
      el.style.visibility = "visible";
      tw(300, (o && o.at) || 0, "out", function (e) { el.style.clipPath = e >= 1 ? "" : "inset(-20% " + ((1 - e) * 100).toFixed(1) + "% -20% -4%)"; });
    }
  };
  V.hl = {
    set: function (el, on) { split(el, "word").forEach(function (w) { w.classList.toggle("e-lit", !!on); }); el.style.visibility = ""; },
    play: function (el) {
      split(el, "word").forEach(function (w, i) {
        w.classList.remove("e-lit");
        tw(1, i * T.word, "linear", function (e, t) { if (t >= 1) w.classList.add("e-lit"); });
      });
    }
  };
  V.dot = {   // the element is the final rule; a dot falls onto its left end, then stretches into it
    set: function (el, on) { clear(el); el.style.borderRadius = ""; el.style.opacity = on ? "" : 0; el.style.transformOrigin = "0 50%"; },
    play: function (el) {
      var w = el.offsetWidth || 96, h = el.offsetHeight || 8, d = Math.max(h, 26) / w;
      el.style.transformOrigin = "0 50%";
      tw(T.m, 0, "snap", function (e) {
        el.style.opacity = clamp(e * 3);
        el.style.borderRadius = "999px";
        el.style.transform = "translateY(" + (-120 * (1 - e)).toFixed(1) + "px) scale(" + d.toFixed(4) + "," + (Math.max(26, h) / h).toFixed(3) + ")";
        el.style.filter = e >= 1 ? "" : "blur(" + (6 * (1 - e)).toFixed(2) + "px)";
      });
      tw(T.l, T.m + T.gap, "inout", function (e) {
        var sx = lerp(d, 1, e), sy = lerp(Math.max(26, h) / h, 1, e);
        el.style.transform = e >= 1 ? "" : "scale(" + sx.toFixed(4) + "," + sy.toFixed(3) + ")";
        if (e >= 1) el.style.borderRadius = "";
      }, function () { clear(el); }, true);
    }
  };
  V.pills = {
    step: function (el, k, instant) {
      var ps = [].slice.call(el.children), cur = -1;
      var fixed = el.getAttribute("data-e-cur");   // a sequence across slides: this slide is pill n (fills on open)
      if (fixed !== null) cur = +fixed;
      else ps.forEach(function (p, i) { var at = p.hasAttribute("data-b") ? +p.getAttribute("data-b") : i; if (at <= k) cur = i; });
      ps.forEach(function (p, i) {
        var bar = p.querySelector("i") || mk("i", "", p);
        if (p.firstChild !== bar) p.insertBefore(bar, p.firstChild);
        p.classList.toggle("e-cur", i === cur);
        if (i === cur && !instant && el.__cur !== cur) {
          tw(T.l, 0, "out", function (e) { bar.style.transform = "scaleX(" + e.toFixed(4) + ")"; });
        } else { bar.style.transform = i <= cur ? "scaleX(1)" : "scaleX(0)"; }
      });
      el.__cur = cur;
    }
  };

  // ---- cursors: a labelled arrow that moves with purpose (fast start, soft stop), presses, drags ----
  var PTR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2.5 L4 19.5 L8.6 15.3 L11.8 22 L14.9 20.6 L11.8 14 L18.2 13.6 Z"/></svg>';
  function cur(el) { if (!el.__p) { el.insertAdjacentHTML("afterbegin", PTR); el.__p = { x: 0, y: 0 }; mk("i", "e-ring", el); } return el; }
  function curAt(c, x, y) { c.__p = { x: x, y: y }; c.style.transform = "translate(" + x.toFixed(1) + "px," + y.toFixed(1) + "px)"; }
  function curGo(c, x, y, at, dur, done) { var x0, y0; return tw(dur, at, "out", function (e) { if (x0 === undefined) { x0 = c.__p.x; y0 = c.__p.y; } curAt(c, lerp(x0, x, e), lerp(y0, y, e)); }, done, true); }
  function curClick(c, at) { var r = c.querySelector(".e-ring"); tw(T.l, at, "out", function (e) { r.style.opacity = (1 - e).toFixed(3); r.style.transform = "scale(" + lerp(0.4, 1.8, e).toFixed(3) + ")"; }, null, true); }
  function pts(s) { return String(s || "").trim().split(/\s+/).filter(Boolean).map(function (p) { var q = p.split(","); return [+q[0], +q[1]]; }); }
  function result(el, on, at) {
    var sc = el.closest(".sl, section, body") || document.body, sel = el.getAttribute("data-e-result"), r = sel ? sc.querySelector(sel) : null;
    if (!r) return;
    if (on === "play") { r.style.visibility = "visible"; V["in"].play(r, { at: at, dy: 12 }); } else { clear(r); r.style.visibility = on ? "visible" : "hidden"; }
  }
  V.cursor = {   // data-e-path="x,y x,y ..." (in the parent's px), data-e-click="1 3" (which points click), data-e-result="#sel"
    set: function (el, on) { cur(el); var p = pts(el.getAttribute("data-e-path")), last = p[p.length - 1] || [0, 0]; curAt(el, last[0], last[1]); el.style.opacity = on ? 1 : 0; result(el, on); },
    play: function (el) {
      cur(el); var p = pts(el.getAttribute("data-e-path")), clicks = (el.getAttribute("data-e-click") || "").split(/\s+/).map(Number), at = 0;
      if (!p.length) return;
      curAt(el, p[0][0], p[0][1]); el.style.opacity = 1; result(el, false);
      for (var i = 1; i < p.length; i++) { curGo(el, p[i][0], p[i][1], at, T.cursor); at += T.cursor + T.gap; if (clicks.indexOf(i) >= 0) { curClick(el, at - T.gap); at += T.s; } }
      result(el, "play", at);
    }
  };
  // drag scene: <div class="e-board" data-e="drag" data-e-result="#out">
  //   <div class="e-item" data-e-from="x,y" style="left:..;top:..">  (its CSS left/top = where it ends)
  //   <div class="e-cur" data-e-for="0"><b>이름</b></div>  (one labelled cursor per item, colour via --e-cc)
  V.drag = {
    parts: function (el) { return { items: qa(el, ".e-item"), curs: qa(el, ".e-cur").map(cur), sel: el.querySelector(".e-sel") || mk("div", "e-sel", el), gv: el.querySelector(".e-guide.v") || mk("i", "e-guide v", el), gh: el.querySelector(".e-guide.h") || mk("i", "e-guide h", el) }; },
    set: function (el, on) {
      var P = V.drag.parts(el);
      P.items.forEach(function (it) { var f = pts(it.getAttribute("data-e-from"))[0] || [0, 0]; it.style.transform = on ? "" : "translate(" + f[0] + "px," + f[1] + "px)"; });
      P.curs.forEach(function (c) { c.style.opacity = 0; c.classList.remove("e-grab"); });
      [P.sel, P.gv, P.gh].forEach(function (g) { g.style.opacity = 0; });
      result(el, on);
    },
    play: function (el) {
      var P = V.drag.parts(el), at = 0;
      V.drag.set(el, false);
      P.items.forEach(function (it, n) {
        var c = P.curs.filter(function (k) { return +k.getAttribute("data-e-for") === n; })[0] || P.curs[n % Math.max(1, P.curs.length)];
        if (!c) return;
        var f = pts(it.getAttribute("data-e-from"))[0] || [0, 0], x1 = it.offsetLeft, y1 = it.offsetTop, w = it.offsetWidth, h = it.offsetHeight;
        var sx = x1 + f[0] + w * 0.6, sy = y1 + f[1] + h * 0.55;
        tw(1, at, "linear", function (e, t) { if (t >= 1) { curAt(c, sx + 140, sy + 90); c.style.opacity = 1; } });
        curGo(c, sx, sy, at + 10, T.cursor);
        at += T.cursor + T.gap;
        tw(1, at, "linear", function (e, t) { if (t >= 1) c.classList.add("e-grab"); });
        tw(T.cursor + T.l, at + T.xs, "inout", function (e) {
          it.style.transform = e >= 1 ? "" : "translate(" + (f[0] * (1 - e)).toFixed(1) + "px," + (f[1] * (1 - e)).toFixed(1) + "px)";
          curAt(c, x1 + f[0] * (1 - e) + w * 0.6, y1 + f[1] * (1 - e) + h * 0.55);
          var near = e > 0.82;
          P.gv.style.cssText = "left:" + (x1 + w / 2) + "px;top:-30px;bottom:-30px;width:1.5px;opacity:" + (near ? 1 : 0);
          P.gh.style.cssText = "top:" + y1 + "px;left:-30px;right:-30px;height:1.5px;opacity:" + (near ? 1 : 0);
          P.sel.style.cssText = "left:" + (x1 + f[0] * (1 - e)) + "px;top:" + (y1 + f[1] * (1 - e)) + "px;width:" + w + "px;height:" + h + "px;opacity:1";
        }, null, true);
        at += T.cursor + T.l + T.xs + T.gap;
        tw(T.s, at, "out", function (e) { c.classList.remove("e-grab"); P.gv.style.opacity = P.gh.style.opacity = (1 - e).toFixed(3); c.style.opacity = (1 - e).toFixed(3); }, null, true);
        at += T.s;
      });
      tw(T.s, at, "out", function (e) { P.sel.style.opacity = (1 - e).toFixed(3); }, null, true);
      result(el, "play", at + T.gap);   // the scene ends on the real result, never on the cursor
    }
  };

  // ---- HUD frame ----
  function hud(sl, i, n) {
    var h = sl.querySelector(":scope > .e-hud");
    if (!h) { h = mk("div", "e-hud", sl, "<i></i><i></i><i></i><i></i><u><b></b></u>"); h.setAttribute("aria-hidden", "true"); }
    var b = h.querySelector("u>b"), x = n > 1 ? i / (n - 1) : 0;
    b.style.left = (x * 100).toFixed(2) + "%";
    return h;
  }

  // ---- the step driver ----
  function stepAt(el) { var b = el.getAttribute("data-b"); return b === null ? 0 : +b; }
  function stillMode() { return RM || document.body.classList.contains("noanim") || document.body.classList.contains("printing"); }
  function step(sl, k, instant) {
    if (!sl) return;
    instant = instant || stillMode();
    if (sl.__k === undefined || k === 0) { sl.__visit = ++visit; }
    var fwd = !instant && sl.__k !== undefined && k === sl.__k + 1 || (!instant && k === 0);
    if (k === 0 || instant) stopAll();
    sl.__k = k;
    qa(sl, "[data-e]").forEach(function (el) {
      var kind = el.getAttribute("data-e"), v = V[kind];
      if (!v) return;
      if (kind === "pills") { v.step(el, k, instant); return; }
      var at = stepAt(el);
      if (at > k) { v.set(el, false); return; }
      if (at < k || instant || !fwd || el.__seen === sl.__visit) { v.set(el, true); el.__seen = sl.__visit; return; }
      el.__seen = sl.__visit;
      v.set(el, false);
      v.play(el);
    });
    if (document.body.classList.contains("e-motion")) {   // E mode: every other build entrance is the fast blur-in
      qa(sl, ".b[data-b]:not([data-e])").forEach(function (el) {
        if (!instant && fwd && stepAt(el) === k && el.__seen !== sl.__visit) { el.__seen = sl.__visit; V["in"].play(el); } else if (stepAt(el) <= k) { el.__seen = sl.__visit; clear(el); }
      });
    }
  }
  function maxStep(sl) { var m = 0; qa(sl, "[data-b]").forEach(function (e) { m = Math.max(m, +e.getAttribute("data-b")); }); return m; }
  function auto(root) {   // stand-alone pages: the whole page is one "slide" stepped with → / ← / click
    root = root || document.body;
    var k = 0, m = maxStep(root);
    function show(n, inst) { k = Math.max(0, Math.min(m, n)); qa(root, "[data-b]").forEach(function (e) { e.classList.toggle("on", +e.getAttribute("data-b") <= k); }); step(root, k, inst); }
    document.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); show(k + 1); }
      if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); show(k - 1, true); }
    });
    root.addEventListener("click", function (e) { if (!(e.target.closest && e.target.closest("a,button,input,textarea,select"))) show(k + 1); });
    show(/[?&]static=1/.test(location.search) ? m : 0, /[?&]static=1/.test(location.search));
    return { show: show, get: function () { return k; }, max: m };
  }
  return { step: step, hud: hud, auto: auto, tw: tw, stop: stopAll, split: split, V: V, T: T, reduced: function () { return stillMode(); } };
})();
