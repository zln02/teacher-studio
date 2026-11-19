# 규칙·점검 전수 조사 (2026-11-19)

원칙: 하네스는 지름길이지 울타리가 아니다. 사용자 뜻이 이긴다. 점검은 AI가 보여 주기 전에 스스로 고치라는 장치이고, 사용자를 막는 장치가 아니다.
기본값은 안전하게 두고, 사용자가 말하면 끌 수 있게 한다. 진짜 안전·법 한계만 단단히 둔다.

- **단단함(HARD)**: 사용자가 시켜도 안 한다. 대신 할 수 있는 길을 한 줄로 알린다.
- **기본값(DEFAULT)**: 안전하게 켜져 있고, 사용자가 말하면 끈다. 끄면 한 줄 주의가 나온다.
- **주의(WARN)**: 알려만 주고 막지 않는다. 끄는 스위치 필요 없음.

## 1. 단단함 (끄지 않음)

| 규칙 | 어디 | 지금 동작 | 이유 |
|---|---|---|---|
| 학생 개인정보를 바깥 서비스로 보내기 금지 | 전 스킬 Absolute rules, teacher-data, check_tool | 어디에도 업로드·전송 안 함. 도구는 바깥 요청 0 | 개인정보 보호법 |
| AI가 원본 표(행)를 읽지 않음 | teacher-data SKILL 1번 | 스크립트가 집계만 내놓음 | 학생 정보가 대화에 새는 걸 막음 |
| 불법 행위, 실존 인물·브랜드 흉내, 남의 저작물 복제(가사·유명 캐릭터) | teacher-law, 각 SKILL 절대 규칙 | 안 만들고 대안 안내 | 법·저작권 |
| 되돌릴 수 없는 바깥 행동(보내기·게시·삭제) 전에 확인 | ask-first.md, deliver.py | 먼저 묻고 「네」 후 실행. deliver는 업로드 안 함 | 되돌릴 수 없음 |
| 번쩍임·소리 안전(juice 점검) | check_game wow_checks | 위험하면 FAIL | 광과민 발작 예방 |
| 끝까지 안 돌아감·JS 오류·깨진 파일(DOCTYPE, 문법) | check_game, check_tool, check_page | FAIL | 작동하지 않는 결과물 |
| 입력칸 없음(이름·학번·사진 받는 칸) | check_game, check_tool | FAIL | 학생 정보를 받는 구조 금지 (사용자가 대신 파일을 올리는 건 별개) |

## 2. 기본값 (사용자가 끌 수 있음)

| 규칙 | 어디 | 지금 → 바뀐 동작 | 끄는 방법 (말 예시 → 모델이 설정) |
|---|---|---|---|
| 번호·학번·id 칸은 절대 안 보임 | teacher-data `tdata.py`, `analyze.py` | 숨김(기본). **바뀜**: 요청하면 높은·낮은 목록에 실제 번호를 보이고 「이 파일은 밖으로 보내지 마세요」를 리포트와 meta에 적음. 점검(`check_report`)은 번호 새어 나옴을 FAIL 대신 WARN으로. 원본 행은 AI가 읽지 않는 것 그대로 | 「번호도 보여 줘」「학번 그대로」 → plan `"show_ids": true` |
| 높은·낮은 목록은 익명 순위(상위 1위…) | `analyze.py` rank | 기본 익명. 요청하면 가명(학생01) 라벨. (이미 있던 `show_labels`에 안내 문구·SKILL 지시를 맞춤) | 「이름/가명 라벨 보여 줘」 → plan `"show_labels": true` |
| 빈칸(`[학교명]`, 20XX, OO, 000)이 남으면 FAIL | `placeholders.py`, `deck.py`, `slides_review.py`, `pptx_check.py` | 기본 FAIL(보내기 전에 AI가 채움). **바뀜**: 양식·틀 요청이면 빈칸 허용, 「바꿔 넣을 곳」으로 알리고 한 줄 주의 | 「양식으로」「빈칸 있는 틀로」「서식만」 → spec `"template_blanks": true` (파일만 검사할 때 `pptx_check.py --allow-blanks`) |
| 바깥 주소(인터넷) 요청 FAIL | `check_game.py`, `check_page.py`(motion·slides), `check_tool.py` | 기본 오프라인. 이미 `"online": true`면 CDN·Google 글꼴만 허용(그 밖의 주소는 계속 FAIL). SKILL에 말투 추가 | 「인터넷 연결돼도 돼」「구글 글꼴 써 줘」 → spec `"online": true` (+「인터넷이 있어야 제대로 열려요」) |
| 작은 글자 FAIL(요소·게임 속 글자 바닥) | `check_game.py` | 기본 FAIL → AI가 글을 줄여 고침. **바뀜**: 원하면 주의로 | 「글씨 작아도 돼」 → spec `"waive": ["text_size"]` |
| 글자 잘림·넘침·화면 밖 FAIL | `check_game.py`(clipcheck 포함) | 같음 | 「이 배치 그대로」 → `"waive": ["overflow"]` |
| 상단 바(타이머·점수)가 문제 상자를 가림 FAIL | `check_game.py` hudoverlap | 같음 | 「상단 바 겹쳐도 돼」 → `"waive": ["hud"]` |
| 폰 화면 점검 FAIL(글자 14px, 버튼 44px, 화면 밖) | `phone_check.py` via `check_game` | JS 오류는 제외하고 같음 | 「폰에서 작아도 돼」 → `"waive": ["phone"]` |
| 오래된 크롬 대응(`?.` `??`, 새 라이브러리 motion) | specs.py, check_game | 이미 `allow_modern:true`로 끌 수 있음 | 「요즘 크롬만 써」 → `"allow_modern": true` |
| 수업용 큰 글자 바닥(class) | design.py tokens | `use: personal`로 완화 가능 | 「개인용으로」 → spec `use: "personal"` |
| 만든 표시 숨김 | `credit` | 기본 숨김, 원하면 켬 | 「만든 도구 표시해 줘」 → `"credit": true` |
| 하네스 경로 자체(도구·점검) | teacher-studio Override | 이미 「하네스 없이 해 줘」 | 「그냥 네 방식대로」 |
| 설치·큰 다운로드는 먼저 묻기 | No-regret rules | 묻고 진행 | 「알아서」는 질문만 건너뜀, 설치 동의는 유지 |

## 3. 주의만 하는 것 (WARN, 막지 않음)

색약에서 비슷해 보이는 색(`color_check`), 정답 위치 쏠림, 한국어 단어 중간 줄바꿈, 한 글자 끝줄(orphan), 일부 오래된 크롬 부품(allow_modern 시), 「바꿔 넣을 곳」 목록, 파일 속 숫자 대조 이외의 문장 길이 안내, Playwright 없을 때 화면 점검 건너뜀.

## 4. 아직 안 바꾼 것 (다음 작업 후보)

| 규칙 | 어디 | 생각 |
|---|---|---|
| 수업 도구에 저장소(localStorage) 쓰기 FAIL | `check_tool.py` | 팀 명단을 이 기기에 저장하고 싶다는 요청이 생기면 `"allow_storage"` + 「이 기기에만 저장돼요」 주의로 열기. 입력한 이름이 저장되므로 학생 이름이면 기본값 유지 |
| 파일 크기 2MB 초과 FAIL | `check_game.py`, `check_tool.py` | 원하면 WARN으로 낮출 수 있음 (waive에 `size` 추가) |
| 문장 길이·어려운 말 비율 FAIL | `check_report.py` | 전문가용 리포트에서는 WARN이 알맞을 수 있음 |
| 글 속 전화·이메일·주민번호 모양 FAIL | `check_report.py` | 사용자가 직접 넣은 안내문 연락처라면 허용 스위치 후보. 개인정보 이슈라 신중히 |
| 한 슬라이드 요소 36개 등 덩어리(clutter) 상한 | `slides_review.py` | 기본 유지, 요청 시 `"waive"` 후보 |

## 5. 모델이 사용자에게 말하는 법

사용자가 기본값을 끄라고 하면: 스위치를 켜고, 주의 한 줄만 말하고, 바로 진행한다. 설교하지 않는다. 단단함 목록의 요청이면 못 하는 이유를 한 줄로, 대신 할 수 있는 길을 한 줄로 말한다.
(라우터의 「User wins」 절, `skills/teacher-studio/SKILL.md`)
