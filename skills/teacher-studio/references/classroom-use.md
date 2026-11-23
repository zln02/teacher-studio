# 활용·전달 단계 (use + delivery step) - how the result will be used, on THIS computer

Runs at stage 6 (배포) of `pipeline.md`, after the file passed its checker. Name it 「수업 활용」 only for teachers; for everyone else it is 「활용·전달」. Reply in the user's language (Korean default), plain words.

## 1. Audience (infer; never ask 「선생님이세요?」)
- Teacher signals: 수업, 학생, 학급, 반, 교과/과목, 학년, 가정통신문, 학부모, 출구 티켓, or `prefs.py show` has a school level.
- Otherwise general: office worker, club, family, shop owner, creator. Unsure -> general wording (it reads fine for teachers too).

## 2. The closing menu (ALWAYS, even after 「알아서」; owner rule 2026-11-23)
First make the recommended way (the use the request said, else by result: deck/game/tool -> TV·화면, 안내문·가정통신문 -> 단톡방·메신저 PDF, data -> 고쳐 쓸 파일; 「알아서」 -> `--use auto`). Then end with the menu `deliver.py` prints (`delivery_menu`): 「✅ 다 만들었어요! 어떻게 받으시겠어요? (추천: …)」 ① TV·화면 ② 단톡방·메신저 ③ 학생 태블릿 ④ 인쇄·PDF ⑤ 고쳐 쓸 파일(한글·PPT) — the recommended one marked 「이미 만들어 뒀어요」. A number -> make that one (`--use tv|share|tablet|print|archive`); ②③ go through the privacy check first. The longer lists below stay for when the user asks for more ways.
- Teacher: 「어떻게 쓰실 건가요? (추천: 교실 TV로 띄우기)」 1 교실 TV·프로젝터 · 2 학생 태블릿·폰에 나눠 주기 · 3 인쇄 · 4 학급 홈페이지·패들렛·클래스룸에 올리기 · 5 가정에 보내기 · 6 다음에 고칠 원본으로 보관
- General: 「어떻게 쓰실 건가요? (추천: 화면에 띄우기)」 1 회의실 화면·발표 · 2 카톡·메일로 공유 · 3 인쇄 · 4 SNS·블로그·홈페이지에 올리기 · 5 팀 공유 폴더(드라이브) · 6 보관·나중에 수정
- 「네」 = the recommended one. 「알아서」 = default without asking: TV/screen + a print PDF (`--use auto`).
- Recommend by result: deck/game/tool -> TV·screen; 가정통신문·안내문 -> 가정에 보내기 / 카톡 공유; worksheet -> 인쇄; data report -> 보관 (+ screen).

## 3. Use -> files (`scripts/deliver.py FILE --use <use>` makes them with the existing weapons)
| use (teacher / general) | Gives | How it is made |
|---|---|---|
| `tv` / `screen` | the offline single HTML (big-screen mode), F11 full screen, Win+P 복제; PPTX -> F5 | source kept; docx/hwpx -> PDF |
| `tablet` | the HTML or PDF + QR for a link the USER gives + phone-layout check | `--url` -> offline QR; never upload |
| `print` (both) | PDF, A4, 100% scale | HTML -> PDF via teacher-docs `pdf_tools.html_to_pdf`; office -> LibreOffice if present, else 「PDF로 저장」 how-to |
| `lms` / `sns`, `drive` | the right file type + short upload how-to (클래스룸 자료 → 파일, 패들렛 + → 업로드) | PDF next to HTML; CSV <-> XLSX; HTML tables -> CSV |
| `home` / `share` | PDF (HWPX for 학교 양식 결재), privacy check FIRST | PDF |
| `archive` (both) | editable originals: PPTX/DOCX/HWPX/XLSX + the spec | deck HTML + `--spec deck.json` -> PPTX (teacher-slides `deck.py --pptx`); CSV -> XLSX |
Data/tables -> CSV/XLSX. School forms -> HWPX (`teacher-docs`). Editable -> PPTX/DOCX. A new HWPX/DOCX is made by its own skill, not by deliver.

## 4. Fit this computer
- `scripts/env_programs.py` (read-only, cached 7 days in `~/.teacher-studio/env.json` "programs"): 한글, PowerPoint/Word/Excel, LibreOffice, Chrome/Edge/Whale, PDF reader, Python, Node. deliver prints for each file which program opens it here.
- Prefer formats that open on this PC (no PowerPoint but 한글 -> PDF or HWPX; no Office -> PDF + HTML).
- Missing or outdated program -> OFFER, with the size, and wait for 「네」: small helpers via `shared/tools/ensure.py <name> --yes` (openpyxl ~3MB, python-pptx ~6MB), LibreOffice ~350MB (`ensure.py libreoffice --yes`), others as one plain instruction (where to get it). Never install silently; never claim a size you do not know (say 「크기는 설치 화면에 나와요」).

## 5. Ideas (2-3 short lines, plain words, tailored to the result and grade/audience)
- Teacher: 「도입 5분 퀴즈로」「모둠 대항전」「출구 티켓」 (초등: 몸으로 OX; 고등: 이유 한 줄 쓰기).
- General: 「회의 시작 5분 요약용」「모임 공지 카드로」「행사 마지막 경품 퀴즈로」.

## 6. Privacy (always)
- You never upload, post or send anything. The user does it; you hand over files and how-tos.
- Before anything goes outward (tablet, lms/sns/drive, home/share): one reminder - real names/photos/grades (teacher) or others' contacts/faces/customer data (general), others' works and logos. Student data found -> stop and route Decision 1.

## Final message (with `pipeline.md` final checkpoint)
Path(s) · how to open them on this PC · check result · the 꾸러미 lines from deliver (files, how to use, 2-3 ideas, privacy) · the one use question if not yet answered. Never more than one question.
