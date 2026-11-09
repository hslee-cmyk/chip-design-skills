"""T 망 sweep: Cn·C2·Rm(×1/gm3)별 우반면 영점 수 -- 손계산 모델 안정 쪽 방향 확인."""
import json, sympy as sp, numpy as np, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"t_numeric.py"),encoding="utf-8").read().split("gm3v=P")[0])
gm3v=P["gm3"]
OUT2=os.path.join(os.path.dirname(os.path.abspath(__file__)),"t_sweep.out.jsonl"); open(OUT2,"w").close()
base={g1:P["gm1"],C1:D["M201"]["CGG_W"]*D["M201"]["W"]+5e-15,G1:P["gm1"]/50,gm2:P["gm2"],gmd:D["M203"]["gm"],
      gm4:D["M204"]["gm"],G2:D["M204"]["gm"]/100,gm3:gm3v,Go:1/25e3,CL:1e-12,Cm1:P["Cm1"],Cm2:P["Cm2"]}
cnt={}
for Cnv in (0.0,1e-16,3e-15,3e-14):
  for C2v in (0.0,7e-14,3e-13,1e-12):
    Rn=(C2v+P["Cm2"])/(P["Cm2"]*gm3v)
    for k in (0.8,0.95,1.0,1.05,"Rnull",1.2,1.5,2.0):
      R=Rn if k=="Rnull" else k/gm3v
      sub=dict(base); sub.update({Cn:Cnv,C2:C2v,Rm:R})
      c=[float(sp.N(x.subs(sub))) for x in Np.all_coeffs()]
      while len(c)>1 and abs(c[0])<1e-90: c=c[1:]
      z=np.roots(c) if len(c)>1 else []
      nr=int(sum(1 for x in z if x.real>0 and abs(x)<1e15))
      rec={"Cn":Cnv,"C2":C2v,"R_over_RS":R*gm3v,"Rnull_over_RS":Rn*gm3v,"n_rhp_finite":nr}
      open(OUT2,"a").write(json.dumps(rec)+"\n")
      print(rec)
