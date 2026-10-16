"""OP-1 (ii)(iii): LUT slice meta -- model_files_sha256 / simulator version presence. read only."""
import json, sys, os, glob, hashlib
import numpy as np
R = r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m2_m3_lut_meta.jsonl"
def app(rec):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
man = json.load(open(os.path.join(R, "manifest.json"), encoding="utf-8"))
app({"what": "manifest_keys", "keys": list(man.keys()) if isinstance(man, dict) else str(type(man))})
def walk(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            lk = k.lower()
            if "sha256" in lk or "ngspice" in lk or "simulator" in lk or "version" in lk or "model_files" in lk:
                hits.append((p, v if not isinstance(v, (dict, list)) or len(json.dumps(v)) < 400 else json.dumps(v)[:400]))
            hits += walk(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:3]):
            hits += walk(v, f"{path}[{i}]")
    return hits
app({"what": "manifest_hits", "hits": walk(man)[:60]})
for f in sorted(glob.glob(os.path.join(R, "*.npz"))):
    z = np.load(f, allow_pickle=False)
    keys = list(z.files)
    meta = {}
    for k in keys:
        if "meta" in k.lower():
            a = z[k]
            try:
                s = a.item() if a.shape == () else (a.tobytes().decode("utf-8") if a.dtype.kind in "SU" else None)
                if isinstance(s, bytes): s = s.decode("utf-8")
                if a.dtype.kind == "U": s = str(a)
                meta[k] = json.loads(s) if isinstance(s, str) else repr(a)[:200]
            except Exception as e:
                meta[k] = f"<unparsed {a.dtype} {a.shape}: {e}>"
    rec = {"file": os.path.basename(f), "n_keys": len(keys), "meta_keys": list(meta.keys()),
           "non_meta_keys_head": [k for k in keys if "meta" not in k.lower()][:20]}
    for mk, mv in meta.items():
        if isinstance(mv, dict):
            rec[mk + ".top_keys"] = list(mv.keys())
            rec[mk + ".model_files_sha256"] = mv.get("model_files_sha256", "<ABSENT>")
            rec[mk + ".hits"] = walk(mv)[:30]
    app(rec)
print("done")
