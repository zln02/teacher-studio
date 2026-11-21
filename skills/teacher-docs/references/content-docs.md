# Document content — 공문 · 보고서 · 가정통신문 at the level a 교감 · 장학사 signs

`gongmun-format.md` covers form (항목 기호, 끝, 붙임, 날짜). This file covers what the document says. The same rules drive `public` decks in `teacher-slides`. Wording: `../teacher-studio/references/content-writing.md`. Derive the structure from this document's purpose; do not reuse the paragraph order of a previous output.

## Steps
1. **Classify the document by what the reader must do.**
   | reader must | kind | lead with |
   |---|---|---|
   | approve / decide | 내부결재 · 계획서 · 품의 | what is to be approved, cost, date |
   | act and reply | 협조 · 제출 요청 공문 | what to submit, to whom, by when, in what form |
   | know | 알림 · 결과 보고 | the result or the fact, then detail |
   | (parents) act or consent | 가정통신문 | what the family does, by when, how |
   If you cannot name the reader's action, ask the teacher one question before drafting.
2. **Conclusion first (두괄식).** The title names the matter and the action (「… 제출」「… 안내」「… 결과 보고」). The first item states the purpose and, for 공문, the basis (「관련: 〈문서명·번호〉(날짜)」) when one exists. Background comes after the request, and only as much as the decision needs.
3. **Complete the action facts** (a reviewer checks these first): 대상 · 일시(요일) · 장소 · 내용 · 방법 · 기한 · 제출처 · 준비물/비용 · 문의(담당자 · 전화). A fact the user gave is used as given. Missing fact → a plausible example value in the body and the tables (a real date with its computed weekday, a place, a round amount, a role such as 「담임 교사」), added to `"fillins"`; an underline blank or check box only inside the reply slip or form the family writes on. One small line at the foot of the body says some dates, places and amounts are examples (the builder adds it when `"fillins"` is not empty). Never 「확인 필요」, a bracket slot or a 「교사 초안」 mark on the page (CONTENT-RULES, Unknowns).
   - **Follow the reader's action to the end**, and add only what this case needs: what the cost includes and excludes, how participants are chosen and what happens to those not chosen (정원 초과 · 대기), how a change or cancellation is announced, what to do if the deadline is missed. A reply link or form must open for someone without a school account; say what to do if it does not.
4. **Numbers carry 단위 · 기준일 · 출처.**
   - Statistic: 「〈값〉〈단위〉(〈기준일〉 기준, 〈출처〉)」. Own counts: 「우리 학교 자체 집계(2026. 11.)」.
   - Comparison names the base: 전년 대비 · 계획 대비 · 전체 〈n〉명 중.
   - % and %p answer different questions: 20% → 25% is a 5%p rise and a 25% increase over the base. Say which one you mean; a rate shows its numerator and denominator at least once.
   - Tables: totals recomputed from the raw counts; 계 = sum of rows for counts. Rounded percentages may sum to 99.9 or 100.1 and 복수 응답 can exceed 100: add a 주 line instead of adjusting a figure. The same number is identical in body, table and 붙임.
   - 예산: 산출 근거 (단가 × 수량 × 횟수 = 금액), 합계 일치, 금액 표기는 `gongmun-format.md`.
5. **Write 개조식 properly** (공문 · 보고서 body).
   - One item = one fact or one request, one line where possible, at most two.
   - Endings: noun or 「~함 · ~임 · ~예정 · ~필요」; a request to another office ends in a polite sentence (「~하여 주시기 바랍니다」). Do not mix endings inside one level.
   - Items at one level are parallel in grammar and weight; a level with one item gets no mark.
   - 개조식 is not telegraphic: keep 조사 that carry meaning (「~에게」「~까지」), and never drop the subject when two readings are possible.
   - Keep the depth shallow (about 3 levels) because readers lose the parent item beyond that. If a fourth level appears, ask what the content is: items compared on the same criteria → a table; a condition with its exceptions or a procedure → keep the hierarchy or number the steps, do not force a table. An agency's fixed form (지정 서식) is never restructured.
6. **Set the tone by reader.**
   | reader | tone and content |
   |---|---|
   | 상급 기관 · 타 기관 | formal, neutral, facts and requests only; no adjectives of self-praise; cite the basis |
   | 교내 (내부결재) | shortest form; decision, cost, schedule, 담당 |
   | 학부모 | 합쇼체, respectful and warm in one greeting sentence, then facts; everyday words in place of 행정 용어 (「실시」→「합니다」, 「익일」→「다음 날」, 「제출 요망」→「내 주세요」); what the family must do is findable in 5 seconds (box or first numbered item) |
   | 학생 | direct, short, no threat tone; what to bring/do and when |
   For parents: say the reason for a rule or a cost in one line, give a way to ask questions, and do not assume family form (「부모님」→「보호자」 where the school uses it), language level or device ownership.
7. **Draw the legal and privacy lines.** Detect, then route to `../teacher-law`; do not write law from memory.
   - 회신서 · 신청서 collecting student or family data → collect the minimum; a consent section is a legal text → `teacher-law`.
   - Named students, 사진, 성적, 건강 · 상담 · 징계 facts → not in a document that leaves the 담당자; use counts or 「학생 A」. Removing the name is not enough: 학년 · 반 · 행사 · 날짜 · 사진 배경 together can point to one student. Check 공개 목적 · 공개 범위 · who could recognise the person; when in doubt, generalise further or leave it out, and ask `teacher-law` for the basis (동의, 법정대리인 동의 for younger students).
   - Small counts in a table can be worked out from totals (전체 and one group shown → the hidden group is known). Hide or merge so that subtraction does not reveal them.
   - 공문 공개 구분, 수익자 부담 경비, 안전 · 보험, 외부 강사 · 업체 names → write the usual example value (a generic name such as 「시립 실내수영장」「전문 강사」, a round amount), add it to `"fillins"`, and ask the teacher in the final message to check it against the school's rule.
   - Third-party images or text in a 통신문 → basis and credit, or remove.
8. **Review as the 결재권자 would** (list below), then run `doc_check.py`.

## What a 교감 · 장학사 flags first
- Title does not match the body, or does not say what is wanted.
- No basis (관련 문서) for a request that needs one; or a basis cited with the wrong date/number.
- Date and weekday disagree; period end before start; deadline already past or on a holiday. **Compute weekdays.**
- Leftovers from last year's file: old 연도 · 학년도 · 학교명 · 담당자 · 전화.
- Sums that do not add; a count in the text that differs from the table; unit missing.
- 수신자 wrong or too broad; 붙임 count differs from the list; 「끝.」 misplaced.
- One term written three ways (방과후/방과 후, 학부모/보호자, 신청서/참가 신청서). Pick one.
- Requests without 기한 · 제출 방법 · 제출처; contact line missing.
- Personal data that need not be there; a 회신서 asking more than the purpose needs.
- Self-praise, vague claims (「큰 성과」「적극 추진」) without a number; filler background before the point.
- Sentences a parent would have to read twice; 한자어 · 외래어 habit words.
- A decision or expense that needs a prior 결재 or 학교운영위원회 step, written as already decided → word it as planned (「~할 예정」) and name the step in the final message.
- State of the document unclear: draft before 결재 sent as if final; 수신 · 공개 범위 wider than intended; 본문 and 붙임 saying different things (date, amount, count).
- Cost with no statement of what it covers; selection with no criteria; no word on change or cancellation where one is likely.

## 전문가 점검표
- [ ] Reader's required action is stated in the title or first item.
- [ ] Action facts complete: 대상 · 일시(요일) · 장소 · 방법 · 기한 · 제출처 · 비용 · 문의.
- [ ] Every number has 단위; statistics have 기준일 · 출처; comparisons name the base; totals recomputed.
- [ ] Every weekday computed; periods and deadlines consistent; 학년도 and names current.
- [ ] 개조식: one fact per item, parallel endings, ≤ 3 levels, no ambiguity from dropped 조사.
- [ ] Tone matches the reader; a parent finds what to do in 5 seconds; no 행정 용어 in a 가정통신문.
- [ ] One term per concept through the whole document and its 붙임.
- [ ] No unnecessary personal data; legal items routed to `teacher-law`; what could not be confirmed is named in the final message, not printed on the page.
- [ ] No invented basis, document number, statistic or rule.
- [ ] Reading goals met or knowingly exceeded: a 가정통신문 aims at one A4 (reply slip may be the lower part) and a 보고서 요약 at about 5 lines with the key numbers. These are house goals, not rules: a required condition or consent text is never dropped to fit, and the school's or 교육청's own form and rules come first.
- [ ] Unknowns follow the one rule (CONTENT-RULES, Unknowns): 기한 · 대상 · 비용 · 장소 the user did not give are example values listed in `"fillins"`; blanks only inside the 회신서 · 신청서 · 서명란; one example note at the foot; no 「확인 필요」, slot or 「교사 초안」 mark on the page. A 가정통신문 the family must answer keeps its reply slip.
- [ ] The reader's path was walked to the end (cost coverage, selection, change/cancel, link opens without a school account) and 본문 = 붙임.
- [ ] No person can be recognised from combined details; no small count recoverable from totals.
- [ ] `content-writing.md` tell check passed.

## Sources (checked 2026-11-20)
- Current articles, read today with `teacher-law/scripts/law_fetch.py`:
  - 행정업무의 운영 및 혁신에 관한 규정 시행규칙 (행정안전부령 제408호, 시행 2023. 6. 28.) 제2조제1항: 항목 기호 1., 가., 1), 가), (1), (가), ①, ㉮ and optional □ ○ - ㆍ; 제2조제2항: 금액 표기. 제4조제4항: 붙임; 제4조제5항: 「끝」 표시 and 「이하 빈칸」. https://www.law.go.kr/법령/행정업무의운영및혁신에관한규정시행규칙/제2조 · https://www.law.go.kr/법령/행정업무의운영및혁신에관한규정시행규칙/제4조
  - 행정업무의 운영 및 혁신에 관한 규정 (시행 2026. 10. 2.) 제7조: 어문규범에 맞는 한글, 간결 · 명확하고 이해하기 쉽게, 날짜는 숫자와 온점, 시각은 24시각제와 쌍점, A4. https://www.law.go.kr/법령/행정업무의운영및혁신에관한규정/제7조
  - Note: `gongmun-format.md` cites the 붙임 · 끝 rule as 제4조제5항 and the date rule as 「규정 제7조」; both match. Its 편람 page numbers refer to the 2011 edition.
- 행정안전부 「2025 행정업무운영 편람」 (정보공개제도과, 게시 2026. 1. 2., PDF dated 2025. 12. 17.): https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000012&nttId=122878 . The post and files were confirmed; the PDF's contents were **not read today**, so page-level citations to it are not given here.
- Plain language duty: 국어기본법 제14조제1항 (시행 2026. 10. 29., read today). 국립국어원 「쉬운 공문서 쓰기 길잡이」 https://www.korean.go.kr/front/etcData/etcDataView.do?etc_seq=700&mn_id=&pageIndex=1 (contents not read today).
- The reviewer list, the parent-tone rules, 「about 3 levels」, 「one A4」 and 「요약 5 lines」 are school practice or house goals, not regulation. Say 「관행」 when asked whether they are mandatory, and check the school's and 교육청's own rules and fixed forms.
