# 표본 절 발췌(줄마다 앞 N자) -- 검증자 읽기용. 사용: python sample_dump.py <doc 40|41> <start-end,...> <N> <out>
import sys
D = r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/'
F = {'40': 'gain-budget-gmid-sizing.40-engine.design.md', '41': 'gain-budget-gmid-sizing.41-gain-budget.design.md'}
doc, ranges, n, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
lines = open(D + F[doc], encoding='utf-8').read().split('\n')
res = []
for r in ranges.split(','):
    a, b = map(int, r.split('-'))
    res.append(f'===== {doc}:{a}-{b}')
    for i in range(a, b + 1):
        l = lines[i - 1]
        if not l.strip():
            continue
        res.append(f'{i}[{len(l)}]: ' + (l[:n] + (' …' if len(l) > n else '')))
open(out, 'w', encoding='utf-8').write('\n'.join(res))
