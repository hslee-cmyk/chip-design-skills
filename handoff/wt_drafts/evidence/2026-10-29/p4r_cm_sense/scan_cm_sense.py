"""9회로 전수: 저항 CM 감지 꼴(두 저항이 한 내부 넷을 공유하고, 그 넷의 다른 연결이 MOS gate뿐이며,
저항의 다른 끝이 서로 다른 넷) 판독 -- connectivity만 사용(태그·주석 무시)."""
import json, glob, os, sys
lib = sys.argv[1]
out = sys.argv[2]
rows = []
for f in sorted(glob.glob(os.path.join(lib, '*.topology.json'))):
    if '_TEMPLATE' in f: continue
    d = json.load(open(f, encoding='utf-8'))
    name = os.path.basename(f).replace('.topology.json', '')
    mos = [n for n in d.get('netlist', []) if n.get('kind') in ('nmos', 'pmos')]
    pas = [p for p in d.get('passive_elements', []) + [n for n in d.get('netlist', []) if n.get('kind') not in ('nmos','pmos')]]
    res = [p for p in pas if p.get('kind') == 'resistor']
    caps = [p for p in pas if p.get('kind') == 'capacitor']
    def conns(net):
        c = []
        for m in mos:
            for t in ('gate', 'drain', 'source'):
                if m.get(t) == net: c.append((m['name'], t))
        for p in pas:
            if net in p.get('terminals', []): c.append((p['name'], p['kind']))
        return c
    hits = []
    nets = {}
    for r in res:
        for t in r['terminals']:
            nets.setdefault(t, []).append(r['name'])
    for net, rs in nets.items():
        if len(rs) < 2: continue
        c = conns(net)
        others = [x for x in c if x[0] not in rs]
        only_gates = all(x[1] == 'gate' for x in others) and len(others) > 0
        far = []
        for rn in rs:
            r = next(x for x in res if x['name'] == rn)
            far += [t for t in r['terminals'] if t != net]
        hits.append({'net': net, 'resistors': rs, 'far_ends': far, 'other_conns': others, 'only_gates': only_gates})
    rows.append({'circuit': name, 'n_resistors': len(res),
                 'resistors': [{'name': r['name'], 'terminals': r['terminals'], 'value_ohm': r.get('value_ohm')} for r in res],
                 'shared_resistor_nets': hits,
                 'cm_sense_pattern': any(h['only_gates'] and len(set(h['far_ends'])) >= 2 for h in hits)})
with open(out, 'w', encoding='utf-8') as fo:
    for r in rows:
        fo.write(json.dumps(r, ensure_ascii=False) + '\n')
print('n_circuits', len(rows), 'cm_sense', sum(r['cm_sense_pattern'] for r in rows))
for r in rows:
    print(r['circuit'], r['n_resistors'], [ (x['name'], x['terminals']) for x in r['resistors']], 'CM' if r['cm_sense_pattern'] else '')
