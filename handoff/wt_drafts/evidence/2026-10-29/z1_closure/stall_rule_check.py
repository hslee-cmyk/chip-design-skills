"""멈춤 규칙 후보를 이미 잰 닫기 이력에 사후 적용(oracle 새 실행 없음). 결과 append(stall_rule_check.jsonl).
R1(앞 보고 제안): 옮긴 실패 metric 모두 |s_k − s_{k−1}| ≤ 분해능 → 정지.
R2(새 상수 없음): 옮긴 실패 metric 모두 |s_k − s_{k−1}| < |s_k| (한 걸음 진전이 남은 부족분보다 작음) → 정지.
R4(새 상수 없음): 옮긴 실패 metric 모두 |s_k − s_{k−1}| ≤ 분해능 이면서 |Δ_k − Δ_{k−1}| > 분해능
    (문턱은 분해능보다 크게 옮겼는데 oracle은 분해능만큼도 안 움직임 = oracle 둔감) → 정지.
판정: 실제로 닫힌 이력에서 규칙이 먼저 걸리면 '거짓 정지', 도달 불가 이력에서 걸린 걸음 = '정지 시점'.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stall_rule_check.jsonl")


def hists():
    for l in open(os.path.join(HERE, "results.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if r["kind"] == "closure" and r["aim"] in ("mid", "secant"):
            yield (r["case"], r["aim"], r["res_rel"], r["status"],
                   [[h["s_rel"]] for h in r["hist"]], [[h["delta"]] for h in r["hist"]])
    for l in open(os.path.join(HERE, "multi.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if r["case"].endswith("_c2"):
            continue  # 수정 전 코드 기록(무효)
        hs = [h for h in r["hist"] if "s" in h]
        yield r["case"], r["method"], r["res_rel"], r["status"], [h["s"] for h in hs], [h["D"] for h in hs]


def fire(rule, s, ps, D, pD, res):
    idx = [i for i in range(len(s)) if s[i] < 0 and D[i] != pD[i]]
    if not idx:
        return False
    if rule == "R1":
        return all(abs(s[i] - ps[i]) <= res for i in idx)
    if rule == "R4":
        return all(abs(s[i] - ps[i]) <= res and abs(D[i] - pD[i]) > res for i in idx)
    return all(abs(s[i] - ps[i]) < abs(s[i]) for i in idx)


seen = set()
for case, meth, res, status, S, D in hists():
    key = (case, meth, res, len(S))
    if key in seen:
        continue
    seen.add(key)
    rec = {"case": case, "method": meth, "res": res, "status": status, "runs": len(S)}
    for rule in ("R1", "R2", "R4"):
        k_fire = next((k for k in range(1, len(S)) if fire(rule, S[k], S[k - 1], D[k], D[k - 1], res)), None)
        rec[rule] = k_fire
        rec[rule + "_false"] = status == "closed" and k_fire is not None and k_fire < len(S) - 1
    with open(OUT, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec) + "\n")
    if rec["R1_false"] or rec["R4_false"] or status not in ("closed",):
        print(rec)
