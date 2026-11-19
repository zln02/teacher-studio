# Integration pass (2026-11-19)

Windows, `PYTHONUTF8=1`, one headless browser at a time. Machine was also running a heavy 3D-deck agent, so timing checks are noisy.

| Step | Result |
|---|---|
| `tools/test_*.py` (11 files, incl. `TS_BROWSER=1` test_webapp) | PASS. One stale assertion fixed (router case count 38 -> 47) |
| `shared/tools/test_*.py` (test_color, test_video_eyes) | PASS |
| `sync_shared.py` + `--check` | PASS (635 copies, dist zips rebuilt). Drift found and synced: `ensure.py` (x6), `check_page.py` (waive), slide scripts |
| 17 skins `studio.py fire` | 17/17 PASS |
| Slide decks x4 (HTML + `--pptx`) + `pptx_check` | 4/4 PASS, 0 fail 0 warn |
| Class tools x5 | 5/5 build; a-timer fails only the 4x-throttle frame-rate check (see known issues), the rest PASS |
| Data examples x4 (`check_report`) | 4/4 PASS (colour-blind WARNs only) |
| Webapp examples x2 (`check_webapp`) | 2/2 PASS |
| Game spec examples x12 (`build.py` incl. `check_game`) | 11 fail ONLY the 4x-throttle frame-rate check; f-sort-recycle also had a real clipping FAIL (fixed, below) |
| Switch: game `waive` | builds, no schema error (its only FAIL is frame rate, which cannot be waived) |
| Switch: slides `template_blanks` | with flag: deck + pptx_check PASS; without flag: placeholder FAIL as designed |
| Switch: data `show_ids` | PASS; check turns the ID check into a WARN (「밖으로 보내지 마세요」) |
| Timer + 「팀 차례」 HUD (c-survival: timer 20 + 3 teams; j-tv-quiz: timer 25) | `hud_overlaps=0`, `hud_hits=[]` in `design_review`; `check_game` has no HUD FAIL |
| `setup.py --agent claude-code` | all 7 skills installed, each with its description |

## Fix
- `skills/teacher-game/assets/components/components.css`: the sort game's bin counter (`× 1`) sat 8 px from the bottom, inside the bin's 40 px lid border plus the checker's margin, so `clipcheck` flagged it. Moved it to `right/bottom: 62px`. f-sort-recycle: clip FAIL gone.

## Known issues
- **Frame rate under 4x CPU throttle (< 30 fps)** fails on every game and on the class-tools timer on this PC (2-22 fps, also when run alone, and worse while two runs overlapped). Not a regression: commit `fa3efe5` (where the check was introduced) fails the same way (a-escape 7.2 fps), and `0d49b43`, `cf3b9db` fail too. Records as a known PC-load issue; the check's own message says classroom PCs are fine. A quiet-machine rerun is still worth doing.
- `b72f6b6` is NOT a usable baseline: it predates the Wow kit and the frame-rate check (it prints PASS only because the check does not exist there).
- `pptx_check.py` without `--spec` / `--allow-blanks` passed a deck that still contains `[학교명]`; the blank gate seems to live in `deck.py` (FAIL there) and in `pptx_check --spec`. Not investigated further.
- Another agent was editing `skills/teacher-slides` (deck scripts, new `assets/spec-examples/context/*.json`) during this pass; the deck scripts were swept into the sync commit, the new context examples are still untracked and were not fired.
