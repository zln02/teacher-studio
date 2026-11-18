# 교사 스튜디오 — 지도 (Claude가 맨 먼저 읽는 한 장)

> **북극성: 무기고에 고급 무기를 채워 두면, 어떤 요청이 와도 어떤 모델이든 같은 상용 품질이 나온다.**
> Claude는 처음부터 만들지 않는다. 미사일(완제품) → 고급 무기(부품·프로그램) → 디자인 세트 순으로 꺼내 쓰고, 품질 장치(점검기)를 반드시 통과시킨다.

**규칙: 이 지도만 읽고, 선생님 요청에 맞는 칸 하나만 내려받는다.** 전체를 받지 않는다.
상태: ✅ 바로 사용 · 🔨 만드는 중 · 📋 계획

## 1. 요청 → 칸 찾기
| 선생님 말 (예) | 칸 | 내려받을 폴더 |
|---|---|---|
| 게임, 퀴즈, 방탈출, 골든벨, 단어·분류 | 🎮 수업 게임 | `skills/teacher-game` ✅ (quiz-show · escape-room · drag-deliver, 스킨 9) |
| 타이머, 뽑기, 모둠 나누기, 자리 바꾸기, 투표 | 🧰 수업 도구 | `skills/teacher-class-tools` (예정) 📋 |
| 수업 슬라이드, 발표 자료(웹), 연수 자료 | 🖥 슬라이드 | `skills/teacher-slides` ✅ (lesson-deck: chalkboard · clean-keynote · notebook-pastel) |
| 과목 소개 영상, 수업 시작 화면, 오프닝, 글자 움직이기 | ✨ 모션·타이포·영상 | `skills/teacher-motion` ✅ (subject-intro 3 · lesson-opening 2) |
| 학습지, 활동지, 형성평가지(인쇄) | 📝 학습지 | `skills/teacher-worksheet` (예정) 📋 |
| 공문, 가정통신문, 계획서, 결과보고서, 회의록 (한글) | 📄 업무 문서 | `skills/teacher-work-docs` (예정) 🔨 |
| PPT 파일, 파워포인트 | 📊 PPT 파일 | `skills/teacher-pptx` (예정) 🔨 |
| 영상 자르기, 자막, 배경음악, 사진 영상 | 🎬 영상 | `skills/teacher-video` (예정) 🔨 |
| 포스터, 카드뉴스, 캔바, 피그마 | 🎨 디자인 | `skills/teacher-design` (예정) 📋 |
| 자료 찾아 줘, 논문 요약, 비교해 줘 | 🔎 조사 | `skills/teacher-research` (예정) 📋 |
| 3D, 분자 모형, 학교 둘러보기 | 🧊 3D | `skills/teacher-3d` (예정) 📋 |
| 링크로 보내기, QR, 학교 모음에 올리기 | 📤 나누기 | `skills/teacher-studio` ✅ (게시·QR·파일 안내) |
| 처음 설정, 안 돼요, 여기서 되나요? | ⚙️ 시작·설정 | `skills/teacher-studio` ✅ (준비 카드·환경 확인) |

두 칸에 걸치면(예: 「게임 + 그걸 소개하는 PPT」) 두 칸만 받는다.

## 2. 설치·내려받기
- Claude Code / Codex: 저장소의 `INSTALL.md`를 따라 `python3 scripts/setup.py --agent <claude-code|codex>` (스킬 4개 등록 + 환경 확인)
- Claude 앱·웹: `dist/`의 zip 4개를 스킬로 올리기
- 모든 요청의 첫 관문은 `skills/teacher-studio` (준비 카드 → 칸 고르기 → `studio.py fire`)

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
- 결과물은 **파일 하나(HTML)**: 고급 프로그램(anime.js 등)은 파일 안에 넣어 인터넷·설치 없이 크롬만 있으면 열린다. 글꼴만 Google Fonts(없으면 기본 글꼴로 자동 대체).
- 무거운 도구는 있을 때만: MP4 정확 렌더(Playwright+ffmpeg), HyperFrames(Apache-2.0, 0.9.x 매일 바뀜 → 쓰면 버전 고정). 없으면 페이지의 🎥 버튼(크롬 탭 녹화 → .webm).
- 라이선스: 넣는 프로그램은 MIT·Apache·OFL·CC0만. GSAP은 무료지만 재배포 조항이 불명확 → 파일에 넣지 않고 필요 시 CDN 링크로만.
- 오래된 학교 크롬 대응: `?.` `??` 등 금지 문법 점검기로 자동 검사 (넣는 프로그램도 같은 검사, anime.js는 1곳 패치).
