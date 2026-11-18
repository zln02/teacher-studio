#!/usr/bin/env python3
"""Install-on-first-need helper: check a tool, ask in plain Korean, install only with consent.

    from ensure import ensure, ensure_ffmpeg, ensure_playwright
    res = ensure("python-pptx")            # -> {"ok": False, "prompt": "PPT 파일을 만들려면 ... 설치할까요? (약 6MB)", ...}
    res = ensure("python-pptx", consent=True)   # installs with:  python -m pip install --user python-pptx

CLI:
    python3 ensure.py status                 # which tools are present / install on first need (JSON with --json)
    python3 ensure.py <name> [--yes]         # check, or install with --yes
    python3 ensure.py ffmpeg [--yes]         # system ffmpeg first, else imageio-ffmpeg's bundled binary
    python3 ensure.py playwright [--yes]     # system Chrome/Edge first, else (with --yes) download Chromium

Rules: nothing is installed without consent=True / --yes; no ffmpeg binary is ever shipped in this repo.
If the network looks off (typical for Codex's default sandbox) the prompt says how to allow it.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import platform
import shutil
import site
import socket
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

# name -> import name(s), pip package(s), approximate size, why (plain Korean, shown to teachers)
PACKAGES: dict[str, dict] = {
    "fonttools": {"imports": ["fontTools", "brotli"], "pip": ["fonttools", "brotli"], "mb": 3,
                  "why": "글꼴을 파일 안에 넣어서 인터넷이 없어도 예쁘게 보이게 하려면"},
    "python-pptx": {"imports": ["pptx"], "pip": ["python-pptx"], "mb": 6, "why": "PPT 파일(.pptx)을 만들려면"},
    "python-docx": {"imports": ["docx"], "pip": ["python-docx"], "mb": 4, "why": "워드 파일(.docx)을 만들려면"},
    "openpyxl": {"imports": ["openpyxl"], "pip": ["openpyxl"], "mb": 3, "why": "엑셀 파일(.xlsx)을 만들거나 읽으려면"},
    "python-hwpx": {"imports": ["hwpx"], "pip": ["python-hwpx"], "mb": 3, "why": "한글 파일(.hwpx)을 만들려면"},
    "pypdf": {"imports": ["pypdf"], "pip": ["pypdf"], "mb": 2, "why": "PDF를 합치거나 나누거나 읽으려면"},
    "pillow": {"imports": ["PIL"], "pip": ["pillow"], "mb": 3, "why": "사진 크기를 줄이거나 자르려면"},
    "qrcode": {"imports": ["qrcode"], "pip": ["qrcode"], "mb": 1, "why": "QR 코드를 만들려면"},
    "imageio-ffmpeg": {"imports": ["imageio_ffmpeg"], "pip": ["imageio-ffmpeg"], "mb": 40, "why": "영상 파일(MP4)을 만들거나 자르려면"},
    "playwright": {"imports": ["playwright"], "pip": ["playwright"], "mb": 40, "why": "화면을 직접 열어 보고 영상으로 녹화하려면"},
}
CODEX_NETWORK_HELP = ("인터넷이 막혀 있어요. Codex에서는 ~/.codex/config.toml 에 [sandbox_workspace_write] 아래 network_access = true 를 넣고 "
                      "Codex를 다시 시작해 주세요. (회사·학교 망이면 pypi.org 접속이 허용돼야 해요.)")


def _importable(mod: str) -> bool:
    """True when `mod` can be imported (user site is added if pip just created it)."""
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def is_present(name: str) -> bool:
    """True when every module of the package can be imported."""
    spec = PACKAGES[name]
    return all(_importable(m) for m in spec["imports"])


def network_ok(host: str = "pypi.org", timeout: float = 3.0) -> bool:
    """Quick check that the network is reachable (DNS + TCP 443)."""
    try:
        with socket.create_connection((host, 443), timeout=timeout):
            return True
    except OSError:
        return False


def _prompt(name: str, spec: dict) -> str:
    size = f"약 {spec['mb']}MB"
    return f"{spec['why']} 작은 도구({name}, {size})를 한 번만 설치해야 해요. 설치할까요? (선생님 컴퓨터에만 설치돼요)"


def _pip_install(packages: list[str]) -> tuple[bool, str]:
    """python -m pip install --user ... (falls back to no --user inside a virtualenv)."""
    base = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    for extra in (["--user"], []):
        r = subprocess.run(base + extra + packages, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            importlib.invalidate_caches()
            try:
                user = site.getusersitepackages()
                if os.path.isdir(user) and user not in sys.path:
                    site.addsitedir(user)
            except Exception:
                pass
            return True, ""
        err = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
        if "--user" in extra and "virtual" not in (r.stderr or "").lower():
            return False, err[0]
    return False, err[0]


def ensure(name: str, consent: bool = False) -> dict:
    """Check a tool; install it only when consent is True.

    Returns {name, ok, installed_now, size_mb, prompt, error}. `prompt` (plain Korean) is what to say to the teacher when ok is False.
    """
    if name not in PACKAGES:
        raise KeyError(f"unknown tool '{name}' (known: {', '.join(PACKAGES)})")
    spec = PACKAGES[name]
    res = {"name": name, "ok": False, "installed_now": False, "size_mb": spec["mb"], "prompt": "", "error": ""}
    if is_present(name):
        res["ok"] = True
        return res
    if not consent:
        res["prompt"] = _prompt(name, spec)
        if not network_ok():
            res["prompt"] += " 지금은 " + CODEX_NETWORK_HELP
        return res
    if not network_ok():
        res["error"] = "network"
        res["prompt"] = CODEX_NETWORK_HELP
        return res
    ok, err = _pip_install(spec["pip"])
    res["installed_now"] = ok
    res["ok"] = ok and is_present(name)
    if not res["ok"]:
        res["error"] = err or "install failed"
        res["prompt"] = f"{name} 설치가 안 됐어요. 인터넷이나 권한 문제일 수 있어요: {err}".strip()
    return res


def ensure_ffmpeg(consent: bool = False) -> dict:
    """ffmpeg for video: system ffmpeg on PATH first, else imageio-ffmpeg's bundled binary (pip, ~40MB), else a consent prompt.

    Returns {ok, path, source ('system'|'imageio-ffmpeg'|''), prompt}. No ffmpeg binary is ever shipped in this repo.
    """
    found = shutil.which("ffmpeg")
    if found:
        return {"ok": True, "path": found, "source": "system", "prompt": ""}
    res = ensure("imageio-ffmpeg", consent=consent)
    if res["ok"]:
        try:
            exe = importlib.import_module("imageio_ffmpeg").get_ffmpeg_exe()
            return {"ok": True, "path": exe, "source": "imageio-ffmpeg", "prompt": ""}
        except Exception as exc:  # pragma: no cover - platform specific
            return {"ok": False, "path": "", "source": "", "prompt": f"영상 도구를 찾지 못했어요: {exc}"}
    win = platform.system() == "Windows"
    prompt = res["prompt"] or "영상 파일을 만들려면 영상 도구(ffmpeg)가 필요해요."
    if "40MB" not in prompt and not win:
        prompt += " (영상 도구는 보통 40~70MB예요)"
    return {"ok": False, "path": "", "source": "", "prompt": prompt}


def find_system_browser() -> str:
    """Playwright channel of an installed browser ('chrome' or 'msedge'), or ''."""
    cands = {
        "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                   "/Applications/Google Chrome.app", "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"],
        "msedge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                   "/Applications/Microsoft Edge.app", "/usr/bin/microsoft-edge"],
    }
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        cands["chrome"].append(str(Path(local) / "Google" / "Chrome" / "Application" / "chrome.exe"))
    for channel, paths in cands.items():
        if any(Path(p).exists() for p in paths) or shutil.which(channel) or shutil.which("google-chrome" if channel == "chrome" else channel):
            return channel
    return ""


def ensure_playwright(consent: bool = False) -> dict:
    """Playwright with a browser: system Chrome/Edge first (launch with channel=...), Chromium download only as a last resort.

    Returns {ok, channel, prompt}. Launch with  pw.chromium.launch(channel=res["channel"]) when channel is set.
    """
    res = ensure("playwright", consent=consent)
    channel = find_system_browser()
    if not res["ok"]:
        return {"ok": False, "channel": channel, "prompt": res["prompt"]}
    if channel:
        return {"ok": True, "channel": channel, "prompt": ""}
    if not consent:
        return {"ok": False, "channel": "", "prompt": "컴퓨터에 크롬이나 엣지가 없어서 화면 녹화용 브라우저(약 150MB)를 따로 내려받아야 해요. 설치할까요?"}
    if not network_ok():
        return {"ok": False, "channel": "", "prompt": CODEX_NETWORK_HELP}
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {"ok": r.returncode == 0, "channel": "", "prompt": "" if r.returncode == 0 else "브라우저 내려받기에 실패했어요. 인터넷을 확인해 주세요."}


def status() -> dict:
    """Which tools are present now and which would install on first need (for doctor.py)."""
    present, on_demand = [], []
    for name, spec in PACKAGES.items():
        (present if is_present(name) else on_demand).append({"name": name, "mb": spec["mb"], "why": spec["why"]})
    ff = shutil.which("ffmpeg")
    return {"present": present, "on_first_need": on_demand, "ffmpeg": "system" if ff else ("imageio-ffmpeg" if is_present("imageio-ffmpeg") else ""),
            "browser": find_system_browser(), "network": network_ok()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", help="status | ffmpeg | playwright | " + " | ".join(PACKAGES))
    ap.add_argument("--yes", action="store_true", help="the teacher agreed: install now")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.what == "status":
        out = status()
    elif a.what == "ffmpeg":
        out = ensure_ffmpeg(a.yes)
    elif a.what == "playwright":
        out = ensure_playwright(a.yes)
    else:
        out = ensure(a.what, a.yes)
    if a.json or a.what == "status":
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(out.get("prompt") or ("OK " + str({k: v for k, v in out.items() if k not in ("prompt", "error") and v})))
    return 0 if a.what == "status" or out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
