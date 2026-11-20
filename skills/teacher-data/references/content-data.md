# Data report content — what a careful analyst writes around the charts

The scripts aggregate and check numbers. This file decides which questions the report answers and what its sentences may claim (plan `narrative`, chart choice, order). Wording: `../teacher-studio/references/content-writing.md`. Build the report from this data's question; do not reuse a previous report's section order.

## Steps
1. **Question first.** Before any chart, write the 1-3 questions the user wants answered, as real questions (「〈집단〉 사이에 〈무엇〉이 다른가?」「〈기간〉 동안 〈무엇〉이 어떻게 변했나?」「무엇을 먼저 고쳐야 하나?」). No question given → propose them from the columns and get a 「네」, or state them as the assumption.
   - A report that only describes every column answers nothing. Columns outside the questions are left out or put in an appendix table.
2. **Know the data before interpreting it** (from the aggregates and the user, not raw rows): what one row is, who is included and who is missing, when it was collected, how each value was measured (scale, 만점, 단위), n per group, 응답률 for surveys. Put this in a 「자료 설명」 line. Unknown → ask or state 「확인 필요」.
3. **One claim, one chart.** Write the claim as a sentence first; that sentence is the chart's title. Then choose the form by the claim:
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
   - Differences are reported in the right unit: 점, 명, %p (not % when comparing two percentages).
5. **Treat small n with care** (matches the skill's rule: groups with n < 5 are not compared as if certain).
   - n < 5: no comparison sentence, and no display that could identify a person; merge groups or show 「자료가 적어 비교하지 않음」.
   - Small groups generally (heuristic: n < 20-30): give counts rather than percentages (「〈n〉명 중 〈k〉명」), avoid decimals, and say that one or two people would change the picture.
   - Averages hide shape: with skew or outliers give 중앙값 and the range too, and say which you used.
   - One class, one test, one survey round is one observation. Do not generalise to 「학생들은」.
6. **Write takeaways in plain language, bounded by the data.**
   - Each takeaway: what the number is → compared to what → how sure. 「〈A〉가 〈B〉보다 〈차이·단위〉 높음 (각 n=…).」
   - Words follow size: do not call a 1-2점 or 1-2명 difference 「크게」; if a difference is within what chance or one person explains, say 「비슷함」.
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
- [ ] Percentages name the 분모 and show n; differences between percentages are in %p.
- [ ] No comparison for n < 5; counts instead of percentages for small groups; 중앙값 given when the mean misleads.
- [ ] No causal wording from correlational or before/after data.
- [ ] Adjectives match effect size; 「비슷함」 is used when that is the truth.
- [ ] Limits stated: who is missing, what was not measured, one-time data.
- [ ] Each main finding has a next action and a way to check it; suggestions are marked as suggestions.
- [ ] Every number in a sentence exists in the aggregates (the checker confirms); nothing estimated by eye.
- [ ] No person identifiable; no individual ranking.

## Note on sources
These are standard statistical-practice rules (question-first analysis, honest axes, n with every rate, correlation vs causation). The n < 5 line is this skill's own rule; the n < 20-30 caution is a heuristic, not an official threshold. No Korean regulation is cited here (checked 2026-11-20: none looked up); privacy questions go to `teacher-law`.
