# Web app and tool content — the task, the truth, the classroom

`webapp.md` gives the build path and the technical checks. This file decides what the app is for, what it says, and what it promises. Lesson-facing content also follows `content-lesson.md`; wording follows `content-writing.md`. Design the flow from this user's task; do not start from an example spec's parts and rename them.

## Steps
1. **Write the task flow before any screen.** 「〈누가〉 〈어떤 상황에서〉 → ① … → ② … → ③ 〈끝났다고 아는 순간〉.」 3-5 steps in the user's words. The app's first screen is step ①, not a menu, an introduction or settings.
   - Who drives: 선생님 on the TV for the whole class, or each student on a tablet? This changes amount of text, control size and pacing. Unknown and it matters → ask once.
   - Anything not on the flow is not in the first version.
2. **Define the result.** What does the user see at the end of the flow: a number with unit, an answer, a list, something to copy or print? Design that output first, then the inputs that produce it. Fewest inputs. The first screen must make the first action obvious without setup; a pre-filled example is one way to do that, not the goal.
   - An example value is labelled as an example (「예시」) and looks different from the student's own result, so nobody copies it down as their measurement.
   - If the learning point is to predict or observe before seeing the answer (탐구 · 실험 · 추정), do not show a result on opening: ask for the prediction or the input first.
3. **Fill it with real content for this class.**
   - helper: the questions students at this grade actually ask, in their words, including the wrong-headed ones; answers that are correct at textbook level, 2-3 short lines, with the next thing to try. Cover the unit's main 오개념.
   - calculator / simulation: the textbook's quantities, symbols, units and ranges; limits that match reality (no negative length, no speed beyond what the model covers); one worked case the teacher can verify by hand.
   - practice: items by `../teacher-game/references/content-items.md`; feedback says why, not only 맞음/틀림.
   - No placeholder text, no invented facts; unsure → 「확인 필요」 to the teacher (not shown to students as fact).
4. **State capability honestly, in the app and in the final message.**
   - `can` / `cannot` are written for this app: what it answers or computes, from what (준비한 설명 N개 · 이 공식), and where it stops (범위 밖 질문, 저장 안 됨, 채점 안 함).
   - Rules-based helpers are never called AI that 「이해한다 · 생각한다」; a simulation says which simplifications it makes (마찰 무시, 반올림).
   - The fallback answer for an unknown question admits it and points to the teacher or the textbook; it does not guess.
   - Never imply saving, grading, tracking or online lookup that does not exist.
5. **Make every state say something useful.**
   - Empty: an example already filled in or one line on what to do first.
   - Result: number + unit + one plain sentence that reads the result.
   - Wrong or out-of-range input: what is allowed and why, in one kind line; never NaN, 「오류」 alone or silence. After an error the student can correct and retry without losing the rest.
   - Labels are verbs or nouns the student knows (「계산하기」「처음으로」), short enough not to wrap on the real button (about 8자 is a useful warning line; test on the projector and a phone).
6. **Fit classroom constraints** (content side; the checker covers the technical side).
   - Time: the core flow fits in the minutes the teacher has (state it); one round ≤ 5-10분 unless asked.
   - Attention: one task per screen; no feature that invites off-task play unless that is the point.
   - Shared screen: nothing private typed on the TV; no names, 학번, photos; results never rank named students.
   - Network and devices: works offline, on an old Chrome, on a tablet in landscape; say so only as far as it was checked.
   - Sound off by default or one switch away; 30 tablets at once.
   - Access: the whole flow can be done with the keyboard alone, at 200% zoom, and makes sense read aloud by a screen reader (order, names of controls, results announced). Anything done by dragging also works by tapping or keys; nothing depends on colour or sound alone.
   - Age: reading load matches the grade; under-14 privacy and AI-service age limits → `../teacher-law` if the user wants accounts, logging or a live AI.
7. **Give the teacher the operating notes**: how to start (더블클릭), the one-line honest capability statement, how to reset between classes, what to check before class (the worked case), and what it does not do.
8. **Verify by doing the flow.** Walk steps ①-③ with the worked case and one wrong input; compare outputs with hand calculation; then run the build's checks. Report what was and was not tested.
   - Calculations: also try the edges (0, the smallest and largest allowed value, a decimal, a unit change) and check 단위 and 반올림 match the textbook's convention. A formula or constant you could not verify is left out of the app and named in the final message.
   - Walk the flow once more with the keyboard only, and once at 200% zoom.

## 전문가 점검표
- [ ] The task flow is written, and the first screen is its first step.
- [ ] Within a few seconds of opening the user knows what to do first and can do it without scrolling or setup (about 5초 is the usual yardstick; a predict-first activity deliberately shows no result yet).
- [ ] Example values are labelled and cannot be mistaken for the student's result.
- [ ] Inputs are the minimum; each has a unit and a label in student words.
- [ ] Edge values, units and rounding checked; error → correct → retry works.
- [ ] Usable by keyboard alone, at 200% zoom and by screen reader; no drag-only, colour-only or sound-only step.
- [ ] Content is real for this grade and unit; facts and formulas verified; a worked case matches hand calculation.
- [ ] `can` / `cannot` and the fallback are specific to this app and true; no implied AI, saving or grading.
- [ ] Every state (empty · result · wrong input · unknown question) gives a helpful line.
- [ ] Fits the stated minutes; one task per screen; nothing personal is typed or shown.
- [ ] Simplifications of a model are stated where the student sees them.
- [ ] Teacher notes include start, reset, pre-class check and limits.
- [ ] The flow was actually walked; untested parts are named in the report.
