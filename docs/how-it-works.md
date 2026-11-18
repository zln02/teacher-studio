# ⚙️ 구조 설명 (개발자용)

## 폴더
```
teacher-studio/
├─ README.md · INSTALL.md(AI용 설치 지시서) · AGENTS.md · CLAUDE.md · MAP.md(지도)
├─ skills/                      ← Agent Skills 표준. 폴더 하나 = 스킬 하나 (스스로 완결)
│  ├─ teacher-studio/              ← 첫 관문: 준비 카드, 환경 확인(doctor), 라우팅, studio.py
│  ├─ teacher-game/         ← 게임: engine.html + missiles/(quiz-show, escape-room, drag-deliver)
│  ├─ teacher-slides/              ← 슬라이드: stage.html + missiles/lesson-deck
│  └─ teacher-motion/              ← 영상·화면: stage.html + missiles/(subject-intro, lesson-opening)
├─ shared/stage/                ← 슬라이드·모션 공통 무대 원본 (tools/sync_shared.py로 각 스킬에 복사)
├─ scripts/setup.py             ← 설치: 스킬 등록(Claude Code ~/.claude/skills, Codex ~/.agents/skills) + doctor
├─ tools/                       ← 개발 도구: sync_shared.py(공통 파일 동기화 + dist zip), build_assets.py(그림 팩)
├─ dist/                        ← Claude 앱 업로드용 zip
└─ docs/                        ← 주문 예시, 갤러리, 배너
```

## 세 층
| 층 | 무엇 | 위치 |
|---|---|---|
| 🚀 미사일 | 완제품 + 스킨. 내용(content.json)만 바꿈 | `skills/*/assets/missiles/<id>/` |
| 🔫 고급 무기 | 게임 엔진(`NG`), 무대(`STAGE`), anime.js 4.5.0, WebAudio 효과음, 그림 팩 | `assets/engine.html`, `assets/stage.html`, `assets/vendor/`, `assets/packs/` |
| 🛡 품질 장치 | 선생님 말 사전, 교실 크기 기준, 점검기, doctor | `references/`, `scripts/check_*.py`, `teacher-studio/scripts/doctor.py` |

## 미사일 형식
**게임** (`teacher-game/assets/missiles/<id>/`): `logic.js`(window.GAME_LOGIC) · `style.css` · `skins/<skin>.json`(완전한 game.json) · `README.md`
**슬라이드·모션** (`.../missiles/<id>/`): `show.js`(window.SHOW) · `style.css` · `skins/<skin>.json`(완전한 DOC) · `README.md`

규칙: 과목별 문구를 코드에 넣지 않는다(전부 skins/content에서). 스킨마다 그림을 따로 그린다(색만 바꾸기 금지). 시간 연출은 가상 시계(`NG.after` / `STAGE.timeline`)로 — 그래야 자동 점검과 MP4 렌더가 정확하다.

## 명령
```bash
python3 skills/teacher-studio/scripts/studio.py list
python3 skills/teacher-studio/scripts/studio.py fire game/escape-room/lab --content c.json --open
python3 skills/teacher-studio/scripts/studio.py fire motion/subject-intro/science-neon --mp4
python3 skills/teacher-studio/scripts/studio.py check file.html
python3 skills/teacher-studio/scripts/studio.py doctor --agent codex
```

## 새 미사일 추가
1. 비슷한 미사일 폴더를 복사해 `logic.js`/`show.js`를 고친다.
2. 스킨 3개(서로 다른 세계)를 만든다.
3. 모든 스킨을 `fire` → `check` PASS → 크롬에서 결과 화면까지 플레이(오답 1번, 선생님 메뉴 포함).
4. 해당 스킬 SKILL.md의 미사일 표, `teacher-studio/SKILL.md`의 라우팅 표, `MAP.md`, README 무기고 표를 갱신.
5. `python3 tools/sync_shared.py`로 zip 갱신.

## 도구 선정 기준
- 파일 안에 넣는 프로그램은 MIT·Apache·OFL·CC0만 (예: anime.js MIT, Kenney CC0).
- GSAP: 무료지만 재배포 조항이 불명확하고 Webflow 경쟁 도구 금지 조항이 있어 넣지 않는다.
- HyperFrames(Apache-2.0): 버전이 매우 자주 바뀜 → 쓸 때는 버전 고정. 기본 MP4는 자체 `render_mp4.py`.
- 오래된 학교 크롬: 넣는 프로그램도 점검기로 검사 (anime.js는 `?.` 1곳 패치).
