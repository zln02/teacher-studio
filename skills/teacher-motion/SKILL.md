---
name: teacher-motion
description: Makes keynote-quality motion videos and animated screens (subject intro, lesson-start countdown, personal videos) as one HTML page, exportable to webm/MP4. Use for any video or motion request.
license: Apache-2.0
---

# 교사 스튜디오 · 영상·화면

선생님(코딩 모름)이 말로 원하는 **수업용 영상·움직이는 화면**을 1920×1080 무대 위 단일 HTML로 만들고, 영상 파일(webm/MP4)로도 뽑아 준다.
퀄리티는 무대(`assets/stage.html`)와 미사일(완제품)이 책임진다. **맞는 미사일이 있으면 무조건 미사일로 쏜다.**

## 선생님 말 알아듣기 (가장 먼저)
- 「멋있게」「첫 시간에 보여 줄 거」「애들 집중시키게」 같은 말은 `references/teacher-language.md` 사전으로 바로 작업으로 바꾼다(0번 표가 영상·화면 요청).
- 사전에 없는 말도 「교실에서 언제, 어디에 띄우나」로 해석해 **먼저 만들고**, 「○○로 이해하고 이렇게 만들었어요」라고 한 줄로 알린다. 크게 갈릴 때만 보기 2~3개로 되묻는다.
- 대답에서는 사전 5번 표대로 개발 용어를 선생님 말로 바꿔 쓴다(타임라인 → 장면 순서, 렌더링 → 영상 파일로 만들기).

## 선생님 말 → 미사일
| 선생님 말 (이렇게 말하면) | 미사일 | 기본 스킨 |
|---|---|---|
| 「과목 소개 영상」「첫 시간에 보여 줄 거」「오리엔테이션 영상」「우리 과목 홍보」「새 학기 첫 수업 인트로」「과목 소개 PPT 대신 영상으로」「우리 과목 맛보기 영상」 | `subject-intro` | 과학·기술·수학 → science-neon / 국어·한문·역사·도덕 → korean-brush / 영어·사회·진로 → english-news |
| 「멋있게, 네온 느낌」「실험실 분위기」「SF 느낌」 | `subject-intro` | science-neon |
| 「붓글씨 느낌」「한국적인」「차분하고 고급스럽게」「수묵화처럼」 | `subject-intro` | korean-brush |
| 「뉴스처럼」「속보처럼」「방송국 느낌」「유튜브 채널처럼」 | `subject-intro` | english-news |
| 「수업 시작할 때 띄울 거」「집중시키는 화면」「카운트다운」「종 치고 띄워 둘 거」「오늘 배울 거 보여 주는 화면」「학습 목표 띄우기」「수업 오프닝」 | `lesson-opening` | bold-pop |
| 「1교시라 차분하게」「조용히 집중」「아침 분위기」「저학년처럼 부드럽게」 | `lesson-opening` | calm-paper |
| 「신나게」「확 깨우게」「점심 먹고 졸릴 때」 | `lesson-opening` | bold-pop |

📋 **아직 미사일이 없는 요청** → 아래 「미사일이 없을 때 직접 제작」으로 STAGE에서 바로 만든다(같은 품질 기준).
| 선생님 말 | 나중 미사일(준비 중) |
|---|---|
| 「다음 단원 예고편」「다음 시간 예고」 | 📋 단원 예고편 |
| 「체육대회·축제·졸업식 오프닝」「행사 시작 영상」 | 📋 행사 오프닝 |
| 「통계 숫자 보여 주는 영상」「설문 결과를 움직이게」 | 📋 숫자 인포그래픽 |
| 「글자만 나오는 영상」「명언·시 한 편 띄우기」「가사처럼 글자 영상」 | 📋 글자 영상 |
| 「사진으로 슬라이드쇼」「추억 영상」「활동 사진 모음」 | 📋 사진 슬라이드쇼 (선생님 사진 파일 필요) |
| 「쇼츠」「세로 영상」「릴스」「학교 인스타용」 | 📋 세로 숏폼 (1080×1920) |

## 말투와 태도
- 항상 한국어, 선생님 말로. HTML·코드·타임라인 같은 말은 묻기 전에는 꺼내지 않는다. 결과는 **결과물 화면(아티팩트)** 으로 띄운다.
- 질문은 한 번에 모아 번호+기본값으로. 「알아서 해 줘」면 기본값으로 바로 진행.

## 작업 순서
### 1단계 · 빠진 것만 묻기
- subject-intro: 과목·학년 / 분위기(스킨) / 「이 과목에서 만날 것」 3~4개 / 선생님 한마디 / 마무리에 넣을 학교·학년·선생님 표기(넣지 않아도 됨)
- lesson-opening: 오늘의 주제 / 목표 한 줄 / 분위기(신나게·차분하게) / 카운트다운 몇 초(기본 5) / 오늘의 순서(선택)
- 선생님이 이미 말한 것은 다시 묻지 않는다. 문구가 없으면 Claude가 초안을 쓰고 2단계에서 확인받는다.

### 2단계 · 구성표 → 선생님 확인
- 장면 순서 표: 번호 | 장면 | 화면에 나올 글자 | 그림(아이콘) | 길이. 예: `1 | 질문 | 세상은 무엇으로…? | 원자 궤도 | 5초`
- 끝에 반드시: 「화면에 나올 글자가 맞는지 확인해 주세요. 고칠 곳을 말씀하시거나 '좋아'라고 하시면 만들게요.」
- **관문: 확인 전에는 만들지 않는다.** 처음부터 「바로 만들어 줘」면 표를 보여 주고 이어서 만든다.

### 3단계 · 미사일 발사
```
python3 scripts/build_stage.py --list
python3 scripts/build_stage.py --missile <미사일> --skin <스킨> --content content.json --out page.html
```
| 미사일 | 스킨 | 길이 | 내용 형식 |
|---|---|---|---|
| `subject-intro` 과목 소개 영상 | science-neon · korean-brush · english-news | 35~45초 | `assets/missiles/subject-intro/README.md` |
| `lesson-opening` 수업 시작 화면 | bold-pop · calm-paper | 10~15초 + 누를 때까지 대기 | `assets/missiles/lesson-opening/README.md` |
- `content.json`에는 바뀌는 것만 쓴다. 형식은 그 미사일 README 하나만 읽는다. show.js·style.css는 고치지 않는다(문구·색·아이콘은 전부 content로 바뀜).

### 4단계 · 점검 (통과할 때까지)
```
python3 scripts/check_page.py page.html
```
- FAIL이 있으면 고치고 다시. 브라우저(Playwright)가 있으면 `window.__stage.manual(); window.__stage.seek(ms)`로 장면마다 캡처해 **눈으로** 겹침·잘림·대비를 본다(1280×720과 1920×1080 둘 다). 시간은 앞에서 뒤로만 넘기며 캡처한다.

### 5단계 · 보여 주기 + 고치기 + 공유/보관/영상 저장
- 완성 HTML을 결과물 화면으로 띄운다. 안내: 「오른쪽 위 ⏯ 재생/멈춤, ↺ 처음부터, ⛶ 전체 화면(F). 수업 시작 화면은 화면을 누르거나 Space로 넘어가요.」
- 고치기 제안 3개(예: 「글씨 더 크게」「분위기 더 차분하게(다른 스킨)」「장면 하나 추가」).
- 자료에 남의 그림·글·음악이나 학생 정보가 있으면, 링크로 공개하기 전에 한 번 확인해요 (궁금하면 '법률 안내'에 물어보세요).
- 공유: 「오른쪽 위 '게시(Publish)' → 링크 복사. 학생·다른 선생님은 로그인 없이 봐요.」
- 보관: 「'다운로드'로 HTML 파일도 받아 두세요. 인터넷이 없어도 크롬에서 열려요(글씨체만 기본 글꼴로 바뀜).」
- **영상 파일로 받기** (유튜브·학교 홈페이지·단톡방용):
  - (가) **어디서나 — 🎥 버튼**: 크롬에서 열고 오른쪽 위 🎥 → 「이 탭」 선택 → 「공유」. 처음부터 끝까지 자동 녹화 후 **.webm 파일이 다운로드 폴더에** 저장돼요. 녹화 중엔 창을 바꾸지 마세요. (.mp4가 꼭 필요하면 무료 변환 사이트·곰인코더 등으로 바꾸기)
  - (나) **Claude가 직접 MP4로 — Playwright와 ffmpeg가 있는 환경에서만**: `python3 scripts/render_mp4.py page.html out.mp4` → 프레임 단위로 정확히 찍어 끊김 없는 30fps MP4(기본 30MB 이하, `--max-mb`로 조절). 끝나면 파일로 전달. 없는 환경이면 (가)로 안내.

## 고치기 요청 처리
- 말한 부분만 고친다(글자 → content.json, 분위기 → 스킨 교체, 색 → `vars`). 다시 4단계 점검.
- 「너무 빨라」→ 장면 수 줄이기(장면당 시간이 늘어남) / 「너무 길어」→ items 3개로 / 「글씨가 안 보여」→ 문구 짧게(자동 확대) 또는 대비 높은 스킨.

## 미사일이 없을 때 직접 제작 (STAGE)
**`assets/stage.html`을 다시 타이핑하지 않는다.** `doc.json` + `show.js`(+`extra.css`)만 쓰고 조립한다:
`python3 scripts/build_stage.py --data doc.json --show show.js --css extra.css --out page.html`
- 무대: 1920×1080 고정 좌표(화면에 자동 맞춤). 안전 여백 96px 이상. `body[data-skin]`, CSS 변수(`DOC.vars` → `--이름`).
- `window.DOC` = 모든 글자(제목·문구·스킨·vars). show.js에 과목 문구를 직접 쓰지 않는다.
- `window.SHOW = {start(), onKey?(e)→처리했으면 true, toText?()}`
- STAGE 함수: `h(tag, attrs, html)` 요소 만들기 · `esc(s)` · `split(el)` 글자 단위(단어는 안 끊김) / `split(el,"word")` 단어 단위 · `fitText(el,max,min)` 상자에 맞게 글씨 줄이기 · `setVars` · `bg(fn(ctx,t,W,H))` 배경 캔버스(매 프레임, **t만으로 결정**) · `timeline(tl, ms)` **모든 움직임 등록**(재생·멈춤·녹화·MP4가 이걸로 동작) · `now()` · `clear()` · `toast()` · `el.scene/stage/bg`
- anime.js 4.5.0 (`window.anime`): `anime.createTimeline({autoplay:true}).add(대상, {속성:[시작,끝], duration, delay: anime.stagger(40), ease:"outExpo"}, 위치ms)`, `anime.svg.createDrawable(path)` + `{draw:["0 0","0 1"]}` 선 그리기, `anime.utils.set()`, ease: outExpo·outBack(1.7)·outElastic(1,.6)·inOutQuad·inOutSine.
- 함정(실제로 겪은 것):
  1. anime는 트윈이 **시작될 때까지 시작값을 칠하지 않는다** → `anime.utils.set(대상, 시작값)`을 먼저(미사일 show.js의 `add()` 도우미 참고). 안 하면 그림·글자가 처음부터 보임.
  2. 한 요소의 같은 속성에 트윈 두 개 금지(뒤로 감기 깨짐) → 들어오기는 바깥 div, 나가기는 안쪽 div.
  3. flex 상자 안에서 `split`하면 단어마다 줄이 바뀜 → 글자는 안쪽 블록(div)에 넣고 split.
  4. 반복(loop) 움직임은 `STAGE.timeline(anim, 1)`로 등록(길이 무한대 방지). setTimeout/setInterval로 연출하지 않는다.
  5. 영상 길이 = `STAGE.timeline(tl, 총ms)`. 웹 글꼴이 늦게 오면 `document.fonts` 'loadingdone'에서 fitText 다시.

## 절대 규칙
1. **학생 정보 금지**: 학생 이름·얼굴·목소리·학번을 넣지 않는다. 선생님 자료에 보이면 「학생 정보가 보여요. 지우고 진행할까요?」 먼저 묻기.
2. **사실 확인**: 과목 소개·목표 문구에 사실 내용이 들어가면 확실한 것만. 애매하면 구성표에 「확인 필요」.
3. **저작권은 막지 말고 권고만**(`references/legal-advisory.md`): 선생님이 올린 음악·사진·글꼴은 그대로 쓰고 한 줄 권고. 유명 캐릭터·로고·방송사 로고는 Claude가 그려 내지 않고 비슷한 분위기의 오리지널로(english-news도 실제 방송사 이름·로고 금지).
4. **외부 자원 금지**: 그림은 SVG·CSS·캔버스 오리지널만, 외부 이미지·영상 링크 금지. 글꼴은 Google Fonts만(없어도 동작).
5. **오래된 크롬 대응**: `?.` `??` `replaceAll` `.at(` `#private` `structuredClone` 금지, CSS `aspect-ratio` `:has` `dvh` 금지.
6. 무대의 ⏯ ↺ 🎥 ⛶ 버튼과 R/F/Space 키는 지우지 않는다. `stage.html`·`vendor/`·`scripts/`는 고치지 않는다.

## 파일 안내 (필요할 때만 읽기)
| 파일 | 언제 |
|---|---|
| `references/teacher-language.md` | **항상**: 선생님 말 → 작업, 개발 용어 → 선생님 말 |
| `assets/missiles/<미사일>/README.md` | 미사일 쏠 때 그것 하나만 |
| `assets/missiles/<미사일>/skins/*.json` | 스킨 기본 문구·색 전체 목록이 필요할 때 |
| `assets/missiles/<미사일>/show.js` | 직접 제작 때 수준 기준점·도우미(add/box/fit) 참고 |
| `references/legal-advisory.md` | 음악·글꼴·사진·초상권 권고 문장 |
| `scripts/build_stage.py` · `scripts/check_page.py` · `scripts/render_mp4.py` | 조립 / 점검 / MP4 |
| `assets/stage.html` | 읽지 않는다(조립 스크립트가 그대로 복사) |
