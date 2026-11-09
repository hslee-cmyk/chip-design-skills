import sys
L=open('segdiff_plan_6a31bf1c_adb3686a.txt',encoding='utf-8').read().split('\n')
newp=open('plan_adb3686a.md',encoding='utf-8').read()
H=open('hist_adb3686a.md',encoding='utf-8').read()
out=open('hist_check.txt','w',encoding='utf-8')
for l in L:
    if l.startswith('  - '):
        s=l[4:].strip()
        k=s[:50]
        st='PLAN' if s in newp else ('HIST' if s in H else ('HIST50' if k in H else ('PLAN50' if k in newp else 'MISS')))
        out.write(f'{st}\t{s[:200]}\n')
out.close()
