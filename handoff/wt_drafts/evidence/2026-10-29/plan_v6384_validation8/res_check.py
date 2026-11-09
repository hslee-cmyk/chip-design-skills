# 검증 8: 저항 손계산 꼴 점검 (l 정의 표기, R_min 대 선언 저항, C_par)
import math
rsheet_cell=1112.41   # Ohm per um, _0p35 cell param (fixed w=0.35)
w=0.35
Rsq=rsheet_cell*w     # Ohm/sq
rcon=589.99
crpf=1.06e-4; crpfsw=5.04e-11
def C(l):  # cell formula, l,w in um
    return ((l+2*2.08)*w*crpf*1e-12+2*(l+2*2.08+w)*crpfsw*1e-6)
out=[]
out.append(f"R_sq = rsheet_cell*w = {Rsq:.2f} Ohm/sq")
for R in [1412,1701,2e3,1e4,1e5,1e6]:
    l_ok=R/rsheet_cell           # = R*w/R_sq
    l_bad=R*w/rsheet_cell        # literal reading with cell rsheet (Ohm/um)
    out.append(f"R={R:>9.0f}  l(R/rsheet_cell)={l_ok:9.3f} um C={C(l_ok)*1e15:8.2f} fF | literal l(R*w/rsheet_cell)={l_bad:9.3f} um C={C(l_bad)*1e15:8.2f} fF ratio={C(l_bad)/C(l_ok):.3f}")
# R_min from audit (ngspice semantics k=0.724): head-only value at l->? just report body-only minimum feasibility
out.append("heldout rfc_ota RB = 1412 Ohm (value declared, DUT bias resistor) < R_min 1701 Ohm (_0p35)")
out.append(f"single cell head alone rcon={rcon} Ohm; R_min (audit, ngspice pow semantics) = 1701 Ohm at l*=0.333 um")
open('res_check.out.txt','w',encoding='utf-8').write("\n".join(out)+"\n")
print("\n".join(out))
