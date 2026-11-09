# 절(###/####) 단위 분량: 09e5b13a(2차 전) 대 190e764c(2차 뒤), 41·40
import re,sys,json
def secs(path):
    L=open(path,encoding='utf-8').read().split('\n'); out=[];cur=('(머리)',0);size=0
    for l in L:
        if re.match(r'#{2,4} ',l):
            out.append((cur[0],size)); cur=(l.strip()[:70],0); size=0
        size+=len(l.encode('utf-8'))+1
    out.append((cur[0],size)); return out
res={}
for d in ['40','41']:
    a=dict(); 
    for n,s in secs(f'{d}_09e5b13a.md'): a[n]=a.get(n,0)+s
    b=dict()
    for n,s in secs(f'{d}_190e764c.md'): b[n]=b.get(n,0)+s
    rows=[(n,a.get(n,0),b.get(n,0)) for n in dict.fromkeys(list(a)+list(b))]
    rows.sort(key=lambda r:-r[2])
    res[d]=rows
    print('==',d,'total',sum(a.values()),'->',sum(b.values()))
    for n,x,y in rows[:22]: print(f'{y:8d} {x:8d} {y-x:+8d}  {n}')
json.dump(res,open('section_sizes.out.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
