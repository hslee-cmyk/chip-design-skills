"""순서 3 base 표(T 복제본, base 게이트) 대 병합본 redteam 실행의 케이스·단계 판정 기계 대조.
사용: python cmp_rt.py <base 전체 log> <병합 전체 log> <base cases log> <병합 cases log> <출력 json>"""
import hashlib
import json
import sys


def table(path):
    cases, steps, summary = {}, {}, None
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("summary"):
            summary = {k: d[k] for k in ("cases", "steps")}
            continue
        cases[d["case"]] = d["verdict"]
        for s in d.get("steps", []):
            steps["%s::%s" % (d["case"], s["step"])] = {"verdict": s["verdict"], "exit": s.get("exit"),
                                                        "observed": s.get("observed")}
    return cases, steps, summary


bf, mf, bc, mc, out = sys.argv[1:6]
res = {}
for tag, (b, m) in {"full": (bf, mf), "cases": (bc, mc)}.items():
    cb, sb, smb = table(b)
    cm, sm, smm = table(m)
    res[tag] = {
        "base_log_sha256": hashlib.sha256(open(b, "rb").read()).hexdigest(),
        "merged_log_sha256": hashlib.sha256(open(m, "rb").read()).hexdigest(),
        "base_summary": smb, "merged_summary": smm,
        "case_set_equal": sorted(cb) == sorted(cm), "step_set_equal": sorted(sb) == sorted(sm),
        "case_verdict_diff": {k: [cb.get(k), cm.get(k)] for k in sorted(set(cb) | set(cm)) if cb.get(k) != cm.get(k)},
        "step_verdict_diff": {k: [sb.get(k, {}).get("verdict"), sm.get(k, {}).get("verdict")]
                              for k in sorted(set(sb) | set(sm))
                              if sb.get(k, {}).get("verdict") != sm.get(k, {}).get("verdict")},
        "merged_nonpass_steps": {k: v for k, v in sm.items() if v["verdict"] not in ("PASS", "RECORD")},
        "merged_34": {k: v for k, v in sm.items() if k.startswith("34-")},
        "merged_step_verdicts_sha256": hashlib.sha256(json.dumps({k: v["verdict"] for k, v in sm.items()},
                                                                 sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
    }
with open(out, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
