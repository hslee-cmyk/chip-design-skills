import sys
# usage: show.py file a b [cap] [skip]
f = sys.argv[1]; a = int(sys.argv[2]); b = int(sys.argv[3])
cap = int(sys.argv[4]) if len(sys.argv) > 4 else 1500
skip = int(sys.argv[5]) if len(sys.argv) > 5 else 0
L = open(f, encoding='utf-8', errors='replace').read().split('\n')
for i in range(a, b + 1):
    s = L[i - 1]
    print(f"{i}[{len(s)}]: {s[skip:skip+cap]}{' <<TRUNC>>' if len(s) > skip+cap else ''}")
