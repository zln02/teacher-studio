/* THEME default — generic look derived only from design tokens (no skin art): gradient + soft drifting shapes.
   Theme contract: COMP.themes.<id> = { paint(ctx, t, dt, W, H, TK) } drawn every frame on the engine background canvas. */
COMP.themes["default"] = (function(){
  var shapes = null;
  function rgba(hex, a){ var h = hex.replace("#", ""); return "rgba(" + parseInt(h.substr(0, 2), 16) + "," + parseInt(h.substr(2, 2), 16) + "," + parseInt(h.substr(4, 2), 16) + "," + a + ")"; }
  function make(TK, W, Hh){
    var n = TK.motion === "high" ? 14 : (TK.motion === "calm" ? 5 : 9), out = [];
    for (var i = 0; i < n; i++) out.push({ x: Math.random() * W, y: Math.random() * Hh, r: 60 + Math.random() * 150, sp: 6 + Math.random() * 14, ph: Math.random() * 6.28, c: i % 2 ? TK.colors.accent : TK.colors.primary });
    return out;
  }
  return { paint: function(ctx, t, dt, W, Hh, TK){
    if (!shapes) shapes = make(TK, W, Hh);
    var g = ctx.createLinearGradient(0, 0, 0, Hh); g.addColorStop(0, TK.colors.bg1); g.addColorStop(1, TK.colors.bg2);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, Hh);
    var drift = TK.motion === "calm" ? 0.4 : 1;
    for (var i = 0; i < shapes.length; i++){
      var s = shapes[i]; s.y -= s.sp * dt * drift; if (s.y < -s.r) { s.y = Hh + s.r; s.x = Math.random() * W; }
      ctx.fillStyle = rgba(s.c, 0.10); ctx.beginPath(); ctx.arc(s.x + Math.sin(t * 0.5 + s.ph) * 30, s.y, s.r, 0, 6.283); ctx.fill();
    }
  } };
})();
