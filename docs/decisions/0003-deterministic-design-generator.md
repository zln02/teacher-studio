# 0003. 결정적 디자인 방향 생성기

- 상태: Accepted (2026-11-18)

## 배경
AI에게 색과 글자 크기를 고르게 하면 대비가 낮은 조합, 칠판에서 안 읽히는 작은 글씨, 매번 다른 결과가 나온다. 「더 예쁘게」를 반복하게 되는 원인이다.

## 결정
`skills/teacher-game/scripts/design.py`가 `subject / grade / mood / use`를 입력받아 **디자인 토큰**(색·글자·움직임)을 규칙으로 계산한다. AI가 쓰는 것은 spec의 `design.subject/grade/mood` 같은 **방향**뿐이고 색 값은 고르지 않는다.
- 같은 입력이면 같은 출력(`--seed`로만 변주).
- 본문 글자 대비 **4.5:1 이상**(WCAG 상대 휘도 계산)을 `design.py --validate`와 점검기에서 확인.
- 글자 크기 하한: `class`는 1920x1080 무대 기준 문제 60px·보기 48px·작은 글 34px, `personal`은 문제 44px·보기 36px. `large:true`면 class 수준.
- 분위기에 따라 움직임 강도 변경(긴장감·신남은 활발, 차분·집중은 약하게).

## 검토한 대안
- **모델이 색을 직접 선택**: 편차가 크고 대비 보장이 없음. 기각.
- **스킨별 수작업 팔레트만 사용**: 품질은 높지만 주제·분위기 조합 수만큼 늘어남. 기각. (대신 검증된 팔레트 세트 `assets/design/palettes.json`을 규칙의 재료로 사용)
- **런타임 자동 대비 보정**: 실패를 숨기고 의도가 흐려짐. 기각 — 점검기에서 FAIL로 드러낸다.

## 결과
- 장점: 재현 가능, 접근성 기준을 코드로 강제, 모델이 바뀌어도 품질이 같음. 선생님 말(「긴장감 있게」)이 곧 `mood`로 매핑됨.
- 단점: 팔레트 수가 정해져 있어 세밀한 브랜드 색 맞춤은 어렵다. 참고 사진에서 새 디자인을 뽑는 기능은 「계획」(README 로드맵).
- 교실과 개인 용도의 글자 하한을 나눈 것은 「교실 기본, 개인은 완화」(ADR 0010)의 구현이다.

## 근거/측정
- `skills/teacher-game/scripts/design.py`(헤더 설명, `contrast()` 함수), `assets/design/palettes.json`, `tokens.schema.json`.
- `check_game.py`: 「design tokens: text contrast >= 4.5:1 and <use> type floor」 항목과 실제 화면 글자 크기 검사.
