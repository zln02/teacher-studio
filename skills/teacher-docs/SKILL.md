---
name: teacher-docs
description: Makes and edits documents - 한글 HWPX 공문·가정통신문·안내문·보고서, Word, PDF (merge, split, form fill, watermark). Use when a teacher or anyone needs an official-format document, a form filled or an existing file fixed without breaking its layout.
license: Apache-2.0
---

# 교사 스튜디오 · 문서 (한글 · 워드 · PDF)

Teacher (no coding) asks for 공문, 가정통신문, 안내문, 계획서·결과 보고서, or to fill / fix a 한글·워드·PDF file. You write a **short JSON spec** (or a list of edits); the tools apply the official format, the house typesetting and the checks.
Respond in the user's language, in plain words (`../teacher-slides/references/teacher-language.md`: never show code or file names). Ask-first rule: `../teacher-studio/references/ask-first.md`. Student info, 생기부, someone else's work or public sharing -> also `teacher-law`.

## Which job
| teacher says | do |
|---|---|
| 공문 / 기안문 / 협조 요청 | `docs.py make --spec x.json --out 공문.hwpx` with `"kind":"gongmun"` |
| 가정통신문 / 동의서 / 회신서 | `"kind":"notice"` (+ `reply` = 회신서 with cut line) |
| 안내문 / 행사 안내 | `"kind":"guide"` (`sections`, `lead` box) |
| 계획서 / 결과 보고서 | `"kind":"report"` (title box, 요약 box, Ⅰ. headings, □ ○ - marks, tables + 자료) |
| 「이 양식 채워 줘」 (.hwpx / .docx / .pdf form) | `docs.py fill FILE --set 성명=… --out new` : `{{키}}`, `[키]`, label cells (성명 → next cell), PDF form fields |
| 「이 한글 파일 고쳐 줘」 | `docs.py patch FILE.hwpx --edits edits.json --out new.hwpx` : `[{"find","replace"}, {"para":n,"text"}, {"after","insert"}]`; exit 2 = some edit not applied -> say which, never claim success |
| 워드로 / .docx | same spec, `--out x.docx` (python-docx on first need; user's `.docx/.dotx` as `--template` keeps their styles) |
| PDF로 | same spec, `--out x.pdf` (our A4 HTML printed by the PC's Chrome/Edge), or 「Ctrl+P → PDF로 저장」 |
| PDF 합치기·나누기·워터마크·표 뽑기 | `docs.py pdf merge|split|watermark|tables|fields|fill|png ...` (pypdf / pdfplumber on first need) |
| 옛 .hwp 파일 | never upload it. `docs.py text x.hwp` prints the plain guide: 한글에서 「다른 이름으로 저장 → HWPX」, or convert with their own 한글 (`docs.py where` says if installed). |

Output: one new file next to the original (never overwrite theirs) + for HWPX a preview page `*.preview.html` (our approximation of 한글: say 「실제 한글 화면과 줄바꿈이 조금 다를 수 있어요」).

## Spec (`docmodel.py` has the full key list)
```json
{"kind":"gongmun", "org":"우리교육지원청", "receiver":"수신자 참조", "title":"... 안내",
 "body":["관련: ...", "다음과 같이 ... 바랍니다.", ["일시: 2026. 12. 3.(목) 14:00∼17:00", "장소: ...", "신청 방법", ["...", "..."]], {"table":{"columns":[..],"rows":[[..]]}}],
 "attachments":["운영 계획 1부", "신청서 1부"], "sender":"우리교육지원청교육장", "receivers":["관내 초등학교장"], "fillins":["담당자 전화"]}
```
A string is an item, a list right after it holds its sub-items; marks are automatic: **1. 가. 1) 가) (1) (가) ① ㉮**, one item alone = no mark, `끝.` added with two spaces (after the last 붙임 line, or under a final table), dates become `2026. 11. 19.`. Dict entries: `{"p": 번호 없는 문단}`, `{"h": 소제목}`, `{"note": "※ …"}`, `{"table": {columns, rows, unit, source, widths, kind:"form"}}`, `{"box": [...], "label": "요약"}`.
Official vs practice and the sources: `references/gongmun-format.md`. Examples: `assets/examples/*.json` (공문, 가정통신문, 안내문, 보고서, 신청서 양식).
**No blanks:** same rule as slides (`[학교명]`, `20XX`, `○○`, `000-0000` FAIL) - fill with stated assumptions or list in `"fillins"`; 「양식으로」 -> `"template_blanks": true`.

## Gate (`doc_check.py`, runs after every make; also `docs.py check FILE`)
blanks · privacy (주민번호 FAIL; 휴대전화·전자우편·「성명: 홍길동」·학년반번호 WARN) · 공문 format (수신/제목, mark order, single-item mark, `끝` two spaces, `붙임` no colon) · dates `2026. 11. 19.` / 24-hour time · simple 띄어쓰기 (WARN, never auto-fix) · file reopens (HWPX: mimetype first+stored, XML, every charPr/paraPr/borderFill reference) · fonts (common Korean fonts; PDF fonts embedded). FAIL -> fix and rebuild; WARN -> tell the teacher in one line each.

## Design (automatic)
A4, 20/20/20/15 mm, 함초롬바탕 12.5 pt body (house default; 한글 always has it), title 20 pt, headings 14 pt, tables with a light header fill and right-aligned numbers, hanging indents so wrapped lines align after the mark. 공문 stays black; notices/guides take one accent from the house tokens (`shared/design/design.py --use print`). The user's own template comes first: fill or patch their `.hwpx`/`.docx` instead of making a new one; for Word pass `--template`.

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
| `scripts/doc_check.py` | the gate |
| `references/gongmun-format.md` | rules + sources (official vs practice) |
