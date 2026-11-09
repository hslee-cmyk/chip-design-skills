"""Re-run the final hand-design SPICE testbench with the junction geometry extracted from the GDS.

usage: python post_layout_spice.py <final_dir> <extracted.cir> <out_dir>
- final_dir: hand design final run (tso_vbias.cir, spice_vbias.json)
- extracted.cir: KLayout LVS target netlist (merged devices: total W, AS/AD/PS/PD in um / um^2)
Each finger line X<dev>_<k> keeps its w_s and L; its ad/as/pd/ps become the extracted totals / fingers.
Extracted devices are matched to schematic devices by connectivity (gate net label, diode, model, L, W) --
no device name from the extractor is used.
"""
import json
import os
import re
import subprocess
import sys

NGSPICE = "C:/ngspice/Spice64/bin/ngspice_con.exe"
final_dir, ext_path, out_dir = sys.argv[1:4]
os.makedirs(out_dir, exist_ok=True)
design = json.load(open(os.path.join(final_dir, "design_for_layout.json"), encoding="utf-8"))
dev = design["devices"]

# --- parse extracted netlist (continuation lines start with '+') ---
txt = open(ext_path, encoding="utf-8").read().replace("\n+", " ")
ext = []
for line in txt.splitlines():
    if not line.startswith("M"):
        continue
    tok = line.split()
    d, g, s, b, model = tok[1:6]
    kv = dict(t.split("=") for t in tok[6:])
    ext.append(dict(d=d, g=g, s=s, model=model, **{k.upper(): float(v) for k, v in kv.items()}))


def match(name, p):
    kind_model = "sky130_fd_pr__nfet_01v8" if p["kind"] == "nmos" else "sky130_fd_pr__pfet_01v8"
    W = p["w_s"] * p["m"] * 1e6
    Lg = p["L"] * 1e6
    cands = [e for e in ext if e["model"] == kind_model and abs(e["L"] - Lg) < 1e-6 and abs(e["W"] - W) < 1e-6]
    # gate net: labelled nets keep their names in the extraction; diode = gate net equals one S/D net
    named = [e for e in cands if e["g"] == p["g"]]
    if named:
        cands = named
    elif p["g"] == p["d"] or p["g"] == p["s"]:
        cands = [e for e in cands if e["g"] in (e["d"], e["s"])]
    else:
        cands = [e for e in cands if e["g"] not in (e["d"], e["s"])]
    if len(cands) != 1:
        raise RuntimeError("cannot match %s uniquely: %d candidates" % (name, len(cands)))
    return cands[0]


per_finger = {}
table = []
for n, p in dev.items():
    e = match(n, p)
    m = p["m"]
    per_finger[n] = dict(ad=e["AD"] / m, as_=e["AS"] / m, pd=e["PD"] / m, ps=e["PS"] / m)
    table.append((n, m, e["W"], e["L"], e["AD"], e["AS"], e["PD"], e["PS"]))

src = open(os.path.join(final_dir, "tso_vbias.cir"), encoding="utf-8").read().splitlines()
outl = []
pat = re.compile(r"^X(M\d+)_(\d+) ")
for line in src:
    mo = pat.match(line)
    if mo:
        n = mo.group(1)
        f = per_finger[n]
        line = re.sub(r"ad=\S+", "ad=%.6gp" % f["ad"], line)
        line = re.sub(r"as=\S+", "as=%.6gp" % f["as_"], line)
        line = re.sub(r"pd=\S+", "pd=%.6gu" % f["pd"], line)
        line = re.sub(r"ps=\S+", "ps=%.6gu" % f["ps"], line)
    outl.append(line)
cir = os.path.join(out_dir, "tso_vbias_postlayout.cir")
open(cir, "w", encoding="utf-8").write("\n".join(outl) + "\n")
r = subprocess.run([NGSPICE, "-b", cir], capture_output=True, text=True)
log = r.stdout + r.stderr
open(os.path.join(out_dir, "tso_vbias_postlayout.log"), "w", encoding="utf-8").write(log)
res = {}
for key in ("a0db", "fu", "phu"):
    mm = re.search(r"^%s\s*=\s*([-+0-9.eE]+)" % key, log, re.M)
    res[key] = float(mm.group(1)) if mm else None
mi = re.search(r"i\(vdd\)\s*=\s*([-+0-9.eE]+)", log)
res["i_vdd"] = float(mi.group(1)) if mi else None
pre = json.load(open(os.path.join(final_dir, "spice_vbias.json"), encoding="utf-8"))
res["pm"] = 180 + res["phu"] if res["phu"] is not None else None
out = {"post_layout": res, "pre_layout": {k: pre.get(k) for k in ("a0db", "fu", "phu", "pm", "i(vdd)")},
       "extracted_devices": [dict(zip(("dev", "m", "W_um", "L_um", "AD_um2", "AS_um2", "PD_um", "PS_um"), t)) for t in table]}
json.dump(out, open(os.path.join(out_dir, "post_layout_spice.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1))
