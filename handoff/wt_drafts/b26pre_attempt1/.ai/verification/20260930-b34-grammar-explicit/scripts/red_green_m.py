"""순서 7: 순서 3 red 27(out/red_check.json 'b34')이 병합본 green 실행(out/green_m.txt, -rA)에서 PASSED인지,
그리고 failure_hash를 base 판 merge_gate.red_failure_hash로 다시 계산해 같은지 본다.
사용: PYTHONPATH=<캐시> python -P red_green_m.py <red_check.json> <green_m.txt> <out.json>"""
import hashlib, json, re, sys
import merge_gate as mg
rc, green, out = sys.argv[1:4]
red = json.load(open(rc, encoding="utf-8"))["b34"]
txt = open(green, encoding="utf-8").read()
status = {}
for m in re.finditer(r"^(PASSED|FAILED|ERROR|XFAIL|XPASS|SKIPPED) (\S+)", txt, re.M):
    tid = m.group(2).replace("\\", "/")
    i = tid.find("skills/analog-gmid-design/")
    status[tid[i:]] = m.group(1)
res = {"red_n": len(red), "passed": 0, "not_passed": [], "hash_mismatch": [], "green_status_counts": {}}
for s in status.values():
    res["green_status_counts"][s] = res["green_status_counts"].get(s, 0) + 1
for r in red:
    st = status.get(r["test_id"])
    if st == "PASSED":
        res["passed"] += 1
    else:
        res["not_passed"].append([r["test_id"], st])
    if mg.red_failure_hash(r["test_id"], r["exc_type"]) != r["failure_hash"]:
        res["hash_mismatch"].append(r["test_id"])
ids = sorted(r["test_id"] for r in red)
hs = sorted(r["failure_hash"] for r in red)
res["test_ids"] = ids
res["failure_hashes"] = [r["failure_hash"] for r in sorted(red, key=lambda r: r["test_id"])]
res["sorted_hashes_sha256"] = hashlib.sha256("\n".join(hs).encode()).hexdigest()
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: res[k] for k in ("red_n", "passed", "not_passed", "hash_mismatch", "green_status_counts", "sorted_hashes_sha256")})
