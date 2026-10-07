"""
세션11 스모크 테스트 -- run_harness.py(8192개 격자 조합)가 26분+ 걸린 원인(2^13 자유 theta)을
확인한 뒤, 프로덕션 topology.json은 건드리지 않고 임시 복사본에서 자유 theta 대부분을
bounds[0]==bounds[1]로 얼려(고정) 조합 수만 줄여 완주 여부와 조합당 소요시간을 잰다.
회로/사이징 로직 자체는 원본과 동일 -- 오직 grid 크기만 축소.
"""
import sys, json, time, tempfile, os, traceback
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

with open(TOPO, encoding="utf-8") as f:
    topo = json.load(f)

thetas = topo["sizing_roles"]["theta"]
free = [t for t in thetas if t["bounds"][0] != t["bounds"][1]]
KEEP_FREE = 2  # 2개만 자유로 남기고 나머지는 중간값으로 고정(하한값은 M9b 음전류로 infeasible 확인됨)
for t in free[KEEP_FREE:]:
    mid = (t["bounds"][0] + t["bounds"][1]) / 2
    t["bounds"] = [mid, mid]

frozen_names = [t["name"] for t in free[KEEP_FREE:]]
kept_names = [t["name"] for t in free[:KEEP_FREE]]
print(f"자유 theta {len(free)}개 중 {len(kept_names)}개만 유지({kept_names}), "
      f"{len(frozen_names)}개 고정: {frozen_names}")

tmp_path = os.path.join(tempfile.gettempdir(), "smoke_current_reuse_telescopic_ota.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo, f)
print(f"임시 topology: {tmp_path}")

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

t0 = time.time()
try:
    result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=2)
    elapsed = time.time() - t0
    n_combo = 2 ** KEEP_FREE
    print(f"OK -- 소요시간: {elapsed:.1f}s (combo={n_combo}개, combo당 평균 {elapsed/n_combo:.1f}s)")
    print(f"전체 8192개 격자 추정 소요시간: {elapsed/n_combo*8192/60:.1f}분")
    print("theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    print("metrics:", result["metrics"])
except Exception as e:
    elapsed = time.time() - t0
    print(f"[FAIL] {elapsed:.1f}s 후 {type(e).__name__}: {e}")
    traceback.print_exc()
