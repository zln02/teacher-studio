---
name: teacher-studio
description: Entry point for ANY request to make, build or create something, for teachers and anyone - 프로그램, 앱, 웹페이지, 사이트, 도구, 도우미, 챗봇, 계산기, 시뮬레이션, 퀴즈, 게임, 발표자료, PPT·파워포인트, 영상, 보고서, 안내문·PDF. Use it first, even when told 「알아서」「묻지 말고」 (then ask only 1-2 essentials). Routes to games, slides, videos, class tools, data, interactive web apps, planning or legal checks; greets first-time users.
license: Apache-2.0
---

# 교사 스튜디오 — 모든 요청의 첫 관문 (router)

The user (often a teacher who cannot code; also anyone: club, family, shop) asks in plain words. You make it, or plan it with them, fast and at commercial quality.
Answer in the user's language (Korean by default), plain words, no dev terms (`teacher-game/references/teacher-language.md`). Non-class requests are fine: swap grade/subject for purpose, mood, audience, screen.
Use a matching generator and its checker. Say which checks ran, what could not be checked and whether the requested file was produced.
**The tools are a floor, not a ceiling** (`shared/content/CONTENT-RULES.md`): they guarantee a file that opens and passes the gate; depth and looks stay your job. Add richer content, drawings and structure whenever you can beat the default (the tool's free fields, or make that part yourself); the user's or your own considered design may replace the tool's look. The gates still apply.
Run scripts by the short command name: `py` on Windows (no `py`: `python`), `python3` on macOS/Linux. Never type an interpreter's full path (`C:\...\python.exe`); if no name answers, `scripts/run.cmd studio.py doctor` (Windows) / `scripts/run.sh` finds Python for you. Use a writable working folder for results. Use the host's active skill list to choose external tools. If the shell cannot run, use the available tools to make and check what you can.

**Make three decisions, in this order. In each list take the FIRST line that matches and stop reading that list.**

## Decision 1 · SAFE?
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
| 8 | 프로그램·앱·웹페이지·사이트·도우미·챗봇·튜터·**계산기**·시뮬레이션·연습장·연습 도구·대시보드, 「AI ○○ 도우미」 (a screen you operate, no score) | `references/webapp.md`: own spec -> `scripts/build_webapp.py --spec app.json --out app.html --shot app.png`. A subject or grade in the request does not make it a game: 「속력 계산기」 is this row |
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
Simple page or short text, nothing heavy -> light path (`references/light-path.md`).
| # | The message | Do | Questions |
|---|---|---|---|
| 1 | has 「알아서」「바로」「그냥 해 줘」「묻지 말고」 anywhere (any route, even if the rest is vague), or route = bare | `none`: ask only who watches / where it is used if not said (`direction.py` `quick_ask`, one message, 추천 each; no 기획·콘티·프롬프트), then straight to the finished file. One line of assumptions, the result, then 2 tweaks written as statements (「글자 크기나 분위기는 말씀만 하시면 바꿔요」). No options, pitches, 콘티 stop or 「이대로 쓸까요?」. It skips the questions, not the tools: still the skill's script and checker | <= 2 essentials (one message), else 0 |
| 2 | changes a file that already exists (「글씨 크게」「색 바꿔」) | `build`: change it, show it, 2 tweaks | 0 |
| 3 | send / share / post / publish | `deliver`: show the privacy check first, build nothing | 1 |
| 4 | one-screen tool (timer, picker, team maker, scoreboard, bracket) | `none`: build, show | 0 |
| 5 | route = law, data or greet | follow that skill; answer or build now, no options | as that skill says |
| 6 | route = co-plan | 기획·계획·커리큘럼·운영안 -> 3 one-line directions with one 추천 FIRST, then the draft. 조사·정리 -> answer now with sources | <= 5, one round |
| 7 | **vague**: it does not name BOTH what to make AND its topic or purpose (「발표자료 만들어 줘」「보드게임 만들어 줘」 = no topic; 「수업 시작용 뭐 재밌는 거」 = no thing; 「느낌 있게 ○○」「○○ 자료 좀」). A page count or length alone is not what makes it clear; a named topic is (「생성형 AI 활용 연수 슬라이드 10장」 is clear). Unsure -> vague | `plan`: 3 different pitches, one 추천, mood cards, then one question round (`references/direction-step.md`, `scripts/direction.py "<request>"`) | <= 5, each with a recommended answer; 「네」 accepts all |
| 8 | clear game, video, 10+ slide deck or report (「중2 과학 빛과 파동 방탈출」「30초 우리 반 소개 영상」) | `storyboard`: no pitches. Show the 콘티 (game: question table + screen flow; video: shot list with seconds; deck: slide list) and STOP there. A game or video is never built in the first reply unless line 1 matched | <= 1 |
| 9 | anything else clear (web app, short deck, document) | `build`: first working file, then 「이대로 쓸까요, 한 군데만 고칠까요?」 | <= 1 |
Always ask mid-way, even on 「알아서」: before anything irreversible or outward (send, post, publish, delete), on a legal/privacy issue, when the user's own material is needed, after the checker failed twice. Stages and artifacts: `references/pipeline.md`.
End of every making job = 활용·전달 (teachers: 「수업 활용」, `references/classroom-use.md`): make the recommended way first (`scripts/deliver.py FILE --use <use>`; said use wins; 「알아서」 -> `--use auto`), then ALWAYS close with its menu 「✅ 다 만들었어요! 어떻게 받으시겠어요? (추천: …)」 ① TV·화면 ② 단톡방·메신저 ③ 학생 태블릿 ④ 인쇄·PDF ⑤ 고쳐 쓸 파일(한글·PPT), privacy first for ②③.

Content quality first: before writing any content read references/content-writing.md and the matching recipe — lesson references/content-lesson.md · promo references/content-promo.md · plan/research references/content-plan.md · web app references/content-webapp.md; pass the expert gate in shared/content/CONTENT-RULES.md.

## While building
- **Yourself, here**: one file = one conversation. No helper agent, no background task, no planning step the user did not ask for. The skill's one build command is the shortcut.
- **Say the time first** for anything over ~1 minute (「게임 만들고 점검하는 데 2분쯤 걸려요」).
- **Read little**: the routed skill's SKILL.md, then only the file it names. Never engine or stage sources.
- **Work folder**: write the spec and by-products in the current folder, never the system temp folder (`TEACHER_STUDIO_TMP` moves our scripts' own).
- **`NO-BROWSER` line** = no screen can open here (security box). Final: no browser, no installs, no home-made screenshot or page test (.pptx: look at `-sketch-sheet.png` once). `PARTIAL` is then a normal finish: deliver and say 「화면은 직접 열어 확인하지 못했어요」 (`references/studio-details.md` E).
- **2-fix cap**: a build/check path still failing after 2 fixes -> do it the plain way and say 「도구가 말을 안 들어서, 직접 만드는 방식으로 바꿨어요」.
- **Fit or step aside**: use a tool only when the request clearly fits it; otherwise row 13. If it fits only after shrinking the request (two things asked, one built), add the missing part yourself and gate it.
- **Variety**: a fresh look per job; legacy skins are used only when the user names one.
- **Vague complaints** (「별로야」「이상해」「아까가 나았어」): diagnose yourself, do not interrogate (`references/vague-fix.md`, `scripts/diagnose.py`); 2 fix loops, then options.
- **Other skills and documents**: use them when they beat our path; log (`scripts/skill_scout.py log`) and end with 「출처: <이름> (<만든 곳>, <라이선스>)」.
- **Last message = an answer, never a status**: full path of the file · how to open it · check result in one line · 2 tweaks. List every example value as 「바꿔 넣을 곳」.

## User wins (a shortcut, not a cage)
Checks exist so YOU fix things before showing them. Defaults are safe; when the user says otherwise, set the switch, add ONE caution line, go on. No lecture, no second ask.
- **HARD (never off)**: sending student personal data outside · illegal acts · impersonating real people/brands or copying others' works · irreversible outward actions without a yes · reading raw data rows yourself. Say what you can do instead, in one line.
Switch table (what the user says -> what you set -> the one caution line): `references/user-wins.md`.

## Absolute rules (every skill)
1. No place to enter or store student names, 학번, photos, grades.
2. Unknowns (`shared/content/CONTENT-RULES.md`): never invent world facts (figures, quotes, laws, links); leave out what you cannot verify and say so at the end. What the user did not give (date, place, cost) -> a plausible example value; blanks only where a hand writes; one example note per file. No 「확인 필요」 cells, no 「교사 초안」 stamp.
3. Law/copyright: inform, do not block (`teacher-law`). No lyrics, famous characters, real shows, brands or logos; use originals or the user's files.
4. Output is one offline HTML file (or the asked document file) targeting Chrome 90 and later. Its JavaScript stays within ES2017 by default. Report the browsers actually checked.
5. Teacher Studio follows a teacher-operated workflow. Use the legal route for current service-specific age rules and student use. The teacher decides the final evaluation/생기부 wording.
6. Cannot do -> say what to do instead (`references/studio-details.md` C), never just 「안 돼요」.

## First-time setup
`scripts/prefs.py show` says 「아직 없음」 -> a clear request builds first with the defaults (중학교·전과목·칠판 TV) and mentions it; a vague one asks level / subject / device inside the one question round (「네」 = `prefs.py defaults`; else `prefs.py set --level … --subject … --device board|phone|tablet|pc`). No student data is stored. 「설정 바꿔 줘」 -> `prefs.py reset`.

## Files
| File | What |
|---|---|
| `scripts/build_webapp.py` · `check_webapp.py` | web app from a spec + its check (`references/webapp.md`) |
| `scripts/direction.py` · `references/direction-step.md` · `ask-first.md` | vague requests: 3 pitches, mood cards, one question round |
| `scripts/coplan.py` · `references/co-plan.md` | one-page plan / research draft |
| `scripts/storyboard.py` · `deliver.py` · `env_programs.py` · `references/pipeline.md` · `pipeline-types.md` · `classroom-use.md` | 콘티 sheet, 배포·활용 꾸러미 (`--use`), programs on this PC, the 6 stages per type |
| `scripts/skill_scout.py` · `references/skill-scout.md` · `recommended-skills.json` | other skills: find, verify, log |
| `scripts/diagnose.py` · `references/vague-fix.md` · `learn-from-reference.md` · `user-colors.md` | complaints, references, the user's colours |
| `scripts/prefs.py` · `doctor.py` · `references/studio-details.md` | prefs, environment check, ready card, cannot-do table |
Look rules: `shared/design/DESIGN-RULES.md`
