"""검증 5 -- v6.38.4 전체에서 바뀐 표 행의 열 수 점검.
(1) tablecols.txt: 바뀐 줄 중 머리와 열 수가 다른 행(원시)
(2) tablecols_delta.txt: 같은 첫 칸 행이 base(07181524)와 열 수가 달라진 경우만(새로 생긴 열 수 변화)
열 수 = 이스케이프 `\\|`·백틱 안 `|`를 뺀 `|` 개수.
"""
import re, difflib

NAMES = ['gain-budget-gmid-sizing', 'graph-consumption', 'offset-strategy', 'oracle-portability', 'headroom-chain', 'offset-trim']


def cells(l):
    s = re.sub(r'\\\|', '', l)
    s = re.sub(r'`[^`]*`', '``', s)
    return s.count('|')


def key(l):
    if l.startswith('|') and l.count('|') > 2:
        return l.split('|')[1].strip()
    return None


out = open('tablecols.txt', 'w', encoding='utf-8')
out2 = open('tablecols_delta.txt', 'w', encoding='utf-8')
for name in NAMES:
    for kind in ['plan', 'history']:
        a = open(f'base/{name}.{kind}.md', encoding='utf-8').read().splitlines()
        b = open(f'snap/{name}.{kind}.md', encoding='utf-8').read().splitlines()
        changed = set()
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag != 'equal':
                changed.update(range(j1, j2))
        hdr = None
        for j, l in enumerate(b):
            if l.startswith('|'):
                if hdr is None:
                    hdr = cells(l)
                    continue
                if re.match(r'^\|[\s:|-]+\|?\s*$', l):
                    continue
                if j in changed and cells(l) != hdr:
                    out.write(f'{name}.{kind}:{j+1}: cols {cells(l)} vs header {hdr}: {l[:150]}\n')
            else:
                hdr = None
        bas = {}
        for l in a:
            k = key(l)
            if k:
                bas.setdefault(k, cells(l))
        for j, l in enumerate(b):
            k = key(l)
            if k and j in changed and k in bas and bas[k] != cells(l):
                out2.write(f'{name}.{kind}:{j+1}: {k[:50]} base {bas[k]} now {cells(l)}\n')
