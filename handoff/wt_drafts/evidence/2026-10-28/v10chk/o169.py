import subprocess,sys,difflib,re,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6383'
a,b='9d153f2f','c2f8ca5e'
pat=re.compile(r'(현행 유지|as-built 유지|기존 결정 유지|호환|둘째 경로|그대로 둔다|그대로 유지|유지한다|유지\)|는 유지|을 유지|를 유지|존치|그대로다|보존)')
fs=[f for f in subprocess.run(['git','-C',W,'diff','--name-only',a,b],capture_output=True,text=True).stdout.split() if 'history' not in f]
for f in fs:
    o=subprocess.run(['git','-C',W,'show',f'{a}:{f}'],capture_output=True).stdout.decode().split('\n')
    n=subprocess.run(['git','-C',W,'show',f'{b}:{f}'],capture_output=True).stdout.decode().split('\n')
    sm=difflib.SequenceMatcher(None,o,n,autojunk=False)
    for t,i1,i2,j1,j2 in sm.get_opcodes():
        if t=='equal':continue
        oldtxt='\n'.join(o[i1:i2])
        for j in range(j1,j2):
            for m in pat.finditer(n[j]):
                s=max(0,m.start()-220);e=min(len(n[j]),m.end()+120)
                frag=n[j][s:e]
                if frag[200:260] and n[j][max(0,m.start()-40):m.end()+20] in oldtxt: continue  # pre-existing text
                print(f'{f.split("/")[-1]}:{j+1}:{m.start()} [{m.group()}] ...{frag}...')
