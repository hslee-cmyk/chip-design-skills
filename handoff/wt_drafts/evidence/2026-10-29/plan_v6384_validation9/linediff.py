import sys,difflib,re
a=open(sys.argv[1],encoding='utf-8').read().split('\n')
b=open(sys.argv[2],encoding='utf-8').read().split('\n')
out=open(sys.argv[3],'w',encoding='utf-8')
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
tok=lambda s: re.findall(r'\S+|\s+',s)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    out.write(f'=== {op} old {i1+1}-{i2} new {j1+1}-{j2} (oldlen {sum(len(x) for x in a[i1:i2])} newlen {sum(len(x) for x in b[j1:j2])})\n')
    if op=='replace' and i2-i1==j2-j1:
        for k in range(i2-i1):
            ta,tb=tok(a[i1+k]),tok(b[j1+k])
            s2=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
            for o,x1,x2,y1,y2 in s2.get_opcodes():
                if o=='equal': continue
                out.write(f'  [line old {i1+k+1}/new {j1+k+1}] {o}: -<<{"".join(ta[x1:x2])}>> +<<{"".join(tb[y1:y2])}>>\n')
    else:
        for x in a[i1:i2]: out.write(' - '+x[:3000]+('...' if len(x)>3000 else '')+'\n')
        for x in b[j1:j2]: out.write(' + '+x[:3000]+('...' if len(x)>3000 else '')+'\n')
