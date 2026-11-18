# INSTALL — AI가 읽고 따라 하는 설치 순서

> 이 문서는 **Claude Code·Codex·Claude 앱(코드 실행)** 이 읽고 그대로 실행하는 설치 지시서입니다.
> 상대는 코딩을 모르는 선생님입니다. 진행 중에는 **선생님 말로 한 줄씩만** 알리고, 명령어·경로·영어 오류 문장을 길게 보여 주지 마세요.

## 0. 내가 어디서 실행 중인지 정하기
스스로 판단해 `AGENT` 값을 정한다.
- Claude Code → `claude-code` · Codex(앱·CLI·IDE) → `codex` · Claude 앱·웹의 코드 실행 → `claude-app`

선생님께: 「교사 스튜디오를 설치할게요. 1~2분 걸려요.」

## 1. 내려받기
```bash
git clone --depth 1 https://github.com/zln02/teacher-studio.git ~/teacher-studio \
  || (cd ~/teacher-studio && git pull --ff-only)
```
- `git`이 없으면: `https://codeload.github.com/zln02/teacher-studio/zip/refs/heads/main` 를 받아 `~/teacher-studio`에 풀기 (Python `urllib` + `zipfile`로 가능).
- Windows는 `~` 대신 `%USERPROFILE%`. 명령은 PowerShell 기준으로 바꿔 실행한다.

## 2. 등록 + 환경 확인
```bash
cd ~/teacher-studio
python3 scripts/setup.py --agent <AGENT>        # Windows: py scripts/setup.py --agent <AGENT>
```
- 스킬 4개(`teacher-studio`, `teacher-game`, `teacher-slides`, `teacher-motion`)를 등록한다.
  - Claude Code → `~/.claude/skills/` · Codex → `~/.agents/skills/`
- 끝에 「🎉 준비 완료」 요약이 나온다.
- `claude-app`이면 등록 대신: 작업 공간에 받은 폴더의 `skills/teacher-studio/scripts/studio.py doctor --agent claude-app`을 실행하고, 선생님께 「설정 → 스킬에서 `dist/` zip 4개를 올리면 다음 대화부터 자동으로 켜져요」라고 안내한다.

## 3. (선택) 영상 MP4·자동 플레이 점검 도구
선생님께 먼저 묻는다: 「영상을 MP4 파일로도 받으시려면 프로그램을 하나 더 깔아야 해요(약 150MB, 2~3분). 지금 깔까요? (예 / 나중에)」
- 예 → `python3 scripts/setup.py --agent <AGENT> --video`
- ffmpeg가 없다고 나오면 운영체제에 맞는 설치 명령 한 줄을 실행한다 (Windows `winget install ffmpeg`, Mac `brew install ffmpeg`). 실패하면 「영상은 화면의 🎥 버튼으로 받으시면 돼요」로 마무리.

## 4. 시험 발사 (30초)
```bash
python3 ~/.claude/skills/teacher-studio/scripts/studio.py fire motion/lesson-opening/bold-pop --open
# Codex는 ~/.agents/skills/... 경로
# Windows(PowerShell): py "$env:USERPROFILE\.claude\skills\teacher-studio\scripts\studio.py" fire motion/lesson-opening/bold-pop --open
```
- `READY` 가 나오면 성공. 크롬에 「수업 시작 화면」이 열린다.

## 5. 선생님께 첫 인사
`teacher-studio` 스킬의 **준비 카드**를 그대로 보여 준다 (doctor 요약 + 메뉴 5개).
- 이 환경에서 안 되는 기능(공유 링크, MP4 등)은 카드 안에 이미 한 줄로 들어 있다. 덧붙여 설명하지 않는다.
- 마지막 줄: 「새 대화에서 '교사 스튜디오 시작'이라고 하시거나, 만들고 싶은 걸 바로 말씀해 주세요.」
- Claude Code·Codex는 새 스킬을 바로 못 볼 수 있다 → 「한 번 껐다 켜 주세요」 안내.

## 문제가 생기면
| 상황 | 할 일 |
|---|---|
| `python3` 없음 | Windows: `py` 사용, 없으면 `winget install Python.Python.3.12` / Mac: `xcode-select --install` |
| 권한 오류 | 사용자 폴더(`~`) 안에서만 설치한다. 관리자 권한을 요구하지 않는다 |
| 회사·학교 네트워크로 git 차단 | zip 받기 경로로 |
| 그래도 안 됨 | 선생님께 「캡처 한 장 보내 주세요」, 오류 문장은 직접 해석해서 한 줄로 설명 |

## 업데이트
`cd ~/teacher-studio && git pull && python3 scripts/setup.py --agent <AGENT>`
