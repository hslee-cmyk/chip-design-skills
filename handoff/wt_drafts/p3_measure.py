"""Phase 3 (30-module-split) 준비 실측 -- 읽기 전용. 결과를 p3_measure.json에 쓴다."""
import ast, json, os, re, subprocess, sys
from collections import defaultdict, Counter

ROOT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
A = os.path.join(ROOT, "skills", "analog-gmid-design", "assets")
REG = os.path.join(ROOT, "docs", "03-analysis", "gain-budget-gmid-sizing.function-registry.md")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p3_measure.json")

MODS = {"gmid_lut": 1, "topology_authoring": 2, "circuit_state_graph": 3, "gmid_sizing_engine": 4,
        "circuit_metrics": 5, "theta_search": 6, "stick_diagram": 7, "sizing_layout_convergence": 8,
        "instance_report_builder": 9, "gmid_design_pipeline": 10}
SRC = ["sizing_recipe", "stick_diagram", "topology_library", "design_report", "audit_current_forced",
       "topology_to_markdown", "sky130_lut_sweep"]

res = {}
# 1. top-level defs
defs = {}
for m in SRC:
    p = os.path.join(A, m + ".py")
    tree = ast.parse(open(p, "rb").read().decode("utf-8"))
    names = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append((n.name, n.lineno, type(n).__name__))
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            tgts = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in tgts:
                if isinstance(t, ast.Name):
                    names.append((t.id, n.lineno, "Assign"))
    defs[m] = {"tree": tree, "names": names}
res["toplevel_counts"] = {m: Counter(k for _, _, k in d["names"]) for m, d in defs.items()}

# 2. registry rows
reg_lines = open(REG, "rb").read().decode("utf-8").splitlines()
rows = []
sec = sub = None
dest_col = None
for i, ln in enumerate(reg_lines, 1):
    if ln.startswith("## "):
        sec = ln[3:].split(" ")[0]
    elif ln.startswith("### "):
        sub = ln[4:].split(" ")[0]
    elif ln.startswith("| 함수"):
        hdr = [c.strip() for c in ln.strip("|").split("|")]
        dest_col = hdr.index("이관 목적지")
        proc_col = hdr.index("처리") if "처리" in hdr else None
    elif ln.startswith("| `") and dest_col is not None and sec not in ("1.", "2."):
        cells = [c.strip() for c in ln.strip("|").split("|")]
        nm = re.findall(r"`([^`]+)`", cells[0])
        dest = cells[dest_col] if len(cells) > dest_col else ""
        mod = None
        for k in MODS:
            if k in dest:
                mod = k; break
        rows.append({"line": i, "grade_sec": sec, "src": sub, "names": nm, "dest": dest,
                     "mod": mod, "proc": cells[proc_col] if proc_col is not None and len(cells) > proc_col else None})
res["registry_rows"] = len(rows)
res["registry_dest_mod_counts"] = Counter(r["mod"] or "UNMAPPED" for r in rows)
res["registry_unmapped"] = [(r["line"], r["names"], r["dest"][:80]) for r in rows if not r["mod"]]

# name -> dest
name2 = {}
for r in rows:
    for n in r["names"]:
        base = n.strip().split(".")[0].strip()
        base = base.replace("└", "").strip()
        name2.setdefault(base, []).append((r["line"], r["mod"], r["src"]))

# 3. coverage: top-level defs (func/class) of engine modules without registry row
cov = {}
for m in ["sizing_recipe", "stick_diagram", "topology_library", "design_report", "audit_current_forced"]:
    fn = [(n, l) for n, l, k in defs[m]["names"] if k != "Assign"]
    missing = [(n, l) for n, l in fn if n not in name2]
    cov[m] = {"defs": len(fn), "missing_in_registry": len(missing), "missing_sample": missing[:400]}
res["coverage"] = cov
# names with multiple/conflicting destinations
res["multi_dest"] = {k: v for k, v in name2.items() if len({x[1] for x in v}) > 1}

# 4. plan N3.10 representative targets vs registry dest
plan_rep = {
 1: ["GmIdLUT", "SemiEmpiricalGmIdLUT", "_multilinear_interp", "_solve_vgs", "lut_conditions_from_npz"],
 2: ["load_topology", "validate_metric_units", "validate_no_legacy_vs_key", "require_declared_spec_source", "validate_theta_declaration_order"],
 3: ["is_diode_connected", "true_current_mirror_groups", "l_sharing_classes", "l_class_owners", "vgs_alias_map", "_kcl_and_matching_edges", "propagate_topology_forced_currents", "spec_fingerprint"],
 4: ["size_transistor", "feasible_gm_ids", "measure_L_knee", "solve_diode_connected_vds", "solve_stacked_diode_pair", "apply_theta_feed"],
 5: ["compute_metric", "_METRICS_REGISTRY", "build_ac_network", "_full_circuit_response", "estimate_mismatch_sigma"],
 6: ["_build_theta_evaluator", "optimize_full_circuit_budget", "search_stage_budget_L_warm_start", "presolve_warm_start", "_optimize_theta_slsqp", "repair_infeasible_baseline"],
 8: ["run_topology_pipeline_with_finger_fixup", "revalidate_finger_override", "resolve_stack_layout"],
 9: ["save_instance_json"],
}
inv = {v: k for k, v in MODS.items()}
where = {}
for m in SRC:
    for n, l, k in defs[m]["names"]:
        where.setdefault(n, []).append("%s:%d" % (m, l))
rep = []
for mid, names in plan_rep.items():
    for n in names:
        rd = name2.get(n)
        rep.append({"plan_mod": mid, "name": n, "where": where.get(n), "registry": rd,
                    "agree": bool(rd) and all(x[1] == inv[mid] for x in rd)})
res["plan_rep_vs_registry"] = rep

# 5. reference graph between top-level defs under registry assignment (sizing_recipe + stick_diagram + topology_library + design_report)
assign = {}
for m in ["sizing_recipe", "stick_diagram", "topology_library", "design_report"]:
    for n, l, k in defs[m]["names"]:
        rd = name2.get(n)
        tgt = rd[0][1] if rd and rd[0][1] else None
        assign[(m, n)] = tgt
# module-level name tables
top_names = {m: {n for n, _, _ in defs[m]["names"]} for m in defs}
# which modules import which (current)
cur_imports = {}
for m in SRC:
    s = set()
    for n in ast.walk(defs[m]["tree"]):
        if isinstance(n, ast.Import):
            s |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            s.add(n.module.split(".")[0])
    cur_imports[m] = sorted(x for x in s if x in SRC or x == "run_harness")
res["current_intra_imports"] = cur_imports

edges = Counter()
viol = []
for m in ["sizing_recipe", "stick_diagram", "topology_library", "design_report"]:
    for node in defs[m]["tree"].body:
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            continue
        src_mod = assign.get((m, node.name))
        if not src_mod:
            continue
        refs = {x.id for x in ast.walk(node) if isinstance(x, ast.Name)} | \
               {x.attr for x in ast.walk(node) if isinstance(x, ast.Attribute)}
        for r in refs:
            if r == node.name:
                continue
            # same-file reference, or cross-module attr reference by name
            if r in top_names[m]:
                cands = [(m, r)]
            else:
                cands = [(mm, r) for mm in ["sizing_recipe", "stick_diagram", "topology_library", "design_report"] if r in top_names[mm] and mm in cur_imports[m]]
            for c in cands:
                t = assign.get(c)
                if t and t != src_mod:
                    edges[(src_mod, t)] += 1
                    if MODS[t] > MODS[src_mod]:
                        viol.append({"from": "%s.%s" % (m, node.name), "from_mod": src_mod, "to": "%s.%s" % c, "to_mod": t})
res["mod_edges"] = {"%s->%s" % k: v for k, v in sorted(edges.items())}
res["upward_violations_count"] = len(viol)
res["upward_violations_by_pair"] = Counter("%s->%s" % (v["from_mod"], v["to_mod"]) for v in viol)
res["upward_violations_sample"] = viol[:300]
res["unassigned_toplevel"] = {m: [n for (mm, n), t in assign.items() if mm == m and t is None] for m in ["sizing_recipe", "stick_diagram", "topology_library", "design_report"]}

json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("wrote", OUT)
