import difflib,re,hashlib
a=open('gb_6a7e1fe3.md',encoding='utf-8').read().split('\n')
b=open('gb_d89910ed.md',encoding='utf-8').read().split('\n')
H=open('gbh_d89910ed.md',encoding='utf-8').read()
Hl=H.split('\n')
o=open('preserve_B.out.txt','w',encoding='utf-8')
# 1. Status chain
old11=a[10]; idx=old11.find('이전 판: **Plan v6.38.3')
if idx<0: idx=old11.find('이전 판:')
chain=old11[idx:]
h1532=Hl[1531]
o.write(f'status chain old len chars={len(chain)} bytes={len(chain.encode())} sha={hashlib.sha256(chain.encode()).hexdigest()[:16]}\n')
o.write(f'history 1532 len chars={len(h1532)} bytes={len(h1532.encode())} sha={hashlib.sha256(h1532.encode()).hexdigest()[:16]}\n')
o.write(f'exact equal: {chain==h1532}; chain in H: {chain in H}\n')
if chain!=h1532:
    sm=difflib.SequenceMatcher(None,chain,h1532,autojunk=False)
    for op in sm.get_opcodes():
        if op[0]!='equal': o.write(f'  diff {op} old={chain[op[1]:op[2]][:200]!r} new={h1532[op[3]:op[4]][:200]!r}\n')
# what's before chain in old status vs new status
o.write('old status prefix tail: '+old11[max(0,idx-300):idx]+'\n')
# 2. deleted spans
tok=lambda s: re.findall(r'\S+|\s+',s)
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
miss=0;tot=0
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    for k in range(min(i2-i1,j2-j1)):
        ta,tb=tok(a[i1+k]),tok(b[j1+k])
        for oo,x1,x2,y1,y2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
            if oo in('delete','replace'):
                d=''.join(ta[x1:x2]).strip()
                if len(d)<60 or i1+k==10: continue
                tot+=1
                # sample 50-char windows
                ws=[d[p:p+50] for p in range(0,max(1,len(d)-50),max(1,(len(d)-50)//5 or 1))][:6]
                hit=sum(1 for w in ws if w in H)
                if hit<len(ws): miss+=1
                o.write(f'L{j1+k+1} len={len(d)} samples {hit}/{len(ws)} :: {d[:150]}\n')
o.write(f'spans>=60: {tot}, with missing samples: {miss}\n')
