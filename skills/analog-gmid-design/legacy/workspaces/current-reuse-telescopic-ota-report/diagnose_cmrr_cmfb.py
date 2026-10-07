"""CMFB 포함 CMRR 신규식(telescopic_class_ab_cmfb) 실회로 적용 진단 -- 2026-08-03.

2026-08-03 배치 7-5c 갱신: topology.json _correction_log_5(Fig.5 CMFB 7소자 전면 정정 --
M36a/M36b는 미러가 아니라 독립 diode 부하, M39/M40은 PMOS diode 2단 분압기라 v(Voc_des)=0)
에 맞춰 재작성. A_c는 이제 다이오드 부하 차동쌍이라 O(1) 음수이고, CM 루프의 음귀환 여부는
A_c 혼자가 아니라 T = -H*A_c*G2(2단 CM 이득 포함) 전체 부호가 정한다.

diagnose_cmrr_psrr.py와 같은 방식(theta 전부 중간값 고정, CMRR/PSRR 제약만 완화)으로
51개 소자 harness를 한 번 돌린 뒤,
  (a) 옛 식(telescopic_class_ab, 1단 open-loop)과 새 식(CMFB 포함)의 CMRR 수치 비교
  (b) 새 식의 내부 항(Acm_open / H / A_c / 루프이득 T) 분해
  (c) CMFB 소자(M38/M39/M40/M36b)와 M7의 사이징이 CMRR을 어떻게 움직이는지 스윕
을 하네스 재실행 없이(수식 재사용) 확인한다.
"""
import sys, json, tempfile, os, math
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
import sizing_recipe
from sizing_recipe import (SemiEmpiricalGmIdLUT, optimize_full_circuit_budget, compute_metric,
                            SizingContext, _cmfb_amp_gain_diode_load)

# diagnose_cmrr_psrr.py와 동일한 우회(별개 gap: common_centroid_layout()의 count=1<n=2).
import types
sizing_recipe.repair_matching_safety = lambda rows, pairs, kinds, max_iter=3: (rows, types.SimpleNamespace(ok=False))

ASSETS = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
LUTFILE = os.path.join(ASSETS, "sky130_nfet_pfet_lut_sample.npz")
TOPO = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
# 2026-08-03 배치 7-5c: 다른 세션이 Class-AB 2단(Monticelli 부동전류원 M9a/M9b, M8/M11a/M13
# 병렬전류원)을 동시 재배선 중이라 sizing_roles.theta의 전류 전파가 아직 안 맞고
# (Vg15/Vg16이 5단자 노드가 되면서 M12/M10의 전류를 A엔진이 못 정함) 하네스가 완주하지
# 못한다. 이 진단의 목적은 **CMFB 정정만의 효과**를 보는 것이므로, 마지막 커밋(HEAD)의
# Class-AB 넷리스트 + 이번 CMFB 정정만 합친 토폴로지로 돌린다(TOPO_OVERRIDE 환경변수).
TOPO = os.environ.get("TOPO_OVERRIDE", TOPO)

with open(TOPO, "r", encoding="utf-8") as f:
    topo = json.load(f)
for t in topo["sizing_roles"]["theta"]:
    lo, hi = t["bounds"]
    mid = (lo + hi) / 2.0
    t["bounds"] = [mid, mid]
for c in topo["sizing_roles"]["constraints"]:
    if c["metric"] in ("cmrr_estimate_db", "psrr_estimate_db"):
        c["value"] = -1e9
# 진단 목적: A_c<=0(CM 양귀환)일 때도 사이징 결과 자체는 보고 싶으므로, 이 스크립트 안에서만
# cmrr_estimate_db metric을 임시로 제거해 하네스를 완주시킨다(sizing_recipe.py는 안 건드림 --
# 실제 계산은 아래에서 compute_metric()으로 직접 호출해 예외까지 그대로 관찰한다).
_cmrr_spec_saved = topo["sizing_roles"]["metrics"].pop("cmrr_estimate_db")
topo["sizing_roles"]["constraints"] = [c for c in topo["sizing_roles"]["constraints"]
                                        if c["metric"] != "cmrr_estimate_db"]

tmp_path = os.path.join(tempfile.gettempdir(), "current_reuse_telescopic_ota.cmfbdiag.topology.json")
with open(tmp_path, "w", encoding="utf-8") as f:
    json.dump(topo, f)

d = np.load(LUTFILE)
W_REF = 5e-6
nmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_n"], d["GM_n"], d["GDS_n"],
                             d["CGG_n"], W_ref=W_REF, SID_1F=d["SID_1F_n"])
pmos = SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"], d["ID_p"], d["GM_p"], d["GDS_p"],
                             d["CGG_p"], W_ref=W_REF, SID_1F=d["SID_1F_p"])

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
ctx = SizingContext(sized=sizing, spec=spec)
mspec = _cmrr_spec_saved


def cmrr(spec_override=None):
    try:
        return f"{compute_metric(spec_override or mspec, ctx):10.2f}"
    except ValueError:
        return f"{'양귀환거부':>10}"

print("=== baseline metrics (theta=midpoint 전부) ===")
for k, v in result["metrics"].items():
    print(f"  {k} = {v}")

print()
print("=== CMRR 관련 소자 사이징 ===")
for name in ["M1a", "M2a", "M3a", "M4a", "M5", "M6", "M7",
             "M36a", "M36b", "M37a", "M37b", "M38", "M39", "M40"]:
    e = sizing[name]
    print(f"  {name}: L={e['L']*1e6:7.4f}um W={e['W']*1e6:8.3f}um gm_id={e['gm_id']:6.2f} "
          f"gm={e['gm']:.4e} gds={e['gds']:.4e} ID={e['ID']:.4e}")

print()
print("=== 옛 식(open-loop) vs 새 식(CMFB 포함) ===")
old = compute_metric({k: v for k, v in mspec.items() if not k.startswith("cmfb")
                      and k != "cm_sense_gain"} | {"circuit_family": "telescopic_class_ab"}, ctx)
print(f"  telescopic_class_ab      (1단 open-loop) : {old:9.3f} dB")
print(f"  telescopic_class_ab_cmfb (CMFB 포함)     : {cmrr()} dB")

# 내부 항 분해
gmp, gdsp1 = sizing["M1a"]["gm"], sizing["M1a"]["gds"]
gmcp, gdsp2 = sizing["M2a"]["gm"], sizing["M2a"]["gds"]
gmn, gdsn1 = sizing["M4a"]["gm"], sizing["M4a"]["gds"]
gmcn, gdsn2 = sizing["M3a"]["gm"], sizing["M3a"]["gds"]
Rx = 1.0 / (sizing["M6"]["gds"] + sizing["M7"]["gds"])
Ry = 1.0 / sizing["M5"]["gds"]
Kp_ = gmcp / (gdsp1 * gdsp2); Kn_ = gmcn / (gdsn1 * gdsn2)
Kp, Kn = gmp * Kp_, gmn * Kn_
Adm = (gmp + gmn) * (Kp_ * Kn_ / (Kp_ + Kn_))
Acm0 = (Rx + Ry) * Kn * Kp / (Kn * Ry + Kp * Rx)
H = -sizing["M7"]["gm"] * (Rx * Kp) * (Ry * Kn) / (Rx * Kp + Ry * Kn)
A_c = _cmfb_amp_gain_diode_load(mspec, ctx)
s2 = [sizing[d] for d in mspec["cmfb_stage2_devices"]]
G2 = -sum(e["gm"] for e in s2) / sum(e["gds"] for e in s2) * mspec.get("cm_sense_gain", 1.0)
T = -H * A_c * G2
print()
print("=== 새 식 내부 항 분해 ===")
print(f"  Adm_open = {Adm:.4e}  ({20*math.log10(Adm):.2f} dB)")
print(f"  Acm_open = {Acm0:.4e}  -> CMRR_open = {20*math.log10(Adm/Acm0):.3f} dB")
print(f"  Rx = {Rx:.4e} ohm, Ry = {Ry:.4e} ohm, Kp = {Kp:.4e}, Kn = {Kn:.4e}")
print(f"  H  (v_o1cm/v_cmfb, 음수여야 정상) = {H:.4e}")
print(f"  A_c(CMFB 다이오드부하 차동쌍 이득, 음수여야 정상) = {A_c:.4f}"
      f"   [leading order -gm37a*gm37b/(gm36a*(gm37a+gm37b)) = "
      f"{-sizing['M37a']['gm']*sizing['M37b']['gm']/(sizing['M36a']['gm']*(sizing['M37a']['gm']+sizing['M37b']['gm'])):.4f}]")
print(f"  G2 (2단 CM 이득, 음수여야 정상) = {G2:.4e}  ({20*math.log10(abs(G2)):.2f} dB)")
print(f"  T = -H*A_c*G2 = {T:.4e}  ({'음귀환 OK' if T>0 else '★양귀환 -- 계산 거부됨'})"
      f"  -> 20log10|1+T| = {20*math.log10(abs(1+T)):.3f} dB")

print()
print("=== CMFB 소자/M7 스윕: 어느 파라미터가 CMRR을 움직이는가 ===")
print(f"{'param':<28}{'x0.25':>10}{'x0.5':>10}{'x1':>10}{'x2':>10}{'x4':>10}")
for dev, key in [("M7", "gm"), ("M38", "gds"), ("M36a", "gm"), ("M36b", "gm"),
                 ("M37a", "gm"), ("M37b", "gm"), ("M15", "gm"), ("M15", "gds"),
                 ("M16", "gds"), ("M5", "gds"), ("M6", "gds")]:
    base = sizing[dev][key]
    row = []
    for m in [0.25, 0.5, 1.0, 2.0, 4.0]:
        sizing[dev][key] = base * m
        row.append(cmrr())
    sizing[dev][key] = base
    print(f"{dev + '.' + key:<28}" + "".join(row))

print()
print("=== M39/M40은 정말 식에서 사라졌는가(v(Voc_des)=0 전제 확인) ===")
b39, b40 = sizing["M39"]["gds"], sizing["M40"]["gds"]
base_db = cmrr()
for m in [0.1, 1.0, 10.0]:
    sizing["M39"]["gds"] = b39 * m
    sizing["M40"]["gds"] = b40 * m
    print(f"  gds39/gds40 x{m:5.2f} -> CMRR = {cmrr()} dB  (기준 {base_db} dB, 변하면 회귀)")
sizing["M39"]["gds"], sizing["M40"]["gds"] = b39, b40

print()
print("=== gds38(M38 tail)을 흔들어도 부호가 뒤집히지 않는가 ===")
base38 = sizing["M38"]["gds"]
for m in [0.1, 0.5, 1.0, 2.0, 6.0]:
    sizing["M38"]["gds"] = base38 * m
    ac = _cmfb_amp_gain_diode_load(mspec, ctx)
    print(f"  gds38 x{m:4.2f} = {sizing['M38']['gds']:.4e}  ->  A_c = {ac:9.4f}  CMRR = {cmrr()}")
sizing["M38"]["gds"] = base38

print()
print("=== cm_sense_gain 민감도 (R1/R2 평균망 이득; 이상적 R1=R2면 1.0) ===")
for g in [0.1, 0.5, 1.0, 2.0, 10.0, 100.0]:
    print(f"  cm_sense_gain={g:6.1f} -> CMRR = {cmrr({**mspec, 'cm_sense_gain': g})} dB")
print("DONE")
