import sys
t=open(sys.argv[1],encoding='utf-8').read()
key=sys.argv[2]; b=int(sys.argv[3]); a=int(sys.argv[4])
i=t.find(key)
while i>=0:
    ln=t.count('\n',0,i)+1
    print(f"=== line {ln} @ {i}"); print(t[max(0,i-b):i+a]); print()
    i=t.find(key,i+1)
