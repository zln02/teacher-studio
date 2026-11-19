# Per-type content of the pipeline stages

대본 = what is said/asked/written. 콘티 = what is seen, in order. Fill only what the type needs (short).

| Type (route) | 2 대본 (script) | 3 콘티 (storyboard) | 4 제작 | 6 배포 |
|---|---|---|---|---|
| slides (`teacher-slides`) | per-slide message (one sentence) + speaker `note` | slide-by-slide list: type, title, visual; `storyboard.py deck.json` | `studio.py build slides --spec` | web file, Ctrl+P -> PDF, QR/closing slide, LMS upload |
| game (`teacher-game`, `fire`) | questions + answers + rules + clue words | screen flow (title -> play -> reveal -> result), win/lose, 2-3 juice moments (꽃가루, 종, 긴장 음) | `fire` or `build game --spec` | one HTML, TV/phone, LMS/Classroom/padlet 링크 첨부 |
| motion / video (`teacher-motion`) | narration + captions per shot | shot list with seconds (sum = target length), motion per shot | `fire motion/...` + `--mp4` | webm/mp4 export, TV play, upload to LMS/YouTube unlisted (ask first) |
| class tool (`teacher-class-tools`) | none; the spec list (what buttons, default minutes/teams) | none (merge); at most a 3-line layout note | `build_tool.py` | one HTML, pin on the TV, works offline |
| data report (`teacher-data`) | analysis questions (what do you want to know?) | chart plan: one chart per question, kind + takeaway | teacher-data script (never read rows) | HTML/PDF print; hide names; no raw rows |
| document / 가정통신문 | outline (headings) -> draft text, placeholders for names/dates | page layout list: header, body blocks, reply slip | docx/pptx/hwp skill or chat text | print/PDF, 한글 file; privacy check (no names) before sending |
| web / app / dev (not in table = R5) | user stories (who needs what) | screen wireframe list + feature list | build with own ability, then test | say what is outside the harness; run tests; ask before deploy |
| co-plan (planning/research) | outline -> draft (one page) | skip | sources check (links + date) | one-page plan; 출처 list |

## 6 배포 menu (offer only what fits; run `scripts/deliver.py FILE`)
- Single HTML file: offline OK; send by 메신저/메일/USB; open by double-click.
- Phone/TV: TV = full-screen (F11), phone = open from a link or file; link only if the user gives a URL (QR is drawn offline).
- Print/PDF: Ctrl+P -> PDF (background graphics on).
- mp4/webm: export button or `--mp4`.
- LMS / Google Classroom / padlet: attach the file or a link; teacher uploads (we never upload).
- Privacy check before sharing: student names? faces? grades? other people's works? If yes, stop and ask (law route).
- 출처 line when another skill/doc was used (`skill_scout.py log`), one line at the end.
