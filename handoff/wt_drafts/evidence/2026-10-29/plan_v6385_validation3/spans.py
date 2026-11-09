import difflib,sys,re
O=sys.argv[1]
out=open(O+'/spans.txt','w',encoding='utf-8')
for name in ['plan','history']:
    a=open(f'{O}/old_gain-budget-gmid-sizing.{name}.md',encoding='utf-8').read().split('\n')
    b=open(f'{O}/new_gain-budget-gmid-sizing.{name}.md',encoding='utf-8').read().split('\n')
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal':continue
        out.write(f'=== {name} {tag} old {i1+1}-{i2} new {j1+1}-{j2}\n')
        if tag=='replace' and i2-i1==j2-j1:
            for k in range(i2-i1):
                wa=re.split(r'(\s+)',a[i1+k]); wb=re.split(r'(\s+)',b[j1+k])
                s2=difflib.SequenceMatcher(None,wa,wb,autojunk=False)
                for t,x1,x2,y1,y2 in s2.get_opcodes():
                    if t=='equal':continue
                    ctx=''.join(wa[max(0,x1-12):x1])
                    out.write(f'  [L{j1+k+1}] ...{ctx[-120:]}\n    - {"".join(wa[x1:x2])}\n    + {"".join(wb[y1:y2])}\n')
        else:
            for k in range(j1,j2): out.write(f'  +L{k+1}: {b[k]}\n')
            for k in range(i1,i2): out.write(f'  -L{k+1}: {a[k][:300]}\n')
