# 엔진 API (engine.html을 읽지 말고 이 문서만 본다)

엔진은 76KB. **읽거나 다시 타이핑하지 않는다.** `scripts/build_game.py`가 엔진을 그대로 복사하고 데이터·로직·CSS만 끼워 넣는다.

```
python3 scripts/build_game.py --data game.json --logic logic.js [--css extra.css] --out game.html
python3 scripts/check_game.py game.html
```
작업 공간(코드 실행)이 없을 때만 engine.html 전체를 복사해 GAME / GAME LOGIC 블록만 바꾼다.

## 1. game.json (= window.GAME)
| 키 | 기본 | 뜻 |
|---|---|---|
| title, subtitle | | 제목 화면 글자 |
| theme | "arcade" | arcade·space·fairytale·hanok·sports·detective·forest·ocean·gameshow |
| themeOverride | | `{primary, accent, bg1, bg2, text, card, cardBorder, good, bad, mood, bgType}` 일부만 바꿔도 됨 |
| teams | 0 | 0 = 개인, 2~6 = 팀 |
| teamChoice | true | false면 제목 화면 팀 선택 버튼 숨김 (개인 태블릿용) |
| timer | 0 | 문제당 초 (로직에서 `NG.timer.start(G.timer, fn)` 해야 동작) |
| music | true | false = 배경음악 끔 |
| calm | false | **차분 모드**: 흔들림·번쩍임 끔, 정답/오답 연출과 소리를 부드럽게 (시·명상·감상 활동) |
| mascots | true | 제목 화면 기본 캐릭터 2개. 직접 그린 캐릭터를 쓰면 false |
| transition | "iris" | 장면 전환 iris·wipe·fade |
| bonusEvery | 4 | quiz-show 부품 보너스 간격 |
| items | [] | 문제·단계 데이터. **항목마다 객체 하나** `{...}` (키 이름 자유) |
| packs | | `["kenney-platformer-core"]` 그림·소리 팩 넣기 (300KB 늘어남) |

## 2. logic.js 계약
```js
window.GAME_LOGIC = {
  start: function(){ /* 카운트다운 끝나면 호출. 현재 장면(.screen)에 그리기 시작 */ },
  toText: function(){ return {index:i, total:n}; }   // 자동 점검용 상태
};
```
- 흐름: 제목(title) → 카운트다운 → `start()` → … → `NG.finish(d)` → 결과(result) → 다시 하기.
- `NG.finish({title, lines:["한 줄", …], total, ratio(0~1), score, unit:"송이"})` — 0.6초 뒤 결과 화면. 개인전: 별 3개(ratio 기준)+점수+맞힌 수, 팀전: 막대 그래프+우승. `NG.state.wrongList`가 있으면 「다시 볼 문제」.
- 협동·세계관 결과(방탈출 성공 장면 등)가 필요하면 `NG.scene("result", function(el, d){...})`를 다시 정의하고 「다시 하기」에 `NG.restart()`를 연결.
- 개인 태블릿 제목 화면: `teamChoice:false` + `teams:0`이면 기본 제목 화면 그대로 써도 된다.
- 내 장면이 필요하면 `NG.scene("stage", function(el, data){...})` 정의 후 `NG.go("stage", data)`. **장면 그리기는 반드시 장면 함수 안에서** (`NG.go`는 기존 화면이 사라진 뒤 비동기로 붙음).
- 제목 화면을 바꾸려면 `NG.scene("title", fn)`을 다시 정의. 시작 버튼에서 `NG.setupTeams(n); NG.go("countdown")` 호출.
- 선생님 메뉴 연결: `NG.teacher.hooks = {next, skip, reveal}` (다음/건너뛰기/정답 보기).

## 3. 함수 목록
**흐름**: `NG.go(name, data)` · `NG.scene(name, fn)` · `NG.finish(d)` · `NG.restart()` · `NG.pause(bool)` · `NG.paused`
**시간** (가상 시계, 일시정지 자동 반영 — setTimeout 대신 사용): `NG.after(ms, fn)→id` · `NG.cancel(id)` · `NG.wait(ms)→Promise` · `NG.onUpdate(fn(dt초, t))` · `NG.offUpdate(fn)` · `NG.now()`
**입력** (콜백 인자: `onStart(e)`, `onMove(e)`, `onDrop(center{x,y}, e)`, `onTap(e)`): `NG.button(el, fn)` (누름 효과·소리 포함, 일시정지 중 막힘. 메뉴 버튼엔 `data-always`) · `NG.drag(el, {onStart, onMove, onDrop(center)→true면 놓임, onTap(e)→18px 미만 움직이면 탭, onEnd(ok, "drop"|"tap"|"cancel")})` · `NG.hitTest(pt, el)` · `NG.snap(el, target)` · `NG.util.center(el)→{x,y}` (무대 좌표)
- 움직이는 대상은 click 대신 `pointerdown`으로 판정.
- 끌 요소에 CSS 애니메이션(둥실 등)을 주려면 **안쪽 요소**에 준다 (transform 충돌).
**점수·팀**: `NG.setupTeams(n)` · `NG.addScore(점수, 팀번호?, at?)` · `NG.nextTurn()` · `NG.currentTeam()` · `NG.combo(ok)` · `NG.state` = `{score, teams[{name,icon,color,score}], turn, correct, wrong, total, wrongList, phase}`
**정답·오답 한 번에**: `NG.feedback(ok, el, {text, silentBadge, record})` — 소리+반짝이+배지+콤보, `state.correct/wrong` +1, `record`(문장)는 결과의 「다시 볼 문제」로. 점수는 따로 `NG.addScore`. 두 번째 시도 정답을 따로 세려면 직접 변수로.
**HUD**: `NG.hud.setProgress(0~1)` · `NG.timer.start(초, onEnd)` · `NG.timer.stop()` · `NG.timer.add(초)` · `NG.timer.left`
**효과** `NG.fx.*`: `burst(x,y,{count,speed,colors})` · `sparkle(x,y,n)` · `confetti()` · `rain(emoji)` · `shake(0~1)` · `hitstop(ms)` · `flash(color, a)` · `float(text,x,y,color)` · `badge(text, "good"|"bad"|"info", ms)` · `toast(text)` · `pop(el)` · `wobble(el)` · `press(el)` · `countUp(el, to, ms, suffix)`
**소리**: `NG.sfx(name)` — tap select correct wrong coin jump hit explode shoot powerup levelup tick warn count go whoosh pop flip drumroll fanfare lose star · `NG.defineSfx(name, fn)` · `NG.music.start(mood)` — upbeat space cute korean sports mystery nature tension · `NG.music.stop()` · `NG.music.setTempo(1.3)` (긴장 올리기)
**배경**: `NG.bg.set(type)` — grid stars clouds petals pitch fog leaves sea spot · `NG.bg.custom(function(ctx, t, dt, W, H){...})` 캔버스에 직접 그리기 (매 프레임 지워진 뒤 호출)
**캐릭터**: `NG.char({color, size, shape:"blob"|"square"|"star", accessory:"none"|"crown"|"cap"|"leaf"|"antenna"})` → `{el, mood("happy"|"sad"|"wow"|"idle"), hop(h), squash(), react(ok), shake()}` · `NG.shade(색, -0.3)`
**그림 팩**: `NG.img(name)`(data URI) · `NG.imgEl(name, attrs)` · `NG.hasImg(name)` · `NG.imgNames(prefix)` · `NG.sprite(el, frames, fps)` · `NG.playSample(name, {rate, vol})`
**도구**: `NG.util` = `$ h(tag, attrs, html) esc rand randInt pick shuffle clamp lerp center` · `NG.overlay(html, onMount)` · `NG.closeOverlay()` · `NG.store.get/set` (이 기기에만, 학생 정보 저장 금지) · `NG.W=1920 NG.H=1080` · `NG.el.scene/hud/overlay`

## 4. CSS 클래스 (extra.css에서 덮어쓰기)
`.screen`(장면, 세로 흐름 정렬) · `.card` · `.btn` `.btn.small` `.btn.secondary` · `.h1` `.h2` · `.title` · `.choice` `.choice.correct` `.choice.wrong` · `.enter`(등장) `.pulse` `.shine`
- 변수: `--primary --accent --bg1 --bg2 --text --card --cardBorder --good --bad --font-display --font-body`
- 자유 배치는 `.screen` 안에 `position:absolute` 요소(또는 class `abs`)로. 흐름 여백(24px)이 자동으로 빠진다.
- `.card`를 불투명하게: `.card{background:var(--card)}` 를 extra.css에 (뒤 배경이 비치면 글자가 안 읽힘).
- 테마의 `skin`과 다른 모양을 원하면 `body[data-skin]` 규칙보다 구체적으로 쓴다 (`body .card{...}`).

## 5. 함정
- 화면 가장자리: 위 0~110px는 HUD(점수·⚙️), 아래 1040px 이하는 안내 띠·여유. **중요한 글자·버튼은 y 120~1020 안에** 둔다.
- 변수 `--muted`(흐린 글자)·`--btnText`(버튼 글자색)·`--cardText`도 밝은 배경 테마에선 extra.css에서 바꾼다.
- 전체 화면 고정 무대 1920×1080. 세로 태블릿은 위아래 여백이 생김 → 시작 화면에 「가로로 돌려 주세요」 한 줄 (classroom.md).
- `advanceTime(ms)`(점검용)은 장면 전환 애니메이션(실제 시간)을 기다리지 않는다. 자동 점검은 실제 대기 + advanceTime 섞어서.
- 백틱 문자열 안 `#fff;` 등은 점검기가 오탐하지 않지만, 오래된 크롬을 위해 백틱 대신 `+` 연결을 권장.
