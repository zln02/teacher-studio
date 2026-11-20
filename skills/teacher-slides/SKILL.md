---
name: teacher-slides
description: Makes PPT / PowerPoint (.pptx) files and web slide decks - 파워포인트·피피티·발표자료·수업 PPT·홍보 PPT·보고 PPT - from a short spec, with a content recipe, a gate (blanks, overflow, empty-looking slides) and a preview picture. Use it first, before any generic pptx skill, when a teacher or anyone wants slides for lessons, training, parents, reports, company or club talks (회사·모임); the user's own template comes first.
license: Apache-2.0
---

# 교사 스튜디오 · 슬라이드

Teacher (no coding) asks in plain words for a PPT / talk / training / parent-meeting / club deck. You write a **short JSON spec**; tools design it, check it, and screenshot it.
Principle: tools guarantee the floor (type scale, contrast, safe margins, keep-all Korean, density), you add the message. Restraint beats decoration: one focal element per slide, one accent colour.

Respond in the user's language. Follow the ask-first rule: `../teacher-studio/references/ask-first.md`.
The user's own template or reference comes first. (The user-template weapon - building from a PPT/design the user supplies - is planned, not built yet. Colours are covered: `shared/design/color_from.py deck.pptx --out pal.json`, then `"design": {"palette_from": "pal.json"}` in the spec, see `../teacher-studio/references/user-colors.md`; the composition stays ours. For type and layout learn from the file via `../teacher-studio/references/learn-from-reference.md` and say honestly that it is an approximation, not a copy.)

## Words
- Never show code or file names to the teacher. 「PPT 만들어 줘」「칠판에 띄울 거」「글씨 더 크게」 -> `references/teacher-language.md`.
- **Editable PowerPoint** (「PPT」「파워포인트」「피피티」「.pptx」, or 「나중에 내가 고칠 거예요」) -> ALWAYS deliver an editable `.pptx` next to the web deck: add `--pptx` (same spec, same look; real text boxes, native charts and tables, speaker notes, QR as shapes). Say honestly what changes in PPT: 「단계별 나타나기·타이머·수식·아이콘 그림은 단순해져요」 and 「글꼴은 PC에 없으면 비슷한 글꼴로 바뀌어요」. python-pptx is installed on first need only after the teacher says yes (`shared/tools/ensure.py`, `--yes`). The teacher's own `.pptx/.potx` -> `--pptx --template mine.pptx` (their masters and layouts are used: template first). If the official `pptx` skill is listed by `doctor` (`official_doc_skills`) you may hand the file work to it for extras (animations, SmartArt, tracked edits); we still bring the structure, design and checks. PDF: 「Ctrl+P → PDF로 저장」.
- Intro video / countdown -> teacher-motion. Quiz game -> teacher-game.

## Pick the context from the request (one spec key)
`"context"`: **class** (수업·차시·학습 목표) · **promo** (홍보·모집·축제·알리기) · **public** (기관 보고·업무 보고·교육청·결과 보고) · **personal** (가족·자기소개·동호회·여행). It switches layouts, type scale, palette, numbering and slide defaults for the web deck and the .pptx; unsure -> ask once in the first question ("수업용 / 홍보용 / 기관 보고용 / 개인용"). Public = 표지(`org`,`date`,`dept`) + auto 목차 + `summary` + Ⅰ./1. + 개조식 + `table` + `source` on every data slide (required). Class = `objectives` + quiz/activity + `recap`. Promo = `hero` + CTA/QR. Personal = photo `hero`. Details, keys, sources: `references/context-recipes.md`; examples: `assets/spec-examples/context/`. A user template still wins (`--template`, `palette_from`).

## A PowerPoint file was asked for (「PPT」「파워포인트」「.pptx」): the short path
One command builds the .pptx, checks it and draws the preview: `python3 scripts/deck.py --spec deck.json --pptx 발표.pptx --pptx-only --review review/` (drop `--pptx-only` and add `--out deck.html` when the web deck is wanted too).
1. Write the spec with the **content recipe** below (context, real structure, figures, check questions with answers). 「알아서」 = no questions: fill unknowns with stated assumptions.
2. Run the command. Read every `FIX` / `FAIL` / `NOTE` line.
3. **Look once**: open `review/<name>-approx-sheet.png` (all slides, drawn from the pptx: shapes, lines, tables, charts, pictures). Thin or plain slide -> add a `diagram`, `table`, `chart`, `compare` or `activity`; never ship a text-only deck.
4. **Hard gate, last step, always:** rerun until the build prints `READY 발표.pptx`. `NOT DONE` / any `FAIL pptx:` line = not finished: fix the spec and run again (max 3 loops, then say plainly what still fails). Never write 「다 됐어요」 while it FAILs. A .pptx made or edited any other way (by hand, by another skill, after a fix request) goes through the same gate: `python3 scripts/pptx_check.py FILE.pptx --render review/` until `RESULT: PASS`.
5. Last message: the file in the folder the user named (current folder if they said so), what was assumed (one line), the 「바꿔 넣을 곳」 list only if the user wanted a template, and that the picture was an approximate preview.
Working alone or handing the job to a helper agent, the recipe and the gate travel with it: put this skill's name and step 4 in the hand-off.

## Content recipe (what makes the deck worth using)
- **수업 (class):** cover -> 학습 목표 -> 생각 열기 질문 -> for EACH concept: one idea slide (a `diagram` for anything that has a picture in the textbook: rays, cycles, structures, graphs; `compare` / `table` for two things side by side) + a 활동 (`activity`, minutes, materials in the note) or a 확인 문제 (`quiz` with `answer` and `explain`: the .pptx gets the answer slide automatically) -> 정리 (`recap`) -> closing with the next lesson. At least 2 check questions and 1 activity in a 10-slide lesson. Facts must be textbook-correct (angles from the normal, units, signs).
- **기관 보고 (public):** 표지(`org`, `date`, `dept`) -> 목차 -> 요약 -> Ⅰ 추진 배경·목적 -> Ⅱ 추진 체계·실적 (`table` + `chart` + `bignumbers`, every one with `source`) -> Ⅲ 성과·문제점 -> Ⅳ 향후 계획·일정 (`timeline`) -> 건의·협조 사항. Numbers must agree with each other across slides (20/24 = 83.3 %); invented numbers are labelled once per slide in `source` as 「예시 자료(가상 수치), 실제 집계로 교체」 and listed in the last message. 개조식 endings.
- **홍보 (promo):** `hero` -> 3 reasons -> programme `table` / `timeline` (date, time, place) -> CTA closing.
- **Unknown facts** (school name, presenter, phone): first choice = **leave them out** when the slide works without them (a lesson cover needs the grade, subject and unit, not a school or teacher name). Where the format needs one (기관 보고 표지의 기관·부서, 발신 명의) write the plausible value, never a slot: 「우리 학교」「교육연구부」, today's date `2026. 11. 20.`. Say the assumptions in one line at the end. Slots like `(학교명 입력)`, `○○학교`, `OOO`, `[...]`, `(예시)` FAIL the gate. Only when the user asks for blanks to fill in by hand: a labelled underline (`학교: ________`, `교사: ________`), never `○○` / `OO`, plus `"template_blanks": true` and the 「바꿔 넣을 곳」 list.

## Flow
1. **Ask only what is missing, once** (numbered, with defaults): ① who watches (grade / teachers / parents / club) ② topic or source file ③ length (default 10 slides) ④ mood in the teacher's words (따뜻하게, 깔끔하게, 신나게, 힙하게 ...) ⑤ date/presenter line.
2. **Outline table** (번호 | 종류 | 화면 글 | 메모) -> teacher says OK. Skip if they said 「바로 만들어」 (show the table with the result).
3. **Write the spec** (`deck.json`, below) and build:
```
python3 scripts/deck.py --spec deck.json --out deck.html --review review/ [--pptx]      # or: studio.py build slides --spec deck.json
```
   The seed is printed and stored in the file; `--seed N` rebuilds the same look, no seed = a fresh look every time (say so: 「마음에 안 들면 다시 뽑아 드려요」).
4. **Look.** Open `review/<name>-sheet.png` and judge every slide: *would a professional designer ship this?* Fix the spec (shorter text, other type, `--style`), rebuild, max 2 loops. `check_page.py` + `slides_review.py` must PASS (the build prints both).
5. Show the deck (artifact). Give three fixes in teacher words. Share / PDF / keep-offline lines: 「오른쪽 위 '게시' → 링크」「Ctrl+P → PDF로 저장(배경 그래픽 켜기)」「'다운로드'로 파일 보관, 인터넷 없이도 열려요」. Keys: → / click = next build, ← back, N notes, B black, F full screen, digits+Enter jump.

## Spec
```json
{"purpose":"수업|연수|학부모 설명회|발표|동아리|개인", "audience":"...", "mood":"따뜻하게", "subject":"과학",
 "title":"...", "seed": 7,                       // seed optional
 "design": {"style":"minimal-premium", "builds":true},   // optional overrides
 "slides":[ {"type":"title","title":"..","subtitle":"..","meta":"..","kicker":".."}, ... ]}
```
Words in `**stars**` are emphasised; `\n` breaks a line. Every slide may have `note` (presenter notes), `kicker`, `build:false`, `layout:"bullets.cards"` (force a variant).

| type | keys (limits) |
|---|---|
| title | title, subtitle, meta |
| section | title, sub |
| statement | text (one big sentence <= 70), sub |
| bullets | title, items 2-6 (<= 60 chars each) |
| compare | title, a:{label,items}, b:{label,items} or rows:[{k,a,b}] (<= 5) |
| steps | title, steps 3-6 [{title<=18,text<=44}] |
| bignumber | value, unit, caption |
| bignumbers | title, items 2-3 [{value,unit,caption}] (two big numbers side by side = compare) |
| quote | text, source |
| illustration | title, text, motif (Korean/Lucide word), art rings/blocks/arc — geometric, image-free |
| quiz | q, choices 2-5, answer (0-based), explain — next click reveals the answer |
| timeline | title, events 3-6 [{when,title,text}] |
| chart | title, kind bar/line/pie/doughnut, labels, series:[{name,data}], unit, takeaway (Chart.js, inlined) |
| math | tex (KaTeX), text |
| timer | minutes, title — start/pause/reset/±1 min, Space = start/pause |
| qr | url, title, caption — drawn at build time, offline |
| image | file (local path -> inlined, resized to <= 1920px / 3MB), title, caption |
| video | file (<= 8MB embedded, bigger -> 「영상 열기」 button), title |
| closing | title, sub, next[<=4], url (adds a QR) |
| table | title, columns 2-6, rows 1-8 (cells <= 40), unit, highlight, source, footnote |
| summary | title, text, label (핵심), points 2-5 |
| toc | title, items 2-8 (public: filled from sections) |
| hero | headline <= 34, sub, kicker, cta, url (QR), file (photo) |
| diagram | title, shapes 2-40 on a 100 x 60 canvas: `line` `dash` `arrow` `dasharrow` {x1,y1,x2,y2,color,w} · `rect` {x,y,w,h,fill,text} · `circle` {cx,cy,r,fill,text} · `arc` {cx,cy,r,from,to: degrees, 0 = right, 90 = up} · `label` {x,y,text,color,size s/m/l,align}; colours pr ac tx mu good bad water sky sun or #hex; points 0-4 (notes beside it), caption. Real lines and arrows in the .pptx. Example: `assets/spec-examples/context/class-light-reflection.json` |

**No blanks, ever.** Never write `[학교명]`, `(학교명 입력)`, `(…을 입력하세요)`, `[날짜]`, `20XX`, `OO초`, `OOO`, `○○학교`, `(예시)`, `(미정)`, `000-0000` in a spec. Fill with a plausible stated assumption (today's date, 2026학년도 / the current school year, generic 「우리 학교」·「3학년」) and say it in one line. Facts only the teacher knows (the real school name, phone, meeting date) go in `"fillins": ["학교 전화번호", ...]` (top-level list, words as they appear): the deck may then still contain them, and you show a short 「바꿔 넣을 곳」 list in the last message. Any other leftover is a FAIL (HTML review and `pptx_check.py`). **The user wins:** 「양식으로 해 줘」「빈칸 있는 틀로」「서식만」 -> spec `"template_blanks": true` (top level): all blanks stay, are reported as 「바꿔 넣을 곳」, and the build prints one caution line (`pptx_check.py --allow-blanks` for a lone file).
Rules: one message per slide, <= 330 characters of text on a slide, no emoji (stripped). Text is projection-sized (>= 28px) — never ask for smaller. Do not invent statistics; unsure facts -> note 「확인 필요」. No student names/photos.
Build errors are lists of 「고칠 곳」: fix exactly those and rerun.
Old `fire slides/lesson-deck/<skin>` (3 skins) still works but is the **lowest priority**: use it only if the teacher names a legacy look.

## Design language (automatic)
`scripts/deck_style.py` maps purpose + mood + subject to one of the 12 shared styles (`shared/design/styles.py`) and a palette; each style has its own composition (title treatment, card, emphasis, background motif, transition, preferred layout families). Every slide type has 2-4 layout variants (asymmetric splits, full-bleed type, bento cards, editorial rows, numbered steps, comparison panels); the picker never repeats a layout twice in a row. Use the user's logo/template colours first (`design.palette_from`; means, not our design). `slides_review.py` and `check` WARN when correct/wrong or chart colours look alike to colour-blind eyes (add shapes or text). Custom flair is allowed per slide and sandboxed: `"flair":{"css":"...","svg":"<svg>..</svg>"}` (no external urls, scripts, fixed positioning; css is scoped to that slide). Keep it rare.

## Review gate (`scripts/slides_review.py`)
**no placeholders left** (`placeholders.py`: `[대괄호]`, `20XX`, `OO`, `○○`, `000`, 학교명 ... FAIL unless listed in `fillins`) · External requests 0 · contrast >= 4.5 on real pixels · text >= 28px · overflow / safe margin / keep-all · not empty · **clutter caps** (elements <= 36, icons <= 3, big colours <= 5) · no 3 identical layouts in a row. Compare decks: `slides_review.py --compare a.html b.html` (distance >= 0.35).

## PowerPoint (.pptx) review - `scripts/pptx_check.py deck.pptx --spec deck.json --render review/`
`deck.py --pptx` builds the file, **shrinks text that would overflow its box** (never below 60% / 12pt; same metrics as the check, `pptx_fit.py`), then runs `pptx_check`: placeholders FAIL · text fit (estimate) FAIL · shapes inside the slide · no empty placeholder · **no empty-looking slide** (`pptx_fill.py`: a body slide whose content covers < 6 % of the slide or stops above 60 % of its height FAILs: add content or merge it). A FAIL on text fit means: shorten or split that slide in the spec and rebuild. The build ends with `READY file` only when every check passes, otherwise `NOT DONE`.
**Look at it.** `--review DIR` also draws PNGs: with **LibreOffice** installed it is a real rendering; otherwise it is an **approximate** preview drawn from the pptx itself (`pptx_draw.py`: shapes, lines and arrows, pictures, tables, native charts, groups, master art; red outline = estimated overflow). It works on any .pptx, so two decks can be compared with the same eyes. Always tell the teacher which one it was. LibreOffice is large (about 350MB download, 5-10 minutes): offer it once with the size (`py shared/tools/ensure.py libreoffice`, install only after a yes, `--yes-libreoffice`); declining is fine.
**Last message** (pipeline.md, Final checkpoint): file path, how to open it, check result, the 「바꿔 넣을 곳」 list.

## Absolute rules
1. **No student info** on slides. Example names are fictional.
2. **Facts**: unsure -> 「확인 필요」; sources of numbers go to the note.
3. **Copyright is advisory, not blocking** (`references/legal-advisory.md`): teacher's own images/quotes go in with one line of advice.
4. **Offline**: no external requests; fonts are embedded Noto Sans/Serif KR; old Chrome safe (no `?.` `??` `replaceAll` `:has` `aspect-ratio`).
5. Full-screen button and notes (N) stay; notes hidden by default.

## Files
| file | when |
|---|---|
| `scripts/deck.py` | build a deck (spec -> html, runs the checker) |
| `scripts/slides_review.py` | screenshots, contact sheet, metrics, `--compare` |
| `scripts/pptx_check.py`, `pptx_fill.py`, `pptx_render.py`, `pptx_draw.py`, `pptx_chart.py`, `pptx_fit.py`, `placeholders.py` | .pptx gate (blanks, text fit, empty-looking slides), PNG drawing (shapes, tables, charts, pictures), placeholder detector |
| `scripts/deck_diagram.py` | the `diagram` slide (web SVG + PowerPoint lines / arrows / shapes) |
| `scripts/deck_layouts.py` | layout variants (read only to add one) |
| `assets/spec-examples/*.json` | four finished specs (parents / training / photosynthesis / club) |
| `references/teacher-language.md`, `legal-advisory.md` | wording, advice lines |
| `assets/missiles/lesson-deck/` + `scripts/build_stage.py` | legacy skins, hand-made stage pages (`--data/--show`), MP4 (`render_mp4.py`) |

## Pipeline (`../teacher-studio/references/pipeline.md`)
대본 = per-slide message + `note`; 콘티 = the Outline table in Flow step 2, or the thumbnail sheet: `py ../teacher-studio/scripts/storyboard.py deck.json --html sheet.html --open` (reads deck.json as is). Checkpoint: outline/콘티 before building, then the first deck; deliver with `deliver.py deck.html` (PDF, QR, privacy check for parent decks). Skip for 「바로/알아서」.
