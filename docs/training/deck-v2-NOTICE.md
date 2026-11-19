# deck-v2.html: 함께 들어간 남의 코드·글꼴

`deck-v2.html`은 인터넷 없이 열리도록 아래 코드를 파일 안에 그대로 넣었습니다. 외부 요청은 0개입니다.

| 이름 | 버전 | 라이선스 | 어디서 | 메모 |
|---|---|---|---|---|
| three.js | r128 (`three@0.128.0`, `build/three.min.js`) | MIT, Copyright © 2010-2021 three.js authors | `npm pack three@0.128.0 --ignore-scripts` 뒤 패키지 안 `LICENSE`를 직접 읽음 | sha256 `9274bbce…2c1ce2`. 3D 장면 6개. ES5 UMD 빌드라 오래된 크롬에서도 돌아감 (`?.`처럼 보이는 곳은 삼항 연산자 `?.07`) |
| anime.js | 4.5.0 | MIT, Copyright (c) 2025 Julian Garnier | 저장소 `shared/vendor/animejs` (읽기만) | 빌드·글자 움직임 |
| Lucide icons | 1.75.0 (스프라이트에서 쓰는 기호만) | ISC, Copyright (c) 2026 Lucide Icons and Contributors | `shared/vendor/lucide` (읽기만) | |
| Noto Sans KR · Noto Serif KR | KS X 1001 부분 글꼴 | SIL Open Font License 1.1 | `shared/fonts` 임베더 (읽기만) | 덱에 쓰인 글자만 잘라 넣음 |
| QR Code generator (Project Nayuki) | 저장소 동봉본 | MIT | `shared/vendor/qrcodegen` (만들 때 SVG로 그림) | 마지막 장 사이트 QR |

다시 만들기: `set PYTHONUTF8=1 && py docs/training/deck-v2-src/build.py`
(three.js는 이미 만든 `deck-v2.html` 안의 블록을 해시 확인 뒤 다시 씁니다. 처음부터 만들 때는 `--three <패키지>/build/three.min.js`.)

`docs/training/compare/` 화면(시연 결과 캡처)은 있으면 만들 때 JPEG data URI로 넣고, 없으면 「결과 화면 들어갈 자리」 틀을 보여 줍니다.
