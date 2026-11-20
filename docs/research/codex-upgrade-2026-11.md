# Codex(GPT) 하네스 업그레이드 2026-11

모델: 검토 1차 gpt-6.1-sol, 2차·구현·실사용 시험 gpt-6.2-sol (추론 xhigh/high, 검토는 웹 검색 켬). 브랜치 `codex/upgrade-2026-11`.

## 결론 먼저

- GPT가 보기에 하네스는 Codex에서 **뼈대는 맞지만(`~/.agents/skills` 경로, AGENTS.md)** 「한 번 말하면 전문가급」·「하네스 없는 모델보다 낫다」는 두 목표는 아직 입증되지 않았다. 새 라이브러리보다 **배포 정합성(ZIP이 원본과 다름), '검사 완료/못 함' 구분, 환경 진단, 설치 안전성**이 먼저라고 두 모델이 같은 결론을 냈다.
- GPT 6.2가 Codex 쪽 막힘을 고쳤고 단위 테스트 15개 파일이 모두 통과했다. 다만 **실제 Codex 실행에서는 샌드박스에 `py`가 없어** 첫 시험의 제작 도구가 돌지 않았다(아래 Phase C). 이 부분은 아직 남은 숙제다.

## GPT가 찾은 것 (공통 / 모델별)

- 공통(6.1·6.2 모두): ZIP 7/8이 원본과 다름 / 검사 못 한 것을 '통과'처럼 말함 / 환경 확인이 설정 한 줄만 봄 / 설치 실패 시 기존 설치가 사라질 수 있음 / Codex 평가기 응답 형식 오류 / 자료 분석에서 개인별 예시 행 노출과 경계값 오류 / 슬라이드·문서 품질 기준은 담당 팀에 제안.
- 6.1만: 오래된 Chrome 지원을 실제 문법 검사(Acorn)로 확인, 상수열 상관계수 0 처리와 집단 내 값이 같을 때 p=1 버그.
- 6.2만: 설명(description)만 보고 맞는 스킬을 고르게 하기, 분명한 요청은 첫 응답에서 끝내기(콘티 확인은 필요할 때만), 외부 스킬은 검색 단계에서 실행하지 않고 버전·라이선스 확인 후 설치, 법령은 실제로 읽은 조문까지만 '확인 완료'.
- 전문: `codex-review-2026-11-gpt61.md`, `codex-review-2026-11-gpt62.md` (출처 링크 포함).

## 바뀐 것 (커밋 2개, 52개 파일)

- AGENTS.md·CLAUDE.md·INSTALL.md·setup.py: Codex 라우팅과 설치 경로, Windows(py)·macOS(python3) 명령 분리, 설치 실패 시 기존 설치 복구.
- 환경 확인(doctor): 설정 파일 한 줄이 아니라 쓰기·브라우저·인터넷을 실제로 확인.
- 제작 검사 결과를 PASS / PARTIAL / FAIL로 구분(디자인 검사·MP4 변환 실패도 반영). 게임·웹앱·수업 도구 점검기 보강.
- 자료 분석: 개인별 예시 행 제거, 상수열·빈 집단 처리 수정. 법령 조회·외부 스킬 찾기는 확인 범위를 기록.
- 새 도구 `shared/tools/syntax_check.py`: Acorn 8.15.0(MIT)로 ES2017 문법 검사. 필요할 때 npm에서 받으며 번들하지 않음. `manifest.json`(on_demand_tools)과 `NOTICE`에 기록, 라이선스 원문 `shared/vendor/acorn-LICENSE.txt`. anime.js는 ES2017 호환을 위해 spread·optional catch도 치환(NOTICE 갱신).
- 라우터 평가(`tools/router_eval.py`, `router_cases.json`), 신규 테스트 `tools/test_codex_workflows.py`, `.github/workflows/` 추가.
- 지킨 것: teacher-slides, teacher-docs, docs/training, dist/ zip은 건드리지 않음.

## 검증

- `tools/test_*.py` 15개 전부 통과 (PYTHONUTF8=1, `py`).
- `sync_shared.py --check`는 **보호 구역 때문에 의도적으로 실패**: slides의 anime.js, docs의 ensure.py 사본이 낡음, dist zip 6개가 낡음. 병합 후 담당자가 `py tools/sync_shared.py`를 돌려 zip까지 다시 만들어야 한다 (Codex는 이 부분을 되돌리지 않고 `codex-suggestions-for-other-teams-2026-11.md`에 남김).
- Codex 샌드박스가 `git commit`을 거부해(오류 1909) 커밋은 리드가 직접 했다(메시지 끝에 GPT 공동 저자 표기).

## 아직 제안인 것

- 슬라이드: 실제 PowerPoint 렌더와 근사 미리보기 구분, 문서: 학교명·행사일·금액 임의 채움 금지, 연수 자료 품질 기준 (`codex-suggestions-for-other-teams-2026-11.md`).
- 같은 모델·같은 요청으로 하네스 유무를 짝지어 반복 비교(첫 응답 완성률을 출시 판단에 포함).
- 스킬 설명 한국어 예시 앞세우기의 실제 호스트 확인.

## Phase C: Codex 실사용 시험 (gpt-6.2-sol, high)

방법: 빈 작업 폴더의 `.agents/skills/`에 8개 스킬을 복사(작업 폴더 범위 설치, 사용자 `~/.codex`·`~/.agents`는 수정하지 않음). 임시 CODEX_HOME은 위치가 Temp면 명령이 정책에 막혀 쓸 수 없어 기본 홈을 쓰고 스킬은 작업 폴더로 격리. 샌드박스 workspace-write, 인터넷 켬.

| 요청 | 스킬 선택 | 시간 | 결과 | 점검 |
|---|---|---|---|---|
| 초5 사회 문화유산 복습 게임 만들어 줘, 알아서 | teacher-studio, teacher-game 정확히 선택(SKILL.md 읽음) | 443초 | HTML 1개 완성(10문제, 3모둠, 출처 3개). **제작 도구는 안 돌았고 직접 작성**: 샌드박스 PATH에 `py`가 없어 `studio.py build`가 실패, 대체 파이썬도 환경 문제 | `check_game` FAIL(7): 스튜디오 구조 항목(GAME 데이터, 엔진, 음소거·선생님 메뉴) 없음 + aspect-ratio 1건, 브라우저 열기 검사 시간초과 |
| 학급 1인 1역할 정하는 도구 만들어 줘, 알아서 | teacher-studio, teacher-class-tools 선택 | 405초 | `build_webapp.py`로 생성, 도구 작동(무작위 배정·맞바꾸기·인쇄) | `check_webapp` FAIL 4: 버튼 겹침 3화면, 초기화 버튼 없음; 12~13px 글자 경고 |

비교(`ceiling-eval-2026-11`, sonnet 스튜디오): 복습 게임 첫 결과 6.4분·점수 4.50, 역할 정하기 2.5분·3.88. Codex GPT는 6.7분/6.8분으로 느리지만 스킬 선택은 정확했다. 점수 비교는 심사를 돌리지 않아 하지 못했다(점검기 실패 수만: sonnet 스튜디오 게임 1·역할 2, Codex 게임 7·역할 4. 게임의 7은 도구를 쓰지 못해 구조 항목이 빠진 탓이 큼).

### Phase C가 드러낸 남은 문제 (다음 작업 후보)
1. Codex 샌드박스에서 `py` 명령이 없다 → 문서의 `py`를 믿지 말고 doctor가 찾은 **절대경로 파이썬**을 준비 카드에 적어 그대로 쓰게 하거나, 스크립트를 `python`/`python3`/`py` 순으로 시도하는 얇은 진입점(run.cmd/run.sh)을 두기.
2. 도구 실행에 실패했을 때 「직접 만들기」로 빠지면 점검기가 구조 항목 때문에 항상 FAIL이 된다 → 대체 경로용 중립 점검 모드 필요.
3. 웹 앱 점검에서 버튼 겹침·초기화 버튼은 레시피에 사전 규칙으로 넣기.

### 참고
- 시험 중 실수로 `taskkill`이 사용자 Codex 앱 프로세스(codex.exe)를 한 번 종료시켰다. 앱은 재실행하면 된다.
- 산출물(시험용 HTML)은 `C:\Users\User\codex-e2e\`에 있다 (저장소 밖).
