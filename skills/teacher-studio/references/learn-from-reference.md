# Learn from a reference - patterns only, never copies

## When
The teacher says 「이 사이트처럼」「이런 느낌으로」「저 앱 같은 디자인」, or gives a URL, a screenshot or a video of something well made.

## Legal line (say it once, short)
「구조와 느낌만 배우고, 글·그림·로고·코드는 가져오지 않아요.」
We take structure, rhythm and feel (layout, spacing, type scale, color relationships, motion speed). We never take text, images, logos, icons, fonts files, code or a recognizable look-alike of a brand (trade dress). Values are rounded and softened on purpose.

## Hard rules
- Only a public page the teacher explicitly gave. One page, one load per viewport. No crawling, no login, no clicking through.
- `robots.txt` is checked first; if the path is disallowed the tool stops. Then ask for a screenshot instead.
- Nothing from the page is saved except our own screenshots and numbers (no HTML, images, fonts, scripts).
- Fonts are reported only (they may be licensed). Pick a similar-feeling font from `shared/fonts`.
- Student or private pages (logged-in, school intranet): do not analyze.

## Steps
1. **Analyze**: `python scripts/ref_analyze.py URL|file.html [--out DIR] [--scroll-video]`
   Output (default `~/TeacherStudio/ref/<host>/`): `analysis.html` (contact sheet), `analysis.json`, `tokens-suggestion.json` (our token names, softened), four screenshots (390x844 and 1440x900, fold and full).
   Screenshot or video instead of a URL: look at the image with your own vision; for a video run `shared/tools/video_eyes.py clip.mp4` and read the contact sheet. Extract the same things by eye: 3-4 colors, type feel, spacing density, layout, speed.
2. **Look** at `analysis.html` and the screenshots. The numbers are a draft; your eyes decide what actually makes it good.
3. **Say 3-5 patterns in plain Korean**, no jargon. Example: 「여백이 넉넉하고, 제목이 본문보다 훨씬 커서 한눈에 보여요. 강조색은 파랑 하나만 써요. 카드는 같은 모양으로 반복돼요.」
4. **Ask first, only if needed** (one question, with a recommended answer, per `ask-first.md`): e.g. 「이 중 어떤 점이 제일 마음에 드세요? ① 색 ② 배치 ③ 움직임 (추천: ② 배치)」. If the request is clear or 「알아서」, skip it.
5. **Apply to OUR build** as a token set and a layout recipe: start from `tokens-suggestion.json`, keep our own palette family, fonts and wording, then pass through `shared/design/design.py`. Use the layout idea (section order, grid, spacing unit, radius, container width), not the pixels.
6. **Design review side by side**: screenshot ours at the same two viewports next to the reference sheet. Check: does it share the feel but not look like a copy? Same hero image/logo/wording/color-for-color match = fix it. Run the normal checks (contrast, tap targets 44px, mobile width).

## What the tool measures
Color by area (background / text / accent), font families (report only), size, weight and line-height scale, spacing values and inferred grid unit, radii, shadows, container width, section order and roles (header, hero, search, card grid, tabs, footer), component counts (buttons, cards, chips, nav, inputs), transition durations and easings, keyframes, contrast pairs, tap targets under 44px, horizontal scroll on mobile.
Limits: shadow DOM and canvas content may be missed; sections are heuristic. Trust the screenshots over the numbers.

## Report back (Korean, short)
Patterns learned (3-5 lines) -> what we apply -> what we deliberately did not copy. End with the legal line if the teacher might publish the result.
