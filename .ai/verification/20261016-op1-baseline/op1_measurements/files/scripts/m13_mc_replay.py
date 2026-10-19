"""design §13.2 preparation (verifier): from a baseline offset_mc result (seed, n_requested, mismatch_vars) and its input
(devices order, n_fingers), regenerate z with numpy default_rng(seed).standard_normal() in the old order
(sample -> device (input order) -> variable), rebuild the alterparam values z*1e-6/sqrt(m) with the old '%.12e' format,
and compare them string-for-string with the baseline <stem>.mc.cir. Bit identity here = the replay order of S-4 is right.
usage: python m13_mc_replay.py <sim.json or offset_mc json> <oracle_input.json> <mc.cir>   (appends to results/m13_mc_replay.jsonl)"""
import json, math, re, sys
import numpy as np
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m13_mc_replay.jsonl"


def main(simp, inpp, cirp):
    s = json.load(open(simp, encoding="utf-8"))
    mc = s.get("offset_mc", s)
    inp = json.load(open(inpp, encoding="utf-8"))
    seed, n = int(mc["seed"]), int(mc["n_requested"])
    mv = mc["mismatch_vars"]
    devs = inp["devices"]
    rng = np.random.default_rng(seed)
    exp = []                    # per sample: {param name: formatted value}; draw order = sample -> input device -> variable
    for k in range(n):
        blk = {}
        for d in devs:
            nm = d["name"]
            for j in range(len(mv.get(nm, []))):
                blk[f"pv_{nm}_{j}"] = f"{float(rng.standard_normal()) * 1e-6 / math.sqrt(d['n_fingers']):.12e}"
        exp.append(blk)
    lines = re.findall(r"^alterparam (\S+) = (\S+)$", open(cirp, encoding="utf-8").read(), re.M)
    zero = sum(len(mv.get(d["name"], [])) for d in devs)
    blocks = [dict(lines[i:i + zero]) for i in range(0, len(lines), zero)] if zero else []
    got, got_s = lines, blocks[1:]          # block 0 = sample 0 (all zeros); lines are emitted in netlist order, keyed by name
    rec = {"sim": simp, "input": inpp, "mc_cir": cirp, "seed": seed, "n_requested": n,
           "n_vars_total": zero, "n_expected_lines": len(exp), "n_got_lines": len(got_s),
           "sample0_all_zero": bool(blocks) and all(float(v) == 0.0 for v in blocks[0].values()),
           "bit_identical": exp == got_s,
           "first_mismatch": next(({"i": i, "exp": e, "got": g} for i, (e, g) in enumerate(zip(exp, got_s)) if e != g), None),
           "sigma_in_mV": mc.get("sigma_in_mV"), "mean_in_mV": mc.get("mean_in_mV"), "a_dc_signed": mc.get("a_dc_signed")}
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False)[:800])


if __name__ == "__main__":
    main(*sys.argv[1:4])
