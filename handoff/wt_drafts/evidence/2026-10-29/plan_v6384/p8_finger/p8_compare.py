"""P8 비교: p8_enum.out.jsonl의 자기 정합 해(fits)에서 기준안 (B') 'w_f ≤ w_hi 가운데 w_f 최대, 같으면 m 최소'와
(C) 'm 최소, 같으면 w_f 최대', (D) '총 폭 m·w_f 최소'를 고르고 옛 반복 규칙(design 40 §3.7-A 5 재현) 결과와 대조. 출력 p8_compare.out.json"""
import json, collections
GRIDUM = 0.005
rows = collections.defaultdict(collections.Counter); detail = []
for l in open("p8_enum.out.jsonl", encoding="utf-8"):
    r = json.loads(l)
    for p in r.get("points", []):
        for dev, d in p["devices"].items():
            it, e = d["iter_rule"], d["enum"]
            fits = [f for f in e["fits"] if f[1] <= e["w_hi_um"] + GRIDUM / 2]
            c = rows[r["circuit"]]; c["device_points"] += 1; c["iter_" + it["status"]] += 1
            if not e["fits"]:
                c["enum_no_fit"] += 1
            if not fits:
                c["rule_none"] += 1
                detail.append([r["circuit"], p["point"], dev, it["status"], "no fit"]); continue
            B = max(fits, key=lambda f: (f[1], -f[0])); C = min(fits, key=lambda f: (f[0], -f[1])); D = min(fits, key=lambda f: (f[0] * f[1], f[0]))
            if it["status"] == "converged":
                last = it["seq"][-1]; key_it, m_it = it["final"], last[2]
                for name, pick in (("B", B), ("C", C), ("D", D)):
                    same = pick[2] == key_it and abs(pick[0] - m_it) <= max(1, int(0.001 * m_it))
                    c[name + ("_same" if same else "_diff")] += 1
                    if not same and name == "B":
                        detail.append([r["circuit"], p["point"], dev, "converged", "iter", [m_it, last[3], key_it], "B", B])
            else:
                c["resolved_by_B"] += 1
                detail.append([r["circuit"], p["point"], dev, it["status"], "B", B, "C", C, "D", D])
out = {"per_circuit": {k: dict(v) for k, v in rows.items()}, "detail": detail}
json.dump(out, open("p8_compare.out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in rows.items(): print(k, dict(v))
for d in detail: print(d)
