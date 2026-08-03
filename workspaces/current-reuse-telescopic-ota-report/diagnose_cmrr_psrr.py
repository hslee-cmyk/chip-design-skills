"""
CMRR/PSRR 미달 근본원인 진단 -- 배치 7-5 이어서, 2026-08-03 (2).
스모크 실행(theta 전부 중간값 고정)의 실제 sizing 결과(M1a/M4a/M2a/M3a/M5/M6/M7)를
그대로 읽어서, L_cascode의 gm_id(현재 고정 기본값 15.0)를 gm_id_grid 전체로 스윕했을 때
CMRR이 60dB를 넘는 지점이 있는지, M5의 gm_id_role을 'balanced'->'gain'으로 바꿨을 때
PSRR이 어떻게 바뀌는지를 하네스 재실행 없이(수식 재사용) 확인한다.
"""
import sys, json, tempfile, os, math
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
import sizing_recipe
from sizing_recipe import (SemiEmpiricalGmIdLUT, optimize_full_circuit_budget,
                            search_gm_id_for_role)

# 이 진단 스크립트는 CMRR/PSRR sizing(gm/gds/gm_id/L/ID)만 필요하다 -- 별개 gap
# (common_centroid_layout()의 "count=1 < n=2", context.md 이월 항목)이 매번 이 단계에서
# 막아서 결과 dict를 못 받으므로, repair_matching_safety()만 이 진단에서 no-op으로
# 우회한다(sizing_recipe.py 자체는 수정하지 않음 -- 이 파일 안에서만 monkeypatch).
import types
sizing_recipe.repair_matching_safety = lambda rows, pairs, kinds, max_iter=3: (rows, types.SimpleNamespace(ok=False))

LUTFILE = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz"
TOPO = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json"

with open(TOPO, "r", encoding="utf-8") as f:
    topo = json.load(f)
for t in topo["sizing_roles"]["theta"]:
    lo, hi = t["bounds"]
    mid = (lo + hi) / 2.0
    t["bounds"] = [mid, mid]

# CMRR/PSRR만 완화(-1e9) -- 실제 sizing(gm/gds/gm_id/L/ID)을 읽기 위해서일 뿐,
# gain/mismatch 등 이미 만족하는 제약은 그대로 둬서 다른 회귀는 안 섞이게 한다.
for c in topo["sizing_roles"]["constraints"]:
    if c["metric"] in ("cmrr_estimate_db", "psrr_estimate_db"):
        c["value"] = -1e9

tmp_path = os.path.join(tempfile.gettempdir(), "current_reuse_telescopic_ota.diag.topology.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo, f)

d = np.load(LUTFILE)
W_REF = 5e-6
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=W_REF, SID_1F=d["SID_1F_n"])
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=W_REF, SID_1F=d["SID_1F_p"])

spec = {
    "lut_by_kind": {"nmos": nmos, "pmos": pmos}, "lut": nmos, "vdd": 1.8,
    "L_candidates": [float(v) for v in nmos.L_grid],
    "VDS_candidates": [float(v) for v in nmos.VDS_grid[::24]],
    "gm_id_grid": [4.0, 8.0, 12.0, 16.0, 20.0, 24.0],
    "L_min": 0.15e-6, "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
    "W_bounds": (1e-6, 200e-6),
    "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
    "stage_objective": "power", "stage_w_max": 200e-6,
    "min_finger_w": 1e-6, "max_finger_w": 40e-6,
    "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    "t_lln": 30e-9, "PM_target_deg": 70.0,
    "Cc": 500e-15, "Cf": 500e-15, "Cs": 500e-15, "C_Ltot": 1e-12,
    "t_settle_total": 6.9 * 30e-9, "omega_c": 6.9 / 30e-9,
}

result = optimize_full_circuit_budget(tmp_path, spec, grid_points_per_theta=2)
sizing = result["sizing"]
print("=== baseline metrics (theta=midpoint 전부, L_cascode gm_id=15.0 기본값) ===")
for k, v in result["metrics"].items():
    print(f"  {k} = {v}")

for name in ["M1a", "M4a", "M2a", "M3a", "M5", "M6", "M7"]:
    e = sizing[name]
    print(f"  {name}: L={e.get('L')*1e6:.4f}um gm_id={e.get('gm_id'):.2f} "
          f"gm={e.get('gm'):.4e} gds={e.get('gds'):.4e} ID={e.get('ID'):.4e}")

gmp = sizing["M1a"]["gm"]
gmn = sizing["M4a"]["gm"]
rop1 = 1.0 / sizing["M1a"]["gds"]
ron1 = 1.0 / sizing["M4a"]["gds"]
gds_tail_p = sizing["M6"]["gds"] + sizing["M7"]["gds"]
Rx = 1.0 / gds_tail_p
Ry = 1.0 / sizing["M5"]["gds"]

print()
print("=== L_cascode gm_id 스윕 (M2a/M3a에만 명시적 gm_id 적용, 나머지는 baseline 그대로) ===")
print(f"{'gm_id':>6} {'L(um)':>8} {'CMRR(dB)':>10}")
L_cascode_bounds = [1.5e-7, 1.0e-6]
best = None
for gm_id in [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 16.0, 18.0, 20.0, 22.0, 24.0]:
    for L in [L_cascode_bounds[0], (L_cascode_bounds[0]+L_cascode_bounds[1])/2, L_cascode_bounds[1]]:
        idu = nmos.gm_id_to_id_density(gm_id, L, 0.6, 0.0)  # cascode devices: 대칭이라 n/p 동일 LUT 가정은 근사
        ID_p2a = sizing["M2a"]["ID"]  # KCL로 이미 확정된 실제 ID 재사용
        ID_n3a = sizing["M3a"]["ID"]
        gm_gds_p = pmos.gm_gds_ratio(gm_id, L, 0.6, 0.0)
        gm_gds_n = nmos.gm_gds_ratio(gm_id, L, 0.6, 0.0)
        gm2a = gm_id * ID_p2a
        gds2a = gm2a / gm_gds_p
        gm3a = gm_id * ID_n3a
        gds3a = gm3a / gm_gds_n
        rop2 = 1.0 / gds2a
        ron2 = 1.0 / gds3a
        Kp_prime = gmp * rop1 * rop2
        Kn_prime = gmn * ron1 * ron2
        R_out = Kp_prime * Kn_prime / (Kp_prime + Kn_prime)
        Adm = (gmp + gmn) * R_out
        Kp = gmp * Kp_prime
        Kn = gmn * Kn_prime
        Acm = Kn * Kp * (Rx + Ry) / (Kn * Ry + Kp * Rx)
        cmrr = 20 * math.log10(Adm / Acm)
        marker = " <== BEST" if (best is None or cmrr > best[0]) else ""
        if marker:
            best = (cmrr, gm_id, L)
        print(f"{gm_id:6.1f} {L*1e6:8.3f} {cmrr:10.2f}{marker}")

print()
print(f"CMRR 최댓값: {best[0]:.2f}dB @ gm_id={best[1]}, L={best[2]*1e6:.3f}um "
      f"(목표 60dB {'달성' if best[0]>=60 else '미달'})")

print()
print("=== M5/M6/M7(tail) 자체의 L/gm_id를 극단으로 밀었을 때 Rx/Ry(=1/gds) 상한 및 "
      "그때의 CMRR/PSRR 상한 (L_cascode는 baseline gm_id=15.0 그대로 고정) ===")
ID5, ID6, ID7 = sizing["M5"]["ID"], sizing["M6"]["ID"], sizing["M7"]["ID"]
best_tail = None
for gm_id_tail in [2.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0]:
    for L_tail in [0.15e-6, 0.35e-6, 0.5e-6, 1.0e-6, nmos.L_grid[-1]]:
        try:
            gm_gds5 = nmos.gm_gds_ratio(gm_id_tail, L_tail, 0.6, 0.0)
            gm_gds6 = pmos.gm_gds_ratio(gm_id_tail, L_tail, 0.6, 0.0)
            gm_gds7 = pmos.gm_gds_ratio(gm_id_tail, L_tail, 0.6, 0.0)
        except ValueError:
            continue
        gds5 = gm_id_tail * ID5 / gm_gds5
        gds6 = gm_id_tail * ID6 / gm_gds6
        gds7 = gm_id_tail * ID7 / gm_gds7
        Ry_t = 1.0 / gds5
        Rx_t = 1.0 / (gds6 + gds7)
        psrr_t = 20 * math.log10(gm_id_tail * ID5 / gds5)
        # CMRR 재계산(cascode는 baseline 그대로, tail만 교체)
        rop2 = 1.0 / sizing["M2a"]["gds"]
        ron2 = 1.0 / sizing["M3a"]["gds"]
        Kp_prime_t = gmp * rop1 * rop2
        Kn_prime_t = gmn * ron1 * ron2
        R_out_t = Kp_prime_t * Kn_prime_t / (Kp_prime_t + Kn_prime_t)
        Adm_t = (gmp + gmn) * R_out_t
        Kp_t = gmp * Kp_prime_t
        Kn_t = gmn * Kn_prime_t
        Acm_t = Kn_t * Kp_t * (Rx_t + Ry_t) / (Kn_t * Ry_t + Kp_t * Rx_t)
        cmrr_t = 20 * math.log10(Adm_t / Acm_t)
        score = min(cmrr_t, psrr_t)
        marker = " <== BEST(min)" if (best_tail is None or score > best_tail[0]) else ""
        if marker:
            best_tail = (score, gm_id_tail, L_tail, cmrr_t, psrr_t)
        print(f"  gm_id_tail={gm_id_tail:5.1f} L={L_tail*1e6:6.3f}um -> Rx={Rx_t:9.0f} Ry={Ry_t:9.0f} "
              f"CMRR={cmrr_t:7.2f}dB PSRR={psrr_t:7.2f}dB{marker}")
print()
print(f"tail 극단화 최선: gm_id={best_tail[1]}, L={best_tail[2]*1e6:.3f}um -> "
      f"CMRR={best_tail[3]:.2f}dB, PSRR={best_tail[4]:.2f}dB "
      f"(둘 다 60dB {'달성' if best_tail[0]>=60 else '미달'})")

print()
print("=== M5 gm_id_role: balanced(현재) vs gain(대안) 비교 ===")
M5 = sizing["M5"]
L5, ID5 = M5["L"], M5["ID"]
vds5 = 0.6
gm_id_balanced = search_gm_id_for_role(nmos, L5, vds5, 0.0, ID5, role="balanced",
                                        W_bounds=(1e-6, 200e-6), gm_id_grid=spec["gm_id_grid"])
gm_id_gain = search_gm_id_for_role(nmos, L5, vds5, 0.0, ID5, role="gain",
                                    W_bounds=(1e-6, 200e-6), gm_id_grid=spec["gm_id_grid"])
for label, gm_id in [("balanced(현재)", gm_id_balanced), ("gain(대안)", gm_id_gain)]:
    ratio = nmos.gm_gds_ratio(gm_id, L5, vds5, 0.0)
    psrr = 20 * math.log10(ratio)
    print(f"  {label}: gm_id={gm_id:.2f} gm/gds={ratio:.2f} psrr_estimate_db={psrr:.2f}")

print("DONE")
