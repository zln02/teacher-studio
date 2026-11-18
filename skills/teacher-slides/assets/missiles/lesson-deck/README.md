# lesson-deck — 키노트급 수업·연수 슬라이드 (웹)

## 언제
수업 PPT, 발표 자료, 칠판에 띄울 슬라이드, 교원 연수 자료, 학부모 설명회 자료. `items` 한 개 = 한 장.
진짜 .pptx 파일이 필요하면 이 미사일이 아니다(📋 teacher-pptx, 아직 없음) → 웹 슬라이드 + PDF 인쇄로 안내.

## 선생님 말 예시
- 「다음 주 과학 수업 PPT 만들어 줘. 생물의 구성 단계, 10장 정도」 → chalkboard
- 「월요일 연수 발표 자료, 애플 키노트처럼 깔끔하게」 → clean-keynote
- 「학부모 설명회 슬라이드, 부드럽고 친근하게」 → notebook-pastel

## 발사
```
python3 scripts/build_stage.py --missile lesson-deck --skin <스킨> --content content.json --out deck.html
python3 scripts/check_page.py deck.html
```
영상(MP4)으로: content에 `"reel": true` 를 넣어 따로 만든 뒤 `python3 scripts/render_mp4.py deck-reel.html deck.mp4 --fps 24`
(전체 장이 자동 진행. 페이지의 🎥 버튼도 자동으로 같은 전체 진행을 녹화한다.)

## content.json (바뀌는 것만)
`{"title":"…", "world":{"labels":{…}}, "items":[…]}` — 공통 키: `layout`, `kicker`(작은 머리말), `note`(선생님 메모, N키로만 보임), `build:false`(한꺼번에 등장).
글 안의 `**낱말**` = 강조(분필 밑줄/형광펜/그라데이션). `\n` = 줄바꿈. 아이콘은 `icon`에 키워드.
| layout | 키 |
|---|---|
| cover | title, subtitle, meta(발표자·날짜), icon |
| section | title, sub, num(생략 시 01, 02… 자동) |
| question | q, hint(다음 누르면 등장) |
| bigtext | text, sub |
| cards | title, cards:[{icon,title,text}] 2~4 (하나씩 등장) |
| compare | title, a:{label,icon}, b:{label,icon}, rows:[{k,a,b}] 2~5 |
| steps | title, steps:[{icon,title,text}] 3~6 (선이 이어지며 등장) |
| bignumber | value("87%"·"1,200"도 됨), unit, caption, kicker |
| quote | text, source |
| timeline | title, events:[{when,title,text}] 3~6 |
| quiz | q, choices[2~4], answer(0부터), explain — 다음 누르면 정답 공개 |
| image | icon(또는 이모지), title, text, kicker |
| end | title, sub, next:[…최대 4], qr(QR 자리 안내 글) |

아이콘 키워드: flask book globe lightbulb chart people school robot calendar check star heart music leaf atom cell tissue person microscope chat target pencil sparkle clock puzzle search home phone question megaphone mail shield warning game (한국어 별명도 됨: 세포·조직·실험·책·지구·학교·목표·게임 …). 모르는 낱말이면 반짝이 아이콘, 이모지는 그대로.
`world.labels`: question hint quiz answer correctMark vs thanks notes noNote lastSlide qr. `world.builds:false` = 전 장 한꺼번에. `world.reelHold`(ms) = 영상 한 장 머무는 시간.

## 스킨
- **chalkboard** — 초록 칠판·나무 틀·분필 가루, Jua+고운바탕, 글자가 써지고 밑줄·동그라미가 손으로 그려짐, 지우개로 지우며 넘김
- **clean-keynote** — 흰 무대·Noto Sans KR 900 큰 글자·여백, 단어가 마스크에서 올라오고 강조는 파랑→청록 그라데이션 (어둡게: vars bg1 #0b0b0f, text #f5f5f7, card #1c1c22)
- **notebook-pastel** — 모눈 공책·마스킹테이프·포스트잇, Gaegu 손글씨, 형광펜 강조, 통통 튀며 등장

## 조작
→ / Space / PageDown / Enter / 화면 오른쪽 탭 = 다음(한 줄씩) · ← / PageUp / 왼쪽 탭 = 뒤로 · 밀기 · Home/End · 숫자+Enter = 그 장으로 · N = 메모 · B 또는 . = 화면 끄기 · F = 전체 화면.
진행 막대·쪽 번호는 넘길 때만 잠깐 보인다. 리모컨(프레젠터)의 PageDown/PageUp 그대로 동작.
PDF: 크롬 인쇄(Ctrl+P) → 「PDF로 저장」, 「배경 그래픽」 켜기 → 한 장 = 가로 한 쪽, 마지막 상태(정답 공개)로 인쇄.

## 확인된 것 (2026-11-18)
- 3 스킨 check_page PASS, 1920×1080·1280×720 전 장·전 단계 캡처 확인, 페이지 오류 0 (글꼴 없이도 동작)
- 키보드·탭·밀기·숫자 이동·N·B·뒤로(빌드 되돌리기)·연타 15회, `__stage.seek`로 현재 장 재생, reel 전체 seek 앞뒤
- PDF 인쇄 12쪽 = 12장, MP4(clean-keynote reel) 1920×1080 105초 재생 확인
- 크기: 페이지 약 220KB (anime.js 포함)
