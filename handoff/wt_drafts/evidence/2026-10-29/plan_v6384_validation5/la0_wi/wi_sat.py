# 검증 5 O-171: 약반전 포화 -- .op gds 로 확산 항을 CLM/DIBL 과 가를 수 있는가, gm/ID 점근 '붙음' 판정이 무엇을 고르는가
import subprocess, os, math, re, sys
PDK = r"C:\pdk\sky130_fd_pr"; NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
inc = [f'.include "{os.path.join(PDK,"models","parameters","lod.spice")}"',
       rf'.include "{PDK}\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__tt.pm3.spice"',
       rf'.include "{PDK}\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"']
out = open('wi_sat.txt', 'w', encoding='utf-8')
def w(s): print(s); out.write(s + '\n'); out.flush()
UT = 0.025852  # kT/q @ 27C
def run(L, vgs_list, vds_list):
    net = ['* wi'] + inc + ['vg g 0 dc 0', 'vd d 0 dc 0', 'vs s 0 dc 0', 'vb b 0 dc 0',
           f'xdut d g s b sky130_fd_pr__pfet_01v8 l={L}u w=5u ad=2.5p as=2.5p pd=7u ps=7u', '.control']
    for vg in vgs_list:
        for vd in vds_list:
            net += [f'alter vg = {-vg}', f'alter vd = {-vd}', 'op', 'echo P',
                    'print @m.xdut.msky130_fd_pr__pfet_01v8[id]', 'print @m.xdut.msky130_fd_pr__pfet_01v8[gm]',
                    'print @m.xdut.msky130_fd_pr__pfet_01v8[gds]', 'destroy all']
    net += ['quit', '.endc', '.end']
    open('wi.cir', 'w').write('\n'.join(net) + '\n')
    r = subprocess.run([NG, '-b', 'wi.cir'], capture_output=True, text=True)
    vals = re.findall(r'^@\S+\s*=\s*([-+0-9.eE]+)\s*$', r.stdout, re.M)
    vals = [float(v) for v in vals]
    res = {}; k = 0
    for vg in vgs_list:
        for vd in vds_list:
            res[(vg, vd)] = tuple(abs(x) for x in vals[k:k+3]); k += 3
    return res
for L in (0.5, 1.0, 4.0):
    vgs_list = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
    vds_list = [round(UT*m, 5) for m in (2, 3, 4, 5, 6, 8)] + [0.9]
    res = run(L, vgs_list, vds_list)
    gmid_max = max(res[(vg, 0.9)][1]/res[(vg, 0.9)][0] for vg in vgs_list)
    w(f'## pfet L={L}u  max gm/ID(VDS=0.9) over VGS grid = {gmid_max:.2f} /V  (1/U_T = {1/UT:.2f})')
    w('VGS  gm/ID@0.9  VDS/U_T  ID/ID(0.9)  1-e^-x  gds*U_T/ID(op)  diffusion e^-x/(1-e^-x)  ratio op/diff')
    for vg in vgs_list:
        idref = res[(vg, 0.9)][0]
        for vd in vds_list[:-1]:
            idv, gm, gds = res[(vg, vd)]; x = vd/UT
            dif = math.exp(-x)/(1-math.exp(-x))
            w(f'{vg:.2f} {res[(vg,0.9)][1]/idref:7.2f} {x:5.1f} {idv/idref:8.4f} {1-math.exp(-x):8.4f} {gds*UT/idv:10.4f} {dif:10.4f} {gds*UT/idv/dif:8.2f}')
