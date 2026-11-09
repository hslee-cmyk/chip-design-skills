# 균일 RC 선 2단자 Y 대 π(C/2) 근사 오차 -- 검증 5 M-3 (O-171)
import cmath, math, json, sys
out = open('rc_err.txt', 'w', encoding='utf-8')
def w(*a):
    s = ' '.join(str(x) for x in a); print(s); out.write(s + '\n')
# 계수: PDK 셀 res_high_po_0p35 (rsheet 1112.41 Ω/µm 폭 0.35 µm 기준 길이당 R), crpf 1.06e-4 F/m², crpfsw 5.04e-11 F/m (res_typical__cap_typical.spice:40-41)
rsh_per_um = 1112.41; wum = 0.35; crpf = 1.06e-4; crpfsw = 5.04e-11; head = 2.08
def cpar(R):
    L = R / rsh_per_um   # µm, rcon 무시(근사)
    return (L + 2*head) * wum * crpf * 1e-12 + 2 * (L + 2*head + wum) * crpfsw * 1e-6
# Taylor 검증: θcothθ, θ/sinhθ 계수
w('Taylor 확인: x=1e-3 θ² -> (θcothθ-1)/θ² =', ((cmath.sqrt(1e-3)/cmath.tanh(cmath.sqrt(1e-3)))-1)/1e-3, ' (1/3 기대);', (1-cmath.sqrt(1e-3)/cmath.sinh(cmath.sqrt(1e-3)))/1e-3, '(1/6 기대)')
w('R[Ω]  C_par[fF]  f[Hz]  ωRC  |다리항 ωRC/6|  |Y11 오차|/(1/R)  |Y12 오차|/(1/R)')
for f, tag in ((0.816e6, 'nmcnr GBW spec'), (3.41e6, 'cr UGF_cm'), (28.5e6, 'cr UGF_dm')):
    for R in (1e3, 1e4, 1e5, 5e5, 1e6, 1e7):
        C = cpar(R); s = 1j * 2 * math.pi * f; th = cmath.sqrt(s * R * C)
        y11 = (th / cmath.tanh(th)) / R; y12 = -(th / cmath.sinh(th)) / R
        p11 = 1 / R + s * C / 2; p12 = -1 / R   # π(C/2): 다리 = 순수 R
        w(f'{R:.0e} {C*1e15:8.3f} {f:.3g} {abs(s*R*C):.3g} {abs(s*R*C)/6:.3g} {abs(y11-p11)*R:.3g} {abs(y12-p12)*R:.3g}  [{tag}]')
