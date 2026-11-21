#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""video_eyes: let the AI SEE a local video as a contact sheet + frames (+ optional subtitles). Local only.

Pattern credit: the "watch a video as scene frames + transcript" idea comes from claude-video (/watch)
by bradautomates (MIT). This is an independent, safer re-implementation: LOCAL FILES ONLY, no URL
download (no yt-dlp), no network, no cloud video/audio API. Nothing leaves the computer.

Usage:
    python3 video_eyes.py clip.mp4 [--out DIR] [--max 24] [--width 512|1024] [--start S] [--end S]
                                   [--scene 0.3] [--subs] [--yes]
Outputs in DIR (default: <video name>_eyes next to the video):
    sheet.png     contact sheet, every frame with its timestamp  (look at THIS first)
    frames/*.jpg  the frames (scene changes first, evenly spaced fill-in, near-duplicates removed)
    frames.json   {video, duration, frames:[{i, t, file, reason}], sheet, subs?}
Uses: generated-video QA (motion/slides MP4) and analysing a teacher's own reference/event video.
--max is capped at 60. --width 512 (default) or 1024 (detail). --start/--end trim in seconds.
--subs  transcribes the audio on this computer (faster-whisper, CPU only). Needs a one-time small
        install + model download; it asks first (plain Korean) and installs only with --yes.
Needs ffmpeg (ensure_ffmpeg: system, else imageio-ffmpeg ~40MB with consent) and Pillow (consent).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ensure  # noqa: E402

VIDEO_EXT = {".mp4", ".webm", ".mov", ".m4v", ".mkv", ".avi", ".gif"}
MAX_CAP = 60
DEDUPE_DIFF = 3.0   # mean abs difference (0-255) of 24x24 grayscale thumbs below which two frames are "the same"
SUBS_PROMPT = ("영상 속 말을 글자로 바꾸려면 작은 도구(faster-whisper, 약 150MB)를 한 번 설치하고 음성 모델(약 140MB)을 "
               "내려받아야 해요. 변환은 선생님 컴퓨터 안에서만 하고 영상은 어디로도 보내지 않아요. 설치할까요?")


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe(ff: str, path: Path) -> dict:
    """Duration (s), has_audio, from `ffmpeg -i` (no ffprobe needed)."""
    r = _run([ff, "-hide_banner", "-i", str(path)])
    txt = r.stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", txt)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    return {"duration": dur, "audio": bool(re.search(r"Stream #.*Audio:", txt))}


def scene_times(ff: str, path: Path, start: float, end: float, thr: float, width: int) -> list[float]:
    """Timestamps (absolute seconds) where the picture changes a lot."""
    cmd = [ff, "-hide_banner", "-nostats", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(path), "-an",
           "-vf", f"scale={width}:-2,select='gt(scene,{thr})',showinfo", "-f", "null", "-"]
    r = _run(cmd)
    out = []
    for m in re.finditer(r"pts_time:(\d+(?:\.\d+)?)", r.stderr):
        out.append(start + float(m.group(1)))
    return out


def plan(scene: list[float], start: float, end: float, n: int) -> list[tuple[float, str]]:
    """Candidate timestamps: first frame + scene changes + evenly spaced fill, thinned to about 1.5*n."""
    span = max(end - start, 0.1)
    cands: list[tuple[float, str]] = [(start + min(0.05, span / 2), "scene")]
    cands += [(t, "scene") for t in scene]
    cands += [(start + span * (k + 0.5) / n, "uniform") for k in range(n)]
    cands.sort()
    gap = span / (n * 2.5)
    kept: list[tuple[float, str]] = []
    for t, why in cands:
        if kept and t - kept[-1][0] < gap:
            if why == "scene" and kept[-1][1] == "uniform":
                kept[-1] = (t, why)
            continue
        kept.append((t, why))
    return kept


def grab(ff: str, path: Path, t: float, width: int, dest: Path) -> bool:
    r = _run([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
              "-vf", f"scale={width}:-2", "-q:v", "3", str(dest)])
    return r.returncode == 0 and dest.exists() and dest.stat().st_size > 0


def thumb(img) -> list[int]:
    return list(img.convert("L").resize((24, 24)).getdata())


def tdiff(a: list[int], b: list[int]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def fmt_t(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}"


def contact_sheet(frames: list[dict], fdir: Path, out: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    n = len(frames)
    cols = 3 if n <= 6 else 4 if n <= 12 else 6
    tw = 400 if cols <= 4 else 320
    imgs = [Image.open(fdir.parent / f["file"]).convert("RGB") for f in frames]
    th = max(1, round(tw * imgs[0].height / imgs[0].width))
    rows = (n + cols - 1) // cols
    pad, lab = 8, 26
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=18)
    except TypeError:  # old Pillow
        font = ImageFont.load_default()
    for k, (f, im) in enumerate(zip(frames, imgs)):
        x, y = pad + (k % cols) * (tw + pad), pad + (k // cols) * (th + lab + pad)
        sheet.paste(im.resize((tw, th)), (x, y + lab))
        d.text((x + 2, y + 2), f"#{f['i']}  {fmt_t(f['t'])}" + ("  scene" if f["reason"] == "scene" else ""), fill=(255, 224, 120), font=font)
    sheet.save(out)


def transcribe(path: Path, ff: str, start: float, end: float, consent: bool) -> dict:
    """Optional local speech-to-text (faster-whisper, CPU). Returns {ok, segments, prompt}."""
    if not ensure._importable("faster_whisper"):
        if not consent:
            msg = SUBS_PROMPT + ("" if ensure.network_ok() else " 지금은 " + ensure.CODEX_NETWORK_HELP)
            return {"ok": False, "segments": [], "prompt": msg}
        ok, err = ensure._pip_install(["faster-whisper"])
        if not ok or not ensure._importable("faster_whisper"):
            return {"ok": False, "segments": [], "prompt": f"자막 도구 설치가 안 됐어요: {err}"}
    from faster_whisper import WhisperModel
    import workdir
    with workdir.temp_dir("subs", near=path) as td:
        wav = Path(td) / "a.wav"
        r = _run([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(path),
                  "-vn", "-ac", "1", "-ar", "16000", str(wav)])
        if r.returncode != 0:
            return {"ok": False, "segments": [], "prompt": "소리를 꺼내지 못했어요."}
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segs, _info = model.transcribe(str(wav), vad_filter=True)
        return {"ok": True, "prompt": "", "segments": [{"start": round(start + s.start, 2), "end": round(start + s.end, 2), "text": s.text.strip()} for s in segs]}


def run(video: str, out: str | None = None, n: int = 24, width: int = 512, start: float = 0.0, end: float | None = None,
        scene: float = 0.3, subs: bool = False, yes: bool = False) -> dict:
    """Programmatic entry. Returns {ok, out, sheet, frames_json, frames, prompt}."""
    if re.match(r"^[a-z][a-z0-9+.-]*://", video, re.I):
        return {"ok": False, "prompt": "인터넷 주소는 받지 않아요. 영상을 컴퓨터에 저장한 뒤 그 파일을 알려 주세요. (영상이 밖으로 나가지 않게 하려는 규칙이에요)"}
    path = Path(video)
    if not path.is_file() or path.suffix.lower() not in VIDEO_EXT:
        return {"ok": False, "prompt": f"영상 파일을 찾지 못했어요: {video} (mp4, webm, mov 등 컴퓨터에 있는 파일만 돼요)"}
    n = max(1, min(int(n), MAX_CAP))
    width = 1024 if int(width) >= 1024 else 512
    ff = ensure.ensure_ffmpeg(consent=yes)
    if not ff["ok"]:
        return {"ok": False, "prompt": ff["prompt"]}
    pil = ensure.ensure("pillow", consent=yes)
    if not pil["ok"]:
        return {"ok": False, "prompt": pil["prompt"]}
    from PIL import Image
    info = probe(ff["path"], path)
    dur = info["duration"]
    if dur <= 0:
        return {"ok": False, "prompt": "영상 길이를 읽지 못했어요. 파일이 깨졌을 수 있어요."}
    s = max(0.0, float(start))
    e = min(dur, float(end)) if end else dur
    if e - s < 0.1:
        return {"ok": False, "prompt": "--start/--end 범위가 너무 짧거나 영상 밖이에요."}
    odir = Path(out) if out else path.with_name(path.stem + "_eyes")
    fdir = odir / "frames"
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob("*.jpg"):
        old.unlink()
    cands = plan(scene_times(ff["path"], path, s, e, scene, width), s, e, n)
    kept: list[dict] = []
    prev = None
    for t, why in cands:
        tmp = fdir / "_tmp.jpg"
        if not grab(ff["path"], path, t, width, tmp):
            continue
        with Image.open(tmp) as im:
            th = thumb(im)
        if prev is not None and tdiff(prev, th) < DEDUPE_DIFF:
            continue
        prev = th
        kept.append({"t": round(t, 2), "reason": why, "_tmp": tmp.read_bytes()})
    tmp = fdir / "_tmp.jpg"
    if tmp.exists():
        tmp.unlink()
    if len(kept) > n:  # thin evenly, scene frames win ties
        scenes = [k for k in kept if k["reason"] == "scene"]
        pick = {id(k) for k in scenes}
        rest = [k for k in kept if id(k) not in pick]
        need = n - len(pick)
        if need > 0 and rest:
            step = len(rest) / need
            pick |= {id(rest[int(i * step)]) for i in range(need)}
        kept = [k for k in kept if id(k) in pick]
        if len(kept) > n:
            step = len(kept) / n
            kept = [kept[int(i * step)] for i in range(n)]
    frames = []
    for i, k in enumerate(kept, 1):
        name = f"frames/f{i:02d}_{k['t']:07.2f}s.jpg"
        (odir / name).write_bytes(k["_tmp"])
        frames.append({"i": i, "t": k["t"], "file": name, "reason": k["reason"]})
    if not frames:
        return {"ok": False, "prompt": "장면을 하나도 뽑지 못했어요. 영상 형식을 확인해 주세요."}
    sheet = odir / "sheet.png"
    contact_sheet(frames, fdir, sheet)
    doc = {"video": path.name, "duration": round(dur, 2), "range": [round(s, 2), round(e, 2)], "width": width,
           "max": n, "has_audio": info["audio"], "frames": frames, "sheet": "sheet.png", "local_only": True}
    prompt = ""
    if subs:
        if not info["audio"]:
            prompt = "이 영상에는 소리가 없어서 자막을 만들 수 없어요."
        else:
            tr = transcribe(path, ff["path"], s, e, yes)
            if tr["ok"]:
                doc["subs"] = tr["segments"]
            else:
                prompt = tr["prompt"]
    (odir / "frames.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "out": str(odir), "sheet": str(sheet), "frames_json": str(odir / "frames.json"), "frames": len(frames),
            "subs_ok": "subs" in doc, "prompt": prompt, "ffmpeg": ff["source"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", help="local video file (no URLs)")
    ap.add_argument("--out")
    ap.add_argument("--max", type=int, default=24, help=f"max frames (default 24, cap {MAX_CAP})")
    ap.add_argument("--width", type=int, default=512, choices=(512, 1024))
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--scene", type=float, default=0.3, help="scene-change sensitivity 0-1 (lower = more frames)")
    ap.add_argument("--subs", action="store_true", help="local speech-to-text (asks before installing)")
    ap.add_argument("--yes", action="store_true", help="the teacher agreed to the small installs (ffmpeg / Pillow / faster-whisper)")
    a = ap.parse_args()
    res = run(a.video, a.out, a.max, a.width, a.start, a.end, a.scene, a.subs, a.yes)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
