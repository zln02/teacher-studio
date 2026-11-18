# Changelog

## [Unreleased]
### Added
- `shared/` 공용 도구함: `design/`(디자인 생성기·팔레트 15·글자 크기표 — 게임·슬라이드·영상·포스터·초대장·인쇄·웹 공통, 「따뜻하게」「고급스럽게」 같은 말 인식), `vendor/`(Motion·canvas-confetti·Chart.js·KaTeX·Lucide·Phaser·axe-core 고정 버전 + 라이선스, `inline.py`로 쓴 것만 파일에 넣기), `fonts/`(Noto Sans/Serif KR을 페이지에 쓰는 글자만 잘라 넣기 → 인터넷 없이도 글꼴 유지), `tools/ensure.py`(처음 필요할 때 동의 받고 설치: fonttools·python-pptx·python-docx·openpyxl·python-hwpx·pypdf·pillow·qrcode·imageio-ffmpeg·playwright, 시스템 ffmpeg·크롬 우선)
- `tools/sync_shared.py --check`: 공용 복사본·AGENTS/CLAUDE·dist zip이 원본과 다르면 실패
- `teacher-studio`: 「못 하는 것 → 대신 이렇게」 표, doctor가 처음 필요할 때 설치되는 도구와 공식 문서 스킬(PPT·워드·엑셀·PDF)을 알려 줌
- 게임 spec에 `libs`(필요한 부품만 넣기), 게임·슬라이드·영상이 글꼴을 파일에 넣음(`--no-fonts`로 끔)
- `teacher-law`: 법률 안내 스킬 — 최신 법을 공식 출처에서 직접 찾아 고정 형식 답 카드로 안내, 인쇄용 A4 안내문(`make_notice.py`), 공식 출처·확인 조항 목록, 점검 질문
- 만든이 표시: `NOTICE`·`CITATION.cff`·README 「만든 사람」, 소스 파일 SPDX 머리말, 결과 HTML에 보이지 않는 `meta generator`+주석(게임·슬라이드·영상·법률 안내문), 게임 선생님 메뉴 맨 아래 「만든 도구」 줄. 화면에 보이는 표시는 기본 꺼짐 (게임 spec `credit:true` / `build_stage.py --credit`, 선생님이 원할 때만)
- `shared/voice/voice.js`: 기기에서 가장 자연스러운 목소리 자동 선택(Natural/Neural/Google 등 점수), 문장별 읽기, 크롬 15초 끊김·iOS 대응. 게임 빙고·끌어서 보내기가 사용하고 선생님 메뉴에 쓰는 목소리와 Edge 안내 표시
- `.gitattributes`(줄바꿈 LF 고정, 바이너리 지정)
### Changed
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
