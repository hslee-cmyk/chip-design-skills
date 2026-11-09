# -*- coding: utf-8 -*-
# design_b56_validation M8 재측정: KCL 항등 0 집합 = MOS 엣지가 다리인가 (topology 파일만 읽음, 엔진 안 읽음)
# 사용: python oracle_m8_bridge.py <assets/library 경로> <결과 jsonl>
import json, glob, os, sys
lib, out = sys.argv[1], sys.argv[2]
open(out, 'w').close()
for f in sorted(glob.glob(os.path.join(lib, '*.topology.json'))):
    t = json.load(open(f, encoding='utf-8'))
    ports = t.get('ports') or {}
    items = ports.items() if isinstance(ports, dict) else [(p.get('name'), p) for p in ports]
    fixed = set(t.get('supply_nets') or [])
    bi = t.get('bias_inputs') or []
    fixed |= set(bi.keys() if isinstance(bi, dict) else [b if isinstance(b, str) else b.get('net') or b.get('name') for b in bi])
    for name, p in items:
        role = p if isinstance(p, str) else (p.get('role') or '')
        net = name if isinstance(p, str) or not p.get('net') else p['net']
        if 'input' in role:
            fixed.add(net)
    F = '__FIXED__'
    n = lambda x: F if x in fixed else x
    edges = []
    def rows(key):
        v = t.get(key) or []
        if isinstance(v, dict):
            return [dict(e, name=e.get('name', k)) for k, e in v.items() if isinstance(e, dict)]
        return [e for e in v if isinstance(e, dict)]
    if not rows('netlist'):
        rec = {'file': os.path.basename(f), 'skip': 'netlist 원소 dict 아님', 'netlist_type': str(type(t.get('netlist')))}
        with open(out, 'a', encoding='utf-8') as g:
            g.write(json.dumps(rec, ensure_ascii=False) + '\n')
        print(rec)
        continue
    for d in rows('netlist'):
        edges.append((d['name'], n(d['drain']), n(d['source']), True))
    for e in rows('passive_elements'):
        if 'capacitor' not in e.get('kind', ''):
            edges.append((e['name'], n(e['terminals'][0]), n(e['terminals'][1]), False))
    for e in rows('ideal_sources'):
        edges.append((e['name'], n(e['terminals'][0]), n(e['terminals'][1]), False))
    res = []
    for i, (nm, a, b, is_mos) in enumerate(edges):
        if not is_mos or a == b:
            continue
        seen = {a}; st = [a]
        while st:
            u = st.pop()
            for j, (_, x, y, _m) in enumerate(edges):
                if j == i:
                    continue
                for s, v in ((x, y), (y, x)):
                    if s == u and v not in seen:
                        seen.add(v); st.append(v)
        if b not in seen:
            res.append(nm)
    rec = {'file': os.path.basename(f), 'n_edges': len(edges), 'kcl_zero': res}
    with open(out, 'a', encoding='utf-8') as g:
        g.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(rec)
