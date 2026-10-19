"""OP-1 (iv): can an adapter set / read per-instance deterministic mismatch values inside the PDK subckt (binned model)?
T11a instance-line override of an undeclared subckt param; T11b wrapper-local .param (current oracle method); T11c read via showmod / @ vector."""
import json, re, sys
sys.path.insert(0, r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/scripts")
sys.argv = [sys.argv[0], "NONE"]
import m1_native_mc as M  # noqa: E402

V = "sky130_fd_pr__nfet_01v8__vth0_slope_spectre"
# a: instance-line override (XA gets +1, XB gets -1)
pa = ["Ia 0 ga DC 10u", "Ib 0 gb DC 10u",
      f"XA ga ga 0 0 sky130_fd_pr__nfet_01v8 w=5 l=1 {V}=1", f"XB gb gb 0 0 sky130_fd_pr__nfet_01v8 w=5 l=1 {V}=-1"]
a = M.run("T11a_inst", M.bench([], pa, "scale=1u"))
M.app({"test": "T11a_instance_line_override", "rc": a[0], "vth0_A": M.pick(a[3], "xa", "vth0"), "vth0_B": M.pick(a[3], "xb", "vth0"),
       "dVGS": a[2].get("v(ga)-v(gb)"),
       "msgs": [l for l in a[1].splitlines() if re.search("error|warn|unknown|ignored|param", l, re.I)][:8]})
# b: wrapper-local .param (oracle's current approach)
wr = [".subckt mmv d g s b params: v0=0", f".param {V}={{v0}}", "X1 d g s b sky130_fd_pr__nfet_01v8 w=5 l=1", ".ends"]
pb = ["Ia 0 ga DC 10u", "Ib 0 gb DC 10u", "XA ga ga 0 0 mmv v0=1", "XB gb gb 0 0 mmv v0=-1"]
ctrl = ["op", "print v(ga) v(gb) v(ga)-v(gb)",
        "showmod m.xa.x1.msky130_fd_pr__nfet_01v8 : vth0", "showmod m.xb.x1.msky130_fd_pr__nfet_01v8 : vth0",
        "print @m.xa.x1.msky130_fd_pr__nfet_01v8[vth] @m.xb.x1.msky130_fd_pr__nfet_01v8[vth]"]
b = M.run("T11b_wrap", M.bench([], wr + pb, "scale=1u", ctrl=ctrl))
M.app({"test": "T11b_wrapper_local_param", "rc": b[0], "vth0_lines": re.findall(r"vth0\s+(\S+)", b[1]),
       "model_hdr": re.findall(r"model\s+(\S+)", b[1]), "dVGS": b[2].get("v(ga)-v(gb)"),
       "vth_op": {k: v for k, v in b[2].items() if "[vth]" in k}})
# c: read paths in plain (non-wrapper) instance: showmod name, @-vector of a model param
ctrl_c = ["op", "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0 lmin lmax wmin wmax",
          "print @m.xa.msky130_fd_pr__nfet_01v8[vth] @m.xa.msky130_fd_pr__nfet_01v8[vth0]"]
c = M.run("T11c_read", M.bench(M.GL_ALL, M.PAIR, "scale=1u seed=2", ctrl=ctrl_c))
M.app({"test": "T11c_read_paths", "rc": c[0], "tail": [l for l in c[1].splitlines() if l.strip()][-14:]})
print("done")
