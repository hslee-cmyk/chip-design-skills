"""검증 3 추가 검사: Q-ZG1 W 대 L. pfet W 슬라이스 DC LUT, VDS = 0, VS = 0(bulk = source), tt.
(1) gds 대 W(같은 L·VSG): R·W가 상수(1/W 선형)인가 (2) 같은 R을 얻는 (W, L) 조합의 면적 W·L (3) R_min(W) at L_min.
L 보간(2)은 log R 대 L 선형 보간 -- 비교용 추정(같은 bin 규칙 아님, 격자점 실측과 구분 표기)."""
import glob, math, re, numpy as np
D="C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
O="C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation3/zg1_w.txt"
fs=sorted(glob.glob(D+"sky130_fd_pr__pfet_01v8__tt__W*um_dc.npz"))
S={}
for f in fs:
    d=np.load(f,allow_pickle=True)
    assert d['VDS'][0]==0 and d['VS'][0]==0
    S[float(d['W'])]=(d['L'],d['VGS'],d['GDS'],d['GM'],d['ID'])
Ws=sorted(S)
out=open(O,'w',encoding='utf-8')
out.write("source: %s (pfet tt, VDS=0, VS=0 = bulk=source)\nW slices um: %s\n\n"%(D,[round(w*1e6,3) for w in Ws]))
def g(W,l,v):
    L,V,G,GM,ID=S[W]; li=np.where(abs(L-l)<1e-12)[0]; vi=np.where(abs(V-v)<1e-9)[0]
    if len(li)==0 or len(vi)==0: return None
    return float(G[li[0],vi[0],0,0]),float(GM[li[0],vi[0],0,0]),float(ID[li[0],vi[0],0,0])
VSGs=(0.3,0.375,0.4125)
out.write("## (1) gds 대 W (격자점 실측). R·W 정규화 = (R·W)/(R·W at W_min) -- 1이면 1/W 선형\n")
for l in (0.15e-6,0.5e-6,1e-6):
    for v in VSGs:
        out.write("\nL=%.3g um, VSG=%.4g V\n| W um | gds S | gm S | ID A | R Ohm | gds/W (S/um) | R·W 정규화 |\n|---|---|---|---|---|---|---|\n"%(l*1e6,v))
        r0=None
        for W in Ws:
            x=g(W,l,v)
            if x is None: out.write("| %.3g | (L 격자 없음) |\n"%(W*1e6)); continue
            gd,gm,idv=x; R=1/gd; rw=R*W
            if r0 is None: r0=rw
            out.write("| %.3g | %.4e | %.1e | %.1e | %.4e | %.4e | %.3f |\n"%(W*1e6,gd,gm,idv,R,gd/(W*1e6),rw/r0))
out.write("\n## (2) 같은 R의 (W, L) 조합 면적 W·L (VSG 0.375 V; L은 log R 대 L 선형 보간 -- 추정)\n")
v=0.375
def L_for_R(W,Rt):
    L,V,G,_,_=S[W]; vi=int(np.where(abs(V-v)<1e-9)[0][0]); lr=np.log(1/G[:,vi,0,0])
    # monotone in L assumed; find bracket
    for k in range(len(L)-1):
        a,b=lr[k],lr[k+1]
        if (a-math.log(Rt))*(b-math.log(Rt))<=0 and a!=b:
            t=(math.log(Rt)-a)/(b-a); return L[k]+t*(L[k+1]-L[k])
    return None
for Rt in (1e7,1e8,1e9,1e10,1e11):
    out.write("\nR target %.0e Ohm\n| W um | L um | W·L um2 |\n|---|---|---|\n"%Rt)
    for W in Ws:
        Lx=L_for_R(W,Rt)
        if Lx is None: out.write("| %.3g | 범위 밖(L 격자 [0.15, 20] um에서 도달 못함) | - |\n"%(W*1e6)); continue
        out.write("| %.3g | %.4g | %.4g |\n"%(W*1e6,Lx*1e6,W*Lx*1e12))
out.write("\n## (3) L_min(0.15 um)에서 R_min(W) -- R을 줄여야 할 때 W 축이 필요한 범위\n| W um | R @VSG0.3 | R @0.375 | R @0.4125 |\n|---|---|---|---|\n")
for W in Ws:
    rs=[]
    for vv in VSGs:
        x=g(W,0.15e-6,vv); rs.append("%.3e"%(1/x[0]) if x else "-")
    out.write("| %.3g | %s |\n"%(W*1e6," | ".join(rs)))
out.close(); print(open(O,encoding='utf-8').read())
