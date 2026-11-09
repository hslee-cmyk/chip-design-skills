import difflib,re
a=open('gb_6a7e1fe3.md',encoding='utf-8').read().split('\n')
b=open('gb_d89910ed.md',encoding='utf-8').read().split('\n')
o=open('marker_B.out.txt','w',encoding='utf-8')
ORD='(?:첫|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|열한|열두|열둘|열셋|열넷|열다섯|열여섯|열일곱|열여덟|열아홉|스무|스물한)째'
PAT=[r'v6\.38\.4 '+ORD+r' 커밋( (단순화|백로그 재감사|정정|P9 검증 [A-Za-z0-9·]+))?',r'계획 검증 \d+( [A-Za-z]+-?\d+(·[A-Za-z]+-?\d+)*)?(으로|로)?',r'P9 검증 [A-Za-z0-9·]+',r'v6\.38\.4 '+ORD]
def strip(s):
    for p in PAT: s=re.sub(p,'',s)
    return s
tok=lambda s: re.findall(r'\S+|\s+',s)
SKIP={11,12,553,555,2349,2350,2351,2352,2353,2354,2355,2356,2357}
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
n=0;res=0
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    for k in range(min(i2-i1,j2-j1)):
        if (i1+k+1) in SKIP: continue
        ta,tb=tok(a[i1+k]),tok(b[j1+k])
        for oo,x1,x2,y1,y2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
            if oo=='equal': continue
            d=''.join(ta[x1:x2]); ins=''.join(tb[y1:y2]); n+=1
            rd=re.sub(r'[\s()\-:;,·.\*]','',strip(d)); ri=re.sub(r'[\s()\-:;,·.\*]','',strip(ins))
            if rd!=ri:
                res+=1; o.write(f'L{i1+k+1} RESIDUAL del={d[:300]!r} ins={ins[:300]!r} | rd={rd[:120]!r} ri={ri[:120]!r}\n')
o.write(f'edits {n}, residual(non-marker) {res}\n')
# count remaining markers in final plan body
fb='\n'.join(b)
for p in [r'v6\.38\.4 '+ORD+' 커밋',r'계획 검증 \d+']:
    o.write(f'remaining {p!r}: total {len(re.findall(p,fb))}, in Status L11: {len(re.findall(p,b[10]))}\n')
