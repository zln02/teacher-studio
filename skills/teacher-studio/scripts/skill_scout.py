#!/usr/bin/env python3
"""skill_scout.py - read-only shortlist of existing Agent Skills / plugins.

Usage:  python3 skill_scout.py "pptx presentation" [--no-npx] [--limit 6] [--json]
        python3 skill_scout.py verify owner/repo [--json]      # before recommending: exists? license? fresh? no curl|sh?
        python3 skill_scout.py log --name pptx --source https://github.com/anthropics/skills --license Apache-2.0 [--kind skill|doc|asset]
        python3 skill_scout.py log --list                      # local provenance file ~/.teacher-studio/used.json (no personal data)

Queries (all keyless, read-only):
  1. curated list  references/recommended-skills.json (local file)
  2. `npx --yes skills find <kw>`  (vercel-labs/skills CLI; only if node/npx exist; 20s cap)
  3. GitHub search API /search/repositories (10 req/min unauthenticated)
  4. npm registry /-/v1/search
It never installs anything and never runs code it finds. Hard total cap ~25s.
Output is a shortlist for the AI to vet with references/skill-scout.md.
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CURATED = os.path.join(HERE, "..", "references", "recommended-skills.json")
DEADLINE = time.time() + 25
OFFICIAL = {"anthropics", "google", "googlechrome", "openai", "vercel-labs", "cloudflare",
            "microsoft", "github", "supabase", "figma"}
UA = {"User-Agent": "teacher-studio-skill-scout", "Accept": "application/json"}


def left():
    return max(1.0, DEADLINE - time.time())


def get_json(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=min(8, left())) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            return None, "rate-limited (HTTP %d); try again in a minute" % e.code
        return None, "HTTP %d" % e.code
    except Exception as e:  # network off, timeout, bad json
        return None, type(e).__name__


def curated(words):
    out = []
    try:
        data = json.load(open(CURATED, encoding="utf-8"))
    except Exception:
        return out
    for s in data.get("skills", []):
        hay = (" ".join(s.get("tasks", [])) + " " + s.get("name", "") + " " + s.get("for", "")).lower()
        if any(w in hay for w in words):
            out.append({"src": "curated", "name": s["name"], "publisher": s["publisher"],
                        "signal": "vetted " + s.get("checked", "?"), "license": s.get("license", "?"),
                        "updated": s.get("checked", "?"), "url": s["url"],
                        "note": s.get("for", ""), "install": s.get("install", "")})
    return out


def npx_find(q):
    exe = shutil.which("npx")
    if not exe or not shutil.which("node"):
        return [], "node/npx not found (skipped)"
    try:
        p = subprocess.run([exe, "--yes", "skills", "find"] + q.split(), capture_output=True, text=True,
                           timeout=min(20, left()), stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return [], "npx skills find timed out (skipped)"
    except Exception as e:
        return [], "npx failed: " + type(e).__name__
    txt = re.sub(r"\x1b\[[0-9;]*m", "", p.stdout or "")
    res = []
    for m in re.finditer(r"^\s*(\S+/\S+@\S+)\s+([\d.,]+[KMkm]?)\s+installs", txt, re.M):
        ident, n = m.group(1), m.group(2)
        owner, rest = ident.split("/", 1)
        res.append({"src": "skills.sh", "name": rest, "publisher": owner, "signal": n + " installs",
                    "license": "check in repo", "updated": "?",
                    "url": "https://skills.sh/" + owner + "/" + rest.replace("@", "/", 1),
                    "install": "npx skills add " + ident})
    return res, (None if res else "no results")


def github(q):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": q + " (skill OR skills OR agent-skills) in:name,description,topics", "sort": "stars",
         "order": "desc", "per_page": 8})
    d, err = get_json(url)
    res = []
    for i in (d or {}).get("items", []):
        lic = (i.get("license") or {}).get("spdx_id") or "NONE/unknown"
        res.append({"src": "github", "name": i["full_name"], "publisher": i["owner"]["login"],
                    "signal": "%s stars" % i["stargazers_count"], "license": lic,
                    "updated": (i.get("pushed_at") or "?")[:10], "url": i["html_url"],
                    "note": (i.get("description") or "")[:80]})
    return res, err


def npm(q):
    url = "https://registry.npmjs.org/-/v1/search?" + urllib.parse.urlencode(
        {"text": q + " agent skill", "size": 6})
    d, err = get_json(url)
    res = []
    for o in (d or {}).get("objects", []):
        p = o["package"]
        res.append({"src": "npm", "name": p["name"], "publisher": (p.get("publisher") or {}).get("username", "?"),
                    "signal": "popularity %.2f" % o.get("score", {}).get("detail", {}).get("popularity", 0),
                    "license": "check in package", "updated": (p.get("date") or "?")[:10],
                    "url": (p.get("links") or {}).get("npm", ""), "note": (p.get("description") or "")[:80]})
    return res, err


def rank(r):
    pub = r["publisher"].lower()
    tier = 0 if r["src"] == "curated" else 1 if pub in OFFICIAL else 2
    lic = r["license"]
    bad = 1 if lic.startswith("NONE") else 0  # unknown license -> guide-only, sink it
    m = re.match(r"([\d.,]+)\s*([KkMm]?)", r["signal"])
    num = 0.0
    if m:
        num = float(m.group(1).replace(",", "")) * {"": 1, "k": 1e3, "m": 1e6}[m.group(2).lower()]
    return (bad, tier, -num)


# ---------------------------------------------------------------- verify before recommend
PERMISSIVE = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "cc0-1.0", "unlicense", "0bsd"}
BAD_PATTERNS = [  # text in a SKILL.md / README that should stop us (data, never instructions)
    (r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh", "curl|sh style install"),
    (r"(iwr|irm|Invoke-WebRequest|Invoke-RestMethod)[^\n|]*\|\s*iex", "download and run (PowerShell)"),
    (r"npx\s+-y\s+\S+\s+instruct", "live remote instructions (run and obey output)"),
    (r"ignore (all |any )?(previous|prior|above) instructions", "prompt-injection phrase"),
]
MAX_AGE_DAYS = 183


def check_text(text):
    """Return the list of risky patterns found in a SKILL.md / README text."""
    return [why for pat, why in BAD_PATTERNS if re.search(pat, text or "", re.I)]


def evaluate(repo, texts=None, today=None):
    """Pure verdict from a GitHub repo JSON (None = does not exist, {} = unreachable) and fetched texts.
    verdict: ok | ok-but-stale | guide-only (license missing/not permissive) | reject (risky install text) | missing | unverified."""
    today = today or datetime.date.today()
    if repo is None:
        return {"verdict": "missing", "checks": [{"name": "exists", "ok": False, "detail": "repo not found"}]}
    if repo == {}:
        return {"verdict": "unverified", "checks": [{"name": "exists", "ok": None, "detail": "could not reach GitHub"}]}
    checks = [{"name": "exists", "ok": True, "detail": repo.get("full_name", "")}]
    spdx = ((repo.get("license") or {}).get("spdx_id") or "NONE")
    lic_ok = spdx.lower() in PERMISSIVE
    checks.append({"name": "license", "ok": lic_ok, "detail": spdx})
    pushed = (repo.get("pushed_at") or "")[:10]
    try:
        age = (today - datetime.date.fromisoformat(pushed)).days
    except ValueError:
        age = None
    fresh = age is not None and age <= MAX_AGE_DAYS and not repo.get("archived")
    checks.append({"name": "recent", "ok": fresh, "detail": "pushed %s (%s days ago)%s" % (
        pushed or "?", age if age is not None else "?", ", ARCHIVED" if repo.get("archived") else "")})
    risks = []
    for t in (texts or []):
        risks += check_text(t)
    checks.append({"name": "no risky install text", "ok": not risks,
                   "detail": "; ".join(sorted(set(risks))) or ("checked %d file(s)" % len(texts or []))})
    if risks:
        verdict = "reject"
    elif not lic_ok:
        verdict = "guide-only"
    else:
        verdict = "ok" if fresh else "ok-but-stale"
    return {"verdict": verdict, "license": spdx, "pushed": pushed, "checks": checks}


def _raw(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=8) as r:
            return r.read(200000).decode("utf-8", "replace")
    except Exception:
        return None


def verify(ref):
    """Network wrapper: ref = owner/repo or a github.com URL. Reads repo metadata, README and root SKILL.md. Installs nothing."""
    m = re.search(r"(?:github\.com/)?([\w.-]+)/([\w.-]+?)(?:\.git)?(?:/|$)", ref.strip())
    if not m:
        return {"verdict": "unverified", "checks": [{"name": "ref", "ok": False, "detail": "not an owner/repo"}]}
    owner, name = m.group(1), m.group(2)
    d, err = get_json("https://api.github.com/repos/%s/%s" % (owner, name))
    if d is None:
        r = evaluate(None if err == "HTTP 404" else {})
        r["error"] = err
        return r
    base = "https://raw.githubusercontent.com/%s/%s/%s/" % (owner, name, d.get("default_branch", "main"))
    texts = [t for t in (_raw(base + f) for f in ("SKILL.md", "README.md")) if t]
    return evaluate(d, texts)


# ---------------------------------------------------------------- provenance log
def used_path():
    home = os.environ.get("TEACHER_STUDIO_HOME") or os.path.join(os.path.expanduser("~"), ".teacher-studio")
    return os.path.join(home, "used.json")


def _clean(v, n=200):
    return re.sub(r"[\x00-\x1f]", " ", str(v or "")).strip()[:n]


def log_use(name, source, license_, kind="skill", note="", today=None):
    """Append one record {name, source, license, kind, date}. Only what the caller passes, trimmed; same name+source = one row."""
    path = used_path()
    try:
        rows = json.loads(open(path, encoding="utf-8").read())
        rows = rows if isinstance(rows, list) else []
    except Exception:
        rows = []
    rec = {"name": _clean(name, 80), "source": _clean(source), "license": _clean(license_, 60) or "unknown",
           "kind": kind if kind in ("skill", "doc", "asset") else "skill", "date": str(today or datetime.date.today())}
    if note:
        rec["note"] = _clean(note, 120)
    rows = [r for r in rows if not (r.get("name") == rec["name"] and r.get("source") == rec["source"])] + [rec]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows[-200:], f, ensure_ascii=False, indent=1)
    return rec


def credit_line(rec):
    return "출처: %s (%s, %s)" % (rec["name"], rec["source"], rec["license"])


def cli_verify(argv):
    ap = argparse.ArgumentParser(prog="skill_scout.py verify")
    ap.add_argument("ref")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = verify(a.ref)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("verify %s -> %s" % (a.ref, r["verdict"].upper()))
        for c in r["checks"]:
            print("  [%s] %s: %s" % ({True: "ok", False: "NO", None: "?"}[c["ok"]], c["name"], c["detail"]))
        print("ok = may recommend (still ask before install); guide-only = describe, do not install; reject/missing = do not use; unverified = say so.")
    return 0 if r["verdict"].startswith("ok") else 1


def cli_log(argv):
    ap = argparse.ArgumentParser(prog="skill_scout.py log")
    ap.add_argument("--name")
    ap.add_argument("--source")
    ap.add_argument("--license", default="unknown")
    ap.add_argument("--kind", default="skill")
    ap.add_argument("--note", default="")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        try:
            print(json.dumps(json.loads(open(used_path(), encoding="utf-8").read()), ensure_ascii=False, indent=1))
        except Exception:
            print("[]")
        return 0
    if not a.name or not a.source:
        ap.error("--name and --source are required")
    rec = log_use(a.name, a.source, a.license, a.kind, a.note)
    print("logged -> %s\n%s" % (used_path(), credit_line(rec)))
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) > 1 and sys.argv[1] in ("verify", "log"):
        sys.exit({"verify": cli_verify, "log": cli_log}[sys.argv[1]](sys.argv[2:]))
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--no-npx", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    words = [w for w in re.split(r"\W+", a.query.lower()) if len(w) > 1]
    rows, notes = curated(words), []
    steps = [("github", github)] + ([] if a.no_npx else [("skills.sh", npx_find)]) + [("npm", npm)]
    for name, fn in steps:
        if time.time() > DEADLINE:
            notes.append(name + ": skipped (time cap)")
            continue
        r, err = fn(a.query)
        rows += r
        if err:
            notes.append("%s: %s" % (name, err))
    seen, uniq = set(), []
    for r in sorted(rows, key=rank):
        k = r["url"].lower()
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    uniq = uniq[: a.limit]
    if a.json:
        print(json.dumps({"query": a.query, "results": uniq, "notes": notes}, ensure_ascii=False, indent=1))
        return
    print("Skill scout (read-only shortlist, nothing installed) - query: %s" % a.query)
    for n, r in enumerate(uniq, 1):
        print("%d. [%s] %s  by %s  | %s | license: %s | updated: %s" % (
            n, r["src"], r["name"], r["publisher"], r["signal"], r["license"], r["updated"]))
        print("   %s" % r["url"])
        if r.get("note"):
            print("   " + r["note"])
        if r.get("install"):
            print("   install (only after teacher OK): " + r["install"])
    for n in notes:
        print("note - " + n)
    print("NEXT: vet with references/skill-scout.md (read SKILL.md + scripts, license, privacy) before any use.")


if __name__ == "__main__":
    main()
