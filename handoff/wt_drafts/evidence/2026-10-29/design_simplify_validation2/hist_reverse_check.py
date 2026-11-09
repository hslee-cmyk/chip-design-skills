# 역방향: design 이력 H 절의 원문 줄(40자 이상)이 옮기기 직전 판(각 커밋의 부모)의 40·41·42 본문에 그대로 있었는지 -- 이력에서 문언이 바뀌었는지 확인
import re,subprocess,json
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115'
show=lambda r,p: subprocess.run(['git','-C',W,'show',f'{r}:{p}'],capture_output=True).stdout.decode('utf-8')
docs=['40-engine','41-gain-budget','42-gap-checklist']
src=''
for c in ['09e5b13a','028bea62','7e57ee63','c7a51e41','2d84ffbb','ca5e8557','4e31a88b','e3dc6585','ad63532e']:
    for d in docs: src+=show(c,f'docs/02-design/features/gain-budget-gmid-sizing.{d}.design.md')+'\n'
norm=lambda s: re.sub(r'\s+',' ',s).strip()
S=norm(src)
hist=show('190e764c','docs/02-design/features/gain-budget-gmid-sizing.design.history.md')
secs=re.split(r'\n(?=## H4[01]-\d\d)',hist)
res=[]
for s in secs:
    m=re.match(r'## (H4[01]-\d\d)',s)
    if not m: continue
    body=s.split('\n')[1:]
    lines=[l for l in body if len(norm(l))>=40]
    miss=[]
    for l in lines:
        n=norm(l)
        if n in S: continue
        # allow markdown list/table prefix differences
        n2=norm(re.sub(r'^[-*>\s]+','',l))
        if n2 in S: continue
        parts=[norm(p) for p in re.split(r'\|',l) if len(norm(p))>=30]
        if parts and all(p in S for p in parts): continue
        miss.append(n[:200])
    res.append({'id':m.group(1),'lines':len(lines),'missing':len(miss),'examples':miss[:3]})
json.dump(res,open('hist_reverse_check.out.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for r in res: print(r['id'],r['lines'],r['missing'],r['examples'][:2])
