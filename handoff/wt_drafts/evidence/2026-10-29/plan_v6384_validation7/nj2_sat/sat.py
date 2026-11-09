# 검증 7 NJ-2: LA-0 (5) 새 판정(같은 점 SPICE ID 대 엔진 가정 ID <= eps)이 포화를 가르는가, 물리 판정은 무엇이어야 하는가
# DUT 줄 = LUT 생성기 sky130_lut_sweep.py:90 와 같음 (W 5u). 크기 규약(|V|).
# (가) 계획 문언: |ID_SPICE(VDS_op) - ID_LUT(VDS_op)|/ID_LUT <= eps
#      (엔진은 LUT 를 실제 VDS_op 에서 조회 -- block_widths.py:44-47, block_columns.py:150-154)
# (A) 접선 결손: delta_A(V) = 1 - ID(V)/[ID(Vr)+gds(Vr)(V-Vr)], Vr = 1.8 V (LUT VDS 축 끝)
# (B) EKV 역방향 분율: delta_B(V) = ID(VGS-V, VSB+V; VDS=Vr)/ID(VGS, VSB; VDS=Vr)
#     (ID = IF - IR, IR = 소스를 드레인 전위로 옮긴 순방향 전류 -- 소스/드레인 대칭)
import os, subprocess, math
import numpy as np
PDK = r"C:\pdk\sky130_fd_pr"; NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
LUT = np.load('C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz', allow_pickle=True)
out = open(os.path.join(HERE, 'sat.txt'), 'w', encoding='utf-8')
def w(s): print(s); out.write(s + '\n'); out.flush()
TOLV = 1e-3; VR = 1.8
UT0 = 1.380649e-23 * 300.15 / 1.602176634e-19


def inc(cell):
    return [f'.include "{PDK}\\models\\parameters\\lod.spice"',
            f'.include "{PDK}\\cells\\{cell}\\sky130_fd_pr__{cell}__tt.pm3.spice"',
            f'.include "{PDK}\\cells\\{cell}\\sky130_fd_pr__{cell}__mismatch.corner.spice"']


def run(cell, L, srcs, ana, dat):
    cir = os.path.join(HERE, 'x.cir'); d = os.path.join(HERE, dat).replace(os.sep, '/')
    inst = f'@m.xdut.msky130_fd_pr__{cell}'
    net = ['* s'] + inc(cell) + srcs + [
        f'xdut d g s b sky130_fd_pr__{cell} l={L}u w=5u ad=2.5p as=2.5p pd=7u ps=7u',
        f'.save {inst}[vdsat] {inst}[id]', '.control', ana, f'wrdata {d} {inst}[id] {inst}[vdsat]', 'quit', '.endc', '.end']
    open(cir, 'w').write('\n'.join(net) + '\n')
    subprocess.run([NG, '-b', cir], capture_output=True, text=True)
    a = np.atleast_2d(np.loadtxt(d))
    return a[:, 0], np.abs(a[:, 1]), np.abs(a[:, 3])


def sg(cell):
    return -1 if cell.startswith('p') else 1


def vd_sweep(cell, L, vg):
    s = sg(cell)
    return run(cell, L, [f'vg g 0 dc {s*vg}', 'vd d 0 dc 0', 'vs s 0 dc 0', 'vb b 0 dc 0'], f'dc vd 0 {s*VR} {s*0.001}', 'vd.dat')


def rev_sweep(cell, L, vg):
    # 소스 0, 벌크 = -s*V(역 body), 게이트 = s*vg - s*V... : vx = -s*V 를 x 에 두고 g = x + s*vg, b = x
    s = sg(cell)
    return run(cell, L, ['vx x 0 dc 0', f'vg g x dc {s*vg}', f'vd d 0 dc {s*VR}', 'vs s 0 dc 0', 'vb b x dc 0'],
               f'dc vx 0 {-s*VR} {-s*0.001}', 'rv.dat')


def id_at(cell, L, vg):
    s = sg(cell)
    return run(cell, L, [f'vg g 0 dc {s*vg}', f'vd d 0 dc {s*VR}', 'vs s 0 dc 0', 'vb b 0 dc 0'], 'op', 'g.dat')


def lut_pt(cell, L, vg, j):
    k = 'ID_p' if cell.startswith('p') else 'ID_n'
    iL = int(np.argmin(np.abs(LUT['L'] - L * 1e-6))); iG = int(np.argmin(np.abs(LUT['VGS'] - vg)))
    return (float(LUT[k][iL, iG, j, 0]), float(LUT['VDS'][j]), float(LUT[k.replace('ID', 'VDSAT')][iL, iG, j, 0]),
            float(LUT['L'][iL]), float(LUT['VGS'][iG]))


w(f'tol_V = {TOLV*1e3} mV (예시), Vr = {VR} V, VSB = 0, 크기 규약, U_T0 = {UT0*1e3:.3f} mV')
w('cell L |VGS| gm/ID eps | (가) LUT 격자 VDS 37.5·75 mV(깊은 선형)에서 |ID_SPICE-ID_LUT|/ID_LUT -> 판정 (LUT VDsat) |'
  ' VDS*(A 접선 결손=eps) VDS*(B 역방향 분율=eps) | @m VDsat(VDS=Vr) | U_T ln(1/eps)')
for cell in ('pfet_01v8', 'nfet_01v8'):
    for L in (0.5, 1.0, 4.0):
        for vgr in (0.4875, 0.6, 0.7125, 0.9, 1.2):
            v, i, vdsat_sw = vd_sweep(cell, L, vgr); v = np.abs(v)
            ip = id_at(cell, L, vgr + 0.002)[1][-1]; im = id_at(cell, L, vgr - 0.002)[1][-1]
            g = (math.log(ip) - math.log(im)) / 0.004; eps = g * TOLV
            res = []
            for j in (1, 2):
                il, vdg, vdsat_l, Lg, vgg = lut_pt(cell, L, vgr, j)
                isp = float(np.interp(vdg, v, i))
                d = abs(isp - il) / il
                res.append(f'{vdg*1e3:.1f}mV {d:.1e} {"성립" if d <= eps else "불일치"} (VDsat {vdsat_l*1e3:.0f}mV)')
            gds_r = (i[-1] - i[-3]) / (v[-1] - v[-3])
            dA = 1 - i / (i[-1] + gds_r * (v - v[-1]))
            okA = np.where((dA <= eps) & (v > 0.002))[0]; vA = v[okA[0]] if len(okA) else float('nan')
            vx, ir, _ = rev_sweep(cell, L, vgr); vx = np.abs(vx)
            dB = ir / ir[0]
            okB = np.where(dB <= eps)[0]; vB = vx[okB[0]] if len(okB) else float('nan')
            w(f'{cell[:4]} {L:3.1f} {vgr:.4f} {g:5.1f} {eps:.4f} | {" ; ".join(res)} | A {vA*1e3:6.1f} mV  B {vB*1e3:6.1f} mV'
              f' | VDsat {vdsat_sw[-1]*1e3:6.1f} mV | {UT0*math.log(1/eps)*1e3:5.1f} mV')
