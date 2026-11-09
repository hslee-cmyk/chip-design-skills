"""초안 할당(계획 N3.10 우선 + 레지스트리 목적지 열 보정)으로 계산한 모듈 간 참조 그래프 -- 읽기 전용 실측."""
import ast, json, os, re, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
A = os.path.join(ROOT, "skills", "analog-gmid-design", "assets")
REG = os.path.join(ROOT, "docs", "03-analysis", "gain-budget-gmid-sizing.function-registry.md")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p3_assign.json")
MODS = {"gmid_lut": 1, "topology_authoring": 2, "circuit_state_graph": 3, "gmid_sizing_engine": 4,
        "circuit_metrics": 5, "theta_search": 6, "stick_diagram": 7, "sizing_layout_convergence": 8,
        "instance_report_builder": 9, "gmid_design_pipeline": 10}
SRC = ["sizing_recipe", "stick_diagram", "topology_library", "design_report"]
trees = {m: ast.parse(open(os.path.join(A, m + ".py"), "rb").read().decode("utf-8")) for m in SRC}

def tops(t):
    out = {}
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            out[n.name] = n
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for tg in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if isinstance(tg, ast.Name):
                    out[tg.id] = n
    return out
top = {m: tops(t) for m, t in trees.items()}

# registry destination (first MOD token, 'optimizer' -> theta_search, ditto -> previous row)
reg = {}
prev = None
hdr_dest = None
for ln in open(REG, "rb").read().decode("utf-8").splitlines():
    if ln.startswith("| 함수"):
        hdr = [c.strip() for c in ln.strip("|").split("|")]
        hdr_dest = hdr.index("이관 목적지")
        continue
    if not ln.startswith("| `") or hdr_dest is None:
        continue
    cells = [c.strip() for c in ln.strip("|").split("|")]
    dest = cells[hdr_dest]
    if dest.startswith("〃"):
        mod = prev
    else:
        pos = sorted((dest.find(k), k) for k in MODS if k in dest)
        mod = pos[0][1] if pos else ("theta_search" if "optimizer" in dest else None)
    prev = mod
    for nm in re.findall(r"`([^`]+)`", cells[0]):
        nm = nm.replace("└", "").strip().split(".")[0]
        if "/" in nm:
            for x in nm.split("/"):
                reg.setdefault(x.strip(), mod)
        else:
            reg.setdefault(nm, mod)

PLAN = {
 "gmid_lut": ["GmIdLUT", "SemiEmpiricalGmIdLUT", "_multilinear_interp", "_multilinear_interp_point_multi", "lut_conditions_from_npz"],
 "topology_authoring": ["validate_metric_units", "validate_no_legacy_vs_key", "require_declared_spec_source", "validate_theta_declaration_order", "load_topology"],
 "circuit_state_graph": ["is_diode_connected", "true_current_mirror_groups", "l_sharing_classes", "l_class_owners", "vgs_alias_map", "_kcl_and_matching_edges", "propagate_topology_forced_currents", "spec_fingerprint"],
 "gmid_sizing_engine": ["size_transistor", "feasible_gm_ids", "measure_L_knee", "solve_diode_connected_vds", "solve_stacked_diode_pair", "apply_theta_feed"],
 "circuit_metrics": ["compute_metric", "_METRICS_REGISTRY", "build_ac_network", "_full_circuit_response", "estimate_mismatch_sigma"],
 "theta_search": ["_build_theta_evaluator", "search_stage_budget_L_warm_start", "presolve_warm_start", "_optimize_theta_slsqp", "repair_infeasible_baseline"],
 "sizing_layout_convergence": ["run_topology_pipeline_with_finger_fixup", "revalidate_finger_override", "resolve_stack_layout", "optimize_full_circuit_budget"],
}
override = {n: m for m, ns in PLAN.items() for n in ns}
assign = {}
src_default = {"sizing_recipe": None, "stick_diagram": "stick_diagram", "topology_library": "gmid_sizing_engine", "design_report": "instance_report_builder"}
for m in SRC:
    for n in top[m]:
        a = override.get(n) or reg.get(n)
        if a is None:
            if n.startswith("_metric_"):
                a = "circuit_metrics"
            else:
                a = src_default[m]
        if a is None:
            a = "UNASSIGNED"
        assign[(m, n)] = a
# imported cross-module names
imported = defaultdict(set)
for m, t in trees.items():
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom) and n.module in SRC:
            for a_ in n.names:
                imported[m].add((n.module, a_.name))
edges = Counter(); viol = []
for m in SRC:
    imp = {nm: mod for mod, nm in imported[m]}
    for n, node in top[m].items():
        s = assign[(m, n)]
        if s == "UNASSIGNED":
            continue
        for r in {x.id for x in ast.walk(node) if isinstance(x, ast.Name)} - {n}:
            if r in top[m]:
                c = (m, r)
            elif r in imp:
                c = (imp[r], r)
            else:
                continue
            t_ = assign.get(c)
            if not t_ or t_ == "UNASSIGNED" or t_ == s:
                continue
            edges[(s, t_)] += 1
            if MODS[t_] > MODS[s]:
                viol.append(("%s.%s" % (m, n), s, "%s.%s" % c, t_))
res = {"assign_counts": Counter(assign.values()), "edges": {"%s->%s" % k: v for k, v in sorted(edges.items())},
       "upward": len(viol), "upward_by_pair": Counter("%s->%s" % (v[1], v[3]) for v in viol),
       "upward_by_from": Counter(v[0] for v in viol).most_common(40), "upward_list": viol,
       "unassigned": [n for (m, n), a in assign.items() if a == "UNASSIGNED"]}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
for k in ["assign_counts", "edges", "upward", "upward_by_pair", "upward_by_from"]:
    print(k, res[k])
print("unassigned", len(res["unassigned"]), res["unassigned"][:80])
