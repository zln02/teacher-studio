# Changelog

## [Unreleased]
### Summary (7 skills, 7 zips)
- **스킬 7개**: `teacher-studio`(첫 관문·라우터) · `teacher-game` · `teacher-slides`(spec 기반으로 전환) · `teacher-motion` · `teacher-law` · `teacher-class-tools`(타이머·뽑기·모둠·대진표·점수판) · `teacher-data`(엑셀·CSV 분석 보고서). `dist/`에 zip 7개, `tools/sync_shared.py --check`가 공용 복사본·zip을 모두 검사
- **공용 도구함 확장**: `shared/juice`(Game Wow 키트: 게임 + 수업 도구), `shared/tools/video_eyes.py`(영상 → 장면 사진, 로컬 전용), `shared/vendor/qrcodegen`, `shared/design/styles.py`
- **첫 관문 규칙**: 먼저 묻기(`ask-first`), 막연한 불평 자동 진단(`diagnose.py`), 스킬 스카우트, 참고 사이트 패턴 분석(`ref_analyze.py`), 첫 설정 기억(`prefs.py`), 무손실 원칙. 모든 스킬: 「선생님과 누구나」, 사용자 언어로 답하고 사용자가 준 양식·참고가 먼저 (사용자 양식으로 만드는 도구는 아직 계획)
- `teacher-data` 문구 정리: 점수대 그래프 설명이 설문 문구를 쓰던 것 수정, 「가장 높은 A와 가장 낮은 B의 차이」처럼 두 곳을 밝힘, 소수 자릿수 통일(-0.4점, 6.0점)
- `docs/training/deck.json`을 새 슬라이드 spec으로 다시 만듦(21장, 점검 통과)

### 공정 비교에서 찾은 것 고치기 + 주인 결정 (2026-11-23)
- **문서**: 절 내용을 `items`·`table`·`text`로 써도, `lead`를 목록으로 써도 빠지지 않음. 제목 번호 두 번(「1. 1.」) 없앰. 점검기에 **내용 보존 검사**(spec의 문장·항목·표 칸이 HWPX/PDF/DOCX 글에 다 있는지), 넣지 못한 칸·목록 기호 노출·이중 번호 = FAIL.
- **게임**: 모둠 2~6개(6모둠 한 줄 배치). 장식(소품·사회자·간판·말풍선)이 글자·보기·위쪽 표시에 겹치면 비켜서거나 안 그리고, 점검기는 겹침을 FAIL로 잡음. 우리가 고른 배치가 겹치면 다른 배치로 최대 3번 다시 만듦.
- **먼저 묻기**: 결과를 바꾸는 사실(안내문·행사·여행의 날짜, 모둠 수, 누가 보는지)이 요청에 없으면 「알아서」여도 1~2개를 한 번에 물음. 이름이 있는 문서·페이지 요청은 막연한 요청으로 보지 않음.
- **전달 메뉴 항상**: 「✅ 다 만들었어요! 어떻게 받으시겠어요? (추천: …)」 ① TV·화면 ② 단톡방·메신저 ③ 학생 태블릿 ④ 인쇄·PDF ⑤ 고쳐 쓸 파일(한글·PPT), 추천은 이미 만들어 둠, 공유 전 개인정보 확인 유지 (`deliver.py`).
- **가벼운 길**: 단순한 페이지·짧은 글은 바로 만들고 `light_check.py`(개인정보·빈칸·오프라인·옛 크롬)와 전달 메뉴만 (`references/light-path.md`).
- **새 틀**: teacher-motion `event-promo`(행사 오프닝·홍보 30초, 그림 없으면 그려 넣음, MP4), teacher-class-tools `"tool": "set"`(뽑기·모둠·타이머를 탭으로 한 페이지).
- **영상 요청 참고**: `teacher-motion/references/motion-prompts.md` (awesome-opus5-5-videos, MIT, 우리 말로 고쳐 씀, NOTICE 24).
- 시험 `tools/test_compare_bugs.py` · `test_owner_rules.py` · `test_new_builders.py`.

### 하네스 업그레이드 E (2026-11-22, 11/23 연수 덱에서 배운 것 되돌려 넣기)
- **프리셋 E 「잉크 포스터」** (`shared/design/preset_e.py`, 스타일 `ink-poster`, 13번째 스타일): 먹 #121214 · 종이 #F0EDE6 · 주홍 #E4502F(강조 하나) · 코발트(먹 위 글자 #6F74FF) · 회색 · 라임(정답 표시만). 어두운 판·밝은 판 글자 대비 모두 점검(`--check`, 주홍은 종이 위 큰 글자만), 12칸 격자(`swiss`), 글자 크기표(바닥 28px), 카드 6가지(평평 · 1.5px 선 · 모서리 12), 움직임 값. 장식 `hud` 추가. 슬라이드 연수·발표 후보에 들어가고(「강렬하게」「임팩트」「키노트」), 게임 `body[data-style=ink]`, 껍데기 키트·방향 카드에도.
- **움직임 낱말** (`shared/design/motion_e.js`, ES2017, 라이브러리 없음): 큰 글자(음절 45ms) · 펜 긋기(글자를 찾아 동그라미·밑줄·상자·화살표 + 메모) · 단계 알약 · 낱말 밝히기 · 주홍 점 → 밑줄 · HUD 틀 · 끌어다 놓기 커서 장면(맞춤선, 끝은 진짜 결과) · 시연 커서. 클릭으로 진행, 뒤로·인쇄·`?static=1`·움직임 줄이기 = 끝 모습. 슬라이드 런타임(`deck.js`)이 단계마다 부름; 프리셋 E에서는 큰 글자를 핵심 문장 장(표지·섹션·한 문장)에만.
- **고명(garnish)** (`shared/design/garnish.py`): 환경 확인(`env`), 같은 화풍 바탕 2~3장 계획(`plan`, 글자·로고·얼굴 없음, Codex 명령은 선택: `codex exec --skip-git-repo-check -s workspace-write [-i ref.png] -- "<prompt>"`), 압축 + 프롬프트 기록(`finish`), Claude만 있을 때 코드로 그린 바탕(`svg_backdrop`), 글 많은 장은 생략(`skip_reason`). 슬라이드 spec `"garnish"`, 장마다 `"backdrop"` `"pen"` `"pills"`.
- **내용 규칙** (`teacher-slides/references/content-slides.md` 「Scene rules」, 게임·영상·웹 앱 안내에도): 큰 글자는 핵심 장만, 한 장면 한 생각, 작은 글 카드보다 그림, 비유는 진짜 화면 먼저, 같은 판 여러 번 대신 이름표 바꾸기, 근거 숫자는 그대로, 커서 장면은 진짜 결과로 끝내고 속도 주장 금지. 공정표에 「고명」 단계.
- **작은 글씨 자동 고침**: `slides_review.py --fix-small`(빌드가 기본으로 씀)이 바닥보다 작은 글씨를 그 자리에서 키우고 다시 점검, 넘치면 장 번호와 함께 FAIL.
- **고침**: 공공·홍보 덱의 「예시 값 안내」 발표자 메모를 빈칸 점검이 빈자리로 잘못 잡아 `NOT DONE`이 나던 것(빌드·리뷰 둘 다).
- **방향 질문**: `direction.py`가 요청 말에서 일상·업무·수업을 가려 기본 답을 맞춤(「교직원 회의」 → 회의·보고 / 동료·직원, 「가족 여행」 → 모임·행사 / 가족). 아무 단서가 없으면 셋을 다 보여 줌.
- **개발 도구** `tools/ref_frames.py`: 참고 영상(파일·주소) → 촘촘한 장면 사진 한 장(Playwright Edge, 찾아가서 찍기, Pillow 접촉 시트, ffmpeg 없음).
- 시험 `tools/test_harness_e.py` (19개).

### 남은 일 6가지 (2026-11-21, `docs/research/leftovers-2026-11.md`)
- **뜻이 있는 색**: 「초록불」「빨간불」「청팀·백팀」「금·은·동」처럼 낱말이 색 이름이면 그 색으로 칠한다 (`shared/design/meaning.py`). PPT·웹 슬라이드의 비교 칸·목록·단계·보기·카드·강조한 낱말, 게임 분류 통, 점수판·모둠 카드·시상식. 옆 칸은 비슷한 색을 피한다. PPT 점검기는 다른 색으로 칠한 색 낱말을 WARN으로 알린다.
- **장수**: `target_slides`는 「N장」에 맞춘다. 정답 장 한 장만 N+1장째로 받아들이고, 그 밖에 넘거나 모자라면 `WARN 장수:`, 많이 넘으면 전처럼 멈춘다.
- **예시 안내 한 번**: 출처·주석 줄 두 곳 이상에 「가상」「예시」를 쓰면 조립이 멈추고 고치는 법을 알려 준다(출처에는 자료 이름만, 안내는 첫 장 발표자 메모 한 줄). 넣어 둔 보고 예시 2개도 규칙에 맞게 고침. 예시 안내를 세는 점검이 「수치는 예시」 같은 말도 센다.
- **HTML 결과물의 빈칸 점검**: 게임·웹 앱·수업 도구·웹 슬라이드 점검기가 「확인 필요」 빈말(1~2곳 WARN, 3곳 이상 FAIL), 「교사 초안」 도장(FAIL), `[학교명]`·`○○초`·`20XX` 빈자리(FAIL), 되풀이한 예시 안내(WARN)를 본다 (`placeholders.html_checks`). 빈칸 채우기 문제의 `○○`, 대진표의 「미정」, 입력칸 안내는 세지 않는다.
- **게임 배치**: 배치 가중치를 실제로 잰 겹침 순서로 바꿈(겹침이 큰 `split`·`bento`·`poster`는 덜, `left`·`right`·`stair`·`stack`은 더). 배치의 자리와 크기는 그대로. 서로 다른 요청 0.502 → 0.467(시드 1~3) · 0.480(시드 4~6).
- **Python 부르기**: 모든 스킬이 「짧은 이름으로(`py`, 없으면 `python`; macOS·Linux는 `python3`), 전체 경로는 쓰지 않는다」를 같은 문장으로 말한다. 측정용 허용 목록은 같은 프로그램의 전체 경로도 받는다(`blanks-policy-2026-11/bp_eval.py`).

### 모르는 값은 예시로 채우고, 손으로 쓰는 곳만 빈칸 (2026-11-21, `docs/research/blanks-policy-2026-11.md`)
- **빈칸 규칙을 하나로**: `CONTENT-RULES.md`의 「Release status(교사 초안)」 절을 없애고 「Unknowns」 절로 바꿈. 사용자가 준 사실은 그대로, 주지 않은 날짜·장소·금액은 그럴듯한 예시 값, 회신서·신청서·서명란만 빈칸, 예시 안내는 파일마다 한 줄, 마지막 안내에 「바꿔 넣을 곳」 전부. 「확인 필요」 칸과 「교사 초안」 도장은 쓰지 않음. 「빈칸으로 둬」는 사용자 말이 먼저.
- 문서·슬라이드·첫 관문 스킬과 내용 규칙 글의 서로 다른 문장을 이 규칙으로 맞춤. 문서 스킬의 「알아서」 줄을 PDF 절 밖으로 옮겨 한글·워드에도 적용.
- **도구**: spec의 `fillins`가 있으면 문서는 본문 맨 아래, PPT는 첫 장 발표자 메모에 예시 안내 한 줄을 넣고 목록을 출력 (`"example_note": false`로 끔).
- **점검**: 「확인 필요」 같은 말 3곳 이상 FAIL(1~2곳 WARN), 「교사 초안」 도장 FAIL, 예시 안내 없음·반복 WARN, 답을 요구하는 가정통신문에 회신서 없음 FAIL(`"reply": false`로 밝히면 통과), 회신서 밖 밑줄 빈칸 WARN. 새 시험 `tools/test_unknowns_policy.py`.
- 처음 쓰는 과제 4개로 잰 결과: GPT 일반 3.48 대 스튜디오 3.85(6승 2패), Claude 3.77 대 3.48(실행 하나가 측정용 허용 목록에 막혀 파일 없음. 빼면 3.72 대 3.83). 스튜디오 결과물에 「확인 필요」·「교사 초안」 0번, 회신서·신청서 빠짐 0번.

### GPT(Codex)에서도 손해 보지 않게: 보안 상자 안에서 도는 도구, 「도구는 바닥」 (2026-11-21, `docs/research/cross-vendor-fix-2026-11.md`)
- **임시 폴더를 쓰지 않는다**: 모든 스크립트가 `tempfile`의 전용 폴더 대신 `shared/tools/workdir.py`를 쓴다 (결과 파일 옆 `.teacher-studio-work/` → 지금 폴더 → 시스템 임시 폴더 → `~/.teacher-studio/tmp`, 끝나면 지움. `TEACHER_STUDIO_TMP`로 위치 지정). Windows의 Python 3.12.4+가 만든 전용 임시 폴더에는 Codex 보안 상자가 쓰지 못해, 게임·PPT 만들기가 멈추던 문제.
- **설치기**: `setup.py`가 스킬을 전용 임시 폴더에서 준비해 옮기던 탓에, Windows에서 설치된 스킬 폴더를 Codex 보안 상자가 읽지 못했다. 보통 폴더에서 준비하도록 고침. **이전에 Windows에서 `--agent codex`로 설치했다면 한 번 다시 설치.**
- **화면을 못 띄우는 곳**: 스크립트가 바로 알아채고 `NO-BROWSER` 한 줄만 말한 뒤 브라우저 없이 되는 점검으로 넘어간다. PPT는 Pillow로 그린 밑그림(`pptx_sketch.py`, `-sketch-sheet.png`)을 낸다. `TEACHER_STUDIO_NO_BROWSER=1`로 같은 길을 시험.
- **도구는 바닥이지 천장이 아니다**: `CONTENT-RULES.md`에 「Floor, not ceiling」 절. 게임·슬라이드·수업 도구·웹 앱·문서 스킬 글에서 「도구가 정한 모양만」「최소 구성」으로 읽히던 줄을 고침 (주제 그림·사료·여러 단계·확인 문제 여럿은 더 넣고, 도구에 자리가 없으면 직접 만들어 같은 점검기에 통과).
- 「확인 필요 · 교사 초안」 규칙은 이때 바꾸지 않음 (위 「모르는 값은 예시로」 항목에서 바꿈).
- 다시 잰 결과(같은 과제 6개, GPT): 일반 3.69 대 스튜디오 3.71 (고치기 전 3.80 대 3.40). 게임·수업 도우미·대진표는 이기고, 수업 PPT·가정통신문·보고 PPT는 아직 진다. Claude는 3.65 대 3.68로 그대로.

### PPT를 일반 AI만큼: 한 장에 근거 여럿, 결론 띠, 주제 그림 (2026-11-21, `docs/research/ppt-win-2026-11.md`)
- **`panel` 장**: 주장 하나 + 근거 2~4개(숫자 카드·머리말 카드·목록·그래프·표·강조 한 줄·흐름·조직도·그림)를 한 장에. 배치는 내용에서 정해지고, 블록이 읽기 어려운 크기로 눌리면 만들기를 멈춘다. 웹 화면과 PPT 모두.
- **`takeaway`**(장 아래 결론 띠), `diagram`의 `poly`·타원, 표지 그림(`title.shapes`), 강조색을 번갈아 쓰는 두 색, 수업·홍보의 더 큰 글자.
- **다시 만들어도 같은 모양**: 같은 spec 파일을 다시 만들면 처음 모양 유지(`--fresh`가 새 모양). PPT가 웹과 같은 스타일을 씀.
- **점검**: 글머리표 쏠림·같은 종류 반복·결론 없는 자료 장 알림, 어떤 pptx든 10pt 미만 글자 FAIL, 요일이 틀린 날짜는 만들기 중단, 미리보기 브라우저는 한 번에 하나, x·y 그래프도 미리보기에 그림.
- 고친 것: 바탕과 같은 색 카드의 테두리, 표지 장식이 제목을 가리던 것, 홍보 표지 문구 두 번 찍힘.
- **새 주제 10개 측정**(Sonnet, 주제마다 2회, Opus 익명 A/B): 평균 일반 AI 3.85 / 스튜디오 3.86, 최악 2.50 / 3.12, 맞대결은 일반 AI 25 대 스튜디오 15. 내용·적합성은 스튜디오, **디자인은 일반 AI(4.33 대 3.62)**. 수업·홍보 PPT는 아직 진다.

### 틀 걷어 내기: 예시는 시험용 파일로, 뼈대는 내용에서 (2026-11-20, `docs/research/template-removal-2026-11.md`)
- **내용 레시피 연결**: SKILL.md 6개에 「Content quality first」 줄, `shared/content/`가 스킬 안으로 복사됨(`tools/sync_shared.py`).
- **예시 = 시험용 파일**: 예시 42개에 `"_fixture"` 표시, 게임 예시의 `design.seed` 삭제, 스킬 문서의 「가장 가까운 예시를 복사」 지시 삭제, 수업·기관 보고 레시피의 고정 순서와 단원 예시를 「할 일 + 내용 모양 → 장 종류」로 교체. 제목의 낱말(「퀴즈쇼」「세포」)만으로 옛 장면 테마가 통째로 불리던 것을 모양 낱말로 지목했을 때만 불리게 함.
- **「예시를 그대로 따라간 것 같아요」 WARN**(`shared/tools/example_likeness.py`): 예시 문장 60% 이상, 같은 차례 + 같은 제목, 장마다 같은 뼈대. 게임·발표·프로그램 점검기와 발표·문서 조립기에서 돎.
- **발표 장 종류를 내용 모양에서**: `"type": "auto"` → `scripts/deck_shape.py`가 quiz·table·timeline·bignumbers·compare·statement 등으로 정하고, 글머리표 장이 사실은 순서·날짜·수치면 NOTE.
- **게임 문제 화면 배치 5종 → 덮는 자리가 다른 10종**(`column` · `left` · `right` · `rail` · `stair` 추가, `news`는 아래쪽, `poster`는 위쪽 띠). 고르는 열쇠에 요청 지문을 섞음. 닮음 점수(`tools/game_sameness.py`, 18판): 서로 다른 요청 0.671 → **0.502**, 같은 요청 다른 시드 0.701 → **0.554**.
- **끌지 않는 길**: 엔진의 `NG.drag` · `NG.button`에 키보드(Tab · Enter)를 넣음. 분류 게임은 숫자 키 1~4와 통 번호 표시.
- **Chart.js가 ES2017로 읽힘**: 클래스 필드 81곳 · 객체 펼침 6곳을 같은 뜻의 옛 문법으로 바꿈(`tools/es2017_static_fields.js`, `NOTICE` 5번). 차트가 든 발표 3개의 「JavaScript syntax」 FAIL이 사라짐.

### 디자인 시스템 개편: 「밤티」 걷어 내기 (2026-11-20, `docs/research/design-overhaul-2026-11.md`)
- **글꼴**: 모든 무기의 기본 글꼴이 **TS Sans**(Pretendard 1.3.9를 잘라 이름을 바꾼 것, OFL)로. 파일 안에 들어가서 인터넷 없는 교실에서도 같은 글꼴. 예전 제목 글꼴(Black Han Sans·Jua·Do Hyeon)은 파일에 안 들어 있어 오프라인에서 바뀌던 문제도 같이 없어짐
- **시스템 한 곳**: `shared/design/system.py`(글자 크기 단계·크기별 자간/줄 간격/굵기·8pt 여백·이름 있는 격자 6개·OKLCH 색 사다리·장식 7가지·움직임 값) + 규칙 문서 `shared/design/DESIGN-RULES.md`(규칙 27개, 스킬 문서마다 한 줄 링크)
- **스타일 12개를 뼈대로**: 격자·글자 처리·모서리·장식 둘·배경이 서로 다름. 네온 격자 → 「먹빛 테크」, 금색 보케 → 「먹과 놋쇠」, 유리 방울 → 「소프트 뎁스」, 무대 조명 → 「스튜디오 쇼」(id는 그대로라 옛 스펙도 만들어짐). 팔레트는 주 색 하나 + 보조 색 하나 + 회색 사다리, 형광 0개, 정답·오답은 색약에도 구분
- **밤티 검사**(`ai_look.py`): 빛 번짐·속 빈 글자·여러 색 그라데이션·강조색 수·형광·제목 이모지·굵기 900·여백 격자·장식 겹·글꼴 수·기울임·줄 간격 → 「전문 디자이너 기준 n/5」. WARN만, 사용자가 준 디자인이면 검사하지 않음
- **템플릿 느낌 줄이기**: 게임 문제 화면 배치를 내용(OX 비율·보기 길이·문제 길이·그림)으로 고르고 같은 요청도 시드가 다르면 다른 뼈대. 프로그램(webapp)은 배치 6종 + 머리 3종(예전에는 한 가지)
- 적용: 게임(공통 마감 층·스타일 묶음·배경 8종·옛 장면 테마와 스킨의 형광/빛 번짐 제거), 발표, 껍데기 키트·콘티·방향 카드, 프로그램, 수업 도구·데이터 보고서, 안내문 PDF(제목 띠 → 강조 줄 + 고딕 제목)

### 일반 AI에 진 곳 고치기: PPT·PDF (2026-11-20, `docs/research/ceiling-eval-2026-11/rerun-ppt-pdf.md`)
- **원인**: sonnet 스튜디오의 PPT 두 건은 우리 슬라이드 도구를 쓰지 않았다(`teacher-slides` 설명에 PPT·파워포인트가 없어 계정 기본 pptx 스킬로 감). 설명을 「PPT / PowerPoint (.pptx)…before any generic pptx skill」로 고침.
- **빈칸**: `placeholders.py`가 `(학교명 입력)`·`(…을 입력하세요)`·`○○학교`·`△△부`·`OOO`·`(예시)`·`(미정)`·`<학교명>`·`00월 00일`도 잡음 (손으로 쓰는 밑줄 칸 `교사: ______`는 빈칸으로 보지 않음). 모르는 값은 빼거나 「우리 학교」·오늘 날짜로 채우고 한 줄로 알림.
- **끝까지 고치기(hard gate)**: `deck.py --pptx`·`pptx_check.py`·`docs.py make`가 FAIL이면 `READY` 대신 `NOT DONE`을 찍고, 스킬 문서의 마지막 단계가 PASS까지 다시 돌리기. PPT만 필요하면 `--pptx-only`(웹 덱 점검 생략).
- **비어 보이는 장**: `pptx_fill.py`(내용이 화면의 6% 미만이거나 위 60%에서 끝나면 FAIL), `deck_pptx.py` 글머리·표·요약·단계·연표·비교 칸이 본문을 채우도록 손봄.
- **미리보기**: `pptx_draw.py`·`pptx_chart.py`가 pptx XML에서 선·화살표·그림·표·차트·묶음·마스터 도형·글자 모양을 그림(LibreOffice 없이). 어떤 pptx든 같은 눈으로 비교 가능.
- **내용**: 새 장 종류 `diagram`(선·화살표·도형·각 표시·이름표: 웹은 SVG, PPT는 진짜 선), 마무리 앞에 「확인 문제 정답」 장 자동 추가, 수업용·기관 보고용 구성 안내와 점검 문구(확인 문제 2개·활동·그림, 표·그래프·일정). 화살표 글자(→)가 지워지던 버그 수정. 예시 `class-light-reflection.json`.
- **문서/PDF**: `design.font_size`(pt 인쇄 배율), `{"pagebreak"}`·`{"image"}`·`{"qr"}`·`{"form"}` 블록, `kind:"form"`(신청서), 안내문 `reply`(+`"page": true`), `max_pages`(조금 줄여 맞춤)·`min_font`, 쪽수·쪽별 채움·가장 작은 글자 점검(`doc_look.py`), 모든 쪽을 한 장에 모은 `*.preview.png`, 한 줄 명령 `docs.py append 원본.pdf --spec 신청서.json --out 새.pdf`. 안내문·신청서 PDF 제목 띠.
- 다시 잰 결과(sonnet, 같은 미리보기): PDF 3.00 → 4.62(일반 AI 4.25), 수업 PPT 3.25 → 4.62(4.88), 공공 보고 PPT 3.25 → 3.50(3.88). 한 곳만 뒤집혔고 PPT 두 곳은 아직 근소하게 아래. `target_slides`(요청 장수의 1.25배를 넘으면 멈춤), 「확인 문제 정답」 한 장, 공공용 머리 띠.
- 시험 `py tools/test_ppt_pdf_rerun.py`(19개).

### Testbed fixes (2026-11-19, `docs/research/testbed-fix-2026-11.md`)
- 폰 세로 화면(quiz): 600칸 세로 무대 + 폰 점검(390×844·844×390, 글자·넘침·버튼 44px). 기본 오프라인(바깥 주소 FAIL, `online:true`만 허용). 스타일은 words가 제목보다 우선 + `--spec` 미리 보기. `color_from.py` 여러 파일·이름 있는 색. `design.font`, 비네트 밝기별. `direction.py` 폰 인식. 라우터 새 게임은 spec→build. 제작 공정표 번호 규칙(haiku 0.81→1.0). `teacher-data` 설명 YAML 복원 + `sync_shared --check` 설명 검사.

### Added
- **활용·전달 단계 (선생님은 「수업 활용」)**: 만든 뒤 마지막에 「어떻게 쓰실 건가요? (추천: …)」 한 번만 묻기(말했으면 안 묻고, 「알아서」는 TV·화면 + PDF). 선생님(교실 TV·태블릿·인쇄·클래스룸·가정 발송·보관)과 누구나(회의실 화면·카톡·인쇄·SNS·드라이브·보관) 목록을 대화로 짐작, 묻지 않음. `references/classroom-use.md`, `scripts/env_programs.py`(한글·오피스·LibreOffice·크롬/엣지/웨일·PDF·Python·Node 읽기 전용 확인, `~/.teacher-studio/env.json`에 7일 저장, 없거나 오래된 프로그램은 크기와 함께 설치 제안만), `deliver.py --use`(HTML→PDF·CSV↔XLSX·표→CSV·슬라이드→PPTX를 기존 도구로 만들고 이 컴퓨터에서 여는 법·활용 아이디어 2~3개·개인정보 확인 출력, 아무것도 올리지 않음). 입구 평가 사례 9개(`tag use`), 시험 `py tools/test_classroom_use.py`(22개).
- **제작 공정표(production pipeline)**: 모든 결과물이 같은 줄을 따른다: 기획 → 대본·내용 → 연출·콘티 → 제작 → 수정 → 배포. 단계마다 눈에 보이는 작은 결과물 하나, 확인 지점은 최대 3번(기획 뒤·콘티 뒤·첫 제작 뒤, 「네」로 계속), 「알아서」는 건너뜀, 작고 분명한 일은 단계를 합치거나 생략, 되돌릴 수 없는·밖으로 나가는 일·법/개인정보·내 자료 필요·점검 두 번 실패는 언제나 묻기. `references/pipeline.md` + 종류별 표 `pipeline-types.md`(슬라이드·게임·영상·수업 도구·데이터·문서·웹/앱·같이 기획). 각 스킬 SKILL.md에 「Pipeline」 두세 줄.
- `scripts/storyboard.py`: spec(슬라이드·게임·컷 목록·`{"frames":[…]}`)을 번호 붙은 콘티 한 장(오프라인 HTML + 글자본)으로, 기존 spec 형식은 그대로 읽음, 저장한 내 색 반영. `scripts/deliver.py`: 완성 파일의 「배포 꾸러미」(크기·인터넷 없이 열림·폰/TV·인쇄/PDF·개인정보 확인표·출처 한 줄, 내 링크만 오프라인 QR, 아무것도 올리지 않음). 시험 `py tools/test_pipeline.py`(17개), 입구 평가에 공정표 사례 8개 추가(`docs/research/pipeline-eval-2026-11.md`).
- **방향 잡기(direction harness)**: `skills/teacher-studio/references/direction-step.md`(아는 것 먼저 → 방향 3가지·추천 → 분위기 카드 → 질문 한 번(최대 5) → 한 줄 계획 → 고치기 2개, 「알아서」는 바로 만들기), `scripts/direction.py`(요청에서 추정한 값·비어 있는 결정 5칸·피치 칸 3개·서로 다른 스타일 3개의 오프라인 미리보기 HTML + 글자 대체본, 저장된 내 색이 있으면 한 장은 내 색), `references/ask-first.md`를 「먼저 보여 주고 마지막에 묻는다」로 다시 씀(첫 설정 질문도 같은 한 번 안에).
- **같이 기획**: 기획·조사·분석(유튜브 채널, 행사, 커리큘럼, 학부모 모임)용 `references/co-plan.md` + `scripts/coplan.py`(한 장 초안: 목표·대상·방향 3가지·추천·할 일·위험·출처).
- **라우터를 번호 규칙으로**: `skills/teacher-studio/SKILL.md`를 R0~R5 순서 규칙 78줄로 줄임(상세는 `references/studio-details.md`). 「유튜브 채널 기획」은 영상이 아니라 같이 기획, 「학부모 상담 자료」는 슬라이드 + 한 줄 안내(과민 반응 없음), 자료 분석은 원본 줄을 읽지 않음. 내 로고·양식 색 먼저 규칙 유지.
- **다른 스킬로 가는 통로**: `recommended-skills.json` 7개 → 19개(기획·글쓰기·SNS·조사·데이터), `skill_scout.py verify`(저장소 있음·라이선스·최근 업데이트·`curl | sh` 검사), `skill_scout.py log`(`~/.teacher-studio/used.json`, 개인정보 없음), 결과 끝 「출처」 한 줄 규칙.
- **입구 평가**: `tools/router_eval.py` + `tools/router_cases.json`(요청 30개) + `tools/test_direction.py`(31개 테스트). 모델별 바닥값·평균: `docs/research/router-eval-2026-11.md`.
- `tools/sync_shared.py --check`가 문서의 스킬·zip 개수와 `skills/` 폴더 수가 다르면 실패(INSTALL.md·docs/training의 5개 → 7개 수정). `teacher-studio`도 `shared/design`을 받음.
- 연구 기록: `docs/research/self-audit-2026-11.md`, `docs/research/benchmark-2026-11.md`.
- **소리 귀 (선택 무기 earshot)**: `shared/tools/sound_ears.py`(`listen` 쉬운 한국어 소리 점검, `sfx` 효과음 만들기, 설치 안 돼도 기본 점검·ZzFX로 동작) + `ensure.py earshot`(동의 뒤, 크기 약 2.4GB 안내, 전용 폴더 `~/.teacher-studio/tools/earshot`, `--uninstall`). 코드 MIT · 모델 Apache-2.0/BSD-3-Clause. 게임 소리 점검·영상 소리 믹스 점검에 연결. 시험 `py shared/tools/test_sound_ears.py`(12개).
### Fixed
- 첫 관문 스크립트의 HTML 저장형 XSS 막기: `direction.py` 미리보기 카드·`ref_analyze.py` 분석 시트(페이지에서 읽은 값 전부)·`storyboard.py`는 모든 글자를 `html.escape`, 색은 `#rrggbb`만 받음. 시험 5개 추가(`tools/test_security_xss.py`). `examples/baseline/game-baseline.json`의 sha256은 원래 만들 때마다 달라서(글꼴 부분집합·seed) 이스케이프 때문이 아니며, 실제 본문 차이는 JSON 안의 `<` → `<` 한 곳뿐(같은 뜻). 두 스킨 화면을 전후로 비교해 같은 모습임을 확인하고 기준 파일을 갱신.
- Windows(cp949)에서 `studio.py fire`·`check`가 한글 출력 때문에 죽던 문제: 하위 프로세스 읽기를 UTF-8로 고정하고, 출력이 파이프일 때 UTF-8로 내보냄(`prefs.py show` 글자 깨짐도 해결).
- 슬라이드의 정답·오답 색을 색약에게도 구분되는 파랑·주황으로(색약 경고 WARN 해소, 네 가지 예시 spec 다시 확인).
- **색 도구 3종**(`shared/design/`): `color_from.py`(내 로고·사진 PNG/JPG·PPTX/POTX·DOCX·한글 HWPX·사이트 CSS/HTML에서 주색·포인트 색을 뽑아 디자인 값으로: 중앙값 분할(median-cut)·배경(흰/검정) 제외·테마 XML 읽기, 글자 대비 4.5는 **밝기만** 조정해 색상 유지, `--save-default`는 요청할 때만 `~/.teacher-studio/prefs.json`), `color_check.py`(Machado 2009 적·녹·청황색약 시뮬레이션, 선형 RGB, 뜻 있는 색 쌍의 OKLab 거리 < 0.10이면 **WARN**: 「빨강·초록만으로 구분하고 있어요. 모양이나 글자도 같이 써 주세요.」), `oklch.py`(sRGB↔OKLab↔OKLCH·색 영역 맞춤·조화색·같은 간격 명암). `design.py --palette-from`과 spec `design.palette_from`(게임·슬라이드·수업 도구, 데이터 `report.py --palette-from`, 값 `saved`=저장한 기본)으로 내 색을 받고, 기본 출력은 그대로. 점검기(게임·슬라이드 review·수업 도구·데이터 보고서)에 색약 WARN. `prefs.py palette-show|palette-reset`. 가이드 `skills/teacher-studio/references/user-colors.md`(내 로고·양식 색 먼저, 수단일 뿐 우리 디자인 아님). 시험 `py -m unittest shared/tools/test_color.py`(32개). JPG 읽기는 Pillow(필요할 때 동의 후 설치), PNG는 설치 없이
- **모두를 위한 README**(ADR 0012): 「누가 쓰나요」(선생님·직장인·자영업자·학생·개발자·데이터 분석가·크리에이터)·「내 양식대로」 추가, 전용 도구와 스킬 스카우트 범위를 정직하게 구분(데이터 분석·조사 도구는 준비 중), 영문 `README.en.md`, ADR 0012
- **슬라이드 도구 구조 전환** (ADR 0001~0003·0011 적용): `studio.py build slides --spec deck.json`(`scripts/deck.py`) — AI는 목적·청중·분위기·장 종류별 짧은 JSON만 쓰고, 도구가 디자인한다. 12가지 스타일 분류(이제 `shared/design/styles.py`, 게임과 공용)를 **슬라이드 구성 언어**(제목 처리·카드·강조·배경 모티프 하나·전환·선호 배치)로 번역, 장 19종(표지·구역·한 문장·목록·비교·단계·큰 숫자·**큰 숫자 둘 나란히**·인용·그림(이미지 없는 도형)·퀴즈 정답 공개·타임라인·Chart.js 그래프·KaTeX 수식·**타이머(시작/멈춤/초기화/±1분)**·**QR(빌드 때 SVG로, 외부 요청 0)**·**이미지(로컬 파일 → 파일 안에, 최대 1920px/3MB)**·**영상(8MB 이하 삽입, 크면 「영상 열기」 버튼)**·마무리)마다 배치 변형 2~4개(비대칭 분할·꽉 찬 큰 글자·벤토·에디토리얼 행·번호 단계·비교 패널…), 같은 배치를 연달아 쓰지 않음. 실행마다 새 seed(출력·`<meta name="ts-deck">`), `--seed`로 재현. 절제 원칙: 한 장에 초점 하나·강조 색 하나·배경 모티프 하나·아이콘 장식 없음, 글자 28px 이상, 장당 글 330자 이하(넘으면 「고칠 곳」). 장별 샌드박스 `flair`(css·svg) 허용. 옛 `lesson-deck` 스킨 3개와 `fire`는 그대로 두되 최하 우선순위. 예시 spec 4개(`skills/teacher-slides/assets/spec-examples/`)
- `scripts/slides_review.py`: 장마다 애니메이션이 끝난 뒤 캡처 → 접촉 시트 + 수치(외부 요청 0·실제 화면 픽셀 대비 4.5·글자 크기·넘침·안전 여백·keep-all·휑함·**어수선함 상한: 요소 36·아이콘 3·큰 색 6**·같은 배치 3연속 금지), `--compare`로 덱끼리 닮음(스타일·배치 집합·강조색) 거리
- 공용: `shared/vendor/qrcodegen`(Nayuki, MIT) 추가(NOTICE 18), `shared/stage/build_stage.py`에 `scene_html`·`offline`(구글 글꼴 링크 제거 → 외부 요청 0) 옵션, `teacher-game/scripts/style_auto.py`는 `shared/design/styles.py`를 불러다 쓰는 입구로
- **무손실 원칙**(ADR 0011): 하네스가 맨 모델보다 나빠지지 않도록 확신 관문·2번 고치기 후 맨 모델로 전환·「하네스 없이 해 줘」 해제·설치 동의·안내만 하는 법 규칙을 `teacher-studio` SKILL.md에 추가 (맨 모델 대비 평가 관문·줄 수 실측은 「계획」)
- 3차 **구성 다양성**: 12가지 스타일 분류(`scripts/style_auto.py`: 네온/사이버·골드 럭셔리·팝 컬러풀·축제/파티·TV 게임쇼·글래스/3D·애니/카툰·파스텔·레트로/픽셀·미니멀 프리미엄·칠판/종이·자연/차분)를 세계(소품·도우미·시그니처 그림)와 따로 뽑아 조합, 스타일마다 색·배경 생성기·문제 화면 배치(`scripts/layout_auto.py`, `assets/layouts/layouts.css`: stack·split·bento·news·poster)·버튼 5종·카드 4종·점수판 4종·제목 4종·방식별 판 배치·전환을 달리함. 안 적으면 매번 새 seed(출력·`<meta name="ts-seed">`)
- 요청에서 뽑은 **시그니처 그림**(태양계 궤도·독도 섬·송년회 시계 12시·피라미드·산·궁궐), 새 도우미(우주인·토끼·부엉이·여우), `custom_css`/`custom_svg` AI 자유 칸(크기·바깥 주소·스크립트 제한), 디자인 점검의 **배치 닮음** 검사
- 편향 정리: 자동 조합에서 옛 스킨의 진행자·LED 벽·ON AIR·APPLAUSE·연단을 쓰지 않음(요청이 그 세계를 직접 부를 때만 이식 테마 한 벌), 옛 스킨 수치는 최소선으로만 사용, 점검표는 요즘 상용 디자인 기준으로 다시 씀
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
