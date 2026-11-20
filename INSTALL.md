# 교사 스튜디오 설치 안내

> Codex·Claude가 읽고 실행하는 안내입니다. 선생님께는 진행 상황과 다음에 할 일을 일상적인 말로 짧게 알려 주세요.

## 1. 사용할 곳 확인

- **Codex 앱·명령 창·편집기**에서 이 저장소를 열었다면 아래 순서를 실행한다. 사용자 스킬 위치는 Windows에서 `$HOME/.agents/skills`, macOS에서 `~/.agents/skills`다.
- **Claude Code**는 같은 순서에서 `--agent claude-code`를 쓴다. 사용자 스킬 위치는 `~/.claude/skills`다.
- **Claude 앱·웹**에서 스킬 올리기와 파일 실행 기능을 실제로 사용할 수 있다면, [배포](dist/)에서 같은 출시 버전의 ZIP 8개를 올린다.
- 일반 대화와 관리형 환경에서는 스킬 목록, 명령 실행, 파일 저장이 서로 다른 기능이다. 앱에서 확인한 범위만 안내한다. Codex 공개 플러그인 배포 상태와 관계없이 아래 사용자 폴더 설치를 쓸 수 있다.

선생님께 「교사 스튜디오 설치를 시작할게요.」라고 알린다.

## 2. 설치 파일과 파이썬 확인

이미 저장소를 열었다면 그 폴더에서 이어 간다. 링크만 받았다면 쓸 수 있는 작업 폴더에서 `git clone --depth 1 https://github.com/zln02/teacher-studio.git`을 실행하고 `teacher-studio`로 이동한다. `git`을 쓸 수 없으면 저장소의 Download ZIP을 내려받아 압축을 푼다.

**Windows PowerShell**

```powershell
py --version
# py로 실행되지 않으면 다음 명령을 시험한다.
python --version
```

**macOS**

```sh
python3 --version
```

실제로 Python 3.9 이상이 실행된 명령을 이후에도 사용한다. 실행기가 없으면 [Python 내려받기](https://www.python.org/downloads/)를 이용하거나 이미 쓸 수 있는 실행기를 고른다. 설치 위치에 쓸 수 있는 권한이 있어야 한다. 앱이 제공하는 승인 절차가 있으면 그 절차를 따르고, 학교에서 관리하는 환경의 권한을 임의로 바꾸지 않는다.

## 3. 사용자 폴더에 등록

**Windows PowerShell**

```powershell
$env:PYTHONUTF8 = '1'
py scripts/setup.py --agent codex
# 앞 단계에서 python만 동작했다면 python scripts/setup.py --agent codex
```

**macOS**

```sh
python3 scripts/setup.py --agent codex
```

Claude Code에서는 `codex`를 `claude-code`로 바꾼다. 스킬 8개는 서로 옆 폴더를 찾는 한 묶음이므로 함께 등록한다. 설치기는 새 묶음을 임시 위치에서 확인한 뒤 교체한다. 업데이트할 때는 저장소를 `git pull --ff-only`로 갱신한 뒤 같은 명령을 쓴다.

명령 실행이 불가능하고 사용자 폴더에 쓸 수 있다면 `skills` 안의 `teacher-` 폴더를 모두 해당 사용자 스킬 위치에 복사할 수 있다. 이미 설치한 것이 있으면 먼저 별도 위치에 보관한다.

## 4. 현재 대화에서 확인

새 대화나 앱 재시작 후, 연동된 목록에서 `teacher-studio`를 확인한다. 저장소 안에서 읽는 `AGENTS.md`는 해당 작업에 적용된다. 저장소 밖에서는 설치된 스킬 설명을 보고 고르므로, 빈 작업 폴더에서 「교사 스튜디오 시작」, 「5분 타이머 만들어 줘」, 「중2 과학 수업 시작 화면 만들어 줘」를 각각 시험할 수 있다. Codex에서 직접 고를 때는 `$teacher-studio`를 사용한다.

작업 폴더에서 셸 실행과 파일 저장을 확인할 수 있다면, 다음 명령은 HTML을 만들고 검사를 실행한다.

**Windows PowerShell**

```powershell
py "$HOME/.agents/skills/teacher-studio/scripts/studio.py" fire motion/lesson-opening/bold-pop --out "수업 시작.html"
```

**macOS**

```sh
python3 "$HOME/.agents/skills/teacher-studio/scripts/studio.py" fire motion/lesson-opening/bold-pop --out "수업 시작.html"
```

Claude Code에서는 명령의 `.agents`를 `.claude`로 바꾼다. 파일이 만들어졌는지와 실제 작동을 확인했는지는 따로 알린다. 브라우저 확인이 어려우면 선생님께 「파일을 만들었어요. 화면이 잘 움직이는지는 아직 확인하지 못했어요.」라고 알린다.

현재 대화에서 실제로 검색·미리 보기·링크 만들기를 할 수 있는지 각각 확인한다. 준비 카드에 포함하려면 `studio.py doctor`에 `--web-search`, `--preview`, `--share`를 각각 `yes` 또는 `no`로 전달한다. 확인 전에는 생략한다. 셸에서 설치 파일을 받는 곳에 연결되는지와 대화에서 공식 출처를 검색할 수 있는지는 별도로 판단한다.

문법 검사가 일부 미확인이고 작은 점검 도구 받기에 동의한 경우, `shared/tools/ensure.py acorn --yes`를 같은 파이썬 명령으로 실행한다. 그다음 검사를 다시 실행한다.

## 5. 필요해졌을 때 영상 도구 확인

MP4나 자동 작동 확인을 처음 부탁받으면 쓸 수 있는 도구가 있는지 먼저 확인한다. 추가 설치가 필요하면 용량을 짧게 알리고 동의를 받은 뒤 같은 설치 명령에 `--video`를 붙인다. 이미 설치된 Chrome·Edge나 녹화 프로그램부터 확인한다. 설치가 어려우면 만들 수 있는 화면을 제공하고 「화면의 녹화 버튼으로 영상을 받을 수 있어요.」라고 안내한다.

설치 이후에는 새 대화에서 「교사 스튜디오 시작」이라고 하시거나, 만들고 싶은 걸 바로 말씀해 달라고 안내한다.
