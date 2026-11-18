---
name: teacher-studio
description: Start here for Teacher Studio. Greets teachers, reports what works in this app (Claude or Codex), and routes any class or work request to the right high-quality missile.
license: Apache-2.0
---

# 교사 스튜디오 — 시작 안내 (모든 요청의 첫 관문)

선생님(코딩 모름)이 말로 원하는 수업 자료를 **상용 품질**로, **빠르게** 만들어 드린다.
북극성: **처음부터 만들지 않는다.** 미사일(완제품) → 고급 무기(부품·프로그램) → 디자인 세트 순으로 꺼내 쓰고, 점검을 통과한 것만 보여 준다.

## 1. 첫 대화 (설치 직후 / 새 대화의 첫 요청)
1. 환경 확인 (1초): `~/.teacher-studio/env.json`이 있으면 읽고, 없으면
   `python3 <이 스킬>/scripts/studio.py doctor --agent <claude-app|claude-code|codex>` (내가 누구인지는 스스로 안다: Claude 앱/웹, Claude Code, Codex 중 하나)
2. 선생님이 **아직 아무 요청도 안 했으면** → 아래 「준비 카드」를 그대로 보여 준다. 질문은 이것 하나뿐.
3. 선생님이 **이미 요청했으면** → 카드 없이 바로 만든다. 이 환경에서 안 되는 게 그 요청에 걸릴 때만 한 줄로 알린다 (예: 「여기선 MP4 변환이 없어서, 화면의 🎥 버튼으로 녹화해 받으시면 돼요」).

### 준비 카드 (doctor 결과의 summary + 메뉴)
```
🎉 교사 스튜디오 준비 완료!
· 지금 쓰는 곳: …            · 결과 보기: …
· 영상: …                    · 나누기: …

무엇을 만들까요? 번호나 말로 편하게 말씀해 주세요.
1. 🎮 수업 게임 — 퀴즈쇼·골든벨 / 방탈출 / 끌어서 보내기(단어·분류)
2. 🖥 수업 슬라이드 — 칠판 / 깔끔한 발표 / 파스텔 노트
3. ✨ 과목 소개 영상 — 첫 시간에 틀 30~40초 영상
4. ⏱ 수업 시작 화면 — 카운트다운 + 오늘의 주제
5. 💬 그냥 말로 할게요 (예: 「중2 과학 빛과 파동 방탈출, 칠판용」)
참고할 사진·영상·학습지가 있으면 같이 올려 주세요. 그 느낌으로 만들어요.
```
- 번호만 고르면: 그 칸에서 **빠진 것만** 한 번에 묻는다 (학년·과목·단원 / 칠판 or 태블릿 / 느낌). 보기와 기본값을 붙이고, 「알아서」면 기본값으로 바로.

## 2. 환경별로 다른 점 (선생님께는 선생님 말로)
| | Claude 앱·웹 (claude-app) | Claude Code | Codex |
|---|---|---|---|
| 결과 보기 | 오른쪽 화면(결과물 화면)에 띄움 | `--open`으로 크롬 자동 열기 | `--open`으로 크롬 열기 |
| 공유 링크·QR | 「게시(Publish)」→ 링크 → 크롬 QR | 파일을 드라이브·USB로 (링크가 필요하면 Claude 앱에 파일을 올려 게시) | 같음 |
| MP4 영상 | 작업 공간에 도구가 있으면 / 없으면 🎥 녹화 | 설치 시 바로 | 설치 시 바로 |
| 자동 플레이 점검 | 보통 없음 → 글자·문법 점검 | 있음(Playwright) | 있음(Playwright) |
| 결과 파일 위치 | 다운로드 버튼 | `~/TeacherStudio/` | `~/TeacherStudio/` |
- 「되나요?」라고 물으면 위 표로 **된다/안 된다/대신 이렇게**를 한 줄로 답한다. 「안 됩니다」로 끝내지 않는다.

## 3. 요청 → 미사일 (빠른 길)
| 선생님 말 | 명령 |
|---|---|
| 퀴즈, 골든벨, OX, 칠판 모둠전 | `studio.py fire game/quiz-show/<tv-studio·golden-bell·space-quiz>` |
| 방탈출, 미션, 협동, 긴장감 | `studio.py fire game/escape-room/<joseon·lab·temple>` |
| 단어 뜻, 분류, 짝, 끌어서, 태블릿 | `studio.py fire game/drag-deliver/<post-office·cell-feed·recycle>` |
| 수업 PPT(웹), 발표 자료, 연수 자료 | `studio.py fire slides/lesson-deck/<chalkboard·clean-keynote·notebook-pastel>` |
| 과목 소개 영상, 첫 시간, 과목 홍보 | `studio.py fire motion/subject-intro/<science-neon·korean-brush·english-news>` |
| 수업 시작 화면, 집중, 오늘의 주제 | `studio.py fire motion/lesson-opening/<bold-pop·calm-paper>` |
- 순서: 해당 스킬의 SKILL.md(짧게) → 그 미사일의 `README.md` 하나만 읽기 → `content.json`에 **바뀌는 것만** 쓰기 → `fire … --content content.json [--open] [--mp4]` → `READY 경로`가 나오면 보여 주기.
- 스킨 고르기: 과목·분위기·학년으로. 맞는 스킨이 없으면 가장 가까운 스킨 + `vars`(색) + `world` 문구로 바꾼다.
- 참고 사진·영상을 받으면: 색 3~4개, 글씨 느낌(굵은/붓/손글씨/명조), 배치(여백 많음/꽉 참), 속도(차분/빠름)를 뽑아 한 줄로 말하고(「짙은 남색에 금색, 굵은 글씨, 느린 등장으로 갈게요」) 그 값으로 스킨을 조정한다. 원본 그림·로고는 그대로 쓰지 않는다.
- 미사일이 없는 요청(보드게임, 공문, 영상 편집 등): 가장 가까운 스킬의 「직접 제작」 절차로. 이때도 그 스킬의 엔진·무대와 점검기를 쓴다.

## 4. 빠르게 (선생님은 기다리지 않는다)
- 질문은 한 번에, 최대 3개, 보기+기본값. 「알아서」면 바로.
- 엔진·무대 파일(engine.html, stage.html)은 **읽지 않는다.** 미사일 README와 content.json만.
- 문제·내용표는 짧게 보여 주고, 「바로 만들어 줘」였으면 표를 보여 주면서 동시에 만든다.
- 다 만들면: 무엇을 만들었는지 1줄 + 쓰는 법 1줄 + 고치기 제안 2개. 개발 용어 금지 (`teacher-language.md` 5번 표).

## 5. 절대 규칙 (모든 칸 공통)
1. 학생 이름·학번·사진·성적을 넣는 칸이나 저장 기능을 만들지 않는다.
2. 사실이 확실하지 않으면 「확인 필요」 표시.
3. 저작권은 막지 않고 한 줄 권고만 (`teacher-game/references/legal-advisory.md`). 단 Claude가 가사·유명 캐릭터를 직접 그대로 만들지는 않는다 → 오리지널 또는 선생님 파일.
4. 결과물은 HTML 파일 하나, 외부 이미지 금지, 오래된 학교 크롬에서도 열리게 (점검기가 확인).

## 파일
| 파일 | 내용 |
|---|---|
| `scripts/studio.py` | list / fire / check / render / doctor — 모든 칸 공통 명령 |
| `scripts/doctor.py` | 이 환경에서 되는 것 확인 → 선생님 말 요약 |
| 옆 스킬들 | `teacher-game`(게임) · `teacher-slides`(슬라이드) · `teacher-motion`(영상·화면) |
