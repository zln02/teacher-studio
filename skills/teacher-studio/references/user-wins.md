# User wins - switch table

| User says | You set | Caution line |
|---|---|---|
| 「번호도 보여 줘」「학번 그대로」 (data) | plan `"show_ids": true` | 「이 파일은 밖으로 보내지 마세요」 |
| 「가명으로/이름 라벨 보여 줘」 (data) | plan `"show_labels": true` | 「이 파일은 밖으로 보내지 마세요」 |
| 「양식으로」「빈칸 있는 틀」「빈칸으로 둬」 (slides, docs: otherwise unknowns are example values) | spec `"template_blanks": true` | 「빈칸은 쓰기 전에 채워 주세요」 |
| 「인터넷 연결해도 돼」「글꼴·영상 링크 써 줘」 | spec `"online": true` | 「인터넷이 있어야 제대로 열려요」 |
| 「글씨 작아도 돼」「이 배치 그대로」 (game) | spec `"waive": ["text_size"\|"overflow"\|"hud"\|"phone"]` | 「글자가 작거나 잘려 보일 수 있어요」 |
| 「이 문제 그대로」 (game) | `build.py --ok-content` | none |
