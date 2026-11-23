# 가벼운 길 (light path) - step aside when the plain agent is already good

Why: in the fair comparison (2026-11-22) a family-trip web page took 14 minutes through the full pipeline and 44 seconds plain, with the same number of things to fix. A harness that is slower and not better on simple work should step aside.

## Routing rule (check before Decision 3 in SKILL.md)
Take the light path when ALL hold:
1. The request is ONE simple file: a short web page (일정표, 소개, 안내 한 장), a plain notice text, a list or checklist, a short message.
2. It names nothing heavy: no game or quiz, deck or PPT, video, 한글/워드 form or 공문, data file, report, class tool, student data, and no sharing or posting.
3. No brand, template or reference file of the user's to follow.
`py scripts/light_check.py --route "<request>"` prints `light` or `full` (same rule). Unsure -> full.

## What the light path does
- Still asks first when a fact only the user knows changes the result (date, 모둠 수, who reads it): at most 2 questions in one message (`direction.py` `quick_ask`).
- Reads nothing else: no other SKILL.md, no references, no storyboard, no screenshots, no pitches.
- Writes the file directly (one offline HTML, ES2017, no outside images; or plain text).
- Runs only `py scripts/light_check.py FILE`: privacy (주민번호 · 휴대전화 · 학년반번호 · 실명 칸), blanks, offline, old-Chrome syntax, phone viewport.
- Ends with the delivery menu it prints (「✅ 다 만들었어요! 어떻게 받으시겠어요?」 ①~⑤), like every job.
- If the user then asks for more (a printable 한글 file, a game, sharing), that request goes the full way.
