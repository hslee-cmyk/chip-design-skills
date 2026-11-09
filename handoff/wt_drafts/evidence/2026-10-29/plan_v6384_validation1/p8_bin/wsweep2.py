"""wsweep.py 정정판: ngspice bin 선택 허용오차(경계 -1 nm부터 위 bin, binsel3.log) 때문에 경계 표본을 경계-3 nm(자기 모델)로, 계단은 양쪽 외삽."""
"""검증 1 P8: sky130 pfet_01v8·nfet_01v8 L=0.15 µm에서 단위 폭 전류 IDu(w)와 gm/ID(w)를 w 촘촘히(bin 경계 ±1 nm 포함) 재서
(1) bin 경계 계단 유무 (2) bin 안 선형 보간(w 대 1/w) 오차를 잰다. ngspice_con -b, 결과 wsweep2.out.jsonl(케이스마다 append)."""
import subprocess, os, json, re, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"wsweep2.out.jsonl"); open(OUT,"w").close()
NG="C:/ngspice/Spice64/bin/ngspice_con.exe"
def edges(kind):
    t=open(f"C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__tt.pm3.spice",encoding="utf-8",errors="replace").read()
    ws=set()
    for m in re.split(r'\n\.model\s+',t)[1:]:
        g={k:float(re.search(r'\b'+k+r'\s*=\s*([0-9.eE+-]+)',m).group(1)) for k in ('lmin','lmax','wmin','wmax')}
        if g['lmin']<=0.15e-6<g['lmax']: ws.add(round(g['wmin']*1e6,4)); ws.add(round(g['wmax']*1e6,4))
    return sorted(ws)
def run(kind, vov, vds, ws):
    inc=f'.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"\n.include "C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__tt.pm3.spice"\n.include "C:/pdk/sky130_fd_pr/cells/{kind}_01v8/sky130_fd_pr__{kind}_01v8__mismatch.corner.spice"\n'
    if kind=="pfet": src=f"vs s 0 1.8\nvg g 0 {1.8-vov}\nvd d 0 {1.8-vds}\n"; b="s"
    else: src=f"vs s 0 0\nvg g 0 {vov}\nvd d 0 {vds}\n"; b="s"
    lines=[f"* sweep {kind}",inc,src]
    for i,w in enumerate(ws): lines.append(f"x{i} d g s {b} sky130_fd_pr__{kind}_01v8 l=0.15u w={w}u")
    ctl=[".control","op"]+[f"echo R {i} $&@m.x{i}.msky130_fd_pr__{kind}_01v8[id] $&@m.x{i}.msky130_fd_pr__{kind}_01v8[gm]" for i in range(len(ws))]+["quit",".endc",".end"]
    fn=os.path.join(HERE,f"ws_{kind}_{vov}_{vds}.cir"); open(fn,"w").write("\n".join(lines+ctl)+"\n")
    o=subprocess.run([NG,"-b",fn],capture_output=True,text=True).stdout
    res={}
    for l in o.splitlines():
        p=l.split()
        if len(p)==4 and p[0]=="R": res[int(p[1])]=(abs(float(p[2])),abs(float(p[3])))
    return [(w,res[i][0]/(w*1e-6),res[i][1]/res[i][0]) for i,w in enumerate(ws) if i in res]
for kind in ("pfet","nfet"):
    E=edges(kind); Emin=E[0]
    ws=set()
    for a,b in zip(E[:-1],E[1:]):
        if b>8: continue
        for x in np.linspace(a,b,9): ws.add(round(float(x),5))
        ws.discard(round(b,5)); ws.add(round(b-0.003,5)); ws.add(round(b-0.006,5)); ws.add(round(a+0.003,5)); ws.add(round(b,5))
    ws=sorted(w for w in ws if w>=Emin)
    for vov,vds in ((0.45,0.9),(0.6,0.9),(0.8,0.9),(0.6,0.2),(1.0,0.9)):
        data=run(kind,vov,vds,ws)
        d={w:(i,g) for w,i,g in data}
        # (1) edge step: compare idu at b-0.5nm vs b+0.5nm
        steps=[]
        for b in E:
            l1=round(b-0.003,5); l2=round(b-0.006,5); h1=round(b,5); h2=round(b+0.003,5)
            if all(x in d for x in (l1,l2,h1,h2)):
                left=d[l1][0]+(d[l1][0]-d[l2][0]); right=d[h1][0]-(d[h2][0]-d[h1][0])  # 경계로 선형 외삽(각 쪽 자기 모델)
                steps.append({"edge":b,"idu_rel_step":right/left-1})
        # (2) in-bin interp error using bin edge samples a,b (as two slices) at interior 7 points
        interp=[]
        for a,b in zip(E[:-1],E[1:]):
            bb=round(b-0.003,5)
            if b>8 or round(a,5) not in d or bb not in d: continue
            ia,ib=d[round(a,5)][0],d[bb][0]; ga,gb=d[round(a,5)][1],d[bb][1]; b0=b; b=bb
            errw=[];errinv=[];errg=[]
            for x in np.linspace(a,b0,9)[1:-1]:
                x=round(float(x),5); 
                if x not in d: continue
                t=(x-a)/(b-a); ti=(1/x-1/a)/(1/b-1/a)
                errw.append((ia+t*(ib-ia))/d[x][0]-1); errinv.append((ia+ti*(ib-ia))/d[x][0]-1); errg.append((ga+t*(gb-ga))/d[x][1]-1)
            interp.append({"bin":[a,b],"idu_end_ratio":ib/ia,"max_abs_err_lin_w":max(map(abs,errw)),"max_abs_err_lin_invw":max(map(abs,errinv)),"max_abs_err_gmid_lin_w":max(map(abs,errg))})
        rec={"kind":kind,"vov_vgs_abs":vov,"vds_abs":vds,"n_w":len(data),"max_edge_idu_step":max((abs(s["idu_rel_step"]) for s in steps),default=None),"steps":steps,"interp":interp}
        open(OUT,"a",encoding="utf-8").write(json.dumps(rec)+"\n")
        print(kind,vov,vds,"max edge step",rec["max_edge_idu_step"], "max interp err lin_w", max(x["max_abs_err_lin_w"] for x in interp), "lin_invw", max(x["max_abs_err_lin_invw"] for x in interp))
