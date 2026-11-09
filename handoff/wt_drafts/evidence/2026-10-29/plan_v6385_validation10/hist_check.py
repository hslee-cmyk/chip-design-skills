import re,sys
L=open('segdiff_plan_974adc68_6a31bf1c.txt',encoding='utf-8').read().split('\n')
newp=open('plan_6a31bf1c.md',encoding='utf-8').read()
H=open('hist_6a31bf1c.md',encoding='utf-8').read().split('\n')
Hn='\n'.join(H[1930:1942])
out=open('hist_check.txt','w',encoding='utf-8')
for l in L:
    if l.startswith('  - '):
        s=l[4:].strip()
        k=s[:60]
        st='PLAN' if s in newp else ('HIST' if s in Hn else ('HIST60' if k in Hn else 'MISS'))
        out.write(f'{st}\t{s[:160]}\n')
out.close()
