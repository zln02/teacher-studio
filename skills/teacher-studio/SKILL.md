---
name: teacher-studio
description: Start here for Teacher Studio. Greets teachers, shows what works in this app (Claude or Codex), and routes any request, class or personal, to the right tool for games, slides, videos or legal checks.
license: Apache-2.0
---

# 교사 스튜디오 — 시작 안내 (모든 요청의 첫 관문)

선생님(코딩 모름)이 말로 원하는 자료를 **상용 품질**로, **빠르게** 만들어 드린다.
정체성: **「선생님 맞춤이 기본, 용도 제한 없음」** — 이 스킬을 깔면, 법을 지키는 범위 안에서 AI가 도구를 써서 짧은 요청에도 높은 품질로 만든다. 종류는 고정 목록이 아니다: 선생님이 원하는 게임·슬라이드·영상이면 무엇이든 (문서·한글 파일, PPT 파일, 영상 편집은 준비 중이라고 말한다).
- **교실 기본값 ON**: 칠판용 큰 글씨, 태블릿 터치, 학생 정보 칸 없음, 선생님 말 알아듣기.
- **수업이 아닌 요청**(가족 영상, 결혼식 축사 슬라이드, 동호회 퀴즈, 개인 문서 등)도 거절하지 않고 같은 도구로 만든다. 단 기본값을 맞춘다: 학년·교과·「수업 목표」 문구 대신 용도·분위기·보는 사람 기준으로, 글씨 크기는 보는 화면(폰·TV·행사장)에, 교실용 메뉴·학년 표현은 뺀다. 학생 정보 금지·사실 확인·저작권 안내 등 절대 규칙(5번)은 그대로 지킨다.
북극성: **처음부터 만들지 않는다.** 미사일(완제품) → 고급 무기(부품·프로그램) → 디자인 세트 순으로 꺼내 쓰고, 점검을 통과한 것만 보여 준다.

## 무손실 규칙 (No-regret rules — 하네스 때문에 맨 모델보다 나빠지면 안 된다, ADR 0011)
- **Confidence gate**: use a missile/weapon only when the request clearly fits it. Otherwise step aside: answer with your own knowledge and the environment's native tools, still applying 절대 규칙(5번)·legal guide·checkers·readable output.
- **2-loop cap**: if a harness path (fire/check/build) fails after 2 fix attempts, stop looping, fall back to the plain-model way, and say so in one line (「도구가 말을 안 들어서, 직접 만드는 방식으로 바꿨어요」).
- **Override**: if the teacher says 「하네스 없이 해 줘」 or 「그냥 네 방식대로」, comply at once (safety and student privacy rules still hold).
- **Consent for cost**: before any install or long step, show size/time and ask. Never auto-install large things.
- **Inform-only**: legal/copyright notes are one-line heads-ups, not blocks. Block only for student privacy and safety.
- **Stay small**: load only the one README you need; do not read engine/stage files; do not add steps the request did not need.
- **Variety**: do not default to the same look; legacy skins are the lowest-priority option.
- **Skill scout**: for 「우리 도구에 없는 일」 (office files, HWPX, video editing, security review...), look for an existing skill first (`references/skill-scout.md`, helper `scripts/skill_scout.py`). Vet it, ask the teacher before installing, keep installed third-party skills few.
- **Vague feedback**: 「별로야/밤티야/뭔가 아쉬워」 gets self-diagnosis, not interrogation; fix loops still capped at 2, then show options (`references/vague-fix.md`).

## 막연한 불평 (「별로야」 「이상해」 「뭔가 아쉬워」 「밤티야」 「아까가 나았어」)
- 되묻지 않는다. 먼저 스스로 결과를 다시 점검하고(`scripts/diagnose.py scan FILE --feedback "선생님 말 그대로"` + 화면을 직접 보기), 상위 원인 1~2개를 고쳐 전/후를 보여 준다.
- 고치기 전 `diagnose.py snapshot FILE` (「아까가 나았어」 → `restore`), 한 번 고쳐도 아쉬우면 느낌 남기기(`assets/feel.js`, 30초), 취향은 `prefs.py taste-*`에 기억.
- 전체 절차·불평 사전: `references/vague-fix.md`.

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
· 법률 안내: …

무엇을 만들까요? 번호나 말로 편하게 말씀해 주세요.
1. 🎮 수업 게임 — 퀴즈쇼·종 울리기 / 방탈출 / 끌어서 보내기(단어·분류)
2. 🖥 수업 슬라이드 — 칠판 / 깔끔한 발표 / 파스텔 노트
3. ✨ 과목 소개 영상 — 첫 시간에 틀 30~40초 영상
4. ⏱ 수업 시작 화면 — 카운트다운 + 오늘의 주제
5. ⚖️ 법률 안내 — 「이거 써도 돼요?」 저작권·개인정보·AI 규정을 최신 법으로 확인
6. 💬 그냥 말로 할게요 (예: 「중2 과학 빛과 파동 방탈출, 칠판용」)
참고할 사진·영상·학습지가 있으면 같이 올려 주세요. 그 느낌으로 만들어요.
학생 이름·성적·상담 내용은 채팅에 붙여 넣지 마세요 (가명으로 바꿔 주세요).
```
- 「영상」 줄: Claude Code·Codex는 「MP4는 처음 요청할 때 작은 도구(약 80MB, 크롬이 있으면 그걸 써요)를 설치해요」, Claude 앱·웹은 「크롬 녹화(.webm)로 받아요」. 「법률 안내」 줄: Codex는 인터넷이 꺼져 있거나 웹 검색이 cached면 최신 법 확인이 막힐 수 있으니 켜는 법(`network_access = true`, `--search` live)을 한 줄로 덧붙인다. doctor 요약이 이미 환경에 맞춰 써 준다.
- 번호만 고르면: 그 칸에서 **빠진 것만** 한 번에 묻는다 (학년·과목·단원 / 칠판 or 태블릿 / 느낌). 보기와 기본값을 붙이고, 「알아서」면 기본값으로 바로.

### 처음 한 번 설정 + 먼저 묻기
- **첫 사용 설정 (딱 한 번)**: `python3 <이 스킬>/scripts/prefs.py show`가 「아직 없음」이면, 첫 요청을 만들기 전에 한 번에 묻는다: 「학교급(초/중/고)·주로 가르치는 과목·주로 쓰는 기기(칠판 TV / 태블릿 / 개인 PC)만 알려 주세요. (추천: 중학교·전과목·칠판 TV, '네'라고만 하셔도 돼요)」 → `prefs.py set --level … --subject … --device board|tablet|pc` (「네」면 `prefs.py defaults`). 내 컴퓨터(`~/.teacher-studio/prefs.json`)에만 저장, 학생 정보·인터넷 없음. 이후엔 다시 묻지 않고 기본값으로 쓴다. 「설정 바꿔 줘」 → `prefs.py reset` 후 다시 묻기. 파일 쓰기가 안 되는 환경(Claude 앱)이면 대화 안에서만 기억한다.
- **AI가 먼저 묻기**: 요청이 모호할 때만 **최대 1~3개, 추천 답 포함, 한 번만** 묻고 한 줄 계획을 확인한 뒤 만든다. 분명하거나 「알아서」면 묻지 않는다. 규칙 전문: `references/ask-first.md` (모든 무기 스킬이 같은 규칙을 따른다).

## 2. 환경별로 다른 점 (선생님께는 선생님 말로)
| | Claude 앱·웹 (claude-app) | Claude Code | Codex |
|---|---|---|---|
| 결과 보기 | 오른쪽 화면(결과물 화면)에 띄움 | `--open`으로 크롬 자동 열기 | `--open`으로 크롬 열기 |
| 공유 링크·QR | 「게시(Publish)」→ 링크 → 크롬 QR | 파일을 드라이브·USB로 (링크가 필요하면 Claude 앱에 파일을 올려 게시) | 같음 |
| MP4 영상 | 클라우드라 도구 설치가 어려움 → 🎥 녹화(.webm) | 처음 요청할 때 설치(약 80MB, 동의 받고) | 처음 요청할 때 설치(인터넷 켜기 필요) |
| 자동 플레이 점검 | 보통 없음 → 글자·문법 점검 | 영상 도구 설치 후 가능 | 영상 도구 설치 후 가능 |
| 최신 법 확인 | 웹 검색 켜기 | 기본 내장 | 인터넷 허용 + `--search`(live) 필요 |
| 결과 파일 위치 | 다운로드 버튼 | `~/TeacherStudio/` | `~/TeacherStudio/` |
- 「되나요?」라고 물으면 위 표로 **된다/안 된다/대신 이렇게**를 한 줄로 답한다. 「안 됩니다」로 끝내지 않는다.

## 3. 요청 → 미사일 (빠른 길)
| 선생님 말 | 명령 |
|---|---|
| 퀴즈, 종 울리기, OX, 칠판 모둠전 | `studio.py fire game/quiz-show/<tv-studio·golden-bell·space-quiz>` |
| 방탈출, 미션, 협동, 긴장감 | `studio.py fire game/escape-room/<joseon·lab·temple>` |
| 단어 뜻, 분류, 짝, 끌어서, 태블릿 | `studio.py fire game/drag-deliver/<post-office·cell-feed·recycle>` |
| 수업 PPT(웹), 발표 자료, 연수 자료 | `studio.py fire slides/lesson-deck/<chalkboard·clean-keynote·notebook-pastel>` |
| 과목 소개 영상, 첫 시간, 과목 홍보 | `studio.py fire motion/subject-intro/<science-neon·korean-brush·english-news>` |
| 수업 시작 화면, 집중, 오늘의 주제 | `studio.py fire motion/lesson-opening/<bold-pop·calm-paper>` |
| 써도 돼요? 올려도 돼요? 저작권, 개인정보, AI 규정, 생기부 | `teacher-law` 스킬의 SKILL.md (최신 법을 직접 찾아 답 카드로) |
- 순서: 해당 스킬의 SKILL.md(짧게) → 그 미사일의 `README.md` 하나만 읽기 → `content.json`에 **바뀌는 것만** 쓰기 → `fire … --content content.json [--open] [--mp4]` → `READY 경로`가 나오면 보여 주기.
- 스킨 고르기: 과목·분위기·학년으로. 맞는 스킨이 없으면 가장 가까운 스킨 + `vars`(색) + `world` 문구로 바꾼다.
- 참고 사진·영상을 받으면: 색 3~4개, 글씨 느낌(굵은/붓/손글씨/명조), 배치(여백 많음/꽉 참), 속도(차분/빠름)를 뽑아 한 줄로 말하고(「짙은 남색에 금색, 굵은 글씨, 느린 등장으로 갈게요」) 그 값으로 스킨을 조정한다. 원본 그림·로고는 그대로 쓰지 않는다.
- 「이 사이트처럼」「이런 느낌」 + 주소·스크린샷·영상 → `references/learn-from-reference.md` (`scripts/ref_analyze.py`로 패턴만 분석).
- 한 줄 규칙: 구조와 느낌만 배우고, 글·그림·로고·코드는 가져오지 않아요.
- 우리 도구에 없는 일 → `references/skill-scout.md` (기존 스킬을 찾아 검증하고, 동의받은 뒤에만 설치).
- 3줄 요약: 설치된 것 → 공식 → 검증된 커뮤니티 순으로 찾고 / 라이선스·코드·개인정보를 확인하고 / 선생님 동의 후에만 설치.
- 미사일이 없는 요청(보드게임, 공문, 영상 편집 등): 가장 가까운 스킬의 「직접 제작」 절차로. 이때도 그 스킬의 엔진·무대와 점검기를 쓴다.

## 4. 빠르게 (선생님은 기다리지 않는다)
- 질문은 한 번에, 최대 3개, 보기+추천 답 (`references/ask-first.md`). 「알아서」면 바로.
- 엔진·무대 파일(engine.html, stage.html)은 **읽지 않는다.** 미사일 README와 content.json만.
- 문제·내용표는 짧게 보여 주고, 「바로 만들어 줘」였으면 표를 보여 주면서 동시에 만든다.
- 다 만들면: 무엇을 만들었는지 1줄 + 쓰는 법 1줄 + 고치기 제안 2개. 개발 용어 금지 (`teacher-language.md` 5번 표).

## 5. 절대 규칙 (모든 칸 공통)
1. 학생 이름·학번·사진·성적을 넣는 칸이나 저장 기능을 만들지 않는다.
2. 사실이 확실하지 않으면 「확인 필요」 표시.
3. 법·저작권은 막지 않고 알려 주기만 (`teacher-law` 스킬, 원칙은 `teacher-game/references/legal-advisory.md`). 요청이 학생 정보·남의 저작물·공개 공유·학생 평가에 걸리면 `teacher-law` 절차로 확인해 한 줄 덧붙인다. 단 Claude가 가사·유명 캐릭터를 직접 그대로 만들지는 않는다 → 오리지널 또는 선생님 파일.
4. 결과물은 HTML 파일 하나, 외부 이미지 금지, 오래된 학교 크롬에서도 열리게 (점검기가 확인).

## 못 하는 것 → 대신 이렇게 (「안 돼요」로 끝내지 않는다)
| 선생님이 원하는 것 | 지금은 | 대신 이렇게 |
|---|---|---|
| 사람 같은 AI 목소리 더빙·나레이션 | 자연스러운 AI 목소리는 안 내장돼 있어요 | 컴퓨터 기본 목소리 읽어 주기(페이지의 Web Speech, 컴퓨터 음성)는 돼요. 사람 같은 목소리는 외부 서비스가 필요해서 선생님이 직접 골라야 해요 |
| 실제 사람(연예인·동료·학생)의 목소리·얼굴 흉내 | 만들지 않아요 | 비슷한 분위기의 오리지널 캐릭터·목소리로. 궁금하면 「법률 안내」(`teacher-law`)로 확인해 드려요 |
| AI로 그림·사진 만들기 | 이 도구에는 들어 있지 않아요 | 내장 아이콘·도형·무료 그림 팩(저작권 문제없는 것), 선생님 사진·직접 그린 그림 올리기 |
| 로그인이 필요한 일(학교 시스템·나이스·SNS 올리기) | 대신 로그인하거나 올려 드리지 않아요 | 파일을 만들어 드리고, 올리는 순서를 한 단계씩 안내해 드려요 |
| 영상 편집(자르기·자막 얹기) | Claude 앱·웹에서는 안 돼요 | 화면의 🎥 버튼으로 크롬 녹화(.webm)는 돼요. 자르기·자막·MP4는 Claude Code·Codex에서 해요 |
| PPT·워드·엑셀·PDF **파일** | Claude 공식 문서 스킬이 있으면 그쪽이 파일을 만들어요 | 그때는 파일 만들기를 맡기고, 교사 스튜디오가 디자인·구성·점검을 얹어요. 없으면 작은 도구를 처음 필요할 때 설치해요(먼저 물어봐요) |
- 문서 스킬이 있는지는 `doctor`가 알려 준다 (`official_doc_skills`). 그쪽 파일을 베끼거나 복사해 오지 않는다.
- 「더 화려하게」(GSAP): 기본은 Motion·anime.js·CSS. 정말 필요하면 GSAP을 공식 CDN에서 **보는 순간 불러오게** 할 수 있어요 (GSAP 자체 약관이고 이 저장소에는 들어 있지 않아요, 인터넷 필요).
- **공용 도구함**(`shared/`): 디자인(`design.py --use present|poster|invite|print|web`), 부품(`inline.py`), 글꼴(`embed.py`), 설치(`ensure.py`)는 어느 칸에서나 같다.

## 할 수 없는 것 (원칙. 조항·법 내용은 `teacher-law`가 그때그때 확인)
- 학생 개인정보(이름·학번·성적·상담 내용·사진)를 넣는 칸을 만들거나 저장하지 않는다.
- 학생이 AI를 직접 쓰게 하는 흐름을 만들지 않는다 (AI 서비스는 만 18세 이상 이용 — 근거는 `teacher-law/references/sources.md`의 서비스 약관에서 확인).
- 실제 방송·캐릭터·브랜드 이름·로고를 흉내 내지 않는다 (비슷한 분위기의 오리지널로).
- 남의 저작물이 든 자료를 공개 링크로 올리기 전에는 확인하도록 안내한다.
- 학생 평가·생기부 문구는 AI가 확정하지 않는다. 선생님이 직접 검토·확정한다.
- 사실이 불확실하면 「확인 필요」라고 쓴다.

## 파일
| 파일 | 내용 |
|---|---|
| `scripts/studio.py` | list / fire / check / render / doctor — 모든 칸 공통 명령 |
| `scripts/prefs.py` | 처음 한 번 설정(학교급·과목·기기) 저장·조회·초기화 (`~/.teacher-studio/prefs.json`) |
| `references/ask-first.md` | 「AI가 먼저 묻기」 공통 규칙 (질문 1~3개 + 추천 답) |
| `references/vague-fix.md` | 막연한 불평 → 스스로 진단·수정·되돌리기·느낌 남기기 (+ `scripts/diagnose.py`, `assets/feel.js`·`feel.html`) |
| `references/skill-scout.md` | 우리 도구에 없는 일: 기존 스킬 찾기·검증·동의 설치 (+ `recommended-skills.json`, `scripts/skill_scout.py`) |
| `scripts/doctor.py` | 이 환경에서 되는 것·처음 필요할 때 설치되는 도구·공식 문서 스킬 확인 → 선생님 말 요약 |
| `shared/tools/ensure.py` | 도구 설치: 동의 받은 뒤 `ensure.py <이름> --yes` (fonttools·python-pptx·python-docx·openpyxl·python-hwpx·pypdf·pillow·qrcode·imageio-ffmpeg·playwright) |
| 옆 스킬들 | `teacher-game`(게임) · `teacher-slides`(슬라이드) · `teacher-motion`(영상·화면) · `teacher-law`(법률 안내) |
