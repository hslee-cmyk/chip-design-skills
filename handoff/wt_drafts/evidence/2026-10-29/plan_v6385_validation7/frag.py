import difflib,re,sys
O=sys.argv[1]
def rd(p): return open(p,encoding='utf-8').read().split('\n')
def toks(s): return re.split(r'(?<=[.;)])\s+|\s+--\s+|<br>', s)
for kind,a,b in [('plan','plan_9afc3730.md','plan_8cbf8306.md'),('hist','hist_9afc3730.md','hist_8cbf8306.md')]:
    A=rd(f'{O}/{a}');B=rd(f'{O}/{b}')
    out=open(f'{O}/frag_{kind}.txt','w',encoding='utf-8')
    sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
    for op,i1,i2,j1,j2 in sm.get_opcodes():
        if op=='equal': continue
        out.write(f'\n######## {op} old {i1+1}-{i2} new {j1+1}-{j2}\n')
        ta=[t for l in A[i1:i2] for t in toks(l)]; tb=[t for l in B[j1:j2] for t in toks(l)]
        s2=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
        for o,x1,x2,y1,y2 in s2.get_opcodes():
            if o=='equal': continue
            for t in ta[x1:x2]: out.write('- '+t+'\n')
            for t in tb[y1:y2]: out.write('+ '+t+'\n')
            out.write('~~\n')
