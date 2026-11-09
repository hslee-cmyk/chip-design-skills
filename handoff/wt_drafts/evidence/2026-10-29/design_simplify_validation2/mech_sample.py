# 기계 정리 세 커밋에서 바뀐 조각 표본(커밋당 16개, seed 고정)을 앞뒤 문맥과 함께 덤프
import json,subprocess,difflib,random
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115'
def show(r,d): return subprocess.run(['git','-C',W,'show',f'{r}:docs/02-design/features/gain-budget-gmid-sizing.{d}.design.md'],capture_output=True).stdout.decode('utf-8').split('\n')
random.seed(20261029)
out=open('mech_sample.out.md','w',encoding='utf-8')
n=0
for c in ['4e31a88b','e3dc6585','ad63532e']:
    r=json.load(open('mech_'+c+'.json',encoding='utf-8'))
    segs=[]
    for x in r:
        a=show(c+'~1',x['doc'])[x['line']-1] if False else None
    cache={}
    for x in r:
        d=x['doc']
        if d not in cache: cache[d]=(show(c+'~1',d),show(c,d))
        a=cache[d][0][x['line']-1]; b=cache[d][1][x['line']-1]
        sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
        for op,i1,i2,j1,j2 in sm.get_opcodes():
            if op!='equal': segs.append((d,x['line'],a[max(0,i1-150):i2+100],b[max(0,j1-150):j1+100]))
    pick=random.sample(segs,min(16,len(segs)))
    for d,l,o,nw in pick:
        n+=1
        out.write(f'### S{n:02d} {c} {d}:{l}\nOLD: {o}\nNEW: {nw}\n\n')
print(n)
