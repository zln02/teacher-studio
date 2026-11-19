#!/bin/bash
S=/c/Users/User/AppData/Local/Temp/claude/d85f5c5f00edac37/c8098317-2fbb-4131-bf8f-07218752ac6e/scratchpad
export PYTHONUTF8=1
c=$1
case $c in
 game) P="중2 과학 빛 단원 복습 게임 만들어 줘 알아서 끝까지 만들어 줘. 결과 파일은 지금 폴더에 저장해 줘.";;
 parents) P="학부모 총회 발표자료 PPT로 만들어 줘 (8장 정도) 알아서 끝까지 만들어 줘. 결과 파일은 지금 폴더에 저장해 줘.";;
 data) P="우리 반 성적 엑셀 분석해 줘 알아서 끝까지 만들어 줘. 결과 파일은 지금 폴더에 저장해 줘.";;
 law) P="가정통신문에 인터넷에서 찾은 캐릭터 그림 써도 돼?";;
esac
D=$S/runs2/$c; rm -rf $D; mkdir -p $D; cd $D
[ $c = data ] && cp $S/성적.csv .
st=$(date +%s)
CLAUDE_CONFIG_DIR=$S/cfg-v2 timeout 1500 claude -p --model sonnet --permission-mode bypassPermissions --output-format json "$P" > _result.json 2> _err.txt
echo $(( $(date +%s)-st )) > _secs.txt
