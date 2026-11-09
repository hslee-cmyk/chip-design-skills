"""P9 2차 순서 7 재사용 판정(auditor). 사용: python -P o7_reuse.py <복제본> <새 병합본 M2> <out.json>
(1) 재사용 조건: 1차 병합본 M1 b7765b0과 M2 사이 diff 경로 목록, 엔진·tests·workspaces·library·tools 트리 id 비교,
    M2의 stick_diagram.py blob = 1차 K 16a71fa의 blob, M2 첫 부모 = T2.
(2) 계약 8 레지스트리 대조: KCL 관련 행(§2 'KCL 엣지', §4 _metric_kcl_residual, §5 trace_vdd_to_gnd_branches,
    §6 kcl_series_union·_kcl_and_matching_edges·_kcl_terminal_sign)을 이름으로 찾아 줄 번호 표기(SD:/SR:/'NNNN행'/숫자 범위)를 뽑는다."""
import json, re, subprocess, sys
root, m2, out = sys.argv[1:4]
M1 = "b7765b047ac510b7150a3b99b102891e4083e970"; K1 = "16a71fade512c365885acf4c67e72faf670d91e2"
T2 = "6bf510b6c7bf427129224338cd64930f0343d5d0"
REG = "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
g = lambda *a: subprocess.run(["git", "-C", root] + list(a), capture_output=True, check=True).stdout.decode("utf-8").strip()
res = {"M2": g("rev-parse", m2), "M2_parents": g("log", "-1", "--format=%P", m2).split(), "M2_trailers": g("log", "-1", "--format=%(trailers)", m2)}
res["M2_first_parent_is_T2"] = res["M2_parents"][0] == T2 if res["M2_parents"] else False
res["diff_M1_M2"] = g("diff", "--name-only", M1, m2).splitlines()
trees = {}
for p in ("skills", "skills/analog-gmid-design/assets/tests", "workspaces", "tools", "skills/analog-gmid-design/assets/library"):
    trees[p] = {"M1": g("rev-parse", "%s:%s" % (M1, p)), "M2": g("rev-parse", "%s:%s" % (m2, p))}
    trees[p]["same"] = trees[p]["M1"] == trees[p]["M2"]
res["trees"] = trees
sd = "skills/analog-gmid-design/assets/stick_diagram.py"
res["sd_blob"] = {"K1": g("rev-parse", "%s:%s" % (K1, sd)), "M2": g("rev-parse", "%s:%s" % (m2, sd))}
res["sd_blob"]["same"] = res["sd_blob"]["K1"] == res["sd_blob"]["M2"]
res["reuse_ok"] = res["M2_first_parent_is_T2"] and res["sd_blob"]["same"] and trees["skills"]["same"] and trees["workspaces"]["same"] and trees["tools"]["same"] \
    and set(res["diff_M1_M2"]) <= {REG}
reg = subprocess.run(["git", "-C", root, "show", "%s:%s" % (m2, REG)], capture_output=True, check=True).stdout.decode("utf-8").splitlines()
keys = {"s2_kcl_edge": "| KCL 엣지 |", "s4_metric_kcl_residual": "| `_metric_kcl_residual` |", "s5_trace_vdd": "| `trace_vdd_to_gnd_branches` |",
        "s6_kcl_series_union": "| `kcl_series_union` |", "s6_kcl_and_matching_edges": "| `_kcl_and_matching_edges` |", "s6_kcl_terminal_sign": "| `_kcl_terminal_sign` |"}
LN = re.compile(r"(?:SD|SR):\d+(?:-\d+)?|\d{3,5}행|\(\d{3,5}(?:[-,·]\d{3,5})*\)")
rows = {}
for k, pref in keys.items():
    hit = [(i + 1, l) for i, l in enumerate(reg) if l.startswith(pref)]
    rows[k] = [{"line": n, "line_number_refs": LN.findall(l), "text": l,
                "mentions_sign_convention": "부호 규약" in l, "mentions_rail_name_set": "레일 이름 집합" in l} for n, l in hit]
res["registry_rows"] = rows
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("reuse_ok", res["reuse_ok"], "diff", res["diff_M1_M2"], "sd_same", res["sd_blob"]["same"], {p: t["same"] for p, t in trees.items()})
for k, v in rows.items():
    for r in v:
        print(k, r["line"], "refs", r["line_number_refs"], "sign", r["mentions_sign_convention"], "rail", r["mentions_rail_name_set"])
