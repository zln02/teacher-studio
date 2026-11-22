# Slide content — what goes on each slide, by context

Run the scripts as written with `python3`; on Windows type `py` instead (no `py`: `python`). Always the short command name, never an interpreter's full path (`C:\...\python.exe`).

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
4. **Then choose the slide type from the shape of the evidence**: sequence → `steps`/`timeline`; two things on the same criteria → `compare`/`table`; one number that matters → `bignumber`; parts and relations → `diagram`; a check → `quiz`. `bullets` only when the items are truly parallel and unordered. A claim that needs two kinds of evidence at once (the headline figures and the trend behind them; a drawing and the rule it shows; a table and what follows from it) keeps them on one slide: `panel`. Splitting them over two thin slides makes the audience hold the first in their head; packing two claims into one panel hides both.
5. **Title = the claim** (class: may be the question being answered), short enough to read at a glance from the back; about 20자 is where to start checking, and a precise longer title beats a vague short one. Not a category label. Varied forms across the deck; not 「〈주제〉: 〈부제〉」 every time.
6. **Body carries what the speaker cannot say fast**: the figure, the term, the number. Explanation and transitions go to `note`; a slide that only repeats the talk is trimmed. Where the evidence does not speak for itself (a table, a chart, a comparison), the slide ends with what it means in one line (`takeaway`): the meaning, not a repeat of the title.
   - Fill with substance, not with size: a slide whose body is two short lines is either missing its evidence (add the example, the figure, the case) or belongs on its neighbour.
   - Each slide names particulars: the real example, the figure with its unit and base, the place and date, the term as the field writes it. Text has two levels (a short heading and its detail), not one long sentence per bullet.
   - Keep on the slide, even though the teacher also says it: task instructions and their conditions, safety steps, formulas and definitions, the key sentence students must copy or use, and what a figure shows (caption). Students who hear poorly, arrive late or read the handout later depend on these.
   - If the deck is also a 배포본 (printed, sent home, uploaded), check it as a handout too: does it make sense without the speaker? Add the missing sentence to the slide or to visible notes.
7. **Budget**: slide count follows the story and the activities, not a quota. A rough check is one slide per 1.5-3 minutes of talking; activity, discussion and check slides stay up much longer. Cut slides to fit the time; do not shrink text to fit.
8. **Check the build output against the claims list**, not only the gate: is each claim still the first thing seen on its slide?

## Scene rules (learned from the 2026-11-23 training deck; every context, any style, strongest with preset E)
- **Big-type opening only on key-message slides.** The syllable drop (`statement`, `title`, `hero`, `section` in preset E) is for the two or three sentences the room must leave with. A list, a table or a chart never opens with big type; if every slide shouts, none does.
- **One idea per scene.** One claim, one picture or figure, one takeaway. A second idea gets its own slide (or a `panel` when it is evidence for the same claim).
- **Picture-led over text-only small cards.** Prefer one drawing, diagram, real screen or backdrop with 2-3 large labels to six small text cards. A row of tiny cards that each hold one line is a list pretending to be a design: make it `steps`, a `diagram`, or fewer, larger cards.
- **Analogy for AI beginners: the real thing first, then the analogy.** Show the actual screen or object (the app window, the real form, the real tool) and point at its parts; only then the picture that explains it (「식당으로 치면 …」). An analogy shown alone leaves the audience unable to find the thing on their own screen.
- **Do not show N identical boards when one scene with changing labels says it.** Three copies of the same layout with different words = one scene whose label changes on each click (`pills`, the build steps, `pen` notes).
- **Evidence lines keep exact numbers and their source; no invented claims.** 「92 % → 71 %」 stays 「92 % → 71 %」 with 「자료: …」; never round into a slogan, never add a figure nobody measured. A world fact you cannot check is left out (and named in the last message).
- **Cursor / 「making-of」 scenes end on a real output and carry no speed claim.** A demo cursor or a drag scene must finish on the actual result (the real screenshot, the real file), never on a mock; and no 「3초 만에」「1분이면」 unless it was timed and the timing is shown as measured.
- **Pen notes point, they do not explain.** One or two marks per slide (`"pen": [{"mark": "circle", "text": "83%", "note": "목표 초과"}]`), a note of a few words; the explanation stays in the talk or the `takeaway`.
- **Garnish (고명) last, and only where it helps.** A backdrop or illustration is added after the content passes; dense slides (table, chart, long text) get none (the build skips them and says so); pictures carry no text, logos or real faces, and keep one look across the deck (`shared/design/garnish.py`). A picture must not teach a wrong fact (a light ray drawn against the law it illustrates is cut, not dimmed).

## By context
**class**
- Outline comes from `content-lesson.md` steps 3-9: objectives → evidence → 오개념 → rhythm. Every 5-7 minutes of input is followed by a `quiz` or `activity` slide.
- The 도입 slide poses something students cannot yet answer; the same thing is answered on a 정리 slide.
- One new idea per slide. A `diagram` needs labels that name parts in textbook terms, and a caption that says what to notice.
- A drawing of a real thing (표지, 실험 기구, 동식물, 지도 기호) must be recognisable as that thing: its real outline, colours, border and the mark inside it. A bare shape with a word in it teaches the shape, not the thing; draw fewer, fully. Boxes beside a drawing add what it cannot show (까닭, 예외, 헷갈리는 짝), not its labels again.
- Short is the sentence, not the lesson: for young children every line is short, and the distinctions the unit teaches (두 가지가 비슷해 보이지만 뜻이 다른 것, 누구를 위한 규칙인지, 예외) still each get their place. In a short deck the frame shrinks first (목표는 표지 한 줄, 정리는 마무리, 확인 문제 여러 개는 한 장).
- `quiz`: `answer` + `explain` (「왜」) always; options follow `../teacher-game/references/content-items.md`.
- `activity`: product, minutes, materials, what early finishers do. 수준별 tasks sit side by side on one slide with neutral labels.
- `objectives`: 1-3, student words, checkable verbs. 「~할 수 있다」 is correct here.

**public** (기관 보고 · 업무 보고)
- 요약 slide = the conclusion and the request (승인 · 예산 · 협조), with the 2-4 numbers that support it. A reader who sees only this slide can decide. For a decision deck it also carries the basis, the conditions attached, and the main remaining risk.
- Every number: 단위 · 기준일 · 출처, and the same value everywhere it appears. Comparisons name the base (전년 대비, 계획 대비).
- 실적 is stated against the plan or target, not alone. 문제점 comes with 원인 and 개선 과제 (who · by when).
- 개조식 endings, one line per item, no 「~습니다」. Section order follows what the reviewer asks: 왜 → 무엇을 했나 → 결과 → 남은 문제 → 다음 일정 · 건의.
- Figures the user gave are used as given. Their own counts and amounts they did not give are plausible example values that agree with each other, listed in `"fillins"`, with a believable `source` (「우리 학교 자체 집계(2026. 11.)」) and noted ONCE for the deck: the first slide's speaker notes (the build adds it), or one small `footnote` under the first data table (「※ 수치는 예시입니다. 실제 집계로 바꿔 주세요.」). Not on every slide: a `source` or `footnote` line never says 「가상」「예시」 (it names the record only; the build stops when two slides repeat it). Never a 「확인 필요」「집계 필요」 cell. Statistics about the world (전국 평균, 연구 결과) are never invented (CONTENT-RULES, Unknowns).

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
- [ ] Slide type matches the shape of the content; `bullets` is not the default; no slide type fills more than a third of the body and neighbours do not repeat one shape.
- [ ] No body slide is half empty and none is a wall of text; a claim with two kinds of evidence shows both on one slide (`panel`); data slides say what the data means (`takeaway`).
- [ ] Body is not the script, but instructions, safety steps, formulas, key sentences and figure captions are on the slide.
- [ ] Checked on the final output: from the back of the room, and as the handout if it will be distributed.
- [ ] No 「확인 필요」 text, slot or draft stamp on any slide. An answer or safety condition you could not verify is left out and named in the final message; the user's unknowns are example values listed in `"fillins"`, noted once (not in a lesson deck).
- [ ] class: objectives ↔ check questions match one to one; hook answered at the end; answers and 「왜」 present.
- [ ] public: conclusion and request on the 요약 slide; every number has 단위 · 기준일 · 출처 and agrees across slides; totals recomputed.
- [ ] promo: one message, one CTA, action facts complete and consistent.
- [ ] Slide count fits the time; nothing was shrunk to fit.
- [ ] The outline is not a copy of a `spec-examples/` file or of `context-recipes.md`'s list.
- [ ] `content-writing.md` tell check passed; `../../shared/content/CONTENT-RULES.md` gate G1-G10 passed (repo checkout; when the folder is absent, the checklist above stands in).
