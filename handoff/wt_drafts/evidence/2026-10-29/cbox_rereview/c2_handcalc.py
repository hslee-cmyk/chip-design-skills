"""C2. 결합비 하한 alpha_req 손계산 (단일 소자 sky130 DC = LUT 조회와 같은 양만 사용, 회로 전체 SPICE 아님).

상승 edge(out 상승) 전류 사슬: X -> M3B(게이트) / M5(게이트 n_m5g, CBAT1_L 결합) -> n_m7d -> M7(게이트 n_m8g, CBAT2 결합)
-> M9(diode, 게이트 n_m7d) -> 미러 M10 -> M8(게이트 n_m8g) -> out.  필요 전류 I_req = CL * SR_spec (spec 선언 두 값).
(1) CBAT1: M5 가 I_req 를 흘리려면 V_g5 >= V_s5 + V_GS5(I_req, V_SB = V_s5).  V_g5 = VCN + alpha1 * dV_X.
    V_s5 = M3B 드레인 = I_req * R_on(M3B @ V_GS = V_X,pk) (M3B 는 큰 V_X 에서 선형 -- 포화 조건 아님, 실측 n_m5s ~ 0.03 V)
    => alpha1_req = (V_s5 + V_GS5 - VCN) / dV_X.
(2) CBAT2: M9 diode 가 I_req 를 흘리면 n_m7d = VDD - V_SG9(I_req); M7 이 I_req 를 흘리려면 V_g7 <= n_m9d - V_SG7(I_req, V_BS),
    n_m9d <= VDD - V_SD9 (M9 선형 허용 시 VDD 쪽 상한), V_g7 = VCP - alpha2 * |dn7d|, |dn7d| = n7d_q - (VDD - V_SG9(I_req))
    => alpha2_req = (VCP - (n_m9d - V_SG7)) / |dn7d|  (분자 <= 0 이면 결합 없이도 성립 = 0).
dV_X(대신호 X 최대 스윙)는 선언 양이 아니다 -- 아래에서는 실측 큰 C 값(c1_sweep, C 10 pF)을 입력으로 쓰고 그 사실을 표시한다.
결과: c2_handcalc.txt (덮어씀)."""
import pathlib, re, subprocess
HERE = pathlib.Path(__file__).parent
OUT = HERE / "c2_handcalc.txt"
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] +
                [f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"'
                 for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])
VDD, VCP, VCN = 1.8, 0.7, 0.7
SR_SPEC, CL = 19.32e6, 70e-12
I_REQ = SR_SPEC * CL
Q = dict(x=0.497641, n7d=1.008564)            # flow_derivation s2_op_ac.txt 정지점
lines = []


def ng(deck, tag):
    p = HERE / f"c2_{tag}.cir"
    p.write_text(deck, encoding="utf-8")
    o = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, cwd=HERE).stdout
    (HERE / f"c2_{tag}.log").write_text(o, encoding="utf-8")
    return o


def solve_vgs(kind, w, l, vs, vd, vb, ireq, tag):
    """소자 하나: V_G 를 sweep 해 |I_D| = ireq 인 V_GS(NMOS) / V_SG(PMOS) -- LUT 역조회와 같은 양."""
    model = f"sky130_fd_pr__{kind}_01v8"
    deck = "\n".join(["* single", LIB, f"vd d 0 {vd}", f"vs s 0 {vs}", f"vb b 0 {vb}", "vg g 0 0",
                      f"x1 d g s b {model} w={w}u l={l}u", ".control", "dc vg 0 1.8 0.0005",
                      "wrdata " + str(HERE / f"c2_{tag}.dat").replace("\\", "/") + " i(vd)", ".endc", ".end"])
    ng(deck, tag)
    import numpy as np
    d = np.loadtxt(HERE / f"c2_{tag}.dat"); (HERE / f"c2_{tag}.dat").unlink()
    vg, i = d[:, 0], np.abs(d[:, 1])
    if kind == "nfet":
        k = np.argmax(i >= ireq); return vg[k] - vs
    k = np.where(i >= ireq)[0]; k = k[-1]; return vs - vg[k]


def solve_vds_triode(w, l, vgs, ireq, tag):
    import numpy as np
    model = "sky130_fd_pr__nfet_01v8"
    deck = "\n".join(["* triode", LIB, "vd d 0 0", "vs s 0 0", "vb b 0 0", f"vg g 0 {vgs}",
                      f"x1 d g s b {model} w={w}u l={l}u", ".control", "dc vd 0 0.6 0.0005",
                      "wrdata " + str(HERE / f"c2_{tag}.dat").replace("\\", "/") + " i(vd)", ".endc", ".end"])
    ng(deck, tag)
    d = np.loadtxt(HERE / f"c2_{tag}.dat"); (HERE / f"c2_{tag}.dat").unlink()
    vd, i = d[:, 0], np.abs(d[:, 1])
    return vd[np.argmax(i >= ireq)]


def log(s):
    lines.append(s); print(s)


log(f"# C2 alpha_req 손계산 (sky130 tt 단일 소자 DC, I_req = CL*SR_spec = {I_REQ*1e3:.4f} mA)")
for dvx_tag, dvx in (("c1 sweep C=10 pF 실측 dX(입력 -- 선언 양 아님)", None),):
    pass
# dV_X, dn7d 실측 입력은 c1_sweep.txt 의 C 10 pF 행에서 읽는다
txt = (HERE / "c1_sweep.txt").read_text(encoding="utf-8")
row = [r for r in txt.splitlines() if r.startswith("| both | 10 |")][0].split("|")
dX = float(row[7]); dn7d = float(row[10])
log(f"- 입력(대신호 실측, C 10 pF both): dV_X = {dX:.3f} V, dn7d = {dn7d:.3f} V")
vx_pk = Q["x"] + dX
vs5 = solve_vds_triode(90, 0.3, vx_pk, I_REQ, "m3b_tri")
vgs5 = solve_vgs("nfet", 60, 0.3, vs5, 1.0, 0.0, I_REQ, "m5")
a1 = (vs5 + vgs5 - VCN) / dX
log(f"- (1) V_s5 = V_DS(M3B 90/0.3 @ V_GS {vx_pk:.3f}, I_req) = {vs5:.4f} V; V_GS5(60/0.3, V_SB {vs5:.3f}) = {vgs5:.4f} V")
log(f"      alpha1_req = ({vs5:.4f} + {vgs5:.4f} - {VCN}) / {dX:.3f} = **{a1:.3f}**")
vsg9 = solve_vgs("pfet", 48, 0.3, VDD, VDD - 1.0, VDD, I_REQ, "m9")  # diode 근사: V_SD 1 V 에서 V_SG
n7d_req = VDD - vsg9
dn7d_hc = Q["n7d"] - n7d_req
vsg7 = solve_vgs("pfet", 24, 0.3, VDD - 0.05, 0.3, VDD, I_REQ, "m7")  # 소스 n_m9d ~ VDD-0.05 (M9 선형 쪽)
n9d = VDD - 0.05
a2 = max(0.0, (VCP - (n9d - vsg7)) / dn7d_hc)
log(f"- (2) V_SG9(48/0.3, I_req) = {vsg9:.4f} V -> n_m7d = {n7d_req:.4f} V, |dn7d| 손계산 = {dn7d_hc:.4f} V (실측 {abs(dn7d):.3f})")
log(f"      V_SG7(24/0.3, 소스 {n9d:.2f} V) = {vsg7:.4f} V; 필요 V_g7 <= {n9d - vsg7:.4f} V; alpha2_req = ({VCP} - {n9d - vsg7:.4f}) / {dn7d_hc:.4f} = **{a2:.3f}**")
log("- 결합비 -> C 하한: C_min = alpha_req/(1 - alpha_req) * C_g,eff.  C_g,eff 는 c1_sweep 실측 alpha 에서 역산(C_g,eff = C(1-alpha)/alpha).")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
