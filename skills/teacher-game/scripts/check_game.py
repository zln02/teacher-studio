#!/usr/bin/env python3
"""Static quality check for a Teacher Studio game HTML game.

Usage: python3 check_game.py game.html
Prints PASS/WARN/FAIL lines and exits 1 if any FAIL.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOWED_HOSTS = ("cdnjs.cloudflare.com", "cdn.jsdelivr.net/npm/", "unpkg.com", "fonts.googleapis.com", "fonts.gstatic.com")
FORBIDDEN_JS = {
    r"\?\.(?=[A-Za-z_$\[(])": "optional chaining ?. (old Chrome)",
    r"\?\?": "nullish ?? (old Chrome)",
    r"\.replaceAll\(": "replaceAll (old Chrome)",
    r"\.at\(\s*-?\d": ".at() (old Chrome)",
    r"structuredClone\(": "structuredClone (old Chrome)",
    r"(?<![\w$])#[a-zA-Z_]\w*\s*[=(;]": "#private field (old Chrome)",
    r"\balert\(|\bprompt\(|\bconfirm\(": "alert/prompt/confirm blocks the game",
}
FORBIDDEN_CSS = {
    r"aspect-ratio\s*:": "aspect-ratio (old Chrome)",
    r":has\(": ":has() (old Chrome)",
    r"\b\d+(\.\d+)?dvh\b": "dvh unit (old Chrome)",
}
STUDENT_DATA = re.compile(r"(학번|이름을?\s*입력|실명|student\s*name|전화번호)", re.I)


def _bracket_body(src: str, i: int) -> str:
    """Return the text inside the [ ... ] that opens at index i."""
    depth, quote, prev = 0, "", ""
    for j in range(i, len(src)):
        ch = src[j]
        if quote:
            if ch == quote and prev != "\\":
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                return src[i + 1:j]
        prev = ch
    return src[i + 1:]


def _top_level_objects(src: str) -> int:
    """Count {...} objects at depth 0 of an array body (ignores braces inside strings)."""
    depth, n, quote, prev = 0, 0, "", ""
    for ch in src:
        if quote:
            if ch == quote and prev != "\\":
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            if depth == 0:
                n += 1
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        prev = ch
    return n


def main(path: Path) -> int:
    """Run all checks and print a report. Returns process exit code."""
    if not path.exists():
        print(f"FAIL file not found: {path}")
        return 1
    html = path.read_text(encoding="utf-8", errors="replace")
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)  # ignore HTML comments
    results: list[tuple[str, str]] = []

    def add(level: str, msg: str) -> None:
        results.append((level, msg))

    size_kb = len(html.encode()) / 1024
    add("PASS" if size_kb < 2048 else "FAIL", f"file size {size_kb:.0f} KB")
    add("PASS" if html.lstrip().lower().startswith("<!doctype html") else "FAIL", "starts with <!DOCTYPE html>")
    is_stage = "STAGE RUNTIME (do not edit" in html
    markers = (
        (("window.DOC =", "DOC data block"), ("window.SHOW", "SHOW block"), ("STAGE.boot()", "STAGE.boot() call"),
         ("STAGE RUNTIME (do not edit", "stage runtime intact"), ("b-full", "fullscreen button kept"),
         ("Anime.js", "anime.js inlined"))
        if is_stage else
        (("window.GAME =", "GAME data block"), ("window.GAME_LOGIC", "GAME_LOGIC block"),
         ("NG.boot()", "NG.boot() call"), ("ENGINE (do not edit", "engine block intact"),
         ("ng-mute", "mute button kept"), ("Teacher.open", "teacher menu kept"))
    )
    for marker, label in markers:
        add("PASS" if marker in html else "FAIL", label)

    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
    js = "\n".join(scripts)
    js_nostr = re.sub(r"//[^\n]*|/\*.*?\*/", "", js, flags=re.S)
    js_nostr = re.sub(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"", "''", js_nostr)
    for pat, label in FORBIDDEN_JS.items():
        hits = len(re.findall(pat, js_nostr))
        add("FAIL" if hits else "PASS", f"no {label}" + (f" ({hits} found)" if hits else ""))
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)) + "\n" + " ".join(re.findall(r'style="([^"]*)"', html))
    for pat, label in FORBIDDEN_CSS.items():
        hits = len(re.findall(pat, css))
        add("FAIL" if hits else "PASS", f"no {label}" + (f" ({hits} found)" if hits else ""))

    urls = re.findall(r"""(?:src|href)\s*=\s*["'](https?://[^"']+)""", html) + re.findall(r"url\(\s*['\"]?(https?://[^)'\"]+)", html)
    bad = sorted({u for u in urls if not any(h in u for h in ALLOWED_HOSTS)})
    add("FAIL" if bad else "PASS", "external resources only from cdnjs / jsdelivr npm / unpkg / Google Fonts" + (f": {bad[:3]}" if bad else ""))
    cdn = re.findall(r"cdnjs\.cloudflare\.com/ajax/libs/[^/]+/([^/]+)/", html)
    cdn += re.findall(r"cdn\.jsdelivr\.net/npm/(?:@[^/]+/)?[^@/]+@([^/]+)/", html)
    if any(not re.match(r"\d+\.\d+", v) for v in cdn):
        add("FAIL", "cdnjs URLs must pin an exact version")
    if re.search(r"<img[^>]+src=[\"']https?:", html):
        add("FAIL", "no external <img>")
    if re.search(r"\bdraggable\s*=\s*[\"']?true", html) or "dragstart" in js_nostr:
        add("WARN", "HTML5 drag API does not work on tablets; use NG.drag")
    if STUDENT_DATA.search(html):
        add("WARN", "possible student personal data field (이름/학번) — remove unless clearly fictional")
    logs = len(re.findall(r"console\.log\(", js_nostr))
    if logs:
        add("WARN", f"{logs} console.log left")

    g = -1 if is_stage else html.find("window.GAME")
    m = re.compile(r"[\"']?items[\"']?\s*:\s*\[").search(html, g) if g >= 0 else None
    count = _top_level_objects(_bracket_body(html, m.end() - 1)) if m else 0
    add("PASS" if count or not m else "WARN", f"GAME.items has {count} entries")

    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
            tmp.write(js)
        proc = subprocess.run([node, "--check", tmp.name], capture_output=True, text=True)
        add("PASS" if proc.returncode == 0 else "FAIL", "JavaScript syntax" + ("" if proc.returncode == 0 else ": " + proc.stderr.strip().splitlines()[-1][:160]))
    else:
        add("WARN", "node not found; JavaScript syntax not checked")

    for level, msg in results:
        print(f"{level:4} {msg}")
    fails = sum(1 for lv, _ in results if lv == "FAIL")
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({fails} fail, {sum(1 for lv, _ in results if lv == 'WARN')} warn)")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(Path(sys.argv[1])))
