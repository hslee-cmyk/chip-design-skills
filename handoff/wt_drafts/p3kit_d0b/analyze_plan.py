"""D0b 작성 전 실측(측정 전용, 역할 산출물 아님): D0a `plan` 시제품 출력 JSON을 D0b 계약 항목별로 요약한다.

    python -B analyze_plan.py <plan.json> <out.json> [<비교할 plan.json>]

요약: 판정 목록 길이, 규칙 분포, MOD별 배정 수, MOD7(N3.10 MOD7 파일) 배정 중 그 파일 밖 단위(D0b 계약 'SD 밖 MOD7 0'),
upward 간선의 (원천 MOD, 대상 MOD) 분포와 원천·대상 단위, cycles, unassigned, import_time_high.
세 번째 인자가 있으면 (단위 키 -> mod) 사상 비교(파일 부분·rule 제외 -- D0a 계약 8 (b)와 같은 비교).
MOD 번호는 파일 이름이 아니라 출력의 `order`에 나온 순서가 아니라 N3.10 표에서 읽어야 하므로, 호출자가 MOD 파일→번호를
환경 변수 없이 계산할 수 있게 `--n310` 대신 이 스크립트 안의 표를 쓰지 않는다 -- upward 문자열의 두 단위를 assignment에서 찾아 MOD 파일로 센다.
"""
import collections
import json
import sys

src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8"))
A = d["assignment"]
res = {"verdict": d["verdict"]}
res["lens"] = {k: len(d[k]) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high", "absent_split")}
res["n_assigned"] = len(A)
res["rules"] = dict(collections.Counter(v["rule"] for v in A.values()))
res["per_mod"] = dict(sorted(collections.Counter(v["mod"] for v in A.values()).items()))
res["mod7_outside_sd"] = sorted(u for u, v in A.items() if v["mod"] == "stick_diagram.py" and not u.startswith("stick_diagram.py::"))
pairs = collections.Counter()
edges = []
for e in d["upward"]:
    a, b = e.split(" -> ")
    pairs["%s -> %s" % (A[a]["mod"], A[b]["mod"])] += 1
    edges.append({"from": a, "from_mod": A[a]["mod"], "from_rule": A[a]["rule"], "to": b, "to_mod": A[b]["mod"], "to_rule": A[b]["rule"]})
res["upward_mod_pairs"] = dict(pairs.most_common())
res["upward_edges"] = edges
res["upward_sources"] = dict(collections.Counter(e["from"] for e in edges).most_common())
res["upward_targets"] = dict(collections.Counter(e["to"] for e in edges).most_common())
res["cycles"] = d["cycles"]
res["unassigned"] = d["unassigned"]
res["conflicts"] = d["conflicts"]
res["import_time_high"] = d["import_time_high"]
res["reg_mismatch_rules"] = dict(collections.Counter(m["rule"] for m in d["reg_mismatch"]))
res["reg_mismatch"] = d["reg_mismatch"]
if len(sys.argv) > 3:
    e = json.load(open(sys.argv[3], encoding="utf-8"))["assignment"]
    k1 = {u.split("::", 1)[1]: v["mod"] for u, v in A.items()}
    k2 = {u.split("::", 1)[1]: v["mod"] for u, v in e.items()}
    res["compare"] = {"only_here": sorted(set(k1) - set(k2)), "only_there": sorted(set(k2) - set(k1)),
                      "mod_diff": sorted(k for k in set(k1) & set(k2) if k1[k] != k2[k])}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("verdict", "lens", "n_assigned", "rules", "per_mod", "upward_mod_pairs")}, ensure_ascii=False))
print("mod7_outside_sd", res["mod7_outside_sd"])
if "compare" in res:
    print("compare", {k: len(v) for k, v in res["compare"].items()})
