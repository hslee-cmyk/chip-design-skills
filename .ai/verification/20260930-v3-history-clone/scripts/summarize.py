"""run_all 로그에서 케이스·단계 판정표를 뽑고 base 하네스(isob) 부분 실행과 대조한다."""
import hashlib
import json

LOGS = {
    "T_full": "C:/g17/iso/tools/gates/redteam/logs/20260930-195924-direct.jsonl",
    "T_cases": "C:/g17/iso/tools/gates/redteam/logs/20260930-203703-direct-cases.jsonl",
    "baseh_vcase": "C:/g17/isob/tools/gates/redteam/logs/20260930-200253-direct.jsonl",
    "baseh_cases": "C:/g17/isob/tools/gates/redteam/logs/20260930-200747-direct-cases.jsonl",
    "T_red31": "C:/g17/iso/tools/gates/redteam/logs/20260930-195723-direct.jsonl",
}


def table(path):
    cases, steps, summary = {}, {}, None
    for l in open(path, encoding="utf-8"):
        d = json.loads(l)
        if d.get("summary"):
            summary = d
            continue
        cases[d["case"]] = d["verdict"]
        for s in d.get("steps", []):
            steps["%s::%s" % (d["case"], s["step"])] = [s["verdict"], s.get("exit"), s.get("observed")]
    return cases, steps, summary


out = {}
for k, p in LOGS.items():
    c, s, sm = table(p)
    out[k] = {"sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "summary": sm, "cases": c,
              "n_steps": len(s)}
    out[k]["_steps"] = s
tf, bv = out["T_full"], out["baseh_vcase"]
diff_steps = {k: [bv["_steps"][k], tf["_steps"].get(k)] for k in bv["_steps"] if bv["_steps"][k] != tf["_steps"].get(k)}
diff_cases = {k: [bv["cases"][k], tf["cases"].get(k)] for k in bv["cases"] if bv["cases"][k] != tf["cases"].get(k)}
out["compare_vcase_baseh_vs_T"] = {"cases_compared": len(bv["cases"]), "steps_compared": len(bv["_steps"]),
                                   "diff_cases": diff_cases, "diff_steps": diff_steps}
tc, bc = out["T_cases"], out["baseh_cases"]
out["compare_cases_baseh_vs_T"] = {"diff_cases": {k: [bc["cases"][k], tc["cases"].get(k)] for k in bc["cases"]
                                                  if bc["cases"][k] != tc["cases"].get(k)},
                                   "diff_steps": {k: [bc["_steps"][k], tc["_steps"].get(k)] for k in bc["_steps"]
                                                  if bc["_steps"][k] != tc["_steps"].get(k)}}
out["T_full_nonpass_steps"] = {k: v for k, v in tf["_steps"].items() if v[0] not in ("PASS", "RECORD")}
out["T_full_step_verdicts"] = {k: v[0] for k, v in tf["_steps"].items()}
out["T_full_step_verdicts_sha256"] = hashlib.sha256(
    json.dumps(out["T_full_step_verdicts"], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
for k in LOGS:
    out[k].pop("_steps")
with open("C:/g17/probe/summary.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("compare_vcase_baseh_vs_T", "compare_cases_baseh_vs_T", "T_full_nonpass_steps",
                                      "T_full_step_verdicts_sha256")}, ensure_ascii=False, indent=1)[:4000])
print(json.dumps({k: {"sha": out[k]["sha256"], "summary": out[k]["summary"], "cases": out[k]["cases"]}
                  for k in LOGS}, ensure_ascii=False)[:9000])
