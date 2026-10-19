import json, hashlib, os
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m2_m3_lut_meta.jsonl"
PDK = r"C:/pdk/sky130_fd_pr"
res = {}
for l in open(OUT, encoding="utf-8"):
    r = json.loads(l)
    if r.get("file", "").startswith("sky130_nfet_pfet"):
        m = r["meta_json.model_files_sha256"]
        res[r["file"]] = {dev: {p: hashlib.sha256(open(os.path.join(PDK, p), "rb").read()).hexdigest() == s for p, s in d.items()} for dev, d in m.items()}
# pfet slice: lod.spice included?
for l in open(OUT, encoding="utf-8"):
    r = json.loads(l)
    if r.get("file", "").startswith("sky130_fd_pr__pfet"):
        res["pfet_slice_files:" + r["file"]] = sorted(r["meta_json.model_files_sha256"].keys()); break
with open(OUT, "a", encoding="utf-8") as f:
    f.write(json.dumps({"what": "combined_sha_check", "res": res}, ensure_ascii=False) + "\n")
print(json.dumps(res, indent=0)[:3000])
