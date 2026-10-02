"""20260930-v3-changed-stmt-scope 순서 7 (auditor): 병합본 redteam 그룹 로그를 합쳐 표를 만들고(combine.py와 같은 방식)
순서 3 base 표(out/base_table.json)와 케이스·단계 단위로 기계 대조한다.
사용: python -B cmp35.py <runs.txt> <base_table.json> <redteam 루트> <병합 표 출력> <대조 출력>"""
import hashlib
import json
import os
import sys

runs_p, base_p, root, merged_out, cmp_out = sys.argv[1:6]
runs = [l.rstrip("\n").split("\t") for l in open(runs_p, encoding="utf-8") if l.strip()]
table = {"runs": [], "cases": {}, "cases_replay": {}}
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
        dest[name] = {"verdict": x["verdict"], "group": g, "steps": steps, "reason": x.get("reason")}
expect_dirs = sorted(p for p in os.listdir(root + "/attacks") if os.path.isfile(f"{root}/attacks/{p}/expect.json"))
expect_dirs += [n for n in ("v3_survivor", "v7_unwired") if os.path.isfile(f"{root}/{n}/expect.json")]
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
json.dump(table, open(merged_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

base = json.load(open(base_p, encoding="utf-8"))
cmp = {"case_set_same": sorted(base["cases"]) == sorted(table["cases"]),
       "replay_set_same": sorted(base["cases_replay"]) == sorted(table["cases_replay"]),
       "case_verdict_diff": {}, "step_set_diff": {}, "step_verdict_diff": {}, "step_exit_diff": {}, "step_observed_diff": {},
       "replay_diff": {}}
for name in sorted(set(base["cases"]) | set(table["cases"])):
    b, m = base["cases"].get(name), table["cases"].get(name)
    if b is None or m is None:
        cmp["case_verdict_diff"][name] = [b and b["verdict"], m and m["verdict"]]
        continue
    if b["verdict"] != m["verdict"]:
        cmp["case_verdict_diff"][name] = [b["verdict"], m["verdict"]]
    if sorted(b["steps"]) != sorted(m["steps"]):
        cmp["step_set_diff"][name] = [sorted(b["steps"]), sorted(m["steps"])]
    for s in sorted(set(b["steps"]) & set(m["steps"])):
        bs, ms = b["steps"][s], m["steps"][s]
        k = name + "::" + s
        if bs["verdict"] != ms["verdict"]:
            cmp["step_verdict_diff"][k] = [bs["verdict"], ms["verdict"]]
        if bs["exit"] != ms["exit"]:
            cmp["step_exit_diff"][k] = [bs["exit"], ms["exit"]]
        if bs["observed"] != ms["observed"]:
            cmp["step_observed_diff"][k] = [bs["observed"], ms["observed"]]
for name in sorted(set(base["cases_replay"]) | set(table["cases_replay"])):
    b, m = base["cases_replay"].get(name), table["cases_replay"].get(name)
    if (b and b["verdict"]) != (m and m["verdict"]) or (b and b["steps"]) != (m and m["steps"]):
        cmp["replay_diff"][name] = [b, m]
red = sorted(r["test_id"].split("::", 1)[1] for r in base["red"])
flip = sorted(k.split("::", 1)[1] for k, v in cmp["step_verdict_diff"].items()
              if k.startswith("35-v3-changed-scope::") and v == ["FAIL", "PASS"])
cmp["red_steps_base"] = red
cmp["fail_to_pass_35"] = flip
cmp["only_35_differs_in_verdict"] = set(cmp["case_verdict_diff"]) == {"35-v3-changed-scope"} \
    and cmp["case_verdict_diff"]["35-v3-changed-scope"] == ["FAIL", "PASS"]
cmp["step_verdict_diff_equals_red"] = sorted(cmp["step_verdict_diff"]) == ["35-v3-changed-scope::" + s for s in red] and flip == red
cmp["contract7_same"] = {n: (n not in cmp["case_verdict_diff"]
                             and not any(k.startswith(n + "::") for k in list(cmp["step_verdict_diff"]) + list(cmp["step_exit_diff"]) + list(cmp["step_observed_diff"])))
                         for n in ("34-v3-exempt-binding", "v3_survivor", "26-gate-output-utf8", "27f-v6-reconfigure-except",
                                   "28-v3-gmid-options", "29-v4-decision-exempt", "31-v3-git-history")}
cmp["merged_counts"] = table["counts"]
cmp["base_counts"] = base["counts"]
cmp["coverage"] = table["coverage"]
cmp["merged_35_steps"] = table["cases"].get("35-v3-changed-scope", {}).get("steps")
json.dump(cmp, open(cmp_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in cmp.items() if k != "merged_35_steps"}, ensure_ascii=False, indent=1)[:6000])
