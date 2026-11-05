"""관문이 막혀 선언을 쓰지 않았다. 측정된 값으로 만들면 어떤 모양인지 재기만 한다(파일로 선언을 쓰지 않음, 측정 산출물 points.jsonl만 입력)."""
import json, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/op7a-iso/.ai/verification/20261104-op7a/scripts")
import bin_rule_lib as B
W = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work"
plan = json.load(open(W + "/plan.json", encoding="utf-8"))
kinds = {k["name"]: k for k in plan["kinds"]}
g = plan["lut_grid_um"] * 1e-6
dirs, ev = [], []
per = {}
for ln in open(W + "/run1/points.jsonl", encoding="utf-8"):
    p = json.loads(ln)
    k = kinds[p["kind"]]; by = {b["model"]: b for b in k["bins"]}
    d = B.point_direction(p["L"], p["W"], by[p["default"]], k["bins"], g)
    dirs.append(d)
    per[p["kind"]] = per.get(p["kind"], 0) + 1
    if d:
        ev.append((p["L"], p["W"], p["default"]))
rule, why = B.derive_rule(dirs)
lf, md = B.union_model_sha([tuple(r) for r in plan["model_records"]], lambda x: open(x, "rb").read())
ver = B.set_versions(plan["set_versions"])
d = B.build_decl(lf, ver[0], "default", "", rule, ev, plan["date"])
print(json.dumps({"rule": rule, "why": why, "points_total": per, "tie_points": len(ev), "n_lf": len(lf), "n_machine": len(md),
                  "unrecorded": ver[1], "validate": B.validate_decl(d)}))
