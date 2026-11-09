import sys,re
f,pat,w=sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 300
for i,l in enumerate(open(f,encoding='utf-8'),1):
    for m in re.finditer(pat,l):
        s=max(0,m.start()-w); e=min(len(l),m.end()+w)
        print(f"{i}: ...{l[s:e].strip()}...")
