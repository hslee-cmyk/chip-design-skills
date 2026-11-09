"""검증 3 독립 재현: W 슬라이스 DC LUT(pfet W0p42) VDS=0·VS=0 점 gds 표본, 축 부호·격자 정확 일치 확인."""
import math, numpy as np, glob
P="C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_fd_pr__pfet_01v8__tt__W0p4200um_dc.npz"
O="C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6385_validation3/zg1_repro.txt"
d=np.load(P,allow_pickle=True)
out=open(O,'w',encoding='utf-8')
out.write('keys %s\n'%list(d.keys()))
for k in d.keys():
    a=d[k]
    if a.ndim<=1 and a.size<200: out.write('%s %s\n'%(k,np.array2string(np.asarray(a),max_line_width=400)))
    else: out.write('%s shape %s\n'%(k,a.shape))
L=d['L'];V=d['VGS'];VD=d['VDS'];VS=d['VS'];G=d['GDS'];GM=d['GM']
ID=d['ID'] if 'ID' in d else None
for l_um,vsg in [(0.15,0.375),(0.15,0.6),(0.5,0.375),(1.0,0.375),(0.15,0.3)]:
    li=int(np.argmin(abs(L-l_um*1e-6))); vi=int(np.argmin(abs(V-vsg)))
    exact=(abs(L[li]-l_um*1e-6)<1e-12, abs(V[vi]-vsg)<1e-9)
    g=float(G[li,vi,0,0]); gm=float(GM[li,vi,0,0]); idv=float(ID[li,vi,0,0]) if ID is not None else float('nan')
    out.write('L=%g VGSaxis=%g exact=%s VDS0=%g VS0=%g gds=%.4e gm=%.3e ID=%.3e R=%.4e fHP(0.1pF)/1.37MHz=%.3e\n'%(L[li],V[vi],exact,VD[0],VS[0],g,gm,idv,1/g,g/(2*math.pi*1e-13)/1.37e6))
out.close(); print(open(O,encoding='utf-8').read())
