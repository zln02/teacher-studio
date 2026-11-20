#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 박진영 (zln02)
"""Sound ears: listen to an audio file in plain Korean, and make a sound effect. Optional weapon (earshot), safe without it.

    py sound_ears.py listen clip.wav [--kids] [--json]
    py sound_ears.py sfx "물방울 똑 떨어지는 소리" --out drop.wav --seconds 1
    py sound_ears.py doctor                      # is earshot installed? how to install / remove

* `listen` ALWAYS works for .wav (standard library only: peak, loudness, clipping, length, silence). If earshot is installed
  it adds true LUFS/peak and what the sound resembles (AI tags). Without it, it says so and offers the install.
* `sfx` renders from earshot's bank of 252 code-made effects (NOT free text-to-audio: the description picks the closest
  bank sound by words). If earshot is missing or nothing fits, it falls back to the ZzFX presets used by games
  (shared/assets/sfx/presets.json) and says which.
* Nothing is installed here. Install only with consent: `py ensure.py earshot --yes` (size is stated in the prompt).
  Uninstall: `py ensure.py earshot --uninstall`.
Classroom-safe limits: peak <= -1 dBFS, no clipping, program loudness about -23..-14 LUFS (quiet room friendly), a single effect <= 3 s.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import subprocess
import sys
import wave
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import ensure as _ensure
except ImportError:  # pragma: no cover
    _ensure = None

# classroom limits (kids' ears, small rooms, phones/TV speakers)
PEAK_MAX_DB = -1.0       # louder than this: risk of clipping on playback
PEAK_LOUD_DB = -3.0      # sharp, harsh peaks start here for short effects
RMS_QUIET_DB = -40.0     # quieter than this: students at the back won't hear
RMS_LOUD_DB = -12.0      # louder than this: tiring for kids
SFX_MAX_S = 3.0
CLIP_LEVEL = 0.999

# Korean/English words -> earshot bank category (checked against `earshot sfx list`; unknown ones are skipped at run time)
SFX_WORDS = [
    (("물방울", "똑", "drop", "drip", "bubble", "방울"), "drip"),
    (("휘익", "쉭", "whoosh", "swish", "바람", "넘어가", "슬라이드"), "whoosh_fast"),
    (("쿵", "충격", "impact", "hit", "punch", "타격", "꽝"), "pro_impact"),
    (("키보드", "타자", "key", "typing", "딸깍"), "typing_key"),
    (("딩", "알림", "ding", "notify", "bell", "종", "정답", "띵"), "notify"),
    (("팝", "pop", "톡", "뿅"), "pro_pop"),
    (("반짝", "shimmer", "sparkle", "별", "마법"), "shimmer"),
    (("글리치", "glitch", "오류"), "glitch"),
    (("상승", "riser", "긴장", "카운트", "두근"), "riser"),
]
# fallback ZzFX preset names (see shared/assets/sfx/presets.json)
ZZFX_WORDS = [(("정답", "딩", "correct", "right", "성공"), "correct"), (("오답", "틀", "wrong", "buzz"), "wrong"),
              (("쿵", "hit", "impact"), "hit"), (("휘익", "whoosh"), "whoosh"), (("팝", "pop", "톡"), "pop")]


def earshot_path() -> str:
    return _ensure.earshot_exe() if _ensure else ""


def _env() -> dict:
    env = dict(os.environ, PYTHONUTF8="1")
    if _ensure:
        env["EARSHOT_HOME"] = str(_ensure.EARSHOT_DIR / "cache")
    return env


def install_hint() -> str:
    gb = _ensure.EARSHOT_GB if _ensure else "약 1.1GB 이상"
    return ("더 정확히 들으려면 소리 도우미(earshot, 무료)를 설치하면 돼요. 내려받는 양: " + gb + ". 이 컴퓨터의 전용 폴더에만 설치되고 "
            "`py ensure.py earshot --uninstall` 로 지울 수 있어요. 원하시면 「설치해 줘」라고 말씀해 주세요.")


def _db(x: float) -> float:
    return 20.0 * math.log10(x) if x > 1e-9 else -120.0


def wav_stats(path: str) -> dict:
    """Peak, RMS, clipping, length, edge silence from a PCM .wav (standard library only)."""
    with wave.open(str(path), "rb") as w:
        ch, width, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width == 2:
        vals = struct.unpack("<%dh" % (len(raw) // 2), raw)
        scale = 32768.0
    elif width == 1:
        vals = [b - 128 for b in raw]
        scale = 128.0
    elif width in (3, 4):
        if width == 3:
            vals = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw) - 2, 3)]
            scale = 8388608.0
        else:
            vals = struct.unpack("<%di" % (len(raw) // 4), raw)
            scale = 2147483648.0
    else:
        raise ValueError("지원하지 않는 wav 형식이에요")
    if ch > 1:
        vals = [sum(vals[i:i + ch]) / ch for i in range(0, len(vals) - ch + 1, ch)]
    if not vals:
        return {"seconds": 0.0, "sr": sr, "peak_db": -120.0, "rms_db": -120.0, "clipped": 0, "lead_silence_s": 0.0, "tail_silence_s": 0.0,
                "max_window_rms_db": -120.0, "min_window_rms_db": -120.0}
    a = [abs(v) / scale for v in vals]
    peak = max(a)
    rms = math.sqrt(sum(v * v for v in a) / len(a))
    clipped = sum(1 for v in a if v >= CLIP_LEVEL)
    thr = max(peak * 0.01, 1e-4)
    first = next((i for i, v in enumerate(a) if v > thr), len(a))
    last = next((i for i, v in enumerate(reversed(a)) if v > thr), len(a))
    win = max(1, int(sr * 0.05))
    wr = [math.sqrt(sum(v * v for v in a[i:i + win]) / len(a[i:i + win])) for i in range(0, len(a), win)]
    loud = [x for x in wr if x > thr]
    return {"seconds": round(len(a) / sr, 3), "sr": sr, "peak_db": round(_db(peak), 1), "rms_db": round(_db(rms), 1),
            "clipped": clipped, "lead_silence_s": round(first / sr, 3), "tail_silence_s": round(last / sr, 3),
            "max_window_rms_db": round(_db(max(wr)), 1), "min_window_rms_db": round(_db(min(loud)) if loud else -120.0, 1)}


def verdict(st: dict, kids: bool = True, lufs: float | None = None) -> list[str]:
    """Plain-Korean findings (list of lines). Empty list never happens: ends with a one-line overall answer."""
    out: list[str] = []
    ok = True
    if st["clipped"] > 0:
        out.append("소리가 찌그러져요(깨짐 %d곳). 볼륨을 낮춰 다시 만들어야 해요." % st["clipped"])
        ok = False
    if st["peak_db"] > PEAK_MAX_DB:
        out.append("가장 큰 소리가 너무 커요(%.1f dB). -1 dB 아래로 낮춰야 스피커에서 깨지지 않아요." % st["peak_db"])
        ok = False
    elif st["peak_db"] > PEAK_LOUD_DB and st["seconds"] < 2:
        out.append("짧은 효과음인데 꼭대기 소리가 날카로울 수 있어요(%.1f dB). 아이들 귀에는 조금 낮추는 게 좋아요." % st["peak_db"])
    loud_db = lufs if lufs is not None else st["rms_db"]
    unit = "LUFS" if lufs is not None else "dB(평균)"
    if loud_db > RMS_LOUD_DB + (0 if lufs is None else -2):
        out.append("전체적으로 시끄러워요(%.1f %s). 교실에서 오래 들으면 피곤해요." % (loud_db, unit))
        ok = False
    elif loud_db < RMS_QUIET_DB + (0 if lufs is None else -3):
        out.append("너무 조용해요(%.1f %s). 뒷자리 학생은 못 들을 수 있어요." % (loud_db, unit))
        ok = False
    if st["max_window_rms_db"] - st["min_window_rms_db"] > 40 and st["seconds"] > 4:
        out.append("소리 크기가 들쭉날쭉해요(가장 큰 곳과 작은 곳이 %d dB 차이)." % (st["max_window_rms_db"] - st["min_window_rms_db"]))
    if st["seconds"] > SFX_MAX_S and kids and st["seconds"] < 20:
        out.append("효과음치고 길어요(%.1f초). 3초 안쪽이 좋아요. (배경음악이면 괜찮아요)" % st["seconds"])
    if st["lead_silence_s"] > 0.3:
        out.append("앞에 %.1f초 빈 소리가 있어서 반응이 느리게 느껴져요." % st["lead_silence_s"])
    if st["tail_silence_s"] > 1.0:
        out.append("뒤에 %.1f초 빈 소리가 있어요. 잘라내면 깔끔해요." % st["tail_silence_s"])
    out.append("교실에서 써도 괜찮아요." if ok else "고친 뒤에 다시 확인하세요.")
    return out


def _run_earshot(args: list[str], timeout: int = 300) -> tuple[bool, str]:
    exe = earshot_path()
    if not exe:
        return False, "earshot 없음"
    try:
        r = subprocess.run([exe] + args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=_env(), timeout=timeout)
    except PermissionError as e:
        return False, "이 컴퓨터의 보안 설정이 소리 도우미 실행을 막았어요(%s)" % e
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    return r.returncode == 0, (r.stdout if r.returncode == 0 else (r.stderr or r.stdout))


def _find_key(d, names):
    """Depth-first search for the first numeric value under any of the key names."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k.lower() in names and isinstance(v, (int, float)) and not isinstance(v, bool):
                return float(v)
        for v in d.values():
            r = _find_key(v, names)
            if r is not None:
                return r
    elif isinstance(d, list):
        for v in d:
            r = _find_key(v, names)
            if r is not None:
                return r
    return None


def _tags(d) -> list[str]:
    """Top tag names from earshot `describe --json` (shape tolerant)."""
    names: list[str] = []
    if isinstance(d, dict):
        for key in ("tags", "labels", "audioset"):
            v = d.get(key)
            if isinstance(v, list):
                for t in v[:5]:
                    n = t.get("tag") or t.get("label") or t.get("name") if isinstance(t, dict) else str(t)
                    if n:
                        names.append(str(n))
                if names:
                    return names
        for v in d.values():
            if isinstance(v, (dict, list)):
                names = _tags(v)
                if names:
                    return names
    elif isinstance(d, list):
        for v in d:
            names = _tags(v)
            if names:
                return names
    return names


def listen(path: str, kids: bool = True, use_earshot: bool = True) -> dict:
    """Evaluate an audio file. Returns {"ok", "mode": "basic"|"earshot", "stats", "lines", "install_hint"?}."""
    p = Path(path)
    if not p.exists():
        return {"ok": False, "mode": "none", "lines": ["파일을 찾을 수 없어요: %s" % path], "stats": {}}
    res: dict = {"ok": True, "mode": "basic", "stats": {}, "tags": [], "lufs": None}
    is_wav = p.suffix.lower() == ".wav"
    if is_wav:
        try:
            res["stats"] = wav_stats(str(p))
        except (wave.Error, ValueError, EOFError) as e:
            res["note"] = "wav를 읽지 못했어요: %s" % e
    exe = earshot_path() if use_earshot else ""
    if exe:
        ok, txt = _run_earshot(["measure", str(p), "--json"])
        if ok:
            try:
                m = json.loads(txt)
                res["lufs"] = _find_key(m, {"lufs", "integrated_lufs", "loudness_lufs", "lufs_i"})
                tp = _find_key(m, {"true_peak_db", "true_peak", "true_peak_dbtp", "tp_db"})
                if tp is not None and not res["stats"]:
                    res["stats"] = {"seconds": _find_key(m, {"duration", "duration_s", "dur_s", "seconds"}) or 0.0, "peak_db": tp, "rms_db": res["lufs"] or -120.0,
                                    "clipped": 0, "lead_silence_s": 0.0, "tail_silence_s": 0.0, "max_window_rms_db": 0.0, "min_window_rms_db": 0.0}
                res["mode"] = "earshot"
            except ValueError:
                pass
        ok, txt = _run_earshot(["describe", str(p), "--json"])
        if ok:
            try:
                res["tags"] = _tags(json.loads(txt))
                res["mode"] = "earshot"
            except ValueError:
                pass
    if not res["stats"]:
        res["ok"] = False
        res["lines"] = [res.get("note") or "이 파일 형식은 기본 점검으로는 읽을 수 없어요(.wav만 가능)."] + ([] if exe else [install_hint()])
        return res
    lines = verdict(res["stats"], kids, res["lufs"])
    if res["tags"]:
        lines.insert(0, "AI가 들은 느낌: " + ", ".join(res["tags"][:4]))
    if not exe:
        lines.append("(기본 점검만 했어요: 최대·평균 크기, 깨짐, 길이.) " + install_hint())
        res["install_hint"] = install_hint()
    res["lines"] = lines
    return res


def pick_bank(description: str) -> str:
    d = description.lower()
    for words, cat in SFX_WORDS:
        if any(w in d for w in words):
            return cat
    return ""


def pick_zzfx(description: str) -> str:
    d = description.lower()
    for words, name in ZZFX_WORDS:
        if any(w in d for w in words):
            return name
    return "pop"


def sfx(description: str, out: str, seconds: float = 1.0, use_earshot: bool = True) -> dict:
    """Make an effect file. Returns {"ok", "source": "earshot"|"zzfx", "path"?, "sound"?, "lines"}."""
    seconds = max(0.2, min(float(seconds), SFX_MAX_S))
    exe = earshot_path() if use_earshot else ""
    if not exe:
        return _zzfx_fallback(description, seconds, "소리 도우미(earshot)가 설치돼 있지 않아요. " + install_hint())
    cat = pick_bank(description)
    ok, txt = _run_earshot(["sfx", "list", "--category", cat] if cat else ["sfx", "list"], timeout=120)
    ids = [t for t in txt.replace(",", " ").split() if "/" in t and not t.startswith("-")] if ok else []
    if cat:
        ids = [i for i in ids if i.startswith(cat + "/")] or ids
    if not ids:
        return _zzfx_fallback(description, seconds, "설명에 맞는 효과음을 효과음 창고에서 못 찾았어요.")
    sound = ids[0]
    ok, txt = _run_earshot(["sfx", "render", sound, "-o", str(out), "--dur", str(seconds), "--peak", str(PEAK_MAX_DB)])
    if not ok or not Path(out).exists():
        return _zzfx_fallback(description, seconds, "효과음 만들기에 실패했어요: " + (txt or "").strip()[-120:])
    chk = listen(out, True, use_earshot=False)
    return {"ok": True, "source": "earshot", "sound": sound, "path": str(out), "lines": [
        "효과음 창고의 「%s」로 %.1f초짜리를 만들었어요: %s" % (sound, seconds, out),
        "※ 글로 설명한 소리를 새로 만드는 게 아니라, 창고 소리 중 가장 비슷한 것을 골라요."] + chk["lines"][-1:]}


def _zzfx_fallback(description: str, seconds: float, why: str) -> dict:
    name = pick_zzfx(description)
    return {"ok": True, "source": "zzfx", "sound": name, "path": "", "lines": [
        why, "대신 게임에 이미 들어 있는 기본 효과음 「%s」(ZzFX, 설치 없이 바로 나와요)를 쓸게요. 파일이 필요하면 소리 도우미를 설치해 주세요." % name]}


def doctor() -> dict:
    exe = earshot_path()
    return {"installed": bool(exe), "path": exe, "install": "py ensure.py earshot --yes", "uninstall": "py ensure.py earshot --uninstall",
            "hint": "" if exe else install_hint()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("listen")
    pl.add_argument("audio")
    pl.add_argument("--json", action="store_true")
    pl.add_argument("--no-earshot", action="store_true", help="basic check only")
    ps = sub.add_parser("sfx")
    ps.add_argument("description")
    ps.add_argument("--out", default="sfx.wav")
    ps.add_argument("--seconds", type=float, default=1.0)
    ps.add_argument("--json", action="store_true")
    sub.add_parser("doctor")
    a = ap.parse_args()
    if a.cmd == "listen":
        r = listen(a.audio, use_earshot=not a.no_earshot)
    elif a.cmd == "sfx":
        r = sfx(a.description, a.out, a.seconds)
    else:
        r = doctor()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    if getattr(a, "json", False):
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("\n".join(r.get("lines", [])))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
