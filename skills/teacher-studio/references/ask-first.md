# Ask-first rule: 「먼저 보여 주고, 마지막에 묻는다」 - shared by every Teacher Studio skill

Goal: the user chooses, they do not have to invent. Show options first, ask last, ask once. Full steps: `direction-step.md`.
Inspired by "grill-me" (mattpocock/skills, MIT), rewritten and shrunk for non-coders.

## Rules
1. **Clear request: ask only the facts only the user knows and the result depends on** (the date of a notice, event or trip; the number of 모둠 for a team game; who watches when unsaid), at most 2, in ONE message with 추천 each (`scripts/direction.py "<request>"` -> `quick_ask`; nothing open -> no question). Otherwise build. State assumptions in one line: 「바로 만들게요. (<가정>으로 했어요)」
1a. **「알아서」/「바로」/「묻지 말고」/「그냥 해 줘」**: ask only the 1-2 essential questions the request left open (누가 보나요? / 어디에 쓰시나요?: `direction.py` `quick_questions`, `quick_ask` is the message), in ONE short message, each with 추천 (「네」 = all recommended), then make it with no other stop. The request already says who and where (「중2 수업 도입용」「교직원 회의용」) -> no question at all. A one-line ask is enough: the harness works out the rest itself so the user does not need fix-up rounds. Never name the steps to the user (no 기획 · 콘티 · 프롬프트).
2. **Vague request: options first.** Three one-line directions with one marked 추천, a mood preview when the environment can show it, only then questions (`direction-step.md`).
3. **One round in total, at most 5 questions** (spec: fewer is better). The first-run prefs question (school level, subject, device) is part of that same round and is asked only if it cannot be inferred. Never ask twice.
4. **Never ask what you can infer or look up**: device and level (`~/.teacher-studio/prefs.json`), grade and subject from wording ("초3 구구단"), OS, file type, size. Never ask about tools, formats or code.
5. **Every question has a recommended answer** and numbered choices; 「네」 / 「그대로」 / 「1번」 accepts it. Format: `질문 (추천: ○○)`.
6. **No open questions** such as 「어떤 걸 원하세요?」. Offer 2-3 choices instead.
7. Korean for the teacher, plain words, no dev terms (`teacher-game/references/teacher-language.md`).

## How to show a look
- `python3 scripts/direction.py "<request>" --html FILE --open` draws 3 distinct looks (colour, font, sample title, layout) as one offline file.
- Cannot render: use its `text_fallback` (one plain line per look).

## After the answer
- Plan line: 「이렇게 만들게요: <한 줄 계획>. 바꾸고 싶은 데가 있으면 말씀해 주세요.」 and build in the same turn.
- No follow-up questions unless the user invites them (「더 물어봐 줘」/「꼼꼼히 해 줘」). After building, offer 2 tweaks instead.
- Privacy and legal rules still apply; asking never replaces them.

## Mid-way asks
Beyond the first round, ask again only at pipeline checkpoints or for the always-ask list in `pipeline.md` (irreversible/outward steps, legal/privacy, own material needed).
