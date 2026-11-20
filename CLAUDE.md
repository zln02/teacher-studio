# CLAUDE.md — Claude Code 작업 안내 (AGENTS.md와 같은 내용)

이 저장소는 **교사 스튜디오**: 코딩을 모르는 선생님을 위한 수업 자료 하네스(Agent Skills 모음)입니다.

- 선생님이 설치를 부탁하면 → [`INSTALL.md`](INSTALL.md)를 처음부터 그대로 따른다.
- 「교사 스튜디오 시작」, 수업 자료 새로 만들기, 수업 도구에 해당하면 → [`skills/teacher-studio/SKILL.md`](skills/teacher-studio/SKILL.md)부터 읽는다 (준비 카드 · 환경 확인 · 미사일 고르기).
- 기존 저장소 코드 수정이나 사용자가 다른 도구를 정한 작업은 해당 지시를 따른다. 저장소 밖에서는 설치한 스킬 설명이 입구다.
- 스크립트는 Windows에서 `py`(없으면 `python`), macOS·Linux에서는 `python3`로 실제 버전을 확인해 실행한다.
- 전체 지도 → [`MAP.md`](MAP.md). 필요한 칸의 스킬 폴더만 읽는다.
- 법·저작권·개인정보·AI 규정 질문, 또는 학생 정보·남의 저작물·공개 공유·생기부가 걸린 요청 → [`skills/teacher-law/SKILL.md`](skills/teacher-law/SKILL.md) (최신 법을 직접 찾아 근거와 함께 안내. 법 내용을 저장소에 적어 두지 않는다.)
- 선생님께는 개발 용어를 쓰지 않는다 (`skills/teacher-game/references/teacher-language.md`).

## 개발할 때 (저장소 자체를 고칠 때)
- 공통 무대·공용 도구함(`shared/stage` · `shared/design` · `shared/vendor` · `shared/fonts` · `shared/tools`)을 고쳤으면 `python3 tools/sync_shared.py`(Windows는 `py tools/sync_shared.py`)로 각 스킬에 복사 + `dist/` zip 갱신. 끝나면 `python3 tools/sync_shared.py --check`로 어긋남이 없는지 확인한다 (스킬 안의 `shared/` 복사본은 직접 고치지 않는다).
- 보호 범위가 명시된 작업에서는 동기화와 점검 모두에 `--skip-skill 이름`과 `--skip-zips`를 필요한 만큼 사용한다. 통합 배포 전에는 제외 없이 다시 점검한다.
- 새 라이브러리·글꼴을 넣을 때는 npm pack / pip download로 받아 **실제 LICENSE 파일을 읽고** `shared/vendor/manifest.json`과 `NOTICE`에 적는다 (허용: MIT·ISC·Apache·OFL·CC0, axe-core만 점검기 전용 예외). GSAP·ffmpeg는 넣지 않는다.
- 디자인(색·글꼴·글자 크기)은 `shared/design/design.py`로 정한다. 스킬마다 따로 만들지 않는다.
- 엔진·무대·미사일을 고친 뒤에는 모든 스킨을 `studio.py fire`로 다시 만들고 `check`가 PASS인지 확인한다.
- 결과물 규칙: HTML 한 파일, 외부 이미지 금지, ES2017 문법(`?.` `??` 금지), 학생 정보 칸 금지.
- 이 문서의 `python3`는 Windows에서 `py`로 바꿔 실행한다.
- 커밋: conventional commits (`feat:` `fix:` `docs:` …).
