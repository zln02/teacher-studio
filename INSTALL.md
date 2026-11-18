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
python3 scripts/setup.py --agent <AGENT>
```
- 파이썬 실행 이름은 환경마다 다르다. 이 문서의 `python3`는 Windows에서 `py`(없으면 `python`)로 바꿔 실행한다. 예: `py scripts/setup.py --agent <AGENT>`
- 스킬 5개(`teacher-studio`, `teacher-game`, `teacher-slides`, `teacher-motion`, `teacher-law`)를 등록한다.

### 환경별 설치
| 환경 | 설치 방법 | 알아 둘 점 |
|---|---|---|
| **Claude Code** | 위 명령 → `~/.claude/skills/`에 등록 | 내 컴퓨터에서 실행, 인터넷 제한 없음. 웹 검색·페이지 읽기 내장 (최신 법 확인 OK). Claude 구독 또는 API 키 필요 |
| **Codex** (앱·CLI·IDE) | 위 명령 → `~/.agents/skills/`에 등록 | 내 컴퓨터에서 실행. 작업 폴더 밖에 쓸 때는 **승인 창**이 뜨니 허용하도록 안내. **인터넷은 기본 꺼짐**: `~/.codex/config.toml`에 `[sandbox_workspace_write]` 아래 `network_access = true`를 켜야 도구 설치·최신 법 확인이 된다. 웹 검색은 `--search`(live)로 켠다. 무료·Go 요금제에도 포함 |
| **Claude 앱·웹** | 등록 대신 zip 올리기 (아래) | 클라우드 컨테이너에서 실행 → 내 컴퓨터 폴더·크롬에 접근 못 함, 결과는 미리보기·다운로드. 인터넷은 PyPI·npm·GitHub 정도만 허용. 무료 요금제 포함 |

**Claude 앱·웹 (`claude-app`)**: 선생님께 「설정(Customize) → Skills에서 `dist/` 폴더의 zip 5개(`teacher-studio`·`teacher-game`·`teacher-slides`·`teacher-motion`·`teacher-law`)를 올려 주세요. 다음 대화부터 자동으로 켜져요」라고 안내한다.
- 설정 → Capabilities에서 **코드 실행·파일 만들기**가 켜져 있어야 한다 (기본 켜짐). 최신 법 확인에는 **웹 검색**도 켠다.
- AI가 이미 코드 실행 환경에 저장소를 받았다면 `python3 skills/teacher-studio/scripts/studio.py doctor --agent claude-app`로 환경만 확인한다.
- 끝에 「🎉 준비 완료」 요약이 나온다 (Claude Code·Codex).

## 3. 영상 MP4·자동 플레이 점검 도구 — 처음 요청할 때 설치
**설치 중에는 묻지 않는다.** 선생님이 처음으로 MP4 파일(또는 자동 플레이 점검)이 필요한 요청을 했을 때 이렇게 말한다:
「MP4로 받으려면 프로그램을 하나 더 깔아야 해요(약 80MB, 크롬이 이미 있으면 그걸 써요). 지금 깔까요? (예 / 나중에)」
- **예** → `python3 scripts/setup.py --agent <AGENT> --video` (직접 미리 깔고 싶을 때 쓰는 수동 방법이기도 하다)
  - 영상 도구(ffmpeg)는 `shared/tools/ensure.py`가 컴퓨터에 있는 것을 먼저 쓰고, 없으면 `pip install --user imageio-ffmpeg`(약 40MB)로 받는다. 직접 깔려면 Windows `winget install ffmpeg`, Mac `brew install ffmpeg`. 실패하면 「영상은 화면의 🎥 버튼으로 받으시면 돼요」로 마무리.
- **Claude Code**: 바로 가능 (인터넷 제한 없음).
- **Codex**: 인터넷이 켜져 있어야 한다. 꺼져 있으면 위 표의 `network_access = true` 안내를 먼저 하고, 그래도 어려우면 🎥 녹화로 대신한다.
- **Claude 앱·웹**: 인터넷 제한 때문에 도구 설치가 안 될 가능성이 크다 → 처음부터 크롬 녹화(.webm) 방법으로 안내한다.

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
| `python3` 없음 (Windows는 `py`) | Windows: `py` 사용, 없으면 `winget install Python.Python.3.12` / Mac: `xcode-select --install` |
| 권한 오류 | 사용자 폴더(`~`) 안에서만 설치한다. 관리자 권한을 요구하지 않는다 |
| 회사·학교 네트워크로 git 차단 | zip 받기 경로로 |
| 그래도 안 됨 | 선생님께 「캡처 한 장 보내 주세요」, 오류 문장은 직접 해석해서 한 줄로 설명 |

## 업데이트
`cd ~/teacher-studio && git pull && python3 scripts/setup.py --agent <AGENT>` (Windows: `py scripts/setup.py --agent <AGENT>`)
