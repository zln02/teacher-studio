import json,html,re,asyncio,pathlib,sys
from playwright.async_api import async_playwright
R=pathlib.Path(sys.argv[1]); O=pathlib.Path(sys.argv[2])
def pptx_html(path,outdir):
    from pptx import Presentation
    p=Presentation(path); W,H=p.slide_width,p.slide_height
    n=0
    for i,s in enumerate(p.slides):
        bg='#fff'
        try:
            m=s._element.cSld.xpath('./p:bg//a:srgbClr/@val')
            if m: bg='#'+m[0]
        except Exception: pass
        parts=[]
        for sh in s.shapes:
            st='left:%.2f%%;top:%.2f%%;width:%.2f%%;height:%.2f%%;'%(sh.left/W*100,sh.top/H*100,sh.width/W*100,sh.height/H*100)
            try:
                m=sh._element.spPr.xpath('./a:solidFill/a:srgbClr/@val')
                if m: st+='background:#%s;'%m[0]
                g=sh._element.spPr.xpath('./a:prstGeom/@prst')
                if g and g[0]=='ellipse': st+='border-radius:50%;'
                elif g and g[0]=='roundRect': st+='border-radius:2cqw;'
            except Exception: pass
            t=''
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    r=para.runs
                    if not r: t+='<div>&nbsp;</div>'; continue
                    f=r[0].font; sz=f.size.pt if f.size else 18
                    col='#333'
                    m=para._p.xpath('.//a:rPr/a:solidFill/a:srgbClr/@val')
                    if m: col='#'+m[0]
                    al=para._p.xpath('./a:pPr/@algn'); al=al[0] if al else 'l'
                    t+='<div style="text-align:%s;font-size:%.2fcqw;color:%s;font-weight:%s">%s</div>'%({'ctr':'center','r':'right'}.get(al,'left'),sz/960*100,col,'700' if f.bold else '400',html.escape(para.text))
            parts.append('<div class=sh style="%s">%s</div>'%(st,t))
        h='<meta charset=utf-8><style>body{margin:0;background:#222;display:flex;justify-content:center;align-items:center;height:100vh}.sl{position:relative;height:100vh;container-type:inline-size;overflow:hidden;font-family:"Malgun Gothic",sans-serif}.sh{position:absolute;overflow:hidden;line-height:1.25}</style><div class=sl style="background:%s;aspect-ratio:%d/%d">%s</div>'%(bg,W,H,''.join(parts))
        (outdir/('_pp-%d.html'%i)).write_text(h,encoding='utf-8'); n+=1
    return n
def md2(t):
    t=html.escape(t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'(https?://[^\s)\]]+)',r'<u>\1</u>',t)
    return t.replace('\n','<br>')
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(channel='chrome',args=['--mute-audio'])
        u=lambda p:pathlib.Path(p).resolve().as_uri()
        async def pg(url,w=1600,h=900):
            p=await b.new_page(viewport={'width':w,'height':h});await p.goto(url);await p.wait_for_timeout(2500);return p
        # law
        j=json.load(open(R/'law/_result.json',encoding='utf-8'))
        css='body{margin:0;background:#eef1f6;font-family:"Malgun Gothic",sans-serif}.card{width:1100px;margin:30px auto;background:#fff;border-radius:18px;padding:34px 44px;box-shadow:0 4px 24px #0002;font-size:19px;line-height:1.6;color:#1b2333}.tag{display:inline-block;background:#1b2333;color:#fff;border-radius:8px;padding:3px 14px;font-size:16px;margin-bottom:12px}.q{font-size:22px;font-weight:700;margin-bottom:12px;color:#445}'
        (R/'law/_card.html').write_text(f'<meta charset=utf-8><style>{css}</style><div class=card><div class=tag>교사 스튜디오 v2 (harness)</div><div class=q>가정통신문에 인터넷에서 찾은 캐릭터 그림 써도 돼?</div>{md2(j["result"])}</div>',encoding='utf-8')
        p=await pg(u(R/'law/_card.html'));await p.screenshot(path=str(O/'law-harness-v2.png'),full_page=True)
        # game
        g=sorted((R/'game').glob('light-review.html'))[0]
        p=await pg(u(g));await p.screenshot(path=str(O/'game-harness-v2.png'))
        await p.get_by_text('시작').first.click();await p.wait_for_timeout(5000);await p.screenshot(path=str(O/'game-harness-v2-key.png'))
        # data
        h=list((R/'data').glob('*.html'))[0]
        p=await pg(u(h));await p.screenshot(path=str(O/'data-harness-v2.png'))
        await p.mouse.wheel(0,900);await p.wait_for_timeout(1200);await p.screenshot(path=str(O/'data-harness-v2-key.png'))
        print('dataH',await p.evaluate('document.body.scrollHeight'))
        # pptx
        n=pptx_html(str(list((R/'parents').glob('*.pptx'))[0]),R/'parents')
        for i in range(n):
            p=await pg(u(R/'parents'/('_pp-%d.html'%i)));await p.screenshot(path=str(R/'parents'/('_pp-%d.png'%i)))
        import PIL.Image as I
        ims=[I.open(R/'parents'/('_pp-%d.png'%i)).crop((0,0,1600,900)).resize((800,450)) for i in range(n)]
        sheet=I.new('RGB',(1600,450*((n+1)//2)))
        for i,im in enumerate(ims): sheet.paste(im,((i%2)*800,(i//2)*450))
        sheet.save(O/'parents-harness-v2.png'); 
        I.open(R/'parents'/'_pp-2.png').save(O/'parents-harness-v2-key.png')
        await b.close()
asyncio.run(main())
