# Changelog

## [Unreleased]
### Added
- 자동 테마 2차: 세계별 **정해진 소품**(바다 → 고래·물고기·조개·불가사리·닻·해초·거품·게, 직접 그린 색 있는 그림 / 그 밖의 세계는 Tabler 아이콘을 색 스티커로), 바다 도우미(고래·문어·복어 직접 그림), 카드 무늬와 짝 맞추기 **카드 뒷면 엠블럼**, 분류 게임의 **색 뚜껑 큰 통 + 개수 표시**, 방송 부품(**팀 연단 줄·왼쪽 큰 진행자 기둥**), 제목 반짝임 상자 제거
- `design_review.py`: 소품 관련성 검사, 밋밋한 카드 검사
- 게임 **자동 테마 `theme:"auto"`(기본)**: `design.words`(우주·바다·동화·긴장감·따뜻하게·고급스럽게·역사 …)·분위기·과목으로 `scripts/theme_auto.py`가 배경 장면(오로라·파도·언덕·도시·보케·잉크산·구장·기하·메시)·무늬·도우미 캐릭터·떠다니는 소품·축하 연출·제목 글꼴·음악을 조합 (같은 입력 → 같은 결과). 요청이 한 세계를 분명히 가리키면 이식 테마 한 벌을 그대로 사용
- 옛 스킨 9개의 연출을 **이식 테마**로 재사용: `tv-studio` · `auditorium-bell`(강당 종 울리기) · `space-station` · `joseon-war-room` · `antidote-lab` · `sun-temple` · `post-office-night` · `cell-feeding` · `recycle-robot` (진행자 캐릭터·무대 장치·장면·반응). 7개 방식(quiz·survival·escape·match·bingo·board·sort) 모두에서 동작하고, auto가 이 부품(진행자·무대)을 다른 배경·소품과 섞어 쓴다
- 테마 런타임(`core.js`): 진행도·정답/오답 펄스·승패를 모든 방식이 같은 상태(`COMP.S`)로 내보내고, 도우미 캐릭터(4가지 표정)·말풍선·무대 장식이 반응
- `shared/assets/`: 라이선스 확인된 디자인 소재 — DiceBear CC0 캐릭터 8세트, Tabler·Iconoir 아이콘(MIT), Open Color(MIT), ZzFX(MIT)와 효과음 프리셋, `manifest.json`·`verify_assets.py` (NOTICE 13~17)
- `scripts/design_review.py` + `references/design-rubric.md`: 제목·문제·정답·오답·결과 화면을 찍어 접촉 시트 PNG와 수치(장식 밀도·휑함·색 수·시선·대비·겹침)를 만들고 옛 스킨 9개 기준(`assets/design-baseline.json`)과 비교해 WARN+고칠 방법을 알려 줌. 흐름: build → check → design_review → AI가 그림을 보고 → spec 수정 (최대 2번)
- 예시 spec 10개로 늘림(바다 짝 맞추기·역사 방탈출·송년회 퀴즈·방송국 퀴즈), `examples/design-review/`에 접촉 시트·비교 그림
- 점검기·디자인 점검·캡처 도구가 소리 없이 돌아감(`--mute-audio` + 말하기·오디오 출력 막기)
- `shared/` 공용 도구함: `design/`(디자인 생성기·팔레트 15·글자 크기표 — 게임·슬라이드·영상·포스터·초대장·인쇄·웹 공통, 「따뜻하게」「고급스럽게」 같은 말 인식), `vendor/`(Motion·canvas-confetti·Chart.js·KaTeX·Lucide·Phaser·axe-core 고정 버전 + 라이선스, `inline.py`로 쓴 것만 파일에 넣기), `fonts/`(Noto Sans/Serif KR을 페이지에 쓰는 글자만 잘라 넣기 → 인터넷 없이도 글꼴 유지), `tools/ensure.py`(처음 필요할 때 동의 받고 설치: fonttools·python-pptx·python-docx·openpyxl·python-hwpx·pypdf·pillow·qrcode·imageio-ffmpeg·playwright, 시스템 ffmpeg·크롬 우선)
- `tools/sync_shared.py --check`: 공용 복사본·AGENTS/CLAUDE·dist zip이 원본과 다르면 실패
- `teacher-studio`: 「못 하는 것 → 대신 이렇게」 표, doctor가 처음 필요할 때 설치되는 도구와 공식 문서 스킬(PPT·워드·엑셀·PDF)을 알려 줌
- 게임 spec에 `libs`(필요한 부품만 넣기), 게임·슬라이드·영상이 글꼴을 파일에 넣음(`--no-fonts`로 끔)
- `teacher-law`: 법률 안내 스킬 — 최신 법을 공식 출처에서 직접 찾아 고정 형식 답 카드로 안내, 인쇄용 A4 안내문(`make_notice.py`), 공식 출처·확인 조항 목록, 점검 질문
- 만든이 표시: `NOTICE`·`CITATION.cff`·README 「만든 사람」, 소스 파일 SPDX 머리말, 결과 HTML에 보이지 않는 `meta generator`+주석(게임·슬라이드·영상·법률 안내문), 게임 선생님 메뉴 맨 아래 「만든 도구」 줄. 화면에 보이는 표시는 기본 꺼짐 (게임 spec `credit:true` / `build_stage.py --credit`, 선생님이 원할 때만)
- `shared/voice/voice.js`: 기기에서 가장 자연스러운 목소리 자동 선택(Natural/Neural/Google 등 점수), 문장별 읽기, 크롬 15초 끊김·iOS 대응. 게임 빙고·끌어서 보내기가 사용하고 선생님 메뉴에 쓰는 목소리와 Edge 안내 표시
- `.gitattributes`(줄바꿈 LF 고정, 바이너리 지정)
### Changed
- 옛 스킨 「골든벨」의 방송 프로그램 이름을 글에서 뺌(`golden-bell` 스킨 id·파일명은 그대로, 새 이름 「강당 종 울리기」)
- Motion 부품은 `allow_modern:true`(게임 spec) / `--allow-modern`(슬라이드·영상)을 줄 때만 파일에 넣음. 없이 들어가면 만들기가 멈추고 anime.js를 권하며, 점검기는 실패(허용했을 땐 주의)
- 디자인 생성기를 `teacher-game`에서 `shared/design/`으로 옮김 (`teacher-game/scripts/design.py`는 그대로 쓰는 입구)
- `render_mp4.py`: 시스템 크롬·ffmpeg(없으면 imageio-ffmpeg)를 자동으로 찾고, 설치는 동의 후(`--yes`)
- ADR 0007: axe-core(MPL-2.0, 점검기 전용·수정 없이) 예외, ISC 허용 명시
- `teacher-studio`: 법률 질문 라우팅, 준비 카드에 법률 안내·학생 정보 주의 문구, 「할 수 없는 것」 절
- `legal-advisory.md`: 법 결론 제거, `teacher-law`로 안내
- 게임·슬라이드·영상 스킬과 선생님 말 사전: 링크 공개 전 확인 문구 추가

## [0.1.0] - 2026-11-18
### Added
- `teacher-studio`: 첫 관문 스킬 — 준비 카드, 환경 확인(doctor), 라우팅, 통합 명령 `studio.py`
- `teacher-game`: 게임 엔진 + 미사일 3종(퀴즈쇼·방탈출·끌어서 보내기) × 스킨 9, 점검기
- `teacher-slides`: 공통 무대 + 수업·연수 슬라이드 미사일(화면 구성 13종) × 스킨 3
- `teacher-motion`: 과목 소개 영상 × 스킨 3, 수업 시작 화면 × 스킨 2, MP4 렌더(`render_mp4.py`), 🎥 크롬 녹화
- `scripts/setup.py`: Claude Code·Codex 스킬 등록, 선택 설치(Playwright·Chromium)
- README·INSTALL·AGENTS/CLAUDE·MAP, 갤러리, 이슈 양식
