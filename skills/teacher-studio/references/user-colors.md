# The user's own colours first (template-first rule)

## When
The user brings a logo, a photo of their brand, a PPT/POTX/DOCX/HWPX template, or a website (「우리 학교 로고 색으로」「회사 PPT 색 그대로」「이 사이트 색」). Their colours come BEFORE our palettes and moods. This is a means to honour what they already have, not our own design: the colours stay theirs, we only make sure text is readable.

## Steps
1. Extract (stdlib; run the copy inside the skill you are using, e.g. `<skill>/shared/design/color_from.py`; repo root: `shared/design/color_from.py`):
   `py color_from.py <logo.png|photo.jpg|deck.pptx|theme.potx|doc.docx|form.hwpx|site.css|page.html> --out my-palette.json [--dark]`
   - PNG is read with the stdlib. JPG/GIF/BMP/WEBP need Pillow: `py shared/tools/ensure.py pillow` asks in plain Korean; install only with the teacher's yes (`--yes`). If it is missing the tool prints the message and stops; offer a PNG instead.
   - PPTX/POTX/DOCX/XLSX: the theme's accent1 is the main colour. HWPX: only colours the document really uses (often black/white only, so it may say "no colours found": ask for the logo). Old .hwp/.ppt/.doc: ask them to save as HWPX/PPTX/DOCX.
2. Say what you found in one plain line (「주색 파랑, 포인트 주황으로 할게요」). Mapping keeps the hue and moves only lightness so text contrast is >= 4.5; `good`/`bad` are always green/red-ish but split in lightness so they also differ for red-green colour blindness.
3. Use it: spec `"design": {"palette_from": "my-palette.json"}` (game, slides, class tools; path relative to the spec file for slides) or `design.py --palette-from my-palette.json` or `report.py --palette-from ...` (data). Type sizes, motion, fonts and layout stay ours.
4. Save as the default ONLY when the user asks (「앞으로 계속 이 색으로」): `color_from.py <file> --save-default` (writes `palette` to `~/.teacher-studio/prefs.json`; `prefs.py palette-show|palette-reset`). Then `"palette_from": "saved"` uses it. Never apply a saved palette silently.

## Colour-blind check
`color_check.py` runs inside the game, slides, class-tools and data checkers as a WARN (never FAIL): meaning colours (correct/wrong, team colours, chart series) that look alike for protan/deutan/tritan vision (Machado 2009, OKLab distance < 0.10). Fix = add shapes/text (○ ✕, 정답/오답, labels), or change lightness/hue. Do not block delivery on it.

## Helpers
`oklch.py`: `hex_to_oklch`, `oklch_to_hex` (gamut clamp), `harmony(seed, "analogous|complementary|triad|split|tetrad")`, `ramp(seed, n)` (equal perceived steps), `fit_contrast(fg, bg, 4.5)` (lightness only). Use them for tints of the user's colour instead of ad-hoc mixing.

## Limits to say honestly
Only colours are taken, not layout or fonts (approximation, not a copy). Logos and photos are never copied into the output. A greyscale logo gives a neutral primary plus a default blue accent (the tool notes it).
