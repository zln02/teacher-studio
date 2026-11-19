# deck-v2 하네스 피드백: 우리 무기로 못 해서 손으로 만든 것

대상: `teacher-slides`(deck.py 스펙 덱), `teacher-motion`(STAGE + 미사일). 이 덱(`deck-v2.html`, 25장, 3D 장면 6개)은 두 무기를 읽기만 하고 **전부 손으로** 만들었다. 사용자의 AI가 다음엔 코드 없이 만들 수 있게, 빠진 것과 넣을 것을 적는다.

## 1. 무기가 못 한 것

| 필요했던 것 | teacher-slides | teacher-motion | 이번에 한 일 |
|---|---|---|---|
| 3D 장면 (three.js) | 없음. 슬라이드 종류에 3D가 없고 vendor에 three가 없다 | 없음. `bg(fn(ctx,t))`는 2D 캔버스뿐 | `npm pack three@0.128.0`, LICENSE 읽고 직접 넣음 |
| **빌드 단계가 3D까지 이어짐** (→ 누르면 차가 다음 정거장으로, 카메라가 따라감) | 빌드는 요소 보이기/숨기기뿐 | 시간축(timeline)만 있고 '누르면 다음 단계'가 없다 | `setStep(n, snap)` / `update(dt,t,snap)` 규약을 손으로 만듦 |
| 3D 위 한국어 이름표 (3D 위치를 따라다니는 HTML) | 없음 | 없음 | 매 프레임 `project()`로 HTML 라벨 위치 계산 |
| '그 단계일 때만' 보이는 글 (`data-only`) | 빌드는 쌓이기만 한다 | 없음 | `data-only="n"` 추가 |
| 슬라이드 안 타이머 + 클릭 진행 공존 | `timer` 슬라이드는 한 장 전체를 차지, Space를 뺏는다 | lesson-opening만 | 원형 타이머 컴포넌트(클릭/T 키), Space는 진행용으로 남김 |
| 덱 안에 움직이는 슬라이드와 정적 슬라이드 섞기 | 정적만 | 한 화면짜리 영상만 | 두 세계를 한 엔진으로 |
| 저사양 대응: DPR 1.5 상한, 안 보이면 멈춤, 느리면 해상도 자동 낮춤, WebGL 없으면 2D | 해당 없음 | 없음 | 렌더러 1개를 슬라이드끼리 돌려 씀, `visibilitychange`, 프레임 시간 보고 0.5까지 낮춤, `body.no-gl` 대체 화면 |
| prefers-reduced-motion: 3D는 멈춘 한 장면 | CSS 전환만 끔 | 없음 | `snap` 경로로 최종 상태 한 프레임만 그림 |
| 결과 화면 캡처를 '있으면 넣고 없으면 자리 표시' | `image`는 파일이 꼭 있어야 한다 | 없음 | `build.py`가 `compare/<case>-<side>.png`를 찾아 data URI로, 없으면 「결과 화면 들어갈 자리」 |
| 3D 장면 점검 (캔버스가 비었나) | `slides_review.py`는 3D를 모른다 | `check_page.py`도 마찬가지 | `shoot.py`: 캔버스 영역 픽셀 표준편차, 콘솔 오류, 외부 요청 |
| 움직임 GIF | 없음 (MP4는 ffmpeg 필요) | `render_mp4.py`는 timeline 페이지만 | Playwright 캡처 → PIL GIF |

## 2. 손으로 만든 부품 (그대로 무기로 옮길 수 있는 것)
`docs/training/deck-v2-src/deck.js` 안에 있다.
- **3D 런타임**: `initGL / sizeGL / startLoop / stopLoop / projectLabels` — 렌더러 1개, 활성 슬라이드에만 붙음.
- **장면 규약**: `SCENES.<이름>(slideEl) → {scene, camera, labels:[{el,obj,off}], setStep(n,snap), update(dt,t,snap)}`. 상태는 목표값으로 감쇠(`damp`)해서 앞뒤로 넘겨도 깨지지 않고, `snap`이면 즉시 최종 상태(=reduced-motion, 스크린샷).
- **부품**: `card()`(둥근 카드 + 한국어 글씨 텍스처), `ribbon()`(곡선 따라 납작한 길, 진행만큼 `reveal`), `dashes()`, `carMesh()`, `museumMesh()`, `schoolMesh()`, `postMesh()/lightPost()`(경유지 불), `blob()`(가짜 그림자·빛), `lights()`.
- **장면 6개**: cover(떠 있는 공정 카드), nav(같은 목적지 두 길), route(경유지 다섯), pipeline(여섯 정거장 + 확인 문), cheat(여섯 칸 신호 + 막는 벽, 추상 도형만), made(무기 카드 고리).

## 3. 제안: 다음엔 AI가 스펙만 쓰게

### teacher-slides에 넣을 것
1. **`scene3d` 슬라이드 종류** — 스펙 예:
   ```json
   {"type":"scene3d","preset":"route","title":"기획부터 배포까지",
    "stops":["기획","대본","콘티","제작","수정","배포"], "checks":[1,3,6],
    "captions":[{"title":"기획","text":"아이디어 3개 → 고르기","gate":"선생님 고르기"}, ...]}
   ```
   프리셋 후보: `route`(길 위 정거장, 차가 이동), `split-route`(헤매는 길 vs 곧은 길), `pipeline-signal`(칸을 지나는 신호 + 막는 벽), `card-orbit`(표지·마무리용 떠 있는 카드), `folder-reveal`(파일에서 카드가 하나씩). 각 프리셋 = 위 장면 규약을 따르는 JS 한 파일 + 2D 대체 화면.
2. **`data-only` 캡션과 `steps` 수**를 빌드 시스템에 정식으로 (지금은 쌓이는 빌드만).
3. **`timer`를 위젯으로**: 어느 슬라이드에나 `"timer":{"minutes":17,"corner":"right"}`로 붙이고, 클릭/T 키로만 동작.
4. **`compare-shots` 슬라이드**: `{"type":"compare-shots","ask":"…","a":{"label":"맨몸","file":"compare/game-bare.png"},"b":{...}}` — 파일이 없으면 자리 표시 틀(지금 `build.py`의 `shot()`과 같음).
5. **스펙에 `dark:true` 장 구간**(부정행위처럼 분위기 바뀌는 묶음)과 **구간 진행 띠(agenda)** 자동 표시.
6. `slides_review.py`에 3D 점검: 캔버스 비었는지, WebGL 없는 모드(`?nogl=1`) 스크린샷, `?reduced=1` 스크린샷.

### teacher-motion에 넣을 것
1. **`STAGE.scene3d(presetOrFn)`**: STAGE 시간축과 같은 시계(`t만으로 결정`)로 three 장면을 그려 녹화·MP4도 되게. 위 장면 규약에 `seek(t)`만 더하면 된다.
2. **step 모드**: `STAGE.steps(n, onStep)` — 영상이 아니라 '누를 때마다 다음'인 화면(연수 시연용).
3. vendor에 **three.js r128**(ES5, MIT) 추가: `shared/vendor/three/` + `manifest.json` + `NOTICE`. 최신판(r16x)은 ES 모듈·class 필드라 오래된 크롬 규칙과 부딪혀서 r128을 권한다. `inline.py --libs three`.
4. 저사양 규칙을 STAGE 공통으로: DPR 상한 1.5, 숨으면 멈춤, 프레임 시간 보고 해상도 낮추기, WebGL 실패 시 2D.

### 공통 (shared)
- 3D 부품 라이브러리 `shared/stage/three-kit.js`(card/ribbon/car/post/blob/lights + 라벨 투영 + 렌더러 공유). design.py 팔레트를 3D 재질 색으로 넘기는 `tokens.three`.
- `check_page.py`(teacher-motion 복사본)로 이 덱을 돌리면 옛 크롬 문법·외부 요청·JS 문법은 모두 PASS지만, 게임 엔진 블록(GAME data, GAME_LOGIC, NG.boot, 음소거·선생님 메뉴) 6개가 FAIL로 나온다. 손으로 만든 페이지용 `--kind page`(엔진 블록 검사 끄기) 모드가 필요하다.
- `check_page.py`: three.min.js 안의 `?.07` 같은 삼항을 `?.`로 오탐하지 않도록 (지금 정규식은 숫자 뒤를 거르므로 통과하지만, vendor 블록은 아예 건너뛰기).

## 4. 이번에 손으로 정한 디자인 규칙 (프리셋 기본값 후보)
- 3D는 화면 오른쪽 55%, 글은 왼쪽 760px 안. 카메라는 물체 왼쪽을 바라보게(lookAt을 물체보다 왼쪽) 두면 글과 안 겹친다.
- 따뜻한 밝은 배경 + 테라코타 하나 + 청록 하나(확인·통과 색). 어두운 구간은 호박색 강조.
- flatShading 저폴리, 그림자 대신 방사형 그라데이션 판, 안개는 배경색.
- 깜빡임: 블랙박스 점 0.8Hz, 맥동 링 0.8Hz (초당 3회 이하).

## 5. 제안: 하네스에 넣을 「3D 물건 상자」(three-kit)

이번 수정에서 「아무 3D 도형」이 아니라 **말 그대로의 물건**(안경, 휴대폰, AI 구름, 이어폰, 시계, 노트북, 차, 건물, 사람)이 있어야 선생님이 알아본다는 게 분명해졌다. 하네스(teacher-slides·teacher-motion 공용)에 넣을 물건 상자는 이렇게 생겨야 한다. 지금 원형은 `deck-v2-src/deck.js`의 「3D 물건 상자 (KIT)」 블록이다.

1. **재질·빛 토큰 한 곳**: `P`(3D 색) + `CSS`(캔버스 글씨 색) 객체 하나, `design.py` 팔레트에서 생성(`tokens.three`). 재질은 `M`(새틴 점토)·`MF`(저폴리 면)·`E`(빛나는 면)·`Bm`(빛 영향 없음) 네 가지만. 빛은 `rig(scene, warm, size)` 하나: 반구광 + 그림자 키 라이트 + 채움 빛 + 강조색 테두리 빛. 덱 색을 바꾸면 3D도 같이 바뀐다.
2. **기본형**: `rbox`(모서리 둥근 상자, 점토 느낌의 핵심), `sph`, `cyl`, `rrShape`, `star4`, `tex`(캔버스 텍스처, `redraw` 가능), `plane`, `blob`(빛 번짐), `catcher`(투명 바닥 그림자), `pathTube` + `pulseMesh`(곡선 위를 지나는 신호), `card`(글씨 + Lucide 아이콘 카드, 밝기 보고 글자색 자동).
3. **물건 목록(이름 = 화면에 쓰는 말)**: 카메라 안경 / 화면 안경 / 초소형 이어폰(소리 물결) / 휴대폰(화면 텍스처 교체) / 스마트워치 / 노트북 / 클라우드 AI(구름 + 반짝 별) / 키보드와 손 / 모니터 대화창 / 학생과 책상(의자·시험지·연필·주머니) / 길 묻는 행인 / 자동차 / 목적지 건물(정문·옆문) / 학교 / 나무 / 문(게이트) / 가로등 / 전구·대본·콘티·톱니·연필·종이비행기. 각 물건은 `userData`로 움직일 부분(렌즈 화면, 카메라 고리, 소리 물결, 손가락, 문 빛)을 내놓는다.
4. **안전선이 걸린 물건은 갈래 모양만**: 기기 물건은 뉴스에 나오는 수준의 생김새만. 브랜드 모양·로고·실제 제품 비율을 흉내 내지 않는다. 물건 상자 README에 이 규칙을 적는다.
5. **장면 규약 그대로**: `{scene, camera, labels, setStep(n, snap), update(dt, t, snap)}`. `snap`은 최종 모습(스크린샷·움직임 줄이기). 이동하는 것(사진·말풍선)은 `snap`일 때 길 중간에 멈춰 보이게 해서 한 장 그림으로도 뜻이 통하게.
6. **점검 도구**: `closeup(name)`으로 물건 하나씩 따로 찍는 기능 + `shoot.py --closeup`이 만드는 물건 모음 사진(`deck-v2-3d-closeup.png`). 새 물건을 넣으면 이 사진에서 「기본 도형 같지 않은가」를 사람이 본다. 점검기(`check_page.py`)에는 캔버스가 비었는지, WebGL 없는 화면, 움직임 줄인 화면을 넣는다.
7. **저사양 규칙**: 렌더러 하나, 보이는 장만 그림, DPR 상한 1.5, 프레임이 느리면 해상도를 낮추고 그림자 갱신을 멈춤(`shadowMap.autoUpdate=false`), WebGL이 없으면 2D 카드 대체 화면.
8. **이름표는 HTML**: 3D 위 글씨는 캔버스가 아니라 투영한 HTML(`lbl`)로. 글꼴·대비·크기를 CSS 토큰이 책임지고, 슬라이드 캡션과 같은 단어를 쓴다.
