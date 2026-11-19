---
name: teacher-class-tools
description: Makes classroom tools as one offline HTML file - timer, number/name picker, team maker, tournament bracket, scoreboard. TV-readable, touch-friendly. Use for any quick class or family tool request.
license: Apache-2.0
---

# Teacher Studio - Class Tools

Quick, reliable tools for the moment a teacher asks for them ("5분 타이머", "발표자 뽑기", "모둠 나눠줘", "대진표", "점수판"). The AI writes a short spec; `build_tool.py` makes one offline HTML file and `check_tool.py` gates it.

## When to use / not use
- Use for: timer, picker, teams, bracket, scoreboard (class or personal/family/club use; do not refuse non-class use).
- Not for: quizzes or games (-> teacher-game), slides (-> teacher-slides), videos (-> teacher-motion). If the request is clearly a one-off the model can do better inline, say so and do that (no-regret rule).
- Speak Korean to the teacher, plain words. Do not mention HTML/JSON/spec unless asked. Show the result as an artifact.

## Steps
1. Pick the tool and ask only what is missing, in one numbered message with defaults: duration / how many people / team count / team names / sound on?
2. Write a spec (copy the closest file from `assets/spec-examples/`), then:
   `python3 scripts/build_tool.py --spec spec.json --out tool.html`
   This builds and runs the checker. Fix and rebuild at most 2 times; then tell the teacher plainly what is off.
3. Show the page. Tell them the keys: Space/Enter = main action; "전체화면" button for the board.

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
Design uses the shared design system (palette from subject/grade/mood), one embedded Korean font, no external files.

## Privacy rules (non-negotiable)
- Prefer numbers (1번, 2번...) over real student names. Default is numbers; if the teacher wants names, say once: "실제 이름보다 번호를 추천해요" and continue.
- Names typed into the page stay in that page: nothing is saved, sent, or logged (no storage, no network; the checker fails the build otherwise). Do not put real student names into the spec file.
- No accounts, no sign-in, no tracking.

## Classroom defaults
- Class: text >= 34px, buttons >= 80px, board-readable digits (timer 230px). Personal: normal sizes; `large:true` for far screens.
- Landscape 16:9 and portrait phone layouts. Words never split mid-word (keep-all).
- Motion polish: timer = orbit ring + end pulse, picker = slot spin + impact-frame slam, teams = pop-in cards, scoreboard = count-up. All stop with prefers-reduced-motion. End alert is text plus optional sound; sound is a visible on/off button (default on for timer only).

## Checker (`scripts/check_tool.py`)
PASS required: no external request, no storage/network APIs, no `<form>`, inputs autocomplete off, keep-all, token contrast >= 4.5:1, text/button size floors, no overflow (landscape + portrait), tool logic (no duplicate draws, fair teams, bracket champion, timer end, count-up), reduced motion leaves nothing animating, no JS errors. Needs Playwright for the headless part (system Chrome is used; audio muted); without it only static checks run.

## Files
`scripts/build_tool.py` build · `scripts/check_tool.py` check · `scripts/shots.py` contact sheet for review · `assets/tools.js|css` runtime (copied as is) · `assets/spec-examples/` 5 specs.
`shared/` (design, fonts, tools) is used from the skill folder when installed, else from the repo root.
