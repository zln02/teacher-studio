<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.svg">
  <img src="docs/assets/banner-light.svg" alt="Teacher Studio" width="100%">
</picture>

English · <a href="README.md">한국어</a>

**Say one short line to your AI. Get expert-level work back.**

</div>

Teacher Studio is a skill bundle for Claude and Codex (Agent Skills, `SKILL.md`) that turns short requests into polished, checked results. **Teacher-friendly Korean defaults come first, but anyone can use it. There is no profession or language gate.**

> The AI answers in **your language**. The classroom defaults (big board-readable text, tablet touch, no student-info fields) and the sample prompts are Korean because the first users are Korean teachers.

## What it does

The target is **all work you do with AI**, in two layers:

- **Our own tools (creative and education work):** games (7 play styles, auto themes, a "Wow" kit for juice and sound), web slide decks (short JSON spec -> designed deck, 13 styles (incl. preset E "ink poster") x 23 slide types, 4 contexts: class / promo / public report / personal, editable .pptx), motion videos and opening screens (MP4 export), class tools (timer, picker, teams, bracket, scoreboard), data analysis (`teacher-data`: anyone's CSV/XLSX -> plain-language chart report, the AI never reads the raw rows), documents (`teacher-docs`: 공문, 가정통신문, notices and reports as 한글 HWPX / Word / PDF with the official Korean format checked, form filling, editing an HWPX in place, PDF merge/split), a legal guide (looks up current law from official sources), and `video_eyes` (reads frames and subtitles of a video locally only).
- **Direction first:** for a vague request it shows three directions (one recommended) and mood preview cards before asking anything, then one question round (max 5, each with a recommended answer; "yes" accepts all); "just do it" skips it. Planning, research and analysis go to a one-page co-plan draft. `tools/router_eval.py` measures this routing per model.
- **One production line for everything:** plan, script, storyboard (콘티), build, fix, deliver, with at most three "does this look right?" checkpoints; small clear jobs skip steps and "just do it" skips the checkpoints. `storyboard.py` draws the frame sheet, `deliver.py` prepares the hand-out pack (offline QR for your own link, privacy checklist, credit line) and never uploads anything.
- **Everything else (coding, web, security review):** a skill scout finds an existing, vetted skill (for example Anthropic's official office-document skills, web guidance, a security-audit skill), asks you first, then installs it on first need. Otherwise the model's own ability is used, under the same no-regret rules and quality gates. Dedicated **research/compare tools are planned (준비 중)**. All 8 skills ship as ZIPs in `dist/`.

The AI asks 1 to 3 questions only when your request is vague (with a recommended answer each). A one-time setup stores your level, subject and device on your own computer.

## Your template first

The goal is **your design**. If you have a school or company template, brand colors, or reference images/videos, it follows them first. Our design system is only the fallback when you give nothing. Please make sure you may use the reference material (copyright, trademarks).

## Who uses it

| Who | Example request |
|---|---|
| Teacher | "A solar-system quiz show for 5th grade" |
| Office worker | "6 clean opening slides for our team workshop" |
| Small business owner | "A warm intro video for our cafe's new menu" |
| Student | "Slides for my club presentation" (Claude requires age 18+; check the service terms) |
| Developer / data analyst | "Write tests first, then implement this" / "Clean and summarize this CSV" (coding uses vetted existing skills plus the model; CSV/XLSX analysis uses the built-in `teacher-data` skill) |
| Creator | "A flashy quiz game for my 10k-subscriber milestone" |

## Install (try from the top)

1. **One line:** tell Claude Code, the Claude desktop app's Cowork or Code tab, or the Codex app "Install this skill: https://github.com/zln02/teacher-studio" (plain Chat tab cannot install from a link, use step 3). Cowork and plugins need a paid plan (Pro+); Team/Enterprise admins must enable them.
2. **One command:** `npx skills add zln02/teacher-studio` (choose all 8 skills). In Claude Code: `/plugin install teacher-studio --marketplace zln02/teacher-studio`.
3. **Upload files:** Claude app Chat, upload the 8 ZIPs in [`dist/`](dist/) under Customize, Skills (turn on code execution in Settings, Capabilities).
4. **Copy folders:** copy the eight `teacher-*` folders from `skills` into `.claude/skills` (Claude Code) or `.agents/skills` (Codex).

Other apps (verified 2026-11-19 from search summaries, **confirm on screen before a training**): ChatGPT personal accounts use the Codex app (skills folder `~/.agents/skills`, skill-installer with a GitHub folder URL, or plugins); plain ChatGPT Skills exist only on Business/Enterprise/Edu with admin approval. The Gemini app accepts SKILL.md-format Skills (since 2026-10) but our scripts need tools, so expect limited results; Gemini CLI: `gemini skills install https://github.com/zln02/teacher-studio` (developers).

Details: [INSTALL.md](INSTALL.md) (Korean). Then say "start Teacher Studio" or just ask for what you want.

## Where it works

| | Claude app/web | Claude Code | Codex |
|---|---|---|---|
| Build + auto checks | yes (turn on code execution) | yes | yes |
| Getting results | preview/download | saved locally, opens Chrome | saved locally, opens Chrome |
| Share link / QR | yes ("Publish") | files only | files only |
| Video file | Chrome recording (.webm); MP4 conversion unlikely | MP4 (ffmpeg installed on first use, about 150 MB) | MP4 (needs internet allowed) |
| Latest-law lookup | turn on web search | built in | needs live web search |
| Free plan | skills and code execution included | subscription or API key | included (limits not published) |

Checked against official docs on 2026-11-18. Results are single offline HTML files; nice Korean web fonts are fetched on open if online.

## Limits and responsibility

- **No student personal data:** no fields for names, IDs, photos or grades, and nothing is stored. Pseudonymize before pasting anything into chat.
- **No flows where students use the AI directly** (Claude is for ages 18+).
- **No imitation of real broadcasts, characters or brands**; original look-alikes only.
- **Check third-party assets** (art, text, music) before publishing a public link.
- **Grades and school-record text** are not finalized by the AI; the teacher reviews them.
- Uncertain facts are marked "needs checking". The legal guide (Korean law) is **not legal advice**; final judgment and responsibility are yours.
- Output is an AI-assisted draft. Review it before use.

## Roadmap (all planned, 준비 중)

Korean official documents (HWPX), PPT files (alongside Claude's official skills), video editing (cut, subtitles, photo slideshows), worksheets, data-analysis and research/compare tools, more game types, auto-making a new design from a reference.

## Contribute and credits

[Feature request](../../issues/new?template=request.yml) · [Bug report](../../issues/new?template=bug.yml) · [How it works](docs/how-it-works.md) · [CHANGELOG](CHANGELOG.md)

Author: Jinyoung Park ([zln02](https://github.com/zln02)). The name and banner may not be used as the original without permission (Apache-2.0 section 6 grants no trademark rights).
Code: [Apache-2.0](LICENSE) · Third-party notices: [NOTICE](NOTICE) (anime.js MIT, Kenney CC0, Google Fonts OFL).

<sub>An unofficial open-source project, not affiliated with Anthropic or OpenAI. Made for Korean teachers, open to everyone.</sub>
