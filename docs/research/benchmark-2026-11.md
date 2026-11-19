# 벤치마크: 남들은 "막연한 사용자"를 어떻게 이끄나 (2026-11-19)

조사 범위: 공개 저장소 12곳과 공식 문서 3곳의 원문(README, SKILL.md, 문서)을 직접 읽었다. 별(stars)·라이선스 수치는 2026-11-19 GitHub API 기준이다. 읽지 못했거나 추정한 것은 **[미확인]**으로 표시했다.

용어 풀이: 스킬(skill)=AI에게 일 하는 법을 알려 주는 폴더. 게이트(gate)=조건을 채워야 다음으로 넘어가는 관문. 평가(eval)=AI가 제대로 했는지 재는 시험. 프런티어(frontier)=지금 바로 물어볼 수 있는 질문 묶음.

## 1. 결론 (5줄)

1. 막연한 사용자를 다루는 방법은 거의 다 한 가지로 모인다. **"한 번에 묶어서 묻고, 질문마다 추천 답을 달고, '네'가 추천을 받아들이는 뜻이 되게 한다."** (grill-me, frontend-slides, spec-kit, Game Studios 공통)
2. 모델이 달라도 똑같이 따르게 하는 힘은 **글이 아니라 스크립트와 점검기**에서 나온다. 글(prose)로만 쓴 규칙은 모델마다 흔들린다고 Anthropic 공식 문서도 말한다. 우리는 이미 `studio.py`·`check`가 있어 가장 앞선 편이다.
3. 우리에게 없는 것은 **(a) 질문 전에 "이미 아는 것/찾을 수 있는 것"부터 찾는 단계, (b) 시각 미리보기로 고르게 하는 단계, (c) 스킬이 정말 불리는지·모델별로 같은지 재는 평가 세트**다.
4. 길 안내(라우팅)는 "스킬이 서로를 이름으로 부르는 것"(superpowers, ask-matt)과 "설치 도구가 찾아 주는 것"(skills.sh find-skills)으로 나뉜다. 우리는 MAP.md가 있으니 **'라우터 스킬 + 다른 스킬을 찾아 쓰게 하는 한 줄 통로'**만 더하면 된다.
5. 품질은 대부분 "바닥(floor) 점검"만 있고 "최고(best)"는 사람 몫이다. 눈에 띄는 예외는 Game Studios의 **블라인드 비교**(질문으로 만든 기획서 vs 손으로 쓴 기획서 3:0)와 "아직 사람이 안 해 봄"을 적는 인수 카드다.

## 2. 비교표

| 프로젝트 (라이선스·별) | (a) 막연한 사용자 시작법 | (b) 모델 간 일관성 | (c) 라우팅·출처 | (d) 품질 측정 | (e) 빌릴 것 |
|---|---|---|---|---|---|
| **Anthropic 스킬 문서·best practices** (문서) | skill-creator가 "Capture Intent→Interview"로 시작 | 취약한 작업은 "정확히 이 스크립트만 실행"(낮은 자유도), 열린 작업은 글. **Haiku·Sonnet·Opus 모두로 시험** 권고 | 설명(description)에 "무엇+언제"를 써서 선택. 참조는 한 단계 깊이만 | "평가를 먼저 만들라", 최소 3개 시나리오, 기준선(없을 때) 대비 | 자유도 3단계 구분 + 3모델 시험 체크리스트 |
| **anthropics/skills** (루트 LICENSE 없음. 확인한 skill-creator·pdf·frontend-design은 Apache-2.0 / 별 197k) | skill-creator: 의도 파악→인터뷰→평가 | 스크립트 동봉(pdf 등) | README가 spec·템플릿 링크 | `evals/evals.json`, with-skill vs baseline 동시 실행, 뷰어 | 평가 파일 형식(Apache라 구조 차용 가능) |
| **obra/superpowers** (MIT / 321k) | brainstorming: 먼저 "내가 아는 게 뭔가?" 점검→조사→접근법 나열·추천→승인 | using-superpowers: "1% 가능성이라도 스킬 호출" 강제 + 합리화 방지 표 | 스킬끼리 이름으로 호출(brainstorming→writing-plans) | writing-skills: 스킬도 TDD(압박 시나리오로 기준선→통과 확인). 구체 점수 체계는 **[미확인]** | "이미 아는 것 먼저" 질문 + "변명 표" |
| **mattpocock/skills** (MIT / 327k) | grill-me→grilling: 결정 트리, **프런티어 한 번에 묻기**, 질문마다 추천 답(➡️), "네"=추천 수락, 사실은 AI가 찾고 결정만 사용자에게 | 짧은 SKILL.md, 한 줄 위임. `agents/openai.yaml`로 Codex도 지원 | ask-matt가 흐름 라우터. 읽고 나서 말하라는 규칙 | SCOPE.md: "실제로 실패한 사례"만 기능 추가 근거 | 질문 형식(추천 답 달기)과 "사실은 AI가 찾는다" 원칙 |
| **Donchitos/Claude-Code-Game-Studios** (MIT / 40k) | /prototype: 장르별 **한 라운드 질문**, 각 질문에 "보통 답", "you pick" 허용. 막연하면 한 줄 기획 2~3개 먼저 | 훅 18개(커밋·쓰기 검증), 스크립트에 --help, rigor 모드(minimal/standard) | /next-step, /gate-check로 다음 길 안내 | studio-tests/(스킬 자체 린터+행동 명세), 블라인드 비교, 인수 카드에 "사람이 아직 안 해 봄" | 인수 카드의 정직한 "미확인" 표기 + 한 줄 기획 2~3개 제시 |
| **zarazhangrui/frontend-slides** (MIT / 32k) | "모두 한꺼번에 질문"(목적·길이·내용·밀도), 이어서 **스타일 미리보기 3장을 직접 만들어 보여 줌**("보여 주기, 말하지 말기") | 고정 1920×1080 무대 같은 "절대 규칙" 목록, 미리보기 진위 규칙 | 가벼운 인덱스만 먼저 읽고 선택된 것만 상세 로딩(점진 공개) | 미리보기 진위 규칙(내부 용어 노출 금지 등) | **시각 3안 미리보기로 고르게 하기** |
| **hugohe3/ppt-master** (MIT / 78k) | Strategist 단계에서 소통 계약+템플릿 선택을 한 번에 확인. quick 모드는 "묻지 않고 결정" | `⛔ BLOCKING`: 게이트에서 멈춰 사용자 확인, "게이트 전 선행조건 확인", 결정적 라우팅, 용어집 | routing.md가 경로를 정함(질문 추가 금지) | 점검기가 쪽마다 "영수증"을 만듦 | **막히는 게이트 vs 빠른 경로(quick)** 두 모드 |
| **github/spec-kit** (MIT / 150k) | /clarify: 모호함 분류표로 훑고 **최대 5문**, 객관식 2~5개 또는 5단어 답 | 템플릿+스크립트(check-prerequisites)+확장 훅, 헌법(constitution) | handoffs로 다음 명령 연결 | 체크리스트="요구사항의 단위 테스트"(구현 검사 아님) | **질문 상한 5 + 분류표로 우선순위** |
| **bmad-code-org/BMAD-METHOD** (README상 MIT, GitHub는 NOASSERTION, 별도 TRADEMARK.md / 55k) | forge-idea: 한 번에 한 질문, 약한 곳 압박, "버려도 성공". advanced-elicitation: 초안을 "첫 답"에서 밀어냄 | validate_skills.py(결정적 12규칙)+LLM 판정 규칙 분리. "LLM 출력은 자동 테스트하지 말라" | 스킬 이름 호출, 팀·역할 에이전트 | 스킬 검증기 + 보고서 | **결정적 검사와 판단 검사 분리** |
| **garrytan/gstack** (MIT / 142k) | /office-hours: 틀 자체를 반박, `Q<N>`+"왜 묻는지" 형식, 선택지는 `(recommended)` 한 개 | 호스트별 표(Claude 강제 훅 vs Codex 권고), `benchmark-models`로 모델 비교 | 공용 서문(preamble)을 해시로 관리, 설계 문서를 다른 스킬이 읽음 | CI evals 4종, eval-plan(사전 등록·비용 시험) | **"왜 묻는지" 한 줄**과 호스트별 강제력 차이 표 |
| **vercel-labs/skills** (MIT / 40k) + find-skills | find-skills: "어떻게 하지?" 질문에 설치 가능한 스킬을 찾아 줌 | `skills-lock.json` 해시, 75+ 에이전트 지원 | skills.sh 순위→`npx skills find`→**품질 확인 후 추천** | 설치 수, 해시 | 통로: **'다른 스킬 찾기' 스킬 + 추천 전 검증** |
| **vercel-labs/agent-skills** (LICENSE 없음 / 34k) | **[미확인]** (구조만 봄) | AGENTS.md·CLAUDE.md·skills.sh.json 동시 제공 | skills.sh 연동 | 미확인 | 구조 참고만 |
| **ComposioHQ/awesome-claude-skills** (README 배지 Apache-2.0, LICENSE 파일 못 찾음 / 80k) | 목록형. 질문 방식 없음 | 템플릿 스킬 제공 | 큐레이션 목록(출처 통로) | 없음 | "출처 목록" 형식 정도 |
| **OpenAI Codex 문서·openai/skills** (Codex Apache-2.0, openai/skills LICENSE 없음·**지원 중단 표시**) | Codex: 이름·설명만 먼저 읽음(문맥 약 2%), 명시(`$`)/암시 호출 | AGENTS.md: 루트→현재 폴더 순 합치기, 기본 32KiB 한도, SKILL.md 형식은 공통 표준. `openai.yaml`은 OpenAI 전용(추정) | `.agents/skills`를 상위로 훑으며 탐색 | 스크립트는 "결정적 동작이 필요할 때만" 권고 | AGENTS.md 32KiB 한도 의식, 핵심은 SKILL.md에 |
| **agentskills.io 명세** (문서) | - | name·description 필수, `compatibility` 선택, `skills-ref validate` | 점진 공개(메타 ~100토큰→본문 5000토큰 권장) | 검증 도구 | 우리 SKILL.md를 명세 검증기로 돌리기 |

주의: 별 수는 이 시점 API 값을 그대로 적었다(비정상적으로 커 보이는 것도 있으나 재확인은 하지 않았다 **[미확인]**).

## 3. 우리가 따라 할 패턴 TOP 10 (효과 큰 순서)

주인장 목표 = "설치하면 알아서 되고, 막히면 사용자가 생각하기 전에 아이디어·방향·기획을 먼저 가져오고, 어떤 모델이든 같게."

| 순위 | 패턴 | 왜 효과가 큰가 | 출처 · 라이선스 |
|---|---|---|---|
| 1 | **프런티어 한 번에 묻기 + 모든 질문에 추천 답 + "네"=추천 수락** | 선생님이 생각하기 전에 답이 이미 놓여 있다. 라운드 3번이면 끝 | [mattpocock/skills grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) · MIT |
| 2 | **"아는 것부터 점검" + "사실은 AI가 찾고, 결정만 사용자에게"** | 이미 말한 것을 또 묻지 않는다. 질문 수가 줄어 막막함이 준다 | [obra/superpowers brainstorming](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md) · MIT, grilling 위와 같음 |
| 3 | **막연한 한마디에는 "한 줄 기획 2~3개"를 먼저 보여 주기** | "고를 수 있는 것"이 생긴다. 빈 칸 앞에서 얼어붙지 않는다 | [Game Studios README](https://github.com/Donchitos/Claude-Code-Game-Studios) · MIT |
| 4 | **시각 3안 미리보기로 고르게 하기** (말로 묻지 않고 보여 주기) | 비전문가는 취향을 말로 못 한다. 우리 스킨·글꼴·색 고르기에 그대로 맞는다 | [frontend-slides](https://github.com/zarazhangrui/frontend-slides/blob/main/SKILL.md) · MIT |
| 5 | **질문 상한(최대 5)과 분류표로 우선순위** | 질문이 길어지면 이탈한다. 큰 영향 순으로만 묻는다 | [spec-kit clarify](https://github.com/github/spec-kit/blob/main/templates/commands/clarify.md) · MIT |
| 6 | **두 모드: 막히는 게이트 vs 묻지 않는 빠른 경로**, 라우팅은 규칙표로 결정 | "아무거나 만들어 줘"와 "하나하나 고를래"를 둘 다 받는다. 모델 판단에 맡기지 않는다 | [ppt-master](https://github.com/hugohe3/ppt-master/blob/main/skills/ppt-master/SKILL.md) · MIT |
| 7 | **평가 세트 만들기: 스킬 있을 때 vs 없을 때, Haiku·Sonnet·Opus 3모델로** | "어느 모델이든 같게"를 눈으로 증명하는 유일한 방법. 지금 우리 가장 큰 구멍 | [Anthropic best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) · 문서 / Apache-2.0(확인한 폴더 기준) |
| 8 | **결정적 검사(스크립트)와 판단 검사(글) 분리, 글에서 못 지키는 건 스크립트로** | 모델 차이를 줄이는 핵심. 우리 `check`를 이 구조로 정리 | [BMAD skill-validator](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/tools/skill-validator.md) · 라이선스 불명확(README상 MIT), 아이디어만 |
| 9 | **정직한 인수 카드: "통과/아직 고장/추측함/사람이 아직 안 해 봄"** + 블라인드 비교로 "최고"를 잰다 | 바닥 점검만 하는 다른 곳과 달리, 최고(best)에 접근한다 | [Game Studios README](https://github.com/Donchitos/Claude-Code-Game-Studios) · MIT |
| 10 | **통로: 다른 스킬 찾아 주기 + 추천 전 검증, 이름 호출 규칙** | "각종 스킬 문서랑 다른 스킬도 같이 쓰게" 요구. 설치 전 출처·점검을 하게 한다 | [vercel-labs find-skills](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md) · MIT, [superpowers using-superpowers](https://github.com/obra/superpowers/blob/main/skills/using-superpowers/SKILL.md) · MIT |

라이선스 메모:
- MIT·Apache-2.0은 문장을 가져올 때도 저작권 고지만 지키면 되지만, 우리 방침상 **아이디어만 차용하고 우리 말로 다시 쓴다**.
- LICENSE가 없거나 불명확한 것(agent-skills, awesome 목록, openai/skills, BMAD)은 **글 복사 금지, 아이디어만**.
- Apache-2.0은 문장 복사 시 NOTICE에 적어야 한다 (`shared/vendor/manifest.json` 규칙과 같음).

## 4. 따라 하지 말 것과 이유

1. **"1%라도 가능하면 반드시 호출" 같은 강압 어투**(superpowers). 모델마다 과잉 호출·무시 반응이 달라진다. 우리는 규칙표와 스크립트로 대신한다. (효과는 모델별 시험 **[미확인]**)
2. **서브에이전트·역할 놀이 49개 규모**(Game Studios, gstack, BMAD 역할극). 선생님에게는 개념 부담이 크고 Claude Code 전용 훅에 기댄다. gstack 표도 Codex 등은 "권고만, 강제 아님"이라고 인정한다.
3. **개발 용어가 그대로 드러나는 질문 형식**(`D<N>`, question_id, "design tree", 프런티어). 형식의 뼈대만 쓰고 선생님께는 쉬운 말로 낸다 (`teacher-language.md`).
4. **개인 선호를 파일에 쌓아 질문을 자동 생략하는 기능**(gstack question tuning). 공개 배포물에 사용자 정보·학생 정보 칸 금지 원칙과 충돌 위험.
5. **설치 후 자동 업그레이드·`curl | 실행`류 설치**(여러 곳). 비전문가에게 위험하고 우리의 "허용 라이선스·출처 검증" 방침과 안 맞는다.
6. **스킬 수 늘리기 경쟁**(awesome 목록 80k별, 스킬 75개). 매트 포콕의 "실제로 실패한 사례만 추가" 기준(SCOPE.md)이 더 낫다.
7. **광고·후원 안내를 스킬에 넣기**(ppt-master는 요청 시에만 노출하도록 막아 둠). 우리에게는 해당 없음, 흉내 내지 않는다.
8. **LLM 출력 자체를 자동 테스트하라는 BMAD 방침 그대로 수용**. 결정적 코드 결과만 자동 시험한다는 점은 맞지만, 우리는 "스킬이 불리는가"를 재는 평가(7번)가 따로 필요하다.
9. **`openai/skills` 저장소를 기준으로 삼기**: 지원 중단 표시가 붙어 있다. Codex 쪽은 공식 문서와 `agentskills.io` 명세를 기준으로 한다.

## 5. 미확인·한계

- 별 수: API 값을 그대로 적음, 재검증 안 함.
- superpowers의 압박 시험(스킬 TDD)이 실제로 점수화되는지, gstack CI evals 내용, ppt-master 점검기의 구체 기준은 원문 전체를 읽지 않았다.
- anthropics/skills의 docx·pdf·pptx·xlsx 폴더 라이선스는 README가 Apache-2.0이라 했으나, 폴더별 LICENSE는 pdf·skill-creator·frontend-design만 확인했다.
- 다른 모델(GPT, Gemini 등)에서의 실제 동작은 직접 돌려 보지 않았다. "모델 간 일관성" 주장은 각 프로젝트의 문서·구조에 근거한다.
- 한국 교육 현장 전용 선행 프로젝트는 이번 조사에서 찾지 못했다 (별도 검색 필요).
