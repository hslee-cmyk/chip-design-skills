"""Generate + run single-device .op SPICE cross-checks for the key sized devices,
following the sky130-worked-example.md pattern (nfet needs __tt.pm3+mismatch.corner;
pfet needs those + lod.spice; PMOS biased with negative VGS/VDS)."""
import json, subprocess, re, os

PDK = "C:/pdk/sky130_fd_pr"
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "..", "vgs_table.json")) as f:
    data = json.load(f)

NFET_INC = f"""
.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice"
.include "{PDK}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
"""
PFET_INC = f"""
.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice"
.include "{PDK}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice"
.include "{PDK}/models/parameters/lod.spice"
"""

results = {}
for name, d in data["vgs"].items():
    kind = d["kind"]
    W = data["W"][name]
    L = d["L_um"]
    vgs = d["vgs"]
    vds = d["vds"]
    model = "sky130_fd_pr__nfet_01v8" if kind == "nmos" else "sky130_fd_pr__pfet_01v8"
    inc = NFET_INC if kind == "nmos" else PFET_INC
    sign = 1 if kind == "nmos" else -1
    # sky130 model binning tops out well under W~200um (sky130-worked-example.md sec12.3) -- for wide
    # devices, realize W as N REAL parallel unit-width (5um) X-instances sharing d/g/s/b (NOT the
    # subckt's `mult` parameter -- verified by direct test that `mult` is declared in the .subckt
    # .param line but never wired into the internal `m...` device line in this ngspice pm3.spice, so
    # it has ZERO effect on current; a controlled mult=1 vs mult=10 test at identical bias returned
    # IDENTICAL current, confirming this). Total ID is read from the drain supply's own current
    # (sums all parallel branches correctly regardless of the mult bug); total gm = N * per-finger gm.
    if W > 90.0:
        unit_w = 5.0
        N = max(1, round(W / unit_w))
        w_eff = unit_w
    else:
        N = 1
        w_eff = W
    insts = "\n".join(f"XM{i} d g s b {model} l={L:.6f}u w={w_eff:.6f}u" for i in range(N))
    netlist = f"""* single-device op check: {name} ({kind}), N={N} parallel unit fingers
{inc}
Vg g 0 {sign*vgs:.6f}
Vd d 0 {sign*vds:.6f}
Vsrc s 0 0
Vb b 0 0
{insts}
.op
.control
run
print @m.xm0.m{model}[id]
print @m.xm0.m{model}[gm]
print @m.xm0.m{model}[vdsat]
print @m.xm0.m{model}[vth]
print -i(vd)
.endc
.end
"""
    path = os.path.join(here, f"sd_{name}.cir")
    with open(path, "w") as f:
        f.write(netlist)
    out = subprocess.run(["ngspice_con.exe", "-b", path], capture_output=True, text=True,
                          env={**os.environ, "PATH": "/c/ngspice/Spice64/bin:" + os.environ.get("PATH","")})
    log = out.stdout + out.stderr
    def grab(tag):
        m = re.search(rf"{re.escape(tag)}\s*=\s*([\-0-9.eE+]+)", log)
        return float(m.group(1)) if m else None
    idv_total = grab("i(vd)")   # total current through the drain supply == sum of all N parallel fingers
    gmv_unit = grab(f"@m.xm0.m{model}[gm]")
    vdsatv = grab(f"@m.xm0.m{model}[vdsat]")
    vthv = grab(f"@m.xm0.m{model}[vth]")
    gmv = gmv_unit * N if gmv_unit is not None else None
    results[name] = dict(kind=kind, W_um=W, L_um=L, VGS=vgs, VDS=vds, N_parallel=N,
                          ID_target_uA=d["ID_target_uA"],
                          ID_sim_uA=abs(idv_total)*1e6 if idv_total is not None else None,
                          gm_sim_uS=abs(gmv)*1e6 if gmv is not None else None,
                          vdsat_sim=vdsatv, vth_sim=vthv, log_tail=log[-800:])
    print(name, results[name])

with open(os.path.join(here, "..", "spice_single_device_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("done")
