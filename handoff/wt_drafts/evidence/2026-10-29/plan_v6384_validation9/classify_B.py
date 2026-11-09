import difflib,re,sys,json
a=open('gb_6a7e1fe3.md',encoding='utf-8').read().split('\n')
b=open('gb_d89910ed.md',encoding='utf-8').read().split('\n')
out=open('B_classify.txt','w',encoding='utf-8')
tok=lambda s: re.findall(r'\S+|\s+',s)
MARK=re.compile(r'(v6\.38\.4|커밋|계획 검증|검증 \d|열\S*째|스무째|스물\S*째|아홉째|여덟째|일곱째|단순화|백로그 재감사|[A-Z]\d*-?\d*|M\d|m\d|--|[();,·:]|\s)')
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
n=0;cnt={'marker_only':0,'other':0}
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    if i2-i1!=j2-j1:
        out.write(f'### UNEVEN old {i1+1}-{i2} new {j1+1}-{j2}\n'); 
        for x in a[i1:i2]: out.write(' - '+x[:1500]+'\n')
        for x in b[j1:j2]: out.write(' + '+x[:1500]+'\n')
        continue
    for k in range(i2-i1):
        ta,tb=tok(a[i1+k]),tok(b[j1+k])
        s2=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
        for o,x1,x2,y1,y2 in s2.get_opcodes():
            if o=='equal': continue
            d=''.join(ta[x1:x2]); ins=''.join(tb[y1:y2]); n+=1
            out.write(f'[{n}] L{j1+k+1} {o}: -<<{d[:1200]}>> +<<{ins[:600]}>>\n')
out.write(f'total edits {n}\n')
