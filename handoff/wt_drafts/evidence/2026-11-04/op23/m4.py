"""§10.3 U-5·U-6 선언(.option scale + mult)을 쓴 소자 줄 대 옛 소자 줄 실현 가능성: 경계 소속, 공칭 값 차.
(읽기·임시 폴더 실행만. 저장소 파일 안 고침)"""
import json,os,re,subprocess,sys,tempfile,hashlib
W=r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/docs-op23"
HERE=os.path.dirname(os.path.abspath(__file__))
EXE=r"C:/ngspice/Spice64/bin/ngspice_con.exe"
PDK="C:/pdk/sky130_fd_pr"
out=open(os.path.join(HERE,"m4.jsonl"),"w",encoding="utf-8")
def w(**k):
    out.write(json.dumps(k,ensure_ascii=False)+"\n"); out.flush()
INC={"n":[f'.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice"',f'.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"'],
     "p":[f'.include "{PDK}/models/parameters/lod.spice"',f'.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice"',f'.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice"']}
SUB={"n":"sky130_fd_pr__nfet_01v8","p":"sky130_fd_pr__pfet_01v8"}
env=dict(os.environ)
home=tempfile.mkdtemp(); env["HOME"]=env["USERPROFILE"]=home
for k in ("HOMEDRIVE","HOMEPATH","SPICE_USERINIT_DIR"): env.pop(k,None)
def run(text,tag):
    d=tempfile.mkdtemp()
    p=os.path.join(d,"t.cir"); open(p,"w",newline="\n").write(text)
    r=subprocess.run([EXE,"-b",p],cwd=d,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace")
    return r.stdout+r.stderr
def lines(kind,pts,scale):
    L=["* t"]+INC[kind]
    if scale: L.append(".option scale=1u")
    L+=["vgs g 0 dc 0","vds d 0 dc 0","vsrc s 0 dc 0","vb b 0 dc 0"]
    for i,(l,wd) in enumerate(pts):
        if scale: L.append(f"xp{i} d g s b {SUB[kind]} l={l*1e6:.15g} w={wd*1e6:.15g}")
        else: L.append(f"xp{i} d g s b {SUB[kind]} l={l:.15g} w={wd:.15g}")
    L+=[".control","op"]
    for i in range(len(pts)):
        L+=[f"echo SHOWMOD p{i}",f"showmod m.xp{i}.m{SUB[kind]} : lmin lmax wmin wmax"]
    L+=["quit",".endc",".end"]
    return "\n".join(L)+"\n"
def parse(t):
    res={}
    for blk in re.split(r"SHOWMOD ",t)[1:]:
        k=blk.split()[0]
        d={}
        for key in ("lmin","lmax","wmin","wmax"):
            m=re.search(rf"^\s*{key}\s+([-+0-9.eE]+)",blk,re.M)
            d[key]=float(m.group(1)) if m else None
        res[k]=d
    return res
d=json.load(open(W+"/skills/analog-gmid-design/assets/lut_v2_bin_rule.json",encoding="utf-8"))
pts={"n":[],"p":[]}
for q in d["evidence"]["points"]:
    pts["n" if "nfet" in q["chosen_bin"] else "p"].append((q["L"],q["W"]))
w(m="points",n=len(pts["n"]),p=len(pts["p"]))
tot=0;diff=[]
for k in "np":
    P=pts[k]
    for s in range(0,len(P),60):
        ch=P[s:s+60]
        a=parse(run(lines(k,ch,False),"si")); b=parse(run(lines(k,ch,True),"sc"))
        for i,pt in enumerate(ch):
            tot+=1
            x,y=a.get(f"p{i}"),b.get(f"p{i}")
            if x!=y or x is None or None in x.values(): diff.append({"kind":k,"L":pt[0],"W":pt[1],"si":x,"scale":y})
w(m="bin_si_vs_scale",points=tot,differ=len(diff),examples=diff[:20])
# 공칭 op 값: 옛 줄(SI m=) 대 새 줄(scale + m + mult) 대 scale만
def bench(form):
    k="n"
    L=["* v"]+INC[k]+[".temp 27.0",".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7"]
    if form!="si": L.append(".option scale=1u")
    dev={"si":f"Xm1 d g 0 0 {SUB[k]} l=5e-07 w=2e-06 m=2 ad=1e-12 as=1e-12 pd=4e-06 ps=4e-06",
         "scale":f"Xm1 d g 0 0 {SUB[k]} l=0.5 w=2 m=2 ad=1 as=1 pd=4 ps=4",
         "scale_mult":f"Xm1 d g 0 0 {SUB[k]} l=0.5 w=2 m=2 mult=2 ad=1 as=1 pd=4 ps=4"}[form]
    L+=[dev,"Vg g 0 DC 0.7 AC 1","Vd d 0 DC 0.9",".control","op"]
    for q in ("id","gm","gds","vth","vdsat"):
        L.append(f"print @m.xm1.m{SUB[k]}[{q}]")
    L+=["ac dec 5 1 1e9","print vm(d)[0]" ,"quit",".endc",".end"]
    return "\n".join(L)+"\n"
vals={}
for f in ("si","scale","scale_mult"):
    t=run(bench(f),f)
    vals[f]={q:(re.search(rf"\[{q}\]\s*=\s*([-+0-9.eE]+)",t).group(1) if re.search(rf"\[{q}\]\s*=\s*([-+0-9.eE]+)",t) else None) for q in ("id","gm","gds","vth","vdsat")}
w(m="op_forms",vals=vals)
def rel(a,b):
    a,b=float(a),float(b); return abs(a-b)/max(abs(a),abs(b))
w(m="op_forms_rel",scale={q:rel(vals["si"][q],vals["scale"][q]) for q in vals["si"]},scale_mult={q:rel(vals["si"][q],vals["scale_mult"][q]) for q in vals["si"]})
