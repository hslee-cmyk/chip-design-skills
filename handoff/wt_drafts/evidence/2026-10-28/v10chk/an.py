import json,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
for l in open('out10.jsonl',encoding='utf-8'):
    r=json.loads(l); c=r['circuit']
    if 'error' in r: print(c,'ERROR',r['error'][-300:]); continue
    rt=r.get('rung_t'); calls=r['calls']
    root=[];pm=[];nc=[];inact=0
    for k in calls:
        conds=[x[1] for x in k['recs'] if x[0]=='macro_root_missing']
        codes={x[0] for x in k['recs']}
        tag=(k['t'] if k['t'] is None else round(k['t'],4), 'R' if k['refine'] else 'n', k['caller'])
        if 'target_not_reached_at_upper_limit' in conds: root.append(tag)
        if 'pm_target_not_met_within_ranges' in conds: pm.append(tag)
        if 'macro_nonconvergent' in codes: nc.append(tag)
        if 'macro_inactive' in codes: inact+=1
    rtr=[round(x,4) for x in rt] if rt else rt
    print(f"{c}: rungs={rtr} calls={len(calls)} inactive_calls={inact}")
    print("   root_missing:",root)
    print("   pm_miss:",pm)
    print("   nonconv:",nc)
