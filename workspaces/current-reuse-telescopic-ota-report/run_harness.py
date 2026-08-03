"""
batch 7-5 -- current_reuse_telescopic_ota를 optimize_full_circuit_budget() 하나만으로
spec -> instance.json까지 완주시키는 harness-only 실행 스크립트.
"""
import sys, json, traceback
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

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
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    traceback.print_exc()
