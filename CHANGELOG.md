# Changelog

## [Unreleased]
### Added
- `teacher-law`: 법률 안내 스킬 — 최신 법을 공식 출처에서 직접 찾아 고정 형식 답 카드로 안내, 인쇄용 A4 안내문(`make_notice.py`), 공식 출처·확인 조항 목록, 점검 질문
### Changed
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
