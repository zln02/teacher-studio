**결론: Codex에서 사용할 수 있는 기반은 갖췄지만, “한 번 요청하면 전문가 수준”, “하네스 없는 모델보다 항상 낫다”는 두 목표는 아직 달성했다고 보기 어렵습니다.** 우선 해결할 문제는 새 라이브러리의 부족보다 **배포본 불일치, 검사하지 못한 결과의 PASS 처리, 환경을 잘못 판별하는 코드, 불필요한 제작 중단**입니다.

저장된 천장 평가에서도 Sonnet은 일반 실행 평균 **3.92**, 하네스 적용 **3.67**이었습니다. 다만 조건별 실행이 한 번이고 PPT를 근사 미리보기로 심사했으므로, 이 수치를 현재 버전의 확정 성능으로 받아들이면 안 됩니다. 이후 개선 기록에도 Codex 실험은 미실행으로 남아 있습니다. [천장 평가](C:/Users/User/Downloads/teacher-studio-codex/docs/research/ceiling-eval-2026-11/README.md), [후속 개선 기록](C:/Users/User/Downloads/teacher-studio-codex/docs/research/fable-upgrade-2026-11.md)

이번 검토는 읽기 전용으로 진행했습니다. 안내문·스킬 본문·참조 문서·연구 기록을 교차 검토하고, 스킬의 Python 스크립트 71개를 정적 검색했으며 핵심 설치·생성·검사·평가 경로를 상세 추적했습니다. **파일 수정과 설치는 하지 않았습니다.** 현재 셸에서 `py`, `python`, `python3`를 찾지 못해 생성 시험과 Python 검사기는 실행하지 않았습니다. 대신 ZIP 내부 파일 비교와 벤더 해시 대조는 직접 수행했습니다.

**Codex 호환성 판정은 다음과 같습니다.**

| 항목 | 판정과 막히는 곳 |
|---|---|
| `AGENTS.md` 라우팅 | 저장소 안에서 적용되는 방식은 맞습니다. 다만 스킬 폴더를 사용자 영역에 복사하는 것만으로 이 저장소의 `AGENTS.md`까지 다른 프로젝트에 적용되지는 않습니다. 설치 후에는 스킬 설명에 의한 실제 선택을 별도로 시험해야 합니다. [공식 안내](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [설치 코드](C:/Users/User/Downloads/teacher-studio-codex/scripts/setup.py:33) |
| `~/.agents/skills` 설치 | Codex의 공식 검색 위치와 일치합니다. 형제 스킬을 찾는 구조이므로 현재 설치 안내처럼 8개를 함께 설치해야 합니다. 하나만 설치하면 필요한 생성기를 찾지 못할 수 있습니다. [공식 검색 위치](https://learn.chatgpt.com/docs/build-skills), [형제 스킬 탐색](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/scripts/studio.py:40) |
| 스킬 설명과 자동 선택 | `teacher-studio`의 “ANY request”는 범위가 넓습니다. 다른 전문 스킬과 충돌하는지 실제 호스트에서 확인해야 합니다. Codex는 스킬이 많으면 설명을 줄이거나 일부를 초기 목록에서 생략할 수 있습니다. [입구 스킬](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/SKILL.md:3), [공식 동작](https://learn.chatgpt.com/docs/build-skills) |
| Windows·macOS 실행 | 내부 하위 명령에 `sys.executable`을 사용하는 점은 좋습니다. 하지만 Python 자체가 없는 환경의 시작 절차가 부족합니다. Windows 안내도 PowerShell 문맥에 `%USERPROFILE%` 표기가 섞여 있습니다. macOS 실기 검증은 이번에 하지 못했습니다. [실행 코드](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/scripts/studio.py:50), [설치 안내](C:/Users/User/Downloads/teacher-studio-codex/INSTALL.md:39) |
| 샌드박스·네트워크 | 현재 진단은 설정 파일의 `network_access = true` 한 줄을 보고 판단합니다. 실제 쓰기 권한, 셸 네트워크, 웹 검색은 따로 확인해야 합니다. 기본 출력 위치인 `~/TeacherStudio`도 작업 폴더 밖일 수 있습니다. [진단 코드](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/scripts/doctor.py:85), [출력 위치](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/scripts/studio.py:37), [공식 권한 설명](https://learn.chatgpt.com/docs/sandboxing) |
| Codex 플러그인 | 현재 manifest에는 `author`와 `interface`가 없습니다. 현재 공식 Codex 배포 형식에서는 필요한 항목이므로, 폴더 복사 설치와 플러그인 설치의 지원 상태를 구분해야 합니다. [현재 manifest](C:/Users/User/Downloads/teacher-studio-codex/.codex-plugin/plugin.json), [공식 배포 형식](https://developers.openai.com/plugins/deploy/submission) |
| Claude 전용 가정 | 문서 스킬 이름·검색 경로, ‘게시’ 버튼 안내, 평가 프롬프트에 남아 있습니다. 특히 문서의 `find_skill()`은 `.claude`만 검색합니다. [문서 탐색 코드](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-docs/scripts/docs.py:39), [환경별 안내](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/references/studio-details.md), [평가 프롬프트](C:/Users/User/Downloads/teacher-studio-codex/tools/router_eval.py:101) |

**우선순위 10개입니다.** ‘바로 구현 가능’은 독립적인 패치로 진행할 수 있다는 뜻이며, 이번 검토에서 구현했다는 뜻은 아닙니다.

1. **배포 ZIP이 원본과 다르면 출시를 막기 — [안전·독립적으로 바로 구현 가능]**

   직접 대조한 결과, **ZIP 8개 중 `teacher-law.zip`을 제외한 7개가 현재 스킬 폴더와 달랐습니다.** 폴더 설치와 ZIP 설치가 다른 동작을 제공하는 상태입니다. 이미 있는 `sync_shared.py --check`를 출시 필수 조건으로 연결하면 됩니다. ZIP 재생성은 다른 팀의 변경을 합친 시점에 함께 처리해야 합니다. [기존 일치 검사](C:/Users/User/Downloads/teacher-studio-codex/tools/sync_shared.py:188), [배포 파일](C:/Users/User/Downloads/teacher-studio-codex/dist/teacher-game.zip)

2. **‘검사 완료’와 ‘검사 못 함’을 구분하기 — [안전·독립적으로 바로 구현 가능]**

   브라우저가 없어 자동 실행을 건너뛰어도 최종 `PASS`가 나올 수 있습니다. 더 직접적인 문제는 디자인 검사가 `FAIL`이어도 종료값이 0이고, 빌더는 그 결과와 무관하게 `READY`를 출력할 수 있다는 점입니다. 결과를 `PASS / PARTIAL / FAIL`로 구분하고, 실행하지 않은 검사는 ‘미확인’으로 남겨야 합니다. 결과물 생성은 계속할 수 있어도 검증 완료라고 표시해서는 안 됩니다. [실행 생략 처리](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-game/scripts/check_game.py:288), [디자인 검사 종료값](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-game/scripts/design_review.py:539), [READY 판정](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-game/scripts/build.py:364)

3. **환경 확인을 실제 기능 기준으로 바꾸기 — [안전·독립적으로 바로 구현 가능]**

   설정 파일의 문자열 대신 **실행기, 허용된 출력 폴더, 브라우저 실행, 셸 네트워크, 웹 검색, 미리보기·공유 기능**을 각각 판별해야 합니다. 판별하지 못하면 ‘모름’으로 표시해야 합니다. 현재처럼 네트워크 설정만 바꾸면 해결된다고 안내하면 읽기 전용·관리형 환경에서 계속 막힙니다. 설치된 스킬도 폴더 이름 추측보다 호스트가 제공한 목록을 우선해야 합니다. [현재 진단](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/scripts/doctor.py:109), [공식 기능 분리](https://learn.chatgpt.com/docs/sandboxing)

4. **설치 실패 시 기존 설치를 보존하기 — [안전·독립적으로 바로 구현 가능]**

   설치기는 기존 폴더를 먼저 지우고 새 폴더를 복사합니다. 중간 실패 시 기존 설치까지 잃을 수 있습니다. 임시 폴더에 복사·검증한 뒤 교체하고 실패하면 복구하도록 바꾸는 편이 안전합니다. 또한 설치·환경 확인 명령의 실패를 최종 종료값에 반영하고, `--video`는 기존 Chrome과 공용 설치 도우미를 재사용하도록 통일해야 합니다. 현재 별도 경로는 Chromium을 설치하고 `--break-system-packages` 재시도도 합니다. [설치 교체](C:/Users/User/Downloads/teacher-studio-codex/scripts/setup.py:33), [영상 설치](C:/Users/User/Downloads/teacher-studio-codex/scripts/setup.py:50)

5. **분명한 요청은 완성까지 진행하고, 기본 모델의 도구 사용을 보존하기 — [안전·독립적으로 바로 구현 가능]**

   현재는 분명한 게임·영상 요청도 ‘알아서’ 같은 표현이 없으면 콘티에서 멈춥니다. `ask-first.md`의 “분명하면 만들라”는 지시와도 충돌합니다. 또한 ‘하네스 없이’ 경로의 **“no tools”는 일반 모델이 원래 쓰던 도구까지 금지**합니다. 분명한 요청은 가정을 밝히고 제작까지 진행하고, 대체 경로에서도 기존 스킬·검색·검사 도구를 사용할 수 있어야 합니다. [입구 규칙](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/SKILL.md), [먼저 묻기 규칙](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/references/ask-first.md)

6. **Codex 평가기의 구체적인 오류부터 고치기 — [안전·독립적으로 바로 구현 가능]**

   `--trigger` 평가에서 Claude에는 전용 응답 형식을 주지만, Codex에는 일반 라우팅 형식을 줍니다. 평가 문맥도 “You are Claude Code”로 시작합니다. 따라서 지금 코드는 Codex의 스킬 선택을 공정하게 평가하지 못합니다. 이를 고친 뒤에는 JSON으로 “하겠다”고 말하는 평가와, 실제 스킬 선택·명령 실행·완성 파일을 보는 평가를 분리해야 합니다. [평가 문맥](C:/Users/User/Downloads/teacher-studio-codex/tools/router_eval.py:90), [Codex 호출](C:/Users/User/Downloads/teacher-studio-codex/tools/router_eval.py:223), [공식 스킬 평가 안내](https://developers.openai.com/blog/eval-skills)

7. **자료 분석의 경계값과 출력 범위를 바로잡기 — [안전·독립적으로 바로 구현 가능]**

   정적 분석상 상수열의 상관계수는 `0`, 집단 내부 값이 일정한 경우의 검정은 `p=1`로 처리됩니다. ‘계산 불가’를 ‘관계없음·차이없음’으로 바꾸지 않아야 합니다. 상수열·빈 집단·결측값·극단적인 수치를 기준값과 대조하십시오. 별도로 `profile_data.py`는 마스킹한 3행을 출력하므로, ‘집계만 전달’이라는 약속에 맞추려면 기본 출력에서 개인별 행을 제외해야 합니다. [통계 계산](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-data/scripts/tdata.py:335), [행 출력](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-data/scripts/profile_data.py:40), [상수열 처리의 공식 참고](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)

8. **오래된 Chrome 지원을 실제 문법 검사로 확인하기 — [안전·독립적으로 바로 구현 가능]**

   현재는 금지 문법을 정규식으로 찾고, 벤더 코드 대부분은 검사 대상에서 제거합니다. 이것만으로 ES2017 지원을 보증할 수는 없습니다. Acorn으로 모든 실행 스크립트를 `ecmaVersion: 2017` 기준으로 검사하고, `.at()` 같은 실행 기능은 별도 점검해야 합니다. 지원하는 최소 Chrome 버전도 숫자로 명시해야 합니다. [현재 검사](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-game/scripts/check_game.py:399), [Acorn 공식 옵션](https://github.com/acornjs/acorn/tree/master/acorn)

9. **외부 스킬 검증 결과에 실제 확인 범위를 기록하기 — [안전·독립적으로 바로 구현 가능]**

   `skill_scout.py verify`는 저장소 메타데이터와 루트 `SKILL.md`·`README.md`를 확인합니다. 실제 하위 스킬의 LICENSE와 스크립트 전체를 검사하는 것은 아닙니다. ‘확인한 파일 0개’도 안전 확인처럼 보이지 않게 해야 합니다. 사용한 정확한 버전·커밋·라이선스 원문·확인한 파일을 기록하고, 설치 패키지의 버전도 고정해야 재현성이 생깁니다. [현재 검증 범위](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-studio/scripts/skill_scout.py:140), [버전 없는 설치 목록](C:/Users/User/Downloads/teacher-studio-codex/shared/tools/ensure.py:41)

10. **슬라이드·문서·학습 자료의 완료 기준을 담당 팀과 통일하기 — [제안만]**

    현재 슬라이드와 문서도 실패 종료값을 반환하면서 `READY`를 출력하는 경로가 있습니다. 담당 팀에 완료 표시 통일을 제안합니다. 근사 미리보기와 실제 사용 프로그램에서 확인한 결과도 구분해야 합니다. 학교명·실제 행사일·경비처럼 근거가 필요한 값은 빈칸 검사를 통과하려고 채우지 않도록 해야 합니다. `docs/training`에는 같은 모델·권한·도구 조건에서 일반 실행과 하네스 실행을 비교한 실제 산출물, 새 시험 사례, 반복 결과를 추가하는 방향을 제안합니다. [슬라이드 완료 표시](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-slides/scripts/deck.py:320), [문서 완료 표시](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-docs/scripts/docs.py:176), [기존 평가의 한계](C:/Users/User/Downloads/teacher-studio-codex/docs/research/ceiling-eval-2026-11/README.md)

**추가 도구·스킬·재료는 아래 후보를 권합니다.** Claude보다 우월하다는 비교 실험을 한 것은 아닙니다. 현재 코드에서 확인한 빈틈에 맞춰 선정했으며, 신규 후보는 요청한 허용 라이선스에 한정했습니다. 모두 도입 전 소규모 비교가 필요한 제안입니다.

| 후보 | 라이선스 원문 | 적용할 곳과 기대 효과 |
|---|---|---|
| **Acorn** | [MIT](https://github.com/acornjs/acorn/blob/master/acorn/LICENSE) | 정규식 중심의 JavaScript 문법 검사를 보완합니다. 배포 결과물에 넣을 필요 없이 개발 검사에 사용합니다. [공식 사용법](https://github.com/acornjs/acorn/tree/master/acorn) |
| **fast-check** | [MIT](https://github.com/dubzzz/fast-check/blob/main/LICENSE) | 클릭·일시정지·재시작 순서를 다양하게 시험하고, 실패한 순서를 작게 줄여 재현할 수 있습니다. 자동 정답 진행만으로 놓치는 상태 오류를 찾는 후보입니다. [공식 시험 방식](https://fast-check.dev/docs/advanced/model-based-testing/) |
| **Microsoft Playwright CLI + 스킬** | [Apache-2.0](https://github.com/microsoft/playwright-cli/blob/main/LICENSE) | Python 경로 외에 Node 기반 브라우저 검사 경로를 마련하는 후보입니다. 이미 제공되는 브라우저 도구가 있으면 먼저 재사용하십시오. [공식 저장소·요구 조건](https://github.com/microsoft/playwright-cli) |
| **mpmath** | [BSD-3-Clause](https://github.com/mpmath/mpmath/blob/master/LICENSE) | 직접 구현한 불완전 베타 함수 등의 계산을 높은 정밀도로 대조하는 개발 검사 후보입니다. 사용자용 결과물에는 포함하지 않아도 됩니다. [공식 수학 함수](https://mpmath.org/doc/current/functions/gamma.html) |
| **Jua 글꼴** | [SIL OFL 1.1](https://github.com/google/fonts/blob/main/ofl/jua/OFL.txt) | 현재 ‘고딕 굵게’로 처리하는 둥근 글꼴 선택을 실제 자산으로 구현하는 후보입니다. 공용 디자인·글꼴 처리에 연결하고 가독성을 확인해야 합니다. [현재 처리](C:/Users/User/Downloads/teacher-studio-codex/skills/teacher-game/scripts/build.py:184) |
| **Poly Haven 소재** | [CC0](https://polyhaven.com/license) | 주제에 맞는 질감·배경 소재 후보입니다. 작은 정적 그림으로 가공해 파일 안에 넣는 방식부터 비교하고, 큰 원본이나 실행 중 외부 요청은 추가하지 않는 편이 현재 구조에 맞습니다. [소재 범위](https://polyhaven.com/about-contact) |

현재 들어 있는 벤더 9개의 코드 해시는 manifest와 일치했습니다. 따라서 기존 자산을 대거 교체하기보다 위의 결함을 먼저 고치는 순서가 적절합니다. 신규 도입 시에는 저장소 규칙대로 실제 배포 패키지의 LICENSE와 필요한 부속 라이선스까지 확인해야 합니다. [벤더 기록](C:/Users/User/Downloads/teacher-studio-codex/shared/vendor/manifest.json), [저장소 규칙](C:/Users/User/Downloads/teacher-studio-codex/AGENTS.md)

“하네스 없는 모델보다 절대 나쁘지 않게”는 **같은 모델의 기본 도구 사용을 보존하고, 불리한 경로에서는 빠르게 대체하며, 실제 결과의 퇴보를 출시 전에 잡는 기준**으로 구체화하는 것이 좋습니다. 다음 평가는 동일 모델·동일 권한·동일 도구로 일반 실행과 하네스 실행을 짝지어 반복하고, 완성률·내용 정확성·수정 횟수·시간·비용을 함께 기록하도록 제안합니다. 기존 점수와 새 버전의 효과를 분리하고, 규칙을 고칠 때 보지 않은 요청도 포함해야 합니다. [기존 라우터 평가의 한계](C:/Users/User/Downloads/teacher-studio-codex/docs/research/router-eval-2026-11.md), [공식 평가 안내](https://developers.openai.com/blog/eval-skills)