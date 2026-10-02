"""참고 대조: 키트 scope_proto.select(N2w·N2b)와 auditor 분류(disc35.json targets_auditor) 비교. 판정 근거 아님."""
import ast, json, sys
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit")
sys.path.insert(0, "C:/g244/gate")
import scope_proto as sp
import mutate_changed as mc

ENGINE = "skills/analog-gmid-design/assets/rt_engine.py"
spec = json.load(open("C:/g244/iso/tools/gates/redteam/attacks/35-v3-changed-scope/v.json", encoding="utf-8"))
mine = json.load(open("C:/g244/out/disc35.json", encoding="utf-8"))["steps"]
out = {}
for case in spec["cases"]:
    q = case["subjects"][0].split(".")[-1]
    bs = case["base"][ENGINE]["text"]; hs = case["head"][ENGINE]["text"]
    bfn = [n for n in ast.parse(bs).body if isinstance(n, ast.FunctionDef) and n.name == q][0]
    hfn = [n for n in ast.parse(hs).body if isinstance(n, ast.FunctionDef) and n.name == q][0]
    muts = mc.mutants(hfn, hs)
    ids = ["rt_engine:%s:%s:%s" % (q, op, p) for op, p, _ in muts]
    r = {}
    for v in ("N2w", "N2b"):
        sel = sp.select(bfn, hfn, muts, v)
        r[v] = [i for i, s in zip(ids, sel) if s]
    m = mine.get(case["step"], {}).get("targets_auditor")
    out[case["step"]] = {"proto_N2w": r["N2w"], "proto_N2b": r["N2b"], "auditor": m,
                         "N2w_eq_auditor": None if m is None else sorted(r["N2w"]) == sorted(m)}
json.dump(out, open("C:/g244/out/ref_proto.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v["N2w_eq_auditor"], len(v["proto_N2w"]), len(v["proto_N2b"])) for k, v in out.items()}))
