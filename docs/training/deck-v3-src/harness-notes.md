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
10. **ai_look.py(「밤티 검사」)는 파일 전체를 봐요.** deck-v3.html은 v2의 옛 CSS(굵기 900 · 유리 판 등)를 아직 품고 있어서 v2와 똑같이 1/5가 나와요.
    v3 층(motion.css)만 재는 옵션이 있으면 바꾼 장만 점검할 수 있어요. 37장까지 다 바꾼 뒤 옛 CSS를 걷어 내고 다시 재야 해요.
11. **느린 PC 점검에서 찾은 것** (record.py --fps-check, 소프트웨어 렌더링 1280x720): 6장 사진이 매 프레임 필터째 다시 그려져 7 fps →
    `.kb{will-change:transform}` 한 줄로 71 fps. 「큰 사진·필터를 움직일 때는 합성 층으로」를 DESIGN-RULES 움직임 장에 넣을 만해요.
    고칠 코드(제안, skills/는 건드리지 않았어요): `var mt = cs.transform.match(/matrix\(([^,]+),([^,]+)/); var rot = mt ? Math.abs(parseFloat(mt[2])) : 0;`
    (`matrix3d`는 회전량을 0으로 보고 넘어가기. 뒤집힌 카드처럼 3D로 돈 요소는 화면 모양이 달라 어차피 이 탐침으로 잴 수 없어요.)
13. **phase 2에서 더 필요했던 것**: 「단계마다 이 요소를 이 움직임으로」를 HTML 속성으로 적는 길(`data-k="단계" data-m="snap|spring|grow|draw|tip|wipe"` + `data-at="ms"`).
    v3는 FX.v3gen 하나로 14~19 · 21장을 돌려요. 스킬의 무대에도 이런 선언형 단계가 있으면 덱마다 JS를 안 써도 돼요.
14. **그림 자리(illust-slot)**: 그림 화풍이 정해지기 전에 자리와 크기만 잡아 두는 약속(`<div class="illust-slot" data-scene="이름">`, `?slots=1`로 보기)이 스킬에 없어요. 슬라이드 스킬과 같이 쓰면 좋아요.
15. **한 엔진으로 두 덱**: build.py에 `--slides --out --title --foot --agenda`를 열어 AI 커닝 덱(ai-cheating/)을 같은 엔진으로 만들어요. 스킬의 덱 빌더도 「엔진 하나 + 슬라이드 파일 여러 개」를 기본으로 하면 좋아요.
16. **점검기가 꼭 잡아야 했던 것 (phase 2)**: 마지막 장에서 →가 더 안 넘어가면 녹화 · 점검이 끝없이 돌았어요(record.py에서 고침).
    숨긴 층(visibility:hidden)을 겹침으로 세지 않기, 큰 덩어리(전체 폭 컨테이너)끼리 겹침은 글자 실제 영역으로 다시 재기.
17. **소프트웨어 렌더링에서 3D 장면 점검은 아주 느려요** (1920x1080에서 로봇 장면 한 단계 3~5분, 한 번은 브라우저가 죽음). 3D 장은 960x540로 찍고, 글자 넘침은 2D 장 위주로 재는 편이 현실적이에요.
18. **스킨을 통째로 바꾸기 (D)**: 장마다 쓰는 값이 토큰(--v-*, --c-*)으로 모여 있어서, 새 스킨은 `skin-d.css` 한 파일(토큰 다시 정하기 + 틀 · 글자 · 면 · 장별 손질)로 1~2시간에 21장을 다 바꿨어요.
    스킬의 디자인 체계도 「토큰 → 부품 → 장」 3층을 지키면 같은 일이 쉬워져요. 밝은 판(html.light)도 토큰만 바꿔서 돼요.
19. **고정폭 주석 + 한글**: 고정폭 글꼴(Consolas)에는 한글이 없어서, 글꼴 목록에 Pretendard를 바로 뒤에 둬야 굴림체로 떨어지지 않아요 (`--mono:Consolas,…,"TS Deck Sans"`).
20. **멈춘 점검 프로세스**: 배경으로 돌린 점검기를 셸에서 멈춰도 python 자식 프로세스와 브라우저가 남을 수 있어요(한 시간 넘게 브라우저를 붙잡아 모든 녹화가 느려짐). 점검기 스스로 제한 시간을 두고 끝나게 하는 게 좋아요.
12. **녹화 함정**: Playwright `clock.pause_at()`을 부팅 뒤에 부르면 시간이 한 번에 건너뛰어 막 시작한 움직임이 끝나 버려요 → 설치 직후(goto 전)에 멈춰 두기.

## deck-e (스킨 E · 22장) — 2026-11-22
덱 번호: deck-e는 v3의 7장을 둘로 나눠(7 = AI 앱 화면 짚기, 8 = 주방 하나) 8장부터 v3보다 하나 커요. 위 기록의 장 번호는 v3 기준이에요.
21. **장 파일 표시로 효과 고르기**: `data-fx="eBig" data-e-inner="v3gen"` + `<div class="e-big">` 하나로 「큰 글자 장면 → 원래 장 효과를 한 단계 뒤로」를 어느 장에나 붙여요.
    스킬 무대에도 「장 효과 감싸기(앞에 단계 끼우기)」가 있으면 좋아요. 장 효과마다 `enter(장, 단계)`가 「뒤로 오면 끝 모습」을 지켜 주면 감싸기가 거의 공짜예요.
22. **옛 CSS와 이름 부딪힘**: 새 부품에 `.hl` `.chip` `.pn` `.tl`을 썼다가 옛 deck.css 규칙(위치 · 크기)이 그대로 먹혔어요 → 새 층은 모두 `e-` 앞붙이. 스킬 디자인 체계에도 「층마다 앞붙이」를 규칙으로.
23. **움직임 값 한 곳에서 줄이기**: TOK(xs · s · m · l · gap)를 E 층에서만 줄이니(620 → 260ms 등) 21장의 안쪽 움직임이 한 번에 빨라졌어요. 3D도 TOK.sec()를 써서 같이 따라와요.
24. **record.py 함정**: CSS transition이 키 누르기와 같은 박자에 생기면 SYNC가 처음 모습으로 멈춰 찍어요 → E 층은 transition 대신 스크립트 움직임(MO.tw)만 써요. `--deck`로 다른 덱 녹화.
25. **그림 조각(PUPPET) 시점**: deck.js 뒤쪽에서 채워지는 값을 움직임 층(앞쪽)에서 쓰려면 setTimeout 0 한 박자 뒤에 읽어야 해요.
