# 설계 결정 기록 (Architecture Decision Records)

이 폴더는 교사 스튜디오가 **왜 이렇게 만들어졌는지**를 짧게 남긴 기록이다. 각 문서는 Michael Nygard 형식(상태·배경·결정·검토한 대안·결과·근거)을 따르고, 저장소 안에 실제로 있는 파일과 숫자만 인용한다. 아직 구현되지 않은 부분은 「계획」으로 표시했다. 코드를 읽기 전에 이 기록을 보면 구조의 의도를 빠르게 파악할 수 있다.

| 번호 | 결정 | 상태 |
|---|---|---|
| [0001](0001-tool-structure-over-templates.md) | 템플릿 대신 도구 구조 (engine + components + tokens + spec) | Accepted (테마 이식은 「계획」) |
| [0002](0002-ai-writes-short-spec.md) | AI는 코드 대신 짧은 JSON spec을 쓴다 | Accepted |
| [0003](0003-deterministic-design-generator.md) | 결정적 디자인 방향 생성기 | Accepted |
| [0004](0004-checker-as-release-gate.md) | 점검기를 출시 관문으로 | Accepted |
| [0005](0005-live-official-law-lookup.md) | 법 조문 저장 대신 공식 출처 실시간 조회 | Accepted |
| [0006](0006-student-privacy-no-student-ai.md) | 학생 개인정보 입력·저장 금지, 학생 직접 AI 사용 흐름 없음 | Accepted |
| [0007](0007-license-policy.md) | 라이선스 정책 | Accepted (CC-BY 자동 표기는 「계획」) |
| [0008](0008-per-environment-handling.md) | 환경별 처리 (Claude 앱 / Code / Codex) | Accepted |
| [0009](0009-reuse-official-skills.md) | 공식 스킬·기존 도구 재사용 | Accepted (구현은 「계획」) |
| [0010](0010-identity-teacher-first.md) | 정체성: 선생님 맞춤이 기본, 용도 제한 없음 | Accepted |
| [0011](0011-no-regret-principle.md) | 무손실 원칙: 하네스가 맨 모델보다 나빠지면 안 된다 | Accepted (평가 관문은 「계획」) |
| [0012](0012-for-everyone.md) | 모두를 위해: 선생님·한국어 기본값, 직업·언어 제한 없음, 사용자 디자인 우선 | Accepted (0010 확장) |
| [0013](0013-documents-weapon-teacher-docs.md) | 문서 무기는 새 스킬 teacher-docs: HWPX 표준 라이브러리 직접 작성, 설치된 hwp-docs·docx 스킬에 위임, 워드·PDF는 필요할 때 설치 | Accepted (0009 일부 변경) |

## AI 활용 개발

이 프로젝트는 AI 코딩 도구(Claude Code 등)의 도움을 받아, 소유자의 지시와 검토 아래 만들었다. 코드 작성 속도는 AI가 높였지만, 여기에 기록된 **설계 결정(무엇을 만들고, 무엇을 만들지 않으며, 어디까지 책임질지)은 소유자의 것**이다.
