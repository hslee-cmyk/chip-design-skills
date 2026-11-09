import subprocess,difflib,re,sys
W="C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384"
files=["gain-budget-gmid-sizing","graph-consumption","headroom-chain","offset-strategy","offset-trim","oracle-portability"]
kws=["정확","ngspice","PDK 셀","Richardson","중점","bin 중점","맞춤","δ_B","SPICE 실측","sha256","셀 식","동일성","충실도","분포","ωRC","정밀"]
out=open("kw_added.txt","w",encoding="utf-8")
tot_added=0
for f in files:
    p=f"docs/01-plan/features/{f}.plan.md"
    A=subprocess.run(["git","-C",W,"show",f"07181524:{p}"],capture_output=True).stdout.decode()
    B=subprocess.run(["git","-C",W,"show",f"824da846:{p}"],capture_output=True).stdout.decode()
    al=A.split("\n"); bl=B.split("\n")
    sm=difflib.SequenceMatcher(None,al,bl,autojunk=False)
    added_bytes=0
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=="equal": continue
        for j in range(j1,j2):
            new=bl[j]
            # find inserted segments vs best old line
            old="\n".join(al[i1:i2])
            s=difflib.SequenceMatcher(None,old,new,autojunk=False)
            segs=[new[q1:q2] for t,p1,p2,q1,q2 in s.get_opcodes() if t in("replace","insert")]
            ins="".join(segs); added_bytes+=len(ins.encode())
            for k in kws:
                for seg in segs:
                    for m in re.finditer(re.escape(k),seg):
                        a=max(0,m.start()-120); b=min(len(seg),m.end()+120)
                        out.write(f"{f}:{j+1} <{k}> {seg[a:b]}\n")
    print(f, "added bytes(approx)", added_bytes, "old", len(A.encode()), "new", len(B.encode()))
