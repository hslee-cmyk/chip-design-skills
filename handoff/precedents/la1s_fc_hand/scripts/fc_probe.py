"""LUT 격자(L 축, 슬라이스 폭, 기준 폭)와 PDK 역할 양을 파일에 적는다."""
import sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/scripts")
import lutlib as lt
import pdklib

out = open(sys.argv[1], "w", encoding="utf-8")
for k in ("nmos", "pmos"):
    ws = lt.slice_widths(k)
    out.write("%s slices um: %s\n" % (k, [round(w * 1e6, 3) for w in ws]))
    s = lt._slice(k, ws[0])
    out.write("%s L um: %s\n" % (k, [round(x * 1e6, 3) for x in s["L"]]))
    out.write("%s VGS %s..%s n=%d, VDS %s..%s n=%d, VS %s..%s n=%d\n" % (k, s["VGS"][0], s["VGS"][-1], len(s["VGS"]), s["VDS"][0], s["VDS"][-1], len(s["VDS"]), s["VS"][0], s["VS"][-1], len(s["VS"])))
c = lt.cap_table()
out.write("cap w_ref_m %s, L %s\n" % (c["w_ref_m"], [round(x * 1e6, 3) for x in c["L"]]))
names = ["min_finger_w_m", "manufacturing_grid_m", "finger_pitch_overhead_m", "row_gap_m", "dummy_w_m",
         "tap_w_m", "well_spacing_m", "mim_cap_density_f_per_m2"]
q = pdklib.quantities(names)
for n in names:
    out.write("%s = %.6g\n" % (n, q[n]))
out.close()
