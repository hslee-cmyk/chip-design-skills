"""OP-3 소자 줄 숫자 표기가 bin 소속을 바꾸는가: 944 동률 점에서 L/u, W/u를 repr 그대로 쓴 줄 대 선언 chosen_bin(default 모드 측정).
그리고 시뮬레이터가 보고하는 인스턴스 기하 원값."""
import json,os,re,sys,tempfile,subprocess
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
W=r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/docs-op23"
EXE=r"C:/ngspice/Spice64/bin/ngspice_con.exe";PDK="C:/pdk/sky130_fd_pr"
out=open(os.path.join(HERE,"m5.jsonl"),"w",encoding="utf-8")
def w(**k):
    out.write(json.dumps(k,ensure_ascii=False)+"\n"); out.flush()
INC={"n":[f'.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice"',f'.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"'],
     "p":[f'.include "{PDK}/models/parameters/lod.spice"',f'.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice"',f'.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice"']}
SUB={"n":"sky130_fd_pr__nfet_01v8","p":"sky130_fd_pr__pfet_01v8"}
env=dict(os.environ);home=tempfile.mkdtemp();env["HOME"]=env["USERPROFILE"]=home
for k in ("HOMEDRIVE","HOMEPATH","SPICE_USERINIT_DIR"): env.pop(k,None)
def run(text):
    d=tempfile.mkdtemp();p=os.path.join(d,"t.cir");open(p,"w",newline="\n").write(text)
    r=subprocess.run([EXE,"-b",p],cwd=d,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace")
    return r.stdout+r.stderr
d=json.load(open(W+"/skills/analog-gmid-design/assets/lut_v2_bin_rule.json",encoding="utf-8"))
sys.path.insert(0,W+"/.ai/verification/20261104-op7a/scripts")
pts={"n":[],"p":[]}
for q in d["evidence"]["points"]:
    pts["n" if "nfet" in q["chosen_bin"] else "p"].append((q["L"],q["W"],q["chosen_bin"]))
pm=open(PDK+"/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice",encoding="utf-8",errors="replace").read()
def bins(path):
    t=open(path,encoding="utf-8",errors="replace").read()
    res={}
    for m in re.finditer(r"\.model\s+(\S+)\s+\w+\s*\n(.*?)(?=\n\.model|\Z)",t,re.S|re.I):
        b=m.group(2);g=lambda k:float(re.search(rf"\b{k}\s*=\s*([-+0-9.eE]+)",b).group(1))
        res[(g("lmin"),g("lmax"),g("wmin"),g("wmax"))]=m.group(1)
    return res
TAB={"n":bins(PDK+"/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice"),"p":bins(PDK+"/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice")}
def showlines(k,P,fmt):
    L=["* t"]+INC[k]+[".option scale=1u","vgs g 0 dc 0","vds d 0 dc 0","vsrc s 0 dc 0","vb b 0 dc 0"]
    for i,(l,wd,_) in enumerate(P):
        L.append(f"xp{i} d g s b {SUB[k]} l={fmt(l/1e-6)} w={fmt(wd/1e-6)}")
    L+=[".control","op"]
    for i in range(len(P)):
        L+=[f"echo SHOWMOD p{i}",f"showmod m.xp{i}.m{SUB[k]} : lmin lmax wmin wmax"]
    L+=["quit",".endc",".end"]
    return "\n".join(L)+"\n"
for name,fmt in (("repr",repr),("num8g",lambda x:f"{x:.8g}"),("num15g",lambda x:f"{x:.15g}")):
    tot=0;diff=[];none=0
    for k in "np":
        P=pts[k]
        for s in range(0,len(P),60):
            ch=P[s:s+60]
            t=run(showlines(k,ch,fmt))
            blks=re.split(r"SHOWMOD ",t)[1:]
            got={}
            for blk in blks:
                i=int(blk.split()[0][1:]);vals=[]
                for key in ("lmin","lmax","wmin","wmax"):
                    m=re.search(rf"^\s*{key}\s+([-+0-9.eE]+)",blk,re.M);vals.append(float(m.group(1)) if m else None)
                got[i]=tuple(vals)
            for i,pt in enumerate(ch):
                tot+=1
                b=TAB[k].get(got.get(i));
                if b is None: none+=1
                elif b.lower()!=pt[2].lower(): diff.append({"k":k,"L":pt[0],"W":pt[1],"decl":pt[2],"got":b,"lu":fmt(pt[0]/1e-6)})
    w(m="format_vs_decl",fmt=name,points=tot,differ=len(diff),unmatched=none,ex=diff[:12])
t=run("\n".join(["* g"]+INC["n"]+[".option scale=1u",f"Xm1 d g 0 0 {SUB['n']} l=0.5 w=2 m=2 mult=2 ad=1 as=1 pd=4 ps=4","Vg g 0 DC 0.7","Vd d 0 DC 0.9",".control","op"]+[f"print @m.xm1.m{SUB['n']}[{q}]" for q in ("l","w","m","ad","pd","id")]+["quit",".endc",".end"])+"\n")
w(m="readback_scale",lines=[l for l in t.splitlines() if "@m." in l])
t=run("\n".join(["* g"]+INC["n"]+[f"Xm1 d g 0 0 {SUB['n']} l=5e-07 w=2e-06 m=2 ad=1e-12 as=1e-12 pd=4e-06 ps=4e-06","Vg g 0 DC 0.7","Vd d 0 DC 0.9",".control","op"]+[f"print @m.xm1.m{SUB['n']}[{q}]" for q in ("l","w","m","ad","pd","id")]+["quit",".endc",".end"])+"\n")
w(m="readback_si",lines=[l for l in t.splitlines() if "@m." in l])
