"""C4. c1_sweep.txt 에서 (1) 실측 alpha 로 대신호 실효 게이트 용량 C_g,eff = C(1 - alpha)/alpha 역산,
(2) 상승 SR 대 alpha2(CBAT2 변형 c2) 선형 모형 SR = SR_inf * alpha 의 오차, (3) alpha_req = SR_spec/SR_inf -> C_min,
(4) 손계산 C_g: 단일 소자 sky130 .op cgg (포화 정지점 / 강반전 선형 V_GS 1.8 V·V_DS 0) 합.
결과: c4_fit.txt (덮어씀)."""
import pathlib, re, subprocess
import numpy as np
HERE = pathlib.Path(__file__).parent
OUT = HERE / "c4_fit.txt"
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] +
                [f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"'
                 for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])
SR_SPEC = 19.32
L = []


def log(s):
    L.append(s); print(s)


rows = {}
for r in (HERE / "c1_sweep.txt").read_text(encoding="utf-8").splitlines():
    if not r.startswith("| both") and not r.startswith("| c1") and not r.startswith("| c2"):
        continue
    f = [x.strip() for x in r.strip("|").split("|")]
    rows[(f[0], float(f[1]))] = dict(srf=float(f[4]), srr=float(f[5]), a1=float(f[8]), a2=float(f[11]), a1r=float(f[14]))

log("## (1) 실효 게이트 용량 역산 C_g,eff = C(1-alpha)/alpha  [pF]")
log("| C pF | n_m5g (CBAT1, 상승) | n_m8g (CBAT2, 상승) | n_m6g (CBAT1_R, 하강) |")
log("|---|---|---|---|")
for c in (0.1, 0.2, 0.3, 0.5, 1, 2, 5, 10):
    r1, r2 = rows[("c1", c)], rows[("c2", c)]
    g = lambda C, a: C * (1 - a) / a
    log(f"| {c} | {g(c, r1['a1']):.3f} | {g(c, r2['a2']):.3f} | {g(c, r1['a1r']):.3f} |")

log("\n## (2) 상승 SR 대 alpha2 (c2 변형: CBAT1 10 pF 고정) -- 모형 SR = SR_inf * alpha2, SR_inf = C 10 pF 값")
sr_inf = rows[("c2", 10)]["srr"]
log(f"SR_inf = {sr_inf} V/us (C 10 pF, alpha2 {rows[('c2', 10)]['a2']}) -- 대신호 양(oracle .tran), 손계산 아님")
log("| C pF | alpha2 | SR rise 실측 | SR_inf*alpha2/alpha2(10p) | 오차 % |")
log("|---|---|---|---|---|")
a10 = rows[("c2", 10)]["a2"]
for c in (0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.7, 1, 2, 5):
    r = rows[("c2", c)]
    m = sr_inf * r["a2"] / a10
    log(f"| {c} | {r['a2']:.3f} | {r['srr']:.2f} | {m:.2f} | {100*(m - r['srr'])/r['srr']:+.1f} |")
a_req = SR_SPEC / sr_inf * a10
cg2 = np.median([rows[("c2", c)] and c * (1 - rows[("c2", c)]["a2"]) / rows[("c2", c)]["a2"] for c in (0.3, 0.5, 0.7, 1, 2)])
log(f"\n## (3) alpha2_req = SR_spec/SR_inf (x alpha2(10p)) = {a_req:.3f}; C_g,eff(n_m8g) 중앙값 {cg2:.3f} pF -> C_min = a/(1-a)*C_g = {a_req/(1-a_req)*cg2:.3f} pF")
log("   sweep 실측 경계(c2): 0.7 pF FAIL(18.54) / 1 pF PASS(19.97); (both): 1 pF FAIL(18.89) / 2 pF PASS(19.34)")


def op_cgg(kind, w, l, vg, vd, vs, vb):
    model = f"sky130_fd_pr__{kind}_01v8"
    dev = f"@m.x1.msky130_fd_pr__{kind}_01v8[cgg]"
    deck = "\n".join(["* cgg", LIB, f"vd d 0 {vd}", f"vg g 0 {vg}", f"vs s 0 {vs}", f"vb b 0 {vb}",
                      f"x1 d g s b {model} w={w}u l={l}u", ".control", "op", f"print {dev}", ".endc", ".end"])
    p = HERE / "c4_cgg.cir"; p.write_text(deck, encoding="utf-8")
    o = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, cwd=HERE).stdout
    m = re.search(r"=\s*([-+0-9.eE]+)\s*$", o.strip().splitlines()[-1]) if o.strip() else None
    for line in o.splitlines():
        mm = re.match(r".*cgg\]\s*=\s*([-+0-9.eE]+)", line)
        if mm:
            return float(mm.group(1))
    return float("nan")


log("\n## (4) 손계산 C_g (단일 소자 .op cgg = LUT 열과 같은 양)")
# 강반전 선형(V_DS 0, |V_GS| 1.8): 채널 전체 W L Cox + overlap -- 대신호 상한 쪽
c5_lin = op_cgg("nfet", 60, 0.3, 1.8, 0, 0, 0)
c7_lin = op_cgg("pfet", 24, 0.3, 0, 1.8, 1.8, 1.8)
c21 = 8.832e-15  # M21 정지 cgg (flow_derivation s2_op_ac.txt)
c19 = 6.809e-15
log(f"- M5 (60/0.3) 강반전 선형 cgg = {c5_lin*1e15:.1f} fF; + M19 정지 {c19*1e15:.1f} fF -> n_m5g C_g 손 = {(c5_lin + c19)*1e12:.3f} pF (정지 소신호 cgg 62.1 fF + 6.8 fF = 0.069 pF)")
log(f"- M7·M8 (24/0.3 각) 강반전 선형 cgg = {c7_lin*1e15:.1f} fF 각; + M21 {c21*1e15:.1f} fF -> n_m8g C_g 손 = {(2*c7_lin + c21)*1e12:.3f} pF (정지 소신호 합 0.060 pF)")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
