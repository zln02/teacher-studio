# Studio details (moved out of SKILL.md; read only the part you need)

## A. Ready card (show once, only if the user has made no request yet)
```
🎉 교사 스튜디오 준비 완료!
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
- 「영상」 line: Claude Code/Codex: 「MP4는 처음 요청할 때 작은 도구(약 80MB, 크롬이 있으면 그걸 써요)를 설치해요」; Claude app/web: 「크롬 녹화(.webm)로 받아요」. 「법률」 line: Codex with internet off or cached search: add how to turn it on (`network_access = true`, `--search` live). The doctor summary already adapts.
- A number only: ask what is missing for that row, inside the single direction round.

## B. Per environment (say it in the teacher's words; answer 「되나요?」 with 된다/안 된다/대신 이렇게)
| | Claude app/web | Claude Code | Codex |
|---|---|---|---|
| 결과 보기 | 오른쪽 결과물 화면 | `--open` 크롬 | `--open` 크롬 |
| 공유 링크·QR | 「게시(Publish)」 -> 링크 | 파일을 드라이브·USB로 | 같음 |
| MP4 영상 | 🎥 녹화(.webm) | 처음 요청 때 설치(약 80MB, 동의 후) | 같음 (인터넷 필요) |
| 자동 플레이 점검 | 보통 없음 -> 글자·문법 점검 | 영상 도구 설치 후 | 같음 |
| 최신 법 확인 | 웹 검색 켜기 | 내장 | 인터넷 허용 + `--search` |
| 결과 위치 | 다운로드 버튼 | `~/TeacherStudio/` | 같음 |

## C. Cannot do -> instead (never end at 「안 돼요」)
| 원하는 것 | 지금은 | 대신 이렇게 |
|---|---|---|
| 사람 같은 AI 목소리 | 내장 안 됨 | 컴퓨터 기본 읽어 주기(Web Speech)는 됨. 사람 같은 목소리는 외부 서비스를 선생님이 골라야 함 |
| 실제 사람(연예인·동료·학생) 목소리·얼굴 흉내 | 만들지 않음 | 비슷한 분위기의 오리지널 캐릭터. 궁금하면 `teacher-law` |
| AI 그림·사진 만들기 | 안 들어 있음 | 내장 아이콘·도형, 무료 그림 팩, 선생님 사진 |
| 로그인 필요한 일(나이스·SNS 올리기) | 대신 로그인·업로드 안 함 | 파일을 만들고 올리는 순서를 안내 |
| 영상 편집(자르기·자막) | 앱·웹에선 안 됨 | 🎥 녹화(.webm)는 됨. 자르기·자막·MP4는 Claude Code·Codex |
| PPT·워드·엑셀·PDF **파일** | 공식 문서 스킬이 있으면 그쪽 | 파일은 그쪽에 맡기고 디자인·구성·점검을 얹음. `doctor`의 `official_doc_skills`로 확인. 그쪽 파일을 베끼지 않음 |
- 「더 화려하게」 (GSAP): default is Motion, anime.js, CSS. GSAP only if truly needed, loaded from the official CDN at view time (its own terms, internet needed, not bundled).
- Shared toolbox (`shared/`): `design.py --use present|poster|invite|print|web`, colour tools (`color_from.py`, `color_check.py`, `oklch.py`), parts (`inline.py`), fonts (`embed.py`), install (`ensure.py`).

## D. Fast path after a request is clear
- Read the skill's SKILL.md (short) -> the one missile README -> write only the changing parts in `content.json` -> `studio.py fire ... --content content.json [--open] [--mp4]` -> show the file when `READY <path>` prints. Never read engine.html / stage.html.
- Pick a skin by subject, mood, grade; no skin fits -> nearest skin + `vars` (colours) + `world` text.
- Reference photo/video: pull 3-4 colours, type feel, layout density, pace; say it in one line; adjust. Never reuse their logos or art. 「이 사이트처럼」 + URL/screenshot -> `learn-from-reference.md` (`ref_analyze.py`).
- The user's template, logo, PPT/POTX/Word/HWPX/CSS colours come first (`user-colors.md`, `color_from.py` -> spec `design.palette_from`).
- After building: 1 line what, 1 line how, 2 tweaks. No dev terms.
