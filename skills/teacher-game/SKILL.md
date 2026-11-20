---
name: teacher-game
description: "수업용 퀴즈·방탈출·빙고·단어 짝 맞추기 게임을 만들 때 씁니다. Use for original classroom games with play rules or scoring that can run in a single offline HTML file. Class timers, general websites, and existing code edits follow their own workflows."
license: Apache-2.0
---

# 교사 스튜디오 · 게임 (Teacher Studio · Game)

You write ONE short spec (content + mechanic + design direction). The scripts do the engine, the look, the sounds and the checks, so every model gets the same quality.
Reply in the user's language (Korean by default), plain words, no dev terms (file, HTML, spec, script -> 「게임 파일」「설계」). The user's own template, colours or question sheet come first.
Class use is the default; family, club and shop games are welcome with the same tool (`"use": "personal"`). Never refuse them or turn them into a lesson.

## Recipe (do it yourself in this chat: 3-4 tool calls, about 2 minutes)
Never hand the build to a helper agent or a background task. Never read `assets/engine.html`, `assets/components/` or `assets/themes/`.
1. **Decide without asking** when the request names a topic or says 「알아서」「바로」: mechanic (table below), 10 questions (5-6 for a 5-minute opener), `teams` 2-4 for a class on the board, `timer` 20-30 with teams. Ask (one message, numbered, each with a default) only when the topic or unit is missing.
2. **Show the question table first, unless told 「알아서」「바로」**: 번호 | 문제 | 정답 | 오답 보기 | 해설, then 「정답이 맞는지 확인해 주세요. '좋아'라고 하시면 만들게요.」 With 「알아서」「바로」 skip the wait and build in the same reply.
3. **Write `spec.json`** from the exemplar below. Open `references/spec-schema.md` only for a field the exemplar does not show; copy `assets/spec-examples/<closest>.json` only for a non-quiz mechanic.
4. **Say first** 「게임을 만들고 점검하는 데 2분쯤 걸려요」, then run ONE command (design + assemble + check + picture sheet):
   `python3 scripts/build.py --spec spec.json --out <이름>.html --review` (Windows: `py`)
5. **Act on the output, in this order** (2 rebuilds at most, then say plainly what is left):
   - `SPEC FIX NEEDED` / `FAIL` -> change the spec as the line says, rerun.
   - `CONTENT FIX` (the build stopped before assembling, 1 second) -> fix those questions in the spec, rerun. Add `--ok-content` only when the user gave these exact questions.
   - `WARN` -> leave it unless it names text the user would see cut or covered.
   - `sheet: <png>` -> open that picture ONCE and run the look check below. A problem -> change `design.words` / `seed` / `style` only, rebuild once.
   - `READY <path>` -> go to step 6. `PARTIAL` -> state the missing checks and offer the generated file when useful. For `FAIL`, fix the listed issues before using the file; use the fallback if two fixes fail.
6. **Last message, always a real answer** (never 「만드는 중」): full path of the file · 「더블클릭하면 브라우저에서 열려요, F = 전체 화면, ⚙️ = 선생님 메뉴(일시정지·정답 보기·점수 조정)」 · what is inside (문항 수, 팀, 시간) · check result in one line · 2-3 tweaks in plain words (「글자 더 크게」「문제 더 어렵게」「다른 분위기로」).

## Request -> mechanic (first match)
| 요청 | `mechanic` | one item |
|---|---|---|
| 퀴즈·복습·종 울리기·OX | `quiz` | `{q, choices[2-4], answer, exp}` or `{type:"ox", q, answer:0(O)/1(X), exp}` |
| 모둠 OX 서바이벌·탈락전 | `survival` | OX items only, `lives` |
| 방탈출·미션·협동 | `escape` | quiz item + `clue`; 3-6 items, `seconds` |
| 짝 맞추기·카드 뒤집기 | `match` | `{a, b}`, 3-8 pairs |
| 빙고 | `bingo` | `{word, clue}`, `grid` 3 or 4 |
| 주사위 말판·보드게임 | `board` | quiz items, `tiles`, `maxTurns` |
| 분류·끌어서 넣기 | `sort` | `{q, a}` (`a` = bin name, 2-4 bins) |
| anything else | closest mechanic; custom code only if the user insists (`references/advanced.md`) | |
「복습 게임」 with no type = `quiz` with teams. Pick another mechanic when the content is pairs (용어-뜻 -> `match`) or groups (-> `sort`).

## Spec exemplar (vary every value; do not copy the questions)
```json
{"title": "중2 과학 · 빛과 파동 복습", "subtitle": "모둠 대항 10문제",
 "mechanic": "quiz", "use": "class", "device": "board", "teams": 3, "timer": 25,
 "design": {"subject": "과학", "grade": 8, "mood": "신남", "words": ["빛", "무지개", "실험실"]},
 "items": [
  {"q": "물속 빨대가 꺾여 보이는 까닭은?", "choices": ["빛의 굴절", "빛의 반사", "빛의 분산", "빛의 합성"], "answer": 0,
   "exp": "빛이 물에서 공기로 나올 때 진행 방향이 꺾여요"},
  {"type": "ox", "q": "거울에 비친 상은 좌우가 바뀌어 보인다", "answer": 0, "exp": "평면거울은 좌우가 바뀐 상을 만들어요"}
 ]}
```
- Never write colours, fonts or sizes: the tool picks them (12 styles, new combination every build; the printed `design.seed` reproduces a look). You steer with `design.words` (2-3 scene words from the topic), `mood` (긴장감·신남·차분·따뜻함·밝음) and, only if the user asks for a look, `design.style`.
- Family / club / shop: `"use": "personal"`; far screen or elders: `"design": {"large": true}`; student tablets: `"device": "tablet"`; phones: `"device": "phone"`.
- The user's logo or template colours: `design.palette_from` (`../teacher-studio/references/user-colors.md`).

## Question quality bar (you are the only author of the content; the script checks the starred lines)
1. Every question comes from the named unit at that grade's textbook level. Not sure of a fact -> leave it out (or mark 「확인 필요」 in the table). Numbers, years, units: check twice.
2. Order easy -> hard. About 6 recall : 4 apply (a situation: 「물속 빨대가 꺾여 보이는 까닭은?」), not ten definitions.
3. ★ One sentence, 25-40 characters; choices are a word or short phrase (<= 16 characters).
4. ★ Wrong choices: same kind as the answer, about the same length, one common misconception. No 「모두 정답」「정답 없음」, at most one funny choice in the whole game.
5. ★ `exp` on every question: one line saying WHY, not repeating the answer word (the screen already prints 「정답: …」).
6. ★ At most 2 in 10 negative questions (「아닌 것은?」). No two questions that test the same fact.
7. Any answer position is fine: the tool balances positions itself.

## Look check (on the sheet picture; fix only what fails)
1. Reading order is question -> choices -> decoration. 2. No text cut off, covered or overlapping (top bar, 「팀 차례」 tag, host character). 3. The scene fits the topic (words/props match). 4. Text is easy to read on its background. 5. It does not look like the last game you made (else change `design.seed`).
Details and fixes per item: `references/design-rubric.md`.

## Changes after delivery
Change only what was said, in the spec, then rebuild with the same `design.seed` (printed by the build) so the look stays. 「글자 크게」 -> `design.large` · 「화려하게/차분하게」 -> `mood` · 「다른 모양」 -> new `seed`. Vague words (「애들이 헷갈려해」「밋밋해」) -> `references/teacher-language.md`. While iterating use `--no-check` (seconds), and run the full command once at the end.

## Hard rules
1. No field or storage for student names, 학번, photos; no public ranking of individuals. Team names are animals by default.
2. Questions the user confirmed or supplied are used as they are.
3. Copyright: inform in one line, do not block (`references/legal-advisory.md`); do not draw famous characters or reproduce lyrics.
4. One offline HTML file: no outside images, fonts or links unless the user asks (`"online": true`, say 「인터넷이 있어야 제대로 열려요」).
5. Old school Chrome: no `?.` `??` `replaceAll` `.at(` in any custom code; the checker fails them.
6. Keep the teacher menu, 소리 끄기, 효과 줄이기 and 전체 화면 buttons.
7. Checks are for YOU to fix first (shorten text, change layout). Only when the user wants that exact result: `"waive": ["text_size"|"overflow"|"hud"|"phone"]` plus one caution line. Contrast, script errors and a game that cannot finish cannot be waived.
8. The speed line of the check judges the page's own work per frame; a low frame-rate WARN on a slow or busy PC is not a failure.

## Files (open only when needed)
| File | When |
|---|---|
| `references/spec-schema.md` | a spec field not in the exemplar (all options, defaults) |
| `assets/spec-examples/*.json` | a working spec per mechanic |
| `references/content.md` | writing questions from the user's own material, word games, poems |
| `references/design-rubric.md` | the look check in detail |
| `references/teacher-language.md` | vague requests and complaints -> concrete changes |
| `references/game-types.md` | recommending a game type when the user has none |
| `references/advanced.md` | sound/effects kit tuning (`juice`), custom mechanics and custom art, legacy finished skins (`fire`), credit line, voice |
| `scripts/build.py` | the one command (`--no-check`, `--verbose`, `--review`, `--ok-content`, `--seed N`) |
| `scripts/check_game.py` · `design_review.py` | run by `build.py`; alone only to re-check a finished file |
| `../../shared/tools/sound_ears.py` | **optional audio check / custom effects**: `py sound_ears.py listen clip.wav` (plain-Korean loudness · clipping · too harsh/quiet · length · fits a kids' classroom; works for .wav with no install, richer with the optional earshot ears) · `sfx "물방울 똑" --out x.wav --seconds 1`. Not installed -> it says so, offers the install (size stated, only after a yes: `py ensure.py earshot --yes`) and the game keeps its built-in ZzFX sounds. Use when the user wants custom effect files, or when reviewing a finished game: check peaks (<= -1 dB), no clipping, effects of similar volume. Classroom-safe rules stay: sound-off button, no sudden loud sound, no flashing (<= 3 flashes/s). |

## Pipeline (`../teacher-studio/references/pipeline.md`)
대본 = the question table (step 2); 콘티 = screen flow sheet: `python3 ../teacher-studio/scripts/storyboard.py spec.json --html sheet.html --open`, shown before the build only when the router's checkpoint is `storyboard`. Skip both stops for 「알아서」「바로」. Deliver with `deliver.py game.html`.

Design rules (type, spacing, colour, ornaments, the 5-point 「밤티 검사」 gate): [`shared/design/DESIGN-RULES.md`](shared/design/DESIGN-RULES.md)
