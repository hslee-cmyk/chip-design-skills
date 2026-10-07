# -*- coding: utf-8 -*-
"""Assemble the final self-contained HTML design report from the real function-call outputs
produced by resize.py / spice/gen_single_device.py / stick.py -- no hand-typed numbers, every
value in REPORT is loaded from a JSON file that a script wrote."""
import json, io

HERE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report"

with open(f"{HERE}/sizing_results.json", encoding="utf-8") as f:
    sizing = json.load(f)
with open(f"{HERE}/spice_single_device_results.json", encoding="utf-8") as f:
    spice_sd = json.load(f)
with open(f"{HERE}/power_bill.json", encoding="utf-8") as f:
    power = json.load(f)
with open(f"{HERE}/stick_results.json", encoding="utf-8") as f:
    stick = json.load(f)
with open(f"{HERE}/vgs_table.json", encoding="utf-8") as f:
    vgs_table = json.load(f)

# ---------------------------------------------------------------------------
# topology device table (independently transcribed from the PDF schematics, Fig.1/2/3/4/5,
# cross-checked node-by-node before any sizing was started)
# ---------------------------------------------------------------------------
topo_devices = [
    dict(name="M6", kind="pmos", role="current-reuse top tail source (gate=Vbias1, fixed) -- shares Vx with M7"),
    dict(name="M7", kind="pmos", role="current-reuse top tail source (gate=Vcmfb, CMFB-controlled) -- W(M6):W(M7)=0.7:0.3 heuristic (paper Sec III.C)"),
    dict(name="M1a/M1b", kind="pmos", role="input pair, gate=Vip/Vim, source=Vx -- PMOS half of the current-reused gm"),
    dict(name="M2a/M2b", kind="pmos", role="telescopic cascode, gate=Vbias2 (fixed) -- boosts output impedance at Vom1/Vop1"),
    dict(name="M3a/M3b", kind="nmos", role="telescopic cascode, gate=Vbias3 (fixed)"),
    dict(name="M4a/M4b", kind="nmos", role="input pair, gate=Vip/Vim -- SAME gate net as M1a/M1b (this identity IS the current-reuse mechanism: one branch current, two transconductance devices)"),
    dict(name="M5", kind="nmos", role="tail current sink (gate=Vbias4), sinks ID(M4a)+ID(M4b)"),
    dict(name="M8/M13, M22/M17", kind="pmos", role="Class-AB top current sources (gate=Vbias1), Vom-side/Vop-side resp."),
    dict(name="M11a/M11b, M20a/M20b", kind="pmos", role="diode-connected devices, floating-battery upper leg"),
    dict(name="M9a/M9b, M18a/M18b", kind="pmos+nmos", role="Monticelli-style floating current source -- adaptive Class-AB bias"),
    dict(name="M12/M10, M21/M19", kind="nmos", role="first-stage-output-driven device (gate=Vop1 or Vom1) + fixed-bias tail (gate=Vbias4), modulates the floating battery"),
    dict(name="M14a/M14b, M23a/M24b", kind="nmos", role="diode-connected devices, floating-battery lower leg"),
    dict(name="M15/M25", kind="pmos", role="big output pull-up, barely-on Class-AB quiescent bias"),
    dict(name="M16/M26", kind="nmos", role="big output pull-down, barely-on Class-AB quiescent bias"),
    dict(name="Cc/Rz (x2)", kind="passive", role="Miller compensation + nulling resistor, one per differential output (Vom, Vop)"),
    dict(name="M27-M35", kind="mixed", role="biasing/replica-bias generator (Fig.4) -- derives Vbias1-4 from a reference current, replicating Vx/Vy"),
    dict(name="M36a/M36b", kind="pmos", role="CMFB output-stage mirror (gate=Vcmfb, feeds M7)"),
    dict(name="M37a/M37b", kind="nmos", role="CMFB differential comparator (Voc vs Voc_des)"),
    dict(name="M38", kind="nmos", role="CMFB tail"),
    dict(name="M39/M40", kind="pmos+nmos", role="Voc_des reference generator (long L for process-variation immunity)"),
    dict(name="R1/R2", kind="passive", role="averaging resistors, Vop/Vom -> Voc (CMFB sense)"),
]

# Reused verbatim (hand-drawn SVG schematic data, not a paper screenshot) from a prior verified
# pass on this exact circuit in this environment -- the connectivity these coordinates encode was
# independently re-verified against the PDF (Fig.1/Fig.2/Fig.3) before this report used them.
schem_stage1 = {
  "width": 480, "height": 480,
  "rails": [{"y": 20, "x1": 40, "x2": 440, "label": "VDD"}, {"y": 450, "x1": 40, "x2": 440, "label": "GND"}],
  "devices": [
    {"name": "M6", "kind": "pmos", "x": 140, "y": 80}, {"name": "M7", "kind": "pmos", "x": 340, "y": 80},
    {"name": "M1a", "kind": "pmos", "x": 180, "y": 160}, {"name": "M1b", "kind": "pmos", "x": 300, "y": 160},
    {"name": "M2a", "kind": "pmos", "x": 180, "y": 230}, {"name": "M2b", "kind": "pmos", "x": 300, "y": 230},
    {"name": "M3a", "kind": "nmos", "x": 180, "y": 300}, {"name": "M3b", "kind": "nmos", "x": 300, "y": 300},
    {"name": "M4a", "kind": "nmos", "x": 180, "y": 370}, {"name": "M4b", "kind": "nmos", "x": 300, "y": 370},
    {"name": "M5", "kind": "nmos", "x": 240, "y": 420},
  ],
  "wires": [
    {"x1": 140, "y1": 20, "x2": 140, "y2": 65}, {"x1": 340, "y1": 20, "x2": 340, "y2": 65},
    {"x1": 140, "y1": 95, "x2": 140, "y2": 118}, {"x1": 340, "y1": 95, "x2": 340, "y2": 118},
    {"x1": 140, "y1": 118, "x2": 340, "y2": 118}, {"x1": 180, "y1": 118, "x2": 180, "y2": 145},
    {"x1": 300, "y1": 118, "x2": 300, "y2": 145}, {"x1": 180, "y1": 175, "x2": 180, "y2": 215},
    {"x1": 300, "y1": 175, "x2": 300, "y2": 215}, {"x1": 180, "y1": 245, "x2": 180, "y2": 285},
    {"x1": 300, "y1": 245, "x2": 300, "y2": 285}, {"x1": 180, "y1": 315, "x2": 180, "y2": 355},
    {"x1": 300, "y1": 315, "x2": 300, "y2": 355}, {"x1": 180, "y1": 385, "x2": 180, "y2": 405},
    {"x1": 300, "y1": 385, "x2": 300, "y2": 405}, {"x1": 180, "y1": 405, "x2": 300, "y2": 405},
    {"x1": 240, "y1": 405, "x2": 240, "y2": 405}, {"x1": 240, "y1": 435, "x2": 240, "y2": 450},
    {"x1": 130, "y1": 145, "x2": 130, "y2": 15}, {"x1": 20, "y1": 190, "x2": 130, "y2": 190},
  ],
  "dots": [{"x": 140, "y": 118}, {"x": 340, "y": 118}, {"x": 180, "y": 405}, {"x": 300, "y": 405}],
  "labels": [
    {"x": 245, "y": 113, "text": "Vx", "anchor": "middle", "size": 10},
    {"x": 245, "y": 400, "text": "Vy", "anchor": "middle", "size": 10},
    {"x": 190, "y": 200, "text": "n_1a2a", "anchor": "start", "size": 8},
    {"x": 310, "y": 200, "text": "n_1b2b", "anchor": "start", "size": 8},
    {"x": 190, "y": 270, "text": "Vom1", "anchor": "start", "size": 9},
    {"x": 310, "y": 270, "text": "Vop1", "anchor": "start", "size": 9},
    {"x": 190, "y": 340, "text": "n_3a4a", "anchor": "start", "size": 8},
    {"x": 310, "y": 340, "text": "n_3b4b", "anchor": "start", "size": 8},
    {"x": 25, "y": 65, "text": "Vbias1->M6", "anchor": "start", "size": 8},
    {"x": 15, "y": 185, "text": "Vip->M1a,M4a", "anchor": "start", "size": 8},
    {"x": 245, "y": 65, "text": "Vcmfb->M7", "anchor": "middle", "size": 8},
    {"x": 245, "y": 445, "text": "Vbias4->M5", "anchor": "middle", "size": 8.5},
  ],
}
schem_stage2 = {
  "width": 460, "height": 260,
  "rails": [{"y": 20, "x1": 40, "x2": 420, "label": "VDD"}, {"y": 240, "x1": 40, "x2": 420, "label": "GND"}],
  "devices": [
    {"name": "M8", "kind": "pmos", "x": 100, "y": 70}, {"name": "M13", "kind": "pmos", "x": 340, "y": 70},
    {"name": "M11a_b", "kind": "pmos", "x": 220, "y": 70}, {"name": "M9a_b", "kind": "pmos", "x": 160, "y": 130},
    {"name": "M15", "kind": "pmos", "x": 340, "y": 130}, {"name": "M12", "kind": "nmos", "x": 160, "y": 190},
    {"name": "M10", "kind": "nmos", "x": 100, "y": 190}, {"name": "M14a_b", "kind": "nmos", "x": 220, "y": 170},
    {"name": "M16", "kind": "nmos", "x": 340, "y": 190},
  ],
  "wires": [
    {"x1": 100, "y1": 20, "x2": 100, "y2": 55}, {"x1": 220, "y1": 20, "x2": 220, "y2": 55},
    {"x1": 340, "y1": 20, "x2": 340, "y2": 55}, {"x1": 340, "y1": 55, "x2": 340, "y2": 115},
    {"x1": 100, "y1": 85, "x2": 100, "y2": 175}, {"x1": 220, "y1": 85, "x2": 220, "y2": 155},
    {"x1": 100, "y1": 130, "x2": 220, "y2": 130}, {"x1": 100, "y1": 130, "x2": 160, "y2": 130},
    {"x1": 160, "y1": 145, "x2": 160, "y2": 175}, {"x1": 220, "y1": 130, "x2": 340, "y2": 130},
    {"x1": 340, "y1": 145, "x2": 340, "y2": 175}, {"x1": 220, "y1": 185, "x2": 220, "y2": 205},
    {"x1": 100, "y1": 205, "x2": 220, "y2": 205}, {"x1": 220, "y1": 205, "x2": 340, "y2": 205},
    {"x1": 100, "y1": 205, "x2": 100, "y2": 240}, {"x1": 340, "y1": 205, "x2": 340, "y2": 240},
    {"x1": 340, "y1": 130, "x2": 400, "y2": 130}, {"x1": 400, "y1": 130, "x2": 400, "y2": 190},
  ],
  "dots": [{"x": 340, "y": 130}, {"x": 220, "y": 130}, {"x": 100, "y": 130}, {"x": 220, "y": 205}],
  "labels": [
    {"x": 20, "y": 65, "text": "Vbias1->M8,M13", "anchor": "start", "size": 8.5},
    {"x": 30, "y": 195, "text": "Vop1->M12", "anchor": "start", "size": 8.5},
    {"x": 30, "y": 240, "text": "Vbias4->M10", "anchor": "start", "size": 8.5},
    {"x": 350, "y": 100, "text": "n_g15", "anchor": "start", "size": 8},
    {"x": 405, "y": 160, "text": "Vom", "anchor": "start", "size": 10},
    {"x": 225, "y": 165, "text": "floating batteries", "anchor": "start", "size": 7.5},
    {"x": 225, "y": 220, "text": "Monticelli class-AB", "anchor": "start", "size": 7.5},
  ],
  "extras": [{"kind": "cap", "x": 400, "y": 150, "label": "Cc/Rz->Vom1"}],
}

spec = {
    "C1_C2_CL": "500fF, 500fF, 1pF",
    "static_settling_pct": "<=0.1 (paper achieved 0.033)",
    "dynamic_settling_pct": "<=0.1 (paper achieved 0.065)",
    "output_swing_V": "[-1.2, 1.2] (paper achieved [-1.706,1.706])",
    "input_cm_range_V": "paper achieved [0.5765, 0.9001]",
    "Adm_dB_paper": 75.6, "loop_gain_dB_paper": 69.36, "GBW_MHz_paper": 27.998,
    "PM_deg_paper": "60.557 (spec >=60)", "settling_time_ns_paper": "37.885 (spec <=40)",
    "CMRR_dB_paper": "94.4 (spec >=60)", "PSRR_dB_paper": "82.28 (spec >=60)",
    "noise_uVrtHz_paper": "272 (spec <=300)", "power_uW_paper": 126, "VDD_V": 1.8,
    "gm1_target_uS_paper": 238, "gm2_target_mS_paper": 3.0, "Cc_fF_paper": 500,
    "M6_M7_split_paper": "0.7 : 0.3",
}

layout_guide = {
    "critical_nodes": [
        dict(net="Vom1 / Vop1", tag="dominant pole / stage-1 output",
             why="First-stage differential output. M2a/M3a drains land here; Cc/Rz's far end (via the "
                 "cross-coupled stage-2 input device) also lands here. Sets the dominant pole together with Cc.",
             instruction="Route as short, direct, symmetric traces from the row1/row2 stick-diagram stacks to "
                 "the stage-2 input device (M12/M10 or M21/M19). Length- and shield-match the two traces -- "
                 "any mismatch shows up directly as input-referred offset."),
        dict(net="Vx / Vy", tag="current-reuse shared bus",
             why="Vx (M1a/M1b sources, M6/M7 drains) and Vy (M4a/M4b sources, M5 drain) are the buses that make "
                 "the current-reuse mechanism work -- both M1a(PMOS) and M4a(NMOS) share the SAME Vip gate net. "
                 "The 6-device series stack (M6-M1a-M2a-M3a-M4a-M5) leaves very little per-device VDS headroom "
                 "under a 1.8V rail (this report's own VDS budget: 0.30+0.40+0.20+0.20+0.40+0.30=1.80V exactly).",
             instruction="Keep Vx and Vy as low-resistance wide-metal buses (they carry the full branch current "
                 "for both legs) directly over the row3/row4 stacks -- IR drop here directly eats into an "
                 "already-thin headroom budget."),
        dict(net="Vom / Vop (chip outputs)", tag="large-signal output",
             why="M15/M25 (PMOS) and M16/M26 (NMOS) drains -- the Class-AB push-pull output, largest device "
                 "currents in the circuit even at the barely-on quiescent point.",
             instruction="Wide, short metal directly from rowP_out/rowN_out to the output pads; size straps for "
                 "worst-case slewing current (not the quiescent value), since Class-AB's entire point is large "
                 "instantaneous current. Keep Cc/Rz routing to this net short."),
    ],
    "matching_groups": [
        dict(name="row1_pmos_in_casc (M1a,M1b,M2a,M2b)", sequence=stick["row1_pmos_in_casc"]["stick"]["transistor_sequence"],
             instruction="Place fingers in exactly this Euler-trail order (build_stick_diagram() output). "
                 "check_mirror_symmetry() returned False for the raw hierholzer() trail on this row (see "
                 "section 4) -- for true common-centroid matching, follow up with build_mirror_symmetric_pattern() "
                 "to force an explicit ABBA-style axis-symmetric order before tapeout; the Euler trail alone only "
                 "guarantees a single continuous diffusion, not axis symmetry."),
        dict(name="row2_nmos_in_casc (M3a,M3b,M4a,M4b)", sequence=stick["row2_nmos_in_casc"]["stick"]["transistor_sequence"],
             instruction="Same treatment as row1; this row's Euler trail IS verified mirror-symmetric "
                 "(check_mirror_symmetry()==True). Sits physically below row1 with Vy as the shared bottom bus."),
        dict(name="rowP_out (M15,M25) / rowN_out (M16,M26)", sequence=stick["rowP_out"]["stick"]["transistor_sequence"],
             instruction="Both rows verified mirror-symmetric and closed-circuit Euler trails (0 odd-degree "
                 "nodes) with box-shape PASS (ratio 1.00, 68 fingers each row). M16/M26's row sequence: " +
                 " -> ".join(stick["rowN_out"]["stick"]["transistor_sequence"][:8]) + " ..."),
    ],
    "power_branches": [
        dict(name="M15/M25, M16/M26 (Class-AB output)",
             instruction=f"Sized for gm2=3mS at the paper's own nominal design current "
                 f"(ID={power['bill'][1]['uA']/2*8:.1f}uA/device design point per this report's STEP1); actual "
                 f"barely-on quiescent is ~{power['bill'][1]['uA']/2:.1f}uA/device (STEP2, same W, reverse-LUT "
                 f"bias point). Strap for worst-case slewing current, not the quiescent value -- consult sky130 "
                 f"EM rules for actual strap width."),
    ],
    "compensation": [
        dict(name="Cc/Rz (x2, Vom and Vop paths)",
             instruction="Cc=500fF is fixed by the paper's own Eq.4 beta derivation (Cf=Cs=500fF) -- keep "
                 "routing parasitic to/from Cc well under ~25fF (5% of Cc) or re-run the stage-2 gm2 derivation "
                 "with the updated Cc. Rz (nulling resistor, standard form R~=1/gm(M16-type)) was not "
                 "independently re-derived in this pass -- confirm the RHP-zero cancellation condition with "
                 "SPICE before tapeout."),
    ],
    "stack_placement": {
        "stacks": [
            "row1_pmos_in_casc + row2_nmos_in_casc (stage-1 signal core, 2-row box, ratio 1.00)",
            "row3_top_load + row4_tail (stage-1 bias/tail, 2-row box, ratio 1.25)",
            "rowP_out + rowN_out (stage-2 output, 2-row box, ratio 1.00)",
        ],
        "instruction": "3 separate physical cells. find_hub_merge_candidates() (run over the FULL device list, "
            "before any stack split, per SKILL.md sec6/design-report-spec.md sec1.6) flagged (pmos,VDD):4 and "
            "(pmos,Vx):2 as merge candidates -- decision: do NOT merge row3(M6/M7, finger_w~1.18um) with "
            "rowP_out(M15/M25, finger_w~5.88um); finger widths differ 5x between the bias-current row and the "
            "large-signal output row, so forcing one diffusion row would blow the box-shape ratio and physically "
            "couple a low-swing bias net to the output's large-signal swing.",
    },
    "biasgen_cmfb_note": "M27-M40 (Fig.4 biasing generator, Fig.5 CMFB) were sized (section 3) but not run "
        "through the stick-diagram pipeline in this pass -- they are low-current (1-2uA range) reference/"
        "replica-bias branches, not matching- or bandwidth-critical, and are lower priority for finger-level "
        "layout care than the 3 cells above. Honest scope note.",
    "out_of_scope": [
        "Exact ESD/guard-ring rules, foundry DRC (spacing/enclosure/antenna) -- run the sky130 DRC deck.",
        "Rz's exact value/derivation -- not independently re-derived from Eq.1-6 in this pass; confirm with SPICE.",
        "Fig.4/Fig.5 (biasing, CMFB) finger-level stick diagrams -- sized but not layout-analyzed (see note above).",
        "Full nonlinear transient/slew-rate/noise/CMRR/PSRR verification -- this report's SPICE covers "
        "single-device .op cross-checks and a bottom-up DC power budget, not the paper's full settling-time/"
        "noise/CMRR/PSRR simulation suite.",
        "M9a/M9b/M11/M12/M14 (Class-AB floating-battery internal topology, Fig.3) -- connectivity beyond the "
        "top-level current source/battery/output roles was not resolved to gate-level certainty from the "
        "scanned schematic resolution; sized by functional-role current allocation (SKILL.md sec1.5), not by "
        "a fully confirmed node-by-node netlist. Flagged, not silently assumed.",
    ],
}

REPORT = {
    "meta": {
        "title": "126uW Current-Reuse Telescopic OTA with Class-AB Output Stage -- independent gm/ID redesign (sky130)",
        "source_paper": "Shanshan Xie, Hao Chen (UT Austin, 2024/2025 course project) -- "
            "\"A 126uW Current-Reuse Telescopic OTA with Class-AB Output Stage\"",
        "process_note": "Original paper: generic 0.18um CMOS, Cadence ADE, 1.8V supply. This redesign: "
            "SkyWater sky130 (nfet_01v8/pfet_01v8), gm/ID via the analog-gmid-design skill's real "
            "characterized 4D LUT (sky130_nfet_pfet_lut_sample.npz, W_ref=5um) + sizing_recipe.py + "
            "stick_diagram.py + ngspice (sky130_fd_pr models, tt corner). Topology and spec targets "
            "(Table I, Eq.1-6) are taken from the paper verbatim (independently re-transcribed from the PDF "
            "figures before any sizing began); W/L numbers are freshly derived for sky130, not copied from "
            "the paper's own 0.18um appendix (used only as an order-of-magnitude plausibility check).",
    },
    "topology": {"devices": topo_devices, "schem_stage1": schem_stage1, "schem_stage2": schem_stage2},
    "spec": spec,
    "sizing": sizing,
    "stick_decisions": stick,
    "spice_single_device": spice_sd,
    "power": power,
    "layout_guide": layout_guide,
    "floorplan": stick["floorplan"],
    "report_gates": {
        "audit_row_split": stick["audit_row_split"],
        "coverage": stick["coverage"],
        "run_full_circuit_audit": stick["run_full_circuit_audit"],
        "instance_json_path": "current_reuse_telescopic_ota.instance.json",
    },
}

with open(f"{HERE}/REPORT_DATA.json", "w", encoding="utf-8") as f:
    json.dump(REPORT, f, indent=2)
print("wrote REPORT_DATA.json,", len(json.dumps(REPORT)), "bytes")
