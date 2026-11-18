---
name: teacher-game
description: Makes any game as one HTML file from a plain request - class quiz, escape room, bingo, board, matching, sorting - or a family/club game. Big board-readable defaults. Use for any game or activity.
license: Apache-2.0
---

# 교사 스튜디오 · 게임

말로 설명한 **어떤 게임이든** 전자칠판·태블릿에서 바로 돌아가는 화려한 단일 HTML 게임으로 만든다. 수업용이 기본이고, 가족 모임·동아리·개인용도 **막지 않고 같은 도구로** 만든다.
AI는 **짧은 기획(spec) 한 장**만 쓴다. 엔진·부품·디자인·점검은 도구가 맡는다 → 매번 같은 품질, 사용량 최소.

## 선생님 말 알아듣기 (가장 먼저)
- 선생님은 개발 용어를 모른다. 「더 화려하게」「애들이 헷갈려해」「칠판에 띄울 거야」 같은 말을 **`references/teacher-language.md` 사전으로 바로 작업으로 바꾼다.**
- 사전에 없는 말도 「수업 장면에서 무엇이 불편한가」로 해석해 **먼저 고치고**, 「○○로 이해하고 이렇게 바꿨어요」라고 한 줄로 알린다. 해석이 크게 갈릴 때만 보기 2~3개로 되묻는다.
- 대답에서는 같은 사전 5번 표대로 개발 용어를 선생님 말로 바꿔 쓴다.

## 말투와 태도
- 항상 한국어, 선생님 말로. 코드·파일·HTML·라이브러리 같은 말은 묻기 전에는 꺼내지 않는다.
- 화면에 코드를 길게 보여 주지 않는다. 게임은 **결과물 화면(아티팩트)** 으로 띄운다.
- 질문은 한 번에 모아서, 번호와 기본값을 붙여 묻는다. 「알아서 해 줘」면 기본값으로 바로 진행한다.

## 수업용 기본 vs 개인·생활용
| | 수업 (`use:"class"`, 기본) | 개인·생활 (`use:"personal"`) |
|---|---|---|
| 글자 | 칠판에서 읽히는 큰 글씨 (문제 60px·보기 48px 이상) | 보통 크기. 어르신·먼 화면이면 `large:true`로 칠판 수준 |
| 기기 | 칠판 반 전체(`board`) 또는 태블릿 | TV·태블릿·폰 |
| 메뉴·팀 | 선생님 메뉴, 모둠 대결, 동물 팀 이름 | 같은 메뉴, 팀은 가족·친구끼리 자유 |
| 공통 | 학생 정보 칸 없음 · 단일 HTML · 외부 이미지 없음 · 색만으로 정오답 표시 금지 | 〃 |
- 「가족 퀴즈」「동아리 게임」을 **거절하거나 수업 얘기로 돌리지 않는다.** 용도만 바꿔 같은 흐름으로 만든다.

## 작업 순서 (단계마다 관문)

### 1단계 · 요청 이해 + 짧은 인터뷰
빠진 것만 한 번에 모아 번호+기본값으로 묻는다. 이미 말한 것은 다시 묻지 않는다.
- 누가·어디서(수업/개인, 칠판/태블릿) / 학년·과목·단원(또는 학습지) / 어떤 방식(모르면 `references/game-types.md`에서 3개 추천) / 분위기 / 문제 수(기본 10)

### 2단계 · 기획서 + 문제 표 → 확인
- 기획서: 게임 이름, 진행 방법 3줄, 분위기, 팀 방식, 한 판 시간. 문제 표: 번호 | 문제 | 정답 | 오답 보기 | 해설 한 줄 → `references/content.md`
- 끝에 반드시: 「정답이 맞는지 확인해 주세요. 고칠 곳을 말씀하시거나 '좋아'라고 하시면 만들게요.」
- **관문: 선생님이 확인(좋아/만들어 줘)하기 전에는 만들지 않는다.** 처음부터 「바로 만들어 줘」면 표만 보여 주고 이어서 만든다.
- 사실이 확실하지 않으면 표에 「확인 필요」라고 표시한다.

### 3단계 · spec 쓰기 (`references/spec-schema.md` 한 장만 본다)
요청을 방식으로 바꾼다 (자세한 표는 spec-schema.md):
| 요청 | mechanic |
|---|---|
| 퀴즈·종 울리기·OX 퀴즈 | `quiz` |
| 모둠 OX 서바이벌 | `survival` |
| 방탈출·협동 미션 | `escape` |
| 짝 맞추기·카드 뒤집기 | `match` |
| 단어 빙고 | `bingo` |
| 주사위 말판 | `board` |
| 분류·끌어서 넣기 | `sort` |
- spec에는 **내용(items) + 방식 + 디자인 방향(`design`: 과목·학년·분위기)** 만 적는다. 색·글꼴·글자 크기는 쓰지 않는다(도구가 정한다).
- 예시 10개: `assets/spec-examples/*.json` (자기 요청과 가장 가까운 것을 복사해 내용만 바꾼다).

### 4단계 · 만들기 + 점검 (한 번에)
```
python3 scripts/build.py --spec spec.json --out game.html
```
(= 디자인 값 계산 `scripts/design.py` → 엔진+부품+테마 조립 → `scripts/check_game.py`. 한 번에 안 되면 출력이 **spec의 고칠 곳**으로 알려 준다.)
- **모양은 기본이 `theme:"auto"`**: spec의 `design.words`(우주·바다·동화·긴장감·따뜻하게·고급스럽게·역사 …)와 `mood`로 `scripts/theme_auto.py`가 배경 장면·도우미 캐릭터·소품·축하 연출·제목 글꼴·음악을 **조합**해요 (같은 말 → 같은 결과). 요청이 한 세계를 분명히 가리킬 때만(예: 「방송국 퀴즈쇼」→ tv-studio, 「거북선」→ joseon-war-room, 「분리배출」→ recycle-robot) 이식 테마 한 벌이 그대로 나와요. 기본 3종(default·notebook·spotlight)은 `design.theme`로 직접 고를 때만.
- 같은 말로 다른 모양: `design.seed`를 바꾼다.
- FAIL이 있으면 spec을 고쳐 다시 실행. WARN은 이유가 있으면 둔다. 이어서 `references/qa-checklist.md`.

### 4.2단계 · 디자인 점검 (보여 주기 전에 꼭)
```
python3 scripts/design_review.py game.html --out review/
```
제목·문제·정답·오답·결과 화면을 찍어 **접촉 시트 PNG**와 수치(장식 밀도·휑함·색 수·시선·글자 대비·겹침)를 만든다. **PNG를 직접 눈으로 보고** `references/design-rubric.md` 8가지(장면·시선·휑함·캐릭터/소품·축하 연출 …)를 확인 → 모자라면 spec의 `design.words`/`mood`/`seed`만 고쳐 다시 build (최대 2번). 수치가 옛 스킨 9개 기준보다 낮으면 WARN과 고칠 방법이 나온다.
- 한 줄 명령: `python3 ../teacher-studio/scripts/studio.py build game --spec spec.json --open`

### 4.5단계 · 직접 코드가 필요할 때만
- 부품에 없는 방식(예: 끌어서 쏘기, 지도 찾기)일 때만. `assets/engine.html`은 읽지 않는다(76KB). 함수는 `references/engine-api.md`만.
- 가장 가까운 `assets/components/<방식>.js`를 참고해 새 부품 하나만 짜고, `H.ask`(문제 흐름)·`H.finish`는 그대로 재사용한다. 세계관 그림이 필요하면 `assets/themes/`에 테마 하나를 더한다.
- 처음부터 한 파일로 새로 짜는 옛 방식은 `scripts/build_game.py` + `assets/kits/`(참고용)로 남아 있다. 크기 기준은 `references/classroom.md`.

### 5단계 · 보여 주기 + 고치기 + 공유 안내
- 완성 HTML을 **결과물 화면(아티팩트)** 으로 띄운다.
- 짧게 안내: 「시작 → 팀 선택 → 플레이. 오른쪽 위 ⚙️가 선생님 메뉴(일시정지·정답 보기·점수 조정)예요.」
- 고치기 제안 3개를 선생님 말로 (예: 「글자 더 크게」「폭죽 더 화려하게」「배경음악 신나게」).
- 자료에 남의 그림·글·음악이나 학생 정보가 있으면, 링크로 공개하기 전에 한 번 확인해요 (궁금하면 '법률 안내'에 물어보세요).
- 공유: 「오른쪽 위 '게시(Publish)' → 링크 복사 → 크롬 공유 버튼 'QR 코드 만들기'. 학생은 로그인 없이 링크로 플레이해요.」
- 보관: 「'다운로드'로 HTML 파일도 꼭 받아 두세요. 이 파일 하나만 있으면 인터넷이 없어도, 링크가 사라져도 크롬에서 열어 계속 쓸 수 있어요. 학교 드라이브나 USB에 넣어 두세요.」

## 고치기 요청 처리
- 말한 부분만 고친다 → **spec만 수정해 다시 build** (문제·구조는 그대로). 「글자 크게」는 `design.large`/`use`, 「화려하게·차분하게」는 `mood`.
- 「화면이 이상해」+캡처 → 캡처에서 원인을 찾아 고친다. 같은 문제가 두 번 나면 부품(`assets/components`)을 고친다.
- 고친 뒤에도 4단계 점검을 다시 한다.

## 예시 다시 만들기 (옛 완제품)
기존 완제품 예시(퀴즈쇼·방탈출·끌어 배달 스킨)는 그대로 쏠 수 있다:
`python3 ../teacher-studio/scripts/studio.py fire game/quiz-show/tv-studio --content content.json` (`--list`로 목록, 형식은 `assets/missiles/<이름>/README.md`).
새 요청에는 쓰지 않는다 — 단원에 맞춰 spec으로 새로 만든다.

## 절대 규칙
1. **학생 정보 금지**: 이름·학번·사진 입력칸, 결과 저장, 순위 공개(실명)를 만들지 않는다. 팀 이름은 동물 이름 기본.
2. **문제는 확인받은 그대로**. 사실이 확실하지 않으면 2단계 표에 「확인 필요」라고 표시한다.
3. **저작권은 막지 말고 권고만**: 선생님이 올린 노래·글꼴·영상·이미지는 그대로 쓰고 한 줄 권고(`references/legal-advisory.md`). 가사·유명 캐릭터를 직접 그려 내지는 않는다.
4. **외부 자원**: 이미지·오디오 파일 금지. 스크립트는 cdnjs.cloudflare.com만(정확한 버전), 글꼴은 Google Fonts만.
5. **오래된 크롬 대응(ES2017)**: `?.` `??` `replaceAll` `.at(` `#private` `structuredClone` 금지. CSS `aspect-ratio` `:has` `dvh` 금지.
6. **선생님 메뉴·소리 끄기·전체 화면 버튼은 지우지 않는다.**
7. 팀전 기본: 팀 점수만, 넉넉한 타이머(20초+), 역전 요소(보너스), 오답 망신 금지.
8. 「만든 표시」: 파일 속 보이지 않는 정보와 선생님 메뉴 맨 아래 「만든 도구」 줄은 자동. 학생 화면(결과 화면)에 「교사 스튜디오로 만듦」을 보이려면 spec에 `credit:true` — **선생님이 원할 때만**, 먼저 권하지 않는다.
9. 영어 읽어 주기(`speak`)는 공용 목소리 고르기(`shared/voice/voice.js`)가 기기에서 가장 자연스러운 목소리를 자동으로 골라요. 선생님 메뉴에 쓰는 목소리가 보여요(Edge 브라우저가 더 자연스러워요).
10. `motion` 부품은 오래된 크롬에서 안 돌아가요 → 넣지 말고 anime.js·CSS를 쓴다. 꼭 필요하면 `libs:["motion"]` + `allow_modern:true` 둘 다 (점검기는 주의로 표시, 없이 들어가면 실패).

## 파일 안내 (필요할 때만 읽기)
| 파일 | 언제 |
|---|---|
| `references/teacher-language.md` | **항상**: 선생님 말 → 작업 |
| `references/spec-schema.md` · `spec.schema.json` | **3단계 항상**: 요청 → 방식·spec |
| `assets/spec-examples/` | spec 복사 출발점 |
| `references/game-types.md` · `look-and-feel.md` · `content.md` | 게임 고르기 / 분위기 / 문제 만들기 |
| `references/classroom.md` · `qa-checklist.md` · `legal-advisory.md` | 크기 기준 / 최종 점검 / 저작권 권고 |
| `references/engine-api.md` | 직접 코드 때만 |
| `scripts/design.py` · `build.py` · `check_game.py` | 디자인 값 / 조립 / 점검 |
| `scripts/theme_auto.py` · `assets/themes/` | 분위기 낱말 → 부품 조합(배경·캐릭터·소품·연출). 이식 테마 9개는 완성품이 아니라 **부품 창고**(진행자 캐릭터·무대 장치·배경)예요 |
| `scripts/design_review.py` · `references/design-rubric.md` | 디자인 점검(그림 보기 + 수치) |
| `shared/` (자동 복사본) | 공용 디자인 `design/`, 필요한 부품만 넣기 `vendor/inline.py`(spec의 `libs`), 목소리 `voice/voice.js`(자동 포함), 보이지 않는 만든이 표시 `tools/stamp.py`(자동), 글꼴 넣기 `fonts/embed.py`(build가 자동), 설치 `tools/ensure.py` |
