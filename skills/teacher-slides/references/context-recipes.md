# PPT context recipes (`"context"` in the spec)

Pick ONE context from the request and put it in the spec. It changes layouts, type scale, palette and slide defaults for both the web deck and the `.pptx`. No context = the old behaviour.

| request words | context | what changes |
|---|---|---|
| 수업, 차시, 학습 목표, 아이들 앞에서 | `class` | bigger type (floor 32px, body ×1.12), one idea per slide, `objectives` slide after the cover, `quiz` / `activity` (+ `timer`), `recap` before the closing; bright style family |
| 홍보, 모집, 축제, 알리기, 포스터 같은 | `promo` | `hero` cover (image + headline + CTA + QR), poster/big-type layouts, headline ×1.18, copy ≤ 24 chars, ≤ 3 points, CTA closing with QR; bold style family |
| 기관 보고, 업무 보고, 교육청, 결과 보고, 공공 | `public` | 표지(기관·날짜·부서), auto 목차, 요약(핵심 box), Ⅰ./1. numbered headings, 개조식 lists (□ ○ -, or `"marks":"num"` 가./1)/가)), real tables, 자료/주 line, header with section + 기관, navy/slate/teal palette, no build animation, type floor 24px |
| 가족, 자기소개, 동호회, 돌잔치, 여행 | `personal` | `hero` photo cover, image-led story layouts, warm style family (pastel / nature / gold) |

Template-first still wins: `--template mine.pptx` uses the user's masters; `design.palette_from` keeps their colours. The recipe then only adds structure (numbering, 목차, 자료 line).

## Spec keys added by the recipes
- top level: `"context"`, `"objectives": [..]`, `"recap": [..]` (class), `"summary": [..]`, `"org"`, `"date"` (any format -> `2026. 11. 19.`), `"dept"`, `"toc": false`, `"numbering": false` (public).
- slide types: `panel` {title, blocks 2-4 (kpis / cards / list / chart / table / note / flow / tree / diagram), takeaway, layout} · `diagram` {title, shapes (line / dash / arrow / dasharrow / rect / circle / poly / arc / label on a 100 x 60 canvas), points 0-4, caption} · `table` {title, columns 2-6, rows 1-8, unit, highlight (column index), source, footnote} · `summary` {title, text, label, points 2-5} · `toc` {title, items (auto from sections in public)} · `hero` {headline ≤ 34, sub, kicker, cta ≤ 20, url (QR), file (photo)} · aliases `objectives`, `recap`, `activity` {steps or items, minutes}.
- any data slide: `source` ("기관, 자료명(연도)") and `footnote` -> 「자료: … 주: …」 line. **public: `source` is required on chart / table / bignumber(s) / compare-with-rows** (build stops with a fix line).

## Type scale (1920×1080 stage px)
| context | cover | heading | body | caption / source | floor |
|---|---|---|---|---|---|
| class | 120 | 72 | 44 | 32 | 32 |
| promo | 160 | 88 | 40 | 28 | 28 |
| public | 80 | 52 | 32 | 24 | 24 |
| personal | 112 | 64 | 38 | 28 | 28 |

## What a good deck holds (jobs, not a slide order; the outline comes from the content)
A context names the jobs a deck must do. Which slides do them, how many and in what order is decided from THIS content (`content-slides.md`). Do not reuse a list of slide types from an earlier deck or from `assets/spec-examples/`.
- **class**: says what will be learned · opens with a question or a case · carries each sub-topic of the unit on a slide whose type fits its shape · checks understanding more than once, with answers and reasons · gives the class something to do · closes with what was learned and what comes next. The .pptx collects the answers on one 「확인 문제 정답」 slide before the closing.
- **public**: 표지 · 목차 (auto) · 요약 with the key numbers come first by convention. After that, one section per real part of the work; each data slide has `source` ("우리 학교 자체 집계(2026. 11.)") and numbers that agree across slides. Figures the user did not give are example values: listed in `"fillins"` and noted once for the deck (first slide's speaker notes, or one `footnote` under the first data table), not on every slide.
- **promo**: one promise · the reasons that are real · the facts needed to act · one call to action.
- **personal**: the pictures lead; words only where a picture cannot say it.
- Shape -> slide type (any context; `"type": "auto"` lets the build choose, `scripts/deck_shape.py` prints the choice):

| the content is | type |
|---|---|
| something that is drawn in the textbook (paths, cycles, parts) | `diagram` |
| two things side by side | `compare`, or `table` when there are 3+ attributes |
| an order of actions | `steps` · dated or timed -> `timeline` |
| one figure / two or three figures / a series | `bignumber` / `bignumbers` / `chart` |
| counts per group | `table` |
| one sentence to remember | `statement` |
| one claim that needs two or three kinds of evidence together (figures + their chart, a drawing + its rule, a table + what follows) | `panel` |
| who does what / what belongs under what | `panel` with a `tree` block |
| several points of equal weight with no other shape | `bullets` (the last choice, not the first) |
- Any body slide may end with `takeaway` (the conclusion in a band). Use it where the audience could miss what the evidence means; not on every slide.
- Body slides carry weight: 3-4 items or a figure. A slide with two short lines is merged into its neighbour (the .pptx gate FAILs empty-looking slides).

## Lints (printed as NOTE, public `source` is a FIX)
- every context: three plain list slides in a row · lists are more than a third of the body · one slide type is more than half of the body · a lone `bignumber(s)` slide next to the chart or table it summarises (-> one `panel`)
- public: missing `source` (FIX) · polite endings 「~습니다/~해요」 in body text (개조식: ~함, ~임, ~추진) · no 요약 slide · no 기관 · date not `YYYY. M. D.`
- class: no objectives / quiz-or-activity / recap · more than 4 bullets on one slide · fewer than 2 check questions or no activity in a deck of 8+ slides · a quiz without `explain` · no figure slide (diagram / image / compare / table / chart / steps)
- public (also): no table or chart · no 일정 (timeline / steps) · no 기관 -> write 「우리 학교」, never a slot
- promo: no CTA (hero `cta` or closing `url`) · headline > 24 chars · more than 3 bullets
- personal: no photo slide

## Fixtures (`assets/spec-examples/`): test files, not patterns
The JSON files there carry `"_fixture"`. They exist so tests can build every slide type in every context. Do not open them to plan a deck and never copy an outline, a heading or `design` words from one: the build WARNs 「예시를 그대로 따라간 것 같아요」 when a deck repeats a fixture's sentences, its slide sequence with its headings, or its skeleton part for part. The pictures in `context/photos/` are abstract images generated by this project (no third-party content). Numbers in the public fixtures are labelled 「예시 자료(가상 수치)」 — never present invented numbers as facts.

## Sources for the public conventions (checked 2026-11-19)
What is **official** (공문서 rules that public decks borrow) and what is only **common practice** are kept apart.
- Item hierarchy 1. 가. 1) 가) (1) (가) ① ㉮, optional □ ○ - ㆍ; date `2026. 11. 19.`; time `15:20`: 「행정업무의 운영 및 혁신에 관한 규정」 및 시행규칙 (행정안전부령 제408호, 시행 2023. 6. 28.) — https://www.law.go.kr/법령/행정업무의운영및혁신에관한규정시행규칙 ; quoted in 경기도교육청 「한 곳에 정리한 공문서 작성법」(2023. 12. 1.) https://www.goe.go.kr/resource/old/BBSMSTR_000000000028/BBS_202410150153084250.pdf
- 「문장은 짧게 끊어서 개조식으로」: same 경기도교육청 2023 guide (p.13).
- The □ → ○ → - order, 1-page 요약 box, 「자료:/주:」 line under tables and charts, restrained colours and a 목차 are **common practice in Korean public reports, not a rule in law** (no official manual text was found; 서울시 distributes its own report templates internally: https://opengov.seoul.go.kr/sanction/view/?nid=11678326). Say 「관행」 if a user asks whether it is mandatory.
- 행정안전부 「행정업무운영 편람」 (2011, 5th ed.; latest edition not found online) and the 2017 change that body text starts at the left margin: https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId=60226
