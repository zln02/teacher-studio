"""Fire every existing game skin, check it, and log PASS/FAIL + sha256 + size.
Usage: python examples/baseline/run_baseline.py <outdir>   (writes game-baseline.json next to this file)"""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "skills" / "teacher-studio" / "scripts" / "studio.py"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
res = []
for m in sorted((ROOT / "skills/teacher-game/assets/missiles").iterdir()):
    for s in sorted((m / "skins").glob("*.json")):
        f = out / f"{m.name}-{s.stem}.html"
        p = subprocess.run([sys.executable, str(STUDIO), "fire", f"game/{m.name}/{s.stem}", "--out", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        c = subprocess.run([sys.executable, str(STUDIO), "check", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        ok = p.returncode == 0 and c.returncode == 0 and "RESULT: PASS" in c.stdout
        b = f.read_bytes() if f.exists() else b""
        res.append({"skin": f"{m.name}/{s.stem}", "result": "PASS" if ok else "FAIL", "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)})
(Path(__file__).parent / "game-baseline.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps([(r["skin"], r["result"], r["bytes"]) for r in res], ensure_ascii=False))
