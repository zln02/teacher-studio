import re,zipfile
src='out.hwpx'; dst='현장체험학습_안내_가정통신문.hwpx'
z=zipfile.ZipFile(src); order=z.infolist(); files={i.filename:z.read(i.filename) for i in order}
s=files['Contents/section0.xml'].decode(); h=files['Contents/header.xml'].decode()
def para(txt):
    m=re.search(r'<hp:p paraPrIDRef="(\d+)" styleIDRef="0"><hp:run charPrIDRef="(\d+)"><hp:t>'+re.escape(txt),s); assert m,txt; return m
g=lambda t,i:re.search(r'<hh:%s id="%s".*?</hh:%s>'%(t,i,t),h,re.S).group(0)
d=para('2026년 11월 20일'); sd=para('________초등학교장</hp:t>')
pid,cid=d.group(1),d.group(2); sid=sd.group(2)
npp=int(re.search(r'<hh:paraProperties itemCnt="(\d+)"',h).group(1)); ncp=int(re.search(r'<hh:charProperties itemCnt="(\d+)"',h).group(1))
P1,P2=npp,npp+1; C1,C2,C3=ncp,ncp+1,ncp+2
pc=g('paraPr',pid).replace('id="%s"'%pid,'id="%d"'%P1)
pc=re.sub(r'horizontal="\w+"','horizontal="CENTER"',pc,1); pc=re.sub(r'(<hc:prev value=")\d+',r'\g<1>600',pc,1)
pb=pc.replace('id="%d"'%P1,'id="%d"'%P2).replace('pageBreakBefore="0"','pageBreakBefore="1"')
h=h.replace('</hh:paraProperties>',pc+pb+'</hh:paraProperties>').replace('<hh:paraProperties itemCnt="%d"'%npp,'<hh:paraProperties itemCnt="%d"'%(npp+2))
c20,c24=g('charPr',cid),g('charPr',sid)
add=c20.replace('id="%s"'%cid,'id="%d"'%C1).replace('height="1200"','height="1600"')
add+=c24.replace('id="%s"'%sid,'id="%d"'%C2).replace('height="1200"','height="2000"')
add+=c24.replace('id="%s"'%sid,'id="%d"'%C3).replace('height="1200"','height="2800"')
h=h.replace('</hh:charProperties>',add+'</hh:charProperties>').replace('<hh:charProperties itemCnt="%d"'%ncp,'<hh:charProperties itemCnt="%d"'%(ncp+3))
n=0
def sub(pat,rep):
    global s,n
    s,k=re.subn(pat,rep,s); assert k==1,pat; n+=k
sub(r'<hp:p paraPrIDRef="\d+" styleIDRef="0"><hp:run charPrIDRef="\d+"><hp:t>(2026년 11월 20일</hp:t>)',r'<hp:p paraPrIDRef="%d" styleIDRef="0"><hp:run charPrIDRef="%d"><hp:t>\1'%(P1,C1))
sub(r'<hp:p paraPrIDRef="\d+" styleIDRef="0"><hp:run charPrIDRef="\d+"><hp:t>(________초등학교장</hp:t>)',r'<hp:p paraPrIDRef="%d" styleIDRef="0"><hp:run charPrIDRef="%d"><hp:t>\1'%(P1,C2))
sub(r'<hp:p paraPrIDRef="\d+" styleIDRef="0"><hp:run charPrIDRef="(\d+)"><hp:t>(✂ - - - 자르는 선 - - -</hp:t>)',r'<hp:p paraPrIDRef="%d" styleIDRef="0"><hp:run charPrIDRef="\1"><hp:t>\2'%P1)
sub(r'<hp:p paraPrIDRef="\d+" styleIDRef="2"><hp:run charPrIDRef="\d+"><hp:t>1\.<hp:tab[^>]*/></hp:t></hp:run><hp:run charPrIDRef="\d+"><hp:t>현장체험학습 참가 동의서</hp:t></hp:run></hp:p>',
    '<hp:p paraPrIDRef="%d" styleIDRef="0" pageBreak="1"><hp:run charPrIDRef="%d"><hp:t>현장체험학습 참가 동의서</hp:t></hp:run></hp:p>'%(P2,C3))
print('applied',n)
files['Contents/section0.xml']=s.encode(); files['Contents/header.xml']=h.encode()
with zipfile.ZipFile(dst,'w') as o:
    for i in order: o.writestr(i.filename,files[i.filename],compress_type=zipfile.ZIP_STORED if i.filename=='mimetype' else zipfile.ZIP_DEFLATED)
