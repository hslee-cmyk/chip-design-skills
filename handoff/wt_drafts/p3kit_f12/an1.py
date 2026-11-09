import json,sys,re,collections
d=json.load(open(sys.argv[1],encoding='utf-8'))
EXCL=re.compile(r'^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)')
nf=[p for p,i in d['files'].items() if i.get('needs_change')]
inn=[p for p in nf if not EXCL.search(p)]; ex=[p for p in nf if EXCL.search(p)]
print('needs',len(nf),'outside_excl',len(inn),'excl',len(ex),ex)
def grp(p):
    A='skills/analog-gmid-design/assets/'
    if p.startswith(A+'tests/'): return 'A/tests/'+p[len(A+'tests/'):].split('/')[0] if '/' in p[len(A+'tests/'):] else 'A/tests/(root)'
    if p.startswith(A): return 'A/(root)'
    if p.startswith('workspaces/'): return '/'.join(p.split('/')[:2])
    return p.split('/')[0]
print(collections.Counter(grp(p) for p in inn))
shim=[p for p in inn if any(r['mod']!='stick_diagram' for r in d['files'][p]['need']) or any(b['mod']!='stick_diagram' for b in d['files'][p]['bare'])]
sdonly=[p for p in inn if p not in shim]
print('shim-importers',len(shim),'sd-name-only',len(sdonly)); print('sdonly',sdonly)
# forms
forms=collections.Counter(); multi=[]
for p in inn:
    i=d['files'][p]
    for r in i['need']: forms[(r['mod'],r['form'])]+=1
    for k,v in i['alias_dests'].items():
        if len(v)>1 and (k.split('@')[1]!='stick_diagram' or any(r['form']!='from' and r['mod']=='stick_diagram' for r in i['need'])):
            multi.append((p,k,v))
print(forms)
print('multi-dest aliases',len(multi))
for m in multi: print(' ',m)
print('d17'); 
for x in d['d17']: print(' ',x['file'].split('/')[-1],x['line'],x['mod'],x['name'],x['form'],x['def_file'],x['callers'])
print('sd_drop',d['sd_drop'])
