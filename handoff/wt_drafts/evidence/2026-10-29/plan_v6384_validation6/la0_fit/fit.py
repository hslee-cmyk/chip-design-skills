# 검증 6 O-171 MJ-3: .dc VDS 스윕을 I_inf*(1-exp(-V/UT))*(1+V/VE) 에 맞춤 -- UT 고정(kT/q) 대 UT 자유
import subprocess, os, math, re
import numpy as np
from scipy.optimize import least_squares
PDK = r"C:\pdk\sky130_fd_pr"; NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
inc = [f'.include "{os.path.join(PDK,"models","parameters","lod.spice")}"',
       rf'.include "{PDK}\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__tt.pm3.spice"',
       rf'.include "{PDK}\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"']
UT0 = 1.380649e-23*300.15/1.602176634e-19
out = open(os.path.join(HERE,'fit.txt'),'w',encoding='utf-8')
def w(s): print(s); out.write(s+'\n'); out.flush()
def sweep(L, vg):
    cir = os.path.join(HERE, 'sw.cir'); dat = os.path.join(HERE, 'sw.dat').replace(os.sep,'/')
    net = ['* sweep']+inc+[f'vg g 0 dc {-vg}','vd d 0 dc 0','vs s 0 dc 0','vb b 0 dc 0',
      f'xdut d g s b sky130_fd_pr__pfet_01v8 l={L}u w=5u ad=2.5p as=2.5p pd=7u ps=7u',
      '.control','dc vd 0 -0.9 -0.002',f'wrdata {dat} i(vd)','quit','.endc','.end']
    open(cir,'w').write('\n'.join(net)+'\n')
    subprocess.run([NG,'-b',cir],capture_output=True,text=True)
    a = np.loadtxt(dat); return -a[:,0], np.abs(a[:,1])
def gmid(L, vg):
    _, i1 = sweep(L, vg+0.001); _, i0 = sweep(L, vg-0.001)
    return (math.log(i1[-1])-math.log(i0[-1]))/0.002
w(f'UT0 = kT/q @27C = {UT0*1e3:.3f} mV')
w('L  VGS  gm/ID(0.9V)  | UT고정: VE[V] 최대상대잔차 (x<=8 구간 잔차)  | UT자유: UT_fit[mV] UT_fit/UT0 VE 최대상대잔차 | x*=VDS where ID/(Iinf(1+V/VE))>=1-eps (eps=gmid*1mV): 측정/UT고정식/UT자유식')
for L in (0.5, 1.0, 4.0):
    for vg in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2):
        v, i = sweep(L, vg); m = v > 0.004
        v, i = v[m], i[m]; g = gmid(L, vg)
        f1 = lambda p: (p[0]*(1-np.exp(-v/UT0))*(1+v/p[1]) - i)/i
        r1 = least_squares(f1, [i[-1], 5.0], bounds=([0,0.05],[np.inf,1e4]))
        f2 = lambda p: (p[0]*(1-np.exp(-v/p[2]))*(1+v/p[1]) - i)/i
        r2 = least_squares(f2, [i[-1], 5.0, UT0], bounds=([0,0.05,0.005],[np.inf,1e4,0.5]))
        eps = g*1e-3
        def xstar(Iinf, VE):
            frac = i/(Iinf*(1+v/VE)); ok = np.where(frac >= 1-eps)[0]
            return v[ok[0]] if len(ok) else float('nan')
        xs_meas1 = xstar(r1.x[0], r1.x[1]); xs_meas2 = xstar(r2.x[0], r2.x[1])
        xs_formula1 = UT0*math.log(1/eps); xs_formula2 = r2.x[2]*math.log(1/eps)
        sel = v <= 8*UT0
        w(f'{L:3.1f} {vg:.2f} {g:6.2f} | {r1.x[1]:7.2f} {np.max(np.abs(r1.fun)):7.3f} ({np.max(np.abs(r1.fun[sel])):6.3f}) | {r2.x[2]*1e3:6.2f} {r2.x[2]/UT0:5.2f} {r2.x[1]:7.2f} {np.max(np.abs(r2.fun)):6.3f} | eps={eps:.4f} 측정자료(고정맞춤 envelope) {xs_meas1*1e3:6.1f} mV, 식 UT0 ln(1/eps) {xs_formula1*1e3:6.1f} mV, 측정자료(자유맞춤) {xs_meas2*1e3:6.1f} mV, 식 UTfit ln(1/eps) {xs_formula2*1e3:6.1f} mV')
