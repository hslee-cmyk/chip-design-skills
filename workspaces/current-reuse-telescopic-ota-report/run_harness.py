"""
batch 7-5 -- current_reuse_telescopic_ota를 optimize_full_circuit_budget() 하나만으로
spec -> instance.json까지 완주시키는 harness-only 실행 스크립트.
"""
import sys, json, traceback
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget
from stick_diagram import save_instance_json

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"
INSTANCE_OUT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces\current-reuse-telescopic-ota-report\current_reuse_telescopic_ota.instance.json"

d = np.load(LUTFILE)
W_REF = 5e-6
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=W_REF, SID_1F=d["SID_1F_n"])
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=W_REF, SID_1F=d["SID_1F_p"])

spec = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos},
    "lut": nmos,
    "vdd": 1.8,
    "L_candidates": [float(v) for v in nmos.L_grid],
    "VDS_candidates": [float(v) for v in nmos.VDS_grid[::24]],
    "gm_id_grid": [4.0, 8.0, 12.0, 16.0, 20.0, 24.0],
    "L_min": 0.15e-6,
    "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
    "stage_objective": "power",
    "stage_w_max": 200e-6,
    "min_finger_w": 1e-6,
    "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    # compensation.parameters
    "t_lln": 30e-9,
    "PM_target_deg": 70.0,
    "Cc": 500e-15,
    "Cf": 500e-15,
    "Cs": 500e-15,
    "C_Ltot": 1e-12,
    "t_settle_total": 6.9 * 30e-9,  # t_lln*omega_c=6.9 정의를 그대로 이용한 총 정착시간(초)
    "omega_c": 6.9 / 30e-9,         # 메인루프 unity-gain 각주파수 (N_cmfb_bw servo feed용)
}

try:
    result = optimize_full_circuit_budget(TOPO, spec, grid_points_per_theta=2)
    print("OK -- theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    print("metrics:", result["metrics"])
    # 세션18 -- optimize_full_circuit_budget()은 계산까지만 하고 저장은 안 한다(순수
    # 함수 유지, .ai/context.md 세션18 참고). instance.json 저장은 "진짜 최상위"인 이
    # 스크립트(run_harness.py)의 몫 -- audit_ok=False여도 감사 실패 항목이 있는 상태
    # 그대로 정직하게 저장한다(조용히 성공으로 둔갑시키지 않는다, §1.5 원칙과 동일).
    if result["pipeline_result"] is not None:
        save_instance_json(INSTANCE_OUT, TOPO, result["sizing"], result["pipeline_result"])
        note = "" if result["audit_ok"] else \
            " (audit_ok=False -- audit_row_split에 남은 FAIL 항목 그대로 저장됨)"
        print(f"instance.json 저장: {INSTANCE_OUT}{note}")
    else:
        print("pipeline_result=None -- 넷리스트 전체가 사이징되지 않아 instance.json 저장 생략")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    traceback.print_exc()
