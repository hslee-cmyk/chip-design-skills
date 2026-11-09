# status_only_names.txt의 이름마다: 현 design 40·41·42(190e764c), 계획 plan.md, 이력 H40-01/H41-16 문맥, 엔진(master, integ/it12) 출현 수
import re,subprocess,json
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115'; M='C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills'
src=open('C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/design_v1152/simplify/status_only_names.txt',encoding='utf-8').read()
names=[]
for line in src.split('\n'):
    if line.startswith('#') or not line.strip(): continue
    for n in line.split(' | '):
        n=n.strip()
        if n and n not in names: names.append(n)
docs={d:open(f'{d}_190e764c.md',encoding='utf-8').read() for d in ['40','41','42']}
plan=subprocess.run(['git','-C',W,'show','190e764c:docs/01-plan/features/gain-budget-gmid-sizing.plan.md'],capture_output=True).stdout.decode('utf-8')
hist=subprocess.run(['git','-C',W,'show','190e764c:docs/02-design/features/gain-budget-gmid-sizing.design.history.md'],capture_output=True).stdout.decode('utf-8')
def eng(ref,n):
    r=subprocess.run(['git','-C',M,'grep','-F','-c',n,ref,'--','skills/analog-gmid-design/gmid_engine/'],capture_output=True).stdout.decode('utf-8','replace')
    tot=0;files=[]
    for l in r.strip().split('\n'):
        if not l: continue
        p,c=l.rsplit(':',1); tot+=int(c); files.append(p.split('gmid_engine/')[-1])
    nt=[f for f in files if '/tests/' not in f and not f.startswith('tests/')]
    return tot,nt[:4]
rows=[]
for n in names:
    key=n
    r={'name':n,'40':docs['40'].count(key),'41':docs['41'].count(key),'42':docs['42'].count(key),'plan':plan.count(key),'hist':hist.count(key)}
    r['eng_master'],r['eng_master_src']=eng('master',key)
    r['eng_it12'],r['eng_it12_src']=eng('integ/it12',key)
    # context in history (first occurrence)
    i=hist.find(key); r['hist_ctx']=hist[max(0,i-140):i+len(key)+100].replace('\n',' ') if i>=0 else ''
    i=plan.find(key); r['plan_ctx']=plan[max(0,i-140):i+len(key)+100].replace('\n',' ') if i>=0 else ''
    rows.append(r)
with open('names_check.out.jsonl','w',encoding='utf-8') as f:
    for r in rows: f.write(json.dumps(r,ensure_ascii=False)+'\n')
print(len(names))
for r in rows: print(f"{r['name'][:60]:60s} d40={r['40']} d41={r['41']} d42={r['42']} plan={r['plan']} hist={r['hist']} eng_m={r['eng_master']} {r['eng_master_src']} it12={r['eng_it12']} {r['eng_it12_src']}")
