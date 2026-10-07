"""
세션22 -- >=60dB constraint 재보정 근거 확보용 실측 스크립트.
세션21 2차가 cmrr_estimate_db/psrr_estimate_db를 topology-무관 51소자 수치 MNA로
전면 교체하면서 절대 dB 스케일이 완전히 달라졌다(self-test 앵커: CMRR≈125.8dB,
PSRR≈105.5dB) -- 하지만 그 앵커는 self-test용 합성 fixture이지 실제
current_reuse_telescopic_ota 회로를 이 topology.json의 실제 theta bounds로 사이징한
값이 아니다. "상상으로 채우지 말고 근거+확인 후 진행" 원칙에 따라, 실제 회로를 대표
theta 조합 3개(전부 하한/중간/상한 고정)로 실제 사이징해 새 스케일에서 진짜
cmrr_estimate_db/psrr_estimate_db/gain_db/gain_full_circuit_db가 어느 범위에
나오는지부터 확인한다. 프로덕션 topology.json은 읽기만 하고 임시 복사본만 수정한다
(session20 스모크 테스트와 동일 패턴).
"""
import sys, json, tempfile, os, traceback
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

with open(TOPO, encoding="utf-8") as f:
    topo_orig = json.load(f)

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


# 균일 fraction(전부 같은 비율로 고정)은 M9b=M8-M9a KCL 부호가 깨져 전부 infeasible로
# 확인됨(1차 시도, 실측) -- r_classab_battery(M8 몫)/K_replica(M9a 몫)의 상대적 균형이
# 깨지기 때문. 나머지 11개 자유 theta는 원래 중간값으로 고정하고, 이 KCL에 실제로 관여하는
# K_replica/r_classab_battery만 각자 bounds 전체를 4점 격자로 남겨(4x4=16 combo, 원래
# 8192개 전수탐색의 병목이었던 조합폭발과 무관한 소규모) optimize_full_circuit_budget()이
# 그중 실제 feasible한 조합을 스스로 찾게 한다 -- KCL 관계를 손으로 추측해 강제하지 않는다.
FREE_TO_KEEP = {"K_replica", "r_classab_battery"}


def make_fixed_topo():
    topo = json.loads(json.dumps(topo_orig))
    thetas = topo["sizing_roles"]["theta"]
    for t in thetas:
        lo, hi = t["bounds"]
        if lo != hi and t["name"] not in FREE_TO_KEEP:
            mid = (lo + hi) / 2
            t["bounds"] = [mid, mid]
    return topo


METRICS_OF_INTEREST = ["power_uA", "gain_db", "gain_full_circuit_db",
                        "cmrr_estimate_db", "psrr_estimate_db",
                        "mismatch_sigma_mV", "classab_centering_dev_v"]

topo = make_fixed_topo()
tmp_path = os.path.join(tempfile.gettempdir(), "sample_metrics_s22_kcl_grid.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo, f)
print(f"임시 topology: {tmp_path} (자유: {sorted(FREE_TO_KEEP)}, 나머지는 중간값 고정)")
try:
    result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=4)
    print("theta_star:", result["theta_star"])
    print("audit_ok:", result["audit_ok"])
    for k in METRICS_OF_INTEREST:
        v = result["metrics"].get(k)
        print(f"  {k}: {v}")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {e}")
    traceback.print_exc()
