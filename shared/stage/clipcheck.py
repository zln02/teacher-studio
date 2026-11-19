# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Shared browser probe: is any answer text clipped by its button?

`window.__tsClip()` (injected with page.add_init_script(CLIP_JS)) returns [["clipped", "<class>", "<text>"], ...] for every visible choice / tile / chip /
button / card in the scene whose text lines stick out of the element's box or out of its ROUNDED shape (a 999px "pill" or a big radius cuts the corners
that the plain scrollWidth test cannot see: the 2026-11 compare run showed 3-4 line answers poking out of tall pills).
Used by check_game.py (autoplay), design_review.py (per screen) and the unit tests. Pure geometry, no screenshots.
"""
from __future__ import annotations

CLIP_JS = r"""
window.__tsClip = function(){
  var out = [], scene = document.querySelector('#scene .screen') || document.getElementById('scene') || document.body;
  var els = scene.querySelectorAll('.choice, .ts-choice, .ts-tile, .ts-chip, .btn, button, .card, [data-fit]');
  function rad(cs, w, h, sc){
    var v = ['borderTopLeftRadius', 'borderTopRightRadius', 'borderBottomRightRadius', 'borderBottomLeftRadius'].map(function(k){
      var m = String(cs[k]).match(/[\d.]+/); var n = m ? parseFloat(m[0]) : 0; if (/%/.test(cs[k])) n = n / 100 * Math.min(w, h); return n * sc; });
    return Math.min(Math.max.apply(null, v), Math.min(w, h) / 2);
  }
  for (var i = 0; i < els.length; i++){
    var e = els[i], cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.2) continue;
    var en = e.closest('.enter'); if (en && en.getAnimations && en.getAnimations().some(function(a){ return a.playState === 'running'; })) continue;   /* still sliding in */
    var r = e.getBoundingClientRect(); if (r.width < 20 || r.height < 20) continue;
    var sc = e.offsetWidth ? r.width / e.offsetWidth : 1, R = rad(cs, r.width, r.height, sc);
    var rot = /matrix/.test(cs.transform) ? Math.abs(parseFloat(cs.transform.match(/matrix\(([^,]+),([^,]+)/)[2])) : 0;
    var bwid = Math.max(parseFloat(cs.borderTopWidth) || 0, parseFloat(cs.borderLeftWidth) || 0, parseFloat(cs.borderRightWidth) || 0), bgm = String(cs.backgroundColor).match(/[\d.]+/g) || [],
        shown = bwid > 0 || cs.backgroundImage !== 'none' || (bgm.length < 4 || parseFloat(bgm[3]) > 0.05);   /* a visible plate: text must clear its border */
    var inset = shown ? (bwid + 12) * sc : 0, tol = 1 + rot * r.width * 0.5;   /* text must clear the border + a 12px margin */
    var bl = r.left + inset, bt = r.top + inset, br = r.right - inset, bb = r.bottom - inset, R2 = Math.max(0, R - inset);
    var tw = document.createTreeWalker(e, NodeFilter.SHOW_TEXT, null, false), nd, bad = '';
    while ((nd = tw.nextNode()) && !bad){
      var tx = nd.nodeValue.replace(/\s+/g, ' ').trim(); if (tx.length < 1 || !/[가-힣A-Za-z0-9]/.test(tx)) continue;
      var rg = document.createRange(); rg.selectNodeContents(nd);
      var rs = rg.getClientRects();
      for (var j = 0; j < rs.length && !bad; j++){
        var q = rs[j]; if (q.width < 2 || q.height < 2) continue;
        var hh = q.height * 0.14, pts = [[q.left, q.top + hh], [q.right, q.top + hh], [q.left, q.bottom - hh], [q.right, q.bottom - hh]];
        for (var p = 0; p < 4; p++){
          var x = pts[p][0], y = pts[p][1];
          if (x < bl - tol || x > br + tol || y < bt - tol || y > bb + tol){ bad = tx; break; }
          if (R2 > 4){
            var cx = Math.min(Math.max(x, bl + R2), br - R2), cy = Math.min(Math.max(y, bt + R2), bb - R2);
            if (Math.sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy)) > R2 + tol){ bad = tx; break; }
          }
        }
      }
    }
    if (bad){ var cn = (typeof e.className === 'string' && e.className ? e.className : e.tagName).split(' ').slice(0, 2).join('.'); out.push(['clipped', cn, bad.slice(0, 14)]); }
  }
  return out;
};
"""
