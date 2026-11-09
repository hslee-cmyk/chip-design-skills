import sys,re
f,pat=sys.argv[1],sys.argv[2]; w=int(sys.argv[3]) if len(sys.argv)>3 else 160
lines=open(f,encoding='utf-8').read().split('\n')
only=set(int(x) for x in sys.argv[4].split(',')) if len(sys.argv)>4 else None
for i,l in enumerate(lines,1):
    if only and i not in only: continue
    for m in re.finditer(re.escape(pat),l):
        s=max(0,m.start()-w); e=min(len(l),m.end()+w)
        print(f'{i}: …{l[s:e]}…')
