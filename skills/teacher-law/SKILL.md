---
name: teacher-law
description: Answers legal and rules questions (privacy, copyright, AI rules, characters, school records) by looking up current Korean law (한국법 기준) live from official sources. For teachers and anyone.
license: Apache-2.0
---

# 교사 스튜디오 · 법률 안내 (Teacher Studio · Law)

The user asks 「이거 써도 돼요?」「올려도 돼요?」. You read the CURRENT official text, then answer with a short fixed card in plain Korean.
This skill stores no article text and no conclusions (law changes). It is: where to look + how to look fast + the card.

## Principles
1. Responsibility stays with the user. You inform; you never block the work and this is not legal advice.
2. Nothing is asserted without a source. What you could not confirm is written 「확인 필요」.
3. Plain words in the body; article numbers only in the 근거 lines. No dev terms.

## Recipe (2 tool calls, about 30 seconds; answer in this chat, no helper agent, no other skill files)
1. **Sort the question** into one or two kinds and pick the laws from the table. Ask ONE question only if a missing fact flips the answer (공개 범위, 학생 얼굴이 나오는지, 상업적 이용인지); otherwise state the assumption in the card.
2. **Read the official text in ONE call** (prints 시행일 + the article text + its link; each law takes about 2 s):
   `python3 scripts/law_fetch.py --articles "저작권법:25,35의5"` (repeat `--articles` for a second law; Windows `py`; `--chars 1200` for a long article)
   - The table below is only a guess of WHERE to look. Use what the script prints; 「못 찾은 조문」 or 「못 읽음」 -> write 「확인 필요」 for that item and give the link. Never retry the same site.
3. **Only if needed, ONE web search**: the question hangs on something that is not a statute (교육부 지침, 교육청 안내, a service's terms, a 위원회 해설), or step 2 could not read anything. Official sites first (`references/sources.md`); a blog or news page may support the answer but is labelled 「보조 출처(공식 아님)」.
4. **Write the card.** Stop there: no extra sections, no source list after the card.
No search or shell tool in this environment -> say 「지금 이 환경에서는 최신 법을 확인할 수 없어요」, give the official links from the table, and give NO conclusion (how to turn search on: `references/sources.md` §4).

| Kind | Look at (guess; the script confirms) |
|---|---|
| 저작권 (그림·글·음악·영상·글꼴·교과서) | `저작권법:25,28,35의5` · 한국저작권위원회 copyright.or.kr |
| 캐릭터·상표·로고 | `저작권법:25,35의5` + search 상표법 / 부정경쟁방지법 only if the use is commercial or public |
| 개인정보 (학생 이름·사진·성적·상담) | `개인정보 보호법:15,17,18,22의2` · 개인정보보호위원회 pipc.go.kr |
| AI 규정 (학생 평가·수행평가·AI 서비스) | `인공지능 발전과 신뢰 기반 조성 등에 관한 기본법:2,31` · 교육부 moe.go.kr 「수행평가 AI 활용 관리 방안」 |
| 생기부·학교 규정 | search: 교육부 학교생활기록 작성 및 관리지침 (최신 연도) · 시·도 교육청 |
| 서비스 약관·나이 | the service's own terms page (Anthropic, OpenAI …) |

## The card (fixed shape; the whole answer is at most about 250 words)
```
⚖️ 질문: (한 줄)
✅ 한 줄 결론: (쉬운 말, 「~일 수 있어요」 수준. 단정 금지)
왜 그런가요?
 · (2~3줄. 조문이 실제로 말하는 조건을 쉬운 말로)
근거
 · 법령 이름 제N조 (시행 YYYY-MM-DD) 원문 링크      ← 줄마다 하나, 최대 3줄
 · (확인하지 못한 것은 「확인 필요」, 공식이 아니면 「보조 출처(공식 아님)」)
이렇게 하면 안전해요
 1) …  2) …  3) …
법률 자문이 아니에요. 최종 판단과 책임은 선생님께 있어요. 애매하면 학교 관리자·교육청(법무 담당)에 확인하세요.
법은 바뀔 수 있어요 — 확인한 날: YYYY-MM-DD
```
Quality bar (check before sending):
1. The conclusion answers the user's exact situation (their material, their place of use), not the topic in general.
2. Every 근거 line has a law name, article, 시행일 and a link that the script or search actually returned. No article number from memory.
3. 「왜」 states the condition that decides the case (예: 수업 목적인지, 공개 범위, 일부인지 전부인지), in words a non-lawyer uses.
4. The three safe options are things the user can do today, the easiest first (예: 무료 이용 표시가 있는 그림으로 바꾸기).
5. Tone: 「이렇게 하면 걱정이 줄어요」, never a ban. The last two lines are copied exactly, with today's date.

## When another skill calls this (student data, others' works, public sharing, 생기부 in a making job)
Keep the making job going. Do step 2 once and add ONE line to that job's final message (결론 + 근거 링크 하나). No full card unless asked.

## Output
- Default: the card in chat.
- 「안내문으로」「인쇄할래」 -> one A4 HTML page: `python3 scripts/make_notice.py --data notice.json --out ~/TeacherStudio/law-notice-<날짜>.html` (keys: `title`, `question`, `conclusion`, `reasons`[], `sources`[{`name`,`article`,`effective`,`url`}], `safe_options`[], `checked_date`). Print with Ctrl+P.
- 한글(HWPX): 「한글 문서는 가정통신문 무기와 함께 준비 중이에요.」

## Student data
Never ask for or store student names, grades, counseling content or photos. If the user pasted some, say once 「학생 정보가 보여요. 가명으로 바꾸시면 더 안전해요」, do not repeat it back, and go on.

## Files
| File | What |
|---|---|
| `scripts/law_fetch.py` | `--articles "법령명:조,조"` official text + 시행일 in one call; `--url` / `--secondary` any page, one try each (6 s), blocked hosts remembered 30 min, 40 s total |
| `references/sources.md` | official sites, per-kind article list, how search is switched on per environment |
| `scripts/make_notice.py` · `assets/notice-template.html` | printable notice |
| `references/test-questions.md` | questions for checking this skill |
