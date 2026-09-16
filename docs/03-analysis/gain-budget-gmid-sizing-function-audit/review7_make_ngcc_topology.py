# -*- coding: utf-8 -*-
"""사용자 확정 넷 표로 ngcc_3stage_ff.topology.json 작성(connectivity만)."""
import io
import json

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"


def m(name, kind, drain, gate, source):
    return {"name": name, "kind": kind, "source": source, "drain": drain, "gate": gate}


d = {
    "schema_version": "2.0",
    "topology_name": "ngcc_3stage_ff",
    "source": ("Jae-Seung Lee, Jun-Hyun Bae, Ho-Young Kim, Ji-Yong Um, Jae-Yoon Sim, Hong-June Park, "
               "\"A Design Guide of 3-stage CMOS Operational Amplifier with Nested Gm-C Frequency Compensation\", "
               "JSTS(Journal of Semiconductor Technology and Science) Vol.7 No.1, March 2007, Fig. 3 "
               "\"Circuit diagram of 3-stage NGCC amplifier\" (p.24). DOI 10.5573/JSTS.2007.7.1.020"),
    "_note": ("2026-09-16 사용자 확정 넷 표로 작성(오케스트레이터가 원문 Fig. 3을 확대해 판독하고 사용자가 항목별 확정). "
              "NGCC = Nested Gm-C Compensation: feedforward 소자 gmf1(M7)·gmf2(M14)가 Cm1·Cm2가 만드는 RHP zero를 상쇄한다(gmf,i = gm,i). "
              "신호 경로가 Vout에서 세 갈래로 합류한다(M7 feedforward1, M13 gm3, M14 feedforward2) -- 계획 DEC-81(복합 블록)이 실제로 발동하는 첫 회로다(U-34). "
              "feedforward1 가지: M5(VBP 전류원)가 NX에 바이어스를 주고 M6B가 1단 미러 선(ND)에서 신호 전류를 복사해 빼며, diode M6A가 그 차이를 전압으로 바꿔 M7 게이트를 구동한다(M6A:M7 = 1:2). "
              "벌크는 기본 규칙(nmos = 최저 전위 레일, pmos = 최고 전위 레일)이라 bulk 필드를 두지 않는다. symmetry 판정·sizing 필드는 미정."),
    "linked_topology_files": [],
    "supply_nets": ["vdd", "gnd"],
    "_supply_nets_comment": "계획 DEC-60(레일 넷 선언). 전압은 사이징 스펙 `supplies_v`로 선언한다(논문 VDD=1.2V, sky130 재설계 전압은 별도 결정).",
    "compensation": None,
    "_compensation_status": "pending_topology_fn",
    "_compensation_status_comment": ("보상식은 `topology_library.ngcc_3stage_topology()`(방법론 §10.2, 이 논문 Eq 8.a/8.b)가 이미 구현·대조돼 있다. "
                                     "`stage_devices` 매핑(gm1 = M1/M2, gm2 = M8, gm3 = M13, gmf1 = M7, gmf2 = M14)은 공동분석 ratify 뒤 채운다."),
    "netlist": [
        m("M0", "pmos", "TAIL", "VBP", "vdd"),
        m("M1", "pmos", "ND", "Vinn", "TAIL"),
        m("M2", "pmos", "V1", "Vinp", "TAIL"),
        m("M3", "nmos", "ND", "ND", "gnd"),
        m("M4", "nmos", "V1", "ND", "gnd"),
        m("M5", "pmos", "NX", "VBP", "vdd"),
        m("M6A", "nmos", "NX", "NX", "gnd"),
        m("M6B", "nmos", "NX", "ND", "gnd"),
        m("M7", "nmos", "Vout", "NX", "gnd"),
        m("M8", "nmos", "NP", "V1", "gnd"),
        m("M9", "pmos", "NP", "NP", "vdd"),
        m("M10", "pmos", "V2", "NP", "vdd"),
        m("M11", "nmos", "V2", "VBN", "gnd"),
        m("M12", "pmos", "Vout", "VBP", "vdd"),
        m("M13", "nmos", "Vout", "V2", "gnd"),
        m("M14", "nmos", "Vout", "V1", "gnd"),
    ],
    "passive_elements": [
        {"name": "Cm1", "kind": "capacitor", "value_farad": None, "terminals": ["V1", "Vout"],
         "_comment": "바깥 nested 보상. 논문 설계 예시 1.68 pF(Table 4), 값은 보상망이 계산한다(DEC-24)."},
        {"name": "Cm2", "kind": "capacitor", "value_farad": None, "terminals": ["V2", "Vout"],
         "_comment": "안쪽 nested 보상. 논문 설계 예시 1.32 pF."},
        {"name": "CL", "kind": "capacitor", "value_farad": None, "terminals": ["Vout", "gnd"],
         "_comment": "부하. 논문 스펙 10 pF."},
    ],
    "ports": {
        "Vinn": {"role": "differential_input_n", "direction": "input"},
        "Vinp": {"role": "differential_input_p", "direction": "input"},
        "Vout": {"role": "single_ended_output", "direction": "output"},
    },
    "symmetry": {"matching_pairs": [], "_comment": "미판정 -- find_matching_candidates() 후보를 사용자와 공동 판정해 채운다."},
    "sizing_roles": None,
    "device_roles": None,
    "_paper_target_spec_comment": ("논문 Ⅳ절·Table 4의 설계 예시. **문서화 전용**(엔진 미사용). 실행 정본은 workspaces/run_harness.py SPECS이며 "
                                  "sky130 재설계 전원·부하는 사용자 결정 뒤 채운다. 계획 MG0에서 필드 이름을 `_declared_target_spec`으로 통일할 예정."),
    "_paper_target_spec": {
        "process": "0.18 um CMOS (논문). sky130 재설계 전압은 미정",
        "supplies_v": {"vdd": 1.2, "gnd": 0.0, "_comment": "논문 VDD=1.2V"},
        "loading": {"CL_farad": 1e-11, "_comment": "논문 CL = 10 pF"},
        "performance_targets": {
            "gbw_hz": {"op": ">=", "value": 1e7, "_comment": "GB = 10 MHz"},
            "pm_deg": {"op": ">=", "value": 63.4, "_comment": "PM = 63.4 deg (설계 목표), 시뮬레이션 결과 59 deg"},
            "icmr_v": {"op": ">=", "value": 0.4, "_comment": "ICMR >= VDD/3"},
        },
        "design_example": {
            "k": 4, "alpha": 0.3,
            "gm_s": {"gm1": 1.05e-4, "gm2": 1.86e-4, "gm3": 2.5e-3},
            "id_amp": {"ID1": 4.2e-6, "ID2": 7.4e-6, "ID3": 1.0e-4},
            "w_over_l": {"1": 20, "2": 8, "3": 105},
            "cm_farad": {"Cm1": 1.68e-12, "Cm2": 1.32e-12},
            "vdsat_v": 0.08,
            "_comment": "Table 4. 참고값 -- 이 프로젝트 사이징 목표로 그대로 쓰지 않는다(공정이 다르다).",
        },
    },
}

p = LIB + "\\ngcc_3stage_ff.topology.json"
io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
print("wrote", p)
