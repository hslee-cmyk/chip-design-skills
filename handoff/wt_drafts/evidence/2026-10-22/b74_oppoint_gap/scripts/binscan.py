import subprocess, re
PDK = "C:/pdk/sky130_fd_pr"
Ws = [0.84, 0.99, 1.0, 1.001, 1.1, 1.26, 1.261, 2.99, 3.0, 3.001, 4.0, 4.99, 5.0, 5.001, 5.2, 5.5, 6.0, 6.99, 7.0, 7.001, 8.5, 20.0]
inc = [PDK + "/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice", PDK + "/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice",
       PDK + "/models/parameters/lod.spice", PDK + "/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice",
       PDK + "/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice"]
L = ["* bin edge scan"] + ['.include "%s"' % f for f in inc] + [".temp 27", "vgn gn 0 0.55", "vdn dn 0 0.9", "vgp gp 0 -0.70", "vdp dp 0 -0.9"]
pr = []
for i, w in enumerate(Ws):
    ad = w * 0.5; pd = w + 2
    L.append("xn%d dn gn 0 0 sky130_fd_pr__nfet_01v8 l=0.15u w=%gu ad=%gp as=%gp pd=%gu ps=%gu" % (i, w, ad, ad, pd, pd))
    L.append("xp%d dp gp 0 0 sky130_fd_pr__pfet_01v8 l=0.15u w=%gu ad=%gp as=%gp pd=%gu ps=%gu" % (i, w, ad, ad, pd, pd))
    pr += ["print @m.xn%d.msky130_fd_pr__nfet_01v8[id]" % i, "print @m.xp%d.msky130_fd_pr__pfet_01v8[id]" % i]
L += [".control", "option numdgt=8", "op"] + pr + ["quit", ".endc", ".end"]
open("run/binscan.cir", "w").write("\n".join(L) + "\n")
o = subprocess.run([r"C:\ngspice\Spice64\bin\ngspice_con.exe", "-b", "run/binscan.cir"], capture_output=True, text=True).stdout
open("run/binscan.log", "w").write(o)
v = {}
for ln in o.splitlines():
    m = re.match(r"@m\.x([np])(\d+)\.\S+\[id\]\s*=\s*(\S+)", ln.strip())
    if m:
        v[(m.group(1), int(m.group(2)))] = abs(float(m.group(3)))
k5 = Ws.index(5.0)
lines = ["W_um  nfet_ID/W(A/m) ratio_to_W5   pfet_ID/W(A/m) ratio_to_W5   (L=0.15um, nfet VGS=0.55 VDS=0.9, pfet VGS=-0.70 VDS=-0.9, VSB=0)"]
for i, w in enumerate(Ws):
    jn = v[("n", i)] / (w * 1e-6); jp = v[("p", i)] / (w * 1e-6)
    lines.append("%7.3f  %.5e %.3f   %.5e %.3f" % (w, jn, jn / (v[("n", k5)] / 5e-6), jp, jp / (v[("p", k5)] / 5e-6)))
print("\n".join(lines)); open("out/binscan.txt", "w").write("\n".join(lines) + "\n")
