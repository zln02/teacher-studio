import json,html,re,asyncio,pathlib
import openpyxl
from playwright.async_api import async_playwright
R=pathlib.Path('runs');O=pathlib.Path('out')
def md2(t):
    t=html.escape(t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'(https?://[^\s)\]]+)',r'<u>\1</u>',t)
    return t.replace('\n','<br>')
css='body{margin:0;background:#eef1f6;font-family:"Malgun Gothic",sans-serif}.card{width:1100px;margin:30px auto;background:#fff;border-radius:18px;padding:34px 44px;box-shadow:0 4px 24px #0002;font-size:19px;line-height:1.6;color:#1b2333}.tag{display:inline-block;background:#1b2333;color:#fff;border-radius:8px;padding:3px 14px;font-size:16px;margin-bottom:12px}.q{font-size:22px;font-weight:700;margin-bottom:12px;color:#445}'
for k in ['bare','harness']:
    j=json.load(open(R/f'law-plain/{k}/_result.json',encoding='utf-8'))
    open(R/f'law-plain/{k}/_card.html','w',encoding='utf-8').write(f'<meta charset=utf-8><style>{css}</style><div class=card><div class=tag>{"일반 AI (bare)" if k=="bare" else "교사 스튜디오 (harness)"}</div><div class=q>가정통신문에 인터넷에서 찾은 캐릭터 그림 써도 돼?</div>{md2(j["result"])}</div>')
# data-bare: xlsx sheet dump
wb=openpyxl.load_workbook(R/'data/bare/class_grade_analysis.xlsx')
h='<meta charset=utf-8><style>body{margin:0;background:#fff;font-family:"Malgun Gothic",sans-serif;padding:18px 30px;font-size:14px}table{border-collapse:collapse;margin:6px 0 14px}td{border:1px solid #bbb;padding:3px 10px}h3{margin:6px 0;color:#1f4e79}.sn{background:#217346;color:#fff;padding:2px 10px;font-size:13px}</style><div class=sn>class_grade_analysis.xlsx — 시트 값 재현(차트 2개는 이 화면에 포함 안 됨)</div>'
for ws in list(wb)[:3]:
    h+=f'<h3>시트: {ws.title}</h3><table>'
    for i,row in enumerate(ws.iter_rows(values_only=True)):
        if i>14: break
        h+='<tr>'+''.join(f'<td>{"" if v is None else (round(v,2) if isinstance(v,float) else html.escape(str(v)))}</td>' for v in row)+'</tr>'
    h+='</table>'
open(R/'data/bare/_render.html','w',encoding='utf-8').write(h)
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(channel='chrome',args=['--mute-audio'])
        u=lambda p:pathlib.Path(p).resolve().as_uri()
        async def pg(url):
            p=await b.new_page(viewport={'width':1600,'height':900});await p.goto(url);await p.wait_for_timeout(2000);return p
        for k in ['bare','harness']:
            p=await pg(u(R/f'law-plain/{k}/_card.html'));await p.screenshot(path=str(O/f'law-{k}.png'),full_page=True)
            print(k,await p.evaluate('document.body.scrollHeight'))
        p=await pg(u(R/'data/bare/_render.html'));await p.screenshot(path=str(O/'data-bare.png'))
        p=await pg(u(R/'parents/harness/학부모총회.html'))
        for _ in range(2): await p.keyboard.press('ArrowRight');await p.wait_for_timeout(1000)
        await p.wait_for_timeout(5000);await p.screenshot(path=str(O/'parents-harness-key.png'))
        p=await pg(u(R/'game/harness/light-review.html'))
        await p.get_by_text('시작').first.click();await p.wait_for_timeout(7000);await p.screenshot(path=str(O/'game-harness-key.png'))
        await b.close()
asyncio.run(main())
