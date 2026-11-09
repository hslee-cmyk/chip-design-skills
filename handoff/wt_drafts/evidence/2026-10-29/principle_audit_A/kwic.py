import sys,re
# usage: kwic.py file pattern [width] [maxhits]
f,pat=sys.argv[1],sys.argv[2]; w=int(sys.argv[3]) if len(sys.argv)>3 else 160; mx=int(sys.argv[4]) if len(sys.argv)>4 else 200
n=0
for i,l in enumerate(open(f,encoding='utf-8',errors='replace'),1):
    for m in re.finditer(pat,l):
        s=max(0,m.start()-w); e=min(len(l),m.end()+w)
        print(f"{i}: ...{l[s:e].strip()}...")
        n+=1
        if n>=mx: sys.exit()
        break
