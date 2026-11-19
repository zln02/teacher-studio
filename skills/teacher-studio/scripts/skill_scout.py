#!/usr/bin/env python3
"""skill_scout.py - read-only shortlist of existing Agent Skills / plugins.

Usage:  python3 skill_scout.py "pptx presentation" [--no-npx] [--limit 6] [--json]

Queries (all keyless, read-only):
  1. curated list  references/recommended-skills.json (local file)
  2. `npx --yes skills find <kw>`  (vercel-labs/skills CLI; only if node/npx exist; 20s cap)
  3. GitHub search API /search/repositories (10 req/min unauthenticated)
  4. npm registry /-/v1/search
It never installs anything and never runs code it finds. Hard total cap ~25s.
Output is a shortlist for the AI to vet with references/skill-scout.md.
"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request

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


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
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
