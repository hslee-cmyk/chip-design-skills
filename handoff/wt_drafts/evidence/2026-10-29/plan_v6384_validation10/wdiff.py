import sys,difflib,re
a,b,out=sys.argv[1:4]
A=open(a,encoding='utf-8').read().split('\n');B=open(b,encoding='utf-8').read().split('\n')
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
tok=lambda s:re.findall(r'\s+|[^\s]+',s)
o=open(out,'w',encoding='utf-8')
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal':continue
    o.write(f'=== {op} old {i1+1}-{i2} new {j1+1}-{j2}\n')
    if op=='replace' and i2-i1==j2-j1:
        for k in range(i2-i1):
            x,y=tok(A[i1+k]),tok(B[j1+k]);s2=difflib.SequenceMatcher(None,x,y,autojunk=False)
            o.write(f'--- line old {i1+k+1} / new {j1+k+1}\n')
            for op2,p1,p2,q1,q2 in s2.get_opcodes():
                if op2=='equal':continue
                ctxb=''.join(x[max(0,p1-12):p1]);ctxa=''.join(x[p2:p2+12])
                o.write(f'  [{op2}] ...{ctxb}《-{"".join(x[p1:p2])}》《+{"".join(y[q1:q2])}》{ctxa}...\n')
    else:
        for k in range(i1,i2):o.write(f'- {k+1}: {A[k][:3000]}\n')
        for k in range(j1,j2):o.write(f'+ {k+1}: {B[k][:3000]}\n')
