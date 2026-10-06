"""kill_results.jsonl + v3_b26v4(.out).jsonl -> 판정 수치 요약. argv: <out 디렉터리> <요약 json>"""
import hashlib
import json
import sys

O, OUTP = sys.argv[1:3]
recs = [json.loads(l) for l in open(O + "/kill_results.jsonl", encoding="utf-8")]
main = [r for r in recs if r["table"] == "main"]
ref = [r for r in recs if r["table"] == "ref"]
base_runs = [r for r in recs if r["table"] == "baseline"]
ident = [r for r in recs if r["table"] == "identity"]
extra = [r for r in recs if r["table"] == "extra"]
assert len(main) == 20 and len(ref) == 16
stmt_units = {}
for r in main:
    k = (r["module"], r["base_line"], r["op"])
    stmt_units.setdefault(k, []).append(r["killed"])
assert all(len(set(v)) == 1 for v in stmt_units.values())
seed = [r for r in ref if "seed" in r["memo"]]
v3 = json.load(open(O + "/v3_b26v4.json", encoding="utf-8"))
v5 = json.load(open(O + "/v3_b26v5.json", encoding="utf-8"))
ids = json.load(open(O + "/ids_b26v4.json", encoding="utf-8"))
id_recs = [json.loads(l) for l in open(O + "/v3_b26v4.out.jsonl", encoding="utf-8")]
sel = [x for x in id_recs if x["id"] in set(ids)]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


res = {
    "main_ids_targeted": v3["ids_targeted"], "main_ids_total": v3["ids_total"],
    "v3_b1_h4": {k: v3.get(k) for k in ("mutants", "not_targeted", "out_records", "defs", "proto_targeted", "sym_diff", "order_ok", "tool_exit")},
    "v3_c4b_h5": {k: v5.get(k) for k in ("mutants", "not_targeted", "out_records", "defs", "proto_targeted", "sym_diff", "order_ok", "tool_exit")},
    "v3_b26v4_out_sha256": sha(O + "/v3_b26v4.out.jsonl"), "v3_b26v5_out_sha256": sha(O + "/v3_b26v5.out.jsonl"),
    "main_id_records": sel,
    "main_killed_ids": sum(r["killed"] for r in main), "main_survived_ids": [(r["head_id"], r["base_line"], r["base_text"]) for r in main if not r["killed"]],
    "main_stmt_units": len(stmt_units), "main_stmt_killed": sum(1 for v in stmt_units.values() if v[0]),
    "main_stmt_survived": sorted("%s %s %s" % k for k, v in stmt_units.items() if not v[0]),
    "ref_total": len(ref), "ref_killed": sum(r["killed"] for r in ref),
    "ref_survived": [(r["memo"], r["base_line"], r["base_text"]) for r in ref if not r["killed"]],
    "seed_total": len(seed), "seed_killed": sum(r["killed"] for r in seed),
    "baseline": [(r["tag"], r["summary"], r["exit"]) for r in base_runs],
    "identity_controls": len(ident), "identity_all_pass": all(r["exit"] == 0 and not r["killed"] for r in ident),
    "extras": [(r["memo"], r["summary"], r["exit"]) for r in extra],
    "non_kill_exit_codes": sorted({r["exit"] for r in main + ref if not r["killed"]}),
    "killed_exit_codes": sorted({r["exit"] for r in main + ref if r["killed"]}),
    "errors_in_runs": sum(r.get("n_error", 0) for r in recs),
    "table": [{"n": r["n"], "t": r["table"], "op": r["op"], "line": r["base_line"], "killed": r["killed"],
               "by": r["failed"], "contracts": r["killing_contracts"]} for r in main + ref],
}
json.dump(res, open(OUTP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("table", "main_id_records")}, ensure_ascii=False, indent=1))
