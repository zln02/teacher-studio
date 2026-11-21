# deck-v3 · 하네스 사용 기록 (나중에 skills/teacher-motion으로 되돌려 넣을 것)

phase 1 (1~7장)을 모션 그래픽 덱으로 바꾸면서 `skills/teacher-motion`을 실제로 쓴 결과. 스킬·shared 파일은 고치지 않았어요 (읽기만).

## 도움이 된 것
- **anime.js 4.5.0 (shared/vendor)**: 그대로 썼어요. 다만 v3는 anime를 「시계」로만 쓰고(0→1 한 값), 모양은 직접 칠해요.
  한 요소의 transform을 여러 트윈이 나눠 쓰면 뒤로 감기가 깨진다는 SKILL.md 함정 2번이 맞았어요 → 요소마다 트윈 하나가 transform 전체를 맡아요.
- **SKILL.md 함정 1번** (anime는 지연 동안 시작값을 칠하지 않음): `MO.tw`가 시작 모습을 바로 칠하게 만든 이유.
- **DESIGN-RULES.md 5장 (움직임)**: 박자 값(160 · 420 · 700 ms)과 들어오기 곡선 (.16,1,.3,1)을 출발점으로 삼았어요.
  v3 토큰은 xs 160 · s 320 · m 620 · l 900 ms, 간격 90 ms로 조금 넓혔어요 (덱은 클릭 한 번에 한 박자라 영상보다 길게 보여도 돼요).
- **DESIGN-RULES 1장 (글자)**: 굵기 ≤ 800, 큰 글자 자간 −0.045em, 「」 따옴표 → v3 머리글에 그대로.
- **clipcheck.py (`window.__tsClip`)**: 카드 글자가 둥근 모서리 밖으로 삐져나오는지 보는 탐침. record.py가 add_init_script로 넣고, 덱 카드에 `data-fit`을 달아 썼어요.
- **syntax_check (ES2017)**: build.py가 `?.` `??`를 막는 것과 같은 규칙.

## 모자랐던 것 (되돌려 넣을 후보)
1. **클릭으로 넘기는 덱이 없음.** STAGE(`window.__stage`)는 시간이 흐르는 영상 하나를 전제로 해요 (`timeline(tl, ms)`, `seek`).
   클릭 단계(step)마다 한 박자, 뒤로 가면 끝 모습으로 바로, 장을 떠나면 다 멈추기 → 이 덱의 `MO.run` / `MO.stop` / `V3DIR` 같은 「단계형 무대」가 스킬에 필요해요.
2. **뜻에 따른 움직임 어휘가 없음.** 스킬은 ease 이름 목록만 줘요. v3의 MO(spring · snap · flip · gather · wipe · kin · stamp · shake)와
   「무엇에 어느 움직임」 표(친근한 것 = 통통, 결과·숫자 = 탁, 전→후 = 뒤집기 …)를 shared/design 쪽 움직임 규칙으로 올리면 좋아요.
3. **DESIGN-RULES 25번과 충돌**: 「Enter = fade + 12~24px travel」「one thing moves per beat」는 차분한 문서에는 맞지만,
   주인이 원한 모션 그래픽(넘쳤다 돌아오는 통통, 뒤집기, 도장)은 이 규칙으로는 못 만들어요. 「차분(문서) / 모션 그래픽(발표·영상)」 두 단계로 나누자는 제안.
4. **3D와 2D가 같은 토큰을 쓰는 길이 없음.** three.js 장면은 초 단위, DOM은 ms. v3는 `TOK.sec()` 하나로 맞췄어요 (표지 3D 카드 = TOK.m, 간격 TOK.gap).
5. **render_mp4.py는 클릭 덱을 못 찍어요** (`__stage.seek` 전용). 그래서 deck-v3-src/record.py를 따로 썼어요:
   Playwright 가짜 시계(page.clock) + 키 누르기 + CSS 애니메이션 currentTime 맞추기 → 프레임 → imageio-ffmpeg로 MP4·GIF.
   스킬에 「클릭 덱 녹화」(키 순서 + 단계별 머무는 시간)를 넣으면 다른 덱도 쓸 수 있어요.
6. **clipcheck.py 버그**: `cs.transform`이 `matrix3d(...)`이면 `/matrix/`는 맞지만 `match(/matrix\(/)`가 null이라 `[2]`에서 터져요
   (뒤집힌 카드 `rotateY(180deg)`에서 발생). 고칠 곳: `skills/teacher-motion/scripts/clipcheck.py` (그리고 같은 코드를 쓰는 다른 스킬 복사본) — matrix3d면 회전 0으로 보거나 건너뛰기.
7. **check_page.py는 게임·STAGE 페이지용**이라 덱에는 맞지 않아요 (문서 머리말도 「game」). 덱 넘침 점검은 record.py의 BOUNDS(무대 가장자리 · 넘침 · 글자 덩어리 겹침)를 썼어요.
8. **움직임 줄이기 점검이 없음.** record.py가 `reduced_motion="reduce"`로 클릭마다 끝 모습이 다 보이는지 따로 봐요. 스킬 점검기에 넣을 만해요.
9. **프레임 속도 점검이 없음.** record.py `--fps-check`가 실제 시계로 단계마다 rAF 간격(평균 fps · 가장 긴 프레임 · 50ms 넘는 비율)을 재요.
