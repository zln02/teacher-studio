# Studio details (moved out of SKILL.md; read only the part you need)

## A. Ready card (show once, only if the user has made no request yet)
```
🎉 교사 스튜디오 준비 상태
· 지금 쓰는 곳: …            · 결과 보기: …
· 영상: …                    · 나누기: …
· 법률 안내: …

무엇을 만들까요? 번호나 말로 편하게 말씀해 주세요.
1. 🎮 게임 — 퀴즈쇼·종 울리기 / 방탈출 / 끌어서 보내기(단어·분류)
2. 🖥 슬라이드 — 칠판 / 깔끔한 발표 / 파스텔 노트
3. ✨ 소개 영상 — 첫 시간에 틀 30~40초 영상
4. ⏱ 시작 화면 — 카운트다운 + 오늘의 주제
5. 🧰 도구 — 타이머 · 뽑기 · 모둠 · 대진표 · 점수판
6. 📊 자료 분석 — 엑셀·설문·점수를 쉬운 그래프로
7. 🧭 같이 기획 — 유튜브 채널·행사·수업 계획·학부모 모임, 조사·분석
8. ⚖️ 법률 안내 — 「이거 써도 돼요?」를 최신 법으로 확인
9. 💬 그냥 말로 할게요 (예: 「중2 과학 빛과 파동 방탈출, 칠판용」)
참고할 사진·영상·학습지가 있으면 같이 올려 주세요. 그 느낌으로 만들어요.
학생 이름·성적·상담 내용은 채팅에 붙여 넣지 마세요 (가명으로 바꿔 주세요).
```
- Use the current doctor summary. Confirm the active host’s preview, sharing and search features separately. Show the menu as available choices, and mention the specific unavailable feature if it affects the request.
- A number only: ask what is missing for that row, inside the single direction round.

## B. Capabilities in the current conversation
| What to confirm | How to describe it |
|---|---|
| File write | 파일을 저장할 수 있는 작업 폴더 / 이 위치에는 저장할 수 없어요 |
| Runtime | 화면을 열어 작동을 확인할 수 있어요 / 실제 작동은 아직 확인하지 못했어요 |
| Preview and sharing | 대화에서 미리 보기·공유가 확인됐을 때 그 방법을 안내한다. 파일을 저장했다면 여는 방법을 알려 준다 |
| Official sources | 대화의 검색 또는 공식 페이지 읽기가 실제로 가능한 경우만 확인했다고 한다 |
| MP4 | 영상 도구가 실제로 동작하면 MP4로 받는다. 화면에서 녹화할 수 있으면 그 방법을 안내한다 |

## C. Cannot do -> instead (never end at 「안 돼요」)
| 원하는 것 | 지금은 | 대신 이렇게 |
|---|---|---|
| 사람 같은 AI 목소리 | 내장 안 됨 | 컴퓨터 기본 읽어 주기(Web Speech)는 됨. 사람 같은 목소리는 외부 서비스를 선생님이 골라야 함 |
| 실제 사람(연예인·동료·학생) 목소리·얼굴 흉내 | 만들지 않음 | 비슷한 분위기의 오리지널 캐릭터. 궁금하면 `teacher-law` |
| AI 그림·사진 만들기 | 안 들어 있음 | 내장 아이콘·도형, 무료 그림 팩, 선생님 사진 |
| 로그인 필요한 일(나이스·SNS 올리기) | 대신 로그인·업로드 안 함 | 파일을 만들고 올리는 순서를 안내 |
| 영상 편집(자르기·자막) | 앱·웹에선 안 됨 | 🎥 녹화(.webm)는 됨. 자르기·자막·MP4는 현재 쓸 수 있는 영상 도구를 확인 |
| PPT·워드·엑셀·PDF **파일** | 이 대화에서 쓸 수 있는 문서 도구를 확인 | 파일은 그쪽에 맡기고 디자인·구성·점검을 얹음. 대화에 표시된 도구 목록에서 확인 |
- 「더 화려하게」 (GSAP): default is Motion, anime.js, CSS. GSAP only if truly needed, loaded from the official CDN at view time (its own terms, internet needed, not bundled).
- Shared toolbox (`shared/`): `design.py --use present|poster|invite|print|web`, colour tools (`color_from.py`, `color_check.py`, `oklch.py`), parts (`inline.py`), fonts (`embed.py`), install (`ensure.py`).

## D. Fast path after a request is clear
- Read the skill's SKILL.md (short) -> the one missile README -> write only the changing parts in `content.json` -> `studio.py fire ... --content content.json [--open] [--mp4]` -> show the file and its actual status (`READY` or `PARTIAL`). Never read engine.html / stage.html.
- Pick a skin by subject, mood, grade; no skin fits -> nearest skin + `vars` (colours) + `world` text.
- Reference photo/video: pull 3-4 colours, type feel, layout density, pace; say it in one line; adjust. Never reuse their logos or art. 「이 사이트처럼」 + URL/screenshot -> `learn-from-reference.md` (`ref_analyze.py`).
- The user's template, logo, PPT/POTX/Word/HWPX/CSS colours come first (`user-colors.md`, `color_from.py` -> spec `design.palette_from`).
- After building: 1 line what, 1 line how, 2 tweaks. No dev terms.

## E. Inside an agent's security box (Codex and others): work folder and `NO-BROWSER`
- **Work folder.** Scripts never need the system temp folder. Intermediate files go, in this order, to `$TEACHER_STUDIO_TMP`, `<output folder>/.teacher-studio-work/`, `<current folder>/.teacher-studio-work/`, the system temp folder, `~/.teacher-studio/tmp`; the first that accepts a file is used and the folder is removed afterwards (`shared/tools/workdir.py`). Write your own spec files in the current working folder too.
- **`NO-BROWSER`.** The box refuses the channel a headless browser needs, so Chrome, Edge and Playwright cannot start whatever you try. A script prints the line once and goes on with the checks that need no browser:
  | making | what still runs | what is skipped | say |
  |---|---|---|---|
  | .pptx | blanks, text fit, shapes inside, empty-looking slides + a rough picture `review/<name>-sketch-sheet.png` (Pillow) | the closer `-approx-sheet.png` | 「밑그림 미리보기로 확인했어요」 |
  | game · class tool · web app · web deck | static checks (offline, old-Chrome syntax, storage, privacy, structure) -> `PARTIAL` | play-through, overflow, contrast on pixels, screenshots | 「화면은 직접 열어 확인하지 못했어요」 |
  | HWPX · Word | everything (no browser needed) | - | - |
  | PDF | nothing: printing needs a browser | the PDF itself | give the `.print.html` and 「Ctrl+P → PDF로 저장」, or run outside the box |
- Do not spend turns on it: no launching a browser with other flags, no installs, no home-made screenshot, DOM-emulation or drawing script. `TEACHER_STUDIO_NO_BROWSER=1` forces this path anywhere (for a test), `=0` forces a real try.
