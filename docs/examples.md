# 💬 실제로 이렇게 만들었어요 — 요청 → 결과 기록

README의 「이렇게 말하면, 이렇게 나와요」에 나온 5개 예시를 **누구나 그대로 다시 만들어 볼 수 있게** 적어 둔 기록입니다.
선생님이 한 줄로 말한 요청 → AI가 스킬을 읽고 알맞은 도구에 내용만 채움 → 점검기(`check`) 통과 → 그 화면을 그대로 녹화한 것이 GIF예요.
(GIF는 결과의 일부를 잘라 보여 드리는 것이고, 실제 결과는 HTML 파일 한 개입니다. 만든 HTML은 저장소에 두지 않아요. 아래 명령으로 언제든 다시 만들 수 있어요.)

| # | 선생님 요청 (그대로) | 쓴 도구와 디자인 | 내용 파일 | 결과 GIF |
|---|---|---|---|---|
| 1 | 5학년 과학 태양계 퀴즈쇼 만들어 줘 | 퀴즈쇼 · 우주 정거장 | [`examples/quiz-solar-system.json`](examples/quiz-solar-system.json) | `gallery/ex-quiz-solar-system.gif` |
| 2 | 3학년 분리배출 게임 만들어 줘, 태블릿으로 | 끌어서 보내기 · 분리수거 로봇 | [`examples/drag-recycle.json`](examples/drag-recycle.json) | `gallery/ex-drag-recycle.gif` |
| 3 | 6학년 과학 광합성 수업 슬라이드 만들어 줘 | 수업 슬라이드 · 칠판 | [`examples/slides-photosynthesis.json`](examples/slides-photosynthesis.json) | `gallery/ex-slides-photosynthesis.gif` |
| 4 | 1학년 영어 과목 소개 영상 만들어 줘, 뉴스처럼 | 과목 소개 영상 · 영어 뉴스 | [`examples/intro-english.json`](examples/intro-english.json) | `gallery/ex-intro-english.gif` |
| 5 | 수업 시작할 때 띄울 화면 만들어 줘, 오늘은 분수의 덧셈 | 수업 시작 화면 · 종이 | [`examples/opening-fractions.json`](examples/opening-fractions.json) | `gallery/ex-opening-fractions.gif` |

## 만든 방법 (다시 만들어 보기)

```bash
# 1) 내용 파일을 도구에 채워 넣기 → 점검기(check)가 자동으로 돌고 PASS가 나와야 해요
python skills/teacher-studio/scripts/studio.py fire game/quiz-show/space-quiz        --content docs/examples/quiz-solar-system.json    --out out/quiz.html
python skills/teacher-studio/scripts/studio.py fire game/drag-deliver/recycle        --content docs/examples/drag-recycle.json         --out out/drag.html
python skills/teacher-studio/scripts/studio.py fire slides/lesson-deck/chalkboard    --content docs/examples/slides-photosynthesis.json --out out/slides.html
python skills/teacher-studio/scripts/studio.py fire motion/subject-intro/english-news --content docs/examples/intro-english.json       --out out/intro.html
python skills/teacher-studio/scripts/studio.py fire motion/lesson-opening/calm-paper  --content docs/examples/opening-fractions.json   --out out/opening.html
```

모든 예시는 `RESULT: PASS (0 fail, 0 warn)` 이었어요. (`/out/`은 저장소가 무시하는 폴더입니다.)

## GIF 만든 방법
`tools/capture_example.py`가 설치된 크롬을 띄워 화면을 녹화해요 (Playwright + Pillow 필요, 추가 다운로드 없음).

```bash
# 영상·화면: 정확한 시점으로 프레임을 찍음 (앞뒤 장면만 골라 이어 붙임)
python tools/capture_example.py motion out/opening.html docs/gallery/ex-opening-fractions.gif --start 0 --end 11.5 --fps 7
python tools/capture_example.py motion out/intro.html   docs/gallery/ex-intro-english.gif --segments "3-4.5,8-9,14-15,19-20.5,29-30,37-38,41.5-43" --fps 6 --colors 32
# 슬라이드: 키를 눌러 넘기며 실시간 녹화
python tools/capture_example.py slides out/slides.html  docs/gallery/ex-slides-photosynthesis.gif --keys "Space*19@650,Space*1@1500" --colors 32
# 게임: 프로그램이 학생처럼 직접 풀며 녹화 (정답은 같은 내용 파일에서 찾아 누름. 처음 몇 문제 + 마지막 장면만 녹화)
python tools/capture_example.py play out/quiz.html docs/gallery/ex-quiz-solar-system.gif --script quiz --content docs/examples/quiz-solar-system.json --rec 1 --width 560
python tools/capture_example.py play out/drag.html docs/gallery/ex-drag-recycle.gif     --script drag --content docs/examples/drag-recycle.json --rec 2 --width 576
```

## 솔직하게 알려 드려요
- GIF는 용량 때문에 **앞부분·핵심 장면만** 잘랐어요 (영상은 약 44초 중 하이라이트, 슬라이드는 8장 중 일부 단계, 게임은 처음 몇 문제와 마지막 장면). 중간은 같은 방식으로 이어져요.
- 퀴즈쇼 요청에 「2팀」「20초」, 분리배출에 「4개 통」 같은 세부 값은 AI가 학년·상황에 맞게 정한 기본값이에요. 선생님이 바꿔 말하면 그대로 바뀌어요.
- 문제·설명 내용은 AI가 쓴 초안이에요. 수업에 쓰기 전에 선생님이 한 번 확인해 주세요.
