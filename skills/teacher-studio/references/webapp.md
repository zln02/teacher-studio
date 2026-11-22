# 웹 앱 · 프로그램 만들기 (interactive web app)

For any moving screen that no other row covers: 프로그램, 앱, 웹페이지, 사이트, 도우미, 챗봇, 튜터, 계산기, 시뮬레이션, 연습장, 대시보드, 「AI ○○ 도우미」.
Not for: games (`teacher-game`), decks, videos, timer/picker/teams/scoreboard (`teacher-class-tools`), spreadsheet reports (`teacher-data`).
Needs a server, login, database or app store -> R5.

## Fast path (target: 3 minutes, one conversation)
Do it yourself, here. No helper agent, no plan step, no extra skill reads. 「알아서」「묻지 말고」 = 0 questions; still use this path.
1. Say one line: 「바로 만들게요. (<가정: 학년·과목·언어>) 1~2분 걸려요.」
2. Write `app.json` from the request (Spec below). Choose the parts from what the user will DO, not from a stock pair:
   - asks questions in words -> `helper` · tries code -> `runner` · changes quantities and watches a result, fills a form, sorts, counts -> `custom` (your own controls)
   - 1 part when one job is enough; 2-3 only when the request has that many jobs. The page layout is picked from the parts (how many, which kinds, how much text), so do not arrange it yourself.
   - 「직접 해 보며 익히는」「연습」「실험」「시뮬레이션」 = the user DOES things: `custom` parts with real activities. A `helper` question box alone is never the answer to that request.
   - **Floor, not ceiling** (`shared/content/CONTENT-RULES.md`): a learning program is as deep as a good lesson on that unit. Cover each idea the unit has (for 경우의 수: 수형도·표로 세기, 합의 법칙, 곱의 법칙, 대표 유형) with something to try, practice questions that give the answer and the reason at once, and a harder challenge. Three parts is the builder's limit, not the content's: one `custom` part may hold several activities (your own tabs or steps inside its `html`). If the page you would make by hand is richer than what the parts allow, build it by hand as one offline HTML file and gate it with `check_webapp.py`. The style picked from `words` is a default; the user's `palette`, or one you choose for the topic, replaces it.
   - `../assets/webapp/examples/` holds test fixtures, not patterns for the builder. Open one only to see how a `custom` part wires `html` / `js`; never reuse its questions, its part order or its `words`. A page that repeats one gets the WARN 「예시를 그대로 따라간 것 같아요」.
3. `py <skill>/scripts/build_webapp.py --spec app.json --out <이름>.html --shot <이름>.png` (`python3` on Mac/Linux). It builds and checks. Report `PARTIAL` when checks could not run and `NOT READY` when a check failed. A `NO-BROWSER` line = no screen can open in this environment: do not try a browser yourself or write your own page test; `PARTIAL` is the normal finish, say the screen was not opened.
4. FAIL -> fix the spec (shorter labels, a missing `<label>`, `?.`), rebuild. Max 2 fixes, then the plain way (no-regret rule).
5. Final message: full path, 「더블클릭하면 브라우저에서 열려요」, the check line, the honest-AI line below, 2 tweak offers (예: 「질문 더 넣기」「파이썬 예시로」).

## Quality bar (what makes it worth more than a plain page; check before the final message)
1. **The first screen works in 5 seconds**: one clear title, the main control visible without scrolling, a sensible starting value or example already filled in.
2. **Real content for this class**: helper = 8-12 questions students of that grade actually ask, in their words; calculator/simulation = the textbook's own quantities, units and a worked example; no lorem ipsum, no 「예시 1」.
3. **Every control gives a visible result at once** (number + unit + one plain sentence 「시속 60 km로 2시간이면 120 km를 가요」), and wrong input gets a kind hint, not NaN.
4. **Facts are right for the grade**; one you cannot verify is left out and named in the last message. Formulas are shown the way the textbook writes them.
5. **Readable on the projector**: test with P (projector mode); labels are short enough not to wrap inside buttons.
6. The honest-AI line and what it can / cannot do (`can`, `cannot`) are written for this app.
7. **The screen is full of the subject, not of empty space**: after the first click nothing leaves most of the page blank, and repeating an action replaces the last result instead of stacking the same answer again.

## Spec
```
{"title": "≤40자", "subtitle": "학년 · 과목 · 핵심", "words": "2-3 words from THIS topic and the mood the user asked for (they pick the look: do not reuse a stock word)", "style": "<optional id from shared/design/styles.py>",
 "palette": {"primary": "#…"}, "ai": "rules" | "none", "about": "한 문장", "can": [...], "cannot": [...],
 "parts": [ 1-3 of:
   {"type": "helper", "name", "greeting", "placeholder", "fallback", "chips": [4-6 common questions],
    "intents": [{"keys": ["반복", "for", "while"], "answer": "2-3 short plain lines", "code": "optional ≤8 lines"}]},
   {"type": "runner", "name", "timeout_ms": 3000, "examples": [{"name", "code"}]},          // JavaScript only
   {"type": "custom", "name", "icon", "html": "...", "css": "...", "js": "..."} ]}
```
- helper: 8-12 intents. Keys = Korean words + English/code words a student would type. Answers are plain text (no markdown marks), accurate for the grade; an answer you cannot verify is left out. With a runner on the page, code in an answer gets a 「연습장에서 해 보기」 button.
- runner: JavaScript in a Web Worker; `console.log` prints; endless loops stop after `timeout_ms`; errors come with a plain Korean hint.
- custom: your own controls. Rules: ES2017 (no `?.` `??`), every input has a `<label>`, `autocomplete="off"`, sizes in rem, no fields for names/학번/phone, no storage, no network. Use `APP.el(id)`, `APP.onReset(fn)` (「처음으로」), `APP.say(text)` (screen readers), `APP.toRunner(code)`.
- Built in, never re-implement: 가-/가+, projector mode (P), 「처음으로」, 「이 프로그램은?」 panel, keyboard (Enter, Ctrl+Enter, Esc, ?), skip link, phone layout, embedded Noto Sans KR, style from `words` (the user's `palette` wins).

## Honest about "AI" (always)
- Never put an API key, token or a call to an online AI in the file. The checker fails on keys and on network code.
- `ai: "rules"` = prepared answers. Say it in the final message, one line: 「인터넷 AI(챗GPT 같은)가 아니라, 준비한 설명 N개에서 골라 답해요. 그래서 키·비용·인터넷이 필요 없어요.」 The page says the same in 「이 프로그램은?」.
- If the user wants a real AI chatbot: it needs an account, a key and money, and students may not use AI services directly (18+). Offer the rules version for students and, for the teacher only, how to use an AI service themselves. Do not build a key into a file.

## Garnish and motion (optional, last)
- After the page works and passes its check: `py shared/design/garnish.py env`. Codex present -> one consistent backdrop or illustration set (no text, logos or faces; `garnish.py plan` prints the optional command, `finish` compresses and writes the prompt manifest). Claude only -> `garnish.svg_backdrop()` or the CC0 packs. Inline the picture, keep it behind a scrim, never behind a form or a table.
- A talk-like page (an explainer, a guided demo) may use the preset E motion words (`shared/design/motion_e.js`: `TSE.auto()`, `data-e="big|pen|hl|cursor|drag"`); a demo cursor ends on the real result and makes no speed claim.

## Offline by default
- No CDN, no outside fonts or images. Python in the browser (Pyodide) is a ~10 MB+ download from the internet, so it breaks on a blocked school network: use the JavaScript pad, and if the class uses Python, show Python as read-only code in helper answers and say so in one line.
- `"online"` is not supported here; if the user insists on an online library, that is the bare path (R5) with a 「인터넷이 있어야 열려요」 line.

## Check (`check_webapp.py`, run by the build)
Static: outside addresses, `?.`/`??`, network/storage APIs, keys/secrets, student-identity fields, title/lang/viewport.
Browser (one headless Chromium, ~10 s): 1600x900, projector mode, 390 phone; JS errors, outside requests, sideways scroll, cut or vertically broken button text, overlapping controls, unnamed buttons, unlabeled inputs, small text, contrast; one click per part, then 「처음으로」 must clear it. `--deep` also proves the endless-loop stop. No Playwright -> static only (say so).

For custom calculations, include representative browser checks in `cases`. Each case maps input element IDs to values in `inputs` and gives the result element ID in `output` and its expected text in `expected`. See `speed-sim.json`.
