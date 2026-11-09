import subprocess, difflib, sys, re
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384'
A,B='c9340f8b','3a02b206'
out=open(sys.argv[1],'w',encoding='utf-8')
for f in ['docs/01-plan/features/gain-budget-gmid-sizing.plan.md','docs/01-plan/features/headroom-chain.plan.md','docs/01-plan/features/gain-budget-gmid-sizing.history.md','docs/01-plan/features/headroom-chain.history.md']:
    a=subprocess.run(['git','-C',W,'show',f'{A}:{f}'],capture_output=True).stdout.decode('utf-8').splitlines()
    b=subprocess.run(['git','-C',W,'show',f'{B}:{f}'],capture_output=True).stdout.decode('utf-8').splitlines()
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal': continue
        out.write(f'\n===== {f} {tag} old {i1+1}-{i2} new {j1+1}-{j2}\n')
        if tag=='replace' and i2-i1==j2-j1:
            for x,y in zip(a[i1:i2],b[j1:j2]):
                ta=re.split(r'(\s+)',x); tb=re.split(r'(\s+)',y)
                s=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
                for t,p1,p2,q1,q2 in s.get_opcodes():
                    if t=='equal': continue
                    ctx=''.join(ta[max(0,p1-12):p1])
                    out.write(f'  ...{ctx[-120:]}\n   - [{"".join(ta[p1:p2])}]\n   + [{"".join(tb[q1:q2])}]\n')
        else:
            for y in b[j1:j2]: out.write('+ '+y+'\n')
            for x in a[i1:i2]: out.write('- '+x[:3000]+'\n')
