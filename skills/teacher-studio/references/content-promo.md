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
3. **Write the one core message** as a headline: benefit or invitation, one idea, a verb if possible. The real test is a reading test for the medium: seen for about 3 seconds at walking speed (poster), or in one scroll stop (SNS), does the reader know what it is and whether it is for them? Short headlines pass that test more often, so start near 15자 and treat about 24자 as the point to re-check on the real size; a longer headline that passes the test is fine, a short one that fails is not.
   - If the headline works for any event by swapping the noun (「함께해요, 〈행사명〉!」), it is not a message yet.
4. **Limit the hierarchy to 3 levels.**
   - L1: the headline (one).
   - L2: the facts needed to decide: 언제 · 어디서 · 누구 대상 · 얼마 (2-3 items).
   - L3: how to act and details: 신청 방법 · 마감 · 문의 · 주최.
   Background, history and greetings beyond L1-L3 are cut or moved behind the QR/link. Two things competing for L1 means step 1 is unfinished.
   - **Never move a deciding condition behind the link.** What makes someone eligible or changes their decision stays on the piece itself: 참가 자격 · 비용과 포함 내용 · 정원과 선정 방식 · 보호자 동행 · 준비물 · 안전 조건. Three levels is a limit on emphasis, not on necessary facts; put them at L2/L3 in plain small text.
   - Add when likely: what happens when 정원 is exceeded, and how a change or cancellation is announced.
5. **Give one call to action** with everything needed to do it now: the verb (「〈날짜〉까지 QR로 신청」), the channel (QR + short readable address or place), the deadline. One CTA per piece; a second action goes to the linked page.
   - QR alone is not enough: add what it opens and a fallback (교무실, 전화, 링크 글자).
   - Open the link as an outsider would (logged out, on a phone, without a school account). A form that asks for a school login shuts out parents and the community.
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
   - Essential facts are real text, never only inside a picture; every image that carries meaning has alt text or a caption (SNS: 대체 텍스트 칸). A poster image posted online needs the same facts repeated as text in the post.
   - Try it as a screen-reader user would: read only the text and alt text, in the order the file gives them. Is the order sensible (headline → when/where → how to apply) and is every deciding fact there? A QR code needs its address as text.
   - Text contrast ≥ 4.5:1. Large text may go down to 3:1, where large means about 18pt (24px) or more, or 14pt (about 18.7px) bold or more. Logos and pure decoration are exempt. Meaning never by colour alone; no text over a busy photo without a solid panel.
   - Dates with 요일, time in a form everyone reads (오후 3시; add 15:00 in official notices), place with 층/호.
   - Plain words; expand abbreviations once. Video: captions that match the speech and name meaningful sounds; what is only shown is also said or written; moving content can be paused; no flashing (`teacher-motion/references/content-motion.md`).
   - These are content checks, not a legal audit. Whether a school site or service has a legal accessibility duty → `../teacher-law`.
9. **Clear the rights of every image, font, music and face.** Detect and route to `../teacher-law` (it reads the current law).
   - Usually safe: made in this project, the user's own photos (people in them agreed), CC0, 공공누리 with the type's conditions met. Read the mark on each work: **제0유형** = free use, no 출처표시 condition (저작인격권 still respected); **제1-4유형** all require 출처표시, and 2 · 4 forbid 상업적 이용, 3 · 4 forbid 변경 (cropping, recolouring and compositing count as 변경); **AI유형** only covers use as AI 학습용 데이터 and is shown together with a 제1-4유형 mark, so for a poster follow that accompanying type.
   - Even with a free licence, the people, trademarks and private details inside a photo are separate questions.
   - Material that was fine inside a lesson is not thereby fine in public promotion: a new use needs its own basis.
   - Needs a basis before use: web-search images, 캐릭터 · 로고 · 연예인, stock with a watermark, music, fonts with a use limit, AI images imitating a named artist or character.
   - Students' faces or names in public material → a consent matter (법정대리인 동의 for younger students) → `teacher-law`. Prefer hands, objects, crowds from afar, illustrations. A back view is not automatically anonymous: 교복 · 이름표 · 반 · 행사명 · 배경 can identify a student, so check 공개 범위 and who could recognise them.
   - Keep one record per asset: 원본 링크 · 만든이/기관 · 이용 조건 · 변경 여부(자르기 · 합성 · 번역) · 게시할 곳 · 확인한 날짜.
10. **Verify the facts last**: date ↔ weekday (compute), time, place, 대상, cost, deadline before the event, link/QR opens the right page, contact current. One wrong date voids the piece.

## 전문가 점검표
- [ ] One audience, one action, one message; the headline states a benefit or a clear invitation.
- [ ] Reading test passed on the real medium and size: what it is and who it is for (headline length was a means to this, not the criterion).
- [ ] ≤ 3 levels of emphasis; nothing competes with L1; every deciding condition (자격 · 비용 · 정원 · 동행 · 안전) is on the piece, not only behind the link.
- [ ] No deciding fact is still 「확인 필요」 (date, place, cost, eligibility, deadline); otherwise the piece is a 「교사 초안」 and is not posted.
- [ ] Decision facts complete and identical everywhere: 언제(요일) · 어디서 · 누구 · 얼마 · 어떻게 · 마감 · 문의.
- [ ] One CTA with verb + channel + deadline + fallback to the QR.
- [ ] No empty adjectives; each claim has a visible or countable proof; nothing invented.
- [ ] Essential info is text; contrast ≥ 4.5:1 (large text ≥ 3:1); not colour-only; alt text / captions present; text-only reading order makes sense and holds every deciding fact.
- [ ] Link/QR opens logged out, on a phone, without a school account.
- [ ] Every image · font · music · face has a basis and a credit line; open questions sent to `teacher-law`.
- [ ] Weekday computed; deadline precedes the event; link/QR target checked.
- [ ] The piece does not reuse the last piece's headline pattern or layout order.

## Sources (checked 2026-11-20)
- Contrast 4.5:1 (normal text), 3:1 (large text = 18pt, or 14pt bold), logo/decoration exempt: W3C WCAG 2.2 SC 1.4.3 https://www.w3.org/TR/WCAG22/ . 한국형 웹 콘텐츠 접근성 지침 2.2 (KS X OT0003:2022, 2022. 12. 28.) 5.4.3 「텍스트 콘텐츠의 명도 대비」 4.5 대 1 이상, read today from https://www.webwatch.or.kr/static/homepage/attach/sa/korea_contents_law2.2.pdf (its large-text exception was not checked line by line → use the W3C wording for 3:1).
- 공공누리 types (제0유형, 제1-4유형, AI유형) and their conditions, read today on the official page: https://www.kogl.or.kr/info/license.do . The page also says 제0유형 and AI유형 are not attached together. 공유마당 https://gongu.copyright.or.kr
- Copyright and portrait questions are answered by `teacher-law` from the current law, not from this page.
- Headline length, 3-level hierarchy and the 3-second test are practice heuristics.
