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

## Pick the checkpoint (first rule that matches; the router line in SKILL.md is the same list)
| # | The message is | Checkpoint = where the first reply stops | Skips | Questions |
|---|---|---|---|---|
| 1 | has 「알아서」「바로」「그냥 해 줘」 | `none`: build, show, 2 tweak offers (assumptions in one line) | all stops | 0 |
| 2 | a change to an existing file | `build`: the changed file + 2 tweak offers | plan, script, storyboard | 0 |
| 3 | send / share / post / publish | `deliver`: the privacy check first | build | 1 (recommended answer) |
| 4 | one-screen tool (timer, picker, team maker, scoreboard, countdown, notice) | `none` | storyboard | 0 |
| 5 | vague (no topic or purpose) | `plan`: 3 pitches, one 추천 | everything after | up to 5 in one round |
| 6 | clear game / video / 10+ slide deck / report | `storyboard`: the 콘티 sheet (script text inside the frames); build only after the user reacts | plan | 1 |
| 7 | anything else clear | `build`: first working file, then 「이대로 쓸까요, 한 군데만 고칠까요?」 | | 1 |
- A game or a video is rule 6 even when the request is short; never go straight to a finished file. Rule 1 beats every other row, so 「알아서」 never stops at `build`.
- Each stop shows the artifact + one recommended next action, so 「네」 continues. At most 3 stops in a whole job (plan, storyboard, first build).
- Between stops keep going without asking. User says 「바꿔 줘」 at a stop: change that artifact only, re-show, go on. Never restart from stage 1.

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

## Final checkpoint (the LAST message of every job, even 「알아서」 and even when a helper agent did the building)
1. **End with an answer, never a status.** The last message must contain: (a) the finished file's full path, (b) how to open it (「더블클릭하면 브라우저에서 열려요」 / PowerPoint), (c) the check result in one line (PASS, or what is still open and why). Never end on 「서브 에이전트가 만드는 중이에요」, 「백그라운드에서 진행 중」 or a plan. If a helper is still running, wait for it, then answer; if you cannot wait, say plainly that it is NOT finished and where the partial file is.
2. **No blanks in the deliverable.** `[대괄호]`, `20XX`, `OO`/`○○`, `000`, 「학교명」 must never ship. Fill them with a plausible stated assumption (today's date and school year, generic 「우리 학교」, 「3학년」) and say the assumption in one line, OR collect the true unknowns in the spec as `"fillins": [...]` and show them as a short **「바꿔 넣을 곳」** list in the final message (name, which slide). The slides review and `pptx_check.py` FAIL on any other leftover.
3. **A PowerPoint was looked at.** With `.pptx`: report the `pptx_check` result (placeholders, text fit). Show the rendered PNG sheet (`deck.py ... --review DIR` writes it). Real drawing needs LibreOffice (~350MB; ask first, `ensure.py libreoffice`); without it the picture is an APPROXIMATE preview drawn from the shapes: say so in plain words (「대략의 미리보기예요, PowerPoint에서 한 번 열어 보세요」).
4. A report/data job: say which columns were treated as identifiers and hidden (`teacher-data`).

## Rules
- Plain Korean, no dev terms. Artifacts are shown, not described; Claude app: artifact; Claude Code/Codex: open the file.
- Never invent facts for 대본 (mark 「확인 필요」); sources recorded for deliver stage.
- The storyboard sheet is a drawing aid, not a deliverable; it contains no student data.
- Do not read raw spreadsheet rows at any stage (teacher-data does it).
- Keep each artifact one screen. If it grows, cut.
