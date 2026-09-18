import json, os, collections
import analysis as A, engine as E
fn = os.path.join(E.SP, "results3_dc.jsonl"); open(fn, "w").close()
SPEC_CIRCUITS = {"two_stage_ota", "current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier"}  # run_harness.SPECS keys
for c in E.circuits():
    out = dict(circuit=c["name"])
    # GB0
    g = {}
    g["supply_nets_declared"] = c["supply_nets_declared"]; g["rails"] = c["rails"]
    g["hidden_rail_candidates_unpruned"] = A.hidden_rails(c)
    g["hidden_rails_if_supply_nets_minus_last"] = A.hidden_rails(c, c["rails"][:-1]) if len(c["rails"]) >= 3 else None
    # name-set interpretation (transition): which of {vdd, gnd, vss} exist
    nets = E.all_nets(c)
    g["nameset_rails"] = sorted(n for n in nets if n.lower() in ("vdd", "gnd", "vss", "avdd", "avss", "agnd", "0"))
    g["has_sizing_spec(SPECS)"] = c["name"] in SPEC_CIRCUITS
    sr = c["sizing_roles"]
    g["constraints_key"] = isinstance(sr, dict) and "constraints" in sr
    cons = (sr or {}).get("constraints") if isinstance(sr, dict) else None
    g["n_constraints"] = len(cons) if cons else 0
    g["constraint_sources"] = sorted({x.get("source") for x in (cons or [])}, key=str)
    g["constraints_missing_source"] = [x.get("metric") for x in (cons or []) if not x.get("source")]
    g["constraints_paper_source"] = [x.get("metric") for x in (cons or []) if "paper" in str(x.get("source")).lower()]
    g["value_from_spec_oldnames"] = [x.get("value_from_spec") for x in (cons or []) if x.get("value_from_spec")]
    g["paper_target_spec_present"] = "_paper_target_spec" in c["raw"]
    out["gb0"] = g
    # DEC-64
    out["gvgs"] = A.gvgs(c)
    # DEC-71
    col = A.columns(c)
    col.pop("col_dev_sets", None); col["covered"] = sorted(col["covered"])
    out["columns"] = col
    # unpruned variant
    Gu, _ = A.dc_graph(c, prune=False)
    out["n_branch_nodes_unpruned"] = sum(1 for n in Gu.nodes if n not in c["rails"] and Gu.degree(n) >= 3)
    with open(fn, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, default=str) + "\n")
    print(c["name"], "done", flush=True)
