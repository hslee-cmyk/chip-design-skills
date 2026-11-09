# 검증 7 NJ-1: 셀 R 식 역산 -- (i) 머리 = rcon 상수(1차 가정) (ii) 수학적 부호 pow (iii) ngspice 평가(pow 음수 밑 = |x|^y)
# 각 l 로 ngspice X 인스턴스 R(dV=1uV) 을 재서 theta R 재현 여부. 또 DC 차 전압 0.05/0.5/0.8 V 에서 R/R(0).
import os, subprocess, re, math
from scipy.optimize import brentq
PDK = 'C:/pdk/sky130_fd_pr'; NG = r'C:\ngspice\Spice64\bin\ngspice_con.exe'
HERE = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(HERE, 'invert.txt'), 'w', encoding='utf-8')
def w(s): print(s); out.write(s + '\n'); out.flush()
RSHEET = 1112.41; RCON = 589.99; T = 27.0
tf = 1 + (-7.1e-3) * (T - 30)
x = -1.7
k_signed = (x * -2.02e-2 + x**2 * 1.55e-1 + x**3 * 4.61e-2) * tf
k_ngspice = (x * -2.02e-2 + abs(x)**2 * 1.55e-1 + abs(x)**3 * 4.61e-2) * tf
inc = [f'.include "{PDK}/models/r+c/res_typical__cap_typical__lin.spice"',
       '.param sky130_fd_pr__res_high_po__slope_spectre = 0.0 sky130_fd_pr__res_high_po__con_slope_spectre = 0.0',
       '.param crpf_precision = 1.06e-4 crpfsw_precision_1_1 = 5.04e-11',
       f'.include "{PDK}/cells/res_high_po/sky130_fd_pr__res_high_po_0p35.model.spice"']
def meas(l, dv):
    net = ['* c'] + inc + [f'.option temp={T}', f'v1 a 0 dc {dv}', 'vb b 0 dc 0', f'x1 a 0 b sky130_fd_pr__res_high_po_0p35 l={l} w=0.35',
           '.control', 'op', 'print -i(v1)', 'quit', '.endc', '.end']
    cir = os.path.join(HERE, 'i.cir'); open(cir, 'w').write('\n'.join(net) + '\n')
    r = subprocess.run([NG, '-b', cir], capture_output=True, text=True)
    return dv / float(re.findall(r'i\(v1\)\)? = ([-+0-9.eE]+)', r.stdout)[0])
def R_of(l, k): return l * RSHEET + RCON * (1 + k / math.sqrt(l))
w(f'k_signed(dV=0) = {k_signed:.5f}, k_ngspice(dV=0) = {k_ngspice:.5f}  (R_cell(l) = l*rsheet + rcon*(1 + k/sqrt(l)) -- l 에 1차가 아님)')
w('R_target  | l(i) 머리상수  R_ng/R | l(ii) 수학 pow  R_ng/R | l(iii) ngspice식  R_ng/R | R(0.05V)/R(0) R(0.5V)/R(0) R(0.8V)/R(0) at l(iii)')
for R in (2e3, 4383.386, 1e4, 7.01342e4, 1e5, 1e6):
    l1 = (R - RCON) / RSHEET
    l2 = brentq(lambda l: R_of(l, k_signed) - R, 0.4, 1e4)
    l3 = brentq(lambda l: R_of(l, k_ngspice) - R, 0.4, 1e4)
    r1, r2, r3 = meas(l1, 1e-6), meas(l2, 1e-6), meas(l3, 1e-6)
    dc = [meas(l3, v) / r3 for v in (0.05, 0.5, 0.8)]
    w(f'{R:9.1f} | {l1:8.3f} {r1/R:.5f} | {l2:8.3f} {r2/R:.5f} | {l3:8.3f} {r3/R:.6f} | {dc[0]:.5f} {dc[1]:.5f} {dc[2]:.5f}')
