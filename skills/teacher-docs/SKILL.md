---
name: teacher-docs
description: Makes and edits documents - 한글 HWPX 공문·가정통신문·안내문·신청서·보고서, Word, and PDF 안내문 (make, add a page, merge, split, form fill, watermark) - with one command, a gate (blanks, page count, smallest text) and a preview picture. Use it first when a teacher or anyone needs a notice, a form, an official-format document, a PDF, or an existing file fixed without breaking its layout.
license: Apache-2.0
---

# 교사 스튜디오 · 문서 (한글 · 워드 · PDF)

Run the scripts as written with `python3`; on Windows type `py` instead (no `py`: `python`). Always the short command name, never an interpreter's full path (`C:\...\python.exe`).

Teacher (no coding) asks for 공문, 가정통신문, 안내문, 계획서·결과 보고서, or to fill / fix a 한글·워드·PDF file. You write a **short JSON spec** (or a list of edits); the tools apply the official format, the house typesetting and the checks.
Respond in the user's language, in plain words (`../teacher-slides/references/teacher-language.md`: never show code or file names). Ask-first rule: `../teacher-studio/references/ask-first.md`. Student info, 생기부, someone else's work or public sharing -> also `teacher-law`.

Content quality first: before writing any content read references/content-docs.md; pass the expert gate in shared/content/CONTENT-RULES.md.

## Which job
| teacher says | do |
|---|---|
| 공문 / 기안문 / 협조 요청 | `docs.py make --spec x.json --out 공문.hwpx` with `"kind":"gongmun"` |
| 가정통신문 / 동의서 / 회신서 | `"kind":"notice"` (+ `reply` = 회신서 with cut line) |
| 안내문 / 행사 안내 | `"kind":"guide"` (`sections`, `lead` box; + `reply` = 신청서, `"page": true` puts it on its own page) |
| 신청서 / 동의서 한 장 | `"kind":"form"` (`fields`, `statement`, `sign`, `to`) |
| 「이 PDF 끝에 신청서(한 쪽) 붙여 줘」 | ONE command: `docs.py append 원본.pdf --spec 신청서.json --out 새이름.pdf` (builds the page, merges, checks, draws the preview; the original stays). If the PDF already has that page (our 안내문 puts the 신청서 on the back), the command says so: replace it with `--replace-from N` and tell the teacher it was already there, never ship two |
| 계획서 / 결과 보고서 | `"kind":"report"` (title box, 요약 box, Ⅰ. headings, □ ○ - marks, tables + 자료) |
| 「이 양식 채워 줘」 (.hwpx / .docx / .pdf form) | `docs.py fill FILE --set 성명=… --out new` : `{{키}}`, `[키]`, label cells (성명 → next cell), PDF form fields |
| 「이 한글 파일 고쳐 줘」 | `docs.py patch FILE.hwpx --edits edits.json --out new.hwpx` : `[{"find","replace"}, {"para":n,"text"}, {"after","insert"}]`; exit 2 = some edit not applied -> say which, never claim success |
| 워드로 / .docx | same spec, `--out x.docx` (python-docx on first need; user's `.docx/.dotx` as `--template` keeps their styles) |
| PDF로 | same spec, `--out x.pdf` (our A4 HTML printed by the PC's Chrome/Edge; fonts embedded), or 「Ctrl+P → PDF로 저장」 |
| PDF 합치기·나누기·워터마크·표 뽑기 | `docs.py pdf merge|split|watermark|tables|fields|fill|png ...` (pypdf / pdfplumber on first need) |
| 옛 .hwp 파일 | never upload it. `docs.py text x.hwp` prints the plain guide: 한글에서 「다른 이름으로 저장 → HWPX」, or convert with their own 한글 (`docs.py where` says if installed). |

## What the user did not give (every format: HWPX, Word, PDF)
One rule (`shared/content/CONTENT-RULES.md`, 「Unknowns」). What the user gave is used as given. For the rest, and always with 「알아서」 (= no questions):
- **Body, tables, schedule -> a plausible example value**: a real upcoming date whose weekday matches, a time, a deadline, a place (「시립 실내수영장」), a round amount; names as roles (「우리 학교」「우리 학교장」「담임 교사」), never a made-up real-looking name. Never `○○`, `(학교명 입력)`, `[수영장명]`, and never the words 「확인 필요」「미정」 in a cell.
- **Blanks only where a hand writes**: the 회신서 · 신청서 · 동의서, the sign line, student and guardian fields (`reply` / `form` fields: an empty value or `□` choices). A 가정통신문 the family must answer, choose, pay for or consent to always has its `reply`; a notice with nothing to answer says `"reply": false`.
- **Write every example value into `"fillins"`** (`["수영 수업 날짜 2026. 12. 7.(월)∼12. 11.(금)", "수영장 이름", "참가비 20,000원"]`). The build then adds ONE small line at the foot of the body (「※ 날짜·장소·금액 등 일부 내용은 예시입니다. …」) and prints the list: copy all of it into the last message as 「바꿔 넣을 곳」. No other example mark, and never a 「교사 초안」 stamp in the file.
- **The user wins**: 「빈칸으로 둬」「양식으로」 -> `"template_blanks": true` (labelled underlines in the body too); their own file -> `fill` / `patch` it as it stands.

## PDF: the short path (one build, one look)
1. Write the spec ONCE, complete, from this document's own content (keys below; the files in `assets/examples/` are test fixtures, not patterns: never copy their sections or sentences).
2. `python3 scripts/docs.py make --spec x.json --out 안내문.pdf` . It prints the gate (blanks, dates, fonts, **쪽수 + how full each page is + smallest text**) and `look x.preview.png`.
3. Open **only that preview picture**, once. Do not read the PDF file itself and do not print pages one by one: that costs far more than the whole job.
4. `READY` = done. `NOT DONE` / `FAIL` -> fix the spec and rerun (max 2 loops). The gate also checks that every sentence, item and cell of the spec is in the file (「content preserved」), that no list prints as 「['…']」 and no heading reads 「1. 1.」. A section may hold `body`, `items`, `text`, `table` or `note` (unknown keys FAIL, never dropped quietly); write headings without numbers. A last page that holds only a few lines -> `"max_pages": N` (the build shrinks the print scale a little to fit, never below 10 pt).
Spec extras: `"design": {"font_size": 14 | "large" | "small", "line": 1.6}` (print scale in pt: every size follows) · `"max_pages"`, `"min_font"` (also `--max-pages`, `--min-font`, `--font-size`) · body blocks `{"pagebreak": true}`, `{"image": "file.png", "width_mm": 80, "caption": ""}`, `{"qr": "https://…", "caption": "", "size_mm": 28}` (offline QR), `{"form": {"fields": [...]}}`. HWPX gets the page break and the sizes; pictures and QR are PDF / Word only (HWPX keeps the caption and the address as text, and says so).
A good 안내문: lead box (언제·어디서·무엇을·언제까지) -> 일정 표 -> 신청 방법 -> 알아 둘 점 -> 문의 -> 날짜·발신. A good 신청서 (paper, written by hand: name blanks are fine here): 학년/반/번호 · 학생 이름 · 보호자 성함 · 연락처 · choices as □ boxes with real dates and times (1지망 / 2지망) · 하고 싶은 말 · 개인정보는 이 용도로만 쓴다는 한 줄 · 날짜 · 서명 · 「학교장 귀하」. The 안내문 must point to it (「뒷면 신청서」) and must not describe another way to apply.

A good 가정통신문 (any format, HWPX too): one greeting sentence -> what the family does and by when (box or first item) -> 일정·장소·대상 as a table -> 준비물 -> 안전·유의 사항 -> the 회신서 or 동의서 (`reply`) whenever the family must answer, choose or consent -> 문의 -> 날짜·발신. **Floor, not ceiling** (`shared/content/CONTENT-RULES.md`): one A4 is the goal, a half-empty page is not finished; a notice that drops the reply slip, the table or the safety items a school's own notice would carry is thinner than the request.
`NO-BROWSER` printed = no screen can open in this environment: HWPX and Word are still built and gated; a PDF cannot be printed there (give the `.print.html` and 「Ctrl+P → PDF로 저장」, or run the same command outside the security box). Do not try a browser yourself.

Output: one new file next to the original (never overwrite theirs) + for HWPX a preview page `*.preview.html` (our approximation of 한글: say 「실제 한글 화면과 줄바꿈이 조금 다를 수 있어요」).

## Spec (`docmodel.py` has the full key list)
```json
{"kind":"gongmun", "org":"우리교육지원청", "receiver":"수신자 참조", "title":"... 안내",
 "body":["관련: ...", "다음과 같이 ... 바랍니다.", ["일시: 2026. 12. 3.(목) 14:00∼17:00", "장소: ...", "신청 방법", ["...", "..."]], {"table":{"columns":[..],"rows":[[..]]}}],
 "attachments":["운영 계획 1부", "신청서 1부"], "sender":"우리교육지원청교육장", "receivers":["관내 초등학교장"], "fillins":["담당자 전화"]}
```
A string is an item, a list right after it holds its sub-items; marks are automatic: **1. 가. 1) 가) (1) (가) ① ㉮**, one item alone = no mark, `끝.` added with two spaces (after the last 붙임 line, or under a final table), dates become `2026. 11. 19.`. Dict entries: `{"p": 번호 없는 문단}`, `{"h": 소제목}`, `{"note": "※ …"}`, `{"table": {columns, rows, unit, source, widths, kind:"form"}}`, `{"box": [...], "label": "요약"}`.
Official vs practice and the sources: `references/gongmun-format.md`. `assets/examples/*.json` = test fixtures, not patterns (one per kind, for the builder's tests); a document that repeats one gets the WARN 「예시를 그대로 따라간 것 같아요」.
**No slots, no filler:** `[학교명]`, `20XX`, `○○`, `000-0000` FAIL; so do three or more 「확인 필요」-type cells and any 「교사 초안」 stamp. Fill with example values and list them in `"fillins"` (section 「What the user did not give」); 「양식으로」 -> `"template_blanks": true`.

## Gate (`doc_check.py`, runs after every make; also `docs.py check FILE`)
blanks (`(학교명 입력)`, `○○학교`, `OOO`, `(예시)` too) · unknowns (「확인 필요」-type filler: 1-2 WARN, 3+ FAIL; a 「교사 초안」 stamp FAIL; the example note missing or repeated WARN; underline blanks outside the 회신서 / 신청서 WARN; a 가정통신문 that asks for an answer but has no `reply` FAIL) · PDF: page count (`max_pages` FAIL), a nearly empty last page (WARN), smallest text (WARN under 9 pt, FAIL under `min_font`) · privacy (주민번호 FAIL; 휴대전화·전자우편·「성명: 홍길동」·학년반번호 WARN) · 공문 format (수신/제목, mark order, single-item mark, `끝` two spaces, `붙임` no colon) · dates `2026. 11. 19.` / 24-hour time · simple 띄어쓰기 (WARN, never auto-fix) · file reopens (HWPX: mimetype first+stored, XML, every charPr/paraPr/borderFill reference) · fonts (common Korean fonts; PDF fonts embedded). FAIL -> fix and rebuild; WARN -> tell the teacher in one line each.

## Design (automatic)
A4, 20/20/20/15 mm, 함초롬바탕 12.5 pt body (house default; 한글 always has it; `design.font_size` rescales everything), title 20 pt in the sans face under one accent rule for 안내문·가정통신문·신청서 (PDF), headings 14 pt with an accent bar, tables with a light header fill and right-aligned numbers, hanging indents so wrapped lines align after the mark. 공문 stays black; notices/guides take one accent from the house tokens (`shared/design/design.py --use print`). The user's own template comes first: fill or patch their `.hwpx`/`.docx` instead of making a new one; for Word pass `--template`.

## Other skills (never copy their files - point to them)
- `docs.py where` lists what this computer has: **hwp-docs** (kordoc: reads .hwp/.hwpx/.pdf to Markdown, `validate`), the official **docx** / **pdf** skills, 한글, a browser. If `hwp-docs` is installed, use it for reading old `.hwp` text and for `npx kordoc validate out.hwpx` as a second opinion; use the official `docx` skill for tracked changes, comments, complex layouts. We keep the Korean format, the house design and the gate.
- Slides from the same content -> teacher-slides (`"context":"public"` for 기관 보고).

## Files
| file | when |
|---|---|
| `scripts/docs.py` | the one entry point (make, fill, patch, check, preview, text, pdf, where) |
| `scripts/docmodel.py` | spec -> blocks (공문 rules live here) |
| `scripts/hwpx_write.py` · `hwpx_edit.py` · `hwpx_preview.py` | HWPX create (stdlib, from `assets/hwpx/Skeleton.hwpx`, Apache-2.0) · fill/patch in place · our preview |
| `scripts/docx_tools.py` · `pdf_tools.py` · `doc_html.py` | Word · PDF · A4 HTML (fonts embedded) |
| `scripts/doc_check.py` · `doc_look.py` | the gate · PDF page count / fill / smallest text + the one preview picture |
| `references/gongmun-format.md` | rules + sources (official vs practice) |

Design rules (type, spacing, colour, ornaments, the 5-point 「밤티 검사」 gate): [`shared/design/DESIGN-RULES.md`](shared/design/DESIGN-RULES.md)
