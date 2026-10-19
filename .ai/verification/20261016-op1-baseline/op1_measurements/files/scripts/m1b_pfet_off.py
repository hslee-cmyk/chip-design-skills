"""OP-1 (i) supplement: pfet pair independence (4 vars, L=0.5 bin with vth0_slope1) + 'switch off' bit identity (PC-3 (c))."""
import json, math, statistics as st, sys, re
sys.path.insert(0, r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/scripts")
sys.argv = [sys.argv[0], "NONE"]
import m1_native_mc as M  # noqa: E402

P_INC = ['.include "C:\\pdk\\sky130_fd_pr\\models\\parameters\\lod.spice"',
         '.include "C:\\pdk\\sky130_fd_pr\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__tt.pm3.spice"',
         '.include "C:\\pdk\\sky130_fd_pr\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"']
PV = ["toxe", "vth0", "voff", "nfactor"]
GLP = [f".param sky130_fd_pr__pfet_01v8__{v}_slope_spectre = agauss(0,1,1)" for v in PV]
PAIRP = ["Vdd vdd 0 1.8", "Ia ga 0 DC 10u", "Ib gb 0 DC 10u",
         "XA ga ga vdd vdd sky130_fd_pr__pfet_01v8 w=5 l=0.5", "XB gb gb vdd vdd sky130_fd_pr__pfet_01v8 w=5 l=0.5"]


def benchp(gl, opts):
    c = ["op", "print v(ga) v(gb) v(ga)-v(gb)",
         "showmod m.xa.msky130_fd_pr__pfet_01v8 : vth0 toxe voff nfactor", "showmod m.xb.msky130_fd_pr__pfet_01v8 : vth0 toxe voff nfactor"]
    return "\n".join(["* m1b pfet"] + P_INC + gl + [f".option {opts}"] + PAIRP + [".control"] + c + ["quit", ".endc", ".end"]) + "\n"


rn = M.run("P_nom", benchp([], "scale=1u"))
nom = {p: M.pick(rn[3], "xa", p) for p in PV}
rows = []
for s in range(1, 101):
    r = M.run("P_s", benchp(GLP, f"scale=1u seed={s}"))
    rows.append({p + x: M.pick(r[3], x, p) for p in PV for x in ("xa", "xb")} | {"dVGS": r[2].get("v(ga)-v(gb)"), "rc": r[0]})


def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


dA = [x["vth0xa"] - nom["vth0"] for x in rows]
dB = [x["vth0xb"] - nom["vth0"] for x in rows]
slope1 = None
for ln in open(r"C:/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice", encoding="utf-8"):
    m = re.match(r"\.param\s+sky130_fd_pr__pfet_01v8__vth0_slope1\s*=\s*(\S+)", ln)
    if m:
        slope1 = float(m.group(1))
M.app({"test": "T9_pfet_pair_L0p5_100seeds", "nominal": nom, "N": len(rows), "rc_set": sorted({x["rc"] for x in rows}),
       "sd_dvth0_A_mV": st.stdev(dA) * 1e3, "sd_dvth0_B_mV": st.stdev(dB) * 1e3,
       "pfet_vth0_slope1": slope1, "expected_if_slope1_mV": (slope1 / math.sqrt(2.5) * 1e3) if slope1 else None,
       "corr_A_B": corr(dA, dB), "corr_95pct_bound": 1.96 / math.sqrt(len(rows)), "sd_dVGS_mV": st.stdev([x["dVGS"] for x in rows]) * 1e3})

# PC-3 (c): switch = 0 vs no override, bit identity of node voltages
GLS = [".param mc_mm_switch = 0"] + [f".param sky130_fd_pr__nfet_01v8__{v}_slope_spectre = agauss(0,1,1)*mc_mm_switch" for v in M.NV]
a = M.run("OFF_none", M.bench([], M.PAIR, "scale=1u"))
b = M.run("OFF_sw0", M.bench(GLS, M.PAIR, "scale=1u seed=4"))
ra = re.findall(r"^v\(g[ab]\)\s*=\s*(\S+)", a[1], re.M)
rb = re.findall(r"^v\(g[ab]\)\s*=\s*(\S+)", b[1], re.M)
M.app({"test": "T10_switch_off_bit_identity", "no_override": ra, "switch0": rb, "printed_identical": ra == rb,
       "vth0_none": M.pick(a[3], "xa", "vth0"), "vth0_sw0": M.pick(b[3], "xa", "vth0")})
print("done")
