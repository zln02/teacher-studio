# 과목 소개 영상 미사일 (subject-intro)

## 언제
- 학기 첫 시간·오리엔테이션에 띄우는 35~45초 「과목 소개 영상」(16:9, 전자칠판·TV·유튜브)
- 흐름: 질문 하나(궁금증) → 과목 이름 크게 등장 → 「이 과목에서 만날 것」 2~6장면(그림+한 줄) → 선생님 한마디 → 마무리 카드(학교·학년·선생님)

## 선생님 말 예시
- 「첫 시간에 과학 소개하는 영상 만들어 줘, 멋있게」 → science-neon
- 「국어 오리엔테이션 영상, 붓글씨 느낌으로 차분하게」 → korean-brush
- 「영어 과목 홍보 영상, 뉴스 속보처럼」 → english-news

## content.json 형식 (바뀌는 것만 — 스킨 파일 위에 덮어씀)
```json
{ "title": "중학교 수학 소개",
  "hook": { "kicker": "첫 번째 질문", "text": "숫자 없이 하루를 살 수 있을까?" },
  "subject": { "name": "수학", "en": "MATH", "sub": "중학교 1학년" },
  "items": [ { "icon": "numbers", "word": "수와 연산", "line": "음수까지 넓어지는 수의 세계" },
             { "icon": "magnifier", "word": "탐구", "line": "규칙을 찾고 이유를 설명해요" } ],
  "message": { "label": "선생님의 한마디", "text": "틀려도 괜찮아요. 끝까지 생각해 본 사람이 이깁니다." },
  "closing": { "school": "", "grade": "1학년", "teacher": "", "line": "첫 수업에서 만나요" },
  "world": { "meet": "이 과목에서 만날 것" } }
```
- `subject`·`hook`·`message`·`closing`·`world`는 한 단계만 합쳐지므로 **과목을 바꿀 때는 `subject`의 `name`·`en`·`sub`를 모두** 쓴다(안 쓰면 스킨 예시 값이 남음).
- `closing`의 `school`·`grade`·`teacher`는 빈칸("")이면 화면에서 빠짐. 학생 이름은 넣지 않는다.
- `items` 2~6개 (3~4개 권장). 개수에 맞춰 장면 길이가 자동 조절(총 35~45초). `word`는 2~8자, `line`은 30자 이내.
- `icon` 이름(원본 선 그림): beaker atom dna planet magnet leaf bolt book brush speech paper pen globe mic chat plane music numbers bulb heart star people palette ball clock school hanok magnifier map wave gear — 없는 이름은 star.
- 스킨별 `world` 문구:
  - science-neon: `hookTag`(질문 번호 장식 "Q.01"), `meet`
  - korean-brush: `seal`(낙관 글자 1~4자, 예 "國語" — 과목 바꾸면 꼭 바꾸기, 비우면 과목 첫 글자), `meet`, `numerals`(장면 번호 글자 배열)
  - english-news: `live` `channel` `time` `breaking` `topStory` `meet` `story` `interview` `signoff` `tickerLabel` `ticker`(아래 자막 띠 문장 배열). english-news는 `items[].word`에 영어 키워드, `line`에 한국어 설명. `closing.teacher`는 인터뷰 이름표에도 나옴.
- `vars`로 색·글씨체 변경 가능(스킨 파일에 전체 목록). 색만 바꾸면 그림·배경 색이 함께 바뀜.

## 스킨 (서로 다른 세계 — 색만 바꾼 것이 아님)
- **science-neon** 어두운 실험실: 원근 격자 바닥·떠다니는 입자, 네온 선이 그려지며 빛나는 그림(비커·원자·DNA·행성), 네온관처럼 깜빡이며 켜지는 제목, 빛 막대가 쓸고 지나가는 장면 전환, CRT 화면이 켜지듯 열리는 마무리. 글씨: Black Han Sans + Space Mono.
- **korean-brush** 한지 위 수묵: 종이 결·먹 번짐 산수 능선·붉은 해, 붓 한 획이 지나가며 과목 이름이 드러남(비백 포함), 낙관 도장이 쾅, 원상(붓 원) 안에 먹선 그림, 먹이 스미듯 나타나고 번지며 사라지는 전환. 글씨: Song Myung + 나눔명조, 세로쓰기 장식.
- **english-news** 뉴스 속보 방송: LIVE 표시·채널명·시계·아래 흐르는 자막 띠, 회전하는 지구본 배경, BREAKING NEWS 띠, 빨강·흰·남색 사선 막이 휩쓰는 전환, 모니터+하단 자막 바, 인터뷰 이름표, STAY TUNED 엔딩. 글씨: Anton + Black Han Sans + Noto Sans KR.

## 확인된 것 (2026-11-18)
- 3스킨 모두 `check_page.py` PASS, 1280×720·1920×1080에서 장면별 캡처 확인(겹침·잘림 없음), 페이지 오류 0.
- 정확한 프레임 MP4: science-neon 44초 30fps (`scripts/render_mp4.py`) 재생 확인.
- 글씨가 길면 자동으로 줄어듦(STAGE.fitText). 웹 글꼴이 늦게 와도 다시 맞춤.
- 한계: 인터넷이 없으면 Google 글꼴 대신 기본 글꼴로 보임(배치는 유지). 소리 없음(필요하면 영상 편집기에서 음악 추가).
