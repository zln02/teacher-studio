# CLAUDE.md — Claude Code 작업 안내 (AGENTS.md와 같은 내용)

이 저장소는 **교사 스튜디오**: 코딩을 모르는 선생님을 위한 수업 자료 하네스(Agent Skills 모음)입니다.

- 선생님이 설치를 부탁하면 → [`INSTALL.md`](INSTALL.md)를 처음부터 그대로 따른다.
- 선생님이 무언가 만들어 달라고 하면 → [`skills/teacher-studio/SKILL.md`](skills/teacher-studio/SKILL.md)부터 읽는다 (준비 카드 · 환경 확인 · 미사일 고르기).
- 전체 지도 → [`MAP.md`](MAP.md). 필요한 칸의 스킬 폴더만 읽는다.
- 법·저작권·개인정보·AI 규정 질문, 또는 학생 정보·남의 저작물·공개 공유·생기부가 걸린 요청 → [`skills/teacher-law/SKILL.md`](skills/teacher-law/SKILL.md) (최신 법을 직접 찾아 근거와 함께 안내. 법 내용을 저장소에 적어 두지 않는다.)
- 선생님께는 개발 용어를 쓰지 않는다 (`skills/teacher-game/references/teacher-language.md`).

## 개발할 때 (저장소 자체를 고칠 때)
- 공통 무대(`shared/stage/`)를 고쳤으면 `python3 tools/sync_shared.py`(Windows는 `py tools/sync_shared.py`)로 각 스킬에 복사 + `dist/` zip 갱신.
- 엔진·무대·미사일을 고친 뒤에는 모든 스킨을 `studio.py fire`로 다시 만들고 `check`가 PASS인지 확인한다.
- 결과물 규칙: HTML 한 파일, 외부 이미지 금지, ES2017 문법(`?.` `??` 금지), 학생 정보 칸 금지.
- 이 문서의 `python3`는 Windows에서 `py`로 바꿔 실행한다.
- 커밋: conventional commits (`feat:` `fix:` `docs:` …).
