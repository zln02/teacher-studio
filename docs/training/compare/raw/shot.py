import sys,json,html,asyncio,pathlib
from playwright.async_api import async_playwright
R=pathlib.Path('runs'); O=pathlib.Path('out')
def pptx_html(path,out,upto=None):
    from pptx import Presentation
    from pptx.util import Emu
    p=Presentation(path); W,H=p.slide_width,p.slide_height
    sl=[]
    for s in p.slides:
        bg='#fff'
        try:
            f=s.background.fill
            if f.type==1: bg='#%s'%f.fore_color.rgb
        except Exception: pass
        parts=[]
        for sh in s.shapes:
            st='left:%.2f%%;top:%.2f%%;width:%.2f%%;height:%.2f%%;'%(sh.left/W*100,sh.top/H*100,sh.width/W*100,sh.height/H*100)
            try:
                if sh.fill.type==1: st+='background:#%s;'%sh.fill.fore_color.rgb
            except Exception: pass
            t=''
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    r=para.runs
                    if not r: continue
                    f=r[0].font; sz=f.size.pt if f.size else 18
                    col='#333'
                    try: col='#%s'%f.color.rgb
                    except Exception: pass
                    t+='<div style="font-size:%.2fcqw;color:%s;font-weight:%s">%s</div>'%(sz/720*100,col,'700' if f.bold else '400',html.escape(para.text))
            parts.append('<div class=sh style="%s">%s</div>'%(st,t))
        sl.append('<div class=sl style="background:%s;aspect-ratio:%d/%d">%s</div>'%(bg,W,H,''.join(parts)))
    open(out,'w',encoding='utf-8').write('<meta charset=utf-8><style>body{margin:0;background:#222;display:flex;justify-content:center;align-items:center;height:100vh}.sl{position:relative;height:100vh;container-type:inline-size;overflow:hidden;font-family:"Malgun Gothic",sans-serif}.sh{position:absolute;overflow:hidden;line-height:1.25}</style>'+''.join(sl[:1])+'')
    # per-slide files
    for i,x in enumerate(sl):
        open(str(out).replace('.html','-%d.html'%i),'w',encoding='utf-8').write('<meta charset=utf-8><style>body{margin:0;background:#222;display:flex;justify-content:center;align-items:center;height:100vh}.sl{position:relative;height:100vh;container-type:inline-size;overflow:hidden;font-family:"Malgun Gothic",sans-serif}.sh{position:absolute;overflow:hidden;line-height:1.25}</style>'+x)
    return len(sl)
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(channel='chrome',args=['--mute-audio'])
        async def shot(url,name,pre=None):
            pg=await b.new_page(viewport={'width':1600,'height':900})
            await pg.goto(url); await pg.wait_for_timeout(2500)
            await pg.screenshot(path=str(O/(name+'.png')))
            if pre:
                try: await pre(pg)
                except Exception as e: print('pre fail',name,e)
                await pg.wait_for_timeout(1500)
                await pg.screenshot(path=str(O/(name+'-key.png')))
            await pg.close()
        async def clickstart(pg):
            await pg.get_by_text('시작').first.click()
        async def nextslides(pg):
            for _ in range(2):
                await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(1500)
        u=lambda p:pathlib.Path(p).resolve().as_uri()
        await shot(u(R/'game/bare/light_game.html'),'game-bare',clickstart)
        await shot(u(R/'game/harness/light-review.html'),'game-harness',clickstart)
        await shot(u(R/'parents/harness/학부모총회.html'),'parents-harness',nextslides)
        n=pptx_html(str(R/'parents/bare/학부모총회_발표자료.pptx'),R/'parents/bare/_render.html')
        await shot(u(R/'parents/bare/_render-0.html'),'parents-bare')
        await shot(u(R/'parents/bare/_render-2.html'),'parents-bare-key')
        await shot(u(R/'data/bare/class_grade_summary.md'),'x') if False else None
        await shot(u(R/'data/harness/성적분석.html'),'data-harness')
        await b.close()
asyncio.run(main())
