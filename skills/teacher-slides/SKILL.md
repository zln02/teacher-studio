---
name: teacher-slides
description: Makes keynote-quality web slide decks for lessons, teacher training, parent meetings or personal talks (builds, quiz reveal, notes, PDF, MP4). Use for any PPT, slide or presentation request.
license: Apache-2.0
---

# 교사 스튜디오 · 슬라이드

선생님(코딩 모름)이 말로 원하는 **수업 PPT·발표 자료·연수 자료**를 1920×1080 무대 위 단일 HTML 슬라이드로 만든다.
키노트급 글자 위계·등장 연출·리모컨 조작은 무대(`assets/stage.html`)와 미사일(완제품)이 책임진다. **맞는 미사일이 있으면 무조건 미사일로 쏜다.**

## 선생님 말 알아듣기 (가장 먼저)
- 선생님은 개발 용어를 모른다. 「PPT 만들어 줘」「칠판에 띄울 거」「글씨 더 크게」 같은 말을 **`references/teacher-language.md` 사전으로 바로 작업으로 바꾼다.**
- 사전에 없는 말도 「교실 화면에서 무엇이 불편한가」로 해석해 **먼저 고치고**, 「○○로 이해하고 이렇게 바꿨어요」라고 한 줄로 알린다. 크게 갈릴 때만 보기 2~3개로 되묻는다.
- **「PPT 파일로 줘」「.pptx로」「파워포인트에서 고칠 거야」처럼 파일 자체가 필요할 때**는 다른 모듈(📋 teacher-pptx, 아직 없음)이다. 지금은 「웹 슬라이드로 만들고, 크롬 인쇄 → PDF로 저장하면 한 장씩 가로 PDF가 돼요」라고 안내하고 웹 슬라이드를 만든다.

## 선생님 말 → 미사일
| 선생님 말 | 미사일 · 스킨 |
|---|---|
| 「수업 PPT 만들어 줘」「수업 자료 슬라이드」「이 단원 정리 화면」 | `lesson-deck` · 과목 분위기로 (과학·수학 → chalkboard) |
| 「칠판에 띄울 슬라이드」「전자칠판에 띄울 거」「판서 대신」 | `lesson-deck` · **chalkboard** |
| 「발표 자료」「연수 자료」「교원 연수 PPT」「애플처럼 깔끔하게」「세련되게」 | `lesson-deck` · **clean-keynote** |
| 「학부모 설명회」「가정통신 대신 보여 줄 거」「입학 설명회」「귀엽게」「부드럽게」 | `lesson-deck` · **notebook-pastel** |
| 「퀴즈도 몇 장 넣어 줘」「정답은 클릭하면 나오게」 | `lesson-deck` · `quiz` 장 추가 |
| 「한 줄씩 나오게」「하나씩 클릭하면 나오게」 | `lesson-deck` · cards/steps/compare/timeline 기본 동작 |
| 「내가 할 말 메모해 둬」「대본도 넣어 줘」 | 각 장 `note` (N키로만 보임) |
| 「인쇄해서 나눠 줄래」「PDF로」 | 같은 슬라이드 → 크롬 인쇄 → PDF로 저장 안내 |
| 「영상으로 만들어 줘」「자동으로 넘어가게」 | `lesson-deck` + `"reel": true` → MP4 (또는 🎥 버튼) |
| 「PPT 파일로」「.pptx로 줘」 | 📋 teacher-pptx (아직 없음) → 웹 슬라이드 + PDF로 대안 |
| 「도입 영상」「카운트다운」 | 이 스킬 아님 → teacher-motion |
| 「퀴즈 게임」「종 울리기」 | 이 스킬 아님 → teacher-game |

## 말투와 태도
- 항상 한국어, 선생님 말로. 코드·HTML·파일 구조는 묻기 전에는 꺼내지 않는다. 결과는 **결과물 화면(아티팩트)** 으로 띄운다.
- 질문은 한 번에 모아 번호+기본값으로. 「알아서 해 줘」면 기본값으로 바로 진행한다.

## 작업 순서
### 1단계 · 빠진 것만 묻기
한 번에 모아서: ① 누구 앞(학생 몇 학년 / 교사 연수 / 학부모) ② 주제·단원(학습지·PDF 있으면 그걸로) ③ 분량(기본 10장) ④ 분위기(기본: 학생 → chalkboard, 교사 → clean-keynote, 학부모 → notebook-pastel) ⑤ 날짜·발표자 표시(기본: 학교 이름 + 날짜만).

### 2단계 · 구성표 → 선생님 확인
- 표 한 장: 번호 | 장 종류(표지·질문·카드·비교·단계·숫자·퀴즈·마무리…) | 화면 글 | 선생님 메모.
- 한 장에 한 메시지. 글은 짧게(제목 20자, 카드 문장 30자 안팎). 사실이 확실하지 않으면 「확인 필요」 표시.
- 끝에: 「내용이 맞는지 봐 주세요. 고칠 곳을 말씀하시거나 '좋아'라고 하시면 만들게요.」 **확인 전에는 만들지 않는다** (처음부터 「바로 만들어 줘」면 표만 보여 주고 이어서 만든다).

### 3단계 · 미사일 발사
```
python3 scripts/build_stage.py --list
python3 scripts/build_stage.py --missile lesson-deck --skin <스킨> --content content.json --out deck.html
```
| 미사일 | 스킨 | 맞는 요청 |
|---|---|---|
| `lesson-deck` | chalkboard · clean-keynote · notebook-pastel | 수업 PPT, 발표·연수 자료, 칠판 슬라이드, 설명회 |
- `content.json`에는 바뀌는 것만(`title`, `items`, 필요하면 `world.labels`·`vars`). 형식은 `assets/missiles/lesson-deck/README.md` **그 파일 하나만** 읽는다.
- 13가지 장(cover section question bigtext cards compare steps bignumber quote timeline quiz image end)을 섞어 쓴다. 같은 장 종류를 3번 연속 쓰지 않는다.
- 학교 색이 있으면 `vars`(primary, accent …)만 바꾼다. 스킨 CSS는 건드리지 않는다.

### 4단계 · 점검 (통과할 때까지)
```
python3 scripts/check_page.py deck.html
```
FAIL이 있으면 고친다. 가능하면 브라우저로 전 장을 넘기며(→ 키) 캡처를 눈으로 본다: 글자 잘림·겹침·너무 작은 글씨(본문 28px 미만)·대비.

### 5단계 · 보여 주기 + 고치기 + 공유/보관/영상 저장
- 결과물 화면으로 띄우고 짧게 안내: 「→·스페이스·리모컨으로 넘겨요. 화면 오른쪽을 누르면 다음, 왼쪽은 뒤로. N은 내 메모, B는 화면 끄기, 숫자 누르고 Enter는 그 장으로.」
- 고치기 제안 3개를 선생님 말로 (예: 「글자 더 크게」「퀴즈 한 장 더」「학교 색으로」).
- 자료에 남의 그림·글·음악이나 학생 정보가 있으면, 링크로 공개하기 전에 한 번 확인해요 (궁금하면 '법률 안내'에 물어보세요).
- 공유: 「오른쪽 위 '게시' → 링크 복사. 다른 선생님은 로그인 없이 링크로 볼 수 있어요.」
- 보관: 「'다운로드'로 파일도 받아 두세요. 인터넷이 없어도 크롬에서 열려요(USB·학교 드라이브).」
- 인쇄·PDF: 「크롬에서 Ctrl+P → 대상 'PDF로 저장' → '배경 그래픽' 켜기. 한 장이 가로 한 쪽, 정답까지 다 보인 상태로 나와요.」
- 영상: 「오른쪽 위 🎥 → '이 탭' 공유 → 전 장이 자동으로 넘어가며 녹화돼요(webm).」 MP4가 필요하면 `"reel": true`로 따로 만들어 `scripts/render_mp4.py`.

## 고치기 요청 처리
- 말한 장만 고친다. 나머지 장·순서·메모는 그대로. 고친 뒤 4단계 점검을 다시 한다.
- 「글씨가 작아」 → 그 장 글을 줄이거나 두 장으로 나눈다(자동 맞춤이 줄여 놓은 것이므로). 「한꺼번에 나오게」 → 그 장 `"build": false`.

## 미사일이 없을 때만 직접 제작 (STAGE)
`assets/stage.html`은 다시 타이핑하지 않는다. `doc.json` + `show.js` (+ `extra.css`)만 쓰고 `build_stage.py --data doc.json --show show.js --css extra.css --out page.html`.
- `window.SHOW = {start(), onKey?(e) → 처리했으면 true, toText?()}`. 모든 글은 `DOC`에서 읽는다.
- `STAGE.h(tag, attrs, html)` 요소 · `STAGE.esc` · `STAGE.split(el, "word"|"char")` 낱말 단위로 쪼개기(한국어 낱말 유지) · `STAGE.fitText(el, max, min)` 상자에 맞게 글자 줄이기 · `STAGE.setVars` · `STAGE.bg(fn(ctx, t, W, H))` 배경 그리기(t에만 의존) · `STAGE.timeline(tl, ms)` 등록(→ `__stage.seek`·영상 저장) · `STAGE.toast` · `STAGE.el.scene/stage`.
- 움직임은 anime.js 4.5.0 (`anime.createTimeline({autoplay:false}).add(el, {opacity:[0,1]}, 위치)`, `anime.stagger`, ease `outExpo`·`outBack(1.7)`). setTimeout으로 연출하지 않는다. 시작 전 상태는 `anime.utils.set`으로 먼저 깔아 둔다(타임라인은 시작 전 값을 미리 그리지 않음). 같은 요소를 새 타임라인이 다시 움직이면 이전 타임라인은 `revert()`.
- 1920×1080, 안전 여백 96px 이상, 제목 120~260px, 본문 28px 이상, `word-break:keep-all`.

## 절대 규칙
1. **학생 정보 금지**: 학생 이름·사진·성적·학번을 화면에 넣지 않는다. 예시 이름은 가상(모둠1, 학생A).
2. **사실 확인**: 교과 내용·통계·날짜가 확실하지 않으면 구성표에 「확인 필요」. 숫자 장(bignumber)은 출처를 선생님 메모에 적는다.
3. **저작권은 막지 말고 권고만**: 선생님 이미지·글꼴·인용은 넣고 한 줄 권고(`references/legal-advisory.md`). 실존 인물 인용은 선생님이 준 문장만 쓴다.
4. **외부 자원 금지**: 그림 파일·외부 이미지 없이 내장 아이콘(SVG)·이모지·도형으로. 글꼴은 파일에 넣은 Noto Sans/Serif KR(build가 자동)과 Google Fonts. 없어도 동작하게.
5. **오래된 크롬 대응**: `?.` `??` `replaceAll` `.at(` `#private` `structuredClone` 금지. CSS `aspect-ratio` `:has` `dvh` 금지.
6. 전체 화면·🎥 버튼·선생님 메모(N)는 지우지 않는다. 메모는 기본으로 숨긴다.

## 파일 안내 (필요할 때만 읽기)
| 파일 | 언제 |
|---|---|
| `references/teacher-language.md` | **항상**: 선생님 말 → 작업, 개발 용어 → 선생님 말 |
| `assets/missiles/lesson-deck/README.md` | **제작 때 항상**: 장 종류·키·스킨·조작 (show.js 대신) |
| `assets/missiles/lesson-deck/skins/*.json` | 스킨별 완성 예시(칠판 과학 수업 / 교원 연수 / 학부모 설명회) |
| `references/legal-advisory.md` | 글꼴·이미지·인용 권고 문장 |
| `scripts/build_stage.py` · `check_page.py` · `render_mp4.py` | 조립 / 자동 점검 / MP4 |
| `shared/` (자동 복사본) | 디자인 `design/design.py --use present --mood 고급스럽게`로 색·글꼴 정하기, 부품 `vendor/inline.py`(`build_stage.py --libs chartjs,katex,lucide`), 글꼴 넣기(build가 자동, `--no-fonts`로 끔), 설치 `tools/ensure.py`. 더 화려한 움직임이 꼭 필요하면 GSAP을 공식 CDN에서 보는 순간 불러오는 길만 (저장소에 없음, 기본은 anime.js·CSS. Motion은 2020년 이전 크롬에서 안 돌아가서 `--allow-modern`을 줄 때만 들어가요) |
| 「만든 표시」 | 파일 속 보이지 않는 정보로 `교사 스튜디오 · 박진영`이 자동으로 들어가요(화면에는 안 보임). **선생님이 원할 때만** `build_stage.py --credit`으로 마지막 화면에 작게 「교사 스튜디오로 만듦」을 넣어요 (기본은 끔, 먼저 권하지 않아요) |
