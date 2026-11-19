---
name: teacher-data
description: Turns anyone's spreadsheets (CSV/XLSX: scores, surveys, budgets, sales) into an easy offline chart report without the AI reading raw rows. For teachers and anyone; hides names.
license: Apache-2.0
---

# Teacher Studio - Data Analysis Weapon

Respond in the user's language. If the user brings a template or reference, use it first (ask-first rule: `../teacher-studio/references/ask-first.md`).

Use for 「반별 평균 비교해 줘」「설문 결과 그래프로」「가계부 정리」「매출 추이」. Not for one-off arithmetic on a few typed numbers (do it inline), nor slides/games (-> teacher-slides / teacher-game; they can embed the chart numbers).

## Hard rules
1. **Never read the data file yourself** (no Read/cat/head on it). Run scripts; read only their aggregate output.
2. Never put raw rows, names, phones or e-mails in chat, specs or output. The original file is never modified; nothing is sent anywhere.
3. If `profile_data.py` reports personal columns, say once: 「학생 이름이 보여요. 가명으로 바꿔서 분석할게요」 and go on (pseudonyms are automatic).
4. Report is for people: conclusion first (one sentence a child understands), 3 lines, then charts with plain titles + units.
5. Fix loop max 2, then tell the teacher plainly (ADR 0011). Speak Korean, plain words, no dev terms.

## Steps
1. **Ask first (ask-first.md, 0-3 questions, each with a recommended answer; skip if clear or 「알아서」)**: who reads it? (추천: 학부모 / 초등 / 선생님 / 전문가) · what to compare (only if the columns do not make it obvious) · also want an Excel file? (추천: 아니요)
2. `python3 scripts/profile_data.py FILE [--sheet S] --json` -> schema, types, missing, units, PII, suggestions. `.xlsx` needs openpyxl: if the output has `need_install`, show its `prompt` and rerun with `--yes` only after consent.
3. Write a plan (copy from `assets/spec-examples/`): `python3 scripts/analyze.py --data FILE --plan plan.json --out agg.json`
   Types: `groupby` (compare), `change` (before/after per group), `trend` (over time), `distribution` (counts/bins), `likert` (survey scale), `crosstab`, `correlation`. Filters, `top`, `test` (significance, only with n>=5 per group), `metric`, `unit` are optional.
4. `python3 scripts/report.py --agg agg.json --out report.html --audience 초등|학부모|선생님|전문가 [--xlsx r.xlsx] [--csv a.csv]`. Wording and numbers come from the aggregates; override only via plan `narrative` (numbers still checked).
5. `python3 scripts/check_report.py report.html --agg agg.json --source FILE` must print PASS. Fix the plan (not the HTML) and rebuild, max 2 times.
6. Show the page. Offer 2 tweaks (다른 눈높이로 / 엑셀로도). Mention correlation is not cause and small samples (the report already says so).

## Chart rules (built in)
Bar = compare, line = change over time, pie only <= 5 parts (else bar), stacked = shares per group. Rounded numbers with units, axis shows 「단위」, bars start at 0, colour never the only cue (values are printed), colour-blind-safe series colours, keep-all Korean, text >= 14 px, contrast >= 4.5:1.

## Checker (`scripts/check_report.py`)
Zero external requests (static + real browser), no storage/network APIs, no raw personal data (patterns + the real names/phones/e-mails of `--source`), chart numbers == aggregates, every number in sentences exists in aggregates, units on every chart, keep-all/size/contrast, conclusion at top, sentence length and hard-word ratio per audience, no overflow at 1280/390 px, all canvases drawn.

## Files
`scripts/`: `profile_data.py` · `analyze.py` · `report.py` (+`export.py` xlsx with formulas/csv) · `check_report.py` · `shots.py` · `make_samples.py` (synthetic practice files in `assets/sample-data/`) · `tdata.py` (shared helpers). `shared/` (design, fonts, vendor Chart.js, tools) is used from the skill folder when installed, else from the repo root.
Audience: 초등 = short friendly sentences, no stats words; 학부모 = polite plain; 선생님 = adds n and caveats; 전문가 = adds p-values, effect sizes.
