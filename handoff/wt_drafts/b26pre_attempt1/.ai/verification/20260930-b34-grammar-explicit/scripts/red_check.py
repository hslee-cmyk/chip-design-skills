"""red 캡처(red_T.jsonl)와 pytest 출력(full_T_red.txt) 대조 + 해시 재계산(base 판 merge_gate.red_failure_hash)."""
import json, re, sys
import merge_gate as mg

cap, txt, out = sys.argv[1:4]
L = [json.loads(l) for l in open(cap, encoding="utf-8")]
failed = set()
for line in open(txt, encoding="utf-8", errors="replace"):
    if line.startswith("FAILED "):
        nid = line[7:].split(" - ")[0].strip()
        nid = nid.replace("\\", "/")
        nid = nid[nid.index("skills/"):]
        failed.add(nid)
res = {"capture_lines": len(L), "pytest_failed": len(failed), "b34": [], "other": [], "hash_mismatch": []}
for x in L:
    h = mg.red_failure_hash(x["test_id"], x["exc_type"])
    if h != x["failure_hash"]:
        res["hash_mismatch"].append(x["test_id"])
    (res["b34"] if "test_b34_grammar_explicit.py" in x["test_id"] else res["other"]).append(x)
res["b34_in_pytest_failed"] = sum(1 for x in res["b34"] if x["test_id"] in failed)
res["b34_not_failed"] = [x for x in res["b34"] if x["test_id"] not in failed]
res["failed_not_captured"] = sorted(failed - {x["test_id"] for x in L})
res["b34_exc_types"] = sorted({x["exc_type"] for x in res["b34"]})
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: (v if not isinstance(v, list) or k in ("b34_exc_types", "hash_mismatch", "failed_not_captured", "b34_not_failed") else len(v)) for k, v in res.items()})
