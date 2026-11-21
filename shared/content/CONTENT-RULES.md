# CONTENT-RULES — what goes inside, before how it looks

Read this before writing any content (deck, game, document, poster, report, plan, app). The format gates (`check`, `doc_check.py`, lints) only prove the file is well-formed. This page and the per-kind recipes decide whether the **material** is right.

Owner's bar: 「재료가 전문가 이상 급이 만든 느낌」. A practitioner in that field should be able to use the output as it is, without rewriting.

These are principles and decisions, not templates. Never copy wording or structure from a recipe or from `spec-examples/` into an output; two outputs on different topics must not read as the same skeleton with nouns swapped.

## Which recipe
| making | read |
|---|---|
| lesson material (slides, game, worksheet, activity) | `skills/teacher-studio/references/content-lesson.md` (+ `teacher-slides/references/content-slides.md`, `teacher-game/references/content-items.md`) |
| 공문 · 가정통신문 · 보고서 · 기관 보고 PPT | `skills/teacher-docs/references/content-docs.md` |
| poster · 홍보 PPT · SNS · 홍보 영상 | `skills/teacher-studio/references/content-promo.md` (+ `teacher-motion/references/content-motion.md`) |
| chart report from data | `skills/teacher-data/references/content-data.md` |
| plan · research · comparison (co-plan) | `skills/teacher-studio/references/content-plan.md` |
| web app · helper · calculator · simulation | `skills/teacher-studio/references/content-webapp.md` |
| every sentence in all of the above | `skills/teacher-studio/references/content-writing.md` |

## Top rules (all kinds)
1. **Reader and use first.** Name who reads it, where (TV at 8 m, phone, printed A4, 결재 화면) and what they do next. If either is unknown and it changes the content, ask once; otherwise state the assumption in one line.
2. **One purpose, said in one sentence, before writing.** If you cannot write 「이것을 본 사람은 ___를 한다/안다」 the content is not ready. Everything that does not serve that sentence is cut, not shrunk.
3. **Content before container.** Decide the claims, their order and the evidence first; then pick slide types, layouts and length. Do not fill a layout because it exists.
4. **Facts are verified or marked.**
   - Every number, date, name, definition, quotation and formula is one of: (a) from the user's own material, (b) checked against a source in this session, (c) marked 「확인 필요」. These are three different states, not three ways to pass (see 「Release status」 below).
   - User material can be old or contradict itself or an official source (last year's date, a changed rule, two different deadlines). Do not silently pick one: show the conflict to the teacher.
   - Not common knowledge → source on the page: who, what, year (and 기준일 for statistics).
   - Dates: compute the weekday, never recall it. Sums and percentages: recompute from the raw counts with the same 분모. Rounded shares may not add to 100% (33.3% × 3 = 99.9%) and 복수 응답 shares can exceed it; say so in a note instead of forcing the figures to fit.
   - Never invent statistics, quotes, laws, 성취기준 codes, links or "research says". An honest gap beats a confident error.
   - Illustrative numbers are labelled 「예시(가상 수치)」 on the same screen.
5. **Specific over generic.** Each sentence must be falsifiable or actionable. If a sentence fits any topic unchanged (「다양한 활동으로 효과적으로…」), delete or replace it with the particular fact, number, step or example. Exception: safety instructions, official wording (성취기준 원문, 법정 문구) and standing notices stay even though they repeat across topics.
6. **Shape follows the content.** Sequence → steps; comparison → table; one number → big number; cause → diagram. Three bullets are not the default shape of a thought.
7. **Level is chosen, not defaulted.** Vocabulary, sentence length and amount per screen match the stated grade or audience (`content-writing.md`). Plain is not childish.
8. **Legal and privacy lines.** No real student data, faces or contact details in content; third-party text, images, music and characters need a stated basis. When the request touches these, go to `skills/teacher-law` (it reads the current law; do not answer from memory, and do not store law text in recipes).
9. **Honest about limits.** Say what the material does not cover, what was assumed, what was not checked. Never claim a capability (AI, 자동 채점, 저장) the output does not have.
10. **Length is a budget.** Decide it from the use (minutes of class, one A4, one phone screen) and cut to fit. Do not pad to look thorough, and do not thin to look tidy: the budget caps filler, never depth (see 「Floor, not ceiling」). Cutting never removes a condition, an exception or a safety step.
11. **Numbers in the recipes are defaults, each with a reason.** Figures such as 「제목 15자」「5-7분」「5초」「1/3」 name a problem (unreadable from the back row, attention drifting, a first screen that does nothing, a quiz that is all recall). Meet the reason, not the number. Deviate when this content needs it and say why in one line; never bend the content to hit a number.
12. **Check the real thing, in real use.** The draft being right does not make the file right: after building, confirm on the final screen or printout that answers, units, deadlines and attachments survived (not cut off, not shown to students, not different from the 붙임). Then try it as someone who cannot see the picture, hear the sound or drag with a finger (per-kind recipes say how).

## Floor, not ceiling — the tools set the minimum, you set the level
The generators and gates guarantee a floor: the file opens, reads from the back row, has no leftovers, works offline. They do not decide how much it teaches or how good it looks. That is your job, and the tools must never make your output poorer than what you would have made without them.

- **Depth.** Before building, list what the best practitioner's version of THIS request would contain, then put it in: the thing itself drawn (기관의 위치, 지도, 도형, 장치), a source to read (사료 · 본문 · 실험 자료) with its citation, a worked example, the process step by step, an activity with stages, more than one check question with answers and reasons, the reply slip a notice needs, sources at the end. 「Cut」 in rules 2 and 10 means cut what does not serve the purpose; it never means shorten what does.
- **Per-screen limits are not content limits.** 「One message per slide」, character caps and item counts keep one screen readable. More to say → another slide, a panel, another round, another part, another page. Never fewer facts.
- **Where the tool has no place for it, add it yourself.** In this order: (1) the tool's own free fields (custom drawing, custom css / svg, diagram shapes, custom parts), (2) build that piece, or the whole file, yourself in the plain way. Then run the same gate on the result. A hand-made file that passes the gate beats a tool-made file that is thin.
- **Design.** Tool-picked colours, fonts and layouts are safe defaults, not requirements. Order: the user's design > a look you can justify for this topic and room (your own palette, illustration, composition) > the tool default. Whatever you choose still passes the gates: contrast, text size, no overflow, offline, privacy, no AI house look.
- **Last check before the final message:** 「Would I have made something richer, deeper or better-looking for this request without these tools?」 If yes, it is not finished: add what is missing.

## Release status — 「배포용」 or 「교사 초안」
Some facts cause harm when wrong. These are **blocking facts**: 정답과 채점 기준 · 제출 마감과 일시 · 신청 자격과 선정 기준 · 비용 · 안전 조건(실험 · 체험 · 급식 · 이동) · 법적 근거와 동의 · 공식 문구(성취기준, 조문). Add any fact a reader would act on without asking.

- Every blocking fact verified (from a checked source, or confirmed by the teacher for this use) → the output may be called 배포용.
- Any blocking fact still 「확인 필요」, or user material that conflicts with an official source → the output is a **「교사 초안」**. It does not pass the gate. Say so in the first line of the final message, mark it on the teacher-facing page (not on what students or parents see as fact), and list each open item: what, where in the file, how to confirm.
- Non-blocking 「확인 필요」 items (a side fact, a term that differs by textbook) may ship if listed.
- Keep a short verification note for the teacher: each blocking fact, its source or who confirmed it, and where it appears in the file.

## Expert self-review gate — 「이 분야 전문가가 그대로 쓸 수준인가?」
Run after the draft, and again on the built file. Any 「아니오」 → fix, then re-check. Report unresolved items to the user in plain words; do not hide them.

| # | criterion | pass when |
|---|---|---|
| G1 | 목적 | one sentence states what the reader does or knows afterward, and every part serves it |
| G2 | 정확성 | every fact is traced to user material or a checked source; numbers recomputed; dates and weekdays computed; **no blocking fact is 「확인 필요」** (otherwise status = 교사 초안, with the open items listed); conflicts in user material were shown to the teacher |
| G3 | 전문가의 눈 | the checks in the per-kind 「전문가 점검표」 all pass (the things a 수석교사 · 교감 · 장학사 · 홍보 담당 · 통계 담당 would flag first) |
| G4 | 구체성 | no sentence survives that would fit another topic unchanged; no filler words from the banned list |
| G5 | 수준 | a reader at the stated level understands it on first reading, and an adult does not feel talked down to |
| G6 | 분량 · 깊이 | fits the time / page / screen budget with nothing essential missing, and is at least as deep and as well made as what you would produce without the tools (Floor, not ceiling) |
| G7 | 고유함 | structure was derived from this content; it is not a copy of an example or of the previous output |
| G8 | 선 | no personal data; third-party material has a basis and a credit; limits and assumptions are stated |
| G9 | 쓸모 | the user can use it tomorrow without rework: answers included, times stated, 다음 할 일 clear |
| G10 | 실제 사용 | the built file was checked (nothing cut, answers not exposed, 본문 = 붙임); the task can be done without relying on colour, sound, a picture or dragging alone; nothing lets a reader work out a hidden person or count |

Reading test for G3 and G5: reread as (1) the strictest reviewer in that field looking for an error, then (2) the least prepared reader looking for a word they do not know. Fix what each finds.

## When checks disagree
Accuracy > clarity > completeness > polish. A wrong fact in a beautiful deck fails. If the content cannot be made right inside the budget, deliver less and say what is missing.
