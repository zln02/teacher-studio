# 제작 공정표 (production pipeline) - one common line for every output

Every making job (deck, game, video, tool, report, document, web/app, plan) walks the same six stages. Only the CONTENT of each stage changes per type (`pipeline-types.md`). Each stage yields ONE small visible artifact the user can react to, never a wall of text.

| # | Stage | Artifact the user sees | Detail |
|---|---|---|---|
| 1 | 기획 plan | 3 pitches (one 추천) + one-line plan | `direction-step.md`; `scripts/direction.py` |
| 2 | 대본·내용 script | the words/rules/questions/spec list | type table |
| 3 | 연출·콘티 storyboard | numbered frame sheet | `scripts/storyboard.py spec.json --html out.html` |
| 4 | 제작 build | the first working file | skill build + report which checks passed, failed or could not run |
| 4+ | 고명 garnish (optional, last touch of build) | the same file, dressed: backdrops / illustrations / motion words where they help reading | `shared/design/garnish.py env` -> Codex: a consistent picture set (`plan` prints the optional command, `finish` compresses + manifest); Claude only: `svg_backdrop()` / CC0 packs / preset E motion (`motion_e.js`). Skip on dense screens; no text, logos or faces in pictures; never required |
| 5 | 수정 fix | the changed file, 2 tweak offers | `vague-fix.md`; max 2 loops |
| 6 | 배포 deliver = 활용·전달 (teachers: 수업 활용) | 꾸러미: files for the use, how to open them on THIS PC, 2-3 use ideas, privacy, 출처 | `classroom-use.md`; `scripts/deliver.py FILE --use tv\|tablet\|print\|lms\|home\|archive` (general: screen\|share\|sns\|drive) |

## Pick the checkpoint (first rule that matches; the router line in SKILL.md is the same list)
| # | The message is | Checkpoint = where the first reply stops | Skips | Questions |
|---|---|---|---|---|
| 1 | send / share / post / publish | `deliver`: confirm outward action after the privacy check | build | 1 |
| 2 | the user asks to review a storyboard first | `storyboard`: show the draft and wait | | <= 1 |
| 3 | clear request, a small tool, or 「알아서」「바로」「그냥 해 줘」「묻지 말고」 | `none`: make and check the result (「알아서」: first the 1-2 essential questions it left open, one short message, `direction.py` `quick_ask`) | merge plan, script and storyboard as needed | 0 (「알아서」: <= 2, only who watches / where it is used) |
| 4 | vague and the choice would change the outcome substantially | `plan`: up to three pitches with a recommendation | | up to 5 in one round |

For clear games, videos, decks and reports, draft a storyboard internally when helpful. Plan or research work can merge the stages into an outline and checked draft. Changes to an existing file jump to stage 5.

## Always ask mid-way (even in 「알아서」; ask once, with a recommended answer)
1. The next step is irreversible or outward-facing: publish, share a link, send to parents or students, post online, overwrite the user's file.
2. A legal or privacy issue appears (student names/faces/grades, others' works, real people, AI evaluation): route per `teacher-law` / router R1.
3. The user's own material is needed: template, logo, source file, data file, textbook page.
4. The checker fails twice: switch to the available search, making and checking tools, and say so in plain words (「도구가 말을 안 들어서 직접 만드는 방식으로 바꿨어요」).
5. Cost or install: size/time first (`ask-first.md`).

## Final checkpoint (the LAST message of every job, even 「알아서」 and even when a helper agent did the building)
1. **End with an answer, never a status.** The last message must contain: (a) the finished file's full path, (b) how to open it (「더블클릭하면 브라우저에서 열려요」 / PowerPoint), (c) the check result in one line (PASS, or what is still open and why). Never end on 「서브 에이전트가 만드는 중이에요」, 「백그라운드에서 진행 중」 or a plan. If a helper is still running, wait for it, then answer; if you cannot wait, say plainly that it is NOT finished and where the partial file is.
2. **Use known facts in the deliverable; fill the rest with example values** (`shared/content/CONTENT-RULES.md`, 「Unknowns」). Every example value (date, place, amount, the user's own counts) goes in the `fillins` list, where supported, and the last message names each one under 「바꿔 넣을 곳」. Blanks only in hand-filled parts (회신서 · 신청서 · 서명란); no 「확인 필요」 cells, no draft stamp.
3. **A PowerPoint was looked at.** With `.pptx`: report the `pptx_check` result (placeholders, text fit). Show the rendered PNG sheet (`deck.py ... --review DIR` writes it). Real drawing needs LibreOffice (~350MB; ask first, `ensure.py libreoffice`); without it the picture is an APPROXIMATE preview drawn from the shapes: say so in plain words (「대략의 미리보기예요, PowerPoint에서 한 번 열어 보세요」).
4. A report/data job: say which columns were treated as identifiers and hidden (`teacher-data`).
5. **How it will be used** (`classroom-use.md`): the use was said -> run `deliver.py FILE --use <use>` and show its 꾸러미 lines; 「알아서」 -> `--use auto` (TV/screen + PDF), no question; and ALWAYS end with the delivery menu 「✅ 다 만들었어요! 어떻게 받으시겠어요? (추천: …)」 ①~⑤ (`deliver.py` prints it; the recommended one is already made; never ask whether the user is a teacher). Programs missing on this PC -> offer with the size, never install silently. Never upload.

## Rules
- Plain Korean, no dev terms. Show the created file, and offer a preview when the current conversation can display it.
- Never invent world facts for 대본 (leave out what you cannot verify and say so); sources recorded for deliver stage.
- The storyboard sheet is a drawing aid, not a deliverable; it contains no student data.
- Do not read raw spreadsheet rows at any stage (teacher-data does it).
- Keep each artifact one screen. If it grows, cut.
