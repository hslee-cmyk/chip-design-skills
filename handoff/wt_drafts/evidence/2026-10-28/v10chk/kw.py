import sys,re,io,subprocess
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6383'
rev,f,pat=sys.argv[1:4]; ctx=int(sys.argv[4]) if len(sys.argv)>4 else 200
lines=subprocess.run(['git','-C',W,'show',f'{rev}:{f}'],capture_output=True).stdout.decode('utf-8').split('\n')
only=set(int(x) for x in sys.argv[5].split(',')) if len(sys.argv)>5 else None
for i,l in enumerate(lines,1):
    if only and i not in only: continue
    for m in re.finditer(pat,l):
        s=max(0,m.start()-ctx);e=min(len(l),m.end()+ctx)
        print(f'{i}:{m.start()}: ...{l[s:e]}...')
