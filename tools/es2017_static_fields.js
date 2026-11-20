// SPDX-License-Identifier: Apache-2.0
// Rewrites class fields (ES2022, static and instance) into Object.defineProperty calls and object spread (ES2018) into Object.assign,
// so a vendored library parses as ES2017 (old school Chrome).
// Usage: node tools/es2017_static_fields.js <acorn.js> <in.js> <out.js>     (acorn = ~/.teacher-studio/tools/acorn-*.js, fetched by ensure_acorn)
// Same define semantics as a class field (enumerable, writable, configurable; no setter is called). Stops if a static field uses `this`/`super`,
// or on a private name or a static block: those need a real compiler, not this patch.
const fs = require('fs');
const acorn = require(require('path').resolve(process.argv[2]));
const src = fs.readFileSync(process.argv[3], 'utf8');
const ast = acorn.parse(src, {ecmaVersion: 2022, sourceType: 'script'});
const classes = [], spreads = [];
(function walk(n, parent) {
  if (!n || typeof n.type !== 'string') return;
  if (n.type === 'ClassDeclaration' || n.type === 'ClassExpression') classes.push([n, parent]);
  if (n.type === 'ObjectExpression' && n.properties.some(q => q.type === 'SpreadElement')) spreads.push(n);
  for (const k of Object.keys(n)) {
    const v = n[k];
    if (Array.isArray(v)) v.forEach(c => walk(c, n)); else if (v && typeof v.type === 'string') walk(v, n);
  }
})(ast, null);
function usesThis(n) {
  let hit = false;
  (function w(x) {
    if (!x || typeof x.type !== 'string' || hit) return;
    if (x.type === 'ThisExpression' || x.type === 'Super') { hit = true; return; }
    if (x.type === 'FunctionExpression' || x.type === 'FunctionDeclaration') return;
    for (const k of Object.keys(x)) { const v = x[k]; if (Array.isArray(v)) v.forEach(w); else if (v && typeof v.type === 'string') w(v); }
  })(n);
  return hit;
}
const edits = [];  // [start, end, text]
let count = 0, uid = 0;
const DEF = (ref, key, val) => 'Object.defineProperty(' + ref + ',' + key + ',{value:' + val + ',writable:true,enumerable:true,configurable:true})';
function superCalls(fn) {
  const hits = [];
  (function w(x) {
    if (!x || typeof x.type !== 'string') return;
    if (x.type === 'CallExpression' && x.callee.type === 'Super') hits.push(x);
    if (x.type === 'FunctionExpression' || x.type === 'FunctionDeclaration' || x.type === 'ClassExpression' || x.type === 'ClassDeclaration') return;
    for (const k of Object.keys(x)) { const v = x[k]; if (Array.isArray(v)) v.forEach(w); else if (v && typeof v.type === 'string') w(v); }
  })(fn.body);
  return hits;
}
for (const [cls, parent] of classes) {
  const fields = cls.body.body.filter(m => m.type === 'PropertyDefinition' || m.type === 'StaticBlock');
  if (!fields.length) continue;
  const stmtParents = ['Program', 'BlockStatement', 'StaticBlock', 'SwitchCase'];
  const decl = cls.type === 'ClassDeclaration';
  if (decl && stmtParents.indexOf(parent.type) < 0) throw new Error('class declaration in an unexpected place at ' + cls.start);
  const ref = decl ? cls.id.name : '_tsC' + (uid++);
  const defs = [], inst = [];
  for (const f of fields) {
    if (f.type !== 'PropertyDefinition' || f.key.type === 'PrivateIdentifier' || (f.static && f.value && usesThis(f.value)))
      throw new Error('unsupported class member at ' + f.start + ': ' + src.slice(f.start, f.start + 60));
    const key = f.computed ? src.slice(f.key.start, f.key.end) : JSON.stringify(f.key.type === 'Identifier' ? f.key.name : f.key.value);
    if (f.computed && !f.static) throw new Error('computed instance field at ' + f.start);
    const val = f.value ? src.slice(f.value.start, f.value.end) : 'void 0';
    (f.static ? defs : inst).push(DEF(f.static ? ref : 'this', key, val));
    let end = f.end;
    if (src[end] === ';') end++;
    edits.push([f.start, end, '']);
    count++;
  }
  if (inst.length) {  // instance fields run where the engine runs them: first thing in a base constructor, right after super() in a derived one
    const ctor = cls.body.body.find(m => m.type === 'MethodDefinition' && m.kind === 'constructor');
    if (!ctor) edits.push([cls.body.start + 1, cls.body.start + 1, cls.superClass ? 'constructor(...a){super(...a);' + inst.join(';') + '}' : 'constructor(){' + inst.join(';') + '}']);
    else if (!cls.superClass) edits.push([ctor.value.body.start + 1, ctor.value.body.start + 1, inst.join(';') + ';']);
    else {
      const calls = superCalls(ctor.value);
      if (calls.length !== 1) throw new Error('constructor with ' + calls.length + ' super() calls at ' + ctor.start);
      edits.push([calls[0].start, calls[0].start, '(']);
      edits.push([calls[0].end, calls[0].end, ',' + inst.join(',') + ',this)']);
    }
  }
  if (!defs.length) continue;
  if (decl) edits.push([cls.end, cls.end, defs.join(';') + ';']);
  else { edits.push([cls.start, cls.start, '(()=>{const ' + ref + '=']); edits.push([cls.end, cls.end, ';' + defs.join(';') + ';return ' + ref + ';})()']); }
}
for (const obj of spreads) {  // {...a, b: 1} (ES2018) -> Object.assign({}, a, {b: 1})
  const ps = obj.properties;
  edits.push([obj.start, obj.start + 1, 'Object.assign({},']);
  ps.forEach((q, i) => {
    if (q.type === 'SpreadElement') { edits.push([q.start, q.start + 3, '']); return; }
    if (i === 0 || ps[i - 1].type === 'SpreadElement') edits.push([q.start, q.start, '{']);
    if (i === ps.length - 1 || ps[i + 1].type === 'SpreadElement') edits.push([q.end, q.end, '}']);
  });
  edits.push([obj.end - 1, obj.end, ')']);
}
edits.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
let out = src;
for (const [s, e, t] of edits) out = out.slice(0, s) + t + out.slice(e);
acorn.parse(out, {ecmaVersion: 2017, sourceType: 'script'});  // throws when anything newer than ES2017 is left
fs.writeFileSync(process.argv[4], out);
console.log('class fields rewritten: ' + count + ', object spreads: ' + spreads.length + '; output parses as ES2017');
