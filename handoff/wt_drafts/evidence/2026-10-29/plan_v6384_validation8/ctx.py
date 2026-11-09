import sys,re
f=sys.argv[1]; pats=sys.argv[2:]
L=open(f,encoding='utf-8').read().split('\n')
for i,s in enumerate(L):
    for p in pats:
        for m in re.finditer(re.escape(p),s):
            a=max(0,m.start()-250); b=min(len(s),m.end()+250)
            print(f"[{i+1}] <{p}> ...{s[a:b]}...")
            print()
