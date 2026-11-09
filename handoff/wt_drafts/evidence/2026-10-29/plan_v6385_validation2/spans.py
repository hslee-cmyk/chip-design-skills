import re,sys
t=open(sys.argv[1],encoding='utf-8').read()
out=[]
for m in re.finditer(r'(\[-.*?-\]|\{\+.*?\+\})',t,re.S):
    s=m.group(0)
    out.append(f"--- @{m.start()} len={len(s)}\n{s}\n")
open(sys.argv[2],'w',encoding='utf-8').write("\n".join(out))
