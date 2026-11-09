"""q2_cbox m4: 결합 C 하한 결정자 alpha = C/(C+C_g,eff) 를 held-out 없이 합성 toy 로 보이기 (sky130 tt, ngspice).
toy(구성 입력, spec 근거 아님): 구동 마디 X 에 계단 dVx(이상 전압원, 상승 1 ns) -> 결합 C -> 게이트 G.
G 는 R_b(이상 큰 R) 로 VB 에 DC 고정. NMOS(W/L 구성값) 드레인 = 고정 VD(전류 측정), 소스 = 0.
측정: alpha = dVg_peak/dVx, dId_peak(출력 전류 능력 = SR*CL 대리), C_g,eff = C(1-alpha)/alpha,
      정지 cgg(.op) 와 비교, 손계산 C_min = a_req/(1-a_req) * C_g,eff 대 실측 경계.
출력: m4_coupling_toy.txt (+ deck/log 는 m4_runs/)
"""
import math, pathlib, re, subprocess

NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
HERE = pathlib.Path(__file__).parent
RUNS = HERE / "m4_runs"
RUNS.mkdir(exist_ok=True)
OUT = pathlib.Path(__file__).with_suffix(".txt")
OUT.write_text("", encoding="utf-8")
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"',
                 '.include "C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice"',
                 '.include "C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"'])
W, L, VB, VD, DVX = "20u", "0.3u", 0.55, 0.9, 0.6   # 구성 입력


def emit(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def deck(c):
    return f"""* coupling toy
{LIB}
.option gmin=1e-15 reltol=1e-5 abstol=1e-15 vntol=1e-8 method=gear
vx x 0 pwl(0 0 10n 0 11n {DVX})
cc x g {c}
rb g vb 1e12
vvb vb 0 {VB}
vvd d 0 {VD}
xm1 d g 0 0 sky130_fd_pr__nfet_01v8 w={W} l={L}
.control
op
let cgg0 = @m.xm1.msky130_fd_pr__nfet_01v8[cgg]
let id0 = -i(vvd)
print cgg0 id0
tran 0.05n 40n
meas tran vgpk max v(g) from=10n to=40n
let idd = -i(vvd)
meas tran idpk max idd from=10n to=40n
meas tran vg0 find v(g) at=9n
meas tran id0t find idd at=9n
.endc
.end
"""


def run(c):
    p = RUNS / f"c_{c:.2e}.cir"
    p.write_text(deck(c), encoding="utf-8")
    r = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, timeout=300)
    log = r.stdout + r.stderr
    (RUNS / f"c_{c:.2e}.log").write_text(log, encoding="utf-8")
    g = lambda k: float(re.search(r"^\s*%s\s*=\s*([-+0-9.eE]+)" % k, log, re.M).group(1))
    return dict(cgg0=g("cgg0"), vgpk=g("vgpk"), idpk=g("idpk"), vg0=g("vg0"), id0=g("id0t"))


Cs = [1e-14, 2e-14, 5e-14, 1e-13, 2e-13, 5e-13, 1e-12, 2e-12, 5e-12, 1e-11, 1e-10]
emit(f"구성: W={W} L={L} VB={VB} VD={VD} dVx={DVX} V (상승 1 ns), R_b=1e12")
rows = []
for c in Cs:
    m = run(c)
    a = (m["vgpk"] - m["vg0"]) / DVX
    cg = c * (1 - a) / a if a > 0 else float("nan")
    rows.append((c, a, m["idpk"] - m["id0"], cg, m["cgg0"], m["id0"]))
    emit(f"C={c:.2e}: alpha={a:.4f} dId_pk={rows[-1][2]*1e6:.2f} uA  C_g,eff(역산)={cg*1e15:.2f} fF  정지 cgg={m['cgg0']*1e15:.2f} fF  Id0={m['id0']*1e6:.2f} uA")
didmax = rows[-1][2]
emit("")
emit("== toy 요구 전류(구성 입력: dId_req = k x dId(C=100pF), k 별) 에 대한 C 하한: 실측 경계 대 손계산 ==")
for k in (0.5, 0.8, 0.9):
    req = k * didmax
    ok = [r for r in rows if r[2] >= req]
    bad = [r for r in rows if r[2] < req]
    lo = max((r[0] for r in bad), default=None)
    hi = min((r[0] for r in ok), default=None)
    # alpha_req: dId(alpha) 를 실측 점 사이 선형 보간
    pts = sorted((r[1], r[2]) for r in rows)
    a_req = None
    for (a1, d1), (a2, d2) in zip(pts, pts[1:]):
        if d1 < req <= d2:
            a_req = a1 + (a2 - a1) * (req - d1) / (d2 - d1)
    cg_static = rows[-1][4]
    cg_eff = [r[3] for r in rows if hi and r[0] == hi][0] if hi else float("nan")
    cs = a_req / (1 - a_req) * cg_static if a_req else float("nan")
    ce = a_req / (1 - a_req) * cg_eff if a_req else float("nan")
    emit(f"k={k}: dId_req={req*1e6:.1f} uA  실측 경계 C in ({lo}, {hi}]  alpha_req={a_req:.3f}  "
         f"손계산 C_min(정지 cgg {cg_static*1e15:.1f} fF)={cs*1e15:.1f} fF  C_min(경계점 C_g,eff {cg_eff*1e15:.1f} fF)={ce*1e15:.1f} fF")
