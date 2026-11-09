import json, sys, collections, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
rs=[json.loads(l) for l in open('devices_j1b_eng.jsonl',encoding='utf-8')]
ok=[r for r in rs if 'skipped' not in r]
sw={ (r['circuit'],r['dev']):r for r in map(json.loads, open('../devices_j1b.jsonl',encoding='utf-8'))}
P=json.load(open('pooled_j1b_eng.json'))
def pg(key,cls,kind): return P.get("|".join(map(str,key))+f"|{cls}|{kind}")
print("== per-device: D2 (가) att leak(maj?), moved(D1 ga full/share), t* median lnIDu/VGS/gm/ID/W for D1@1mV ga full, and sweep(ID1e-5/1e-4) same")
for r in ok:
    out=[r['circuit'],r['dev'],r['cls'],r['kind'],r['mode'],'%.3g'%r['id_or_gm']]
    for bud in ('none','full','share'):
        c=r['combos'][f"D1@t1mV|ga|IDeng|{bud}"]
        out.append(f"{bud}: ts lnIDu {c['ts']['lnidu'][1]:.1f} VGS {c['ts']['vgs'][1]:.3f} g {c['ts']['gm_id'][1]:.1f} W {c['ts']['w_m'][1]:.2g} moved {c['moved']}/{c['sd_nonempty']}")
    d2=r['combos']["D2|ga|IDeng|none"]; out.append(f"D2 att leak {d2['leak_att']['t1mV']}/{d2['att']['n']}")
    print(" | ".join(out))
print("== counts (N=16: S11 F5), tol 1mV")
def cnt(vt,rule,bud,point):
    c=collections.Counter()
    for r in ok:
        cc=r['combos'][f"{vt}|{rule}|IDeng|{bud}"]; ne=cc['sd_nonempty']; c[(r['cls'],'N')]+=1
        if ne==0: continue
        n=cc[point]['n']; lk=cc['leak_'+point]['t1mV']
        if n and lk>=.5*n: c[(r['cls'],'maj')]+=1
        if lk>0: c[(r['cls'],'any')]+=1
        if cc['moved']>=.5*ne: c[(r['cls'],'mv')]+=1
        if cc['moved']>0: c[(r['cls'],'mvany')]+=1
    return c
for vt in ("D1@t1mV","D2P@t1mV","D2"):
  for rule in ("ga","na"):
    a=cnt(vt,rule,'none','att')
    print(vt,rule,"att leak maj S",a[('S','maj')],"F",a[('F','maj')],"any S",a[('S','any')],"F",a[('F','any')])
    for bud in ('full','share'):
        b=cnt(vt,rule,bud,'ts'); m=cnt(vt,rule,bud,'att')
        print("   ",bud,"ts leak maj S",b[('S','maj')],"F",b[('F','maj')],"| moved maj S",b[('S','mv')],"F",b[('F','mv')],"any S",b[('S','mvany')],"F",b[('F','mvany')])
def row(key):
    cells=[]
    for cls in "SF":
        for kind in "np":
            d=pg(key,cls,kind)
            if not d or d['n']==0: cells.append('-'); continue
            q=d['abs_dlnidu_p50_p90_max']; v=d['abs_dvgs_p50_p90_max']
            cells.append(f"{d['n_differ']/d['n']:.1%}/ln p90 {q[1]:.2f} max {q[2]:.2f}/VGS max {v[2]:.3f} (n={d['n']})")
    return cells
for bud in ('none','full','share'):
    print("== pooled",bud)
    for rule in ("ga","na"):
        for pair in ("D1-D2P","D1-D2"):
            print("K10",rule,pair," || ".join(row(("K10",rule,pair,"t1mV","eng",bud))))
    for vt in ("D1@t1mV","D2"):
        print("K3",vt," || ".join(row(("K3","na-ga",vt,"-","eng",bud))))
