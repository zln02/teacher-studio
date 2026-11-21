/* RobotChef: a code-modeled, rigged 3D robot chef (three.js r128, ES2017, no optional chaining or nullish ops).
   RobotChef(THREE, opts) -> { root, stove, beats, pose(beat, t), apply(P, clock), cams }
   pose(beat, t) is a pure function of time t (seconds since the beat started), so fake clocks,
   jump-to-end (t = beat.dur) and going back all give the same picture. */
function RobotChef(THREE, opts) {
  'use strict';
  opts = opts || {};
  var REDUCED = !!opts.reduced;
  var PI = Math.PI;
  /* shared motion tokens (deck motion.js), in seconds */
  var TOK = { xs: 0.16, s: 0.32, m: 0.62, l: 0.9, gap: 0.09, lead: 0.9 };
  var EZ = {
    snap: function (t) { return 1 - Math.pow(1 - t, 5); },
    out: function (t) { return 1 - Math.pow(1 - t, 3); },
    inout: function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; },
    spring: function (t) { return t >= 1 ? 1 : 1 - Math.exp(-6.2 * t) * Math.cos(12.5 * t); }
  };
  function cl(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
  function seg(t, a, b) { return cl((t - a) / (b - a)); }
  function mix(a, b, u) { return a + (b - a) * u; }
  function wob(tau, amp) { return tau <= 0 ? 0 : amp * Math.exp(-6.2 * tau) * Math.sin(12.5 * tau); }   // the deck's spring, as a wobble
  function arc(t, t0, d, h) { var u = (t - t0) / d; return u > 0 && u < 1 ? 4 * u * (1 - u) * h : 0; }
  function bump(t, a, b, c, d) { return EZ.inout(seg(t, a, b)) * (1 - EZ.inout(seg(t, c, d))); }
  function V(x, y, z) { return new THREE.Vector3(x, y, z); }
  function C(h) { return new THREE.Color(h).convertSRGBToLinear(); }

  /* ---------- materials ---------- */
  var COL = { cream: 0xf4e6cf, hat: 0xfbf4e8, amber: 0xf0a23c, amberD: 0xe48d2e, blue: 0x93abb7, blueD: 0x5f7280,
    tire: 0x4a3122, grey: 0x8a776a, wok: 0x4e362b, wokIn: 0x3a2820, wood: 0xa9622e, steel: 0xb9b2a8,
    rice: 0xe0602f, egg: 0xfff8ec, yolk: 0xf7ad22, kimchi: 0xc8352a, green: 0x74ad55, counter: 0xe6d3b4, top: 0x9a5b2e, burner: 0x2a211c };
  function std(h, r, o) { return new THREE.MeshStandardMaterial(Object.assign({ color: C(h), roughness: r === undefined ? 0.55 : r, metalness: 0 }, o || {})); }
  function shellM(h, r) { return std(h, r === undefined ? 0.55 : r, { side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }); }
  var M = { cream: std(COL.cream, 0.48), hat: std(COL.hat, 0.62), amber: std(COL.amber, 0.42), amberD: std(COL.amberD, 0.5),
    blue: std(COL.blue, 0.5), tire: std(COL.tire, 0.82), grey: std(COL.grey, 0.6), wood: std(COL.wood, 0.58), steel: std(COL.steel, 0.35, { metalness: 0.4 }),
    wok: std(COL.wok, 0.5, { side: THREE.DoubleSide }), egg: std(COL.egg, 0.5), yolk: std(COL.yolk, 0.22), kimchi: std(COL.kimchi, 0.45), green: std(COL.green, 0.5) };
  var S_AMBER = shellM(COL.amber, 0.5), S_AMBERD = shellM(COL.amberD, 0.55), S_BLUE = shellM(COL.blue, 0.5);
  /* thin warm-brown inverted-hull outline, like the drawing's ink line */
  var OLM = new THREE.ShaderMaterial({ uniforms: { c: { value: new THREE.Color(0x4a2a18) }, w: { value: 0.011 } },
    vertexShader: 'uniform float w;void main(){vec3 p=position+normal*w;gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);}',
    fragmentShader: 'uniform vec3 c;void main(){gl_FragColor=vec4(c,1.0);}', side: THREE.BackSide });

  function mesh(g, m, par, x, y, z, ol) {
    var o = new THREE.Mesh(g, m); o.position.set(x || 0, y || 0, z || 0); o.castShadow = true; o.receiveShadow = true;
    if (par) par.add(o);
    if (ol && opts.outline !== false) { var h = new THREE.Mesh(g, OLM); h.castShadow = false; h.receiveShadow = false; o.add(h); }
    return o;
  }
  /* superellipsoid (rounded toy-box shapes) with analytic normals; partial patches via sphere phi/theta ranges */
  function supEll(sx, sy, sz, e, o) {
    o = o || {};
    var g = new THREE.SphereGeometry(1, o.ws || 40, o.hs || 28, o.ps === undefined ? 0 : o.ps, o.pl === undefined ? PI * 2 : o.pl, o.ts || 0, o.tl === undefined ? PI : o.tl);
    var p = g.attributes.position, n = g.attributes.normal, k = o.k || 1, tp = o.taper || 0, fb = o.fb, i;
    for (i = 0; i < p.count; i++) {
      var q = supDir(p.getX(i), p.getY(i), p.getZ(i), sx, sy, sz, e, k, tp, fb);
      p.setXYZ(i, q[0], q[1], q[2]); n.setXYZ(i, q[3], q[4], q[5]);
    }
    g.computeBoundingSphere();
    return g;
  }
  function f(v, e) { return (v < 0 ? -1 : 1) * Math.pow(Math.abs(v), e); }
  function supDir(x, y, z, sx, sy, sz, e, k, tp, fb) {
    var X = f(x, e) * sx / 2 * k, Y = f(y, e) * sy / 2 * k, Z = f(z, e) * sz / 2 * k, tw = 1 + (tp || 0) * (-Y / (sy / 2));
    X *= tw; Z *= tw; if (fb !== undefined && Y < -sy / 2 * fb) Y = -sy / 2 * fb;
    var nx = f(x, 2 - e) / sx, ny = f(y, 2 - e) / sy, nz = f(z, 2 - e) / sz, L = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    return [X, Y, Z, nx / L, ny / L, nz / L];
  }
  function supPt(sx, sy, sz, e, phi, th, k, tp) {   // same mapping as SphereGeometry: x=-cos(phi)sin(th), y=cos(th), z=sin(phi)sin(th)
    var q = supDir(-Math.cos(phi) * Math.sin(th), Math.cos(th), Math.sin(phi) * Math.sin(th), sx, sy, sz, e, k || 1, tp);
    return V(q[0], q[1], q[2]);
  }
  function capsule(r, len) {   // hangs from y=0 down to y=-len
    var pts = [], n = 8, i, a;
    for (i = 0; i <= n; i++) { a = -PI / 2 + i / n * PI / 2; pts.push(new THREE.Vector2(Math.cos(a) * r + 1e-4, -len + Math.sin(a) * r)); }
    for (i = 1; i <= n; i++) { a = i / n * PI / 2; pts.push(new THREE.Vector2(Math.cos(a) * r + 1e-4, Math.sin(a) * r)); }
    return new THREE.LatheGeometry(pts, 20);
  }
  function canvasTex(w, h, draw) {
    var c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
    var t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; t.anisotropy = 4; return t;
  }
  function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }

  /* ---------- face screen expressions (drawn, crisp at any size) ---------- */
  function faceTex(kind) {
    return canvasTex(512, 320, function (g) {
      rr(g, 4, 4, 504, 312, 118);
      var gr = g.createLinearGradient(0, 0, 0, 320); gr.addColorStop(0, '#3d241a'); gr.addColorStop(1, '#25140e'); g.fillStyle = gr; g.fill();
      g.save(); g.clip(); g.fillStyle = 'rgba(255,236,214,0.07)'; g.beginPath(); g.ellipse(180, 52, 210, 46, -0.12, 0, 7); g.fill(); g.restore();
      var cr = '#fbf1df'; g.lineCap = 'round'; g.lineJoin = 'round';
      function happy(x, y) { g.strokeStyle = cr; g.lineWidth = 16; g.beginPath(); g.arc(x, y + 16, 33, PI * 1.13, PI * 1.87); g.stroke(); }
      function calm(x, y) { g.strokeStyle = cr; g.lineWidth = 14; g.beginPath(); g.arc(x, y - 22, 34, PI * 0.2, PI * 0.8); g.stroke(); }
      function ring(x, y, s) { g.strokeStyle = cr; g.lineWidth = 12; g.beginPath(); g.ellipse(x, y, 27 * s, 29 * s, 0, 0, 7); g.stroke(); g.fillStyle = cr; g.beginPath(); g.arc(x + 3, y + 2, 11 * s, 0, 7); g.fill(); }
      function cheeks(a) { g.fillStyle = 'rgba(240,116,102,' + a + ')'; g.beginPath(); g.ellipse(112, 196, 36, 22, 0, 0, 7); g.fill(); g.beginPath(); g.ellipse(400, 196, 36, 22, 0, 0, 7); g.fill(); }
      function mouth(w, h, y) {
        y = y || 184; g.beginPath(); g.moveTo(256 - w, y); g.quadraticCurveTo(256, y + h * 2, 256 + w, y); g.closePath();
        g.fillStyle = '#7d2a24'; g.fill(); g.save(); g.clip(); g.fillStyle = '#f08884'; g.beginPath(); g.ellipse(256, y + h * 1.15, w * 0.62, h * 0.55, 0, 0, 7); g.fill(); g.restore();
      }
      if (kind === 'smile') { happy(170, 132); happy(342, 132); mouth(36, 30); cheeks(0.85); }
      else if (kind === 'wink') { ring(170, 128, 1); happy(342, 132); mouth(36, 30); cheeks(0.85); }
      else if (kind === 'surprised') { ring(170, 126, 1.15); ring(342, 126, 1.15); g.fillStyle = '#7d2a24'; g.beginPath(); g.ellipse(256, 214, 17, 21, 0, 0, 7); g.fill(); cheeks(0.55); }
      else if (kind === 'proud') { calm(170, 138); calm(342, 138); mouth(46, 32, 186); cheeks(0.9);
        g.fillStyle = '#f2a94e'; g.beginPath(); var sx = 446, sy = 62; for (var i = 0; i < 8; i++) { var a = i / 8 * PI * 2 - PI / 2, r = i % 2 ? 7 : 22; g.lineTo(sx + Math.cos(a) * r, sy + Math.sin(a) * r); } g.closePath(); g.fill(); }
    });
  }
  var FACES = { smile: faceTex('smile'), wink: faceTex('wink'), surprised: faceTex('surprised'), proud: faceTex('proud') };
  var faceMat = new THREE.MeshStandardMaterial({ map: FACES.smile, emissiveMap: FACES.smile, emissive: new THREE.Color(1, 1, 1), emissiveIntensity: 0.6,
    roughness: 0.22, metalness: 0, transparent: true, alphaTest: 0.5, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 });
  var ventTex = canvasTex(256, 150, function (g) {
    rr(g, 3, 3, 250, 144, 44); g.fillStyle = '#93abb7'; g.fill(); g.strokeStyle = '#6d5040'; g.lineWidth = 5; g.stroke();
    g.fillStyle = '#4f606b'; [88, 128, 168].forEach(function (x) { rr(g, x - 9, 42, 18, 66, 9); g.fill(); });
  });
  var riceTex = canvasTex(256, 256, function (g) {
    g.fillStyle = '#dc5a2b'; g.fillRect(0, 0, 256, 256); var s = 7;
    function rnd() { s = (s * 16807) % 2147483647; return s / 2147483647; }
    for (var i = 0; i < 900; i++) { g.fillStyle = rnd() < 0.55 ? '#f3a066' : rnd() < 0.5 ? '#f8c896' : '#c9472a'; g.beginPath(); g.ellipse(rnd() * 256, rnd() * 256, 4.5, 2.6, rnd() * 3, 0, 7); g.fill(); }
  });
  var dotTex = canvasTex(32, 32, function (g) { g.fillStyle = '#fff'; g.beginPath(); g.ellipse(16, 16, 14, 10, 0.5, 0, 7); g.fill(); });
  var blobTex = canvasTex(128, 128, function (g) { var r = g.createRadialGradient(64, 64, 4, 64, 64, 62); r.addColorStop(0, 'rgba(20,10,5,0.75)'); r.addColorStop(0.6, 'rgba(20,10,5,0.32)'); r.addColorStop(1, 'rgba(20,10,5,0)'); g.fillStyle = r; g.fillRect(0, 0, 128, 128); });

  /* ---------- the robot (rig) ----------
     root(x,z,turn) > base(hop, squash, 4 wheels) > waist(lean/twist) > torso > neck > head(face screen, ears) > hat(squash)
     torso > shoulder L/R > elbow > wrist > mitten  (2-bone IK to hand targets)      torso > wok(rice, egg, grains) */
  var HOME = 1.1, WR = 0.17, R = {};
  R.root = new THREE.Group(); R.root.name = 'robotChef';
  R.base = new THREE.Group(); R.root.add(R.base);
  var BS = [1.0, 0.44, 0.8], BE = 0.42, BY = 0.38;
  mesh(supEll(BS[0], BS[1], BS[2], BE, { fb: 0.85 }), M.cream, R.base, 0, BY, 0, true);
  mesh(supEll(BS[0], BS[1], BS[2], BE, { k: 1.012, ts: 0.34, tl: 0.36 }), S_AMBER, R.base, 0, BY, 0);
  mesh(supEll(BS[0], BS[1], BS[2], BE, { k: 1.012, ts: 1.98, tl: 0.3, fb: 0.85 }), S_AMBER, R.base, 0, BY, 0);
  var vent = mesh(supEll(BS[0], BS[1], BS[2], BE, { k: 1.022, ps: PI / 2 - 0.36, pl: 0.72, ts: 1.28, tl: 0.62, ws: 16, hs: 12 }),
    new THREE.MeshStandardMaterial({ map: ventTex, roughness: 0.45, transparent: true, alphaTest: 0.5, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 }), R.base, 0, BY, 0);
  vent.castShadow = false;
  R.wheels = [];
  [[-1, 1], [1, 1], [-1, -1], [1, -1]].forEach(function (s) {
    var w = new THREE.Group(); w.position.set(s[0] * 0.47, WR, s[1] * 0.25); R.base.add(w);
    var tire = mesh(new THREE.TorusGeometry(0.112, 0.06, 14, 30), M.tire, w, 0, 0, 0, true); tire.rotation.y = PI / 2;
    var hub = mesh(new THREE.CylinderGeometry(0.088, 0.088, 0.1, 24), M.amber, w); hub.rotation.z = PI / 2;
    var cap = mesh(new THREE.CylinderGeometry(0.034, 0.034, 0.112, 14), M.cream, w); cap.rotation.z = PI / 2;
    mesh(new THREE.BoxGeometry(0.108, 0.026, 0.15), M.amberD, w);
    R.wheels.push({ g: w, side: s[0] });
  });
  R.waist = new THREE.Group(); R.waist.position.y = 0.55; R.base.add(R.waist);
  R.torso = new THREE.Group(); R.waist.add(R.torso);
  var TS = [1.1, 0.84, 0.86], TE = 0.55, TY = 0.4, TT = 0.1;
  function torsoG(o) { return supEll(TS[0], TS[1], TS[2], TE, Object.assign({ taper: TT, fb: 0.9 }, o || {})); }
  function torsoPt(phi, th, k) { var p = supPt(TS[0], TS[1], TS[2], TE, phi, th, k, TT); p.y += TY; return p; }
  mesh(torsoG(), M.cream, R.torso, 0, TY, 0, true);
  mesh(torsoG({ k: 1.012, ps: -0.55, pl: 1.1, ts: 1.95, tl: 0.62 }), S_BLUE, R.torso, 0, TY, 0);
  mesh(torsoG({ k: 1.012, ps: PI - 0.55, pl: 1.1, ts: 1.95, tl: 0.62 }), S_BLUE, R.torso, 0, TY, 0);
  mesh(torsoG({ k: 1.018, ts: 1.6, tl: 0.15 }), S_AMBER, R.torso, 0, TY, 0);                                  // belt line
  mesh(torsoG({ k: 1.028, ps: PI / 2 - 0.8, pl: 1.6, ts: 1.52, tl: 1.0 }), S_AMBER, R.torso, 0, TY, 0);       // apron skirt
  mesh(torsoG({ k: 1.028, ps: PI / 2 - 0.5, pl: 1.0, ts: 0.74, tl: 0.86 }), S_AMBER, R.torso, 0, TY, 0);      // bib
  mesh(torsoG({ k: 1.04, ps: PI / 2 - 0.3, pl: 0.6, ts: 1.66, tl: 0.42 }), S_AMBERD, R.torso, 0, TY, 0);      // pocket
  [-1, 1].forEach(function (s) {
    mesh(torsoG({ k: 1.028, ps: PI / 2 + s * 0.42 - 0.07, pl: 0.14, ts: 0.1, tl: 0.7 }), S_AMBER, R.torso, 0, TY, 0);       // front straps
    mesh(torsoG({ k: 1.028, ps: 3 * PI / 2 + s * 0.42 - 0.07, pl: 0.14, ts: 0.1, tl: 1.5 }), S_AMBER, R.torso, 0, TY, 0);   // back straps
    var b = torsoPt(PI / 2 + s * 0.4, 0.86, 1.05); mesh(new THREE.SphereGeometry(0.035, 12, 8), M.amberD, R.torso, b.x, b.y, b.z);
  });
  mesh(torsoG({ k: 1.028, ps: 3 * PI / 2 - 0.5, pl: 1.0, ts: 1.36, tl: 0.14 }), S_AMBER, R.torso, 0, TY, 0);     // back cross strap
  function makeArm(side) {
    var sh = new THREE.Group(); sh.position.set(side * 0.57, 0.6, 0.04); R.torso.add(sh);
    mesh(new THREE.SphereGeometry(0.135, 24, 16), M.amber, sh, 0, 0, 0, true);
    mesh(capsule(0.078, 0.3), M.cream, sh, 0, 0, 0, true);
    var el = new THREE.Group(); el.position.y = -0.3; sh.add(el);
    mesh(capsule(0.076, 0.27), M.cream, el, 0, 0, 0, true);
    var wr = new THREE.Group(); wr.position.y = -0.27; el.add(wr);
    var cuff = mesh(new THREE.TorusGeometry(0.08, 0.032, 10, 24), M.amber, wr, 0, 0.015, 0); cuff.rotation.x = PI / 2;
    mesh(supEll(0.2, 0.22, 0.14, 0.7), M.cream, wr, 0, -0.11, 0, true);
    mesh(supEll(0.075, 0.12, 0.08, 0.8), M.cream, wr, -side * 0.1, -0.075, 0.015, true);
    return { sh: sh, el: el, wr: wr, a: 0.3, b: 0.27, side: side };
  }
  R.armL = makeArm(-1); R.armR = makeArm(1);
  R.neck = new THREE.Group(); R.neck.position.y = 0.8; R.torso.add(R.neck);
  mesh(new THREE.CylinderGeometry(0.13, 0.17, 0.14, 20), M.grey, R.neck, 0, 0.03, 0);
  R.head = new THREE.Group(); R.head.position.y = 0.06; R.neck.add(R.head);
  var HS = [1.2, 0.88, 0.88], HE = 0.42, HY = 0.43;
  mesh(supEll(HS[0], HS[1], HS[2], HE), M.cream, R.head, 0, HY, 0, true);
  R.screen = mesh(supEll(HS[0], HS[1], HS[2], HE, { k: 1.014, ps: PI / 2 - 0.62, pl: 1.24, ts: 1.2, tl: 0.76, ws: 40, hs: 24 }), faceMat, R.head, 0, HY, 0);
  R.screen.castShadow = false;
  (function planarUV(g) {   // project the face straight on, so the drawn face is not stretched by the rounded head
    g.computeBoundingBox(); var bb = g.boundingBox, p = g.attributes.position, uv = g.attributes.uv;
    for (var j = 0; j < p.count; j++) uv.setXY(j, (p.getX(j) - bb.min.x) / (bb.max.x - bb.min.x), (p.getY(j) - bb.min.y) / (bb.max.y - bb.min.y));
    uv.needsUpdate = true;
  })(R.screen.geometry);
  [-1, 1].forEach(function (s) {
    mesh(supEll(0.17, 0.38, 0.38, 0.6), M.amber, R.head, s * 0.61, HY, 0, true);
    var ring = mesh(new THREE.TorusGeometry(0.11, 0.025, 10, 24), M.cream, R.head, s * 0.695, HY, 0); ring.rotation.y = PI / 2;
  });
  R.hat = new THREE.Group(); R.hat.position.y = HY + 0.38; R.head.add(R.hat);
  mesh(supEll(0.52, 0.15, 0.44, 0.4), M.amber, R.hat, 0, 0.04, 0, true);
  mesh(new THREE.CylinderGeometry(0.26, 0.24, 0.24, 28), M.hat, R.hat, 0, 0.2, 0, true);
  [[0, 0.44, 0, 0.21], [0.18, 0.38, 0, 0.16], [-0.18, 0.38, 0, 0.16], [0, 0.38, 0.14, 0.15], [0, 0.38, -0.14, 0.15], [0.12, 0.42, 0.11, 0.13], [-0.12, 0.42, -0.1, 0.13], [-0.12, 0.42, 0.1, 0.13], [0.12, 0.42, -0.1, 0.13]].forEach(function (b) {
    mesh(new THREE.SphereGeometry(b[3], 22, 14), M.hat, R.hat, b[0], b[1], b[2], true);
  });
  /* wok with 김치볶음밥 + fried egg, held in torso space (hands follow it with IK) */
  var WK = 1.12;
  R.wok = new THREE.Group(); R.torso.add(R.wok);
  var wk = new THREE.Group(); wk.scale.setScalar(WK); R.wok.add(wk);
  var prof = [[0, -0.12], [0.14, -0.12], [0.23, -0.096], [0.29, -0.048], [0.325, 0.015], [0.342, 0.06]].map(function (p) { return new THREE.Vector2(p[0] + 1e-4, p[1]); });
  mesh(new THREE.LatheGeometry(prof, 40), M.wok, wk, 0, 0, 0, true);
  var rim = mesh(new THREE.TorusGeometry(0.342, 0.014, 8, 48), M.wok, wk, 0, 0.06, 0); rim.rotation.x = PI / 2;
  R.mound = new THREE.Group(); wk.add(R.mound);
  mesh(supEll(0.6, 0.17, 0.6, 0.8, { tl: PI / 2 + 0.05 }), std(0xffffff, 0.7, { map: riceTex }), R.mound, 0, 0.0, 0);
  var s0 = 3; function rnd() { s0 = (s0 * 16807) % 2147483647; return s0 / 2147483647; }
  for (var i = 0; i < 9; i++) { var a = rnd() * PI * 2, r = 0.08 + rnd() * 0.17; var kb = mesh(supEll(0.07, 0.025, 0.05, 0.5), M.kimchi, R.mound, Math.cos(a) * r, 0.068 - r * r * 0.5, Math.sin(a) * r); kb.rotation.set(rnd(), rnd() * 3, rnd() * 0.5); }
  for (i = 0; i < 6; i++) { a = rnd() * PI * 2; r = 0.1 + rnd() * 0.15; mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.01, 10), M.green, R.mound, Math.cos(a) * r, 0.075 - r * r * 0.5, Math.sin(a) * r); }
  R.egg = new THREE.Group(); R.egg.position.set(0.02, 0.07, -0.02); R.mound.add(R.egg);
  var eg = supEll(0.32, 0.04, 0.27, 0.85), ep = eg.attributes.position;
  for (i = 0; i < ep.count; i++) { var ex = ep.getX(i), ez = ep.getZ(i), ang = Math.atan2(ez, ex), w8 = 1 + 0.07 * Math.sin(ang * 5 + 1) + 0.04 * Math.sin(ang * 3); ep.setX(i, ex * w8); ep.setZ(i, ez * w8); }
  mesh(eg, M.egg, R.egg, 0, 0.012, 0, true);
  var yk = mesh(new THREE.SphereGeometry(0.068, 20, 14), M.yolk, R.egg, -0.01, 0.03, 0.01); yk.scale.y = 0.62;
  mesh(new THREE.BoxGeometry(0.05, 0.06, 0.07), M.steel, wk, 0.355, 0.03, 0);
  var hd = new THREE.Group(); hd.position.set(0.37, 0.04, 0); hd.rotation.z = 0.14; wk.add(hd);
  var hm = mesh(new THREE.CylinderGeometry(0.03, 0.04, 0.44, 14), M.wood, hd, 0.22, 0, 0, true); hm.rotation.z = PI / 2;
  /* rice grains for the toss (wok-local, only visible in flight) */
  var NG = 46, gpos = new Float32Array(NG * 3), gcol = new Float32Array(NG * 3), GR = [];
  for (i = 0; i < NG; i++) {
    var c = C([0xf6c08c, 0xe8692f, 0xfbe3c4, 0xc8352a][i % 4]); gcol[i * 3] = c.r; gcol[i * 3 + 1] = c.g; gcol[i * 3 + 2] = c.b;
    a = rnd() * PI * 2; r = rnd() * 0.2;
    GR.push({ x: Math.cos(a) * r, z: Math.sin(a) * r, vx: Math.cos(a) * (0.08 + rnd() * 0.2), vz: Math.sin(a) * (0.08 + rnd() * 0.2) - 0.05, vy: 1.35 + rnd() * 0.75 });
  }
  var gg = new THREE.BufferGeometry(); gg.setAttribute('position', new THREE.BufferAttribute(gpos, 3)); gg.setAttribute('color', new THREE.BufferAttribute(gcol, 3));
  R.grains = new THREE.Points(gg, new THREE.PointsMaterial({ size: 0.05, map: dotTex, vertexColors: true, transparent: true, alphaTest: 0.4, depthWrite: true }));
  R.grains.frustumCulled = false; wk.add(R.grains);
  var blob = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 1.25), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false }));
  blob.rotation.x = -PI / 2; blob.position.y = 0.006; blob.renderOrder = 1; R.root.add(blob); R.blob = blob;
  R.root.traverse(function (o) { if (o.isMesh && o.material === OLM) o.castShadow = false; });

  /* ---------- the stove counter behind the robot (in front of the painted kitchen) ---------- */
  var ST = { x: HOME + 0.15, z: -1.5, top: 0.94 }, stove = new THREE.Group(); stove.name = 'stove';
  mesh(supEll(2.7, 0.9, 0.82, 0.12, { fb: 1 }), std(COL.counter, 0.6), stove, ST.x, 0.45, ST.z, true);
  mesh(supEll(2.86, 0.09, 0.94, 0.16), std(COL.top, 0.55), stove, ST.x, 0.93, ST.z, true);
  [-0.9, 0, 0.9].forEach(function (dx) {
    mesh(supEll(0.8, 0.62, 0.05, 0.14), std(0xeedfc4, 0.55), stove, ST.x + dx, 0.44, ST.z + 0.42, true);
    mesh(new THREE.SphereGeometry(0.04, 12, 8), M.amberD, stove, ST.x + dx + 0.26, 0.6, ST.z + 0.46);
  });
  var BX = HOME + 0.04, BZ = -1.34;
  mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.025, 32), std(COL.burner, 0.6), stove, BX, ST.top + 0.012, BZ);
  var br = mesh(new THREE.TorusGeometry(0.15, 0.018, 8, 28), std(0x5a4a40, 0.5), stove, BX, ST.top + 0.03, BZ); br.rotation.x = PI / 2;
  var pot = new THREE.Group(); pot.position.set(ST.x + 0.85, ST.top, ST.z - 0.08); stove.add(pot);
  mesh(new THREE.CylinderGeometry(0.24, 0.22, 0.26, 28), std(0x8fb3bf, 0.45), pot, 0, 0.13, 0, true);
  mesh(supEll(0.52, 0.1, 0.52, 0.6), std(0xe9a24a, 0.45), pot, 0, 0.27, 0, true);
  mesh(new THREE.SphereGeometry(0.04, 12, 8), std(0xe9a24a, 0.45), pot, 0, 0.33, 0);
  var flames = [];
  var flM = new THREE.MeshBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false });
  var flB = new THREE.MeshBasicMaterial({ color: 0x6fb6e8, transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending, depthWrite: false });
  for (i = 0; i < 10; i++) { a = i / 10 * PI * 2; var fl = new THREE.Mesh(new THREE.ConeGeometry(0.035, 0.13, 8), i % 2 ? flB : flM); fl.position.set(BX + Math.cos(a) * 0.15, ST.top + 0.09, BZ + Math.sin(a) * 0.15); fl.castShadow = false; stove.add(fl); flames.push(fl); }

  /* ---------- rig helpers ---------- */
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _s = V(WK, WK, WK), _bm = new THREE.Matrix4();
  function wokPt(w, lx, ly, lz) { _e.set(w.rx, w.ry, w.rz); _q.setFromEuler(_e); _m.compose(V(w.x, w.y, w.z), _q, _s); return V(lx, ly, lz).applyMatrix4(_m); }
  function gripR(w) { return wokPt(w, 0.6, 0.05, 0).add(V(0.02, 0.05, -0.1)); }
  function gripL(w) { return wokPt(w, -0.36, 0.07, 0.07).add(V(-0.05, 0.04, -0.09)); }
  var RESTL = V(-0.68, 0.06, 0.12), RESTR = V(0.68, 0.06, 0.12);
  function ik(arm, T, pole) {
    var S = arm.sh.position, d = T.clone().sub(S), L = d.length(), a = arm.a, b = arm.b;
    L = Math.max(Math.abs(a - b) + 0.02, Math.min(a + b - 0.002, L)); d.setLength(L);
    var Th = d.clone().normalize(), P = (pole || V(arm.side * 0.35, -0.3, -1)).clone();
    P.sub(Th.clone().multiplyScalar(P.dot(Th))); if (P.lengthSq() < 1e-6) P.set(0, 0, -1); P.normalize();
    var al = Math.acos(Math.max(-1, Math.min(1, (a * a + L * L - b * b) / (2 * a * L))));
    var U = Th.clone().multiplyScalar(Math.cos(al)).add(P.clone().multiplyScalar(Math.sin(al))).normalize();
    var Pp = P.clone().sub(U.clone().multiplyScalar(P.dot(U))); if (Pp.lengthSq() < 1e-8) Pp.set(0, 0, -1); Pp.normalize();
    var Z = Pp.negate(), Y = U.clone().negate(), X = new THREE.Vector3().crossVectors(Y, Z);
    _bm.makeBasis(X, Y, Z); arm.sh.quaternion.setFromRotationMatrix(_bm);
    arm.el.rotation.set(PI - Math.acos(Math.max(-1, Math.min(1, (a * a + b * b - L * L) / (2 * a * b)))), 0, 0);
  }

  /* ---------- beats: pose(beat, t) is pure ---------- */
  var WOK0 = { x: 0.0, y: 0.3, z: 0.54, rx: 0, ry: 0, rz: 0 };
  var BEATS = [
    { id: 'enter', dur: 3.0, cam: 'front' },
    { id: 'wave', dur: 2.8, cam: 'front' },
    { id: 'toss', dur: 3.6, cam: 'tq' },
    { id: 'turn', dur: 4.8, cam: 'side' },
    { id: 'bow', dur: 2.8, cam: 'bow' },
    { id: 'puzzle', dur: 2.2, cam: 'front', extra: true }      // extra, for the deck's "huh?" clicks (not in the demo run)
  ];
  var CAMS = {
    front: { yaw: 0, pitch: 0.1, dist: 7.7, tx: 0.3, ty: 1.24, tz: 0 },
    tq: { yaw: 0.62, pitch: 0.17, dist: 7.0, tx: 0.6, ty: 1.3, tz: 0.15 },
    side: { yaw: -1.02, pitch: 0.3, dist: 7.0, tx: 0.95, ty: 1.1, tz: -1.0 },
    bow: { yaw: 0.1, pitch: 0.08, dist: 7.0, tx: 0.38, ty: 1.24, tz: 0 }
  };
  function rest() {
    return { x: HOME, z: 0, ry: 0, hop: 0, sq: 0, lean: 0, twist: 0, tilt: 0, hx: 0, hy: 0, hz: 0, hat: 0, hatLag: 0, br: 0,
      face: 'smile', wok: Object.assign({}, WOK0), wokOn: true, L: null, R: null, poleL: null, poleR: null,
      rice: -1, mound: 0, eggY: 0, eggR: 0, flame: 0, t: 0 };
  }
  function lerpW(a, b, u) { return { x: mix(a.x, b.x, u), y: mix(a.y, b.y, u), z: mix(a.z, b.z, u), rx: mix(a.rx, b.rx, u), ry: mix(a.ry, b.ry, u), rz: mix(a.rz, b.rz, u) }; }
  function tossCurve(tau) {       // anticipation (-0.18..0) -> flick (0..0.12) -> spring back; returns [dy, dz, drx]
    if (tau < -0.18 || tau > 0.75) return [0, 0, 0];
    var A = [-0.05, -0.03, 0.16], F = [0.1, 0.06, -0.34], u;
    if (tau < 0) { u = EZ.inout(seg(tau, -0.18, 0)); return [A[0] * u, A[1] * u, A[2] * u]; }
    if (tau < 0.12) { u = EZ.snap(tau / 0.12); return [mix(A[0], F[0], u), mix(A[1], F[1], u), mix(A[2], F[2], u)]; }
    u = 1 - EZ.spring(seg(tau, 0.12, 0.75)); return [F[0] * u, F[1] * u, F[2] * u];
  }
  var TOSS = [1.0, 1.65, 2.3];
  function pose(b, t) {
    var P = rest(), B = BEATS[b], u;
    P.t = t;
    if (B.id === 'enter') {
      P.x = mix(-7.2, HOME, EZ.out(seg(t, 0, 1.75)));
      var headW = PI / 2 * (1 - EZ.snap(seg(t, 1.15, 1.65)));
      P.ry = PI / 2 * (1 - EZ.inout(seg(t, 1.5, 2.2)));
      P.hy = Math.max(-1.1, Math.min(1.1, headW - P.ry));
      P.lean = -0.08 * bump(t, 0, 0.3, 0.6, 1.0) + wob(t - 1.5, 0.16);
      P.sq = 0.08 * Math.sin(PI * seg(t, 2.08, 2.28)) - (arc(t, 2.28, 0.36, 1) > 0 ? 0.05 : 0) + wob(t - 2.64, 0.12);
      P.hop = arc(t, 2.28, 0.36, 0.14);
      P.hat = wob(t - 2.64, 0.16) + wob(t - 1.5, 0.08); P.hatLag = wob(t - 1.5, 0.12);
    } else if (B.id === 'wave') {
      var up = V(-0.86, 1.05, 0.26), wig = Math.sin((t - 0.45) * PI * 4) * 0.1 * bump(t, 0.45, 0.6, 1.8, 1.95);
      var u1 = EZ.snap(seg(t, 0, 0.45)), u2 = EZ.inout(seg(t, 1.95, 2.45)), w1 = u1 * (1 - u2);
      P.wok.rz = 0.06 * w1; P.wok.x = 0.05 * w1;
      var rim = gripL(P.wok);
      P.L = rim.clone().lerp(up.clone().add(V(wig, Math.abs(wig) * 0.3, 0)), w1);
      P.poleL = V(-0.35, -0.3, -1).lerp(V(-1, -0.5, 0.15), w1);
      P.face = t > 0.3 && t < 2.05 ? 'wink' : 'smile';
      P.hz = 0.14 * bump(t, 0.15, 0.55, 1.9, 2.4); P.twist = -0.1 * bump(t, 0.1, 0.5, 1.9, 2.4);
      P.hop = arc(t, 0.05, 0.3, 0.05); P.hat = wob(t - 0.35, 0.08);
    } else if (B.id === 'toss') {
      var dy = 0, dz = 0, drx = 0, k;
      for (k = 0; k < TOSS.length; k++) {
        var c = tossCurve(t - TOSS[k]); dy += c[0]; dz += c[1]; drx += c[2];
        var tg = t - TOSS[k] - 0.05; if (tg >= 0 && tg < 0.62) P.rice = tg;
        P.mound += arc(t, TOSS[k] + 0.04, 0.32, 0.05);
        P.hat += wob(t - TOSS[k] - 0.12, 0.1);
        P.lean += c[0] * 0.6;
      }
      var t3 = t - TOSS[2];
      P.eggY = arc(t3, 0.05, 0.5, 0.32); P.eggR = PI * 2 * EZ.inout(seg(t3, 0.08, 0.5));
      P.wok.y += dy; P.wok.z += dz; P.wok.rx += drx;
      P.face = t > 0.95 && t < 2.95 ? 'surprised' : 'smile';
      P.hx = 0.14 * bump(t, 0.5, 0.9, 2.8, 3.2) - (P.rice >= 0 ? 0.06 * Math.sin(PI * P.rice / 0.62) : 0);
      P.twist = 0.08 * bump(t, 0.4, 0.9, 2.8, 3.3);
      if (t > 2.95) P.hop = arc(t, 2.95, 0.3, 0.06);
    } else if (B.id === 'turn') {
      P.ry = PI * EZ.inout(seg(t, 0, 0.95)) * (1 - EZ.inout(seg(t, 3.2, 4.15)));
      P.z = -0.6 * EZ.inout(seg(t, 0.35, 1.1)) * (1 - EZ.inout(seg(t, 3.3, 4.2)));
      var at = EZ.inout(seg(t, 1.0, 1.45)) * (1 - EZ.inout(seg(t, 2.6, 3.05)));
      P.wok = lerpW(WOK0, { x: -0.06, y: 0.6, z: 0.7, rx: -0.1, ry: 0, rz: 0 }, at);
      P.wok.z += 0.06 * Math.sin((t - 1.6) * PI * 4) * bump(t, 1.55, 1.7, 2.35, 2.5);
      P.lean = 0.1 * at; P.hx = 0.2 * at;
      P.flame = bump(t, 1.3, 1.5, 2.65, 2.85);
      P.mound = 0.02 * Math.abs(Math.sin((t - 1.6) * PI * 4)) * bump(t, 1.55, 1.7, 2.35, 2.5);
      P.sq = wob(t - 4.2, 0.07); P.hat = wob(t - 4.2, 0.1) + wob(t - 0.95, 0.06); P.hatLag = wob(t - 0.95, 0.1) - wob(t - 4.15, 0.1);
      P.face = t > 1.5 && t < 2.6 ? 'wink' : 'smile';
    } else if (B.id === 'bow') {
      var down = EZ.snap(seg(t, 0.25, 0.75)), upk = EZ.spring(seg(t, 1.2, 2.1));
      P.lean = -0.08 * Math.sin(PI * seg(t, 0, 0.25)) + 0.5 * down * (1 - upk) - 0.06 * EZ.inout(seg(t, 1.3, 1.9));
      P.hx = 0.2 * bump(t, 0.3, 0.8, 1.15, 1.7);
      P.hatLag = wob(t - 0.72, -0.28) + wob(t - 1.3, 0.18); P.hat = wob(t - 0.72, 0.1);
      P.face = t < 0.25 ? 'smile' : 'proud';
      u = EZ.inout(seg(t, 1.45, 2.1));
      P.wok = lerpW(WOK0, { x: 0, y: 0.38, z: 0.6, rx: 0.32, ry: 0, rz: 0 }, u); P.wok.rx -= P.lean;
      P.hop = arc(t, 1.7, 0.3, 0.05);
    } else if (B.id === 'puzzle') {
      u = bump(t, 0, 0.35, 1.7, 2.1);
      P.face = t > 0.1 && t < 1.8 ? 'surprised' : 'smile'; P.hz = 0.26 * u; P.hx = -0.06 * u;
      P.L = gripL(P.wok).lerp(V(-0.9, 0.62, 0.32), u); P.poleL = V(-1, -0.6, 0);
      P.hat = wob(t - 0.35, 0.1);
    }
    /* idle breathing after the beat (very small), off for reduced motion */
    if (!REDUCED && t > B.dur) { var k2 = seg(t, B.dur, B.dur + 0.8) * 0.007; P.br = Math.sin((t - B.dur) * PI * 2 / 3.6) * k2; }
    return P;
  }

  /* ---------- apply a pose to the rig ---------- */
  var curFace = 'smile';
  function apply(P, clock) {
    R.root.position.set(P.x, P.hop, P.z); R.root.rotation.y = P.ry;
    var s = P.sq; R.base.scale.set(1 + s * 0.5, 1 - s, 1 + s * 0.5);
    R.waist.rotation.set(P.lean, P.twist, P.tilt);
    R.torso.scale.set(1, 1 + P.br, 1);
    R.head.rotation.set(P.hx, P.hy, P.hz);
    R.hat.scale.set(1 + P.hat * 0.5, 1 - P.hat, 1 + P.hat * 0.5); R.hat.rotation.x = P.hatLag;
    var fwd = ((P.x - HOME) - P.z) / WR, turn = P.ry * 0.47 / WR;
    R.wheels.forEach(function (w) { w.g.rotation.x = fwd + w.side * turn; });
    var w = P.wok; R.wok.position.set(w.x, w.y, w.z); R.wok.rotation.set(w.rx, w.ry, w.rz); R.wok.visible = P.wokOn;
    R.mound.position.y = P.mound; R.egg.position.y = 0.07 + P.eggY; R.egg.rotation.x = P.eggR;
    ik(R.armL, P.L || (P.wokOn ? gripL(w) : RESTL), P.poleL);
    ik(R.armR, P.R || (P.wokOn ? gripR(w) : RESTR), P.poleR);
    if (P.face !== curFace) { faceMat.map = FACES[P.face]; faceMat.emissiveMap = FACES[P.face]; curFace = P.face; }
    for (var i = 0; i < NG; i++) {
      var g = GR[i], tau = P.rice - (i % 5) * 0.012, T = 2 * g.vy / 7, on = P.rice >= 0 && tau > 0 && tau < T;
      gpos[i * 3] = on ? g.x + g.vx * tau : 0; gpos[i * 3 + 1] = on ? 0.07 + g.vy * tau - 3.5 * tau * tau : -99; gpos[i * 3 + 2] = on ? g.z + g.vz * tau : 0;
    }
    R.grains.geometry.attributes.position.needsUpdate = true;
    var ck = clock || 0;
    flames.forEach(function (fl, k) { var v = P.flame * (0.85 + 0.15 * Math.sin(ck * 31 + k * 1.7)); fl.visible = P.flame > 0.01; fl.scale.set(1, Math.max(0.01, v), 1); });
    R.blob.position.y = 0.006 - P.hop; R.blob.scale.setScalar(1 - Math.min(0.3, P.hop * 1.5)); R.blob.material.opacity = 1 - Math.min(0.5, P.hop * 2);
  }
  function setOutline(on) { R.root.traverse(function (o) { if (o.material === OLM) o.visible = on; }); stove.traverse(function (o) { if (o.material === OLM) o.visible = on; }); }
  return { setOutline: setOutline, root: R.root, rig: R, stove: stove, beats: BEATS, cams: CAMS, tok: TOK, ez: EZ, pose: pose, apply: apply, faces: FACES, home: HOME };
}
