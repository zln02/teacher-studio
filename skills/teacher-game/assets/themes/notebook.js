/* THEME notebook — ruled-paper look for personal / writing-heavy games (static, no motion). Colors from tokens. */
COMP.themes.notebook = { paint: function(ctx, t, dt, W, Hh, TK){
  ctx.fillStyle = TK.colors.bg1; ctx.fillRect(0, 0, W, Hh);
  ctx.strokeStyle = TK.colors.cardBorder; ctx.globalAlpha = 0.25; ctx.lineWidth = 2;
  for (var y = 140; y < Hh; y += 70){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.strokeStyle = TK.colors.accent; ctx.globalAlpha = 0.35; ctx.beginPath(); ctx.moveTo(110, 0); ctx.lineTo(110, Hh); ctx.stroke(); ctx.globalAlpha = 1;
} };
