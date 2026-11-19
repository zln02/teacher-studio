/* TS:JUICE-MOTION v1 - ten generic motion techniques, implemented from scratch (no third-party code).
   Needs juice.js first. Every effect is a small function; when motion is reduced (OS setting or the in-page switch)
   it does the quiet version (instant state / soft fade) and still calls onDone. Heavy blur is avoided on purpose. */
(function (root) {
  'use strict';
  var J = root.Juice, doc = root.document, fx = J.fx = {};
  function later(fn, ms) { return root.setTimeout(fn, ms); }
  function rm(n) { if (n && n.parentNode) n.parentNode.removeChild(n); }
  function mk(tag, cls, css) { var e = doc.createElement(tag); if (cls) e.className = cls; if (css) e.style.cssText = css; return e; }
  function done(o) { if (o && o.onDone) o.onDone(); }

  /* 1. Impact frame: one hard "hit" beat - faint tint + radial speed lines for ~140ms. One flash only (governed), never strobes. */
  fx.impactFrame = function (o) {
    o = o || {};
    if (J.reduced()) { done(o); return; }
    J.flash(o.color || '#ffffff', 0.1, 120);
    var d = mk('div', 'juice-impact'); doc.body.appendChild(d);
    var a = J.anim(d, [{ opacity: 0, transform: 'scale(1.15)' }, { opacity: 0.55, transform: 'scale(1)', offset: 0.3 }, { opacity: 0, transform: 'scale(1)' }], { duration: o.ms || 260, easing: 'ease-out' });
    later(function () { rm(d); done(o); }, a ? (o.ms || 260) + 20 : 10);
  };
  /* 2. Letter dive titles: each letter dives in from above with a small overshoot, staggered. */
  fx.letterDive = function (el, o) {
    o = o || {};
    if (!el) return; var txt = o.text || el.textContent; el.setAttribute('aria-label', txt); el.textContent = '';
    var stg = o.stagger || 38, spans = [];
    Array.prototype.forEach.call(txt, function (c) { var s = mk('span', 'jl'); s.setAttribute('aria-hidden', 'true'); s.textContent = c === ' ' ? ' ' : c; s.style.display = 'inline-block'; if (c === ' ') s.style.whiteSpace = 'pre'; el.appendChild(s); spans.push(s); });
    if (J.reduced()) { done(o); return; }
    spans.forEach(function (s, i) {
      J.anim(s, [{ transform: 'translateY(-' + (o.dist || 90) + 'px) scale(1.5)', opacity: 0 }, { transform: 'translateY(6px) scale(.96)', opacity: 1, offset: 0.7 }, { transform: 'translateY(0) scale(1)', opacity: 1 }], { duration: 520, delay: i * stg, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards' });
    });
    later(function () { done(o); }, 520 + spans.length * stg);
  };
  /* 3. Layer explode: the children of a container fly apart from the centre ("out"), or fly back together ("in"). */
  fx.layerExplode = function (box, o) {
    o = o || {}; var kids = Array.prototype.slice.call(box.children), mode = o.mode || 'out', R = o.radius || 120;
    if (J.reduced() || !kids.length) { done(o); return; }
    kids.forEach(function (k, i) {
      var a = (i / kids.length) * 6.2832 + 0.5, dx = Math.cos(a) * R, dy = Math.sin(a) * R, rot = (i % 2 ? 1 : -1) * 12;
      var far = 'translate(' + dx.toFixed(0) + 'px,' + dy.toFixed(0) + 'px) rotate(' + rot + 'deg) scale(1.08)', home = 'translate(0,0) rotate(0) scale(1)';
      J.anim(k, mode === 'out' ? [{ transform: home, opacity: 1 }, { transform: far, opacity: 0.0 }] : [{ transform: far, opacity: 0 }, { transform: home, opacity: 1 }],
        { duration: o.ms || 620, delay: i * 30, easing: 'cubic-bezier(.22,1,.36,1)', fill: mode === 'out' ? 'forwards' : 'backwards' });
    });
    later(function () { done(o); }, (o.ms || 620) + kids.length * 30);
  };
  /* 4. Rack focus: attention moves - the target stays sharp, the others soften by at most 3px and dim a little. */
  fx.rackFocus = function (target, others, o) {
    o = o || {}; var b = Math.min(3, o.blur == null ? 3 : o.blur);
    (others || []).forEach(function (e) {
      if (J.reduced()) { e.style.opacity = o.clear ? '' : '0.6'; return; }
      e.style.transition = 'filter 360ms ease, opacity 360ms ease';
      e.style.filter = o.clear ? '' : 'blur(' + b + 'px)'; e.style.opacity = o.clear ? '' : '0.6';
    });
    if (target) { target.style.filter = ''; target.style.opacity = ''; }
    later(function () { done(o); }, J.reduced() ? 0 : 380);
  };
  /* 5. Dolly zoom (reveal): the subject grows while its backdrop shrinks the other way, so the subject "jumps out". */
  fx.dollyZoom = function (subject, backdrop, o) {
    o = o || {}; var k = o.amount || 0.1, ms = o.ms || 800;
    if (J.reduced()) { done(o); return; }
    var e = 'cubic-bezier(.45,0,.2,1)';
    J.anim(subject, [{ transform: 'scale(.9)' }, { transform: 'scale(' + (1 + k) + ')', offset: 0.7 }, { transform: 'scale(1)' }], { duration: ms, easing: e });
    if (backdrop) J.anim(backdrop, [{ transform: 'scale(' + (1 + k) + ')' }, { transform: 'scale(1)' }], { duration: ms, easing: e });
    later(function () { done(o); }, ms);
  };
  /* 6. Paper tear (transition): a paper sheet covers the screen, tears down a jagged line and the halves slide away.
        fx.paperTear({color, ms, onMid, onDone}) - call your scene change inside onMid (screen is fully covered then). */
  fx.paperTear = function (o) {
    o = o || {};
    if (J.reduced()) { if (o.onMid) o.onMid(); done(o); return; }
    var col = o.color || '#f4efe4', ms = o.ms || 700, pts = [], i, n = 14, W = 100;
    for (i = 0; i <= n; i++) pts.push((50 + (i % 2 ? 3 : -3) + (Math.random() * 3 - 1.5)).toFixed(1) + '% ' + (i * 100 / n).toFixed(1) + '%');
    var L = mk('div', 'juice-paper', 'background:' + col + ';clip-path:polygon(0 0,' + pts.join(',') + ',0 100%)');
    var R = mk('div', 'juice-paper', 'background:' + col + ';clip-path:polygon(100% 0,' + pts.join(',') + ',100% 100%)');
    doc.body.appendChild(L); doc.body.appendChild(R);
    J.anim(L, [{ opacity: 0 }, { opacity: 1 }], { duration: 160, fill: 'forwards' }); J.anim(R, [{ opacity: 0 }, { opacity: 1 }], { duration: 160, fill: 'forwards' });
    later(function () {
      if (o.onMid) o.onMid(); J.sound.play('whoosh');
      J.anim(L, [{ transform: 'translateX(0) rotate(0)' }, { transform: 'translateX(-' + W + '%) rotate(-4deg)' }], { duration: ms, easing: 'cubic-bezier(.65,0,.35,1)', fill: 'forwards' });
      J.anim(R, [{ transform: 'translateX(0) rotate(0)' }, { transform: 'translateX(' + W + '%) rotate(4deg)' }], { duration: ms, easing: 'cubic-bezier(.65,0,.35,1)', fill: 'forwards' });
      later(function () { rm(L); rm(R); done(o); }, ms + 40);
    }, 220);
  };
  /* 7. Blade slice: the element is cut along a diagonal; the two halves part and fade (right/wrong split, removing a card). */
  fx.bladeSlice = function (el, o) {
    o = o || {}; if (!el) { done(o); return; }
    if (J.reduced()) { el.style.opacity = '0.4'; done(o); return; }
    var r = el.getBoundingClientRect(), ms = o.ms || 520, ang = o.angle == null ? -14 : o.angle;
    function half(clip, dx, dy) {
      var c = el.cloneNode(true); c.removeAttribute('id'); c.style.cssText += ';position:fixed;left:' + r.left + 'px;top:' + r.top + 'px;width:' + r.width + 'px;height:' + r.height + 'px;margin:0;z-index:9000;pointer-events:none;clip-path:' + clip;
      doc.body.appendChild(c);
      J.anim(c, [{ transform: 'translate(0,0) rotate(0)', opacity: 1 }, { transform: 'translate(' + dx + 'px,' + dy + 'px) rotate(' + (dx > 0 ? 3 : -3) + 'deg)', opacity: 0 }], { duration: ms, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'forwards' });
      later(function () { rm(c); }, ms + 40);
    }
    var t = Math.tan(ang * Math.PI / 180) * 50;
    half('polygon(0 0,100% 0,100% ' + (50 + t) + '%,0 ' + (50 - t) + '%)', -10, -28); /* top half drifts up-left */
    half('polygon(0 ' + (50 - t) + '%,100% ' + (50 + t) + '%,100% 100%,0 100%)', 10, 28);
    el.style.visibility = 'hidden';
    var line = mk('div', 'juice-slash', 'left:' + (r.left - 20) + 'px;top:' + (r.top + r.height / 2) + 'px;width:' + (r.width + 40) + 'px;transform:rotate(' + ang + 'deg)');
    doc.body.appendChild(line); J.anim(line, [{ opacity: 0, transform: 'rotate(' + ang + 'deg) scaleX(0)' }, { opacity: 1, transform: 'rotate(' + ang + 'deg) scaleX(1)', offset: 0.4 }, { opacity: 0, transform: 'rotate(' + ang + 'deg) scaleX(1)' }], { duration: 320, easing: 'ease-out' });
    later(function () { rm(line); if (o.restore) el.style.visibility = ''; done(o); }, ms);
  };
  /* 8. Sketch words: a hand-drawn underline (or circle) is "written" under/around the text. */
  fx.sketchWords = function (el, o) {
    o = o || {}; if (!el) { done(o); return null; }
    var ns = 'http:' + '//www.w3.org/2000/svg', r = el.getBoundingClientRect(), host = el.offsetParent || el.parentNode;
    var svg = doc.createElementNS(ns, 'svg'), p = doc.createElementNS(ns, 'path'), w = Math.max(40, r.width), h = 22;
    svg.setAttribute('viewBox', '0 0 ' + w.toFixed(0) + ' ' + h); svg.setAttribute('class', 'juice-sketch'); svg.setAttribute('aria-hidden', 'true');
    svg.style.cssText = 'position:absolute;left:' + (el.offsetLeft) + 'px;top:' + (el.offsetTop + el.offsetHeight - 8) + 'px;width:' + w + 'px;height:' + h + 'px;pointer-events:none;overflow:visible';
    var d = 'M2 ' + (h * 0.6).toFixed(1), x, seg = Math.max(3, Math.round(w / 60));
    for (x = 1; x <= seg; x++) d += ' Q' + ((x - 0.5) * w / seg).toFixed(1) + ' ' + (h * (x % 2 ? 0.1 : 0.95)).toFixed(1) + ' ' + (x * w / seg - 2).toFixed(1) + ' ' + (h * (0.5 + 0.12 * (x % 2 ? 1 : -1))).toFixed(1);
    p.setAttribute('d', d); p.setAttribute('fill', 'none'); p.setAttribute('stroke', o.color || 'var(--accent, #ffd447)'); p.setAttribute('stroke-width', o.width || 6); p.setAttribute('stroke-linecap', 'round');
    svg.appendChild(p); if (host) { if (root.getComputedStyle(host).position === 'static') host.style.position = 'relative'; host.appendChild(svg); }
    var len = p.getTotalLength ? p.getTotalLength() : w; p.style.strokeDasharray = len; p.style.strokeDashoffset = J.reduced() ? 0 : len;
    if (!J.reduced()) { p.style.transition = 'stroke-dashoffset ' + (o.ms || 650) + 'ms ease-out'; root.requestAnimationFrame(function () { root.requestAnimationFrame(function () { p.style.strokeDashoffset = 0; }); }); }
    later(function () { done(o); }, J.reduced() ? 0 : (o.ms || 650));
    return svg;
  };
  /* 9. Orbit ring (timer / loading): a ring with a dot orbiting it. ctl.set(fraction 0..1) fills it; ctl.spin() loops (loading). */
  fx.orbitRing = function (box, o) {
    o = o || {}; var ns = 'http:' + '//www.w3.org/2000/svg', S = o.size || 160, c = S / 2, r = S / 2 - 12, C = 2 * Math.PI * r;
    var svg = doc.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 ' + S + ' ' + S); svg.setAttribute('class', 'juice-orbit'); svg.setAttribute('aria-hidden', 'true'); svg.style.cssText = 'width:' + S + 'px;height:' + S + 'px';
    svg.innerHTML = '<circle cx="' + c + '" cy="' + c + '" r="' + r + '" fill="none" stroke="currentColor" stroke-opacity=".2" stroke-width="8"/>' +
      '<circle class="jo-prog" cx="' + c + '" cy="' + c + '" r="' + r + '" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round" stroke-dasharray="' + C.toFixed(1) + '" stroke-dashoffset="0" transform="rotate(-90 ' + c + ' ' + c + ')"/>' +
      '<g class="jo-dot"><circle cx="' + c + '" cy="' + (c - r) + '" r="9" fill="var(--accent,currentColor)"/></g>';
    box.appendChild(svg);
    var prog = svg.querySelector('.jo-prog'), dot = svg.querySelector('.jo-dot'), spinning = false, ang = 0, raf = 0;
    var ctl = {
      el: svg,
      set: function (f) { f = Math.max(0, Math.min(1, f)); prog.style.strokeDashoffset = (C * (1 - f)).toFixed(1); dot.setAttribute('transform', 'rotate(' + (f * 360).toFixed(1) + ' ' + c + ' ' + c + ')'); },
      spin: function () { if (J.reduced() || spinning) return; spinning = true; prog.style.strokeDashoffset = (C * 0.75).toFixed(1); (function f() { if (!spinning) return; ang = (ang + 5) % 360; svg.style.transform = 'rotate(' + ang + 'deg)'; raf = root.requestAnimationFrame(f); })(); },
      stop: function () { spinning = false; root.cancelAnimationFrame(raf); svg.style.transform = ''; }
    };
    return ctl;
  };
  /* 10. Day dial (schedule): a 12-slot clock face for a day plan. slots: [{label, from, to}] in hours (0-24); ctl.hand(hour) points the hand. */
  fx.dayDial = function (box, o) {
    o = o || {}; var ns = 'http:' + '//www.w3.org/2000/svg', S = o.size || 320, c = S / 2, r = S / 2 - 10, slots = o.slots || [];
    var svg = doc.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 ' + S + ' ' + S); svg.setAttribute('class', 'juice-dial'); svg.style.cssText = 'width:' + S + 'px;height:' + S + 'px';
    var cols = ['var(--primary,#4a8)', 'var(--accent,#fa4)', 'var(--good,#4c8)', '#8a7bd8', '#e86f8a', '#4aa3d8'], h = '<circle cx="' + c + '" cy="' + c + '" r="' + r + '" fill="var(--card,#fff)" stroke="currentColor" stroke-width="3"/>';
    function pt(hr, rad) { var a = (hr / 12) * 2 * Math.PI - Math.PI / 2; return [(c + Math.cos(a) * rad).toFixed(1), (c + Math.sin(a) * rad).toFixed(1)]; }
    slots.forEach(function (s, i) {
      var a = pt(s.from % 12, r - 4), b = pt(s.to % 12, r - 4), big = ((s.to - s.from + 24) % 24) > 6 ? 1 : 0;
      h += '<path d="M' + c + ' ' + c + ' L' + a[0] + ' ' + a[1] + ' A' + (r - 4) + ' ' + (r - 4) + ' 0 ' + big + ' 1 ' + b[0] + ' ' + b[1] + ' Z" fill="' + cols[i % cols.length] + '" fill-opacity=".75"><title>' + String(s.label).replace(/</g, '') + '</title></path>';
    });
    for (var q = 0; q < 12; q++) { var p1 = pt(q, r - 2), p2 = pt(q, r - (q % 3 ? 12 : 22)); h += '<line x1="' + p1[0] + '" y1="' + p1[1] + '" x2="' + p2[0] + '" y2="' + p2[1] + '" stroke="currentColor" stroke-width="3"/>'; }
    h += '<g class="jd-hand"><line x1="' + c + '" y1="' + c + '" x2="' + c + '" y2="' + (c - r + 24) + '" stroke="currentColor" stroke-width="6" stroke-linecap="round"/></g><circle cx="' + c + '" cy="' + c + '" r="9" fill="currentColor"/>';
    svg.innerHTML = h; box.appendChild(svg);
    var hand = svg.querySelector('.jd-hand');
    var ctl = { el: svg, hand: function (hr, animate) {
      var deg = ((hr % 12) / 12 * 360).toFixed(1), tf = 'rotate(' + deg + ' ' + c + ' ' + c + ')';
      if (animate && !J.reduced()) { hand.style.transition = 'transform 700ms cubic-bezier(.34,1.56,.64,1)'; hand.style.transformOrigin = c + 'px ' + c + 'px'; hand.style.transform = 'rotate(' + deg + 'deg)'; } else { hand.setAttribute('transform', tf); }
    } };
    if (o.now != null) ctl.hand(o.now, false);
    return ctl;
  };
})(typeof window !== 'undefined' ? window : this);
