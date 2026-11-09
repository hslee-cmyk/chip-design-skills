"""주표 20 id(브리프 2.3 (나) 표 그대로 auditor가 적음) -> JSON. p35_items.B26PRE_20과 대조 출력."""
import json, sys
SR, SD = "sizing_recipe:", "stick_diagram:"
G = "run_matching_safety_with_finger_growth"
IDS = [SR + s for s in (
    "_fixup_euler_blocked_rows:stmt_delete:body[5].body[13]",
    "_fixup_euler_blocked_rows:stmt_delete:body[5].body[14]",
    "_fixup_euler_blocked_rows:stmt_delete:body[5].body[16]",
    "optimize_full_circuit_budget._evaluate_row_split:stmt_delete:body[5].body[3].orelse[0]",
    "optimize_full_circuit_budget._evaluate_row_split:stmt_delete:body[5].body[3].orelse[1]",
    "optimize_full_circuit_budget:stmt_delete:body[12].body[3].body[5].body[3].orelse[0]",
    "optimize_full_circuit_budget:stmt_delete:body[12].body[3].body[5].body[3].orelse[1]",
    "resolve_stack_layout:stmt_delete:body[5]",
    G + ":stmt_delete:body[10].body[1]", G + ":stmt_delete:body[10].body[2]",
    G + ":stmt_delete:body[11]", G + ":stmt_delete:body[12]",
    G + ":stmt_delete:body[13]", G + ":stmt_delete:body[14]")] + [SD + s for s in (
    "propose_device_roles_gap_fill:stmt_delete:body[49]",
    "propose_vertical_stack_id_gap_fill:stmt_delete:body[2]",
    "run_full_circuit_audit:stmt_delete:body[16]",
    "run_full_circuit_audit:stmt_delete:body[17]",
    "find_differential_pair_candidates:const+:body[8].body[3].body[1].body[0].iter.args[0].right",
    "find_differential_pair_candidates:arith:body[8].body[3].body[1].body[0].iter.args[0]")]
assert len(IDS) == 20 and len(set(IDS)) == 20
json.dump(IDS, open(sys.argv[1], "w", encoding="utf-8"), indent=1)
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/post35_kit")
import p35_items
print("same_as_p35_items_B26PRE_20", IDS == p35_items.B26PRE_20)
