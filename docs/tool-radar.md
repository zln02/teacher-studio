# 도구 레이더 (Tool radar)

하네스에 넣을지 검토한 외부 도구·저장소 기록. 확인한 날: 2026-11-19 (earshot 행은 2026-11-20 원문 확인).
판정: **채택**(필요할 때 설치·연결) · **참고**(방식만 가져옴) · **안내만**(선생님께 조건과 함께 소개) · **넘어감** · **지켜보기**.
라이선스·약관은 바뀔 수 있으니 실제로 넣기 전에 원문을 다시 확인한다.

| 도구 | 하는 일 | 라이선스·조건 | 판정 | 이유 |
|---|---|---|---|---|
| Openverse (openverse.org) | CC·공공 저작물 이미지·소리 검색 API | 계정 없이 사용, 대량 수집 금지 | 채택 | 배경음악·효과음 무료 검색처, 출처 표기 자동화 |
| earshot (Leonxlnx/earshot) v0.4.1 (2026-11-06) | 소리 파일을 듣고 설명·측정(LUFS·최대음·깨짐)하고, 코드로 만든 효과음 창고 252개에서 골라 만듦 (**글로 새 소리를 만드는 AI는 아님**) | 코드 MIT(LICENSE 원문 확인). 모델은 따로 받음: CLAP `laion/larger_clap_general` Apache-2.0, AST `MIT/ast-finetuned-audioset` BSD-3-Clause(모델 카드 확인). CPU 전용, Windows 가능(torch 포함 파이썬 3.10+). 크기 실측: 라이브러리 약 1.3GB + 모델 1.1GB ≈ 2.4GB, 설치 약 7분. PyPI의 `earshot`은 **다른 프로젝트**라 GitHub 태그로 설치 | 채택(선택·동의 후 설치) | `shared/tools/ensure.py earshot`(전용 폴더, `--uninstall`) · `sound_ears.py listen/sfx`. 이 PC에서는 보안 정책(Application Control)이 `earshot.exe`를 막아 실행 확인은 못 함 |
| MMAudio | 영상에 맞는 효과음 생성 | 코드 MIT, **가중치 CC-BY-NC**, GPU 약 6GB | 안내만 | 비상업·GPU 필요 |
| Supertonic 3 | 로컬 음성 합성 | MIT / OpenRAIL-M(AI 음성 표시, 사칭 금지) | 채택(기본 목소리) | 일반 PC에서 빠름 |
| Qwen3-TTS 0.6B | 로컬 음성 합성(소희) | Apache-2.0, CPU 느림 | 채택(고급 옵션) | 품질 좋음, 시간 오래 걸림 |
| ThreeRT (meshy-dev/ThreeRT) | 레이트레이싱 three.js | MIT, macOS 앱 중심 | 지켜보기 | 브라우저에선 일반 three.js와 같음 |
| CLI-Anything (HKUDS) | 설치된 프로그램(Shotcut, GIMP, Blender…)을 AI가 조작 | Apache-2.0, 앱 설치 필요 | 참고·선택 경로 | 사용자 PC에 프로그램이 있을 때 길 고르기 |
| founder-skill | 창업자용 스킬 11개 | MIT | 참고 | 단계별 설치 안내 방식 |
| mattpocock/skills | grill-me(질문으로 요구 확정), handoff, setup | MIT | 참고 | 미니 질문(1~3개, 추천 답), 한 줄 설치 |
| anthropics/skills | 공식 PPT·Word·엑셀·PDF 등 | 스킬별 상이 | 함께 쓰기 | 있으면 위임, 우리는 디자인·점검 |
| GoogleChrome/modern-web-guidance | 최신 웹 기술 지침 스킬 | Apache-2.0 | 참고(규칙 발췌) | 웹페이지 무기·사이트 규칙 |
| meta/astryx | React 디자인 시스템 | MIT, React 19 필요 | 넘어감(웹앱 무기 후보) | 빌드 없는 결과물과 안 맞음 |
| pingdotgg/t3code | 코딩 에이전트 GUI | MIT, Windows 지원 | 참고 | 개발자용 |
| claude-video (/watch) | 영상 → 장면 사진 + 자막 | MIT, Gemini 자동 업로드·yt-dlp | 직접 안전판 제작 완료 (`shared/tools/video_eyes.py`) | 로컬 파일만, 외부 전송 없이 |
| OKLab / OKLCH (Björn Ottosson) | 사람 눈에 고른 색 공간: 변환·조화색·같은 간격 명암 | 행렬은 공개 도메인(저자 공개) | 채택(직접 구현 `shared/design/oklch.py`, 외부 코드 없음) | 색 뽑기·색약 점검의 거리 계산 |
| Machado·Oliveira·Fernandes 2009 색각 이상 시뮬레이션 | 적·녹·청황색약에서 색이 어떻게 보이는지 | 논문의 공개 행렬(심한 정도 1.0) | 채택(직접 구현 `shared/design/color_check.py`) | 정답·오답, 모둠, 그래프 색이 비슷하면 WARN |
| Pillow | JPG·GIF·WEBP 사진에서 색 뽑기 | HPND(허용형) | 채택(선택, 필요할 때 동의 후 `ensure.py pillow`) | PNG는 설치 없이 직접 읽음 |
| Alpine.js | 작은 화면 상호작용 | MIT | 사용 중(노안중 사이트) | 빌드 없이 한 줄로, 이 하네스 결과물에는 넣지 않음(바닐라 JS 유지) |
| Open Props | CSS 변수 모음 | MIT | 사용 중(노안중 사이트) | 색·간격 기준 참고 |
| Web Awesome | 웹 컴포넌트 | MIT(무료판) | 사용 중(노안중 사이트) | 하네스 결과물은 단일 HTML·외부 요청 0 원칙이라 번들하지 않음 |
| newtake.ai | AI 영상 제작 서비스 | 계정, 업로드물 영구 사용권 | 안내만 | 학생 얼굴 영상 비권장 |
| Upload-Post | SNS 올리기·예약 MCP | 무료 월 10번 | 안내만 | 초상권·개인정보 |
| PostHog | 방문자 분석 MCP | 무료 월 100만 이벤트 | 넘어감 | 추적 금지 원칙 |
| Firecrawl / Bright Data | 웹 수집 MCP | 키 필요, 무료 한도 | 넘어감 | 기본 웹 검색으로 충분, 약관 문제 |
| Meta Ads | 광고 AI 커넥터 | 베타 | 넘어감 | 선생님 업무와 무관 |
| GSAP | 고급 애니메이션 | 자체 Standard License | 동봉 안 함 | CDN 선택 기능만 |
| Remotion | React 영상 | 자체 라이선스 | 넘어감 | 재배포 조건 |

| Claude-Code-Game-Studios (Donchitos) | 에이전트 49개·스킬 75개 게임 스튜디오 | MIT | 참고 | 브리프 항목별 built/broken 점검, 키 입력 스모크 테스트, 「사람이 아직 안 해 봄」 명시 |
| google/skills | Google Cloud·Firebase·Gemini 개발 스킬 | Apache-2.0 | 넘어감 | Workspace·Classroom 스킬 없음 |
| cloudflare/security-audit-skill | 보안 점검(정찰→검증→보고서) | MIT, 서브에이전트 많이 씀 | 채택(출시 전 1회) | 하네스 스크립트·노안중 사이트 점검, 번들 안 함 |
| herdr (ogulcancelik) | 에이전트용 터미널 멀티플렉서 | Apache-2.0 | 넘어감 | 개발자용 |
| HeyGen hyperframes | HTML 기반 모션그래픽 스킬 | 미확인 | 검토 예정 | 우리 HTML 움직임 엔진과 방향이 같음 |

모션 효과 20선(출처 미확인)은 일반 기법이라 직접 구현한다. 우선 10개: Impact frame, Letter dive, Layer explode, Rack focus, Dolly zoom, Paper tear, Blade slice, Sketch words, Orbit ring, Day dial. GPU 없는 PC를 위해 큰 blur·filter는 줄인다.
