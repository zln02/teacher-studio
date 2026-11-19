---
name: teacher-slides
description: Makes designer-grade web slide decks from a short JSON spec for lessons, training, parents, company or club talks (회사·모임). For teachers and anyone; the user's own template comes first.
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

Rules: one message per slide, <= 330 characters of text on a slide, no emoji (stripped). Text is projection-sized (>= 28px) — never ask for smaller. Do not invent statistics; unsure facts -> note 「확인 필요」. No student names/photos.
Build errors are lists of 「고칠 곳」: fix exactly those and rerun.
Old `fire slides/lesson-deck/<skin>` (3 skins) still works but is the **lowest priority**: use it only if the teacher names a legacy look.

## Design language (automatic)
`scripts/deck_style.py` maps purpose + mood + subject to one of the 12 shared styles (`shared/design/styles.py`) and a palette; each style has its own composition (title treatment, card, emphasis, background motif, transition, preferred layout families). Every slide type has 2-4 layout variants (asymmetric splits, full-bleed type, bento cards, editorial rows, numbered steps, comparison panels); the picker never repeats a layout twice in a row. Use the user's logo/template colours first (`design.palette_from`; means, not our design). `slides_review.py` and `check` WARN when correct/wrong or chart colours look alike to colour-blind eyes (add shapes or text). Custom flair is allowed per slide and sandboxed: `"flair":{"css":"...","svg":"<svg>..</svg>"}` (no external urls, scripts, fixed positioning; css is scoped to that slide). Keep it rare.

## Review gate (`scripts/slides_review.py`)
External requests 0 · contrast >= 4.5 on real pixels · text >= 28px · overflow / safe margin / keep-all · not empty · **clutter caps** (elements <= 36, icons <= 3, big colours <= 5) · no 3 identical layouts in a row. Compare decks: `slides_review.py --compare a.html b.html` (distance >= 0.35).

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
| `scripts/deck_layouts.py` | layout variants (read only to add one) |
| `assets/spec-examples/*.json` | four finished specs (parents / training / photosynthesis / club) |
| `references/teacher-language.md`, `legal-advisory.md` | wording, advice lines |
| `assets/missiles/lesson-deck/` + `scripts/build_stage.py` | legacy skins, hand-made stage pages (`--data/--show`), MP4 (`render_mp4.py`) |

## Pipeline (`../teacher-studio/references/pipeline.md`)
대본 = per-slide message + `note`; 콘티 = the Outline table in Flow step 2, or the thumbnail sheet: `py ../teacher-studio/scripts/storyboard.py deck.json --html sheet.html --open` (reads deck.json as is). Checkpoint: outline/콘티 before building, then the first deck; deliver with `deliver.py deck.html` (PDF, QR, privacy check for parent decks). Skip for 「바로/알아서」.
