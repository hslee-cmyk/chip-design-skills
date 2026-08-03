"""
배치 7-5 -- 구조 완주 여부만 빠르게 확인하는 스모크 테스트.
모든 theta의 bounds를 중간값 하나로 접어서 combo 수를 1개로 줄인다(회로가 harness
하나로 끝까지 도는지만 우선 확인 -- 실제 최적 설계점 탐색은 이후 본 실행에서 한다).
"""
import sys, json, copy, tempfile, os, traceback
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

with open(TOPO, "r", encoding="utf-8") as f:
    topo = json.load(f)

for t in topo["sizing_roles"]["theta"]:
    lo, hi = t["bounds"]
    mid = (lo + hi) / 2.0
    t["bounds"] = [mid, mid]

# (제약 완화 제거 -- 실제 constraints 그대로 사용)

tmp_path = os.path.join(tempfile.gettempdir(), "current_reuse_telescopic_ota.smoke.topology.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo, f)

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
    "t_lln": 30e-9,
    "PM_target_deg": 70.0,
    "Cc": 500e-15,
    "Cf": 500e-15,
    "Cs": 500e-15,
    "C_Ltot": 1e-12,
    "t_settle_total": 6.9 * 30e-9,
    "omega_c": 6.9 / 30e-9,
}

try:
    result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=2)
    print("OK -- theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    print("metrics:", result["metrics"])
    n_sized = sum(1 for k, v in result["sizing"].items() if "W" in v)
    print(f"sized devices: {n_sized} / {len(result['sizing'])}")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    traceback.print_exc()
