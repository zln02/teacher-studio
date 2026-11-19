#!/bin/bash
# law question re-run WITHOUT the "알아서 끝까지 만들어 줘" suffix (a question, not a build request)
S=/c/Users/User/AppData/Local/Temp/claude/d85f5c5f00edac37/c8098317-2fbb-4131-bf8f-07218752ac6e/scratchpad
export PYTHONUTF8=1
cond=$1
P="가정통신문에 인터넷에서 찾은 캐릭터 그림 써도 돼?"
D=$S/runs/law-plain/$cond; mkdir -p $D; cd $D
cfg=$S/cfg-$cond
st=$(date +%s)
CLAUDE_CONFIG_DIR=$cfg timeout 900 claude -p --model sonnet --permission-mode bypassPermissions --output-format json "$P" > _result.json 2> _err.txt
echo $(( $(date +%s)-st )) > _secs.txt
