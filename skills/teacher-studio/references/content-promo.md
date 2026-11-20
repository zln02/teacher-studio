# Promotion content — poster, 홍보 PPT, SNS card, short video

What a 홍보 담당 decides before any design. Used by `teacher-slides` (`promo`), `teacher-motion`, and SNS/poster outputs. Wording: `content-writing.md`. Principles and choices only; the message is derived from this event and this audience, never from a previous poster.

## Steps
1. **Name the audience and the one action.** 「〈누가〉 이것을 보고 〈무엇을 한다〉.」 (신청 · 참석 · 방문 · 저장 · 공유 · 투표). Two audiences with different actions (학생 모집 + 학부모 안내) → two pieces, not one.
2. **Find the benefit from the audience's side.** Ask 「그래서 나한테 뭐가 좋은데?」 until the answer is concrete (something they get, do, avoid or become). The organiser's name, 회차, 주최 are facts, not the benefit.
   | if the audience is | lead with |
   |---|---|
   | students | what they will do or make, with whom; proof it is fun or useful (a specific activity, not 「재미있는」) |
   | parents | what the child gains, safety · cost · time, how to ask |
   | staff / officials | the result, the number, the fit with a policy or plan |
   | community / public | what is open to them, when, free or not |
3. **Write the one core message** as a headline: benefit or invitation in ≤ 15자 (hard limit 24자), one idea, a verb if possible. Test: shown for 3 seconds at walking speed, does the reader know what it is and whether it is for them?
   - If the headline works for any event by swapping the noun (「함께해요, 〈행사명〉!」), it is not a message yet.
4. **Limit the hierarchy to 3 levels.**
   - L1: the headline (one).
   - L2: the facts needed to decide: 언제 · 어디서 · 누구 대상 · 얼마 (2-3 items).
   - L3: how to act and details: 신청 방법 · 마감 · 문의 · 주최.
   Anything that is not L1-L3 is cut or moved behind the QR/link. Two things competing for L1 means step 1 is unfinished.
5. **Give one call to action** with everything needed to do it now: the verb (「〈날짜〉까지 QR로 신청」), the channel (QR + short readable address or place), the deadline. One CTA per piece; a second action goes to the linked page.
   - QR alone is not enough: add what it opens and a fallback (교무실, 전화, 링크 글자).
   - Scarcity or deadline only if true (정원, 선착순).
6. **Fit the medium.**
   | medium | content rule |
   |---|---|
   | wall poster | readable at 3-5 m: L1 and date/place only at distance; L3 at arm's length |
   | 홍보 PPT | one message per slide; story = hook → what it is → proof (past photo, number, one quote with permission) → how to join → CTA |
   | SNS card / 카드뉴스 | first card is the whole message; each card one fact; last card the CTA; the caption repeats date · place · link as text |
   | short video | message in the first 3 seconds; works without sound (text on screen); CTA held ≥ 3 seconds at the end |
   | 가정통신문-style notice | not promotion: use `teacher-docs/references/content-docs.md` |
7. **Proof over adjectives.** Replace 「알찬 · 다채로운 · 특별한」 with one countable or visible fact (how many booths, which activity, who comes, what you take home). Past results need a source or the user's own data; no invented testimonials or numbers.
8. **Accessibility is part of the content.**
   - Essential facts are real text, never only inside a picture; every image that carries meaning has alt text or a caption (SNS: 대체 텍스트 칸).
   - Text contrast ≥ 4.5:1 (large text ≥ 3:1); meaning never by colour alone; no text over a busy photo without a solid panel.
   - Dates with 요일, time in a form everyone reads (오후 3시; add 15:00 in official notices), place with 층/호.
   - Plain words; expand abbreviations once. Video: captions; no flashing.
9. **Clear the rights of every image, font, music and face.** Detect and route to `../teacher-law` (it reads the current law).
   - Safe by default: made in this project, the user's own photos (people in them agreed), CC0, 공공누리 with the type's conditions met (출처표시 is required for all four types; some types forbid 상업적 이용 or 변경).
   - Needs a basis before use: web-search images, 캐릭터 · 로고 · 연예인, stock with a watermark, music, fonts with a use limit, AI images imitating a named artist or character.
   - Students' faces or names in public material → guardian consent matter → `teacher-law`; default to backs, hands, crowds, illustrations.
   - Keep a credit line: 〈작품/사진〉 · 〈만든이/기관〉 · 〈라이선스〉 · 〈받은 날짜〉.
10. **Verify the facts last**: date ↔ weekday (compute), time, place, 대상, cost, deadline before the event, link/QR opens the right page, contact current. One wrong date voids the piece.

## 전문가 점검표
- [ ] One audience, one action, one message; the headline states a benefit or a clear invitation in ≤ 15자 (≤ 24자).
- [ ] 3-second test passed: what it is and who it is for.
- [ ] ≤ 3 hierarchy levels; nothing competes with L1.
- [ ] Decision facts complete and identical everywhere: 언제(요일) · 어디서 · 누구 · 얼마 · 어떻게 · 마감 · 문의.
- [ ] One CTA with verb + channel + deadline + fallback to the QR.
- [ ] No empty adjectives; each claim has a visible or countable proof; nothing invented.
- [ ] Essential info is text; contrast ≥ 4.5:1; not colour-only; alt text / captions present.
- [ ] Every image · font · music · face has a basis and a credit line; open questions sent to `teacher-law`.
- [ ] Weekday computed; deadline precedes the event; link/QR target checked.
- [ ] The piece does not reuse the last piece's headline pattern or layout order.

## Sources (checked 2026-11-20)
- Contrast 4.5:1 (normal text) and 3:1 (large text): W3C WCAG 2.2 SC 1.4.3 (Recommendation 2023-10-05) https://www.w3.org/TR/2023/REC-WCAG22-20231005/ . 한국형 웹 콘텐츠 접근성 지침 2.2 (2022. 12. 28.) is listed by 서울시 https://news.seoul.go.kr/gov/archives/47485 ; its contrast value was not re-read today (**unverified**, expected to match).
- 공공누리 4 types, 출처표시 common to all: 문화체육관광부 https://www.mcst.go.kr/kor/s_open/kogl/koglType.jsp · 한국저작권위원회 https://www.copyright.or.kr/gov/nuri/guide/index.do . 공유마당 https://gongu.copyright.or.kr
- Copyright and portrait questions are answered by `teacher-law` from the current law, not from this page.
- Headline length, 3-level hierarchy and the 3-second test are practice heuristics.
