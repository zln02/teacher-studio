# 공문·가정통신문·안내문 형식 (what docmodel.py applies, and where it comes from)

Checked 2026-11-19. **Official** = written in the regulation or the 행정안전부 편람. **Practice** = common in schools, no official text found. Tell the teacher which one it is when they ask 「꼭 이렇게 해야 해요?」.

## 공문 (기안문) - official
| rule | what we do | source |
|---|---|---|
| regulation name | 「행정업무의 운영 및 혁신에 관한 규정」 및 시행규칙 (행정안전부령 제408호, 시행 2023. 6. 28.; 제목 개정 2023. 6. 27.) | law.go.kr: https://www.law.go.kr/법령/행정업무의운영및혁신에관한규정시행규칙 · 경기도교육청 「한 곳에 정리한 공문서 작성법」(2023. 12. 1.) https://www.goe.go.kr/resource/old/BBSMSTR_000000000028/BBS_202410150153084250.pdf |
| item marks | 1. → 가. → 1) → 가) → (1) → (가) → ① → ㉮ ; beyond 하. continue 거. 너. … | 시행규칙 제2조제1항; 편람(2011, 5판) 제2장 제1절 https://cced.suwon.ac.kr/content/pds/down.asp?fileid=593 ; 경기도교육청 2023 |
| indent | first level at the left margin; each lower level 2타 (= one Hangul character) further in; one 타 between mark and text | 행정안전부 보도 2017. 10. 31. (본문 왼쪽 기본선 시작, 2017. 11. 1. 시행) https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId=60226 ; 경기도교육청 2023 |
| single item | a group with only one item gets no mark | 편람 2011; 경기도교육청 2023 |
| 끝 | two spaces after the last body text: `…바랍니다.  끝.` ; with 붙임, after the last 붙임 line ; body ending with a table → `끝.` on the line under the table (table filled to the end) or `이하 빈칸` in the next cell | 시행규칙 제4조제5항; 편람 2011 pp.44-45 |
| 붙임 | `붙임  1. 계획서 1부.` / `2. 서류 1부.  끝.` ; no colon ; one attachment → no number | 편람 2011; 경기도교육청 2023 |
| date / time | `2026. 11. 19.` (온점, no leading 0, final dot), weekday `2026. 11. 19.(목)`, period `11. 3.∼11. 14.` ; time 24-hour `15:20` | 규정 제7조; 경기도교육청 2023 pp.8-9 |
| money | `금113,560원(금일십일만삼천오백육십원)` | 시행규칙 제2조제2항 |
| structure | 두문 (기관명, 수신, (경유)) · 본문 (제목, 내용, 붙임) · 결문 (발신명의, 기안자·검토자·결재권자, 시행·접수 번호, 우편번호·주소·홈페이지, 전화·전송·전자우편·공개구분) | 시행규칙 제4조, 별지 제1호서식; 편람 2011 pp.39-48 |
| 수신 | `내부결재` when there is no receiver (then no 발신명의) ; many receivers → `수신자 참조` and a `수신자 …` line after 발신명의 | 편람 2011 pp.42-43 |
| paper | A4 210 × 297 mm | 규정 제7조제6항 |

**Not official (house defaults, say so):** margins 20/20/20/15 mm, body 12.5 pt 함초롬바탕, line spacing 160%. No official 기안문 margin or font was found (the 편람 values are for 민원서식 only). 결문's 결재란·시행번호 are filled by the 업무관리시스템 (K-에듀파인); our file is the draft body, so the 결문 block is printed only when `footer` is given.

## 가정통신문 / 안내문 - practice
No 교육청 guideline was found. We follow common school practice plus the official plain-language rules (쉬운 말, 1건 1매, 경어 `~하시기 바랍니다`; 국어기본법 제14조, quoted in 경기도교육청 2023 pp.3, 11-14): school name + 호수, title, greeting, numbered body (same marks as 공문), date, 「○○학교장」, optional 회신서 with a cut line.
- 회신서 asks for the minimum. Fields like 학생 이름·학년·반·번호·연락처 are personal data: the checker WARNs; if they are really needed, add them on the teacher's request and point to `teacher-law` (개인정보 수집·이용 동의).

## 보고서 - practice
Title box, date/부서 line, 요약 box, Ⅰ. headings, □ ○ - ㆍ marks, tables with `자료:` line. The □ → ○ → - order and the 요약 box are practice, not law (서울시 distributes its own templates internally: https://opengov.seoul.go.kr/sanction/view/?nid=11678326). 개조식 is recommended officially (경기도교육청 2023 p.13: 「문장은 짧게 끊어서 개조식으로」).

## 띄어쓰기 checks (WARN only, never auto-fixed)
「한글 맞춤법」 제41-45항 (조사는 붙여, 의존명사·단위명사는 띄어, 수는 만 단위로; https://ko.wikisource.org/wiki/대한민국_한글_맞춤법(제88-1호) - current text is the 문화체육관광부 2017 edition, same articles) and the 경기도교육청 2023 list of frequent 공문 mistakes (p.10): `할수 → 할 수`, `하는것이 → 하는 것이`, `그 동안 → 그동안`, `방과후 → 방과 후`, `50%이상 → 50% 이상`, `(금) 까지 → (금)까지`, `두가지 → 두 가지` … Numbers + units (`50명`) are allowed both ways, so they are not flagged.
