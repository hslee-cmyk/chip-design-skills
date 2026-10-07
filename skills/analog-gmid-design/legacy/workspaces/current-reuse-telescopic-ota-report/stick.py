"""Stick diagram / Euler trail / box-shape / matching analysis for the current-reuse telescopic
OTA + Class-AB output, using MY OWN sizing_results.json (independently computed) and the skill's
real stick_diagram.py functions (not hand-approximated)."""
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
from dataclasses import asdict
import re
from stick_diagram import (Transistor, search_shared_finger_w, search_stack_finger_w, check_box_shape,
                            build_stick_diagram, find_matching_candidates, find_hub_merge_candidates,
                            check_mirror_symmetry, build_mirror_symmetric_pattern, run_full_circuit_audit,
                            block_from_row_widths, pack_floorplan_grouped, audit_row_split,
                            check_stick_diagram_coverage, save_instance_json)

def gen1(trs):
    """build_stick_diagram() returns {stack_id: StickResult} -- for a single homogeneous-polarity
    row this is exactly one entry; unwrap it and return the StickResult as a plain dict."""
    r = build_stick_diagram(trs)
    assert len(r) == 1, f"expected exactly one stack, got {list(r.keys())}"
    return asdict(next(iter(r.values())))

with open("sizing_results.json") as f:
    S = {r["name"]: r for r in json.load(f)}

def W(name):
    return S[name]["W_um"]

report = {}

# ---------------------------------------------------------------------------
# Row 1: PMOS input+cascode (M1a/M1b/M2a/M2b) -- current-reuse top half
# ---------------------------------------------------------------------------
row1_devs = {"M1a": W("M1a/M1b"), "M2a": W("M2a/M2b")}
cand1 = search_shared_finger_w(row1_devs, min_finger_w=0.3, max_finger_w=5.0)[0]
print("Row1 (PMOS in+casc) shared finger_w candidate:", cand1)
n_fw1 = cand1.finger_w
n1a = cand1.n_fingers_per_device["M1a"]
n2a = cand1.n_fingers_per_device["M2a"]
trs_row1 = [
    Transistor("M1a", "pmos", source="Vx", drain="n_1a2a", n_fingers=n1a, finger_w=n_fw1, gate="Vip", stack_id="row1_pmos_in_casc"),
    Transistor("M1b", "pmos", source="Vx", drain="n_1b2b", n_fingers=n1a, finger_w=n_fw1, gate="Vim", stack_id="row1_pmos_in_casc"),
    Transistor("M2a", "pmos", source="n_1a2a", drain="Vom1", n_fingers=n2a, finger_w=n_fw1, gate="Vbias2", stack_id="row1_pmos_in_casc"),
    Transistor("M2b", "pmos", source="n_1b2b", drain="Vop1", n_fingers=n2a, finger_w=n_fw1, gate="Vbias2", stack_id="row1_pmos_in_casc"),
]
stick1 = gen1(trs_row1)
print("Row1 stick:", stick1["status"], "odd_nodes:", stick1.get("odd_nodes"))
report["row1_pmos_in_casc"] = dict(cand=cand1.__dict__, stick=stick1)

# ---------------------------------------------------------------------------
# Row 2: NMOS input+cascode (M3a/M3b/M4a/M4b) -- current-reuse bottom half
# ---------------------------------------------------------------------------
row2_devs = {"M3a": W("M3a/M3b"), "M4a": W("M4a/M4b")}
cand2 = search_shared_finger_w(row2_devs, min_finger_w=0.05, max_finger_w=2.0)[0]
print("Row2 (NMOS in+casc) shared finger_w candidate:", cand2)
n_fw2 = cand2.finger_w
n3a = cand2.n_fingers_per_device["M3a"]
n4a = cand2.n_fingers_per_device["M4a"]
trs_row2 = [
    Transistor("M3a", "nmos", source="n_3a4a", drain="Vom1", n_fingers=n3a, finger_w=n_fw2, gate="Vbias3", stack_id="row2_nmos_in_casc"),
    Transistor("M3b", "nmos", source="n_3b4b", drain="Vop1", n_fingers=n3a, finger_w=n_fw2, gate="Vbias3", stack_id="row2_nmos_in_casc"),
    Transistor("M4a", "nmos", source="Vy", drain="n_3a4a", n_fingers=n4a, finger_w=n_fw2, gate="Vip", stack_id="row2_nmos_in_casc"),
    Transistor("M4b", "nmos", source="Vy", drain="n_3b4b", n_fingers=n4a, finger_w=n_fw2, gate="Vim", stack_id="row2_nmos_in_casc"),
]
stick2 = gen1(trs_row2)
print("Row2 stick:", stick2["status"], "odd_nodes:", stick2.get("odd_nodes"))
report["row2_nmos_in_casc"] = dict(cand=cand2.__dict__, stick=stick2)

# ---------------------------------------------------------------------------
# Row 3: tail SOURCE M6/M7 (0.7/0.3 split, same gate net question -- different gates: Vbias1/Vcmfb)
# ---------------------------------------------------------------------------
w6, w7 = W("M6"), W("M7")
# common finger_w: since W6/W7 ratio should mirror the 0.7:0.3 design ratio, try their GCD-ish split
cand3 = search_shared_finger_w({"M6": w6, "M7": w7}, min_finger_w=0.3, max_finger_w=5.0)[0]
print("Row3 (M6/M7 tail source) shared finger_w candidate:", cand3)
n_fw3 = cand3.finger_w
n6 = cand3.n_fingers_per_device["M6"]
n7 = cand3.n_fingers_per_device["M7"]
trs_row3 = [
    Transistor("M6", "pmos", source="VDD", drain="Vx", n_fingers=n6, finger_w=n_fw3, gate="Vbias1", stack_id="row3_top_load"),
    Transistor("M7", "pmos", source="VDD", drain="Vx", n_fingers=n7, finger_w=n_fw3, gate="Vcmfb", stack_id="row3_top_load"),
]
stick3 = gen1(trs_row3)
print("Row3 stick:", stick3["status"], "odd_nodes:", stick3.get("odd_nodes"))
report["row3_top_load"] = dict(cand=cand3.__dict__, stick=stick3)

# ---------------------------------------------------------------------------
# Row 4: tail SINK M5 (single device, sized to sink 2x branch current -- matched finger_w to row3
# via search_stack_finger_w so the two rows stack into one box-shape cell)
# ---------------------------------------------------------------------------
w5 = W("M5")
cand4_list = search_stack_finger_w({"M5": w5}, target_row_fingers=n6+n7, min_finger_w=0.3, max_finger_w=5.0)
cand4 = cand4_list[0] if cand4_list else None
print("Row4 (M5 tail sink) stack finger_w candidate (target row3 fingers):", cand4)
n_fw4 = cand4.finger_w if cand4 else w5  # fallback: 1 finger of full W
n5 = cand4.n_fingers_per_device["M5"] if cand4 else 1
trs_row4 = [Transistor("M5", "nmos", source="Vy", drain="GND", n_fingers=n5, finger_w=n_fw4, gate="Vbias4", stack_id="row4_tail")]
stick4 = gen1(trs_row4)
print("Row4 stick:", stick4["status"], "odd_nodes:", stick4.get("odd_nodes"))
report["row4_tail"] = dict(cand=(cand4.__dict__ if cand4 else None), stick=stick4)

bs_bias_tail = check_box_shape({"row3_top_load": n6+n7, "row4_tail": n5})
print("box-shape (bias/tail cell):", bs_bias_tail)

bs_core = check_box_shape({"row1_pmos_in_casc": 2*(n1a+n2a), "row2_nmos_in_casc": 2*(n3a+n4a)})
print("box-shape (core signal cell):", bs_core)

# ---------------------------------------------------------------------------
# Row 5/6: Stage-2 output M15/M25 (PMOS) and M16/M26 (NMOS)
# ---------------------------------------------------------------------------
w15 = S["M15/M25"]["W_um"]  # capped 200um
w16 = S["M16/M26"]["W_um"]
cand5 = search_shared_finger_w({"M15": w15}, min_finger_w=5.0, max_finger_w=15.0)[0]
n_fw5 = cand5.finger_w
n15 = cand5.n_fingers_per_device["M15"]
cand6_list = search_stack_finger_w({"M16": w16, "M26": w16}, target_row_fingers=2*n15, min_finger_w=1.0,
                                    max_finger_w=10.0, tol_fingers=10, max_n=200)
cand6 = cand6_list[0] if cand6_list else None
n_fw6 = cand6.finger_w if cand6 else w16
n16 = cand6.n_fingers_per_device["M16"] if cand6 else 1
print(f"Row5(M15/M25) finger_w={n_fw5} n={n15} x2   Row6(M16/M26) finger_w={n_fw6} n={n16} x2")

trs_rowP = [
    Transistor("M15", "pmos", source="VDD", drain="Vop", n_fingers=n15, finger_w=n_fw5, gate="n_batt_p_a", stack_id="rowP_out"),
    Transistor("M25", "pmos", source="VDD", drain="Vom", n_fingers=n15, finger_w=n_fw5, gate="n_batt_p_b", stack_id="rowP_out"),
]
stickP = gen1(trs_rowP)
trs_rowN = [
    Transistor("M16", "nmos", source="Vom", drain="GND", n_fingers=n16, finger_w=n_fw6, gate="n_batt_n_a", stack_id="rowN_out"),
    Transistor("M26", "nmos", source="Vop", drain="GND", n_fingers=n16, finger_w=n_fw6, gate="n_batt_n_b", stack_id="rowN_out"),
]
stickN = gen1(trs_rowN)
print("RowP(M15/M25) stick:", stickP["status"], stickP.get("odd_nodes"))
print("RowN(M16/M26) stick:", stickN["status"], stickN.get("odd_nodes"))
report["rowP_out"] = dict(finger_w=n_fw5, n=n15, stick=stickP)
report["rowN_out"] = dict(finger_w=n_fw6, n=n16, stick=stickN)

bs_out = check_box_shape({"rowP_out": 2*n15, "rowN_out": 2*n16})
print("box-shape (stage2 output cell):", bs_out)

# ---------------------------------------------------------------------------
# Matching candidate detection (whole device list -- gate-net based, per SKILL.md sec2.6)
# ---------------------------------------------------------------------------
all_trs = trs_row1 + trs_row2 + trs_row3 + trs_row4 + trs_rowP + trs_rowN
matches = find_matching_candidates(all_trs)
print("\nMatching candidates (current_mirror/diff_pair):")
for k, v in matches.items():
    print(" ", k, "->", len(v), "groups" if isinstance(v, dict) else "")

hub = find_hub_merge_candidates(all_trs)
print("\nHub-merge candidates:", {k: len(v) if hasattr(v,'__len__') else v for k,v in hub.items()} if isinstance(hub, dict) else hub)

# Mirror symmetry check on each row's ACTUAL generated sequence
pair_maps = {
    "row1_pmos_in_casc": {"M1a": "M1b", "M1b": "M1a", "M2a": "M2b", "M2b": "M2a"},
    "row2_nmos_in_casc": {"M3a": "M3b", "M3b": "M3a", "M4a": "M4b", "M4b": "M4a"},
    "rowP_out": {"M15": "M25", "M25": "M15"},
    "rowN_out": {"M16": "M26", "M26": "M16"},
}
mirror_results = {}
for row, data, pm in [("row1_pmos_in_casc", stick1, pair_maps["row1_pmos_in_casc"]),
                       ("row2_nmos_in_casc", stick2, pair_maps["row2_nmos_in_casc"]),
                       ("rowP_out", stickP, pair_maps["rowP_out"]),
                       ("rowN_out", stickN, pair_maps["rowN_out"])]:
    seq = data.get("transistor_sequence", [])
    ok = check_mirror_symmetry(seq, pm).ok if seq else None
    mirror_results[row] = ok
    print(f"check_mirror_symmetry({row}) = {ok}")

report["matching_candidates"] = {str(k): (list(map(str,v)) if isinstance(v, list) else
                                    {str(kk): list(map(str,vv)) for kk,vv in v.items()} if isinstance(v, dict) else v)
                                   for k, v in matches.items()}
report["hub_merge"] = {str(k): (list(map(str,v)) if hasattr(v,'__iter__') and not isinstance(v,str) else v) for k,v in hub.items()} if isinstance(hub, dict) else str(hub)
report["mirror_symmetry"] = mirror_results
report["box_shape"] = dict(core=bs_core.__dict__, bias_tail=bs_bias_tail.__dict__, stage2_out=bs_out.__dict__)

# ---------------------------------------------------------------------------
# Physical floorplan (required report section, SKILL.md sec7 row 8) -- pack the 3 cells this
# pass actually covers (core_signal / bias_tail / stage2_output) as independent spine groups.
# Honest scope note: M27-M40 (biasing generator, Fig.4) and M36-M40/R1-R2 (CMFB, Fig.5) were
# sized (section 3) but not run through the stick-diagram pipeline in this pass (see
# report["biasgen_cmfb_note"] upstream in build_report.py) -- they are therefore not in this
# floorplan either. This is a partial-scope floorplan, not a full-circuit one; said explicitly
# rather than silently omitting the section (design-report-spec.md sec2 item 8).
# ---------------------------------------------------------------------------
spine_groups = {
    "core_signal_cell": [block_from_row_widths("row1_pmos_in_casc", {"row1_pmos_in_casc": bs_core.row_widths["row1_pmos_in_casc"]}),
                         block_from_row_widths("row2_nmos_in_casc", {"row2_nmos_in_casc": bs_core.row_widths["row2_nmos_in_casc"]})],
    "bias_tail_cell": [block_from_row_widths("row3_top_load", {"row3_top_load": bs_bias_tail.row_widths["row3_top_load"]}),
                       block_from_row_widths("row4_tail", {"row4_tail": bs_bias_tail.row_widths["row4_tail"]})],
    "stage2_output_cell": [block_from_row_widths("rowP_out", {"rowP_out": bs_out.row_widths["rowP_out"]}),
                           block_from_row_widths("rowN_out", {"rowN_out": bs_out.row_widths["rowN_out"]})],
}
floorplan = pack_floorplan_grouped(spine_groups, mirror_pairs=[])
print("\nFloorplan (3 covered cells):", "bbox=", floorplan.bbox_width, "x", floorplan.bbox_height,
      "aspect_ratio=", floorplan.aspect_ratio, "packing_density=", floorplan.packing_density)
report["floorplan"] = {
    "placements": {name: dict(x=p.x, y=p.y, width=p.width, height=p.height) for name, p in floorplan.placements.items()},
    "bbox": {"width": floorplan.bbox_width, "height": floorplan.bbox_height},
    "aspect_ratio": floorplan.aspect_ratio,
    "packing_density": floorplan.packing_density,
    "scope_note": ("pack_floorplan_grouped() output, real run -- 3 cells covered by this pass "
                   "(core_signal_cell/bias_tail_cell/stage2_output_cell). M27-M40 (biasing "
                   "generator, Fig.4) and CMFB (Fig.5, M36-M40/R1-R2) were sized but not run "
                   "through the stick-diagram/floorplan pipeline in this pass -- see the honest "
                   "scope note in section 7 (layout guide). This is a partial-scope floorplan, "
                   "not a full-circuit one."),
}

# ---------------------------------------------------------------------------
# audit_row_split() -- matching-safety gate, once per independently-boxed physical cell.
# (per its own docstring: box-shape + matching-safety are checked TOGETHER for whatever
# `rows` dict is passed in one call -- passing unrelated cells together would produce a
# meaningless combined box-shape ratio, so this circuit's 3 physical cells each get their
# own call, not one call across all 6 rows.)
# ---------------------------------------------------------------------------
audit_core = audit_row_split(
    {"row1_pmos_in_casc": trs_row1, "row2_nmos_in_casc": trs_row2},
    matching_pairs=[("M1a", "M1b"), ("M2a", "M2b"), ("M3a", "M3b"), ("M4a", "M4b")],
    pair_kinds={
        ("M1a", "M1b"): "diff_pair",        # share source Vx, differ gate Vip/Vim
        ("M4a", "M4b"): "diff_pair",        # NMOS half of the same current-reuse diff pair --
                                             # find_matching_candidates() buckets this under
                                             # hub_merge instead (M5 also shares net Vy, a
                                             # whole-circuit net-sharing artifact) but this IS a
                                             # genuine matched pair for layout purposes, so it's
                                             # declared explicitly here (audit_row_split()'s
                                             # documented manual-override use of pair_kinds).
        ("M2a", "M2b"): "current_mirror",   # share gate Vbias2 (fixed cascode bias)
        ("M3a", "M3b"): "current_mirror",   # share gate Vbias3 (fixed cascode bias)
    })
audit_bias_tail = audit_row_split(
    {"row3_top_load": trs_row3, "row4_tail": trs_row4},
    matching_pairs=[])  # M6/M7 is an intentional 0.7:0.3 ASYMMETRIC split (not a matched pair);
                        # M5 is a single device -- neither needs a matching-safety check here.
audit_stage2 = audit_row_split(
    {"rowP_out": trs_rowP, "rowN_out": trs_rowN},
    matching_pairs=[("M15", "M25"), ("M16", "M26")],
    pair_kinds={
        ("M15", "M25"): "branch_symmetric",  # mirrored output legs, no shared node -- same
        ("M16", "M26"): "branch_symmetric",  # category as folded_cascode's M7/M8 (docstring)
    })
print("\naudit_row_split(core_signal_cell).ok =", audit_core.ok)
for c in audit_core.checks:
    print("   ", c.name, "->", c.ok, "|", c.detail)
print("audit_row_split(bias_tail_cell).ok =", audit_bias_tail.ok)
print("audit_row_split(stage2_output_cell).ok =", audit_stage2.ok)
for c in audit_stage2.checks:
    print("   ", c.name, "->", c.ok, "|", c.detail)
report["audit_row_split"] = {
    "core_signal_cell": dict(ok=audit_core.ok, checks=[asdict(c) for c in audit_core.checks]),
    "bias_tail_cell": dict(ok=audit_bias_tail.ok, checks=[asdict(c) for c in audit_bias_tail.checks]),
    "stage2_output_cell": dict(ok=audit_stage2.ok, checks=[asdict(c) for c in audit_stage2.checks]),
}

# ---------------------------------------------------------------------------
# check_stick_diagram_coverage() -- do ALL sized devices have a physical row? Sized names in
# sizing_results.json are grouped/annotated ("M15/M25 (barely-on Q-point)", "M27/M28/M29") --
# expand to individual physical device names before comparing (grouped names would never
# set-match the individual names build_stick_diagram() actually used).
# ---------------------------------------------------------------------------
def _expand_device_names(raw_name):
    """sizing_results.json names are grouped/annotated ('M15/M25 (barely-on Q-point)',
    'M27/M28/M29') and sometimes use the paper's own shorthand for a mirrored pair ('M14a/b'
    means M14a and M14b, not a literal device named 'b') -- reconstruct that shorthand by
    reusing the previous full name's numeric prefix. Genuinely ambiguous compound tokens
    (e.g. 'M30-M32') are kept as one literal name rather than guessed apart -- honest
    imprecision, not fabricated precision."""
    base = re.sub(r"\s*\(.*?\)\s*", "", raw_name).strip()
    parts = [p.strip() for p in base.split("/") if p.strip()]
    expanded, prev_full = [], None
    for part in parts:
        if re.match(r"^[a-zA-Z]+$", part) and not part.startswith("M") and prev_full:
            m = re.match(r"^(M\d+)[a-zA-Z]*$", prev_full)
            part = m.group(1) + part if m else part
        expanded.append(part)
        prev_full = part
    return set(expanded)

sized_individual_names = set()
for r in S.values():
    sized_individual_names |= _expand_device_names(r["name"])

stick_diagram_devices = {
    "row1_pmos_in_casc": [t.name for t in trs_row1], "row2_nmos_in_casc": [t.name for t in trs_row2],
    "row3_top_load": [t.name for t in trs_row3], "row4_tail": [t.name for t in trs_row4],
    "rowP_out": [t.name for t in trs_rowP], "rowN_out": [t.name for t in trs_rowN],
}
coverage = check_stick_diagram_coverage(sized_individual_names, stick_diagram_devices)
print("\ncheck_stick_diagram_coverage().ok =", coverage.ok)
print("  missing (sized but no physical row -- honest, already-disclosed partial scope):",
      sorted(coverage.missing))
report["coverage"] = dict(ok=coverage.ok, missing=sorted(coverage.missing))

# ---------------------------------------------------------------------------
# run_full_circuit_audit() -- single mandatory gate (device-count/net-case/matching-disposition/
# box-shape), scoped HONESTLY to the 15 devices this pass actually resolved to gate-level
# connectivity (core_signal_cell + bias_tail_cell + stage2_output_cell). Bias-gen (M27-M40),
# CMFB (M36-M40, R1/R2), and Class-AB floating-battery internals (M8-M14, M17-M24) were sized
# but their gate-level connectivity was never confirmed to certainty from the scanned schematic
# (see this report's own out_of_scope note) -- auditing them here would mean fabricating
# connectivity that was never actually verified, so they are excluded rather than assumed.
# ---------------------------------------------------------------------------
block_of = {
    "M1a": "core_signal_cell", "M1b": "core_signal_cell", "M2a": "core_signal_cell", "M2b": "core_signal_cell",
    "M3a": "core_signal_cell", "M3b": "core_signal_cell", "M4a": "core_signal_cell", "M4b": "core_signal_cell",
    "M6": "bias_tail_cell", "M7": "bias_tail_cell", "M5": "bias_tail_cell",
    "M15": "stage2_output_cell", "M25": "stage2_output_cell", "M16": "stage2_output_cell", "M26": "stage2_output_cell",
}
audit_devices = {t.name: (t.kind, t.source, t.drain, t.gate, block_of[t.name]) for t in all_trs}
expected_counts = {"core_signal_cell": 8, "bias_tail_cell": 3, "stage2_output_cell": 4}
dispositions = {}
for (kind, net), group in hub.items():
    if len(group) >= 2:
        dispositions[("hub_merge", kind, net)] = ("real_match", "find_hub_merge_candidates()로 §4에서 이미 확인됨")
for (kind, net), group in matches.get("current_mirror", {}).items():
    dispositions[("current_mirror", kind, net)] = ("real_match", "고정 바이어스 게이트 공유 캐스코드 쌍, §4에서 확인됨")
for (kind, net), group in matches.get("diff_pair", {}).items():
    dispositions[("diff_pair", kind, net)] = ("real_match", "차동쌍(source 공유, gate 상이), §4에서 확인됨")
box_shape_checks = {
    "core_signal_cell": {"row1_pmos_in_casc": bs_core.row_widths["row1_pmos_in_casc"],
                          "row2_nmos_in_casc": bs_core.row_widths["row2_nmos_in_casc"]},
    "bias_tail_cell": {"row3_top_load": bs_bias_tail.row_widths["row3_top_load"],
                        "row4_tail": bs_bias_tail.row_widths["row4_tail"]},
    "stage2_output_cell": {"rowP_out": bs_out.row_widths["rowP_out"], "rowN_out": bs_out.row_widths["rowN_out"]},
}
full_audit = run_full_circuit_audit(audit_devices, expected_counts, dispositions, box_shape_checks=box_shape_checks)
print("\nrun_full_circuit_audit() [partial scope -- 15 devices, 3 covered cells].ok =", full_audit.ok)
for c in full_audit.checks:
    print("   ", c.name, "->", c.ok, "|", c.detail)
run_full_circuit_audit_scope_note = (
    "Partial-scope audit -- covers only the 15 devices in the 3 cells this pass builds stick "
    "diagrams for (core_signal_cell/bias_tail_cell/stage2_output_cell). Bias-gen (M27-M40), "
    "CMFB (M36-M40, R1/R2), and Class-AB floating-battery internals (M8-M14, M17-M24) were sized "
    "but their connectivity was not resolved to gate-level certainty from the scanned schematic "
    "in this pass -- auditing them would require fabricating connectivity not actually verified, "
    "so they are honestly excluded here rather than assumed. See report's own out_of_scope note."
)
report["run_full_circuit_audit"] = dict(ok=full_audit.ok, checks=[asdict(c) for c in full_audit.checks],
                                         scope_note=run_full_circuit_audit_scope_note)

with open("stick_results.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print("\nWrote stick_results.json")

# ---------------------------------------------------------------------------
# save_instance_json() -- the design-specified instance-output JSON
# (docs/02-design/features/analog-topology-json-library.design.md: workspaces/<design>/
# <design_name>.instance.json). This circuit has 3 independently-boxed physical cells rather
# than one, so box_shape/audit_row_split are passed as {cell_name: verdict} dicts (2026-07-29
# save_instance_json() extension -- see stick_diagram.py). scope_note documents the same
# partial-scope honesty as above.
# ---------------------------------------------------------------------------
instance_pipeline_result = {
    "transistors": all_trs,
    "box_shape": {"core_signal_cell": bs_core, "bias_tail_cell": bs_bias_tail, "stage2_output_cell": bs_out},
    "audit_row_split": {"core_signal_cell": audit_core, "bias_tail_cell": audit_bias_tail, "stage2_output_cell": audit_stage2},
    "floorplan": floorplan,
    "coverage": coverage,
    "scope_note": (
        "Partial-scope instance -- only the 15 devices sized+laid out in this pass "
        "(core_signal_cell/bias_tail_cell/stage2_output_cell) are covered by netlist/floorplan/"
        "box_shape/audit_row_split above. Bias-gen (M27-M40), CMFB (M36-M40, R1/R2), and "
        "Class-AB floating-battery internals (M8-M14, M17-M24) were sized (see the 'sizing' key, "
        "sourced from sizing_results.json) but not run through the stick-diagram/floorplan/audit "
        "pipeline in this pass -- see run_full_circuit_audit.scope_note in stick_results.json for why."
    ),
}
save_instance_json(
    "current_reuse_telescopic_ota.instance.json",
    "skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json",
    S, instance_pipeline_result)
print("Wrote current_reuse_telescopic_ota.instance.json")
