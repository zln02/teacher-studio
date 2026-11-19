# 제작 공정표 (production pipeline) - one common line for every output

Every making job (deck, game, video, tool, report, document, web/app, plan) walks the same six stages. Only the CONTENT of each stage changes per type (`pipeline-types.md`). Each stage yields ONE small visible artifact the user can react to, never a wall of text.

| # | Stage | Artifact the user sees | Detail |
|---|---|---|---|
| 1 | 기획 plan | 3 pitches (one 추천) + one-line plan | `direction-step.md`; `scripts/direction.py` |
| 2 | 대본·내용 script | the words/rules/questions/spec list | type table |
| 3 | 연출·콘티 storyboard | numbered frame sheet | `scripts/storyboard.py spec.json --html out.html` |
| 4 | 제작 build | the first working file | skill build + checker must PASS |
| 5 | 수정 fix | the changed file, 2 tweak offers | `vague-fix.md`; max 2 loops |
| 6 | 배포 deliver | 배포 꾸러미 (size, phone/TV, print, privacy, 출처) | `scripts/deliver.py FILE` |

## Checkpoints (at most 3; each shows the artifact + one recommended next action, so 「네」 continues)
- **CP1 after 1 기획**: the pitches/plan line. Next: 「이 방향(추천 B)으로 대본부터 쓸까요?」
- **CP2 after 3 콘티**: the storyboard sheet. Next: 「이 흐름으로 만들까요?」 Stages 2+3 are shown together as one sheet (script text sits inside the frames); do not stop after 2 alone.
- **CP3 after 4 제작**: the first build, opened. Next: 「이대로 쓸까요, 한 군데만 고칠까요? (추천: 이대로)」 with exactly 2 tweak offers.
- Between checkpoints keep going without asking. One question per checkpoint, answerable by 「네」.
- 「알아서」「바로」「그냥 해 줘」: no checkpoint at all. Run 1-6 straight, state assumptions in one line at the start (no-regret rule). Still stop for the always-ask list below.
- User says 「바꿔 줘」 at any checkpoint: change that artifact only, re-show, go on. Never restart from stage 1.

## When to skip or merge stages (small and clear jobs)
- Clear request + one-screen result (timer, picker, team maker, scoreboard, countdown, 5-line notice): merge 1-3 into the spec; no storyboard, no CP1/CP2. Build, then CP3 only if the user has not said 「바로」.
- Clear request, many parts (10-slide deck, game, 30-second video, report): skip 1 (no pitches); keep 2+3 as one sheet = CP2; build; CP3.
- Vague request: full line, CP1 first.
- Plan/research (co-plan): stages 1-3 collapse to outline -> draft; one checkpoint (the draft); stage 4 is the sources check.
- Change request on an existing file: jump to 5, then 6 only if asked.
- A stage whose artifact would just repeat the user's own words is skipped; say nothing about skipping.
- Weak model: still follow the order; never run stage 4 before the user has seen the artifact of any checkpoint that applies.

## Always ask mid-way (even in 「알아서」; ask once, with a recommended answer)
1. The next step is irreversible or outward-facing: publish, share a link, send to parents or students, post online, overwrite the user's file.
2. A legal or privacy issue appears (student names/faces/grades, others' works, real people, AI evaluation): route per `teacher-law` / router R1.
3. The user's own material is needed: template, logo, source file, data file, textbook page.
4. The checker fails twice: stop, say so in plain words (「도구가 말을 안 들어서 직접 만드는 방식으로 바꿨어요」), offer the plain path.
5. Cost or install: size/time first (`ask-first.md`).

## Rules
- Plain Korean, no dev terms. Artifacts are shown, not described; Claude app: artifact; Claude Code/Codex: open the file.
- Never invent facts for 대본 (mark 「확인 필요」); sources recorded for deliver stage.
- The storyboard sheet is a drawing aid, not a deliverable; it contains no student data.
- Do not read raw spreadsheet rows at any stage (teacher-data does it).
- Keep each artifact one screen. If it grows, cut.
