import re,sys
f,pat,outp=sys.argv[1],sys.argv[2],sys.argv[3]
lines=[int(x) for x in sys.argv[4].split(',')] if len(sys.argv)>4 else None
L=open(f,encoding='utf-8').read().splitlines()
o=open(outp,'w',encoding='utf-8')
for i,s in enumerate(L,1):
    if lines and i not in lines: continue
    for m in re.finditer(pat,s):
        a=max(0,m.start()-350); o.write(f'[{i}] ..{s[a:m.end()+350]}\n\n')
