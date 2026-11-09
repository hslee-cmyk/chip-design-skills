# 검증 6 O-171 MJ-2: PDK 셀 X 인스턴스(res_high_po_0p35)의 R 이 '시트 저항 x 길이' 기하와 같은 값인가
# l = R_target / rsheet(셀 rsheet = 1112.41 Ohm/um, 폭 0.35 um 고정) 로 두고 DC 소신호 R(작은 차 전압)과 0.5 V 차 전압 R 을 잰다.
# 또 같은 셀의 C 쌍(C/2 x 2)을 AC 로 확인: r1 접지, r0 에 AC 1 V -> 저주파 R 로 나눈 뒤 남는 허수부 = 2*pi*f*C/2 (r0 쪽 C/2)
import os, subprocess, re, math
PDK = 'C:/pdk/sky130_fd_pr'; NG = r'C:\ngspice\Spice64\bin\ngspice_con.exe'
HERE = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(HERE, 'cell_r.txt'), 'w', encoding='utf-8')
def w(s): print(s); out.write(s + '\n'); out.flush()
RSHEET = 1112.41
CRPF, CRPFSW = 1.06e-4, 5.04e-11
inc = [f'.include "{PDK}/models/r+c/res_typical__cap_typical__lin.spice"',
       '.param sky130_fd_pr__res_high_po__slope_spectre = 0.0 sky130_fd_pr__res_high_po__con_slope_spectre = 0.0',  # = models/sky130_fd_pr__model__linear.model.spice:16-17 (그 파일은 sparse checkout 에 없는 셀을 include)
       f'.param crpf_precision = {CRPF} crpfsw_precision_1_1 = {CRPFSW}',
       f'.include "{PDK}/cells/res_high_po/sky130_fd_pr__res_high_po_0p35.model.spice"']
w('R_target[Ohm]  l[um]  R_cell(dV=1mV)  R_cell/R_target  R_cell(dV=0.5V)/R_target  C_par_formula[fF]  C_r0_from_AC[fF]')
for R in (1e4, 1e5, 1e6):
    l = R / RSHEET
    rows = []
    for dv in (1e-3, 0.5):
        net = ['* cell'] + inc + [f'v1 a 0 dc {dv} ac 1', 'vb b 0 dc 0',
               f'x1 a 0 b sky130_fd_pr__res_high_po_0p35 l={l} w=0.35',
               '.control', 'op', 'print -i(v1)', 'ac lin 1 1k 1k', 'print imag(-i(v1))', 'quit', '.endc', '.end']
        cir = os.path.join(HERE, 'c.cir'); open(cir, 'w').write('\n'.join(net) + '\n')
        r = subprocess.run([NG, '-b', cir], capture_output=True, text=True)
        nums = re.findall(r'i\(v1\)\)? = ([-+0-9.eE]+)', r.stdout)
        if len(nums) < 2:
            w('ERR ' + r.stdout[-800:] + r.stderr[-800:]); break
        i_dc = float(nums[0]); im = float(nums[-1])
        rows.append((dv / i_dc, im / (2 * math.pi * 1e3)))
    if len(rows) < 2: continue
    cpar = (l + 2 * 2.08) * 0.35 * CRPF * 1e-12 + 2 * (l + 2 * 2.08 + 0.35) * CRPFSW * 1e-6
    w(f'{R:10.0f} {l:9.3f} {rows[0][0]:12.1f} {rows[0][0]/R:8.4f} {rows[1][0]/R:8.4f} {cpar*1e15:9.3f} {rows[0][1]*1e15:9.3f} (C/2 = {cpar/2*1e15:.3f})')
