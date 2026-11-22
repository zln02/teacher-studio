# DESIGN-RULES: the studio look, as rules a checker can read

One design system for every weapon (game, slides, 콘티, direction cards, web app, class tools, data report, documents).
Numbers live in [`system.py`](system.py), the 12 styles in [`styles.py`](styles.py), palettes in [`palettes.json`](palettes.json),
the check in [`ai_look.py`](ai_look.py) (「밤티 검사」). Benchmark: the owner-approved deck look 「먹과 놋쇠」 (matte, restrained, editorial).

**Rule 0. The user's design wins.** Their template, logo colours, font or picture is used as given. Nothing below is applied over it,
and the checks stay silent (`palette_from`, `--template`, `data-user-design`).

## 1. Type
1. One family: **TS Sans** (Pretendard subset, embedded). Stack: `system.STACK_SANS`. Noto Serif KR only in a style that is editorial by design, never on cream paper.
2. Sizes come from the scale, not from taste. Stage 1920x1080: display 132 · h1 96 · h2 72 · h3 56 · lead 44 · body 36 · label 28 · caption 24. **Nothing below 22px** on the stage (web 0.75rem, print 9pt).
3. Tracking by size (`system.tracking`): 96px+ → −0.045em · 60px+ → −0.035em · 36px+ → −0.022em · 24px+ → −0.012em. Small labels / kickers: +0.06em.
4. Line-height by size (`system.leading`): 96px+ → 1.1 · 56px+ → 1.18 · 40px+ → 1.28 · text → 1.5.
5. **Weight ≤ 800.** The bigger the type, the lighter: 96px+ → 700, 56px+ → 760, below → 800. Body 500 on a stage, 400 on paper.
6. Numbers that change or line up (scores, timers, tables, page numbers) use tabular figures: `font-variant-numeric:tabular-nums`.
7. Korean: `word-break:keep-all`, `line-break:strict`, headings `text-wrap:balance`, body `text-wrap:pretty`. Quotes are 「」, the list dot is `·`, an ellipsis is `…` (one character). Brackets and dots lose their dead half space: `text-spacing-trim:space-first`.
8. No faux bold or italic: `font-synthesis:none`. Korean is never slanted; emphasis is weight or ONE colour.

## 2. Space and grid
9. Spacing is on the 8pt rhythm: **4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128** (`system.SPACE`; 4 and 12 are half steps for icon gaps).
10. A screen names ONE grid (`system.GRIDS`): `poster` (centred 8 of 12) · `editorial` (7 / 4) · `ledger` (3 label + 9) · `split` (6 / 6) · `bento` (unequal tiles) · `stack` (rows). Stage margins 96px, gutter 32px.
11. Nothing essential within 70px of the stage edge (`system.SAFE`).
12. The composition follows the content: how many items, how long, pictures or not (`layout_auto.content_features`, `deck.pick_layouts`, `build_webapp.pick_layout`). Never one default skeleton; another seed gives another skeleton.

## 3. Colour
13. A palette = a tinted neutral ramp + **one primary + one support** (`system.palette`, built in OKLCH). Accent hues on a screen ≤ 3; right/wrong colours are counted separately.
14. Text contrast ≥ 4.5:1 (large display ≥ 3:1). `design.py --validate` must print "all palettes valid".
15. Right = light teal-blue, wrong = deeper orange-red: apart in hue AND lightness (colour-blind safe), and always also said in words or a mark (O / X). **A word that names a colour is drawn in that colour** (초록불 green, 빨간불 red, 청팀 blue, 금 · 은 · 동): `meaning.py` (`color_of`, `assign`, `js()`) is asked before any rotation of tones, and a neighbour never keeps a look-alike hue.
16. **No fluorescent colour** (`system.is_neon`: OKLCH C > 0.165 with L > 0.7). An accent covers ≤ 5% of the screen: one word, one rule, one icon.
    Slides (.pptx): the primary may carry structure (a cover field, a header band, a card head). The support colour and one third tone
    (`deck_style.third_tone`, far in hue from both) are markers only: badges, icon tiles, a second head, chart series. Never a fourth hue.
17. Greys carry a little of the brand hue (`system.neutral_ramp`), never pure #808080. No cream paper + serif headline (the "AI company" look).

## 4. Surfaces and ornaments
18. **Matte.** No coloured blur: no `box-shadow` / `text-shadow` `0 0 Npx <colour>`, no `drop-shadow(0 0 …)`, no canvas `shadowBlur`. One neutral shadow that falls down (`0 18px 40px -22px rgba(0,0,0,.55)`) or one hard offset, never both.
19. No hollow outlined type (`-webkit-text-stroke`). Oversized numerals are filled at 8 to 10% of the text colour.
20. No gradient through two different hues. A background is one colour, or two lightness steps of the same colour.
21. The ornament vocabulary is closed (`system.ORNAMENTS`): **rule · kicker · frame · edge · corner · numeral · grain**. A style uses at most TWO of them (`STYLES[id]["orn"]`); a screen shows at most three ornament elements.
22. No scattered confetti, sparkles, blobs, light beams, perspective grids, emoji as decoration. A heading has no emoji.
23. Icons: one line weight (Tabler 1.6 to 2px; Lucide 2px in decks), on a matte tile, picked by what the line names (`deck_icons.pick`): no icon is better than a vague one. Photos are real and licensed, or absent. Living things are never faked in 3D.

## 5. Motion
24. Durations: instant 90 · fast 160 · base 240 · slow 420 · scene 700 ms. Eases: `standard` (.2,0,0,1) · `enter` (.16,1,.3,1) · `exit` (.4,0,1,1). Stagger 60ms.
25. One thing moves per beat. Enter = fade + 12 to 24px of travel. Exit is faster than enter. Backdrops do not animate.
26. `prefers-reduced-motion`: no travel, only fades.
26a. Two registers: calm (documents, reports, games' menus: rules 24-26) and **motion graphics** (talks, openings, videos: preset E below). Motion graphics may use the syllable drop, pen draw-on and cursor scenes, but still: one accent moves per beat, nothing moves while it must be read, and the presenter's click starts every beat.
26b. Motion graphics are script tweens, not CSS transitions (a recorder that freezes the clock catches a transition half way). Big photos or filtered layers that move get their own compositing layer (`will-change: transform`).

## 6. The 13 styles are structures
27. A style = grid + type treatment + radius + two ornaments + backdrop, then a palette. Two styles must differ in at least three of those five, not only in colour.

| id | name | grid | type | radius | ornaments | backdrop |
|---|---|---|---|---|---|---|
| neon-cyber | 먹빛 테크 | ledger | 700, tracked labels | 6 | kicker, grain | dotgrid |
| gold-luxury | 먹과 놋쇠 | poster | serif 600 | 2 | frame, rule | frame |
| pop-colorful | 팝 블록 | bento | 800 tight | 20 | corner, numeral | blocks |
| festival-party | 축제 포스터 | stack | 800 | 28 | corner, rule | papercut |
| tv-gameshow | 스튜디오 쇼 | split | 800, tracked labels | 10 | edge, rule | panels |
| glass-3d | 소프트 뎁스 | bento | 700 | 28 | edge, grain | planes |
| anime-cartoon | 만화 컷 | split | 800 tight | 12 | corner, grain | halftone |
| pastel-cute | 파스텔 | bento | 760 | 40 | corner, kicker | hills |
| retro-pixel | 픽셀 | split | 800 open | 0 | grain, edge | pixel |
| minimal-premium | 에디토리얼 | editorial | 700, tracked labels | 2 | rule, kicker | minimal |
| chalk-paper | 칠판 | stack | 700 | 14 | frame, rule | chalk |
| nature-calm | 자연 | editorial | 700 | 20 | rule, corner | bands |
| ink-poster | 잉크 포스터 (preset E) | swiss | 800 tight, mono labels | 12 | hud, rule | hud |

### Preset E (「잉크 포스터」, `preset_e.py` + `motion_e.js`)
- Palette (from the reference video): ink `#121214` · paper `#F0EDE6` · vermilion `#E4502F` (the ONE accent) · cobalt `#3338F0` (on ink as text: `#6F74FF`) for "with the tool" and pen notes · grey `#8E8E92` · lime `#D8E46C` for a correct mark only. Every text pair is checked in dark and light (`preset_e.py --check`); vermilion on paper is large text only (3.3:1).
- Grid: 12 columns, 128px margins, 32px gutter; text left six, picture right six; big type may span. Type: big 176 · h1 84 · h2 62 · card 46 · body 34 · detail 30 · kicker/label 28 (nothing under the 28px slide floor). Weight 800 max, big type tracking -0.055em.
- Six cards, all flat (1.5px hairline, radius 12, no shadow): note · step (mono accent number) · ask (one accent caret) · pair (hairline down the middle, the tool side in cobalt) · node (outline icon + label) · window (an app frame: the real screen first).
- Motion tokens: xs 120 · s 200 · m 260 · l 420 ms, gap 60, syllable stagger 45, word 70. Fast in, blur only while moving, hold still. Back / print / reduced motion = final state.
- Layer prefix: every class is `e-` so older page CSS (`.hl` `.chip` `.pn`) cannot leak in. Recolouring one slide means setting the `--e-*` values on that slide (custom properties resolve where they are declared).
- Garnish (`garnish.py`): backdrops by role (story / tool / calm), one base prompt, light from the upper right, left 55 % dark, a soft scrim from the text side; no text, logos or faces; skipped on dense slides. One soft accent light is the only glow this preset allows, and only inside a backdrop picture.

The retired looks (neon grid floor, bokeh, glass blobs, stage light beams, bunting + confetti) keep their ids so old specs still build; they are drawn the new way.

## 7. Self-review gate: 「전문 디자이너가 그대로 쓸 수준인가?」
Run `python3 shared/design/ai_look.py --html page.html` (every checker also runs it and prints `밤티 검사`). Ship only at **5/5**:

| # | criterion | passes when |
|---|---|---|
| 1 | type | ≤ 3 named families (aim for 1), no weight 900 more than twice, no italic Korean |
| 2 | colour | ≤ 3 accent hues among the theme colours, no fluorescent colour |
| 3 | surface | coloured glow ≤ 2 places, no hollow type, ≤ 1 multi-hue gradient |
| 4 | rhythm | ≥ 60% of spacing values on the 4px step, body line-height ≥ 1.3 |
| 5 | restraint | no element with more than 5 stacked decoration layers, ≤ 3 emoji in headings |

Then look at the picture once and answer three questions a checker cannot: Is the brightest thing the subject? Can you say what each ornament is for?
If the colour were removed, would the layout still read? If any answer is no, cut the piece. Fewer, better pieces win.
