import sys
f,out=sys.argv[1],sys.argv[2]
L=open(f,encoding='utf-8').read().split('\n')
with open(out,'w',encoding='utf-8') as o:
    for n in map(int,sys.argv[3:]):
        o.write(f'##### {n} len={len(L[n-1])}\n{L[n-1]}\n\n')
