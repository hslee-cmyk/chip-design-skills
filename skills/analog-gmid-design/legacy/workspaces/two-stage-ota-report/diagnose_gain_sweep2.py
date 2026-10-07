"""
세션31 BZ① 진단 전용 2 -- diagnose_gain_sweep.py 결과가 헷갈렸던 이유를 분리한다.
gain_db constraint를 완전히 빼면 grid search가 순수 objective(minimize power_uA)만 보고
L_mirror_M3/L_mirror_M5를 최소값(1.5e-7)으로 고른다(gain을 전혀 고려 안 함) -- 그래서
36~37dB로 오히려 낮게 나왔다. 반대로 gain_db>=60(infeasible) 상태에서 에러 메시지가 보여준
"마지막 평가 조합"(L_mirror_M3=L_mirror_M5=1e-6, 즉 itertools.product의 마지막 격자점)이
49.32dB였다 -- 이게 25개 격자점 중 최댓값인지 확인하려면 L_mirror_M3/M5를 1e-6으로
고정(bounds=[1e-6,1e-6])해두고 stage_gain_min(M1/M2/M6 compensation floor)만 스윕해
achieved gain_db 상한을 직접 확인한다.
"""
import sys, json, os, tempfile
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget, dense_candidates, layout_grid_L_candidates

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\two_stage_ota.topology.json"
L_GRID_STEP = 0.005e-6

with open(TOPO, encoding="utf-8") as f:
    topo_dict = json.load(f)
for c in topo_dict["sizing_roles"]["constraints"]:
    if c["metric"] == "gain_db":
        c["value"] = 0.0
for t in topo_dict["sizing_roles"]["theta"]:
    if t["name"] in ("L_mirror_M3", "L_mirror_M5"):
        t["bounds"] = [1.0e-6, 1.0e-6]  # 격자를 없애고 최댓값(sky130 LUT 최대 L)에 고정
tmp_path = os.path.join(tempfile.gettempdir(), "two_stage_ota_gainsweep2.topology.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo_dict, f)

d = np.load(LUTFILE)
W_REF = 5e-6
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=W_REF, SID_1F=d["SID_1F_n"])
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=W_REF, SID_1F=d["SID_1F_p"])

base_spec = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos},
    "lut": nmos,
    "vdd": 1.8,
    "L_candidates": layout_grid_L_candidates(nmos, L_GRID_STEP, n=41),
    "L_grid_step": L_GRID_STEP,
    "VDS_candidates": dense_candidates(nmos.VDS_grid, n=13),
    "gm_id_grid": [i * 0.5 for i in range(4, 61)],
    "GBW": 20e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
    "L_min": 0.15e-6,
    "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
    "stage_objective": "power",
    "stage_w_max": 1500e-6,
    "min_finger_w": 0.1e-6,
    "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                "M5": ["M5", "M7"], "M6": ["M6"]},
}

for gain_min_db_per_stage in [38.0, 42.0, 46.0, 50.0, 54.0, 58.0, 62.0]:
    spec = dict(base_spec)
    spec["stage_gain_min"] = [10 ** (gain_min_db_per_stage / 20)] * 2
    try:
        result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=1)
        m = result["metrics"]
        print(f"stage_gain_min={gain_min_db_per_stage}dB/stage -> gain_db={m['gain_db']:.2f}, "
              f"power_uA={m['power_uA']*1e6:.2f}")
    except Exception as e:
        print(f"stage_gain_min={gain_min_db_per_stage}dB/stage -> [FAIL] {type(e).__name__}: {str(e)[:200]}")
