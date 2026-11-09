# 단서 낱말 주변 문맥(앞뒤 120자)과 줄 번호 -- 결과 cue_context.out.md
import re
D = r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/'
F = {'40': 'gain-budget-gmid-sizing.40-engine.design.md', '41': 'gain-budget-gmid-sizing.41-gain-budget.design.md'}
PATS = ['ngspice', 'Richardson', 'µV', '훑기', '점 중', 'SPICE와 같', 'SPICE 수준', 'SPICE 복제', '정밀']
out = []
for p in PATS:
    out.append(f'## {p}')
    for k, fn in F.items():
        lines = open(D + fn, encoding='utf-8').read().split('\n')
        for i, l in enumerate(lines, 1):
            for m in re.finditer(re.escape(p), l):
                a = max(0, m.start() - 120); b = min(len(l), m.end() + 120)
                out.append(f'- {k}:{i} … {l[a:b]} …')
    out.append('')
open('cue_context.out.md', 'w', encoding='utf-8').write('\n'.join(out))
