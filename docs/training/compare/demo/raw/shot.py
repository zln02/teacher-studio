import sys,json
from playwright.sync_api import sync_playwright
out={}
with sync_playwright() as p:
    try: b=p.chromium.launch(args=['--mute-audio'])
    except Exception as e:
        print('chromium fail',e); b=p.chromium.launch(channel='chrome',args=['--mute-audio'])
    for c,Q,RUN,ASK,INP in [('bare','#q','#run',None,'#q'),('h','#askInput','#runBtn',None,'#askInput')]:
        pg=b.new_page(viewport={'width':1600,'height':900})
        reqs=[];errs=[]
        pg.on('request',lambda r,reqs=reqs: reqs.append(r.url) if r.url.startswith('http') else None)
        pg.on('pageerror',lambda e,errs=errs: errs.append(str(e)))
        pg.on('console',lambda m,errs=errs: errs.append('C:'+m.text) if m.type=='error' else None)
        pg.goto('file:///C:/Users/User/AppData/Local/Temp/claude/d85f5c5f00edac37/c8098317-2fbb-4131-bf8f-07218752ac6e/scratchpad/demo/run-%s/coding-helper.html'%c)
        pg.wait_for_timeout(1500)
        pg.screenshot(path='%s-1.png'%c)
        # run default code
        pg.click(RUN); pg.wait_for_timeout(6000)
        if c=='bare':
            # input() prompt may appear
            pg.screenshot(path='bare-2.png')
        else:
            pg.screenshot(path='h-2.png')
        pg.fill(INP,'반복문이 뭐예요?'); pg.keyboard.press('Enter'); pg.wait_for_timeout(1500)
        pg.screenshot(path='%s-3.png'%c)
        out[c]={'reqs':reqs,'errs':errs,'text':pg.inner_text('body')[:1500]}
        pg.close()
    b.close()
json.dump(out,open('shot.json','w'),ensure_ascii=False,indent=1)
