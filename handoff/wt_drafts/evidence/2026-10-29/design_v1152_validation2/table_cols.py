import sys, re
# 표 열 수 점검: 머리 행과 열 수가 다른 행(이스케이프 \| 제외)
SP = re.compile(r'(?<!\\)\|')
for f in sys.argv[1:]:
    L = open(f, encoding='utf-8').read().split('\n')
    hdr = None; bad = []
    for i, l in enumerate(L, 1):
        if not l.startswith('|'):
            hdr = None; continue
        n = len(SP.split(l)) - 2
        if hdr is None:
            hdr = (i, n); continue
        if n != hdr[1]:
            bad.append((i, n, hdr))
    print(f.split('/')[-1], 'mismatch', bad)
