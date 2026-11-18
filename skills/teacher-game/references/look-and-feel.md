# 분위기·그림·소리·화려함

## 1. 분위기 (theme → 출발점, themeOverride·extra.css로 세계관에 맞게)
| 선생님 말 | theme | 음악 mood | 배경 |
|---|---|---|---|
| 신나게·게임처럼 | arcade / gameshow | upbeat | grid / spot |
| 우주·과학 | space | space | stars 또는 custom |
| 동화·귀엽게·저학년 | fairytale | cute | clouds |
| 한국·전통·역사 | hanok | korean | petals |
| 운동회·대결 | sports | sports | pitch |
| 추리·방탈출 | detective | mystery → 위기 때 tension | fog |
| 자연·생물 | forest | nature | leaves |
| 바다·섬 | ocean | nature | sea |
| 차분·예쁘게·시 | fairytale/forest + `calm:true` | 끔 또는 nature | custom 정적 그림 |

**「AI 티」 피하기**: 보라-파랑 그라데이션 + 둥근 흰 카드 + 이모지 나열만으로 끝내지 않는다. 세계관 소품(두루마리·관제 패널·우체국 간판)을 패널 모양으로 쓰고, 색은 세계관에서 2~3개 뽑는다.

## 2. 그림 (외부 이미지 금지 → SVG·CSS·Canvas·이모지·팩)
- 캐릭터: 머리 크고 몸 작게(2~2.5등신), 굵은 외곽선(6~8), 눈 하이라이트, 표정 3종(기본·기쁨·슬픔). 단원 소품을 하나 들려 준다(우편 가방·전립·헬멧).
- 배경: 먼 층(하늘·산) → 중간(건물·섬) → 가까운 층(땅·풀) 3겹. 가까운 층만 살짝 움직인다.
- 시그니처 연출은 **그림이 바뀌는 것**으로: 불이 켜짐, 꽃이 핌, 배가 출항.
- 유명 캐릭터 요청은 비슷한 분위기의 오리지널로 (legal-advisory.md).

## 3. 소리
- 효과음은 엔진 이름으로 (`NG.sfx`), 새 소리는 `NG.defineSfx`. 차분 게임은 pop·flip·star 위주.
- 배경음악은 카운트다운 뒤 자동 시작(`music:false`로 끔). 긴장 장면은 `NG.music.setTempo(1.25)`.

## 4. 화려함 기준
| 순간 | 기본 | 차분(calm) |
|---|---|---|
| 문제 읽기 | 깨끗하게, 움직임 최소 | 같음 |
| 정답 | `NG.feedback(true, el)` + 시그니처 그림 변화 | 부드러운 반짝이 + 그림 변화 |
| 오답 | `NG.feedback(false, el)` + 정답 보여 주기 | 흔들림 없음, 「다시 볼까요」 |
| 3연속 | 콤보 배지(자동) | 없음 |
| 마지막 | 시그니처 대장면 → 결과 | 천천히 내리는 꽃잎 정도 |
- 「너무 정신없어」 → 효과 줄이기, 「밋밋해」 → 정답 순간만 키운다(문제 화면은 그대로).
