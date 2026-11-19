# 시험장 기록(AI 말 2분 복습 게임)에 따른 하네스 수정 (2026-11-19)

원본 기록: noan-ai 저장소 `docs/harness-testbed/2026-11-ai-quiz.md` (F1~F15). 이 저장소에서 고친 것과 남은 것을 적는다. 전·후 그림: `testbed-fix-2026-11.png` (같은 spec을 postbuild 없이 옛 하네스와 고친 하네스로 만듦).

## 고친 것
| # | 무엇 | 어떻게 |
|---|---|---|
| F1 | 폰 세로 | 엔진 `fit()`: `device:"phone"` + `quiz`(OX 포함)가 세로로 들리면 600칸 폭 세로 무대(돌리지 않음) + `layouts/portrait.css`. 글자 16px 이상·버튼 44px 이상. 다른 방식은 세로에서 「폰을 가로로 돌려 주세요」 안내. 가로(844×390)는 버튼 44px·글자 키움. `phone_check.py`가 390×844·844×390을 실제 Chrome으로 재서 `check_game`(PASS/FAIL)·`design_review`(`-phone.png`)에 들어감 |
| F2 | 바깥 주소 | 기본 오프라인: Google 글꼴 링크·주석 속 주소·stamp의 저장소 주소 제거(`build_game`·`build`·`build_stage`). `check_game`(= 슬라이드·영상 점검기와 같은 파일)이 link/script/img/css url·@import/fetch/XHR의 바깥 주소를 FAIL. spec `online:true`일 때만 허용 |
| F3 | 스타일 | `design.style` > `design.words`·`mood` > 제목·과목 > 씨앗. 「AI」 키 삭제. `style_auto.py --spec`·`layout_auto.py --spec`는 build와 같은 함수(`build.layout_for`) |
| F4 | 비네트 | `--vig`: 어두운 장면 .35, 밝은 장면 0 |
| F5 | 색 | `color_from.py` 파일 여러 개, `--ok/--danger/--ink/--border/--bg` 같은 이름 있는 색 우선(이름뿐인 `--mint`·`--red`는 뒤), 정답·오답은 밝기 띠 안에서만 조정(칙칙하지 않게, 색약 안전), 포인트 원색은 `accentDeco` |
| F6 | 글꼴 | `design.font`: sans · serif · rounded · system |
| F7 | 한 글자 줄 | `check_game`이 마지막 줄이 한 글자면 WARN, `layout_auto`는 긴 보기(12자 초과)를 옆으로 나란히 두지 않음 |
| F8 | 라우터 | 모든 새 게임은 spec → build, 옛 스킨은 이름으로 지목할 때만 |
| F9 | 폰 | `direction.py`: 폰·핸드폰·휴대폰·스마트폰·모바일 → `phone`(폰트·헤드폰은 제외) |
| F10 | 출력 | 빌드가 `look: style=… layout=…` 출력 + `<meta name="ts-look">`, `design.title_style`·`design.title` 둘 다 읽음 |
| F11 | 요약 | `design_review` 요약이 화면별 최악값(겹침 최대·대비 최소) |
| F12·F13 | 느림·해설 겹침 | SKILL.md에 `--no-check` 빠른 고치기, `content.md`에 exp 규칙 |
| F14 | 확대·링크 | 확대 허용(폰), spec `back`·`head_meta` |
| F15 | 만든 표시 주소 | `creditUrl`은 `credit:true`일 때만 |
| 추가 | 스킬 설명 | `teacher-data` 설명에 `: `가 있어 YAML이 깨져 제목이 대신 보이던 것 → 따옴표 + 설명 복원. `sync_shared.py --check`가 7개 SKILL.md의 이름·설명(60자 이상·쓰임 포함·따옴표)을 검사 |

## 남은 일 (후속)
- 세로 폰 배치는 `quiz`만. match·bingo·sort·board·survival·escape는 가로로 돌리라는 안내(점검은 PASS). 각각 세로 배치가 필요.
- `design.font:"rounded"`는 둥근 글꼴 파일이 없어 고딕 굵게(OFL 글꼴을 받아 `shared/vendor/manifest.json`·`NOTICE`에 적은 뒤 교체).
- `design_review --fast`(결과 화면 빼기)는 만들지 않음. 작은 폰(375×667)의 세로 높이는 따로 확인하지 않음.
- 슬라이드·영상 페이지는 폰 점검 없음(가로 무대 전용).
- 옛 스킨(fire)은 Google 글꼴이 빠져 기기 글꼴로 보임(기본 오프라인의 대가).

## 입구 평가: 제작 공정표 8건 (before → after)
| 모델 | before (`claude -p`, 2026-11-19 아침) | after (서브에이전트 실행, 같은 맥락 파일·스키마) |
|---|---|---|
| haiku | 0.808 (p02·p03·p04·p06·p08 틀림: 「알아서」를 build 정지로, 영상·게임의 콘티 정지 건너뜀) | **1.000** (8/8) |
| sonnet | 0.952 (p06 콘티 건너뜀, p07 질문 1개) | **1.000** (8/8) |
주의: after는 이 PC의 `claude -p` 로그인이 만료되어 같은 프롬프트를 서브에이전트로 한 번씩 돌린 것이라 도구 없는 `claude -p`와 완전히 같은 조건은 아니다. 원자료: `pipeline-eval-2026-11-after-haiku.json`·`-sonnet.json`(모델 답), 이전 값은 `pipeline-eval-2026-11.json`.
고친 문구: `SKILL.md` Pipeline 줄 7개 번호 규칙 + `references/pipeline.md` 「Pick the checkpoint」 표(첫 번째로 맞는 규칙).
