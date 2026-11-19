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

## 6. 시네마틱 판 (CC0 사진 환경 · 진짜 재질 · 후처리 · 유리 판): 하네스로 옮기는 법

이번 판에서 손으로 한 일을 세 가지 무기로 나누면, 다음부터는 AI가 「무엇을 보여 줄지」만 정하면 돼요.

### 6-1. `shared/tools/cc0_fetch.py` (필요할 때만 받아 오는 CC0 환경·텍스처·모델 도구)
- 입력: 종류(`hdri` · `texture` · `model`)와 자산 id 또는 낱말(예: `kitchen`, `asphalt`, `school`). Poly Haven API(`api.polyhaven.com/assets?t=…`, `/files/<id>`)와 ambientCG API(`ambientcg.com/api/v2/full_json`)만 씀.
- 하는 일: 새 빈 폴더에 받기 → 그림·JSON으로만 열기(실행 금지, `py -I`) → 줄이기(`deck-v2-src/prep_assets.py`와 같은 일):
  HDRI는 4k .hdr를 필름 곡선으로 톤 매핑해 반사용 1024×512 + 장면 배경용 흐린 자르기 1600×900 + HTML 장 배경용 아주 흐린 960×540,
  텍스처는 색 1k · 노멀/거칠기 512, glTF 모델은 버퍼·그림을 data URI로 묶고 텍스처 512로.
- 출처 URL·라이선스(CC0)·고른 이유를 NOTICE 표에 자동으로 한 줄씩. 받은 원본은 저장소에 넣지 않음.
- 크기 예산을 지키게: 이번 덱은 사진·텍스처 19개 + 모델 2개를 넣고도 약 6~7MB.

### 6-2. `scene3d` 프리셋 (이름 있는 함수 + 인자)
- `dress(S, kind)`: 장면 종류 → 환경(`SEG` 표: road · hall · kitchen) → PMREM 반사 + 흐린 사진 배경(살짝 시차) + 직접 빛 줄이기(`lightK`) + 후처리 기본값.
- 재질 프리셋 `PH`: `plastic`(클리어코트) · `metal` · `paint`(자동차 도장) · `glass`(환경 반사만 더하는 유리 층) · `tint`(옅은 유리색), `pbr(set, 반복)`(색·노멀·거칠기 묶음).
- 후처리 `draw()`: RenderPass → UnrealBloom(문턱 0.9, 정말 밝은 것만) → 마지막 셰이더(초점 밖 흐림 · 비네트 · 그레인 · 부드러운 S 곡선). 장면은 `S.fx = {focus, r, blur, bloom}` 또는 `S.focusObj`(그 물건에 초점)만 정함.
- 카메라: 단계마다 `[위치, 바라볼 곳]` 표를 두고 부드럽게 옮김 + `camDrift`(아주 느린 트럭·달리, 매 프레임 원위치 후 더하기라 장면 코드와 안 싸움).
- 약한 PC: 평균 40ms가 넘으면 ① 후처리 끄기 ② 해상도 1.5→1→0.75→0.5 ③ 그림자 갱신 멈춤. `?fx=1` 늘 켬(점검·사진), `?fx=0` 끔.
- WebGL 없을 때: `shoot.py --stills`가 장면마다 마지막 단계를 1280×720으로 찍고, build.py가 `.fb` 배경으로 넣음. 같은 장면 사진이 보여요.
- 실제 모델이 손으로 만든 것보다 나을 때만 모델(이번엔 도자기 말 조각상, 둥근 안경). 나머지(웍·그릇·밥알·김치·달걀)는 lathe/instanced로 직접.

### 6-3. 유리 판 슬라이드 스킨 (`glass` 스킨)
- 배경: HDRI에서 자른 아주 흐린 사진(`--hb-road` · `--hb-hall`) 위에 위→아래 어둠막 + 강조색 빛 한 점 + 가장자리 비네트. 밝은 구간 = 길, 어두운 구간 = 시험장.
- 판: `backdrop-filter: blur(22px) saturate(150%)` + 흰 빛 위 테두리(inset 1px) + 왼쪽 위 흰 빛 → 오른쪽 아래 강조색으로 흐르는 빛 테두리(mask 한 겹). 지원 안 하면 짙은 단색 판.
- 아이콘: Lucide 하나만, 선 굵기 2 하나만, 둥근 사각 「배지」(`.bd`)에 넣고 강조색 빛.
- 움직임: 빌드마다 흐림 10px→0 + 28px 올라오기 + 0.97→1 (outExpo), 섹션이 바뀌면 빛 한 줄기가 화면을 훑음(`#wipe`). 길이는 400ms·700ms 두 가지만.
- 대비: 글자 #eef2ff / 보조 #a9b3cf가 판 위에서 4.5 이상이 되게 배경을 충분히 어둡게.

### 6-4. 디자인 시스템을 한 곳에 (다음 판 규칙)
- 토큰은 `deck.css` 맨 위 `:root` 두 곳(색 · 글자 크기 · 간격 · 모서리 · 움직임 시간)과 `deck.js`의 `P`(3D 색) 하나뿐. 슬라이드는 토큰만 씀.
- 부품: 유리 판(`.card` 등) · 나란히 비교(`.pair`/`.screens`) · 시간 줄(`.tl`) · 카드 격자(`.trio` `.appgrid` `.board`) · 큰 문장(`.stmt .big`, `.capline`) · 부탁 카드(`.prompt`) · 등식 막대(`.eqbar`).
- 3D 프리셋: `SCENES.<이름>`은 모두 `{scene, camera, labels, setStep(n, snap), update(dt, t, snap), fx, focusObj}` 모양. 새 장면은 `dress`가 환경·후처리를 입혀 줌.

### 6-5. 최고의 재료 목록 (라이선스 깨끗한 것만)
| 무엇 | 고른 것 | 라이선스 | 왜 |
|---|---|---|---|
| 한글 글꼴 | Pretendard 1.3.9 가변(이 페이지 글자만 잘라 이름을 「TS Deck Sans」로 바꿔 넣음) | SIL OFL 1.1 (예약 이름 때문에 수정본은 이름 변경) | 한글 UI·제목에 가장 많이 쓰는 글꼴, 굵기 45~920 하나로 |
| 비상 글꼴 | Noto Sans KR 부분 글꼴 | SIL OFL 1.1 | 저장소 기본. Serif는 빼서 약 200KB 절약 |
| 아이콘 | Lucide 1.75 | ISC | 이미 동봉, 선 굵기 하나로 통일 |
| 3D 엔진 · 후처리 · 모델 읽기 | three.js r128 + examples/js(EffectComposer · UnrealBloomPass · GLTFLoader) | MIT | ES5 빌드라 학교 PC에서도 돎 |
| 움직임 | anime.js 4.5 | MIT | 동봉 |
| 환경 사진(HDRI) | Poly Haven: evening_road_01 · school_hall · blinds | CC0 | 실제 하늘·강당·부엌 빛과 반사 |
| 재질 | Poly Haven: asphalt_02 · aerial_grass_rock · wood_table_001 · marble_01 / ambientCG: Paper003 | CC0 | 바닥·풀·책상·조리대·종이 |
| 모델 | Poly Haven: horse_statue_01 · round_spectacles | CC0 | 손으로 만든 것보다 확실히 나은 두 가지 |
| 쓰지 않은 것 | 유료 이미지·영상 생성, 출처 불명 사진, GSAP, ffmpeg | - | 저장소 규칙 |

### 6-6. 그림책 장 (스타일 바꾸기를 의도적으로)
- 김치볶음밥 이야기만 포근한 툰 부엌: `MeshToonMaterial` + 5단 부드러운 램프 + 펠트 얼룩 텍스처, 둥근 소품(`rbox`), 창 햇살(가산 판 3장) + 먼지 점, 부드러운 그림자. 사진 환경 없음(`SEG.robot = none`).
- 주인공은 CC0 리깅 로봇(RobotExpressive.glb): `AnimationMixer`로 단계·시간마다 동작을 고르고(`want`), 자리·방향은 `where` 표로. 날아오는 레시피·도구는 포물선 + 빛 꼬리 + 착지 찌그러짐(`squash`).
- 들어갈 때 그림책 쪽이 펼쳐지는 전환(`pageOpen`), 화면은 둥근 쪽 틀 안. 끝은 키노트 문구 「이게 하네스!」 → 「AI에게 도구와 레시피를 주는 것」(아이콘이 낱말 옆에 착).
- 하네스로 옮길 때: `story-toon` 프리셋 = 툰 재질 함수 `TM` + 부엌 세트 `toonKitchen` + 동작 표(`want`/`where`) + 도장 낱말(`.stamp`) + 결론 문구(`.punch`).
