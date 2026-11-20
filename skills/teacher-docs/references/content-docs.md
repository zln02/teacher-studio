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
3. **Complete the action facts** (a reviewer checks these first): 대상 · 일시(요일) · 장소 · 내용 · 방법 · 기한 · 제출처 · 준비물/비용 · 문의(담당자 · 전화). Missing fact → ask or mark 「〈확인 필요〉」 visibly; never fill with a plausible guess.
4. **Numbers carry 단위 · 기준일 · 출처.**
   - Statistic: 「〈값〉〈단위〉(〈기준일〉 기준, 〈출처〉)」. Own counts: 「우리 학교 자체 집계(2026. 11.)」.
   - Comparison names the base: 전년 대비 · 계획 대비 · 전체 〈n〉명 중.
   - % and %p are different; a rate shows its numerator and denominator at least once.
   - Tables: totals recomputed; 계 = sum of rows; the same number is identical in body, table and 붙임.
   - 예산: 산출 근거 (단가 × 수량 × 횟수 = 금액), 합계 일치, 금액 표기는 `gongmun-format.md`.
5. **Write 개조식 properly** (공문 · 보고서 body).
   - One item = one fact or one request, one line where possible, at most two.
   - Endings: noun or 「~함 · ~임 · ~예정 · ~필요」; a request to another office ends in a polite sentence (「~하여 주시기 바랍니다」). Do not mix endings inside one level.
   - Items at one level are parallel in grammar and weight; a level with one item gets no mark.
   - 개조식 is not telegraphic: keep 조사 that carry meaning (「~에게」「~까지」), and never drop the subject when two readings are possible.
   - Depth ≤ 3 levels. If a fourth is needed, the content wants a table.
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
   - Named students, 사진, 성적, 건강 · 상담 · 징계 facts → not in a document that leaves the 담당자; use counts or 「학생 A」.
   - 공문 공개 구분, 수익자 부담 경비, 안전 · 보험, 외부 강사 · 업체 names → flag for the teacher to confirm with the school's rule; state it as 「확인 필요」, not as fact.
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
- A decision or expense that needs a prior 결재 or 학교운영위원회 step, written as already decided → mark 「확인 필요」.

## 전문가 점검표
- [ ] Reader's required action is stated in the title or first item.
- [ ] Action facts complete: 대상 · 일시(요일) · 장소 · 방법 · 기한 · 제출처 · 비용 · 문의.
- [ ] Every number has 단위; statistics have 기준일 · 출처; comparisons name the base; totals recomputed.
- [ ] Every weekday computed; periods and deadlines consistent; 학년도 and names current.
- [ ] 개조식: one fact per item, parallel endings, ≤ 3 levels, no ambiguity from dropped 조사.
- [ ] Tone matches the reader; a parent finds what to do in 5 seconds; no 행정 용어 in a 가정통신문.
- [ ] One term per concept through the whole document and its 붙임.
- [ ] No unnecessary personal data; legal items routed to `teacher-law` or marked 「확인 필요」.
- [ ] No invented basis, document number, statistic or rule.
- [ ] 가정통신문 fits one A4 (reply slip may be the lower part); 보고서 요약 ≤ 5 lines with the key numbers.
- [ ] `content-writing.md` tell check passed.

## Sources (checked 2026-11-20)
- Form rules and their sources (행정업무의 운영 및 혁신에 관한 규정 · 시행규칙, 경기도교육청 「한 곳에 정리한 공문서 작성법」 2023. 12. 1., 행정안전부 편람): see `gongmun-format.md`. Search today confirmed 시행규칙 제2조 is 「공문서 작성의 방법」 on the current text; the 항목 기호 · 끝 표시 wording was seen only on an older copy → treat `gongmun-format.md`'s citations as the reference and re-check on law.go.kr (https://www.law.go.kr/LSW/lsInfoP.do?lsId=007319) when quoting an article number.
- 행정업무운영 편람: a 2020 edition is reported (https://www.hangyo.com/news/article.html?no=80528); the newest edition's text was not found online (**unverified** which edition is current).
- Plain language duty: 국어기본법 제14조 (law.go.kr; wording via `teacher-law`). 국립국어원 「쉬운 공문서 쓰기 길잡이」 (contents not read today).
- The reviewer list and the parent-tone rules are school practice, not regulation. Say 「관행」 when asked whether they are mandatory.
