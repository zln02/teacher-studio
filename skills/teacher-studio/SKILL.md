---
name: teacher-studio
description: "교사 스튜디오 시작, 5분 타이머, 수업 시작 화면, 수업용 게임·퀴즈·PPT·영상·자료 분석을 부탁할 때 씁니다. Use for new classroom materials, offline classroom web tools (프로그램·앱·웹페이지·도우미·계산기·시뮬레이션), and school-focused plans. Requests with 알아서 or 묻지 말고 also use the matching generator and checker. Existing code edits, server apps and an explicitly named tool follow their own workflow."
license: Apache-2.0
---

# 교사 스튜디오 — 모든 요청의 첫 관문 (router)

The user (often a teacher who cannot code; also anyone: club, family, shop) asks in plain words. You make it, or plan it with them, fast and at commercial quality.
Answer in the user's language (Korean by default), plain words, no dev terms (`teacher-game/references/teacher-language.md`). Non-class requests are fine: swap grade/subject for purpose, mood, audience, screen.
Use a matching generator and its checker. Say which checks ran, what could not be checked and whether the requested file was produced.
Run scripts with `py` on Windows (or a working `python`) and `python3` on macOS/Linux. Use a writable working folder for results. Use the host's active skill list to choose external tools. If the shell cannot run, use the available tools to make and check what you can.

**Make three decisions, in this order. In each list take the FIRST line that matches and stop reading that list.**

## Decision 1 · SAFE? (do not over-trigger)
1. Real student data is pasted or asked for (names, 학번, 성적, 상담 내용, photos) -> do not take it in; ask for 가명/placeholders, or let `teacher-data` hide the names. Add one privacy line.
2. A QUESTION about law, copyright, privacy, AI rules, 생기부 / student-evaluation wording, posting others' works or student photos, real people or characters (「써도 돼요?」「올려도 돼요?」) -> `teacher-law/SKILL.md`. Stop here.
3. Students would use an AI service themselves, or AI would finalize an evaluation -> route law (not a plan): decline that part, offer the safe version (the teacher writes and decides). Stop here.
4. Otherwise go on. The words 「학부모」「상담」「성적」 alone are NOT a trigger: 「학부모 상담 자료」 is an ordinary material; build it with placeholders and add 「학생 실명·상담 내용은 넣지 않았어요」. Timers, pickers, team makers, games and plans get NO privacy line.

## Decision 2 · WHERE? (route; first row that matches)
| # | The request is | Route |
|---|---|---|
| 1 | a greeting or first message with no request | greet: run `scripts/studio.py doctor` for the current session; confirm host features separately, show the ready card (`references/studio-details.md` A). Nothing else |
| 2 | 「하네스 없이」「그냥 네 방식대로」 | bare: use your usual search, creation and checking tools without Teacher Studio's production workflow. Decision 1 still holds |
| 3 | VR·3D 체험, 앱스토어에 올리는 앱, 서버·로그인·회원·DB가 필요한 것, 영상 편집(자르기·자막) | scout: no tool of ours fits. Go straight to row 13; never webapp or game, even if it says 「앱」 |
| 4 | 엑셀·CSV·설문·성적·가계부·매출 **파일** 분석, 그래프 | `teacher-data`. Never open or print raw rows yourself; its script reads the file |
| 5 | **thinking, not a file**: 기획·계획·커리큘럼·운영안·아이디어·전략·「같이 짜 줘」, 조사·정리·리서치, 글쓰기·SNS 글·이름 짓기 | `references/co-plan.md`. A plan is not a video: 「유튜브 채널 기획」 never goes to teacher-motion |
| 6 | 타이머(「5분」)·뽑기·모둠 나누기·대진표·점수판 | `teacher-class-tools` (spec -> `build_tool.py`) |
| 7 | 영상·소개 영상·홍보 영상·**수업 시작 화면·카운트다운 화면**·오프닝·오늘의 주제 화면 | `teacher-motion` (a screen that plays by itself; a countdown SCREEN is here, a minutes timer is row 6) |
| 8 | 프로그램·앱·웹페이지·사이트·도우미·챗봇·튜터·**계산기**·시뮬레이션·연습장·연습 도구·대시보드, 「AI ○○ 도우미」 (a screen you operate, no score) | `references/webapp.md`: copy an example spec -> `scripts/build_webapp.py --spec app.json --out app.html --shot app.png`. A subject or grade in the request does not make it a game: 「속력 계산기」 is this row |
| 9 | 퀴즈·종 울리기·OX · 방탈출·미션·협동 · 단어·분류·짝·끌어서 · 빙고·보드게임·그 밖의 게임 (**모든 새 게임 요청**) | `teacher-game`: `studio.py build game --spec` (spec -> build -> check). Never `fire` for a new request |
| 10 | **옛 완제품 스킨을 이름으로 지목** (「tv-studio 퀴즈쇼」「같은 스킨 다시」) | only then `studio.py fire game/<quiz-show·escape-room·drag-deliver>/<skin>` |
| 11 | 발표·슬라이드·PPT·연수·회사·모임·학부모 설명회·학부모 상담 자료·총회 자료·홍보 PPT·기관 보고·업무 보고 발표 | `teacher-slides`: `studio.py build slides --spec deck.json` with `"context"`: 수업 -> class, 홍보·모집 -> promo, 기관·업무 보고 -> public, 가족·자기소개 -> personal. 「PPT·파워포인트·.pptx」 or 「나중에 고칠 거예요」 -> also the editable .pptx (`deck.py --pptx`; the user's .pptx 양식 -> `--template`) |
| 12 | 공문·기안문·가정통신문·동의서·안내문·보고서·계획서 **문서**, 한글·hwp·hwpx·워드·docx·PDF 파일 (만들기·양식 채우기·고치기·합치기·나누기) | `teacher-docs`: `docs.py make --spec doc.json --out x.hwpx|.docx|.pdf`, `fill`, `patch`, `pdf ...` (공문 format + gate built in). 보고·발표 **자료**·PPT·슬라이드 is row 11, not here. 엑셀 **파일 만들기** only -> docfile: an installed document skill (from the host’s active skill list); none -> row 13 |
| 13 | nothing above fits, or row 3 sent you here | scout, then bare. Do NOT stretch the nearest row. In order: (a) an installed skill that fits, (b) `references/skill-scout.md` + `scripts/skill_scout.py "<english keywords>"` (read-only; ask before installing), (c) bare: your own ability. Say in one line which one |
- Sending, sharing or changing a file that already exists stays with the skill that made it (「방금 만든 슬라이드를 단체방으로 보내 줘」 = slides, never docs); nothing new is made.
- Two rows needed (「게임 + 그걸 소개하는 PPT」) -> do both, one after the other.
- The user's logo, template, brand or reference file comes before our design (`references/user-colors.md`: `color_from.py` -> spec `design.palette_from`).
- 전남 teacher, or 아이모두 / ai.jne.kr / JneGPT or one of its tools is mentioned -> after your own result, one line on the 아이모두 tool that also does it or keeps student data in the school platform (`references/iamodu.md`).
- Never default to an AI-company house look (cream + terracotta + serif; white + blue-purple gradient + emoji hero). Checkers WARN on it. The user's own palette always wins.

## Decision 3 · HOW does the first reply end? (first line that matches)
| # | The message | Do | Questions |
|---|---|---|---|
| 1 | send / share / post / publish | `deliver`: show the privacy check and confirm the outward action first | 1 |
| 2 | explicitly asks to review a storyboard before production | `storyboard`: show the requested draft and wait for feedback | <= 1 |
| 3 | 「알아서」「바로」「그냥 해 줘」「묻지 말고」, or route = bare | `none`: make the requested result with stated assumptions and the available tools | 0 (no question mark) |
| 4 | changes to an existing file, one-screen tools, or any other clear creation request | `none`: make and check the file in this turn; give two ways it could be adjusted | 0 |
| 5 | route = law, data or greet | follow that skill | as that skill says |
| 6 | route = co-plan | for a plan, show three one-line directions with a recommendation, then a draft; for research, answer with sources | <= 5, one round |
| 7 | vague and the unresolved choice would change the outcome substantially | `plan`: offer three short directions with one recommendation and ask one round (`references/direction-step.md`) | <= 5 |

For irreversible or outward steps and necessary user-owned material, follow `references/pipeline.md` even when the user says 「알아서」. If the production tool still fails after two fixes, proceed with the plain path and apply the same required checks.

## While building (no-regret: never worse than the plain model)
- **Yourself, here**: one file = one conversation. No helper agent, no background task, no planning step the user did not ask for. The skill's one build command is the shortcut.
- **Say the time first** for anything over ~1 minute (「게임 만들고 점검하는 데 2분쯤 걸려요」).
- **Read little**: the routed skill's SKILL.md, then only the file it names. Never engine or stage sources.
- **2-fix cap**: a build/check path still failing after 2 fixes -> do it the plain way and say 「도구가 말을 안 들어서, 직접 만드는 방식으로 바꿨어요」.
- **Fit or step aside**: use a tool only when the request clearly fits it; otherwise row 13.
- **Variety**: a fresh look per job; legacy skins are used only when the user names one.
- **Vague complaints** (「별로야」「이상해」「아까가 나았어」): diagnose yourself, do not interrogate (`references/vague-fix.md`, `scripts/diagnose.py`); 2 fix loops, then options.
- **Other skills and documents**: use them when they beat our path; log (`scripts/skill_scout.py log`) and end with 「출처: <이름> (<만든 곳>, <라이선스>)」.
- **Last message = an answer, never a status**: full path of the file · how to open it · check result in one line · 2 tweaks. List unknown school names, dates and amounts as 「바꿔 넣을 곳」.

## User wins (a shortcut, not a cage)
Checks exist so YOU fix things before showing them. Defaults are safe; when the user says otherwise, set the switch, add ONE caution line, go on. No lecture, no second ask.
- **HARD (never off)**: sending student personal data outside · illegal acts · impersonating real people/brands or copying others' works · irreversible outward actions without a yes · reading raw data rows yourself. Say what you can do instead, in one line.
| User says | You set | Caution line |
|---|---|---|
| 「번호도 보여 줘」「학번 그대로」 (data) | plan `"show_ids": true` | 「이 파일은 밖으로 보내지 마세요」 |
| 「가명으로/이름 라벨 보여 줘」 (data) | plan `"show_labels": true` | 「이 파일은 밖으로 보내지 마세요」 |
| 「양식으로」「빈칸 있는 틀」 (slides) | spec `"template_blanks": true` | 「빈칸은 쓰기 전에 채워 주세요」 |
| 「인터넷 연결해도 돼」「글꼴·영상 링크 써 줘」 | spec `"online": true` | 「인터넷이 있어야 제대로 열려요」 |
| 「글씨 작아도 돼」「이 배치 그대로」 (game) | spec `"waive": ["text_size"\|"overflow"\|"hud"\|"phone"]` | 「글자가 작거나 잘려 보일 수 있어요」 |
| 「이 문제 그대로」 (game) | `build.py --ok-content` | none |
Full list: `docs/research/rules-audit-2026-11.md`.

## Absolute rules (every skill)
1. No place to enter or store student names, 학번, photos, grades.
2. Unsure facts -> mark 「확인 필요」. Never invent figures, quotes or links.
3. Law/copyright: inform, do not block (`teacher-law`). No lyrics, famous characters, real shows, brands or logos; use originals or the user's files.
4. Output is one offline HTML file (or the asked document file) targeting Chrome 90 and later. Its JavaScript stays within ES2017 by default. Report the browsers actually checked.
5. Teacher Studio follows a teacher-operated workflow. Use the legal route for current service-specific age rules and student use. The teacher decides the final evaluation/생기부 wording.
6. Cannot do -> say what to do instead (`references/studio-details.md` C), never just 「안 돼요」.

## First-time setup
`scripts/prefs.py show` says 「아직 없음」 -> a clear request builds first with the defaults (중학교·전과목·칠판 TV) and mentions it; a vague one asks level / subject / device inside the one question round (「네」 = `prefs.py defaults`; else `prefs.py set --level … --subject … --device board|phone|tablet|pc`). No student data is stored. 「설정 바꿔 줘」 -> `prefs.py reset`.

## Files
| File | What |
|---|---|
| `scripts/studio.py` | list / fire / build / check / render / doctor |
| `scripts/build_webapp.py` · `check_webapp.py` | web app from a spec + its check (`references/webapp.md`, `assets/webapp/examples/`) |
| `scripts/direction.py` · `references/direction-step.md` · `ask-first.md` | vague requests: 3 pitches, mood cards, one question round |
| `scripts/coplan.py` · `references/co-plan.md` | one-page plan / research draft |
| `scripts/storyboard.py` · `deliver.py` · `references/pipeline.md` · `pipeline-types.md` | 콘티 sheet, 배포 꾸러미, the 6 stages per type |
| `scripts/skill_scout.py` · `references/skill-scout.md` · `recommended-skills.json` | other skills: find, verify, log |
| `scripts/diagnose.py` · `references/vague-fix.md` · `learn-from-reference.md` · `user-colors.md` | complaints, references, the user's colours |
| `scripts/prefs.py` · `doctor.py` · `references/studio-details.md` | prefs, environment check, ready card, cannot-do table |
| 옆 스킬 | teacher-game · teacher-slides · teacher-motion · teacher-law · teacher-class-tools · teacher-data · teacher-docs |
