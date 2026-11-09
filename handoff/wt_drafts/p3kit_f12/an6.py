import json,sys
sys.path.insert(0,'C:/g202/r/tools/gates')
import reachability as rch
A='skills/analog-gmid-design/assets/'
idx=rch.SourceIndex(rch.read_tree('C:/g202/r','4e932be',rch.SOURCE_GLOBS))   # FU+개정 판(엔진 = dd60db6 + FU 두 줄), G1 시제품 색인은 작업 트리 tools/gates
plan=json.load(open('C:/g202/out/plan_d31h.json',encoding='utf-8'))['assignment']
d=json.load(open('C:/g202/out/callers_m9f.json',encoding='utf-8'))
SR=A+'sizing_recipe.py'
gn=idx.global_names(SR)
for x in d['d17']:
    nm=x['name']
    us=[k for k,v in gn.items() if nm in v and idx.binding_origin(SR,nm)[0] in ('def',)]
    mods=sorted({plan.get('sizing_recipe.py::'+k,{}).get('mod','?') for k in us})
    print(x['file'].split('/')[-1], x['line'], nm, 'base-SR readers->', mods, 'callers', x['callers'], 'SAME' if mods==x['callers'] else 'DIFF')
