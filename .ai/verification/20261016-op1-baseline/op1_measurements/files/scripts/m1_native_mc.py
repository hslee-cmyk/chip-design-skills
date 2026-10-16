"""OP-1 (i): sky130_fd_pr (raw, f62031a1) + ngspice-46 native random functions -- per-instance independence etc.
Each test appends one JSON line to results/m1_native_mc.jsonl. Sequential ngspice runs only."""
import json, os, re, subprocess, sys, time, math, statistics as st
EXE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/runs/m1"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m1_native_mc.jsonl"
N_INC = ['.include "C:\\pdk\\sky130_fd_pr\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__tt.pm3.spice"',
         '.include "C:\\pdk\\sky130_fd_pr\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"']
NV = ["toxe", "vth0", "voff"]
_V = re.compile(r"^\s*(\S+)\s*=\s*([-+0-9.eE]+)\s*$", re.M)
_SM = re.compile(r"model\s+(\S+)\s*\n((?:[ \t]+\w+[ \t]+\S+[ \t]*\n)+)", re.M)


def app(rec):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(name, text, timeout=120):
    p = os.path.join(W, name + ".cir")
    open(p, "w", encoding="utf-8").write(text)
    t0 = time.perf_counter()
    r = subprocess.run([EXE, "-b", os.path.basename(p)], cwd=W, capture_output=True, text=True, errors="replace", timeout=timeout)
    dt = time.perf_counter() - t0
    log = r.stdout + r.stderr
    open(os.path.join(W, name + ".log"), "w", encoding="utf-8").write(log)
    vals = {m.group(1).lower(): float(m.group(2)) for m in _V.finditer(log)}
    sm = {}
    for m in _SM.finditer(log):
        sm.setdefault(m.group(1), {}).update({a: b for a, b in re.findall(r"(\w+)[ \t]+(\S+)", m.group(2))})
    return r.returncode, log, vals, sm, dt


def bench(gl, insts, opts, extra="", ctrl=None, temp=None):
    lines = ["* m1 bench"] + N_INC + gl + [f".option {opts}"] + ([f".temp {temp}"] if temp is not None else []) + [extra]
    lines += insts
    c = ctrl or ["op", "print v(ga) v(gb) v(ga)-v(gb)",
                 "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0 toxe voff", "showmod m.xb.msky130_fd_pr__nfet_01v8 : vth0 toxe voff"]
    lines += [".control"] + c + ["quit", ".endc", ".end"]
    return "\n".join(lines) + "\n"


PAIR = ["Ia 0 ga DC 10u", "Ib 0 gb DC 10u",
        "XA ga ga 0 0 sky130_fd_pr__nfet_01v8 w=5 l=1", "XB gb gb 0 0 sky130_fd_pr__nfet_01v8 w=5 l=1"]
GL_ALL = [f".param sky130_fd_pr__nfet_01v8__{v}_slope_spectre = agauss(0,1,1)" for v in NV]


def pick(sm, inst, key):
    for k, d in sm.items():
        if k.startswith(inst + ":") and key in d:
            return float(d[key])
    return None


which = sys.argv[1:] or ["T0", "T1", "T2", "T3", "T4", "T5", "T6", "T8"]

if "T0" in which:  # nominal
    rc, log, v, sm, dt = run("T0_nominal", bench([], PAIR, "scale=1u"))
    app({"test": "T0_nominal_no_agauss", "rc": rc, "wall_s": dt, "dVGS": v.get("v(ga)-v(gb)"), "vga": v.get("v(ga)"),
         "vth0_A": pick(sm, "xa", "vth0"), "vth0_B": pick(sm, "xb", "vth0"), "toxe_A": pick(sm, "xa", "toxe"), "voff_A": pick(sm, "xa", "voff"),
         "model_names": list(sm.keys())})

if "T1" in which:  # N seeds, separate processes, all 3 vars global agauss
    N = int(os.environ.get("M1_N", "200"))
    rows, walls = [], []
    for s in range(1, N + 1):
        rc, log, v, sm, dt = run("T1_s", bench(GL_ALL, PAIR, f"scale=1u seed={s}"))
        walls.append(dt)
        rows.append({"seed": s, "rc": rc, "dVGS": v.get("v(ga)-v(gb)"), "vga": v.get("v(ga)"), "vgb": v.get("v(gb)"),
                     **{f"{p}_{x}": pick(sm, x, p) for p in NV for x in ("xa", "xb")}})
    app({"test": "T1_seeds_global_agauss_all3", "N": N, "wall_s_mean": st.mean(walls), "wall_s_total": sum(walls), "rows": rows})

if "T2" in which:  # reproducibility: same seed twice, + seed differs
    r1 = run("T2_a", bench(GL_ALL, PAIR, "scale=1u seed=11"))
    r2 = run("T2_b", bench(GL_ALL, PAIR, "scale=1u seed=11"))
    r3 = run("T2_c", bench(GL_ALL, PAIR, "scale=1u seed=12"))
    f = lambda r: {"dVGS": r[2].get("v(ga)-v(gb)"), "vth0_A": pick(r[3], "xa", "vth0"), "vth0_B": pick(r[3], "xb", "vth0")}
    app({"test": "T2_seed_reproducibility", "seed11_run1": f(r1), "seed11_run2": f(r2), "seed12": f(r3),
         "bit_identical_same_seed": f(r1) == f(r2), "differs_other_seed": f(r1) != f(r3)})
    r4 = run("T2_d", bench(GL_ALL, PAIR, "scale=1u"))
    r5 = run("T2_e", bench(GL_ALL, PAIR, "scale=1u"))
    app({"test": "T2b_no_seed_option_two_runs", "run1": f(r4), "run2": f(r5), "identical": f(r4) == f(r5)})

if "T3" in which:  # SI units, no scale -- magnitude of perturbation
    pair_si = ["Ia 0 ga DC 10u", "Ib 0 gb DC 10u",
               "XA ga ga 0 0 sky130_fd_pr__nfet_01v8 w=5e-6 l=1e-6", "XB gb gb 0 0 sky130_fd_pr__nfet_01v8 w=5e-6 l=1e-6"]
    rn = run("T3_nom_si", bench([], pair_si, "reltol=1e-4"))
    rs = run("T3_si", bench([GL_ALL[1]], pair_si, "seed=3"))
    rsc = run("T3_scale", bench([GL_ALL[1]], PAIR, "scale=1u seed=3"))
    rnc = run("T3_nom_scale", bench([], PAIR, "scale=1u"))
    app({"test": "T3_units_SI_vs_scale1u_vth0only_seed3",
         "SI_nominal_vth0": pick(rn[3], "xa", "vth0"), "SI_mc_vth0_A": pick(rs[3], "xa", "vth0"), "SI_mc_vth0_B": pick(rs[3], "xb", "vth0"),
         "SI_rc": rs[0], "SI_dVGS": rs[2].get("v(ga)-v(gb)"),
         "SI_errors": [l for l in rs[1].splitlines() if re.search("error|warn|fail|singular", l, re.I)][:8],
         "scale_nominal_vth0": pick(rnc[3], "xa", "vth0"), "scale_mc_vth0_A": pick(rsc[3], "xa", "vth0"), "scale_mc_vth0_B": pick(rsc[3], "xb", "vth0"),
         "expected_sigma_dvth0_scale_V": 3.356e-3 / math.sqrt(5 * 1), "expected_sigma_dvth0_SI_V": 3.356e-3 / math.sqrt(5e-6 * 1e-6)})

if "T4" in which:  # temperature: same seed, different temp
    a = run("T4_27", bench(GL_ALL, PAIR, "scale=1u seed=21", temp=27))
    b = run("T4_85", bench(GL_ALL, PAIR, "scale=1u seed=21", temp=85))
    c = run("T4_m40", bench(GL_ALL, PAIR, "scale=1u seed=21", temp=-40))
    g = lambda r: {p + "_" + x: pick(r[3], x, p) for p in NV for x in ("xa", "xb")}
    app({"test": "T4_same_seed_across_temps", "t27": g(a), "t85": g(b), "tm40": g(c),
         "draws_identical_across_temps": g(a) == g(b) == g(c),
         "dVGS": [a[2].get("v(ga)-v(gb)"), b[2].get("v(ga)-v(gb)"), c[2].get("v(ga)-v(gb)")]})
    ctrl = ["set temp=27", "op", "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0", "print v(ga)-v(gb)",
            "set temp=85", "op", "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0", "print v(ga)-v(gb)"]
    d = run("T4_inproc", bench(GL_ALL, PAIR, "scale=1u seed=21", ctrl=ctrl))
    app({"test": "T4b_in_process_temp_change", "rc": d[0],
         "vth0_lines": re.findall(r"vth0\s+(\S+)", d[1]), "dVGS_lines": re.findall(r"v\(ga\)-v\(gb\)\s*=\s*(\S+)", d[1])})

if "T5" in which:  # in-process redraw: reset / mc_source
    ctrl = []
    for k in range(3):
        ctrl += ["reset", "op", f"echo R{k}", "print v(ga)-v(gb)", "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0"]
    a = run("T5_reset", bench(GL_ALL, PAIR, "scale=1u seed=5", ctrl=ctrl))
    ctrl2 = ["op", "echo M0", "print v(ga)-v(gb)", "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0"]
    for k in range(1, 3):
        ctrl2 += ["mc_source", "op", f"echo M{k}", "print v(ga)-v(gb)", "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0"]
    b = run("T5_mcsource", bench(GL_ALL, PAIR, "scale=1u seed=5", ctrl=ctrl2))
    ctrl3 = ["op", "echo S0", "print v(ga)-v(gb)"]
    for k in range(1, 3):
        ctrl3 += [f"setseed {100 + k}", "mc_source", "op", f"echo S{k}", "print v(ga)-v(gb)", "showmod m.xa.msky130_fd_pr__nfet_01v8 : vth0"]
    c = run("T5_setseed_mcsource", bench(GL_ALL, PAIR, "scale=1u seed=5", ctrl=ctrl3))
    for nm, r in (("reset", a), ("mc_source", b), ("setseed+mc_source", c)):
        app({"test": f"T5_in_process_redraw_{nm}", "rc": r[0], "wall_s": r[4],
             "dVGS_seq": re.findall(r"v\(ga\)-v\(gb\)\s*=\s*(\S+)", r[1]), "vth0_A_seq": re.findall(r"vth0\s+(\S+)", r[1]),
             "errors": [l for l in r[1].splitlines() if re.search("error|unknown|not found", l, re.I)][:6]})

if "T6" in which:  # instance multiplier m vs subckt mult
    insts = lambda extra: ["Ia 0 ga DC 40u", "Ib 0 gb DC 40u",
                           f"XA ga ga 0 0 sky130_fd_pr__nfet_01v8 w=5 l=1 {extra}", f"XB gb gb 0 0 sky130_fd_pr__nfet_01v8 w=5 l=1 {extra}"]
    out = {}
    for tag, extra in (("m1", "m=1"), ("m4", "m=4"), ("m4_mult4", "m=4 mult=4")):
        devs = []
        for s in (31, 32, 33):
            r = run(f"T6_{tag}_{s}", bench([GL_ALL[1]], insts(extra), f"scale=1u seed={s}"))
            devs.append({"seed": s, "rc": r[0], "vth0_A": pick(r[3], "xa", "vth0"), "dVGS": r[2].get("v(ga)-v(gb)"),
                         "err": [l for l in r[1].splitlines() if re.search("error|unknown", l, re.I)][:3]})
        out[tag] = devs
    rn = run("T6_nom", bench([], insts("m=1"), "scale=1u"))
    app({"test": "T6_instance_m_vs_mult_vth0only", "nominal_vth0": pick(rn[3], "xa", "vth0"), "runs": out})

if "T8" in which:  # semantics: one global agauss param referenced twice in one subckt scope / in two instances / top level
    txt = "\n".join(["* T8 semantics", ".param p = agauss(0,1,1)", ".option seed=9",
                     ".subckt two a", "R1 a 0 {1k*(2+p)}", "R2 a 0 {1k*(2+p)}", ".ends",
                     "X1 n1 two", "X2 n2 two", "R3 n3 0 {1k*(2+p)}", "R4 n4 0 {1k*(2+p)}",
                     "V1 n1 0 1", "V2 n2 0 1", "V3 n3 0 1", "V4 n4 0 1",
                     ".control", "op", "show r : resistance", "quit", ".endc", ".end"]) + "\n"
    r = run("T8_semantics", txt)
    app({"test": "T8_param_semantics", "rc": r[0], "show_lines": [l for l in r[1].splitlines() if l.strip()][-30:]})

print("done", which)
