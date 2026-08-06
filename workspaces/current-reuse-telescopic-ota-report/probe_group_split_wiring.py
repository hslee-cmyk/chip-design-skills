import sys, os, json, tempfile
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")

from sizing_recipe import (
    build_toy_lut, size_transistor, SizingContext, run_topology_pipeline_with_finger_fixup,
    _blocked_euler_rows,
)

lut = build_toy_lut()

_l4c_m3a_netlist = [
    {"name": "M3a", "kind": "nmos", "source": "N3a4a", "drain": "Vom1", "gate": "Vbias3"},
    {"name": "M3b", "kind": "nmos", "source": "N3b4b", "drain": "Vop1", "gate": "Vbias3"},
    {"name": "M4a", "kind": "nmos", "source": "Vy", "drain": "N3a4a", "gate": "Vip"},
    {"name": "M4b", "kind": "nmos", "source": "Vy", "drain": "N3b4b", "gate": "Vim"},
    {"name": "M5", "kind": "nmos", "source": "gnd", "drain": "Vy", "gate": "Vbias4"},
    {"name": "M9b", "kind": "nmos", "source": "Vop1", "drain": "Vg15", "gate": "N14a14b"},
    {"name": "M10", "kind": "nmos", "source": "gnd", "drain": "Vop1", "gate": "Vbias4"},
    {"name": "M18b", "kind": "nmos", "source": "Vom1", "drain": "Vg25", "gate": "N24b23a"},
    {"name": "M19", "kind": "nmos", "source": "gnd", "drain": "Vom1", "gate": "Vbias4"},
    {"name": "M64", "kind": "nmos", "source": "N64_63", "drain": "Vbias3", "gate": "Vbias3"},
    {"name": "M63", "kind": "nmos", "source": "Vy", "drain": "N64_63", "gate": "Vbias3"},
]
_l4c_matching_pairs_meta = [
    {"names": ["M4a", "M4b"], "matching_sensitivity": "offset"},
    {"names": ["M3a", "M3b"], "matching_sensitivity": "ratio"},
    {"names": ["M10", "M19"], "matching_sensitivity": "ratio"},
    {"names": ["M9b", "M18b"], "matching_sensitivity": "ratio"},
]
_l4c_row = "m3a_row"
_l4c_L, _l4c_vds, _l4c_gm_id = 0.5e-6, 0.6, 12.0
_l4c_r = size_transistor(gm=50e-6, gm_id=_l4c_gm_id, L=_l4c_L, lut=lut, vds=_l4c_vds)
_l4c_gds = _l4c_r.gm / lut.gm_gds_ratio(_l4c_gm_id, _l4c_L, _l4c_vds, 0.0)
_l4c_names = [d["name"] for d in _l4c_m3a_netlist]
_l4c_overrides = {n: {"n_fingers": 1, "finger_w": _l4c_r.W, "w": _l4c_r.W, "stack_id": _l4c_row}
                   for n in _l4c_names}
_l4c_ctx = SizingContext(sized={
    n: {"ID": _l4c_r.ID, "W": _l4c_r.W, "L": _l4c_L, "gm": _l4c_r.gm, "gm_id": _l4c_gm_id,
        "gds": _l4c_gds, "kind": "nmos", "vds": _l4c_vds, "vs": 0.0}
    for n in _l4c_names
})
_l4c_metrics = {"group_area": {"type": "sum_area", "devices": _l4c_names}}
_l4c_baseline_area = len(_l4c_names) * _l4c_r.W * _l4c_L

with tempfile.TemporaryDirectory() as tmpdir:
    topo_path = os.path.join(tmpdir, "m3a_row.topology.json")
    with open(topo_path, "w", encoding="utf-8") as f:
        json.dump({
            "topology_name": "m3a_row_selftest",
            "schema_version": "2.0",
            "netlist": _l4c_m3a_netlist,
            "symmetry": {"matching_pairs": _l4c_matching_pairs_meta, "dispositions": []},
        }, f)

    constraints_b = [{"metric": "group_area", "op": "<=", "value": _l4c_baseline_area * 1.001}]

    # 1. cell_groups 없이
    result_b = run_topology_pipeline_with_finger_fixup(
        topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, constraints_b,
        gm_id_bounds=(2.0, 28.0))
    print("=== 케이스B (cell_groups 없음) ===")
    print("unresolved_row:", result_b["unresolved_row"])
    print("unresolved_reason:", result_b["unresolved_reason"])
    print("blocked euler rows (final):", _blocked_euler_rows(result_b["audit_row_split"]))
    print("fixup_rounds count:", len(result_b["fixup_rounds"]))
    print("group_splits:", json.dumps(result_b["group_splits"], indent=2, default=str))
    print("final stack_ids:", {t.name: t.stack_id for t in result_b["transistors"]})
    ar = result_b["audit_row_split"]
    print("audit.ok:", ar.ok)
    for c in ar.checks:
        print(" ", c.name, c.ok, c.detail[:80] if c.detail else "")

    print()
    print("=== 케이스C (cell_groups 명시 -- C-3 검증) ===")
    cell_groups = {"cellA": [_l4c_row, "other_row_not_present"]}
    result_c = run_topology_pipeline_with_finger_fixup(
        topo_path, _l4c_overrides, _l4c_ctx, {"nmos": lut}, _l4c_metrics, constraints_b,
        gm_id_bounds=(2.0, 28.0), cell_groups=cell_groups)
    print("unresolved_row:", result_c["unresolved_row"])
    print("group_splits:", json.dumps(result_c["group_splits"], indent=2, default=str))
    print("original cell_groups (should be untouched):", cell_groups)
    print("final audit_row_split keys:", list(result_c["audit_row_split"].keys()) if isinstance(result_c["audit_row_split"], dict) else "not dict")
    print("cellA euler checks:")
    for c in result_c["audit_row_split"]["cellA"].checks:
        if c.name.startswith("1. euler"):
            print("  ", c.name, c.ok)
    print("cellA row_widths:", result_c["box_shape"]["cellA"].row_widths)
