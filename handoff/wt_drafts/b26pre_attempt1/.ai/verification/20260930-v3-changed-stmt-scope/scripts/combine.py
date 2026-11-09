"""그룹별 run_all 로그를 합쳐 base 표를 만든다 + red failure_hash(base 판 merge_gate.red_failure_hash).
PYTHONPATH=C:/g244/gate -P 로 실행."""
import hashlib, json, os, sys
import merge_gate as mg

ROOT = "C:/g244/iso/tools/gates/redteam"
runs = [l.rstrip("\n").split("\t") for l in open("C:/g244/out/runs.txt", encoding="utf-8") if l.strip()]
table = {"runs": [], "cases": {}, "cases_replay": {}}
seen = {}
for g, rc, start, end, log, _sha in runs:
    data = open(log, "rb").read()
    lines = [json.loads(x) for x in data.decode("utf-8").splitlines() if x.strip()]
    summ = [x for x in lines if x.get("summary")]
    table["runs"].append({"group": g, "exit": int(rc), "start": start, "end": end, "log": log.replace("\\", "/"),
                          "log_sha256": hashlib.sha256(data).hexdigest(), "summary": summ[-1] if summ else None})
    dest = table["cases_replay"] if g == "g7cases" else table["cases"]
    for x in lines:
        if x.get("summary"):
            continue
        name = x["case"]
        if name in dest:
            raise SystemExit("중복 케이스 " + name)
        steps = {s["step"]: {"verdict": s["verdict"], "exit": s.get("exit"), "observed": s.get("observed")}
                 for s in x.get("steps", [])}
        dest[name] = {"verdict": x["verdict"], "group": g, "steps": steps,
                      "reason": x.get("reason")}
# 범위 확인: run_all.discover(None)와 같은 디렉터리 집합
expect_dirs = sorted(p for p in os.listdir(ROOT + "/attacks") if os.path.isfile(f"{ROOT}/attacks/{p}/expect.json"))
expect_dirs += [n for n in ("v3_survivor", "v7_unwired") if os.path.isfile(f"{ROOT}/{n}/expect.json")]
table["coverage"] = {"expected": len(expect_dirs), "got": len(table["cases"]),
                     "missing": sorted(set(expect_dirs) - set(table["cases"])),
                     "extra": sorted(set(table["cases"]) - set(expect_dirs))}
cnt, scnt = {}, {}
for c in table["cases"].values():
    cnt[c["verdict"]] = cnt.get(c["verdict"], 0) + 1
    for s in c["steps"].values():
        scnt[s["verdict"]] = scnt.get(s["verdict"], 0) + 1
table["counts"] = {"cases": cnt, "steps": scnt}
sv = {f"{k}::{s}": v["verdict"] for k, c in table["cases"].items() for s, v in c["steps"].items()}
table["step_verdicts_sha256"] = hashlib.sha256(json.dumps(sv, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
table["step_verdicts_n"] = len(sv)
red = []
c35 = table["cases"].get("35-v3-changed-scope", {})
for s, v in sorted(c35.get("steps", {}).items()):
    if v["verdict"] == "FAIL":
        tid = "tools/gates/redteam/attacks/35-v3-changed-scope::" + s
        red.append({"test_id": tid, "exc_type": "redteam.FAIL", "failure_hash": mg.red_failure_hash(tid, "redteam.FAIL")})
table["red"] = red
table["aggregate_hash"] = hashlib.sha256("\n".join(sorted(r["failure_hash"] for r in red)).encode("utf-8")).hexdigest()
json.dump(table, open("C:/g244/out/base_table.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"coverage": table["coverage"], "counts": table["counts"], "red": red,
                  "aggregate": table["aggregate_hash"], "sv": table["step_verdicts_sha256"], "n": len(sv),
                  "runs": [(r["group"], r["exit"], r["log_sha256"]) for r in table["runs"]],
                  "non_pass": {k: v["verdict"] for k, v in table["cases"].items() if v["verdict"] != "PASS"}},
                 ensure_ascii=False, indent=1))
