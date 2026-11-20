---
name: teacher-data
description: "Turns anyone's spreadsheets (CSV/XLSX: scores, surveys, budgets, sales) into an easy offline chart report without the AI reading raw rows. Use when a teacher or anyone wants to compare groups, see a trend or summarize a survey; names are hidden."
license: Apache-2.0
---

# Teacher Studio - Data Analysis Weapon

Respond in the user's language. If the user brings a template or reference, use it first (ask-first rule: `../teacher-studio/references/ask-first.md`).

Use for 「반별 평균 비교해 줘」「설문 결과 그래프로」「가계부 정리」「매출 추이」. Not for one-off arithmetic on a few typed numbers (do it inline), nor slides/games (-> teacher-slides / teacher-game; they can embed the chart numbers).

## Hard rules
1. **Never read the data file yourself** (no Read/cat/head on it). Run scripts; read only their aggregate output.
2. Never put raw rows, names, phones or e-mails in chat, specs or output. The original file is never modified; nothing is sent anywhere.
3. If `profile_data.py` reports personal columns, say once: 「학생 이름이 보여요. 가명으로 바꿔서 분석할게요」 and go on (pseudonyms are automatic).
   - Names that are ALREADY pseudonyms (학생01, ID003 ...) are recognised: kept as is, not warned about, and the privacy self-check skips them (no false FAIL). ID-like columns (번호, 학번, id, 출석번호, 순번) count as identifiers: never used as labels and never shown. Top/bottom lists show anonymous ranks (상위 1위 ... 하위 1위) by default. **The user wins**: 「가명으로 보여 줘」 -> plan `"show_labels": true` (pseudonyms); 「번호/학번도 보여 줘」 -> plan `"show_ids": true` (real 번호 from the column, local-only report). When you set either, tell once: 「이 파일은 밖으로 보내지 마세요」 (the report notes it; `check_report` turns the ID check into a WARN). You still never read the raw rows.
4. Report is for people: conclusion first (one sentence a child understands), 3 lines, then charts with plain titles + units.
5. Fix loop max 2, then tell the teacher plainly (ADR 0011). Speak Korean, plain words, no dev terms.

## Steps (do them yourself in this chat, 4 commands, about 1 minute; no helper agent)
1. **Ask first (ask-first.md, 0-3 questions, each with a recommended answer; skip if clear or 「알아서」)**: who reads it? (추천: 학부모 / 초등 / 선생님 / 전문가) · what to compare (only if the columns do not make it obvious) · also want an Excel file? (추천: 아니요)
2. `python3 scripts/profile_data.py FILE [--sheet S] --json` -> schema, types, missing, units, PII, suggestions. `.xlsx` needs openpyxl: if the output has `need_install`, show its `prompt` and rerun with `--yes` only after consent.
3. Write a plan (copy from `assets/spec-examples/`): `python3 scripts/analyze.py --data FILE --plan plan.json --out agg.json`
   Types: `overview` (**wide table, one column per subject: use this first**; one plan line = stats of EVERY numeric column + score bands + top/bottom (pseudonyms, or groups with `group`) + which columns move together + 「다음에 해 볼 일」; the headline names all columns, never just the first), `groupby` (compare), `change` (before/after per group), `trend` (over time), `distribution` (counts/bins), `likert` (survey scale), `crosstab`, `correlation`. Filters, `top`, `test` (significance, only with n>=5 per group), `metric`, `unit` are optional.
4. `python3 scripts/report.py --agg agg.json --out report.html --audience 초등|학부모|선생님|전문가 [--xlsx r.xlsx] [--csv a.csv]`. Wording and numbers come from the aggregates; override only via plan `narrative` (numbers still checked). If the user gave a logo/template, use its colours first: `--palette-from pal.json` (from `shared/design/color_from.py`, see `../teacher-studio/references/user-colors.md`; a means, not our design). `check_report.py` WARNs when chart colours look alike to colour-blind eyes.
5. `python3 scripts/check_report.py report.html --agg agg.json --source FILE` must print PASS. Fix the plan (not the HTML) and rebuild, max 2 times.
6. Show the page. Offer 2 tweaks (다른 눈높이로 / 엑셀로도). Mention correlation is not cause and small samples (the report already says so).

## Plan picker (from the `profile_data.py` output; first match, 1-4 analyses, one chart per question)
| The columns are | Plan |
|---|---|
| 3+ number columns side by side (국어·수학·과학 …), one row per person | one `overview` (add `"group"` when a 반/모둠 column exists). Do not add a `groupby` per subject |
| one category + one number, and the user says 비교 | `groupby` (`by`, `value`, `agg` mean for scores, sum for money) |
| a date column + a number | `trend` (`freq` month/week); money -> also `groupby` by 분류 with `"style": "share"`, `top` 5 |
| before/after or two test columns | `change` |
| 1-5 scale answers (매우 그렇다 …) | `likert`; free choices -> `distribution` |
| the user asks 「관계 있어?」 | `correlation` (say it is not cause) |
With 「알아서」 use the picker and go; the user's own question, when given, is always the first analysis.

## Quality bar (read the finished report once before showing it)
1. The first sentence answers the user's question for the WHOLE data (every subject/group), in words a child understands, with one number.
2. Each chart answers one question; its title says the question and the unit. No chart that repeats another.
3. No name, 번호 or 학번 anywhere (unless the user set the switch). Small groups (n < 5) are not compared as if certain.
4. One 「다음에 해 볼 일」 line the reader can act on. No cause claimed from a correlation.
5. Final message: file path · how to open · the headline sentence · which columns were hidden as identifiers · check PASS · 2 tweaks.

## Chart rules (built in)
Bar = compare, line = change over time, pie only <= 5 parts (else bar), stacked = shares per group. Rounded numbers with units, axis shows 「단위」, bars start at 0, colour never the only cue (values are printed), colour-blind-safe series colours, keep-all Korean, text >= 14 px, contrast >= 4.5:1.

## Checker (`scripts/check_report.py`)
Zero external requests (static + real browser), no storage/network APIs, no raw personal data (patterns + the real names/phones/e-mails of `--source`), chart numbers == aggregates, every number in sentences exists in aggregates, units on every chart, keep-all/size/contrast, conclusion at top, sentence length and hard-word ratio per audience, no overflow at 1280/390 px, all canvases drawn.

## Files
`scripts/`: `profile_data.py` · `analyze.py` · `report.py` (+`export.py` xlsx: summary + one sheet per analysis, formulas, native Excel charts, 「다음에 할 일」 sheet; names stay hidden; needs openpyxl via ensure, ask once) · `check_report.py` · `shots.py` · `make_samples.py` (synthetic practice files in `assets/sample-data/`) · `tdata.py` (shared helpers). `shared/` (design, fonts, vendor Chart.js, tools) is used from the skill folder when installed, else from the repo root.
Audience: 초등 = short friendly sentences, no stats words; 학부모 = polite plain; 선생님 = adds n and caveats; 전문가 = adds p-values, effect sizes.

## Pipeline (`../teacher-studio/references/pipeline.md`)
대본 = the analysis questions (what do you want to know?); 콘티 = chart plan, one chart per question (ask before running; never read raw rows). Checkpoint: the question list/chart plan, then the first report; deliver: print/PDF, names hidden (`deliver.py`).

Design rules (type, spacing, colour, ornaments, the 5-point 「밤티 검사」 gate): [`shared/design/DESIGN-RULES.md`](shared/design/DESIGN-RULES.md)
