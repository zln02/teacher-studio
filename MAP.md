# 교사 스튜디오 — 지도 (Claude가 맨 먼저 읽는 한 장)

> **북극성: 무기고에 고급 무기를 채워 두면, 어떤 요청이 와도 어떤 모델이든 같은 상용 품질이 나온다.**
> Claude는 처음부터 만들지 않는다. 미사일(완제품) → 고급 무기(부품·프로그램) → 디자인 세트 순으로 꺼내 쓰고, 품질 장치(점검기)를 반드시 통과시킨다.

**규칙: 이 지도만 읽고, 선생님 요청에 맞는 칸 하나만 내려받는다.** 전체를 받지 않는다.
상태: ✅ 바로 사용 · 🔨 만드는 중 · 📋 계획

## 1. 요청 → 칸 찾기
| 선생님 말 (예) | 칸 | 내려받을 폴더 |
|---|---|---|
| 게임, 퀴즈, 방탈출, 종 울리기, 단어·분류 | 🎮 수업 게임 | `skills/teacher-game` ✅ (spec → `build.py`로 어떤 게임이든 + 옛 미사일: quiz-show · escape-room · drag-deliver, 스킨 9) |
| 타이머, 뽑기, 모둠 나누기, 대진표, 점수판 | 🧰 수업 도구 | `skills/teacher-class-tools` ✅ (spec → `build_tool.py`, 오프라인 HTML 1개, 가족·동호회도) |
| 프로그램, 앱, 웹페이지, 도우미·챗봇, 계산기, 시뮬레이션, 연습장 | 🖥️ 웹 앱 | `skills/teacher-studio` ✅ (`references/webapp.md`: spec → `scripts/build_webapp.py` + `check_webapp.py`, 오프라인 HTML 1개, 프로젝터 모드, 「AI」는 솔직하게) |
| 엑셀·CSV·설문·점수·가계부 분석, 그래프 | 📊 자료 분석 | `skills/teacher-data` ✅ (AI가 원본을 읽지 않고 스크립트가 집계 → 쉬운 그래프 보고서, 이름 가림·숫자 대조) |
| 수업 슬라이드, 발표 자료(웹·PPT), 연수 자료, 홍보 PPT, 기관 보고 | 🖥 슬라이드 | `skills/teacher-slides` ✅ (spec → `build slides`: 12 스타일 × 장 23종 × 배치 변형 × 용도 4(수업·홍보·기관 보고·개인), 점검·접촉 시트·닮음 검사 / 옛 lesson-deck 스킨 3개는 최하 우선순위) |
| 과목 소개 영상, 수업 시작 화면, 오프닝, 글자 움직이기 | ✨ 모션·타이포·영상 | `skills/teacher-motion` ✅ (subject-intro 3 · lesson-opening 2) |
| 학습지, 활동지, 형성평가지(인쇄) | 📝 학습지 | `skills/teacher-worksheet` (예정) 📋 |
| 공문, 가정통신문, 안내문, 계획서, 결과보고서 (한글·워드·PDF), 양식 채우기, 한글 파일 고치기, PDF 합치기·나누기 | 📄 문서 | `skills/teacher-docs` ✅ (spec → `docs.py make` HWPX·DOCX·PDF, 공문 형식 자동(1. 가. 1) …·끝·붙임·날짜), `fill`·`patch`로 원본 서식 유지, 점검기 `doc_check.py`) |
| PPT 파일, 파워포인트 | 📊 PPT 파일 | `skills/teacher-slides` ✅ (`--pptx`, 내 양식 `--template`, 용도 `"context"`: 수업·홍보·기관 보고·개인) |
| 영상 자르기, 자막, 배경음악, 사진 영상 | 🎬 영상 | `skills/teacher-video` (예정) 🔨 |
| 포스터, 카드뉴스, 캔바, 피그마 | 🎨 디자인 | `skills/teacher-design` (예정) 📋 |
| 자료 찾아 줘, 논문 요약, 비교해 줘 | 🔎 조사 | `skills/teacher-research` (예정) 📋 |
| 3D, 분자 모형, 학교 둘러보기 | 🧊 3D | `skills/teacher-3d` (예정) 📋 |
| 써도 돼요?, 올려도 돼요?, 저작권, 개인정보, AI 규정, 생기부 | ⚖️ 법률 안내 | `skills/teacher-law` ✅ (최신 법을 직접 찾아 근거와 함께 답 카드·인쇄용 안내문) |
| 링크로 보내기, QR, 학교 모음에 올리기 | 📤 나누기 | `skills/teacher-studio` ✅ (게시·QR·파일 안내) |
| 처음 설정, 안 돼요, 여기서 되나요? | ⚙️ 시작·설정 | `skills/teacher-studio` ✅ (준비 카드·환경 확인) |

두 칸에 걸치면(예: 「게임 + 그걸 소개하는 PPT」) 두 칸만 받는다.

## 2. 설치·내려받기
- Claude Code / Codex: 저장소의 `INSTALL.md`를 따라 `python3 scripts/setup.py --agent <claude-code|codex>` (스킬 8개 등록 + 환경 확인)
- Claude 앱·웹: `dist/`의 zip 8개를 스킬로 올리기
- 모든 요청의 첫 관문은 `skills/teacher-studio` (번호 붙은 라우터 R0~R5: 안전 → 분명/막연 → 만들기/같이 기획 → 스킬 → 못 찾으면 스카우트·맨 길). 막연하면 `scripts/direction.py`(방향 3가지 + 분위기 카드), 기획·조사는 `references/co-plan.md`. 만드는 일은 모두 `references/pipeline.md`의 6단계(기획→대본→콘티→제작→수정→배포, 확인 최대 3번): 콘티 `scripts/storyboard.py`, 배포 `scripts/deliver.py`, 끝에 활용·전달 단계(선생님은 「수업 활용」: `references/classroom-use.md`, `deliver.py --use tv|tablet|print|lms|home|archive|screen|share|sns|drive`, 이 컴퓨터 프로그램 확인 `scripts/env_programs.py`). 평가: `tools/router_eval.py` + `tools/router_cases.json`(결과 `docs/research/router-eval-2026-11.md`)

## 3. 부품 등급
| 등급 | 뜻 | 예 |
|---|---|---|
| 기본기 (칼) | Claude가 원래 하는 것. 부품 없이 됨 | 글쓰기, 간단한 HTML, 표 정리 |
| 부품 (총) | 검증된 프로그램 + 우리 사용법 + 점검기. 매번 같은 품질 | 게임 엔진, 한글 공문 생성기, PPT 한글 글꼴 고정기, 영상 레시피 |
| 대포 | 무겁거나 연결이 필요. 필요할 때만 | 그림 팩(300KB), 3D 모델, Canva·Figma 연결 |

부품 카드 형식 (각 모듈 `PARTS.md`):
`이름 | 언제 쓰나 | 불러오는 법 | 크기 | 검증 상태(날짜) | 라이선스 | 점검 명령`

## 4. 모든 칸 공통 순서
선생님 말 해석(shared/teacher-language) → 빠진 것만 묻기 → 기획 한 장 확인 → 부품으로 제작 → 자동 점검 → 화면으로 보여 주기 → 고치기 → 나누기·보관 안내

## 5. 어디서든 쓰기 (이식성 규칙)
- 형식: 모든 칸은 **Agent Skills 표준(SKILL.md)** 폴더 → Claude(웹·앱·Claude Code), Codex, Gemini CLI, Cursor 등 SKILL.md 지원 도구에서 그대로 읽힌다.
- 설치: claude.ai는 「설정 > 스킬」에 칸별 zip 올리기 또는 작업 공간에서 내려받기 / Claude Code·Codex는 skills 폴더에 복사(또는 `npx skills add <repo>`).
- 결과물은 **파일 하나(HTML)**: 고급 프로그램(anime.js 등)과 한글 글꼴(TS Sans = Pretendard 잘라낸 것, Noto Serif KR. 쓰는 글자만)은 파일 안에 넣어 인터넷·설치 없이 크롬만 있으면 열린다. 장식 글꼴(검은고딕 등)만 Google Fonts(없으면 넣어 둔 Noto로 대체).
- 무거운 도구는 있을 때만: MP4 정확 렌더(Playwright+ffmpeg), HyperFrames(Apache-2.0, 0.9.x 매일 바뀜 → 쓰면 버전 고정). 없으면 페이지의 🎥 버튼(크롬 탭 녹화 → .webm).
- 라이선스: 넣는 프로그램은 MIT·ISC·Apache·OFL·CC0만 (axe-core MPL-2.0은 점검기 전용·수정 없이). GSAP은 저장소에 넣지 않고, 「더 화려하게」가 필요할 때만 공식 CDN에서 보는 순간 불러온다 (GSAP 자체 약관).
- 오래된 학교 크롬 대응: `?.` `??` 등 금지 문법 점검기로 자동 검사 (넣는 프로그램도 같은 검사, anime.js는 1곳 패치). Motion은 `?.`가 있어 `allow_modern`(게임 spec) / `--allow-modern`(슬라이드·영상)을 줄 때만 넣고, 없이 들어가면 점검기가 실패로 막는다.

## 6. 공용 도구함 `shared/` (모든 칸이 같이 쓴다. 고치면 `python3 tools/sync_shared.py`, 점검은 `--check`)
| 폴더 | 내용 | 쓰는 법 |
|---|---|---|
| `shared/design/` | 디자인 생성기 `design.py` + 팔레트 15 + 글자 크기표 (게임·발표·포스터·초대장·인쇄·웹) | `design.py --use present --mood 고급스럽게` → 색·글꼴·글자 크기 한 세트 |
| `shared/design/system.py` · `DESIGN-RULES.md` · `ai_look.py` | 글자 크기 단계 · 자간 · 8pt 여백 · 이름 있는 배치 틀 · 색 밝기 사다리(OKLCH) · 장식 7가지 · 움직임 값 / 규칙 27개 / 「밤티 검사」(빛 번짐·형광·속 빈 글자·그라데이션·강조색 수·여백·장식 겹) | `ai_look.py --html 결과.html` → 전문 디자이너 기준 5/5 |
| `shared/design/color_from.py` · `color_check.py` · `oklch.py` | 내 로고·사진·PPT/POTX·워드·한글(HWPX)·사이트 CSS에서 색 뽑기 → 디자인 값(글자 대비 4.5, 밝기만 조정) / 색약(적·녹·청황) 점검 WARN / OKLCH 변환·조화색·같은 간격 명암 | `color_from.py logo.png --out pal.json` → spec `design.palette_from`. 점검기가 자동으로 WARN. 가이드 `skills/teacher-studio/references/user-colors.md` |
| `shared/design/meaning.py` | 뜻이 있는 색: 「초록불」「빨간불」「청팀·백팀」「금·은·동」처럼 낱말이 색 이름이면 그 색으로 칠함(순서대로 돌려 쓰는 색보다 먼저). 옆 칸은 비슷한 색을 피함 | 슬라이드(PPT·웹) 비교 칸·목록·카드, 게임 분류 통, 점수판·모둠 카드가 자동으로 물어봄 (`color_of` · `assign` · 화면용 `js()`) |
| `shared/vendor/` | Motion · canvas-confetti · Chart.js · KaTeX · Lucide · Phaser · anime.js · axe-core(점검기 전용) | `inline.py`로 쓴 것만 파일에 넣기 (`manifest.json`에 버전·라이선스) |
| `shared/fonts/` | TS Sans(Pretendard) · Noto Sans/Serif KR 기본 글자 모음 + `embed.py` | 페이지에 쓰는 글자만 잘라 WOFF2로 파일 안에 넣기 |
| `shared/tools/ensure.py` | 처음 필요할 때 동의 받고 설치 | `ensure("python-pptx")`, `ensure_ffmpeg()`, `ensure_playwright()` |
| `shared/tools/workdir.py` | 작업 폴더(시스템 임시 폴더 없이 동작: 결과 파일 옆 `.teacher-studio-work/`, `TEACHER_STUDIO_TMP`로 지정)와 「화면을 띄울 수 있나」 확인. 못 띄우면 `NO-BROWSER` 한 줄 뒤 브라우저 없는 점검으로 | 모든 스크립트가 `tempfile` 전용 폴더 대신 사용 (`temp_dir` · `make` · `named` · `guard_browser`) |
| `shared/tools/stamp.py` | 결과 파일에 보이지 않는 만든이 표시(meta generator + 주석) | 게임·슬라이드·영상 조립 때 자동 |
| `shared/tools/placeholders.py` | 빈자리·빈말 점검 하나: 문서·PPT(`policy_checks`)와 HTML 화면(`html_checks`: 「확인 필요」 빈말, 「교사 초안」 도장, `[학교명]`·`○○초` 빈자리, 되풀이한 예시 안내) | 문서·PPT·게임·웹 앱·수업 도구 점검기가 자동으로 부름 |
| `shared/tools/example_likeness.py` | 결과가 넣어 둔 예시 파일(시험용 fixture)을 그대로 따라갔는지 검사: 문장 60% 이상 같음 · 차례와 제목이 같음 · 뼈대가 장마다 같음 → WARN 「예시를 그대로 따라간 것 같아요」 | 게임·발표·프로그램 점검기와 발표·문서 조립기가 자동으로 부름 |
| `shared/content/CONTENT-RULES.md` | 내용 규칙과 전문가 관문(G1~G10). 무기별 레시피는 각 스킬 `references/content-*.md` | 각 SKILL.md의 「Content quality first」 줄이 가리킴. 스킬 안 `shared/content/`로 복사됨 |
| `shared/assets/` | 디자인 소재(CC0 캐릭터 DiceBear·Tabler/Iconoir 아이콘·Open Color·ZzFX 효과음) + `manifest.json` | 게임 `theme:auto`가 `theme_auto.py`로 골라 씀 (쓴 것만 파일에 들어감) |
| `shared/voice/voice.js` | 브라우저에서 가장 자연스러운 목소리를 골라 읽어 주기 (문장 나눔·15초 끊김 대책·iOS 대응) | 게임 조립 때 자동 포함 (`TSVoice.speak`) |
| `shared/stage/` | 슬라이드·영상 공통 무대 | 기존대로 |
| `shared/juice/` | 「Game Wow」 키트: 소리 12종·입자·흔들림·점수 올라가기·시상대·움직임 효과 10개 + 안전 점검(`juice_lint.py`) | 게임·수업 도구가 자동 포함 (`spec.juice`로 조절) |
| `shared/tools/sound_ears.py` | 소리 파일 듣기·점검(크기·깨짐·길이, 교실에 맞는지), 효과음 만들기. 선택 도구 earshot은 동의 후 전용 폴더에 설치, 없어도 기본 점검·ZzFX로 동작 | teacher-game·teacher-motion 점검 |
| `shared/tools/video_eyes.py` | 영상 → 장면 사진(+선택 자막), **내 컴퓨터 안에서만**(외부 전송 없음, 동의 후 도구 설치) | `diagnose.py`·`ref_analyze.py`가 사용 |
| `shared/vendor/qrcodegen` | QR을 만들 때 SVG로 직접 그림(MIT) | 슬라이드 QR 장 |
