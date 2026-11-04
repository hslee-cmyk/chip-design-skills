"""원인 규명: 경계 L에서 두 모드 ID가 실제로 같은가. 자릿수를 15로 올리고 geometry 포함으로 @m[id]·i(vds)를 읽는다.
또 슬라이스 meta 기록 bin(model_bin_per_L·model_bin_bounds_per_L)과 r2 model_bin_per_L_at_w_ref를 points.jsonl 본 측정·대조 cwd와 대조한다."""
import json, os, re, subprocess, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/op7a-iso/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
import numpy
W = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work"
plan = json.load(open(W + "/plan.json", encoding="utf-8"))
kinds = {k["name"]: k for k in plan["kinds"]}
g = plan["lut_grid_um"] * 1e-6
res = open(W + "/hand_c10b.jsonl", "w", encoding="utf-8")
def geom(text):
    m = re.search(r"ad=as=([0-9.eE+-]+)p pd=ps=([0-9.eE+-]+)u", text)
    return float(m.group(1)), float(m.group(2))
def run(k, pr, mode):
    d = f"{W}/hand_b/{pr['kind']}_{pr['l_m']:.3e}_{mode}"
    os.makedirs(d + "/cwd", exist_ok=True); os.makedirs(d + "/home", exist_ok=True)
    if mode == "hsa":
        open(d + "/cwd/.spiceinit", "w", newline="").write("set ngbehavior=hsa\n")
    sim = pr["sim"]; sub = k["subckt"]; ad, pd = geom(pr["_geometry"]); inst = f"m.xp.m{sub}"
    lines = ["* hand", *k["includes"], f".temp {sim['temp_c']}", f"vgs g 0 dc {sim['vgs']}", f"vds d 0 dc {sim['vds']}",
             f"vsrc s 0 dc {sim['vs']}", f"vb b 0 dc {sim['vb']}",
             f"xp d g s b {sub} l={pr['l_m']*1e6:g}u w={pr['_w_m']*1e6:g}u ad={ad:g}p as={ad:g}p pd={pd:g}u ps={pd:g}u m={sim['mult']:g}",
             ".control", "set numdgt=15", "op", "print i(vds)", f"print @{inst}[id]", f"print @{inst}[gm]", f"print @{inst}[vth]", "quit", ".endc", ".end"]
    open(d + "/cwd/s.cir", "w", newline="\n").write("\n".join(lines) + "\n")
    p = subprocess.run([plan["ngspice_exe"], "-b", "s.cir"], cwd=d + "/cwd", env=B.isolated_env(os.environ, d + "/home"), capture_output=True)
    t = p.stdout.decode(errors="replace")
    def f(pat):
        m = re.search(pat, t); return float(m.group(1)) if m else None
    return {"i_vds": f(r"i\(vds\)\s*=\s*([0-9.eE+-]+)"), "id": f(r"\[id\]\s*=\s*([0-9.eE+-]+)"), "gm": f(r"\[gm\]\s*=\s*([0-9.eE+-]+)"), "vth": f(r"\[vth\]\s*=\s*([0-9.eE+-]+)")}
for pr in plan["source"]["probes"]:
    k = kinds[pr["kind"]]; lut = pr["lut"]
    with numpy.load(lut["npz"]) as z:
        arr = z["ID"]; v = float(arr[tuple(lut["index"])]); dtype = str(arr.dtype)
    d, h = run(k, pr, "default"), run(k, pr, "hsa")
    r = {"kind": pr["kind"], "l_m": pr["l_m"], "lut_id": v, "dtype": dtype, "default": d, "hsa": h,
         "id_rel_modes": abs(abs(d["id"]) - abs(h["id"])) / abs(d["id"]),
         "ivds_rel_modes": abs(abs(d["i_vds"]) - abs(h["i_vds"])) / abs(d["i_vds"]),
         "lut_vs_id_rel": abs(v - abs(d["id"])) / v, "lut_vs_ivds_rel": abs(v - abs(d["i_vds"])) / v,
         "identify_id": B.identify_mode(v, d["id"], h["id"]), "identify_ivds": B.identify_mode(v, d["i_vds"], h["i_vds"])}
    res.write(json.dumps(r) + "\n"); res.flush()
res.close()

# 기록 bin 대조: 슬라이스 meta vs 본 측정·대조 (L, W)
MD = W + "/meta_dump"
pts = {}
for ln in open(W + "/run1/points.jsonl", encoding="utf-8"):
    p = json.loads(ln)
    pts[(p["kind"], B.grid_index(p["L"], g), B.grid_index(p["W"], g))] = p
man = json.load(open("C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/manifest.json", encoding="utf-8"))
rows = {"slice_cells": 0, "match_default": 0, "match_cwd": 0, "tie_cells": 0, "tie_match_default": 0, "tie_match_cwd": 0, "tie_differs_modes": 0, "missing": 0}
out = []
for s in man["slices"]:
    m = json.load(open(f"{MD}/{s['file']}.json", encoding="utf-8"))["meta_json"]
    kind = s["device"]; bins = kinds[kind]["bins"]
    for ls, mod in m["model_bin_per_L"].items():
        l = float(ls) * 1e-6
        key = (kind, B.grid_index(l, g), B.grid_index(m["w_m"], g))
        p = pts.get(key)
        if p is None:
            rows["missing"] += 1; continue
        rows["slice_cells"] += 1
        rows["match_default"] += mod == p["default"]; rows["match_cwd"] += mod == p["cwd"]
        if B.tie_axes(l, m["w_m"], bins, g):
            rows["tie_cells"] += 1
            rows["tie_match_default"] += mod == p["default"]; rows["tie_match_cwd"] += mod == p["cwd"]
            rows["tie_differs_modes"] += p["default"] != p["cwd"]
    out.append((s["file"], rows["tie_match_default"]))
# 결합 세트
combo = {}
for f in ("sky130_nfet_pfet_lut_v2_r2", "sky130_nfet_pfet_lut_v2_verify_midpoints_r2"):
    m = json.load(open(f"{MD}/{f}.npz.json", encoding="utf-8"))["meta_json"]
    c = {"cells": 0, "match_default": 0, "match_cwd": 0, "tie": 0, "tie_default": 0, "tie_cwd": 0}
    for dev, tab in m["model_bin_per_L_at_w_ref"].items():
        for ls, b in tab.items():
            l = float(ls) * 1e-6
            p = pts[(dev, B.grid_index(l, g), B.grid_index(m["w_ref_m"], g))]
            c["cells"] += 1; c["match_default"] += b["model"] == p["default"]; c["match_cwd"] += b["model"] == p["cwd"]
            if B.tie_axes(l, m["w_ref_m"], kinds[dev]["bins"], g):
                c["tie"] += 1; c["tie_default"] += b["model"] == p["default"]; c["tie_cwd"] += b["model"] == p["cwd"]
    combo[f] = c
# 위치 선언 cap 묶음
loc = json.load(open("C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/op7a-iso/skills/analog-gmid-design/assets/lut_v2_location.json", encoding="utf-8"))
cap = {}
for f in ("noise", "mismatch"):
    m = json.load(open(f"{MD}/{loc['files'][f]['path']}.json", encoding="utf-8"))["meta_json"]
    cap[f] = m["cap_npz_sha256"] == loc["files"]["cap_npz"]["sha256"]
json.dump({"slice_vs_measure": rows, "combined": combo, "cap_bind": cap}, open(W + "/record_bin_check.json", "w"), indent=1)
print(json.dumps({"slice_vs_measure": rows, "combined": combo, "cap_bind": cap}, indent=1))
