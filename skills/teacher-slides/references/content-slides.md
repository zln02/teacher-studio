# Slide content — what goes on each slide, by context

`context-recipes.md` sets layout, type and lints. This file decides the **content**. Read the matching cross-skill recipe first, then apply the slide rules here:
- `class` → `../teacher-studio/references/content-lesson.md`
- `public` → `../teacher-docs/references/content-docs.md`
- `promo` → `../teacher-studio/references/content-promo.md`
- every sentence → `../teacher-studio/references/content-writing.md`

The slide lists in `context-recipes.md` and the files in `spec-examples/` show what the builder accepts. They are not the outline. Derive the outline from this deck's purpose; two decks on different topics must not share a slide-by-slide skeleton.

## Steps (all contexts)
1. **Write the deck's one sentence**: 「이 발표가 끝나면 〈청중〉은 〈무엇을 안다/한다/결정한다〉.」
2. **Write the storyline as full-sentence claims**, one per slide, before choosing any slide type. Read only those sentences in order: they must make the argument or the lesson by themselves. A slide whose sentence is a topic word (「현황」「특징」) has no claim yet.
3. **Give each claim its evidence**: a figure, a number with source, a worked example, a question. No evidence and not a transition → merge or cut.
4. **Then choose the slide type from the shape of the evidence**: sequence → `steps`/`timeline`; two things on the same criteria → `compare`/`table`; one number that matters → `bignumber`; parts and relations → `diagram`; a check → `quiz`. `bullets` only when the items are truly parallel and unordered.
5. **Title = the claim** (class: may be the question being answered), short enough to read at a glance from the back; about 20자 is where to start checking, and a precise longer title beats a vague short one. Not a category label. Varied forms across the deck; not 「〈주제〉: 〈부제〉」 every time.
6. **Body carries what the speaker cannot say fast**: the figure, the term, the number. Explanation and transitions go to `note`; a slide that only repeats the talk is trimmed.
   - Keep on the slide, even though the teacher also says it: task instructions and their conditions, safety steps, formulas and definitions, the key sentence students must copy or use, and what a figure shows (caption). Students who hear poorly, arrive late or read the handout later depend on these.
   - If the deck is also a 배포본 (printed, sent home, uploaded), check it as a handout too: does it make sense without the speaker? Add the missing sentence to the slide or to visible notes.
7. **Budget**: slide count follows the story and the activities, not a quota. A rough check is one slide per 1.5-3 minutes of talking; activity, discussion and check slides stay up much longer. Cut slides to fit the time; do not shrink text to fit.
8. **Check the build output against the claims list**, not only the gate: is each claim still the first thing seen on its slide?

## By context
**class**
- Outline comes from `content-lesson.md` steps 3-9: objectives → evidence → 오개념 → rhythm. Every 5-7 minutes of input is followed by a `quiz` or `activity` slide.
- The 도입 slide poses something students cannot yet answer; the same thing is answered on a 정리 slide.
- One new idea per slide. A `diagram` needs labels that name parts in textbook terms, and a caption that says what to notice.
- `quiz`: `answer` + `explain` (「왜」) always; options follow `../teacher-game/references/content-items.md`.
- `activity`: product, minutes, materials, what early finishers do. 수준별 tasks sit side by side on one slide with neutral labels.
- `objectives`: 1-3, student words, checkable verbs. 「~할 수 있다」 is correct here.

**public** (기관 보고 · 업무 보고)
- 요약 slide = the conclusion and the request (승인 · 예산 · 협조), with the 2-4 numbers that support it. A reader who sees only this slide can decide. For a decision deck it also carries the basis, the conditions attached, and the main remaining risk.
- Every number: 단위 · 기준일 · 출처, and the same value everywhere it appears. Comparisons name the base (전년 대비, 계획 대비).
- 실적 is stated against the plan or target, not alone. 문제점 comes with 원인 and 개선 과제 (who · by when).
- 개조식 endings, one line per item, no 「~습니다」. Section order follows what the reviewer asks: 왜 → 무엇을 했나 → 결과 → 남은 문제 → 다음 일정 · 건의.
- Invented figures are never presented as real: 「예시 자료(가상 수치), 실제 집계로 교체」.

**promo**
- One message; headline says the benefit to the audience, not the organiser's title. ≤ 3 levels of emphasis on a slide (headline → key facts → details).
- The facts a person needs to act (누가 · 언제 · 어디서 · 어떻게 신청 · 마감 · 문의) are all present and identical on every slide where they appear.
- One CTA, repeated at the end with the QR/link.

**personal**
- A story with a turn (before → event → after), not an album. One photo or moment per slide with one line that adds what the picture does not show.

## 전문가 점검표
- [ ] The slide claims, read alone in order, make the whole argument or lesson.
- [ ] Every slide has one claim and its evidence; no slide exists to fill a layout.
- [ ] Titles are claims or questions, readable at a glance, in varied forms.
- [ ] Slide type matches the shape of the content; `bullets` is not the default.
- [ ] Body is not the script, but instructions, safety steps, formulas, key sentences and figure captions are on the slide.
- [ ] Checked on the final output: from the back of the room, and as the handout if it will be distributed.
- [ ] No answer, date, number or safety condition on a slide is still 「확인 필요」; otherwise the deck is a 「교사 초안」.
- [ ] class: objectives ↔ check questions match one to one; hook answered at the end; answers and 「왜」 present.
- [ ] public: conclusion and request on the 요약 slide; every number has 단위 · 기준일 · 출처 and agrees across slides; totals recomputed.
- [ ] promo: one message, one CTA, action facts complete and consistent.
- [ ] Slide count fits the time; nothing was shrunk to fit.
- [ ] The outline is not a copy of a `spec-examples/` file or of `context-recipes.md`'s list.
- [ ] `content-writing.md` tell check passed; `../../shared/content/CONTENT-RULES.md` gate G1-G10 passed (repo checkout; when the folder is absent, the checklist above stands in).
