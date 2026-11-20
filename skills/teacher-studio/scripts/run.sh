#!/bin/sh
# Run a Teacher Studio script with whatever Python exists: the path doctor.py recorded, else python3 / python / py.
# Usage: sh scripts/run.sh studio.py doctor   (script names are relative to this folder)
here=$(cd "$(dirname "$0")" && pwd)
env_json="${TEACHER_STUDIO_HOME:-$HOME/.teacher-studio}/env.json"
py=""
if [ -f "$env_json" ]; then
  py=$(sed -n 's/.*"python_path"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p' "$env_json" | head -n 1 | sed 's/\\/\/g')
  [ -n "$py" ] && [ -x "$py" ] || py=""
fi
if [ -z "$py" ]; then
  for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then py="$c"; break; fi
  done
fi
[ -n "$py" ] || { echo "Python을 찾지 못했어요. python3, python, py 중 하나가 필요해요." >&2; exit 127; }
script="$1"; shift
case "$script" in /*|?:*) ;; *) script="$here/$script" ;; esac
PYTHONUTF8=1 exec "$py" "$script" "$@"
