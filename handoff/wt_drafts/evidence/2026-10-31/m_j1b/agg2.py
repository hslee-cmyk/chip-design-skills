import json, collections, sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
recs = [json.loads(l) for l in open('devices_j1b.jsonl', encoding='utf-8')]
IDS = ["1e-07", "1e-06", "1e-05", "0.0001", "0.001"]
def cnt_dev(vt, rule, idc, bud, point, tol, cls_filter=None, only_budget=False):
    out = collections.Counter()
    for r in recs:
        if only_budget and r['budget_m2'] is None: continue
        c = r['combos'].get(f"{vt}|{rule}|ID{idc}|{bud}")
        key = r['cls']
        out[(key,'N')] += 1
        if c['sd_nonempty'] == 0: out[(key,'empty')] += 1; continue
        n = c[point]['n']
        lk = c['leak_'+point][tol]
        if n and lk >= 0.5*n: out[(key,'maj')] += 1
        if lk > 0: out[(key,'any')] += 1
        if n < c['sd_nonempty']: out[(key,'ts_partial')] += 1
        if n == 0: out[(key,'ts_none')] += 1
    return out
def fmt(o):
    return f"S {o[('S','maj')]}/{o[('S','N')]} (any {o[('S','any')]}) F {o[('F','maj')]}/{o[('F','N')]} (any {o[('F','any')]})"
print("== ts leakage (t*), D2, tol=t1mV, budget circuits only (N=48)")
for rule in ("ga","na"):
  for bud in ("none","full","share"):
    for idc in IDS:
        print(rule,bud,idc, fmt(cnt_dev("D2",rule,idc,bud,'ts','t1mV',only_budget=True)), "ts_none", cnt_dev("D2",rule,idc,bud,'ts','t1mV',only_budget=True)[('S','ts_none')],cnt_dev("D2",rule,idc,bud,'ts','t1mV',only_budget=True)[('F','ts_none')])
print("== att leakage (na rule) D2 tol=t1mV all devices")
for idc in IDS[:1]+IDS[-1:]:
    print('na', idc, fmt(cnt_dev("D2","na",idc,"none",'att','t1mV')))
print("== moved by budget (ts != att) majority/any; budget circuits N=48")
def moved(vt, rule, idc, bud):
    o = collections.Counter()
    for r in recs:
        if r['budget_m2'] is None: continue
        c = r['combos'][f"{vt}|{rule}|ID{idc}|{bud}"]
        ne = c['sd_nonempty']
        o[(r['cls'],'N')] += 1
        if ne == 0: o[(r['cls'],'empty')] += 1; continue
        if c['moved'] >= 0.5*ne: o[(r['cls'],'maj')] += 1
        if c['moved'] > 0: o[(r['cls'],'any')] += 1
        if c['ts_missing'] > 0: o[(r['cls'],'missing_any')] += 1
        if c['ts_missing'] >= 0.5*ne: o[(r['cls'],'missing_maj')] += 1
    return o
for vt in ("D1@t1mV","D2P@t1mV","D2"):
  for rule in ("ga","na"):
    for bud in ("full","share"):
      print(vt, rule, bud, " | ".join(f"ID{i}: S {moved(vt,rule,i,bud)[('S','maj')]}/{moved(vt,rule,i,bud)[('S','N')]} F {moved(vt,rule,i,bud)[('F','maj')]}/{moved(vt,rule,i,bud)[('F','N')]} (miss S{moved(vt,rule,i,bud)[('S','missing_maj')]} F{moved(vt,rule,i,bud)[('F','missing_maj')]})" for i in IDS))
