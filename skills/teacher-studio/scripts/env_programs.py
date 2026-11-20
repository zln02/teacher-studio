#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Which programs can open the result on THIS computer? Read-only, fast, cached; never installs anything.

Usage:
    python3 env_programs.py [--json] [--refresh]

Looks for: 한글(Hancom), PowerPoint/Word/Excel (Office), LibreOffice, Chrome / Edge / Whale, a PDF reader, Python, Node.
Windows: registry App Paths + uninstall list (DisplayVersion) + `where`; macOS: /Applications/*.app (Info.plist version);
Linux: `which`. Result is cached in ~/.teacher-studio/env.json under "programs" (other keys are kept), re-probed after 7 days.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HOME = Path(os.environ.get("TEACHER_STUDIO_HOME") or Path.home() / ".teacher-studio")
CACHE = HOME / "env.json"
MAX_AGE_DAYS = 7

# key -> Korean name, Windows App Paths exe(s), uninstall DisplayName pattern, macOS app bundle(s), Linux command(s)
PROGRAMS: dict[str, dict] = {
    "hwp": {"name": "한글(한컴오피스)", "exe": ["Hwp.exe"], "uninstall": r"한컴오피스|Hancom ?Office|한글 ?20\d\d|HWP 20\d\d",
            "mac": ["Hancom Office HWP.app", "한컴오피스 한글.app", "Hancom Office HWP 2024.app"], "linux": ["hwp", "hoffice"]},
    "powerpoint": {"name": "PowerPoint", "exe": ["POWERPNT.EXE"], "uninstall": r"Microsoft (365|Office)|PowerPoint",
                   "mac": ["Microsoft PowerPoint.app"], "linux": []},
    "word": {"name": "Word", "exe": ["WINWORD.EXE"], "uninstall": r"Microsoft (365|Office)|Word", "mac": ["Microsoft Word.app"], "linux": []},
    "excel": {"name": "Excel", "exe": ["EXCEL.EXE"], "uninstall": r"Microsoft (365|Office)|Excel", "mac": ["Microsoft Excel.app"], "linux": []},
    "libreoffice": {"name": "LibreOffice", "exe": ["soffice.exe"], "uninstall": r"LibreOffice", "mac": ["LibreOffice.app"],
                    "linux": ["soffice", "libreoffice"]},
    "chrome": {"name": "크롬", "exe": ["chrome.exe"], "uninstall": r"Google Chrome", "mac": ["Google Chrome.app"],
               "linux": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]},
    "edge": {"name": "엣지", "exe": ["msedge.exe"], "uninstall": r"Microsoft Edge$", "mac": ["Microsoft Edge.app"], "linux": ["microsoft-edge"]},
    "whale": {"name": "웨일", "exe": ["whale.exe"], "uninstall": r"Naver Whale|네이버 웨일", "mac": ["Naver Whale.app", "Whale.app"],
              "linux": ["naver-whale", "whale"]},
    "pdf_reader": {"name": "PDF 보기 프로그램", "exe": ["AcroRd32.exe", "Acrobat.exe", "SumatraPDF.exe", "HncPdf.exe"],
                   "uninstall": r"Adobe Acrobat|Acrobat Reader|SumatraPDF|한컴오피스 ?PDF|Hancom PDF",
                   "mac": ["Preview.app", "Adobe Acrobat Reader.app"], "linux": ["evince", "okular", "xdg-open"]},
    "python": {"name": "Python", "exe": [], "uninstall": "", "mac": [], "linux": ["python3", "python"], "where": ["py", "python3", "python"]},
    "node": {"name": "Node", "exe": [], "uninstall": "", "mac": [], "linux": ["node"], "where": ["node"]},
}
# a version below this (first number) is too old for the file type we would hand out
MIN_MAJOR = {"hwp": 9, "powerpoint": 14, "word": 14, "excel": 14, "python": 3, "node": 18}
# 한글 2014 = internal 9.x; Office 2010 = 14.x (older ones open .pptx/.docx badly or not at all)


def _win_registry() -> dict:
    """{'apppaths': {exe_lower: path}, 'uninstall': [(name, version)]}. Empty off Windows or on any error."""
    out: dict = {"apppaths": {}, "uninstall": []}
    try:
        import winreg  # type: ignore
    except ImportError:
        return out
    roots = [(winreg.HKEY_LOCAL_MACHINE, 0), (winreg.HKEY_CURRENT_USER, 0)]
    views = [getattr(winreg, "KEY_WOW64_64KEY", 0), getattr(winreg, "KEY_WOW64_32KEY", 0)]

    def subkeys(h):
        i = 0
        while True:
            try:
                yield winreg.EnumKey(h, i)
            except OSError:
                return
            i += 1
    for root, _ in roots:
        for view in views:
            for path, kind in ((r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths", "apppaths"),
                               (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "uninstall")):
                try:
                    h = winreg.OpenKey(root, path, 0, winreg.KEY_READ | view)
                except OSError:
                    continue
                for name in subkeys(h):
                    try:
                        sk = winreg.OpenKey(h, name)
                        if kind == "apppaths":
                            val = winreg.QueryValueEx(sk, "")[0]
                            out["apppaths"][name.lower()] = str(val).strip('"')
                        else:
                            dn = winreg.QueryValueEx(sk, "DisplayName")[0]
                            try:
                                dv = winreg.QueryValueEx(sk, "DisplayVersion")[0]
                            except OSError:
                                dv = ""
                            out["uninstall"].append((str(dn), str(dv)))
                    except OSError:
                        continue
    return out


def _mac_version(app: Path) -> str:
    try:
        with open(app / "Contents" / "Info.plist", "rb") as f:
            return str(plistlib.load(f).get("CFBundleShortVersionString", ""))
    except (OSError, ValueError, plistlib.InvalidFileException):
        return ""


def _cmd_version(exe: str) -> str:
    try:
        p = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
        m = re.search(r"(\d+(?:\.\d+)+)", (p.stdout or "") + (p.stderr or ""))
        return m.group(1) if m else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _major(v: str) -> int | None:
    m = re.match(r"\s*v?(\d+)", v or "")
    return int(m.group(1)) if m else None


def probe(system: str | None = None, registry: dict | None = None, which=shutil.which, exists=os.path.exists,
          version_of=_cmd_version, mac_version=_mac_version) -> dict:
    """{key: {ok, name, version, outdated, how}}. All OS calls are injectable (tests pass fakes)."""
    system = system or sys.platform
    res: dict = {}
    reg = registry if registry is not None else (_win_registry() if system.startswith("win") else {"apppaths": {}, "uninstall": []})
    for key, spec in PROGRAMS.items():
        ok, ver, how = False, "", ""
        if system.startswith("win"):
            for exe in spec["exe"]:
                p = reg.get("apppaths", {}).get(exe.lower())
                if p and exists(p):
                    ok, how = True, "registry"
                    break
            office = key in ("powerpoint", "word", "excel")  # "Microsoft 365" alone does not prove PowerPoint is there: App Paths does
            if spec["uninstall"] and (ok or not office):
                for dn, dv in reg.get("uninstall", []):
                    if re.search(spec["uninstall"], dn, re.I):
                        ok, how, ver = True, how or "registry", dv
                        if dv:
                            break
            for exe in spec["exe"] if not ok else []:
                if which(exe):
                    ok, how = True, "where"
                    break
        elif system == "darwin":
            for app in spec["mac"]:
                for base in ("/Applications", "/System/Applications", str(Path.home() / "Applications")):
                    p = base.rstrip("/") + "/" + app
                    if exists(p):
                        ok, how, ver = True, "applications", mac_version(Path(p))
                        break
                if ok:
                    break
        if not ok:
            for cmd in (spec.get("where") or []) + (spec["linux"] if not system.startswith("win") and system != "darwin" else []):
                w = which(cmd)
                if w:
                    ok, how = True, "which"
                    if key in ("python", "node", "libreoffice"):
                        ver = version_of(w)
                    break
        mj = _major(ver)
        outdated = bool(ok and mj is not None and key in MIN_MAJOR and mj < MIN_MAJOR[key])
        if key == "hwp" and mj is not None and mj >= 2000:  # some installers report the year (2014, 2020)
            outdated = mj < 2014
        res[key] = {"ok": ok, "name": spec["name"], "version": ver, "outdated": outdated, "how": how}
    # Edge/Chrome/Whale open PDFs too: count them as a PDF reader
    if not res["pdf_reader"]["ok"]:
        for b in ("edge", "chrome", "whale"):
            if res[b]["ok"]:
                res["pdf_reader"] = {"ok": True, "name": res[b]["name"] + "(PDF 열기)", "version": "", "outdated": False, "how": "browser"}
                break
    return res


def load(refresh: bool = False, cache: Path | None = None, today: datetime.date | None = None, **probe_kw) -> dict:
    """Cached probe. Keeps every other key of env.json (doctor.py writes it too)."""
    cache = cache or CACHE
    today = today or datetime.date.today()
    data: dict = {}
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    if not refresh and isinstance(data.get("programs"), dict):
        try:
            age = (today - datetime.date.fromisoformat(str(data.get("programs_checked")))).days
            if 0 <= age <= MAX_AGE_DAYS:
                return data["programs"]
        except ValueError:
            pass
    progs = probe(**probe_kw)
    data["programs"], data["programs_checked"] = progs, today.isoformat()
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    return progs


# which program opens which format (first that is present wins)
OPENERS = {
    ".html": ["chrome", "edge", "whale"],
    ".pdf": ["pdf_reader", "edge", "chrome", "whale"],
    ".pptx": ["powerpoint", "libreoffice", "hwp"],
    ".docx": ["word", "hwp", "libreoffice"],
    ".hwpx": ["hwp", "libreoffice"],
    ".hwp": ["hwp"],
    ".xlsx": ["excel", "libreoffice", "hwp"],
    ".csv": ["excel", "libreoffice", "hwp"],
}
# how to get a missing program: (what to say, size note). Only an OFFER; nothing is installed here.
GET = {
    "hwp": "한컴 홈페이지의 무료 「한글 뷰어」로 열 수 있어요 (보기만 가능, 크기는 설치 화면에 나와요). 아니면 PDF로 드릴게요.",
    "powerpoint": "PowerPoint가 없으면 무료 LibreOffice(약 350MB)로 열 수 있어요. 설치할까요? 아니면 웹 화면(HTML)으로 띄우면 돼요.",
    "word": "Word가 없으면 한글이나 무료 LibreOffice(약 350MB)로 열려요. 아니면 PDF로 드릴게요.",
    "excel": "Excel이 없으면 한글의 한셀이나 무료 LibreOffice(약 350MB)로 열려요. CSV는 메모장으로도 열려요.",
    "libreoffice": "무료 LibreOffice(약 350MB)를 설치하면 열 수 있어요. 설치할까요?",
    "chrome": "엣지나 웨일이 있으면 그걸로 열면 돼요. 없으면 크롬(무료, 약 100MB)을 직접 받아 설치해 주세요.",
    "pdf_reader": "브라우저(엣지·크롬)로 PDF가 열려요.",
}


def opener(ext: str, progs: dict) -> dict:
    """{'ok', 'program', 'outdated', 'offer'} for one file type on this computer."""
    ext = ext.lower()
    cands = OPENERS.get(ext, [])
    for key in cands:
        p = progs.get(key) or {}
        if p.get("ok"):
            offer = ""
            if p.get("outdated"):
                offer = f"{p.get('name')} 버전이 오래돼서 이 파일이 잘 안 열릴 수 있어요. 업데이트할까요? (크기는 업데이트 화면에 나와요)"
            return {"ok": True, "program": p.get("name", key), "outdated": bool(p.get("outdated")), "offer": offer}
    first = cands[0] if cands else ""
    return {"ok": False, "program": "", "outdated": False, "offer": GET.get(first, "이 컴퓨터에서 열 프로그램을 찾지 못했어요. PDF로 바꿔 드릴까요?")}


def can_open(ext: str, progs: dict) -> bool:
    return opener(ext, progs)["ok"]


def summary(progs: dict) -> str:
    have = [p["name"] + (f" {p['version']}" if p.get("version") else "") + (" (오래됨)" if p.get("outdated") else "")
            for p in progs.values() if p.get("ok")]
    miss = [p["name"] for k, p in progs.items() if not p.get("ok") and k not in ("python", "node")]
    return "이 컴퓨터에 있는 것: " + (", ".join(have) or "없음") + ("\n없는 것: " + ", ".join(miss) if miss else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    progs = load(refresh=a.refresh)
    print(json.dumps(progs, ensure_ascii=False, indent=1) if a.json else summary(progs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
