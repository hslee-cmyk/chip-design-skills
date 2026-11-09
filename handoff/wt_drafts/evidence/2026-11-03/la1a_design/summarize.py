# q8_la1a.jsonl·uncovered.jsonl 요약 -> summary.txt (측정 결과 표 생성, 저장소 쓰기 0)
import json, os
O = os.path.dirname(os.path.abspath(__file__))
out = []
for ln in open(os.path.join(O, 'q8_la1a.jsonl'), encoding='utf-8'):
    d = json.loads(ln)
    if d['case'] == 'captured':
        gi = (d.get('gain_inputs') or [{}])[0]
        out.append('%s g1=%s kinds=%s best=%s' % (d['mode'], gi.get('g1'), gi.get('kinds'), d.get('best_anchor')))
        for f in d.get('fields') or []:
            out.append('   L_nm=%s conf=%s' % ([(c.split(',')[1].strip(" ')"), round(v * 1e9)) for c, v in f['rung0_L']], f['conflicts_L']))
    if d['case'] == 'front':
        r = d['rows']
        out.append('%s front=%s sealed=%s %s M8_L=%s' % (d['mode'], d['n_front'], d['n_sealed'], {k.split(':')[-1]: (v['pass'], round(v['c_max'], 3)) for k, v in r.items()}, d.get('L_nm_seen', {}).get('M8')))
out.append('=== uncovered')
p = os.path.join(O, 'uncovered.jsonl')
if os.path.exists(p):
    for ln in open(p, encoding='utf-8'):
        d = json.loads(ln)
        if 'error' in d:
            out.append('%s ERROR %s' % (d['circuit'], d['error'][-300:]))
            continue
        if d.get('stage_a') != 'ok':
            out.append('%s stage_a=%s stop=%s' % (d['circuit'], d.get('stage_a'), (d.get('stop') or '')[:140]))
            continue
        r0 = (d.get('rungs') or [{}])[0]
        out.append('%s n_theta=%s n_rungs=%s missing=%s r_vars=%s c_vars=%s' % (d['circuit'], d.get('n_theta_vars'), d.get('n_rungs'), r0.get('missing_by_kind'), d.get('r_vars'), d.get('c_vars')))
open(os.path.join(O, 'summary.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out))
