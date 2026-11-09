"""T 망(nmcnr Structure 4) 손계산 모델 수치 영점 -- 파일럿 설계점 wt/_pilot_nmcnr/design_point.json 값.
C2 = NodeS2 접지 용량(M301 Cgg + M204/M202 drain 근사), Rm 후보 = 1/gm3(R_S), R_null 식, 그 사이."""
import json, sympy as sp, numpy as np, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t_numeric.out.jsonl"); open(OUT,"w").close()
d = json.load(open("C:/Users/HSLEE/Documents/Todoc/fpga/wt/_pilot_nmcnr/design_point.json", encoding="utf-8"))
P, D = d["params"], d["devices"]
s = sp.symbols('s')
g1,C1,G1,gm2,gmd,Cn,gm4,G2,C2,gm3,Go,CL,Cm1,Cm2,Rm = sp.symbols('g1 C1 G1 gm2 gmd Cn gm4 G2 C2 gm3 Go CL Cm1 Cm2 Rm')
v1,vc,v2,vo,vm,vin = sp.symbols('v1 vc v2 vo vm vin')
eqs=[sp.Eq(0,g1*vin+v1*(G1+s*C1)+(v1-vm)*s*Cm1), sp.Eq(0,-gm2*v1+vc*(gmd+s*Cn)),
     sp.Eq(0,gm4*vc+v2*(G2+s*C2)+(v2-vm)*s*Cm2), sp.Eq(0,gm3*v2+vo*(Go+s*CL)+(vo-vm)/Rm),
     sp.Eq(0,(vm-v1)*s*Cm1+(vm-v2)*s*Cm2+(vm-vo)/Rm)]
sol=sp.solve(eqs,[v1,vc,v2,vo,vm],dict=True)[0]
num,den=sp.fraction(sp.together(sol[vo])); Np=sp.Poly(sp.expand(num.subs(vin,1)),s)
gm3v=P["gm3"]
C2v = D["M301"]["CGG_W"]*D["M301"]["W"] + 2e-15   # + drain 근사(작음)
base={g1:P["gm1"],C1:D["M201"]["CGG_W"]*D["M201"]["W"]+5e-15,G1:P["gm1"]/50,gm2:P["gm2"],gmd:D["M203"]["gm"],Cn:3e-15,
      gm4:D["M204"]["gm"],G2:D["M204"]["gm"]/100,C2:C2v,gm3:gm3v,Go:1/25e3,CL:1e-12,Cm1:P["Cm1"],Cm2:P["Cm2"]}
Rnull=(C2v+P["Cm2"])/(P["Cm2"]*gm3v)
for lab,R in (("R_S=1/gm3",1/gm3v),("pilot Rm",P["Rm"]),("R_null",Rnull),("1.1*R_null",1.1*Rnull),("C2=0 control R_S",None)):
    sub=dict(base); 
    if R is None: sub[C2]=0.0; R=1/gm3v
    sub[Rm]=R
    c=[float(sp.N(x.subs(sub))) for x in Np.all_coeffs()]
    while abs(c[0])<1e-80: c=c[1:]
    z=np.roots(c)
    rec={"label":lab,"Rm":R,"C2":sub[C2],"Cm2":P["Cm2"],"zeros_Hz":[str(complex(x)/(2*np.pi)) for x in z],"n_rhp":int(sum(1 for x in z if x.real>0))}
    open(OUT,"a").write(json.dumps(rec)+"\n"); print(rec)
print("R_null/R_S =", Rnull*gm3v)
