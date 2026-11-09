"""S4. 행동 모형으로 doublet 정착 꼬리 식 검증 (Kamath-Meyer-Gray 1974 꼴).
OTA = Gm 적분기(CL) + 고역 통과 boost 경로 k*Gm*HP(s), HP(s) = s tau/(1 + s tau), tau = 1/(2 pi f_HP).
개루프 A(s) = (Gm/(s CL)) (1 + s tau (1+k)) / (1 + s tau)  -> 영점 w_z = 1/(tau(1+k)), 극 w_p = 1/tau (영점이 극 아래 = 고역 이득 증가).
폐루프(beta) 계단 오차 e(t) = 빠른 항 + 느린 항 A_s e^{-t/tau_s},
  식: A_s ~= (w_p - w_z)/(beta w_u) = k f_HP / ((1+k) beta f_u),  tau_s ~= 1/w_z = (1+k)/(2 pi f_HP)   (f_HP << beta f_u)
  여기서 f_u = Gm (1+k) / (2 pi CL) (doublet 위 단위이득 주파수, beta = 1).
ngspice 행동 모형 과도 해석 결과를 식과 정확해(2차 다항식 근·유수)와 대조. 결과: s4_doublet_model.txt"""
import math, pathlib, subprocess
import numpy as np

HERE = pathlib.Path(__file__).parent
OUT = HERE / "s4_doublet_model.txt"
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
CL = 70e-12
FU = 470e3            # S2 실측 f_u(coupled) 근방
K = 0.074             # S2 실측: f_u(coupled)/f_u(const) - 1
BETA = 0.5
GM = 2 * math.pi * FU * CL / (1 + K)


def exact(fhp):
    wp = 2 * math.pi * fhp; wz = wp / (1 + K); wu = BETA * GM * (1 + K) / CL
    # e(s) = (s + wp) / (s^2 + s(wp + wu) + wu wz)   (식 유도: 본문 2절)
    r = np.roots([1, wp + wu, wu * wz])
    s_slow = max(r, key=lambda x: x.real); s_fast = min(r, key=lambda x: x.real)
    A = (s_slow + wp) / (s_slow - s_fast)
    return A.real, -1 / s_slow.real


lines = [f"# S4 doublet model: CL {CL}, f_u {FU}, k {K}, beta {BETA}, Gm {GM:.4e}",
         "| f_HP Hz | 식 A_s = k f_HP/((1+k) beta f_u) | 정확 A_s | ngspice A_s (적합) | 식 tau_s = (1+k)/(2 pi f_HP) s | 정확 tau_s | ngspice tau_s | 1% 정착 ns (ngspice) |",
         "|---|---|---|---|---|---|---|---|"]
for fhp in (1e1, 1e2, 1e3, 1e4, 3e4, 1e5):
    tau = 1 / (2 * math.pi * fhp)
    tstop = min(8 * tau * (1 + K), 2e-2)
    deck = f"""* doublet model
vin in 0 pulse(0 1m 1n 1n 1n 1 2)
ein vn 0 value={{{BETA}*v(out) + (1-{BETA})*v(in)*0 + 0}}
* err = beta*(vin_target) : 반전 대신 비반전 등가(beta 폐루프) -- 이상 목표 out_final = vin/beta
eerr err 0 value={{v(in) - {BETA}*v(out)}}
gmain 0 out err 0 {GM}
* 고역 통과: 노드 hp = err 의 HP(s)
chp err hp {tau / 1e6}
rhp hp 0 1e6
gbst 0 out hp 0 {GM * K}
cl out 0 {CL}
.control
tran {min(tau/200, 1e-8)} {tstop} 0 {min(tau/200, 2e-8)}
wrdata {str(HERE / 's4_tmp.dat').replace(chr(92), '/')} v(out)
.endc
.end
"""
    p = HERE / "s4_tmp.cir"
    p.write_text(deck, encoding="utf-8")
    subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, cwd=HERE)
    d = np.loadtxt(HERE / "s4_tmp.dat")
    t, o = d[:, 0], d[:, 1]
    vfin = 1e-3 / BETA
    e = (vfin - o) / vfin
    # 느린 항 적합: t in [20/(beta w_u), tstop/2] 에서 log e 직선
    wu = BETA * GM * (1 + K) / CL
    m = (t > 30 / wu) & (t < tstop * 0.6) & (e > 0)
    if m.sum() > 10:
        sl, ic = np.polyfit(t[m], np.log(e[m]), 1)
        As_ng, tau_ng = math.exp(ic), -1 / sl
    else:
        As_ng, tau_ng = float("nan"), float("nan")   # 느린 항이 빠른 항과 분리되지 않음(f_HP ~ beta f_u)
    bad = np.where(np.abs(e) > 0.01)[0]
    ts = t[bad[-1]] - 1e-9 if len(bad) else 0
    Ae, te = exact(fhp)
    lines.append(f"| {fhp:.0e} | {K*fhp/((1+K)*BETA*FU):.3e} | {Ae:.3e} | {As_ng:.3e} | {(1+K)*tau:.3e} | {te:.3e} | {tau_ng:.3e} | {ts*1e9:.0f} |")
    print(lines[-1], flush=True)
lines.append("\n정착 판정식: 느린 항이 1 % 오차 띠 안에 처음부터 있으면(A_s <= eps) 정착 시간은 빠른 항이 정한다 ->"
             " f_HP <= eps (1+k) beta f_u / k 이면 doublet 무해. 아니면 t_s >= tau_s ln(A_s/eps).")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
