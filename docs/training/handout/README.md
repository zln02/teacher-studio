# 「AI에게 무기를 주면」 종이 안내지

2026. 11. 23.(월) 14:00 · 60분 연수용 **A4 한 쪽** 안내지 (deck-e v5): Claude **Cowork** · ChatGPT **Codex** 들어가는 법만 (교사 스튜디오 설치 안내는 뺐어요).
① 앱 열기 ② 채팅 말고 Cowork · Codex ③ 한 줄로 부탁(+ 양식 파일) ④ 받아서 확인 · 「물어볼 땐 채팅, 맡길 땐 Cowork · Codex」 · 개인정보 · 유료 요금제 안내 · 연수 쪽 QR.

| 파일 | 용도 |
|---|---|
| `handout.pdf` | 인쇄용 (A4 1쪽, 글꼴 포함, 흑백 인쇄 OK) |
| `handout.hwpx` | 한글에서 고칠 수 있는 판 (QR·아이콘 없음, 사이트 주소는 글자로) |
| `handout-preview.png` | 미리보기 |
| `handout.html` | PDF 원본 (브라우저에서 열어 Ctrl+P도 가능) |
| `handout.spec.json` | HWPX 원본 (teacher-docs `guide` 스펙) |
| `build_handout.py` | 전부 다시 만들기: `set PYTHONUTF8=1` 후 `py build_handout.py` |

## 인쇄하는 법
- 용지 **A4**, 배율 **100% (실제 크기)**: 「페이지에 맞춤」은 끄기. 여백은 PDF에 들어 있어요.
- 한 쪽이라 단면 인쇄면 돼요.
- 흑백으로 인쇄해도 번호·상자·QR이 모두 잘 보이게 만들었어요.
- QR은 미리보기 PNG에서 실제로 읽어 확인함 → `https://zln02.github.io/noan-ai/training/s2.html`.

## 점검 결과 (teacher-docs `docs.py check`)
- PDF: 열림(2쪽) · 빈칸 없음 · 주민번호 없음 · 날짜/시간 형식 · 띄어쓰기 · 글꼴 포함 → 모두 PASS
- HWPX: 파일 구조(쪽 나눔 손질 후에도) · 빈칸 · 개인정보 · 날짜 · 띄어쓰기 · 글꼴 → 모두 PASS
- 개인정보: 학생 정보 없음. 발표자 이름·직함만 의도적으로 넣음.

## 하네스 사용 중 걸린 점 (friction)
1. **글자 크기를 못 키움**: `docs.py` 스펙에 큰 글씨/크기 옵션이 없음 (본문 12.5pt 고정). 「크게 읽히는 안내지」는 docs 무기만으로 불가.
2. **쪽 나눔 없음**: 스펙에 page break · keep-with-next가 없어 2쪽 첫 줄을 정할 수 없고, 1쪽 맨 아래에 제목만 혼자 남음. HWPX는 `pageBreak="1"`을 XML에서 직접 고쳐 해결 (build_handout.py `patch_hwpx_page_break`).
3. **그림·QR·아이콘 블록 없음**: 스펙에 image/QR 항목이 없어 HWPX에는 QR을 못 넣음. PDF는 docs 레이아웃을 버리고 직접 HTML을 짜서(design 토큰 + shell 아이콘 + QR) `pdf_tools.html_to_pdf`로 인쇄.
4. **QR 도구가 slides 안에 있음**: `deck_qr.py`가 `teacher-slides/scripts`에만 있어 docs에서 쓰려면 다른 스킬 경로를 import해야 함 (shared/tools로 옮기면 좋겠음).
5. **번호 모양 고정**: `guide`는 소제목 `1.`·항목 `가.` 자동. ①②③④를 쓰려고 `{"p": "① ..."}`로 우회. `box`는 글 앞에 `□`를 자동으로 붙여서 `※`로 시작해 우회.
6. **양쪽 정렬 + 「」**: 기본 justify라 「」가 있는 줄의 글자 사이가 벌어짐 (항목별 정렬 옵션이 `p`에만 있음).
7. **아이콘 세트에 요리 그림 없음**: 175개 중 그릇·프라이팬·밥 없음 → 「불(도구) + 책(레시피) = 달걀(김치볶음밥)」 칩으로 대신.
8. **design 토큰 단위**: `design.py --use print --large`가 A4 794px 기준 px 크기(제목 48, 본문 18)를 줘서 pt로 쓰는 인쇄물에는 직접 환산해야 함.
9. **점검기 빈 곳**: 쪽수 상한(2쪽)·최소 글자 크기·흑백 대비는 확인하지 않음 → 미리보기로 눈 확인.
10. **Windows**: `PYTHONUTF8=1` 없이 stdin으로 넘긴 파이썬이 한글을 cp949로 읽어 깨짐 (`docs.py` 자체는 문제없음).
