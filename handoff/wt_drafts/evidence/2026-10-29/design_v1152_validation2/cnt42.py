import sys, re, collections
# D42 표 행 계수: 절(1 FR·NFR, 2 DEC, 3 설계 항목)마다 '상태' 열 첫 낱말, ID(첫 열) 중복
f = sys.argv[1]
L = open(f, encoding='utf-8').read().split('\n')
heads = [i for i, l in enumerate(L) if l.startswith('## ')]
def sec(prefix):
    for k, i in enumerate(heads):
        if L[i].startswith(prefix):
            return i, (heads[k + 1] if k + 1 < len(heads) else len(L))
secs = {'FR': sec('## 1.'), 'DEC': sec('## 2.'), 'DES': sec('## 3.')}
SPLIT = re.compile(r'(?<!\\)\|')
ids = collections.defaultdict(list)
for name, (a, b) in secs.items():
    hdr = None; c = collections.Counter(); n = 0
    for i in range(a, b):
        l = L[i]
        if not l.startswith('|'):
            hdr = None; continue
        cells = [x.strip() for x in SPLIT.split(l)[1:-1]]
        if hdr is None:
            hdr = cells; continue
        if set(''.join(cells)) <= set('-: '):
            continue
        si = next((k for k, h in enumerate(hdr) if '상태' in h), None)
        raw = cells[si] if si is not None and si < len(cells) else ''
        m = re.match(r'\**\s*(OK|DEV|PART|MISS|N/A)', raw)
        st = m.group(1) if m else 'OTHER:' + raw[:20]
        c[st] += 1; n += 1
        ids[cells[0]].append(i + 1)
    print(name, n, dict(c))
print('dup ids', {k: v for k, v in ids.items() if len(v) > 1})
