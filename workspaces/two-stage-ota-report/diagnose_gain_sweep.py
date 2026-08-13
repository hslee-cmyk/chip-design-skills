"""
세션31 BZ① 진단 전용 -- stage_w_max=500um에서도 gain_db=49.3dB(<60)로 infeasible이라,
real sky130 LUT에서 stage_gain_min(dB)을 30->42로 스윕했을 때(BX가 toy LUT로 이미 해본
스윕과 동일 절차) 실제 달성 가능한 gain_db 상한이 어디인지 확인한다. topology.json 원본은
건드리지 않고, gain_db constraint만 0으로 낮춘 임시 사본을 써서(self-test와 동일 패턴)
매번 infeasible ValueError로 죽지 않고 achieved gain_db를 그대로 얻는다.
"""
import sys, json, os, tempfile, traceback
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
        c["value"] = 0.0  # infeasible로 죽지 않게 임시로 낮춤(진단 전용, 원본 파일 미변경)
tmp_path = os.path.join(tempfile.gettempdir(), "two_stage_ota_gainsweep.topology.json")
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
    "stage_w_max": 500e-6,
    "min_finger_w": 0.1e-6,
    "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                "M5": ["M5", "M7"], "M6": ["M6"]},
}

for gain_min_db_per_stage in [30.0, 34.0, 38.0, 42.0, 46.0, 50.0]:
    spec = dict(base_spec)
    spec["stage_gain_min"] = [10 ** (gain_min_db_per_stage / 20)] * 2
    try:
        result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=5)
        m = result["metrics"]
        print(f"stage_gain_min={gain_min_db_per_stage}dB/stage -> gain_db={m['gain_db']:.2f}, "
              f"power_uA={m['power_uA']*1e6:.2f}, mismatch_sigma_mV={m['mismatch_sigma_mV']:.3f}, "
              f"theta_star={result['theta_star']}")
    except Exception as e:
        print(f"stage_gain_min={gain_min_db_per_stage}dB/stage -> [FAIL] {type(e).__name__}: {e}")
