"""
세션22 item 2 -- 13개 자유 theta 각각이 cmrr_estimate_db/psrr_estimate_db/gain_db/
gain_full_circuit_db/classab_centering_dev_v에 실제로 얼마나 영향을 주는지 one-at-a-time(OAT)
수치 민감도로 확인한다. 세션20-B의 그룹 구조(5-theta 결합/2-theta feasibility 결합/6개 독립)는
세션21 2차의 topology-무관 51소자 solver로 metric 발자국이 완전히 바뀌어(원칙적으로 거의 모든
소자에 의존) 무효화됐다 -- 정적 그래프가 아니라 실측 수치로 다시 확인한다(.ai/context.md
"지금 상태" 2번).

방법: 나머지 12개 자유 theta를 BASELINE 값(물리적으로 유효함이 이미 확인된 조합, 세션22
sample_metrics 스크립트 결과 재사용)에 고정하고, 대상 theta 1개만 bounds의 하한/BASELINE/상한
3점으로 흔든다. optimize_full_circuit_budget()의 feasibility 게이트(constraints 위반 시
그 조합을 조용히 건너뛰고 전부 실패하면 예외)는 이 실험 목적과 안 맞으므로(민감도를 보려는
것이지 "실제로 쓸 조합을 찾으려는" 게 아님) 임시 topology 복사본에서 constraints를 빈 리스트로
비워 매 조합이 물리적으로만 유효하면(음전류 등만 없으면) 그대로 metrics를 받는다 -- 이건
constraints 자체를 바꾸는 게 아니라 "이 실험용 임시 파일"에서만 비활성화(프로덕션
topology.json은 읽기만 함).
"""
import sys, json, tempfile, os
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import SemiEmpiricalGmIdLUT, optimize_full_circuit_budget, InfeasibleSizingError

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

thetas_orig = topo_orig["sizing_roles"]["theta"]
free_names = [t["name"] for t in thetas_orig if t["bounds"][0] != t["bounds"][1]]
bounds_by_name = {t["name"]: tuple(t["bounds"]) for t in thetas_orig}

# 세션22 sample_metrics_session22.py가 물리적으로 유효함을 실측 확인한 조합(나머지는 자기
# bounds의 중간값) -- 이 실험의 BASELINE.
BASELINE = {name: (lo + hi) / 2 for name, (lo, hi) in bounds_by_name.items()}
BASELINE["K_replica"] = 0.1
BASELINE["r_classab_battery"] = 0.3

METRICS = ["power_uA", "gain_db", "gain_full_circuit_db", "cmrr_estimate_db",
           "psrr_estimate_db", "classab_centering_dev_v", "mismatch_sigma_mV"]


def eval_point(theta_values):
    """theta_values(전체 13개 자유 theta 값)를 고정하고 constraints 없이 1개 조합만 평가."""
    topo = json.loads(json.dumps(topo_orig))
    thetas = topo["sizing_roles"]["theta"]
    for t in thetas:
        if t["name"] in theta_values:
            v = theta_values[t["name"]]
            t["bounds"] = [v, v]
    topo["sizing_roles"]["constraints"] = []
    tmp_path = os.path.join(tempfile.gettempdir(), "theta_sens_s22_point.json")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(topo, f)
    result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=2)
    return result["metrics"]


print("=== BASELINE ===")
try:
    base_metrics = eval_point(BASELINE)
    for k in METRICS:
        print(f"  {k}: {base_metrics.get(k)}")
except Exception as e:
    base_metrics = None
    print(f"[BASELINE FAIL] {type(e).__name__}: {e}")

print()
for name in free_names:
    lo, hi = bounds_by_name[name]
    base_val = BASELINE[name]
    print(f"=== {name} (bounds=[{lo}, {hi}], baseline={base_val}) ===")
    for label, val in [("lo", lo), ("base", base_val), ("hi", hi)]:
        tv = dict(BASELINE)
        tv[name] = val
        try:
            m = eval_point(tv)
            row = ", ".join(f"{k}={m.get(k):.3g}" if isinstance(m.get(k), (int, float)) else f"{k}={m.get(k)}"
                             for k in METRICS)
            print(f"  [{label}={val:.4g}] {row}")
        except InfeasibleSizingError as e:
            print(f"  [{label}={val:.4g}] PHYSICALLY INFEASIBLE: {e}")
        except Exception as e:
            print(f"  [{label}={val:.4g}] [FAIL] {type(e).__name__}: {e}")
    print()
