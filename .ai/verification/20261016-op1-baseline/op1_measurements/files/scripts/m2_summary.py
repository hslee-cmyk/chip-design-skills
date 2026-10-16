import json, hashlib, os
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/m2_m3_lut_meta.jsonl"
PDK = r"C:/pdk/sky130_fd_pr"
rows = [json.loads(l) for l in open(OUT, encoding="utf-8")]
summ = []
for r in rows:
    if "file" not in r: continue
    m = r.get("meta_json.model_files_sha256", "<NO meta_json>")
    hits = dict((h[0], h[1]) for h in r.get("meta_json.hits", []))
    ver = hits.get(".ngspice", "<ABSENT>")
    chk = {}
    if isinstance(m, dict):
        for p, s in m.items():
            fp = os.path.join(PDK, p)
            chk[p] = (hashlib.sha256(open(fp, "rb").read()).hexdigest() == s) if os.path.exists(fp) else "missing"
    summ.append({"file": r["file"], "meta_keys": r["meta_keys"], "has_model_files_sha256": isinstance(m, dict) and len(m) > 0,
                 "n_model_files": len(m) if isinstance(m, dict) else 0, "sha_match_pdk": chk, "ngspice_version": ver,
                 "top_keys": r.get("meta_json.top_keys")})
with open(OUT, "a", encoding="utf-8") as f:
    f.write(json.dumps({"what": "SUMMARY", "rows": summ}, ensure_ascii=False) + "\n")
for s in summ:
    print(s["file"], "| meta:", s["meta_keys"], "| msha:", s["has_model_files_sha256"], s["n_model_files"], "| match:", set(map(str, s["sha_match_pdk"].values())), "| ver:", s["ngspice_version"])
