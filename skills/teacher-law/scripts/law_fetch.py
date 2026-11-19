#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Fail-fast reader for law pages: try each official page ONCE with a short timeout, remember what is blocked, then fall back and label the result.

    py law_fetch.py --law 개인정보보호법 --article 17 [--kind 개인정보] [--secondary URL ...] [--timeout 6] [--budget 40] [--json]
    py law_fetch.py --url https://www.pipc.go.kr/... [--url ...]            # your own list, tried in order

Why: the 2026-11 compare run spent 12 minutes retrying a law.go.kr that was blocked. Now:
  1. every URL gets ONE try (connect+read <= --timeout seconds, default 6); a blocked / slow / empty answer is a miss, never retried;
  2. a host that failed is remembered for 30 minutes (~/.teacher-studio/law-blocked.json) so the next lookup skips it at once;
  3. the total time is capped by --budget (default 40 s); when it is spent we stop and say so;
  4. result label: 공식 (official source) / 보조 (secondary, NOT official: say so in the answer) / 못 읽음 (nothing readable: write 「확인 필요」).
Never prints more than --chars characters of page text. Nothing is installed, only the standard library is used. `--legacy` reproduces the old retry
behaviour (3 tries, 30 s each) only so the saving can be measured.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

MEMO = Path.home() / ".teacher-studio" / "law-blocked.json"
MEMO_SECS = 30 * 60
UA = "Mozilla/5.0 (teacher-studio law lookup; reads public pages only)"

# kind -> official entry pages tried after the direct law.go.kr article page (see references/sources.md for what each is good for)
OFFICIAL = {
    "개인정보": ["https://www.pipc.go.kr"],
    "저작권": ["https://www.copyright.or.kr"],
    "AI": ["https://www.msit.go.kr", "https://www.moe.go.kr"],
    "학교": ["https://www.moe.go.kr"],
    "": ["https://www.moleg.go.kr"],
}


def host_of(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()


def _memo() -> dict:
    try:
        d = json.loads(MEMO.read_text(encoding="utf-8"))
        return {h: t for h, t in d.items() if time.time() - t < MEMO_SECS}
    except Exception:
        return {}


def _remember(host: str) -> None:
    d = _memo()
    d[host] = time.time()
    try:
        MEMO.parent.mkdir(parents=True, exist_ok=True)
        MEMO.write_text(json.dumps(d), encoding="utf-8")
    except Exception:
        pass


def to_text(raw: bytes, ctype: str, chars: int) -> tuple[str, str]:
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I) or re.search(rb"charset=[\"']?([\w-]+)", raw[:2000], re.I)
    enc = (m.group(1).decode() if isinstance(m.group(1), bytes) else m.group(1)) if m else "utf-8"
    try:
        s = raw.decode(enc, "replace")
    except LookupError:
        s = raw.decode("utf-8", "replace")
    tm = re.search(r"<title[^>]*>(.*?)</title>", s, re.S | re.I)
    s = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return html.unescape(tm.group(1)).strip() if tm else "", re.sub(r"\s+", " ", s).strip()[:chars]


def fetch_once(url: str, timeout: float, chars: int) -> dict:
    t0 = time.time()
    r = {"url": url, "ok": False, "secs": 0.0, "status": None, "title": "", "text": "", "why": ""}
    try:
        url = urllib.parse.quote(url, safe=":/?&=%#+,;@~-._")  # Korean letters in a path or query -> %XX
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko,en;q=0.5"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            r["status"] = resp.status
            raw = resp.read(600_000)
            r["title"], r["text"] = to_text(raw, resp.headers.get("Content-Type", ""), chars)
            r["ok"] = len(r["text"]) >= 200
            if not r["ok"]:
                r["why"] = "내용이 거의 없음(스크립트로 그려지는 페이지일 수 있어요)"
    except urllib.error.HTTPError as e:
        r["status"], r["why"] = e.code, f"HTTP {e.code} (접속 거부·차단일 수 있어요)"
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as e:
        r["why"] = f"{type(e).__name__}: 시간 초과 또는 접속 불가"
    r["secs"] = round(time.time() - t0, 2)
    return r


def law_url(law: str, article: str) -> str:
    name = urllib.parse.quote(law)
    return f"https://www.law.go.kr/법령/{name}" + (f"/제{urllib.parse.quote(str(article))}조" if article else "")


def run(urls: list[tuple[str, str]], timeout: float, budget: float, chars: int, legacy: bool = False) -> dict:
    """urls: [(url, label)] in order. Returns {'result': first success or None, 'tries': [...], 'secs': total, 'stopped': reason}."""
    t0, tries, blocked = time.time(), [], _memo()
    for url, label in urls:
        h = host_of(url)
        if not legacy and h in blocked:
            tries.append({"url": url, "label": label, "ok": False, "secs": 0.0, "why": "방금 막힌 곳이라 건너뜀(30분 기억)"})
            continue
        left = budget - (time.time() - t0)
        if not legacy and left <= 1:
            return {"result": None, "tries": tries, "secs": round(time.time() - t0, 1), "stopped": f"시간 한도 {budget:.0f}초를 다 썼어요"}
        attempts = 3 if legacy else 1
        for k in range(attempts):
            r = fetch_once(url, timeout if legacy is False else 30.0, chars)
            r["label"] = label
            tries.append(r)
            if r["ok"]:
                return {"result": r, "tries": tries, "secs": round(time.time() - t0, 1), "stopped": ""}
        if not legacy:
            _remember(h)
    return {"result": None, "tries": tries, "secs": round(time.time() - t0, 1), "stopped": "읽을 수 있는 곳이 없었어요"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--law")
    ap.add_argument("--article")
    ap.add_argument("--kind", default="", help="개인정보 | 저작권 | AI | 학교 (picks the official entry pages)")
    ap.add_argument("--url", action="append", default=[], help="official URL (repeatable, tried in order)")
    ap.add_argument("--secondary", action="append", default=[], help="secondary (non-official) URL, tried only after the official ones")
    ap.add_argument("--timeout", type=float, default=6.0)
    ap.add_argument("--budget", type=float, default=40.0)
    ap.add_argument("--chars", type=int, default=1500)
    ap.add_argument("--legacy", action="store_true", help="old behaviour (3 tries x 30 s, no memory): for measuring only")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    urls = [(u, "공식") for u in a.url]
    if a.law:
        urls.insert(0, (law_url(a.law, a.article or ""), "공식"))
    urls += [(u, "공식") for u in OFFICIAL.get(a.kind, OFFICIAL[""]) if (u, "공식") not in urls]
    urls += [(u, "보조") for u in a.secondary]
    if not urls:
        ap.error("--law, --url or --secondary needed")
    res = run(urls, a.timeout, a.budget, a.chars, a.legacy)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0 if res["result"] else 2
    for t in res["tries"]:
        print(f"{'OK  ' if t['ok'] else 'MISS'} [{t['label']}] {t['secs']:>5}s {t['url']}" + ("" if t["ok"] else f"  ({t['why']})"))
    r = res["result"]
    if r:
        tag = "공식 출처" if r["label"] == "공식" else "보조 출처(공식 아님: 답에 그렇게 적으세요)"
        print(f"\n=== {tag}: {r['title']}\n{r['text']}\n(총 {res['secs']}초)")
        return 0
    print(f"\n못 읽음: {res['stopped']} (총 {res['secs']}초). 답에는 「확인 필요」라고 쓰고 공식 링크만 안내하세요. 더 재시도하지 마세요.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
