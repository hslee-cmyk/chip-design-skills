import subprocess,difflib,re,sys,json
W='C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384'
A,B='643b04c8','00628569'
feats=['gain-budget-gmid-sizing','oracle-portability','graph-consumption','headroom-chain','offset-strategy','offset-trim']
def show(c,f): return subprocess.check_output(['git','-C',W,'show',c+':'+f]).decode('utf-8')
out=open(sys.argv[1],'w',encoding='utf-8')
tot={'lines':0,'verbatim':0,'segs':0,'segs_ok':0}
def norm(s): return re.sub(r'\s+',' ',s.replace('\|','|')).strip()
for ft in feats:
    p='docs/01-plan/features/%s.plan.md'%ft; h='docs/01-plan/features/%s.history.md'%ft
    a=show(A,p).splitlines(); b=show(B,p).splitlines()
    hist=show(B,h); histA=show(A,h); hn=norm(hist)
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='equal' or tag=='insert': continue
        for k in range(i1,i2):
            ol=a[k]; tot['lines']+=1
            if not ol.strip(): continue
            if ol in hist and ol not in histA:
                tot['verbatim']+=1; out.write(f'{ft} old {k+1}: VERBATIM\n'); continue
            if norm(ol) in hn:
                tot['verbatim']+=1; out.write(f'{ft} old {k+1}: VERBATIM(norm)\n'); continue
            # find best matching new line in replacement block
            cand=b[j1:j2]
            best=max(cand,key=lambda x: difflib.SequenceMatcher(None,ol,x,autojunk=False).ratio()) if cand else ''
            ow=re.split(r'(\s+)',ol); nw=re.split(r'(\s+)',best)
            s2=difflib.SequenceMatcher(None,ow,nw,autojunk=False)
            miss=[]
            for t,x1,x2,y1,y2 in s2.get_opcodes():
                if t in('replace','delete'):
                    seg=norm(''.join(ow[x1:x2]))
                    if len(seg)<25: continue
                    tot['segs']+=1
                    if seg in hn: tot['segs_ok']+=1
                    else:
                        # try fragments
                        frag=seg[:60]
                        miss.append((seg[:200], frag in hn))
            out.write(f'{ft} old {k+1}: segs missing {len(miss)}\n')
            for m in miss: out.write(f'   MISS(frag60 in hist={m[1]}): {m[0]}\n')
out.write(json.dumps(tot)+'\n'); print(tot)
