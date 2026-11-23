# 행사 오프닝·홍보 영상 미사일 (event-promo)

## 언제
- 축제·발표회·체육대회·설명회·동아리 모집처럼 **행사를 알리는 30초 화면/영상**: 큰 글자 한 마디 → 그림(사진) 한 장 + 행사 이름 → 날짜 크게 → 프로그램 카드 3개 → 움직이는 낱말 → 끝 카드(언제·어디서, 2.5초 넘게 멈춤)
- 강당 TV·복도 모니터에 반복 재생, 단톡방·학교 누리집에 MP4로 올리기

## 선생님 말 예시
- 「가을 축제 홍보 영상 30초」 → festival
- 「학예회 오프닝 화면, 날짜랑 프로그램 보이게」 → festival + content.json

## content.json 형식 (바뀌는 것만)
```json
{ "title": "가을 축제", "school": "우리 학교",
  "hook_small": "올가을,", "hook_a": "우리 학교가", "hook_b": "들썩인다!", "tagline": "우리가 만드는 하루",
  "date_num": "11.27", "date_day": "금", "date_chips": ["오후 1시", "학교 운동장"],
  "program_head": "이런 게 기다려요",
  "program": [ {"icon": "stage", "name": "학급 공연", "desc": "무대 위 우리 반"},
               {"icon": "booth", "name": "체험 부스", "desc": "만들고 겨루고"},
               {"icon": "food",  "name": "먹거리 장터", "desc": "함께 만든 간식"} ],
  "kinetic": ["보러 와요", "같이 놀아요", "함께 만들어요!"],
  "end_when": "11월 27일(금) 오후 1시", "end_line": "학교 운동장에서 만나요",
  "hero": "poster.jpg" }
```
- 한 장면에 한 생각: `hook_a`·`hook_b` 6자 안팎, 카드 `name` 6자·`desc` 10자 이내. 날짜는 요일까지 맞게.
- `hero` = 그림 한 장(content.json 옆 파일 또는 비워 두기). 파일이면 페이지 안에 넣어져 인터넷 없이 열려요. 비우면 스킨 색으로 그린 무대 그림이 대신 들어가요.
  그림을 새로 만들려면 고명 단계: `shared/design/garnish.py env` (Codex가 있으면 같은 화풍 그림, 글자·로고·얼굴 없이). 학생 얼굴 사진은 넣지 않아요.
- 아이콘: `stage`(무대) `booth`(부스) `food`(먹거리) 등 show.js의 ICON 목록.

## 만들기 · 점검 · 영상
`python3 scripts/build_stage.py --missile event-promo --skin festival --content content.json --out promo.html`
`python3 scripts/check_page.py promo.html` → PASS. MP4: `python3 scripts/render_mp4.py promo.html promo.mp4` (Playwright + ffmpeg가 있을 때만, 시간 먼저 말하기) 또는 페이지의 🎥 버튼(webm).

## 확인된 것 (2026-11-23)
- 2026-11-22 쇼케이스 「가을 축제」 화면을 틀로 옮김(문구는 모두 DOC에서, 학교명은 예시 「우리 학교」). 30초 타임라인 `STAGE.timeline`, R = 처음부터.
