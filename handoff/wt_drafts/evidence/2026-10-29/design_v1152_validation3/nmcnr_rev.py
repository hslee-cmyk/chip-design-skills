# nmcnr T 망 반대 방향(A = C 쪽 끝, B = R 쪽 끝 Vout -- design 40 §3.5 표 방향) 결합 조사
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
mos = [(e['name'], e['kind'], e.get('drain'), e.get('gate'), e.get('source')) for e in d['netlist']]
pas = [(p['name'], p['kind'], p['terminals']) for p in d.get('passive_elements', [])]
print([p for p in pas if p[0] in ('Rm', 'Cm1', 'Cm2')])
for A in ('NodeS2', 'NodeM2'):
    B = 'Vout'
    S = [x[0] for x in mos if x[3] == A and x[2] == B]
    for o in [x for x in mos if x[2] == B and x[3] != A]:
        G = o[3]
        coup = [(x[0], [k for k, v in zip('dgs', x[2:]) if v == A], [k for k, v in zip('dgs', x[2:]) if v == G]) for x in mos if A in x[2:] and G in x[2:]]
        coup += [(q[0], q[1]) for q in pas if A in q[2] and G in q[2]]
        print(json.dumps({'A': A, 'B': B, 'S': S, 'out_dev': o[0], 'G': G, 'A_G_coupling': coup}))
