# 같이 기획 (co-plan) - for work that is not "make a file": planning, analysis, research

Use for: YouTube channel, event, curriculum, parent meeting plan, club/shop plan, "정리·조사·분석해 줘". Output is a one-page plan the user can approve, not a tool run. After approval, any piece that is a making job goes to the matching skill (slides, game, ...).

## Steps
1. Know first: read prefs, the request, attached files. Do not ask what is inferable.
2. Vague request: show 3 one-line directions with one 추천 (`direction-step.md` step 2), then at most 5 questions in one round (each with a recommended answer; 「네」 accepts all). Clear request or 「알아서」: skip to 3.
3. Research/analysis jobs: search the web when a search tool exists and say so (「최신 자료를 찾아봤어요」). When it does not, say once: 「여기서는 인터넷 검색이 안 돼서 제가 아는 범위로 썼고, 확인 필요 표시를 달았어요」. Never invent figures, quotes or links; unsure -> 「확인 필요」.
4. Write the one-page draft (below). Keep it to one screen of text.
5. Ask one thing only: 「이 방향(추천 B)으로 다음 단계를 진행할까요?」. Then offer 2 tweaks.
6. Optional: `python3 scripts/coplan.py --title ... ` prints the empty skeleton if a fixed shape helps a weak model.

## One-page draft (fixed order)
```
# <제목>
목표: <한 줄>        대상: <누구를 위한 것>
방향 3가지: A <한 줄·장단점>  B <...> (추천)  C <...>
추천 이유: <한 줄>
할 일 (순서대로): 1) 2) 3) (각각 누가·언제)
위험·주의: <개인정보·저작권·시간 등 1~3개>
출처: <제목, 링크, 확인한 날짜>  (없으면 「출처 없음, 확인 필요」)
```

## Rules
- Plain Korean, no dev terms. Sources always with link and date; do not copy long text from them.
- Student data, parent contact details, counseling content never go into the plan; use placeholders (「학생 A」). Law/privacy questions -> `teacher-law`.
- Planning a counseling/parent material is allowed; only real student information is not (router rule 1).
- Use other skills and documents when they help (record with `skill_scout.py log`, credit with one 「출처」 line).
- Pipeline: co-plan collapses stages 1-3 into outline -> draft with one checkpoint (`pipeline.md`); a making piece that follows goes through the full line.
