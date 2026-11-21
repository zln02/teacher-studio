---
name: teacher-class-tools
description: Makes timer, picker, team maker, bracket and scoreboard as one offline HTML file for teachers and anyone (class, 가족·동호회). TV-readable and touch-friendly.
license: Apache-2.0
---

# Teacher Studio - Class Tools

Run the scripts as written with `python3`; on Windows type `py` instead (no `py`: `python`). Always the short command name, never an interpreter's full path (`C:\...\python.exe`).

Respond in the user's language. If the user brings a template or reference, use it first (ask-first rule: `../teacher-studio/references/ask-first.md`).

Quick, reliable tools for the moment a teacher asks for them ("5분 타이머", "발표자 뽑기", "모둠 나눠줘", "대진표", "점수판"). The AI writes a short spec; `build_tool.py` makes one offline HTML file and `check_tool.py` gates it.

## When to use / not use
- Use for: timer, picker, teams, bracket, scoreboard (class or personal/family/club use; do not refuse non-class use).
- Not for: quizzes or games (-> teacher-game), slides (-> teacher-slides), videos (-> teacher-motion). If the request is clearly a one-off the model can do better inline, say so and do that (no-regret rule).
- **Floor, not ceiling** (`shared/content/CONTENT-RULES.md`): one spec makes ONE tool. Do not shrink the request to fit it. Two tools asked for one event (「대진표와 점수판」), or rules the spec cannot hold (a sport's own scoring such as 21점·듀스·세트, 코트 배정, 리그전 순위표) -> the room wants them on one screen with those rules: make that page yourself as one offline HTML file with this skill's quality bar (the number the room reads is the biggest thing, one-tap buttons, 「효과 줄이기」「소리 끄기」, no storage, no network, no outside files) and gate it with `python3 ../teacher-studio/scripts/check_webapp.py <file>.html`; or build the tools separately when they really are used apart, and say how to use them together. The tool-picked look is a default: the user's colours or a look that suits the event may replace it. A page you make yourself must be ready the moment it opens, as our tools are: example entries already filled in (1팀 … 8팀, or numbers), the bracket drawn and the scoreboard showing on the first screen, every button doing something at once. Never start from an empty form that asks for input before anything appears.
- Speak Korean to the teacher, plain words. Do not mention HTML/JSON/spec unless asked. Show the result as an artifact.

## Steps (yourself, in this chat: write spec, one command, answer; under a minute)
1. Pick the tool. Do NOT ask when the request has the number it needs (「5분 타이머」「6모둠」) or says 「알아서」「바로」: use the defaults (numbers 1-30 for people, 4 teams, animal team names, sound on for the timer only) and say them in one line. Ask one numbered message only when the count of people or teams is unknowable.
2. Write a spec with the keys below from the request's own numbers and names (`assets/spec-examples/` = test fixtures, not patterns for each tool's shape), then:
   `python3 scripts/build_tool.py --spec spec.json --out tool.html`
   This builds and runs the checker. Fix and rebuild at most 2 times; then tell the teacher plainly what is off. A `NO-BROWSER` line = no screen can open in this environment: `PARTIAL` is then the normal finish; do not try a browser yourself, deliver the file and say the screen was not opened.
3. Show the page. Last message: file path · 「더블클릭하면 열려요」 · keys (Space/Enter = main action, 「전체화면」 button) · 2 tweaks (예: 「10분으로」「모둠 이름 바꾸기」). No privacy line for a tool that holds no names.

## Quality bar
1. The one thing the room must read (time left, the picked number, the score) is the biggest thing on screen and readable from the back row.
2. One obvious main button; everything works with one tap or Space.
3. Fair and visible: no repeat draws unless asked, teams differ by at most one, the bracket shows who meets whom.
4. Numbers, not student names, in the spec.

## Spec
```
{"tool":"timer|picker|teams|bracket|scoreboard","title":"...","use":"class|personal","sound":true,
 "design":{"subject":"과학","grade":5,"mood":"집중","seed":0,"large":false},
 "<tool>":{...}}
```
| tool | options |
|---|---|
| timer | `mode` countdown/stopwatch, `minutes` (0.1-180), `presets` [1,3,5,10], `warn_at` seconds (default 10) |
| picker | `items` or `numbers:{from,to}`, `no_repeat` (default true), `label` |
| teams | `items` or `numbers`, `team_count` (2-8) or `team_size`, `team_names` |
| bracket | `items` or `numbers` (2-16 entries), `shuffle` |
| scoreboard | `teams` (2-8 names), `steps` e.g. [1,5,10], `start` |
Design uses the shared design system (palette from subject/grade/mood), one embedded Korean font, no external files. The user's own logo/template colours come first: `"design": {"palette_from": "pal.json"}` (made by `shared/design/color_from.py`, see `../teacher-studio/references/user-colors.md`). `check_tool.py` WARNs when correct/wrong or team colours look alike to colour-blind eyes.

## Privacy rules (non-negotiable)
- Prefer numbers (1번, 2번...) over real student names. Default is numbers; if the teacher wants names, say once: "실제 이름보다 번호를 추천해요" and continue.
- Names typed into the page stay in that page: nothing is saved, sent, or logged (no storage, no network; the checker fails the build otherwise). Do not put real student names into the spec file.
- No accounts, no sign-in, no tracking.

## Classroom defaults
- Class: text >= 34px, buttons >= 80px, board-readable digits (timer 230px). Personal: normal sizes; `large:true` for far screens.
- Landscape 16:9 and portrait phone layouts. Words never split mid-word (keep-all).
- Game Wow kit (`shared/juice`, built in): timer = last-5 s ticks + gentle swell, end = fanfare + burst + confetti; picker = rack focus + drumroll + impact frame + burst; teams = cards fly in; bracket = champion fanfare; scoreboard = count-up + squash and a 「🏆 시상식」 podium (teams only, 3rd -> 2nd -> 1st, tap to skip). No random rewards, no fake urgency, no ranking of individuals.
- Always visible: 「🌙 효과 줄이기」 and 「🔇 소리 끄기」 buttons; the OS "reduce motion" setting is honoured too. Everything stops with reduced motion. End alert is text plus optional sound (default on for timer only). Tune/disable: build with `--no-juice` (comparison only); values in `shared/juice/README.md`.

## Checker (`scripts/check_tool.py`)
PASS required: no external request, no storage/network APIs, no `<form>`, inputs autocomplete off, keep-all, token contrast >= 4.5:1, text/button size floors, no overflow (landscape + portrait), tool logic (no duplicate draws, fair teams, bracket champion, timer end, count-up), reduced motion leaves nothing animating, no JS errors. Wow lint (`shared/juice/juice_lint.py`): flashes <= 3/s and none above 341x256 px, tap targets >= 44 px, class text >= 28 px, right/wrong never colour alone, 「효과 줄이기」+「소리 끄기」 present, the page's own work per frame <= 33 ms with the CPU throttled 4x (a low frame rate on a slow or busy test PC is a WARN, not a failure), click -> next frame <= 100 ms. Needs Playwright for the headless part (system Chrome is used; audio muted); without it only static checks run.

## Files
`scripts/build_tool.py` build · `scripts/check_tool.py` check · `scripts/shots.py` contact sheet for review · `assets/tools.js|css` runtime (copied as is) · `assets/spec-examples/` 5 fixtures.
`shared/` (design, fonts, tools) is used from the skill folder when installed, else from the repo root.

## Pipeline (`../teacher-studio/references/pipeline.md`)
Small, clear tools skip 콘티 and checkpoints: the spec list is the 대본; build, show, offer 2 tweaks. Deliver: `deliver.py tool.html` (pin on the TV, works offline).

Design rules (type, spacing, colour, ornaments, the 5-point 「밤티 검사」 gate): [`shared/design/DESIGN-RULES.md`](shared/design/DESIGN-RULES.md)
