import re,sys
L=open('plan_6a31bf1c.md',encoding='utf-8').read().split('\n')
pat=sys.argv[1]; lo=int(sys.argv[2]) if len(sys.argv)>2 else 1; hi=int(sys.argv[3]) if len(sys.argv)>3 else len(L); w=int(sys.argv[4]) if len(sys.argv)>4 else 150
for i in range(lo-1,hi):
    for m in re.finditer(re.escape(pat),L[i]):
        print(i+1,'|',L[i][max(0,m.start()-w):m.end()+w].replace('\n',' '))
