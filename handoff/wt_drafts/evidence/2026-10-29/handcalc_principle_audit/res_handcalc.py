"""저항 손계산 꼴 오차: (H-a) l = R/rsheet(머리 무시) 로 C_par 계산 vs 셀 역산 l(ngspice pow 의미, 검증 7 식).
식·계수 출처: 검증 5·6·7 (셀 _0p35 :41-56, res_typical__cap_typical :40-45). 결과 = res_handcalc.out.txt"""
import math
rs=1112.41; rcon=589.99; k=0.724; w=0.35; crpf=1.06e-4*1e-12; crpfsw=None
# crpfsw_precision_1_1 [F/m] -- 검증5 값 5.04e-11 F/m (=> *1e-6 per um)
crpfsw=5.04e-11*1e-6
def Rcell(l): return l*rs+rcon*(1+k/math.sqrt(l))
def Cpar(l): return (l+2*2.08)*w*crpf+2*(l+2*2.08+w)*crpfsw
def inv(R):
    lo,hi=0.333,1e5
    if Rcell(lo)>R: return None
    for _ in range(200):
        m=(lo+hi)/2
        if Rcell(m)<R: lo=m
        else: hi=m
    return lo
o=open("res_handcalc.out.txt","w",encoding="utf-8")
o.write("R[ohm] l_naive l_cell C_naive[fF] C_cell[fF] C비 | w*R*C_cell@30MHz | 머리상수 rcon만 역산시 셀R/R\n")
for R in (2e3,4.383e3,1e4,7.01e4,1e5,1e6):
    ln=R/rs; lc=inv(R); cn=Cpar(ln)*1e15; cc=Cpar(lc)*1e15 if lc else float('nan')
    lr=(R-rcon)/rs; rr=Rcell(lr)/R if lr>0 else float('nan')
    o.write(f"{R:9.0f} {ln:8.3f} {lc if lc else float('nan'):8.3f} {cn:7.3f} {cc:7.3f} {cn/cc:6.3f} | {2*math.pi*30e6*R*cc*1e-15:.2e} | {rr:.3f}\n")
o.write(f"R_min = {Rcell(0.333):.0f} ohm at l*=0.333um\n")
o.close(); print(open("res_handcalc.out.txt",encoding="utf-8").read())
