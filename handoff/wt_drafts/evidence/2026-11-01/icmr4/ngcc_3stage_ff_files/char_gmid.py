"""sky130 nfet/pfet_01v8 단일 소자 gm/ID 특성(ngspice .dc) -- 손 사이징 시험점용 전류밀도 ID/W 조회.
L = 0.5 um(원문 'gate lengths of all MOSFETs were set to 0.5um, about 3 times the minimum feature size' p.24의 '최소 3배' 규칙을
sky130 최소 L 0.15 um 에 적용 = 0.45 um -> 제조 격자 위 0.5 um 로 둠 -- 시험점 선택이지 spec 값 아님), W = 1 um, |VDS| = 0.6 V.
결과: char_<kind>.txt (VGS, id, gm) + char_gmid.log append.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
INC = r"""
.include "C:\pdk\sky130_fd_pr\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__tt.pm3.spice"
.include "C:\pdk\sky130_fd_pr\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
.include "C:\pdk\sky130_fd_pr\models\parameters\lod.spice"
.include "C:\pdk\sky130_fd_pr\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__tt.pm3.spice"
.include "C:\pdk\sky130_fd_pr\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"
"""
L = 0.5e-6


def run(kind):
    if kind == "n":
        body = ("Vd d 0 DC 0.6\nVg g 0 DC 0.5\nXM d g 0 0 sky130_fd_pr__nfet_01v8 l=%g w=1e-6\n" % L)
        dev = "@m.xm.msky130_fd_pr__nfet_01v8"
    else:
        body = ("Vdd s 0 DC 1.8\nVd d 0 DC 1.2\nVg g 0 DC 1.3\nXM d g s s sky130_fd_pr__pfet_01v8 l=%g w=1e-6\n" % L)
        dev = "@m.xm.msky130_fd_pr__pfet_01v8"
    out = HERE / ("char_%s.txt" % kind)
    sweep = "dc vg 0 1.8 0.005"
    cir = ("* char %s\n" % kind) + INC + ".temp 27\n" + body + (
        ".control\nset wr_singlescale\nset wr_vecnames\noption numdgt=10\nsave %s[id] %s[gm] %s[vdsat] %s[vth]\n%s\n"
        "wrdata %s %s[id] %s[gm] %s[vdsat] %s[vth]\nquit\n.endc\n.end\n") % (dev, dev, dev, dev, sweep, out.as_posix(), dev, dev, dev, dev)
    p = HERE / ("char_%s.cir" % kind)
    p.write_text(cir, encoding="utf-8")
    r = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, cwd=str(HERE))
    with open(HERE / "char_gmid.log", "a", encoding="utf-8") as f:
        f.write("=== char %s rc=%d\n%s\n" % (kind, r.returncode, (r.stdout + r.stderr)[-1500:]))


if __name__ == "__main__":
    for k in sys.argv[1:] or ["n", "p"]:
        run(k)
