# OP-7b 찾기 규칙 실현 가능성: OP-1b 입력 LUT 기록 값 -> 뿌리 아래 파일 LF ⊆ 선언 model_files_sha256? (시뮬레이터 호출 0) 결과 m3.jsonl
import hashlib, json, os, sys, io
import numpy as np
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/docs-op75"
A = W + "/skills/analog-gmid-design/assets"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m3.jsonl")
open(OUT, "w").close()


def w(o):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")


def lf(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


decl = json.load(open(A + "/lut_v2_bin_rule.json", encoding="utf-8"))
dset = set(decl["model_files_sha256"])
w({"decl_n": len(dset), "simulator": decl["simulator"], "compat_mode": decl["compat"]["mode"],
   "spiceinit_sha_ok": hashlib.sha256(decl["compat"]["spiceinit_text"].encode()).hexdigest() == decl["compat"]["spiceinit_sha256"]})
loc = json.load(open(A + "/lut_v2_location.json", encoding="utf-8"))
pdk = (loc.get("pdk_root") or {})
root = os.environ.get(pdk.get("env") or "", "") or pdk.get("default")
w({"root": root, "root_exists": bool(root and os.path.isdir(root))})
B = W + "/.ai/verification/20261104-op1b/baseline"
for i in range(1, 11):
    d = json.load(open(f"{B}/R{i}.converted.json", encoding="utf-8"))["input"]
    pr = d.get("process") or {}
    recs = {}
    out = {"input": f"R{i}", "lut_fields": [k for k in pr if "lut" in k]}
    lst = pr.get("lut_files") or ([{"path": pr["lut_npz"]}] if pr.get("lut_npz") else [])
    out["n_lut"] = len(lst)
    for e in lst:
        p = e.get("path")
        out["path_tail"] = (p or "")[-60:]
        try:
            z = np.load(p, allow_pickle=False)
            m = json.loads(str(z["meta_json"]))
            mf = m.get("model_files_sha256") or {}
            flat = {}
            for k, v in mf.items():
                if isinstance(v, dict):
                    flat.update(v)
                else:
                    flat[k] = v
            recs.update(flat)
            out["simulator_meta"] = {k: m.get(k) for k in ("ngspice", "simulator") if k in m}
        except Exception as ex:
            out["err"] = f"{type(ex).__name__}: {ex}"[:160]
    miss = []
    for rel, s in recs.items():
        q = os.path.join(root, rel)
        if not os.path.exists(q):
            miss.append({"rel": rel, "why": "no_file"}); continue
        v = lf(open(q, "rb").read())
        if v not in dset:
            miss.append({"rel": rel, "why": "lf_not_in_decl", "lf": v[:12], "rec": s[:12]})
    out.update(n_records=len(recs), not_subset=miss, rec_value_in_decl_direct=sum(1 for s in recs.values() if s in dset))
    w(out)
