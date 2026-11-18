/* THEME spotlight — stage-light beams for show-style games. Beam count follows tokens.motion; colors from tokens. */
COMP.themes.spotlight = { paint: function(ctx, t, dt, W, Hh, TK){
  var g = ctx.createRadialGradient(W / 2, Hh * 0.15, 80, W / 2, Hh * 0.5, Hh); g.addColorStop(0, TK.colors.bg2); g.addColorStop(1, TK.colors.bg1);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, Hh);
  var n = TK.motion === "calm" ? 2 : 4, k = TK.motion === "calm" ? 0.3 : 1;
  ctx.globalAlpha = 0.10; ctx.fillStyle = TK.colors.primary;
  for (var i = 0; i < n; i++){
    var x = W * (i + 0.5) / n, a = Math.sin(t * 0.6 * k + i * 1.7) * 0.35;
    ctx.save(); ctx.translate(x, -20); ctx.rotate(a); ctx.beginPath(); ctx.moveTo(-30, 0); ctx.lineTo(30, 0); ctx.lineTo(220, Hh * 1.2); ctx.lineTo(-220, Hh * 1.2); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  ctx.globalAlpha = 1;
} };
