# 게임 기획 한 장 (spec) — 요청을 부품으로 바꾸는 표

AI는 **짧은 spec JSON 하나**만 쓴다(내용 + 방식 + 디자인 방향). 엔진·부품·디자인·점검은 도구가 맡는다. 형식 전체는 `spec.schema.json`, 예시 10개는 `assets/spec-examples/`.

## 1. 요청 → 방식(mechanic)
| 선생님·사용자 말 | mechanic | items 한 칸 | 비고 |
|---|---|---|---|
| 퀴즈·종 울리기·복습·OX 퀴즈 | `quiz` | `{q, choices[2~4], answer, exp}` 또는 `{type:"ox", q, answer:0/1}` | 팀 차례제, 보너스, 틀린 문제만 다시 |
| 모둠 OX 서바이벌·탈락전 | `survival` | OX 문제만 | 팀마다 라이프, 마지막 생존 팀 우승 (`lives`) |
| 방탈출·미션·협동 | `escape` | quiz 형식 + `clue`(단서 글자) | 자물쇠 3~6개, 제한 시간(`seconds`), 오답 시간 감점 |
| 짝 맞추기·카드 뒤집기·받아쓰기 낱말 | `match` | `{a, b}` | 3~8쌍 |
| 빙고(영어 단어·용어) | `bingo` | `{word, clue}` | `grid` 3/4, 낱말은 grid²개 이상, `world.speak`로 읽어 주기 |
| 주사위 말판·보드게임 | `board` | quiz 형식 | `tiles`, `maxTurns`, 칸 문제는 items에서 |
| 분류·끌어서 넣기·배달 | `sort` | `{q, a}` | `a`가 통 이름(2~4개) |
| 위에 없는 방식 | (가장 가까운 mechanic + 부족한 부분만 직접 코드) | | `assets/components/*.js`를 복사해 새 부품 하나만 추가 → 아래 4번 |

## 2. 정해야 할 것 (기본값)
| 항목 | 기본 | 바꾸는 경우 |
|---|---|---|
| `use` | `class` | 가족·모임·동아리·개인용이면 `personal` (막지 않는다, 같은 도구) |
| `device` | `board` | 학생 태블릿이면 `tablet`(팀 선택 숨김), 폰이면 `phone` |
| `teams` | 0 | 모둠전이면 2~4 (survival은 2~4 권장) |
| `rounds` / `timer` | 전부 / 없음 | 수업 시작 5분 → 문제 5~6개. 칠판 팀전은 timer 20~30 |
| `design.subject/grade/mood` | 과목·학년·분위기 | 분위기: 긴장감·신남·차분·따뜻함·밝음 (「따뜻하게」「고급스럽게」 같은 말도 알아들어요) |
| `design.large` | false | 어르신·먼 화면 → true (personal에서 칠판 수준 글자) |
| `design.style` | 자동 | **12가지 스타일 중 하나** (네온/사이버 `neon-cyber` · 골드 럭셔리 `gold-luxury` · 팝 컬러풀 `pop-colorful` · 축제/파티 `festival-party` · TV 게임쇼 `tv-gameshow` · 글래스/3D `glass-3d` · 애니/카툰 `anime-cartoon` · 파스텔 귀여움 `pastel-cute` · 레트로/픽셀 `retro-pixel` · 미니멀 프리미엄 `minimal-premium` · 칠판/종이 `chalk-paper` · 자연/차분 `nature-calm`). 스타일마다 색·배경·배치·버튼·카드·점수판·제목·전환이 다른 「구성 언어」예요. 안 적으면 `design.words`의 스타일 낱말(네온·미니멀·글래스 …)이나 세계(우주·바다 …)에 어울리는 것이 `seed`로 뽑혀요 |
| `design.seed` | **매번 새로** | 안 적으면 만들 때마다 새 조합(스타일·배치·버튼·카드·점수판·제목)이 뽑히고, 뽑힌 숫자가 화면에 출력돼요(파일 안 `<meta name="ts-seed">`에도 있어요). 「아까 그거 다시」는 그 숫자를 `design.seed`에 적으면 똑같이 나와요 |
| `design.layout` · `choice` · `card` · `score` · `title_style` | 자동 | 직접 지정: layout `stack·split·bento·news·poster`(문제 화면 배치), choice `pill·tile·stamp·neon·note`, card `round·ticket·polaroid·hex`, score `led·chalk·sticker·banner`, title_style `outline·stack3d·stamp·underline`. 방식별 판 배치(짝 맞추기 grid·scatter·shelf·brick, 빙고 grid·tilt·shelf, 분류 bins·shelves·conveyor, 말판 snake·wave·stair, 서바이벌 row·bridge·stagger·arena, 방탈출 top·side)는 seed가 골라요 |
| `custom_css` · `custom_svg` | 없음 | **AI 자유 칸**: 도구가 만든 바닥 위에 AI가 더하는 한 끗. `custom_css`(6000자 이내, 글자 크기 34px 이상 규칙 그대로)·`custom_svg`(12000자 이내, `<svg viewBox="0 0 1920 1080">` 전체 무대 장식, 맨 뒤에 깔림). 바깥 주소·script·onclick·`?.` `??` 금지, 점검(check)과 디자인 점검을 그대로 통과해야 해요 |
| `design.theme` | **auto** | 기본은 auto. 요청이 한 세계를 분명히 가리킬 때만 이름 지정: `tv-studio`(방송국 퀴즈쇼) · `auditorium-bell`(강당 종 울리기) · `space-station` · `joseon-war-room`(거북선·임진왜란) · `antidote-lab`(해독제·연구소) · `sun-temple`(유적·이집트) · `post-office-night`(우체국) · `cell-feeding`(세포) · `recycle-robot`(분리배출). 그 밖에 notebook(필기 느낌)·spotlight(쇼 느낌)·default. **이식 테마(옛 스킨 9개)는 가장 마지막 선택지**: 요청이 그 세계를 직접 부를 때만(예: 「방송국」「거북선」「분리배출」) 쓰고, 자동 조합에서는 옛 진행자·LED 벽·ON AIR 간판·연단을 쓰지 않아요 |
| `design.words` | 없음 | auto일 때 장면 낱말 목록: 우주·바다·동화·숲·역사·긴장감·따뜻하게·고급스럽게·송년·스포츠·과학 … 도우미 캐릭터·배경·소품·축하 연출·글꼴·음악이 낱말로 정해져요 (낱말이 없으면 제목·과목·분위기에서 찾아요) |
| `design.hostCol` · `design.podiums` | false | 진행자를 왼쪽 큰 기둥으로 + 아래 팀 연단 줄(방송 느낌). quiz·survival·escape(칠판)에서만 기둥, 연단은 모든 방식. 방송국 테마(tv-studio)는 기본으로 켜져요 |
| `libs` | 없음 | 필요한 부품만 파일에 넣기: confetti(꽃가루)·katex(수식)·lucide(아이콘)·chartjs·anime·phaser(크다, 정말 필요할 때만). `motion`은 2020년 이전 크롬에서 안 돌아가서 `allow_modern:true`를 함께 적어야만 들어가요(아니면 만들기가 멈추고 anime.js를 권해요) |
| `allow_modern` | false | `libs`에 `motion`을 꼭 넣어야 할 때만 true (점검기는 주의로 표시) |
| `credit` | false | **선생님이 원할 때만** true → 결과 화면에 작게 「교사 스튜디오로 만듦」. 기본은 화면에 아무 표시도 없어요 (파일 속 보이지 않는 정보와 선생님 메뉴 맨 아래 「만든 도구」 줄만 있어요) |

## 3. 교실 기본 vs 개인 용도
- **class**: 문제 60px·보기 48px·작은 글 34px 이상, 버튼 110px 이상, 선생님 메뉴, 학생 정보 칸 없음.
- **personal**: 같은 도구, 글자 바닥만 완화(문제 44px·보기 36px). `large:true`면 class 수준.
- 둘 다: HTML 한 파일, 외부 이미지 없음, ES2017(`?.` `??` 금지), 입력칸 없음, 색만으로 정오답 표시 금지(✔/✖ 병행).

## 4. 순서
1. spec 쓰기 → 2. `python3 scripts/design.py --subject 과학 --grade 5 --mood 긴장감 [--use personal --large]` (build가 자동으로 호출하므로 보통 생략) →
3. `python3 scripts/build.py --spec spec.json --out game.html` (spec 오류는 「고칠 곳」으로 알려 줌) →
4. 점검 `python3 scripts/check_game.py game.html` (build가 자동 실행) → 5. 결과물로 보여 주기.
- 직접 코드가 필요할 때: 엔진 API는 `engine-api.md`만 본다. 새 방식은 `assets/components/core.js`의 `H.ask`(문제 흐름)를 재사용해 `COMP.mech.<이름>`을 하나 추가하고 `scripts/specs.py`의 `LIMITS`와 검사 규칙 한 줄을 더한다.
