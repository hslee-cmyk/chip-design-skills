"""design §13.2/§14 B-7 measurement: does replacing the DC-gain 'real' test |Im h0| <= 1e-3|h0| by |Im h0| <= data_rel(ac file)|h0|
change the baseline? Scans every <stem>.ac.txt under baseline/ (h0 = first row) and every sim.json with offset_mc.
data_rel re-derived here from its definition (0.5*10^(1-d_min), d_min = fewest mantissa digits in the file)."""
import glob, json, os, re
B = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/baseline"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m7_gain_imag.json"


def data_rel(path):
    d_min = None
    for line in open(path):
        for tok in line.split():
            mant = re.split(r"[eE]", tok.lstrip("+-"), maxsplit=1)[0]
            if not re.fullmatch(r"[0-9]+\.?[0-9]*|\.[0-9]+", mant):
                continue
            dg = mant.replace(".", "").lstrip("0")
            if dg and (d_min is None or len(dg) < d_min):
                d_min = len(dg)
    return None if d_min is None else 0.5 * 10.0 ** (1 - d_min)


def first(path):
    for line in open(path):
        try:
            v = [float(x) for x in line.split()]
        except ValueError:
            continue
        if len(v) >= 3:
            return v[1], v[2]
    return None


rows = []
for p in glob.glob(B + "/**/*.ac.txt", recursive=True):
    h = first(p)
    if not h:
        continue
    mag = abs(complex(*h))
    if mag == 0:
        continue
    r = abs(h[1]) / mag
    u = data_rel(p)
    rows.append({"file": os.path.relpath(p, B), "ratio_im_over_abs": r, "data_rel": u, "old_real": r <= 1e-3, "new_real": (u is not None and r <= u)})
mc = []
for p in glob.glob(B + "/**/*.sim.json", recursive=True):
    try:
        s = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    m = s.get("offset_mc")
    if isinstance(m, dict):
        mc.append({"file": os.path.relpath(p, B), "status": m.get("status"), "reason": m.get("reason"), "a_dc_signed": m.get("a_dc_signed")})
flip = [r for r in rows if r["old_real"] and not r["new_real"]]
res = {"n_ac_files": len(rows), "n_old_real": sum(r["old_real"] for r in rows), "n_new_real": sum(r["new_real"] for r in rows),
       "n_flip_ok_to_unavailable": len(flip), "ratio_range_old_real": [min((r["ratio_im_over_abs"] for r in rows if r["old_real"]), default=None),
                                                                      max((r["ratio_im_over_abs"] for r in rows if r["old_real"]), default=None)],
       "data_rel_values": sorted({r["data_rel"] for r in rows if r["data_rel"] is not None}),
       "offset_mc_runs": mc, "rows": rows}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v for k, v in res.items() if k != "rows"})
