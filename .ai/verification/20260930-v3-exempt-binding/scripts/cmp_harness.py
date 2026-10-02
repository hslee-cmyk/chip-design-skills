"""순서 3: T 하네스(iso) 대 base 하네스(isob) -- 같은 base 게이트에서 redteam 전체·--cases 0.5 로그의 케이스·단계
(verdict, exit, observed) 기계 대조. 사용: python cmp_harness.py <T full> <B full> <T cases> <B cases> <출력 json>"""
import hashlib
import json
import sys


def table(path):
    cases, steps, summary = {}, {}, None
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("summary"):
            summary = {k: d.get(k) for k in ("cases", "steps")}
            continue
        cases[d["case"]] = d["verdict"]
        for s in d.get("steps", []):
            steps["%s::%s" % (d["case"], s["step"])] = {"verdict": s["verdict"], "exit": s.get("exit"),
                                                        "observed": s.get("observed")}
    return cases, steps, summary


tf, bf, tc, bc, out = sys.argv[1:6]
res = {}
for tag, (t, b) in {"full": (tf, bf), "cases": (tc, bc)}.items():
    ct, st, smt = table(t)
    cb, sb, smb = table(b)
    res[tag] = {
        "T_log_sha256": hashlib.sha256(open(t, "rb").read()).hexdigest(),
        "B_log_sha256": hashlib.sha256(open(b, "rb").read()).hexdigest(),
        "T_summary": smt, "B_summary": smb,
        "cases_only_T": sorted(set(ct) - set(cb)), "cases_only_B": sorted(set(cb) - set(ct)),
        "case_verdict_diff": {k: [ct[k], cb[k]] for k in sorted(set(ct) & set(cb)) if ct[k] != cb[k]},
        "common_steps": len(set(st) & set(sb)),
        "step_diff": {k: [st[k], sb[k]] for k in sorted(set(st) & set(sb)) if st[k] != sb[k]},
        "steps_only_T": sorted(set(st) - set(sb)), "steps_only_B": sorted(set(sb) - set(st)),
        "T_nonpass_steps": {k: v for k, v in st.items() if v["verdict"] not in ("PASS", "RECORD")},
        "T_34": {k: v for k, v in st.items() if k.startswith("34-")},
        "T_step_verdicts_sha256": hashlib.sha256(json.dumps({k: v["verdict"] for k, v in st.items()}, sort_keys=True,
                                                            ensure_ascii=False).encode("utf-8")).hexdigest(),
        "T_case_verdicts": ct,
    }
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
for tag, r in res.items():
    print(tag, {k: r[k] for k in ("T_summary", "B_summary", "cases_only_T", "cases_only_B", "case_verdict_diff",
                                  "common_steps", "step_diff", "steps_only_B")}, len(r["steps_only_T"]))
