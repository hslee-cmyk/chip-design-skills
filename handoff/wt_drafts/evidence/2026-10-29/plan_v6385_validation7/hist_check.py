import sys
O=sys.argv[1]
H=open(f'{O}/hist_8cbf8306.md',encoding='utf-8').read()
Hn=H.replace('\|','|')
P=open(f'{O}/plan_8cbf8306.md',encoding='utf-8').read()
out=open(f'{O}/hist_check.txt','w',encoding='utf-8')
miss=0
for l in open(f'{O}/frag_plan.txt',encoding='utf-8'):
    if l.startswith('- '):
        t=l[2:].strip()
        if len(t)<4: continue
        ok = t in H or t in Hn
        inplan = t in P
        if not ok: miss+=1
        out.write(f"{'OK ' if ok else 'MISS'} {'(still in plan)' if inplan else ''} {t[:120]}\n")
out.write(f'miss={miss}\n')
