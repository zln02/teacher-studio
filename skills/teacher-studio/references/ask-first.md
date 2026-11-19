# Ask-first rule (「AI가 먼저 묻기」) — shared by every Teacher Studio skill

Goal: one short, friendly check that makes the result fit the teacher, never an interview.
Inspired by the "grill-me" idea (mattpocock/skills, MIT), shrunk for non-coder teachers.

## When to ask
1. If the request is already clear (what + who + rough look), or the teacher says 「알아서」 / 「바로 만들어 줘」 / 「그냥 해 줘」: **do not ask. Build.** State your assumptions in the one-line plan instead.
2. Otherwise ask **at most 1-3 questions in a single message**, only about decisions the teacher must make:
   purpose/audience, mood/look, material (their own file/photo/text or not).
3. Never ask what you can detect or infer: device (read `~/.teacher-studio/prefs.json` and env.json), grade level from wording ("초3 구구단"), subject, OS/environment, file type, size. Never ask about tools, formats, or code.
4. First-run preferences (school level / subject / device) are asked once via `scripts/prefs.py`, not here. Read them and reuse.

## How to ask
- Every question carries a **recommended answer** and numbered choices. Say it so 「그대로」 / 「네」 / 「1번」 accepts it.
  Format: `질문 (추천: ○○)` + 2-3 numbered choices.
- If the question is about **look/mood**, show 3 style options as visual swatches when the environment can render them
  (artifact/preview: three small colour+font cards; use `shared/design/styles.py` / `teacher-game/scripts/style_auto.py` to pick three distinct styles if present).
  Otherwise describe each in one plain Korean line (「짙은 남색+금색, 굵은 글씨」).
- Korean for the teacher, plain words, no dev terms (see `teacher-game/references/teacher-language.md`).

## Then
- Confirm a **one-line plan** and build in the same turn, e.g. 「중2 과학 빛과 파동, 방탈출, 칠판용 · 파란 실험실 느낌으로 만들게요.」
- **One round only.** Do not ask follow-ups unless the teacher invites it (「더 물어봐 줘」 / 「꼼꼼히 해 줘」). After building, offer 2 tweaks instead of asking more.
- Privacy and legal rules still apply; asking never replaces them. Never ask the teacher for student names or data.

## Exact lines (Korean, say as written)
- Plan line: 「이렇게 만들게요: <한 줄 계획>. 바꾸고 싶은 데가 있으면 말씀해 주세요.」
- Accept hint under questions: 「그대로 괜찮으면 '네'라고만 하세요.」
- Skip case: 「바로 만들게요. (<가정>으로 했어요)」
