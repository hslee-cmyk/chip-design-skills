import json,re,collections
d=json.load(open('C:/g202/out/callers_m9f.json',encoding='utf-8'))
E=re.compile(r'^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)')
A='skills/analog-gmid-design/assets/'
nf=[p for p,i in d['files'].items() if i.get('needs_change') and not E.search(p)]
def role(p):
    if p.startswith(A+'tests/tools/'): return 'code(tests/tools)'
    if p.startswith(A+'tests/'): return 'test'
    if p=='workspaces/run_harness.py': return 'code(run_harness)'
    if p.startswith('workspaces/'): return 'out-of-role(workspaces/<dir>)'
    return 'other'
c=collections.Counter(role(p) for p in nf); print(c)
for p in nf:
    if role(p) in ('code(tests/tools)','out-of-role(workspaces/<dir>)','other'): print(' ',role(p),p)
names=collections.Counter(); dests=collections.Counter()
for p in nf:
    for r in d['files'][p]['need']:
        names[(r['mod'],r['name'])]+=1; dests[r.get('dest')]+=1
print('distinct (mod,name)',len(names)); print('dest counts',dests)
# test files with B-group (contracts)
print([p.split('/')[-1] for p in nf if '/contracts/' in p])
print([p.split('/')[-1] for p in nf if '/unit/' in p])
print([p.split('/')[-1] for p in nf if p.startswith(A+'tests/') and p.count('/')==4])
