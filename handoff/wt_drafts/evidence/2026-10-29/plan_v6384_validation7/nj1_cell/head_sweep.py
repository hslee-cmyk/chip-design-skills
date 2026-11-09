# 검증 7 NJ-1: _0p35 셀 R(l) 의 머리 항이 l 에 무관(상수)인지 -- R_cell(l) - l*rsheet 를 l 스윕으로 잼
import os, subprocess, re, math, sys
PDK='C:/pdk/sky130_fd_pr'; NG=r'C:\ngspice\Spice64\bin\ngspice_con.exe'
HERE=os.path.dirname(os.path.abspath(__file__))
out=open(os.path.join(HERE, sys.argv[1] if len(sys.argv)>1 else 'head_sweep.txt'),'w',encoding='utf-8')
def w(s): print(s); out.write(s+'\n'); out.flush()
RSHEET=1112.41; RCON=589.99
inc=[f'.include "{PDK}/models/r+c/res_typical__cap_typical__lin.spice"',
     '.param sky130_fd_pr__res_high_po__slope_spectre = 0.0 sky130_fd_pr__res_high_po__con_slope_spectre = 0.0',
     '.param crpf_precision = 1.06e-4 crpfsw_precision_1_1 = 5.04e-11',
     f'.include "{PDK}/cells/res_high_po/sky130_fd_pr__res_high_po_0p35.model.spice"']
TEMP=float(sys.argv[2]) if len(sys.argv)>2 else 27.0
k_raw=(-1.7)*(-2.02e-2)+(1.7**2)*1.55e-1+(-1.7**3)*4.61e-2
def rend_formula(l,T): return RCON*(1+k_raw/math.sqrt(l)*(1-7.1e-3*(T-30)))
w(f'TEMP={TEMP}  k_raw(dV=0)={k_raw:.5f}')
w('l[um]  R_cell(dV=1uV)  R_cell-l*rsheet  rend_formula(l)  rbody_tc?')
def meas(l,dv=1e-6):
    net=['* c']+inc+[f'.option temp={TEMP}',f'v1 a 0 dc {dv}','vb b 0 dc 0',f'x1 a 0 b sky130_fd_pr__res_high_po_0p35 l={l} w=0.35',
         '.control','op','print -i(v1)','quit','.endc','.end']
    cir=os.path.join(HERE,'h.cir'); open(cir,'w').write('\n'.join(net)+'\n')
    r=subprocess.run([NG,'-b',cir],capture_output=True,text=True)
    n=re.findall(r'i\(v1\)\)? = ([-+0-9.eE]+)',r.stdout)
    return dv/float(n[0])
for l in (0.5,1,2,4,8.989,20,50,89.895,200,898.949):
    R=meas(l)
    w(f'{l:9.3f} {R:14.2f} {R-l*RSHEET:12.2f} {rend_formula(l,TEMP):10.2f} ratio_body={(R-rend_formula(l,TEMP))/(l*RSHEET):.6f}')
