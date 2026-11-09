import subprocess,sys,difflib,re,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6383'
a,b,f=sys.argv[1:4]
old=subprocess.run(['git','-C',W,'show',f'{a}:{f}'],capture_output=True).stdout.decode('utf-8').split('\n')
new=subprocess.run(['git','-C',W,'show',f'{b}:{f}'],capture_output=True).stdout.decode('utf-8').split('\n')
sm=difflib.SequenceMatcher(None,old,new,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':continue
    print(f'=== {tag} old {i1+1}-{i2} new {j1+1}-{j2}')
    if tag=='replace' and i2-i1==j2-j1:
        for k in range(i2-i1):
            o=re.split(r'(\s+)',old[i1+k]);n=re.split(r'(\s+)',new[j1+k])
            s2=difflib.SequenceMatcher(None,o,n,autojunk=False)
            r=s2.ratio()
            print(f'-- line new {j1+k+1} ratio {r:.2f}')
            for t,x1,x2,y1,y2 in s2.get_opcodes():
                if t=='equal':continue
                ctx=''.join(o[max(0,x1-12):x1])
                print(f'  [{t}] ...{ctx[-120:]} | -[{"".join(o[x1:x2])}] +[{"".join(n[y1:y2])}]')
    else:
        for l in old[i1:i2]:print('-',l[:3000])
        for l in new[j1:j2]:print('+',l[:3000])
