import sys, re
# usage: sent.py file pattern [lines a-b] [width]
# prints, for each matching line, the sentence-ish fragments (split on '. ' / ' -- ' / ';') containing pattern
f = sys.argv[1]; pat = re.compile(sys.argv[2])
rng = sys.argv[3] if len(sys.argv) > 3 else None
w = int(sys.argv[4]) if len(sys.argv) > 4 else 400
a, b = (map(int, rng.split('-')) if rng and rng != '-' else (1, 10**9))
for i, l in enumerate(open(f, encoding='utf-8', errors='replace'), 1):
    if i < a or i > b:
        continue
    for m in pat.finditer(l):
        s = max(0, m.start() - w); e = min(len(l), m.end() + w)
        print(f"[{i}@{m.start()}] ...{l[s:e]}...")
        print()
