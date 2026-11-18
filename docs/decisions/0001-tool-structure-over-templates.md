# 0001. 템플릿(미사일·스킨) 대신 도구 구조로 간다

- 상태: Accepted (2026-11-18)

## 배경
처음 버전(0.1.0)은 「미사일」이라 부르는 완제품 게임 3종에 「스킨」 9개를 얹은 구조였다. 스킨 하나는 장면·그림·문구까지 담은 완전한 JSON이라(약 2.6~5.7KB) 새 주제마다 AI가 이 JSON을 통째로 써야 했고, 목록에 없는 게임(빙고, 보드게임 등)은 만들 수 없었다. 즉 「정해진 종류만 만드는」 구조였다.

## 결정
템플릿 모음이 아니라 **도구 체인**으로 바꾼다.

`engine`(공통 게임 엔진) + `components`(문제 흐름 + 7가지 방식: quiz·survival·escape·match·bingo·board·sort) + `design tokens`(색·글자·움직임) + `spec`(짧은 기획 JSON) → `build.py` → `check_game.py`.

기존 미사일·스킨 9개는 지우지 않고 **예제이자 회귀 테스트 fixture**로 남긴다(`examples/baseline/`).

## 검토한 대안
- **스킨 계속 늘리기**: 요청 종류 x 디자인만큼 파일이 늘고, 스킨마다 그림을 따로 그려야 해서 유지 비용이 선형으로 증가. 기각.
- **매번 AI가 HTML 직접 작성**: 자유롭지만 품질 편차·토큰 낭비·점검 실패가 큼. 기각(ADR 0002).
- **템플릿 폐기**: 기존 품질 기준을 잃는다. 기각 — fixture로 보존.

## 결과
- 장점: 새 게임 방식은 부품 하나만 추가(`COMP.mech.<이름>`). 디자인은 토큰으로 분리되어 어떤 주제에도 일관된 품질. 빙고·주사위 보드·가족 퀴즈처럼 기존에 없던 요청이 같은 경로로 나온다.
- 단점·트레이드오프: **스킨마다 따로 그린 화려한 연출(진행자 로봇, 방송국 무대 등)은 당분간 사라진다.** 기본 테마는 토큰만 쓰고, 연출 있는 테마(notebook, spotlight 등 일부만 이식됨)로 되살리는 것은 「계획」(기존 스킨 연출의 테마 이식).
- 품질 관문: 스킨 9개의 결과를 baseline으로 고정해 두고 엔진·무대를 고칠 때마다 다시 빌드해 PASS를 확인한다.

## 근거/측정
- `examples/baseline/game-baseline.json`: 레거시 9개 스킨 전부 PASS, 파일 크기와 sha256 기록(예: `quiz-show/tv-studio` 153,575 B, sha256 `6b3a8ca6…`).
- `examples/baseline/spec-builds.json`: spec 9개(신규 7 + 레거시 이식 2) 모두 PASS, 결과 HTML 98~102KB.
- 스킨 JSON 2.6~5.7KB(`skills/teacher-game/assets/missiles/*/skins/`) vs spec 0.6~2.5KB.
- 커밋 `864f2ca`: components 7종, themes 3종(default·notebook·spotlight), 예제 spec 7개 추가.
