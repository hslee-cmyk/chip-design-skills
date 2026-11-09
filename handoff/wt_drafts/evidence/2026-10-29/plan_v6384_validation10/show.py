import sys
f=sys.argv[1]; L=open(f,encoding='utf-8').read().split('\n')
for a in sys.argv[2:]:
    if ':' in a:
        n,pat=a.split(':',1); s=L[int(n)-1]; i=s.find(pat)
        print(f'## {n} @{i}:', s[max(0,i-1500):i+2500] if i>=0 else 'NOTFOUND'); continue
    n=int(a); print(f'## {n}:', L[n-1][:6000])
