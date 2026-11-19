# Direction step (방향 잡기) - same steps for every model

Goal: when the request is vague, bring ideas, mood and plan to the user first, so they only choose. When it is clear, skip this and build.
Idea sources (own wording): ask with recommended answers and "facts you can find yourself" (mattpocock/skills grilling, MIT); show 3 visual options instead of asking about taste (zarazhangrui/frontend-slides, MIT); one line pitches before questions (Donchitos/Claude-Code-Game-Studios, MIT); max-5 question cap (github/spec-kit, MIT).

Run: `python3 <skill>/scripts/direction.py "<request>" [--html FILE --open]` (Windows: `py`). It prints JSON: `inferred`, `coverage` (5 decisions), `vague`, `mode`, `pitch_slots`, `cards`, `text_fallback`. Use its structure; write the wording yourself.

## Quick mode (check first)
- 「알아서」「바로」「그냥 해 줘」 or `mode = build_now`: no pitches, no questions. Say one line: 「바로 만들게요. (<assumptions>으로 했어요)」 and build. Assumptions = `assumptions` list.

## Steps (vague requests)
1. **Know first.** Read `inferred` (subject, grade, device from the request, prefs and env). Never ask what is already there. Facts you can look up (a file the user attached, today's date) you look up.
2. **3 pitches.** Fill `pitch_slots` A/B/C: one line each, three different directions (A idea, B mood, C structure), not three versions of one idea. Mark one 「추천」 (pick the one that fits the user's prefs and the clearest benefit). Plain Korean, no jargon.
3. **Mood preview.** Show the 3 `cards`: Claude app -> the HTML as an artifact; Claude Code / Codex -> `--html FILE --open`; cannot render -> paste `text_fallback`. If the user already named a look, skip this step. If they gave a logo/template/brand file or have a saved palette (`--palette-from FILE|saved`, default saved), card A shows their own colours (`references/user-colors.md`).
4. **One question round, at most 5 questions.** Only `open` items from `coverage`, most important first; each has a recommended answer; 「네」 / 「그대로」 accepts every recommendation. The first-run prefs question (level, subject, device) goes inside this same round, and only if it could not be inferred. Never a second round unless the user asks.
5. **One-line plan, then build in the same turn.** 「이렇게 만들게요: <한 줄>. 바꾸고 싶은 데가 있으면 말씀해 주세요.」
6. **After building**: one line what, one line how to use, then offer exactly 2 tweaks (예: 「글씨를 더 크게 / 색을 더 차분하게 할까요?」).

## Message shape (one message, then wait)
```
이런 방향은 어떠세요? (추천: B)
A. <아이디어 한 줄>   B. <분위기 한 줄>   C. <구성 한 줄>
[미리보기 카드]
고르실 것 (모르면 「네」라고만 하세요):
1) <질문> (추천: <답>)  2) ...
```

## Rules
- Safety/privacy/law comes before this step (router rule 1). Never ask for student names or data.
- Choices, not open questions. Never write 「어떤 걸 원하세요?」 alone.
- The user's own template, logo or reference always comes first (`user-colors.md`, `learn-from-reference.md`).
- If the user ignores the options and states a direction, take it and build.
