# Changelog

## [Unreleased]
### Summary (7 skills, 7 zips)
- **스킬 7개**: `teacher-studio`(첫 관문·라우터) · `teacher-game` · `teacher-slides`(spec 기반으로 전환) · `teacher-motion` · `teacher-law` · `teacher-class-tools`(타이머·뽑기·모둠·대진표·점수판) · `teacher-data`(엑셀·CSV 분석 보고서). `dist/`에 zip 7개, `tools/sync_shared.py --check`가 공용 복사본·zip을 모두 검사
- **공용 도구함 확장**: `shared/juice`(Game Wow 키트: 게임 + 수업 도구), `shared/tools/video_eyes.py`(영상 → 장면 사진, 로컬 전용), `shared/vendor/qrcodegen`, `shared/design/styles.py`
- **첫 관문 규칙**: 먼저 묻기(`ask-first`), 막연한 불평 자동 진단(`diagnose.py`), 스킬 스카우트, 참고 사이트 패턴 분석(`ref_analyze.py`), 첫 설정 기억(`prefs.py`), 무손실 원칙. 모든 스킬: 「선생님과 누구나」, 사용자 언어로 답하고 사용자가 준 양식·참고가 먼저 (사용자 양식으로 만드는 도구는 아직 계획)
- `teacher-data` 문구 정리: 점수대 그래프 설명이 설문 문구를 쓰던 것 수정, 「가장 높은 A와 가장 낮은 B의 차이」처럼 두 곳을 밝힘, 소수 자릿수 통일(-0.4점, 6.0점)
- `docs/training/deck.json`을 새 슬라이드 spec으로 다시 만듦(21장, 점검 통과)

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
