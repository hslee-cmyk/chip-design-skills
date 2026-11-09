"""q2_cbox m5: m4 toy 의 결합 C 하한을 정지 곡선(LUT 꼴: Id(VGS), cgg(VGS) DC sweep)만으로 손계산 -> m4 실측 경계와 대조.
손계산(θ 고정, 대신호 끝점 DC 양만 사용):
  VGS_req = Id^{-1}(Id0 + dId_req)           (정지 Id 곡선 역함수)
  alpha_req = (VGS_req - VB)/dVx
  C_g,bar = (1/(VGS_req-VB)) * integral_{VB}^{VGS_req} cgg dV  (전하 평균 = 큰 신호 게이트 용량)
  C_min = alpha_req/(1-alpha_req) * C_g,bar
출력: m5_coupling_handcalc.txt
"""
import pathlib, re, subprocess

NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
HERE = pathlib.Path(__file__).parent
RUNS = HERE / "m4_runs"
OUT = pathlib.Path(__file__).with_suffix(".txt")
OUT.write_text("", encoding="utf-8")
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"',
                 '.include "C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice"',
                 '.include "C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"'])
W, L, VB, VD, DVX = "20u", "0.3u", 0.55, 0.9, 0.6   # m4 와 같은 구성


def emit(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


vg_pts = [round(VB + i * 0.005, 4) for i in range(int(DVX / 0.005) + 1)]
lines = []
for v in vg_pts:
    lines.append(f"alter vvb dc = {v}\nop\nprint {v} @m.xm1.msky130_fd_pr__nfet_01v8[cgg] i(vvd)")
deck = f"""* static curves
{LIB}
.option gmin=1e-15 reltol=1e-5 abstol=1e-15
vvb g 0 {VB}
vvd d 0 {VD}
xm1 d g 0 0 sky130_fd_pr__nfet_01v8 w={W} l={L}
.control
""" + "\n".join(f"alter vvb dc = {v}\nop\necho PT {v} $&@m.xm1.msky130_fd_pr__nfet_01v8[cgg] $&i(vvd)" for v in vg_pts) + "\n.endc\n.end\n"
p = RUNS / "m5_static.cir"
p.write_text(deck, encoding="utf-8")
log = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, timeout=600).stdout
(RUNS / "m5_static.log").write_text(log, encoding="utf-8")
curve = [(float(a), float(b), -float(c)) for a, b, c in re.findall(r"^PT\s+(\S+)\s+(\S+)\s+(\S+)", log, re.M)]
assert len(curve) == len(vg_pts), len(curve)
id0 = curve[0][2]
emit(f"정지 곡선 {len(curve)}점, VB={VB}: Id0={id0*1e6:.2f} uA, cgg(VB)={curve[0][1]*1e15:.2f} fF, cgg(VB+dVx)={curve[-1][1]*1e15:.2f} fF")

# m4 실측 행 다시 읽기
m4 = (HERE / "m4_coupling_toy.txt").read_text(encoding="utf-8")
rows = [(float(c), float(a), float(d) * 1e-6) for c, a, d in re.findall(r"C=(\S+): alpha=(\S+) dId_pk=(\S+) uA", m4)]
didmax = rows[-1][2]
for k in (0.5, 0.8, 0.9):
    req = k * didmax
    tgt = id0 + req
    vreq = None
    for (v1, _, i1), (v2, _, i2) in zip(curve, curve[1:]):
        if i1 < tgt <= i2:
            vreq = v1 + (v2 - v1) * (tgt - i1) / (i2 - i1)
    if vreq is None:
        emit(f"k={k}: 정지 곡선 범위 밖")
        continue
    a_req = (vreq - VB) / DVX
    integ = 0.0
    for (v1, c1, _), (v2, c2, _) in zip(curve, curve[1:]):
        if v2 <= vreq:
            integ += 0.5 * (c1 + c2) * (v2 - v1)
        elif v1 < vreq:
            cm = c1 + (c2 - c1) * (vreq - v1) / (v2 - v1)
            integ += 0.5 * (c1 + cm) * (vreq - v1)
    cbar = integ / (vreq - VB)
    cmin = a_req / (1 - a_req) * cbar
    bad = [r[0] for r in rows if r[2] < req]
    ok = [r[0] for r in rows if r[2] >= req]
    emit(f"k={k}: dId_req={req*1e6:.1f} uA -> VGS_req={vreq:.4f} V alpha_req={a_req:.3f} C_g,bar={cbar*1e15:.2f} fF "
         f"-> 손계산 C_min={cmin*1e15:.1f} fF ; m4 실측 경계 ({max(bad):.2g}, {min(ok):.2g}] F")
