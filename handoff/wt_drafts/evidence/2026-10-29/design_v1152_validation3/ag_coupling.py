# 검증 3 -- R-C 보상 경로(A->B)마다 B에 drain이 닿은 S 밖 출력 소자의 gate 넷 G와 A 사이 결합 소자 분류
# 입력: integ-it12 / design-v115 assets/library/*.topology.json (연결만 읽음, 태그 READS 0)
import json, glob, os, sys
lib = sys.argv[1]; out = sys.argv[2]
res = []
for f in sorted(glob.glob(os.path.join(lib, '*.topology.json'))):
    if '_TEMPLATE' in f: continue
    d = json.load(open(f, encoding='utf-8'))
    name = d.get('topology_name')
    mos = []
    for e in d.get('netlist', []):
        k = e.get('kind') or e.get('type')
        t = e.get("terminals") or {kk: e.get(kk) for kk in ("drain","gate","source")}
        if isinstance(t, dict):
            mos.append((e.get('name'), k, t.get('drain') or t.get('d'), t.get('gate') or t.get('g'), t.get('source') or t.get('s')))
        else:
            mos.append((e.get('name'), k, *(list(t)[:3])))
    pas = [(p['name'], p['kind'], p['terminals']) for p in d.get('passive_elements', [])]
    caps = [p for p in pas if p[1] == 'capacitor']; ress = [p for p in pas if p[1] == 'resistor']
    # R-C 경로: R 한 끝 넷 X에 R과 C만 닿음(MOS 단자 없음, 다른 수동 없음)
    def touch(net):
        m = [x for x in mos if net in x[2:]]
        p = [x for x in pas if net in x[2]]
        return m, p
    for r in ress:
        for i, X in enumerate(r[2]):
            m, p = touch(X)
            if m: continue
            cs = [q for q in p if q[1] == 'capacitor']
            if len(cs) != len(p) - 1 or not cs: continue  # R 하나 + C만 (T 망이면 C마다 경로)
            for c in cs:
              ends = [r[2][1 - i], [n for n in c[2] if n != X][0]]
              for A, B in (ends,):  # A = R 쪽 끝(구동), B = C 쪽 끝(출력)
                  S = [x[0] for x in mos if x[3] == A and x[2] == B]
                  outs = [x for x in mos if x[2] == B and x[3] != A]
                  for o in outs:
                      G = o[3]
                      coup = []
                      for x in mos:
                          nets = {'d': x[2], 'g': x[3], 's': x[4]}
                          roles = {kk for kk, v in nets.items() if v in (A, G)}
                          if A in nets.values() and G in nets.values():
                              ta = [kk for kk, v in nets.items() if v == A]; tg = [kk for kk, v in nets.items() if v == G]
                              typ = 'Cgs/Cgd(gate on A or G)' if ('g' in ta or 'g' in tg) else 'Cds(channel only)'
                              coup.append({'mos': x[0], 'kind': x[1], 'A_term': ta, 'G_term': tg, 'type': typ, 'gate_net': x[3]})
                      for q in pas:
                          if A in q[2] and G in q[2]:
                              coup.append({'passive': q[0], 'kind': q[1]})
                      res.append({'circuit': name, 'R': r[0], 'C': c[0], 'S_empty_path': not S, 'A': A, 'B': B, 'S': S,
                                  'out_dev': o[0], 'G': G, 'A_G_coupling': coup})
with open(out, 'w', encoding='utf-8') as fo:
    for x in res: fo.write(json.dumps(x, ensure_ascii=False) + '\n')
print(len(res))
