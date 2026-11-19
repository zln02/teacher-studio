# 보안 점검 2026-11 — teacher-studio · noan-ai

## 결론 먼저

두 저장소 모두 **치명적(Critical) 문제는 없음**. 가장 눈에 띄는 것은 noan-ai(B)의 `art-motion` 수업(미술 생성 AI)에 쓰는 **학생 참가 코드가 평문으로 레포에 적혀 있다가 SHA-256 해시로 바뀐 내역**(과거 커밋), 그리고 **CSP(콘텐츠 보안 정책)가 두 사이트 어디에도 없다**는 점. teacher-studio(A)는 설치·다운로드 전부 "선생님 동의 먼저" 원칙을 지키고 있고, 생성되는 HTML의 사용자 입력은 대부분 이스케이프되지만 **수업 도구(timer 등)의 제목(title)과 teacher-game의 커스텀 CSS/SVG 경로는 그대로 HTML에 꽂혀** 저장된 XSS가 가능함을 직접 만들어 확인했다.

실제로 재현한 것: `teacher-class-tools`의 `title`에 `</title><img src=x onerror=...>`를 넣고 빌드하면 **그대로 HTML에 삽입됨** (이스케이프 없음). `teacher-game`의 퀴즈 항목 문자열에 `</script><script>alert(9)</script>`를 넣어도 **그대로 실행 가능한 스크립트로 들어감**. 둘 다 "선생님이 스펙(JSON)을 직접 쓰거나, AI가 선생님 말을 받아 만드는" 구조라 공격자가 바로 주입하긴 어렵지만, 외부에서 받은 텍스트(예: 학생 이름, 외부 콘테스트 설명, AI가 그대로 베껴 넣은 텍스트)가 섞이면 저장된 XSS가 된다.

## findings 표

| # | 심각도 | 대상 | 위치 | 내용 | 근거(확인 방법) |
|---|--------|------|------|------|------------------|
| 1 | High | A | `skills/teacher-class-tools/scripts/build_tool.py:127-140` | 수업 도구의 `title`이 이스케이프 없이 `<title>`과 `<h1>`에 직접 삽입됨(`f'<title>{title}</title>'`, `f'<h1>{title}</h1>'`). payload는 `</`→`<\/`만 치환되고 그 외 HTML은 그대로. | `title`에 `</title><img src=x onerror=alert(1)>`를 넣고 `build_tool.py`로 빌드 → 결과 HTML에 그대로 삽입됨을 직접 확인 |
| 2 | High | A | `skills/teacher-game/scripts/build.py` (title/h1 처리), `assets/engine.html:820` 등 | 게임 제목·문항 텍스트가 `window.GAME = {...}`(JSON, `</`이스케이프됨)으로는 안전하지만, `<title>` 치환과 `custom_svg`/`custom_css`(136-150행, AI가 쓴 "추가 장식")는 이스케이프 없이 원문 그대로 CSS/HTML에 삽입됨 | 퀴즈 항목 텍스트에 `</script><script>alert(9)</script>`를 넣고 빌드 → 결과 HTML에 실행 가능한 `<script>` 태그가 그대로 삽입됨을 확인. `custom_svg`는 설계상 "AI가 만든 SVG"를 검증 없이 그대로 꽂음(`spec_out["customSvg"] = spec["custom_svg"]`) |
| 3 | Medium | A | 전반(`shared/stage/build_stage.py`, `skills/*/scripts/*.py`) | 1·2의 패턴이 teacher-slides(제목), teacher-motion(동일 stage 빌더)에도 같은 구조로 반복됨. 데이터 쪽(`teacher-data/scripts/report.py`)은 `html.escape`를 꼼꼼히 쓰고 있어 비교적 안전 — 이 부분은 모범 사례로 참고할 만함 | 코드 리딩으로 확인(동일 regex 치환 패턴 `shared/stage/build_stage.py:70-71`) |
| 4 | Medium | B | 전 사이트 (모든 `.html`) | Content-Security-Policy 메타 태그가 한 곳도 없음(`grep`으로 전수 확인, 0건). innerHTML을 광범위하게 쓰는 사이트(`ai/ai.js`, `guide/home.js`, `contest/index.html`, `iamodu/iamodu.js` 등)에서 XSS가 나면 CSP가 2차 방어선이 되어주지 못함 | `grep -ri "content-security-policy"` 결과 0건 |
| 5 | Medium | B | `data/*.js`→`*.html`의 innerHTML 소비처 (`ai/ai.js:46`, `guide/home.js:366`, `contest/index.html:176` 등) | 데이터는 레포 안의 정적 JS/JSON(공격자가 직접 못 바꿈)이라 지금은 안전하지만, **URL 필드는 `esc()`로 에스케이프하면서도 속성 삽입 패턴이라 `href="javascript:..."` 같은 scheme은 막지 않음**. 데이터가 외부 입력(요청 폼 등)으로 확장되면 즉시 위험해짐 | `ai/ai.js:31`의 `esc(m.url)`이 HTML 엔티티만 치환, scheme 검증 없음을 코드로 확인 |
| 6 | Medium | B | `supabase/functions/art-motion/index.ts` 전체 | 학생이 업로드한 그림을 **Anthropic API로 그대로 전달**(prompt 다듬기), **Luma API로 외부 전송**. 요금 결제와 직결된 유료 생성 기능이 `verify_jwt = false`(`config.toml`)로 공개 엔드포인트에 떠 있고, 접근 제어는 자체 발급 코드(해시 대조)뿐. 레이트리밋이 DB의 `reserve_art_quota` RPC(건수 제한)만 있고 **IP/요청 빈도 제한이 없어** 코드 1개를 알면 빠르게 반복 호출로 과금 유발 가능 | `index.ts:50-56`(Anthropic 호출), `config.toml`(`verify_jwt=false`), `202610120001_art_motion.sql`의 `reserve_art_quota`만 제한 로직임을 확인 |
| 7 | Low | B | `supabase/migrations/202610120003_art_access_codes.sql`, `202610120004_art_teacher_code.sql` | 참가 코드 20개 + 선생님 코드가 **SHA-256 해시(salt 없음)로 레포에 커밋됨**. salt 없는 SHA-256은 짧고 예측 가능한 코드(교실 코드 성격상 짧을 가능성)일 경우 레인보우테이블/사전공격에 약함. (해시를 역산하는 시도는 보안상 하지 않았음 — 아래 "시도 안 한 것" 참고) | 파일 내용 확인(해시값 64자 hex, salt 컬럼 없음) |
| 8 | Low | B | `supabase/functions/art-motion/index.ts:263` | `imageGenerationId` 정규식이 `[0-9a-f-]{36}`로 UUID 형식만 검증하지만 `-`의 위치를 강제하지 않아 `000000000000000000000000000000000000`(36자 숫자)도 통과함 — 실질적 위험은 낮음(DB 조회에서 막힘) | 정규식 직접 분석 |
| 9 | Low | A | `skills/teacher-studio/scripts/ref_analyze.py` | 외부 URL을 Playwright로 로드하기 전 `robots.txt`를 확인하고 사설 IP/로컬호스트 차단 로직은 없음(SSRF 가능성: `http://169.254.169.254/` 같은 메타데이터 주소도 `robots_ok`만 통과하면 로드) — 다만 결과는 스크린샷/디자인 토큰만 추출하고 응답 바이트를 그대로 되돌려주진 않아 영향은 제한적 | `robots_ok()`·`main()` 코드에 사설 IP 차단 분기 없음을 확인 |
| 10 | Low | A | `shared/tools/ensure.py`, `scripts/setup.py` | pip/playwright 설치가 **HTTPS(PyPI 기본)이고 동의 후에만 실행**되지만, 설치 패키지에 버전 고정(pin)이나 체크섬 검증이 없음(`pip install <name>`, 버전 미지정) — 공급망 측면에서 "최신판 신뢰" 구조 | `PACKAGES` 딕셔너리에 버전 지정 없음, `_pip_install`에 `--require-hashes` 등 없음 |
| 11 | Info | A | `shared/vendor/manifest.json` | 벤더 라이브러리(anime 4.5.0, motion 14.14.0, confetti 1.9.4, chartjs 4.6.1, katex 0.19.1, lucide 1.75.0, phaser 4.2.1, axe-core 4.14.1, qrcodegen 1.8.0) sha256 해시가 매니페스트와 **실파일 전부 일치**(직접 재계산해서 확인). 라이선스도 허용 목록(MIT/ISC/OFL/MPL 예외)과 일치. CVE는 전부 패키징/빌드 도구 버전(npm/webpack 등)에 관한 것이라 **번들된 브라우저 런타임 코드엔 해당 없음**으로 판단(공식 웹서치는 수행하지 않음 — 아래 참고) | 매니페스트 sha256 재계산 스크립트로 대조 |
| 12 | Info | B | `shared/vendor/three(r128)`, `alpine(3.17.5)`, `webawesome(3.15.0)`, `open-props` | three.js r128(2021, MIT)은 오래된 버전이지만 **외부 네트워크 호출이 없는 정적 렌더러**(README에도 명시)라 알려진 three.js CVE(주로 loader의 외부 리소스 로딩·XSS 관련)는 이 사용 범위(로컬 3D 애니메이션만)와 거리가 있음. Alpine 3.17.5, Web Awesome 3.15.0은 비교적 최신. 실제 CVE 데이터베이스 대조는 웹서치를 쓰지 않아 **미검증**(아래 참고) | 버전 문자열 직접 추출, 네트워크 호출 여부 README·코드로 확인 |
| 13 | Info | B | `supabase/feedback.sql`, `shared/feedback.js`, `dokdo_scores` 류 테이블 | "insert-only" RLS 주장은 SQL로 실제 확인됨: `revoke all ... grant insert(특정 컬럼만)`. 이름·학교·IP는 받지 않음(주석과 실제 컬럼 모두 일치). dokdo 점수판은 `select`도 `anon`에 허용(랭킹 공개용으로 의도된 설계) — 스푸핑(가짜 높은 점수 제출)은 가능하지만 개인정보 유출은 없음 | SQL 파일 전수 확인 |
| 14 | Info (오탐 기각) | B | 외부 링크 전체 | `rel="noopener"`가 거의 모든 `target="_blank"`에 붙어 있음(grep 전수 확인, 예외 없음 발견 못함) → 문제 없음으로 판단 | grep 결과 |
| 15 | Info (오탐 기각) | A | subprocess 사용 전반 | 모든 `subprocess.run`/`Popen` 호출이 `shell=True` 없이 리스트 인자로 호출되어 셸 인젝션 경로 없음(파일명·스펙 값이 커맨드 문자열에 섞이는 경우 없음) | 전체 `shell=True` grep 0건 |
| 16 | Info (오탐 기각) | A | `tools/sync_shared.py`, `scripts/setup.py`의 zip 처리 | zip은 **쓰기(압축)만** 하고 압축 해제(extractall)하는 코드가 레포 안에 없음 → zip-slip 경로 없음 | `extractall` grep 0건 |

## 고친다면 순서(랭크)

1. **(High, #1·#2)** teacher-studio: `build_tool.py`의 title과 teacher-game의 `<title>`/`custom_svg`/`custom_css` 삽입 지점에 `html.escape()` 또는 `teacher-data/scripts/report.py`가 이미 쓰는 패턴을 그대로 적용. `custom_svg`는 최소한 `<script`, `on\w+=`, `javascript:` 패턴을 거부하는 화이트리스트 검사(SVG 태그/속성 목록 허용) 추가.
2. **(Medium, #4)** noan-ai 모든 `index.html`에 `<meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'self' https://dovpodhwmredayldjrvb.supabase.co; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'">` 수준의 CSP 추가 (인라인 스크립트가 많아 처음엔 `unsafe-inline` 필요할 수 있으나, 최소 `connect-src`/`frame-ancestors`부터 시작).
3. **(Medium, #6)** art-motion 엣지함수에 IP 기반 또는 세션당 호출 빈도 제한(Supabase가 제공하는 레이트리밋 또는 `art_usage`에 "최근 1분 N회" 체크) 추가. 유료 API(Luma/Anthropic) 호출 비용이 코드 하나 유출로 증폭될 수 있음.
4. **(Low, #7)** 참가 코드 해시에 salt(또는 HMAC with server secret) 추가. 현재도 "해시만 저장"이라는 원칙은 맞지만 salt 없는 SHA-256은 짧은 코드엔 약함.
5. **(Low, #9)** `ref_analyze.py`에 사설 대역(10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16, 127.0.0.0/8, ::1) 차단을 robots 체크 전에 추가.
6. **(Low, #10)** `ensure.py`의 `PACKAGES`에 버전 고정(`"python-pptx==1.0.2"` 식) 추가해 공급망 변동 리스크를 줄임.

## 기각한(오탐으로 판단한) 항목

- subprocess shell 인젝션 — 전수 확인 결과 `shell=True` 없음, 리스트 인자만 사용.
- zip 경로 트래버설 — extractall 코드 자체가 레포에 없음(압축만 함).
- teacher-data(report.py) XSS — `H.escape` 일관 사용, 문제 없음.
- `rel=noopener` 누락 — 전수 grep에서 예외 발견 못함.
- 레포/깃 히스토리의 평문 API 키·토큰 — 패턴 검색(AKIA/sk-/ghp_/BEGIN PRIVATE KEY 등) 0건.

## 확인하지 못한 것 (한계)

- **벤더 라이브러리 CVE**: 웹서치 도구를 쓰지 않고 버전·사용 맥락만으로 "영향 없음"을 추정했음. 정확한 결론을 위해선 NVD/GitHub Advisory에서 anime.js 4.5.0, motion 14.14.0, Chart.js 4.6.1, KaTeX 0.19.1, Phaser 4.2.1, three.js r128, Alpine 3.17.5, Web Awesome 3.15.0을 직접 조회해야 함.
- **참가 코드 해시 역산**: 학생 참가 코드가 평문 없이 해시만 레포에 있는 구조라, 코드가 추측하기 쉬운지(예: 극히 짧은 패턴) 확인하려는 시도를 했으나 **살아있는 운영 시스템의 인증 수단을 깨는 시도라서 중단**했다. 대신 "salt 없는 SHA-256"이라는 설계 자체의 약점(#7)으로만 지적함.
