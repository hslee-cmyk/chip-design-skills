# sandbox-only measurement: contract 1 scenario from attempt-1 test, dump stack_id set + repaired_rows keys
import json, os, sys, importlib.util
def test_measure_c1(tmp_path, toy_lut):
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("b26pre_t1", os.path.join(here, "test_b26pre_existing_paths.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    import sizing_recipe
    w0, s = m._b26pre_sizing(toy_lut)
    pair = m._b26pre_pair(w0)
    path = m._b26pre_write_topology(
        tmp_path, "b26pre_lutless", [m._b26pre_net_entry(t) for t in pair],
        symmetry={"matching_pairs": [{"names": ["Ma", "Mb"], "matching_sensitivity": "offset", "current_forced": False}], "dispositions": []},
        device_roles={"Ma": {"gm_id_role": "", "L_role": ""}, "Mb": {"gm_id_role": "", "L_role": ""}},
        sizing_roles={"metrics": {"pair_area": {"type": "sum_area", "unit": "m^2", "devices": ["Ma", "Mb"]}},
                      "constraints": [{"metric": "pair_area", "op": "<=", "value": 2 * w0 * 0.5e-6 * 3}]})
    spec_d = {"known_sizing": {"Ma": s, "Mb": s}, "min_finger_w": 0.1e-6, "max_finger_w": 40e-6, "L_min": 0.1e-6,
              "gm_id_bounds": (2.0, 28.0), "stack_groups_override": {"pair_row": ["Ma", "Mb"]}}
    res = sizing_recipe.optimize_full_circuit_budget(path, spec_d)
    pr = res["pipeline_result"]
    out = {
        "stack_ids_list": [t.stack_id for t in pr["transistors"]],
        "names": [t.name for t in pr["transistors"]],
        "stack_id_set": sorted({t.stack_id for t in pr["transistors"]}),
        "repaired_rows_keys": sorted(pr["repaired_rows"]),
        "repaired_rows_members": {k: [t.name for t in v] for k, v in pr["repaired_rows"].items()},
        "audit_ok": res["audit_ok"],
        "has_growth_rounds": "growth_rounds" in pr,
        "c3c": [(c.name, c.ok) for c in pr["repaired_audit"].checks if c.name.startswith("3c.")],
        "seed": os.environ.get("PYTHONHASHSEED"),
    }
    with open(os.environ["B26PRE_MEASURE_OUT"], "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
