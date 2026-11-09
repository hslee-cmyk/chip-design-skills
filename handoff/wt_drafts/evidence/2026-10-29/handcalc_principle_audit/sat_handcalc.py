"""포화 문턱 손계산 꼴 비교 (NJ-2' 대체 후보). 입력 = 검증 7 sat.txt (SPICE 측정값, 재실행 안 함).
H0 = BSIM VDsat(엔진 LUT VDSAT 열과 같은 양), H1 = max(VDsat, U_T ln(1/eps)).
기준 = (B) 역방향 분율 VDS*(eps). 결과 = sat_handcalc.out.txt"""
import re
src="C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6384_validation7/nj2_sat/sat.txt"
o=open("sat_handcalc.out.txt","w",encoding="utf-8")
rows=[]
for l in open(src,encoding="utf-8"):
    m=re.match(r"(pfet|nfet) (\S+) (\S+)\s+(\S+) (\S+) \|.*B\s+(\S+) mV \| VDsat\s+(\S+) mV \|\s+(\S+) mV",l)
    if not m: continue
    k,L,vgs,gmid,eps,B,vd,ut=m.groups(); B,vd,ut,gmid=float(B),float(vd),float(ut),float(gmid)
    h1=max(vd,ut); rows.append((k,L,vgs,gmid,B,vd,h1))
    o.write(f"{k} L{L} VGS{vgs} gm/ID {gmid:5.1f}: VDS*_B {B:6.1f}  H0 {vd:6.1f} (차 {vd-B:+6.1f})  H1 {h1:6.1f} (차 {h1-B:+6.1f})\n")
for name,idx in (("H0",5),("H1",6)):
    d=[r[idx]-r[4] for r in rows]; wi=[r[idx]-r[4] for r in rows if r[3]>=17]; si=[r[idx]-r[4] for r in rows if r[3]<17]
    o.write(f"{name}: 전체 차 min {min(d):+.0f} max {max(d):+.0f} mV; 약반전(gm/ID>=17) {min(wi):+.0f}~{max(wi):+.0f}; 강반전 {min(si):+.0f}~{max(si):+.0f}\n")
o.close(); print(open("sat_handcalc.out.txt",encoding="utf-8").read()[-400:])
