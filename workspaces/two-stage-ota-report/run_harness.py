"""
세션31 최종 harness -- two_stage_ota를 optimize_full_circuit_budget() 하나만으로 spec ->
instance.json까지 완주시킨다(current-reuse-telescopic-ota-report/run_harness.py와 동일
패턴, 실제 sky130 LUT 사용).

## 경위(.ai/context.md 세션31 BZ①~CJ 전체 요약)
원래 목표(GBW=20MHz, gain_db>=60, "typical" 문헌값)는 실제 sky130 LUT로 모든 레버
(L 범위 1um->4um 확장, 면적예산 500um->2000um, M5/M7 theta 독립분리)를 다 시도해도
물리적으로 달성 불가능함이 확정됐다(진짜 상한 ~50~51dB). 유일하게 유효했던 레버는
**GBW를 낮추는 것**(compensation 공식 gm1=2π·GBW·Cm 관계상 GBW가 낮아지면 같은 면적
예산으로 훨씬 긴 L을 쓸 여유가 생김) -- GBW 20MHz~1MHz 전 구간을 스윕해 "10MHz 부근부터
수확체감(무릎)"을 확인한 뒤, 사용자가 그 무릎 지점에서 타협하기로 결정:
**GBW=7MHz(원 스펙 대비 1/3)로 gain_db=57.5dB 달성(원 스펙 51dB보다 오히려 +6.4dB 개선),
전력은 오히려 291uA로 66% 절감**. `library/two_stage_ota.topology.json`의 `gain_db`
constraint도 이 결정에 맞춰 `>=60`에서 `>=57`로 갱신됨(topology.json `_target_spec_
comment` 참고). M5/M7은 theta 분리를 한 번 시도했다가(+1dB, 그런데 folding 4배 필요)
GBW 레버가 훨씬 크게 개선한 뒤라 가치가 낮아져 공유 theta(`L_mirror_M5`)로 원복.

box-shape는 M6(매칭 파트너 없는 단독 소자, stage2 출력이라 W가 압도적으로 큼)만
`row_split`(2026-08-13 세션31 CD/CE 신설 `apply_explicit_row_split()`)으로 2행 folding
하면 충분(max_ratio 1.2, 허용치 1.5 이내 PASS).
"""
import sys, json, traceback
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import (SemiEmpiricalGmIdLUT, optimize_full_circuit_budget, dense_candidates,
                            layout_grid_L_candidates)
from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology
from design_report import assemble_report_data, save_html_report

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\two_stage_ota.topology.json"
INSTANCE_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\two-stage-ota-report\two_stage_ota.instance.json"
REPORT_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\two-stage-ota-report\two_stage_ota.report.html"
# current_reuse의 run_harness.py와 동일 근거(sky130hs.tlef "MANUFACTURINGGRID 0.005 ;" 원문).
L_GRID_STEP = 0.005e-6

d = np.load(LUTFILE)
W_REF = 5e-6
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=W_REF, SID_1F=d["SID_1F_n"])
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=W_REF, SID_1F=d["SID_1F_p"])

spec = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos},
    "lut": nmos,
    # LUT 특성화 범위(VDS 0~1.8V)가 sky130 nominal rail과 일치.
    "vdd": 1.8,
    "L_candidates": layout_grid_L_candidates(nmos, L_GRID_STEP, n=41),
    "L_grid_step": L_GRID_STEP,
    "VDS_candidates": dense_candidates(nmos.VDS_grid, n=13),
    "gm_id_grid": [i * 0.5 for i in range(4, 61)],
    # 2026-08-13(세션31 CJ) -- GBW 20MHz->7MHz(무릎 지점, 사용자 결정). Z/NDP는 원래
    # "typical" 값 그대로(Z를 3.5까지 낮춰봐도 GBW 여유가 거의 안 늘어남을 실측 확인,
    # .ai/context.md CJ 참고 -- Z는 지배적 레버가 아니었다).
    "GBW": 7e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
    "stage_gain_min": [10 ** (30.0 / 20), 10 ** (30.0 / 20)],
    "L_min": 0.15e-6,
    "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
    "stage_objective": "power",
    "stage_w_max": 500e-6,
    "min_finger_w": 0.1e-6,
    "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                "M5": ["M5", "M7"], "M6": ["M6"]},
    # M6(단독 소자, box-shape의 유일한 병목)만 2행 folding -- CE~CJ 실측으로 충분함이
    # 확인됨(max_ratio=1.2, 허용치 1.5 이내 PASS).
    "row_split": {"M6": 2},
}

try:
    # 2026-08-13(세션31 CJ) -- L 범위가 4um까지 넓어진 뒤로는 5점 격자가 너무 성겨(CF/CG
    # 실측으로 7점 이상 필요함이 확인됨) grid_points_per_theta=7로 상향.
    result = optimize_full_circuit_budget(TOPO, spec, grid_points_per_theta=7)
    print("OK -- theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    print("metrics:", result["metrics"])

    # library/two_stage_ota.topology.json에 _netlist_sections_structured가 없어(CC가
    # 남긴 별개 gap, 아직 미해결) 이 감사는 항상 실패한다 -- box-shape/사이징과 무관하므로
    # 정직하게 건너뛰고 별도로 보고한다.
    full_circuit_audit = None
    try:
        full_circuit_audit = run_full_circuit_audit_from_topology(TOPO)
        print("run_full_circuit_audit.ok:", full_circuit_audit.ok)
        for c in full_circuit_audit.checks:
            print(f"  - {c.name}: {c.ok} ({c.detail})")
    except ValueError as e:
        print(f"[SKIP] run_full_circuit_audit_from_topology() 실패(별도 gap, CC 참고): {e}")

    if result["pipeline_result"] is not None:
        pr = result["pipeline_result"]
        print(f"box_shape.ok={pr['box_shape'].ok} max_ratio={pr['box_shape'].max_ratio:.3f} "
              f"row_widths={pr['box_shape'].row_widths}")
        print(f"coverage.ok={pr['coverage'].ok} missing={pr['coverage'].missing}")

        save_instance_json(INSTANCE_OUT, TOPO, result["sizing"], result["pipeline_result"])
        note_parts = []
        if not result["audit_ok"]:
            note_parts.append("audit_ok=False -- audit_row_split에 남은 FAIL 항목 그대로 저장됨")
        if full_circuit_audit is not None and not full_circuit_audit.ok:
            note_parts.append("run_full_circuit_audit.ok=False -- 위 체크 결과 참고")
        note = f" ({'; '.join(note_parts)})" if note_parts else ""
        print(f"instance.json 저장: {INSTANCE_OUT}{note}")

        if full_circuit_audit is not None:
            report_data = assemble_report_data(TOPO, INSTANCE_OUT, full_circuit_audit=full_circuit_audit)
            save_html_report(report_data, REPORT_OUT)
            print(f"report.html 저장: {REPORT_OUT}")
        else:
            print("report.html 생략(full_circuit_audit 실패로 assemble_report_data 입력 불완전 -- "
                  "_netlist_sections_structured gap 해소 후 재시도할 것)")
    else:
        print("pipeline_result=None -- 넷리스트 전체가 사이징되지 않아 instance.json/report 저장 생략")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    traceback.print_exc()
