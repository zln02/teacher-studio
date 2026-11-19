# 0013. 문서 무기는 새 스킬 `teacher-docs` (한글 HWPX · 워드 · PDF)

- 상태: Accepted (2026-11-20)
- 관련: 0007(라이선스), 0008(환경별 처리), 0009(공식 스킬 재사용), 0011(후회 없는 원칙)

## 배경
운영자(AI교육코디네이터) 관찰: 선생님이 가장 많이 쓰는 것은 PPT와 **문서**다. 문서는 공문·가정통신문·안내문·보고서를 새로 쓰기, 받은 양식 채우기, 있는 한글 파일 고치기, PDF 합치기·나누기·서명용 정리다. `MAP.md`에는 「업무 문서 (teacher-work-docs, 예정)」만 있었고, 법률 스킬의 `make_notice.py`는 법률 안내 한 장짜리 HTML이다.

## 결정
1. **새 스킬 `skills/teacher-docs`** 를 만든다. 슬라이드나 법률 스킬에 넣지 않는다.
   - 입력·출력 형식이 다르다 (HWPX/DOCX/PDF 파일 vs 1920×1080 HTML 무대). 점검 항목도 다르다 (공문 형식·끝 표시·날짜 vs 글자 크기·대비·겹침).
   - 크기: 생성기 + 편집기 + 미리보기 + PDF 도구 + 점검기 = 스킬 하나 분량. 슬라이드 zip에 넣으면 슬라이드만 원하는 사람도 받게 된다 (MAP 규칙 「필요한 칸만 받는다」).
   - 법률 스킬은 「최신 법을 찾아 답한다」가 정체성이다. 문서 형식은 규정이 근거지만 만들기 도구라 분리하고, 학생 정보·동의서가 걸리면 서로 가리킨다.
2. **HWPX는 표준 라이브러리로 직접 쓴다** (zipfile + 문자열/ElementTree). 바탕 파일은 `python-hwpx` 6.12.0(Apache-2.0)이 배포하는 빈 문서 `Skeleton.hwpx` 하나만 가져온다 (LICENSE·NOTICE 동봉, `shared/vendor/manifest.json`·`NOTICE` 기록).
   - 0009는 「HWPX는 python-hwpx」였다. 바꾸는 이유: 선생님 PC에 lxml 포함 설치가 필요 없고(오프라인·학교 망), 우리가 쓰는 범위(문단·글자 모양·표·채우기·찾아 바꾸기)는 작아서 직접 관리할 수 있다. 원본 서식 보존은 「<hp:t> 글자만 바꾸고 나머지 zip 항목은 그대로」 규칙으로 지킨다.
   - 고급 편집(셀 병합 바꾸기, 수식, 개체)은 python-hwpx를 「필요할 때 설치」(`ensure.py`에 이미 있음)로 남겨 둔다.
3. **이미 설치된 스킬에 맡긴다, 복사하지 않는다.** `docs.py where`가 `hwp-docs`(kordoc: .hwp 읽기·validate), 공식 `docx`·`pdf` 스킬, 한글 프로그램, 브라우저를 찾는다. 있으면 SKILL.md가 그쪽으로 넘기는 경우를 적는다 (옛 .hwp 글자 읽기, 변경 추적·메모 같은 워드 고급 기능). 그 파일은 저장소에 넣지 않는다.
4. **워드는 python-docx(MIT), PDF는 pypdf(BSD-3)·pdfplumber(MIT)** 를 동의 후 설치. PDF 만들기는 우리 A4 HTML(글꼴 내장)을 PC의 크롬/엣지로 인쇄한다 (reportlab 같은 새 의존성 없이 한글 글꼴 해결).
5. **옛 .hwp(바이너리)는 올리지도 변환 서비스에 보내지도 않는다.** 「한글에서 HWPX로 저장」을 안내하고, 한글이 있으면 그 프로그램으로 바꾸는 길을 안내한다.
6. **하나의 블록 모델** (`docmodel.py`) → HWPX / DOCX / HTML(PDF) 세 출력. 공문 규칙(1. 가. 1) 가) …, 항목 하나면 기호 없음, 끝 두 칸, 붙임, 날짜)은 모델에서 한 번만 적용한다.
7. **점검기 `doc_check.py`** 가 모든 문서의 출고 관문이다 (0004). 빈칸(슬라이드와 같은 `placeholders.py`, 원본은 `shared/tools/`), 개인정보, 공문 형식, 날짜, 간단한 띄어쓰기, 다시 열림·구조, 글꼴.

## 검토한 대안
- **teacher-slides에 문서 추가**: zip 비대, 점검기 혼합. 기각.
- **teacher-law의 make_notice 확장**: 법률 답 카드와 업무 문서는 목적이 다름. 기각 (법률 안내문은 그대로 둔다).
- **python-hwpx를 기본 의존성으로**: 기능은 많지만 lxml 포함 설치·버전 변화(6.x 잦은 릴리스)를 선생님 PC가 떠안음. 「필요할 때」로 강등.
- **kordoc(Node) 직접 사용**: Node 18+ 필요, 학교 PC에 거의 없음. 설치된 경우에만 위임.

## 결과
- 장점: 한글 문서가 인터넷·설치 없이 만들어지고 채워진다. 같은 내용을 HWPX·워드·PDF로. 공문 규칙이 근거(규정·편람)와 함께 자동 적용.
- 단점: 우리 HWPX 미리보기는 근사치다(한글 자체가 아님). 한글에서 실제로 열어 보는 확인은 사람이 해야 한다 → 무거운 단계에서 예시 문서를 한글 또는 kordoc validate로 한 번 더 확인하고 결과를 기록한다.
- 스킬 수가 7 → 8개가 된다. 개수를 적은 문서(README·INSTALL·MAP, 연수 자료)를 함께 고쳐야 `sync_shared.py --check`가 통과한다.

## 근거
- 공문 형식 근거와 「공식 / 관행」 구분: `skills/teacher-docs/references/gongmun-format.md`.
- 라이선스: python-hwpx 6.12.0 LICENSE(Apache-2.0)·NOTICE, pypdf 7.1.1 LICENSE(BSD-3), pdfplumber 0.11.10 LICENSE.txt(MIT), python-docx 1.2.0 LICENSE(MIT) — `pip download`로 받아 실제 파일을 읽음 (2026-11-19).
