#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Work folders and the "can a browser start here?" probe, for every Teacher Studio script.

Why this file exists (measured in docs/research/cross-vendor-fix-2026-11.md):
  * Python 3.12.4+ on Windows makes `tempfile.mkdtemp()` / `TemporaryDirectory()` folders readable by their creator only.
    Inside an agent's security box (Codex on Windows) the script runs with a narrower identity, so it can create that folder
    and then cannot write into it - wherever TEMP points. Scripts therefore never use those two calls.
  * The same box refuses the pipes a headless browser needs, so Playwright / Chrome cannot start at all.

    import workdir
    with workdir.temp_dir("deck", near=out_path) as td: ...   # a plain folder next to the output, removed afterwards
    d = workdir.make("deck", near=out_path)                   # same, kept until workdir.cleanup(d)
    p = workdir.named("storyboard.html")                      # a stable scratch file (system temp first, then the work folder)
    if workdir.guard_browser(): ...                           # True = no browser here: one line was printed, skip the screen checks

Where the folder goes (first place that really accepts a file):
    1. $TEACHER_STUDIO_TMP           (set it to move every intermediate file somewhere else)
    2. <folder of the output>/.teacher-studio-work
    3. <current folder>/.teacher-studio-work
    4. the system temp folder        (plain mkdir, never mkdtemp)
    5. ~/.teacher-studio/tmp
The system temp folder is never required.
"""
from __future__ import annotations

import contextlib
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

ENV_DIR = "TEACHER_STUDIO_TMP"
ENV_NO_BROWSER = "TEACHER_STUDIO_NO_BROWSER"  # "1" = never try a browser, "0" = always try
WORK_NAME = ".teacher-studio-work"
NO_BROWSER = "NO-BROWSER"
NO_BROWSER_LINE = (NO_BROWSER + " 이 실행 환경에서는 화면(브라우저)을 띄울 수 없어요: {why}. 화면으로 보는 점검만 건너뛰고 나머지 점검은 그대로 했어요. "
                   "브라우저·Playwright를 직접 실행하거나 설치하려고 다시 시도하지 마세요(같은 이유로 막혀요). "
                   "마지막 안내에 「화면은 직접 열어 확인하지 못했어요」 한 줄만 적고 넘어가세요.")
_said = False


def _usable(folder: Path) -> bool:
    """True when a file can really be written in this folder (created without a private mode if missing)."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / f".probe-{uuid.uuid4().hex[:8]}"
        probe.write_bytes(b"ok")
        probe.unlink()
        return True
    except OSError:
        return False


def _near_dir(near) -> Path | None:
    if not near:
        return None
    p = Path(near)
    try:
        p = p.resolve()
    except OSError:
        pass
    return p if p.is_dir() else p.parent


def _candidates(near=None, temp_first: bool = False) -> list[Path]:
    out: list[Path] = []
    env = os.environ.get(ENV_DIR, "").strip()
    if env:
        out.append(Path(env))
    local: list[Path] = []
    nd = _near_dir(near)
    if nd is not None:
        local.append(nd / WORK_NAME)
    try:
        local.append(Path.cwd() / WORK_NAME)
    except OSError:
        pass
    try:
        system = [Path(tempfile.gettempdir()) / "teacher-studio"]
    except OSError:  # no usable temp folder at all
        system = []
    out += (system + local) if temp_first else (local + system)
    out.append(Path.home() / ".teacher-studio" / "tmp")
    seen, uniq = set(), []
    for c in out:
        k = os.path.normcase(str(c))
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    return uniq


def base(near=None, temp_first: bool = False) -> Path:
    """The first folder that accepts a file. Raises OSError with a plain line only when none of the five places works."""
    tried = []
    for c in _candidates(near, temp_first):
        if _usable(c):
            return c
        tried.append(str(c))
    raise OSError("쓸 수 있는 작업 폴더가 없어요. 환경 변수 " + ENV_DIR + "에 쓸 수 있는 폴더를 적어 주세요. (시도한 곳: " + ", ".join(tried) + ")")


def make(prefix: str = "work", near=None) -> Path:
    """A fresh, empty, ordinary folder (never an owner-only one). Remove it with cleanup()."""
    root = base(near)
    for _ in range(20):
        d = root / f"{prefix}-{uuid.uuid4().hex[:8]}"
        try:
            d.mkdir()  # default mode: inherits the parent's permissions
            return d
        except FileExistsError:
            continue
    raise OSError(f"작업 폴더를 만들지 못했어요: {root}")


def cleanup(folder) -> None:
    """Remove a folder from make(), and the .teacher-studio-work folder around it once that is empty."""
    folder = Path(folder)
    shutil.rmtree(folder, ignore_errors=True)
    parent = folder.parent
    if parent.name in (WORK_NAME, "teacher-studio", "tmp"):
        try:
            parent.rmdir()  # only succeeds when empty
        except OSError:
            pass


@contextlib.contextmanager
def temp_dir(prefix: str = "work", near=None):
    """`with temp_dir("deck", near=out) as td:` - replaces tempfile.TemporaryDirectory()."""
    d = make(prefix, near)
    try:
        yield str(d)
    finally:
        cleanup(d)


def named(name: str, near=None) -> Path:
    """A stable scratch path for a by-product the user may open (a preview page, a lock). System temp first, so the user's
    folder stays clean; the work folder when temp is not writable."""
    return base(near, temp_first=True) / name


# ---------------------------------------------------------------------------------------------------------------- browser probe
def browser_blocked() -> str:
    """'' when a headless browser may be able to start, else a short plain reason. Takes a few milliseconds.

    Windows: asks for the same pipe pair that Playwright's driver and Chrome's own processes need. A security box that refuses
    it (Codex on Windows does) refuses the browser too, so there is no point in waiting for each launch to fail."""
    flag = os.environ.get(ENV_NO_BROWSER, "").strip()
    if flag == "1":
        return os.environ.get(ENV_NO_BROWSER + "_WHY") or f"{ENV_NO_BROWSER}=1 로 꺼 둠"
    if flag == "0":
        return ""
    if os.name == "nt":
        try:
            import _winapi
            from asyncio import windows_utils
            h1, h2 = windows_utils.pipe(overlapped=(True, True))
            _winapi.CloseHandle(h1)
            _winapi.CloseHandle(h2)
        except PermissionError:
            return "보안 상자가 프로그램 사이의 통로를 막고 있어요"
        except Exception:  # noqa: BLE001 - an unknown failure of the probe is not proof: let the real launch decide
            return ""
    return ""


class _NoBrowser:
    """Stands in for playwright.sync_api when the browser cannot start: every call site already handles a launch error."""

    expect = None  # `from playwright.sync_api import expect, sync_playwright` must still import

    def __init__(self, why: str):
        self.why = why

    def sync_playwright(self):
        raise RuntimeError(f"{NO_BROWSER}: {self.why} (다시 시도해도 같아요)")

    def __getattr__(self, name):  # AttributeError keeps the import machinery (hasattr checks) working
        raise AttributeError(name)


def say_no_browser(why: str) -> None:
    """Print the one line (once per process, and once per chain of child scripts)."""
    global _said
    if _said or os.environ.get("TEACHER_STUDIO_NO_BROWSER_SAID") == "1":
        return
    _said = True
    os.environ["TEACHER_STUDIO_NO_BROWSER_SAID"] = "1"
    print(NO_BROWSER_LINE.format(why=why), flush=True)


def guard_browser(quiet: bool = False) -> bool:
    """Call once at the top of a script that may open a browser. True = no browser here.
    Then: the one NO-BROWSER line is printed, child scripts skip their own tries, and `from playwright.sync_api import
    sync_playwright` gives a stand-in that fails at once, so the script's usual "could not look" path runs without a wait."""
    why = browser_blocked()
    if not why:
        return False
    os.environ[ENV_NO_BROWSER] = "1"
    os.environ.setdefault(ENV_NO_BROWSER + "_WHY", why)  # child scripts repeat the same plain reason
    if "playwright.sync_api" not in sys.modules or not isinstance(sys.modules["playwright.sync_api"], _NoBrowser):
        sys.modules["playwright.sync_api"] = _NoBrowser(why)  # type: ignore[assignment]
    if not quiet:
        say_no_browser(why)
    return True


def is_no_browser(exc) -> bool:
    return NO_BROWSER in str(exc)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    print("work folder:", base())
    why_ = browser_blocked()
    print("browser:", ("blocked - " + why_) if why_ else "may start")
