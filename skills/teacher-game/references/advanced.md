# Advanced (read only the part you need)

## A. How the look is chosen
- Default `design.theme` is `auto`: every build draws a fresh combination from 12 styles (`neon-cyber` · `gold-luxury` · `pop-colorful` · `festival-party` · `tv-gameshow` · `glass-3d` · `anime-cartoon` · `pastel-cute` · `retro-pixel` · `minimal-premium` · `chalk-paper` · `nature-calm`), 10 question layouts (footprints that differ: full, upper band, lower third, centre, left, right, rail, stair, bento) and button / card / scoreboard / title variants. The build prints `design.seed=N`; the same seed gives the same look.
- `design.words` (우주·바다·동화·숲·역사·긴장감·따뜻하게·고급스럽게·송년·스포츠·과학 …) and `mood` pick the backdrop, helper character, props, celebration, title font and music (`scripts/theme_auto.py`; same words -> same result).
- The nine ported worlds are used only when the request names that world: 「방송국 퀴즈쇼」 `tv-studio` · 「강당 종 울리기」 `auditorium-bell` · `space-station` · 「거북선」 `joseon-war-room` · `antidote-lab` · `sun-temple` · `post-office-night` · `cell-feeding` · 「분리배출」 `recycle-robot`.
- Preview without building: `python3 scripts/style_auto.py --spec spec.json`, `python3 scripts/layout_auto.py --spec spec.json`.
- Your own touch on top: `custom_css` (<= 6000 chars, text still >= 34 px) and `custom_svg` (<= 12000 chars, `<svg viewBox="0 0 1920 1080">` behind everything). No outside addresses, script, onclick, `?.`, `??`.

## B. Game Wow kit (sounds and effects; automatic)
Right answer = squash + short freeze + particles + light shake + 3-layer sound (pitch rises on streaks); wrong = one gentle shake + ✖ + words (never colour alone, never mocking); 3/5/10 streak cheers; last 5 seconds swell without blinking; result = drum roll -> count-up -> confetti, team games get a podium (3rd -> 2nd -> 1st).
- Tune: spec `"juice": {"correct": {"burst": {"count": 20}}}` (values: `shared/juice/README.md`); off: `"juice": false`.
- White-hat only: praise, growth, progress. No random rewards, fake urgency, streak-loss pressure or shaming of individuals.
- 「효과 줄이기」 and 「소리 끄기」 are always there; the OS reduce-motion setting is honoured.
- The check measures flashes (<= 3/s, <= 341x256 px), text >= 28 px, tap targets >= 44 px, colour-only cues, the page's own work per frame (<= 33 ms at 4x CPU throttle) and click response (<= 100 ms). Raw frame rate is a WARN only: headless Chrome draws in software, and a slow or busy test PC turns every speed result into a WARN.
- Before/after proof: `python3 scripts/wow_proof.py --spec <spec> --out <dir>`.

## C. A mechanic the tool does not have (only when the user insists)
- Read `references/engine-api.md` only; never `assets/engine.html` (76 KB).
- Copy the closest `assets/components/<mechanic>.js`, write ONE new component, reuse `H.ask` (question flow) and `H.finish`; add its limits to `scripts/specs.py` `LIMITS`. A new world picture goes in `assets/themes/`.
- The old whole-file way (`scripts/build_game.py` + `assets/kits/`) remains for reference; size rules in `references/classroom.md`.
- `motion` does not run on pre-2020 Chrome: use anime.js / CSS, or `libs:["motion"]` + `allow_modern:true` together (the check then warns instead of failing).

## D. Legacy finished skins (only when the user names one)
`python3 ../teacher-studio/scripts/studio.py fire game/quiz-show/tv-studio --content content.json` (`--list` shows them; format in `assets/missiles/<name>/README.md`). Never for a new request.

## E. Small things
- Credit: the file carries an invisible maker tag and a 「만든 도구」 line in the teacher menu. A visible 「교사 스튜디오로 만듦」 on the result screen only with `credit:true`, and only when the user asks.
- English read-aloud (`speak`) picks the most natural voice on the device (`shared/voice/voice.js`); the teacher menu shows which.
- HUD rule: timer bar, score and buttons live in the top band (y < 126); question boxes and 「팀 차례」 tags start below. `check_game.py` (hudoverlap) and `design_review.py` (hud_overlaps) fail when they collide.
- Team games: team scores only, timer 20 s or more, a catch-up bonus, no shaming on a wrong answer.
- Phone (`device:"phone"`): quiz has a real portrait layout; the checks also measure 390x844 and 844x390.
- Sharing (Claude app): 「게시(Publish)」 -> copy link -> Chrome 「QR 코드 만들기」. Always suggest keeping the downloaded file too: it opens offline.
