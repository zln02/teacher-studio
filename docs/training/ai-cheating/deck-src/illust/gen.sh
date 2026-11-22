#!/bin/sh
# usage: gen.sh name  (runs codex image gen for one illustration)
cd "$(dirname "$0")/.."
n=$1
base=$(grep '^BASE:' illust/prompts.txt | sed 's/^BASE: //' | sed "s/{name}/$n/")
scene=$(grep "^$n:" illust/prompts.txt | sed "s/^$n: //")
REF=../../deck-v3-src/illust-e/spot-wall.jpg
codex exec --skip-git-repo-check -s workspace-write -i "$REF" -- "$base $scene" > illust/$n.log 2>&1
ls -la illust/$n.* 
