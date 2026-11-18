# 0007. 라이선스 정책

- 상태: Accepted (2026-11-18) — 일부 항목은 「계획」

## 배경
이 저장소는 공개되고, 학교·개인이 결과물(HTML)을 그대로 배포할 수 있다. 번들한 부품의 라이선스가 재배포·상업·파생을 막으면 선생님이 모르는 사이에 위반이 생긴다.

## 결정
- 저장소 코드는 **Apache-2.0**.
- 파일 안에 **번들하는 것은 허용적 라이선스만**: MIT / BSD / ISC / Apache-2.0 / OFL / CC0. 현재: anime.js·Motion·Chart.js·KaTeX·Phaser(MIT), canvas-confetti·Lucide(ISC), Kenney 그림·소리(CC0), Noto Sans/Serif KR(OFL, 페이지에 쓰는 글자만 잘라 넣음), 그 밖의 글씨체는 Google Fonts(OFL, 열 때 불러옴). 제3자 고지는 `NOTICE`.
- **CC-BY 자료는 번들하지 않고 필요할 때 받아 쓰며** 출처 표기를 자동으로 붙인다 — 「계획」.
- **NC·SA·재배포 제한 자료는 피한다**: Remotion, unDraw, Blush, Quaternius, pyhwpxlib 등.
- **예외 하나: axe-core(MPL-2.0)** — 점검기 전용으로 수정 없이 파일 그대로 `shared/vendor/`에 두고, 선생님이 받는 결과물에는 넣지 않는다 (파일 단위 약한 카피레프트라, 수정하거나 결과물에 넣지만 않으면 추가 의무가 없다).
- **GSAP은 번들하지 않는다**: 자체 Standard License(재배포·경쟁 도구 조항)가 불명확. 필요하면 선택적 CDN 사용.
- **ffmpeg는 번들하지 않는다**: GPL이 섞인 빌드가 있어 배포 시 의무가 생긴다. 처음 필요할 때 사용자 동의를 받아 설치한다(ADR 0008).

## 검토한 대안
- **다 번들**: 편하지만 라이선스 위험과 용량 증가. 기각.
- **라이선스 무시하고 외부 링크만**: 오프라인 결과물 원칙 위반, 추적 불가. 기각.
- **GPL 계열 허용**: 결과물 HTML 배포에 전염될 수 있음. 기각.

## 결과
- 장점: 결과물을 자유롭게 나눠도 안전. `NOTICE`로 출처가 투명하다.
- 단점: 고품질 상용 자산 선택지가 줄고, 직접 그리거나 CC0만 써야 한다. CC-BY 자동 표기는 아직 구현 전. 각 도구의 약관은 바뀔 수 있어 주기적 재확인이 필요하다.

## 근거/측정
- `docs/how-it-works.md` 「도구 선정 기준」: MIT·Apache·OFL·CC0만 번들, GSAP 제외 사유, anime.js `?.` 1곳 패치.
- `LICENSE`(Apache-2.0), `NOTICE`, `INSTALL.md`(ffmpeg는 필요할 때 `winget`/`brew`로 설치).
- 「피할 목록」(Remotion 등)과 CC-BY 자동 표기는 작성 시점에 저장소 문서만으로는 개별 확인되지 않은 항목이다.
