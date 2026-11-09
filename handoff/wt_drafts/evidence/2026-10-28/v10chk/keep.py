import subprocess,sys,difflib,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6383'
a,b=sys.argv[1:3]
fs=subprocess.run(['git','-C',W,'diff','--name-only',a,b],capture_output=True,text=True).stdout.split()
for f in fs:
    if 'history' in f: continue
    o=subprocess.run(['git','-C',W,'show',f'{a}:{f}'],capture_output=True).stdout.decode().split('\n')
    n=subprocess.run(['git','-C',W,'show',f'{b}:{f}'],capture_output=True).stdout.decode().split('\n')
    sm=difflib.SequenceMatcher(None,o,n,autojunk=False);pairs=0;low=[]
    for t,i1,i2,j1,j2 in sm.get_opcodes():
        if t=='replace' and i2-i1==j2-j1:
            for k in range(i2-i1):
                pairs+=1
                s=difflib.SequenceMatcher(None,o[i1+k],n[j1+k],autojunk=False)
                kept=sum(m.size for m in s.get_matching_blocks())/max(1,len(o[i1+k]))
                if kept<0.8: low.append((j1+k+1,round(kept,2),len(o[i1+k])))
        elif t!='equal': low.append((t,i1+1,i2,j1+1,j2))
    print(f,pairs,low)
