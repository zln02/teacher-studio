# SPDX-License-Identifier: Apache-2.0
"""Check executable HTML scripts independently, including inlined libraries."""
from __future__ import annotations

import json
import shutil
import subprocess
from html.parser import HTMLParser

from ensure import ensure_acorn


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self.external = 0
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name, value in attrs.items():
            if name.startswith("on") and value:
                self.scripts.append((self.getpos()[0], "script", "function eventHandler(event) {\n" + value + "\n}"))
        if tag != "script":
            return
        kind = (attrs.get("type") or "").split(";")[0].strip().lower()
        if kind not in ("", "module", "text/javascript", "application/javascript",
                        "text/ecmascript", "application/ecmascript"):
            return
        if "src" in attrs:
            self.external += 1
        else:
            self.current = (self.getpos()[0], "module" if kind == "module" else "script", [])

    def handle_data(self, data):
        if self.current:
            self.current[2].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.current:
            line, kind, parts = self.current
            self.scripts.append((line, kind, "".join(parts)))
            self.current = None


NODE_CHECK = r"""
const fs = require('fs'), vm = require('vm');
const acorn = process.argv[1] ? require(process.argv[1]) : null;
const allowModern = process.argv[2] === 'modern';
const out = [];
for (const [line, type, code] of JSON.parse(fs.readFileSync(0, 'utf8'))) {
  const modern = allowModern && /^\/\* TS:VENDOR motion /.test(code);
  try {
    if (acorn) acorn.parse(code, {ecmaVersion: modern ? 2020 : 2017, sourceType: type});
    else if (type === 'script') new vm.Script(code);
  } catch (e) {
    out.push('HTML line ' + (line + (e.loc ? e.loc.line - 1 : 0)) + ': ' + e.message);
  }
}
process.stdout.write(JSON.stringify(out));
"""


def checks(html: str, *, consent: bool = False, allow_modern: bool = False) -> list[tuple[str, str]]:
    node = shutil.which("node")
    if not node:
        return [("SKIP", "JavaScript syntax: Node.js unavailable")]
    src = Scripts()
    src.feed(html)
    src.close()
    tool = ensure_acorn(consent)
    parser = tool["path"]
    try:
        result = subprocess.run([node, "-e", NODE_CHECK, parser, "modern" if allow_modern else ""],
                                input=json.dumps(src.scripts, ensure_ascii=True), capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=15)
        if result.returncode:
            return [("SKIP", "JavaScript syntax checker could not start")]
        errors = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return [("SKIP", "JavaScript syntax checker could not finish")]
    out = []
    if errors:
        out.extend(("FAIL", f"JavaScript syntax: {error[:160]}") for error in errors[:5])
    elif parser:
        label = "ES2017 syntax (ES2020 for opted-in Motion only)" if allow_modern else "ES2017 syntax"
        out.append(("PASS", f"{label}: {len(src.scripts)} inline script(s)"))
    if not parser:
        out.append(("SKIP", "ES2017 syntax: Acorn unavailable"))
    if src.external:
        out.append(("SKIP", f"syntax of {src.external} external script(s)"))
    return out
