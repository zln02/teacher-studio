# Data report content — what a careful analyst writes around the charts

The scripts aggregate and check numbers. This file decides which questions the report answers and what its sentences may claim (plan `narrative`, chart choice, order). Wording: `../teacher-studio/references/content-writing.md`. Build the report from this data's question; do not reuse a previous report's section order.

## Steps
1. **Question first.** Before any chart, write the 1-3 questions the user wants answered, as real questions (「〈집단〉 사이에 〈무엇〉이 다른가?」「〈기간〉 동안 〈무엇〉이 어떻게 변했나?」「무엇을 먼저 고쳐야 하나?」). No question given → propose them from the columns and get a 「네」, or state them as the assumption.
   - A report that only describes every column answers nothing. Columns outside the questions are left out or put in an appendix table.
2. **Know the data before interpreting it** (from the aggregates and the user, not raw rows): what one row is, who is included and who is missing, when it was collected, how each value was measured (scale, 만점, 단위), n per group, 응답률 for surveys. Put this in a 「자료 설명」 line. Unknown → ask or state 「확인 필요」.
   - Tell apart before computing: 중복 응답(같은 사람 두 번) · 무응답 · 「해당 없음」 · a real 0. Each changes the 분모 differently; say which 분모 each rate uses.
   - Groups are comparable only when 분모 · 기간 · 문항 wording match. If they do not, say so next to the comparison or do not compare.
3. **One claim, one chart.** Write the claim as a sentence first; that sentence is the chart's title. (When the data only allow exploring, a question title is honest: 「〈무엇〉은 어떻게 나뉘어 있나?」, with the observation written below.) Then choose the form by the claim:
   | claim | form |
   |---|---|
   | A is larger than B (few groups) | bar, sorted, zero-based |
   | change over ordered time | line (≥ 3 points); 2 points → two numbers and the difference |
   | share of a whole (≤ 5 parts, sums to 100%) | stacked bar or the numbers; pie only for 2-3 parts |
   | spread, typical value, outliers | histogram / dot strip / box with n |
   | relation between two measures | scatter with n; never a dual-axis line |
   | agreement scale (Likert) | diverging or 100% stacked bar, levels in order, n shown |
   | one number that matters | the number, its unit and its comparison base; no chart |
   A chart with no claim is deleted. Two claims in one chart → two charts.
4. **Keep the scales honest.**
   - Bars start at zero. A cut axis on a line chart is marked and said in words.
   - Same measure across charts → same axis range and same colour for the same group.
   - Percent charts say percent of what (분모) and show n. Never percent without n.
   - No 3D, no area for single values, no sorting that hides the order of ordinal categories.
   - Differences are reported in the right unit: 점, 명, %p. 20% → 25% is 「5%p 상승」; it is also 「25% 증가」 relative to the base. Both are correct for different questions; name which, and never write 「5% 상승」 for it.
   - Rounding: compute from raw counts, round once at the end. Rounded shares may sum to 99.9% or 100.1%, and 복수 응답 shares exceed 100%: add a note; do not adjust a figure to make it fit.
   - Under each chart: one sentence that states the point, and for anything shared outside the room, the numbers as a table for people who cannot read the chart.
5. **Treat small n with care** (matches the skill's rule: groups with n < 5 are not compared as if certain).
   - n < 5: no comparison sentence, and no display that could identify a person; merge groups or show 「자료가 적어 비교하지 않음」.
   - Hiding one cell is not enough when totals are shown: 전체 13명 and A반 11명 reveal that the hidden B반 is 2명. Hide a second cell, merge groups or drop the total so subtraction does not recover it. n < 5 is this skill's line for comparing; whether to publish also depends on what else the audience knows (a small school, a known event), so judge the sharing context too.
   - Small groups generally (heuristic: n < 20-30): give counts rather than percentages (「〈n〉명 중 〈k〉명」), avoid decimals, and say that one or two people would change the picture.
   - Averages hide shape: with skew or outliers give 중앙값 and the range too, and say which you used.
   - One class, one test, one survey round is one observation. Do not generalise to 「학생들은」.
6. **Write takeaways in plain language, bounded by the data.**
   - Each takeaway: what the number is → compared to what → how sure. 「〈A〉가 〈B〉보다 〈차이·단위〉 높음 (각 n=…).」
   - Words follow size and evidence: do not call a 1-2점 or 1-2명 difference 「크게」. A small or uncertain difference is not proof that groups are the same either: report what was observed and what limits the judgement (「〈A〉가 〈차이〉 높게 나왔으나 각 〈n〉명이라 한두 명에 따라 달라짐」), and say what data would settle it. Write 「비슷함」 only when the data support similarity (enough n, small spread), not as the default for 「모름」.
   - 상관 ≠ 원인: 「〈X〉가 높은 반이 〈Y〉도 높았음」, never 「〈X〉 때문에」 unless the design supports it. Before/after without a comparison group → 「달라졌음」, not 「효과가 있었음」.
   - State what the data cannot tell, in one line. Missing data and exclusions are reported, not hidden.
   - Audience level (`--audience`) changes vocabulary and amount, never the claim.
7. **End with next actions.** For each main finding: one thing to do, who can do it, and what to look at next time to see if it worked. If the data do not support an action, say what extra data would. Recommendations are labelled as suggestions, separate from findings.
8. **Order the report**: answer to the main question at the top (2-4 lines with the numbers) → the charts in question order → limits → next actions → 자료 설명 · 집계 방법.
9. **Protect people.** No names, 번호, 학번; no cell small enough to point at one student; no ranking of individuals. Sensitive columns (건강 · 가정 · 상담) → do not chart; `../teacher-law` if the user wants to share it.

## 전문가 점검표
- [ ] The report opens with the question(s) and their answers in numbers.
- [ ] Every chart's title is a claim sentence; every chart has 단위, n and 기준일/수집 시기.
- [ ] Chart form matches the claim; bars zero-based; cut axes marked; consistent scale and colour across charts.
- [ ] Percentages name the 분모 and show n; differences between percentages are in %p (a relative % change is labelled as such); rounding and 복수 응답 are noted where sums look off.
- [ ] 중복 · 무응답 · 해당 없음 · 0 were handled on purpose; compared groups share 분모 · 기간 · 문항.
- [ ] No comparison for n < 5; counts instead of percentages for small groups; 중앙값 given when the mean misleads.
- [ ] No causal wording from correlational or before/after data.
- [ ] Adjectives match effect size; an inconclusive difference is reported as observed with its limits, not as 「비슷함」 or 「차이 없음」.
- [ ] Limits stated: who is missing, what was not measured, one-time data.
- [ ] Each main finding has a next action and a way to check it; suggestions are marked as suggestions.
- [ ] Every number in a sentence exists in the aggregates (the checker confirms); nothing estimated by eye.
- [ ] No person identifiable; no individual ranking; no hidden count recoverable by subtracting from a total; the sharing context was considered.
- [ ] Each chart has a one-sentence reading; a shared report has the numbers as a table too.

## Note on sources
These are standard statistical-practice rules (question-first analysis, honest axes, n with every rate, correlation vs causation, complementary suppression of small cells). The n < 5 line is this skill's own rule; the n < 20-30 caution is a heuristic, not an official threshold. Neither is a legal safe harbour. A reviewer pointed to 개인정보보호위원회 가명정보 처리 가이드라인 (https://pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS217&nttId=11931) for re-identification risk; **not read today**, so nothing is quoted from it and privacy questions go to `teacher-law`.
