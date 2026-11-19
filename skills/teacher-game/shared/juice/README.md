# shared/juice - Game Wow kit

Vanilla JS + CSS (ES2017, no `?.` / `??`), no dependencies, no network, no storage, MIT-compatible (all code written here; the sound
synth is our own ZzFX-style implementation, Tone.js is not used). One kit, used by `teacher-game` (all 7 mechanics through
`assets/components/juice-game.js`) and `teacher-class-tools` (picker, timer, teams, bracket, scoreboard).

| file | what |
|---|---|
| `juice.js` | presets (params), particles, flash governor, squash/shake/kick/hit-stop, count-up, timer pulse, streak tiers, reveal, podium, 12 sounds, music loop |
| `juice-motion.js` | 10 motion effects (`Juice.fx.*`) |
| `juice.css` | press/hover feel, banner, podium, toggles, reduced-motion rules |
| `juice_lint.py` | accessibility + safety lint used by `check_game.py` / `check_tool.py` |

Tune everything with JSON: `Juice.configure({correct:{burst:{count:20}}})`, or in a game spec `"juice": {"correct": {"burst": {"count": 20}}}`
(`"juice": false` turns the kit off). Values are starting points - tune by eye and ear.

## Parameters (`Juice.params`)
| key | default | meaning |
|---|---|---|
| `input.respondMs` | 100 | budget for the first visible response after a click (lint measures it) |
| `press.hover / press / backMs / anticipate` | 1.05 / 0.95 / 120 / 0.97 | button scale on hover / press, back-out time, slight anticipation |
| `correct.hitStopMs` | 60 | particle freeze after a hit (50-80) |
| `correct.squash` | x 1.15, y 0.9, 150 ms | squash and stretch on the answer |
| `correct.burst` | count 18, 750 ms | particles (12-24 sweet spot); halved on low-end |
| `correct.kickPx / kickMs` | 3 / 110 | camera kick of the whole scene (2-4 px) |
| `wrong.shakePx / ms` | 6 / 250 | ONE decaying shake; the host adds icon + text (never colour alone) |
| `score.countMs / minMs / maxMs` | 650 / 500 / 800 | count-up, ease-out |
| `timer.pulseFrom / pulseScale` | 5 / 1.08 | last 5 s: a gentle swell once per second, never blinking |
| `streak.tiers / repeatEvery` | [3,5,10] / 5 | celebration tiers (small, big, confetti); then every 5 |
| `reveal.tensionMs` | 2200 (1500-3000) | drumroll + decelerating number, then burst |
| `reveal.podiumStepMs` | 1200 | 3rd -> 2nd -> 1st |
| `lowEnd` | cores 4, memory 4, FPS probe 600 ms (< 40 fps) | any hit halves particles (`burstScale` 0.5) |
| `particles.max` | 80 | hard cap |
| `flash.maxPerSec / maxAlpha / maxAlphaSmall / maxArea` | 2 / 0.12 / 0.5 / 341x256 px | flash governor (WCAG 2.3.1: <= 3 flashes/s, area <= 341x256 or faint) |
| `sound.master / sfx / music` | 0.9 / 1.0 / 0.5 | SFX is twice the music. The game adapter sets master 0.3 to match the engine's own bus |

## API (short)
`Juice.install({camera})` · `reduced()` / `setReduce(b)` (OS setting, in-page 「효과 줄이기」, host hook) · `burst(x,y,o)` · `confetti()` ·
`hitStop(ms)` · `flash(color, alpha, ms, rect)` (the only flash door) · `squash(el)` · `shakeEl(el)` · `kick(px)` · `press(el)` · `pop(el)` ·
`countUp(el, to, ms)` · `timerPulse(el, secondsLeft, baseTransform)` · `streak(n, anchor)` · `banner(text, tier)` ·
`reveal(el, to, {tensionMs, celebrate, onDone})` · `podium(box, teams, {onDone})` (teams only; the rest shown as plain chips, no rank) ·
`sound.play(name, {streak, step, ms})` · `setMuted(b)` · `warm()` · `music.start/stop/ramp` · `mountToggles(box)` · `stats` (read by the lint).

Reduced motion (OS setting or in-page switch): nothing moves; every effect becomes a still state and still calls its `onDone`.

## Sounds (`Juice.presets`)
`click` `pop` `correct` (3 layers: pluck + two-note chime + sparkle; pitch +1 semitone per streak step, max +12) `wrong` (soft low bonk, not a buzzer)
`comboUp` `tick` `tickLast` `reveal` `drumroll` `fanfare` `podium` (step 0-2) `whoosh`.
Muted by default when `navigator.webdriver` is set (automated checks). 「소리 끄기」 is a visible switch in games and tools.

## Motion effects (`Juice.fx`, generic techniques)
| effect | use |
|---|---|
| `impactFrame()` | one faint tint + radial lines for ~0.25 s (never strobes) - big moments |
| `letterDive(el)` | title letters dive in, staggered |
| `layerExplode(box, {mode:'in'|'out'})` | children fly apart / together (teams re-split) |
| `rackFocus(target, others, {clear})` | attention shift, blur <= 3 px |
| `dollyZoom(subject, backdrop)` | winner reveal: subject grows while the backdrop shrinks |
| `paperTear({color, onMid})` | round / section transition (game start on some seeds) |
| `bladeSlice(el)` | cut a card in two (right/wrong split, removal) |
| `sketchWords(el)` | hand-drawn underline |
| `orbitRing(box)` | timer / loading ring with an orbiting dot (`set(f)`, `spin()`) |
| `dayDial(box, {slots})` | 12-hour schedule dial with a hand |

## Where it is used
Games: correct = squash + hit-stop + burst + kick + 3-layer chime; wrong = one soft shake + `✖` + words; streak tiers; last-5 s timer swell;
music quickens before the last question; result = drumroll -> decelerating number -> burst, or podium for teams; paper tear on some seeds.
Tools: picker = rack focus + drumroll + impact + burst; timer = last-5 s ticks + swell, fanfare + burst + confetti at the end; teams = layer-in;
bracket = champion fanfare; scoreboard = count-up + squash + 「🏆 시상식」 podium.

## White-hat rules (what the kit will NOT do)
Praise, mastery and progress only. No random rewards or loot boxes, no fake urgency (no flashing countdown), no streak-loss pressure
(a miss resets quietly, nothing is shown), no sad "lose" sound, no mocking text, no individual ranking or low-score highlighting
(podium is for teams; everyone else appears as plain chips).

## Accessibility lint (`juice_lint.py`)
Static: no CSS loop faster than 3/s, `prefers-reduced-motion`, 「효과 줄이기」 and 「소리 끄기」 present, kit present.
Runtime (Chrome headless, CPU throttled 4x via CDP, audio stubbed + muted): the page's own work per frame (script + style + layout) <= 33 ms, click -> next frame <= 100 ms (raw fps is reported; below 30 it is a WARN because headless Chrome draws in software, and every speed result turns into a WARN when the calibration probe says the test PC is too slow or busy), flashes <= 3/s and none above
341x256 px at strong alpha, tap targets >= 44 px, class text >= 28 px, right/wrong never colour alone, no JS errors.
Honest limits: flashes are counted from the governor's log plus a CSS scan (no pixel-level luminance probe); response time is "click to next frame"
in software-rendered headless Chrome.

## Sync (maintainers)
`tools/sync_shared.py` must copy `shared/juice/` into `skills/teacher-game/shared/` and `skills/teacher-class-tools/shared/` (the builders and checkers
fall back to the repo-level `shared/juice/` when the skill copy is missing).
